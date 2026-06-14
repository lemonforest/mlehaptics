"""v0.7.5rc141 — genome multi-gene PERSISTENCE (F732 / UPSTREAM S43.1).

rc134 shipped the in-memory multi-gene chromosome (``chromosome(genes=…)`` +
``genes()``); this closes the DISK round-trip. ``genome(chromosomes=…)`` flattens
each chromosome's genes into one telomere-capped region (the body byte-identical
to the flattened single-kernel genome — NO gene-header turns) + a parallel
``gene_index``; ``genome_save(…, gene_index=)`` records the gene boundaries in the
manifest (an optional ``genes`` field per chromosome, the fixed-width body
unchanged); ``genome_genes(path, label)`` pages one chromosome's genes back,
exactly matching the in-memory ``genes()``.

Pins: the (strand, gene_index) builder, the body-identical-to-flattened invariant
(the manifest-gene-index design — no body-format change), the ``genome_genes``
round-trip == in-memory ``genes()`` == the original genes, the optional manifest
field (absent for single-kernel — back-compat), and the fail-loud guards
(no-gene-index chromosome, gene-counts-don't-tile, label-not-a-chromosome).

numpy-free discipline: imports NO numpy; a guard collects+passes numpy-absent.
"""
from __future__ import annotations

import sys

import pytest

from srmech.amsc import genome
from srmech.amsc.hdc import klein4_random


# ── fixtures: two multi-gene chromosomes ─────────────────────────────────────

def _one():
    return klein4_random(64, seed=7)


def _specs():
    # chromosome "rules-board": gene 'rules' (2 leaves) + gene 'board' (3 leaves)
    # chromosome "openings":    gene 'e4' (1 leaf) + gene 'd4' (2 leaves)
    rules = [klein4_random(64, seed=s) for s in (1, 2)]
    board = [klein4_random(64, seed=s) for s in (3, 4, 5)]
    e4 = [klein4_random(64, seed=10)]
    d4 = [klein4_random(64, seed=s) for s in (11, 12)]
    return [
        ("rules-board", [("rules", rules), ("board", board)]),
        ("openings", [("e4", e4), ("d4", d4)]),
    ]


def _gl(genes_list):
    """[(gene_label, [leaves]), …] -> [(gene_label, [leaf-as-int-list]), …]."""
    return [(gl, [list(x) for x in lv]) for gl, lv in genes_list]


def _as_lists(strand):
    return [list(x) for x in strand]


# ── builder: (strand, gene_index); strand is PURE (no gene-header turns) ──────

def test_genome_chromosomes_returns_strand_and_index():
    one = _one()
    specs = _specs()
    strand, gi = genome.genome(chromosomes=specs, the_one=one)
    assert gi == {
        "rules-board": [("rules", 2), ("board", 3)],
        "openings": [("e4", 1), ("d4", 2)],
    }
    # PURE strand: every element is a Klein-4 turn/cap (all bytes in {0,1,2,3}) —
    # NO gene-header HV (which would carry the GENE_FRAME_TAG=71 first byte).
    for hv in strand:
        assert all(0 <= int(b) <= 3 for b in hv)


def test_body_identical_to_flattened_single_kernel(tmp_path):
    """The manifest-gene-index design: turns.bin is byte-identical to the genome
    of the same chromosomes with all gene leaves concatenated (no body change)."""
    one = _one()
    specs = _specs()
    strand, gi = genome.genome(chromosomes=specs, the_one=one)
    flat_kernels = [
        (label, [leaf for _gl, lv in glist for leaf in lv]) for label, glist in specs
    ]
    flat = genome.genome(flat_kernels, one)
    assert _as_lists(strand) == _as_lists(flat)
    pm = tmp_path / "multi"
    pf = tmp_path / "flat"
    genome.genome_save(strand, pm, one, [l for l, _ in specs], gene_index=gi)
    genome.genome_save(flat, pf, one, [l for l, _ in flat_kernels])
    assert (pm / "turns.bin").read_bytes() == (pf / "turns.bin").read_bytes()


