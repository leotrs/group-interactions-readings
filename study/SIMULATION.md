# Supplementary File S1: simulation details

This file gives the full specification of the simulated study in the paper, so that it
can be rebuilt without the code. Values are those of the main setting. Times are in
seconds unless stated. The code that implements each part is named in brackets.

## Event and gatherings [world.py]

- 200 people, 3 days of 8 hours. The 24 hours of event time are one continuous period;
  "day" means one of the three consecutive 8-hour blocks.
- Gatherings start at the times of a Poisson process over the whole event, at 10.88 per
  hour (0.0030220 per second).
- At each start time, the people who are free are those whose last gathering has ended.
  If fewer than 2 are free, no gathering forms. Otherwise the size is drawn uniformly
  from 2, 3, 4, 5 and 6 (capped at the number of free people), and the members are drawn
  uniformly without replacement from the free people.
- Each gathering lasts an exponentially distributed time with mean 15 minutes, cut at
  the end of the event.
- The rate of 10.88 per hour was set by bisection so that each person is with 6 distinct
  people a day on average. That number is computed for each day from the gatherings that
  start in it, as the number of distinct other people that a person shares a gathering
  with, averaged over people and days.

## Spreading [world.py, tune.py]

- Each spreading process starts with 24 first adopters drawn uniformly at random.
  Adoption is permanent.
- A person who has not adopted and is in a gathering with k adopters adopts at rate
  - pairwise world: lam * k, with lam = 0.469 per hour (1.3013e-4 per second);
  - group world: mu if k >= 2 and 0 otherwise, with mu = 4 per hour (1/900 per second);
  - mixed world: (lam / 2) * k + (mu / 2 if k >= 2).
  There is no adoption outside gatherings.
- Tuning, in this order: mu is fixed at 1/900 per second; the number of first adopters
  is the smallest, counting up from 2, at which at least half of the people adopt in the
  group world (24); with those, lam is found by bisection on a log scale so that half
  adopt in the pairwise world. Each check averages 30 runs. In the main setting, 49% to
  61% of people adopt, by world, counting the first adopters.
- Spreading is simulated exactly: between the start or end of a gathering and the next
  adoption, all rates are constant, so the time to the next adoption is exponential.

## Runs and records [run.py, record.py]

- A run draws one set of gatherings, then, for each world, two independent spreading
  processes over them, each with its own 24 first adopters. The first process is used
  for fitting and the second is held out.
- Meeting log: every gathering with its members, start and end, plus the adoption times.
- Sensors: samples at every multiple of 20 seconds from the start of the event. At each
  sample that falls inside a gathering, each pair in the gathering is detected
  independently with probability 0.5. A detected pair is recorded as in contact for the
  20 seconds after the sample (cut at the end of the event, not at the end of the
  gathering). The recorded groups at a sample are the connected components of the graph
  of pairs detected at that sample, each present for the same 20 seconds. The sensor
  record also includes the adoption times.

## Models and fitting [model.py]

- For a person i who has not adopted, with a_i adopters in contact now and a_e adopters
  in each current recorded group e:
  - linear graph: lam * a_i + b;
  - nonlinear graph: lam * a_i^nu + b;
  - hypergraph: lam * sum over e of a_e^nu + b.
  On the log, "in contact" means in the same gathering. On the sensors, it means in a
  pair detected within the last 20 seconds.
- Likelihood: the usual one for event times, in seconds. It is the sum of the log rates
  at the adoptions minus the integral of all rates over the event. The first adopters
  are taken as given.
- Fit: maximum likelihood with L-BFGS-B, over log lam and log b (both bounded to [-40,
  5]) and nu in [0.05, 6], from 9 starting points for the linear model and 36 for the
  others; the best fit is kept.

## Scores [run.py, structure.py, report.py]

