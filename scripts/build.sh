#!/bin/bash
# Configures, builds and installs one variant into $ROOT/install-<variant>.
# Usage: scripts/build.sh stock|dropin|fast-<engine>|<variant>-layout-name|<variant>-layout-noreorder
# The layout variants reuse src-<variant> and only change code layout:
# <variant>-layout-name: -ffunction-sections plus GNU ld --sort-section=name;
# <variant>-layout-noreorder: -fno-reorder-functions (no .text.hot/.unlikely placement).
# Run on the build host.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variant=${1:?variant}
cxxflags= ; ldflags=
case $variant in
  stock) src=$ROOT/upstream/geant4-v11.4.3 ;;
  *-layout-name)
    src=$ROOT/src-${variant%-layout-name}
    cxxflags=-ffunction-sections
    ldflags=-Wl,--sort-section=name ;;
  *-layout-noreorder)
    src=$ROOT/src-${variant%-layout-noreorder}
    cxxflags=-fno-reorder-functions ;;
  *) src=$ROOT/src-$variant ;;
esac
[ -d "$src" ] || { echo "missing $src (run prepare-source.sh)" >&2; exit 1; }
build=$ROOT/build-$variant
inst=$ROOT/install-$variant
rm -rf "$build" "$inst"
cmake -S "$src" -B "$build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$inst" \
  -DCMAKE_CXX_FLAGS="$cxxflags" \
  -DCMAKE_SHARED_LINKER_FLAGS="$ldflags" -DCMAKE_EXE_LINKER_FLAGS="$ldflags" \
  -DGEANT4_BUILD_MULTITHREADED=ON -DGEANT4_USE_SYSTEM_EXPAT=OFF \
  -DGEANT4_INSTALL_DATA=OFF -DGEANT4_INSTALL_DATADIR="$DATA" > "$ROOT/build-$variant.cmake.log"
ninja -C "$build" -j"$JOBS" > "$ROOT/build-$variant.ninja.log"
ninja -C "$build" install > /dev/null
echo "installed $inst"
