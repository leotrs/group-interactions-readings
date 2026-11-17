"""Checks of the implementation, computed without the code in stats.py and fit.py.

1. Time spent H: recomputed on a 1-second grid by counting, at each grid point, the
   adopters among each person's contacts and in the person's group.
2. Adoption counts D: recomputed by scanning all windows for each adoption.
3. Group rate fits: the log-likelihood is concave in (lam, mu, b) on the linear scale,
   so a fit on that scale finds the global maximum. The log-scale fit should reach it.
4. Share of people who adopt in each world, over 150 sets of gatherings, against the
   49% to 61% given in SIMULATION.md. The 20 runs alone are too few to check this.
"""

import sys

import numpy as np
from scipy.optimize import minimize

import fit
import sim
import stats


def grid_exposure(windows, t_adopt, dt=1.0):
    """Return H computed on a grid with spacing dt."""
    grid = np.arange(0.0, sim.T_END, dt) + dt / 2
    a = np.zeros((len(grid), sim.N_PEOPLE), dtype=np.int8)
    c = np.zeros((len(grid), sim.N_PEOPLE), dtype=np.int8)
    for s, e, groups in windows:
        lo, hi = np.searchsorted(grid, [s, e])
        tt = grid[lo:hi, None]
        for members, nbrs in groups:
            for i in members:
                others = members[members != i]
                nb = others if nbrs is None else nbrs[int(i)]
                a[lo:hi, i] = (t_adopt[nb][None, :] <= tt).sum(1)
                c[lo:hi, i] = (t_adopt[others][None, :] <= tt).sum(1)
    risk = grid[:, None] < t_adopt[None, :]
    H = np.zeros((stats.KMAX, stats.KMAX))
    np.add.at(H, (a[risk], c[risk]), dt)
    return H


def scan_adoptions(windows, t_adopt):
    """Return D computed by scanning all windows for each adoption."""
    D = np.zeros((stats.KMAX, stats.KMAX))
    for i in np.flatnonzero(np.isfinite(t_adopt) & (t_adopt > 0)):
        ti = t_adopt[i]
        hits = []
        for s, e, groups in windows:
            if s <= ti < e:
                for members, nbrs in groups:
                    if i in members:
                        others = members[members != i]
                        nb = others if nbrs is None else nbrs[int(i)]
                        hits.append(((t_adopt[nb] < ti).sum(),
                                     (t_adopt[others] < ti).sum()))
        assert len(hits) <= 1, "a person is in two windows at once"
        D[hits[0] if hits else (0, 0)] += 1
    return D


def linear_scale_fit(model, H, D):
    """Fit a group rate model on the linear scale; return the log-likelihood."""
    g = (fit.A >= 2) if model == "group_rate_graph" else (fit.C >= 2)
    feats = [fit.A, g.astype(float), np.ones_like(fit.A)]
    used = D > 0

    def neg(p):
        rate = sum(pk * f for pk, f in zip(p, feats))
        ll = (D[used] * np.log(np.maximum(rate[used], 1e-300))).sum() - (H * rate).sum()
        safe = np.maximum(rate[used], 1e-300)
        grad = [(D[used] * f[used] / safe).sum() - (H * f).sum() for f in feats]
        return -ll, -np.array(grad)

    # The three parameters differ in size by orders of magnitude, so they are rescaled
    # to values near 1 for L-BFGS-B.
    scale = np.array([1e-4, 1e-3, 1e-6])
    r = minimize(lambda q: tuple(v * w for v, w in zip(neg(q * scale), (1.0, scale))),
                 np.ones(3), jac=True, method="L-BFGS-B", bounds=[(0, None)] * 3)
    return -r.fun


def main():
    worst_h, worst_d, worst_ll = 0.0, 0, 0.0
    for seed in range(3):
        ss = np.random.SeedSequence(seed)
        g_ss, s_ss, *w_ss = ss.spawn(2 + 2 * len(sim.WORLDS))
        gatherings = sim.make_gatherings(np.random.default_rng(g_ss))
        sensors = sim.make_sensor_record(gatherings, np.random.default_rng(s_ss))
        windows = {"log": stats.log_windows(gatherings), "sensors": sensors}
        for w, world in enumerate(sim.WORLDS):
            t_adopt = sim.spread(gatherings, world, np.random.default_rng(w_ss[2 * w]))
            for rec, win in windows.items():
                H, D = stats.exposure(win, t_adopt)
                Hg = grid_exposure(win, t_adopt)
                rel = np.abs(H - Hg).sum() / H.sum()
                dd = int(np.abs(D - scan_adoptions(win, t_adopt)).sum())
                worst_h, worst_d = max(worst_h, rel), max(worst_d, dd)
                gaps = []
                for model in ("group_rate_graph", "group_rate_group"):
                    _, ll = fit.fit(model, H, D)
                    gaps.append(linear_scale_fit(model, H, D) - ll)
                worst_ll = max(worst_ll, *gaps)
                print(f"seed {seed} {world:8s} {rec:7s} H rel. diff {rel:.2e}  "
                      f"D diff {dd}  LL gap (linear minus log fit) "
                      f"{gaps[0]:+.2e} {gaps[1]:+.2e}")
    print(f"\nworst H relative difference {worst_h:.2e} "
          "(grid of 1 s, so a small nonzero value is expected)")
    print(f"worst D difference {worst_d} (should be 0)")
    print(f"largest LL gain of the linear-scale fit {worst_ll:.2e} nats "
          "(should be about 0 or less)")
    # Limits for an automatic run: the 1 s grid gives relative differences of about
    # 1e-5, and the two fits agree to about 1e-9 nats.
    failed = [msg for bad, msg in (
        (worst_h > 1e-4, "time at each count differs from the 1 s grid"),
        (worst_d != 0, "adoption counts differ from the separate scan"),
        (worst_ll > 1e-6, "the log-scale fit misses the maximum likelihood"),
    ) if bad]

    rng = np.random.default_rng(12345)
    shares = {w: [] for w in sim.WORLDS}
    for _ in range(150):
        g = sim.make_gatherings(rng)
        for w in sim.WORLDS:
            shares[w].append(np.isfinite(sim.spread(g, w, rng)).mean())
    print("\nshare who adopt over 150 sets of gatherings (SIMULATION.md: 49% to 61%):")
    for w, v in shares.items():
        v = 100 * np.array(v)
        se = v.std() / np.sqrt(len(v))
        print(f"  {w:8s} {v.mean():.1f}% (standard error {se:.1f})")
    if failed:
        sys.exit("FAILED: " + "; ".join(failed))
    print("\nall checks passed")


if __name__ == "__main__":
    main()