- Structure bits (Rommens et al., Proposition 7; the mixed-size form is ours). Only who
  met whom is coded, not when.
  - Graph: log2(P + 1) + log2 C(P, m), with P = C(200, 2) and m the number of distinct
    pairs.
  - Hypergraph: log2(200) for the largest size, then for each size k from 2 up to it,
    log2(S_k + 1) + log2 C(S_k, M_k), with S_k = C(200, k) and M_k the number of
    distinct groups of size k.
- Rule bits: (1/2) log2(n) for each parameter, with n the number of adoptions in the
  fitted process, not counting first adopters. The linear graph model has 2 parameters
  (lam, b); the other two have 3 (lam, b, nu).
- Misfit: minus the log-likelihood, in bits, of the held-out process under the
  parameters fitted to the first process. Because adoption times are continuous, this is
  a density in seconds; the time unit shifts all three models by the same amount and
  changes no comparison.
- Message length: structure bits plus rule bits plus misfit.
- Ties: models whose scores differ by at most 1e-6 bits share the win.

## Causal effect [run.py, model.py]

- A person who has not adopted meets two adopters either together, in one gathering of
  15 minutes, or one at a time, in two gatherings of 15 minutes each. The effect is the
  chance of adopting together minus the chance one at a time.
- True chances from the world's rule: 1 - exp(-r(2) * 900) together and 1 - exp(-2 *
  r(1) * 900) one at a time, with r(k) the rate above.
- Predicted chances from each fitted model, without the background rate b: 1 - exp(-lam
  * 2^nu * 900) together and 1 - exp(-2 * lam * 900) one at a time (nu = 1 for the
  linear graph model). These are the same for a record of either kind.
- Reported: the median over runs, with the interquartile range.

## Settings [common.py, record.py, run.py, tune.py]

The main setting uses the values above. Each other setting changes one hyperparameter
from its main value, for 14 settings in all (the main one and 13 changes). Each setting
has 20 runs, with run seeds 0 to 19.

- People met a day: 6 in the main setting; also 3, 10 and 25. For each value, the
  gathering rate, the number of first adopters and lam are tuned again as above.
- Sensor detection probability: 0.5; also 0.25, 0.75 and 1.
- Sensor sampling interval: 20 seconds; also 60 and 300. A detection stands for one
  interval after its sample.
- Delay in recorded adoption times: none; also a mean of 5 and 30 minutes. Each
  recorded adoption time, except those of first adopters, is the true time plus an
  exponentially distributed delay with that mean. An adoption whose recorded time
  falls after the end of the event is not recorded.
- Spreading processes fitted: 1; also 5 and 10. With k processes, the models are fitted
  to k independent processes over the same gatherings and scored on k others.
- Sensor groups: the connected components of detected pairs at each sample; also one
  group per gathering, made of everyone detected in it at any sample, present from its
  first sample to the end of its last. The second uses the true gathering times, which
  real sensors do not record, and serves only as a check.

## Model with a group rate, for the causal effect only [model.py, run.py]

- rate = lam * a_i + mu * (number of the person's current recorded groups e with a_e >= 2)
  + b, with a_i and a_e as in "Models and fitting". On the meeting log a person is in
  one gathering at a time, so the group term is mu when at least two adopters share the
  person's gathering.
- Fitted by maximum likelihood to the first process, like the other models, over log lam,
  log b and log mu (each bounded to [-40, 5]) from 27 starting points.
- It is not part of the comparisons by message length or held-out misfit. Its predicted
  effect uses together = 1 - exp(-(2 * lam + mu) * 900) and one at a time = 1 - exp(-2 *
  lam * 900), without b. Figure 2C shows it as hollow diamonds.
- Main setting, 20 runs: median predicted effect 63.5 points on the log and 56.4 on the
  sensors in the group world, 31.2 and 30.3 in the mixed world, and 0.0 and 10.1 in the
  pairwise world. On the sensors in the pairwise world, its held-out misfit is lower than
  that of the nonlinear graph model in 20 of 20 runs.
