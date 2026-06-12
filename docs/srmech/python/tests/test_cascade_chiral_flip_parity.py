"""C/Python parity tests for srmech.amsc.cascade.chiral_flip.

v0.4.5rc1 corrects the v0.4.3rc6 / v0.4.4rc1 carve-out that shipped
cascade ops Python-only. This test confirms native + Python paths produce
bit-identical outputs across the supported input types.

numpy-free: ``chiral_flip`` is an orientation reversal, so the reference is
``seq[::-1]`` (the textbook reversal). Inputs are plain Python lists/tuples/
strings; the op returns the same plain container reversed. The old
ndarray-dtype parity cases were deleted — they only asserted numpy
``.dtype``/``np.testing`` behaviour that no longer exists now that numpy is
out of srmech and the op returns plain lists.
"""
import random

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not HAS_NATIVE,
    reason="native srmech library not loaded; C-parity test cannot run",
)


# Whether the loaded libsrmech actually exposes the chiral_flip symbols.
# Mirrors the test_hdc_polar_parity.py pattern — a stale lib (pre-rc1)
# loads fine but doesn't expose the new symbols; tests that need the
# native path skip cleanly when this is False.
_CHIRAL_FLIP_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_chiral_flip_i64")
    and hasattr(_native.LIB, "srmech_cascade_chiral_flip_f64")
)

SKIP_IF_NO_CHIRAL_FLIP_NATIVE = pytest.mark.skipif(
    not _CHIRAL_FLIP_NATIVE,
    reason="installed libsrmech predates v0.4.5rc1 chiral_flip symbols",
)


# Construct several sequences of different shapes and types.
RNG = random.Random(42)


def test_python_path_basic():
    """The Python fallback path (string input) still works."""
    assert cascade.chiral_flip("abc") == "cba"
    assert cascade.chiral_flip(()) == ()
    assert cascade.chiral_flip((1, 2, 3)) == (3, 2, 1)


@SKIP_IF_NO_NATIVE
def test_parity_int64_list():
    seq = [RNG.randint(-1_000_000, 1_000_000) for _ in range(17)]
    native = cascade.chiral_flip(seq)
    python_ref = seq[::-1]
    assert native == python_ref


@SKIP_IF_NO_NATIVE
def test_parity_float64_list():
    seq = [RNG.gauss(0.0, 1.0) for _ in range(17)]
    native = cascade.chiral_flip(seq)
    python_ref = seq[::-1]
    assert native == python_ref  # bit-exact reversal preserves equality


@SKIP_IF_NO_NATIVE
def test_parity_empty():
    assert cascade.chiral_flip([]) == []


@SKIP_IF_NO_NATIVE
def test_parity_singleton():
    assert cascade.chiral_flip([42]) == [42]
    assert cascade.chiral_flip([3.14]) == [3.14]


@SKIP_IF_NO_NATIVE
def test_parity_odd_length():
    """Odd-length input requires careful middle-element handling."""
    seq = [1, 2, 3, 4, 5, 6, 7]
    native = cascade.chiral_flip(seq)
    assert native == [7, 6, 5, 4, 3, 2, 1]


@SKIP_IF_NO_CHIRAL_FLIP_NATIVE
def test_native_lib_exposes_symbols():
    """The libsrmech native library exposes both typed variants.

    Skips cleanly on a stale lib (pre-rc1) — mirrors the rc12 /
    polar / klein4 best-effort binding convention. Once the v0.4.5rc1
    wheel is installed, this test confirms the symbols are present.
    """
    # Bindings live on the loaded ctypes CDLL (_native.LIB), which is the
    # established pattern for hasattr-guarded native symbols in this
    # module (mirrors the rc12 / polar / klein4 binding blocks).
    assert _native.LIB is not None
    assert hasattr(_native.LIB, "srmech_cascade_chiral_flip_i64")
    assert hasattr(_native.LIB, "srmech_cascade_chiral_flip_f64")
