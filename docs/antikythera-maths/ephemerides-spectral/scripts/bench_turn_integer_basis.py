#!/usr/bin/env python3
"""v0.29.0rc1 — channel-basis TURN_INTEGER spike benchmark.

Quantifies the dual-path delta between LEGACY (`× 2π/2^53` software
multiply then libm cos/sin on a [0, 2π) argument) and TURN_INTEGER
(integer quarter-turn decomposition + libm cos/sin on a [0, π/2)
argument + i^quadrant rotation by sign/swap).

Measures, for each (seed, D) point and on a representative HDC roll-
and-accumulate pipeline:

  * max |bytes(legacy) - bytes(turn_integer)|   pointwise basis drift
  * max ||basis| - 1|                            unit-magnitude error
  * accumulator-drift after a body roll-sum                 │  HDC
  * residual deviation from unity after normalising         │  pipeline

Both routes are deterministic across platforms; results should
match exactly between Windows, WSL2, macOS, etc. Per project
convention NDJSON over indented JSON for results outputs.

Run:

    python scripts/bench_turn_integer_basis.py > bench_v0.29.0rc1.ndjson

Run with --human for the formatted summary only (no NDJSON):

    python scripts/bench_turn_integer_basis.py --human

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
    ES_BASIS_METHOD_LEGACY,
    ES_BASIS_METHOD_TURN_INTEGER,
)


def _check_native() -> None:
    if not _native_bip.HAS_NATIVE:
        print(
            "no native library loaded; TURN_INTEGER spike bench requires it. "
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

    max_*_delta is the L∞ over the D-vector between LEGACY and
    TURN_INTEGER. max_byte_delta is max |complex64(legacy) -
    complex64(turn_integer)| as a complex magnitude. The two routes
    use different bit-extraction strategies (LEGACY uses 53 mantissa
    bits; TURN_INTEGER uses 32 high bits) so the delta is not the
    "rounding loss" — it's the difference between two valid bases
    constructed from the same underlying splitmix64 stream via
    different decomposition algorithms.
    """
    legacy = _basis(seed, D, ES_BASIS_METHOD_LEGACY)
    ti = _basis(seed, D, ES_BASIS_METHOD_TURN_INTEGER)
    diff = legacy - ti
    max_re = float(np.max(np.abs(diff.real)))
    max_im = float(np.max(np.abs(diff.imag)))
    max_mag = float(np.max(np.abs(np.abs(ti) - 1.0)))
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

    Stand-in for the real `es_encode_state_hd` accumulation — same
    kind of roll-by-residue + normalise pattern but body-count
    agnostic.
    """
    basis = _basis(seed, D, method)
    # Use float64 internally so the accumulator's float32-noise doesn't
    # dominate the cosmetic compare; both routes start from float32 so
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


def _quarter_turn_dispatch_count(seed: int, D: int) -> int:
    """Count how many basis elements landed on a bit-exact quarter
    turn under TURN_INTEGER. For random splitmix64 phases the
    expected count is ~D / 2^30 — essentially zero at D ≤ 65536.
    Surfaced for completeness; if a future bench deliberately seeds
    quarter-turn-aligned phases this would be non-zero.
    """
    ti = _basis(seed, D, ES_BASIS_METHOD_TURN_INTEGER)
    re_zero = ti.real == 0.0
    im_zero = ti.imag == 0.0
    # A quarter turn has exactly ONE component zero AND the other ±1.
    one_zero = re_zero ^ im_zero  # XOR: exactly one zero
    abs_one = (np.abs(ti.real) == 1.0) | (np.abs(ti.imag) == 1.0)
    return int(np.sum(one_zero & abs_one))


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
    binary_version = _native_bip.native_version() or "<unknown>"

    header = {
        "schema": "ephemerides_spectral.bench.turn_integer_basis.v1",
        "binary_version": binary_version,
        "abi_version": _native_bip.ABI_VERSION,
        "timestamp_unix": time.time(),
    }
    if ndjson:
        _emit({"record": "header", **header}, stream)
    if human:
        print(
            f"Bench: ephemerides-spectral {binary_version} (ABI v{header['abi_version']})\n"
            f"  TURN_INTEGER route: cyclic-group-native quarter-turn\n"
            f"    decomposition + libm cos/sin on a [0, π/2) argument\n"
            f"    + i^quadrant sign/swap rotation. Deterministic across\n"
            f"    platforms.\n",
            file=sys.stderr,
        )
        print(
            f"{'seed':>8} {'D':>7} | "
            f"{'maxΔre':>10} {'maxΔim':>10} {'maxByte':>10} | "
            f"{'TI |mag-1|':>12} {'LEGACY |mag-1|':>14} | "
            f"{'hdc ‖acc‖ Δ':>14} {'QT exact':>9}",
            file=sys.stderr,
        )
        print("-" * 120, file=sys.stderr)

    summary_max_byte = 0.0
    summary_max_mag_ti = 0.0
    summary_max_mag_legacy = 0.0
    summary_max_hdc_drift = 0.0
    summary_qt_total = 0
    for seed, D in SEEDS_DS:
        max_re, max_im, max_mag_ti, max_byte = _basis_drift(seed, D)
        max_mag_legacy = _unit_mag_error(seed, D, ES_BASIS_METHOD_LEGACY)

        hdc_legacy_norm, _ = _hdc_roll_accumulate(seed, D, ES_BASIS_METHOD_LEGACY)
        hdc_ti_norm, _ = _hdc_roll_accumulate(seed, D, ES_BASIS_METHOD_TURN_INTEGER)
        hdc_norm_drift = abs(hdc_ti_norm - hdc_legacy_norm)

        qt_count = _quarter_turn_dispatch_count(seed, D)

        rec = {
            "record": "point",
            "seed": seed,
            "D": D,
            "max_re_delta": max_re,
            "max_im_delta": max_im,
            "max_byte_delta": max_byte,
            "turn_integer_max_mag_minus_1": max_mag_ti,
            "legacy_max_mag_minus_1": max_mag_legacy,
            "hdc_legacy_acc_norm": hdc_legacy_norm,
            "hdc_turn_integer_acc_norm": hdc_ti_norm,
            "hdc_acc_norm_drift": hdc_norm_drift,
            "quarter_turn_exact_count": qt_count,
        }
        if ndjson:
            _emit(rec, stream)
        if human:
            print(
                f"{seed:>8} {D:>7} | "
                f"{max_re:>10.2e} {max_im:>10.2e} {max_byte:>10.2e} | "
                f"{max_mag_ti:>12.2e} {max_mag_legacy:>14.2e} | "
                f"{hdc_norm_drift:>14.2e} {qt_count:>9d}",
                file=sys.stderr,
            )

        summary_max_byte = max(summary_max_byte, max_byte)
        summary_max_mag_ti = max(summary_max_mag_ti, max_mag_ti)
        summary_max_mag_legacy = max(summary_max_mag_legacy, max_mag_legacy)
        summary_max_hdc_drift = max(summary_max_hdc_drift, hdc_norm_drift)
        summary_qt_total += qt_count

    summary = {
        "record": "summary",
        "max_byte_delta_overall": summary_max_byte,
        "max_mag_minus_1_turn_integer": summary_max_mag_ti,
        "max_mag_minus_1_legacy": summary_max_mag_legacy,
        "max_hdc_acc_norm_drift": summary_max_hdc_drift,
        "quarter_turn_exact_total": summary_qt_total,
        "turn_integer_tighter_than_legacy": summary_max_mag_ti <= summary_max_mag_legacy,
    }
    if ndjson:
        _emit(summary, stream)
    if human:
        verdict = (
            "TURN_INTEGER tighter than LEGACY on unit-magnitude error"
            if summary["turn_integer_tighter_than_legacy"]
            else "TURN_INTEGER NOT tighter than LEGACY — investigate"
        )
        print(
            f"\nSummary:\n"
            f"  max |basis(legacy) - basis(turn_integer)|  = {summary_max_byte:.2e}\n"
            f"  max ||basis_turn_integer| - 1|             = {summary_max_mag_ti:.2e}\n"
            f"  max ||basis_legacy| - 1|                   = {summary_max_mag_legacy:.2e}\n"
            f"  max |‖hdc_turn_integer‖ - ‖hdc_legacy‖|    = {summary_max_hdc_drift:.2e}\n"
            f"  quarter-turn bit-exact dispatches (total)  = {summary_qt_total}\n"
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
