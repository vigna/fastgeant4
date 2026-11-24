#!/bin/bash
# Builds (patched, see below) Geant4 examples against $ROOT/install-<variant> into
# $ROOT/examples-<variant>/<name>.
# Usage: scripts/build-examples.sh <variant> <example-dir-under-examples/>...
# Run on the build host.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variant=${1:?variant}; shift
inst=$ROOT/install-$variant
[ -d "$inst" ] || { echo "missing $inst" >&2; exit 1; }
# A copy of the stock examples with patches/examples-11.4.3.patch applied
# (it removes TestEm11's switch to RanecuEngine and makes OpNovice2 print its
# run summary with 8 digits instead of 2).
exsrc=$ROOT/examples-src
stamp=$exsrc/.patched-$(sha256sum "$repo/patches/examples-11.4.3.patch" | cut -c1-16)
if [ ! -e "$stamp" ]; then
  rm -rf "$exsrc"; mkdir -p "$exsrc"
  cp -R "$ROOT/upstream/geant4-v11.4.3/examples" "$exsrc/"
  patch -s -p1 -d "$exsrc" < "$repo/patches/examples-11.4.3.patch"
  touch "$stamp"
fi
for ex in "$@"; do
  name=$(basename "$ex")
  b=$ROOT/examples-$variant/$name
  rm -rf "$b"; mkdir -p "$(dirname "$b")"
  cmake -S "$exsrc/examples/$ex" -B "$b" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DGeant4_DIR="$inst/lib64/cmake/Geant4" > "$b.cmake.log" 2>&1 \
    || { cat "$b.cmake.log" >&2; exit 1; }
  ninja -C "$b" > "$b.ninja.log" 2>&1 || { tail -30 "$b.ninja.log" >&2; exit 1; }
  echo "built $b"
done
