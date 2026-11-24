## Multithreaded

### Reference and noise

| workload | drop-in MIXMAX ms/event | run-to-run CV | layout band | reps | stock vs. drop-in MIXMAX |
|:--|--:|--:|--:|--:|--:|
| testem3 | 0.4064 | 0.37% | 0.56% | 10 | -0.52% [-0.84, -0.20] (n.s.) |
| b4hadr | 0.06705 | 0.55% | 0.39% | 10 | +0.04% [-0.17, +0.26] (n.s.) |
| testem11 | 0.00275 | 0.56% | 0.85% | 10 | +0.58% [+0.17, +0.99] (n.s.) |
| opnovice2 | 0.1135 | 0.44% | 0.55% | 10 | +1.03% [+0.86, +1.20] |
| range | 0.01042 | 0.28% | 0.75% | 10 | +0.13% [-0.07, +0.33] (n.s.) |

### A. Drop-in engines vs. drop-in MIXMAX (same binary)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +1.39% [+1.10, +1.67] | +1.48% [+1.34, +1.63] |
| b4hadr | +1.65% [+1.25, +2.04] | +1.89% [+1.56, +2.21] |
| testem11 | +8.02% [+7.47, +8.56] | +11.52% [+10.96, +12.07] |
| opnovice2 | +2.38% [+2.05, +2.72] | +2.78% [+2.46, +3.11] |
| range | +2.68% [+2.39, +2.97] | +3.57% [+3.25, +3.89] |

### B. Fast-path engines vs. fast-path MIXMAX (generator effect on the fast path)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +0.59% [-0.33, +1.53] (n.s.) | +1.30% [+1.09, +1.52] |
| b4hadr | +1.04% [+0.50, +1.58] | +1.46% [+1.04, +1.88] |
| testem11 | +7.91% [+7.08, +8.74] | +12.18% [+11.68, +12.68] |
| opnovice2 | +2.27% [+1.75, +2.78] | +3.94% [+3.57, +4.32] |
| range | +3.14% [+2.83, +3.44] | +4.19% [+3.84, +4.54] |

### Call path: fast path vs. drop-in, same engine

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.79% [+1.59, +1.98] | +0.99% [-0.02, +2.01] (n.s.) | +1.61% [+1.41, +1.81] |
| b4hadr | +1.50% [+1.20, +1.80] | +0.89% [+0.62, +1.16] | +1.07% [+0.85, +1.29] |
| testem11 | +2.13% [+1.79, +2.47] | +2.03% [+1.35, +2.71] | +2.74% [+2.30, +3.18] |
| opnovice2 | +5.43% [+5.23, +5.63] | +5.31% [+4.93, +5.69] | +6.62% [+6.37, +6.87] |
| range | +0.61% [+0.43, +0.80] (n.s.) | +1.07% [+0.84, +1.29] | +1.22% [+0.78, +1.65] |

### Total: fast-path engine vs. drop-in MIXMAX

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +1.79% [+1.59, +1.98] | +2.39% [+1.53, +3.26] | +3.12% [+2.93, +3.30] |
| b4hadr | +1.50% [+1.20, +1.80] | +2.55% [+2.04, +3.06] | +2.98% [+2.59, +3.38] |
| testem11 | +2.13% [+1.79, +2.47] | +10.20% [+9.37, +11.04] | +14.57% [+14.04, +15.10] |
| opnovice2 | +5.43% [+5.23, +5.63] | +7.82% [+7.27, +8.37] | +9.59% [+9.20, +9.98] |
| range | +0.61% [+0.43, +0.80] (n.s.) | +3.77% [+3.47, +4.07] | +4.83% [+4.57, +5.09] |

### Total: fast-path engine vs. stock

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +2.32% [+2.02, +2.62] | +2.93% [+2.02, +3.84] | +3.65% [+3.32, +3.99] |
| b4hadr | +1.46% [+1.22, +1.69] | +2.51% [+2.01, +3.01] | +2.94% [+2.50, +3.37] |
| testem11 | +1.54% [+1.17, +1.91] | +9.57% [+8.75, +10.40] | +13.91% [+13.50, +14.32] |
| opnovice2 | +4.36% [+4.15, +4.56] | +6.72% [+6.28, +7.17] | +8.47% [+8.17, +8.77] |
| range | +0.49% [+0.33, +0.65] (n.s.) | +3.64% [+3.27, +4.00] | +4.70% [+4.30, +5.09] |

