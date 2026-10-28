# Figures

This section specifies the five figures referenced in the paper. For each figure
we provide a number, a caption (the verbatim text to appear beneath the figure),
a description (intent and reading guidance, not printed), and ready-to-render
source code. All numeric values are taken from the verified experimental record;
the data arrays are embedded inline in each source listing so that every figure
is reproducible without external files. Detector and corrector metrics are
reported on the test set (an $8{,}000$-sentence subset where noted).

---

## Figure 1 — System architecture

**Caption.** Figure 1: Architecture of the Turan Text Corrector. An input
sentence is first classified by a language router; Russian input is passed
through unchanged (deliberate no-op), while Kazakh input — including
special-letter-stripped Kazakh recovered by the russified-lexicon signal — is
sent to the two-stage correction pipeline. A KazRoBERTa token-classification
detector labels each token KEEP/ERROR; flagged tokens are passed to the
corrector, which generates candidates by inverse look-alike substitution and an
Optimal String Alignment (OSA) edit-distance search over the Kazakh lexicon. A
morphological guard validates stem+suffix segmentation and vowel harmony before
the corrected sentence is emitted.

**Description.** A left-to-right (or top-to-bottom) block diagram drawn in TikZ.
It expresses the control flow `input → language router → {Russian no-op |
Kazakh pipeline}`, where the Kazakh pipeline is `detector → corrector →
morphology guard → output`. The detector block is annotated with its backbone
(KazRoBERTa, `kz-transformers/kaz-roberta-conversational`) and its two-label
token-classification head; the corrector block lists its candidate sources
(inverse ka2ru/harmony substitution filtered by the lexicon, and OSA fallback)
and the frequency tie-break. The russified-lexicon routing signal is shown as a
side annotation on the router to make explicit the failure mode that motivates
it. This diagram mirrors, in static print form, the live React component
`frontend/src/components/NeuralNetDiagram.tsx`, which renders the detailed
KazRoBERTa encoder stack; the print figure abstracts that encoder into a single
detector block and instead foregrounds the end-to-end pipeline. The architecture
of the encoder (byte-level BPE vocabulary $\approx 52{,}000$; transformer layers,
attention heads, and hidden size) is reported per the project worklog [TODO:
verify layer/head/hidden counts from `models/kazakh_detector/config.json`]; we
therefore omit precise per-layer counts from the printed caption and label the
block simply as the KazRoBERTa encoder [liu2019roberta, sagyndyk2025kazroberta].

**Source (TikZ / LaTeX).**

```latex
% Requires: \usepackage{tikz}\usetikzlibrary{arrows.meta,positioning,fit,backgrounds}
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  font=\small,
  >={Stealth[length=2.4mm]},
  node distance=7mm,
  block/.style={rectangle, rounded corners=3pt, draw, thick,
                align=center, minimum height=10mm, inner sep=4pt, text width=34mm},
  io/.style={block, fill=blue!6, draw=blue!60},
  router/.style={block, fill=cyan!8, draw=cyan!60, text width=34mm},
  detect/.style={block, fill=violet!8, draw=violet!60},
  correct/.style={block, fill=indigo!8, draw=indigo!60},
  morph/.style={block, fill=green!8, draw=green!55},
  out/.style={block, fill=teal!10, draw=teal!60},
  note/.style={align=left, font=\scriptsize\itshape, text=black!55, text width=42mm},
  flow/.style={->, thick, draw=black!55},
]

% --- nodes ---
\node[io]      (input)  {Input sentence\\ \scriptsize Cyrillic, up to 5000 chars};
\node[router, below=of input] (router)
      {Language router\\ \scriptsize char + lexicon signals};
\node[out, right=22mm of router] (ru)
      {Russian path\\ \scriptsize deliberate no-op};
\node[detect, below=of router] (detector)
      {Error detector\\ \scriptsize KazRoBERTa token classifier\\ KEEP / ERROR per token};
\node[correct, below=of detector] (corrector)
      {Corrector\\ \scriptsize inverse ka2ru/harmony (lexicon-filtered)\\ + OSA edit-distance search, freq.\ tie-break};
\node[morph, below=of corrector] (morph)
      {Morphology guard\\ \scriptsize stem+suffix \& vowel-harmony check};
\node[out, below=of morph] (output) {Corrected sentence};

% --- side note: russified-lexicon routing signal ---
\node[note, left=8mm of router]
      {Russified-lexicon signal:\\ Kazakh lexicon mapped through\\
       ka2ru, Russian-stopword-excluded,\\ length-aware (recovers
       special-letter-stripped Kazakh)};

% --- edges ---
\draw[flow] (input)     -- (router);
\draw[flow] (router)    -- node[right, font=\scriptsize]{Kazakh} (detector);
\draw[flow] (router)    -- node[above, font=\scriptsize]{Russian} (ru);
\draw[flow] (detector)  -- node[right, font=\scriptsize]{flagged tokens} (corrector);
\draw[flow] (corrector) -- (morph);
\draw[flow] (morph)     -- (output);

% --- grouping box around the Kazakh two-stage pipeline ---
\begin{scope}[on background layer]
  \node[draw=indigo!40, dashed, rounded corners,
        fit=(detector)(corrector)(morph),
        inner sep=4mm, label={[indigo!70, font=\scriptsize\bfseries]north east:Two-stage Kazakh pipeline}] {};
\end{scope}
\end{tikzpicture}
\caption{Architecture of the Turan Text Corrector: language router feeding a
two-stage detect$\rightarrow$correct pipeline with a morphological guard.}
\label{fig:architecture}
\end{figure}
```

