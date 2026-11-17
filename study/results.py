"""Load the runs of a setting and compute what the paper reports from them: who wins
under each criterion, and each model's predicted causal effect.
"""

import json
from collections import Counter, defaultdict

import numpy as np

from models import CHECK_MODELS, MODELS
from settings import OUTPUTS, RUNS, fingerprint, settings, tuned_path

SHORT = {"graph_linear": "G-lin", "graph_nonlinear": "G-nonlin", "hypergraph": "H",
         "group_rate": "G+rate"}

# message_length is the criterion of Rommens et al. (Sec. 8, p. 22): "encode both
# structure and rule, and compare their held-out message lengths". The "_cliques"
# version writes down the graph by naming cliques (their p. 18). heldout_misfit is the
# last part of the message length alone. The rest are reported only in the text report:
# Eq. (29) on the fitted process, with and without the structure, and the other two ways
# of holding out data (Supplementary File S2).
CRITERIA = ("message_length", "message_length_cliques", "heldout_misfit",
            "fitted_message_length", "fitted_message_length_without_structure",
            "split_by_people_misfit", "split_in_time_misfit")
SWEEP_CRITERIA = ("message_length", "message_length_cliques", "heldout_misfit")

# Scores that are equal up to numerical error share the win. On the meeting log the
# nonlinear graph and hypergraph models are the same model and their scores differ by
# exactly 0; the smallest gap between different models in the main setting is about
# 0.001 bits.
TIE = 1e-6


def criterion_bits(criterion, scores):
    """The score of one model in one condition under a criterion, in bits."""
    if criterion.startswith("message_length"):
        key = ("structure_bits_cliques" if criterion.endswith("_cliques")
               else "structure_bits")
        return scores[key] + scores["rule_bits"] + scores["heldout_misfit_bits"]
    if criterion == "fitted_message_length_without_structure":
        return scores["fitted_message_bits"] - scores["structure_bits"]
    return scores[{"heldout_misfit": "heldout_misfit_bits",
                   "fitted_message_length": "fitted_message_bits",
                   "split_by_people_misfit": "split_by_people_misfit_bits",
                   "split_in_time_misfit": "split_in_time_misfit_bits"}[criterion]]


def winner(bits):
    """The model with the fewest bits, or several joined by "=" if they tie."""
    best = min(bits.values())
    return "=".join(SHORT[m] for m in MODELS if bits[m] <= best + TIE)


def load(name):
    """The runs of a setting, checked against the current tuning file."""
    current = fingerprint(tuned_path(settings(name)))
    files = sorted((OUTPUTS / "runs" / name).glob("run_*.json"))
    runs = [json.loads(f.read_text()) for f in files]
    stale = [r["run"] for r in runs if r["tuned"] != current]
    if stale:
        raise SystemExit(f"{name}: runs made from an old tuning: {stale}")
    return runs


def by_condition(runs):
    """The results of every run, grouped by (world, record)."""
    rows = defaultdict(list)
    for r in runs:
        for c in r["conditions"]:
            rows[(c["world"], c["record"])].append(c)
    return rows


def winners(cs, criterion):
    """Counter of winners (single models and ties) over the runs of one condition."""
    return Counter(winner({m: criterion_bits(criterion, v)
                           for m, v in c["models"].items()}) for c in cs)


def wins_per_model(cs, criterion):
    """Runs won by each model, out of RUNS. A tied run counts for every model in the
    tie, as in Figure 2."""
    if len(cs) != RUNS:
        raise SystemExit(f"expected {RUNS} runs, found {len(cs)}")
    wins = Counter()
    for w, n in winners(cs, criterion).items():
        for m in w.split("="):
            wins[m] += n
    return {m: wins.get(SHORT[m], 0) for m in MODELS}


def effect(chances):
    """Together minus one at a time, in percentage points."""
    return 100 * (chances["together"] - chances["apart"])


def predicted_effects(cs):
    """Quartiles (25, 50, 75) over runs of each model's predicted effect, compared
    models first, then the check model."""
    out = {}
    for m in MODELS:
        out[m] = tuple(np.percentile([effect(c["models"][m]["together_apart"])
                                      for c in cs], (25, 50, 75)))
    for m in CHECK_MODELS:
        out[m] = tuple(np.percentile([effect(c["check_models"][m]["together_apart"])
                                      for c in cs], (25, 50, 75)))
    return out
