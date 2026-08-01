"""§102 G7 (rc333, task #887) — BYTE-PARITY between the two coherency projections of the
GENES FAMILY, the three wire-glue ops that earned whole-op C peers this rc:

  * ``genome.genes`` -> ``srmech_genome_genes`` — the IN-MEMORY per-gene (label, leaves)
    BOUNDARY-PRESERVING split. ``srmech_genome_recall`` FLATTENS the boundaries and
    ``srmech_genome_gene_express_plan`` returns SPANS, so neither returns this split.
  * ``genome.genome_genes`` -> ``srmech_genome_genome_genes`` — the ON-DISK sibling: obtain
    the manifest, page ONE chromosome's region (§45 cap-integrity checked), then the same split.
  * ``genome.genome_genes_expressed`` -> ``srmech_genome_genes_expressed`` — the demand-load
    ORCHESTRATION: the per-community head gate (``srmech_genome_gene_express_plan``) + the
    per-gene decision (``srmech_genome_gene_express``) existed, but the plan-walk / region-page /
    collect loop around them did not.

ADR-0009: the capability is the invariant; neither implementation is primary. So the test is NOT
"does C agree with Python" — it is "do the two projections emit the SAME (label, leaves)". The
native whole-op peer runs the WHOLE split / filter in C (the §44 scan + the carrier-aware
sc_uncouple decouple, klein4 / §Q8 / §𝕆 from the on-disk turn marker); the pure body (forced here
by disabling the native surface) is the byte-parity ORACLE (and raises the exact ValueErrors the C
peer declines on). The list assembly is the trivial formatting (the rc329 mint_plan pattern).

The three closures move ``_KNOWN_GLUE_GAPS -> _WHOLE_OP_C_PEER`` and drop ``CEIL_WIRE_GLUE_GAPS``
4 -> 1 in test_rosetta_transitive_standalone.py (only ``plasmid.add_plasmid`` remains); this file
pins the byte-parity AND that each peer is both DECLARED in the whole-op map and actually
DISPATCHED (not merely present in the lib). numpy-free; no abs() (a leaf / gene count is a
non-negative cardinality; the cell_state is an exact Class-I bitmask, never negated).
"""
from __future__ import annotations

import importlib.util
import shutil
import tempfile
from pathlib import Path

import pytest

from srmech.biology import genome as G
from srmech import _native as _N
from srmech.math.hdc import klein4_expand


def _one(seed=7):
    return klein4_expand(64, seed)


def _lv(n, base=0):
    return [klein4_expand(64, base + s) for s in range(n)]


def _norm(genes):
    """A carrier-agnostic normal form for a [(label, [HV, …]), …] result."""
    return [(l, [list(map(int, x)) for x in lv]) for l, lv in genes]


def _gene_chrom(one, label="c"):
    return G.chromosome(coupling=one, label=label,
                        genes=[("g1", _lv(2, 10)), ("g2", _lv(3, 20))])


def _saved(strand, one):
    d = Path(tempfile.mkdtemp(prefix="rc333_"))
    G.genome_save(strand, d, one)
    return d


