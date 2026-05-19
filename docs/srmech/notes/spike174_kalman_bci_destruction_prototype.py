"""Spike #174 — Kalman filtering vs form-function-rotation cross-binning.

Tests whether Kalman filtering (constant-velocity linear-Gaussian state model)
applied to BCI-like signal pipelines structurally destroys the substrate-portable
algebraic content carried by form-function-rotation cross-binning composition
(Class A ∘ Class C ∘ Class M per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``).

Trauma-informed defensive scope: signal-processing-methodology research only.
NO patient treatment claims. NO clinical recommendations. NO targeting
framing. The simulation models a synthetic BCI-like signal pipeline as the
substrate-portable test substrate; results inform MS-14 BCI translation
methodology choice between Kalman-class and structure-preserving filters.

14 A-N primitive vocabulary intact; no class promotion. Uses srmech.amsc.hdc
(Class M), srmech.amsc.cyclic (Class I, via stdlib gcd), and stdlib hashlib
(Class A primitive surface).
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from dataclasses import dataclass, field
from math import gcd
from pathlib import Path
from typing import Sequence

# Ensure srmech is importable from the worktree.
HERE = Path(__file__).resolve()
SRMECH_PY = HERE.parents[2] / "python"
if str(SRMECH_PY) not in sys.path:
    sys.path.insert(0, str(SRMECH_PY))

from srmech.amsc import hdc  # noqa: E402


# -----------------------------------------------------------------------
# Construction parameters
# -----------------------------------------------------------------------

D_BITS = 8192                       # canonical RBS-HDC dimension (cf. Spike #170)
D_BYTES = D_BITS // 8               # 1024 bytes
N_EVENTS = 9                        # symbols per stream — odd, low enough that
                                    # per-atom contribution to bundle is well
                                    # above decoy noise floor for clean decode
SNR_DB_GRID = (20.0, 10.0, 0.0, -10.0)
RNG_SEED = 0xC0FFEE                 # deterministic
KALMAN_SIGMA_PROC_DEFAULT = 0.1     # process noise stddev (state-units / sample)
KALMAN_DT = 1.0                     # 1 sample per timestep


# -----------------------------------------------------------------------
# Class A ∘ Class C ∘ Class M encoding (form-function-rotation cross-bind)
# -----------------------------------------------------------------------

def content_to_shift(token: bytes, modulus: int) -> int:
    """Class A: SHA-256 of token → integer shift modulo D_BITS."""
    h = hashlib.sha256(token).digest()
    # First 8 bytes of digest as little-endian uint64.
    val = int.from_bytes(h[:8], "little", signed=False)
    return val % modulus


def stream_to_bundle(tokens: Sequence[bytes], d_bytes: int = D_BYTES) -> bytes:
    """Encode a token stream via form-function-rotation cross-bind.

    For each token:
      shift_i = SHA-256(token_i) mod D  (Class A → Class I modular)
      atom_i  = permute(BASE_ATOM, shift_i)  (Class C cyclic permute)
    Bundle (Class M majority) the atoms into a single D-bit fingerprint.

    BASE_ATOM is a deterministic stable pattern derived from the spike
    name so we get a reproducible substrate atom (no ML training).
    """
    base_seed = hashlib.sha256(b"spike174_base_atom").digest()
    # Stretch to D_BYTES by chained hashing.
    base = bytearray()
    seed = base_seed
    while len(base) < d_bytes:
        base.extend(seed)
        seed = hashlib.sha256(seed).digest()
    base_atom = bytes(base[:d_bytes])

    n = len(tokens)
    # Bundle needs odd count; if even, append a deterministic tie-break atom.
    atoms: list[bytes] = []
    for t in tokens:
        shift = content_to_shift(t, d_bytes * 8)
        atoms.append(hdc.permute(base_atom, shift))
    if (n & 1) == 0:
        # tie-break: another deterministic permute of base by a content-of-stream shift
        stream_shift = content_to_shift(
            b"||".join(tokens), d_bytes * 8
        )
        atoms.append(hdc.permute(base_atom, stream_shift))
    return hdc.bundle(atoms), atoms, base_atom


def reverse_decode_fraction(
    bundle: bytes,
    base_atom: bytes,
    tokens: Sequence[bytes],
) -> float:
    """For each token, recover its shift via cross-correlation against bundle.

    Build candidate codebook = {token → permute(base, shift(token))}.
    For each candidate, similarity(candidate, bundle) should be highest for
    the tokens that ARE in the stream. Fraction recovered = how many of the
    true tokens are in the top-K most-similar candidates of a larger pool.

    For a clean test, we just check: for each true token, similarity to
    bundle > similarity to randomly-shifted decoy atoms. We report fraction
    of true tokens that beat ALL same-bundle decoys constructed from
    arbitrary non-stream content.
    """
    d_bits = len(base_atom) * 8
    true_atoms = []
    for t in tokens:
        shift = content_to_shift(t, d_bits)
        true_atoms.append(hdc.permute(base_atom, shift))

    # Construct decoys: hashes of indices that are NOT tokens.
    decoy_atoms = []
    for i in range(2 * len(tokens)):
        decoy_tok = f"decoy_{i:06d}".encode()
        if decoy_tok in tokens:
            continue
        shift = content_to_shift(decoy_tok, d_bits)
        decoy_atoms.append(hdc.permute(base_atom, shift))

    # For each true atom, compute similarity. Find threshold = max decoy sim.
    decoy_sims = [hdc.similarity(d, bundle) for d in decoy_atoms]
    decoy_max = max(decoy_sims) if decoy_sims else 0.0
    hits = 0
    for atom in true_atoms:
        s = hdc.similarity(atom, bundle)
        if s > decoy_max:
            hits += 1
    return hits / len(true_atoms)


# -----------------------------------------------------------------------
# Signal embedding: bundle bits → real-valued signal stream
# -----------------------------------------------------------------------

def bundle_to_signal(bundle: bytes) -> list[float]:
    """Embed bundle bits into a signal sequence.

    Each bit maps to ±1.0. Length = D_BITS samples. The bit-discrete
    structure is what carries the algebraic content; ANY filter that smooths
    across bits without preserving the discrete signature destroys content.
    """
    samples: list[float] = []
    for byte in bundle:
        for bit in range(8):
            samples.append(1.0 if ((byte >> bit) & 1) else -1.0)
    return samples


def signal_to_bundle(samples: list[float]) -> bytes:
    """Recover bundle bytes from signal via threshold-at-zero sign-decoding."""
    out = bytearray(len(samples) // 8)
    for i, s in enumerate(samples):
        if s > 0.0:
            out[i // 8] |= (1 << (i % 8))
    return bytes(out)


# -----------------------------------------------------------------------
# Noise model
# -----------------------------------------------------------------------

class XOSHIRO:
    """Deterministic PRNG (no numpy dependency). Box-Muller for Gaussian."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF
        if self.state == 0:
            self.state = 1

    def next_u64(self) -> int:
        # Simple SplitMix64.
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def uniform_01(self) -> float:
        return self.next_u64() / 2**64

    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        # Box-Muller pair, return one.
        u1 = max(self.uniform_01(), 1e-300)
        u2 = self.uniform_01()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + sigma * z


