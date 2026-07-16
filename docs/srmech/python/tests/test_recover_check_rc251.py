"""rc251 (gh #1390 item 4) — laplacian.recover_check (+ the F1227 split).

The packaged round-trip integrity check of a stored directed Class-L graph:
the four faculties op / operand / responsion / curvature (faithful port of
R-RBS-LM-RECOVERCHECK). ok == op and operand and responsion — curvature is
reported honestly, NOT a hard gate. Plus the F1227 corpus-scale split:
recover_check_structural (sparse, O(edges), R-RBS-LM-SIONA231) +
recover_check_spectral (op / responsion on a bounded principal submatrix). All
are composition_of_c — pure compositions of shipped C-routed ops.
"""
from __future__ import annotations

from srmech.amsc import laplacian as L


def test_directed_cyclic_passes_and_carries_curvature():
    # a lone non-cancelling charge around a cycle -> nonzero holonomy (PASS)
    v = L.recover_check(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [1, 0, 0])
    assert v["ok"] and v["op"] and v["operand"] and v["responsion"]
    assert v["curvature"]["holonomy_nonzero"]
    assert "curvature (nonzero holonomy)" in v["curvature"]["verdict"]


def test_return_shape():
    v = L.recover_check(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [1, 0, 0])
    assert set(v) == {"ok", "op", "operand", "responsion", "curvature", "diagnostics"}
    assert set(v["curvature"]) == {"directed", "n_cycles", "holonomy_nonzero", "verdict"}


def test_symmetric_bag_passes_but_flagged_flat():
    v = L.recover_check(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [0, 0, 0])
    assert v["ok"] and not v["curvature"]["directed"]
    assert "symmetric-bag" in v["curvature"]["verdict"]


def test_curvature_is_not_a_gate():
    # ok excludes curvature: a symmetric (curvature-flat) graph still passes ok
    v = L.recover_check(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [0, 0, 0])
    assert v["ok"] == (v["op"] and v["operand"] and v["responsion"])


def test_amputated_operand_fails_honestly():
    v = L.recover_check(3, [(0, 1), (1, 2)], [], None)
    assert (not v["ok"]) and (not v["operand"])


def test_undirected_none_charges_is_flat():
    v = L.recover_check(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], None)
    assert v["ok"] and not v["curvature"]["directed"]


def test_structural_sparse():
    s = L.recover_check_structural(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [1, 0, 0])
    assert set(s) == {"operand", "directed", "curvature_sampled_nonzero", "ok_structural"}
    assert s["ok_structural"] and s["operand"] and s["directed"]
    assert s["curvature_sampled_nonzero"]


def test_structural_amputated_fails():
    s = L.recover_check_structural(3, [(0, 1)], [], None)
    assert not s["ok_structural"] and not s["operand"]


def test_spectral_bounded_submatrix():
    sp = L.recover_check_spectral(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [1, 0, 0])
    assert set(sp) == {"op", "responsion", "dim", "diagnostics"}
    assert sp["op"] and sp["responsion"] and sp["dim"] == 3


def test_spectral_bounds_large_vocab():
    # a corpus vocab n=1000 is bounded to max_dim=256; out-of-block edges dropped
    sp = L.recover_check_spectral(
        1000, [(0, 1), (1, 2), (0, 2), (500, 600)], [2, 2, 2, 1], [1, 0, 0, 0],
        max_dim=256)
    assert sp["dim"] == 256
    assert sp["diagnostics"]["n_edges_in_block"] == 3   # the (500,600) edge dropped
    assert sp["op"]


def test_registered_in_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.recover_check" in names
    assert "srmech.amsc.laplacian.recover_check_structural" in names
    assert "srmech.amsc.laplacian.recover_check_spectral" in names


def test_no_abs_class_k_magnitude():
    # a negative-charge directed store phase-scales via Class-K magnitude (no abs)
    v = L.recover_check(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 2], [-3, 0, 0])
    assert v["ok"] and v["curvature"]["directed"]
