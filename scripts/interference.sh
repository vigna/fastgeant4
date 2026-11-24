#!/bin/bash
# Do parallel slots slow each other? Runs the same reps (same seeds, hence the
# same physics) twice on each slot's CPUs: first each slot alone, one slot at a
# time, then all slots at once. The per-rep ratio parallel/alone, on the same
# CPUs, is the slowdown due to the neighbours; its spread is the added noise.
# Prints SLOTS-CLEAN yes|no (analyze.interference_verdict: no slowdown of 2% or
# more, no added noise) before INTERFERENCE-DONE.
# Usage: HOST=<host> scripts/interference.sh <dir> st|mt <slots> <event-scale> <workload>...
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
dir=${1:?dir}; mode=${2:?mode}; n=${3:?slots}; scale=${4:?event scale}; shift 4
args=(--mode "$mode" --variants dropin --engines mixmax --workloads "$@" --reps $((2 * n))
      --event-scale "$scale")
for k in $(seq 0 $((n - 1))); do
  python3 scripts/run.py run "${args[@]}" --slot "$k" --slots "$n" --out "$dir/alone-$k.csv"
done
pids=()
for k in $(seq 0 $((n - 1))); do
  python3 scripts/run.py run "${args[@]}" --slot "$k" --slots "$n" \
    --out "$dir/parallel-$k.csv" > "$dir/parallel-$k.log" 2>&1 & pids+=($!)
done
fail=0; for p in "${pids[@]}"; do wait "$p" || fail=1; done
[ $fail = 0 ] || { echo "INTERFERENCE-FAILED (see $dir/parallel-*.log)"; exit 1; }
python3 - "$dir" <<'PY'
import csv, statistics, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import analyze
d = Path(sys.argv[1])
rows = []
for kind in ("alone", "parallel"):
    for p in sorted(d.glob(f"{kind}-*.csv")):
        for r in csv.DictReader(open(p)):
            r["variant"] = kind
            rows.append(r)
for mode, w in sorted({(r["mode"], r["workload"]) for r in rows}):
    res = analyze.compare(rows, (mode, w), ("parallel", "mixmax"), ("alone", "mixmax"))
    a = analyze.by_rep(rows, (mode, w), ("alone", "mixmax"))
    p = analyze.by_rep(rows, (mode, w), ("parallel", "mixmax"))
    ratios = [p[r] / a[r] for r in sorted(set(a) & set(p), key=int)]
    print(f"{mode} {w}: parallel/alone = {res['ratio']:.4f} [{res['lo']:.4f}, {res['hi']:.4f}], "
          f"ratio sd {statistics.stdev(ratios) * 100:.2f}%, n = {res['n']}")
print("SLOTS-CLEAN", "yes" if analyze.interference_verdict(rows)["clean"] else "no")
PY
echo INTERFERENCE-DONE
