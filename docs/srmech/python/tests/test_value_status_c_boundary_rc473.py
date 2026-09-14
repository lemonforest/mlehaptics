"""rc473 (`#T1188`) — THE C BOUNDARY, read directly. Status AND written value.

WHY THIS FILE EXISTS
--------------------
srmech's central architectural claim is that Python and C are CO-EQUAL
PROJECTIONS of the same mathematics — a bare-C host, no Python present, runs
every op. ADR-0009 §2.1 is the decision record: *"'Realizes it by calling the
other implementation' is not realizing it."* §2.4: implementations *"may not
differ in which inputs they serve."*

Measured on the rc472 tree, that claim was false and nothing in the package
could tell::

    Python : equation_of_centre(2.0**53+1, 0.0549, 4)        -> REFUSES
    C      : srmech_equation_of_centre(2.0**53+1, 0.0549, 4) -> SRMECH_OK,
                                                   -0.08984990210223018

THE INSTRUMENT WAS POINTED AT THE WRONG BOUNDARY, WHICH IS WHY IT STAYED
-----------------------------------------------------------------------
Every parity test in this tree compares *native-through-the-Python-wrapper*
against *pure-through-the-Python-wrapper*. Measured at rc472: of the **47**
test files under ``python/tests`` whose name carries ``parity``, **42 make ZERO
direct calls to a C symbol**, and of the five that do, none names a math op.
So the sentence "our two projections agree" had never been tested at the place
where they could disagree.

rc472 then added a guard INSIDE the Python wrapper — ``kepler.py``'s
pre-dispatch refusal, which raises before ``if _native.HAS_NATIVE:`` is even
consulted. That turned the parity gates green while the defect stayed exactly
where it was: the repair was applied at the one point that satisfies the
instrument without touching the thing it measures.

**The asymmetry in every row below is the whole design.** The C side is read at
the SYMBOL (``_native.LIB.srmech_*``, ctypes, no wrapper). The Python side is
read at the op a user calls. A cover inside the wrapper therefore cannot make a
row pass: it changes only the Python side, and the C side still answers.

This file generalises the one template that already existed —
``tests/test_native_explog_rc46.py:55-57``, a direct ``LIB.srmech_log(-1.0)``
asserting ``st == SRMECH_ERR_BAD_INPUT`` **and** ``math.isnan(o.value)``. That
was the only test in the tree naming a math op through ``LIB.``.

⚠️ ABSENCE IS NOT A SKIP WHEN A LIBRARY IS PRESENT
--------------------------------------------------
A gate that skips itself is an instrument that cannot return otherwise. This
file skips ONLY when no shared library file exists beside ``srmech/_native/``
at all — a genuinely pure cell (pure wheel / Pyodide). If a library FILE is
present and ``HAS_NATIVE`` is False, the library failed to load — an ABI
mismatch, a stale artifact, a missing symbol — and this file FAILS rather than
skips, because that is precisely the state in which a native gate silently
stops measuring. ``test_the_cell_is_classified`` runs in both cells and is
never skipped, so the classification itself is always on the record.
"""

from __future__ import annotations

import ctypes
import math
import re
from pathlib import Path

import pytest

from srmech import _native
from srmech.math import kepler, rational

# --------------------------------------------------------------------------
# Cell classification. Decided from the filesystem, not from a flag, so that a
# library which is present-but-unloadable cannot present as "pure".
# --------------------------------------------------------------------------
_NATIVE_PKG_DIR = Path(_native.__file__).resolve().parent
_LIB_SUFFIXES = (".so", ".dylib", ".dll", ".pyd")


def _library_files() -> list[Path]:
    if not _NATIVE_PKG_DIR.is_dir():
        return []
    return sorted(
        p for p in _NATIVE_PKG_DIR.iterdir()
        if p.is_file() and p.suffix in _LIB_SUFFIXES
    )


_LIB_FILES = _library_files()
_PURE_CELL = (not _native.HAS_NATIVE) and not _LIB_FILES

_needs_native = pytest.mark.skipif(
    _PURE_CELL,
    reason=(
        "genuinely pure cell: HAS_NATIVE is False AND no shared library file "
        f"exists in {_NATIVE_PKG_DIR}. A library that is present but does not "
        "load is a FAILURE here, not a skip — see test_the_cell_is_classified."
    ),
)

# --------------------------------------------------------------------------
# Declines rc473 does NOT repair. Named in the marker so the task id is
# greppable rather than buried in a decorator, following the shape of
# tests/test_genome_read_bound_global_rc342.py's _PENDING_T954.
#
# STRICT, and the reason strict is right here rather than inherited: the C
# behaviour being pinned is deterministic and host-independent (measured on
# this cell, srmech_exp(+inf) -> (SRMECH_OK, inf)), which is exactly the
# condition _PENDING_T954's non-strict rationale — "a host whose behaviour
# moves first does not turn CI red" — does not apply to. A strict xfail deletes
# itself when satisfied instead of passing forever.
# --------------------------------------------------------------------------
_DECLINED_T1188 = pytest.mark.xfail(
    strict=True,
    reason=(
        "`#T1188`: C serves an argument to exp / log / rational_sqrt that the "
        "pure projection refuses — an ADR-0009 §2.4 'differ in which inputs "
        "they serve' instance rc473 does NOT repair. NOT confined to the "
        "non-finite: srmech_exp(-1e300) -> (SRMECH_OK, 0.0) is a FINITE "
        "witness, and it is a row below. Measured hazard: lap_sqrt(1.0 + "
        "tau*tau) in srmech_laplacian.c and sq_sqrt in srmech_svd_qr.c both "
        "reach +Inf on the tau-overflow path and rely on sqrt(+Inf) = +Inf to "
        "get t = 1/(tau + Inf) = 0, inside static helpers with no status "
        "channel. Disclosure is necessary and is not sufficient (ADR-0009 §5) "
        "— the tracked filing is ADR-0009 §1.2, this rc's exp / log / "
        "rational_sqrt row, which the rc473 repair pass re-titled from "
        "'at ±Inf' to the domain it actually covers."
    ),
)

# --------------------------------------------------------------------------
# NOT EXERCISED, and disclosed by name rather than dropped.
#
# rational.exp at |x| ~ 2**55 does not refuse and does not return: exp(x) is
# built as 2**n * exp(r), so n ~ 5.2e16 and the exact integer has ~5e16 bits.
# Measured under `ulimit -v 4000000` it raises MemoryError; unbounded it is a
# machine-filling allocation. A gate must not execute it. That pure-side crash
# (where C answers (SRMECH_OK, +Inf)) is a real defect and a different one from
# the discarded statuses this file measures.
# --------------------------------------------------------------------------
_NOT_EXERCISED_PURE = {
    ("exp", 2.0 ** 55),
    ("exp", math.nextafter(2.0 ** 55, 0.0)),
}

NAN = float("nan")
INF = float("inf")

_D = ctypes.c_double
_DP = ctypes.POINTER(ctypes.c_double)
_U32 = ctypes.c_uint32
_SIZE = ctypes.c_size_t


def _bind(name: str, argtypes: list) -> object:
    fn = getattr(_native.LIB, name)
    fn.argtypes = argtypes
    fn.restype = ctypes.c_int
    return fn


def _c_unary(name: str, x: float) -> tuple[int, float]:
    """Call a one-argument C symbol DIRECTLY. No wrapper on this path."""
    fn = _bind(name, [_D, _DP])
    out = ctypes.c_double(-12345.0)
    status = fn(_D(x), ctypes.byref(out))
    return status, out.value


def _c_atan2(y: float, x: float) -> tuple[int, float]:
    fn = _bind("srmech_atan2", [_D, _D, _DP])
    out = ctypes.c_double(-12345.0)
    status = fn(_D(y), _D(x), ctypes.byref(out))
    return status, out.value


def _pure_raises(fn, *args) -> tuple[bool, object]:
    """Did the pure projection refuse? Returns (refused, value-or-exception)."""
    try:
        value = fn(*args)
    except Exception as exc:  # noqa: BLE001 - classifying, not handling
        return True, exc
    return False, value


