"""rc170 — §53 / F818: native dispatch for the Class-M klein4 core.

The C ``srmech_klein4_bind`` / ``_bundle`` / ``_similarity`` already ship in
libsrmech and are ctypes-bound, but the Python ops ran pure-Python (~8.7 ms/bind
at D=10000). rc170 wires the dispatch. These tests prove the native fast path is
**bit-identical** to the pure-Python cascade (so a downstream HDC content-
addressed walk can use srmech at C speed without changing the result), and that
the pure-Python fallback still holds when native is absent.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""

from array import array

import pytest

from srmech.amsc import hdc
from srmech.amsc import _native


def _codes(seed, n):
    """A deterministic klein4 code stream (values 0..3), no RNG dependency."""
    return array("B", [((i * seed + 1013904223) >> 5) & 3 for i in range(n)])


def test_pure_python_path_always_correct():
    """With or without native, klein4_bind/bundle/similarity give the spec result
    (XOR / per-bit majority / match-fraction)."""
    a = array("B", [0, 1, 2, 3, 1, 2])
    b = array("B", [3, 2, 1, 0, 1, 0])
    bound = hdc.klein4_bind(a, b)
    assert list(bound.buffer) == [a[i] ^ b[i] for i in range(len(a))]
    # similarity = fraction equal
    assert hdc.klein4_similarity(a, a) == 1.0
    assert 0.0 <= hdc.klein4_similarity(a, b) <= 1.0
    # bundle of one vector is that vector
    assert list(hdc.klein4_bundle(a).buffer) == list(a)


@pytest.mark.skipif(
    not _native.has_native_klein4_bind(),
    reason="native klein4 bind/bundle/similarity not loaded (no-C env)",
)
class TestNativeDifferential:
    """When native IS present, the native path == the pure-Python path,
    bit-for-bit, across a sweep of sizes + vector counts."""

    def test_bind_native_equals_pure(self):
        for D in (1, 2, 7, 64, 999, 10000):
            a = _codes(7, D)
            b = _codes(13, D)
            native = hdc.klein4_bind(a, b)
            pure = array("B", [a[i] ^ b[i] for i in range(D)])
            assert list(native.buffer) == list(pure), f"bind mismatch at D={D}"

    def test_bundle_native_equals_pure(self):
        for D in (1, 3, 64, 5000):
            for n_vec in (1, 2, 3, 4, 7, 8):
                arrs = [_codes(s + 1, D) for s in range(n_vec)]
                native = hdc.klein4_bundle(*arrs)
                pure = hdc._klein4_bundle_core([array("B", x) for x in arrs])
                assert list(native.buffer) == list(pure), (
                    f"bundle mismatch at D={D}, n_vec={n_vec}")

    def test_similarity_native_equals_pure(self):
        for D in (1, 2, 64, 10000):
            a = _codes(3, D)
            b = _codes(29, D)
            native = hdc.klein4_similarity(a, b)
            # v0.9.0 (F868): klein4_similarity returns the EXACT Q matches/D, so
            # assert native == the exact rational (Q == its (num, den) house form),
            # not an approx float compare.
            matches = sum(1 for x, y in zip(a, b) if x == y)
            assert native == (matches, D), f"similarity mismatch at D={D}"

    def test_bind_self_inverse_native(self):
        a = _codes(11, 4096)
        b = _codes(17, 4096)
        # bind(a, bind(a, b)) == b (XOR self-inverse) — through the native path
        assert list(hdc.klein4_bind(a, hdc.klein4_bind(a, b)).buffer) == list(b)

    def test_native_path_is_actually_taken(self):
        """Sanity: the dispatch accessor is True here, so klein4_bind routed to
        C (this class is skipped otherwise)."""
        assert _native.has_native_klein4_bind() is True

    def test_chirality_bundle_stays_consistent(self):
        """The non-default chirality bundle (a distinct value for asymmetric
        inputs) still runs + returns a length-D klein4 buffer (it is NOT the
        native chunk path)."""
        arrs = [_codes(s + 5, 256) for s in range(3)]
        out = hdc.klein4_bundle(*arrs, mode="chirality", sectors=4)
        assert len(out.buffer) == 256
        assert all(0 <= x <= 3 for x in out.buffer)
