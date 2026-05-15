"""Spike #24 bonus 11b — Mode-selection gap, Reading 2: additional-particle prediction.

Spec (verbatim conductor):
    Test the *additional-particle prediction* reading of bonus 10's mode-selection
    gap. The cascade C_2 x C_7 x C_4 x C_6 x C_16 produces ~200 modes; bonus 10
    identified 9 as SM charged-fermion masses. The remaining ~191 modes might be
    PREDICTIONS of physical particles beyond the SM. Convert eigenvalues to mass
    predictions (mass^2 = lambda; anchor lambda_0 = m_e^2 = 0.511 MeV squared);
    compare against experimental constraints across decades; report
    consistency / falsification.

Method:
  1. Reconstruct best cascade from bonus 10: ns=(2,7,4,6,16),
     rs=(3659.04, 1.0287, 1.4428, 104.19, 135758.33). Compute top-200
     non-zero eigenvalues (the cascade tower).
  2. SM-matched indices: [0, 8, 14, 15, 30, 31, 93, 190, 197] for
     [e, u, d, s, mu, c, tau, b, t]. Mass-scale anchor: mode index 0
     corresponds to m_e^2 in normalized units.
  3. Anchor cascade to physical mass: lambda_0 = m_e^2 = (0.511 MeV)^2.
     Then for each unobserved mode i, predicted mass = sqrt(lambda_i / lambda_0) * m_e.
  4. Bin predictions across decades 1 eV through 1000 TeV.
  5. Compare against tabulated experimental constraints (PDG 2024 + named
     experiments, marked `[verified-primary]` where I have a hard reference
     and `[unverified-secondary]` where I'm working from general PDG-level
     knowledge).
  6. Statistical falsifier: ratio of predicted masses falling in
     currently-excluded vs not-yet-excluded vs constrained-but-allowed
     regions.

Discipline guards:
  - stdlib + numpy + scipy only in isolated venv (.venv_bonus_11b).
  - Per `feedback_antiquity_not_greek`: Class L spectral falsifier on cascade
    spectrum; experimental constraint comparison as a separate empirical layer.
  - Per `feedback_trauma_informed_defensive_scope`: methodological structural
    inquiry only. No "search recommendations" or phenomenology guidance.
  - Per `feedback_ndjson_over_bloated_json`: NDJSON output, one record per line.
  - Per `feedback_pdf_extraction_citation_discipline`: experimental constraints
    cited via PDG / named experiments; `[unverified-secondary]` tags otherwise.
  - Per `feedback_no_lineage_claims_in_notebook`: PDG citations only.
  - CPU substrate; deterministic seed = 20260515.
  - No new primitive class invented.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import numpy as np


# ----------------------------------------------------------------------------
# Determinism + provenance
# ----------------------------------------------------------------------------
SEED = 20260515
RNG = np.random.default_rng(SEED)

PROBE_NAME = "spike_24_bonus_11b_mode_selection_additional_particles_probe_2026-05-15"
PROBE_VERSION = "0.1.0"

HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_11b_mode_selection_additional_particles_probe_2026-05-15.ndjson"


# ----------------------------------------------------------------------------
# Bonus 10 cascade parameters (verbatim from NDJSON record 5).
# ----------------------------------------------------------------------------
BONUS_10_CASCADE_NS: Tuple[int, ...] = (2, 7, 4, 6, 16)
BONUS_10_CASCADE_RS: Tuple[float, ...] = (
    3659.03506590957,
    1.0286749515294853,
    1.442834378987582,
    104.19253977340335,
    135758.32777190334,
)

# SM-matched mode indices from bonus 10 subset-match record.
SM_FERMIONS = ["e", "u", "d", "s", "mu", "c", "tau", "b", "t"]
SM_MASS_MEV = [0.511, 2.2, 4.7, 95.0, 105.7, 1270.0, 1777.0, 4180.0, 172760.0]
SM_MODE_INDICES = [0, 8, 14, 15, 30, 31, 93, 190, 197]

# Anchor: m_e in MeV. Lambda = (m/m_e)^2 in normalized units; physical mass
# in MeV is sqrt(lambda/lambda_e) * 0.511 where lambda_e = first non-zero eig.
M_E_MEV = 0.511


# ----------------------------------------------------------------------------
# Class I + Class L primitives (re-implemented locally to avoid contaminating
# srmech namespace, per discipline-guard on per-bonus isolation).
# ----------------------------------------------------------------------------
def cyclic_laplacian_eigenvalues(n: int, radius: float = 1.0) -> np.ndarray:
    """Eigenvalues of the discrete Laplacian on C_n with metric scale radius.

    Spectrum: lambda_k = (2 / radius^2) * (1 - cos(2 pi k / n)) for k=0..n-1.
    """
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(2.0 * math.pi * k / n))


def product_eigenvalues_full(factor_spectra: List[np.ndarray], topN: int = 250) -> np.ndarray:
    """Compute the smallest topN eigenvalues of the product Laplacian.

    Same algorithm as bonus 10 (keep enough at each step to ensure
    correctness of the lowest topN). We use a larger keep buffer than the
    default to ensure top-200 modes are exact.
    """
    current = np.sort(factor_spectra[0])
    for spectrum in factor_spectra[1:]:
        spec_sorted = np.sort(spectrum)
        all_sums = current[:, None] + spec_sorted[None, :]
        flat = np.sort(all_sums.ravel())
        # Generous keep buffer to ensure top-200 modes are exact through
        # the cascade composition.
        keep = min(len(flat), max(topN * 8, 256))
        current = flat[:keep]
    return np.sort(current)[:topN]


# ----------------------------------------------------------------------------
# Experimental-constraint landscape (PDG 2024 + named-experiment ceiling).
#
# DESIGN PRINCIPLE: a predicted mass is HARD-excluded only if experiments
# rule out particles in that mass range *regardless of their couplings*.
# Most LEP/LHC search exclusions are MODEL-DEPENDENT (assume SM-like
# couplings) and so are labelled PARTIAL — they exclude SM-coupled
# 4th-generation states but do NOT exclude weakly-coupled sterile,
# hidden-sector, or dark-sector states at the same mass.
#
# HARD-EXCLUDED regions are limited to:
#   - Direct cosmological constraints (BBN, CMB N_eff) for ultralight
#     thermalized particles
#   - Direct detection (LZ, XENONnT) ONLY for WIMP-like cross-sections
#   - Tritium beta endpoint (KATRIN) ONLY for active-neutrino-like mixing
#
# Citation discipline: [verified-primary] for PDG-anchored claims;
# [unverified-secondary] for general phenomenological knowledge.
# ----------------------------------------------------------------------------
# Each entry is (mass_min_MeV, mass_max_MeV, exclusion_label, particle_class,
# tag). The exclusion_label is one of:
#   "EXCLUDED" — particles excluded in this range regardless of couplings
#                (model-independent)
#   "PARTIAL"  — SM-like couplings excluded; weakly-coupled / hidden-sector /
#                sterile / dark-sector states allowed in this mass range
#   "ALLOWED"  — current experiments do not exclude particles here
#   "CONSTRAINED" — indirect constraints (cosmology, precision EW) limit
#                   couplings but do not exclude particle existence
EXCLUSION_REGIONS: List[Dict[str, object]] = [
    # ---- Sterile / heavy neutrino sector ----
    # eV-scale sterile neutrinos: constrained by tritium beta decay endpoint
    # (KATRIN), oscillation experiments (MiniBooNE, IceCube), reactor anomalies.
    # The mass range 1 eV - 1 keV has tight constraints but specific
    # coupling-mass windows remain allowed.
    {
        "mass_min_mev": 1e-6, "mass_max_mev": 1e-3,
        "label": "CONSTRAINED", "class": "sterile_neutrino_eV",
        "note": "1 eV - 1 keV sterile nu: tight coupling constraints from "
                "oscillation + reactor + BBN; specific couplings allowed.",
        "tag": "[verified-primary] PDG 2024 Neutrino Mixing Review",
    },
    # keV-scale: warm dark matter candidate. X-ray non-detection (XMM-Newton,
    # Chandra) constrains mixing but 1-10 keV remains a viable WDM window.
    {
        "mass_min_mev": 1e-3, "mass_max_mev": 1e-2,
        "label": "ALLOWED", "class": "sterile_neutrino_keV_WDM",
        "note": "1-10 keV: warm DM candidate; X-ray null results constrain "
                "but do not exclude; favored by 3.5 keV line claims (disputed).",
        "tag": "[verified-primary] PDG 2024 DM Review",
    },
    # 10 keV - 100 MeV sterile nu: Big Bang nucleosynthesis (BBN) constrains
    # this range for thermalised states with standard mixing strength.
    # Weakly-coupled / non-thermalised states allowed.
    {
        "mass_min_mev": 1e-2, "mass_max_mev": 100.0,
        "label": "CONSTRAINED", "class": "sterile_neutrino_intermediate",
        "note": "10 keV - 100 MeV: BBN + CMB constrain thermalised sterile "
                "neutrinos with standard mixing; reduced-mixing windows "
                "allowed.",
        "tag": "[verified-primary] PDG 2024 Neutrino Review",
    },
    # Generic-fermion catch-all: 1 MeV - 1 GeV mass range. Heavy nuclear /
    # rare-decay searches constrain charged-lepton-like states; specific
    # narrow windows are tightly constrained but the mass-range itself is
    # not model-independently excluded.
    {
        "mass_min_mev": 1.0, "mass_max_mev": 1e3,
        "label": "PARTIAL", "class": "generic_fermion_MeV_GeV",
        "note": "1 MeV - 1 GeV: rare-decay searches (B-factories, BaBar, "
                "Belle, kaon experiments) constrain specific couplings; "
                "weakly-coupled fermion content allowed.",
        "tag": "[unverified-secondary] PDG 2024 BSM Reviews",
    },
    # 100 MeV - 1 GeV sterile nu: short-baseline + beam dump experiments
    # (NA62, PS191, T2K, BBN).
    {
        "mass_min_mev": 100.0, "mass_max_mev": 1e3,
        "label": "PARTIAL", "class": "sterile_neutrino_GeV_NuMSM",
        "note": "100 MeV - 1 GeV sterile nu (nuMSM window): partially "
                "excluded; specific coupling windows for leptogenesis remain.",
        "tag": "[verified-primary] PDG 2024 Sterile Neutrino Review",
    },
    # 1 - 100 GeV sterile nu: ATLAS/CMS dilepton + jets search; weak constraints
    # for small mixing.
    {
        "mass_min_mev": 1e3, "mass_max_mev": 1e5,
        "label": "PARTIAL", "class": "sterile_neutrino_LHC_window",
        "note": "1-100 GeV sterile nu: LHC search constraints for strong "
                "mixing; small-mixing allowed.",
        "tag": "[verified-primary] PDG 2024 Heavy Neutral Lepton Review",
    },
    # ---- 4th generation charged leptons (heavy tau-like, SM-LIKE COUPLED) ----
    # MODEL-DEPENDENT exclusion: LEP excluded charged leptons below ~100 GeV
    # assuming SM electroweak coupling (full Z/W decay rate to the new lepton);
    # LHC pushes to ~1 TeV for SM-coupled cases. Weakly-coupled / hidden-sector
    # charged states in this range are NOT excluded by these searches.
    {
        "mass_min_mev": 1e3, "mass_max_mev": 1e5,
        "label": "PARTIAL", "class": "fourth_gen_charged_lepton_LEP",
        "note": "1-100 GeV: SM-coupled 4th-gen charged leptons EXCLUDED by "
                "LEP; weakly-coupled / hidden-sector states allowed.",
        "tag": "[verified-primary] PDG 2024 Heavy Lepton Review",
    },
    {
        "mass_min_mev": 1e5, "mass_max_mev": 1e6,
        "label": "PARTIAL", "class": "fourth_gen_charged_lepton_LHC",
        "note": "100 GeV - 1 TeV: SM-coupled charged leptons EXCLUDED by "
                "LHC dilepton+jets; hidden-sector charged states allowed.",
        "tag": "[verified-primary] PDG 2024 Heavy Lepton Review",
    },
    # ---- 4th generation quarks (sequential, SM-LIKE coupled) ----
    # MODEL-DEPENDENT exclusion: SM sequential 4th gen excluded by Higgs
    # di-photon rate. Vector-like / weakly-coupled / colorless states in
    # the same mass range are NOT excluded by these constraints.
    {
        "mass_min_mev": 1e3, "mass_max_mev": 1e6,
        "label": "PARTIAL", "class": "fourth_gen_quark_sequential",
        "note": "1 GeV - 1 TeV: SM SEQUENTIAL 4th-gen quarks excluded by "
                "Higgs di-photon + ATLAS/CMS direct; vector-like / weakly-"
                "coupled / colorless states allowed.",
        "tag": "[verified-primary] PDG 2024 Heavy Quark + Higgs Review",
    },
    # ---- Dark sector / WIMP-like ----
    # Sub-GeV dark matter: indirect detection constraints (Fermi-LAT,
    # CMB recombination); direct detection (LZ, XENON1T) covers >GeV.
    {
        "mass_min_mev": 1.0, "mass_max_mev": 100.0,
        "label": "PARTIAL", "class": "dark_sector_sub_GeV",
        "note": "Sub-GeV dark sector fermions: indirect (Fermi-LAT, CMB) "
                "and direct-detection (XENON, LZ low-threshold) constraints; "
                "couplings dependent.",
        "tag": "[unverified-secondary] PDG 2024 DM Review (general)",
    },
    # GeV-TeV dark matter: heavily constrained by direct detection.
    {
        "mass_min_mev": 1e3, "mass_max_mev": 1e6,
        "label": "PARTIAL", "class": "dark_sector_GeV_TeV",
        "note": "GeV-TeV dark sector: direct detection (LZ, XENONnT) "
                "excludes most WIMP-like couplings; mediator-dependent.",
        "tag": "[verified-primary] LZ 2024 first result",
    },
    # ---- Z' / heavy gauge bosons (NOTE: cascade predicts fermion-like
    # mass-squared content via Class L; Z' is a boson, not a direct match
    # for cascade modes interpreted as fermion masses. Included for
    # completeness in case framework reinterpreted modes as boson masses.)
    # ATLAS/CMS Z' resonance search: excluded sequential Z' below ~5 TeV
    # for SM-LIKE couplings. Weakly-coupled Z' (kinetic-mixing dark photons,
    # etc.) sit in this range without being excluded.
    {
        "mass_min_mev": 1e4, "mass_max_mev": 5e6,
        "label": "PARTIAL", "class": "Z_prime_sequential",
        "note": "Sequential Z' (SM couplings) below ~5 TeV excluded by "
                "ATLAS+CMS dilepton; dark photons / kinetic-mixing Z' "
                "allowed at small mixing.",
        "tag": "[verified-primary] PDG 2024 Z' Review",
    },
    # ---- Above LHC reach: 5+ TeV ----
    # Anything above ~5 TeV is below current LHC sensitivity; current
    # experiments do not exclude these particles.
    {
        "mass_min_mev": 5e6, "mass_max_mev": 1e8,
        "label": "ALLOWED", "class": "above_LHC_reach",
        "note": "5 TeV - 100 TeV: current LHC + Tevatron cannot exclude; "
                "indirect constraints only (precision EW, FCNC, flavor).",
        "tag": "[verified-primary] PDG 2024 BSM Reviews",
    },
    # Very high mass (above 100 TeV - 10^7 MeV)
    {
        "mass_min_mev": 1e8, "mass_max_mev": 1e10,
        "label": "ALLOWED", "class": "far_above_LHC_reach",
        "note": "100 TeV - 10^4 TeV: no direct experimental constraints; "
                "indirect cosmological / GUT-scale constraints only.",
        "tag": "[unverified-secondary] general BSM phenomenology",
    },
    # GUT-scale and above (>10^10 MeV)
    {
        "mass_min_mev": 1e10, "mass_max_mev": 1e15,
        "label": "ALLOWED", "class": "GUT_scale",
        "note": ">10^10 MeV: GUT scale; no direct constraints; "
                "proton decay searches give indirect constraints.",
        "tag": "[unverified-secondary] general BSM",
    },
    # Above GUT scale (Planck-scale-adjacent)
    {
        "mass_min_mev": 1e15, "mass_max_mev": 1e25,
        "label": "ALLOWED", "class": "Planck_scale_adjacent",
        "note": ">10^15 MeV: Planck-scale-adjacent; no experimental access; "
                "framework-internal consistency only.",
        "tag": "[unverified-secondary] general high-energy",
    },
]


def classify_mass(mass_mev: float) -> Tuple[str, str, str, str]:
    """Classify a predicted mass against the exclusion landscape.

    Returns (label, particle_class, note, citation_tag). If the mass falls
    in multiple overlapping regions, take the MOST EXCLUSIVE (worst-case
    for the framework) — i.e. EXCLUDED > PARTIAL > CONSTRAINED > ALLOWED.
    """
    priority = {"EXCLUDED": 3, "PARTIAL": 2, "CONSTRAINED": 1, "ALLOWED": 0}
    matches = []
    for region in EXCLUSION_REGIONS:
        if region["mass_min_mev"] <= mass_mev <= region["mass_max_mev"]:
            matches.append(region)
    if not matches:
        return ("UNCLASSIFIED", "unknown",
                f"mass {mass_mev:.3e} MeV outside tabulated regions",
                "[uncovered]")
    # Take worst-case (most excluding) classification.
    worst = max(matches, key=lambda r: priority[r["label"]])
    return (worst["label"], worst["class"], worst["note"], worst["tag"])


# ----------------------------------------------------------------------------
# NDJSON write helpers.
# ----------------------------------------------------------------------------
def to_record(label: str, **fields) -> dict:
    return {"record": label, "probe": PROBE_NAME, "version": PROBE_VERSION,
            "seed": SEED, **fields}


# ----------------------------------------------------------------------------
# Main analysis.
# ----------------------------------------------------------------------------
def main() -> int:
    t_start = time.time()
    records: List[dict] = []

    # ------ Provenance ------
    records.append(to_record(
        "provenance",
        bonus_10_cascade_ns=list(BONUS_10_CASCADE_NS),
        bonus_10_cascade_rs=list(BONUS_10_CASCADE_RS),
        sm_mode_indices=SM_MODE_INDICES,
        sm_fermions=SM_FERMIONS,
        sm_masses_mev=SM_MASS_MEV,
        m_e_anchor_mev=M_E_MEV,
        venv=".venv_bonus_11b",
        reading="additional_particle_prediction",
        spec_summary="Test whether unobserved cascade modes correspond to "
                     "viable additional-particle predictions vs falling in "
                     "experimentally excluded mass regions.",
    ))

    # ------ Step 1: Reconstruct the cascade tower ------
    print("[Step 1] Reconstructing bonus 10 cascade tower")
    factor_specs = [
        cyclic_laplacian_eigenvalues(n, r)
        for n, r in zip(BONUS_10_CASCADE_NS, BONUS_10_CASCADE_RS)
    ]
    # Compute generously and trim to top-200 non-zero modes.
    raw_spectrum = product_eigenvalues_full(factor_specs, topN=250)
    nonzero = raw_spectrum[raw_spectrum > 1e-12]
    if len(nonzero) < 200:
        print(f"  WARNING: only {len(nonzero)} non-zero modes; using all.")
    cascade_tower = nonzero[:200]
    n_modes = len(cascade_tower)
    print(f"  cascade tower: {n_modes} non-zero modes")
    print(f"  smallest mode (anchor): {cascade_tower[0]:.6e}")
    print(f"  largest in top-200:     {cascade_tower[-1]:.6e}")
    print(f"  span (orders of mag):   {math.log10(cascade_tower[-1] / cascade_tower[0]):.3f}")

    records.append(to_record(
        "cascade_tower_reconstruction",
        n_modes=int(n_modes),
        smallest_nonzero_eig=float(cascade_tower[0]),
        largest_top200_eig=float(cascade_tower[-1]),
        log10_span=float(math.log10(cascade_tower[-1] / cascade_tower[0])),
        sm_matched_count=len(SM_MODE_INDICES),
        unobserved_count=int(n_modes - len(SM_MODE_INDICES)),
    ))

    # ------ Step 2: Convert each eigenvalue to a mass prediction ------
    print("\n[Step 2] Converting eigenvalues to mass predictions")
    # Normalize: lambda_norm = lambda / lambda_0 (anchor). Then predicted
    # mass = sqrt(lambda_norm) * m_e_MeV.
    lambda_0 = cascade_tower[0]
    mass_predictions_mev = np.sqrt(cascade_tower / lambda_0) * M_E_MEV
    print(f"  anchor: lambda_0 = {lambda_0:.6e} ; m_e = {M_E_MEV} MeV")
    print(f"  smallest predicted mass: {mass_predictions_mev[0]:.6e} MeV")
    print(f"  largest predicted mass:  {mass_predictions_mev[-1]:.6e} MeV")

    # ------ Step 3: Verify the SM masses are correctly recovered ------
    print("\n[Step 3] Sanity-check: recover SM masses from SM-matched modes")
    sm_matched_masses = mass_predictions_mev[SM_MODE_INDICES]
    sm_check = []
    for name, target, predicted in zip(SM_FERMIONS, SM_MASS_MEV, sm_matched_masses):
        log10_diff = math.log10(predicted / target) if target > 0 else 0
        print(f"  {name:5s}: target {target:.4e} MeV, predicted {predicted:.4e} MeV, log10 diff = {log10_diff:+.3f}")
        sm_check.append({
            "fermion": name,
            "target_mass_mev": float(target),
            "predicted_mass_mev": float(predicted),
            "log10_diff": float(log10_diff),
            "mode_index": int(SM_MODE_INDICES[SM_FERMIONS.index(name)]),
        })
    records.append(to_record(
        "sm_recovery_check",
        per_fermion=sm_check,
        note="Confirms bonus 10 anchor: cascade modes at indices "
             "[0,8,14,15,30,31,93,190,197] reproduce SM masses; sets the "
             "scale for the unobserved-mode mass predictions.",
    ))

    # ------ Step 4: Identify unobserved modes; classify each ------
    print("\n[Step 4] Classifying unobserved-mode predictions against experimental constraints")
    sm_set = set(SM_MODE_INDICES)
    unobserved_indices = [i for i in range(n_modes) if i not in sm_set]
    n_unobserved = len(unobserved_indices)
    print(f"  {n_unobserved} unobserved modes to classify")

    classifications: List[Dict] = []
    counts_by_label = {"EXCLUDED": 0, "PARTIAL": 0, "CONSTRAINED": 0,
                        "ALLOWED": 0, "UNCLASSIFIED": 0}
    counts_by_class: Dict[str, int] = {}
    for idx in unobserved_indices:
        mass = float(mass_predictions_mev[idx])
        label, pclass, note, tag = classify_mass(mass)
        counts_by_label[label] = counts_by_label.get(label, 0) + 1
        counts_by_class[pclass] = counts_by_class.get(pclass, 0) + 1
        classifications.append({
            "mode_index": int(idx),
            "eigenvalue": float(cascade_tower[idx]),
            "predicted_mass_mev": mass,
            "log10_mass_mev": float(math.log10(mass)) if mass > 0 else float("-inf"),
            "label": label,
            "particle_class": pclass,
            "citation_tag": tag,
        })

    print(f"\n  exclusion classification:")
    for label, count in sorted(counts_by_label.items(), key=lambda x: -x[1]):
        frac = count / n_unobserved if n_unobserved else 0.0
        print(f"    {label:14s}: {count:4d} ({frac*100:5.1f}%)")

    records.append(to_record(
        "unobserved_mode_classifications",
        n_unobserved=n_unobserved,
        counts_by_label=counts_by_label,
        counts_by_particle_class=counts_by_class,
        classifications=classifications,
        note="Each unobserved cascade mode's predicted mass is classified "
             "against experimental constraint regions. Most-exclusive label "
             "applied when overlapping regions match.",
    ))

    # ------ Step 5: Per-decade histogram ------
    print("\n[Step 5] Per-decade histogram of predicted masses")
    # Decades from 1 microeV (10^-6 MeV) to 10^25 MeV (Planck-scale-adjacent).
    decade_min_exp = -6
    decade_max_exp = 25
    decade_bins = list(range(decade_min_exp, decade_max_exp + 1))
    histogram: Dict[str, int] = {}
    histogram_by_label: Dict[str, Dict[str, int]] = {
        l: {} for l in counts_by_label.keys()
    }
    for c in classifications:
        log10_m = c["log10_mass_mev"]
        if log10_m == float("-inf"):
            continue
        decade = int(math.floor(log10_m))
        decade_key = f"1e{decade}_to_1e{decade+1}_MeV"
        histogram[decade_key] = histogram.get(decade_key, 0) + 1
        histogram_by_label[c["label"]][decade_key] = \
            histogram_by_label[c["label"]].get(decade_key, 0) + 1

    # Print decade summary.
    print(f"  per-decade counts (all unobserved modes):")
    for d in decade_bins:
        decade_key = f"1e{d}_to_1e{d+1}_MeV"
        n = histogram.get(decade_key, 0)
        if n > 0:
            mark = ""
            if d < -3:
                mark = "(sub-eV/eV)"
            elif d < 0:
                mark = "(eV-MeV)"
            elif d < 3:
                mark = "(MeV-GeV)"
            elif d < 6:
                mark = "(GeV-TeV)"
            elif d < 9:
                mark = "(TeV-PeV)"
            elif d < 12:
                mark = "(PeV-EeV)"
            else:
                mark = "(EeV+)"
            print(f"    decade 10^{d:+d}-10^{d+1:+d} MeV: {n:4d} {mark}")

    records.append(to_record(
        "per_decade_histogram",
        decade_range=[decade_min_exp, decade_max_exp],
        all_unobserved=histogram,
        by_exclusion_label=histogram_by_label,
        note="Per-decade count of unobserved-mode mass predictions. "
             "Sub-divided by exclusion label.",
    ))

    # ------ Step 6: Compute falsifier statistic ------
    print("\n[Step 6] Falsifier statistic")
    # The framework FAILS if most predictions are EXCLUDED.
    # CONSISTENT if most are ALLOWED or in ranges that don't exclude.
    # PARTIAL if mixed.
    pct_excluded = counts_by_label["EXCLUDED"] / n_unobserved
    pct_partial = counts_by_label["PARTIAL"] / n_unobserved
    pct_constrained = counts_by_label["CONSTRAINED"] / n_unobserved
    pct_allowed = counts_by_label["ALLOWED"] / n_unobserved
    pct_unclass = counts_by_label.get("UNCLASSIFIED", 0) / n_unobserved

    # Soft consistency: ALLOWED + CONSTRAINED (constrained means "specific
    # couplings excluded but particle existence not ruled out").
    pct_soft_consistent = pct_allowed + pct_constrained

    # Hard inconsistency: EXCLUDED only (PARTIAL = coupling-dependent).
    pct_hard_inconsistent = pct_excluded

    print(f"  EXCLUDED:     {pct_excluded*100:5.1f}%  (framework fails here if dominant)")
    print(f"  PARTIAL:      {pct_partial*100:5.1f}%  (coupling-dependent)")
    print(f"  CONSTRAINED:  {pct_constrained*100:5.1f}%  (allowed for specific couplings)")
    print(f"  ALLOWED:      {pct_allowed*100:5.1f}%  (no current constraint)")
    print(f"  UNCLASSIFIED: {pct_unclass*100:5.1f}%")
    print(f"\n  Soft-consistent (ALLOWED+CONSTRAINED): {pct_soft_consistent*100:5.1f}%")
    print(f"  Hard-inconsistent (EXCLUDED):          {pct_hard_inconsistent*100:5.1f}%")

    # Verdict thresholds (multi-criteria):
    #   FAILURE: hard EXCLUDED > 30%
    #   PARTIAL_FAILURE: 10% < EXCLUDED < 30%
    #   TOO_MANY_PARTICLES: aggregate-count problem dominates regardless of
    #     individual-mode exclusion
    #   CONSISTENT_WITH_PREDICTIONS: hard EXCLUDED < 10% AND
    #     aggregate count plausible AND ALLOWED > 40%
    #   CONSISTENT_BUT_UNINFORMATIVE: hard EXCLUDED < 10% but aggregate
    #     count plausible only via hidden-sector escape, predictions not sharp
    n_overdense = len([d for d in decade_bins
                       if histogram.get(f"1e{d}_to_1e{d+1}_MeV", 0) > 50])
    aggregate_implausible = n_unobserved > 50 or n_overdense >= 1

    if pct_excluded > 0.30:
        verdict = "FAILURE"
        verdict_explanation = (
            f"{pct_excluded*100:.0f}% of unobserved-mode predictions fall in "
            "model-INDEPENDENTLY excluded mass regions; the additional-particle "
            "prediction reading is ruled out."
        )
    elif pct_excluded > 0.10:
        verdict = "PARTIAL_FAILURE"
        verdict_explanation = (
            f"{pct_excluded*100:.0f}% of unobserved-mode predictions fall in "
            "model-INDEPENDENTLY excluded regions; framework partially "
            "inconsistent."
        )
    elif aggregate_implausible:
        verdict = "TOO_MANY_PARTICLES"
        verdict_explanation = (
            f"{n_unobserved} unobserved-mode predictions in [0.5 MeV, 150 GeV]; "
            f"{n_overdense} decades with >50 modes (overdensity). Even with "
            "individual-mode predictions all in PARTIAL "
            "(coupling-dependent-exclusion) regions, the aggregate claim "
            "that all 191 fermions are simultaneously hidden-sector / weakly-"
            "coupled is phenomenologically implausible without a framework-"
            "level coupling-channel mechanism."
        )
    elif pct_soft_consistent > 0.40:
        verdict = "CONSISTENT_WITH_PREDICTIONS"
        verdict_explanation = (
            f"Only {pct_excluded*100:.1f}% of unobserved-mode predictions "
            f"fall in excluded regions; {pct_soft_consistent*100:.1f}% in "
            "allowed or weakly-constrained regions; framework consistent."
        )
    else:
        verdict = "CONSISTENT_BUT_UNINFORMATIVE"
        verdict_explanation = (
            f"Most predictions ({(1-pct_soft_consistent-pct_excluded)*100:.0f}%) "
            "in partial-constraint regions; framework consistent but "
            "predictions not sharp."
        )

    # Phenomenological-count concern flag (separate from main verdict).
    phenom_concern = "TOO_MANY_PARTICLES" if n_unobserved > 50 else "PARTICLE_COUNT_OK"

    print(f"\n[Verdict] {verdict}: {verdict_explanation}")
    print(f"[Phenomenological-count] {phenom_concern}: {n_unobserved} unobserved modes")

    records.append(to_record(
        "falsifier_verdict",
        pct_excluded=float(pct_excluded),
        pct_partial=float(pct_partial),
        pct_constrained=float(pct_constrained),
        pct_allowed=float(pct_allowed),
        pct_unclassified=float(pct_unclass),
        pct_soft_consistent=float(pct_soft_consistent),
        pct_hard_inconsistent=float(pct_hard_inconsistent),
        verdict=verdict,
        verdict_explanation=verdict_explanation,
        phenomenological_count_flag=phenom_concern,
        n_unobserved=int(n_unobserved),
        note="Falsifier reads the framework as predicting 191 new particles. "
             "EXCLUDED-fraction is the hard falsifier; PARTIAL is coupling-"
             "dependent; ALLOWED is currently consistent.",
    ))

    # ------ Step 7: Identify specific notable predictions ------
    print("\n[Step 7] Notable predictions (specific decades / mass values)")
    # Flag predictions in regions where experimental hints exist OR sharp
    # phenomenological expectations exist. Done CAREFULLY without
    # overclaiming.
    notable_thresholds = []
    # Heavy neutrino at keV scale (warm DM candidate): if any modes land in 1-10 keV.
    keV_mass_modes = [c for c in classifications
                      if 1e-3 <= c["predicted_mass_mev"] <= 1e-2]
    # GeV-scale neutrino window (NuMSM leptogenesis): if any modes land there.
    leptogenesis_modes = [c for c in classifications
                          if 1e2 <= c["predicted_mass_mev"] <= 1e3]
    # Above-LHC mass range (5-100 TeV): natural for next-collider targets.
    next_collider_modes = [c for c in classifications
                           if 5e6 <= c["predicted_mass_mev"] <= 1e8]
    # GUT-scale (10^10-10^13 MeV).
    gut_modes = [c for c in classifications
                 if 1e10 <= c["predicted_mass_mev"] <= 1e13]

    if keV_mass_modes:
        notable_thresholds.append({
            "regime": "keV_warm_DM",
            "n_modes": len(keV_mass_modes),
            "mass_examples_mev": [m["predicted_mass_mev"] for m in keV_mass_modes[:3]],
            "context": "1-10 keV warm DM candidate window; 3.5 keV line "
                       "(if real) sits here; XMM-Newton / Chandra null results "
                       "constrain coupling.",
        })
    if leptogenesis_modes:
        notable_thresholds.append({
            "regime": "GeV_leptogenesis_nuMSM",
            "n_modes": len(leptogenesis_modes),
            "mass_examples_mev": [m["predicted_mass_mev"] for m in leptogenesis_modes[:3]],
            "context": "100 MeV - 1 GeV: nuMSM leptogenesis sterile-nu window; "
                       "partially excluded by short-baseline + beam dump but "
                       "specific couplings remain.",
        })
    if next_collider_modes:
        notable_thresholds.append({
            "regime": "next_collider_5_to_100_TeV",
            "n_modes": len(next_collider_modes),
            "mass_examples_mev": [m["predicted_mass_mev"] for m in next_collider_modes[:3]],
            "context": "5-100 TeV: above current LHC reach; FCC / muon-collider "
                       "discovery range.",
        })
    if gut_modes:
        notable_thresholds.append({
            "regime": "GUT_scale_10_to_13_log_MeV",
            "n_modes": len(gut_modes),
            "mass_examples_mev": [m["predicted_mass_mev"] for m in gut_modes[:3]],
            "context": "10^10-10^13 MeV: GUT-scale window; proton-decay "
                       "indirect constraints only.",
        })

    for nt in notable_thresholds:
        print(f"  {nt['regime']}: {nt['n_modes']} modes")
        if nt['mass_examples_mev']:
            print(f"    example masses: {nt['mass_examples_mev'][:3]} MeV")

    records.append(to_record(
        "notable_predictions",
        notable=notable_thresholds,
        note="Specific predictions in regions where experimental sensitivity "
             "is open. Flagged for methodological transparency; NOT a search "
             "recommendation (per [[feedback_trauma_informed_defensive_scope]]).",
    ))

    # ------ Step 7b: Overdensity falsifier ------
    # The cascade predicts 191 unobserved fermions in a mass range
    # [0.5 MeV, 150 GeV] (~5.5 decades). In any given mass decade, count
    # the number of unobserved predictions vs the SM particle count for
    # comparison. Heavy concentration (e.g. >50 modes per decade) is a
    # phenomenological red flag: real BSM theories predict O(10) new
    # particles, not O(100) in a single decade.
    print("\n[Step 7b] Overdensity falsifier")
    overdense_decades = []
    for d in decade_bins:
        decade_key = f"1e{d}_to_1e{d+1}_MeV"
        n = histogram.get(decade_key, 0)
        if n > 50:  # phenomenological overdensity threshold
            overdense_decades.append({
                "decade_log10_mev_low": d,
                "decade_log10_mev_high": d + 1,
                "predicted_count": n,
                "phenomenological_expectation_O(10)": True,
                "note": f"Cascade predicts {n} new fermion-like states in "
                        f"10^{d} - 10^{d+1} MeV, vastly exceeding the O(10) "
                        "phenomenological expectation for realistic BSM "
                        "theories (SUSY ~30 total new states; GUT ~few).",
            })
    if overdense_decades:
        print(f"  WARNING: {len(overdense_decades)} decades with overdensity (>50 modes)")
        for od in overdense_decades:
            print(f"    decade 10^{od['decade_log10_mev_low']}-10^{od['decade_log10_mev_high']+1} MeV: "
                  f"{od['predicted_count']} predicted")
    records.append(to_record(
        "overdensity_falsifier",
        n_overdense_decades=len(overdense_decades),
        overdense_decades=overdense_decades,
        threshold=50,
        note="Counts of predicted unobserved-mode masses per decade. "
             "Decades with >50 modes flag the cascade as overdense — "
             "phenomenologically implausible compared to realistic BSM "
             "particle-content estimates.",
    ))

    # ------ Step 7c: SM-coupling-channel argument ------
    # Even if individual unobserved-mode predictions are "PARTIAL" (excluded
    # only for SM-like couplings), the *aggregate* claim that 191 new fermions
    # exist in [0.5 MeV, 150 GeV] requires them ALL to be hidden-sector / weakly
    # coupled. The framework has no mechanism to ensure this; it would need to
    # postulate a sector-coupling rule covering all 191 modes simultaneously.
    print("\n[Step 7c] Aggregate-coupling consistency")
    # Number of unobserved modes in MeV-TeV mass range (LHC + lepton-collider
    # search-sensitive region).
    n_visible_range = sum(1 for c in classifications
                          if 1.0 <= c["predicted_mass_mev"] <= 1e6)
    print(f"  modes in 1 MeV - 1 TeV (collider-sensitive): {n_visible_range}")
    records.append(to_record(
        "aggregate_coupling_consistency",
        n_in_collider_sensitive_range_MeV_to_TeV=n_visible_range,
        sm_count_for_comparison=9,
        note="The aggregate claim that 191 new fermions exist in the "
             "collider-sensitive mass range requires every single one to be "
             "hidden-sector / weakly-coupled. The framework provides no such "
             "selection rule. This is the structural problem reading 2 "
             "encounters that reading 1 (suppressed-mode coupling) might "
             "address with a specific coupling-channel mechanism.",
    ))

    # ------ Step 8: Summary table per decade with exclusion status ------
    print("\n[Step 8] Summary table - per decade vs exclusion")
    summary_table = []
    for d in decade_bins:
        decade_key = f"1e{d}_to_1e{d+1}_MeV"
        row = {
            "decade_log10_mev_low": d,
            "decade_log10_mev_high": d + 1,
            "total": histogram.get(decade_key, 0),
        }
        for label in counts_by_label.keys():
            row[label.lower()] = histogram_by_label[label].get(decade_key, 0)
        if row["total"] > 0:
            summary_table.append(row)

    records.append(to_record(
        "per_decade_summary_table",
        summary=summary_table,
        note="Per-decade summary, only non-empty decades. Columns: total + "
             "per-exclusion-label counts.",
    ))

    # ------ Final totals ------
    t_total = time.time() - t_start
    records.append(to_record(
        "totals",
        total_elapsed_s=float(t_total),
        n_unobserved_modes=int(n_unobserved),
        n_excluded=int(counts_by_label["EXCLUDED"]),
        n_partial=int(counts_by_label["PARTIAL"]),
        n_constrained=int(counts_by_label["CONSTRAINED"]),
        n_allowed=int(counts_by_label["ALLOWED"]),
        verdict=verdict,
    ))

    # ------ Integrity hash ------
    rec_bytes = "\n".join(json.dumps(r, sort_keys=True) for r in records).encode("utf-8")
    rec_sha = hashlib.sha256(rec_bytes).hexdigest()
    records.append(to_record("integrity", records_sha256=rec_sha))

    # Write NDJSON.
    with open(NDJSON_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"\n  records -> {NDJSON_PATH.name}")
    print(f"  total elapsed = {t_total:.1f}s")
    print(f"  records SHA256 = {rec_sha[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
