"""rc315 — Q8 GENOME API COMPLETENESS prove-gates (Q1-Q6).

rc311 threaded ``element_type`` through the LOW-LEVEL turn path; rc315 completes
the HIGH-LEVEL build + read surface so a Q8 (substrate) genome can be MINTED and
EXPRESSED/READ through the normal genome API with NO hand-construction of the OCT
coupling. This module is the committed provenance for the six prove-gates:

* Q1 — ``q8_from_one`` mints a valid OCT one; V4 projection == klein4_from_one
        (backward-faithful, by construction; sign plane non-trivial).
* Q2 — ``mint_strand(element_type=Q8)`` builds a Q8 genome; ``recall`` recovers
        the EXACT leaves.
* Q3 — ``gene_express`` / ``gene_express_levels`` / ``genes`` on a Q8 genome
        return correct results via the Q8 decouple (NOT the klein4 XOR), and
        their V4-projection matches the klein4 genome's expression.
* Q4 — ``partition`` on a Q8 genome works end-to-end.
* Q5 — the full downstream flow (q8_from_one -> mint_strand(Q8) -> gene_express)
        works with no hand-construction.
* Q6 — klein4 UNCHANGED: existing klein4 genomes round-trip exactly (no regression).
* Q7 — ``gene_express_plan`` strides at the Q8 data-turn width on a Q8 gene genome:
        the emitted byte spans tile EXACTLY on the real on-disk cap boundaries (a
        klein4-width stride would drift the offsets — the gap the decouple-heuristic
        audit missed, since the plan seeks PAST turns rather than decoupling them).

numpy-free (no importorskip — the suite runs numpy-ABSENT); native == pure is
re-verified by forcing the pure path (Q_PARITY).
"""
from __future__ import annotations

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.cascade.one import the_one
from srmech.math.hdc import klein4_from_one
from srmech.math.hv import HV
from srmech.biology.q8 import q8_from_one, q8_project_v4

Q8 = G.ELEMENT_TYPE_Q8
K4 = G.ELEMENT_TYPE_KLEIN4
D = 48


def _one_a():
    return the_one(1, 1, 3)


def _q8_one():
    return q8_from_one(_one_a(), D)


def _k4_one():
    return klein4_from_one(_one_a(), D)


def _lift(k4_hv, tag):
    """A Q8 leaf whose V4 projection is EXACTLY the klein4 leaf (non-trivial signs)."""
    kb = k4_hv.tobytes()
    sign = klein4_from_one(the_one(1, tag, 5), D).tobytes()
    return HV.from_sequence(
        bytes(((sign[i] & 1) << 2) | (kb[i] & 3) for i in range(D)), sectors=8)


def _k4_gene_leaves():
    return {"rules": [klein4_from_one(the_one(1, s, 9), D) for s in (11, 12)],
            "board": [klein4_from_one(the_one(1, 13, 9), D)]}


def _q8_gene_leaves(k4_leaves):
    return {lbl: [_lift(k, i * 10 + j) for j, k in enumerate(lv)]
            for i, (lbl, lv) in enumerate(k4_leaves.items())}


# ── Q1 ──────────────────────────────────────────────────────────────────────
def test_q1_q8_from_one_valid_and_backward_faithful():
    q = _q8_one()
    assert q.sectors == 8 and len(q) == D
    assert all(0 <= b < 8 for b in q), "every byte a valid Q8 element"
    assert any(b > 3 for b in q), "the sign plane is non-trivial (a genuine Q8 one)"
    # backward-faithful bridge: V4 projection is EXACTLY klein4_from_one
    assert bytes(q8_project_v4(q)) == _k4_one().tobytes()
    # distinct Ones -> distinct couplings
    assert q.tobytes() != q8_from_one(the_one(-1, 2, 7), D).tobytes()


# ── Q2 ──────────────────────────────────────────────────────────────────────
def test_q2_mint_strand_q8_builds_and_recall_recovers_exact():
    q8_one = _q8_one()
    leaves = [_lift(klein4_from_one(the_one(1, 20 + i, 9), D), 500 + i) for i in range(5)]
    chrom = G.chromosome(leaves, q8_one, label="q8kernel", element_type=Q8)
    minted = G.mint_strand(chrom, q8_one, element_type=Q8)
    assert any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in minted), \
        "mint_strand splices the interior centromere"
    assert G.recall(minted, q8_one, element_type=Q8) == leaves


