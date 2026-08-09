"""rc204 (gh#1324; F1167–F1169) — the spectral SPINE.

`srmech.math.laplacian.spectral_spine` reads the DOMINANT eigenvector (largest
λ) of a (signed) graph Laplacian: its top-|component| nodes are the structurally
CENTRAL items — the dominant-mode read-out that completes the community/spine
pair with the LOW-mode fiedler_vector / fiedler_sparse (2-way) +
three_fold_eigvec_groups (3-way). `relational_structure` is the one-call sugar.

This suite pins:
  1. Hand-checked star graph — the hub IS the spine (analytic eigenvector).
  2. native == pure WITHIN-TOL on a graph with a non-degenerate, well-separated
     dominant eigenvector (the C composite vs the genuinely-pure Jacobi cascade).
  3. relational_structure — spine + Fiedler communities + λ₂ coherence.
  4. Edge cases — empty graph, single node, k ≤ 0, k > n, weights, no abs().
  5. Registration — the two ToolEntries, tools.total == 418, the Rosetta rows,
     the C peer exists / is JPL-clean-adjacent.

Numpy-free (the whole laplacian surface is numpy-free); the test is numpy-free.
"""
from __future__ import annotations

import pytest

from srmech.math import laplacian as L
from srmech import _native
from srmech.math.laplacian import (
    signed_laplacian,
    symmetric_eigendecompose,
    _jacobi_eig_py,
    _spectral_spine_native,
    _infer_n_from_edges,
)


# --- a genuinely-PURE reference (no C anywhere) --------------------------------
def _pure_spine(n, edges, weights, k):
    """The spine via the pure-Python Jacobi cascade (`_jacobi_eig_py`) — NOT the
    C-backed symmetric_eigendecompose — so it is a genuine native==pure oracle
    even when HAS_NATIVE. Dominant eigenvector = last column (ascending λ); rank
    by |component|² (re²+im², no abs / no sqrt), descending, ties ascending idx."""
    Lm = signed_laplacian(n, edges, weights)
    rows = [[Lm[i, j] for j in range(n)] for i in range(n)]
    _ev, V = _jacobi_eig_py(rows)  # V nested list, columns ascending
    col = n - 1
    magsq = [V[i][col] * V[i][col] for i in range(n)]
    order = sorted(range(n), key=lambda i: (-magsq[i], i))
    return order[: min(int(k), n)]


# ── 1. hand-checked star: the hub is the spine ────────────────────────────────
def test_star_hub_is_the_spine():
    # K_{1,4}: hub = node 0, leaves = 1..4. The largest Laplacian eigenvalue is
    # m+1 = 5 with eigenvector (m, -1, -1, -1, -1) = (4, -1, -1, -1, -1): the hub
    # has the LARGEST |component| (4 vs 1), so it is the top of the spine.
    star = [(0, 1), (0, 2), (0, 3), (0, 4)]
    assert L.spectral_spine(star, k=1) == [0]
    full = L.spectral_spine(star, k=8)
    assert full[0] == 0                      # hub first
    assert set(full) == {0, 1, 2, 3, 4}      # all nodes, leaves after the hub
    assert len(full) == 5                     # min(k=8, n=5)


def test_star_n_inferred_from_edges():
    # n is one past the largest endpoint — no explicit n argument.
    assert _infer_n_from_edges([(0, 1), (0, 4)]) == 5
    assert _infer_n_from_edges([]) == 0


# ── 2. native == pure WITHIN-TOL (non-degenerate dominant eigenvalue) ─────────
_PARITY_EDGES = [(0, 1), (0, 2), (0, 3), (1, 2), (3, 4), (4, 5)]
_PARITY_W = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
_PARITY_N = 6


def _assert_well_separated(n, edges, w):
    """The dominant eigenvector magnitudes are all distinct with a gap far above
    fp noise, so the top-k ordering is STABLE (native and pure agree exactly)."""
    ref = _pure_spine(n, edges, w, n)
    Lm = signed_laplacian(n, edges, w)
    rows = [[Lm[i, j] for j in range(n)] for i in range(n)]
    _ev, V = _jacobi_eig_py(rows)
    col = n - 1
    mags = sorted((V[i][col] * V[i][col] for i in range(n)), reverse=True)
    gaps = [mags[i] - mags[i + 1] for i in range(n - 1)]
    assert min(gaps) > 1e-6, "parity graph must have a well-separated spectrum"
    return ref


def test_public_spine_matches_pure_cascade():
    # spectral_spine() dispatches to the C composite when HAS_NATIVE, else its own
    # pure fallback; either way it must match the genuinely-pure Jacobi oracle.
    ref = _assert_well_separated(_PARITY_N, _PARITY_EDGES, _PARITY_W)
    got = L.spectral_spine(_PARITY_EDGES, _PARITY_W, k=_PARITY_N)
    assert got == ref


