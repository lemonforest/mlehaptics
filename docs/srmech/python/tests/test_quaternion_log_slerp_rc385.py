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
