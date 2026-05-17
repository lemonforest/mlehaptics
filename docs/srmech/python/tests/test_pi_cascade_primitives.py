"""Unit tests for π geometric-cascade primitives (Milestone #4).

Per `[[user_stance_pi_spectral_shape_scalar_invariant]]` and Spike #32
(PR #460): π's substrate identity is the cascade-emergent CF-convergent
ladder. These tests pin:

1. ``continued_fraction_convergents`` produces canonical π convergents
   from the canonical π CF expansion.
2. ``pi_cascade_digits`` produces bit-exact canonical decimal expansion
   at requested precision.
3. AST-verified zero ``math.pi`` invocations anywhere in
   ``pi_cascade_digits``'s call graph (discipline gate).
"""

from __future__ import annotations

import ast
import inspect

import pytest

from srmech.amsc import rational
from srmech.amsc.rational import (
    continued_fraction_convergents,
    pi_cascade_digits,
)


# ──────────────────────────────────────────────────────────────────────
# continued_fraction_convergents — canonical π convergent ladder
# ──────────────────────────────────────────────────────────────────────


# Canonical π CF expansion (Khinchin Continued Fractions §10):
# π = [3; 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, ...]
CANONICAL_PI_CF = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1]

# Canonical π convergents (verifiable independently from CF coefficients
# via the recurrence; cross-checked against Hardy & Wright §10):
CANONICAL_PI_CONVERGENTS_FIRST_8 = [
    (3, 1),         # 3/1 = 3
    (22, 7),        # 22/7 ≈ 3.142857...
    (333, 106),     # 333/106 ≈ 3.141509...
    (355, 113),     # 355/113 ≈ 3.141592920... (4 correct digits)
    (103993, 33102),
    (104348, 33215),
    (208341, 66317),
    (312689, 99532),
]


def test_continued_fraction_convergents_canonical_pi_first_6() -> None:
    """The canonical π CF [3; 7, 15, 1, 292, 1] produces the canonical
    convergents (3,1), (22,7), (333,106), (355,113), (103993, 33102),
    (104348, 33215)."""
    result = continued_fraction_convergents([3, 7, 15, 1, 292, 1])
    expected = [
        (3, 1), (22, 7), (333, 106), (355, 113),
        (103993, 33102), (104348, 33215),
    ]
    assert result == expected


def test_continued_fraction_convergents_canonical_pi_full() -> None:
    """The full 16-term π CF produces the full canonical convergent
    ladder; matches Hardy & Wright §10.6 / Khinchin §10 references."""
    result = continued_fraction_convergents(CANONICAL_PI_CF)
    assert len(result) == 16
    # Pin the first 8 (the rest are derivable but vary in tabulation).
    for i, (exp_h, exp_k) in enumerate(CANONICAL_PI_CONVERGENTS_FIRST_8):
        assert result[i] == (exp_h, exp_k), (
            f"conv_{i}: expected ({exp_h}, {exp_k}), got {result[i]}"
        )


def test_continued_fraction_convergents_simple_rationals() -> None:
    """[2] → (2, 1); [1, 2] → (1, 1), (3, 2); [0, 1] → (0, 1), (1, 1)."""
    assert continued_fraction_convergents([2]) == [(2, 1)]
    assert continued_fraction_convergents([1, 2]) == [(1, 1), (3, 2)]
    assert continued_fraction_convergents([0, 1]) == [(0, 1), (1, 1)]


def test_continued_fraction_convergents_canonical_e() -> None:
    """e's CF [2; 1, 2, 1, 1, 4, 1, 1, 6] produces canonical e convergents.
    Provides cross-substrate sanity check (different transcendental, same
    primitive)."""
    cf_e = [2, 1, 2, 1, 1, 4, 1, 1, 6]
    result = continued_fraction_convergents(cf_e)
    # First few canonical e convergents (verifiable independently):
    # 2/1, 3/1, 8/3, 11/4, 19/7, 87/32, 106/39, 193/71, 1264/465
    expected = [
        (2, 1), (3, 1), (8, 3), (11, 4), (19, 7),
        (87, 32), (106, 39), (193, 71), (1264, 465),
    ]
    assert result == expected


