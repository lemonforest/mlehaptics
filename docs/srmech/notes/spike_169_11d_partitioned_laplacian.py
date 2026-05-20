"""Spike #169 — 11D component-wise Laplacian spectral test.

PURPOSE: Bit-exact comparison between

  (A) Framework's 11D partitioned-Laplacian spectrum on
      3D_s ⊕ 7D_g ⊕ 1D_t per MFO §VII Stage 1:
        3D_s = C_32 × C_32 × C_32 (cyclic groups, Class I substrate)
        7D_g = C_3 × C_3 × C_2 × C_5 × C_7 × C_11 × C_13
        1D_t = C_64
      Class L Laplacian on the graph Cartesian product
      (Kirchhoff-Laplacian theorem; eigenvalues are sums of
      per-component cyclic-graph eigenvalues).

  (B) M-theory's baseline 4D-Lorentzian × 7D-internal Laplacian
      spectrum at matched mode-count. Uses canonical round-S^7
      (Spin(8) isometry, lambda_l = l(l+6), Spike #51.D) for the
      7D-internal factor and a uniform 4D-Lorentzian box-mode
      proxy for the M^4 factor.

against two observational targets:

  (a) Spike #47 R4-1 CMB selection-mask chain
      Lambda = {2, 12, 28, 52, 84, 126, 178, 244}
  (b) Spike #51.D KK partial-match levels (already known:
      ~5.1× better squashed-S^7 at p=0.041)

H1: framework's partitioned spectrum bit-exact-matches the CMB chain
    BETTER than M-theory's uniform 4D × 7D-internal spectrum by a
    quantifiable margin.

H0: per-component partition is spectrally indistinguishable from
    M-theory's uniform-compactification at currently testable
    observational targets, leaving the partition choice
    underdetermined.

Falsifier: bit-exact comparison of the two spectra against
(a) and (b) above.

PER-COMPONENT SPECTRA (cyclic-graph Laplacian on C_n):

  For undirected cycle graph C_n, the graph Laplacian L = D - A
  has eigenvalues
      lambda_k(C_n) = 2 - 2 cos(2*pi*k/n) = 4 sin^2(pi*k/n)
  for k = 0, 1, ..., n-1.
  Reference: Kirchhoff (1847) / Spielman 2007 lecture notes on
  graph Laplacians; canonical result.

  Graph Cartesian product G_1 □ G_2 □ ... □ G_d has eigenvalues
      lambda_{k1,...,kd} = sum_i lambda_{ki}(G_i)
  Reference: Merris 1994 "Laplacian matrices of graphs: a survey"
  Linear Algebra Appl. 197-198, 143-176.

  This is the SUBSTRATE-LEVEL spectrum per [[user_stance_cascade_lives_on_circles]]
  — eigenvalues live on the unit circle algebraically; the 4 sin^2
  form is the continuous-projection shadow per [[user_stance_pi_as_projection]].

MODE COUNT:
  |3D_s| = 32^3 = 32768
  |7D_g| = 3*3*2*5*7*11*13 = 90090
  |1D_t| = 64
  Total = 32768 * 90090 * 64 = 188,917,186,560 eigenvalues
  (this is the full cardinality of the underlying cyclic-group
  product per MFO §VII Stage 1; we compute LOW-MODE spectrum
  by sampling only the first few k per factor — the substrate
  eigenvalue catalog at low-momentum)

M-THEORY BASELINE:
  Standard 4D-Lorentzian (Mink^4) Laplacian spectrum is continuous
  (R^4 has no compact directions); for matched-mode-count we use
  a 4D-box with L^4 sites at lattice spacing matched to the CMB
  multipole-scale. The 7D-internal factor is round-S^7 KK tower
  lambda_l = l(l+6) per Spike #51.D (canonical Spin(8)).

CITATIONS (PDF-verified per [[feedback_pdf_extraction_citation_discipline]]):
- Spielman 2007 (lecture notes on graph Laplacians; standard cycle spectrum)
- Merris 1994 LinAlgAppl 197-198:143 (Laplacian survey; Cartesian-product theorem)
- Ekhammar-Nilsson 2021 arXiv:2105.05229 (squashed-S^7 KK; Eq. 3.3, 3.5)
- Nilsson 2024 arXiv:2412.04208 (round-S^7 Laplacian; Fig. 2)
- Awada-Duff-Pope 1983 PRL 50:294 (cite-by-ref; APS paywall)
- Spike #47 R4-1 internal anchor (selection-mask chain)
- Spike #51.D internal anchor (KK spectrum comparison)
- Spike #164 internal anchor (M-theory failure modes 12/15)

Per [[feedback_no_privileged_primitive_classes]]: 14 classes A-N intact.
Per [[feedback_computational_provenance_discipline]]: this script IS
the computational provenance for every numerical claim in
spike_169_findings_2026-05-19.ndjson.
Per [[feedback_ndjson_over_bloated_json]]: NDJSON output, one record
per (substrate-spec, observable-target, metric) cell.

NDJSON output: spike_169_findings_2026-05-19.ndjson
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path


# =============================================================================
# Per-component cyclic-graph Laplacian spectra
# =============================================================================


def cyclic_laplacian_eigenvalues(n: int) -> list[float]:
    """Eigenvalues of the Laplacian of cycle graph C_n.

    lambda_k = 2 - 2 cos(2 pi k / n) = 4 sin^2(pi k / n)
    for k = 0, 1, ..., n-1.

    Reference: standard graph Laplacian result on the n-cycle.
    """
    return [4.0 * math.sin(math.pi * k / n) ** 2 for k in range(n)]


def cyclic_laplacian_low_modes(n: int, max_k: int) -> list[float]:
    """First max_k+1 modes (k = 0..max_k) of C_n Laplacian.

    For large n, the low-momentum modes are
        lambda_k ~= (2*pi*k/n)^2 = 4*pi^2 k^2 / n^2
    which is the dominant contribution to small total-eigenvalue sums.
    """
    return [4.0 * math.sin(math.pi * k / n) ** 2 for k in range(max_k + 1)]


def kk_eigenvalues_continuum(n: int, max_k: int) -> list[float]:
    """KK-tower eigenvalues on cyclic substrate C_n, continuum-limit form.

    For comparison with KK spectra on continuous compact manifolds
    (round-S^7 lambda_l = l(l+6), etc.), the natural normalization is
    the squared-momentum form:
        lambda_k = k^2  (in units where compactification radius = 1)

    This is the KK-tower-on-S^1 spectrum
    (compactified-circle massless Laplacian -d^2/dx^2 with periodic
    boundary). The cycle-graph 4*sin^2(pi*k/n) reduces to (2*pi*k/n)^2
    in the n→∞ limit; we use the k^2 form for the comparison since
    CMB chain values {2, 12, 28, 52, 84, 126, 178, 244} are in
    units already consistent with l(l+6)-type KK spectra.

    Per [[user_stance_pi_as_projection]]: the continuum-limit form is
    the projection-shadow of the integer-cyclic substrate-level
    catalog; both encode the same algebraic content, the difference
    is just whether we read at substrate-level (integer k catalog)
    or projection-level (continuous lambda_k tower).
    """
    return [float(k) ** 2 for k in range(max_k + 1)]


# =============================================================================
# Graph Cartesian product: eigenvalues are sums of per-component eigenvalues
# =============================================================================


def low_mode_spectrum_cartesian(
    factors: list[int],
    max_k_per_factor: int = 4,
    n_eigs_to_return: int = 400,
    mode: str = "kk_continuum",
) -> list[float]:
    """Compute the lowest-K modes of the Laplacian on a Cartesian product of
    cycle graphs.

    For C_{n_1} x C_{n_2} x ... x C_{n_d}, eigenvalues are
        sum_i lambda_{k_i}(C_{n_i})
    with k_i in [0, n_i - 1].

    Two modes (per [[user_stance_pi_as_projection]] substrate-vs-shadow):

    - mode="graph_laplacian": substrate-level eigenvalues 4*sin^2(pi*k/n),
      bounded in [0, 4] per factor. This is the integer-cyclic-algebra
      form per Spike #58.G and Spike #75.
    - mode="kk_continuum": KK-tower-projection eigenvalues k^2 (continuum
      limit; unbounded). This is the form that matches CMB chain
      magnitudes and l(l+6) KK spectra. Per [[user_stance_pi_as_projection]],
      this is the projection-shadow of the substrate-level integer catalog.

    We enumerate combinations with k_i in [0, max_k_per_factor],
    sort ascending, and return the lowest n_eigs_to_return.
    """
    if mode == "graph_laplacian":
        per_factor = [cyclic_laplacian_low_modes(n, max_k_per_factor) for n in factors]
    elif mode == "kk_continuum":
        per_factor = [kk_eigenvalues_continuum(n, max_k_per_factor) for n in factors]
    else:
        raise ValueError(f"Unknown mode: {mode}")

    eigs: list[float] = []
    indices = [0] * len(factors)
    # Cartesian product over per_factor indices
    while True:
        eig = sum(per_factor[i][indices[i]] for i in range(len(factors)))
        eigs.append(eig)
        # Increment indices like an odometer
        i = len(factors) - 1
        while i >= 0:
            indices[i] += 1
            if indices[i] < len(per_factor[i]):
                break
            indices[i] = 0
            i -= 1
        if i < 0:
            break

    eigs.sort()
    return eigs[:n_eigs_to_return]


# =============================================================================
# Substrate specifications per brief
# =============================================================================

# 3D_s = C_32 x C_32 x C_32 (per MFO §VII Stage 1, "32-strands" anchor)
SPATIAL_3D_FACTORS = [32, 32, 32]

# 7D_g = C_3 x C_3 x C_2 x C_5 x C_7 x C_11 x C_13 (per brief; canonical
# small-prime composition from MFO §VII Stage 1; first seven primes with
# C_3 repeated for SU(2)_L doubling per [[user_stance_gauge_ball_is_4plus3_hopf_dimple]])
GAUGE_7D_FACTORS = [3, 3, 2, 5, 7, 11, 13]

# 1D_t = C_64 (per brief; 2^6 = 64, single asymptotic-DOF tick per
# [[user_stance_universal_1d_t_tick_projects_to_per_body_local_time_dof]])
TEMPORAL_1D_FACTORS = [64]

# Combined 11D
ALL_11D_FACTORS = SPATIAL_3D_FACTORS + GAUGE_7D_FACTORS + TEMPORAL_1D_FACTORS


# =============================================================================
# M-theory baseline: 4D x 7D-internal uniform compactification
# =============================================================================


def mtheory_4d_box_eigenvalues(L: int, max_k: int,
                                mode: str = "kk_continuum") -> list[float]:
    """4D-Lorentzian box-Laplacian eigenvalues at lattice size L.

    On a Lorentzian R^{3,1} with periodic boundary conditions at
    scale L (M-theory's 4D-spacetime treated as compactified for
    matched-mode-count), eigenvalues are

        mode="graph_laplacian": 4 sin^2(pi k_i / L)  (lattice form)
        mode="kk_continuum":    k_i^2                 (KK-tower form)

    Using same mode as framework for fair comparison.
    """
    if mode == "graph_laplacian":
        per_dir = cyclic_laplacian_low_modes(L, max_k)
    elif mode == "kk_continuum":
        per_dir = kk_eigenvalues_continuum(L, max_k)
    else:
        raise ValueError(f"Unknown mode: {mode}")
    eigs: list[float] = []
    for k0 in range(max_k + 1):
        for k1 in range(max_k + 1):
            for k2 in range(max_k + 1):
                for k3 in range(max_k + 1):
                    eigs.append(per_dir[k0] + per_dir[k1] + per_dir[k2] + per_dir[k3])
    eigs.sort()
    return eigs


def round_S7_KK_eigenvalues(l_max: int = 20) -> list[float]:
    """Round-S^7 scalar Laplacian KK tower: lambda_l = l(l+6).

    Per Spike #51.D canonical reference; standard result.
    Multiplicity inherits SO(8) symmetric traceless rank-l tensor dim.
    """
    return [float(l * (l + 6)) for l in range(l_max + 1)]


def mtheory_uniform_spectrum(L: int = 32, max_k_4d: int = 4,
                              l_max_S7: int = 12,
                              n_eigs_to_return: int = 400,
                              mode_4d: str = "kk_continuum") -> list[float]:
    """M-theory's uniform 4D x 7D-internal spectrum.

    M-theory compactification: 11D = M^4 x X^7 with X^7 = round-S^7
    (parallelizable-7-manifold proxy; G_2-holonomy quotients are
    same algebra at Laplacian-eigenvalue level per Spike #51 R3-delta).

    Combined Laplacian eigenvalues are sums:
        lambda = lambda_4D + lambda_S7

    The 7D-internal factor is canonical l(l+6) — unitful, unbounded.
    The 4D-Lorentzian factor is computed with same `mode` as framework
    for fair comparison.
    """
    eigs_4d = mtheory_4d_box_eigenvalues(L, max_k_4d, mode=mode_4d)
    eigs_S7 = round_S7_KK_eigenvalues(l_max_S7)
    combined: list[float] = []
    for e4 in eigs_4d:
        for e7 in eigs_S7:
            combined.append(e4 + e7)
    combined.sort()
    return combined[:n_eigs_to_return]


# =============================================================================
# Observational targets
# =============================================================================

# Spike #47 R4-1 CMB selection-mask chain
CMB_CHAIN = [2, 12, 28, 52, 84, 126, 178, 244]


def fit_to_chain(spectrum: list[float], chain: list[float]) -> dict:
    """For each Lambda in chain, find closest eigenvalue in spectrum.

    Returns:
      per_lambda: list of {Lambda, closest, |delta|, rel_pct, bit_exact}
      median_abs: median |delta|
      mean_abs: mean |delta|
      bit_exact_count: number of bit-exact matches (|delta| < 1e-12)
      n_within_1pct: count of relative differences below 1%
      sum_sq: sum of squared |delta| (proxy for chi^2)
    """
    per: list[dict] = []
    for lam in chain:
        closest = min(spectrum, key=lambda x: abs(x - lam))
        delta = abs(closest - lam)
        # bit-exact at machine precision
        bit_exact = delta < 1e-12
        rel_pct = delta / max(abs(lam), 1.0) * 100.0
        per.append({
            "Lambda": lam,
            "closest_spectrum_eig": closest,
            "abs_diff": delta,
            "rel_pct": rel_pct,
            "bit_exact": bit_exact,
            "within_1pct": rel_pct < 1.0,
        })
    abs_diffs = sorted(p["abs_diff"] for p in per)
    median = abs_diffs[len(abs_diffs) // 2]
    mean = sum(abs_diffs) / len(abs_diffs)
    sum_sq = sum(d * d for d in abs_diffs)
    bit_exact_count = sum(1 for p in per if p["bit_exact"])
    within_1pct = sum(1 for p in per if p["within_1pct"])
    return {
        "per_lambda": per,
        "median_abs_diff": median,
        "mean_abs_diff": mean,
        "bit_exact_count": bit_exact_count,
        "within_1pct_count": within_1pct,
        "n_chain": len(chain),
        "sum_squared_abs_diff": sum_sq,
        "rms": math.sqrt(sum_sq / len(chain)),
    }


# =============================================================================
# Null hypothesis test (research-discipline per Spike #181)
# =============================================================================


def null_test_random_uniform(
    chain: list[float],
    n_spectrum_eigs: int,
    eig_range: tuple[float, float],
    n_trials: int = 1000,
    seed: int = 42,
) -> dict:
    """Random uniform-in-range eigenvalues; how often does median |delta|
    beat the observed value?

    This is the p-value test for "did the substrate-spec just luck out by
    having dense-enough modes?" Per [[feedback_computational_provenance_discipline]].
    """
    rng = random.Random(seed)
    medians: list[float] = []
    for _ in range(n_trials):
        random_spectrum = [rng.uniform(eig_range[0], eig_range[1])
                          for _ in range(n_spectrum_eigs)]
        diffs = [min(abs(s - lam) for s in random_spectrum) for lam in chain]
        diffs.sort()
        medians.append(diffs[len(diffs) // 2])
    medians.sort()
    return {
        "n_trials": n_trials,
        "seed": seed,
        "n_spectrum_eigs_sampled": n_spectrum_eigs,
        "eig_range_lo": eig_range[0],
        "eig_range_hi": eig_range[1],
        "null_median_p25": medians[n_trials // 4],
        "null_median_p50": medians[n_trials // 2],
        "null_median_p75": medians[3 * n_trials // 4],
        "null_median_p05": medians[n_trials // 20],
    }


def p_value_of_observed(
    observed_median: float,
    chain: list[float],
    n_spectrum_eigs: int,
    eig_range: tuple[float, float],
    n_trials: int = 10000,
    seed: int = 42,
) -> float:
    """Fraction of null trials with median <= observed_median.

    p < 0.05 means observed is significantly tighter than chance.

    Per Spike #181 discipline: n_spectrum_eigs MUST be the count of UNIQUE
    eigenvalues in the relevant range, not the total spectrum size, to
    match density-of-states between spectrum and null trials.
    """
    rng = random.Random(seed)
    n_below = 0
    for _ in range(n_trials):
        random_spectrum = [rng.uniform(eig_range[0], eig_range[1])
                          for _ in range(n_spectrum_eigs)]
        diffs = [min(abs(s - lam) for s in random_spectrum) for lam in chain]
        diffs.sort()
        median = diffs[len(diffs) // 2]
        if median <= observed_median:
            n_below += 1
    return n_below / n_trials


def density_of_states(spectrum: list[float], eig_range: tuple[float, float]) -> dict:
    """Diagnose density of states for honest p-value computation.

    Per Spike #181 discipline: dense substrates can match anything by
    pigeon-hole. The honest comparison is `match-quality per unit density`.
    """
    in_range = [e for e in spectrum if eig_range[0] <= e <= eig_range[1]]
    unique_in_range = sorted({round(e, 9) for e in in_range})
    return {
        "n_in_range": len(in_range),
        "n_unique_in_range": len(unique_in_range),
        "range_width": eig_range[1] - eig_range[0],
        "density_per_unit": len(unique_in_range) / max(eig_range[1] - eig_range[0], 1e-9),
        "mean_gap": (
            sum(unique_in_range[i+1] - unique_in_range[i] for i in range(len(unique_in_range)-1))
            / max(len(unique_in_range) - 1, 1)
        ) if len(unique_in_range) > 1 else float("inf"),
    }


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    out_path = Path(__file__).parent / "spike_169_findings_2026-05-19.ndjson"

    records: list[dict] = []

    # -------------------------------------------------------------------------
    # FRAMEWORK SPECTRUM: 11D = 3D_s + 7D_g + 1D_t partitioned-Laplacian
    # -------------------------------------------------------------------------

    # Per-component sub-spectra (low-mode catalog, KK-continuum form for
    # comparability with CMB chain magnitudes per [[user_stance_pi_as_projection]])
    # max_k_per_factor=16 gives single-direction modes up to k^2 = 256 — enough
    # to span the CMB chain {2..244}
    spatial_low = low_mode_spectrum_cartesian(SPATIAL_3D_FACTORS, max_k_per_factor=16,
                                              n_eigs_to_return=2000,
                                              mode="kk_continuum")
    gauge_low = low_mode_spectrum_cartesian(GAUGE_7D_FACTORS, max_k_per_factor=12,
                                            n_eigs_to_return=2000,
                                            mode="kk_continuum")
    temporal_low = kk_eigenvalues_continuum(64, max_k=16)

    # Full 11D combined: sum per-component eigenvalues, take lowest 400
    framework_eigs: list[float] = []
    for es in spatial_low[:60]:
        for eg in gauge_low[:60]:
            for et in temporal_low[:17]:
                framework_eigs.append(es + eg + et)
    framework_eigs.sort()
    # Deduplicate at machine precision for cleaner set-overlap analysis
    framework_eigs_dedup: list[float] = []
    for e in framework_eigs:
        if not framework_eigs_dedup or abs(e - framework_eigs_dedup[-1]) > 1e-12:
            framework_eigs_dedup.append(e)
    framework_eigs = framework_eigs_dedup[:600]

    # Record substrate spec
    records.append({
        "kind": "substrate_spec_framework",
        "spike": "#169",
        "date": "2026-05-19",
        "spec": "11D = 3D_s + 7D_g + 1D_t",
        "spatial_3D_factors": SPATIAL_3D_FACTORS,
        "spatial_3D_cardinality": math.prod(SPATIAL_3D_FACTORS),
        "gauge_7D_factors": GAUGE_7D_FACTORS,
        "gauge_7D_cardinality": math.prod(GAUGE_7D_FACTORS),
        "temporal_1D_factors": TEMPORAL_1D_FACTORS,
        "temporal_1D_cardinality": math.prod(TEMPORAL_1D_FACTORS),
        "total_cardinality": math.prod(ALL_11D_FACTORS),
        "n_eigs_computed_for_comparison": len(framework_eigs),
        "lowest_10_eigs": framework_eigs[:10],
        "reference": "MFO §VII Stage 1 substrate composition; [[project_space_gauge_time_framework]]; [[user_stance_universal_1d_t_tick_projects_to_per_body_local_time_dof]]",
    })

    # -------------------------------------------------------------------------
    # M-THEORY SPECTRUM: 4D x 7D-internal uniform compactification
    # -------------------------------------------------------------------------

    mtheory_eigs = mtheory_uniform_spectrum(L=32, max_k_4d=16, l_max_S7=16,
                                             n_eigs_to_return=600,
                                             mode_4d="kk_continuum")
    # Deduplicate
    mt_dedup: list[float] = []
    for e in mtheory_eigs:
        if not mt_dedup or abs(e - mt_dedup[-1]) > 1e-12:
            mt_dedup.append(e)
    mtheory_eigs = mt_dedup[:600]

    records.append({
        "kind": "substrate_spec_mtheory",
        "spike": "#169",
        "date": "2026-05-19",
        "spec": "11D = M^4 x X^7 (M-theory uniform compactification)",
        "M4_box_size_L": 32,
        "M4_max_k": 4,
        "X7_substrate": "round-S^7 KK tower (Spin(8))",
        "X7_l_max": 12,
        "n_eigs_computed_for_comparison": len(mtheory_eigs),
        "lowest_10_eigs": mtheory_eigs[:10],
        "reference": "Spike #51.D round-S^7 canonical; Witten 1995 hep-th/9503124 cite-by-ref; Acharya-Witten 2001 hep-th/0109152 cite-by-ref",
    })

    # -------------------------------------------------------------------------
    # OBSERVATIONAL TARGET (a): Spike #47 R4-1 CMB selection-mask chain
    # -------------------------------------------------------------------------

    framework_fit = fit_to_chain(framework_eigs, CMB_CHAIN)
    mtheory_fit = fit_to_chain(mtheory_eigs, CMB_CHAIN)

    records.append({
        "kind": "fit_to_cmb_chain_framework",
        "spike": "#169",
        "date": "2026-05-19",
        "observable": "Spike #47 R4-1 CMB selection-mask chain",
        "chain": CMB_CHAIN,
        "substrate": "framework_partitioned_11D",
        **framework_fit,
    })

    records.append({
        "kind": "fit_to_cmb_chain_mtheory",
        "spike": "#169",
        "date": "2026-05-19",
        "observable": "Spike #47 R4-1 CMB selection-mask chain",
        "chain": CMB_CHAIN,
        "substrate": "mtheory_uniform_11D",
        **mtheory_fit,
    })

    # Pairwise comparison
    fw_median = framework_fit["median_abs_diff"]
    mt_median = mtheory_fit["median_abs_diff"]
    fw_rms = framework_fit["rms"]
    mt_rms = mtheory_fit["rms"]

    if min(fw_median, mt_median) < 1e-9:
        median_ratio = float("inf") if fw_median < mt_median else 0.0
    else:
        median_ratio = mt_median / fw_median  # >1 means framework better

    if min(fw_rms, mt_rms) < 1e-9:
        rms_ratio = float("inf") if fw_rms < mt_rms else 0.0
    else:
        rms_ratio = mt_rms / fw_rms  # >1 means framework better

    # Chi^2 ratio (using sum_squared_abs_diff as chi^2 proxy)
    fw_chi2 = framework_fit["sum_squared_abs_diff"]
    mt_chi2 = mtheory_fit["sum_squared_abs_diff"]
    if min(fw_chi2, mt_chi2) < 1e-9:
        chi2_ratio = float("inf") if fw_chi2 < mt_chi2 else 0.0
    else:
        chi2_ratio = mt_chi2 / fw_chi2  # >1 means framework better

    # -------------------------------------------------------------------------
    # NULL HYPOTHESIS TESTS (per [[feedback_computational_provenance_discipline]])
    # -------------------------------------------------------------------------

    eig_range = (0.0, max(CMB_CHAIN) * 1.05)

    # Density-of-states diagnostic per Spike #181 discipline
    fw_dos = density_of_states(framework_eigs, eig_range)
    mt_dos = density_of_states(mtheory_eigs, eig_range)

    records.append({
        "kind": "density_of_states_diagnostic",
        "spike": "#169",
        "date": "2026-05-19",
        "eig_range_lo": eig_range[0],
        "eig_range_hi": eig_range[1],
        "framework_dos": fw_dos,
        "mtheory_dos": mt_dos,
        "density_ratio_framework_over_mtheory": (
            fw_dos["density_per_unit"] / max(mt_dos["density_per_unit"], 1e-9)
        ),
        "note": (
            "Per Spike #181 discipline (catch density-of-states artifact in p-value tests): "
            "If framework spectrum is denser than M-theory spectrum, framework will "
            "trivially have lower median |Δ| by pigeon-hole. The HONEST p-value uses "
            "the count of UNIQUE eigenvalues in the relevant range as the null-trial "
            "spectrum size, not the total computed spectrum count."
        ),
    })

    # Use density-matched null-trial spectrum sizes for fair p-values
    fw_p = p_value_of_observed(
        observed_median=fw_median,
        chain=CMB_CHAIN,
        n_spectrum_eigs=fw_dos["n_unique_in_range"],
        eig_range=eig_range,
        n_trials=10000,
        seed=42,
    )
    mt_p = p_value_of_observed(
        observed_median=mt_median,
        chain=CMB_CHAIN,
        n_spectrum_eigs=mt_dos["n_unique_in_range"],
        eig_range=eig_range,
        n_trials=10000,
        seed=42,
    )

    records.append({
        "kind": "pairwise_comparison_cmb",
        "spike": "#169",
        "date": "2026-05-19",
        "observable": "Spike #47 R4-1 CMB selection-mask chain",
        "framework_median_abs_diff": fw_median,
        "mtheory_median_abs_diff": mt_median,
        "median_ratio_mtheory_over_framework": median_ratio,
        "framework_rms": fw_rms,
        "mtheory_rms": mt_rms,
        "rms_ratio_mtheory_over_framework": rms_ratio,
        "framework_chi2": fw_chi2,
        "mtheory_chi2": mt_chi2,
        "chi2_ratio_mtheory_over_framework": chi2_ratio,
        "framework_bit_exact_count": framework_fit["bit_exact_count"],
        "mtheory_bit_exact_count": mtheory_fit["bit_exact_count"],
        "framework_within_1pct_count": framework_fit["within_1pct_count"],
        "mtheory_within_1pct_count": mtheory_fit["within_1pct_count"],
        "framework_null_p_value": fw_p,
        "mtheory_null_p_value": mt_p,
        "null_test_trials": 10000,
        "null_test_seed": 42,
        "null_test_eig_range_lo": eig_range[0],
        "null_test_eig_range_hi": eig_range[1],
    })

    # -------------------------------------------------------------------------
    # OBSERVATIONAL TARGET (b): Spike #51.D KK partial-match
    # -------------------------------------------------------------------------
    #
    # Already-known: squashed-S^7 fits chain ~5.1x better than round-S^7
    # (median |Delta|: round=4, squashed=0.778). The framework's
    # partitioned-Laplacian must improve on BOTH to claim H1.

    SQUASHED_S7_MEDIAN = 0.7778  # from Spike #51.D
    ROUND_S7_MEDIAN = 4.0          # from Spike #51.D

    records.append({
        "kind": "fit_to_cmb_chain_squashed_S7_canonical",
        "spike": "#169",
        "date": "2026-05-19",
        "observable": "Spike #47 R4-1 CMB selection-mask chain",
        "substrate": "M-theory squashed-S^7 (Awada-Duff-Pope 1983)",
        "median_abs_diff": SQUASHED_S7_MEDIAN,
        "p_value": 0.041,
        "reference": "Spike #51.D records (spike_51_d_kk_spectrum_records_2026-05-19.ndjson)",
        "note": "Used as canonical M-theory-best-case alternative; squashed-S^7 fits chain best among M-theory spectra tested in Spike #51.D",
    })

    records.append({
        "kind": "fit_to_cmb_chain_round_S7_canonical",
        "spike": "#169",
        "date": "2026-05-19",
        "observable": "Spike #47 R4-1 CMB selection-mask chain",
        "substrate": "round-S^7 KK tower (Spin(8))",
        "median_abs_diff": ROUND_S7_MEDIAN,
        "reference": "Spike #51.D records (spike_51_d_kk_spectrum_records_2026-05-19.ndjson)",
        "note": "Canonical M-theory uniform-X^7 reference",
    })

    # Cross-comparison: framework vs squashed-S^7 vs round-S^7 vs mtheory-uniform
    records.append({
        "kind": "cross_comparison_four_way",
        "spike": "#169",
        "date": "2026-05-19",
        "observable": "Spike #47 R4-1 CMB selection-mask chain",
        "spectra_ranked_by_median_abs_diff": sorted([
            ("framework_partitioned_11D", fw_median),
            ("mtheory_uniform_4D_x_S7", mt_median),
            ("squashed_S7_alone", SQUASHED_S7_MEDIAN),
            ("round_S7_alone", ROUND_S7_MEDIAN),
        ], key=lambda x: x[1]),
        "framework_vs_squashed_ratio": (
            SQUASHED_S7_MEDIAN / fw_median if fw_median > 0 else float("inf")
        ),
        "framework_vs_round_ratio": (
            ROUND_S7_MEDIAN / fw_median if fw_median > 0 else float("inf")
        ),
    })

    # -------------------------------------------------------------------------
    # H1 vs H0 verdict
    # -------------------------------------------------------------------------

    # H1 criteria (Spike #181-discipline-aware):
    #   (i) framework_median < mtheory_median (margin >= 2x)
    #   (ii) framework_bit_exact > mtheory_bit_exact OR within_1pct >
    #   (iii) framework p-value < 0.05 (density-matched null)
    h1_criterion_i = median_ratio >= 2.0
    h1_criterion_ii = (
        framework_fit["bit_exact_count"] > mtheory_fit["bit_exact_count"]
        or framework_fit["within_1pct_count"] > mtheory_fit["within_1pct_count"]
    )
    h1_criterion_iii = fw_p < 0.05

    h1_score = sum([h1_criterion_i, h1_criterion_ii, h1_criterion_iii])

    # Honest density-of-states diagnostic per Spike #181:
    # If framework density >> M-theory density, the bit-exact match is
    # likely a density artifact, not a substrate-specific signal.
    density_ratio = fw_dos["density_per_unit"] / max(mt_dos["density_per_unit"], 1e-9)
    density_artifact_concern = density_ratio > 3.0

    if h1_score == 3 and not density_artifact_concern:
        verdict = "H1-CONFIRMED"
    elif h1_score == 3 and density_artifact_concern:
        verdict = "H1-CONFIRMED-WITH-DENSITY-ARTIFACT-CONCERN"
    elif h1_score == 2:
        verdict = "H1-PARTIAL"
    elif h1_score == 1:
        verdict = "H0-LEANING"
    else:
        verdict = "H0-CONFIRMED"

    # Additional discriminator: framework must improve on squashed-S^7 to be load-bearing
    framework_beats_squashed = fw_median < SQUASHED_S7_MEDIAN

    records.append({
        "kind": "h1_vs_h0_verdict",
        "spike": "#169",
        "date": "2026-05-19",
        "verdict": verdict,
        "h1_score": f"{h1_score}/3",
        "h1_criterion_i_margin_2x": h1_criterion_i,
        "h1_criterion_ii_more_bit_exact_or_within_1pct": h1_criterion_ii,
        "h1_criterion_iii_p_lt_005": h1_criterion_iii,
        "density_artifact_concern": density_artifact_concern,
        "framework_density_per_unit": fw_dos["density_per_unit"],
        "mtheory_density_per_unit": mt_dos["density_per_unit"],
        "density_ratio_framework_over_mtheory": density_ratio,
        "framework_beats_squashed_S7_alone": framework_beats_squashed,
        "framework_p_value": fw_p,
        "mtheory_p_value": mt_p,
        "median_ratio_mtheory_over_framework": median_ratio,
        "interpretation": (
            "Framework's 11D partitioned-Laplacian "
            + (
                f"BIT-EXACT-beats M-theory's 4D x 7D uniform spectrum by {median_ratio:.2f}x "
                "on median |Δ| against Spike #47 R4-1 CMB chain. "
                if h1_criterion_i else
                "DOES NOT decisively beat M-theory's 4D x 7D uniform spectrum "
                f"(ratio {median_ratio:.2f}x; needs >= 2.0x for H1). "
            )
            + (
                f"Framework p-value {fw_p:.4f} (density-matched null) is significant. "
                if h1_criterion_iii else
                f"Framework p-value {fw_p:.4f} (density-matched null) is not below 0.05. "
            )
            + (
                "Framework also beats squashed-S^7 (Spike #51.D best-of-class). "
                if framework_beats_squashed else
                f"Framework median |Δ|={fw_median:.3f} does NOT beat squashed-S^7 ({SQUASHED_S7_MEDIAN}). "
            )
            + (
                f"DENSITY-OF-STATES CONCERN per Spike #181: framework density "
                f"{fw_dos['density_per_unit']:.3f}/unit is {density_ratio:.1f}x higher than M-theory "
                f"{mt_dos['density_per_unit']:.3f}/unit; bit-exact matches may be a "
                "density artifact rather than substrate-specific signal. The fair "
                "p-value test (density-matched null) is the load-bearing diagnostic."
                if density_artifact_concern else
                "Density-of-states ratio is acceptable; bit-exact matches are "
                "substrate-specific not density-artifact."
            )
        ),
    })

    # -------------------------------------------------------------------------
    # Composes-with stance check
    # -------------------------------------------------------------------------

    records.append({
        "kind": "composes_with_canonical_stances",
        "spike": "#169",
        "date": "2026-05-19",
        "if_H1": [
            "project_space_gauge_time_framework (strengthened: bit-exact diagnostic)",
            "feedback_spacetime_means_full_11d_not_just_3d_s_plus_1d_t (strengthened)",
            "user_stance_1d_collapse_to_loe_identity_not_action (strengthened)",
            "user_stance_competing_theories_via_loe_instantiation_intersection (strengthened: surgical diagnostic)",
            "Spike #164 entry #12 (4D x 7D-internal NOT-INSTANTIATED) — promoted from algebra-level to bit-exact-spectral-level",
        ],
        "threatens_regardless": [
            "M-theory's 4D x 7D-internal IDENTITY claim — Spike #164 already mapped 12/15 NOT-INSTANTIATED; this spike supplies bit-exact diagnostic",
        ],
        "if_H0": [
            "Per-component partition is spectrally indistinguishable at current observational targets",
            "Partition choice is underdetermined — does NOT promote framework over M-theory at spectral level",
            "Algebra-level distinction (Spike #164) stands; spectral-level distinction needs higher-precision observable",
        ],
    })

    # -------------------------------------------------------------------------
    # Write NDJSON
    # -------------------------------------------------------------------------

    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=lambda x: (
                list(x) if isinstance(x, tuple) else
                str(x)
            )) + "\n")

    print(f"Wrote {out_path}")
    print()
    print("=" * 80)
    print("SPIKE #169 — 11D component-wise Laplacian spectral test")
    print("=" * 80)
    print()
    print(f"Framework substrate: 3D_s = C_32^3, 7D_g = C_3 x C_3 x C_2 x C_5 x C_7 x C_11 x C_13, 1D_t = C_64")
    print(f"M-theory substrate:  M^4 (L=32 box) x round-S^7 (l_max=12)")
    print(f"Observational target: Spike #47 R4-1 CMB chain {CMB_CHAIN}")
    print()
    print(f"Framework spectrum lowest 10: {[round(x, 4) for x in framework_eigs[:10]]}")
    print(f"M-theory spectrum lowest 10:  {[round(x, 4) for x in mtheory_eigs[:10]]}")
    print()
    print("=" * 80)
    print("FIT TO CMB CHAIN — per-Lambda detail")
    print("=" * 80)
    print(f"{'Lambda':>8} {'fw eig':>10} {'fw |d|':>8} {'fw rel%':>8} {'mt eig':>10} {'mt |d|':>8} {'mt rel%':>8}")
    for lam, fp, mp in zip(CMB_CHAIN, framework_fit["per_lambda"], mtheory_fit["per_lambda"]):
        print(f"{lam:>8} {fp['closest_spectrum_eig']:>10.4f} {fp['abs_diff']:>8.4f} {fp['rel_pct']:>8.2f} "
              f"{mp['closest_spectrum_eig']:>10.4f} {mp['abs_diff']:>8.4f} {mp['rel_pct']:>8.2f}")
    print()
    print("=" * 80)
    print("AGGREGATE COMPARISON")
    print("=" * 80)
    print(f"Framework median |delta|:  {fw_median:.4f}    rms: {fw_rms:.4f}    chi^2 (sum sq): {fw_chi2:.4f}")
    print(f"M-theory median |delta|:   {mt_median:.4f}    rms: {mt_rms:.4f}    chi^2 (sum sq): {mt_chi2:.4f}")
    print(f"Median-ratio (mt / fw):    {median_ratio:.4f}")
    print(f"RMS-ratio (mt / fw):       {rms_ratio:.4f}")
    print(f"Chi^2-ratio (mt / fw):     {chi2_ratio:.4f}")
    print()
    print(f"Framework bit-exact count:        {framework_fit['bit_exact_count']}/{len(CMB_CHAIN)}")
    print(f"M-theory bit-exact count:         {mtheory_fit['bit_exact_count']}/{len(CMB_CHAIN)}")
    print(f"Framework within-1pct count:      {framework_fit['within_1pct_count']}/{len(CMB_CHAIN)}")
    print(f"M-theory within-1pct count:       {mtheory_fit['within_1pct_count']}/{len(CMB_CHAIN)}")
    print()
    print(f"Framework null p-value:           {fw_p:.4f}")
    print(f"M-theory null p-value:            {mt_p:.4f}")
    print()
    print("=" * 80)
    print("REFERENCE — Spike #51.D canonical (squashed vs round S^7 alone)")
    print("=" * 80)
    print(f"squashed-S^7 alone median |Delta|: {SQUASHED_S7_MEDIAN}  (p=0.041)")
    print(f"round-S^7 alone median |Delta|:    {ROUND_S7_MEDIAN}")
    print()
    print(f"Framework vs squashed-S^7 ratio:   {SQUASHED_S7_MEDIAN / fw_median if fw_median > 0 else float('inf'):.4f}")
    print(f"Framework vs round-S^7 ratio:      {ROUND_S7_MEDIAN / fw_median if fw_median > 0 else float('inf'):.4f}")
    print()
    print("=" * 80)
    print(f"VERDICT: {verdict}  ({h1_score}/3 H1 criteria)")
    print("=" * 80)
    print(f"  (i)   margin >= 2x:                  {h1_criterion_i}")
    print(f"  (ii)  more bit-exact/1pct:           {h1_criterion_ii}")
    print(f"  (iii) p < 0.05 (density-matched):    {h1_criterion_iii}")
    print(f"  Framework beats squashed-S^7:        {framework_beats_squashed}")
    print()
    print(f"  DENSITY OF STATES per Spike #181 discipline:")
    print(f"    Framework: {fw_dos['n_unique_in_range']} unique eigs in [0, {eig_range[1]:.0f}]  ({fw_dos['density_per_unit']:.4f}/unit, mean gap {fw_dos['mean_gap']:.3f})")
    print(f"    M-theory:  {mt_dos['n_unique_in_range']} unique eigs in [0, {eig_range[1]:.0f}]  ({mt_dos['density_per_unit']:.4f}/unit, mean gap {mt_dos['mean_gap']:.3f})")
    print(f"    Density ratio (fw/mt):             {density_ratio:.2f}x")
    print(f"    Density-artifact concern:          {density_artifact_concern}")


if __name__ == "__main__":
    main()
