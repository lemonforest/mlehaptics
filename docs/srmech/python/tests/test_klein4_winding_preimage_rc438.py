"""rc438 (`#T1140`, gh #1530 §G) — the ONE-A14 coupling reads the WHOLE One.

Through rc437 both coupling minters built their Class-A preimage from THREE of
the One's four declared constructor fields and silently dropped the fourth. The
winding triad has been a declared, PINNED parameter of ``cascade.the_one`` since
rc408 (`#T1078`) and has been serialised by ``One._to_jsonable()`` since rc414
(`#T1092`) — so ``klein4_from_one``'s own shipped promise, "a DECLARED FUNCTION
of the ``One``'s ... constructor integers", was false of every wound One.

THE DEFECT, AS MEASURED AT rc437. Over ``w ∈ [-4,4]³`` — **729** distinct
windings with σ/θ/terms held fixed — all three coupling surfaces returned **one
distinct value out of 729**:

  * ``klein4_from_one``                     1/729
  * ``q8_from_one`` V4 coset plane          1/729 (it IS ``klein4_from_one``)
  * ``q8_from_one`` **Z₂ sign plane**       1/729 — and it has its OWN preimage

That is a measured zero and not a dead instrument, which is the whole reason
:func:`test_the_instrument_moves_on_every_other_declared_axis` is in this file
rather than in a comment: the SAME ops, on their other axes, separate 40
distinct θ into 40 couplings, 2 σ into 2 and 20 ``terms`` into 20. A zero with
no working control is an unread dial (`[[feedback_an_instrument_that_cannot_
return_otherwise_is_not_a_measurement]]`).

BOTH PLANES MOVED IN ONE RC, AND THAT WAS NOT OPTIONAL. Fixing only the V4
plane would leave a HALF-WOUND Q₈ coupling — winding-bearing cosets over
winding-blind signs. It would not have been caught downstream, because the
documented bridge ``q8_project_v4(q8_from_one(one, D)) == klein4_from_one(one,
D)`` would still hold, and go on certifying the incoherent object.

⚠️ WHAT THIS RC DOES **NOT** BUY, gated here so no reader has to take it on
trust. It buys a COMMITMENT, not a READ. Two tests measure the ceiling
directly: :func:`test_sha_avalanche_destroys_adjacency_so_no_local_read_exists`
and :func:`test_the_stored_strand_carries_zero_bits_about_its_key`. Nothing
here lets a reader recover ``w`` from stored bytes, and that is
information-theoretic rather than a difficulty claim.

AND THE COST, gated rather than left to be discovered:
:func:`test_unwound_ones_are_byte_identical_to_the_rc437_preimage` and
:func:`test_wound_ones_mint_differently_which_is_the_whole_point` are the two
halves of a REGIME-SELECTIVE invalidation. Nothing on disk records that a
genome was minted wound, so no audit can enumerate the affected set — that
follows from the no-sidecar discipline and is permanent.
"""

from __future__ import annotations

import itertools
import json

import pytest

import srmech._native as _native
from srmech.biology.q8 import q8_from_one, q8_project_v4
from srmech.cascade.one import the_one
from srmech.math.hdc import (klein4_address, klein4_bind, klein4_from_one,
                             klein4_match_count, klein4_sector_frame)
from srmech.math.q import Q

D = 64

#: ``w ∈ [-4,4]³`` — the grid the defect was measured on. 729 distinct windings
#: with σ/θ/terms held fixed, so winding is the ONLY thing that varies.
WINDING_GRID = tuple(itertools.product(range(-4, 5), repeat=3))

requires_native = pytest.mark.skipif(
    not _native.HAS_NATIVE, reason="no libsrmech loaded (pure-only host)")


# ── helpers: read each surface as plain bytes ──────────────────────────────

def _k4(one) -> bytes:
    return bytes(int(c) & 3 for c in klein4_from_one(one, D))


def _q8(one) -> bytes:
    return bytes(int(c) & 7 for c in q8_from_one(one, D))


def _q8_v4_plane(one) -> bytes:
    return bytes(q8_project_v4(_q8(one)))


def _q8_sign_plane(one) -> bytes:
    return bytes((c >> 2) & 1 for c in _q8(one))


