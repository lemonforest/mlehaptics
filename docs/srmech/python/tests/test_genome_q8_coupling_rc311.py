"""§Q8 / rc311 — native Q8 genome coupling + recall-inverse PROVE-GATES.

The rc310 Q8 carrier ops (:mod:`srmech.amsc.q8`) are wired into the GENOME as a NEW
``element_type`` path (:data:`~srmech.amsc.genome.ELEMENT_TYPE_Q8`) that COEXISTS with the
shipped klein4 path (``ELEMENT_TYPE_KLEIN4``, byte-untouched). Q₈ is the NON-abelian central
extension of the Klein-4 coset, so its coupling is the Q₈ group product (RIGHT-couple) and its
recall is the group INVERSE (the Class-C conjugate) — NOT the XOR self-inverse klein4 uses.

This file is the six NON-NEGOTIABLE prove-gates for that wiring. Every gate is numpy-free (the
module under test is numpy-free) and seeded (reproducible). NO ``-k`` filter is used to run them.

  P1  Q8 round-trip — recall(chromosome(leaves, one, Q8), one, Q8) == leaves exactly.
  P2  backward-faithful sequence — q8_project_v4(Q8 recall) == klein4-projected recall (the
      π: Q₈ → V4 homomorphism at the genome level).
  P3  sign-bit fault-injection (Break C) — a LONE Q₈ sign-bit flip (the over/under-winding
      read-error mode, NEW at Q8) in one diploid copy is RECOVERED by the two-copy + mark EC
      operating on the full 3-bit symbol.
  P4  orthogonality floor (Break E) — the 0.25 HV orthogonality floor SURVIVES data-turn
      sectors going QUAD(4) → OCT(8); a numeric floor test, and coupling preserves it exactly.
  P5  coupling-side assertion — a WRONG (left) coupling side FAILS LOUDLY (the runtime
      HARD-ASSERT predicate is False → the assert fires; and the round-trip mismatches).
  P6  klein4 UNCHANGED — existing klein4 genomes recall/recover byte-identically to the raw
      shipped klein4_bind (no regression on the shipped path).
"""
from __future__ import annotations

import random

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc.genome import (
    ELEMENT_TYPE_KLEIN4,
    ELEMENT_TYPE_Q8,
    OCT,
    QUAD,
    chromosome,
    diploid,
    quad_turn,
    recall,
    recover_diploid,
    telomere,
)
from srmech.math.hdc import klein4_bind
from srmech.amsc.hv import HV
from srmech.amsc.q8 import q8_bind, q8_conjugate, q8_mult, q8_project_v4


# ── helpers ──────────────────────────────────────────────────────────────────
def _rand_q8_leaves(rng, n_leaves, leaf_dim):
    """``n_leaves`` random Q₈ leaves (``sectors=8`` HVs, bytes in ``[0, 8)``)."""
    return [HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)), sectors=OCT)
            for _ in range(n_leaves)]


def _rand_q8_one(rng, leaf_dim):
    """A random Q₈ coupling ``one`` (``sectors=8`` HV)."""
    return HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)), sectors=OCT)


def _lists(hvs):
    return [h.tolist() for h in hvs]


# ── P1 — Q8 round-trip ───────────────────────────────────────────────────────
def test_p1_q8_roundtrip_exact():
    """recall(chromosome(leaves, one, Q8), one, Q8) == leaves, over random leaves + one.
    The NON-involutive Q₈ group inverse must recover exactly."""
    rng = random.Random(31101)
    trials = 0
    for _ in range(250):
        leaf_dim = rng.randrange(16, 48)
        n_leaves = rng.randrange(1, 9)
        leaves = _rand_q8_leaves(rng, n_leaves, leaf_dim)
        one = _rand_q8_one(rng, leaf_dim)
        strand = chromosome(leaves, one, element_type=ELEMENT_TYPE_Q8)
        rec = recall(strand, one, element_type=ELEMENT_TYPE_Q8)
        assert _lists(rec) == _lists(leaves)
        # every recovered leaf is a valid Q₈ byte vector (sectors=8, 0..7)
        assert all(all(0 <= b < OCT for b in h.tolist()) for h in rec)
        trials += 1
    assert trials == 250