def _load_rosetta():
    path = Path(__file__).with_name("test_rosetta_transitive_standalone.py")
    spec = importlib.util.spec_from_file_location("_rosetta_rc333", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_genes_native = pytest.mark.skipif(
    not _N.has_native_genome_genes(),
    reason="rc333 native srmech_genome_genes not built into this lib",
)
_genome_genes_native = pytest.mark.skipif(
    not _N.has_native_genome_genome_genes(),
    reason="rc333 native srmech_genome_genome_genes not built into this lib",
)
_expressed_native = pytest.mark.skipif(
    not _N.has_native_genome_genes_expressed(),
    reason="rc333 native srmech_genome_genes_expressed not built into this lib",
)


# ── genes (in-memory) — srmech_genome_genes ──────────────────────────────────

@_genes_native
@pytest.mark.parametrize("genespec", [
    [("g1", _lv(2, 10)), ("g2", _lv(3, 20))],          # multi-gene, varied leaf counts
    [("solo", _lv(4, 1))],                             # a single gene
    [("a", _lv(1, 0)), ("b", _lv(1, 9)), ("c", _lv(5, 40))],  # three genes
])
def test_genes_byte_parity(monkeypatch, genespec):
    one = _one()
    chrom = G.chromosome(coupling=one, label="c", genes=genespec)
    nat = G.genes(chrom, one)
    assert _N.has_native_genome_genes()
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        assert not _N.has_native_genome_genes()
        pur = G.genes(chrom, one)
    assert _norm(nat) == _norm(pur), "genes(): (label, leaves) split diverges"
    assert [l for l, _ in nat] == [g[0] for g in genespec]     # boundaries preserved, in order


@_genes_native
def test_genes_empty_strand(monkeypatch):
    one = _one()
    nat = G.genes([], one)
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        pur = G.genes([], one)
    assert nat == pur == []


@_genes_native
def test_genes_no_genes_flattens_to_empty(monkeypatch):
    """A single-kernel chromosome (no GENE caps) yields NO genes in BOTH projections."""
    one = _one()
    chrom = G.mint({"astro": _lv(6, 100)}, one)         # a CHROM cap + data turns, no gene caps
    nat = G.genes(chrom, one)
    with monkeypatch.context() as m:
        m.setattr(_N, "HAS_NATIVE", False)
        pur = G.genes(chrom, one)
    assert nat == pur == []


@_genes_native
def test_genes_c_returns_the_structure_directly():
    """The C peer really produces the split (not a silent None -> pure)."""
    one = _one()
    chrom = _gene_chrom(one)
    sb = b"".join(h.tobytes() for h in chrom)
    got = _N.genome_genes_c(sb, len(chrom), 64, one.tobytes())
    assert got is not None
    assert [lbl for lbl, _ in got] == ["g1", "g2"]
    assert [len(lv) for _, lv in got] == [2, 3]         # per-gene leaf counts preserved


# ── genome_genes (on-disk) — srmech_genome_genome_genes ──────────────────────

@_genome_genes_native
def test_genome_genes_byte_parity(monkeypatch):
    one = _one()
    strand = G.genome(coupling=one, chromosomes=[
        ("cc", [("a", _lv(2, 1)), ("b", _lv(3, 5))]),
        ("dd", [("x", _lv(1, 30)), ("y", _lv(2, 40))]),
    ])
    d = _saved(strand, one)
    try:
        for lbl in ("cc", "dd"):
            nat = G.genome_genes(str(d), lbl)
            with monkeypatch.context() as m:
                m.setattr(_N, "HAS_NATIVE", False)
                pur = G.genome_genes(str(d), lbl)
            assert _norm(nat) == _norm(pur), f"genome_genes({lbl!r}) diverges"
        # and the on-disk read == the in-memory genes() of the same chromosome
        assert _norm(G.genome_genes(str(d), "cc")) == _norm(
            [("a", _lv(2, 1)), ("b", _lv(3, 5))])
    finally:
        shutil.rmtree(d, ignore_errors=True)


@_genome_genes_native
def test_genome_genes_bad_label_error_parity(monkeypatch):
    one = _one()
    strand = G.genome(coupling=one, chromosomes=[("cc", [("a", _lv(2, 1))])])
    d = _saved(strand, one)
    try:
        with pytest.raises(ValueError):
            G.genome_genes(str(d), "missing")
        with monkeypatch.context() as m:
            m.setattr(_N, "HAS_NATIVE", False)
            with pytest.raises(ValueError):
                G.genome_genes(str(d), "missing")
    finally:
        shutil.rmtree(d, ignore_errors=True)


@_genome_genes_native
def test_genome_genes_no_gene_caps_error_parity(monkeypatch):
    """A single-kernel chromosome (no inline GENE caps) raises in BOTH projections — the C peer
    returns an EMPTY split and the caller raises the exact ValueError."""
    one = _one()
    strand = G.mint({"astro": _lv(6, 100)}, one)        # single-kernel: CHROM cap + data, no genes
    d = _saved(strand, one)
    try:
        with pytest.raises(ValueError):
            G.genome_genes(str(d), "astro")
        with monkeypatch.context() as m:
            m.setattr(_N, "HAS_NATIVE", False)
            with pytest.raises(ValueError):
                G.genome_genes(str(d), "astro")
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── genome_genes_expressed (on-disk, regulatory + chromatin) ─────────────────

_B0, _B1, _B2, _B3 = 1 << 0, 1 << 1, 1 << 2, 1 << 3
_ALL = _B0 | _B1 | _B2 | _B3


def _regulatory_genome(one):
    """A mixed-gate two-community genome (the rc135 layout): an always-on organelle + four
    nuclear communities, one delivered gate KIND each (E1 / E2 / E4 / E3)."""
    org = {"gate": "boolean", "dnf": [(0, 0)]}          # E2 tautology (always on)
    e2 = {"gate": "boolean", "dnf": [(_B1, 0)]}
    e4 = {"gate": "threshold", "weights": [0, 0, 5], "threshold": 5}
    e3 = {"gate": "graded", "weights": [0, 0, 0, 7], "denom": 7}
    communities = [("mito", org), ("nuc_e1", _B0), ("nuc_e2", e2),
                   ("nuc_e4", e4), ("nuc_e3", e3)]
    chrom_list = []
    for name, gate in communities:
        chrom_list.append((name, [(name + "_h", _lv(2, 0), gate),
                                   (name + "_b", _lv(3, 1), gate)]))
    return G.genome(coupling=one, chromosomes=chrom_list)


@_expressed_native
@pytest.mark.parametrize("cs", [0, _B0, _B1, _B2, _B3, _B0 | _B2, _ALL])
def test_genome_genes_expressed_byte_parity(monkeypatch, cs):
    one = _one()
    d = _saved(_regulatory_genome(one), one)
    try:
        nat = G.genome_genes_expressed(str(d), one, cs)
        assert _N.has_native_genome_genes_expressed()
        with monkeypatch.context() as m:
            m.setattr(_N, "HAS_NATIVE", False)
            assert not _N.has_native_genome_genes_expressed()
            pur = G.genome_genes_expressed(str(d), one, cs)
        assert _norm(nat) == _norm(pur), f"genome_genes_expressed(cs={cs}) diverges"
    finally:
        shutil.rmtree(d, ignore_errors=True)


@_expressed_native
def test_genome_genes_expressed_chromatin_gated_byte_parity(monkeypatch):
    """A CONDENSED (chromatin-silenced) community contributes no expressed gene — the §98 outer
    gate. The two projections must agree with the cap present, silenced AND re-opened."""
    one = _one()
    base = G.genome(coupling=one, chromosomes=[
        ("plain", [("p1", _lv(2, 1)), ("p2", _lv(2, 5))]),
        ("gated", [("g1", _lv(2, 9)), ("g2", _lv(2, 13))]),
    ])
    # facultative heterochromatin over the 'gated' chromosome: accessible only when bit0 present
    cond = G.condense(base, coupling=one, label="gated",
                      state={"activator": _B0, "repressor": 0}, region=None)
    d = _saved(cond, one)
    try:
        for cs in (0, _B0, _B1):
            nat = G.genome_genes_expressed(str(d), one, cs)
            with monkeypatch.context() as m:
                m.setattr(_N, "HAS_NATIVE", False)
                pur = G.genome_genes_expressed(str(d), one, cs)
            assert _norm(nat) == _norm(pur), f"chromatin-gated cs={cs} diverges"
    finally:
        shutil.rmtree(d, ignore_errors=True)


@_expressed_native
def test_genome_genes_expressed_matches_full_gene_express(monkeypatch):
    """The partial-load reader == the expressed subset of a full in-memory gene_express."""
    one = _one()
    strand = _regulatory_genome(one)
    d = _saved(strand, one)
    try:
        for cs in (0, _B1, _ALL):
            got = G.genome_genes_expressed(str(d), one, cs)
            full = G.gene_express(strand, one, cs)
            assert _norm(got) == _norm(full), f"cs={cs}: partial-load != full-load-filtered"
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── peers declared-and-dispatched + the gap closure ──────────────────────────

def test_rc333_peers_declared_and_gaps_closed():
    """The three ops left ``_KNOWN_GLUE_GAPS`` for ``_WHOLE_OP_C_PEER``; the map names the right
    symbols and none is still a gap. The full transitive ratchet + the DOWN-ONLY global ceiling
    pin live in test_rosetta_transitive_standalone.py; this is a local coherence pin for THESE ops."""
    r = _load_rosetta()
    assert r._WHOLE_OP_C_PEER["srmech.biology.genome.genes"] == "srmech_genome_genes"
    assert r._WHOLE_OP_C_PEER["srmech.biology.genome.genome_genes"] == "srmech_genome_genome_genes"
    assert (r._WHOLE_OP_C_PEER["srmech.biology.genome.genome_genes_expressed"]
            == "srmech_genome_genes_expressed")
    for op in ("genes", "genome_genes", "genome_genes_expressed"):
        assert f"srmech.biology.genome.{op}" not in r._KNOWN_GLUE_GAPS
    # rc334 closed the last gap (add_plasmid): _KNOWN_GLUE_GAPS is now EMPTY and the
    # DOWN-ONLY ceiling agrees at 0 (see test_genome_add_plasmid_c_rc334.py).
    assert set(r._KNOWN_GLUE_GAPS) == set()
    assert len(r._KNOWN_GLUE_GAPS) == r.CEIL_WIRE_GLUE_GAPS == 0


def test_rc333_peers_are_actually_dispatched():
    """The other half of the ADR-0003 proof: each op REACHES its declared peer through its
    dispatch glue (the rc273 failure mode was a declared-but-unreached symbol)."""
    r = _load_rosetta()
    objs = r._live_objects()
    for op, sym in (("srmech.biology.genome.genes", "srmech_genome_genes"),
                    ("srmech.biology.genome.genome_genes", "srmech_genome_genome_genes"),
                    ("srmech.biology.genome.genome_genes_expressed",
                     "srmech_genome_genes_expressed")):
        fn = objs.get(op)
        assert fn is not None, f"{op} not importable"
        assert sym in r._glue_c_symbols(fn), f"{op} does not dispatch {sym}"