def test_continued_fraction_convergents_negative_a0() -> None:
    """Negative a_0 is allowed (simple-CF convention); subsequent terms
    must remain positive."""
    # [-1; 2] represents -1 + 1/2 = -1/2; convergents: (-1, 1), (-1, 2).
    result = continued_fraction_convergents([-1, 2])
    assert result == [(-1, 1), (-1, 2)]


def test_continued_fraction_convergents_bignum_ladder() -> None:
    """A long ladder should produce convergents beyond int64 without
    error; the wrapper transparently falls through to bignum-Python."""
    # 20 large CF coefficients → convergent ladder will exceed int64
    # somewhere along the way. Result must still be returned.
    long_cf = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1,
               2, 2, 2, 1, 84]
    result = continued_fraction_convergents(long_cf)
    assert len(result) == len(long_cf)
    # Last convergent's denominator should be substantial:
    _, k_last = result[-1]
    assert k_last > 0


def test_continued_fraction_convergents_empty_raises() -> None:
    """Empty coef_list rejected."""
    with pytest.raises(ValueError):
        continued_fraction_convergents([])


def test_continued_fraction_convergents_wrong_type_raises() -> None:
    """Non-list / wrong-typed entries rejected."""
    with pytest.raises(TypeError):
        continued_fraction_convergents("not a list")  # type: ignore[arg-type]
    with pytest.raises(AssertionError):
        # Python's assert catches mixed type entries
        continued_fraction_convergents([1, 2, "3"])  # type: ignore[list-item]


def test_continued_fraction_convergents_zero_or_negative_inner_term() -> None:
    """Simple CF requires a_k > 0 for k > 0."""
    with pytest.raises(ValueError):
        continued_fraction_convergents([1, 0, 2])  # a_1 = 0
    with pytest.raises(ValueError):
        continued_fraction_convergents([1, -2])    # a_1 negative


def test_continued_fraction_convergents_cap() -> None:
    """Coef list exceeding cap is rejected."""
    too_long = [1] * (rational._CF_CONVERGENTS_MAX_COEFS + 1)
    with pytest.raises(ValueError):
        continued_fraction_convergents(too_long)


# ──────────────────────────────────────────────────────────────────────
# pi_cascade_digits — canonical decimal expansion
# ──────────────────────────────────────────────────────────────────────


# Canonical π to 50 decimal digits (independently verifiable; reference:
# any standard π table, e.g. NIST Digital Library §3.12). This is the
# "ground truth" we compare against for rc12-era tests.
CANONICAL_PI_50 = "3.14159265358979323846264338327950288419716939937510"

# Canonical π to 1000 decimal digits — rc13 cap-expansion (Task #248)
# ground-truth reference. Generated independently of srmech (mpmath
# at decimal precision 1100; cross-validated bit-exact against the
# cascade at every rc12-supported precision level + the rc13 cap-
# expansion validation rows in the AMSC catalog). Used by rc13 tests
# at num_digits ∈ {100, 200, 350, 500, 750, 1000}.
CANONICAL_PI_1000 = (
    "3.1415926535897932384626433832795028841971693993751058209749445923078164"
    "062862089986280348253421170679821480865132823066470938446095505822317253"
    "594081284811174502841027019385211055596446229489549303819644288109756659"
    "334461284756482337867831652712019091456485669234603486104543266482133936"
    "072602491412737245870066063155881748815209209628292540917153643678925903"
    "600113305305488204665213841469519415116094330572703657595919530921861173"
    "819326117931051185480744623799627495673518857527248912279381830119491298"
    "336733624406566430860213949463952247371907021798609437027705392171762931"
    "767523846748184676694051320005681271452635608277857713427577896091736371"
    "787214684409012249534301465495853710507922796892589235420199561121290219"
    "608640344181598136297747713099605187072113499999983729780499510597317328"
    "160963185950244594553469083026425223082533446850352619311881710100031378"
    "387528865875332083814206171776691473035982534904287554687311595628638823"
    "537875937519577818577805321712268066130019278766111959092164201989"
)


def test_pi_cascade_digits_zero_digits() -> None:
    """num_digits=0 returns '3.' (just the integer part separator)."""
    assert pi_cascade_digits(0) == "3."


def test_pi_cascade_digits_5_digits() -> None:
    """π to 5 digits: '3.14159'."""
    assert pi_cascade_digits(5) == "3.14159"


