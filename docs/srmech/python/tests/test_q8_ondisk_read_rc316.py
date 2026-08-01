"""rc316 — ON-DISK Q8 gene-genome READ completeness prove-gates (R1-R5).

rc315 completed the IN-MEMORY Q8 read surface (genes / gene_express / partition /
mint_strand + gene_express_plan) but LEFT the ON-DISK path readers on the klein4
default: ``genome_genes`` / ``genome_genes_expressed`` delegated to
``genes()`` / ``gene_express()`` WITHOUT threading element_type, so reading a SAVED
Q8 GENE genome RAISED (``klein4_bind: elements must be in {0,1,2,3}`` — the Q8
leaves carry bytes 4..7). rc316 makes them SELF-DESCRIBING: the stored v16 head
carries the element_type ``carrier`` ("klein4"/"q8"), surfaced by ``_catalog_data``
as ``data["carrier"]``; the readers derive element_type from it and thread it into
the decode. Python-only — ABI (10), GENOME_FORMAT_VERSION (16) and the tool count
(491) all UNCHANGED.

* R1 — ``genome_genes`` on a saved Q8 GENE genome == the in-memory
        ``genes(element_type=Q8)`` truth, EXACTLY (per gene, per leaf).
* R2 — ``genome_genes_expressed`` on a saved Q8 GENE genome == the in-memory
        ``gene_express(element_type=Q8)`` truth, EXACTLY.
* R3 — the head stores + surfaces ``carrier=="q8"``; the SAFE sibling
        ``genome_window`` is element_type-AGNOSTIC (returns raw coupled turns, never
        decouples) — it does not raise on a Q8 genome.
* R4 — klein4 UNCHANGED: a saved klein4 gene genome reads byte-identically through
        both on-disk readers (no regression).
* R5 — backward-faithful: the on-disk Q8 leaves' V4 projection == the klein4
        genome's on-disk leaves.

numpy-free (the suite runs numpy-ABSENT); native == pure re-verified by forcing the
pure path (R_PARITY).
"""
from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc.cascade.one import the_one
from srmech.math.hdc import klein4_from_one
from srmech.math.hv import HV
from srmech.amsc.q8 import q8_from_one, q8_project_v4

Q8 = G.ELEMENT_TYPE_Q8
K4 = G.ELEMENT_TYPE_KLEIN4
D = 48


def _q8_one():
    return q8_from_one(the_one(1, 5, 11), D)


def _k4_one():
    return klein4_from_one(the_one(1, 5, 11), D)


def _lift(k4_hv, tag):
    """A Q8 leaf whose V4 projection is EXACTLY the klein4 leaf (non-trivial signs)."""
    kb = k4_hv.tobytes()
    sign = klein4_from_one(the_one(1, tag, 5), D).tobytes()
    return HV.from_sequence(
        bytes(((sign[i] & 1) << 2) | (kb[i] & 3) for i in range(D)), sectors=8)


def _k4_gene_leaves():
    return {"g": [klein4_from_one(the_one(1, 13 + i, 9), D) for i in range(2)],
            "h": [klein4_from_one(the_one(1, 21, 9), D)]}


def _q8_gene_leaves():
    return {"g": [_lift(klein4_from_one(the_one(1, 13 + i, 9), D), 7 + i) for i in range(2)],
            "h": [_lift(klein4_from_one(the_one(1, 21, 9), D), 30)]}


def _saved(leaves, one, element_type):
    """Build + save a gene genome; return (dir, in-memory genes() truth dict)."""
    strand = G.chromosome(genes=[(l, leaves[l]) for l in leaves], coupling=one,
                          element_type=element_type)
    mem = {l: lv for l, lv in G.genes(strand, one, element_type=element_type)}
    d = tempfile.mkdtemp()
    G.genome_save(strand, d, one, element_type=element_type)
    return d, mem


