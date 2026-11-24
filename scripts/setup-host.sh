#!/bin/bash
# Prepares a new build host: checks the tools (installs them with --install,
# dnf or apt), checks the Geant4 tarball and unpacks it into $ROOT/upstream,
# and prints a host description (CPU, topology, compiler, kernel) to
# $ROOT/host.txt.
# Copy the tarball first, e.g. from the Mac:
#   scp upstream/geant4-v11.4.3.tar.gz <host>:geant4-rng/upstream/
# The datasets are installed after the stock build:
#   $ROOT/install-stock/bin/geant4-config --install-datasets
# Usage: HOST=<host> scripts/setup-host.sh [--install]   (run on the host)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:?set HOST}.env"
tools=(g++ cmake ninja python3 taskset patch rsync curl sha256sum readelf perf)
missing=()
for t in "${tools[@]}"; do command -v "$t" > /dev/null || missing+=("$t"); done
if [ ${#missing[@]} -gt 0 ]; then
  if [ "${1:-}" != --install ]; then
    echo "missing: ${missing[*]} (rerun with --install)" >&2; exit 1
  fi
  # Only the packages of the missing tools (a full list can conflict with
  # preinstalled variants, e.g. curl-minimal on Amazon Linux).
  declare -A dnf_pkg=([g++]=gcc-c++ [cmake]=cmake [ninja]=ninja-build [python3]=python3
    [taskset]=util-linux [patch]=patch [rsync]=rsync [curl]=curl [sha256sum]=coreutils
    [readelf]=binutils [perf]=perf)
  declare -A apt_pkg=([g++]=g++ [cmake]=cmake [ninja]=ninja-build [python3]=python3
    [taskset]=util-linux [patch]=patch [rsync]=rsync [curl]=curl [sha256sum]=coreutils
    [readelf]=binutils [perf]="linux-tools-common linux-tools-$(uname -r)")
  if command -v dnf > /dev/null; then
    sudo dnf install -y $(for t in "${missing[@]}"; do echo "${dnf_pkg[$t]}"; done)
  elif command -v apt-get > /dev/null; then
    sudo apt-get update && sudo apt-get install -y $(for t in "${missing[@]}"; do echo "${apt_pkg[$t]}"; done)
  else
    echo "no dnf or apt-get: install ${missing[*]} by hand" >&2; exit 1
  fi
fi
mkdir -p "$ROOT/upstream" "$DATA" "$ROOT/logs"
# A compiler outside the system paths (GCC_PREFIX in the host file): wrappers
# that link every binary with a runpath to its runtime libraries and to
# $ORIGIN: a shared library with a runpath no longer sees the executable's
# rpath, so it must find its sibling libraries (libG4ptl for libG4global)
# itself.
if [ -n "${GCC_PREFIX:-}" ]; then
  mkdir -p "$ROOT/bin"
  for c in gcc:gcc cc:gcc g++:g++ c++:g++; do  # wrapper:driver (a GCC install has no cc)
    cat > "$ROOT/bin/${c%%:*}" <<WRAPPER
#!/bin/sh
exec $GCC_PREFIX/bin/${c#*:} "\$@" -Wl,-rpath,$GCC_PREFIX/lib64 -Wl,-rpath,'\$ORIGIN'
WRAPPER
    chmod +x "$ROOT/bin/${c%%:*}"
  done
  echo 'int main(void){return 0;}' | cc -x c - -o "$ROOT/bin/.rpath-test-c" || \
    { echo "C compiler wrapper does not work" >&2; exit 1; }
  [ "$(command -v g++)" = "$ROOT/bin/g++" ] || { echo "$ROOT/bin is not first in PATH" >&2; exit 1; }
  echo 'int main(){}' | g++ -x c++ - -o "$ROOT/bin/.rpath-test" && \
    readelf -d "$ROOT/bin/.rpath-test" | grep -qF "[$GCC_PREFIX/lib64:\$ORIGIN]" || \
    { echo "compiler wrapper does not add the rpath" >&2; exit 1; }
fi
tarball=$ROOT/upstream/geant4-v11.4.3.tar.gz
[ -f "$tarball" ] || { echo "missing $tarball (copy it from the Mac)" >&2; exit 1; }
echo "718752c1829cbfcf174f0e539d60ee3f76843b894444e61d2228d66a6887ef6e  $tarball" | sha256sum -c --quiet
[ -d "$ROOT/upstream/geant4-v11.4.3" ] || tar xzf "$tarball" -C "$ROOT/upstream"
{
  echo "host: $HOST ($(hostname))"; date -Is
  uname -srm
  grep -m1 PRETTY_NAME /etc/os-release || true
  g++ --version | head -1; cmake --version | head -1; python3 --version
  lscpu
  echo; lscpu -e=CPU,CORE,SOCKET,NODE,CACHE,MAXMHZ,MINMHZ
  echo; cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor 2>/dev/null || echo "no cpufreq governor"
  cat /sys/devices/system/cpu/cpufreq/boost 2>/dev/null || true
  echo "SMT: $(cat /sys/devices/system/cpu/smt/active 2>/dev/null || echo ?)"
  free -g
} > "$ROOT/host.txt"
echo "host ready; description in $ROOT/host.txt"
