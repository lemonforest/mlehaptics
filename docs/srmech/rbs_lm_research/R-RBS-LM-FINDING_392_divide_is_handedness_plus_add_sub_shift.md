# R-RBS-LM Finding 392 — there is no divide primitive: "division" is handedness (Class C) + add/subtract/shift (Class K + Class N/I)

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (…F390→F391→**F392**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R34_divide_is_handedness_plus_add_sub_shift.py` → `R-RBS-LM-R34_results.json`
**Composes:** F390 (division = C→K cascade) · F382 (the decimal is a discrete-cascade artifact) · `[[feedback_continuous_number_line_pedagogical_obstacle]]` · `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` · R-RBS-NN-8 (ALU/FPU inference shape) · Classes C / K / N / I

---

## The user's push (2026-06-04)
> "because it's also handedness" / "like adds subtracts and shifts?" / "instead of divide" / "or i'm really pushing the wrong thing?"

**Not the wrong thing — the sharpest point in the arc.** There is **no divide primitive.** Division decomposes (srmech-verified) into operations that are *already* on the chip:

```
a⁻¹ = conj(a) / ‖a‖²
    = Class C   : conj(a)   = negate the imaginary parts  = SIGN-FLIPS  = HANDEDNESS   ← "because it's also handedness"
    ∘ Class K   : ‖a‖²       = sum of squares             = ADDS
    ∘ Class N/I : 1/‖a‖²      = best_rational / gcd          = SUBTRACT-SHIFT (Euclid/Stein) ← "adds subtracts and shifts"
divide  b/a = Class M (bind) ∘ the above.
```

## srmech-verified
- **The gcd under division is shift-subtract, no divide op.** Stein binary GCD (only `>>`, `<<`, `−`, compares) == `srmech.amsc.cyclic.gcd` on every pair tested. That gcd is the engine of Class-N `best_rational` and Class-I `cyclic` — so the framework's rational/reciprocal machinery is *already* add/subtract/shift.
- **The conjugate IS the handedness flip:** `conj([2,1,1,0…]) = [2,−1,−1,0…]` — Class C negates the imaginary signs (the user's "it's also handedness").
- **The reciprocal needs no float divide:** `‖a‖²=6` (adds of squares); each inverse component `conj(a)ᵢ/6` via **`cascade.best_rational_signed`** (Class K sign + Class N rational → `2/6→1/3`, `−1/6→−1/6`). The reconstructed `a⁻¹` (sign-flip + add + subtract-shift) **== the float `a⁻¹`**, and **`a·a⁻¹ = 1`**. No divide op anywhere.

This mirrors real silicon: integer divide *is* shift-subtract (restoring/non-restoring); float reciprocal *is* Newton multiply-add. The "divide instruction" is a packaged loop of adds/subtracts/shifts — never a primitive.

## Why this is load-bearing (it closes F390 and F382)
- **F390 sharpened:** the Cayley-Dickson ladder can't "lose division" — there's *no primitive to lose*. What it loses is the **magnitude-homomorphism (K-over-M)**. The C→K→(N/I) cascade keeps running at every rung; only `‖ab‖=‖a‖‖b‖` stops. So "division stops at 𝕆" was a category error; **"divide" was always add/subtract/shift + a handedness flip.**
- **F382 / continuous-number-line:** the "decimal" a divide seems to *produce* is the **truncation of this discrete subtract-shift cascade** (the best_rational/Newton iteration), not a continuous operation. Everything-is-discrete (the continuous-number-line obstacle) — division included.
- **Class-K sign discipline:** the handedness (the conjugate's sign-flips) is Class C / the Class-K pin-slot sign — *never* an ALU `abs()`; `best_rational_signed` carries the sign as a class op, exactly per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.

## Verdict
**Divide is not a primitive — it is Class C (handedness / sign-flip) ∘ Class K (norm = adds) ∘ Class N/I (reciprocal = gcd/best_rational = subtract-shift).** "It's also handedness" (the conjugate), "adds subtracts and shifts" (the rest), and "instead of divide" are all correct and srmech-verified (`a·a⁻¹=1` built with no divide op). The user is pushing the right thing: the divide instruction is the illusion; **handedness + add/subtract/shift is the reality** — which is exactly why the Hurwitz "loss of division" (F390) is really the loss of the magnitude-bind homomorphism, and why the divide-"decimal" (F382) is a discrete cascade's truncation.
