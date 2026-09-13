"""rc473 (`#T1188`) — the two kepler argument slots where the C projection
SERVED what the pure projection REFUSED, and no filed row named the slot.

WHAT WAS MEASURED, and how
==========================
A slot sweep: one argument varied at a time off a known-good baseline, every
row driven through the PUBLIC op on a native cell and on a pure cell, plus the
raw C symbol on the native cell so a row can separate "the wrapper refused"
from "the symbol refused". 63 rows per cell; 11 differed; **three** of those
eleven were the serve-vs-refuse class (ADR-0009 §2.4):

    pin_slot(theta=0.0, pin_offset=1.0, pin_distance=+inf)
        C  -> (SRMECH_OK, 0.0)                  pure -> TypeError
    pin_slot(theta=0.0, pin_offset=1.0, pin_distance=-inf)
        C  -> (SRMECH_OK, 3.141592653589793)    pure -> TypeError
    kepler_solve(M=pi/2, e=0.0549, tolerance=+inf, max_iter=20)
        C  -> (SRMECH_OK, 1.625613861425157)    pure -> TypeError

The +inf tolerance row is the sharpest: `|delta| < +inf` is true on the first
Newton step, so C returns the ONE-STEP estimate and reports convergence. NaN
and -inf tolerances were the same defect wearing a different answer — C ran
the loop out and told the caller "did not converge" about an argument that was
never a tolerance (SRMECH_ERR_OVERFLOW, i.e. a DIFFERENT wrong story, not a
refusal of the argument).

WHY THESE SLOTS AND NOT A CALLEE
================================
Neither argument ever reaches a callee that could check it. `pin_distance` and
`pin_offset` enter at the bare double arithmetic `x = pin_distance +
pin_offset * cs`; `tolerance` is only ever the right-hand side of
`adelta < tolerance`. So the refusal belongs to the function whose arguments
they are, which is why the guards sit beside `srmech_pin_slot`'s existing
(0, 0) refusal and `srmech_kepler_solve`'s existing eccentricity band rather
than inside srmech_sin / srmech_cos / srmech_atan2.

Both projections move together, and the Python guard is NOT a cover: rc473's
own `equation_of_centre` lesson is that a pre-dispatch guard over a CASCADE
-DOMAIN refusal hides the C defect for release candidates at a time. These are
PRECONDITIONS on the op's own arguments — the category `pin_slot` already
raises before dispatch for, documented there as legitimate *"because it is a
precondition on the ARGUMENTS and the C peer refuses the same pair"*. The
tests below drive the C SYMBOL directly, so that "and the C peer refuses" half
is asserted rather than asserted-about.

WHAT DELIBERATELY DID NOT MOVE
==============================
A FINITE tolerance of any sign or magnitude. Zero, -0.0, negative and huge
finite tolerances still run to non-convergence in BOTH projections, which is
what they already agreed on; `test_a_finite_tolerance_is_unchanged` is that
control, and without it this file would be equally consistent with a guard
that refuses far more than it was written to refuse.

numpy-free.
"""
from __future__ import annotations

import ctypes
import math
from pathlib import Path

import pytest

from srmech import _native
from srmech.math import kepler


_NATIVE_PKG_DIR = Path(_native.__file__).resolve().parent
_LIB_SUFFIXES = {".so", ".dll", ".dylib", ".pyd"}
_LIB_FILES = [
    p for p in (_NATIVE_PKG_DIR.iterdir() if _NATIVE_PKG_DIR.is_dir() else [])
    if p.is_file() and p.suffix in _LIB_SUFFIXES
]
_PURE_CELL = (not _native.HAS_NATIVE) and not _LIB_FILES

_needs_native = pytest.mark.skipif(
    _PURE_CELL,
    reason=(
        "genuinely pure cell: HAS_NATIVE is False AND no shared library file "
        f"exists in {_NATIVE_PKG_DIR}. The C-symbol rows below have nothing "
        "to drive; the projection-equality rows run on both cells."
    ),
)

NAN = float("nan")
INF = float("inf")

