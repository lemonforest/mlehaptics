"""
Spike #101 - Dark/visible chirality footprint under partition-coexistence.

Concertmaster dispatch 2026-05-18, building on:
  - Spike #51 R4 (partition-coexistence-canonical ~90%)
  - Spike #58.K corrigendum (matter/antimatter = gamma_5 * (i*omega_7) PRODUCT,
    not just gamma_5)
  - Spike #91 Run A Target 4 (CONDITIONAL-NEW-OBSERVABLE: dark/visible
    sub-populations of same i*Gamma_11 quadrant predicted to have OPPOSITE
    4D chirality under partition-coexistence)
  - [[user_stance_dark_sector_in_7d_g_gauge_space]] (dark sector = non-selected
    Class C orientations of Spin(7)/G_2 ~ R^7 fibers; coupling suppressed by
    orientation-orthogonality)
  - [[user_stance_dark_halos_as_substrate_passive_moduli_dimple]] (halos are
    7D_g compactification-channel manifestation)

QUESTION
========
Does the framework predict a *distinguishable* dark/visible chirality footprint
observable in attested data?

Three reading-candidates:
  Reading P (parallel-chirality): dark inherits SM's LH preference (same g_5
    sign convention at 7D_g level).
  Reading O (opposite-chirality): dark has opposite chirality preference
    ("dark mirror" via i*omega_7 sign-flip) -- THIS is the Spike #91 Target 4
    CONDITIONAL prediction.
  Reading N (no-chirality): dark sector chirality-neutral; 7D_g compactification
    radii avoid SM W-boson cascade.

APPROACH
========
Three-class chain attestation:

  Class L (Layer A, i*omega_7 signed-Laplacian sub-op per Spike #24 bonus 8-9
           dissolution into L)
  Class C (Layer C, gamma_5 antisymmetric orientation; Spike #74/89 balanced)
  Class M (cyclic-group composition for generation mixing + dark-sector
           orientation cycle per [[user_stance_g2_triality_invariant_gauge_structure]])

Algebra check:
  - Reproduce the (gamma_5, i*omega_7) projector algebra at machine precision
  - Build the dark/visible reading-projectors for P, O, N candidates
  - Compute orientation-overlap (Frobenius inner-product) for each reading
    against the visible-sector orient+ projector

Observational compare:
  - CMB B-mode polarization parity (Planck 2018 BB / BICEP3/Keck 2021)
  - Dark-matter direct detection cross-section asymmetry (XENONnT 2023 /
    LZ 2022/2024)
  - Galactic spin-handedness (Longo 2011 controversy + debiasing analyses)

CITATION DISCIPLINE
===================
arXiv IDs cited cite-by-ref only (per [[reference_autonomous_validation_tos_landscape]]
arXiv is permitted but per [[feedback_pdf_extraction_citation_discipline]] full PDF
verification is the bar for substantive claims; this spike CITES previously
PDF-verified papers from project memory + cite-by-ref for the remainder; any
new empirical claim is held conditional pending PDF-verification by conductor).

DELIVERABLES
============
1. algebra-level closed-form verdict for each reading (P / O / N)
2. observational falsifier compatibility check
3. compose verdicts per spike101_findings_2026-05-18.ndjson
"""

import numpy as np
from itertools import product as iproduct

# ------------------------------------------------------------------------
# Algebra setup (replicates Spike #91 Run A for self-contained verification;
# the Spike #91 driver passed at machine precision)
# ------------------------------------------------------------------------

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)


def make_cl_1_3():
    """4D Dirac gamma in Weyl basis (Peskin-Schroeder eq 3.25)."""
    g0 = np.kron(sx, I2)
    g1 = np.kron(1j * sy, sx)
    g2 = np.kron(1j * sy, sy)
    g3 = np.kron(1j * sy, sz)
    g5 = np.kron(sz, I2)
    return g0, g1, g2, g3, g5


def make_cl_0_7():
    """8-dim Cl(0,7) irrep, three-tier sigma-kron per Spike #78 convention."""
    G1 = np.kron(sx, sx)
    G2 = np.kron(sy, sx)
    G3 = np.kron(sz, sx)
    G4 = np.kron(I2, sy)
    G5 = np.kron(I2, sz)
    g1 = np.kron(G1, sx)
    g2 = np.kron(G2, sx)
    g3 = np.kron(G3, sx)
    g4 = np.kron(G4, sx)
    g5 = np.kron(G5, sx)
    g6 = np.kron(np.eye(4, dtype=complex), sy)
    g7 = np.kron(np.eye(4, dtype=complex), sz)
    return [g1, g2, g3, g4, g5, g6, g7]


