## Multithreaded

### Reference and noise

| workload | drop-in MIXMAX ms/event | run-to-run CV | layout band | reps | stock vs. drop-in MIXMAX |
|:--|--:|--:|--:|--:|--:|
| testem3 | 0.4201 | 0.26% | 1.08% | 10 | +0.91% [+0.68, +1.14] (n.s.) |
| b4hadr | 0.06747 | 0.21% | 0.73% | 10 | -0.01% [-0.25, +0.24] (n.s.) |
| testem11 | 0.002738 | 0.47% | 1.18% | 10 | +0.75% [+0.47, +1.03] (n.s.) |
| opnovice2 | 0.1048 | 0.46% | 0.10% | 10 | +0.52% [+0.09, +0.96] (n.s.) |
| range | 0.01032 | 0.22% | 0.38% | 10 | -0.13% [-0.35, +0.09] (n.s.) |

### A. Drop-in engines vs. drop-in MIXMAX (same binary)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +1.88% [+1.60, +2.17] | +2.19% [+2.04, +2.34] |
| b4hadr | +1.41% [+1.11, +1.72] | +1.71% [+1.37, +2.06] |
| testem11 | +8.98% [+8.59, +9.36] | +12.51% [+12.02, +13.00] |
| opnovice2 | +2.35% [+2.09, +2.60] | +2.74% [+2.31, +3.17] |
| range | +2.48% [+2.22, +2.74] | +3.39% [+3.12, +3.66] |

### B. Fast-path engines vs. fast-path MIXMAX (generator effect on the fast path)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +0.99% [+0.02, +1.96] (n.s.) | +2.93% [+2.63, +3.22] |
| b4hadr | +0.89% [+0.53, +1.24] (n.s.) | +1.89% [+1.46, +2.32] |
| testem11 | +7.07% [+6.05, +8.11] | +12.73% [+12.53, +12.94] |
| opnovice2 | +2.24% [+1.84, +2.64] | +4.00% [+3.72, +4.28] |
| range | +2.53% [+2.29, +2.77] | +3.39% [+3.10, +3.69] |

### Call path: fast path vs. drop-in, same engine

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.51% [+1.30, +1.73] | +0.62% [-0.24, +1.49] (n.s.) | +2.24% [+2.01, +2.46] |
| b4hadr | +0.80% [+0.66, +0.95] (n.s.) | +0.28% [+0.05, +0.50] (n.s.) | +0.98% [+0.88, +1.08] |
| testem11 | +1.38% [+0.97, +1.80] (n.s.) | -0.39% [-1.20, +0.43] (n.s.) | +1.59% [+1.13, +2.05] (n.s.) |
| opnovice2 | +4.30% [+3.77, +4.84] | +4.29% [+3.86, +4.73] | +5.55% [+5.37, +5.73] |
| range | +1.15% [+0.87, +1.42] | +1.19% [+0.84, +1.55] | +1.15% [+0.88, +1.41] |

### Total: fast-path engine vs. drop-in MIXMAX

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.51% [+1.30, +1.73] | +2.51% [+1.49, +3.55] | +4.48% [+4.19, +4.77] |
| b4hadr | +0.80% [+0.66, +0.95] (n.s.) | +1.70% [+1.40, +1.99] | +2.71% [+2.41, +3.01] |
| testem11 | +1.38% [+0.97, +1.80] (n.s.) | +8.55% [+7.67, +9.45] | +14.29% [+13.72, +14.87] |
| opnovice2 | +4.30% [+3.77, +4.84] | +6.79% [+6.20, +7.38] | +8.44% [+8.05, +8.82] |
| range | +1.15% [+0.87, +1.42] | +3.70% [+3.25, +4.16] | +4.58% [+4.33, +4.82] |

### Total: fast-path engine vs. stock

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +0.60% [+0.23, +0.97] (n.s.) | +1.59% [+0.64, +2.55] (n.s.) | +3.54% [+3.30, +3.78] |
| b4hadr | +0.81% [+0.56, +1.05] (n.s.) | +1.70% [+1.26, +2.15] | +2.71% [+2.32, +3.11] |
| testem11 | +0.63% [+0.34, +0.91] (n.s.) | +7.74% [+6.88, +8.62] | +13.44% [+13.03, +13.85] |
| opnovice2 | +3.68% [+3.40, +3.96] | +6.17% [+5.54, +6.80] | +7.87% [+7.60, +8.14] |
| range | +1.28% [+1.01, +1.55] | +3.84% [+3.44, +4.24] | +4.71% [+4.41, +5.02] |

### Predicted / measured drop-in speedup (from counts and microbenchmarks)

