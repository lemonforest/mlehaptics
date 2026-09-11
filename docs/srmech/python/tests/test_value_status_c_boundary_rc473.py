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
        "`#T1188`: C serves a non-finite argument to exp / log / rational_sqrt "
        "where the pure projection refuses it — an ADR-0009 §2.4 'differ in "
        "which inputs they serve' instance rc473 does NOT repair. Measured "
        "hazard: lap_sqrt(1.0 + tau*tau) in srmech_laplacian.c and sq_sqrt in "
        "srmech_svd_qr.c both reach +Inf on the tau-overflow path and rely on "
        "sqrt(+Inf) = +Inf to get t = 1/(tau + Inf) = 0, inside static helpers "
        "with no status channel. Disclosure is necessary and is not sufficient "
        "(ADR-0009 §5): the tracked filing is owed separately."
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
    refuses; ``srmech_kepler.c:180`` discards that refusal. Measured at rc472:
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
        "srmech_cos(2^55) already refuses and srmech_kepler.c:97 discards it"
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
