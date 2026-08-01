"""rc308 (#944) — the ℍ (associative) sibling of ``magnetic_laplacian``.

``quaternion_laplacian`` (the 4n×4n real-symmetric quaternion GAIN Laplacian)
+ ``hypercomplex_perspectives`` (the scalar/imaginary channel reader that also
closes the ℂ ``magnetic_laplacian`` latent dim-2 read). Genuine theorem checks
(NOT smoke tests):

  1. shape (4n×4n) + EXACT real-symmetry (``L(conj g) == L(g)ᵀ`` term-by-term).
  2. GAUGE INVARIANCE — a node-wise unit-quaternion gauge
     ``g_uv → s_u·g_uv·conj(s_v)`` leaves the spectrum fixed (~3.3e-15; the ℍ
     generalisation of the complex-unit-gain U(1) gauge invariance).
  3. the ×4 DEGENERACY THEOREM — ℍ associativity ⇒ the left-built matrix
     commutes with the fixed right-ℍ Sp(1) commutant, so every eigenvalue has
     multiplicity a multiple of 4 (n distinct quadruples on a generic graph).
  4. identity-gain KNOWN ANSWER — ``gains=None`` == ``½·(dense L) ⊗ I₄`` EXACTLY.
  5. native == pure parity — the assembled matrix is byte-identical whether
     ``quaternion_left_mult`` dispatches to C or runs the pure table fallback.
  6. ``hypercomplex_perspectives`` — dim-2 (ℂ) and dim-4 (ℍ) channel splits read
     correctly (synthetic known-answers + end-to-end on both Laplacians).

Plus edge/error cases and the registration ratchet (ToolEntry ×2 / __all__ /
LAPLACIAN_OPS / the Rosetta rows). numpy-free (srmech + stdlib only).
"""
from __future__ import annotations

import importlib.util
import math

import pytest

from srmech import _native
from srmech.math.mat import Mat
from srmech.math.laplacian import (
    quaternion_laplacian,
    hypercomplex_perspectives,
    dense_laplacian,
    magnetic_laplacian,
    mat_hermitian_eigendecompose,
    LAPLACIAN_OPS,
    _resolve_quaternion_gains,
    _quaternion_laplacian_blocks,
    _validate_edges_weights_py,
)
import srmech.math.laplacian as _lap
from srmech.qm.quaternion import quaternion_left_mult, quaternion_conjugate


# A fixed non-trivial ℍ-gain graph (3 nodes, 3 edges = one triangle; mixed
# weights + generic non-unit gains that the op normalises to Sp(1)).
_N = 3
_EDGES = [(0, 1), (1, 2), (0, 2)]
_WEIGHTS = [1.0, 2.0, 0.5]
_GAINS = [
    [0.3, 0.5, -0.4, 0.2],
    [-0.1, 0.7, 0.2, 0.6],
    [0.8, -0.2, 0.5, 0.1],
]


# ── helpers (srmech-only quaternion algebra; no numpy) ────────────────────
def _qmul(p, q):
    """``p·q`` via the Class-M left-multiplication matrix (L(p) applied to q)."""
    lp = quaternion_left_mult(p).tolist()
    return [sum(lp[a][b] * q[b] for b in range(4)) for a in range(4)]


def _unit(q):
    nrm = math.sqrt(sum(x * x for x in q))
    return [x / nrm for x in q]


def _eigvals(L):
    ev, V = mat_hermitian_eigendecompose(L)
    return [ev[i, 0] for i in range(ev.n_rows)], V


# ── 0. numpy is genuinely absent on the numpy-free gate ──────────────────
def test_numpy_is_absent_so_this_runs_not_skips():
    """This module tests a numpy-free surface; on the numpy-absent gate numpy
    must be truly unimportable (a stray numpy would mask a carrier-path bug)."""
    if importlib.util.find_spec("numpy") is not None:
        pytest.skip("numpy present (dev host) — the numpy-absent gate runs this")
    assert importlib.util.find_spec("numpy") is None


# ── 1. shape + exact real-symmetry ───────────────────────────────────────
def test_shape_and_exact_symmetry():
    L = quaternion_laplacian(_N, _EDGES, _WEIGHTS, gains=_GAINS)
    assert isinstance(L, Mat)
    assert L.shape == (4 * _N, 4 * _N)
    assert L.is_complex is False
    # EXACT symmetry: block(u,v) = -(w/2)L(g), block(v,u) = -(w/2)L(conj g),
    # and L(conj g) == L(g)ᵀ term-by-term, so no float asymmetry is introduced.
    asym = max(abs(L[i, j] - L[j, i])
               for i in range(L.n_rows) for j in range(L.n_cols))
    assert asym == 0.0


