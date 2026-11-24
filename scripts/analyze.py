#!/usr/bin/env python3
"""Analysis of a Geant4 PRNG study campaign.

    analyze.py <results-dir>     # reads runs*.csv (+ bench.csv and counts.csv
                                 # if present), writes summary.md

Times are event-loop real time per event. Runs are paired by repetition:
the runs of a repetition use the same seeds and run back to back, so a
comparison of configuration C with reference R takes one ratio t_C / t_R per
repetition present in both, and reports their geometric mean (below 1 means
C is faster), the speedup 1/ratio - 1, and a 95% Student-t confidence
interval on the mean log ratio. A difference is significant when the
interval excludes 1; for comparisons across binaries, when it excludes
[1 - band, 1 + band], where band is the layout-noise band: the largest
deviation from drop-in MIXMAX of a drop-in replicate built with a different
code layout and running identical code.

Before the analysis, runs that lost CPU to other processes are screened out
(screen()): ST runs whose process CPU time is below 99% of their real time,
MT runs whose CPU utilization is more than 2% below the median of their
workload, and runs during which other processes loaded the pinned CPUs'
hyperthread siblings, the host, or the hypervisor (columns recorded by the
runner since 2026-11-23). They are listed in the summary.
"""

import csv
import math
import statistics
import sys
from pathlib import Path

ENGINES = ["mixmax", "xoshiro256pp", "mwc192x"]
NEW = ["xoshiro256pp", "mwc192x"]
REF = ("dropin", "mixmax")
STOCK = ("stock", "mixmax")


def load(f):
    return list(csv.DictReader(f))


def load_dir(d):
    """The runs of a results directory: every runs*.csv in it (one per
    parallel slot, or a single runs.csv), not those of subdirectories."""
    rows = []
    for p in sorted(Path(d).glob("runs*.csv")):
        with open(p) as f:
            rows += load(f)
    return rows


# 97.5% quantiles of Student's t with 1..30 degrees of freedom.
T975 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def t975(df):
    if df <= len(T975):
        return T975[df - 1]
    z = 1.959964  # Cornish-Fisher expansion, error < 1e-3 for df > 30
    return z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)


def by_rep(rows, key, cfg):
    """Time per event of each repetition of `cfg`, keyed by repetition."""
    mode, workload = key
    variant, engine = cfg
    return {r["rep"]: float(r["real_s"]) / int(r["events"]) for r in rows
            if r["mode"] == mode and r["workload"] == workload
            and r["variant"] == variant and r["engine"] == engine}


def cpu_s(r):
    return float(r["user_s"]) + float(r["sys_s"])


def screen(rows, st_min=0.99, mt_rel=0.98):
    """Runs that lost CPU to other processes: ST runs with CPU time below
    st_min of real time; MT runs with utilization below mt_rel times the
    median utilization of their workload; and, when the runner recorded
    them, runs during which the idle hyperthread siblings of the pinned CPUs
    were busy more than 5% of the time, the hypervisor stole more than 0.05
    CPUs, or other processes used more than one CPU. Rows without CPU times
    pass."""
    timed = [r for r in rows if r.get("user_s") not in (None, "")]
    util = {}
    for r in timed:
        if r["mode"] == "mt":
            util.setdefault(r["workload"], []).append(cpu_s(r) / float(r["real_s"]))
    median = {w: statistics.median(u) for w, u in util.items()}
    flagged = []
    for r in timed:
        u = cpu_s(r) / float(r["real_s"])
        if (r["mode"] == "st" and u < st_min) or \
           (r["mode"] == "mt" and u < mt_rel * median[r["workload"]]) or \
           float(r.get("sibling_busy") or 0) > 0.05 or \
           float(r.get("steal_cpus") or 0) > 0.05 or \
           float(r.get("foreign_cpus") or 0) > 1.0:
            flagged.append(r)
    return flagged


def drop_flagged(rows, flagged):
    ids = {id(r) for r in flagged}
    return [r for r in rows if id(r) not in ids]


