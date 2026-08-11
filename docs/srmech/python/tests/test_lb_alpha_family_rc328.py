"""rc328 (task #893 / #888 rec (c)) — the Laplace–Beltrami α-family.

Two closed-form Class-L constructors that expose the discrete Laplace–Beltrami
operator as a WEIGHTING/NORMALIZATION of the shipped weighted graph Laplacian
(the #888 verdict: LB is a *weighting* of Class L, not a new member —
docs/srmech/notes/laplace_beltrami_scoping.md):

  * ``mass_normalized_laplacian`` — the α-family / mass-normalized Laplacian
    M^(−1/2)(D−W)M^(−1/2) (symmetric) or M^(−1)(D−W) (random-walk). masses=None
    → degree D (α=0 connectivity, recovers ``normalized_laplacian``); a supplied
    diagonal mass → α=1 metric / discrete LB.
  * ``cotangent_weights`` — the discrete-LB cotangent edge weights
    ½·cot(θ) = ½·(u·v)/|u×v| (Lagrange cross magnitude; NO trig, NO abs), which
    feed ``dense_laplacian`` (parallel-edge accumulation) into the standard
    ½(cot α + cot β) cotangent Laplacian.

Covers: native == pure byte/value parity; the PSD / nullvector / [0,2] /
row-sum correctness invariants; the cotangent closed form on a right / an
equilateral triangle and a two-triangle grid; the full α=1 LB pipeline; and
registration (__all__, LAPLACIAN_OPS, tool_schema).
"""
from __future__ import annotations

import math

import pytest

from srmech import _native
from srmech.math import laplacian as _lap
from srmech.math.laplacian import (
    LAPLACIAN_OPS,
    cotangent_weights,
    dense_laplacian,
    jacobi_eigvals,
    mass_normalized_laplacian,
    normalized_laplacian,
    _mass_normalized_laplacian_py,
    _cotangent_weights_py,
    _validate_edges_weights_py,
)


# ── graphs / meshes under test ───────────────────────────────────────────────
_PATH_N, _PATH_E = 4, [(0, 1), (1, 2), (2, 3)]
_CYCLE_N, _CYCLE_E = 5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
_WEIGHTED_N = 4
_WEIGHTED_E = [(0, 1), (1, 2), (2, 3), (0, 3), (0, 2)]
_WEIGHTED_W = [1.5, 2.0, 0.5, 3.0, 0.75]


def _mat_eq_rows(mat, rows, tol=0.0):
    n = len(rows)
    assert mat.n_rows == n and mat.n_cols == n
    for i in range(n):
        for j in range(n):
            d = abs(mat[i, j] - rows[i][j])
            assert d <= tol, f"[{i},{j}] native {mat[i, j]!r} != pure {rows[i][j]!r} (Δ={d})"


# ═══════════════════════════════════════════════════════════════════════════
# mass_normalized_laplacian
# ═══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("kind", ["symmetric", "rw"])
@pytest.mark.parametrize(
    "n,edges,weights,masses",
    [
        (_PATH_N, _PATH_E, None, None),
        (_CYCLE_N, _CYCLE_E, None, None),
        (_WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W, None),
        (_WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W, [2.0, 3.0, 1.5, 4.0]),
        (_PATH_N, _PATH_E, None, [1.0, 2.0, 2.0, 1.0]),
    ],
)
def test_mass_normalized_native_equals_pure(n, edges, weights, masses, kind):
    """The C peer builds a byte/value-identical matrix to the pure cascade."""
    kind_code = 0 if kind == "symmetric" else 1
    el, wl = _validate_edges_weights_py(n, edges, weights)
    ml = None if masses is None else [float(x) for x in masses]
    pure = _mass_normalized_laplacian_py(n, el, wl, ml, kind_code)
    api = mass_normalized_laplacian(n, edges, weights, masses, kind=kind)
    _mat_eq_rows(api, pure, tol=0.0)


def test_mass_normalized_forced_pure_equals_native(monkeypatch):
    """Toggling HAS_NATIVE off yields the SAME matrix — the pure path is a
    complete no-C alternative (ADR-0003), value-identical here."""
    native = mass_normalized_laplacian(_WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W,
                                       [2.0, 3.0, 1.5, 4.0], kind="symmetric")
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    pure = mass_normalized_laplacian(_WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W,
                                     [2.0, 3.0, 1.5, 4.0], kind="symmetric")
    _mat_eq_rows(native, [[pure[i, j] for j in range(_WEIGHTED_N)]
                          for i in range(_WEIGHTED_N)], tol=0.0)


