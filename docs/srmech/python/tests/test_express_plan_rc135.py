"""rc135 (UPSTREAM §134, #1273, siona green-light) — DEMAND-LOADED gene expression:
``gene_express_plan`` (the offset-only LOAD-PLAN — the expressed set + on-disk byte
ranges WITHOUT touching content) + ``genome_genes_expressed`` (the PARTIAL-LOAD reader —
seek only the expressed byte-ranges → byte-identical to the full-load-filtered, WITHOUT
loading the unexpressed). Makes the #736 probe shippable: bounded RAM WITHOUT bounded
availability.

Proven here (the ask's DoD):
  (i)   the STRAND-variant plan expressed-set == gene_express on the full strand
        (all cell_states, several chromosomes);
  (ii)  genome_genes_expressed recovers BYTE-IDENTICAL leaves vs the expressed subset of
        a full gene_express (the partial-load == the full-load-filtered);
  (iii) the PATH (variant b) plan uses the manifest offsets + does NOT read the full body —
        bytes-touched << full-body-bytes (bounded I/O, measured through the read seam);
  (iv)  the SIONA TWO-GENOME LAYOUT: an ORGANELLE chromosome (E2 always-on service gate)
        + NUCLEAR chromosomes (E1/E2/E4/E3 single-community gates) → the plan ALWAYS
        includes the organelle + ONLY the cell_state-matching nuclear chromosome;
  (v)   read-only (the strand + turns.bin are byte-identical after both ops);
  (vi)  Python==C byte-identical (the plan offsets + the partial-load leaves).

NO format addition (the ops READ existing caps/manifest — genome format v11 stays).
numpy-free; no abs() (cell_state is an exact Class-I bitwise integer, never negated).
"""
from __future__ import annotations

import pathlib
import tempfile

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native

LEAF = G.LEAF_CAP
B0, B1, B2, B3 = 1 << 0, 1 << 1, 1 << 2, 1 << 3
ALLB = B0 | B1 | B2 | B3

# The siona TWO-GENOME layout + the delivered gate FAMILY (E1/E2/E4/E3), one kind per
# nuclear community. Every gene in a community carries the SAME gate, so the per-chromosome
# HEAD gate IS the community gate (head off <=> the whole community off) — the invariant the
# demand-load skip rests on.
_ORG = {"gate": "boolean", "dnf": [(0, 0)]}          # E2 tautology: the always-on organelle
_E2_B1 = {"gate": "boolean", "dnf": [(B1, 0)]}       # E2 boolean, gated on bit1
_E4_B2 = {"gate": "threshold", "weights": [0, 0, 5], "threshold": 5}   # E4, gated on bit2
_E3_B3 = {"gate": "graded", "weights": [0, 0, 0, 7], "denom": 7}       # E3, gated on bit3

#: (chrom_label, gate_spec, the community bit — None for the always-on organelle)
_COMMUNITIES = [
    ("mito",   _ORG,   None),   # ORGANELLE — E2 always-on service gate (any cell_state)
    ("nuc_e1", B0,     B0),     # NUCLEAR — E1 activator (int 3-tuple), gated on bit0
    ("nuc_e2", _E2_B1, B1),     # NUCLEAR — E2 boolean, gated on bit1
    ("nuc_e4", _E4_B2, B2),     # NUCLEAR — E4 threshold, gated on bit2
    ("nuc_e3", _E3_B3, B3),     # NUCLEAR — E3 graded, gated on bit3
]


def _leaves(n, fill):
    return [[(fill + i) & 3 for i in range(LEAF)] for _ in range(n)]


def _build(tmp, head=4, body=8):
    """Build + save the mixed two-genome layout; return (strand, the_one, dir)."""
    one = G._default_the_one(LEAF)
    chrom_list = []
    for name, gate, _bit in _COMMUNITIES:
        genes = [(name + "_head", _leaves(head, 0), gate),
                 (name + "_body", _leaves(body, 1), gate)]
        chrom_list.append((name, genes))
    strand = G.genome(the_one=one, chromosomes=chrom_list)
    G.genome_save(strand, tmp, one)
    return strand, one


