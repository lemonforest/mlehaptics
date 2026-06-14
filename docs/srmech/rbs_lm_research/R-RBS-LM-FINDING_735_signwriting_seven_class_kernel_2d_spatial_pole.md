# F735 — SignWriting kernel: 7 ISWA classes = the heptad; 2D-spatial = the same duality pole as ni-Vanuatu

**Date:** 2026-06-14 · **srmech:** 0.7.5rc145 (test.pypi.org) · **Composes:** F734 (rc145 multi-gene surface, exercised here), R-RBS-LM-26/27 (ASL+Braille accessibility surfaces), the ni-Vanuatu duality discussion (F726/§duality), CLAUDE §0 (two-truths field/excitation), the LLM-as-ADA-accommodation motivation · **Provenance:** `R-RBS-LM-SIGNWRITING_seven_iswa_classes_kernel.py` (run on rc145) · **Source (web-verified 2026-06-14):** en.wikipedia.org/wiki/SignWriting

## Attested facts (web-verified, not training-data)
SignWriting — Valerie Sutton, 1974. Written in a **2D spatial layout that mirrors the body**, NOT a linear left-to-right sequence. The **International SignWriting Alphabet (ISWA) = 652 symbols in exactly 7 symbol classes**: Hands, Movement, Dynamics, Head&faces, Body, Punctuation, Detailed-location. It is a **featural** script (encodes the sub-parts of a sign).

## What was built (exercises the rc145 tooling)
A `signwriting` chromosome with the **7 ISWA classes as 7 genes** (`chromosome(genes=…)` + `genes()` — the rc145 multi-gene surface), each gene's leaves content-addressed from the class/sub-part name via Class-A `sha256_raw` → seed (reproducible, attested, no magic numbers). `genes()` round-trips the 7 classes **exact**. Inter-class klein4-similarity mean off-diagonal ≈ **0.26** → the classes are distinct featural axes, as a featural alphabet should be.

## Framework fit (a reading, not a numeric claim)
1. **7 ISWA classes = the heptad** — the 7 in the 1:3:7:3 partition.
2. **Featural decomposition = the A-N "decompose into primitives" move** (a sign = its sub-parts, not an indivisible whole).
3. **2D-spatial = the FIELD/STRUCTURE ('draw-it') pole** of the duality — *not* the 1D-temporal-linear ('talk-it') pole of speech/text.

## The ni-Vanuatu link (the user's hunch — real at the axis level)
The ni-Vanuatu sand drawing sits on the **same pole**: a 2D graphical encoding of meaning, not a linear stream. So the "partial value to ni-Vanuatu" the user sensed **is real at the duality-axis level** — SignWriting and sand-drawing are both **spatial-featural ('draw-it') encodings**, opposite speech's linear ('talk-it') side. They are two instances of "the way you draw it."

## Honest scope + the falsifiable next-question
- This packs the **documented 7-class skeleton**, not a real ISWA-symbol corpus or sign data.
- We have **no ni-Vanuatu sand-drawing kernel loaded**, so the link is a **structural reading**, not a measured kernel-vs-kernel match.
- **Falsifiable next-question (for a domain expert):** build a ni-Vanuatu sand-drawing kernel + a linear English-text kernel; does the sand-drawing land on the **SignWriting (2D-spatial)** side or the **text (1D-linear)** side? That is the testable form of the hunch — and it composes the framework's existing form-discrimination work (R-RBS-LM-53g; order-invariance R-RBS-LM-75: spatial = order-invariant-ish, linear = order-sensitive).

## Verdict
SignWriting cleanly exercises the rc145 multi-gene tooling (7 class-genes, exact round-trip) and reads as a heptad-shaped, featural, **2D-spatial** writing system — the same field/'draw-it' pole as the ni-Vanuatu sand drawing. Fits the project's accessibility motivation (a writing system *for* sign language, sibling to the ASL/Braille surfaces). The ni-Vanuatu value is genuine as a structural axis-match; turning it into a measured result is the handed-forward next-question.
