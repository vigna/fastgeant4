#!/bin/bash
# Prepares and builds every study variant, in order, on CPUs given by
# BUILD_CPUS (default: all). Usage: scripts/build-all.sh [variant...]
# Run on the build host.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
variants=("$@")
[ ${#variants[@]} -gt 0 ] || variants=(fast-mixmax fast-xoshiro256pp fast-mwc192x \
  dropin dropin-layout-name dropin-layout-noreorder)
pin=(); [ -n "${BUILD_CPUS:-}" ] && pin=(taskset -c "$BUILD_CPUS")
for v in "${variants[@]}"; do
  case $v in
    dropin-layout-*) ;;  # reuses src-dropin
    *) "${pin[@]}" "$repo/scripts/prepare-source.sh" "$v" ;;
  esac
  "${pin[@]}" "$repo/scripts/build.sh" "$v"
done
echo ALL-BUILDS-DONE
