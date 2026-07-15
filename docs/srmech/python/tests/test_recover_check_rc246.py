"""rc246 (gh #1390 item 4) — the Class-L genome recover-check.

``laplacian.recover_check(n, edges, weights, charges=None)`` is the packaged
round-trip integrity verify (F1225): does a recovered graph recover its op /
operand / responsion / (directed) ℂ-curvature? It composes dense_laplacian +
symmetric_eigendecompose + responsion + cycle_holonomy (composes_c). A verify,
not a raise. The F1231 octonion ORDER faculty (the order-sensitive 5th) lands
on top in rc247.
"""
from __future__ import annotations

from srmech.amsc import genome as G
from srmech.amsc import laplacian as L
from srmech.amsc import text as T


def test_symmetric_recovers():
    r = L.recover_check(4, [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)], [1] * 5)
    assert r["operand"] and r["op"] and r["responsion"]
    assert r["curvature"] is None            # symmetric store: faculty N/A
    assert r["recovered"] is True


def test_directed_with_curvature_recovers():
    # normalised charge/weight gains [2/3, -1/3, 1/3] → cycle holonomy 2/3 ≠ 0
    r = L.recover_check(3, [(0, 1), (1, 2), (2, 0)], [3, 3, 3], charges=[2, -1, 1])
    assert r["curvature"] is True
    assert r["recovered"] is True


def test_directed_zero_charge_flags_missing_curvature():
    # a directed store whose net charge is zero everywhere is symmetric-in-
    # disguise: the curvature faculty FAILS (it recovers no holonomy).
    r = L.recover_check(3, [(0, 1), (1, 2), (2, 0)], [3, 3, 3], charges=[0, 0, 0])
    assert r["curvature"] is False
    assert r["recovered"] is False


def test_empty_and_degenerate():
    assert L.recover_check(0, [], [])["recovered"] is False
    assert L.recover_check(3, [], [])["operand"] is False
    # a misaligned weights list fails the operand faculty
    assert L.recover_check(2, [(0, 1)], [1, 2])["operand"] is False


def test_full_1390_chain_end_to_end():
    """cooccurrence_edges(directed=True) → graph_to_kernel → kernel_to_graph →
    recover_check — the whole item 1 → 2 → 4 pipeline round-trips + verifies."""
    n, e, w = T.cooccurrence_edges([["a", "b", "a", "c", "b", "a"]], window=2,
                                   vocab=["a", "b", "c"], directed=True)
    charges = [1] * len(e)
    strand = G.graph_to_kernel(list(range(n)), e, w, charges)
    rv, re, rw, rc = G.kernel_to_graph(strand)
    assert (rv, re, rw, rc) == (list(range(n)), e, w, charges)   # byte-exact
    verdict = L.recover_check(len(rv), re, rw, rc)
    assert verdict["op"] and verdict["operand"] and verdict["responsion"]


def test_registered_in_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.recover_check" in names


def test_is_a_verify_not_a_raise():
    # even a self-loop-only / weird graph returns a verdict dict, never raises
    out = L.recover_check(2, [(0, 0)], [1])
    assert isinstance(out, dict) and "recovered" in out