def add_gaussian_noise(
    samples: list[float], snr_db: float, rng: XOSHIRO
) -> list[float]:
    """Add zero-mean Gaussian noise at target SNR (dB).

    Signal power for ±1 samples is 1.0. Noise sigma = 10^(-snr_db/20).
    """
    sigma = 10.0 ** (-snr_db / 20.0)
    return [s + rng.gauss(0.0, sigma) for s in samples]


# -----------------------------------------------------------------------
# Filters: Kalman + alternatives (T6)
# -----------------------------------------------------------------------

def kalman_constant_velocity(
    measurements: list[float],
    sigma_proc: float = KALMAN_SIGMA_PROC_DEFAULT,
    sigma_meas: float | None = None,
) -> list[float]:
    """Standard constant-velocity Kalman filter (1D position + velocity state).

    State: x = [pos, vel]; F = [[1, dt], [0, 1]]; H = [1, 0]; Q = sigma_proc^2 * [[dt^4/4, dt^3/2], [dt^3/2, dt^2]] (white-acceleration); R = sigma_meas^2.

    Returns the filtered position estimates.

    This is the canonical BCI-pipeline Kalman model (Wu et al. 2006 inspired
    motor-decoder; Kim, Hochberg et al. BrainGate-class).
    """
    if sigma_meas is None:
        # Estimate from measurement variance (typical real-world choice).
        m = statistics.mean(measurements)
        var = sum((x - m) ** 2 for x in measurements) / max(len(measurements) - 1, 1)
        sigma_meas = math.sqrt(max(var, 1e-12))

    dt = KALMAN_DT
    # Initial state.
    x = [measurements[0], 0.0]
    # Initial covariance (large, uncertain start).
    P = [[1.0, 0.0], [0.0, 1.0]]
    # Process noise covariance (white-acceleration assumption).
    q = sigma_proc ** 2
    Q = [
        [q * dt**4 / 4.0, q * dt**3 / 2.0],
        [q * dt**3 / 2.0, q * dt**2],
    ]
    R = sigma_meas ** 2

    out: list[float] = []
    for z in measurements:
        # Predict.
        x_pred = [x[0] + dt * x[1], x[1]]
        # P_pred = F P F^T + Q
        # F = [[1, dt], [0, 1]]
        p00 = P[0][0] + dt * (P[1][0] + P[0][1]) + dt * dt * P[1][1]
        p01 = P[0][1] + dt * P[1][1]
        p10 = P[1][0] + dt * P[1][1]
        p11 = P[1][1]
        P_pred = [[p00 + Q[0][0], p01 + Q[0][1]],
                  [p10 + Q[1][0], p11 + Q[1][1]]]
        # Innovation.
        y = z - x_pred[0]
        S = P_pred[0][0] + R
        K0 = P_pred[0][0] / S
        K1 = P_pred[1][0] / S
        x = [x_pred[0] + K0 * y, x_pred[1] + K1 * y]
        # Update covariance.
        P = [
            [(1.0 - K0) * P_pred[0][0], (1.0 - K0) * P_pred[0][1]],
            [P_pred[1][0] - K1 * P_pred[0][0], P_pred[1][1] - K1 * P_pred[0][1]],
        ]
        out.append(x[0])
    return out


