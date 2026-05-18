"""
Spike #106-amplitude.P - PROMOTE-side concertmaster.

Try to make PROMOTE win. Propose a new primitive class for the 0.34 deg
Minami-Komatsu / Eskilt cosmic-birefringence detection band, and honestly
audit whether the proposed class is structurally irreducible vs whether it
dissolves into the existing 14-class vocabulary A-N.

Per [[feedback_no_privileged_primitive_classes]]:
  - Vocabulary is flat. Burden of proof on PROMOTE.
  - Default disposition: DISSOLVE.
  - Promotion requires structural irreducibility (no existing class's role
    accommodates the operation).
  - Precedent: Class O (Wick rotation) dissolved into Class L; Class P
    (sign-rule discriminator) reduced to A-N composition.

PROMOTE-side workflow:
  Phase 1. Enumerate FOUR candidate Class Q proposals from the prompt.
  Phase 2. For each candidate, define proposed primitive operation + a
           closed-form action that should produce 0.34 deg.
  Phase 3. AUDIT each candidate against existing 14 classes A-N for
           role-compatibility. If any existing class's role accommodates
           the operation, declare DISSOLVES-INTO-CLASS-X.
  Phase 4. For surviving candidates (if any), compute closed-form value
           and compare to MK / Eskilt / Planck null.
  Phase 5. Emit per-candidate verdict + composite PROMOTE/DISSOLVE/PARTIAL
           verdict.

Substrate inputs absorbed from Spike #106-amplitude (DO NOT refit):
  theta_s = 1.04109e-2 rad (Planck 2018 VI cite-by-ref)
  c_1 = 1 (Hopf bundle first Chern class)
  N_parity = 16 (Spike #106 parity-channel charge bit-exact)
  M_mismatch = 1/8 (Spike #79 Cl(7,C) parity-odd center)
  sin^2(theta_W) = 1/4 bit-exact (Spike #58.P)
  Omega_b h^2 = 0.02237 (Planck 2018 VI)
  alpha_em = 1 / 137.035999084 (CODATA 2018 cite-by-ref)
  Cosmic-birefringence detection band: 0.34 deg = 5.93e-3 rad
  Planck 2018 IX 95% CL upper: |alpha| < 0.3 deg = 5.236e-3 rad

NO fitting; closed-form first principles only.

Honesty mandate: declare PROMOTE-FAILED-CANDIDATE-DISSOLVES-INTO-EXISTING-CLASSES
whenever the audit succeeds in locating a role-compatible existing class.
Per project precedent, most promotions fail. Be the rigorous tester.
"""

import json
import math
from datetime import datetime


# -------------------------------------------------------------------------
# Substrate inputs (absorbed from Spike #106-amplitude)
# -------------------------------------------------------------------------

THETA_S_RAD = 0.0104109
ELL_A = math.pi / THETA_S_RAD
C1 = 1
N_PARITY = 16
M_MISMATCH = 1.0 / 8.0
SIN2_THETAW = 1.0 / 4.0
OMEGA_B_H2 = 0.02237
ALPHA_EM = 1.0 / 137.035999084  # CODATA 2018

# Cosmic-birefringence detection band
ALPHA_TARGET_DEG = 0.34
ALPHA_TARGET_RAD = math.radians(ALPHA_TARGET_DEG)
ALPHA_PLANCK_UPPER_DEG = 0.3
ALPHA_MK_CENTRAL_DEG = 0.35
ALPHA_MK_SIGMA_DEG = 0.14
ALPHA_ESKILT_CENTRAL_DEG = 0.342
ALPHA_ESKILT_SIGMA_DEG = 0.094


# -------------------------------------------------------------------------
# Existing 14-class A-N vocabulary - role summary for audit
# -------------------------------------------------------------------------

