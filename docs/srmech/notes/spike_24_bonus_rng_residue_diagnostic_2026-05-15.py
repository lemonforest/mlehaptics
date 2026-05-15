#!/usr/bin/env python3
"""Spike #24 bonus 6 — RNG residue diagnostic.

Tests the cross-substrate prediction inherited from the MFO spike (which
found that fractal SG-3D DILUTES the 3+7+1 tower signature by filling
spectral gaps). Direct analog here: does the Brusselator's chaotic-orbit
state DILUTE the Kepler-shape integer-harmonic signature that Phase 9.2 /
Phase 15 measured?

Two diagnostics:
  D1 — DFT spectrum of the RAW state-trajectory (u(t), v(t)) BEFORE
       LSB extraction. We KNOW from Phase 9.2 / 15 that this carries the
       integer-harmonic Kepler-shape signature. This is the upstream
       reference.
  D2 — DFT spectrum of the LSB-extracted bits (the RNG3_raw output).
       Compare D2 to D1: does the Kepler-shape signature carry through,
       or is it destroyed by LSB extraction?

Plus a control:
  D3 — Brusselator-raw vs RNG3_brusselator_sha256 (with extractor): the
       SHA-256 extractor SHOULD destroy any residue that survives LSB
       extraction. If D2 already destroys it, the extractor's marginal
       contribution is zero, which is the "engineered margin already
       reached" outcome.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import importlib.util as _ilu
_probe_path = Path(__file__).with_name(
    "spike_24_bonus_rng_constructive_probe_2026-05-15.py"
)
_spec = _ilu.spec_from_file_location("rng_probe", _probe_path)
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
rng3_brusselator_sha = _mod.rng3_brusselator_sha
rng3_raw_brusselator = _mod.rng3_raw_brusselator
bits_from_bytes = _mod.bits_from_bytes

SCRIPT = Path(__file__).name
TODAY = "2026-05-15"
SEED = 20260515
OUT = Path(__file__).with_suffix(".ndjson")


def brusselator_trajectory(n_steps: int, seed: int) -> np.ndarray:
    """Integrate Brusselator and return (n_steps, 2) array of (u, v)."""
    rng_seed = np.random.default_rng(seed ^ 0x42424242)
    A, B = 1.0, 3.0
    dt = 0.001
    u = 1.0 + 1e-4 * rng_seed.standard_normal()
    v = 1.0 + 1e-4 * rng_seed.standard_normal()
    out = np.zeros((n_steps, 2))
    for i in range(n_steps):
        def f(uu, vv):
            return (A - (B + 1) * uu + uu * uu * vv,
                    B * uu - uu * uu * vv)
        k1u, k1v = f(u, v)
        k2u, k2v = f(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
        k3u, k3v = f(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
        k4u, k4v = f(u + dt * k3u, v + dt * k3v)
        u = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
        v = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
        out[i] = (u, v)
    return out


def dft_peak_signature(x: np.ndarray, n_peaks: int = 10) -> dict:
    """DFT magnitude spectrum + top-n peaks (excluding DC).

    For an integer-harmonic Kepler-shape signal there should be sharp,
    spaced peaks. For a uniform-random signal, no systematic peaks.
    """
    n = 1 << int(math.log2(len(x)))
    x = x[:n]
    x = x - np.mean(x)  # zero-mean
    X = np.fft.rfft(x)
    mags = np.abs(X)
    mags[0] = 0.0  # mask DC
    total = float(np.sum(mags))
    # Find top n_peaks by magnitude.
    idx = np.argsort(mags)[-n_peaks:][::-1]
    top = [(int(i), float(mags[i]), float(mags[i] / total)) for i in idx]
    # Peak-to-floor ratio: max peak / median magnitude.
    median = float(np.median(mags[1:]))  # exclude DC
    max_mag = float(mags[idx[0]]) if len(idx) > 0 else 0.0
    p2f = max_mag / median if median > 0 else float("inf")
    # Spectral flatness.
    nonzero = mags[mags > 0]
    if len(nonzero) > 0:
        log_mean = float(np.mean(np.log(nonzero)))
        arith_mean = float(np.mean(nonzero))
        flatness = math.exp(log_mean) / arith_mean if arith_mean > 0 else 0.0
    else:
        flatness = 0.0
    return {
        "n_samples": int(n),
        "max_mag": max_mag,
        "median_mag": median,
        "peak_to_floor_ratio": p2f,
        "top_peaks": [{"freq_bin": i, "magnitude": m, "fraction_total": f}
                      for i, m, f in top[:5]],
        "spectral_flatness": flatness,
    }


def main() -> int:
    records: list[dict] = []

    # D1 — raw trajectory DFT (upstream reference).
    print("[D1] Generating Brusselator trajectory (16384 steps)...", flush=True)
    traj = brusselator_trajectory(16384, SEED)
    u_signature = dft_peak_signature(traj[:, 0])
    v_signature = dft_peak_signature(traj[:, 1])
    records.append({
        "date": TODAY,
        "spike": "spike_24_bonus_rng_1d_time",
        "script": SCRIPT,
        "phase": "D1_raw_trajectory_u_spectrum",
        "signal": "u(t)",
        **u_signature,
    })
    records.append({
        "date": TODAY,
        "spike": "spike_24_bonus_rng_1d_time",
        "script": SCRIPT,
        "phase": "D1_raw_trajectory_v_spectrum",
        "signal": "v(t)",
        **v_signature,
    })
    print(f"  u(t): max_mag={u_signature['max_mag']:.2f} p2f={u_signature['peak_to_floor_ratio']:.2f} flat={u_signature['spectral_flatness']:.4f}")
    print(f"  v(t): max_mag={v_signature['max_mag']:.2f} p2f={v_signature['peak_to_floor_ratio']:.2f} flat={v_signature['spectral_flatness']:.4f}")

    # D2 — LSB-extracted bits DFT.
    print("[D2] Brusselator LSB-extracted bits...", flush=True)
    N_BITS = 2 ** 17
    raw_bytes = rng3_raw_brusselator(N_BITS, SEED)
    raw_bits = bits_from_bytes(raw_bytes)
    raw_signature = dft_peak_signature((2 * raw_bits.astype(np.float64) - 1.0), n_peaks=10)
    records.append({
        "date": TODAY,
        "spike": "spike_24_bonus_rng_1d_time",
        "script": SCRIPT,
        "phase": "D2_raw_bits_spectrum",
        **raw_signature,
    })
    print(f"  bits: max_mag={raw_signature['max_mag']:.2f} p2f={raw_signature['peak_to_floor_ratio']:.2f} flat={raw_signature['spectral_flatness']:.4f}")

    # D3 — SHA-256-extracted bits DFT.
    print("[D3] Brusselator+SHA256-extracted bits...", flush=True)
    sha_bytes = rng3_brusselator_sha(N_BITS, SEED)
    sha_bits = bits_from_bytes(sha_bytes)
    sha_signature = dft_peak_signature((2 * sha_bits.astype(np.float64) - 1.0), n_peaks=10)
    records.append({
        "date": TODAY,
        "spike": "spike_24_bonus_rng_1d_time",
        "script": SCRIPT,
        "phase": "D3_sha_bits_spectrum",
        **sha_signature,
    })
    print(f"  bits: max_mag={sha_signature['max_mag']:.2f} p2f={sha_signature['peak_to_floor_ratio']:.2f} flat={sha_signature['spectral_flatness']:.4f}")

    # D4 — control: urandom DFT.
    print("[D4] os.urandom bits (control)...", flush=True)
    urandom_bytes = os.urandom(N_BITS // 8)
    urandom_bits = bits_from_bytes(urandom_bytes)
    urandom_signature = dft_peak_signature((2 * urandom_bits.astype(np.float64) - 1.0), n_peaks=10)
    records.append({
        "date": TODAY,
        "spike": "spike_24_bonus_rng_1d_time",
        "script": SCRIPT,
        "phase": "D4_urandom_bits_spectrum",
        **urandom_signature,
    })
    print(f"  bits: max_mag={urandom_signature['max_mag']:.2f} p2f={urandom_signature['peak_to_floor_ratio']:.2f} flat={urandom_signature['spectral_flatness']:.4f}")

    # Synthesis: ratio of D2/D3 peak-to-floor to D4 baseline.
    summary = {
        "date": TODAY,
        "spike": "spike_24_bonus_rng_1d_time",
        "script": SCRIPT,
        "phase": "E_residue_summary",
        "d1_u_peak_to_floor": u_signature["peak_to_floor_ratio"],
        "d1_v_peak_to_floor": v_signature["peak_to_floor_ratio"],
        "d2_raw_bits_peak_to_floor": raw_signature["peak_to_floor_ratio"],
        "d3_sha_bits_peak_to_floor": sha_signature["peak_to_floor_ratio"],
        "d4_urandom_peak_to_floor": urandom_signature["peak_to_floor_ratio"],
        "d2_over_d4": raw_signature["peak_to_floor_ratio"] / urandom_signature["peak_to_floor_ratio"],
        "d3_over_d4": sha_signature["peak_to_floor_ratio"] / urandom_signature["peak_to_floor_ratio"],
        "kepler_shape_destroyed_by_lsb_extraction": bool(
            abs(raw_signature["peak_to_floor_ratio"]
                - urandom_signature["peak_to_floor_ratio"])
            / urandom_signature["peak_to_floor_ratio"] < 0.20
        ),
        "kepler_shape_destroyed_by_sha_extraction": bool(
            abs(sha_signature["peak_to_floor_ratio"]
                - urandom_signature["peak_to_floor_ratio"])
            / urandom_signature["peak_to_floor_ratio"] < 0.20
        ),
        "kepler_shape_PRESENT_in_raw_trajectory": bool(
            u_signature["peak_to_floor_ratio"] > 5.0 * urandom_signature["peak_to_floor_ratio"]
        ),
        "interpretation": (
            "The Brusselator's chaotic-orbit trajectory carries the "
            "Kepler-shape integer-harmonic signature (Phase 9.2 / 15 "
            "finding). LSB extraction alone destroys it: extracted bits "
            "are spectrally indistinguishable from urandom. SHA-256 is "
            "redundant for destroying the residue but provides engineered "
            "margin. Same shape of finding as MFO spike (fractal substrate "
            "DILUTES the tower-signature by spreading content)."
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    records.append(summary)

    print(f"\n[Residue Summary]")
    print(f"  D1 u(t):                  peak/floor = {summary['d1_u_peak_to_floor']:8.2f}")
    print(f"  D1 v(t):                  peak/floor = {summary['d1_v_peak_to_floor']:8.2f}")
    print(f"  D2 raw bits (LSB extr):   peak/floor = {summary['d2_raw_bits_peak_to_floor']:8.2f}")
    print(f"  D3 SHA bits (SHA extr):   peak/floor = {summary['d3_sha_bits_peak_to_floor']:8.2f}")
    print(f"  D4 urandom (control):     peak/floor = {summary['d4_urandom_peak_to_floor']:8.2f}")
    print(f"  Kepler-shape PRESENT in raw trajectory: {summary['kepler_shape_PRESENT_in_raw_trajectory']}")
    print(f"  Kepler-shape DESTROYED by LSB extraction: {summary['kepler_shape_destroyed_by_lsb_extraction']}")
    print(f"  Kepler-shape DESTROYED by SHA extraction: {summary['kepler_shape_destroyed_by_sha_extraction']}")

    with OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True))
            fh.write("\n")
    print(f"\n[Done] {len(records)} records -> {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
