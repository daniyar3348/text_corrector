import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import numpy as np

BLUE, FILL = "#2f5d8a", "#dceafe"
GREEN, GFILL = "#3b6d2b", "#cfe8bf"
RED, RFILL = "#a83f25", "#f4d3c8"
AMBER, AFILL = "#9a6a12", "#fbeecb"
GREY, GYFILL = "#6a6a6a", "#e3e3df"
EDGE, TEAL = "#c2cad3", "#2c8a8a"
plt.rcParams.update({"font.family": "serif", "font.size": 11})

fig, ax = plt.subplots(figsize=(18, 12.2))
ax.set_xlim(0, 17); ax.set_ylim(0, 11.7); ax.set_aspect("equal"); ax.axis("off")


def neuron(x, y, r=0.12, fc=FILL, ec=BLUE):
    ax.add_patch(Circle((x, y), r, facecolor=fc, edgecolor=ec, lw=1.2, zorder=4))


def vdots(x, y):
    for dy in (-0.09, 0, 0.09):
        ax.add_patch(Circle((x, y + dy), 0.018, facecolor="#555", edgecolor="none", zorder=4))


def column(x, n, ytop, ybot, fc=FILL, ec=BLUE, dots=True):
    ys = np.linspace(ytop, ybot, n)
    for y in ys:
        neuron(x, y, fc=fc, ec=ec)
    if dots:
        vdots(x, ybot - 0.3)
    return ys


def connect(x1, ys1, x2, ys2, color=EDGE, lw=0.4, alpha=0.5):
    for a in ys1:
        for b in ys2:
            ax.plot([x1, x2], [a, b], color=color, lw=lw, alpha=alpha, zorder=1)


def bracket(x1, x2, y, text):
    ax.plot([x1, x2], [y, y], color="#555", lw=1.2)
    for xx in (x1, x2):
        ax.plot([xx, xx], [y, y - 0.1], color="#555", lw=1.2)
    ax.text((x1 + x2) / 2, y + 0.08, text, ha="center", va="bottom", fontsize=11,
            fontweight="bold", color="#333")


ax.text(8.5, 11.45, "KazRoBERTa  ·  RobertaForTokenClassification  —  full architecture  (82.86M params)",
        ha="center", fontsize=16, fontweight="bold", color="#1a1a1a")

# ── A. full forward stack (top) ──────────────────────────────────────────────
tok_x, emb_x = 0.6, 2.0
xL = [3.4, 4.4, 5.4, 6.4, 7.4, 8.4]
head_x = 10.0
tok = column(tok_x, 5, 10.1, 8.9, fc=GYFILL, ec=GREY)
emb = column(emb_x, 6, 10.3, 8.7)
connect(tok_x, tok, emb_x, emb)
prev, px = emb, emb_x
for xl in xL:
    cur = column(xl, 6, 10.3, 8.7)
    connect(px, prev, xl, cur)
    prev, px = cur, xl
connect(xL[-1], prev, head_x, [9.8, 9.0])
neuron(head_x, 9.8, r=0.17, fc=GFILL, ec=GREEN)
neuron(head_x, 9.0, r=0.17, fc=RFILL, ec=RED)
ax.text(head_x + 0.27, 9.8, "KEEP", ha="left", va="center", color=GREEN, fontweight="bold", fontsize=10.5)
ax.text(head_x + 0.27, 9.0, "ERROR", ha="left", va="center", color=RED, fontweight="bold", fontsize=10.5)
bracket(xL[0] - 0.3, xL[-1] + 0.3, 10.78,
        "× 6  RobertaLayer  (self-attention + FFN, residual)   ·   6 × 7.09M = 42.5M")
ax.text(tok_x, 8.5, "L tokens", ha="center", fontsize=9, color="#555")
ax.text(emb_x, 8.35, "embed 768\n40.3M (49%)", ha="center", fontsize=8.4, color="#555")
for i, xl in enumerate(xL, 1):
    ax.text(xl, 8.45, f"L{i}", ha="center", fontsize=9, color="#555")
