#!/bin/bash
# Runs the C++ tests on the build host against a Geant4 install.
# Usage: tests/run-tests.sh [install-variant] (default: stock). Run on the build host.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variant=${1:-stock}
inst=$ROOT/install-$variant
out=$ROOT/tests-$variant
mkdir -p "$out"
CXX="g++ -std=c++17 -O2 -Wall -Wextra"
if [ "$variant" = stock ]; then
  # Engines are not in the stock CLHEP yet: compile them into the test.
  $CXX -I"$repo/engines/include" -I"$inst/include/Geant4" \
    -I"$here" "$here/test_engines.cc" "$repo/engines/src/G4RngEngines.cc" \
    -L"$inst/lib64" -Wl,--disable-new-dtags,-rpath,"$inst/lib64" -lG4clhep -o "$out/test_engines"
else
  $CXX -I"$here" -I"$inst/include/Geant4" "$here/test_engines.cc" \
    -L"$inst/lib64" -Wl,--disable-new-dtags,-rpath,"$inst/lib64" -lG4clhep -o "$out/test_engines"
fi
(cd "$out" && ./test_engines)