# --------------------------------------------------------------------------
# THE ROW TABLE. One row per (C symbol, argument) the two projections must
# agree about. `want` is the POST-rc473 contract:
#
#   "refuse" — the C projection must return non-SRMECH_OK and write NaN.
#   "serve"  — the C projection must return SRMECH_OK, and the value must
#              agree with the pure projection's.
#
# Every "refuse" row was measured returning SRMECH_OK on the rc472 tree unless
# its comment says otherwise; the rows that already refuse are kept as controls
# so a repair that widened a refusal past its domain would be caught.
# --------------------------------------------------------------------------
_UNARY_ROWS: list[tuple[str, str, float, str]] = [
    # (c symbol, pure attribute on rational, argument, want)
    ("srmech_sin", "sin", NAN, "refuse"),
    ("srmech_cos", "cos", NAN, "refuse"),
    ("srmech_atan", "atan", NAN, "refuse"),
    ("srmech_exp", "exp", NAN, "refuse"),
    ("srmech_log", "log", NAN, "refuse"),
    ("srmech_rational_sqrt", "sqrt", NAN, "refuse"),
    # rc472 already refuses these — controls, in the refusing direction.
    ("srmech_sin", "sin", INF, "refuse"),
    ("srmech_sin", "sin", -INF, "refuse"),
    ("srmech_cos", "cos", INF, "refuse"),
    ("srmech_cos", "cos", -INF, "refuse"),
    ("srmech_sin", "sin", 2.0 ** 55, "refuse"),
    ("srmech_cos", "cos", 2.0 ** 55, "refuse"),
    ("srmech_log", "log", -1.0, "refuse"),
    ("srmech_log", "log", -INF, "refuse"),
    ("srmech_rational_sqrt", "sqrt", -4.0, "refuse"),
    ("srmech_rational_sqrt", "sqrt", -INF, "refuse"),
    # Served, and the values must agree.
    ("srmech_sin", "sin", math.nextafter(2.0 ** 55, 0.0), "serve"),
    ("srmech_cos", "cos", math.nextafter(2.0 ** 55, 0.0), "serve"),
    ("srmech_sin", "sin", 0.5, "serve"),
    ("srmech_cos", "cos", 0.5, "serve"),
    ("srmech_atan", "atan", 1.0, "serve"),
    ("srmech_exp", "exp", 1.0, "serve"),
    ("srmech_log", "log", 2.0, "serve"),
    ("srmech_rational_sqrt", "sqrt", 4.0, "serve"),
    # atan is TOTAL on the extended reals and the pure projection AGREES.
    # Written from the measurement, not assumed: rc472 srmech_atan(+inf) ->
    # (SRMECH_OK, 1.5707963267948966) and rational.atan(+inf) ->
    # Q(3622009729038561421, 2305843009213693952), the same pi/2. These are
    # "serve" rows for that reason and for no other.
    ("srmech_atan", "atan", INF, "serve"),
    ("srmech_atan", "atan", -INF, "serve"),
]

# D8: C serves where pure refuses. Deferred, pinned, strict-xfailed.
_DECLINED_ROWS: list[tuple[str, str, float]] = [
    ("srmech_exp", "exp", INF),
    ("srmech_exp", "exp", -INF),
    ("srmech_log", "log", INF),
    ("srmech_rational_sqrt", "sqrt", INF),
    # rc473 repair pass (`#T1188`) — the FINITE witness. The four rows above
    # are all non-finite, which let the ADR row's own title read "at ±Inf" and
    # let a reader conclude the residual divergence is confined to the
    # non-finite. It is not. MEASURED on this cell (native, ABI 26 == 26,
    # CPython 3.12.3, numpy absent): srmech_exp(-1e300) -> (SRMECH_OK, 0.0),
    # srmech_exp_q61(-1e300) -> status 2 (its own 1e18 bound), and
    # rational.exp(-1e300) raises. Safe to EXECUTE, unlike the +2**55
    # direction in _NOT_EXERCISED_PURE below: exp of a large NEGATIVE argument
    # underflows to 0.0 rather than allocating ~5e16 bits.
    ("srmech_exp", "exp", -1e300),
]

_ATAN2_ROWS: list[tuple[float, float, str]] = [
    (NAN, 1.0, "refuse"),
    (1.0, NAN, "refuse"),
    (INF, 1.0, "serve"),
    (-INF, 1.0, "serve"),
    (1.0, INF, "serve"),
    (1.0, -INF, "serve"),
    (1.0, 1.0, "serve"),
    # inf/inf is NaN inside srmech_atan2, so the poison value comes back with
    # SRMECH_OK without any NaN ever being passed in. Pure answers pi/4.
    (INF, INF, "serve"),
    (-INF, -INF, "serve"),
]


def _row_id(symbol: str, arg: float) -> str:
    return f"{symbol}({arg!r})"


# --------------------------------------------------------------------------
# The cell classification. NEVER skipped.
# --------------------------------------------------------------------------
def test_the_cell_is_classified() -> None:
    """A present-but-unloadable library must FAIL here, never skip."""
    if _native.HAS_NATIVE:
        assert _native.LIB is not None
        return
    if _LIB_FILES:
        pytest.fail(
            "srmech._native.HAS_NATIVE is False, but "
            f"{len(_LIB_FILES)} shared library file(s) are present in "
            f"{_NATIVE_PKG_DIR}: {[p.name for p in _LIB_FILES]}. "
            "A library that is on disk and does not load is the state in "
            "which every native gate in this tree silently degrades to a "
            "skip and stops measuring. Expected ABI is "
            f"{_native.EXPECTED_ABI_VERSION}. Rebuild and reinstall it "
            "(cmake --build build -- -k && cp build/libsrmech.so "
            "python/srmech/_native/); never set SRMECH_ALLOW_STALE_NATIVE "
            "and never touch mtimes."
        )
    # Genuinely pure: nothing on disk to load. That is a legitimate cell.


# --------------------------------------------------------------------------
# Non-vacuity controls. Both sides of every claim must be able to move.
# --------------------------------------------------------------------------
@_needs_native
def test_the_row_table_is_not_vacuous() -> None:
    assert len(_UNARY_ROWS) >= 20, f"only {len(_UNARY_ROWS)} unary rows"
    assert len(_ATAN2_ROWS) >= 6, f"only {len(_ATAN2_ROWS)} atan2 rows"
    wants = {want for _, _, _, want in _UNARY_ROWS}
    assert wants == {"refuse", "serve"}, (
        f"the table must exercise BOTH directions; it carries {sorted(wants)}. "
        "A table of refusals alone would be satisfied by a library that "
        "refused everything."
    )
    assert len(_DECLINED_ROWS) >= 1


@_needs_native
def test_the_direct_call_path_reaches_the_library_not_a_wrapper() -> None:
    """Control: the ctypes handle is the loaded shared object, not Python.

    If this ever reads a Python object, every row in the file is measuring the
    wrapper — which is the exact failure this file was written to remove.
    """
    lib_name = str(_native.LIB._name)
    assert lib_name, "srmech._native.LIB carries no library path"
    assert Path(lib_name).suffix in _LIB_SUFFIXES, (
        f"_native.LIB._name is {lib_name!r}, which is not a shared library"
    )
    status, value = _c_unary("srmech_log", 1.0)
    assert status == _native.SRMECH_OK
    assert value == 0.0, f"srmech_log(1.0) through the symbol gave {value!r}"


