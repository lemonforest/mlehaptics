# F901 — executes F900 Open(a): the recursive C1 ladder PROTOTYPED + MEASURED + run through `RBSLMInferenceSubstrate`. ONE scale-invariant compositor (C1 = role-filler bundle) at every rung byte→word→phrase→sentence is self-similar (0.745 / 0.689 / 0.724 at D=8192 — reproduces F900's D=2048 band); the atom/compose DUAL coexists (atom = exact identity 1.000, compose = graded 0.560); and the **scale_signature is a working introspection** — it IDs the compositor (C1 0.745 vs chained-bind 0.250) AND detects on-manifold coherence (real-morphology 0.586 vs gibberish 0.269, 2.2× separation). The C1 word-rung runs through the packaged inference object. No srmech change — research prototype per F900 Open(a), before any package edit.

**Date:** 2026-06-21 · **srmech:** 0.9.0rc13 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_901_recursive_c1_ladder_executes_f900_open_a.py` · **Composes / extends:** **F900** (the reframe — one C1 compositor, word-hash is its dual, the chained-bind ladder is broken; this finding executes its **Open (a)**), F899 (the packaged encode is word-hash), F865/F612 (the byte/glyph core), F166 (`RBSLMInferenceSubstrate`), Spike #64/#122 (coherence/hallucination introspection), [[user_stance_whole_research_corpus_is_proof_not_single_arc]] (scale-invariant cosmos-math) · **User direction (2026-06-21):** "we need to do the research for it here since we've already got the environment primed" + (F900) "hash coherent string of words before they become sentences … glyph/byte scaffolding but can be introspected by scale invariance fractal things … did you keep this as sparse?"

## What this is
F900 (srmech session) established the reframe by encode-level measurement and lodged the **Open** decision: (a) prototype the recursive C1 + atom/compose dual + a `scale_signature` introspection through `RBSLMInferenceSubstrate` and measure, before any srmech change; or (b) graduate it as a srmech rc. The user directed **(a), here** (primed env). This finding is that prototype + measurement. **The number F900 was a known collision** (the srmech session's F900 stands as the reframe; my in-session byte/glyph-object probe was only ever called "F900" in `/tmp`, never committed) — this research lands as **F901**.

## The operator and its two duals (one definition, every scale)
```
pos_key(i) = klein4_random(seed=POS_BASE+i)            # role / position key
byte_atom(b) = klein4_random(seed=b)                   # bounded 256-byte codebook
compose(parts) = bundle_odd_i klein4_bind(part_i, pos_key(i))   # C1 — the ONE operator
atom(x)        = klein4_random(seed=sha256(x))         # the DUAL: content-address / identity
word_C1(w)     = compose(byte_atom(b)  for b in w)     # parts at level n+1 = composed vectors of level n
phrase_C1(ws)  = compose(word_C1(w)    for w in ws)
sentence_C1(ps)= compose(phrase_C1(p)  for p in ps)
```

## Measured (srmech rc13 klein4, D=8192, chance ≈ 0.25; numpy-absent)

**(1) C1 is self-similar — the SAME graceful 1-part-change band at every rung** (change one of n parts; similarity of whole vs changed):

| rung | n | sim(whole, 1-part-changed) | F900 @ D=2048 |
|---|---|---|---|
| byte→word | 8 | **0.745** | 0.733 |
| word→**phrase / skeleton** | 5 | **0.689** | 0.625 |
| phrase→sentence | 3 | **0.724** | 0.698 |

All three sit in one ~0.69–0.745 band → **C1 is genuinely scale-invariant** (self-similar across three scales), and reproduces F900's independent D=2048 result. The **"coherent word-string before a sentence" the user named is the phrase/skeleton rung — and it is scale-invariant under C1** (0.689).

**(2) the three operators differ — C1 is the unique scale-invariant, similarity-preserving one:**

| pair | C1 compose | atom-mint (word-hash) | chained-bind (the broken ladder) |
|---|---|---|---|
| cat / cot | **0.560** | 0.257 | 0.245 |
| walk / walked | **0.716** | 0.259 | 0.245 |
| run / running | **0.558** | 0.252 | 0.243 |
| cat / dog (unrelated) | 0.248 ✓ | 0.243 | 0.253 |

C1 grades by morphology and keeps genuinely-unrelated words at chance; atom-mint and chained-bind both collapse near-words to chance.

**(3) the atom/compose DUAL — two channels riding together (the user's "word-hash is a fractal form, keep it"):**
- **atom** (identity/address): `atom(cat)==atom(cat)` → **1.000** (exact content-address); `atom(cat)` vs `atom(cot)` → 0.257 (avalanche — a clean hash).
- **compose** (similarity/generalization): `word_C1(cat)` vs `word_C1(cot)` → **0.560** (graded).
- They are complementary: atom is the fast exact cache/identity; compose is the graded generalizer. Keep both at every level (atom is **not** the enemy — it is the address dual).

**(4) the scale_signature is a working introspection** ("introspected by scale-invariance fractal things"):
- **(a) it IDs the compositor:** the 1-part-change band is **0.745 for C1** (graceful) vs **0.250 for chained-bind** (collapsed). The signature tells you which operator built a unit — so a coherently-composed unit is recognizable by its self-similar band.
- **(b) it detects on-manifold coherence:** max-similarity of a unit to the rung's real vocabulary — **real-morphology OOV words (cats / runner / walking / lighthouse) 0.586** vs **gibberish (xqzwk / vmbgp …) 0.269** (2.2×). Coherent units sit **on** the self-similar manifold (they have neighbors at the level below); gibberish falls off it. This is a concrete coherence detector built purely from C1's scale-invariance — **coherence == scale-invariance, made measurable** (Spike #64/#122).

**(5) the recursive C1 ladder runs through the packaged `RBSLMInferenceSubstrate`** — `C1Context.enc = compose(byte_atoms)` injected (no package edit); `learn(400 tok)` + `infer` execute on the C1 word rung. **Integration confirmed.** (Inference *quality* is NOT claimed here — 400 tokens / k=2 / tiny vocab is a degenerate attractor regime for any encode, the same toy-regime caveat as the F900-era probes; a real inference-quality measurement is a separate axis needing a proper corpus, deferred.)

## Sparsity (kept — user: "did you keep this as sparse?")
Single fixed-D HV per unit (1/3/8/28-byte words all → one `HV` of length D, no growth); Klein-4 `{0,1,2,3}` state; only `klein4_random`/`bind`/`bundle`/`similarity`; numpy-free; **bounded 256-byte codebook + position keys** (vs word-hash's unbounded word-atom vocabulary). The fractal tree keeps each bundle within HDC capacity (~5 parts/level, never a flat 1000-wide bundle). Strictly sparse, per F900 §69.

## Verdict / next
**F900 Open(a) is DONE and the reframe holds under measurement:** C1 (role-filler bundle) is one scale-invariant compositor self-similar across byte→word→phrase→sentence; the atom/compose dual coexists (identity + generalization); the scale_signature is a real introspection (IDs the compositor AND detects on-manifold coherence, 2.2×); the C1 ladder integrates with the packaged inference object. Strictly sparse. **Still no package change.** **Open (the remaining fork, user's call — F900 Open(b)):** graduate to a srmech rc — a scale-invariant **`klein4_compose(parts)`** op (Python + C peer) + the `bigram/skeleton/sentence` ladder rebuilt on it + a **`scale_signature`** introspection surface, with **atom-mint kept as the explicit identity dual**. Two research extensions that would harden it first if wanted: **(i)** phrase/sentence-level coherence detection (real vs word-order-scrambled vs random-word strings) to push (4b) up the ladder; **(ii)** a non-degenerate-corpus inference-quality measurement of the C1 ladder vs word-hash (the proper version of the confounded F900-era OOV test).
