"""Unit tests for scripts/run.py (stdlib unittest: python3 -m unittest tests/test_runner.py)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import run  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"


def read(name):
    return (DATA / name).read_text()


class ParseTimer(unittest.TestCase):
    def test_parse_master_timer(self):
        # Workers print their own blocks prefixed "G4WT<n> > "; the master's
        # block is the unprefixed one, and it is the one to time.
        events, user, real, sys_ = run.parse_timer(read("mt-output.txt"))
        self.assertEqual(events, 1000)
        self.assertAlmostEqual(real, 41.234567)
        self.assertAlmostEqual(user, 322.5)
        self.assertAlmostEqual(sys_, 0.75)

    def test_parse_serial_timer(self):
        events, user, real, _ = run.parse_timer(read("st-output.txt"))
        self.assertEqual(events, 200)
        self.assertAlmostEqual(user, 59.87)
        self.assertAlmostEqual(real, 60.02)

    def test_missing_block_fails(self):
        with self.assertRaises(run.RunFailed):
            run.parse_timer("G4WT0 >  Run terminated.\nG4WT0 >   User=1.0s Real=1.0s Sys=0.0s\n")


class Banner(unittest.TestCase):
    def test_banner_match(self):
        run.check_banner("G4RNG: variant=dropin engine=mwc192x\n", "dropin", "mwc192x")
        run.check_banner("G4RNG: variant=fast engine=xoshiro256pp\n", "fast-xoshiro256pp", "xoshiro256pp")
        run.check_banner("G4RNG: variant=dropin engine=mixmax\n", "dropin-layout-name", "mixmax")
        run.check_banner("", "stock", "mixmax")

    def test_banner_mismatch(self):
        with self.assertRaises(run.RunMismatch):
            run.check_banner("G4RNG: variant=dropin engine=xoshiro256pp\n", "dropin", "mwc192x")
        with self.assertRaises(run.RunMismatch):
            run.check_banner("G4RNG: variant=dropin engine=xoshiro256pp\n", "fast-xoshiro256pp", "xoshiro256pp")
        with self.assertRaises(run.RunMismatch):
            run.check_banner("", "dropin", "mixmax")
        with self.assertRaises(run.RunMismatch):
            run.check_banner("G4RNG: variant=dropin engine=mixmax\n", "stock", "mixmax")

    def test_replaced_engine(self):
        with self.assertRaises(run.RunMismatch):
            run.check_banner(
                "G4RNG: variant=dropin engine=xoshiro256pp\nG4RNG: engine replaced by MTwistEngine\n",
                "dropin", "xoshiro256pp")


class Observables(unittest.TestCase):
    def test_observables_from_master_lines(self):
        obs = run.parse_observables(
            read("mt-output.txt"),
            [{"name": "edep", "regex": r"Edep in absorber 1 = ([-+0-9.eE]+) MeV"}])
        # The worker line (G4WT0 >) carries a different value and is ignored.
        self.assertEqual(obs, {"edep": 123.45})

    def test_observable_with_unit(self):
        # G4BestUnit picks the unit: a second group converts to MeV / mm.
        ob = [{"name": "eabs", "regex": r"EAbs : mean = ([-+0-9.eE]+) (\w+)"}]
        self.assertEqual(run.parse_observables(" EAbs : mean = 850 MeV rms = 1 GeV\n", ob),
                         {"eabs": 850.0})
        self.assertEqual(run.parse_observables(" EAbs : mean = 1.25 GeV rms = 1 GeV\n", ob),
                         {"eabs": 1250.0})
        ob = [{"name": "len", "regex": r"Track length of primary track = ([-+0-9.eE]+) (\w+)"}]
        self.assertEqual(run.parse_observables(" Track length of primary track = 17.5 cm\n", ob),
                         {"len": 175.0})
        with self.assertRaises(run.RunFailed):
            run.parse_observables(" Track length of primary track = 17.5 furlong\n", ob)

    def test_missing_observable_fails(self):
        with self.assertRaises(run.RunFailed):
            run.parse_observables("nothing\n", [{"name": "x", "regex": r"x = ([0-9.]+)"}])


class Command(unittest.TestCase):
    def test_command_args(self):
        self.assertEqual(run.build_command({}, "/x/TestEm3", "/w/run.mac", "2"),
                         ["taskset", "-c", "2", "/x/TestEm3", "/w/run.mac"])
        self.assertEqual(run.build_command({"args": ["-m", "@MACRO@"]}, "/x/exampleB4a",
                                           "/w/run.mac", "0,2"),
                         ["taskset", "-c", "0,2", "/x/exampleB4a", "-m", "/w/run.mac"])


class LoadGate(unittest.TestCase):
    def test_load_gate_waits_then_runs(self):
        values = iter([2.0, 0.3])
        sleeps = []
        busy = run.wait_for_quiet(read_busy=lambda: next(values), limit=0.5,
                                  max_wait_s=600, poll_s=30, sleep=sleeps.append)
        self.assertEqual(busy, 0.3)
        self.assertEqual(sleeps, [30])

    def test_load_gate_aborts(self):
        sleeps = []
        with self.assertRaises(run.HostBusy):
            run.wait_for_quiet(read_busy=lambda: 2.0, limit=0.5,
                               max_wait_s=60, poll_s=30, sleep=sleeps.append)
        self.assertEqual(sleeps, [30, 30])


class Schedule(unittest.TestCase):
    def test_schedule_rotates_configs(self):
        configs = [("dropin", "mixmax"), ("dropin", "xoshiro256pp"), ("fast-mwc192x", "mwc192x")]
        sched = list(run.schedule(["a", "b"], configs, reps=3))
        self.assertEqual(len(sched), 2 * 3 * 3)
        # rep-major, then workload, then configs rotated by rep
        self.assertEqual(sched[0], (0, "a", "dropin", "mixmax"))
        self.assertEqual(sched[3], (0, "b", "dropin", "mixmax"))
        self.assertEqual(sched[6], (1, "a", "dropin", "xoshiro256pp"))
        self.assertEqual(sched[12], (2, "a", "fast-mwc192x", "mwc192x"))

    def test_seeds_are_paired_across_configs(self):
        self.assertEqual(run.seeds_for("testem3", 4), run.seeds_for("testem3", 4))
        self.assertNotEqual(run.seeds_for("testem3", 4), run.seeds_for("testem3", 5))
        self.assertNotEqual(run.seeds_for("testem3", 4), run.seeds_for("b4hadr", 4))


class ForeignLoad(unittest.TestCase):
    STAT = """cpu  100 0 50 1000 0 0 0 0 0 0
