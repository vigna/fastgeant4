## Single-threaded

### Reference and noise

| workload | drop-in MIXMAX ms/event | run-to-run CV | layout band | reps | stock vs. drop-in MIXMAX |
|:--|--:|--:|--:|--:|--:|
| testem3 | 24 | 0.42% | 1.66% | 22 | +1.21% [+1.00, +1.43] (n.s.) |
| b4hadr | 4.523 | 1.34% | 0.98% | 22 | +0.11% [-0.08, +0.30] (n.s.) |
| testem11 | 0.1716 | 0.50% | 0.80% | 22 | +1.24% [+1.00, +1.48] |
| opnovice2 | 7.073 | 0.56% | 0.30% | 22 | +0.61% [+0.30, +0.91] |
| range | 0.6566 | 0.55% | 0.59% | 22 | -0.21% [-0.45, +0.03] (n.s.) |

### A. Drop-in engines vs. drop-in MIXMAX (same binary)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +2.55% [+2.35, +2.75] | +1.56% [+0.08, +3.07] |
| b4hadr | +2.22% [+1.42, +3.03] | +2.00% [+1.29, +2.71] |
| testem11 | +2.54% [+2.27, +2.80] | +2.77% [+2.48, +3.06] |
| opnovice2 | +3.45% [+3.01, +3.89] | +3.63% [+3.26, +4.01] |
| range | +0.71% [+0.48, +0.94] | +0.80% [+0.54, +1.05] |

### B. Fast-path engines vs. fast-path MIXMAX (generator effect on the fast path)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +1.32% [+0.77, +1.87] (n.s.) | +2.20% [+0.84, +3.59] (n.s.) |
| b4hadr | +1.36% [+0.50, +2.22] (n.s.) | +2.32% [+1.67, +2.98] |
| testem11 | -0.47% [-1.18, +0.23] (n.s.) | +2.92% [+2.55, +3.29] |
| opnovice2 | +3.37% [+2.95, +3.79] | +4.97% [+4.64, +5.31] |
| range | +0.33% [+0.16, +0.49] (n.s.) | +1.33% [+1.06, +1.60] |

### Call path: fast path vs. drop-in, same engine

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.86% [+1.66, +2.06] (n.s.) | +0.64% [+0.17, +1.12] (n.s.) | +2.50% [+2.26, +2.75] |
| b4hadr | +0.81% [+0.67, +0.95] (n.s.) | -0.05% [-0.42, +0.32] (n.s.) | +1.13% [+0.99, +1.26] |
| testem11 | +1.25% [+0.95, +1.55] | -1.73% [-2.45, -1.00] | +1.40% [+1.08, +1.72] |
| opnovice2 | +4.06% [+3.78, +4.33] | +3.98% [+3.74, +4.22] | +5.40% [+5.13, +5.68] |
| range | +1.19% [+0.97, +1.41] | +0.80% [+0.64, +0.97] | +1.73% [+1.43, +2.02] |

### Total: fast-path engine vs. drop-in MIXMAX

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.86% [+1.66, +2.06] (n.s.) | +3.21% [+2.68, +3.74] | +4.11% [+2.64, +5.60] |
| b4hadr | +0.81% [+0.67, +0.95] (n.s.) | +2.18% [+1.27, +3.09] | +3.15% [+2.48, +3.82] |
| testem11 | +1.25% [+0.95, +1.55] | +0.77% [-0.02, +1.56] (n.s.) | +4.20% [+3.86, +4.55] |
| opnovice2 | +4.06% [+3.78, +4.33] | +7.56% [+7.19, +7.94] | +9.23% [+8.96, +9.51] |
| range | +1.19% [+0.97, +1.41] | +1.52% [+1.31, +1.73] | +2.54% [+2.23, +2.85] |

### Total: fast-path engine vs. stock

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +0.64% [+0.46, +0.83] (n.s.) | +1.97% [+1.40, +2.54] (n.s.) | +2.86% [+1.46, +4.28] (n.s.) |
| b4hadr | +0.70% [+0.52, +0.88] (n.s.) | +2.07% [+1.17, +2.97] | +3.04% [+2.38, +3.70] |
| testem11 | +0.01% [-0.30, +0.33] (n.s.) | -0.46% [-1.32, +0.40] (n.s.) | +2.93% [+2.56, +3.31] |
| opnovice2 | +3.43% [+3.16, +3.70] | +6.92% [+6.53, +7.31] | +8.58% [+8.29, +8.86] |
| range | +1.40% [+1.22, +1.59] | +1.74% [+1.57, +1.90] | +2.76% [+2.40, +3.11] |

### Predicted / measured drop-in speedup (from counts and microbenchmarks)

| workload | draws/event | via getTheEngine | reseeds/event | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|--:|--:|
| testem3 | 2.814e+05 | 47% | 0.00746 | -0.27% / +2.55% | -0.78% / +1.56% |
| b4hadr | 4.048e+04 | 51% | 0.00137 | -0.21% / +2.22% | -0.60% / +2.00% |
| testem11 | 2308 | 31% | 5.18e-05 | -0.31% / +2.54% | -0.90% / +2.77% |
| opnovice2 | 1.586e+05 | 99% | 0.00227 | -0.52% / +3.45% | -1.49% / +3.63% |
| range | 2544 | 100% | 0.0002 | -0.09% / +0.71% | -0.26% / +0.80% |

Speedups are 1/ratio − 1 of event-loop time per event (geometric mean of the ratios of runs paired by repetition), with 95% Student-t intervals; (n.s.) marks intervals that do not exclude no change (or, across binaries, the layout band). MT predictions compare the CPU time saved with the thread time per event. Predictions use the microbenchmark's time per call, which understates the in-situ cost of a draw: on a wide out-of-order core the benchmark loop overlaps successive calls (scripts/bench-instr.sh, scripts/perfstat.py: the instructions saved per draw agree, the cycles do not). xoshiro256pp and mwc192x are seeded by jumping (distinct seeds give non-overlapping streams, as MIXMAX's).

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
