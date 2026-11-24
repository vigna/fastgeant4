#!/bin/bash
# Counts draws and reseedings per event (drop-in build, G4RNG_ENGINE=count:mixmax),
# single- and multithreaded, and the calls of HepRandom::getTheEngine() (an
# LD_PRELOAD shim, bench/count_getengine.cc: the draws through the static path,
# G4UniformRand() and engine-less shoot(), as opposed to cached engine pointers);
# writes <dir>/counts.csv (mode,workload,events,flat,flatArray,setSeeds,getTheEngine).
# Usage: scripts/count.sh <results-dir> [workload...]. Run on the build host.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
dir=${1:?results-dir}; shift
wl=("$@"); [ ${#wl[@]} -gt 0 ] || wl=(testem3 b4hadr testem11 opnovice2 range)
source "$repo/hosts/${HOST:-desktop}.env"
mkdir -p "$dir/count" "$ROOT/bench-dropin"
shim=$ROOT/bench-dropin/libcountgetengine.so
g++ -std=c++17 -O2 -shared -fPIC "$repo/bench/count_getengine.cc" -o "$shim" -ldl
export LD_PRELOAD=$shim
for mode in st mt; do
  python3 "$repo/scripts/run.py" run --mode $mode --variants dropin --engines count:mixmax \
    --workloads "${wl[@]}" --reps 1 --event-scale 0.1 --no-warmup --busy-limit 99 \
    --out "$dir/count/runs.csv"
done
python3 - "$dir" <<'PY'
import csv, gzip, re, sys
from pathlib import Path
d = Path(sys.argv[1])
rows = list(csv.DictReader(open(d / "count" / "runs.csv")))
with open(d / "counts.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["mode", "workload", "events", "flat", "flatArray", "setSeeds", "getTheEngine"])
    for r in rows:
        tag = f"{r['mode']}-{r['workload']}-{r['variant']}-{r['engine']}-{r['rep']}"
        err = gzip.open(d / "count" / "logs" / f"{tag}.err.gz", "rt").read()
        m = re.search(r"^G4RNG-COUNT flat=(\d+) flatArray=(\d+) setSeeds=(\d+)$", err, re.M)
        if not m:
            sys.exit(f"no G4RNG-COUNT line for {tag}")
        g = re.search(r"^G4RNG-COUNT getTheEngine=(\d+)$", err, re.M)
        if not g:
            sys.exit(f"no getTheEngine count for {tag}")
        w.writerow([r["mode"], r["workload"], r["events"], *m.groups(), g.group(1)])
print(open(d / "counts.csv").read())
PY
unset LD_PRELOAD
