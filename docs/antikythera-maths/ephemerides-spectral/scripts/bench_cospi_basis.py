#!/usr/bin/env python3
"""v0.29.0rc1 — channel-basis cospi/sinpi spike benchmark.

Quantifies the dual-path delta between LEGACY (× π in software) and
COSPI (libm cospi/sinpi or fallback). Use the report to decide whether
to graduate COSPI to default + update the Python mirror, or keep
LEGACY as the byte-parity default and COSPI as opt-in precision.

Measures, for each (seed, D) point and on a representative HDC roll-
and-accumulate pipeline:

  * max |bytes(legacy) - bytes(cospi)|        — pointwise basis drift
  * max ||basis| - 1|                          — unit-magnitude error
  * accumulator-drift after a typical body roll-sum                 │  HDC
  * residual deviation from unity at unit-norm check                │  pipeline

Output: NDJSON to stdout (one record per measurement), human-readable
summary banner to stderr. Per project convention NDJSON is preferred
for result outputs (one record per line) over indented JSON.

Run:

    python scripts/bench_cospi_basis.py > bench_v0.29.0rc1.ndjson

Run with --human for the formatted summary only (no NDJSON):

    python scripts/bench_cospi_basis.py --human

The script imports `ephemerides_spectral._native_bip` — requires the
native library to be loaded (`HAS_NATIVE = True`). Exits with code 2
when no native binary is present (e.g. sdist install).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np

from ephemerides_spectral import _native_bip
from ephemerides_spectral._native_bip import (
    ES_BASIS_METHOD_COSPI,
    ES_BASIS_METHOD_LEGACY,
)


def _check_native() -> None:
    if not _native_bip.HAS_NATIVE:
        print(
            "no native library loaded; cospi/sinpi spike bench requires it. "
            f"LOAD_ERROR: {_native_bip.LOAD_ERROR or '<unknown>'}",
            file=sys.stderr,
        )
        sys.exit(2)


def _basis(seed: int, D: int, method: int) -> np.ndarray:
    return _native_bip.native_channel_basis_method(seed, D, method)


def _emit(record: Dict[str, Any], stream: Any = sys.stdout) -> None:
    """Emit a single NDJSON record (one line, no trailing comma)."""
    stream.write(json.dumps(record, separators=(",", ":")))
    stream.write("\n")


# ─────────────────────────────────────────────────────────────────────
# Measurement primitives
# ─────────────────────────────────────────────────────────────────────


def _basis_drift(seed: int, D: int) -> Tuple[float, float, float, float]:
    """Return (max_re_delta, max_im_delta, max_mag_delta, max_byte_delta).

    max_*_delta is the L∞ over the D-vector between LEGACY and COSPI.
    max_byte_delta is max |complex64(legacy) - complex64(cospi)| as a
    complex magnitude.
    """
    legacy = _basis(seed, D, ES_BASIS_METHOD_LEGACY)
    cospi = _basis(seed, D, ES_BASIS_METHOD_COSPI)
    diff = legacy - cospi
    max_re = float(np.max(np.abs(diff.real)))
    max_im = float(np.max(np.abs(diff.imag)))
    max_mag = float(np.max(np.abs(np.abs(cospi) - 1.0)))
    max_byte = float(np.max(np.abs(diff)))
    return max_re, max_im, max_mag, max_byte


def _unit_mag_error(seed: int, D: int, method: int) -> float:
    basis = _basis(seed, D, method)
    return float(np.max(np.abs(np.abs(basis) - 1.0)))


def _hdc_roll_accumulate(seed: int, D: int, method: int,
                         n_bodies: int = 52,
                         offset_step: int = 311) -> Tuple[float, float]:
    """Mock HDC roll-and-accumulate: build the basis once, roll it
    n_bodies times by varying offsets, sum, normalise, return
    (||sum||, |||sum_normalised|| - 1.0|).

    This is a stand-in for the real `es_encode_state_hd` accumulation —
    same kind of roll-by-residue + normalise pattern but body-count
    agnostic.
    """
    basis = _basis(seed, D, method)
    # Use float64 internally to avoid summation float32-noise dominating
    # the cosmetic compare; both LEGACY and COSPI start from float32 so
    # this measures the *basis-construction* delta, not the sum loss.
    acc = np.zeros(D, dtype=np.complex128)
    for b in range(n_bodies):
        roll = (b * offset_step) % D
        acc += np.roll(basis.astype(np.complex128), roll)
    norm = float(np.linalg.norm(acc))
    if norm == 0.0:
        return 0.0, 1.0
    acc /= norm
    final_unit = float(abs(np.linalg.norm(acc) - 1.0))
    return norm, final_unit


# ─────────────────────────────────────────────────────────────────────
# Sweep
# ─────────────────────────────────────────────────────────────────────


SEEDS_DS: List[Tuple[int, int]] = [
    (2026,         1024),    # body 0 (sun)         small
    (2026 + 5,     1024),    # body 5 (jupiter)     small
    (2026 + 37,    1024),    # body 37              small
    (777,          1024),    # syzygy node basis    small
    (9999,         1024),    # topocentric coord    small
    (2026,         4096),    # body 0               mid
    (2026,         16384),   # body 0               larger
    (2026,         65536),   # body 0               production-D
    (2026 + 5,     65536),   # body 5               production-D
]


def run_sweep(stream: Any, *, ndjson: bool, human: bool) -> Dict[str, Any]:
    """Run the full sweep; return summary stats."""
    has_native = _native_bip.native_has_native_cospi()
    binary_version = _native_bip.native_version() or "<unknown>"

    header = {
        "schema": "ephemerides_spectral.bench.cospi_basis.v1",
        "binary_version": binary_version,
        "has_native_cospi": has_native,
        "abi_version": _native_bip.ABI_VERSION,
        "timestamp_unix": time.time(),
    }
    if ndjson:
        _emit({"record": "header", **header}, stream)
    if human:
        print(
            f"Bench: ephemerides-spectral {binary_version} (ABI v{header['abi_version']})\n"
            f"  has_native_cospi = {has_native}\n"
            f"  ({'using libm cospi/sinpi or __cospi/__sinpi' if has_native else 'fallback to cos(π·x): COSPI ≡ LEGACY at byte level'})\n",
            file=sys.stderr,
        )
        print(
            f"{'seed':>8} {'D':>7} | "
            f"{'maxΔre':>10} {'maxΔim':>10} {'maxByte':>10} | "
            f"{'cospi |mag-1|':>14} {'legacy |mag-1|':>14} | "
            f"{'hdc ‖acc‖ Δ':>14}",
            file=sys.stderr,
        )
        print("-" * 110, file=sys.stderr)

    summary_max_byte = 0.0
    summary_max_mag_cospi = 0.0
    summary_max_mag_legacy = 0.0
    summary_max_hdc_drift = 0.0
    for seed, D in SEEDS_DS:
        max_re, max_im, max_mag_cospi, max_byte = _basis_drift(seed, D)
        max_mag_legacy = _unit_mag_error(seed, D, ES_BASIS_METHOD_LEGACY)

        hdc_legacy_norm, _ = _hdc_roll_accumulate(seed, D, ES_BASIS_METHOD_LEGACY)
        hdc_cospi_norm, _ = _hdc_roll_accumulate(seed, D, ES_BASIS_METHOD_COSPI)
        hdc_norm_drift = abs(hdc_cospi_norm - hdc_legacy_norm)

        rec = {
            "record": "point",
            "seed": seed,
            "D": D,
            "max_re_delta": max_re,
            "max_im_delta": max_im,
            "max_byte_delta": max_byte,
            "cospi_max_mag_minus_1": max_mag_cospi,
            "legacy_max_mag_minus_1": max_mag_legacy,
            "hdc_legacy_acc_norm": hdc_legacy_norm,
            "hdc_cospi_acc_norm": hdc_cospi_norm,
            "hdc_acc_norm_drift": hdc_norm_drift,
        }
        if ndjson:
            _emit(rec, stream)
        if human:
            print(
                f"{seed:>8} {D:>7} | "
                f"{max_re:>10.2e} {max_im:>10.2e} {max_byte:>10.2e} | "
                f"{max_mag_cospi:>14.2e} {max_mag_legacy:>14.2e} | "
                f"{hdc_norm_drift:>14.2e}",
                file=sys.stderr,
            )

        summary_max_byte = max(summary_max_byte, max_byte)
        summary_max_mag_cospi = max(summary_max_mag_cospi, max_mag_cospi)
        summary_max_mag_legacy = max(summary_max_mag_legacy, max_mag_legacy)
        summary_max_hdc_drift = max(summary_max_hdc_drift, hdc_norm_drift)

    summary = {
        "record": "summary",
        "max_byte_delta_overall": summary_max_byte,
        "max_mag_minus_1_cospi": summary_max_mag_cospi,
        "max_mag_minus_1_legacy": summary_max_mag_legacy,
        "max_hdc_acc_norm_drift": summary_max_hdc_drift,
        "cospi_tighter_than_legacy": summary_max_mag_cospi <= summary_max_mag_legacy,
    }
    if ndjson:
        _emit(summary, stream)
    if human:
        verdict = (
            "COSPI tighter than LEGACY on unit-magnitude error"
            if summary["cospi_tighter_than_legacy"]
            else "COSPI not tighter — investigate or fallback active"
        )
        print(
            f"\nSummary:\n"
            f"  max |basis(legacy) - basis(cospi)|   = {summary_max_byte:.2e}\n"
            f"  max ||basis_cospi| - 1|              = {summary_max_mag_cospi:.2e}\n"
            f"  max ||basis_legacy| - 1|             = {summary_max_mag_legacy:.2e}\n"
            f"  max |‖hdc_cospi‖ - ‖hdc_legacy‖|     = {summary_max_hdc_drift:.2e}\n"
            f"  → {verdict}",
            file=sys.stderr,
        )
    return summary


# ─────────────────────────────────────────────────────────────────────
# Entry
# ─────────────────────────────────────────────────────────────────────


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--human", action="store_true",
        help="Print formatted summary to stderr; suppress NDJSON to stdout.",
    )
    parser.add_argument(
        "--ndjson-only", action="store_true",
        help="NDJSON to stdout, no human-readable summary.",
    )
    args = parser.parse_args(argv)
    _check_native()
    ndjson = not args.human
    human = not args.ndjson_only
    run_sweep(sys.stdout, ndjson=ndjson, human=human)
    return 0


if __name__ == "__main__":
    sys.exit(main())
