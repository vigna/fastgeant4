#!/bin/bash
# Reproduces the study on one Linux host, from nothing to a results page:
#
#   setup         downloads Geant4 11.4.3 (checked against its SHA-256), checks
#                 the tools, unpacks (scripts/setup-host.sh)
#   build         stock, drop-in, fast paths, layout replicates, the datasets
#                 and the five workloads for every build (scripts/build-host.sh)
#   verify        known answers, engine selection, fast path, worker engines,
#                 drop-in call path identical to stock (scripts/verify-host.sh)
#   bench         time, instructions and cycles per call of each call path
#   count         draws and reseedings per event
#   calibrate     event scales for this host: about 60 s per single-thread run,
#                 40 s per multithreaded run (pilot runs, run.py calibrate)
#   interference  do parallel single-thread slots slow each other?
#   mt            multithreaded campaign on the whole machine, 10 paired runs
#   st            single-thread campaign: in parallel slots, 2 runs per slot
#                 and at least 20 per configuration, if they do not
#                 interfere; else sequentially, 10 per configuration
#   perfstat      hardware counters per engine (perf stat), 4 runs each
#   analyze       physics checks (check.txt) and analyses (summary.md)
#   site          the results page, index.html
#
# Each stage prints STAGE-DONE <stage> and leaves a marker: rerunning with the
# same RUN resumes after the last completed stage, and the campaigns skip the
# runs already recorded. Naming stages runs just those, done or not.
#
# Needs hosts/$HOST.env (single-thread CPUs) and hosts/$HOST-full.env (the
# whole machine), see hosts/TEMPLATE.env. Results in $ROOT/results/$HOST/$RUN
# and $ROOT/results/$HOST-full/$RUN.
#
# Usage: HOST=<host> [RUN=<id>] scripts/reproduce.sh [stage...]   (on the host)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
: "${HOST:?set HOST to the name of a hosts/<name>.env file}"
[ -f "hosts/$HOST.env" ] || { echo "missing hosts/$HOST.env (see hosts/TEMPLATE.env)"; exit 1; }
[ -f "hosts/$HOST-full.env" ] || { echo "missing hosts/$HOST-full.env (see hosts/TEMPLATE.env)"; exit 1; }
source "hosts/$HOST.env"
export HOST
RUN=${RUN:-$(date +%F)}
R=$ROOT/results/$HOST/$RUN
F=$ROOT/results/$HOST-full/$RUN
mkdir -p "$R/stages" "$F"
STAGES=(setup build verify bench count calibrate interference mt st perfstat analyze site)
W=(testem3 b4hadr testem11 opnovice2 range)
V=(stock dropin fast-mixmax fast-xoshiro256pp fast-mwc192x dropin-layout-name dropin-layout-noreorder)
URL=https://gitlab.cern.ch/geant4/geant4/-/archive/v11.4.3/geant4-v11.4.3.tar.gz

calibration() {  # exports the calibrated event scales (overriding the host files)
  [ -f "$R/calibration.env" ] || { echo "no $R/calibration.env: run the calibrate stage"; exit 1; }
  set -a; source "$R/calibration.env"; set +a
}

nslots() { echo $ST_CPUS | wc -w | tr -d " "; }

do_setup() {
  local tarball=$ROOT/upstream/geant4-v11.4.3.tar.gz
  if [ ! -f "$tarball" ]; then
    mkdir -p "$ROOT/upstream"
    curl -fsSL --retry 3 -o "$tarball.part" "$URL" && mv "$tarball.part" "$tarball"
  fi
  scripts/setup-host.sh
}

do_build() { scripts/build-host.sh; }

do_verify() {
  scripts/verify-host.sh | tee "$R/verify.log"
  grep -q '^VERIFY-PASSED' "$R/verify.log"
}

do_bench() {
  rm -f "$R/bench.csv" "$R/bench-instr.csv"
  scripts/bench.sh "$R/bench.csv"
  scripts/bench-instr.sh "$R/bench-instr.csv"
}

do_count() { scripts/count.sh "$R"; }

