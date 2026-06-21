"""Class N — rational-approximation primitive (Task #217 Phase C1).

Three operations:

- :func:`continued_fraction(p, q)` — simple continued-fraction expansion
  of ``p/q`` as a list of integer terms ``[a_0, a_1, a_2, ...]``.
- :func:`best_rational(p, q, max_denominator)` — best rational
  ``p'/q'`` with ``q' <= max_denominator`` approximating ``p/q`` via
  continued-fraction convergents.
- :func:`exp_series_truncate(num, den, num_terms)` — partial sum
  ``S_N(p/q) = Σ_{k=0..N} (p/q)^k / k!`` returned as an exact rational
  in lowest terms. Pure integer/rational arithmetic; the operational
  realisation of the asymptotic-rate framing from Spike #28 — no
  infinity invoked at any step, no floating-point at any step.

Class N is the third pure-integer primitive (after I — modular
arithmetic, J — prime factorisation / period). The first two
operations have uint64 inputs and a native C path via
``srmech_rational.c``. ``exp_series_truncate`` returns arbitrary-
precision ``int`` (factorial growth exceeds uint64 quickly); C parity
for a small-N case is a Phase C1 follow-on per
``[[feedback_no_binding_layer_carveout]]``.
"""

from __future__ import annotations

import ctypes
import struct
from typing import List, Tuple

from . import _native
from . import cyclic as _cyclic

__all__ = [
    "continued_fraction",
    "continued_fraction_convergents",
    "best_rational",
    "exp_series_truncate",
    "rational_add",
    "rational_mul",
    "rational_div",
    "rational_pow_uint",
    "sin_series_truncate",
    "cos_series_truncate",
    "log1p_series_truncate",
    "atan_series_truncate",
    "pi_cascade_digits",
    "cos",
    "sin",
    "tan",
    "atan",
    "atan2",
    "exp",
    "log",
    "cexp",
    "complex_exp",
    "sqrt",
    "hypot",
]

# Max terms a uint64 continued fraction can produce is Fibonacci-worst-
# case ~91 iterations; 128 is the C-side cap and a safe Python ceiling.
_MAX_TERMS: int = 128

# ── float classification + integer-sqrt without stdlib `math` (rc13 purge) ──
# `_is_finite` / `_is_inf` were the last float-classification calls in
# the cascade; they are pure IEEE-754 predicates, expressed here as plain
# comparisons (a `float("inf")` literal needs no maths library). `math.isqrt`
# was the last pure-integer primitive Python borrowed — replaced by a native
# two-limb dispatch (`srmech_isqrt`) + an arbitrary-precision integer-Newton.
_FLOAT_INF: float = float("inf")


def _is_finite(x: float) -> bool:
    """``_is_finite`` via comparison: finite iff not NaN and within ±∞."""
    return x == x and -_FLOAT_INF < x < _FLOAT_INF


def _is_inf(x: float) -> bool:
    """``_is_inf`` via comparison: ``x`` is ±∞."""
    return x == _FLOAT_INF or x == -_FLOAT_INF