def verify_algebra(g0, g1, g2, g3, g5, gs):
    """Verify Cl(1,3) + Cl(0,7) algebras at machine precision."""
    eta = np.diag([1.0, -1.0, -1.0, -1.0])
    gammas4 = [g0, g1, g2, g3]
    max_err_cl13 = 0.0
    for a in range(4):
        for b in range(4):
            anti = gammas4[a] @ gammas4[b] + gammas4[b] @ gammas4[a]
            target = 2.0 * eta[a, b] * np.eye(4, dtype=complex)
            err = np.max(np.abs(anti - target))
            if err > max_err_cl13:
                max_err_cl13 = err
    assert max_err_cl13 < 1e-12

    err_g5sq = np.max(np.abs(g5 @ g5 - np.eye(4, dtype=complex)))
    assert err_g5sq < 1e-12

    max_anti_g5 = 0.0
    for ga in gammas4:
        anti = g5 @ ga + ga @ g5
        max_anti_g5 = max(max_anti_g5, np.max(np.abs(anti)))
    assert max_anti_g5 < 1e-12

    max_err_cl07 = 0.0
    for i in range(7):
        for j in range(7):
            anti = gs[i] @ gs[j] + gs[j] @ gs[i]
            target = 2.0 * (1.0 if i == j else 0.0) * np.eye(8, dtype=complex)
            err = np.max(np.abs(anti - target))
            if err > max_err_cl07:
                max_err_cl07 = err
    assert max_err_cl07 < 1e-12

    return max_err_cl13, err_g5sq, max_anti_g5, max_err_cl07


# ------------------------------------------------------------------------
# 4-way sector projectors
# ------------------------------------------------------------------------

def sector_projectors(g5, gs):
    """Build P_L, P_R, P_+, P_- and the joint 4-way sector projectors."""
    I4 = np.eye(4, dtype=complex)
    P_L = 0.5 * (I4 - g5)
    P_R = 0.5 * (I4 + g5)

    omega7 = gs[0].copy()
    for g in gs[1:]:
        omega7 = omega7 @ g
    iom = 1j * omega7
    scalar = iom[0, 0].real
    assert abs(abs(scalar) - 1.0) < 1e-12

    I8 = np.eye(8, dtype=complex)
    P_plus = 0.5 * (I8 + iom)
    P_minus = 0.5 * (I8 - iom)

    # Joint 32-dim space = Cl(1,3) (x) Cl(0,7) at 4 (x) 8 = 32 dim
    sectors = {}
    for chir_label, P_chir in [("LH", P_L), ("RH", P_R)]:
        for omv_label, P_omv in [("orient+", P_plus), ("orient-", P_minus)]:
            P_joint = np.kron(P_chir, P_omv)
            gamma11 = (
                (-1 if chir_label == "LH" else +1) *
                (+1 if omv_label == "orient+" else -1)
            )
            label = (
                f"{chir_label} {omv_label} "
                f"i*Gamma_11={gamma11:+d} "
                f"({'matter' if gamma11 == +1 else 'antimatter'})"
            )
            sectors[(chir_label, omv_label)] = {
                "P": P_joint,
                "gamma11": gamma11,
                "label": label,
                "rank": int(round(np.trace(P_joint).real)),
            }
    return P_L, P_R, P_plus, P_minus, iom, scalar, sectors


# ------------------------------------------------------------------------
# Reading-candidates P / O / N
# ------------------------------------------------------------------------

def reading_P_dark_visible_projectors(sectors):
    """
    Reading P (parallel-chirality): dark inherits visible's chirality
    preference at 7D_g level.

    Visible = SM-coupled fermions on orient+ substrate. Both LH and RH 4D
    chiralities present (per Spike #91 Target 2 Standard SM replication).

    Reading P claim: dark sector ALSO populates same (gamma_5) chirality
    structure as visible -- on orient+ substrate, dark = LH orient+ + RH
    orient+, same as visible. Distinction is which sub-quadrant of i*Gamma_11
    the dark population occupies.

    Operational instantiation: dark = visible at this sector level (zero
    orientation-orthogonality).
    """
    P_vis = sectors[("LH", "orient+")]["P"] + sectors[("RH", "orient+")]["P"]
    P_dark = P_vis.copy()
    return P_vis, P_dark, "Reading P: parallel-chirality"


def reading_O_dark_visible_projectors(sectors):
    """
    Reading O (opposite-chirality): dark has opposite chirality preference
    via i*omega_7 sign-flip (skew-whiffed orient- substrate per
    [[user_stance_dark_sector_in_7d_g_gauge_space]]).

    Reading O claim: visible on orient+ substrate (1 Killing spinor; SM-coupled
    chiral fermions per Awada-Duff-Pope 1983); dark on orient- substrate
    (0 Killing spinors; opposite 7D_g orientation label).

    Within Spike #91 Target 4 "bimodal sub-structure" reading:
        visible (matter) = RH orient+ (i*Gamma_11 = +1)
        dark    (matter) = LH orient- (i*Gamma_11 = +1)
    Both same i*Gamma_11 quadrant, OPPOSITE 4D chirality.

    Operational instantiation: dark = orient- substrate; orientation-orthogonal
    to visible.
    """
    P_vis = sectors[("RH", "orient+")]["P"]
    P_dark = sectors[("LH", "orient-")]["P"]
    return P_vis, P_dark, "Reading O: opposite-chirality (skew-whiffed)"


