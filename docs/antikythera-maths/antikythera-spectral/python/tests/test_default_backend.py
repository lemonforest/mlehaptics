"""Default-backend behavior — v0.3.0 default flip from complex128 to bit.

Three layers of tests, mirroring the three layers of the v0.3.0 flip:

A. Top-level ``default_encode`` (Option B): one-liner shorthand for
   "encode this date as a hypervector under the package's default
   backend."  Default ``backend="bit"`` per ``DEFAULT_BACKEND``.
B. Bridge dispatch (Option C): ``bridge.get_dial_state`` /
   ``decode_dial`` / ``decode_to_jd`` use the bit ALU by default;
   ``backend="complex128"`` recovers the v0.2.x reference shape.
C. Round-trip parity: a date encoded under bit and decoded under
   bit gives a similar D-bin residue to the same date encoded /
   decoded under complex128.  (Not bitwise-identical — different
   bases — but agreement to within decoder noise.)

These supplement the cohort-level immolation tests in
``test_immolation.py`` with focused behavioural checks.
"""

from __future__ import annotations

import numpy as np
import pytest

from antikythera_spectral import (
    DEFAULT_BACKEND,
    bridge,
    default_encode,
)
from antikythera_spectral.bit_alu import n_words


# ---------------------------------------------------------------------------
# A. Top-level `default_encode`
# ---------------------------------------------------------------------------

def test_default_backend_constant_is_bit() -> None:
    """``DEFAULT_BACKEND`` must be ``"bit"`` in v0.3.0."""
    assert DEFAULT_BACKEND == "bit"


def test_default_encode_default_backend_is_bit() -> None:
    """Calling ``default_encode(jd)`` with no backend kwarg must
    return a packed-uint64 array."""
    arr = default_encode(1684500.0)
    assert arr.dtype == np.dtype("uint64")
    assert arr.shape == (n_words(940),)


@pytest.mark.parametrize("D", [940, 13440])
def test_default_encode_dimension_param(D: int) -> None:
    """``default_encode(jd, D=...)`` returns a packed-uint64 array of
    the right length for the chosen D."""
    arr = default_encode(1684500.0, D=D)
    assert arr.shape == (n_words(D),)


def test_default_encode_complex128_backend() -> None:
    """``backend="complex128"`` returns a length-D complex array."""
    arr = default_encode(1684500.0, backend="complex128")
    assert np.iscomplexobj(arr)
    assert arr.shape == (940,)


def test_default_encode_unknown_backend_raises() -> None:
    """Unknown backend name must raise ValueError, not silently dispatch."""
    with pytest.raises(ValueError, match="backend must be"):
        default_encode(1684500.0, backend="binary_spatter_code")


# ---------------------------------------------------------------------------
# B. Bridge dispatch — get_dial_state / decode_dial / decode_to_jd
# ---------------------------------------------------------------------------

def test_bridge_get_dial_state_default_envelope() -> None:
    """Default ``get_dial_state`` envelope shape (bit backend)."""
    out = bridge.get_dial_state(1684500.0)
    assert out["ok"] is True
    assert out["backend"] == "bit"
    state = out["state"]
    assert state["dtype"] == "uint64"
    assert state["n_bits"] == 940
    assert state["shape"] == [n_words(940)]
    assert len(state["packed_uint64"]) == n_words(940)
    # All packed entries fit in uint64.
    for w in state["packed_uint64"]:
        assert 0 <= w < (1 << 64)


def test_bridge_get_dial_state_complex128_envelope() -> None:
    """Backward-compat: ``backend='complex128'`` returns the v0.2.x shape."""
    out = bridge.get_dial_state(1684500.0, backend="complex128")
    assert out["ok"] is True
    assert out["backend"] == "complex128"
    state = out["state"]
    assert state["dtype"] == "complex128"
    assert state["shape"] == [940]
    assert len(state["interleaved_f32"]) == 2 * 940


def test_bridge_get_dial_state_unknown_backend_returns_error() -> None:
    """Unknown backend must produce ``ok=False`` (not crash)."""
    out = bridge.get_dial_state(1684500.0, backend="quaternion")
    assert out["ok"] is False


@pytest.mark.parametrize("backend", ["bit", "complex128"])
def test_bridge_decode_dial_dispatch(backend: str) -> None:
    """``decode_dial`` auto-detects the backend from the input."""
    encoded = bridge.get_dial_state(1684500.0 + 100.0, backend=backend)
    out = bridge.decode_dial(encoded["state"], "Metonic", D=940)
    assert out["ok"] is True
    assert out["backend"] == backend
    assert 0 <= out["recovered_residue"] < 940


@pytest.mark.parametrize("backend", ["bit", "complex128"])
def test_bridge_decode_to_jd_dispatch(backend: str) -> None:
    """``decode_to_jd`` auto-detects the backend from the input."""
    encoded = bridge.get_dial_state(1684500.0 + 365.25, backend=backend)
    out = bridge.decode_to_jd(encoded["state"], D=940)
    assert out["ok"] is True
    assert out["backend"] == backend
    assert isinstance(out["median_jd"], float)


def test_bridge_decode_dial_accepts_bare_uint64_array() -> None:
    """A raw uint64 numpy array should be accepted as a bit-backend state
    (in addition to the dict envelope)."""
    encoded = bridge.get_dial_state(1684500.0 + 100.0)
    arr = np.array(encoded["state"]["packed_uint64"], dtype=np.uint64)
    out = bridge.decode_dial(arr, "Metonic", D=940)
    assert out["ok"] is True
    assert out["backend"] == "bit"


def test_bridge_decode_dial_accepts_legacy_interleaved_f32() -> None:
    """Legacy v0.2.x callers that pass a bare interleaved-Float32 list
    should still work (backward-compat for explicit callers that built
    their own state vector)."""
    encoded = bridge.get_dial_state(1684500.0 + 100.0, backend="complex128")
    flat = encoded["state"]["interleaved_f32"]
    out = bridge.decode_dial(flat, "Metonic", D=940)
    assert out["ok"] is True
    assert out["backend"] == "complex128"


# ---------------------------------------------------------------------------
# C. Round-trip parity — both backends recover similar residues
# ---------------------------------------------------------------------------

def test_round_trip_bit_and_complex_recover_same_residue() -> None:
    """Both backends are argmax-similarity decoders over the same
    rotation range [0, D); they should agree on the recovered residue
    to within decoder-noise tolerance.  Tested at a date where the
    Metonic dial sits well inside its modulus (no near-boundary noise)."""
    jd = 1684500.0 + 365.25 * 5
    bit_state = bridge.get_dial_state(jd)
    cx_state = bridge.get_dial_state(jd, backend="complex128")
    bit_out = bridge.decode_dial(bit_state["state"], "Metonic", D=940)
    cx_out = bridge.decode_dial(cx_state["state"], "Metonic", D=940)
    assert bit_out["ok"] and cx_out["ok"]
    diff = abs(bit_out["recovered_residue"] - cx_out["recovered_residue"])
    diff = min(diff, 940 - diff)  # cyclic distance
    assert diff <= 5, (
        f"bit decoder recovered {bit_out['recovered_residue']}, "
        f"complex128 decoder recovered {cx_out['recovered_residue']}; "
        f"cyclic-distance {diff} exceeds 5 quantisation steps"
    )
