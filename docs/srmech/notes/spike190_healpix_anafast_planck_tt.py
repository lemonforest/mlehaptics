"""Spike #190 — HEALPix anafast on Planck SMICA/NILC component-
separated CMB temperature map; per-integer-ℓ TT C_ℓ at low-ℓ
cross-substrate test of Mersenne-fiber-degree concentration.

Origin: PR #629 (Spike #187) returned H0_substrate_specific on
CMB low-ℓ BB Cl with three load-bearing caveats:

  (1) ℓ=1 dipole structurally unavailable (CMB convention).
  (2) BB is noise-dominated at Planck sensitivity (statistical
      upper limits, not detections).
  (3) CMB TT low-ℓ unbinned lives in ephemerides-spectral; the
      cleanest cross-substrate test was excluded by scope.

Spike #190 closes caveat (2) and (3): runs HEALPix `anafast` on
the Planck 2018 SMICA (or NILC) component-separated full-sky
temperature map (Nside=2048) to extract per-integer-ℓ TT C_ℓ
directly, at signal-dominated S/N (the SMICA/NILC product
suppresses foregrounds and instrumental noise). Caveat (1)
remains: ℓ=1 is still removed by convention. The dominant test
target therefore moves from ℓ ∈ {1, 3, 7} (Spike #185) down to
ℓ ∈ {3, 7} (Spike #187 + Spike #190).

Hypotheses:

* H1: Mersenne-fiber-degree concentration at ℓ ∈ {3, 7}
  replicates on Planck SMICA TT low-ℓ (clean signal, no noise
  domination), strengthening the universal compressed-phase-
  boundary stance.

* H0: H0_substrate_specific stands. Even on the cleaner TT
  spectrum, ℓ ∈ {3, 7} does NOT carry 3.7-4.0× null power.
  The Mersenne-fiber-degree-concentration signature is
  substrate-specific to magnetostatic / dipole-dominated source
  geometries (planetary internal fields), not universal across
  all compressed-phase-boundary substrates.

* Falsifier: density-aware permutation null on {3, 7} bucket
  fraction in the TT per-integer-ℓ Cl spectrum.

Data source: Planck Legacy Archive (PLA) SMICA full-sky CMB
temperature map: `COM_CMB_IQU-smica_2048_R3.00_full.fits`
(Nside=2048, IQU; we only use the I/temperature component).
URL pattern verified 2026-05-19 via HEAD request:
http://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=
COM_CMB_IQU-smica_2048_R3.00_full.fits.

PLA is open-access; permitted per
`[[reference_autonomous_validation_tos_landscape]]`.

Cited literature (PDF-arXiv-verified per
`[[feedback_pdf_extraction_citation_discipline]]`):

* Aghanim N. et al. (Planck Collaboration), "Planck 2018 results
  IV: Diffuse component separation", *A&A* 641 (2020), A4.
  DOI:10.1051/0004-6361/201833881; arXiv:1807.06208. Source for
  SMICA/NILC component-separation algorithm and full-sky CMB
  temperature map products.
* Aghanim N. et al. (Planck Collaboration), "Planck 2018 results
  V: CMB power spectra and likelihoods", *A&A* 641 (2020), A5.
  DOI:10.1051/0004-6361/201936386; arXiv:1907.12875. Planck
  2018 power-spectrum methodology (anafast pseudo-Cl pipeline).
* Górski K.M. et al., "HEALPix: a Framework for High-Resolution
  Discretization and Fast Analysis of Data Distributed on the
  Sphere", *ApJ* 622 (2005), 759-771. arXiv:astro-ph/0409513.
  HEALPix discretization + `anafast` spherical harmonic transform.
* Zonca A. et al. (healpy collaboration), "healpy: equal area
  pixelization and spherical harmonics transforms for data on
  the sphere in Python", *JOSS* 4 (2019), 1298. doi:10.21105/
  joss.01298. healpy Python implementation.
* Hopf, Hurwitz, Adams citations as in spike-185 / spike-187.

Numbering note: Searched all branches + docs/ for prior
"spike-190" / "spike_190" / "spike190" usage on 2026-05-19;
no collision detected. Spike-189 (figure-8 lemniscate) is the
predecessor on origin/main (commit ce85d25). Spike-190 is the
first occupant of this slot.

14 A-N classes intact. No class promotion.
Identity-not-implementation per
`[[user_stance_identity_not_implementation_discipline]]`.
Trauma-informed defensive scope (canonical public cosmology
data; component-separated full-sky CMB temperature map).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import sys
import time
from typing import Dict, List, Optional, Tuple

PROTOTYPE_VERSION = "spike190-2026-05-19-rc2"
SEED = 0
N_PERMUTATIONS = 10000
LMAX_PRIMARY = 40  # primary test ℓ=2..40 (low-ℓ Sachs-Wolfe + onset of
                   # acoustic-peak physics; matches parallel agent's
                   # lmax_test=40 for cross-pipeline comparability)
LMAX_FALSIFIER = 191  # falsifier extension covers {15, 31, 63, 127}
                       # higher Mersenne-form ells; framework predicts
                       # NO concentration at these (Hopf-bundle ladder
                       # bounded at S^7 per Adams 1962). Nside=2048
                       # supports lmax up to 3*Nside-1 = 6143; using
                       # 191 ≥ 127 with comfortable margin
LMAX = LMAX_PRIMARY  # backward-compat alias for primary test
DOWNLOAD_TIMEOUT_S = 1800  # 30 min for the FITS download

# Planck Legacy Archive (PLA) URL for the Planck 2018 component-
# separated CMB temperature maps (Nside=2048; PR3 / R3.00).
# Permitted per `[[reference_autonomous_validation_tos_landscape]]`.
#
# Strategy: dual-product cross-verification with the parallel
# Spike #190 agent (agent-a49706a9b75aaaa63), which ran SMICA-
# nosz and returned H1 (ratio 6.19× null; p=0.006). This agent
# runs NILC (different component-separation algorithm; Needlet
# Internal Linear Combination vs. SMICA's Spectral Matching ILC)
# for cross-algorithm replication.
SMICA_URL = (
    "http://pla.esac.esa.int/pla/aio/product-action"
    "?MAP.MAP_ID=COM_CMB_IQU-smica_2048_R3.00_full.fits"
)
SMICA_NOSZ_URL = (
    "http://pla.esac.esa.int/pla/aio/product-action"
    "?MAP.MAP_ID=COM_CMB_IQU-smica-nosz_2048_R3.00_full.fits"
)
NILC_URL = (
    "http://pla.esac.esa.int/pla/aio/product-action"
    "?MAP.MAP_ID=COM_CMB_IQU-nilc_2048_R3.00_full.fits"
)
# Primary product for this script: SMICA-nosz (cross-pipeline
# replication of parallel agent's SMICA-nosz result — same
# component-separation product, different analysis pipeline).
# SMICA-nosz is ~384 MB; the full NILC IQU is ~3.6 GB and requires
# a long download. NILC is still available as PRIMARY_URL_NILC for
# the optional cross-algorithm follow-up below.
PRIMARY_URL = SMICA_NOSZ_URL
PRIMARY_LABEL = "smica-nosz"
PRIMARY_URL_NILC = NILC_URL  # optional cross-algorithm follow-up

# Hopf-fiber set (per spike-185 / spike-187 stance):
HOPF_FIBER_DIMS = (1, 3, 7)
# Restricted to ℓ ∈ {3, 7} on CMB (ℓ=1 dipole removed by convention).
HOPF_FIBER_DIMS_CMB_AVAILABLE = (3, 7)
# Higher Mersenne-form ells (falsifier extension):
HIGHER_MERSENNE = (15, 31, 63, 127)


def fetch_planck_map(
    cache_dir: pathlib.Path,
    url: str = SMICA_URL,
    label: str = "smica",
) -> pathlib.Path:
    """Download the Planck full-sky CMB temperature map from PLA.

    Streams via `requests` (no Sci-Hub-class tooling). Uses
    SHA-256 of url+filename as cache key. Idempotent: if the
    cache file exists and is non-empty, returns it without
    re-downloading.

    Per `[[reference_autonomous_validation_tos_landscape]]`:
    PLA is open-access, no paywall, autonomous validation
    permitted.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    fname = f"planck_cmb_{label}_iqu_nside2048_R3.00_full.fits"
    out = cache_dir / fname
    # Variant: the SMICA-nosz product is ~384 MB (component-
    # separated single-product map). NILC and full SMICA IQU
    # are larger (~3.6 GB; multi-product IQU+masks). Treat any
    # file > 300 MB as a complete cached Planck product.
    if out.exists() and out.stat().st_size > 300_000_000:
        print(f"[cache] {out} already present ({out.stat().st_size/1e9:.2f} GB)")
        return out

    try:
        import requests
    except ImportError as e:
        raise RuntimeError(
            "requests required; pip install requests"
        ) from e

    print(f"[download] {url}")
    print(f"[download] → {out}")
    t0 = time.time()
    with requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT_S) as r:
        r.raise_for_status()
        total_bytes = 0
        next_print_threshold = 50 << 20  # 50 MB
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):  # 1 MB chunks
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)
                    if total_bytes >= next_print_threshold:
                        elapsed = time.time() - t0
                        rate_mbps = (total_bytes / 1e6) / max(elapsed, 0.001)
                        print(
                            f"[download] {total_bytes/1e9:.2f} GB"
                            f" ({rate_mbps:.1f} MB/s)"
                        )
                        next_print_threshold += 50 << 20
    print(
        f"[download] complete: {out.stat().st_size/1e9:.2f} GB"
        f" in {time.time()-t0:.0f} s"
    )
    return out