---

## Figure 2 — Error-type distribution

**Caption.** Figure 2: Realized distribution of the six injected error operations
across all edits in the synthetic dataset (from `meta.json`). The look-alike
ka2ru class is dominant at $30.5\%$, reflecting its sampling weight of $0.45$;
vowel-harmony violations follow at $21.3\%$. Percentages are of all injected
edits and sum to $100\%$.

**Description.** A single-series vertical bar chart with six bars, one per error
operation, ordered by descending realized share: ka2ru, harmony, swap, drop,
dup, sub. Values are the realized percentages of all injected edits; the ka2ru
bar is highlighted to emphasize the paper's novelty hook. Note that these are
the *realized* shares (the fraction of edits actually produced), which differ
from the sampling *weights* used by the generator; the chart reports the
realized shares because they describe the dataset as built.

**Source (matplotlib / Python).**

```python
import matplotlib.pyplot as plt

# Realized distribution of injected edits (meta.json), % of all edits.
ops    = ["ka2ru", "harmony", "swap", "drop", "dup", "sub"]
share  = [30.5,    21.34,     17.93,  11.91,  9.64,  8.68]   # percent
counts = [1157438, 809903,    680471, 451816, 366027, 329509]  # raw edit counts

colors = ["#4338ca" if op == "ka2ru" else "#9aa6e8" for op in ops]

fig, ax = plt.subplots(figsize=(6.4, 3.6))
bars = ax.bar(ops, share, color=colors, edgecolor="#2b3470", linewidth=0.6)

for b, v in zip(bars, share):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.1f}%",
            ha="center", va="bottom", fontsize=9)

ax.set_ylabel("Share of injected edits (%)")
ax.set_xlabel("Error operation")
ax.set_ylim(0, 34)
ax.set_title("Realized error-type distribution (synthetic dataset)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("fig2_error_distribution.pdf", bbox_inches="tight")
```

---

## Figure 3 — Detection: trained vs. baseline

**Caption.** Figure 3: Token-level error-detection performance on the test set.
The fine-tuned KazRoBERTa detector achieves $\mathrm{F1}=97.3\%$
($\mathrm{P}=97.1\%$, $\mathrm{R}=97.4\%$), substantially exceeding a
lexicon-membership heuristic baseline ($\mathrm{F1}=86.3\%$). Precision and
recall for the heuristic baseline were not recorded and are omitted.

**Description.** A grouped vertical bar chart comparing the trained detector
against the heuristic baseline (flag a word if it is absent from the lexicon)
across three metrics: Precision, Recall, and F1. Only F1 is available for the
heuristic baseline; its precision and recall bars are intentionally absent and
annotated as not recorded, rather than fabricated. The chart makes the
$11$-point F1 gap visually salient and supports the claim that detection is
essentially solved by the trained model.

**Source (matplotlib / Python).**

```python
import matplotlib.pyplot as plt
import numpy as np

metrics = ["Precision", "Recall", "F1"]
x = np.arange(len(metrics))
w = 0.38

# Trained KazRoBERTa detector (test set). Heuristic baseline: only F1 recorded.
trained   = [97.1, 97.4, 97.3]
baseline  = [None, None, 86.3]   # P/R not recorded for the heuristic baseline

fig, ax = plt.subplots(figsize=(6.0, 3.8))

b1 = ax.bar(x - w/2, trained, w, label="KazRoBERTa detector",
            color="#4338ca", edgecolor="#2b3470", linewidth=0.6)
# Plot only the available baseline value (F1).
base_vals = [v if v is not None else 0 for v in baseline]
b2 = ax.bar(x + w/2, base_vals, w, label="Heuristic baseline",
            color="#c0c7ef", edgecolor="#2b3470", linewidth=0.6)

for xi, v in zip(x - w/2, trained):
    ax.text(xi, v + 0.3, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
for xi, v in zip(x + w/2, baseline):
    if v is None:
        ax.text(xi, 1.5, "n/r", ha="center", va="bottom", fontsize=8,
                style="italic", color="#666")
    else:
        ax.text(xi, v + 0.3, f"{v:.1f}", ha="center", va="bottom", fontsize=9)

ax.set_xticks(x, metrics)
ax.set_ylabel("Score (%)")
ax.set_ylim(80, 100)
ax.set_title("Error detection: trained vs. heuristic baseline (test)")
ax.legend(frameon=False, loc="lower left")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("fig3_detection_pr_f1.pdf", bbox_inches="tight")
# Note: "n/r" = not recorded (heuristic baseline P/R were not saved).
```

---

