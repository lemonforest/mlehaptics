#!/usr/bin/env python3
"""Spike #24 bonus 6 — RNG spectral-graph test (the mandatory falsifier).

Per the antiquity-geocentric methodological discriminator (MFO bonus 5):
the falsifier MUST be a spectral-graph operation, NOT a statistical test,
NOT a curve-fit. Statistical tests (NIST SP 800-22 frequency / runs / etc.)
are uniformity-distinguishers; they answer "is this distribution flat?" but
NOT "does this have primitive-vocabulary residue?"

Three spectral signatures:
  S1 — Eigenvalue spectrum of the bit-pair-transition graph.
       Build directed graph: node = 2-bit pattern (4 nodes); edge weight =
       observed transition frequency. For a true-random stream all eight
       directed-edge weights converge to 1/4. Deviations give nonzero
       Fiedler-like Class L signature. Generalised to k-bit patterns for
       larger graphs.
  S2 — Class L Laplacian spectrum of an n-byte-window adjacency graph.
       Build graph: node = position-in-output (modulo M for compression);
       edge (i, j) weight = popcount XOR of byte[i] and byte[j]. The Class L
       Laplacian's leading eigenvalues form a spectrum that for true-random
       bytes is dense and uniform; for structured bytes shows gaps and
       multiplicity.
  S3 — Frequency-domain DFT (Class L on a cyclic-shift graph).
       The DFT spectrum of the bit sequence is the Class L eigendecomposition
       of the cyclic-shift graph; primitive-vocabulary residue shows up as
       peaks in the DFT spectrum.

Each construction's spectra are compared to the os.urandom baseline. The
DISCRIMINATION TEST is: can we identify which construction produced a buffer
by its spectral signature alone? If yes, the construction has primitive-
vocabulary residue. If no, the construction is spectrally indistinguishable
from true randomness within tooling precision.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Import the constructions from the constructive probe via importlib
# (filename has hyphens, so it's not a valid Python module name).
import importlib.util as _ilu
_probe_path = Path(__file__).with_name(
    "spike_24_bonus_rng_constructive_probe_2026-05-15.py"
)
_spec = _ilu.spec_from_file_location("rng_probe", _probe_path)
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
rng0a_urandom = _mod.rng0a_urandom
rng0b_counter = _mod.rng0b_counter
rng0c_numpy_pcg64 = _mod.rng0c_numpy_pcg64
rng1_hmac_drbg = _mod.rng1_hmac_drbg
rng2_lfsr_gf2_256 = _mod.rng2_lfsr_gf2_256
rng3_brusselator_sha = _mod.rng3_brusselator_sha
rng3_raw_brusselator = _mod.rng3_raw_brusselator
bits_from_bytes = _mod.bits_from_bytes

SCRIPT = Path(__file__).name
TODAY = "2026-05-15"
SEED = 20260515
N_BITS = 2 ** 17  # 131,072 bits = 16 KiB per construction
OUT = Path(__file__).with_suffix(".ndjson")


# =========================================================================
# S1 — Bit-pattern transition graph spectrum (Class L on the symbol-graph)
# =========================================================================
def spectrum_bit_transition_graph(bits: np.ndarray, k: int = 4) -> dict:
    """Build the k-bit pattern transition graph and compute its spectrum.

    For k=4: 16 nodes, up to 16x16=256 directed edges. Edge weight = observed
    transition count from pattern i to pattern j.

    Returns:
      - eigenvalues of the (symmetric part of the) weighted adjacency
      - top-3 eigenvalues
      - spectral gap (1st - 2nd)
      - chi-square distance of edge-weights from uniform
    """
    n = len(bits) - k
    # Pack each k-window into a node index.
    pat = np.zeros(n + 1, dtype=np.int64)
    for j in range(k):
        pat = (pat << 1) | bits[j:j + n + 1].astype(np.int64)
    pat &= (1 << k) - 1
    n_nodes = 1 << k
    A = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    for src, dst in zip(pat[:-1], pat[1:]):
        A[src, dst] += 1.0
    # Symmetrize for Laplacian spectrum (undirected transition strength).
    A_sym = 0.5 * (A + A.T)
    # Class L Laplacian: D - A.
    D = np.diag(A_sym.sum(axis=1))
    L = D - A_sym
    # Eigenvalues, sorted ascending.
    eigs = np.linalg.eigvalsh(L)
    # Edge-weight uniformity chi-square: expected count per edge = n / n_edges
    # but we'll use chi-square over the (i->j) flat counts (no symmetrization).
    flat = A.ravel()
    flat_nonzero = flat[flat > 0]  # safety filter
    expected = n / (n_nodes * n_nodes)
    chi_sq = float(np.sum((flat - expected) ** 2 / max(expected, 1e-10)))

    # Spectral gap: ratio of (lambda_2 - lambda_1) to lambda_max
    lam_max = float(eigs[-1])
    lam_sorted_unique = np.unique(np.round(eigs, decimals=10))
    # ratio second-smallest nonzero / largest
    nonzero = eigs[eigs > 1e-9]
    fiedler = float(nonzero[0]) if len(nonzero) > 0 else 0.0
    return {
        "k": k,
        "n_nodes": n_nodes,
        "top3_eigs": [float(x) for x in eigs[-3:]],
        "bot3_eigs": [float(x) for x in eigs[:3]],
        "lambda_max": lam_max,
        "lambda_fiedler": fiedler,
        "fiedler_over_max": fiedler / lam_max if lam_max > 0 else 0.0,
        "n_distinct_eigs": int(len(lam_sorted_unique)),
        "eig_chi_sq": chi_sq,
    }


# =========================================================================
# S2 — Class L on n-byte-window XOR-popcount adjacency
# =========================================================================
def spectrum_byte_window_graph(buf: bytes, window_M: int = 256) -> dict:
    """Build the window-adjacency graph.

    Take the first window_M bytes (or modulo window_M). Build M x M graph
    with edge weight (i, j) = popcount(buf[i] XOR buf[j]). For a uniformly-
    random buffer the popcount distribution is Binomial(8, 0.5) ~ mean 4,
    std ~ 1.41; the resulting Laplacian has a well-known semi-circle-like
    eigenvalue density.

    Primitive-vocabulary residue would show up as deviations from the
    random-matrix density (clustering near specific eigenvalues, gaps).
    """
    b = np.frombuffer(buf, dtype=np.uint8)
    if len(b) > window_M:
        b = b[:window_M]
    n = len(b)
    # Vectorised popcount-XOR.
    xor = np.bitwise_xor.outer(b, b)
    popcnt = np.zeros_like(xor, dtype=np.int64)
    for shift in range(8):
        popcnt += (xor >> shift) & 1
    A = popcnt.astype(np.float64)
    np.fill_diagonal(A, 0.0)
    D = np.diag(A.sum(axis=1))
    L = D - A
    eigs = np.linalg.eigvalsh(L)
    lam_max = float(eigs[-1])
    # Spectral compactness: ratio std / mean
    mean_e = float(np.mean(eigs))
    std_e = float(np.std(eigs))
    # Multiplicity at lambda_max (count within 0.01 of max).
    mult_max = int(np.sum(np.abs(eigs - eigs[-1]) < 0.01))
    return {
        "window_M": n,
        "lambda_max": lam_max,
        "lambda_mean": mean_e,
        "lambda_std": std_e,
        "cv_eigenvalues": std_e / mean_e if mean_e > 0 else 0.0,
        "multiplicity_at_max": mult_max,
        "spectral_compactness": std_e / lam_max if lam_max > 0 else 0.0,
        "top5_eigs": [float(x) for x in eigs[-5:]],
    }


# =========================================================================
# S3 — DFT spectrum as Class L on cyclic-shift graph
# =========================================================================
def spectrum_dft(bits: np.ndarray, n_top: int = 16) -> dict:
    """DFT magnitude spectrum of the bit sequence (+1/-1 mapped).

    The DFT of a cyclic-shift graph signal IS the Class L eigendecomposition
    of the cyclic shift's circulant matrix. Peaks in the DFT magnitude are
    eigenmode-with-large-projection signatures.

    For true-random bits the DFT magnitudes are chi-squared distributed; no
    systematic peaks. Primitive-vocabulary residue shows up as deterministic
    spectral peaks.
    """
    x = 2 * bits.astype(np.float64) - 1.0
    # Truncate to power of two for FFT efficiency.
    n = 1 << int(math.log2(len(x)))
    x = x[:n]
    X = np.fft.rfft(x)
    mags = np.abs(X)
    # Skip DC component (mags[0] is just the bit-balance).
    mags_nonzero = mags[1:]
    # Top n_top magnitudes and their indices.
    top_idx = np.argsort(mags_nonzero)[-n_top:][::-1]
    top_mags = mags_nonzero[top_idx]
    # Reference: for n_samples random +/-1 the DFT magnitude is Rayleigh-
    # distributed with sigma = sqrt(n/2); expected max over n/2 frequencies
    # is sqrt(n/2 * 2 * ln(n/2)) ≈ sqrt(n * ln(n/2)).
    expected_max = math.sqrt(n * math.log(n / 2.0)) if n > 4 else math.sqrt(n)
    # Spectral flatness (geometric mean / arithmetic mean of magnitudes).
    log_mean = float(np.mean(np.log(mags_nonzero + 1e-12)))
    arith_mean = float(np.mean(mags_nonzero))
    spectral_flatness = math.exp(log_mean) / arith_mean if arith_mean > 0 else 0.0
    return {
        "n_samples": n,
        "n_freqs": len(mags_nonzero),
        "max_mag": float(np.max(mags_nonzero)),
        "max_mag_over_expected": float(np.max(mags_nonzero) / expected_max),
        "top_n_indices": [int(i) for i in top_idx[:8]],
        "top_n_magnitudes": [float(m) for m in top_mags[:8]],
        "spectral_flatness": spectral_flatness,
    }


# =========================================================================
# Discrimination test — can spectral signature identify the construction?
# =========================================================================
def discrimination_test(spectra_by_name: dict[str, dict]) -> dict:
    """Given each construction's S1/S2/S3 spectral signatures, ask:
    are the signatures distinguishable from RNG0a_urandom?

    For each construction X, compute:
      |signature(X) - signature(RNG0a_urandom)| / signature(RNG0a_urandom)
    on the load-bearing metrics (S2 cv_eigenvalues, S3 spectral_flatness,
    S1 fiedler_over_max).

    A construction is "spectrally distinguishable" if any metric's relative
    deviation > 10%. Note this is a soft criterion; with a single seed we
    can't compute a real p-value, but we can identify substantial-deviation
    constructions.
    """
    base_name = "RNG0a_urandom"
    base = spectra_by_name[base_name]
    metrics = [
        ("S1.fiedler_over_max", "S1", "fiedler_over_max"),
        ("S2.cv_eigenvalues", "S2", "cv_eigenvalues"),
        ("S2.spectral_compactness", "S2", "spectral_compactness"),
        ("S3.spectral_flatness", "S3", "spectral_flatness"),
        ("S3.max_mag_over_expected", "S3", "max_mag_over_expected"),
    ]
    results = []
    for name, spec_set in spectra_by_name.items():
        if name == base_name:
            continue
        verdicts = {}
        for label, S_key, metric_key in metrics:
            base_val = base[S_key][metric_key]
            this_val = spec_set[S_key][metric_key]
            if abs(base_val) < 1e-10:
                rel_dev = float("inf") if this_val != 0 else 0.0
            else:
                rel_dev = abs(this_val - base_val) / abs(base_val)
            verdicts[label] = {
                "base": float(base_val),
                "this": float(this_val),
                "rel_dev": float(rel_dev),
                "distinguishable_at_10pct": bool(rel_dev > 0.10),
            }
        any_distinguishable = any(
            v["distinguishable_at_10pct"] for v in verdicts.values()
        )
        results.append({
            "name": name,
            "any_distinguishable": any_distinguishable,
            "metrics": verdicts,
        })
    return {"baseline": base_name, "results": results}


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
        ("RNG0a_urandom", rng0a_urandom),
        ("RNG0b_counter", rng0b_counter),
        ("RNG0c_pcg64", rng0c_numpy_pcg64),
        ("RNG1_hmac_drbg", rng1_hmac_drbg),
        ("RNG2_lfsr_gf2_256", rng2_lfsr_gf2_256),
        ("RNG3_brusselator_sha256", rng3_brusselator_sha),
        ("RNG3_brusselator_raw", rng3_raw_brusselator),
    ]

    spectra_by_name: dict[str, dict] = {}

    for name, fn in constructions:
        print(f"[Build+spec] {name} ...", flush=True)
        data = fn(N_BITS, SEED)
        bits = bits_from_bytes(data)

        # S1 — bit-pattern transition graph spectrum.
        s1 = spectrum_bit_transition_graph(bits, k=4)
        write_record(records,
                     phase="S1_bit_transition_spectrum",
                     name=name,
                     **s1)

        # S2 — byte-window XOR-popcount Laplacian.
        s2 = spectrum_byte_window_graph(data, window_M=256)
        write_record(records,
                     phase="S2_byte_window_spectrum",
                     name=name,
                     **s2)

        # S3 — DFT spectrum.
        s3 = spectrum_dft(bits, n_top=16)
        write_record(records,
                     phase="S3_dft_spectrum",
                     name=name,
                     **s3)

        spectra_by_name[name] = {"S1": s1, "S2": s2, "S3": s3}
        print(f"  S1.fiedler={s1['lambda_fiedler']:.4f} S2.cv={s2['cv_eigenvalues']:.4f} S3.flat={s3['spectral_flatness']:.4f}", flush=True)

    # Discrimination test against RNG0a_urandom baseline.
    disc = discrimination_test(spectra_by_name)
    write_record(records,
                 phase="D_discrimination_test",
                 baseline=disc["baseline"],
                 results=disc["results"])

    # Discrimination summary.
    summary = []
    for r in disc["results"]:
        max_rel = max(m["rel_dev"] for m in r["metrics"].values()
                      if m["rel_dev"] != float("inf"))
        summary.append({
            "name": r["name"],
            "any_distinguishable_at_10pct": r["any_distinguishable"],
            "max_rel_dev_pct": float(100.0 * max_rel),
        })
    write_record(records,
                 phase="E_summary",
                 baseline=disc["baseline"],
                 summary=summary)
    print("\n[Discrimination summary]")
    for s in summary:
        print(f"  {s['name']:34s}  max_rel_dev={s['max_rel_dev_pct']:8.2f}%  distinguishable={s['any_distinguishable_at_10pct']}", flush=True)

    with OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True))
            fh.write("\n")
    print(f"\n[Done] {len(records)} records -> {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