@pytest.mark.skipif(
    not _native.has_native_spectral_spine(),
    reason="rc204 native spectral_spine composite not loaded (pure / stale host)",
)
def test_native_composite_matches_pure_cascade():
    # Exercise the C peer DIRECTLY (not just via the public wrapper) vs the pure
    # oracle — the differential native==pure parity contract.
    ref = _pure_spine(_PARITY_N, _PARITY_EDGES, _PARITY_W, _PARITY_N)
    native = _spectral_spine_native(_PARITY_N, _PARITY_EDGES, _PARITY_W, _PARITY_N)
    assert native is not None
    assert native == ref
    # and top-k truncation is a prefix
    assert _spectral_spine_native(_PARITY_N, _PARITY_EDGES, _PARITY_W, 3) == ref[:3]


# ── 3. relational_structure ───────────────────────────────────────────────────
def test_relational_structure_shape_and_values():
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
    rs = L.relational_structure(edges)
    assert set(rs) == {"spine", "communities", "coherence"}
    # spine agrees with spectral_spine(default k=8)
    assert rs["spine"] == L.spectral_spine(edges)
    # communities partition ALL nodes exactly once (a 2-way split)
    left, right = rs["communities"]
    assert sorted(left + right) == list(range(4))
    assert set(left).isdisjoint(right)
    # coherence == λ₂ (the second-smallest eigenvalue), non-negative
    eigvals, _V = symmetric_eigendecompose(signed_laplacian(4, edges, None))
    assert rs["coherence"] == pytest.approx(float(eigvals[1]), abs=1e-9)
    assert rs["coherence"] >= -1e-9


def test_relational_structure_communities_are_fiedler_sign_split():
    # A barbell (two triangles joined by a bridge) has an obvious 2-way split.
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 3)]
    rs = L.relational_structure(edges)
    left, right = rs["communities"]
    assert sorted(left + right) == list(range(6))
    # the two triangles land on opposite sides of the bridge (Fiedler sign).
    assert {0, 1, 2} == set(left) or {0, 1, 2} == set(right)


# ── 4. edge cases ─────────────────────────────────────────────────────────────
def test_empty_graph():
    assert L.spectral_spine([]) == []
    rs = L.relational_structure([])
    assert rs == {"spine": [], "communities": [[], []], "coherence": 0.0}


def test_single_node():
    # one self-loop → n = 1; the sole node is trivially the spine, no bisection.
    assert L.spectral_spine([(0, 0)], k=4) == [0]
    rs = L.relational_structure([(0, 0)])
    assert rs["spine"] == [0]
    assert rs["communities"] == [[0], []]
    assert rs["coherence"] == 0.0


def test_k_zero_and_negative():
    star = [(0, 1), (0, 2)]
    assert L.spectral_spine(star, k=0) == []
    assert L.spectral_spine(star, k=-3) == []


def test_k_exceeds_n_returns_all():
    star = [(0, 1), (0, 2)]  # n = 3
    got = L.spectral_spine(star, k=99)
    assert len(got) == 3
    assert set(got) == {0, 1, 2}


def test_negative_weights_signed_laplacian():
    # A signed (frustrated) edge is allowed — the spine is still well-defined
    # (signed degree Σ|A_ij| keeps L PSD). Just assert it returns a valid spine.
    edges = [(0, 1), (1, 2), (2, 0)]
    got = L.spectral_spine(edges, [1.0, -1.0, 1.0], k=3)
    assert sorted(got) == [0, 1, 2]


def test_no_abs_in_source():
    # Cascade-honesty: the spine ranking uses Class-K magnitude-square, never
    # abs(). AST-check for a genuine abs() CALL (not a docstring mention).
    import ast
    import inspect
    import textwrap
    for fn in (L._spine_from_V, L.spectral_spine, L._infer_n_from_edges):
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        calls = [n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        assert "abs" not in calls, f"{fn.__name__} calls abs()"


# ── 5. registration + Rosetta ledger ──────────────────────────────────────────
def test_tool_schema_registration():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.math.laplacian.spectral_spine" in names
    assert "srmech.math.laplacian.relational_structure" in names
    assert len(get_tool_schema().tools) == 569


def test_rosetta_ledger_rows():
    import json
    from pathlib import Path
    fx = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in fx.read_text(encoding="utf-8").splitlines() if l.strip()}
    assert rows["srmech.math.laplacian.spectral_spine"] == "c_dispatched"
    assert rows["srmech.math.laplacian.relational_structure"] == "composition_of_c"


def test_exports_in_all():
    assert "spectral_spine" in L.__all__
    assert "relational_structure" in L.__all__
