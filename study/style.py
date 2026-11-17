"""Colors, axis style and saving, shared by the figures.

Every figure is drawn twice, in a light and a dark theme, and saved as PDF, TIF and PNG
(light) and as a PNG for dark pages. Frontiers asks for RGB TIF at 300 dpi, 180 mm wide
for two columns, no text under 8 points and lines at least 2 points wide.
"""

import io

import matplotlib.pyplot as plt
from PIL import Image

# Each palette was checked for color-vision deficiencies and contrast against its own
# background; the dark one has the same hues, stepped for the dark background. The
# worlds take muted hues that no model uses. Teal and slate have little color, so the
# world lines also differ in line style and are labeled directly.
THEMES = {
    "light": {"surface": "#fcfcfb", "text": "#2b2b29", "muted": "#5c5b55",
              "axis": "#c9c8c0", "graph_linear": "#2a78d6",
              "graph_nonlinear": "#eb6834", "hypergraph": "#1baf7a",
              "pairwise": "#2f6f73", "group": "#a8324a", "mixed": "#6b6f80"},
    "dark": {"surface": "#1a1a19", "text": "#f0efec", "muted": "#c3c2b7",
             "axis": "#4a4945", "graph_linear": "#3987e5",
             "graph_nonlinear": "#d95926", "hypergraph": "#199e70",
             "pairwise": "#4f9da2", "group": "#d4566f", "mixed": "#8a8ea0"},
}
WIDTH = 180 / 25.4  # inches


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
    """Black or white, whichever has the higher contrast with a filled box."""
    lum = luminance(face)
    return "black" if (lum + 0.05) / 0.05 >= 1.05 / (lum + 0.05) else "white"


def style(ax, title, t):
    """A panel with a title on the left, no frame except a 2-point bottom axis."""
    ax.set_facecolor(t["surface"])
    ax.set_title(title, fontsize=9, loc="left", color=t["text"])
    ax.tick_params(labelsize=8, colors=t["muted"], length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["axis"])
    ax.spines["bottom"].set_linewidth(2.0)


def left_axis(ax, t):
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(t["axis"])
    ax.spines["left"].set_linewidth(2.0)


def save(draw, path):
    """draw(theme) returns a figure. Writes path.pdf, .tif and .png, and _dark.png."""
    light = draw(THEMES["light"])
    light.savefig(f"{path}.pdf", dpi=300, facecolor=THEMES["light"]["surface"])
    buf = io.BytesIO()
    light.savefig(buf, format="png", dpi=300, facecolor=THEMES["light"]["surface"])
    Image.open(buf).convert("RGB").save(f"{path}.tif", dpi=(300, 300),
                                        compression="tiff_lzw")
    # The PNGs for the web page have no background, so they sit on the page's own.
    light.savefig(f"{path}.png", dpi=300, transparent=True)
    draw(THEMES["dark"]).savefig(f"{path}_dark.png", dpi=300, transparent=True)
    plt.close("all")
