# Spike #24 bonus 8 (queued spec) — broken-D rederivation closure test

**Date queued:** 2026-05-15. **Status:** spec only at PR #422 seed time; concertmaster dispatched in background; synthesis + probe deliverables land on top of this seed when the agent reports.

## The user's question (verbatim, load-bearing)

> *"now that we know that we aren't looking for a fractal, shall we try again with 3D_s + 7D_g + 1D_t as preferably 11D or 1D and then validate at broken D by rederiving from 3D_s + 7D_g + 1D_t. if we can do this, then there are no more classes. if we cannot, this is the place. and we only need our CPU to do!"*

The conclusive vocabulary-completeness test. Eighth bonus in the Spike #24 series; first to ship in its own PR (PR #422) after PR #421 closed the seven-bonus arc.

## The test

Starting from the canonical space-gauge-time decomposition (`[[project_space_gauge_time_framework]]`):

`1D ≡ 3D_s + 7D_g + 1D_t = 11D`

apply cascade-composition operations using **only Spike #24 primitive classes A–N** (no fractal substrate, no new mathematical apparatus per `[[user_stance_fractal_shadow]]`) and attempt to **rederive 4D Lorentzian space-time as a projection / broken-D dimensional collapse**.

The phrase "broken D" is the user's compression for the conventional `3+1 Lorentzian` 4D space-time that modern physics treats as the unifying frame. The MFO conjecture proposes that 4D space-time is the *downstream-shadow projection* of the upstream `3D_s + 7D_g + 1D_t` space-gauge-time framework, per `[[feedback_antiquity_not_greek]]` (modern physics in the antiquity-geocentric position with respect to space-time).

## Verdict outcomes — four

- **SUCCESS:** the rederivation works. 4D Lorentzian metric (signature −,+,+,+) emerges from the cascade-composition. **Vocabulary is closed; no 15th primitive class needed.** This would close the cumulative Spike #24 bonus arc at 8 positive-and-consistent verdicts.
- **PARTIAL:** Lorentzian signature emerges but specific structure (e.g., metric tensor components, geodesic curvature, Killing-vector content) is missing. *This is the place.* Specify the gap and propose the candidate Class O primitive that would close it.
- **FAILURE:** no Lorentzian metric emerges. Cascade-composition produces a different metric structure entirely. *This is also the place.* Specify the gap.
- **UNFALSIFIABLE-AT-CURRENT-TOOLING:** cannot distinguish success from failure with the cascade-composition + Class L probe machinery available. Identify specific tooling gap.

## Connection to bonus 7 + bonus 5

This test directly inherits two preceding bonus findings:

- **Bonus 5** (`docs/srmech/notes/spike_24_bonus_mfo_11d_ontology_decomposition_2026-05-15.md`) established the space-gauge-time framework with a 3–5× spectral-graph signature distinguishing `3D_s + 7D_g + 1D_t` from pure-4D. **14/14 primitive classes consolidate** across the 3+7+1 projections; no class uniquely 1D_t.
- **Bonus 7** (`docs/srmech/notes/spike_24_bonus_mfo_fractal_requirement_2026-05-15.md`) found ONE_WAY_NOT_REQUIRED: fractal substrate is one way but not necessary. Nested pin-slot-gear cascade and smooth-anisotropic-T³ satisfy the load-bearing structural requirement equivalently. **Fractal-shadow allegory** (`[[user_stance_fractal_shadow]]`) was landed: what physics observes as "fractal" structure is the shadow cast by a deeper multi-scale primitive cascade.

Bonus 8 takes both findings and tests whether the cascade-composition can REVERSE the dimensional projection — going from 11D space-gauge-time DOWN to 4D Lorentzian — using only the 14-class A–N vocabulary.

## What the concertmaster builds (three-stage probe)