ax.text(head_x, 8.5, "768→2 · per token", ha="center", fontsize=8.4, color="#555")

# ── B. zoom funnel from the stack to the expanded layer ──────────────────────
for (sx, ex) in [(3.1, 1.2), (8.7, 10.0)]:
    ax.add_patch(FancyArrowPatch((sx, 8.25), (ex, 7.35), arrowstyle="-", lw=1.1,
                                 color="#999", linestyle=(0, (5, 4)), zorder=1))
ax.text(5.9, 7.95, "one RobertaLayer, expanded  ↓", ha="center", fontsize=11,
        fontweight="bold", color="#333")

# ── C. expanded RobertaLayer (neuron level + module names) ───────────────────
xi, xa, xf, xo = 1.5, 4.2, 7.0, 9.5
ci = column(xi, 6, 6.5, 4.3)
ca = column(xa, 6, 6.5, 4.3, fc="#d7ece9", ec=TEAL)
connect(xi, ci, xa, ca, color=TEAL, lw=0.5, alpha=0.4)
cf = column(xf, 8, 6.7, 4.1, fc=AFILL, ec=AMBER)
connect(xa, ca, xf, cf, lw=0.38, alpha=0.45)
co = column(xo, 6, 6.5, 4.3)
connect(xf, cf, xo, co, lw=0.38, alpha=0.45)
ax.text(xi, 3.75, "768 (in)", ha="center", fontsize=9, color="#555")
ax.text(xa, 3.75, "attn out 768", ha="center", fontsize=9, color=TEAL)
ax.text(xf, 3.55, "3072 · GELU", ha="center", fontsize=9, color=AMBER)
ax.text(xo, 3.75, "768 (out)", ha="center", fontsize=9, color="#555")
ax.text((xi + xa) / 2, 7.0, "attention.self : Q,K,V 768→768 (1.77M)\n"
        "softmax(QKᵀ⁄√64)·V · 12 heads×64 · drop 0.1\n+ attention.output 768→768 +LN (0.59M)",
        ha="center", fontsize=8, color="#444")
ax.text((xa + xf) / 2 + 0.1, 7.05, "intermediate\n768→3072 · GELU\n(2.36M)", ha="center", fontsize=8, color="#444")
ax.text((xf + xo) / 2, 7.05, "output\n3072→768 +LN\n(2.36M) · drop 0.1", ha="center", fontsize=8, color="#444")

# ── D. exact module-structure tree (right column, same canvas) ───────────────
ax.add_patch(FancyBboxPatch((11.05, 0.45), 5.8, 9.6, boxstyle="round,pad=0.05",
                            fc="#fbfbf9", ec="#cccccc", lw=1.3, zorder=2))
ax.text(11.35, 9.7, "Module structure  (real, from checkpoint)", fontsize=11,
        fontweight="bold", va="top", color="#222", zorder=3)
spec = (
"RobertaForTokenClassification     82.86M\n"
"│\n"
"├─ roberta.embeddings             40.33M  (49%)\n"
"│    word_embeddings   52000×768   39.94M\n"
"│    position_embeddings 514×768    0.39M  abs.\n"
"│    token_type_embeddings 1×768      768\n"
"│    LayerNorm(eps=1e-12) + Dropout(0.1)\n"
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
"     Dropout(0.1) → per-token logits {KEEP,ERROR}\n"
"\n"
"hidden 768 · heads 12 (d=64) · FFN 3072\n"
"vocab 52000 · max_pos 514 · pad 1 · eps 1e-12\n"
"position embeddings: absolute"
)
ax.text(11.35, 9.25, spec, fontsize=9.0, va="top", family="monospace", color="#222",
        linespacing=1.3, zorder=3)

fig.savefig("/tmp/nn_one.png", dpi=140, facecolor="white", bbox_inches="tight")
print("saved")
