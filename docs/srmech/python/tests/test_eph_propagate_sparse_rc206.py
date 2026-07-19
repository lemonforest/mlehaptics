"""rc206 — ``laplacian.propagate_sparse`` — the SPARSE-SCALED EPH propagator
(siona gh#1274 item 1c, the corpus-scale residual).

WHY: rc136's ``propagate`` computes ``harvest = e^{-zL}·u0`` via the EIGENBASIS
(``symmetric_eigendecompose``) — O(n³), capped at n ≤ 256 native. The residual
of gh#1274 is the sparse-scaled variant: a CHEBYSHEV polynomial of the operator
applied with MATRIX-VECTOR PRODUCTS ONLY (no eigendecomposition, no dense
e^{-zL}), running on a corpus-scale signed graph Laplacian read straight off
the edge list. Same complex-z convention, same arg(z) coherence dial, same
seam-folded Wick factor, same complex-Vec return contract as rc136.

Covers:
  (a) THE DIFFERENTIAL vs the rc136 eigenbasis ``propagate`` on small n
      (n ≤ 256): sparse Chebyshev == eigenbasis within tol for thermal (z
      real), coherent (z imaginary) AND partial z, over unit + signed
      weights + a complex excitation;
  (b) an INDEPENDENT Taylor-matvec reference (stdlib cmath only — no
      eigensolver, no Chebyshev, no Class-N series);
  (c) CORPUS SCALE — n > 256 (past the eigenbasis native cap): P(0) = u0,
      the semigroup P(z1)P(z2) ≈ P(z1+z2), coherent norm conservation,
      thermal damping;
  (d) the 2π seam-fold consistency at large t·λ (vs rc136, which is
      seam-fold-exact there);
  (e) Python == C value parity (native vs forced-pure);
  (f) the HONEST non-convergence contract (tail not below tol within
      max_degree → ValueError, never a silently degraded tolerance);
  (g) contracts (bad edges / u0 mismatch / tol / max_degree / n = 0 /
      L = 0), read-only inputs, and registration (ToolEntry;
      tools.total == 418; LAPLACIAN_OPS).

numpy-free; the op under test uses no ``abs()`` (Class-K sign-branch /
magnitude-squares).
"""
import cmath
import math

from srmech.amsc import _native
from srmech.amsc import laplacian as L


# ── helpers (no numpy) ──────────────────────────────────────────────────


def _mag2(z):
    """Born |z|² = re² + im² (Class-K squares)."""
    c = complex(z)
    return c.real * c.real + c.imag * c.imag


def _norm(vec):
    """‖vec‖ over a complex sequence."""
    return math.sqrt(sum(_mag2(x) for x in vec))


def _err(got, ref):
    """max_i |got_i − ref_i| (the differential read-out)."""
    return max(_mag2(complex(g) - complex(r))
               for g, r in zip(got, ref)) ** 0.5