def _expected_communities(cell_state):
    """The communities whose head gate expresses under cell_state — the organelle ALWAYS,
    each nuclear community iff its bit is present."""
    out = ["mito"]
    for name, _gate, bit in _COMMUNITIES:
        if bit is not None and (cell_state & bit) == bit:
            out.append(name)
    return out


def _norm(genes):
    return [(l, [list(map(int, x)) for x in lv]) for l, lv in genes]


class _CountFile:
    """A read-only file proxy counting bytes actually read (the bounded-I/O probe)."""

    def __init__(self, f):
        self.f = f
        self.n = 0

    def seek(self, *a):
        return self.f.seek(*a)

    def read(self, *a):
        b = self.f.read(*a)
        self.n += len(b)
        return b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.f.close()
        return False


@pytest.fixture()
def counting_seam(monkeypatch):
    """Route the demand-load ops' body reads through a counting proxy + force the pure
    path (so the bytes-touched is measurable in Python; the C path reads the same by
    construction)."""
    opened = []
    orig = G._open_body_ro

    def wrap(p):
        cf = _CountFile(orig(p))
        opened.append(cf)
        return cf

    monkeypatch.setattr(G, "_open_body_ro", wrap)
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)
    return opened


# ── (i) STRAND-variant plan expressed-set == gene_express ─────────────────────────
def test_strand_plan_matches_gene_express():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135i_"))
    strand, one = _build(tmp)
    for cs in range(0, ALLB + 1):
        plan = G.gene_express_plan(strand, one, cs)
        plan_labels = sorted(p[0] for p in plan)
        ge_labels = sorted(l for l, _ in G.gene_express(strand, one, cs))
        assert plan_labels == ge_labels, f"cs={cs}: {plan_labels} != {ge_labels}"
        # the STRAND plan never returns a negative / zero-width span
        for _lbl, off, ln in plan:
            assert off >= 0 and ln >= LEAF


# ── (ii) partial-load byte-identical vs the full-load-filtered ────────────────────
def test_partial_load_byte_identical():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135ii_"))
    strand, one = _build(tmp)
    for cs in range(0, ALLB + 1):
        got = G.genome_genes_expressed(str(tmp), one, cs)
        full = G.gene_express(strand, one, cs)          # the whole-genome ground truth
        assert _norm(got) == _norm(full), f"cs={cs}"


# ── (iii) variant-b bounded I/O — the plan does NOT read the full body ────────────
def test_variant_b_bounded_io(counting_seam):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135iii_"))
    _build(tmp, head=4, body=40)                        # sizeable bodies → dramatic skip
    one = G._default_the_one(LEAF)
    full_body = (tmp / G._BODY_NAME).stat().st_size
    counting_seam.clear()
    plan = G.gene_express_plan(str(tmp), one, B1)       # a physics-only query
    plan_bytes = sum(cf.n for cf in counting_seam)
    # the PLAN touches only one leaf_dim gate cap per chromosome — << the full body
    assert plan_bytes <= len(_COMMUNITIES) * LEAF
    assert plan_bytes < full_body // 2
    assert sorted(p[0] for p in plan) == sorted(_expected_communities(B1))
    # the READER pages only the expressed regions (organelle + the one nuclear) — the
    # unexpressed nuclear communities are never touched
    counting_seam.clear()
    G.genome_genes_expressed(str(tmp), one, B1)
    reader_bytes = sum(cf.n for cf in counting_seam)
    assert reader_bytes < full_body, (reader_bytes, full_body)


# ── (iv) the SIONA two-genome layout: organelle-always + nuclear-matched ──────────
def test_two_genome_layout():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135iv_"))
    _build(tmp)
    one = G._default_the_one(LEAF)
    for cs in [0, B0, B1, B2, B3, B0 | B2, ALLB]:
        plan_labels = sorted(p[0] for p in G.gene_express_plan(str(tmp), one, cs))
        assert "mito" in plan_labels, f"organelle must ALWAYS be in the plan (cs={cs})"
        assert plan_labels == sorted(_expected_communities(cs)), f"cs={cs}"
    # each single-community query yields exactly {organelle, the matching nuclear}
    assert sorted(p[0] for p in G.gene_express_plan(str(tmp), one, B0)) == ["mito", "nuc_e1"]
    assert sorted(p[0] for p in G.gene_express_plan(str(tmp), one, B3)) == ["mito", "nuc_e3"]