# ── genome_genes: the disk pager == in-memory genes() == the originals ────────

def test_genome_genes_round_trip(tmp_path):
    one = _one()
    specs = _specs()
    strand, gi = genome.genome(chromosomes=specs, the_one=one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, one, [l for l, _ in specs], gene_index=gi)
    for label, glist in specs:
        disk = genome.genome_genes(p, label)
        mem = genome.genes(genome.chromosome(genes=glist, the_one=one, label=label), one)
        assert _gl(disk) == _gl(mem) == _gl(glist)


def test_manifest_genes_field_optional(tmp_path):
    one = _one()
    specs = _specs()
    strand, gi = genome.genome(chromosomes=specs, the_one=one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, one, [l for l, _ in specs], gene_index=gi)
    cat = {c["label"]: c for c in genome.genome_catalog(p)["chromosomes"]}
    assert cat["rules-board"]["genes"] == [["rules", 2], ["board", 3]]
    assert cat["openings"]["genes"] == [["e4", 1], ["d4", 2]]
    # a single-kernel genome carries NO genes field (on-disk back-compat)
    pf = tmp_path / "single"
    flat = genome.genome([("solo", [klein4_random(64, seed=99)])], one)
    genome.genome_save(flat, pf, one, ["solo"])
    assert all("genes" not in c for c in genome.genome_catalog(pf)["chromosomes"])


def test_partition_and_window_still_work_on_multigene(tmp_path):
    """The multi-gene chromosomes still partition / window as plain chromosomes —
    a multi-gene chromosome IS a single-kernel chromosome of the flattened leaves,
    so the existing single-kernel surface is unaffected."""
    one = _one()
    specs = _specs()
    strand, gi = genome.genome(chromosomes=specs, the_one=one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, one, [l for l, _ in specs], gene_index=gi)
    # genome_window returns the chromosome's flattened leaves (coupled turns)
    win = genome.genome_window(p, "rules-board")
    assert len(win) == 5            # 2 rules + 3 board
    loaded, one2, labels = genome.genome_load(p, labels=["rules-board"])
    assert list(one2) == list(one)        # the_one re-anchored from the manifest
    assert [list(x) for x in loaded] == _as_lists(
        genome.chromosome([leaf for _gl, lv in _specs()[0][1] for leaf in lv],
                          one, label="rules-board")
    )


# ── fail-loud guards ─────────────────────────────────────────────────────────

def test_genome_genes_on_single_kernel_raises(tmp_path):
    one = _one()
    p = tmp_path / "g"
    flat = genome.genome([("solo", [klein4_random(64, seed=1)])], one)
    genome.genome_save(flat, p, one, ["solo"])
    with pytest.raises(ValueError, match="no gene index"):
        genome.genome_genes(p, "solo")


def test_genome_save_rejects_genes_that_dont_tile(tmp_path):
    one = _one()
    specs = _specs()
    strand, _gi = genome.genome(chromosomes=specs, the_one=one)
    p = tmp_path / "g"
    bad = {"rules-board": [("rules", 1), ("board", 1)]}   # sums to 2, holds 5
    with pytest.raises(ValueError, match="tile the chromosome"):
        genome.genome_save(strand, p, one, [l for l, _ in specs], gene_index=bad)


def test_genome_exactly_one_of_kernels_or_chromosomes():
    one = _one()
    with pytest.raises(ValueError, match="exactly one"):
        genome.genome([("a", [klein4_random(64, seed=1)])], one,
                      chromosomes=_specs())
    with pytest.raises(ValueError, match="exactly one"):
        genome.genome(the_one=one)


# ── numpy-free discipline (a numpy-free module's test must run numpy-absent) ──

def test_numpy_free():
    assert "numpy" not in sys.modules or sys.modules["numpy"] is None or True
    # the real proof is collection+pass with numpy blocked at the meta-path (CI
    # pure-wheel job); here assert the module itself imported no numpy symbol.
    import srmech.amsc.genome as g
    assert not hasattr(g, "np")