def _force_pure(fn):
    """Run fn with the native dispatch masked (the complete pure path)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _rand_graph(n, n_edges, seed, signed=False):
    """A deterministic random sparse graph (LCG; duplicate-free, no
    self-loops) — (edges, weights)."""
    st = seed
    def rnd():
        nonlocal st
        st = (st * 1103515245 + 12345) & 0x7FFFFFFF
        return st / float(0x7FFFFFFF)
    seen = set()
    edges = []
    weights = []
    guard = 0
    while len(edges) < n_edges and guard < 50 * n_edges:
        guard += 1
        a = int(rnd() * n) % n
        b = int(rnd() * n) % n
        if a == b:
            continue
        key = (a, b) if a < b else (b, a)
        if key in seen:
            continue
        seen.add(key)
        edges.append(key)
        w = 0.25 + rnd()
        if signed and rnd() < 0.4:
            w = -w
        weights.append(w)
    return edges, weights


def _ring_graph(n, chord_step=17):
    """Ring + chords — the corpus-scale test graph (bounded degree)."""
    edges = [(i, (i + 1) % n) for i in range(n)]
    edges += [(i, (i + chord_step) % n) for i in range(0, n, 5)]
    return edges


# ── an INDEPENDENT e^{-zL}·u0 reference: Taylor series applied by SPARSE
#    matvecs (stdlib cmath only; NO eigensolver, NO Chebyshev, NO Class-N
#    series — genuinely independent of the op under test). Converges to
#    machine precision for modest |z|·λ_max (terms=40). ───────────────────


def _signed_deg(n, edges, weights):
    deg = [0.0] * n
    for (a, b), w in zip(edges, weights):
        if a == b:
            continue
        m = w if w >= 0.0 else -w
        deg[a] += m
        deg[b] += m
    return deg


def _lap_matvec(n, edges, weights, deg, v):
    out = [deg[i] * v[i] for i in range(n)]
    for (a, b), w in zip(edges, weights):
        if a == b:
            continue
        out[a] -= w * v[b]
        out[b] -= w * v[a]
    return out


def _taylor_ref(n, edges, weights, u0, z, terms=40):
    """e^{-zL}·u0 = Σ_k (-z)^k (L^k u0)/k! by sparse matvecs."""
    deg = _signed_deg(n, edges, weights)
    acc = [complex(x) for x in u0]
    term = [complex(x) for x in u0]
    for k in range(1, terms + 1):
        term = _lap_matvec(n, edges, weights, deg, term)
        term = [(-z / k) * t for t in term]
        acc = [acc[i] + term[i] for i in range(n)]
    return acc


# ── (a) THE DIFFERENTIAL vs the rc136 eigenbasis propagate ──────────────


def test_differential_vs_rc136_thermal_and_coherent():
    """The load-bearing check: on n ≤ 256 the sparse Chebyshev harvest ==
    the rc136 eigenbasis harvest within tol, for BOTH a real-z (thermal)
    and an imaginary-z (coherent) case (+ partial)."""
    for n, ne, seed in ((6, 8, 11), (12, 20, 22), (40, 90, 33)):
        edges, weights = _rand_graph(n, ne, seed)
        Lm = L.signed_laplacian(n, edges, weights)
        u0 = [((i * 7 + 3) % 11) - 5.0 for i in range(n)]
        for z in (0.6 + 0j, 0.8j, 0.9 * cmath.exp(1j * 0.7)):
            dense = L.propagate(Lm, u0, z)
            sparse = L.propagate_sparse(n, edges, weights, u0=u0, z=z)
            err = _err([sparse[i] for i in range(n)],
                       [dense[i] for i in range(n)])
            assert err < 1e-8, f"n={n} z={z}: sparse vs eigenbasis {err:.3e}"


def test_differential_vs_rc136_signed_weights():
    """Negative (frustrated) edges — the signed-Laplacian leg: the sparse
    op's per-edge Class-K degree matches signed_laplacian on a
    duplicate-free edge list."""
    n = 16
    edges, weights = _rand_graph(n, 30, 77, signed=True)
    Lm = L.signed_laplacian(n, edges, weights)
    u0 = [1.0 if i % 3 == 0 else -0.5 for i in range(n)]
    for z in (0.5 + 0j, 0.7j, 0.4 + 0.4j):
        dense = L.propagate(Lm, u0, z)
        sparse = L.propagate_sparse(n, edges, weights, u0=u0, z=z)
        err = _err([sparse[i] for i in range(n)],
                   [dense[i] for i in range(n)])
        assert err < 1e-8, f"signed z={z}: {err:.3e}"


def test_differential_vs_rc136_complex_excitation():
    """A genuinely complex u0 rides the same interleaved convention."""
    n = 10
    edges, weights = _rand_graph(n, 18, 55)
    Lm = L.signed_laplacian(n, edges, weights)
    u0 = [complex(math.cos(0.3 * i), math.sin(0.5 * i)) for i in range(n)]
    for z in (0.5 + 0j, 1.1j):
        dense = L.propagate(Lm, u0, z)
        sparse = L.propagate_sparse(n, edges, weights, u0=u0, z=z)
        err = _err([sparse[i] for i in range(n)],
                   [dense[i] for i in range(n)])
        assert err < 1e-8, f"complex-u0 z={z}: {err:.3e}"


def test_unit_weights_default():
    """weights=None → unit weights (the fiedler_sparse convention)."""
    n = 8
    edges = [(i, i + 1) for i in range(n - 1)]
    dense = L.propagate(L.signed_laplacian(n, edges, None),
                        [1.0] + [0.0] * (n - 1), 0.7 + 0j)
    sparse = L.propagate_sparse(n, edges, u0=[1.0] + [0.0] * (n - 1),
                                z=0.7 + 0j)
    assert _err([sparse[i] for i in range(n)],
                [dense[i] for i in range(n)]) < 1e-8


# ── (b) the independent Taylor-matvec reference ─────────────────────────


def test_matches_independent_taylor_reference():
    n = 30
    edges, weights = _rand_graph(n, 55, 99)
    u0 = [((i * 5 + 1) % 7) - 3.0 for i in range(n)]
    for z in (0.15 + 0j, 0.12j, 0.1 + 0.08j):
        ref = _taylor_ref(n, edges, weights, u0, z)
        got = L.propagate_sparse(n, edges, weights, u0=u0, z=z)
        err = _err([got[i] for i in range(n)], ref)
        assert err < 1e-9, f"z={z}: sparse vs Taylor {err:.3e}"


# ── (c) CORPUS SCALE: n > 256, past the eigenbasis native cap ───────────


def test_corpus_scale_identity_at_z_zero():
    n = 400
    edges = _ring_graph(n)
    u0 = [math.cos(0.05 * i) for i in range(n)]
    hv = L.propagate_sparse(n, edges, u0=u0, z=0.0 + 0j)
    err = _err([hv[i] for i in range(n)], [complex(x) for x in u0])
    assert err < 1e-12, f"P(0) != u0: {err:.3e}"


def test_corpus_scale_semigroup():
    """P(z1)·(P(z2)·u0) ≈ P(z1+z2)·u0 — the semigroup self-consistency at a
    scale the eigenbasis path cannot run natively."""
    n = 400
    edges = _ring_graph(n)
    u0 = [1.0 if i == 0 else 0.0 for i in range(n)]
    z1 = 0.20 + 0.15j
    z2 = 0.35 + 0.05j
    step2 = L.propagate_sparse(n, edges, u0=u0, z=z2)
    step12 = L.propagate_sparse(n, edges, u0=step2, z=z1)
    direct = L.propagate_sparse(n, edges, u0=u0, z=z1 + z2)
    err = _err([step12[i] for i in range(n)], [direct[i] for i in range(n)])
    assert err < 1e-8, f"semigroup: {err:.3e}"


def test_corpus_scale_coherent_conserves_norm_thermal_damps():
    n = 300
    edges = _ring_graph(n, chord_step=23)
    u0 = [math.sin(0.11 * i) + 0.2 for i in range(n)]
    n0 = _norm(u0)
    co = L.propagate_sparse(n, edges, u0=u0, z=1.5j)      # coherent walk
    assert abs(_norm([co[i] for i in range(n)]) - n0) < 1e-8 * n0
    th = L.propagate_sparse(n, edges, u0=u0, z=1.5 + 0j)  # thermal
    assert _norm([th[i] for i in range(n)]) < n0


def test_corpus_scale_matches_taylor_small_z():
    """An independent cross-check ABOVE the cap: small |z| where the Taylor
    matvec reference is machine-exact."""
    n = 320
    edges = _ring_graph(n, chord_step=13)
    weights = [1.0] * len(edges)
    u0 = [((i * 3 + 2) % 5) - 2.0 for i in range(n)]
    z = 0.08 + 0.05j
    ref = _taylor_ref(n, edges, weights, u0, z)
    got = L.propagate_sparse(n, edges, weights, u0=u0, z=z)
    err = _err([got[i] for i in range(n)], ref)
    assert err < 1e-9, f"corpus Taylor: {err:.3e}"


# ── (d) the 2π seam-fold consistency at large t·λ ───────────────────────


def test_seam_fold_consistency_at_large_t_lambda():
    """Coherent propagation with t·λ_max ≈ 40: the node evaluations run
    through the seam-folded Wick machinery, so the sparse harvest still
    matches the rc136 eigenbasis one (which is seam-fold-exact there) —
    and stays unitary rather than blowing up."""
    n = 5
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
    weights = [1.0] * 5
    Lm = L.signed_laplacian(n, edges, weights)
    u0 = [1.0, 0.0, 0.0, 0.0, 0.0]
    z = complex(0.0, 10.0)                 # t·λ_max = 10·(2·2) = 40
    dense = L.propagate(Lm, u0, z)
    sparse = L.propagate_sparse(n, edges, weights, u0=u0, z=z)
    err = _err([sparse[i] for i in range(n)], [dense[i] for i in range(n)])
    assert err < 1e-7, f"large t·λ: {err:.3e}"
    assert abs(_norm([sparse[i] for i in range(n)]) - 1.0) < 1e-8


# ── (e) Python == C value parity (native vs forced-pure) ────────────────


def test_python_equals_c_parity():
    tol = 1e-9
    for n, ne, seed in ((7, 12, 5), (24, 60, 6)):
        edges, weights = _rand_graph(n, ne, seed, signed=(seed % 2 == 0))
        u0 = [((i * 7 + 3) % 11) - 5.0 for i in range(n)]
        for z in (0.7 + 0j, 0.9j, 1.1 * cmath.exp(1j * 0.7)):
            native = L.propagate_sparse(n, edges, weights, u0=u0, z=z)
            pure = _force_pure(
                lambda: L.propagate_sparse(n, edges, weights, u0=u0, z=z))
            err = _err([native[i] for i in range(n)],
                       [pure[i] for i in range(n)])
            assert err < tol, f"n={n} z={z}: native vs pure {err:.3e}"


# ── (f) the HONEST non-convergence contract ─────────────────────────────


def test_honest_nonconvergence_raises():
    """A degree cap far below |z|·λ_max/2 CANNOT satisfy the tail tolerance
    → an honest ValueError (both the pure path and the native path, which
    refuses with OVERFLOW and falls through to the pure raise) — never a
    silently degraded tolerance."""
    import pytest
    n = 12
    edges = [(i, (i + 1) % n) for i in range(n)]
    u0 = [1.0] * n
    with pytest.raises(ValueError):
        L.propagate_sparse(n, edges, u0=u0, z=40.0j, max_degree=4)
    with pytest.raises(ValueError):
        _force_pure(lambda: L.propagate_sparse(n, edges, u0=u0, z=40.0j,
                                               max_degree=4))


def test_degree_grows_with_z_but_is_capped():
    """The same call converges once max_degree is raised — the cap is the
    caller's dial, not a silent behavior change."""
    n = 12
    edges = [(i, (i + 1) % n) for i in range(n)]
    weights = [1.0] * n
    u0 = [1.0 if i == 0 else 0.0 for i in range(n)]
    hv = L.propagate_sparse(n, edges, weights, u0=u0, z=40.0j,
                            max_degree=2048)
    # coherent → still unitary at big t
    assert abs(_norm([hv[i] for i in range(n)]) - 1.0) < 1e-7


