"""Canonical bound-state potentials: hydrogen radial + harmonic oscillator (numpy-free).

Per ``[[feedback_science_is_ssot_not_project]]``: textbook sources for
both; chess-spectral / ephemerides-spectral are downstream consumers.

numpy-FREE (v0.7.5rc121, #564): the discretized radial Hamiltonian and the
harmonic-oscillator ladder/Hamiltonian are held in the framework-native
:class:`~srmech.amsc.mat.Mat` carrier. ``hydrogen_radial`` builds its
real-symmetric tridiagonal Hamiltonian as a ``Mat`` and eigensolves it
through the Class-L :func:`~srmech.amsc.laplacian.mat_hermitian_eigendecompose`
(native dense Jacobi, ``n`` up to 2048 as of rc120; pure-Python cascade
fallback) — the radial grid ``r`` and the eigen-energies are plain Python
lists, and since the Hamiltonian is real-symmetric the eigenvectors are
returned as a **real** ``Mat`` (the value-preserving real part of the complex
unitary). The ladder operator ``√n`` entries use the Class-N libm-free
:func:`srmech.amsc.rational.sqrt`, and the oscillator Hamiltonian
``H = ω(a†a + ½I)`` is assembled through the Class-L
:func:`~srmech.amsc.laplacian.mat_matmul` — **no numpy**.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: these
operations couple the LoE-content to specific potential-shape substrates
(Coulomb for hydrogen, quadratic for the oscillator). Each potential
dissolves into Class L (eigendecomp of the discretized Hamiltonian) or
Class M (binding of ladder-operator states).
"""

from __future__ import annotations

from typing import List, Tuple

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import mat_hermitian_eigendecompose, mat_matmul
from srmech.amsc.mat import Mat


# ----------------------------------------------------------------------
# numpy-free Mat helpers
# ----------------------------------------------------------------------