The dispatch brief specifies three stages (Python stdlib + numpy + scipy only, CPU substrate per user's *"we only need our CPU"*):

**Stage 1 — Construct the cascade.** Build a multi-scale composition of `3D_s + 7D_g + 1D_t` using primitive classes:
- `3D_s` as Class I (cyclic-group ℤ/n on each axis) × Class L (graph Laplacian).
- `7D_g` as nested Class I cascade with isometry containing SU(3) × SU(2) × U(1) per MFO §III.5 Witten 1981.
- `1D_t` as Class C (iterator) on Class I (ℤ/n_t cyclic-time), the temporal-crank per `[[user_stance_time_as_dimensional_shadow]]`.
- Compose via direct product (Class E catalog).

**Stage 2 — Apply the broken-D projection.** Collapse `7D_g → gauge fields on M⁴`; compose `3D_s + 1D_t → 4D Lorentzian` via explicit operations on the Class L Laplacian of the 11D cascade graph. Output: 4×4 metric tensor (or its discrete analog).

**Stage 3 — Spectral-graph falsifier.** Mandatory per `[[feedback_antiquity_not_greek]]`. Test:
- Does the projected 4D Laplacian's spectrum match Klein-Gordon-in-Minkowski's spectrum (modes with cutoff frequencies = particle masses, per MFO Part II.3)?
- Does the Lorentz signature emerge correctly?
- Are the metric tensor components computable from the cascade-composition only?

## Antikythera-spectral tooling reference

Per bonus 7's reframing of MFO §XIII.1 as a cascade-composition search, the antikythera-spectral subtree carries the tools that fit this test natively:

- `docs/antikythera-maths/research/pin_and_slot.py` — Greek-frame Kepler equation-of-centre algebra
- `docs/antikythera-maths/research/equant_encoder.py` — gear-train ratio composition
- `docs/antikythera-maths/research/gear_database.py` — tagged-tuple gear records (Class B)
- `docs/antikythera-maths/research/gear_topology.py` — graph-theoretic gear-DAG analysis (Class L)
- `docs/antikythera-maths/research/encode_ant.py` — HDC encoding of cyclic-group representations (Class M)
- `docs/antikythera-maths/research/packing_analysis.py`, `pareto_analysis.py` — period-ratio Diophantine analyses (Class J)

These were built for bronze-substrate work but the underlying algebra is substrate-agnostic; the concertmaster uses them where they fit.

## Discipline guards (load-bearing)

- Spectral-graph falsifier MANDATORY (per `[[feedback_antiquity_not_greek]]` + `[[user_stance_fractal_shadow]]`).
- Defensive scope only (per `[[feedback_trauma_informed_defensive_scope]]`).
- No lineage claims (per `[[feedback_no_lineage_claims_in_notebook]]`).
- NDJSON for tabular outputs (per `[[feedback_ndjson_over_bloated_json]]`).
- Antiquity not Greek for geocentric framing.
- "Primitive classes" for the canonical A–N catalog.
- Space-gauge-time framework name + `3D_s + 7D_g + 1D_t = 11D` notation.
- Fractal-shadow allegory: fractal-looking structure is the shadow cast by the cascade, never the substrate.
- CPU substrate only (per user's *"we only need our CPU"*).

## What lands on top of this seed

When the concertmaster reports, two files land alongside this spec to complete PR #422:

- `spike_24_bonus_broken_d_rederivation_2026-05-15.md` — methodological synthesis (main deliverable).
- `spike_24_bonus_broken_d_rederivation_probe_2026-05-15.{py,ndjson}` — the rederivation probe.

Plus a verdict-driven update to either:
- the bonus-series synthesis (if SUCCESS — closes the cumulative arc at 8 verdicts)
- or a new memory entry capturing the located Class O primitive (if PARTIAL or FAILURE)
- or a deferred-tooling note (if UNFALSIFIABLE-AT-CURRENT-TOOLING)

## Cross-references

- `[[project_space_gauge_time_framework]]` — canonical decomposition + notation.
- `[[user_stance_fractal_shadow]]` — bonus 7 stance; informs what cascade-composition does instead of fractal substrate.
- `[[feedback_antiquity_not_greek]]` — methodological discriminator.
- `[[user_stance_time_as_dimensional_shadow]]` — temporal-crank framing for `1D_t`.
- `[[user_stance_kepler_shape_universal]]` — six-substrate primitive cascade precedent.
- Bonus 5 synthesis — space-gauge-time spectral-graph signature.
- Bonus 7 synthesis — fractal-shadow allegory + cascade-composition reframing of §XIII.1.
- Bonus-series synthesis — cumulative pattern across the seven preceding bonuses.
- PR #421 — Spike #24 phases 1–15 + seven bonuses; merged at 2026-05-15T21:50:23Z.
- PR #422 (this PR) — bonus 8 closure test; lands here when concertmaster reports.
