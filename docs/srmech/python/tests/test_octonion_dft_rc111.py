"""0.9.0rc111 — ``cascade.octonion_dft`` GRADUATED first-class + the
qm.octonion ODFT twiddle family (issue #1234 Item 1c, re-raise of #863;
F378 / F379 / F380).

The op now stands on the qm.octonion foundation (the 8×8 ``L_a``/``R_a``
operators + the rc111 ``octonion_twiddle``) and dispatches the WHOLE O(N²)
exact-reference transform — ALL THREE forms — to the same-rc C peer
``srmech_octonion_dft`` (byte-exact composed fallback — the parity
contract, not a tolerance).

THE DECLARED BRACKETING CONVENTION under test (𝕆 non-associative → the ODFT
is NOT unique without it; the ATTESTED field, verbatim from the TOML):

    per-summand-single-product; the inverse applies the conjugate twiddle
    (σ flip) on the SAME declared side; the two-sided 3-factor association
    order is the explicit `bracketing` parameter.

The load-bearing gates this rc must hold:

  (a) ROUND-TRIP EXACT UNDER THE DECLARED CONVENTION — inverse(forward(x))
      == x, BOTH one-sided forms, several N incl. non-powers-of-2, every
      named axis incl. the e4..e7 octonion extras + diagonal + a general
      8-vector axis.
  (b) THE BRACKETING FIELD IS LOAD-BEARING, NOT DECORATIVE — a deliberately
      different bracketing yields a DIFFERENT result: the two-sided
      left/right_associated spectra DIVERGE for distinct axes, and the
      twiddle associated through a PRODUCT of two samples differs from the
      per-summand convention (W·(x·y) ≠ (W·x)·y).
  (c) THE ALTERNATIVITY FINDING (where non-associativity actually bites —
      Artin's theorem made empirical): the alternative laws a(ax)=(aa)x /
      (xa)a=x(aa) hold EXACTLY over the attested table; the same-axis
      round-trip composition conj(W)·(W·x)=x is exact; the two-sided
      bracketings COINCIDE when μ_l=μ_r (two generators) and DIVERGE for
      distinct axes (three generators); a genuine associator witness
      ((e1·e2)·e5 = −e6 ≠ +e6 = e1·(e2·e5)) pins the non-associativity as
      real.
  (d) KLEIN-4 ⊗ 2 PRESERVATION — the rc110 demo one rung up: a signal
      carrying structure in the EXTRA octonion axes (e4..e7) round-trips
      exactly through the ODFT, is REJECTED by quaternion_dft (out of ℍ),
      and is structurally lost by the ℂ projection.
  (e) LEFT ≠ RIGHT on a generic octonion signal; EXACT left==right
      degeneracy for ℝ[μ] signals; Parseval both one-sided forms.
  (f) PARITY — native whole-transform vs fully-forced-pure composed path
      BYTE-EXACT per coefficient, all three forms.
  (g) DSL — the graduated ``octonion_dft.toml`` loads + runs; the
      descriptor declares the C peer AND the attested bracketing block
      (convention + alternativity_note — the #1234 Item 1c ask).
  (h) REGISTRATION — tools.total 359 → 362 (the 3 new qm.octonion
      twiddle-family ToolEntries; the octonion_dft entry pre-existed) +
      the Rosetta bucket flips.
  (i) The qm.octonion twiddle family gates (the rc109 quaternion gates at
      dim 8): exp unit norm / addition law / conjugate inverse; twiddle
      N-th-roots closure + cyclic index reduction; series-truncate vs a
      Fraction oracle; contract errors.

numpy-free by construction (no numpy import, no ``np.``;
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""
from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path

import pytest

import srmech.amsc.cascade.hypercomplex_dft as hd
from srmech.amsc import _native
from srmech.amsc.cascade import octonion_dft, quaternion_dft
from srmech.amsc.mat import Mat
from srmech.qm import octonion as oct_mod
from srmech.qm.octonion import (
    octonion_conjugate,
    octonion_exp,
    octonion_exp_series_truncate,
    octonion_left_mult,
    octonion_norm,
    octonion_right_mult,
    octonion_twiddle,
)

ONE_SIDED = ("left", "right")
BRACKETINGS = ("left_associated", "right_associated")
NS = (1, 2, 3, 5, 7, 8, 12, 16)          # incl. non-powers-of-2 (3, 5, 7, 12)
AXES = ("i", "j", "k", "e4", "e5", "e6", "e7", "ijk", "diagonal")


def _signal(n, seed=20260703):
    """A deterministic generic octonion signal (all eight components live)."""
    rng = random.Random(seed + n)
    return [[rng.uniform(-2.0, 2.0) for _ in range(8)] for _ in range(n)]


def _max_err(a, b):
    return max(abs(x - y) for u, v in zip(a, b) for x, y in zip(u, v))


def _omul(a, b):
    """Octonion product a·b via the left operator (the attested table path)."""
    rows = octonion_left_mult(a).tolist()
    return [sum(rows[i][c] * float(b[c]) for c in range(8)) for i in range(8)]


def _force_pure(monkeypatch):
    """Force the FULLY-pure composed path: the whole-transform C peer AND the
    qm.octonion twiddle-family + loop-operator native dispatches are all
    bypassed."""
    monkeypatch.setattr(hd, "_odft_native_ready", lambda: False)
    monkeypatch.setattr(oct_mod, "_native_ready", lambda s: False)
    monkeypatch.setattr(oct_mod, "_loop_op_native_ready", lambda s: False)


# ────────────────────────────────────────────────────────────────────
# (a) Round-trips exact under the DECLARED convention
# ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("form", ONE_SIDED)
@pytest.mark.parametrize("n", NS)
def test_round_trip_both_directions(form, n):
    x = _signal(n)
    fwd_back = octonion_dft(octonion_dft(x, form=form), form=form,
                            inverse=True)
    assert _max_err(fwd_back, x) < 1e-12 * max(1, n)
    inv_fwd = octonion_dft(octonion_dft(x, form=form, inverse=True),
                           form=form)
    assert _max_err(inv_fwd, x) < 1e-12 * max(1, n)


@pytest.mark.parametrize("axis", AXES)
def test_round_trip_every_axis_non_power_of_two(axis):
    """Every named axis — including the e4..e7 octonion extras beyond ℍ —
    round-trips at a non-power-of-2 length."""
    x = _signal(7)
    got = octonion_dft(octonion_dft(x, form="right", mu_axis=axis),
                       form="right", mu_axis=axis, inverse=True)
    assert _max_err(got, x) < 1e-12


def test_round_trip_general_octonion_axis():
    """A general (non-named, e4/e6-weighted) unit axis round-trips."""
    ax = [0.0, 0.0, 0.0, 3.0, 0.0, 4.0, 0.0, 0.0]
    x = _signal(5)
    got = octonion_dft(octonion_dft(x, mu_axis=ax), mu_axis=ax, inverse=True)
    assert _max_err(got, x) < 1e-12


# ────────────────────────────────────────────────────────────────────
# (b) The bracketing field is LOAD-BEARING (a different bracketing is a
#     different transform)
# ────────────────────────────────────────────────────────────────────

def test_two_sided_bracketings_diverge_for_distinct_axes():
    """(W_l·x)·W_r vs W_l·(x·W_r) with μ_l=i, μ_r=j: three independent
    generators → the DECLARED association order changes the spectrum
    (F378). The attested field is load-bearing, not decorative."""
    x = _signal(5)
    la = octonion_dft(x, form="two_sided", bracketing="left_associated",
                      mu_axis="i", two_sided_right_axis="j")
    ra = octonion_dft(x, form="two_sided", bracketing="right_associated",
                      mu_axis="i", two_sided_right_axis="j")
    diff = _max_err(la, ra)
    assert diff > 1e-2, (
        f"distinct-axes two-sided bracketings must diverge; got {diff:.2e}")


def test_twiddle_through_sample_product_is_a_different_bracketing():
    """Deliberately associating the twiddle THROUGH a product of two samples
    — W·(x·y) vs (W·x)·y — yields a DIFFERENT result (⟨μ, x, y⟩ = three
    generators). The per-summand-single-product convention is a genuine
    declaration, not a no-op."""
    x = [2.0, 1.0, -1.0, 4.0, 0.0, -2.0, 1.0, 3.0]
    y = [0.5, 2.0, -1.5, 1.0, -0.5, 3.0, 0.0, -2.0]
    w = octonion_exp(0.7, "e5")
    w_xy = _omul(w, _omul(x, y))          # W·(x·y)
    wx_y = _omul(_omul(w, x), y)          # (W·x)·y
    diff = max(abs(a - b) for a, b in zip(w_xy, wx_y))
    assert diff > 1.0, (
        f"the through-product bracketing must differ; got {diff:.2e}")


def test_two_sided_same_axis_bracketings_coincide_the_artin_boundary():
    """With μ_l = μ_r everything lives in the TWO-generator subalgebra
    ⟨μ, x⟩, which Artin's theorem makes associative — the two bracketings
    coincide (float round-off only; the op-order differs so the match is a
    tolerance, not byte equality). The boundary demonstrated from the
    associative side."""
    x = _signal(5)
    la = octonion_dft(x, form="two_sided", bracketing="left_associated",
                      mu_axis="i", two_sided_right_axis="i")
    ra = octonion_dft(x, form="two_sided", bracketing="right_associated",
                      mu_axis="i", two_sided_right_axis="i")
    assert _max_err(la, ra) < 1e-12


def test_two_sided_inverse_raises():
    o = [[0.0] * 8 for _ in range(3)]
    with pytest.raises(NotImplementedError):
        octonion_dft(o, form="two_sided", inverse=True)


# ────────────────────────────────────────────────────────────────────
# (c) The alternativity finding — WHERE non-associativity actually bites
# ────────────────────────────────────────────────────────────────────

_Q_INT = [1.0, -2.0, 3.0, 0.0, 5.0, -1.0, 2.0, -3.0]
_X_INT = [2.0, 1.0, -1.0, 4.0, 0.0, -2.0, 1.0, 3.0]


def test_alternative_laws_hold_exactly():
    """𝕆 is ALTERNATIVE: a(ax) = (aa)x and (xa)a = x(aa) — EXACT (==) over
    the attested table at integer octonions (integer float arithmetic is
    exact). This is the algebraic ground the one-sided round-trip stands
    on."""
    a, x = _Q_INT, _X_INT
    aa = _omul(a, a)
    assert _omul(a, _omul(a, x)) == _omul(aa, x)          # left alternative
    xa = _omul(x, a)
    assert _omul(xa, a) == _omul(x, aa)                   # right alternative


def test_flexible_law_holds_exactly():
    """The flexible law a(xa) = (ax)a — the third alternative identity."""
    a, x = _Q_INT, _X_INT
    assert _omul(a, _omul(x, a)) == _omul(_omul(a, x), a)


def test_octonions_are_genuinely_non_associative():
    """The associator witness: (e1·e2)·e5 = −e6 while e1·(e2·e5) = +e6 —
    non-associativity is real (168/210 basis triples, F378), so the exact
    alternative-law and round-trip results above are NOT trivialities."""
    e = lambda i: [1.0 if j == i else 0.0 for j in range(8)]  # noqa: E731
    lhs = _omul(_omul(e(1), e(2)), e(5))
    rhs = _omul(e(1), _omul(e(2), e(5)))
    assert lhs != rhs
    assert lhs == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0]
    assert rhs == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]


@pytest.mark.parametrize("axis", ("i", "e4", "e7", "diagonal"))
def test_same_axis_round_trip_composition_is_artin_exact(axis):
    """The inverse composition conj(W)·(W·x) recovers x: W, conj(W) ∈ ℝ[μ]
    and x give TWO generators, so Artin associativity makes
    conj(W)·(W·x) = (conj(W)·W)·x = x — despite 𝕆's non-associativity.
    This is precisely why the one-sided ODFT round-trip is exact."""
    w = octonion_exp(0.7, axis)
    wc = octonion_conjugate(w)
    back = _omul(wc, _omul(w, _X_INT))
    err = max(abs(a - b) for a, b in zip(back, _X_INT))
    assert err < 1e-14


# ────────────────────────────────────────────────────────────────────
# (d) Klein-4 ⊗ 2 preservation — structure in the e4..e7 axes survives
# ────────────────────────────────────────────────────────────────────

def _enc16(s):
    """Sector s ∈ {0..15} → octonion: bit0 → sign of e1, bit1 → e2 (the ℍ
    Klein-4 pair), bit2 → e4, bit3 → e6 (the extra-axes pair beyond ℍ)."""
    q = [0.0] * 8
    q[1] = 1.0 - 2 * (s & 1)
    q[2] = 1.0 - 2 * ((s >> 1) & 1)
    q[4] = 1.0 - 2 * ((s >> 2) & 1)
    q[6] = 1.0 - 2 * ((s >> 3) & 1)
    return q


def _dec16(q):
    b0 = 0 if q[1] > 0 else 1
    b1 = 0 if q[2] > 0 else 1
    b2 = 0 if q[4] > 0 else 1
    b3 = 0 if q[6] > 0 else 1
    return b0 | (b1 << 1) | (b2 << 2) | (b3 << 3)


def test_extra_axes_structure_round_trips_exactly():
    """The rc110 Klein-4 preservation demo ONE RUNG UP: a signal carrying
    structure in the e4..e7 octonion axes (beyond ℍ — the iω₇-side
    structure) round-trips through the ODFT with every sector recovered
    exactly; the same samples are REJECTED by quaternion_dft (they are not
    quaternions) and the ℂ projection has no slots for e2..e7 at all."""
    sectors = [0, 5, 10, 15, 3, 12, 6, 9]          # all four bits toggle
    x = [_enc16(s) for s in sectors]

    # ODFT (𝕆 coefficient algebra): all four sign-carrying axes survive.
    back = octonion_dft(octonion_dft(x, form="left"), form="left",
                        inverse=True)
    assert [_dec16(q) for q in back] == sectors
    assert _max_err(back, x) < 1e-12

    # The quaternion transform CANNOT even carry these samples (e4..e7 ≠ 0).
    with pytest.raises(ValueError):
        quaternion_dft(x)

    # The ℂ projection (q0 + q1·i) structurally loses the e4/e6 channels.
    proj_back = [[q[0], q[1], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] for q in x]
    e4_loss = max(abs(a[4] - b[4]) for a, b in zip(x, proj_back))
    e6_loss = max(abs(a[6] - b[6]) for a, b in zip(x, proj_back))
    assert e4_loss == 1.0 and e6_loss == 1.0, "the ℂ shadow must lose e4/e6"


# ────────────────────────────────────────────────────────────────────
# (e) Non-commutativity + degeneracy + Parseval
# ────────────────────────────────────────────────────────────────────

def test_left_and_right_are_genuinely_different():
    x = _signal(6)
    left = octonion_dft(x, form="left")
    right = octonion_dft(x, form="right")
    assert _max_err(left, right) > 1e-2, \
        "𝕆 non-commutativity must make the left/right ODFTs differ"


@pytest.mark.parametrize("axis,slot", [("i", 1), ("e4", 4), ("e7", 7)])
def test_r_mu_signal_degenerates_to_equality(axis, slot):
    """The classic degeneracy: samples in ℝ[μ] commute with the twiddle, so
    left == right EXACTLY (same floats, not a tolerance)."""
    rng = random.Random(42)
    x = []
    for _ in range(5):
        s = [0.0] * 8
        s[0] = rng.uniform(-1, 1)
        s[slot] = rng.uniform(-1, 1)
        x.append(s)
    left = octonion_dft(x, form="left", mu_axis=axis)
    right = octonion_dft(x, form="right", mu_axis=axis)
    assert left == right


@pytest.mark.parametrize("form", ONE_SIDED)
@pytest.mark.parametrize("n", (3, 5, 8, 12))
def test_parseval_energy(form, n):
    """Σ_k ‖X[k]‖² == N·Σ_m ‖x[m]‖² (forward unscaled — 𝕆 is a composition
    algebra, ‖ab‖ = ‖a‖‖b‖, and the twiddle orthogonality runs inside
    ℝ[μ] ≅ ℂ)."""
    x = _signal(n, seed=4)
    X = octonion_dft(x, form=form)
    e_time = sum(c * c for v in x for c in v)
    e_freq = sum(c * c for v in X for c in v)
    assert e_freq == pytest.approx(n * e_time, rel=1e-12)


# ────────────────────────────────────────────────────────────────────
# (f) Python == C parity — BYTE-EXACT (the parity contract)
# ────────────────────────────────────────────────────────────────────

def test_native_symbols_present_on_native_build():
    """On a native build the rc111 symbols exist (never pure-only by
    accident). Skipped only when the whole lib is absent (pure wheel)."""
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        pytest.skip("pure-Python environment (no native lib)")
    for sym in ("srmech_octonion_dft", "srmech_octonion_exp",
                "srmech_octonion_twiddle"):
        assert hasattr(_native.LIB, sym), f"native lib lacks {sym}"


@pytest.mark.parametrize("form", ONE_SIDED)
@pytest.mark.parametrize("inverse", (False, True))
def test_native_matches_pure_byte_for_byte_one_sided(form, inverse,
                                                     monkeypatch):
    """Whichever path is active vs the FULLY-forced-pure composed path:
    IDENTICAL coefficients (==, not a tolerance) across axes and lengths."""
    cases = [(n, ax) for n in (1, 2, 3, 5, 8, 12) for ax in AXES]
    cases += [(6, [0.0, 0.0, 0.0, 3.0, 0.0, 4.0, 0.0, 0.0])]
    active = {}
    for n, ax in cases:
        key = (n, str(ax))
        active[key] = octonion_dft(_signal(n), form=form, mu_axis=ax,
                                   inverse=inverse)
    _force_pure(monkeypatch)
    for n, ax in cases:
        key = (n, str(ax))
        pure = octonion_dft(_signal(n), form=form, mu_axis=ax,
                            inverse=inverse)
        assert active[key] == pure, (
            f"octonion_dft(n={n}, form={form}, mu_axis={ax}, "
            f"inverse={inverse}) diverged native vs pure"
        )


@pytest.mark.parametrize("bracketing", BRACKETINGS)
def test_native_matches_pure_byte_for_byte_two_sided(bracketing, monkeypatch):
    """The two-sided form (the bracketing-keyed path) is byte-exact too —
    the C peer implements the SAME declared association order."""
    cases = [(n, ax) for n in (1, 2, 3, 5, 8) for ax in ("i", "e4", "diagonal")]
    active = {}
    for n, ax in cases:
        key = (n, str(ax))
        active[key] = octonion_dft(_signal(n), form="two_sided",
                                   bracketing=bracketing, mu_axis=ax,
                                   two_sided_right_axis="e5")
    _force_pure(monkeypatch)
    for n, ax in cases:
        key = (n, str(ax))
        pure = octonion_dft(_signal(n), form="two_sided",
                            bracketing=bracketing, mu_axis=ax,
                            two_sided_right_axis="e5")
        assert active[key] == pure, (
            f"two-sided octonion_dft(n={n}, mu_axis={ax}, "
            f"bracketing={bracketing}) diverged native vs pure"
        )


def test_forced_pure_path_round_trips(monkeypatch):
    """The composed pure path alone (no C at any layer) decides the transform
    completely — the co-equal-parity discipline."""
    _force_pure(monkeypatch)
    x = _signal(5)
    for form in ONE_SIDED:
        back = octonion_dft(octonion_dft(x, form=form), form=form,
                            inverse=True)
        assert _max_err(back, x) < 1e-12


# ────────────────────────────────────────────────────────────────────
# (g) DSL — the graduated TOML loads + the ATTESTED bracketing block
# ────────────────────────────────────────────────────────────────────

def test_dsl_loads_descriptor_and_runs_chain():
    from srmech import dsl
    x = _signal(4)
    via_chain = dsl.chain().then("octonion_dft", form="right",
                                 mu_axis="e5").run(x)
    direct = octonion_dft(x, form="right", mu_axis="e5")
    assert via_chain == direct


def test_descriptor_declares_the_graduation_and_c_peer():
    from srmech.dsl import get_descriptor
    desc = get_descriptor("octonion_dft")
    cascade = desc["cascade"]
    assert cascade["name"] == "octonion_dft"
    assert cascade["native"]["c_symbol"] == "srmech_octonion_dft"
    assert cascade["native"]["abi_version"] == 3
    assert "graduated" in cascade["graduation"]["tier"]
    assert set(cascade["signature"]["forms"]) == {"left", "right", "two_sided"}


def test_descriptor_bracketing_block_is_the_attested_field():
    """The #1234 Item 1c ask verbatim: the bracketing convention is an
    EXPLICIT DECLARED/ATTESTED field in the TOML descriptor — which
    parenthesisation was used, why it must be declared, and the
    alternativity finding (where non-associativity actually bites)."""
    from srmech.dsl import get_descriptor
    br = get_descriptor("octonion_dft")["cascade"]["bracketing"]
    assert "per-summand-single-product" in br["convention"]
    assert "SAME declared side" in br["convention"]
    assert br["left_associated"] == "(W_l · x) · W_r"
    assert br["right_associated"] == "W_l · (x · W_r)"
    assert br["measurably_differ"] is True
    assert "non-associative" in br["why_declared"]
    # The alternativity note: Artin / 2-generated associativity + where the
    # non-associativity actually bites (>= 3 generators).
    note = br["alternativity_note"]
    assert "ALTERNATIVE" in note and "Artin" in note
    assert "EXACTLY" in note and "distinct axes" in note


# ────────────────────────────────────────────────────────────────────
# (h) Registration / ledger
# ────────────────────────────────────────────────────────────────────

def test_tools_total_is_362():
    """rc111 adds the 3 qm.octonion twiddle-family ToolEntries (359 → 362);
    the octonion_dft ToolEntry pre-existed (v0.7.0rc31 — graduation updates
    the entry + its Rosetta bucket, it does not add a tool)."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 362


