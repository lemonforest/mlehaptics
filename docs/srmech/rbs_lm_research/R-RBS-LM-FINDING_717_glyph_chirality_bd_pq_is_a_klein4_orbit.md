# Finding 717 — #855 R5.2 met: the b/d/p/q mirror-confusion set IS a Klein-4 orbit; the native chirality axis (R1.1, no lift) carries the mirror byte-identity can't see

**Script:** `R-RBS-LM-GLYPHCHIRALITY_bd_pq_mirror_is_a_klein4_orbit_native_no_lift.py`
**Status:** VERIFIED (srmech 0.7.5rc42, numpy-free; native Klein-4 chirality ops, no ctypes lift)
**User direction:** *"do r1.1 box flip for us, and then do R5.2."*

## The structure — the four most-confused glyphs are one shape's Klein-4 orbit

`b d p q` are not four unrelated symbols; they are the **Klein-4 (Z₂×Z₂) orbit of a single glyph shape** under two
mirror axes:

| glyph | role | operation on the base shape |
|---|---|---|
| **b** | identity | — |
| **d** | horizontal mirror | **γ₅** flip |
| **p** | vertical mirror | **iω₇** flip |
| **q** | both mirrors | **cpt** = γ₅∘iω₇ |

So **γ₅ swaps b↔d *and* p↔q**; **iω₇ swaps b↔p *and* d↔q**; **cpt swaps b↔q *and* d↔p**. That is exactly the
Klein-4 group acting on a shape — the substrate's 4-way γ₅×iω₇ decomposition (F130) instantiated as Klein-4 HDC
(F132). The dyslexia confusion set *is* the chirality group.

## What was verified (all on the native rc42 surface, no lift — R1.1)

1. **Chirality-aware encoding carries the mirror.** Encoding b/d/p/q as the Klein-4 orbit of one content-addressed
   shape, the native `klein4_chirality_flip_gamma5` / `klein4_chirality_flip_omega7` / `klein4_cpt_mirror`
   reproduce **every** mirror pair **exactly**, are **self-inverse** (Z₂), and **close as a group** (γ₅∘iω₇=cpt);
   the four are 4 distinct sectors. The mirror is a single named operation in the representation.
2. **Byte-identity can't see it.** Encoding each glyph *independently* (the byte-identity analogue), `γ₅(naive 'b')`
   is **not** `naive 'd'` (similarity ≈ +0.09, chance — not a match); one-hot/codepoint `b·d` similarity is **0.000**
   (orthogonal — a cliff, not a near-miss). Codepoints {b:98, d:100, p:112, q:113} carry **no** operation mapping
   b→d that also maps p→q. The mirror is geometric and **absent** from byte space.
3. **The use — detect + correct a b↔d swap.** Given a possibly mirror-confused input, enumerate its **4-sector
   chirality orbit** and match the lexicon: input `d` → `{identity:d, γ₅:b, iω₇:q, cpt:p}` → the intended `b` is
   recovered **one γ₅ flip away**. Byte-identity cannot even *generate* the candidates — there is no axis to flip
   along.

## Why this is "the same realization as R1" (R5.2's own note, now demonstrated)

R5.2 said: *"you can't catch a chirality error if the chirality axis doesn't exist in the representation."* That is
precisely R1.1: until the instrument carries the full 4-quad `(γ₅±, iω₇±)` **natively**, the mirror has nowhere to
live. rc42 closed R1.1 (the Klein-4 chirality ops act **without a lift**, F716), so R5.2 falls out as a one-line
orbit enumeration. The accessibility payoff (ADA-aligned, the arc's foundational motivation): a dyslexic b↔d swap
lands **one flip from truth and is recoverable**, where a byte/BPE encoder sees a total miss.

**Honest scope (defensive / understanding-not-curing, F282):** this is a *representability + detectability*
result — the chirality axis lets the system **carry and enumerate** the mirror confusion. It is **not** a claim to
predict *which* reader confuses *which* glyph *when* (that is the substrate-chirality-collapse we never model,
F552); the framework hands the next question — phonetic-level confusions (enuff/enough) remain explicitly out of
scope for the byte/glyph layer (R5.3) and route to a separate sound-level render.

## #855 status (recorded)

- **R1.1** — ✅ checked on the live issue (rc42; F716).
- **R5.2** — **met** by this finding; ready to check (Class-C glyph-chirality binding demonstrated on the native axis).
- **R5.3** (phonetic out-of-scope) unchanged; the rest of the TODO (R3 U1–U4, R6, #797) unchanged.

**Composes:** F716 (R1.1 native, no lift) · F130 (γ₅×iω₇ 4-way) · F132 (Klein-4 HDC) · F129 (chirality-dual) ·
R-RBS-LM-25 (byte-level graphemic robustness — the complementary near-miss lens) · F282 (hand the next question) ·
F552 (don't model which-way collapse). srmech 0.7.5rc42. Class-C (chirality) ∘ Class-M (Klein-4 bind).