| workload | draws/event | via getTheEngine | reseeds/event | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|--:|--:|
| testem3 | 2.813e+05 | 47% | 1 | -0.15% / +1.88% | -0.51% / +2.19% |
| b4hadr | 4.196e+04 | 50% | 1 | +0.11% / +1.41% | -0.09% / +1.71% |
| testem11 | 2310 | 31% | 1 | +6.58% / +8.98% | +8.87% / +12.51% |
| opnovice2 | 1.557e+05 | 99% | 1 | -0.20% / +2.35% | -0.83% / +2.74% |
| range | 2555 | 100% | 1 | +1.69% / +2.48% | +2.23% / +3.39% |

Speedups are 1/ratio − 1 of event-loop time per event (geometric mean of the ratios of runs paired by repetition), with 95% Student-t intervals; (n.s.) marks intervals that do not exclude no change (or, across binaries, the layout band). MT predictions compare the CPU time saved with the thread time per event. Predictions use the microbenchmark's time per call, which understates the in-situ cost of a draw: on a wide out-of-order core the benchmark loop overlaps successive calls (scripts/bench-instr.sh, scripts/perfstat.py: the instructions saved per draw agree, the cycles do not). xoshiro256pp and mwc192x are seeded by jumping (distinct seeds give non-overlapping streams, as MIXMAX's).

### Runs screened out (lost CPU to other processes)

| mode | workload | variant | engine | rep | real s | CPU s |
|:--|--:|--:|--:|--:|--:|--:|
| mt | opnovice2 | fast-xoshiro256pp | xoshiro256pp | 4 | 32.665036 | 2957.48 |
| mt | opnovice2 | fast-mixmax | mixmax | 8 | 34.364261 | 3017.30 |

### bench.csv

| host | variant | engine | what | ns |
|:--|--:|--:|--:|--:|
| zen5 | stock | mixmax | G4UniformRand | 2.3756 |
| zen5 | stock | mixmax | getTheEngine_flat | 2.2916 |
| zen5 | stock | mixmax | RandGaussQ | 10.9095 |
| zen5 | stock | mixmax | setSeeds | 23266.2358 |
| zen5 | dropin | mixmax | G4UniformRand | 2.2301 |
| zen5 | dropin | mixmax | getTheEngine_flat | 2.2783 |
| zen5 | dropin | mixmax | RandGaussQ | 10.8821 |
| zen5 | dropin | mixmax | setSeeds | 23178.8888 |
| zen5 | dropin | xoshiro256pp | G4UniformRand | 2.4631 |
| zen5 | dropin | xoshiro256pp | getTheEngine_flat | 2.9064 |
| zen5 | dropin | xoshiro256pp | RandGaussQ | 9.9077 |
| zen5 | dropin | xoshiro256pp | setSeeds | 6629.2726 |
| zen5 | dropin | mwc192x | G4UniformRand | 2.9052 |
| zen5 | dropin | mwc192x | getTheEngine_flat | 3.3509 |
| zen5 | dropin | mwc192x | RandGaussQ | 9.6792 |
| zen5 | dropin | mwc192x | setSeeds | 501.0687 |
| zen5 | fast-mixmax | mixmax | G4UniformRand | 1.4100 |
| zen5 | fast-mixmax | mixmax | getTheEngine_flat | 1.4849 |
| zen5 | fast-mixmax | mixmax | RandGaussQ | 8.8685 |
| zen5 | fast-mixmax | mixmax | setSeeds | 23054.5567 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | G4UniformRand | 1.1086 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | getTheEngine_flat | 1.3477 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | RandGaussQ | 8.1645 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | setSeeds | 6623.0420 |
| zen5 | fast-mwc192x | mwc192x | G4UniformRand | 0.8391 |
| zen5 | fast-mwc192x | mwc192x | getTheEngine_flat | 1.3432 |
| zen5 | fast-mwc192x | mwc192x | RandGaussQ | 7.9120 |
| zen5 | fast-mwc192x | mwc192x | setSeeds | 500.8949 |

### counts.csv

| mode | workload | events | flat | flatArray | setSeeds | getTheEngine |
|:--|--:|--:|--:|--:|--:|--:|
| st | testem3 | 134 | 20616814 | 17090080 | 1 | 17880860 |
| st | b4hadr | 730 | 17542504 | 12007851 | 1 | 14988439 |
| st | testem11 | 19300 | 19601755 | 24939526 | 1 | 13736671 |
| st | opnovice2 | 440 | 69375633 | 415463 | 1 | 69358674 |
| st | range | 5000 | 12721125 | 0 | 1 | 12721131 |
| mt | testem3 | 610 | 93878764 | 77727632 | 611 | 81426163 |
| mt | b4hadr | 3700 | 91806623 | 63436130 | 3701 | 78358343 |
| mt | testem11 | 92000 | 93460274 | 119098453 | 92001 | 65491111 |
| mt | opnovice2 | 2300 | 355915881 | 2275841 | 2301 | 355828373 |
| mt | range | 25000 | 63837408 | 50000 | 25001 | 63837488 |
