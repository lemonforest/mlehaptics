"""§100 G3 (rc321, task #904) — BYTE-PARITY between the two coherency projections
of ``genome.genome_partition`` (the GRAPH op).

ADR-0009: the capability is the invariant; neither implementation is primary. So
the test is NOT "does C agree with Python" — it is "do the two projections emit the
SAME STRUCTURE". The native whole-op peer ``srmech_genome_graph_partition`` runs
recursive_cut + the exact-integer participation + the antimode histogram DECISION +
per-node classify + group assembly all in C; the pure body is the byte-parity
oracle (forced here by monkeypatching the dispatcher to ``None``).

The cases span shape x size x degeneracy — that is where an out-of-core community
driver + the antimode tie-break actually break: a ring-of-cliques (bimodal split), a
single connected mass (unimodal, no forced split), disconnected components, edgeless,
single node, empty (n == 0), isolated nodes (tot == 0), self-loops, integer-weighted
edges, and the §101 cancel path.
"""
import pytest

from srmech.amsc import _native
from srmech.amsc import genome


pytestmark = pytest.mark.skipif(
    not _native.has_native_genome_graph_partition(),
    reason="rc321 native genome_graph_partition not built into this lib",
)


def _pure(monkeypatch):
    """Force the pure-Python body (the parity ORACLE) for one call."""
    monkeypatch.setattr(_native, "genome_graph_partition_c", lambda *a, **k: None)


def _run(tmp_path, tag, n, edges, weights=None, max_tome=4, n_bins=16, progress=None):
    wd = tmp_path / tag
    return genome.genome_partition(
        n, edges, weights, work_dir=str(wd), max_tome=max_tome, n_bins=n_bins,
        progress=progress)


# ---------------------------------------------------------------------------
# the input graphs: shape x size x degeneracy
# ---------------------------------------------------------------------------

def _ring_of_cliques(n_cliques, clique):
    """Real community structure: cliques joined in a ring by ONE weak bridge
    (integer weights: heavy INTERNAL edges, unit bridges — a clean bimodal
    participation split)."""
    edges, weights = [], []
    for c in range(n_cliques):
        base = c * clique
        for i in range(clique):
            for j in range(i + 1, clique):
                edges.append((base + i, base + j))
                weights.append(5)
    for c in range(n_cliques):
        a = c * clique + clique - 1
        b = ((c + 1) % n_cliques) * clique
        edges.append((a, b))
        weights.append(1)
    return n_cliques * clique, edges, weights


def _complete(n):
    e = [(i, j) for i in range(n) for j in range(i + 1, n)]
    return n, e, [1] * len(e)


def _disconnected(n_comp, size):
    edges, weights = [], []
    for c in range(n_comp):
        base = c * size
        for i in range(size):
            for j in range(i + 1, size):
                edges.append((base + i, base + j))
                weights.append(1)
    return n_comp * size, edges, weights


def _self_loops(n):
    """Every node carries a self-loop plus a path — self-loops are internal (never
    cross), so they stress the tot += 2w / cross unchanged accounting."""
    edges = [(i, i) for i in range(n)] + [(i, i + 1) for i in range(n - 1)]
    weights = [3] * n + [1] * (n - 1)
    return n, edges, weights


def _two_cores_with_bridges(core=5, nbridge=3):
    """Two dense cores joined by a handful of high-participation BRIDGE nodes — a
    genuinely BIMODAL participation split (embedded core nodes at bin 0, bridges high
    up, an empty valley between). At finer max_tome the cores fragment into several
    occupied bins, so this also exercises the antimode's WIDEST-gap tie-break (the
    surface where an out-of-core driver + the split decision actually break)."""
    edges, weights = [], []
    for base in (0, core):
        for i in range(core):
            for j in range(i + 1, core):
                edges.append((base + i, base + j))
                weights.append(1)
    for b in range(nbridge):
        bn = 2 * core + b
        edges.append((bn, b % core))
        weights.append(1)
        edges.append((bn, core + (b % core)))
        weights.append(1)
    return 2 * core + nbridge, edges, weights


