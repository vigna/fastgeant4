#!/usr/bin/env python3
"""Hardware counters per engine (perf stat, user space): where a generator's
in-situ saving comes from. Runs single-threaded workloads as scripts/run.py
does (same macros, seeds and CPU) under perf stat, for each configuration and
rep, into <dir>/perfstat/runs.csv (resumable; perf's own output in
<dir>/perfstat/raw/), and writes <dir>/perfstat.md:
per workload and configuration, against the reference configuration, the
change per event of cycles and instructions, and the change per draw (draws
from <dir>/counts.csv) of every counter. The counters cover the whole process;
initialization is the same in every configuration of a binary and cancels in
the differences. Configurations with the reference's engine run the same
events, so their differences are free of physics noise; other engines run
other events (other random numbers), whose cost varies by about the run-to-run
spread.

Usage: HOST=<host> scripts/perfstat.py <results-dir> [--workloads w...]
         [--configs variant:engine...] [--reps N] [--event-scale S]
"""

import argparse
import csv
import statistics
import tempfile
from pathlib import Path

import run

# Five counters: with the NMI watchdog's, six fit AMD's six counters unmultiplexed.
COUNTERS = ["cycles", "instructions", "branch-misses", "L1-icache-load-misses",
            "L1-dcache-load-misses"]
COLUMNS = ["workload", "variant", "engine", "rep", "events", "real_s"] + COUNTERS
REF = ("dropin", "mixmax")
CONFIGS = ["stock:mixmax", "dropin:mixmax", "dropin:xoshiro256pp", "dropin:mwc192x",
           "fast-mixmax:mixmax", "fast-xoshiro256pp:xoshiro256pp", "fast-mwc192x:mwc192x"]


def event_name(field):
    """The event of a perf stat -x, event field: cycles:u -> cycles, and on
    hybrid CPUs (one line per core type) cpu_core/cycles/u -> cycles."""
    if "/" in field:
        return field.split("/")[1]
    return field.split(":")[0]


def parse_perf_stat(text):
    """{event: count} from `perf stat -x,` output, modifiers (:u) dropped;
    None for counters not supported or not counted. On hybrid CPUs (one line
    per core type) the count is that of the type the process ran on longest:
    perf scales each type's count from the time the process ran on that type
    to the whole run, so a type it visited for a moment (an unpinned start)
    reports an extrapolation, not a count to add."""
    out, ran = {}, {}
    for line in text.splitlines():
        f = line.split(",")
        if line.startswith("#") or len(f) < 3:
            continue
        k = event_name(f[2])
        try:
            v = float(f[0])
        except ValueError:
            out.setdefault(k, None)
            continue
        t = float(f[3]) if len(f) > 3 and f[3] else 0.0
        if out.get(k) is None or t > ran[k]:
            out[k], ran[k] = v, t
    return out


def perf_command(cpus, events, stat):
    """perf stat, writing to `stat`, pinned to `cpus` with the process it runs
    (taskset inside perf would leave the forked child unpinned until it runs)."""
    return ["taskset", "-c", cpus, "perf", "stat", "-x,", "-o", str(stat), "-e", events, "--"]


def open_runs(out):
    """(runs done, file, csv writer) for appending to `out`: the runs already
    recorded as (workload, variant, engine, rep), and a header written if needed."""
    new = not out.exists() or out.stat().st_size == 0
    done = set() if new else {(r["workload"], r["variant"], r["engine"], r["rep"])
                              for r in csv.DictReader(open(out))}
    fh = open(out, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=COLUMNS)
    if new:  # not "if not done": a first run that failed leaves a header only
        w.writeheader()
    return done, fh, w


def _num(x):
    return float(x) if x not in (None, "") else None


def _paired(rows, workload, cfg, ref):
    def by_rep(c):
        return {r["rep"]: r for r in rows
                if r["workload"] == workload and (r["variant"], r["engine"]) == tuple(c)}
    a, b = by_rep(cfg), by_rep(ref)
    return [(a[k], b[k]) for k in sorted(set(a) & set(b), key=int)]


def per_draw_deltas(rows, workload, cfg, ref, draws):
    """Per counter: the mean over reps (paired) of counter per event of cfg
    minus that of ref, divided by the draws per event; None if missing."""
    pairs = _paired(rows, workload, cfg, ref)
    out = {}
    for k in COUNTERS:
        ds = []
        for x, y in pairs:
            u, v = _num(x.get(k)), _num(y.get(k))
            if u is None or v is None:
                ds = []
                break
            ds.append(u / int(x["events"]) - v / int(y["events"]))
        out[k] = statistics.mean(ds) / draws if ds else None
    return out


def per_event_change(rows, workload, cfg, ref, k):
    """Mean over reps of (k per event of cfg) / (k per event of ref) - 1, and its sd."""
    rs = [(_num(x.get(k)) / int(x["events"])) / (_num(y.get(k)) / int(y["events"])) - 1
          for x, y in _paired(rows, workload, cfg, ref)
          if _num(x.get(k)) is not None and _num(y.get(k)) is not None]
    if not rs:
        return None, None
    return statistics.mean(rs), (statistics.stdev(rs) if len(rs) > 1 else 0.0)


def draws_per_event(d):
    out = {}
    p = d / "counts.csv"
    if p.exists():
        for x in csv.DictReader(open(p)):
            if x["mode"] == "st":
                out[x["workload"]] = (int(x["flat"]) + int(x["flatArray"])) / int(x["events"])
    return out


