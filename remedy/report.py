"""Read results/runs.json, write RESULTS.md and print it."""

import json
from pathlib import Path

import numpy as np

import fit
import sim

HERE = Path(__file__).parent
TIE_BITS = 1e-6
RECORDS = ("log", "sensors")
MODEL_NAMES = {"nonlinear": "nonlinear graph", "remedy_graph": "remedy, graph form",
               "remedy_group": "remedy, group form"}


def true_effect(world):
    together = 1 - np.exp(-sim.world_rate(world, 2) * fit.DURATION)
    apart = 1 - np.exp(-2 * sim.world_rate(world, 1) * fit.DURATION)
    return together - apart


def q(xs):
    lo, med, hi = np.percentile(xs, [25, 50, 75])
    return med, lo, hi


def pp(xs):
    med, lo, hi = q(100 * np.asarray(xs))
    return f"{med:.1f} ({lo:.1f} to {hi:.1f})"


def sci(x):
    return f"{x:.2e}"


def main():
    data = json.loads((HERE / "results" / "runs.json").read_text())
    runs = data["runs"]
    n = len(runs)
    L = []
    L.append("# Results\n")
    L.append(f"Main setting, {n} runs (seeds 0 to {n - 1}). Effects are in percentage "
             "points: median over runs, with the interquartile range in brackets. "
             f"Wall time {data['wall_seconds']:.0f} s with 3 worker processes.\n")

    L.append("## Checks of the simulated world\n")
    met = [r["met_per_day"] for r in runs]
    ng = [r["n_gatherings"] for r in runs]
    L.append(f"- Distinct people met per person per day: mean {np.mean(met):.2f} "
             f"(runs {min(met):.2f} to {max(met):.2f}); the specification gives 6.")
    L.append(f"- Gatherings per run: mean {np.mean(ng):.0f}.")
    for world in sim.WORLDS:
        fr = [f for r in runs for f in r["worlds"][world]["adopted_fraction"]]
        L.append(f"- {world} world, share of people who adopt (first adopters counted): "
                 f"mean {100 * np.mean(fr):.1f}% over {len(fr)} processes.")
    L.append("- The specification gives 49% to 61% by world.\n")

    L.append("## Predicted effect of meeting two adopters together rather than apart\n")
    L.append("| world | true | record | nonlinear graph | remedy, graph form | remedy, group form |")
    L.append("|---|---|---|---|---|---|")
    for world in sim.WORLDS:
        for rec in RECORDS:
            cells = [pp([r["worlds"][world]["records"][rec][m]["effect"] for r in runs])
                     for m in fit.MODELS]
            L.append(f"| {world} | {100 * true_effect(world):.2f} | {rec} | " + " | ".join(cells) + " |")
    L.append("")
    L.append("True effects from the world's rule: "
             + ", ".join(f"{w} {100 * true_effect(w):.4f}" for w in sim.WORLDS) + " points.\n")

    L.append("## Median fitted parameters (per second)\n")
    L.append("World rates: lam = 1.3013e-4 (pairwise), mu = 1.1111e-3 (group); "
             "the mixed world has half of each.\n")
    L.append("| world | record | model | lam | mu | nu | b |")
    L.append("|---|---|---|---|---|---|---|")
    for world in sim.WORLDS:
        for rec in RECORDS:
            for m in fit.MODELS:
                ps = [r["worlds"][world]["records"][rec][m]["params"] for r in runs]
                med = {k: np.median([p[k] for p in ps]) for k in ps[0]}
                mu = sci(med["mu"]) if "mu" in med else "-"
                nu = f"{med['nu']:.2f}" if "nu" in med else "-"
                L.append(f"| {world} | {rec} | {MODEL_NAMES[m]} | {sci(med['lam'])} | "
                         f"{mu} | {nu} | {sci(med['b'])} |")
    L.append("")

    L.append("## Held-out misfit: remedy models against the nonlinear graph model\n")
    L.append("Misfit is minus the log-likelihood of the held-out process, in bits, under the "
             "parameters fitted to the first process. All three models have 3 parameters. "
             "'Remedy lower' counts runs in which the remedy model has lower misfit by more "
             f"than {TIE_BITS:g} bits; 'tie' counts runs within that margin. The difference "
             "is nonlinear misfit minus remedy misfit (positive: the remedy fits better).\n")
    L.append("| world | record | remedy form | remedy lower | tie | nonlinear lower | median difference (bits) |")
    L.append("|---|---|---|---|---|---|---|")
    for world in sim.WORLDS:
        for rec in RECORDS:
            for m in ("remedy_graph", "remedy_group"):
                diff = np.array([
                    (r["worlds"][world]["records"][rec][m]["loglik_heldout"]
                     - r["worlds"][world]["records"][rec]["nonlinear"]["loglik_heldout"])
                    / np.log(2) for r in runs])
                win = int((diff > TIE_BITS).sum())
                tie = int((np.abs(diff) <= TIE_BITS).sum())
                med, lo, hi = q(diff)
                L.append(f"| {world} | {rec} | {m.split('_')[1]} | {win} | {tie} | "
                         f"{n - win - tie} | {med:.1f} ({lo:.1f} to {hi:.1f}) |")
    L.append("")

    L.append("## Notes\n")
    L.append("- Check against the paper: the paper reports that the nonlinear graph model fitted "
             "to the meeting log predicts about 15 points in the group world and about 7 or "
             "less in the mixed world. The table above gives the values from this code.")
    L.append("- On the meeting log, a person is in one gathering at a time, so the two remedy "
             "forms have the same likelihood and give identical rows.")
    L.append("- The mean share who adopt over 20 runs can fall outside 49% to 61% by chance. "
             "`just check` measures it over 150 sets of gatherings.")
    L.append("- One sensor record is drawn per run and is used for all worlds and both "
             "processes of that run.")
    L.append("")
    text = "\n".join(L)
    (HERE / "RESULTS.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
