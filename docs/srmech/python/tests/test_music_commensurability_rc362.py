"""v0.9.0rc362 — the acoustic/music domain slice, plus the two shipped defects
it exposed.

Covers, in order:

1. ``Qalg.__eq__`` scalar coercion (the defect: same value, three spellings,
   two answers) + the ``is_rational`` / ``as_rational`` oracle it enables.
2. ``pin_slot_at_zero`` origin type preservation (the Class-K float leak) and
   the ``magnitude`` it composes.
3. The TIER TAG — Tier 1 / Tier 2 inferred, Tier 3 DECLARED.
4. The commensurability verdict that CAN return "inharmonic", and the
   ``common_period`` guard that makes silent harmonisation unreachable.
   Includes the MEASURED demonstration of the corruption being guarded against
   (``[[feedback_computational_provenance_discipline]]`` — the generating code
   for every load-bearing number is right here, not in prose).
5. The four constructors, each at its declared tier.
6. The promoted Bessel primitives and their C peer's bit-parity.
7. The config-TOML domain-naming layer.

numpy-free; no ``abs()``; every exactness claim is asserted on an exact carrier,
never on a float.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srmech.cascade.atoms import magnitude, pin_slot_at_zero
from srmech.math.q import Q
from srmech.math.qalg import Qalg
from srmech import music

_HERE = Path(__file__).resolve().parent
# rc364: moved out of tests/data/ into the shipped alias catalog (ADR-0010 amendment B).
# rc362 landed the tree's first [[alias]] descriptor here by DEFAULT rather than by
# decision — there was no ALIAS_CATALOG_DIR to land it in — and tests/** is not in the
# wheel, so it shipped to nobody.
from srmech.dsl import ALIAS_CATALOG_DIR                     # noqa: E402
_ALIAS_TOML = ALIAS_CATALOG_DIR / "music_domain_aliases.toml"

_X2_MINUS_2 = [-2, 0, 1]


# ── 1. Qalg.__eq__ coercion ─────────────────────────────────────────────────

def test_qalg_eq_coerces_int_and_q_like_the_ring_ops_do():
    """THE DEFECT: ``Qalg.alpha([-2,0,1])**2`` has coords ``(Q(2,1), Q(0,1))``
    — the field element 2 — yet compared True against ``Qalg.rational(2, m)``
    and False against both ``2`` and ``Q(2,1)``. ``__mul__``/``__add__``
    already coerced an exact-rational scalar; ``__eq__`` did not."""
    two = Qalg.alpha(_X2_MINUS_2) ** 2
    assert two.coords == (Q(2, 1), Q(0, 1))
    assert two == Qalg.rational(2, _X2_MINUS_2)      # always worked
    assert two == 2                                   # was False
    assert two == Q(2, 1)                             # was False
    assert 2 == two                                   # reflected
    assert Q(2, 1) == two
    assert two != 3
    assert two != Q(5, 2)


def test_qalg_eq_does_not_flatten_an_irrational_onto_a_scalar():
    """Coercion must not become sloppiness: α itself is NOT 2, and no scalar
    can equal an element with a nonzero coordinate above α⁰."""
    alpha = Qalg.alpha(_X2_MINUS_2)
    assert alpha != 2
    assert alpha != Q(3, 2)
    assert not alpha.is_rational()
    assert alpha.as_rational() is None


def test_qalg_hash_matches_eq_for_rational_elements():
    """The Python data model requires equal objects to hash equal; the rc362
    coercion would otherwise have broken dict/set behaviour."""
    two = Qalg.alpha(_X2_MINUS_2) ** 2
    assert hash(two) == hash(2) == hash(Q(2, 1))
    assert len({two, 2, Q(2, 1)}) == 1
    # A non-rational element cannot equal any scalar, so it keeps its own bucket.
    assert len({Qalg.alpha(_X2_MINUS_2), 2}) == 2


def test_qalg_eq_is_total_across_fields_and_foreign_types():
    """``==`` is a total predicate (unlike ``+``/``*``, which legitimately
    raise on a field mismatch, because the RESULT would be ill-defined)."""
    assert Qalg.rational(2, _X2_MINUS_2) != Qalg.rational(2, [-3, 0, 1])
    assert Qalg.rational(2, _X2_MINUS_2) != "two"
    with pytest.raises(ValueError):
        Qalg.alpha(_X2_MINUS_2) * Qalg.alpha([-3, 0, 1])


def test_qalg_is_rational_is_the_decidable_oracle_on_equal_temperament():
    """THE MEASURED CASE the whole verdict rests on: in ℚ[x]/(x¹²−2), s⁰ is
    rational, s¹…s¹¹ are ALL irrational, s¹² is rational."""
    m = [-2] + [0] * 11 + [1]
    s = Qalg.alpha(m)
    power = s.one()
    rationality = []
    for _k in range(13):
        rationality.append(power.is_rational())
        power = power * s
    assert rationality[0] is True
    assert rationality[12] is True
    assert all(r is False for r in rationality[1:12])


def test_qalg_still_rejects_a_non_integer_minimal_polynomial():
    """Tier 3 has no exact carrier BY CONSTRUCTION — a transcendental cannot be
    smuggled in as if it were exact."""
    with pytest.raises(ValueError):
        Qalg.alpha([Q(-1, 2), 0, 1])


# ── 2. the Class-K origin float leak ────────────────────────────────────────

def test_pin_slot_at_zero_origin_preserves_the_input_carrier():
    """THE DEFECT: the origin branch ended ``return 0, 0.0`` unconditionally,
    so the ONE op that exists to replace ``abs()`` leaked a float at exactly
    the phase boundary it is named for — while every other input kept its
    type."""
    orientation, mag = pin_slot_at_zero(0)
    assert (orientation, mag) == (0, 0)
    assert type(mag) is int                       # was float

    orientation, mag = pin_slot_at_zero(Q(0, 1))
    assert orientation == 0 and mag == Q(0, 1)
    assert type(mag) is Q                         # was float


def test_pin_slot_at_zero_nonzero_branches_are_unchanged():
    assert pin_slot_at_zero(5) == (+1, 5)
    assert pin_slot_at_zero(-3) == (-1, 3)
    assert type(pin_slot_at_zero(5)[1]) is int
    assert pin_slot_at_zero(Q(3, 2)) == (+1, Q(3, 2))
    assert type(pin_slot_at_zero(Q(3, 2))[1]) is Q


def test_pin_slot_at_zero_float_dead_band_is_bit_identical():
    """``float`` must not move: that path also carries NaN and signed zero,
    whose documented Class-K dead-band reading is ``0.0`` and must stay
    bit-identical to the native C peer."""
    for value in (0.0, -0.0, float("nan")):
        orientation, mag = pin_slot_at_zero(value)
        assert orientation == 0
        assert type(mag) is float
        assert mag == 0.0
    assert pin_slot_at_zero(float("inf")) == (+1, float("inf"))
    assert pin_slot_at_zero(float("-inf")) == (-1, float("inf"))


def test_magnitude_inherits_the_origin_fix_and_stays_type_preserving():
    assert magnitude(0) == 0 and type(magnitude(0)) is int
    assert magnitude(Q(0, 1)) == Q(0, 1) and type(magnitude(Q(0, 1))) is Q
    assert magnitude(-3) == 3 and type(magnitude(-3)) is int
    assert magnitude(Q(-3, 2)) == Q(3, 2)
    assert magnitude(-2.5) == 2.5 and type(magnitude(-2.5)) is float


def test_class_k_atoms_are_annotated_for_the_carriers_they_actually_accept():
    """DOC-1: both were annotated ``float``-only despite being type-preserving,
    which discouraged the exact-carrier use the ``abs()`` ban requires."""
    from srmech.cascade import atoms
    # ``from __future__ import annotations`` keeps these as source strings, so
    # the assertion is a containment check rather than an equality one.
    assert "Real" in atoms.pin_slot_at_zero.__annotations__["x"]
    assert "Real" in atoms.pin_slot_at_zero.__annotations__["return"]
    assert "Real" in atoms.magnitude.__annotations__["x"]
    assert "Real" in atoms.magnitude.__annotations__["return"]
    assert "float" not in atoms.magnitude.__annotations__["return"]


# ── 3. the TIER TAG ─────────────────────────────────────────────────────────

def test_tier_1_is_inferred_from_an_exact_rational_carrier():
    tag = music.spectrum_tier([Q(1, 1), Q(3, 2), 2])
    assert tag["tier"] == 1 and tag["tier_name"] == "rational"
    assert tag["exact"] is True
    assert tag["open_indices"] == () and tag["open_reason"] is None
    assert all(row["in_rationals"] is True for row in tag["per_partial"])


def test_tier_2_is_inferred_from_an_exact_algebraic_irrational_carrier():
    """Tier 2 is still EXACT and still decidable — ``α² == 2`` holds in the
    field, which the rc362 coercion is what lets us assert directly."""
    alpha = Qalg.alpha(_X2_MINUS_2)
    assert alpha * alpha == 2
    tag = music.spectrum_tier([Q(1, 1), alpha])
    assert tag["tier"] == 2 and tag["tier_name"] == "algebraic"
    assert tag["exact"] is True
    assert tag["per_partial"][1]["field_degree"] == 2
    assert tag["per_partial"][1]["in_rationals"] is False


def test_tier_3_must_be_declared_and_reports_undecided_not_false():
    """Tier 3 CANNOT be inferred: a rational standing in for a transcendental
    is, as a carrier, just a rational. So the tier is declared, and the
    partial's ℚ-membership reads ``None`` (UNDECIDED), never ``False``."""
    tag = music.spectrum_tier([Q(1, 1), Q(22, 7)], open_partials=[1])
    assert tag["tier"] == 3 and tag["tier_name"] == "open"
    assert tag["exact"] is False
    assert tag["open_indices"] == (1,)
    assert "DECLARED PRECISION" in tag["open_reason"]
    assert tag["per_partial"][1]["in_rationals"] is None
    # Without the declaration the very same carrier reads Tier 1 — which is
    # exactly why the declaration has to exist.
    assert music.spectrum_tier([Q(1, 1), Q(22, 7)])["tier"] == 1


