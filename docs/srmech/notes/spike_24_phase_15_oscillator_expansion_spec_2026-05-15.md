# Spike #24 Phase 15 — dual-formulation × dual-rigour oscillator-set expansion

**Spec drafted:** 2026-05-15. **Status:** dispatched.

## Goal

Phase 9.2 confirmed Kepler-shape signature in 3 oscillating chemical systems (Lotka-Volterra, Brusselator, Oregonator) at chemistry-dynamics substrate. User scope-expansion request: add 3 more oscillator domains (CIMA, glycolysis, calcium signaling) with **dual-formulation honoring** (per `[[user_explanation_discipline]]` — two canonical sources both fit the bill → both honored as validation/falsification opportunity) and **dual-rigour pedagogy** (find bounds, look for siloing-induced deviations).

## Roster — 12 runs

| Domain | Formulation A (textbook-reduction) | Formulation B (biochem-honest) | Rigour Level A | Rigour Level B |
|--------|-----------------------------------|--------------------------------|----------------|----------------|
| **CIMA** | Lengyel-Epstein 1991 (2-var activator-inhibitor) | Citri-Epstein 1987 (4-var: ClO₂⁻ + I⁻ + ClO₂ + I₂) | 5000 cycles + Hann + parabolic interp | 50000 cycles + Welch + 95% CI |
| **Glycolysis** | Sel'kov 1968 (2-var ADP-F6P-ATP) | Goldbeter 1972 (3-var allosteric: F6P + FBP + AMP) | same | same |
| **Calcium** | Goldbeter-Dupont-Berridge 1990 (2-var: cytosolic + ER) | De Young-Keizer 1992 (~9-state: 8-state IP₃R + Ca²⁺ + IP₃) | same | same |

Total: 3 domains × 2 formulations × 2 rigour levels = **12 cells**.

## Methodology per cell

1. **Set up:** integrate the ODE with parameter values chosen to produce sustained limit-cycle oscillation (no damping, no chaos). Document the parameter set + reference for the choice in each script.
2. **Rigour-A:** integrate 5000 cycles (`t_final ≈ 5000 · T_cycle`), Phase 9.2-style — FFT with Hann window, parabolic peak interpolation, extract top-K harmonic ratios, no confidence interval.
3. **Rigour-B:** integrate 50000 cycles, Welch's method (50% overlap, 100-segment averaging), 95% confidence intervals on harmonic amplitudes via bootstrap, statistical significance test (p < 0.05 against null of pure noise) per harmonic peak.
4. **Detect Kepler-shape:** top-K harmonic ratios = {1.0, 2.0, 3.0, ...} within tolerance (Rigour-A: ±0.05; Rigour-B: within 95% CI of integer).
5. **Per-cell verdict:** Class K confirmed (clean integer ratios) | Class K confirmed-with-extras (integer ratios + non-integer peaks above noise) | Class K absent (no integer-ratio pattern).

## Cross-comparison axes

- **Textbook-vs-biochem within domain** (3 comparisons): does the biochem-honest formulation show ADDITIONAL harmonic peaks the textbook reduction obscures? DIFFERENT ratios? SAME structure?
  - **Hypothesis** if vocabulary keeps consolidating: same Kepler-shape ratios in both, biochem-honest may show extra peaks at non-integer frequencies that are *additional* phenomena not previously catalogued.
  - **Hypothesis** if siloing IS load-bearing: textbook and biochem disagree on Kepler-shape detection; the textbook's reduction is the artifact.
- **Rigour-A-vs-Rigour-B within formulation** (6 comparisons): does the cheap-and-fast method agree with the expensive-and-rigourous one? Phase 9.2's method validation.
  - **Hypothesis** if Phase 9.2 method is sound: 6/6 agreement on Kepler-shape verdict; Rigour-B refines harmonic-amplitude precision but doesn't change the verdict.

## Deliverables

- 6 Python scripts (one per (domain × formulation) pair, each handling both rigour levels):
  - `spike_24_phase_15_cima_lengyel_epstein_2026-05-15.py`
  - `spike_24_phase_15_cima_citri_epstein_2026-05-15.py`
  - `spike_24_phase_15_glyc_selkov_2026-05-15.py`
  - `spike_24_phase_15_glyc_goldbeter_2026-05-15.py`
  - `spike_24_phase_15_calcium_gdb_2026-05-15.py`
  - `spike_24_phase_15_calcium_dyk_2026-05-15.py`
- 6 NDJSON output files (one per script, each emitting per-rigour-level records).
- 1 cross-comparison NDJSON: `spike_24_phase_15_crosscompare_2026-05-15.ndjson` — textbook-vs-biochem deviations per domain + rigour-A-vs-rigour-B agreement per formulation.
- 1 Phase 15 section in findings doc.

## Dependencies

- `numpy`, `scipy.integrate.solve_ivp` (already used in Phase 9.2).
- No new external packages required.

## Bounded scope guards

- If a parameter set fails to produce sustained oscillation (decays to fixed point, or goes chaotic), document that as a finding and try one alternative parameter set per literature reference. Do not parameter-sweep exhaustively — pick the canonical published value and report.
- Statistical-significance test (Rigour-B) requires longer integration; the 50000-cycle target means integration may take several minutes per system. That's acceptable.
- DYK 1992 is the most complex (9-state with stiff dynamics near CICR-locking); use `LSODA` or `Radau` if `RK45` struggles.

## Connection to Spike #24

Phase 9.2 confirmed Kepler-shape at chemistry-dynamics with 3 systems. Phase 15 expands to 9 total systems with method-validation + dual-formulation honoring. If 9/9 (or even 8/9 with one defensible outlier) confirm Kepler-shape, the universal stands stronger. If textbook-vs-biochem disagreements surface, the vocabulary still consolidates *or* a new substrate-boundary phenomenon surfaces — either outcome is honest landing of the learning the user requested.