# ── Q3 ──────────────────────────────────────────────────────────────────────
def test_q3_gene_readers_q8_decouple_and_backward_faithful():
    k4_one, q8_one = _k4_one(), _q8_one()
    k4_leaves = _k4_gene_leaves()
    q8_leaves = _q8_gene_leaves(k4_leaves)
    q8_strand = G.chromosome(genes=[(l, q8_leaves[l]) for l in q8_leaves],
                             coupling=q8_one, element_type=Q8)
    k4_strand = G.chromosome(genes=[(l, k4_leaves[l]) for l in k4_leaves],
                             coupling=k4_one, element_type=K4)

    # genes(): exact Q8 recovery + V4-projection == klein4 recovery
    g_q8 = G.genes(q8_strand, q8_one, element_type=Q8)
    g_k4 = G.genes(k4_strand, k4_one)
    for (lbl_q, lv_q), (lbl_k, lv_k) in zip(g_q8, g_k4):
        assert lbl_q == lbl_k
        assert lv_q == q8_leaves[lbl_q]                         # exact Q8 leaves
        assert [bytes(q8_project_v4(x)) for x in lv_q] == [y.tobytes() for y in lv_k]

    # gene_express(): expressed labels + backward-faithful leaves
    ex_q8 = G.gene_express(q8_strand, q8_one, 0, element_type=Q8)
    ex_k4 = G.gene_express(k4_strand, k4_one, 0)
    assert [l for l, _ in ex_q8] == [l for l, _ in ex_k4]
    for (_, lv_q), (_, lv_k) in zip(ex_q8, ex_k4):
        assert [bytes(q8_project_v4(x)) for x in lv_q] == [y.tobytes() for y in lv_k]

    # gene_express_levels(): same levels + backward-faithful leaves
    lv_q8 = G.gene_express_levels(q8_strand, q8_one, 0, element_type=Q8)
    lv_k4 = G.gene_express_levels(k4_strand, k4_one, 0)
    assert [(l, lvl) for l, _, lvl in lv_q8] == [(l, lvl) for l, _, lvl in lv_k4]
    for (_, lq, _), (_, lk, _) in zip(lv_q8, lv_k4):
        assert [bytes(q8_project_v4(x)) for x in lq] == [y.tobytes() for y in lk]


# ── Q4 ──────────────────────────────────────────────────────────────────────
def test_q4_partition_q8_end_to_end():
    q8_one = _q8_one()
    q8_leaves = _q8_gene_leaves(_k4_gene_leaves())
    multi = (G.chromosome(q8_leaves["rules"], q8_one, label="a", element_type=Q8)
             + G.chromosome(q8_leaves["board"], q8_one, label="b", element_type=Q8))
    part = G.partition(multi, q8_one, element_type=Q8)
    assert set(part) == {"a", "b"}
    assert part["a"] == q8_leaves["rules"]
    assert part["b"] == q8_leaves["board"]


# ── Q5 ──────────────────────────────────────────────────────────────────────
def test_q5_full_downstream_flow_no_hand_construction():
    one = q8_from_one(the_one(1, 5, 11), D)             # the OCT one, minted (not hand-built)
    data = [_lift(klein4_from_one(the_one(1, 40 + i, 9), D), 900 + i) for i in range(4)]
    dchrom = G.chromosome(data, one, label="ds", element_type=Q8)
    minted = G.mint_strand(dchrom, one, element_type=Q8)
    assert G.recall(minted, one, element_type=Q8) == data          # data genome round-trips
    # a minted DATA genome carries no genes -> gene_express is a clean empty read
    assert G.gene_express(minted, one, 0, element_type=Q8) == []
    # and a gene-bearing Q8 chromosome off the SAME minted one expresses correctly
    q8_leaves = _q8_gene_leaves(_k4_gene_leaves())
    gene_chrom = G.chromosome(genes=[("g", q8_leaves["board"])], coupling=one, element_type=Q8)
    expressed = G.gene_express(gene_chrom, one, 0, element_type=Q8)
    assert len(expressed) == 1 and expressed[0][1] == q8_leaves["board"]


# ── Q6 ──────────────────────────────────────────────────────────────────────
def test_q6_klein4_unchanged_round_trip():
    k4_one = _k4_one()
    k4_leaves = _k4_gene_leaves()
    k4_gene_strand = G.chromosome(genes=[(l, k4_leaves[l]) for l in k4_leaves],
                                  coupling=k4_one)
    # recall / mint_strand round-trip on the default (klein4) path
    data = [klein4_from_one(the_one(1, 60 + i, 9), D) for i in range(6)]
    minted = G.mint_strand(G.chromosome(data, k4_one, label="k"), k4_one)
    assert G.recall(minted, k4_one) == data
    # genes / gene_express / partition default path unchanged
    assert [lbl for lbl, _ in G.genes(k4_gene_strand, k4_one)] == list(k4_leaves)
    assert all(lv == k4_leaves[lbl] for lbl, lv in G.genes(k4_gene_strand, k4_one))
    multi = (G.chromosome(k4_leaves["rules"], k4_one, label="a")
             + G.chromosome(k4_leaves["board"], k4_one, label="b"))
    assert G.partition(multi, k4_one) == {"a": k4_leaves["rules"], "b": k4_leaves["board"]}
    assert [l for l, _ in G.gene_express(k4_gene_strand, k4_one, 0)] == list(k4_leaves)