#: Every non-finite spelling, so a guard that catches one and not another is
#: reported rather than averaged away.
NON_FINITE: "tuple[tuple[str, float], ...]" = (
    ("nan", NAN), ("+inf", INF), ("-inf", -INF),
)

#: The baseline each sweep varies ONE slot off.
PIN_BASE = {"theta": 0.0, "pin_offset": 1.0, "pin_distance": 1.0}
KEP_BASE = {"M_rad": 1.5707963267948966, "e": 0.0549,
            "tolerance": 1e-12, "max_iter": 20}


def _c_pin_slot(theta: float, pin_offset: float, pin_distance: float):
    out = ctypes.c_double(0.0)
    st = _native.LIB.srmech_pin_slot(
        ctypes.c_double(theta), ctypes.c_double(pin_offset),
        ctypes.c_double(pin_distance), ctypes.byref(out))
    return int(st), float(out.value)


def _c_kepler_solve(m_rad: float, e: float, tol: float, max_iter: int):
    out = ctypes.c_double(0.0)
    st = _native.LIB.srmech_kepler_solve(
        ctypes.c_double(m_rad), ctypes.c_double(e), ctypes.c_double(tol),
        ctypes.c_uint32(max_iter), ctypes.byref(out))
    return int(st), float(out.value)


# ── the C symbol refuses, which is the half a Python guard cannot assert ──

@_needs_native
@pytest.mark.parametrize("slot", ("pin_offset", "pin_distance"))
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_c_pin_slot_refuses_non_finite_geometry(
    slot: str, label: str, value: float,
) -> None:
    """`srmech_pin_slot` returns SRMECH_ERR_BAD_INPUT, at the symbol."""
    kwargs = dict(PIN_BASE)
    kwargs[slot] = value
    st, out = _c_pin_slot(kwargs["theta"], kwargs["pin_offset"],
                          kwargs["pin_distance"])
    assert st == _native.SRMECH_ERR_BAD_INPUT, (
        f"srmech_pin_slot with {slot}={label} returned status {st} and wrote "
        f"{out!r}. Through the rc473 A6 pass pin_distance=+inf returned "
        "(SRMECH_OK, 0.0) and -inf returned (SRMECH_OK, 3.141592653589793) "
        "where the pure projection raised; this row is that repair."
    )


@_needs_native
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_c_kepler_solve_refuses_a_non_finite_tolerance(
    label: str, value: float,
) -> None:
    """`srmech_kepler_solve` returns SRMECH_ERR_BAD_INPUT, at the symbol.

    Note what it must NOT return: SRMECH_ERR_OVERFLOW. That is this function's
    non-convergence status, and it is what NaN and -inf produced before the
    repair — a wrong story about the argument rather than a refusal of it.
    """
    st, out = _c_kepler_solve(KEP_BASE["M_rad"], KEP_BASE["e"], value,
                              KEP_BASE["max_iter"])
    assert st == _native.SRMECH_ERR_BAD_INPUT, (
        f"srmech_kepler_solve with tolerance={label} returned status {st} and "
        f"wrote {out!r}. Before the repair +inf returned (SRMECH_OK, "
        "1.625613861425157) — the one-Newton-step estimate reported as "
        f"converged — and nan / -inf returned SRMECH_ERR_OVERFLOW "
        f"({_native.SRMECH_ERR_OVERFLOW})."
    )


@_needs_native
def test_the_c_refusal_is_the_argument_and_not_the_eccentricity_shortcut() -> None:
    """`e == 0` takes an early-return path; the tolerance guard precedes it.

    Without this row the guard could sit after `if (e == 0.0) return OK;` and
    a circular orbit with a nonsense tolerance would still be served by C
    while the Python precondition refused it — a NEW divergence introduced by
    the repair, in the slot the repair exists for.
    """
    st, out = _c_kepler_solve(KEP_BASE["M_rad"], 0.0, INF, 20)
    assert st == _native.SRMECH_ERR_BAD_INPUT, (
        f"srmech_kepler_solve(M, e=0.0, tolerance=+inf) returned status {st} "
        f"and wrote {out!r}; the guard must precede the e == 0 shortcut so "
        "the two projections still agree there."
    )


