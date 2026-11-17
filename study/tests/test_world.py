import numpy as np
import pytest

import world
from world import Gatherings, Params


def test_no_one_is_in_two_gatherings_at_once():
    p = Params(n_people=50, days=1, gathering_rate=200 / world.DAY)
    g = world.gatherings(p, np.random.default_rng(1))
    assert len(g.start) > 50
    for i in range(p.n_people):
        spans = sorted((s, e) for s, e, x in zip(g.start, g.end, g.members) if i in x)
        assert all(e1 <= s2 for (_, e1), (s2, _) in zip(spans, spans[1:]))
    assert all(2 <= len(x) <= 6 for x in g.members)


def test_rates_of_the_three_worlds():
    p = Params(lam=1.0, mu=10.0)
    assert [world.rate("pairwise", k, p) for k in range(4)] == [0, 1, 2, 3]
    assert [world.rate("group", k, p) for k in range(4)] == [0, 0, 10, 10]
    assert [world.rate("mixed", k, p) for k in range(4)] == [0, 0.5, 6, 6.5]


@pytest.mark.parametrize("w", world.WORLDS)
def test_spread_matches_the_exact_chance_of_adopting(w):
    """A person who has not adopted meets two adopters for 15 minutes, together or one
    at a time; the simulated share who adopt matches the exact chance."""
    p = Params(n_people=3, days=1, lam=1 / 1800, mu=1 / 900)
    length = 900.0
    rng = np.random.default_rng(2)
    trials = 4000
    together = Gatherings(np.array([0.0]), np.array([length]), [np.array([0, 1, 2])])
    apart = Gatherings(np.array([0.0, length]), np.array([length, 2 * length]),
                       [np.array([0, 2]), np.array([1, 2])])
    got = [np.mean([np.isfinite(world.spread(g, w, p, rng, [0, 1])[2])
                    for _ in range(trials)]) for g in (together, apart)]
    want = {"pairwise": (2 * p.lam * length, 2 * p.lam * length),
            "group": (p.mu * length, 0.0),
            "mixed": ((p.lam + p.mu / 2) * length, p.lam * length)}[w]
    for g, x in zip(got, want):
        assert abs(g - (1 - np.exp(-x))) < 4 * np.sqrt(0.25 / trials)
