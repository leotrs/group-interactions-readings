from itertools import combinations
from math import comb, log2

import numpy as np
import pytest

import model
import record
import structure
import world
from world import Gatherings, Params


def test_no_one_in_two_gatherings_at_once():
    p = Params(n=50, days=1, gathering_rate=200 / world.DAY)
    g = world.gatherings(p, np.random.default_rng(1))
    assert len(g.start) > 50
    for i in range(p.n):
        spans = sorted((s, e) for s, e, x in zip(g.start, g.end, g.members) if i in x)
        assert all(e1 <= s2 for (_, e1), (s2, _) in zip(spans, spans[1:]))
    assert all(2 <= len(x) <= 6 for x in g.members)


def _one_meeting(members, length):
    return Gatherings(np.array([0.0]), np.array([length]), [np.array(members)])


@pytest.mark.parametrize("mechanism", world.MECHANISMS)
def test_spread_matches_exact_probability(mechanism):
    """A non-adopter with two adopters for 15 minutes, together or apart."""
    p = Params(n=3, days=1, lam=1 / 1800, mu=1 / 900)
    length = 900.0
    rng = np.random.default_rng(2)
    trials = 4000
    together = _one_meeting([0, 1, 2], length)
    apart = Gatherings(np.array([0.0, length]), np.array([length, 2 * length]),
                       [np.array([0, 2]), np.array([1, 2])])
    got = [np.mean([np.isfinite(world.spread(g, mechanism, p, rng, [0, 1])[2])
                    for _ in range(trials)]) for g in (together, apart)]
    want = {"independent": (2 * p.lam * length, 2 * p.lam * length),
            "joint": (p.mu * length, 0.0),
            "both": ((p.lam + p.mu / 2) * length, p.lam * length)}[mechanism]
    for g, w in zip(got, want):
        assert abs(g - (1 - np.exp(-w))) < 4 * np.sqrt(0.25 / trials)


def test_sensors_with_certain_detection_give_the_log():
    g = Gatherings(np.array([0.0, 100.0]), np.array([90.0, 500.0]),
                   [np.array([0, 1, 2]), np.array([2, 3])])
    rec = record.sensor_record(g, 1.0, np.random.default_rng(0), t_max=1000.0)
    log = record.log_record(g)
    assert rec.edges() == log.edges()
    assert rec.hyperedges() == log.hyperedges()
    # Samples at 0, 20, ..., 80 for the first gathering, each standing for 20 s.
    first = rec.group_start < 90
    assert list(rec.group_start[first]) == [0.0, 20.0, 40.0, 60.0, 80.0]
    assert rec.group_end[first][-1] == 100.0


def test_sensors_miss_gatherings_between_samples():
    g = _one_meeting([0, 1], 10.0)
    g.start[:] = 1.0
    g.end[:] = 15.0  # no multiple of 20 s inside
    rec = record.sensor_record(g, 1.0, np.random.default_rng(0), t_max=100.0)
    assert rec.edges() == set() and rec.hyperedges() == set()


def test_components():
    parts = record.components([(0, 1), (1, 2), (5, 6)])
    assert sorted(parts) == [(0, 1, 2), (5, 6)]


def test_structure_codes_follow_proposition_7():
    n, k, m = 1000, 4, 5
    groups = [tuple(range(k * j, k * j + k)) for j in range(m)]
    pairs = {pr for e in groups for pr in combinations(e, 2)}
    h = structure.hypergraph_bits(n, groups)
    gbits = structure.graph_bits(n, len(pairs))
    # Proposition 7 without the count terms, which we add.
    core_h = structure.log2_comb(comb(n, k), m)
    core_g = structure.log2_comb(comb(n, 2), m * comb(k, 2))
    extra_h = log2(n) + sum(log2(comb(n, j) + 1) for j in range(2, k + 1))
    assert h == pytest.approx(core_h + extra_h)
    assert gbits == pytest.approx(core_g + log2(comb(n, 2) + 1))
    assert core_g / core_h == pytest.approx(k - 1, rel=0.1)


def _simulate_model(name, contacts, lam, b, nu, seeds, t_max, rng):
    """Adoption times drawn from one of the models itself, to test the likelihood."""
    t = np.full(contacts.n, np.inf)
    t[seeds] = 0.0
    bounds = np.unique(np.concatenate([[0.0, t_max], contacts.boundaries()]))
    for c, c_next in zip(bounds[:-1], bounds[1:]):
        now = c
        while True:
            adopted = np.isfinite(t)
            a, hist = contacts.state(c, adopted)
            rates = lam * model._drive(name, a, hist, nu) + b
            rates[adopted] = 0
            now += rng.exponential(1 / rates.sum())
            if now >= c_next:
                break
            t[rng.choice(contacts.n, p=rates / rates.sum())] = now
    return t


def _busy_world(seed):
    p = Params(n=150, days=1, gathering_rate=300 / world.DAY)
    return p, world.gatherings(p, np.random.default_rng(seed))


@pytest.mark.parametrize("name", model.MODELS)
@pytest.mark.parametrize("recording", ["log", "sensors"])
def test_fit_recovers_parameters_of_its_own_model(name, recording):
    p, g = _busy_world(3)
    rng = np.random.default_rng(4)
    rec = (record.log_record(g) if recording == "log"
           else record.sensor_record(g, 0.5, rng, p.t_max))
    contacts = model.Contacts(p.n, rec)
    lam, b, nu = 1e-3, 1e-6, (1.0 if name == "graph_linear" else 2.0)
    t = _simulate_model(name, contacts, lam, b, nu, list(range(10)), p.t_max, rng)
    f = model.Features(contacts, t, 0.0, p.t_max)
    assert f.n_events > 60
    got = model.fit(name, f)
    assert got[0] == pytest.approx(lam, rel=0.5)
    if name != "graph_linear":
        assert got[2] == pytest.approx(nu, abs=0.5)