cpu0 10 0 5 100 0 0 0 0 0 0
cpu1 20 0 0 100 0 1 1 3 0 0
cpu2 30 0 10 100 0 0 0 0 0 0
cpu3 40 0 0 100 0 0 0 0 0 0
intr 1 2 3
"""

    def test_read_cpu_jiffies(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(self.STAT)
        j = run.read_cpu_jiffies(f.name)
        self.assertEqual(sorted(j), [0, 1, 2, 3])
        self.assertEqual(j[1], (22, 3))  # user+nice+system+irq+softirq, steal
        self.assertEqual(j[2], (40, 0))

    def test_foreign_load(self):
        # 10 s run, 100 jiffies/s; the run used 10 CPU-seconds (CPU 2); CPU 3
        # (CPU 2's idle sibling) was busy 2 s; 1 s of other work on CPU 0;
        # CPU 1 lost 0.5 s to steal.
        before = {0: (0, 0), 1: (0, 0), 2: (0, 0), 3: (0, 0)}
        after = {0: (100, 0), 1: (0, 50), 2: (1000, 0), 3: (200, 0)}
        f = run.foreign_load(before, after, own_cpu_s=10.0, wall_s=10.0, hz=100, watch=[3])
        self.assertAlmostEqual(f["foreign_cpus"], 0.3)
        self.assertAlmostEqual(f["sibling_busy"], 0.2)
        self.assertAlmostEqual(f["steal_cpus"], 0.05)

    def test_idle_siblings(self):
        topo = {0: "0-1", 1: "0-1", 2: "2-3", 3: "2-3", 4: "4,5", 16: "16"}
        read = lambda c: topo[c]
        self.assertEqual(run.idle_siblings([2], read), [3])
        self.assertEqual(run.idle_siblings([0, 2, 4], read), [1, 3, 5])
        self.assertEqual(run.idle_siblings([16], read), [])

    def test_append_keeps_existing_header(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("host,mode,real_s\n")
        self.assertEqual(run.csv_fieldnames(Path(f.name)), ["host", "mode", "real_s"])
        self.assertEqual(run.csv_fieldnames(Path(f.name + ".new")), run.COLUMNS)
        self.assertIn("foreign_cpus", run.COLUMNS)


class Host(unittest.TestCase):
    def test_default_host_comes_from_environment(self):
        # The shell scripts select the host with $HOST; run.py must agree.
        self.assertEqual(run.default_host({"HOST": "zen5"}), "zen5")
        self.assertEqual(run.default_host({}), "desktop")


class Slots(unittest.TestCase):
    """Parallel slots: slot k of N runs the reps r with r % N == k, pinned to
    its own CPUs; each rep's configurations still run back to back."""
    HOST = {"ST_CPUS": "20 12 28", "MT_CPUS": "8,9", "MT_SLOT_CPUS": "8-15 16-23"}

    def test_schedule_slot_takes_its_reps(self):
        configs = [("dropin", "mixmax"), ("dropin", "xoshiro256pp")]
        full = list(run.schedule(["a"], configs, reps=6))
        part = list(run.schedule(["a"], configs, reps=6, slot=1, slots=3))
        self.assertEqual(part, [x for x in full if x[0] in (1, 4)])

    def test_slot_cpus_st(self):
        self.assertEqual(run.slot_cpus(self.HOST, "st", 0, 1), ("20", []))
        self.assertEqual(run.slot_cpus(self.HOST, "st", 1, 3), ("12", [20, 28]))

    def test_slot_cpus_mt(self):
        self.assertEqual(run.slot_cpus(self.HOST, "mt", 0, 1), ("8,9", []))
        self.assertEqual(run.slot_cpus(self.HOST, "mt", 1, 2), ("16-23", list(range(8, 16))))

    def test_too_many_slots_fail(self):
        with self.assertRaises(SystemExit):
            run.slot_cpus(self.HOST, "st", 3, 4)
        with self.assertRaises(SystemExit):
            run.slot_cpus({"MT_CPUS": "8,9"}, "mt", 0, 2)

    def test_foreign_load_excludes_other_slots(self):
        # CPUs 1 and 2 run the other slots: their load is not foreign.
        before = {0: (0, 0), 1: (0, 0), 2: (0, 0), 3: (0, 0)}
        after = {0: (1000, 0), 1: (1000, 0), 2: (1000, 0), 3: (50, 0)}
        f = run.foreign_load(before, after, own_cpu_s=10.0, wall_s=10.0, hz=100, watch=[],
                             exclude=[1, 2])
        self.assertAlmostEqual(f["foreign_cpus"], 0.05)

    def test_event_scale_default_from_host(self):
        host = {"EVENT_SCALE_ST": "1.5"}
        self.assertEqual(run.default_event_scale(host, "st"), 1.5)
        self.assertEqual(run.default_event_scale(host, "mt"), 1.0)

    def test_check_reads_several_csvs(self):
        import argparse, csv, io, json, tempfile, contextlib
        paths = []
        for variant, n in (("dropin", 7.0), ("fast-xoshiro256pp", 7.1)):
            with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
                w = csv.writer(f)
                w.writerow(["mode", "workload", "variant", "engine", "rep", "observables"])
                w.writerow(["st", "testem3", variant, "xoshiro256pp", 0, json.dumps({"n": n})])
            paths.append(f.name)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run.cmd_check(argparse.Namespace(csv=paths)), 1)


