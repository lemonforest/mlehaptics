"""Qalg TAIL Batch 1b (0.9.0rc157): the π family earns a ``srmech_bigint``-backed
C path — ``bignum_reference → c_dispatched`` / ``composition_of_c``.

The NEW C kernel ``srmech_pi_archimedes`` runs the WHOLE Pfaff–Archimedes
two-mean chiral-pair loop (per-step harmonic-mean ``srmech_bigint_divmod`` +
geometric-mean ``srmech_bigint_isqrt``) on the caller-arena ``srmech_bigint``, so
``srmech.amsc.rational.pi_cascade_digits`` DISPATCHES to it, and its two
signal-processing wrappers
(``signal_processing.{closed_form_ops,path_b_ops}.pi_cascade.op``) free-ride.

This test pins:
  1. the native symbol is actually loaded (so parity exercises C, not a silent
     pure fallback on BOTH sides);
  2. ``pi_cascade_digits`` native == FORCED-PURE is BYTE-IDENTICAL across
     ``n ∈ {1, 10, 50, 100, 500, 1000}`` (exact π digits, not float);
  3. the STRONGEST cross-check ``pi_chudnovsky_digits(n) == pi_cascade_digits(n)``
     — two INDEPENDENT π algorithms (rotation-last vs projects-every-step) agree;
  4. the value oracle ``str(pi_cascade_digits(1000))[:11] == "3.141592653"``;
  5. the 2 signal-processing wrappers are native == pure;
  6. the raw ``pi_archimedes_c`` helper computes the whole loop in C (a bare-C
     host reaches the digit stream with no Python);
  7. the 3 Rosetta rows are ``c_dispatched`` / ``composition_of_c``.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import rational as R
from srmech.signal_processing.closed_form_ops import pi_cascade as _cf_pi
from srmech.signal_processing.path_b_ops import pi_cascade as _pb_pi


# The parity digit-counts (spanning the auto depth/precision scaling to the
# rc13 cap of 1000; 500/1000 exercise the ~20000-bit isqrt radicand).
_NS = [1, 10, 50, 100, 500, 1000]


def _force(has_native: bool, fn, *args, **kw):
    """Run ``fn`` with ``_native.HAS_NATIVE`` pinned, then restore."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_symbol_present():
    # The C kernel is actually loaded, so the parity tests exercise C.
    assert _native.has_native_pi_archimedes()
    # The raw helper computes the whole Archimedes loop in C (no Python loop).
    depth, pb = R._pi_cascade_auto_params(50)
    assert _native.pi_archimedes_c(50, depth, pb) == R.pi_cascade_digits(50)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("n", _NS + [0])
def test_pi_cascade_native_equals_pure_byte_identical(n):
    """pi_cascade_digits native == FORCED-PURE, BYTE-IDENTICAL (exact digits)."""
    nat = _force(True, R.pi_cascade_digits, n)
    pure = _force(False, R.pi_cascade_digits, n)
    assert nat == pure, (n, nat[:40], pure[:40])
    # shape: always "3." then exactly n fractional digits
    assert nat.startswith("3.")
    assert len(nat) == n + 2


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("n", _NS)
def test_pi_chudnovsky_equals_pi_cascade(n):
    """The STRONGEST check: two INDEPENDENT π algorithms agree byte-for-byte —
    the rotation-last Chudnovsky vs the projects-every-step Archimedes bracket."""
    assert R.pi_chudnovsky_digits(n) == R.pi_cascade_digits(n)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("n", [1, 10, 50, 100])
def test_sp_wrappers_native_equals_pure(n):
    """Both signal-processing pi_cascade wrappers are native == forced-pure and
    equal the underlying rational.pi_cascade_digits (composition_of_c)."""
    for op in (_cf_pi.op, _pb_pi.op):
        nat = _force(True, op, n)
        pure = _force(False, op, n)
        assert nat == pure, (op.__module__, n, nat[:40], pure[:40])
        assert nat == R.pi_cascade_digits(n)


def test_value_oracles():
    """Named value oracles (native path; also runs pure on a no-C lib)."""
    assert R.pi_cascade_digits(0) == "3."
    assert R.pi_cascade_digits(5) == "3.14159"
    assert R.pi_cascade_digits(15) == "3.141592653589793"
    # the batch's headline value oracle
    assert str(R.pi_cascade_digits(1000))[:11] == "3.141592653"
    # and the full 1000-digit stream agrees with the independent Chudnovsky SSoT
    assert R.pi_cascade_digits(1000) == R.pi_chudnovsky_digits(1000)


def test_ledger_rows():
    """pi_cascade_digits → c_dispatched; the 2 sp wrappers → composition_of_c."""
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fixture.read_text(encoding="utf-8").splitlines() if l.strip()}
    assert rows.get("srmech.amsc.rational.pi_cascade_digits") == "c_dispatched"
    assert rows.get(
        "srmech.signal_processing.closed_form_ops.pi_cascade.op"
    ) == "composition_of_c"
    assert rows.get(
        "srmech.signal_processing.path_b_ops.pi_cascade.op"
    ) == "composition_of_c"
