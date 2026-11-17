"""Figure 2 of the paper and the figure of Supplementary File S2, from the saved runs.

Usage: uv run python figures.py [SETTING]   (default main)
Writes, in outputs/figures/:
  figure2: (A, B) runs won by each model under the message length and under the
    held-out misfit; (C) the true and predicted effect of meeting two adopters
    together rather than one at a time;
  figure_s2: runs won under three ways of holding out data.
Figure 1 is drawn by design_figure.py.
"""

import sys

import matplotlib.pyplot as plt

from models import CHECK_MODELS, MODELS
from results import by_condition, effect, load, predicted_effects, wins_per_model
from settings import OUTPUTS, RUNS
from style import WIDTH, ink, left_axis, mix, save, style
from world import WORLDS

RECORDS = ("log", "sensors")
NAMES = {"graph_linear": "linear graph", "graph_nonlinear": "nonlinear graph",
         "hypergraph": "hypergraph", "group_rate": "linear graph + group rate"}
COLUMNS = {"graph_linear": "linear\ngraph", "graph_nonlinear": "nonlinear\ngraph",
           "hypergraph": "hyper-\ngraph"}
# Each model has its own marker, so that the markers can be told apart without color.
MARKERS = {"graph_linear": "o", "graph_nonlinear": "s", "hypergraph": "^"}


def draw_wins(ax, title, rows, t):
    """One win matrix: a row per condition, a column per model, shaded by wins."""
    style(ax, title, t)
    ax.spines["bottom"].set_visible(False)
    for y, (_, wins) in enumerate(rows):
        for x, m in enumerate(MODELS):
            face = mix(t[m], t["surface"], 0.12 + 0.88 * wins[m] / RUNS)
            ax.add_patch(plt.Rectangle((x - 0.46, y - 0.42), 0.92, 0.84, fc=face, lw=0))
            ax.text(x, y, str(wins[m]), ha="center", va="center", fontsize=8,
                    color=ink(face))
    ax.set_xlim(-0.5, len(MODELS) - 0.5)
    ax.set_xticks(range(len(MODELS)), [COLUMNS[m] for m in MODELS])


def draw_effect(ax, rows, t):
    """rows: a list of (world, record, true effect, {model: (low, mid, high)}), in
    percentage points. One column per world and record, with the models side by side
    in it and the true effect as a bar across it."""
    style(ax, "(C) Causal effect", t)
    left_axis(ax, t)
    ax.spines["bottom"].set_visible(False)
    ticks, labels, centers = [], [], {}
    for i, (w, rec, true, pred) in enumerate(rows):
        x0 = (i // 2) * 2.6 + (i % 2) * 1.15
        ax.plot([x0 - 0.5, x0 + 0.5], [true, true], color=t["text"], lw=2.0,
                solid_capstyle="butt", zorder=1)
        for n, m in enumerate(pred):
            lo, mid, hi = pred[m]
            x = x0 + (n - (len(pred) - 1) / 2) * 0.25
            if m in CHECK_MODELS:
                # Not one of the compared models, so it is drawn hollow in ink rather
                # than in a fourth series color.
                ax.plot([x, x], [lo, hi], color=t["text"], lw=2.0, zorder=2)
                ax.plot(x, mid, "D", ms=7, mfc=t["surface"], mec=t["text"], mew=2.0,
                        zorder=3)
                continue
            ax.plot([x, x], [lo, hi], color=t[m], lw=2.0, zorder=2)
            ax.plot(x, mid, MARKERS[m], ms=8, color=t[m], mec=t["surface"], mew=1.0,
                    zorder=3)
        ticks.append(x0)
        labels.append(rec)
        centers.setdefault(w, []).append(x0)
    ax.set_xticks(ticks, labels)
    for w, xs in centers.items():
        ax.text(sum(xs) / len(xs), -0.13, w, transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=8, color=t["text"])
    ax.set_xlim(ticks[0] - 0.7, ticks[-1] + 0.7)
    ax.set_ylim(-12, 68)
    ax.set_yticks(range(0, 61, 20))
    ax.set_ylabel("together minus one at a time,\npercentage points", fontsize=8,
                  color=t["muted"])
    handles = [plt.Line2D([0], [0], marker=MARKERS[m], ls="none", ms=8, color=t[m])
               for m in MODELS]
    handles.append(plt.Line2D([0], [0], marker="D", ls="none", ms=7,
                              mfc=t["surface"], mec=t["text"], mew=2.0))
    handles.append(plt.Line2D([0], [0], color=t["text"], lw=2.0))
    names = [NAMES[m] for m in MODELS + CHECK_MODELS] + ["true effect"]
    # The top left corner is empty, because the effects in the pairwise world are all
    # near zero.
    ax.legend(handles, names, loc="upper left", ncol=1, frameon=False, fontsize=8,
              labelcolor=t["text"], borderaxespad=0.3)


def draw(panels, t, height, effect_rows=None):
    """Win matrices side by side, and, if effect_rows is given, the effect panel below
    them across the width."""
    fig = plt.figure(figsize=(WIDTH, height), facecolor=t["surface"])
    grid = fig.add_gridspec(2 if effect_rows else 1, len(panels),
                            height_ratios=[1, 0.9] if effect_rows else None)
    axes = [fig.add_subplot(grid[0, 0])]
    axes += [fig.add_subplot(grid[0, i], sharey=axes[0]) for i in range(1, len(panels))]
    for ax, (title, rows) in zip(axes, panels):
        draw_wins(ax, title, rows, t)
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)
    labels = [label for label, _ in panels[0][1]]
    axes[0].set_yticks(range(len(labels)), labels)
    axes[0].set_ylim(len(labels) - 0.5, -0.5)
    if effect_rows:
        draw_effect(fig.add_subplot(grid[1, :]), effect_rows, t)
    fig.tight_layout()
    return fig


def figure2(rows):
    conditions = [(w, rec) for w in WORLDS for rec in RECORDS]
    panels = [(title, [(f"{w}, {rec}", wins_per_model(rows[(w, rec)], criterion))
                       for w, rec in conditions])
              for criterion, title in (("message_length", "(A) Message length"),
                                       ("heldout_misfit", "(B) Held-out misfit"))]
    effects = [(w, rec, effect(rows[(w, rec)][0]["true"]),
                predicted_effects(rows[(w, rec)])) for w, rec in conditions]
    return lambda t: draw(panels, t, 5.6, effects)


def figure_s2(rows):
    held = {"heldout_misfit": "second process",
            "split_by_people_misfit": "split by people",
            "split_in_time_misfit": "split in time"}
    panels = [(title, [(f"{w}, {how}", wins_per_model(rows[(w, rec)], criterion))
                       for w in WORLDS for criterion, how in held.items()])
              for rec, title in (("log", "(A) Meeting log"), ("sensors", "(B) Sensors"))]
    return lambda t: draw(panels, t, 4.4)


def main(name):
    rows = by_condition(load(name))
    out = OUTPUTS / "figures"
    out.mkdir(parents=True, exist_ok=True)
    suffix = "" if name == "main" else f"_{name}"
    save(figure2(rows), out / f"figure2{suffix}")
    save(figure_s2(rows), out / f"figure_s2{suffix}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