def test_rosetta_buckets():
    fixture = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = [json.loads(l) for l in
            fixture.read_text(encoding="utf-8").splitlines() if l.strip()]
    buckets = {r["defined_at"]: r["bucket"] for r in rows}
    assert buckets[
        "srmech.amsc.cascade.hypercomplex_dft.octonion_dft"
    ] == "c_dispatched"
    assert buckets["srmech.qm.octonion.octonion_exp"] == "c_dispatched"
    assert buckets["srmech.qm.octonion.octonion_twiddle"] == "c_dispatched"
    assert buckets[
        "srmech.qm.octonion.octonion_exp_series_truncate"
    ] == "bignum_reference"


def test_octonion_twiddle_family_tool_entries_registered():
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    for name in (
        "srmech.qm.octonion.octonion_exp",
        "srmech.qm.octonion.octonion_exp_series_truncate",
        "srmech.qm.octonion.octonion_twiddle",
    ):
        entry = schema.lookup(name)
        assert entry is not None
        assert entry.owner == "srmech"
        assert entry.category == "qm.octonion"


# ────────────────────────────────────────────────────────────────────
# (i) The qm.octonion twiddle family (the rc109 gates at dim 8)
# ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("axis", AXES)
def test_exp_is_unit(axis):
    w = octonion_exp(0.9, axis)
    assert len(w) == 8
    assert octonion_norm(w) == pytest.approx(1.0, abs=1e-15)