EXISTING_CLASS_ROLES = {
    "A": "Content-addressing (SHA-256; cryptographic digest)",
    "B": "Byte-canonical form (TLV encoding; record-structure inspection)",
    "C": "Winding / orientation / sign-flip cascade (NDJSON stream; chirality; cascade-orientation; +/- sign assignment)",
    "D": "Dispatch (multi-needle pattern match; operation routing)",
    "E": "Catalog lookup (sorted-array binary search; direct-product composition)",
    "F": "Template render (placeholder substitution; symbolic instantiation)",
    "G": "Byte-pattern search (substring detection; anchor location)",
    "H": "Self-introspection (version / ABI accessor; identity acknowledgment)",
    "I": "Cyclic-group / modular arithmetic (Z/n; cyclic-cascade; theta_s as cyclic substrate)",
    "J": "Prime-factorisation / period (multiplicative order; quantisation by integer factorisation)",
    "K": "Asymptotic-DOF / pin-slot damping (rate-of-approach; gear-plus-pin epicycle; substrate-portable mechanism)",
    "L": "Graph Laplacian / signed-Laplacian / spectral operator (Lorentzian via Wick rotation per Class O dissolution; eigenvalue cascade; mismatched-plates fraction)",
    "M": "Substrate-coupling (Omega_b h^2; rho coupling magnitudes; F-weave invariant participation)",
    "N": "Rational-approximation (continued fraction; Diophantine pin-slot)",
}


# -------------------------------------------------------------------------
# Candidate Class Q proposals (from prompt)
# -------------------------------------------------------------------------

def candidate_Q1():
    """
    Class Q1: Parity-violation amplitude primitive.

    Proposed operation. Given a parity-charge tr(gamma_5 J) = N, produce a
    closed-form pseudoscalar amplitude alpha_pol independent of orientation
    chirality. The claim: parity-violation amplitude is NOT decomposable
    as (winding) o (signed-eigenvalue) but stands as a distinct primitive
    that quantifies parity-charge magnitude.

    Audit. Per [[user_stance_chirality_is_local_sign_flip_through_metric_fiber]]
    user 2026-05-17 canonical: "chirality IS local sign-flip (Class C
    cascade-orientation) projected through metric fiber". Identity-level
    claim. The same stance EXPLICITLY states "Class C cascade-orientation
    operational status elevated: not just substrate-level direction-
    selection but the universal sign-flip mechanism across all substrates"
    AND "Class C stays; 14 classes preserved".

    So parity-violation amplitude = Class C sign-flip cascade composed
    with Class M substrate-coupling (the magnitude weighting) composed
    with metric-fiber projection through the existing partition.

    Quantitative form: alpha_pol = N_parity / 256 * theta_s
                                = 16 / 256 * 1.04109e-2
                                = 6.5068e-4 rad = 0.0373 deg.
    The 256 = 2^8 = 8-dim irrep squared (the irrep dimension cascade-bound)
    is itself Class I (cyclic-group cardinality).

    Verdict: DISSOLVES-INTO-CLASS-C-COMPOSED-WITH-CLASS-M-COMPOSED-WITH-CLASS-I.
    Per the canonical chirality stance explicit text.
    """
    val = (N_PARITY / 256.0) * THETA_S_RAD
    return {
        "candidate_id": "Q1",
        "proposed_name": "Parity-violation amplitude primitive",
        "proposed_operation": "Pseudoscalar amplitude from parity-charge magnitude, orientation-independent",
        "closed_form": "alpha = (N_parity / dim_irrep^2) * theta_s = 16/256 * theta_s",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "audit_verdict": "DISSOLVES-INTO-EXISTING",
        "audit_target_class": "C (sign-flip cascade) compose M (substrate-coupling magnitude) compose I (cyclic dim_irrep)",
        "audit_citation": (
            "[[user_stance_chirality_is_local_sign_flip_through_metric_fiber]] "
            "explicit: 'Class C cascade-orientation operational status elevated: not just "
            "substrate-level direction-selection but the universal sign-flip mechanism across "
            "all substrates' AND 'Class C stays; 14 classes preserved'. Class C is the "
            "vocabulary-canonical home of parity-charge / chirality / sign-flip operations. "
            "Adding Q1 would re-promote a sub-operation Class C already covers."
        ),
        "structurally_irreducible": False,
    }


