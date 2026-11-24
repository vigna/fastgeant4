## Single-threaded

### Reference and noise

| workload | drop-in MIXMAX ms/event | run-to-run CV | layout band | reps | stock vs. drop-in MIXMAX |
|:--|--:|--:|--:|--:|--:|
| testem3 | 24 | 0.65% | 1.11% | 22 | -0.56% [-0.90, -0.22] (n.s.) |
| b4hadr | 4.549 | 1.25% | 0.92% | 22 | +0.27% [+0.16, +0.38] (n.s.) |
| testem11 | 0.1744 | 0.41% | 2.13% | 22 | +1.71% [+1.47, +1.95] (n.s.) |
| opnovice2 | 7.194 | 0.93% | 1.20% | 22 | +2.13% [+1.66, +2.59] |
| range | 0.6638 | 0.47% | 1.11% | 22 | +0.90% [+0.64, +1.16] (n.s.) |

### A. Drop-in engines vs. drop-in MIXMAX (same binary)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +2.02% [+1.70, +2.34] | +2.03% [+1.70, +2.37] |
| b4hadr | +2.08% [+1.33, +2.85] | +1.63% [+0.91, +2.35] |
| testem11 | +1.19% [+0.74, +1.63] | +2.21% [+1.93, +2.49] |
| opnovice2 | +2.94% [+2.11, +3.77] | +3.64% [+3.05, +4.24] |
| range | +1.18% [+0.92, +1.44] | +1.47% [+1.22, +1.72] |

### B. Fast-path engines vs. fast-path MIXMAX (generator effect on the fast path)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem3 | +0.47% [-0.22, +1.16] (n.s.) | +1.20% [+0.89, +1.51] (n.s.) |
| b4hadr | +1.23% [+0.41, +2.05] (n.s.) | +1.46% [+0.77, +2.15] (n.s.) |
| testem11 | +0.85% [+0.08, +1.62] (n.s.) | +1.93% [+1.64, +2.23] (n.s.) |
| opnovice2 | +2.82% [+1.79, +3.85] | +4.78% [+4.27, +5.29] |
| range | +1.22% [+0.91, +1.53] (n.s.) | +2.21% [+1.91, +2.51] |

### Call path: fast path vs. drop-in, same engine

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +2.54% [+2.32, +2.77] | +0.98% [+0.28, +1.69] (n.s.) | +1.71% [+1.49, +1.93] |
| b4hadr | +1.60% [+1.44, +1.77] | +0.75% [+0.53, +0.97] (n.s.) | +1.43% [+1.28, +1.59] |
| testem11 | +3.59% [+3.32, +3.85] | +3.24% [+2.61, +3.87] | +3.31% [+3.04, +3.58] |
| opnovice2 | +6.08% [+5.79, +6.38] | +5.96% [+5.58, +6.34] | +7.24% [+6.93, +7.56] |
| range | +0.71% [+0.36, +1.06] (n.s.) | +0.75% [+0.48, +1.01] (n.s.) | +1.45% [+1.24, +1.66] |

### Total: fast-path engine vs. drop-in MIXMAX

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +2.54% [+2.32, +2.77] | +3.03% [+2.31, +3.75] | +3.77% [+3.45, +4.09] |
| b4hadr | +1.60% [+1.44, +1.77] | +2.85% [+2.05, +3.66] | +3.08% [+2.34, +3.84] |
| testem11 | +3.59% [+3.32, +3.85] | +4.46% [+3.73, +5.21] | +5.59% [+5.32, +5.86] |
| opnovice2 | +6.08% [+5.79, +6.38] | +9.07% [+8.06, +10.09] | +11.15% [+10.62, +11.68] |
| range | +0.71% [+0.36, +1.06] (n.s.) | +1.93% [+1.58, +2.29] | +2.93% [+2.69, +3.17] |

### Total: fast-path engine vs. stock

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem3 | +3.12% [+2.72, +3.52] | +3.61% [+2.86, +4.36] | +4.36% [+4.00, +4.72] |
| b4hadr | +1.33% [+1.19, +1.47] | +2.57% [+1.74, +3.42] | +2.81% [+2.05, +3.57] |
| testem11 | +1.84% [+1.63, +2.06] (n.s.) | +2.71% [+2.00, +3.42] (n.s.) | +3.81% [+3.57, +4.06] |
| opnovice2 | +3.87% [+3.46, +4.29] | +6.80% [+5.78, +7.83] | +8.84% [+8.46, +9.21] |
| range | -0.19% [-0.51, +0.14] (n.s.) | +1.03% [+0.76, +1.29] (n.s.) | +2.02% [+1.81, +2.22] |

### Predicted / measured drop-in speedup (from counts and microbenchmarks)

| workload | draws/event | via getTheEngine | reseeds/event | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|--:|--:|
| testem3 | 2.814e+05 | 47% | 0.00746 | +1.34% / +2.02% | +1.34% / +2.03% |
| b4hadr | 4.048e+04 | 51% | 0.00137 | +1.02% / +2.08% | +1.02% / +1.63% |
| testem11 | 2308 | 31% | 5.18e-05 | +1.52% / +1.19% | +1.52% / +2.21% |
| opnovice2 | 1.586e+05 | 99% | 0.00227 | +2.55% / +2.94% | +2.56% / +3.64% |
| range | 2544 | 100% | 0.0002 | +0.44% / +1.18% | +0.44% / +1.47% |

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
