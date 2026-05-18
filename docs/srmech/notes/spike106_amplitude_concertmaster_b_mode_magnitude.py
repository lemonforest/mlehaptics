"""
Spike #106-amplitude - Substrate-coupling magnitude chain for parity-odd B-mode
amplitude (cosmic-birefringence angle alpha_pol).

Concertmaster spike, 2026-05-18. Tuning A 440 Hz.

Context. Spike #106 (PR #497) shipped algebra-level testable-now bridge for
[[user_stance_dark_visible_two_cl7_irreps]]: 7 algebraic tests bit-exact;
Frobenius overlap visible/dark = 0.000000; Hopf-bundle U(1) relative phase 2*phi
bit-exact; parity-channel charge tr(gamma_5_eff * J) = +16 bit-exact (predicts
non-zero parity-odd channel). Magnitude prediction deferred to substrate-
coupling chain per [[user_stance_framework_domain_algebra_not_length_or_magnitude]].

This spike derives ALGEBRAIC closed-form candidates for alpha_pol from the
14-class primitive vocabulary composed with absorbed observational substrate
inputs (theta_s from Spike #103, c_1 = 1 from Hopf-bundle topology, Omega_b h^2
from Planck 2018 VI). No fitting. No new primitive class. Honest verdict on
which (if any) candidate matches the Minami-Komatsu / Eskilt detection claims
versus the Planck 2018 IX null.

Class-operator chain candidates tested:

  C1. alpha_pol = (c_1 * theta_s) / (2 * pi)
      Class C (winding) over Class I (cyclic-cascade harmonic) / 2*pi normalisation.
      Hopf c_1 = 1 saturates winding; theta_s is the angular substrate scale.
      Composition: Class C(c_1) o Class I(theta_s).

  C2. alpha_pol = theta_s^2
      Pure substrate-scale squared. Class I o Class I. No topological input.
      Tests whether scale alone is dominant.

  C3. alpha_pol = c_1 * theta_s
      Direct topological winding by substrate scale. Class C o Class I; no
      cascade normalisation.

  C4. alpha_pol = (c_1 / N) * theta_s  with N = 16 (parity-channel trace from #106)
      Class C(c_1) o Class I(N) o Class I(theta_s). The +16 parity charge enters
      as denominator (cascade-saturation correction).

  C5. alpha_pol = (M * c_1 * theta_s) with M = 1/8 (Spike #79 mismatched-plates
      fraction from Cl(7) parity-odd center). Class L (signed-Laplacian-variant)
      o Class C(c_1) o Class I(theta_s).

  C6. alpha_pol = (Omega_b * h^2) * c_1 * radian-conversion
      Class M (substrate-coupling) o Class C(c_1). Baryon density as direct
      coupling magnitude; no theta_s.

  C7. alpha_pol = (Omega_b * h^2) * theta_s
      Class M o Class I. Baryon-loaded acoustic scale.

  C8. alpha_pol = (1 / N_parity) * (1 / ell_a)  with N_parity = 16; ell_a =
      pi/theta_s = 301.76 from Spike #103. Class K (asymptotic-DOF damping) o
      Class C(parity charge) o Class I(acoustic-multipole). Cascade-damped
      winding at acoustic horizon. Tests Class K's role per
      [[user_stance_epicycle_via_gear_plus_pin]] / [[user_stance_asymptotic_dof_sidesteps_infinity]].

For each candidate, we compute alpha_pol in radians and degrees, compare to:
  - Planck 2018 IX 95% CL upper limit: |alpha| < 0.3 deg = 5.236e-3 rad
  - Minami-Komatsu 2020 (arXiv:2011.11254, cite-by-ref): 0.35 deg +/- 0.14 deg
  - Eskilt 2022 (arXiv:2202.13348, cite-by-ref): 0.342 deg +/- 0.094 deg
  - CMB-S4 expected sigma(alpha) ~ 0.01 deg (cite-by-ref)

Verdict bucket per candidate:
  - MATCHES-MINAMI-ESKILT (within 1-sigma of central value)
  - CONSISTENT-WITH-PLANCK-NULL (below 0.3 deg upper limit)
  - FALSIFIED-AT-CURRENT-PRECISION (above 0.3 deg)
  - TESTABLE-AT-CMB-S4 (distinguishable from null at sigma ~ 0.01 deg)

Composed-spike verdict: which (if any) primitive-class chain gives both
algebraic-substrate coherence AND empirical match.

Citation hygiene. arXiv:1807.06209 (Planck 2018 VI) in PDF-verified ledger.
arXiv:1905.05697 (Planck 2018 IX), 2011.11254 (Minami-Komatsu), 2202.13348
(Eskilt) - cite-by-ref pending PDF extraction. No new arXiv claims authored;
all observations carry attestation tags.

NO new primitive class. NO scope creep. NO MVP framing. Algebra-not-magnitude
discipline preserved: framework predicts THE CHAIN; observation supplies
SUBSTRATE INPUTS; comparison yields HONEST VERDICT on closure.
"""