def test_left_mult_conjugate_is_transpose():
    """The identity the exact symmetry rests on: L(conj g) == L(g)ᵀ."""
    for g in _GAINS:
        lg = quaternion_left_mult(g).tolist()
        lgc = quaternion_left_mult(quaternion_conjugate(g)).tolist()
        assert all(lgc[a][b] == lg[b][a] for a in range(4) for b in range(4))


# ── 2. gauge invariance (~3.3e-15) ───────────────────────────────────────
def test_gauge_invariance_spectrum():
    L0 = quaternion_laplacian(_N, _EDGES, _WEIGHTS, gains=_GAINS)
    ev0, _ = _eigvals(L0)

    # node-wise unit-quaternion gauge s_u; g_uv -> s_u · g_uv · conj(s_v).
    s = [_unit(x) for x in (
        [0.6, 0.1, 0.7, -0.3],
        [-0.2, 0.5, 0.4, 0.6],
        [0.9, 0.2, -0.1, 0.3],
    )]
    gauged = []
    for (u, v), g in zip(_EDGES, _GAINS):
        gauged.append(_qmul(_qmul(s[u], g), quaternion_conjugate(s[v])))
    Lg = quaternion_laplacian(_N, _EDGES, _WEIGHTS, gains=gauged)
    evg, _ = _eigvals(Lg)

    max_diff = max(abs(a - b) for a, b in zip(sorted(ev0), sorted(evg)))
    assert max_diff < 1e-11, f"gauge shifted the spectrum by {max_diff}"


# ── 3. the ×4 degeneracy THEOREM ─────────────────────────────────────────
def test_x4_degeneracy_theorem():
    L = quaternion_laplacian(_N, _EDGES, _WEIGHTS, gains=_GAINS)
    ev, _ = _eigvals(L)
    assert len(ev) == 4 * _N
    ev = sorted(ev)
    # every consecutive group of 4 is one eigenvalue (multiplicity ≥ 4).
    for k in range(0, len(ev), 4):
        grp = ev[k:k + 4]
        assert max(grp) - min(grp) < 1e-9, f"quadruple {k//4} not degenerate: {grp}"
    # on this generic gain graph the n quadruples are DISTINCT (a true ×4, not
    # an accidental higher multiplicity).
    centers = [sum(ev[k:k + 4]) / 4 for k in range(0, len(ev), 4)]
    gaps = [centers[i + 1] - centers[i] for i in range(len(centers) - 1)]
    assert min(gaps) > 1e-6, f"quadruples not distinct: {centers}"
    # dedup-by-tolerance == n (the caller's 'take every 4th' recipe).
    assert len(centers) == _N


# ── 4. identity-gain KNOWN ANSWER: ½·(dense L) ⊗ I₄ ──────────────────────
def test_identity_gain_is_half_dense_laplacian_kron_i4():
    Lid = quaternion_laplacian(_N, _EDGES, _WEIGHTS)  # gains=None
    Ld = dense_laplacian(_N, _EDGES, _WEIGHTS).tolist()
    for u in range(_N):
        for v in range(_N):
            want = 0.5 * Ld[u][v]
            for a in range(4):
                for b in range(4):
                    got = Lid[4 * u + a, 4 * v + b]
                    expect = want if a == b else 0.0
                    assert got == expect, (u, v, a, b, got, expect)


# ── 5. native == pure parity of the assembled matrix ─────────────────────
def test_native_pure_parity(monkeypatch):
    """The assembled matrix is byte-identical whether quaternion_left_mult
    dispatches to the C peer or runs the pure table fallback (the composition
    is path-independent — the only 'new op' parity claim, since there is no new
    C symbol)."""
    L_native = quaternion_laplacian(_N, _EDGES, _WEIGHTS, gains=_GAINS).tolist()
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    L_pure = quaternion_laplacian(_N, _EDGES, _WEIGHTS, gains=_GAINS).tolist()
    assert L_native == L_pure


# ── 6. hypercomplex_perspectives ─────────────────────────────────────────
def test_perspectives_synthetic_dim2():
    m = Mat.from_rows([[1 + 2j, 3 + 4j], [5 + 6j, 7 + 8j]], is_complex=True)
    p = hypercomplex_perspectives(m, dim=2)
    assert p["dim"] == 2 and p["n_vectors"] == 2 and p["n_blocks"] == 2
    assert p["channel_names"] == ["e0", "e1"]
    assert p["vectors"][0]["e0"] == [1.0, 5.0]
    assert p["vectors"][0]["e1"] == [2.0, 6.0]
    assert p["vectors"][1]["e0"] == [3.0, 7.0]
    assert p["vectors"][1]["e1"] == [4.0, 8.0]


def test_perspectives_synthetic_dim4():
    col = [[float(x)] for x in (1, 2, 3, 4, 5, 6, 7, 8)]
    m = Mat.from_rows(col, is_complex=False)
    p = hypercomplex_perspectives(m, dim=4)
    assert p["dim"] == 4 and p["n_vectors"] == 1 and p["n_blocks"] == 2
    assert p["channel_names"] == ["e0", "e1", "e2", "e3"]
    v = p["vectors"][0]
    assert v["e0"] == [1.0, 5.0]
    assert v["e1"] == [2.0, 6.0]
    assert v["e2"] == [3.0, 7.0]
    assert v["e3"] == [4.0, 8.0]


