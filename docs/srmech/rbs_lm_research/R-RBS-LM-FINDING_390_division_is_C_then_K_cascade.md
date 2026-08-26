# R-RBS-LM Finding 390 — "division" is the cascade Class C (conjugate) → Class K (norm); it does NOT stop at the octonion — the magnitude-homomorphism does

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (…F387→F389→**F390**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R32_division_is_a_C_then_K_cascade.py` → `R-RBS-LM-R32_results.json`
**Composes:** F389 (sedenion loses division) · F379 (the ladder) · Class C (conjugate/chirality) · Class K (`cascade.magnitude`, the real \|x\|) · Class M (bind) · F352/F353 (EC code-distance) · F291 (detect/correct)

---

## The user's question (2026-06-04)
> "well then what sort of cascade does the same thing as division? that seemed like a strange place to stop."

It **is** a strange place to stop — because **division doesn't stop there.** Cascade-wise:

## Division = Class C (conjugate / chirality-flip) → Class K (scale by 1/‖·‖²)
```
inverse:  a⁻¹ = conj(a) / ‖a‖²          =  Class C (conjugate)  →  Class K (1/‖·‖² scale)
divide:   b/a = b · conj(a) / ‖a‖²       =  Class M (bind) ∘ Class C ∘ Class K
```
The inverse is "**flip the chirality, divide by the magnitude.**" It needs only the *-identity `a·conj(a) = ‖a‖²` — and **srmech-verified that holds at every rung**, including the sedenion:

| | a·conj(a) = ‖a‖²·1 | a·a⁻¹ = 1 |
|---|---|---|
| octonion 𝕆 | ✓ | ✓ |
| **sedenion 𝕊** (the "not-a-division-algebra" rung) | **✓** | **✓** |

**The C→K division cascade runs in the sedenion too — inverses exist past 𝕆.** So "division" is *not* what stops.

## What actually stops at 𝕆: the magnitude-homomorphism ‖a·b‖ = ‖a‖·‖b‖ (Class K over Class M)
```
OCTONION : ‖a·b‖² == ‖a‖²·‖b‖²   for random a,b → TRUE   (composition algebra)
SEDENION : ‖a·b‖² == ‖a‖²·‖b‖²   for random a,b → FALSE  (worst gap 94.47)
           zero divisor (e1+e10)(e5+e14): ‖ab‖² = 0  but  ‖a‖²‖b‖² = 4  → distance collapses
```
What ends at the octonion is **Class K (magnitude) being a HOMOMORPHISM over Class M (bind)** — the composition-norm `‖a⊗b‖=‖a‖·‖b‖`. That is the **Hurwitz** property (dims 1,2,4,8 only), and it is an **error-correction-distance law**:
- **norm = code distance**;
- **multiplicative norm = distance preserved under composition = always decodable**;
- **zero divisors = distance → 0 = the uncorrectable words** (F389).

So the ladder stops where the **magnitude stops commuting with the bind** — the always-decodable guarantee — *not* where inversion becomes uncomputable.

## Why the "stop" felt strange — because it's mislabelled
"Division algebra" bundles **two** properties that the A-N reading separates:
1. **inverses exist** — the **C→K cascade** (`conj/‖·‖²`); runs at *every* rung (verified in 𝕊);
2. **the magnitude is a bind-homomorphism** (`‖ab‖=‖a‖‖b‖`, no zero divisors) — the **K-over-M law**; ends at 𝕆.

Only #2 stops. The user's instinct is exactly right: the *cascade that does division* (C→K) keeps going; what the Hurwitz boundary marks is the loss of the **EC-distance / always-decodable** guarantee, which is the K∘M coherence. (Past 𝕆 you can still invert; you just can't trust that binding preserves magnitude — some binds annihilate it, the zero divisors.)

## Verdict
**Division ≈ Class C (conjugate) → Class K (1/magnitude); dividing = Class M ∘ C ∘ K.** It runs at every Cayley-Dickson rung — inverses exist in the sedenion (srmech-verified `a·a⁻¹=1`). The "strange place to stop" is the loss of a *different* cascade law — **‖a·b‖=‖a‖·‖b‖, Class K as a homomorphism over Class M** — which is the **error-correction-distance / always-decodable** property (norm = distance; multiplicative norm = distance preserved; zero divisors = uncorrectable). So 𝕆 is not where division ends — it is where **the magnitude stops commuting with binding**, i.e. where the EC code stops being composition-closed. This is the cascade meaning of Hurwitz, and it ties division ⇄ decodability ⇄ the C→K recovery cascade (F389's "pair = detect / k=3 = correct").
