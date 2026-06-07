"""W14 (RBS-LM bugfix wishlist) — series domain guards.

The naive Taylor partial sums ``atan_series_truncate`` / ``log1p_series_truncate``
have radius of convergence 1. Before v0.7.5rc1 they silently returned a
*divergent* rational for an out-of-domain argument (e.g. ``atan(2/1)`` → ~3e16,
``log1p(799/1)`` → blow-up). They now refuse the out-of-domain input loudly
with a Class-N domain ``ValueError`` (the §15.1/§18 Class-K contract-error
pattern). These exact-rational ops cannot range-reduce (π is irrational); the
float projection :func:`srmech.amsc.rational.atan` IS band-reduced and stays
the path for ``|x| > 1``.
"""

from __future__ import annotations

import math

import pytest

from srmech.amsc import rational as r


# ---- in-domain still works (incl. the |x| = 1 conditional boundary) --------

@pytest.mark.parametrize(
    "num,den",
    [(0, 1), (1, 10), (1, 4), (1, 2), (-1, 4), (1, 1), (-1, 2)],
)
def test_atan_in_domain_unchanged(num: int, den: int) -> None:
    """``|p/q| ≤ 1`` (boundary included) still computes a finite rational."""
    n, d = r.atan_series_truncate(num, den, 30)
    assert d > 0
    # the boundary atan(1) = π/4 converges (slowly) to the right value
    if (num, den) == (1, 1):
        assert abs(n / d - math.pi / 4) < 1e-1


@pytest.mark.parametrize(
    "num,den",
    [(0, 1), (1, 10), (1, 4), (1, 1), (-1, 4), (-1, 2)],
)
def test_log1p_in_domain_unchanged(num: int, den: int) -> None:
    """``-1 < p/q ≤ 1`` still computes a finite rational; the x = 1 boundary
    (log 2) is allowed."""
    n, d = r.log1p_series_truncate(num, den, 30)
    assert d > 0
    if (num, den) == (1, 1):
        assert abs(n / d - math.log(2.0)) < 1e-1


# ---- out-of-domain is now refused loudly (was: silent divergent rational) --

@pytest.mark.parametrize("num,den", [(2, 1), (5, 1), (-2, 1), (-3, 1), (101, 100)])
def test_atan_out_of_domain_raises(num: int, den: int) -> None:
    """``|p/q| > 1`` raises a Class-N domain ``ValueError`` (no silent
    divergent rational)."""
    with pytest.raises(ValueError, match="radius of convergence"):
        r.atan_series_truncate(num, den, 30)


@pytest.mark.parametrize("num,den", [(2, 1), (799, 1), (-1, 1), (-2, 1), (101, 100)])
def test_log1p_out_of_domain_raises(num: int, den: int) -> None:
    """``x > 1`` or ``x ≤ -1`` raises (``x = -1`` is log(0) = -∞)."""
    with pytest.raises(ValueError, match="radius of convergence"):
        r.log1p_series_truncate(num, den, 30)


# ---- the float projection remains the range-reduced path for |x| > 1 -------

@pytest.mark.parametrize("x", [2.0, 5.0, -3.0, 100.0, -0.5, 1.0, 0.0])
def test_float_atan_is_range_safe(x: float) -> None:
    """``rational.atan(x)`` (band-reduced) matches libm for any real x —
    the documented escape for arguments the exact series refuses."""
    assert abs(r.atan(x) - math.atan(x)) < 1e-9