def test_graph_nonlinear_and_hypergraph_coincide_on_the_log():
    p, g = _busy_world(5)
    contacts = model.Contacts(p.n, record.log_record(g))
    rng = np.random.default_rng(6)
    t = _simulate_model("hypergraph", contacts, 1e-3, 1e-6, 2.0, list(range(10)),
                        p.t_max, rng)
    f = model.Features(contacts, t, 0.0, p.t_max)
    for params in [(1e-3, 1e-6, 2.0), (3e-4, 1e-5, 0.7)]:
        assert model.loglik("graph_nonlinear", params, f) == pytest.approx(
            model.loglik("hypergraph", params, f))


def test_loglik_by_hand():
    # Two people together from 0 to 20; person 0 adopted at 0, person 1 adopts at 10.
    g = _one_meeting([0, 1], 20.0)
    contacts = model.Contacts(2, record.log_record(g))
    f = model.Features(contacts, np.array([0.0, 10.0]), 0.0, 30.0)
    lam, b = 0.3, 0.1
    want = np.log(lam + b) - (lam + b) * 10
    assert model.loglik("graph_linear", (lam, b, 1.0), f) == pytest.approx(want)
    assert model.loglik("hypergraph", (lam, b, 3.0), f) == pytest.approx(want)


def test_contacts_only_count_while_present():
    # Person 1 meets adopter 0 from 0 to 10, then is alone until 30.
    g = _one_meeting([0, 1], 10.0)
    contacts = model.Contacts(2, record.log_record(g))
    f = model.Features(contacts, np.array([0.0, np.inf]), 0.0, 30.0)
    lam, b = 0.3, 0.1
    want = -(lam + b) * 10 - b * 20
    assert model.loglik("graph_linear", (lam, b, 1.0), f) == pytest.approx(want)


@pytest.mark.parametrize("name", model.MODELS)
def test_loglik_splits_over_people(name):
    p, g = _busy_world(7)
    rng = np.random.default_rng(8)
    contacts = model.Contacts(p.n, record.sensor_record(g, 0.5, rng, p.t_max))
    params = (1e-3, 1e-6, 2.0)
    t = _simulate_model(name, contacts, *params, list(range(10)), p.t_max, rng)
    f = model.Features(contacts, t, 0.0, p.t_max)
    keep = rng.random(p.n) < 0.5
    whole = model.loglik(name, params, f)
    everyone = f.people(np.ones(p.n, bool))
    assert model.loglik(name, params, everyone) == pytest.approx(whole)
    halves = model.loglik(name, params, f.people(keep)) + model.loglik(
        name, params, f.people(~keep))
    assert halves == pytest.approx(whole)
    assert f.people(keep).n_events + f.people(~keep).n_events == f.n_events


def test_clique_cover_covers_every_edge_and_finds_disjoint_cliques():
    groups = {(0, 1, 2, 3), (4, 5, 6), (7, 8)}
    edges = {pr for e in groups for pr in combinations(e, 2)}
    assert structure.clique_cover(edges) == groups
    rng = np.random.default_rng(9)
    edges = {tuple(sorted(rng.choice(30, 2, replace=False))) for _ in range(120)}
    cover = structure.clique_cover(edges)
    assert {pr for c in cover for pr in combinations(c, 2)} >= edges
    assert all(pr in edges for c in cover for pr in combinations(c, 2))


def test_sensor_grouping_by_gathering():
    g = Gatherings(np.array([0.0, 100.0]), np.array([90.0, 500.0]),
                   [np.array([0, 1, 2]), np.array([2, 3])])
    rec = record.sensor_record(g, 1.0, np.random.default_rng(0), 1000.0,
                               grouping="gathering")
    assert rec.hyperedges() == {(0, 1, 2), (2, 3)}
    assert list(rec.group_start) == [0.0, 100.0]
    assert list(rec.group_end) == [100.0, 500.0]


def test_combined_processes_add_up():
    p, g = _busy_world(10)
    contacts = model.Contacts(p.n, record.log_record(g))
    rng = np.random.default_rng(11)
    params = (1e-3, 1e-6, 2.0)
    parts = [model.Features(contacts, _simulate_model(
        "hypergraph", contacts, *params, list(rng.choice(p.n, 10, replace=False)),
        p.t_max, rng), 0.0, p.t_max) for _ in range(3)]
    both = model.combine(parts)
    assert model.loglik("hypergraph", params, both) == pytest.approx(
        sum(model.loglik("hypergraph", params, f) for f in parts))
    assert both.n_events == sum(f.n_events for f in parts)


def test_group_step_effect_and_rate():
    from math import exp
    from model import _rate, together_apart_chances
    lam, b, mu = 1e-4, 1e-6, 1e-3
    ch = together_apart_chances("group_step", (lam, b, mu), 900.0)
    assert abs(ch["together"] - (1 - exp(-(2 * lam + mu) * 900))) < 1e-12
    assert abs(ch["apart"] - (1 - exp(-2 * lam * 900))) < 1e-12
    # hist[i, v-1] counts groups holding v adopters: only groups with 2 or more count.
    a = np.array([1.0, 2.0, 3.0])
    hist = np.array([[1.0, 0, 0], [0, 1.0, 0], [1.0, 0, 1.0]])
    assert np.allclose(_rate("group_step", (lam, b, mu), a, hist),
                       lam * a + mu * np.array([0, 1, 1]) + b)
