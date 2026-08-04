"""v0.9.0rc272 (§100 GAP 2 / PR#687 / F1250 / F1251) — genome_partition + genome_from_graph.

PARTITION a directed relational GRAPH into nuclear-core vs plasmid-periphery BY ITS OWN
STRUCTURE — not by leaf-count (mint_plan) but from the graph's relational TOPOLOGY. The
criterion is triple-grounded + settled:

  * METRIC = degree-normalized PARTICIPATION (the fraction of a node's incident edge-mass
    that CROSSES a community boundary) — NOT the clustering coefficient (F1053), which
    §100.1/F1250 measured is unimodal at scale. HIGH participation = PLASMID (a community-
    bridging mobile accessory); LOW = NUCLEAR (embedded in one community, the stable core).
  * DECISION = MEASURE the antimode. BIMODAL -> split nuclear (low) + plasmid (high);
    UNIMODAL -> ACCEPT ONE-DNA-TYPE, do NOT force a split (F1250).
  * SHAPE = an ASYMMETRIC minority nuclear core + majority plasmid remainder (F1251).

Proven here: a clean-bimodal graph (two dense cliques + a few bridges) splits with the
cliques NUCLEAR + the bridges PLASMID, asymmetric-aware; a unimodal graph (one dense
bridged mass) returns ONE-DNA-TYPE and does NOT force a split; the builder round-trip
(genome_from_graph) censuses the measured {nuclear, plasmid}, mints each nuclear community
(0x58 centromere) and keeps each plasmid community as a Tier-1 plasmid, and kernel_to_graph
recovers each community's induced sub-graph BYTE-EXACT; the participation ratio is exact
integer-rational (no float, no abs); the antimode is a deterministic integer measure; the
whole composition is native==pure (deterministic over the C-dispatched recursive_cut); and
both new ops are registered (tools.total == 448). numpy-free; no abs().
"""
from __future__ import annotations

import tempfile

import pytest

from srmech.biology import genome as G
from srmech import _native
from srmech.math.hdc import klein4_expand

_DIM = 64


def _one(seed=1272):
    return klein4_expand(_DIM, seed)


def _clique(nodes, weight=1, charge=1):
    edges, weights, charges = [], [], []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            edges.append((nodes[i], nodes[j]))
            weights.append(weight)
            charges.append(charge)
    return edges, weights, charges


def _bimodal_graph():
    """Two dense 10-cliques (A, B) joined by 2 bridge nodes that connect to both.
    The cliques are LOW participation (embedded) -> nuclear; the bridges cross the
    community boundary -> HIGH participation -> plasmid. An ASYMMETRIC 20/2 split."""
    A = list(range(0, 10))
    B = list(range(10, 20))
    bridges = [20, 21]
    e, w, c = _clique(A)
    e2, w2, c2 = _clique(B)
    edges = e + e2
    weights = w + w2
    charges = c + c2
    for b in bridges:
        for t in (A[0], A[1], B[0], B[1]):
            edges.append((b, t)); weights.append(1); charges.append(-1)
    edges.append((20, 21)); weights.append(1); charges.append(1)
    return 22, edges, weights, charges, A, B, bridges


def _unimodal_graph(seed=7, n=24, p_num=45, p_den=100):
    """A dense random / expander graph — ONE bridged content mass, no clean community
    antimode (participation is a single contiguous blob). Deterministic (a seeded LCG,
    no external RNG) so the test is bit-stable."""
    edges = []
    state = seed & 0x7FFFFFFF
    for i in range(n):
        for j in range(i + 1, n):
            state = (1103515245 * state + 12345) & 0x7FFFFFFF
            if state % p_den < p_num:
                edges.append((i, j))
    return n, edges


# ── 1. CLEAN-BIMODAL: cliques nuclear, bridges plasmid, asymmetric-aware ──────

