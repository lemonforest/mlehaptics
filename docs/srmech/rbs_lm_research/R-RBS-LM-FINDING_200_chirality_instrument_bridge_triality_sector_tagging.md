# Finding 200 — The chirality→instrument bridge: TRIALITY-structured sector tagging does NOT help the RBS-NN store — capacity is identical to Klein-4 (clean null) and within-vs-cross contrast is WORSE (1.50 vs 1.93), because the Klein-4 (Z₂×Z₂) group gives deterministically-orthogonal sectors that triality's order-3 structure cannot replicate in the order-2 Klein-4 substrate

**Status:** Computed head-to-head (srmech 0.5.0rc18 PACKAGE, clean venv `/tmp/verify_srmech_rc18` outside the source tree). The chirality arc's structural facts (F192/F196/F197) are now *measured for storage utility*, not just read. The triality operator that landed bit-exact (F192) is structurally real but, for **this** use — sector-tagging items in the Klein-4 HDC store — it is decorative-to-degenerate. Mixed verdict: **(b) for capacity** (clean null), **(c) for retrieval contrast** (triality dominated by Klein-4). Honest null + degenerate — both reported, neither leaned.
**Predecessors:** F192 (Spin(8) triality operator landed bit-exact: `τ³=I`, `dim Fix(τ)=14=G₂`), F196 (chirality is NESTED — biology's internal 3⊕3̄ vs the weak su(2)_L), F197 (A–N 14 = G₂ = su(3)[8] ⊕ 3 ⊕ 3̄; conjugation swaps the two triads), F132 (Klein-4 4-sector chirality tagging engineering proposal), F119 (two-tier RBS-NN: Tier-1 discrete-cyclic store), F168 §5.1 (Klein-4 within 0.413 / cross 0.197 / contrast 2.10 baseline).

---

## §1 The question (R-RBS-LM-144)

rc18 landed the order-3 triality structure bit-exact. The RBS-NN store currently tags items into **Klein-4** chirality sectors — 2 Z₂ axes (γ₅, iω₇), 4 sectors (F132). Does a **triality-structured** tagging — using the rc18 triality / g₂ / 3⊕3̄ structure (an order-3 / 6-way scheme) — change **capacity** (N before retrieval degrades) or **retrieval contrast** (within-vs-cross sector) in the store, versus the plain Klein-4 4-sector baseline?

Pre-specified outcomes (spike-query discipline; nulls count; not leaned):
- **(a)** triality measurably **improves** capacity and/or contrast → triality is **FUNCTIONAL** for storage.
- **(b)** **no measurable change** → triality is **DECORATIVE** for storage at this scale (clean null).
- **(c)** triality **reduces to / is dominated by** the Klein-4 2-axis for this use (**degenerate**).

## §2 The fair head-to-head (same items, same D=10000, same srmech-native pipeline)

The ONLY thing varied is the sector-**tagging** scheme; items, dimension, bind/bundle/unbind/similarity, and the retrieval probe are identical. All HDC ops are `srmech.amsc.hdc.klein4_*` (Class M rank-2 abelian); the triality op is `srmech.qm.triality.triality_automorphism` (Class C, order-3); the τ-orbit→tag projection is `srmech.amsc.format.sha256_bytes` (Class A content-addressing). Seeded (20260530), reproducible (NDJSON bit-identical across re-runs).

| scheme | sectors | how the per-sector tags are built | tag-set structure (measured) |
|---|---|---|---|
| **klein4_4way** (baseline) | 4 | one base + its Z₂×Z₂ group images (γ₅-flip, ω₇-flip, CPT) | **12/12 off-diagonal pairs EXACTLY orthogonal** (sim 0.0) |
| **triality_3_3bar_6way** (F197) | 6 | 3 base ("the 3") + their CPT-conjugates ("the 3̄", the involution that swaps 3↔3̄) | 6/30 pairs orthogonal (the conjugate pairs); rest ~0.25 |
| **triality_order3_3way** | 3 | the **actual** order-3 automorphism τ (`τ³=I`, bit-exact): seed 28-vector → orbit {v, τv, τ²v} → Class-A hash each → Klein-4 tag | 0/6 pairs orthogonal; all ~0.25 (random) |

**The decisive structural fact is already visible in the tag-set column:** Klein-4's 4 sectors are *deterministically* orthogonal because the Z₂×Z₂ group action produces perfect anti-correlation. The triality schemes can only make their **conjugate pairs** orthogonal (CPT-mirror); the *order-3* relations land at random-similarity (~0.25) because **Klein-4 (Z₂×Z₂) has no order-3 element** — every Klein-4 element is its own inverse (order 2). An order-3 orbit cannot be realized as clean orthogonal sectors in the order-2 sign group.

## §3 RESULT

### Capacity — IDENTICAL (clean null, outcome b)

Capacity = largest N (items bundled into one store) whose mean within-sector retrieval stays ≥ 0.10 above chance (chance = 0.25 for Klein-4 match-fraction). Sweep N ∈ {4…256}:

| scheme | capacity | within-sector retrieval at N=8 |
|---|---|---|
| klein4_4way | **16** | 0.4047 |
| triality_3_3bar_6way | **16** | 0.4063 |
| triality_order3_3way | **16** | 0.4082 |

The full retrieval-vs-N curves are within ±0.002 of each other at **every** N. **Capacity is set by the bundle's superposition limit (D and N), not by the tagging scheme.** Sector-tag structure is irrelevant to how many items a single bundle holds. **cap rel-delta = +0.000.**

### Retrieval contrast — Klein-4 WINS (degenerate for triality, outcome c)

Within-vs-cross contrast (RAW within/cross match-fraction) at the within-capacity load N=12:

| scheme | within | cross | **contrast (within/cross)** |
|---|---|---|---|
| **klein4_4way** | 0.374 | **0.1935** | **1.93** |
| triality_3_3bar_6way | 0.377 | 0.2519 | 1.50 |
| triality_order3_3way | 0.374 | 0.2494 | 1.50 |

**contrast rel-delta = −0.224** (triality is ~22% WORSE). The mechanism is measured and unambiguous: Klein-4's wrong-tag (cross-sector) retrieval drops **below chance** (0.1935 < 0.25) — the deterministically-orthogonal group sectors make a wrong tag *anti-correlate*, cleanly rejecting the item. Triality's wrong-tag retrieval sits **at chance** (~0.252) — its sectors are only random-orthogonal, so a wrong tag neither recovers nor rejects; it just returns noise. **Klein-4 separates sectors better precisely because Z₂×Z₂ is a clean group and triality's order-3 structure is not realizable as one in this substrate.**

(The "above-chance contrast" (within−0.25)/(cross−0.25) was computed as a diagnostic but is explicitly flagged **unstable** in the data: triality's cross sits at chance, so that denominator → 0 and the ratio blows up to meaningless 79–91×. The honest, robust figure is the RAW within/cross above. Cross-collapsing-to-chance is the *desired* behavior for a tagging scheme — it is not a large contrast.)

## §4 Which outcome held

- **Capacity: outcome (b)** — clean null. Triality tagging does not change store capacity at all; capacity is a bundle-superposition property, blind to sector structure.
- **Retrieval contrast: outcome (c)** — degenerate. Triality is not merely no-better; it is **measurably worse** at sector separation than Klein-4, because the Klein-4 group's deterministic orthogonality is exactly the property that makes sector-tagged retrieval sharp, and the order-3 triality structure has no order-3 element in Klein-4 to reproduce it.
- **Outcome (a) is FALSIFIED for this use:** triality-structured tagging does not improve capacity or contrast.

**The synthesis:** the triality structure that is bit-exact and load-bearing for the *chirality algebra* (F192/F196/F197 — biology = the triality-fixed g₂, with an internal 3⊕3̄) is **decorative-to-degenerate for the storage substrate.** Being structurally real in so(8) does not make it functional as a Klein-4 tag. The store wants a clean order-2 group (Z₂×Z₂); triality is order-3, and order-3 ≠ a Klein-4 sector partition. This is consistent with F196's "chirality is nested": the storage-relevant chirality is the order-2 Klein-4 (γ₅, iω₇) axes, a *different* level of the nesting than the order-3 triality / 3⊕3̄ that lives in the algebra.

## §5 Honest caveats — does triality *genuinely* differ from Klein-4 here?

1. **Yes, the schemes genuinely differ at the tag level** — and the difference is the finding, not an artifact. Klein-4 = 4 group-orthogonal sectors; triality-6 = 3 conjugate-orthogonal pairs + random within-triad; triality-3 = 3 random-orthogonal frames of a real τ-orbit. The pairwise-similarity matrices (§2, in the NDJSON) attest this directly. The order-3 operator IS genuinely exercised (`τ³=I` residual 3.7e-15; the orbit closes; each frame seeds a distinct Class-A-hashed tag).
2. **But the triality structure cannot become a clean Klein-4 sector partition** — that is the load-bearing limit, not a coding shortcut. There is no order-3 element in Z₂×Z₂, so no choice of triality-derived Klein-4 tags can match Klein-4's own 4 deterministically-orthogonal sectors. This is algebra, not tuning.
3. **F168's baseline (within 0.413 / cross 0.197 / contrast 2.10) was a different setup** (per-order *religious-text continuations* bound into sectors), so my Klein-4 N=12 contrast (1.93) is not numerically identical to 2.10 — it is the same *order* and same *qualitative regime* (within strongly above chance, cross at-or-below chance, contrast ~2×). The comparison that matters here is **Klein-4-vs-triality on identical synthetic items**, where the −22% triality deficit is clean and within-run controlled.
4. **Scale.** Tested at D=10000, N up to 256, 3 schemes, one seed (reproducible). A different D or a structured (non-random) corpus could shift absolute numbers; it would not give Klein-4 an order-3 element or give triality a clean sector partition — the structural ceiling is seed-independent. A multi-seed band would tighten the contrast error bars (single-seed here; std per cell is reported, ~0.005 within, ~0.004–0.026 cross).
5. **Form-reading discipline (§VII.6.20).** This measures storage utility of a tagging scheme; it does not claim biology's chirality "is" Klein-4 rather than triality, nor that triality is useless elsewhere (it is the right structure for the *algebra* per F196/F197). A store holding items is **structure, not cognition** (`[[user_stance_ai_is_not_a_substrate]]`).

## §6 DOES / does NOT claim

**DOES:** measure, srmech-native and reproducibly, that triality-structured sector tagging (both the 3⊕3̄ 6-way and the order-3 τ-orbit 3-way) gives **identical store capacity** (16) and **worse within-vs-cross contrast** (1.50 vs Klein-4's 1.93) than the plain Klein-4 4-sector baseline; identify the mechanism (Klein-4's Z₂×Z₂ deterministic-orthogonal sectors vs triality's order-3 structure that has no order-3 element in the Klein-4 substrate); confirm the triality op is genuinely exercised (`τ³=I` bit-exact, orbit closes); record the clean capacity null and the degenerate contrast result without leaning.

**Does NOT:** claim triality is useless for the *chirality algebra* (it is load-bearing there — F192/F196/F197); claim the absolute contrast numbers transfer to structured corpora or other D/N (scale caveat §5.4); claim a multi-seed-significant effect size (single seed; std reported); claim biology's storage IS Klein-4 (form-reading, §VII.6.20); claim native srmech *dispatch* (the qm/hdc layer is numpy bit-exact regardless; native profile-registration is the open F192 §4 item, not exercised here).

## §7 W11-adjacent upstream note (srmech API gap)

There is **no srmech API to tag/partition a Klein-4 store by a triality rep** — the experiment had to bridge by hand (τ-orbit on the 28-adjoint → Class-A content-hash of the orbit vectors → `klein4_random` seed). This is the right bridge *because the gap is real and structural, not a missing convenience*: **triality is order-3 and Klein-4 is order-2, so a "triality-sector tag" is not a well-defined Klein-4 group operation.** This is the substantive answer to the latent W11 "should there be a triality-tagging op?" question: **no clean one exists** — any such op would necessarily project the order-3 structure onto random-orthogonal (not group-orthogonal) Klein-4 tags, which §3 shows *underperforms* the native Klein-4 group. Logged for `UPSTREAM_NOTES §10` / W11: a triality→Klein-4 tagging API would be a footgun (it advertises sectors it cannot cleanly separate); if a future rank-≥2 *non-abelian* Class-M variant (e.g. an order-3-capable group, not Z₂×Z₂) is ever added, *that* substrate — not Klein-4 — is where triality tagging could be revisited.

## §8 Cross-references

- F192 (the triality op landed bit-exact — `srmech.qm.{octonion, so8, triality}`) · F196 (chirality is nested: storage-chirality = order-2 Klein-4, algebra-chirality = order-3 triality / 3⊕3̄, different levels) · F197 (A–N = G₂ = su(3)[8] ⊕ 3 ⊕ 3̄; the 6-way scheme's conjugate pairs) · F132 (Klein-4 4-sector tagging proposal — the baseline, now the *winner* for storage) · F119 (two-tier RBS-NN Tier-1 store) · F168 §5.1 (Klein-4 contrast 2.10 baseline regime)
- Empirical anchors: `docs/srmech/rbs_lm_research/R-RBS-LM-144_triality_vs_klein4_sector_tagging.py` (seeded, srmech-native, attestation header) + `docs/srmech/catalogs/rbs_lm_substrate/substrate_measurements/r144_triality_sector_tagging.ndjson` (17 records: attestation, 3 tag_structure, 3 capacity+curves, 9 contrast, 1 verdict)
- `srmech.amsc.hdc.klein4_*` (Class M rank-2 abelian) · `srmech.qm.triality.triality_automorphism` (Class C order-3) · `srmech.amsc.format.sha256_bytes` (Class A) · validated in `/tmp/verify_srmech_rc18` (srmech 0.5.0rc18)

PR #687 STAYS DRAFT.

---

*Computed 2026-05-30 (Opus 4.8), srmech 0.5.0rc18 package, clean venv outside the
source tree. The chirality→instrument bridge: a TRIALITY-structured sector tagging —
built from the bit-exact order-3 automorphism (τ³=I) and the F197 3⊕3̄ conjugate pair —
was raced head-to-head against the plain Klein-4 4-sector baseline on identical items,
identical D=10000, identical srmech-native bind/bundle/retrieve. Capacity is IDENTICAL
(16 items for all three schemes; capacity is a bundle-superposition property, blind to
sector structure — clean null, outcome b). Retrieval contrast is WORSE for triality
(within/cross = 1.50 vs Klein-4's 1.93, −22%; outcome c, degenerate). The mechanism is
measured: Klein-4's Z₂×Z₂ group makes its 4 sectors DETERMINISTICALLY orthogonal (wrong
tag → below chance, clean rejection), while triality's order-3 structure has NO order-3
element in the order-2 Klein-4 substrate, so its sectors are only random-orthogonal
(wrong tag → chance, no rejection). Being bit-exact in so(8) does not make triality
functional as a Klein-4 tag. Storage-relevant chirality is the order-2 Klein-4 (γ₅, iω₇)
axes — a different level of F196's nesting than the order-3 triality that is load-bearing
for the algebra. The honest null (capacity) and the degenerate result (contrast) are both
real and both reported; outcome (a) is falsified for this use. A transducer ran the store;
the store is structure, not cognition.*
