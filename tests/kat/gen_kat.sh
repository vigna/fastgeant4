#!/bin/bash
# Compiles the reference generators and prints their known answers.
# Needs checkouts of https://github.com/vigna/prng-speed,
# https://github.com/vigna/MWCPRNG and https://github.com/boostorg/random
# (by default in ~/git; override with PRNG_SPEED, MWCPRNG and BOOST_RANDOM)
# and the Boost headers (BOOST_INCLUDE, default /opt/local/include).
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=${TMPDIR:-/tmp}/gen_kat.$$
P=${PRNG_SPEED:-$HOME/git/prng-speed}/cpu
M=${MWCPRNG:-$HOME/git/MWCPRNG}/prngs
cc -O2 -w -I"$P" -DA=17 -DB=45 -DR=23 -c "$here/kat_xoshiro256pp.c" -o "$out.2.o"
cc -O2 -w -I"$M" -c "$here/kat_mwc192x.c" -o "$out.3.o"
c++ -std=c++17 -O2 -w -I"${BOOST_RANDOM:-$HOME/git/boost-random}/include" -I"${BOOST_INCLUDE:-/opt/local/include}" \
  -c "$here/kat_jump_xoshiro256pp.cc" -o "$out.4.o"
cc -O2 -c "$here/gen_kat.c" -o "$out.0.o"
c++ -O2 "$out.0.o" "$out.2.o" "$out.3.o" "$out.4.o" -o "$out"
"$out"
rm -f "$out" "$out".*.o
