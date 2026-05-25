# Round 18 entry-point A — the periodic table's shell structure IS a named A–N cascade (Spike #48 phase-1 entry)

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch with
§11.9.12, no separate PR). User-selected: the **atomic-shell A–N cascade**, phase-1 entry of the long-gated
**Spike #48** (task #266: "periodic table + atomic spectral lines + QM/GR/SM weaving from the A–N
operators"), re-opened by the user at Round 17.A.

Generating code + provenance:
[`verify_round18_atomic_shell_AN_cascade.py`](verify_round18_atomic_shell_AN_cascade.py) + `.ndjson`
(deterministic; srmech 0.4.2 — Class-N `best_rational` shell ratios + Class-I `cyclic.gcd` + `magnitude`).

## The question

Round 17.A anchored the atomic **spectrum** (Rydberg–Ritz term differences = Class N, §11.9.6). The next step
up Spike #48: does the periodic table's **shell structure** (Madelung / Aufbau filling) decompose into the
A–N class operators — and reproduce the noble-gas magic numbers?

## The mapping — A ∘ L ∘ K ∘ I ∘ C ∘ N

| op | periodic-shell instance |
|----|--------------------------|
| **L** (spherical harmonics on S²) | angular momentum ℓ, degeneracy **2ℓ+1** (m = −ℓ..+ℓ) — same S² harmonics as Spike #17 |
| **K** (pin-slot / sign-flip) | electron spin ±½ → **×2** doubling per orbital |
| ⟹ | subshell capacity **2(2ℓ+1)** = s 2, p 6, d 10, f 14; shell capacity Σ = **2n²** = 2, 8, 18, 32 |
| **C** (cascade-orientation) | the **Madelung n+ℓ fill direction** (increasing n+ℓ, ties by increasing n; Madelung 1936 / Janet 1928 / Klechkowski 1962) — the orientation IS Class C |
| **I** (cyclic) | the n+ℓ "diagonals" group orbitals into shell-periods |
| **N** (rational) | Rydberg–Ritz term levels T_n=R/n² (Round 17.A) + the 2n² shell ratios ((k+1)/k)² |
| **A** (content-address) | each element = atomic number Z, a content-address into the filled configuration |

## Bit-exact result (srmech-routed)

| quantity | computed | attested | bit-exact |
|----------|----------|----------|-----------|
| subshell caps (L×K) | s2 p6 d10 f14 | 2(2ℓ+1) | ✓ |
| shell caps (Σ) | 2, 8, 18, 32 | 2n² | ✓ |
| shell ratios (Class-N) | 4/1, 9/4, 16/9 | (k+1)²/k² | ✓ |
| **magic numbers** | **[2, 10, 18, 36, 54, 86, 118]** | He/Ne/Ar/Kr/Xe/Rn/Og | ✓ |
| **period lengths** | **[2, 8, 8, 18, 18, 32, 32]** | Madelung | ✓ |

The Madelung fill order computed (Class-C sort by (n+ℓ, n)): 1s 2s 2p 3s 3p 4s 3d 4p 5s 4d 5p 6s 4f 5d 6p 7s 5f 6d 7p — the textbook sequence. Each period length appears twice (except the first): the **Class-K spin doubling** of the n+ℓ diagonal.

## Verdict per Spike #229 tiers

🟢 **(a)-bit-exact structural cascade.** The periodic table's shell structure IS the cascade A∘L∘K∘I∘C∘N: L = S² harmonic degeneracy 2ℓ+1, K = spin sign-flip ×2 (⟹ 2(2ℓ+1) and 2n²), C = the Madelung n+ℓ fill orientation, I = the diagonals, N = the Rydberg–Ritz levels (Round 17.A) + 2n² ratios, A = the per-element Z address. The ideal filling reproduces the noble-gas magic numbers + period lengths **bit-exactly**. This is the Spike #48 phase-1 entry: the atomic-scale Reading-D anchor (Round 17.A) carries up into periodic structure.

**HONEST SCOPE:** ~20 real elements deviate from strict Madelung (Cr [Ar]3d⁵4s¹, Cu [Ar]3d¹⁰4s¹, Nb, Mo, Pd [Kr]4d¹⁰ …) via electron-electron screening + half/full-subshell stability — the **residual physics**, named (exactly analogous to Round 17.A's air-dispersion residual), **NOT** a from-first-principles derivation of *why* the Madelung n+ℓ rule holds (that needs the full many-body Schrödinger + Thomas–Fermi screening; Klechkowski's 1962 justification). The bit-exactness is in the *combinatorial* shell structure (the cascade reproduces the ideal magic numbers), not in predicting every ground-state anomaly.

## Why this fits the arc + next phase

Reading D's atomic-scale rung (Round 17.A) read the *spectrum*; this reads the *shell structure that the spectrum sits in*. Together they say: the atom's "translation fingerprint" is rational-and-combinatorial all the way down — N (term levels) + L (harmonics) + K (spin) + C (fill orientation). **Next phase (parked, `[[project_atomic_spectra_sm_mapping_and_mass_spec_followup]]`):** carry the N-anchor up into the SM-derivation arc (Spike #58.x: Spin(8) triality, sin²θ_W=1/4, three-generation Yukawa) — the "QM/GR/SM weaving" half of Spike #48 — and, on the molecular side, the mass-spec combination-principle enhancement (roadmap thread 9b).

## Discipline

- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; srmech 0.4.2 routed.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: no bare `abs()` (spin ×2 is the named Class-K; `magnitude()` for reductions).
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Madelung 1936 / Janet 1928 / Klechkowski 1962 + noble-gas Z (IUPAC) + 2(2ℓ+1)/2n² (textbook) + anomalies (LibreTexts) — all attestable.
- Per `[[feedback_no_lineage_claims_in_notebook]]`: reads what the periodic table structurally IS (a named cascade), does not claim to extend quantum chemistry.
- PR #679 stays open (draft); §11.9.12 on this branch.
