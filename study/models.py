"""The models of adoption, their likelihood, fitting, and predicted causal effect.

Each model gives a person i who has not adopted a rate of adoption that depends on the
contacts in the record at that moment:

  graph_linear:    lam * a_i + b
  graph_nonlinear: lam * a_i^nu + b
  hypergraph:      lam * (sum over i's current recorded groups e of a_e^nu) + b

where a_i is the number of adopters in contact with i now (meeting log: in the same
gathering; sensors: in a pair detected at the latest sample), a_e the number of
adopters in group e, and b a constant background rate. These three are the models
compared in the paper. On the meeting log a person's contacts at any moment are exactly
the members of that person's one gathering, so graph_nonlinear and hypergraph give the
same rates there.

One more model is fitted only for the causal effect and takes no part in the
comparisons:

  group_rate:      lam * a_i + mu * (number of i's current groups e with a_e >= 2) + b

It can represent a rate that switches on at two adopters, which the other three cannot.

Rates are constant between changes of the record and adoptions, so the likelihood of
the adoption times has the usual form for event times: the sum of the log rates at the
adoptions minus the integral of all rates over time. First adopters are taken as given.
Times are in seconds, so likelihoods are densities in seconds: the unit shifts all
models by the same amount and changes no comparison.

Parameters are stored as (lam, b, nu), with nu = 1 for graph_linear, and as
(lam, b, mu) for group_rate.
"""

from math import exp, log, log2

import numpy as np
from scipy.optimize import minimize

from records import Record

MODELS = ("graph_linear", "graph_nonlinear", "hypergraph")
CHECK_MODELS = ("group_rate",)
N_PARAMS = {"graph_linear": 2, "graph_nonlinear": 3, "hypergraph": 3, "group_rate": 3}
NU_BOUNDS = (0.05, 6.0)
LOG_BOUNDS = (-40, 5)  # bounds on log lam, log b and log mu


class Contacts:
    """A record, set up to give each person's contact counts at any moment."""

    def __init__(self, n_people, rec: Record):
        self.n_people, self.rec = n_people, rec
        sizes = [len(x) for x in rec.group_members]
        self.inc_g = np.repeat(np.arange(len(sizes)), sizes)
        self.inc_i = (np.concatenate(rec.group_members) if sizes
                      else np.zeros(0, dtype=int))
        self.max_a = max(sizes, default=2)  # a group whose members have all adopted

    def boundaries(self):
        r = self.rec
        return np.concatenate([r.pair_start, r.pair_end, r.group_start, r.group_end])

    def state(self, t, adopted):
        """a[i]: adopters in contact with person i at time t. hist[i, v-1]: how many of
        i's groups present at t hold exactly v adopters."""
        r, x = self.rec, adopted.astype(float)
        on = (r.pair_start <= t) & (t < r.pair_end)
        pi, pj = r.pair_i[on], r.pair_j[on]
        a = (np.bincount(pi, weights=x[pj], minlength=self.n_people)
             + np.bincount(pj, weights=x[pi], minlength=self.n_people))
        hist = np.zeros((self.n_people, self.max_a))
        g_on = (r.group_start <= t) & (t < r.group_end)
        k = np.bincount(self.inc_g, weights=x[self.inc_i] * g_on[self.inc_g],
                        minlength=len(g_on)).astype(int)
        use = g_on[self.inc_g] & (k[self.inc_g] > 0)
        np.add.at(hist, (self.inc_i[use], k[self.inc_g[use]] - 1), 1.0)
        return a, hist


class Features:
    """What the models need from the data in a time window (t0, t1]. For every stretch
    of time in which contacts and adopters stay the same: each person's counts (a and
    hist, as in Contacts.state) and the length of the stretch, dt. For each adoption:
    the counts just before it. Stretches in which a person has no adopter in contact
    are summed per person, since only the background rate acts in them."""

    def __init__(self, contacts: Contacts, t_rec, t0, t1):
        n = contacts.n_people
        times = np.sort(t_rec[(t_rec > t0) & (t_rec <= t1)])
        b = contacts.boundaries()
        cuts = np.unique(np.concatenate([[t0, t1], times, b[(b > t0) & (b < t1)]]))
        adopted = t_rec <= t0
        idle = np.zeros(n)
        a_rows, hist_rows, weights, ids = [], [], [], []
        ev_a, ev_hist, ev_ids = [], [], []
        for c, c_next in zip(cuts[:-1], cuts[1:]):
            a, hist = contacts.state(c, adopted)
            sus = ~adopted
            busy = sus & ((a > 0) | (hist.sum(axis=1) > 0))
            idle[sus & ~busy] += c_next - c
            a_rows.append(a[busy])
            hist_rows.append(hist[busy])
            weights.append(np.full(busy.sum(), c_next - c))
            ids.append(np.flatnonzero(busy))
            who = np.flatnonzero(t_rec == c_next) if c_next in times else []
            for i in who:
                ev_a.append(a[i])
                ev_hist.append(hist[i])
                ev_ids.append(i)
            if len(who):
                adopted = adopted.copy()
                adopted[who] = True
        quiet = np.flatnonzero(idle > 0)
        self.a = np.concatenate(a_rows + [np.zeros(len(quiet))])
        self.hist = np.vstack(hist_rows + [np.zeros((len(quiet), contacts.max_a))])
        self.dt = np.concatenate(weights + [idle[quiet]])
        self.ids = np.concatenate(ids + [quiet]).astype(int)
        self.ev_a = np.array(ev_a, dtype=float)
        self.ev_hist = np.array(ev_hist, dtype=float).reshape(-1, contacts.max_a)
        self.ev_ids = np.array(ev_ids, dtype=int)
        self.n_events = len(ev_a)

    def people(self, keep):
        """The same window restricted to the people with keep[i] True. The likelihood
        is a product over people, so disjoint subsets give log-likelihoods that add
        up."""
        sub = object.__new__(Features)
        rows, evs = keep[self.ids], keep[self.ev_ids]
        sub.a, sub.hist, sub.dt = self.a[rows], self.hist[rows], self.dt[rows]
        sub.ev_a, sub.ev_hist = self.ev_a[evs], self.ev_hist[evs]
        sub.ids, sub.ev_ids = self.ids[rows], self.ev_ids[evs]
        sub.n_events = int(evs.sum())
        return sub


