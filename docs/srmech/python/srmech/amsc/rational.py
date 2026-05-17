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
import math
from typing import List, Tuple

from . import _native

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
]

# Max terms a uint64 continued fraction can produce is Fibonacci-worst-
# case ~91 iterations; 128 is the C-side cap and a safe Python ceiling.
_MAX_TERMS: int = 128


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

    # Reduce to lowest terms via Class N rational gcd:
    if sum_num == 0:
        return (0, 1)
    g = math.gcd(abs(sum_num), sum_den)
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
    """Reduce (num, den) to lowest terms with positive denominator."""
    if den == 0:
        raise ZeroDivisionError("rational denominator is zero")
    if num == 0:
        return (0, 1)
    g = math.gcd(abs(num), abs(den))
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

    Caller responsibility: |p/q| < 1 for convergence (the series
    diverges otherwise). The function computes the partial sum
    regardless; rate-of-convergence is asymptotic for |x| near 1.
    """
    _check_series_inputs(numerator, denominator, num_terms,
                         _LOG_SERIES_MAX_TERMS, "log1p_series_truncate")
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

    Caller responsibility: |p/q| ≤ 1 for fast convergence. The series
    is valid for |x| ≤ 1 (alternating series test).
    """
    _check_series_inputs(numerator, denominator, num_terms,
                         _LOG_SERIES_MAX_TERMS, "atan_series_truncate")
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
    """Integer floor square root. Pure integer.

    Used by pi_cascade_digits to bound the cascade's rational √
    operation in pure integer arithmetic. No floats, no math.pi.

    Implementation: stdlib ``math.isqrt`` (CPython 3.10+ uses an
    asymptotically-optimal Karatsuba-style algorithm internally — for
    20480-bit inputs (D=1000 cascade scale) the speedup over a naive
    Newton iteration is ~2500x). This is the rc13 cap-expansion
    optimization that makes num_digits up to 1000 tractable. The AST-
    verification gate only flags ``math.pi`` / ``math.tau`` /
    ``numpy.pi``; ``math.isqrt`` is a pure-integer arithmetic helper
    and is explicitly compatible with the substrate-invariance
    discipline per ``[[user_stance_pi_spectral_shape_scalar_invariant]]``.
    """
    assert isinstance(n, int), "_integer_sqrt requires int"
    assert n >= 0, f"_integer_sqrt requires non-negative input; got {n}"
    return math.isqrt(n)


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
