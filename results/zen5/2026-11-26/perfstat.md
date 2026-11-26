## Hardware counters against drop-in MIXMAX (perf stat, user space)

Per event: mean change (± sd over reps). Per draw: mean change of the counter per event divided by the draws per event (counts.csv).

### opnovice2 (1.586e+05 draws/event)

| configuration | cycles/event | instructions/event | IPC | cycles/draw | instr./draw | branch-misses/draw | L1i misses/draw | L1d misses/draw | reps |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| dropin mixmax | +0.00% ± 0.00 | +0.00% ± 0.00 | 2.588 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | 4 |
| dropin mwc192x | -3.29% ± 0.70 | -2.15% ± 0.43 | 2.618 | -6.66 | -11.27 | -0.06 | -0.12 | -0.10 | 4 |
| dropin xoshiro256pp | -3.13% ± 0.53 | -0.35% ± 0.49 | 2.662 | -6.33 | -1.86 | -0.06 | -0.12 | -0.01 | 4 |
| fast-mixmax mixmax | -3.48% ± 0.15 | -3.40% ± 0.00 | 2.590 | -7.04 | -17.81 | -0.00 | -0.29 | +0.26 | 4 |
| fast-mwc192x mwc192x | -7.78% ± 0.65 | -6.01% ± 0.41 | 2.638 | -15.73 | -31.47 | -0.06 | -0.59 | -0.06 | 4 |
| fast-xoshiro256pp xoshiro256pp | -6.58% ± 0.82 | -4.46% ± 0.47 | 2.647 | -13.32 | -23.37 | -0.06 | -0.57 | -0.11 | 4 |
| stock mixmax | -0.36% ± 0.75 | +0.02% ± 0.00 | 2.598 | -0.73 | +0.10 | +0.01 | -0.34 | +0.02 | 4 |

### testem3 (2.814e+05 draws/event)

| configuration | cycles/event | instructions/event | IPC | cycles/draw | instr./draw | branch-misses/draw | L1i misses/draw | L1d misses/draw | reps |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| dropin mixmax | +0.00% ± 0.00 | +0.00% ± 0.00 | 2.134 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | 4 |
| dropin mwc192x | -2.40% ± 0.07 | -1.67% ± 0.03 | 2.150 | -9.18 | -13.66 | -0.11 | -0.46 | +0.42 | 4 |
| dropin xoshiro256pp | -2.14% ± 0.17 | -1.01% ± 0.01 | 2.159 | -8.19 | -8.23 | -0.11 | -0.52 | +0.31 | 4 |
| fast-mixmax mixmax | -1.99% ± 0.24 | -1.22% ± 0.00 | 2.151 | -7.63 | -9.99 | -0.02 | -0.61 | -0.09 | 4 |
| fast-mwc192x mwc192x | -4.67% ± 0.51 | -3.18% ± 0.03 | 2.167 | -17.84 | -25.95 | -0.10 | -2.32 | +0.55 | 4 |
| fast-xoshiro256pp xoshiro256pp | -3.27% ± 0.48 | -2.48% ± 0.01 | 2.152 | -12.50 | -20.25 | -0.12 | -0.79 | -0.06 | 4 |
| stock mixmax | -0.98% ± 0.28 | -0.00% ± 0.00 | 2.155 | -3.74 | -0.00 | -0.01 | -1.25 | +0.08 | 4 |

