"""#797 op (b) — directed/signed-Laplacian eigen-op (Class L).

v0.7.0rc26. The undirected combinatorial Laplacian is the F348 navigation
control (Fiedler shuffle-fragile r=0.214); these two generalisations add
the directed-navigation + signed-metric legs the research (F347–F354)
spec'd:

* ``signed_laplacian`` — real-symmetric, PSD even with negative (frustrated)
  edges (the dissolved "Class O" signed-metric, now a Class-L sub-op);
* ``magnetic_laplacian`` — complex Hermitian; direction encoded as phase so
  the existing C-backed ``hermitian_eigendecompose`` diagonalises it. ``q=0``
  collapses to the real symmetrised Laplacian (the undirected control).

The heavy eigendecomposition runs on the existing native solvers; these
tests pin the builder math + the Hermitian/PSD contracts.
"""
import numpy as np
import pytest

from srmech.amsc import laplacian as L


# ── signed Laplacian ───────────────────────────────────────────────────


def test_signed_laplacian_is_real_symmetric():
    Ls = L.signed_laplacian(3, [(0, 1), (1, 2), (0, 2)], [1.0, 1.0, -1.0])
    assert Ls.dtype == np.float64
    assert np.allclose(Ls, Ls.T)


def test_signed_laplacian_psd_with_frustrated_edge():
    """A negative (frustrated) edge stays PSD — the signed-Laplacian point."""
    Ls = L.signed_laplacian(3, [(0, 1), (1, 2), (0, 2)], [1.0, 1.0, -1.0])
    ev = np.linalg.eigvalsh(Ls)
    assert ev.min() >= -1e-9


def test_signed_laplacian_all_positive_matches_dense_laplacian():
    """With all-positive weights the signed Laplacian == the plain one."""
    edges, w = [(0, 1), (1, 2), (0, 2)], [2.0, 3.0, 1.5]
    assert np.allclose(
        L.signed_laplacian(3, edges, w), L.dense_laplacian(3, edges, w)
    )


def test_signed_degree_uses_magnitude_not_signed_sum():
    """Signed degree D̄_ii = Σ|w| (Class-K magnitude), not Σw."""
    # node 0 has edges of weight +1 and -1 → |.|-sum = 2, signed-sum = 0.
    Ls = L.signed_laplacian(3, [(0, 1), (0, 2)], [1.0, -1.0])
    assert Ls[0, 0] == pytest.approx(2.0)


# ── magnetic (directed) Laplacian ──────────────────────────────────────


def test_magnetic_laplacian_is_hermitian():
    Lm = L.magnetic_laplacian(3, [(0, 1), (1, 2), (2, 0)], q=0.25)
    assert Lm.dtype == np.complex128
    assert np.allclose(Lm, Lm.conj().T)


def test_magnetic_q0_is_real_symmetric_control():
    """q=0 collapses to the real symmetrised Laplacian (F348 control)."""
    edges = [(0, 1), (1, 2), (2, 0)]
    Lm0 = L.magnetic_laplacian(3, edges, q=0.0)
    assert np.allclose(Lm0.imag, 0.0)
    assert np.allclose(Lm0, Lm0.real.T)


def test_magnetic_directed_has_imaginary_part():
    """A genuinely directed graph with q>0 carries phase (complex)."""
    Lm = L.magnetic_laplacian(3, [(0, 1), (1, 2), (2, 0)], q=0.25)
    assert not np.allclose(Lm.imag, 0.0)


def test_magnetic_laplacian_real_psd_spectrum():
    """Hermitian ⇒ real eigenvalues; magnetic Laplacian is PSD."""
    Lm = L.magnetic_laplacian(3, [(0, 1), (1, 2), (2, 0)], q=0.25)
    ev = np.linalg.eigvalsh(Lm)
    assert np.allclose(ev.imag, 0.0)
    assert ev.min() >= -1e-9


def test_magnetic_rejects_nonreal_q():
    with pytest.raises(TypeError):
        L.magnetic_laplacian(2, [(0, 1)], q=1j)


# ── fiedler navigation embedding ───────────────────────────────────────


def test_fiedler_vector_real_and_complex():
    edges = [(0, 1), (1, 2), (0, 2)]
    fv_r = L.fiedler_vector(L.dense_laplacian(3, edges))
    assert fv_r.shape == (3,) and fv_r.dtype == np.float64
    fv_c = L.fiedler_vector(L.magnetic_laplacian(3, edges, q=0.25))
    assert fv_c.shape == (3,) and fv_c.dtype == np.complex128


def test_fiedler_vector_needs_two_nodes():
    with pytest.raises(ValueError):
        L.fiedler_vector(np.zeros((1, 1)))


# ── registry ───────────────────────────────────────────────────────────


def test_new_ops_in_laplacian_registry():
    for name in ("signed_laplacian", "magnetic_laplacian", "fiedler_vector"):
        assert name in L.LAPLACIAN_OPS