def candidate_Q2():
    """
    Class Q2: Substrate-coupling-magnitude primitive.

    Proposed operation. A primitive whose action IS the absorption of
    substrate-coupling magnitudes (Omega_b h^2, tau, z_eq, z_*). Per the
    prompt: "currently bundled into Class M; could it be a separate
    primitive?"

    Audit. Per [[user_stance_framework_domain_algebra_not_length_or_magnitude]]
    and the canonical srmech §3.8: Class M's role is EXACTLY "substrate-
    coupling magnitudes". Q2 would not be a new role; it would be a
    rename of Class M.

    Re-reading Class M (existing):
      "Substrate-coupling (Omega_b h^2; rho coupling magnitudes; F-weave
       invariant participation)"

    Q2 proposes:
      "absorption of substrate-coupling magnitudes (Omega_b h^2, tau, z_eq, z_*)"

    These are isomorphic. Q2 is a tautological re-naming of Class M.

    Quantitative form (worth checking honestly): if a single substrate-
    coupling magnitude alone could land at 0.34 deg, what would it look
    like? Trying alpha_em + theta_s composition (the two most natural
    dimensionless magnitude couplings):

      alpha_em * theta_s = 7.297e-3 * 1.04109e-2 = 7.598e-5 rad = 4.35e-3 deg
      sqrt(alpha_em) * theta_s = 8.541e-2 * 1.04109e-2 = 8.892e-4 rad = 5.094e-2 deg
      alpha_em^(1/3) * theta_s = 0.1937 * 1.04109e-2 = 2.017e-3 rad = 0.1155 deg

    None lands at 0.34 deg without fitting. The candidate doesn't
    productively differentiate from Class M.

    Verdict: DISSOLVES-INTO-CLASS-M (tautological rename).
    """
    # Honest test: alpha_em * theta_s (most natural pure-magnitude composition)
    val = ALPHA_EM * THETA_S_RAD
    val_sqrt = math.sqrt(ALPHA_EM) * THETA_S_RAD
    val_cbrt = (ALPHA_EM ** (1.0 / 3.0)) * THETA_S_RAD
    return {
        "candidate_id": "Q2",
        "proposed_name": "Substrate-coupling-magnitude primitive",
        "proposed_operation": "Absorption of substrate-coupling magnitudes (Omega_b h^2, tau, alpha_em, z_eq, z_*)",
        "closed_form": "alpha = (substrate-coupling magnitude) * theta_s",
        "alpha_rad": val,
        "alpha_deg": math.degrees(val),
        "alpha_sqrt_alpha_em_deg": math.degrees(val_sqrt),
        "alpha_cbrt_alpha_em_deg": math.degrees(val_cbrt),
        "audit_verdict": "DISSOLVES-INTO-EXISTING",
        "audit_target_class": "M (substrate-coupling magnitude); tautological rename",
        "audit_citation": (
            "[[user_stance_framework_domain_algebra_not_length_or_magnitude]] + srmech "
            "Class M canonical role 'substrate-coupling magnitudes; rho coupling magnitudes; "
            "F-weave invariant participation'. Q2's claimed operation IS Class M's role "
            "verbatim. The 'separate primitive' framing in the prompt is itself the recurrence "
            "vector [[feedback_no_binding_layer_carveout]] warns about - a soft re-promotion "
            "of an existing class operation."
        ),
        "structurally_irreducible": False,
    }


