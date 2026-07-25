"""§100 GAP 2 / G2 (rc327, task #905) — BYTE-PARITY between the two coherency
projections of ``genome.genome_from_graph`` (the GAP-2 builder).

ADR-0009: the capability is the invariant; neither implementation is primary. So
the test is NOT "does C agree with Python" — it is "do the two projections emit the
SAME multi-chromosome genome". The native whole-op peer ``srmech_genome_from_graph``
composes ``srmech_genome_graph_partition`` (the groups) -> per group an in-RAM
induced-subgraph relabel -> ``srmech_graph_kernel_encode`` -> the HV kernel BLOCK
build -> ``srmech_genome_mint_strand`` (nuclear only) -> strand assembly, all in C;
the pure body is the byte-parity ORACLE (forced here by disabling the whole native
surface, so graph_to_kernel + mint_strand + partition ALL run in pure Python).

The cases span the two regimes the builder must get right — a graph that stays WHOLE
(one community, one DNA type) and a graph that PARTITIONS into >= 2 groups with a MIX
of minted nuclear + kept plasmid chromosomes — across shape x size x degeneracy
(weighted + signed-charge edges, disconnected components, self-loops, isolated nodes,
single node, empty), plus the ``path=`` save + census round-trip.
"""
import pytest

from srmech.amsc import _native
from srmech.amsc import genome


pytestmark = pytest.mark.skipif(
    not _native.has_native_genome_from_graph(),
    reason="rc327 native genome_from_graph not built into this lib",
)


def _strand_bytes(strand):
    """The strand's flat fixed-width leaf-block form (the byte-parity surface)."""
    return b"".join(genome._leaf_blocks(strand))


def _partition_no_wd(part):
    """The partition dict minus the nondeterministic scratch ``work_dir``."""
    return {k: v for k, v in part.items() if k != "work_dir"}


def _build(n, edges, weights, charges, coupling, ld, max_tome, n_bins,
           centromere_at, path):
    return genome.genome_from_graph(
        n, edges, weights=weights, charges=charges, coupling=coupling,
        leaf_dim=ld, max_tome=max_tome, n_bins=n_bins,
        centromere_at=centromere_at, path=path)


def _assert_parity(monkeypatch, tmp_path, tag, n, edges, weights=None,
                   charges=None, ld=52, max_tome=256, n_bins=16,
                   centromere_at=None, save=False):
    coupling = genome._default_coupling(ld)
    npath = str(tmp_path / (tag + "_n.genome")) if save else None
    ppath = str(tmp_path / (tag + "_p.genome")) if save else None
    # native leg — the whole builder runs in C
    assert _native.has_native_genome_from_graph()
    out_n = _build(n, edges, weights, charges, coupling, ld, max_tome, n_bins,
                   centromere_at, npath)
    # pure leg — disable the WHOLE native surface so graph_to_kernel + mint_strand
    # + partition all take their pure bodies (the true parity oracle).
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        out_p = _build(n, edges, weights, charges, coupling, ld, max_tome, n_bins,
                       centromere_at, ppath)

    assert _strand_bytes(out_n["strand"]) == _strand_bytes(out_p["strand"]), \
        f"{tag}: strand bytes diverge"
    assert out_n["chromosomes"] == out_p["chromosomes"], f"{tag}: chromosomes diverge"
    assert out_n["counts"] == out_p["counts"], f"{tag}: counts diverge"
    assert out_n["status"] == out_p["status"], f"{tag}: status diverge"
    assert _partition_no_wd(out_n["partition"]) == \
        _partition_no_wd(out_p["partition"]), f"{tag}: partition diverges"
    if save:
        # the census carries the genome DIR path (npath vs ppath) — compare the rest.
        cn = {k: v for k, v in out_n["census"].items() if k != "path"}
        cp = {k: v for k, v in out_p["census"].items() if k != "path"}
        assert cn == cp, f"{tag}: census diverges"
    return out_n


# ---------------------------------------------------------------------------
# graph builders
# ---------------------------------------------------------------------------

def _ring(n):
    return n, [(i, (i + 1) % n) for i in range(n)]


def _two_triangles_bridge():
    return 6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (2, 3)]


def _cliques_chain(n_cliques, clique):
    edges = []
    for c in range(n_cliques):
        base = c * clique
        for i in range(clique):
            for j in range(i + 1, clique):
                edges.append((base + i, base + j))
    for c in range(n_cliques - 1):
        edges.append((c * clique + clique - 1, (c + 1) * clique))   # weak bridge
    return n_cliques * clique, edges


# ---------------------------------------------------------------------------
# 1) the WHOLE regime (one community, one DNA type -> a single chromosome)
# ---------------------------------------------------------------------------

def test_whole_ring_stays_one_chromosome(monkeypatch, tmp_path):
    n, e = _ring(5)
    out = _assert_parity(monkeypatch, tmp_path, "ring5", n, e)
    assert len(out["chromosomes"]) == 1


def test_whole_two_triangles_default_max_tome(monkeypatch, tmp_path):
    n, e = _two_triangles_bridge()
    out = _assert_parity(monkeypatch, tmp_path, "2tri_whole", n, e)
    assert len(out["chromosomes"]) == 1