# --------------------------------------------------------------------------
# rc473 stage C — THE PYTHON OP MUST CONSULT THE C SYMBOL BEFORE REFUSING.
#
# The rows above read the two projections separately. This one reads the SEAM:
# it plants a recording kernel binding and requires the array op to have called
# it. rc466 and rc472 each repaired this defect class by raising in the Python
# wrapper BEFORE dispatch, which turned every parity gate green while the C
# kernel went on returning 0.0 for a refused element. A pre-dispatch cover is
# therefore not a stylistic matter here: it is the mechanism by which this
# tree's instruments stopped measuring. Runs in BOTH cells — the plant replaces
# srmech.math.laplacian._native wholesale, so no library is required.
# --------------------------------------------------------------------------
def test_the_array_op_consults_the_kernel_before_it_refuses(monkeypatch) -> None:
    from srmech.math import laplacian as _lap

    calls: list[tuple] = []

    class _Lib:
        @staticmethod
        def srmech_elementwise_transcendental(*a):
            calls.append(a)
            return 2                          # SRMECH_ERR_BAD_INPUT

    class _Nat:
        HAS_NATIVE = True
        LIB = _Lib()
        SRMECH_OK = 0
        SRMECH_ERR_BAD_INPUT = 2
        SRMECH_TRANS_EXP = 0
        SRMECH_TRANS_COS = 1
        SRMECH_TRANS_SIN = 2
        SRMECH_TRANS_LOG = 3

    monkeypatch.setattr(_lap, "_native", _Nat)

    for arg, op, pattern in [
        (2.0 ** 55, "cos", "too large for the Q61 octant reduction"),
        (2.0 ** 55, "sin", "too large for the Q61 octant reduction"),
        (NAN, "cos", "must be finite"),
        (NAN, "exp", "must be finite"),
    ]:
        before = len(calls)
        with pytest.raises(ValueError, match=pattern):
            _lap.elementwise_transcendental([arg], op)
        assert len(calls) > before, (
            f"elementwise_transcendental([{arg!r}], {op!r}) refused WITHOUT "
            "calling srmech_elementwise_transcendental. A pre-dispatch cover "
            "is back; the kernel is then free to write a wrong value with "
            "SRMECH_OK and nothing in this tree measures it."
        )

    # exp_i dispatches twice (cos, then sin) and must reach the kernel too
    before = len(calls)
    with pytest.raises(ValueError, match="too large for the Q61 octant reduction"):
        _lap.elementwise_transcendental([2.0 ** 55], "exp_i")
    assert len(calls) > before, "exp_i refused without consulting the kernel"


def test_the_consult_probe_can_fail(monkeypatch) -> None:
    """Non-vacuity: the probe above must report a cover when one is present.

    A cover is simulated by a plant whose op raises before dispatch. If this
    test cannot make the recorder stay empty, the recorder is not measuring.
    """
    from srmech.math import laplacian as _lap

    calls: list[tuple] = []

    class _Lib:
        @staticmethod
        def srmech_elementwise_transcendental(*a):
            calls.append(a)
            return 0

    class _Nat:
        HAS_NATIVE = True
        LIB = _Lib()
        SRMECH_OK = 0
        SRMECH_ERR_BAD_INPUT = 2

    monkeypatch.setattr(_lap, "_native", _Nat)

    def _covered(values, op_name):
        for x in values:
            m = x if x >= 0.0 else -x         # Class-K pin-slot branch
            if m >= rational.Q61_TRIG_RANGE:
                raise ValueError(
                    f"{op_name}: |x| too large for the Q61 octant reduction")
        return _lap.elementwise_transcendental(values, op_name)

    with pytest.raises(ValueError):
        _covered([2.0 ** 55], "cos")
    assert calls == [], (
        "the recorder logged a call from a body that raises before dispatch — "
        "it is not recording what it claims to record")


# --------------------------------------------------------------------------
# THE BOTH-DIRECTIONS CLAUSE. C refuses <=> the pure projection raises.
# --------------------------------------------------------------------------
@_needs_native
@pytest.mark.parametrize(
    ("symbol", "pure_name", "arg", "want"),
    _UNARY_ROWS,
    ids=[f"{s}-{a!r}-{w}" for s, _, a, w in _UNARY_ROWS],
)
def test_c_and_pure_agree_on_what_they_refuse(
    symbol: str, pure_name: str, arg: float, want: str
) -> None:
    status, value = _c_unary(symbol, arg)
    c_refused = status != _native.SRMECH_OK

    if (pure_name, arg) in _NOT_EXERCISED_PURE:
        pytest.fail(
            f"{pure_name}({arg!r}) is on the not-exercised list and must not "
            "appear in the row table"
        )
    pure_refused, pure_result = _pure_raises(getattr(rational, pure_name), arg)

    assert c_refused == (want == "refuse"), (
        f"{_row_id(symbol, arg)} must {want}; C returned status={status} "
        f"value={value!r}"
    )
    assert c_refused == pure_refused, (
        f"{_row_id(symbol, arg)}: the C projection "
        f"{'refused' if c_refused else 'returned ' + repr(value)} while the "
        f"pure projection "
        f"{'raised ' + type(pure_result).__name__ if pure_refused else 'returned ' + repr(pure_result)}. "
        "ADR-0009 §2.4: co-equal implementations may not differ in which "
        "inputs they serve."
    )


@_needs_native
@pytest.mark.parametrize(
    ("symbol", "pure_name", "arg"),
    _DECLINED_ROWS,
    ids=[f"{s}-{a!r}" for s, _, a in _DECLINED_ROWS],
)
@_DECLINED_T1188
def test_declined_c_serves_what_pure_refuses(
    symbol: str, pure_name: str, arg: float
) -> None:
    """Strict-xfail. Passes only when the decline is repaired — then it reds."""
    status, _value = _c_unary(symbol, arg)
    c_refused = status != _native.SRMECH_OK
    pure_refused, _ = _pure_raises(getattr(rational, pure_name), arg)
    assert c_refused == pure_refused


@_needs_native
@pytest.mark.parametrize(
    ("symbol", "pure_name", "arg", "want"),
    [r for r in _UNARY_ROWS if r[3] == "refuse"],
    ids=[f"{s}-{a!r}" for s, _, a, w in _UNARY_ROWS if w == "refuse"],
)
def test_a_refusal_writes_nan_not_a_plausible_number(
    symbol: str, pure_name: str, arg: float, want: str
) -> None:
    """The VALUE half, which a status-only gate cannot see.

    ``srmech.h`` and ``srmech_sqrt.c`` both say a refused argument leaves
    ``*out`` at NaN. The implementation writes ``x - x``, which is **0.0** for
    every finite negative x — measured at rc472,
    ``srmech_rational_sqrt(-4.0) -> (SRMECH_ERR_BAD_INPUT, 0.0)``. The status
    is already correct there; only the written value is wrong, which is exactly
    why status-only propagation would not close it.
    """
    status, value = _c_unary(symbol, arg)
    if status == _native.SRMECH_OK:
        pytest.fail(
            f"{_row_id(symbol, arg)} returned SRMECH_OK with {value!r}; the "
            "status row for it fails separately"
        )
    assert math.isnan(value), (
        f"{_row_id(symbol, arg)} refused with status={status} but wrote "
        f"{value!r}. The header promises NaN. A caller that checks the value "
        "and not the status is handed a real number."
    )


@_needs_native
@pytest.mark.parametrize(
    ("symbol", "pure_name", "arg", "want"),
    [r for r in _UNARY_ROWS if r[3] == "serve"],
    ids=[f"{s}-{a!r}" for s, _, a, w in _UNARY_ROWS if w == "serve"],
)
def test_values_agree_where_both_projections_answer(
    symbol: str, pure_name: str, arg: float, want: str
) -> None:
    status, value = _c_unary(symbol, arg)
    assert status == _native.SRMECH_OK, (
        f"{_row_id(symbol, arg)} must be served; got status={status}"
    )
    pure_refused, pure_result = _pure_raises(getattr(rational, pure_name), arg)
    assert not pure_refused, (
        f"{_row_id(symbol, arg)}: C served it and the pure projection raised "
        f"{type(pure_result).__name__}"
    )
    assert value == pytest.approx(float(pure_result), rel=1e-13, abs=1e-13), (
        f"{_row_id(symbol, arg)}: C gave {value!r}, pure gave "
        f"{float(pure_result)!r}"
    )


@_needs_native
@pytest.mark.parametrize(
    ("y", "x", "want"), _ATAN2_ROWS,
    ids=[f"atan2-{y!r}-{x!r}-{w}" for y, x, w in _ATAN2_ROWS],
)
def test_atan2_agrees_with_pure_in_status_and_value(
    y: float, x: float, want: str
) -> None:
    """``srmech_atan2`` computes ``y / x`` and calls ``srmech_atan``.

    ``inf / inf`` is NaN, so ``atan2(+inf, +inf)`` reaches the poison path with
    no NaN ever passed in. Measured at rc472: ``(SRMECH_OK,
    -3.2146018366025517)`` — a finite value BELOW -pi, outside atan2's own
    codomain — while ``rational.atan2(+inf, +inf)`` answers pi/4. The two
    projections disagree there in value AND in status.
    """
    status, value = _c_atan2(y, x)
    c_refused = status != _native.SRMECH_OK
    pure_refused, pure_result = _pure_raises(rational.atan2, y, x)

    assert c_refused == (want == "refuse"), (
        f"atan2({y!r}, {x!r}) must {want}; C returned status={status} "
        f"value={value!r}"
    )
    assert c_refused == pure_refused, (
        f"atan2({y!r}, {x!r}): C "
        f"{'refused' if c_refused else 'returned ' + repr(value)}, pure "
        f"{'raised' if pure_refused else 'returned ' + repr(pure_result)}"
    )
    if not c_refused:
        assert value == pytest.approx(float(pure_result), rel=1e-13, abs=1e-13), (
            f"atan2({y!r}, {x!r}): C gave {value!r}, pure gave "
            f"{float(pure_result)!r}"
        )


