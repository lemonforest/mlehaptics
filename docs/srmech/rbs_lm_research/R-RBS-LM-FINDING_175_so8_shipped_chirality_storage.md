# Finding 175 — the SHIPPED so(8)/Spin(8) chirality surface does NOT isolate content-specific, translation-invariant storage (it does WORSE than the hand-build, and worse than the flat lexical bundle)

**Arc:** RBS-LM (28D = so(8) cognitive-laboratory instrument)
**Experiment:** `R-RBS-LM-136_so8_chirality_storage_signature.py`
**Measurements:** `docs/srmech/catalogs/rbs_lm_substrate/substrate_measurements/so8_chirality_storage_signature.ndjson`
**srmech:** 0.5.0rc14, HAS_NATIVE=True, ABI=3 · descriptor_hash `c9b58635becf4b54…` · matched token budget 10443/text · VOCAB_SIZE=200 · WINDOW=5 · seed=42 · Klein-4 D=8192
**Scope (load-bearing):** STRUCTURAL test on TEXT OBJECTS only. Texts are structural test-objects. NO doctrinal / truth / origin / ranking / clinical claims. MFO §VII.6.20 epistemic ceiling (form-reading, not substrate-identity).

---

## The question

F173 (R-RBS-LM-135) tried a **hand-built** K1-chiral signature (the directed γ₅-odd antisymmetric Hermitian `H = i·(A−Aᵀ)` eigen-bundle). It beat across-MAX (within 0.553 > across-max 0.465, 1.46×) but gave **no advantage** over the flat lexical eigen-bundle (within 0.667, 1.67×): its chiral energy was near-uniform (0.77–0.90) across texts, so the clean "content-specific deep-structural storage" signature was **not isolated**.

**This experiment swaps the hand-build for srmech's SHIPPED so(8) chirality ops** — the Klein-4 (ℤ₂)² = (γ₅ × iω₇) bi-axial surface (4 sectors × 7 = 28 = dim so(8)): `srmech.amsc.hdc.{klein4_random, klein4_bind, klein4_bundle, klein4_similarity, klein4_sector_count, klein4_chirality_flip_gamma5/omega7, klein4_cpt_mirror}` + `srmech.amsc.cascade.{net_chirality, chiral_flip}` (Class C). Each token's Klein-4 vector is **routed into its directed-co-occurrence-parity (γ₅, iω₇) sector** via the Klein-4 group action `klein4_bind(v, sector_anchor)` — so the word-ORDER chirality the symmetric Laplacian discards drives the sector structure. Three shipped-chirality signatures: **(S1)** bi-axial occupancy profile `klein4_sector_count(K)`; **(S2)** the so(8) chirality kernel compared by `klein4_similarity` (the head-to-head replacement for the hand-built K1-chiral); **(S3)** `net_chirality` cascade handedness per text.

Isolation criterion (same as F172/F173): within-pair (Quran Yusuf vs Rodwell, SAME content) **>** across-content **MAX** among the 6 distinct texts.

> Design note (the trap the brief flagged): `klein4_chirality_flip_*` are pure XOR on the 2-bit sector label, so `sim(K, flip(K)) ≡ 0` for ANY kernel — a self-vs-flip triple is trivially `(0,0,0)` and discriminates nothing. The text-specific signal therefore had to come from STRUCTURE ACROSS the routed token vectors (occupancy + cross-text kernel overlap), not self-vs-flip.

---

## Result (this run; baselines recomputed live, reproduce F172/F173 bit-exactly)

| signature | within | across-mean | across-max | ratio | beats-max? |
|---|---:|---:|---:|---:|:--:|
| **(S1) SHIPPED bi-axial occupancy** | 0.9996 | 0.9989 | 0.9999 | 1.00× | **No** |
| **(S2) SHIPPED so(8) chirality kernel** | 0.2988 | 0.2686 | 0.3402 | 1.11× | **No** |
| (S2u) so(8) kernel, unweighted *(robustness)* | 0.3210 | 0.2767 | 0.3336 | 1.16× | No |
| (CTRL) klein4 bundle, NO routing *(control)* | 0.4728 | 0.4231 | 0.4857 | 1.12× | No |
| `[base F134]` flat eigen-bundle | 0.6667 | 0.3992 | 0.5720 | **1.67×** | **Yes** |
| `[base F135]` hand-built K1-chiral | 0.5530 | 0.3781 | 0.4648 | **1.46×** | **Yes** |

- **across-MAX drivers:** S1 = (kjv_nt, bhagavad_gita); S2 = (kjv_ot, kjv_nt); flat-bundle = (quran_yusuf, bhagavad_gita); **hand-chiral = (tao_legge, dhammapada)** — i.e. F135's genre-pair (two short aphoristic Eastern texts) still drives the hand-chiral across-MAX, reproduced.
- **klein4 random-orthogonal floor = 0.25** (4 sectors). S2 (0.299) sits barely above floor; it is **near-orthogonal for every pair**.
- **net_chirality (S3):** the per-text handedness is `±1` and the Quran pair **does NOT match** (Yusuf +1, Rodwell −1) — a single bit that flips between translations, so it carries no translation-invariant signal either.

## Mechanism (why the shipped surface fails, diagnosed by the control)

