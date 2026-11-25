# fastgeant4: faster random numbers for Geant4

**Results: <https://vigna.github.io/fastgeant4/>**

Geant4 11.4.3 uses MIXMAX (CLHEP `MixMaxRng`, N = 17) as its pseudorandom
number generator. Replacing it with MWC192X, called through an inlined,
non-virtual path, makes five representative simulations 2–9% faster on one
thread and 3–14% faster on 96 threads (AMD Zen 5, 96 cores, clock fixed at
4.5 GHz); xoshiro256++ follows, up to two points behind. Swapping the engine
alone, with no change to Geant4's call path, gives 1.5–3.6% on one thread,
and more with many threads, because Geant4 reseeds every event and MIXMAX
takes 23 µs to reseed (MWC192X 0.5 µs, xoshiro256++ 6.6 µs). The physics is
unchanged: every observable agrees across engines, and the same engine and
seed give identical results in every build.

Only generators that produce a number in 1–2 ns and support jumping are
considered: as with MIXMAX, distinct seeds must give non-overlapping streams.
The author designed MWC192X and co-designed xoshiro256++.

## Two ways of using a new generator

- **Drop-in:** the generators as CLHEP engines behind Geant4's existing call
  path (`G4UniformRand()` → out-of-line `HepRandom::getTheEngine()` →
  virtual `flat()`). In the study build all engines live in one binary and
  are selected at run time with `G4RNG_ENGINE=mixmax|xoshiro256pp|mwc192x`.
- **Fast path:** one build per generator (MIXMAX included) in which
  `getTheEngine()` is an inline thread-local read and `G4UniformRand()` an
  inlined, non-virtual call to the compiled engine.

This repository holds the code of the study, instrumentation included:
engine selection by environment variable, draw counting and diagnostic
banners exist to measure, not to ship. A production change is much smaller:
Geant4 already accepts any engine through `G4Random::setTheEngine`, worker
threads need a few lines to clone the new engine types, and the fast path is
about 50 lines.

## Layout

| Path | Contents |
|:--|:--|
| `docs/index.html` | The results page |
| `engines/` | New CLHEP files: the engines (`G4RngEngines.h/.cc`, jump tables), the fast path (`G4RngFast.h`), engine selection (`G4RngSelect`) and a draw-counting wrapper |
| `patches/geant4-11.4.3-rng.patch` | Changes to existing Geant4 and CLHEP files |
| `patches/examples-11.4.3.patch` | TestEm11 keeps the default engine instead of switching to `RanecuEngine`; OpNovice2 prints its run summary with 8 digits instead of 2 |
| `workloads/` | Macros and `workloads.json` (events, observables) |
| `scripts/` | Build, run, count, benchmark, analyze |
| `bench/rngbench.cc` | Per-call cost of each call path |
| `tests/` | Engine known answers, selection, fast path, worker threads, runner and analysis |
| `hosts/<host>.env` | Host descriptions (paths, CPUs to pin to): `TEMPLATE.env` explains them; `zen5` and `zen5-full` are the machine of the results, `desktop` an Intel hybrid example |
| `results/zen5/2026-11-24/` | Single-thread campaign: 11 parallel single-core slots, 22 paired runs per configuration |
| `results/zen5-full/2026-11-24/` | 96-thread campaign: 10 paired runs per configuration |
| `results/zen5/2026-11-23/` | Hardware counters (`perf stat`) per engine |

Each campaign directory holds the raw runs (CSV, one row per run, with the
physics observables), per-run logs, microbenchmarks, draw counts, the
physics check (`check.txt`) and the analysis (`summary.md`).

## Reproducing

**The analysis, from the published data** (Python 3 only, a few minutes):

```sh
scripts/reanalyze.sh
```

recomputes every physics check, analysis, hardware-counter report and the
results page from the raw runs under `results/`, and shows any difference
from the committed files (there should be none).

**The measurements**, on a Linux host with GCC, CMake, Ninja and `perf`:

```sh
git clone https://github.com/vigna/fastgeant4.git && cd fastgeant4
cp hosts/TEMPLATE.env hosts/myhost.env        # set HOST, ROOT, DATA, JOBS, ST_CPUS, MT_CPUS
cp hosts/TEMPLATE.env hosts/myhost-full.env   # the same, with MT_CPUS = all cores
HOST=myhost scripts/reproduce.sh
```

`scripts/reproduce.sh` runs the whole study in stages, each resumable:
download and check Geant4 11.4.3, build the stock build and the study
variants with the five workloads, verify them, microbenchmarks, draw counts,
calibration of the event counts to the host (about 60 s per single-thread
run and 40 s per multithreaded run), a check that parallel single-thread
slots do not slow each other, the multithreaded campaign on the whole
machine, the single-thread campaign (in parallel slots if they do not
interfere, else sequentially), hardware counters, physics checks and
analyses, and a results page. Results go to `$ROOT/results/<host>/<date>`
and `$ROOT/results/<host>-full/<date>`; rerun with the same `RUN=<date>` to
resume, or name stages to run just those (`scripts/reproduce.sh mt st`). On
the 96-core machine of the published results it takes about 11 hours, most
of them in the two campaigns.

Every run is pinned with `taskset`, waits until the host is idle, and is
rejected unless the process's `G4RNG:` banner names the requested variant
and engine. The runner records the CPU time other processes used during the
run; the analysis screens out runs that lost CPU, pairs the runs of each
repetition (same seeds), and reports geometric-mean ratios with 95%
Student-t intervals. Comparisons between two binaries are called
significant only if they clear the code-layout band, the spread between two
relinks of identical code (`dropin-layout-name`, `dropin-layout-noreorder`).

Without a Geant4 build, `tests/run-tests-local.sh` runs the engine tests
(unpack the Geant4 tarball in `upstream/` first), and
`python3 -m unittest discover -s tests` the runner and analysis tests.
`tests/kat/gen_kat.sh` recomputes the known answers from the reference
implementations.

## Engines

The next-state functions are those of the reference implementations:
[xoshiro256++](https://prng.di.unimi.it/) by D. Blackman and S. Vigna, and
[MWC192X](https://github.com/vigna/MWCPRNG) by S. Vigna. `flat()` returns
`((x >> 11) + 1) * 2^-53`, in (0, 1] as MIXMAX does.

Seeding follows MIXMAX. Multithreaded Geant4 reseeds every event with two
32-bit seeds drawn by the master; `MixMaxRng::setSeeds` does not use them
as a state but as a jump distance from a fixed state (`apply_bigskip`),
which guarantees non-overlapping streams for distinct seeds. xoshiro256++
and MWC192X do the same: from a fixed base state they jump by s · 2^128
(resp. s · 2^96) steps, s = seed0 + seed1 · 2^32, with precomputed tables
(one entry per bit of s, `scripts/gen_jump_tables.py`, checked against the
reference jump constants); MWC192X's jumps are Montgomery multiplications
modulo its prime.

The guarantee is conditional on distinct seeds: Geant4 draws them as
`(long)(100000000L * flat())`, two per event, about 2^53 pairs, so the
probability that two events of a run share a pair (and are identical) is
about n² / (2 · 10^16) for n events.

## License

The code in this repository is distributed under the GNU Lesser General
Public License, version 3 or later (`COPYING.LESSER`, which supplements
`COPYING`), the license of CLHEP. The patches modify Geant4, which is
distributed under the [Geant4 Software License](https://geant4.web.cern.ch/download/license).