# ---------------------------------------------------------------------------
# 2) the PARTITIONED regime (>= 2 groups; a MIX of nuclear + plasmid)
# ---------------------------------------------------------------------------

def test_partitions_into_multiple_groups(monkeypatch, tmp_path):
    n, e = _two_triangles_bridge()
    out = _assert_parity(monkeypatch, tmp_path, "2tri_split", n, e, max_tome=3)
    assert len(out["chromosomes"]) >= 2


def test_cliques_chain_mixed_nuclear_plasmid(monkeypatch, tmp_path):
    n, e = _cliques_chain(4, 3)
    out = _assert_parity(monkeypatch, tmp_path, "chain", n, e, max_tome=3, n_bins=8)
    types = {c["type"] for c in out["chromosomes"]}
    assert "nuclear" in types and "plasmid" in types


def test_weighted_and_signed_charges(monkeypatch, tmp_path):
    n, e = _cliques_chain(4, 3)
    w = [2] * len(e)
    ch = [(-1) ** i * (i % 3) for i in range(len(e))]
    _assert_parity(monkeypatch, tmp_path, "wc", n, e, weights=w, charges=ch,
                   max_tome=3, n_bins=8)


def test_disconnected_components(monkeypatch, tmp_path):
    e = [(0, 1), (1, 2), (2, 0), (10, 11), (11, 12), (12, 10)]
    _assert_parity(monkeypatch, tmp_path, "disc", 13, e, max_tome=3)


def test_self_loops_and_isolated_nodes(monkeypatch, tmp_path):
    e = [(0, 0), (0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (2, 3)]
    _assert_parity(monkeypatch, tmp_path, "selfiso", 7, e, max_tome=3)


# ---------------------------------------------------------------------------
# 3) degenerate sizes + a wider leaf_dim + explicit centromere_at
# ---------------------------------------------------------------------------

def test_single_node(monkeypatch, tmp_path):
    _assert_parity(monkeypatch, tmp_path, "single", 1, [])


def test_empty_graph(monkeypatch, tmp_path):
    _assert_parity(monkeypatch, tmp_path, "empty", 0, [])


def test_wider_leaf_dim(monkeypatch, tmp_path):
    n, e = _cliques_chain(3, 4)
    _assert_parity(monkeypatch, tmp_path, "ld64", n, e, ld=64, max_tome=4, n_bins=8)


def test_explicit_centromere_at(monkeypatch, tmp_path):
    n, e = _cliques_chain(4, 3)
    _assert_parity(monkeypatch, tmp_path, "cen0", n, e, max_tome=3, n_bins=8,
                   centromere_at=0)


# ---------------------------------------------------------------------------
# 4) the path= save + census round-trip parity
# ---------------------------------------------------------------------------

def test_save_and_census_parity(monkeypatch, tmp_path):
    n, e = _cliques_chain(4, 3)
    out = _assert_parity(monkeypatch, tmp_path, "saved", n, e, max_tome=3,
                         n_bins=8, save=True)
    # the saved genome carries BOTH minted-nuclear + kept-plasmid chromosomes on disk
    on_disk = {c["type"] for c in out["census"]["chromosomes"]}
    assert {"nuclear", "plasmid"} <= on_disk


# ---------------------------------------------------------------------------
# 5) the C grouping matches srmech_genome_graph_partition (reuses G3)
# ---------------------------------------------------------------------------

def test_grouping_matches_g3_partition(tmp_path):
    n, e = _cliques_chain(4, 3)
    coupling = genome._default_coupling(52)
    out = genome.genome_from_graph(n, e, coupling=coupling, leaf_dim=52,
                                   max_tome=3, n_bins=8)
    part = genome.genome_partition(n, e, max_tome=3, n_bins=8)
    assert len(out["chromosomes"]) == len(part["groups"])
    for gi, (chrom, g) in enumerate(zip(out["chromosomes"], part["groups"])):
        assert chrom["type"] == g["type"]
        assert chrom["community"] == g["community"]
        assert chrom["nodes"] == g["nodes"]
        assert chrom["label"] == f"{g['type']}_c{g['community']}_{gi}"


# ---------------------------------------------------------------------------
# 6) backward-compat: the C peer + the down-only rosetta ratchet
# ---------------------------------------------------------------------------

def test_symbol_declared_and_bound():
    assert _native.has_native_genome_from_graph()


def test_rosetta_ratchet_closed_g2():
    import importlib.util
    import pathlib
    p = pathlib.Path(__file__).with_name("test_rosetta_transitive_standalone.py")
    spec = importlib.util.spec_from_file_location("_rosetta_ratchet_probe", p)
    R = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(R)
    # The global CEIL_WIRE_GLUE_GAPS count is pinned authoritatively in the
    # ratchet module (and the per-rc test); this per-op G2 test asserts only
    # that genome_from_graph is CLOSED, so it stays green as later rcs (rc329+)
    # lower the ceiling further. (rc329: dropped the stale `== 8` global pin.)
    assert R._WHOLE_OP_C_PEER["srmech.amsc.genome.genome_from_graph"] == \
        "srmech_genome_from_graph"
    assert "srmech.amsc.genome.genome_from_graph" not in R._KNOWN_GLUE_GAPS