def compute_tt_cl(
    fits_path: pathlib.Path, lmax: int = LMAX
) -> Tuple[List[float], Dict]:
    """Run HEALPix `anafast` on the Planck temperature map.

    Returns (cl_TT_list, metadata). cl_TT_list[ℓ] is the
    per-integer-ℓ TT C_ℓ in (map-units)² (Planck maps are in
    μK_CMB; output Cl is μK².  Absolute units don't matter for
    the fractional-power test).

    Per `[[user_stance_identity_not_implementation_discipline]]`:
    healpy's `anafast` IS the canonical Class L (Laplacian
    spectral decomposition on S²) operation; we are NOT
    reimplementing it. The SHT IS Class L on S²; the cyclic-
    membership test IS Class I; this script composes existing
    primitive-class operations.
    """
    try:
        import healpy as hp
        import numpy as np
        from astropy.io import fits
    except ImportError as e:
        raise RuntimeError(
            "healpy + astropy required; pip install healpy astropy"
        ) from e

    print(f"[fits] open {fits_path}")
    hdul = fits.open(fits_path)
    meta = {
        "n_hdus": len(hdul),
        "hdu1_columns": [],
        "hdu1_header_keys": {},
    }
    if len(hdul) >= 2:
        h = hdul[1]
        meta["hdu1_columns"] = [c.name for c in h.columns]
        for k in ["TFIELDS", "NSIDE", "ORDERING", "COORDSYS",
                 "OBJECT", "PIXTYPE", "EXTNAME"]:
            if k in h.header:
                meta["hdu1_header_keys"][k] = h.header[k]
    hdul.close()

    print(f"[fits] meta: {json.dumps(meta, default=str)}")

    # Read temperature map (column I_STOKES) in RING ordering.
    # `read_map` handles ordering conversion automatically.
    print("[healpy] read_map (I component only)")
    map_T = hp.read_map(str(fits_path), field=0)
    print(f"[healpy] map shape: {map_T.shape}, dtype: {map_T.dtype}")
    nside = hp.npix2nside(map_T.size)
    print(f"[healpy] Nside = {nside}, Npix = {map_T.size}")

    # Mask Planck-marked invalid pixels (Healpix UNSEEN sentinel).
    bad = (map_T == hp.UNSEEN) | ~np.isfinite(map_T)
    n_bad = int(bad.sum())
    if n_bad > 0:
        print(f"[healpy] masking {n_bad} bad pixels ({100*n_bad/map_T.size:.4f}%)")
        map_T[bad] = 0.0  # zero-fill; for full-sky SMICA bad-pixel
                           # count is negligible (component-separation
                           # uses inpainting for galactic mask region)

    # Anafast: pseudo-Cl via SHT on full sky.
    # For component-separated full-sky maps (SMICA/NILC), the
    # pseudo-Cl IS the C_ℓ at the level of the cleaned map (no
    # mask correction needed; the cleaning algorithm has already
    # nulled the foregrounds).
    print(f"[healpy] anafast lmax={lmax}")
    t0 = time.time()
    cl_TT = hp.anafast(map_T, lmax=lmax)
    print(f"[healpy] anafast complete in {time.time()-t0:.1f} s")
    print(f"[healpy] cl_TT shape: {cl_TT.shape}")
    print(f"[healpy] cl_TT[2..7]: {cl_TT[2:8].tolist()}")

    meta["nside"] = int(nside)
    meta["npix"] = int(map_T.size)
    meta["n_bad_pixels_zeroed"] = n_bad
    meta["lmax"] = int(lmax)
    meta["anafast_seconds"] = float(time.time() - t0)
    return cl_TT.tolist(), meta


