"""rc249 (gh #1390 item 2) — genome.graph_to_kernel / kernel_to_graph.

A domain-free codec: a sparse SIGNED integer graph (vocab_size + edges + int
weights[metric] + signed charges[direction] + optional node_ids label table +
extras metadata) <-> a self-describing Klein-4 symbol stream for kernel_pack,
inverted BYTE-EXACT. Faithful port of R-RBS-LM-GRAPH2KERNEL. Each int is base-4
digits behind a 2-symbol length header (<=15 digits = 30 bits; Class-K zig-zag
charge). The pure codec is the parity oracle; the C peers
(srmech_graph_kernel_encode / _decode) are byte-identical when loaded.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import hdc

NATIVE = _native.has_native_graph_kernel_codec()
LEAF = 64
COUPLE = hdc.klein4_expand(LEAF, 1080)


def test_directed_round_trip_with_node_ids_and_extras():
    vs = 5
    edges = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4)]
    weights = [3, 2, 5, 1, 7]
    charges = [1, -2, 0, 4, -1]
    node_ids = [10, 20, 30, 40, 50]
    extras = [2, 99]
    strand, n_syms = G.graph_to_kernel(vs, edges, weights, charges,
                                       node_ids=node_ids, extras=extras,
                                       leaf_dim=LEAF, label="g", coupling=COUPLE)
    g = G.kernel_to_graph(strand, COUPLE, n_syms)
    assert g == {"vocab_size": vs, "edges": edges, "weights": weights,
                 "charges": charges, "node_ids": node_ids, "extras": extras}


def test_self_describing_undirected_unlabeled_metadata_free():
    strand, n_syms = G.graph_to_kernel(3, [(0, 1), (1, 2)], [4, 4],
                                       leaf_dim=LEAF, label="u", coupling=COUPLE)
    g = G.kernel_to_graph(strand, COUPLE, n_syms)
    assert g["charges"] == [0, 0]          # charges=None -> all zero
    assert g["node_ids"] == [] and g["extras"] == []


def test_empty_graph_round_trips():
    strand, n_syms = G.graph_to_kernel(2, [], [], leaf_dim=LEAF, label="e",
                                       coupling=COUPLE)
    g = G.kernel_to_graph(strand, COUPLE, n_syms)
    assert g["edges"] == [] and g["weights"] == [] and g["vocab_size"] == 2


def test_self_loop_and_negative_charge():
    strand, n_syms = G.graph_to_kernel(7, [(0, 6), (6, 0), (3, 3)], [100, 1, 255],
                                       [-100, 50, 0], extras=[5],
                                       leaf_dim=LEAF, label="s", coupling=COUPLE)
    g = G.kernel_to_graph(strand, COUPLE, n_syms)
    assert g["edges"] == [(0, 6), (6, 0), (3, 3)]
    assert g["charges"] == [-100, 50, 0] and g["extras"] == [5]


def test_genome_persist_round_trip(tmp_path):
    vs, edges, weights, charges = 4, [(0, 1), (1, 2), (2, 3)], [2, 3, 4], [1, -1, 2]
    strand, n_syms = G.graph_to_kernel(vs, edges, weights, charges,
                                       leaf_dim=LEAF, label="p", coupling=COUPLE)
    d = tmp_path / "p.genome"
    G.genome_save(strand, str(d), COUPLE, labels=["p"])
    chroms, _c, _l = G.genome_load(str(d), labels=["p"], coupling=COUPLE)
    g = G.kernel_to_graph(chroms, COUPLE, n_syms)
    assert g["edges"] == edges and g["weights"] == weights and g["charges"] == charges


def test_30_bit_cap_raises():
    with pytest.raises(ValueError):
        G.graph_to_kernel(1 << 30, [], [], leaf_dim=LEAF, label="x", coupling=COUPLE)


def test_edges_weights_mismatch_raises():
    with pytest.raises(ValueError):
        G.graph_to_kernel(2, [(0, 1)], [1, 2], leaf_dim=LEAF, label="x", coupling=COUPLE)


def test_registered_in_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.genome.graph_to_kernel" in names
    assert "srmech.amsc.genome.kernel_to_graph" in names


# ── native parity ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not NATIVE, reason="rc249 graph-kernel C peer not loaded")
def test_native_symbols_bound():
    assert hasattr(_native.LIB, "srmech_graph_kernel_encode")
    assert hasattr(_native.LIB, "srmech_graph_kernel_decode")
    assert _native.NATIVE_ABI_VERSION == 9


@pytest.mark.skipif(not NATIVE, reason="rc249 graph-kernel C peer not loaded")
def test_native_equals_pure_codec():
    # force the pure codec by toggling the gate, compare to the native path
    cases = [
        (5, [(0, 1), (1, 2), (2, 0)], [3, 2, 5], [1, -2, 0], [10, 20, 30], [2]),
        (2, [], [], None, None, ()),
        (4, [(i % 4, (i + 1) % 4) for i in range(9)], [i + 1 for i in range(9)],
            [(-1) ** i * (i + 1) for i in range(9)], [9, 8, 7, 6], [1, 2, 3]),
    ]
    import srmech.amsc._native as N
    orig = N.has_native_graph_kernel_codec
    for vs, edges, weights, charges, node_ids, extras in cases:
        strand_n, ns_n = G.graph_to_kernel(vs, edges, weights, charges,
                                           node_ids=node_ids, extras=extras,
                                           leaf_dim=LEAF, label="g", coupling=COUPLE)
        g_n = G.kernel_to_graph(strand_n, COUPLE, ns_n)
        N.has_native_graph_kernel_codec = lambda: False          # force pure codec
        try:
            strand_p, ns_p = G.graph_to_kernel(vs, edges, weights, charges,
                                               node_ids=node_ids, extras=extras,
                                               leaf_dim=LEAF, label="g", coupling=COUPLE)
            g_p = G.kernel_to_graph(strand_p, COUPLE, ns_p)
        finally:
            N.has_native_graph_kernel_codec = orig
        assert ns_n == ns_p and g_n == g_p, vs
