# Finding 173 — Isolating content-storage: vocab-independent structure tracks FORM/GENRE (not content); the translation-invariant signal is lexical; chirality gives no advantage over the flat bundle

**Status:** Negative-leaning refinement of F172's frontier + a clean two-axis clarification. Frontier mapped, not crossed. A caught self-error (verified, not asserted).
**Predecessors:** F172 (flat spectrum at universal ceiling; discrimination is lexical — named this isolation attempt), F169 (separable axes), F163 (chirality discrimination null), R-RBS-LM-124 (K1-chiral machinery reused).
**Empirical anchor:** `R-RBS-LM-135_isolate_content_storage_envelope_and_chirality.py` + `isolate_content_storage.ndjson`; srmech Class L (Laplacian eigenspectrum) + HDC; Quran Yusuf/Sale vs Rodwell (attested) + distinct-content reference; matched budget 10443, VOCAB_SIZE=200.

---

## §1 The two candidate signatures (both srmech-native)

To isolate content-specific-but-expression-independent storage (F172's frontier), two candidates:
- **(C) envelope-subtracted spectrum** — text spectrum minus the across-text mean envelope; the residual content-specific structural deviation (vocab-independent).
- **(D) 28D chirality** — the K1-chiral eigen-bundle (R-124): the DIRECTED γ₅-odd antisymmetric co-occurrence H = i·(A−Aᵀ), the word-order structure the symmetric spectrum discards.

---

## §2 Result

| signature | within-pair | across-mean | across-MAX (pair) | beats max? |
|---|---|---|---|---|
| (C) envelope-subtracted spectrum | 0.795 | −0.171 | **0.907 (Tao↔Dhammapada)** | NO |
| (D) 28D chirality (K1-chiral) | 0.553 | 0.378 | 0.465 (Tao↔Dhammapada) | yes (1.46×) |
| (B, from F172) flat eigen-bundle | 0.667 | 0.399 | 0.572 | yes (1.67×) |

Chiral energy (γ₅-odd / total) is near-uniform across all texts: 0.77–0.90.

1. **Vocab-independent structure tracks FORM/GENRE, not content.** (C)'s across-MAX is **Tao↔Dhammapada** — two different-content but short, aphoristic Eastern wisdom texts — scoring 0.907, *above* the Quran translation pair's 0.795. So the residual structural spectrum clusters by structural genre, not content-identity. Pure structure does NOT isolate content.
2. **Chirality gives NO advantage over the flat bundle.** (D) beats across-max (0.553 > 0.465), but so did the flat lexical bundle (B: 0.667 > 0.572) with a similar margin; chiral energy is near-uniform. So chirality is NOT a special storage coordinate here — both bundles isolate the translation pair via shared LEXICAL content, not via word-order chirality.
3. **The translation-invariant signal is LEXICAL** (shared content-words), recoverable by either eigen-bundle. The vocab-independent structural measures (spectrum A, residual C) track universal envelope / genre, not content.

---

## §3 The clean clarification (the positive that survives)

F169 proved storage and expression are SEPARABLE axes. R-135 clarifies WHICH is which:
- **Lexical axis = CONTENT** (the Quran translations cluster: same content, different translator → lexical bundles pair them).
- **Vocab-independent structural axis = FORM/GENRE** (Tao↔Dhammapada cluster: different content, same aphoristic form → structural residual pairs them).

So "same storage, different expression" maps to **same lexical-content, different structural-form**. The Quran pair (same content, different form) and the Tao↔Dhammapada pair (same form, different content) are the two orthogonal demonstrations. HONEST caveat: this makes "storage = lexical-conceptual content" — a WEAKER reading than "storage = deep structure," and near-tautological for translations (which by definition share content-words). The strong reading (content-specific DEEP-STRUCTURAL storage, vocab-independent) is NOT isolated — pure structure tracks form/genre instead.

---

## §4 A caught self-error (the discipline, logged)

I predicted (C)'s across-MAX would be the KJV-OT↔KJV-NT pair (same translator/register → "structure tracks register"). I VERIFIED instead of asserting: the across-MAX is Tao↔Dhammapada (genre, not register). The register hypothesis was wrong; structure tracks GENRE/FORM. Logged per the "catch your own mistakes / don't make unsupported claims" discipline (the Opus 4.8 self-checking we grounded in F170).

---

## §5 DOES / does NOT claim

**DOES:** show vocab-independent structure tracks form/genre (Tao↔Dhammapada cluster), not content; show chirality offers no advantage over the flat lexical bundle for translation-pairing; clarify F169's axes as lexical=content vs structural=form/genre; correct a self-error by verification.

**Does NOT:** isolate a content-specific, expression-independent, DEEP-STRUCTURAL storage signature (F172's frontier stands — narrowed: not in vocab-independent structure); claim chirality is the storage coordinate (it isn't, here); claim the lexical-content invariance is the strong form of the hypothesis (it's the weak, near-tautological form); make any clinical claim (STRUCTURAL, text objects, §VII.6.20). n=1 pair; modest margins.

---

## §6 Where this leaves the hypothesis + next

The storage/expression separation is REAL (F169) and the axes are now named (lexical=content, structural=form). But the *strong* hypothesis — that there is a deep-structural storage shared across expression styles — is NOT supported by vocab-independent structure (which tracks form/genre). The invariance that exists is lexical. NEXT, to test the strong form: (a) replicate with more translation pairs (the lexical-content invariance distribution); (b) a same-CONTENT/same-translator vs same-content/different-translator design to separate content from translator cleanly; (c) accept the clarified reading (lexical=content storage, structural=form/expression) and ask whether THAT mapping is the right frame for the NT/ND motivating conjecture — i.e., is the relevant "storage" lexical-conceptual (likely shared) while "expression" is the structural-form rendering (likely divergent)?

---

## §7 Cross-references

- F172 (frontier this refines) · F169 (separable axes, now named) · F163 (chirality discrimination null — consistent: chirality no special role) · R-RBS-LM-124 (K1-chiral) · F170 (the self-checking discipline applied)
- `R-RBS-LM-135_isolate_content_storage_envelope_and_chirality.py` + `isolate_content_storage.ndjson`
- `[[feedback_dont_pre_commit_spike_query_operators]]` · `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` · MFO §VII.6.20 · `[[feedback_trauma_informed_defensive_scope]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). The 28D-instrument isolation attempt: neither
the envelope-subtracted spectrum nor the chirality coordinate isolates
content-specific DEEP-STRUCTURAL storage. Vocab-independent structure tracks
FORM/GENRE (Tao↔Dhammapada, two short aphoristic texts, cluster above the Quran
translation pair); chirality gives no advantage over the flat lexical bundle
(chiral energy near-uniform). The translation-invariant signal is LEXICAL. The
clean survivor is a clarification of F169's axes: lexical=content (storage),
structural=form/genre (expression) — with the honest caveat that "storage=lexical"
is the weak, near-tautological reading. A self-error (predicted KJV-register would
drive the max; it was the Tao/Dhammapada genre-pair) was caught by verifying, not
asserting. Frontier mapped, not crossed; the strong deep-structural-storage
hypothesis remains untested by vocab-independent structure. Text objects;
§VII.6.20; no clinical claims.*