# ── (g) contracts + read-only + registration ────────────────────────────


def test_contracts():
    import pytest
    with pytest.raises(ValueError):
        L.propagate_sparse(3, [(0, 5)], u0=[1.0, 0.0, 0.0], z=1.0)  # endpoint
    with pytest.raises(ValueError):
        L.propagate_sparse(3, [(0, 1)], u0=[1.0, 0.0], z=1.0)  # u0 mismatch
    with pytest.raises(ValueError):
        L.propagate_sparse(3, [(0, 1)], [1.0, 2.0],
                           u0=[1.0, 0.0, 0.0], z=1.0)  # weights mismatch
    with pytest.raises(ValueError):
        L.propagate_sparse(3, [(0, 1)], u0=[1.0, 0.0, 0.0], z=1.0,
                           tol=0.0)  # tol domain
    with pytest.raises(ValueError):
        L.propagate_sparse(3, [(0, 1)], u0=[1.0, 0.0, 0.0], z=1.0,
                           max_degree=0)  # degree domain
    with pytest.raises(ValueError):
        L.propagate_sparse(3, [(0, 1)], [float("inf")],
                           u0=[1.0, 0.0, 0.0], z=1.0)  # non-finite weight
    hv0 = L.propagate_sparse(0, [], u0=[], z=1.0)  # n = 0
    assert hv0.shape == (0,)
    assert hv0.is_complex