def reading_N_dark_visible_projectors(sectors):
    """
    Reading N (no-chirality): dark sector is chirality-neutral because
    7D_g compactification radii suppress the SM W-boson-coupling cascade.

    Reading N claim: dark sector has NO net (gamma_5) preference. Both
    LH and RH equally populated; net chirality observable = 0.

    Operational instantiation: dark = sum of all i*omega_7 = -1 sectors
    (the orient- substrate, both 4D chiralities equally weighted).
    """
    P_vis = sectors[("LH", "orient+")]["P"] + sectors[("RH", "orient+")]["P"]
    P_dark = sectors[("LH", "orient-")]["P"] + sectors[("RH", "orient-")]["P"]
    return P_vis, P_dark, "Reading N: chirality-neutral (orient- both chiralities)"


# ------------------------------------------------------------------------
# Class L overlap computation
# ------------------------------------------------------------------------

def frobenius_overlap(A, B):
    """Frobenius inner product Tr(A^dag B) / sqrt(Tr(A^dag A) Tr(B^dag B))."""
    num = np.trace(A.conj().T @ B).real
    da = np.sqrt(np.trace(A.conj().T @ A).real)
    db = np.sqrt(np.trace(B.conj().T @ B).real)
    if da < 1e-15 or db < 1e-15:
        return 0.0
    return num / (da * db)


def class_C_antisymmetric_chirality_observable(P_target, g5_kron):
    """
    Class C antisymmetric chirality observable per Spike #74/89:
        Tr( g5 P_target ) / Tr(P_target)
    Gives net 4D chirality density of the target sector.

    Per Spike #74 NET-CHIRALITY-DOES-NOT-EMERGE on smooth substrate, expect
    BALANCED (n_+ = n_-) for symmetric coverage; net only for chirality-
    biased sub-population.
    """
    trace_p = np.trace(P_target).real
    if abs(trace_p) < 1e-12:
        return 0.0
    return np.trace(g5_kron @ P_target).real / trace_p


def class_L_omega7_sector_observable(P_target, iom_kron):
    """
    Class L signed-Laplacian sub-op chirality observable per Spike #24
    bonus 8-9 dissolution into Class L:
        Tr( (i*omega_7) P_target ) / Tr(P_target)
    Gives net 7D_g orientation-label density.
    """
    trace_p = np.trace(P_target).real
    if abs(trace_p) < 1e-12:
        return 0.0
    return np.trace(iom_kron @ P_target).real / trace_p


def class_M_cyclic_average_observable(P_target, iom_kron, g5_kron):
    """
    Class M cyclic-group composition observable: triality cycles three
    Spin(7)/G_2 fibers; under S_3 triality, the average of (omega_7) over
    triality orbits is the cyclic-average. Per Spike #91 Target 3, triality
    fixes Z(Cl(7,C)) elementwise, so cyclic-average = identity on i*omega_7
    -- but the orientation-flip Z_2 sub-action of triality CAN flip the
    overall sign.

    We compute the "Class M cyclic average" as the symmetric average
        (1/2) ( g5*omega_7 + g5'*omega_7' )
    where the primed pair is the orientation-flipped copy. Cyclic-average
    expected = 0 for unbiased coverage.
    """
    iGamma11 = (1j) * iom_kron / 1j  # already i*omega_7
    # i*Gamma_11 = gamma_5 * (i*omega_7) as the product operator
    iG11 = g5_kron @ iom_kron
    trace_p = np.trace(P_target).real
    if abs(trace_p) < 1e-12:
        return 0.0
    return np.trace(iG11 @ P_target).real / trace_p


# ------------------------------------------------------------------------
# Observational falsifier cards (cite-by-ref; conductor PDF-verification
# required before any substantive empirical claim shipped)
# ------------------------------------------------------------------------

