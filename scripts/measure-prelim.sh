#!/bin/bash
# Benchmarks, counts, profiles and an event-count calibration pilot, in order.
# Usage: scripts/measure-prelim.sh <results-dir>. Run on the build host, idle.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
dir=${1:?results-dir}
mkdir -p "$dir"
rm -f "$dir/bench.csv"
"$repo/scripts/bench.sh" "$dir/bench.csv"
"$repo/scripts/count.sh" "$dir"
"$repo/scripts/profile.sh" "$dir"
rm -f "$dir/calib/runs.csv"
python3 "$repo/scripts/run.py" run --mode st --variants dropin --engines mixmax \
  --workloads testem3 b4hadr testem11 opnovice2 range --reps 2 --event-scale 0.34 \
  --out "$dir/calib/runs.csv"
python3 "$repo/scripts/run.py" run --mode mt --variants dropin --engines mixmax \
  --workloads testem3 b4hadr testem11 opnovice2 range --reps 2 --event-scale 0.5 \
  --out "$dir/calib/runs.csv"
echo PRELIM-DONE