def median_filter(samples: list[float], window: int = 3) -> list[float]:
    """Rank-based median filter; structure-preserving."""
    half = window // 2
    out = []
    n = len(samples)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        out.append(statistics.median(samples[lo:hi]))
    return out


def no_filter(samples: list[float]) -> list[float]:
    """Pass-through; baseline for "raw noisy signal" comparison."""
    return list(samples)


def block_majority_filter(samples: list[float], block: int = 1) -> list[float]:
    """Block-aligned sign-majority filter (NEAREST-NEIGHBOUR SMOOTHING).

    For each sample, take majority sign of a [i-block, i+block] window.
    Despite being sign-quantised, this is STILL a spatial smoother — when
    bits are statistically independent (as in SHA-256-derived HDC atoms),
    a 3-sample majority flips the center bit ~25% of the time even with
    zero measurement noise. Included as a "smoothing without Gaussian
    machinery" baseline.
    """
    half = block
    out = []
    n = len(samples)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        s = sum(1 if x > 0 else -1 for x in samples[lo:hi])
        out.append(1.0 if s >= 0 else -1.0)
    return out


def per_bit_threshold_filter(samples: list[float]) -> list[float]:
    """Per-bit threshold-at-zero (HDC-AWARE structure-preserving filter).

    NO spatial window. Each sample independently quantised to its sign.
    Preserves the bit-discrete algebraic structure exactly — assumes no
    cross-bit correlation, matching the structure of SHA-256-derived
    HDC atoms.

    This represents what a *true* HDC-aware filter looks like: refuse to
    smooth across bits, because the bits ARE the algebraic content.

    For real BCI applications, this corresponds to per-channel quantisation
    against a calibrated threshold (e.g., spike-count > median over a
    short calibration window), with NO temporal smoothing across channels.
    """
    return [1.0 if s > 0.0 else -1.0 for s in samples]


# -----------------------------------------------------------------------
# Test harness
# -----------------------------------------------------------------------

@dataclass
class TestResult:
    test_id: str
    snr_db: float
    filter_name: str
    metric_name: str
    value: float
    notes: str = ""

    def as_record(self) -> dict:
        return {
            "spike": 174,
            "date": "2026-05-19",
            "test": self.test_id,
            "snr_db": self.snr_db,
            "filter": self.filter_name,
            "metric": self.metric_name,
            "value": self.value,
            "notes": self.notes,
        }


def hamming_bytes(a: bytes, b: bytes) -> int:
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def build_token_stream(n: int, prefix: bytes = b"spike174_tok") -> list[bytes]:
    """Deterministic content-addressed token stream."""
    return [prefix + f"_{i:06d}".encode() for i in range(n)]


