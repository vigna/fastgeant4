#!/bin/bash
# Runs bench/rngbench for every variant/engine; appends CSV rows
# host,variant,engine,what,ns to the output file.
# Usage: scripts/bench.sh <out.csv> [variant...] (default: stock, dropin and the five fast builds).
# Run on the build host, machine idle.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
out=${1:?out.csv}; shift
variants=("$@")
[ ${#variants[@]} -gt 0 ] || variants=(stock dropin fast-mixmax fast-xoshiro256pp fast-mwc192x)
cpu=${ST_CPUS%% *}
[ -s "$out" ] || echo "host,variant,engine,what,ns" > "$out"
for v in "${variants[@]}"; do
  inst=$ROOT/install-$v
  bin=$ROOT/bench-$v/rngbench
  mkdir -p "$(dirname "$bin")"
  g++ -std=c++17 -O2 -I"$inst/include/Geant4" "$repo/bench/rngbench.cc" \
    -L"$inst/lib64" -Wl,--disable-new-dtags,-rpath,"$inst/lib64" -lG4global -lG4clhep -o "$bin"
  if [[ $v == fast-* ]]; then engines=("${v#fast-}")
  elif [[ $v == stock ]]; then engines=(mixmax)  # stock has only its default engine
  else engines=(mixmax xoshiro256pp mwc192x); fi
  for e in "${engines[@]}"; do
    for what in G4UniformRand getTheEngine_flat RandGaussQ setSeeds; do
      n=200000000; [ $what = RandGaussQ ] && n=50000000; [ $what = setSeeds ] && n=200000
      ns=$(G4RNG_ENGINE=$e taskset -c "$cpu" "$bin" $what $n 5 2>/dev/null)
      echo "$HOST,$v,$e,$what,$ns" | tee -a "$out"
    done
  done
done