# ── (v) read-only: the strand + turns.bin are byte-identical after both ops ───────
def test_read_only():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135v_"))
    strand, one = _build(tmp)
    strand_before = [list(map(int, hv.tolist())) for hv in strand]
    body_before = (tmp / G._BODY_NAME).read_bytes()
    G.gene_express_plan(strand, one, B1)                # STRAND variant
    G.gene_express_plan(str(tmp), one, B1)              # PATH variant
    G.genome_genes_expressed(str(tmp), one, B1)         # partial-load reader
    assert [list(map(int, hv.tolist())) for hv in strand] == strand_before
    assert (tmp / G._BODY_NAME).read_bytes() == body_before


# ── (vi) Python==C byte-identical (plan offsets + partial-load leaves) ────────────
@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built")
def test_python_equals_c(monkeypatch):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135vi_"))
    strand, one = _build(tmp)
    for cs in range(0, ALLB + 1):
        monkeypatch.setattr(_native, "has_native_genome", lambda: True)
        plan_c = G.gene_express_plan(str(tmp), one, cs)
        genes_c = G.genome_genes_expressed(str(tmp), one, cs)
        monkeypatch.setattr(_native, "has_native_genome", lambda: False)
        plan_py = G.gene_express_plan(str(tmp), one, cs)
        genes_py = G.genome_genes_expressed(str(tmp), one, cs)
        assert plan_c == plan_py, f"plan offsets differ cs={cs}: {plan_c} != {plan_py}"
        assert _norm(genes_c) == _norm(genes_py), f"leaves differ cs={cs}"


# ── mixed E1/E2/E4/E3 gate-types across chromosomes — the plan gates by kind ──────
def test_mixed_gate_types():
    """The four delivered gate KINDS (E1 0x67 / E2 0x62 / E4 0x77 / E3 0x64) coexist in one
    genome; the plan gates each community by its inline gate regardless of kind."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135mx_"))
    strand, one = _build(tmp)
    # a query that hits exactly ONE nuclear kind at a time, plus the always-on organelle
    for bit, want in [(B0, "nuc_e1"), (B1, "nuc_e2"), (B2, "nuc_e4"), (B3, "nuc_e3")]:
        labels = sorted(p[0] for p in G.gene_express_plan(str(tmp), one, bit))
        assert labels == sorted(["mito", want]), (bit, labels)
        # and the partial-load recovers exactly that community's genes + the organelle's
        got = G.genome_genes_expressed(str(tmp), one, bit)
        assert _norm(got) == _norm(G.gene_express(strand, one, bit))


# ── no format bump: the ops read the existing v11 caps/manifest ───────────────────
def test_no_format_bump():
    assert G.GENOME_FORMAT_VERSION == 11


# ── the STRAND-variant plan also delimits directly loadable gene byte-ranges ──────
def test_strand_plan_partial_load_byte_identical():
    """A partial-load using the STRAND (variant a) plan's byte-ranges recovers each
    expressed gene's leaves byte-identically (the probe-a mechanic)."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="rc135sa_"))
    strand, one = _build(tmp)
    body = (tmp / G._BODY_NAME).read_bytes()
    for cs in [B0, B1 | B2, ALLB]:
        plan = G.gene_express_plan(strand, one, cs)
        loaded = []
        for lbl, off, ln in plan:
            region = body[off:off + ln]
            lv = [G.quad_turn(dec, one)
                  for _raw, dec in G._walk_region_blocks(region, LEAF, context=lbl)
                  if not G._block_is_cap(dec)]
            loaded.append((lbl, lv))
        assert _norm(loaded) == _norm(G.gene_express(strand, one, cs)), f"cs={cs}"
