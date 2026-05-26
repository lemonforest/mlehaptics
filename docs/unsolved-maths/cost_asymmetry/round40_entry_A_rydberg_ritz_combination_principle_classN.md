# Round 40.A — Spike #48 deeper-SM phase, honestly scoped: the combination principle is one Class-N structure across atomic + mass spectra

**Dispatched** 2026-05-26 on the rolling draft PR #690 (open-queue item: the long-gated Spike #48 "periodic-table + spectral-lines + QM/GR/SM weave," task #266). Generating code: [`verify_round40_rydberg_ritz_combination_principle_classN.py`](verify_round40_rydberg_ritz_combination_principle_classN.py). Tested per `[[feedback_dont_pre_commit_spike_query_operators]]`.

## The tractable, real deliverable — one Class-N combination principle, two substrates

- **Atomic (Rydberg–Ritz, Ritz 1908):** a spectral line is a **difference of terms**, `ν̃ = T_n − T_m`, with terms `T_n = R/n²`. The terms are **Class-N anchors** (small-integer-denominator `1/n²`); lines are their differences.
- **Molecular (mass spec, Round 39.A):** a fragment-peak spacing is a **difference of substructure masses** (neutral losses) — small integers in nucleon space = **Class-N anchors**; peaks are their differences.

**Same Class-N combination principle** — "spectral features are *differences* of a discrete ladder of anchors" — on two substrates (term-energy space vs nucleon-mass space). This unifies **Round 39.A** (mass spec) + **Round 17.A** (atomic Balmer ratios) + **§11.9.14** (mass spec = "molecular Rydberg–Ritz") under one reading; mass spec *is* the molecular Rydberg–Ritz, made explicit.

**Bit-exact:** Balmer lines as exact Class-N rationals (`1/4−1/9 = 5/36`, `1/4−1/16 = 3/16`, `1/4−1/25 = 21/100`); `Hα = (5/36)·R_H = 15233 cm⁻¹` (656.3 nm; `R_H = 109677.58 cm⁻¹` hydrogen, kept distinct from `R_∞ = 109737.31 cm⁻¹`); line ratios `Hα/Hβ = 20/27`, `Hα/Hγ = 125/189` (srmech `best_rational` confirms).

## Honest scope on Spike #48's full "QM/GR/SM weave"

| component | status |
|-----------|--------|
| periodic-table **shell** structure | **Class-L** — already §11.9.12 (Madelung / `2n²`) |
| periodic table + SM share Hurwitz `1+3+7` / Hopf ladder | already §11.9.13 |
| atomic spectral **lines** | **Class-N** combination principle — this round + Round 17.A |
| **SM derivation** (gauge group, masses, mixing) | the **separate Spin(8)/triality arc** (Spikes #58/#85/#86) — **NOT derivable from atomic spectra, NOT claimed here** |

So Spike #48's **QM/atomic-structure weave is substantially addressed** (Class-L shell + Class-N lines + the Hurwitz tie); the **SM-derivation proper is explicitly out of reach of spectra** and remains the Spin(8) arc. Spike #48's "deeper SM phase" is **partially delivered** (the QM/spectra consolidation) with the SM-derivation honestly bounded out.

## Verdict per Spike #229 tiers

🟢 **(a)-bit-exact Rydberg–Ritz Class-N rationals + (b)-interpretive atomic↔molecular combination-principle unification + honest Spike #48 scoping.** New **candidate** stance `[[user_stance_combination_principle_is_one_classN_across_atomic_and_mass_spectra]]`. **HONEST SCOPE:** (a)-bit-exact for the Rydberg rationals + ratios (Ritz 1908; NIST ASD); (b)-interpretive for the unification; the **SM-derivation is explicitly NOT claimed** — the round's contribution is the unification + the honest Spike #48 boundary, not a new SM result. `R_H`/`R_∞` kept distinct.

## Discipline
- Honest Spike #48 scoping — the QM/spectra weave delivered, the SM-derivation explicitly bounded out (the separate Spin(8) arc).
- Bit-exact only for the Rydberg rationals; Ritz 1908 / Bransden–Joachain / NIST ASD (Explore-verified).
- Lands on rolling **PR #690** (Round 40.A); unsolved-maths §11.9.33. No MFO section (atomic-structure/QM, not metric-field — consistent with the recursive-check discipline).