def _py_isqrt(n: int) -> int:
    """Arbitrary-precision integer floor square root (no stdlib ``math.isqrt``).

    Newton's method on Python big-ints, seeded by the bit length — exact for
    every ``n >= 0`` and bignum-safe (the ``pi_cascade_digits`` D=1000 radicand
    is ~20000-bit). The native two-limb ``srmech_isqrt`` handles the bounded
    ``n < 2**128`` case; this is the unbounded fallback."""
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) >> 1)        # ~ceil(bits/2)-bit seed
    while True:
        y = (x + n // x) >> 1                    # integer Newton step
        if y >= x:
            return x
        x = y


def _ensure_uint64(name: str, value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int; got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative; got {value}")
    if value > 0xFFFF_FFFF_FFFF_FFFF:
        raise ValueError(f"{name} exceeds uint64 range; got {value}")
    return value


def continued_fraction(numerator: int, denominator: int) -> List[int]:
    """Return the simple continued-fraction expansion of ``p/q``.

    For ``p/q = [a_0; a_1, a_2, ...]``, returns ``[a_0, a_1, a_2, ...]``.
    Raises ``ValueError`` if ``denominator == 0``.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_rational_parity.py``.
    """
    p = _ensure_uint64("numerator", numerator)
    q = _ensure_uint64("denominator", denominator)
    if q == 0:
        raise ValueError("continued_fraction requires denominator > 0")
    if _native.HAS_NATIVE and _native.LIB is not None:
        terms = (ctypes.c_uint64 * _MAX_TERMS)()
        out_count = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_continued_fraction(
            ctypes.c_uint64(p),
            ctypes.c_uint64(q),
            terms,
            ctypes.c_uint32(_MAX_TERMS),
            ctypes.byref(out_count),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_continued_fraction returned non-OK status {rc}"
            )
        return [int(terms[i]) for i in range(out_count.value)]
    # Pure-Python fallback: Euclidean expansion.
    result: List[int] = []
    while q != 0:
        result.append(p // q)
        p, q = q, p % q
    return result


def best_rational(numerator: int,
                  denominator: int,
                  max_denominator: int) -> Tuple[int, int]:
    """Return the best rational ``(p', q')`` with ``q' <= max_denominator``
    approximating ``numerator / denominator``.

    Uses continued-fraction convergents (Stern-Brocot path through the
    mediant tree). Returns ``(0, 1)`` if no non-trivial convergent fits
    within ``max_denominator``. Raises ``ValueError`` for invalid inputs.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_rational_parity.py``.
    """
    p = _ensure_uint64("numerator", numerator)
    q = _ensure_uint64("denominator", denominator)
    max_q = _ensure_uint64("max_denominator", max_denominator)
    if q == 0:
        raise ValueError("best_rational requires denominator > 0")
    if max_q == 0:
        raise ValueError("best_rational requires max_denominator > 0")
    if _native.HAS_NATIVE and _native.LIB is not None:
        out_p = ctypes.c_uint64(0)
        out_q = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_best_rational(
            ctypes.c_uint64(p),
            ctypes.c_uint64(q),
            ctypes.c_uint64(max_q),
            ctypes.byref(out_p),
            ctypes.byref(out_q),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_best_rational returned non-OK status {rc}"
            )
        return int(out_p.value), int(out_q.value)
    # Pure-Python fallback: walk convergents.
    h_prev, h_curr = 1, 0
    k_prev, k_curr = 0, 1
    best_p, best_q = 0, 1
    while q != 0:
        a = p // q
        # Overflow guard mirrors the C path.
        if h_prev > 0 and a > (0xFFFF_FFFF_FFFF_FFFF - h_curr) // h_prev:
            break
        if k_prev > 0 and a > (0xFFFF_FFFF_FFFF_FFFF - k_curr) // k_prev:
            break
        h_next = a * h_prev + h_curr
        k_next = a * k_prev + k_curr
        if k_next > max_q:
            break
        best_p, best_q = h_next, k_next
        h_curr, h_prev = h_prev, h_next
        k_curr, k_prev = k_prev, k_next
        p, q = q, p % q
    return best_p, best_q


# Upper bound on N to prevent runaway integer-size growth. At N=512 the
# denominator is ~1170 decimal digits which is still tractable but past
# any practical asymptotic-rate-of-convergence use case; standard
# physical applications use N <= 50.
_EXP_SERIES_MAX_TERMS: int = 512


def exp_series_truncate(numerator: int,
                        denominator: int,
                        num_terms: int) -> Tuple[int, int]:
    """Return ``S_N(p/q) = sum_{k=0..N} (p/q)^k / k!`` as an exact rational.

    The partial sum is computed with pure integer/rational arithmetic
    (no floating-point at any step). Composes:

    * **Class N rational primitive**: numerator/denominator tracking.
    * **Class J integer factorial**: ``k!`` as running integer product.
    * **Class I integer arithmetic**: power accumulators ``p^k`` and ``q^k``.

    The result is returned in lowest terms (after a final ``gcd``
    reduction). Inputs may be negative.

    Operational content per Spike #28 §10 / §11 (PR #447) and
    ``[[user_stance_pi_as_projection]]``: the exp series classically
    framed as "requires N → infinity" is here parameterised by finite
    N with closed-form Lagrange-remainder upper bound on the residual.
    No infinity invoked at any step.

    Parameters
    ----------
    numerator : int
        Numerator of ``x`` as rational ``p/q``. May be negative.
    denominator : int
        Denominator of ``x``. Must be positive.
    num_terms : int
        Truncation parameter ``N``. ``S_N`` includes terms
        ``k = 0, 1, ..., N``. Must satisfy ``0 <= N <= 512``.

    Returns
    -------
    (out_num, out_den) : tuple[int, int]
        Reduced rational ``S_N(p/q) = out_num / out_den``. Always
        ``out_den > 0`` and ``gcd(|out_num|, out_den) == 1``.

    Raises
    ------
    TypeError
        If any argument is not ``int``.
    ValueError
        If ``denominator <= 0`` or ``num_terms`` out of range.

    Examples
    --------
    >>> exp_series_truncate(1, 1, 10)  # S_10(1)
    (9864101, 3628800)
    >>> exp_series_truncate(1, 2, 5)   # S_5(0.5)
    (6331, 3840)
    >>> # S_N(0) = 1/1 (first term only contributes)
    >>> exp_series_truncate(0, 1, 5)
    (1, 1)

    Notes
    -----
    Anchored to: srmech notebook §3.8.0a (Class K canonical),
    srmech notebook §3.8.1 (Class N canonical entry), Spike #28 §10
    (canonical chain-spec form), Spike #28 §11 (asymptotic-calculus
    catalog scope inventory).
    """
    if not isinstance(numerator, int):
        raise TypeError(
            f"numerator must be int; got {type(numerator).__name__}"
        )
    if not isinstance(denominator, int):
        raise TypeError(
            f"denominator must be int; got {type(denominator).__name__}"
        )
    if not isinstance(num_terms, int):
        raise TypeError(
            f"num_terms must be int; got {type(num_terms).__name__}"
        )
    if denominator <= 0:
        raise ValueError(
            f"denominator must be positive; got {denominator}"
        )
    if num_terms < 0:
        raise ValueError(
            f"num_terms must be non-negative; got {num_terms}"
        )
    if num_terms > _EXP_SERIES_MAX_TERMS:
        raise ValueError(
            f"num_terms exceeds _EXP_SERIES_MAX_TERMS={_EXP_SERIES_MAX_TERMS};"
            f" got {num_terms}"
        )

    # Try native C path first when inputs fit safe bounds (num_terms <= 20,
    # |numerator| fits int64, denominator fits uint64). Per
    # [[feedback_no_binding_layer_carveout]] the C surface for Class N's
    # exp_series_truncate exists as a real primitive; the Python wrapper
    # dispatches to it for catalog-row-shaped inputs and falls through to
    # the bignum path below for larger N.
    _SAFE_C_N: int = 20
    _INT64_MAX: int = (1 << 63) - 1
    _INT64_MIN: int = -(1 << 63)
    _UINT64_MAX: int = (1 << 64) - 1
    if (_native.HAS_NATIVE and _native.LIB is not None
            and 0 <= num_terms <= _SAFE_C_N
            and _INT64_MIN <= numerator <= _INT64_MAX
            and 0 < denominator <= _UINT64_MAX
            and hasattr(_native.LIB, "srmech_exp_series_truncate")):
        out_num_c = ctypes.c_int64(0)
        out_den_c = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_exp_series_truncate(
            ctypes.c_int64(numerator),
            ctypes.c_uint64(denominator),
            ctypes.c_uint32(num_terms),
            ctypes.byref(out_num_c),
            ctypes.byref(out_den_c),
        )
        if rc == _native.SRMECH_OK:
            return (int(out_num_c.value), int(out_den_c.value))
        # On overflow, fall through to bignum path. Other errors propagate.
        if rc != _native.SRMECH_ERR_OVERFLOW:
            raise RuntimeError(
                f"srmech_exp_series_truncate returned non-OK status {rc}"
            )

    # Bignum / pure-Python path. Arbitrary-precision int via Python builtin.
    # S_N = sum_{k=0..N} (p^k) / (q^k * k!)
    # Common-denominator accumulation: S_N = A_N / (q^N * N!)
    # where A_N = sum_{k=0..N} p^k * q^(N-k) * (N! / k!)
    # All integer; reduce to lowest terms at the end.
    sum_num = 0
    sum_den_pow = 1  # = q^N at end
    k_factorial = 1
    p_pow = 1  # = p^k
    q_pow_complement = 1  # = q^(N-k) for current term

    # Pre-compute q^N and N!
    q_to_N = denominator ** num_terms
    N_factorial = 1
    for k in range(1, num_terms + 1):
        N_factorial *= k

    # Accumulate the common-denominator sum:
    p_pow = 1  # p^0
    k_factorial = 1  # 0! = 1
    for k in range(num_terms + 1):
        # Term k contributes  p^k * q^(N-k) * (N!/k!)  to the numerator
        # of the common-denominator form.
        q_complement_exp = num_terms - k
        q_complement = denominator ** q_complement_exp
        n_over_k_factorial = N_factorial // k_factorial
        sum_num += p_pow * q_complement * n_over_k_factorial
        # Update accumulators for next k:
        p_pow *= numerator
        k_factorial *= (k + 1)

    sum_den = q_to_N * N_factorial

    # Reduce to lowest terms via the Class-I cyclic gcd (use srmech for math,
    # not stdlib math.gcd; uncapped → big-int safe at One-scale numerators):
    if sum_num == 0:
        return (0, 1)
    # Class-K magnitude as an EXPLICIT sign-branch, never an ALU abs()
    # (sum_den is already positive upstream).
    num_mag = sum_num if sum_num >= 0 else -sum_num
    g = _cyclic.gcd(num_mag, sum_den)
    out_num = sum_num // g
    out_den = sum_den // g
    # Ensure denominator is positive.
    if out_den < 0:
        out_num = -out_num
        out_den = -out_den
    return (out_num, out_den)


# ──────────────────────────────────────────────────────────────────────
# Class N rational arithmetic primitives (rc10).
#
# rational_add / rational_mul / rational_pow_uint compose the chain
# operators needed by `srmech.amsc.attested.cosmos_validation/` to
# express the Friedmann dark-fraction rational formula as a multi-step
# linear pipeline under Phase 2 v1 chain DSL.
#
# Each takes tuple inputs (p, q) and returns a reduced (p, q) tuple.
# Pure-Python bignum-capable for arbitrary inputs; C-standalone for
# inputs that fit u64 per `[[feedback_no_binding_layer_carveout]]`.
# ──────────────────────────────────────────────────────────────────────


def _reduce_rational(num: int, den: int) -> Tuple[int, int]:
    """Reduce (num, den) to lowest terms with positive denominator.

    The GCD rides the Class-I :func:`srmech.amsc.cyclic.gcd` (srmech-native, no
    stdlib ``math.gcd``) — now uncapped, so the ~100-digit ``One``-scale
    numerators reduce exactly (native serves its uint64 domain, big-int Euclid
    beyond)."""
    if den == 0:
        raise ZeroDivisionError("rational denominator is zero")
    if num == 0:
        return (0, 1)
    # Class-K magnitude via EXPLICIT sign-branches, never an ALU abs().
    num_mag = num if num >= 0 else -num
    den_mag = den if den >= 0 else -den
    g = _cyclic.gcd(num_mag, den_mag)
    num //= g
    den //= g
    if den < 0:
        num = -num
        den = -den
    return (num, den)


def _try_c_two_rationals(symbol: str,
                          a: Tuple[int, int],
                          b: Tuple[int, int]) -> Tuple[int, int] | None:
    """Try the C path for an add/mul-style op; return None on overflow.

    All four inputs must fit int64 (signed numerators) / uint64
    (denominators); the C function returns SRMECH_ERR_OVERFLOW for
    any intermediate that exceeds u64 range, in which case Python
    bignum takes over.
    """
    _INT64_MAX: int = (1 << 63) - 1
    _INT64_MIN: int = -(1 << 63)
    _UINT64_MAX: int = (1 << 64) - 1
    a_num, a_den = a
    b_num, b_den = b
    if not (_native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, symbol)
            and _INT64_MIN <= a_num <= _INT64_MAX
            and 0 < a_den <= _UINT64_MAX
            and _INT64_MIN <= b_num <= _INT64_MAX
            and 0 < b_den <= _UINT64_MAX):
        return None
    out_num_c = ctypes.c_int64(0)
    out_den_c = ctypes.c_uint64(0)
    rc = getattr(_native.LIB, symbol)(
        ctypes.c_int64(a_num),
        ctypes.c_uint64(a_den),
        ctypes.c_int64(b_num),
        ctypes.c_uint64(b_den),
        ctypes.byref(out_num_c),
        ctypes.byref(out_den_c),
    )
    if rc == _native.SRMECH_OK:
        return (int(out_num_c.value), int(out_den_c.value))
    if rc == _native.SRMECH_ERR_OVERFLOW:
        return None  # caller falls through to bignum path
    raise RuntimeError(f"{symbol} returned non-OK status {rc}")


def rational_add(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:
    """Add two rationals; return (num, den) reduced.

    a/b = (a_num, a_den), c/d = (b_num, b_den).
    Result = (a_num * b_den + b_num * a_den) / (a_den * b_den), reduced.

    Pure-Python bignum-capable. Native C path
    (`srmech_rational_add`) for inputs that fit u64; falls through to
    bignum on SRMECH_ERR_OVERFLOW.
    """
    if not (isinstance(a, (tuple, list)) and len(a) == 2):
        raise TypeError(f"a must be 2-tuple (num, den); got {a!r}")
    if not (isinstance(b, (tuple, list)) and len(b) == 2):
        raise TypeError(f"b must be 2-tuple (num, den); got {b!r}")
    a_num, a_den = int(a[0]), int(a[1])
    b_num, b_den = int(b[0]), int(b[1])
    if a_den <= 0 or b_den <= 0:
        raise ValueError("denominators must be positive")
    out = _try_c_two_rationals("srmech_rational_add", (a_num, a_den), (b_num, b_den))
    if out is not None:
        return out
    return _reduce_rational(a_num * b_den + b_num * a_den, a_den * b_den)


def rational_mul(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:
    """Multiply two rationals; return (num, den) reduced.

    (a_num/a_den) * (b_num/b_den) = (a_num * b_num) / (a_den * b_den).

    Pure-Python bignum-capable; C path (`srmech_rational_mul`) for
    u64-fit inputs.
    """
    if not (isinstance(a, (tuple, list)) and len(a) == 2):
        raise TypeError(f"a must be 2-tuple (num, den); got {a!r}")
    if not (isinstance(b, (tuple, list)) and len(b) == 2):
        raise TypeError(f"b must be 2-tuple (num, den); got {b!r}")
    a_num, a_den = int(a[0]), int(a[1])
    b_num, b_den = int(b[0]), int(b[1])
    if a_den <= 0 or b_den <= 0:
        raise ValueError("denominators must be positive")
    out = _try_c_two_rationals("srmech_rational_mul", (a_num, a_den), (b_num, b_den))
    if out is not None:
        return out
    return _reduce_rational(a_num * b_num, a_den * b_den)


def rational_div(a: Tuple[int, int], b: Tuple[int, int]) -> Tuple[int, int]:
    """Divide two rationals (a / b); return (num, den) reduced.

    (a_num/a_den) / (b_num/b_den) = (a_num * b_den) / (a_den * b_num).

    Pure-Python bignum-capable; C path (`srmech_rational_div`) for
    u64-fit inputs. Raises ZeroDivisionError if b_num == 0.
    """
    if not (isinstance(a, (tuple, list)) and len(a) == 2):
        raise TypeError(f"a must be 2-tuple (num, den); got {a!r}")
    if not (isinstance(b, (tuple, list)) and len(b) == 2):
        raise TypeError(f"b must be 2-tuple (num, den); got {b!r}")
    a_num, a_den = int(a[0]), int(a[1])
    b_num, b_den = int(b[0]), int(b[1])
    if a_den <= 0 or b_den <= 0:
        raise ValueError("denominators must be positive")
    if b_num == 0:
        raise ZeroDivisionError("rational divisor is zero")
    out = _try_c_two_rationals("srmech_rational_div", (a_num, a_den), (b_num, b_den))
    if out is not None:
        return out
    # Python bignum path: a/b = (a_num * b_den) / (a_den * b_num)
    num = a_num * b_den
    den = a_den * b_num
    # If divisor was negative we need to negate both to keep denom positive.
    if den < 0:
        num = -num
        den = -den
    return _reduce_rational(num, den)


def rational_pow_uint(base: Tuple[int, int], exp: int) -> Tuple[int, int]:
    """Raise rational (p, q) to non-negative integer exponent.

    (p/q)^n = p^n / q^n, reduced. exp must satisfy 0 <= exp <= 64
    (matches C surface's bounded loop; for larger exponents use the
    Python bignum path via direct exponentiation).

    Pure-Python bignum-capable; C path
    (`srmech_rational_pow_uint`) for u64-fit inputs + exp <= 64.
    """
    if not (isinstance(base, (tuple, list)) and len(base) == 2):
        raise TypeError(f"base must be 2-tuple (num, den); got {base!r}")
    if not isinstance(exp, int):
        raise TypeError(f"exp must be int; got {type(exp).__name__}")
    if exp < 0:
        raise ValueError(f"exp must be non-negative; got {exp}")
    p, q = int(base[0]), int(base[1])
    if q <= 0:
        raise ValueError("denominator must be positive")
    if exp == 0:
        return (1, 1)
    # Try C path for u64-fit inputs + bounded exp.
    _INT64_MAX: int = (1 << 63) - 1
    _INT64_MIN: int = -(1 << 63)
    _UINT64_MAX: int = (1 << 64) - 1
    if (_native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_rational_pow_uint")
            and _INT64_MIN <= p <= _INT64_MAX
            and 0 < q <= _UINT64_MAX
            and 0 <= exp <= 64):
        out_num_c = ctypes.c_int64(0)
        out_den_c = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_rational_pow_uint(
            ctypes.c_int64(p),
            ctypes.c_uint64(q),
            ctypes.c_uint32(exp),
            ctypes.byref(out_num_c),
            ctypes.byref(out_den_c),
        )
        if rc == _native.SRMECH_OK:
            return (int(out_num_c.value), int(out_den_c.value))
        if rc != _native.SRMECH_ERR_OVERFLOW:
            raise RuntimeError(
                f"srmech_rational_pow_uint returned non-OK status {rc}"
            )
    # Python bignum path
    return _reduce_rational(p ** exp, q ** exp)


# ──────────────────────────────────────────────────────────────────────
# Class N trig + log partial-sum primitives (rc11).
#
# Four Taylor-series-truncation ops following exp_series_truncate's
# common-denominator integer-accumulation pattern:
#
#   sin(x)    = Σ_{k=0..N} (-1)^k * x^(2k+1) / (2k+1)!
#   cos(x)    = Σ_{k=0..N} (-1)^k * x^(2k)   / (2k)!
#   log1p(x)  = Σ_{k=1..N} (-1)^(k+1) * x^k  / k         (|x| < 1 required)
#   atan(x)   = Σ_{k=0..N} (-1)^k * x^(2k+1) / (2k+1)   (|x| ≤ 1 typical)
#
# Each takes (x_num, x_den, num_terms) → (out_num, out_den) exact
# rational. Pure-Python bignum-capable; C-standalone for u64-fit
# inputs (Task #234 §11 inventory). Bounded num_terms per op to keep
# (2N+1)! within u64 in the C path.
# ──────────────────────────────────────────────────────────────────────


def _check_series_inputs(numerator: int,
                         denominator: int,
                         num_terms: int,
                         max_terms: int,
                         op_name: str) -> None:
    """Shared input validation for the trig/log series ops."""
    if not isinstance(numerator, int):
        raise TypeError(f"numerator must be int; got {type(numerator).__name__}")
    if not isinstance(denominator, int):
        raise TypeError(f"denominator must be int; got {type(denominator).__name__}")
    if not isinstance(num_terms, int):
        raise TypeError(f"num_terms must be int; got {type(num_terms).__name__}")
    if denominator <= 0:
        raise ValueError(f"denominator must be positive; got {denominator}")
    if num_terms < 0:
        raise ValueError(f"num_terms must be non-negative; got {num_terms}")
    if num_terms > max_terms:
        raise ValueError(
            f"{op_name}: num_terms exceeds max {max_terms}; got {num_terms}"
        )


_TRIG_SERIES_MAX_TERMS: int = 50
_LOG_SERIES_MAX_TERMS: int = 64


def sin_series_truncate(numerator: int,
                        denominator: int,
                        num_terms: int) -> Tuple[int, int]:
    """Compute sin(p/q) Taylor partial sum to N terms as exact rational.

    sin(x) = Σ_{k=0..N} (-1)^k * x^(2k+1) / (2k+1)!

    Convergence: globally convergent; convergence rate degrades for
    |x| > π so caller should reduce to [-π, π] for typical use.
    Pure-Python bignum-capable.

    Examples
    --------
    >>> sin_series_truncate(0, 1, 5)
    (0, 1)
    >>> sin_series_truncate(1, 1, 5)[0] / sin_series_truncate(1, 1, 5)[1]
    0.841471...
    """
    _check_series_inputs(numerator, denominator, num_terms,
                         _TRIG_SERIES_MAX_TERMS, "sin_series_truncate")
    if numerator == 0:
        return (0, 1)
    # Bignum path: accumulate Σ_{k=0..N} (-1)^k * p^(2k+1) / (q^(2k+1) * (2k+1)!)
    num = 0
    den = 1
    p, q = numerator, denominator
    for k in range(num_terms + 1):
        exp = 2 * k + 1
        factorial_kk1 = 1
        for j in range(1, exp + 1):
            factorial_kk1 *= j
        term_num = (p ** exp)
        term_den = (q ** exp) * factorial_kk1
        if k % 2 == 1:
            term_num = -term_num
        # num/den + term_num/term_den
        num = num * term_den + term_num * den
        den = den * term_den
        # Periodically reduce to keep numbers manageable
        if k % 4 == 3:
            num, den = _reduce_rational(num, den)
    return _reduce_rational(num, den)


def cos_series_truncate(numerator: int,
                        denominator: int,
                        num_terms: int) -> Tuple[int, int]:
    """Compute cos(p/q) Taylor partial sum to N terms as exact rational.

    cos(x) = Σ_{k=0..N} (-1)^k * x^(2k) / (2k)!
    """
    _check_series_inputs(numerator, denominator, num_terms,
                         _TRIG_SERIES_MAX_TERMS, "cos_series_truncate")
    if numerator == 0:
        return (1, 1)
    num = 0
    den = 1
    p, q = numerator, denominator
    for k in range(num_terms + 1):
        exp = 2 * k
        factorial_2k = 1
        for j in range(1, exp + 1):
            factorial_2k *= j
        term_num = (p ** exp)
        term_den = (q ** exp) * factorial_2k if exp > 0 else factorial_2k
        if k % 2 == 1:
            term_num = -term_num
        num = num * term_den + term_num * den
        den = den * term_den
        if k % 4 == 3:
            num, den = _reduce_rational(num, den)
    return _reduce_rational(num, den)


def log1p_series_truncate(numerator: int,
                          denominator: int,
                          num_terms: int) -> Tuple[int, int]:
    """Compute log(1 + p/q) Taylor partial sum to N terms as exact rational.

    log(1+x) = Σ_{k=1..N} (-1)^(k+1) * x^k / k

    Domain: -1 < p/q ≤ 1 — the Taylor radius of convergence (the boundary
    x = 1, log 2, converges conditionally; x = -1 is log(0) = -∞). Outside
    it the partial sum DIVERGES, so an out-of-domain argument (x > 1 or
    x ≤ -1) is refused with a Class-N domain ``ValueError`` rather than
    silently returning a divergent rational (W14 / RBS-LM bugfix wishlist;
    the §15.1/§18 Class-K contract-error pattern). This op stays
    EXACT-rational; there is no float-projection range-reduced log to defer
    to, so |x| ≥ 1 simply isn't in this series' domain.
    """
    _check_series_inputs(numerator, denominator, num_terms,
                         _LOG_SERIES_MAX_TERMS, "log1p_series_truncate")
    if numerator > denominator or numerator <= -denominator:
        raise ValueError(
            f"log1p_series_truncate: p/q must be in (-1, 1] (Taylor radius "
            f"of convergence; x = -1 is log(0) = -∞); got "
            f"{numerator}/{denominator}. The exact-rational series diverges "
            f"outside its radius and cannot range-reduce."
        )
    if numerator == 0 or num_terms == 0:
        return (0, 1)
    num = 0
    den = 1
    p, q = numerator, denominator
    for k in range(1, num_terms + 1):
        term_num = (p ** k)
        term_den = (q ** k) * k
        if (k + 1) % 2 == 1:  # k even → negative
            term_num = -term_num
        num = num * term_den + term_num * den
        den = den * term_den
        if k % 4 == 0:
            num, den = _reduce_rational(num, den)
    return _reduce_rational(num, den)


def atan_series_truncate(numerator: int,
                         denominator: int,
                         num_terms: int) -> Tuple[int, int]:
    """Compute atan(p/q) Taylor partial sum to N terms as exact rational.

    atan(x) = Σ_{k=0..N} (-1)^k * x^(2k+1) / (2k+1)

    Domain: |p/q| ≤ 1 — the Taylor radius of convergence (the boundary
    |x| = 1, e.g. atan(1) = π/4, still converges, conditionally). Outside
    it the partial sum DIVERGES — the term x^(2k+1)/(2k+1) grows without
    bound — so a |p/q| > 1 argument is refused with a Class-N domain
    ``ValueError`` rather than silently returning a divergent rational
    (W14 / RBS-LM bugfix wishlist; the §15.1/§18 Class-K contract-error
    pattern — refuse the out-of-domain input loudly). This op stays
    EXACT-rational, so it cannot range-reduce via ``atan(x) = π/2 −
    atan(1/x)`` (π is irrational); for a |x| > 1 argument use the
    range-reduced float projection :func:`atan` (band-reduced; any real x).
    """
    _check_series_inputs(numerator, denominator, num_terms,
                         _LOG_SERIES_MAX_TERMS, "atan_series_truncate")
    if numerator > denominator or numerator < -denominator:
        raise ValueError(
            f"atan_series_truncate: |p/q| must be ≤ 1 (Taylor radius of "
            f"convergence); got {numerator}/{denominator}. The exact-rational "
            f"series cannot range-reduce (π is irrational); for |x| > 1 use "
            f"the range-reduced float projection srmech.amsc.rational.atan(x)."
        )
    if numerator == 0:
        return (0, 1)
    num = 0
    den = 1
    p, q = numerator, denominator
    for k in range(num_terms + 1):
        exp = 2 * k + 1
        term_num = (p ** exp)
        term_den = (q ** exp) * exp
        if k % 2 == 1:
            term_num = -term_num
        num = num * term_den + term_num * den
        den = den * term_den
        if k % 4 == 3:
            num, den = _reduce_rational(num, den)
    return _reduce_rational(num, den)


# ──────────────────────────────────────────────────────────────────────
# Float-projection trig — substrate-native cos/sin/tan/atan/atan2.
#
# These are the Class-N replacements for ``math.cos`` / ``math.sin`` /
# ``np.cos`` / ``np.sin`` / ``math.atan2`` / ``np.arctan2``. The exact
# rational cascade IS the substrate-native computation; the returned
# float is only the observer-frame *projection* of that rational (the
# continuous number line is a projection per
# ``[[feedback_continuous_number_line_pedagogical_obstacle]]``). There is
# no ``math.cos`` / ``np.cos`` anywhere in the call graph.
#
# Pipeline (resolves the "trig that can replace numpy" gap — the bare
# series were always globally convergent; what was missing was the
# range-reduction wrapper that composes them with the π-cascade):
#   1. range-reduce the angle into ≈[-π, π] using a high-precision π
#      drawn from ``pi_cascade_digits`` (Archimedes hexagon-doubling) —
#      exact rational arithmetic;
#   2. anchor the reduced angle to a fixed-denominator Class-N rational;
#   3. cos/sin Taylor partial sum (``cos_series_truncate`` /
#      ``sin_series_truncate``);
#   4. project the exact rational to float.
# Range reduction is what keeps the globally-convergent series cheap for
# large arguments (e.g. DSP window angles ``2π·n/(N-1)``).
# ──────────────────────────────────────────────────────────────────────

# Digits of π used for range reduction (≈1e-50, far below the float
# projection floor). Cached once; the cascade reruns only if a caller
# asks for more digits than cached.
_PI_RATIONAL_DIGITS: int = 50
_PI_RATIONAL_CACHE: "Tuple[int, int] | None" = None

# Class-N anchor denominator + Taylor term count for the float
# projection. 10**15 anchors the reduced angle at the float64 precision
# floor (≈1e-15) so the projection matches libm to machine scale while
# keeping the reduced-angle bignums bounded; 24 cos/sin terms drive the
# |x|<=π series residual below 1e-16.
_TRIG_FLOAT_ANCHOR_DEN: int = 10 ** 15
_TRIG_FLOAT_TERMS: int = 24
_ATAN_FLOAT_TERMS: int = 40


def _pi_rational(digits: int = _PI_RATIONAL_DIGITS) -> Tuple[int, int]:
    """Return π as an exact rational ``(num, den)`` from the π-cascade.

    Uses :func:`pi_cascade_digits` (Archimedes hexagon-doubling; no
    ``math.pi``) and caches the default-precision value. ``den`` is
    ``10**digits``.
    """
    global _PI_RATIONAL_CACHE
    if _PI_RATIONAL_CACHE is not None and digits <= _PI_RATIONAL_DIGITS:
        return _PI_RATIONAL_CACHE
    decimal = pi_cascade_digits(digits)          # e.g. "3.1415926535..."
    int_part, _, frac_part = decimal.partition(".")
    num = int(int_part + frac_part) if frac_part else int(int_part)
    den = 10 ** len(frac_part) if frac_part else 1
    result = (num, den)
    if digits <= _PI_RATIONAL_DIGITS:
        _PI_RATIONAL_CACHE = result
    return result


def _principal_angle_anchor(x: float,
                            anchor_den: int = _TRIG_FLOAT_ANCHOR_DEN
                            ) -> Tuple[int, int]:
    """Range-reduce ``x`` (radians) into ≈[-π, π] and anchor it to a
    fixed-denominator Class-N rational ``(num, anchor_den)``.

    Exact float→rational (``float.as_integer_ratio``) minus an integer
    multiple of the cascade-derived 2π; the integer-turn selection is the
    only floating step and is exact for ``|x|`` well within float range.
    """
    assert anchor_den > 0, "anchor denominator must be positive"
    x = float(x)
    x_num, x_den = x.as_integer_ratio()
    pi_num, pi_den = _pi_rational()
    tau_num, tau_den = 2 * pi_num, pi_den         # 2π = tau_num / tau_den
    turns = round(x / (tau_num / tau_den))        # nearest integer turn
    # reduced = x - turns * 2π  (exact rational)
    red_num = x_num * tau_den - turns * tau_num * x_den
    red_den = x_den * tau_den
    # Project the reduced angle to float (in ≈[-π, π]) and anchor it.
    anchored_num = round((red_num / red_den) * anchor_den)
    return anchored_num, anchor_den


# ──────────────────────────────────────────────────────────────────────
# Q61 fixed-point trig cascade — the canonical float-projection, bit-exact
# with the native peer ``c/src/srmech_trig.c`` (srmech_{sin,cos,atan,atan2}).
#
# Ported line-for-line from the C. The Class-N Taylor series runs in Q61
# fixed-point (denominator 2**61 — a power-of-two Class-N rational); float
# appears ONLY at the final projection ``float(v) / float(2**61)`` (the same
# two-step int64→double cast the C does). Python's arbitrary-precision ints
# reproduce the C int64/uint64 arithmetic exactly — the ``& _Q61_MASK64``
# masks model C's uint64 wrap, ``_q61_cdiv`` models C's truncate-toward-zero
# integer ``/`` — so this pure-Python path is BIT-IDENTICAL to ``srmech_sin``
# et al. Dispatch to the native peer is therefore a transparent speedup, not
# a different answer (the C↔Python parity test asserts the equality).
#
# This Q61 cascade is the deterministic, C-reproducible float contract for
# ``sin``/``cos``/``tan``/``atan``/``atan2``. The exact-rational
# ``*_series_truncate`` (arbitrary-denominator bignum) stays the separate
# higher-precision REFERENCE surface (where the domain guards live).
# ──────────────────────────────────────────────────────────────────────
_Q61_FBITS = 61
_Q61_ONE = 1 << _Q61_FBITS                       # 1.0 in Q61
_Q61_MASK61 = _Q61_ONE - 1
_Q61_MASK64 = (1 << 64) - 1
_Q61_TWO_OVER_PI_Q64 = 11743562013128004906      # round((2/pi) * 2**64)
_Q61_HALF_PI_Q61 = 3622009729038561421           # round((pi/2) * 2**61)
_Q61_SIN_TERMS = 10                              # |r|<=pi/4: r^21/21! < 2^-62
_Q61_ATAN_TERMS = 40                            # |m|<=sqrt2-1 fast band
# atan band edges tan(pi/8)=√2−1, cot(pi/8)=√2+1 (SELECTION thresholds only —
# they never enter the result; they keep every atan series argument at
# |m| <= √2−1 ≈ 0.414 so the alternating series reaches full precision).
_TAN_PI_8: float = 0.41421356237309515           # √2 − 1
_COT_PI_8: float = 2.414213562373095             # √2 + 1
_Q61_TAN_PI8 = _TAN_PI_8
_Q61_COT_PI8 = _COT_PI_8


def _q61_cdiv(a: int, b: int) -> int:
    """C integer division — truncate toward zero (Python ``//`` floors).

    The magnitudes are taken via the explicit **Class-K** sign-branch (never
    ``abs()`` of the value — `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`),
    the sign re-applied as **Class C**; mirrors ``trig_fxmul``'s C branch.
    """
    assert b != 0, "division by zero in Q61 cascade"
    ua = a if a >= 0 else -a                        # Class-K magnitude
    ub = b if b >= 0 else -b
    q = ua // ub
    return -q if (a < 0) != (b < 0) else q          # Class-C re-orientation


def _q61_fxmul(a: int, b: int) -> int:
    """Q61 signed fixed-point multiply ``(a/2^61)*(b/2^61) -> r/2^61``.

    Mirrors ``trig_fxmul``: the magnitude product is **Class K** (the explicit
    sign-branch, never ``abs()`` of the value), the sign re-application
    **Class C**. ``(|a|·|b|) >> 61`` is the exact product>>61.
    """
    neg = (a < 0) != (b < 0)
    ua = a if a >= 0 else -a                        # Class-K magnitude
    ub = b if b >= 0 else -b
    mag = (ua * ub) >> _Q61_FBITS
    return -mag if neg else mag                     # Class-C re-orientation


def _q61_reduce(x: float):
    """Integer cyclic octant reduction (mirror ``trig_reduce``).

    Returns ``(ok, octant, r_q61)`` with ``|r| <= pi/4`` in Q61. PURE
    INTEGER except the IEEE-754 bit-read of ``x``; the octant count comes
    from an integer wide-multiply by a Q64 ``2/pi``. ``ok`` is False for
    Inf/NaN or ``|x| >= 2**55`` (the two-word product loses octant bits).
    """
    bits = struct.unpack("<Q", struct.pack("<d", float(x)))[0]
    sign = bits >> 63
    raw = (bits >> 52) & 0x7FF
    frac = bits & ((1 << 52) - 1)
    if raw == 0x7FF:
        return (False, 0, 0)                      # Inf / NaN
    if raw == 0 and frac == 0:
        return (True, 0, 0)
    mant = frac if raw == 0 else (frac | (1 << 52))
    e = -1074 if raw == 0 else raw - 1075         # x = ± mant * 2**e
    if e >= 3:
        return (False, 0, 0)                      # |x| >= 2**55
    prod = mant * _Q61_TWO_OVER_PI_Q64
    phi = prod >> 64
    plo = prod & _Q61_MASK64
    s = 3 - e                                     # >= 1: right shift to Q61
    if s >= 128:
        return (True, 0, 0)
    if s >= 64:
        vhi = 0
        vlo = phi >> (s - 64)
    else:
        vhi = phi >> s
        vlo = ((plo >> s) | ((phi << (64 - s)) & _Q61_MASK64)) & _Q61_MASK64
    q = ((vhi << 3) | (vlo >> _Q61_FBITS)) & _Q61_MASK64   # floor(V / 2^61)
    vlo61 = vlo & _Q61_MASK61
    if vlo61 >= (1 << (_Q61_FBITS - 1)):          # round half up
        k = (q + 1) & _Q61_MASK64
        fr = vlo61 - _Q61_ONE
    else:
        k = q
        fr = vlo61
    if sign:
        fr = -fr
        k = (-k) & _Q61_MASK64                    # negate mod 2**64
    octant = k & 3
    r_q61 = _q61_fxmul(fr, _Q61_HALF_PI_Q61)      # r = frac * (pi/2)
    return (True, octant, r_q61)


def _q61_sin_core(r: int) -> int:
    """``sin(r)`` for ``|r| <= pi/4``, Q61 → Q61 (mirror ``trig_sin_core``)."""
    r2 = _q61_fxmul(r, r)
    term = r
    s = r
    for k in range(1, _Q61_SIN_TERMS + 1):
        term = _q61_fxmul(term, r2)
        term = _q61_cdiv(term, (2 * k) * (2 * k + 1))
        s = s - term if (k & 1) else s + term
    return s


def _q61_cos_core(r: int) -> int:
    """``cos(r)`` for ``|r| <= pi/4``, Q61 → Q61 (mirror ``trig_cos_core``)."""
    r2 = _q61_fxmul(r, r)
    term = _Q61_ONE
    s = _Q61_ONE
    for k in range(1, _Q61_SIN_TERMS + 1):
        term = _q61_fxmul(term, r2)
        term = _q61_cdiv(term, (2 * k - 1) * (2 * k))
        s = s - term if (k & 1) else s + term
    return s


def _q61_atan_core(m: int) -> int:
    """``atan(m)`` for ``0 <= m <= √2−1``, Q61 → Q61 (mirror ``trig_atan_core``)."""
    m2 = _q61_fxmul(m, m)
    term = m
    s = m
    for k in range(1, _Q61_ATAN_TERMS + 1):
        term = _q61_fxmul(term, m2)
        contrib = _q61_cdiv(term, 2 * k + 1)
        s = s - contrib if (k & 1) else s + contrib
    return s


def _q61_to_double(q61: int) -> float:
    """Project Q61 → float: ``float(v) / float(2**61)`` (matches the C
    two-step ``(double)q61 / (double)SRMECH_TRIG_ONE`` cast exactly).

    This is the OLD display-boundary collapse. As of 0.9.0rc7 the public
    transcendentals stay rational (:class:`~srmech.amsc.q.Q`) and only collapse
    when the caller asks (``float(q)``); this helper is retained for the
    internal float-reduction arithmetic (Cody-Waite ``r``, atan band edges)
    where a transient double is legitimate, never as the public return.
    """
    return float(q61) / float(_Q61_ONE)


# ── stay-rational Q factory + recombination constants (0.9.0rc7) ──────────
# F868 stay-rational ([[feedback_stay_rational_collapse_only_at_display]]):
# the transcendentals compute an EXACT Q61 rational (the int64 cascade value
# over 2**61, or a clean power-of-two-scaled form for exp/sqrt) and the OLD
# code threw ~9 bits away into a float at ``_q61_to_double``. The public
# ``sin``/``cos``/``tan``/``atan``/``atan2``/``exp``/``log``/``sqrt``/``hypot``
# now return that exact rational as a ``Q``; ``float(q)`` reproduces (and
# slightly betters) the old float. ``Q`` is imported lazily to break the
# ``q.py`` ↔ ``rational.py`` import cycle (q imports rational at load).
_Q_CLS = None


def _q(num: int, den: int):
    """Build a :class:`~srmech.amsc.q.Q` from an exact ``(num, den)`` integer
    pair (deferred import — ``q`` imports this module). The Q reducer rides the
    Class-N Euclidean GCD, so power-of-two denominators stay powers of two."""
    global _Q_CLS
    if _Q_CLS is None:
        from .q import Q as _Q_imported
        _Q_CLS = _Q_imported
    return _Q_CLS(num, den)


# ln(2) in Q61 (denominator 2**61), DERIVED from the Class-N log1p cascade
# (no math.log): ln2 = −log1p(−1/2) (|−1/2|<1 → fast), quantised to Q61. The
# e·ln2 recombine in ``log`` stays in this Q61 model (matching ``pi/2`` =
# ``_Q61_HALF_PI_Q61``), so ``log`` returns a clean ``Q(v, 2**61)``.
_Q61_LN2 = 1598288580650331957                   # round(ln2 * 2**61)


def _atan_nonneg_q61(m: float) -> int:
    """``atan(m)`` for ``m >= 0`` as a Q61 INTEGER (the stay-rational peer of
    :func:`_q61_atan_nonneg`): the three-band reduction accumulates in Q61
    ints (``pi/2`` = ``_Q61_HALF_PI_Q61``, ``pi/4`` = that ``// 2``), so the
    result is exact over ``2**61``. The band edges + ``1/m`` / ``(m−1)/(m+1)``
    fold the float argument (inherent — the input is a float); the SERIES and
    the recombine are integer."""
    assert m >= 0.0, "atan magnitude must be non-negative (Class-K)"
    if m <= _Q61_TAN_PI8:
        mq = int(m * float(_Q61_ONE) + 0.5)
        return _q61_atan_core(mq)
    if m >= _Q61_COT_PI8:                          # atan(m) = pi/2 − atan(1/m)
        mq = int((1.0 / m) * float(_Q61_ONE) + 0.5)
        return _Q61_HALF_PI_Q61 - _q61_atan_core(mq)
    u = (m - 1.0) / (m + 1.0)                       # middle band: pi/4 + atan(u)
    neg = u < 0.0
    um = -u if neg else u
    a = _q61_atan_core(int(um * float(_Q61_ONE) + 0.5))
    return (_Q61_HALF_PI_Q61 // 2) + (-a if neg else a)


def _q61_atan_nonneg(m: float) -> float:
    """``atan(m)`` for ``m >= 0`` via the three-band reduction (mirror
    ``trig_atan_nonneg``); the band keeps every series argument ≤ √2−1."""
    half_pi = _q61_to_double(_Q61_HALF_PI_Q61)
    if m <= _Q61_TAN_PI8:
        mq = int(m * float(_Q61_ONE) + 0.5)
        return _q61_to_double(_q61_atan_core(mq))
    if m >= _Q61_COT_PI8:                          # atan(m) = pi/2 - atan(1/m)
        inv = 1.0 / m
        mq = int(inv * float(_Q61_ONE) + 0.5)
        return half_pi - _q61_to_double(_q61_atan_core(mq))
    u = (m - 1.0) / (m + 1.0)                      # middle band: pi/4 + atan(u)
    neg = u < 0.0
    um = -u if neg else u
    mq = int(um * float(_Q61_ONE) + 0.5)
    a = _q61_to_double(_q61_atan_core(mq))
    return half_pi / 2.0 + (-a if neg else a)


def cos(x: float, *, terms: int = _TRIG_FLOAT_TERMS) -> "Q":
    """``cos(x)`` (radians) → an EXACT :class:`~srmech.amsc.q.Q` (Q61 rational).

    0.9.0rc7 stay-rational (F868): the Class-N Q61 cascade computes the exact
    rational ``v / 2**61``; this returns that ``Q`` instead of collapsing to a
    float — ``float(cos(x))`` reproduces (and slightly betters) the old float.
    Substrate-native replacement for ``math.cos`` / ``np.cos`` — no ``math.cos``
    in the call graph. Non-finite ``x`` raises (``Q`` is the finite-rational
    carrier). ``terms`` is retained for back-compat (fixed Q61 cap). The
    arbitrary-precision exact reference surface is ``cos_series_truncate``.
    """
    x = float(x)
    if not _is_finite(x):
        raise ValueError("cos: x must be finite (Q is the finite-rational carrier)")
    if _native.has_native_trans_q61():          # 0.9.0rc7: native Q61, byte-exact
        return _q(_native.cos_q61_c(x), _Q61_ONE)
    ok, octant, r = _q61_reduce(x)
    if not ok:
        raise ValueError(f"cos: |x| too large for the Q61 octant reduction; got {x}")
    sc = _q61_sin_core(r)
    cc = _q61_cos_core(r)
    v = cc if octant == 0 else -sc if octant == 1 else -cc if octant == 2 else sc
    return _q(v, _Q61_ONE)


def sin(x: float, *, terms: int = _TRIG_FLOAT_TERMS) -> "Q":
    """``sin(x)`` (radians) → an EXACT :class:`~srmech.amsc.q.Q` (Q61 rational).

    Stay-rational peer of :func:`cos` (the exact Q61 ``v / 2**61``).
    Substrate-native replacement for ``math.sin`` / ``np.sin``.
    """
    x = float(x)
    if not _is_finite(x):
        raise ValueError("sin: x must be finite (Q is the finite-rational carrier)")
    if _native.has_native_trans_q61():          # 0.9.0rc7: native Q61, byte-exact
        return _q(_native.sin_q61_c(x), _Q61_ONE)
    ok, octant, r = _q61_reduce(x)
    if not ok:
        raise ValueError(f"sin: |x| too large for the Q61 octant reduction; got {x}")
    sc = _q61_sin_core(r)
    cc = _q61_cos_core(r)
    v = sc if octant == 0 else cc if octant == 1 else -sc if octant == 2 else -cc
    return _q(v, _Q61_ONE)


def tan(x: float, *, terms: int = _TRIG_FLOAT_TERMS) -> "Q":
    """``tan(x) = sin(x) / cos(x)`` → an EXACT :class:`~srmech.amsc.q.Q`.

    The exact ``Q`` quotient of the Q61 ``sin`` / ``cos`` (no native
    ``srmech_tan``). Raises where ``cos(x) == 0``."""
    c = cos(x)
    if c == 0:
        raise ValueError("tan undefined: cos(x) == 0")
    return sin(x) / c                              # exact Q / Q


def atan(x: float, *, terms: int = _ATAN_FLOAT_TERMS) -> "Q":
    """``atan(x)`` → an EXACT :class:`~srmech.amsc.q.Q` via the Q61 three-band
    Class-N cascade.

    Class-K magnitude (never ``abs()`` of the value) + Class-C re-orientation;
    the three-band reduction keeps every series argument fast. ``atan(±Inf)`` =
    ``±π/2`` is a representable rational, returned as ``Q(±pi/2_q61, 2**61)``;
    NaN raises. Substrate-native replacement for ``math.atan`` / ``np.arctan``.
    """
    x = float(x)
    if x != x:                                     # NaN
        raise ValueError("atan: x is NaN (not a rational)")
    if _native.has_native_trans_q61():          # native handles ±Inf via the COT band
        return _q(_native.atan_q61_c(x), _Q61_ONE)
    if _is_inf(x):                              # atan(±Inf) = ±π/2 (exact Q)
        v = _Q61_HALF_PI_Q61 if x > 0.0 else -_Q61_HALF_PI_Q61
        return _q(v, _Q61_ONE)
    xm = x if x >= 0.0 else -x                     # Class-K magnitude
    v = _atan_nonneg_q61(xm)
    return _q(v if x >= 0.0 else -v, _Q61_ONE)     # Class-C re-orientation


def atan2(y: float, x: float, *, terms: int = _ATAN_FLOAT_TERMS) -> "Q":
    """``atan2(y, x)`` → an EXACT :class:`~srmech.amsc.q.Q` via the Q61 atan
    cascade with quadrant logic.

    The quadrant limits (``±π/2``, ``±π/4``, ``±3π/4``, ``±π``, ``±0``) are all
    representable rationals — returned as exact ``Q`` over ``2**61`` — so the
    ``±Inf`` argument cases stay rational; only a NaN argument raises.
    Substrate-native replacement for ``math.atan2`` / ``np.arctan2``.
    """
    y = float(y)
    x = float(x)
    if y != y or x != x:                           # any NaN → not a rational
        raise ValueError("atan2: y or x is NaN (not a rational)")
    hp = _Q61_HALF_PI_Q61                          # pi/2 in Q61
    if not (_is_finite(y) and _is_finite(x)):
        if _is_inf(y) and _is_inf(x):        # both ±Inf → ±π/4 or ±3π/4
            mag = hp // 2 if x > 0.0 else 3 * (hp // 2)
            return _q(mag if y >= 0.0 else -mag, _Q61_ONE)
        if _is_inf(y):                          # |y|=Inf, x finite → ±π/2
            return _q(hp if y >= 0.0 else -hp, _Q61_ONE)
        if x > 0.0:                                # x=+Inf, y finite → ±0
            return _q(0, 1)
        return _q(2 * hp if y >= 0.0 else -2 * hp, _Q61_ONE)   # x=−Inf → ±π
    if x == 0.0:
        return _q(hp if y > 0.0 else (-hp if y < 0.0 else 0), _Q61_ONE)
    base = atan(y / x)                             # exact Q
    if x > 0.0:
        return base
    pi = _q(2 * hp, _Q61_ONE)                       # x<0 quadrant shift (Class C)
    return base + pi if y >= 0.0 else base - pi


# Default Taylor terms for the exact-rational (bignum REFERENCE) exp surface.
_EXP_FLOAT_TERMS: int = 24


# ──────────────────────────────────────────────────────────────────────
# Q61 fixed-point exp/log/sqrt cascade — the canonical float-projection,
# bit-exact with the native peers ``c/src/srmech_explog.c`` (srmech_{exp,log})
# and ``c/src/srmech_sqrt.c`` (srmech_rational_sqrt). Ported line-for-line; the
# Q61 series machinery (``_q61_fxmul`` / ``_q61_cdiv`` / ``_q61_to_double``) is
# the same as the trig block above. exp/log are NOT cyclic, so the reduction
# differs from trig:
#   - exp: x = n·ln2 + r, |r| <= ln2/2 (Cody-Waite two-word LN2_HI+LN2_LO
#     split keeps r to machine-eps; the 2^n recombine is built straight into
#     the IEEE exponent field, no ldexp). This REPLACES the old halving-and-
#     square reduction, which amplified error to ~345 ULP; the Cody-Waite
#     reduction holds ~1 ULP and is what the C + notebook §exp specify.
#   - log: x = m·2^e read EXACTLY from the bit pattern, m folded into
#     [1/√2, √2); log(m) = 2·atanh((m−1)/(m+1)) is the Q61 series; e·ln2
#     recombine uses the same two-word ln2.  (rational.log is NEW this rc —
#     the notebook listed it as srmech_log's Python peer but it was missing.)
#   - sqrt: x = M·2^e from the bit pattern, e made even; root = isqrt(M<<2K)
#     (``math.isqrt`` == the C two-limb integer isqrt), projected by 2^(e/2−K).
# float appears ONLY at the final projection. The exact-rational bignum
# surfaces (``exp_series_truncate`` / ``log1p_series_truncate`` / the
# ``precision_bits`` sqrt path) remain the separate higher-precision REFERENCE.
# ──────────────────────────────────────────────────────────────────────
_EXPLOG_INV_LN2 = 1.4426950408889634074
_EXPLOG_LN2_HI = 6.93147180369123816490e-01      # two-word ln2 (fdlibm split)
_EXPLOG_LN2_LO = 1.90821492927058770002e-10
_EXPLOG_SQRT2 = 1.4142135623730951               # band edge (selection only)
_EXPLOG_EXP_TERMS = 18                            # |r|<=ln2/2: r^19/19! < 2^-62
_EXPLOG_LOG_TERMS = 13                            # |t|<=√2-edge: t^27/27 < 2^-62
_EXPLOG_OVERFLOW = 709.782712893384              # ln(DBL_MAX)
_EXPLOG_UNDERFLOW = -745.2                        # ln(smallest subnormal)
_SQRT_C_K = 27                                    # root precision bits (C peer)


def _q_pow2(p: int) -> float:
    """``2**p`` as a double, built directly from the IEEE-754 exponent field
    (exact, no ``ldexp``). ``p`` must keep the biased exponent in [1, 2046]."""
    assert -1023 < p < 1024, "pow2 exponent out of normal range"
    bits = (((p + 1023) & 0x7FF) << 52) & _Q61_MASK64
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


def _q_scale2(m: float, n: int) -> float:
    """``m * 2**n``, splitting ``n`` so neither power-of-two leaves the normal
    range (mirror ``explog_scale2``). ``n//2`` is C truncate-toward-zero."""
    nh = n // 2 if n >= 0 else -((-n) // 2)        # C trunc-toward-zero
    nl = n - nh
    return m * _q_pow2(nh) * _q_pow2(nl)


def _q_exp_core(r: int) -> int:
    """``exp(r)`` for ``|r| <= ln2/2``, Q61 → Q61 (mirror ``explog_exp_core``)."""
    term = _Q61_ONE
    s = _Q61_ONE
    for k in range(1, _EXPLOG_EXP_TERMS + 1):
        term = _q61_fxmul(term, r)
        term = _q61_cdiv(term, k)
        s += term
    return s


def _q_log_core(t: int) -> int:
    """``2·atanh(t)`` for ``|t| <= √2-edge``, Q61 → Q61 (mirror ``explog_log_core``).

    This IS ``log(m)`` for ``m = (1+t)/(1-t)``; the caller forms ``t = (m−1)/(m+1)``.
    """
    t2 = _q61_fxmul(t, t)
    term = t
    s = t
    for k in range(1, _EXPLOG_LOG_TERMS + 1):
        term = _q61_fxmul(term, t2)
        s += _q61_cdiv(term, 2 * k + 1)
    return s * 2


def exp(x: float, *, terms: int = _EXP_FLOAT_TERMS) -> "Q":
    """``e^x`` → an EXACT :class:`~srmech.amsc.q.Q` via the Q61 Class-N exp
    cascade with Cody-Waite ln2 reduction.

    ``x = n·ln2 + r`` with ``|r| <= ln2/2``; ``exp(r)`` is the Q61 integer
    Taylor ``1 + r + r²/2! + …`` (an exact ``Q(core, 2**61)``) and the ``2^n``
    scale is an EXACT power of two folded into the rational — so the result is
    the exact rational ``core·2^n / 2**61``, never a float-collapsed ``2^n``
    recombine. 0.9.0rc7 stay-rational: there is no ``DBL_MAX`` overflow gate
    (that was a float artefact) — a finite ``x`` gives the exact (possibly
    large) rational; only non-finite ``x`` raises. Substrate-native replacement
    for ``math.exp`` / ``np.exp`` (real). ``terms`` selects the arbitrary-
    precision REFERENCE surface ``exp_series_truncate``.
    """
    x = float(x)
    if not _is_finite(x):
        raise ValueError("exp: x must be finite (Q is the finite-rational carrier)")
    if _native.has_native_trans_q61():          # 0.9.0rc7: native Q61, byte-exact
        core, n = _native.exp_q61_c(x)
        return _q(core << n, _Q61_ONE) if n >= 0 else _q(core, _Q61_ONE << (-n))
    tn = x * _EXPLOG_INV_LN2
    n = int(tn + (0.5 if tn >= 0.0 else -0.5))     # round half away from zero
    r = (x - n * _EXPLOG_LN2_HI) - n * _EXPLOG_LN2_LO
    rq = int(r * float(_Q61_ONE) + (0.5 if r >= 0.0 else -0.5))
    core = _q_exp_core(rq)                          # exp(r) as Q61 int (≈[0.7,1.4])
    if n >= 0:                                      # exact 2^n scale (no float)
        return _q(core << n, _Q61_ONE)
    return _q(core, _Q61_ONE << (-n))


def log(x: float, *, terms: int = _EXPLOG_LOG_TERMS) -> "Q":
    """``ln(x)`` (natural log, x > 0) → an EXACT :class:`~srmech.amsc.q.Q` via
    the Q61 Class-N atanh cascade.

    ``x = m·2^e`` read EXACTLY from the bit pattern, ``m`` folded into
    ``[1/√2, √2)``; ``log(m) = 2·atanh((m−1)/(m+1))`` is the Q61 series and the
    ``e·ln2`` recombine stays in the Q61 model (``_Q61_LN2``, cascade-derived),
    so the result is the exact ``Q((logm + e·ln2_q61), 2**61)`` — no two-word
    float recombine. Substrate-native replacement for ``math.log`` / ``np.log``
    (real). Domain: ``x <= 0`` raises (``log 0 = −∞``, ``log(<0)`` undefined —
    neither is a rational); non-finite raises. The arbitrary-precision REFERENCE
    surface is ``log1p_series_truncate``.
    """
    x = float(x)
    if not _is_finite(x):
        raise ValueError("log: x must be finite (Q is the finite-rational carrier)")
    if x <= 0.0:
        raise ValueError(f"log domain: x must be > 0 (log 0 = −∞ is not rational); got {x}")
    if _native.has_native_trans_q61():          # 0.9.0rc7: native Q61, byte-exact
        logm, e = _native.log_q61_c(x)
        return _q(logm + e * _Q61_LN2, _Q61_ONE)
    bits = struct.unpack("<Q", struct.pack("<d", x))[0]
    raw = (bits >> 52) & 0x7FF
    frac = bits & ((1 << 52) - 1)
    if raw == 0:                                   # subnormal — normalise
        f = frac
        sh = 0
        while sh < 53 and (f & (1 << 52)) == 0:
            f <<= 1
            sh += 1
        mant = f
        e = -1022 - sh
    else:
        mant = frac | (1 << 52)
        e = raw - 1023
    m = mant / (1 << 52)                           # m in [1, 2)
    if m >= _EXPLOG_SQRT2:                         # fold to [1/√2, √2)
        m *= 0.5
        e += 1
    tt = (m - 1.0) / (m + 1.0)
    tq = int(tt * float(_Q61_ONE) + (0.5 if tt >= 0.0 else -0.5))
    logm = _q_log_core(tq)                          # log(m) as Q61 int
    return _q(logm + e * _Q61_LN2, _Q61_ONE)        # + e·ln2, exact in Q61


def cexp(theta: float, *, terms: int = _TRIG_FLOAT_TERMS) -> complex:
    """``e^(i·theta) = cos(theta) + i·sin(theta)`` via the Class-N cascade.

    Euler's formula: Class-N trig ∘ Class-C imaginary-unit rotation (the
    imaginary unit *is* a 90° phase-plane rotation). Substrate-native
    replacement for ``np.exp`` / ``cmath.exp`` of ``1j*theta`` — the
    DFT twiddle factor and the quantum time-evolution phase.
    """
    return complex(cos(theta, terms=terms), sin(theta, terms=terms))


def complex_exp(z: complex, *, terms: int = _TRIG_FLOAT_TERMS) -> complex:
    """``e^z`` for complex ``z`` via the Class-N cascade.

    ``e^z = e^(z.real)·(cos(z.imag) + i·sin(z.imag))`` — Class-N exp +
    trig, composed by a Class-C imaginary-unit rotation. Substrate-native
    replacement for ``np.exp`` / ``cmath.exp`` on a complex argument.
    """
    z = complex(z)
    er = exp(z.real)                                # Q — stay in the integer ALU
    # e^z = e^Re·(cos Im + i sin Im). The ``er * cos`` / ``er * sin`` are exact
    # Q·Q products (ALU); the float/FPU appears ONLY at the ``complex()`` last
    # rotate (this IS the display boundary for the complex result).
    return complex(er * cos(z.imag, terms=terms), er * sin(z.imag, terms=terms))


# Scaled-integer precision for the bignum REFERENCE sqrt (bits below the
# radix point; 64 → relative error well under the float64 floor). Pass
# ``precision_bits=`` explicitly to select this higher-precision reference;
# the default float sqrt is the bit-exact-with-C K=27 cascade below.
_SQRT_PRECISION_BITS: int = 64


#: Default fractional bits for the √ of an EXACT rational (Q input / hypot's
#: exact sum-of-squares): 54 — double the float64 mantissa, so the rational
#: root carries more than the float floor. The float-input path keeps K=27
#: (the native C-parity baseline) for the IEEE-bit decomposition.
_SQRT_Q_K: int = 54


def _sqrt_rational(num: int, den: int, k: int):
    """``√(num/den)`` as an EXACT ``Q(root, 2**k)`` (integer ``isqrt`` of the
    ``2^{2k}``-scaled radicand). ``num, den >= 0``; ``den > 0``."""
    assert num >= 0 and den > 0, "sqrt of a non-negative rational only"
    root = _integer_sqrt((num << (2 * k)) // den)   # floor(√(num/den) · 2^k)
    return _q(root, 1 << k)


def sqrt(x, *, precision_bits: int = None) -> "Q":
    """``√x`` (x ≥ 0) → an EXACT :class:`~srmech.amsc.q.Q` via the Class-N
    rational sqrt cascade.

    ``x`` may be a ``float`` OR a :class:`~srmech.amsc.q.Q` (rc7 — stays
    rational through :func:`hypot` and the complex modulus). Default
    (``precision_bits=None``): the IEEE-bit ``M·2^e`` decomposition with
    ``root = isqrt(M << 2K)`` (K=27) scaled by the EXACT ``2^(e/2−K)`` — the
    result is the exact ``Q(root, 2^k)`` (``float`` of it betters the old
    ``float(root)·2^…`` which pre-rounded ``root``). **Class N** rational ∘
    **Class K** sqrt-convergence. A ``Q`` input is rooted at ``_SQRT_Q_K`` bits
    (exact rational radicand). Negative ``x`` raises (Class-K pin-slot at zero).

    ``precision_bits=N`` selects the higher-precision path (the exact rational
    rooted at ``N`` fractional bits), e.g. for the π-cascade.
    """
    # Q-input: root the exact rational directly (stay-rational; e.g. hypot).
    if hasattr(x, "as_pair") and not isinstance(x, float):
        xn, xd = x.as_pair()
        if xn < 0:
            raise ValueError(f"sqrt domain error: x must be >= 0; got {x}")
        if xn == 0:
            return _q(0, 1)
        return _sqrt_rational(xn, xd, precision_bits or _SQRT_Q_K)
    x = float(x)
    if x < 0.0:                                   # Class-K pin-slot at zero
        raise ValueError(f"sqrt domain error: x must be >= 0; got {x}")
    if not _is_finite(x):
        raise ValueError("sqrt: x must be finite (Q is the finite-rational carrier)")
    if x == 0.0:
        return _q(0, 1)
    if precision_bits is not None:                # exact rational at N frac bits
        xn, xd = x.as_integer_ratio()
        return _sqrt_rational(xn, xd, precision_bits)
    if _native.has_native_trans_q61():          # 0.9.0rc7: native Q61, byte-exact
        root, p = _native.sqrt_q61_c(x)
        return _q(root << p, 1) if p >= 0 else _q(root, 1 << (-p))
    bits = struct.unpack("<Q", struct.pack("<d", x))[0]
    raw = (bits >> 52) & 0x7FF
    frac = bits & ((1 << 52) - 1)
    mant = frac if raw == 0 else (frac | (1 << 52))
    e = -1074 if raw == 0 else raw - 1075         # x = mant · 2^e
    if e & 1:                                      # make e even
        mant <<= 1
        e -= 1
    root = _integer_sqrt(mant << (2 * _SQRT_C_K))   # 128-bit; native srmech_isqrt
    p = e // 2 - _SQRT_C_K                          # exact power-of-two scale
    return _q(root << p, 1) if p >= 0 else _q(root, 1 << (-p))


def hypot(a: float, b: float, *, precision_bits: int = None) -> "Q":
    """``hypot(a, b) = √(a² + b²)`` → an EXACT :class:`~srmech.amsc.q.Q`.

    **Class M** (the sum-of-squares bind) ∘ **Class N∘K** (:func:`sqrt`). rc7
    stay-rational: ``a² + b²`` is formed as an EXACT rational (each float's
    ``as_integer_ratio`` squared and added — no float ``a*a`` rounding) and
    ``√`` of that exact rational is returned as ``Q``. Substrate-native
    replacement for ``math.hypot`` / ``np.hypot`` (the complex modulus
    ``|z| = hypot(z.real, z.imag)``). ``a``/``b`` may be ``float`` or ``Q``.
    """
    an, ad = (a.as_pair() if hasattr(a, "as_pair") and not isinstance(a, float)
              else float(a).as_integer_ratio())
    bn, bd = (b.as_pair() if hasattr(b, "as_pair") and not isinstance(b, float)
              else float(b).as_integer_ratio())
    num = an * an * bd * bd + bn * bn * ad * ad    # (a²+b²) exact numerator
    den = ad * ad * bd * bd
    return _sqrt_rational(num, den, precision_bits or _SQRT_Q_K)


# ──────────────────────────────────────────────────────────────────────
# Class N π geometric-cascade primitives (Milestone #4 / Task #245).
#
# Two pi-emergent primitives operationalising
# ``[[user_stance_pi_spectral_shape_scalar_invariant]]`` and Spike #32
# (PR #460 confirmed across 3 substrates):
#
#   * continued_fraction_convergents(coef_list)
#     — Standard CF recurrence: given canonical π CF coefficients
#       [3; 7, 15, 1, 292, 1, ...], emits convergent ladder
#       (3,1), (22,7), (333,106), (355,113), (103993,33102), ...
#       (Hardy & Wright *Theory of Numbers* 4th ed. §10, Khinchin
#       *Continued Fractions* §10).
#
#   * pi_cascade_digits(num_digits)
#     — Archimedes hexagon-doubling cascade with rational-bounded √
#       via integer Newton-Raphson on scaled bignum (precision_bits
#       at 512 by default). Produces decimal digits of π without
#       invoking math.pi anywhere in the call graph. AST-verified
#       discipline gate enforced by tests/test_pi_cascade_primitives.py.
#
# These earn a C surface (continued_fraction_convergents) for int64-fit
# convergent ladders + bignum-Python fallback for the long ladder; the
# cascade decimal-digits op stays Python-only by scope (bignum native
# from the cascade step onwards — Python int handles it cleanly).
# ──────────────────────────────────────────────────────────────────────


# 30 canonical convergents is well beyond any practical request and
# matches the C-side cap to avoid runaway integer growth.
_CF_CONVERGENTS_MAX_COEFS: int = 256


def continued_fraction_convergents(
        coef_list: List[int]) -> List[Tuple[int, int]]:
    """Produce the convergent ladder for a continued-fraction expansion.

    Given coefficients ``[a_0; a_1, a_2, ..., a_n]`` (the simple
    continued fraction of some real), returns the list of convergents
    ``[(h_0, k_0), (h_1, k_1), ..., (h_n, k_n)]`` produced by the
    standard recurrence:

        h_{-1} = 1, h_0 = a_0,   h_k = a_k * h_{k-1} + h_{k-2}
        k_{-1} = 0, k_0 = 1,     k_k = a_k * k_{k-1} + k_{k-2}

    Pure integer arithmetic. Python's arbitrary-precision int handles
    convergent ladders well beyond int64 (the canonical π ladder
    crosses int64 at depth ~17 with terms like 1146408/364913); no
    overflow concerns at any depth.

    The convergent property (Hardy & Wright Thm 154): every convergent
    h_k / k_k is the BEST rational approximation to the limit value
    with denominator ≤ k_k. The classical π convergents drop out
    when ``coef_list`` is the canonical π CF
    ``[3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, ...]``:

    >>> continued_fraction_convergents([3, 7, 15, 1, 292])
    [(3, 1), (22, 7), (333, 106), (355, 113), (103993, 33102)]

    Native C path (``srmech_cf_convergents_int64``) handles the
    int64-fit prefix and returns ``SRMECH_ERR_OVERFLOW`` once any
    convergent exceeds int64; the wrapper transparently falls
    through to the bignum-Python path.

    Anchored to ``[[user_stance_pi_spectral_shape_scalar_invariant]]``
    (the convergent ladder IS π at the substrate-level identity); Spike
    #32 (PR #460) confirmed substrate-invariance across triangle /
    square / hexagon cascades.

    Parameters
    ----------
    coef_list : list[int]
        Continued-fraction coefficients ``[a_0, a_1, a_2, ...]``.
        Must be non-empty. ``a_0`` may be negative; remaining
        coefficients must be positive (simple CF convention).

    Returns
    -------
    list[tuple[int, int]]
        Convergent ladder ``[(h_0, k_0), (h_1, k_1), ...]``, one
        entry per input coefficient.

    Raises
    ------
    TypeError
        If ``coef_list`` is not a list or contains non-int entries.
    ValueError
        If ``coef_list`` is empty or exceeds the implementation cap
        (``_CF_CONVERGENTS_MAX_COEFS``).
    """
    if not isinstance(coef_list, list):
        raise TypeError(
            f"coef_list must be list[int]; got {type(coef_list).__name__}"
        )
    assert coef_list is not None, "coef_list must not be None"
    assert all(isinstance(c, int) for c in coef_list), (
        "every coef_list entry must be int"
    )
    if len(coef_list) == 0:
        raise ValueError("coef_list must be non-empty")
    if len(coef_list) > _CF_CONVERGENTS_MAX_COEFS:
        raise ValueError(
            f"coef_list length {len(coef_list)} exceeds cap "
            f"{_CF_CONVERGENTS_MAX_COEFS}"
        )
    for i, c in enumerate(coef_list):
        if not isinstance(c, int):
            raise TypeError(
                f"coef_list[{i}] must be int; got {type(c).__name__}"
            )
        if i > 0 and c <= 0:
            raise ValueError(
                f"coef_list[{i}] = {c}; simple CF requires a_k > 0 for k > 0"
            )

    # Try native C path first when inputs fit safe bounds (every
    # coefficient fits int64 and the cap is well-bounded). The C
    # implementation falls back via SRMECH_ERR_OVERFLOW the moment
    # any convergent exceeds int64.
    _INT64_MAX: int = (1 << 63) - 1
    _INT64_MIN: int = -(1 << 63)
    if (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_cf_convergents_int64")
            and all(_INT64_MIN <= c <= _INT64_MAX for c in coef_list)):
        n = len(coef_list)
        coefs_arr = (ctypes.c_int64 * n)(*coef_list)
        nums_arr = (ctypes.c_int64 * n)()
        dens_arr = (ctypes.c_int64 * n)()
        rc = _native.LIB.srmech_cf_convergents_int64(
            coefs_arr,
            ctypes.c_size_t(n),
            nums_arr,
            dens_arr,
        )
        if rc == _native.SRMECH_OK:
            return [(int(nums_arr[i]), int(dens_arr[i])) for i in range(n)]
        if rc != _native.SRMECH_ERR_OVERFLOW:
            raise RuntimeError(
                f"srmech_cf_convergents_int64 returned non-OK status {rc}"
            )
        # else fall through to bignum path

    # Bignum-Python path. Standard CF recurrence; pure integer.
    convergents: List[Tuple[int, int]] = []
    h_prev: int = 1
    h_curr: int = 0  # h_{-2}, h_{-1} in the conventional indexing
    k_prev: int = 0
    k_curr: int = 1
    for a in coef_list:
        h_next = a * h_prev + h_curr
        k_next = a * k_prev + k_curr
        convergents.append((h_next, k_next))
        # Shift: (h_{k-2}, h_{k-1}) := (h_{k-1}, h_k)
        h_curr, h_prev = h_prev, h_next
        k_curr, k_prev = k_prev, k_next
    return convergents


# Cap on cascade depth — each cascade doubling adds ~0.6 decimal digits
# (log10(4)/log10(10) ≈ 0.602). The fixed-precision-integer cascade
# carries a single bignum at scale M = 2^precision_bits, so increasing
# depth costs O(depth · precision_bits) bits total — tractable.
#
# rc13 raises the depth cap from 90 to 2000 to accommodate num_digits up
# to 1000 (depth 1800 covers >1000 decimal-digit accuracy with safety
# margin per `_pi_cascade_auto_params`). The bound is still finite and
# JPL-clean (fixed loop bound).
_PI_CASCADE_MAX_DEPTH: int = 2000

# Cap on requested digit count. rc13 raises from 50 to 1000 per the
# benchmark note's engineering finding (PR #468) — the cascade scales
# linearly in depth + precision; rc12's cap was the validated regime
# bound, not a mathematical bound. With math.isqrt's asymptotically-
# optimal sqrt and depth/precision auto-scaling, 1000 digits is
# reachable in single-digit seconds.
_PI_CASCADE_MAX_DIGITS: int = 1000

# Maximum precision_bits caller may pass. Raised from 8192 (rc12) to
# 32768 (rc13) to cover the auto-scaled precision needed at
# num_digits=1000 (~10240 bits) with substantial headroom.
_PI_CASCADE_MAX_PRECISION_BITS: int = 32768


def _pi_cascade_auto_params(num_digits: int) -> Tuple[int, int]:
    """Compute auto-scaled (max_cascade_depth, precision_bits) for a
    given num_digits request.

    Linear scaling derived from the rc12 validated point (num_digits=50
    at depth=90, precision_bits=512) per the benchmark note in
    ``docs/srmech/notes/pi_cascade_digits_benchmark_2026-05-17.md``:

      depth          = max(90,  ceil(num_digits * 90  / 50))
      precision_bits = max(512, ceil(num_digits * 512 / 50))

    The 90/50 = 1.8 cascade-doublings-per-digit ratio leaves an ~8%
    safety margin over the theoretical log10(4)⁻¹ ≈ 1.66 minimum.
    The 512/50 = 10.24 precision-bits-per-digit ratio leaves ~3x
    headroom over the theoretical log2(10) ≈ 3.32 minimum.

    Caller-overridable: explicit ``max_cascade_depth`` /
    ``precision_bits`` kwargs to ``pi_cascade_digits`` skip this helper
    entirely.

    Parameters
    ----------
    num_digits : int
        Number of decimal digits requested. Must be in [0, 1000].

    Returns
    -------
    (depth, precision_bits) : tuple[int, int]
        Auto-scaled cascade parameters. Both quantities scale linearly
        with num_digits; minimum values are rc12's validated defaults.
    """
    assert isinstance(num_digits, int), "num_digits must be int"
    assert num_digits >= 0, f"num_digits must be non-negative; got {num_digits}"
    # Round-up division for ceil(a*90/50) etc. — pure integer.
    depth = max(90, (num_digits * 90 + 49) // 50)
    precision_bits = max(512, (num_digits * 512 + 49) // 50)
    return (depth, precision_bits)


def _integer_sqrt(n: int) -> int:
    """Integer floor square root — substrate-native (rc13: the stdlib
    ``math.isqrt`` is GONE; this IS the srmech integer-isqrt).

    Dispatches the native two-limb ``srmech_isqrt`` for a bounded radicand
    (``n < 2**128`` — the hot ``rational.sqrt`` / hypercomplex-twiddle case)
    and an arbitrary-precision integer-Newton (``_py_isqrt``) for the
    unbounded ``pi_cascade_digits`` scale (D=1000 → ~20000-bit radicand).
    Neither path touches a maths library; pure integer arithmetic throughout
    (no floats, no ``math.pi``), so the substrate-invariance discipline per
    ``[[user_stance_pi_spectral_shape_scalar_invariant]]`` is preserved.
    """
    assert isinstance(n, int), "_integer_sqrt requires int"
    assert n >= 0, f"_integer_sqrt requires non-negative input; got {n}"
    if n < (1 << 128) and _native.has_native_isqrt():
        return _native.isqrt128_c(n)
    return _py_isqrt(n)


def _rational_sqrt_midpoint(
        num: int,
        den: int,
        precision_bits: int) -> Tuple[int, int]:
    """Compute a rational mid-bound approximation of √(num/den) at given precision.

    Returns (p, q) with q = den * 2^precision_bits, where p is the
    rounded integer square root of the scaled bignum (truncated-floor
    plus 1/2 correction), so |p/q - √(num/den)| ≤ 1/(2q) approximately.

    Pure integer Newton-Raphson on scaled bignum; no floats; no math.pi.
    Used by ``pi_cascade_digits`` to avoid the one-sided error
    accumulation that lower-bound truncation produces over many
    cascade steps.
    """
    assert isinstance(num, int) and isinstance(den, int), "rational sqrt needs int inputs"
    assert num >= 0, f"rational_sqrt requires non-negative numerator; got {num}"
    assert den > 0, f"rational_sqrt requires positive denominator; got {den}"
    if num == 0:
        return (0, 1)
    M = 1 << precision_bits
    # √(num/den) = √(num*den) / den. Scale by M for precision; round-
    # to-nearest by computing both s = floor(√(scaled)) and adjusting
    # if (s+1)^2 - scaled < scaled - s^2 (i.e. (s+1) is closer).
    scaled = num * den * M * M
    s_lo = _integer_sqrt(scaled)
    s_hi = s_lo + 1
    # Round to nearest: pick s_hi if its square is closer to `scaled`
    # than s_lo's square. Pure integer comparison.
    if (s_hi * s_hi - scaled) < (scaled - s_lo * s_lo):
        s = s_hi
    else:
        s = s_lo
    return (s, den * M)


def pi_cascade_digits(num_digits: int,
                      *,
                      max_cascade_depth: int | None = None,
                      precision_bits: int | None = None) -> str:
    """Stream decimal digits of π via Archimedes hexagon-doubling cascade.

    Computes the decimal-digit expansion of π to ``num_digits`` digits
    after the decimal point. No invocation of ``math.pi`` (or any
    transcendental library function) anywhere in the call graph — the
    cascade uses only:

    * Pure integer arithmetic for half-perimeter accumulation
    * Rational-bounded √ via integer-floor square root (``math.isqrt``)
    * Integer long-division for decimal-digit extraction

    Algorithm (Archimedes, c. 250 BCE):

    Start with a regular hexagon inscribed in a unit circle. The
    hexagon has 6 sides each of length 1 (so s² = 1 exactly). At each
    cascade step, double the number of sides via the half-angle
    identity:

        s²_{2n} = 2 − √(4 − s²_n)

    The half-perimeter of the inscribed n-gon is (n/2) · s_n, which
    converges to π as n → ∞. After ``max_cascade_depth`` doublings,
    the rational half-perimeter (computed in lower-bound form using
    rational-bounded √) is converted to a decimal string by integer
    long division.

    Per ``[[user_stance_pi_spectral_shape_scalar_invariant]]``: the
    scalar decimal expansion 3.14159... is a downstream readout of
    the substrate-level CF-convergent ladder. Spike #32 (PR #460)
    confirmed cascade emergence across hexagon / square / triangle
    substrates with AST-verified zero math.pi invocations.

    Per ``[[user_stance_pi_as_projection]]``: π is generated by a
    cascade-substrate operation (integer-cyclic doubling on a
    polygon's vertex count); the scalar value is the projection
    artifact under continuous-length metric. No math.pi required
    to compute the decimal expansion.

    Auto-scaling (rc13)
    -------------------
    When ``max_cascade_depth`` / ``precision_bits`` are left as
    ``None`` (the default), they are computed automatically from
    ``num_digits`` via ``_pi_cascade_auto_params`` using the linear
    scaling validated by Task #248:

      depth          = max(90,  ceil(num_digits * 90  / 50))
      precision_bits = max(512, ceil(num_digits * 512 / 50))

    Callers may override either kwarg explicitly to study cascade
    convergence at non-canonical parameter combinations.

    Parameters
    ----------
    num_digits : int
        Number of decimal digits to emit after the decimal point.
        Must satisfy ``0 <= num_digits <= 1000`` (rc13 cap; rc12 was 50).
    max_cascade_depth : int or None, keyword-only
        Cascade doubling depth. ``None`` (default) → auto-scaled from
        ``num_digits`` per ``_pi_cascade_auto_params``. Explicit value
        must be in [1, 2000].
    precision_bits : int or None, keyword-only
        Bit precision for the scaled-integer √ operation. ``None``
        (default) → auto-scaled from ``num_digits``. Explicit value
        must be in [64, 32768].

    Returns
    -------
    str
        Decimal expansion as a string ``"3.141592653589793..."`` —
        always starts with ``"3."`` then ``num_digits`` digits.

    Examples
    --------
    >>> pi_cascade_digits(15)
    '3.141592653589793'
    >>> pi_cascade_digits(0)
    '3.'
    >>> pi_cascade_digits(5)
    '3.14159'

    Raises
    ------
    TypeError
        If ``num_digits`` is not int.
    ValueError
        If ``num_digits`` is negative or exceeds the practical cap.

    Notes
    -----
    AST-verified zero ``math.pi`` invocations per
    ``[[user_stance_pi_spectral_shape_scalar_invariant]]`` — pinned
    by ``tests/test_pi_cascade_primitives.py``.

    The function imports ``math`` for ``math.gcd`` (rational reduction)
    and ``math.isqrt`` (integer square root) only; ``math.pi`` and
    ``math.tau`` are never accessed. The AST gate test walks this
    function's source tree and asserts no ``Attribute(math, pi)`` or
    ``Attribute(math, tau)`` nodes.
    """
    if not isinstance(num_digits, int):
        raise TypeError(
            f"num_digits must be int; got {type(num_digits).__name__}"
        )
    assert num_digits is not None, "num_digits must not be None"
    if num_digits < 0:
        raise ValueError(f"num_digits must be non-negative; got {num_digits}")
    if num_digits > _PI_CASCADE_MAX_DIGITS:
        raise ValueError(
            f"num_digits exceeds practical cap "
            f"{_PI_CASCADE_MAX_DIGITS}; got {num_digits}"
        )
    # Auto-scale either kwarg when caller passes None.
    auto_depth, auto_precision_bits = _pi_cascade_auto_params(num_digits)
    if max_cascade_depth is None:
        max_cascade_depth = auto_depth
    if precision_bits is None:
        precision_bits = auto_precision_bits
    assert isinstance(max_cascade_depth, int), (
        "max_cascade_depth must be int"
    )
    assert isinstance(precision_bits, int), "precision_bits must be int"
    if max_cascade_depth < 1 or max_cascade_depth > _PI_CASCADE_MAX_DEPTH:
        raise ValueError(
            f"max_cascade_depth must be in [1, {_PI_CASCADE_MAX_DEPTH}]; "
            f"got {max_cascade_depth}"
        )
    if (precision_bits < 64
            or precision_bits > _PI_CASCADE_MAX_PRECISION_BITS):
        raise ValueError(
            f"precision_bits must be in [64, "
            f"{_PI_CASCADE_MAX_PRECISION_BITS}]; got {precision_bits}"
        )

    # Special case: zero digits → "3." (the integer part of π).
    if num_digits == 0:
        return "3."

    # Fixed-precision-integer Archimedes cascade. We carry one
    # canonical scale factor M = 2^precision_bits throughout: every
    # quantity is an integer that, divided by the appropriate power
    # of M, gives the underlying rational. This avoids the rational-
    # arithmetic bit-length explosion that occurs when carrying full
    # (num, den) pairs through the cascade.
    #
    # Convention:
    #   s_sq    represents s²        with scaling factor M  (s² · M)
    # i.e. s_sq = round(true_s_squared * M).
    #
    # Initial hexagon: s²_6 = 1, so s_sq = M exactly.
    M: int = 1 << precision_bits
    s_sq: int = M  # = 1 * M, exact
    n: int = 6

    # Cascade doubling: s²_{2n} = 2 − √(4 − s²_n).
    # In scaled-integer form: s_sq_new = 2*M − round(√((4*M − s_sq) * M))
    # because √(x · M)/M = √x when x is given as x·M (single scaling).
    # General rule for round-to-nearest integer √ at scale M:
    #   round_sqrt_scaled(y) returns round(√(y * M)) — integer.
    for _ in range(max_cascade_depth):
        # 4 − s²_n  (in scaled form):  4*M − s_sq
        four_minus_s_sq_scaled = 4 * M - s_sq
        if four_minus_s_sq_scaled < 0:
            # numerical guard — should never happen with sane inputs
            four_minus_s_sq_scaled = 0
        # Compute round(√(four_minus_s_sq_scaled * M)) — this is
        # the scaled-integer representation of √(4 − s²).
        rsq_scaled = _scaled_integer_sqrt(four_minus_s_sq_scaled, M)
        # s²_{2n} = 2 − √(4 − s²_n);  scaled: 2*M − rsq_scaled
        s_sq = 2 * M - rsq_scaled
        n *= 2

    # Final half-perimeter approximation of π:
    #   π ≈ (n/2) · √(s²)
    # In scaled form:  pi_scaled = (n/2) · round(√(s_sq · M))
    s_scaled = _scaled_integer_sqrt(s_sq, M)
    # half_perimeter ≈ (n/2) · (s_scaled / M); we keep this as integer-
    # scaled value pi_scaled where pi_scaled / M ≈ π.
    # Note n is always even (n = 6, 12, 24, ...), so n/2 is integer.
    pi_scaled = (n * s_scaled) // 2

    # Extract decimal digits from pi_scaled / M.
    # Multiply pi_scaled by 10^(num_digits) before dividing by M to
    # produce the integer pi_int_digits = round(π · 10^num_digits).
    ten_pow = 10 ** num_digits
    pi_int = (pi_scaled * ten_pow) // M
    # Defensive: the integer part should be 3 · 10^num_digits.
    # i.e. pi_int / 10^num_digits ∈ [3.14159..., 3.14160...].
    integer_part = pi_int // ten_pow
    if integer_part != 3:
        raise RuntimeError(
            f"pi_cascade_digits produced integer part {integer_part}, "
            f"expected 3 (cascade depth + precision may be insufficient)"
        )
    fractional_part = pi_int - integer_part * ten_pow
    # Zero-pad the fractional part to exactly num_digits.
    frac_str = str(fractional_part).zfill(num_digits)
    return "3." + frac_str


def _scaled_integer_sqrt(y: int, M: int) -> int:
    """Compute round-to-nearest integer √(y) at scale M.

    Given y where y/M represents some non-negative real value, return
    round(√(y/M) * M) — the integer-scaled representation of √(y/M).

    Computed as round(√(y * M)) using integer-sqrt floor + nearest-
    integer correction. Pure integer arithmetic.
    """
    assert isinstance(y, int) and isinstance(M, int), "_scaled_integer_sqrt needs int"
    assert M > 0, f"_scaled_integer_sqrt requires positive M; got {M}"
    if y <= 0:
        return 0
    scaled = y * M
    s_lo = _integer_sqrt(scaled)
    s_hi = s_lo + 1
    # Round to nearest by squared-distance comparison
    if (s_hi * s_hi - scaled) < (scaled - s_lo * s_lo):
        return s_hi
    return s_lo