CASES = [
    ("ring3x3", *_ring_of_cliques(3, 3)),
    ("ring4x4", *_ring_of_cliques(4, 4)),
    ("ring5x4", *_ring_of_cliques(5, 4)),
    ("complete8", *_complete(8)),            # single connected mass — unimodal
    ("complete12", *_complete(12)),
    ("disconnected3x4", *_disconnected(3, 4)),
    ("disconnected5x3", *_disconnected(5, 3)),
    ("selfloops7", *_self_loops(7)),
    ("edgeless9", 9, [], []),                # every node isolated (tot == 0)
    ("single", 1, [], []),                   # single node
    ("two_isolated", 2, [], []),
    ("pair", 2, [(0, 1)], [1]),
    ("empty", 0, [], []),                    # n == 0
    ("weighted_ring", *_ring_of_cliques(4, 5)),
    ("bimodal_5_3", *_two_cores_with_bridges(5, 3)),   # genuinely BIMODAL split
    ("bimodal_6_4", *_two_cores_with_bridges(6, 4)),
    ("bimodal_4_5", *_two_cores_with_bridges(4, 5)),
]


def _assert_partition_parity(native, pure, tag):
    assert native["status"] == pure["status"], f"{tag}: status differs"
    assert native["n"] == pure["n"], f"{tag}: n differs"
    assert native["n_communities"] == pure["n_communities"], f"{tag}: n_comm differs"
    assert native["communities"] == pure["communities"], f"{tag}: communities differ"
    assert native["bimodal"] == pure["bimodal"], f"{tag}: bimodal differs"
    assert native["one_dna_type"] == pure["one_dna_type"], f"{tag}: one_dna_type differs"
    assert native["antimode"] == pure["antimode"], f"{tag}: antimode dict differs"
    assert native["participation"] == pure["participation"], (
        f"{tag}: participation pairs differ")
    assert native["counts"] == pure["counts"], f"{tag}: per-group counts differ"
    assert native["node_counts"] == pure["node_counts"], f"{tag}: node_counts differ"
    assert native["groups"] == pure["groups"], f"{tag}: groups differ"


@pytest.mark.parametrize("tag,n,edges,weights", CASES)
@pytest.mark.parametrize("max_tome", [1, 2, 3, 4])
def test_graph_partition_is_structure_identical(
        tmp_path, monkeypatch, tag, n, edges, weights, max_tome):
    """THE acceptance test: same structure, both projections, every degenerate shape."""
    native = _run(tmp_path, f"{tag}_{max_tome}_c", n, edges, weights, max_tome=max_tome)
    with monkeypatch.context() as m:
        _pure(m)
        pure = _run(tmp_path, f"{tag}_{max_tome}_py", n, edges, weights,
                    max_tome=max_tome)
    _assert_partition_parity(native, pure, f"{tag}/mt{max_tome}")


@pytest.mark.parametrize("n_bins", [2, 4, 8, 16, 32])
@pytest.mark.parametrize("max_tome", [2, 4, 6])
def test_graph_partition_n_bins_parity(tmp_path, monkeypatch, n_bins, max_tome):
    """The antimode histogram resolution is a real degeneracy axis (a valley present
    at 16 bins can vanish at 2) — pin both projections across it on a bimodal graph
    whose cores fragment at finer max_tome (multiple candidate gaps)."""
    n, edges, weights = _two_cores_with_bridges(6, 4)
    native = _run(tmp_path, f"nb{n_bins}_{max_tome}_c", n, edges, weights,
                  max_tome=max_tome, n_bins=n_bins)
    with monkeypatch.context() as m:
        _pure(m)
        pure = _run(tmp_path, f"nb{n_bins}_{max_tome}_py", n, edges, weights,
                    max_tome=max_tome, n_bins=n_bins)
    _assert_partition_parity(native, pure, f"bimodal6x4/nb{n_bins}/mt{max_tome}")