def _scale(s, m: "Mat") -> "Mat":
    """``s · M`` (scalar × ``Mat``) as a new complex ``Mat`` (numpy-free)."""
    rows = [[s * m[i, j] for j in range(m.n_cols)] for i in range(m.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


def _mat_add(a: "Mat", b: "Mat") -> "Mat":
    """``A + B`` element-wise as a new complex ``Mat`` (numpy-free)."""
    rows = [[a[i, j] + b[i, j] for j in range(a.n_cols)] for i in range(a.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


def _eye(n: int) -> "Mat":
    """The ``n × n`` complex identity as a ``Mat`` (numpy-free)."""
    return Mat.from_rows(
        [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)],
        is_complex=True,
    )


def hydrogen_radial(
    n_grid: int = 400,
    r_max: float = 80.0,
    l_quantum: int = 0,
) -> Tuple[List[float], List[float], "Mat"]:
    """Hydrogen-atom radial Schrödinger equation eigenstates.

    Discretizes the radial equation for ``u(r) = r R(r)``::

        (-1/2) d²u/dr² + (l(l+1)/(2 r²) - 1/r) u = E u

    on a uniform 1D grid with the 3-point central-difference Laplacian
    and Dirichlet boundaries (u(0) = u(r_max) = 0). The lowest eigenvalues
    approach the Rydberg series ``E_n = -1/(2 n²)`` (in atomic units,
    ``ℏ = m_e = e²/(4πε₀) = 1``).

    Canonical SSoT: Bohr (1913) *Philosophical Magazine* 26, 476;
    Schrödinger (1926); Sakurai *Modern QM* §3.7; Griffiths *Intro QM*
    §4.2 eq 4.53.

    Args:
        n_grid: Number of interior radial grid points (Dirichlet BC).
        r_max: Maximum radial coordinate in Bohr radii.
        l_quantum: Orbital angular momentum quantum number ``l ≥ 0``.

    Returns:
        ``(r, energies, eigenvectors)``: ``r`` the radial grid as a length-
        ``n_grid`` list of float, ``energies`` the eigenvalues ascending as a
        length-``n_grid`` list of float, and ``eigenvectors`` the column-stacked
        eigenvectors as a **real** ``(n_grid, n_grid)`` ``Mat`` (the Hamiltonian
        is real-symmetric, so the eigenvectors are real). For the 1s state:
        ``energies[0] ≈ -0.5`` (Rydberg); finite-grid corrections are O(dr²).
    """
    if n_grid < 4:
        raise ValueError(f"hydrogen_radial: n_grid must be ≥ 4; got {n_grid}")
    if r_max <= 0:
        raise ValueError(f"hydrogen_radial: r_max must be positive; got {r_max}")
    if l_quantum < 0:
        raise ValueError(
            f"hydrogen_radial: l_quantum must be ≥ 0; got {l_quantum}"
        )
    dr = r_max / (n_grid + 1)
    # The radial grid as a plain Python list (numpy-free; Class-N exact arithmetic
    # on the uniform spacing — no np.arange).
    r = [(i + 1) * dr for i in range(n_grid)]
    inv_2dr2 = 1.0 / (2.0 * dr * dr)
    lcent = l_quantum * (l_quantum + 1)
    # Build the real-symmetric tridiagonal Hamiltonian as a nested list, then a
    # COMPLEX Mat so it feeds mat_hermitian_eigendecompose. Diagonal:
    #   2·inv_2dr2 + l(l+1)/(2 r_i²) − 1/r_i ; off-diagonals −inv_2dr2 on k=±1.
    rows = [[0.0] * n_grid for _ in range(n_grid)]
    for i in range(n_grid):
        ri = r[i]
        rows[i][i] = 2.0 * inv_2dr2 + lcent / (2.0 * ri * ri) - 1.0 / ri
        if i + 1 < n_grid:
            rows[i][i + 1] = -inv_2dr2
            rows[i + 1][i] = -inv_2dr2
    H = Mat.from_rows(rows, is_complex=True)
    # Class-L Hermitian eigendecomposition (srmech's own primitive). H here is
    # real-symmetric, so the eigenvectors are real; the cascade carries them in a
    # complex container — take the value-preserving real part (mathematically
    # exact for real-symmetric input) and return them as a real Mat.
    eigvals_mat, eigvecs_mat = mat_hermitian_eigendecompose(H)
    n = eigvecs_mat.n_rows
    eigenvectors = Mat.from_rows(
        [[eigvecs_mat[i, j].real for j in range(n)] for i in range(n)],
        is_complex=False,
    )
    energies = [eigvals_mat[k, 0] for k in range(n_grid)]
    return r, energies, eigenvectors


def harmonic_oscillator_ladder(
    n_dim: int = 30, omega: float = 1.0
) -> Tuple["Mat", "Mat"]:
    """Harmonic-oscillator ladder operators ``(a, a†)`` truncated at n_dim.

    Satisfies ``a |n⟩ = √n |n-1⟩``, ``a† |n⟩ = √(n+1) |n+1⟩``, and the
    canonical commutation relation ``[a, a†] = I`` (up to the truncation
    boundary; deviation is O(n_dim⁻¹) at large indices).

    Per Spike #24 / ``[[user_stance_kepler_shape_universal]]``-adjacent:
    a, a† are Class M (HDC binding) primitives for Fock-space states.

    Canonical SSoT: Heisenberg (1925) *Zeitschrift für Physik* 33, 879;
    Born, Heisenberg & Jordan (1926) *Zeitschrift für Physik* 35, 557;
    Sakurai *Modern QM* §2.3 eq 2.3.18-19; Cohen-Tannoudji §V.B.

    Args:
        n_dim: Truncation dimension of the Fock space (n_dim ≥ 2).
        omega: Angular frequency (used only by the Hamiltonian builder).

    Returns:
        ``(a, a_dagger)``: lowering and raising operators, complex
        ``(n_dim, n_dim)`` ``Mat``.
    """
    if n_dim < 2:
        raise ValueError(f"harmonic_oscillator_ladder: n_dim must be ≥ 2; got {n_dim}")
    if omega <= 0:
        raise ValueError(f"harmonic_oscillator_ladder: omega must be positive; got {omega}")
    # Lowering operator a[n-1, n] = √n (Class-N libm-free rational.sqrt); zeros
    # elsewhere. Built as a complex Mat; a† is its conjugate transpose.
    rows = [[0j] * n_dim for _ in range(n_dim)]
    for n in range(1, n_dim):
        rows[n - 1][n] = _srn.sqrt(float(n))
    a = Mat.from_rows(rows, is_complex=True)
    a_dagger = a.conj().T
    return a, a_dagger


def harmonic_oscillator_hamiltonian(
    n_dim: int = 30, omega: float = 1.0
) -> "Mat":
    """Harmonic-oscillator Hamiltonian ``H = ℏω (a† a + 1/2)``.

    Eigenvalues (exact at infinite truncation): ``E_n = ℏω (n + 1/2)`` for
    ``n = 0, 1, 2, …``. With ℏ = 1 the spectrum is ``ω (n + 1/2)``.

    Canonical SSoT: same as ``harmonic_oscillator_ladder``;
    Sakurai *Modern QM* §2.3 eq 2.3.16.

    Args:
        n_dim: Truncation dimension.
        omega: Angular frequency.

    Returns:
        Hermitian ``(n_dim, n_dim)`` Hamiltonian as a complex ``Mat``.
    """
    a, a_dagger = harmonic_oscillator_ladder(n_dim, omega)
    # H = ω·(a†·a + ½·I) — Class-L matmul cascade + numpy-free Mat add/scale.
    return _scale(omega, _mat_add(mat_matmul(a_dagger, a), _scale(0.5, _eye(n_dim))))


__all__ = [
    "harmonic_oscillator_hamiltonian",
    "harmonic_oscillator_ladder",
    "hydrogen_radial",
]
