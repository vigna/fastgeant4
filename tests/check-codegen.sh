#!/bin/bash
# Checks that the out-of-line flat() of each new engine in libG4clhep.so has no
# vector instructions (GCC's SLP vectorizer once packed MWC192X's state stores
# into a 16-byte store, defeating store-to-load forwarding: 3.7 vs 1.3 ns/draw).
# Usage: tests/check-codegen.sh <variant>. Run on the build host.
set -uo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
lib=$ROOT/install-${1:?variant}/lib64/libG4clhep.so
dis=$(mktemp); objdump -d --no-show-raw-insn -C "$lib" > "$dis"
fail=0
for g in Xoshiro256ppGen Mwc192xGen; do
  n=$(awk "/<CLHEP::GenEngine<CLHEP::$g>::flat\\(\\)>:/,/^\$/" "$dis" | grep -cE 'punpck|movups|movdqu|movdqa|movaps|vmov')
  if [ "$n" = 0 ]; then echo "ok   $g::flat has no vector instructions"
  else echo "FAIL $g::flat has $n vector instructions"; fail=1; fi
done
rm -f "$dis"
[ $fail = 0 ] && echo "CODEGEN OK"
exit $fail