def run_t1_t2_t3(records: list[TestResult]) -> None:
    """T1: Construct synthetic signal. T2: Kalman preservation. T3: Identity preservation."""
    tokens = build_token_stream(N_EVENTS)
    true_bundle, atoms, base_atom = stream_to_bundle(tokens)
    true_signal = bundle_to_signal(true_bundle)

    filters = {
        "no_filter": no_filter,
        "kalman_cv": kalman_constant_velocity,
        "median_w3": lambda s: median_filter(s, 3),
        "block_majority": lambda s: block_majority_filter(s, 1),
        "per_bit_threshold": per_bit_threshold_filter,
    }

    for snr_db in SNR_DB_GRID:
        rng = XOSHIRO(RNG_SEED ^ int(snr_db * 1000))
        noisy_signal = add_gaussian_noise(true_signal, snr_db, rng)

        for fname, ffn in filters.items():
            filt_signal = ffn(noisy_signal)
            recovered_bundle = signal_to_bundle(filt_signal)

            # T2.1: Bit-error rate vs true bundle.
            ham = hamming_bytes(true_bundle, recovered_bundle)
            ber = ham / (len(true_bundle) * 8)
            records.append(TestResult(
                "T2_ber", snr_db, fname, "bit_error_rate", ber,
                notes=f"hamming={ham}/{len(true_bundle)*8} bits",
            ))

            # T2.2: Reverse-decode fraction (semantic recovery).
            frac = reverse_decode_fraction(recovered_bundle, base_atom, tokens)
            records.append(TestResult(
                "T2_decode", snr_db, fname, "reverse_decode_fraction", frac,
                notes=f"n_tokens={len(tokens)}",
            ))

            # T3: Algebraic-identity recovery from filtered signal.
            # Setup: Encode TWO atoms a, b. Encode their bind c = a XOR b.
            # Pass each separately through the noise-and-filter pipeline.
            # Then test: does the recovered c'==a'XOR b' relationship hold?
            # This is the REAL test of "can we still recover algebra from
            # filtered signals?" — a XOR b = c is what binding gives us;
            # if the filter is content-preserving, a' XOR b' should equal c'.
            k = 137  # arbitrary shift
            if len(atoms) >= 2:
                a, b = atoms[0], atoms[1]
                c = hdc.bind(a, b)  # algebraic ground truth

                # Independent noise realisations per atom.
                rng_a = XOSHIRO(RNG_SEED ^ 0x1111 ^ int(snr_db * 1000) ^ hash(fname) % 65536)
                rng_b = XOSHIRO(RNG_SEED ^ 0x2222 ^ int(snr_db * 1000) ^ hash(fname) % 65536)
                rng_c = XOSHIRO(RNG_SEED ^ 0x3333 ^ int(snr_db * 1000) ^ hash(fname) % 65536)
                a_f = signal_to_bundle(ffn(add_gaussian_noise(bundle_to_signal(a), snr_db, rng_a)))
                b_f = signal_to_bundle(ffn(add_gaussian_noise(bundle_to_signal(b), snr_db, rng_b)))
                c_f = signal_to_bundle(ffn(add_gaussian_noise(bundle_to_signal(c), snr_db, rng_c)))

                # Algebraic recovery: how close is (a_f XOR b_f) to c_f?
                # Perfect filter: bit-exact identity. Destructive filter: bits drift.
                xor_ab = hdc.bind(a_f, b_f)
                # Hamming(xor_ab, c_f) is the test. If filter destroyed independent
                # bit patterns differently in a vs b vs c, the relationship breaks.
                rel_ber = hamming_bytes(xor_ab, c_f) / (len(c_f) * 8)
                records.append(TestResult(
                    "T3_algebra_recovery", snr_db, fname,
                    "bind_relationship_ber",
                    rel_ber,
                    notes=f"hamming(a_f^b_f, c_f)/D; 0=identity recovered, ~0.5=destroyed",
                ))

                # Also: permute-commute test on the filtered atoms.
                lhs2 = hdc.permute(hdc.bind(a_f, b_f), k)
                rhs2 = hdc.bind(hdc.permute(a_f, k), hdc.permute(b_f, k))
                # By math, these MUST be equal regardless of a_f, b_f content
                # (permute and XOR commute by definition). So this is sanity-
                # check, not new information.
                ident2_pass = (lhs2 == rhs2)
                records.append(TestResult(
                    "T3_sanity_permute_commute", snr_db, fname,
                    "bind_permute_commutes",
                    1.0 if ident2_pass else 0.0,
                    notes="mathematical identity; should always be 1.0",
                ))


