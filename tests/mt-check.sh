#!/bin/bash
# Runs TestEm3 with 4 threads and G4RNG_DEBUG=1 for each engine of a variant
# and checks that every thread runs the requested engine.
# Usage: tests/mt-check.sh <variant> [engine...]  (default: the three engines,
# or the compiled one for fast-<engine>). Run on the build host.
set -uo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variant=${1:?variant}; shift
if [ $# -gt 0 ]; then engines=("$@")
elif [[ $variant == fast-* ]]; then engines=("${variant#fast-}")
else engines=(mixmax xoshiro256pp mwc192x); fi
declare -A cls=([mixmax]=MixMaxRng [xoshiro256pp]=Xoshiro256ppEngine [mwc192x]=Mwc192xEngine)
exe=$ROOT/examples-$variant/TestEm3/TestEm3
[ -x "$exe" ] || "$repo/scripts/build-examples.sh" "$variant" extended/electromagnetic/TestEm3 || exit 1
work=$(mktemp -d)
fail=0
for e in "${engines[@]}"; do
  (cd "$work" && LD_LIBRARY_PATH=$ROOT/install-$variant/lib64 G4RNG_DEBUG=1 G4RNG_ENGINE=$e \
     "$exe" "$repo/tests/data/mt-check-testem3.mac" 4 > out.txt 2> err.txt)
  status=$?
  n=$(grep -c '^G4RNG: thread engine=' "$work/err.txt")
  bad=$(grep '^G4RNG: thread engine=' "$work/err.txt" | grep -vc "=${cls[$e]}\$")
  repl=$(grep -c '^G4RNG: engine replaced' "$work/err.txt")
  done_=$(grep -c '^ Run terminated' "$work/out.txt")
  if [ $status = 0 ] && [ "$n" -ge 9 ] && [ "$bad" = 0 ] && [ "$repl" = 0 ] && [ "$done_" -ge 1 ]; then
    echo "ok   $variant $e: $n thread-engine lines, all ${cls[$e]}"
  else
    echo "FAIL $variant $e: status=$status lines=$n wrong=$bad replaced=$repl terminated=$done_"
    tail -5 "$work/err.txt"; fail=1
  fi
done
rm -rf "$work"
[ $fail = 0 ] && echo "MT CHECK PASSED"
exit $fail
