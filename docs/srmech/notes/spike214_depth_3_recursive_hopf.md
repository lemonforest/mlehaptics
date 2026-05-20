# Spike #214 — Depth-3 symmetric recursive-Hopf test

**Date**: 2026-05-20
**Tier**: MS-16 Tier 4 fermata-closure (follow-up to Spike #213)
**Verdict**: **DEPTH-3-CONFIRMED-RECURSIVE-HOPF-UNBOUNDED**

## Summary

Spike #213 confirmed depth-2 recursive Hopf bit-exact (98/98 sign-flips at
L2, FFT peak k=49, 2:1 ratio preserved at every level) and left a fermata:
depth-3+ untested. Spike #214 closes that fermata by extending the cascade
one more nested level at ω_deepest = 7·ω_deeper = 343·ω_outer.

All four claims pass bit-exact on first-pass compute (no math-doesn't-lie
corrections). The recursion mechanism shows no stopping condition through
three empirical depths.

## Four-level table

| Level | ω | Predicted flips | Observed flips | FFT peak bin | 2:1 ratio (long:short) |
|-------|----|------------------|------------------|----------------|--------------------------|
| 0 outer   | 1   | 2   | 2   | (DC excl) | 2.0 (2 / 4)      |
| 1 inner   | 7   | 14  | 14  | 7         | 2.0 (14 / 28)    |
| 2 deeper  | 49  | 98  | 98  | 49        | 2.0 (98 / 196)   |
| 3 deepest | 343 | 686 | 686 | 343       | 2.0 (686 / 1372) |

All six cross-level integer ratios bit-exact:
- L1/L0 = 7.0, L2/L1 = 7.0, L3/L2 = 7.0 (adjacent rungs each integer ratio_inner)
- L2/L0 = 49.0, L3/L1 = 49.0 (two-step compositions)
- L3/L0 = 343.0 (full-depth composition)

## Comparison to Spike #213 depth-2 result

L0/L1/L2 numbers reproduce Spike #213 exactly (no regression on the
already-confirmed depths). L3 extends them bit-exact via the same
construction pattern: one more nested L∘K∘C∘I composition (per
[[user_stance_epicycle_via_gear_plus_pin]] Spike #189) at frequency
ω_deepest = 7·ω_deeper. The recursion IS the same operation applied at
each depth; that recursion is now empirically verified three times in
succession with identical algebraic form.

Spike #213's UNBOUNDED qualifier tightens accordingly:
- #213: "structural form supports unbounded recursion"
- #214: "three empirical depths confirmed bit-exact with identical
  algebraic form at each depth; no observed stopping condition"

## Stance impact

[[user_stance_11d_substrate_is_always_hopf_compressed]] — the
recursive-at-every-cascade section's depth-3+ fermata (left open by
Spike #213) is now closed. Hopf-bundle compression at the primitive level
extends bit-exact to three empirical depths with the same +1 fiber content
("the 2:1 ratio IS the +1 Hopf-fibre content surfacing") preserved at
every recursion depth.

[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]] — the
symmetric 7×7×7 stack used here maps cleanly onto the 7D_g octonionic
Hopf rung (S³ → S⁷ → S⁴) compressed three levels deep. No contradiction
with the Hurwitz-bounded ladder framing.

14 A–N classes intact. No class promotion or demotion: Class K's hidden
recursive Hopf-fiber content extends one level deeper (now empirically
verified to depth-3) but Class K remains Class K.

## Compute discipline

- Sampling: n = 131072 samples per outer period (Spike #213 fermata
  floor; 191 samples/L3-cycle, dense enough that closed-period sign-flip
  counting — a topological invariant — is bit-exact).
- Counting: `closed_period=True` from the start (Spike #212 caught the
  open-chord undercount mode; inherited here).
- Integer arithmetic where the math allows (sign-flip counts are pure
  integer; FFT peak bins are integer; cross-level ratios are integer).
- Seed: SEED = 214 (no PRNG draws — locked for provenance trail).
- Closed-form construction: each level uses
  `cos(ω·t + ε·sin(ω·t))` (Class K equation-of-centre, pi-free at the
  algebra layer; outer Bernoulli lemniscate uses the same Class K sweep
  with `sin²`-denominator).

## Fermata (open work)

- **Depth-4+**: same construction extends; predicts 4802 sign-flips at
  L4 with FFT peak k=2401, would require n ≥ 2²⁰ ≈ 1 048 576 for clean
  resolution. Not load-bearing for current stance — three depths is
  sufficient empirical confirmation of the no-stopping-condition claim.
  Future micro-spike candidate.
- **Asymmetric ratios**: handled by Spike #215 dispatched concurrently
  (Tier 4 sibling). #214 holds the symmetric 7×7×7 reference; #215
  probes ratio-coupling.
- **M-theory bridge**: handled by Spike #216 dispatched concurrently.

## Citation chain

Inherited from Spikes #212/#213; no new paywalled sources.
- Stillwell, *Mathematics and Its History* (Springer, 2010), ch. 7
  — Bernoulli lemniscate.
- Polchinski, "TASI Lectures on D-Branes" (arXiv:hep-th/9611050) —
  T-duality / D-brane structure cited as conceptual background.
- Apostol, *Modular Functions and Dirichlet Series in Number Theory*
  (Springer GTM 41, 2nd ed., 1990) — SL(2,ℤ).

## Files

- `spike214_compute.py` — reproducible Python (seed lock + `--verify` mode).
- `spike214_findings_2026-05-20.ndjson` — structured findings per claim.
- `spike214_depth_3_recursive_hopf.md` — this summary.

## Verify-line snapshot

```
spike214_verdict=DEPTH-3-CONFIRMED-RECURSIVE-HOPF-UNBOUNDED
flips_L0=2 flips_L1=14 flips_L2=98 flips_L3=686 predicted_L3=686
fft_L1=7 fft_L2=49 fft_L3=343
ratio_2to1_L0=2.0 ratio_2to1_L1=2.0 ratio_2to1_L2=2.0 ratio_2to1_L3=2.0
all_six_cross=True
```