# --------------------------------------------------------------------------
# THE COMPOSITES. Every row here is red WITHOUT any contract change: the callee
# already refuses at rc472 and the composite discards its status.
# --------------------------------------------------------------------------
@_needs_native
def test_equation_of_centre_the_named_defect() -> None:
    """The row the whole rc is named for.

    ``4 * (2**53 + 1)`` is exactly ``2**55``, which ``srmech_sin`` already
    refuses; at rc472 ``srmech_kepler.c:180`` discarded that refusal. Measured then:
    ``(SRMECH_OK, -0.08984990210223018)`` from C, ``ValueError`` from Python.
    """
    fn = _bind("srmech_equation_of_centre", [_D, _D, _U32, _DP])
    out = ctypes.c_double(0.0)
    status = fn(_D(2.0 ** 53 + 1), _D(0.0549), _U32(4), ctypes.byref(out))

    python_refused, python_result = _pure_raises(
        kepler.equation_of_centre, 2.0 ** 53 + 1, 0.0549, 4
    )
    assert python_refused, (
        "the Python projection must refuse this input; it returned "
        f"{python_result!r}"
    )
    assert status != _native.SRMECH_OK, (
        f"equation_of_centre(2^53+1, 0.0549, 4) returned SRMECH_OK with "
        f"{out.value!r} at the C symbol, while the Python projection raised "
        f"{type(python_result).__name__}. A bare-C host computes a wrong "
        "number and is told it is correct."
    )


@_needs_native
@pytest.mark.parametrize("ecc", [NAN, INF, -INF, 1.0, -0.1])
def test_the_eccentricity_band_is_refused_identically_by_both_projections(
    ecc: float,
) -> None:
    """The repair pass's own row (`#T1188`) — the parameter, not the angle.

    Every composite row above reaches its refusal through a CALLEE. This one
    is the function's guard on its OWN parameter, and through
    ``7665c594c`` that guard was written ``e < 0.0 || e >= 1.0`` — NaN-BLIND,
    since both comparisons are false for a NaN, so the rejecting branch was
    not taken. The Python peer has always spelled it ``not (0.0 <= e < 1.0)``
    (in ``kepler.kepler_solve`` and ``kepler.equation_of_centre``), which IS
    NaN-catching.

    Measured at ``7665c594c`` before the repair, native cell, ABI 26 == 26,
    CPython 3.12.3, numpy absent::

        C  equation_of_centre(0.7, nan, 4) -> status 0, out=nan
        py equation_of_centre(0.7, nan, 4) -> ValueError: e must satisfy
                                              0 <= e < 1; got nan

    ``kepler_solve`` carried the identical guard and was saved only
    incidentally — a NaN ``e`` poisons ``E`` and ``srmech_sin`` now refuses
    NaN — so it is parametrised here too: "saved incidentally" is a property
    of today's callees, not a contract.
    """
    for symbol, argtypes, c_args, pure_fn, pure_args in (
        ("srmech_equation_of_centre", [_D, _D, _U32, _DP],
         (_D(0.7), _D(ecc), _U32(4)), kepler.equation_of_centre, (0.7, ecc, 4)),
        ("srmech_kepler_solve", [_D, _D, _D, _U32, _DP],
         (_D(0.7), _D(ecc), _D(1e-12), _U32(30)), kepler.kepler_solve, (0.7, ecc)),
    ):
        fn = _bind(symbol, argtypes)
        out = ctypes.c_double(0.0)
        status = fn(*c_args, ctypes.byref(out))
        python_refused, python_result = _pure_raises(pure_fn, *pure_args)
        assert python_refused, (
            f"{symbol}: the Python projection must refuse e={ecc!r}; it "
            f"returned {python_result!r}"
        )
        assert status != _native.SRMECH_OK, (
            f"{symbol} accepted e={ecc!r} and returned SRMECH_OK with "
            f"{out.value!r}, while the Python projection raised "
            f"{type(python_result).__name__}. ADR-0009 §2.4: co-equal "
            "projections may not differ in which inputs they serve."
        )


@_needs_native
def test_pin_slot_propagates_its_cos_refusal() -> None:
    fn = _bind("srmech_pin_slot", [_D, _D, _D, _DP])
    out = ctypes.c_double(0.0)
    status = fn(_D(2.0 ** 55), _D(0.5), _D(1.0), ctypes.byref(out))
    python_refused, python_result = _pure_raises(
        kepler.pin_slot, 2.0 ** 55, 0.5, 1.0
    )
    assert python_refused, f"Python returned {python_result!r}"
    assert status != _native.SRMECH_OK, (
        f"pin_slot(2^55, 0.5, 1.0) returned SRMECH_OK with {out.value!r}; "
        "srmech_cos(2^55) already refuses, and rc472's srmech_kepler.c:97 "
        "discarded it"
    )


@_needs_native
def test_kepler_solve_propagates_its_sin_refusal() -> None:
    fn = _bind("srmech_kepler_solve", [_D, _D, _D, _U32, _DP])
    out = ctypes.c_double(0.0)
    status = fn(_D(2.0 ** 55), _D(0.3), _D(1e-12), _U32(20), ctypes.byref(out))
    python_refused, python_result = _pure_raises(
        kepler.kepler_solve, 2.0 ** 55, 0.3
    )
    assert status != _native.SRMECH_OK, (
        f"kepler_solve(2^55, 0.3, 1e-12, 20) returned SRMECH_OK with "
        f"{out.value!r}. srmech_sin(2^55) already refuses; the Newton "
        "iteration then never moves E off its M initial guess, so the caller "
        f"is handed E == M. (E == M: {out.value == 2.0 ** 55}.) The Python "
        f"projection {'raised ' + type(python_result).__name__ if python_refused else 'returned ' + repr(python_result)}."
    )


@_needs_native
@pytest.mark.parametrize(
    ("op_id", "op_name", "arg"),
    [
        (1, "COS", 2.0 ** 55),
        (2, "SIN", 2.0 ** 55),
        (1, "COS", INF),
        (2, "SIN", INF),
        (0, "EXP", NAN),
        (1, "COS", NAN),
        (2, "SIN", NAN),
        (3, "LOG", NAN),
    ],
    ids=lambda v: str(v),
)
def test_elementwise_transcendental_propagates_per_element(
    op_id: int, op_name: str, arg: float
) -> None:
    """The array kernel's own LOG pre-scan is ``arr[i] <= 0.0``.

    That is FALSE for NaN, so NaN reaches the callee in every op including LOG
    — the hole the Python-side cover does not reach either, since
    ``_q61_trig_range_refuse`` compares magnitudes and NaN fails both
    comparisons.
    """
    fn = _bind("srmech_elementwise_transcendental", [_U32, _DP, ctypes.c_int, _DP])
    arr = (ctypes.c_double * 1)(arg)
    out = (ctypes.c_double * 1)(-12345.0)
    status = fn(_U32(1), ctypes.cast(arr, _DP), ctypes.c_int(op_id),
                ctypes.cast(out, _DP))
    assert status != _native.SRMECH_OK, (
        f"elementwise_transcendental([{arg!r}], {op_name}) returned SRMECH_OK "
        f"with {out[0]!r}, while the scalar peer it calls refuses the same "
        "argument"
    )