def test_exp_zero_is_identity():
    assert octonion_exp(0.0, "e6") == [1.0] + [0.0] * 7


@pytest.mark.parametrize("axis", ("i", "e4", "e7", "diagonal"))
def test_exp_same_axis_addition_law(axis):
    """exp(μθ₁)·exp(μθ₂) = exp(μ(θ₁+θ₂)) — the ℝ[μ] ≅ ℂ subalgebra."""
    t1, t2 = 0.4, 0.85
    lhs = _omul(octonion_exp(t1, axis), octonion_exp(t2, axis))
    rhs = octonion_exp(t1 + t2, axis)
    assert max(abs(a - b) for a, b in zip(lhs, rhs)) < 1e-15


@pytest.mark.parametrize("axis", ("j", "e5", "diagonal"))
def test_exp_conjugate_is_inverse(axis):
    """conj(exp(μθ)) == exp(−μθ) — the inverse-ODFT twiddle."""
    assert octonion_conjugate(octonion_exp(0.6, axis)) == \
        octonion_exp(-0.6, axis)


@pytest.mark.parametrize("n_points", (2, 3, 5, 8))
def test_twiddle_nth_roots_of_unity_closure(n_points):
    """exp(μ·2π/N)^N == 1 for several N — the DFT twiddle closure."""
    w = octonion_twiddle(1, 1, n_points, sigma=1, mu="e4")
    acc = [1.0] + [0.0] * 7
    for _ in range(n_points):
        acc = _omul(w, acc)
    ident = [1.0] + [0.0] * 7
    assert max(abs(a - b) for a, b in zip(acc, ident)) < 1e-14


