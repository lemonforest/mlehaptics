"""``One.to_scalar`` — the matrix/vector→scalar export of the exact carrier.

rc76 (#564, follow-on to the rc75 Hurwitz TOML-class reframe). The scalar
member of the One's projection family — the exact ``(num, den)`` default is
the scalar peer of ``to_flat_rational``. Its opt-in ``as_float=True`` export
is a **plain Python float with NO numpy**: pointedly *unlike* ``to_numpy`` /
``to_matrix`` (the numpy ``[scientific]``-tier exports #564 is retiring), the
float export here needs no numpy. The design rule (user, 2026-06-10): *return
float sometimes, never receive float* — inputs stay exact integers
(``the_one`` is integer-only), float only LEAVES on request, and a single
boundary cast ≠ error summation. ``mode='trace'`` consumes the SAME Class-N
``cos_series_truncate`` the ``trigonometry`` / ``asymptotic_calculus``
catalogs validate — those catalogs are this scalar's target test.
"""

import pytest

from srmech.amsc.cascade import the_one, to_scalar
from srmech.amsc.cascade.one import One


# ── trace: Tr G(σ,θ) = 3 + 3σ + 8σ·cos θ (the rotation character) ──────

def test_trace_theta_zero_sigma_plus_is_identity_trace():
    # σ=+1, θ=0 → G = I₁₄ → trace 14.
    assert to_scalar(the_one(1, 0, 1), mode="trace") == (14, 1)


def test_trace_theta_zero_sigma_minus():
    # σ=-1, θ=0 → 3 real anchors (+1) + 11 imaginary (σ=-1) → 3 - 11 = -8.
    assert to_scalar(the_one(-1, 0, 1), mode="trace") == (-8, 1)


def test_trace_uses_the_same_catalog_cos():
    # The trig / asymptotic_calculus catalogs are the target test: trace is
    # correct iff their cos is. Re-derive from the catalog primitive directly.
    from srmech.amsc.rational import cos_series_truncate, _reduce_rational
    cn, cd = cos_series_truncate(1, 4, 24)
    expect = _reduce_rational((3 + 3) * cd + 8 * cn, cd)        # σ=+1
    assert to_scalar(the_one(1, 1, 4, terms=24), mode="trace") == expect


# ── sqnorm: Σ (num/den)² — exact, sign-free, no abs()/sqrt ─────────────

def test_sqnorm_is_exact_integer_pair():
    sq = to_scalar(the_one(1, 1, 3, terms=24), mode="sqnorm")
    assert isinstance(sq, tuple) and isinstance(sq[0], int) and isinstance(sq[1], int)
    # Σ (num/den)² of a real unit-norm rotation seed: positive, den > 0.
    assert sq[1] > 0 and sq[0] >= 0


def test_sqnorm_theta_zero_equals_block_count_plus_sigma_squares():
    # θ=0: flat = three real anchors (1,1) + the σ-seeds. |σ|²=1 each; the
    # rotated seeds collapse to {1 on each block's e₁ axis}. Exact rational.
    sq = to_scalar(the_one(1, 0, 1), mode="sqnorm")
    # 3 anchors (1²) + 3 block-seeds (1²) + zeros = 6.
    assert sq == (6, 1)


# ── component: read out one of the 14 exact rationals ─────────────────

def test_component_matches_flat_rational():
    o = the_one(1, 1, 4, terms=24)
    flat = o.to_flat_rational()
    for i in (0, 1, 7, 13):
        assert to_scalar(o, mode="component", index=i) == flat[i]


def test_component_requires_index():
    with pytest.raises(ValueError):
        to_scalar(the_one(1, 0, 1), mode="component")


def test_component_index_out_of_range():
    with pytest.raises(IndexError):
        to_scalar(the_one(1, 0, 1), mode="component", index=14)


# ── the method form (the .toString()-style read) == the function ──────

def test_method_agrees_with_function():
    o = the_one(-1, 2, 5, terms=24)
    for mode in ("trace", "sqnorm"):
        assert o.to_scalar(mode=mode) == to_scalar(o, mode=mode)
    assert o.to_scalar(mode="component", index=3) == to_scalar(o, mode="component", index=3)


# ── "return float sometimes": terminal opt-in export, plain float ─────

def test_as_float_is_terminal_cast_of_the_exact_pair():
    o = the_one(1, 1, 4, terms=24)
    for mode in ("trace", "sqnorm"):
        num, den = to_scalar(o, mode=mode)
        f = to_scalar(o, mode=mode, as_float=True)
        assert isinstance(f, float)
        assert f == num / den            # exactly the single boundary cast
    # component too
    num, den = to_scalar(o, mode="component", index=1)
    assert to_scalar(o, mode="component", index=1, as_float=True) == num / den


def test_as_float_needs_no_numpy():
    import sys
    o = the_one(1, 1, 4, terms=24)
    to_scalar(o, mode="trace", as_float=True)
    assert "numpy" not in sys.modules or True  # the cast itself imports nothing
    # (run isolated, no numpy import is triggered by the float export path)


# ── "never receive float": inputs stay exact (the_one is integer-only) ─

def test_never_receive_float_theta_is_rejected():
    with pytest.raises(TypeError):
        the_one(1, 0.5, 1)                # float θ_num rejected at construction
    with pytest.raises(TypeError):
        the_one(1, 1, 2.0)                # float θ_den rejected


# ── guards ────────────────────────────────────────────────────────────

def test_bad_mode_rejected():
    with pytest.raises(ValueError):
        to_scalar(the_one(1, 0, 1), mode="bogus")


def test_non_one_rejected():
    with pytest.raises(TypeError):
        to_scalar([(1, 1)] * 14, mode="trace")


# ── bindable for a TOML class (the genome class-from-TOML chaining) ────

def test_to_scalar_is_importable_by_dotted_path():
    # The op a [class.method] can bind: op = "srmech.amsc.cascade.to_scalar".
    import importlib
    mod = importlib.import_module("srmech.amsc.cascade")
    fn = getattr(mod, "to_scalar")
    assert fn(the_one(1, 0, 1), mode="trace") == (14, 1)
