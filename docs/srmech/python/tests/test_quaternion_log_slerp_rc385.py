"""rc385 (`#T1048`) — the ℍ log/slerp pair, the inverse of the exp twiddle.

Two shipped ops with byte-exact same-rc C peers:

  * ``srmech.physics.qm.quaternion.quaternion_log(q)`` — the INVERSE of
    ``quaternion_exp`` for a UNIT quaternion q=[w,v]: the tangent [0, θ·v̂] with
    ‖v‖ the Class-K magnitude, θ = atan2(‖v‖, w) ∈ [0, π]. The pure-real branch
    (‖v‖==0) is the Class-K pin-slot: the zero tangent.
  * ``srmech.physics.qm.quaternion.quaternion_slerp(q0, q1, t)`` — the exp/log
    geodesic interpolation on S³: q0·exp(t·log(conj(q0)·q1)).

Genuine checks (NOT smoke tests):

  1. THE WORKED EXACT PROOF: log([4/5, 3/5, 0, 0]) = [0, atan(3/4), 0, 0]
     (real part exactly 0, axis exactly i); ‖v‖² = 9/25 exact.
  2. the Class-K pin-slot: log(±1) = [0, 0, 0, 0].
  3. EXP∘LOG round-trips to the float64 boundary (~1 ulp).
  4. slerp endpoints (t=0 → q0 EXACTLY, t=1 → q1 to float), the midpoint on the
     unit sphere, the degenerate q1=±q0 branch, and the ℝ[i] great-circle sweep.
  5. THE ACCEPTANCE ORACLE (native only): pure vs c_dispatched byte-identity for
     BOTH ops across a quadrant/pin-slot bank (w<0 exercises the atan2 quadrant).
  6. registration ratchet (__all__ / Rosetta c_dispatched / _c_claims / the
     describe() total 546) + a no-abs()/no-libm source guard.

numpy-free (srmech + stdlib only); mirrors notes/quaternion_log_slerp_rc385.py.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import pytest

import srmech
from srmech import _native
from srmech.physics.qm import quaternion as QMOD
from srmech.physics.qm.quaternion import (
    quaternion_log, quaternion_slerp, quaternion_exp, quaternion_conjugate,
    quaternion_norm,
)
from srmech.math.q import Q
from srmech.math.rational import sqrt as _rsqrt   # Class-N; NOT stdlib math.sqrt

_ID = [1.0, 0.0, 0.0, 0.0]


def _bits(x: float) -> bytes:
    return struct.pack("<d", float(x))


def _pure(fn, *args):
    """Run ``fn`` forced through the PURE cascade (native dispatch disabled)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn(*args)
    finally:
        _native.HAS_NATIVE = saved


def _unit(v):
    n = quaternion_norm(v)
    return [c / n for c in v]


# ── 1. the worked exact proof ──────────────────────────────────────────────
def test_log_worked_proof():
    """log([4/5, 3/5, 0, 0]) = [0, atan(3/4), 0, 0]. The unit + ‖v‖² are EXACT
    over ℚ (9/25); θ = atan2(3/5, 4/5) = atan(3/4) is the labelled Class-N lift."""
    q1 = [0.8, 0.6, 0.0, 0.0]
    # exact unit + exact imaginary norm-squared
    assert (Q(4, 5) * Q(4, 5)) + (Q(3, 5) * Q(3, 5)) == Q(1, 1)
    lg = quaternion_log(q1)
    assert lg[0] == 0.0, "log of a unit quaternion is pure-imaginary"
    assert lg[2] == 0.0 and lg[3] == 0.0, "axis is exactly i"
    # θ = atan(3/4); the Q61 cascade tracks libm to ~1 ulp.
    assert abs(lg[1] - math.atan(0.75)) < 1e-12
    # ‖v‖ projects to the double nearest 3/5.
    assert float(_rsqrt(0.36)) == 0.6


