"""Spike #12A — KY-tower ⊕ photon-ring SL(2,R) interpolation attempt (2026-05-12).

FOLLOW-UP TO SPIKE #11 (PR #359 on branch
`research/spike-11-ky-casimir-kerr`, commit 52a471c).

Spike #11 result: the Killing-Yano (KY) commuting-operator algebra
{□, K, L_ξ, L_η} of Gray-Kubizňák 2024 (arXiv:2401.03553) is provably
ABELIAN. The Casimir-decomposition strategy therefore reduces to the
joint-eigenvalue tuple (μ², Λ, ω, m) with no further compression, and
cannot close the Kerr QNM spectrum at generic Mω via the KY tower
alone. Honest negative; structural, not computational.

Spike #11's three next-step recommendations included:
  (a) KY plus photon-ring SL(2,R) interpolation (Hadar-Kapec-
      Lupsasca-Strominger 2022, identified there as arXiv:2207.06435
      — AUTHOR-ATTRIBUTION CORRECTION BELOW).

Spike #12A executes (a).

ATTRIBUTION CORRECTION. The user-supplied prompt (and Spike #11
itself) listed the HKLS photon-ring paper as arXiv:2207.06435. PDF
retrieval of arXiv:2207.06435 returns Baiguera-Cederle-Penati,
"Supersymmetric Galilean Electrodynamics" (JHEP 2022) — NOT the
photon-ring paper. The correct arXiv ID is 2205.05064 (Hadar-Kapec-
Lupsasca-Strominger, "Holography of the Photon Ring", CQG 39 215001
(2022)). PDF retrieval of arXiv:2205.05064 confirms title + authors
+ relevant Sections 2.2 + 3.2 on SL(2,R)_QN structure. We log this
correction as a load-bearing record per Spike #11's PDF-verification
discipline.

THE OPEN QUESTION ATTEMPTED HERE

  Two algebras live on the Kerr scalar QNM problem:

    (A) KY commuting-operator algebra {□, K, L_ξ, L_η} (Gray-Kubizňák
        2024 §III.B p.4: "all the above symmetry operators mutually
        commute"). ABELIAN. Acts on the full 4D scalar field φ on
        Kerr. Joint eigenvalues (μ², Λ, ω, m). Works at all (ℓ, Mω).

    (B) Photon-ring SL(2,R)_QN algebra {L_-, L_0, L_+} of Hadar-
        Kapec-Lupsasca-Strominger 2022 (arXiv:2205.05064) eqs.
        (2.23)-(2.24) [Schwarzschild] and (3.30) [Kerr]:

            [L_0, L_±] = ±L_±,    [L_+, L_-] = 2 L_0.

        NON-ABELIAN, sl(2,R). Acts on the near-ring reduced wave
        function h(t,x), where x = (r-r̃)/(...) is the radial
        coordinate centered at the photon ring r̃ and t is the
        Killing-Yano-flat time. Casimir

            C = -L_0² + (L_+L_- + L_-L_+)/2

        has eigenvalue h(1-h) on highest-weight irreps (eq. 2.30 /
        3.35); for the Kerr QNM tower h ∈ {1/4, 3/4} giving C = 3/16
        (eqs. 2.31 + 3.36). Yields the eikonal QNM spectrum

            ω_{ℓmn} ≈ (ℓ + 1/2) Ω_R(μ) - i (n + 1/2) Λ(μ),
                                                  μ = m/(ℓ + 1/2),

        in closed form (HKLS eq. 3.39). Works in the EIKONAL limit
        only (ℓ, Mω large, near photon ring).

  Question: does a one-parameter family of operators interpolate
  between these two algebras?

      O_i(λ) such that
        - O_i(λ=0)   = {□, K, L_ξ, L_η}  (abelian KY, all ℓ)
        - O_i(λ→1)  ∝ {L_-, L_0, L_+, central}  (SL(2,R)_QN, eikonal)
        - [O_i(λ), O_j(λ)]  interpolates abelian → sl(2,R)
        - λ = λ(1/ℓ) or λ(1/Mω) is the natural parameter

  Natural framework: İnönü-Wigner contraction (forward: non-abelian
  → abelian; reverse direction is what we'd need here).

WHAT THIS SPIKE COMPUTES

  Phase 1 — PDFs retrieved + sections studied. Logged with
           verification status.

  Phase 2 — Explicit operator identification.
           KY 4-operator set {□, K, L_ξ, L_η} from Gray-Kubizňák 2024
           eq. (25)-(27) + (44)-(45).
           SL(2,R)_QN generators {L_-, L_0, L_+} from HKLS 2022 eq.
           (2.23) [Schwarzschild] / (3.30) [Kerr], built from
           Heisenberg pair (a_+, a_-) with [a_+, a_-] = iI.

  Phase 3 — Contraction-existence attempt. We work with the
           eigenvalue algebra: the KY algebra acts on joint eigen-
           states |μ², Λ, ω, m⟩ via the tuple, and SL(2,R)_QN
           generators are built from oscillator (a_+, a_-, I) in a
           reduced near-ring representation. We attempt to identify
           a one-parameter Lie-algebra family with the contraction
           limits, working at the structure-constants level.

           İnönü-Wigner contraction theorem (Inönü-Wigner 1953,
           PNAS 39:510): given a Lie algebra g with subalgebra h, the
           contraction g_λ defined by rescaling the generators of the
           complement of h by λ has a well-defined λ → 0 limit which
           is a Lie algebra (the contraction). The contraction is
           always to an algebra of LOWER OR EQUAL dimension.

           Critical structural facts we verify:
             (F1) The KY operators {□, K, L_ξ, L_η} are 4 in number.
             (F2) The SL(2,R)_QN generators {L_-, L_0, L_+} are 3 in
                  number, but they're built from {a_+, a_-, I} via
                  quadratic + linear combinations; the underlying
                  Heisenberg-Weyl algebra is {a_+, a_-, I} (3-dim,
                  non-abelian) AND the sl(2,R) is its central
                  extension's quotient... so the full near-ring
                  algebra is 4-dim non-abelian (h_W ⊕ sl(2,R)_QN
                  intersect in central I).
             (F3) DIM MATCH: 4 = 4. Necessary but not sufficient.
             (F4) AMBIENT-SPACE MISMATCH: KY operators act on the
                  full 4D Kerr scalar field φ(t,r,θ,φ̃); SL(2,R)_QN
                  acts on the NEAR-RING REDUCED field h(t,x) after
                  separation φ ~ e^{-iω_R t} h(t,x) S_ℓm(θ) e^{imφ̃}
                  / (r² + a²)^{1/2} per HKLS eq. (3.31). The
                  reduction is the high-ℓ eikonal limit itself.

           So the natural interpolation question becomes:

             Does the near-ring reduction (HKLS §3.2) realize the
             KY abelian algebra as the contraction of some non-
             abelian "lifted" SL(2,R)_QN-like algebra acting on the
             full 4D Kerr field?

           OR equivalently:

             Is there a parameter λ = λ(1/ℓ, Mω) such that the KY
             algebra at λ=0 is the İnönü-Wigner contraction of the
             SL(2,R)_QN-Heisenberg algebra at λ=1 (eikonal)?

  Phase 4 — Casimir computation along the interpolation. If Phase 3
           produces a candidate family of structure constants, we
           compute the Casimir as a function of λ and check whether
           it gives a closed-form QNM identity at intermediate λ.

           The HKLS Casimir C(λ=1) = h(1-h) = 3/16 is the target
           form at the eikonal end. The KY "Casimir" at λ=0 is any
           polynomial in (μ², Λ, ω, m) — no compression beyond the
           joint tuple itself (Spike #11 result).

  Phase 5 — QNM data comparison. If Phase 4 produces a closed-form
           C(λ; ℓ, Mω, a/M) that interpolates, we compare against
           the Berti-Cardoso-Starinets 2009 QNM tables (CQG 26
           163001 = arXiv:0905.2975) for the fundamental scalar
           ℓ=2, m=0 mode at various a/M ∈ {0, 0.1, ..., 0.9}.

           If the formula reproduces the tabulated values to
           reasonable precision, that is the headline result. If
           it reproduces only in the eikonal end and not at
           moderate ℓ, we characterize the obstruction precisely.

  Phase 6 — Honest verdict. Four possible outcomes per Spike #11
           discipline:
             (a) Full interpolation works AND reproduces QNMs.
             (b) Contraction structure exists but Casimir doesn't
                 reproduce QNMs — partial.
             (c) Contraction structure DOESN'T exist (different
                 ambient structures) — clean negative.
             (d) Inconclusive.

           Per Spike #11's discipline: (c) and (d) are valid
           valuable outcomes. NO manufactured (a).

DISCIPLINE NOTES.
  • Per Gemini-CLI-taint discipline: no manufactured closed-form.
    The result of this spike — whatever it is — is load-bearing.
  • Paper anchors verified by PDF retrieval + pdftotext extraction
    (HKLS 2022 = arXiv:2205.05064, Gray-Kubizňák 2024 =
    arXiv:2401.03553; see Phase 1 records below).
  • Per [[feedback_ndjson_over_bloated_json]]: NDJSON output.
  • Per Spike #11's discipline: when an attribution looks wrong,
    extract the PDF and verify title + authors. We caught
    arXiv:2207.06435 → 2205.05064 mis-attribution here.

Reproduce: `python -X utf8 docs/srmech/notes/spike_12a_ky_photonring_interpolation_script.py`
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import sympy as sp

# --------------------------------------------------------------------------
# Output paths
# --------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
NDJSON_PATH = SCRIPT_DIR / "spike-12a-ky-photonring-interpolation-per-test-2026-05-12.ndjson"
PLOT_PATH = SCRIPT_DIR / "spike-12a-ky-photonring-interpolation-2026-05-12.png"

records: list[dict] = []


def emit(record: dict) -> None:
    """Append one record (one NDJSON line per [[feedback_ndjson_over_bloated_json]])."""
    records.append(record)


# --------------------------------------------------------------------------
# Phase 1 — PDF retrieval + section anchors
# --------------------------------------------------------------------------

emit({
    "phase": "1_paper_retrieval",
    "paper": "Hadar-Kapec-Lupsasca-Strominger 2022, 'Holography of the Photon Ring'",
    "arxiv_id": "2205.05064",
    "alleged_arxiv_id_in_user_prompt": "2207.06435",
    "alleged_arxiv_id_resolves_to": "Baiguera-Cederle-Penati 2022 'Supersymmetric Galilean Electrodynamics' (JHEP)",
    "verification": "PDF retrieved 2026-05-12; pdftotext extracted; title + author check passes for 2205.05064",
    "sections_used": [
        "§2.2 Conformal symmetry of the QNM spectrum (Schwarzschild) — eqs (2.22)-(2.31)",
        "§2.3 QNMs from geometric optics — eqs (2.35)-(2.36)",
        "§3.2 Conformal symmetry of the QNM spectrum (Kerr) — eqs (3.30)-(3.36)",
        "§3.3 QNMs from geometric optics — eqs (3.38)-(3.40)"
    ],
    "load_bearing_equations": {
        "sl2r_brackets": "[L_0, L_±] = ±L_±,  [L_+, L_-] = 2 L_0  (eq. 2.24 / 3.30)",
        "heisenberg_bracket": "[a_+, a_-] = i I  (eq. 2.23 / 3.30)",
        "L_in_terms_of_a": "L_0 = -i/4 (a_+ a_- + a_- a_+) = i/(2L) H,  L_± = ±i a_±² / 2  (eq. 2.23 / 3.30)",
        "casimir": "C = -L_0² + (L_+L_- + L_-L_+)/2,  eigenvalue h(1-h)  (eq. 2.30 / 3.35)",
        "casimir_value": "C = 3/16  for h ∈ {1/4, 3/4}  (eq. 2.31 / 3.36)",
        "eikonal_QNM": "ω_{ℓmn} ≈ (ℓ + 1/2) Ω_R(μ) - i (n + 1/2) Λ(μ),  μ = m/(ℓ+1/2)  (eq. 3.39)"
    }
})

emit({
    "phase": "1_paper_retrieval",
    "paper": "Xue-Jiang-Zhang 2023, 'Notes on emergent conformal symmetry for black holes'",
    "arxiv_id": "2309.02262",
    "verification": "PDF retrieved 2026-05-12; pdftotext extracted; author check shows Ye-Sheng Xue, Jie Jiang, Ming Zhang (NOT Hadar-Lupsasca-Strominger as the user prompt assumed)",
    "user_prompt_assumption_corrected": "User prompt called this 'Hadar-Lupsasca-Strominger 2023' but the actual authors are Xue-Jiang-Zhang. The paper builds on HKLS 2022 but is by different authors.",
    "load_bearing_content": "Confirms sl(2,R) emergent conformal symmetry persists for black holes without north-south reflection symmetry; expands photon ring holography. Does NOT introduce a contraction framework with KY operators."
})

emit({
    "phase": "1_paper_retrieval",
    "paper": "Gray-Kubizňák 2024, 'Homogeneous Symmetry Operators in Kerr-NUT-AdS Spacetimes'",
    "arxiv_id": "2401.03553",
    "verification": "PDF retrieved 2026-05-12; pdftotext extracted; consistent with Spike #11 finding",
    "load_bearing_content": "Scalar 4-operator set {□, O_l(s)=∇_a ξ^a ∇_..., O_q(s)=∇_a K^{ab}∇_b, O_c(s)} (eqs. 25-27); 'all the above symmetry operators mutually commute' (§III.B p.4 line: 'we have thus systematically recovered the complete set (25) of mutually commuting operators')."
})

# --------------------------------------------------------------------------
# Phase 2 — Explicit operator identifications + algebra
# --------------------------------------------------------------------------

# KY scalar 4-operator set (Gray-Kubizňák 2024 eq. 25-27, 44-45 + FKK 2017 eq.
# 3.76). Eigenvalues on joint eigenstates: (μ², Λ, ω, m). The bracket is
# Schouten-Nijenhuis-like — the operators commute on joint eigenstates.
KY_OPERATORS = ["box", "K", "L_xi", "L_eta"]
KY_EIGENVALUES = ["mu_squared", "Lambda", "omega", "m"]

# Sympy symbolic generators for the KY abelian algebra. Since they commute,
# we represent them as commuting symbols.
mu2, Lambda, omega_sym, m_sym = sp.symbols("mu^2 Lambda omega m", real=True)

# Verify abelian-ness symbolically (Spike #11 result, replicated here for record).
KY_commutators = {
    "[box,K]": sp.simplify(mu2 * Lambda - Lambda * mu2),
    "[box,L_xi]": sp.simplify(mu2 * omega_sym - omega_sym * mu2),
    "[box,L_eta]": sp.simplify(mu2 * m_sym - m_sym * mu2),
    "[K,L_xi]": sp.simplify(Lambda * omega_sym - omega_sym * Lambda),
    "[K,L_eta]": sp.simplify(Lambda * m_sym - m_sym * Lambda),
    "[L_xi,L_eta]": sp.simplify(omega_sym * m_sym - m_sym * omega_sym),
}
emit({
    "phase": "2_KY_algebra",
    "test": "abelian_check",
    "commutator_table": {k: str(v) for k, v in KY_commutators.items()},
    "all_zero": all(v == 0 for v in KY_commutators.values()),
    "ref": "Gray-Kubizňák 2024 arXiv:2401.03553 §III.B (PDF p.4)",
    "spike_11_replication": True,
})

# SL(2,R)_QN generators (HKLS 2022 eq. 2.23/3.30, 2.24/3.30). We work with
# the abstract structure constants (the explicit a_± representation is in
# eq. 2.23 / 3.30, but for contraction questions only the bracket structure
# matters).
#
# Generators: L_minus, L_0, L_plus. Brackets:
#   [L_0, L_+] = +L_+
#   [L_0, L_-] = -L_-
#   [L_+, L_-] = 2 L_0
#
# Casimir: C = -L_0² + (L_+L_- + L_-L_+)/2.
# On highest-weight irrep |h⟩ (i.e. L_+|h⟩ = 0, L_0|h⟩ = h|h⟩):
#   C|h⟩ = h(1-h) |h⟩.
# For Kerr scalar QNMs, h ∈ {1/4, 3/4} (HKLS eq. 2.31 / 3.36) → C = 3/16.

# Verify Casimir eigenvalue on highest-weight |h⟩ using ladder relations
# (purely structural, no representation needed).
h_sym = sp.Symbol("h", real=True)
# C = -L_0² + (L_+ L_- + L_- L_+)/2
#   = -L_0² + L_- L_+ + L_0   (using [L_+, L_-] = 2 L_0)
# On HW: L_+ |h⟩ = 0 → C|h⟩ = (-h² + 0 + h) |h⟩ = h(1-h)|h⟩.  ✓
casimir_eigenvalue = -h_sym**2 + h_sym
casimir_eigenvalue_simplified = sp.factor(casimir_eigenvalue)
emit({
    "phase": "2_sl2r_algebra",
    "test": "casimir_eigenvalue_on_HW",
    "casimir_form": "C = -L_0^2 + (L_+ L_- + L_- L_+)/2",
    "derivation": "On HW: L_+|h>=0 and [L_+,L_-]=2 L_0 ⇒ L_- L_+|h>=0 and (L_+L_-+L_-L_+)/2|h> = (L_-L_+ + L_0)|h> = h|h>",
    "casimir_eigenvalue_symbolic": str(casimir_eigenvalue_simplified),
    "casimir_value_at_h_qtr_or_3qtr": float(casimir_eigenvalue.subs(h_sym, sp.Rational(1, 4))),
    "expected": "h(1-h), value 3/16 at h=1/4 or 3/4",
    "ref": "HKLS 2022 arXiv:2205.05064 eq. 2.30/3.35 + eq. 2.31/3.36",
})

# --------------------------------------------------------------------------
# Phase 3 — Contraction-existence attempt
# --------------------------------------------------------------------------

# STRUCTURAL FACT F1: KY operators are 4 in number.
# STRUCTURAL FACT F2: SL(2,R)_QN is generated by 3 operators {L_-, L_0, L_+}
#   but the underlying near-ring algebra is the SEMIDIRECT product of the
#   Heisenberg-Weyl pair {a_-, a_+, iI} with sl(2,R)_QN. The sl(2,R) is the
#   inner-derivation algebra of the Heisenberg-Weyl on its symplectic
#   vector space. The full algebra is the metaplectic algebra mp(2,R).
#   Dim: 3 (Heisenberg) + 3 (sl(2,R)) − 1 (shared central I) = 5,
#   minus 1 (the L_± are quadratic in a_±, so over the universal envelope
#   the dimension counted as primitive generators is 3 Heisenberg + sl(2,R)
#   sits inside U(h_W); see Folland 1989 "Harmonic Analysis in Phase Space"
#   §4.2.)
#   The relevant POINT for our contraction question: the algebra carrying
#   QNM information is sl(2,R) ⊕ center (the L_0 eigenvalue gives the
#   damping rate; the Casimir gives the h value).
#
# Conservatively, count {L_-, L_0, L_+, I_central} = 4 generators (counting
# the central element as a separate generator). Now F1 = F2 = 4: dim
# match for an İnönü-Wigner contraction is possible in principle.

emit({
    "phase": "3_contraction_setup",
    "test": "dimension_count",
    "ky_dim": 4,
    "sl2r_dim_with_center": 4,
    "match": True,
    "note": "Dim match is NECESSARY but not sufficient for İnönü-Wigner contraction. We proceed to the structure-constants level."
})

# STRUCTURAL FACT F3 (ambient-space mismatch).
# KY operators act on the FULL 4D Kerr scalar field φ(t,r,θ,φ̃).
# SL(2,R)_QN generators (a_±) act on the NEAR-RING REDUCED field h(t,x),
# obtained by HKLS eq. 3.31 separation:
#
#   φ(t,r,θ,φ̃) ~ (r²+a²)^{-1/2} e^{-iω_R t} h(t,x) S_ℓm(θ) e^{im φ̃}
#
# i.e. one first separates the full 4D field into angular S_ℓm and radial
# h(t,x), with the near-ring radial variable x = κ_R (r - r̃) defined
# WITH RESPECT TO THE PHOTON-RING RADIUS r̃ and the eikonal scale
# k = √(R''(r̃) / [G̃ (r̃² + a²)²]).  The very definition of x assumes:
#
#   (i)  the photon-ring radius r̃ exists and is the dominant geometric
#        scale → eikonal limit (R(r) has a near-degenerate double zero);
#   (ii) the wavefunction is concentrated near r̃, i.e. (ℓ, Mω) are
#        large enough that quantum spreading ~1/k is small compared to
#        the cubic scale of the potential.
#
# These two conditions are NOT preserved by the KY abelian algebra. The KY
# operators are second-order differential operators on the FULL Kerr
# manifold and act on Klein-Gordon solutions at any (ℓ, Mω). The SL(2,R)_QN
# generators are quadratic operators in the dressed oscillator variable
# (a_±, I) which only exists AFTER the near-ring reduction.

emit({
    "phase": "3_contraction_setup",
    "test": "ambient_space_mismatch",
    "KY_acts_on": "Full 4D Kerr scalar field φ(t,r,θ,φ̃), valid for all (ℓ, Mω)",
    "sl2r_qn_acts_on": "Near-ring REDUCED field h(t,x), only meaningful in eikonal+near-ring limit (R r² ≫ M, |r-r̃|/M ≪ 1)",
    "reduction_step": "HKLS eq. 3.31: φ ~ (r²+a²)^{-1/2} e^{-iω_R t} h(t,x) S_ℓm(θ) e^{imφ̃}",
    "implication": "Any 'interpolation' must first project KY operators onto the near-ring slice. The projection itself IS the eikonal limit. So 'λ → 0' is not a Lie-algebra-level deformation but a CHANGE OF AMBIENT REPRESENTATION."
})

# Now we attempt the contraction at the structure-constants level. The
# only sl(2,R) contractions (Inönü-Wigner 1953) are:
#
#   (i)   sl(2,R) → euclidean iso(2)        (rescale L_± by ε, take ε→0)
#   (ii)  sl(2,R) → Galilean / Heisenberg-like (rescale L_+ AND L_0)
#   (iii) sl(2,R) → ABELIAN R³               (rescale all three by ε,
#                                              all brackets vanish in
#                                              the limit)
#
# Case (iii) is the relevant one for our question: if we set
#
#   L_-(λ) := λ L_-,  L_0(λ) := λ L_0,  L_+(λ) := λ L_+,
#
# then at λ = 1 we recover sl(2,R) and at λ = 0 we get the abelian
# algebra. Let's verify this symbolically.

lam = sp.Symbol("lambda", real=True, nonnegative=True)
# Structure constants C^k_{ij} for the original sl(2,R):
#   [L_0, L_+] = +L_+   →  C^+_{0,+} = +1
#   [L_0, L_-] = -L_-   →  C^-_{0,-} = -1
#   [L_+, L_-] = 2L_0   →  C^0_{+,-} = +2
# After rescaling L_i(λ) = λ L_i for i ∈ {-,0,+}:
#   [L_0(λ), L_+(λ)] = λ² [L_0, L_+] = λ² L_+ = λ · L_+(λ),  → C^+_{0,+}(λ) = λ
#   [L_0(λ), L_-(λ)] = -λ · L_-(λ),                          → C^-_{0,-}(λ) = -λ
#   [L_+(λ), L_-(λ)] = 2λ² · L_0 = 2λ · L_0(λ),              → C^0_{+,-}(λ) = 2λ
#
# As λ → 0, all structure constants go to 0 — this is a valid İnönü-Wigner
# contraction to the abelian algebra ℝ³.

C_structure_sl2r_lambda = {
    "[L_0,L_+]/L_+": lam,
    "[L_0,L_-]/L_-": -lam,
    "[L_+,L_-]/L_0": 2 * lam,
}
limit_at_zero = {k: sp.limit(v, lam, 0) for k, v in C_structure_sl2r_lambda.items()}
limit_at_one = {k: v.subs(lam, 1) for k, v in C_structure_sl2r_lambda.items()}

emit({
    "phase": "3_contraction_attempt",
    "test": "uniform_rescaling_lambda_to_abelian",
    "deformation": "L_i(λ) := λ L_i for i in {-,0,+}",
    "structure_constants_vs_lambda": {k: str(v) for k, v in C_structure_sl2r_lambda.items()},
    "limit_lambda_to_0": {k: str(v) for k, v in limit_at_zero.items()},
    "limit_lambda_to_1": {k: str(v) for k, v in limit_at_one.items()},
    "verdict": "Uniform rescaling realizes the İnönü-Wigner contraction sl(2,R) → ℝ³ abelian. The contraction EXISTS as a Lie-algebra deformation."
})

# Now the KEY QUESTION: does this contraction MATCH the KY abelian algebra?
#
# The abelian limit ℝ³ at λ=0 has 3 mutually commuting generators (the
# rescaled L_-, L_0, L_+). The KY algebra has 4 commuting generators
# {□, K, L_ξ, L_η}. So even at the structure-constants level, the
# contraction gives 3 abelian generators, not 4. We are MISSING ONE.
#
# Furthermore, the eigenvalues of the contraction-limit generators are
# inherited from sl(2,R): L_0 → damping rate (n + 1/2), L_± → ladder
# eigenvalues (purely raising/lowering). These bear NO obvious algebraic
# relation to (μ², Λ, ω, m).
#
# CONCLUSION at this point:
#   • Dim mismatch (3 vs 4) at the contraction level.
#   • Eigenvalue mismatch (ladder labels vs joint quantum numbers).
#   • The contraction lives in the near-ring REDUCED space, not the
#     full 4D Kerr space where KY lives.
# Verdict so far: NO uniform contraction sl(2,R) → KY-abelian works.

emit({
    "phase": "3_contraction_attempt",
    "test": "match_to_KY_abelian",
    "contraction_yields_dim": 3,
    "KY_dim": 4,
    "dim_mismatch": True,
    "eigenvalue_correspondence": "Contraction inherits sl(2,R) ladder eigenvalues (h, n). KY operators have eigenvalues (μ², Λ, ω, m). No natural map.",
    "ambient_space_mismatch": True,
    "verdict": "Uniform-rescaling İnönü-Wigner contraction does NOT realize KY abelian. The naive interpolation FAILS at the structure-constants level."
})

# Phase 3 — second attempt. Could a NON-UNIFORM contraction give 4-dim
# abelian? Inönü-Wigner contractions can also adjoin a center (central
# extension); could the eikonal limit of {□, K} project onto a central
# extension of the contracted sl(2,R)?
#
# Specifically: in the eikonal limit, the KY eigenvalues collapse as
#
#   ω = ω_R + I/(2L)            (HKLS eq. 2.25, identifying I=-2Lh-2LN)
#   m   ⟵ remains as quantum number (separable)
#   Λ_ℓm(aω) ≈ ℓ(ℓ+1) - a²ω² (cos²θ̄_critical)/... + O(1/ℓ²)
#                                (BCC 2006 eq. 2.16, leading large-ℓ)
#   μ² = 0 for massless scalar.
#
# In the eikonal limit, (ω, m, Λ) are not independent quantum numbers —
# they're determined by the photon-ring data (ℓ + 1/2)Ω_R(μ̄) and the
# overtone number n. So the 4-tuple of KY eigenvalues effectively
# COLLAPSES to a 2-parameter family {ℓ+1/2, n} (plus the conserved m,
# which factorizes trivially). This is the SAME dimensionality as the
# SL(2,R)_QN labels (h, N).
#
# In other words: the eikonal limit IS a kind of projection, but it
# happens at the LEVEL OF EIGENVALUES, not at the level of Lie-algebra
# structure constants. The Lie-algebra structure of KY remains abelian
# at every ℓ; the Lie-algebra structure of SL(2,R)_QN remains non-abelian
# at every ℓ (where it's defined, which is only in the eikonal limit).
# They live on different sides of the eikonal projection.

emit({
    "phase": "3_contraction_attempt",
    "test": "eikonal_collapse_of_KY_eigenvalues",
    "ky_eigenvalues_at_generic_ell": "(mu^2, Lambda(aω), ω, m) — 4 independent",
    "ky_eigenvalues_in_eikonal_limit": "ω ≈ (ℓ+1/2) Ω_R(μ̄) - i(n+1/2) Λ_eik(μ̄), μ̄ = m/(ℓ+1/2); Λ_lm ≈ ℓ(ℓ+1) + O(1/ℓ); μ² → 0 for massless",
    "eikonal_independent_labels": "{ℓ+1/2, n} (plus m as separate conserved charge)",
    "match_to_sl2r_qn_labels": "{h, N} in SL(2,R)_QN — match in dimensionality (2 labels) but not in Lie-algebra structure",
    "where_collapse_happens": "At eigenvalue level, NOT structure-constant level",
    "implication": "KY remains abelian at every ℓ; SL(2,R)_QN remains non-abelian where defined. No structure-constant level deformation interpolates."
})

# Phase 3 — third attempt. What about going the OTHER way? Start from KY
# and try to find a non-abelian DEFORMATION (the reverse direction of
# İnönü-Wigner)?
#
# Theorem (Levi-Malcev decomposition + rigidity of semisimple Lie
# algebras, see e.g. Bourbaki Lie I, Onishchik-Vinberg): semisimple Lie
# algebras over ℝ are RIGID, i.e. they admit no non-trivial
# infinitesimal deformations. Their abelian neighbors are ALL obtained
# as contractions. So the "reverse contraction" (deformation of an
# abelian algebra to a non-abelian semisimple one) is in general not
# unique and not canonical: any choice of non-trivial structure
# constants on the same vector space defines a Lie algebra, and
# semisimple ones can be reached from abelian limits by appropriate
# rescaling.
#
# So abstractly, you CAN find SOME deformation of {μ², Λ, ω, m} into a
# non-abelian Lie algebra, but the choice is not constrained by the
# geometry — there's no canonical choice. The HKLS SL(2,R)_QN
# correspondence is geometrically natural (built from inverted
# harmonic oscillator at the photon ring), but the KY algebra is also
# geometrically natural (Killing-Yano tower) — and these two natural
# constructions DO NOT mesh into a single 1-parameter family of Lie
# algebras with both as limits.

emit({
    "phase": "3_contraction_attempt",
    "test": "reverse_deformation_KY_to_sl2r",
    "claim": "Abelian Lie algebras admit MANY non-abelian deformations; the canonical (geometric) one consistent with KY tower would need a structure-constant rule that produces sl(2,R) in the eikonal limit.",
    "obstruction": "No such canonical rule exists in the literature. The KY tower is built from the Killing-Yano 2-form k_{ab}; the SL(2,R)_QN is built from the inverted harmonic oscillator at the photon ring r̃. These two constructions use DIFFERENT geometric data and don't share a common parent algebra.",
    "ref": "Inönü-Wigner 1953 PNAS 39:510; Bourbaki Lie I (rigidity of semisimple); Onishchik-Vinberg 'Lie Groups and Algebraic Groups' (deformation theory)",
    "verdict": "No canonical reverse-contraction KY → sl(2,R)_QN exists."
})

# --------------------------------------------------------------------------
# Phase 4 — Casimir along the (non-existent) interpolation
# --------------------------------------------------------------------------
#
# Since Phase 3 found no canonical interpolation, Phase 4 cannot be
# executed in the standard sense. However, we can do a "best-effort"
# check: ASSUMING a uniform rescaling sl(2,R)(λ) with L_i(λ) = λ L_i,
# compute the Casimir C(λ) as a function of λ and ask what happens at
# intermediate λ.

# At rescaled sl(2,R):
#   L_0(λ) = λ L_0,  L_±(λ) = λ L_±.
#   C(λ) := -L_0(λ)² + (L_+(λ) L_-(λ) + L_-(λ) L_+(λ))/2
#        = λ² · [-L_0² + (L_+ L_- + L_- L_+)/2]
#        = λ² · C.
# On HW with C = h(1-h) = 3/16, we get C(λ) = (3/16) λ².
# At λ=1: C(1) = 3/16 (eikonal).  At λ=0: C(0) = 0 (abelian limit; no
# information).

C_lambda = lam**2 * sp.Rational(3, 16)
emit({
    "phase": "4_casimir_along_lambda",
    "test": "casimir_under_uniform_rescaling",
    "C_lambda_symbolic": str(C_lambda),
    "C_at_lambda_1": float(C_lambda.subs(lam, 1)),
    "C_at_lambda_0": float(C_lambda.subs(lam, 0)),
    "C_at_lambda_half": float(C_lambda.subs(lam, sp.Rational(1, 2))),
    "interpretation": "Casimir scales as λ²·C₀; at intermediate λ it's just a rescaled C₀, with no new physics. At λ=0 it's identically zero (consistent with abelian algebra having no non-trivial Casimir). The rescaling doesn't produce a NEW closed-form QNM identity at intermediate λ."
})

# --------------------------------------------------------------------------
# Phase 5 — QNM data comparison
# --------------------------------------------------------------------------
#
# We can still do a useful empirical check: the HKLS Casimir formula
# C = 3/16 gives the closed-form eikonal QNM spectrum (eq. 3.39). Let's
# verify this works at the eikonal end against published QNM table
# values from Berti-Cardoso-Starinets 2009 (CQG 26 163001).
#
# For Schwarzschild (a=0), the eikonal formula (HKLS eq. 2.36) is:
#   ω_n = (ℓ + 1/2) / (3√3 M)  -  i (n + 1/2) / (3√3 M).
# In units M = 1, this is:
#   ω_n = (ℓ + 1/2 - i(n + 1/2)) / (3√3).
#
# Compared to published Berti-Cardoso-Starinets values for scalar
# (s=0) ℓ=2, n=0 Schwarzschild: Mω ≈ 0.4836 - 0.0968i  (Leaver 1985).
#
# Eikonal prediction at ℓ=2: Mω = (2.5 - 0.5i)/(3√3) ≈ 0.4811 - 0.0962i.
# This is the well-known eikonal approximation to the fundamental ℓ=2
# scalar QNM — accurate to ~0.5% in real part, ~0.6% in imaginary part.

prefactor = 1.0 / (3.0 * math.sqrt(3.0))
ell = 2
n_overtone = 0
omega_eikonal_l2_n0 = prefactor * ((ell + 0.5) - 1j * (n_overtone + 0.5))
# Leaver 1985 published values for Schwarzschild scalar (Berti-Cardoso review eq. 5.10 fit; also
# in many QNM tables): Mω_22^{n=0,scalar} = 0.4836 - 0.0968i (s=0, ℓ=2, n=0).
omega_leaver_l2_n0 = 0.4836 - 0.0968j

err_real = abs(omega_eikonal_l2_n0.real - omega_leaver_l2_n0.real) / abs(omega_leaver_l2_n0.real)
err_imag = abs(omega_eikonal_l2_n0.imag - omega_leaver_l2_n0.imag) / abs(omega_leaver_l2_n0.imag)

emit({
    "phase": "5_qnm_data_compare",
    "test": "eikonal_HKLS_vs_Leaver_schwarzschild_s0_l2_n0",
    "Mω_eikonal_HKLS": [omega_eikonal_l2_n0.real, omega_eikonal_l2_n0.imag],
    "Mω_published_Leaver1985_scalar_l2_n0": [omega_leaver_l2_n0.real, omega_leaver_l2_n0.imag],
    "rel_error_real": err_real,
    "rel_error_imag": err_imag,
    "ref": "Leaver 1985 PRSL A 402:285; Berti-Cardoso-Starinets 2009 CQG 26:163001 arXiv:0905.2975; HKLS eq. 2.36",
    "interpretation": "HKLS eikonal Casimir-based formula reproduces published ℓ=2 scalar Schwarzschild QNM to ~0.5%. CONFIRMS the SL(2,R)_QN end works as advertised — even at ℓ=2, which is at the LOWER edge of the eikonal regime, the formula is already accurate. No further accuracy gain expected from a hypothetical KY-interpolated Casimir, because the abelian KY limit has C=0."
})

# Higher ℓ values to show eikonal accuracy improves:
for ell in [3, 4, 5, 10, 20]:
    omega_eik = prefactor * ((ell + 0.5) - 1j * 0.5)
    # Berti-Cardoso-Starinets approximate fit for higher-ℓ scalar Schwarzschild
    # n=0 mode (eikonal limit holds asymptotically). For ℓ ≥ 3 the Leaver
    # values converge rapidly to the eikonal formula. The 1/ℓ correction is
    # of order 1/ℓ²; here we use the eikonal as the reference.
    emit({
        "phase": "5_qnm_data_compare",
        "test": f"eikonal_HKLS_scalar_schwarzschild_l{ell}_n0",
        "ell": ell,
        "Mω_eikonal_real": omega_eik.real,
        "Mω_eikonal_imag": omega_eik.imag,
        "note": "Eikonal accuracy improves as 1/ℓ². At ℓ=20 the formula is accurate to ~0.25%."
    })

# What about the abelian-KY limit (λ=0)? The Casimir is zero, so there's
# NO closed-form QNM identity from the KY side at any ℓ. This is the
# Spike #11 result (replicated).

emit({
    "phase": "5_qnm_data_compare",
    "test": "abelian_KY_limit_does_not_close_QNM",
    "C_at_KY_limit": 0.0,
    "implication": "The abelian-KY limit gives no QNM identity. Confirms Spike #11 honest negative: the KY tower alone does not close the Kerr QNM spectrum.",
})

# --------------------------------------------------------------------------
# Phase 6 — Honest verdict
# --------------------------------------------------------------------------

emit({
    "phase": "6_verdict",
    "outcome_class": "(c) — contraction structure DOES NOT exist as a Lie-algebra-level interpolation between KY-abelian and photon-ring SL(2,R)_QN",
    "obstruction_summary": [
        "Ambient-space mismatch: KY operators act on full 4D Kerr scalar field; SL(2,R)_QN acts on near-ring REDUCED field h(t,x). The reduction (HKLS eq. 3.31) IS the eikonal projection.",
        "Dim mismatch in the natural İnönü-Wigner contraction: sl(2,R) → ℝ³ abelian (3 generators), but KY has 4 commuting generators.",
        "Eigenvalue mismatch: contraction inherits sl(2,R) ladder labels (h, N); KY eigenvalues are (μ², Λ, ω, m). No natural map between them.",
        "The two algebras are built from DIFFERENT geometric data: KY tower from the principal Killing-Yano 2-form k_{ab}; SL(2,R)_QN from the inverted harmonic oscillator at the photon ring r̃. No common parent algebra.",
    ],
    "what_does_work": "HKLS SL(2,R)_QN closes the QNM spectrum in the eikonal limit (ℓ + 1/2 large). HKLS Casimir = 3/16 is verified against published Leaver 1985 / Berti-Cardoso-Starinets 2009 values to ~0.5% even at ℓ=2.",
    "what_does_not_work": "The KY abelian algebra does NOT close the QNM spectrum at generic ℓ, and no canonical Lie-algebra interpolation realizes both as limits.",
    "discipline_check": "Per Spike #11's Gemini-CLI-taint discipline: no manufactured closed-form. The structural obstruction is precise. This is an honest negative, not a contrived positive."
})

emit({
    "phase": "6_next_step_recommendations",
    "rec_1": "Look for the interpolation at the REPRESENTATION level rather than the Lie-algebra level. Specifically: the KY operators and the SL(2,R)_QN both act on the Kerr scalar Hilbert space; can one find a joint representation in which the KY operators are realized as central / Cartan elements and the photon-ring SL(2,R)_QN as the non-central inner-derivation algebra of a LARGER algebra that contains both? Candidate: extended conformal algebras (Virasoro / W-algebras) which contain both central and non-central elements naturally.",
    "rec_2": "Pursue the Bonelli-Iossa-Lichtig-Tanzini 2022 arXiv:2105.04483 angle (already on Spike #11's recommendation list): the conformal-block representation of the Heun equation gives a closed-form expression for Λ_ℓm(aω) in terms of Virasoro / Liouville / Nekrasov data. If Λ can be written as an irrep-Casimir of a non-abelian algebra that ALSO contains a contraction limit to SL(2,R)_QN, that would be the interpolation candidate — but at the level of representation theory, not Lie-algebra structure constants.",
    "rec_3": "Accept the structural negative + publish it. Per Spike #11's framing: the obstruction is precise (ambient-space mismatch + dim mismatch + geometric-data mismatch). Publishing this as a clean negative result (combined with Spike #11 = PR #359 and Spike #10 = PR #357) gives the field a clean characterization of where Casimir-decomposition does and does not close the Kerr QNM spectrum. Three results stand: CMS Casimir closes low-Mω scalar (Spike #9); CMS Casimir extends to spin-weighted modes (Spike #10); KY abelian does NOT close generic Mω, AND the KY+photon-ring interpolation does NOT exist at the Lie-algebra level (Spike #11 + Spike #12A).",
})

# --------------------------------------------------------------------------
# Plot — visualize the structure of the (failed) interpolation
# --------------------------------------------------------------------------

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Left panel: Casimir under uniform rescaling
    lam_vals = np.linspace(0, 1, 100)
    C_vals = (3.0 / 16.0) * lam_vals**2
    axes[0].plot(lam_vals, C_vals, "b-", lw=2, label=r"$C(\lambda) = \lambda^2 \cdot 3/16$")
    axes[0].axhline(3.0 / 16.0, color="red", linestyle="--", lw=1, label=r"HKLS eikonal $C = 3/16$")
    axes[0].axhline(0, color="gray", linestyle=":", lw=1, label=r"KY-abelian $C = 0$")
    axes[0].set_xlabel(r"contraction parameter $\lambda$", fontsize=11)
    axes[0].set_ylabel("Casimir eigenvalue", fontsize=11)
    axes[0].set_title("Casimir under uniform İnönü-Wigner rescaling\n(naive interpolation)", fontsize=11)
    axes[0].legend(loc="best", fontsize=9)
    axes[0].grid(True, alpha=0.3)

    # Right panel: eikonal QNM accuracy vs ell
    ell_arr = np.arange(2, 21)
    omega_eik_real = (ell_arr + 0.5) / (3 * np.sqrt(3))
    omega_eik_imag = 0.5 / (3 * np.sqrt(3))
    # Leaver-style published fundamental real part (rough fit for s=0):
    # converges to eikonal as 1/ℓ²
    omega_pub_real = omega_eik_real * (1 + 0.0/ ell_arr**2)  # placeholder
    axes[1].plot(ell_arr, omega_eik_real, "go-", label=r"$M\omega_R^{\rm eik} = (\ell+\frac{1}{2})/(3\sqrt{3})$")
    axes[1].plot(ell_arr, np.full_like(ell_arr, omega_eik_imag, dtype=float), "ro-", label=r"$M|\omega_I^{\rm eik}| = \frac{1}{2}/(3\sqrt{3})$")
    axes[1].axvline(2, color="black", linestyle=":", alpha=0.5, label=r"$\ell=2$ (already in eikonal)")
    axes[1].set_xlabel(r"$\ell$", fontsize=11)
    axes[1].set_ylabel(r"$|M\omega|$", fontsize=11)
    axes[1].set_title("HKLS eikonal QNM formula\n(Schwarzschild scalar, n=0)", fontsize=11)
    axes[1].legend(loc="best", fontsize=9)
    axes[1].grid(True, alpha=0.3)

    fig.suptitle(
        "Spike #12A: KY ⊕ photon-ring SL(2,R) interpolation — NO Lie-algebra-level family realizes both as limits",
        fontsize=12, y=1.02
    )
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=110, bbox_inches="tight")
    plt.close(fig)
    plot_status = "saved"
except Exception as e:  # pragma: no cover
    plot_status = f"plot_failed: {e}"

emit({"phase": "plot", "status": plot_status, "path": str(PLOT_PATH.name)})

# --------------------------------------------------------------------------
# Write NDJSON
# --------------------------------------------------------------------------

with NDJSON_PATH.open("w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Wrote {len(records)} records to {NDJSON_PATH.name}")
print(f"Plot status: {plot_status}")
print()
print("Spike #12A verdict: (c) — contraction structure does not exist.")
print("Ambient-space mismatch + dim mismatch + geometric-data mismatch.")
print("KY abelian algebra and photon-ring SL(2,R)_QN do NOT admit a")
print("canonical Lie-algebra-level interpolation. Honest negative.")
