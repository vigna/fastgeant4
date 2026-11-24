#!/bin/bash
# Builds everything on a fresh host (after scripts/setup-host.sh): the stock
# build, the Geant4 datasets (downloaded from CERN by geant4-config, in parallel
# with the other builds), the six study variants and the five workloads for
# all seven builds. Logs in $ROOT/logs; prints BUILD-HOST-DONE at the end.
# Usage: HOST=<host> scripts/build-host.sh   (run on the host)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:?set HOST}.env"
export HOST
mkdir -p "$ROOT/logs"
"$repo/scripts/build.sh" stock
"$ROOT/install-stock/bin/geant4-config" --install-datasets > "$ROOT/logs/datasets.log" 2>&1 &
datasets=$!
"$repo/scripts/build-all.sh"
"$repo/scripts/build-examples-all.sh"
wait $datasets || { echo "DATASETS-FAILED (see $ROOT/logs/datasets.log)"; exit 1; }
echo BUILD-HOST-DONE
