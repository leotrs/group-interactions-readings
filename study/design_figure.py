"""Figure 1 of the paper: the design of the study (worlds, records, models, scores and
settings).

Usage: uv run python design_figure.py
Writes outputs/figures/figure1.{pdf,tif,png} and figure1_dark.png. The adoption rates
are read from the tuned main setting, so the figure matches the simulation.
"""

import json
from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np

from settings import MAIN, OUTPUTS, SWEEP, settings, tuned_path
from style import WIDTH, ink, left_axis, save, style
from world import WORLDS, Params, rate

# One gathering of five people, and the pairs that one sensor sample detected. Fixed
# by hand so that the example shows a gathering split into two partial groups.
PEOPLE = 5
DETECTED = [(0, 1), (1, 2), (3, 4), (0, 2)]


def worlds_panel(ax, p, t):
    style(ax, "(A) Worlds", t)
    k = np.arange(0, PEOPLE + 1)
    dashes = {"pairwise": "-", "group": "--", "mixed": ":"}
    for w in WORLDS:
        r = [3600 * rate(w, int(x), p) for x in k]
        # The group part of the rate switches on at two adopters. A line from 1 to 2
        # would read as a gradual rise, so the line runs on the linear part up to 2 and
        # then rises vertically.
        jump = 2 * r[1] - r[0]
        ax.plot([0, 1, 2, 2, *k[3:]], [r[0], r[1], jump, *r[2:]], ls=dashes[w],
                color=t[w], lw=2.0)
        ax.plot(k, r, "o", ls="none", color=t[w], ms=4)
        ax.text(k[-1] + 0.35, r[-1], w, fontsize=8, va="center", color=t["text"])
    ax.set_xlim(0, PEOPLE + 1.6)
    ax.set_xticks(k)
    ax.set_yticks(range(5))
    ax.set_xlabel("adopters in the gathering", fontsize=8, color=t["muted"])
    ax.set_ylabel("adoption rate, per hour", fontsize=8, color=t["muted"])
    left_axis(ax, t)


def components(n, pairs):
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i

    for a, b in pairs:
        parent[find(a)] = find(b)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def hull(points):
    """Convex hull, in order (points are few, so a gift-wrap is enough)."""
    pts = sorted(map(tuple, points))
    if len(pts) < 3:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return np.array(lower[:-1] + upper[:-1])


def gathering(ax, x0, pairs, groups, title, t):
    angles = np.pi / 2 + 2 * np.pi * np.arange(PEOPLE) / PEOPLE
    xy = np.c_[x0 + 0.7 * np.cos(angles), 0.7 * np.sin(angles)]
    # Each recorded group is outlined with a thick round stroke around its hull, drawn
    # again thinner in the surface color, which leaves a rounded outline 2 points wide
    # (in a color with at least 3:1 contrast) that also works for a group of two.
    for g in groups:
        h = hull(xy[g])
        for lw, color in ((18, t["muted"]), (14, t["surface"])):
            ax.add_patch(plt.Polygon(h, closed=True, fc=t["surface"], ec=color, lw=lw,
                                     joinstyle="round", capstyle="round", zorder=0))
    for a, b in pairs:
        ax.plot(*xy[[a, b]].T, color=t["muted"], lw=2.0, zorder=1)
    ax.plot(*xy.T, "o", ms=7, color=t["text"], mec=t["surface"], mew=1.0, zorder=2)
    ax.text(x0, -1.35, title, ha="center", va="top", fontsize=8, color=t["text"])


def records_panel(ax, t):
    style(ax, "(B) Records", t)
    ax.spines["bottom"].set_visible(False)
    gathering(ax, 0, list(combinations(range(PEOPLE), 2)), [list(range(PEOPLE))],
              "meeting log:\nall pairs,\none group", t)
    gathering(ax, 2.9, DETECTED, components(PEOPLE, DETECTED),
              "sensors, one\nsample: detected\npairs, two groups", t)
    ax.set_xlim(-1.2, 4.1)
    ax.set_ylim(-2.4, 1.2)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xticks([])
    ax.set_yticks([])


# How each hyperparameter of the sweep is shown, and in what unit.
SHOWN = {
    "people_met_per_day": ("people met a day", lambda v: f"{v:g}"),
    "detection_probability": ("sensor detection probability", lambda v: f"{v:g}"),
    "sampling_interval": ("sensor sampling interval", lambda v: f"{v:g} s"),
    "adoption_delay": ("mean delay in recorded adoption times",
                       lambda v: f"{v / 60:g} min"),
    "processes_fitted": ("spreading processes fitted", lambda v: f"{v}"),
    "sensor_groups": ("sensor groups", lambda v: {"components": "components",
                                                  "gatherings": "per gathering"}[v]),
}


