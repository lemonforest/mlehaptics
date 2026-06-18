"""v0.7.0rc20 — native whole-array C peers for the HD loop division family
agree with the pure-Python Cayley-Dickson recursion (the Rosetta agreement-
attestation).

Per the "C = transpiled Python" discipline (srmech notebook §3.29.4–§3.29.5:
one SSoT — meaning : Python AND C source : Compiled C), the C rendering of an
op must agree with its Python rendering. `loop_bind_hd` got its native peer in
rc11/rc17; rc20 adds the companions `srmech_loop_{conj,inv,unbind,runbind}_hd_f64`
(srmech_loophd_family.c). These tests compare the native whole-array peer against
the pure-Python recursion engine (`_loop_bind_raw` / `_loop_conj_raw`), NOT the
per-block C path — so they attest the two co-equal renderings agree, not that
C agrees with itself.

When the native lib is absent (Pyodide / pure wheel) the native helpers return
None and these tests skip with a log (the pure-Python fallback is exercised by
``test_loop_hd_division.py``).

rc125 (numpy-free, #564): this test is itself numpy-FREE — the HD ops return
``list[float]``; block math is explicit, norms ride ``mat_norm``, random blocks
come from stdlib ``random.Random`` (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""

import random

import pytest

from srmech.amsc.laplacian import mat_dot, mat_norm
from srmech.amsc import hdc
from srmech.amsc.hdc import LOOP_DIM

NB = 48  # blocks; D = NB * 8 = 384 (an HD width, > one octonion)


def _vsub(u, v):
    return [u[i] - v[i] for i in range(len(u))]


def _rand_blocks(seed, *, unit=False):
    """NB random dim-8 blocks flattened to one HD vector (optionally unit-norm)."""
    rng = random.Random(seed)
    out = []
    for _ in range(NB):
        b = [rng.gauss(0.0, 1.0) for _ in range(LOOP_DIM)]
        if unit:
            nrm = sum(x * x for x in b) ** 0.5
            b = [x / nrm for x in b]
        out.extend(b)
    return out


def _blocks(v):
    return [v[k * LOOP_DIM:(k + 1) * LOOP_DIM] for k in range(len(v) // LOOP_DIM)]


def _concat(blocks):
    out = []
    for b in blocks:
        out.extend(b)
    return out


def _require_native(symbol):
    if not hdc._loop_native_ready(symbol):
        pytest.skip(f"native {symbol} not present (pure-Python wheel) — "
                    "pure-Python path covered by test_loop_hd_division.py")


# ----------------------------------------------------------------------
# native peer == pure-Python Cayley-Dickson recursion (Rosetta agreement)
# ----------------------------------------------------------------------


def test_native_conj_hd_matches_python_recursion():
    _require_native("srmech_loop_conj_hd_f64")
    x = _rand_blocks(2026)
    native = hdc._try_native_loop_conj_hd(x)
    assert native is not None
    want = _concat([hdc._loop_conj_raw(b) for b in _blocks(x)])
    assert native == want  # conj is sign flips — exact


def test_native_inv_hd_matches_python_recursion():
    _require_native("srmech_loop_inv_hd_f64")
    # non-unit blocks (distinct scales) — exercises the norm² gate.
    xb = _blocks(_rand_blocks(7))
    for k in range(NB):
        xb[k] = [v * (0.5 + 0.13 * k) for v in xb[k]]
    x = _concat(xb)
    native = hdc._try_native_loop_inv_hd(x)
    assert native is not None
    want = _concat([
        [c / mat_dot(b, b) for c in hdc._loop_conj_raw(b)]
        for b in _blocks(x)
    ])
    assert mat_norm(_vsub(native, want)) < 1e-13


def test_native_unbind_hd_matches_python_recursion():
    _require_native("srmech_loop_unbind_hd_f64")
    a = _rand_blocks(11)
    b = _rand_blocks(12)
    native = hdc._try_native_loop_unbind_hd(a, b)
    assert native is not None
    want = _concat(
        [hdc._loop_bind_raw(hdc._loop_conj_raw(ab), bb)
         for ab, bb in zip(_blocks(a), _blocks(b))])
    assert mat_norm(_vsub(native, want)) < 1e-12


def test_native_runbind_hd_matches_python_recursion():
    _require_native("srmech_loop_runbind_hd_f64")
    a = _rand_blocks(21)
    b = _rand_blocks(22)
    native = hdc._try_native_loop_runbind_hd(a, b)
    assert native is not None
    want = _concat(
        [hdc._loop_bind_raw(bb, hdc._loop_conj_raw(ab))
         for ab, bb in zip(_blocks(a), _blocks(b))])
    assert mat_norm(_vsub(native, want)) < 1e-12


# ----------------------------------------------------------------------
# the public wrapper returns the native result when the peer is present
# ----------------------------------------------------------------------


def test_wrappers_dispatch_to_native_when_present():
    _require_native("srmech_loop_conj_hd_f64")
    x = _rand_blocks(31)
    a = _rand_blocks(32)
    b = _rand_blocks(33)
    assert hdc.loop_conj_hd(x) == hdc._try_native_loop_conj_hd(x)
    assert hdc.loop_inv_hd(x) == hdc._try_native_loop_inv_hd(x)
    assert hdc.loop_unbind_hd(a, b) == hdc._try_native_loop_unbind_hd(a, b)
    assert hdc.loop_runbind_hd(a, b) == hdc._try_native_loop_runbind_hd(a, b)


# ----------------------------------------------------------------------
# round-trip identities hold on the native path
# ----------------------------------------------------------------------


def test_native_round_trip_left_and_right_unbind():
    _require_native("srmech_loop_unbind_hd_f64")
    a = _rand_blocks(41, unit=True)
    v = _rand_blocks(42, unit=True)
    # left-built: b = a·v  ⟹  loop_unbind_hd(a, b) == v
    assert mat_norm(_vsub(hdc.loop_unbind_hd(a, hdc.loop_bind_hd(a, v)), v)) < 1e-12
    # right-built: b = v·a ⟹  loop_runbind_hd(a, b) == v
    assert mat_norm(_vsub(hdc.loop_runbind_hd(a, hdc.loop_bind_hd(v, a)), v)) < 1e-12


def test_native_inv_hd_is_per_block_bind_identity():
    _require_native("srmech_loop_inv_hd_f64")
    x = _rand_blocks(43, unit=True)
    prod = _blocks(hdc.loop_bind_hd(x, hdc.loop_inv_hd(x)))
    e0 = [0.0] * LOOP_DIM
    e0[0] = 1.0
    for k in range(NB):
        assert mat_norm(_vsub(prod[k], e0)) < 1e-12


# ----------------------------------------------------------------------
# zero-block contract: native returns BAD_INPUT → None → fallback raises
# ----------------------------------------------------------------------


def test_inv_hd_zero_block_raises_through_fallback():
    x = _rand_blocks(51, unit=True)
    xb = _blocks(x)
    xb[NB // 2] = [0.0] * LOOP_DIM  # one zero block — no Moufang inverse
    x = _concat(xb)
    # native peer (if present) returns None on BAD_INPUT; the wrapper then
    # falls through to the per-block Python path, which asserts on the zero.
    assert hdc._try_native_loop_inv_hd(x) is None or not hdc._loop_native_ready(
        "srmech_loop_inv_hd_f64")
    with pytest.raises(AssertionError, match="zero vector"):
        hdc.loop_inv_hd(x)
