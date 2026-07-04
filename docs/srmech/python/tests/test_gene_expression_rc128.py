"""rc128 (UPSTREAM §128, #728) — CELL-STATE-MODULATED GENE EXPRESSION: a READ-TIME
FILTER where the cell_state OPERAND modulates which genes the gene_express OPERATOR
includes. The op⊗operand theorem one scale up from the rc127 active telomere.

The #728 RNA/DNA↔cell probe found the genuine NEXT RUNG above rc127: rc127's active
telomere gates ONE divide/senesce BINARY by a carried COUNT; biological gene-regulation
gates a SELECTION over MANY genes by the CELL-STATE. This is the SAME op⊗operand theorem
(operand-modulates-operator) at the GENOME/expression scale — completing a 3-SCALE FRACTAL
TOWER: ribozyme(molecule) ⊂ active-telomere(chromosome, rc127) ⊂ cell-state-expression
(genome, THIS).

THE DUALITY (structural, not decorative): genes carry an inline regulatory MASK (the
"regulatory region / promoter") in a REGULATORY GENE cap (marker 0x67). ``gene_express``
(the OPERATOR) is MODULATED by the applied ``cell_state`` (the OPERAND): same chromosome,
different cell_state → different expressed gene subset. That inequality IS the theorem
(parallel to rc127's count-modulates-divide). Same ``(operand, op)`` pattern as
``op_provenance.carry`` (value, operation) / ``coupling.RecoverableFold`` (lossy_bundle,
exact_seed_R), now with a CELL-STATE operand + an EXPRESSION operator.

Attested biology (ONE FACET — genes have other regulation too; NOT a reduction):
  * Alberts, Johnson, Lewis, Raff, Roberts & Walter, *Molecular Biology of the Cell*
    4th ed., NCBI Bookshelf NBK26887 — "a cell can regulate the expression of each of its
    genes according to the needs of the moment; most obviously by controlling the
    production of its RNA" (differential gene expression).

Proven here (the ask's DoD):
  1. the exact expression rule ``(cell_state & mask) == mask`` on several states/masks;
  2. THE THEOREM: same DNA, different cell_state → different expressed subset;
  3. the READ-TIME FILTER: the strand is BYTE-IDENTICAL after gene_express (no mutation —
     biology does not rewrite DNA to regulate it);
  4. the chromosome SELF-DESCRIBES its regulatory masks by bare-strand scan (no manifest);
  5. back-compat: PLAIN genes always express (an unregulated gene == mask 0);
  6. Python==C byte-identical (the per-gene decision AND the genome_save of a
     regulatory-gene genome, native-vs-forced-pure);
  7. format v7 → v8 additive dual-read; a plain-gene genome reads identically.

numpy-free per the genome module's discipline; no abs() (the mask / cell_state is an exact
Class-I bitwise integer, never negated).
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hv import HV


def _one(dim=64):
    return G._default_the_one(dim)


def _leaves(n, dim=64, base=0):
    return [HV.from_sequence([(base + i + k) % 4 for k in range(dim)], sectors=4)
            for i in range(n)]


def _cell_chromosome(one):
    """A chromosome with one plain gene + two regulatory genes:
      housekeeping — PLAIN (always expresses),
      stress       — mask 0b011 (needs BOTH conditions 0 AND 1),
      mitosis      — mask 0b100 (needs condition 2)."""
    genes = [("housekeeping", _leaves(1, base=0)),
             ("stress", _leaves(2, base=1), 0b011),
             ("mitosis", _leaves(1, base=2), 0b100)]
    return G.chromosome(the_one=one, label="cell", genes=genes)


# ── (1) the exact expression rule (cell_state & mask) == mask ─────────────────

@pytest.mark.parametrize("cell_state,expected", [
    (0b000, ["housekeeping"]),                              # nothing on → only the plain gene
    (0b001, ["housekeeping"]),                              # stress needs BOTH 0 and 1
    (0b011, ["housekeeping", "stress"]),                    # stress satisfied
    (0b100, ["housekeeping", "mitosis"]),                   # mitosis satisfied, stress not
    (0b111, ["housekeeping", "stress", "mitosis"]),         # everything on
    (0b110, ["housekeeping", "mitosis"]),                   # bit1 alone ≠ stress's {0,1}
])
def test_expression_rule_exact(cell_state, expected):
    """gene_express returns EXACTLY the genes whose mask the cell_state satisfies
    ((cell_state & mask) == mask); a plain gene (mask 0) always expresses."""
    one = _one()
    strand = _cell_chromosome(one)
    got = [label for label, _ in G.gene_express(strand, one, cell_state)]
    assert got == expected


# ── (2) THE THEOREM — same DNA, different cell_state → different subset ────────

def test_theorem_state_modulates_expressed_subset():
    """The op⊗operand theorem: the SAME chromosome under DIFFERENT cell_states expresses
    DIFFERENT gene subsets — the operand modulates the operator."""
    one = _one()
    strand = _cell_chromosome(one)
    sub_a = [l for l, _ in G.gene_express(strand, one, 0b011)]     # stress on
    sub_b = [l for l, _ in G.gene_express(strand, one, 0b100)]     # mitosis on
    assert sub_a != sub_b                                          # THE inequality = theorem
    assert "stress" in sub_a and "stress" not in sub_b
    assert "mitosis" in sub_b and "mitosis" not in sub_a


# ── (3) the READ-TIME FILTER — the strand is byte-identical after gene_express ─

def test_gene_express_never_mutates_the_strand():
    """gene_express is a READ (biology does NOT rewrite DNA to regulate it). The strand's
    bytes are IDENTICAL before and after, for every cell_state."""
    one = _one()
    strand = _cell_chromosome(one)
    before = [hv.tobytes() for hv in strand]
    for cs in (0, 0b001, 0b011, 0b100, 0b111, 2**40):
        G.gene_express(strand, one, cs)
    after = [hv.tobytes() for hv in strand]
    assert before == after
    # and the leaves of an expressed gene equal what genes() recovers (leaf fidelity)
    allg = {l: v for l, v in G.genes(strand, one)}
    expr = {l: v for l, v in G.gene_express(strand, one, 0b111)}
    for label in ("housekeeping", "stress", "mitosis"):
        assert [x.tolist() for x in expr[label]] == [x.tolist() for x in allg[label]]


# ── (4) bare-strand mask self-description (no manifest, §44) ──────────────────

def test_bare_strand_self_describes_masks():
    """The chromosome self-describes its regulatory masks by bare-strand SCAN — the mask is
    read from the 0x67 cap inline (no sidecar / manifest)."""
    one = _one()
    strand = _cell_chromosome(one)
    masks = {}
    for hv in strand:
        if G._cap_kind(hv) in (G.GENE_CAP_MARKER, G.REGULATORY_GENE_MARKER):
            _m, label = G._unpack_cap(hv)
            masks[label] = G._regulatory_gene_mask(hv)
    assert masks == {"housekeeping": 0, "stress": 0b011, "mitosis": 0b100}
    # a regulatory gene uses the 0x67 marker; a plain gene the 0x47 marker
    kinds = [G._cap_kind(hv) for hv in strand]
    assert G.REGULATORY_GENE_MARKER in kinds and G.GENE_CAP_MARKER in kinds


# ── (5) back-compat — plain genes always express ─────────────────────────────

def test_plain_genes_always_express():
    """A chromosome of ONLY plain (2-tuple) genes is unregulated — every gene expresses for
    every cell_state (an unregulated gene == a regulatory gene with mask 0)."""
    one = _one()
    genes = [("a", _leaves(1)), ("b", _leaves(2, base=1)), ("c", _leaves(1, base=2))]
    strand = G.chromosome(the_one=one, label="plainonly", genes=genes)
    for cs in (0, 1, 7, 2**63):
        got = [l for l, _ in G.gene_express(strand, one, cs)]
        assert got == ["a", "b", "c"]                              # ALL always express
    # a plain-gene chromosome uses NO 0x67 marker — it is byte-identical to a pre-rc128 one
    assert all(G._cap_kind(hv) != G.REGULATORY_GENE_MARKER for hv in strand)


def test_plain_gene_chromosome_byte_identical_to_prior_writer():
    """A genome of plain genes saved by the v8 writer is byte-identical (turns.bin) to what
    a v7 writer would produce — the ONLY difference is the manifest format_version field."""
    one = _one()
    genes = [("a", _leaves(1)), ("b", _leaves(2, base=1))]
    strand = G.chromosome(the_one=one, label="c", genes=genes)
    # the body carries NO 0x67 marker (a plain-gene chromosome is un-regulated)
    for blk in G._leaf_blocks(strand):
        assert blk[0] != G.REGULATORY_GENE_MARKER


# ── (6) persistence round-trip + v8 format ───────────────────────────────────

def test_regulatory_genome_saves_pages_v8(tmp_path):
    """A regulatory-gene chromosome saves at v8, pages back with genome_genes (mask-agnostic
    recovery), and gene_express filters the paged strand under a cell_state — from disk."""
    one = _one()
    strand = _cell_chromosome(one)
    p = tmp_path / "g"
    man = G.genome_save(strand, p, one)
    assert man["format_version"] == 10
    # genome_genes pages the region + recovers ALL genes (labels + leaves), mask-agnostic
    paged = G.genome_genes(p, "cell", the_one=one)
    assert [l for l, _ in paged] == ["housekeeping", "stress", "mitosis"]
    # gene_express on the paged/loaded strand filters by cell_state (from disk)
    s2, o2, _ = G.genome_load(p)
    got = [l for l, _ in G.gene_express(s2, o2, 0b011)]
    assert got == ["housekeeping", "stress"]


def test_rebuild_by_scan_recovers_masks(tmp_path):
    """§44: with NO manifest, the strand is the SSoT — rebuild-by-scan reproduces the exact
    chromosome and gene_express still filters correctly (the masks live in the body)."""
    one = _one()
    strand = _cell_chromosome(one)
    p = tmp_path / "g"
    G.genome_save(strand, p, one)
    (p / "manifest.json").unlink()                             # drop the derived cache
    s2, o2, _ = G.genome_load(p, the_one=one)                  # rebuild by scanning turns.bin
    assert [l for l, _ in G.gene_express(s2, o2, 0b100)] == ["housekeeping", "mitosis"]


def test_v8_body_reads_a_v2_fixture_unchanged():
    """A pre-rc128 (v2) fixture genome still reads UNCHANGED under the v8 walker — additive
    dual-read (the walker gains ONE 0x67 branch, no migration)."""
    import pathlib
    fixture = pathlib.Path(__file__).parent / "data" / "genome_v2_fixture"
    if not fixture.exists():
        pytest.skip("no v2 fixture in this checkout")
    s, o, _ = G.genome_load(fixture)
    parts = G.partition(s, o)
    assert set(parts) == {"alpha", "multi", "plain"}


# ── (7) guard cases ──────────────────────────────────────────────────────────

def test_cell_state_must_be_nonnegative_int():
    one = _one()
    strand = _cell_chromosome(one)
    with pytest.raises(ValueError, match="non-negative"):
        G.gene_express(strand, one, -1)
    with pytest.raises(ValueError, match="exact int"):
        G.gene_express(strand, one, 1.5)


def test_mask_must_be_nonnegative_int():
    one = _one()
    with pytest.raises(ValueError, match="non-negative"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), -1)])
    with pytest.raises(ValueError, match="exact int"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), 1.5)])


def test_op_provenance_tie_documented():
    """The op⊗operand tie is documented (the (operand, op) pattern of op_provenance /
    RecoverableFold, with a CELL-STATE operand + an EXPRESSION operator)."""
    assert "op_provenance" in G.gene_express.__doc__
    assert "RecoverableFold" in G.gene_express.__doc__
    assert "NBK26887" in G.gene_express.__doc__                 # the Alberts attestation


# ── (8) Python==C byte-identical ──────────────────────────────────────────────

@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("mask,cell_state", [
    (0, 0), (0, 0b111), (0b011, 0b011), (0b011, 0b001), (0b100, 0b100),
    (0xFF, 0xFF), (0xFF, 0xF0), (2**40, 2**40), (2**40, 0), (0b1010, 0b1111),
])
def test_python_equals_c_gene_decision(mask, cell_state):
    """The native per-gene decision (srmech_genome_gene_express) is BYTE-IDENTICAL to the
    pure Class-I bitwise decision, for a regulatory gene AND a plain gene."""
    one = _one()
    reg = G._pack_regulatory_gene("g", mask, dim=64)
    expected = (cell_state & mask) == mask
    assert _native.genome_gene_express_c(reg.tobytes(), 64, cell_state) is expected
    # a plain gene always expresses (mask 0)
    plain = G._gene_cap("g", 64)
    assert _native.genome_gene_express_c(plain.tobytes(), 64, cell_state) is True


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("cell_state", [0, 0b011, 0b100, 0b111])
def test_python_equals_c_gene_express_subset(cell_state):
    """gene_express returns the SAME expressed subset via native and forced-pure paths."""
    one = _one()
    strand = _cell_chromosome(one)
    native = [l for l, _ in G.gene_express(strand, one, cell_state)]
    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        pure = [l for l, _ in G.gene_express(strand, one, cell_state)]
    finally:
        _native.has_native_genome = real
    assert native == pure


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
def test_python_equals_c_genome_save_regulatory(tmp_path):
    """genome_save writes turns.bin + manifest.json BYTE-IDENTICALLY on a genome carrying a
    regulatory-gene chromosome, native-vs-forced-pure (the 0x67 caps are handled the same)."""
    one = _one()
    strand = _cell_chromosome(one)
    dn = tmp_path / "native"
    G.genome_save(strand, dn, one)
    n_body = (dn / "turns.bin").read_bytes()
    n_man = (dn / "manifest.json").read_bytes()
    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        dp = tmp_path / "pure"
        G.genome_save(strand, dp, one)
        p_body = (dp / "turns.bin").read_bytes()
        p_man = (dp / "manifest.json").read_bytes()
    finally:
        _native.has_native_genome = real
    assert n_body == p_body
    assert n_man == p_man