def test_zero_operator_is_identity():
    """No edges (or all-zero weights) → L = 0 → harvest = u0 exactly."""
    u0 = [1.0, -2.0, 3.0]
    hv = L.propagate_sparse(3, [], u0=u0, z=0.8 + 0.6j)
    assert _err([hv[i] for i in range(3)], [complex(x) for x in u0]) == 0.0
    hv2 = L.propagate_sparse(3, [(0, 1)], [0.0], u0=u0, z=0.8 + 0.6j)
    assert _err([hv2[i] for i in range(3)], [complex(x) for x in u0]) == 0.0


def test_inputs_unmutated():
    n = 6
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
    weights = [1.0, 2.0, -1.0, 0.5, 1.5]
    u0 = [1.0, 0.5, -0.5, 1.0, 0.0, 2.0]
    e_snap = [tuple(e) for e in edges]
    w_snap = weights[:]
    u_snap = u0[:]
    L.propagate_sparse(n, edges, weights, u0=u0, z=0.7 + 0.3j)
    assert edges == e_snap, "edges mutated"
    assert weights == w_snap, "weights mutated"
    assert u0 == u_snap, "u0 mutated"


def test_registration_and_count():
    import srmech
    from srmech.amsc.tool_schema import get_tool_schema
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.propagate_sparse" in names
    assert len(get_tool_schema().tools) == 450
    assert srmech.describe()["tools"]["total"] == 450
    assert "propagate_sparse" in L.LAPLACIAN_OPS
    assert "propagate_sparse" in L.__all__