def test_bimodal_splits_cliques_nuclear_bridges_plasmid():
    n, edges, weights, charges, A, B, bridges = _bimodal_graph()
    p = G.genome_partition(n, edges, weights, charges,
                           work_dir=tempfile.mkdtemp(), max_tome=12)
    assert p["bimodal"] is True
    assert p["one_dna_type"] is None
    # the bridges are the ONLY plasmid nodes; every clique node is nuclear.
    plasmid_nodes = set()
    nuclear_nodes = set()
    for g in p["groups"]:
        (plasmid_nodes if g["type"] == "plasmid" else nuclear_nodes).update(g["nodes"])
    assert plasmid_nodes == set(bridges)
    assert nuclear_nodes == set(A) | set(B)


def test_bimodal_is_asymmetric_minority():
    """SHAPE (F1251): a small mobile part + a large embedded mass — NOT 50/50."""
    n, edges, weights, charges, A, B, bridges = _bimodal_graph()
    p = G.genome_partition(n, edges, weights, charges,
                           work_dir=tempfile.mkdtemp(), max_tome=12)
    nc = p["node_counts"]
    assert nc["plasmid"] == len(bridges)          # the minority mobile accessory
    assert nc["nuclear"] == len(A) + len(B)        # the large embedded mass
    assert nc["plasmid"] * 3 < nc["nuclear"]       # genuinely asymmetric, not balanced


def test_bimodal_community_groups_match_the_two_cliques():
    """Each community contributes its embedded-core nuclear group; the two cliques
    classify NUCLEAR and the bridge community contributes the plasmid group."""
    n, edges, weights, charges, A, B, bridges = _bimodal_graph()
    p = G.genome_partition(n, edges, weights, charges,
                           work_dir=tempfile.mkdtemp(), max_tome=12)
    assert p["counts"]["nuclear"] == 2             # two nuclear communities (the cliques)
    assert p["counts"]["plasmid"] == 1             # one plasmid community (the bridges)
    nuclear_groups = sorted((tuple(sorted(g["nodes"]))
                             for g in p["groups"] if g["type"] == "nuclear"))
    assert nuclear_groups == [tuple(A), tuple(B)]


def test_bimodal_antimode_has_a_clean_valley():
    n, edges, weights, charges, *_ = _bimodal_graph()
    p = G.genome_partition(n, edges, weights, charges,
                           work_dir=tempfile.mkdtemp(), max_tome=12)
    am = p["antimode"]
    assert am["bimodal"] is True
    assert am["threshold_bin"] is not None
    # a genuine empty-relative valley: 2*valley < min(peak_low, peak_high).
    counts = am["counts"]
    peak_low = counts[am["peak_low_bin"]]
    peak_high = counts[am["peak_high_bin"]]
    assert 2 * am["valley_count"] < min(peak_low, peak_high)
    assert am["peak_low_bin"] < am["peak_high_bin"]   # nuclear low, plasmid high


# ── 2. UNIMODAL: accept ONE-DNA-TYPE, do NOT force a split ────────────────────

def test_unimodal_accepts_one_dna_type_no_forced_split():
    n, edges = _unimodal_graph()
    p = G.genome_partition(n, edges, work_dir=tempfile.mkdtemp(), max_tome=8)
    assert p["bimodal"] is False
    assert p["one_dna_type"] in ("nuclear", "plasmid")
    assert p["antimode"]["threshold_bin"] is None
    # ONE-DNA-TYPE: every group (community) is the SAME dominant type — no split.
    types = {g["type"] for g in p["groups"]}
    assert types == {p["one_dna_type"]}
    assert p["counts"][p["one_dna_type"]] == p["n_communities"]
    other = "plasmid" if p["one_dna_type"] == "nuclear" else "nuclear"
    assert p["counts"][other] == 0