def run_t4_class_N_rational(records: list[TestResult]) -> None:
    """T4: Class N rational cycle-order signature survives filtering?

    Class N / Class I rational cycle order: D / gcd(stride, D).

    We embed a known stride structure into the bundle by using a token stream
    where each token's content_to_shift produces a known periodic relationship.
    Then we measure whether the filter preserves the integer rational
    relationship vs smearing it.
    """
    # Pick a stride that creates a clean rational cycle order.
    # D = D_BITS = 8192. stride = 1024. cycle_order = D/gcd(1024, 8192) = 8.
    D = D_BITS
    stride = 1024
    expected_cycle_order = D // gcd(stride, D)

    # Build atoms by directly applying known shifts.
    base_seed = hashlib.sha256(b"spike174_t4_base").digest()
    base = bytearray()
    seed = base_seed
    while len(base) < D_BYTES:
        base.extend(seed)
        seed = hashlib.sha256(seed).digest()
    base_atom = bytes(base[:D_BYTES])

    # Compute orbit: apply stride repeatedly, hashed signature of each.
    def orbit_signature(atom: bytes, n_steps: int) -> tuple:
        sigs = []
        cur = atom
        for _ in range(n_steps):
            sigs.append(hashlib.sha256(cur).hexdigest()[:16])
            cur = hdc.permute(cur, stride)
        return tuple(sigs)

    true_orbit = orbit_signature(base_atom, expected_cycle_order * 2)
    # Cycle order = first index where signature repeats first element.
    def detect_cycle(orbit: tuple) -> int:
        first = orbit[0]
        for i in range(1, len(orbit)):
            if orbit[i] == first:
                return i
        return -1  # no cycle within window

    true_cycle = detect_cycle(true_orbit)
    records.append(TestResult(
        "T4_baseline", 0.0, "ground_truth", "cycle_order",
        float(true_cycle),
        notes=f"expected={expected_cycle_order} (D=8192, stride=1024)",
    ))

    # Now embed the atom into a noisy signal, filter, recover, recompute orbit.
    filters = {
        "no_filter": no_filter,
        "kalman_cv": kalman_constant_velocity,
        "median_w3": lambda s: median_filter(s, 3),
        "block_majority": lambda s: block_majority_filter(s, 1),
        "per_bit_threshold": per_bit_threshold_filter,
    }
    for snr_db in SNR_DB_GRID:
        for fname, ffn in filters.items():
            # T4a: Single-pass filter-then-orbit (what we had).
            sig = bundle_to_signal(base_atom)
            rng = XOSHIRO(RNG_SEED ^ int(snr_db * 1000) ^ hash(fname) % 65536)
            noisy = add_gaussian_noise(sig, snr_db, rng)
            filt = ffn(noisy)
            atom_recovered = signal_to_bundle(filt)
            ber_atom = hamming_bytes(base_atom, atom_recovered) / (len(base_atom) * 8)
            recov_orbit = orbit_signature(
                atom_recovered, expected_cycle_order * 2
            )
            recov_cycle = detect_cycle(recov_orbit)
            preserved = 1.0 if recov_cycle == true_cycle else 0.0
            records.append(TestResult(
                "T4_cycle_single_pass", snr_db, fname, "cycle_preserved",
                preserved,
                notes=f"recovered={recov_cycle} expected={true_cycle} atom_ber={ber_atom:.4f}",
            ))

            # T4b: Filter applied at each orbit step (real BCI scenario).
            # Each measurement of the underlying state passes through the filter
            # independently. We want to know: does the filtered-orbit still
            # repeat at cycle_order steps?
            cur = base_atom
            sigs_filtered = []
            for step in range(expected_cycle_order * 2):
                sig_step = bundle_to_signal(cur)
                rng_step = XOSHIRO(RNG_SEED ^ step ^ int(snr_db * 1000) ^ hash(fname) % 65536)
                noisy_step = add_gaussian_noise(sig_step, snr_db, rng_step)
                filt_step = ffn(noisy_step)
                cur_filt = signal_to_bundle(filt_step)
                sigs_filtered.append(hashlib.sha256(cur_filt).hexdigest()[:16])
                # Advance the TRUE orbit (not the filtered).
                cur = hdc.permute(cur, stride)
            # Detect cycle in filtered signatures: same-as-position-0 anywhere?
            first = sigs_filtered[0]
            filt_cycle = -1
            for i in range(1, len(sigs_filtered)):
                if sigs_filtered[i] == first:
                    filt_cycle = i
                    break
            preserved_b = 1.0 if filt_cycle == true_cycle else 0.0
            records.append(TestResult(
                "T4_cycle_per_step_filter", snr_db, fname, "cycle_preserved",
                preserved_b,
                notes=f"per_step_filter recovered={filt_cycle} expected={true_cycle}",
            ))

            # T4c: Coarser cycle preservation — does the filtered orbit match
            # the true orbit's similarity profile? Compute similarity matrix
            # between filtered atoms and true atoms; cycle structure emerges
            # as off-diagonal peaks at multiples of cycle_order.
            # If filter destroys the substrate-portable algebra, the diagonal
            # collapses to noise floor.
            cur = base_atom
            true_atoms_orbit = []
            for _ in range(expected_cycle_order):
                true_atoms_orbit.append(cur)
                cur = hdc.permute(cur, stride)
            # Average similarity of filtered_atom[i] to true_atom[i].
            on_diag_sims = []
            for i, true_a in enumerate(true_atoms_orbit):
                sig_i = bundle_to_signal(true_a)
                rng_i = XOSHIRO(RNG_SEED ^ i ^ int(snr_db * 1000) ^ hash(fname) % 65536)
                noisy_i = add_gaussian_noise(sig_i, snr_db, rng_i)
                filt_i = ffn(noisy_i)
                filt_atom_i = signal_to_bundle(filt_i)
                on_diag_sims.append(hdc.similarity(filt_atom_i, true_a))
            avg_on_diag = sum(on_diag_sims) / len(on_diag_sims)
            records.append(TestResult(
                "T4_orbit_similarity", snr_db, fname,
                "mean_on_diag_similarity",
                avg_on_diag,
                notes=f"avg sim(filtered_orbit[i], true_orbit[i]); 1.0=preserved, 0=destroyed",
            ))


