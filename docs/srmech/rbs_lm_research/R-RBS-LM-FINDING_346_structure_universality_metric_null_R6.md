# R-RBS-LM Finding 346 — #855 R6: the eigenspectrum-shape metric FAILS for structure-universality (reproduces the F172/F188 flat-spectral identity); the cross-language test needs a shuffle-surviving metric — and the multilingual encode stays user-in-loop

**Date:** 2026-06-03 · **srmech:** 0.7.0rc25 · **#855 block:** R6 (Stream-B native-instruction kernels / cross-coupling) · **reproduces:** F172 (srmech-native spectral invariance), F188 (the 0.99 flat-spectral identity) · **script:** `R-RBS-LM-R6_structure_universality_metric.py`

## What R6 attempted (and why scoped this way)

The real R6 question (Stream B): do per-LANGUAGE native-instruction kernels share relationship-**structure** (is structure universal across languages)? The full test needs the multilingual corpus **fetch** + the **substitute-verifier triality** (the requester is not multilingual) — a user-in-loop step. So R6-now is the tractable, no-fetch part: **define + validate the metric** the cross-language test will use, on the available cross-DOMAIN proxy (srmech vs MFO notebooks — both English/framework, different knowledge-bodies) with a **structure-destroyed control**.

Candidate metric: **normalized K1 co-occurrence-Laplacian eigenspectrum-shape Pearson correlation.** Intuition: two corpora that share relationship-structure (even with disjoint surface vocab) should have the same-SHAPE Class-L eigenspectrum.

## Result — the metric FAILS (clean null)

| pair | normalized-eigenspectrum-shape r |
|---|---|
| srmech ~ mfo (real, both framework) | **+0.974** |
| srmech ~ srmech-**SHUFFLED** (structure-destroyed) | **+0.998** |
| mfo ~ srmech-**SHUFFLED** | **+0.967** |

The structure-**destroyed** control (token-shuffled) correlates *as high or higher* (0.998) than the real framework pair (0.974). **The metric cannot distinguish shared structure from destroyed structure** — it returns r≈0.97–0.99 for everything.

## Why — it measures the universal flat-spectral identity, not structure

The normalized K1 Laplacian eigenspectrum **shape** is dominated by the vocabulary **degree/frequency distribution** (Zipf), which **token-shuffling preserves** (shuffling destroys co-occurrence *order* but keeps which tokens are frequent). So the eigenspectrum shape is a **near-universal artifact of natural-language frequency**, not a discriminating relationship-signature. This **reproduces the lodged result**: F188's "0.99 flat-spectral identity" and F172's spectral-invariance — the K1 presence-eigenspectrum is ~identical in shape across corpora. **Prime-first lesson:** F188 already flagged this; the metric I reached for is exactly the one prior work showed is flat. The experiment re-confirmed it on a new pair + a shuffle control (which sharpens it: the control proves it's a *frequency* artifact, not just cross-corpus similarity).

## Corrected next-step — the cross-language test needs a SHUFFLE-SURVIVING metric

A valid structure-universality metric must **fail the shuffle control** (score low on structure-destroyed input). The K1 presence-eigenspectrum does not. Candidates that should survive shuffling:
- **K3 (position-bound sequence) kernel** — order-sensitive by construction; shuffling destroys it (R5 showed byte_seq → ~0 on reordering). A K3-based structure metric would discriminate.
- **EigenVECTOR alignment** (which tokens co-cluster), not eigenVALUEs — the *content* of the spectral structure, not its Zipf-shaped magnitude profile.
- **Cross-kernel RETRIEVAL discrimination** (the F339-style probe z-score) — does language-A's kernel answer language-A probes above chance.

So before the multilingual fetch, the metric must be redesigned to one of these. The naive eigenspectrum-shape correlation is **disqualified** (it would spuriously report "universal structure" for any language pair, including unrelated ones).

## R6 status — pipeline ready, metric redirected, multilingual encode is user-in-loop

- **ENCODE pipeline** (K1/K3 build) is rc25-ready (F339 + R1 confirm the srmech-native ops run).
- **Metric**: the obvious one (eigenspectrum-shape) is **invalid** (this finding) — redirected to a shuffle-surviving metric (K3 / eigenvector / retrieval). This de-risks the cross-language test *before* spending the multilingual-fetch effort.
- **The full cross-LANGUAGE test is GATED on**: (a) the multilingual corpus **fetch** (10 locales SOURCED+ATTESTED, #846, but not downloaded; BG needs OCR, SR script-control disputed), (b) the **substitute-verifier triality** (user-not-multilingual), and now (c) the **corrected metric**. This is the natural **user-in-loop continuation** — the place the autonomous march correctly stops, per the multilingual-verification discipline.

## Discipline

srmech-native (`dense_laplacian` → `hermitian_eigendecompose`); honest null reported straight (the metric I built failed; reported, not spun); **reproduces lodged F172/F188** rather than claiming novelty (prime-first, even if reached late); the shuffle control is the falsifiable check that proved the artifact. No multilingual content fetched without the verifier-triality (defensive + the user-not-multilingual discipline). Composes with R1–R5: the cross-language structure test will likely ride on the **K3/order-sensitive** side (R5 showed sequence is shuffle-fragile = discriminating) and the **retrieval** side (F339), not the K1 eigenspectrum.
