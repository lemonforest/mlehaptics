"""rc403 (`#T1071`) — the Ryu-class shortest-round-trip double writer, gated.

WHAT rc403 FIXED, AND WHY THE OLD GATE DID NOT SEE IT
-----------------------------------------------------
``srmech_double_repr`` shipped from rc190 to rc402 as a search for the shortest
``%.*e`` that ``strtod`` round-trips. That is the shortest **printf-reachable**
round-tripper, not the shortest round-tripper: when the correctly-rounded
decimal at some precision is an exact TIE, glibc breaks it to-even, so the
tie's other neighbour — which *does* round-trip at that length — was never
offered as a candidate and the search fell through to one digit too many.
``srmech.h`` called this "David Gay 'r' mode"; it was not.

MEASURED against the pre-rc403 library while building this test:

    class                                 n           divergences
    -------------------------------------------------------------
    signed powers of two (exhaustive)     4,196            92
    dyadic k/2**n                       243,460           165
    low/high mantissa x every exponent   57,288            92
    subnormals                        1,200,002             0
    fixed<->scientific switch points      6,320             0
    int64 boundaries                        180             0
    random decimal-ish                  498,313             0
    UNIFORMLY RANDOM BIT PATTERNS     3,000,000             0   <-- the trap
    -------------------------------------------------------------
    TOTAL                             5,009,759           349

That last row is why this file sweeps by STRUCTURE and not by volume. Three
million uniformly random doubles found the defect zero times, because it lives
in the zero-mantissa class; 4196 powers of two found it 92 times. A gate built
on random sampling would have gone green with the defect live — and a
previously-proposed gate for this exact work did exactly that.

The same 5,009,759-pattern sweep against rc403 returns 0 divergences, as does a
separate 20,000,000-pattern random confidence run.

WHAT IS CHECKED HERE
--------------------
Bit patterns are fed as INTEGERS and reconstituted with ``struct.unpack``, never
parsed from text, so the parser cannot contaminate the reading. The oracle is
``repr(float)``, which is what ``json.dumps`` emits for a float.

The bare-C half of this gate is ``c/test/test_srmech_ryu_repr_rc403.c`` (in the
ctest ``foreach``, so it runs on Linux gcc / macOS clang / Windows MSVC): it
PROVES shortest-round-trip without an oracle and pins the spelling against
literal ``repr()`` strings. This file is the CPython-side parity half.
"""

from __future__ import annotations

import ctypes
import json
import random
import struct

import pytest

from srmech import _native

_needs_native = pytest.mark.skipif(
    not (_native.HAS_NATIVE and getattr(_native, "LIB", None) is not None
         and hasattr(_native.LIB, "srmech_double_repr")),
    reason="srmech_double_repr not loaded (pure / Pyodide / stale host)",
)


def _repr_c(bits: int) -> "str | None":
    """``srmech_double_repr`` of the double with these exact bits, or ``None``
    when the C declines (non-finite)."""
    lib = _native.LIB
    fn = lib.srmech_double_repr
    fn.argtypes = [ctypes.c_double, ctypes.c_void_p, ctypes.c_size_t,
                   ctypes.POINTER(ctypes.c_size_t)]
    fn.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(48)
    n = ctypes.c_size_t(0)
    value = struct.unpack("<d", struct.pack("<Q", bits))[0]
    rc = fn(ctypes.c_double(value), ctypes.cast(buf, ctypes.c_void_p), 48,
            ctypes.byref(n))
    if rc != _native.SRMECH_OK:
        return None
    return buf.raw[:n.value].decode("ascii")


def _sweep(bit_patterns) -> list[tuple[str, str, str]]:
    """Return the divergences as ``(hex bits, C output, repr(float))``."""
    bad: list[tuple[str, str, str]] = []
    for bits in bit_patterns:
        got = _repr_c(bits)
        want = repr(struct.unpack("<d", struct.pack("<Q", bits))[0])
        if got != want:
            bad.append(("%016x" % bits, str(got), want))
    return bad


