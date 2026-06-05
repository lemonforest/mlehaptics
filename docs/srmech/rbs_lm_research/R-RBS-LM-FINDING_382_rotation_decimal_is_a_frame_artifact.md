# R-RBS-LM Finding 382 — the rotation "decimal" is a FRAME-MISMATCH artifact; map it to its own frame and it's exact

**Date:** 2026-06-04
**Arc:** RBS-LM · FFT-ladder thread (F377→F378→F379→F380→F381→**F382**)
**srmech:** 0.7.0rc28 · **Provenance:** `R-RBS-LM-R24_rotation_decimal_is_frame_artifact.py` → `R-RBS-LM-R24_results.json`
**Composes:** rotation-is-Class-K (`[[user_stance_rotation_is_class_k_pin_slot]]`, F350) · continuous-number-line obstacle (`[[feedback_continuous_number_line_pedagogical_obstacle]]`) · π-as-cascade · F380 (the QDFT flat shadow) · F361 (observer co-rotates)
**→ extended by F401** (the (2+1)-rotation decimal *was* the projected fiber; lift = exact) **and F404** (the decimal is the rotation *shadow* carried by N; 2:4:8 = 2ⁿ shift-exact IFF 1:3:7:3 carries it).

---

## The user's insight (2026-06-04)
> "in (2+1) rotation is always the asymptote and creates a decimal because we aren't prepared to map this to a new cartesian coordinate of its. what if we did?"

**Correct, and it splits into two regimes.** A rotation is **Class-K** living on **S¹ (cyclic, Class I)**. Read in a *fixed* Cartesian frame it is (cos θ, sin θ) — a transcendental **decimal**. That decimal is the **cost of reading an S¹ object in a frame that doesn't co-rotate with it**, not a property of the rotation. (Even srmech's `cos_series_truncate` returns a `num/denom` *rational pair* — the "decimal" is already a truncated cascade, never a continuous primitive.)

Two-layer resolution: (1) **co-rotate** to the eigenbasis — the off-diagonal decimals (cos, sin) vanish, leaving only the angle θ (this is F361's "observer rotates too"); (2) then θ itself splits:

### (A) RATIONAL rotation → maps EXACTLY to its own Cartesian = the cyclic lattice Z_q (Class N → Class I)
```
cartesian reading 0.375  →  best_rational(375,1000,16) = (3,8)  =  element 3 of Z₈
compose two 3/8-turns in its own frame:  mod_add(3,3,8) = 6   (EXACT integer; the decimal is GONE)
```
The decimal was *pure frame-artifact*; in Z₈ the rotation is the integer 3 and composition is integer mod-add.

### (B) IRRATIONAL rotation → no single finite frame; its own coordinate is the best_rational CASCADE (Class N)
Golden (φ−1 = 0.618…) → the Fibonacci convergents, exact to any depth, denominators →∞:
```
3/5 (err 1.8e-2) · 5/8 (7.0e-3) · 8/13 (2.6e-3) · 13/21 (1.0e-3) · 34/55 (1.5e-4) · 89/144 (2.2e-5) · 233/377 (3.1e-6) …
```
The decimal **is the limit of this discrete cyclic-frame cascade** — π-as-cascade applied to rotation: not a continuous mystery, a discrete cascade's asymptote.

## What this is, named
"Map it to a new Cartesian coordinate of its own" **= Class N (`best_rational`) → Class I (`cyclic`)**, already shipped. The (k, n) it returns *is* that coordinate. Honest line between regimes: **rational** → one exact finite frame; **irrational** → exact to any chosen depth, the decimal as the convergent-cascade asymptote (never collapses to one integer in the same dimension). The *other* door is the **dimension-lift ℂ→ℍ→𝕆 (the (n:n−1) ladder)**: more couplings = more room for the rotation to sit simply.

## Tie to the live thread
Same structure as F380, one level down: **the decimal is to a rotation what the flat shadow is to a Klein-4 object — a projection artifact of a frame too small for it.** Both dissolve by giving the object its native frame (the cyclic/quaternionic coordinate), not by adding precision in the wrong frame.

## Verdict
The (2:1)-rotation decimal is a frame-mismatch artifact. Rational turns are exactly integer in their own Z_q; irrational turns are the Class-N convergent cascade whose limit is the decimal. "Mapping to its own Cartesian" is Class N→I (stay in-dimension) or the ℂ→ℍ→𝕆 lift (raise the dimension). **(F382 is the number-level statement; F383 lifts it to the substrate.)**
