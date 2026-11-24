#!/bin/bash
# The verification suite on a host, after scripts/build-host.sh: unit tests,
# engine known answers, selection, fast path, MT worker engines, call path,
# codegen, the getTheEngine counting shim; and that the drop-in build keeps the
# stock call path: as many getTheEngine()@plt call sites in
# libG4processes_core.so as stock, and the same instructions on the hot path of
# HepRandom::getTheEngine() (from its entry to the first ret: what every call
# after a thread's first executes; the one-time initialization path differs by
# the call to the patch's g4rngInit()). Prints VERIFY-PASSED or VERIFY-FAILED.
# Usage: HOST=<host> scripts/verify-host.sh   (run on the host)
set -uo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
source "hosts/${HOST:?set HOST}.env"
export HOST
log=$ROOT/logs/verify
mkdir -p "$log"
fail=0
step() {  # step <name> <command...>: runs it, prints its last line
  local name=$1; shift
  if "$@" > "$log/$name.log" 2>&1; then echo "ok   $name: $(tail -1 "$log/$name.log")"
  else echo "FAIL $name (see $log/$name.log)"; fail=1; fi
}
step unittest python3 -m unittest tests/test_runner.py tests/test_analyze.py tests/test_perfstat.py
step engines tests/run-tests.sh dropin
step select tests/test-select.sh dropin
step mt-dropin tests/mt-check.sh dropin
for e in mixmax xoshiro256pp mwc192x; do
  step fast-$e tests/test-fast.sh fast-$e
  step callpath-fast-$e scripts/check-callpath.sh fast-$e 0
  step mt-fast-$e tests/mt-check.sh fast-$e $e
  step codegen-fast-$e tests/check-codegen.sh fast-$e
done
step codegen-dropin tests/check-codegen.sh dropin
step count-shim tests/test-count-shim.sh dropin
n_stock=$(scripts/check-callpath.sh stock | sed -n 's/^stock: \([0-9]*\) calls.*/\1/p')
n_dropin=$(scripts/check-callpath.sh dropin | sed -n 's/^dropin: \([0-9]*\) calls.*/\1/p')
if [ -n "$n_stock" ] && [ "$n_stock" = "$n_dropin" ] && [ "$n_stock" -gt 0 ]; then
  echo "ok   callpath-dropin: $n_dropin getTheEngine()@plt call sites, as stock"
else echo "FAIL callpath-dropin: $n_dropin call sites, stock $n_stock"; fail=1; fi
hot() {  # HepRandom::getTheEngine() of a build from its entry to the first ret, addresses removed
  objdump -d --no-show-raw-insn -C "$ROOT/install-$1/lib64/libG4clhep.so" |
    awk '/<CLHEP::HepRandom::getTheEngine\(\)>:$/,/^$/' |
    sed -E 's/^ *[0-9a-f]+:\t//; s/[0-9a-f]+ <([^>+]*)(\+0x[0-9a-f]+)?>/<\1>/; s/0x[0-9a-f]+\(%rip\)/X(%rip)/' |
    sed -n '1,/^ret/p'
}
if [ "$(hot stock | tail -1 | cut -c1-3)" = ret ] && diff <(hot stock) <(hot dropin) > "$log/getTheEngine.diff"; then
  echo "ok   getTheEngine-dropin: hot path ($(hot stock | grep -c .) lines) identical to stock"
else echo "FAIL getTheEngine-dropin: hot path differs from stock (see $log/getTheEngine.diff)"; fail=1; fi
[ $fail = 0 ] && echo VERIFY-PASSED || { echo VERIFY-FAILED; exit 1; }