def test_float_ratios_are_refused_because_every_float_is_a_rational():
    for op in (music.spectrum_tier, music.commensurability_verdict,
               music.common_period):
        with pytest.raises(TypeError, match="float"):
            op([1.0, 1.5])


def test_spectrum_tier_rejects_an_empty_or_non_sequence_spectrum():
    with pytest.raises(ValueError):
        music.spectrum_tier([])
    with pytest.raises(TypeError):
        music.spectrum_tier(42)
    with pytest.raises(ValueError):
        music.spectrum_tier([Q(1, 1)], open_partials=[7])


# ── 4. the verdict + the guard ──────────────────────────────────────────────

def test_verdict_returns_inharmonic_for_equal_temperament():
    """THE CORE CAPABILITY. Class-I gcd/lcm structurally cannot reach this
    answer; the field-degree oracle decides it outright."""
    ratios = music.equal_temperament_partials()["ratios"]
    verdict = music.commensurability_verdict(ratios)
    assert verdict["verdict"] == "inharmonic"
    assert verdict["rational_rank"] == 2            # only s⁰ and s¹²
    assert verdict["n_partials"] == 13
    assert verdict["incommensurable"] == tuple(range(1, 12))
    assert verdict["period_multiplier"] is None
    assert verdict["tier"] == 2


