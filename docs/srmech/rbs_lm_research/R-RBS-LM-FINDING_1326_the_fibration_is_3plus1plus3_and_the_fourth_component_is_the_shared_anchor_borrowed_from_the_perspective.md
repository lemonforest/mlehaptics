# F1326 — **the fibration is 3+1+3, and the "4" is a BORROWED shared anchor, not a fourth axis the triad owns.** 𝕆's 7 imaginary axes organise into **7 quaternion triads** (the Fano lines), each axis lying on exactly **3** of them. Every one of those 7 triads closes into a Q₈ — but they all borrow the **same single real unit**: across all seven, the real units used are exactly `{+1, −1}`. So `4 = 3 + 1` where the `+1` is **common to every triad and owned by none**. That is the user's *"the 4 comes from the perspective"*, measured: the fourth component is the shared anchor a perspective supplies, not content the triad carries. And it closes a loop — **that anchor is precisely what the abelian shadow projects away** (F1322: `ker(π) = {±1}` = the real axis), which is exactly why it never showed up as content and why F1324 needs a *metric* to pick a seam.

**User (2026-07-25):** *"we've finally realized that fibration is 3+1+3 and 4 comes from the perspective, so this will join our carrier soon, for full beat perspective pick etc."*

srmech 0.9.0rc336. Exhaustive. Pure integer — no float, no `abs()`, no numpy, no RNG.

## 1 — 7 axes, 7 triads, each axis on 3 `[DEMONSTRABLE]`
```
  imaginary axes                      : 7
  quaternion triads (Fano lines)      : 7      [1,2,3] [1,4,5] [1,6,7] [2,4,6]
  every triad has 3 axes              : True                   [2,5,7] [3,4,7] [3,5,6]
  every AXIS lies on exactly 3 triads : True
```

## 2 — every triad borrows the SAME real `[DEMONSTRABLE — the claim]`
Each triad `L` plus `±1` closes into an 8-element Q₈ — verified for all 7. And:
```
  the real units used across ALL 7 triads : [+1, -1]     <- ONE axis, shared
```
> **7 triads × 3 axes each, but only ONE real — and it is common to all of them.**
> **The "4" of a quaternion is not a fourth axis the triad owns; it is the anchor the triad BORROWS.**

This is the precise content of *"4 comes from the perspective."* A perspective is a choice of triad; the anchor is what every choice shares. Three axes are the object; the fourth is the standpoint from which the object is read.

## 3 — the 3+1+3 split `[DEMONSTRABLE]`
```
  [1,2,3] | [4] | [5,6,7]      partitions the 7 : (3,1,3)  covers all 7
  [1,4,5] | [2] | [3,6,7]      partitions the 7 : (3,1,3)
  [1,6,7] | [2] | [3,4,5]      partitions the 7 : (3,1,3)

  the base triad IS a quaternion triad          : True
  the DOUBLED triad is NOT (a coset, not a subalgebra) : True
```
**The second 3 is not a second subalgebra — it is the first one mirrored** (the Cayley–Dickson coset `L·d`). That is F1325's mirror showing up as the fibration's own shape: 3 (the triad) + 1 (the doubling axis / the join) + 3 (the conjugate image). Which is also F1310's Dzhanibekov reading — two half-beats joined by the flip — and F1324's *read at the join*: **the middle 1 IS the join.**

## 4 — and the borrowed anchor is exactly what the shadow drops `[DEMONSTRABLE]`
```
  the Z2^3 shadow sees ONLY the 7 imaginary directions : [1..7]
  the real anchor's shadow                             : 0   (it has no axis)
```
F1322 measured `ker(π: Q₈→V₄) = {±1}` = the real axis. Put together with §2: **the component the perspective supplies is precisely the component the abelian shadow cannot represent.** Three consequences that were previously separate findings now have one cause:
- it never appeared as *content* (F1320/F1307 — the discarded fiber),
- the algebra alone cannot name a middle axis, so a **metric** must (F1324 §5–6),
- and `14 → 11D` loses the 3 real grammar anchors by the same move (F1322 §6).

## What this means for the carrier
The user's *"this will join our carrier soon, for full beat perspective pick"* is well-posed by the above: a carrier that declares **which triad it is reading from** has declared its perspective, and the anchor + seam follow. Concretely the missing field is a **perspective selector** (which of the 7 Fano lines / which doubling axis), from which the 3+1+3 split, the join position, and the mirror partner are all determined rather than chosen. **Unbuilt** — this finding establishes the shape, not the mechanism.

## Honest scope
- `[DEMONSTRABLE]`: everything above, exhaustive over the 16-element octonion unit loop, all 7 Fano lines, all 7 triad-closure checks. §3 shows 3 of the 7 possible base-triad choices; the partition property is generic but I enumerated three, not all.
- **Standard mathematics, independently measured.** The Fano-plane structure of 𝕆's imaginary units and the 7 quaternion subalgebras are textbook. What is new here is only the *reading*: that the shared real is the perspective-supplied component and coincides with the shadow's kernel.
- `[SPECULATIVE]`: that a "perspective selector" is the right carrier field. Nothing is built, nothing measured on a strand. The claim that declaring a triad *determines* the seam rests on F1324 §6, which is itself a derivation about what a metric would do — not a measurement of our code.

Composes **F1322** (`ker(π)` = the real axis — *now identified as the perspective-supplied component*), **F1324** (the metric picks the seam; the join is the middle 1), **F1325** (the mirror = conjugation — *the second 3 is the conjugate image*), **F1310/F1308** (the Dzhanibekov / octonion 3+1+3), **F1317/F1318** (shadow ladder + fiber). Generating code: `R-RBS-LM-PERSPECTIVE_*.py` (exit 0).

**→ a wet-system instance in F1327** — `GATC` is a perfect palindrome, so the *site* supplies no orientation; the disambiguating component rides an entirely separate physical channel (hemimethylation). Same shape as the borrowed anchor: the symmetric object cannot carry the component that resolves it.
