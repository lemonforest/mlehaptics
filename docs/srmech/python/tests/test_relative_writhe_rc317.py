"""rc317 — Fuller's Second-Theorem exact-rational RELATIVE WRITHE gates.

``srmech.amsc.rational.relative_writhe`` is the single-integral peer of the O(n²)
:func:`~srmech.amsc.genome.discrete_writhe` double sum — a CERTIFIED TRUNCATION
(exact rational + a stated ``remainder_bound``) of Fuller's
``Wr(C) − Wr(C0) = (1/2π) ∮ (t0×t)·d(t0+t)/(1+t0·t) ds``.

The float reference below (``true_writhe`` = the O(n²) double Gauss sum;
``_fuller`` = the single-integral relative writhe) is the correctness ORACLE —
the same float spike that proved (EXP A) Fuller tracks the true writhe to
≤1.2e-4 on an antiparallel-free coil and (EXP B2) the ±2 jump through the
antipode. It is re-run here in-test; numpy-free (``math`` is stdlib).

Gates:
  F1  antiparallel-free tracks truth (the ground-truth gate)
  F2  the ±2 obstruction (antipodal_events + even-integer offset)
  F3  exact-rational return + valid, monotone remainder_bound
  F4  native == pure (byte-identical)
  F5  no regression (discrete_writhe / cwf_consistency_mod2 / self-writhe = 0)
  F6  dual-projection agreement (platform vs bigint at platform-word precision)
  F7  precision monotonicity + bigint growth + FLOAT-FREE
"""
import math

import pytest

from srmech.amsc import _native
from srmech.amsc.rational import (
    relative_writhe, _CLASSN_PLATFORM_DEN_BITS, _classn_precision,
)
from srmech.amsc.genome import discrete_writhe, cwf_consistency_mod2


# ── float ORACLE (copied from the verified fuller_second_spike.py) ──────────
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])
def _norm(a): return math.sqrt(_dot(a, a))
def _unit(a):
    n = _norm(a)
    return (a[0] / n, a[1] / n, a[2] / n)


def _true_writhe(P):
    n = len(P)
    seg = [_sub(P[(i + 1) % n], P[i]) for i in range(n)]
    mid = [tuple(0.5 * (P[(i + 1) % n][k] + P[i][k]) for k in range(3))
           for i in range(n)]
    tot = 0.0
    for i in range(n):
        for j in range(n):
            if i == j or (i + 1) % n == j or (j + 1) % n == i:
                continue
            r = _sub(mid[i], mid[j])
            d = _norm(r)
            if d == 0.0:
                continue
            tot += _dot(r, _cross(seg[i], seg[j])) / (d * d * d)
    return tot / (4.0 * math.pi)


def _tangents(P):
    n = len(P)
    return [_unit(_sub(P[(i + 1) % n], P[(i - 1) % n])) for i in range(n)]


def _fuller(P0, P):
    n = len(P0)
    t0, t = _tangents(P0), _tangents(P)
    tot, mn = 0.0, float("inf")
    for i in range(n):
        de = 1.0 + _dot(t0[i], t[i])
        if de < mn:
            mn = de
        if abs(de) < 1e-12:
            de = math.copysign(1e-12, de) if de != 0 else 1e-12
        k = _cross(t0[i], t[i])
        k = (k[0] / de, k[1] / de, k[2] / de)
        j = (i + 1) % n
        ds = _sub(_add(t[j], t0[j]), _add(t[i], t0[i]))
        tot += _dot(k, ds)
    return tot / (2.0 * math.pi), mn


def _toroidal_coil(n, r, k):
    out = []
    for i in range(n):
        u = 2 * math.pi * i / n
        R = 1.0 + r * math.cos(k * u)
        out.append((R * math.cos(u), R * math.sin(u), r * math.sin(k * u)))
    return out


def _rodrigues(v, kax, a):
    kv = _cross(kax, v)
    kdv = _dot(kax, v)
    ca, sa = math.cos(a), math.sin(a)
    return (v[0] * ca + kv[0] * sa + kax[0] * kdv * (1 - ca),
            v[1] * ca + kv[1] * sa + kax[1] * kdv * (1 - ca),
            v[2] * ca + kv[2] * sa + kax[2] * kdv * (1 - ca))


def _folded_curve(n, lam, w=0.6):
    du = 2 * math.pi / n
    disp = [(0.0, 0.0, 0.0)]
    for i in range(n):
        u = 2 * math.pi * i / n
        t0 = (-math.sin(u), math.cos(u), 0.0)
        radial = (math.cos(u), math.sin(u), 0.0)
        d = abs(u - math.pi)
        d = min(d, 2 * math.pi - d)
        alpha = lam * math.pi * math.exp(-(d / w) ** 2)
        t = _rodrigues(t0, radial, alpha)
        prev = disp[-1]
        disp.append((prev[0] + t[0] * du, prev[1] + t[1] * du,
                     prev[2] + t[2] * du))
    D = disp[n]
    return [(disp[i][0] - (i / n) * D[0], disp[i][1] - (i / n) * D[1],
             disp[i][2] - (i / n) * D[2]) for i in range(n)]


