"""Run the main setting, fit the three models and save the results as JSON."""

import argparse
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

import fit
import sim
import stats

RESULTS = Path(__file__).parent / "results" / "runs.json"
WORKERS = 3


def one_run(seed):
    """Simulate one run, fit every model on both records and return the results."""
    t0 = time.time()
    # One stream for the gatherings, one for the sensors and two for each world, so
    # that each stream stays the same when the code for another stream changes.
    ss = np.random.SeedSequence(seed)
    g_ss, s_ss, *w_ss = ss.spawn(2 + 2 * len(sim.WORLDS))
    gatherings = sim.make_gatherings(np.random.default_rng(g_ss))
    sensors = sim.make_sensor_record(gatherings, np.random.default_rng(s_ss))
    windows = {"log": stats.log_windows(gatherings), "sensors": sensors}
    out = {"seed": seed, "n_gatherings": len(gatherings),
           "met_per_day": sim.people_met_per_day(gatherings), "worlds": {}}
    for w, world in enumerate(sim.WORLDS):
        # The first process is used for fitting and the second is held out.
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
    print(f"seed {seed} done in {time.time() - t0:.1f} s", flush=True)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20, help="seeds 0 to RUNS - 1")
    parser.add_argument("--out", type=Path, default=RESULTS, help="output JSON file")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with Pool(WORKERS) as pool:
        runs = pool.map(one_run, range(args.runs))
    args.out.write_text(json.dumps({"runs": runs}, indent=1) + "\n")
    print(f"{args.runs} runs in {time.time() - t0:.1f} s, saved to {args.out}")


if __name__ == "__main__":
    main()