class PhysicsCheck(unittest.TestCase):
    def check(self, values):
        """Runs cmd_check on a CSV with one observable 'n' per (engine, rep)."""
        import argparse, csv, io, json, tempfile, contextlib
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            w = csv.writer(f)
            w.writerow(["mode", "workload", "variant", "engine", "rep", "observables"])
            for engine, vals in values.items():
                for i, v in enumerate(vals):
                    w.writerow(["st", "opnovice2", "dropin", engine, i, json.dumps({"n": v})])
        with contextlib.redirect_stdout(io.StringIO()):
            return run.cmd_check(argparse.Namespace(csv=f.name))

    def test_check_flags_shift(self):
        self.assertEqual(self.check({"mixmax": [10.0, 10.1, 9.9], "xoshiro256pp": [12.0, 12.1, 11.9]}), 1)

    def test_check_passes_agreement(self):
        self.assertEqual(self.check({"mixmax": [10.0, 10.1, 9.9], "xoshiro256pp": [10.05, 9.95, 10.0]}), 0)

    def test_check_flags_constant_but_different(self):
        # Quantized output (OpNovice2 printed 2 digits): zero spread, different means.
        self.assertEqual(self.check({"mixmax": [3000.0, 3000.0], "xoshiro256pp": [3100.0, 3100.0]}), 1)

    def test_check_passes_constant_and_equal(self):
        self.assertEqual(self.check({"mixmax": [45.0, 45.0], "xoshiro256pp": [45.0, 45.0]}), 0)


