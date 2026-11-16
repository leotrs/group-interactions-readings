"""Runs of the study: 3 mechanisms x 2 recordings, 20 replicates, for one setting of
the hyperparameters (spec.md, common.py).

Usage: uv run python run.py SETTING [JOBS]   (SETTING is "pilot", e.g. "d=0.25", a
comma-separated list, or "sweep" for all; default 3 jobs, at the lowest CPU priority)
Writes outputs/runs/SETTING/rep_R.json. A replicate is skipped if its file exists and
was made from the current tuning file, so an interrupted run resumes.
"""

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import exp, log

import numpy as np

import model
import record
import structure
import world
from common import (EXPOSURE, OUTPUTS, REPLICATES, fingerprint, setting_names,
                    settings, tuned_path, write_json)


def truth(mechanism, p: world.Params):
    """Exact chance of adopting in the experiment: two adopters, each present for
    EXPOSURE seconds, together in one gathering or apart in two (spec.md)."""
    together = world.rate(mechanism, 2, p) * EXPOSURE
    apart = 2 * world.rate(mechanism, 1, p) * EXPOSURE
    return {"together": 1 - exp(-together), "apart": 1 - exp(-apart)}


def features(rec, fitted, held_out, n, t_max):
    """The data used by score(), built once for all three models. fitted and held_out
    are lists of recorded adoption times, one per spreading process."""
    contacts = model.Contacts(n, rec)
    early, late = [], []
    for t in fitted:
        t_med = float(np.median(t[np.isfinite(t) & (t > 0)]))
        early.append(model.Features(contacts, t, 0.0, t_med))
        late.append(model.Features(contacts, t, t_med, t_max))
    return {"full": model.combine([model.Features(contacts, t, 0.0, t_max)
                                   for t in fitted]),
            "held_out": model.combine([model.Features(contacts, t, 0.0, t_max)
                                       for t in held_out]),
            "early": model.combine(early), "late": model.combine(late)}


def score(name, f, s_bits, keep):
    """Eq. (29) of Rommens et al. on the fitted processes, and their held-out log loss
    (item iii, p. 16) on other spreading processes over the same contacts. Two other
    held-out splits are kept for the supplement: fit on the people with keep True and
    score the rest, and fit before the median adoption time and score the rest."""
    full = f["full"]
    p_full = model.fit(name, full)

    def bits(params, data):
        return -model.loglik(name, params, data) / log(2)

    return {
        "structure_bits": s_bits["proposition_7"],
        "structure_bits_cliques": s_bits["cliques"],
        "rule_bits": model.rule_bits(name, full.n_events),
        "eq29_bits": (s_bits["proposition_7"] + model.rule_bits(name, full.n_events)
                      + bits(p_full, full)),
        "heldout_logloss_bits": bits(p_full, f["held_out"]),
        "heldout_people_bits": bits(model.fit(name, full.people(keep)),
                                    full.people(~keep)),
        "heldout_time_bits": bits(model.fit(name, f["early"]), f["late"]),
        "params_full": list(p_full),
        "together_apart": model.together_apart_chances(name, p_full, EXPOSURE),
    }


def score_extra(name, f):
    """A model fitted for the causal effect only (model.EXTRA_MODELS): its fit, its
    held-out misfit, and its predicted effect. It takes no part in the comparisons."""
    p_full = model.fit(name, f["full"])
    return {"heldout_logloss_bits": -model.loglik(name, p_full, f["held_out"]) / log(2),
            "params_full": [float(x) for x in p_full],
            "together_apart": model.together_apart_chances(name, p_full, EXPOSURE)}


def processes(g, mech, p, s, rng, count):
    out = []
    for _ in range(count):
        seeds = rng.choice(p.n, p.n_seeds, replace=False)
        t = world.spread(g, mech, p, rng, seeds)
        out.append(record.recorded_times(t, seeds, s["delta"], rng, p.t_max))
    return out


def replicate(name, rep):
    s = settings(name)
    tuned = tuned_path(s)
    p = world.Params(**json.loads(tuned.read_text())["params"])
    rng = np.random.default_rng(rep)
    g = world.gatherings(p, rng)
    keep = rng.random(p.n) < 0.5
    recordings = {
        "log": record.log_record(g),
        "sensors": record.sensor_record(g, s["d"], rng, p.t_max, s["interval"],
                                        s["grouping"]),
    }
    out = {"rep": rep, "tuned": fingerprint(tuned), "settings": s, "conditions": []}
    for mech in world.MECHANISMS:
        fitted = processes(g, mech, p, s, rng, s["processes"])
        held_out = processes(g, mech, p, s, rng, s["processes"])
        for rec_name, rec in recordings.items():
            edges, hyperedges = rec.edges(), rec.hyperedges()
            f = features(rec, fitted, held_out, p.n, p.t_max)
            h_bits = structure.hypergraph_bits(p.n, hyperedges)
            g_bits = {"proposition_7": structure.graph_bits(p.n, len(edges)),
                      "cliques": structure.graph_clique_bits(p.n, edges)}
            bits = {"graph_linear": g_bits, "graph_nonlinear": g_bits,
                    "hypergraph": {"proposition_7": h_bits, "cliques": h_bits}}
            out["conditions"].append({
                "mechanism": mech, "recording": rec_name,
                "adopted": float(np.mean([np.isfinite(t).mean() for t in fitted])),
                "n_edges": len(edges), "n_hyperedges": len(hyperedges),
                "truth": truth(mech, p),
                "models": {m: score(m, f, bits[m], keep) for m in model.MODELS},
                "extra": {m: score_extra(m, f) for m in model.EXTRA_MODELS}})
    write_json(OUTPUTS / "runs" / name / f"rep_{rep}.json", out)
    return rep


def done(name, rep):
    path = OUTPUTS / "runs" / name / f"rep_{rep}.json"
    return (path.exists() and json.loads(path.read_text())["tuned"]
            == fingerprint(tuned_path(settings(name))))


def main(names, jobs):
    todo = [(n, r) for n in names for r in range(REPLICATES) if not done(n, r)]
    failed = []
    with ProcessPoolExecutor(jobs, initializer=os.nice, initargs=(20,)) as pool:
        futures = {pool.submit(replicate, n, r): (n, r) for n, r in todo}
        for fut in as_completed(futures):
            n, r = futures[fut]
            try:
                fut.result()
                print(n, "replicate", r, "done", flush=True)
            except Exception as err:  # report every replicate even if one breaks
                failed.append((n, r))
                print(n, "replicate", r, "FAILED:", repr(err), flush=True)
    if failed:
        sys.exit(f"failed replicates: {sorted(failed)}")


if __name__ == "__main__":
    names = setting_names() if sys.argv[1] == "sweep" else sys.argv[1].split(",")
    main(names, int(sys.argv[2]) if len(sys.argv) > 2 else 3)