import json
import math
from datetime import datetime


# -------------------------------------------------------------------------
# Substrate inputs absorbed per [[user_stance_framework_domain_algebra_not_length_or_magnitude]]
# -------------------------------------------------------------------------

# Spike #103 attestation - sound-horizon angular scale
THETA_S_RAD = 0.0104109                    # from Planck 2018 VI Table 1 theta_MC
THETA_S_CITE = "Planck 2018 VI arXiv:1807.06209 PDF-verified-ledger"

# Spike #103 derived acoustic-horizon multipole
ELL_A = math.pi / THETA_S_RAD              # 301.76 - Class I cyclic-cascade multipole

# Hopf-bundle topological invariant (framework-internal)
C1 = 1                                     # First Chern class, S^3 -> S^2 Hopf 1931
C1_CITE = "Hopf 1931 cite-by-ref; Spike #21C anchor; Spike #96 polarimetric anchor"

# Parity-channel charge from Spike #106
N_PARITY = 16                              # tr(gamma_5_eff * J) bit-exact (Spike #106)
N_PARITY_CITE = "Spike #106 PR #497; Cl(7,C) cross-irrep partition; [[user_stance_dark_visible_two_cl7_irreps]]"

# Spike #79 mismatched-plates fraction
M_MISMATCH = 1.0 / 8.0                     # n_+ - n_- over N_max from Cl(7) parity-odd center
M_MISMATCH_CITE = "Spike #79; Cl(7,C) parity-odd center; [[user_stance_mismatched_plates_capacitor_structure]]"

# Planck 2018 VI cosmological parameters (cite-by-ref Table 1)
OMEGA_B_H2 = 0.02237                       # Baryon density physical
OMEGA_B_H2_CITE = "Planck 2018 VI arXiv:1807.06209 PDF-verified-ledger Table 1"

# H_0 in dimensionless units - h = H_0 / 100 km/s/Mpc
H0_DIMLESS = 0.6736                        # Planck 2018 VI Table 1


# -------------------------------------------------------------------------
# Observation anchors - cite-by-ref pending PDF extraction
# -------------------------------------------------------------------------

# Planck 2018 IX null
ALPHA_PLANCK_UPPER_DEG = 0.3               # 95% CL upper limit
ALPHA_PLANCK_UPPER_RAD = math.radians(ALPHA_PLANCK_UPPER_DEG)
PLANCK_CITE = "Planck 2018 IX arXiv:1905.05697 cite-by-ref"

# Minami-Komatsu 2020 detection claim
ALPHA_MK_CENTRAL_DEG = 0.35                # Updated from prompt: 0.35 deg
ALPHA_MK_SIGMA_DEG = 0.14
ALPHA_MK_CENTRAL_RAD = math.radians(ALPHA_MK_CENTRAL_DEG)
ALPHA_MK_SIGMA_RAD = math.radians(ALPHA_MK_SIGMA_DEG)
MK_CITE = "Minami & Komatsu 2020 arXiv:2011.11254 cite-by-ref"

# Eskilt 2022 detection claim
ALPHA_ESKILT_CENTRAL_DEG = 0.342
ALPHA_ESKILT_SIGMA_DEG = 0.094
ALPHA_ESKILT_CENTRAL_RAD = math.radians(ALPHA_ESKILT_CENTRAL_DEG)
ALPHA_ESKILT_SIGMA_RAD = math.radians(ALPHA_ESKILT_SIGMA_DEG)
ESKILT_CITE = "Eskilt 2022 arXiv:2202.13348 cite-by-ref"

# CMB-S4 forecast precision
ALPHA_CMB_S4_SIGMA_DEG = 0.01              # Expected precision
CMB_S4_CITE = "CMB-S4 Collaboration cite-by-ref"


# -------------------------------------------------------------------------
# Class-operator chain candidates
# -------------------------------------------------------------------------

