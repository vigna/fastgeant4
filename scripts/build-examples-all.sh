#!/bin/bash
# Builds the five workload examples for every installed variant (in parallel per variant).
# Usage: scripts/build-examples-all.sh [variant...]. Run on the build host.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variants=("$@")
[ ${#variants[@]} -gt 0 ] || variants=(stock dropin dropin-layout-name dropin-layout-noreorder \
  fast-mixmax fast-xoshiro256pp fast-mwc192x)
exs=$(python3 -c "import json; print(' '.join(w['example'] for w in json.load(open('$repo/workloads/workloads.json')).values()))")
# Prepare the patched examples copy once, before the parallel builds.
"$repo/scripts/build-examples.sh" "${variants[0]}" $exs
pids=()
for v in "${variants[@]:1}"; do
  "$repo/scripts/build-examples.sh" "$v" $exs > "$ROOT/logs/examples-$v.log" 2>&1 & pids+=($!)
done
fail=0; for p in "${pids[@]}"; do wait "$p" || fail=1; done
[ $fail = 0 ] && echo ALL-EXAMPLES-DONE || { echo EXAMPLES-FAILED; exit 1; }