def _rc437_preimage_coupling(sigma, tn, td, terms) -> bytes:
    """The rc437 coupling, rebuilt from its LITERAL preimage shape.

    Deliberately NOT a call into the current op with a rest One: this is the
    pre-rc438 serialisation written out, so "unwound Ones are byte-identical"
    is a comparison against the old bytes rather than against ourselves.
    """
    pre = json.dumps({"sigma": sigma, "terms": terms, "theta": [tn, td]},
                     sort_keys=True, separators=(",", ":")).encode("utf-8")
    return bytes(int(c) & 3 for c in
                 klein4_bind(klein4_address(D, pre), klein4_sector_frame(D)))


# ── 1. the defect is closed, on all three surfaces ─────────────────────────

def test_klein4_from_one_separates_all_729_windings():
    """1/729 through rc437; 729/729 from rc438."""
    got = {_k4(the_one(1, 1, 1, 24, w=w)) for w in WINDING_GRID}
    assert len(got) == 729, (
        f"klein4_from_one collapsed {729 - len(got)} of 729 distinct windings "
        f"onto shared addresses ({len(got)} distinct). Through rc437 this was "
        f"1 — the whole grid on one address.")


def test_q8_from_one_separates_all_729_windings_on_BOTH_planes():
    """The V4 plane inherits the fix; the Z₂ sign plane needed its own.

    Fixing one alone yields a half-wound Q₈ coupling, and the documented
    bridge asserted below would still certify it — which is exactly why this
    test measures the two planes SEPARATELY rather than measuring the Q₈ byte
    (a single-byte census cannot distinguish "both planes moved" from "one
    plane moved twice as far").
    """
    ones = [the_one(1, 1, 1, 24, w=w) for w in WINDING_GRID]
    v4 = {_q8_v4_plane(o) for o in ones}
    sign = {_q8_sign_plane(o) for o in ones}
    assert len(v4) == 729, f"V4 coset plane: {len(v4)} distinct of 729"
    assert len(sign) == 729, (
        f"Z2 SIGN plane: {len(sign)} distinct of 729. This plane has its OWN "
        f"preimage (q8.py) — it does not inherit the klein4 fix.")


def test_the_q8_v4_bridge_still_holds_byte_for_byte_over_the_grid():
    """``q8_project_v4(q8_from_one(one, D)) == klein4_from_one(one, D)`` — the
    F380 / R21 backward-faithful bridge, unchanged by the winding fix on all
    729 windings. (It held BEFORE the fix too, over a collapsed grid: this
    bridge is why a half-wound coupling would have gone undetected.)"""
    for w in WINDING_GRID:
        one = the_one(1, 1, 1, 24, w=w)
        assert _q8_v4_plane(one) == _k4(one), f"bridge broke at w={w}"


def test_the_pm_pair_separates_though_the_spinor_shadow_cannot_see_it():
    """``w=(1,0,0)`` and ``w=(-1,0,0)`` share ``spinor_sign == -1``.

    The double-cover sign is an ORDER-2 read: it melds the ±1 winding pair, so
    no amount of looking through it distinguishes them. That is the gh #1530 §G
    motivating case — the coupling has to carry the triad WHOLE, not its
    ``(-1)^Σw`` shadow.
    """
    a = the_one(1, 1, 1, 24, w=(1, 0, 0))
    b = the_one(1, 1, 1, 24, w=(-1, 0, 0))
    sign = lambda o: (o.spinor_sign() if callable(o.spinor_sign)
                      else o.spinor_sign)
    assert sign(a) == sign(b) == -1, "the shadow must be blind here"
    assert _k4(a) != _k4(b)
    assert _q8_sign_plane(a) != _q8_sign_plane(b)
    # and they land at the floor, not merely "somewhere else"
    m = klein4_match_count(klein4_from_one(a, D), klein4_from_one(b, D))
    assert m < D // 2, f"the ± pair matched {m}/{D} — too close to identity"


# ── 2. the CONTROL: this is a measured zero, not a dead dial ───────────────

