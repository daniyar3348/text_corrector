import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.gridspec import GridSpec
import numpy as np

BLUE, FILL = "#2f5d8a", "#dceafe"
GREEN, GFILL = "#3b6d2b", "#cfe8bf"
RED, RFILL = "#a83f25", "#f4d3c8"
AMBER, AFILL = "#9a6a12", "#fbeecb"
GREY, GYFILL = "#6a6a6a", "#e3e3df"
EDGE, TEAL = "#bcc5cf", "#2c8a8a"
plt.rcParams.update({"font.family": "serif", "font.size": 11})


def neuron(ax, x, y, r=0.12, fc=FILL, ec=BLUE):
    ax.add_patch(Circle((x, y), r, facecolor=fc, edgecolor=ec, lw=1.2, zorder=4))


def vdots(ax, x, y):
    for dy in (-0.09, 0, 0.09):
        ax.add_patch(Circle((x, y + dy), 0.018, facecolor="#555", edgecolor="none", zorder=4))


def column(ax, x, n, ytop, ybot, fc=FILL, ec=BLUE, dots=True):
    ys = np.linspace(ytop, ybot, n)
    for y in ys:
        neuron(ax, x, y, fc=fc, ec=ec)
    if dots:
        vdots(ax, x, ybot - 0.32)
    return ys


def connect(ax, x1, ys1, x2, ys2, color=EDGE, lw=0.4, alpha=0.5):
    for a in ys1:
        for b in ys2:
            ax.plot([x1, x2], [a, b], color=color, lw=lw, alpha=alpha, zorder=1)


def bracket(ax, x1, x2, y, text):
    ax.plot([x1, x2], [y, y], color="#555", lw=1.2)
    ax.plot([x1, x1], [y, y - 0.1], color="#555", lw=1.2)
    ax.plot([x2, x2], [y, y - 0.1], color="#555", lw=1.2)
    ax.text((x1 + x2) / 2, y + 0.1, text, ha="center", va="bottom", fontsize=11,
            fontweight="bold", color="#333")


fig = plt.figure(figsize=(16.5, 11.2))
fig.suptitle("KazRoBERTa  (RobertaForTokenClassification)  —  full stack with module structure & details",
             fontsize=15.5, fontweight="bold", y=0.99)
gs = GridSpec(2, 2, height_ratios=[1.0, 1.12], width_ratios=[1.32, 1.0],
              hspace=0.16, wspace=0.06)

# ── TOP: full forward stack (full width) ─────────────────────────────────────
ax = fig.add_subplot(gs[0, :]); ax.set_xlim(-0.6, 9.7); ax.set_ylim(0.3, 4.6)
ax.set_aspect("equal"); ax.axis("off")
x_tok, x_emb = 0.0, 1.25
x_layers = [2.55, 3.45, 4.35, 5.25, 6.15, 7.05]
x_out = 8.55
tok = column(ax, x_tok, 5, 3.2, 1.7, fc=GYFILL, ec=GREY)
emb = column(ax, x_emb, 6, 3.35, 1.55)
connect(ax, x_tok, tok, x_emb, emb)
prev, prev_x = emb, x_emb
for xl in x_layers:
    cur = column(ax, xl, 6, 3.35, 1.55)
    connect(ax, prev_x, prev, xl, cur)
    prev, prev_x = cur, xl
connect(ax, x_layers[-1], prev, x_out, [2.55, 1.75])
neuron(ax, x_out, 2.55, r=0.17, fc=GFILL, ec=GREEN)
neuron(ax, x_out, 1.75, r=0.17, fc=RFILL, ec=RED)
ax.text(x_out + 0.26, 2.55, "KEEP", ha="left", va="center", color=GREEN, fontweight="bold", fontsize=10.5)
ax.text(x_out + 0.26, 1.75, "ERROR", ha="left", va="center", color=RED, fontweight="bold", fontsize=10.5)
bracket(ax, x_layers[0] - 0.3, x_layers[-1] + 0.3, 3.95,
        "× 6  RobertaLayer  (self-attention + FFN, residual)   —   6 × 7.09M = 42.5M")
ax.text(x_tok, 1.2, "L tokens", ha="center", fontsize=9, color="#555")
ax.text(x_emb, 1.0, "embed 768\n40.3M (49%)", ha="center", fontsize=8.6, color="#555")
for i, xl in enumerate(x_layers, 1):
    ax.text(xl, 1.05, f"L{i}", ha="center", fontsize=9, color="#555")