# ── 2. the Class-K pin-slot (pure-real q) ──────────────────────────────────
@pytest.mark.parametrize("w", [1.0, -1.0])
def test_log_pure_real_pin_slot(w):
    """log(±1) is the zero tangent — the ‖v‖→0 Class-K pin-slot, no abs()."""
    assert quaternion_log([w, 0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0, 0.0]


# ── 3. exp∘log round-trips ─────────────────────────────────────────────────
@pytest.mark.parametrize("raw", [
    [0.8, 0.6, 0.0, 0.0], [2.0, 1.0, -3.0, 1.0], [-1.0, 1.0, 1.0, 1.0],
    [-2.0, 0.5, -1.5, 0.25], [0.0, 1.0, -2.0, 0.5],
])
def test_exp_of_log_roundtrip(raw):
    """exp(log(q)) == q to the float64 boundary for a unit q (all quadrants)."""
    q = _unit(raw)
    lg = quaternion_log(q)
    back = quaternion_exp(quaternion_norm([0.0, lg[1], lg[2], lg[3]]),
                          [0.0, lg[1], lg[2], lg[3]])
    for i in range(4):
        assert abs(back[i] - q[i]) < 1e-12


def test_log_of_exp_is_pure_imaginary():
    lg = quaternion_log(quaternion_exp(0.5, "ijk"))
    assert lg[0] == 0.0


# ── 4. slerp geometry ──────────────────────────────────────────────────────
def test_slerp_endpoints():
    q1 = [0.8, 0.6, 0.0, 0.0]
    assert quaternion_slerp(_ID, q1, 0.0) == _ID          # t=0 is EXACT
    s1 = quaternion_slerp(_ID, q1, 1.0)
    assert all(abs(s1[i] - q1[i]) < 1e-12 for i in range(4))


def test_slerp_midpoint_on_unit_sphere():
    q1 = _unit([-1.0, 1.0, 1.0, 1.0])
    sh = quaternion_slerp(_ID, q1, 0.5)
    assert abs(sum(c * c for c in sh) - 1.0) < 1e-12


def test_slerp_degenerate_equal_endpoints():
    """slerp(q0, q0, t): conj(q0)·q0 is pure-real → log=0 pin-slot → q0."""
    q0 = _unit([2.0, 1.0, -1.0, 3.0])
    s = quaternion_slerp(q0, q0, 0.37)
    assert all(abs(s[i] - q0[i]) < 1e-12 for i in range(4))


@pytest.mark.parametrize("t", [0.25, 0.5, 0.75])
def test_slerp_sweeps_the_great_circle(t):
    """slerp(1, [cosθ,sinθ,0,0], t) == [cos(tθ), sin(tθ), 0, 0] (to ~1 ulp)."""
    q1 = [0.8, 0.6, 0.0, 0.0]
    theta = quaternion_log(q1)[1]
    st = quaternion_slerp(_ID, q1, t)
    ce = quaternion_exp(t * theta, "i")
    for i in range(4):
        assert abs(st[i] - ce[i]) < 1e-12


# ── 5. THE ACCEPTANCE ORACLE — pure vs c_dispatched byte-identity ──────────
_BANK = [
    _unit([0.8, 0.6, 0.0, 0.0]),        # w>0, axis i (worked proof)
    _unit([2.0, 1.0, -3.0, 1.0]),       # w>0 generic
    _unit([-1.0, 1.0, 1.0, 1.0]),       # w<0 -> atan2 quadrant shift
    _unit([-2.0, 0.5, -1.5, 0.25]),     # w<0 generic
    _unit([0.0, 1.0, -2.0, 0.5]),       # w==0 -> theta = pi/2 branch
    [1.0, 0.0, 0.0, 0.0],               # pure real +1 -> pin-slot
    [-1.0, 0.0, 0.0, 0.0],              # pure real -1 -> pin-slot
]
_T = [0.0, 0.25, 0.5, 0.75, 1.0, -0.5, 1.5]


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="byte-identity oracle needs the built native lib")
@pytest.mark.parametrize("q", _BANK)
def test_log_pure_equals_c_dispatched(q):
    pure, native = _pure(quaternion_log, q), quaternion_log(q)
    assert all(_bits(pure[i]) == _bits(native[i]) for i in range(4)), (
        f"quaternion_log pure vs C diverged for q={q}: {pure} vs {native}")


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="byte-identity oracle needs the built native lib")
@pytest.mark.parametrize("q", _BANK)
@pytest.mark.parametrize("t", _T)
def test_slerp_pure_equals_c_dispatched(q, t):
    pure = _pure(quaternion_slerp, _ID, q, t)
    native = quaternion_slerp(_ID, q, t)
    assert all(_bits(pure[i]) == _bits(native[i]) for i in range(4)), (
        f"quaternion_slerp pure vs C diverged for q={q}, t={t}: "
        f"{pure} vs {native}")


