#!/bin/bash
# Recomputes everything derived from the raw data under results/: the physics
# checks (check.txt), the analyses (summary.md), the hardware-counter reports
# (perfstat.md) and the results page (docs/index.html); then shows what
# differs from the committed files. Nothing should: the published numbers
# follow from the published runs. Needs Python 3 only (no Geant4).
# Usage: scripts/reanalyze.sh
set -euo pipefail
cd "$(dirname "$0")/.."
for d in results/*/*/; do
  d=${d%/}
  host=$(basename "$(dirname "$d")")
  csvs=("$d"/runs*.csv)
  if [ -e "${csvs[0]}" ]; then
    HOST=$host python3 scripts/run.py check "${csvs[@]}" > "$d/check.txt" || true  # verdict in its last line
    HOST=$host python3 scripts/analyze.py "$d" > /dev/null
    echo "$d: $(tail -1 "$d/check.txt")"
  fi
  if [ -f "$d/perfstat/runs.csv" ]; then
    python3 scripts/perfstat.py --report-only "$d"
    echo "$d: perfstat.md"
  fi
done
python3 scripts/build_site.py > /dev/null
echo "docs/index.html"
if git diff --quiet -- results docs; then
  echo "REANALYZE: every derived file reproduces the committed one exactly"
else
  git diff --stat -- results docs
  echo "REANALYZE: the files above differ from the committed ones"
  exit 1
fi
