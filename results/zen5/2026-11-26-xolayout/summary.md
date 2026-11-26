## Single-threaded

### Reference and noise

| workload | drop-in MIXMAX ms/event | run-to-run CV | layout band | reps |
|:--|--:|--:|--:|--:|
| testem11 | – | – | not measured | 0 |

### A. Drop-in engines vs. drop-in MIXMAX (same binary)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem11 | – | – |

### B. Fast-path engines vs. fast-path MIXMAX (generator effect on the fast path)

| workload | xoshiro256pp | mwc192x |
|:--|--:|--:|
| testem11 | – | – |

### Call path: fast path vs. drop-in, same engine

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem11 | – | -1.84% [-2.49, -1.18] | +1.62% [+1.31, +1.93] |

### Total: fast-path engine vs. drop-in MIXMAX

| workload | mixmax | xoshiro256pp | mwc192x |
|:--|--:|--:|--:|
| testem11 | – | – | – |

Speedups are 1/ratio − 1 of event-loop time per event (geometric mean of the ratios of runs paired by repetition), with 95% Student-t intervals; (n.s.) marks intervals that do not exclude no change (or, across binaries, the layout band). MT predictions compare the CPU time saved with the thread time per event. Predictions use the microbenchmark's time per call, which understates the in-situ cost of a draw: on a wide out-of-order core the benchmark loop overlaps successive calls (scripts/bench-instr.sh, scripts/perfstat.py: the instructions saved per draw agree, the cycles do not). xoshiro256pp and mwc192x are seeded by jumping (distinct seeds give non-overlapping streams, as MIXMAX's).
