#!/bin/bash
# Runs a campaign as N parallel slots (scripts/run.py --slot k --slots N): slot
# k runs the reps r with r % N == k, pinned to its own CPUs (ST_CPUS or
# MT_SLOT_CPUS of the host), into <dir>/runs-<mode>-<k>.csv; resumable. Use it
# only where scripts/interference.sh shows that the slots do not slow each
# other. Prints SLOTS-DONE <mode> or SLOTS-FAILED.
# Usage: HOST=<host> scripts/campaign-slots.sh <dir> st|mt <slots> <reps> [variant...]
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
dir=${1:?dir}; mode=${2:?mode}; n=${3:?slots}; reps=${4:?reps}; shift 4
V=("$@")
[ ${#V[@]} -gt 0 ] || V=(stock dropin fast-mixmax fast-xoshiro256pp fast-mwc192x
                         dropin-layout-name dropin-layout-noreorder)
W=(testem3 b4hadr testem11 opnovice2 range)
mkdir -p "$dir"
pids=()
for k in $(seq 0 $((n - 1))); do
  python3 scripts/run.py run --mode "$mode" --variants "${V[@]}" --workloads "${W[@]}" \
    --reps "$reps" --slot "$k" --slots "$n" --out "$dir/runs-$mode-$k.csv" \
    > "$dir/slot-$mode-$k.log" 2>&1 & pids+=($!)
done
fail=0; for p in "${pids[@]}"; do wait "$p" || fail=1; done
if [ $fail = 0 ]; then echo "SLOTS-DONE $mode"; else echo "SLOTS-FAILED $mode (see $dir/slot-$mode-*.log)"; exit 1; fi