def combine(parts):
    """Several spreading processes over the same contacts, as one data set. Their
    likelihoods multiply, so the rows are simply put together."""
    out = object.__new__(Features)
    for key in ("a", "hist", "dt", "ids", "ev_a", "ev_hist", "ev_ids"):
        setattr(out, key, np.concatenate([getattr(f, key) for f in parts]))
    out.n_events = sum(f.n_events for f in parts)
    return out


def _drive(model, a, hist, nu):
    """What multiplies lam in the three compared models."""
    if model == "graph_linear":
        return a
    if model == "graph_nonlinear":
        return np.where(a > 0, a, 1.0) ** nu * (a > 0)
    levels = np.arange(1, hist.shape[1] + 1, dtype=float) ** nu
    return hist @ levels


def rates(model, params, a, hist):
    """Adoption rates for the rows of a and hist."""
    if model == "group_rate":
        lam, b, mu = params
        return lam * a + mu * hist[:, 1:].sum(axis=1) + b
    lam, b, nu = params
    return lam * _drive(model, a, hist, nu) + b


def loglik(model, params, f: Features):
    """Log-likelihood, in nats, of the adoptions in f's window."""
    r = rates(model, params, f.a, f.hist)
    at_events = rates(model, params, f.ev_a, f.ev_hist)
    return float(np.log(at_events).sum() - (r * f.dt).sum())


def fit(model, f: Features):
    """Maximum-likelihood parameters, from several starting points; the best fit is
    kept. Rates are fitted on a log scale, within LOG_BOUNDS."""
    if model == "group_rate":
        return _fit_group_rate(f)
    exposure = f.dt.sum()
    b0 = max(f.n_events, 1) / exposure
    drive = _drive(model, f.a, f.hist, 1.0)
    lam0 = b0 / max(float((drive * f.dt).sum() / exposure), 1e-12)
    linear = model == "graph_linear"

    def unpack(z):
        return np.exp(z[0]), np.exp(z[1]), (1.0 if linear else z[2])

    def neg(z):
        return -loglik(model, unpack(z), f)

    bounds = [LOG_BOUNDS, LOG_BOUNDS] + ([] if linear else [NU_BOUNDS])
    best = None
    for s_lam in (0.1, 1.0, 10.0):
        for s_b in (0.1, 0.5, 1.0):
            for nu in ([None] if linear else (0.5, 1.0, 2.0, 4.0)):
                z0 = [log(lam0 * s_lam), log(b0 * s_b)] + ([] if linear else [nu])
                r = minimize(neg, z0, method="L-BFGS-B", bounds=bounds)
                if best is None or r.fun < best.fun:
                    best = r
    return unpack(best.x)


def _fit_group_rate(f: Features):
    exposure = f.dt.sum()
    b0 = max(f.n_events, 1) / exposure
    lam0 = b0 / max(float((f.a * f.dt).sum() / exposure), 1e-12)
    groups_on = f.hist[:, 1:].sum(axis=1)
    mu0 = b0 / max(float((groups_on * f.dt).sum() / exposure), 1e-12)

    def neg(z):
        return -loglik("group_rate", tuple(np.exp(z)), f)

    best = None
    for s_lam in (0.01, 0.1, 1.0):
        for s_b in (0.1, 0.5, 1.0):
            for s_mu in (0.01, 0.1, 1.0):
                z0 = [log(lam0 * s_lam), log(b0 * s_b), log(mu0 * s_mu)]
                r = minimize(neg, z0, method="L-BFGS-B", bounds=[LOG_BOUNDS] * 3)
                if best is None or r.fun < best.fun:
                    best = r
    return tuple(np.exp(best.x))


def rule_bits(model, n_adoptions):
    """Bits for writing down the fitted rule: (1/2) log2 n per parameter, with n the
    number of adoptions fitted (Rommens et al., Sec. 5)."""
    return N_PARAMS[model] * 0.5 * log2(max(n_adoptions, 2))


def together_apart_chances(model, params, exposure):
    """Predicted chances of adopting after one meeting of `exposure` seconds with two
    adopters together, or two meetings of `exposure` seconds with one adopter each. The
    background rate is left out, as in run.true_chances."""
    if model == "group_rate":
        lam, _, mu = params
        together = (2 * lam + mu) * exposure
    else:
        lam, _, nu = params
        together = lam * 2 ** nu * exposure
    return {"together": 1 - exp(-together), "apart": 1 - exp(-2 * lam * exposure)}