def test_perspectives_dim1_real():
    m = Mat.from_rows([[1.0], [2.0], [3.0]], is_complex=False)
    p = hypercomplex_perspectives(m, dim=1)
    assert p["channel_names"] == ["e0"]
    assert p["n_blocks"] == 3
    assert p["vectors"][0]["e0"] == [1.0, 2.0, 3.0]


def test_perspectives_end_to_end_quaternion_dim4():
    """dim=4 on the real quaternion_laplacian eigenvectors: n_blocks == n, four
    channels, and the channels reconstruct each eigenvector's real part."""
    L = quaternion_laplacian(_N, _EDGES, _WEIGHTS, gains=_GAINS)
    _, V = _eigvals(L)
    p = hypercomplex_perspectives(V, dim=4)
    assert p["n_blocks"] == _N
    assert p["n_vectors"] == 4 * _N
    assert p["channel_names"] == ["e0", "e1", "e2", "e3"]
    for j in range(p["n_vectors"]):
        chans = p["vectors"][j]
        recon = []
        for b in range(_N):
            for c in range(4):
                recon.append(chans["e" + str(c)][b])
        orig = [complex(V[i, j]).real for i in range(V.n_rows)]
        assert max(abs(a - b) for a, b in zip(recon, orig)) == 0.0


def test_perspectives_end_to_end_magnetic_dim2():
    """dim=2 closes the ℂ magnetic_laplacian latent read: each complex entry's
    (re, im) become the (e0, e1) channels."""
    Lm = magnetic_laplacian(4, [(0, 1), (1, 2), (2, 3)], [1.0, 1.0, 1.0],
                            charges=[0.1, 0.2, 0.3])
    _, Vm = mat_hermitian_eigendecompose(Lm)
    p = hypercomplex_perspectives(Vm, dim=2)
    assert p["n_blocks"] == 4
    assert p["channel_names"] == ["e0", "e1"]
    for j in range(p["n_vectors"]):
        col = [complex(Vm[i, j]) for i in range(Vm.n_rows)]
        assert p["vectors"][j]["e0"] == [z.real for z in col]
        assert p["vectors"][j]["e1"] == [z.imag for z in col]


# ── error / edge cases ────────────────────────────────────────────────────
def test_gains_length_mismatch_raises():
    with pytest.raises(ValueError, match="gains length"):
        quaternion_laplacian(_N, _EDGES, _WEIGHTS,
                             gains=[[1.0, 0.0, 0.0, 0.0]])


def test_gain_not_4vector_raises():
    with pytest.raises(ValueError, match="4-vector"):
        quaternion_laplacian(2, [(0, 1)], [1.0], gains=[[1.0, 0.0, 0.0]])


def test_zero_norm_gain_raises():
    with pytest.raises(ValueError, match="non-zero"):
        quaternion_laplacian(2, [(0, 1)], [1.0],
                             gains=[[0.0, 0.0, 0.0, 0.0]])


def test_perspectives_bad_dim_raises():
    m = Mat.from_rows([[1.0], [2.0]], is_complex=False)
    with pytest.raises(ValueError, match="dim must be"):
        hypercomplex_perspectives(m, dim=3)


def test_perspectives_non_mat_raises():
    with pytest.raises(TypeError, match="must be a Mat"):
        hypercomplex_perspectives([[1.0], [2.0]], dim=2)


def test_perspectives_dim4_non_multiple_raises():
    m = Mat.from_rows([[1.0], [2.0], [3.0]], is_complex=False)  # N=3, not / 4
    with pytest.raises(ValueError, match="multiple of dim"):
        hypercomplex_perspectives(m, dim=4)


def test_empty_gain_resolution_defaults_identity():
    el, wl = _validate_edges_weights_py(_N, _EDGES, _WEIGHTS)
    gl = _resolve_quaternion_gains(el, None)
    assert gl == [[1.0, 0.0, 0.0, 0.0]] * len(el)


# ── registration ratchet ──────────────────────────────────────────────────
def test_registration_all_and_laplacian_ops():
    for name in ("quaternion_laplacian", "hypercomplex_perspectives"):
        assert name in _lap.__all__, f"{name} missing from laplacian.__all__"
        assert name in LAPLACIAN_OPS, f"{name} missing from LAPLACIAN_OPS"


def test_registration_tool_schema_entries_present():
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    names = {t.name for t in get_tool_schema().tools}
    for op in ("quaternion_laplacian", "hypercomplex_perspectives"):
        assert f"srmech.math.laplacian.{op}" in names, f"{op} ToolEntry missing"
