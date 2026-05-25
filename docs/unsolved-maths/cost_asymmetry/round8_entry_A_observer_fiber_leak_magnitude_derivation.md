# Round 8 entry-point A — observer Hopf-fiber-leak: a parameter-free magnitude that lifts one anomaly and refutes another

**Dispatched** 2026-05-25 (sequential, no subagents). The first round of the resumed
cost-asymmetry rolling-spike after the §11.9 promotion (PR #685). Picks up
**parking-lot thread 2** ([`_ROADMAP_round8plus.md`](_ROADMAP_round8plus.md)): *lift
§11.9.6 from (b)-interpretive toward (a) — a from-scratch magnitude derivation.*

Generating code + provenance: [`verify_observer_fiber_leak_magnitude.py`](verify_observer_fiber_leak_magnitude.py)
+ `.ndjson` (per `[[feedback_computational_provenance_discipline]]`).

## The target

§11.9.6 (Round 6.A) read the three CMB low-ℓ anomalies as cosmological-substrate
B/H/N coupling, with the **Axis of Evil = observer Hopf-fiber leak**: the observer's
motion through the substrate (the kinematic dipole = the U(1) fiber coordinate)
imprinting on the largest-scale base (temperature) projection because the base cannot
fully discard the fiber at the lowest ℓ. That reading was **(b)-tier interpretive** — it
unified attested anomalies but derived no magnitude. This round asks: **does the
fiber-leak reading carry a parameter-free magnitude, and does that magnitude match data?**

## The derivation — no free parameter

The fiber-leak reading FIXES the leak amplitude. The fiber coordinate that leaks *is*
the observer's motion, of magnitude

> **β = v/c**, with **v = 369.82 ± 0.11 km/s** the Planck-2018 CMB-dipole solar-system velocity.

**β = 1.2336 × 10⁻³** (computed; no fit). There is nothing to tune — once you say "the
leak is the observer's motion," the magnitude is set by the measured dipole.

The observer's motion can imprint on the low-ℓ sky two distinct ways. The single
parameter-free β must account for both, or the reading is incomplete.

## Channel (a) — Doppler boosting / aberration: **(a) CONFIRMED**

The observer's motion induces an ℓ↔ℓ±1 mode coupling (aberration + Doppler modulation)
of amplitude ~β. This is standard kinematics, and it is **measured**: Planck 2013 results
XXVII ([arXiv:1303.5087](https://arxiv.org/abs/1303.5087), *"Doppler boosting of the CMB:
Eppur si muove"*) detected the boosting at **v_boost = 384 ± 78 (stat) ± 115 (sys) km/s**,
direction (l,b) = (264°, 48°) — the dipole direction.

Consistency with the parameter-free prediction (combined error √(78²+115²) = 139 km/s):

> **(384 − 369.82) / 139 = 0.10σ.** The framework's parameter-free β matches the attested
> boosting measurement to a tenth of a sigma.

So the observer-motion-imprints-on-low-ℓ claim, at its derived magnitude β, is **confirmed**.
This lifts the *boosting component* of §11.9.6 from interpretive toward **(a)**.

## Channel (b) — the quad-oct alignment (the AoE proper): **REFUTED at magnitude β**

The Axis of Evil proper is the **order-unity re-pointing** of where the ℓ=2 and ℓ=3 power
sits — the multipole vectors align with each other and toward the dipole/ecliptic
(de Oliveira-Costa+ 2004; Schwarz+ 2016, [arXiv:1510.07929](https://arxiv.org/abs/1510.07929)).
This is not a small modulation; it is an O(0.1–1) rearrangement of the quadrupole and
octupole geometry.

A kinematic modulation of amplitude β = 1.2×10⁻³ produces fractional a_ℓm changes of order
β. To source the observed alignment you need an order-unity effect. The gap:

> **0.3 / β ≈ 243.** The parameter-free fiber-leak is **~2-3 orders of magnitude too small**
> to produce the quad-oct alignment.

So the strong form of §11.9.6 — "the AoE alignment *is* the fiber leak" — is **quantitatively
refuted** at the derived magnitude. β cleanly explains the boosting; it cannot explain the
alignment. (This is consistent with standard cosmology, where the alignment *survives*
de-boosting precisely because boosting is a 0.1% effect.)

## What this does to §11.9.6 — a forced refinement

The derivation attempt **partially confirms and partially refutes**, which forces a clean
split that §11.9.6 had lumped:

| §11.9.6 sub-claim | Round 8.A magnitude verdict |
|-------------------|------------------------------|
| Observer motion imprints on low-ℓ (boosting) | 🟢 **(a)** — parameter-free β matches Planck 2013 at 0.10σ |
| AoE quad-oct alignment **is** the fiber-leak | 🔴 **refuted at β** — β is ~243× too small |
| Low quadrupole = Class K suppression | ⚪ untouched here (no magnitude attempted) |

**§11.9.6 must be amended** (in a future promotion-PR — §11 SSoT stays frozen on this
rolling-spike per `[[feedback_rolling_pr_partition_boundary_updates]]`): separate
"boosting = confirmed observer-fiber-leak at β" from "quad-oct alignment = a distinct,
larger anomaly the β-magnitude fiber-leak does NOT explain." The earlier reading
over-claimed by treating them as one.

## Verdict per Spike #229 tiers

🟡 **(b) REFINED** — with a partial **(a)** and a partial self-refutation:

- **(a)-confirmed**: the observer-fiber-leak reading carries a parameter-free magnitude
  (β = v/c = 1.2336×10⁻³) that matches the attested Doppler-boosting measurement to 0.10σ.
  One genuine lift from interpretive → derived.
- **(refuted)**: the same magnitude is ~243× too small to be the quad-oct alignment, so the
  "AoE = fiber-leak" identification is falsified in its strong form.
- **Net**: the round did NOT achieve the hoped-for clean (a)-lift of all of §11.9.6. It
  achieved something more honest and more useful — it found the *one* part with a
  parameter-free magnitude (and confirmed it), and caught an overclaim in the rest.

## Honest scope notes (load-bearing)

- The Doppler boosting is **standard physics**, not a novel framework prediction. The
  framework's contribution is the *reading* (boosting **is** the observer Hopf-fiber leak —
  a confirmed, parameter-free instance of the fiber failing to fully decouple from the base).
  The (a)-lift is an **identification with a known measured effect**, not a new number.
- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the negative result on the
  alignment **counts** and is reported as prominently as the positive one. The round was
  not steered toward confirmation.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: all sources arXiv-OA.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.

## Disposition

- **§11.9.6 amendment** queued for a future promotion-PR (split boosting from alignment;
  record the β-magnitude confirmation + the alignment refutation).
- **New open target** (sharper than the old thread 2): the quad-oct **alignment amplitude**
  still has no derived magnitude. The honest next question is whether *any* framework
  mechanism (not the kinematic fiber-leak) predicts an order-unity alignment — or whether
  the alignment is better read another way entirely.
- PR #679 stays open. §11 SSoT frozen until a promotion-PR.