def per_event(rows, key, cfg):
    mode, workload = key
    variant, engine = cfg
    return [float(r["real_s"]) / int(r["events"]) for r in rows
            if r["mode"] == mode and r["workload"] == workload
            and r["variant"] == variant and r["engine"] == engine]


def compare(rows, key, cfg, ref, layout_band=0.0):
    """Paired comparison of `cfg` with `ref` (see the module docstring)."""
    a, b = by_rep(rows, key, cfg), by_rep(rows, key, ref)
    reps = sorted(set(a) & set(b), key=int)
    if len(reps) < 2:
        return None
    d = [math.log(a[r] / b[r]) for r in reps]
    n = len(d)
    m = statistics.fmean(d)
    h = t975(n - 1) * statistics.stdev(d) / math.sqrt(n)
    ratio, lo, hi = math.exp(m), math.exp(m - h), math.exp(m + h)
    significant = hi < 1 - layout_band or lo > 1 + layout_band
    ref_t = [b[r] for r in reps]
    return {"ratio": ratio, "lo": lo, "hi": hi, "significant": significant,
            "speedup_pct": (1 / ratio - 1) * 100, "n": n, "n_ref": n,
            "cv_ref": statistics.stdev(ref_t) / statistics.fmean(ref_t)}


def pitman_morgan_t(x, y):
    """Pitman-Morgan statistic for var(x) = var(y) on paired samples: the t of
    the correlation of x - y with x + y (n - 2 df), positive when var(x) > var(y)."""
    d = [a - b for a, b in zip(x, y)]
    s = [a + b for a, b in zip(x, y)]
    n = len(d)
    md, ms = statistics.fmean(d), statistics.fmean(s)
    sxy = sum((a - md) * (b - ms) for a, b in zip(d, s))
    sxx = sum((a - md) ** 2 for a in d)
    syy = sum((b - ms) ** 2 for b in s)
    if sxx == 0 or syy == 0:
        return 0.0
    r = sxy / math.sqrt(sxx * syy)
    return r * math.sqrt((n - 2) / max(1e-300, 1 - r * r))


def interference_verdict(rows, max_slowdown=0.02, max_sd=0.01):
    """Whether parallel slots measure as runs alone do (scripts/interference.sh:
    rows of variant "alone" and "parallel", the same reps on the same CPUs).
    Clean when, for every workload:
    - the 95% interval of parallel/alone excludes a slowdown of max_slowdown
      or more: a small uniform slowdown, shared by every configuration of a
      rep, cancels in the paired ratios; a large one means another machine
      state (EC2's MT slots: 30%, a power limit);
    - the neighbours add no noise: the sd of the per-rep ratios is below
      max_sd, or the parallel runs do not vary across reps significantly more
      than the runs alone (one-sided Pitman-Morgan test at 2.5% on the log
      times, which share each rep's physics): some workloads jitter by ~1% at
      the same seed whatever runs beside them, which widens the ratios of
      both."""
    out = {}
    for key in sorted({(r["mode"], r["workload"]) for r in rows}):
        res = compare(rows, key, ("parallel", "mixmax"), ("alone", "mixmax"))
        a, p = by_rep(rows, key, ("alone", "mixmax")), by_rep(rows, key, ("parallel", "mixmax"))
        reps = sorted(set(a) & set(p), key=int)
        if res is None or len(reps) < 4:
            out[key] = {"clean": False}
            continue
        ratios = [p[r] / a[r] for r in reps]
        sd = statistics.stdev(ratios)
        pm = pitman_morgan_t([math.log(p[r]) for r in reps], [math.log(a[r]) for r in reps])
        out[key] = {"ratio": res["ratio"], "hi": res["hi"], "ratio_sd": sd, "pm_t": pm,
                    "clean": res["hi"] < 1 + max_slowdown and
                    (sd < max_sd or pm < t975(len(reps) - 2))}
    return {"workloads": out, "clean": bool(out) and all(v["clean"] for v in out.values())}


def layout_band(rows, key):
    """Largest |t_replicate / t_dropin_mixmax - 1| over the layout replicates."""
    variants = sorted({r["variant"] for r in rows if r["variant"].startswith("dropin-layout-")})
    devs = []
    for v in variants:
        res = compare(rows, key, (v, "mixmax"), REF)
        if res is not None:
            devs.append(abs(res["ratio"] - 1))
    return max(devs) if devs else None


