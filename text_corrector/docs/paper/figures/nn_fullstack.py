import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.gridspec import GridSpec
import numpy as np

BLUE, FILL = "#2f5d8a", "#dceafe"
GREEN, GFILL = "#3b6d2b", "#cfe8bf"
RED, RFILL = "#a83f25", "#f4d3c8"
AMBER, AFILL = "#9a6a12", "#fbeecb"
GREY, GYFILL = "#6a6a6a", "#e3e3df"
EDGE, TEAL = "#bcc5cf", "#2c8a8a"
plt.rcParams.update({"font.family": "serif", "font.size": 11})


def neuron(ax, x, y, r=0.13, fc=FILL, ec=BLUE):
    ax.add_patch(Circle((x, y), r, facecolor=fc, edgecolor=ec, lw=1.3, zorder=4))


def vdots(ax, x, y):
    for dy in (-0.1, 0, 0.1):
        ax.add_patch(Circle((x, y + dy), 0.02, facecolor="#555", edgecolor="none", zorder=4))


def column(ax, x, n, ytop, ybot, fc=FILL, ec=BLUE, dots=True):
    ys = np.linspace(ytop, ybot, n)
    for y in ys:
        neuron(ax, x, y, fc=fc, ec=ec)
    if dots:
        vdots(ax, x, ybot - 0.35)
    return ys


def connect(ax, x1, ys1, x2, ys2, color=EDGE, lw=0.45, alpha=0.5):
    for a in ys1:
        for b in ys2:
            ax.plot([x1, x2], [a, b], color=color, lw=lw, alpha=alpha, zorder=1)


def bracket(ax, x1, x2, y, text):
    ax.plot([x1, x2], [y, y], color="#555", lw=1.3)
    ax.plot([x1, x1], [y, y - 0.12], color="#555", lw=1.3)
    ax.plot([x2, x2], [y, y - 0.12], color="#555", lw=1.3)
    ax.text((x1 + x2) / 2, y + 0.12, text, ha="center", va="bottom", fontsize=11.5,
            fontweight="bold", color="#333")


fig = plt.figure(figsize=(16, 9.6))
fig.suptitle("KazRoBERTa detector — full stack at the neuron level:  "
             "embedding → 6 encoder layers → KEEP / ERROR",
             fontsize=15.5, fontweight="bold", y=0.985)
gs = GridSpec(2, 1, height_ratios=[1.18, 1.0], hspace=0.12)

# ── TOP: the full forward stack ──────────────────────────────────────────────
ax = fig.add_subplot(gs[0]); ax.set_xlim(-0.6, 9.6); ax.set_ylim(0.4, 4.5)
ax.set_aspect("equal"); ax.axis("off")

x_tok, x_emb = 0.0, 1.25
x_layers = [2.55, 3.45, 4.35, 5.25, 6.15, 7.05]
x_out = 8.55
ytop, ybot = 3.35, 1.55

tok = column(ax, x_tok, 5, 3.2, 1.7, fc=GYFILL, ec=GREY)
emb = column(ax, x_emb, 6, ytop, ybot)
connect(ax, x_tok, tok, x_emb, emb)
prev = emb
for xl in x_layers:
    cur = column(ax, xl, 6, ytop, ybot)
    connect(ax, prev_x if (prev is not emb) else x_emb, prev, xl, cur)
    prev, prev_x = cur, xl
# head
connect(ax, x_layers[-1], prev, x_out, [2.55, 1.75])
neuron(ax, x_out, 2.55, r=0.18, fc=GFILL, ec=GREEN)
neuron(ax, x_out, 1.75, r=0.18, fc=RFILL, ec=RED)
ax.text(x_out + 0.28, 2.55, "KEEP", ha="left", va="center", color=GREEN, fontweight="bold", fontsize=11)
ax.text(x_out + 0.28, 1.75, "ERROR", ha="left", va="center", color=RED, fontweight="bold", fontsize=11)

bracket(ax, x_layers[0] - 0.3, x_layers[-1] + 0.3, 3.95,
        "× 6  Transformer encoder layers  (self-attention + FFN, residual)")
ax.text(x_tok, 1.25, "L tokens", ha="center", fontsize=9.5, color="#555")
ax.text(x_emb, 1.05, "embed 768", ha="center", fontsize=9.5, color="#555")
for i, xl in enumerate(x_layers, 1):
    ax.text(xl, 1.05, f"L{i}·768", ha="center", fontsize=9, color="#555")
ax.text(x_out, 1.2, "per token", ha="center", fontsize=9, color="#555")
ax.text((x_layers[0] + x_layers[-1]) / 2, 0.55,
        "residual stream (each column = 768-d hidden state, 6 of 768 units shown)",
        ha="center", fontsize=9, style="italic", color="#777")

# ── BOTTOM: one encoder layer expanded ───────────────────────────────────────
ax2 = fig.add_subplot(gs[1]); ax2.set_xlim(-0.3, 9.9); ax2.set_ylim(0.2, 3.9)
ax2.set_aspect("equal"); ax2.axis("off")
ax2.text(4.8, 3.7, "↑  each of the 6 blocks above = one such layer, expanded:",
         ha="center", fontsize=11.5, fontweight="bold", color="#333")

xi, xa, xf, xo = 0.7, 3.0, 5.6, 8.1
ci = column(ax2, xi, 6, 3.0, 1.2)
ca = column(ax2, xa, 6, 3.0, 1.2, fc="#d7ece9", ec=TEAL)
connect(ax2, xi, ci, xa, ca, color=TEAL, lw=0.55, alpha=0.4)   # token mixing (attention)
cf = column(ax2, xf, 8, 3.2, 1.0, fc=AFILL, ec=AMBER)
connect(ax2, xa, ca, xf, cf, lw=0.4, alpha=0.45)
co = column(ax2, xo, 6, 3.0, 1.2)
connect(ax2, xf, cf, xo, co, lw=0.4, alpha=0.45)

ax2.text(xi, 0.55, "768 (in)", ha="center", fontsize=9.5, color="#555")
ax2.text(xa, 0.55, "attn out 768", ha="center", fontsize=9.5, color=TEAL)
ax2.text(xf, 0.4, "3072 · GELU", ha="center", fontsize=9.5, color=AMBER)
ax2.text(xo, 0.55, "768 (out)", ha="center", fontsize=9.5, color="#555")
ax2.text((xi + xa) / 2, 3.25, "self-attention\nsoftmax(QKᵀ⁄√64)·V · 12 heads\n+ Add & LayerNorm",
         ha="center", fontsize=8.6, color="#444")
ax2.text((xa + xf) / 2 + 0.1, 3.25, "feed-forward", ha="center", fontsize=8.6, color="#444")
ax2.text((xf + xo) / 2, 3.25, "+ Add & LayerNorm", ha="center", fontsize=8.6, color="#444")

fig.savefig("/tmp/nn_fullstack.png", dpi=155, facecolor="white", bbox_inches="tight")
print("saved")
