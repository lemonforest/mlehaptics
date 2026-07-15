"""rc244 (gh #1390 item 2) — the sparse signed-graph <-> Klein-4 kernel codec.

``genome.graph_to_kernel`` / ``kernel_to_graph`` store + recover a DIRECTED
Class-L integer graph (vocab, edges, weights, signed charges) as a native genome
in ONE call — the zigzag + base-4-varint codec composed with kernel_pack /
kernel_unpack, byte-exact both ways. The pure-Python codec is the parity oracle;
the C peer (srmech_graph_kernel_encode / _decode) is byte-identical when loaded.
"""
from __future__ import annotations

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import text as T

NATIVE_CODEC = _native.has_native_graph_kernel_codec()


def _roundtrip(vocab, edges, weights, charges=None):
    strand = G.graph_to_kernel(vocab, edges, weights, charges)
    return G.kernel_to_graph(strand)


def test_round_trip_signed_graph():
    vocab = [0, 1, 2, 3]
    edges = [(0, 1), (1, 0), (1, 2), (2, 3), (3, 1)]
    weights = [5, 3, 2, 7, 4]
    charges = [2, -2, 0, 1, -1]
    rv, re, rw, rc = _roundtrip(vocab, edges, weights, charges)
    assert rv == vocab
    assert re == edges
    assert rw == weights
    assert rc == charges          # signed curvature recovered exactly


def test_charges_none_is_all_zero():
    vocab, edges, weights = [0, 1, 2], [(0, 1), (1, 2)], [3, 4]
    _, _, _, rc = _roundtrip(vocab, edges, weights)
    assert rc == [0, 0]


def test_hand_checkable_known_values():
    # a->b twice, b->a once (window=1 over "a b a b") — directed adjacency
    vocab = [0, 1]
    edges = [(0, 1), (1, 0)]
    weights = [2, 1]
    charges = [1, -1]
    rv, re, rw, rc = _roundtrip(vocab, edges, weights, charges)
    assert (rv, re, rw, rc) == (vocab, edges, weights, charges)


def test_direction_ratchet_fwd_neq_rev():
    """The reverse graph (edges flipped, charge negated) packs to a DIFFERENT
    strand — the directed store keeps the arrow the symmetric bag loses."""
    vocab = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    weights = [3, 5]
    charges = [2, -4]
    s_fwd = G.graph_to_kernel(vocab, edges, weights, charges)
    s_rev = G.graph_to_kernel(vocab, [(j, i) for (i, j) in edges], weights,
                              [-c for c in charges])
    assert s_fwd != s_rev


def test_cooccurrence_directed_roundtrip():
    n, e, w = T.cooccurrence_edges([["a", "b", "a", "b", "c", "a"]], window=2,
                                   vocab=["a", "b", "c"], directed=True)
    vv = list(range(n))
    rv, re, rw, rc = _roundtrip(vv, e, w)
    assert (rv, re, rw) == (vv, e, w)
    assert rc == [0] * len(e)


def test_overflow_guard_raises_valueerror():
    # a value >= 2**30 cannot fit the 15-base-4-digit length header — RAISE,
    # never silently corrupt. Same ValueError on the pure AND the native path.
    with pytest.raises(ValueError):
        G.graph_to_kernel([0, 1], [(0, 1)], [1 << 30], [0])
    with pytest.raises(ValueError):
        G.graph_to_kernel([0, 1 << 30], [], [], [])          # a huge vocab label


def test_validation():
    with pytest.raises(ValueError):
        G.graph_to_kernel([0, 1], [(0, 2)], [1], [0])        # edge index out of range
    with pytest.raises(ValueError):
        G.graph_to_kernel([0, 1], [(0, 1)], [-1], [0])       # negative weight
    with pytest.raises(ValueError):
        G.graph_to_kernel([0, 1], [(0, 1)], [1, 2], [0])     # weights len mismatch
    with pytest.raises(ValueError):
        G.graph_to_kernel([0, 1], [(0, 1)], [1], [0, 0])     # charges len mismatch


def test_empty_edges_round_trip():
    rv, re, rw, rc = _roundtrip([0, 1, 2], [], [])
    assert (rv, re, rw, rc) == ([0, 1, 2], [], [], [])


def test_registered_in_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.genome.graph_to_kernel" in names
    assert "srmech.amsc.genome.kernel_to_graph" in names


# ── native parity ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not NATIVE_CODEC,
                    reason="rc244 graph_kernel codec C peer not loaded")
def test_native_symbols_bound():
    assert hasattr(_native.LIB, "srmech_graph_kernel_encode")
    assert hasattr(_native.LIB, "srmech_graph_kernel_decode")
    assert _native.NATIVE_ABI_VERSION == 5      # additive symbols, ABI unchanged


@pytest.mark.skipif(not NATIVE_CODEC,
                    reason="rc244 graph_kernel codec C peer not loaded")
def test_native_equals_pure():
    cases = [
        ([0, 1, 2, 3], [(0, 1), (1, 0), (1, 2), (2, 3), (3, 1)],
         [5, 3, 2, 7, 4], [2, -2, 0, 1, -1]),
        ([7, 42, 1000], [(0, 1), (1, 2), (2, 0)], [1, 999999, 3],
         [-500000, 0, 123456]),
        ([0, 1], [], [], []),
        ([0], [(0, 0)], [9], [-9]),
    ]
    for voc, ed, w, c in cases:
        nat = _native.graph_kernel_encode_c(voc, ed, w, c)
        pur = G._graph_ints_to_syms(G._graph_to_ints(voc, ed, w, c))
        assert nat == pur, (voc, ed, w, c)
        # native decode == pure decode of the same syms
        assert _native.graph_kernel_decode_c(nat) == \
            G._ints_to_graph(G._graph_syms_to_ints(nat))