# ── R1 ────────────────────────────────────────────────────────────────────────
def test_r1_genome_genes_q8_reads_exact():
    one = _q8_one()
    d, mem = _saved(_q8_gene_leaves(), one, Q8)
    try:
        labels = [c["label"] for c in G._catalog_data(__import__("pathlib").Path(d), one)["chromosomes"]]
        for lbl in labels:
            og = G.genome_genes(d, lbl, coupling=one)
            assert og, "on-disk Q8 gene read must be non-empty"
            for gene_label, leaves in og:
                assert leaves == mem[gene_label], f"gene {gene_label} != in-memory Q8 truth"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── R2 ────────────────────────────────────────────────────────────────────────
def test_r2_genome_genes_expressed_q8_reads_exact():
    one = _q8_one()
    d, mem = _saved(_q8_gene_leaves(), one, Q8)
    try:
        oge = G.genome_genes_expressed(d, one, 0)
        assert [gl for gl, _ in oge] == list(mem), "expressed labels must match in-memory"
        for gene_label, leaves in oge:
            assert leaves == mem[gene_label], f"expressed gene {gene_label} != Q8 truth"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── R3 ────────────────────────────────────────────────────────────────────────
def test_r3_carrier_surfaced_and_window_agnostic():
    one = _q8_one()
    d, _ = _saved(_q8_gene_leaves(), one, Q8)
    try:
        from pathlib import Path
        data = G._catalog_data(Path(d), one)
        assert data.get("carrier") == "q8", "the v16 head must surface carrier='q8'"
        assert G._ELEMENT_TYPE_CODES.get(data["carrier"]) == Q8
        # the SAFE sibling: genome_window returns RAW coupled turns (no decouple) — must
        # NOT raise on a Q8 genome (element_type-agnostic; the audit's SAFE classification).
        labels = [c["label"] for c in data["chromosomes"]]
        win = G.genome_window(d, labels[0], coupling=one)
        assert win is not None
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── R4 ────────────────────────────────────────────────────────────────────────
def test_r4_klein4_ondisk_unchanged():
    one = _k4_one()
    d, mem = _saved(_k4_gene_leaves(), one, K4)
    try:
        from pathlib import Path
        assert G._catalog_data(Path(d), one).get("carrier") == "klein4"
        labels = [c["label"] for c in G._catalog_data(Path(d), one)["chromosomes"]]
        for lbl in labels:
            for gene_label, leaves in G.genome_genes(d, lbl, coupling=one):
                assert leaves == mem[gene_label]
        for gene_label, leaves in G.genome_genes_expressed(d, one, 0):
            assert leaves == mem[gene_label]
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── R5 ────────────────────────────────────────────────────────────────────────
def test_r5_ondisk_q8_backward_faithful_to_klein4():
    q8_one, k4_one = _q8_one(), _k4_one()
    dq, _ = _saved(_q8_gene_leaves(), q8_one, Q8)
    dk, _ = _saved(_k4_gene_leaves(), k4_one, K4)
    try:
        eq = G.genome_genes_expressed(dq, q8_one, 0)
        ek = G.genome_genes_expressed(dk, k4_one, 0)
        assert [l for l, _ in eq] == [l for l, _ in ek]
        for (_, lq), (_, lk) in zip(eq, ek):
            assert [bytes(q8_project_v4(x)) for x in lq] == [y.tobytes() for y in lk]
    finally:
        shutil.rmtree(dq, ignore_errors=True)
        shutil.rmtree(dk, ignore_errors=True)


# ── PARITY: native == pure (force the pure path, re-run the gates) ─────────────
@pytest.mark.parametrize("gate", [
    test_r1_genome_genes_q8_reads_exact,
    test_r2_genome_genes_expressed_q8_reads_exact,
    test_r3_carrier_surfaced_and_window_agnostic,
    test_r4_klein4_ondisk_unchanged,
    test_r5_ondisk_q8_backward_faithful_to_klein4,
])
def test_r_parity_pure_path(gate, monkeypatch):
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    monkeypatch.setattr(_native, "LIB", None)
    gate()
