# Method / System Architecture

## Overview: a two-stage detect-then-correct pipeline

The proposed system corrects Kazakh spelling and typing errors with a two-stage
pipeline that separates *where* an error occurs from *what* the corrected form
should be. The first stage is a neural **error detector**: a KazRoBERTa
[liu2019roberta; sagyndyk2025kazroberta] token-classification model that reads
the input sentence and emits a per-token KEEP/ERROR judgement. The second stage
is a **corrector** that, for every flagged token, generates candidates from a
frequency lexicon using inverse look-alike substitutions and an
optimal-string-alignment edit-distance fallback, while a morphological analyser
guards valid inflected forms from spurious edits. The two stages communicate
through a single interface — the set of token positions the detector flags — so
the corrector acts only where indicated and otherwise leaves text untouched.
Figure (architecture) depicts the data flow from raw input through language
routing, detection, candidate generation, morphological guarding, and final
reconstruction.

This factorisation is deliberate. Detection is a balanced binary
sequence-labelling task that a pretrained encoder solves with high accuracy,
whereas correction is a precision-sensitive lexical task where uncontrolled
generation risks corrupting already-correct words. Restricting the generative
component to detector-flagged positions and to in-lexicon candidates yields a
conservative failure mode: when no confident candidate exists, the word is left
unchanged rather than rewritten.

## Error detector: KazRoBERTa token classification

The detector fine-tunes `kz-transformers/kaz-roberta-conversational`
[kztransformers2023kazroberta; sagyndyk2025kazroberta], a RoBERTa-style
Transformer encoder [vaswani2017attention; liu2019roberta] pretrained with
masked-language modelling on Kazakh text and using a byte-level BPE vocabulary
[sennrich2016bpe] of $\sim$52{,}000 subwords across 6 layers, 12 attention heads,
and hidden size 768. A token-classification head with two labels,
$\text{id2label}=\{0{:}\,\text{KEEP},\ 1{:}\,\text{ERROR}\}$, is placed on top of
the encoder ([devlin2019bert]).

Training labels are derived by whitespace alignment. The corrupted and the
reference sentence are split on whitespace, and each word $a_i$ in the corrupted
sentence is compared against the aligned reference word $b_i$; the label is
$\text{tag}=\mathbb{1}[a_i \neq b_i]$. Because corruption preserves the number of
whitespace tokens, the two word lists stay aligned position by position. After
subword tokenisation, only the first subword of each word carries the word-level
label; continuation subwords and special tokens are set to the ignore index
$-100$ and do not contribute to the loss. Approximately $10.7\%$ of labelled
tokens are ERROR, giving a usefully balanced labelling task.

We adopt token classification rather than a sequence-to-sequence (seq2seq)
formulation for three reasons. First, the targeted errors are *local* edits —
look-alike letter substitutions, vowel-harmony violations, single-character
swaps, drops, duplications and substitutions — so a non-autoregressive
edit-tagging view aligns naturally with the problem, as in edit-based grammatical
error correction [awasthi2019pie; omelianchuk2020gector]. Second, a tagger
factorises detection from generation, allowing a precise, lexicon-constrained
corrector to handle rewriting deterministically; a seq2seq decoder would fold
both into one model and could hallucinate substitutions on already-correct
tokens. Third, the tagger is cheaper to train and serve and needs no
autoregressive decoding at inference. The model is fine-tuned for 2 epochs
($\approx 80{,}182$ optimiser steps) on a Colab T4 GPU using AdamW with learning
rate $2\times10^{-5}$, batch size 64, weight decay $0.01$, maximum sequence
length 128, and mixed-precision (fp16); the best checkpoint is selected by ERROR
$F_1$ on the validation split. The resulting checkpoint occupies $\sim$316 MiB in
`safetensors` format. On the held-out test set (8{,}000-sentence subset), the
detector attains $F_1 = 97.3\%$ (precision $97.1\%$, recall $97.4\%$), versus
$F_1 = 86.3\%$ for a heuristic baseline that flags any word absent from the
lexicon (Table X).

## Corrector: lexicon-constrained candidates with an edit-distance fallback

Given the detector's flagged positions, the corrector replaces each Cyrillic
substring of a flagged word while preserving surrounding punctuation, hyphenated
parts and original casing. Two complementary candidate generators are used.

The first generator applies **inverse look-alike substitutions**. A bidirectional
substitution map encodes the visually similar Russian$\leftrightarrow$Kazakh
Cyrillic pairs and the vowel-harmony pairs — for example $\text{а}\leftrightarrow
\text{ә}$, $\text{о}\leftrightarrow\text{ө}$, $\text{у}\rightarrow\{\text{ұ},
\text{ү}\}$, $\text{к}\leftrightarrow\text{қ}$, $\text{г}\leftrightarrow\text{ғ}$,
$\text{н}\leftrightarrow\text{ң}$, $\text{и}\rightarrow\text{і}$, $\text{і}
\rightarrow\{\text{ы},\text{и}\}$, $\text{х}\leftrightarrow\text{һ}$. The map
directly inverts the two dominant error classes (the *ka2ru* look-alike class and
vowel-harmony violations). To bound the combinatorial expansion, substitutions
are enumerated over at most six replaceable positions, and only candidates that
appear in the lexicon are retained. Among the surviving candidates the most
frequent form is chosen.

