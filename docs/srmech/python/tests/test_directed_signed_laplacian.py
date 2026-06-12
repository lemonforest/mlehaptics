"""#797 op (b) — directed/signed-Laplacian eigen-op (Class L).

v0.7.0rc26. The undirected combinatorial Laplacian is the F348 navigation
control (Fiedler shuffle-fragile r=0.214); these two generalisations add
the directed-navigation + signed-metric legs the research (F347–F354)
spec'd:

* ``signed_laplacian`` — real-symmetric, PSD even with negative (frustrated)
  edges (the dissolved "Class O" signed-metric, now a Class-L sub-op);
* ``magnetic_laplacian`` — complex Hermitian; direction encoded as phase so
  the existing ``hermitian_eigendecompose`` diagonalises it. ``q=0``
  collapses to the real symmetrised Laplacian (the undirected control).

Post-#564 numpy is GONE from srmech: the builders return plain Python lists
(``list[list[float]]`` / ``list[list[complex]]``) and the eigen-checks ride
srmech's OWN cascades (``jacobi_eigvals`` for real-symmetric, the Hermitian
eigendecompose for the magnetic Laplacian) — never numpy LAPACK.
"""
import pytest

from srmech.amsc import laplacian as L


# ── plain-list matrix helpers (no numpy) ────────────────────────────────


def _is_symmetric(M, tol=1e-12):
    n = len(M)
    return all(abs(M[i][j] - M[j][i]) <= tol for i in range(n) for j in range(n))


def _is_hermitian(M, tol=1e-12):
    n = len(M)
    return all(
        abs(M[i][j] - M[j][i].conjugate()) <= tol
        for i in range(n)
        for j in range(n)
    )


def _max_abs_imag(M):
    out = 0.0
    for row in M:
        for v in row:
            iv = v.imag if isinstance(v, complex) else 0.0
            out = iv if iv > out else (-iv if -iv > out else out)
    return out


def _all_real_entries(M):
    return all(
        (not isinstance(v, complex)) or v.imag == 0.0
        for row in M for v in row
    )


# ── signed Laplacian ───────────────────────────────────────────────────


def test_signed_laplacian_is_real_symmetric():
    Ls = L.signed_laplacian(3, [(0, 1), (1, 2), (0, 2)], [1.0, 1.0, -1.0])
    assert _all_real_entries(Ls)
    assert _is_symmetric(Ls)


def test_signed_laplacian_psd_with_frustrated_edge():
    """A negative (frustrated) edge stays PSD — the signed-Laplacian point."""
    Ls = L.signed_laplacian(3, [(0, 1), (1, 2), (0, 2)], [1.0, 1.0, -1.0])
    ev = L.jacobi_eigvals(Ls)   # srmech's own Jacobi cascade, no numpy
    assert min(ev) >= -1e-9


def test_signed_laplacian_all_positive_matches_dense_laplacian():
    """With all-positive weights the signed Laplacian == the plain one."""
    edges, w = [(0, 1), (1, 2), (0, 2)], [2.0, 3.0, 1.5]
    Ls = L.signed_laplacian(3, edges, w)
    Ld = L.dense_laplacian(3, edges, w)
    n = len(Ld)
    for i in range(n):
        for j in range(n):
            assert abs(Ls[i][j] - Ld[i][j]) < 1e-12


def test_signed_degree_uses_magnitude_not_signed_sum():
    """Signed degree D̄_ii = Σ|w| (Class-K magnitude), not Σw."""
    # node 0 has edges of weight +1 and -1 → |.|-sum = 2, signed-sum = 0.
    Ls = L.signed_laplacian(3, [(0, 1), (0, 2)], [1.0, -1.0])
    assert Ls[0][0] == pytest.approx(2.0)


# ── magnetic (directed) Laplacian ──────────────────────────────────────


def test_magnetic_laplacian_is_hermitian():
    Lm = L.magnetic_laplacian(3, [(0, 1), (1, 2), (2, 0)], q=0.25)
    # complex entries present
    assert any(isinstance(v, complex) for row in Lm for v in row)
    assert _is_hermitian(Lm)


def test_magnetic_q0_is_real_symmetric_control():
    """q=0 collapses to the real symmetrised Laplacian (F348 control)."""
    edges = [(0, 1), (1, 2), (2, 0)]
    Lm0 = L.magnetic_laplacian(3, edges, q=0.0)
    assert _max_abs_imag(Lm0) < 1e-12       # imaginary part vanishes
    # real part is symmetric
    real_part = [[v.real if isinstance(v, complex) else v for v in row] for row in Lm0]
    assert _is_symmetric(real_part)


def test_magnetic_directed_has_imaginary_part():
    """A genuinely directed graph with q>0 carries phase (complex)."""
    Lm = L.magnetic_laplacian(3, [(0, 1), (1, 2), (2, 0)], q=0.25)
    assert _max_abs_imag(Lm) > 1e-6


def test_magnetic_laplacian_real_psd_spectrum():
    """Hermitian ⇒ real eigenvalues; magnetic Laplacian is PSD."""
    Lm = L.magnetic_laplacian(3, [(0, 1), (1, 2), (2, 0)], q=0.25)
    ev, _ = L.hermitian_eigendecompose(Lm)   # Hermitian cascade → real eigvals
    # eigvals are returned as real floats (ascending)
    assert all(not isinstance(e, complex) for e in ev)
    assert min(ev) >= -1e-9


def test_magnetic_rejects_nonreal_q():
    with pytest.raises(TypeError):
        L.magnetic_laplacian(2, [(0, 1)], q=1j)


# ── fiedler navigation embedding ───────────────────────────────────────


def test_fiedler_vector_real_and_complex():
    edges = [(0, 1), (1, 2), (0, 2)]
    fv_r = L.fiedler_vector(L.dense_laplacian(3, edges))
    assert len(fv_r) == 3
    assert all(not isinstance(v, complex) for v in fv_r)
    fv_c = L.fiedler_vector(L.magnetic_laplacian(3, edges, q=0.25))
    assert len(fv_c) == 3
    # magnetic Laplacian is complex Hermitian → its Fiedler vector is complex
    assert any(isinstance(v, complex) for v in fv_c)


def test_fiedler_vector_needs_two_nodes():
    with pytest.raises(ValueError):
        L.fiedler_vector([[0.0]])


# ── registry ───────────────────────────────────────────────────────────


def test_new_ops_in_laplacian_registry():
    for name in ("signed_laplacian", "magnetic_laplacian", "fiedler_vector"):
        assert name in L.LAPLACIAN_OPS
