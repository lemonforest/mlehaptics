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
AWAY-from-zero. These diverge at the .5 boundary. The C peer uses a
LIBM-FREE round-half-to-even branch (v0.9.0rc211; formerly llrint()
under the default IEEE-754 FE_TONEAREST mode — byte-identical on the
fed range 0 <= v < 2^63, differentially pinned by the rc210 tests at
the bottom of this file) for bit-exact match with Python at the
boundary; the dedicated banker's-rounding test case confirms this
matches. Products >= 2^63 overflow the int64 ABI: the C peer returns
SRMECH_ERR_BAD_INPUT (previously an unspecified, platform-divergent
llrint() domain-error result) and the dispatch falls through to the
Python reference path.
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
    a libm-free round-half-to-even branch (v0.9.0rc211; formerly
    llrint() under default IEEE-754 FE_TONEAREST mode — byte-identical
    on the fed range), so the cascade native path matches Python's
    round() at the boundary bit-exactly.

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
        f"Python ref={ref_05} (cascade C peer must round half-to-even "
        f"to match Python's round() at .5)"
    )


def test_bankers_rounding_boundary_negative_native_matches_python():
    """Negative boundary case: -0.5 with fine_scale=1, max_denom=1.

    magnitude = 0.5, fine_scale = 1, magnitude * fine_scale = 0.5
    -> round(0.5) = 0 (banker's) -> (0, 1) [orientation discarded
    because num_pos == 0]. The C peer must reach the same (0, 1)
    result via its round-half-to-even branch (0.5 ties to even 0).
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


# ──────────────────────────────────────────────────────────────────────
# v0.9.0rc211 — libm-free round differential (new round == old llrint)
#
# The C peer's llrint() (the last libm import in libsrmech) was
# replaced by the libm-free _cascade_brs_round_half_even branch. These
# tests differentially pin the replacement: Python's built-in round()
# on a float IS correctly-rounded ties-to-even on the double — exactly
# llrint() under the default IEEE-754 FE_TONEAREST mode — so
# "mirror == round()" across the fed range IS "new round == old
# llrint", with the native end-to-end sweep proving the shipped binary
# agrees.
# ──────────────────────────────────────────────────────────────────────

def _round_half_even_c_mirror(v):
    """Pure-Python mirror of the C helper _cascade_brs_round_half_even.

    Same algorithm, statement for statement: exact truncation, exact
    fractional part (both exact in IEEE-754 for 0 <= v < 2^63), and the
    tie-to-even branch t + (t & 1). Python int(float) truncates toward
    zero like the C cast; float(int) round-trips exactly for the values
    involved (v < 2^53 has t < 2^53 exactly representable; v >= 2^52 is
    already integral so frac == 0.0 identically).
    """
    assert v >= 0.0
    assert v < 2.0 ** 63
    t = int(v)                # exact truncation (C: (long long)v)
    frac = v - float(t)       # exact under IEEE-754 (C: v - (double)t)
    if frac > 0.5:
        return t + 1
    if frac == 0.5:
        return t + (t & 1)    # tie goes to the even neighbour
    return t


def _rc210_fed_range_sweep():
    """The differential sweep: exact ties (both parities), random
    magnitudes across the full fed range, and the representability
    boundaries where the algorithm's exactness argument is tightest.
    """
    values = []
    # Exact .5 ties, even and odd integer parts.
    values += [k + 0.5 for k in range(0, 64)]
    values += [k + 0.5 for k in (999, 1000, 10**6, 10**12, 2**40)]
    # The largest sub-2^52 tie: ulp in [2^51, 2^52) is 0.5, so
    # 2^52 - 0.5 is exactly representable AND an exact tie.
    values += [2.0**52 - 0.5, 2.0**52 - 1.5, 2.0**51 + 0.5]
    # Integral-by-construction region (ulp >= 1): 2^52 .. just below 2^63.
    values += [2.0**52, 2.0**52 + 1.0, 2.0**53, 2.0**53 + 2.0,
               2.0**62, 2.0**63 - 1024.0]  # 2^63 - 1024 = largest double < 2^63
    # Near-half neighbours (one ulp off the tie — must NOT round as ties).
    values += [0.5 - 2.0**-54, 0.5 + 2.0**-53,
               1.5 - 2.0**-52, 1.5 + 2.0**-52]
    # Sub-half + tiny (round to 0, as llrint does).
    values += [0.0, 0.25, 0.49999999999999994, 5e-324, 1e-12]
    # Deterministic random sweep across magnitudes.
    rng = random.Random(20260710)
    for _ in range(500):
        values.append(rng.uniform(0.0, 1.0))
        values.append(rng.uniform(0.0, 1000.0))
        values.append(rng.uniform(0.0, 2.0**32))
        values.append(rng.uniform(0.0, 2.0**52))
    return values


def test_rc211_round_mirror_matches_python_round_across_fed_range():
    """Differential check: the C rounding algorithm (mirrored exactly in
    Python) == Python round() == old llrint()@FE_TONEAREST, across the
    fed range including every tie parity and representability boundary.
    """
    for v in _rc210_fed_range_sweep():
        expected = round(v)  # ties-to-even on the double == llrint
        got = _round_half_even_c_mirror(v)
        assert got == expected, (
            f"rc210 round-half-even mirror diverged from Python round() "
            f"(== llrint @ FE_TONEAREST) at v={v!r} ({v.hex()}): "
            f"mirror={got}, round={expected}"
        )


@SKIP_IF_NO_BEST_RATIONAL_SIGNED_NATIVE
def test_rc211_native_round_differential_end_to_end():
    """End-to-end: with fine_scale=1 and max_denominator=1 the cascade
    output numerator IS round(magnitude), so sweeping x = v through the
    NATIVE path differentially pins the shipped C binary's new rounding
    against Python round() (== the old llrint) across the fed range.
    """
    for v in _rc210_fed_range_sweep():
        if not v < 2.0**63:  # stay inside the int64 ABI (fed range)
            continue
        expected_num = round(v)
        expected = (0, 1) if expected_num == 0 else (expected_num, 1)
        got = cascade.best_rational_signed(v, max_denominator=1, fine_scale=1)
        assert got == expected, (
            f"rc210 native rounding diverged at x={v!r} ({v.hex()}): "
            f"cascade={got}, expected={expected}"
        )
        # Negative branch: Class K strips the sign ahead of the round,
        # so |x| rounds identically and Class C re-applies the sign.
        if expected_num > 0:
            got_neg = cascade.best_rational_signed(
                -v, max_denominator=1, fine_scale=1,
            )
            assert got_neg == (-expected_num, 1), (
                f"rc210 native rounding diverged at x={-v!r}: "
                f"cascade={got_neg}, expected={(-expected_num, 1)}"
            )


@SKIP_IF_NO_BEST_RATIONAL_SIGNED_NATIVE
def test_rc211_product_at_2_63_falls_back_to_python_ref():
    """A product in [2^63, 2^64) exceeds the int64 ABI: the C peer now
    returns SRMECH_ERR_BAD_INPUT and the dispatch falls through to the
    Python reference path, which computes the EXACT convergent
    (numerator still fits uint64). Previously llrint()'s domain error
    made this platform-divergent nonsense (x86-64: (0, 1) via LLONG_MIN;
    aarch64: a convergent of the saturated LLONG_MAX).
    """
    # 1e13 * 10^6 = 1e19, and 2^63 < 1e19 < 2^64. 1e19 is exactly
    # representable (10^19 = 2^19 * 5^19, 5^19 < 2^53), so the Python
    # path rounds it to exactly 10**19 and 10**19 / 10**6 = 10**13.
    x = 1e13
    assert 2**63 < x * 10**6 < 2**64
    result = cascade.best_rational_signed(x)  # default fine_scale=10^6
    ref = _python_ref(x)
    assert ref == (10**13, 1)
    assert result == ref, (
        f"int64-overflow fallback diverged from Python ref at x={x!r}: "
        f"cascade={result}, ref={ref} (the C peer must reject >= 2^63 "
        f"products so the dispatch reaches the exact Python path)"
    )
    assert cascade.best_rational_signed(-x) == (-(10**13), 1)


def test_rc211_product_beyond_uint64_now_computes_matching_pure_python_898():
    """`#898` (rc319) lifted the Class N ``best_rational`` uint64 ceiling, so a
    product >= 2^64 no longer raises. The native cascade peer still rejects it
    at the 2^63 int64 bound, so the dispatch reaches the Python reference path,
    where the now-bignum ``best_rational`` anchors the huge magnitude to a
    low-denominator convergent (q <= max_denominator; here (bignum, 61)). The
    native-enabled and pure-Python surfaces still AGREE — that agreement, not
    the ValueError, was always the point of this pin (pre-rc210 llrint() gave a
    silent platform-divergent result; the old u64 guard replaced it with a
    raise; #898 replaces the raise with an exact bignum answer). Runs in both
    native and pure hosts.
    """
    x = 1e300
    assert x * 10 ** 6 >= 2 ** 64          # the product the old u64 guard rejected
    ref = _python_ref(x)                    # independent pure reference (bignum)
    assert ref[0] > 0 and 1 <= ref[1] <= 100  # a positive anchor within max_denom
    assert cascade.best_rational_signed(x) == ref          # cascade path == ref
    assert cascade.best_rational_signed(-x) == (-ref[0], ref[1])  # sign mirror