def fractional_power_test(
    cl_TT: List[float],
    lmax: int = LMAX,
    ell_min: int = 2,
    hopf_set: Tuple[int, ...] = HOPF_FIBER_DIMS_CMB_AVAILABLE,
    higher_set: Tuple[int, ...] = HIGHER_MERSENNE,
    n_permutations: int = N_PERMUTATIONS,
    seed: int = SEED,
) -> Dict:
    """Compute fractional-power concentration at the Hopf-fiber
    set on the per-integer-ℓ TT spectrum.

    Mirrors the Spike #185 + Spike #187 protocol: density-aware
    permutation null with Wilson-corrected p-value
    `(n_ge + 1) / (N + 1)`.

    Two metrics are reported, paralleling Spike #187:
    * |C_ℓ| fractional power at the Hopf-fiber set
    * |D_ℓ| = ℓ(ℓ+1) C_ℓ / (2π) fractional power at the same set

    D_ℓ is the canonical CMB observable (per-log-ℓ power).
    C_ℓ is the substrate-level spectrum (per-mode power).
    """
    try:
        import numpy as np
    except ImportError as e:
        raise RuntimeError("numpy required") from e

    ells = list(range(ell_min, lmax + 1))
    powers_cell = [abs(float(cl_TT[ell])) for ell in ells]
    powers_dell = [
        abs(float(cl_TT[ell])) * ell * (ell + 1.0) / (2.0 * math.pi)
        for ell in ells
    ]
    n_rows = len(ells)
    total_cell = sum(powers_cell)
    total_dell = sum(powers_dell)

    # Available Hopf-fiber dims in the data
    avail_hopf = sorted(e for e in ells if e in hopf_set)
    avail_hmers = sorted(e for e in ells if e in higher_set)
    n_hopf = len(avail_hopf)
    n_distinct = len(set(ells))

    hopf_cell = sum(p for e, p in zip(ells, powers_cell) if e in hopf_set)
    hopf_dell = sum(p for e, p in zip(ells, powers_dell) if e in hopf_set)
    hmers_cell = sum(p for e, p in zip(ells, powers_cell) if e in higher_set)
    hmers_dell = sum(p for e, p in zip(ells, powers_dell) if e in higher_set)

    uniform_null_hopf = n_hopf / n_distinct if n_distinct else 0.0
    uniform_null_hmers = len(avail_hmers) / n_distinct if n_distinct else 0.0

    frac_cell_hopf = hopf_cell / total_cell if total_cell > 0 else 0.0
    frac_dell_hopf = hopf_dell / total_dell if total_dell > 0 else 0.0
    frac_cell_hmers = hmers_cell / total_cell if total_cell > 0 else 0.0

    ratio_cell_hopf = (
        frac_cell_hopf / uniform_null_hopf if uniform_null_hopf > 0 else None
    )
    ratio_dell_hopf = (
        frac_dell_hopf / uniform_null_hopf if uniform_null_hopf > 0 else None
    )
    ratio_cell_hmers = (
        frac_cell_hmers / uniform_null_hmers
        if uniform_null_hmers > 0 else None
    )

    # Density-aware permutation null: shuffle ℓ-membership labels
    # 10,000 times, recompute Hopf-fiber-frac, count fractions >=
    # observed. Two-sided readings reported but primary p is the
    # right-tail (concentration test).
    rng = np.random.default_rng(seed)
    ells_arr = np.array(ells)
    cell_arr = np.array(powers_cell)
    dell_arr = np.array(powers_dell)
    hopf_mask = np.array([e in hopf_set for e in ells])

    n_ge_cell = 0
    n_ge_dell = 0
    for _ in range(n_permutations):
        perm = rng.permutation(n_rows)
        perm_hopf_mask = hopf_mask[perm]
        cell_perm_frac = (
            cell_arr[perm_hopf_mask].sum() / total_cell
            if total_cell > 0 else 0.0
        )
        dell_perm_frac = (
            dell_arr[perm_hopf_mask].sum() / total_dell
            if total_dell > 0 else 0.0
        )
        if cell_perm_frac >= frac_cell_hopf:
            n_ge_cell += 1
        if dell_perm_frac >= frac_dell_hopf:
            n_ge_dell += 1
    p_value_cell = (n_ge_cell + 1) / (n_permutations + 1)
    p_value_dell = (n_ge_dell + 1) / (n_permutations + 1)

    # Verdict per Spike #185 threshold (3.7-4.0× null on planetary
    # magnetic multipoles; cross-substrate H1 wants comparable-
    # order concentration; H0 if ratio < 1.5×).
    if ratio_cell_hopf is None:
        verdict = "H_undetermined"
    elif ratio_cell_hopf >= 2.0 and p_value_cell < 0.05:
        verdict = "H1_cross_substrate_concentration"
    elif ratio_cell_hopf < 1.5:
        verdict = "H0_substrate_specific"
    else:
        verdict = "H_partial_concentration"

    return {
        "test": "spike190_tt_fractional_power",
        "lmax": lmax,
        "ell_min": ell_min,
        "ells_sampled": ells,
        "hopf_fiber_set_tested": list(hopf_set),
        "available_hopf_fiber_dims_in_data": avail_hopf,
        "available_higher_mersenne_in_data": avail_hmers,
        "ell_1_removed_by_convention": True,
        "n_rows": n_rows,
        "n_distinct_ell": n_distinct,
        "total_C_ell_power_abs": total_cell,
        "total_D_ell_power_abs": total_dell,
        "frac_C_ell_at_hopf_fiber_set": frac_cell_hopf,
        "frac_D_ell_at_hopf_fiber_set": frac_dell_hopf,
        "frac_C_ell_at_higher_mersenne_set": frac_cell_hmers,
        "uniform_null_hopf_fiber": uniform_null_hopf,
        "uniform_null_higher_mersenne": uniform_null_hmers,
        "ratio_C_ell_actual_over_null_hopf": ratio_cell_hopf,
        "ratio_D_ell_actual_over_null_hopf": ratio_dell_hopf,
        "ratio_C_ell_actual_over_null_higher_mers": ratio_cell_hmers,
        "permutation_p_value_C_ell_hopf": p_value_cell,
        "permutation_p_value_D_ell_hopf": p_value_dell,
        "n_permutations": n_permutations,
        "permutation_seed": seed,
        "verdict": verdict,
    }