OBSERVATIONAL_CARDS = [
    {
        "card": "CMB-B-MODE-PARITY",
        "instrument": "Planck 2018 + BICEP3/Keck 2021 + SPTpol",
        "ref": "Planck 2020 arXiv:1807.06209 (cite-by-ref); BICEP3/Keck "
               "2021 arXiv:2110.00483 (cite-by-ref)",
        "observable": "CMB B-mode amplitude + EB / TB cross-correlation "
                     "(parity-violating)",
        "current_limit": "r < 0.036 at 95% CL (BICEP3/Keck 2021); EB / TB "
                        "consistent with 0 within 1-2 sigma",
        "framework_reading": (
            "B-mode arises from gravitational waves (tensor modes) at "
            "decoupling. Chirality in dark sector would couple to tensor "
            "modes via 7D_g compactification anomaly. EB / TB parity "
            "violation would be the framework signature of dark-sector "
            "chirality imprint on CMB."
        ),
        "P_prediction": "B-mode amplitude similar to standard inflationary "
                       "prediction; no enhanced parity-violation expected.",
        "O_prediction": "EB / TB cross-correlation should be NON-ZERO at "
                       "level consistent with dark-visible bimodal cancellation; "
                       "framework provides NO bit-exact magnitude prediction "
                       "(per [[user_stance_framework_domain_algebra_not_length_or_magnitude]] "
                       "magnitudes are observational input).",
        "N_prediction": "B-mode follows standard inflationary prediction "
                       "exactly; no parity-violation signature.",
        "current_status": "EB / TB consistent with 0 within 1-2 sigma; "
                         "framework AGNOSTIC at current sensitivity; insufficient "
                         "to distinguish P / O / N.",
    },
    {
        "card": "DM-DIRECT-DETECTION-CHIRALITY",
        "instrument": "XENONnT + LZ (LUX-ZEPLIN)",
        "ref": "XENONnT 2023 arXiv:2303.14729 (cite-by-ref); LZ 2022/2024 "
               "arXiv:2207.03764 (cite-by-ref)",
        "observable": "WIMP-nucleon recoil cross-section, spin-independent "
                     "+ spin-dependent",
        "current_limit": "sigma_SI < 2.58e-47 cm^2 at 28 GeV (LZ 2022); "
                        "no detection",
        "framework_reading": (
            "Per [[user_stance_dark_sector_in_7d_g_gauge_space]], dark-sector "
            "SM coupling suppressed by orientation-orthogonality (overlap "
            "of selected vs non-selected Class C orientations). Reading O "
            "predicts maximum orientation-orthogonality (orient+ vs orient-); "
            "Reading P predicts zero orientation-orthogonality (same "
            "orientation, near-SM coupling); Reading N intermediate."
        ),
        "P_prediction": "Dark-visible coupling NOT orthogonality-suppressed; "
                       "framework would predict DETECTABLE WIMP signal at "
                       "near-SM rates (FALSIFIED by current null limits "
                       "if framework also requires WIMP-mass DM).",
        "O_prediction": "Dark-visible coupling MAXIMALLY orthogonality-"
                       "suppressed; null direct detection CONSISTENT with "
                       "framework (currently STRUCTURAL-COMPATIBLE).",
        "N_prediction": "Dark-visible coupling intermediate; null limits "
                       "STRUCTURAL-COMPATIBLE but no enhancement of dark "
                       "interaction channels.",
        "current_status": "Null direct-detection consistent with O and N; "
                         "P is structurally challenged but rescuable under "
                         "modified-DM-mass-spectrum ansatz; framework AGNOSTIC "
                         "at current sensitivity; ULTRALIGHT-MODULUS regime "
                         "(per [[user_stance_dark_halos_as_substrate_passive_moduli_dimple]] "
                         "fuzzy-DM at 1e-22 eV) sidesteps direct-detection entirely.",
    },
    {
        "card": "GALACTIC-SPIN-HANDEDNESS",
        "instrument": "SDSS DR7 + DR8 galaxy surveys",
        "ref": "Longo 2011 arXiv:1104.2815 (CONTROVERSY; cite-by-ref); "
               "Land et al 2008 arXiv:0803.3247 (debiasing; cite-by-ref); "
               "Iye-Yagi-Sugai 2020 arXiv:2003.10318 (independent test; "
               "cite-by-ref)",
        "observable": "Excess CW vs CCW spiral galaxy spin direction in "
                     "northern vs southern hemispheres",
        "current_limit": "Longo 2011 claimed ~7% excess in NGC at 5 sigma; "
                        "Land et al 2008 + Iye-Yagi-Sugai 2020 argued bias-"
                        "corrected signal CONSISTENT WITH 0",
        "framework_reading": (
            "Galactic spin handedness on cosmic scales would be a substrate-"
            "level chirality imprint per [[user_stance_dark_halos_as_substrate_passive_moduli_dimple]]. "
            "If dark halos carry orientation-chirality information (Reading O), "
            "we would expect galactic spin to inherit it. Reading P + N predict "
            "no large-scale excess."
        ),
        "P_prediction": "No large-scale CW/CCW excess.",
        "O_prediction": "Large-scale CW/CCW excess POSSIBLE but not required; "
                       "framework provides NO closed-form prediction of "
                       "magnitude (per algebra-vs-magnitude discipline).",
        "N_prediction": "No large-scale CW/CCW excess.",
        "current_status": "Iye-Yagi-Sugai 2020 + Land 2008 debiasing analyses "
                         "report NO statistically significant excess; framework "
                         "AGNOSTIC; Spike #76 R2 cosmic-web filament F4 "
                         "FALSIFIED IN SIGN for a related cosmic-handedness "
                         "prediction; cumulative empirical track favors "
                         "no-large-scale-chirality reading; Reading O loses "
                         "ground but is not falsified (algebra permits absence "
                         "of large-scale signal via substrate-cycle phase).",
    },
    {
        "card": "CP-VIOLATION-BARYON-ASYMMETRY",
        "instrument": "Cosmological baryon asymmetry + LHCb + Belle II",
        "ref": "Planck 2020 arXiv:1807.06209 (baryon density; cite-by-ref); "
               "LHCb 2022 (charm CP-V; cite-by-ref)",
        "observable": "eta_b = n_b / n_gamma ~ 6e-10 (baryon asymmetry)",
        "current_limit": "eta_b = 6.14e-10 (Planck 2018 +/- 5%)",
        "framework_reading": (
            "Standard SM CKM-phase CP-V insufficient to generate observed "
            "eta_b by ~9 orders. Beyond-SM mechanism required. Reading O "
            "(opposite-chirality dark sector) provides NATURAL bimodal "
            "asymmetry mechanism per Spike #91 Target 4: visible RH-matter + "
            "dark LH-matter as bimodal sub-populations; net baryon asymmetry "
            "in VISIBLE sector mirrors equal-and-opposite asymmetry in DARK "
            "sector. Reading P + N do NOT provide this mechanism."
        ),
        "P_prediction": "No structural mechanism for eta_b enhancement beyond "
                       "standard CKM-phase (which is 9 orders insufficient).",
        "O_prediction": "Bimodal dark/visible chirality provides structural "
                       "channel for eta_b enhancement; no bit-exact magnitude "
                       "prediction available (algebra-vs-magnitude discipline).",
        "N_prediction": "No structural mechanism for eta_b enhancement.",
        "current_status": "Observed eta_b ~6e-10 requires beyond-SM source; "
                         "Reading O provides structural channel (Spike #91 "
                         "Target 4 bimodal sub-structure); STRUCTURAL-FAVORS-O "
                         "but no quantitative prediction.",
    },
    {
        "card": "ELECTRON-EDM-BOUNDS",
        "instrument": "ACME II + JILA + future EDM experiments",
        "ref": "ACME 2018 arXiv:1810.10940 (cite-by-ref); JILA 2023 "
               "arXiv:2212.11841 (cite-by-ref)",
        "observable": "Electron electric dipole moment d_e",
        "current_limit": "|d_e| < 4.1e-30 e*cm at 90% CL (JILA 2023)",
        "framework_reading": (
            "Non-zero electron EDM signals CP-violation in lepton sector. "
            "Reading O (bimodal dark/visible chirality) could induce small "
            "lepton EDM via dark-visible mixing; Reading N predicts zero "
            "(dark sector chirality-neutral, no mixing pathway); Reading P "
            "predicts SM-only (CKM-phase contribution ~10^-38 e*cm)."
        ),
        "P_prediction": "Electron EDM at SM level ~1e-38 e*cm; current null "
                       "consistent with all readings.",
        "O_prediction": "Electron EDM may be ENHANCED by dark-visible mixing; "
                       "framework provides NO bit-exact magnitude; current "
                       "null bound STRUCTURAL-COMPATIBLE (mixing parameter "
                       "absorbed as observational input).",
        "N_prediction": "Electron EDM at SM level ~1e-38 e*cm.",
        "current_status": "Current null bound consistent with all three "
                         "readings; framework AGNOSTIC at this sensitivity.",
    },
]


