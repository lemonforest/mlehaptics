"""v0.9.0rc270 (§100 GAP 1 / PR#687 F1249) — genome.mint_strand.

MINT an ALREADY-PACKED strand: splice a §95a interior CENTROMERE (0x58) at the p:q
arm-split, turning a Tier-1 PLASMID into a Tier-2 NUCLEAR chromosome — WITHOUT re-minting
it from leaves. The capability §100 GAP 1 named as missing: the corpus directed-graph
store (graph_to_kernel) returns an HV-strand, and chromosome(strand, centromere=…)
REJECTS it (it treats the packed strand as raw leaves and quad_turn binds the 256-sector
telomere cap -> "klein-4 elements must be in {0,1,2,3}"), and there was no centromere=
hook on graph_to_kernel — so a directed-graph chromosome could not be given a p:q
centromere (simplewiki_directed.genome censused {plasmid:2, nuclear:0}).

Proven here: the rejection cause mint_strand exists to fix; a minted graph strand carries
a 0x58 centromere with a readable p:q orientation and censuses as 'nuclear'; kernel_to_graph
stays BYTE-EXACT across minting (the centromere is an interior cap recall/kernel_unpack
skip) on a mixed directed/signed/labeled/extras graph; the metacentric default arm-ratio
((4,5), (15,15)) + custom centromere_at/orientation; generality over kernel_pack + plain
chromosome strands; the error contract; backward-compat (an un-minted strand is unchanged);
registration (tools.total == 448); and the 1:1 C<->Python byte-parity of the spliced cap
(gated on the native peer). numpy-free; no abs().
"""
from __future__ import annotations

import pytest

from srmech.biology import genome as G
from srmech import _native
from srmech.math.hdc import klein4_expand

_DIM = 64


def _one(seed=1270):
    return klein4_expand(_DIM, seed)


def _leaves(n, base=0):
    return [klein4_expand(_DIM, base + s) for s in range(n)]


def _graph():
    """A MIXED directed graph — signed charges, a node_ids label table, extras."""
    vs = 6
    edges = [(0, 1), (1, 2), (2, 0), (3, 1), (4, 4), (0, 2), (1, 3), (2, 4)]
    weights = [5, 7, 2, 9, 1, 3, 8, 6]
    charges = [1, -1, 1, -1, 0, 1, -1, 1]
    node_ids = [100, 200, 300, 400, 500]
    extras = [42, 7]
    return vs, edges, weights, charges, node_ids, extras


def _graph_strand(one):
    vs, edges, weights, charges, node_ids, extras = _graph()
    strand, n = G.graph_to_kernel(vs, edges, weights, charges, node_ids=node_ids,
                                  extras=extras, leaf_dim=_DIM, label="wiki", coupling=one)
    return strand, n


# ── 0. the REJECTION cause mint_strand exists to fix ────────────────────────

def test_chromosome_centromere_rejects_a_packed_strand():
    """The §100 GAP 1 rejection: chromosome(packed_strand, centromere=o) treats the
    already-packed strand as raw leaves and quad_turn binds the 256-sector telomere cap."""
    one = _one()
    strand, _n = _graph_strand(one)
    with pytest.raises(ValueError, match="klein-4 elements must be in"):
        G.chromosome(strand, one, centromere=1)


# ── 1. mint a graph strand: 0x58 present, p:q readable, censuses minted ──────

def test_mint_graph_strand_carries_centromere():
    one = _one()
    strand, _n = _graph_strand(one)
    assert G.centromere_of(strand) is None                 # un-minted = a stick
    minted = G.mint_strand(strand, one)
    assert len(minted) == len(strand) + 1                  # exactly one cap spliced
    assert any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in minted)  # 0x58
    co = G.centromere_of(minted)
    assert co is not None
    assert co["orientation"] in (0, 1, 2, 3)
    p, q = co["arm_ratio"]
    assert p >= 0 and q >= 0 and p + q == sum(
        1 for hv in strand if G._cap_kind(hv) is None)     # position IS the arm-ratio


def test_mint_graph_strand_censuses_nuclear(tmp_path):
    one = _one()
    strand, _n = _graph_strand(one)
    minted = G.mint_strand(strand, one)
    d = tmp_path / "wiki.genome"
    G.genome_save(minted, d, one)
    census = G.genome_census(str(d), coupling=one)
    assert census["types"]["nuclear"] == 1 and census["types"]["plasmid"] == 0
    assert census["n_chromosomes"] == 1
    assert census["topology"] == "nuclear-like"             # a nuclear genome is a nucleus


# ── 2. kernel_to_graph BYTE-EXACT across minting (the hard requirement) ──────