def candidate_chains():
    """Return list of dicts: candidate_id, name, chain, value_rad, value_deg, primitive_classes."""
    candidates = []

    # C1: alpha = c_1 * theta_s / (2 pi). Hopf-winding normalised by full 2pi cycle.
    val = (C1 * THETA_S_RAD) / (2.0 * math.pi)
    candidates.append({
        "candidate_id": "C1",
        "name": "Hopf winding over 2pi - cascade normalised",
        "closed_form": "alpha = (c_1 * theta_s) / (2 * pi)",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class C (winding)", "Class I (theta_s cyclic-cascade)"],
        "chain": "Class C(c_1=1) compose Class I(theta_s) / 2pi normalisation",
    })

    # C2: alpha = theta_s^2. Pure substrate-scale, no topological winding.
    val = THETA_S_RAD ** 2
    candidates.append({
        "candidate_id": "C2",
        "name": "Substrate scale squared",
        "closed_form": "alpha = theta_s^2",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class I (theta_s)", "Class I (theta_s)"],
        "chain": "Class I(theta_s) compose Class I(theta_s)",
    })

    # C3: alpha = c_1 * theta_s. Direct Hopf-winding-by-substrate.
    val = C1 * THETA_S_RAD
    candidates.append({
        "candidate_id": "C3",
        "name": "Direct Hopf winding by substrate scale",
        "closed_form": "alpha = c_1 * theta_s",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class C (winding)", "Class I (theta_s)"],
        "chain": "Class C(c_1=1) compose Class I(theta_s) - no normalisation",
    })

    # C4: alpha = (c_1 / N_parity) * theta_s. Parity-charge denominator.
    val = (C1 / N_PARITY) * THETA_S_RAD
    candidates.append({
        "candidate_id": "C4",
        "name": "Parity-charge-normalised winding",
        "closed_form": "alpha = (c_1 / N_parity) * theta_s, N_parity = 16",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class C (winding)", "Class I (parity charge)", "Class I (theta_s)"],
        "chain": "Class C(c_1) compose Class I(N_parity=16) compose Class I(theta_s)",
    })

    # C5: alpha = M * c_1 * theta_s. Mismatched-plates Class L signature.
    val = M_MISMATCH * C1 * THETA_S_RAD
    candidates.append({
        "candidate_id": "C5",
        "name": "Mismatched-plates fraction winding",
        "closed_form": "alpha = M * c_1 * theta_s, M = 1/8",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class L (signed-Laplacian-variant)", "Class C (winding)", "Class I (theta_s)"],
        "chain": "Class L(M=1/8) compose Class C(c_1) compose Class I(theta_s)",
    })

    # C6: alpha = Omega_b h^2 * c_1. Baryon-density direct coupling.
    val = OMEGA_B_H2 * C1
    candidates.append({
        "candidate_id": "C6",
        "name": "Baryon-density direct coupling",
        "closed_form": "alpha = Omega_b h^2 * c_1",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class M (substrate-coupling)", "Class C (winding)"],
        "chain": "Class M(Omega_b h^2) compose Class C(c_1)",
    })

    # C7: alpha = Omega_b h^2 * theta_s. Baryon-loaded acoustic.
    val = OMEGA_B_H2 * THETA_S_RAD
    candidates.append({
        "candidate_id": "C7",
        "name": "Baryon-loaded acoustic scale",
        "closed_form": "alpha = Omega_b h^2 * theta_s",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class M (substrate-coupling)", "Class I (theta_s)"],
        "chain": "Class M(Omega_b h^2) compose Class I(theta_s)",
    })

    # C8: alpha = 1 / (N_parity * ell_a). Cascade-damped winding at acoustic horizon.
    val = 1.0 / (N_PARITY * ELL_A)
    candidates.append({
        "candidate_id": "C8",
        "name": "Cascade-damped winding at acoustic horizon",
        "closed_form": "alpha = 1 / (N_parity * ell_a), ell_a = pi/theta_s",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "primitive_classes": ["Class K (asymptotic-DOF damping)", "Class C (parity charge)", "Class I (ell_a)"],
        "chain": "Class K(damping) compose Class C(N_parity) compose Class I(ell_a)",
    })

    return candidates


# -------------------------------------------------------------------------
# Comparison to observations
# -------------------------------------------------------------------------