The second generator is an **edit-distance fallback** for swap, drop,
duplication and substitution errors that look-alike inversion cannot resolve.
It searches the lexicon with `rapidfuzz` `process.extract` using the
optimal-string-alignment (OSA) distance — a restricted Damerau–Levenshtein metric
in which a transposition counts as a single edit (cost 1)
[levenshtein1966binary; damerau1964technique; kukich1992techniques] — with a
score cutoff of 2 edits. The search pool is limited to lexicon forms whose length
is within the distance bound of the query. Among the minimum-distance forms the
most frequent one is selected (frequency tie-break).

When the detector flags a word that is itself a valid lexicon entry but wrong in
context (for example, the Russified surface form *казак* whose intended Kazakh
form is *қазақ*), the corrector runs in a **force-correct** mode: it re-evaluates
even in-lexicon words and accepts a candidate only if the candidate's frequency
is at least that of the original surface form, avoiding replacements toward rarer
words. The lexicon is built from the cleaned corpus
([makhambetov2013kazcorpus]) and contains 339{,}717 surface forms; the *valid*
subset used for candidate filtering retains the 174{,}100 forms with frequency
$\geq 2$, which suppresses noise from corpus artefacts.

The correction decision for a single word can be summarised as follows.

1. Lower-case the word; if the detector did **not** flag it and it is in the
   valid lexicon, return it unchanged.
2. Generate inverse-substitution candidates and keep those in the valid lexicon.
3. If any in-lexicon inverse candidates exist, choose the most frequent one;
   in force-correct mode, keep the original if it is valid and at least as
   frequent as the best candidate; otherwise apply the candidate (restoring
   original casing).
4. If no inverse candidate exists but the word is valid, return it unchanged.
5. Otherwise run the OSA edit-distance search ($\leq 2$ edits); return the
   nearest form (frequency tie-break), or the original word if no candidate is
   within the cutoff.

At oracle detection on the test set the corrector fixes $88\%$ of erroneous words
with $91.6\%$ precision of changes, with strong per-type performance on the
dominant classes (*ka2ru* $97.6\%$, harmony $97.9\%$, duplication $93\%$) and
weaker performance on transposition, substitution and deletion (swap $83\%$,
sub $70\%$, drop $62\%$), reflecting the absence of contextual re-ranking
(Table X).

## Morphological guarding

Kazakh is agglutinative, so a finite lexicon cannot enumerate every inflected
word-form; without protection, the edit-distance fallback would "correct" valid
inflections toward whatever dictionary word lies closest. To prevent this, a
morphological analyser segments a surface form in the canonical nominal order
$\text{STEM}\,(+\text{NUMBER})\,(+\text{POSSESSIVE})\,(+\text{CASE})$
([kessikbayeva2014kazakh; washington2014kypchak]). It strips suffixes from the
right — case, then possessive, then number — using declared allomorph
inventories, requires at least two stem characters to remain (avoiding degenerate
single-letter stems), and reverses stem-final voicing alternations
($\text{қ}\!\rightarrow\!\text{ғ}$, $\text{к}\!\rightarrow\!\text{г}$,
$\text{п}\!\rightarrow\!\text{б}$) when recovering the dictionary stem. Each
segmentation is checked for **vowel-harmony consistency**: every vowel in the
stripped suffix string must belong to the stem's harmony class (back or front),
rejecting an accidental suffix-shaped ending on a foreign or misspelled stem. A
word is treated as a valid inflected form, and left untouched, only if it admits
a segmentation whose stem is a known lexicon entry *and* whose suffixes are
harmony-consistent. For example, *мектептердің* is recognised as *мектеп*-PL-GEN
and is therefore not edit-distance "corrected".

## Language routing

Because the *ka2ru* error class strips the Kazakh-specific letters, corrupted
Kazakh text remains Cyrillic but superficially resembles (broken) Russian,
which misleads conventional language identification and, with multilingual
models, the wrong-language routing this entails [pires2019multilingual]. The
router adds a **russified-lexicon coverage** signal to counter this. The Kazakh
valid lexicon is mapped through the *ka2ru* substitution
$\{\text{ә}\!\rightarrow\!\text{а},\ \text{ө}\!\rightarrow\!\text{о},\
\text{ұ}\!\rightarrow\!\text{у},\ \text{ү}\!\rightarrow\!\text{у},\
\text{қ}\!\rightarrow\!\text{к},\ \text{ғ}\!\rightarrow\!\text{г},\
\text{ң}\!\rightarrow\!\text{н},\ \text{і}\!\rightarrow\!\text{и},\
\text{һ}\!\rightarrow\!\text{х}\}$ to build a set of *russified-Kazakh* forms
(restricted to forms of length $\geq 3$ and frequency $\geq 3$). The signal
$\text{kaz\_lex\_ratio}$ is the fraction of input tokens that fall in this set
**and** are not Russian stopwords, so genuinely Russian function words do not
inflate the Kazakh score.

The signal is length-aware and nonlinear. For inputs of three or more tokens it
ramps only above a coverage of one half,
$\text{kaz\_lex\_signal}=\max\!\big(0,\ (\text{kaz\_lex\_ratio}-0.5)/0.5\big)$,
so a few coincidental matches do not flip routing. For one- or two-token inputs,
where context is scarce, the signal is $1.0$ only when *all* tokens are
russified-Kazakh and $0.0$ otherwise. The router combines this with character-
and token-level cues, $\text{kaz\_score}=0.6\cdot\text{kaz\_char\_ratio}+0.7\cdot
\text{kaz\_lex\_signal}+0.1\cdot\text{kaz\_token\_ratio}$; the Russian branch is a
deliberate no-op (no Russian model), avoiding corruption of valid Russian. For
example, «Бұл мәселе өте маңызды болып тұр», corrupted to «Бул маселе оте манызды
болып тур», is routed to Kazakh and restored to its canonical form.
