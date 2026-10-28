[Date]

[Editor Name]
Editor-in-Chief
[Journal Name]

Dear [Editor Name],

We are pleased to submit our manuscript, "Turan: Detecting and Correcting Kazakh Spelling Errors, with a Focus on the 'ka2ru' Cyrillic Look-Alike Phenomenon," for consideration for publication in [Journal Name]. The work is authored by [Author Names] of [Affiliation].

The manuscript addresses a pervasive but under-studied source of Kazakh spelling errors. The nine Kazakh-specific Cyrillic letters (қ, ә, ң, ұ, ү, ғ, і, ө, һ) are frequently typed as visually similar standard-Russian Cyrillic letters when writers lack or ignore the Kazakh keyboard layout. We term this look-alike substitution the *ka2ru* error class. Because the corrupted text remains Cyrillic and superficially resembles Russian, it harms both orthographic processing and language identification, the latter by removing exactly the letters that distinguish Kazakh from Russian.

Our contribution is threefold. First, we construct a reproducible cleaning and confusion-set-based synthetic-error-generation methodology [grundkiewicz2019synthetic] that yields a large parallel corpus for Kazakh spelling correction, with a training split of 2,565,771 corrupted–correct pairs (2,615,771 pairs in total across train, validation, and test) and ka2ru as the dominant injected class (30.5% of edits). Second, we propose a two-stage pipeline that separates detection from correction: a KazRoBERTa [liu2019roberta; kztransformers2023kazroberta] token classifier labels each token KEEP or ERROR, following the tag-not-rewrite paradigm for grammatical error correction [omelianchuk2020gector], and feeds a corrector combining inverse look-alike substitutions, a frequency-weighted lexicon, restricted Damerau–Levenshtein candidate search [damerau1964technique], and morphological guarding of valid inflected forms. On a held-out test set the detector attains an $F_1$ of 97.3% (precision 97.1%, recall 97.4%), and the full pipeline corrects 80.5% of sentences completely, within roughly three points of the 83.5% oracle ceiling obtained under perfect detection. Third, we introduce a lightweight "russified-lexicon" language-routing signal that recovers special-letter-stripped Kazakh otherwise read as Russian, and we package the result as a deployable CPU-only system (throughput ceiling of approximately 200 requests per second, a running-container footprint of about 373 MB of RAM) validated in an accepted live pilot.

We believe these results are well suited to the readership of [Journal Name] because they advance low-resource NLP for an agglutinative Turkic language and provide a reproducible methodology, quantitative evaluation, and a deployable artifact rather than a model in isolation.

We confirm that this manuscript is original, has not been published previously, and is not under consideration for publication elsewhere. All authors have approved the submission and agree to its content. The authors declare no conflicts of interest.

In support of reproducibility, we intend to make the source code, the dataset cleaning and synthetic-error-generation scripts, and the fine-tuned detector checkpoint publicly available upon acceptance, subject to any licensing constraints of the underlying source corpus.

To assist in identifying suitable referees, we suggest reviewers with expertise in the following areas:

1. **Kazakh / Turkic NLP**: a researcher working on Kazakh language resources and models (for example, corpus construction, sequence labeling, or morphological analysis for agglutinative Turkic languages), who can assess the linguistic and resource-level claims.
2. **Grammatical error correction (GEC) / spelling correction**: a specialist in edit-tagging or sequence-to-sequence error correction and synthetic-data training, who can evaluate the detection-then-correction design and the experimental protocol.
3. **Low-resource machine translation / multilingual NLP**: a researcher focused on low-resource modeling and language identification, who can judge the transferability of the methodology and the language-routing component.

We would be grateful if any individuals with a direct conflict of interest were excluded from review; we have no specific exclusions to request at this time.

Thank you for your consideration. We look forward to your response and would be happy to provide any additional information.

Sincerely,

[Author Names]
[Affiliation]
(on behalf of all authors)
