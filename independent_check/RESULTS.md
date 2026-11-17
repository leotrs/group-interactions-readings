# Results

Main setting, 20 runs (seeds 0 to 19). Effects are in percentage points: median over
runs, with the interquartile range in brackets.

## Checks of the simulated world

- Distinct people met per person per day: mean 5.96 (runs 4.88 to 6.87); the
  specification gives 6.
- Gatherings per run: mean 260.
- pairwise world, share of people who adopt (first adopters counted): mean 48.5% over 40
  processes.
- group world, share of people who adopt (first adopters counted): mean 52.6% over 40
  processes.
- mixed world, share of people who adopt (first adopters counted): mean 63.1% over 40
  processes.
- The specification gives 49% to 61% by world.

## Predicted effect of meeting two adopters together rather than apart

| world | true | record | nonlinear graph | group rate, graph form | group rate, group form |
|---|---|---|---|---|---|
| pairwise | 0.00 | log | -0.7 (-3.2 to 2.0) | 0.0 (0.0 to 4.3) | 0.0 (0.0 to 4.3) |
| pairwise | 0.00 | sensors | -5.9 (-10.7 to -2.6) | 0.0 (0.0 to 0.0) | 11.3 (9.7 to 13.5) |
| group | 63.21 | log | 13.6 (13.0 to 14.6) | 61.7 (60.7 to 63.6) | 61.7 (60.7 to 63.6) |
| group | 63.21 | sensors | 14.1 (10.3 to 18.1) | 33.1 (27.1 to 36.7) | 56.5 (54.2 to 60.2) |
| mixed | 35.00 | log | 7.6 (6.8 to 10.1) | 36.7 (31.0 to 39.2) | 36.7 (31.0 to 39.2) |
| mixed | 35.00 | sensors | -1.0 (-3.4 to 5.8) | 6.6 (1.7 to 12.7) | 35.8 (29.1 to 39.5) |

True effects from the world's rule: pairwise 0.0000, group 63.2121, mixed 34.9984
points.

## Median fitted parameters (per second)

World rates: lam = 1.3013e-4 (pairwise), mu = 1.1111e-3 (group); the mixed world has
half of each.

| world | record | model | lam | mu | nu | b |
|---|---|---|---|---|---|---|
| pairwise | log | nonlinear graph | 1.25e-04 | - | 0.94 | 4.25e-18 |
| pairwise | log | group rate, graph form | 1.14e-04 | 5.91e-18 | - | 4.45e-18 |
| pairwise | log | group rate, group form | 1.14e-04 | 5.91e-18 | - | 4.45e-18 |
| pairwise | sensors | nonlinear graph | 1.90e-04 | - | 0.60 | 1.62e-06 |
| pairwise | sensors | group rate, graph form | 1.73e-04 | 4.25e-18 | - | 1.62e-06 |
| pairwise | sensors | group rate, group form | 1.15e-04 | 1.68e-04 | - | 1.30e-06 |
| group | log | nonlinear graph | 5.44e-05 | - | 2.42 | 4.25e-18 |
| group | log | group rate, graph form | 6.91e-18 | 1.07e-03 | - | 5.04e-18 |
| group | log | group rate, group form | 6.91e-18 | 1.07e-03 | - | 5.04e-18 |
| group | sensors | nonlinear graph | 2.15e-04 | - | 1.68 | 9.71e-07 |
| group | sensors | group rate, graph form | 1.84e-04 | 7.03e-04 | - | 9.72e-07 |
| group | sensors | group rate, group form | 2.72e-05 | 1.02e-03 | - | 5.36e-07 |
| mixed | log | nonlinear graph | 1.23e-04 | - | 1.54 | 4.25e-18 |
| mixed | log | group rate, graph form | 6.88e-05 | 5.96e-04 | - | 4.25e-18 |
| mixed | log | group rate, group form | 6.88e-05 | 5.96e-04 | - | 4.25e-18 |
| mixed | sensors | nonlinear graph | 3.12e-04 | - | 0.96 | 1.81e-06 |
| mixed | sensors | group rate, graph form | 2.87e-04 | 1.27e-04 | - | 1.81e-06 |
| mixed | sensors | group rate, group form | 1.03e-04 | 6.11e-04 | - | 1.39e-06 |

## Held-out misfit: group rate models against the nonlinear graph model

Misfit is minus the log-likelihood of the held-out process, in bits, under the
parameters fitted to the first process. All three models have 3 parameters. 'Group rate
lower' counts runs in which the group rate model has lower misfit by more than 1e-06
bits; 'tie' counts runs within that margin. The difference is nonlinear misfit minus
group rate misfit (positive: the group rate model fits better).

| world | record | form | group rate lower | tie | nonlinear lower | median difference (bits) |
|---|---|---|---|---|---|---|
| pairwise | log | graph | 12 | 0 | 8 | 0.2 (-0.5 to 1.3) |
| pairwise | log | group | 12 | 0 | 8 | 0.2 (-0.5 to 1.3) |
| pairwise | sensors | graph | 11 | 0 | 9 | 0.2 (-0.7 to 1.3) |
| pairwise | sensors | group | 19 | 0 | 1 | 26.3 (17.1 to 30.7) |
| group | log | graph | 20 | 0 | 0 | 52.3 (45.8 to 68.3) |
| group | log | group | 20 | 0 | 0 | 52.3 (45.8 to 68.3) |
| group | sensors | graph | 18 | 0 | 2 | 5.1 (1.7 to 8.3) |
| group | sensors | group | 20 | 0 | 0 | 95.2 (85.8 to 126.0) |
| mixed | log | graph | 18 | 0 | 2 | 12.2 (7.6 to 19.2) |
| mixed | log | group | 18 | 0 | 2 | 12.2 (7.6 to 19.2) |
| mixed | sensors | graph | 14 | 0 | 6 | 0.7 (-0.6 to 1.9) |
| mixed | sensors | group | 20 | 0 | 0 | 54.2 (41.7 to 74.6) |

## Notes

- Check against the paper: the paper reports that the nonlinear graph model fitted to
  the meeting log predicts about 15 points in the group world and about 7 or less in the
  mixed world. The table above gives the values from this code.
- On the meeting log, a person is in one gathering at a time, so the two group rate
  forms have the same likelihood and give identical rows.
- The mean share who adopt over 20 runs can fall outside 49% to 61% by chance. `just
  check` measures it over 150 sets of gatherings.
- One sensor record is drawn per run and is used for all worlds and both processes of
  that run.