def test_verdict_returns_harmonic_at_the_octave_only():
    """The same field, the same oracle, the opposite answer — so the verdict is
    reading the spectrum and not merely reporting its own construction."""
    octave_only = music.equal_temperament_partials(degrees=[0, 12])["ratios"]
    verdict = music.commensurability_verdict(octave_only)
    assert verdict["verdict"] == "harmonic"
    assert verdict["integer_series"] is True
    assert verdict["period_multiplier"] == 1
    assert music.common_period(octave_only) == 1


def test_verdict_separates_commensurable_from_the_integer_series():
    """Two questions, one word. A tuned bell is called *inharmonic* by
    acousticians (not the integer series) yet is exactly COMMENSURABLE."""
    ratios = music.bell_partials()["ratios"]
    verdict = music.commensurability_verdict(ratios)
    assert verdict["verdict"] == "harmonic"
    assert verdict["integer_series"] is False
    assert verdict["period_multiplier"] == 10       # lcm(2, 1, 5, 2, 1)
    # The plain integer series answers True to both.
    plain = music.commensurability_verdict([1, 2, 3, 4, 5])
    assert plain["verdict"] == "harmonic" and plain["integer_series"] is True


def test_verdict_returns_open_and_never_harmonic_for_a_declared_tier_3():
    ratios = [Q(1, 1), Q(22, 7), Q(355, 113)]
    verdict = music.commensurability_verdict(ratios, open_partials=[1, 2])
    assert verdict["verdict"] == "open"
    assert verdict["tier"] == 3
    assert verdict["period_multiplier"] is None
    # The identical carriers, undeclared, would have read "harmonic" with a
    # perfectly finite period — the silent harmonisation, exhibited.
    undeclared = music.commensurability_verdict(ratios)
    assert undeclared["verdict"] == "harmonic"
    assert undeclared["period_multiplier"] == 7 * 113