@_needs_native
@pytest.mark.parametrize("arg", [2.0 ** 55, INF, NAN], ids=lambda v: repr(v))
def test_kuramoto_steps_propagate_their_sin_refusal(arg: float) -> None:
    """At 2**55 the refusal is discarded and oscillator 0 is silently FROZEN.

    Measured at rc472: ``srmech_cascade_kuramoto_step_f64([0.0, 2**55], ...)``
    -> ``(SRMECH_OK, [0.0, 3.602879701896397e+16])`` — a wrong number, not a
    NaN a caller could notice.
    """
    theta = (ctypes.c_double * 2)(0.0, arg)
    omega = (ctypes.c_double * 2)(0.0, 0.0)

    plain = _bind("srmech_cascade_kuramoto_step_f64",
                  [_DP, _DP, _SIZE, _D, _D, _DP])
    out = (ctypes.c_double * 2)(-12345.0, -12345.0)
    status = plain(ctypes.cast(theta, _DP), ctypes.cast(omega, _DP), _SIZE(2),
                   _D(1.0), _D(0.1), ctypes.cast(out, _DP))
    assert status != _native.SRMECH_OK, (
        f"kuramoto_step_f64([0.0, {arg!r}]) returned SRMECH_OK with "
        f"{[out[0], out[1]]!r}"
    )

    general = _bind("srmech_cascade_kuramoto_step_general_f64",
                    [_DP, _DP, _SIZE, _DP, _D, _D, _DP, _DP, _D, _DP])
    out = (ctypes.c_double * 2)(-12345.0, -12345.0)
    status = general(ctypes.cast(theta, _DP), ctypes.cast(omega, _DP), _SIZE(2),
                     None, _D(1.0), _D(0.1), None, None, _D(0.1),
                     ctypes.cast(out, _DP))
    assert status != _native.SRMECH_OK, (
        f"kuramoto_step_general_f64([0.0, {arg!r}]) returned SRMECH_OK with "
        f"{[out[0], out[1]]!r}"
    )


# --------------------------------------------------------------------------
# A MATRIX-KERNEL divergence, pinned. rc473 pre-publish pass, `#T1188`.
#
# Everything above this line is SCALAR: six Class-N C symbols against their
# `srmech.math.rational` peers. rc473's closing question — "is any divergence
# left UNFILED?" — was answered over 90 such rows and the answer was 0, which
# is true of that population and of no other. The first probe at a MATRIX
# kernel found one, and it reproduces on the shipped artifact.
#
# MEASURED, both cells, same interpreter, native cell authenticated by
# srmech_rational_sqrt(NaN) -> status 2 at the ctypes symbol:
#
#   normalized_laplacian(2, [(0,1)], weights=[+inf])
#       native cell, dispatched wrapper  -> [[0.0, nan], [nan, 0.0]]
#       native cell, _normalized_laplacian_py IN THE SAME PROCESS
#                                        -> [[1.0, nan], [nan, 1.0]]
#       pure cell, wrapper (IS the _py)  -> [[1.0, nan], [nan, 1.0]]
#
# The normalised diagonal is 1.0 or 0.0 depending only on whether a library is
# loaded. It is +inf-SPECIFIC — -inf and nan agree on both cells and through
# both routes, and so do the finite controls — which is narrower than
# "non-finite" and was measured rather than assumed. Cause, at the symbol:
# srmech_rational_sqrt(+Inf) -> (SRMECH_OK, +Inf), so +Inf is not a refusal
# class and the two routes differ only in the order they take 1/sqrt(inf) in.
#
# NOT repaired in rc473: which projection is right is the float carrier's
# non-finite contract, which is unwritten. Filed as an ADR-0009 §1.2 row under
# `#T1188`; ADR-0009 §5 says a disclosure without an executable pin is not an
# exemption, and this is the pin.
#
# Two design points that are the whole reason this row is not vacuous:
#   * _needs_native GATING. On a pure cell the wrapper IS
#     _normalized_laplacian_py — measured, both [[1.0, nan], [nan, 1.0]] — so
#     an ungated comparison would agree with ITSELF and a strict xfail would
#     XPASS and redden the pure cell for the wrong reason.
#   * The four AGREEING siblings ship as plain passing rows, so this is not an
#     instrument that can only return "differ".
# --------------------------------------------------------------------------
_DIVERGENT_MATRIX_T1188 = pytest.mark.xfail(
    strict=True,
    reason=(
        "`#T1188`: normalized_laplacian(weights=[+inf]) answers 1.0 on the "
        "normalised diagonal through the pure implementation and 0.0 through "
        "the C symbol — an ADR-0009 §2.4 divergence at a MATRIX kernel, "
        "outside the scalar population rc473's 90-row closing probe asked "
        "about. NOT repaired here: which answer is right is the float "
        "carrier's non-finite contract, which is unwritten, and writing it is "
        "an rc of its own that must separate +Inf from -Inf because at this "
        "divergence they behave differently. Strict, so that repairing it "
        "REDDENS this row instead of letting it pass forever."
    ),
)

#: (weights value, does the wrapper agree with `_normalized_laplacian_py`).
#: The False row is the divergence; the True rows are the controls that prove
#: the comparator can return otherwise.
_LAPLACIAN_NONFINITE_ROWS: "list[tuple[float, bool]]" = [
    (math.inf, False),
    (-math.inf, True),
    (math.nan, True),
    (-1.0, True),
    (1.0, True),
]


def _as_rows(result) -> "list[list[float]]":
    """`Mat` or nested list -> nested list, so the two routes are comparable.

    The dispatched wrapper returns a ``Mat`` and ``_normalized_laplacian_py``
    returns nested lists on this tree; normalising here rather than at the
    assertion keeps the failure message about the VALUES.
    """
    return result.tolist() if hasattr(result, "tolist") else result


def _same_grid(a, b) -> bool:
    """NaN-aware elementwise equality. ``nan != nan``, and every row here has
    NaNs off the diagonal, so a plain ``==`` would report every row as
    divergent and the pin would be vacuous."""
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return False
        for x, y in zip(ra, rb):
            if math.isnan(x) and math.isnan(y):
                continue
            if x != y:
                return False
    return True


@_needs_native
@pytest.mark.parametrize(
    "weight",
    [w for w, agrees in _LAPLACIAN_NONFINITE_ROWS if agrees],
    ids=[repr(w) for w, agrees in _LAPLACIAN_NONFINITE_ROWS if agrees],
)
def test_normalized_laplacian_agrees_between_projections(weight: float) -> None:
    """The controls. Four weights where the two routes agree in-process.

    Without these the divergent row below is an instrument nobody has watched
    return "agree", and a comparator that cannot would pin a defect that is
    its own.
    """
    from srmech.math import laplacian as _lap

    dispatched = _as_rows(_lap.normalized_laplacian(2, [(0, 1)],
                                                    weights=[weight]))
    pure = _as_rows(_lap._normalized_laplacian_py(2, [(0, 1)],
                                                  weights=[weight]))
    assert _same_grid(dispatched, pure), (
        f"normalized_laplacian(weights=[{weight!r}]) disagrees between the "
        f"dispatched wrapper {dispatched!r} and _normalized_laplacian_py "
        f"{pure!r} in the same process. This row is a CONTROL — it agreed "
        "when the +inf divergence beside it was filed, so a failure here is a "
        "NEW divergence, not the filed one."
    )


@_needs_native
@_DIVERGENT_MATRIX_T1188
def test_normalized_laplacian_plus_inf_diverges_between_projections() -> None:
    """Strict-xfail. Passes only when the +inf contract is settled — then reds."""
    from srmech.math import laplacian as _lap

    dispatched = _as_rows(_lap.normalized_laplacian(2, [(0, 1)],
                                                    weights=[math.inf]))
    pure = _as_rows(_lap._normalized_laplacian_py(2, [(0, 1)],
                                                  weights=[math.inf]))
    assert _same_grid(dispatched, pure), (
        f"dispatched {dispatched!r} vs _normalized_laplacian_py {pure!r}"
    )


# --------------------------------------------------------------------------
# ROSTER COVERAGE, two-way. A new scalar Class-N export cannot be added
# without a refusal row here.
# --------------------------------------------------------------------------
_HEADER = (Path(__file__).resolve().parent.parent.parent
           / "c" / "include" / "srmech.h")

