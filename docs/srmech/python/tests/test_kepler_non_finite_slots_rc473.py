"""rc473 (`#T1188`) — the kepler argument slots where the C projection SERVED
what the pure projection REFUSED (or the reverse), and no filed row named the
slot.

WHAT WAS MEASURED, and how
==========================
A slot sweep (`notes/_rc473_twin_d2_slot_sweep.py`, joined by
`notes/_rc473_twin_d2_diff.py`): one argument varied at a time off a
known-good baseline, every row driven through the PUBLIC op on a native cell
and on a genuinely pure cell, plus the raw C symbol on the native cell so a
row can separate "the wrapper refused" from "the symbol refused". Conditions:
WSL2 gcc 13.3.0 Release + SRMECH_PEDANTIC=ON, `srmech_rational_sqrt(NaN)` ->
status 2, ABI 26, CPython 3.12.3, numpy absent; the pure cell is the same
bytes with no library file. At `1ab8d405b`: 107 rows per cell, 17 differed,
SEVEN of them serve-vs-refuse (ADR-0009 §2.4):

    pin_slot(theta=0.0, pin_offset=1.0, pin_distance=+inf)
        C  -> (SRMECH_OK, 0.0)                  pure -> TypeError
    pin_slot(theta=0.0, pin_offset=1.0, pin_distance=-inf)
        C  -> (SRMECH_OK, 3.141592653589793)    pure -> TypeError
    kepler_solve(M=pi/2, e=0.0549, tolerance=+inf, max_iter=20)
        C  -> (SRMECH_OK, 1.625613861425157)    pure -> TypeError
    kepler_solve(M=pi/2, e=0.0549, tolerance=1e-12, max_iter=2**32 + 1)
        native -> RuntimeError (the wire carried 1)   pure -> 1.625613861239322
    kepler_solve(..., tolerance=5e-324 / 1e-310 / 2.2250738585072014e-308)
        native serves, pure never converges — the convergence seam, FILED
        below rather than repaired, because it is not a slot

The +inf tolerance row is the sharpest: `|delta| < +inf` is true on the first
Newton step, so C returned the ONE-STEP estimate (the same value the
`max_iter=1` row prints) and reported convergence. NaN and -inf tolerances
were the same defect wearing a different answer — C ran the loop out and the
native cell said "did not converge" about an argument that was never a
tolerance. After the repair: 107 rows per cell, 11 differ, 3 serve-vs-refuse
— the three tiny tolerances and nothing else.

WHERE EACH REFUSAL LIVES
========================
Neither `pin_offset` / `pin_distance` nor `tolerance` reaches a callee that
could check it: the geometry enters at the bare double arithmetic `x =
pin_distance + pin_offset * cs`, and `tolerance` is only ever the right-hand
side of `adelta < tolerance`. So the refusal belongs to `srmech_pin_slot` and
`srmech_kepler_solve`, beside their existing (0, 0) refusal and eccentricity
band. The Python checks that supply the one text both cells raise sit AFTER
the native call — the placement rc473 gave `equation_of_centre` — so a native
cell reaches the refusal through the C symbol, and the rows below assert that
the symbol was consulted as well as that it refuses.

`max_iter` is the exception, and the reason is the wire: `srmech_kepler_solve`
takes a `uint32_t`, `ctypes.c_uint32` wraps a wider value silently, and no C
code can refuse a value its parameter type cannot hold. That precondition is
therefore checked before dispatch, in both cells, with one text.

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


# ── PLACEMENT: a native cell reaches the refusal THROUGH the C symbol ──

class _CountingLib:
    """Stand-in for `_native.LIB` that counts calls to ONE symbol.

    Every other attribute is the real library's, so the dispatch under test
    runs unchanged; only the named symbol is wrapped.
    """

    def __init__(self, lib: object, symbol: str) -> None:
        self._lib = lib
        self._symbol = symbol
        self.calls = 0

    def __getattr__(self, name: str):
        attr = getattr(self._lib, name)
        if name != self._symbol:
            return attr

        def counted(*args):
            self.calls += 1
            return attr(*args)

        return counted


@_needs_native
@pytest.mark.parametrize("slot", ("pin_offset", "pin_distance"))
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_pin_slot_refusal_is_reached_through_the_c_symbol(
    monkeypatch: pytest.MonkeyPatch, slot: str, label: str, value: float,
) -> None:
    """The public op consults `srmech_pin_slot` BEFORE it raises.

    A Python check placed before dispatch would raise the same text with the
    C symbol never called, and then no public-op gate could see the C refuse
    or fail to refuse — the shape rc473 removed from `equation_of_centre`.
    """
    proxy = _CountingLib(_native.LIB, "srmech_pin_slot")
    monkeypatch.setattr(_native, "LIB", proxy)
    kwargs = dict(PIN_BASE)
    kwargs[slot] = value
    with pytest.raises(ValueError, match="must be finite"):
        kepler.pin_slot(**kwargs)
    assert proxy.calls == 1, (
        f"pin_slot({slot}={label}) raised after {proxy.calls} call(s) to "
        "srmech_pin_slot; the refusal must be reached through the symbol."
    )


@_needs_native
@pytest.mark.parametrize("e", (KEP_BASE["e"], 0.0))
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_kepler_solve_tolerance_refusal_is_reached_through_the_c_symbol(
    monkeypatch: pytest.MonkeyPatch, e: float, label: str, value: float,
) -> None:
    """The public op consults `srmech_kepler_solve` BEFORE it raises —
    including at `e == 0`, where both projections take an early return."""
    proxy = _CountingLib(_native.LIB, "srmech_kepler_solve")
    monkeypatch.setattr(_native, "LIB", proxy)
    with pytest.raises(ValueError, match="tolerance must be finite"):
        kepler.kepler_solve(KEP_BASE["M_rad"], e, tolerance=value,
                            max_iter=KEP_BASE["max_iter"])
    assert proxy.calls == 1, (
        f"kepler_solve(e={e!r}, tolerance={label}) raised after "
        f"{proxy.calls} call(s) to srmech_kepler_solve."
    )


# ── the max_iter WIRE: the one refusal the C projection cannot express ──

#: Iteration counts `ctypes.c_uint32` cannot carry. Measured at `1ab8d405b`
#: on an authenticated native cell, `2**32 + 1` crossed the wire as 1 and the
#: native cell raised "did not converge in 4294967297 iterations" where the
#: pure cell served.
_MAX_ITER_OFF_THE_WIRE: "tuple[int, ...]" = (
    2 ** 32, 2 ** 32 + 1, 2 ** 32 + 20, 2 ** 64 + 20,
)


def test_the_uint32_wire_wraps_which_is_why_the_refusal_precedes_dispatch() -> None:
    """The ctypes fact the precondition exists for, asserted rather than cited."""
    assert ctypes.c_uint32(2 ** 32).value == 0
    assert ctypes.c_uint32(2 ** 32 + 1).value == 1
    assert ctypes.c_uint32(2 ** 32 + 20).value == 20


@pytest.mark.parametrize("e", (KEP_BASE["e"], 0.0))
@pytest.mark.parametrize("max_iter", _MAX_ITER_OFF_THE_WIRE)
def test_kepler_solve_refuses_a_max_iter_the_wire_cannot_carry(
    max_iter: int, e: float,
) -> None:
    """Both cells refuse, with one text, before either projection runs."""
    with pytest.raises(ValueError) as excinfo:
        kepler.kepler_solve(KEP_BASE["M_rad"], e,
                            tolerance=KEP_BASE["tolerance"], max_iter=max_iter)
    assert "max_iter must be at most 2**32 - 1" in str(excinfo.value), (
        f"kepler_solve(max_iter={max_iter}) raised {excinfo.value!r}"
    )


def test_the_largest_max_iter_the_wire_carries_is_still_served() -> None:
    """Control: the bound is 2**32 - 1 inclusive, not an over-refusal."""
    value = kepler.kepler_solve(KEP_BASE["M_rad"], KEP_BASE["e"],
                                tolerance=KEP_BASE["tolerance"],
                                max_iter=2 ** 32 - 1)
    assert isinstance(value, float) and value == value


# ── FILED, not repaired: the finite-tolerance convergence seam ──

def _force_pure(fn):
    """Run `fn` with native dispatch masked — the complete pure path."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _verdict(m_rad: float, e: float, tol: float) -> str:
    """`"serve"` or `"refuse"` for `kepler_solve(m_rad, e, tol, max_iter=30)`."""
    try:
        kepler.kepler_solve(m_rad, e, tolerance=tol, max_iter=30)
    except RuntimeError:
        return "refuse"
    return "serve"


