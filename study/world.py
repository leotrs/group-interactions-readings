"""The simulated world: random gatherings and three adoption mechanisms (spec.md).

Times are in seconds of event time: 3 days of 8 hours, run back to back. Gatherings do
not depend on adoption, so they are generated first and adoption runs on top of them.
"""

from dataclasses import dataclass, replace

import numpy as np

HOUR = 3600.0
DAY = 8 * HOUR
MECHANISMS = ("independent", "joint", "both")


@dataclass(frozen=True)
class Params:
    n: int = 200
    days: int = 3
    min_size: int = 2
    max_size: int = 6
    mean_duration: float = 900.0
    gathering_rate: float = 100 / DAY  # gatherings started per second; calibrated
    n_seeds: int = 10
    lam: float = 1 / HOUR  # independent mechanism, per adopter present
    mu: float = 1 / 900.0  # joint mechanism, while two or more adopters are present

    @property
    def t_max(self):
        return self.days * DAY


@dataclass
class Gatherings:
    start: np.ndarray
    end: np.ndarray
    members: list


def gatherings(p: Params, rng) -> Gatherings:
    """Gatherings start at random times. Each draws its size uniformly from min_size to
    max_size and its members from the people not already in a gathering."""
    times = np.sort(rng.uniform(0, p.t_max, rng.poisson(p.gathering_rate * p.t_max)))
    busy_until = np.zeros(p.n)
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


def partners_per_day(g: Gatherings, p: Params) -> float:
    """Mean number of distinct people each person is with, per day."""
    total = 0
    for day in range(p.days):
        seen = [set() for _ in range(p.n)]
        for s, x in zip(g.start, g.members):
            if day * DAY <= s < (day + 1) * DAY:
                for i in x:
                    seen[i].update(x)
        total += sum(len(s) - (i in s) for i, s in enumerate(seen))
    return total / (p.n * p.days)


def calibrate_gathering_rate(p: Params, target=6.0, runs=5, seed=0) -> float:
    """Gathering rate at which people meet `target` distinct people a day on average."""
    lo, hi = 1 / DAY, 2000 / DAY
    for _ in range(25):
        mid = (lo + hi) / 2
        q = replace(p, gathering_rate=mid)
        rng = np.random.default_rng(seed)
        got = np.mean([partners_per_day(gatherings(q, rng), q) for _ in range(runs)])
        lo, hi = (mid, hi) if got < target else (lo, mid)
    return (lo + hi) / 2


def rate(mechanism, k, p: Params) -> float:
    """Adoption rate of a non-adopter in a gathering with k adopters."""
    if mechanism == "independent":
        return p.lam * k
    if mechanism == "joint":
        return p.mu if k >= 2 else 0.0
    if mechanism == "both":
        return p.lam / 2 * k + (p.mu / 2 if k >= 2 else 0.0)
    raise ValueError(mechanism)


def spread(g: Gatherings, mechanism, p: Params, rng, seeds) -> np.ndarray:
    """Adoption times (inf if never). Rates change only when a gathering starts or ends
    or someone adopts, so between those moments the next adoption is exponential."""
    t_adopt = np.full(p.n, np.inf)
    t_adopt[list(seeds)] = 0.0
    adopted = np.isfinite(t_adopt)
    boundaries = sorted([(e, 0, m) for m, e in enumerate(g.end)]
                        + [(s, 1, m) for m, s in enumerate(g.start)])  # ends first
    active = set()
    t, b = 0.0, 0
    while True:
        people, rates = [], []
        for m in active:
            x = g.members[m]
            k = int(adopted[x].sum())
            r = rate(mechanism, k, p)
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
            t, kind, m = boundaries[b]
            b += 1
            (active.add if kind == 1 else active.discard)(m)
    return t_adopt


def adoption_fraction(p: Params, mechanism, runs, seed) -> float:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(runs):
        g = gatherings(p, rng)
        seeds = rng.choice(p.n, p.n_seeds, replace=False)
        out.append(np.isfinite(spread(g, mechanism, p, rng, seeds)).mean())
    return float(np.mean(out))