The **NO-ROUTE control** (raw klein4 token-bundle, no chirality routing) lands HIGHER (within 0.473) than the routed so(8) kernel (within 0.299): **the directed-parity chirality routing HURTS** — it drops within-pair similarity by ~0.17. Routing splits the shared-lexical signal across the 4 sectors (a token shared by both translations but routed to *different* sectors contributes zero overlap), so it actively destroys the one signal F172 already showed carries translation-invariance: **raw lexical overlap**. Neither the routed kernel nor the control beats across-MAX, but the control at least preserves more of the lexical signal. The bi-axial occupancy (S1) is at a near-uniform flat ceiling (~0.25 per sector, all texts ~0.999) — the same flat-spectral ceiling F172 found, re-expressed in the occupancy axis; it discriminates nothing. (Validated separately: a klein4 bundle with 50% shared tokens → sim 0.44; 0% shared → 0.25 floor — the machinery responds to lexical overlap, confirming the failure is routing dispersing that overlap, not a dead op.)

---

## What this finding DOES claim

- On this n=1 same-content pair under matched token budget + VOCAB_SIZE=200, the **shipped so(8)/Klein-4 chirality surface does NOT isolate a content-specific, translation-invariant storage signature** — it fails the across-MAX criterion in every variant (occupancy, kernel, unweighted, no-route).
- It does **WORSE than F173's hand-built K1-chiral** (1.46×, beats-max) **and** the F134 flat lexical eigen-bundle (1.67×, beats-max): both the hand-build and the plain lexical bundle out-isolate every shipped-chirality variant here.
- The cause is structural and diagnosed: **bi-axial chirality routing disperses the lexical-overlap signal across sectors**, lowering same-content similarity toward the klein4 orthogonality floor. (The NO-ROUTE control isolates this: routing HURTS.)
- **Tempers, does not overturn, F172/F173.** F172: the translation-invariant carrier is lexical (flat bundle within 0.667 > across-max 0.572); the vocab-independent eigenspectrum is at a universal flat ceiling. F173: vocab-independent structure tracks FORM/GENRE; hand-built chirality gave no advantage. **F175 extends this: the *shipped* chirality surface gives no advantage either — and here it is net-harmful, because the bi-axial routing competes with rather than complements the lexical signal.**

## What this finding does NOT claim

- **NOT** that the so(8)/Spin(8) chirality ops are broken or useless — they are exact (sim(v,v)=1, flips = clean XOR, bundle responds to overlap). The null is about **this storage-isolation task**, not the ops.
- **NOT** that chirality is irrelevant to storage in general — only that *this routing of word-order parity into Klein-4 sectors* does not isolate translation-invariant content here. A routing that *preserves* lexical co-incidence while adding a chirality coordinate (rather than partitioning by it) was not tested and is not ruled out.
- **NO** doctrinal / truth / origin / ranking / clinical claim. Texts are structural test-objects; substrate-identity / meaning still requires a DOMAIN anchor (§VII.6.20).
- **n = 1 same-content pair (Quran Yusuf vs Rodwell)** — a single datapoint, not a law. More attested translation pairs are needed before any of this generalizes.

---

## Provenance / discipline

- All primitives via the **srmech package** (Class L `dense_laplacian` / `hermitian_eigendecompose` for the baselines; the shipped Klein-4 / so(8) chirality `hdc.klein4_*`; Class C `cascade.net_chirality`; `cascade.magnitude` for the imbalance axis — **no python `abs()` in the cascade**; `amsc.format.sha256_bytes` for token-seed derivation only, not as a storage proxy). `Counter` used only for raw co-occurrence edge-construction (R-124 style), never as a similarity/storage proxy.
- Confound control: matched token budget (12000 auto-clamped to 10443 = min available) + VOCAB_SIZE=200 across all 7 texts before any cross-corpus comparison.
- Determinism: `seed=42`; per-token `klein4_random(..., seed=)` seeds are deterministic sha256-derived; baselines reproduce F134 (within 0.6667 / across-max 0.5720) and F135 (within 0.5530 / across-max 0.4648) bit-exactly.
- NDJSON records carry `descriptor_hash`, `source_key`, `srmech_version`, `abi_version`, `has_native`, `seed`, `klein4_D`, `vocab_size`, `window`, `chirality_ops`, and the scope note.

## Cross-references

- **F172 / R-RBS-LM-134** — srmech-native (Class L) storage invariance: lexical eigen-bundle carries translation-invariance (1.67×, beats max); vocab-independent eigenspectrum at universal flat-spectral ceiling.
- **F173 / R-RBS-LM-135** — (C) envelope-subtracted spectrum tracks FORM/GENRE; (D) hand-built K1-chiral beats across-max (1.46×) but no advantage over the flat bundle; clean content-specific signature NOT isolated.
- **F142** — chirality discriminates only where chirality is the load-bearing distinction; this is the null-risk F175 confirms for the storage-isolation task.
- **F158 / F163 / F164** — 28D bi-axial chirality framing; F163 length-control rule applied here.

## srmech package notes (for UPSTREAM_NOTES — reporting, not editing)

- `srmech.amsc.format.sha256_bytes(b)` returns a **64-char hex string**, not raw bytes (despite the name). Minor: callers expecting `bytes` (e.g. `int.from_bytes(...)`) must `int(h[:8], 16)` instead. Worth a docstring/name clarification; behaviorally fine.
- `srmech.amsc.hdc.klein4_bundle(*vectors)` accepts an **even** number of vectors in rc14 (no "needs ODD count" enforcement was triggered) — the brief's odd-count caution did not bite. If odd-count IS intended to be required, the guard is missing; if even is fine, the brief's note is stale. Flagging for confirmation; no neutral-pad was needed.
- No functional defects encountered: the Klein-4 / so(8) chirality ops are exact and deterministic with seeding; the null here is a property of the task, not the tooling.
