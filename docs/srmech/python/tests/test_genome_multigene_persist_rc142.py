"""rc142 (F733 / UPSTREAM §44) — genome multi-gene PERSISTENCE via INLINE caps.

§44 replaces rc141's manifest gene-index SIDECAR with a self-describing body:
a multi-gene chromosome carries its gene boundaries + labels as fixed-width INLINE
GENE caps in ``turns.bin`` itself (the strand is the SSoT; the manifest is an
optional derived ``.fai``-style cache). So:

  * ``genome(chromosomes=…)`` returns ONE self-describing strand (no ``gene_index``,
    no 2-tuple);
  * ``genome_save(strand, path, the_one)`` drops the ``gene_index=`` param;
  * ``genome_genes(path, label)`` pages the chromosome region and SCANS the inline
    GENE caps back — no offset table.

numpy-free (the whole genome surface is).
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome
from srmech.amsc.genome import (
    CHROM_CAP_MARKER,
    GENE_CAP_MARKER,
    chromosome,
    genes,
)
from srmech.amsc.hdc import klein4_random


def _one(seed=1, dim=64):
    return klein4_random(dim, seed=seed)


def _specs():
    """Two multi-gene chromosomes (2 genes + 2 genes)."""
    one = _one()
    specs = [
        ("chess", [("rules", [klein4_random(64, seed=s) for s in (1, 2)]),
                   ("board", [klein4_random(64, seed=3)])]),
        ("music", [("scales", [klein4_random(64, seed=10)]),
                   ("chords", [klein4_random(64, seed=s) for s in (11, 12)])]),
    ]
    return one, specs


def _as_lists(xs):
    return [list(x) for x in xs]


def _markers(body, leaf_dim=64):
    return [body[k] for k in range(0, len(body), leaf_dim)]


# ── builder: ONE self-describing strand (no gene_index, no 2-tuple) ──────────
def test_genome_chromosomes_returns_single_strand_no_sidecar():
    one, specs = _specs()
    out = genome.genome(chromosomes=specs, the_one=one)
    assert isinstance(out, list)              # ONE strand, NOT a (strand, gi) tuple
    n_chrom = sum(1 for hv in out if len(hv) and int(hv[0]) == CHROM_CAP_MARKER)
    n_gene = sum(1 for hv in out if len(hv) and int(hv[0]) == GENE_CAP_MARKER)
    assert n_chrom == 2                       # one CHROM cap per chromosome
    assert n_gene == 4                        # 2 + 2 genes, one GENE cap each


# ── disk round-trip: genome_genes SCANS the inline caps back ─────────────────
def test_genome_genes_round_trips_via_inline_scan(tmp_path):
    one, specs = _specs()
    strand = genome.genome(chromosomes=specs, the_one=one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, the_one=one)          # NO gene_index=

    for label, gene_list in specs:
        recovered = genome.genome_genes(p, label)
        assert [gl for gl, _ in recovered] == [gl for gl, _ in gene_list]
        for (_, got), (_, want) in zip(recovered, gene_list):
            assert _as_lists(got) == _as_lists(want)

    # disk genome_genes == in-memory genes() for the chess chromosome
    in_mem = genes(chromosome(genes=specs[0][1], the_one=one, label="chess"), one)
    on_disk = genome.genome_genes(p, "chess")
    assert [gl for gl, _ in on_disk] == [gl for gl, _ in in_mem]
    for (_, a), (_, b) in zip(on_disk, in_mem):
        assert _as_lists(a) == _as_lists(b)


# ── the body itself carries the inline gene caps (no sidecar) ────────────────
def test_body_carries_inline_gene_caps(tmp_path):
    one, specs = _specs()
    strand = genome.genome(chromosomes=specs, the_one=one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, the_one=one)
    markers = _markers((p / "turns.bin").read_bytes())
    assert markers.count(CHROM_CAP_MARKER) == 2
    assert markers.count(GENE_CAP_MARKER) == 4
    # the manifest holds NO gene-index sidecar (§44 — strand is the SSoT)
    cat = genome.genome_catalog(p)
    assert all("genes" not in c for c in cat["chromosomes"])


# ── single-kernel chromosome: genome_genes refuses (no inline GENE caps) ──────
def test_genome_genes_refuses_single_kernel(tmp_path):
    one = _one()
    strand = genome.genome({"solo": [klein4_random(64, seed=5)]}, one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, the_one=one)
    with pytest.raises(ValueError):
        genome.genome_genes(p, "solo")


# ── partition / window FLATTEN a multi-gene genome (genes view is separate) ───
def test_partition_flattens_multigene_by_scan(tmp_path):
    one, specs = _specs()
    strand = genome.genome(chromosomes=specs, the_one=one)
    part = genome.partition(strand, one)            # §44: discovers labels by scan
    assert set(part) == {"chess", "music"}
    flat = [leaf for _gl, leaves in specs[0][1] for leaf in leaves]
    assert _as_lists(part["chess"]) == _as_lists(flat)


def test_window_and_load_round_trip(tmp_path):
    one, specs = _specs()
    strand = genome.genome(chromosomes=specs, the_one=one)
    p = tmp_path / "g"
    genome.genome_save(strand, p, the_one=one)

    # whole strand round-trips byte-for-byte
    ls, lo, ll = genome.genome_load(p)
    assert _as_lists(ls) == _as_lists(strand)
    assert set(ll) == {"chess", "music"}

    # window flattens chess to its coupled data turns (every cap skipped)
    win = genome.genome_window(p, "chess")
    expected = [hv for hv in chromosome(genes=specs[0][1], the_one=one, label="chess")
                if not (len(hv) and int(hv[0]) in (CHROM_CAP_MARKER, GENE_CAP_MARKER))]
    assert _as_lists(win) == _as_lists(expected)