#: A declaration of the form ``srmech_status_t srmech_NAME(double a, double
#: *out);`` or the two-argument ``atan2`` shape, with or without the
#: ``SRMECH_NODISCARD`` attribute macro in front of it. This is the family
#: whose members take a real and write a real through a status channel — the
#: ops this file is responsible for.
#:
#: ⚠️ The optional prefix is load-bearing and was added at rc473 with the
#: attribute itself. Without it the anchor ``^srmech_status_t`` stopped
#: matching every tagged declaration the moment ``SRMECH_NODISCARD`` landed,
#: and the scan fell from eight symbols to one. It did NOT fall silently —
#: ``test_the_roster_covers_every_class_n_scalar_export_two_way`` failed on its
#: own emptiness assertion, whose message is "Re-point the regex; do not delete
#: the assertion" — which is what this is. Both the emptiness control and the
#: two-way equality below are what prove the widened pattern still finds the
#: same family rather than a smaller one.
_SCALAR_DECL = re.compile(
    r"^(?:SRMECH_NODISCARD\s+)?srmech_status_t\s+(srmech_[A-Za-z0-9_]+)\("
    r"\s*double\s+[A-Za-z_][A-Za-z0-9_]*\s*,"
    r"(?:\s*double\s+[A-Za-z_][A-Za-z0-9_]*\s*,)?"
    r"\s*double\s*\*\s*out\s*\)\s*;",
    re.M,
)


#: Declarations the regex above matches that are NOT Class-N rational peers,
#: each with the reason it is out of this file's subject. Written out rather
#: than excluded by a cleverer regex, so that a new scalar export must be
#: either exercised or explicitly ruled out by a human with a stated reason —
#: and so that a stale entry here is itself caught (see the third assertion).
_NOT_A_RATIONAL_PEER = {
    "srmech_cascade_dead_band_f64": (
        "a cascade LEAF, not a Class-N transcendental: its pure peer is "
        "srmech.cascade.leaves.dead_band, not srmech.math.rational. Its "
        "contract is *out = value's OWN zero (`value * 0.0`) below the band, "
        "so dead_band(NaN, band) is NaN BY DESIGN in both projections and is "
        "a pinned required-DIVERGENT witness in the rc450 value-parity "
        "comparator. A refusal row for it would assert the opposite of its "
        "own specification."
    ),
}


def _header_scalar_family() -> set[str]:
    return set(_SCALAR_DECL.findall(_HEADER.read_text(encoding="utf-8")))


def test_the_roster_covers_every_class_n_scalar_export_two_way() -> None:
    """Strict set equality between the header's family and this file's rows.

    Two-way on purpose. A symbol declared and not exercised here is an op whose
    C-boundary behaviour nothing measures; a row naming a symbol the header
    does not declare is a row measuring nothing. The third direction — an
    exclusion that no longer names a real declaration — is asserted too,
    because a stale carve-out reads exactly like a covered symbol.
    """
    declared = _header_scalar_family() - set(_NOT_A_RATIONAL_PEER)
    stale = sorted(set(_NOT_A_RATIONAL_PEER) - _header_scalar_family())
    assert not stale, (
        f"{len(stale)} exclusion(s) in _NOT_A_RATIONAL_PEER no longer match a "
        f"declaration in {_HEADER.name}: {stale}. Remove them — a carve-out "
        "for a symbol that does not exist is indistinguishable from coverage."
    )
    assert declared, (
        f"the scalar-declaration scan of {_HEADER} parsed to ZERO symbols. An "
        "empty parse is not an empty family — it is this gate failing to "
        "measure. Re-point the regex; do not delete the assertion."
    )
    exercised = {symbol for symbol, _, _, _ in _UNARY_ROWS}
    exercised |= {symbol for symbol, _, _ in _DECLINED_ROWS}
    exercised.add("srmech_atan2")

    unexercised = sorted(declared - exercised)
    assert not unexercised, (
        f"{len(unexercised)} scalar Class-N export(s) have no C-boundary row "
        f"in this file: {unexercised}. Add a refusal row and a served row for "
        "each."
    )
    phantom = sorted(exercised - declared)
    assert not phantom, (
        f"{len(phantom)} row(s) name a symbol {_HEADER.name} does not declare "
        f"in the scalar family: {phantom}"
    )


# --------------------------------------------------------------------------
# THE ROSTER'S OWN BLIND SPOT, closed at the A6 repair pass.
#
# `_SCALAR_DECL`'s note above calls its population "the family whose members
# take a real and write a real through a status channel". It is NOT that
# family: the pattern requires the LAST parameter to be spelled literally
# `double *out` and allows at most TWO `double` inputs, so of the SEVENTEEN
# status-returning exports whose parameters are all-`double` scalars plus
# scalar out-pointers it matches EIGHT. On the narrower spelling a merge gate
# used against this rc — n doubles, exactly one `double *` out — it is 8 of 10.
#
# That mattered, and it was found from OUTSIDE this file: a cross-implementation
# differential drove the whole double-taking exported roster instead of these
# six scalar symbols, and reported this gate returning `90 passed, 6 xfailed`
# on a cell where `srmech_winding_fold`'s residue DIVERGED between the
# projections by up to 7.07e8 x 2**-44 (past tense as of the rc473 twin-defect
# pass, which repaired it; the roster blindness it exposed is unchanged and is
# what this section is about) — because `srmech_winding_fold` is a
# declared export this file's roster regex cannot spell. A gate whose
# population predicate is narrower than the family its own prose claims is the
# same defect as a grep that cannot spell its own symbol.
#
# The repair is NOT to widen `_SCALAR_DECL`. Every symbol it matches carries
# both a served and a refused row, and widening it would silently DEMAND those
# rows for nine more symbols — which is a different rc, not a repair. The
# repair is to make the RESIDUAL DECIDABLE: enumerate the wider family from
# the header and require every member to sit in exactly one of three places —
# exercised above, excluded in `_NOT_A_RATIONAL_PEER`, or named below with the
# reason it has no row. A symbol in NONE of them then reddens by name.
# --------------------------------------------------------------------------

#: Head-to-`;` declaration capture, parameter list whitespace-normalised, for
#: the family `_SCALAR_DECL`'s prose claims and its pattern does not reach.
_WIDE_SCALAR_DECL = re.compile(
    r"^(?:SRMECH_NODISCARD\s+)?srmech_status_t\s+(srmech_[A-Za-z0-9_]+)\s*\("
    r"(?P<params>[^;{]*?)\)\s*;",
    re.M | re.S,
)
_SCALAR_IN = re.compile(r"(?:const\s+)?double\s+[A-Za-z_]\w*")
_SCALAR_OUT = re.compile(
    r"(?:double|int64_t|int32_t|uint32_t|int)\s*\*\s*[A-Za-z_]\w*"
)

#: Wider-family members the narrow `_SCALAR_DECL` cannot match, each with the
#: reason it has no served/refused row pair here.
_OUTSIDE_THE_NARROW_SHAPE: "dict[str, str]" = {
    "srmech_sin_q61": "Q61 peer: writes int64_t, not `double *out`.",
    "srmech_cos_q61": "Q61 peer: writes int64_t, not `double *out`.",
    "srmech_atan_q61": "Q61 peer: writes int64_t, not `double *out`.",
    "srmech_exp_q61": "Q61 peer: two int64_t out-params (core, n).",
    "srmech_log_q61": "Q61 peer: two int64_t out-params (logm, e).",
    "srmech_sqrt_q61": "Q61 peer: two int64_t out-params (root, p).",
    "srmech_cascade_magnitude_f64": (
        "a cascade ATOM, not a Class-N transcendental — the same KIND of "
        "reason srmech_cascade_dead_band_f64 carries in _NOT_A_RATIONAL_PEER, "
        "though not the same module. Its pure peer is "
        "srmech.cascade.atoms.magnitude (`_c_claims.py` maps exactly that "
        "name to this symbol), a Class-K pin-slot at zero that is "
        "type-preserving over any ordered real carrier — not "
        "srmech.math.rational. (This entry said `srmech.cascade.leaves` until "
        "it was checked: `dead_band` IS in leaves.py, `magnitude` is in "
        "atoms.py, and a carve-out whose stated reason names the wrong module "
        "is the defect this file's own A6 pass exists to remove.)"
    ),
    "srmech_pin_slot": (
        "`#T1188`: THREE double inputs, so it has no single served/refused "
        "row shape here. It is not unexercised: the divergence this entry "
        "used to record as live — pin_slot(pin_distance=+inf, pin_offset=1.0, "
        "theta=0.0) returning 0.0 through C where the pure projection raised, "
        "and -inf returning 3.141592653589793 — was REPAIRED in the rc473 "
        "twin-defect pass. srmech_pin_slot now refuses a non-finite "
        "pin_offset or pin_distance as a precondition on its own arguments, "
        "and tests/test_kepler_non_finite_slots_rc473.py drives the C symbol "
        "directly over both slots and both signs. (The entry said 'FILED "
        "rather than exercised; pre-existing on b398b8c46' — the second half "
        "was and stays true; the first is now false.)"
    ),
    "srmech_winding_fold": (
        "`#T1188`: two out-params of DIFFERENT types (int64_t *w_out, "
        "double *theta_out), so it has no served/refused row shape here — it "
        "is pinned executably below instead. This entry read 'the theta_out "
        "channel DIVERGES between the projections' at the A6 filing; that "
        "divergence was REPAIRED in the same rc (one 2-pi constant, one "
        "2**-44 grid, both projections), and the rows below now require "
        "bit-identical (w, theta_res) at the 24 angles the law was fitted "
        "over, at the C symbol as well as through the wrapper."
    ),
}


