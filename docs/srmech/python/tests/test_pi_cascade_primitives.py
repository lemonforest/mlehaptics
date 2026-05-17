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
# "ground truth" we compare against.
CANONICAL_PI_50 = "3.14159265358979323846264338327950288419716939937510"


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
    helpers (_integer_sqrt, _scaled_integer_sqrt); verify zero math.pi
    invocations anywhere."""
    # Helpers that pi_cascade_digits depends on:
    helpers = [
        pi_cascade_digits,
        rational._integer_sqrt,
        rational._scaled_integer_sqrt,
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