def models_panel(ax, t):
    """The case in which the models differ in the study: one sensor group holds the
    person, an adopter detected with the person, a third person, and a second adopter
    detected only with the third person. Rates at lambda = 1, nu = 2 and b = 0: the
    graph models count one adopter in contact, the hypergraph model two in the group."""
    style(ax, "(C) Models", t)
    nu = 2
    rates = {"graph_linear": 1, "graph_nonlinear": 1 ** nu, "hypergraph": 2 ** nu}
    # The bars are named below, so that they can be read without color.
    for x, (m, r) in enumerate(rates.items()):
        ax.bar(x, r, 0.7, color=t[m], lw=0)
    ax.set_xlim(-0.5, 2.5)
    ax.set_xticks(range(3), ["linear\ngraph", "nonlinear\ngraph", "hyper-\ngraph"])
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_ylim(0, 4.4)
    ax.set_ylabel("rate, with $\\lambda = 1$, $\\nu = 2$", fontsize=8,
                  color=t["muted"])
    left_axis(ax, t)
    # The sensor group, drawn above the two short bars.
    inset = ax.inset_axes([0.06, 0.40, 0.6, 0.6])
    inset.axis("off")
    inset.set_xlim(-1.3, 4.6)
    inset.set_ylim(-1.3, 1.6)
    # The person, an adopter, the third person, and the second adopter.
    xy = np.array([[0, 0], [0.8, 0.8], [2.5, -0.1], [3.6, 0.6]])
    h = hull(xy)
    for lw, color in ((18, t["muted"]), (14, t["surface"])):
        inset.add_patch(plt.Polygon(h, closed=True, fc=t["surface"], ec=color, lw=lw,
                                    joinstyle="round", capstyle="round", zorder=0))
    for a, b in ((0, 1), (0, 2), (2, 3)):
        inset.plot(*xy[[a, b]].T, color=t["muted"], lw=2.0, zorder=1)
    inset.plot(*xy[[1, 3]].T, "o", ls="none", ms=7, color=t["text"], mec=t["surface"],
               mew=1.0, zorder=2)
    inset.plot(*xy[2], "o", ms=7, color=t["muted"], mec=t["surface"], mew=1.0, zorder=2)
    inset.plot(*xy[0], "o", ms=7, color=t["surface"], mec=t["text"], mew=2.0, zorder=2)
    labels = (("person", True), ("adopter", False), ("non-\nadopter", True),
              ("adopter", False))
    for (x, y), (label, below) in zip(xy, labels):
        inset.text(x, y + (-0.42 if below else 0.38), label, ha="center",
                   va="top" if below else "bottom", fontsize=8, color=t["text"])


def scores_panel(ax, t):
    """The message length as one bar of three parts, with the held-out misfit marked."""
    style(ax, "(D) Scores", t)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    parts = [("record", 0.40, t["axis"]), ("rule", 0.18, t["muted"]),
             ("misfit", 0.42, t["text"])]
    left = 0
    for name, w, c in parts:
        ax.barh(0.5, w - 0.01, left=left + 0.005, height=0.22, color=c, lw=0)
        ax.text(left + w / 2, 0.5, name, ha="center", va="center", fontsize=8,
                color=ink(c))
        left += w

    def bracket(x0, x1, y, label, up):
        d = 0.05 if up else -0.05
        ax.plot([x0, x0, x1, x1], [y, y + d, y + d, y], color=t["text"], lw=2.0)
        ax.text((x0 + x1) / 2, y + 2.2 * d, label, ha="center",
                va="bottom" if up else "top", fontsize=8, color=t["text"])

    bracket(0, 1, 0.65, "message length", True)
    bracket(1 - parts[-1][1], 1, 0.35, "held-out misfit", False)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, 1)


def settings_panel(ax, t):
    """The hyperparameters as a table: the main setting and the values tried."""
    ax.set_facecolor(t["surface"])
    ax.set_title("(E) Settings", fontsize=9, loc="left", color=t["text"])
    ax.axis("off")
    rows = [("header", "hyperparameter", "main setting", "also tried")]
    for k, vs in SWEEP.items():
        name, show = SHOWN[k]
        rows.append(("row", name, show(MAIN[k]), ", ".join(show(v) for v in vs)))
    cols = (0.0, 0.58, 0.79)
    step = 1 / len(rows)
    y = 1 - step / 2
    rule = {"color": t["muted"], "lw": 2.0, "transform": ax.transAxes, "clip_on": False}
    ax.plot([0, 1], [1, 1], **rule)
    for kind, *cells in rows:
        for x, c in zip(cols, cells):
            ax.text(x, y, c, fontsize=8, va="center", transform=ax.transAxes,
                    color=t["muted"] if kind == "header" else t["text"])
        if kind == "header":
            ax.plot([0, 1], [y - step / 2] * 2, **rule)
        y -= step
    ax.plot([0, 1], [y + step / 2] * 2, **rule)


def draw(t):
    p = Params(**json.loads(tuned_path(settings("main")).read_text())["params"])
    fig = plt.figure(figsize=(WIDTH, 5.4), facecolor=t["surface"])
    grid = fig.add_gridspec(2, 3, height_ratios=[1, 0.9], width_ratios=[1, 1.15, 1])
    worlds_panel(fig.add_subplot(grid[0, 0]), p, t)
    records_panel(fig.add_subplot(grid[0, 1]), t)
    models_panel(fig.add_subplot(grid[0, 2]), t)
    scores_panel(fig.add_subplot(grid[1, 0]), t)
    settings_panel(fig.add_subplot(grid[1, 1:]), t)
    fig.tight_layout()
    return fig


def main():
    out = OUTPUTS / "figures"
    out.mkdir(parents=True, exist_ok=True)
    save(draw, out / "figure1")


if __name__ == "__main__":
    main()