def test_the_instrument_moves_on_every_other_declared_axis():
    """40 θ → 40, 2 σ → 2, 20 ``terms`` → 20, on BOTH minters.

    Without this, "1 of 729" is indistinguishable from an op that returns a
    constant. With it, the collapse was specific to the one field the preimage
    dropped.
    """
    ot = [the_one(1, k, 997, 24) for k in range(1, 41)]
    assert len({_k4(o) for o in ot}) == 40
    assert len({_q8_sign_plane(o) for o in ot}) == 40
    os_ = [the_one(s, 3, 7, 24) for s in (1, -1)]
    assert len({_k4(o) for o in os_}) == 2
    assert len({_q8_sign_plane(o) for o in os_}) == 2
    ok = [the_one(1, 3, 7, t) for t in range(5, 25)]
    assert len({_k4(o) for o in ok}) == 20
    assert len({_q8_sign_plane(o) for o in ok}) == 20


# ── 3. the COST, both halves ───────────────────────────────────────────────

def test_unwound_ones_are_byte_identical_to_the_rc437_preimage():
    """Nothing at rest moves — the ``"winding"`` key is emitted ONLY when the
    triad is non-rest, mirroring ``One._to_jsonable()``'s own branch."""
    for k in range(1, 121):
        one = the_one(1, k, 997, 24)
        assert _k4(one) == _rc437_preimage_coupling(1, k, 997, 24), (
            f"a REST One moved at theta={k}/997 — the no-cost claim is false")


def test_wound_ones_mint_differently_which_is_the_whole_point():
    """The other half of the regime-selective invalidation, stated as a
    measurement: a wound One's coupling is NOT the rc437 coupling.

    Nothing on disk records that a genome was minted wound, so this set cannot
    be enumerated by any audit. That is permanent and follows from the
    no-sidecar discipline — it is written down here and in the CHANGELOG
    rather than left to be discovered.
    """
    for k in range(1, 121):
        one = the_one(1, k, 997, 24, w=(1, 0, 0))
        assert _k4(one) != _rc437_preimage_coupling(1, k, 997, 24)


# ── 4. the ACCEPTANCE BAR the hdc.py directive exists to defend ────────────

def _census(hvs):
    """(mean similarity as an exact Q, identical-pair count, closest
    non-identical match count, distinct-address count)."""
    n = len(hvs)
    total = ident = closest = 0
    for i in range(n):
        for j in range(i + 1, n):
            m = klein4_match_count(hvs[i], hvs[j])
            total += m
            if m == D:
                ident += 1
            elif m > closest:
                closest = m
    pairs = n * (n - 1) // 2
    return (Q(total, pairs * D), ident, closest,
            len({bytes(int(c) & 3 for c in h) for h in hvs}))


