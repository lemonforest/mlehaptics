"""C/Python parity tests for srmech.amsc.cascade.best_rational_signed.

v0.4.5rc7 continues the v0.4.5rc1..rc6 cascade-catalog C-parity
correction by retrofitting best_rational_signed (Class K ∘ Class N ∘
Class C cascade) with a cascade-namespace C wrapper and a TOML
descriptor. SECOND of the delegating cascade ops in the arc: the C
peer delegates the LOAD-BEARING Class N stage to the existing
srmech_best_rational primitive and inlines the trivial Class K (sign-
strip) + Class C (sign-re-apply) stages.

This test confirms native + Python paths produce bit-identical outputs
across the supported input shapes — basic positives / basic negatives /
origin / sub-dead-band / NaN / tiny / large / custom kwargs / invalid
kwargs / random sweep / banker's-rounding boundary.

Banker's-rounding parity (load-bearing): Python's built-in round() uses
round-half-to-even (banker's rounding); C99 round() uses round-half-
AWAY-from-zero. These diverge at the .5 boundary. The C peer uses
llrint() under the default IEEE-754 FE_TONEAREST mode (= round-half-to-
even) for bit-exact match with Python at the boundary; the dedicated
banker's-rounding test case confirms this matches.
"""
import math
import random

import pytest

from srmech.amsc import _native, cascade
from srmech.amsc._native import HAS_NATIVE


SKIP_IF_NO_NATIVE = pytest.mark.skipif(
    not HAS_NATIVE,
    reason="native srmech library not loaded; C-parity test cannot run",
)

# Whether the loaded libsrmech actually exposes the best_rational_signed
# cascade wrapper symbol. A stale lib (pre-rc7) loads fine but doesn't
# expose the new symbol; tests that need the native cascade path skip
# cleanly when this is False. The Class N primitive (srmech_best_rational)
# has been present since rc6 of the original Phase C1 build-out, so it's
# expected to always be available when HAS_NATIVE — but we check it too
# so the symbol-exposure test reports both surfaces.
_BEST_RATIONAL_SIGNED_NATIVE = (
    HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_best_rational_signed_f64")
)

SKIP_IF_NO_BEST_RATIONAL_SIGNED_NATIVE = pytest.mark.skipif(
    not _BEST_RATIONAL_SIGNED_NATIVE,
    reason="installed libsrmech predates v0.4.5rc7 best_rational_signed cascade symbol",
)


def _python_ref(x, max_denominator=100, fine_scale=1_000_000):
    """Bit-identical Python-reference mirror (no srmech imports beyond Class N).

    Re-implements the Python fallback path directly so this test is
    independent of the cascade.py implementation (and catches the case
    where cascade.py and the C peer drift apart).
    """
    if x > 0.0:
        orientation, magnitude = +1, x
    elif x < 0.0:
        orientation, magnitude = -1, -x
    else:
        orientation, magnitude = 0, 0.0
    # Python's round() is banker's-rounding (round-half-to-even).
    if orientation == 0 or magnitude < 1e-12:
        return (0, 1)
    num_pos = int(round(magnitude * fine_scale))
    if num_pos == 0:
        return (0, 1)
    # Delegate to the actual Class N primitive (which is itself C-backed).
    from srmech.amsc.rational import best_rational as _br
    nf, df = _br(num_pos, fine_scale, max_denominator)
    if orientation < 0:
        nf = -int(nf)
    return (int(nf), int(df))


# ──────────────────────────────────────────────────────────────────────
# Basic positive correctness
# ──────────────────────────────────────────────────────────────────────

def test_basic_half_is_one_half():
    """best_rational_signed(0.5) -> (1, 2)."""
    assert cascade.best_rational_signed(0.5) == (1, 2)


def test_basic_quarter_is_one_quarter():
    """best_rational_signed(0.25) -> (1, 4)."""
    assert cascade.best_rational_signed(0.25) == (1, 4)


