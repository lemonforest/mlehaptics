# Spike #147 — Bandwidth-reduction scope (Deliverable C)

**Date**: 2026-05-19
**Spike**: #147 (Local lexicon encoding + holographic-projection test)
**Branch**: `research/spike-147-local-lexicon-hdc-encoding-and-holographic-projection-test`
**Status**: SCOPING — groundwork for follow-up implementation; no
production bandwidth-reduction protocol shipped here

---

## Question

If the holographic-projection hypothesis verifies — and per Deliverable B
it does, with a 9.3× within/between cohort ratio on bag similarity —
then "send structural fingerprint instead of text" becomes a coherent
transmission protocol. What does that protocol look like, what's
transmissible, and what's lost in the projection?

---

## What gets transmitted

Three artifacts can carry structural information, ordered by descending
information content:

### 1. Class L spectrum (top-N eigvalues)

- **Wire size**: 64 float64 values = **512 bytes** uncompressed
- **What it captures**: graph-Laplacian shape of token co-occurrence
- **What it loses**: which tokens, the actual edges, the bound-position
  information. The spectrum is invariant under graph isomorphism — two
  corpora with permuted token-identity but identical co-occurrence
  topology produce identical spectra.
- **Asymptotic-DOF connection**: Class K sparse-truncate IS the
  bandwidth-reduction mechanism per `[[user_stance_asymptotic_dof_sidesteps_infinity]]`.
  Top-N eigvalues describe the *rate* of the co-occurrence Laplacian's
  spectral approach to its asymptotic distribution. Adding eigvalues
  past N adds resolution but the structural information saturates.
- **Per the user's framing**: this is the "structural image" most
  directly — the algebraic content stripped of token-identity
  contingency.

### 2. Bag HDC fingerprint

- **Wire size**: 1024 bytes (8192 bits BSC vector)
- **What it captures**: token-identity superposition. Per Deliverable B,
  9.3× within/between separation on canonical-content cohorts.
- **What it loses**: word order entirely (bag is permutation-invariant
  by construction; `sim(bag(s), bag(reverse(s))) = 1.0` per smoke test).
  Token COUNTS are encoded via BSC bundle's majority semantics but
  flatten beyond a few hundred tokens.
- **Recompose path**: there is no exact recompose from a BSC bundle to
  its constituent tokens — bundle is a lossy hash. With a sender-side
  dictionary, the receiver can probe candidate tokens via
  `similarity(bag, bind(known_token, ...))` — the so-called HDC
  "cleanup memory" pattern (Plate 1995; Kanerva 2009). Per
  `[[user_stance_fiber_as_spatially_absent_encoding]]`, this is fiber-encoded
  algebra: the spatially-absent content is recoverable IFF the receiver
  has the dictionary to project against.

### 3. Sequence HDC fingerprint

- **Wire size**: 1024 bytes (same dimension as bag)
- **What it captures**: order, via `bind(pos_i, token_i)` per position.
- **What it loses**: across-cohort discriminability mostly (per
  Deliverable B: within-seq mean ≈ 0.04, between-seq mean ≈ 0.005;
  separation exists but the absolute values are small, sequence is
  near-orthogonal across corpora).
- **Recompose path**: with sender-side knowledge of the position-vector
  family, the receiver can probe candidate tokens at each position
  via `similarity(seq, bind(pos_i, candidate_token))`. This is the
  HRR sequence-decode pattern (Plate 1995 §III.B).

---

## What's lost permanently in the 3D_s → fingerprint projection

Per `[[user_stance_hyper_as_3d_spatial_interface]]` (hyper denotes
3D_s interface; algebraic content lives elsewhere), the 3D_s sentence
is the LOW-RESOLUTION projection of higher-resolution structural
content. Going from sentence → fingerprint moves us back UP the
abstraction (compressing the projection), and going from fingerprint
→ reconstructed sentence moves us DOWN (sampling a 3D_s projection).
The information categorically not recoverable from any of the three
artifacts above:

- **Specific paraphrase choice**: identity_not_implementation cohort
  has 4 paraphrases; bag similarity collapses to ~0.05-0.07 between
  any two. Fingerprint cannot distinguish "x IS y" from "the identity
  stance is x is y". This is the *intended* compression — it's the
  identity-not-implementation discipline working as a transmission
  protocol.