ax.text(x_out, 1.15, "768→2\nper token", ha="center", fontsize=8.6, color="#555")

# ── BOTTOM-LEFT: one RobertaLayer expanded (neuron level + module names) ──────
ax2 = fig.add_subplot(gs[1, 0]); ax2.set_xlim(-0.3, 9.9); ax2.set_ylim(0.0, 4.2)
ax2.set_aspect("equal"); ax2.axis("off")
ax2.text(4.8, 4.0, "one RobertaLayer, expanded (neuron level)", ha="center",
         fontsize=12, fontweight="bold", color="#333")
xi, xa, xf, xo = 0.7, 3.0, 5.6, 8.1
ci = column(ax2, xi, 6, 3.1, 1.3)
ca = column(ax2, xa, 6, 3.1, 1.3, fc="#d7ece9", ec=TEAL)
connect(ax2, xi, ci, xa, ca, color=TEAL, lw=0.5, alpha=0.4)
cf = column(ax2, xf, 8, 3.3, 1.1, fc=AFILL, ec=AMBER)
connect(ax2, xa, ca, xf, cf, lw=0.38, alpha=0.45)
co = column(ax2, xo, 6, 3.1, 1.3)
connect(ax2, xf, cf, xo, co, lw=0.38, alpha=0.45)
ax2.text(xi, 0.65, "768 (in)", ha="center", fontsize=9, color="#555")
ax2.text(xa, 0.65, "attn out 768", ha="center", fontsize=9, color=TEAL)
ax2.text(xf, 0.5, "3072 · GELU", ha="center", fontsize=9, color=AMBER)
ax2.text(xo, 0.65, "768 (out)", ha="center", fontsize=9, color="#555")
ax2.text((xi + xa) / 2, 3.55, "attention.self : Q,K,V 768→768 (1.77M)\nsoftmax(QKᵀ⁄√64)·V · 12h×64 · drop 0.1\n+ attention.output 768→768 +LN (0.59M)",
         ha="center", fontsize=7.8, color="#444")
ax2.text((xa + xf) / 2 + 0.1, 3.62, "intermediate\n768→3072 · GELU\n(2.36M)", ha="center", fontsize=7.8, color="#444")
ax2.text((xf + xo) / 2, 3.62, "output\n3072→768 +LN\n(2.36M) · drop 0.1", ha="center", fontsize=7.8, color="#444")

# ── BOTTOM-RIGHT: exact structure tree ───────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 1]); ax3.axis("off"); ax3.set_xlim(0, 1); ax3.set_ylim(0, 1)
ax3.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.01",
                             transform=ax3.transAxes, fc="#fbfbf9", ec="#cccccc", lw=1.2))
spec = (
"RobertaForTokenClassification     82.86M\n"
"│\n"
"├─ roberta.embeddings             40.33M  (49%)\n"
"│    word_embeddings   52000×768   39.94M\n"
"│    position_embeddings 514×768    0.39M  abs.\n"
"│    token_type_embeddings 1×768      768\n"
"│    LayerNorm(1e-12) + Dropout(0.1)\n"
"│\n"
"├─ roberta.encoder.layer × 6      42.53M\n"
"│    each RobertaLayer ............ 7.09M\n"
"│    ├ attention.self  QKV 768→768  1.77M\n"
"│    │     12 heads × 64 · drop 0.1\n"
"│    ├ attention.output 768→768     0.59M\n"
"│    │     + LayerNorm + Drop 0.1  (res.)\n"
"│    ├ intermediate    768→3072     2.36M\n"
"│    │     GELU\n"
"│    └ output          3072→768     2.36M\n"
"│          + LayerNorm + Drop 0.1  (res.)\n"
"│\n"
"└─ classifier          768→2        1.5k\n"
"     Dropout(0.1) → per-token logits\n"
"\n"
"hidden 768 · heads 12 (d=64) · FFN 3072\n"
"vocab 52000 · max_pos 514 · pad 1 · eps 1e-12"
)
ax3.text(0.06, 0.95, "Module structure  (real, from checkpoint)", fontsize=10.5,
         fontweight="bold", va="top", family="serif", color="#222")
ax3.text(0.06, 0.88, spec, fontsize=9.0, va="top", family="monospace", color="#222",
         linespacing=1.32)

fig.savefig("/tmp/nn_kazroberta.png", dpi=150, facecolor="white", bbox_inches="tight")
print("saved")
