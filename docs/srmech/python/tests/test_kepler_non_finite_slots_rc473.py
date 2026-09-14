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
        native serves, pure never converges — the convergence seam, which
        is not a slot, and which repair round 1 closed (below)

The +inf tolerance row is the sharpest: `|delta| < +inf` was true on the first
Newton step, so C returned the ONE-STEP estimate (the same value the
`max_iter=1` row prints) and reported convergence. NaN and -inf tolerances
were the same defect wearing a different answer — C ran the loop out and the
native cell said "did not converge" about an argument that was never a
tolerance. After the twin-defect pass: 107 rows per cell, 11 differ, 3
serve-vs-refuse — the three tiny tolerances and nothing else.

⚠️ SEVEN WAS A COUNT OF THAT SWEEP, NOT OF THE DIVERGENCES. Every pin_slot row
in the sweep varied one slot off `theta = 0.0`, where the Q61 `sin(theta)` is
exactly 0, so `pin_offset * sin(theta)` is `Inf * 0.0` = NaN and srmech_atan2
refused it with or without a guard. A merge gate removed only the pin_offset
half of the guard and every row here stayed green. Measured in repair round 1
at `1ab8d405b` (WSL2 gcc 13.3.0 Release + SRMECH_PEDANTIC=ON, library
`3cc94398fd33701a`, authenticated), `srmech_pin_slot(theta, ±inf, 1.0)` over
theta in {0, 1e-300, 0.3, 1, pi/2, 3, pi, -2, 100, 2**54} returned SRMECH_OK
at 8 of the 10 angles — `(0.3, +inf, 1.0)` -> `(SRMECH_OK,
0.7853981633974483)`, the public op serving the same value — while the pure
projection raised `TypeError: unsupported operand type(s) for *: 'float' and
'Q'`; only `theta = 0.0` and `1e-300`, whose Q61 sine is 0, refused. The pin
rows below therefore drive `PIN_THETAS`, not only `theta = 0.0`.

REPAIR ROUND 1 — THE SEAM AND THE TEXT, CLOSED
==============================================
Both projections now run ONE iteration for `kepler_solve`: E carried on the
Q61 quarter-turn carrier as M's reduction plus a Q61 correction `eps`, sin and
cos from the Q61 Taylor cores, the Newton step one integer division with `eps`
bracketed by `round(e * 2**61)` Q61 units (at most `2**-62` rad above `e`),
convergence decided exactly as `|step| * 2**-61 < tolerance`, and the answer —
and `best_E` in the non-convergence message — the correctly rounded double of
the iterate (`srmech_trig_kepler_q61` in `c/src/srmech_trig.c`;
`kepler._kepler_q61`). It is Newton-Raphson at a declared `2**-61` rad
precision, not an exact root of Kepler's equation.
Measured on the WSL2 gcc cell against a pure sibling after the repair: the
slot sweep 107 SAME / 0 / 0, the tolerance frontier 306 SAME / 0 / 0, and the
C symbol against `kepler._kepler_q61` over a seeded 200000-row fuzz (184218
rows compared, 15782 refused by both at the reduction) with 0 status and 0
bit mismatches. The rows below pin that, and pin that the comparison can
still say "differ".

WHERE EACH REFUSAL LIVES
========================
No callee refuses every non-finite `pin_offset` / `pin_distance`, and none
refuses a non-finite `tolerance`: the geometry enters at the bare double
arithmetic `x = pin_distance + pin_offset * cs`, whose one callee
`srmech_atan2` refuses a NaN but serves an infinite argument (measured at the
symbol: `srmech_atan2(inf, inf)` -> `(0, 0.7853981633974483)`), and
`tolerance` was only ever the right-hand side of `adelta < tolerance` until
repair round 1, which hands it to the Q61 iteration only after the finite
check — where `tolerance == tolerance` is a Debug-build `assert`, not a
refusal. (Until rc473's truth round this paragraph said no callee "checks"
these arguments; that assert is a check.) So the refusal belongs to `srmech_pin_slot` and
`srmech_kepler_solve`, beside their existing (0, 0) refusal and eccentricity
band. The Python checks that supply the one text both cells raise sit AFTER
the native call — the placement rc473 gave `equation_of_centre` — so a native
cell reaches the refusal through the C symbol, and the rows below assert that
the symbol was consulted as well as that it refuses.

