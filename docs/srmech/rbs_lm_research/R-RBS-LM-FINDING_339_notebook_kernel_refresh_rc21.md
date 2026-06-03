# R-RBS-LM Finding 339 — Updated srmech + MFO notebook kernels (rc21 refresh); they carry the framework's dominant relationship-structure, and the falsification record rides in the low-frequency tail (honest null on the literal "falsification" probe)

**Date:** 2026-06-03 · **srmech:** 0.7.0rc21 (freshly verified, UPSTREAM §16) · **Method:** R-RBS-LM-52b multi-kernel, srmech-native + torch-free · **Script:** `R-RBS-LM-kernel_refresh_2026-06-03.py` · **Artifacts:** `kernels_refresh_2026-06-03/` (12 files) + `…_results.json`

## What & why

User direction: *"need updated kernels for srmech and mfo research notebooks. they carry the knowledge of falsification."*

The prior multi-kernel build (R-RBS-LM-52b) ran on **srmech 0.4.2** against a far smaller notebook state (`116,198`-n-gram combined corpus). Since then the two notebooks grew to carry the whole **F167→F338** arc — **including the falsification record** (every correction, null finding, and triality-trimmed over-reach). Per **F172** the Class-L co-occurrence-Laplacian eigenspectrum IS the srmech-native storage signature, so rebuilding the kernel on the *current* notebooks is how that accreted knowledge enters the kernel.

This refresh builds a kernel **per notebook** (srmech alone, MFO alone) **+ the combined** (continuity with 52b), on the freshly-verified rc21, and **preserves** the historical `R-RBS-LM-52b_results.json` (the 0.4.2 claim stands; this is a peer artifact, not an overwrite).

**Method (srmech-native, no Python-reflex storage proxy):**
- **K1 — presence:** `dense_laplacian` (Class L) → `hermitian_eigendecompose` → top-K=33 eigenvectors → top-M=21 tokens each → Class-A `mint_vector` → Class-M `bundle`. (`Counter` is used only as the edge-weight accumulator feeding `dense_laplacian` and for `most_common` vocab selection — the prescribed build-edges-then-Laplacian path, not a co-occurrence storage proxy.)
- **K3 — sequence:** position-bound 3-gram Class-M `bind`∘`permute` (stride D/3) → hierarchical `bundle`. Captures arrangement-as-meaning.
- D=8192, vocab=200, window=5, 5000 sampled n-grams. Baselines = 100 random same-notebook paragraph pairs.

## Results — the updated kernels

| Notebook | chars | content-tokens | K1 edges | K3 n-grams | K1 framework peak z | K1 neg peak z | K3 framework peak z |
|---|---|---|---|---|---|---|---|
| **srmech** | 778,850 | 59,151 | 13,283 | 58,551 | **+2.59** | −0.27 | +1.79 |
| **MFO** | 904,530 | 69,004 | 14,712 | 68,690 | **+2.68** | −0.17 | +1.34 |
| **combined** | 1,683,380 | 128,155 | 16,438 | 127,241 | **+2.86** | — | +2.27 |

Baselines: K1 mean +0.0153 / std 0.0393 / **max +0.2346**; K3 mean −0.0001 / std 0.0107 / max +0.0312. K1 top-8 eigenvalue tail (the F172 signature): srmech `[7860, 6366, 3845, 2531, …]`, MFO `[7137, 5129, 5008, 4677, …]`.

**Corpus growth vs the prior 0.4.2 build:** combined n-grams **127,241 vs 116,198 = 1.10×** — the ~11k new n-grams are the F167→F338 accretion (~one week of intensive research, falsification record included).

**Signal confirmed (reproduces the 52b pattern).** Framework probes clearly outscore negatives on every kernel (K1 peak z ≈ +2.6–2.9 vs negatives ≈ −0.3 to +1.0). What the kernels carry *most strongly* (srmech K1, z-ranked) is the **core framework relationship-structure**:

| probe | z |
|---|---|
| cascade composition class L laplacian eigenspectrum | **+2.59** |
| primitive class operator vocabulary A N | **+2.34** |
| one three seven three partition hurwitz | **+2.20** |
| epistemic ceiling form not substrate reading | +1.64 |

`above_max = 0/12` on K1 is expected and matches 52b: the K1 baseline max (+0.2346) is inflated because random *same-notebook* paragraph pairs already share heavy framework vocabulary — so "above mean+2σ" (z>2), not "above max," is the right detector here.

## The honest two-part finding (no leaning; null counts)

**(1) CONFIRMED — the kernels carry the framework's dominant relationship-structure**, updated to the current corpus, on rc21. The A–N vocabulary, Class-L cascade composition, and the 1:3:7:3 / Hurwitz partition are all strong (z>2.2). The srmech kernel leans srmech-specific probes (mean z **+0.70** vs MFO-specific **+0.11**); the MFO kernel barely discriminates (srmech **+0.58** ≈ MFO **+0.65**) — because the two notebooks share most framework vocabulary. So the per-notebook split is real but weak; the *content* the kernels carry is the shared framework spine.

**(2) NULL — the literal "falsification" probe sits at baseline.** A bag-of-words probe `"falsification null finding triality trimmed"` does **not** light up the kernels: srmech K1 z=**−0.12**, MFO K1 z=**+0.24**, srmech K3 z=−0.06, MFO K3 z=**−1.63**. Reported straight.

**Honest re-reading of "they carry the knowledge of falsification":** the falsification record IS in the notebook *text* (every corrected/trimmed/null F-number), and the kernel is the spectral signature of that *whole current corpus*. But the falsification record is a **low-frequency / low-eigenvalue feature** — it is NOT what the **top-K presence eigenvectors** emphasize (those are dominated by the dense framework-concept co-occurrence). So a top-K presence kernel carries falsification only as part of the corpus tail, not as a dominant mode, and a literal "falsification" probe reads as baseline. This is the F172 storage-signature truth applied honestly: *the kernel encodes the corpus that contains the falsifications, but it foregrounds the framework's recurring structure, not its corrections.*

## The next question (handed forward)

If the goal is a kernel that genuinely **foregrounds** the falsification knowledge (not just contains it in the tail), the constructive moves are: **(a)** a *low-eigenvalue-tail* kernel (the fine-structure modes, not top-K — the corrections live in the rare co-occurrences), or **(b)** a *falsification-section-restricted* kernel built only from the corrected/null/trimmed findings (the corpus already tags them: "rejected," "downgraded," "triality-trimmed," "null finding"). Either is a clean follow-on; this refresh deliberately kept the proven 52b top-K presence method so the comparison vs the 0.4.2 build is apples-to-apples.

## Artifacts

`docs/srmech/rbs_lm_research/kernels_refresh_2026-06-03/` — 6 kernel instruments (`{srmech,mfo,combined}_notebook_{K1,K3}.bin`, 1024 bytes each = the D=8192 bipolar bundle) + per-kernel `.meta.json` (vocab/edges/eigenvalue-tail/n-gram counts). `R-RBS-LM-kernel_refresh_2026-06-03_results.json` = full per-probe z-scores + growth comparison. Built on rc21; reproducible via the committed script.

## Discipline

srmech-native (Class-L `dense_laplacian`/`hermitian_eigendecompose` + Class-M `mint`/`bundle`/`bind`/`permute`), torch-free; no `np.linalg.eig`, no hand-rolled similarity. Null reported straight per the no-leaning / null-findings-count discipline. The 0.4.2 build is preserved, not overwritten. No-magic-numbers: every constant (D=8192, K=33, M=21, vocab=200, window=5, stride=D/3) is the attested R-RBS-LM-52b configuration.
