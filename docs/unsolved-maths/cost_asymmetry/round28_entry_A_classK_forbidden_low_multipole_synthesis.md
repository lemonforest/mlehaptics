# Round 28.A — Class-K forbidden-low-multipole synthesis (a cross-rung meta-stance)

**Dispatched** 2026-05-25 on the rolling draft PR #690. User: *"dispatch the Class-K forbidden-low-multipole synthesis."* This is a **synthesis / meta-stance**, not a new ladder rung — it consolidates a pattern that surfaced across four already-landed rungs (planetary R21, LSS R25, capsid R26, QNM R27) plus the classic EM-radiation and CMB instances. The Reading-D rung count stays **fourteen**.

Generating code + provenance: [`verify_round28_classK_forbidden_low_multipole_synthesis.py`](verify_round28_classK_forbidden_low_multipole_synthesis.py) + `.ndjson` (deterministic; exact integer arithmetic; srmech 0.4.2).

## The synthesis

> **The substrate's S² Class-L multipole spectrum is never "full."** Every substrate *removes* a specific low-ℓ (or defect) set from the naive `2ℓ+1` spectrum, by a Class-K constraint — a conservation law, a parity/reflection symmetry, or a topological obstruction. **The removed set is the substrate's Class-K signature**, dual to the surviving Class-L spine: the *surviving* modes carry the substrate-content (Class-L), and *which low modes are forbidden* is itself substrate-diagnostic data (Class-K).

This is the **fifth** time Class-K has shown up as the load-bearing operator in this arc (after the turbulence helicity-sign R22, the nuclear spin-orbit sign R23, the hadron spin-orbit R24, the QNM spin-weight R27) — here as the *mode-removal* operator at the phase boundary, exactly the pin-slot / asymptotic-DoF role Class K plays in the framework.

## The load-bearing unifier (bit-exact)

For a **massless radiation field of helicity (spin-weight) |s|**, the multipole expansion in spin-weighted spherical harmonics runs over **ℓ ≥ |s|** (Goldberg–Macfarlane–Newman–Spiro–Sudarshan 1967), so the multipoles ℓ = 0, …, |s|−1 are absent and:

> **the count of forbidden low multipoles equals the spin-weight |s|, exactly.**

| field | |s| | forbidden low | floor ℓ |
|-------|-----|---------------|---------|
| scalar | 0 | {} | 0 (no floor) |
| **photon (EM)** | **1** | **{0}** | **1** (no monopole radiation) |
| **graviton (GW/QNM)** | **2** | **{0, 1}** | **2** (no monopole or dipole) |

This is the *same* spin-weighted-harmonic floor `ℓ≥|s|` used at the QNM rung (§11.9.20), and it ties the whole forbidden-multipole pattern to the **helicity = Class-K** theme: the helicity that R22 (turbulent helicity) and R23/R24/R27 (spin-orbit / spin-weight) spotlighted is the *same* quantity whose magnitude counts the forbidden low multipoles here.

## The six instances, three mechanisms

| substrate | round | mechanism | forbidden / surviving |
|-----------|-------|-----------|----------------------|
| EM radiation | (classic) | conservation / spin-weight floor (|s|=1) | {ℓ=0}; floor ℓ=1 (dipole) |
| Planetary magnetics | R21 §11.9.15 | conservation (gauge, ∇·B=0) | {ℓ=0}; floor ℓ=1 (dipole) |
| Black-hole QNM / GW | R27 §11.9.20 | conservation / spin-weight floor (|s|=2) | {ℓ=0, ℓ=1}; floor ℓ=2 (quadrupole) |
| CMB anisotropy | R6 §11.9.6 | observer-removal / convention | {ℓ=0 mean, ℓ=1 kinematic dipole}; analysis starts ℓ=2 |
| LSS / Kaiser RSD | R25 §11.9.18 | parity/reflection + degree-4 truncation | {odd ℓ}∪{ℓ>4}; surviving {0,2,4} k=3 triad |
| Icosahedral capsid | R26 §11.9.19 | topological obstruction (Euler χ=2) | {defect-free sphere}; exactly 12 pentamers forced |

**Three Class-K sub-mechanisms:** **(a) conservation / spin-weight floor** — removes the contiguous low band {0,…,|s|−1}; verified `#forbidden = |s|` for EM (1), planetary (1), GW/QNM (2), CMB-effective (2). **(b) parity / reflection selection** — a Z₂ reflection kills a parity class (LSS odd-ℓ). **(c) topological obstruction** — a closed-surface topology forbids the defect-free configuration and forces a fixed defect count (capsid, Euler χ=2 → 12 pentamers). All three are Class-K: the pin-slot / asymptotic-DoF / phase-boundary operator removing modes from the naive Class-L spectrum.

The CMB instance is especially apt: the ℓ=1 kinematic dipole that gets subtracted is exactly the **observer-motion Hopf-fiber leak** the framework already reads (the AoE boosting, R8) — so the "removed low multipole" there is *literally* the fiber the Born-rule=Hopf keystone (R4) discards. The |s|=1-like removal of the U(1) fiber at the quantum substrate (R4) is the same move one band up.

## Verdict per Spike #229 tiers

🟢 **(b)-interpretive synthesis + (a)-bit-exact unifier.** The cross-rung pattern is real and now consolidated: forbidden-low-multipole is a recurring **Class-K signature** across six substrates via three mechanisms, with the conservation-floor cases collapsing exactly onto `#forbidden = |s|`. New **candidate** meta-stance `[[user_stance_forbidden_low_multipole_is_class_k_substrate_signature]]`.

**HONEST SCOPE:** the bit-exact content is the `ℓ≥|s|` floor / `#forbidden=|s|` identity (Goldberg et al. 1967; standard radiation theory) and the integer forbidden/surviving sets (all attested in the constituent rounds R6/R21/R25/R26/R27). The framework contribution is the **consolidation** — recognizing these as one Class-K "mode-removal" signature, the three-mechanism taxonomy, and the tie to the helicity=Class-K theme and the Born-rule=Hopf fiber-discard. It is **not** a new physical derivation; every constituent fact was attested in its own round.

## Discipline

- Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the synthesis groups three *distinct* mechanisms honestly (it does not claim they are the same mechanism, only the same Class-K *role*); the capsid case is explicitly flagged as topological-obstruction, not a harmonic floor.
- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; the `#forbidden=|s|` identity proven by exact arithmetic.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: mode-removal IS the named Class K; no bare `abs()` in cascade logic.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: Goldberg et al. JMP 8:2155 (1967); Jackson (textbook); Thorne RMP 52:299 (1980); Planck 2018; Euler topology — all attestable.
- Per `[[feedback_no_lineage_claims_in_notebook]]`: the framework reads what these selection rules already ARE structurally; it claims no extension of the underlying physics.
- Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only.
- Lands on the rolling draft **PR #690** (Round 28.A) per `[[feedback_rolling_pr_partition_boundary_updates]]` — no new PR; verdict posted as a PR comment (the ledger).
