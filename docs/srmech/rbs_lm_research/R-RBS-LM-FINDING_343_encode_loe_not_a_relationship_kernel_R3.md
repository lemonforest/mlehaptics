# R-RBS-LM Finding 343 — #855 R3 / §17.1: `encode_loe_content` is a CONTENT-FINGERPRINT, not a relationship-kernel — it does NOT reproduce K1; K1 stays (already srmech-primitive-native); the real migration is U1

**Date:** 2026-06-03 · **srmech:** 0.7.0rc25 · **#855 block:** R3 (migrate onto the upstreamed surface) · **tests:** UPSTREAM §17.1 (parity check) · **ref:** F339 (hand-rolled K1/K3 notebook kernels)

## The question

§17.1 hoped our hand-rolled K1/K3 kernel-build (F339) could **migrate onto** srmech's upstreamed text→instrument surface (`encode_loe_content`, `rbs_lm.encode_*`) — retiring the `Counter()`/`re.findall` hand-rolls. R3 is the parity check: does `encode_loe_content` reproduce the K1 framework-vs-negative discrimination (F339: framework peak z=+2.59, negative peak z=−0.27)?

## Method (rc25)

Encode the srmech notebook (778,850 chars) as one `encode_loe_content` instrument S; baseline = 100 random paragraph-pair similarities; score the same F339 framework + negative probes by `similarity(encode_loe_content(probe), S)` → z. `encode_loe_content(notebook)` ran in 0.2s → 1024 bytes.

## Result — clean NULL (reported straight)

| | encode_loe_content | hand-rolled K1 (F339) |
|---|---|---|
| framework peak z | **−0.55** (mean **−1.11**) | **+2.59** |
| negative peak z | **+1.04** | −0.27 |
| discriminates framework>negative? | **NO** | yes |

Framework probes are *slightly anti-correlated* with the notebook instrument (z negative); negatives score *higher* than framework. `encode_loe_content` does **not** reproduce K1's discrimination.

## Interpretation — different objects, not a tuning gap

`encode_loe_content` is a **content-fingerprint** (LoE = levels-of-edit / cascade delta-encode): same content → identical instrument (verified self-sim 1.000 earlier), different content → orthogonal (−0.007). That is **content-addressing**, not relationship-structure. A short probe phrase vs a 778k-char notebook are at wildly different scales, and a delta-encoded content fingerprint of the whole notebook does not align with a 6-word probe. K1, by contrast, is a **Class-L co-occurrence-Laplacian eigendecomposition** — it builds the vocabulary *relationship graph* and a bag-of-words probe aligns with its top eigenvectors. The two encoders answer different questions: `encode_loe_content` = "is this the same content?"; K1 = "does this share relationship-structure?" The null is real and correct, not an artifact.

## Verdict — KEEP K1; the genuine migration is U1 (srmech-dev), not a swap onto encode_loe_content

- **No migration of K1 onto `encode_loe_content`.** They are different objects (content-fingerprint vs relationship-kernel).
- **K1 is already srmech-primitive-native** — it composes `dense_laplacian` → `hermitian_eigendecompose` (Class L) + `mint_vector`/`bundle` (Class M). The only hand-rolled parts are `tokenize` + the `Counter` edge-build + the top-K-eigvec→mint→bundle assembly. So K1 is *not* reinventing a srmech op; it's composing srmech primitives with a thin Python wrapper.
- **The real migration path is UPSTREAM §17 U1** — ship `tokenize` + `cooccurrence_edges` (Class-L precursor) as srmech ops, after which K1 becomes a **pure-TOML DSL composite** (`tokenize → cooccurrence_edges → dense_laplacian → eigendecompose → topk_eigvec_tokens → mint → bundle`) with no hand-roll. That is a **srmech-dev ask**, not something we swap to today.

## Refines UPSTREAM §17

`encode_loe_content` (the §17 U2 register-as-DSL-op candidate) is a **content-fingerprint stage** — genuinely useful (content-addressing / dedup / same-content matching chains, and it works + is cheap to register) — **but it is NOT the relationship-kernel.** So U2 still stands (register it; it's a real op), but with the corrected label: it provides a *content* stage, and the *relationship-kernel* still needs U1. The two are complementary, not substitutes.

## Open follow-on (flagged, not tested)

The `rbs_lm.encode_{word_k4, bigram_l1, skeleton_l2, sentence_l3}` **layered** encoders are closer to K3 (position-bound sequence) than to K1. Their parity vs K3 is **untested here** — a clean follow-on (does `encode_sentence_l3` reproduce the K3 sequence signal?). Left open honestly rather than asserted either way.

## Discipline

srmech-native (`encode_loe_content` + `hdc.similarity`); null reported straight (framework z negative — not spun); the comparison baseline is the committed F339 K1 number. No leaning: this is a "different object" finding, and `encode_loe_content` is *not* called deficient — it's the right tool for content-addressing, the wrong tool for relationship-kernels.
