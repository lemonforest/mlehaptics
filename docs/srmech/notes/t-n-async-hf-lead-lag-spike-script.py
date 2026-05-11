"""
T^N quantum-walk lift vs Hayashi-Yoshida — asynchronous high-frequency lead-lag spike.

Spike load-bearing question: does the T^N quantum-walk lift U(t) = exp(-i L_corr t)
on a correlation Laplacian recover asynchronous lead-lag relationships at
competitive accuracy with the Hayashi-Yoshida (2005) estimator on synthetic
async-sampled price series with KNOWN lead-lag structure?

Honest framing: this is the financial-scoping (2026-05-11) round's most novel
claim into finance (finding #7). The Fiedler-vs-HRP spike confirmed Fiedler
beats HRP on STATIC clustering but did NOT exercise this setting (uniform
initial state was eigenvector of the trivial lambda=0 eigenvalue; evolution
barely perturbed). This dispatch tests T^N at its INTENDED load-bearing
setting: async-HF lead-lag estimation, NOT static clustering.

Honest verdict required:
- If T^N lift recovers lag at competitive accuracy with Hayashi-Yoshida ->
  first project -> external new-information win.
- If T^N lift underperforms -> the financial round's most-novel claim falls;
  honest data, not papered over.

MPM discipline: closed-form numerical linear algebra (numpy / scipy); no SGD;
no test-set tuning; deterministic seed; reproducible end-to-end. NDJSON output.

References:
- Hayashi & Yoshida (2005) "On covariance estimation of non-synchronously
  observed diffusion processes," Bernoulli 11(2): 359-379.
  https://arxiv.org/abs/1111.7103 (later survey)
- srmech notebook S3.5.1 layer (b): eigenphase torus T^n, U(t) = exp(-i L t)
- financial-scoping-2026-05-11.md finding #7 (T^N quantum-walk lift)
- fiedler-vs-hrp-vs-gics-spike-2026-05-11.md sub-investigation 5 anomaly 3
  (uniform initial state was the wrong proving ground for the lift)

Author: concertmaster role, 2026-05-11.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.linalg import eigh
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Reproducibility and constants (SSOT)
# ---------------------------------------------------------------------------

SEED = 20260511  # 2026-05-11; deterministic across runs

# Synthetic async-HF price series parameters
N_ASSETS = 6                       # leader + 5 followers
LAG_SCHEDULE = [0, 1, 2, 3, 5, 10] # leader=0, followers at increasing lag
T_HORIZON = 5000.0                 # time horizon (arbitrary units)
SAMPLING_INTENSITY = 1.0           # mean inter-arrival ~ 1.0 unit
DRIFT = 0.0                        # GBM drift (per unit time)
VOL = 0.01                         # GBM volatility (per unit time)
FOLLOWER_NOISE_STD = 0.005         # i.i.d. additive noise on followers

# Multi-trial bootstrap
N_TRIALS = 20

# T^N evolution time sweep
TN_TIMES = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]

# Hayashi-Yoshida lag-search range (in time-grid units)
HY_LAG_MAX = 15

# Output paths
OUTPUT_DIR = Path(r"D:\GitHub\mlehaptics\docs\srmech\notes")
NDJSON_PATH = OUTPUT_DIR / "t-n-async-hf-lead-lag-spike-per-metric-2026-05-11.ndjson"

# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------


def simulate_leader_path(
    rng: np.random.Generator,
    horizon: float,
    drift: float,
    vol: float,
    fine_dt: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Discrete GBM leader path on a fine reference grid.

    Returns (times, log-prices).
    """
    n_fine = int(horizon / fine_dt) + 1
    times = np.arange(n_fine) * fine_dt
    increments = rng.standard_normal(n_fine - 1) * vol * np.sqrt(fine_dt)
    log_prices = np.zeros(n_fine)
    log_prices[1:] = np.cumsum(increments + drift * fine_dt)
    return times, log_prices


def make_followers(
    leader_times: np.ndarray,
    leader_log_prices: np.ndarray,
    lag_schedule: List[float],
    follower_noise_std: float,
    rng: np.random.Generator,
) -> List[np.ndarray]:
    """
    Build follower log-price paths as lagged copies of the leader + noise.

    For each lag tau in lag_schedule, interpolate the leader to (t - tau) and
    add independent Gaussian noise. lag=0 means coincident with leader.

    Returns: list of (n_fine,) arrays, one per asset.
    """
    paths = []
    for tau in lag_schedule:
        # Asset value at time t = leader value at time (t - tau)
        # Use linear interpolation on the leader's fine grid
        shifted_times = leader_times - tau
        # np.interp: for t < tau, extrapolate by holding leader[0]
        interp = np.interp(
            shifted_times, leader_times, leader_log_prices,
            left=leader_log_prices[0], right=leader_log_prices[-1],
        )
        noise = rng.standard_normal(len(interp)) * follower_noise_std
        paths.append(interp + noise)
    return paths