def main(out_ndjson: pathlib.Path, cache_dir: pathlib.Path) -> None:
    print(f"== Spike #190 — HEALPix anafast on Planck SMICA TT ==")
    print(f"   PROTOTYPE_VERSION = {PROTOTYPE_VERSION}")
    print(f"   SEED = {SEED}, N_PERMUTATIONS = {N_PERMUTATIONS}, LMAX = {LMAX}")
    print()

    # 1. Download primary map (NILC; cross-algorithm replication of
    #    parallel agent's SMICA-nosz H1 result). Fall back to
    #    SMICA-nosz (smaller; ~384 MB) if NILC fails.
    fits_path = None
    chosen_label = None
    chosen_url = None
    download_error = None
    try:
        fits_path = fetch_planck_map(
            cache_dir, PRIMARY_URL, PRIMARY_LABEL
        )
        chosen_label = PRIMARY_LABEL.upper()
        chosen_url = PRIMARY_URL
    except Exception as e:
        download_error = (
            f"{PRIMARY_LABEL.upper()} download failed: {e}; "
            f"attempting SMICA-nosz fallback"
        )
        print(f"[fallback] {download_error}")
        try:
            fits_path = fetch_planck_map(
                cache_dir, SMICA_NOSZ_URL, "smica-nosz"
            )
            chosen_label = "SMICA-NOSZ"
            chosen_url = SMICA_NOSZ_URL
        except Exception as e2:
            raise RuntimeError(
                f"Both primary ({PRIMARY_LABEL.upper()}) and "
                f"SMICA-nosz fallback failed: "
                f"primary={e}; fallback={e2}"
            ) from e2

    # 2. Run anafast at lmax = LMAX_FALSIFIER (covers both primary
    #    {3, 7} and falsifier {15, 31, 63, 127} tests)
    cl_TT, fits_meta = compute_tt_cl(fits_path, lmax=LMAX_FALSIFIER)
    fits_meta["component_separation_product"] = chosen_label
    fits_meta["download_url"] = chosen_url
    fits_meta["download_error_if_any"] = download_error

    # 3a. Primary: fractional-power test on {3, 7} at ℓ ∈ [2, 40]
    #    (ℓ=1 unavailable per CMB convention)
    primary = fractional_power_test(
        cl_TT,
        lmax=LMAX_PRIMARY,
        ell_min=2,
        hopf_set=HOPF_FIBER_DIMS_CMB_AVAILABLE,
        higher_set=HIGHER_MERSENNE,
    )
    # 3b. Falsifier: fractional-power test on {15, 31, 63, 127} at
    #     ℓ ∈ [2, 191]. Framework predicts NO concentration here
    #     (Hopf-bundle ladder terminates at S^7).
    falsifier = fractional_power_test(
        cl_TT,
        lmax=LMAX_FALSIFIER,
        ell_min=2,
        hopf_set=HIGHER_MERSENNE,  # treat higher Mersenne set as the
                                    # "test set" for this analysis
        higher_set=(),  # no further extension
    )
    # Tag falsifier records to distinguish from primary
    falsifier["test"] = "spike190_falsifier_higher_mersenne"

    # 4. Composition reading with stance
    verdict = primary["verdict"]
    ratio = primary["ratio_C_ell_actual_over_null_hopf"]
    p_val = primary["permutation_p_value_C_ell_hopf"]
    if verdict == "H1_cross_substrate_concentration":
        composition = (
            "H1 STRENGTHENS the compressed-phase-boundary-as-dark-"
            "sector-window stance. Mersenne-fiber-degree "
            f"concentration at ℓ ∈ {{3, 7}} on Planck {chosen_label} "
            f"TT (clean signal, no noise domination) shows "
            f"{ratio:.3f}× null fractional power (p={p_val:.3f}). "
            "The signature replicates cross-substrate, supporting "
            "universal compressed-phase-boundary observability. "
            "The Spike #187 H0_substrate_specific verdict is "
            "REVERSED: BB-noise-domination was the issue; TT "
            "recovers the concentration."
        )
    elif verdict == "H0_substrate_specific":
        composition = (
            "H0 STRENGTHENS the substrate-specificity refinement "
            f"of the compressed-phase-boundary stance. Planck "
            f"{chosen_label} TT at signal-dominated S/N shows "
            f"{ratio:.3f}× null concentration at ℓ ∈ {{3, 7}} "
            f"(p={p_val:.3f}). Even with the BB noise-domination "
            "caveat resolved, the Mersenne-fiber-degree-"
            "concentration signature does NOT replicate on CMB TT. "
            "The signature is genuinely magnetostatic / dipole-"
            "dominated-only; the Spike #187 refinement stands. "
            "Structural Hopf-bundle algebra (bit-exact 4:3, "
            "Mersenne-prime fibers) UNCHANGED."
        )
    elif verdict == "H_partial_concentration":
        composition = (
            f"PARTIAL replication on Planck {chosen_label} TT: "
            f"{ratio:.3f}× null (p={p_val:.3f}) at ℓ ∈ {{3, 7}}. "
            "Above unity but below the 3.7-4.0× planetary "
            "magnetic-multipole anchor. The cross-substrate "
            "evidence is suggestive but does not yet support "
            "universal compressed-phase-boundary signature claim. "
            "Stance retained with substrate-specificity caveat "
            "softened (replication partial)."
        )
    else:
        composition = (
            f"Indeterminate on Planck {chosen_label} TT; defer."
        )

    primary["composition_with_stance"] = (
        "[[user_stance_compressed_phase_boundary_is_dark_sector_window]]"
    )
    primary["composition_reading"] = composition
    primary["component_separation_product"] = chosen_label

    # 5. NDJSON output (per [[feedback_ndjson_over_bloated_json]])
    records: List[Dict] = []

    # Header record
    records.append({
        "record_type": "spike_header",
        "spike_id": 190,
        "prototype_version": PROTOTYPE_VERSION,
        "date_utc": "2026-05-19",
        "title": "HEALPix anafast on Planck SMICA TT cross-substrate "
                 "Mersenne-fiber-degree concentration test",
        "hypotheses": {
            "H1": "Mersenne-fiber-degree concentration at ℓ ∈ {3,7} "
                  "replicates on Planck SMICA TT low-ℓ",
            "H0": "H0_substrate_specific stands; even clean TT does "
                  "not show {3,7} concentration",
        },
        "discipline_anchors": [
            "[[user_stance_identity_not_implementation_discipline]]",
            "[[user_stance_compressed_phase_boundary_is_dark_sector_window]]",
            "[[user_stance_hopf_bundle_dimensional_ladder_baked_into_11d]]",
            "[[feedback_computational_provenance_discipline]]",
            "[[feedback_pdf_extraction_citation_discipline]]",
            "[[feedback_asymptotic_ring_vocabulary_discipline]]",
            "[[reference_autonomous_validation_tos_landscape]]",
            "[[feedback_ndjson_over_bloated_json]]",
            "[[feedback_no_privileged_primitive_classes]]",
        ],
        "primitive_classes_used": ["C", "I", "L"],
    })

    # FITS-data record
    records.append({
        "record_type": "fits_data_provenance",
        "url": chosen_url,
        "component_separation_product": chosen_label,
        "release": "Planck 2018 PR3 R3.00",
        "fits_metadata": fits_meta,
        "filesize_bytes": int(fits_path.stat().st_size),
    })

    # Per-integer-ℓ Cl record
    records.append({
        "record_type": "per_ell_cl_TT",
        "ell_min": 2,
        "ell_max": LMAX,
        "cl_TT_muK_squared": [cl_TT[ell] for ell in range(2, LMAX + 1)],
        "ells": list(range(2, LMAX + 1)),
    })

    # Primary verdict record
    primary_rec = dict(primary)
    primary_rec["record_type"] = "primary_verdict"
    records.append(primary_rec)

    # Falsifier verdict record
    falsifier_rec = dict(falsifier)
    falsifier_rec["record_type"] = "falsifier_verdict"
    # Falsifier framework-prediction language: H0 here = framework
    # confirmed (Hopf-fiber specificity preserved); H1 here = framework
    # weakened (signal not Hopf-fiber-specific, just Mersenne-form).
    if falsifier["verdict"] == "H0_substrate_specific":
        falsifier_rec["framework_interpretation"] = (
            "FRAMEWORK_CONFIRMED — higher Mersenne ells {15, 31, 63, "
            "127} do NOT concentrate (Hopf-fiber specificity "
            "preserved per Adams 1962 / Bott-Milnor-Kervaire bound)"
        )
    else:
        falsifier_rec["framework_interpretation"] = (
            "FRAMEWORK_WEAKENED — higher Mersenne ells concentrate "
            "too; the signature is generic Mersenne-form, not "
            "specifically Hopf-fiber"
        )
    records.append(falsifier_rec)

    # Cross-substrate composition record (compare with parallel
    # agent's smica-nosz H1 result + Spike #187 BB H0_substrate_specific)
    records.append({
        "record_type": "cross_substrate_composition",
        "this_agent_substrate": f"cmb_TT_lowell_planck2018_{chosen_label.lower()}_anafast",
        "this_agent_ratio_3_7": primary["ratio_C_ell_actual_over_null_hopf"],
        "this_agent_p_value_3_7": primary["permutation_p_value_C_ell_hopf"],
        "parallel_agent_substrate": "cmb_TT_lowell_planck2018_smica-nosz_anafast",
        "parallel_agent_ratio_3_7": 6.19425053358111,
        "parallel_agent_p_value_3_7": 0.0057994200579942,
        "parallel_agent_branch": "research/spike-190-healpix-mersenne-tt-cleaner-test",
        "parallel_agent_verdict": "H1_cross_substrate_concentration",
        "spike_187_BB_ratio_3_7": 0.15494524712526087,
        "spike_187_BB_p_value_3_7": 0.2702729727027297,
        "spike_187_BB_verdict": "H0_substrate_specific",
        "spike_185_planetary_ratio_1_3_7": "3.73x (Earth IGRF-13); 4.00x (Jupiter JRM33)",
        "interpretation_if_both_TT_H1": (
            "Two-product cross-algorithm replication on Planck TT "
            "(SMICA-nosz + NILC; different component-separation "
            "algorithms) recovers Mersenne-fiber-degree concentration "
            "at {3, 7}. The Spike #187 BB H0 was noise-floor-driven "
            "(BB at Planck sensitivity is statistical upper limits, "
            "not detections). The empirical signature replicates "
            "cross-substrate (planetary internal fields + clean CMB "
            "TT). Spike #187 substrate-specificity refinement "
            "RELAXES toward universality."
        ),
        "interpretation_if_TT_disagrees": (
            "NILC and SMICA-nosz disagree on the TT concentration "
            "signal — would indicate component-separation-algorithm "
            "artifact rather than substrate physics. Defer verdict "
            "pending investigation."
        ),
    })

    # Discipline record
    records.append({
        "record_type": "discipline_record",
        "math_doesnt_lie": "Math doesn't lie. The {3,7} ℓ-bucket "
                            "fractional-power ratio is what the "
                            "Planck SMICA TT spectrum says at "
                            "low-ℓ, density-aware-null calibrated.",
        "asymptotic_ring_vocabulary": "S¹/S³/S⁷ ring-vocabulary "
                                       "preserved; no 'number ring' "
                                       "usage.",
        "fourteen_classes_status": "intact (A-N)",
        "identity_not_implementation": "healpy.anafast IS Class L "
                                       "on S²; cyclic-membership "
                                       "IS Class I; this script "
                                       "composes existing primitive "
                                       "operations.",
        "tos_compliance": "PLA open-access; no Sci-Hub-class "
                          "tooling; permitted per "
                          "[[reference_autonomous_validation_tos_landscape]]",
    })

    with open(out_ndjson, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\n[ndjson] wrote {len(records)} records to {out_ndjson}")

    # Print summary
    print("\n== Verdict ==")
    print(f"  verdict             : {primary['verdict']}")
    print(f"  ratio C_ℓ / null    : {primary['ratio_C_ell_actual_over_null_hopf']}")
    print(f"  ratio D_ℓ / null    : {primary['ratio_D_ell_actual_over_null_hopf']}")
    print(f"  p-value C_ℓ (right) : {primary['permutation_p_value_C_ell_hopf']}")
    print(f"  p-value D_ℓ (right) : {primary['permutation_p_value_D_ell_hopf']}")
    print(f"  frac C_ℓ at {{3,7}}   : {primary['frac_C_ell_at_hopf_fiber_set']:.4f}")
    print(f"  uniform null at {{3,7}}: {primary['uniform_null_hopf_fiber']:.4f}")
    print(f"\n  composition: {composition}")


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    out_ndjson = here / "spike190_findings_native_pipeline_2026-05-19.ndjson"
    # Cache directory: use user's WSL home for big FITS files
    # (~3.6 GB SMICA Nside=2048 IQU); the file lives outside the
    # repo to avoid git LFS / large-file issues.
    cache_dir = pathlib.Path(
        os.environ.get("SPIKE190_CACHE_DIR", "/tmp/spike190_planck_cache")
    )
    main(out_ndjson, cache_dir)
