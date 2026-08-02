"""rc252 (gh #1390 item 4b) — laplacian.order_fingerprint / recover_check_order.

The octonion ORDER faculty: an additive 5th recover_check faculty that catches a
walk-order corruption the graph-level faculties are BLIND to (F1079/F1230 — two
orders can share the identical directed graph). Faithful port of
R-RBS-LM-OCTRECOVER: the path-ordered EXACT-integer octonion product (via the
C-routed qm.so8.octonion_mult_table) — 8 ints, length-independent, NO mod (a
lossy verifier, not a store). Supersedes the removed rc247 (which mod-reduced by
2**31-1 — a divergence from the prototype's raw exact products).
"""
from __future__ import annotations

from srmech.math import laplacian as L


def test_the_figure_eight_headline():
    # two walks share the IDENTICAL directed graph (charge 0) — the graph
    # faculties are BLIND; the octonion ORDER faculty CATCHES the reorder.
    walkA = [0, 1, 0, 2, 0]
    walkB = [0, 2, 0, 1, 0]                    # a graph-preserving reorder
    fpA = L.order_fingerprint(walkA)
    assert L.recover_check_order(fpA, walkA) is True     # honest recall
    assert L.recover_check_order(fpA, walkB) is False    # the reorder CAUGHT


def test_fingerprint_is_8_ints_and_length_independent():
    for w in ([], [0], list(range(50)), [7, 7, 7, 7]):
        fp = L.order_fingerprint(w)
        assert len(fp) == 8
    assert L.order_fingerprint([]) == [1, 0, 0, 0, 0, 0, 0, 0]   # empty = identity


def test_raw_exact_no_mod():
    # a length-20 walk grows into big exact ints (NOT reduced mod 2**31-1);
    # matches an INDEPENDENT hand-rolled table product exactly.
    #
    # rc352 (`#T997`): the op under test no longer carries its own private
    # `_order_omul` — the step is the shipped `cascade.table_product`. The
    # reference below is therefore a genuine ORACLE (a hand-rolled triple loop
    # sharing no code with the shipped op), which is exactly what it must be;
    # it is labelled as one so a later reader cannot mistake it for a second
    # implementation the package owns.
    from srmech.physics.qm.so8 import octonion_mult_table
    C = octonion_mult_table()

    def _order_fingerprint_oracle(fiber):
        acc = [1, 0, 0, 0, 0, 0, 0, 0]
        for nid in fiber:
            a, b, out = acc, L._order_node_octonion(int(nid)), [0] * 8
            for i in range(8):
                for j in range(8):
                    for k in range(8):
                        if C[i][j][k]:
                            out[k] += C[i][j][k] * a[i] * b[j]
            acc = out
        return acc

    w = list(range(20))
    fp = L.order_fingerprint(w)
    assert fp == _order_fingerprint_oracle(w)
    assert any(abs(x) > 2 ** 31 for x in fp)             # raw big ints (no mod)


def test_node_octonion_is_generic():
    # F1230/F1231: distinct-per-axis, NON-uniform-component (not a basis unit /
    # a `1 + id%m` collapse).
    for nid in (0, 1, 2, 5, 100):
        no = L._order_node_octonion(nid)
        assert no[0] == 1
        assert len(set(no[1:])) > 1, (nid, no)


def test_order_sensitivity():
    w = [0, 1, 2, 3, 1, 0]
    assert L.order_fingerprint(w) != L.order_fingerprint(list(reversed(w)))


def test_recover_check_order_via_eulerian_walk():
    edges = [(0, 1), (1, 2), (2, 0), (0, 1)]
    true_walk = L.eulerian_path(edges)
    fp = L.order_fingerprint(true_walk)
    assert L.recover_check_order(fp, true_walk) is True


def test_registered_in_tool_schema():
    from srmech.introspect.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.math.laplacian.order_fingerprint" in names
    assert "srmech.math.laplacian.recover_check_order" in names