def test_one_third_approximates_to_1_3():
    """best_rational_signed(1/3) anchors to 1/3 under default max_denom=100."""
    nf, df = cascade.best_rational_signed(1.0 / 3.0)
    assert (nf, df) == (1, 3)


def test_pi_like_3_14_anchors():
    """best_rational_signed(3.14) -> some (n, d) where n/d ≈ 3.14."""
    nf, df = cascade.best_rational_signed(3.14)
    assert df >= 1
    assert abs(nf / df - 3.14) < 0.01


def test_negative_half_is_neg_one_half():
    """best_rational_signed(-0.5) -> (-1, 2)."""
    assert cascade.best_rational_signed(-0.5) == (-1, 2)


def test_negative_quarter_is_neg_one_quarter():
    """best_rational_signed(-0.25) -> (-1, 4)."""
    assert cascade.best_rational_signed(-0.25) == (-1, 4)


def test_negative_pi_like_anchors():
    """best_rational_signed(-3.14) -> (-n, d) where -n/d ≈ -3.14."""
    nf, df = cascade.best_rational_signed(-3.14)
    assert df >= 1
    assert nf < 0
    assert abs(nf / df - (-3.14)) < 0.01


# ──────────────────────────────────────────────────────────────────────
# Dead-band / origin / NaN
# ──────────────────────────────────────────────────────────────────────

def test_origin_maps_to_0_1():
    """best_rational_signed(0.0) -> (0, 1)."""
    assert cascade.best_rational_signed(0.0) == (0, 1)


def test_negative_zero_maps_to_0_1():
    """best_rational_signed(-0.0) -> (0, 1) — Class K dead-band."""
    assert cascade.best_rational_signed(-0.0) == (0, 1)


def test_sub_dead_band_maps_to_0_1():
    """|x| < 1e-12 -> (0, 1) via Class K dead-band."""
    assert cascade.best_rational_signed(1e-15) == (0, 1)
    assert cascade.best_rational_signed(-1e-15) == (0, 1)
    assert cascade.best_rational_signed(5e-13) == (0, 1)


def test_nan_maps_to_0_1():
    """NaN -> (0, 1) (both `x > 0` and `x < 0` evaluate false under IEEE-754)."""
    assert cascade.best_rational_signed(float("nan")) == (0, 1)


# ──────────────────────────────────────────────────────────────────────
# Tiny / large values
# ──────────────────────────────────────────────────────────────────────

def test_tiny_positive_above_dead_band():
    """A tiny positive above 1e-12 -> a valid rational close to 0."""
    nf, df = cascade.best_rational_signed(1e-10)
    # Result must be a non-negative rational; either (0, 1) or a tiny
    # rational depending on fine_scale * 1e-10 rounding.
    assert df >= 1
    assert nf >= 0
    if (nf, df) != (0, 1):
        assert abs(nf / df - 1e-10) < 1e-3


def test_large_value_anchors():
    """best_rational_signed(100.0) -> some (n, d) with n/d ≈ 100."""
    nf, df = cascade.best_rational_signed(100.0)
    assert df >= 1
    assert abs(nf / df - 100.0) < 1.0


def test_negative_large_value_anchors():
    """best_rational_signed(-100.0) -> some (-n, d) with -n/d ≈ -100."""
    nf, df = cascade.best_rational_signed(-100.0)
    assert df >= 1
    assert nf < 0
    assert abs(nf / df - (-100.0)) < 1.0


# ──────────────────────────────────────────────────────────────────────
# Custom kwargs — max_denominator + fine_scale variation
# ──────────────────────────────────────────────────────────────────────

def test_custom_max_denominator_10():
    """max_denominator=10 caps the convergent's denominator."""
    nf, df = cascade.best_rational_signed(0.5, max_denominator=10)
    assert df <= 10
    assert (nf, df) == (1, 2)  # 1/2 fits within max_denom=10