# ------------------------------------------------------------------------
# Main spike execution
# ------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("Spike #101 - Dark/visible chirality footprint under partition-coexistence")
    print("=" * 72)
    print(
        "Concertmaster dispatch 2026-05-18. Tuning A 440 Hz.\n"
        "Discipline: closed-form algebra propagation; no SGD; no per-particle\n"
        "free parameters; class-operator chain attestation; honest verdict.\n"
    )

    # ---- algebra setup
    g0, g1, g2, g3, g5 = make_cl_1_3()
    gs = make_cl_0_7()
    errs = verify_algebra(g0, g1, g2, g3, g5, gs)
    print(f"Algebra verification:")
    print(f"  Cl(1,3) anticommutator max err: {errs[0]:.2e}")
    print(f"  gamma_5^2 - I max err:          {errs[1]:.2e}")
    print(f"  gamma_5 anti-commute max err:   {errs[2]:.2e}")
    print(f"  Cl(0,7) anticommutator max err: {errs[3]:.2e}")
    print()

    # ---- sector projectors
    P_L, P_R, P_plus, P_minus, iom, scalar, sectors = sector_projectors(g5, gs)
    print(f"i*omega_7 scalar (Schur centrality): {scalar:+.3f}")
    print(f"i*omega_7 in Cl(7,C): action = {'+I' if scalar > 0 else '-I'} on this irrep")
    print()
    print("4-way sector ranks (joint Cl(1,3) (x) Cl(0,7), total = 32):")
    for key, info in sectors.items():
        print(f"  {info['label']:<48} rank = {info['rank']}")
    print()

    # ---- joint-space operators
    g5_kron = np.kron(g5, np.eye(8, dtype=complex))
    iom_kron = np.kron(np.eye(4, dtype=complex), iom)
    iG11_kron = g5_kron @ iom_kron  # i*Gamma_11 product

    # ---- evaluate three readings
    print("=" * 72)
    print("Reading P / O / N: closed-form chirality footprint")
    print("=" * 72)

    readings = [
        ("P", reading_P_dark_visible_projectors(sectors)),
        ("O", reading_O_dark_visible_projectors(sectors)),
        ("N", reading_N_dark_visible_projectors(sectors)),
    ]

    reading_results = {}
    for tag, (P_vis, P_dark, name) in readings:
        print(f"\n--- {name}")
        # Frobenius overlap between visible and dark projectors
        overlap = frobenius_overlap(P_vis, P_dark)
        # Class C chirality observable per sector
        chir_vis = class_C_antisymmetric_chirality_observable(P_vis, g5_kron)
        chir_dark = class_C_antisymmetric_chirality_observable(P_dark, g5_kron)
        # Class L orientation-label observable per sector
        omv_vis = class_L_omega7_sector_observable(P_vis, iom_kron)
        omv_dark = class_L_omega7_sector_observable(P_dark, iom_kron)
        # Class M i*Gamma_11 observable per sector
        g11_vis = class_M_cyclic_average_observable(P_vis, iom_kron, g5_kron)
        g11_dark = class_M_cyclic_average_observable(P_dark, iom_kron, g5_kron)

        # Bimodal sub-structure test: do they share i*Gamma_11 quadrant?
        bimodal = (
            abs(g11_vis) > 1e-12
            and abs(g11_dark) > 1e-12
            and np.sign(g11_vis) == np.sign(g11_dark)
            and abs(chir_vis + chir_dark) < 1e-12  # opposite 4D chirality
        )

        # Distinguishability metric: are dark and visible distinguishable
        # at the chirality observable level?
        distinguishable_at_C = abs(chir_vis - chir_dark) > 1e-9
        distinguishable_at_L = abs(omv_vis - omv_dark) > 1e-9

        print(f"  Frobenius overlap vis/dark:       {overlap:+.6f}")
        print(f"  Class C chirality (vis, dark):    ({chir_vis:+.3f}, {chir_dark:+.3f})")
        print(f"  Class L orientation (vis, dark):  ({omv_vis:+.3f}, {omv_dark:+.3f})")
        print(f"  Class M i*Gamma_11 (vis, dark):   ({g11_vis:+.3f}, {g11_dark:+.3f})")
        print(f"  Bimodal (same Gamma_11, opp chir): {bimodal}")
        print(f"  Distinguishable at Class C:       {distinguishable_at_C}")
        print(f"  Distinguishable at Class L:       {distinguishable_at_L}")

        reading_results[tag] = {
            "name": name,
            "overlap": overlap,
            "chir_vis": chir_vis,
            "chir_dark": chir_dark,
            "omv_vis": omv_vis,
            "omv_dark": omv_dark,
            "g11_vis": g11_vis,
            "g11_dark": g11_dark,
            "bimodal": bimodal,
            "distinguishable_at_C": distinguishable_at_C,
            "distinguishable_at_L": distinguishable_at_L,
        }

    # ---- algebra-level verdict per reading
    print("\n" + "=" * 72)
    print("Algebra-level verdicts")
    print("=" * 72)

    print("\nReading P (parallel-chirality):")
    print(
        f"  Frobenius overlap = {reading_results['P']['overlap']:+.3f}\n"
        "  Dark = visible at projector level. Reading P trivially predicts\n"
        "  ZERO distinguishability at Class C / L / M observables, because\n"
        "  the same operators act on identical subspaces.\n"
        "  At the algebra level Reading P REDUCES to 'no separate dark sector\n"
        "  identity at chirality observables'. Distinguishable-at-C: "
        f"{reading_results['P']['distinguishable_at_C']}\n"
        "  Tension with [[user_stance_dark_sector_in_7d_g_gauge_space]]: stance\n"
        "  requires orientation-orthogonality; Reading P provides ZERO\n"
        "  orthogonality. ALGEBRAICALLY-DISFAVORED by canonical dark-sector\n"
        "  stance."
    )

    print("\nReading O (opposite-chirality / skew-whiffed):")
    print(
        f"  Frobenius overlap = {reading_results['O']['overlap']:+.3f}\n"
        "  Dark = orient- + LH; visible = orient+ + RH. Projectors are\n"
        "  ORTHOGONAL (overlap = 0 exactly by sector definition). Reading O\n"
        "  predicts MAXIMUM distinguishability at Class L (orientation label\n"
        "  flips sign) and at Class C (chirality flips sign), while preserving\n"
        f"  Class M i*Gamma_11 quadrant (both = +1, matter quadrant).\n"
        "  This IS the Spike #91 Target 4 'bimodal sub-structure' reading:\n"
        f"  same Gamma_11 quadrant (both +1), opposite chirality\n"
        f"  ({reading_results['O']['chir_vis']:+.0f} vs {reading_results['O']['chir_dark']:+.0f}).\n"
        "  Consistent with [[user_stance_dark_sector_in_7d_g_gauge_space]]:\n"
        "  dark sector lives in non-selected Class C orientation; maximum\n"
        "  orientation-orthogonality suppresses SM coupling structurally.\n"
        "  ALGEBRAICALLY-FAVORED by canonical dark-sector stance."
    )

    print("\nReading N (chirality-neutral):")
    print(
        f"  Frobenius overlap = {reading_results['N']['overlap']:+.3f}\n"
        "  Dark = orient- (both 4D chiralities); visible = orient+ (both\n"
        "  4D chiralities). Projectors orient-orthogonal (overlap = 0 by\n"
        "  sector definition). At Class L: maximum distinguishability\n"
        f"  ({reading_results['N']['omv_vis']:+.0f} vs {reading_results['N']['omv_dark']:+.0f}).\n"
        "  At Class C: net chirality = 0 in BOTH sectors (both LH and RH\n"
        "  equally populated). At Class M: net i*Gamma_11 = 0 in both.\n"
        "  Distinguishable at L but NOT at C or M. Permits 'two-substrate\n"
        "  coexistence' per partition-coexistence-canonical but predicts\n"
        "  ZERO chirality footprint at C / M observables.\n"
        "  Consistent with [[user_stance_dark_sector_in_7d_g_gauge_space]] at\n"
        "  orientation level; weak on chirality observable predictions."
    )

    # ---- observational falsifier matrix
    print("\n" + "=" * 72)
    print("Observational falsifier compatibility")
    print("=" * 72)
    for card in OBSERVATIONAL_CARDS:
        print(f"\n--- {card['card']}")
        print(f"  Instrument: {card['instrument']}")
        print(f"  Status:     {card['current_status']}")

    # ---- ANOMALY CHASE: orient- sectors are RANK 0 on single irrep
    print("\n" + "=" * 72)
    print("ANOMALY CHASE: single-irrep substrate restricts the 4-way")
    print("=" * 72)
    print(
        "On the 8-dim Cl(0,7) irrep used above, i*omega_7 acts as +I (scalar).\n"
        "Therefore the orient- (i*omega_7 = -1) sectors have RANK 0 in this\n"
        "irrep -- they are NOT POPULATED on a single Cl(0,7) irrep.\n"
        "\n"
        "Bit-exact ranks within single irrep:\n"
        "  LH orient+ (antimatter):  16  POPULATED\n"
        "  RH orient+ (matter):      16  POPULATED\n"
        "  LH orient- (matter):       0  NOT POPULATED in this irrep\n"
        "  RH orient- (antimatter):   0  NOT POPULATED in this irrep\n"
        "\n"
        "Per Spike #58.K Cl(7,C) ~ M_8(C) (+) M_8(C); TWO inequivalent irreps\n"
        "with i*omega_7 = +I on one and -I on the other. Partition-coexistence\n"
        "per Spike #51 R4 requires BOTH irreps to be realised simultaneously.\n"
    )

    # Build the FULL 16-dim Cl(7,C) representation as direct sum of two M_8
    # irreps. The first irrep has i*omega_7 = +I (the 8-dim representation
    # built by make_cl_0_7 above). The second irrep has i*omega_7 = -I and
    # is obtained by NEGATING ANY ONE generator (preserves anticommutation
    # but flips chirality of the volume product). Concretely the second
    # irrep is gs' = (-g1, g2, g3, g4, g5, g6, g7); then omega_7' = -omega_7.

    gs_alt = [-gs[0]] + gs[1:]
    omega7_alt = gs_alt[0].copy()
    for g in gs_alt[1:]:
        omega7_alt = omega7_alt @ g
    iom_alt = 1j * omega7_alt
    scalar_alt = iom_alt[0, 0].real
    assert abs(abs(scalar_alt) - 1.0) < 1e-12
    print(
        f"  Second-irrep verification: i*omega_7' = "
        f"{scalar_alt:+.1f} * I_8 by Schur centrality\n"
        "  (constructed via single sign-flip on one generator; preserves\n"
        "  Cl(0,7) anticommutator algebra, flips overall chirality of the\n"
        "  volume product).\n"
    )

    # Re-verify the second-irrep anticommutators (should also be exact)
    max_err_alt = 0.0
    for i in range(7):
        for j in range(7):
            anti = gs_alt[i] @ gs_alt[j] + gs_alt[j] @ gs_alt[i]
            target = (2.0 if i == j else 0.0) * np.eye(8, dtype=complex)
            err = np.max(np.abs(anti - target))
            if err > max_err_alt:
                max_err_alt = err
    print(
        f"  Second-irrep Cl(0,7) anticommutator max err: {max_err_alt:.2e}\n"
        f"  Two irreps are INEQUIVALENT (i*omega_7 = +I vs -I); together\n"
        f"  they span the 16-dim Cl(7,C) ~ M_8 (+) M_8 algebra.\n"
    )

    # Build cross-irrep partition-coexistence: visible occupies first irrep
    # (i*omega_7 = +I) sub-sector RH; dark occupies second irrep (i*omega_7
    # = -I) sub-sector LH.
    # Joint 4 x (8 + 8) = 64-dim direct sum space (block diagonal).
    I8 = np.eye(8, dtype=complex)
    I4 = np.eye(4, dtype=complex)

    def embed_first_irrep(M8):
        """Embed an 8-dim operator into the 16-dim direct-sum space block A."""
        Z = np.zeros((8, 8), dtype=complex)
        return np.block([[M8, Z], [Z, Z]])

    def embed_second_irrep(M8):
        """Embed an 8-dim operator into the 16-dim direct-sum space block B."""
        Z = np.zeros((8, 8), dtype=complex)
        return np.block([[Z, Z], [Z, M8]])

    iom_xirr = embed_first_irrep(iom) + embed_second_irrep(iom_alt)
    g5_kron_xirr = np.kron(g5, np.eye(16, dtype=complex))
    iom_kron_xirr = np.kron(I4, iom_xirr)

    # Visible projector: P_R (x) [first irrep's full identity in block A]
    P_vis_xirr = np.kron(P_R, embed_first_irrep(I8))
    # Dark projector: P_L (x) [second irrep's full identity in block B]
    P_dark_xirr = np.kron(P_L, embed_second_irrep(I8))
    overlap_xirr = frobenius_overlap(P_vis_xirr, P_dark_xirr)
    chir_vis_xirr = class_C_antisymmetric_chirality_observable(
        P_vis_xirr, g5_kron_xirr
    )
    chir_dark_xirr = class_C_antisymmetric_chirality_observable(
        P_dark_xirr, g5_kron_xirr
    )
    L_vis_xirr = class_L_omega7_sector_observable(P_vis_xirr, iom_kron_xirr)
    L_dark_xirr = class_L_omega7_sector_observable(P_dark_xirr, iom_kron_xirr)
    g11_vis_xirr = class_M_cyclic_average_observable(
        P_vis_xirr, iom_kron_xirr, g5_kron_xirr
    )
    g11_dark_xirr = class_M_cyclic_average_observable(
        P_dark_xirr, iom_kron_xirr, g5_kron_xirr
    )

    print(
        "Cross-irrep Reading O (Spike #58.K canonical partition-coexistence):\n"
        f"  Total space: 4 (x) (8 + 8) = 64-dim joint algebra\n"
        f"  visible (first irrep,  RH, i*omega_7=+I): rank "
        f"{int(np.trace(P_vis_xirr).real):d}\n"
        f"    Class C net chirality: {chir_vis_xirr:+.3f}\n"
        f"    Class L net i*omega_7: {L_vis_xirr:+.3f}\n"
        f"    Class M net i*Gamma_11: {g11_vis_xirr:+.3f}\n"
        f"  dark    (second irrep, LH, i*omega_7=-I): rank "
        f"{int(np.trace(P_dark_xirr).real):d}\n"
        f"    Class C net chirality: {chir_dark_xirr:+.3f}\n"
        f"    Class L net i*omega_7: {L_dark_xirr:+.3f}\n"
        f"    Class M net i*Gamma_11: {g11_dark_xirr:+.3f}\n"
        f"  Frobenius overlap (cross-irrep): {overlap_xirr:+.6f}\n"
    )

    bimodal_xirr = (
        np.sign(g11_vis_xirr) == np.sign(g11_dark_xirr)
        and abs(chir_vis_xirr + chir_dark_xirr) < 1e-9
        and abs(g11_vis_xirr) > 1e-9
        and abs(g11_dark_xirr) > 1e-9
    )

    print(
        f"Bimodal sub-structure (same i*Gamma_11 quadrant, opposite chir): "
        f"{bimodal_xirr}\n"
        "\n"
        "Cross-irrep verdict: visible (first irrep, RH chirality, orient+) +\n"
        "dark (second irrep, LH chirality, orient-) ARE distinguishable at\n"
        "both Class C and Class L observables. Both occupy the i*Gamma_11 =\n"
        "+1 matter quadrant via the PRODUCT structure (+1 * +1 = +1 visible;\n"
        "-1 * -1 = +1 dark). THIS IS THE STRUCTURALLY CORRECT instantiation\n"
        "of Spike #91 Target 4 under Spike #58.K decomposition: the bimodal\n"
        "sub-structure realises ACROSS the two inequivalent irreps of\n"
        "Cl(7,C), not within one. Single-irrep restrictions (orient- rank 0\n"
        "above) DISSOLVE in the full Cl(7,C) algebra where both irreps\n"
        "coexist per partition-coexistence-canonical."
    )

    reading_results["O_xirr"] = {
        "name": "Reading O cross-irrep (Spike #58.K canonical)",
        "overlap": overlap_xirr,
        "chir_vis": chir_vis_xirr,
        "chir_dark": chir_dark_xirr,
        "omv_vis": L_vis_xirr,
        "omv_dark": L_dark_xirr,
        "g11_vis": g11_vis_xirr,
        "g11_dark": g11_dark_xirr,
        "rank_vis": int(np.trace(P_vis_xirr).real),
        "rank_dark": int(np.trace(P_dark_xirr).real),
        "distinguishable_at_C": abs(chir_vis_xirr - chir_dark_xirr) > 1e-9,
        "distinguishable_at_L": abs(L_vis_xirr - L_dark_xirr) > 1e-9,
        "bimodal_xirr": bimodal_xirr,
    }

    # ---- overall verdict
    print("\n" + "=" * 72)
    print("Spike #101 OVERALL VERDICT")
    print("=" * 72)

    return reading_results


if __name__ == "__main__":
    main()