# ── both projections refuse, in ONE text ──

@pytest.mark.parametrize("slot", ("pin_offset", "pin_distance"))
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_pin_slot_refuses_non_finite_geometry(
    slot: str, label: str, value: float,
) -> None:
    kwargs = dict(PIN_BASE)
    kwargs[slot] = value
    with pytest.raises(ValueError) as excinfo:
        kepler.pin_slot(**kwargs)
    assert "must be finite" in str(excinfo.value), (
        f"pin_slot({slot}={label}) raised {excinfo.value!r}; the refusal text "
        "must be the same in both cells (rc466 rule D1), and before the "
        "repair the pure cell's was a raw TypeError from `float + Q`."
    )


@pytest.mark.parametrize("label,value", NON_FINITE)
def test_kepler_solve_refuses_a_non_finite_tolerance(
    label: str, value: float,
) -> None:
    with pytest.raises(ValueError) as excinfo:
        kepler.kepler_solve(KEP_BASE["M_rad"], KEP_BASE["e"],
                            tolerance=value, max_iter=KEP_BASE["max_iter"])
    assert "tolerance must be finite" in str(excinfo.value), (
        f"kepler_solve(tolerance={label}) raised {excinfo.value!r}"
    )


# ── the controls: what the repair must NOT have taken with it ──

#: `(tolerance, converges?)` — the MEASURED pre-repair behaviour of every
#: finite tolerance in the sweep, on both cells. A POSITIVE tolerance is met
#: (a huge one on the first Newton step); a zero or negative one never is, so
#: the loop runs out. This table was written the other way round first — "the
#: tight one converges; the rest run out" — and 1e300 falsified it on the
#: first run, which is the whole reason a control states measurements rather
#: than expectations.
_FINITE_TOLERANCES: "tuple[tuple[float, bool], ...]" = (
    (1e-12, True), (1e300, True), (3.602879701896397e16, True),
    (0.0, False), (-0.0, False), (-1.0, False),
    (-3.602879701896397e16, False),
)


@pytest.mark.parametrize("tol,converges", _FINITE_TOLERANCES)
def test_a_finite_tolerance_is_unchanged(tol: float, converges: bool) -> None:
    """Finite tolerances of every sign and magnitude still behave as before.

    Both outcomes are the pre-repair behaviour and both are what the two
    projections already agreed on, so a guard that swallowed either would be
    over-refusing — which is the failure mode a repair to a refusal contract
    is most exposed to.
    """
    if converges:
        value = kepler.kepler_solve(KEP_BASE["M_rad"], KEP_BASE["e"],
                                    tolerance=tol, max_iter=20)
        assert isinstance(value, float) and value == value, (
            f"kepler_solve(tolerance={tol!r}) returned {value!r}"
        )
        return
    with pytest.raises(RuntimeError) as excinfo:
        kepler.kepler_solve(KEP_BASE["M_rad"], KEP_BASE["e"],
                            tolerance=tol, max_iter=20)
    assert "did not converge" in str(excinfo.value)


@pytest.mark.parametrize(
    "pin_distance", (1.0, -1.0, 0.0, 1e300, 3.602879701896397e16),
)
def test_a_finite_geometry_is_unchanged(pin_distance: float) -> None:
    """Finite geometry still answers, including the magnitudes near the door."""
    value = kepler.pin_slot(theta=0.0, pin_offset=1.0,
                            pin_distance=pin_distance)
    assert isinstance(value, float)
    assert -math.pi - 1e-9 <= value <= math.pi + 1e-9, (
        f"pin_slot returned {value!r}, outside the follower angle's range"
    )


def test_the_zero_pair_precondition_still_refuses_first() -> None:
    """The guard added beside it did not displace the (0, 0) refusal."""
    with pytest.raises(ValueError) as excinfo:
        kepler.pin_slot(theta=0.0, pin_offset=0.0, pin_distance=0.0)
    assert "cannot both be zero" in str(excinfo.value)