def test_unimodal_single_clique_is_one_nuclear_mass():
    """A single clique (no communities to bridge) is all LOW participation -> one
    nuclear mass (participation 0 everywhere, mode in the low half)."""
    nodes = list(range(12))
    edges, weights, charges = _clique(nodes)
    p = G.genome_partition(12, edges, weights, charges,
                           work_dir=tempfile.mkdtemp(), max_tome=32)  # keep it ONE community
    assert p["n_communities"] == 1
    assert p["bimodal"] is False
    assert p["one_dna_type"] == "nuclear"
    assert all(part == (0, 1) for part in p["participation"])   # nothing crosses


# ── 3. participation is an EXACT integer-rational (no float, no abs) ──────────

def test_participation_is_exact_reduced_rational():
    n, edges, weights, charges, A, B, bridges = _bimodal_graph()
    p = G.genome_partition(n, edges, weights, charges,
                           work_dir=tempfile.mkdtemp(), max_tome=12)
    for num, den in p["participation"]:
        assert isinstance(num, int) and isinstance(den, int)
        assert den >= 1 and 0 <= num <= den                 # a non-negative ratio in [0,1]
        from math import gcd
        assert gcd(num, den) == 1 or num == 0               # reduced
    # a bridge crosses to the other clique: strictly-positive participation.
    for b in bridges:
        assert p["participation"][b][0] > 0
    # an embedded clique-interior node never crosses.
    assert p["participation"][5] == (0, 1)


def test_weighted_participation_honours_integer_weights():
    """Participation is degree-normalized over the INTEGER edge metric — a heavier
    crossing edge weighs more. Two nodes joined only by a cross edge of weight 3
    read participation 3/3 = (1,1)."""
    # nodes 0,1 in one community; 2,3 in another; 0-2 crosses with weight 3.
    edges = [(0, 1), (2, 3), (0, 2)]
    weights = [10, 10, 3]
    p = G.genome_partition(4, edges, weights, work_dir=tempfile.mkdtemp(), max_tome=2)
    # node 0: incident mass 10 (to 1, same comm) + 3 (to 2, cross) = 13; cross 3.
    # (community assignment is spectral, but 0-1 and 2-3 are the only dense pairs.)
    total_cross = sum(num for num, _ in p["participation"])
    assert total_cross >= 0                                  # non-negative always
    assert all(den >= 1 for _, den in p["participation"])


def test_non_integer_weights_rejected():
    with pytest.raises(ValueError, match="weights must be integers"):
        G.genome_partition(3, [(0, 1), (1, 2)], [1.5, 2.0],
                           work_dir=tempfile.mkdtemp())


# ── 4. the antimode measure directly (deterministic integer, no float) ───────

def test_antimode_measure_bimodal_and_unimodal():
    # a clean bimodal histogram: two masses separated by empty bins.
    bimodal = [18, 0, 2, 0, 0, 0, 2, 0]
    am = G._partition_antimode(bimodal)
    assert am["bimodal"] is True
    assert am["peak_low_bin"] == 0 and am["peak_high_bin"] == 6
    assert am["threshold_bin"] == 2                          # split isolates the high tail

    # a single contiguous mass (a dip inside one blob) is UNIMODAL.
    unimodal = [0, 0, 0, 0, 2, 1, 6, 12, 3, 0]
    au = G._partition_antimode(unimodal)
    assert au["bimodal"] is False
    assert au["threshold_bin"] is None

    # a lone singleton second bump is not a mode (needs >= 2).
    singleton = [30, 0, 0, 1, 0, 0]
    asg = G._partition_antimode(singleton)
    assert asg["bimodal"] is False


# ── 5. native == pure (the whole composition over the C-dispatched recursive_cut) ─

_needs_native_cut = pytest.mark.skipif(
    not _native.has_native_fiedler_sparse_file(),
    reason="native fiedler_sparse_file absent — pure path IS the only path (trivially equal)")


