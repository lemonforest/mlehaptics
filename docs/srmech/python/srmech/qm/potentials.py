"""Canonical bound-state potentials: hydrogen radial + harmonic oscillator.

Per ``[[feedback_science_is_ssot_not_project]]``: textbook sources for
both; chess-spectral / ephemerides-spectral are downstream consumers.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: these
operations couple the LoE-content to specific potential-shape substrates
(Coulomb for hydrogen, quadratic for the oscillator). Each potential
dissolves into Class L (eigendecomp of the discretized Hamiltonian) or
Class M (binding of ladder-operator states).
"""

from __future__ import annotations

import numpy as np
from typing import Tuple

from srmech.amsc.laplacian import dense_matmul_complex, hermitian_eigendecompose


def hydrogen_radial(
    n_grid: int = 400,
    r_max: float = 80.0,
    l_quantum: int = 0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
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
        ``(r, energies, eigenvectors)``: radial grid (n_grid,), eigenvalues
        ascending (n_grid,), eigenvectors column-stacked (n_grid, n_grid).
        For 1s state: ``energies[0] ≈ -0.5`` (Rydberg) at default grid;
        finite-grid corrections are O(dr²).
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
    r = (np.arange(1, n_grid + 1)) * dr
    inv_2dr2 = 1.0 / (2.0 * dr * dr)
    diag = 2.0 * inv_2dr2 + l_quantum * (l_quantum + 1) / (2.0 * r * r) - 1.0 / r
    H = np.diag(diag)
    off = -inv_2dr2 * np.ones(n_grid - 1)
    H += np.diag(off, k=1) + np.diag(off, k=-1)
    # Class-L Hermitian eigendecomposition (srmech's own primitive).
    # H here is real-symmetric, so the eigenvectors are real; the cascade
    # carries them in a complex128 container — take the value-preserving
    # real part (mathematically exact for real-symmetric input).
    eigvals, eigvecs = hermitian_eigendecompose(H)
    eigvecs = np.asarray(eigvecs).real
    return r, eigvals, eigvecs


def harmonic_oscillator_ladder(
    n_dim: int = 30, omega: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
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
        ``(n_dim, n_dim)`` matrices.
    """
    if n_dim < 2:
        raise ValueError(f"harmonic_oscillator_ladder: n_dim must be ≥ 2; got {n_dim}")
    if omega <= 0:
        raise ValueError(f"harmonic_oscillator_ladder: omega must be positive; got {omega}")
    a = np.zeros((n_dim, n_dim), dtype=complex)
    for n in range(1, n_dim):
        a[n - 1, n] = np.sqrt(n)
    a_dagger = a.conj().T.copy()
    return a, a_dagger


def harmonic_oscillator_hamiltonian(
    n_dim: int = 30, omega: float = 1.0
) -> np.ndarray:
    """Harmonic-oscillator Hamiltonian ``H = ℏω (a† a + 1/2)``.

    Eigenvalues (exact at infinite truncation): ``E_n = ℏω (n + 1/2)`` for
    ``n = 0, 1, 2, …``. With ℏ = 1 the spectrum is ``ω (n + 1/2)``.

    Canonical SSoT: same as ``harmonic_oscillator_ladder``;
    Sakurai *Modern QM* §2.3 eq 2.3.16.

    Args:
        n_dim: Truncation dimension.
        omega: Angular frequency.

    Returns:
        Hermitian ``(n_dim, n_dim)`` Hamiltonian matrix.
    """
    a, a_dagger = harmonic_oscillator_ladder(n_dim, omega)
    return omega * (dense_matmul_complex(a_dagger, a) + 0.5 * np.eye(n_dim, dtype=complex))


__all__ = [
    "harmonic_oscillator_hamiltonian",
    "harmonic_oscillator_ladder",
    "hydrogen_radial",
]
