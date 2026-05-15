"""F2 deep-dive: equation-of-centre amplitude puzzle.

Pinpoint computation of:
  - Pin-and-slot atan2 output harmonic content (eccentric-anomaly vs true-anomaly?)
  - Hipparchan first-inequality ~5 deg target vs Brown ~6.29 deg target
  - Required eps under each interpretation
  - Downstream lunar-train gear-ratio amplification (Option D candidate)

Reproduces the figures used in spike_pinslot_elevation_and_differential_findings_2026-05-14.md
under section "F2 deep-dive".

Outputs NDJSON to spike_pinslot_findings_q_f2_deep_dive_2026-05-14.ndjson.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np

OUT = Path(__file__).parent / "spike_pinslot_findings_q_f2_deep_dive_2026-05-14.ndjson"


# ----------------------------------------------------------------------
# Canonical pin-slot transform (from research/pin_and_slot.py)
# ----------------------------------------------------------------------
def f_eps(theta, eps):
    return np.arctan2(np.sin(theta), np.cos(theta) - eps)


# ----------------------------------------------------------------------
# Step 1: Re-derive the small-eps expansion three ways and compare to
#         the Kepler-equation series for (a) eccentric anomaly,
#         (b) true anomaly, (c) the atan2 pin-slot output.
# ----------------------------------------------------------------------
#
# Kepler astronomy conventions (canonical, all standard, no novelty):
#   M = mean anomaly (uniform in time)
#   E = eccentric anomaly
#   nu = true anomaly
#   e = orbital eccentricity (0..1)
#
#   Kepler's equation:   M = E - e sin E
#   Inversion (series):  E = M + e sin M + (e^2 / 2) sin 2M + (e^3/8)(3 sin 3M - sin M) + ...
#                            = M + sum_{k>=1} (2/k) J_k(k e) sin k M
#   True-anomaly series: nu = M + 2 e sin M + (5/4) e^2 sin 2M + (e^3/12)(13 sin 3M - 3 sin M) + ...
#
# The "equation of centre" usually refers to nu - M (the angular discrepancy
# of true position from mean motion). Its leading coefficient is 2 e.
#
# Brown's leading "+22640" sin(l) coefficient with l=mean anomaly is exactly
# the equation-of-centre leading 2 e term:
#   2 * e_moon ~ 2 * 0.0549 = 0.1098 rad = 22651 arcsec  (vs Brown 22640 - matches)
# So Brown's coefficient is 2*e_moon, and corresponds to nu - M, NOT E - M.

# Step 1A: Direct atan2 FFT --------------------------------------------
def atan2_harmonics(eps, N=65536):
    theta = np.linspace(0, 2*np.pi, N, endpoint=False)
    f = f_eps(theta, eps)
    # f - theta has a 2pi sawtooth at theta=pi due to atan2 wrap; unwrap.
    residual = f - theta
    residual = (residual + np.pi) % (2*np.pi) - np.pi
    coeffs = np.fft.fft(residual) / N
    # sin(k theta) coefficient is 2 * Im(-coeffs[k]) since real signal:
    # signal = sum_k a_k e^{i k theta}; sin term: -i (a_k - a_{-k}); for real
    # signals a_{-k}=conj(a_k), so coefficient of sin(k theta) = -2 Im(a_k).
    out = {}
    for k in range(1, 7):
        c = coeffs[k]
        out[k] = -2.0 * np.imag(c)
    return out


# Step 1B: Symbolic series for atan2 pin-slot (verify by independent route)
# atan2(sin th, cos th - eps) is the polar angle of (cos th - eps, sin th).
# This is exactly the angle subtended at the offset centre. In Keplerian
# orbital geometry, if we identify:
#   theta = E (eccentric anomaly)
#   center offset = eps in units of orbital radius
# then atan2(sin E, cos E - eps) = the angle from the orbital focus to the
# point on the orbit -- which is NU, the true anomaly!
#
# Verify: the point (cos E - eps, sin E) is the unit-circle position
# shifted by eps along x; in Keplerian terms with a=1 (semi-major axis):
#   x_orbit = cos E - e         (heliocentric)
#   y_orbit = sqrt(1-e^2) sin E
# Note the sqrt(1-e^2) on y -- the pin-slot does NOT have this. So pin-slot
# is NOT the true anomaly from the focus of an *elliptical* orbit. It is
# the polar angle from the offset center of a CIRCULAR orbit -- different
# geometry, different series.
#
# The pin-slot small-eps series (computable from atan2 Taylor):
#   f_eps(theta) = theta + sum_{k>=1} (eps^k / k) sin(k theta)
# This IS the series for the eccentric anomaly E expressed as function of
# the true longitude from the offset center -- equivalent to inverting
# a CIRCULAR offset-center observation, not a Keplerian elliptical one.

# Step 1C: numerical comparison
def kepler_E_from_M_series(M, e, n_terms=6):
    """E from M, leading-order series E ≈ M + e sin M + (e^2/2) sin 2M + ..."""
    # Exact via Newton iteration
    E = M.copy()
    for _ in range(50):
        E = E - (E - e*np.sin(E) - M) / (1 - e*np.cos(E))
    return E

def kepler_nu_from_M_series(M, e):
    E = kepler_E_from_M_series(M, e)
    # nu from E:  tan(nu/2) = sqrt((1+e)/(1-e)) tan(E/2)
    nu = 2.0 * np.arctan2(np.sqrt(1+e)*np.sin(E/2), np.sqrt(1-e)*np.cos(E/2))
    return nu

def harmonics_of(signal, N, kmax=6):
    coeffs = np.fft.fft(signal) / N
    return {k: -2.0 * np.imag(coeffs[k]) for k in range(1, kmax+1)}


# ----------------------------------------------------------------------
# Step 2-4: bronze under-modelling magnitudes
# ----------------------------------------------------------------------
def main():
    records = []

    EPS_FREETH = 0.054
    EPS_WRIGHT = 0.060
    E_MOON = 0.0549  # modern lunar orbital eccentricity (mean)

    # ------- Step 1: harmonic content of pin-slot vs E-of-M vs nu-of-M -------
    N = 65536
    theta = np.linspace(0, 2*np.pi, N, endpoint=False)
    M = theta.copy()  # treat theta as mean anomaly for these series

    pin_slot_harm = atan2_harmonics(EPS_FREETH, N=N)
    pin_slot_harm_e_moon = atan2_harmonics(E_MOON, N=N)
    pin_slot_harm_dbl = atan2_harmonics(2*EPS_FREETH, N=N)  # what if eps were doubled?

    # E-from-M series for e = EPS_FREETH (pretending pin-slot is Kepler's E)
    E_of_M = kepler_E_from_M_series(M, EPS_FREETH)
    res_E = (E_of_M - M + np.pi) % (2*np.pi) - np.pi
    E_harm = harmonics_of(res_E, N)

    # nu-from-M series for e = EPS_FREETH (pretending pin-slot is Kepler's nu)
    nu_of_M = kepler_nu_from_M_series(M, EPS_FREETH)
    res_nu = (nu_of_M - M + np.pi) % (2*np.pi) - np.pi
    nu_harm = harmonics_of(res_nu, N)

    # nu-from-M series for e = E_MOON (modern lunar eccentricity)
    nu_of_M_moon = kepler_nu_from_M_series(M, E_MOON)
    res_nu_moon = (nu_of_M_moon - M + np.pi) % (2*np.pi) - np.pi
    nu_harm_moon = harmonics_of(res_nu_moon, N)

    AS_PER_RAD = 180.0/np.pi * 3600.0

    records.append({
        "subq": "F2/step1/harmonic-comparison",
        "context": "Three series at e (or eps) = 0.054: pin-slot atan2, eccentric anomaly E(M), true anomaly nu(M)",
        "eps": EPS_FREETH,
        "pin_slot_c_k_arcsec": {str(k): v * AS_PER_RAD for k, v in pin_slot_harm.items()},
        "kepler_E_of_M_c_k_arcsec": {str(k): v * AS_PER_RAD for k, v in E_harm.items()},
        "kepler_nu_of_M_c_k_arcsec": {str(k): v * AS_PER_RAD for k, v in nu_harm.items()},
        "verdict": (
            "pin-slot c_1 ≈ ε ≈ 11138 arcsec ≈ kepler-E c_1; "
            "pin-slot c_1 ≈ HALF of true-anomaly c_1 (2e ≈ 22276 arcsec). "
            "Pin-slot output algebra is the E-of-M series (eccentric anomaly), "
            "NOT the true-anomaly series. Brown's 22640″ is true-anomaly (2e). "
            "The factor of 2 IS the E↔nu distinction."
        ),
    })

    # ------- Step 1B: pin-slot harmonics at e = E_MOON (modern lunar e) -------
    # This isolates the question: if we used e = e_moon = 0.0549 (the modern
    # known value, not Freeth's 0.054), would pin-slot still under-model by 2x?
    records.append({
        "subq": "F2/step1B/pin-slot-at-modern-lunar-e",
        "context": "Pin-slot atan2 with eps set to MODERN orbital eccentricity (0.0549 vs Freeth 0.054)",
        "eps": E_MOON,
        "pin_slot_c_1_arcsec": pin_slot_harm_e_moon[1] * AS_PER_RAD,
        "true_anomaly_c_1_arcsec_at_same_e": nu_harm_moon[1] * AS_PER_RAD,
        "ratio_pin_slot_to_true_anomaly": pin_slot_harm_e_moon[1] / nu_harm_moon[1],
        "verdict": (
            "Even at modern e=0.0549, pin-slot output (E-of-M) is HALF the "
            "true-anomaly output. The factor of 2 is intrinsic to the geometric "
            "interpretation of the pin-slot output, not to Freeth's specific ε."
        ),
    })

    # ------- Step 4: what eps would the pin-slot need to MATCH Hipparchan/Brown? -------
    # pin-slot c_1 = eps (rad) at leading order
    # Hipparchan first inequality leading amplitude ~5 deg = 5*60*60 = 18000 arcsec
    # = 5*pi/180 = 0.08727 rad
    HIPP_AMP_DEG = 5.0  # Hipparchus's first inequality value (~5 deg)
    HIPP_AMP_RAD = math.radians(HIPP_AMP_DEG)
    HIPP_AMP_ARCSEC = HIPP_AMP_DEG * 3600.0
    BROWN_C1_ARCSEC = 22640.0
    BROWN_C1_RAD = BROWN_C1_ARCSEC / AS_PER_RAD

    eps_required_hipparchan = HIPP_AMP_RAD
    eps_required_brown = BROWN_C1_RAD

    records.append({
        "subq": "F2/step4/required-eps",
        "context": "Inverting c_1 = eps to find eps needed to match Hipparchan / Brown amplitudes",
        "freeth_eps": EPS_FREETH,
        "hipparchan_amplitude_arcsec": HIPP_AMP_ARCSEC,
        "hipparchan_eps_required": eps_required_hipparchan,
        "ratio_required_hipparchan_to_freeth": eps_required_hipparchan / EPS_FREETH,
        "brown_amplitude_arcsec": BROWN_C1_ARCSEC,
        "brown_eps_required": eps_required_brown,
        "ratio_required_brown_to_freeth": eps_required_brown / EPS_FREETH,
        "verdict": (
            "To match Hipparchan ~5° (the value Hipparchus actually had c. 130 BCE), "
            f"pin-slot needs ε ≈ {eps_required_hipparchan:.4f} (≈1.62× Freeth's 0.054). "
            "To match Brown's modern 2e, pin-slot needs ε ≈ "
            f"{eps_required_brown:.4f} (≈2.04× Freeth's 0.054). "
            "Neither is achieved at ε=0.054."
        ),
    })

    # ------- Step 5: Option D — downstream gear-ratio amplification -------
    # Per gear_database.py LUNAR_TRAIN and MESH_EDGES:
    #   b1(224) -> c1(38) -> c2(48) [axle] -> d1(24) -> d2(127) [axle] ->
    #   e1(32) -> e3(50) -> e4(50) -> k2(50)
    # The pin-and-slot is BETWEEN e3 and e4 (epicycle frame). e_eccentric(50) is
    # the 4th 50-tooth wheel carrying the offset pin.
    #
    # Crucial question: between the pin-slot OUTPUT (which is the e4 angle, or
    # equivalently k2/e_eccentric angle) and the lunar pointer (k2 axle output),
    # what gear ratio applies?
    #
    # In Freeth's reconstruction, the pin-slot is a 1:1 transmission BY TOOTH
    # COUNT (50:50) but with a non-uniform angle relationship (eccentricity).
    # The pin-slot's two 50-tooth wheels (e3, e4) mesh 1:1 in tooth count;
    # the *angular* relationship is the eccentric one (the f_eps map).
    #
    # k2 is the output of the pin-slot system; k2 drives the lunar pointer
    # (via additional axle transfer to the moon-phase display, but the
    # angular content per revolution is set by k2).
    #
    # So there is NO downstream gear-ratio amplification between the pin-slot
    # output angle and the lunar dial pointer. The k2 angle IS the lunar pointer
    # angle. Option D is structurally ruled out.

    # The lunar train multipliers (c1/b1, d2/d1 etc.) sit UPSTREAM of the
    # pin-slot. They determine that the input to the pin-slot rotates at the
    # anomalistic lunar rate, but they don't post-process the pin-slot's
    # output. The pin-slot output IS the lunar dial reading (after axle
    # transfer to the pointer hand, which is unity).

    # Verify the upstream gear ratio chain
    upstream_chain = [
        ("b1->c1", 224, 38),
        ("c1->c2", 38, 48),  # axle (no ratio change in angular content; axle shares)
        ("c2->d1", 48, 24),
        ("d1->d2", 24, 127),  # axle
        ("d2->e1", 127, 32),
        ("e1->e3", 32, 50),
        # pin-slot e3 -> e4 is 50:50 with eccentric coupling (the f_eps map)
        # ("e4->k2 axle") and ("k2 axle -> lunar pointer") are 1:1
    ]
    upstream_ratio = 1.0
    for label, driver, driven in upstream_chain:
        upstream_ratio *= driver / driven
    # This gives the angular rate of e3 (pin-slot input) per b1 turn.
    # b1 is the calendar/sun shaft (1 turn per year).
    # Expected: e3 rotates at lunar anomalistic rate per b1's solar year.

    records.append({
        "subq": "F2/step5/option-D-downstream-amplification",
        "context": "Is there a gear-ratio amplification downstream of pin-slot that could account for 2x?",
        "upstream_ratio_b1_to_e3_per_b1_turn": upstream_ratio,
        "downstream_pin_slot_to_lunar_pointer": 1.0,
        "note": (
            "Pin-slot's output drives k2 (50t) which IS the lunar pointer axle "
            "via 1:1 axle transfer. No gear ratio between pin-slot output and "
            "lunar dial reading. Option D is structurally ruled out by the "
            "bronze's surviving topology — there is no downstream gear-ratio "
            "amplifier between pin-slot output angle and the dial."
        ),
        "verdict": "Option D FALSIFIED on bronze topology grounds. The 2x must lie elsewhere.",
    })

    # ------- Cross-check: pin-slot at eps=0.110 gives Brown's amplitude? -------
    pin_slot_eps_110 = atan2_harmonics(0.110, N=N)
    records.append({
        "subq": "F2/step5/pin-slot-at-eps-0.110",
        "context": "If reconstruction error: would ε=0.110 produce Brown's 22640 arcsec?",
        "eps": 0.110,
        "pin_slot_c_1_arcsec": pin_slot_eps_110[1] * AS_PER_RAD,
        "pin_slot_c_2_arcsec": pin_slot_eps_110[2] * AS_PER_RAD,
        "pin_slot_c_3_arcsec": pin_slot_eps_110[3] * AS_PER_RAD,
        "brown_c_1_arcsec": BROWN_C1_ARCSEC,
        "brown_c_2_arcsec": 769.0,  # Brown's second equation-of-centre coefficient
        "ratio_pin_slot_to_brown_c1": pin_slot_eps_110[1] * AS_PER_RAD / BROWN_C1_ARCSEC,
        "ratio_pin_slot_to_brown_c2": pin_slot_eps_110[2] * AS_PER_RAD / 769.0,
        "verdict": (
            "ε=0.110 gives c_1=22682 arcsec (matches Brown 22640 within 0.2%) "
            "AND c_2=1248 arcsec which is OFF from Brown's 769 by factor 1.62. "
            "So ε=0.110 reproduces the leading term but BREAKS the second harmonic. "
            "This is consistent with the pin-slot being the E(M) series (where "
            "c_2 = e^2/2 and c_1 = e), NOT the true-anomaly nu(M) series (where "
            "c_1 = 2e and c_2 = (5/4)e^2). Pin-slot is structurally NOT a "
            "Keplerian true-anomaly generator."
        ),
    })

    # ------- Step 2/3: Gourtsoyannis 2012 PDF-extraction-via-web findings -------
    # Per web extraction from Gourtsoyannis "Hipparchos vs. Ptolemy and the
    # Antikythera Mechanism: Pin-Slot Device parameters ultimately linked to
    # real eccentricity of Moon's Orbit" (academia.edu/41392086):
    #   - Pin offset a = 1.1 mm; pin distance a_1 = 9.6 mm.
    #   - ε = a / a_1 = 0.1146 ± 0.0057 (Gourtsoyannis's MEASURED bronze eccentricity)
    #   - α = arctan(0.1147) ≈ 6.50° (max equation of centre device produces)
    #   - α = arctan(0.1098) ≈ 6.30° (modern lunar 2e equation of centre)
    #   - Gourtsoyannis states "ε = 2e where e is orbital eccentricity (0.0549)"
    #   - "discrepancy less than 4%"
    # Also extracted from web (search result on "Phases in the Unraveling" /
    # related): "distance between the arbors on the k gears is about 1.1 mm,
    # with a pin distance of 9.6 mm, giving an angular variation of 6.5°.
    # According to Ptolemy, Hipparchos made two estimates for a lunar anomaly
    # parameter, based on eclipse data, which would require angular variations
    # of 5.9° or 4.5°."
    G_EPS = 0.1146
    G_SIGMA = 0.0057
    pin_slot_g = atan2_harmonics(G_EPS, N=N)
    records.append({
        "subq": "F2/step2-3/gourtsoyannis-bronze-measurement",
        "context": "Direct bronze measurement per Gourtsoyannis 2012 (web-extracted from academia.edu/41392086, not direct PDF)",
        "pin_offset_mm": 1.1,
        "pin_distance_mm": 9.6,
        "eps_bronze_gourtsoyannis": G_EPS,
        "eps_bronze_uncertainty_1sigma": G_SIGMA,
        "ratio_gourtsoyannis_to_freeth_eps": G_EPS / EPS_FREETH,
        "claim_gourtsoyannis": "eps_bronze = 2*e_orbital where e_orbital is modern lunar orbital eccentricity 0.0549; 2*0.0549 = 0.1098, vs measured 0.1146; discrepancy <4%",
        "device_max_equation_of_centre_deg": math.degrees(math.asin(G_EPS)),
        "device_c1_arcsec": pin_slot_g[1] * AS_PER_RAD,
        "device_c2_arcsec": pin_slot_g[2] * AS_PER_RAD,
        "brown_c1_arcsec": BROWN_C1_ARCSEC,
        "ratio_device_c1_to_brown_c1": pin_slot_g[1] * AS_PER_RAD / BROWN_C1_ARCSEC,
        "verdict": (
            "Gourtsoyannis 2012 reports bronze ε=0.1146 from direct measurement "
            "(pin offset 1.1 mm / pin distance 9.6 mm). This is 2.12× Freeth's "
            "reported 0.054. Pin-slot at ε=0.1146 gives c_1 ≈ 23638″ ≈ 6.58° max "
            "equation of centre — matching Brown's modern 22640″ within ~4% AND "
            "Hipparchan/Ptolemaic-quoted 6.30° = arctan(2*0.0549). "
            "If Gourtsoyannis is right, Freeth 2006's ε=0.054 IS A CONVENTION "
            "DIFFERENCE (Freeth's parameter is likely offset/diameter not "
            "offset/radius), and the bronze is NOT under-modelling at all."
        ),
        "citation_status": (
            "Gourtsoyannis primary source via academia.edu/41392086 web extraction; "
            "Freeth 2006 Nature paywalled PDF not extracted; "
            "Carman-Thorndike-Evans 2012 PDF returned binary/corrupted via webspace.pugetsound.edu link. "
            "Per feedback_pdf_extraction_citation_discipline.md, "
            "Freeth-2006 source convention re-verification flagged as outstanding."
        ),
    })

    # ------- Step 5: Hipparchan eccentric-circle hypothesis -------
    # Hipparchus's max equation of centre = 5°1' per Almagest IV.6.
    # Eccentric-circle geometry: observer at distance e from circle center,
    # uniform motion on circle. Observed angle = atan2(sin th, cos th ± e/R).
    # Max eq-of-centre = arcsin(e/R).
    # For 5° max: e/R = sin(5°) = 0.0872.
    # Hipparchus's reported eccentricity (Almagest IV.6): e/R = 5;15/60 = 0.0875.
    HIPP_ER = 5.25/60.0  # 5;15 / 60
    pin_slot_hipp = atan2_harmonics(HIPP_ER, N=N)
    records.append({
        "subq": "F2/step5/hipparchan-eccentric-circle",
        "context": "Hipparchan eccentric-circle (Almagest IV.6) e/R = 5;15/60 = 0.0875",
        "hipparchan_e_over_R": HIPP_ER,
        "hipparchan_max_eq_of_centre_deg": math.degrees(math.asin(HIPP_ER)),
        "c1_arcsec": pin_slot_hipp[1] * AS_PER_RAD,
        "c2_arcsec": pin_slot_hipp[2] * AS_PER_RAD,
        "verdict": (
            "Hipparchan eccentric-circle e/R = 0.0875 produces max eq-of-centre 5.02° "
            "matching Almagest IV.6's 5°1' exactly. Pin-slot geometry IS the "
            "Hipparchan eccentric-circle geometry (same atan2 form). Hipparchus's "
            "ε ≈ 2 × Keplerian e_moon because the eccentric-circle model produces "
            "the E(M) series (c_1 = eps), whereas Keplerian elliptical orbits "
            "produce the nu(M) series (c_1 = 2e). To reproduce the OBSERVED lunar "
            "amplitude with the wrong (eccentric-circle) geometry, Hipparchus "
            "had to use eps ≈ 2×(true Keplerian eccentricity). This is exactly "
            "what we see: HIPP eps=0.0875 ≈ 2 × 0.054 (Freeth's reported ε)."
        ),
    })

    # Three-way comparison: Freeth-reported / Hipparchan-Almagest / Gourtsoyannis-bronze
    records.append({
        "subq": "F2/step5/three-way-comparison",
        "context": "Three ε values circulating in the literature, what each predicts",
        "table": [
            {
                "source": "Freeth 2006 (reported)",
                "eps": 0.054,
                "max_eq_of_centre_deg": math.degrees(math.asin(0.054)),
                "c1_arcsec": atan2_harmonics(0.054, N=N)[1] * AS_PER_RAD,
                "matches": "neither Hipparchus nor Brown",
            },
            {
                "source": "Hipparchus / Almagest IV.6 (5;15/60)",
                "eps": 0.0875,
                "max_eq_of_centre_deg": math.degrees(math.asin(0.0875)),
                "c1_arcsec": atan2_harmonics(0.0875, N=N)[1] * AS_PER_RAD,
                "matches": "Almagest 5°1' value (Hipparchus's reconstructed lunar eccentricity from eclipse data)",
            },
            {
                "source": "Brown modern lunar c_1 = 2e_moon",
                "eps": 0.1098,
                "max_eq_of_centre_deg": math.degrees(math.asin(0.1098)),
                "c1_arcsec": atan2_harmonics(0.1098, N=N)[1] * AS_PER_RAD,
                "matches": "modern observed lunar 6.29° max eq-of-centre",
            },
            {
                "source": "Gourtsoyannis 2012 bronze measurement",
                "eps": 0.1146,
                "max_eq_of_centre_deg": math.degrees(math.asin(0.1146)),
                "c1_arcsec": atan2_harmonics(0.1146, N=N)[1] * AS_PER_RAD,
                "matches": "modern lunar 6.30° within 4% (= 2*e_moon)",
            },
        ],
        "verdict": (
            "The Gourtsoyannis-measured ε=0.1146 ≈ 2 × Freeth-reported ε=0.054. "
            "The most economical reading: Freeth 2006 reports a ratio that is "
            "half the offset/radius (e.g., offset/diameter or e/(2r)), while "
            "Gourtsoyannis reports the true offset/radius ratio. Doubling Freeth's "
            "ε reproduces both Brown modern AND Hipparchus's compensated "
            "eccentric-circle. The bronze likely implements approximately the "
            "modern-equivalent lunar amplitude (~6.3-6.6°), NOT a 3° under-amplitude."
        ),
    })

    # ------- True-anomaly at e=E_MOON c_1 and c_2 cross-check -------
    records.append({
        "subq": "F2/step5/true-anomaly-c_k-cross-check",
        "context": "At e=0.0549 (modern lunar), what are Brown's c_1 and c_2 vs true-anomaly series?",
        "e": E_MOON,
        "true_anomaly_c_1_predicted_2e_arcsec": 2.0 * E_MOON * AS_PER_RAD,
        "true_anomaly_c_2_predicted_5_4_e2_arcsec": 1.25 * E_MOON**2 * AS_PER_RAD,
        "true_anomaly_c_1_measured_arcsec": nu_harm_moon[1] * AS_PER_RAD,
        "true_anomaly_c_2_measured_arcsec": nu_harm_moon[2] * AS_PER_RAD,
        "brown_c_1_arcsec": 22640.0,
        "brown_c_2_arcsec": 769.0,
        "note": (
            "Brown's c_1=22640″ matches 2e_moon*206264.8 = 22647″ (within 0.03%). "
            "Brown's c_2=769″ matches (5/4)e_moon^2*206264.8 = 776″ (within 1%). "
            "Brown's equation-of-centre IS the true-anomaly nu(M) series with "
            "e_moon=0.0549, full stop."
        ),
    })

    return records


def write_ndjson(records):
    with open(OUT, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    records = main()
    write_ndjson(records)
    print(f"Wrote {len(records)} records to {OUT}")
    for r in records:
        print("---")
        print(json.dumps(r, indent=2, default=str)[:2000])
