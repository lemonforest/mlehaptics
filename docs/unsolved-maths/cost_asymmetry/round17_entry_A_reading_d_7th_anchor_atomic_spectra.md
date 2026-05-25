# Round 17 entry-point A — Reading-D 7th scale-ladder anchor: ATOMIC SPECTRAL LINES (the literal "translation fingerprint")

**Dispatched** 2026-05-25 (sequential, no subagents; consolidated model — lands on the PR #679 branch with
§11.9.6 amended, no separate PR). A **fresh** target (user-selected): add a 7th rung to the Reading-D
quantum→cosmological scale-ladder (§11.9.6), which had six anchors and a conspicuous gap at the **atomic
scale** between the abstract 3-qubit Born-rule anchor (Round 4.A) and the molecular/biology rungs.

Generating code + provenance:
[`verify_reading_d_7th_anchor_atomic_spectra.py`](verify_reading_d_7th_anchor_atomic_spectra.py) + `.ndjson`
(deterministic; srmech 0.4.2 — Class-N `best_rational` line-ratio anchors + Class-I `cyclic.gcd` fraction
reduction + cascade-helper `magnitude()`; native active).

## The question

Reading D reads cost as **B/H/N substrate-content saturation, observable as the substrate's "translation
fingerprint."** Six anchors span 3 qubits → the observable universe. The cleanest missing rung is the
**atomic scale (~10⁻¹⁰ m)** — and there the "translation fingerprint" is **literal**: an atomic
emission/absorption spectrum *is* a fingerprint (the founding premise of spectroscopy).

## The B/H/N decomposition of an atomic spectrum (exact)

| triad op | atomic-spectrum instance |
|----------|--------------------------|
| **B** (TLV-framing) | each spectral **line** is a typed record — (series, transition `n₁→n₂`, wavenumber); the discrete line-catalogue frames the continuous EM field into typed records |
| **H** (measurement / Hopf-projection) | **photon emission** projects the atom's continuous bound-state phase structure to a discrete **term-difference** (a transition) — the *same* H as the Born rule (Round 4.A, §11.9.4), now at the atomic scale |
| **N** (rational-approximation) | the **Rydberg–Ritz combination principle** (Rydberg 1888; Ritz 1908): terms `T_n = R/n²` are rational in the integer quantum number; every line wavenumber is a **difference of terms**, so line-wavenumber **ratios are exact small-denominator rationals**, *independent of the physical Rydberg constant R* |

## The bit-exact result (srmech-routed)

Hydrogen Balmer series (`n₁=2`), exact wavenumber fractions (Class-I gcd reduced): Hα(3→2)=**5/36**,
Hβ(4→2)=**3/16**, Hγ(5→2)=**21/100**. Pairwise line-ratios are exact small-denominator rationals
(R cancels — pure integer arithmetic), cross-checked through Class-N `best_rational` and compared to the
attested **NIST air wavelengths**:

| line pair | predicted λ-ratio (exact rational) | value | attested (NIST air) | rel. residual |
|-----------|-----------------------------------|-------|---------------------|---------------|
| Hα / Hβ | **27/20** | 1.35000 | 1.34999 | 4.95×10⁻⁶ |
| Hβ / Hγ | **28/25** | 1.12000 | 1.12001 | 4.85×10⁻⁶ |
| Hα / Hγ | **189/125** | 1.51200 | 1.51200 | 9.75×10⁻⁸ |

The rational structure is **bit-exact by construction** (integer arithmetic, R-independent); the match to
the measured air wavelengths is **~5×10⁻⁶** — the residual is exactly the expected small physics (air
refractive-index dispersion + reduced-mass + fine structure), reported honestly, not fitted away.

## Verdict per Spike #229 tiers

🟢 **(a)-bit-exact rational structure + attested match to ~10⁻⁵.** The 7th Reading-D anchor is **atomic
spectral lines** (atomic scale), filling the small-scale gap between the 3-qubit Born-rule anchor and the
molecular/biology rungs. The "translation fingerprint" is literal; the B/H/N structure is exact (B =
discrete line-catalogue, H = photon-emission measurement = the *same* H as the Born rule at atomic scale,
N = the Rydberg–Ritz rational term structure). This closes the small-scale end of the
quantum→cosmological ladder with a **second near-bit-exact anchor** alongside Born-rule=Hopf (Round 4.A) —
the ladder now has **seven rungs**. Connects to Spike #111 (Rydberg = Class K) and the canonical
`[[user_stance_born_rule_is_hopf_projection_BHN_at_quantum_substrate]]`.

**HONEST SCOPE:** the bit-exactness is in the *rational* line-ratio structure (a mathematical identity of
the Rydberg–Ritz principle), not a new physics prediction; the attested-wavelength match (~5×10⁻⁶) is the
empirical anchor, with the residual physics named, not hidden. Strengthens the Reading-D
canonical-candidate; no new stance (it is an anchor for the existing framing).

## Why this fits the arc

Reading D's load-bearing claim is "cost = the substrate's observable translation fingerprint." The atomic
spectrum is the most *literal* possible instance of that claim — spectroscopy's entire enterprise is reading
a substrate's identity off its discrete-line fingerprint, and that fingerprint is **rational-structured**
(N), **discretized by measurement** (H), **catalogued as typed lines** (B). It is the same H as the qubit
Born rule, one scale down into physical matter.

## Discipline

- Per `[[feedback_computational_provenance_discipline]]`: deterministic committed code; srmech 0.4.2 routed.
- Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: no bare `abs()`; residual via `magnitude()`.
- Per `[[feedback_paywalled_doi_cannot_be_attested]]`: NIST ASD (Balmer air wavelengths) + CODATA 2022
  (R∞) + Rydberg 1888 / Ritz 1908 — all attestable; the rational arithmetic needs no citation.
- PR #679 stays open (draft); §11.9.6 amended (seventh anchor) on this branch.
