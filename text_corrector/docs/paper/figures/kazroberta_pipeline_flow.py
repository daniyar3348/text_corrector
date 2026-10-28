import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({"font.family": "DejaVu Sans"})

FILL, BORDER, TXT = "#e9f2fb", "#2f6cae", "#1f3a5f"
SUB_FILL, SUB_BD = "#cfe4f7", "#2f6cae"
HL_FILL, HL_BD = "#fdeecb", "#e0a52a"
ARR = "#2c4a66"

fig, ax = plt.subplots(figsize=(15, 13.6))
ax.set_xlim(0, 15.6); ax.set_ylim(0, 14.4); ax.axis("off"); ax.invert_yaxis()

LCX, LW = 2.15, 3.7
RCX, RW = 10.85, 9.0
LX, RX = LCX - LW / 2, RCX - RW / 2


def box(cx, cy, w, h, fill=FILL, bd=BORDER, lw=2.0):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, facecolor=fill,
                           edgecolor=bd, linewidth=lw, zorder=2))


def sub(cx, cy, w, h, text, fill=SUB_FILL, bd=SUB_BD, fs=11):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                facecolor=fill, edgecolor=bd, linewidth=1.8, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=TXT, zorder=4)


def txt(cx, y, s, fs=11, bold=False, color=TXT, ha="center"):
    ax.text(cx, y, s, ha=ha, va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=color, zorder=4)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=22, lw=2.4, color=ARR, zorder=1))


# row geometry: (center_y, height)
R = {1: (1.2, 1.05), 2: (4.25, 3.7), 3: (7.65, 1.9),
     4: (10.5, 2.5), 5: (13.4, 1.25)}

# ── Row 1 — input ────────────────────────────────────────────────────────────
cy, h = R[1]
box(LCX, cy, LW, h); txt(LCX, cy, "Input Text", 16, True)
box(RCX, cy, RW, h)
txt(RCX, cy - 0.18, "Original (ka2ru typos):", 13, True)
txt(RCX, cy + 0.22, "«Бул маселе оте манызды болып тур»", 14)

# ── Row 2 — tokenization & encoding ──────────────────────────────────────────
cy, h = R[2]
box(LCX, cy, LW, h)
txt(LCX, cy - h / 2 + 0.45, "Tokenization\n& Encoding", 15, True)
sub(LCX, cy - 0.25, 3.0, 0.7, "Byte-level BPE\nvocab 52 000")
sub(LCX, cy + 0.95, 3.0, 0.85, "KazRoBERTa encoder\n6 layers · 12 heads · 768",
    fill=HL_FILL, bd=HL_BD)
box(RCX, cy, RW, h)
txt(RCX, cy - h / 2 + 0.45, "Encoding (contextual)", 14, True)
txt(RCX, cy - 0.55, "Sub-tokens → token + position embeddings  (LayerNorm)", 12)
txt(RCX, cy + 0.15, "Self-attention  softmax(QKᵀ/√64)·V · 12 heads  +  FFN (GELU)", 12)
txt(RCX, cy + 0.75, "× 6 layers (residual)  →  contextual vector ∈ ℝ⁷⁶⁸ per token", 12)

# ── Row 3 — error detection ──────────────────────────────────────────────────
cy, h = R[3]
box(LCX, cy, LW, h)
txt(LCX, cy - 0.45, "Error Detection", 15, True)
sub(LCX, cy + 0.4, 3.1, 0.6, "Classifier head 768→2")
box(RCX, cy, RW, h)
txt(RCX, cy - h / 2 + 0.35, "Detection — KEEP / ERROR per token", 14, True)
txt(RCX, cy + 0.05, "Бұл=E  маселе=E  оте=E  манызды=E  болып=K  тур=E", 12)
txt(RCX, cy + 0.6, "→ flagged positions sent to the corrector", 12)

# ── Row 4 — correction ───────────────────────────────────────────────────────
cy, h = R[4]
box(LCX, cy, LW, h)
txt(LCX, cy - h / 2 + 0.35, "Correction Module", 15, True)
sub(LCX, cy - 0.45, 3.2, 0.55, "Inverse ka2ru / harmony", fs=10)
sub(LCX, cy + 0.2, 3.2, 0.55, "OSA edit-distance ≤ 2", fs=10)
sub(LCX, cy + 0.85, 3.2, 0.55, "Lexicon 174 100 forms", fill=HL_FILL, bd=HL_BD, fs=10)
box(RCX, cy, RW, h)
txt(RCX, cy - h / 2 + 0.35, "Candidate generation & selection", 14, True)
txt(RCX, cy - 0.35, "candidates = inverse subs ∪ OSA,  filtered ∈ lexicon", 12)
txt(RCX, cy + 0.25, "манызды → { маңызды, … } → pick by frequency / context", 12)
txt(RCX, cy + 0.8, "edits:  н→ң · у→ұ · а→ә · о→ө …", 12)

# ── Row 5 — output ───────────────────────────────────────────────────────────
cy, h = R[5]
box(LCX, cy, LW, h)
txt(LCX, cy, "Output\n(Reconstruction)", 15, True)
box(RCX, cy, RW, h)
txt(RCX, cy - 0.2, "Final text:", 13, True)
txt(RCX, cy + 0.22, "«Бұл мәселе өте маңызды болып тұр»", 14, color="#2c6e2c")

# ── arrows ───────────────────────────────────────────────────────────────────
for a, b in [(1, 2), (2, 3), (3, 4), (4, 5)]:
    ya = R[a][0] + R[a][1] / 2; yb = R[b][0] - R[b][1] / 2
    arrow(LCX, ya, LCX, yb); arrow(RCX, ya, RCX, yb)
for r in (2, 3, 4, 5):
    cy = R[r][0]
    arrow(LX + LW, cy, RX, cy)

ax.set_title("KazRoBERTa  —  Kazakh spelling-correction pipeline (detect → correct)",
             fontsize=17, fontweight="bold", color="#15324f", pad=14)
fig.savefig("/tmp/kazroberta_flow.png", dpi=130, facecolor="white", bbox_inches="tight")
print("saved")
