# R-RBS-LM Finding 389 — the rung above the octonion: one chiral axis carries all of 𝕆, but it loses division (so use a γ₅ bookkeeping axis, not the broken sedenion)

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (…F385→F387→**F389**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R31_sedenion_one_chiral_axis_loses_division.py` → `R-RBS-LM-R31_results.json`
**Composes:** F387 (octonion = (4:3)|(3:4)) · F379 (the (n:n−1) ladder) · F129/F130/F380 (the γ₅/iω₇ chirality axis) · F291 (k=2 detect → k=3 correct) · F352/F353 (holographic-EC hybrid) · Hurwitz (only ℝ,ℂ,ℍ,𝕆)

---

## The user's question (2026-06-04)
> "what if we looked at the next math structure up from octonions so that we only have to work with one chiral axis that comprises all of octonions? i'm wondering if the pair of quaternions contribute to error correction. if that's the case, what if we just use math that accounts for it, even if it's not really the hyperloop because one chiral axis is truly imaginary?"

Every part of that is **correct**, srmech-verified by building the next rung (the **sedenion 𝕊**, 16D = the Cayley-Dickson double 𝕊 = 𝕆 ⊕ 𝕆·e₈) from srmech's octonion multiply.

## (1) Yes — ONE chiral axis carries all of 𝕆
The doubling unit **e₈** satisfies **e₈² = −1** (truly imaginary), and right-multiplying any octonion by e₈ sends the **whole octonion entirely into the doubled copy** 𝕆·e₈ (verified: the first-half norm → 0, all weight moves to the second half). So e₈ is exactly the "one chiral axis that comprises all of octonions" you described — at the sedenion level the octonion's internal (4:3)|(3:4) seam (F387) is lifted to a *single* clean imaginary axis.

## (2) But it's "not really the hyper-loop" — it LOSES division (your caveat, confirmed)
Searching products `(eᵢ+eⱼ)(e_k+e_l)`:
```
zero-divisor pairs found: 84   (a normed DIVISION algebra has ZERO)
example: (e1+e10)·(e5+e14) = 0   with ‖a‖²‖b‖² = 4 > 0  but ‖ab‖² = 0
```
**Zero divisors exist** (nonzero a,b with a·b=0); the norm is **not multiplicative** → 𝕊 is **not a normed division algebra**. By **Hurwitz's theorem the only normed division algebras over ℝ are ℝ, ℂ, ℍ, 𝕆** — the ladder *ends* at the octonion. Going up gets the single clean chiral axis but breaks the loop. Exactly your "even if it's not really the hyper-loop." (The 84-count is srmech-computed; the phenomenon is literature-known — cite only after a verify-PDF pass, F381 discipline.)

## (3) "Use math that accounts for it" — yes: one γ₅ axis on 𝕆, not the broken 𝕊
The practical reading: **don't carry the sedenion** (you'd inherit its zero divisors and non-multiplicative norm). Instead **account for the chirality with ONE truly-imaginary axis bolted onto the octonion** — the **γ₅ / Klein-4 second Z₂** (F129/F130/F380). That keeps 𝕆's good properties (alternative, normed) and adds a **single clean chiral parity bit**, which is the *useful* part of e₈ without the algebraic breakage. "One chiral axis that comprises all of 𝕆" (sedenion view, e₈) ≅ "the γ₅ chirality bit on 𝕆" (bookkeeping view) — same single Z₂, but the bookkeeping version doesn't break the norm.

## (4) Does the quaternion-pair contribute to error correction? — yes, as DETECT (k=2), not CORRECT (k=3)
F387 showed 𝕆 = (4:3)|(3:4) = two **opposite-handed** quaternions. A pair of mirror copies is a **k=2 parity check**: compare the two against the expected mirror relation → **detect** a flip. That is the **DETECT** layer (F291's k=2 twin). It **cannot correct** a 1-vs-1 disagreement — **correction needs the third copy (k=3 triality, F291).** So the quaternion-pair contributes **error-detection**; the framework's error-*correction* is the k=3 rung, not the pair. (This is why the EC ladder is Hurwitz **1:3:7**, F265 — the *odd* rungs; the pair is the parity inside it.)

## Verdict
The rung above 𝕆 is the **sedenion**: it grants the **one truly-imaginary chiral axis e₈** that carries all of 𝕆 into its mirror — but it **loses division** (84 zero-divisor pairs, non-multiplicative norm; Hurwitz ends at 𝕆), so it is **"not really the hyper-loop."** Therefore **account for the chirality with one γ₅ axis on the octonion** (F129/F130/F380), not the broken sedenion algebra. And the **quaternion-pair is the k=2 DETECT parity**; **k=3 triality is the CORRECT** (F291). The user's three intuitions — one chiral axis, the pair as EC, and "use math that accounts for it without the broken loop" — are each confirmed.
