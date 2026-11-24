#!/bin/bash
# The measurement campaign on one host, resumable (run.py skips runs already
# in the CSV): physics pre-check (4 engines on the drop-in build, reduced
# events), ST and MT campaigns with R = 5, analysis, then the ST campaign
# extended to R = 10 and the analysis again. Prints a marker line after each
# stage. The pre-check does not stop the campaign: its flags are judged by
# hand; `run.py check` on the campaign data is the full check (Welch t tests,
# family-wise at 1% over the distinct comparisons, and build identity).
# Usage: scripts/campaign.sh <results dir>    (run on the build host)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
R=${1:?results dir}
W="testem3 b4hadr testem11 opnovice2 range"
V="dropin fast-mixmax fast-xoshiro256pp fast-mwc192x dropin-layout-name dropin-layout-noreorder"

python3 scripts/run.py run --mode st --variants dropin --workloads $W --reps 5 \
  --event-scale 0.1 --out "$R/physics/runs.csv"
python3 scripts/run.py run --mode mt --variants dropin --workloads $W --reps 5 \
  --event-scale 0.25 --out "$R/physics/runs.csv"
python3 scripts/run.py check "$R/physics/runs.csv" > "$R/physics/check.txt" || true
echo "PHYSICS-DONE $(tail -1 "$R/physics/check.txt")"

python3 scripts/run.py run --mode st --variants $V --workloads $W --reps 5 --out "$R/runs.csv"
echo ST5-DONE
python3 scripts/run.py run --mode mt --variants $V --workloads $W --reps 5 --out "$R/runs.csv"
echo MT5-DONE
python3 scripts/analyze.py "$R" || echo ANALYZE-FAILED
python3 scripts/run.py check "$R/runs.csv" > "$R/check.txt" || true
echo "ANALYSIS5-DONE $(tail -1 "$R/check.txt")"

python3 scripts/run.py run --mode st --variants $V --workloads $W --reps 10 --out "$R/runs.csv"
echo ST10-DONE
python3 scripts/analyze.py "$R" || echo ANALYZE-FAILED
python3 scripts/run.py check "$R/runs.csv" > "$R/check.txt" || true
echo "CAMPAIGN-DONE $(tail -1 "$R/check.txt")"