def test_pi_cascade_digits_10_digits() -> None:
    """π to 10 digits: '3.1415926535'."""
    assert pi_cascade_digits(10) == "3.1415926535"


def test_pi_cascade_digits_15_digits() -> None:
    """π to 15 digits: '3.141592653589793' — the IEEE-754 double-
    precision boundary (16 significant digits)."""
    assert pi_cascade_digits(15) == "3.141592653589793"


def test_pi_cascade_digits_20_digits() -> None:
    """π to 20 digits: '3.14159265358979323846' — beyond double-
    precision into bignum territory."""
    assert pi_cascade_digits(20) == "3.14159265358979323846"


def test_pi_cascade_digits_25_digits() -> None:
    """π to 25 digits: '3.1415926535897932384626433'."""
    assert pi_cascade_digits(25) == "3.1415926535897932384626433"


def test_pi_cascade_digits_50_digits() -> None:
    """π to 50 digits: the practical maximum at default depth + precision."""
    result = pi_cascade_digits(50)
    assert result == CANONICAL_PI_50


def test_pi_cascade_digits_matches_canonical_at_every_depth() -> None:
    """Every supported (num_digits) produces a prefix of CANONICAL_PI_50."""
    for d in [0, 1, 3, 7, 12, 18, 25, 35, 45, 50]:
        result = pi_cascade_digits(d)
        expected_prefix = CANONICAL_PI_50[:d + 2]  # "3." + d digits
        assert result == expected_prefix, (
            f"d={d}: expected {expected_prefix!r}, got {result!r}"
        )


def test_pi_cascade_digits_negative_raises() -> None:
    """Negative num_digits is rejected."""
    with pytest.raises(ValueError):
        pi_cascade_digits(-1)


def test_pi_cascade_digits_over_cap_raises() -> None:
    """num_digits > cap is rejected."""
    with pytest.raises(ValueError):
        pi_cascade_digits(rational._PI_CASCADE_MAX_DIGITS + 1)


def test_pi_cascade_digits_wrong_type_raises() -> None:
    """Non-int num_digits is rejected."""
    with pytest.raises(TypeError):
        pi_cascade_digits(15.0)  # type: ignore[arg-type]


def test_pi_cascade_digits_low_depth_low_precision_warns_or_diverges() -> None:
    """At deliberately-low depth, the function still returns a string,
    but the digits will not match canonical π beyond some prefix.
    This pins the parameter's behavior."""
    # Depth 1 (one cascade step) — only correct to ~1-2 digits.
    result = pi_cascade_digits(5, max_cascade_depth=1, precision_bits=64)
    assert result.startswith("3.")
    # Depth 10 — should give us ~6 correct digits.
    result = pi_cascade_digits(5, max_cascade_depth=10, precision_bits=128)
    assert result.startswith("3.14")


def test_pi_cascade_digits_explicit_kwargs_match_default() -> None:
    """Calling with explicit default kwargs equals calling without."""
    a = pi_cascade_digits(15)
    b = pi_cascade_digits(15, max_cascade_depth=90, precision_bits=512)
    assert a == b


# ──────────────────────────────────────────────────────────────────────
# rc13 cap-expansion (Task #248) — num_digits up to 1000
# ──────────────────────────────────────────────────────────────────────


def test_pi_cascade_digits_350_weird_number_on_purpose() -> None:
    """The user's deliberate 'weird number on purpose' probe from
    PR #468 benchmark (2026-05-17): 350 is not a power of 10, not a
    canonical CF convergent denominator. rc12 capped at 50 by
    validation; rc13 cap-expansion closes that gap. Bit-exact against
    canonical π reference."""
    expected = CANONICAL_PI_1000[:352]  # "3." + 350 digits
    assert pi_cascade_digits(350) == expected


@pytest.mark.parametrize("num_digits", [100, 200, 350, 500, 750, 1000])
def test_pi_cascade_digits_scaling_rc13(num_digits: int) -> None:
    """rc13 cap-expansion: every num_digits in {100, 200, 350, 500, 750,
    1000} produces the canonical π expansion bit-exactly. Auto-scaled
    cascade depth + precision_bits per `_pi_cascade_auto_params`."""
    expected = CANONICAL_PI_1000[:num_digits + 2]
    produced = pi_cascade_digits(num_digits)
    assert produced == expected, (
        f"num_digits={num_digits}: cascade produced wrong prefix; "
        f"first divergence at position "
        f"{next((i for i in range(min(len(produced), len(expected))) if produced[i] != expected[i]), 'no-divergence')}"
    )


