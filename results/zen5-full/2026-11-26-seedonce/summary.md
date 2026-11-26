## Multithreaded

### Reference and noise

| workload | drop-in MIXMAX ms/event | run-to-run CV | layout band | reps | stock vs. drop-in MIXMAX |
|:--|--:|--:|--:|--:|--:|
| testem3 | 0.4189 | 0.18% | 0.81% | 10 | +0.84% [+0.71, +0.98] (n.s.) |
| b4hadr | 0.06741 | 0.29% | 0.65% | 10 | +0.18% [-0.09, +0.44] (n.s.) |
| testem11 | 0.002491 | 0.71% | 0.77% | 10 | +1.39% [+0.84, +1.94] |
| opnovice2 | 0.1047 | 0.73% | 0.15% | 8 | +0.56% [-0.02, +1.14] (n.s.) |
| range | 0.01003 | 0.17% | 0.32% | 10 | -0.13% [-0.44, +0.19] (n.s.) |

### A. Drop-in engines vs. drop-in MIXMAX (same binary)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +1.58% [+1.36, +1.80] | +1.87% [+1.67, +2.07] |
| b4hadr | +1.57% [+1.24, +1.89] | +1.77% [+1.50, +2.05] |
| testem11 | +1.99% [+1.00, +2.99] | +2.28% [+1.51, +3.05] |
| opnovice2 | +2.37% [+1.57, +3.19] | +2.37% [+1.66, +3.09] |
| range | +0.77% [+0.59, +0.96] | +0.72% [+0.44, +1.00] |

### B. Fast-path engines vs. fast-path MIXMAX (generator effect on the fast path)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +0.05% [-1.35, +1.47] (n.s.) | +2.72% [+2.57, +2.87] |
| b4hadr | +1.40% [+0.86, +1.95] | +1.99% [+1.39, +2.58] |
| testem11 | +0.52% [-0.13, +1.17] (n.s.) | +2.49% [+2.08, +2.91] |
| opnovice2 | +2.25% [+1.66, +2.84] | +3.42% [+3.00, +3.83] |
| range | +0.29% [-0.00, +0.59] (n.s.) | +0.77% [+0.27, +1.27] (n.s.) |

### Call path: fast path vs. drop-in, same engine

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.66% [+1.49, +1.83] | +0.13% [-1.18, +1.46] (n.s.) | +2.51% [+2.32, +2.69] |
| b4hadr | +0.64% [+0.34, +0.94] (n.s.) | +0.48% [+0.02, +0.94] (n.s.) | +0.86% [+0.43, +1.29] (n.s.) |
| testem11 | +1.75% [+1.22, +2.28] | +0.28% [-0.63, +1.20] (n.s.) | +1.97% [+1.31, +2.63] |
| opnovice2 | +4.53% [+3.94, +5.12] | +4.46% [+4.07, +4.84] | +5.81% [+5.50, +6.12] |
| range | +1.15% [+0.82, +1.48] | +0.66% [+0.23, +1.10] (n.s.) | +1.20% [+0.64, +1.76] |

### Total: fast-path engine vs. drop-in MIXMAX

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.66% [+1.49, +1.83] | +1.71% [+0.32, +3.12] (n.s.) | +4.42% [+4.26, +4.59] |
| b4hadr | +0.64% [+0.34, +0.94] (n.s.) | +2.05% [+1.55, +2.56] | +2.64% [+2.26, +3.02] |
| testem11 | +1.75% [+1.22, +2.28] | +2.28% [+1.33, +3.23] | +4.29% [+3.80, +4.77] |
| opnovice2 | +4.53% [+3.94, +5.12] | +6.97% [+6.22, +7.73] | +7.89% [+7.37, +8.43] |
| range | +1.15% [+0.82, +1.48] | +1.44% [+1.02, +1.87] | +1.92% [+1.55, +2.30] |

### Total: fast-path engine vs. stock

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +0.81% [+0.68, +0.94] (n.s.) | +0.86% [-0.50, +2.24] (n.s.) | +3.55% [+3.43, +3.67] |
| b4hadr | +0.47% [+0.07, +0.86] (n.s.) | +1.87% [+1.37, +2.38] | +2.46% [+2.02, +2.90] |
| testem11 | +0.35% [+0.04, +0.67] (n.s.) | +0.88% [+0.24, +1.52] (n.s.) | +2.86% [+2.52, +3.20] |
| opnovice2 | +4.05% [+3.76, +4.34] | +6.43% [+6.03, +6.84] | +7.62% [+7.12, +8.11] |
| range | +1.28% [+0.92, +1.64] | +1.57% [+1.09, +2.06] | +2.05% [+1.63, +2.48] |

### Predicted / measured drop-in speedup (from counts and microbenchmarks)

| workload | draws/event | via getTheEngine | reseeds/event | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|--:|--:|
| testem3 | 2.813e+05 | 47% | 1 | -0.15% / +1.58% | -0.51% / +1.87% |
| b4hadr | 4.196e+04 | 50% | 1 | +0.11% / +1.57% | -0.09% / +1.77% |
| testem11 | 2310 | 31% | 1 | +7.29% / +1.99% | +9.84% / +2.28% |
| opnovice2 | 1.557e+05 | 99% | 1 | -0.20% / +2.37% | -0.84% / +2.37% |
| range | 2555 | 100% | 1 | +1.74% / +0.77% | +2.30% / +0.72% |

Speedups are 1/ratio − 1 of event-loop time per event (geometric mean of the ratios of runs paired by repetition), with 95% Student-t intervals; (n.s.) marks intervals that do not exclude no change (or, across binaries, the layout band). MT predictions compare the CPU time saved with the thread time per event. Predictions use the microbenchmark's time per call, which understates the in-situ cost of a draw: on a wide out-of-order core the benchmark loop overlaps successive calls (scripts/bench-instr.sh, scripts/perfstat.py: the instructions saved per draw agree, the cycles do not). xoshiro256pp and mwc192x are seeded by jumping (distinct seeds give non-overlapping streams, as MIXMAX's).

### Runs screened out (lost CPU to other processes)

| mode | workload | variant | engine | rep | real s | CPU s |
|:--|--:|--:|--:|--:|--:|--:|
| mt | opnovice2 | dropin | xoshiro256pp | 1 | 35.332753 | 3091.62 |
| mt | opnovice2 | fast-mixmax | mixmax | 2 | 34.468071 | 3027.29 |
| mt | opnovice2 | dropin-layout-noreorder | mixmax | 2 | 35.56182 | 3159.90 |
| mt | opnovice2 | dropin | mixmax | 2 | 35.423129 | 3148.98 |
| mt | opnovice2 | fast-mwc192x | mwc192x | 4 | 32.793569 | 2910.42 |
| mt | opnovice2 | fast-mixmax | mixmax | 7 | 33.335601 | 3035.26 |
| mt | opnovice2 | stock | mixmax | 9 | 35.847076 | 3136.99 |
| mt | opnovice2 | dropin | mixmax | 9 | 35.832384 | 3152.78 |
| mt | opnovice2 | dropin-layout-name | mixmax | 9 | 35.884776 | 3142.43 |

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