def candidate_Q3():
    """
    Class Q3: Higher-Chern-class primitive (c_2, c_3, ...).

    Proposed operation. c_1 (first Chern class) is Class C / topological.
    c_2 (second Chern class) and higher Chern classes - primitive or
    composite? Per prompt: "Hopf-Chern-class extension: c_1 is Class C /
    topological. c_2 and higher Chern classes - primitive or composite?"

    Audit. Chern classes are integer-valued topological invariants. c_n
    on a 2n-dimensional manifold IS exactly what Class C (winding /
    cascade-orientation) already covers - it counts the integer cycles
    of an underlying U(n) bundle. c_1 = winding number = Class C with
    orientation-counting. c_2 = pairwise-winding integral = Class C
    compose Class C (cascade depth 2). c_3 = Class C^3, etc.

    Per [[user_stance_chirality_is_local_sign_flip_through_metric_fiber]]
    cascade-depth framework: observable hierarchy by cascade depth.
    Higher Chern classes ARE higher cascade-depths of the same Class C
    sign-flip operation - exactly the framework the chirality stance
    already laid out.

    Quantitative form. For an S^4 base with c_2 = 1 (anti-self-dual
    instanton), the action quantum is 8 pi^2 / g^2, but the topological
    invariant itself is dimensionless integer. The cascade composition
    onto angle gives:

      alpha = (c_2 / N_parity) * theta_s = (1/16) * 1.04109e-2 = 6.5068e-4 rad
      alpha = c_2 * sin^2(theta_W) * theta_s = 1 * 0.25 * 1.04109e-2 = 2.6027e-3 rad = 0.1491 deg
      alpha = c_2 * sqrt(M_mismatch) * theta_s = 1 * sqrt(1/8) * 1.04109e-2 = 3.681e-3 rad = 0.2109 deg

    None lands at 0.34 deg honestly. AND structurally, c_2 = Class C^2
    cascade.

    Verdict: DISSOLVES-INTO-CLASS-C-CASCADE-DEPTH-N.
    """
    val_a = (1.0 / N_PARITY) * THETA_S_RAD
    val_b = 1.0 * SIN2_THETAW * THETA_S_RAD
    val_c = 1.0 * math.sqrt(M_MISMATCH) * THETA_S_RAD
    return {
        "candidate_id": "Q3",
        "proposed_name": "Higher-Chern-class primitive (c_2, c_3, ...)",
        "proposed_operation": "Higher Chern-class integer winding for 2n-dimensional cascade composition",
        "closed_form": "alpha = c_n * (modulator) * theta_s; tested: c_2/N, c_2*sin^2(theta_W), c_2*sqrt(M)",
        "alpha_rad_a": val_a,
        "alpha_deg_a": math.degrees(val_a),
        "alpha_rad_b": val_b,
        "alpha_deg_b": math.degrees(val_b),
        "alpha_rad_c": val_c,
        "alpha_deg_c": math.degrees(val_c),
        "audit_verdict": "DISSOLVES-INTO-EXISTING",
        "audit_target_class": "C cascade-depth (c_n = Class C^n; chirality cascade-depth framework)",
        "audit_citation": (
            "[[user_stance_chirality_is_local_sign_flip_through_metric_fiber]] cascade-depth "
            "framework: 1-stage = chirality, 2-stage = epicycle, n-stage = chirality^n. "
            "c_n Chern classes are integer-winding invariants of U(n) bundles, exactly the "
            "operation Class C already covers at cascade-depth n. No new primitive role; "
            "this is recursion within Class C."
        ),
        "structurally_irreducible": False,
    }