## Figure 4 — End-to-end vs. oracle ceiling

**Caption.** Figure 4: Sentence-level end-to-end performance on the test set
(fraction of sentences fully corrected). The trained pipeline corrects $80.5\%$
of sentences, the heuristic baseline $64.6\%$, and the oracle configuration
(perfect detection) $83.5\%$. The trained pipeline lies within $\approx 3$
percentage points of the oracle ceiling, indicating that detection is largely
solved and the corrector is the remaining bottleneck.

**Description.** A single-series vertical bar chart with three bars: trained
pipeline, heuristic baseline, and oracle ceiling. A dashed horizontal reference
line at the oracle value ($83.5\%$) emphasizes the small gap between the trained
pipeline and the ceiling. The oracle bar uses a distinct (lighter, hatched)
style to mark it as an upper bound rather than an achieved system.

**Source (matplotlib / Python).**

```python
import matplotlib.pyplot as plt

# Sentence-level fully-corrected rate on the test set (%).
systems = ["Heuristic\nbaseline", "Trained\npipeline", "Oracle ceiling\n(perfect detect.)"]
values  = [64.6,                   80.5,                 83.5]

colors  = ["#c0c7ef", "#4338ca", "#9aa6e8"]
hatches = ["",        "",        "//"]

fig, ax = plt.subplots(figsize=(5.8, 3.8))
bars = ax.bar(systems, values, color=colors, edgecolor="#2b3470", linewidth=0.6)
for b, h in zip(bars, hatches):
    b.set_hatch(h)

for b, v in zip(bars, values):
    ax.text(b.get_x() + b.get_width()/2, v + 0.5, f"{v:.1f}%",
            ha="center", va="bottom", fontsize=9)

# Oracle ceiling reference line.
ax.axhline(83.5, color="#2b3470", linestyle="--", linewidth=1)
ax.text(2.42, 83.5 + 0.6, "oracle ceiling", ha="right", va="bottom",
        fontsize=8, style="italic", color="#2b3470")

ax.set_ylabel("Sentences fully corrected (%)")
ax.set_ylim(0, 95)
ax.set_title("End-to-end correction vs. oracle ceiling (test)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("fig4_e2e_vs_oracle.pdf", bbox_inches="tight")
```

---

## Figure 5 — Per-error-type corrector accuracy

**Caption.** Figure 5: Corrector accuracy by error type under oracle detection on
the test set (fraction of erroneous words correctly fixed). The corrector is
strongest on systematic substitution errors — ka2ru ($97.6\%$) and vowel-harmony
($97.9\%$) — and weakest on the information-losing deletion (drop, $62\%$) and
generic substitution (sub, $70\%$) operations, which lack a deterministic
inverse and would benefit from contextual or language-model re-ranking. The
overall fixed rate is $88\%$ at $91.6\%$ precision-of-changes.

**Description.** A single-series vertical bar chart with six bars, one per error
operation, ordered by descending corrector accuracy: harmony, ka2ru, dup, swap,
sub, drop. The two hard cases (drop and sub) are highlighted in a contrasting
warm color to make the bottleneck visually explicit, while the systematic
substitution classes (ka2ru, harmony) are shown in the cool palette consistent
with the other figures. A dashed reference line marks the $88\%$ overall fixed
rate for context.

**Source (matplotlib / Python).**

```python
import matplotlib.pyplot as plt

# Corrector accuracy by error type at ORACLE detection (test), % fixed.
ops = ["harmony", "ka2ru", "dup", "swap", "sub", "drop"]
acc = [97.9,      97.6,    93.0,  83.0,   70.0,  62.0]

# Highlight the hard cases (drop, sub) in a contrasting warm color.
hard   = {"drop", "sub"}
colors = ["#d97706" if op in hard else "#4338ca" for op in ops]

fig, ax = plt.subplots(figsize=(6.4, 3.8))
bars = ax.bar(ops, acc, color=colors, edgecolor="#2b3470", linewidth=0.6)

for b, v in zip(bars, acc):
    ax.text(b.get_x() + b.get_width()/2, v + 0.6, f"{v:.0f}%",
            ha="center", va="bottom", fontsize=9)

# Overall fixed-rate reference line (88%).
ax.axhline(88.0, color="#2b3470", linestyle="--", linewidth=1)
ax.text(5.45, 88.0 + 0.8, "overall 88%", ha="right", va="bottom",
        fontsize=8, style="italic", color="#2b3470")

ax.set_ylabel("Words correctly fixed (%)")
ax.set_xlabel("Error operation")
ax.set_ylim(0, 105)
ax.set_title("Per-error-type corrector accuracy at oracle detection (test)")
ax.spines[["top", "right"]].set_visible(False)

# Legend distinguishing systematic vs. hard cases.
from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(facecolor="#4338ca", label="systematic substitution"),
    Patch(facecolor="#d97706", label="hard cases (no deterministic inverse)"),
], frameon=False, loc="lower left", fontsize=8)

fig.tight_layout()
fig.savefig("fig5_corrector_by_type.pdf", bbox_inches="tight")
```
