"""Figures of the results.

Usage: uv run python figure.py [SETTING]   (default pilot)
Writes, in outputs/figures/:
  wins_SETTING: wins under the message length and under the held-out misfit, and the
    true and predicted effect of meeting two adopters together rather than one at a
    time;
  holdout_SETTING: wins under three ways of holding out data (for the supplement).
Each figure is saved as .pdf, .tif and .png (light) and _dark.png.
"""

import io
import sys
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from common import EXPOSURE, OUTPUTS
from model import MODELS, together_apart_chances
from report import SHORT, bits_for, by_condition, load, winner

plt.rcParams["hatch.linewidth"] = 2.0

# Each palette was checked with the dataviz palette script against its own surface;
# the dark one is the same hues stepped for the dark surface. The worlds take muted
# hues that no model uses (chosen by the author); teal and slate fall below the
# script's chroma floor, so the world lines also differ in line style and are
# labeled directly.
THEMES = {
    "light": {"surface": "#fcfcfb", "text": "#2b2b29", "muted": "#5c5b55",
              "axis": "#c9c8c0", "G-lin": "#2a78d6", "G-nonlin": "#eb6834",
              "H": "#1baf7a", "independent": "#2f6f73", "joint": "#a8324a",
              "both": "#6b6f80"},
    "dark": {"surface": "#1a1a19", "text": "#f0efec", "muted": "#c3c2b7",
             "axis": "#4a4945", "G-lin": "#3987e5", "G-nonlin": "#d95926",
             "H": "#199e70", "independent": "#4f9da2", "joint": "#d4566f",
             "both": "#8a8ea0"},
}
MODEL_KEYS = ("G-lin", "G-nonlin", "H")
STEP = "step"
NAMES = {"G-lin": "linear graph", "G-nonlin": "nonlinear graph", "H": "hypergraph",
         STEP: "linear graph + group rate"}
COLUMNS = {"G-lin": "linear\ngraph", "G-nonlin": "nonlinear\ngraph",
           "H": "hyper-\ngraph"}
WORLDS = {"independent": "pairwise", "joint": "group", "both": "mixed"}
RUNS = 20
# Each model also has its own marker, so that the dots can be told apart without color.
MARKERS = {"G-lin": "o", "G-nonlin": "s", "H": "^"}


def mix(color, surface, a):
    """The color seen when color is laid over surface with opacity a."""
    c = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    s = [int(surface[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a * x + (1 - a) * y):02x}" for x, y in zip(c, s))


def luminance(hex_color):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def ink(face):
    """Black or white, whichever has the higher contrast with the bar (WCAG ratio)."""
    lum = luminance(face)
    return "black" if (lum + 0.05) / 0.05 >= 1.05 / (lum + 0.05) else "white"


def counts(cs, criterion):
    """Runs won by each model. A tied run counts for every model in the tie."""
    if len(cs) != RUNS:
        raise SystemExit(f"expected {RUNS} runs, found {len(cs)}")
    wins = Counter()
    for c in cs:
        w = winner({m: bits_for(criterion, v) for m, v in c["models"].items()})
        wins.update(w.split("="))
    return {k: wins.get(k, 0) for k in MODEL_KEYS}


def style(ax, title, t):
    ax.set_facecolor(t["surface"])
    ax.set_title(title, fontsize=9, loc="left", color=t["text"])
    ax.tick_params(labelsize=8, colors=t["muted"], length=0)
    # Frontiers asks for lines at least 2 points wide.
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["axis"])
    ax.spines["bottom"].set_linewidth(2.0)