### Predicted / measured drop-in speedup (from counts and microbenchmarks)

| workload | draws/event | via getTheEngine | reseeds/event | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|--:|--:|
| testem3 | 2.813e+05 | 47% | 1 | +1.04% / +1.39% | +1.06% / +1.48% |
| b4hadr | 4.196e+04 | 50% | 1 | +1.06% / +1.65% | +1.16% / +1.89% |
| testem11 | 2310 | 31% | 1 | +8.04% / +8.02% | +10.83% / +11.52% |
| opnovice2 | 1.557e+05 | 99% | 1 | +1.99% / +2.38% | +2.05% / +2.78% |
| range | 2555 | 100% | 1 | +2.08% / +2.68% | +2.74% / +3.57% |

Speedups are 1/ratio − 1 of event-loop time per event (geometric mean of the ratios of runs paired by repetition), with 95% Student-t intervals; (n.s.) marks intervals that do not exclude no change (or, across binaries, the layout band). MT predictions compare the CPU time saved with the thread time per event. Predictions use the microbenchmark's time per call, which understates the in-situ cost of a draw: on a wide out-of-order core the benchmark loop overlaps successive calls (scripts/bench-instr.sh, scripts/perfstat.py: the instructions saved per draw agree, the cycles do not). xoshiro256pp and mwc192x are seeded by jumping (distinct seeds give non-overlapping streams, as MIXMAX's).

### bench.csv

| host | variant | engine | what | ns |
|:--|--:|--:|--:|--:|
| zen5 | stock | mixmax | G4UniformRand | 2.3643 |
| zen5 | stock | mixmax | getTheEngine_flat | 2.2660 |
| zen5 | stock | mixmax | RandGaussQ | 10.8838 |
| zen5 | stock | mixmax | setSeeds | 23238.5928 |
| zen5 | dropin | mixmax | G4UniformRand | 3.5882 |
| zen5 | dropin | mixmax | getTheEngine_flat | 2.2789 |
| zen5 | dropin | mixmax | RandGaussQ | 10.8782 |
| zen5 | dropin | mixmax | setSeeds | 23408.1423 |
| zen5 | dropin | xoshiro256pp | G4UniformRand | 2.4590 |
| zen5 | dropin | xoshiro256pp | getTheEngine_flat | 2.9039 |
| zen5 | dropin | xoshiro256pp | RandGaussQ | 9.7445 |
| zen5 | dropin | xoshiro256pp | setSeeds | 6584.5555 |
| zen5 | dropin | mwc192x | G4UniformRand | 2.4572 |
| zen5 | dropin | mwc192x | getTheEngine_flat | 2.4579 |
| zen5 | dropin | mwc192x | RandGaussQ | 9.7107 |
| zen5 | dropin | mwc192x | setSeeds | 500.8054 |
| zen5 | fast-mixmax | mixmax | G4UniformRand | 1.4081 |
| zen5 | fast-mixmax | mixmax | getTheEngine_flat | 1.4880 |
| zen5 | fast-mixmax | mixmax | RandGaussQ | 8.8524 |
| zen5 | fast-mixmax | mixmax | setSeeds | 18463.8777 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | G4UniformRand | 1.1081 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | getTheEngine_flat | 1.3453 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | RandGaussQ | 8.2477 |
| zen5 | fast-xoshiro256pp | xoshiro256pp | setSeeds | 6585.0545 |
| zen5 | fast-mwc192x | mwc192x | G4UniformRand | 0.8408 |
| zen5 | fast-mwc192x | mwc192x | getTheEngine_flat | 1.3408 |
| zen5 | fast-mwc192x | mwc192x | RandGaussQ | 7.9232 |
| zen5 | fast-mwc192x | mwc192x | setSeeds | 501.8746 |

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
