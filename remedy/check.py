"""Implementation checks, independent of the code paths in stats.py and fit.py.

1. Exposure H: recomputed on a 1-second grid by asking, at each grid point, how many
   adopters each person has among contacts and in the group.
2. Adoption counts D: recomputed by scanning all windows for each adoption.
3. Remedy fits: the log-likelihood is concave in (lam, mu, b) on the linear scale, so a
   solve on that scale finds the global maximum; the log-scale fit should reach it.
4. Share of people who adopt in each world, over 150 sets of gatherings, against the
   49% to 61% given in SIMULATION.md. The 20 runs alone are too few to check this.
"""

import numpy as np
from scipy.optimize import minimize

import fit
import sim
import stats


def grid_exposure(windows, t_adopt, dt=1.0):
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
                        hits.append(((t_adopt[nb] < ti).sum(), (t_adopt[others] < ti).sum()))
        assert len(hits) <= 1, "a person is in two windows at once"
        D[hits[0] if hits else (0, 0)] += 1
    return D


def linear_scale_fit(model, H, D):
    g = (fit.A >= 2) if model == "remedy_graph" else (fit.C >= 2)
    feats = [fit.A, g.astype(float), np.ones_like(fit.A)]
    used = D > 0

    def neg(p):
        rate = sum(pk * f for pk, f in zip(p, feats))
        ll = (D[used] * np.log(np.maximum(rate[used], 1e-300))).sum() - (H * rate).sum()
        grad = [(D[used] * f[used] / np.maximum(rate[used], 1e-300)).sum() - (H * f).sum()
                for f in feats]
        return -ll, -np.array(grad)

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
        windows = {"log": stats.log_windows(gatherings),
                   "sensors": sim.make_sensor_record(gatherings, np.random.default_rng(s_ss))}
        for w, world in enumerate(sim.WORLDS):
            t_adopt = sim.spread(gatherings, world, np.random.default_rng(w_ss[2 * w]))
            for rec, win in windows.items():
                H, D = stats.exposure(win, t_adopt)
                Hg = grid_exposure(win, t_adopt)
                rel = np.abs(H - Hg).sum() / H.sum()
                dd = int(np.abs(D - scan_adoptions(win, t_adopt)).sum())
                worst_h, worst_d = max(worst_h, rel), max(worst_d, dd)
                gaps = []
                for model in ("remedy_graph", "remedy_group"):
                    _, ll = fit.fit(model, H, D)
                    gaps.append(linear_scale_fit(model, H, D) - ll)
                worst_ll = max(worst_ll, *gaps)
                print(f"seed {seed} {world:8s} {rec:7s} H rel. diff {rel:.2e}  "
                      f"D diff {dd}  LL gap (linear minus log fit) "
                      f"{gaps[0]:+.2e} {gaps[1]:+.2e}")
    print(f"\nworst H relative difference {worst_h:.2e} (grid of 1 s, so small nonzero expected)")
    print(f"worst D difference {worst_d} (should be 0)")
    print(f"largest LL gain of the linear-scale solve {worst_ll:.2e} nats (should be about 0 or less)")

    rng = np.random.default_rng(12345)
    shares = {w: [] for w in sim.WORLDS}
    for _ in range(150):
        g = sim.make_gatherings(rng)
        for w in sim.WORLDS:
            shares[w].append(np.isfinite(sim.spread(g, w, rng)).mean())
    print("\nshare who adopt over 150 sets of gatherings (SIMULATION.md: 49% to 61%):")
    for w, v in shares.items():
        v = 100 * np.array(v)
        print(f"  {w:8s} {v.mean():.1f}% (standard error {v.std() / np.sqrt(len(v)):.1f})")


if __name__ == "__main__":
    main()
