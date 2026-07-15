"""rc247 (gh #1390 item 4b / F1231) — the octonion ORDER faculty.

``laplacian.order_fingerprint`` / ``recover_check_order`` are the 5th
recover_check faculty: the path-ordered octonion product of a walk is an
order-sensitive, length-independent fingerprint (8 ints, reduced mod 2**31−1)
that CATCHES a graph-preserving reorder the op / operand / responsion /
ℂ-curvature faculties all miss. The pure Hierholzer-grade product is the parity
oracle; the C peer (srmech_octonion_order_fingerprint, composing the attested
srmech_cd_basis_product) is byte-identical when loaded.
"""
from __future__ import annotations

import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as L

NATIVE = _native.has_native_octonion_order()
_P = (1 << 31) - 1


def test_the_figure_eight_headline():
    # two walks share the IDENTICAL directed graph (charge 0) — the graph
    # faculties are BLIND; the octonion ORDER faculty CATCHES the reorder.
    walkA = [0, 1, 0, 2, 0]
    walkB = [0, 2, 0, 1, 0]              # a graph-preserving reorder
    fpA = L.order_fingerprint(walkA)
    assert L.recover_check_order(fpA, walkA) is True        # honest recall
    assert L.recover_check_order(fpA, walkB) is False       # the reorder CAUGHT


def test_fingerprint_is_8_ints_bounded_and_length_independent():
    for w in ([], [0], list(range(50)), [7, 7, 7, 7]):
        fp = L.order_fingerprint(w)
        assert len(fp) == 8
        assert all(0 <= x < _P for x in fp)                 # bounded (mod 2**31−1)


def test_node_octonion_is_generic():
    # F1230/F1231: distinct-per-axis, NON-uniform-component (not [1,c,c,...],
    # which collides like a basis unit).
    for nid in (0, 1, 2, 5, 100):
        no = L._node_octonion(nid)
        assert no[0] == 1
        assert len(set(no[1:])) > 1, (nid, no)


def test_order_sensitivity_general():
    # reversing a non-palindromic walk changes the fingerprint
    w = [0, 1, 2, 3, 1, 0]
    assert L.order_fingerprint(w) != L.order_fingerprint(list(reversed(w)))


def test_recover_check_order_via_eulerian_walk():
    # the intended use: store the fingerprint of the true walk; recompute from
    # an eulerian_path reconstruction; a matching graph → matching order.
    edges = [(0, 1), (1, 2), (2, 0), (0, 1)]
    true_walk = L.eulerian_path(edges)
    fp = L.order_fingerprint(true_walk)
    assert L.recover_check_order(fp, true_walk) is True


def test_registered_in_tool_schema():
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.order_fingerprint" in names
    assert "srmech.amsc.laplacian.recover_check_order" in names


# ── native parity ──────────────────────────────────────────────────────────

@pytest.mark.skipif(not NATIVE, reason="rc247 octonion order C peer not loaded")
def test_native_symbol_bound():
    assert hasattr(_native.LIB, "srmech_octonion_order_fingerprint")
    assert _native.NATIVE_ABI_VERSION == 5


@pytest.mark.skipif(not NATIVE, reason="rc247 octonion order C peer not loaded")
def test_native_equals_pure():
    from srmech.qm.octonion import octonion_mult_table

    def pure(fiber):
        table = octonion_mult_table()
        acc = [1, 0, 0, 0, 0, 0, 0, 0]
        for nid in fiber:
            acc = L._octonion_mul(acc, L._node_octonion(int(nid)), table)
        return acc

    for w in ([0, 1, 0, 2, 0], [0, 2, 0, 1, 0], [5, 6, 7, 5, 6],
              list(range(20)) + list(range(20)), [0], []):
        assert _native.octonion_order_fingerprint_c([int(x) for x in w]) == pure(w), w
