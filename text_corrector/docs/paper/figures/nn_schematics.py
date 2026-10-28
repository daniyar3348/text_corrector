import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
import numpy as np

BLUE, FILL = "#2f5d8a", "#dceafe"
GREEN, GFILL = "#3b6d2b", "#cfe8bf"
RED, RFILL = "#a83f25", "#f4d3c8"
AMBER, AFILL = "#9a6a12", "#fbeecb"
EDGE = "#b7c0ca"
TEAL = "#2c8a8a"
plt.rcParams.update({"font.family": "serif", "font.size": 11})


def neuron(ax, x, y, r=0.15, fc=FILL, ec=BLUE):
    ax.add_patch(Circle((x, y), r, facecolor=fc, edgecolor=ec, lw=1.5, zorder=4))


def vdots(ax, x, y):
    for dy in (-0.11, 0, 0.11):
        ax.add_patch(Circle((x, y + dy), 0.022, facecolor="#555", edgecolor="none", zorder=4))


def connect(ax, x1, ys1, x2, ys2, color=EDGE, lw=0.5, alpha=0.55):
    for a in ys1:
        for b in ys2:
            ax.plot([x1, x2], [a, b], color=color, lw=lw, alpha=alpha, zorder=1)


def setup(ax, title):
    ax.set_xlim(0, 4); ax.set_ylim(0, 3.1); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=6)


fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2))
fig.suptitle("KazRoBERTa detector — neuron-level schematics  "
             "(6 layers · 12 heads · hidden 768 · FFN 3072)",
             fontsize=15, fontweight="bold", y=0.985)

# ── A. Embedding (per sub-token) ──────────────────────────────────────────────
ax = axes[0, 0]; setup(ax, "A · Token embedding  (per sub-token)")
ax.add_patch(FancyBboxPatch((0.25, 1.3), 1.0, 0.5, boxstyle="round,pad=0.06",
                            fc="#eceff4", ec="#888", lw=1.3, zorder=3))
ax.text(0.75, 1.55, "sub-token", ha="center", va="center", fontsize=10)
ax.add_patch(FancyArrowPatch((1.32, 1.55), (1.95, 1.55), arrowstyle="-|>",
                             mutation_scale=13, lw=1.3, color="#555", zorder=2))
ys = np.linspace(2.55, 0.95, 5)
for y in ys:
    neuron(ax, 2.35, y)
vdots(ax, 2.35, 0.62)
ax.text(2.95, 1.75, "embedding\n∈ ℝ⁷⁶⁸", ha="left", va="center", fontsize=10.5)
ax.text(2.35, 0.2, "word + position + type\n→ LayerNorm", ha="center", va="center",
        fontsize=8.5, color="#555")

# ── B. Multi-head self-attention ──────────────────────────────────────────────
ax = axes[0, 1]; setup(ax, "B · Self-attention  (1 of 12 heads)")
ysl = np.linspace(2.5, 1.0, 5)
for y in ysl:
    neuron(ax, 0.85, y, fc="#dfe6ef")
vdots(ax, 0.85, 0.7)
ysr = np.linspace(2.5, 1.0, 5)
connect(ax, 0.85, ysl, 3.15, ysr, color=TEAL, lw=0.7, alpha=0.45)
for y in ysr:
    neuron(ax, 3.15, y, fc="#d7ece9", ec=TEAL)
vdots(ax, 3.15, 0.7)
ax.text(0.85, 0.32, "tokens (input)", ha="center", fontsize=9, color="#555")
ax.text(3.15, 0.32, "context out", ha="center", fontsize=9, color="#555")
ax.text(2.0, 2.92, "softmax(Q·Kᵀ ⁄ √64)·V", ha="center", fontsize=10)
ax.text(2.0, 0.05, "Q,K,V = X·W  (768→768) · 12 heads × 64", ha="center",
        fontsize=8.5, color="#555")

# ── C. Feed-forward (position-wise) ──────────────────────────────────────────
ax = axes[1, 0]; setup(ax, "C · Feed-forward + Add & LayerNorm")
y1 = np.linspace(2.5, 0.9, 6); y2 = np.linspace(2.7, 0.7, 8); y3 = np.linspace(2.5, 0.9, 6)
connect(ax, 0.7, y1, 2.0, y2, lw=0.45, alpha=0.5)
connect(ax, 2.0, y2, 3.3, y3, lw=0.45, alpha=0.5)
for y in y1: neuron(ax, 0.7, y)
for y in y2: neuron(ax, 2.0, y, fc=AFILL, ec=AMBER)
for y in y3: neuron(ax, 3.3, y)
vdots(ax, 0.7, 0.6); vdots(ax, 2.0, 0.4); vdots(ax, 3.3, 0.6)
ax.text(0.7, 0.2, "768", ha="center", fontsize=9.5, color="#555")
ax.text(2.0, 0.05, "3072 · GELU", ha="center", fontsize=9.5, color=AMBER)
ax.text(3.3, 0.2, "768", ha="center", fontsize=9.5, color="#555")

# ── D. Token-classification head ─────────────────────────────────────────────
ax = axes[1, 1]; setup(ax, "D · Token-classification head  (per token)")
yh = np.linspace(2.5, 0.9, 6)
ke, er = 1.85, 1.05
connect(ax, 1.05, yh, 3.0, [ke, er], lw=0.6, alpha=0.6)
for y in yh: neuron(ax, 1.05, y)
vdots(ax, 1.05, 0.6)
neuron(ax, 3.0, ke, r=0.2, fc=GFILL, ec=GREEN)
neuron(ax, 3.0, er, r=0.2, fc=RFILL, ec=RED)
ax.text(3.32, ke, "KEEP", ha="left", va="center", fontsize=10.5, color=GREEN, fontweight="bold")
ax.text(3.32, er, "ERROR", ha="left", va="center", fontsize=10.5, color=RED, fontweight="bold")
ax.text(1.05, 0.2, "hidden 768", ha="center", fontsize=9.5, color="#555")
ax.text(2.0, 2.92, "P(yᵢ) = softmax(W_c · hᵢ)", ha="center", fontsize=10)

fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("/tmp/nn_schematics.png", dpi=160, facecolor="white", bbox_inches="tight")
print("saved")