`max_iter` is the exception, and the reason is the wire: `srmech_kepler_solve`
takes a `uint32_t`, `ctypes.c_uint32` wraps a wider value silently, and no C
code can refuse a value its parameter type cannot hold. That precondition is
therefore checked before dispatch, in both cells, with one text.

WHAT THE FINITE-TOLERANCE GUARD DELIBERATELY DID NOT MOVE
=========================================================
The VERDICT of a finite tolerance at the base row (`M = pi/2`, `e = 0.0549`,
`max_iter = 20`): `1e-12`, `1e300` and `2**55` converge — a huge one on the
first step — and `0.0`, `-0.0`, `-1.0` and `-2**55` never do.
`_FINITE_TOLERANCES` records those verdicts as measured before the guard, and
`test_a_finite_tolerance_is_unchanged` pins them; without it this file would
be equally consistent with a guard that refuses far more than it was written
to refuse. Repair round 1 then moved finite-tolerance VALUES
(`kepler_solve(pi/2, 0.9)` is `2.263415106356943`; the pre-repair loop gave
`2.2634151063569425`) and, wherever the two old loops disagreed on a verdict,
the verdict of at least one of them. The rows above pin the one answer now.

numpy-free.
"""
from __future__ import annotations

import ctypes
import math
import random
import struct
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

#: Every pin row runs at each of these angles (repair round 1, `#T1188`).
#: `theta = 0.0` alone could not see the pin_offset half of the guard: the
#: Q61 `sin(0.0)` is 0, so `Inf * 0.0` is NaN and srmech_atan2 refused it
#: anyway, while at 0.3, 1.0 and -2.0 the unguarded library SERVED it.
PIN_THETAS: "tuple[float, ...]" = (0.0, 0.3, 1.0, -2.0)
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
@pytest.mark.parametrize("theta", PIN_THETAS)
@pytest.mark.parametrize("slot", ("pin_offset", "pin_distance"))
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_c_pin_slot_refuses_non_finite_geometry(
    slot: str, label: str, value: float, theta: float,
) -> None:
    """`srmech_pin_slot` returns SRMECH_ERR_BAD_INPUT, at the symbol."""
    kwargs = dict(PIN_BASE, theta=theta)
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

@pytest.mark.parametrize("theta", PIN_THETAS)
@pytest.mark.parametrize("slot", ("pin_offset", "pin_distance"))
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_pin_slot_refuses_non_finite_geometry(
    slot: str, label: str, value: float, theta: float,
) -> None:
    kwargs = dict(PIN_BASE, theta=theta)
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


@pytest.mark.parametrize("label,value", NON_FINITE)
def test_kepler_solve_refuses_a_non_finite_tolerance_at_e_zero(
    label: str, value: float,
) -> None:
    """The ``e == 0`` shortcut, on EVERY cell (rc473 close-out, `#T1188`).

    ``kepler_solve`` returns ``M_rad`` at ``e == 0``, and its tolerance check
    must come first, as ``srmech_kepler_solve``'s does. The through-symbol row
    below pins that order on a native cell only; this row runs on a pure cell
    too, so moving the pure check after the ``e == 0.0`` return reddens a pure
    CI shard as well.
    """
    with pytest.raises(ValueError) as excinfo:
        kepler.kepler_solve(KEP_BASE["M_rad"], 0.0, tolerance=value,
                            max_iter=KEP_BASE["max_iter"])
    assert "tolerance must be finite" in str(excinfo.value), (
        f"kepler_solve(e=0.0, tolerance={label}) raised {excinfo.value!r}"
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
    """At the base row, finite tolerances of every sign and magnitude keep the
    verdict recorded before the finite-tolerance guard.

    Both outcomes are the pre-guard verdicts at this row and both were what
    the two projections already agreed on there, so a guard that swallowed
    either would be over-refusing — which is the failure mode a repair to a
    refusal contract is most exposed to.
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
@pytest.mark.parametrize("theta", PIN_THETAS)
@pytest.mark.parametrize("slot", ("pin_offset", "pin_distance"))
@pytest.mark.parametrize("label,value", NON_FINITE)
def test_pin_slot_refusal_is_reached_through_the_c_symbol(
    monkeypatch: pytest.MonkeyPatch, slot: str, label: str, value: float,
    theta: float,
) -> None:
    """The public op consults `srmech_pin_slot` BEFORE it raises.

    A Python check placed before dispatch would raise the same text with the
    C symbol never called, and then no public-op gate could see the C refuse
    or fail to refuse — the shape rc473 removed from `equation_of_centre`.
    """
    proxy = _CountingLib(_native.LIB, "srmech_pin_slot")
    monkeypatch.setattr(_native, "LIB", proxy)
    kwargs = dict(PIN_BASE, theta=theta)
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


