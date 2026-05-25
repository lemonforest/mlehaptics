# Round 12 entry-point A — the (a)-lift attempt: the offset must be a HANDED SHEAR, not a displacement; amplitude stays open

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch
with its §11.9.6c notebook edit, no separate PR). The real (a)-lift attempt for the alignment
(parking-lot **thread 2‴**): *derive w₂, w₃ — and why p=2,3 not p=1 — from the off-centre-observer
Hopf-bundle geometry.* It genuinely could land or fail; it **partly fails, informatively**.

Generating code + provenance: [`verify_offset_geometry_degree_selection.py`](verify_offset_geometry_degree_selection.py)
+ `.ndjson` (deterministic Gauss-Legendre; srmech 0.4.2 Class L cross-check, native active).

## The degree/parity selection (rigorous, bug-free)

A geometric distortion that is a degree-`g` polynomial in the direction cosine μ=cosθ (about the offset
axis) deposits into Legendre multipoles ℓ≤g of matching parity. Verified by quadrature:

| distortion degree g | physical object | deposits into ℓ |
|---|---|---|
| 1 | **displacement** (aberration) | **1 only** (dipole) |
| 2 | **shear** (anisotropic geometry) | 0, **2** |
| 3 | **cubic / handed** | 1, **3** |

So: **p=2 requires a shear (degree ≥ 2); p=3 requires a cubic term (degree ≥ 3); BOTH p=2 and p=3 require
a mixed-parity distortion of degree ≥ 3 = a HANDED SHEAR** (a shear that breaks reflection symmetry — a
swirl). A literal off-centre *position* (degree-1 → dipole only) **fires the Round 11 falsifier**.

## Where this lands — the attested mechanism class

A handed shear / anisotropic-with-vorticity geometry is **exactly the Bianchi type VII_h template** long
used to fit the CMB large-angle anomalies. Jaffe, Banday, Eriksen, Górski & Hansen 2005, *ApJ* 629:L1
([astro-ph/0503213](https://arxiv.org/abs/astro-ph/0503213)) — titled *"Evidence of vorticity and shear at
large angular scales in the WMAP data"* — found a ~3σ Bianchi VII_h correlation that, when removed, reduces
the low-quadrupole, quad-oct alignment, and cold-spot anomalies together. The word **"shear"** is literally
in the attested title; the degree-selection argument lands on the right physical object independently.

## Honest scope — the (a)-lift is NOT achieved, two ways

1. **Framework side:** the round derives the mechanism *class* (handed shear, degree ≥ 3) and the *parity
   structure* (why p=2,3 and why a displacement/dipole fails) — but it does **not** derive the amplitudes
   `w₂, w₃` from Hopf-bundle first principles. Those are the shear + handedness magnitudes, which remain
   **free parameters** (exactly as the Bianchi template's parameters are fit, not derived).
2. **Physical-viability caveat (attested):** the *physical* Bianchi VII_h best-fit is **incompatible with
   ΛCDM** — a Markov-chain analysis ([astro-ph/0605325](https://arxiv.org/abs/astro-ph/0605325)) finds the
   best-fit Bianchi model needs Ω_tot ≈ 0.43, inconsistent with independent constraints; and the original
   vorticity claim was challenged on gauge-invariance grounds ([astro-ph/0503562](https://arxiv.org/abs/astro-ph/0503562)).
   So the attested mechanism class itself carries an unresolved physical-viability problem.

## Verdict per Spike #229 tiers

🟡 **(b) REFINED + (open).**

- **(a)-grade sub-result:** the degree/parity selection — displacement (g=1) → dipole only, shear (g=2) →
  quadrupole, both-p2-and-p3 → handed shear (g≥3, mixed parity). Exact, bug-free, srmech-Class-L
  corroborated. The displacement reading is **falsified** (Round 11 falsifier fires as predicted).
- **(open):** the alignment *amplitude* `w₂, w₃` is **not derived** — the geometric reading now lives or
  dies on whether the off-centre-observer Hopf-bundle geometry produces a handed shear at the observed
  amplitude, AND the attested shear-template (Bianchi VII_h) is itself in tension with ΛCDM. This is the
  honest floor: the framework reading is *consistent with* the literature's attested AoE mechanism (shear)
  and *shares its open problem* (no derived/physical amplitude).

**Net across Rounds 8–12 on the AoE:** boosting = confirmed fiber-leak at β (8.A); the alignment is NOT
the kinematic leak (9.A) and NOT ℓ=7-Mersenne (10.A); it requires a p=2,3 offset (11.A); that offset must
be a **handed shear** (12.A) = the attested Bianchi VII_h class — whose amplitude neither the framework nor
the literature has derived, and whose physical model is contested. The arc has driven the AoE down to a
single, sharply-posed, literature-anchored open question rather than a vague one.

## srmech routing (per user direction + CLAUDE.md §2)

srmech 0.4.2 (updated this session from a stale 0.4.0 install; native active). The multipole decomposition
is a Class L eigenbasis projection; cross-checked through `srmech.amsc.laplacian` (cycle-graph Class L
eigenvalues match analytic). Continuous Legendre/spherical-harmonic remains a flagged srmech catalog
candidate (asymptotic_calculus covers exp/sin/cos/log1p/atan, not spherical harmonics).

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the (a)-lift's **non-achievement is stated as
  prominently as the (a)-grade sub-result**; the physical-viability caveat is included, not hidden.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: all citations arXiv-OA, verified this session.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; the selection is
  exact, not a fit.
- PR #679 stays open (draft); §11.9.6c rides this branch (consolidated model).
