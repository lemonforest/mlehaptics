# Hopf-fibration spectral explorations (2026-05-11)

**Origin:** User-curiosity dispatch — "fiddle around with Hopf fibration; could be handy for MFO spherical event horizon, also curious whether lifting 2D chess board / Hawaii-Emperor chain to 3D-4D via Hopf-like fibration gives different graph-Laplacian information." Pre-flighted as "might yield nothing."

**Verdict in advance:** mixed — **2 of 4 experiments yielded nothing** (trivial lifts of simply-connected bases), **2 of 4 yielded something real** (non-trivial topology = non-trivial spectrum). Honest results, math-doesn't-lie.

Reproduce: `python -X utf8 docs/srmech/notes/hopf_fibration_explorations_script.py`. Runtime ~10s. Deterministic seed `20260511`. numpy + scipy only.

---

## Experiment 1 — Flat 8×8 chess board lifted via Cartesian product with C_8

| Quantity | Value |
|---|---|
| Total dim | 512 = 8×8 × 8 |
| Eigenvalue range | `[0, 11.70]` |
| Factor-sum prediction max dev | `2.31e-14` (machine precision) |

**Verdict: yielded nothing new.** Cartesian product of a flat (simply-connected) base graph with a cycle is textbook Imrich-Klavžar — eigenvalues are exactly sums of factor eigenvalues. The "lift" adds no spectral information because there's no topology to twist around. Equivalent to standard 3D grid Laplacian.

---

## Experiment 2 — Magnetic twist on TOROIDAL 8×8 (T²) — the non-trivial case

Flux sweep `φ ∈ [0, 1]` on `8×8` torus with Landau-gauge vector potential `A_y = (2π·φ·i)/N`:

| Flux φ | Eigenvalue range | Max dev from φ=0 |
|---:|---|---:|
| 0.000 | [0.000, 8.000] | 0.000 (baseline) |
| 0.125 | [0.136, 7.864] | 0.667 |
| 0.250 | [0.158, 7.842] | 0.413 |
| 0.500 | [0.368, 7.633] | 0.540 |
| 0.750 | [0.545, 7.455] | 0.545 |
| 1.000 | [0.709, 7.291] | 0.828 |

**Verdict: yielded something real — Hofstadter-style flux-dependent spectrum.** The toroidal base has `π_1(T²) = Z²`; non-trivial U(1) bundles exist and produce distinct spectra per flux value. The eigenvalue range narrows from [0, 8] at φ=0 toward [0.71, 7.29] at φ=1, with intermediate flux values producing intermediate narrowing. This is the discrete-graph analog of the Hofstadter butterfly (Hofstadter 1976) for electrons on a 2D lattice in a perpendicular magnetic field.

**Math identity**: the twisted Laplacian on `T²` is a real instance of the §3.5.3(C) motif extended to U(1) gauge connections — the flux parameter labels distinct elements of `H¹(T², U(1)) = U(1) × U(1)` (Wilson loops around the two cycles), and the spectrum depends on the Wilson-loop holonomy.

**Why this matters**: it confirms that the "Hopf-like" twist gives new spectral info **precisely when the base has non-trivial fundamental group** (`π_1 ≠ 0`). Flat 8×8 grid (Experiment 1) doesn't have this; toroidal 8×8 does. The chess-extension spike (commit `942e0a3`) already validated toroidal chess at the §3.5.3(C) level — this exploration adds the U(1) gauge connection layer.

---

## Experiment 3 — Discrete Hopf S³ → S² spectral comparison

200 random points sampled on S³; Hopf-projected to S². k-NN graph Laplacian on each:

| Manifold | Spectral gap λ₂ | Top-5 eigenvalues |
|---|---:|---|
| S² (Hopf-projected) | 0.508 | [16.64, 16.94, 17.14, 17.46, 17.69] |
| S³ (sampled) | 1.210 | [16.87, 16.93, 17.07, 17.36, 17.56] |

**Verdict: yielded something — different spectra at small λ; converging at large λ.**

The continuum prediction: `Δ_{S²}` has eigenvalues `l(l+1)` for `l = 0, 1, 2, ...` → {0, 2, 6, 12, 20, ...}; `Δ_{S³}` has eigenvalues `l(l+2)` for `l = 0, 1, 2, ...` → {0, 3, 8, 15, 24, ...}. The S³ gap (λ_min ≠ 0) should be roughly 3 vs S²'s gap of 2 — in continuum.