#: `(M, e, tolerance)` rows where the two cells returned DIFFERENT verdicts on
#: an authenticated native cell against a genuinely pure one, `max_iter=30`.
#: The first and third: native serves, pure never converges. The second:
#: native never converges, pure serves.
_SEAM_ROWS: "tuple[tuple[float, float, float], ...]" = (
    (1.0, 0.0549, 1e-60),
    (1.5707963267948966, 0.5, 1e-16),
    (0.1, 0.5, 1e-18),
)


@_needs_native
@pytest.mark.xfail(
    strict=True,
    reason=(
        "`#T1188`, ADR-0009 §1.2 'kepler_solve at a FINITE tolerance' row, "
        "Still open: the float Newton step can reach an exact 0.0 or stall "
        "one ULP away, and the exact-Q step does neither, so the two "
        "projections halt on different arguments. Closing it is a shared "
        "convergence criterion, not a guard. XPASS here means it closed."
    ),
)
@pytest.mark.parametrize("m_rad,e,tol", _SEAM_ROWS)
def test_kepler_solve_convergence_verdict_agrees_at_a_finite_tolerance(
    m_rad: float, e: float, tol: float,
) -> None:
    native = _verdict(m_rad, e, tol)
    pure = _force_pure(lambda: _verdict(m_rad, e, tol))
    assert native == pure, (
        f"kepler_solve({m_rad!r}, {e!r}, tolerance={tol!r}, max_iter=30): "
        f"native {native}, pure {pure}"
    )


@_needs_native
@pytest.mark.parametrize("m_rad,e", ((1.0, 0.0549), (1.5707963267948966, 0.5),
                                     (0.1, 0.5)))
def test_kepler_solve_convergence_verdict_agrees_at_the_default_tolerance(
    m_rad: float, e: float,
) -> None:
    """CONTROL for the xfail above: the same `(M, e)` at `tolerance=1e-12`
    agree, so the comparison can return 'agree'."""
    native = _verdict(m_rad, e, 1e-12)
    pure = _force_pure(lambda: _verdict(m_rad, e, 1e-12))
    assert native == pure == "serve", (m_rad, e, native, pure)