def test_masses_none_symmetric_recovers_normalized_laplacian():
    """α=0 (masses=degree) symmetric IS I − D^(−1/2)AD^(−1/2), up to the
    exact-1 diagonal convention (here the diagonal is the float d_i·s_i²)."""
    for n, edges, weights in [(_PATH_N, _PATH_E, None),
                              (_CYCLE_N, _CYCLE_E, None),
                              (_WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W)]:
        mm = mass_normalized_laplacian(n, edges, weights)  # symmetric, masses=None
        nl = normalized_laplacian(n, edges, weights)
        for i in range(n):
            for j in range(n):
                assert abs(mm[i, j] - nl[i, j]) < 1e-12


def test_symmetric_is_psd_and_eigs_in_0_2_for_degree_norm():
    """Degree-normalized symmetric L̂ is PSD with spectrum in [0, 2]."""
    for n, edges, weights in [(_PATH_N, _PATH_E, None),
                              (_CYCLE_N, _CYCLE_E, None),
                              (_WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W)]:
        mm = mass_normalized_laplacian(n, edges, weights)
        eigs = list(jacobi_eigvals(mm))
        assert min(eigs) >= -1e-9, f"not PSD: {eigs}"
        assert max(eigs) <= 2.0 + 1e-9, f"eig > 2: {eigs}"


def test_symmetric_mass_nullvector_is_sqrt_m_times_ones():
    """L̂·(M^(1/2)·𝟙) = 0: M^(−1/2)LM^(−1/2)·M^(1/2)𝟙 = M^(−1/2)L𝟙 = 0."""
    n, edges, weights = _WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W
    masses = [2.0, 3.0, 1.5, 4.0]
    mm = mass_normalized_laplacian(n, edges, weights, masses, kind="symmetric")
    nullv = [math.sqrt(m) for m in masses]
    for i in range(n):
        resid = sum(mm[i, j] * nullv[j] for j in range(n))
        assert abs(resid) < 1e-12, f"row {i} residual {resid}"
    # and PSD
    eigs = list(jacobi_eigvals(mm))
    assert min(eigs) >= -1e-9


def test_random_walk_rows_sum_to_zero():
    """M^(−1)(D−W) has every row summing to 0 (L rows sum to 0, scaled)."""
    for n, edges, weights, masses in [
        (_PATH_N, _PATH_E, None, None),
        (_WEIGHTED_N, _WEIGHTED_E, _WEIGHTED_W, [2.0, 3.0, 1.5, 4.0]),
    ]:
        rw = mass_normalized_laplacian(n, edges, weights, masses, kind="rw")
        for i in range(n):
            rs = sum(rw[i, j] for j in range(n))
            assert abs(rs) < 1e-12, f"row {i} sum {rs}"


def test_mass_normalized_input_validation():
    with pytest.raises(ValueError):
        mass_normalized_laplacian(3, [(0, 1)], kind="bogus")
    with pytest.raises(ValueError):
        mass_normalized_laplacian(3, [(0, 1)], masses=[1.0, 2.0])  # len != n


def test_isolated_vertex_gets_zero_scale():
    """A degree-0 / mass-0 vertex gets scale 0 (its row/col is zeroed),
    mirroring normalized_laplacian — no abs, no div-by-zero."""
    mm = mass_normalized_laplacian(3, [(0, 1)])  # vertex 2 isolated
    for j in range(3):
        assert mm[2, j] == 0.0 and mm[j, 2] == 0.0


# ═══════════════════════════════════════════════════════════════════════════
# cotangent_weights
# ═══════════════════════════════════════════════════════════════════════════
def _accumulate(edges, weights, n):
    """Deduplicate the per-corner contributions into per-edge weights (the
    ½(cot α + cot β) form dense_laplacian assembles)."""
    acc: dict = {}
    for (u, v), w in zip(edges, weights):
        key = (u, v) if u <= v else (v, u)
        acc[key] = acc.get(key, 0.0) + w
    return acc


@pytest.mark.parametrize(
    "tris,pos",
    [
        ([(0, 1, 2)], [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]),                 # right, 2-D
        ([(0, 1, 2)], [(0.0, 0.0), (1.0, 0.0), (0.5, math.sqrt(3) / 2)]),   # equilateral
        ([(0, 1, 2), (0, 2, 3)],
         [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),                 # unit square
        ([(0, 1, 2)], [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 1.0)]), # 3-D
    ],
)
def test_cotangent_native_equals_pure(tris, pos):
    """The C peer emits byte/value-identical per-corner contributions."""
    dim = len(pos[0])
    tris_i = [tuple(int(x) for x in t) for t in tris]
    pos_l = [[float(c) for c in p] for p in pos]
    e_pure, w_pure = _cotangent_weights_py(tris_i, pos_l, dim)
    e_api, w_api = cotangent_weights(tris, pos)
    assert e_api == e_pure
    assert w_api == w_pure  # exact float equality — same sqrt cascade


