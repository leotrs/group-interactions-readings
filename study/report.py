"""Print the results of one setting, or the winners in every setting of the sweep.

Usage: uv run python report.py [SETTING]   full report of one setting (default main)
       uv run python report.py sweep       winners in all 14 settings
"""

import json
import sys

import numpy as np

from models import CHECK_MODELS, MODELS
from results import (CRITERIA, SHORT, SWEEP_CRITERIA, TIE, by_condition, effect, load,
                     predicted_effects, winners)
from settings import EXPOSURE, setting_names, settings, tuned_path


def win_line(cs, criterion):
    """Runs won by each model alone, then ties, as a short string."""
    wins = winners(cs, criterion)
    alone = [f"{SHORT[m]} {wins.get(SHORT[m], 0)}" for m in MODELS]
    tied = [f"{k} {v}" for k, v in sorted(wins.items()) if "=" in k]
    return ", ".join(alone + tied)


def sweep():
    for name in setting_names():
        runs = load(name)
        if not runs:
            print(f"\n{name}: no runs yet")
            continue
        print(f"\n{name} ({len(runs)} runs)")
        rows = by_condition(runs)
        for criterion in SWEEP_CRITERIA:
            print(f"  {criterion}")
            for (w, rec), cs in rows.items():
                print(f"    {w:9s} {rec:8s} {win_line(cs, criterion)}")


def main(name):
    runs = load(name)
    tuned = json.loads(tuned_path(settings(name)).read_text())
    print(f"{name}: {len(runs)} runs; settings:", settings(name))
    print("tuned parameters:", tuned["params"])
    print("adoption fractions in tuning:", tuned["adoption_fractions"])
    rows = by_condition(runs)

    print("\nBits for writing down the record (median over runs)")
    for (w, rec), cs in rows.items():
        g = np.median([c["models"]["graph_linear"]["structure_bits"] for c in cs])
        h = np.median([c["models"]["hypergraph"]["structure_bits"] for c in cs])
        print(f"  {w:9s} {rec:8s} graph {g:.0f}  hypergraph {h:.0f}")

    names = [SHORT[m] for m in MODELS]
    for criterion in CRITERIA:
        print(f"\nWins by {criterion}, out of {len(runs)} runs. Models within {TIE} bits "
              "of the best share the win, shown as a tie.")
        print(f"  {'':18s}" + "".join(f"{x:>10s}" for x in names + ["tie"]))
        for (w, rec), cs in rows.items():
            wins = winners(cs, criterion)
            ties = sum(v for k, v in wins.items() if "=" in k)
            tied = sorted(k for k in wins if "=" in k)
            print(f"  {w:9s} {rec:8s}" + "".join(f"{wins.get(x, 0):10d}" for x in names)
                  + f"{ties:10d}  {' '.join(tied)}")

    all_models = MODELS + CHECK_MODELS
    print(f"\nEffect of meeting two adopters together rather than one at a time, each "
          f"for {EXPOSURE / 60:.0f} min, in percentage points: true, and median over "
          f"runs of each model's prediction (G+rate takes no part in the comparisons)")
    print(f"  {'':18s}{'true':>8s}" + "".join(f"{SHORT[m]:>10s}" for m in all_models))
    for (w, rec), cs in rows.items():
        pred = predicted_effects(cs)
        print(f"  {w:9s} {rec:8s}{effect(cs[0]['true']):8.1f}"
              + "".join(f"{pred[m][1]:10.1f}" for m in all_models))

    print("\nHeld-out misfit: runs in which G+rate has a lower misfit than G-nonlin")
    for (w, rec), cs in rows.items():
        lower = sum(c["check_models"]["group_rate"]["heldout_misfit_bits"]
                    < c["models"]["graph_nonlinear"]["heldout_misfit_bits"] - TIE
                    for c in cs)
        print(f"  {w:9s} {rec:8s} {lower} of {len(cs)}")

    print("\nFitted exponent nu (median; fixed at 1 for G-lin), share adopted, and the "
          "numbers of distinct pairs and groups recorded (median)")
    for (w, rec), cs in rows.items():
        nus = [np.median([c["models"][m]["params"][2] for c in cs]) for m in MODELS]
        print(f"  {w:9s} {rec:8s}" + "".join(f"{v:10.2f}" for v in nus)
              + f" | adopted {np.mean([c['adopted'] for c in cs]):.2f}"
              + f" | pairs {np.median([c['n_pairs'] for c in cs]):.0f}"
              + f" | groups {np.median([c['n_groups'] for c in cs]):.0f}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "main"
    sweep() if arg == "sweep" else main(arg)
