"""Unit tests for scripts/analyze.py (python3 -m unittest tests/test_analyze.py)."""

import csv
import io
import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import analyze  # noqa: E402


def synthetic_rows(effect=0.95, reps=10, noise=0.005, seed=1):
    """dropin/mixmax at 1.0 s/event, dropin/xoshiro256pp at `effect` s/event."""
    rnd = random.Random(seed)
    rows = []
    for rep in range(reps):
        for engine, t in (("mixmax", 1.0), ("xoshiro256pp", effect)):
            real = 100 * t * (1 + rnd.gauss(0, noise))
            rows.append({"host": "h", "mode": "st", "workload": "w", "variant": "dropin",
                         "engine": engine, "rep": str(rep), "events": "100",
                         "real_s": str(real)})
    return rows


class Ratio(unittest.TestCase):
    def test_known_effect_in_ci(self):
        rows = synthetic_rows()
        res = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        self.assertAlmostEqual(res["ratio"], 0.95, delta=0.005)
        self.assertLess(res["lo"], 0.95)
        self.assertGreater(res["hi"], 0.95)
        self.assertTrue(res["significant"])
        self.assertAlmostEqual(res["speedup_pct"], (1 / res["ratio"] - 1) * 100)

    def test_no_effect_not_significant(self):
        rows = synthetic_rows(effect=1.0)
        res = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        self.assertLess(res["lo"], 1.0)
        self.assertGreater(res["hi"], 1.0)
        self.assertFalse(res["significant"])

    def test_bootstrap_is_deterministic(self):
        rows = synthetic_rows()
        a = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        b = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        self.assertEqual(a, b)

    def test_cross_binary_inside_layout_band_not_significant(self):
        # A 0.3% effect across binaries is not significant if the layout band is 1%.
        rows = synthetic_rows(effect=0.997, noise=0.0001)
        res = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"),
                              layout_band=0.01)
        self.assertFalse(res["significant"])
        res = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        self.assertTrue(res["significant"])