def screen(rows, tol=0.03):
    """(kept, dropped): drops the runs whose whole-process cycles per second of
    event loop differ by more than tol from the median of their workload. At a
    fixed clock the rate is constant to ~1% (the configurations change the
    event loop by a few per cent, the initialization not at all); a run outside
    lost counts, or ran at another clock."""
    def rate(r):
        c = _num(r.get("cycles"))
        return c / float(r["real_s"]) if c is not None and float(r["real_s"]) > 0 else None
    med = {w: statistics.median(x for x in (rate(r) for r in rows if r["workload"] == w)
                                if x is not None)
           for w in {r["workload"] for r in rows if rate(r) is not None}}
    kept, dropped = [], []
    for r in rows:
        x = rate(r)
        (dropped if x is not None and abs(x / med[r["workload"]] - 1) > tol else kept).append(r)
    return kept, dropped


def report(rows, draws):
    def f(v, fmt):
        return "–" if v is None else fmt.format(v)
    rows, dropped = screen(rows)
    lines = ["## Hardware counters against drop-in MIXMAX (perf stat, user space)", "",
             "Per event: mean change (± sd over reps). Per draw: mean change of the counter "
             "per event divided by the draws per event (counts.csv).", ""]
    if dropped:
        lines += ["Dropped (cycles per event-loop second more than 3% from the workload's "
                  "median: lost counts or another clock):"] + \
                 [f"- {r['workload']} {r['variant']} {r['engine']} rep {r['rep']}: "
                  f"{_num(r['cycles']) / float(r['real_s']) / 1e9:.3f} G/s" for r in dropped] + [""]
    for w in sorted({r["workload"] for r in rows}):
        n = draws.get(w)
        lines += [f"### {w} ({f(n, '{:.4g}')} draws/event)", "",
                  "| configuration | cycles/event | instructions/event | IPC | "
                  "cycles/draw | instr./draw | branch-misses/draw | L1i misses/draw | "
                  "L1d misses/draw | reps |",
                  "|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
        for cfg in sorted({(r["variant"], r["engine"]) for r in rows if r["workload"] == w}):
            pairs = _paired(rows, w, cfg, REF)
            mine = [x for x, _ in pairs]
            ipc = statistics.mean(_num(x["instructions"]) / _num(x["cycles"]) for x in mine) \
                if mine and all(_num(x.get("instructions")) and _num(x.get("cycles"))
                                for x in mine) else None
            cyc, cyc_sd = per_event_change(rows, w, cfg, REF, "cycles")
            ins, ins_sd = per_event_change(rows, w, cfg, REF, "instructions")
            d = per_draw_deltas(rows, w, cfg, REF, n) if n else {k: None for k in COUNTERS}
            pct = (lambda m, s: "–" if m is None else f"{m * 100:+.2f}% ± {s * 100:.2f}")
            lines.append(f"| {cfg[0]} {cfg[1]} | {pct(cyc, cyc_sd)} | {pct(ins, ins_sd)} | "
                         f"{f(ipc, '{:.3f}')} | " +
                         " | ".join(f(d[k], "{:+.2f}") for k in COUNTERS) + f" | {len(pairs)} |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir")
    ap.add_argument("--report-only", action="store_true",
                    help="rewrite perfstat.md from the recorded runs, running nothing")
    ap.add_argument("--workloads", nargs="+", default=["opnovice2", "testem3"])
    ap.add_argument("--configs", nargs="+", default=CONFIGS)
    ap.add_argument("--reps", type=int, default=4)
    ap.add_argument("--event-scale", type=float, default=None)
    args = ap.parse_args(argv)
    d = Path(args.dir)
    if args.report_only:
        rows = list(csv.DictReader(open(d / "perfstat" / "runs.csv")))
        (d / "perfstat.md").write_text(report(rows, draws_per_event(d)) + "\n")
        return
    host = run.load_host(run.default_host())
    workloads = run.load_workloads()
    scale = args.event_scale if args.event_scale is not None \
        else run.default_event_scale(host, "st")
    out = d / "perfstat" / "runs.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cpus, others = run.slot_cpus(host, "st", 0, 1)
    events_list = ",".join(c + ":u" for c in COUNTERS)
    done, fh, w = open_runs(out)
    with fh:
        for rep in range(args.reps):
            for name in args.workloads:
                wl = workloads[name]
                s1, s2 = run.seeds_for(name, rep)
                events = int(wl["events_st"] * scale)
                for variant, engine in (c.split(":") for c in args.configs):
                    if (name, variant, engine, str(rep)) in done:
                        continue
                    with tempfile.TemporaryDirectory(prefix="g4rng-perf-") as t:
                        stat = Path(t) / "perf.txt"
                        r = run.run_one(host, "st", name, wl, variant, engine, events, s1, s2,
                                        None, f"perf-{name}-{variant}-{engine}-{rep}", cpus,
                                        others, perf_command(cpus, events_list, stat))
                        text = stat.read_text()
                        c = parse_perf_stat(text)
                    (out.parent / "raw").mkdir(exist_ok=True)
                    (out.parent / "raw" / f"{name}-{variant}-{engine}-{rep}.txt").write_text(text)
                    w.writerow({"workload": name, "variant": variant, "engine": engine,
                                "rep": rep, "events": r["events"], "real_s": r["real_s"],
                                **{k: ("" if c.get(k) is None else int(c[k])) for k in COUNTERS}})
                    fh.flush()
                    print(f"perf {name} {variant} {engine} {rep}: real={r['real_s']:.3f}s "
                          + " ".join(f"{k}={c.get(k)}" for k in COUNTERS[:2]), flush=True)
    rows = list(csv.DictReader(open(out)))
    text = report(rows, draws_per_event(d))
    (d / "perfstat.md").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
