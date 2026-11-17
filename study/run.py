"""Run the study for one or more settings: 3 worlds x 2 records, 20 runs each.

Usage: uv run python run.py SETTING [JOBS]
SETTING is "main", a setting such as "detection_probability=0.25", a comma-separated
list of them, or "sweep" for all 14. JOBS worker processes (default 3) run at the
lowest CPU priority.

Writes outputs/runs/SETTING/run_RR.json. A run is skipped if its file exists and was
made from the current tuning file, so an interrupted job resumes where it stopped.

Run r draws everything from the random seed r, in a fixed order: the gatherings, a
random half of the people (for one of the other ways of holding out data), the sensor
record, and then, for each world in turn, the fitted and the held-out spreading
processes. The same run number therefore gives the same gatherings and records in all
three worlds, and the same results on every machine with the same library versions.
"""

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import exp, log

import numpy as np

import codes
import models
import records
import world
from settings import (EXPOSURE, RUNS, fingerprint, run_path, setting_names, settings,
                      tuned_path, write_json)


def true_chances(w, p: world.Params):
    """Exact chances of adopting for a person who meets two adopters, each for EXPOSURE
    seconds, together in one gathering or one at a time in two."""
    together = world.rate(w, 2, p) * EXPOSURE
    apart = 2 * world.rate(w, 1, p) * EXPOSURE
    return {"together": 1 - exp(-together), "apart": 1 - exp(-apart)}


def features(rec, fitted, held_out, n_people, t_max):
    """The data that the models are fitted to and scored on, built once for all
    models. fitted and held_out are lists of recorded adoption times, one per process.
    "early" and "late" split each fitted process at its median adoption time, for one
    of the other ways of holding out data."""
    contacts = models.Contacts(n_people, rec)
    early, late = [], []
    for t in fitted:
        t_med = float(np.median(t[np.isfinite(t) & (t > 0)]))
        early.append(models.Features(contacts, t, 0.0, t_med))
        late.append(models.Features(contacts, t, t_med, t_max))
    return {"fitted": models.combine([models.Features(contacts, t, 0.0, t_max)
                                      for t in fitted]),
            "held_out": models.combine([models.Features(contacts, t, 0.0, t_max)
                                        for t in held_out]),
            "early": models.combine(early), "late": models.combine(late)}


def score(model, f, structure_bits, keep):
    """Fit a compared model to the fitted processes and score it.

    heldout_misfit_bits: minus the log-likelihood, in bits, of the held-out processes.
    The message length of the paper is structure_bits + rule_bits + heldout_misfit_bits
    (results.criterion_bits). fitted_message_bits is Eq. (29) of Rommens et al. on the
    fitted processes themselves. The last two misfits are the other ways of holding out
    data in Supplementary File S2: fit on the people with keep True and score the rest,
    and fit before the median adoption time and score after it."""
    fitted = f["fitted"]
    params = models.fit(model, fitted)

    def bits(p, data):
        return -models.loglik(model, p, data) / log(2)

    return {
        "structure_bits": structure_bits["pairs"],
        "structure_bits_cliques": structure_bits["cliques"],
        "rule_bits": models.rule_bits(model, fitted.n_events),
        "fitted_message_bits": (structure_bits["pairs"]
                                + models.rule_bits(model, fitted.n_events)
                                + bits(params, fitted)),
        "heldout_misfit_bits": bits(params, f["held_out"]),
        "split_by_people_misfit_bits": bits(models.fit(model, fitted.people(keep)),
                                            fitted.people(~keep)),
        "split_in_time_misfit_bits": bits(models.fit(model, f["early"]), f["late"]),
        "params": [float(x) for x in params],
        "together_apart": models.together_apart_chances(model, params, EXPOSURE),
    }


def score_check_model(model, f):
    """Fit a model that takes no part in the comparisons (models.CHECK_MODELS): its
    parameters, held-out misfit and predicted effect."""
    params = models.fit(model, f["fitted"])
    return {"heldout_misfit_bits": -models.loglik(model, params, f["held_out"]) / log(2),
            "params": [float(x) for x in params],
            "together_apart": models.together_apart_chances(model, params, EXPOSURE)}


def spreading_processes(g, w, p, s, rng, count):
    out = []
    for _ in range(count):
        first = rng.choice(p.n_people, p.n_first_adopters, replace=False)
        t = world.spread(g, w, p, rng, first)
        out.append(records.recorded_times(t, first, s["adoption_delay"], rng, p.t_max))
    return out


def compute_run(name, run):
    """The results of one run, as saved in its file."""
    s = settings(name)
    tuned = tuned_path(s)
    p = world.Params(**json.loads(tuned.read_text())["params"])
    rng = np.random.default_rng(run)
    g = world.gatherings(p, rng)
    keep = rng.random(p.n_people) < 0.5
    recs = {
        "log": records.meeting_log(g),
        "sensors": records.sensors(g, s["detection_probability"], rng, p.t_max,
                                   s["sampling_interval"], s["sensor_groups"]),
    }
    out = {"run": run, "tuned": fingerprint(tuned), "settings": s, "conditions": []}
    for w in world.WORLDS:
        fitted = spreading_processes(g, w, p, s, rng, s["processes_fitted"])
        held_out = spreading_processes(g, w, p, s, rng, s["processes_fitted"])
        for rec_name, rec in recs.items():
            edges, hyperedges = rec.edges(), rec.hyperedges()
            f = features(rec, fitted, held_out, p.n_people, p.t_max)
            h_bits = codes.hypergraph_bits(p.n_people, hyperedges)
            g_bits = {"pairs": codes.graph_bits(p.n_people, len(edges)),
                      "cliques": codes.graph_clique_bits(p.n_people, edges)}
            structure_bits = {"graph_linear": g_bits, "graph_nonlinear": g_bits,
                              "hypergraph": {"pairs": h_bits, "cliques": h_bits}}
            out["conditions"].append({
                "world": w, "record": rec_name,
                "adopted": float(np.mean([np.isfinite(t).mean() for t in fitted])),
                "n_pairs": len(edges), "n_groups": len(hyperedges),
                "true": true_chances(w, p),
                "models": {m: score(m, f, structure_bits[m], keep)
                           for m in models.MODELS},
                "check_models": {m: score_check_model(m, f)
                                 for m in models.CHECK_MODELS}})
    return out


def one_run(name, run):
    write_json(run_path(name, run), compute_run(name, run))
    return run


def done(name, run):
    path = run_path(name, run)
    return (path.exists() and json.loads(path.read_text())["tuned"]
            == fingerprint(tuned_path(settings(name))))


def main(names, jobs):
    todo = [(n, r) for n in names for r in range(RUNS) if not done(n, r)]
    failed = []
    with ProcessPoolExecutor(jobs, initializer=os.nice, initargs=(20,)) as pool:
        futures = {pool.submit(one_run, n, r): (n, r) for n, r in todo}
        for fut in as_completed(futures):
            n, r = futures[fut]
            try:
                fut.result()
                print(n, "run", r, "done", flush=True)
            except Exception as err:  # report every run even if one fails
                failed.append((n, r))
                print(n, "run", r, "FAILED:", repr(err), flush=True)
    if failed:
        sys.exit(f"failed runs: {sorted(failed)}")


if __name__ == "__main__":
    names = setting_names() if sys.argv[1] == "sweep" else sys.argv[1].split(",")
    main(names, int(sys.argv[2]) if len(sys.argv) > 2 else 3)
