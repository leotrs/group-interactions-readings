"""The simulated event: people meet in gatherings, and a behavior spreads among them.

Times are in seconds of event time: 3 days of 8 hours, one after the other. Gatherings
do not depend on adoption, so they are drawn first and spreading runs on top of them.
The three worlds differ only in the adoption rate (`rate`).
"""

from dataclasses import dataclass, replace

import numpy as np

HOUR = 3600.0
DAY = 8 * HOUR
WORLDS = ("pairwise", "group", "mixed")


@dataclass(frozen=True)
class Params:
    """The event and the spreading. tune.py sets gathering_rate, n_first_adopters and
    lam; the defaults here are only starting values for tuning and for tests."""
    n_people: int = 200
    days: int = 3
    min_size: int = 2
    max_size: int = 6
    mean_duration: float = 900.0
    gathering_rate: float = 100 / DAY  # gatherings started per second
    n_first_adopters: int = 10
    lam: float = 1 / HOUR  # pairwise world: rate per adopter in the gathering
    mu: float = 1 / 900.0  # group world: rate while two or more adopters are present

    @property
    def t_max(self):
        return self.days * DAY


@dataclass
class Gatherings:
    start: np.ndarray
    end: np.ndarray
    members: list  # one sorted array of people per gathering


def gatherings(p: Params, rng) -> Gatherings:
    """Gatherings start at the times of a Poisson process. Each draws its size uniformly
    from min_size to max_size and its members from the people who are not already in a
    gathering, so each person is in at most one gathering at a time."""
    times = np.sort(rng.uniform(0, p.t_max, rng.poisson(p.gathering_rate * p.t_max)))
    busy_until = np.zeros(p.n_people)
    starts, ends, members = [], [], []
    for t in times:
        free = np.flatnonzero(busy_until <= t)
        if len(free) < 2:
            continue
        size = min(int(rng.integers(p.min_size, p.max_size + 1)), len(free))
        group = np.sort(rng.choice(free, size, replace=False))
        end = min(t + rng.exponential(p.mean_duration), p.t_max)
        busy_until[group] = end
        starts.append(t)
        ends.append(end)
        members.append(group)
    return Gatherings(np.array(starts), np.array(ends), members)


def people_met_per_day(g: Gatherings, p: Params) -> float:
    """Mean number of distinct other people that a person shares a gathering with in a
    day, counting the gatherings that start in that day."""
    total = 0
    for day in range(p.days):
        seen = [set() for _ in range(p.n_people)]
        for s, x in zip(g.start, g.members):
            if day * DAY <= s < (day + 1) * DAY:
                for i in x:
                    seen[i].update(x)
        total += sum(len(s) - (i in s) for i, s in enumerate(seen))
    return total / (p.n_people * p.days)


def calibrate_gathering_rate(p: Params, target=6.0, runs=5, seed=0) -> float:
    """The gathering rate at which people meet `target` distinct people a day, found by
    bisection over the average of `runs` draws of the gatherings."""
    lo, hi = 1 / DAY, 2000 / DAY
    for _ in range(25):
        mid = (lo + hi) / 2
        q = replace(p, gathering_rate=mid)
        rng = np.random.default_rng(seed)
        got = np.mean([people_met_per_day(gatherings(q, rng), q) for _ in range(runs)])
        lo, hi = (mid, hi) if got < target else (lo, mid)
    return (lo + hi) / 2


def rate(world, k, p: Params) -> float:
    """Adoption rate of a person who has not adopted, in a gathering with k adopters."""
    if world == "pairwise":
        return p.lam * k
    if world == "group":
        return p.mu if k >= 2 else 0.0
    if world == "mixed":
        return p.lam / 2 * k + (p.mu / 2 if k >= 2 else 0.0)
    raise ValueError(world)


def spread(g: Gatherings, world, p: Params, rng, first_adopters) -> np.ndarray:
    """Adoption times, inf for people who never adopt. Rates change only when a
    gathering starts or ends or someone adopts, so between those moments the time to
    the next adoption is exponential and the simulation is exact."""
    t_adopt = np.full(p.n_people, np.inf)
    t_adopt[list(first_adopters)] = 0.0
    adopted = np.isfinite(t_adopt)
    # At equal times, gatherings end before others start.
    boundaries = sorted([(e, 0, m) for m, e in enumerate(g.end)]
                        + [(s, 1, m) for m, s in enumerate(g.start)])
    active = set()
    t, b = 0.0, 0
    while True:
        people, rates = [], []
        for m in active:
            x = g.members[m]
            r = rate(world, int(adopted[x].sum()), p)
            if r > 0:
                for i in x[~adopted[x]]:
                    people.append(i)
                    rates.append(r)
        total = sum(rates)
        t_next = t + rng.exponential(1 / total) if total > 0 else np.inf
        t_bound = boundaries[b][0] if b < len(boundaries) else np.inf
        if min(t_next, t_bound) >= p.t_max:
            break
        if t_next < t_bound:
            t = t_next
            i = people[rng.choice(len(people), p=np.array(rates) / total)]
            adopted[i] = True
            t_adopt[i] = t
        else:
            t, starts, m = boundaries[b]
            b += 1
            (active.add if starts else active.discard)(m)
    return t_adopt


def adoption_fraction(p: Params, world, runs, seed) -> float:
    """Share of people who adopt by the end, first adopters included, averaged over
    `runs` independent events."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(runs):
        g = gatherings(p, rng)
        first = rng.choice(p.n_people, p.n_first_adopters, replace=False)
        out.append(np.isfinite(spread(g, world, p, rng, first)).mean())
    return float(np.mean(out))
