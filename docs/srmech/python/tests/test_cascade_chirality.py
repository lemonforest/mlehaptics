"""Tests for the v0.4.4 chirality mini-set in srmech.amsc.cascade.

chiral_flip (Class C orientation reversal), chiral_dual (Class C ∘ op ∘ Class C),
net_chirality (Class C net-handedness invariant). The chiral dual of an A-N
operator is "same shape, inverse" (MFO §VIII.31.11) — these tests pin the
value-level behaviour and the spectral "same magnitude, inverted phase" property.
"""
import numpy as np
import pytest

from srmech.amsc import cascade


# ── chiral_flip — Class C orientation reversal ──────────────────────────
def test_chiral_flip_reverses_list():
    assert cascade.chiral_flip([1, 2, 3, 4]) == [4, 3, 2, 1]


def test_chiral_flip_preserves_type_tuple_and_str():
    assert cascade.chiral_flip((1, 2, 3)) == (3, 2, 1)
    assert cascade.chiral_flip("abc") == "cba"


def test_chiral_flip_is_involutive():
    x = [3, 1, 4, 1, 5, 9]
    assert cascade.chiral_flip(cascade.chiral_flip(x)) == x


def test_chiral_flip_ndarray():
    x = np.arange(5)
    assert np.array_equal(cascade.chiral_flip(x), np.array([4, 3, 2, 1, 0]))


# ── chiral_dual — Class C ∘ op ∘ Class C ─────────────────────────────────
def _left_rotate(v):
    return v[1:] + v[:1]


def _right_rotate(v):
    return v[-1:] + v[:-1]


def test_chiral_dual_of_left_rotate_is_right_rotate():
    x = [1, 2, 3, 4, 5]
    assert cascade.chiral_dual(_left_rotate, x) == _right_rotate(x)


def test_chiral_dual_of_identity_is_identity():
    x = [2, 7, 1, 8]
    assert cascade.chiral_dual(lambda v: v, x) == x


def test_chiral_dual_of_negate_is_negate_180deg():
    # Class C / N sign operators: the dual reduces to the bare -1 (180deg).
    x = [1.0, -2.0, 3.0]
    assert cascade.chiral_dual(lambda v: [-a for a in v], x) == [-1.0, 2.0, -3.0]


# ── spectral property: same magnitude, inverted phase (MFO §VIII.31.11) ──
def test_chiral_dual_preserves_fft_magnitude():
    n = 64
    t = np.arange(n)
    x = np.sin(2 * np.pi * 3 * t / n) + 0.5 * np.cos(2 * np.pi * 7 * t / n)
    shift = lambda v: np.roll(v, 5)
    y = shift(x)
    yd = cascade.chiral_dual(shift, x)
    magY = np.sqrt((np.fft.fft(y) * np.conj(np.fft.fft(y))).real)
    magYd = np.sqrt((np.fft.fft(yd) * np.conj(np.fft.fft(yd))).real)
    assert np.max(np.sqrt((magY - magYd) ** 2)) < 1e-9  # same shape


def test_chiral_dual_inverts_phase_not_a_global_turn():
    n = 64
    t = np.arange(n)
    x = np.sin(2 * np.pi * 3 * t / n) + 0.5 * np.cos(2 * np.pi * 7 * t / n)
    shift = lambda v: np.roll(v, 5)
    Y = np.fft.fft(shift(x))
    Yd = np.fft.fft(cascade.chiral_dual(shift, x))
    # NOT a constant pi turn: phase-diff varies across active bins.
    mag = np.sqrt((Y * np.conj(Y)).real)
    active = mag > 1e-6 * np.max(mag)
    pdiff = np.angle(Yd[active]) - np.angle(Y[active])
    pdiff = (pdiff + np.pi) % (2 * np.pi) - np.pi
    assert np.std(pdiff) > 0.1  # orientation-flip, not a rigid 180deg


# ── net_chirality — Class C net handedness ──────────────────────────────
@pytest.mark.parametrize("orients,expected", [
    ([1, 1, 1], 1),
    ([1, -1], -1),
    ([-1, -1], 1),
    ([-1, -1, -1], -1),
    ([1, 0, 1], 0),
    ([], 1),
])
def test_net_chirality(orients, expected):
    assert cascade.net_chirality(orients) == expected


def test_net_chirality_zero_short_circuits():
    assert cascade.net_chirality([1, -1, 0, -1]) == 0


# ── registry / export wiring ────────────────────────────────────────────
def test_cascade_ops_includes_chirality():
    for name in ("chiral_flip", "chiral_dual", "net_chirality"):
        assert name in cascade.CASCADE_OPS
        assert name in cascade.__all__


def test_chirality_ops_have_tool_entries():
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    for op in ("chiral_flip", "chiral_dual", "net_chirality"):
        assert schema.lookup(f"srmech.amsc.cascade.{op}") is not None