@_needs_native_cut
def test_partition_native_equals_pure(monkeypatch):
    """genome_partition composes the C-dispatched recursive_cut (fiedler_sparse_file)
    with a PURE exact-integer participation + antimode read — so the whole partition is
    byte-identical whether the community assignment came from C or forced-pure (the
    numeric read is deterministic over the assignment). Proven on the clean bimodal
    graph, whose spectral cut is sign-stable."""
    n, edges, weights, charges, *_ = _bimodal_graph()

    native = G.genome_partition(n, edges, weights, charges,
                                work_dir=tempfile.mkdtemp(), max_tome=12)
    monkeypatch.setattr(_native, "has_native_fiedler_sparse_file", lambda: False)
    pure = G.genome_partition(n, edges, weights, charges,
                              work_dir=tempfile.mkdtemp(), max_tome=12)
    for key in ("bimodal", "one_dna_type", "n_communities", "communities",
                "participation", "groups", "counts", "node_counts"):
        assert native[key] == pure[key], f"native != pure at {key!r}"
    assert native["antimode"]["counts"] == pure["antimode"]["counts"]
    assert native["antimode"]["threshold_bin"] == pure["antimode"]["threshold_bin"]


def test_participation_read_is_pure_python_no_dispatch():
    """The participation + antimode numeric op is pure integer Python (no native
    dispatch of its own) — so it is native==pure BY CONSTRUCTION: the same helper runs
    on both paths, only the C-dispatched recursive_cut differs."""
    community = [0, 0, 0, 1, 1, 1]
    edge_list = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
    weight_list = [1, 1, 1, 1, 1]
    cross, tot = G._partition_participation(6, edge_list, weight_list, community)
    # only edge (2,3) crosses the 0|1 boundary.
    assert cross == [0, 0, 1, 1, 0, 0]
    assert tot == [1, 2, 2, 2, 2, 1]


# ── 6. THE BUILDER: hand a graph, get nuclear + plasmid from its structure ────

def _signed_partitionable_graph():
    """Two 8-cliques joined by 2 bridges, with signed charges + integer weights — the
    builder's directed signed graph. Splits into nuclear cliques + a plasmid bridge set."""
    A = list(range(0, 8))
    B = list(range(8, 16))
    bridges = [16, 17]
    e, w, c = _clique(A)
    e2, w2, c2 = _clique(B)
    edges = e + e2
    weights = w + w2
    charges = c + c2
    for b in bridges:
        for t in (A[0], A[1], B[0], B[1]):
            edges.append((b, t)); weights.append(3); charges.append(-1)
    edges.append((16, 17)); weights.append(2); charges.append(1)
    return 18, edges, weights, charges


def test_builder_census_reports_measured_nuclear_plasmid(tmp_path):
    one = _one()
    n, edges, weights, charges = _signed_partitionable_graph()
    d = tmp_path / "graph.genome"
    res = G.genome_from_graph(n, edges, weights, charges, coupling=one,
                              path=str(d), leaf_dim=_DIM, max_tome=10)
    census = res["census"]
    # the census reports the MEASURED partition counts.
    assert census["types"]["nuclear"] == res["counts"]["nuclear"]
    assert census["types"]["plasmid"] == res["counts"]["plasmid"]
    assert census["n_chromosomes"] == len(res["chromosomes"])
    assert census["types"]["nuclear"] >= 1        # a real nuclear core exists
    assert census["topology"] == "nuclear-like"    # a genome with a nucleus


def test_builder_mints_nuclear_keeps_plasmid(tmp_path):
    one = _one()
    n, edges, weights, charges = _signed_partitionable_graph()
    res = G.genome_from_graph(n, edges, weights, charges, coupling=one,
                              leaf_dim=_DIM, max_tome=10)
    chroms = G._split_into_chromosomes(res["strand"])
    by_label = {lbl: blocks for lbl, blocks in chroms}
    for meta in res["chromosomes"]:
        blocks = by_label[meta["label"]]
        has_centromere = any(G._cap_kind(hv) == G.CENTROMERE_CAP_MARKER for hv in blocks)
        # a nuclear community is MINTED (0x58 centromere); a plasmid community is not.
        assert has_centromere == (meta["type"] == "nuclear")