def test_kernel_to_graph_byte_exact_after_minting():
    one = _one()
    vs, edges, weights, charges, node_ids, extras = _graph()
    strand, n = G.graph_to_kernel(vs, edges, weights, charges, node_ids=node_ids,
                                  extras=extras, leaf_dim=_DIM, label="wiki", coupling=one)
    base = G.kernel_to_graph(strand, one, n)               # the un-minted decode
    minted = G.mint_strand(strand, one)
    got = G.kernel_to_graph(minted, one, n)
    assert got == base                                     # minting is transparent
    assert got == {"vocab_size": vs, "edges": edges, "weights": weights,
                   "charges": charges, "node_ids": node_ids, "extras": extras}


def test_kernel_to_graph_byte_exact_after_minting_via_genome(tmp_path):
    """The same byte-exactness holds after a genome_save/round-trip of the minted strand."""
    one = _one()
    vs, edges, weights, charges, node_ids, extras = _graph()
    strand, n = G.graph_to_kernel(vs, edges, weights, charges, node_ids=node_ids,
                                  extras=extras, leaf_dim=_DIM, label="wiki", coupling=one)
    base = G.kernel_to_graph(strand, one, n)
    minted = G.mint_strand(strand, one)
    d = tmp_path / "wiki.genome"
    G.genome_save(minted, d, one)
    assert G.kernel_to_graph(str(d), one, n) == base       # from the saved genome path


# ── 3. arm-ratio: metacentric default + custom split/orientation ────────────

def test_metacentric_default_arm_ratio_9_and_30_turns():
    """A plain chromosome (no header) of 9 leaves mints (4,5); 30 leaves mints (15,15)
    — the chromosome() mint default (n_turns // 2)."""
    one = _one()
    c9 = G.chromosome(_leaves(9), one, label="a")
    assert G.centromere_of(G.mint_strand(c9, one))["arm_ratio"] == (4, 5)
    c30 = G.chromosome(_leaves(30), one, label="b")
    assert G.centromere_of(G.mint_strand(c30, one))["arm_ratio"] == (15, 15)


def test_custom_centromere_at_and_orientation():
    one = _one()
    strand, n = _graph_strand(one)
    n_turns = sum(1 for hv in strand if G._cap_kind(hv) is None)
    minted = G.mint_strand(strand, one, centromere_at=1, orientation=2)
    co = G.centromere_of(minted)
    assert co["orientation"] == 2
    assert co["arm_ratio"] == (1, n_turns - 1)
    assert G.kernel_to_graph(minted, one, n) == G.kernel_to_graph(strand, one, n)


def test_default_orientation_is_the_mint_rule():
    """The default orientation is sha256(recovered leaves)[0] & 3 — the SAME
    Class-A->Class-C rule mint() assigns (_mint_orientation)."""
    one = _one()
    strand, _n = _graph_strand(one)
    minted = G.mint_strand(strand, one)
    expected = G._mint_orientation(G.recall(strand, one))
    assert G.centromere_of(minted)["orientation"] == expected


def test_acrocentric_and_telocentric_extremes():
    one = _one()
    strand, n = _graph_strand(one)
    n_turns = sum(1 for hv in strand if G._cap_kind(hv) is None)
    acro = G.mint_strand(strand, one, centromere_at=0)      # p = 0 (all long arm)
    telo = G.mint_strand(strand, one, centromere_at=n_turns)  # q = 0 (all short arm)
    assert G.centromere_of(acro)["arm_ratio"] == (0, n_turns)
    assert G.centromere_of(telo)["arm_ratio"] == (n_turns, 0)
    assert G.kernel_to_graph(acro, one, n) == G.kernel_to_graph(strand, one, n)
    assert G.kernel_to_graph(telo, one, n) == G.kernel_to_graph(strand, one, n)


# ── 4. generality: kernel_pack + plain chromosome strands ───────────────────

def test_mint_a_kernel_pack_strand():
    one = _one()
    strand = G.kernel_pack([1, 2, 3, 0, 3, 2, 1, 0] * 20, leaf_dim=_DIM, coupling=one)
    minted = G.mint_strand(strand, one)
    assert G.centromere_of(minted) is not None
    assert G.kernel_unpack(minted, one) == G.kernel_unpack(strand, one)  # payload intact


def test_mint_a_plain_chromosome_strand():
    one = _one()
    leaves = _leaves(12)
    chrom = G.chromosome(leaves, one, label="astro")
    minted = G.mint_strand(chrom, one)
    assert G.centromere_of(minted) is not None
    assert G.recall(minted, one) == G.recall(chrom, one)   # leaves recovered identically