def test_common_period_refuses_to_manufacture_a_period():
    """THE GUARD. A period is obtainable only by earning the verdict first."""
    et = music.equal_temperament_partials()["ratios"]
    with pytest.raises(ValueError, match="INHARMONIC"):
        music.common_period(et)
    with pytest.raises(ValueError, match="OPEN"):
        music.common_period([Q(1, 1), Q(22, 7)], open_partials=[1])


def test_the_class_n_fallback_really_does_convert_inharmonic_to_harmonic():
    """MEASURED, with its generating code committed
    (``[[feedback_computational_provenance_discipline]]``).

    This is the corruption ``common_period`` guards against, exhibited rather
    than asserted in prose: read an irrational spectral ratio with Class-N
    ``best_rational`` at a rising denominator ceiling and you do not get a
    better approximation of "inharmonic" — you get a *finite period*, which IS
    commensurability IS harmonicity. Raising the ceiling only buys a longer
    FALSE period. The convergent denominators diverge monotonically and never
    close, which is the tell.
    """
    from srmech.math.rational import best_rational, continued_fraction

    # A rational target LOCKS: the same answer at every ceiling. This is the
    # control that proves the instrument can return something else.
    for max_den in (2, 10, 10 ** 3, 10 ** 9):
        assert best_rational(3, 2, max_den) == (3, 2)
    assert continued_fraction(3, 2) == [1, 2]

    # An irrational target (π, scaled to an exact integer pair) never locks —
    # and every anchor it does return is a finite period T₀·q.
    pi_num, pi_den = 314159265358979323846, 10 ** 20
    anchors = [best_rational(pi_num, pi_den, max_den)
               for max_den in (10 ** 2, 10 ** 4, 10 ** 6, 10 ** 7)]
    # MEASURED on this exact input, at rc362. (A lower-precision pi yields a
    # different third anchor — 2917129/928551 — which is why the target is
    # spelled out as an exact integer pair here rather than described: the
    # anchor is a function of the INPUT precision as much as of max_den, and
    # that is itself part of the point.)
    assert anchors == [(22, 7), (355, 113), (1146408, 364913),
                       (5419351, 1725033)]
    induced_periods = [q for _p, q in anchors]
    # Strictly increasing, never repeating: no ceiling ever reaches a verdict,
    # it only buys a longer false period.
    assert induced_periods == sorted(induced_periods)
    assert len(set(induced_periods)) == len(induced_periods)

    # And the corresponding spectrum reads as flatly "harmonic" with a
    # perfectly finite period — the silent conversion, in one line.
    faked = music.commensurability_verdict([Q(1, 1), Q(355, 113)])
    assert faked["verdict"] == "harmonic"
    assert faked["period_multiplier"] == 113


