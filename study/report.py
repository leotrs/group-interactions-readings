"""Summarize the runs.

Usage: uv run python report.py [SETTING]   full summary of one setting (default pilot)
       uv run python report.py sweep       wins for every setting, all three models
"""

import json
import sys
from collections import Counter, defaultdict

import numpy as np

from common import (EXPOSURE, OUTPUTS, fingerprint, setting_names, settings,
                    tuned_path)
from model import MODELS, together_apart_chances

SHORT = {"graph_linear": "G-lin", "graph_nonlinear": "G-nonlin", "hypergraph": "H"}

# heldout_message_bits is the criterion of Rommens et al., Sec. 8, p. 22: "encode both
# structure and rule, and compare their held-out message lengths". The "_cliques"
# version codes the graph by naming cliques (their p. 18). The "_given_record" versions
# leave out the bits for writing down who met whom. The last two criteria (other ways
# of holding out data) are for the supplement.
CRITERIA = ("heldout_message_bits", "heldout_message_bits_cliques",
            "heldout_logloss_bits", "eq29_bits", "eq29_bits_given_record",
            "heldout_people_bits", "heldout_time_bits")
SWEEP_CRITERIA = ("heldout_message_bits", "heldout_message_bits_cliques",
                  "heldout_logloss_bits")


def bits_for(criterion, scores):
    if criterion.startswith("heldout_message_bits"):
        key = "structure_bits_cliques" if criterion.endswith("_cliques") else (
            "structure_bits")
        return scores[key] + scores["rule_bits"] + scores["heldout_logloss_bits"]
    if criterion.endswith("_given_record"):
        base = criterion.removesuffix("_given_record")
        return scores[base] - scores["structure_bits"]
    return scores[criterion]


# Scores that are equal up to numerical error share the win. On the meeting log the
# nonlinear graph and hypergraph models are the same model and their scores differ by
# exactly 0; the smallest gap between different models in the pilot is about 0.001 bits.
TIE = 1e-6


def winner(bits):
    best = min(bits.values())
    return "=".join(SHORT[m] for m in MODELS if bits[m] <= best + TIE)


def load(name):
    current = fingerprint(tuned_path(settings(name)))
    files = sorted((OUTPUTS / "runs" / name).glob("rep_*.json"))
    reps = [json.loads(f.read_text()) for f in files]
    stale = [r["rep"] for r in reps if r["tuned"] != current]
    if stale:
        raise SystemExit(f"{name}: replicates made from an old tuning: {stale}")
    return reps


def by_condition(reps):
    rows = defaultdict(list)
    for r in reps:
        for c in r["conditions"]:
            rows[(c["mechanism"], c["recording"])].append(c)
    return rows


def win_counts(cs, criterion):
    """Wins of each model alone, and ties, as a short string."""
    wins = Counter(winner({m: bits_for(criterion, v) for m, v in c["models"].items()})
                   for c in cs)
    alone = [f"{SHORT[m]} {wins.get(SHORT[m], 0)}" for m in MODELS]
    tied = [f"{k} {v}" for k, v in sorted(wins.items()) if "=" in k]
    return ", ".join(alone + tied)


def sweep():
    for name in setting_names():
        reps = load(name)
        if not reps:
            print(f"\n{name}: no runs yet")
            continue
        print(f"\n{name} ({len(reps)} replicates)")
        rows = by_condition(reps)
        for criterion in SWEEP_CRITERIA:
            print(f"  {criterion}")
            for key, cs in rows.items():
                print(f"    {key[0]:12s} {key[1]:8s} {win_counts(cs, criterion)}")


def main(name):
    reps = load(name)
    tuned = json.loads(tuned_path(settings(name)).read_text())
    print(f"{name}: {len(reps)} replicates; settings:", settings(name))
    print("tuned parameters:", tuned["params"])
    print("adoption fractions in tuning:", tuned["fractions"])
    rows = by_condition(reps)
    print("\nStructure bits (median): bits to write down who met whom")
    for key, cs in rows.items():
        g = np.median([c["models"]["graph_linear"]["structure_bits"] for c in cs])
        h = np.median([c["models"]["hypergraph"]["structure_bits"] for c in cs])
        print(f"  {key[0]:12s} {key[1]:8s} graph {g:.0f}  hypergraph {h:.0f}")
    names = [SHORT[m] for m in MODELS]
    for criterion in CRITERIA:
        print(f"\nWins by {criterion}, out of {len(reps)} replicates. Models within "
              f"{TIE} bits of the best share the win, shown as a tie.")
        print(f"  {'':21s}" + "".join(f"{x:>10s}" for x in names + ["tie"]))
        for key, cs in rows.items():
            wins = Counter(winner({m: bits_for(criterion, v)
                                   for m, v in c["models"].items()}) for c in cs)
            ties = sum(v for k, v in wins.items() if "=" in k)
            tied = sorted(k for k in wins if "=" in k)
            print(f"  {key[0]:12s} {key[1]:8s}"
                  + "".join(f"{wins.get(x, 0):10d}" for x in names)
                  + f"{ties:10d}  {' '.join(tied)}")
    print(f"\nTogether vs apart: chance of adopting after one gathering of "
          f"{EXPOSURE / 60:.0f} min with two adopters (together), or two gatherings of "
          f"{EXPOSURE / 60:.0f} min with one adopter each (apart). Models: median over "
          "replicates of the chances predicted from the fitted parameters.")
    print(f"  {'':21s}{'':9s}{'true':>8s}" + "".join(f"{x:>10s}" for x in names))
    for key, cs in rows.items():
        for arm in ("together", "apart"):
            pred = [np.median([together_apart_chances(m, c["models"][m]["params_full"],
                                                      EXPOSURE)[arm] for c in cs])
                    for m in MODELS]
            print(f"  {key[0]:12s} {key[1]:8s} {arm:9s}{cs[0]['truth'][arm]:8.3f}"
                  + "".join(f"{v:10.3f}" for v in pred))
    print("\nFitted exponent nu (median; graph-linear is fixed at 1), adoption, record")
    for key, cs in rows.items():
        nus = [np.median([c["models"][m]["params_full"][2] for c in cs])
               for m in MODELS]
        print(f"  {key[0]:12s} {key[1]:8s}" + "".join(f"{v:10.2f}" for v in nus)
              + f" | adopted {np.mean([c['adopted'] for c in cs]):.2f}"
              + f" | pairs {np.median([c['n_edges'] for c in cs]):.0f}"
              + f" | groups {np.median([c['n_hyperedges'] for c in cs]):.0f}")

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    sweep() if arg == "sweep" else main(arg)
