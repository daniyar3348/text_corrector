import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({"font.family": "DejaVu Sans"})

FILL, BORDER, TXT = "#e9f2fb", "#2f6cae", "#1f3a5f"
SUB_FILL, SUB_BD = "#cfe4f7", "#2f6cae"
HL_FILL, HL_BD = "#fdeecb", "#e0a52a"
NEW_FILL, NEW_BD, NEW_TX = "#e7f6ea", "#2c7a3f", "#1d5e2c"
GHL_FILL, GHL_BD = "#cdeccf", "#2c7a3f"
ARR = "#2c4a66"

fig, ax = plt.subplots(figsize=(15, 15.8))
ax.set_xlim(0, 15.6); ax.set_ylim(0, 16.6); ax.axis("off"); ax.invert_yaxis()

LCX, LW = 2.2, 3.8
RCX, RW = 10.9, 9.0
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


def arrow(x1, y1, x2, y2, color=ARR):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=22, lw=2.4, color=color, zorder=1))


# (center_y, height)
R = {1: (1.05, 1.0), 2: (3.6, 3.4), 3: (6.7, 1.9),
     4: (9.5, 2.4), 5: (12.55, 2.7), 6: (15.2, 1.25)}

# 1 — input
cy, h = R[1]
box(LCX, cy, LW, h); txt(LCX, cy, "Input Text", 16, True)
box(RCX, cy, RW, h)
txt(RCX, cy - 0.18, "Original (ka2ru typos):", 13, True)
txt(RCX, cy + 0.22, "«Бул маселе оте манызды болып тур»", 14)

# 2 — tokenization & encoding
cy, h = R[2]
box(LCX, cy, LW, h)
txt(LCX, cy - h / 2 + 0.42, "Tokenization\n& Encoding", 15, True)
sub(LCX, cy - 0.2, 3.1, 0.7, "Byte-level BPE\nvocab 52 000")
sub(LCX, cy + 1.0, 3.1, 0.85, "KazRoBERTa encoder\n6 layers · 12 heads · 768",
    fill=HL_FILL, bd=HL_BD)
box(RCX, cy, RW, h)
txt(RCX, cy - h / 2 + 0.42, "Encoding (contextual)", 14, True)
txt(RCX, cy - 0.5, "Sub-tokens → token + position embeddings  (LayerNorm)", 12)
txt(RCX, cy + 0.2, "Self-attention  softmax(QKᵀ/√64)·V · 12 heads  +  FFN (GELU)", 12)
txt(RCX, cy + 0.8, "× 6 layers (residual)  →  contextual vector ∈ ℝ⁷⁶⁸ per token", 12)

# 3 — error detection (pass 1)
cy, h = R[3]
box(LCX, cy, LW, h)
txt(LCX, cy - 0.5, "Error Detection", 15, True)
txt(LCX, cy - 0.05, "pass 1 · cls head", 10, color="#5a6b80")
sub(LCX, cy + 0.5, 3.2, 0.55, "Classifier head 768→2")
box(RCX, cy, RW, h)
txt(RCX, cy - h / 2 + 0.34, "Detection — KEEP / ERROR per token", 14, True)
txt(RCX, cy + 0.05, "Бұл=E   маселе=E   оте=E   манызды=E   болып=K   тур=E", 12)
txt(RCX, cy + 0.6, "→ flagged positions sent to the corrector", 12)

# 4 — candidate generation (symbolic)
cy, h = R[4]
box(LCX, cy, LW, h)
txt(LCX, cy - h / 2 + 0.32, "Candidate Generation", 14, True)
sub(LCX, cy - 0.5, 3.3, 0.52, "Inverse ka2ru / harmony", fs=10)
sub(LCX, cy + 0.13, 3.3, 0.52, "OSA edit-distance ≤ 2", fs=10)
sub(LCX, cy + 0.76, 3.3, 0.52, "Lexicon 174 100 forms", fill=HL_FILL, bd=HL_BD, fs=10)
box(RCX, cy, RW, h)
txt(RCX, cy - h / 2 + 0.32, "Candidate set  C(wᵢ)", 14, True)
txt(RCX, cy - 0.3, "C(wᵢ) = inverse subs  ∪  OSA,   filtered ∈ lexicon", 12)
txt(RCX, cy + 0.3, "манызды → { маңызды, маңыз, манызда, … }", 12)
txt(RCX, cy + 0.85, "edits:  н→ң · у→ұ · а→ә · о→ө …", 12)

# 5 — contextual re-ranking (NEW / refined model)
cy, h = R[5]
box(LCX, cy, LW, h, fill=NEW_FILL, bd=NEW_BD, lw=2.6)
txt(LCX, cy - h / 2 + 0.3, "★ NEW · refined model", 10.5, True, color=NEW_TX)
txt(LCX, cy - h / 2 + 0.72, "Contextual Re-ranking", 14, True, color=NEW_TX)
txt(LCX, cy - h / 2 + 1.06, "pass 2 · MLM head", 10, color="#3a6a45")
sub(LCX, cy + 0.78, 3.3, 0.78, "KazRoBERTa MLM head\n(same weights)",
    fill=GHL_FILL, bd=GHL_BD, fs=10.5)
box(RCX, cy, RW, h, fill=NEW_FILL, bd=NEW_BD, lw=2.6)
txt(RCX, cy - h / 2 + 0.34, "Re-rank candidates in context  →  pick best", 14, True, color=NEW_TX)
txt(RCX, cy - 0.35, "s(c) = α·log P_MLM(c | context) + β·(−d(c,wᵢ)) + γ·log f(c)", 12.5, color=TXT)
txt(RCX, cy + 0.3, "ĉ = argmax s(c),   c ∈ C(wᵢ)", 12.5, color=TXT)
txt(RCX, cy + 0.88, "↻ reuses the KazRoBERTa encoder from step 2 (2nd pass)", 11, color="#3a6a45")

# 6 — output
cy, h = R[6]
box(LCX, cy, LW, h)
txt(LCX, cy, "Output\n(Reconstruction)", 15, True)
box(RCX, cy, RW, h)
txt(RCX, cy - 0.2, "Final text:", 13, True)
txt(RCX, cy + 0.22, "«Бұл мәселе өте маңызды болып тұр»", 14, color="#2c6e2c")

# arrows
for a, b in [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]:
    ya = R[a][0] + R[a][1] / 2; yb = R[b][0] - R[b][1] / 2
    c = NEW_BD if b == 5 else ARR
    arrow(LCX, ya, LCX, yb, c); arrow(RCX, ya, RCX, yb, c)
for r in (2, 3, 4, 5, 6):
    cy = R[r][0]
    arrow(LX + LW, cy, RX, cy, NEW_BD if r == 5 else ARR)

ax.set_title("KazRoBERTa  —  refined spelling-correction model  (detect → generate → context re-rank)",
             fontsize=17, fontweight="bold", color="#15324f", pad=14)
fig.savefig("/tmp/kazroberta_flow2.png", dpi=130, facecolor="white", bbox_inches="tight")
print("saved")