def _bits(value: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", value))[0]


# ──────────────────────────────────────────────────────────────────────
# The zero-mantissa class — EXHAUSTIVE. This is the class the old
# implementation got wrong 92 times and random sampling never reaches.
# ──────────────────────────────────────────────────────────────────────


def _all_powers_of_two() -> list[int]:
    out = []
    for exponent in range(1, 2047):                 # normals
        out.append(exponent << 52)
        out.append((1 << 63) | (exponent << 52))
    for k in range(52):                             # subnormal powers of two
        out.append(1 << k)
        out.append((1 << 63) | (1 << k))
    return out


@_needs_native
def test_every_signed_power_of_two_is_repr_exact() -> None:
    """All 4196 signed powers of two, exhaustively. 92 diverged before rc403."""
    patterns = _all_powers_of_two()
    assert len(patterns) == 4196, len(patterns)
    bad = _sweep(patterns)
    assert not bad, f"{len(bad)} of {len(patterns)} diverge; first 5: {bad[:5]}"


@_needs_native
def test_float32_machine_epsilon_is_the_named_regression() -> None:
    """2**-24 is the worked example in the rc403 CHANGELOG entry.

    The old code emitted the 17-digit ``5.9604644775390625e-08`` because at
    p=15 glibc broke the exact tie to-even and the resulting decimal failed
    round-trip, so the search never tried the away-from-zero neighbour that
    CPython picks at 16 digits.
    """
    assert _repr_c(_bits(2.0 ** -24)) == "5.960464477539063e-08"
    assert _repr_c(_bits(-(2.0 ** -24))) == "-5.960464477539063e-08"


# ──────────────────────────────────────────────────────────────────────
# The rest of the structured classes.
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_subnormals_are_repr_exact() -> None:
    """The bottom of the subnormal range plus a stride across all of it."""
    patterns = [m for m in range(1, 40_001)]
    patterns += [(1 << 63) | m for m in range(1, 40_001)]
    step = (1 << 52) // 20_000
    patterns += [m for m in range(1, 1 << 52, step)]
    bad = _sweep(patterns)
    assert not bad, f"{len(bad)} of {len(patterns)} diverge; first 5: {bad[:5]}"


@_needs_native
def test_dyadic_rationals_are_repr_exact() -> None:
    """k / 2**n and k * 2**n — the exact binary fractions whose shortest
    decimal terminates, so the tie rule is live. 165 diverged before rc403."""
    patterns = []
    for n in range(0, 320):
        for k in range(1, 64):
            value = float(k) / float(2 ** n)
            if value == 0.0:
                continue
            patterns.append(_bits(value))
            patterns.append(_bits(-value))
    for n in range(0, 300):
        for k in range(1, 64):
            value = float(k) * float(2 ** n)
            patterns.append(_bits(value))
    bad = _sweep(patterns)
    assert not bad, f"{len(bad)} of {len(patterns)} diverge; first 5: {bad[:5]}"


@_needs_native
def test_low_and_high_mantissa_across_every_exponent() -> None:
    """Every biased exponent crossed with the mantissa extremes — the
    neighbourhood of the zero-mantissa class. 92 diverged before rc403."""
    patterns = []
    for exponent in range(1, 2047):
        for mantissa in (0, 1, 2, 3, 4, 5, 7, 8, 15, 16,
                         2 ** 51, 2 ** 51 + 1, (1 << 52) - 1, (1 << 52) - 2):
            patterns.append((exponent << 52) | mantissa)
            patterns.append((1 << 63) | (exponent << 52) | mantissa)
    bad = _sweep(patterns)
    assert not bad, f"{len(bad)} of {len(patterns)} diverge; first 5: {bad[:5]}"


@_needs_native
def test_int64_boundaries_and_signed_zero() -> None:
    """+-0.0 and the integer boundaries a serialiser meets in real payloads."""
    patterns = [0, 1 << 63]
    for base in (2 ** 31, 2 ** 32, 2 ** 53, 2 ** 63, 2 ** 64,
                 10 ** 15, 10 ** 16, 10 ** 17):
        for delta in range(-4, 5):
            patterns.append(_bits(float(base) + delta))
            patterns.append(_bits(-(float(base) + delta)))
    bad = _sweep(patterns)
    assert not bad, f"{len(bad)} diverge; first 5: {bad[:5]}"
    assert _repr_c(0) == "0.0"
    assert _repr_c(1 << 63) == "-0.0"


@_needs_native
def test_fixed_scientific_switch_points() -> None:
    """CPython switches to scientific iff ``decpt <= -4 or decpt > 16``.

    Round-trip cannot see a mistake here — ``1e+16`` and
    ``10000000000000000.0`` are both shortest and both round-trip — so the
    switch is pinned by literal spelling, and with it the MINIMUM two-digit
    exponent that ``%.17g`` renders as ``1e+017`` on Windows.
    """
    assert _repr_c(_bits(1e15)) == "1000000000000000.0"
    assert _repr_c(_bits(1e16)) == "1e+16"
    assert _repr_c(_bits(1e17)) == "1e+17"
    assert _repr_c(_bits(1e-4)) == "0.0001"
    assert _repr_c(_bits(1e-5)) == "1e-05"
    assert _repr_c(_bits(5e-8)) == "5e-08"
    assert _repr_c(_bits(1e100)) == "1e+100"
    assert _repr_c(_bits(5e-324)) == "5e-324"
    assert _repr_c(_bits(100.0)) == "100.0"
    assert _repr_c(_bits(5.0)) == "5.0"
    patterns = []
    for exponent in range(-330, 320):
        for lead in ("1", "1.5", "5", "9.999999999999998"):
            try:
                value = float("%se%d" % (lead, exponent))
            except (ValueError, OverflowError):
                continue
            if value == 0.0 or value in (float("inf"), float("-inf")):
                continue
            patterns.append(_bits(value))
            patterns.append(_bits(-value))
    bad = _sweep(patterns)
    assert not bad, f"{len(bad)} diverge; first 5: {bad[:5]}"


@_needs_native
def test_deterministic_random_sweep() -> None:
    """Volume, for completeness — but note this class found the pre-rc403
    defect ZERO times in 3,000,000 draws. It is the weakest test in the file
    and is here only so the strong ones cannot be mistaken for the whole gate.
    """
    rng = random.Random(20260805)
    patterns = []
    for _ in range(200_000):
        bits = rng.getrandbits(64)
        if (bits >> 52) & 0x7FF == 0x7FF:
            bits &= ~(1 << 62)
        patterns.append(bits)
    bad = _sweep(patterns)
    assert not bad, f"{len(bad)} of {len(patterns)} diverge; first 5: {bad[:5]}"


# ──────────────────────────────────────────────────────────────────────
# json.dumps parity — repr(float) IS what json.dumps emits for a float.
# ──────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("value", [
    0.1, 0.2, 0.3, 1.0 / 3.0, 2.0 / 3.0, 1e16, 1e15, 2.0 ** -24,
    1.7976931348623157e308, 5e-324, -0.0, 100.0, 0.30000000000000004,
])
def test_matches_json_dumps_not_just_repr(value: float) -> None:
    """``json.dumps(x)`` for a float is ``repr(x)``; both must match the C."""
    got = _repr_c(_bits(value))
    assert got == repr(value)
    assert got == json.dumps(value)


@_needs_native
def test_non_finite_defers() -> None:
    """NaN / +-Inf return SRMECH_ERR_BAD_INPUT — the caller decides the
    spelling. The two callers decide DIFFERENTLY, on purpose: the MCP marshal
    emits CPython's ``NaN`` / ``Infinity`` / ``-Infinity`` (its contract is
    byte-identity with ``json.dumps``, whose default ``allow_nan=True`` produces
    exactly those), while ``srmech_json_write_ws`` DECLINES the whole write (it
    is paired with the strict-RFC-8259 ``srmech_json_parse`` behind a sha256 and
    must not emit a document its own parser refuses). See the rc403 CHANGELOG.
    """
    assert _repr_c(0x7FF0000000000000) is None          # +inf
    assert _repr_c(0xFFF0000000000000) is None          # -inf
    assert _repr_c(0x7FF8000000000000) is None          # nan
    assert _repr_c(0x7FF0000000000001) is None          # signalling nan