def test_custom_max_denominator_1000_for_pi():
    """max_denominator=1000 lets π anchor closer than default 100."""
    nf, df = cascade.best_rational_signed(math.pi, max_denominator=1000)
    assert df <= 1000
    # 355/113 is the canonical π convergent at this denominator scale.
    assert (nf, df) == (355, 113)


def test_custom_fine_scale():
    """Larger fine_scale -> finer rational anchor."""
    nf, df = cascade.best_rational_signed(
        0.5, max_denominator=100, fine_scale=10_000,
    )
    assert (nf, df) == (1, 2)


# ──────────────────────────────────────────────────────────────────────
# Invalid kwargs (Python path raises ValueError)
# ──────────────────────────────────────────────────────────────────────

def test_max_denominator_zero_raises():
    """max_denominator=0 raises ValueError; native dispatch skipped."""
    with pytest.raises(ValueError, match="max_denominator must be >= 1"):
        cascade.best_rational_signed(0.5, max_denominator=0)


def test_max_denominator_negative_raises():
    with pytest.raises(ValueError, match="max_denominator must be >= 1"):
        cascade.best_rational_signed(0.5, max_denominator=-5)


def test_fine_scale_zero_raises():
    with pytest.raises(ValueError, match="fine_scale must be >= 1"):
        cascade.best_rational_signed(0.5, fine_scale=0)


def test_fine_scale_negative_raises():
    with pytest.raises(ValueError, match="fine_scale must be >= 1"):
        cascade.best_rational_signed(0.5, fine_scale=-3)


# ──────────────────────────────────────────────────────────────────────
# Native + Python ref bit-identical
# ──────────────────────────────────────────────────────────────────────

@SKIP_IF_NO_BEST_RATIONAL_SIGNED_NATIVE
def test_native_vs_python_ref_50_sample_random_sweep():
    """50-sample random sweep; native dispatch must equal Python ref bit-exactly."""
    rng = random.Random(20260528)  # deterministic seed
    for _ in range(50):
        # Mix positive / negative / small / large.
        sign = rng.choice([+1.0, -1.0])
        mag = rng.uniform(1e-8, 1000.0)
        x = sign * mag
        cascade_result = cascade.best_rational_signed(x)
        ref_result = _python_ref(x)
        assert cascade_result == ref_result, (
            f"native cascade diverged from Python ref at "
            f"best_rational_signed({x}): cascade={cascade_result}, "
            f"ref={ref_result}"
        )


@SKIP_IF_NO_BEST_RATIONAL_SIGNED_NATIVE
def test_native_known_rationals_bit_exact():
    """Well-known rationals through the native cascade path."""
    cases = [
        (0.5, (1, 2)),
        (-0.5, (-1, 2)),
        (0.25, (1, 4)),
        (0.75, (3, 4)),
        (-0.75, (-3, 4)),
        (1.0, (1, 1)),
        (-1.0, (-1, 1)),
        (2.0, (2, 1)),
        (1.0 / 3.0, (1, 3)),
        (1.0 / 7.0, (1, 7)),
    ]
    for x, expected in cases:
        result = cascade.best_rational_signed(x)
        assert result == expected, (
            f"best_rational_signed({x}) expected {expected}; got {result}"
        )


# ──────────────────────────────────────────────────────────────────────
# Banker's-rounding boundary (load-bearing — confirms llrint vs C99 round)
# ──────────────────────────────────────────────────────────────────────