def test_twiddle_zero_index_is_exact_identity():
    assert octonion_twiddle(0, 3, 7) == [1.0] + [0.0] * 7
    assert octonion_twiddle(7, 3, 7, mu="e6") == [1.0] + [0.0] * 7


def test_twiddle_reduces_indices_cyclically():
    """The Class-I jk mod N reduction: (j+N)k and jk give the SAME floats."""
    assert octonion_twiddle(2, 3, 5, mu="e5") == \
        octonion_twiddle(7, 3, 5, mu="e5")


def test_twiddle_sigma_orientations_are_conjugate():
    w_fwd = octonion_twiddle(1, 2, 7, mu="e4", sigma=-1)
    w_inv = octonion_twiddle(1, 2, 7, mu="e4", sigma=1)
    assert octonion_conjugate(w_fwd) == w_inv


@pytest.mark.parametrize("axis", (1, 4, 7))
def test_series_truncate_matches_fraction_oracle(axis):
    """The exact-rational tier against an independent Fraction Taylor sum."""
    p, q, terms = 1, 3, 8
    got = octonion_exp_series_truncate(p, q, terms, axis=axis)
    th = Fraction(p, q)
    # The series-truncate contract sums terms k = 0..num_terms INCLUSIVE
    # (the rc109 oracle convention).
    cos_o = sum((-1) ** m * th ** (2 * m) /
                Fraction(_fact(2 * m)) for m in range(terms + 1))
    sin_o = sum((-1) ** m * th ** (2 * m + 1) /
                Fraction(_fact(2 * m + 1)) for m in range(terms + 1))
    assert Fraction(*got[0]) == cos_o
    assert Fraction(*got[axis]) == sin_o
    for slot in range(1, 8):
        if slot != axis:
            assert got[slot] == (0, 1)