def test_mint_strand_agrees_with_chromosome_centromere_on_a_plain_chromosome():
    """For a PLAIN chromosome (no header) the recovered leaves ARE the raw leaves, so
    mint_strand's default orientation == chromosome(centromere=that orientation)."""
    one = _one()
    leaves = _leaves(9)
    chrom = G.chromosome(leaves, one, label="a")
    o = G._mint_orientation(leaves)
    minted = G.mint_strand(chrom, one)                     # default orientation + split
    direct = G.chromosome(leaves, one, label="a", centromere=o)  # build-time mint
    assert [hv.tobytes() for hv in minted] == [hv.tobytes() for hv in direct]


# ── 5. the error contract ───────────────────────────────────────────────────

def test_empty_strand_raises():
    with pytest.raises(ValueError, match="strand is empty"):
        G.mint_strand([], _one())


def test_raw_leaves_raise_not_a_packed_strand():
    one = _one()
    with pytest.raises(ValueError, match="must OPEN with a chromosome-boundary cap"):
        G.mint_strand(_leaves(3), one)                     # raw leaves, no opening cap


def test_double_mint_raises():
    one = _one()
    strand, _n = _graph_strand(one)
    minted = G.mint_strand(strand, one)
    with pytest.raises(ValueError, match="already carries an interior centromere"):
        G.mint_strand(minted, one)


def test_out_of_range_centromere_at_raises():
    one = _one()
    strand, _n = _graph_strand(one)
    with pytest.raises(ValueError, match="out of range"):
        G.mint_strand(strand, one, centromere_at=9999)
    with pytest.raises(ValueError, match="out of range"):
        G.mint_strand(strand, one, centromere_at=-1)


# ── 6. backward-compat: an un-minted strand is byte-for-byte unchanged ───────

def test_unminted_strand_is_never_mutated():
    one = _one()
    strand, n = _graph_strand(one)
    before = [hv.tobytes() for hv in strand]
    _minted = G.mint_strand(strand, one)                   # a READ of the input
    assert [hv.tobytes() for hv in strand] == before       # input un-mutated
    assert G.kernel_to_graph(strand, one, n) == G.kernel_to_graph(strand, one, n)


# ── 7. registration ─────────────────────────────────────────────────────────

def test_mint_strand_registered_and_total_matches_live():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    names = [t.name for t in get_tool_schema().tools]
    assert "srmech.biology.genome.mint_strand" in names
    assert len(names) == 556
    assert "mint_strand" in G.__all__


def test_mint_strand_tool_has_docs():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    entry = next(t for t in get_tool_schema().tools
                 if t.name == "srmech.biology.genome.mint_strand")
    assert entry.explanation and entry.explanation.strip()
    assert entry.example
    # rc340 (#T965): 6 -> 7 — the shared ET_PARAM (element_type) is now published on
    # the MCP surface for every genome op whose Python surface accepts it, so a
    # remote caller can pick the carrier rung instead of silently getting klein4.
    assert len(entry.parameters) == 7
    assert any(p.name == "element_type" for p in entry.parameters)


# ── 8. 1:1 C<->Python byte-parity of the spliced cap (native-gated) ─────────

_native_mint = pytest.mark.skipif(
    not _native.has_native_genome_mint(),
    reason="native srmech_genome_mint peer absent — pure path is the complete alternative")


@_native_mint
def test_parity_mint_strand_cap_native_vs_pure(monkeypatch):
    """mint_strand composes over the native-dispatched centromere() cap-writer + a PURE
    splice, so the minted strand is byte-identical whether the cap came from C or Python."""
    one = _one()
    strand, _n = _graph_strand(one)
    native = b"".join(hv.tobytes() for hv in G.mint_strand(strand, one))   # native cap
    monkeypatch.setattr(_native, "genome_centromere_c",
                        lambda *a, **k: None)              # force the pure cap-writer
    pure = b"".join(hv.tobytes() for hv in G.mint_strand(strand, one))
    assert native == pure


@_native_mint
def test_parity_minted_graph_persistence(tmp_path, monkeypatch):
    """The minted graph strand persists byte-identically native vs pure (genome_save)."""
    one = _one()
    strand, _n = _graph_strand(one)
    minted = G.mint_strand(strand, one)

    def save(native):
        d = tmp_path / ("nat" if native else "pure")
        d.mkdir()
        monkeypatch.setattr(_native, "has_native_genome", lambda: native)
        G.genome_save(minted, d, coupling=one)
        return (d / "turns.bin").read_bytes(), (d / "manifest.json").read_bytes()

    cb, cm = save(True)
    pb, pm = save(False)
    assert cb == pb and cm == pm