def predict(flat_per_event, seeds_per_event, t_event_ns, bench, variant, engine):
    """Predicted speedup (%) of `engine` over MIXMAX on `variant`, from the
    numbers of draws and reseedings per event and the microbenchmark costs."""
    d_draw = bench[(variant, "mixmax", "G4UniformRand")] - bench[(variant, engine, "G4UniformRand")]
    d_seed = bench[(variant, "mixmax", "setSeeds")] - bench[(variant, engine, "setSeeds")]
    saved = flat_per_event * d_draw + seeds_per_event * d_seed
    return (t_event_ns / (t_event_ns - saved) - 1) * 100


def predicted(rows, mode, w, counts, bench, engine, variant="dropin"):
    """Predicted speedup (%) of `engine` on `variant` for workload w. The
    savings are CPU time, so in MT they are compared with the thread time
    per event (process CPU time / events), not with the wall time."""
    c = counts[(mode, w)]
    ref = [r for r in rows if r["mode"] == mode and r["workload"] == w
           and (r["variant"], r["engine"]) == REF]
    if mode == "mt":
        t = statistics.fmean(cpu_s(r) / int(r["events"]) for r in ref)
    else:
        t = statistics.fmean(float(r["real_s"]) / int(r["events"]) for r in ref)
    return predict(c["flat"], c["seeds"], t * 1e9, bench, variant, engine)


def prediction_table(rows, mode, workloads, counts, bench):
    lines = []
    for w in workloads:
        c = counts.get((mode, w))
        if c is None or not per_event(rows, (mode, w), REF):
            continue
        static = c.get("static")
        cells = [w, f"{c['flat']:.4g}",
                 f"{static / c['flat']:.0%}" if static is not None and c["flat"] else "–",
                 f"{c['seeds']:.3g}"]
        for e in NEW:
            try:
                pr = predicted(rows, mode, w, counts, bench, e)
            except KeyError:
                cells.append("–")
                continue
            res = compare(rows, (mode, w), ("dropin", e), REF)
            meas = f"{res['speedup_pct']:+.2f}%" if res else "–"
            cells.append(f"{pr:+.2f}% / {meas}")
        lines.append(cells)
    if not lines:
        return ""
    return table("Predicted / measured drop-in speedup (from counts and microbenchmarks)",
                 ["workload", "draws/event", "via getTheEngine", "reseeds/event"] + NEW,
                 lines)


def fmt(res):
    if res is None:
        return "–"
    mark = "" if res["significant"] else " (n.s.)"
    return (f"{res['speedup_pct']:+.2f}% [{(1 / res['hi'] - 1) * 100:+.2f}, "
            f"{(1 / res['lo'] - 1) * 100:+.2f}]{mark}")


def table(title, header, lines):
    out = [f"### {title}", "", "| " + " | ".join(header) + " |",
           "|" + "|".join([":--"] + ["--:"] * (len(header) - 1)) + "|"]
    out += ["| " + " | ".join(l) + " |" for l in lines]
    return "\n".join(out) + "\n"