def async_sample_paths(
    fine_times: np.ndarray,
    fine_log_prices_list: List[np.ndarray],
    intensity: float,
    horizon: float,
    rng: np.random.Generator,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Asynchronously sample each path via independent Poisson arrival times.

    For each asset, draw arrival times from a homogeneous Poisson process on
    [0, horizon] with rate `intensity`. Interpolate the asset's fine-grid path
    to those arrival times. Returns list of (times_i, prices_i) per asset.
    """
    sampled = []
    for log_prices in fine_log_prices_list:
        # Poisson arrival times via cumulative exponential gaps
        gaps = rng.exponential(scale=1.0 / intensity, size=int(horizon * intensity * 2))
        arrival = np.cumsum(gaps)
        arrival = arrival[arrival < horizon]
        # Interpolate fine-grid path to arrival times
        prices_at_arrival = np.interp(arrival, fine_times, log_prices)
        sampled.append((arrival, prices_at_arrival))
    return sampled


# ---------------------------------------------------------------------------
# Hayashi-Yoshida 2005 lag estimator
# ---------------------------------------------------------------------------


def hayashi_yoshida_lagged_cov_vectorized(
    intervals_i_start: np.ndarray, intervals_i_end: np.ndarray, dp_i: np.ndarray,
    intervals_j_start: np.ndarray, intervals_j_end: np.ndarray, dp_j: np.ndarray,
    lag: float,
) -> float:
    """
    Vectorized HY covariance at a fixed lag.

    HY 2005: cov estimator pairs return increments dp_i(I_a) and dp_j(J_b)
    iff the intervals I_a and SHIFTED J_b = (s_j[b] + lag, e_j[b] + lag]
    overlap. Sum the products.

    For each i-interval a, the overlapping j-intervals form a contiguous
    range [lo_a, hi_a). We compute lo_a, hi_a vectorized via searchsorted.
    Then HY_cov(lag) = sum_a dp_i[a] * (sum of dp_j over [lo_a, hi_a)).

    The inner sum is computed via a precomputed cumulative-sum on dp_j:
    sum_dp_j_range(lo, hi) = cumsum_dp_j[hi] - cumsum_dp_j[lo].

    O(N_i log N_j) per call, fully vectorized.
    """
    s_j_lag = intervals_j_start + lag
    e_j_lag = intervals_j_end + lag

    # For each i interval, find range of j intervals overlapping
    # Overlap iff s_j_lag < e_i AND e_j_lag > s_i
    # On sorted j: lo_a = first index where e_j_lag > s_i[a]
    #              hi_a = first index where s_j_lag >= e_i[a]
    lo_arr = np.searchsorted(e_j_lag, intervals_i_start, side="right")
    hi_arr = np.searchsorted(s_j_lag, intervals_i_end, side="left")

    # Sum dp_j over [lo, hi) per i interval via cumulative sum
    cumsum_dp_j = np.concatenate([[0.0], np.cumsum(dp_j)])
    j_increment_sums = cumsum_dp_j[hi_arr] - cumsum_dp_j[lo_arr]

    # Total covariance
    return float(np.dot(dp_i, j_increment_sums))


def hayashi_yoshida_estimate_lag(
    times_i: np.ndarray, prices_i: np.ndarray,
    times_j: np.ndarray, prices_j: np.ndarray,
    lag_grid: np.ndarray,
) -> Tuple[float, np.ndarray]:
    """
    Estimate the lag between assets i and j by maximising HY covariance.

    Searches over the lag grid; returns the argmax and the full cov-vs-lag
    array. Sign convention: positive estimated lag means asset i leads asset
    j (j is delayed).
    """
    if len(times_i) < 2 or len(times_j) < 2:
        return 0.0, np.zeros_like(lag_grid)
    intervals_i_start = times_i[:-1]
    intervals_i_end = times_i[1:]
    intervals_j_start = times_j[:-1]
    intervals_j_end = times_j[1:]
    dp_i = np.diff(prices_i)
    dp_j = np.diff(prices_j)
    covs = np.array([
        hayashi_yoshida_lagged_cov_vectorized(
            intervals_i_start, intervals_i_end, dp_i,
            intervals_j_start, intervals_j_end, dp_j,
            lg,
        )
        for lg in lag_grid
    ])
    # Asset i leads j when, after lag `lg`, the SHIFTED j (j observed at time
    # t corresponds to leader value at t - lg) aligns with i. If i leads by
    # tau, then i's series at time t equals j's series at time (t + tau)
    # (since j is delayed). So the max covariance occurs when lag = -tau in
    # the original HY convention. Convert: tau_ij = -argmax_lag.
    argmax_lag = lag_grid[np.argmax(covs)]
    tau_ij = -float(argmax_lag)
    return tau_ij, covs


# ---------------------------------------------------------------------------
# Correlation matrix construction
# ---------------------------------------------------------------------------


def common_grid_returns(
    sampled_paths: List[Tuple[np.ndarray, np.ndarray]],
    grid_dt: float = 1.0,
    horizon: float = T_HORIZON,
) -> np.ndarray:
    """
    Project asynchronously-sampled paths to a common grid via last-observation
    carry-forward, then take return increments. This is the canonical "previous
    tick" alignment in HF microstructure. Returns shape: (n_grid, n_assets).

    Microstructure caveat: previous-tick interpolation introduces "Epps effect"
    bias that depresses correlations at fine grids. We use a coarse grid
    (dt=1.0 unit) to mitigate.
    """
    n_grid = int(horizon / grid_dt) + 1
    grid_times = np.arange(n_grid) * grid_dt
    aligned = np.zeros((n_grid, len(sampled_paths)))
    for i, (t_i, p_i) in enumerate(sampled_paths):
        # Find last sample at or before each grid time
        idx = np.searchsorted(t_i, grid_times, side="right") - 1
        idx = np.clip(idx, 0, len(p_i) - 1)
        aligned[:, i] = p_i[idx]
    # Return increments
    returns = np.diff(aligned, axis=0)
    return returns


def real_correlation_matrix(returns: np.ndarray) -> np.ndarray:
    """Pearson correlation matrix from grid-aligned returns. Real-valued."""
    # numpy corrcoef does the right thing
    C = np.corrcoef(returns.T)
    # Symmetrize against round-off
    C = 0.5 * (C + C.T)
    np.fill_diagonal(C, 1.0)
    return C


def complex_correlation_matrix_via_cross_spectrum(
    returns: np.ndarray,
    band_low: float = 0.01,
    band_high: float = 0.5,
) -> Tuple[np.ndarray, float]:
    """
    Complex correlation matrix from cross-spectral density (Welch-style),
    averaged over a frequency band.

    The cross-spectrum S_ij(omega) = FFT(r_i) * conj(FFT(r_j)) per frequency,
    normalized by sqrt(S_ii * S_jj). The argument arg(S_ij) encodes phase
    (lead-lag info at that frequency). We band-average to get a stable
    complex C_ij.

    This is the natural complex extension of the real correlation: |C_ij| ~ rho_ij
    and arg(C_ij) ~ lead-lag phase. Standard finance preserves only |C_ij|;
    we preserve both for the T^N lift.

    Returns: (complex_C, dominant_omega) where dominant_omega is the band-
    midpoint used for phase->lag conversion.
    """
    n_grid, n_assets = returns.shape
    # Demean
    R = returns - returns.mean(axis=0, keepdims=True)
    # FFT each asset's return series
    FT = np.fft.rfft(R, axis=0)
    freqs = np.fft.rfftfreq(n_grid, d=1.0)  # frequency in cycles/unit-time

    # Pick band
    band_mask = (freqs >= band_low) & (freqs <= band_high)
    if band_mask.sum() < 1:
        # Fallback: use all positive frequencies
        band_mask = freqs > 0

    # Per-frequency cross-spectrum
    # S_ij(omega) = FT_i * conj(FT_j); shape (n_freq, n_assets, n_assets)
    # To avoid the full tensor, build it via outer product per freq
    FT_band = FT[band_mask]  # shape (n_band, n_assets)

    # Auto-spectra |FT_i|^2 per freq
    S_auto = np.abs(FT_band) ** 2  # (n_band, n_assets)

    # Average power (for normalization)
    auto_mean = S_auto.mean(axis=0)  # (n_assets,)

    # Cross-spectrum averaged over band
    # S_ij_avg = mean_omega [FT_i(omega) * conj(FT_j(omega))]
    # Using einsum for clarity
    S_cross = np.einsum("ki,kj->ij", FT_band, np.conj(FT_band)) / band_mask.sum()

    # Normalize: C_ij = S_ij_avg / sqrt(S_ii_avg * S_jj_avg)
    norm = np.sqrt(np.outer(auto_mean, auto_mean))
    C_complex = S_cross / (norm + 1e-12)

    # Force diagonal to 1+0i
    np.fill_diagonal(C_complex, 1.0 + 0.0j)
    # The matrix is Hermitian by construction
    C_complex = 0.5 * (C_complex + C_complex.conj().T)

    dominant_omega = float(freqs[band_mask].mean())
    return C_complex, dominant_omega


# ---------------------------------------------------------------------------
# T^N quantum-walk lift on correlation Laplacian
# ---------------------------------------------------------------------------


def build_real_correlation_laplacian(C_real: np.ndarray) -> np.ndarray:
    """
    Real-valued correlation Laplacian L = D - A where A = |C| (magnitude only).

    This is the same construction as the Fiedler spike but expressed as
    combinatorial Laplacian (not normalized). For the T^N lift, the
    eigenstructure matters; either form admits the lift.

    Returns symmetric positive-semidefinite real matrix.
    """
    n = C_real.shape[0]
    A = np.abs(C_real)
    np.fill_diagonal(A, 0.0)
    D = np.diag(A.sum(axis=1))
    L = D - A
    L = 0.5 * (L + L.T)
    return L


def build_complex_correlation_laplacian(C_complex: np.ndarray) -> np.ndarray:
    """
    Complex/Hermitian correlation Laplacian L_H = D - A where A = C_complex,
    with the off-diagonals preserving phase. The diagonal of D is real
    (D_ii = sum_j |A_ij|).

    Properties: L_H is Hermitian (since C is Hermitian) -> real eigenvalues,
    complex unitary eigenvectors. exp(-i L_H t) is unitary; the resulting
    propagator has complex off-diagonals encoding phase evolution.

    This is the project-canonical phase-preserving Laplacian for the T^N lift
    on a complex correlation graph (srmech S3.5.1 layer (b)).
    """
    n = C_complex.shape[0]
    A = C_complex.copy()
    np.fill_diagonal(A, 0.0)
    # D from row-sums of |A| (so D real, positive)
    D_diag = np.abs(A).sum(axis=1)
    D = np.diag(D_diag)
    L_H = D - A
    # Force Hermitian (against round-off)
    L_H = 0.5 * (L_H + L_H.conj().T)
    return L_H


def tn_lift_extract_lag(
    L_real: np.ndarray,
    L_complex: np.ndarray,
    t: float,
    omega_band: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the T^N quantum-walk propagator U(t) = exp(-i L t) on both the
    real Laplacian (control) and the complex Laplacian (load-bearing), and
    extract per-pair lag estimates from the propagator's argument.

    Two lag estimation strategies:
    1. From off-diagonal arguments: tau_ij_complex = -arg(U(t)[i,j]) / omega_band
       (interpretation: a positive lag means i leads j; arg(U[i,j]) is the
       phase j picks up under unit-impulse at i evolved by time t at the
       dominant frequency omega_band).
    2. From off-diagonal arguments on real-L control: should be near zero
       (real L has real-symmetric eigendecomposition; U is symmetric complex
       but with arguments solely from eigenvalue phases, NOT carrying lag info
       because the eigenvectors are real).

    Returns (tau_real_control, tau_complex_lift), each NxN matrix.
    """
    n = L_real.shape[0]
    # Real Laplacian: eigenvectors are real, eigenvalues are real positive
    eigvals_real, eigvecs_real = eigh(L_real)
    phase_factors_real = np.exp(-1j * eigvals_real * t)
    U_real = eigvecs_real @ np.diag(phase_factors_real) @ eigvecs_real.T
    # Note: U_real is complex but its symmetry is preserved (U_real == U_real.T)

    # Complex Laplacian: Hermitian, so eigvecs are complex unitary
    eigvals_c, eigvecs_c = eigh(L_complex)
    phase_factors_c = np.exp(-1j * eigvals_c * t)
    U_complex = eigvecs_c @ np.diag(phase_factors_c) @ eigvecs_c.conj().T

    # Extract pairwise relative phase
    # arg(U[i, j]) ~ -omega_dom * tau_ij at the leading order
    # => tau_ij = -arg(U[i, j]) / omega_dom
    # Asymmetric matrix: tau_ij is the lead of i over j
    arg_U_real = np.angle(U_real)
    arg_U_complex = np.angle(U_complex)
    tau_real_control = -arg_U_real / (omega_band + 1e-12)
    tau_complex_lift = -arg_U_complex / (omega_band + 1e-12)

    return tau_real_control, tau_complex_lift


# ---------------------------------------------------------------------------
# Comparison metrics
# ---------------------------------------------------------------------------


def lag_matrix_metrics(
    L_est: np.ndarray, L_true: np.ndarray,
) -> Dict[str, float]:
    """
    Compute MAE, Spearman rho, sign accuracy of estimated lag matrix vs ground
    truth, over off-diagonal pairs (each ordered pair counted once).

    Returns dict with keys mae, spearman_rho, spearman_p, sign_accuracy,
    n_pairs.
    """
    n = L_est.shape[0]
    iu = np.triu_indices(n, k=1)
    est = L_est[iu]
    true = L_true[iu]
    mae = float(np.mean(np.abs(est - true)))
    if np.std(est) > 1e-9 and np.std(true) > 1e-9:
        rho, p = spearmanr(est, true)
    else:
        rho, p = float("nan"), float("nan")
    # Sign accuracy: fraction where sign matches (excluding pairs where one
    # side is exactly 0, which is degenerate)
    nonzero_mask = (true != 0)
    if nonzero_mask.sum() > 0:
        sa = float(np.mean(np.sign(est[nonzero_mask]) == np.sign(true[nonzero_mask])))
    else:
        sa = float("nan")
    return {
        "mae": mae,
        "spearman_rho": float(rho) if not np.isnan(rho) else float("nan"),
        "spearman_p": float(p) if not np.isnan(p) else float("nan"),
        "sign_accuracy": sa,
        "n_pairs": int(len(est)),
    }


# ---------------------------------------------------------------------------
# Ground-truth lag matrix
# ---------------------------------------------------------------------------


def build_ground_truth_lag_matrix(lag_schedule: List[float]) -> np.ndarray:
    """
    L_true[i, j] = tau_i - tau_j (positive means i is delayed less than j,
    i.e., i leads j by tau_j - tau_i units).

    With our sign convention (tau_ij > 0 iff i leads j), we have:
        L_true[i, j] = lag_schedule[j] - lag_schedule[i]
    So if i is at lag 0 (leader) and j is at lag 3, then L_true[i, j] = +3 > 0
    (i leads j by 3 units, correct).
    """
    n = len(lag_schedule)
    L = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            L[i, j] = lag_schedule[j] - lag_schedule[i]
    return L


# ---------------------------------------------------------------------------
# Single-trial spike
# ---------------------------------------------------------------------------


@dataclass
class TrialResult:
    trial: int
    hy_metrics: Dict[str, float]
    tn_real_control_metrics_by_t: Dict[float, Dict[str, float]]
    tn_complex_lift_metrics_by_t: Dict[float, Dict[str, float]]
    omega_band: float


def run_single_trial(trial_idx: int, rng: np.random.Generator) -> TrialResult:
    """One simulation + estimation cycle."""
    # 1. Simulate leader path
    fine_times, leader_log_prices = simulate_leader_path(
        rng, T_HORIZON, DRIFT, VOL,
    )

    # 2. Build follower paths
    follower_paths = make_followers(
        fine_times, leader_log_prices, LAG_SCHEDULE, FOLLOWER_NOISE_STD, rng,
    )

    # 3. Async-sample each path
    sampled = async_sample_paths(
        fine_times, follower_paths, SAMPLING_INTENSITY, T_HORIZON, rng,
    )

    # 4. Ground truth
    L_true = build_ground_truth_lag_matrix(LAG_SCHEDULE)

    # 5. Hayashi-Yoshida lag estimation per pair
    lag_grid = np.arange(-HY_LAG_MAX, HY_LAG_MAX + 1, 1.0)
    L_hy = np.zeros((N_ASSETS, N_ASSETS))
    for i in range(N_ASSETS):
        for j in range(N_ASSETS):
            if i == j:
                continue
            t_i, p_i = sampled[i]
            t_j, p_j = sampled[j]
            tau_ij, _ = hayashi_yoshida_estimate_lag(t_i, p_i, t_j, p_j, lag_grid)
            L_hy[i, j] = tau_ij

    hy_metrics = lag_matrix_metrics(L_hy, L_true)

    # 6. Build correlation matrices for T^N lift
    returns = common_grid_returns(sampled, grid_dt=1.0, horizon=T_HORIZON)
    C_real = real_correlation_matrix(returns)
    C_complex, omega_band = complex_correlation_matrix_via_cross_spectrum(
        returns, band_low=0.01, band_high=0.5,
    )

    L_real = build_real_correlation_laplacian(C_real)
    L_complex = build_complex_correlation_laplacian(C_complex)

    # 7. T^N lift at various evolution times
    tn_real_metrics_by_t: Dict[float, Dict[str, float]] = {}
    tn_complex_metrics_by_t: Dict[float, Dict[str, float]] = {}
    for t in TN_TIMES:
        tau_real, tau_complex = tn_lift_extract_lag(L_real, L_complex, t, omega_band)
        tn_real_metrics_by_t[t] = lag_matrix_metrics(tau_real, L_true)
        tn_complex_metrics_by_t[t] = lag_matrix_metrics(tau_complex, L_true)

    return TrialResult(
        trial=trial_idx,
        hy_metrics=hy_metrics,
        tn_real_control_metrics_by_t=tn_real_metrics_by_t,
        tn_complex_lift_metrics_by_t=tn_complex_metrics_by_t,
        omega_band=omega_band,
    )


# ---------------------------------------------------------------------------
# Anomaly chase: initial-state choice
# ---------------------------------------------------------------------------


def anomaly_initial_state_choice(rng: np.random.Generator) -> List[Dict]:
    """
    Per fiedler-vs-hrp-vs-gics-spike-2026-05-11.md anomaly 3: uniform initial
    state ψ_0 = 1/√N is eigenvector of trivial λ=0 eigenvalue, so U(t) ψ_0 ≈ ψ_0.
    Test three initial state choices on the complex Laplacian propagator and
    see which (if any) recovers lag.
    """
    rng_local = np.random.default_rng(SEED + 999)
    # Generate one trial's data
    fine_times, leader_log_prices = simulate_leader_path(
        rng_local, T_HORIZON, DRIFT, VOL,
    )
    follower_paths = make_followers(
        fine_times, leader_log_prices, LAG_SCHEDULE, FOLLOWER_NOISE_STD, rng_local,
    )
    sampled = async_sample_paths(
        fine_times, follower_paths, SAMPLING_INTENSITY, T_HORIZON, rng_local,
    )
    L_true = build_ground_truth_lag_matrix(LAG_SCHEDULE)
    returns = common_grid_returns(sampled, grid_dt=1.0, horizon=T_HORIZON)
    C_complex, omega_band = complex_correlation_matrix_via_cross_spectrum(returns)
    L_complex = build_complex_correlation_laplacian(C_complex)
    eigvals, eigvecs = eigh(L_complex)

    records: List[Dict] = []
    t_test = 1.0
    phase_factors = np.exp(-1j * eigvals * t_test)
    U_t = eigvecs @ np.diag(phase_factors) @ eigvecs.conj().T

    # Initial state 1: uniform (the original failure mode)
    psi_uniform = np.ones(N_ASSETS, dtype=complex) / np.sqrt(N_ASSETS)
    psi_t_uniform = U_t @ psi_uniform
    # Lag estimate: arg(psi_t[j]) - arg(psi_t[i]) -> tau_ij
    arg_diff_uniform = np.angle(psi_t_uniform)[None, :] - np.angle(psi_t_uniform)[:, None]
    tau_uniform = -arg_diff_uniform / (omega_band + 1e-12)
    m_uniform = lag_matrix_metrics(tau_uniform, L_true)
    records.append({
        "anomaly_chase": "initial_state_choice",
        "initial_state": "uniform",
        "metrics": m_uniform,
        "circular_phase_variance": float(np.var(np.angle(psi_t_uniform))),
    })

    # Initial state 2: per-asset impulses, use U(t) directly (asymmetric)
    # This is the principled choice: U(t)[i, j] = <e_i| U(t) |e_j>
    # arg(U[i, j]) encodes the phase i picks up when impulse starts at j
    arg_U = np.angle(U_t)
    tau_from_U = -arg_U / (omega_band + 1e-12)
    m_from_U = lag_matrix_metrics(tau_from_U, L_true)
    records.append({
        "anomaly_chase": "initial_state_choice",
        "initial_state": "per_asset_impulses_via_U",
        "metrics": m_from_U,
    })

    # Initial state 3: random unit-norm complex state with seed
    rng_rs = np.random.default_rng(SEED + 1)
    z = rng_rs.standard_normal(N_ASSETS) + 1j * rng_rs.standard_normal(N_ASSETS)
    z = z / np.linalg.norm(z)
    psi_t_rand = U_t @ z
    arg_diff_rand = np.angle(psi_t_rand)[None, :] - np.angle(psi_t_rand)[:, None]
    tau_rand = -arg_diff_rand / (omega_band + 1e-12)
    m_rand = lag_matrix_metrics(tau_rand, L_true)
    records.append({
        "anomaly_chase": "initial_state_choice",
        "initial_state": "random_unit_norm_complex",
        "metrics": m_rand,
    })

    return records


def anomaly_omega_band_sensitivity(rng: np.random.Generator) -> List[Dict]:
    """
    Test sensitivity of the complex-correlation lift to the frequency band
    used for cross-spectrum averaging. Narrow vs wide; low vs high.
    """
    rng_local = np.random.default_rng(SEED + 1000)
    fine_times, leader_log_prices = simulate_leader_path(
        rng_local, T_HORIZON, DRIFT, VOL,
    )
    follower_paths = make_followers(
        fine_times, leader_log_prices, LAG_SCHEDULE, FOLLOWER_NOISE_STD, rng_local,
    )
    sampled = async_sample_paths(
        fine_times, follower_paths, SAMPLING_INTENSITY, T_HORIZON, rng_local,
    )
    L_true = build_ground_truth_lag_matrix(LAG_SCHEDULE)
    returns = common_grid_returns(sampled, grid_dt=1.0, horizon=T_HORIZON)

    records: List[Dict] = []
    bands = [
        (0.005, 0.05, "very_low"),
        (0.01, 0.10, "low"),
        (0.01, 0.50, "wide_default"),
        (0.05, 0.20, "mid"),
        (0.10, 0.50, "high"),
    ]
    for blo, bhi, name in bands:
        C_complex, omega_band = complex_correlation_matrix_via_cross_spectrum(
            returns, band_low=blo, band_high=bhi,
        )
        L_complex = build_complex_correlation_laplacian(C_complex)
        eigvals, eigvecs = eigh(L_complex)
        # Use t = 1.0 / omega_band so omega * t ~ 1 (natural scale)
        t_natural = 1.0 / (omega_band + 1e-12)
        # Cap at TN_TIMES range to avoid wraparound
        t_test = min(t_natural, 5.0)
        phase_factors = np.exp(-1j * eigvals * t_test)
        U_t = eigvecs @ np.diag(phase_factors) @ eigvecs.conj().T
        arg_U = np.angle(U_t)
        tau_est = -arg_U / (omega_band + 1e-12)
        m = lag_matrix_metrics(tau_est, L_true)
        records.append({
            "anomaly_chase": "omega_band_sensitivity",
            "band_name": name,
            "band_low": blo,
            "band_high": bhi,
            "omega_band_midpoint": omega_band,
            "t_test": t_test,
            "metrics": m,
        })
    return records


def anomaly_direct_cross_spectrum_phase(rng: np.random.Generator) -> List[Dict]:
    """
    Counter-experiment: DIRECT pairwise cross-spectrum phase lag estimation.

    Skip the Laplacian / T^N propagator entirely. Compute the
    cross-spectrum S_ij(omega) directly per asset pair, take arg(S_ij(omega))
    at a dominant frequency, and convert to lag via tau_ij = -arg / omega.

    This is the natural Welch-coherence finance baseline. If THIS recovers
    lag well, the failure of T^N is in the Laplacian-aggregation step (which
    mixes pair phases via the L_H eigenstructure), NOT in cross-spectrum
    phase per se. This pinpoints where the lift loses information.

    Per srmech S3.5.1 layer (b), the project's claim is that the T^N lift
    UNIFIES Welch coherence + Hayashi-Yoshida + Onnela dynamic asset trees
    on the same eigenbasis. If direct cross-spectrum phase works but the
    L_H-propagator doesn't, the unification claim is the failure mode.
    """
    rng_local = np.random.default_rng(SEED + 2000)
    fine_times, leader_log_prices = simulate_leader_path(
        rng_local, T_HORIZON, DRIFT, VOL,
    )
    follower_paths = make_followers(
        fine_times, leader_log_prices, LAG_SCHEDULE, FOLLOWER_NOISE_STD, rng_local,
    )
    sampled = async_sample_paths(
        fine_times, follower_paths, SAMPLING_INTENSITY, T_HORIZON, rng_local,
    )
    L_true = build_ground_truth_lag_matrix(LAG_SCHEDULE)
    returns = common_grid_returns(sampled, grid_dt=1.0, horizon=T_HORIZON)

    records: List[Dict] = []
    n = N_ASSETS
    n_grid = returns.shape[0]
    R = returns - returns.mean(axis=0, keepdims=True)
    FT = np.fft.rfft(R, axis=0)
    freqs = np.fft.rfftfreq(n_grid, d=1.0)

    # Try several single-frequency choices
    test_omegas = [0.02, 0.05, 0.10, 0.20, 0.30, 0.40]
    for omega_target in test_omegas:
        # Find the closest frequency bin
        idx = int(np.argmin(np.abs(freqs - omega_target)))
        omega_actual = float(freqs[idx])
        # Cross-spectrum at that single frequency
        FT_om = FT[idx]  # (n_assets,) complex
        # S_ij(omega) = FT_i * conj(FT_j)
        S = np.outer(FT_om, np.conj(FT_om))
        # Normalize
        auto = np.abs(FT_om) ** 2
        norm = np.sqrt(np.outer(auto, auto))
        C_om = S / (norm + 1e-12)
        # Argument -> lag
        # arg(S_ij) = omega * (tau_j - tau_i) for asset i with lag tau_i  (since
        # FT_i has phase factor exp(-i * omega * tau_i) when path is shifted)
        # tau_ij = lag_j - lag_i = arg(S_ij) / omega ?
        # Check: if i is leader (lag 0) and j has lag tau_j, then FT_j ~
        # FT_i * exp(-i * omega * tau_j) (in our sign convention where
        # follower at time t = leader at time t - tau_j; the FT picks up
        # exp(-i * omega * tau_j) per shift property)
        # Then S_ij = FT_i * conj(FT_j) ~ |FT_i|^2 * exp(+i * omega * tau_j)
        # so arg(S_ij) = +omega * tau_j when i is leader, i.e., tau_ij = +tau_j
        # because i leads j by tau_j.
        # In matrix form: tau_ij = arg(S_ij) / omega
        arg_S = np.angle(C_om)
        tau_est = arg_S / (omega_actual + 1e-12)
        m = lag_matrix_metrics(tau_est, L_true)
        records.append({
            "anomaly_chase": "direct_cross_spectrum_phase",
            "omega_target": omega_target,
            "omega_actual": omega_actual,
            "metrics": m,
        })
    return records


def anomaly_larger_lags_higher_snr(rng: np.random.Generator) -> List[Dict]:
    """
    Probe whether T^N would work with a more favorable SNR regime: lower
    follower noise + smaller lag range + slower-frequency leader. If T^N
    still underperforms, the failure isn't SNR-bound — it's structural.
    """
    rng_local = np.random.default_rng(SEED + 3000)
    # Easier benchmark: shorter lags + lower follower noise
    easier_lags = [0, 1, 2, 3, 4, 5]  # max lag = 5 instead of 10
    easier_noise = 0.001  # 10x lower
    fine_times, leader_log_prices = simulate_leader_path(
        rng_local, T_HORIZON, DRIFT, VOL,
    )
    follower_paths = make_followers(
        fine_times, leader_log_prices, easier_lags, easier_noise, rng_local,
    )
    sampled = async_sample_paths(
        fine_times, follower_paths, SAMPLING_INTENSITY, T_HORIZON, rng_local,
    )
    L_true = build_ground_truth_lag_matrix(easier_lags)
    returns = common_grid_returns(sampled, grid_dt=1.0, horizon=T_HORIZON)

    records: List[Dict] = []

    # HY on easier benchmark
    lag_grid = np.arange(-HY_LAG_MAX, HY_LAG_MAX + 1, 1.0)
    L_hy = np.zeros((N_ASSETS, N_ASSETS))
    for i in range(N_ASSETS):
        for j in range(N_ASSETS):
            if i == j:
                continue
            t_i, p_i = sampled[i]
            t_j, p_j = sampled[j]
            tau_ij, _ = hayashi_yoshida_estimate_lag(t_i, p_i, t_j, p_j, lag_grid)
            L_hy[i, j] = tau_ij
    hy_m = lag_matrix_metrics(L_hy, L_true)
    records.append({
        "anomaly_chase": "easier_snr_regime",
        "method": "Hayashi_Yoshida_2005",
        "metrics": hy_m,
        "lags": easier_lags,
        "follower_noise_std": easier_noise,
    })

    # T^N complex lift on easier benchmark
    C_complex, omega_band = complex_correlation_matrix_via_cross_spectrum(
        returns, band_low=0.01, band_high=0.5,
    )
    L_complex = build_complex_correlation_laplacian(C_complex)
    eigvals, eigvecs = eigh(L_complex)
    for t in TN_TIMES:
        phase_factors = np.exp(-1j * eigvals * t)
        U_t = eigvecs @ np.diag(phase_factors) @ eigvecs.conj().T
        arg_U = np.angle(U_t)
        tau_est = -arg_U / (omega_band + 1e-12)
        m = lag_matrix_metrics(tau_est, L_true)
        records.append({
            "anomaly_chase": "easier_snr_regime",
            "method": "TN_complex_lift",
            "t_evolution": t,
            "metrics": m,
        })

    # Direct cross-spectrum on easier benchmark
    n_grid = returns.shape[0]
    R = returns - returns.mean(axis=0, keepdims=True)
    FT = np.fft.rfft(R, axis=0)
    freqs = np.fft.rfftfreq(n_grid, d=1.0)
    for omega_target in [0.05, 0.10, 0.20]:
        idx = int(np.argmin(np.abs(freqs - omega_target)))
        omega_actual = float(freqs[idx])
        FT_om = FT[idx]
        S = np.outer(FT_om, np.conj(FT_om))
        auto = np.abs(FT_om) ** 2
        norm = np.sqrt(np.outer(auto, auto))
        C_om = S / (norm + 1e-12)
        arg_S = np.angle(C_om)
        tau_est = arg_S / (omega_actual + 1e-12)
        m = lag_matrix_metrics(tau_est, L_true)
        records.append({
            "anomaly_chase": "easier_snr_regime",
            "method": "direct_cross_spectrum_phase",
            "omega_actual": omega_actual,
            "metrics": m,
        })

    return records


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


def aggregate_metric_over_trials(
    per_trial_metrics: List[Dict[str, float]],
    metric_key: str,
) -> Tuple[float, float, float, float]:
    """
    Returns (mean, std, ci_low_2.5pct, ci_high_97.5pct) over a list of
    per-trial metric dicts.
    """
    vals = np.array([m[metric_key] for m in per_trial_metrics if not np.isnan(m[metric_key])])
    if len(vals) == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    mean = float(vals.mean())
    std = float(vals.std())
    lo = float(np.percentile(vals, 2.5))
    hi = float(np.percentile(vals, 97.5))
    return mean, std, lo, hi


def main():
    t_start = time.time()
    print(f"=== T^N async-HF lead-lag spike — seed {SEED}, N_TRIALS={N_TRIALS} ===")
    print(f"Lag schedule: {LAG_SCHEDULE}")
    print(f"Horizon: {T_HORIZON}, sampling intensity: {SAMPLING_INTENSITY}/unit")
    rng = np.random.default_rng(SEED)

    all_records: List[Dict] = []

    # Run main multi-trial sweep
    trial_results: List[TrialResult] = []
    for trial in range(N_TRIALS):
        tr = run_single_trial(trial, rng)
        trial_results.append(tr)
        if (trial + 1) % 2 == 0 or trial == 0:
            print(f"  trial {trial + 1}/{N_TRIALS} | "
                  f"HY MAE={tr.hy_metrics['mae']:.3f} | "
                  f"HY rho={tr.hy_metrics['spearman_rho']:.3f}",
                  flush=True)

    # --- Aggregated Hayashi-Yoshida metrics ---
    hy_mae_mean, _, hy_mae_lo, hy_mae_hi = aggregate_metric_over_trials(
        [tr.hy_metrics for tr in trial_results], "mae",
    )
    hy_rho_mean, _, hy_rho_lo, hy_rho_hi = aggregate_metric_over_trials(
        [tr.hy_metrics for tr in trial_results], "spearman_rho",
    )
    hy_sa_mean, _, hy_sa_lo, hy_sa_hi = aggregate_metric_over_trials(
        [tr.hy_metrics for tr in trial_results], "sign_accuracy",
    )
    config = {
        "n_assets": N_ASSETS,
        "lag_schedule": LAG_SCHEDULE,
        "horizon": T_HORIZON,
        "sampling_intensity": SAMPLING_INTENSITY,
        "follower_noise_std": FOLLOWER_NOISE_STD,
        "n_trials": N_TRIALS,
        "seed": SEED,
    }
    for metric, mean, lo, hi in [
        ("mae", hy_mae_mean, hy_mae_lo, hy_mae_hi),
        ("spearman_rho", hy_rho_mean, hy_rho_lo, hy_rho_hi),
        ("sign_accuracy", hy_sa_mean, hy_sa_lo, hy_sa_hi),
    ]:
        all_records.append({
            "method": "Hayashi_Yoshida_2005",
            "metric": metric,
            "value": mean,
            "ci_low": lo,
            "ci_high": hi,
            "ground_truth": "known_lag_schedule",
            "config": config,
        })

    print(f"\n=== Hayashi-Yoshida 2005 (baseline) ===")
    print(f"  MAE              = {hy_mae_mean:.3f}  [{hy_mae_lo:.3f}, {hy_mae_hi:.3f}]")
    print(f"  Spearman rho     = {hy_rho_mean:.3f}  [{hy_rho_lo:.3f}, {hy_rho_hi:.3f}]")
    print(f"  Sign accuracy    = {hy_sa_mean:.3f}  [{hy_sa_lo:.3f}, {hy_sa_hi:.3f}]")

    # --- T^N real-Laplacian control (expected: poor, no phase info) ---
    print(f"\n=== T^N real-Laplacian CONTROL (magnitude-only correlation; expected: poor) ===")
    print(f"{'t':>6s}  {'MAE':>7s}  {'rho':>7s}  {'sign_acc':>9s}")
    for t in TN_TIMES:
        t_metrics = [tr.tn_real_control_metrics_by_t[t] for tr in trial_results]
        m_mae, _, m_mae_lo, m_mae_hi = aggregate_metric_over_trials(t_metrics, "mae")
        m_rho, _, m_rho_lo, m_rho_hi = aggregate_metric_over_trials(t_metrics, "spearman_rho")
        m_sa, _, m_sa_lo, m_sa_hi = aggregate_metric_over_trials(t_metrics, "sign_accuracy")
        for metric, val, lo, hi in [
            ("mae", m_mae, m_mae_lo, m_mae_hi),
            ("spearman_rho", m_rho, m_rho_lo, m_rho_hi),
            ("sign_accuracy", m_sa, m_sa_lo, m_sa_hi),
        ]:
            all_records.append({
                "method": "TN_real_control",
                "metric": metric,
                "value": val,
                "ci_low": lo,
                "ci_high": hi,
                "t_evolution": t,
                "ground_truth": "known_lag_schedule",
                "config": config,
            })
        print(f"  {t:>5.2f}  {m_mae:>7.3f}  {m_rho:>7.3f}  {m_sa:>9.3f}")

    # --- T^N complex-Laplacian LIFT (load-bearing test) ---
    print(f"\n=== T^N complex-Laplacian LIFT (cross-spectrum; load-bearing test) ===")
    print(f"{'t':>6s}  {'MAE':>7s}  {'rho':>7s}  {'sign_acc':>9s}")
    best_t = None
    best_rho = -2.0
    for t in TN_TIMES:
        t_metrics = [tr.tn_complex_lift_metrics_by_t[t] for tr in trial_results]
        m_mae, _, m_mae_lo, m_mae_hi = aggregate_metric_over_trials(t_metrics, "mae")
        m_rho, _, m_rho_lo, m_rho_hi = aggregate_metric_over_trials(t_metrics, "spearman_rho")
        m_sa, _, m_sa_lo, m_sa_hi = aggregate_metric_over_trials(t_metrics, "sign_accuracy")
        for metric, val, lo, hi in [
            ("mae", m_mae, m_mae_lo, m_mae_hi),
            ("spearman_rho", m_rho, m_rho_lo, m_rho_hi),
            ("sign_accuracy", m_sa, m_sa_lo, m_sa_hi),
        ]:
            all_records.append({
                "method": "TN_complex_lift",
                "metric": metric,
                "value": val,
                "ci_low": lo,
                "ci_high": hi,
                "t_evolution": t,
                "ground_truth": "known_lag_schedule",
                "config": config,
            })
        print(f"  {t:>5.2f}  {m_mae:>7.3f}  {m_rho:>7.3f}  {m_sa:>9.3f}")
        if not np.isnan(m_rho) and m_rho > best_rho:
            best_rho = m_rho
            best_t = t

    print(f"\n  Best-t for complex lift: t = {best_t}, Spearman rho = {best_rho:.3f}")

    # --- Anomaly chase: initial state choice ---
    print(f"\n=== Anomaly chase: initial state choice ===")
    anomaly_records = anomaly_initial_state_choice(rng)
    for rec in anomaly_records:
        all_records.append(rec)
        print(f"  {rec['initial_state']:>32s} | "
              f"MAE={rec['metrics']['mae']:.3f} | "
              f"rho={rec['metrics']['spearman_rho']:.3f} | "
              f"sign={rec['metrics']['sign_accuracy']:.3f}")

    # --- Anomaly chase: omega band sensitivity ---
    print(f"\n=== Anomaly chase: omega band sensitivity ===")
    band_records = anomaly_omega_band_sensitivity(rng)
    for rec in band_records:
        all_records.append(rec)
        print(f"  {rec['band_name']:>15s} (omega={rec['omega_band_midpoint']:.3f}, "
              f"t={rec['t_test']:.2f}) | MAE={rec['metrics']['mae']:.3f} | "
              f"rho={rec['metrics']['spearman_rho']:.3f}")

    # --- Anomaly chase: direct cross-spectrum phase ---
    print(f"\n=== Anomaly chase: direct cross-spectrum phase (Welch coherence) ===")
    direct_records = anomaly_direct_cross_spectrum_phase(rng)
    for rec in direct_records:
        all_records.append(rec)
        print(f"  omega={rec['omega_actual']:.3f}  | "
              f"MAE={rec['metrics']['mae']:.3f} | "
              f"rho={rec['metrics']['spearman_rho']:.3f} | "
              f"sign={rec['metrics']['sign_accuracy']:.3f}")

    # --- Anomaly chase: easier SNR regime ---
    print(f"\n=== Anomaly chase: easier SNR regime (shorter lags + lower noise) ===")
    easier_records = anomaly_larger_lags_higher_snr(rng)
    for rec in easier_records:
        all_records.append(rec)
        method = rec.get("method", "?")
        t_str = f"t={rec.get('t_evolution'):.2f} " if "t_evolution" in rec else ""
        om_str = f"omega={rec.get('omega_actual'):.3f} " if "omega_actual" in rec else ""
        print(f"  {method:>30s} {t_str}{om_str}| "
              f"MAE={rec['metrics']['mae']:.3f} | "
              f"rho={rec['metrics']['spearman_rho']:.3f} | "
              f"sign={rec['metrics']['sign_accuracy']:.3f}")

    # --- Per-trial summary ---
    for tr in trial_results:
        all_records.append({
            "method": "per_trial_summary",
            "trial": tr.trial,
            "hy_metrics": tr.hy_metrics,
            "tn_complex_lift_best_t_metrics": tr.tn_complex_lift_metrics_by_t.get(best_t, {}) if best_t else {},
            "tn_complex_lift_best_t": best_t,
            "omega_band": tr.omega_band,
        })

    # --- Honest verdict record ---
    verdict = {
        "method": "verdict",
        "hy_baseline_mae_mean": hy_mae_mean,
        "hy_baseline_spearman_rho_mean": hy_rho_mean,
        "hy_baseline_sign_accuracy_mean": hy_sa_mean,
        "tn_complex_best_t": best_t,
        "tn_complex_best_t_spearman_rho_mean": best_rho,
        "tn_complex_best_t_mae_mean": (
            float(np.mean([tr.tn_complex_lift_metrics_by_t[best_t]["mae"] for tr in trial_results]))
            if best_t else float("nan")
        ),
        "tn_complex_best_t_sign_accuracy_mean": (
            float(np.mean([tr.tn_complex_lift_metrics_by_t[best_t]["sign_accuracy"] for tr in trial_results]))
            if best_t else float("nan")
        ),
        "verdict_summary": (
            "T^N lift recovers lag with Spearman rho={:.3f} at best-t={}; "
            "Hayashi-Yoshida rho={:.3f}. ".format(best_rho, best_t, hy_rho_mean)
            + ("T^N competitive" if (not np.isnan(best_rho) and abs(best_rho) > 0.9 * abs(hy_rho_mean)) else "T^N underperforms HY")
        ),
    }
    all_records.append(verdict)

    # --- Write NDJSON ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with NDJSON_PATH.open("w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")

    elapsed = time.time() - t_start
    print(f"\n=== Wrote NDJSON: {NDJSON_PATH} ===")
    print(f"Total records: {len(all_records)}")
    print(f"Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