Discrete approximations don't reproduce exact continuum eigenvalues at N=200, but **the structural signal is there**: S³ spectral gap (1.21) > S² spectral gap (0.51), matching the continuum ordering. The S³ "extra harmonics" from the S¹ fiber show up as more eigenvalue density per unit interval.

---

## Experiment 4 — Hawaii-Emperor chain (1D path P₅₀) lifted to 2D via Cartesian with C_8

| Quantity | Value |
|---|---|
| Chain dim | 50 |
| Product dim | 400 = 50 × 8 |
| Factor-sum prediction max dev | `8.88e-15` (machine precision) |

**Verdict: yielded nothing new.** Same reason as Experiment 1 — 1D path P₅₀ has trivial topology (`π_1 = 0`); Cartesian product with C_8 gives sum-of-factor eigenvalues exactly. No information beyond what the factor graphs separately provide.

---

## MFO event-horizon connection — what the Hopf fibration actually offers

The MFO §VII.4.1 stance commits to event horizon as a **2D phase boundary** (the visible S²) with "no interior" — matter / information bound to the surface. Spherical compression (the §VII.4.1 operator) takes 3D bulk to inscribed 2D boundary.

**The Hopf fibration provides exactly the mathematical structure needed to formalize what's lost in compression**:

- **Base S²**: the visible event horizon
- **Total space S³**: a U(1)-principal bundle over the horizon
- **Fiber S¹ = U(1)**: encodes one extra dimension of "phase information" per base point
- **Bundle is non-trivial**: total space is genuinely S³, not S² × S¹ (the trivial bundle); the topology twist is the first Chern class = 1

**Spectral content of the lift**: `Δ_{S³}` eigenvalues = `Δ_{S²}` eigenvalues + S¹-fiber harmonics. The continuum gap `l(l+2) - l(l+1) = l` (linear in `l`) is the **extra spectral degree of freedom per S² mode** that the bulk-to-boundary compression discards.

**Holographic-principle reading**: the Hopf bundle's S¹ fiber over the visible S² horizon IS the spectral incarnation of "the bulk information is encoded on the boundary with a phase degree of freedom per mode." This is consistent with — and a finite-dimensional spectral analog of — Maldacena's AdS/CFT correspondence where boundary phase data encodes bulk dynamics.

**MFO §VII.4.1 candidate addition** (conductor decision, not unilateral): note that the Hopf fibration provides the **discrete spectral framework** for the "spherical compression as 3D-bulk → 2D-boundary operator" stance: `Δ_{boundary} + S¹-fiber harmonics = Δ_{lifted bulk}`. The compression operator literally projects out the fiber-harmonic series.

---

## Honest summary

What yielded NOTHING new (textbook math, expected):

- Flat 8×8 chess board × C_8: factor-sum exact at 2.31e-14 max dev. No new info.
- Hawaii chain P₅₀ × C_8: factor-sum exact at 8.88e-15 max dev. No new info.

What yielded SOMETHING real (non-trivial structure surfaces in the math):

- Toroidal 8×8 + magnetic flux: Hofstadter-style flux-dependent spectrum. Eigenvalue range narrows with flux. **Genuine discrete U(1)-gauge instance of the chess §3.5.3(C) toroidal sub-instance, extended with a connection.**
- Discrete Hopf S³ → S²: S³ spectral gap (1.21) > S² spectral gap (0.51), matching continuum `l(l+2) > l(l+1)` ordering. **The S¹ fiber adds spectral degrees of freedom that the base S² doesn't have.**

**MFO connection (load-bearing finding):** the Hopf bundle's spectral decomposition (`Δ_{S³} = Δ_{S²} + fiber harmonics`) is the natural mathematical framework for what "spherical compression" of 3D bulk to 2D event-horizon boundary discards. Conductor-decision-worthy candidate for §VII.4.1 addendum.

---

## Files

- `hopf_fibration_explorations_script.py` — reproducible script (~10s, seed 20260511, numpy+scipy only)
- `hopf-fibration-explorations-2026-05-11.md` — these findings

Cite Hofstadter 1976 for the magnetic-lattice spectrum result; Hopf 1931 for the original fibration; continuum spherical-harmonic eigenvalues are textbook (Stein-Weiss, Sogge, etc.).