def test_bankers_rounding_boundary_native_matches_python():
    """A value where magnitude * fine_scale lands exactly on .5.

    Python's round(0.5) is 0 (banker's, round-half-to-even);
    C99 round(0.5) is 1 (round-half-AWAY-from-zero). The C peer uses
    llrint() under default IEEE-754 FE_TONEAREST mode (banker's),
    so the cascade native path matches Python's round() at the
    boundary bit-exactly.

    We construct x and fine_scale so that magnitude * fine_scale ==
    0.5 exactly. round(0.5) -> 0 in Python, so the cascade returns
    (0, 1). If the C peer used C99 round() instead it would return
    a non-zero numerator and diverge.
    """
    # magnitude * fine_scale = 0.5 -> at fine_scale=1, magnitude=0.5
    # but 0.5 is above the dead-band (1e-12), so this lands in the
    # rounding step. Python's round(0.5) == 0 -> returns (0, 1).
    # With fine_scale=1 and max_denom=1, even if rounded to 1 the
    # result would be (1, 1) — so this case unambiguously
    # distinguishes the two rounding modes.
    result_05 = cascade.best_rational_signed(
        0.5, max_denominator=1, fine_scale=1,
    )
    # Python ref: round(0.5 * 1) = round(0.5) = 0 -> (0, 1).
    ref_05 = _python_ref(0.5, max_denominator=1, fine_scale=1)
    assert ref_05 == (0, 1), f"Python ref must return (0, 1); got {ref_05}"
    assert result_05 == ref_05, (
        f"banker's-rounding boundary mismatch at x=0.5, "
        f"max_denom=1, fine_scale=1: cascade={result_05}, "
        f"Python ref={ref_05} (cascade C peer must use llrint() "
        f"with FE_TONEAREST to match Python's round() at .5)"
    )


def test_bankers_rounding_boundary_negative_native_matches_python():
    """Negative boundary case: -0.5 with fine_scale=1, max_denom=1.

    magnitude = 0.5, fine_scale = 1, magnitude * fine_scale = 0.5
    -> round(0.5) = 0 (banker's) -> (0, 1) [orientation discarded
    because num_pos == 0]. The C peer must reach the same (0, 1)
    result via llrint(0.5) = 0 under FE_TONEAREST.
    """
    result = cascade.best_rational_signed(
        -0.5, max_denominator=1, fine_scale=1,
    )
    ref = _python_ref(-0.5, max_denominator=1, fine_scale=1)
    assert ref == (0, 1)
    assert result == ref, (
        f"banker's-rounding boundary mismatch at x=-0.5: "
        f"cascade={result}, ref={ref}"
    )


def test_bankers_rounding_boundary_at_1_5_native_matches_python():
    """At 1.5: round(1.5) is 2 in Python (banker's, ties to even),
    AND 2 in C99 round (which goes away from zero so also 2). This
    case doesn't distinguish the modes but pins parity at a tie. """
    result = cascade.best_rational_signed(
        1.5, max_denominator=2, fine_scale=1,
    )
    ref = _python_ref(1.5, max_denominator=2, fine_scale=1)
    assert result == ref, (
        f"x=1.5 parity mismatch: cascade={result}, ref={ref}"
    )


# ──────────────────────────────────────────────────────────────────────
# Symbol exposure — both cascade wrapper AND Class N primitive present
# ──────────────────────────────────────────────────────────────────────

@SKIP_IF_NO_NATIVE
def test_cascade_wrapper_symbol_is_exposed():
    """rc7 ships srmech_cascade_best_rational_signed_f64 as the
    cascade-catalog naming-uniform entry-point.
    """
    assert hasattr(_native.LIB, "srmech_cascade_best_rational_signed_f64"), (
        "rc7 cascade-namespace wrapper "
        "srmech_cascade_best_rational_signed_f64 should be exposed in "
        "libsrmech"
    )


@SKIP_IF_NO_NATIVE
def test_class_n_primitive_symbol_still_exposed():
    """The Class N primitive srmech_best_rational must remain exposed
    alongside the cascade wrapper — both surfaces coexist.
    """
    assert hasattr(_native.LIB, "srmech_best_rational"), (
        "the Class N primitive srmech_best_rational should remain "
        "exposed in libsrmech (cascade wrapper composes around it, "
        "not replaces it)"
    )