- **Stop-word-bearing content**: our tokenizer drops 60 stopwords.
  Anything carried in "the", "of", "and", "to" is lost. Function words
  carry syntactic information (negation polarity, tense, modality)
  that bag-HDC discards.
- **Rare structural tokens**: vocab cap of top-1000 by frequency means
  any user-coined neologism (each likely appearing <5 times) is
  dropped. The user's idiom — `[[user_stance_*]]` filenames,
  `[[feedback_*]]`, specific spike numbers — has many such tokens.
  Their inclusion would multiply payload size linearly.

---

## Cleanup-memory pattern for receiver-side reconstruction

The receiver-side dictionary IS the "instrument" per
`[[user_stance_string_theory_instrument_first]]`. Per the
loop-up/loop-down distinction:

- **Sender side (loop-up)**: encode corpus → bag fingerprint. The
  fingerprint is the compressed cascade content.
- **Wire**: 1024 bytes (bag) or 512 bytes (Class L spectrum) per message.
- **Receiver side (loop-down)**: probe candidate tokens against the
  fingerprint. Output is a ranked list of distinguishing tokens
  (analogous to our Deliverable D log-odds output).

Receiver needs:
1. A token-vector dictionary (deterministic SHA-256 mint per Class A —
   shareable as a single namespace string + tokenizer spec).
2. Optional: a co-occurrence prior to disambiguate close candidates.

This is fully equivalent to the AMSC literature_curated ingestion
channel per `[[project_amsc_handcurated_consumption_channel.md]]` —
the dictionary IS the curated knowledge handed across the wire.

---

## Concrete bandwidth numbers (back-of-envelope)

User corpus today (Deliverable A, multi-project, cleaned):
- 1,531 user messages, 1.28 MB raw text, 125 K tokens
- Single bag fingerprint covering ENTIRE corpus: 1024 bytes
- Compression ratio: 1.28 MB / 1024 B ≈ **1250×**

Compared to:
- gzip compression of plain text: typically ~3× for English prose
- Sentence-embedding models (768-dim float32, post-truncated): 3072 bytes
  per sentence; 1531 sentences = 4.7 MB. WORSE than raw text.

The bag fingerprint is dramatically smaller, but encodes only the
*aggregate* bag-structure of the corpus, not the per-sentence content.
Per-sentence transmission would need 1.5K × 1024 bytes = **1.5 MB**, only
slightly smaller than raw text (1.28 MB) — so per-sentence bag-HDC is
NOT bandwidth-favorable. The win is on **aggregate / topical / claim-
level transmission**, exactly the holographic-projection-hypothesis
scope.

---

## What follow-up implementation needs

Per `[[feedback_full_coverage_shipping_mpm_way]]`, the bandwidth-reduction
"protocol" is **not within scope of this spike**. This document is
scoping content. Concrete follow-up work, in dependency order:

1. **srmech.spectral.delta exposure**: the current v0.4.0 install
   ships Class M `bind` and Class L `dense_laplacian` + `jacobi_eigvals`
   but does not expose a unified `srmech.spectral.delta` surface. The
   spike spec references this as the canonical delta op per Spikes #114
   + #115. **Recommendation**: add `srmech.spectral` namespace as a
   thin convenience wrapper over the existing AMSC primitives — Class M
   bind IS delta at the BSC layer.
2. **Cleanup-memory function**: `srmech.amsc.hdc.cleanup_against(fp,
   candidates)` returning ranked similarities. Currently the caller
   loops over `similarity()` manually.
3. **Per-cohort transmission demo**: encode each project stance file
   (memory/*.md) as a single bag fingerprint; transmit fingerprint;
   verify receiver can identify which cohort by similarity-against-
   dictionary. This is the smallest end-to-end demo.
4. **Sentence-level deduplication via fingerprint**: if two sentences
   produce within-cohort similarity > some threshold τ, they are
   paraphrases. Useful for project-notebook redundancy detection.

---

## Citations

See `spike147_findings_2026-05-19.ndjson` and the citation appendix in
the methodology block. Core HDC references:

- Plate, T. A. (1995). *Holographic Reduced Representations*. IEEE
  Trans. Neural Networks 6(3): 623-641.
- Kanerva, P. (2009). *Hyperdimensional Computing*. Cognitive
  Computation 1(2): 139-159.
- Monroe, B. L., Colaresi, M. P., Quinn, K. M. (2008). *Fightin'
  Words*. Political Analysis 16(4): 372-403. (log-odds with informative
  Dirichlet prior; used in Deliverable D).