def test_p1_q8_recall_is_non_involutive():
    """A second couple is NOT the inverse (Q₈ is non-abelian) — proving recall genuinely uses
    the group inverse, not a klein4-style double bind."""
    rng = random.Random(31102)
    non_involutive_seen = 0
    for _ in range(50):
        leaf_dim = rng.randrange(16, 40)
        leaves = _rand_q8_leaves(rng, 4, leaf_dim)
        one = _rand_q8_one(rng, leaf_dim)
        strand = chromosome(leaves, one, element_type=ELEMENT_TYPE_Q8)
        # a WRONG "double couple" recall (re-bind instead of inverse) would give the stored
        # turn coupled AGAIN — assert that is different from the true leaves for some trial.
        double = [q8_bind(t.tobytes(), one.tobytes())
                  for t in strand if G._cap_kind(t) is None]
        if [list(b) for b in double] != _lists(leaves):
            non_involutive_seen += 1
    assert non_involutive_seen > 0


# ── P2 — backward-faithful sequence (π: Q₈ → V4 homomorphism) ─────────────────
def test_p2_backward_faithful_pi_homomorphism():
    """q8_project_v4(recall of a Q8 genome) == recall of the klein4-projected genome, bit for
    bit — the π: Q₈ → V4 homomorphism lifted to the genome level."""
    rng = random.Random(31103)
    for _ in range(150):
        leaf_dim = rng.randrange(16, 48)
        n_leaves = rng.randrange(1, 8)
        q8_leaves = _rand_q8_leaves(rng, n_leaves, leaf_dim)
        q8_one = _rand_q8_one(rng, leaf_dim)

        # Q8 path: build + recall in Q8, then V4-project each recovered leaf.
        q8_strand = chromosome(q8_leaves, q8_one, element_type=ELEMENT_TYPE_Q8)
        q8_rec = recall(q8_strand, q8_one, element_type=ELEMENT_TYPE_Q8)
        projected = [bytes(q8_project_v4(h)) for h in q8_rec]

        # klein4-projected path: project the INPUTS to V4 first, then build + recall in klein4.
        k_leaves = [HV.from_sequence(bytes(b & 3 for b in h.tobytes()), sectors=QUAD)
                    for h in q8_leaves]
        k_one = HV.from_sequence(bytes(b & 3 for b in q8_one.tobytes()), sectors=QUAD)
        k_strand = chromosome(k_leaves, k_one, element_type=ELEMENT_TYPE_KLEIN4)
        k_rec = recall(k_strand, k_one, element_type=ELEMENT_TYPE_KLEIN4)
        klein4_bytes = [bytes(h.tolist()) for h in k_rec]

        assert projected == klein4_bytes


# ── P3 — sign-bit fault-injection (Break C) ──────────────────────────────────
def test_p3_lone_sign_bit_fault_recovers_via_diploid_ec():
    """A LONE Q₈ sign-bit flip (b ^ 4 — the over/under-winding read-error mode, invisible to
    the V4 coset) in the UNMARKED diploid copy is RECOVERED by the existing two-copy + mark EC.
    The full-leaf compare is bit-width-agnostic, so it resolves the 3-bit symbol exactly as it
    resolves a 2-bit V4 one — the EC is SUFFICIENT for the Q8 sign bit."""
    rng = random.Random(31104)
    for _ in range(80):
        leaf_dim = rng.randrange(32, 64)          # room for the "diploid" cap + R=15 centromere
        n_leaves = rng.randrange(2, 6)
        leaves = _rand_q8_leaves(rng, n_leaves, leaf_dim)
        one = _rand_q8_one(rng, leaf_dim)
        # orientation=0 → which-template mark = 0 → the EC trusts copyA; corrupt copyB.
        strand = list(diploid(leaves, one, orientation=0, element_type=ELEMENT_TYPE_Q8))
        cen_idx = next(i for i, hv in enumerate(strand)
                       if G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER)
        target = cen_idx + 1 + rng.randrange(n_leaves)     # a copyB (unmarked) data turn
        buf = bytearray(strand[target].tobytes())
        pos = rng.randrange(len(buf))
        before = buf[pos]
        buf[pos] = before ^ 4                              # flip ONLY the sign bit (Class K∘C)
        assert (buf[pos] & 3) == (before & 3)              # V4 coset unchanged → PURE sign fault
        assert buf[pos] != before                          # the fault is real
        strand[target] = HV.from_sequence(bytes(buf), sectors=OCT)

        rec = recover_diploid(strand, one, element_type=ELEMENT_TYPE_Q8)
        assert _lists(rec) == _lists(leaves), (
            "recover_diploid did NOT correct a lone Q8 sign-bit fault in the unmarked copy — "
            "the two-copy + mark EC is insufficient for the Q8 3-bit symbol")


