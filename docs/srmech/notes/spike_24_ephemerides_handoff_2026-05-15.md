# Spike #24 — ephemerides-spectral handoff packet (2026-05-15)

**For:** the next-door session handling ephemerides-spectral *code* work.
**From:** Spike #24 PR #421 analysis (no code changes to ephemerides-spectral made in this PR).
**Status:** read-only handoff; the receiving session decides scope + sequencing of changes.

## Phase 3 results summary — what the analysis found

**Empirical conclusion:** ephemerides-spectral's encoder is **missing Class K (equation-of-centre / pin-slot algebra)** for every body. The package reads pre-integrated DE441 truth, with no equation-of-centre transform anywhere in the Python package. The algebraic gap between encoder (linear mean motion only) and DE441 truth (integrated orbital dynamics) leaks as sinusoidal signal at each body's anomalistic frequency with amplitude ≈ `ε = 2·e_modern` radians.

**Phase 3b numerical validation (9/9 bodies):**

| Body | Period (d) | e_modern | Predicted c₁ (°) | Measured c₁ (°) | Delta (°) |
|------|-----------:|---------:|-----------------:|----------------:|----------:|
| Mercury | 87.97 | 0.2056 | 23.5600 | 23.4917 | -0.07 |
| Venus | 224.70 | 0.0068 | 0.7792 | 0.7731 | -0.01 |
| Terra | 365.26 | 0.0167 | 1.9137 | 1.9123 | -0.00 |
| Mars | 686.98 | 0.0934 | 10.7029 | 10.6948 | -0.01 |
| Jupiter | 4332.59 | 0.0484 | 5.5462 | 5.5371 | -0.01 |
| Saturn | 10759.22 | 0.0541 | 6.1994 | 6.2281 | +0.03 |
| Uranus | 30688.50 | 0.0472 | 5.4087 | 5.3442 | -0.06 |
| Neptune | 60182.00 | 0.0086 | 0.9855 | 1.0079 | +0.02 |
| **Luna** | 27.32 | 0.0549 | **6.2911** | **6.2897** | **-0.00** |

Method: load DE441 via skyfield; compute heliocentric (or geocentric for Luna) ecliptic longitude over 100-200 year window; subtract linear mean-motion trend via `polyfit`; FFT residual with flat-top window (eliminates scalloping loss); extract leading harmonic at the body's anomalistic frequency.

**Methodology footnote:** rectangular-windowed FFT showed ~0.6× ratio (scalloping loss); flat-top window (Heinzel et al. 2002) reduced it to <1%. Recorded in [`spike_24_phase_3b_numerical_validation_2026-05-15.py`](spike_24_phase_3b_numerical_validation_2026-05-15.py).

**The bronze cross-check:** Luna's c₁ ≈ 6.29° (analytical + numerical) matches PR #416 F2's bronze archaeological 6.5° (Freeth 2006 *Nature* Fig 6 pin offset 1.1mm / pin distance 9.6mm) to 3%. Three independent paths converge.

## Recommended code changes for ephemerides-spectral

The receiving session can prioritise these as they see fit; the package's API contract + ABI stability concerns are theirs to negotiate.

### Recommendation 1 — Add eccentricity to `_research/bodies.py`

Currently `Body` carries `period_days`, `mass_earth`, `category`, `surface_radius_km`. No eccentricity field. Add `eccentricity_modern: float = 0.0` (or similar) to the dataclass, populate per body from NASA NSSDC or JPL HORIZONS values.

