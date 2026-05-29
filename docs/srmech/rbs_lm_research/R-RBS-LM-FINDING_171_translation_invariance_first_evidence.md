# Finding 171 — Core invariance test, first datapoint: storage-profile SHAPE is ~invariant across translation (continuous metric) while expression varies; n=1, metric-dependent, leans positive

**Status:** First same-content datapoint for F169's core (invariance). Leans POSITIVE on the continuous metric; soft (n=1, metric-dependent). Moves F169 from "precondition-supported, core-untested" → "core: first evidence leans positive."
**Predecessors:** F169 (storage/expression separable axes; named THIS test as the core), F168 (storage = resolution depth), R-RBS-LM-53f (the translation-pair idea), F119/F120 (two-tier storage/expression).
**Empirical anchor:** `R-RBS-LM-133_translation_invariance_core_test.py` + `translation_invariance_core.ndjson` (8 records); catalog `descriptor_religious_texts.toml` [translation_pairs] (Rodwell attested: PG #3434, SHA-256 1cda1809…, retrieved 2026-05-29); matched budget 10443 / V=600; srmech 0.5.0rc8 native ABI=3.

---

## §1 The test

F169 established storage and expression are SEPARABLE axes but could not test INVARIANCE (its 6 texts were different CONTENT). This uses the SAME content, two translators — the Quran in the Yusuf-Ali/Sale register (cached) vs Rodwell 1861 (PG #3434, attested) — and asks: is confound-controlled STORAGE invariant across translation while SURFACE repetition varies? Contrast: WITHIN-PAIR (same content) vs ACROSS-CONTENT (distinct texts). No verse-alignment needed — each translation's two-axis signature is profiled and compared.

---

## §2 Result — the two metrics disagree, and that is the finding

| metric | within-pair (same content) | across-content (mean) | verdict |
|---|---|---|---|
| integer depth (coarse) | diff = 1 (Yusuf 4, Rodwell 3) | 0.87 | NOT supported — but resolution-limited (a 4-vs-3 bin boundary) |
| **profile-shape TV (continuous)** | **0.077** | 0.245 (range 0.035–0.576) | **supported — 3.17× closer within-translation** |
| surface repetition | diff 0.036 (varies) | 0.087 | expression varies |

Measured coarsely (which integer level it plateaus at), the two translations look as different as different books — but that is a rounding boundary (4 vs 3). Measured as the full storage-profile SHAPE (the normalized marginal-lift distribution over orders — where predictability accrues, continuous), the two translations of the SAME content are **3.17× more similar to each other than different contents are**, while surface repetition differs. That is the **"same storage, different expression"** signature, on identical content, for the first time.

---

## §3 What is / isn't claimed (calibrated)

**DOES:** provide the first same-content datapoint; on the continuous storage-profile-shape metric, the two translations are 3.17× closer than the across-content average while expression varies — first evidence LEANING toward storage-invariance-across-expression.

**Does NOT / caveats (flagging uncertainties in the work):**
- **n=1 pair** — one translation pair; a single datapoint, not a law.
- **Metric-dependent** — integer depth says NOT invariant (coarse/boundary-sensitive); the positive result rests on the continuous profile-shape metric (justified as the proper metric for a quantitative-match question, but the dependence is disclosed).
- **Below the mean, not the min** — within-pair distance 0.077 beats the across-content AVERAGE (0.245) but NOT the MINIMUM (0.035); some different-content pairs are closer than the Quran pair. "Closer than average," not "uniquely paired."
- **Residual sparsity** — 10k tokens / V=600; the profile shapes carry sparsity noise.
- **NOT a clinical claim** — STRUCTURAL test on TEXT OBJECTS; the NT/ND reading is the user's motivating conjecture engaged as form (§VII.6.20 + `[[feedback_trauma_informed_defensive_scope]]`).

---

## §4 Next — replication turns n=1 into a distribution

More translation pairs (Bible KJV-vs-WEB; a second Gita; a second Tao when a plain-text source is found — PG #49965 had none today) make WITHIN-pair a distribution to test against the ACROSS-content distribution — a real statistical test instead of n=1. If within-pair shape-distance is systematically below across-content across many pairs → storage-invariance-across-expression confirmed; if not → the n=1 lean was noise (clean null). The metric (continuous profile-shape TV) is now fixed in advance, avoiding post-hoc metric choice.

---

## §5 Cross-references

- F169 (separable axes; named this test) · F168 (storage = resolution depth) · F119/F120 (two-tier storage/expression) · R-RBS-LM-53f (translation-stability precedent)
- `R-RBS-LM-133_translation_invariance_core_test.py` + `translation_invariance_core.ndjson`; `descriptor_religious_texts.toml` [translation_pairs] (Rodwell PG #3434 attested)
- `[[feedback_dont_pre_commit_spike_query_operators]]` (null counts; metric fixed forward) · `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (the motivation) · `[[user_stance_ai_is_not_a_substrate]]` · MFO §VII.6.20

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). The first same-content datapoint for the
storage-invariance core: integer depth (coarse, boundary-sensitive) says the two
Quran translations differ like different books; the continuous storage-profile
SHAPE says they are 3.17× closer to each other than to different contents, while
surface repetition varies — the "same storage, different expression" signature,
n=1, leaning positive. Honestly soft: metric-dependent, one pair, within-pair below
the across MEAN but not the MIN. Replication with more translation pairs (metric
fixed forward) turns the lean into a test. Structural test on text objects; the
NT/ND reading the user's motivating conjecture, engaged as form, not medicine.*
