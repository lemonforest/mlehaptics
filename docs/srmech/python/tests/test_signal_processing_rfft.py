"""Tests for the v0.4.3rc5 ``rfft`` dual-path op (UPSTREAM_NOTES §1.1).

Real-input half-spectrum FFT, added as a post-Phase-4 dual-path op
(like ``pi_cascade``). Coverage:

- Path A ``op`` is bit-exact with ``numpy.fft.rfft``.
- Path B ``op`` is D1 algebra-identical with Path A.
- The rFFT half-spectrum equals the first ``N//2 + 1`` bins of the full
  ``fft`` (the conjugate-symmetry identity that makes rfft valid).
- The §1.1 use case: bipolar bit-strings ``{-1, +1}``.
- Both paths registered with ``path_registry``; metadata present.
- ``rfft`` is NOT in the frozen ``PATH_B_MVP_OPS`` roster (post-MVP add).
- Class composition is the same A∘I∘K as ``fft``, all within 14 A-N.
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.signal_processing import path_registry
from srmech.signal_processing.closed_form_ops import fft as a_fft
from srmech.signal_processing.closed_form_ops import rfft as a_rfft
from srmech.signal_processing.path_b_ops import PATH_B_MVP_OPS
from srmech.signal_processing.path_b_ops import rfft as b_rfft
from srmech.signal_processing._paths import PATH_A, PATH_B

_VALID_CLASSES = set("ABCDEFGHIJKLMN")


def _real_signal(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n)


# ----------------------------------------------------------------------
# Path A reference parity
# ----------------------------------------------------------------------


@pytest.mark.parametrize("n", [16, 17, 64, 128])
def test_path_a_matches_numpy_rfft(n: int):
    x = _real_signal(n, seed=n)
    np.testing.assert_array_equal(a_rfft.op(x), np.fft.rfft(x))


def test_path_a_output_length_is_half_plus_one():
    x = _real_signal(64, seed=1)
    out = a_rfft.op(x)
    assert out.shape[0] == 64 // 2 + 1  # 33


def test_path_a_explicit_n_truncate_and_pad():
    x = _real_signal(40, seed=2)
    # n shorter than signal (truncate) and longer (zero-pad).
    np.testing.assert_array_equal(a_rfft.op(x, n=32), np.fft.rfft(x, n=32))
    np.testing.assert_array_equal(a_rfft.op(x, n=64), np.fft.rfft(x, n=64))


# ----------------------------------------------------------------------
# Path B == Path A (D1 algebra identity)
# ----------------------------------------------------------------------


@pytest.mark.parametrize("n", [16, 64, 256, 512])
def test_path_b_equals_path_a(n: int):
    x = _real_signal(n, seed=n + 7)
    np.testing.assert_array_equal(b_rfft.op(x), a_rfft.op(x))


def test_path_b_cycle_order_envelope_runs():
    # n=512 is in the form_function_rotation validation envelope
    # (256 ≤ n ≤ 2^16, multiple of 8) — exercises the Class K cycle-order
    # assertion path without raising.
    x = _real_signal(512, seed=3)
    out = b_rfft.op(x)
    assert out.shape[0] == 512 // 2 + 1


# ----------------------------------------------------------------------
# Half-spectrum identity: rfft(x) == fft(x)[:n//2 + 1]
# ----------------------------------------------------------------------


@pytest.mark.parametrize("n", [15, 16, 63, 64])
def test_rfft_is_first_half_of_fft(n: int):
    x = _real_signal(n, seed=n + 11)
    full = a_fft.op(x)
    half = a_rfft.op(x)
    np.testing.assert_allclose(half, full[: n // 2 + 1], atol=1e-12)


def test_hermitian_reconstruction_of_full_spectrum():
    """A real signal's full FFT is recoverable from the half-spectrum by
    Hermitian symmetry X[N-k] = conj(X[k]) — the redundancy rfft drops."""
    n = 32
    x = _real_signal(n, seed=4)
    half = a_rfft.op(x)  # length n//2 + 1
    # Rebuild the upper half by conjugate reflection of bins 1..n//2-1.
    upper = np.conj(half[1:-1][::-1])
    full_rebuilt = np.concatenate([half, upper])
    np.testing.assert_allclose(full_rebuilt, a_fft.op(x), atol=1e-12)


# ----------------------------------------------------------------------
# §1.1 use case: bipolar bit-strings {-1, +1}
# ----------------------------------------------------------------------


def test_bipolar_bitstring_rfft():
    rng = np.random.default_rng(5)
    bits = rng.integers(0, 2, 256)
    bipolar = (2 * bits - 1).astype(np.float64)  # {-1, +1}
    np.testing.assert_array_equal(b_rfft.op(bipolar), np.fft.rfft(bipolar))


# ----------------------------------------------------------------------
# Registration + metadata
# ----------------------------------------------------------------------


def test_both_paths_registered():
    assert path_registry.has_path("rfft", PATH_A), "Path A rfft not registered"
    assert path_registry.has_path("rfft", PATH_B), "Path B rfft not registered"


def test_metadata_present_both_modules():
    for mod in (a_rfft, b_rfft):
        assert mod.OPERATION_NAME == "rfft"
        assert mod.CLASS_COMPOSITION == ("A", "I", "K")
        assert isinstance(mod.SSOT_CITATION, str) and mod.SSOT_CITATION
        assert set(mod.CLASS_COMPOSITION) <= _VALID_CLASSES


def test_rfft_not_in_frozen_mvp_roster():
    """rfft is a post-Phase-4 addition (UPSTREAM_NOTES §1.1), like
    pi_cascade — it must NOT inflate the frozen 6-op MVP roster."""
    assert "rfft" not in PATH_B_MVP_OPS
    assert len(PATH_B_MVP_OPS) == 6
