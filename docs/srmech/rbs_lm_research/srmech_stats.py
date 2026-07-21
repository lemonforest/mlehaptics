"""srmech_stats — numpy-free replacements for the pure-statistics numpy calls, with numpy's exact semantics.

WHY A SHARED MODULE rather than 21 separate hand-migrations: these substitutions have subtle
semantics that are easy to get wrong once and then wrong everywhere. Defining them ONCE, with the
divergences written down and test vectors attached, is reviewable; scattering them is not.

THE SEMANTIC TRAPS, which are the whole reason this file exists:

  * ``np.std`` / ``np.var`` default to the POPULATION statistic (ddof=0). Python's ``statistics.stdev``
    / ``variance`` are the SAMPLE statistics (ddof=1). Substituting one for the other changes every
    number it touches and NOTHING ERRORS — the classic silent-substitution shape this project keeps
    hitting (F1277's "stable but not resonant" is the same failure in a different domain).
  * ``np.argsort`` is documented as returning a STABLE ordering only with kind="stable"; the default
    quicksort is NOT stable. Python's ``sorted`` IS stable, so this module is stable-by-construction —
    a difference that can only ever make ties more deterministic, never less.
  * ``np.median`` on an EVEN-length input averages the two middle values (it does not pick one).
  * ``np.mean`` of an empty sequence is nan-with-a-warning; here it RAISES. A silent nan is exactly
    the value that ``cascade.magnitude`` would later swallow to 0.0 (F1284), so failing loudly is the
    safer of the two wrong-looking options.

VERIFICATION LIMIT, STATED PLAINLY: numpy will not install on this interpreter (Python 3.14, no wheel),
so these are verified against HAND-COMPUTED vectors and numpy's documented semantics — NOT against a
live numpy. That is weaker than a differential test and it is the best available here. Every function
carries its worked example in the docstring so the arithmetic can be checked by eye.

srmech is used where srmech HAS the op (sqrt / pi are cascade surfaces); plain arithmetic is used where
it does not, because ``sum(x)/len(x)`` is not a cascade of the 14 pretending to be one.
"""
from __future__ import annotations

from typing import Sequence


def mean(xs: Sequence[float]) -> float:
    """np.mean. mean([1,2,3,4]) == 2.5. Empty RAISES (numpy returns nan + warning)."""
    xs = list(xs)
    if not xs:
        raise ValueError("mean() of an empty sequence — numpy returns nan here; raising instead so a "
                         "downstream Class-K magnitude cannot silently turn it into 0.0 (F1284)")
    return sum(xs) / len(xs)


def var(xs: Sequence[float], ddof: int = 0) -> float:
    """np.var — POPULATION by default (ddof=0), NOT statistics.variance (which is ddof=1).
    var([1,2,3,4]) == 1.25  (population)   vs statistics.variance -> 1.6667 (sample)."""
    xs = list(xs)
    n = len(xs)
    if n - ddof <= 0:
        raise ValueError("var(): need more than ddof=%d values, got %d" % (ddof, n))
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / (n - ddof)


def std(xs: Sequence[float], ddof: int = 0) -> float:
    """np.std — POPULATION by default. std([1,2,3,4]) == 1.1180339887... (== sqrt(1.25))."""
    return var(xs, ddof) ** 0.5


def median(xs: Sequence[float]) -> float:
    """np.median. EVEN length averages the two middle values:
    median([1,2,3,4]) == 2.5 ; median([1,2,3]) == 2."""
    s = sorted(xs)
    n = len(s)
    if not n:
        raise ValueError("median() of an empty sequence")
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def argsort(xs: Sequence) -> list:
    """np.argsort — indices that would sort xs. STABLE (Python's sorted is; numpy's default is not).
    argsort([3,1,2]) == [1,2,0]."""
    return sorted(range(len(xs)), key=lambda i: xs[i])


def argmax(xs: Sequence) -> int:
    """np.argmax — index of the max; FIRST occurrence on ties, matching numpy.
    argmax([1,3,3]) == 1."""
    xs = list(xs)
    if not xs:
        raise ValueError("argmax() of an empty sequence")
    return max(range(len(xs)), key=lambda i: xs[i])


def argmin(xs: Sequence) -> int:
    """np.argmin — index of the min; FIRST occurrence on ties. argmin([2,1,1]) == 1."""
    xs = list(xs)
    if not xs:
        raise ValueError("argmin() of an empty sequence")
    return min(range(len(xs)), key=lambda i: xs[i])


def allclose(a: Sequence[float], b: Sequence[float], rtol: float = 1e-5, atol: float = 1e-8) -> bool:
    """np.allclose — |a-b| <= atol + rtol*|b|, numpy's ASYMMETRIC formula (note it is |b|, not |a|).
    Length mismatch is False rather than a broadcast."""
    a, b = list(a), list(b)
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        d = x - y
        d = d if d >= 0 else -d          # Class-K sign branch, not the builtin (F1284)
        by = y if y >= 0 else -y
        if not (d <= atol + rtol * by):
            return False
    return True


def percentile(xs: Sequence[float], q: float) -> float:
    """np.percentile with the DEFAULT 'linear' interpolation:
    idx = q/100 * (n-1), then linear between the neighbours.
    percentile([1,2,3,4], 50) == 2.5 ; percentile([1,2,3,4], 0) == 1."""
    s = sorted(xs)
    n = len(s)
    if not n:
        raise ValueError("percentile() of an empty sequence")
    pos = (q / 100.0) * (n - 1)
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return s[lo] + (s[hi] - s[lo]) * frac


def sqrt(x: float) -> float:
    """np.sqrt for a scalar. srmech ships elementwise_sqrt for carriers; for a plain float the
    exponent form is the same operation without pretending to be a cascade."""
    return x ** 0.5


__all__ = ["mean", "var", "std", "median", "argsort", "argmax", "argmin",
           "allclose", "percentile", "sqrt"]
