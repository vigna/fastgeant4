#!/usr/bin/env python3
"""Builds the results page, docs/index.html, from scripts/site.html.in and
the campaign data: every number on the page comes from the summary.md
tables, bench.csv, bench-instr.csv and perfstat.md files of the campaigns.

Usage: python3 scripts/build_site.py [--st DIR] [--mt DIR] [--perf FILE] [--threads N] [--out FILE]
(defaults: the published campaigns under results/, 96 threads, docs/index.html).
A page built from other data says so at its top: its text describes the
published results, its charts and tables the data given."""

import argparse
import csv
import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ST = REPO / "results/zen5/2026-11-24"         # single thread, 11 slots, R = 22
MT = REPO / "results/zen5-full/2026-11-24"    # 96 threads, R = 10
PERF = REPO / "results/zen5/2026-11-23/perfstat.md"
ENG = ["mwc192x", "xoshiro256pp", "mixmax"]
WL = ["testem3", "b4hadr", "testem11", "opnovice2", "range"]
CELL = re.compile(r"([+-]?[\d.]+)% \[([+-]?[\d.]+), ([+-]?[\d.]+)\]( \(n\.s\.\))?")


def tables(path):
    """{heading: {workload: {column: [value, lo, hi, not significant] or text}}}."""
    out, head, cols = {}, None, None
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("### "):
            head, cols = line[4:].strip(), None
            continue
        if not line.startswith("|") or line.startswith("|:"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cols is None:
            cols = cells
            continue
        row = {}
        for c, v in zip(cols[1:], cells[1:]):
            m = CELL.match(v)
            row[c] = [float(m[1]), float(m[2]), float(m[3]), bool(m[4])] if m else v
        out.setdefault(head, {})[cells[0]] = row
    return out


def pick(tab, cols=ENG):
    return {w: {e: tab[w][e] for e in cols if isinstance(tab.get(w, {}).get(e), list)} for w in WL}


def campaign(d):
    t = tables(d / "summary.md")
    return {
        "total": pick(t["Total: fast-path engine vs. stock"]),
        "dropin": pick(t["A. Drop-in engines vs. drop-in MIXMAX (same binary)"]),
        "callpath": pick(t["Call path: fast path vs. drop-in, same engine"]),
        "noise": {w: {"ms": r["drop-in MIXMAX ms/event"], "cv": r["run-to-run CV"], "band": r["layout band"],
                      "reps": r["reps"], "stock": r.get("stock vs. drop-in MIXMAX")}
                  for w, r in ((w, t["Reference and noise"][w]) for w in WL)},
    }


def perf(path):
    """{workload: {configuration: per-draw cycles, instructions, branch misses}}."""
    out, wl = {}, None
    for line in open(path):
        if line.startswith("### "):
            wl = line[4:].split()[0]
        elif line.startswith("| ") and not line.startswith("| configuration"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            out.setdefault(wl, {})[c[0]] = {"cyc": float(c[4]), "ins": float(c[5]), "bm": float(c[6])}
    return out


def bench(d):
    ns, ins = {}, {}
    for r in csv.DictReader(open(d / "bench.csv")):
        ns.setdefault((r["variant"], r["engine"]), {})[r["what"]] = float(r["ns"])
    for r in csv.DictReader(open(d / "bench-instr.csv")):
        if r["what"] == "G4UniformRand":
            ins[(r["variant"], r["engine"])] = (float(r["instructions"]), float(r["cycles"]))
    out = []
    for e in ENG:
        drop = ("stock", "mixmax") if e == "mixmax" else ("dropin", e)
        fast = ("fast-" + e, e)
        out.append({"e": e, "reseed": ns[drop]["setSeeds"], "nsDrop": ns[drop]["G4UniformRand"],
                    "nsFast": ns[fast]["G4UniformRand"], "insDrop": ins[drop][0], "cycDrop": ins[drop][1],
                    "insFast": ins[fast][0], "cycFast": ins[fast][1]})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--st", type=Path, default=ST, help="single-thread campaign directory")
    ap.add_argument("--mt", type=Path, default=MT, help="multithreaded campaign directory")
    ap.add_argument("--perf", type=Path, default=PERF, help="perfstat.md with the hardware counters")
    ap.add_argument("--threads", type=int, default=96, help="threads of the multithreaded campaign")
    ap.add_argument("--out", type=Path, default=REPO / "docs/index.html")
    a = ap.parse_args(argv)
    data = {"res": {"st": campaign(a.st), "mt": campaign(a.mt)}, "bench": bench(a.st),
            "perf": {"res": perf(a.perf)}, "threads": a.threads}
    notice = ""
    if (a.st.resolve(), a.mt.resolve(), a.perf.resolve(), a.threads) != (ST, MT, PERF, 96):
        notice = ('<p class="notice">Reproduction: the charts and tables show the runs in '
                  f"<code>{html.escape(str(a.st))}</code> and <code>{html.escape(str(a.mt))}</code> "
                  f"({a.threads} threads); the text describes the published results "
                  '(<a href="https://vigna.github.io/fastgeant4/">vigna.github.io/fastgeant4</a>).</p>')
    tpl = (REPO / "scripts/site.html.in").read_text()
    out = a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tpl.replace("/*DATA*/", json.dumps(data, separators=(",", ":"))).replace("<!--NOTICE-->", notice))
    print(out)


if __name__ == "__main__":
    main()
