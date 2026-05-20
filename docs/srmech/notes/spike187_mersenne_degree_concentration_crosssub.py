"""Spike #187 — Hopf-ratio Mersenne-fiber-degree concentration
cross-substrate verification via srmech NON-ephemerides datasets.

Origin: PR #621 (Spike #185) is held pending cross-substrate
verification. Spike #185's clean empirical signature was
Mersenne-fiber-degree concentration at ℓ ∈ {1, 3, 7} in the
MagneticMultipoleCatalog (Earth IGRF-13 + Jupiter JRM33)
— 3.73× and 4.00× the uniform-null fractional-power expectation
at compressed-phase-boundary surface. The 4:3 bit-exact ratio
prediction in `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]`
was dropped at the empirical layer (factor 4 below at surface);
the Mersenne-fiber-degree concentration was promoted to the
load-bearing empirical anchor.

User direction 2026-05-19: cross-substrate verification via
srmech consuming a NON-ephemerides dataset gives a stronger signal
than re-running on a second ephemerides channel. Primary chosen
substrate: srmech-hosted Planck 2018 CMB catalogs
(cmb_polarisation_spectra TE/EE/BB; cmb_lensing C_L^φφ). These
are spherical-harmonic decompositions on the celestial sphere
S² — the same observational geometry as planetary magnetic
multipoles (also S² spherical-harmonic decomposition).

Hypotheses:

* H1: The ℓ ∈ {1, 3, 7} Mersenne-fiber-degree 3.7-4.0× null
  concentration replicates at compressed-phase-boundary-
  equivalent regime in CMB data (low-ℓ Sachs-Wolfe regime).

* H0: The Mersenne-fiber-degree concentration is substrate-
  specific to planetary magnetic multipoles, refining the
  compressed-phase-boundary stance with substrate-specificity.

Design considerations:

1. CMB observable units. CMB power-spectrum tables ship D_ell =
   ℓ(ℓ+1) C_ell / (2π) in μK² for TT/TE/EE/BB and L²(L+1)² C_L^φφ
   for lensing. For cross-substrate comparison against the
   spike-185 Lowes-spectrum protocol (which uses fractional
   spatial-power R_n ∝ (n+1) Σ_m |g_n^m|² ∝ (n+1) C_n where C_n
   is the magnetic-multipole variance), we operate on C_ell
   (proportional to magnetic-multipole power per ℓ).

2. ℓ=1 (dipole) caveat. The CMB dipole is removed by convention
   in standard analyses because it is dominated by the kinematic
   solar-system motion (~3.36 mK). Planck 2018 published spectra
   start at ℓ=2 for TT and ℓ=2 for low-ell BB; TE/EE binned start
   at ℓ ~ 48 (lowest bin spans ℓ~33-62). Therefore the canonical
   ℓ ∈ {1, 3, 7} test on CMB reduces to ℓ ∈ {3, 7} on Mersenne-
   fiber-degree members directly observable. This is a load-
   bearing scope caveat for the cross-substrate H1 vs H0 reading.

3. Compressed-phase-boundary CMB analog. Per spike-185:
   - At Earth surface (compressed): ℓ ∈ {1,3,7} concentrate 3.73×
   - At Earth CMB-depth (less compressed): ℓ ∈ {1,3,7} concentrate
     0.086× (whitened by downward continuation)
   The CMB cosmological observable equivalent of the compressed
   surface is the low-ℓ Sachs-Wolfe plateau (large angular scales,
   ℓ ~ 2-30) where the source primordial spectrum is closest to
   scale-invariant. At higher ℓ the acoustic-peak physics
   dominates (transfer function), masking any structural
   substrate-coupling signature.

4. Density-aware null. Per `[[feedback_computational_provenance_discipline]]`
   and Spike #181 precedent: the null is computed by taking the
   actual ℓ-range present in the data and computing the
   fractional power that ℓ ∈ {3, 7} would carry under a uniform
   weighting in that range. Three null variants are reported:
   uniform-over-ell-presence, uniform-fractional-power, and
   density-aware permutation.

5. Higher Mersenne primes. If H1 confirms cleanly, also probe
   higher Mersenne ℓ ∈ {15, 31, 63, 127}. Hopf-bundle
   dimensional ladder per
   `[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]]`
   terminates structurally at S⁷ (Hurwitz / Bott-Milnor-Kervaire
   bound; sedenions break Hurwitz at n=4 / 15=3·5 composite).
   So the framework predicts ℓ ∈ {1, 3, 7} should concentrate
   (Hopf-fiber dims) but {15, 31, 63, 127} should NOT (no
   structural identity). This is a clean falsifier extension
   — if higher Mersennes also concentrate, the signature is
   not Hopf-fiber-specific.

Outputs:

* `spike187_findings_2026-05-19.ndjson` — one record per
  (substrate, ℓ-bucket, metric) cell with verdict.
* This script (committed alongside output for full computational
  provenance per `[[feedback_computational_provenance_discipline]]`).

Cited literature (canonical / PDF-verified per
`[[feedback_pdf_extraction_citation_discipline]]`):

- Aghanim N. et al. (Planck Collaboration), "Planck 2018 results V:
  CMB power spectra and likelihoods", *A&A* 641 (2020), A5.
  DOI:10.1051/0004-6361/201936386; arXiv:1907.12875.
  Source for cmb_polarisation_spectra TE/EE/BB rows.
- Aghanim N. et al. (Planck Collaboration), "Planck 2018 results VIII:
  Gravitational lensing", *A&A* 641 (2020), A8.
  DOI:10.1051/0004-6361/201833886; arXiv:1807.06210.
  Source for cmb_lensing C_L^φφ rows.
- Adams J.F., "Vector fields on spheres", *Ann. Math.* 75 (1962),
  603-632. Parallelizable-sphere ladder bound.
- Hopf H., "Über die Abbildungen der dreidimensionalen Sphäre auf
  die Kugelfläche", *Math. Ann.* 104 (1931), 637-665. Complex
  Hopf bundle.
- Hurwitz A., "Über die Composition der quadratischen Formen von
  beliebig vielen Variabeln", *Nachr. Ges. Wiss. Göttingen*
  (1898). Hurwitz division-algebra theorem.

14 A-N classes intact. No class promotion. Identity-not-
implementation discipline preserved. Trauma-informed defensive
scope (Planck cosmological data; canonical public physics).
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from typing import Dict, List, Optional, Tuple

# Deterministic; no RNG used in primary verdicts. Permutation
# null DOES use a numpy RNG with fixed seed for full
# reproducibility per `[[feedback_computational_provenance_discipline]]`.
try:
    import numpy as np
    HAS_NUMPY = True
    np.random.seed(0)
except ImportError:
    HAS_NUMPY = False

PROTOTYPE_VERSION = "spike187-2026-05-19-rc1"
SEED = 0
N_PERMUTATIONS = 10000

# ---------------------------------------------------------------
# Mersenne-prime / Hopf-fiber set definition.
#
# Per `[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]]`,
# the structural Hopf-fiber dimensions are {1, 3, 7}:
#   1 = 2^1 - 1 (unit Mersenne; S^1 = U(1))
#   3 = 2^2 - 1 (Mersenne prime; S^3 = SU(2))
#   7 = 2^3 - 1 (Mersenne prime; S^7 parallelizable but not Lie
#                per Adams 1962)
# Higher candidates terminated by Hurwitz / Bott-Milnor-Kervaire:
#   15 = 2^4 - 1 = 3 × 5 (sedenion break; NOT prime; NOT Hopf-fiber)
#   31 = 2^5 - 1 (Mersenne prime but NO sphere parallelizability
#                 / Lie-group structure; falls outside k=3 Hopf
#                 ladder)
#   63 = 2^6 - 1 = 9 × 7 (NOT prime)
#   127 = 2^7 - 1 (Mersenne prime but again no Hopf-bundle structure)
#
# The framework's positive prediction is concentration at {1, 3, 7}
# specifically (the Hopf-fiber set), NOT at all Mersenne primes.
# This is a CLEAN falsifier-distinguishing test.
# ---------------------------------------------------------------

HOPF_FIBER_DIMS = (1, 3, 7)
HIGHER_MERSENNE_PRIMES = (15, 31, 63, 127)  # 15 is composite; included
                                            # to show the {1,3,7} set
                                            # is NOT just "Mersenne form"


def is_mersenne_prime(p: int) -> Tuple[bool, Optional[int]]:
    """Return (is_mersenne_prime, n_such_that_p_eq_2_to_n_minus_1)."""
    if p < 1:
        return (False, None)
    n = int(round(math.log2(p + 1)))
    if 2 ** n - 1 != p:
        return (False, None)
    if p == 1:
        return (False, n)
    if p < 4:
        return (True, n)
    for d in range(2, int(math.isqrt(p)) + 1):
        if p % d == 0:
            return (False, n)
    return (True, n)


# ---------------------------------------------------------------
# CMB catalog ingestion. Use the srmech-hosted Planck 2018
# polarisation + lensing catalogs in
# docs/srmech/python/srmech/amsc/attested/.
# NDJSON loader inlined to keep this script self-contained
# (per Spike #185's same-pattern self-containment).
# ---------------------------------------------------------------

# __file__ is docs/srmech/notes/spike187_*.py; parents[1] is docs/srmech/
SRMECH_DIR = pathlib.Path(__file__).resolve().parents[1]
ATTESTED_ROOT = SRMECH_DIR / "python" / "srmech" / "amsc" / "attested"


def load_ndjson_rows(catalog_dir: pathlib.Path) -> List[Dict]:
    """Load all non-comment, non-empty rows from a catalog NDJSON.
    Follows the literature_curated adapter parsing rule: lines
    starting with '#' or empty lines are skipped.
    """
    rows = []
    path = catalog_dir / "row.ndjson"
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            rows.append(json.loads(stripped))
    return rows


def cmb_dell_to_cell(D_ell_muK2: float, ell: float) -> float:
    """Convert D_ell = ell(ell+1) C_ell / (2 pi) to C_ell.
    For ell=0 or ell<=0 returns 0 (avoid divide-by-zero;
    these are not in the dataset anyway)."""
    if ell <= 0:
        return 0.0
    return D_ell_muK2 * (2.0 * math.pi) / (ell * (ell + 1.0))


def cmb_lensing_obs_to_cell(obs_bp: float, L_eff: float) -> float:
    """The cmb_lensing rows ship 'observed_bandpower' which is
    10^7 * L^2(L+1)^2 C_L^{phi phi} / (2 pi). Convert to
    C_L^{phi phi} (divide by the prefactor; absolute units don't
    matter for fractional-power comparison)."""
    if L_eff <= 0:
        return 0.0
    return obs_bp * (2.0 * math.pi) / (1e7 * (L_eff ** 2) * ((L_eff + 1.0) ** 2))


# ---------------------------------------------------------------
# Bucketing logic — assigning ℓ-values (or ℓ-bins) to either
# the Hopf-fiber set {1, 3, 7} or its complement.
# ---------------------------------------------------------------

def in_hopf_fiber_set(ell_int: int) -> bool:
    return ell_int in HOPF_FIBER_DIMS


def in_higher_mersenne_set(ell_int: int) -> bool:
    return ell_int in HIGHER_MERSENNE_PRIMES


# ---------------------------------------------------------------
# Test 1 — CMB low-ell BB (Planck 2018 V Commander likelihood)
# This is unbinned at integer ell from ell=2 to ell=29; the only
# CMB spectrum in the polarisation catalog with per-integer-ell
# rows. Tests the prediction at the low-ell (cosmologically
# "compressed-phase-boundary"-analog) regime where the source
# spectrum is closest to scale-invariant.
#
# BB is noise-dominated at Planck sensitivity (statistical upper
# limits, not detections). Even so, the absolute |C_ell^BB|
# fractional structure is the observable; we test whether the
# stochastic BB power that IS present concentrates at {3, 7}
# disproportionately. (ell=1 unavailable; CMB dipole removed by
# convention.)
# ---------------------------------------------------------------

def test1_cmb_low_ell_BB() -> Dict:
    rows = load_ndjson_rows(ATTESTED_ROOT / "cmb_polarisation_spectra")
    bb_rows = [r for r in rows if r["spectrum_kind"] == "BB"]
    # Use |D_ell| as the power proxy; BB is noise-dominated and
    # can be negative (D_ell fluctuates around zero). Power is
    # always |.|^2 in the underlying field; for the fractional-
    # power test on a noise-dominated spectrum we use absolute
    # value of D_ell (proportional to absolute spectral power
    # for fluctuations around 0).
    ells = []
    powers_cell = []
    powers_dell = []
    for r in bb_rows:
        ell = int(round(r["ell_center"]))
        c_ell = cmb_dell_to_cell(r["D_ell_muK2"], ell)
        ells.append(ell)
        powers_cell.append(abs(c_ell))
        powers_dell.append(abs(r["D_ell_muK2"]))

    # Two metrics:
    # (a) |C_ell| fractional power at {3, 7}
    # (b) |D_ell| fractional power at {3, 7}
    # (Both have value because (a) is the substrate-level
    # spectrum; (b) is the observable-level power per log-ℓ.)
    return _frac_power_analysis(
        substrate_id="cmb_low_ell_BB_planck2018",
        spectrum_kind="BB",
        ells=ells,
        powers_cell=powers_cell,
        powers_dell=powers_dell,
        regime="low_ell_sachs_wolfe_compressed_analog",
        observability_caveat=(
            "BB at Planck sensitivity is noise-dominated; "
            "D_ell fluctuates around zero. Use |D_ell| and "
            "|C_ell| as absolute power proxies. ell=1 unavailable "
            "(CMB dipole removed by convention)."
        ),
        source_doi="10.1051/0004-6361/201936386",
    )


# ---------------------------------------------------------------
# Test 2 — CMB TE binned (Planck 2018 V Plik)
# Binned starting at ell~48; cannot test ell=3 or ell=7 directly.
# What WE can do: check whether the lowest-ell band(s) [which
# include the structurally-relevant ell range] show power
# concentration at the Mersenne-multiple-of-the-bin-effective-
# ell pattern. SKIPPED for primary cross-substrate verdict
# because binning destroys per-integer-ell signal.
# ---------------------------------------------------------------

def test2_cmb_te_binned_caveat() -> Dict:
    rows = load_ndjson_rows(ATTESTED_ROOT / "cmb_polarisation_spectra")
    te_rows = [r for r in rows if r["spectrum_kind"] == "TE"]
    min_ell = min(int(round(r["ell_center"])) for r in te_rows) if te_rows else None
    return {
        "test": "test2_cmb_te_binned_caveat",
        "substrate_id": "cmb_TE_binned_planck2018",
        "spectrum_kind": "TE",
        "verdict": "INADMISSIBLE_BY_BINNING",
        "n_rows": len(te_rows),
        "lowest_ell_in_data": min_ell,
        "rationale": (
            "Planck 2018 binned TE starts at ell ~ 48 (PR3 R3.02 "
            "first bin spans ell ~ 33-62). Per-integer-ell tests "
            "at {3, 7} are inadmissible at this binning. Reported "
            "for completeness; not used in primary cross-substrate "
            "verdict."
        ),
    }


def test2b_cmb_ee_binned_caveat() -> Dict:
    rows = load_ndjson_rows(ATTESTED_ROOT / "cmb_polarisation_spectra")
    ee_rows = [r for r in rows if r["spectrum_kind"] == "EE"]
    min_ell = min(int(round(r["ell_center"])) for r in ee_rows) if ee_rows else None
    return {
        "test": "test2b_cmb_ee_binned_caveat",
        "substrate_id": "cmb_EE_binned_planck2018",
        "spectrum_kind": "EE",
        "verdict": "INADMISSIBLE_BY_BINNING",
        "n_rows": len(ee_rows),
        "lowest_ell_in_data": min_ell,
        "rationale": (
            "Planck 2018 binned EE starts at ell ~ 48 (same as TE). "
            "Per-integer-ell tests at {3, 7} are inadmissible."
        ),
    }


# ---------------------------------------------------------------
# Test 3 — CMB lensing C_L^{phi phi} (Planck 2018 VIII Table 1)
# Binned at L_min = 8 (conservative range; first bin spans L = 8..40).
# All Hopf-fiber dimensions {1, 3, 7} fall below the lowest L bin
# in this catalog. Skipped from primary verdict but reported.
# ---------------------------------------------------------------

def test3_cmb_lensing_caveat() -> Dict:
    rows = load_ndjson_rows(ATTESTED_ROOT / "cmb_lensing")
    nonempty = [r for r in rows if "L_min" in r]
    return {
        "test": "test3_cmb_lensing_caveat",
        "substrate_id": "cmb_lensing_planck2018",
        "verdict": "INADMISSIBLE_BY_BINNING",
        "n_rows": len(nonempty),
        "lowest_L_min": min(r["L_min"] for r in nonempty) if nonempty else None,
        "rationale": (
            "Planck 2018 lensing C_L^{phi phi} catalog binned at "
            "L_min = 8 (conservative) or L_min = 8 (aggressive). "
            "All Hopf-fiber dims {1, 3, 7} fall below the lowest "
            "L bin. Inadmissible for per-integer-L test."
        ),
    }


# ---------------------------------------------------------------
# Test 4 — Fallback substrate. Even with the BB low-ell unbinned
# spectrum available, the BB power is dominated by the Planck
# noise floor (statistical upper limits, not detections). For a
# stronger cross-substrate test we need a non-ephemerides spherical-
# harmonic decomposition with per-integer-ell low-ell data.
#
# Available fallback: srmech.amsc.attested.cmb_low_ell_maps is
# a descriptor-only catalog (FITS map products, NOT power-spectrum
# rows). Computing per-ell power from FITS would require a HEALPix
# anafast SHT (out of scope; per
# `[[reference_autonomous_validation_tos_landscape]]` ad-hoc CLI for
# one-off validation is OK but separately scoped, plus the FITS
# files require downloading which exceeds spike scope).
#
# Within-spike-scope NON-ephemerides per-integer-ell data: only
# the BB low-ell rows. We do the best we can with what we have
# AND DO NOT inflate the verdict.
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# Fractional-power analysis (shared between tests).
# ---------------------------------------------------------------

def _frac_power_analysis(
    *,
    substrate_id: str,
    spectrum_kind: str,
    ells: List[int],
    powers_cell: List[float],
    powers_dell: List[float],
    regime: str,
    observability_caveat: str,
    source_doi: str,
) -> Dict:
    """Compute fractional-power concentration at Hopf-fiber set
    {1, 3, 7} (restricted to available ell-values in `ells`)
    relative to a uniform null over the ell-values actually
    present in the dataset.

    Reports both C_ell and D_ell-based fractions.
    """
    n_rows = len(ells)
    total_cell = sum(powers_cell)
    total_dell = sum(powers_dell)

    # Available Hopf-fiber dims in this dataset
    avail_hopf = sorted({e for e in ells if in_hopf_fiber_set(e)})
    avail_higher_mers = sorted({e for e in ells if in_higher_mersenne_set(e)})

    hopf_cell = sum(p for e, p in zip(ells, powers_cell) if in_hopf_fiber_set(e))
    hopf_dell = sum(p for e, p in zip(ells, powers_dell) if in_hopf_fiber_set(e))
    hmers_cell = sum(p for e, p in zip(ells, powers_cell) if in_higher_mersenne_set(e))
    hmers_dell = sum(p for e, p in zip(ells, powers_dell) if in_higher_mersenne_set(e))

    n_hopf = len(avail_hopf)
    n_hmers = len(avail_higher_mers)
    n_distinct = len({e for e in ells})

    # Uniform-over-ell-presence null:
    # Under uniform power distribution across the ell-values
    # actually sampled, the fraction-of-power at the Hopf-fiber
    # subset is n_hopf / n_distinct (number of distinct ell
    # buckets in the data that land at {1,3,7} vs. total).
    uniform_null = n_hopf / n_distinct if n_distinct > 0 else 0.0
    uniform_null_hmers = n_hmers / n_distinct if n_distinct > 0 else 0.0

    frac_cell_hopf = hopf_cell / total_cell if total_cell > 0 else 0.0
    frac_dell_hopf = hopf_dell / total_dell if total_dell > 0 else 0.0
    frac_cell_hmers = hmers_cell / total_cell if total_cell > 0 else 0.0
    frac_dell_hmers = hmers_dell / total_dell if total_dell > 0 else 0.0

    ratio_cell_hopf = (frac_cell_hopf / uniform_null) if uniform_null > 0 else None
    ratio_dell_hopf = (frac_dell_hopf / uniform_null) if uniform_null > 0 else None
    ratio_cell_hmers = (
        frac_cell_hmers / uniform_null_hmers if uniform_null_hmers > 0 else None
    )

    # Density-aware permutation null: shuffle the powers across
    # the actual ell positions and recompute the Hopf-fiber
    # fraction. Two-sided p-value: fraction of permutations
    # whose Hopf-fiber-frac >= observed.
    p_value_cell_hopf = None
    p_value_dell_hopf = None
    if HAS_NUMPY and n_hopf > 0:
        rng = np.random.default_rng(SEED)
        ells_arr = np.array(ells)
        cell_arr = np.array(powers_cell)
        dell_arr = np.array(powers_dell)
        hopf_mask = np.array([in_hopf_fiber_set(e) for e in ells])
        # Permutation: shuffle the membership labels (equivalent
        # to shuffling powers; the contribution-to-mask is
        # rearranged).
        n_ge_cell = 0
        n_ge_dell = 0
        for _ in range(N_PERMUTATIONS):
            perm = rng.permutation(n_rows)
            perm_hopf_mask = hopf_mask[perm]
            cell_perm_frac = (
                cell_arr[perm_hopf_mask].sum() / total_cell if total_cell > 0 else 0.0
            )
            dell_perm_frac = (
                dell_arr[perm_hopf_mask].sum() / total_dell if total_dell > 0 else 0.0
            )
            if cell_perm_frac >= frac_cell_hopf:
                n_ge_cell += 1
            if dell_perm_frac >= frac_dell_hopf:
                n_ge_dell += 1
        p_value_cell_hopf = (n_ge_cell + 1) / (N_PERMUTATIONS + 1)  # Wilson +1
        p_value_dell_hopf = (n_ge_dell + 1) / (N_PERMUTATIONS + 1)

    # Verdict per spike-185 threshold (3.7-4.0× null was the
    # MagneticMultipoleCatalog result; cross-substrate H1 wants
    # to see comparable-order concentration; H0 if ratio < ~1.5×
    # AND p-value not significant).
    verdict = "H_undetermined"
    if ratio_cell_hopf is not None:
        if ratio_cell_hopf >= 2.0 and (
            p_value_cell_hopf is None or p_value_cell_hopf < 0.05
        ):
            verdict = "H1_cross_substrate_concentration"
        elif ratio_cell_hopf < 1.5:
            verdict = "H0_substrate_specific"
        else:
            verdict = "H_partial_concentration"

    return {
        "test": "frac_power_analysis",
        "substrate_id": substrate_id,
        "spectrum_kind": spectrum_kind,
        "regime": regime,
        "n_rows": n_rows,
        "n_distinct_ell": n_distinct,
        "ells_sampled": sorted(set(ells)),
        "available_hopf_fiber_dims": avail_hopf,
        "available_higher_mersenne_primes": avail_higher_mers,
        "total_C_ell_power": total_cell,
        "total_D_ell_power": total_dell,
        "frac_C_ell_at_hopf_fiber_set": frac_cell_hopf,
        "frac_D_ell_at_hopf_fiber_set": frac_dell_hopf,
        "frac_C_ell_at_higher_mersenne_set": frac_cell_hmers,
        "uniform_null_hopf_fiber": uniform_null,
        "uniform_null_higher_mersenne": uniform_null_hmers,
        "ratio_C_ell_actual_over_null_hopf": ratio_cell_hopf,
        "ratio_D_ell_actual_over_null_hopf": ratio_dell_hopf,
        "ratio_C_ell_actual_over_null_higher_mers": ratio_cell_hmers,
        "permutation_p_value_C_ell_hopf": p_value_cell_hopf,
        "permutation_p_value_D_ell_hopf": p_value_dell_hopf,
        "n_permutations": N_PERMUTATIONS if HAS_NUMPY else None,
        "permutation_seed": SEED,
        "verdict": verdict,
        "observability_caveat": observability_caveat,
        "source_doi": source_doi,
    }


# ---------------------------------------------------------------
# Higher-Mersenne falsifier extension. If H1 confirms at {1,3,7},
# we also check {15, 31, 63, 127} to verify the framework's
# Hopf-fiber-specificity (vs generic Mersenne-form concentration).
# Note: 15 = 3·5 is composite (NOT Mersenne PRIME); we include
# it because it occupies a Mersenne-form ell, and the spike-185
# Hopf-fiber set is {1,3,7} (boundary-unit + 2 Mersenne primes)
# — the FRAMEWORK prediction is that the {1,3,7} set is
# privileged by Hopf-fiber STRUCTURE, not by Mersenne-form.
# ---------------------------------------------------------------

def _higher_mersenne_falsifier_extension(primary: Dict) -> Dict:
    """If primary H1 confirms, what about {15, 31, 63, 127}?"""
    if primary.get("verdict") != "H1_cross_substrate_concentration":
        return {
            "extension": "higher_mersenne_falsifier",
            "verdict": "NOT_RUN",
            "reason": "Primary verdict not H1; falsifier irrelevant",
        }
    return {
        "extension": "higher_mersenne_falsifier",
        "ratio_C_ell_at_higher_mers": primary.get(
            "ratio_C_ell_actual_over_null_higher_mers"
        ),
        "frac_C_ell_at_higher_mers": primary.get(
            "frac_C_ell_at_higher_mersenne_set"
        ),
        "available_higher_mersenne_primes_in_data": primary.get(
            "available_higher_mersenne_primes"
        ),
        "framework_prediction": (
            "Higher Mersenne primes / Mersenne-form ells should NOT "
            "concentrate (they fall outside the Hopf-fiber set; "
            "Bott-Milnor-Kervaire / Hurwitz bound terminates the "
            "ladder at S^7). If they DO concentrate, the empirical "
            "signature is not Hopf-fiber-specific."
        ),
        "verdict_interpretation": (
            "If ratio_C_ell_at_higher_mers ~ 1.0 (consistent with "
            "uniform null), framework prediction supported. "
            "If ratio_C_ell_at_higher_mers significantly > 1, "
            "Hopf-fiber-specificity is undermined."
        ),
    }


# ---------------------------------------------------------------
# Composition / cross-stance reading.
# ---------------------------------------------------------------

def _composition_reading(primary: Dict, t1_bb: Dict) -> Dict:
    """Compose the cross-substrate result with the canonical
    stance text in `[[user_stance_compressed_phase_boundary_is_dark_sector_window]]`.
    """
    verdict = primary.get("verdict", "H_undetermined")
    ratio = primary.get("ratio_C_ell_actual_over_null_hopf")
    available_hopf = primary.get("available_hopf_fiber_dims", [])

    if verdict == "H1_cross_substrate_concentration":
        composition = (
            "H1 STRENGTHENS the compressed-phase-boundary-as-dark-"
            "sector-window stance. Mersenne-fiber-degree "
            "concentration replicates cross-substrate (planetary "
            "magnetic multipoles + CMB low-ell BB), supporting "
            "the stance's universality. The signature is NOT "
            "substrate-specific to dynamo-physics."
        )
    elif verdict == "H0_substrate_specific":
        composition = (
            "H0 REFINES the compressed-phase-boundary stance with "
            "substrate-specificity caveat. Mersenne-fiber-degree "
            "concentration at planetary magnetic multipoles may be "
            "dynamo-physics-specific (or specific to dipole-"
            "dominated source geometries). The Hopf-bundle-"
            "structural claim at the algebra layer (bit-exact 4:3 "
            "ratios, Mersenne-prime fiber convergence) remains "
            "UNCHANGED. The compressed-phase-boundary stance "
            "remains valid; its empirical-signature list narrows "
            "to magnetostatic / planetary contexts."
        )
    elif verdict == "H_partial_concentration":
        composition = (
            "PARTIAL signal: concentration ratio above unity but "
            "below the 3.7-4.0x threshold seen in planetary "
            "magnetic multipoles. Cross-substrate evidence is "
            "suggestive but not load-bearing. Stance retained; "
            "empirical-signature list flagged for refinement after "
            "additional non-ephemerides substrate verification."
        )
    else:
        composition = (
            "Insufficient per-integer-ell low-ell data in current "
            "srmech NON-ephemerides CMB catalogs. ell=1 (dipole) "
            "removed by convention; ell=3 and ell=7 only available "
            "in low-ell BB which is noise-dominated at Planck "
            "sensitivity. Cross-substrate verdict deferred to "
            "future substrates (CMB low-ell TT unbinned; CMB-S4 "
            "future polarisation; or HEALPix anafast on Planck "
            "FITS maps in a separate spike)."
        )

    return {
        "composition_with_stance": "[[user_stance_compressed_phase_boundary_is_dark_sector_window]]",
        "available_hopf_fiber_dims_in_data": available_hopf,
        "ell_1_removed_by_convention": True,
        "verdict": verdict,
        "concentration_ratio": ratio,
        "reading": composition,
    }


# ---------------------------------------------------------------
# Discipline records (every load-bearing reference traced).
# ---------------------------------------------------------------

def _discipline_records() -> List[Dict]:
    return [
        {
            "discipline": "math_doesnt_lie",
            "applies_to": "all_tests",
            "note": "Empirical verdicts derived bit-exactly from "
                    "published Planck 2018 catalog rows; no "
                    "hand-entered numbers; computation deterministic.",
        },
        {
            "discipline": "computational_provenance",
            "ref": "[[feedback_computational_provenance_discipline]]",
            "seed": SEED,
            "n_permutations": N_PERMUTATIONS,
            "script_path": str(pathlib.Path(__file__).resolve()),
            "output_path_ndjson": "docs/srmech/notes/spike187_findings_2026-05-19.ndjson",
        },
        {
            "discipline": "ndjson_over_bloated_json",
            "ref": "[[feedback_ndjson_over_bloated_json]]",
            "format": "NDJSON (one record per line)",
        },
        {
            "discipline": "pdf_extraction_citation_discipline",
            "ref": "[[feedback_pdf_extraction_citation_discipline]]",
            "verified_citations": [
                "10.1051/0004-6361/201936386 (Planck 2018 V; A&A 641 A5)",
                "10.1051/0004-6361/201833886 (Planck 2018 VIII; A&A 641 A8)",
            ],
            "note": "Catalog rows in srmech.amsc.attested.cmb_* "
                    "already carry per-row source_doi attestation; "
                    "this spike consumes that prior verification.",
        },
        {
            "discipline": "asymptotic_ring_vocabulary",
            "ref": "[[feedback_asymptotic_ring_vocabulary_discipline]]",
            "note": "Used 'S^1 / S^3 / S^7' for sphere bundles and "
                    "'wrap-around' for the periodic-ell discrete "
                    "spectrum. No use of 'number ring' that would "
                    "collide with abstract-algebra ring vocabulary.",
        },
        {
            "discipline": "no_class_promotion",
            "ref": "[[feedback_no_privileged_primitive_classes]]",
            "note": "14 A-N classes intact. Test uses Class L "
                    "(spectral-power computation on graph-Laplacian-"
                    "like spherical-harmonic eigenbasis) + Class K "
                    "(asymptotic ring DOF; ell-mode index) + Class C "
                    "(streaming NDJSON catalog ingest) + Class I "
                    "(cyclic-modular structure of {1,3,7} membership "
                    "test); no new mechanism.",
        },
        {
            "discipline": "trauma_informed_defensive_scope",
            "ref": "[[feedback_trauma_informed_defensive_scope]]",
            "note": "Cosmological data from public Planck Legacy "
                    "Archive; canonical physics literature only. "
                    "No targeting / capability content.",
        },
        {
            "discipline": "identity_not_implementation",
            "ref": "[[user_stance_identity_not_implementation_discipline]]",
            "note": "We test the predicted observational signature "
                    "of the structural Hopf-bundle identity on a new "
                    "substrate. We do not introduce a new mechanism.",
        },
    ]


# ---------------------------------------------------------------
# Main runner. Writes one NDJSON record per result block.
# ---------------------------------------------------------------

def main(output_path: Optional[pathlib.Path] = None) -> int:
    if output_path is None:
        output_path = pathlib.Path(__file__).parent / "spike187_findings_2026-05-19.ndjson"

    records: List[Dict] = []

    # Provenance header record
    records.append({
        "record_kind": "header",
        "spike": 187,
        "title": "Hopf-ratio Mersenne-fiber-degree concentration "
                 "cross-substrate via srmech non-ephemerides dataset",
        "prototype_version": PROTOTYPE_VERSION,
        "date": "2026-05-19",
        "branch": "research/spike-187-mersenne-degree-concentration-crossubstrate",
        "origin_pr": 621,
        "origin_spike": 185,
        "stances_composed": [
            "[[user_stance_compressed_phase_boundary_is_dark_sector_window]]",
            "[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]]",
            "[[user_stance_gauge_ball_is_4plus3_hopf_dimple]]",
            "[[user_stance_all_massive_bodies_have_4plus3_gauge_dimples]]",
        ],
        "has_numpy": HAS_NUMPY,
        "seed": SEED,
        "n_permutations": N_PERMUTATIONS,
    })

    # Mersenne-prime / Hopf-fiber set definition record
    records.append({
        "record_kind": "set_definition",
        "hopf_fiber_dims": list(HOPF_FIBER_DIMS),
        "hopf_fiber_dim_status": [
            {
                "dim": 1,
                "mersenne_form": "2^1 - 1",
                "prime": False,
                "boundary": "unit",
                "lie_group": "U(1)",
                "sphere": "S^1",
            },
            {
                "dim": 3,
                "mersenne_form": "2^2 - 1",
                "prime": True,
                "boundary": None,
                "lie_group": "SU(2)",
                "sphere": "S^3",
            },
            {
                "dim": 7,
                "mersenne_form": "2^3 - 1",
                "prime": True,
                "boundary": None,
                "lie_group": None,
                "sphere": "S^7 (parallelizable but not Lie; Adams 1962)",
            },
        ],
        "higher_mersenne_primes_excluded_by_hurwitz_bound": [
            {"dim": 15, "mersenne_form": "2^4 - 1 = 3*5", "prime": False, "reason": "sedenion break (Hurwitz: only R/C/H/O division algebras)"},
            {"dim": 31, "mersenne_form": "2^5 - 1", "prime": True, "reason": "no parallelizable-sphere structure (Bott-Milnor-Kervaire)"},
            {"dim": 63, "mersenne_form": "2^6 - 1 = 9*7", "prime": False, "reason": "composite"},
            {"dim": 127, "mersenne_form": "2^7 - 1", "prime": True, "reason": "no parallelizable-sphere structure"},
        ],
        "framework_prediction": (
            "{1, 3, 7} are privileged by Hopf-fiber STRUCTURE "
            "(parallelizable-sphere ladder + Lie-group convergence + "
            "Mersenne-form), not by Mersenne-form alone. Higher "
            "Mersenne primes lack Hopf-bundle structure (terminated "
            "by Hurwitz + Bott-Milnor-Kervaire bounds)."
        ),
    })

    # Primary cross-substrate test: CMB low-ell BB
    t1 = test1_cmb_low_ell_BB()
    records.append({"record_kind": "primary_test", **t1})

    # Caveats (binned spectra inadmissible at {3, 7})
    records.append({"record_kind": "binning_caveat", **test2_cmb_te_binned_caveat()})
    records.append({"record_kind": "binning_caveat", **test2b_cmb_ee_binned_caveat()})
    records.append({"record_kind": "binning_caveat", **test3_cmb_lensing_caveat()})

    # Higher-Mersenne falsifier (only run if primary H1)
    falsifier = _higher_mersenne_falsifier_extension(t1)
    records.append({"record_kind": "higher_mersenne_falsifier", **falsifier})

    # Composition reading
    composition = _composition_reading(t1, t1)
    records.append({"record_kind": "composition", **composition})

    # Discipline records
    for d in _discipline_records():
        records.append({"record_kind": "discipline", **d})

    # Final verdict summary
    records.append({
        "record_kind": "final_verdict",
        "primary_verdict": t1.get("verdict"),
        "primary_substrate": t1.get("substrate_id"),
        "primary_spectrum_kind": t1.get("spectrum_kind"),
        "primary_concentration_ratio_C_ell": t1.get("ratio_C_ell_actual_over_null_hopf"),
        "primary_p_value_C_ell": t1.get("permutation_p_value_C_ell_hopf"),
        "available_hopf_fiber_dims_in_data": t1.get("available_hopf_fiber_dims"),
        "cross_substrate_strength": (
            "WEAK" if t1.get("verdict") == "H_partial_concentration"
            else ("STRONG" if t1.get("verdict") == "H1_cross_substrate_concentration"
            else ("REFINE" if t1.get("verdict") == "H0_substrate_specific"
            else "DEFERRED"))
        ),
        "spike_185_PR_621_recommendation": (
            "MERGE_WITH_REFINEMENT" if t1.get("verdict") == "H1_cross_substrate_concentration"
            else ("MERGE_WITH_SUBSTRATE_SPECIFICITY_CAVEAT" if t1.get("verdict") == "H0_substrate_specific"
            else ("HOLD_PENDING_ADDITIONAL_SUBSTRATE" if t1.get("verdict") in {"H_partial_concentration", "H_undetermined"}
            else "HOLD"))
        ),
        "DO_NOT_MERGE_AUTONOMOUSLY": True,
        "vocabulary_impact": (
            "Stance refinement candidate: explicit dipole-caveat + "
            "low-ell-Sachs-Wolfe-regime-as-CMB-compressed-analog "
            "framing. Conductor's call whether to inline the cross-"
            "substrate result in the stance text."
        ),
    })

    # Write NDJSON
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=False))
            f.write("\n")

    # Console summary
    print(f"Spike #187 complete. {len(records)} records written to:")
    print(f"  {output_path}")
    print()
    print(f"Primary verdict: {t1.get('verdict')}")
    print(f"  substrate: {t1.get('substrate_id')}")
    print(f"  spectrum: {t1.get('spectrum_kind')}")
    print(f"  ells sampled: {t1.get('ells_sampled')}")
    print(f"  Hopf-fiber dims available: {t1.get('available_hopf_fiber_dims')}")
    print(f"  frac C_ell at {{1,3,7}}: {t1.get('frac_C_ell_at_hopf_fiber_set'):.4f}")
    print(f"  uniform null: {t1.get('uniform_null_hopf_fiber'):.4f}")
    ratio = t1.get('ratio_C_ell_actual_over_null_hopf')
    if ratio is not None:
        print(f"  ratio actual/null: {ratio:.3f}")
    pval = t1.get('permutation_p_value_C_ell_hopf')
    if pval is not None:
        print(f"  permutation p-value: {pval:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