def test_p3_sign_fault_is_invisible_to_v4_projection():
    """The fault-mode P3 targets is genuinely NEW at Q8: a lone sign flip leaves the V4 coset
    (the only thing klein4 can store) IDENTICAL — so klein4 could not even represent it."""
    for b in range(OCT):
        flipped = b ^ 4
        assert (flipped & 3) == (b & 3)       # sign flip preserves the V4 coset
        assert flipped != b                   # but changes the Q8 byte
        # and it is exactly the Q8 conjugate on the imaginary cosets:
        if (b & 3) != 0:
            assert q8_conjugate(b) == flipped


# ── P4 — orthogonality floor (Break E) QUAD(4) → OCT(8) ──────────────────────
def test_p4_orthogonality_floor_survives_quad_to_oct():
    """Random Q₈ (``sectors=8``) vectors are AT LEAST as orthogonal as klein4: the mean pairwise
    similarity is ≤ 0.25 (the klein4 floor) and concentrates at the Q8 floor 1/8 = 0.125. So the
    0.25 floor SURVIVES the QUAD→OCT sector bump — it is not violated (it improves)."""
    rng = random.Random(31105)
    leaf_dim = 512
    n_vecs = 48
    vecs = [bytes(rng.randrange(OCT) for _ in range(leaf_dim)) for _ in range(n_vecs)]

    def _mean_sim(bufs):
        sims = []
        for i in range(len(bufs)):
            for j in range(i + 1, len(bufs)):
                match = sum(1 for a, b in zip(bufs[i], bufs[j]) if a == b)
                sims.append(match / leaf_dim)
        return sims, sum(sims) / len(sims)

    raw_sims, raw_mean = _mean_sim(vecs)
    assert raw_mean <= 0.25                       # the klein4 floor is not violated
    assert abs(raw_mean - 1.0 / OCT) < 0.02       # concentrates at the Q8 floor 1/8

    # Coupling through a shared `one` PRESERVES orthogonality EXACTLY: right-multiplication by a
    # fixed Q8 element is a bijection, so coupled[i][p] == coupled[j][p] ⟺ vecs[i][p] == vecs[j][p].
    one = bytes(rng.randrange(OCT) for _ in range(leaf_dim))
    coupled = [q8_bind(v, one) for v in vecs]
    coupled_sims, coupled_mean = _mean_sim(coupled)
    assert coupled_sims == raw_sims               # per-pair identical → floor preserved exactly
    assert coupled_mean <= 0.25


