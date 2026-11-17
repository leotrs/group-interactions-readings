"""The three models, their log-likelihood, the fits and the predicted effect.

The log-likelihood is computed from the statistics H and D in stats.py.
"""

import itertools

import numpy as np
from scipy.optimize import minimize

from stats import KMAX

A = np.arange(KMAX)[:, None] * np.ones((1, KMAX))
C = np.ones((KMAX, 1)) * np.arange(KMAX)[None, :]
LOG_A = np.log(np.where(A > 0, A, 1.0))
LOG_BOUND = (-40.0, 5.0)
NU_BOUND = (0.05, 6.0)
DURATION = 900.0

MODELS = ("nonlinear", "group_rate_graph", "group_rate_group")


def _unpack(model, x):
    """Turn the fitted coordinates into named parameters."""
    if model == "nonlinear":
        return {"lam": np.exp(x[0]), "b": np.exp(x[1]), "nu": x[2]}
    return {"lam": np.exp(x[0]), "mu": np.exp(x[1]), "b": np.exp(x[2])}


def _rate_and_grad(model, x):
    """Return the rate at each (a, c) and its derivatives in the fitted coordinates."""
    p = _unpack(model, x)
    if model == "nonlinear":
        pw = np.where(A > 0, A ** p["nu"], 0.0)
        term = p["lam"] * pw
        rate = term + p["b"]
        grads = [term, np.full_like(A, p["b"]), term * LOG_A]
    else:
        g = (A >= 2) if model == "group_rate_graph" else (C >= 2)
        lam_t = p["lam"] * A
        mu_t = p["mu"] * g
        rate = lam_t + mu_t + p["b"]
        grads = [lam_t, mu_t, np.full_like(A, p["b"])]
    return rate, grads


def loglik(model, x, H, D):
    """Return the log-likelihood in nats."""
    rate, _ = _rate_and_grad(model, x)
    used = D > 0
    return float((D[used] * np.log(rate[used])).sum() - (H * rate).sum())


def _neg(x, model, H, D):
    """Return minus the log-likelihood and its gradient, for the optimizer."""
    rate, grads = _rate_and_grad(model, x)
    used = D > 0
    ll = (D[used] * np.log(rate[used])).sum() - (H * rate).sum()
    g = [(D[used] * gr[used] / rate[used]).sum() - (H * gr).sum() for gr in grads]
    return -ll, -np.array(g)


def _starts(model):
    """Return the grid of starting points."""
    if model == "nonlinear":
        return [np.array(s) for s in itertools.product(
            (-12.0, -9.0, -6.0), (-16.0, -12.0, -8.0), (0.5, 1.0, 2.0, 4.0))]
    return [np.array(s) for s in itertools.product(
        (-12.0, -9.0, -6.0), (-10.0, -7.0, -4.0), (-16.0, -12.0, -8.0))]


def fit(model, H, D):
    """Fit from every starting point; return the best coordinates and log-likelihood."""
    if model == "nonlinear":
        bounds = [LOG_BOUND, LOG_BOUND, NU_BOUND]
    else:
        bounds = [LOG_BOUND] * 3
    best = None
    for x0 in _starts(model):
        r = minimize(_neg, x0, args=(model, H, D), jac=True, method="L-BFGS-B",
                     bounds=bounds)
        if best is None or r.fun < best.fun:
            best = r
    return best.x, -best.fun


def effect(model, x):
    """Return the predicted effect of meeting two adopters together.

    The effect is the probability of adopting in one 900 s meeting with two adopters,
    minus the probability of adopting over two 900 s meetings with one adopter each,
    computed without the background rate b.
    """
    p = _unpack(model, x)
    if model == "nonlinear":
        together = p["lam"] * 2.0 ** p["nu"]
    else:
        together = 2.0 * p["lam"] + p["mu"]
    apart = 2.0 * p["lam"]
    return float(np.exp(-apart * DURATION) - np.exp(-together * DURATION))


def params(model, x):
    """Return the fitted parameters as plain floats."""
    return {k: float(v) for k, v in _unpack(model, x).items()}
