#!/bin/bash
# Runs tests/test_engines.cc without a Geant4 build: the engines and the few
# CLHEP sources they need are compiled from upstream/geant4-v11.4.3 (unpack
# the tarball there). Usage: tests/run-tests-local.sh
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/.." && pwd)
clhep=$repo/upstream/geant4-v11.4.3/source/externals/clhep
[ -d "$clhep" ] || { echo "missing $clhep (unpack the Geant4 tarball in upstream/)" >&2; exit 1; }
out=$(mktemp -d "${TMPDIR:-/tmp}/g4rng-tests.XXXXXX")
c++ -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter \
  -I"$repo/engines/include" -I"$clhep/include" -I"$here" \
  "$here/test_engines.cc" "$repo/engines/src/G4RngEngines.cc" \
  "$clhep/src/RandomEngine.cc" "$clhep/src/engineIDulong.cc" "$here/local_stubs.cc" \
  -o "$out/test_engines"
(cd "$out" && ./test_engines)
rm -rf "$out"
