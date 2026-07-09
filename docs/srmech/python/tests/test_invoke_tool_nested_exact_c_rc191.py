"""rc191 — the NESTED exact-ℚ carrier OPERAND marshal (the #796 LINCHPIN foundation).

The bignum-safe C reader that lowers the MCP nested-ℚ wire form of the §76 "telescope"
reducer operands (the exact-ℚ carriers ``Poly`` / ``BiPoly``) into arena-backed
``srmech_bigint`` coefficient arrays — extending the rc176 ``srmech_infer.c``
``inf_read_poly`` pattern ONE nesting level per carrier, in the REUSABLE form the rc192
``srmech_infer.c`` wiring calls to dispatch the deferred exact #796 infer rows
(sigma-definite / q / elliptic) for a bare-C host.

WHY NOT THE INVOKE_TOOL VTABLE (the rc191 scope finding). The §76 reducer C kernels need
MB–GB caller workspaces (``srmech_gosper`` ~9 MB, ``srmech_wz_verify`` ~32 MB,
``srmech_zeilberger`` ~470 MB), sized by ``srmech_infer_arena_bytes`` (~41 MB). The
``invoke_tool`` marshalling arena is ``srmech_invoke_tool_arena_bytes`` = ``256*params_len
+ 65536`` (~114 KB) and JPL Rule 3 forbids malloc — so a reducer thunk carving its ws from
the vtable arena ALWAYS overflows → always defers. The reducers already run in the
``srmech_infer.c`` path (which sizes the arena correctly); THAT is their home. And the
reducer MCP RESULTS serialise (``json.dumps default=repr``) to Python ``repr()`` STRINGS
carrying only metadata (``"Poly(degree=1, exact-rational)"``), not exact-ℚ structures. So
rc191 ships the OPERAND MARSHAL FOUNDATION; rc192 wires it into the infer DECISION path.

THE PARITY PROOF (the DoD). For each carrier + coefficient shape, the C round-trip
``carrier_marshal_roundtrip_c(kind, json)`` (parse → ``srmech_bigint`` arrays →
re-serialise canonical ``[num,den]`` JSON) is BYTE-for-byte the Python carrier's own
coefficient view ``json.dumps(canon(input), separators=(",", ":"))`` — INCLUDING a bignum
coefficient (a decimal string beyond int64), which the marshal transports exactly via
``srmech_bigint_from_dec`` (never the clamping ``strtoll``). A malformed operand → a
non-OK status (the caller runs the COMPLETE pure carrier coercer). numpy-free."""
from __future__ import annotations

import json

import pytest

from srmech.amsc import _native

_needs_native = pytest.mark.skipif(
    not _native.has_native_carrier_marshal(),
    reason="rc191 nested exact-ℚ carrier marshal C peer not loaded (pure / stale host)",
)


def _cc(c):
    """Canonicalise one wire coefficient to the ``[num, den]`` view the carrier
    holds: a bare int / a decimal string → ``[int, 1]``; a ``[num, den]`` pair →
    the two scalars (each int or decimal string). Verbatim (no reduction) — the
    marshal lands the operand exactly as the reducers consume it."""
    if isinstance(c, (list, tuple)):
        return [int(c[0]), int(c[1])]
    return [int(c), 1]


def _canon_poly(p):
    return [_cc(c) for c in p]


def _canon_bipoly(b):
    return [[_cc(c) for c in slot] for slot in b]


def _dumps(x) -> str:
    return json.dumps(x, separators=(",", ":"))


# ── Poly (1-level) round-trip cases — the gosper term-ratio operand shape ──────
_POLY_CASES = [
    [0, 1],                        # two bare-int coeffs  (t=k ratio numerator)
    [1],                           # the constant polynomial
    [],                            # the zero polynomial (empty coeff list)
    [1, 2, 1],                     # (k+1)^2
    [-1, 0, 3],                    # signed coeffs
    [[1, 2], [3, 1]],              # exact-rational coeffs  (1/2, 3/1)
    [[0, 1], [-5, 7]],             # signed rational coeff
    [3, [7, 2], -4],               # MIXED bare-int + [num,den] leaves
    # a BIGNUM coefficient (beyond int64) as a decimal STRING — the marshal
    # transports it exactly (srmech_bigint_from_dec), never the clamping strtoll.
    [["123456789012345678901234567890", 1]],
    [["-98765432109876543210987654321", "1000000000000000000000"]],
]

# ── BiPoly (2-level) round-trip cases — the zeilberger / wz bivariate ratios ───
_BIPOLY_CASES = [
    [[1, 1]],                          # a single k-slot Poly-in-n
    [[1, 1], [-1]],                    # r_n den of Σ_k C(n,k)=2^n : (n+1)-k
    [[0, 1], [-1]],                    # r_k num : n-k
    [[1], [1]],                        # r_k den : k+1
    [[], [[3, 2], 1]],                 # an EMPTY k-slot (zero Poly-in-n) + a rational
    [[1, 1], [1, 1]],                  # r_n num of Σ_k C(n,k)^2
    [[["10000000000000000000001", 1]]],  # a bignum coeff inside a BiPoly cell
]