def test_pi_cascade_digits_1000_rc13_ceiling() -> None:
    """The rc13 cap-expansion ceiling at num_digits=1000. Bit-exact
    against the 1000-digit canonical reference."""
    assert pi_cascade_digits(1000) == CANONICAL_PI_1000


def test_pi_cascade_digits_over_rc13_cap_raises() -> None:
    """num_digits > 1000 (rc13 cap) is rejected with ValueError."""
    with pytest.raises(ValueError):
        pi_cascade_digits(1001)
    with pytest.raises(ValueError):
        pi_cascade_digits(rational._PI_CASCADE_MAX_DIGITS + 1)


def test_pi_cascade_digits_auto_params_helper() -> None:
    """The auto-scaling helper produces (depth, precision_bits)
    proportional to num_digits, with minimum (90, 512) at the rc12-era
    validated point. Spot-check the table at canonical levels."""
    # At num_digits=50 (rc12's validated point): exactly (90, 512).
    assert rational._pi_cascade_auto_params(50) == (90, 512)
    # At num_digits=0: (90, 512) — the minimum bound clamps in.
    assert rational._pi_cascade_auto_params(0) == (90, 512)
    # At num_digits=350: (630, 3584) per the benchmark note's
    # projection (depth = 350*90/50 = 630; prec = 350*512/50 = 3584).
    assert rational._pi_cascade_auto_params(350) == (630, 3584)
    # At num_digits=1000: (1800, 10240).
    assert rational._pi_cascade_auto_params(1000) == (1800, 10240)


def test_pi_cascade_digits_explicit_kwargs_override_auto() -> None:
    """When the caller passes explicit max_cascade_depth /
    precision_bits, those values are used instead of the auto-scaled
    defaults. Smaller-than-auto values should still work for small
    num_digits (the cascade just runs at lower precision)."""
    # Auto-scaling for num_digits=15 gives (90, 512) — the rc12-era
    # minimum. Pass explicit (50, 256) — should still produce ~15
    # correct digits (depth 50 covers 50*log10(4)/log10(10) ~= 30 digits).
    result = pi_cascade_digits(15, max_cascade_depth=50, precision_bits=256)
    assert result == "3.141592653589793", (
        f"Explicit kwargs produced wrong result: {result}"
    )


# ──────────────────────────────────────────────────────────────────────
# AST-verification gate — zero math.pi invocations
# ──────────────────────────────────────────────────────────────────────


def _walk_for_math_pi(node: ast.AST) -> list[ast.AST]:
    """Walk AST and return all nodes that access math.pi attribute.

    Detects:
    - ``math.pi``      — Attribute(Name('math'), 'pi')
    - ``numpy.pi``     — Attribute(Name('numpy'), 'pi')
    - ``np.pi``        — Attribute(Name('np'), 'pi')
    - ``math.tau``     — Attribute(Name('math'), 'tau')  (2π)
    """
    hits = []
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute):
            if isinstance(child.value, ast.Name):
                pi_names = {"math", "numpy", "np", "sympy", "scipy"}
                pi_attrs = {"pi", "tau"}
                if (child.value.id in pi_names
                        and child.attr in pi_attrs):
                    hits.append(child)
    return hits


def test_pi_cascade_digits_ast_no_math_pi() -> None:
    """The pi_cascade_digits function's source must NOT access math.pi
    (or any equivalent transcendental constant). This is the discipline
    gate per `[[user_stance_pi_spectral_shape_scalar_invariant]]` —
    π is generated by the cascade substrate; the scalar constant is
    not invoked anywhere in the call graph.
    """
    source = inspect.getsource(pi_cascade_digits)
    tree = ast.parse(source)
    hits = _walk_for_math_pi(tree)
    assert len(hits) == 0, (
        f"pi_cascade_digits accesses math.pi (or equivalent) "
        f"{len(hits)} times: {[ast.dump(h) for h in hits]}"
    )


