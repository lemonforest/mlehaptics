"""§59 / F861 continuous-phase Klein-4 graduation (0.9.0rc3).

The LM-agnostic ``klein4_phase_key`` / ``klein4_phase_bind`` primitive graduates
from siona to srmech per UPSTREAM §62. Tests are numpy-free and assert the
EXACT rational similarity law (a :class:`Q`, never ``pytest.approx`` of a float),
plus reversibility, the σ-mirror, and the population-code key construction.
"""
from array import array

import pytest

from srmech.amsc import hdc
from srmech.amsc.q import Q
from srmech.amsc._native import HAS_NATIVE


def _circ_dist(df: float) -> float:
    d = df % 1.0
    return min(d, 1.0 - d)


# ── the key construction (population code: elem on a circular half-window) ──

def test_phase_key_construction_default_half_window():
    k = hdc.klein4_phase_key(8, 0.0)            # start=0, width=4, elem=2
    assert list(k.buffer) == [2, 2, 2, 2, 0, 0, 0, 0]


def test_phase_key_offset_wraps_circularly():
    k = hdc.klein4_phase_key(8, 0.5)            # start=4, width=4
    assert list(k.buffer) == [0, 0, 0, 0, 2, 2, 2, 2]
    kw = hdc.klein4_phase_key(8, 0.875)         # start=7 → wraps [7,0,1,2)
    assert list(kw.buffer) == [2, 2, 2, 0, 0, 0, 0, 2]


def test_phase_key_elem_and_width_overrides():
    k = hdc.klein4_phase_key(8, 0.0, elem=1, width=2)
    assert list(k.buffer) == [1, 1, 0, 0, 0, 0, 0, 0]


def test_phase_key_rejects_bad_args():
    with pytest.raises(ValueError):
        hdc.klein4_phase_key(0, 0.0)            # D must be positive
    with pytest.raises(ValueError):
        hdc.klein4_phase_key(8, 0.0, elem=4)    # elem out of {0,1,2,3}
    with pytest.raises(ValueError):
        hdc.klein4_phase_key(8, 0.0, width=9)   # width > D


# ── the exact-rational similarity law: 1 − 2·circ_dist(Δφ) (stay-rational) ──

def test_phase_similarity_is_exact_rational_law():
    D = 1000
    h = hdc.klein4_random(D, seed=42)
    base = hdc.klein4_phase_bind(h, 0.0)
    cases = {0.0: Q(1, 1), 0.25: Q(1, 2), 0.5: Q(0, 1),
             0.9: Q(4, 5), 0.1: Q(4, 5), 0.75: Q(1, 2)}
    for df, expect in cases.items():
        s = hdc.klein4_similarity(base, hdc.klein4_phase_bind(h, df))
        assert isinstance(s, Q)
        assert s == expect                      # EXACT, never approx
        assert float(s) == pytest.approx(1.0 - 2.0 * _circ_dist(df))


def test_phase_bind_is_reversible():
    h = hdc.klein4_random(256, seed=7)
    pb = hdc.klein4_phase_bind(h, 0.3)
    back = hdc.klein4_phase_bind(pb, 0.3)        # same key twice = identity
    assert bytes(back.buffer) == bytes(h.buffer)


def test_phase_sigma_mirror():
    h = hdc.klein4_random(800, seed=11)
    base = hdc.klein4_phase_bind(h, 0.0)
    sp = hdc.klein4_similarity(base, hdc.klein4_phase_bind(h, 0.2))
    sm = hdc.klein4_similarity(base, hdc.klein4_phase_bind(h, -0.2))
    assert sp == sm                             # ±φ equidistant from base


def test_phase_bind_accepts_bytes_and_hv():
    raw = bytes([0, 1, 2, 3] * 4)
    a = hdc.klein4_phase_bind(raw, 0.25)
    b = hdc.klein4_phase_bind(hdc.HV(array("B", raw), sectors=4), 0.25)
    assert bytes(a.buffer) == bytes(b.buffer)


# ── surface bookkeeping ──

def test_phase_ops_public_and_counted():
    assert "klein4_phase_key" in hdc.__all__
    assert "klein4_phase_bind" in hdc.__all__
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] >= 314


@pytest.mark.skipif(not HAS_NATIVE, reason="native lib absent")
def test_phase_key_native_matches_pure():
    # the C srmech_klein4_phase_key fill is bit-identical to the pure window
    from srmech.amsc.hdc import _klein4_phase_key_core, _klein4_phase_start
    for D, frac, elem, width in [(64, 0.3, 2, None), (100, 0.9, 1, 25), (8, 0.0, 3, 4)]:
        w = D // 2 if width is None else width
        start = _klein4_phase_start(D, frac)
        got = hdc.klein4_phase_key(D, frac, elem=elem, width=width)
        assert bytes(got.buffer) == bytes(_klein4_phase_key_core(D, start, w, elem))
