# Independent check of the simulated study

This folder is an independent check of the main study in `../study/`. The code was
written from the specification in `../study/SIMULATION.md` alone. No other file from
`../study/` or `../paper/` was read or used. The code draws its own gatherings and
sensor records, so its numbers are close to those of the main study but not the same.
The folder backs Supplementary File S3 of the paper (`SUPPLEMENT.md`).

## Models

For a person who has not adopted, with a_i adopters in contact now and a_e adopters in
each of the person's current recorded groups e:

- nonlinear graph (`nonlinear`): rate = lam * a_i^nu + b;
- group rate, graph form (`group_rate_graph`): rate = lam * a_i + mu * [a_i >= 2] + b;
- group rate, group form (`group_rate_group`): rate = lam * a_i + mu * (number of groups
  e with a_e >= 2) + b.

The names in brackets are the keys in `results/runs.json`.

## What was run

- World: 200 people, 24 hours of event time, gatherings started by a Poisson process at
  0.0030220 per second, sizes uniform from 2 to 6 among free people, exponential
  durations with mean 900 s, 24 first adopters. The three worlds (pairwise, group,
  mixed) use lam = 1.3013e-4 and mu = 1/900 per second. Spreading is simulated exactly,
  event by event (`sim.py`).
- Records: the meeting log, and sensors sampled every 20 s. Each pair in a gathering is
  detected with probability 0.5 at each sample and counts as in contact for the next
  20 s. The recorded groups are the connected components of the detected pairs at each
  sample (`sim.py`).
- Runs: seeds 0 to 19. Each run draws one set of gatherings and one sensor record. The
  same sensor record is used for all three worlds and for both spreading processes of
  the run. SIMULATION.md does not say whether the main study draws it once per run; this
  code does. For each world there are two spreading processes: the first is used for
  fitting and the second is held out.
- Fitting (`stats.py`, `fit.py`): maximum likelihood with L-BFGS-B. The
  log-likelihood is the sum of the log rates at adoptions minus the integral of all
  rates, with the first adopters taken as given. Each model's rate depends only on
  (a, c): a is the number of adopters among the person's contacts and c is the number of
  adopters in the person's current group. A person is in at most one recorded group at
  a time on either record, because a person is in at most one gathering at each sample.
  So the likelihood is computed exactly from the time spent at each (a, c) and the
  number of adoptions at each (a, c).
  - nonlinear graph model: log lam and log b in [-40, 5], nu in [0.05, 6], 36 starting
    points;
  - group rate models: log lam, log mu and log b in [-40, 5], 27 starting points.
- Effect: the probability of adopting in one 900 s meeting with two adopters, minus the
  probability of adopting over two 900 s meetings with one adopter each, from the fitted
  rule without b.
- Held-out misfit: minus the log-likelihood of the held-out process, in bits, under the
  parameters fitted to the first process.

## Files

- `sim.py`: gatherings, spreading and the sensor record
- `stats.py`: time spent and adoptions at each (a, c)
- `fit.py`: models, likelihood, fits and the predicted effect
- `main.py`: the 20 runs, saved to `results/runs.json`
- `report.py`: writes `RESULTS.md` from `results/runs.json`
- `check.py`: checks of the implementation
- `results/runs.json`: fitted parameters, log-likelihoods and effects of every run
- `RESULTS.md`: tables made from `results/runs.json`
- `SUPPLEMENT.md`: Supplementary File S3 of the paper
- `justfile`: the commands below
- `pyproject.toml`, `uv.lock`, `.python-version`: Python and package versions

## How to run

The commands need [uv](https://docs.astral.sh/uv/) and
[just](https://github.com/casey/just). uv installs Python and the packages on the
first run.

```
just run      # 20 runs with 3 worker processes, then writes RESULTS.md (about 15 s)
just check    # checks of the implementation (about 10 s)
just report   # rewrites and prints RESULTS.md from results/runs.json
just verify   # reruns the 20 runs and checks that they equal results/runs.json
```

`check.py` recomputes the time spent at each (a, c) on a 1-second grid and recounts the
adoptions at each (a, c) by a separate scan, on seeds 0 to 2. It also refits the group
rate models on the linear scale, where the log-likelihood is concave, to confirm that
the log-scale fits reach the global maximum. Last, it measures the share of people who
adopt in each world over 150 sets of gatherings.

## Versions and seeds

- Python 3.15, numpy 2.5.5 and scipy 1.18.1, as fixed in `.python-version` and
  `uv.lock`.
- Run s (s = 0 to 19) uses `numpy.random.SeedSequence(s)`, split into 8 streams: one for
  the gatherings, one for the sensor record, and two for each world (the fitted process
  and the held-out process), with the worlds in the order pairwise, group, mixed.
- `check.py` uses the same streams for seeds 0 to 2, and
  `numpy.random.default_rng(12345)` for the 150 sets of gatherings.
- `results/runs.json` has no timing or other values that change between reruns, so
  `just verify` compares the files byte by byte.