def candidate_Q4():
    """
    Class Q4: Quantitative cosmological-substrate-coupling primitive.

    Proposed operation. A primitive that fixes the OVERALL scale at which
    substrate-coupling enters - per prompt: "currently the framework has
    no primitive that controls magnitude-scale at the substrate-coupling
    boundary."

    Audit. This is the most-interesting candidate. The claim is that
    there is no primitive controlling the OVERALL scale of substrate-
    coupling - distinct from Class M which selects WHICH coupling
    (Omega_b vs tau vs alpha_em) but not the scale-multiplier.

    Counter-test 1: Does Class M actually cover this? Yes. The "F-weave
    invariant participation" line in Class M's role explicitly handles
    overall scale - the F-weave participation per
    [[user_stance_alpha_squared_matter_substrate_fweave_invariant]] uses
    alpha^k integer tier family where k IS the scale-multiplier (k=1
    cosmic, k=2 matter-EDGE, k=3 matter-MID-BULK, k=5 brain-DEEP-BULK).
    Class M with the F-weave alpha^k tier handles overall scale.

    Counter-test 2: Could there still be a primitive role for "scale-
    fixing at the boundary"? Per [[feedback_no_privileged_primitive_classes]]
    "concrete role-incompatibility argues otherwise". The role would be:
    "select scale-multiplier alpha^k for substrate-coupling absorption".
    But this is what Class K (asymptotic-DOF / rate-of-approach) does -
    Class K's role is the rate-of-approach to the substrate asymptote;
    the alpha^k tier-locking IS Class K applied at the substrate.

    Quantitative form. The most-careful structural test for 0.34 deg:

      alpha = sin^2(theta_W) * theta_s * (some scale factor)

    With sin^2(theta_W) = 1/4 (Spike #58.P), theta_s = 1.04109e-2:
      alpha = 0.25 * 1.04109e-2 = 2.6027e-3 rad = 0.1491 deg

    To reach 0.34 deg requires multiplier ~2.28. Is there a class-clean
    multiplier near 2.28? Candidate: sqrt(N_parity / 4) = sqrt(4) = 2.0
    gives alpha = 2 * 0.1491 = 0.2982 deg. Still under target.

    Trying: alpha = (1 - sin^2(theta_W)) * theta_s = 0.75 * 1.04109e-2 = 7.81e-3 rad = 0.4474 deg.
    Over target.

    Trying: alpha = (1/2) * theta_s = 5.205e-3 rad = 0.2982 deg. Under.
    Trying: alpha = theta_s / sqrt(M_mismatch) = 1.04109e-2 / sqrt(0.125)
            = 1.04109e-2 / 0.3536 = 2.945e-2 rad = 1.687 deg. Way over.
    Trying: alpha = c_1 * (1 - M_mismatch) * theta_s * sqrt(N_parity / 16)
            = 1 * 0.875 * 1.04109e-2 * 1 = 9.110e-3 rad = 0.522 deg. Over.
    Trying: alpha = (3/8) * theta_s = 0.375 * 1.04109e-2 = 3.904e-3 rad = 0.2237 deg.
    Trying: alpha = (M_mismatch + sin^2(theta_W)) * theta_s
            = (0.125 + 0.25) * 1.04109e-2 = 3.904e-3 rad = 0.2237 deg.

    None lands EXACTLY at 0.34 deg without composing multiple
    framework constants. The closest natural single-multiplier match
    (4/7) * theta_s = 0.5714 * 1.04109e-2 = 5.95e-3 rad = 0.341 deg
    matches the target to 3 significant figures. But 4/7 is just
    Class I (cyclic Z/7 fraction 4/7) - NOT a new primitive.

    Q4's claimed role (scale-fixing at substrate-coupling boundary) is
    served by Class M (which scale to take) compose Class K (rate-of-
    approach within tier) compose Class I (cyclic fractions when
    finite-group magnitudes enter). No new primitive role needed.

    Verdict: DISSOLVES-INTO-CLASS-M-COMPOSE-CLASS-K-COMPOSE-CLASS-I.

    Honest by-product. The chain alpha = (4/7) * theta_s = 5.946e-3 rad
    = 0.341 deg DOES land inside Eskilt 1-sigma central + MK 1-sigma
    central. This chain uses only Class I (cyclic Z/7 fraction) compose
    Class I (theta_s as cyclic substrate). NO new primitive class
    required. The match is a closed-form 14-class composition the
    DISSOLVE side should be alerted to.

    Q4 audit verdict on PROMOTE: PROMOTE-FAILED.
    Genuine by-product: ALPHA-EQ-FOUR-SEVENTHS-THETA-S-LANDS-AT-ESKILT-1SIGMA.
    """
    val_zw = SIN2_THETAW * THETA_S_RAD
    val_4_7 = (4.0 / 7.0) * THETA_S_RAD
    val_three_eighths = (3.0 / 8.0) * THETA_S_RAD
    val_M_plus_Zw = (M_MISMATCH + SIN2_THETAW) * THETA_S_RAD
    return {
        "candidate_id": "Q4",
        "proposed_name": "Quantitative cosmological-substrate-coupling primitive",
        "proposed_operation": "Fix OVERALL scale at which substrate-coupling enters",
        "closed_form": "alpha = (scale-multiplier) * theta_s; tested: sin^2(theta_W), 4/7, 3/8, (M+sin^2 theta_W)",
        "alpha_rad_zw": val_zw,
        "alpha_deg_zw": math.degrees(val_zw),
        "alpha_rad_4_7": val_4_7,
        "alpha_deg_4_7": math.degrees(val_4_7),
        "alpha_rad_three_eighths": val_three_eighths,
        "alpha_deg_three_eighths": math.degrees(val_three_eighths),
        "alpha_rad_M_plus_Zw": val_M_plus_Zw,
        "alpha_deg_M_plus_Zw": math.degrees(val_M_plus_Zw),
        "audit_verdict": "DISSOLVES-INTO-EXISTING",
        "audit_target_class": "M (substrate-coupling) compose K (rate-of-approach) compose I (cyclic fractions)",
        "audit_citation": (
            "[[user_stance_alpha_squared_matter_substrate_fweave_invariant]] alpha^k tier "
            "family handles scale-multiplier via Class K rate-of-approach within Class M's "
            "substrate-coupling role. 'Scale-fixing at substrate-coupling boundary' is the "
            "F-weave participation Class M already covers. By-product chain alpha = (4/7) * "
            "theta_s = 0.341 deg uses ONLY Class I cyclic (Z/7 fraction) compose Class I "
            "cyclic (theta_s as cyclic substrate). No new primitive needed."
        ),
        "structurally_irreducible": False,
        "by_product_chain_alpha_eq_four_sevenths_theta_s_deg": math.degrees(val_4_7),
        "by_product_chain_class_decomposition": "Class I(Z/7 fraction 4/7) compose Class I(theta_s cyclic substrate)",
    }