def test_bimodal_graph_actually_splits(tmp_path):
    """Sanity: the two-cores-with-bridges graph really IS read as bimodal (a nuclear
    core + a plasmid bridge tail) — otherwise the split path is never exercised."""
    res = _run(tmp_path, "bimodal_real", *_two_cores_with_bridges(5, 3), max_tome=2)
    assert res["bimodal"] is True
    assert res["antimode"]["threshold_bin"] is not None
    assert res["node_counts"]["plasmid"] >= 1
    types = {g["type"] for g in res["groups"]}
    assert "plasmid" in types


def test_unimodal_mass_is_not_forced_to_split(tmp_path):
    """A single connected clique is one bridged mass — UNIMODAL, one_dna_type set,
    no forced split (F1250)."""
    res = _run(tmp_path, "unimodal_real", *_complete(10), max_tome=64)
    assert res["bimodal"] is False
    assert res["one_dna_type"] in ("nuclear", "plasmid")


# ---------------------------------------------------------------------------
# §101 progress / cancel
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cancel_at", [1, 2, 3])
def test_cancel_is_structure_identical(tmp_path, monkeypatch, cancel_at):
    """A cancel is a CLEAN partial: both projections emit the same coarser
    community partition + the cancelled status (participation/groups empty)."""
    n, edges, weights = _ring_of_cliques(4, 4)

    def mk():
        calls = {"k": 0}

        def tick(ev):
            calls["k"] += 1
            return 1 if calls["k"] >= cancel_at else 0
        return tick

    native = _run(tmp_path, f"cx{cancel_at}_c", n, edges, weights, max_tome=2,
                  progress=mk())
    with monkeypatch.context() as m:
        _pure(m)
        pure = _run(tmp_path, f"cx{cancel_at}_py", n, edges, weights, max_tome=2,
                    progress=mk())
    assert native["status"] == pure["status"] == genome.GENOME_STATUS_CANCELLED
    assert native["communities"] == pure["communities"], "cancelled communities differ"
    assert native["participation"] == pure["participation"] == []
    assert native["groups"] == pure["groups"] == []
    assert native["antimode"] == pure["antimode"] is None
    # every node still lands in exactly one community (a clean coarser partition)
    seen = [x for tome in native["communities"] for x in tome]
    assert sorted(seen) == list(range(n)), "cancelled partition lost nodes"


def test_cancelled_partition_is_a_clean_partition(tmp_path):
    n, edges, weights = _ring_of_cliques(5, 4)

    def tick(ev):
        return 1                              # cancel on the very first tick

    res = _run(tmp_path, "cancel_first", n, edges, weights, max_tome=2, progress=tick)
    assert res["status"] == genome.GENOME_STATUS_CANCELLED
    seen = [x for tome in res["communities"] for x in tome]
    assert sorted(seen) == list(range(n))


def test_progress_exception_propagates(tmp_path):
    n, edges, weights = _ring_of_cliques(3, 3)

    def boom(ev):
        raise RuntimeError("tick blew up")

    with pytest.raises(RuntimeError, match="tick blew up"):
        _run(tmp_path, "boom", n, edges, weights, max_tome=2, progress=boom)


def test_participation_ratios_are_reduced_and_bounded(tmp_path):
    """Every participation pair is an exact reduced rational in [0, 1]."""
    res = _run(tmp_path, "reduced", *_ring_of_cliques(4, 4), max_tome=2)
    from srmech.amsc.cyclic import gcd as _gcd
    for num, den in res["participation"]:
        assert den >= 1
        assert 0 <= num <= den
        assert _gcd(num, den) in (den, 1) or (num == 0 and den == 1) or _gcd(num, den) == 1