do_calibrate() {
  rm -rf "$R/calib"
  python3 scripts/run.py run --mode st --variants dropin --engines mixmax --workloads "${W[@]}" \
    --reps 1 --event-scale 0.3 --out "$R/calib/st.csv"
  HOST=$HOST-full python3 scripts/run.py run --mode mt --variants dropin --engines mixmax \
    --workloads "${W[@]}" --reps 1 --event-scale 1 --out "$R/calib/mt.csv"
  local st mt
  st=$(python3 scripts/run.py calibrate "$R/calib/st.csv" --mode st --target 60)
  mt=$(python3 scripts/run.py calibrate "$R/calib/mt.csv" --mode mt --target 40)
  printf 'EVENT_SCALE_ST=%s\nEVENT_SCALE_MT=%s\n' "$st" "$mt" > "$R/calibration.env"
  cat "$R/calibration.env"
}

do_interference() {
  calibration
  local n; n=$(nslots)
  if [ "$n" -lt 2 ]; then echo no > "$R/slots-clean"; echo "one ST CPU: sequential runs"; return; fi
  local scale; scale=$(python3 -c "print(f'{$EVENT_SCALE_ST / 4:.3g}')")  # about 15 s per run
  scripts/interference.sh "$R/interference-st" st "$n" "$scale" testem3 b4hadr | tee "$R/interference.log"
  if grep -q '^SLOTS-CLEAN yes' "$R/interference.log"; then echo yes; else echo no; fi > "$R/slots-clean"
}

do_mt() {
  calibration
  cp "$R/bench.csv" "$R/bench-instr.csv" "$R/counts.csv" "$F/"
  HOST=$HOST-full python3 scripts/run.py run --mode mt --variants "${V[@]}" --workloads "${W[@]}" \
    --reps 10 --out "$F/runs.csv"
}

do_st() {
  calibration
  local n; n=$(nslots)
  if [ "$(cat "$R/slots-clean")" = yes ]; then
    scripts/campaign-slots.sh "$R" st "$n" $(( n * ((20 + n - 1) / n) )) "${V[@]}"
  else
    echo "parallel slots interfere (or only one ST CPU): sequential campaign on the first CPU"
    python3 scripts/run.py run --mode st --variants "${V[@]}" --workloads "${W[@]}" \
      --reps 10 --out "$R/runs-st-0.csv"
  fi
}

do_perfstat() {
  calibration
  python3 scripts/perfstat.py "$R" --reps 4
}

do_analyze() {
  python3 scripts/run.py check "$R"/runs-st-*.csv > "$R/check.txt" || true
  HOST=$HOST-full python3 scripts/run.py check "$F/runs.csv" > "$F/check.txt" || true
  python3 scripts/analyze.py "$R" > /dev/null
  HOST=$HOST-full python3 scripts/analyze.py "$F" > /dev/null
  echo "single thread: $(tail -1 "$R/check.txt")"
  echo "multithreaded: $(tail -1 "$F/check.txt")"
}

do_site() {
  local threads
  threads=$(python3 -c "import sys; sys.path.insert(0, 'scripts'); import run; print(len(run.parse_cpu_list(run.load_host('$HOST-full')['MT_CPUS'])))")
  python3 scripts/build_site.py --st "$R" --mt "$F" --perf "$R/perfstat.md" --threads "$threads" \
    --out "$R/index.html"
}

run_stage() {
  local s=$1 force=$2
  if [ "$force" = no ] && [ -e "$R/stages/$s" ]; then echo "STAGE-SKIPPED $s (done)"; return; fi
  echo "STAGE-START $s $(date -u +%FT%TZ)"
  # A subshell outside any if, so that set -e stops the stage at its first
  # failing command (bash ignores set -e in functions called as conditions).
  local status
  set +e
  ( set -e; "do_$s" )
  status=$?
  set -e
  if [ $status = 0 ]; then
    touch "$R/stages/$s"
    echo "STAGE-DONE $s $(date -u +%FT%TZ)"
  else
    echo "STAGE-FAILED $s"
    exit 1
  fi
}

echo "REPRODUCE host=$HOST run=$RUN results=$R"
if [ $# -gt 0 ]; then
  for s in "$@"; do
    [[ " ${STAGES[*]} " == *" $s "* ]] || { echo "unknown stage $s (stages: ${STAGES[*]})"; exit 1; }
    run_stage "$s" yes
  done
else
  for s in "${STAGES[@]}"; do run_stage "$s" no; done
  echo "REPRODUCE-DONE: results page $R/index.html"
fi
