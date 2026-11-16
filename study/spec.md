# Study spec (revised 2026-11-13: follows Rommens et al.; timed contacts)

Purpose: run the benchmark Rommens et al. call for (arXiv 2609.26031v2, Sec. 8, p. 22),
follow its verdict to a claim about the real system, and check that claim against an
experiment in the same simulated world.

Each requirement taken from their paper is marked [R, section, page]. All quotes were
checked in the arXiv v2 PDF on 2026-11-13.

## World

- 200 people at a 3-day workplace event, 8 hours a day.
- People gather at random: gatherings of 2 to 6 people, members drawn from those not
  already in a gathering, lengths exponential with mean 15 minutes. One gathering at a
  time per person.
- Adopters at the start: tuned in tune.py so that about half of people adopt (24 in the
  pilot). Adoption is permanent.

## Factor 1: adoption mechanism (3 levels) [R, Sec. 8, p. 22: "systems built to be
pairwise, systems built to depend on groups, and ambiguous cases"]

- Independent (built to be pairwise): each adopter in your gathering converts you at
  rate lambda.
- Joint (built to depend on groups): while at least two adopters are in your gathering,
  you adopt at rate mu.
- Ambiguous (both): while in a gathering with k adopters, you adopt at rate
  lambda * k + mu * [k >= 2], with lambda and mu each at half their values in the two
  pure mechanisms.

lambda and mu are set by hand so that about half of people adopt by the end. No run is
filtered out.

## Factor 2: data recording [R, Sec. 8: "partial observation varied independently"]

- Meeting log: every gathering with its start, end and attendees, plus adoption times.
- Proximity sensors: every 20 seconds, each pair in the same gathering is detected with
  probability d; no detections outside gatherings. Plus adoption times.
- Noise, varied independently of recording: each recorded adoption time is the true
  time plus a random delay, exponential with mean delta. delta = 0 in the pilot; it is
  swept after.

## Structures (fixed skeleton) [R, Sec. 4.3, pp. 14-15]

Both structures are fixed by the record, not optimized. The paper: "Mixing these
problems creates artificial description-length advantages for whichever side is
allowed to optimize."

Both recordings keep times, and every contact counts only while it is present.
(Revised 2026-11-13: an earlier version treated every recorded contact as present for
the whole event, which pushed the fitted exponent up in every world; that version is in
git commit 58b1057.)

- Graph G: pair contacts with times. Log: every pair in a gathering, for the length of
  the gathering. Sensors: every pair detected at a sample, for the 20 s that follow.
- Hypergraph H: group contacts with times. Log: every gathering. Sensors: at each
  sample, the connected parts of the detected pairs, for the 20 s that follow. A person
  is in one gathering at a time, so a part never mixes two gatherings.

## Rule classes (stated, as required) [R, Sec. 4.3, p. 15: "Which rule classes are
admissible is a modeling decision and should be stated"]

Continuous-time adoption rates, with a background rate b; all parameters shared across
people [R, Sec. 5, p. 15: "Parameters shared across nodes are encoded once"].

- Graph, linear: rate = lambda * (adopted people in contact now) + b.
- Graph, nonlinear: rate = lambda * (adopted people in contact now)^nu + b.
- Hypergraph: rate = lambda * sum over your groups present now of (adopters in it)^nu
  + b.

Non-nesting check [R, Sec. 4.3, p. 14: the comparison is vacuous if the classes are
nested]: on the meeting log, a person's contacts at any moment are exactly the people in
that person's one gathering, so the nonlinear graph rule and the hypergraph rule give
the same rates (checked by a test). The classes differ only on the sensors, through
missed detections.

Comparable regularization [R, Sec. 5, p. 15: "graph and hypergraph rules must be
regularized at comparable strength"]: the nonlinear graph and the hypergraph rule have
the same three parameters at the same precision.

## Criterion: Eq. (29) [R, Sec. 5, p. 15]

L = L_L(S) + L_C(D | S) - log2 p(D | S, D), in bits.

- Structure code, Proposition 7 [R, Sec. 6.2, p. 17]: name the edges among all pairs,
  log2 C(C(N,2), m); name the hyperedges among the k-subsets, log2 C(C(N,k), M_k),
  summed over sizes k. Extending it to mixed sizes (plus the counts M_k) is ours. The
  code counts who met whom, not when; the times are not coded.
- Rule code: each parameter at "1/2 log2 n bits each for n observed transitions"
  [R, Sec. 5, p. 15].
- Fit: minus log2 of the continuous-time likelihood of the adoption times.
- Main criterion: held-out message length [R, Sec. 8, p. 22: "encode both structure and
  rule, and compare their held-out message lengths"]: structure bits plus rule bits plus
  the held-out log loss. Held-out data: a second spreading process on the same contacts,
  from different first adopters [R, item (iii), p. 16: "held-out trajectories"].
- Also reported: the same without the structure bits, Eq. (29) on all data with and
  without them, and two other ways of holding out data (supplement.md).

## What we report: their four quantities [R, Sec. 5, p. 16]

(i) structural length L_L(S); (ii) rule length L_C(D | S); (iii) predictive log loss
on held-out trajectories or interventions; (iv) stability of the selected interaction
order under alternative reasonable codes and data resolutions.

## Experiment [R, Sec. 7.1, p. 21: "holding fixed, for each node, the number of active
neighbors while changing which group those neighbors belong to"]

For each mechanism, a non-adopter meets two adopters for the same time, either together
in one gathering or apart in two. This is the perturbation the paper describes. Results
enter as (iii), held-out log loss on interventions, and as the true answer to compare
with what each fitted model predicts.

## Hyperparameters (one value each in the pilot; then changed one at a time)

Pilot values first; the sweep values are in common.py (SWEEP). 20 runs per setting.

- Partners per day: 6; sweep 3, 10, 25. Literature: 3 to 10 distinct partners per day
  at workplaces, 20 to 30 at conferences (study/empirical_values.md). Each value is
  tuned again so that about half of people adopt.
- Sensor detection probability per sample d: 0.5; sweep 0.25, 0.75, 1.0.
- Sensor sampling interval: 20 s; sweep 60 s, 300 s [R, item (iv): data resolution].
- Noise on recorded adoption times, mean delay delta: 0; sweep 300 s, 1800 s
  [R, Sec. 8].
- Spreading processes per record: 1; sweep 5, 10. The same number is held out.
- Sensor grouping: connected parts at each sample; sweep one group per gathering, which
  uses the true gathering times and is a diagnostic only.
- Structure code: Prop. 7 and a graph code that names cliques, both computed in every
  run [R, item (iv); p. 18: "a graph code that names cliques rather than edges avoids
  the factor, but it is then naming groups"].
