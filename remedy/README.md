# Remedy side test

This folder tests a "remedy" graph model, which adds a group term to the linear graph model:

- graph form: rate = lam * a_i + mu * [a_i >= 2] + b
- group form: rate = lam * a_i + mu * (number of the person's current recorded groups e with a_e >= 2) + b

The models are fitted to the simulated study in the main setting. The code was written from
`../study/SIMULATION.md` alone. No other file from `study/` or `paper/` was read or used.

## What was run

- World: 200 people, 24 hours of event time, gatherings started by a Poisson process at
  0.0030220 per second, sizes uniform from 2 to 6 among free people, exponential durations
  with mean 900 s, 24 first adopters. The three worlds use lam = 1.3013e-4 and mu = 1/900 per
  second. Spreading is simulated exactly, event by event (`sim.py`).
- Records: the meeting log, and sensors sampled every 20 s. Each pair in a gathering is
  detected with probability 0.5 at each sample and counts as in contact for the next 20 s.
  The recorded groups are the connected components of the detected pairs at each sample
  (`sim.py`).
- Runs: seeds 0 to 19. Each run draws one set of gatherings and one sensor record. The same
  sensor record is used for all three worlds and for both spreading processes of the run
  (SIMULATION.md does not say whether the paper draws it once per run; this is my choice).
  For each world there are two spreading processes: the first is used for fitting and the
  second is held out.
- Fitting (`stats.py`, `fit.py`): maximum likelihood with L-BFGS-B. The log-likelihood is the
  sum of the log rates at adoptions minus the integral of all rates, with the first adopters
  taken as given. Each model's rate depends only on (a, c): a is the number of adopters among
  the person's contacts and c is the number of adopters in the person's current group. A person
  is in at most one recorded group at a time on either record, because a person is in at most
  one gathering at each sample. So the likelihood is computed exactly from the time spent at
  each (a, c) and the number of adoptions at each (a, c).
  - nonlinear graph model: log lam and log b in [-40, 5], nu in [0.05, 6], 36 starting points;
  - remedy models: log lam, log mu and log b in [-40, 5], 27 starting points.
- Effect: P(adopt with both adopters in one 900 s meeting) minus P(adopt over two 900 s
  meetings with one adopter each), from the fitted rule without b.

## How to run

```
just check    # implementation checks on 3 seeds (about 10 s)
just run      # 20 runs with 3 worker processes, then writes RESULTS.md (about 10 s)
just report   # rewrites and prints RESULTS.md from results/runs.json
```

`check.py` recomputes the time spent at each (a, c) on a 1-second grid and recounts the
adoptions at each (a, c) by a separate scan. It also refits the remedy models on the linear
scale, where the log-likelihood is concave, to confirm that the log-scale fits reach the
global maximum.

## Files

- `sim.py`: gatherings, spreading, sensor record
- `stats.py`: time spent and adoptions at each (a, c)
- `fit.py`: models, likelihood, fits, effect
- `main.py`: the 20 runs, saved to `results/runs.json`
- `report.py`: writes `RESULTS.md`
- `check.py`: implementation checks
