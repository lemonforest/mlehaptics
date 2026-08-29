"""rc461 (`#T1181`) — the ``feit_higman_allowed`` BRANCH gate.

THE MEASUREMENT THAT PUT THIS FILE HERE
=======================================
``generalized_ngon`` has shipped a ``feit_higman_allowed`` field since rc399.
It rides inside every wheel, reaches users through ``describe()``, the MCP tool
list and the compiled-in C tool registry, and it is named in the op's docstring
and in its ``returns=`` string.

Measured at the rc460 head, predicate stated — ``git grep -n
feit_higman_allowed -- tests/`` — the field appears in **zero** test files. Not
under-tested: **unasserted, in either branch.** The op's own acceptance file,
``tests/test_cayley_plane_ngon_rc399.py``, exercises girth / diameter /
biregularity / the spectral constraint and never reads this key.

That is the ungated-surface shape exactly
(``[[feedback_ungated_surfaces_trickle_gated_surfaces_race_to_100]]``), on a
field whose whole job is to be a verdict.

WHAT THE PREDICATE ACTUALLY SAYS, AND THE TRAP IN IT
====================================================
``srmech/math/laplacian.py``::

    feit_higman_allowed = (n in _FEIT_HIGMAN_THICK_N) if thick else (n is not None)

TWO ARMS, and reading the field as "n ∈ {2,3,4,6,8}" is wrong for half of its
domain. A THIN structure at ``n = 5`` — the ordinary pentagon, ``C_10`` — is
ALLOWED, because ordinary n-gons exist for every ``n``; only the THICK arm is
constrained. A test that only ever fed thick examples would report full
coverage of a predicate whose thin arm it never entered.

THE FALSE BRANCH IS REACHABLE, AND IS REACHED HERE
==================================================
``[[feedback_a_guard_that_fires_is_evidence_not_an_obstacle]]``: "not A" ≠ "B".
The reachable False arm is ``n is None`` — an incidence structure whose graph
is ACYCLIC has no girth, so no polygon order. Three points on two lines is
enough, and it is built here rather than described.

⚠️ THE ARM THIS FILE DOES **NOT** WITNESS, NAMED RATHER THAN HIDDEN
==================================================================
The other False arm — **thick, with ``n ∉ {2,3,4,6,8}``** — is NOT witnessed by
any object in this tree, and cannot be without external data. Such an object is
a thick biregular bipartite graph of girth ≥ 10; at the minimum degree 3 the
smallest is a 70-vertex ``(3,10)``-cage, whose adjacency is a published
construction and not something derivable from first principles inside a test.
Committing a recalled LCF sequence for one would be exactly the citation-
hallucination class the whole AMSC discipline exists to prevent
(``[[feedback_pdf_extraction_citation_discipline]]``), so it is not committed.

The gap is therefore a NAMED BLIND SPOT, in the shape
``tests/test_unowned_acquisition_rc432.py`` uses: the arm is stated, the reason
it is absent is stated, and the seeded mutation below still proves the
predicate is live in both directions on the arms that ARE constructible.

WHAT IS CONSTRUCTED HERE, FROM FIRST PRINCIPLES, WITH NO EXTERNAL DATA
=====================================================================
The Petersen graph as the Kneser graph ``K(5,2)`` (vertices = 2-subsets of a
5-set, edges = disjoint pairs) and its **bipartite double cover**, the Desargues
graph. Both are derived, and every property this file uses of them — 3-regular,
20 vertices, girth 6, diameter 5 — is MEASURED by ``generalized_ngon``'s own
BFS rather than quoted. It is the sharpest witness in the file: Desargues is
thick, biregular, connected, has ``n = 3``, and is therefore
``feit_higman_allowed = True`` **while not being a generalized polygon at all**
(diameter 5 ≠ 3). Allowed is not is.
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

import pytest

from srmech.math import laplacian
from srmech.math.laplacian import _FEIT_HIGMAN_THICK_N, generalized_ngon


# ── constructed witnesses (no external data anywhere in this file) ─────────

def _petersen_edges() -> Tuple[List[Tuple[int, int]], Dict[Tuple[int, ...], int]]:
    """Petersen = the Kneser graph K(5,2): 2-subsets of {0..4}, adjacent iff
    DISJOINT. Derived, not tabulated."""
    verts = list(combinations(range(5), 2))
    idx = {v: i for i, v in enumerate(verts)}
    edges = [(idx[a], idx[b]) for a, b in combinations(verts, 2)
             if not set(a) & set(b)]
    return edges, idx


def _bipartite_double_cover_as_incidence() -> List[Tuple[int, ...]]:
    """The bipartite double cover of Petersen (the Desargues graph), expressed
    as an incidence structure: ``points`` = one copy of V, ``lines`` = the
    other, incident iff adjacent in Petersen."""
    edges, _ = _petersen_edges()
    return [tuple(sorted({b if a == v else a for a, b in edges if v in (a, b)}))
            for v in range(10)]


# ══════════════════════════════════════════════════════════════════════
# 1. The FALSE branch — reached, with a constructed witness
# ══════════════════════════════════════════════════════════════════════

def test_an_acyclic_incidence_structure_is_not_allowed() -> None:
    """Three points on two lines: the incidence graph is a path, so it has no
    cycle, so ``girth`` is absent and ``n`` is ``None``. The thin arm then
    reads ``n is not None`` → **False**. This is the whole False branch, and
    before this file nothing in the tree entered it."""
    got = generalized_ngon(n_points=3, lines=[(0, 1), (1, 2)],
                           spectral_max_nodes=0)
    assert got["n"] is None
    assert got["thick"] is False
    assert got["feit_higman_allowed"] is False
    assert got["is_generalized_polygon"] is False


def test_the_false_branch_is_not_an_artefact_of_disconnection() -> None:
    """The witness above is CONNECTED (diameter 4), so its False verdict comes
    from acyclicity and not from the graph being in pieces — otherwise the test
    would be measuring the wrong cause."""
    got = generalized_ngon(n_points=3, lines=[(0, 1), (1, 2)],
                           spectral_max_nodes=0)
    assert got["connected"] is True
    assert got["diameter"] == 4
    assert got["girth"] < 0            # the "no cycle" sentinel


# ══════════════════════════════════════════════════════════════════════
# 2. The TWO ARMS are genuinely different — the trap, executed
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("k", [5, 7, 9])
def test_thin_polygons_are_allowed_at_n_outside_the_thick_set(k: int) -> None:
    """``n = 5, 7, 9`` are NOT in ``{2,3,4,6,8}``, and the ordinary k-gon at
    each is still ``feit_higman_allowed`` — because it is THIN. Reading the
    field as the thick set alone gets every one of these wrong."""
    got = generalized_ngon(example="ordinary_%d" % k)
    assert got["n"] == k
    assert k not in _FEIT_HIGMAN_THICK_N
    assert got["thick"] is False
    assert got["order_s"] == 1 and got["order_t"] == 1
    assert got["feit_higman_allowed"] is True
    assert got["is_generalized_polygon"] is True


@pytest.mark.parametrize("example,n", [("fano", 3), ("doily", 4)])
def test_the_two_thick_builtins_land_inside_the_thick_set(example: str,
                                                          n: int) -> None:
    got = generalized_ngon(example=example)
    assert got["n"] == n and got["thick"] is True
    assert got["order_s"] >= 2 and got["order_t"] >= 2
    assert n in _FEIT_HIGMAN_THICK_N
    assert got["feit_higman_allowed"] is True
    assert got["is_generalized_polygon"] is True


def test_the_thin_arm_and_the_thick_arm_disagree_somewhere() -> None:
    """The two arms must be separable by SOME input, or the branch is
    decorative. ``n = 5`` is that input: allowed thin, and the same ``n``
    would be refused thick."""
    thin5 = generalized_ngon(example="ordinary_5")
    assert thin5["thick"] is False and thin5["feit_higman_allowed"] is True
    assert (thin5["n"] in _FEIT_HIGMAN_THICK_N) is False, (
        "5 is in the thick set — the arms cannot be separated at n=5 and this "
        "test is no longer measuring the trap it was written for")


# ══════════════════════════════════════════════════════════════════════
# 3. ALLOWED is not IS — the Desargues witness, constructed
# ══════════════════════════════════════════════════════════════════════

def test_the_constructed_petersen_is_the_graph_it_claims_to_be() -> None:
    """Every property used below is MEASURED off the construction, so a wrong
    Kneser build fails here rather than silently weakening the next test."""
    edges, idx = _petersen_edges()
    assert len(idx) == 10 and len(edges) == 15
    deg = {v: sum(1 for e in edges if v in e) for v in range(10)}
    assert set(deg.values()) == {3}


def test_desargues_is_feit_higman_allowed_and_is_not_a_polygon() -> None:
    """The bipartite double cover of Petersen: thick (s = t = 2), biregular,
    connected, girth 6 so ``n = 3`` — and 3 IS in the thick set, so the field
    reads True. It is nevertheless NOT a generalized polygon, because its
    diameter is 5 and a generalized 3-gon must have diameter 3.

    "not A" ≠ "B": passing the Feit–Higman arithmetic is a NECESSARY condition
    the op reports separately, never the verdict. A consumer that read
    ``feit_higman_allowed`` as "this is a generalized polygon" would be wrong
    on this object, and this object is twenty vertices of derived combinatorics
    away from anyone who wants to check."""
    got = generalized_ngon(n_points=10, lines=_bipartite_double_cover_as_incidence(),
                           spectral_max_nodes=0)
    assert got["n_vertices"] == 20
    assert got["biregular"] is True and got["connected"] is True
    assert got["order_s"] == 2 and got["order_t"] == 2
    assert got["thick"] is True
    assert got["girth"] == 6 and got["n"] == 3
    assert got["diameter"] == 5
    assert got["feit_higman_allowed"] is True
    assert got["is_generalized_polygon"] is False


# ══════════════════════════════════════════════════════════════════════
# 4. THE SEEDED MUTATION — the predicate is live, in both directions
# ══════════════════════════════════════════════════════════════════════

def test_shrinking_the_thick_set_flips_a_thick_example_to_false(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove 3 from ``_FEIT_HIGMAN_THICK_N`` and the Fano plane — thick,
    ``n = 3`` — must go False. Without this the True results above are
    compatible with a field hard-wired to True."""
    assert generalized_ngon(example="fano")["feit_higman_allowed"] is True
    monkeypatch.setattr(laplacian, "_FEIT_HIGMAN_THICK_N",
                        tuple(n for n in _FEIT_HIGMAN_THICK_N if n != 3))
    assert generalized_ngon(example="fano")["feit_higman_allowed"] is False
    # ...and the THIN arm is untouched by that mutation, which is what proves
    # the two arms are separate code paths and not one predicate written twice.
    assert generalized_ngon(example="ordinary_3")["feit_higman_allowed"] is True


