#!/bin/bash
# Checks engine selection through G4RNG_ENGINE on a drop-in install.
# Usage: tests/test-select.sh <variant>. Run on the build host.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variant=${1:?variant}
inst=$ROOT/install-$variant
out=$ROOT/tests-$variant
mkdir -p "$out"
g++ -std=c++17 -O2 -Wall -I"$inst/include/Geant4" "$here/test_select.cc" \
  -L"$inst/lib64" -Wl,--disable-new-dtags,-rpath,"$inst/lib64" -lG4global -lG4clhep -o "$out/test_select" || exit 1
ulimit -c 0
fail=0
check() { # env-value expected-name
  got=$(G4RNG_ENGINE=$1 "$out/test_select" 2>/dev/null | sed -n 's/^engine=//p')
  if [ "$got" = "$2" ]; then echo "ok   $1 -> $got"; else echo "FAIL $1 -> '$got' (want $2)"; fail=1; fi
}
check mixmax MixMaxRng
check xoshiro256pp Xoshiro256ppEngine
check mwc192x Mwc192xEngine
check count:xoshiro256pp "G4RngCountingEngine(Xoshiro256ppEngine)"
if G4RNG_ENGINE=bogus "$out/test_select" >/dev/null 2>&1; then echo "FAIL bogus accepted"; fail=1; else echo "ok   bogus rejected"; fi
cnt=$(G4RNG_ENGINE=count:xoshiro256pp "$out/test_select" 1000 2>&1 >/dev/null | grep '^G4RNG-COUNT')
if [ "$cnt" = "G4RNG-COUNT flat=1000 flatArray=0 setSeeds=0" ]; then echo "ok   $cnt"; else echo "FAIL count line: '$cnt'"; fail=1; fi
banner=$(G4RNG_ENGINE=mwc192x "$out/test_select" 2>&1 >/dev/null | grep '^G4RNG: variant=')
if [ "$banner" = "G4RNG: variant=dropin engine=mwc192x" ]; then echo "ok   $banner"; else echo "FAIL banner: '$banner'"; fail=1; fi
[ $fail = 0 ] && echo "ALL SELECT TESTS PASSED"
exit $fail
