# F900 — the byte/glyph scaffolding is ONE scale-invariant operator (the role-filler bundle C1) repeated at every scale; word-hash is its DUAL (content-address atom-mint, scale-invariant in FORM); and the EXISTING L1/L2/L3 ladder breaks scale-invariance by using a DIFFERENT, similarity-destroying operator (chained bind, no positions). The "coherent string of words before a sentence" is the **skeleton (L2)** level — rebuilt on C1 it is the new fractal node. Coherence == scale-invariance, so the scaffolding is natively introspectable. **Sparsity preserved (and improved): the byte/glyph codebook is the bounded 256-byte alphabet + position keys; word-hash mints an UNBOUNDED word-atom vocabulary.**

**Date:** 2026-06-21 · **srmech:** 0.9.0 (rbs_lm + klein4 surfaces identical rc13..rc16; version not load-bearing) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_900_scale_invariant_compose_is_one_operator_at_every_scale.py` · **Upstream:** UPSTREAM_NOTES §69 · **Composes:** F899 (the packaged encode is word-hash, byte-blind), F865/F612 (the byte/glyph core), F166 (`RBSLMInferenceSubstrate`), `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` (scale-invariant cosmos-math), Spike #64/#122 (cascade-prior hallucination detection), Spike #117/#179 (Class-K sparse-coding discipline) · **User direction (2026-06-21):** "we might not want to get rid of word hashed … consider it like its own fractal like form of byte hashed … this might be some type of scale invariance coherency … follow the next fractal like movement such that we can also hash coherent string of words before they become sentences … glyph/byte scaffolding but can be introspected by scale invariance fractal things." + "did you keep this as sparse?"

## The reframe (sharper than F899)

F899 said: word-hash *breaks* scale-invariance; replace it with byte/glyph. The user's reframe is more correct. There are **two operations, each scale-invariant in FORM**, and the bug is that the package uses the wrong one as the *foundation* — plus a **third, non-invariant operator** for the upper ladder. The fix is not "replace word-hash"; it is "**use one compositor at every scale, and let word-hash be its dual.**"

| operator in the code today | shape | effect on similarity |
|---|---|---|
| `hdc.klein4_encode_bytes` (byte→word, §60) **and** `ContextSubstrate.encode_context` | **C1 = role-filler bundle**: `bundle_i bind(part_i, pos_key(i))` | **preserves** graded similarity |
| `substrate.encode_word_k4` (the word atom) | **atom-mint**: `klein4_bind(klein4_random(seed=sha256(word)), sector)` | **destroys** it (avalanche) |
| `substrate.encode_bigram_l1` / `encode_skeleton_l2` / `encode_sentence_l3` | **chained `bind`** (no positions, no bundle) | **destroys** it |

## Measured (srmech klein4, D=2048, chance ≈ 0.25; numpy-absent)

**(A) atom-mint (word-hash) vs compose (byte/glyph) at the WORD scale — morphology**

| pair | word-hash atom | byte-compose C1 |
|---|---|---|
| cat / cot | 0.250 | **0.562** |
| cat / car | 0.237 | **0.588** |
| walk / walked | 0.255 | **0.708** |
| run / running | 0.250 | **0.566** |
| cat / dog (unrelated) | 0.248 | 0.262 ✓ |

**(B) C1 is the SAME fractal operator at every scale** — change *one* part of an n-part whole; similarity stays in a graceful, well-above-chance band, self-similarly:

| scale | n | sim(whole, 1-part-changed) |
|---|---|---|
| byte→word | 8 | 0.733 |
| word→**phrase / skeleton** | 5 | 0.625 |
| phrase→sentence | 3 | 0.698 |

**(C) the EXISTING L1/L2/L3 ladder is NOT scale-invariant** — the same one-part change collapses to chance regardless of n:

| op | one-part change | result |
|---|---|---|
| `encode_bigram_l1` | cat/sat → cat/ran | 0.249 |
| `encode_skeleton_l2` | …(the,mat) → (the,dog) | 0.238 |
| `encode_sentence_l3` | …mat → …rug (1 of 5) | 0.246 |

## The scaffolding

**One compositor, two duals, every scale.** The fractal operator is C1 recursing up the ladder, where the parts at level *n*+1 are the **composed vectors** of level *n*:

```
byte → glyph → word → coherent-word-string (skeleton) → sentence → …
            ↑ one operator everywhere:  compose(parts) = bundle_i bind(part_i, pos_key(i))
