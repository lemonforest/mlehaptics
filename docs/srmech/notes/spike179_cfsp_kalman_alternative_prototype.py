"""Spike #179 — CFSP-Kalman alternative prototype.

Test: Class K truncate_sparse + Class M delta-bind composition as a
tracking estimator that PRESERVES substrate-portable bit-discrete
content where standard Kalman destroys it.

Identity claim (per `[[user_stance_identity_not_implementation_discipline]]`):
    TRACKING-OF-BIT-DISCRETE-CONTENT IS  Class M (delta-bind = XOR-accumulate)
                                       ∘ Class K (truncate_sparse =
                                                  Hamming-threshold gate
                                                  at substrate-natural
                                                  Class N rational)

Empirical anchors:
- Spike #174: Kalman destroys 19.79% BER + 36% bind-relationship + 40%
  orbit similarity at +20 dB SNR (essentially noise-free).
- Spike #176 / `[[user_stance_rotation_is_class_k_pin_slot]]`:
  rotation IS Class K (pin-slot composition).
- Spike #177 / `[[user_stance_pin_slot_resonate_music_box_mechanism]]`:
  pin-slot-resonate = Class I+K+C+M∘K named composition pattern;
  substrate-natural ring-down 0.68% precision.

Tests T1-T6 per Spike #179 brief.

Canonical SSoT (per `[[feedback_science_is_ssot_not_project]]`):
- Kalman R.E. (1960) "A New Approach to Linear Filtering and Prediction
  Problems", J. Basic Eng. 82, 35. DOI 10.1115/1.3662552.
- Kay S.M. (1993) "Fundamentals of Statistical Signal Processing:
  Estimation Theory", Prentice Hall. ISBN 0-13-345711-7.
- Donoho D.L. & Johnstone I.M. (1994) "Ideal spatial adaptation by
  wavelet shrinkage", Biometrika 81(3), 425. DOI 10.1093/biomet/81.3.425.
- Kanerva P. (2009) "Hyperdimensional Computing", Cognitive Computation
  1, 139. DOI 10.1007/s12559-009-9009-8.
- Plate T.A. (1995) "Holographic Reduced Representations", IEEE TNN
  6, 623. DOI 10.1109/72.377968.

Trauma-informed defensive scope (methodology research/educational only).
14 A-N intact; no class promotion.
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

# Make srmech.amsc importable from this notes directory.
_SRMECH_PY = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "python")
)
if _SRMECH_PY not in sys.path:
    sys.path.insert(0, _SRMECH_PY)

from srmech.amsc import hdc  # noqa: E402  Class M primitive surface


# ----------------------------------------------------------------------
# Bit-vector helpers (BSC = D-bit binary state; matches srmech HDC layout)
# ----------------------------------------------------------------------

D_BYTES = 128        # 1024-bit hypervector (Kanerva 2009 canonical small)
D_BITS = 8 * D_BYTES


def random_bits(rng: np.random.Generator) -> bytes:
    """Sample a uniformly random D-bit vector as bytes."""
    return bytes(rng.integers(0, 256, size=D_BYTES, dtype=np.uint8).tolist())


def hamming(a: bytes, b: bytes) -> int:
    """Bit-level Hamming distance (count of differing bits)."""
    assert len(a) == len(b), "hamming: length mismatch"
    n = 0
    for x, y in zip(a, b):
        n += bin(x ^ y).count("1")
    return n


def popcount(a: bytes) -> int:
    return sum(bin(x).count("1") for x in a)


def ber(estimate: bytes, truth: bytes) -> float:
    """Bit error rate vs truth."""
    return hamming(estimate, truth) / D_BITS


def bit_flip_noise(x: bytes, p_flip: float, rng: np.random.Generator) -> bytes:
    """Bernoulli bit-flip channel: each bit independently flipped with prob p."""
    flips = rng.random(D_BITS) < p_flip
    out = bytearray(x)
    for i in range(D_BITS):
        if flips[i]:
            out[i >> 3] ^= 1 << (i & 7)
    return bytes(out)


def snr_db_to_pflip(snr_db: float) -> float:
    """Map SNR (dB) to BSC bit-flip probability.

    Convention: SNR is defined for a BPSK-equivalent channel.
    p_flip = Q(sqrt(2 * 10^(SNR/10))) where Q is the standard
    Gaussian Q-function. Per Kay 1993 §A.

    We use erfc directly: p_flip = 0.5 * erfc(sqrt(snr_linear)).
    """
    snr_lin = 10.0 ** (snr_db / 10.0)
    return 0.5 * math.erfc(math.sqrt(snr_lin))


def snr_db_to_sigma(snr_db: float) -> float:
    """Map SNR (dB) to Gaussian noise sigma on ±1 BPSK signal.

    Signal power = 1 (BPSK constellation at ±1).
    Noise variance sigma^2 = 10^(-SNR/10).
    """
    return math.sqrt(10.0 ** (-snr_db / 10.0))


def bpsk_encode_with_gaussian(
    x: bytes, sigma: float, rng: np.random.Generator
) -> np.ndarray:
    """Continuous BPSK-encoded measurement: y = (2*x - 1) + N(0, sigma^2).

    Returns D-dim numpy array of continuous-valued measurements.
    """
    bits = np.zeros(D_BITS, dtype=np.float64)
    for i in range(D_BITS):
        bits[i] = float((x[i >> 3] >> (i & 7)) & 1)
    signal = 2.0 * bits - 1.0
    noise = rng.normal(0.0, sigma, size=D_BITS)
    return signal + noise


def threshold_to_bits(y: np.ndarray) -> bytes:
    """Threshold continuous measurement at 0 -> bit decision."""
    out = bytearray(D_BYTES)
    for i in range(D_BITS):
        if y[i] >= 0.0:
            out[i >> 3] |= 1 << (i & 7)
    return bytes(out)


# ----------------------------------------------------------------------
# T1 — Ground truth state evolution
# ----------------------------------------------------------------------

def random_slow_walk(
    n_steps: int,
    flip_rate: float,
    rng: np.random.Generator,
) -> List[bytes]:
    """Generate substrate-natural slow walk in BSC space.

    At each step, exactly `flip_rate` fraction of bits flip from prior
    state; substrate-natural evolution (Class M delta with small Class N
    rational of D bits per step).
    """
    states = [random_bits(rng)]
    n_flip = int(round(flip_rate * D_BITS))
    for _ in range(n_steps - 1):
        prev = states[-1]
        flip_indices = rng.choice(D_BITS, size=n_flip, replace=False)
        nxt = bytearray(prev)
        for idx in flip_indices:
            nxt[idx >> 3] ^= 1 << (idx & 7)
        states.append(bytes(nxt))
    return states


# ----------------------------------------------------------------------
# T2 — Standard Kalman baseline (continuous-state smoothing destroys bits)
# ----------------------------------------------------------------------

def kalman_bpsk_baseline(
    measurements_continuous: List[np.ndarray],
    process_var: float,
    measurement_var: float,
) -> List[bytes]:
    """Per-bit independent scalar Kalman filter on continuous BPSK signal.

    Reproduces #174 destruction pattern: Kalman assumes the state evolves
    SLOWLY (small Q) under continuous Gaussian noise, so the predict step
    pulls each bit-track toward the prior estimate. When the underlying
    bit-discrete state actually flips between time steps (substrate-natural
    Class M delta), the Kalman smoothing AVERAGES the flip across multiple
    steps, leaving the bit estimate in the wrong half-plane until enough
    measurements accumulate. This is the algebraic-content-destruction
    mechanism: Gaussian-Markov assumption is structurally incompatible
    with substrate-portable bit-discrete updates.

    Per Kay 1993 §13:
        State:        x_t = x_{t-1} + w,   w ~ N(0, Q)
        Measurement:  y_t = x_t + v,        v ~ N(0, R)
    Signal range ±1 (BPSK); decision threshold = 0.
    """
    n_steps = len(measurements_continuous)
    # Initialize each bit-track at 0 (centred on decision boundary) with
    # high variance.
    mu = np.zeros(D_BITS, dtype=np.float64)
    P = np.full(D_BITS, 1.0, dtype=np.float64)
    Q = process_var
    R = measurement_var
    estimates: List[bytes] = []
    for t in range(n_steps):
        # Predict.
        P = P + Q
        # Update.
        y = measurements_continuous[t]
        K = P / (P + R)
        mu = mu + K * (y - mu)
        P = (1.0 - K) * P
        # Threshold at 0 for BPSK bit estimate.
        est_bits = bytearray(D_BYTES)
        for i in range(D_BITS):
            if mu[i] >= 0.0:
                est_bits[i >> 3] |= 1 << (i & 7)
        estimates.append(bytes(est_bits))
    return estimates


# ----------------------------------------------------------------------
# T3 — CFSP-Kalman alternative: Class M ∘ Class K
# ----------------------------------------------------------------------

def class_k_truncate_sparse(
    delta: bytes,
    threshold_bits: int,
) -> bytes:
    """Class K asymptotic-DOF gate on a delta vector.

    If popcount(delta) <= threshold_bits, retain delta unchanged.
    Otherwise, zero the delta (substrate-natural rejection: a delta
    that exceeds the substrate's update-rate capacity is interpreted
    as noise burst and not propagated).

    This is the substrate-natural asymptotic-DOF mechanism per
    `[[user_stance_epicycle_via_gear_plus_pin]]`: Class K parameterises
    the rate of approach to the limit (how many bits the substrate can
    plausibly flip per step). Deltas inside the threshold are valid
    substrate evolution; deltas exceeding it are noise.

    Identity-not-implementation: this IS asymptotic-DOF threshold-gate
    (Class K); not a heuristic smoothing op.
    """
    pc = popcount(delta)
    if pc <= threshold_bits:
        return delta
    # Reject the update — return zero-delta (no change to posterior).
    return b"\x00" * len(delta)


def cfsp_kalman_alternative(
    measurements_bits: List[bytes],
    prior_state: bytes,
    threshold_bits: int,
) -> List[bytes]:
    """CFSP-Kalman alternative tracking estimator.

    State update per step t:
        update_delta[t]    = bind(x_post[t-1], y[t])      # Class M XOR
        truncated_delta[t] = truncate_sparse(update_delta, threshold_bits)
        x_post[t]          = bind(x_post[t-1], truncated_delta[t])

    Composition: x_post[t] = x_post[t-1] XOR (truncate(x_post[t-1] XOR y[t]))

    All Class M ops via srmech.amsc.hdc.bind (XOR, commutative,
    associative, self-inverse).

    NOTE: prior_state should be the FIRST measurement (substrate-natural
    initialization), not zero — otherwise the very first delta is huge
    and the truncate rejects it.
    """
    x_post = prior_state
    estimates: List[bytes] = []
    for y in measurements_bits:
        delta = hdc.bind(x_post, y)                       # Class M
        truncated = class_k_truncate_sparse(delta, threshold_bits)  # Class K
        x_post = hdc.bind(x_post, truncated)              # Class M
        estimates.append(x_post)
    return estimates


def cfsp_from_continuous(
    measurements_continuous: List[np.ndarray],
    threshold_bits: int,
) -> List[bytes]:
    """CFSP-Kalman alternative on continuous BPSK measurements.

    Pipeline:
      1. Threshold each continuous measurement at 0 -> bytes (Class A
         content addressing of bit content).
      2. Use FIRST thresholded measurement as prior state (substrate-
         natural initialization — substrate begins where it is observed).
      3. Apply Class M ∘ Class K composition for subsequent steps.
    """
    if not measurements_continuous:
        return []
    bits_seq = [threshold_to_bits(y) for y in measurements_continuous]
    prior = bits_seq[0]
    return cfsp_kalman_alternative(bits_seq, prior, threshold_bits)


def no_filter(measurements_bits: List[bytes]) -> List[bytes]:
    """Identity passthrough — measurement is the estimate."""
    return list(measurements_bits)


def no_filter_from_continuous(
    measurements_continuous: List[np.ndarray],
) -> List[bytes]:
    return [threshold_to_bits(y) for y in measurements_continuous]


# ----------------------------------------------------------------------
# T4 — SNR sweep + metric aggregation
# ----------------------------------------------------------------------

@dataclass
class TrackingResult:
    method: str
    snr_db: float
    p_flip: float
    mean_ber: float
    median_ber: float
    final_ber: float
    mean_bind_preserved: float  # bind-commutativity check
    n_steps: int
    threshold_bits: int


def bind_commutativity_score(
    estimates: List[bytes],
    truth: List[bytes],
    rng: np.random.Generator,
) -> float:
    """Algebraic-identity preservation: does bind(estimate, R) ≈ bind(truth, R)?

    Generates a random reference R, binds both sequences against it,
    measures average similarity. Bind is Class M XOR-commutative, so
    bind(a, R) XOR bind(b, R) = a XOR b — equivalent to direct similarity,
    but lets us probe whether the estimator is "bind-stable" (i.e., XOR
    structure is preserved through tracking).
    """
    R = random_bits(rng)
    sims = []
    for est, tr in zip(estimates, truth):
        e_bound = hdc.bind(est, R)
        t_bound = hdc.bind(tr, R)
        sims.append(hdc.similarity(e_bound, t_bound))
    return float(np.mean(sims))


def bind_relationship_preservation(
    estimates: List[bytes],
    truth: List[bytes],
) -> float:
    """Class M bind-relationship preservation across time-step pairs.

    For each adjacent pair (t, t+1), compute:
        true_delta = bind(truth[t], truth[t+1])      # XOR difference
        est_delta  = bind(est[t],   est[t+1])
        agreement  = similarity(true_delta, est_delta)

    If the estimator preserves the XOR-relationship between adjacent
    states (the substrate-natural step delta), this is high. If the
    estimator destroys the step-by-step algebraic content, this is low.

    This is the #174 "bind-relationship" metric — Kalman destroyed
    it at +20 dB SNR because Gaussian smoothing flattens the step-deltas.
    """
    sims = []
    for i in range(len(estimates) - 1):
        true_delta = hdc.bind(truth[i], truth[i + 1])
        est_delta = hdc.bind(estimates[i], estimates[i + 1])
        sims.append(hdc.similarity(true_delta, est_delta))
    if not sims:
        return 1.0
    return float(np.mean(sims))


def run_snr_sweep(
    snr_db_list: List[float],
    n_steps: int,
    walk_flip_rate: float,
    threshold_bits: int,
    rng_seed: int,
) -> List[TrackingResult]:
    """Run all three methods at each SNR; return aggregated metrics.

    Measurement model (continuous BPSK + Gaussian noise):
        signal[i] = 2 * x_true[i] - 1            in {-1, +1}
        y[i] = signal[i] + N(0, sigma^2)
        sigma^2 = 10^(-SNR/10)
    Each method consumes the continuous y stream; threshold at 0 -> bit.
    """
    rng = np.random.default_rng(rng_seed)
    truth = random_slow_walk(n_steps, walk_flip_rate, rng)
    results: List[TrackingResult] = []
    for snr_db in snr_db_list:
        sigma = snr_db_to_sigma(snr_db)
        measurements_continuous = [
            bpsk_encode_with_gaussian(t, sigma, rng) for t in truth
        ]
        # No-filter baseline: threshold-each-step independently.
        nf = no_filter_from_continuous(measurements_continuous)
        # Kalman on continuous signal.
        # MODEL MISSPECIFICATION (the #174 destruction mechanism): the
        # filter is told the state is nearly static (Q very small) but
        # the truth flips at substrate-natural rate. Kalman smooths
        # across discrete flips, destroying algebraic-bit content.
        # This reproduces the structural-incompatibility-of-Gaussian-
        # smoothing-with-bit-discrete-content phenomenon.
        process_var = 1e-4  # filter believes state is nearly static
        measurement_var = sigma * sigma
        kf = kalman_bpsk_baseline(
            measurements_continuous, process_var, measurement_var
        )
        # CFSP-Kalman alternative.
        cfsp = cfsp_from_continuous(measurements_continuous, threshold_bits)
        for method, ests in [("no_filter", nf), ("kalman", kf),
                              ("cfsp", cfsp)]:
            bers = [ber(e, t) for e, t in zip(ests, truth)]
            bind_score = bind_commutativity_score(ests, truth, rng)
            bind_rel = bind_relationship_preservation(ests, truth)
            results.append(TrackingResult(
                method=method,
                snr_db=snr_db,
                p_flip=sigma * sigma,  # noise variance instead of p_flip
                mean_ber=float(np.mean(bers)),
                median_ber=float(np.median(bers)),
                final_ber=float(bers[-1]),
                mean_bind_preserved=bind_score,
                n_steps=n_steps,
                threshold_bits=threshold_bits,
            ))
            # Stash bind-relationship in a side dict (attach to last item).
            results[-1].__dict__["bind_relationship"] = bind_rel
    return results


# ----------------------------------------------------------------------
# T5 — Pin-slot-resonate composition (cyclic-Class-I ring-down)
# ----------------------------------------------------------------------

def pin_slot_resonate_walk(
    n_steps: int,
    base_state: bytes,
    period: int,
    amplitude_bits: int,
    rng: np.random.Generator,
) -> List[bytes]:
    """Ring-down state-evolution per Spike #177.

    Substrate-natural ring-down: state x[t] = base XOR perturbation[t]
    where perturbation[t] has popcount that decays exponentially toward
    zero with cyclic-group-modulated bit-positions (Class I + Class K).

        popcount(perturbation[t]) = amplitude_bits * cos((2*pi/period)*t)^2
                                   * exp(-t / tau)

    The cos² factor implements the pin-slot rocker (Class K asymptotic-
    DOF in the cyclic-period direction); the exp factor implements the
    ring-down envelope (Class M ∘ Class K decay).

    Identity: this IS Class I + Class K + Class C + Class M∘K composition
    per `[[user_stance_pin_slot_resonate_music_box_mechanism]]`.
    """
    states = [base_state]
    tau = n_steps / 3.0
    for t in range(1, n_steps):
        # Pin-slot envelope: cos² modulation × exponential decay.
        phase = 2.0 * math.pi * t / period
        env = (math.cos(phase) ** 2) * math.exp(-t / tau)
        decay_amp = int(round(amplitude_bits * env))
        nxt = bytearray(base_state)
        if decay_amp > 0:
            # Deterministic-but-cyclic perturbation pattern (Class I):
            # rotate the bit-mask offset with period.
            offset = (t * 13) % D_BITS  # deterministic stride
            for k in range(decay_amp):
                idx = (offset + k) % D_BITS
                nxt[idx >> 3] ^= 1 << (idx & 7)
        states.append(bytes(nxt))
    return states


def ring_down_signature(states: List[bytes], base: bytes) -> List[int]:
    """Extract per-step Hamming distance from base — the ring-down envelope."""
    return [hamming(s, base) for s in states]


def ring_down_correlation(env_a: List[int], env_b: List[int]) -> float:
    """Pearson correlation of two ring-down envelopes."""
    a = np.array(env_a, dtype=np.float64)
    b = np.array(env_b, dtype=np.float64)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


# ----------------------------------------------------------------------
# T6 — Class N rational threshold sensitivity sweep
# ----------------------------------------------------------------------

def threshold_sweep(
    n_steps: int,
    walk_flip_rate: float,
    snr_db: float,
    rationals: List[Tuple[int, int]],
    rng_seed: int,
) -> List[Dict]:
    """Sweep truncate-sparse threshold across Class N rationals D / k."""
    rng = np.random.default_rng(rng_seed)
    truth = random_slow_walk(n_steps, walk_flip_rate, rng)
    sigma = snr_db_to_sigma(snr_db)
    measurements_cont = [bpsk_encode_with_gaussian(t, sigma, rng) for t in truth]
    out = []
    for num, den in rationals:
        threshold_bits = int(round(D_BITS * num / den))
        cfsp = cfsp_from_continuous(measurements_cont, threshold_bits)
        bers = [ber(e, t) for e, t in zip(cfsp, truth)]
        out.append({
            "rational_num": num,
            "rational_den": den,
            "rational_value": num / den,
            "threshold_bits": threshold_bits,
            "mean_ber": float(np.mean(bers)),
            "median_ber": float(np.median(bers)),
            "final_ber": float(bers[-1]),
        })
    return out


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------

def main() -> None:
    notes_dir = os.path.dirname(__file__)
    records_path = os.path.join(
        notes_dir, "spike179_records_2026-05-19.ndjson"
    )
    records: List[Dict] = []

    def emit(rec: Dict) -> None:
        records.append(rec)

    # ---- T1 ---- Ground truth construction
    rng = np.random.default_rng(20260519)
    n_steps = 64
    walk_flip_rate = 0.05  # 5% bits flip per step — substrate-natural
    truth = random_slow_walk(n_steps, walk_flip_rate, rng)
    emit({
        "spike": 179, "test": "T1", "kind": "ground_truth",
        "n_steps": n_steps, "D_bits": D_BITS,
        "walk_flip_rate": walk_flip_rate,
        "per_step_hamming_mean": float(np.mean([
            hamming(truth[i], truth[i+1]) for i in range(n_steps-1)
        ])),
        "per_step_hamming_expected": walk_flip_rate * D_BITS,
        "note": "Substrate-natural slow walk in BSC space",
    })

    # ---- T2-T4 ---- Kalman baseline + CFSP-alternative + no-filter sweep
    snr_list = [20.0, 10.0, 0.0, -10.0]
    threshold_bits = int(round(D_BITS * walk_flip_rate * 2))  # 2x substrate rate
    sweep = run_snr_sweep(
        snr_db_list=snr_list,
        n_steps=n_steps,
        walk_flip_rate=walk_flip_rate,
        threshold_bits=threshold_bits,
        rng_seed=20260519,
    )
    for r in sweep:
        emit({
            "spike": 179, "test": "T2-T4", "kind": "snr_sweep_point",
            "method": r.method, "snr_db": r.snr_db,
            "noise_variance": r.p_flip,
            "mean_ber": r.mean_ber, "median_ber": r.median_ber,
            "final_ber": r.final_ber,
            "mean_bind_preserved": r.mean_bind_preserved,
            "bind_relationship": r.__dict__.get("bind_relationship", None),
            "n_steps": r.n_steps, "threshold_bits": r.threshold_bits,
        })

    # ---- T5 ---- Pin-slot-resonate composition (#177)
    rng_t5 = np.random.default_rng(20260520)
    base = random_bits(rng_t5)
    period = 7
    amplitude_bits = int(round(D_BITS * 0.10))  # 10% initial amplitude
    truth_rd = pin_slot_resonate_walk(n_steps, base, period, amplitude_bits, rng_t5)
    truth_envelope = ring_down_signature(truth_rd, base)
    snr_t5_db = 10.0
    sigma_t5 = snr_db_to_sigma(snr_t5_db)
    measurements_rd_cont = [
        bpsk_encode_with_gaussian(s, sigma_t5, rng_t5) for s in truth_rd
    ]
    # Kalman.
    kf_rd = kalman_bpsk_baseline(
        measurements_rd_cont,
        process_var=4.0 * 0.10 * 0.90,
        measurement_var=sigma_t5 * sigma_t5,
    )
    kf_envelope = ring_down_signature(kf_rd, base)
    # CFSP.
    cfsp_rd = cfsp_from_continuous(measurements_rd_cont, threshold_bits)
    cfsp_envelope = ring_down_signature(cfsp_rd, base)
    # No-filter.
    nf_rd = no_filter_from_continuous(measurements_rd_cont)
    nf_envelope = ring_down_signature(nf_rd, base)
    kf_bers = [ber(e, t) for e, t in zip(kf_rd, truth_rd)]
    cfsp_bers = [ber(e, t) for e, t in zip(cfsp_rd, truth_rd)]
    nf_bers = [ber(e, t) for e, t in zip(nf_rd, truth_rd)]
    emit({
        "spike": 179, "test": "T5", "kind": "ring_down_composition",
        "snr_db": snr_t5_db, "sigma": sigma_t5,
        "period": period, "amplitude_bits": amplitude_bits,
        "truth_envelope_first8": truth_envelope[:8],
        "truth_envelope_last8": truth_envelope[-8:],
        "kalman_envelope_corr": ring_down_correlation(truth_envelope, kf_envelope),
        "cfsp_envelope_corr": ring_down_correlation(truth_envelope, cfsp_envelope),
        "no_filter_envelope_corr": ring_down_correlation(
            truth_envelope, nf_envelope
        ),
        "kalman_mean_ber": float(np.mean(kf_bers)),
        "cfsp_mean_ber": float(np.mean(cfsp_bers)),
        "no_filter_mean_ber": float(np.mean(nf_bers)),
        "kalman_final_ber": float(kf_bers[-1]),
        "cfsp_final_ber": float(cfsp_bers[-1]),
    })

    # ---- T5b ---- Fast ring-down (stress-test pin-slot-resonate at high
    #             cyclic rate; smaller tau forces Kalman to lag)
    rng_t5b = np.random.default_rng(20260522)
    base_b = random_bits(rng_t5b)
    period_b = 3   # fast cycle
    amp_b = int(round(D_BITS * 0.20))  # 20% amplitude
    # Fast ring-down: tau = n_steps / 8 (decays in first 8 steps)
    truth_rd_fast = []
    truth_rd_fast.append(base_b)
    tau_fast = n_steps / 8.0
    for t in range(1, n_steps):
        phase = 2.0 * math.pi * t / period_b
        env = (math.cos(phase) ** 2) * math.exp(-t / tau_fast)
        decay_amp = int(round(amp_b * env))
        nxt = bytearray(base_b)
        if decay_amp > 0:
            offset = (t * 13) % D_BITS
            for k in range(decay_amp):
                idx = (offset + k) % D_BITS
                nxt[idx >> 3] ^= 1 << (idx & 7)
        truth_rd_fast.append(bytes(nxt))
    truth_env_fast = ring_down_signature(truth_rd_fast, base_b)
    measurements_fast = [
        bpsk_encode_with_gaussian(s, sigma_t5, rng_t5b) for s in truth_rd_fast
    ]
    kf_fast = kalman_bpsk_baseline(
        measurements_fast,
        process_var=1e-4,  # misspec
        measurement_var=sigma_t5 * sigma_t5,
    )
    cfsp_fast = cfsp_from_continuous(measurements_fast, threshold_bits)
    nf_fast = no_filter_from_continuous(measurements_fast)
    kf_env_fast = ring_down_signature(kf_fast, base_b)
    cfsp_env_fast = ring_down_signature(cfsp_fast, base_b)
    nf_env_fast = ring_down_signature(nf_fast, base_b)
    emit({
        "spike": 179, "test": "T5b", "kind": "ring_down_fast_cycle",
        "snr_db": snr_t5_db, "sigma": sigma_t5,
        "period": period_b, "tau": tau_fast, "amplitude_bits": amp_b,
        "truth_envelope_first8": truth_env_fast[:8],
        "kalman_envelope_corr": ring_down_correlation(truth_env_fast, kf_env_fast),
        "cfsp_envelope_corr": ring_down_correlation(truth_env_fast, cfsp_env_fast),
        "no_filter_envelope_corr": ring_down_correlation(
            truth_env_fast, nf_env_fast
        ),
        "kalman_mean_ber": float(np.mean([ber(e, t) for e, t in zip(kf_fast, truth_rd_fast)])),
        "cfsp_mean_ber": float(np.mean([ber(e, t) for e, t in zip(cfsp_fast, truth_rd_fast)])),
        "no_filter_mean_ber": float(np.mean([ber(e, t) for e, t in zip(nf_fast, truth_rd_fast)])),
        "kalman_bind_rel": bind_relationship_preservation(kf_fast, truth_rd_fast),
        "cfsp_bind_rel": bind_relationship_preservation(cfsp_fast, truth_rd_fast),
        "no_filter_bind_rel": bind_relationship_preservation(nf_fast, truth_rd_fast),
        "note": "Fast cycle stresses Kalman's slow-evolution prior",
    })

    # ---- T6 ---- Class N rational threshold sensitivity
    rationals = [
        (1, 2),    # D/2 = 50% bits — maximally permissive
        (1, 3),    # D/3 ≈ 33%
        (1, 5),    # D/5 = 20%
        (1, 8),    # D/8 = 12.5%
        (1, 10),   # D/10 = 10% — matches substrate-natural * 2
        (3, 32),   # 3D/32 = 9.375%
        (1, 12),   # D/12 ≈ 8.33%
        (1, 16),   # D/16 = 6.25%
        (3, 50),   # 3D/50 = 6.00%
        (1, 18),   # D/18 ≈ 5.56% — just above substrate rate
        (1, 20),   # D/20 = 5% — substrate-natural rate
        (1, 22),   # D/22 ≈ 4.55% — just below
        (1, 24),   # D/24 ≈ 4.17%
        (1, 32),   # D/32 = 3.125% — below substrate rate
        (1, 64),   # D/64 = 1.56% — far below
    ]
    t6 = threshold_sweep(
        n_steps=n_steps,
        walk_flip_rate=walk_flip_rate,
        snr_db=10.0,
        rationals=rationals,
        rng_seed=20260521,
    )
    best = min(t6, key=lambda r: r["mean_ber"])
    for r in t6:
        emit({
            "spike": 179, "test": "T6", "kind": "threshold_sensitivity",
            "rational": f"{r['rational_num']}/{r['rational_den']}",
            "rational_value": r["rational_value"],
            "threshold_bits": r["threshold_bits"],
            "mean_ber": r["mean_ber"],
            "median_ber": r["median_ber"],
            "final_ber": r["final_ber"],
            "is_best": r["threshold_bits"] == best["threshold_bits"],
        })
    emit({
        "spike": 179, "test": "T6", "kind": "threshold_optimum",
        "best_rational": f"{best['rational_num']}/{best['rational_den']}",
        "best_rational_value": best["rational_value"],
        "best_threshold_bits": best["threshold_bits"],
        "best_mean_ber": best["mean_ber"],
        "substrate_natural_rate": walk_flip_rate,
        "substrate_natural_bits": int(round(D_BITS * walk_flip_rate)),
        "match_substrate_natural": (
            abs(best["rational_value"] - walk_flip_rate * 2) < 0.05
        ),
        "note": (
            "Predict: optimum at substrate-natural rate (5% = D/20) "
            "or 2x substrate-natural (10% = D/10) per Class K asymptotic-DOF"
        ),
    })

    # ---- Verdict aggregation ----
    by_method_snr = {}
    for r in sweep:
        by_method_snr[(r.method, r.snr_db)] = r
    verdicts = []
    for snr_db in snr_list:
        nf_r = by_method_snr[("no_filter", snr_db)]
        kf_r = by_method_snr[("kalman", snr_db)]
        cfsp_r = by_method_snr[("cfsp", snr_db)]
        cfsp_wins_vs_kalman = cfsp_r.mean_ber < kf_r.mean_ber
        cfsp_wins_vs_nofilter = cfsp_r.mean_ber < nf_r.mean_ber
        verdicts.append({
            "snr_db": snr_db,
            "p_flip": nf_r.p_flip,
            "no_filter_ber": nf_r.mean_ber,
            "kalman_ber": kf_r.mean_ber,
            "cfsp_ber": cfsp_r.mean_ber,
            "cfsp_wins_vs_kalman": cfsp_wins_vs_kalman,
            "cfsp_wins_vs_nofilter": cfsp_wins_vs_nofilter,
            "kalman_destroys_at_high_snr": (
                snr_db >= 10.0 and kf_r.mean_ber > 0.10
            ),
        })
    emit({
        "spike": 179, "test": "verdict", "kind": "summary",
        "verdicts_by_snr": verdicts,
        "kalman_destruction_reproduced": any(
            v["kalman_destroys_at_high_snr"] for v in verdicts
        ),
        "cfsp_wins_at_all_snr": all(v["cfsp_wins_vs_kalman"] for v in verdicts),
        "cfsp_wins_at_high_snr": all(
            v["cfsp_wins_vs_kalman"]
            for v in verdicts if v["snr_db"] >= 10.0
        ),
    })

    # Write NDJSON.
    with open(records_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    print(f"wrote {len(records)} records to {records_path}")

    # Print verdict table to stdout for the conductor's inline summary.
    print("\n--- Verdict table (BER) ---")
    print(f"{'SNR(dB)':>8}  {'sigma^2':>10}  {'no-filt':>8}  {'kalman':>8}  {'cfsp':>8}")
    for v in verdicts:
        print(
            f"{v['snr_db']:>8.1f}  {v['p_flip']:>10.6f}  "
            f"{v['no_filter_ber']:>8.4f}  {v['kalman_ber']:>8.4f}  "
            f"{v['cfsp_ber']:>8.4f}"
        )

    print("\n--- Bind-relationship preservation (algebraic-identity) ---")
    by_ms = {(r.method, r.snr_db): r for r in sweep}
    print(f"{'SNR(dB)':>8}  {'no-filt':>8}  {'kalman':>8}  {'cfsp':>8}")
    for snr_db in snr_list:
        nf_r = by_ms[("no_filter", snr_db)]
        kf_r = by_ms[("kalman", snr_db)]
        cfsp_r = by_ms[("cfsp", snr_db)]
        print(
            f"{snr_db:>8.1f}  "
            f"{nf_r.__dict__.get('bind_relationship', 0):>8.4f}  "
            f"{kf_r.__dict__.get('bind_relationship', 0):>8.4f}  "
            f"{cfsp_r.__dict__.get('bind_relationship', 0):>8.4f}"
        )
    print("\n--- T5 ring-down envelope correlations ---")
    t5 = [r for r in records if r.get("test") == "T5"][0]
    print(f"  truth-vs-kalman:    {t5['kalman_envelope_corr']:>8.4f}")
    print(f"  truth-vs-cfsp:      {t5['cfsp_envelope_corr']:>8.4f}")
    print(f"  truth-vs-no-filter: {t5['no_filter_envelope_corr']:>8.4f}")
    print("\n--- T6 threshold sensitivity ---")
    t6_pts = [r for r in records
              if r.get("test") == "T6" and r.get("kind") == "threshold_sensitivity"]
    for r in t6_pts:
        marker = " <-- best" if r.get("is_best") else ""
        print(
            f"  rational={r['rational']:>5}  "
            f"value={r['rational_value']:.4f}  "
            f"bits={r['threshold_bits']:>4}  "
            f"mean_ber={r['mean_ber']:.4f}{marker}"
        )


if __name__ == "__main__":
    main()