def test_the_verdict_carries_the_standing_notes_about_the_two_old_gauges():
    verdict = music.commensurability_verdict([1, 2])
    assert "always has an lcm" in verdict["class_i_note"]
    assert "CONVERTS" in verdict["class_n_warning"]


# ── 5. the four constructors ────────────────────────────────────────────────

def test_bell_partials_is_tier_1_with_the_founders_vocabulary():
    bell = music.bell_partials()
    assert bell["tier"] == 1
    assert bell["names"] == ("hum", "prime", "tierce", "quint", "nominal")
    assert bell["ratios"] == (Q(1, 2), Q(1, 1), Q(6, 5), Q(3, 2), Q(2, 1))
    assert "Fletcher" in bell["cite_as"]
    assert music.spectrum_tier(bell["ratios"])["tier"] == 1


def test_stiff_string_at_zero_stiffness_recovers_the_ideal_string_exactly():
    """The built-in control: B == 0 collapses every radicand to n², so the
    Tier-2 constructor degenerates to Tier 1 and the plain integer series."""
    string = music.stiff_string_partials(0, n_partials=6)
    assert string["tier"] == 1
    assert string["ratios"] == tuple(Q(n, 1) for n in range(1, 7))
    verdict = music.commensurability_verdict(string["ratios"])
    assert verdict["verdict"] == "harmonic"
    assert verdict["integer_series"] is True
    assert music.common_period(string["ratios"]) == 1


def test_stiff_string_with_rational_stiffness_is_tier_2_and_exact():
    """``f_n = n·f₀·√(1 + B n²)`` with B rational ⇒ each ratio is a quadratic
    surd, carried EXACTLY: squaring it returns the radicand on the nose."""
    string = music.stiff_string_partials(Q(1, 1000), n_partials=6)
    assert string["tier"] == 2
    for ratio, radicand in zip(string["ratios"], string["radicands"]):
        assert ratio * ratio == radicand           # exact, no tolerance
    verdict = music.commensurability_verdict(string["ratios"])
    assert verdict["verdict"] == "inharmonic"
    assert verdict["rational_rank"] == 0
    assert verdict["field_degrees"] == (2,) * 6
    with pytest.raises(ValueError, match="INHARMONIC"):
        music.common_period(string["ratios"])


def test_stiff_string_refuses_a_float_and_a_negative_stiffness():
    with pytest.raises(TypeError, match="EXACT"):
        music.stiff_string_partials(0.001)
    with pytest.raises(ValueError):
        music.stiff_string_partials(Q(-1, 10))
    with pytest.raises(ValueError):
        music.stiff_string_partials(0, n_partials=0)


def test_equal_temperament_refuses_a_reducible_pure_radical():
    """``x⁴ − 4`` is reducible, so ℚ[x]/(x⁴−4) is not a field and the
    ℚ-membership oracle would be meaningless. Refuse rather than answer from a
    broken carrier."""
    with pytest.raises(ValueError, match="REDUCIBLE"):
        music.equal_temperament_partials(divisions=4, octave=4)
    # …but the Eisenstein-clean case is fine.
    ok = music.equal_temperament_partials(divisions=4, octave=2)
    assert ok["minimal_polynomial"] == (-2, 0, 0, 0, 1)
    assert ok["field_degree"] == 4