# ── REPAIR ROUND 1: one iteration, one answer, one text ──
#
# Through the twin-defect pass this section was a native-gated STRICT XFAIL
# over three seam rows, and `kepler_solve`'s non-convergence text was a second
# filed divergence. Both are closed by the Q61 iteration the module docstring
# describes, so the rows below are equalities, a pure-cell golden table, and a
# non-vacuity row proving the comparator still reports a difference.

PI_2 = 1.5707963267948966


def _force_pure(fn):
    """Run `fn` with native dispatch masked — the complete pure path."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _outcome(call) -> str:
    """THE comparator every row below uses: ``"serve <repr>"`` or
    ``"refuse <Type>: <text>"``. It compares ``repr``, not ``==``, so a
    sign-of-zero or one-ULP difference is a difference."""
    try:
        return "serve %r" % (call(),)
    except Exception as exc:  # noqa: BLE001 — the refusal TEXT is the payload
        return "refuse %s: %s" % (type(exc).__name__, exc)


def _bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


#: The tolerance frontier the twin-defect pass filed: 134 of these 306 rows
#: returned a different VERDICT in the two cells at `2eb05877f`.
_FRONTIER_MS = (PI_2, 1.0, 3.0, 0.1, 100.0, 1e6)
_FRONTIER_ES = (0.0549, 0.5, 0.9)
_FRONTIER_TOLS = (1e-12, 1e-14, 1e-15, 1e-16, 1e-17, 1e-18, 1e-20, 1e-25,
                  1e-30, 1e-40, 1e-60, 1e-100, 1e-200, 1e-300,
                  2.2250738585072014e-308, 1e-310, 5e-324)

#: The slot sweep's kepler rows whose TEXT differed (the eight SAME-VERDICT
#: rows) or whose verdict did (the three tiny positive tolerances).
_TEXT_AND_TINY_ROWS: "tuple[dict, ...]" = tuple(
    {"tolerance": t, "max_iter": 20}
    for t in (0.0, -0.0, -1.0, -2.0 ** 55, -5e-324, -1e-310,
              5e-324, 1e-310, 2.2250738585072014e-308)
) + ({"tolerance": 1e-12, "max_iter": 1}, {"tolerance": 1e-12, "max_iter": 2})


@_needs_native
def test_kepler_solve_is_one_answer_in_both_projections() -> None:
    """Native and pure return the SAME outcome — verdict, value bits via
    ``repr``, and refusal text — over the whole frontier, the slot sweep's
    kepler rows and ADR-0009 row 52's ``M = 2**53, e = 0.999``."""
    rows = [(m, e, {"tolerance": t, "max_iter": 30})
            for m in _FRONTIER_MS for e in _FRONTIER_ES for t in _FRONTIER_TOLS]
    rows += [(PI_2, 0.0549, kw) for kw in _TEXT_AND_TINY_ROWS]
    rows.append((2.0 ** 53, 0.999, {}))
    differ = []
    for m_rad, e, kw in rows:
        native = _outcome(lambda: kepler.kepler_solve(m_rad, e, **kw))
        pure = _force_pure(
            lambda: _outcome(lambda: kepler.kepler_solve(m_rad, e, **kw)))
        if native != pure:
            differ.append((m_rad, e, kw, native[:120], pure[:120]))
    assert len(rows) == 318
    assert not differ, (
        f"{len(differ)} of {len(rows)} rows differ between the cells; the "
        f"first: {differ[:3]}"
    )