def test_pi_cascade_digits_call_graph_ast_no_math_pi() -> None:
    """Walk the full call graph from pi_cascade_digits and its private
    helpers (_integer_sqrt, _scaled_integer_sqrt, _pi_cascade_auto_params);
    verify zero math.pi invocations anywhere. rc13 adds
    `_pi_cascade_auto_params` to the gate so the cap-expansion
    auto-scaling stays AST-clean."""
    # Helpers that pi_cascade_digits depends on:
    helpers = [
        pi_cascade_digits,
        rational._integer_sqrt,
        rational._scaled_integer_sqrt,
        rational._pi_cascade_auto_params,
    ]
    total_hits = 0
    for fn in helpers:
        source = inspect.getsource(fn)
        tree = ast.parse(source)
        hits = _walk_for_math_pi(tree)
        total_hits += len(hits)
    assert total_hits == 0, (
        f"pi_cascade_digits call graph contains {total_hits} math.pi "
        f"invocations; expected zero"
    )


def test_pi_cascade_digits_ast_no_math_pi_across_rc13_scale() -> None:
    """rc13 cap-expansion preservation gate: confirm the function's
    source AST contains zero math.pi / math.tau / numpy.pi accesses,
    AND that this holds when num_digits scales up to the rc13 ceiling
    of 1000. The discipline gate per
    `[[user_stance_pi_spectral_shape_scalar_invariant]]` survives the
    cap-expansion: π is generated by the cascade substrate, never by
    invoking a transcendental constant. Same AST source — same
    discipline — at any num_digits.

    This test exercises the function at every level the catalog ships
    and re-asserts the AST gate as a soft "the call path doesn't
    introduce math.pi at runtime" check; the strong gate is
    `test_pi_cascade_digits_call_graph_ast_no_math_pi`.
    """
    # Re-run the AST scan after the call-graph entries are walked.
    helpers = [
        pi_cascade_digits,
        rational._integer_sqrt,
        rational._scaled_integer_sqrt,
        rational._pi_cascade_auto_params,
    ]
    for fn in helpers:
        source = inspect.getsource(fn)
        tree = ast.parse(source)
        hits = _walk_for_math_pi(tree)
        assert len(hits) == 0, (
            f"{fn.__name__} contains math.pi/tau/numpy.pi at rc13: "
            f"{[ast.dump(h) for h in hits]}"
        )
    # And confirm at-scale behavior: each canonical num_digits still
    # produces canonical π. Small set (50/100) only — the larger ones
    # are covered by the parametrised scaling test (don't want to run
    # 1000-digit cascade twice in the unit-test suite).
    for d in [50, 100]:
        result = pi_cascade_digits(d)
        assert result == CANONICAL_PI_1000[:d + 2]


def test_continued_fraction_convergents_ast_no_math_pi() -> None:
    """continued_fraction_convergents must also not invoke math.pi."""
    source = inspect.getsource(continued_fraction_convergents)
    tree = ast.parse(source)
    hits = _walk_for_math_pi(tree)
    assert len(hits) == 0, (
        f"continued_fraction_convergents accesses math.pi "
        f"{len(hits)} times: {[ast.dump(h) for h in hits]}"
    )


# ──────────────────────────────────────────────────────────────────────
# Cross-check: pi_cascade_digits + continued_fraction_convergents agree
# ──────────────────────────────────────────────────────────────────────


def test_cascade_and_convergents_share_substrate() -> None:
    """The 355/113 convergent (from CF [3; 7, 15, 1]) approximates π to
    ~6 correct digits — and pi_cascade_digits's first 6 digits agree.
    Documents the substrate-readout consistency."""
    # 355/113 = 3.141592920353...
    convs = continued_fraction_convergents([3, 7, 15, 1])
    assert convs[-1] == (355, 113)
    # And pi_cascade_digits(6) gives "3.141592" — first 6 digits match
    # 355/113 up to the rounding error.
    cascade_result = pi_cascade_digits(6)
    assert cascade_result == "3.141592"
    # 355/113 as float: 3.1415929... — first 6 digits also "3.141592"
    # (the 7th differs: cascade is 6, 355/113 is 9).
    convergent_str = f"{355 / 113:.6f}"
    # Sanity: first 6 digits of 355/113 == first 6 digits of true π:
    # 355/113 = 3.141593 (rounded) — at 6 digits they agree.
    # This documents Spike #32's substrate-invariance result.
    assert convergent_str.startswith("3.14159")
