"""Run the 20 runs of the main setting, fit the models and save results/runs.json."""

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import fit
import sim
import stats

OUT = Path(__file__).parent / "results"
WORKERS = 3


def one_run(seed):
    t0 = time.time()
    ss = np.random.SeedSequence(seed)
    g_ss, s_ss, *w_ss = ss.spawn(2 + 2 * len(sim.WORLDS))
    gatherings = sim.make_gatherings(np.random.default_rng(g_ss))
    windows = {"log": stats.log_windows(gatherings),
               "sensors": sim.make_sensor_record(gatherings, np.random.default_rng(s_ss))}
    out = {"seed": seed, "n_gatherings": len(gatherings),
           "met_per_day": sim.people_met_per_day(gatherings), "worlds": {}}
    for w, world in enumerate(sim.WORLDS):
        procs = [sim.spread(gatherings, world, np.random.default_rng(w_ss[2 * w + j]))
                 for j in range(2)]
        wres = {"adopted_fraction": [float(np.isfinite(p).mean()) for p in procs],
                "n_adoptions_fit": int((np.isfinite(procs[0]) & (procs[0] > 0)).sum()),
                "records": {}}
        for rec, win in windows.items():
            H1, D1 = stats.exposure(win, procs[0])
            H2, D2 = stats.exposure(win, procs[1])
            rres = {}
            for model in fit.MODELS:
                x, ll_fit = fit.fit(model, H1, D1)
                rres[model] = {"params": fit.params(model, x),
                               "loglik_fit": ll_fit,
                               "loglik_heldout": fit.loglik(model, x, H2, D2),
                               "effect": fit.effect(model, x)}
            wres["records"][rec] = rres
        out["worlds"][world] = wres
    out["seconds"] = time.time() - t0
    print(f"seed {seed} done in {out['seconds']:.1f} s", flush=True)
    return out


def main():
    n_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    with Pool(WORKERS) as pool:
        runs = pool.map(one_run, range(n_runs))
    wall = time.time() - t0
    (OUT / "runs.json").write_text(json.dumps({"wall_seconds": wall, "runs": runs}, indent=1))
    print(f"{n_runs} runs in {wall:.1f} s wall time")


if __name__ == "__main__":
    main()
