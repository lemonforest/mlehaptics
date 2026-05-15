#!/usr/bin/env python3
"""Spike #24 bonus 6 — RNG constructive probe.

Builds three candidate RNGs from project primitive vocabulary and benchmarks
them against NIST SP 800-22-style statistical tests (frequency / runs /
serial / approximate-entropy / cumulative-sums). Emits one NDJSON record per
construction per test.

Constructions:
  RNG1 — HMAC-DRBG over SHA-256 (Class A composed with Class B).
         Standard CSPRNG construction per NIST SP 800-90A.
  RNG2 — LFSR on GF(2^256) (Class I + Class L).
         Cyclic-group action + Laplacian-style feedback.
  RNG3 — Mass-action-oscillator-driven extractor (Class K + Class A).
         Brusselator trajectory -> bit extraction via SHA-256 of state windows.
         Probes whether Kepler-shape integer-harmonic structure can be
         TURNED INTO RNG rather than just observed in.

Plus baselines:
  RNG0a — os.urandom (system entropy; "true-random" baseline within
          classical-machine reach).
  RNG0b — Pure deterministic counter (zero-entropy lower bound; should fail
          every test).
  RNG0c — numpy default_rng (PCG64; high-quality non-cryptographic baseline).

Tests are reduced-scope versions of NIST SP 800-22:
  T1 — monobit frequency
  T2 — runs (number of runs vs expectation)
  T3 — block frequency (M=64)
  T4 — cumulative sums
  T5 — serial 2-bit pattern frequency
  T6 — approximate-entropy ApEn(m=2)

Per [[feedback_trauma_informed_defensive_scope]]: methodological inquiry only.
No recommendations of these constructions for production use.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import struct
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).name
TODAY = "2026-05-15"
SEED = 20260515
N_BITS = 2 ** 17  # 131,072 bits per construction = 16 KiB
OUT = Path(__file__).with_suffix(".ndjson")


# =========================================================================
# RNG1 — HMAC-DRBG over SHA-256 (Class A composed with Class B)
# =========================================================================
class HmacDrbgSha256:
    """Minimal HMAC-DRBG per NIST SP 800-90A.

    Per [[feedback_trauma_informed_defensive_scope]]: this is a reference
    implementation for the methodological probe ONLY; not for production.
    """

    def __init__(self, seed_bytes: bytes) -> None:
        # Initial K and V per SP 800-90A 10.1.2.2.
        self.K = b"\x00" * 32
        self.V = b"\x01" * 32
        self._update(seed_bytes)

    def _hmac(self, key: bytes, data: bytes) -> bytes:
        return hmac.new(key, data, hashlib.sha256).digest()

    def _update(self, provided: bytes) -> None:
        self.K = self._hmac(self.K, self.V + b"\x00" + provided)
        self.V = self._hmac(self.K, self.V)
        if provided:
            self.K = self._hmac(self.K, self.V + b"\x01" + provided)
            self.V = self._hmac(self.K, self.V)

    def generate(self, nbytes: int) -> bytes:
        out = b""
        while len(out) < nbytes:
            self.V = self._hmac(self.K, self.V)
            out += self.V
        self._update(b"")  # backtrack-resistance reseed-of-self
        return out[:nbytes]


def rng1_hmac_drbg(n_bits: int, seed: int) -> bytes:
    drbg = HmacDrbgSha256(seed.to_bytes(8, "big") + b"spike24_rng1_hmac_drbg")
    return drbg.generate(n_bits // 8)


# =========================================================================
# RNG2 — LFSR on GF(2^256) (Class I + Class L)
# =========================================================================
def rng2_lfsr_gf2_256(n_bits: int, seed: int) -> bytes:
    """LFSR over a 256-bit state with a dense tap set.

    Class I: cyclic-group shift register (period <= 2^256 - 1).
    Class L: tap polynomial defines feedback graph (Laplacian-style row).

    Tap polynomial chosen for non-trivial spread, not maximum length proven:
    bits 0, 1, 3, 5, 12, 27, 64, 100, 127, 200, 255.
    """
    # Seed expansion: SHA-256(seed_bytes) gives 256 initial bits.
    seed_bytes = seed.to_bytes(8, "big") + b"spike24_rng2_lfsr"
    state_int = int.from_bytes(hashlib.sha256(seed_bytes).digest(), "big")
    if state_int == 0:
        state_int = 1  # avoid stuck-at-zero

    taps = (0, 1, 3, 5, 12, 27, 64, 100, 127, 200, 255)
    out = bytearray()
    bits_per_byte = 8
    n_bytes = n_bits // 8

    # Build per-byte output by clocking the LFSR 8 times per byte.
    for _ in range(n_bytes):
        byte = 0
        for _bit in range(bits_per_byte):
            # Feedback bit = XOR of taps.
            fb = 0
            for t in taps:
                fb ^= (state_int >> t) & 1
            # Output the bit being shifted out (bit 0).
            byte = (byte << 1) | (state_int & 1)
            # Shift right, insert feedback at top.
            state_int = (state_int >> 1) | (fb << 255)
        out.append(byte)
    return bytes(out)


# =========================================================================
# RNG3 — Mass-action-oscillator-driven extractor (Class K + Class A)
# =========================================================================
def rng3_brusselator_sha(n_bits: int, seed: int) -> bytes:
    """Brusselator trajectory -> bit extraction via SHA-256 of state windows.

    Class K: mass-action oscillator (the pin-slot integer-harmonic of Spike #24
    Phase 9.2 / Phase 15 substrate; Kepler-shape in the spectrum).
    Class A: SHA-256 extracts uniform bits from trajectory windows.

    This is the most interesting construction: tests whether the
    Kepler-shape integer-harmonic structure persists into the SHA-256-extracted
    output as residue, OR whether the extractor's avalanche destroys it.

    Brusselator ODE:
      du/dt = A - (B+1)u + u^2 v
      dv/dt = Bu - u^2 v
    For A=1, B=3 the system is in oscillatory regime with limit-cycle period
    ~7 time units. Integrate, sample at fixed dt, window into chunks, hash.
    """
    rng_seed = np.random.default_rng(seed ^ 0x42424242)  # init perturbation
    A, B = 1.0, 3.0
    dt = 0.001
    # Initial state on attractor neighborhood; small jitter from seed.
    u = 1.0 + 1e-4 * rng_seed.standard_normal()
    v = 1.0 + 1e-4 * rng_seed.standard_normal()

    # Per window: 4096 samples = ~4 limit-cycle periods, packed as bytes,
    # SHA-256 -> 32 bytes of output. So ~128 windows for 16 KiB.
    window_samples = 4096
    n_bytes = n_bits // 8
    n_windows = (n_bytes + 31) // 32

    out = bytearray()
    for _ in range(n_windows):
        # Pack (u, v) trajectory as float64 bytes; window_samples points x 16 bytes.
        buf = bytearray(window_samples * 16)
        for i in range(window_samples):
            # RK4 step.
            def f(uu, vv):
                return (A - (B + 1) * uu + uu * uu * vv,
                        B * uu - uu * uu * vv)
            k1u, k1v = f(u, v)
            k2u, k2v = f(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
            k3u, k3v = f(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
            k4u, k4v = f(u + dt * k3u, v + dt * k3v)
            u = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
            v = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
            struct.pack_into("dd", buf, i * 16, u, v)
        digest = hashlib.sha256(bytes(buf)).digest()
        out.extend(digest)
    return bytes(out[:n_bytes])


# Bonus: rng3 RAW — Brusselator trajectory without SHA-256 extraction.
def rng3_raw_brusselator(n_bits: int, seed: int) -> bytes:
    """Brusselator trajectory bits WITHOUT the SHA-256 extraction step.

    Probes the user's question directly: does the Kepler-shape structure
    persist as residue when we DON'T apply the avalanche-extractor? Expected
    to show statistical structure (Class K's integer-harmonic signature).
    """
    rng_seed = np.random.default_rng(seed ^ 0x42424242)
    A, B = 1.0, 3.0
    dt = 0.001
    u = 1.0 + 1e-4 * rng_seed.standard_normal()
    v = 1.0 + 1e-4 * rng_seed.standard_normal()

    n_bytes = n_bits // 8
    out = bytearray()
    # Take LSB of round(u * 2^30) mod 256 per step; sample every 4 steps to
    # decorrelate fixed-dt integration noise.
    samples_needed = n_bytes
    samples = 0
    while samples < samples_needed:
        for _stride in range(4):
            def f(uu, vv):
                return (A - (B + 1) * uu + uu * uu * vv,
                        B * uu - uu * uu * vv)
            k1u, k1v = f(u, v)
            k2u, k2v = f(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
            k3u, k3v = f(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
            k4u, k4v = f(u + dt * k3u, v + dt * k3v)
            u = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
            v = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
        bits = int(round(u * (1 << 30))) ^ int(round(v * (1 << 30)))
        out.append(bits & 0xFF)
        samples += 1
    return bytes(out[:n_bytes])


# =========================================================================
# Baselines
# =========================================================================
def rng0a_urandom(n_bits: int, seed: int) -> bytes:
    # System entropy. seed is ignored (true-random baseline).
    return os.urandom(n_bits // 8)


def rng0b_counter(n_bits: int, seed: int) -> bytes:
    # Pure deterministic counter; zero entropy; fails every test.
    n_bytes = n_bits // 8
    out = bytearray()
    counter = seed & 0xFFFFFFFF
    for i in range(n_bytes // 4):
        out.extend((counter + i).to_bytes(4, "big"))
    while len(out) < n_bytes:
        out.append(0)
    return bytes(out[:n_bytes])


def rng0c_numpy_pcg64(n_bits: int, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    return rng.bytes(n_bits // 8)


# =========================================================================
# Tests — reduced NIST SP 800-22 subset
# =========================================================================
def bits_from_bytes(buf: bytes) -> np.ndarray:
    """Unpack to a flat int8 array of 0/1."""
    arr = np.frombuffer(buf, dtype=np.uint8)
    bits = np.unpackbits(arr)
    return bits.astype(np.int8)


def test_monobit_frequency(bits: np.ndarray) -> dict:
    """T1: monobit frequency. Pass if p_value > 0.01."""
    n = len(bits)
    s = int(np.sum(2 * bits - 1))  # +1/-1 sum
    s_obs = abs(s) / math.sqrt(n)
    p = math.erfc(s_obs / math.sqrt(2))
    return {
        "test": "T1_monobit",
        "p_value": p,
        "pass": bool(p > 0.01),
        "ones_count": int(bits.sum()),
        "zeros_count": int(n - bits.sum()),
        "expected_fraction": 0.5,
        "observed_fraction": float(bits.sum() / n),
    }


def test_runs(bits: np.ndarray) -> dict:
    """T2: number of runs. Pass if p_value > 0.01."""
    n = len(bits)
    pi = bits.mean()
    if abs(pi - 0.5) >= 2.0 / math.sqrt(n):
        return {"test": "T2_runs", "p_value": 0.0, "pass": False,
                "note": "pre-test failed (frequency too skewed)"}
    v_obs = 1 + int(np.sum(bits[1:] != bits[:-1]))
    denom = 2.0 * math.sqrt(2 * n) * pi * (1 - pi)
    p = math.erfc(abs(v_obs - 2 * n * pi * (1 - pi)) / denom)
    return {
        "test": "T2_runs",
        "p_value": p,
        "pass": bool(p > 0.01),
        "v_obs": int(v_obs),
    }


def test_block_frequency(bits: np.ndarray, M: int = 64) -> dict:
    """T3: block frequency. Pass if p_value > 0.01."""
    n = len(bits)
    N = n // M
    if N == 0:
        return {"test": "T3_block_freq", "p_value": 0.0, "pass": False}
    pis = []
    for i in range(N):
        block = bits[i * M:(i + 1) * M]
        pis.append(block.mean())
    pis = np.array(pis)
    chi_sq = 4.0 * M * float(np.sum((pis - 0.5) ** 2))
    # incomplete gamma upper Q(N/2, chi_sq/2)
    p = upper_incomplete_gamma_regularised(N / 2.0, chi_sq / 2.0)
    return {
        "test": "T3_block_freq",
        "p_value": p,
        "pass": bool(p > 0.01),
        "M": M,
        "N_blocks": int(N),
        "chi_sq": float(chi_sq),
    }


def test_cumulative_sums(bits: np.ndarray) -> dict:
    """T4: cumulative sums (forward). Pass if p_value > 0.01."""
    n = len(bits)
    x = 2 * bits.astype(np.int64) - 1
    s = np.cumsum(x)
    z = int(np.max(np.abs(s)))
    if z == 0:
        return {"test": "T4_cusum_fwd", "p_value": 1.0, "pass": True, "z": 0}
    # NIST formula
    sqrt_n = math.sqrt(n)
    s_sum1 = 0.0
    k_start_a = int((-n / z + 1) / 4)
    k_end_a = int((n / z - 1) / 4)
    for k in range(k_start_a, k_end_a + 1):
        a = (4 * k + 1) * z / sqrt_n
        b = (4 * k - 1) * z / sqrt_n
        s_sum1 += standard_normal_cdf(a) - standard_normal_cdf(b)
    k_start_b = int((-n / z - 3) / 4)
    k_end_b = int((n / z - 1) / 4)
    s_sum2 = 0.0
    for k in range(k_start_b, k_end_b + 1):
        a = (4 * k + 3) * z / sqrt_n
        b = (4 * k + 1) * z / sqrt_n
        s_sum2 += standard_normal_cdf(a) - standard_normal_cdf(b)
    p = 1.0 - s_sum1 + s_sum2
    p = max(0.0, min(1.0, p))
    return {
        "test": "T4_cusum_fwd",
        "p_value": p,
        "pass": bool(p > 0.01),
        "z_max": int(z),
    }


def test_serial_2bit(bits: np.ndarray) -> dict:
    """T5: serial 2-bit pattern frequency (chi-square on 2-bit patterns)."""
    n = len(bits) - 1
    pairs = bits[:-1] * 2 + bits[1:]
    counts = np.bincount(pairs, minlength=4).astype(np.float64)
    expected = n / 4.0
    chi_sq = float(np.sum((counts - expected) ** 2 / expected))
    p = upper_incomplete_gamma_regularised(1.5, chi_sq / 2.0)
    return {
        "test": "T5_serial_2bit",
        "p_value": p,
        "pass": bool(p > 0.01),
        "pattern_counts": counts.astype(int).tolist(),
        "expected_per_pattern": float(expected),
        "chi_sq": float(chi_sq),
    }


def test_approximate_entropy(bits: np.ndarray, m: int = 2) -> dict:
    """T6: approximate entropy ApEn(m). Pass if p_value > 0.01."""
    n = len(bits)
    if m + 1 > 16:
        raise ValueError("m too large")

    def phi(mm: int) -> float:
        # count m-bit window frequencies with wraparound
        c = np.zeros(2 ** mm, dtype=np.int64)
        for i in range(n):
            idx = 0
            for j in range(mm):
                idx = (idx << 1) | int(bits[(i + j) % n])
            c[idx] += 1
        cm = c / n
        # phi = sum c_m * log c_m
        return float(np.sum(np.where(cm > 0, cm * np.log(cm), 0.0)))

    apen = phi(m) - phi(m + 1)
    chi_sq = 2.0 * n * (math.log(2) - apen)
    p = upper_incomplete_gamma_regularised(2 ** (m - 1), chi_sq / 2.0)
    return {
        "test": "T6_apen_m2",
        "p_value": p,
        "pass": bool(p > 0.01),
        "apen": float(apen),
        "chi_sq": float(chi_sq),
    }


# =========================================================================
# Numerical helpers (stdlib + scipy mimicked here to avoid scipy dependency)
# =========================================================================
def standard_normal_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def upper_incomplete_gamma_regularised(a: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(a, x). Returns NIST-style p-value.

    For the NIST SP 800-22 tests we need Q(N/2, chi^2/2). Uses series + cf
    standard implementation.
    """
    if x < 0 or a <= 0:
        return 0.0
    if x == 0:
        return 1.0
    if x < a + 1.0:
        # series for P, return 1 - P
        gln = math.lgamma(a)
        ap = a
        s = 1.0 / a
        term = s
        for _i in range(1, 1000):
            ap += 1.0
            term *= x / ap
            s += term
            if abs(term) < abs(s) * 1e-15:
                break
        p_lower = s * math.exp(-x + a * math.log(x) - gln)
        return max(0.0, min(1.0, 1.0 - p_lower))
    else:
        # continued fraction for Q
        gln = math.lgamma(a)
        b = x + 1.0 - a
        c = 1e30
        d = 1.0 / b
        h = d
        for i in range(1, 1000):
            an = -i * (i - a)
            b += 2.0
            d = an * d + b
            if abs(d) < 1e-30:
                d = 1e-30
            c = b + an / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < 1e-15:
                break
        return max(0.0, min(1.0, math.exp(-x + a * math.log(x) - gln) * h))


# =========================================================================
# Driver
# =========================================================================
def write_record(records: list, **kw) -> None:
    rec = dict(kw)
    rec.setdefault("date", TODAY)
    rec.setdefault("spike", "spike_24_bonus_rng_1d_time")
    rec.setdefault("script", SCRIPT)
    rec.setdefault("created_at_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    records.append(rec)


def main() -> int:
    records: list[dict] = []

    constructions = [
        ("RNG0a_urandom", rng0a_urandom, "true-random baseline (os.urandom)",
         "Class — substrate-external (kernel entropy pool)"),
        ("RNG0b_counter", rng0b_counter, "zero-entropy baseline (deterministic counter)",
         "Class I trivial (cyclic-group step-by-1)"),
        ("RNG0c_pcg64", rng0c_numpy_pcg64, "non-cryptographic baseline (numpy PCG64)",
         "Class I + Class L (LCG-style permutation)"),
        ("RNG1_hmac_drbg", rng1_hmac_drbg, "HMAC-DRBG over SHA-256",
         "Class A composed with Class B (NIST SP 800-90A)"),
        ("RNG2_lfsr_gf2_256", rng2_lfsr_gf2_256, "LFSR on GF(2^256)",
         "Class I (cyclic-group shift) + Class L (tap polynomial = Laplacian-style feedback)"),
        ("RNG3_brusselator_sha256", rng3_brusselator_sha, "Brusselator trajectory + SHA-256 extractor",
         "Class K (mass-action / Kepler-shape) composed with Class A (SHA-256 avalanche)"),
        ("RNG3_brusselator_raw", rng3_raw_brusselator, "Brusselator LSB sampling (NO extractor)",
         "Class K (mass-action / Kepler-shape) alone, no extractor"),
    ]

    for name, fn, description, classification in constructions:
        write_record(records,
                     phase="A_construction",
                     name=name,
                     description=description,
                     classification=classification)
        print(f"[Build] {name} ...", flush=True)
        data = fn(N_BITS, SEED)
        assert len(data) == N_BITS // 8, f"{name} produced {len(data)} bytes; expected {N_BITS // 8}"
        write_record(records,
                     phase="B_buffer_summary",
                     name=name,
                     n_bits=N_BITS,
                     n_bytes=len(data),
                     first_8_hex=data[:8].hex(),
                     last_8_hex=data[-8:].hex(),
                     sha256_of_buffer=hashlib.sha256(data).hexdigest())

        # Run tests on this buffer.
        bits = bits_from_bytes(data)
        for test_fn in (test_monobit_frequency,
                        test_runs,
                        test_block_frequency,
                        test_cumulative_sums,
                        test_serial_2bit,
                        test_approximate_entropy):
            res = test_fn(bits)
            print(f"  {res['test']}: p={res['p_value']:.6f} pass={res['pass']}", flush=True)
            write_record(records,
                         phase="C_test_result",
                         name=name,
                         **res)

    # Per-construction summary: how many of 6 tests pass.
    by_name: dict[str, list[bool]] = {}
    for r in records:
        if r.get("phase") == "C_test_result":
            by_name.setdefault(r["name"], []).append(bool(r["pass"]))
    for name, passes in by_name.items():
        write_record(records,
                     phase="D_summary",
                     name=name,
                     n_tests=len(passes),
                     n_pass=int(sum(passes)),
                     pass_rate=float(sum(passes) / len(passes)) if passes else 0.0)

    with OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True))
            fh.write("\n")
    print(f"\n[Done] {len(records)} records -> {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