# ── Scalar (EllRatio) round-trip cases — a single exact-ℚ coefficient ──────────
_SCALAR_CASES = [
    5,
    -7,
    [3, 4],
    [-22, 7],
    ["340282366920938463463374607431768211456", 1],  # 2^128, bignum
]


@_needs_native
@pytest.mark.parametrize("poly", _POLY_CASES)
def test_poly_roundtrip_native_equals_canonical(poly) -> None:
    """C Poly round-trip == the Python carrier's [num,den] coefficient view."""
    status, out = _native.carrier_marshal_roundtrip_c(
        _native.CARRIER_POLY, _dumps(poly).encode("utf-8"))
    assert status == 0, (poly, status)
    assert out.decode("utf-8") == _dumps(_canon_poly(poly)), poly


@_needs_native
@pytest.mark.parametrize("bipoly", _BIPOLY_CASES)
def test_bipoly_roundtrip_native_equals_canonical(bipoly) -> None:
    """C BiPoly round-trip (flat + klen re-emitted) == the Python k-ascending
    Poly-in-n coefficient view — the 'one nesting level up' foundation."""
    status, out = _native.carrier_marshal_roundtrip_c(
        _native.CARRIER_BIPOLY, _dumps(bipoly).encode("utf-8"))
    assert status == 0, (bipoly, status)
    assert out.decode("utf-8") == _dumps(_canon_bipoly(bipoly)), bipoly


@_needs_native
@pytest.mark.parametrize("scalar", _SCALAR_CASES)
def test_scalar_roundtrip_native_equals_canonical(scalar) -> None:
    """C scalar-coefficient round-trip == the [num,den] view (EllRatio scalar)."""
    status, out = _native.carrier_marshal_roundtrip_c(
        _native.CARRIER_SCALAR, _dumps(scalar).encode("utf-8"))
    assert status == 0, (scalar, status)
    assert out.decode("utf-8") == _dumps(_cc(scalar)), scalar


@_needs_native
def test_bignum_coefficient_not_clamped() -> None:
    """A coefficient beyond int64 rides the decimal-string transport EXACTLY —
    the marshal never routes it through the clamping strtoll (the reason the
    bignum wire form is a string, not a bare literal). The C round-trip returns
    the FULL value, digit-for-digit."""
    big = "123456789012345678901234567890123456789012345678901234567890"
    status, out = _native.carrier_marshal_roundtrip_c(
        _native.CARRIER_POLY, _dumps([[big, 1]]).encode("utf-8"))
    assert status == 0
    assert out.decode("utf-8") == f"[[{big},1]]"


# Malformed operands the marshal must DECLINE (non-OK status) → the pure carrier
# coercer is the complete fallback (rc103 inform-don't-limit; never a wrong read).
_MALFORMED = [
    (_native.CARRIER_POLY, 5),                  # a Poly must be an array
    (_native.CARRIER_POLY, [[1, 2, 3]]),        # a coeff pair must have arity 2
    (_native.CARRIER_POLY, [[1, "x"]]),         # a non-decimal string leaf
    (_native.CARRIER_POLY, [1.5]),              # a float coeff (not exact-ℚ)
    (_native.CARRIER_BIPOLY, [1, 2]),           # a BiPoly slot must be an array
    (_native.CARRIER_BIPOLY, [[[1, 2, 3]]]),    # a nested coeff bad arity
    (_native.CARRIER_SCALAR, [1, 2, 3]),        # a scalar pair must have arity 2
    (_native.CARRIER_SCALAR, "notanumber"),     # a non-decimal string scalar
]


@_needs_native
@pytest.mark.parametrize("kind,bad", _MALFORMED)
def test_malformed_declines_cleanly(kind, bad) -> None:
    """A malformed operand → a non-OK status + no output (defer to pure)."""
    status, out = _native.carrier_marshal_roundtrip_c(kind, _dumps(bad).encode("utf-8"))
    assert status != 0, (kind, bad)
    assert out is None, (kind, bad)


@_needs_native
def test_bad_kind_declines() -> None:
    """An out-of-range carrier kind → a non-OK status (BAD_INPUT)."""
    status, out = _native.carrier_marshal_roundtrip_c(99, _dumps([1, 2]).encode("utf-8"))
    assert status != 0
    assert out is None


@_needs_native
def test_reducer_operand_shapes_are_marshallable() -> None:
    """The exact operand shapes the deferred #796 infer rows feed their reducers
    (the rc192 readiness evidence): the sigma-definite (n,k) BiPoly term-ratios of
    Σ_k C(n,k)=2^n round-trip byte-identically — so a bare-C host CAN marshal them
    into the srmech_zeilberger / srmech_wz_verify operand arrays."""
    ratios = {
        "rn_num": [[1, 1]],
        "rn_den": [[1, 1], [-1]],
        "rk_num": [[0, 1], [-1]],
        "rk_den": [[1], [1]],
    }
    for name, bp in ratios.items():
        status, out = _native.carrier_marshal_roundtrip_c(
            _native.CARRIER_BIPOLY, _dumps(bp).encode("utf-8"))
        assert status == 0, name
        assert out.decode("utf-8") == _dumps(_canon_bipoly(bp)), name