# ── P5 — coupling-side HARD-ASSERT fires for the wrong side ───────────────────
def test_p5_wrong_coupling_side_fails_loudly():
    """The coupling SIDE is a fireable runtime invariant. RIGHT-couple (the shipped path)
    satisfies :func:`_q8_side_ok`; a LEFT-couple does NOT (Q₈ is non-abelian) — so the
    HARD-ASSERT in :func:`_q8_couple` fires for the wrong side, and a wrong-side round-trip
    mismatches loudly instead of corrupting silently."""
    rng = random.Random(31106)
    leaf_dim = 128
    turn = bytearray(rng.randrange(OCT) for _ in range(leaf_dim))
    one = bytearray(rng.randrange(OCT) for _ in range(leaf_dim))
    # FORCE slot 0 to an anticommuting pair (i·j = +k, j·i = −k) so the side error is guaranteed.
    turn[0], one[0] = 1, 2
    turn, one = bytes(turn), bytes(one)

    right = q8_bind(turn, one)                      # stored[i] = q8_mult(turn[i], one[i])
    left = bytes(q8_mult(o, t) for t, o in zip(turn, one))   # WRONG: q8_mult(one[i], turn[i])
    assert left != right                            # the sides genuinely differ (non-abelian)

    assert G._q8_side_ok(right, turn, one) is True  # the shipped right-couple passes the guard
    assert G._q8_side_ok(left, turn, one) is False  # the wrong side FAILS the guard

    # The exact guard :func:`_q8_couple` runs, exercised on a wrong-side couple → AssertionError.
    def _left_couple_with_guard(t, o):
        stored = bytes(q8_mult(oo, tt) for tt, oo in zip(t, o))   # left (wrong) side
        assert G._q8_side_ok(stored, t, o), "q8 couple side error"
        return stored

    with pytest.raises(AssertionError):
        _left_couple_with_guard(turn, one)

    # And a full wrong-side round-trip MISMATCHES: hand-build a strand of left-coupled turns,
    # recall (right-uncouple), and confirm it does NOT recover the leaves.
    leaves = _rand_q8_leaves(random.Random(31107), 5, leaf_dim)
    cap = telomere("chromosome", dim=leaf_dim)
    wrong_turns = [
        HV.from_sequence(bytes(q8_mult(o, t) for t, o in zip(leaf.tobytes(), one)),
                         sectors=OCT)
        for leaf in leaves
    ]
    wrong_rec = recall([cap] + wrong_turns, HV.from_sequence(one, sectors=OCT),
                       element_type=ELEMENT_TYPE_Q8)
    assert _lists(wrong_rec) != _lists(leaves)      # loud mismatch — side is load-bearing


def test_p5_shipped_couple_asserts_and_recovers():
    """The shipped :func:`quad_turn`/:func:`_q8_couple` (right-couple) passes its own runtime
    HARD-ASSERT for every input AND round-trips — the assertion does not false-fire."""
    rng = random.Random(31108)
    for _ in range(100):
        leaf_dim = rng.randrange(8, 40)
        turn = _rand_q8_one(rng, leaf_dim)
        one = _rand_q8_one(rng, leaf_dim)
        stored = quad_turn(turn, one, element_type=ELEMENT_TYPE_Q8)   # asserts internally
        back = G._quad_unturn(stored, one, element_type=ELEMENT_TYPE_Q8)
        assert back.tolist() == turn.tolist()


# ── P6 — klein4 UNCHANGED (no regression on the shipped path) ─────────────────
def test_p6_klein4_chromosome_byte_identical_to_raw_bind():
    """A klein4 chromosome's data turns are byte-identical to the raw shipped klein4_bind
    (the pre-rc311 coupling) — the default element_type path is UNCHANGED."""
    rng = random.Random(31109)
    for _ in range(120):
        leaf_dim = rng.randrange(16, 48)
        n_leaves = rng.randrange(1, 8)
        leaves = [HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)),
                                   sectors=QUAD) for _ in range(n_leaves)]
        one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)),
                               sectors=QUAD)
        # default (no element_type) and explicit klein4 both produce the raw klein4_bind turns.
        for strand in (chromosome(leaves, one),
                       chromosome(leaves, one, element_type=ELEMENT_TYPE_KLEIN4)):
            data = [h for h in strand if G._cap_kind(h) is None]
            golden = [klein4_bind(leaf, one) for leaf in leaves]
            assert _lists(data) == _lists(golden)
            # and recall inverts it back to the leaves (the shipped involution)
            assert _lists(recall(strand, one)) == _lists(leaves)
            assert _lists(recall(strand, one, element_type=ELEMENT_TYPE_KLEIN4)) == _lists(leaves)


def test_p6_klein4_quad_turn_and_unturn_are_the_involution():
    """klein4 ``quad_turn`` (default + explicit) and the new ``_quad_unturn`` are BOTH the same
    reversible XOR bind — byte-identical to ``klein4_bind`` (the shipped op is untouched)."""
    rng = random.Random(31110)
    for _ in range(100):
        leaf_dim = rng.randrange(8, 40)
        t = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
        c = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
        raw = klein4_bind(t, c)
        assert quad_turn(t, c).tolist() == raw.tolist()
        assert quad_turn(t, c, element_type=ELEMENT_TYPE_KLEIN4).tolist() == raw.tolist()
        assert G._quad_unturn(t, c, element_type=ELEMENT_TYPE_KLEIN4).tolist() == raw.tolist()
        # involution: couple then uncouple == identity
        assert G._quad_unturn(quad_turn(t, c), c).tolist() == t.tolist()


