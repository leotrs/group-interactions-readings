from math import exp

import numpy as np
import pytest

import models
import records
import world
from world import Gatherings, Params


def _simulate_model(model, contacts, params, first, t_max, rng):
    """Adoption times drawn from one of the models itself, to test the likelihood."""
    t = np.full(contacts.n_people, np.inf)
    t[first] = 0.0
    bounds = np.unique(np.concatenate([[0.0, t_max], contacts.boundaries()]))
    for c, c_next in zip(bounds[:-1], bounds[1:]):
        now = c
        while True:
            adopted = np.isfinite(t)
            a, hist = contacts.state(c, adopted)
            r = models.rates(model, params, a, hist)
            r[adopted] = 0
            if r.sum() == 0:  # everyone has adopted
                break
            now += rng.exponential(1 / r.sum())
            if now >= c_next:
                break
            t[rng.choice(contacts.n_people, p=r / r.sum())] = now
    return t


def _busy_event(seed):
    p = Params(n_people=150, days=1, gathering_rate=300 / world.DAY)
    return p, world.gatherings(p, np.random.default_rng(seed))


def _one_meeting(members, length):
    return Gatherings(np.array([0.0]), np.array([length]), [np.array(members)])


@pytest.mark.parametrize("model", models.MODELS + models.CHECK_MODELS)
@pytest.mark.parametrize("record", ["log", "sensors"])
def test_fit_recovers_the_parameters_of_its_own_model(model, record):
    p, g = _busy_event(3)
    rng = np.random.default_rng(4)
    rec = (records.meeting_log(g) if record == "log"
           else records.sensors(g, 0.5, rng, p.t_max, 20.0))
    contacts = models.Contacts(p.n_people, rec)
    third = {"graph_linear": 1.0, "group_rate": 3e-3}.get(model, 2.0)
    params = (1e-3, 1e-6, third)
    t = _simulate_model(model, contacts, params, list(range(10)), p.t_max, rng)
    f = models.Features(contacts, t, 0.0, p.t_max)
    assert f.n_events > 60
    got = models.fit(model, f)
    assert got[0] == pytest.approx(params[0], rel=0.5)
    if model == "group_rate":
        assert got[2] == pytest.approx(params[2], rel=0.5)
    elif model != "graph_linear":
        assert got[2] == pytest.approx(params[2], abs=0.5)


def test_nonlinear_graph_and_hypergraph_coincide_on_the_log():
    p, g = _busy_event(5)
    contacts = models.Contacts(p.n_people, records.meeting_log(g))
    t = _simulate_model("hypergraph", contacts, (1e-3, 1e-6, 2.0), list(range(10)),
                        p.t_max, np.random.default_rng(6))
    f = models.Features(contacts, t, 0.0, p.t_max)
    for params in [(1e-3, 1e-6, 2.0), (3e-4, 1e-5, 0.7)]:
        assert models.loglik("graph_nonlinear", params, f) == pytest.approx(
            models.loglik("hypergraph", params, f))


def test_loglik_by_hand():
    # Two people together from 0 to 20; person 0 adopted at 0, person 1 adopts at 10.
    contacts = models.Contacts(2, records.meeting_log(_one_meeting([0, 1], 20.0)))
    f = models.Features(contacts, np.array([0.0, 10.0]), 0.0, 30.0)
    lam, b = 0.3, 0.1
    want = np.log(lam + b) - (lam + b) * 10
    assert models.loglik("graph_linear", (lam, b, 1.0), f) == pytest.approx(want)
    assert models.loglik("hypergraph", (lam, b, 3.0), f) == pytest.approx(want)


def test_contacts_count_only_while_present():
    # Person 1 meets adopter 0 from 0 to 10, then is alone until 30.
    contacts = models.Contacts(2, records.meeting_log(_one_meeting([0, 1], 10.0)))
    f = models.Features(contacts, np.array([0.0, np.inf]), 0.0, 30.0)
    lam, b = 0.3, 0.1
    want = -(lam + b) * 10 - b * 20
    assert models.loglik("graph_linear", (lam, b, 1.0), f) == pytest.approx(want)


@pytest.mark.parametrize("model", models.MODELS)
def test_loglik_splits_over_people(model):
    p, g = _busy_event(7)
    rng = np.random.default_rng(8)
    contacts = models.Contacts(p.n_people, records.sensors(g, 0.5, rng, p.t_max, 20.0))
    params = (1e-3, 1e-6, 2.0)
    t = _simulate_model(model, contacts, params, list(range(10)), p.t_max, rng)
    f = models.Features(contacts, t, 0.0, p.t_max)
    keep = rng.random(p.n_people) < 0.5
    whole = models.loglik(model, params, f)
    assert models.loglik(model, params, f.people(np.ones(p.n_people, bool))) == (
        pytest.approx(whole))
    halves = (models.loglik(model, params, f.people(keep))
              + models.loglik(model, params, f.people(~keep)))
    assert halves == pytest.approx(whole)
    assert f.people(keep).n_events + f.people(~keep).n_events == f.n_events


def test_combined_processes_add_up():
    p, g = _busy_event(10)
    contacts = models.Contacts(p.n_people, records.meeting_log(g))
    rng = np.random.default_rng(11)
    params = (1e-3, 1e-6, 2.0)
    parts = [models.Features(contacts, _simulate_model(
        "hypergraph", contacts, params, list(rng.choice(p.n_people, 10, replace=False)),
        p.t_max, rng), 0.0, p.t_max) for _ in range(3)]
    both = models.combine(parts)
    assert models.loglik("hypergraph", params, both) == pytest.approx(
        sum(models.loglik("hypergraph", params, f) for f in parts))
    assert both.n_events == sum(f.n_events for f in parts)


def test_group_rate_counts_groups_with_two_or_more_adopters():
    lam, b, mu = 1e-4, 1e-6, 1e-3
    # hist[i, v-1] counts a person's groups that hold v adopters.
    a = np.array([1.0, 2.0, 3.0])
    hist = np.array([[1.0, 0, 0], [0, 1.0, 0], [1.0, 0, 1.0]])
    assert np.allclose(models.rates("group_rate", (lam, b, mu), a, hist),
                       lam * a + mu * np.array([0, 1, 1]) + b)


def test_predicted_chances():
    lam, b, mu, nu = 1e-4, 1e-6, 1e-3, 2.0
    ch = models.together_apart_chances("group_rate", (lam, b, mu), 900.0)
    assert ch["together"] == pytest.approx(1 - exp(-(2 * lam + mu) * 900))
    assert ch["apart"] == pytest.approx(1 - exp(-2 * lam * 900))
    ch = models.together_apart_chances("hypergraph", (lam, b, nu), 900.0)
    assert ch["together"] == pytest.approx(1 - exp(-lam * 2 ** nu * 900))