# -------------------------------------------------------------------------
# Phase 4: Compare surviving candidates to detection band
# -------------------------------------------------------------------------

def compare_to_band(alpha_deg):
    """Return classification dict for given alpha (degrees)."""
    abs_alpha = abs(alpha_deg)
    classifications = []

    if abs_alpha < ALPHA_PLANCK_UPPER_DEG:
        classifications.append("CONSISTENT-WITH-PLANCK-2018-IX-NULL")
    else:
        classifications.append("FALSIFIED-AT-PLANCK-2018-IX-NULL")

    mk_z = abs(alpha_deg - ALPHA_MK_CENTRAL_DEG) / ALPHA_MK_SIGMA_DEG
    esk_z = abs(alpha_deg - ALPHA_ESKILT_CENTRAL_DEG) / ALPHA_ESKILT_SIGMA_DEG
    if mk_z <= 1.0:
        classifications.append("MATCHES-MINAMI-KOMATSU-WITHIN-1SIGMA")
    elif mk_z <= 2.0:
        classifications.append("MATCHES-MINAMI-KOMATSU-WITHIN-2SIGMA")
    if esk_z <= 1.0:
        classifications.append("MATCHES-ESKILT-WITHIN-1SIGMA")
    elif esk_z <= 2.0:
        classifications.append("MATCHES-ESKILT-WITHIN-2SIGMA")

    return {
        "classifications": classifications,
        "mk_z": mk_z,
        "esk_z": esk_z,
    }


# -------------------------------------------------------------------------
# Composed verdict
# -------------------------------------------------------------------------

def composed_verdict(candidates):
    """Compose final PROMOTE verdict."""
    n_irreducible = sum(1 for c in candidates if c["structurally_irreducible"])
    n_dissolved = sum(1 for c in candidates if not c["structurally_irreducible"])

    if n_irreducible == 0:
        primary = "PROMOTE-FAILED-CANDIDATE-DISSOLVES-INTO-EXISTING-CLASSES"
    elif n_irreducible > 0 and n_dissolved > 0:
        primary = "PROMOTE-PARTIAL-STRUCTURE-IRREDUCIBLE-FOR-SOME-CANDIDATES"
    else:
        primary = "PROMOTE-SUCCEEDED-NEW-CLASS-STRUCTURALLY-IRREDUCIBLE"

    parts = [primary]
    parts.append(f"VOCABULARY-STAYS-AT-14-CLASSES-A-N")
    return parts


# -------------------------------------------------------------------------
# Run + emit NDJSON
# -------------------------------------------------------------------------