def test_widening_the_thick_set_does_not_flip_the_acyclic_witness(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The converse control. Adding every n up to 20 to the thick set leaves
    the acyclic witness False, because its arm never consults that set — so the
    False result in §1 is genuinely the ``n is None`` arm and not a thick-set
    miss wearing its clothes."""
    monkeypatch.setattr(laplacian, "_FEIT_HIGMAN_THICK_N", tuple(range(2, 21)))
    got = generalized_ngon(n_points=3, lines=[(0, 1), (1, 2)],
                           spectral_max_nodes=0)
    assert got["feit_higman_allowed"] is False


# ══════════════════════════════════════════════════════════════════════
# 5. The declared set, and the blind spot, both pinned in source
# ══════════════════════════════════════════════════════════════════════

def test_the_thick_set_is_what_the_op_documents() -> None:
    """The docstring, the ``returns=`` string and the constant must agree. Two
    of those three ship inside the wheel."""
    from srmech.introspect.tool_schema import get_tool_schema
    assert _FEIT_HIGMAN_THICK_N == (2, 3, 4, 6, 8)
    assert "{2,3,4,6,8}" in generalized_ngon.__doc__
    entry = next(t for t in get_tool_schema().tools
                 if t.name == "srmech.math.laplacian.generalized_ngon")
    assert "feit_higman_allowed" in entry.returns.shape


def test_the_unwitnessed_arm_is_named_in_this_files_own_docstring() -> None:
    """A blind spot that is not written down is not a blind spot, it is a hole.
    This asserts the disclosure exists, so deleting the paragraph turns the
    suite red rather than quietly widening the claim."""
    doc = __doc__ or ""
    assert "THE ARM THIS FILE DOES **NOT** WITNESS" in doc
    assert "``(3,10)``-cage" in doc
    assert "**thick, with ``n ∉ {2,3,4,6,8}``**" in doc
    assert "NAMED BLIND SPOT" in doc
