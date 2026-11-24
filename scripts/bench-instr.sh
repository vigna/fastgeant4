#!/bin/bash
# Instructions and cycles per call of bench/rngbench (perf stat, user space),
# to set against the per-draw changes measured in the workloads
# (scripts/perfstat.py): the counts of a run of 2n calls minus those of a run
# of n calls, divided by n, so that start-up cancels. Appends
# host,variant,engine,what,instructions,cycles to <out.csv>.
# Usage: HOST=<host> scripts/bench-instr.sh <out.csv> [variant...]
# (after scripts/bench.sh, which builds the binaries). BENCH_CPU overrides the
# CPU (default: the first of ST_CPUS); BENCH_N the n (default 10^8).
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
out=${1:?out.csv}; shift
variants=("$@")
[ ${#variants[@]} -gt 0 ] || variants=(stock dropin fast-mixmax fast-xoshiro256pp fast-mwc192x)
cpu=${BENCH_CPU:-${ST_CPUS%% *}}
n=${BENCH_N:-100000000}
[ -s "$out" ] || echo "host,variant,engine,what,instructions,cycles" > "$out"
counts() {  # perf stat -x, output on stdin: prints "instructions cycles" (scripts/perfstat.py's parser)
  python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import perfstat
c = perfstat.parse_perf_stat(sys.stdin.read()); print(int(c["instructions"]), int(c["cycles"]))' "$repo/scripts"
}
count() {  # count <bin> <engine> <what> <calls>: prints "instructions cycles"
  G4RNG_ENGINE=$2 taskset -c "$cpu" perf stat -x, -e instructions:u,cycles:u -- "$1" "$3" "$4" 1 \
    2>&1 > /dev/null | counts
}
for v in "${variants[@]}"; do
  bin=$ROOT/bench-$v/rngbench
  [ -x "$bin" ] || { echo "no $bin: run scripts/bench.sh first" >&2; exit 1; }
  if [[ $v == fast-* ]]; then engines=("${v#fast-}")
  elif [[ $v == stock ]]; then engines=(mixmax)
  else engines=(mixmax xoshiro256pp mwc192x); fi
  for e in "${engines[@]}"; do
    for what in G4UniformRand getTheEngine_flat; do
      read -r i1 c1 < <(count "$bin" "$e" $what "$n")
      read -r i2 c2 < <(count "$bin" "$e" $what $((2 * n)))
      awk -v h="$HOST" -v v="$v" -v e="$e" -v w=$what -v n="$n" -v i1="$i1" -v i2="$i2" \
          -v c1="$c1" -v c2="$c2" \
          'BEGIN {printf "%s,%s,%s,%s,%.3f,%.3f\n", h, v, e, w, (i2 - i1) / n, (c2 - c1) / n}' |
        tee -a "$out"
    done
  done
done