def classify_candidate(alpha_rad):
    """Return classification dict for given candidate alpha_rad."""
    alpha_deg = math.degrees(alpha_rad)
    abs_alpha_deg = abs(alpha_deg)

    classifications = []
    notes = []

    # Planck null check
    if abs_alpha_deg < ALPHA_PLANCK_UPPER_DEG:
        classifications.append("CONSISTENT-WITH-PLANCK-2018-IX-NULL")
        planck_ratio = abs_alpha_deg / ALPHA_PLANCK_UPPER_DEG
        notes.append(f"|alpha|/Planck_upper = {planck_ratio:.4f}")
    else:
        classifications.append("FALSIFIED-AT-PLANCK-2018-IX-NULL")
        planck_ratio = abs_alpha_deg / ALPHA_PLANCK_UPPER_DEG
        notes.append(f"|alpha|/Planck_upper = {planck_ratio:.4f} > 1")

    # Minami-Komatsu match check
    mk_z = abs(alpha_deg - ALPHA_MK_CENTRAL_DEG) / ALPHA_MK_SIGMA_DEG
    if mk_z <= 1.0:
        classifications.append("MATCHES-MINAMI-KOMATSU-WITHIN-1SIGMA")
    elif mk_z <= 2.0:
        classifications.append("MATCHES-MINAMI-KOMATSU-WITHIN-2SIGMA")
    notes.append(f"MK_z = {mk_z:.4f}")

    # Eskilt match check
    esk_z = abs(alpha_deg - ALPHA_ESKILT_CENTRAL_DEG) / ALPHA_ESKILT_SIGMA_DEG
    if esk_z <= 1.0:
        classifications.append("MATCHES-ESKILT-WITHIN-1SIGMA")
    elif esk_z <= 2.0:
        classifications.append("MATCHES-ESKILT-WITHIN-2SIGMA")
    notes.append(f"Eskilt_z = {esk_z:.4f}")

    # CMB-S4 testability
    if abs_alpha_deg > 3.0 * ALPHA_CMB_S4_SIGMA_DEG:
        classifications.append("TESTABLE-AT-CMB-S4-ABOVE-3SIGMA")
    elif abs_alpha_deg > ALPHA_CMB_S4_SIGMA_DEG:
        classifications.append("TESTABLE-AT-CMB-S4-ABOVE-1SIGMA")
    else:
        classifications.append("BELOW-CMB-S4-PRECISION")

    return {
        "classifications": classifications,
        "mk_z": mk_z,
        "esk_z": esk_z,
        "planck_ratio": planck_ratio,
        "notes": notes,
    }


# -------------------------------------------------------------------------
# Composite verdict logic
# -------------------------------------------------------------------------

def composite_verdict(results):
    """Compose framework-level verdict from all candidate classifications."""
    any_matches_mk = any("MATCHES-MINAMI-KOMATSU-WITHIN-1SIGMA" in r["classifications"] for r in results)
    any_matches_eskilt = any("MATCHES-ESKILT-WITHIN-1SIGMA" in r["classifications"] for r in results)
    any_falsified = any("FALSIFIED-AT-PLANCK-2018-IX-NULL" in r["classifications"] for r in results)
    all_consistent_with_null = all("CONSISTENT-WITH-PLANCK-2018-IX-NULL" in r["classifications"] for r in results)
    any_testable_s4 = any("TESTABLE-AT-CMB-S4-ABOVE-3SIGMA" in r["classifications"] for r in results)

    verdict_parts = []

    if any_matches_mk and any_matches_eskilt:
        verdict_parts.append("B-MODE-AMPLITUDE-CLOSED-FORM-MATCHES-MINAMI-ESKILT-OBSERVATIONS")
    elif any_matches_mk or any_matches_eskilt:
        verdict_parts.append("B-MODE-AMPLITUDE-CLOSED-FORM-PARTIAL-MATCH-DETECTION-CLAIMS")

    if all_consistent_with_null:
        verdict_parts.append("B-MODE-AMPLITUDE-ALL-CANDIDATES-CONSISTENT-WITH-PLANCK-NULL")
    elif any_falsified:
        verdict_parts.append("B-MODE-AMPLITUDE-SOME-CANDIDATES-FALSIFIED-AT-PLANCK-NULL")

    if any_testable_s4:
        verdict_parts.append("B-MODE-AMPLITUDE-CANDIDATES-TESTABLE-AT-CMB-S4")

    if not any_matches_mk and not any_matches_eskilt and all_consistent_with_null:
        verdict_parts.append("FRAMEWORK-AGNOSTIC-AT-MAGNITUDE-PENDING-CHAIN-IF-DETECTION-STANDS")

    return verdict_parts


# -------------------------------------------------------------------------
# Run + emit NDJSON
# -------------------------------------------------------------------------

