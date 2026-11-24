## Hardware counters against drop-in MIXMAX (perf stat, user space)

Per event: mean change (± sd over reps). Per draw: mean change of the counter per event divided by the draws per event (counts.csv).

### opnovice2 (1.586e+05 draws/event)

| configuration | cycles/event | instructions/event | IPC | cycles/draw | instr./draw | branch-misses/draw | L1i misses/draw | L1d misses/draw | reps |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| dropin mixmax | +0.00% ± 0.00 | +0.00% ± 0.00 | 2.557 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | 4 |
| dropin mwc192x | -3.91% ± 0.73 | -2.33% ± 0.55 | 2.599 | -8.18 | -12.48 | -0.06 | -0.31 | -0.27 | 4 |
| dropin xoshiro256pp | -3.76% ± 0.73 | -0.39% ± 0.53 | 2.647 | -7.87 | -2.12 | -0.07 | -0.36 | -0.25 | 4 |
| fast-mixmax mixmax | -5.40% ± 0.26 | -3.33% ± 0.00 | 2.613 | -11.30 | -17.82 | -0.01 | -0.51 | -0.09 | 4 |
| stock mixmax | -0.56% ± 2.88 | +0.02% ± 0.00 | 2.574 | -1.14 | +0.10 | +0.01 | -0.57 | -0.18 | 4 |

### testem3 (2.814e+05 draws/event)

| configuration | cycles/event | instructions/event | IPC | cycles/draw | instr./draw | branch-misses/draw | L1i misses/draw | L1d misses/draw | reps |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| dropin mixmax | +0.00% ± 0.00 | +0.00% ± 0.00 | 2.127 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | 4 |
| dropin mwc192x | -2.10% ± 0.42 | -1.71% ± 0.03 | 2.135 | -8.11 | -13.98 | -0.11 | +0.15 | +0.40 | 4 |
| dropin xoshiro256pp | -2.20% ± 0.51 | -1.01% ± 0.05 | 2.152 | -8.49 | -8.30 | -0.11 | +0.20 | +0.20 | 4 |
| fast-mixmax mixmax | -2.59% ± 0.34 | -1.22% ± 0.00 | 2.157 | -9.99 | -9.99 | -0.01 | -1.24 | +0.15 | 4 |
| stock mixmax | -0.64% ± 0.82 | -0.00% ± 0.00 | 2.140 | -2.47 | -0.00 | +0.01 | -0.09 | +0.66 | 4 |

