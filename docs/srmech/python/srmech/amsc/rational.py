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
    "best_rational",
    "exp_series_truncate",
    "rational_add",
    "rational_mul",
    "rational_div",
    "rational_pow_uint",
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
