#!/bin/bash
# Checks bench/count_getengine.cc on the drop-in build: rngbench's G4UniformRand
# loop of n calls must be counted as at least n getTheEngine() calls (and at most
# n plus a few for setup), its cached-pointer-free getTheEngine_flat loop too.
# Usage: tests/test-count-shim.sh [variant]   (run on the build host)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
v=${1:-dropin}
inst=$ROOT/install-$v
work=$ROOT/bench-$v
mkdir -p "$work"
g++ -std=c++17 -O2 -shared -fPIC "$repo/bench/count_getengine.cc" -o "$work/libcountgetengine.so" -ldl
g++ -std=c++17 -O2 -I"$inst/include/Geant4" "$repo/bench/rngbench.cc" \
  -L"$inst/lib64" -Wl,--disable-new-dtags,-rpath,"$inst/lib64" -lG4global -lG4clhep -o "$work/rngbench"
n=100000
for what in G4UniformRand getTheEngine_flat; do
  err=$(G4RNG_ENGINE=mixmax LD_PRELOAD="$work/libcountgetengine.so" "$work/rngbench" $what $n 1 2>&1 >/dev/null)
  c=$(sed -n 's/^G4RNG-COUNT getTheEngine=\([0-9]*\)$/\1/p' <<<"$err")
  [ -n "$c" ] || { echo "FAIL: no count line for $what: $err"; exit 1; }
  if [ "$c" -lt $n ] || [ "$c" -gt $((n + 100)) ]; then
    echo "FAIL: $what: $c getTheEngine calls counted, expected $n (+ setup)"; exit 1
  fi
  echo "$what: $c calls for $n draws"
done
echo "COUNT SHIM TEST PASSED"
