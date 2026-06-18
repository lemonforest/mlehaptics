"""Tests for the v0.4.4 chirality mini-set in srmech.amsc.cascade.

chiral_flip (Class C orientation reversal), chiral_dual (Class C ∘ op ∘ Class C),
net_chirality (Class C net-handedness invariant). The chiral dual of an A-N
operator is "same shape, inverse" (MFO §VIII.31.11) — these tests pin the
value-level behaviour and the spectral "same magnitude, inverted phase" property.

numpy-free: the spectral checks use a pure-Python DFT (Σ x[t]·e^{-2πikt/n}) as
the reference oracle; signals are built with ``math.sin``/``math.cos`` and the
roll is a pure-Python slice rotation. The old ``test_chiral_flip_ndarray`` was
deleted — it only asserted ``np.array_equal`` on an ``np.arange`` input, which
no longer applies now that numpy is out of srmech and the op takes plain lists.
"""
import cmath
import math
import statistics

import pytest

from srmech.amsc import cascade


# ── pure-Python DFT oracle (numpy-free) ─────────────────────────────────
def _dft(x):
    """Σ_t x[t]·e^{-2πikt/n} — the textbook DFT, the numpy-free oracle."""
    n = len(x)
    return [sum(x[t] * cmath.exp(-2j * cmath.pi * k * t / n) for t in range(n))
            for k in range(n)]


def _roll(v, shift):
    """Circular right-shift of a list by ``shift`` (numpy.roll equivalent)."""
    if not v:
        return list(v)
    s = shift % len(v)
    if s == 0:
        return list(v)
    return list(v[-s:]) + list(v[:-s])


# ── chiral_flip — Class C orientation reversal ──────────────────────────
def test_chiral_flip_reverses_list():
    assert cascade.chiral_flip([1, 2, 3, 4]) == [4, 3, 2, 1]


def test_chiral_flip_preserves_type_tuple_and_str():
    assert cascade.chiral_flip((1, 2, 3)) == (3, 2, 1)
    assert cascade.chiral_flip("abc") == "cba"


def test_chiral_flip_is_involutive():
    x = [3, 1, 4, 1, 5, 9]
    assert cascade.chiral_flip(cascade.chiral_flip(x)) == x


def test_chiral_flip_list_of_range():
    """A list of integers reverses element-for-element."""
    assert cascade.chiral_flip([0, 1, 2, 3, 4]) == [4, 3, 2, 1, 0]


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
def _make_signal(n):
    return [math.sin(2 * math.pi * 3 * t / n) + 0.5 * math.cos(2 * math.pi * 7 * t / n)
            for t in range(n)]


def test_chiral_dual_preserves_fft_magnitude():
    n = 64
    x = _make_signal(n)
    shift = lambda v: _roll(list(v), 5)
    y = shift(x)
    yd = cascade.chiral_dual(shift, x)
    magY = [abs(c) for c in _dft(y)]
    magYd = [abs(c) for c in _dft(yd)]
    # Same shape: signed difference per bin stays below 1e-9.
    assert max(abs(a - b) for a, b in zip(magY, magYd)) < 1e-9


def test_chiral_dual_inverts_phase_not_a_global_turn():
    n = 64
    x = _make_signal(n)
    shift = lambda v: _roll(list(v), 5)
    Y = _dft(shift(x))
    Yd = _dft(cascade.chiral_dual(shift, x))
    # NOT a constant pi turn: phase-diff varies across active bins.
    mag = [abs(c) for c in Y]
    mx = max(mag)
    active = [i for i, m in enumerate(mag) if m > 1e-6 * mx]
    pdiff = []
    for i in active:
        d = cmath.phase(Yd[i]) - cmath.phase(Y[i])
        d = (d + math.pi) % (2 * math.pi) - math.pi
        pdiff.append(d)
    assert statistics.pstdev(pdiff) > 0.1  # orientation-flip, not a rigid 180deg


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