def _header_wide_scalar_family() -> "set[str]":
    text = _HEADER.read_text(encoding="utf-8")
    out: "set[str]" = set()
    for m in _WIDE_SCALAR_DECL.finditer(text):
        parts = [p.strip() for p in " ".join(m.group("params").split()).split(",")]
        if not parts or parts in ([""], ["void"]):
            continue
        ins = [p for p in parts if "*" not in p]
        outs = [p for p in parts if "*" in p]
        if not ins or not outs:
            continue
        if not all(_SCALAR_IN.fullmatch(p) for p in ins):
            continue
        if not all(_SCALAR_OUT.fullmatch(p) for p in outs):
            continue
        out.add(m.group(1))
    return out


def test_the_wider_scalar_family_has_no_unaccounted_member() -> None:
    """Every all-double-in / scalar-out status export is PLACED, or this reds.

    Exercised above, excluded with a reason, or named in
    `_OUTSIDE_THE_NARROW_SHAPE` with a reason. The point is that a symbol in
    NONE of them — which is what `srmech_winding_fold` and `srmech_pin_slot`
    were — fails here BY NAME instead of being invisible to a roster regex.
    """
    wide = _header_wide_scalar_family()
    narrow = _header_scalar_family()
    assert len(wide) >= len(narrow), (
        "the wide scalar family parsed SMALLER than the narrow one, which "
        "means this scan is broken rather than that the family shrank: "
        f"wide={len(wide)} narrow={len(narrow)}"
    )
    exercised = {symbol for symbol, _, _, _ in _UNARY_ROWS}
    exercised |= {symbol for symbol, _, _ in _DECLINED_ROWS}
    exercised.add("srmech_atan2")
    placed = exercised | set(_NOT_A_RATIONAL_PEER) | set(_OUTSIDE_THE_NARROW_SHAPE)

    unaccounted = sorted(wide - placed)
    assert not unaccounted, (
        f"{len(unaccounted)} scalar status export(s) sit in NO place this file "
        f"accounts for: {unaccounted}. Give each a served/refused row pair, or "
        "a named reason in _OUTSIDE_THE_NARROW_SHAPE. Do not narrow this scan "
        "to make them disappear."
    )
    phantom = sorted(set(_OUTSIDE_THE_NARROW_SHAPE) - wide)
    assert not phantom, (
        f"{len(phantom)} entry/entries in _OUTSIDE_THE_NARROW_SHAPE no longer "
        f"name a declaration in the wider family: {phantom}. A carve-out for a "
        "symbol that does not exist is indistinguishable from coverage."
    )


def test_the_narrow_roster_is_a_subset_and_not_the_family() -> None:
    """Non-vacuity for the row above: the two populations must DIFFER.

    If the narrow regex ever matched the whole wider family, the assertion
    above would be satisfied by `_SCALAR_DECL` alone and
    `_OUTSIDE_THE_NARROW_SHAPE` would be a dead instrumentation seam.
    """
    missed = sorted(_header_wide_scalar_family() - _header_scalar_family())
    assert missed, (
        "the narrow _SCALAR_DECL now matches the whole wider scalar family. "
        "Good news — but _OUTSIDE_THE_NARROW_SHAPE is then dead: fold its "
        "entries into the rows above and delete this test."
    )
    assert set(missed) == set(_OUTSIDE_THE_NARROW_SHAPE), (
        "the set the narrow regex misses is not the set named as missed. "
        f"missed={missed} named={sorted(_OUTSIDE_THE_NARROW_SHAPE)}"
    )


# --------------------------------------------------------------------------
# `srmech.cascade.one.winding_fold` — `theta_res` DIVERGED between the
# projections at ordinary FINITE angles. Filed at the A6 repair pass;
# REPAIRED in the same rc, and this block is the inverted pin.
#
# WHAT WAS HERE, and why it is gone. A6 shipped a STRICT xfail asserting the
# gap at theta = 3.1415926535897932e16 exceeded the 2**-44 grid, with a reason
# recording the law: |native − pure| / |w| in [7.944e-21, 8.039e-21] rad per
# turn over the 15 probed angles with |w| >= 1e8, a 1.2% spread across five
# decades, reaching 4.0193e-05 = 7.07e8 x 2**-44, 17 of 24 probed angles over
# the grid, `w` exact-integer equal on every row. All of that reproduced —
# independently, on an authenticated cell — and the repair then made the row
# XPASS, which is what a strict xfail is for. It is replaced rather than
# deleted so the figure it carried is not lost.
#
# WHAT THE REPAIR WAS. The divergence was TWO 2-pi constants: the C read the
# residue off the quarter-turn fold's 64-bit 2/pi (own error 8.1449e-22 =
# 2**-70.06, inherited by the residue at pi**2*delta = 8.0387e-21 rad per whole
# turn), while the pure peer folds against the Machin-2-pi rational
# `_EPH_TWO_PI = N / 2**80`. `srmech_winding_fold` now folds against that same
# rational, in exact integers, and emits on the same 2**-44 grid — so the two
# projections return the IDENTICAL `(w, theta_res)` pair, not two
# quantisations of one. srmech_sin / srmech_cos are untouched: trig_reduce_k
# still serves them and only the winding fold settles.
#
# The pin's shape is the A6 one, inverted:
#   * `_needs_native`-gated — on a pure cell the dispatched op IS the pure
#     fold, so an ungated equality would agree with itself and pin nothing;
#   * dispatched public op vs `_eph_seam_fold` IN ONE PROCESS, so there is no
#     cell confound, PLUS a row driving the C symbol directly, because the
#     wrapper could agree while the symbol a bare-C host calls does not;
#   * a NON-VACUITY row proving the comparator can still say "differ" — an
#     equality assertion that cannot fail is not a measurement.
# --------------------------------------------------------------------------

#: The 24 angles the A6 law was fitted over, verbatim, so the repair is proven
#: on the population that produced the finding rather than a friendlier one.
#: 17 of these carried a gap over 2**-44 before the repair.
_WINDING_FOLD_FILED: "tuple[float, ...]" = (
    1.0, 31.41592653589793, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11,
    1e12, 1e13, 1e14, 1e15, 2.0 ** 40, 2.0 ** 50, 2.0 ** 53, 2.0 ** 54, 1.5e16,
    3.1415926535897932e16, -1e10, -1e8, -3.1415926535897932e16,
)

#: `theta` values that agreed even BEFORE the repair. Kept as controls: if
#: these ever disagree the comparator itself has moved, not the fold.
_WINDING_FOLD_AGREEING: "tuple[float, ...]" = (0.0, 1.0, 0.5, -1.0, 2.0)


def _winding_fold_pair(theta: float) -> "tuple[tuple[int, float], tuple[int, float]]":
    """`(dispatched, pure)` as `(w, theta_res)` pairs, in ONE process."""
    from srmech.cascade import one as _one
    from srmech.math import laplacian as _lap

    w_d, res_d = _one.winding_fold(theta)
    w_p, qn = _lap._eph_seam_fold(theta)
    return (w_d, res_d), (w_p, qn / float(_lap._EPH_FOLD_DEN))


def _same_fold(a: "tuple[int, float]", b: "tuple[int, float]") -> bool:
    """THE comparator every winding-fold row below uses: `==` on both harvests.

    One function, so the non-vacuity row exercises the same comparison the
    equality rows assert rather than a look-alike.
    """
    return a[0] == b[0] and a[1] == b[1]


def _gap_mag(a: float, b: float) -> float:
    """`|a - b|` as a Class-K sign branch (never `abs()`), for failure text."""
    d = a - b
    return d if d >= 0.0 else -d