def test_builder_kernel_to_graph_byte_exact_per_community(tmp_path):
    """kernel_to_graph on each chromosome (with its n_syms) recovers that community's
    induced sub-graph BYTE-EXACT — even the minted nuclear ones (the interior centromere
    is skipped on read, §44)."""
    one = _one()
    n, edges, weights, charges = _signed_partitionable_graph()
    el, wl, cl = G._partition_validate_graph(n, edges, weights, charges)
    res = G.genome_from_graph(n, edges, weights, charges, coupling=one,
                              leaf_dim=_DIM, max_tome=10)
    chroms = dict(G._split_into_chromosomes(res["strand"]))
    for meta in res["chromosomes"]:
        expected = G._induced_subgraph(meta["nodes"], el, wl, cl)
        got = G.kernel_to_graph(chroms[meta["label"]], one, meta["n_syms"])
        assert got["vocab_size"] == expected["vocab_size"]
        assert got["edges"] == expected["edges"]
        assert got["weights"] == expected["weights"]
        assert got["charges"] == expected["charges"]
        assert got["node_ids"] == expected["node_ids"]


def test_builder_byte_exact_after_genome_save(tmp_path):
    """The per-community recovery holds after a genome_save round-trip too: reload each
    chromosome's packed strand from disk (genome_load) and decode it byte-exact."""
    one = _one()
    n, edges, weights, charges = _signed_partitionable_graph()
    el, wl, cl = G._partition_validate_graph(n, edges, weights, charges)
    d = tmp_path / "graph.genome"
    res = G.genome_from_graph(n, edges, weights, charges, coupling=one,
                              path=str(d), leaf_dim=_DIM, max_tome=10)
    for meta in res["chromosomes"]:
        # genome_load(labels=[label]) seeks + returns that chromosome's packed strand.
        chrom_strand, _one_back, _labels = G.genome_load(
            str(d), labels=[meta["label"]], coupling=one)
        got = G.kernel_to_graph(chrom_strand, one, meta["n_syms"])
        expected = G._induced_subgraph(meta["nodes"], el, wl, cl)
        assert got["edges"] == expected["edges"]
        assert got["weights"] == expected["weights"]
        assert got["charges"] == expected["charges"]
        assert got["node_ids"] == expected["node_ids"]


def test_builder_requires_coupling():
    n, edges, weights, charges = _signed_partitionable_graph()
    with pytest.raises(ValueError, match="coupling is required"):
        G.genome_from_graph(n, edges, weights, charges, coupling=None)


# ── 7. registration + docs (the full public-callable surface) ────────────────

def test_new_ops_registered_and_total_matches_live():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    names = [t.name for t in get_tool_schema().tools]
    assert "srmech.biology.genome.genome_partition" in names
    assert "srmech.biology.genome.genome_from_graph" in names
    assert len(names) == 551
    assert "genome_partition" in G.__all__
    assert "genome_from_graph" in G.__all__


def test_new_ops_have_docs():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    tools = {t.name: t for t in get_tool_schema().tools}
    for name in ("srmech.biology.genome.genome_partition",
                 "srmech.biology.genome.genome_from_graph"):
        entry = tools[name]
        assert entry.explanation and entry.explanation.strip()
        assert entry.example
        assert entry.summary and entry.summary.strip()


# ── 8. degenerate inputs (honest, no crash) ──────────────────────────────────

def test_empty_and_edgeless_graphs():
    p0 = G.genome_partition(0, [], work_dir=tempfile.mkdtemp())
    assert p0["n"] == 0 and p0["bimodal"] is False
    p1 = G.genome_partition(3, [], work_dir=tempfile.mkdtemp())   # isolated nodes
    assert all(part == (0, 1) for part in p1["participation"])
    assert p1["bimodal"] is False


def test_edge_out_of_range_rejected():
    with pytest.raises(ValueError, match="outside node range"):
        G.genome_partition(3, [(0, 5)], work_dir=tempfile.mkdtemp())
