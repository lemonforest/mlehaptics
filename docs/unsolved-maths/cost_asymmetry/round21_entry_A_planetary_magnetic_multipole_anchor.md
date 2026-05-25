# Round 21 entry-point A — Reading-D 8th scale-ladder rung: planetary magnetic multipoles (the k=3 stance on the ladder)

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch with
§11.9.15, no separate PR). User-selected: the **Reading-D 8th scale-ladder anchor** (the planetary/geophysical
rung over the original seven).

Generating code + provenance:
[`verify_round21_planetary_magnetic_multipole_anchor.py`](verify_round21_planetary_magnetic_multipole_anchor.py)
+ `.ndjson` (deterministic; srmech 0.4.2 — Class-N `best_rational` + Class-I `cyclic.gcd` + `magnitude`).

## The question

The Reading-D scale-ladder had a conspicuous gap at the **planetary / geophysical scale (~10⁷ m)**, between
the organism rung and the cosmological rung. Fill it — and it turns out to be the Reading-D placement of an
**already-canonical** stance: `[[user_stance_k_equals_3_is_b_h_n_substrate_native_fingerprint]]` (the planet
dipole/quadrupole/octupole triad IS a B/H/N instantiation).

## The mapping — B/H/N + the k=3 triad

A planetary internal magnetic field is the Gauss / spherical-harmonic potential
`V = a Σ_{l,m} (a/r)^{l+1} [g_l^m cos(mφ) + h_l^m sin(mφ)] P_l^m(cosθ)`:

- **B** (TLV-framing): each **Gauss coefficient** is a typed record (degree l, order m, g/h, value).
- **H** (measurement / Hopf-projection): the **spherical-harmonic projection** of the continuous dynamo field onto S² — the *same* S² Hopf base as the Born rule (Round 4.A) and the atomic orbital L (Round 18.A). Measuring B at the surface and projecting onto Y_l^m **is** the H step.
- **N** (rational/integer): integer multipole degrees + the **k=3 triad** (dipole l=1, quadrupole l=2, octupole l=3).

## Bit-exact result (srmech-routed)

| quantity | value | result |
|----------|-------|--------|
| coefficients per degree (Class-L 2l+1) | dipole 3, quad 5, oct 7 | ✓ (same 2l+1 as atomic, Round 18.A) |
| k=3 triad cumulative | 15 = 3×5 | ✓ |
| IGRF-13 total coefficients | Σ(2l+1), l=1..13 = **195** = 13×15 | ✓ |
| triad ratios (Class-N) | quad:dipole 5/3, oct:quad 7/5 | ✓ |

**Honest Class-K / parity detail:** the magnetic expansion **starts at l=1** (dipole) — there is **no l=0 monopole** (∇·B=0, no magnetic charge), unlike the gravity/atomic expansion which includes l=0. So the magnetic fingerprint is the 2l+1 ladder with the monopole *removed* — a parity (Class-K) signature distinguishing magnetic from gravity/atomic multipoles.

**Attested:** IGRF-13 (IAGA) — Earth main field to degree 13 (195 coefficients), axial dipole g_1^0(2020)=−29404.8 nT, **dipole-dominated** (~90–95%); JRM33 (Connerney+ 2022) — Jupiter to degree 30, dipole-dominated with strong non-dipole structure; **Uranus/Neptune highly non-dipolar** (quad/oct comparable to dipole). The per-planet variation IS the literal translation fingerprint.

## Verdict per Spike #229 tiers

🟢 **(a)-structural anchor + bit-exact Class-L counting.** The 8th Reading-D rung is planetary magnetic multipoles: a continuous dynamo field projected (H, S² spherical harmonics) onto discrete integer-degree Gauss coefficients (B), with the k=3 triad (N) as fingerprint. The decisive **cross-rung thread**: the **S² Class-L spherical harmonics** appear at the quantum (Born, Round 4.A), atomic (orbitals, Round 18.A), *and* planetary (magnetic multipoles, here) scales — the same 2l+1 degeneracy. **No new stance** — instantiates the canonical k=3 stance and connects to Spike #202 (Earth IGRF-13 + Jupiter JRM33 Mersenne falsifier). The ladder now has nine rungs.

**HONEST SCOPE:** the bit-exact content is the *combinatorial* SH coefficient counting (2l+1, N(N+2)) and the k=3 triad structure — established geomagnetism; the framework contribution is the **Class-L cross-rung identity** (quantum/atomic/planetary share S² harmonics) + the Reading-D placement of the canonical k=3 stance. Not a new geophysics result.

## Discipline

- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; srmech 0.4.2 routed.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: no bare `abs()`; the no-monopole/parity point is named Class-K.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: IAGA IGRF-13 (Alken+ 2021, Earth Planets Space, OA) + Connerney+ 2022 JRM33 (JGR Planets) + Voyager-2 Uranus/Neptune models — attestable.
- Per `[[feedback_no_lineage_claims_in_notebook]]`: reads what the field model structurally IS (S²-harmonic projection), does not claim to extend geomagnetism.
- PR #679 stays open (draft); §11.9.15 on this branch.