def _pre_repair_q61_residue(theta: float) -> float:
    """The residue `srmech_winding_fold` returned BEFORE the twin-defect pass.

    Transliterated from the pre-repair C (`1ab8d405b:c/src/srmech_trig.c`):
    the quarter-turn reduction's octant and Q61 remainder `r`, then
    `theta_q61 = oct_rel * HALF_PI_Q61 + r` and `theta_q61 / 2**61`, with
    `oct_rel` in {0, 1, -2 or 2 by the sign of r, -1} for octant 0..3. The
    reduction is `srmech.math.rational._q61_reduce`, the pure mirror of the C
    `trig_reduce`, so the 64-bit 2/pi this fold inherited its drift from is
    the same constant here.
    """
    from srmech.math import rational as _r

    ok, octant, r = _r._q61_reduce(theta)
    assert ok, f"_q61_reduce refused {theta!r}; the row is inside the door"
    if octant == 0:
        oct_rel = 0
    elif octant == 1:
        oct_rel = 1
    elif octant == 2:
        oct_rel = -2 if r >= 0 else 2
    else:
        oct_rel = -1
    return float(oct_rel * _r._Q61_HALF_PI_Q61 + r) / float(1 << 61)


def _winding_fold_at_symbol(theta: float) -> "tuple[int, int, float]":
    """`(status, w, theta_res)` straight off `srmech_winding_fold`."""
    import ctypes

    fn = _native.LIB.srmech_winding_fold
    w = ctypes.c_int64(0)
    res = ctypes.c_double(0.0)
    st = fn(ctypes.c_double(theta), ctypes.byref(w), ctypes.byref(res))
    return int(st), int(w.value), float(res.value)


@_needs_native
@pytest.mark.parametrize("theta", _WINDING_FOLD_AGREEING)
def test_winding_fold_agrees_between_projections_at_small_windings(
    theta: float,
) -> None:
    """CONTROL rows. These agreed BEFORE the repair as well as after."""
    (w_d, res_d), (w_p, res_p) = _winding_fold_pair(theta)
    assert w_d == w_p, f"winding disagrees at {theta!r}: {w_d} vs {w_p}"
    assert res_d == res_p, (
        f"theta_res disagrees at {theta!r}: dispatched {res_d!r} vs "
        f"_eph_seam_fold {res_p!r}. This row is a CONTROL — it agreed before "
        "the repair too, so a failure here is a comparator move."
    )


@_needs_native
@pytest.mark.parametrize("theta", _WINDING_FOLD_FILED)
def test_winding_fold_is_bit_identical_between_projections(theta: float) -> None:
    """The inverted pin: BOTH harvests equal, on the 24 filed angles.

    `w` was already exact-integer equal on every one of these; `theta_res` was
    not, on 17 of them. Equality here is bit-level — `==` on the float, not a
    tolerance — because the two projections now quantise onto the same grid
    from the same constant, so there is nothing left for a tolerance to cover.
    """
    (w_d, res_d), (w_p, res_p) = _winding_fold_pair(theta)
    assert w_d == w_p, (
        f"the WINDING diverges at {theta!r} ({w_d} vs {w_p}). That half held "
        "throughout the divergence, so a failure here is a NEW finding."
    )
    assert _same_fold((w_d, res_d), (w_p, res_p)), (
        f"theta_res diverges at {theta!r}: dispatched {res_d!r} vs "
        f"_eph_seam_fold {res_p!r}, gap {_gap_mag(res_d, res_p)!r} = "
        f"{_gap_mag(res_d, res_p) / 2.0 ** -44:.6g} x 2**-44. ADR-0009 §1.2's "
        "winding_fold row is REPAIRED, not filed — this reopens it."
    )


@_needs_native
def test_winding_fold_c_symbol_itself_matches_the_pure_fold() -> None:
    """The bare-C host's view, not the wrapper's.

    `cascade.one.winding_fold` falls back to `_eph_seam_fold` on any non-OK
    status, so a wrapper-only comparison would also pass if the C symbol
    started REFUSING every angle. This row reads the status and requires
    SRMECH_OK, so the door is proven open as well as the value equal.
    """
    for theta in _WINDING_FOLD_FILED:
        st, w_c, res_c = _winding_fold_at_symbol(theta)
        (_, _), (w_p, res_p) = _winding_fold_pair(theta)
        assert st == _native.SRMECH_OK, (
            f"srmech_winding_fold({theta!r}) returned status {st}; the "
            "|theta| < 2**55 door must stay open at these angles."
        )
        assert _same_fold((w_c, res_c), (w_p, res_p)), (
            f"the C SYMBOL diverges at {theta!r}: ({w_c}, {res_c!r}) vs pure "
            f"({w_p}, {res_p!r}). A bare-C host sees this even if the Python "
            "wrapper does not."
        )


def test_the_winding_fold_comparator_can_still_report_a_difference() -> None:
    """NON-VACUITY. An equality that cannot fail is not a measurement.

    Feeds `_same_fold` — the comparator the equality rows above assert with —
    a genuinely DIFFERENT fold: the pre-repair Q61 residue, transliterated in
    `_pre_repair_q61_residue`, paired with the pure winding. At
    `theta = 3.1415926535897932e16` it must report "differ", by more than the
    2**-44 grid; at `theta = 1.0`, where the two folds agreed before the
    repair too, it must report "agree". Both halves run on every cell: the
    comparison involves no library, so a pure cell proves it as well.

    (This row used to assert only `res_p + 2**-44 != res_p` — float
    arithmetic, with no second fold ever compared, so it could not have
    caught a comparator that always said "equal".)

    rc473 repair round 1 (`#T1188`): the two pairs above only proved the
    comparator can see a gap of 7.07e8 grid steps. A merge gate replaced `==`
    with `(a - b)**2 <= tol**2` and this row stayed green at tol = 1e-5 and at
    tol = 2**-44, while six filed angles differ from the pure fold by less
    than one grid step. So the row now also requires "differ" for the
    pre-repair residue at `theta = 31.41592653589793`, a SUB-GRID gap
    (1.224715e-15 = 0.0215 x 2**-44, printed by the repair round's probe on a
    WSL2 CPython 3.12.3 cell), and for a residue and its one-ULP neighbour —
    so any tolerance of one ULP or more reddens it.
    """
    theta = 3.1415926535897932e16
    (_, _), (w_p, res_p) = _winding_fold_pair(theta)
    res_old = _pre_repair_q61_residue(theta)
    gap = _gap_mag(res_old, res_p)
    assert not _same_fold((w_p, res_old), (w_p, res_p)), (
        f"the comparator called the pre-repair fold EQUAL to the pure one at "
        f"{theta!r}: old {res_old!r} vs pure {res_p!r}. Every equality row "
        "above is then unable to fail."
    )
    assert gap > 2.0 ** -44, (
        f"the pre-repair residue differs by {gap!r}, within one 2**-44 grid "
        "step — so this row would not distinguish the forked constant from "
        "a rounding tie, which is not the difference it exists to show."
    )

    (_, _), (w_1, res_1) = _winding_fold_pair(1.0)
    assert _same_fold((w_1, _pre_repair_q61_residue(1.0)), (w_1, res_1)), (
        "control: at theta = 1.0 the pre-repair and pure folds agreed before "
        "the repair; the comparator must still say so, or it is an instrument "
        "that can only return 'differ'."
    )

    theta_sub = 31.41592653589793
    (_, _), (w_s, res_s) = _winding_fold_pair(theta_sub)
    res_old_s = _pre_repair_q61_residue(theta_sub)
    gap_s = _gap_mag(res_old_s, res_s)
    assert 0.0 < gap_s < 2.0 ** -44, (
        f"the pre-repair residue at {theta_sub!r} differs by {gap_s!r}; this "
        "pair exists to be a gap SMALLER than one 2**-44 step and nonzero."
    )
    assert not _same_fold((w_s, res_old_s), (w_s, res_s)), (
        f"the comparator called a sub-grid gap of {gap_s!r} EQUAL at "
        f"{theta_sub!r}; a tolerance that wide hides every filed angle whose "
        "gap is under one grid step."
    )
    res_ulp = math.nextafter(res_1, math.inf)
    assert not _same_fold((w_1, res_1), (w_1, res_ulp)), (
        f"the comparator called {res_1!r} and its one-ULP neighbour "
        f"{res_ulp!r} EQUAL; the equality rows are then a tolerance, not ==."
    )