# ── native == pure BYTE PARITY for the Q8 genome peers ───────────────────────
def test_native_pure_parity_q8_recall(monkeypatch):
    """The native ``srmech_genome_recall_q8`` peer is BYTE-IDENTICAL to the pure Q8 recall walk.
    When the native symbol is absent this trivially compares pure-to-pure; when present (our
    fresh build) it proves native == pure exactly."""
    rng = random.Random(31120)
    for _ in range(60):
        leaf_dim = rng.randrange(16, 48)
        n_leaves = rng.randrange(1, 8)
        leaves = _rand_q8_leaves(rng, n_leaves, leaf_dim)
        one = _rand_q8_one(rng, leaf_dim)
        strand = chromosome(leaves, one, element_type=ELEMENT_TYPE_Q8)
        native_rec = recall(strand, one, element_type=ELEMENT_TYPE_Q8)
        with monkeypatch.context() as m:
            m.setattr(_native, "has_native_genome_recall_q8", lambda: False)
            pure_rec = recall(strand, one, element_type=ELEMENT_TYPE_Q8)
        assert _lists(native_rec) == _lists(pure_rec) == _lists(leaves)


def test_native_pure_parity_q8_recover_diploid(monkeypatch):
    """The native ``srmech_genome_recover_diploid_q8`` peer is BYTE-IDENTICAL to the pure Q8 EC
    walk — including under a lone sign-bit fault in the unmarked copy."""
    rng = random.Random(31121)
    for _ in range(40):
        leaf_dim = rng.randrange(32, 64)
        n_leaves = rng.randrange(2, 6)
        leaves = _rand_q8_leaves(rng, n_leaves, leaf_dim)
        one = _rand_q8_one(rng, leaf_dim)
        strand = list(diploid(leaves, one, orientation=0, element_type=ELEMENT_TYPE_Q8))
        # inject a lone sign-bit fault into a copyB turn (unmarked)
        cen_idx = next(i for i, hv in enumerate(strand)
                       if G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER)
        target = cen_idx + 1 + rng.randrange(n_leaves)
        buf = bytearray(strand[target].tobytes())
        buf[rng.randrange(len(buf))] ^= 4
        strand[target] = HV.from_sequence(bytes(buf), sectors=OCT)

        native_rec = recover_diploid(strand, one, element_type=ELEMENT_TYPE_Q8)
        with monkeypatch.context() as m:
            m.setattr(_native, "has_native_genome_recover_diploid_q8", lambda: False)
            pure_rec = recover_diploid(strand, one, element_type=ELEMENT_TYPE_Q8)
        assert _lists(native_rec) == _lists(pure_rec) == _lists(leaves)


def test_p6_klein4_diploid_ec_unchanged():
    """A klein4 diploid + recover_diploid round-trips and still error-corrects a corrupted
    copy — the shipped §95b EC path is untouched."""
    rng = random.Random(31111)
    for _ in range(40):
        leaf_dim = rng.randrange(32, 64)
        n_leaves = rng.randrange(2, 6)
        leaves = [HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)),
                                   sectors=QUAD) for _ in range(n_leaves)]
        one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
        strand = list(diploid(leaves, one, orientation=0))
        assert _lists(recover_diploid(strand, one)) == _lists(leaves)
        # corrupt a copyB turn (unmarked; which=0 trusts copyA) and recover
        cen_idx = next(i for i, hv in enumerate(strand)
                       if G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER)
        target = cen_idx + 1 + rng.randrange(n_leaves)
        buf = bytearray(strand[target].tobytes())
        buf[rng.randrange(len(buf))] ^= 1        # flip a klein4 coset bit
        strand[target] = HV.from_sequence(bytes(buf), sectors=QUAD)
        assert _lists(recover_diploid(strand, one)) == _lists(leaves)
