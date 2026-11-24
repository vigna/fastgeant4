#!/bin/bash
# Copies the current engines/ files into existing prepared sources and rebuilds
# incrementally (ninja), then reinstalls. Equivalent to a clean build of the same
# sources. Usage: scripts/update-engines.sh [variant...] (default: all eight).
# Run on the build host.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variants=("$@")
[ ${#variants[@]} -gt 0 ] || variants=(fast-mixmax fast-xoshiro256pp fast-mwc192x \
  dropin dropin-layout-name dropin-layout-noreorder)
for v in "${variants[@]}"; do
  case $v in dropin-layout-*) src=$ROOT/src-dropin ;; *) src=$ROOT/src-$v ;; esac
  clhep=$src/source/externals/clhep
  for f in "$repo"/engines/include/CLHEP/Random/*.h "$repo"/engines/include/CLHEP/Random/*.icc; do
    cmp -s "$f" "$clhep/include/CLHEP/Random/$(basename "$f")" || cp "$f" "$clhep/include/CLHEP/Random/"
  done
  for f in "$repo"/engines/src/*.cc; do
    cmp -s "$f" "$clhep/src/$(basename "$f")" || cp "$f" "$clhep/src/"
  done
  ninja -C "$ROOT/build-$v" -j"$JOBS" > "$ROOT/build-$v.update.log"
  ninja -C "$ROOT/build-$v" install > /dev/null
  echo "updated $ROOT/install-$v"
done
echo ALL-UPDATES-DONE