# ── Q7 ──────────────────────────────────────────────────────────────────────
def test_q7_gene_express_plan_q8_byte_spans_tile_on_disk():
    """``gene_express_plan`` on a Q8 gene genome must stride at the Q8 data-turn
    width (§Q8/v16, 3 bits/symbol), NOT the narrower klein4 width (§55/v3) — else the
    emitted ``(offset, length)`` byte spans drift and a demand-loader seeks the wrong
    range. A Q8 gene genome has klein4 gene CAPS but Q8 DATA TURNS; the plan seeks PAST
    the turns to reach each cap. STRAND variant: every span tiles EXACTLY on the real
    on-disk cap boundaries. PATH variant (stored offsets): same expressed labels."""
    import os
    import shutil
    import tempfile
    one = _q8_one()
    # genes of DIFFERENT leaf-counts so the stride is exercised across several turns
    leaves = {"g": [_lift(klein4_from_one(the_one(1, 13 + i, 9), D), 7 + i) for i in range(2)],
              "h": [_lift(klein4_from_one(the_one(1, 21, 9), D), 30)]}
    strand = G.chromosome(genes=[(l, leaves[l]) for l in leaves], coupling=one,
                          element_type=Q8)

    plan_q8 = G.gene_express_plan(strand, one, 0, element_type=Q8)
    # element_type MUST change the stride (guards against a no-op thread)
    assert plan_q8 != G.gene_express_plan(strand, one, 0)      # != klein4-default stride
    assert [l for l, _, _ in plan_q8] == list(leaves)          # all genes expressed at cs=0

    d = tempfile.mkdtemp()
    try:
        G.genome_save(strand, d, one, element_type=Q8)
        body = open(os.path.join(d, G._BODY_NAME), "rb").read()

        def _cap_at(pos):
            blk = body[pos:pos + D]
            return None if len(blk) < D else G._cap_kind(G._hv_from_block(blk))

        for lbl, off, ln in plan_q8:
            assert _cap_at(off) is not None, f"{lbl}: offset {off} not on a cap"
            end = off + ln
            assert end == len(body) or _cap_at(end) is not None, \
                f"{lbl}: end {end} off a cap boundary (turn-width drift)"

        # single-leaf gene 'h' span is EXACTLY [gene cap] + [one Q8 turn]
        h_len = {l: ln for l, _, ln in plan_q8}["h"]
        assert h_len == D + (1 + G._packed_payload_len_q8(D))

        # PATH variant is element_type-agnostic (STORED manifest offsets, CHROMOSOME
        # granularity — not gene, unlike STRAND). It runs on a Q8 genome and its spans
        # tile on real cap boundaries too.
        path_plan = G.gene_express_plan(d, one, 0, element_type=Q8)
        assert path_plan, "PATH plan non-empty for an all-expressed Q8 genome"
        for _lbl, poff, pln in path_plan:
            assert _cap_at(poff) is not None, f"PATH offset {poff} not on a cap"
            pend = poff + pln
            assert pend == len(body) or _cap_at(pend) is not None, \
                f"PATH end {pend} off a cap boundary"
    finally:
        shutil.rmtree(d, ignore_errors=True)

    assert [l for l, _ in G.gene_express(strand, one, 0, element_type=Q8)] == list(leaves)


# ── PARITY: native == pure (force the pure path, re-run the gates) ────────────
@pytest.mark.parametrize("gate", [
    test_q1_q8_from_one_valid_and_backward_faithful,
    test_q2_mint_strand_q8_builds_and_recall_recovers_exact,
    test_q3_gene_readers_q8_decouple_and_backward_faithful,
    test_q4_partition_q8_end_to_end,
    test_q5_full_downstream_flow_no_hand_construction,
    test_q6_klein4_unchanged_round_trip,
    test_q7_gene_express_plan_q8_byte_spans_tile_on_disk,
])
def test_q_parity_pure_path(gate, monkeypatch):
    """Every gate holds identically with the native library forced OFF — the
    pure Python fallback is the COMPLETE alternative (the parity contract)."""
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    monkeypatch.setattr(_native, "LIB", None)
    gate()