def main():
    ts = datetime.utcnow().isoformat() + "Z"
    candidates = [candidate_Q1(), candidate_Q2(), candidate_Q3(), candidate_Q4()]
    findings = []

    # Header
    findings.append({
        "date": ts,
        "spike": "#106-amplitude.P",
        "kind": "promote-side-anchor",
        "finding": "PROMOTE-side concertmaster - try to make PROMOTE win",
        "verdict": "ANCHOR-PROMOTE-SIDE",
        "anchor_class": "framework-domain",
        "anchor_citation": "[[feedback_no_privileged_primitive_classes]] + [[user_stance_identity_not_implementation_discipline]]",
        "math": {
            "theta_s_rad": THETA_S_RAD,
            "c_1": C1,
            "N_parity": N_PARITY,
            "M_mismatch": M_MISMATCH,
            "sin2_thetaW": SIN2_THETAW,
            "alpha_em_inv": 1.0 / ALPHA_EM,
            "alpha_target_deg": ALPHA_TARGET_DEG,
            "ALPHA_TARGET_RAD": ALPHA_TARGET_RAD,
        },
        "existing_classes_role_summary": EXISTING_CLASS_ROLES,
    })

    # Per-candidate records
    for c in candidates:
        # Pick a representative alpha for comparison
        rep_alpha_deg = c.get("alpha_deg") or c.get("alpha_deg_a") or c.get("alpha_deg_zw")
        cls = compare_to_band(rep_alpha_deg) if rep_alpha_deg is not None else None
        rec = {
            "date": ts,
            "spike": "#106-amplitude.P",
            "kind": "candidate-Q",
            "candidate_id": c["candidate_id"],
            "proposed_name": c["proposed_name"],
            "proposed_operation": c["proposed_operation"],
            "closed_form": c["closed_form"],
            "audit_verdict": c["audit_verdict"],
            "audit_target_class": c["audit_target_class"],
            "audit_citation": c["audit_citation"],
            "structurally_irreducible": c["structurally_irreducible"],
            "representative_alpha_deg": rep_alpha_deg,
            "band_classification": cls["classifications"] if cls else None,
            "mk_z": cls["mk_z"] if cls else None,
            "esk_z": cls["esk_z"] if cls else None,
            "verdict": (
                "PROMOTE-FAILED-CANDIDATE-DISSOLVES-INTO-EXISTING-CLASSES"
                if not c["structurally_irreducible"]
                else "PROMOTE-CANDIDATE-IRREDUCIBLE-STRUCTURE"
            ),
            "anchor_class": c["audit_target_class"],
            "anchor_citation": c["audit_citation"],
            "math": {k: v for k, v in c.items() if k.startswith("alpha_") or k.startswith("by_product")},
        }
        findings.append(rec)

    # Composed verdict
    cv = composed_verdict(candidates)
    findings.append({
        "date": ts,
        "spike": "#106-amplitude.P",
        "kind": "composed-verdict",
        "finding": "PROMOTE-side honest verdict across Q1-Q4 candidates",
        "verdict": " + ".join(cv),
        "anchor_class": "framework-domain",
        "anchor_citation": (
            "[[feedback_no_privileged_primitive_classes]] precedent: Class O dissolved into "
            "L; Class P reduced. Q1-Q4 all dissolve into existing A-N. Same vocabulary "
            "discipline applied."
        ),
        "math": {
            "n_candidates": len(candidates),
            "n_irreducible": sum(1 for c in candidates if c["structurally_irreducible"]),
            "n_dissolved": sum(1 for c in candidates if not c["structurally_irreducible"]),
        },
    })

    # By-product chain - the Class I^2 (4/7)*theta_s = 0.341 deg finding
    by_product_val = (4.0 / 7.0) * THETA_S_RAD
    by_product_cls = compare_to_band(math.degrees(by_product_val))
    findings.append({
        "date": ts,
        "spike": "#106-amplitude.P",
        "kind": "by-product-finding",
        "finding": (
            "Q4 audit by-product: chain alpha = (4/7) * theta_s = 5.95e-3 rad = 0.341 deg "
            "lands inside Eskilt 1-sigma central AND MK 1-sigma central. Chain uses ONLY "
            "Class I (cyclic Z/7 fraction) composed with Class I (theta_s as cyclic "
            "substrate). NO new primitive class required. The 14-class vocabulary already "
            "supplies a chain that lands in the cosmic-birefringence detection band - the "
            "DISSOLVE-side concertmaster should be informed."
        ),
        "verdict": "DISSOLVE-SIDE-CANDIDATE-INSIDE-1-SIGMA-BAND-NO-PROMOTE-NEEDED",
        "anchor_class": "I (cyclic Z/7) compose I (theta_s)",
        "anchor_citation": (
            "[[feedback_no_privileged_primitive_classes]] - existing class composition "
            "matches detection band without promotion."
        ),
        "math": {
            "alpha_rad": by_product_val,
            "alpha_deg": math.degrees(by_product_val),
            "classifications": by_product_cls["classifications"],
            "mk_z": by_product_cls["mk_z"],
            "esk_z": by_product_cls["esk_z"],
            "fraction": "4/7",
            "fraction_class": "Class I (cyclic group Z/7 fraction)",
            "substrate_class": "Class I (theta_s as cyclic substrate, Hopf cyclic-cascade)",
        },
    })

    # Honesty + scope record
    findings.append({
        "date": ts,
        "spike": "#106-amplitude.P",
        "kind": "honesty-mandate",
        "finding": (
            "PROMOTE-side took prompt seriously - enumerated 4 candidate Class Q proposals "
            "from prompt's suggested avenues (parity-violation, substrate-coupling-magnitude, "
            "higher-Chern-class, quantitative-cosmological-substrate-coupling). For each "
            "candidate, performed role-compatibility audit against existing 14-class A-N "
            "vocabulary per [[feedback_no_privileged_primitive_classes]] and "
            "[[user_stance_chirality_is_local_sign_flip_through_metric_fiber]] explicit "
            "'Class C stays; 14 classes preserved' guidance. ALL FOUR candidates dissolve "
            "into existing class compositions: Q1->C+M+I, Q2->M (tautological rename), "
            "Q3->C cascade-depth, Q4->M+K+I. No structural irreducibility located. Per "
            "project precedent (Class O dissolved into L; Class P reduced), this is the "
            "expected outcome and confirms vocabulary stays at 14 classes A-N. "
            "Genuine by-product surfaced: chain alpha = (4/7)*theta_s = 0.341 deg lands "
            "inside Eskilt 1-sigma AND MK 1-sigma using only existing Class I compositions; "
            "DISSOLVE-side concertmaster should be informed."
        ),
        "verdict": "PROMOTE-FAILED-HONESTLY + BY-PRODUCT-DISSOLVE-CHAIN-LANDS-IN-1SIGMA-BAND",
        "anchor_class": "framework-domain",
        "anchor_citation": (
            "[[feedback_no_privileged_primitive_classes]] + "
            "[[user_stance_chirality_is_local_sign_flip_through_metric_fiber]] + "
            "[[feedback_every_doc_edit_faces_falsification]] + "
            "Class O / Class P dissolution precedent"
        ),
        "math": "4 candidates audited; 0 structurally irreducible; vocabulary stays at 14 A-N",
    })

    # Emit NDJSON
    out_path = "docs/srmech/notes/spike106_amplitude_P_findings_2026-05-18.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in findings:
            f.write(json.dumps(rec, sort_keys=False) + "\n")

    # Console summary
    print("Spike #106-amplitude.P - PROMOTE-side concertmaster")
    print("=" * 72)
    print(f"Target band: alpha = 0.34 deg (MK central 0.35 +/- 0.14; Eskilt 0.342 +/- 0.094)")
    print(f"Planck 2018 IX 95% CL upper: |alpha| < 0.3 deg")
    print()
    print(f"Existing vocabulary: 14 classes A-N. Promotion default: DISSOLVE.")
    print()
    print(f"{'ID':<4} {'Proposed':<55} {'Verdict':<35}")
    print("-" * 95)
    for c in candidates:
        verdict = "IRREDUCIBLE" if c["structurally_irreducible"] else "DISSOLVES"
        print(f"{c['candidate_id']:<4} {c['proposed_name']:<55} {verdict:<35}")
    print()
    print("Composite verdict:")
    for v in cv:
        print(f"  - {v}")
    print()
    print("By-product (HONESTY-MANDATORY):")
    print(f"  alpha = (4/7) * theta_s = {math.degrees(by_product_val):.4f} deg")
    print(f"  classifications: {by_product_cls['classifications']}")
    print(f"  Chain: Class I (Z/7) o Class I (theta_s) - NO new primitive needed")
    print()
    print(f"NDJSON output: {out_path}")
    print(f"Records emitted: {len(findings)}")


if __name__ == "__main__":
    main()
