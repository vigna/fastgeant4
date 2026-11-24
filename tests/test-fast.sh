#!/bin/bash
# Usage: tests/test-fast.sh fast-<engine>. Run on the build host.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variant=${1:?variant}
inst=$ROOT/install-$variant
out=$ROOT/tests-$variant
mkdir -p "$out"
g++ -std=c++17 -O2 -Wall -I"$inst/include/Geant4" "$here/test_fast.cc" \
  -L"$inst/lib64" -Wl,--disable-new-dtags,-rpath,"$inst/lib64" -lG4global -lG4clhep -o "$out/test_fast" || exit 1
fail=0
"$out/test_fast" || fail=1
other=xoshiro256pp; [ "$variant" = fast-xoshiro256pp ] && other=mwc192x
if G4RNG_ENGINE=$other "$out/test_fast" > /dev/null 2>&1; then echo "FAIL G4RNG_ENGINE=$other accepted"; fail=1
else echo "ok   G4RNG_ENGINE=$other rejected"; fi
[ $fail = 0 ] && echo "ALL FAST TESTS PASSED"
exit $fail
