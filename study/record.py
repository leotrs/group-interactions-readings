"""Data recording: a meeting log or proximity sensors, plus adoption times (spec.md).

Both recordings keep times. A record is a list of pair contacts and a list of group
contacts, each present on [start, end).
"""

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from world import Gatherings

SENSOR_INTERVAL = 20.0


@dataclass
class Timed:
    pair_start: np.ndarray
    pair_end: np.ndarray
    pair_i: np.ndarray
    pair_j: np.ndarray
    group_start: np.ndarray
    group_end: np.ndarray
    group_members: list

    def edges(self) -> set:
        """Pairs ever in contact, for the structure code."""
        return {(int(i), int(j)) for i, j in zip(self.pair_i, self.pair_j)}

    def hyperedges(self) -> set:
        """Distinct groups ever recorded, for the structure code."""
        return {tuple(int(i) for i in x) for x in self.group_members}


def _timed(pairs, groups) -> Timed:
    p = np.array(pairs, dtype=float).reshape(-1, 4)
    return Timed(p[:, 0], p[:, 1], p[:, 2].astype(int), p[:, 3].astype(int),
                 np.array([s for s, _, _ in groups], dtype=float),
                 np.array([e for _, e, _ in groups], dtype=float),
                 [np.array(x, dtype=int) for _, _, x in groups])


def log_record(g: Gatherings) -> Timed:
    """Every gathering with its start and end; every pair in it for the same time."""
    groups = [(s, e, sorted(int(i) for i in x))
              for s, e, x in zip(g.start, g.end, g.members)]
    pairs = [(s, e, i, j) for s, e, x in groups for i, j in combinations(x, 2)]
    return _timed(pairs, groups)


def components(pairs) -> list:
    """Connected parts of a set of pairs, as sorted tuples."""
    parent = {}

    def root(i):
        while parent.setdefault(i, i) != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in pairs:
        parent[root(i)] = root(j)
    parts = {}
    for i in parent:
        parts.setdefault(root(i), []).append(i)
    return [tuple(sorted(x)) for x in parts.values()]


def sensor_record(g: Gatherings, d, rng, t_max, interval=SENSOR_INTERVAL,
                  grouping="parts") -> Timed:
    """Sensors sample at multiples of `interval`. At each sample, each pair in the same
    gathering is detected with probability d, and a detection stands for the next
    `interval` seconds.

    grouping="parts": the groups at a sample are the connected parts of the detected
    pairs; a person is in one gathering at a time, so a part never mixes gatherings.
    grouping="gathering": one group per gathering, made of everyone detected in it, from
    its first sample to the end of its last. This uses the true gathering times, which
    real sensors do not have; it is a diagnostic only."""
    pairs, groups = [], []
    for start, end, x in zip(g.start, g.end, g.members):
        all_pairs = list(combinations(sorted(int(i) for i in x), 2))
        samples = np.arange(np.ceil(start / interval) * interval, end, interval)
        present = set()
        for s in samples:
            seen = [pr for pr in all_pairs if rng.random() < d]
            stop = min(s + interval, t_max)
            pairs += [(s, stop, i, j) for i, j in seen]
            present.update(i for pr in seen for i in pr)
            if grouping == "parts":
                groups += [(s, stop, part) for part in components(seen)]
        if grouping == "gathering" and present:
            groups.append((samples[0], min(samples[-1] + interval, t_max),
                           sorted(present)))
    return _timed(pairs, groups)


def recorded_times(t_adopt, seeds, delta, rng, t_max) -> np.ndarray:
    """Adoption times as recorded: non-seeds get a random delay with mean delta. A delay
    that pushes the record past the end of the event means the adoption is not seen."""
    t = t_adopt.copy()
    if delta > 0:
        late = np.isfinite(t)
        late[list(seeds)] = False
        t[late] += rng.exponential(delta, late.sum())
        t[t >= t_max] = np.inf
    return t