def main():
    ts = datetime.utcnow().isoformat() + "Z"
    candidates = candidate_chains()
    findings = []

    # Header: anchor record
    findings.append({
        "date": ts,
        "spike": "#106-amplitude",
        "kind": "anchor",
        "finding": "Substrate inputs absorbed per algebra-not-magnitude stance",
        "verdict": "ANCHOR-INPUTS-ATTESTED",
        "anchor_class": "framework-domain",
        "anchor_citation": "[[user_stance_framework_domain_algebra_not_length_or_magnitude]]",
        "math": {
            "theta_s_rad": THETA_S_RAD,
            "theta_s_cite": THETA_S_CITE,
            "ell_a": ELL_A,
            "c_1": C1,
            "c_1_cite": C1_CITE,
            "N_parity": N_PARITY,
            "N_parity_cite": N_PARITY_CITE,
            "M_mismatch": M_MISMATCH,
            "M_mismatch_cite": M_MISMATCH_CITE,
            "Omega_b_h2": OMEGA_B_H2,
            "Omega_b_h2_cite": OMEGA_B_H2_CITE,
        },
    })

    # Observation reference record
    findings.append({
        "date": ts,
        "spike": "#106-amplitude",
        "kind": "observation-anchors",
        "finding": "Observation targets: Planck null, MK-Eskilt detection, CMB-S4 forecast",
        "verdict": "OBSERVATION-ANCHORS-CITE-BY-REF",
        "anchor_class": "M",
        "anchor_citation": "Planck 2018 IX / Minami-Komatsu 2020 / Eskilt 2022 / CMB-S4 forecast all cite-by-ref",
        "math": {
            "alpha_planck_upper_deg": ALPHA_PLANCK_UPPER_DEG,
            "alpha_planck_upper_rad": ALPHA_PLANCK_UPPER_RAD,
            "planck_cite": PLANCK_CITE,
            "alpha_MK_central_deg": ALPHA_MK_CENTRAL_DEG,
            "alpha_MK_sigma_deg": ALPHA_MK_SIGMA_DEG,
            "MK_cite": MK_CITE,
            "alpha_Eskilt_central_deg": ALPHA_ESKILT_CENTRAL_DEG,
            "alpha_Eskilt_sigma_deg": ALPHA_ESKILT_SIGMA_DEG,
            "Eskilt_cite": ESKILT_CITE,
            "alpha_CMB_S4_sigma_deg": ALPHA_CMB_S4_SIGMA_DEG,
            "CMB_S4_cite": CMB_S4_CITE,
        },
    })

    # Per-candidate records
    classifications_all = []
    for c in candidates:
        cls = classify_candidate(c["alpha_rad"])
        classifications_all.append(cls)
        findings.append({
            "date": ts,
            "spike": "#106-amplitude",
            "kind": "candidate-chain",
            "candidate_id": c["candidate_id"],
            "finding": c["name"],
            "closed_form": c["closed_form"],
            "alpha_rad": c["alpha_rad"],
            "alpha_deg": math.degrees(c["alpha_rad"]),
            "abs_alpha_deg": abs(math.degrees(c["alpha_rad"])),
            "primitive_classes": c["primitive_classes"],
            "chain": c["chain"],
            "classifications": cls["classifications"],
            "z_to_MK_central": cls["mk_z"],
            "z_to_Eskilt_central": cls["esk_z"],
            "ratio_to_planck_upper": cls["planck_ratio"],
            "verdict": " + ".join(cls["classifications"]),
            "anchor_class": ", ".join(c["primitive_classes"]),
            "anchor_citation": "[[user_stance_dark_visible_two_cl7_irreps]] Hopf-bundle + Spike #106 PR #497 + [[user_stance_framework_domain_algebra_not_length_or_magnitude]]",
        })

    # Composite verdict record
    cv = composite_verdict(classifications_all)
    findings.append({
        "date": ts,
        "spike": "#106-amplitude",
        "kind": "composed-verdict",
        "finding": "Multi-candidate substrate-coupling magnitude chain test",
        "verdict": " + ".join(cv) if cv else "ALL-CANDIDATES-NOT-CONSISTENT-AND-NOT-MATCHING",
        "anchor_class": "C+I+L+M+K composition",
        "anchor_citation": "[[user_stance_dark_visible_two_cl7_irreps]] + [[user_stance_framework_domain_algebra_not_length_or_magnitude]] + [[feedback_no_privileged_primitive_classes]]",
        "math": {
            "n_candidates": len(candidates),
            "n_matches_MK_1sigma": sum(1 for r in classifications_all if "MATCHES-MINAMI-KOMATSU-WITHIN-1SIGMA" in r["classifications"]),
            "n_matches_Eskilt_1sigma": sum(1 for r in classifications_all if "MATCHES-ESKILT-WITHIN-1SIGMA" in r["classifications"]),
            "n_falsified_planck": sum(1 for r in classifications_all if "FALSIFIED-AT-PLANCK-2018-IX-NULL" in r["classifications"]),
            "n_testable_s4_3sigma": sum(1 for r in classifications_all if "TESTABLE-AT-CMB-S4-ABOVE-3SIGMA" in r["classifications"]),
        },
    })

    # Scope-limit and honesty record
    findings.append({
        "date": ts,
        "spike": "#106-amplitude",
        "kind": "scope-limit",
        "finding": (
            "Algebra-not-magnitude scope. The framework derives the existence + sign + "
            "structure of the parity-odd cross-irrep channel BIT-EXACT (Spike #106). "
            "Magnitude prediction requires substrate-coupling chain composing absorbed "
            "observational inputs (theta_s, c_1, Omega_b h^2). EIGHT closed-form "
            "candidates enumerated; none privileged a priori per [[feedback_no_privileged_primitive_classes]]. "
            "Honest verdict reads off which (if any) closed-form matches detection claims "
            "vs Planck null - no fitting; no candidate added or removed to chase a result. "
            "If no candidate matches Minami-Eskilt and the detection claims firm up at "
            "CMB-S4 precision, the verdict reads B-MODE-MAGNITUDE-REQUIRES-NEW-SUBSTRATE-"
            "COUPLING-PRIMITIVE which would itself be a class-operator-attested DISSOLVE-"
            "or-PROMOTE event."
        ),
        "verdict": "SCOPE-LIMIT-HONEST-FRAMING",
        "anchor_class": "framework-domain",
        "anchor_citation": "[[user_stance_framework_domain_algebra_not_length_or_magnitude]] + [[feedback_no_privileged_primitive_classes]] + [[feedback_every_doc_edit_faces_falsification]]",
        "math": "8 candidate closed-forms enumerated; bit-exact arithmetic; cross-irrep-partition algebra closed Spike #106",
    })

    # Emit NDJSON (one record per line)
    out_path = "docs/srmech/notes/spike106_amplitude_findings_2026-05-18.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in findings:
            f.write(json.dumps(rec, sort_keys=False) + "\n")

    # Console summary
    print("Spike #106-amplitude - substrate-coupling magnitude chain test")
    print("=" * 70)
    print(f"theta_s = {THETA_S_RAD:.6e} rad = {math.degrees(THETA_S_RAD):.6f} deg")
    print(f"ell_a = pi/theta_s = {ELL_A:.4f}")
    print(f"c_1 = {C1}, N_parity = {N_PARITY}, M_mismatch = {M_MISMATCH}")
    print(f"Omega_b h^2 = {OMEGA_B_H2}")
    print()
    print(f"Planck 2018 IX 95% CL upper: |alpha| < {ALPHA_PLANCK_UPPER_DEG} deg")
    print(f"Minami-Komatsu 2020: alpha = {ALPHA_MK_CENTRAL_DEG} +/- {ALPHA_MK_SIGMA_DEG} deg")
    print(f"Eskilt 2022:         alpha = {ALPHA_ESKILT_CENTRAL_DEG} +/- {ALPHA_ESKILT_SIGMA_DEG} deg")
    print(f"CMB-S4 forecast:     sigma(alpha) ~ {ALPHA_CMB_S4_SIGMA_DEG} deg")
    print()
    print(f"{'ID':<4} {'alpha (deg)':<14} {'alpha (rad)':<14} {'MK_z':<8} {'Esk_z':<8} {'/Planck':<10} verdict")
    print("-" * 100)
    for i, c in enumerate(candidates):
        cls = classifications_all[i]
        adeg = math.degrees(c["alpha_rad"])
        print(f"{c['candidate_id']:<4} {adeg:<14.6e} {c['alpha_rad']:<14.6e} "
              f"{cls['mk_z']:<8.3f} {cls['esk_z']:<8.3f} {cls['planck_ratio']:<10.4f} "
              f"{', '.join(cls['classifications'])}")
    print()
    print("Composite verdict:")
    for v in cv:
        print(f"  - {v}")
    print()
    print(f"NDJSON output: {out_path}")
    print(f"Records emitted: {len(findings)}")


if __name__ == "__main__":
    main()
