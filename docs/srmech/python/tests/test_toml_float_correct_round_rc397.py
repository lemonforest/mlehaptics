"""rc397 (`#T1066`) — srmech_toml's C float parse is CORRECTLY ROUNDED.

Before rc397 the C decimal→double parser accumulated ``mant*10 + d`` then divided
by ``10^fracdigits`` (two roundings) and applied the exponent by a per-step
multiply/divide loop (one rounding PER exponent step). Measured over a 3000-token
battery, 1941 tokens came out bit-different from Python's ``float(str)`` — up to
**24 ULP** off for large |exponent| — and ``5e-324`` and other denormals were
rejected outright by the old ``exp > 308`` guard. That is why ``toml_loads_c``
DECLINED every float-bearing document and rode the stdlib parser.

rc397 replaces the accumulator with a correctly-rounded, libm-free parse:

* **Clinger fast path** (Clinger, PLDI 1990) — when the significand is exactly
  representable (D ≤ 2^53) and the net exponent |E| ≤ 22, a SINGLE IEEE
  multiply/divide by an exact power of ten is provably correctly rounded.
* **Exact tail** — otherwise the correctly-rounded double of the exact rational
  D·10^E is computed over ``srmech_bigint`` (num/den, one big divmod,
  round-to-nearest-EVEN on the halfway tie), assembling the IEEE bit pattern
  directly so normals, denormals, underflow (→ ±0) and overflow (→ ±inf) all
  round exactly.

This test is the bit-exactness gate: for every battery + fuzz token the C parse
equals ``float(token)`` BIT-FOR-BIT (compared via ``struct.pack('<d', …)``, the
only comparison that distinguishes -0.0 from 0.0 and a 1-ULP miss from a hit).
``float`` / ``tomllib`` are IEEE correctly-rounded round-to-nearest-even, so this
IS the parity target.

The C-path assertions are native-guarded with ``require_native`` (the `#T843` /
`#T1004` contract): they SKIP pure-by-design in the no-native shard and FAIL if
the library is missing unexpectedly. numpy-free by construction (stdlib only).
"""

from __future__ import annotations

import random
import struct

import pytest

from srmech import _native, _toml
from tests._native_gate import require_native


def _c_float(tok: str):
    """The double srmech_toml's C parser yields for ``x = <tok>`` (native path)."""
    got = _native.toml_loads_c("x = " + tok)
    assert got is not None, (
        f"C parser DECLINED float token {tok!r} — since rc397 every float token "
        f"must self-host on the correctly-rounded native parse, not decline")
    return got["x"]


def _bits(x: float) -> bytes:
    """The 8 raw IEEE-754 bytes — the only bit-exact identity for a double
    (separates -0.0 from 0.0 and any 1-ULP miss from a hit)."""
    return struct.pack("<d", x)


#: The hand-picked battery: the classic hard cases (0.1/0.2/0.3), the IEEE
#: boundary values (min normal, min/next denormals, max normal), the exponent-
#: compounding cases the old loop got worst (1e-300), the exact-2^53 boundary,
#: and long / all-fraction significands.
_BATTERY = [
    "0.1", "0.2", "0.3", "3.141592653589793",
    "2.2250738585072014e-308",   # smallest normal
    "2.2250738585072009e-308",   # largest subnormal
    "5e-324",                    # smallest positive denormal
    "4.9406564584124654e-324",   # smallest denormal, full form
    "1.7976931348623157e308",    # largest finite (DBL_MAX)
    "1e-300", "9.999999999999999e22",
    "1234567890123456789.0",
    "0.00000000000000000001",    # 1e-20
    "1e-12", "6.022e23", "3.1415",
    "9007199254740992", "9007199254740993",   # 2^53 and 2^53+1
    "9007199254740993.0",
    "0.0", "-0.0", "100.0", "-0.1", "2.5", "0.5", "1234.5678",
    "1e22", "1e23", "1e-22", "1e-23",
    "123456789012345678901234567890e-15",
    "0.5000000000000001",
]