def test_cotangent_right_triangle_closed_form():
    """Right triangle: the edge opposite the right angle gets ½·cot(90°)=0;
    the two legs' opposite edges get ½·cot(45°)=½."""
    e, w = cotangent_weights([(0, 1, 2)], [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)])
    acc = _accumulate(e, w, 3)
    assert abs(acc[(1, 2)] - 0.0) < 1e-15      # opposite the right angle
    assert abs(acc[(0, 2)] - 0.5) < 1e-12
    assert abs(acc[(0, 1)] - 0.5) < 1e-12


def test_cotangent_equilateral_closed_form():
    """Equilateral: every angle 60°, cot(60°)=1/√3, so each edge weight is
    ½·(1/√3)."""
    e, w = cotangent_weights(
        [(0, 1, 2)], [(0.0, 0.0), (1.0, 0.0), (0.5, math.sqrt(3) / 2)])
    acc = _accumulate(e, w, 3)
    want = 0.5 * (1.0 / math.sqrt(3))
    for edge in ((0, 1), (0, 2), (1, 2)):
        assert abs(acc[edge] - want) < 1e-12, f"{edge}: {acc[edge]} != {want}"


def test_cotangent_laplacian_symmetric_psd_rowsum_zero():
    """The assembled cotangent Laplacian is symmetric, PSD, has a 0 eigenvalue
    (constant nullvector), and every row sums to 0."""
    tris = [(0, 1, 2), (0, 2, 3)]
    pos = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    Lc = dense_laplacian(4, *cotangent_weights(tris, pos))
    for i in range(4):
        assert abs(sum(Lc[i, j] for j in range(4))) < 1e-12       # rows sum 0
        for j in range(4):
            assert abs(Lc[i, j] - Lc[j, i]) < 1e-15               # symmetric
    eigs = list(jacobi_eigvals(Lc))
    assert min(eigs) >= -1e-9                                     # PSD
    assert abs(min(abs(x) for x in eigs)) < 1e-9                  # a 0 eigenvalue


def test_cotangent_feeds_full_lb_pipeline():
    """The α=1 discrete Laplace–Beltrami pipeline: cotangent stiffness weights
    + a Voronoi-like diagonal mass → mass_normalized_laplacian is symmetric,
    PSD, with the M^(1/2)𝟙 nullvector."""
    tris = [(0, 1, 2), (0, 2, 3)]
    pos = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    edges, weights = cotangent_weights(tris, pos)
    masses = [1.0, 1.0, 1.0, 1.0]  # uniform (barycentric) mass
    lb = mass_normalized_laplacian(4, edges, weights, masses, kind="symmetric")
    nullv = [math.sqrt(m) for m in masses]
    for i in range(4):
        assert abs(sum(lb[i, j] * nullv[j] for j in range(4))) < 1e-12
    assert min(jacobi_eigvals(lb)) >= -1e-9


def test_cotangent_degenerate_triangle_raises():
    with pytest.raises(ValueError):
        cotangent_weights([(0, 1, 2)], [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)])  # collinear


def test_cotangent_input_validation():
    with pytest.raises(ValueError):
        cotangent_weights([(0, 1, 2)], [])                       # empty positions
    with pytest.raises(ValueError):
        cotangent_weights([(0, 1, 2)], [(0.0,), (1.0,), (0.0,)])  # 1-D
    with pytest.raises(ValueError):
        cotangent_weights([(0, 1, 5)], [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)])  # oob idx


def test_cotangent_shared_edge_accumulates_both_triangles():
    """Two triangles sharing an edge emit that edge TWICE (parallel edges);
    dense_laplacian sums them into ½(cot α + cot β)."""
    tris = [(0, 1, 2), (0, 2, 3)]
    pos = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    e, w = cotangent_weights(tris, pos)
    shared = [wt for (u, v), wt in zip(e, w) if {u, v} == {0, 2}]
    assert len(shared) == 2  # one contribution from each triangle


# ═══════════════════════════════════════════════════════════════════════════
# registration
# ═══════════════════════════════════════════════════════════════════════════
def test_registration_all_and_laplacian_ops():
    for name in ("mass_normalized_laplacian", "cotangent_weights"):
        assert name in _lap.__all__, f"{name} missing from laplacian.__all__"
        assert name in LAPLACIAN_OPS, f"{name} missing from LAPLACIAN_OPS"


def test_registration_tool_schema():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    schema = get_tool_schema()
    assert len(schema.tools) == 605
    names = {t.name for t in schema.tools}
    for op in ("mass_normalized_laplacian", "cotangent_weights"):
        assert f"srmech.math.laplacian.{op}" in names, f"{op} ToolEntry missing"


def test_c_claims_manifest_names_the_symbols():
    """The c_dispatched claim resolves to the real C symbols (rc300 manifest)."""
    from srmech.introspect._c_claims import C_CLAIMS
    assert C_CLAIMS["srmech.math.laplacian.mass_normalized_laplacian"] == (
        "srmech_graph_mass_normalized_laplacian",)
    assert C_CLAIMS["srmech.math.laplacian.cotangent_weights"] == (
        "srmech_graph_cotangent_weights",)