_SCALE = 1 << 22


def _quantize(P):
    """Exact-rational vertices (num, den) on a 2**22 grid — floats out."""
    return [tuple((round(c * _SCALE), _SCALE) for c in p) for p in P]


def _to_float(P):
    return [tuple(c[0] / c[1] for c in p) for p in P]


def _f(pair):
    return pair[0] / pair[1]


def _is_int_pair(x):
    return (isinstance(x, tuple) and len(x) == 2
            and isinstance(x[0], int) and not isinstance(x[0], bool)
            and isinstance(x[1], int) and not isinstance(x[1], bool))


# ── F1 — antiparallel-free tracks truth (the ground-truth gate) ─────────────
def test_f1_antiparallel_free_tracks_true_writhe():
    n = 240
    C0 = _quantize(_toroidal_coil(n, 0.0, 3))
    C = _quantize(_toroidal_coil(n, 0.30, 3))
    C0f, Cf = _to_float(C0), _to_float(C)
    f_full, min_de = _fuller(C0f, Cf)
    f_true = _true_writhe(Cf) - _true_writhe(C0f)

    res = relative_writhe(C, C0)               # embedding=C, reference=C0; platform
    val = _f(res["value"])

    assert min_de > 0.1                        # genuinely antiparallel-free
    assert res["antipodal_events"] == 0
    # matches the float spike's single-integral sum to ~sqrt precision
    assert abs(val - f_full) < 1e-9, (val, f_full)
    # and tracks the O(n²) TRUE double-Gauss-sum relative writhe to a few e-3
    assert abs(val - f_true) < 5e-3, (val, f_true)
    # the exact rational is within its own stated remainder_bound of the spike
    assert abs(val - f_full) <= _f(res["remainder_bound"]) + 1e-15


# ── F2 — the ±2 obstruction (Z ↠ Z/2, kernel 2Z) ───────────────────────────
def test_f2_pm2_antipodal_obstruction():
    n = 300
    C0 = _quantize(_folded_curve(n, 0.0, 0.6))          # == circle reference
    true0 = _true_writhe(_to_float(C0))

    # antiparallel-free fold (lam below the antipode): no event, tracks truth
    Csafe = _quantize(_folded_curve(n, 0.7, 0.6))
    rsafe = relative_writhe(Csafe, C0)
    assert rsafe["antipodal_events"] == 0
    dsafe = _f(rsafe["value"]) - (_true_writhe(_to_float(Csafe)) - true0)
    assert abs(dsafe) < 5e-2

    # folded THROUGH the antipode (lam > 1): a near-antipodal band + a ±2 jump
    Cfold = _quantize(_folded_curve(n, 1.2, 0.6))
    rfold = relative_writhe(Cfold, C0)
    val = _f(rfold["value"])
    cont = _true_writhe(_to_float(Cfold)) - true0        # antiparallel-free continuation
    diff = val - cont

    assert rfold["antipodal_events"] > 0                 # the pole was approached
    assert _f(rfold["min_one_plus_dot"]) < 0.05          # genuinely near-antipodal
    # off from the continuation by a NONZERO EVEN integer — the same Z→Z/2
    # (kernel 2Z) obstruction cwf_consistency_mod2 reads via the Q8 center parity
    r = round(diff)
    assert r % 2 == 0 and r != 0, (diff, r)
    assert abs(diff - r) < 0.1, diff               # cleanly ±2, not a smear


# ── F3 — exact-rational return + valid, MONOTONE remainder_bound ────────────
def test_f3_exact_rational_and_monotone_bound():
    n = 200
    C0 = _quantize(_toroidal_coil(n, 0.0, 3))
    C = _quantize(_toroidal_coil(n, 0.25, 3))

    # every returned number is an EXACT (num, den) int pair (no float)
    r = relative_writhe(C, C0)
    for key in ("value", "remainder_bound", "min_one_plus_dot"):
        assert _is_int_pair(r[key]), (key, r[key])
        assert r[key][1] > 0
    assert isinstance(r["antipodal_events"], int)
    assert r["mode"] == "platform" and r["precision"] == _CLASSN_PLATFORM_DEN_BITS

    # increasing precision TIGHTENS the bound monotonically; the value converges
    prev_bound = None
    prev_val = None
    ref = relative_writhe(C, C0, precision=256)     # high-precision anchor
    ref_val = _f(ref["value"])
    for P in (40, 80, 160):
        rp = relative_writhe(C, C0, precision=P)
        assert rp["mode"] == "bigint" and rp["precision"] == P
        b = _f(rp["remainder_bound"])
        v = _f(rp["value"])
        # the bound is a VALID upper bound on the residual to the high-P anchor
        assert abs(v - ref_val) <= b, (P, v, ref_val, b)
        if prev_bound is not None:
            assert b < prev_bound, (P, b, prev_bound)         # monotone tighten
            assert abs(v - ref_val) <= abs(prev_val - ref_val) + 1e-30
        prev_bound, prev_val = b, v