def summarize(rows, extra="", counts=None, bench=None, flagged=()):
    out = []
    modes = [m for m in ("st", "mt") if any(r["mode"] == m for r in rows)]
    for mode in modes:
        workloads = list(dict.fromkeys(r["workload"] for r in rows if r["mode"] == mode))
        name = "Single-threaded" if mode == "st" else "Multithreaded"
        out.append(f"## {name}\n")
        noise, band_lines = [], []
        bands = {}
        stock = any(r["mode"] == mode and r["variant"] == "stock" for r in rows)
        for w in workloads:
            ref = per_event(rows, (mode, w), REF)
            band = layout_band(rows, (mode, w))
            bands[w] = band or 0.0
            line = [w, f"{statistics.fmean(ref) * 1e3:.4g}" if ref else "–",
                    f"{statistics.stdev(ref) / statistics.fmean(ref) * 100:.2f}%"
                    if len(ref) > 1 else "–",
                    f"{band * 100:.2f}%" if band is not None else "not measured",
                    str(len(ref))]
            if stock:  # the drop-in call path should be stock's: this should be n.s.
                line.append(fmt(compare(rows, (mode, w), STOCK, REF, bands[w])))
            noise.append(line)
        out.append(table("Reference and noise", ["workload", "drop-in MIXMAX ms/event",
                                                  "run-to-run CV", "layout band", "reps"] +
                         (["stock vs. drop-in MIXMAX"] if stock else []), noise))
        sections = [
            ("A. Drop-in engines vs. drop-in MIXMAX (same binary)",
             lambda w, e: compare(rows, (mode, w), ("dropin", e), REF)),
            ("B. Fast-path engines vs. fast-path MIXMAX (generator effect on the fast path)",
             lambda w, e: compare(rows, (mode, w), (f"fast-{e}", e), ("fast-mixmax", "mixmax"),
                                  bands[w])),
            ("Call path: fast path vs. drop-in, same engine",
             lambda w, e: compare(rows, (mode, w), (f"fast-{e}", e), ("dropin", e), bands[w])),
            ("Total: fast-path engine vs. drop-in MIXMAX",
             lambda w, e: compare(rows, (mode, w), (f"fast-{e}", e), REF, bands[w])),
        ]
        if stock:
            sections.append(("Total: fast-path engine vs. stock",
                             lambda w, e: compare(rows, (mode, w), (f"fast-{e}", e), STOCK,
                                                  bands[w])))
        for title, fn in sections:
            engines = ENGINES if title.startswith(("Call", "Total")) else NEW
            lines = [[w] + [fmt(fn(w, e)) for e in engines] for w in workloads]
            out.append(table(title, ["workload"] + engines, lines))
        if counts and bench:
            out.append(prediction_table(rows, mode, workloads, counts, bench))
    out.append("Speedups are 1/ratio − 1 of event-loop time per event (geometric mean of "
               "the ratios of runs paired by repetition), with 95% Student-t intervals; "
               "(n.s.) marks intervals that do not exclude no change (or, across binaries, "
               "the layout band). MT predictions compare the CPU time saved with the thread "
               "time per event. Predictions use the microbenchmark's time per call, which "
               "understates the in-situ cost of a draw: on a wide out-of-order core the "
               "benchmark loop overlaps successive calls (scripts/bench-instr.sh, "
               "scripts/perfstat.py: the instructions saved per draw agree, the cycles do "
               "not). xoshiro256pp and mwc192x are seeded by jumping (distinct seeds "
               "give non-overlapping streams, as MIXMAX's).\n")
    if flagged:
        out.append(table("Runs screened out (lost CPU to other processes)",
                         ["mode", "workload", "variant", "engine", "rep", "real s", "CPU s"],
                         [[r["mode"], r["workload"], r["variant"], r["engine"], r["rep"],
                           r["real_s"], f"{cpu_s(r):.2f}"] for r in flagged]))
    return "\n".join(out) + extra


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = Path(sys.argv[1])
    rows = load_dir(d)
    extra = ""
    counts, bench = {}, {}
    for name in ("bench.csv", "counts.csv"):
        p = d / name
        if p.exists():
            with open(p) as f:
                r = list(csv.reader(f))
            extra += "\n" + table(name, r[0], r[1:])
            with open(p) as f:
                for x in csv.DictReader(f):
                    if name == "bench.csv":
                        bench[(x["variant"], x["engine"], x["what"])] = float(x["ns"])
                    else:
                        ev = int(x["events"])
                        counts[(x["mode"], x["workload"])] = {
                            "flat": (int(x["flat"]) + int(x["flatArray"])) / ev,
                            "seeds": int(x["setSeeds"]) / ev}
                        if x.get("getTheEngine"):  # draws through the static path
                            counts[(x["mode"], x["workload"])]["static"] = \
                                int(x["getTheEngine"]) / ev
    flagged = screen(rows)
    text = summarize(drop_flagged(rows, flagged), extra, counts, bench, flagged)
    (d / "summary.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