@_needs_native
def test_kepler_solve_non_convergence_is_one_text() -> None:
    """The text half on its own: ``best_E`` renders as the float last mile in
    BOTH cells. At `2eb05877f` the pure cell rendered the exact Q, whose
    digits began ``33350282498237497256435084978559495037``."""
    for kw in _TEXT_AND_TINY_ROWS[:6] + _TEXT_AND_TINY_ROWS[-2:]:
        native = _outcome(lambda: kepler.kepler_solve(PI_2, 0.0549, **kw))
        pure = _force_pure(
            lambda: _outcome(lambda: kepler.kepler_solve(PI_2, 0.0549, **kw)))
        assert native.startswith("refuse RuntimeError: kepler_solve: did not "
                                 "converge"), (kw, native)
        assert native == pure, (kw, native, pure)
        best = native.rsplit("best_E=", 1)[1].rstrip(")")
        assert repr(float(best)) == best, (
            f"best_E={best!r} is not a float's repr; it must be the last mile"
        )


def _double(bits: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


def _fuzz_rows(n: int, seed: int):
    """Seeded arguments over the whole door: M uniform, log-uniform up to and
    past 2**55, subnormal and random bit patterns; e uniform, near 1, tiny and
    subnormal; tolerances of every sign and magnitude; max_iter 1..40.

    Every value is built from integers and exactly-rounded IEEE operations —
    ``uniform``, ``ldexp`` inside the normal range, ``nextafter``, subtraction
    and raw bit patterns — and never from ``**`` on a float, because libm
    ``pow`` is not correctly rounded. MEASURED in repair round 1: the first
    version used ``10 ** x``, and 2 of the 906 stream rows got a one-ULP
    different ``M`` on Windows CPython 3.14.4 than on Linux CPython 3.12.3, so
    the digest pin below differed by platform while both projections agreed
    on every row with the same inputs.
    """
    rng = random.Random(seed)
    ldexp = math.ldexp
    for _ in range(n):
        k = rng.randrange(5)
        if k == 0:
            m_rad = rng.uniform(-math.pi, math.pi)
        elif k == 1:
            m_rad = rng.choice((1, -1)) * ldexp(1.0 + rng.random(), rng.randint(-1021, 55))
        elif k == 2:
            m_rad = rng.uniform(-1e7, 1e7)
        elif k == 3:
            m_rad = rng.choice((1, -1)) * _double(rng.getrandbits(52))   # subnormal
        else:
            m_rad = _double(rng.getrandbits(64))
        e = rng.choice((rng.uniform(0.0, 1.0),
                        1.0 - ldexp(1.0 + rng.random(), -rng.randint(2, 53)),
                        ldexp(1.0 + rng.random(), -rng.randint(2, 1021)),
                        _double(rng.getrandbits(52)),
                        math.nextafter(1.0, 0.0)))
        tol = rng.choice((ldexp(1.0 + rng.random(), rng.randint(-100, 1)),
                          ldexp(1.0 + rng.random(), rng.randint(-1021, -100)),
                          _double(rng.getrandbits(52)),
                          0.0, -1.0, 4.0, math.nextafter(4.0, 0.0),
                          ldexp(1.0, -61), ldexp(3.0, -61)))
        if 0.0 < e < 1.0:
            yield m_rad, e, tol, rng.choice((1, 2, 3, 5, 8, 13, 20, 30, 40))


@_needs_native
def test_the_c_symbol_is_the_q61_iteration_bit_for_bit() -> None:
    """The bare-C host's view: ``srmech_kepler_solve`` at the SYMBOL against
    ``kepler._kepler_q61``, status against converged and the WRITTEN double's
    bit pattern — including the best-effort E on non-convergence."""
    from srmech.math import rational

    compared = served = unconverged = refused = 0
    for m_rad, e, tol, max_iter in _fuzz_rows(1500, 1188):
        st, out = _c_kepler_solve(m_rad, e, tol, max_iter)
        if not rational._q61_reduce(m_rad)[0]:
            assert st == _native.SRMECH_ERR_BAD_INPUT, (m_rad, e, tol, max_iter, st)
            refused += 1
            continue
        converged, want = kepler._kepler_q61(m_rad, e, tol, max_iter)
        assert st == (_native.SRMECH_OK if converged
                      else _native.SRMECH_ERR_OVERFLOW), (
            m_rad, e, tol, max_iter, st, converged)
        assert _bits(out) == _bits(want), (
            f"kepler_solve({m_rad!r}, {e!r}, {tol!r}, {max_iter}): C wrote "
            f"{out!r}, the pure iteration {want!r}"
        )
        compared += 1
        served += converged
        unconverged += not converged
    assert compared >= 1000 and served >= 100 and unconverged >= 100 and refused >= 10, (
        compared, served, unconverged, refused)


#: Printed by both cells after repair round 1 (WSL2 gcc 13.3.0 Release +
#: SRMECH_PEDANTIC=ON, authenticated, against a pure sibling with 0 library
#: files; CPython 3.12.3, numpy absent), identical in both. Runs on a pure
#: cell too, where it is the only kepler row that can see a pure-side move.
_GOLDEN: "tuple[tuple[tuple, dict, str], ...]" = (
    ((PI_2, 0.0549), {}, "serve 1.625613861239322"),
    ((PI_2, 0.9), {}, "serve 2.263415106356943"),
    ((2.0 ** 53, 0.999), {}, "serve 9007199254740992.0"),
    ((1.0, 0.0549), {"tolerance": 1e-60, "max_iter": 30},
     "serve 1.0475545924186345"),
    ((PI_2, 0.5), {"tolerance": 1e-16, "max_iter": 30},
     "serve 2.02097993808977"),
    ((0.1, 0.5), {"tolerance": 1e-18, "max_iter": 30},
     "serve 0.19869517172589946"),
    ((PI_2, 0.0549), {"tolerance": 5e-324, "max_iter": 20},
     "serve 1.625613861239322"),
    ((-0.0, 0.3), {}, "serve 0.0"),
    ((PI_2, 0.0549), {"tolerance": 0.0, "max_iter": 20},
     "refuse RuntimeError: kepler_solve: did not converge in 20 iterations "
     "(M=1.5707963267948966, e=0.0549, best_E=1.625613861239322)"),
    ((PI_2, 0.0549), {"max_iter": 1},
     "refuse RuntimeError: kepler_solve: did not converge in 1 iterations "
     "(M=1.5707963267948966, e=0.0549, best_E=1.625613861425157)"),
    ((0.1, 0.99), {"tolerance": 1e-15, "max_iter": 2},
     "refuse RuntimeError: kepler_solve: did not converge in 2 iterations "
     "(M=0.1, e=0.99, best_E=0.8829696002059165)"),
)


@pytest.mark.parametrize("args,kwargs,want", _GOLDEN)
def test_kepler_solve_golden_outcomes(args: tuple, kwargs: dict, want: str) -> None:
    got = _outcome(lambda: kepler.kepler_solve(*args, **kwargs))
    assert got == want, f"kepler_solve{args} {kwargs}: {got!r}, measured {want!r}"


def _outcome_stream() -> bytes:
    """Every frontier row and a seeded fuzz, one ``_outcome`` per line."""
    rows = [(m, e, t, 30)
            for m in _FRONTIER_MS for e in _FRONTIER_ES for t in _FRONTIER_TOLS]
    rows += list(_fuzz_rows(600, 473))
    return "\n".join(
        _outcome(lambda: kepler.kepler_solve(m_rad, e, tolerance=tol,
                                             max_iter=max_iter))
        for m_rad, e, tol, max_iter in rows
    ).encode("utf-8")


#: sha256 of ``_outcome_stream()`` (906 lines). The eleven goldens above did
#: NOT catch a pure-side rounding change on a pure cell — measured in repair
#: round 1 by planting floor rounding in ``_kq_emul``: native went red, pure
#: stayed ``62 passed, 61 skipped`` — so a pure CI shard needs a pin over many
#: rows. Printed identically, after the repair and after `_fuzz_rows` stopped
#: using float `**`, by the authenticated WSL2 gcc native cell (CPython
#: 3.12.3), its pure sibling on CPython 3.12.3 and 3.10, the authenticated
#: Windows clang-cl 22.1.0 Release and Debug cells and a Windows pure cell
#: (CPython 3.14.4).
#: (The first pin, `4977176573515e9e…`, was printed on the Linux cells only,
#: and a Windows cell printed `7f33761e5e48b9a3…` for it — see `_fuzz_rows`.)
_OUTCOME_DIGEST = "9585bbd6dacbd77a71ef89722e13c22476794572d7b7e667ef528fb4c0323cd0"


def test_kepler_solve_outcome_stream_is_pinned() -> None:
    from srmech.amsc.format import sha256_bytes

    got = sha256_bytes(_outcome_stream())
    assert got == _OUTCOME_DIGEST, (
        f"kepler_solve's outcome stream moved: sha256 {got}, pinned "
        f"{_OUTCOME_DIGEST}. Both cells printed the pinned value; a move is a "
        "change to the Q61 iteration or to a refusal text in THIS cell."
    )


def _pre_repair_outcome(m_rad: float, e: float, tol: float, max_iter: int) -> str:
    """``1ab8d405b:c/src/srmech_kepler.c``'s ``srmech_kepler_solve``, transliterated.

    Newton on ``double`` over ``srmech_sin`` / ``srmech_cos``, which write the
    double of the Q61 rational — ``float(rational.sin(x))``. Checked before it
    was trusted: equal, status and bits, to that library's C symbol on 20320
    rows (the 306-row frontier, 14 slot rows and a seeded 20000-row fuzz;
    WSL2 gcc 13.3.0 Release, library ``3cc94398fd33701a``, authenticated).
    Only finite, in-door rows are passed here.
    """
    from srmech.math import rational

    E = m_rad + e * float(rational.sin(m_rad))
    for _ in range(max_iter):
        f = E - e * float(rational.sin(E)) - m_rad
        f_prime = 1.0 - e * float(rational.cos(E))
        delta = f / f_prime
        E -= delta
        if (delta if delta >= 0.0 else -delta) < tol:      # Class-K magnitude
            return "serve %r" % (E,)
    return ("refuse RuntimeError: kepler_solve: did not converge in %d "
            "iterations (M=%s, e=%s, best_E=%s)" % (max_iter, m_rad, e, E))


def test_the_kepler_comparator_can_still_report_a_difference() -> None:
    """NON-VACUITY: the rows above assert "agree", so this one proves the same
    comparator says "differ" — for a verdict, for one ULP, and for the
    pre-repair iteration itself — and "agree" where the two iterations do.
    No library is involved beyond ``rational.sin``, so it runs on both cells."""
    old = _pre_repair_outcome(PI_2, 0.9, 1e-12, 30)
    new = _outcome(lambda: kepler.kepler_solve(PI_2, 0.9))
    assert old == "serve 2.2634151063569425", (
        f"the transliteration no longer reproduces the pre-repair figure: {old!r}")
    assert old != new, "one ULP apart and the comparator said equal"

    old_v = _pre_repair_outcome(PI_2, 0.5, 1e-16, 30)
    new_v = _outcome(lambda: kepler.kepler_solve(PI_2, 0.5, tolerance=1e-16,
                                                 max_iter=30))
    assert old_v.startswith("refuse") and new_v.startswith("serve"), (old_v, new_v)

    x = 2.263415106356943
    assert _outcome(lambda: x) != _outcome(lambda: math.nextafter(x, math.inf)), (
        "_outcome rendered two doubles one ULP apart as the same text")

    assert _pre_repair_outcome(PI_2, 0.0549, 1e-12, 30) == _outcome(
        lambda: kepler.kepler_solve(PI_2, 0.0549)), (
        "control: at the default tolerance the pre-repair and Q61 iterations "
        "agree; the comparator must still say so")
