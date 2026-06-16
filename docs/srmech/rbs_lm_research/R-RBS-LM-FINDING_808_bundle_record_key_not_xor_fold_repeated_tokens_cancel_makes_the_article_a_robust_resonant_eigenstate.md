# F808 — the F807 dips were a self-inverse-bind bug, now FIXED: the context key was an XOR-fold (`klein4_bind`, which is its own inverse), so a token that REPEATS inside a context cancels its own identity (`the ⊕ the = 0`) and two different contexts sharing a repeated token COLLIDE. The fix is the canonical VSA RECORD — assemble the role-filler binds with a BUNDLE (superposition), not an XOR-fold. Result: the fixed-point accuracy (C) becomes MONOTONE and saturates at 100% from the determinism threshold onward — the article is a ROBUST resonant fixed-point eigenstate (input = output, F804) at EVERY k ≥ k*.

**Date:** 2026-06-16 · **srmech:** 0.7.5rc169 · **Provenance:** `R-RBS-LM-RESONKEY_…py` (read-only, simplewiki abstracts) · **Composes:** F807 (the non-monotonic dips), F806 (fiber confirmed; structure-matters: bundle for the small record, not the global store), F804 (resonance/eigenstate), F802 (the global-bundle null), F137/F146 (klein-4 capacity), the canonical VSA "record" (Kanerva/Plate: a struct = bundle of role⊗filler binds) · **User direction (2026-06-16):** "yes, do keep going please."

## The bug (why F807's (C) dipped after k_res)
F807's (C) was non-monotonic — it reached 100% at k_res then fell ~4–7% at higher k, which is combinatorially impossible (more context can only increase determinism). Traced to a single anomaly (april, k=8, position 11): **two different 7-gram contexts tied at similarity 1.0**, e.g.
- `(the, fourth, month, of, the, year, in)` → "the"
- `(fourth, month, of, the, year, in, the)` → "julian" (the true one)

Both contain "the" twice. The context key was `foldbind = klein4_bind(…)` over the role-filler binds, and **`klein4_bind` is XOR (Z2×Z2, self-inverse)**, so `bind(the,p_i) ⊕ bind(the,p_j) = p_i ⊕ p_j` — **the repeated token's identity CANCELS**, collapsing the key toward a position-only residue and colliding contexts that share a repeated token. Longer contexts are likelier to repeat a function word ("the"/"of"), so the collisions — and the dips — grow with k.

## The fix (the canonical VSA record)
A structured record is `bundle_j bind(role_j, filler_j)` — bind PAIRS role↔filler, BUNDLE (superposition) ASSEMBLES the record. We were XOR-folding the binds together instead of bundling them. Bundling does not cancel repeats: `bind(the,p0)` and `bind(the,p4)` are distinct vectors and superpose. Switching the context key from XOR-fold to `klein4_bundle` of the role-filler binds:

```
              k:   2    3    4    5    6    7    8
 april  XOR-fold: 77%  98%  96%  93% 100% 100%  95%   ← dips (repeats cancel)
        BUNDLE  : 77%  98% 100% 100% 100% 100% 100%   ← monotone, saturates 100%
 a      BUNDLE  : 74%  88% 100% 100% 100% 100% 100%
 august BUNDLE  : 83% 100% 100% 100% 100% 100% 100%
```

**(C) is now monotone and stays 100% from k\* onward** — the article is a ROBUST resonant fixed-point eigenstate (input = output) at every k ≥ k*, not just at isolated k. The deterministic walk is now dependable across k, not k-sensitive.

## What we learned
1. **A self-inverse bind cannot assemble a record with repeats.** XOR-binding (klein-4's group op) cancels any duplicated filler — fine for a one-shot pairing, fatal for a positional record where tokens repeat. The fix is structural, not parametric (no D increase, no cleanup iteration needed): use the right combiner.
2. **bind vs bundle is the role/record distinction.** `bind` pairs a role (position) with a filler (token); `bundle` assembles the pairs into the record. Conflating them (folding binds with bind) was the error. This is the canonical VSA record (Kanerva/Plate), now matched.
3. **Structure-matters, again (composes F806).** A bundle is right for the SMALL per-context record (≤ k-1 binds = the key); a single GLOBAL bundle over ALL transitions is wrong (capacity, F802/F806). Same op, opposite verdict by scale — bundle the key, address the store.

## Honest scope
- Short abstracts (28–49 tokens), 3 articles. The fix is structural so it should hold generally, but longer articles (more repeats, higher k*) and the full-article markup path (#225) are the next scale test.
- (C) is the instrument (fixed-point) metric; the deterministic generator is the clean walk, now exact at every k ≥ k* with the bundle key (no k-sensitivity). F806/F807 stand as the record of the XOR-key era (superseded here for the key only; their fiber/eigenstate findings are unchanged and now more robust).
- A cleanup/resonance ITERATION (F804 power-iteration) was NOT needed for these — the bundle record alone removed the collisions. Iteration remains the tool for harder regimes (longer contexts, near-ties at low k).

## Verdict
F807's non-monotonic dips were a self-inverse-bind artifact: XOR-folding the role-filler binds cancels repeated tokens (`the ⊕ the = 0`), colliding contexts that share a repeat. Assembling the context key as the canonical VSA RECORD — a BUNDLE of role-filler binds — removes the collisions, making the fixed-point accuracy (C) monotone and 100% from k* onward: the article is a robust resonant eigenstate (input = output, F804) at every k ≥ k*, and the deterministic RBS-HDC walk is now dependable across k. bind pairs, bundle assembles, context-addressed retrieval reads — and a global bundle still fails (F806): structure decides.
