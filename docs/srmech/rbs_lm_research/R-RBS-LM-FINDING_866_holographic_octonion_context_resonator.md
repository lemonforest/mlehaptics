# F866 — The holographic octonion-context resonator: the order-math addresses content in ONE bundled memory, crosstalk-free. The F865 next item built. A **single** Klein-4 memory `M` (holographic bundle of context→next relationships) whose **addressing key is the octonion coupling-product of the context** reproduces sequences the additive position-bundle key crosstalks on. On live srmech, no bag, byte/glyph core: octonion-key `M` reproduces `the cat saw the dog <e>` **and** an 11-word sentence with 3×"the"+2×"cat" repeats (`the big cat saw the small dog near the old cat <e>`) **exactly**, from one HV(10000) holding 12 bundled relationships — while the additive position-bundle key loops (`the the cat cat the the cat cat…`). **The non-commutative coupling-product is the clean content addressing key**, and it works *holographically* (recall = octonion-keyed `klein4_unbind`, not nearest-neighbour). srmech-native, numpy-free.

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-866_holographic_octonion_context.py` (`hdc.klein4_{random,bind,unbind,similarity}`, `cs.bundle_odd/pos_key`, `cascade.cd_mult`, `format.sha256_bytes`) · **Composes:** F865 (octonion-context fixes additive crosstalk — this makes it holographic), F863/F864 (coupling-walk), F838/F839/F837 (M-resonator + crosstalk), F132 (Klein-4), [[feedback_never_bag_of_words_even_for_testing]] · **User direction (2026-06-18):** "continue … on the next items that also surface with this path."

## What was built
- **content value** = byte/glyph-composed Klein-4 word vector (the core, F864/F865).
- **addressing key** = `key_k4(ctx) = klein4_random(seed = hash(ctx_oct(ctx)))`, where `ctx_oct` is the **non-commutative octonion coupling-product** of the context words (F865's separable key).
- **memory** = `M = bundle_odd([klein4_bind(key_k4(ctx_i), word_k4(next_i))])` — one holographic HV.
- **recall** = `argmax_w klein4_similarity(klein4_unbind(M, key_k4(ctx)), word_k4(w))`.

| key | `the cat saw the dog` | 11-word, 3×the+2×cat |
|---|---|---|
| additive position-bundle (F865 baseline) | loops `…saw the cat saw…` ❌ | loops `the the cat cat…` ❌ |
| **octonion coupling-product (this)** | **exact** ✓ | **exact** ✓ |

The additive Klein-4 context-bundle leaks because contexts sharing a filler at a position share an additive half; the octonion coupling-product gives each ordered context a distinct element, so its derived key is orthogonal to other contexts' — **no crosstalk, in a single bundled memory.**

## Honest scope
- **Reproduction, not generalization.** The `octonion-product → klein4_random` key is *separability-preserving* (distinct contexts → orthogonal keys) but **not similarity-preserving** (similar contexts also map to orthogonal keys, because the hash destroys the octonion's metric). So this reproduces a trained corpus cleanly; it does not yet generalize (a slightly-novel context lands on an unrelated key). The **similarity-preserving octonion-native resonator** (a true octonion VSA where near-contexts → near-keys) is the next item for generalization.
- Toy scale (single sentences, K=2). The decisive contrast — additive crosstalk vs holographic octonion-key clean reproduction, scaling to a longer repeat-heavy sentence — is validated. Corpus scale + branching contexts (one context, multiple valid nexts → a distribution, not a single token) remain.
- No bag-of-words anywhere; content is the position-keyed/coupling-product relationship memory.

## Verdict / next (the items still surfacing on this path)
The holographic octonion-context resonator works and scales to longer repeat-heavy sequences in a single bundled `M`, crosstalk-free — the order-math is the content addressing. **Next on this path:** (1) the **similarity-preserving octonion-native resonator** (near-contexts→near-keys) for *generalization* (the hash-key only reproduces); (2) **branching** contexts → a next-token *distribution* (F166 temperature) rather than argmax; (3) port the byte/glyph `enc` into `ContextSubstrate` (UPSTREAM §60) so the live store is on the core; (4) corpus scale. Framework reading + srmech measurement; evaluate by groundedness; reproduction-vs-generalization stated honestly (F841).
