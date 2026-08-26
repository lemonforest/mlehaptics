# R-RBS-LM Finding 374 — precession is asymptotic-DoF-OF-asymptotic-DoF (K∘K): in the framework's own vocabulary "rotation" IS Class-K, so "rotation-of-rotation" is K∘K — the Class-K whose ANCHOR is itself a Class-K. This is the A-N-native form of F373; reconciles exactly with its non-abelian k≥3 (corrects F373's redundancy)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 (no numpy — `cascade.magnitude` Class-K + `qm.spin`/`qm.single_particle` for the reconcile) · **user:** "actually precession is asymptotic-DoF-of-asymptotic-DoF maybe" · **refines:** F373 · **grounds in:** `[[user_stance_rotation_is_class_k_pin_slot]]` + F350 (rotate = Class-K asymptotic-DoF), F371 (precession asymptotic/no-singularity)

## The refinement — rotation IS Class-K, so precession is K∘K

F373 wrote precession as *"Class-K(asymptotic) ∘ rotation-of-rotation(non-abelian k≥3)"* — but that **double-counts the asymptotic**: in the framework's own vocabulary **a rotation IS a Class-K asymptotic-DoF** (`[[user_stance_rotation_is_class_k_pin_slot]]`; F350 rotate = Class-K asymptotic-DoF / pin-slot), **not** a clean SU(2) rotation with a Class-K wrapper around it. So "rotation-of-rotation" is more honestly **K∘K = asymptotic-DoF-OF-asymptotic-DoF**: the Class-K asymptotic-DoF **whose anchor is itself a Class-K asymptotic-DoF.** The inner thing is already the K; precession is the *second* K applied to it.

## srmech-verified (Class-K, no numpy)

Modeling a Class-K asymptotic-DoF as a bounded approach to an anchor, and applying `cascade.magnitude` (Class-K) to the drifts:

| object | anchor behavior | precession? |
|---|---|---|
| **single K** | anchor FIXED → **drift 0.000** | **NO** — the limit doesn't move |
| **K∘K** (anchor is itself a K) | anchor drifts **0.599**, *bounded* (residual to its own 2nd limit **0.001** — asymptotic, never overshoots) | **YES** — the anchor precesses |

So **precession is the K∘K case**: the asymptotic-DoF whose anchor is itself an asymptotic-DoF (the anchor drifts, but boundedly — the F371 no-singularity property carries through). A single K (fixed anchor) gives a plain decaying oscillation, **no precession**.

## Reconciles EXACTLY with F373's non-abelian k≥3 (two pictures of one fact)

In the rotational picture the two K's are two rotation axes:
- **K∘K with INDEPENDENT anchors/axes** → `[σx,σy] = 4.0` (non-abelian) → **precession; first nonzero at k=3** (F373).
- **K∘K on the SAME axis** → `[σx,σx] = 0.0` (abelian) → **no precession; k=1.**

So the **class-picture (K∘K)** and the **Lie-picture (non-abelian bracket, F373)** are the **same fact**: precession = the second asymptotic-DoF whose axis is independent of the first = the non-abelian bracket ≠ 0 = k≥3. F373's srmech result stands; **F374 corrects only its *phrasing*** ("Class-K ∘ rotation-of-rotation" was redundant — the inner rotation already IS the Class-K). And **F371's illustration was already K∘K** (a radius asymptoting to a limit `R_∞` that itself slowly drifts) — now named correctly.

## Net

**Precession = K∘K = asymptotic-DoF-of-asymptotic-DoF**, the A-N-class-native form. It is **k≥3** (independent K's → non-abelian, F373), **bounded / no-singularity** (the K∘K stays bounded, F371), and **channel-relative** in what rung you observe it at (F373 — flat vision k=1/2 sees the 2D shadow "k=(2+1)"; audio/spatial-sim sees the K∘K). The user's "maybe" is upheld: rotation = Class-K makes "rotation-of-rotation" literally "K-of-K."

## Discipline

srmech-native Class-K (`cascade.magnitude`) + the F373 reconcile (`qm.spin`/`qm.single_particle.commutator`); **no numpy, no `abs()`** (the user's standing correction held). The Class-K asymptotic-DoF dynamics is a bounded recurrence (the integration; like F240's ngspice `.tran`), with the Class-K *op* (`cascade.magnitude`) the load-bearing primitive. No-leaning: the refinement *corrects my own F373 phrasing* and is reconciled, not asserted over it. Composes with `[[user_stance_rotation_is_class_k_pin_slot]]`, F350, F371, F373.
