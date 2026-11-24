#!/bin/bash
# After scripts/campaign.sh: extends the MT campaign to R = 10 (the spec asks for
# R >= 10 for every configuration; campaign.sh ran MT with R = 5), then analyzes.
# Waits for campaign.sh to finish; does nothing unless it printed CAMPAIGN-DONE.
# Usage: scripts/campaign-mt10.sh <results dir> <campaign log>   (on the build host)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
R=${1:?results dir}; log=${2:?campaign log}
while pgrep -f "bash scripts/campaign.sh" > /dev/null; do sleep 60; done
grep -q CAMPAIGN-DONE "$log" || { echo "MT10-ABORTED: campaign.sh did not finish"; exit 1; }
W="testem3 b4hadr testem11 opnovice2 range"
V="dropin fast-mixmax fast-xoshiro256pp fast-mwc192x dropin-layout-name dropin-layout-noreorder"
python3 scripts/run.py run --mode mt --variants $V --workloads $W --reps 10 --out "$R/runs.csv"
python3 scripts/analyze.py "$R" > /dev/null || echo ANALYZE-FAILED
python3 scripts/run.py check "$R/runs.csv" > "$R/check.txt" || true
echo "MT10-DONE $(tail -1 "$R/check.txt")"
