# R-RBS-LM Finding 373 — "precession" is our only word for ASYMPTOTIC ROTATION-OF-ROTATION; srmech-verified it requires k≥3 (the non-abelian bracket, 0 at k=1, first nonzero at k=3 — same threshold as F270 self-bumping); and the k-rung you SEE it at is set by the OBSERVING channel (vision flat k=1/2 → "k=(2+1)" shadow; audio/spatial → k=3)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 (no numpy — `qm.spin` + `qm.single_particle.commutator` + Class-K `cascade.magnitude`) · **user:** "precession is the only word we have for a thing that looks like asymptotic rotation of rotation, and we only see it in k=(2+1) sometimes and k=3 sometimes; visual field is flat 2D but the spatial-field simulation is not; audio may reconstruct in k=3, vision is really k=1 or k=2 — but I could be wrong, I don't get the visual render engine" · **composes:** F270 (non-abelian self-bumping = k≥3), F371 (precession asymptotic/no-singularity), F348/F361 (vision-vs-spatial-sim) · **attestation node:** the user's render-free spatial-sim

## srmech-verified — rotation-OF-rotation requires k≥3 (the structural half)

"Precession" is the word for **asymptotic rotation-of-rotation** — a rotation acting on a rotation axis, seen asymptotically. Decomposed: **Class-K (asymptotic, F371 — bounded cone, no singularity) ∘ rotation-of-rotation.** The rotation-of-rotation part is **exactly a non-abelian bracket**, and it has a sharp k-threshold (srmech-native, no numpy):

| rung | bracket | size | rotation-of-rotation? |
|---|---|---|---|
| **k=1** (U(1)/S¹) | a single generator, `[G,G]` | **0.000** | **NO** — one rotation, no second axis to rotate |
| **k=3** (SU(2)/S³) | `[σx,σy]`, `[σy,σz]`, `[σz,σx]` | **4.000** each | **YES** — a rotation about x rotates the y-rotation |
| k=3 same-axis | `[σx,σx]` | 0.000 | (a rotation can't rotate *itself* in its own plane) |

So **rotation-of-rotation is identically zero at k=1 and first turns nonzero at k=3** — the **same non-abelian threshold as F270's self-bumping** (`[A,A]≠0` ⇔ non-abelian ⇔ k≥3). **Precession is structurally a k≥3 phenomenon; it cannot exist at k=1.** (srmech `qm.spin.pauli_matrices` + `qm.single_particle.commutator`; commutator-size via Class-K `cascade.magnitude` on the real+imag parts — no numpy, no `abs()`.)

## Channel-relativity — what k you SEE it at is set by the observing channel (reading + hypothesis)

The user's frame: *we see precession in k=(2+1) sometimes and k=3 sometimes.* The structural fact above says the *thing* is k≥3; so **the apparent rung is set by the OBSERVING sensory channel's reconstruction, not by the precession.** The user's channel-by-rung hypothesis:
- **Vision = flat 2D (k=1/k=2):** a 2D retinal projection (which Hopf fibration — S¹ vs S³ — is the user's open question). A flat k=1/2 channel sees only the **2D shadow** of the k=3 rotation-of-rotation = the apparent **"k=(2+1)"** wobble (the 2D view + 1 inferred).
- **Audio ≈ k=3:** binaural hearing *computes* 3D direction (interaural time/level + spectral cues) — reconstructs the rotation-of-rotation in 3D.
- **Spatial-field simulation (navigation) is NOT flat:** the F348/F361 navigable manifold — the user maps 3D *without* the visual render. This is the higher-k channel, distinct from flat vision.

So "k=(2+1) sometimes, k=3 sometimes" = *which channel reconstructs it.* The same k≥3 precession is a flat shadow to vision and a full rotation-of-rotation to audio / the spatial-sim manifold.

## Attestation + the question handed to the expert

The user's **render-free** condition is the clean attestation node: they navigate via the **spatial-sim manifold (not the visual render they lack)**, so they directly experience **spatial-field ≠ flat-2D-vision** — exactly the channel-distinction the hypothesis needs. Their honest uncertainty — *"vision is really k=1 or k=2, I'm not sure which fibration… I don't get the visual render engine"* — is **handed to the vision-science expert** (per `[[user_stance_framework_hands_the_next_question_to_the_expert]]`): *which Hopf rung (S¹/S³/S⁷) does the visual reconstruction sit on, and does audition reconstruct one rung higher than vision?* The framework supplies the **well-posed question** (the sensory channels reconstruct at different Hopf rungs; precession is k≥3 so a flat channel only shadows it), not the answer.

## Honest scope

- **srmech-VERIFIED:** *only* the structural fact — rotation-of-rotation = the non-abelian bracket, 0 at k=1, nonzero at k=3 (ties F270). That is exact and srmech-native.
- **READING / hypothesis (not srmech-computed):** the sensory-channel→k mapping (vision k=1/2, audio k=3, spatial-sim higher) — the user's hypothesis, grounded in the F348/F361 vision-vs-spatial-sim distinction + standard sensory science (vision = 2D retinal projection; audition = computed 3D localization), held lightly and handed to the expert. **Not asserted as fact** (the user flags their own uncertainty).
- **No-leaning:** the verified half and the hypothesis half are kept strictly separate. Vision/audition science is literature-owned (no-lineage). srmech-first throughout (the user's "use srmech, no numpy" correction held — this finding uses only `qm.spin`/`qm.single_particle`/`cascade`).