def test_membrane_partials_declare_tier_3_and_assert_nothing():
    membrane = music.membrane_partials(n_orders=2, m_zeros=2, scale_bits=96)
    assert membrane["tier"] == 3
    assert membrane["declared_precision_only"] is True
    assert membrane["transcendence_claim"].startswith("NONE")
    assert "Siegel" in membrane["transcendence_claim"]
    assert membrane["open_partials"] == tuple(range(len(membrane["ratios"])))
    assert membrane["modes"] == ((0, 1), (0, 2), (1, 1), (1, 2))
    # The first ratio is exactly 1 (the fundamental over itself), exactly.
    assert membrane["ratios"][0] == Q(1, 1)
    verdict = music.commensurability_verdict(
        membrane["ratios"], open_partials=membrane["open_partials"])
    assert verdict["verdict"] == "open"
    with pytest.raises(ValueError, match="OPEN"):
        music.common_period(membrane["ratios"],
                            open_partials=membrane["open_partials"])


def test_membrane_mode_ratios_land_on_the_known_values():
    """Corroboration only, at a terminal float readout — NOT an attestation.
    j₁₁/j₀₁ ≈ 3.8317/2.4048 ≈ 1.5933 and j₀₂/j₀₁ ≈ 5.5201/2.4048 ≈ 2.2954."""
    membrane = music.membrane_partials(n_orders=2, m_zeros=2, scale_bits=96)
    lookup = dict(zip(membrane["modes"], membrane["ratios"]))
    # ONE terminal FPU lift, at the readout, after the whole body stayed exact.
    def _readout(q):
        return q.numerator / q.denominator
    assert _readout(lookup[(0, 2)]) == pytest.approx(2.295417, abs=1e-5)
    assert _readout(lookup[(1, 1)]) == pytest.approx(1.593341, abs=1e-5)
    assert _readout(lookup[(1, 2)]) == pytest.approx(2.917295, abs=1e-5)


# ── 6. the promoted Bessel primitives + C parity ────────────────────────────

def test_bessel_j_fixed_hits_the_exact_series_endpoints():
    scale = 1 << 64
    assert music.bessel_j_fixed(0, 0, 1, scale_bits=64) == (scale, scale)  # J₀(0)=1
    for order in (1, 2, 5):
        num, den = music.bessel_j_fixed(order, 0, 1, scale_bits=64)
        assert (num, den) == (0, scale)                                    # Jₖ(0)=0


def test_bessel_zero_residual_is_tiny_at_the_declared_precision():
    """The zero is a rational OF DECLARED PRECISION; the honest statement of
    its quality is its residual, which is reported, not assumed."""
    zero = music.bessel_zero_fixed(0, 1, scale_bits=128)
    residual = Q(*music.bessel_j_fixed(0, zero[0], zero[1], scale_bits=128))
    bound = Q(1, 10 ** 30)
    assert magnitude(residual) < bound
    # …and the value itself matches the classical first zero of J₀.
    assert zero[0] / zero[1] == pytest.approx(2.404825557695773, abs=1e-12)


def test_bessel_zeros_interlace_per_watson_15_22():
    """Watson (1922) §15.22 interlacing: j_{n,m} < j_{n+1,m} < j_{n,m+1}."""
    zeros = {}
    for n in range(3):
        for m in range(1, 4):
            num, den = music.bessel_zero_fixed(n, m, scale_bits=96)
            zeros[(n, m)] = Q(num, den)
    for n in range(2):
        for m in range(1, 3):
            assert zeros[(n, m)] < zeros[(n + 1, m)] < zeros[(n, m + 1)]


def test_bessel_j_fixed_domain_errors():
    with pytest.raises(ValueError, match="Class-K"):
        music.bessel_j_fixed(0, -1, 1)
    with pytest.raises(ValueError):
        music.bessel_j_fixed(-1, 1, 1)
    with pytest.raises(ValueError):
        music.bessel_j_fixed(0, 1, 0)
    with pytest.raises(ValueError):
        music.bessel_j_fixed(0, 1, 1, scale_bits=4)
    with pytest.raises(ValueError):
        music.bessel_zero_fixed(0, 0)