@pytest.mark.parametrize("tok", _BATTERY, ids=lambda t: t)
def test_battery_bit_exact(tok: str) -> None:
    """Every battery token: C parse == ``float(token)`` bit-for-bit."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), "stale lib: no srmech_toml_parse"
    py = float(tok)
    c = _c_float(tok)
    assert _bits(c) == _bits(py), (
        f"C float parse for {tok!r} is not bit-exact: C={c.hex()} "
        f"float()={py.hex()}")


def _fuzz_tokens(n: int, seed: int) -> list[str]:
    """A deterministic fuzz set (fixed seed = computational provenance): random
    significands (1–40 digits) crossed with exponents spanning the normal,
    denormal and out-of-range regimes.

    Every token is a WELL-FORMED TOML float — a decimal point with digits on
    both sides, and/or an ``e`` exponent — never a bare integer (a bare
    >int64 integer token is a legitimate int64-overflow decline, not a float
    parse, so it must not enter a float-fidelity battery)."""
    rng = random.Random(seed)
    out: list[str] = []
    while len(out) < n:
        d = rng.randint(1, 40)
        mant = "".join(rng.choice("0123456789") for _ in range(d))
        sign = "-" if rng.random() < 0.3 else ""
        e = rng.choice([
            rng.randint(-340, -300), rng.randint(-40, 40),
            rng.randint(300, 340), rng.randint(-400, 400),
        ])
        if len(mant) >= 2 and rng.random() < 0.5:
            pt = rng.randint(1, len(mant) - 1)          # digits on both sides
            core = mant[:pt] + "." + mant[pt:]
            tok = f"{sign}{core}" + (f"e{e}" if rng.random() < 0.5 else "")
        else:
            tok = f"{sign}{mant}e{e}"                    # int significand + exp
        try:
            float(tok)
        except ValueError:
            continue
        out.append(tok)
    return out


def test_fuzz_bit_exact() -> None:
    """3000 deterministic fuzz tokens, each C parse == ``float(token)`` bit-for-bit.

    Denormals, ties-to-even, 40-digit significands and out-of-range magnitudes
    are all in-distribution here — the regimes the old accumulator missed."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), "stale lib: no srmech_toml_parse"
    mismatches = []
    for tok in _fuzz_tokens(3000, seed=0xC0FFEE):
        py = float(tok)
        c = _c_float(tok)
        if _bits(c) != _bits(py):
            mismatches.append((tok, py.hex(), c.hex()))
    assert not mismatches, (
        f"{len(mismatches)} fuzz token(s) not bit-exact vs float(); first few: "
        f"{mismatches[:8]}")


def test_out_of_range_matches_python() -> None:
    """Overflow → ±inf, underflow → ±0.0 — bit-identical to ``float(token)``
    (and, verified separately, to tomllib, so no native-vs-pure divergence)."""
    require_native("srmech_toml_parse")
    for tok in ["1e400", "-1e400", "1e309", "1e-500", "-1e-500", "1e-330"]:
        assert _bits(_c_float(tok)) == _bits(float(tok)), (
            f"out-of-range token {tok!r}: C={_c_float(tok)!r} float()={float(tok)!r}")


def test_negative_zero_preserved() -> None:
    """-0.0 must stay -0.0 through the C parse (the sign bit is load-bearing and
    ``==`` would not catch its loss; only the raw bytes do)."""
    require_native("srmech_toml_parse")
    assert _bits(_c_float("-0.0")) == _bits(-0.0)
    assert _bits(_c_float("0.0")) == _bits(0.0)
    assert _bits(_c_float("-0.0")) != _bits(0.0)


def test_frontdoor_matches_float() -> None:
    """The internal front door (``_toml.loads``, native-first with a tomllib
    floor) also returns the correctly-rounded float bit-for-bit — the value a
    consumer actually receives."""
    require_native("srmech_toml_parse")
    for tok in _BATTERY:
        got = _toml.loads("x = " + tok)["x"]
        assert _bits(got) == _bits(float(tok)), (
            f"front-door float parse for {tok!r} not bit-exact: {got.hex()} vs "
            f"{float(tok).hex()}")