#: A NON-IDENTITY start, so ``conj(q0)*q1`` is a general rotation rather than
#: ``q1`` itself (rc477, `#T1188`). The bank above pins ``q0 = _ID``, which
#: makes the tangent ``t*log(q1)`` -- already a general pure-imaginary vector,
#: which is why those 49 rows DO exercise ``srmech_quat__exp_pure`` -- but it
#: never exercises the left-multiply by a non-unit-real ``q0`` on the way back.
_Q0_BANK = [
    _unit([0.3, -0.4, 0.5, 0.7]),        # generic, w > 0
    _unit([-0.9, 0.1, 0.2, -0.3]),       # w < 0 on the START quaternion
    _unit([0.0, 0.0, 1.0, 0.0]),         # a pure-imaginary start
]


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="byte-identity oracle needs the built native lib")
@pytest.mark.parametrize("q0", _Q0_BANK)
@pytest.mark.parametrize("q1", _BANK)
@pytest.mark.parametrize("t", _T)
def test_slerp_pure_equals_c_dispatched_from_a_nonidentity_start(q0, q1, t):
    """The WIDENING rc477 (`#T1188`) owed, and it is a widening because the row
    above already existed.

    rc477 replaced ``srmech_quat__exp_pure``'s float pre-normalisation
    (``1.0 / tnorm`` then a multiply -- three roundings) with the EXACT
    per-component route the Python ``_resolve_mu4`` takes, so the two
    projections agree by construction rather than by matching float-op order.
    The two disagree on **2441 of 5000** seeded pure-imaginary vectors (3054 of
    15000 components) if only one of them moves, so byte-identity here is the
    detector for getting that edit wrong.

    ⚠️ It is NOT done by passing ``tw`` unnormalised to
    ``srmech_quaternion_exp``: that symbol does not normalise, measured through
    its own export -- ``exp(0.7, [0,1,1,1])`` returns a quaternion of squared
    norm 1.830032857099759 -- and its caller-normalises-mu contract is
    unchanged by that release.
    """
    pure = _pure(quaternion_slerp, q0, q1, t)
    native = quaternion_slerp(q0, q1, t)
    assert all(_bits(pure[i]) == _bits(native[i]) for i in range(4)), (
        f"quaternion_slerp pure vs C diverged for q0={q0}, q1={q1}, t={t}: "
        f"{pure} vs {native}")


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="byte-identity oracle needs the built native lib")
@pytest.mark.parametrize("t", _T)
def test_slerp_the_antipodal_and_zero_tangent_pin_slots(t):
    """The two degenerate arms the bank above cannot reach (rc477, `#T1188`).

    ``q1 = q0`` and ``q1 = -q0`` both make ``conj(q0)*q1`` PURE REAL, so
    ``log`` is zero and ``srmech_quat__exp_pure`` takes its ``tn_sq == 0``
    pin-slot and returns the identity WITHOUT calling the axis normaliser at
    all. That branch is the one an edit to the normalisation can silently
    break -- by reaching the normaliser with a zero vector, which refuses -- so
    it is asserted on both projections and against the closed form.
    """
    q0 = _unit([0.3, -0.4, 0.5, 0.7])
    for q1, expect in ((list(q0), q0), ([-v for v in q0], q0)):
        pure = _pure(quaternion_slerp, q0, q1, t)
        native = quaternion_slerp(q0, q1, t)
        assert all(_bits(pure[i]) == _bits(native[i]) for i in range(4)), (
            f"the pin-slot arm diverged for q1={q1}, t={t}: {pure} vs {native}")
        assert all(_bits(native[i]) == _bits(expect[i]) for i in range(4)), (
            f"a zero tangent must return q0 unchanged; got {native} for "
            f"q1={q1}, t={t}")


# ── 6. registration ratchet + source discipline ───────────────────────────
def test_both_ops_in_all_and_describe_total_is_pinned():
    # NAME CARRIES NO NUMBER ON PURPOSE. This pin tracks a value that MOVES;
    # a name that spells the value is falsified by the next bump and was —
    # 16 such tests were found tree-wide, one named for 367 asserting 663.
    # See test_pinned_names_carry_no_value_rc447.py.
    assert "quaternion_log" in QMOD.__all__
    assert "quaternion_slerp" in QMOD.__all__
    names = {e.name for e in __import__(
        "srmech.introspect.tool_schema", fromlist=["get_tool_schema"]
    ).get_tool_schema().tools}
    assert "srmech.physics.qm.quaternion.quaternion_log" in names
    assert "srmech.physics.qm.quaternion.quaternion_slerp" in names
    assert srmech.describe()["tools"]["total"] == 732


def test_rosetta_rows_present_c_dispatched():
    path = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip()]
    by = {r["exposed_as"]: r for r in rows}
    for name in ("srmech.physics.qm.quaternion.quaternion_log",
                 "srmech.physics.qm.quaternion.quaternion_slerp"):
        assert name in by, f"{name} missing from the Rosetta ledger"
        assert by[name]["bucket"] == "c_dispatched"


def test_c_claims_rows_present():
    from srmech.introspect._c_claims import C_CLAIMS
    assert C_CLAIMS["srmech.physics.qm.quaternion.quaternion_log"] == (
        "srmech_quaternion_log",)
    assert C_CLAIMS["srmech.physics.qm.quaternion.quaternion_slerp"] == (
        "srmech_quaternion_slerp",)


def test_module_imports_no_libm():
    """Cascade-honesty: the quaternion module never imports libm — the trig /
    sqrt ride the Class-N Q61 cascades (abs() is banned too, but is quoted
    dozens of times in the cascade-honesty prose, so it is not string-checkable
    here; the byte-identity oracle proves the no-libm/no-abs paths in effect)."""
    src = Path(QMOD.__file__).read_text(encoding="utf-8")
    assert "\nimport math" not in src and "\nfrom math import" not in src
