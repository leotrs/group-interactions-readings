# Supplementary File S3: models with a separate rate for two or more adopters

None of the three models in the main text can represent a rate that is zero with one
adopter present and positive with two. This supplement fits two models that can, in the
main setting (File S1), with 20 runs (seeds 0 to 19).

## Models

For a person who has not adopted, with a_i adopters in contact now and a_e adopters in
each of the person's current recorded groups e:

- graph form: rate = lam * a_i + mu * [a_i >= 2] + b;
- group form: rate = lam * a_i + mu * (number of groups e with a_e >= 2) + b.

On the meeting log a person is in one gathering at a time, so the two forms are the same
model. Fitting, held-out misfit and the causal effect follow File S1: maximum likelihood
on the first spreading process, misfit on the second, and the effect computed from the
fitted rule without b (together: rate 2 * lam + mu for 900 s; one at a time: rate lam
for 900 s, twice).

The numbers in the main text and Figure 2C come from the main study code, where the
group form is fitted in the same runs as the three compared models (File S1). This
supplement is an independent check: its code was written apart from the main study code,
from File S1 alone, and draws its own random gatherings and sensor records. Its medians
differ from those of the main runs by at most 6 points (mixed world, log: 36.7 here,
31.2 there), and it gives the same pattern: close to the true effect on the meeting log,
and a false group effect on the sensors in the pairwise world (11.3 here, 10.1 there).
As a check, its nonlinear graph model fitted to the meeting log predicts 13.6 points in
the group world and 7.6 in the mixed world, against about 14 and about 7 or less in the
main text.

## Predicted effect of meeting two adopters together rather than one at a time

Percentage points, median over runs (interquartile range).

| world (true effect) | record | nonlinear graph | separate rate, graph form | separate rate, group form |
|---|---|---|---|---|
| pairwise (0.0) | log | -0.7 (-3.2 to 2.0) | 0.0 (0.0 to 4.3) | 0.0 (0.0 to 4.3) |
| pairwise (0.0) | sensors | -5.9 (-10.7 to -2.6) | 0.0 (0.0 to 0.0) | 11.3 (9.7 to 13.5) |
| group (63.2) | log | 13.6 (13.0 to 14.6) | 61.7 (60.7 to 63.6) | 61.7 (60.7 to 63.6) |
| group (63.2) | sensors | 14.1 (10.3 to 18.1) | 33.1 (27.1 to 36.7) | 56.5 (54.2 to 60.2) |
| mixed (35.0) | log | 7.6 (6.8 to 10.1) | 36.7 (31.0 to 39.2) | 36.7 (31.0 to 39.2) |
| mixed (35.0) | sensors | -1.0 (-3.4 to 5.8) | 6.6 (1.7 to 12.7) | 35.8 (29.1 to 39.5) |

## Held-out misfit against the nonlinear graph model

Runs out of 20 in which the model with a separate rate has the lower held-out misfit (no
ties occurred).

| world | log | sensors, graph form | sensors, group form |
|---|---|---|---|
| pairwise | 12 | 11 | 19 |
| group | 20 | 18 | 20 |
| mixed | 18 | 14 | 20 |

On the sensors in the pairwise world, the group form has the lower held-out misfit in 19
of 20 runs (median difference 26 bits) and predicts an effect of 11 points where there
is none. The sensors miss pairs through which spreading happens, so the recorded
contacts are not the routes of spreading.