@pytest.mark.parametrize("label", ["theta", "winding", "mixed"])
def test_the_winding_bearing_preimage_is_not_a_structure_bearing_leak(label):
    """D=64, 120 members, 7140 pairs: mean ≈ 0.25 with ZERO identical pairs.

    ``hdc.py``'s shipped directive bans "improving" this op toward
    structure-bearing: the naive slot projection scores **0.82** mutual
    similarity and reads one genome with another's key at **64/64**. This is
    the guard on that ban, re-run against the SHIPPED op on all three axes
    after the winding fix. It cannot leak by construction — the winding never
    enters the One's 14-D adjoint (which is w-invariant), so the triad joins
    the Class-A digest exactly as σ/θ/terms do and never reaches the vector
    structure the ban targets — but "cannot by construction" is an argument,
    and this is the measurement.
    """
    if label == "theta":
        hvs = [klein4_from_one(the_one(1, k, 997, 24), D)
               for k in range(1, 121)]
    elif label == "winding":
        cube = [w for w in itertools.product(range(-2, 3), repeat=3)
                if w != (0, 0, 0)]
        hvs = [klein4_from_one(the_one(1, 1, 1, 24, w=w), D)
               for w in cube[:120]]
    else:
        hvs = []
        for k in range(120):
            sg = 1 if k % 2 == 0 else -1
            w = ((k % 5) - 2, ((k // 5) % 5) - 2, ((k // 25) % 5) - 2)
            hvs.append(klein4_from_one(the_one(sg, 1 + k, 997, 24, w=w), D))

    mean, ident, closest, distinct = _census(hvs)
    assert ident == 0, (
        f"{label} census: {ident} IDENTICAL pair(s) at D={D}. The bar is ZERO "
        f"— one identical pair is the 64/64 read the directive bans.")
    assert distinct == 120, f"{label} census: only {distinct}/120 distinct"
    assert Q(1, 5) < mean < Q(3, 10), (
        f"{label} census: mean similarity {float(mean)} is outside "
        f"(0.20, 0.30). Drift toward 0.82 is the structure-bearing LEAK.")
    assert closest < D, f"{label} census: closest non-identical == D"


# ── 5. what it does NOT buy — the ceiling, measured ────────────────────────

def test_sha_avalanche_destroys_adjacency_so_no_local_read_exists():
    """Adjacent windings do not give adjacent couplings — not "hard to read",
    NOT READABLE. A one-step change in ``w₂`` moves most of the 64 symbols,
    and ``symbol[0]`` alone ranges over all four Klein-4 values as ``w₀``
    varies, so no position is a partial read of any component."""
    rest = _k4(the_one(1, 1, 1, 24))
    step = _k4(the_one(1, 1, 1, 24, w=(0, 0, 1)))
    differing = sum(1 for x, y in zip(rest, step) if x != y)
    assert differing > D // 2, (
        f"only {differing}/{D} symbols moved for a one-step winding change — "
        f"that would be an adjacency an attacker could walk")
    first_symbol = {_k4(the_one(1, 1, 1, 24, w=(w0, 0, 0)))[0]
                    for w0 in range(-4, 5)}
    assert first_symbol == {0, 1, 2, 3}, (
        f"symbol[0] took only {sorted(first_symbol)} across w0 in [-4,4]; it "
        f"must take all four values or it is a partial read of w0")


def test_the_stored_strand_carries_zero_bits_about_its_key():
    """``klein4_bind`` is a Hamming ISOMETRY, so a stored body is consistent
    with EVERY key — witnessed explicitly, not argued.

    This is the information-theoretic ceiling on what a coupling can ever be:
    for any stored strand and any key ``cB`` there EXISTS a body ``tB`` with
    ``tB ⊕ cB`` byte-identical to the strand. rc438 changes which key a wound
    One mints; it does not, and cannot, make the strand testify to it.
    """
    t1 = klein4_address(D, b"strand-content-1")
    t2 = klein4_address(D, b"strand-content-2")
    cA = klein4_from_one(the_one(1, 1, 1, 24, w=(1, 0, 0)), D)
    cB = klein4_from_one(the_one(1, 1, 1, 24, w=(2, 0, 0)), D)

    # (a) the isometry: binding by ANY coupling preserves every pairwise count
    assert klein4_match_count(t1, t2) == klein4_match_count(
        klein4_bind(t1, cA), klein4_bind(t2, cA))
    assert klein4_match_count(t1, t2) == klein4_match_count(
        klein4_bind(t1, cB), klein4_bind(t2, cB))

    # (b) the witness: a DIFFERENT body that produces the SAME stored bytes
    stored = klein4_bind(t1, cA)
    tB = klein4_bind(stored, cB)
    assert bytes(tB.buffer) != bytes(t1.buffer), "cA and cB must differ"
    assert bytes(klein4_bind(tB, cB).buffer) == bytes(stored.buffer), (
        "the universal-consistency witness failed — if THIS breaks, the bind "
        "is no longer an isometry and the whole coupling contract changed")


# ── 6. the duck-typed operand contract ─────────────────────────────────────

class _BareOne:
    """The structurally-read operand the op's Args block promises to accept."""

    def __init__(self, sigma, theta, terms, **kw):
        self.sigma, self.theta, self.terms = sigma, theta, terms
        for k, v in kw.items():
            setattr(self, k, v)


def test_an_operand_with_no_winding_at_all_reads_as_at_rest():
    """"No winding" can only mean rest, and must not raise — the op is
    documented as reading ``.sigma`` / ``.theta`` / ``.terms`` structurally."""
    bare = _BareOne(1, (3, 7), 24)
    assert bytes(klein4_from_one(bare, D).buffer) == \
        bytes(klein4_from_one(the_one(1, 3, 7, 24), D).buffer)
    assert bytes(q8_from_one(bare, D).buffer) == \
        bytes(q8_from_one(the_one(1, 3, 7, 24), D).buffer)


@pytest.mark.parametrize("bad", [(1, 2), (1, 2, 3, 4), "abc", 5, (1, 2, "x")])
def test_a_malformed_winding_raises_rather_than_being_read_as_rest(bad):
    """A present-but-malformed ``.winding`` must NOT be silently read as rest.

    Silently reading it as rest is the exact failure class rc438 closes one
    level up — a declared field dropped with no error signal.
    """
    with pytest.raises(TypeError, match="winding"):
        klein4_from_one(_BareOne(1, (3, 7), 24, winding=bad), D)


# ── 7. the ABI-15 wire, and both projections on it ────────────────────────

def test_expected_abi_is_pinned():
    """The winding triad on ``srmech_klein4_from_one``'s wire is a change to an
    EXISTING exported signature, so ABI moves 14 → 15 (an additive symbol
    would not have). The pin is what rejects a stale rc437 ``.so`` — which
    would still return CORRECT bytes on the rest path, and so would reintroduce
    the defect on wound Ones only, silently."""
    # NAME CARRIES NO NUMBER ON PURPOSE. This pin tracks a value that MOVES;
    # a name that spells the value is falsified by the next bump and was —
    # 16 such tests were found tree-wide, one named for 367 asserting 663.
    # See test_pinned_names_carry_no_value_rc447.py.
    assert _native.EXPECTED_ABI_VERSION == 21


@requires_native
def test_the_native_projection_agrees_byte_for_byte_in_BOTH_regimes():
    """Co-equal parity across the new wire — the half the rc435 study could not
    reach, because it ran with ``HAS_NATIVE`` False."""
    assert _native.NATIVE_ABI_VERSION == 21

    def pure(one):
        saved = _native.HAS_NATIVE
        _native.HAS_NATIVE = False
        try:
            return bytes(klein4_from_one(one, D).buffer)
        finally:
            _native.HAS_NATIVE = saved

    mismatches = []
    for w in itertools.product(range(-2, 3), repeat=3):      # 125 windings
        for sg, tn, td, terms in ((1, 1, 1, 24), (-1, 3, 7, 6)):
            one = the_one(sg, tn, td, terms, w=w)
            if bytes(klein4_from_one(one, D).buffer) != pure(one):
                mismatches.append((sg, tn, td, terms, w))
    assert not mismatches, (
        f"{len(mismatches)} native/pure divergence(s), first "
        f"{mismatches[:3]} — the C branch and the Python branch must emit the "
        f"SAME preimage in both regimes")


@requires_native
def test_an_out_of_int64_winding_declines_to_the_pure_path_not_truncated():
    """The int64 wire is a BOUND, not a silent modulus. A winding outside it
    declines to the pure body — which still separates it from rest."""
    from srmech.math import hdc
    big = 2 ** 70
    assert hdc._klein4_from_one_native(1, 1, 1, 24, (big, 0, 0), D) is None
    assert _k4(the_one(1, 1, 1, 24, w=(big, 0, 0))) != _k4(the_one(1, 1, 1, 24))


# ── 8. the declared chain is the permanent ratchet ─────────────────────────

def test_the_catalog_descriptor_declares_both_regimes_as_separate_chains():
    """``klein4_from_one.toml`` carries rest/wound as TWO ``[[cascade.chain]]``
    variants (the ``kuramoto_step`` precedent), NOT one chain with a
    conditional step form — that would be a discriminator widening, and
    `#T1141` measured that C implements 1 of the 3 existing step forms.

    ``tests/test_cascade_catalog_executable_rc420.py`` is what EXECUTES those
    chains against the shipped op and demands bit-identity; this test only
    pins that the two-variant shape is what shipped.
    """
    from srmech.dsl._cascade_chain import cascade_chain_specs
    variants = [v for v, _s, _e in cascade_chain_specs("klein4_from_one")]
    assert variants == ["rest", "wound"], variants


def test_every_declared_regime_carries_a_proof_case_that_covers_it():
    """A declared chain with no proof case for its own regime is prose."""
    from srmech.dsl import get_descriptor
    chains = get_descriptor("klein4_from_one")["cascade"]["chain"]
    covered = {c.get("covers") for e in chains
               for c in e.get("proof_cases", [])}
    assert {"rest", "wound", "pm_pair"} <= covered, covered
