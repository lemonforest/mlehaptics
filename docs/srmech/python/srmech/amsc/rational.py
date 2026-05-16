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

__all__ = ["continued_fraction", "best_rational", "exp_series_truncate"]

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