def _fact(n):
    out = 1
    for i in range(2, n + 1):
        out *= i
    return out


def test_series_tier_agrees_with_float_tier():
    """The bignum series tier converges to the Q61/float twiddle."""
    got = octonion_exp_series_truncate(1, 3, 20, axis=5)
    w = octonion_exp(1.0 / 3.0, "e5")
    assert float(Fraction(*got[0])) == pytest.approx(w[0], abs=1e-12)
    assert float(Fraction(*got[5])) == pytest.approx(w[5], abs=1e-12)


def test_exp_and_twiddle_contract_errors():
    with pytest.raises(ValueError):
        octonion_exp(float("nan"), "i")
    with pytest.raises(ValueError, match="diagonal"):
        octonion_exp(0.1, "z")
    with pytest.raises(ValueError):
        octonion_exp(0.1, [1.0, 1.0, 0, 0, 0, 0, 0, 0])   # e0 != 0
    with pytest.raises(ValueError):
        octonion_exp(0.1, [0.0] * 8)                       # zero axis
    with pytest.raises(ValueError):
        octonion_twiddle(-1, 0, 4)
    with pytest.raises(ValueError):
        octonion_twiddle(0, 0, 0)
    with pytest.raises(ValueError):
        octonion_twiddle(0, 0, 4, sigma=2)
    with pytest.raises(ValueError):
        octonion_exp_series_truncate(1, 3, 4, axis=8)


