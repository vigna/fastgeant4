#!/bin/bash
# Counts out-of-line calls to HepRandom::getTheEngine() in libG4processes_core.so
# and shows the code of a G4UniformRand() site in G4KleinNishinaCompton::SampleSecondaries.
# Usage: scripts/check-callpath.sh <variant> [expected-count]. Run on the build host.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variant=${1:?variant}
lib=$ROOT/install-$variant/lib64/libG4processes_core.so
dis=$(mktemp)
objdump -d --no-show-raw-insn -C "$lib" > "$dis"
n=$(grep -c 'call.*<CLHEP::HepRandom::getTheEngine()@plt>' "$dis" || true)
echo "$variant: $n calls to getTheEngine()@plt"
awk '/<G4KleinNishinaCompton::SampleSecondaries.*>:$/,/^$/' "$dis" | grep -m1 -B4 -A14 '%fs:' || true
rm -f "$dis"
if [ $# -ge 2 ]; then
  [ "$n" = "$2" ] && echo "CALLPATH OK" || { echo "CALLPATH FAIL (want $2)"; exit 1; }
fi
