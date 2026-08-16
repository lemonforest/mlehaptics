"""rc250 (gh #1390 item 3) — laplacian.eulerian_path / eulerian_circuit.

A node-agnostic Hierholzer Eulerian trail / circuit over a DIRECTED edge
multiset — the walk-reconstruction the directed Class-L genome store recovers a
sequence with. Faithful port of R-RBS-LM-EULERWALK: feasibility is CHECKED
(degree balance + full-edge-consumption connectivity) — an infeasible /
disconnected graph returns None, never a partial walk. Deterministic
(adjacency consumed from the END). The pure Hierholzer is the parity oracle;
srmech_eulerian_walk is byte-identical for integer nodes.
"""
from __future__ import annotations

import pytest

from srmech import _native
from srmech.math import laplacian as L

NATIVE = _native.has_native_eulerian()


def _valid_walk(p, edges):
    if p is None or len(p) != len(edges) + 1:
        return False
    used = list(edges)
    for a in range(len(p) - 1):
        e = (p[a], p[a + 1])
        if e in used:
            used.remove(e)
        else:
            return False
    return not used


def test_triangle_circuit():
    edges = [(0, 1), (1, 2), (2, 0)]
    p = L.eulerian_path(edges)
    c = L.eulerian_circuit(edges)
    assert _valid_walk(p, edges) and c is not None and c[0] == c[-1]


def test_simple_path_is_not_a_circuit():
    edges = [(0, 1), (1, 2), (2, 3)]
    assert L.eulerian_path(edges) == [0, 1, 2, 3]
    assert L.eulerian_circuit(edges) is None       # unbalanced -> no circuit


def test_self_loop():
    edges = [(0, 0), (0, 1), (1, 0)]
    assert _valid_walk(L.eulerian_path(edges), edges)


def test_figure_eight_is_deterministic():
    edges = [(0, 1), (1, 0), (0, 2), (2, 0)]
    assert L.eulerian_path(edges) == [0, 2, 0, 1, 0]   # pop-from-end order


def test_infeasible_and_disconnected_return_none():
    assert L.eulerian_path([(0, 1), (0, 2)]) is None          # out-degree +2
    assert L.eulerian_circuit([(0, 1), (0, 2)]) is None
    assert L.eulerian_path([(0, 1), (2, 3)]) is None          # disconnected
    assert L.eulerian_circuit([(0, 1), (2, 3)]) is None


def test_empty_edges():
    assert L.eulerian_path([]) == []
    assert L.eulerian_path([], start=5) == [5]
    assert L.eulerian_circuit([]) == []


def test_start_honoured_for_circuit():
    w = L.eulerian_path([(0, 1), (1, 2), (2, 0)], start=1)
    assert w is not None and w[0] == 1 and w[-1] == 1


def test_start_ignored_for_path():
    # a path forces the +1 out-degree node regardless of start
    w = L.eulerian_path([(0, 1), (1, 2), (2, 3)], start=2)
    assert w == [0, 1, 2, 3]


def test_registered_in_tool_schema():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.math.laplacian.eulerian_path" in names
    assert "srmech.math.laplacian.eulerian_circuit" in names


def test_non_integer_nodes_pure_path():
    # string nodes stay on the pure body (native handles integer nodes only)
    edges = [("a", "b"), ("b", "c"), ("c", "a")]
    p = L.eulerian_path(edges)
    assert p is not None and len(p) == 4 and p[0] == p[-1]


# ── native parity ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not NATIVE, reason="rc250 eulerian C peer not loaded")
def test_native_symbol_bound():
    assert hasattr(_native.LIB, "srmech_eulerian_walk")
    assert _native.NATIVE_ABI_VERSION == 16


@pytest.mark.skipif(not NATIVE, reason="rc250 eulerian C peer not loaded")
def test_native_equals_pure():
    import srmech._native as N
    cases = [
        [(0, 1), (1, 2), (2, 0)],
        [(0, 1), (1, 0), (0, 2), (2, 0)],
        [(0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (3, 0)],
        [(0, 1), (0, 2)],
        [(0, 1), (2, 3)],
        [(i % 5, (i + 1) % 5) for i in range(5)],
        [(3, 1), (1, 4), (4, 3), (3, 2), (2, 3)],
    ]
    orig = N.has_native_eulerian
    for edges in cases:
        for st in (None, 0, 1, 3):
            nat_p = L.eulerian_path(edges, start=st)
            nat_c = L.eulerian_circuit(edges, start=st)
            N.has_native_eulerian = lambda: False
            try:
                pur_p = L.eulerian_path(edges, start=st)
                pur_c = L.eulerian_circuit(edges, start=st)
            finally:
                N.has_native_eulerian = orig
            assert nat_p == pur_p and nat_c == pur_c, (edges, st)
