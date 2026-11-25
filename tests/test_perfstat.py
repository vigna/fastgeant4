"""Unit tests for scripts/perfstat.py (python3 -m unittest tests/test_perfstat.py)."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import perfstat  # noqa: E402

PERF_OUTPUT = """# started on Mon Nov 23 05:00:00 2026

123456789,,cycles:u,1000,100.00,,
98765,,instructions:u,1000,100.00,2.50,insn per cycle
<not supported>,,L1-icache-load-misses:u,0,100.00,,
<not counted>,,iTLB-load-misses:u,0,0.00,,
"""


class Parse(unittest.TestCase):
    def test_counts_and_missing_counters(self):
        c = perfstat.parse_perf_stat(PERF_OUTPUT)
        self.assertEqual(c["cycles"], 123456789.0)
        self.assertEqual(c["instructions"], 98765.0)
        self.assertIsNone(c["L1-icache-load-misses"])
        self.assertIsNone(c["iTLB-load-misses"])
        self.assertNotIn("cycles:u", c)

    def test_hybrid_cpu_counts_per_core_type(self):
        # Alder Lake (perf 6.x): one line per core type, named pmu/event/modifiers;
        # a process pinned to a P-core counts on cpu_core only.
        c = perfstat.parse_perf_stat(HYBRID_OUTPUT)
        self.assertEqual(c["cycles"], 243314.0)
        self.assertEqual(c["instructions"], 135688.0)
        self.assertEqual(c["L1-dcache-load-misses"], 1441.0)
        self.assertNotIn("cpu_core/cycles/u", c)

    def test_hybrid_count_is_that_of_the_core_type_the_process_ran_on(self):
        # Real desktop output (perf 7.3) of a run that spent 0.19 ms on an E-core
        # before taskset pinned it: perf scales each core type's count from the
        # time it ran on that type to the whole run, so the atom line is an
        # extrapolation (~1e5 times its real count), not something to add.
        c = perfstat.parse_perf_stat(
            "28772835727,,cpu_atom/cycles/u,190343,0.00,,\n"
            "216629171763,,cpu_core/cycles/u,60408451421,99.00,,\n"
            "8288364102,,cpu_atom/instructions/u,190343,0.00,,\n"
            "308062957235,,cpu_core/instructions/u,60408451421,99.00,,\n")
        self.assertEqual(c["cycles"], 216629171763.0)
        self.assertEqual(c["instructions"], 308062957235.0)

    def test_hybrid_line_order_does_not_matter(self):
        c = perfstat.parse_perf_stat("250,,cpu_core/cycles/u,900,99.00,,\n"
                                     "100,,cpu_atom/cycles/u,1,0.00,,\n")
        self.assertEqual(c["cycles"], 250.0)

    def test_hybrid_counter_counted_on_no_core_type_is_none(self):
        c = perfstat.parse_perf_stat("<not counted>,,cpu_atom/cycles/u,0,0.00,,\n"
                                     "<not supported>,,cpu_core/cycles/u,0,0.00,,\n")
        self.assertIsNone(c["cycles"])


class Resume(unittest.TestCase):
    # A first run that fails (e.g. perf refused on a new host) leaves a file
    # holding only the header; resuming must not write a second one, which
    # report() would later read as a data row.
    def test_resume_after_header_only_file_writes_no_second_header(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "runs.csv"
            done, fh, w = perfstat.open_runs(out)
            fh.close()
            done, fh, w = perfstat.open_runs(out)
            self.assertEqual(done, set())
            fh.close()
            self.assertEqual(out.read_text().count("workload,variant"), 1)

    def test_resume_returns_the_runs_done_and_appends(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "runs.csv"
            done, fh, w = perfstat.open_runs(out)
            w.writerow({"workload": "w", "variant": "dropin", "engine": "mixmax", "rep": 0})
            fh.close()
            done, fh, w = perfstat.open_runs(out)
            fh.close()
            self.assertEqual(done, {("w", "dropin", "mixmax", "0")})
            self.assertEqual(out.read_text().count("workload,variant"), 1)


class PerfCommand(unittest.TestCase):
    def test_perf_is_pinned_with_the_workload(self):
        # perf outside taskset lets the forked child run unpinned (on a hybrid
        # CPU possibly on another core type) until taskset sets its affinity.
        cmd = perfstat.perf_command("2", "cycles:u,instructions:u", "/t/perf.txt")
        self.assertEqual(cmd[:4], ["taskset", "-c", "2", "perf"])
        self.assertEqual(cmd[-1], "--")
        self.assertIn("cycles:u,instructions:u", cmd)
        self.assertEqual(cmd[cmd.index("-o") + 1], "/t/perf.txt")


HYBRID_OUTPUT = """<not counted>,,cpu_atom/cycles/u,0,0.00,,
243314,,cpu_core/cycles/u,225079,100.00,,
<not counted>,,cpu_atom/instructions/u,0,0.00,,
135688,,cpu_core/instructions/u,225079,100.00,,
<not counted>,,cpu_atom/branch-misses/u,0,0.00,,
2558,,cpu_core/branch-misses/u,225079,100.00,,
<not supported>,,cpu_atom/L1-dcache-load-misses/u,0,100.00,,
1441,,cpu_core/L1-dcache-load-misses/u,225079,100.00,,
"""


def row(variant, engine, rep, events, **counters):
    r = {"workload": "w", "variant": variant, "engine": engine, "rep": str(rep),
         "events": str(events)}
    r.update({k.replace("_", "-"): str(v) for k, v in counters.items()})
    return r


class PerDraw(unittest.TestCase):
    def test_paired_difference_per_draw(self):
        # 10 draws per event; per event the engine saves 100 cycles in rep 0
        # and 120 in rep 1 (different event counts: per-event normalization),
        # and 30 instructions: -11 cycles and -3 instructions per draw.
        rows = [row("dropin", "mixmax", 0, 100, cycles=100000, instructions=50000),
                row("dropin", "xoshiro256pp", 0, 100, cycles=90000, instructions=47000),
                row("dropin", "mixmax", 1, 200, cycles=200000, instructions=100000),
                row("dropin", "xoshiro256pp", 1, 200, cycles=176000, instructions=94000)]
        d = perfstat.per_draw_deltas(rows, "w", ("dropin", "xoshiro256pp"), ("dropin", "mixmax"), 10)
        self.assertAlmostEqual(d["cycles"], -11.0)
        self.assertAlmostEqual(d["instructions"], -3.0)

    def test_missing_counter_is_none(self):
        rows = [row("dropin", "mixmax", 0, 100, cycles=100000),
                row("dropin", "xoshiro256pp", 0, 100, cycles=90000)]
        rows[0]["L1-icache-load-misses"] = ""
        rows[1]["L1-icache-load-misses"] = ""
        d = perfstat.per_draw_deltas(rows, "w", ("dropin", "xoshiro256pp"), ("dropin", "mixmax"), 10)
        self.assertAlmostEqual(d["cycles"], -10.0)
        self.assertIsNone(d["L1-icache-load-misses"])


def timed(variant, engine, rep, real_s, cycles, workload="w"):
    r = row(variant, engine, rep, 100, cycles=cycles, instructions=cycles)
    r["workload"], r["real_s"] = workload, str(real_s)
    return r


class Screen(unittest.TestCase):
    # On a fixed-frequency core, whole-process cycles per event-loop second are
    # constant to ~1%; a run whose rate is 18% off was miscounted (or ran at
    # another clock) and must not enter the comparisons.
    ROWS = [timed("dropin", "mixmax", 0, 60.0, 270e9), timed("dropin", "xoshiro256pp", 0, 58.0, 261e9),
            timed("dropin", "mixmax", 1, 61.0, 274e9), timed("dropin", "xoshiro256pp", 1, 58.5, 216e9),
            timed("dropin", "mixmax", 2, 60.5, 272e9), timed("dropin", "xoshiro256pp", 2, 58.2, 262e9),
            timed("dropin", "mixmax", 0, 10.0, 30e9, workload="v")]

    def test_run_with_anomalous_cycle_rate_is_dropped(self):
        kept, dropped = perfstat.screen(self.ROWS)
        self.assertEqual([(r["variant"], r["engine"], r["rep"]) for r in dropped],
                         [("dropin", "xoshiro256pp", "1")])
        self.assertEqual(len(kept), len(self.ROWS) - 1)

    def test_rate_is_compared_within_a_workload(self):
        # workload v runs at 3e9 cycles/s, 34% below w's 4.5e9: not an anomaly
        kept, _ = perfstat.screen(self.ROWS)
        self.assertIn("v", {r["workload"] for r in kept})

    def test_report_lists_dropped_runs_and_pairs_without_them(self):
        text = perfstat.report(self.ROWS, {"w": 10})
        self.assertIn("w dropin xoshiro256pp rep 1", text)
        eng = [l for l in text.splitlines() if l.startswith("| dropin xoshiro256pp |")][0]
        self.assertTrue(eng.endswith("| 2 |"), eng)


if __name__ == "__main__":
    unittest.main()


class ReportOnly(unittest.TestCase):
    # scripts/reanalyze.sh rewrites perfstat.md from the recorded runs on a
    # machine without Geant4: nothing may be run, even if configurations of
    # the default list are missing.
    def test_report_only_writes_the_report_without_running(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "perfstat").mkdir()
            rows = [row("dropin", "mixmax", r, 100, cycles=100000, instructions=50000) for r in range(2)]
            rows += [row("dropin", "mwc192x", r, 100, cycles=90000, instructions=47000) for r in range(2)]
            for r in rows:
                r["real_s"] = "10.0"
            with open(d / "perfstat" / "runs.csv", "w") as f:
                f.write(",".join(perfstat.COLUMNS) + "\n")
                for r in rows:
                    f.write(",".join(r.get(c, "") for c in perfstat.COLUMNS) + "\n")
            (d / "counts.csv").write_text("mode,workload,events,flat,flatArray,setSeeds,getTheEngine\n"
                                          "st,w,10,1000,0,1,1000\n")
            perfstat.main(["--report-only", str(d)])
            text = (d / "perfstat.md").read_text()
            self.assertIn("dropin mwc192x", text)
            self.assertNotIn("fast-xoshiro256pp", text)