class PhysicsCalibration(unittest.TestCase):
    """The physics check must hold its false-alarm rate whatever the number of
    reps and of comparisons: with 5 reps a standard error has few degrees of
    freedom, and a campaign makes about a hundred comparisons."""

    def test_t_tail(self):
        # Two-sided P(|T| > t) of Student's t.
        self.assertAlmostEqual(run.t_sf2(3.0, 8), 0.01707, places=4)
        self.assertAlmostEqual(run.t_sf2(2.776445, 4), 0.05, places=4)
        self.assertAlmostEqual(run.t_sf2(2.042272, 30), 0.05, places=4)
        self.assertAlmostEqual(run.t_sf2(0.0, 5), 1.0)

    def test_null_campaigns_rarely_fail(self):
        # 300 campaigns with no real effect: 40 observables x 3 engines, 5 reps
        # each. |z| > 3 fails most of them (~87%); the family-wise check at
        # alpha = 0.01 should fail about 1%.
        import random
        rng = random.Random(7)
        failed = 0
        for _ in range(300):
            groups = {}
            for ob in range(40):
                groups[("st", "w", f"o{ob}")] = {
                    (v, e): [rng.gauss(100.0, 1.0) for _ in range(5)]
                    for v, e in [("dropin", "mixmax"), ("dropin", "xoshiro256pp"),
                                 ("dropin", "mwc192x")]}
            failed += any(c["flagged"] for c in run.physics_comparisons(groups))
        self.assertLessEqual(failed / 300, 0.03)

    def test_duplicate_builds_count_once(self):
        # fast-xoshiro256pp repeats dropin/xoshiro256pp (same seeds, same events), stock
        # repeats the reference: one distinct comparison, so t = 4 with 8
        # degrees of freedom (p = 0.004, below 0.01 / 1) is flagged.
        ref, other = [10.0, 10.2, 9.8, 10.1, 9.9], [10.4, 10.6, 10.2, 10.5, 10.3]
        groups = {("st", "w", "o"): {("dropin", "mixmax"): ref, ("stock", "mixmax"): ref[::-1],
                                     ("dropin", "xoshiro256pp"): other, ("fast-xoshiro256pp", "xoshiro256pp"): other}}
        cs = run.physics_comparisons(groups)
        self.assertEqual({c["n"] for c in cs}, {1})
        eng = [c for c in cs if c["cfg"] == ("dropin", "xoshiro256pp")][0]
        self.assertLess(eng["p"], 0.01)
        self.assertTrue(eng["flagged"])

    def test_duplicates_with_unequal_reps_count_once(self):
        # A campaign in progress: dropin/xoshiro256pp has a sixth rep that
        # fast-xoshiro256pp does not have yet. Still one comparison per engine (the
        # identity check makes builds of one engine agree rep by rep).
        ref, other = [10.0, 10.2, 9.8, 10.1, 9.9, 10.0], [10.4, 10.6, 10.2, 10.5, 10.3, 10.4]
        groups = {("st", "w", "o"): {("dropin", "mixmax"): ref, ("fast-mixmax", "mixmax"): ref[:5],
                                     ("dropin", "xoshiro256pp"): other, ("fast-xoshiro256pp", "xoshiro256pp"): other[:5]}}
        cs = run.physics_comparisons(groups)
        self.assertEqual({c["n"] for c in cs}, {1})
        self.assertEqual(sum(not c["duplicate"] for c in cs), 1)
        eng = [c for c in cs if c["cfg"] == ("dropin", "xoshiro256pp")][0]
        self.assertLess(eng["p"], 0.01)
        self.assertTrue(eng["flagged"])