def test_bessel_c_peer_is_bit_identical_to_the_python_body():
    """1:1 C:Python parity for the one NEW numerical kernel this rc ships.

    The C peer is bit-identical BY CONSTRUCTION, not by luck: the running term
    is a non-negative magnitude and the alternating sign is an explicit Class-K
    orientation applied at the accumulation, so no shift or divide ever sees a
    negative operand and C truncation cannot diverge from Python floor. When
    the native lib is absent this degrades to a pure-Python self-check that
    still exercises the whole body.
    """
    from srmech import _native
    from srmech.music import _bessel

    cases = [(order, p, q, sb)
             for order in (0, 1, 2, 3, 5, 8)
             for (p, q) in ((0, 1), (1, 1), (1, 2), (5, 2), (24048, 10000),
                            (31, 7), (100, 3))
             for sb in (32, 64, 128)]

    saved = _native.bessel_j_fixed_c
    try:
        for order, p, q, scale_bits in cases:
            native = saved(order, p, q, scale_bits)
            _native.bessel_j_fixed_c = lambda *_a, **_k: None
            pure_num, pure_den = _bessel.bessel_j_fixed(
                order, p, q, scale_bits=scale_bits)
            _native.bessel_j_fixed_c = saved
            assert pure_den == 1 << scale_bits
            if native is not None:
                assert native == pure_num, (
                    f"C/Python divergence at order={order} x={p}/{q} "
                    f"scale_bits={scale_bits}")
    finally:
        _native.bessel_j_fixed_c = saved


# ── 7. the config-TOML domain-naming layer ──────────────────────────────────

def test_domain_names_are_a_toml_binding_over_the_general_ops():
    """The domain word is CONFIG, not source: change the TOML entry and the
    domain-referenced name changes with no source edit and no recompile."""
    from srmech.dsl import load_aliases_toml

    names = load_aliases_toml(_ALIAS_TOML)
    assert names["partials"]() == music.bell_partials()
    assert names["exactness"]([1, 2]) == music.spectrum_tier([1, 2])
    assert names["overtone_period"]([1, 2, 4]) == music.common_period([1, 2, 4])
    assert names["is_inharmonic"](
        music.equal_temperament_partials()["ratios"])["verdict"] == "inharmonic"
    # Each alias records what it binds to, so the layer is introspectable.
    assert names["partials"].srmech_alias_target == "srmech.music.bell_partials"


def test_rebinding_a_domain_name_needs_no_source_change():
    from srmech.dsl import build_aliases_from_toml_str

    spec = ('[[alias]]\nname = "teilton"\n'
            'target = "srmech.music.bell_partials"\n')
    names = build_aliases_from_toml_str(spec)
    assert names["teilton"]()["names"][2] == "tierce"


# ── the naming boundary this package must not cross ─────────────────────────

def test_music_never_collides_with_the_chirality_sense_of_harmonic():
    """``classify_harmonic`` is NOT acoustic — it maps an A–N class letter to
    its chirality order. Nothing in ``srmech.music`` shadows or imports it, and
    the two surfaces answer entirely different questions."""
    from srmech.music import harmonics

    # It answers a CHIRALITY question: which of the three HARMONIC_PARTITION
    # rungs an A-N class letter sits on. Its whole codomain is {1, 2, 3}, and
    # its domain is a class letter — neither is a frequency in any sense.
    rungs = {c: harmonics.classify_harmonic(c) for c in harmonics.ALL_CLASS_LETTERS}
    assert set(rungs.values()) == {1, 2, 3}
    assert rungs["A"] == 1 and rungs["I"] == 3
    for rung, letters in harmonics.HARMONIC_PARTITION.items():
        assert all(rungs[c] == rung for c in letters)
    assert "classify_chirality_harmonic" in harmonics.__all__

    # No name is shared between the two surfaces, in either direction.
    assert not (set(music.__all__) & set(harmonics.__all__))
    assert "classify_harmonic" not in music.__all__
    assert not any(name.startswith("classify_") for name in music.__all__)