class Coverage(unittest.TestCase):
    def simulate(self, n, ratio, noise, drift, sims, seed):
        """Fraction of `sims` campaigns whose interval covers the true ratio."""
        rnd = random.Random(seed)
        hit = 0
        for _ in range(sims):
            rows = []
            for rep in range(n):
                d = rnd.gauss(0, drift)  # shared by the configurations of a rep
                for engine, t in (("mixmax", 1.0), ("xoshiro256pp", ratio)):
                    real = 100 * t * math.exp(d + rnd.gauss(0, noise))
                    rows.append({"mode": "st", "workload": "w", "variant": "dropin",
                                 "engine": engine, "rep": str(rep), "events": "100",
                                 "real_s": str(real)})
            res = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
            hit += res["lo"] <= ratio <= res["hi"]
        return hit / sims

    def test_interval_covers_95_percent_at_5_reps(self):
        # 1000 campaigns: binomial SE of the coverage 0.7%; accept 93-97%.
        cov = self.simulate(n=5, ratio=0.97, noise=0.01, drift=0.0, sims=1000, seed=7)
        self.assertGreater(cov, 0.93)
        self.assertLess(cov, 0.97)

    def test_pairing_removes_shared_rep_effect(self):
        # A 1% effect under a 5% drift shared by the runs of each rep (and 0.1%
        # independent noise) is resolved only if the runs are paired by rep.
        rnd = random.Random(3)
        rows = []
        for rep in range(5):
            d = rnd.gauss(0, 0.05)
            for engine, t in (("mixmax", 1.0), ("xoshiro256pp", 0.99)):
                rows.append({"mode": "st", "workload": "w", "variant": "dropin",
                             "engine": engine, "rep": str(rep), "events": "100",
                             "real_s": str(100 * t * math.exp(d + rnd.gauss(0, 0.001)))})
        res = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        self.assertTrue(res["significant"])
        self.assertLess(res["lo"], 0.99)
        self.assertGreater(res["hi"], 0.99)

    def test_unpaired_reps_are_ignored(self):
        rows = synthetic_rows(reps=4)
        rows = [r for r in rows if not (r["engine"] == "xoshiro256pp" and r["rep"] == "3")]
        res = analyze.compare(rows, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        self.assertEqual(res["n"], 3)


class Screen(unittest.TestCase):
    def row(self, mode, rep, real, user, engine="mixmax"):
        return {"mode": mode, "workload": "w", "variant": "dropin", "engine": engine,
                "rep": str(rep), "events": "100", "real_s": str(real), "user_s": str(user),
                "sys_s": "0.0"}

    def test_st_run_with_lost_cpu_is_flagged(self):
        rows = [self.row("st", 0, 60.0, 59.9), self.row("st", 1, 60.0, 58.0)]
        flagged = analyze.screen(rows)
        self.assertEqual([r["rep"] for r in flagged], ["1"])

    def test_mt_run_below_workload_median_is_flagged(self):
        rows = [self.row("mt", i, 40.0, u) for i, u in enumerate([300.0, 301.0, 299.0, 290.0])]
        self.assertEqual([r["rep"] for r in analyze.screen(rows)], ["3"])

    def test_foreign_load_during_run_is_flagged(self):
        rows = [self.row("st", i, 60.0, 59.9) for i in range(4)]
        rows[1]["sibling_busy"] = "0.2"   # CPU 2's sibling busy 20% of the run
        rows[2]["steal_cpus"] = "0.3"     # hypervisor took CPU time
        rows[3]["foreign_cpus"] = "0.1"   # light load elsewhere: kept
        self.assertEqual([r["rep"] for r in analyze.screen(rows)], ["1", "2"])

    def test_flagged_runs_leave_the_comparison(self):
        rows = synthetic_rows(reps=4)
        for r in rows:
            r["user_s"], r["sys_s"] = r["real_s"], "0.0"
        bad = next(r for r in rows if r["engine"] == "xoshiro256pp" and r["rep"] == "2")
        bad["user_s"] = str(float(bad["real_s"]) * 0.9)
        kept = analyze.drop_flagged(rows, analyze.screen(rows))
        res = analyze.compare(kept, ("st", "w"), ("dropin", "xoshiro256pp"), ("dropin", "mixmax"))
        self.assertEqual(res["n"], 3)


def interference_rows(slowdown=1.0, jitter=0.005, added=0.0, reps=22, seed=3):
    """Each rep run alone and in parallel on the same seed: a per-seed time
    (the physics), per-run timing jitter, and in parallel a slowdown and
    added noise."""
    rnd = random.Random(seed)
    rows = []
    for rep in range(reps):
        base = 1.0 + rnd.gauss(0, 0.01)
        for kind, f, extra in (("alone", 1.0, 0.0), ("parallel", slowdown, added)):
            t = base * f * (1 + rnd.gauss(0, jitter)) * (1 + rnd.gauss(0, extra))
            rows.append({"mode": "st", "workload": "w", "variant": kind, "engine": "mixmax",
                         "rep": str(rep), "events": "100", "real_s": str(100 * t)})
    return rows


class Interference(unittest.TestCase):
    @staticmethod
    def clean_fraction(n=200, **kw):
        return sum(analyze.interference_verdict(interference_rows(seed=s, **kw))["clean"]
                   for s in range(n)) / n

    def test_small_uniform_slowdown_is_clean(self):
        # the first EC2 instance: 0.4% slower, no added noise
        self.assertGreaterEqual(self.clean_fraction(slowdown=1.004, jitter=0.002), 0.9)

    def test_power_limited_slowdown_is_not_clean(self):
        # EC2 MT slots: 30% slower with all domains busy
        self.assertEqual(self.clean_fraction(n=20, slowdown=1.30), 0.0)

    def test_three_percent_slowdown_is_not_clean(self):
        self.assertLessEqual(self.clean_fraction(slowdown=1.03, jitter=0.002), 0.05)

    def test_timing_jitter_without_added_noise_is_clean(self):
        # desktop testem3: ratio sd 1.67% and interval up to 1.0125 from same-seed
        # jitter, 14 reps, with no slowdown and no added noise
        self.assertGreaterEqual(self.clean_fraction(jitter=0.012, reps=14), 0.9)
        his = [analyze.interference_verdict(interference_rows(jitter=0.012, reps=14, seed=s))
               ["workloads"][("st", "w")]["hi"] for s in range(50)]
        self.assertTrue(any(h > 1.01 for h in his))

    def test_added_noise_is_not_clean(self):
        # neighbours adding 2% noise per run to 0.2% jitter
        self.assertLessEqual(self.clean_fraction(jitter=0.002, added=0.02), 0.1)

    def test_no_data_is_not_clean(self):
        self.assertFalse(analyze.interference_verdict([])["clean"])


class Prediction(unittest.TestCase):
    def test_mt_prediction_uses_thread_time(self):
        # MT: 10 ms wall and 80 ms of thread time per event (8 threads); the
        # savings are thread time, so they are divided by 80 ms, not 10 ms.
        bench = {("dropin", "mixmax", "G4UniformRand"): 6.0,
                 ("dropin", "xoshiro256pp", "G4UniformRand"): 5.0,
                 ("dropin", "mixmax", "setSeeds"): 30000.0,
                 ("dropin", "xoshiro256pp", "setSeeds"): 10.0}
        rows = [{"mode": "mt", "workload": "w", "variant": "dropin", "engine": "mixmax",
                 "rep": str(i), "events": "1000", "real_s": "10.0", "user_s": "79.0",
                 "sys_s": "1.0"} for i in range(2)]
        counts = {("mt", "w"): {"flat": 1000, "seeds": 1}}
        pr = analyze.predicted(rows, "mt", "w", counts, bench, "xoshiro256pp")
        self.assertAlmostEqual(pr, (80e6 / (80e6 - 1000 - 29990) - 1) * 100)

    def test_predicted_speedup(self):
        # 1000 draws and 1 reseeding per event; MIXMAX 6 ns/draw and 30000 ns/reseed,
        # xoshiro256++ 5 ns/draw and 10 ns/reseed; MIXMAX event time 1 ms.
        bench = {("dropin", "mixmax", "G4UniformRand"): 6.0,
                 ("dropin", "xoshiro256pp", "G4UniformRand"): 5.0,
                 ("dropin", "mixmax", "setSeeds"): 30000.0,
                 ("dropin", "xoshiro256pp", "setSeeds"): 10.0}
        st = analyze.predict(flat_per_event=1000, seeds_per_event=0, t_event_ns=1e6,
                             bench=bench, variant="dropin", engine="xoshiro256pp")
        self.assertAlmostEqual(st, (1e6 / (1e6 - 1000) - 1) * 100)
        mt = analyze.predict(flat_per_event=1000, seeds_per_event=1, t_event_ns=1e6,
                             bench=bench, variant="dropin", engine="xoshiro256pp")
        self.assertAlmostEqual(mt, (1e6 / (1e6 - 1000 - 29990) - 1) * 100)


class StaticShare(unittest.TestCase):
    def test_prediction_table_shows_static_path_share(self):
        bench = {("dropin", e, w): v for e, w, v in [
            ("mixmax", "G4UniformRand", 6.0), ("mixmax", "setSeeds", 30000.0)] +
            [(e, w, v) for e in analyze.NEW for w, v in (("G4UniformRand", 5.0),
                                                         ("setSeeds", 10.0))]}
        rows = synthetic_rows(reps=2)
        for r in rows:
            r["user_s"], r["sys_s"] = r["real_s"], "0"
        counts = {("st", "w"): {"flat": 1000, "seeds": 0, "static": 600}}
        text = analyze.prediction_table(rows, "st", ["w"], counts, bench)
        self.assertIn("via getTheEngine", text)
        self.assertIn("| 60% |", text)


class Stock(unittest.TestCase):
    def test_summary_compares_stock_with_dropin_mixmax(self):
        # stock 2% faster than drop-in MIXMAX: the reference table says so.
        rnd = random.Random(5)
        rows = []
        for rep in range(5):
            for variant, t in (("dropin", 1.0), ("stock", 1 / 1.02)):
                rows.append({"mode": "st", "workload": "w", "variant": variant,
                             "engine": "mixmax", "rep": str(rep), "events": "100",
                             "real_s": str(100 * t * (1 + rnd.gauss(0, 0.001)))})
        text = analyze.summarize(rows)
        self.assertIn("stock vs. drop-in MIXMAX", text)
        self.assertIn("+2.0", text)
        self.assertIn("Total: fast-path engine vs. stock", text)

    def test_no_stock_section_without_stock_runs(self):
        self.assertNotIn("vs. stock", analyze.summarize(synthetic_rows()))


class Dir(unittest.TestCase):
    def test_load_dir_reads_all_run_csvs(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        for k in range(2):
            (d / f"runs-st-{k}.csv").write_text(
                "mode,workload,variant,engine,rep,events,real_s\n"
                f"st,w,dropin,mixmax,{k},10,2.5\n")
        (d / "physics").mkdir()
        (d / "physics" / "runs.csv").write_text("mode,workload,variant,engine,rep,events,real_s\n"
                                                "st,w,dropin,mixmax,9,10,2.5\n")
        rows = analyze.load_dir(d)
        self.assertEqual(sorted(r["rep"] for r in rows), ["0", "1"])


class Csv(unittest.TestCase):
    def test_load_reads_runs_csv(self):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=["mode", "workload", "variant", "engine", "rep",
                                            "events", "real_s"])
        w.writeheader()
        w.writerow({"mode": "st", "workload": "w", "variant": "dropin", "engine": "mixmax",
                    "rep": 0, "events": 10, "real_s": 2.5})
        rows = analyze.load(io.StringIO(buf.getvalue()))
        self.assertEqual(analyze.per_event(rows, ("st", "w"), ("dropin", "mixmax")), [0.25])


if __name__ == "__main__":
    unittest.main()
