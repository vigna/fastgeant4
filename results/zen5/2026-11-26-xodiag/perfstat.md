## Hardware counters against drop-in MIXMAX (perf stat, user space)

Per event: mean change (± sd over reps). Per draw: mean change of the counter per event divided by the draws per event (counts.csv).

### testem11 (2308 draws/event)

| configuration | cycles/event | instructions/event | IPC | cycles/draw | instr./draw | branch-misses/draw | L1i misses/draw | L1d misses/draw | reps |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| dropin mixmax | +0.00% ± 0.00 | +0.00% ± 0.00 | 2.394 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | 3 |
| dropin mwc192x | -2.70% ± 0.32 | -1.85% ± 0.04 | 2.415 | -8.97 | -14.70 | -0.08 | +0.21 | -0.52 | 3 |
| dropin xoshiro256pp | -2.33% ± 0.57 | -1.27% ± 0.02 | 2.421 | -7.75 | -10.08 | -0.09 | +0.12 | -0.43 | 3 |
| fast-mixmax mixmax | -0.49% ± 0.28 | -0.90% ± 0.00 | 2.385 | -1.63 | -7.13 | +0.00 | +1.32 | -0.14 | 3 |
| fast-mwc192x mwc192x | -3.63% ± 0.36 | -2.79% ± 0.04 | 2.415 | -12.04 | -22.15 | -0.09 | -0.22 | -0.33 | 3 |
| fast-xoshiro256pp xoshiro256pp | -1.62% ± 0.11 | -2.17% ± 0.02 | 2.381 | -5.36 | -17.24 | -0.10 | +4.17 | -0.65 | 3 |