class IdentityCheck(unittest.TestCase):
    """Runs of one engine and repetition use the same seeds in every build
    (drop-in, fast path, layout replicates), so their physics must agree."""

    def check(self, runs):
        import argparse, csv, io, json, tempfile, contextlib
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            w = csv.writer(f)
            w.writerow(["mode", "workload", "variant", "engine", "rep", "observables"])
            for variant, engine, rep, n in runs:
                w.writerow(["st", "testem3", variant, engine, rep, json.dumps({"n": n})])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = run.cmd_check(argparse.Namespace(csv=f.name))
        return status, out.getvalue()

    def test_identical_builds_pass(self):
        status, _ = self.check([("dropin", "xoshiro256pp", 0, 7.0), ("fast-xoshiro256pp", "xoshiro256pp", 0, 7.0),
                                ("dropin", "mixmax", 0, 7.5), ("fast-mixmax", "mixmax", 0, 7.5),
                                ("dropin-layout-name", "mixmax", 0, 7.5)])
        self.assertEqual(status, 0)

    def test_fast_build_with_other_stream_fails(self):
        status, out = self.check([("dropin", "xoshiro256pp", 0, 7.0), ("fast-xoshiro256pp", "xoshiro256pp", 0, 7.1)])
        self.assertEqual(status, 1)
        self.assertIn("fast-xoshiro256pp", out)

    def test_layout_replicate_with_other_physics_fails(self):
        status, _ = self.check([("dropin", "mixmax", 1, 7.5),
                                ("dropin-layout-noreorder", "mixmax", 1, 7.4)])
        self.assertEqual(status, 1)

    def test_different_reps_are_not_compared(self):
        status, _ = self.check([("dropin", "xoshiro256pp", 0, 7.0), ("fast-xoshiro256pp", "xoshiro256pp", 1, 7.1)])
        self.assertEqual(status, 0)


if __name__ == "__main__":
    unittest.main()


class EventScale(unittest.TestCase):
    # scripts/reproduce.sh calibrates the scale for the host and exports it:
    # the environment overrides the host file, for every script that runs.
    def test_environment_overrides_the_host_file(self):
        host = {"EVENT_SCALE_ST": "1.8"}
        self.assertEqual(run.default_event_scale(host, "st", {"EVENT_SCALE_ST": "2.5"}), 2.5)
        self.assertEqual(run.default_event_scale(host, "st", {}), 1.8)
        self.assertEqual(run.default_event_scale({}, "mt", {}), 1.0)


class Calibrate(unittest.TestCase):
    WL = {"a": {"events_st": 100, "events_mt": 10}, "b": {"events_st": 1000, "events_mt": 10},
          "c": {"events_st": 10, "events_mt": 10}}

    @staticmethod
    def row(workload, events, real_s, mode="st"):
        return {"mode": mode, "workload": workload, "events": str(events), "real_s": str(real_s)}

    def test_scale_gives_the_target_time_to_the_median_workload(self):
        # Seconds per event a: 0.2, b: 0.04, c: 0.2; 60 s needs 300, 1500 and 300
        # events, i.e. scales 3, 1.5 and 30: the median is 3.
        rows = [self.row("a", 50, 10.0), self.row("b", 500, 20.0), self.row("c", 5, 1.0)]
        self.assertEqual(run.calibrated_scale(rows, self.WL, "st", 60.0), 3.0)

    def test_scale_has_two_significant_digits(self):
        rows = [self.row("a", 100, 33.0)]           # 60 s needs 181.8 events: scale 1.818...
        self.assertEqual(run.calibrated_scale(rows, self.WL, "st", 60.0), 1.8)

    def test_repetitions_of_a_workload_are_averaged_and_modes_kept_apart(self):
        rows = [self.row("a", 50, 9.0), self.row("a", 50, 11.0), self.row("a", 50, 99.0, mode="mt")]
        self.assertEqual(run.calibrated_scale(rows, self.WL, "st", 60.0), 3.0)


class MacroLines(unittest.TestCase):
    # Extra commands (e.g. /run/eventModulo 0 1, a reseeding policy) go just
    # before /run/beamOn, where the run's state accepts them.
    def test_extra_lines_precede_beam_on(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            dest = Path(t) / "m.mac"
            run.render_macro({"macro": "testem11.mac.in"}, 10, 1, 2, dest, ["/run/eventModulo 0 1"])
            lines = [l.strip() for l in dest.read_text().splitlines()]
            i = lines.index("/run/eventModulo 0 1")
            self.assertTrue(lines[i + 1].startswith("/run/beamOn"), lines[i:i + 2])
            self.assertEqual(sum(l.startswith("/run/beamOn") for l in lines), 1)

    def test_no_extra_lines_leave_the_macro_unchanged(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            a, b = Path(t) / "a.mac", Path(t) / "b.mac"
            run.render_macro({"macro": "testem11.mac.in"}, 10, 1, 2, a)
            run.render_macro({"macro": "testem11.mac.in"}, 10, 1, 2, b, [])
            self.assertEqual(a.read_text(), b.read_text())
            self.assertNotIn("eventModulo", a.read_text())