def draw_effect(ax, effect, t):
    """effect: (title, rows), rows a list of ("world, record", true, {model: (low, mid,
    high)}), in percentage points. One column per world and record, with the models
    side by side in it and the true effect as a bar across it."""
    title, rows = effect
    style(ax, title, t)
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(t["axis"])
    ax.spines["left"].set_linewidth(2.0)
    ax.spines["bottom"].set_visible(False)
    ticks, labels, worlds = [], [], {}
    for i, (label, true, models) in enumerate(rows):
        world, record = label.split(", ")
        x0 = (i // 2) * 2.6 + (i % 2) * 1.15
        ax.plot([x0 - 0.5, x0 + 0.5], [true, true], color=t["text"], lw=2.0,
                solid_capstyle="butt", zorder=1)
        keys = list(models)
        for n, k in enumerate(keys):
            lo, mid, hi = models[k]
            x = x0 + (n - (len(keys) - 1) / 2) * 0.25
            if k == STEP:
                # Not one of the compared models, so it is drawn hollow in ink rather
                # than in a fourth series color.
                ax.plot([x, x], [lo, hi], color=t["text"], lw=2.0, zorder=2)
                ax.plot(x, mid, "D", ms=7, mfc=t["surface"], mec=t["text"], mew=2.0,
                        zorder=3)
                continue
            ax.plot([x, x], [lo, hi], color=t[k], lw=2.0, zorder=2)
            ax.plot(x, mid, MARKERS[k], ms=8, color=t[k], mec=t["surface"], mew=1.0,
                    zorder=3)
        ticks.append(x0)
        labels.append(record)
        worlds.setdefault(world, []).append(x0)
    ax.set_xticks(ticks, labels)
    for world, xs in worlds.items():
        ax.text(sum(xs) / len(xs), -0.13, world, transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=8, color=t["text"])
    ax.set_xlim(ticks[0] - 0.7, ticks[-1] + 0.7)
    ax.set_ylim(-12, 68)
    ax.set_yticks(range(0, 61, 20))
    ax.set_ylabel("together minus one at a time,\npercentage points", fontsize=8,
                  color=t["muted"])


def draw(panels, t, height, effect=None):
    """panels: list of (title, rows), where rows is a list of (label, counts), drawn
    side by side. effect: a panel drawn by draw_effect below them, across the width."""
    fig = plt.figure(figsize=(180 / 25.4, height), facecolor=t["surface"])
    grid = fig.add_gridspec(2 if effect else 1, len(panels),
                            height_ratios=[1, 0.9] if effect else None)
    axes = [fig.add_subplot(grid[0, 0])]
    axes += [fig.add_subplot(grid[0, i], sharey=axes[0]) for i in range(1, len(panels))]
    for ax, (title, rows) in zip(axes, panels):
        style(ax, title, t)
        ax.spines["bottom"].set_visible(False)
        for y, (_, wins) in enumerate(rows):
            for x, k in enumerate(MODEL_KEYS):
                face = mix(t[k], t["surface"], 0.12 + 0.88 * wins[k] / RUNS)
                ax.add_patch(plt.Rectangle((x - 0.46, y - 0.42), 0.92, 0.84, fc=face,
                                           lw=0))
                ax.text(x, y, str(wins[k]), ha="center", va="center", fontsize=8,
                        color=ink(face))
        ax.set_xlim(-0.5, len(MODEL_KEYS) - 0.5)
        ax.set_xticks(range(len(MODEL_KEYS)), [COLUMNS[k] for k in MODEL_KEYS])
    for ax in axes[1:]:
        ax.tick_params(labelleft=False)
    labels = [label for label, _ in panels[0][1]]
    axes[0].set_yticks(range(len(labels)), labels)
    axes[0].set_ylim(len(labels) - 0.5, -0.5)
    if effect is None:
        fig.tight_layout()
        return fig
    ax = fig.add_subplot(grid[1, :])
    draw_effect(ax, effect, t)
    handles = [plt.Line2D([0], [0], marker=MARKERS[k], ls="none", ms=8, color=t[k])
               for k in MODEL_KEYS]
    handles.append(plt.Line2D([0], [0], marker="D", ls="none", ms=7,
                              mfc=t["surface"], mec=t["text"], mew=2.0))
    handles.append(plt.Line2D([0], [0], color=t["text"], lw=2.0))
    labels_shown = [NAMES[k] for k in MODEL_KEYS] + [NAMES[STEP], "true effect"]
    # The legend belongs to panel C only. Its top left corner is empty, because the
    # effects in the pairwise world are all near zero.
    ax.legend(handles, labels_shown, loc="upper left", ncol=1, frameon=False,
              fontsize=8, labelcolor=t["text"], borderaxespad=0.3)
    fig.tight_layout()
    return fig


def wins_panels(rows):
    keys = [(w, r) for w in WORLDS for r in ("log", "sensors")]
    return [(title, [(f"{WORLDS[w]}, {r}", counts(rows[(w, r)], criterion))
                     for w, r in keys])
            for criterion, title in (
                ("heldout_message_bits", "(A) Message length"),
                ("heldout_logloss_bits", "(B) Held-out misfit"))]


def effect_panel(rows):
    """Median and interquartile range over runs of each model's predicted effect."""
    keys = [(w, r) for w in WORLDS for r in ("log", "sensors")]
    out = []
    for w, r in keys:
        cs = rows[(w, r)]
        tr = cs[0]["truth"]
        models = {}
        for m in MODELS:
            d = [100 * (ch["together"] - ch["apart"]) for ch in
                 (together_apart_chances(m, c["models"][m]["params_full"], EXPOSURE)
                  for c in cs)]
            models[SHORT[m]] = tuple(np.percentile(d, (25, 50, 75)))
        d = [100 * (c["extra"]["group_step"]["together_apart"]["together"]
                    - c["extra"]["group_step"]["together_apart"]["apart"]) for c in cs]
        models[STEP] = tuple(np.percentile(d, (25, 50, 75)))
        out.append((f"{WORLDS[w]}, {r}", 100 * (tr["together"] - tr["apart"]), models))
    return ("(C) Causal effect", out)


def holdout_panels(rows):
    held = {"heldout_logloss_bits": "second process",
            "heldout_people_bits": "split by people",
            "heldout_time_bits": "split in time"}
    return [(title,
             [(f"{WORLDS[w]}, {h}", counts(rows[(w, r)], c))
              for w in WORLDS for c, h in held.items()])
            for r, title in (("log", "(A) Meeting log"), ("sensors", "(B) Sensors"))]


def save(make, path):
    light = make(THEMES["light"])
    # Frontiers asks for RGB TIF, JPEG or EPS at 300 dpi, 180 mm wide for two columns,
    # with no text under 8 points.
    light.savefig(f"{path}.pdf", dpi=300, facecolor=THEMES["light"]["surface"])
    buf = io.BytesIO()
    light.savefig(buf, format="png", dpi=300, facecolor=THEMES["light"]["surface"])
    Image.open(buf).convert("RGB").save(f"{path}.tif", dpi=(300, 300),
                                        compression="tiff_lzw")
    # The PNGs for the web page have no background, so they sit on the page's own.
    light.savefig(f"{path}.png", dpi=300, transparent=True)
    make(THEMES["dark"]).savefig(f"{path}_dark.png", dpi=300, transparent=True)
    plt.close("all")


def main(name):
    rows = by_condition(load(name))
    out = OUTPUTS / "figures"
    out.mkdir(parents=True, exist_ok=True)
    save(lambda t: draw(wins_panels(rows), t, 5.6, effect_panel(rows)),
         out / f"wins_{name}")
    save(lambda t: draw(holdout_panels(rows), t, 4.4), out / f"holdout_{name}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pilot")