# ────────────────────────────────────────────────────────────────────
# Carrier + contract hygiene
# ────────────────────────────────────────────────────────────────────

def test_real_mat_input_accepted():
    x = _signal(4)
    m = Mat.from_rows(x, is_complex=False)
    assert octonion_dft(m) == octonion_dft(x)


def test_complex_mat_input_rejected():
    m = Mat.from_rows([[1 + 1j] + [0] * 7], is_complex=True)
    with pytest.raises(ValueError):
        octonion_dft(m)


def test_quaternion_samples_zero_extend():
    """4-component samples embed as ℍ ⊂ 𝕆 (the rc31 contract preserved)."""
    q4 = [[0.5, -1.0, 0.25, 0.75], [1.0, 0.0, -0.5, 0.5]]
    q8 = [v + [0.0] * 4 for v in q4]
    assert octonion_dft(q4) == octonion_dft(q8)


def test_contract_errors_preserved():
    with pytest.raises(ValueError):
        octonion_dft([[1.0, 2.0, 3.0]])                  # not a 4/8-vector
    with pytest.raises(ValueError):
        octonion_dft([[0] * 8], form="bogus")
    with pytest.raises(ValueError):
        octonion_dft([[0] * 8], bracketing="middle")
    with pytest.raises(ValueError, match="diagonal"):
        octonion_dft([[0.0] * 8], mu_axis="z")
    assert octonion_dft([]) == []