def run_t5_t6(records: list[TestResult]) -> None:
    """T5/T6: combined — alternatives comparison aggregated from T2/T3/T4.

    T5 is implicit: if Kalman destroys cycle-period signature (T4) and bit
    structure (T2), then the substrate-natural shadow-projection (which IS
    the cycle period / bit pattern, per the 7th shadow-stance candidate)
    is destroyed. We aggregate.
    """
    pass  # Aggregation done in summary; no separate test needed.


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main() -> None:
    records: list[TestResult] = []
    print("# Spike #174 — Kalman vs form-function-rotation cross-binning")
    print(f"# D={D_BITS} bits, N_events={N_EVENTS}, SNR grid={SNR_DB_GRID}")

    print("\n## T1/T2/T3: Signal preservation + algebraic identity")
    run_t1_t2_t3(records)

    print("\n## T4: Class N rational cycle-order signature")
    run_t4_class_N_rational(records)

    print("\n## T5/T6: Substrate-natural shadow + alternatives (aggregated)")
    run_t5_t6(records)

    # Write NDJSON.
    out_path = HERE.parent / "spike174_records_2026-05-19.ndjson"
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r.as_record(), separators=(",", ":")) + "\n")
    print(f"\nWrote {len(records)} records -> {out_path.name}")

    # Print summary table.
    print("\n## Summary by filter × SNR (averaged metrics)")
    by_key: dict[tuple, list[float]] = {}
    for r in records:
        key = (r.test_id, r.filter_name, r.snr_db)
        by_key.setdefault(key, []).append(r.value)

    # Pretty table for T2/T3/T4 metrics.
    for test_id in (
        "T2_ber", "T2_decode",
        "T3_algebra_recovery", "T3_sanity_permute_commute",
        "T4_cycle_single_pass", "T4_cycle_per_step_filter",
        "T4_orbit_similarity",
    ):
        print(f"\n### {test_id}")
        print(f"{'filter':<20} | " + " | ".join(
            f"SNR={s:+5.1f}dB" for s in SNR_DB_GRID))
        for fname in ("no_filter", "kalman_cv", "median_w3", "block_majority",
                      "per_bit_threshold"):
            row_vals = []
            for s in SNR_DB_GRID:
                vals = by_key.get((test_id, fname, s), [])
                if vals:
                    row_vals.append(f"{sum(vals)/len(vals):10.4f}")
                else:
                    row_vals.append("    -     ")
            print(f"{fname:<20} | " + " | ".join(row_vals))


if __name__ == "__main__":
    main()
