"""Spike #33 — AoE direction dark-sector ring-down: local Class K signature test.

Three falsifiable sub-tests + synthetic substrate experiment.

Q1: direction-dependent Class K signature (synthetic experiment)
Q2: epsilon_AoE from 18.3 deg geometry (closed-form geometric inversion)
Q3: matter-drift vs medium-push consistency

Output: NDJSON records to D:/temp/spike_33/spike_33_findings_2026-05-16.ndjson

Discipline:
- Math-doesn't-lie: every number derived from closed form or numerical integration
- No commercial-data access; AoE direction (l,b) = (240, 60) from PR #437 working note
  citing Schwarz et al 2004 / Land-Magueijo 2005 (preserved as note-level cited values)
- NDJSON output per [[feedback_ndjson_over_bloated_json]]
- Strict three-criteria K-test reused verbatim from Spike #30B
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh

# ---------- canonical anchors (from prior spikes) ----------

# AoE pole direction (Schwarz et al 2004; Land-Magueijo 2005; cited in PR #437 working note)
AOE_L_DEG = 240.0
AOE_B_DEG = 60.0
# CMB dipole direction (Planck Collaboration; cited in PR #437 working note)
DIPOLE_L_DEG = 264.0
DIPOLE_B_DEG = 48.0
# Auger UHECR dipole direction (Pierre Auger 2017 arXiv:1709.07321; PR #437 Part VI)
UHECR_L_DEG = 100.0  # decoded from PR #437 separation tables: 73.3 deg from AoE pole at (240,60)
UHECR_B_DEG = -24.0  # decoded from PR #437 separation tables: 8 deg from HPA pole (226,-17)
# HPA pole (Hansen 2009; cited in PR #437)
HPA_L_DEG = 226.0
HPA_B_DEG = -17.0

# Saadeh et al 2016 isotropy bound (PRL 117, 131302) — verified prior, cited as discriminator anchor
# 121 sigma equivalent precision per AMSC catalog memory; bound on fractional anisotropy
SAADEH_ANISOTROPY_BOUND = 1.4e-5  # at 95% CL on rotational shear / quadrupole

# Saadeh-style upper bound on Bianchi quadrupole at large angular scale ≈ 10^-4
BIANCHI_QUAD_BOUND = 1e-4

# Strict K-criteria from Spike #30B (verbatim)
K_MIN_R2 = 0.99
K_EPS_LO = 0.001
K_EPS_HI = 0.5


def angular_separation_deg(l1: float, b1: float, l2: float, b2: float) -> float:
    """Great-circle separation on the celestial sphere in degrees (Galactic l, b)."""
    l1r, b1r, l2r, b2r = map(math.radians, (l1, b1, l2, b2))
    cos_d = math.sin(b1r) * math.sin(b2r) + math.cos(b1r) * math.cos(b2r) * math.cos(l1r - l2r)
    cos_d = max(-1.0, min(1.0, cos_d))
    return math.degrees(math.acos(cos_d))


# ---------- Class K strict criteria test (Spike #30B verbatim) ----------

def k_test_strict(signal_corrections: np.ndarray, M_grid: np.ndarray, max_k: int = 7) -> dict:
    """Strict three-criteria K-signature test.

    signal_corrections: phi(M) - M values at M_grid points
    Returns dict with r_squared, eps_fit, monotonic, in_range, present, coefs[]
    """
    # Fourier sin-series coefficients: c_k = (2/N) * sum signal[i] * sin(k * M[i])
    N = len(M_grid)
    coefs = []
    for k in range(1, max_k + 1):
        c_k = (2.0 / N) * np.sum(signal_corrections * np.sin(k * M_grid))
        coefs.append(abs(c_k))
    coefs = np.array(coefs)
    if np.all(coefs == 0):
        return dict(r_squared=0.0, eps_fit=0.0, monotonic=False, in_range=False, present=False, coefs=[0.0]*max_k)
    # Log-linear fit log|c_k| ~ k * log(eps) + const; using c_k = eps^k / k form gives
    # log|c_k * k| ~ k * log(eps), better recovery per Spike #30B anomaly resolution
    coef_k = coefs * np.arange(1, max_k + 1)
    nonzero_idx = coef_k > 1e-30
    if nonzero_idx.sum() < 3:
        return dict(r_squared=0.0, eps_fit=0.0, monotonic=False, in_range=False, present=False, coefs=coefs.tolist())
    log_coef_k = np.log(coef_k[nonzero_idx])
    k_arr = np.arange(1, max_k + 1)[nonzero_idx]
    # Linear regression
    A = np.vstack([k_arr, np.ones_like(k_arr)]).T
    slope, intercept = np.linalg.lstsq(A, log_coef_k, rcond=None)[0]
    eps_fit = math.exp(slope)
    pred = slope * k_arr + intercept
    ss_res = np.sum((log_coef_k - pred) ** 2)
    ss_tot = np.sum((log_coef_k - log_coef_k.mean()) ** 2)
    r2 = 1.0 - ss_res / max(ss_tot, 1e-30)
    monotonic = bool(np.all(np.diff(coefs) <= 0))
    in_range = bool(K_EPS_LO < eps_fit < K_EPS_HI)
    present = bool(r2 > K_MIN_R2 and monotonic and in_range)
    return dict(
        r_squared=float(r2),
        eps_fit=float(eps_fit),
        monotonic=monotonic,
        in_range=in_range,
        present=present,
        coefs=coefs.tolist(),
    )


# ---------- Q1: Synthetic axially-perturbed cascade substrate ----------

def build_ring_laplacian(N: int) -> np.ndarray:
    """Pure cyclic ring C_N — Class I substrate baseline."""
    L = np.zeros((N, N))
    for i in range(N):
        L[i, i] = 2.0
        L[i, (i + 1) % N] = -1.0
        L[i, (i - 1) % N] = -1.0
    return L


def build_axially_perturbed_ring(N: int, axis_node: int, eps: float, width: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """Ring substrate with smooth Gaussian perturbation localised near axis_node.

    Perturbation form: D_i = 2 + eps * exp(-((i - axis_node)^2) / (2 * width^2))
                       A_ij keep ring topology but offdiag weights scale by sqrt(D_i D_j)/2
    This models a 'fiber-perturbed' substrate where one direction has extra coupling
    (analog: AoE direction has enhanced local epicycle structure).
    """
    A = np.zeros((N, N))
    # Gaussian perturbation centred at axis_node (wrap-around)
    dist = np.minimum(
        np.abs(np.arange(N) - axis_node),
        N - np.abs(np.arange(N) - axis_node),
    )
    pert = eps * np.exp(-(dist ** 2) / (2.0 * width ** 2))
    for i in range(N):
        # ring topology with locally-perturbed edge weights
        w_fwd = 1.0 + 0.5 * (pert[i] + pert[(i + 1) % N])
        A[i, (i + 1) % N] = w_fwd
        A[(i + 1) % N, i] = w_fwd
    D = np.diag(A.sum(axis=1))
    L = D - A
    return L, pert


def project_eigenmode_to_direction(eigvec: np.ndarray, node_idx: int) -> float:
    """Projection of an eigenmode onto a specific node — the spectral analog of
    'directional contribution' (substrate-side reading of 'temperature anisotropy
    along that direction')."""
    return float(eigvec[node_idx])


def directional_residual_test(N: int = 256, axis_node: int = 64, eps: float = 0.05,
                              width: int = 8, n_directions: int = 16) -> dict:
    """Test: build axially-perturbed ring; compute per-direction residuals against
    pure-ring baseline; check if the perturbation-axis direction shows a Class K signature.

    Returns dict with per-direction K-test results.
    """
    # Build perturbed substrate
    L_pert, pert_profile = build_axially_perturbed_ring(N, axis_node, eps, width)
    L_base = build_ring_laplacian(N)
    # Eigendecompose
    eigvals_pert, eigvecs_pert = np.linalg.eigh(L_pert)
    eigvals_base, eigvecs_base = np.linalg.eigh(L_base)
    # For each "direction" (node index), compute the spectral residual:
    # the difference in mode-energy distribution at that node between perturbed and base
    n_modes = min(N, 64)  # use leading modes
    direction_nodes = np.round(np.linspace(0, N - 1, n_directions)).astype(int)
    results = []
    for d_node in direction_nodes:
        # Spectral density at node d_node (under perturbed Laplacian)
        # Modal weight at this node for each mode k: w_k = |<e_k, delta_d>|^2 * f(lambda_k)
        # where f is the "temperature window" — use heat-kernel weight at a fixed t
        t = 0.5
        weights_pert = (eigvecs_pert[d_node, :n_modes]) ** 2 * np.exp(-eigvals_pert[:n_modes] * t)
        weights_base = (eigvecs_base[d_node, :n_modes]) ** 2 * np.exp(-eigvals_base[:n_modes] * t)
        residual = weights_pert - weights_base
        # As a phase-angle observable: pack residuals into a phase-grid along the ring
        # and treat sin-series harmonics as K-signature candidates
        # The signal we test for K-shape: the directional "anomaly amplitude" as a
        # function of angle (M_grid = 2*pi*k/n_modes for mode k)
        M_grid = 2 * np.pi * np.arange(n_modes) / n_modes
        # Normalise residual to amplitude
        sig_max = max(abs(residual).max(), 1e-30)
        signal = residual / sig_max
        k_result = k_test_strict(signal, M_grid, max_k=7)
        # Distance from perturbation axis
        dist_from_axis = min(abs(d_node - axis_node), N - abs(d_node - axis_node))
        results.append({
            "direction_node": int(d_node),
            "dist_from_axis": int(dist_from_axis),
            "residual_amplitude": float(sig_max),
            "k_signature": k_result,
        })
    return {
        "N": N,
        "axis_node": axis_node,
        "eps": eps,
        "width": width,
        "perturbation_max": float(pert_profile.max()),
        "perturbation_min": float(pert_profile.min()),
        "n_directions": n_directions,
        "directions": results,
    }


# ---------- Q1 stronger test: directional f_RD time-trajectory ----------

def directional_fRD_trajectory(N: int = 256, axis_node: int = 64,
                               eps: float = 0.05, width: int = 8,
                               n_steps: int = 60) -> dict:
    """For each direction, compute the heat-kernel-integrated 'completion fraction'
    f_RD^direction(t) = 1 - <delta_d | exp(-L t) | delta_d>_norm and look for
    non-monotonic / sign-flip behaviour.
    """
    L_pert, _ = build_axially_perturbed_ring(N, axis_node, eps, width)
    eigvals, eigvecs = np.linalg.eigh(L_pert)
    t_grid = np.logspace(-2, 1, n_steps)
    n_dir = 16
    direction_nodes = np.round(np.linspace(0, N - 1, n_dir)).astype(int)
    # For each direction: f_RD^dir(t) computed as
    #   K_d(t) = sum_k |eigvecs[d,k]|^2 exp(-lambda_k t)
    #   f_RD^dir(t) = 1 - K_d(t)/K_d(0)
    trajectories = []
    for d_node in direction_nodes:
        c_dk2 = eigvecs[d_node, :] ** 2
        K_t = np.array([np.sum(c_dk2 * np.exp(-eigvals * t)) for t in t_grid])
        K0 = np.sum(c_dk2)
        f_RD = 1.0 - K_t / K0
        # f_RD slope (the "rate of completion")
        slope = np.gradient(f_RD, np.log(t_grid))
        # Check: any sign-flip in the slope? (indicates non-monotone trajectory)
        sign_flips = int(np.sum(np.diff(np.sign(slope[slope != 0])) != 0))
        # Local minimum / maximum count
        local_min = int(np.sum((slope[1:-1] < slope[:-2]) & (slope[1:-1] < slope[2:])))
        local_max = int(np.sum((slope[1:-1] > slope[:-2]) & (slope[1:-1] > slope[2:])))
        dist_from_axis = min(abs(d_node - axis_node), N - abs(d_node - axis_node))
        trajectories.append({
            "direction_node": int(d_node),
            "dist_from_axis": int(dist_from_axis),
            "f_RD_final": float(f_RD[-1]),
            "f_RD_max": float(f_RD.max()),
            "f_RD_argmax_t": float(t_grid[f_RD.argmax()]),
            "rate_sign_flips": sign_flips,
            "local_minima": local_min,
            "local_maxima": local_max,
            "non_monotone": bool(sign_flips > 0 or f_RD[-1] < f_RD.max() - 1e-6),
        })
    return {
        "N": N,
        "axis_node": axis_node,
        "eps": eps,
        "width": width,
        "n_directions": n_dir,
        "t_grid_lo": float(t_grid[0]),
        "t_grid_hi": float(t_grid[-1]),
        "trajectories": trajectories,
    }


# ---------- Q2: 18.3 deg epsilon_AoE inversion ----------

def eps_AoE_from_separation(separation_deg: float, max_k: int = 7) -> dict:
    """Multiple geometric inversions that map 18.3 deg AoE-dipole separation to
    an effective eccentricity eps_AoE.

    Three readings of the geometric relationship:

    Reading R1 (LEADING-EQUATION-OF-CENTRE):
      Pin-slot algebra at eccentricity e produces leading-amplitude
      c_1 = 2e (Brouwer-Clemence 1961 EOC series). If 18.3 deg
      is the leading angular displacement carried by the AoE-direction
      epicycle, then eps_AoE = sin(18.3 deg)/2.

    Reading R2 (HARMONIC PROJECTION):
      For mode-k harmonic with c_k = eps^k/k, the kth-harmonic angular
      projection is arctan(eps^k/k * sin(k * M)). At a specific harmonic
      that dominates the AoE alignment, the angular scale is set by
      arctan(eps_AoE^k / k). If we assume k=1 (fundamental epicycle),
      eps_AoE = tan(18.3 deg).

    Reading R3 (BUNDLE PROJECTION):
      If the AoE pole is the bundle base-direction and the dipole is a
      pull-direction, the angular separation is half-aperture of the
      pull-bundle cone (orthogonal Hopf-projection: angle subtended by
      a fibre over a point at distance d from the base direction).
      This gives eps_AoE = (1 - cos(18.3 deg)) ≈ 18.3 deg^2/2 in rad^2.
    """
    sep_rad = math.radians(separation_deg)
    # Reading R1
    eps_R1 = math.sin(sep_rad) / 2.0
    # Reading R2
    eps_R2 = math.tan(sep_rad)
    # Reading R3 (1 - cos)
    eps_R3 = 1.0 - math.cos(sep_rad)

    readings = []
    for tag, eps_val, formula in [
        ("R1_leading_EOC_c1_eq_2eps", eps_R1, "sin(18.3 deg) / 2"),
        ("R2_fundamental_arctan", eps_R2, "tan(18.3 deg)"),
        ("R3_bundle_aperture_1mc", eps_R3, "1 - cos(18.3 deg)"),
    ]:
        in_strict_K_range = K_EPS_LO < eps_val < K_EPS_HI
        readings.append({
            "tag": tag,
            "formula": formula,
            "eps_value": float(eps_val),
            "in_physical_K_range_0p001_0p5": in_strict_K_range,
            "in_cosmic_quadrupole_bound": eps_val < BIANCHI_QUAD_BOUND ** 0.5,  # since variance ~ eps^2
        })

    # Determine convergent reading
    in_range_count = sum(1 for r in readings if r["in_physical_K_range_0p001_0p5"])
    return {
        "separation_deg": separation_deg,
        "readings": readings,
        "n_readings_in_physical_K_range": in_range_count,
        "all_three_in_range": in_range_count == 3,
        "saadeh_isotropy_bound": SAADEH_ANISOTROPY_BOUND,
        "saadeh_bound_in_amplitude_units": math.sqrt(SAADEH_ANISOTROPY_BOUND),
    }


# ---------- Q3: matter-drift vs medium-push consistency ----------

def eps_from_matter_drift_reading(uhecr_offset_from_aoe_deg: float = 73.3,
                                  hpa_offset_from_aoe_deg: float = 77.8) -> dict:
    """Matter-drift reading: AoE-direction matter-density anomaly induces
    peculiar-velocity-flow toward AoE; observable signature is the
    deflection-of-UHECR-source-direction from isotropic expectation.

    If UHECR dipole is 73.3 deg from AoE, matter-drift reading predicts:
      eps_matter_drift = sin(angular_deflection)
    where the angular deflection is the AoE-induced velocity-flow correction.
    Per PR #437 Part VI Q14: UHECR direction is NOT on AoE — it's 73.3 deg
    away. So if matter-drift were happening at the AoE, the predicted
    UHECR-direction-deflection is the difference between observed UHECR
    direction and the AoE direction; the deflection magnitude depends on
    eps_matter_drift.

    Since AoE doesn't drift the UHECR dipole onto the AoE direction itself,
    the matter-drift reading at AoE-direction is constrained by:
      sin(73.3 deg) ~ sin(arctan(v_pec/c)) ~ v_pec/c at peculiar-velocity-scale.
    Local-volume v_pec / c ~ 1.23e-3 (CMB dipole velocity). So the
    'effective matter-drift eccentricity' that maps onto the observed
    UHECR direction is bounded by the lack of an AoE-aligned UHECR signal.

    Verdict: matter-drift reading at AoE direction is consistent with
      eps_matter_drift < (v_pec/c) / cos(73.3 deg) ~ 4.3e-3 (upper bound)
    """
    v_pec_over_c = 1.23e-3  # CMB dipole velocity
    # Upper bound: if matter-drift were producing any velocity-flow toward AoE
    # that's NOT visible in the UHECR direction, the angular factor cos(73.3 deg)
    # = 0.287 protects us — only the AoE-projection of any drift flow is bounded
    eps_matter_drift_upper = v_pec_over_c / max(math.cos(math.radians(uhecr_offset_from_aoe_deg)), 1e-6)
    eps_matter_drift_upper = min(eps_matter_drift_upper, 1.0)
    return {
        "uhecr_offset_from_aoe_deg": uhecr_offset_from_aoe_deg,
        "hpa_offset_from_aoe_deg": hpa_offset_from_aoe_deg,
        "v_pec_over_c": v_pec_over_c,
        "eps_matter_drift_upper_bound": float(eps_matter_drift_upper),
        "reasoning": "AoE direction has NO UHECR dipole alignment (Auger 2017 73.3 deg offset); "
                     "if matter-drift were producing velocity flow toward AoE, UHECR direction "
                     "should rotate toward AoE; it doesn't; matter-drift at AoE is bounded.",
    }


def eps_from_medium_push_reading(separation_deg: float = 18.3,
                                 uhecr_offset_from_aoe_deg: float = 73.3) -> dict:
    """Medium-push reading: AoE-direction is the substrate-bundle-base-direction
    along which the propagation medium (substrate cascade) ring-down rate is
    locally enhanced. Observable signature: anisotropy in propagation-time
    differential = substrate rate variation across the AoE direction.

    Per the local-epicycle reading: the substrate's Class K signature at the
    AoE direction has an eccentricity eps_medium_push such that the angular
    aperture of the substrate-bundle perturbation is set by
      half_aperture = arctan(eps_medium_push * f(harmonic_k))

    The 18.3 deg AoE-dipole separation, under medium-push reading, IS the
    eccentricity-induced aperture of the AoE-direction substrate-bundle.
    Per R2 reading above:
      eps_medium_push = tan(18.3 deg) = 0.331
    (this is the eps_AoE^(R2)).

    Cross-check: medium-push reading is consistent with UHECR observation
    if and only if substrate rate variation does NOT couple to matter-particle
    propagation enough to deflect UHECR sources. UHECR propagation at GZK-
    horizon scale traverses substrate over ~100 Mpc; if substrate rate
    variation is ~eps_medium_push at the AoE direction, the deflection on
    UHECR over 100 Mpc would be ~ (100 Mpc / observable_horizon) * eps =
    ~0.025 * 0.331 = 0.008 rad ~ 0.5 deg. Well below UHECR angular resolution
    (~10 deg). Verdict: medium-push reading SURVIVES the UHECR null result.
    """
    eps_medium_push = math.tan(math.radians(separation_deg))
    # UHECR deflection prediction at GZK horizon (~100 Mpc) vs observable horizon (~4 Gpc)
    deflection_estimate_deg = math.degrees((100.0 / 4000.0) * eps_medium_push)
    uhecr_resolution_deg = 10.0
    return {
        "separation_deg": separation_deg,
        "eps_medium_push": float(eps_medium_push),
        "uhecr_deflection_estimate_deg": float(deflection_estimate_deg),
        "uhecr_resolution_deg": uhecr_resolution_deg,
        "consistent_with_uhecr_null": deflection_estimate_deg < uhecr_resolution_deg,
        "reasoning": "Medium-push at AoE produces substrate rate variation; "
                     "UHECR over GZK horizon would deflect by "
                     f"~{deflection_estimate_deg:.2f} deg, well below Auger resolution. "
                     "Reading consistent with PR #437 Part VI Q14 result.",
    }


def matter_drift_vs_medium_push_consistency(separation_deg: float = 18.3,
                                            uhecr_offset_deg: float = 73.3) -> dict:
    """Q3: do matter-drift and medium-push readings give consistent eps_AoE?"""
    md = eps_from_matter_drift_reading(uhecr_offset_deg)
    mp = eps_from_medium_push_reading(separation_deg, uhecr_offset_deg)
    eps_md_upper = md["eps_matter_drift_upper_bound"]
    eps_mp = mp["eps_medium_push"]
    # Consistency: do these overlap?
    consistent = eps_mp <= eps_md_upper or abs(eps_mp - eps_md_upper) / max(eps_md_upper, 1e-6) < 0.2
    return {
        "matter_drift_eps_upper_bound": eps_md_upper,
        "medium_push_eps_central": eps_mp,
        "consistent_within_20pct": consistent,
        "ratio_mp_over_md_upper": float(eps_mp / max(eps_md_upper, 1e-6)),
        "verdict": ("CONSISTENT — both readings find AoE eccentricity in "
                    "overlapping range; partition-for-understanding survives at AoE.")
                   if consistent else
                   ("INCONSISTENT — matter-drift reading bounds eps far below "
                    "medium-push prediction; one reading has hidden assumption failure."),
    }


# ---------- emit findings as NDJSON ----------

def emit(records: list[dict], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")


def main() -> int:
    out_dir = Path("D:/temp/spike_33")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "spike_33_findings_2026-05-16.ndjson"

    records: list[dict] = []

    # Meta record
    records.append({
        "spike": 33,
        "kind": "meta",
        "date": "2026-05-16",
        "framing": "AoE direction local Class K signature — three falsifiable sub-tests",
        "phases": ["Q1_synthetic_substrate", "Q2_eps_from_18p3deg", "Q3_matter_vs_medium_consistency"],
    })

    # --- Q2 first (closed-form geometric inversion; cheap) ---
    q2 = eps_AoE_from_separation(18.3)
    records.append({"spike": 33, "kind": "Q2_eps_AoE_inversion", **q2})

    # --- Q3 ---
    q3 = matter_drift_vs_medium_push_consistency()
    records.append({"spike": 33, "kind": "Q3_matter_vs_medium_consistency", **q3})

    # --- Angular-separation discriminator anchors ---
    records.append({
        "spike": 33,
        "kind": "angular_anchors",
        "aoe_pole_galactic": [AOE_L_DEG, AOE_B_DEG],
        "cmb_dipole_galactic": [DIPOLE_L_DEG, DIPOLE_B_DEG],
        "uhecr_dipole_galactic_approx": [UHECR_L_DEG, UHECR_B_DEG],
        "hpa_pole_galactic": [HPA_L_DEG, HPA_B_DEG],
        "aoe_to_dipole_deg": angular_separation_deg(AOE_L_DEG, AOE_B_DEG, DIPOLE_L_DEG, DIPOLE_B_DEG),
        "aoe_to_uhecr_deg": angular_separation_deg(AOE_L_DEG, AOE_B_DEG, UHECR_L_DEG, UHECR_B_DEG),
        "aoe_to_hpa_deg": angular_separation_deg(AOE_L_DEG, AOE_B_DEG, HPA_L_DEG, HPA_B_DEG),
    })

    # --- Q1a: synthetic substrate experiment - directional spectral residual ---
    # Sweep over eps values to see how K-signature emerges with perturbation strength
    print("Q1a: directional spectral residual sweep")
    eps_sweep = [0.01, 0.05, 0.1, 0.2, 0.331, 0.5]
    for eps in eps_sweep:
        result = directional_residual_test(N=256, axis_node=64, eps=eps, width=8, n_directions=16)
        records.append({"spike": 33, "kind": "Q1a_directional_residual_sweep",
                       "eps_perturbation": eps, **result})

    # --- Q1b: directional f_RD trajectory — does the perturbed-axis direction show
    #         non-monotone signature? ---
    print("Q1b: directional f_RD trajectory")
    for eps in [0.05, 0.1, 0.2, 0.331]:
        result = directional_fRD_trajectory(N=256, axis_node=64, eps=eps, width=8, n_steps=60)
        records.append({"spike": 33, "kind": "Q1b_directional_fRD_trajectory",
                       "eps_perturbation": eps, **result})

    # --- Falsifier evaluations ---
    # F2 (load-bearing): does eps_AoE from 18.3 deg fall in physical eccentricity range?
    f2_pass = q2["all_three_in_range"]
    records.append({
        "spike": 33,
        "kind": "falsifier_F2",
        "description": "eps_AoE from 18.3 deg in physical K-range (0.001, 0.5)",
        "pass": f2_pass,
        "verdict": "All three readings fall in physical K-range." if f2_pass else
                  "Not all three readings in physical K-range.",
    })

    # F3 (load-bearing): matter-drift vs medium-push reading consistent eps_AoE?
    f3_consistent = q3["consistent_within_20pct"]
    records.append({
        "spike": 33,
        "kind": "falsifier_F3",
        "description": "Matter-drift and medium-push readings give consistent eps_AoE",
        "pass": f3_consistent,
        "verdict": q3["verdict"],
    })

    # Anti-falsifier A2: physical eccentricity (0.01 < eps_AoE < 0.1)?
    eps_central = q2["readings"][2]["eps_value"]  # R3 reading
    eps_R1 = q2["readings"][0]["eps_value"]
    eps_R2 = q2["readings"][1]["eps_value"]
    a2_pass = K_EPS_LO * 10 < eps_R1 < 0.1
    records.append({
        "spike": 33,
        "kind": "antifalsifier_A2",
        "description": "eps_AoE in standard-cosmology eccentricity range (0.01 < eps < 0.1)",
        "eps_R1_leading_EOC": eps_R1,
        "eps_R2_fundamental_arctan": eps_R2,
        "eps_R3_bundle_aperture": eps_central,
        "pass": a2_pass,
        "verdict": "R1 reading (sin/2) gives physical eccentricity in standard range." if a2_pass else
                  "Eccentricity outside standard range; reading specifics matter.",
    })

    emit(records, out_path)
    print(f"\nNDJSON written: {out_path}")
    print(f"Records: {len(records)}")

    # Print key numbers
    print("\n--- Key numbers ---")
    print(f"Q2 R1 eps_AoE = sin(18.3 deg)/2 = {eps_R1:.6f}")
    print(f"Q2 R2 eps_AoE = tan(18.3 deg) = {eps_R2:.6f}")
    print(f"Q2 R3 eps_AoE = 1-cos(18.3 deg) = {eps_central:.6f}")
    print(f"Q2 readings in physical K-range: {q2['n_readings_in_physical_K_range']}/3")
    print(f"Q3 verdict: {q3['verdict']}")
    print(f"F2 (eps_AoE in physical K-range): {'PASS' if f2_pass else 'FAIL'}")
    print(f"F3 (matter-drift vs medium-push consistent): {'CONSISTENT' if f3_consistent else 'INCONSISTENT'}")
    print(f"A2 (eps_R1 in 0.01-0.1 standard range): {'PASS' if a2_pass else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
