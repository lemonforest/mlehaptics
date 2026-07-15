"""rc245 (gh #1390 item 3) — Eulerian walk reconstruction (Hierholzer).

``laplacian.eulerian_path`` / ``eulerian_circuit`` rebuild the ordered node walk
of a directed Eulerian path / circuit from a directed edge multiset — the
sandroing round-trip (F1080/F1213). The pure Hierholzer is the parity oracle;
the C peer (srmech_eulerian_walk) is byte-identical when loaded.
"""
from __future__ import annotations

import collections

import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as L

NATIVE = _native.has_native_eulerian()


def _edge_multiset(walk):
    return collections.Counter(zip(walk, walk[1:]))


def test_eulerian_path_round_trip():
    # node 0 has out−in = +1 (start), node 1 has −1 (end)
    edges = [(0, 1), (1, 2), (2, 0), (0, 1)]
    w = L.eulerian_path(edges)
    assert len(w) == len(edges) + 1
    assert w[0] == 0                                    # the out−in=+1 start
    assert _edge_multiset(w) == collections.Counter(edges)


def test_eulerian_path_hand_checkable():
    # "a b a b" as glyph ids 0,1: edges (0,1)(1,0)(0,1) — path 0→1→0→1
    w = L.eulerian_path([(0, 1), (1, 0), (0, 1)])
    assert w == [0, 1, 0, 1]


def test_eulerian_circuit_closes():
    cw = L.eulerian_circuit([(0, 1), (1, 2), (2, 0)])
    assert cw[0] == cw[-1]
    assert _edge_multiset(cw) == collections.Counter([(0, 1), (1, 2), (2, 0)])


def test_eulerian_circuit_explicit_start():
    e = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 0)]
    cw = L.eulerian_circuit(e, start=0)
    assert cw[0] == 0 and cw[-1] == 0
    assert _edge_multiset(cw) == collections.Counter(e)


def test_longer_round_trip():
    walk0 = [0, 1, 0, 2, 0, 3, 1]                        # a valid Eulerian path
    e = list(zip(walk0, walk0[1:]))
    rec = L.eulerian_path(e)
    assert _edge_multiset(rec) == collections.Counter(e)


def test_no_eulerian_path_raises():
    with pytest.raises(ValueError):
        L.eulerian_path([(0, 1), (0, 2), (0, 3)])       # node 0 out−in = +3
    with pytest.raises(ValueError):
        L.eulerian_path([(0, 1), (2, 3)])               # two +1 start nodes


def test_no_eulerian_circuit_raises():
    with pytest.raises(ValueError):
        L.eulerian_circuit([(0, 1), (1, 2)])            # unbalanced
    with pytest.raises(ValueError):
        L.eulerian_circuit([(0, 1), (1, 0), (2, 3), (3, 2)])   # disconnected
    with pytest.raises(ValueError):
        L.eulerian_circuit([(0, 1), (1, 0)], start=5)   # start has no out-edge


def test_empty_multiset():
    assert L.eulerian_path([]) == []
    assert L.eulerian_circuit([]) == []


def test_registered_in_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.eulerian_path" in names
    assert "srmech.amsc.laplacian.eulerian_circuit" in names


# ── native parity ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not NATIVE, reason="rc245 eulerian C peer not loaded")
def test_native_symbol_bound():
    assert hasattr(_native.LIB, "srmech_eulerian_walk")
    assert _native.NATIVE_ABI_VERSION == 5              # additive symbol


@pytest.mark.skipif(not NATIVE, reason="rc245 eulerian C peer not loaded")
def test_native_equals_pure():
    paths = [
        [(0, 1), (1, 2), (2, 0), (0, 1)],
        [(0, 1), (1, 2), (2, 0), (0, 2)],
        [(0, 1), (1, 0), (0, 2), (2, 0), (0, 3), (3, 1)],
    ]
    for e in paths:
        assert L.eulerian_path(e) == L._eulerian_path_pure(e), e
    circuits = [
        [(0, 1), (1, 2), (2, 0)],
        [(0, 1), (1, 2), (2, 0), (0, 3), (3, 0)],
    ]
    for e in circuits:
        assert L.eulerian_circuit(e) == L._eulerian_circuit_pure(e, None), e