# ── F4 — native == pure (byte-identical) ────────────────────────────────────
def test_f4_native_equals_pure(monkeypatch):
    n = 200
    C0 = _quantize(_toroidal_coil(n, 0.0, 3))
    C = _quantize(_toroidal_coil(n, 0.25, 3))

    native = {
        "plat": relative_writhe(C, C0),
        "big": relative_writhe(C, C0, precision=96),
    }
    # force the pure-Python fallback on every dispatching Class-N op
    monkeypatch.setattr(_native, "HAS_NATIVE", False, raising=False)
    monkeypatch.setattr(_native, "LIB", None, raising=False)
    pure = {
        "plat": relative_writhe(C, C0),
        "big": relative_writhe(C, C0, precision=96),
    }
    for k in ("plat", "big"):
        for field in ("value", "remainder_bound", "min_one_plus_dot",
                      "antipodal_events", "mode", "precision"):
            assert native[k][field] == pure[k][field], (k, field)


# ── F5 — no regression (siblings unchanged; self-writhe = 0) ────────────────
def test_f5_no_regression():
    # discrete_writhe: a planar square has no crossings → writhe 0
    square = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)]
    assert discrete_writhe(square, closed=True)["writhe"] == (0, 1)

    # cwf_consistency_mod2 still returns its documented dict shape
    tri_edges = [(0, 1), (1, 2), (2, 0)]
    gains = [(1, 0, 0, 0)] * 3
    cwf = cwf_consistency_mod2(tri_edges, gains)
    assert set(cwf) >= {"lk_mod2", "tw_mod2", "consistent", "note"}

    # relative_writhe of a curve against ITSELF is exactly 0 (Wr(C) − Wr(C) = 0)
    C = _quantize(_toroidal_coil(120, 0.2, 3))
    self_r = relative_writhe(C, C)
    assert self_r["value"] == (0, 1)
    assert self_r["antipodal_events"] == 0


# ── F6 — dual-projection agreement (platform ↔ bigint) ──────────────────────
def test_f6_dual_projection_agreement():
    n = 200
    C0 = _quantize(_toroidal_coil(n, 0.0, 3))
    C = _quantize(_toroidal_coil(n, 0.30, 3))

    plat = relative_writhe(C, C0)                        # platform
    big = relative_writhe(C, C0, precision=_CLASSN_PLATFORM_DEN_BITS)  # bigint @ word
    assert plat["mode"] == "platform" and big["mode"] == "bigint"
    # the two co-equal projections agree within the platform remainder_bound
    assert abs(_f(plat["value"]) - _f(big["value"])) <= _f(plat["remainder_bound"])


# ── F7 — precision monotonicity + bigint growth + FLOAT-FREE ────────────────
def test_f7_precision_monotone_bigint_growth_float_free():
    n = 200
    C0 = _quantize(_toroidal_coil(n, 0.0, 3))
    C = _quantize(_toroidal_coil(n, 0.25, 3))

    prev_bound = None
    prev_den_bits = None
    prev_num_bits = None
    for P in (40, 100, 200):
        r = relative_writhe(C, C0, precision=P)
        # FLOAT-FREE: every returned scalar is an exact int / int-pair, no float
        assert isinstance(r["antipodal_events"], int)
        for key in ("value", "remainder_bound", "min_one_plus_dot"):
            assert _is_int_pair(r[key])
            assert not isinstance(r[key][0], float)
            assert not isinstance(r[key][1], float)
        vn, vd = r["value"]
        b = _f(r["remainder_bound"])
        if prev_bound is not None:
            assert b < prev_bound, (P, b, prev_bound)              # monotone
            # the srmech-native bigint num/den LENGTHEN with P
            assert vd.bit_length() > prev_den_bits, (P, vd.bit_length())
            assert vn.bit_length() > prev_num_bits, (P, vn.bit_length())
        prev_bound = b
        prev_den_bits = vd.bit_length()
        prev_num_bits = vn.bit_length()


def test_precision_contract_helper():
    """The reusable Class-N precision-contract pilot maps the knob correctly."""
    plat = _classn_precision(None)
    assert plat.mode == "platform" and plat.effective == _CLASSN_PLATFORM_DEN_BITS
    big = _classn_precision(128)
    assert big.mode == "bigint" and big.effective == 128
    assert big.sqrt_bits > 128 and big.pi_digits >= 40
    with pytest.raises(ValueError):
        _classn_precision(0)
    with pytest.raises(TypeError):
        _classn_precision(1.5)