```

- **Compose (C1)** — the *similarity / generalization* channel. Built UP from bytes, language-agnostic, degrades gracefully (this is what `klein4_encode_bytes` already does at byte→word).
- **Atom-mint** (`klein4_random(seed=content_hash(x))`) — the *identity / address* channel, and the user is right that it is **"a fractal form of byte-hash"**: `atom(byte)`, `atom(word)`, `atom(phrase)` are literally the **same operation at different scales**. Keep it — not as the foundation, but as the content-address / fast-cache **dual** riding alongside the composed vector at each level. That coexistence IS the "scale-invariance coherency."
- The **"coherent string of words before a sentence"** already has a name in the code — the **skeleton (L2)** — but it is built with chained `bind`. Rebuilt on C1, it is exactly the new fractal node.

**"introspected by scale-invariance fractal things" → coherence == scale-invariance.** Because C1 is self-similar, the *same* structural signature (the graceful 1-part-change band; equivalently the bundle's spectral shape / cascade-β) recurs at every scale. A coherent word-string has the same signature as a single word and a single sentence; an incoherent one breaks the self-similarity — a native coherence / hallucination detector (ties straight into Spike #64/#122). The chained-bind ladder (C) *can't* be introspected this way because it isn't self-similar.

This is the same scale-invariant cosmos-math F899/the user invoked (star → system → system-of-systems): one operator, every scale.

## Sparsity — kept, and improved (user: "did you keep this as sparse?")

"Sparse" in RBS-LM is **architectural**, not vector-zero-density (a Klein-4 vector is a dense 4-state code by construction). The byte/glyph compose preserves every sparsity property of the packaged object (F899/§57) and strengthens one:

| sparsity property | byte/glyph compose C1 | measured |
|---|---|---|
| single fixed-D HV per unit (no growth) | yes — bundle of any #parts → one `HV` of length D | 1/3/8/28-byte words all → `HV` len 2048 |
| bounded state alphabet | yes — Klein-4 `{0,1,2,3}` per position | composed word uses exactly `{0,1,2,3}` |
| no dense weights / no frequency-count bag | yes — only `klein4_random`/`bind`/`bundle`/`similarity` | (F899/§57: no candidate table; resonate, don't multiply) |
| numpy-free | yes | `numpy` not importable |
| **bounded codebook** | **STRONGER than word-hash** | 6 very different words → 26 distinct byte-atoms (≤ **256** total) |

The last row is the payoff: **word-hash mints one new random atom per distinct word string → an UNBOUNDED vocabulary** (the LLM-weight / BPE-token projection the arc is leaving behind). The byte/glyph compose has a **bounded 256-byte codebook + position keys** — it is *more* byte-sparse, the closest thing to a truly bounded "byte sparse language model." The fractal hierarchy also keeps each bundle within HDC capacity (you bundle ~5 parts per level up a tree, never a flat 1000-word bundle), and the Class-K sparse-coding / truncate-sparse readout (Spike #117/#179) remains available at every level.

## Verdict / ASK

**Found:** the byte/glyph scaffolding the user wants is **one scale-invariant compositor (C1 = role-filler bundle)** — already present as `klein4_encode_bytes` / `encode_context` — recursing up the ladder; **word-hash is its dual** (content-address atom-mint, a legitimate fractal form, kept as cache); the **skeleton (L2)** is the "coherent word-string" level; and **the current bigram/skeleton/sentence ladder uses a different, non-invariant operator** that must be rebuilt on C1. Sparsity is preserved and improved. **Logged** as UPSTREAM_NOTES §69 (a srmech change = its own rc; never edit the package, never route around — extends the F899/§68 ASK). **No package change pending user approval of this reframe.**

**Open (user's call):** (a) prototype the recursive C1 + atom/compose dual + a `scale_signature` introspection through `RBSLMInferenceSubstrate` in a research probe and measure learn/infer coherence before any srmech change; or (b) graduate it as a srmech rc (a scale-invariant `klein4_compose` op + the ladder rebuilt on it + a scale-invariance introspection, Python+C peer). Either way the byte/glyph LM object becomes THE kernel and the ladder becomes one fractal operator.