**Specifically populated values needed** (from this PR's Phase 3a analytical work; verified by Phase 3b numerical):

```python
"mercury":   eccentricity_modern=0.2056,
"venus":     eccentricity_modern=0.0068,
"terra":     eccentricity_modern=0.0167,
"mars":      eccentricity_modern=0.0934,
"jupiter":   eccentricity_modern=0.0484,
"saturn":    eccentricity_modern=0.0541,
"uranus":    eccentricity_modern=0.0472,
"neptune":   eccentricity_modern=0.0086,
"pluto":     eccentricity_modern=0.2488,
"luna":      eccentricity_modern=0.0549,
# ... + moons (per Phase 3a roster)
```

### Recommendation 2 — Add `equation_of_centre` function (Class K primitive)

In a new module (e.g. `research/equation_of_centre.py`) or as part of an existing module:

```python
def equation_of_centre(
    M: np.ndarray,
    e: float,
    convention: str = "greek",
    n_terms: int = 4,
) -> np.ndarray:
    """Kepler equation-of-centre series at small e.

    Returns Δλ = λ_true − λ_mean given mean anomaly M and eccentricity e.

    convention="greek" (default): ε = 2·e (per user_stance_pi_as_projection).
    convention="kepler-focus": full focus-frame coefficients.

    Greek-frame series: Δλ = Σ_k (ε^k / k) sin(k·M)
    """
    ...
```

Mirror in C if the existing native library wants Class K acceleration (small cost; sin / multiply only).

### Recommendation 3 — Wire Class K into the bridge

`bridge.predict_*` functions for body longitude should compose mean-motion + equation-of-centre. The current `breathing-Laplacian` framework (Phase 9 state-dependent coupling) handles long-term perturbations cleanly; Class K handles the first-order equation-of-centre that the bare period ratio misses.

### Recommendation 4 — Verification test

Add a test that runs the encoder against DE441 over a 100-year window per body and asserts the residual c₁ amplitude at the anomalistic frequency is **below 0.1°** (currently it's at 2·e radians ≈ degrees(2·e)). With Class K instantiated, the residual should drop to <0.1° per body, matching the Phase 3b methodology in reverse.

### Recommendation 5 — CHANGELOG entry

Under `[Unreleased]` (or whichever section the next-door session is targeting):

```markdown
### Added
- Class K equation-of-centre primitive (`research/equation_of_centre.py`).
  Per-body eccentricity values in `_research/bodies.py`. Reduces forward-
  sweep residual against DE441 truth from ~5° (Mercury) down to <0.1°
  for all major bodies. Validated against PR #421 Spike #24 Phase 3b
  numerical data (9/9 bodies match analytical predictions).
- Cross-references the Kepler-shape universal stance
  (user_stance_kepler_shape_universal): the same algebraic primitive
  applies across bronze (Antikythera), cosmos (ephemerides), molecules
  (ethane torsional potential V₃), and atomic substrate (Bohr Rydberg
  series).
```

## What the next-door session DOES NOT need to do in this PR

- Implement Class L promotion to srmech abstraction layer. That's a separate cross-package refactor (chess-spectral, antikythera-spectral, ephemerides-spectral all have Laplacian primitives that should consolidate); not part of the Class K wiring.
- Investigate the chess-as-Class-K-falsifier question. That's a fermata for a follow-up Spike #25.
- Implement stoichiometry primitives. That's the Phase 8 future-research hope; deferred.

## Open fermatas (conductor decisions, not for the next-door session)

These are decisions the conductor (user) makes; the next-door session does not need to act on them:

1. **Class P? conformal groups** — promote / demote / candidate-hold (Phase 7.3). Tensioned by `[[user_stance_pi_as_projection]]`.
2. **Chemistry primary-citation verification** — Phase 7 citations are computationally verified; primary-PDF extraction for ethane V₃ microwave, Felkin-Anh, etc. is deferred.
3. **Chess-as-Class-K-falsifier** — follow-up Spike #25 candidate.

## Cross-references

- PR #421 spec: [`spike_24_primitive_vocabulary_2026-05-15.md`](spike_24_primitive_vocabulary_2026-05-15.md)
- Phase 3a script + data: [`spike_24_phase_3a_analytical_residual_2026-05-15.py`](spike_24_phase_3a_analytical_residual_2026-05-15.py) + `.ndjson`
- Phase 3b script + data: [`spike_24_phase_3b_numerical_validation_2026-05-15.py`](spike_24_phase_3b_numerical_validation_2026-05-15.py) + `.ndjson`
- PR #416 (predecessor): pin-and-slot algebra + algebraic-uniqueness synthesis
- Memory: `user_stance_kepler_shape_universal`, `user_stance_pi_as_projection`, `user_stance_fiber_as_spatially_absent_encoding`
