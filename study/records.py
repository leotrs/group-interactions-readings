"""The two ways of recording the gatherings: a meeting log and proximity sensors.

A record is a list of pair contacts and a list of group contacts, each present on the
time interval [start, end). Both records also keep the adoption times (see
`recorded_times`).
"""

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from world import Gatherings


@dataclass
class Record:
    pair_start: np.ndarray
    pair_end: np.ndarray
    pair_i: np.ndarray
    pair_j: np.ndarray
    group_start: np.ndarray
    group_end: np.ndarray
    group_members: list

    def edges(self) -> set:
        """Pairs that were ever in contact, for the structure codes."""
        return {(int(i), int(j)) for i, j in zip(self.pair_i, self.pair_j)}

    def hyperedges(self) -> set:
        """Distinct groups that were ever recorded, for the structure codes."""
        return {tuple(int(i) for i in x) for x in self.group_members}


def _record(pairs, groups) -> Record:
    p = np.array(pairs, dtype=float).reshape(-1, 4)
    return Record(p[:, 0], p[:, 1], p[:, 2].astype(int), p[:, 3].astype(int),
                  np.array([s for s, _, _ in groups], dtype=float),
                  np.array([e for _, e, _ in groups], dtype=float),
                  [np.array(x, dtype=int) for _, _, x in groups])


def meeting_log(g: Gatherings) -> Record:
    """Every gathering, with its members, start and end; every pair in it for the
    same time."""
    groups = [(s, e, sorted(int(i) for i in x))
              for s, e, x in zip(g.start, g.end, g.members)]
    pairs = [(s, e, i, j) for s, e, x in groups for i, j in combinations(x, 2)]
    return _record(pairs, groups)


def components(pairs) -> list:
    """Connected components of a set of pairs, as sorted tuples."""
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


def sensors(g: Gatherings, detection_probability, rng, t_max, sampling_interval,
            groups="components") -> Record:
    """Sensors sample at every multiple of `sampling_interval`. At each sample, each
    pair in the same gathering is detected with `detection_probability`, and a detected
    pair counts as in contact until the next sample.

    groups="components": the recorded groups at a sample are the connected components
    of the pairs detected at that sample. A person is in one gathering at a time, so a
    component never mixes two gatherings.
    groups="gatherings": one group per gathering, made of everyone detected in it, from
    its first sample to the end of its last. This uses the true gathering times, which
    real sensors do not have, so it serves only as a check in the sweep."""
    pairs, recorded = [], []
    for start, end, x in zip(g.start, g.end, g.members):
        all_pairs = list(combinations(sorted(int(i) for i in x), 2))
        samples = np.arange(np.ceil(start / sampling_interval) * sampling_interval, end,
                            sampling_interval)
        present = set()
        for s in samples:
            seen = [pr for pr in all_pairs if rng.random() < detection_probability]
            stop = min(s + sampling_interval, t_max)
            pairs += [(s, stop, i, j) for i, j in seen]
            present.update(i for pr in seen for i in pr)
            if groups == "components":
                recorded += [(s, stop, part) for part in components(seen)]
        if groups == "gatherings" and present:
            recorded.append((samples[0], min(samples[-1] + sampling_interval, t_max),
                             sorted(present)))
    return _record(pairs, recorded)


def recorded_times(t_adopt, first_adopters, delay, rng, t_max) -> np.ndarray:
    """Adoption times as recorded. With delay > 0, each adoption after the first
    adopters is recorded late by an exponential time with mean `delay`; an adoption
    whose recorded time falls after the end of the event is not recorded."""
    t = t_adopt.copy()
    if delay > 0:
        late = np.isfinite(t)
        late[list(first_adopters)] = False
        t[late] += rng.exponential(delay, late.sum())
        t[t >= t_max] = np.inf
    return t
