"""Canonical single-particle QM operations.

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites
canonical physics literature. Implementations are numpy-based; for large
real-symmetric Hamiltonians the underlying eigendecomposition is the
Class L primitive (``srmech.amsc.laplacian.jacobi_eigvals``); numpy
covers the complex-Hermitian general case.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: these
substrate-coupling operations act on Hilbert-space content; the
LoE-content itself lives at 1D_t per MFO §VII.1.2.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple

from srmech.amsc.laplacian import (
    dense_matmul_complex,
    dense_matvec_complex,
    dense_outer_complex,
    hermitian_eigendecompose,
)


def tdse_evolve(H: np.ndarray, psi: np.ndarray, t: float) -> np.ndarray:
    """Closed-form Time-Dependent Schrödinger evolution.

    Solves ``iℏ ∂_t ψ = H ψ`` (ℏ = 1) via eigenbasis-diagonal closed form:
    ``ψ(t) = V·diag(exp(-iλt))·V^H ψ(0)`` where ``(λ, V) = eigh(H)``.

    Canonical SSoT: Schrödinger (1926) *Annalen der Physik* 79, 489;
    Sakurai *Modern QM* §2.1.5 eq 2.1.40; Cohen-Tannoudji *QM* §III.D.2.

    Args:
        H: Hermitian Hamiltonian (n × n).
        psi: Initial state (n).
        t: Evolution time (in units of ℏ / energy).

    Returns:
        ψ(t) of shape (n,), complex dtype.
    """
    if H.shape[0] != H.shape[1]:
        raise ValueError(f"tdse_evolve: H must be square; got shape {H.shape}")
    if psi.shape[0] != H.shape[0]:
        raise ValueError(
            f"tdse_evolve: psi shape {psi.shape} incompatible with H shape {H.shape}"
        )
    # Class-L Hermitian eigendecomposition (srmech's own primitive). H is a
    # general complex-Hermitian Hamiltonian, so V stays complex128.
    eigvals, V = hermitian_eigendecompose(H)
    psi_eigbasis = dense_matvec_complex(V.conj().T, psi)   # Class-L matvec cascade
    psi_t_eigbasis = np.exp(-1j * eigvals * t) * psi_eigbasis
    return dense_matvec_complex(V, psi_t_eigbasis)          # Class-L matvec cascade


def tise_solve(H: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Time-Independent Schrödinger Equation ``H ψ_n = E_n ψ_n``.

    Canonical SSoT: Schrödinger (1926) *Annalen der Physik* 79, 361;
    Sakurai *Modern QM* §2.1.3; Griffiths *Intro QM* §2.1.

    Args:
        H: Hermitian Hamiltonian (n × n).

    Returns:
        ``(eigenvalues, eigenvectors)``: ascending eigenvalues (n,) and
        column-stacked eigenvectors (n, n), orthonormal.
    """
    if H.shape[0] != H.shape[1]:
        raise ValueError(f"tise_solve: H must be square; got shape {H.shape}")
    # Class-L Hermitian eigendecomposition (srmech's own primitive). General
    # complex-Hermitian H, so the eigenvectors stay complex128.
    return hermitian_eigendecompose(H)


def commutator(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Operator commutator ``[A, B] = A B - B A``.

    Canonical SSoT: Sakurai *Modern QM* §1.4 eq 1.4.6.
    """
    if A.shape != B.shape or A.shape[0] != A.shape[1]:
        raise ValueError(
            f"commutator: A and B must be square and same shape; "
            f"got {A.shape} vs {B.shape}"
        )
    return dense_matmul_complex(A, B) - dense_matmul_complex(B, A)  # Class-L matmul cascade


def heisenberg_evolve(A: np.ndarray, H: np.ndarray, t: float) -> np.ndarray:
    """Heisenberg-picture operator evolution ``A_H(t) = U†(t) A U(t)``.

    With ``U(t) = exp(-iHt/ℏ)`` and ℏ = 1. Equivalent to integrating the
    Heisenberg equation ``dA_H/dt = (i/ℏ) [H, A_H]``.

    Canonical SSoT: Sakurai *Modern QM* §2.2 eq 2.2.15; Heisenberg (1925)
    *Zeitschrift für Physik* 33, 879.

    Args:
        A: Operator to evolve (n × n).
        H: Hermitian Hamiltonian (n × n).
        t: Evolution time.

    Returns:
        ``A_H(t)`` of shape (n, n), complex dtype.
    """
    if A.shape != H.shape:
        raise ValueError(
            f"heisenberg_evolve: A and H must have same shape; "
            f"got A={A.shape} vs H={H.shape}"
        )
    # Class-L Hermitian eigendecomposition (srmech's own primitive); general
    # complex-Hermitian H, so V stays complex128.
    eigvals, V = hermitian_eigendecompose(H)
    phases = np.exp(-1j * eigvals * t)
    # U = V·diag(phases)·Vᴴ, then A_H = Uᴴ·A·U — Class-L matmul cascade throughout.
    U = dense_matmul_complex(dense_matmul_complex(V, np.diag(phases)), V.conj().T)
    return dense_matmul_complex(dense_matmul_complex(U.conj().T, A), U)


def lattice_momentum(n: int, dx: float = 1.0) -> np.ndarray:
    """Lattice momentum operator ``p̂ = -i ∂_x`` via central-difference.

    Periodic boundary; uniform 1D lattice with spacing ``dx``.
    ``p̂[i, j] = -i/(2 dx) (δ_{j, i+1 mod n} - δ_{j, i-1 mod n})``.
    Hermitian by construction. Per ``[[user_stance_pi_as_projection]]`` —
    the discrete-cyclic upstream of the continuous derivative.

    Canonical SSoT: Sakurai *Modern QM* §1.6 (canonical momentum operator);
    standard lattice-QFT discretization (Wilson 1974 *Phys Rev D* 10, 2445
    for the lattice-QFT framing).

    Args:
        n: Number of lattice sites.
        dx: Lattice spacing.

    Returns:
        Hermitian (n, n) momentum operator (complex dtype).
    """
    if n < 2:
        raise ValueError(f"lattice_momentum: n must be ≥ 2; got {n}")
    if dx <= 0:
        raise ValueError(f"lattice_momentum: dx must be positive; got {dx}")
    p = np.zeros((n, n), dtype=complex)
    coef = 1j / (2.0 * dx)
    for i in range(n):
        p[i, (i + 1) % n] = -coef
        p[i, (i - 1) % n] = coef
    return p


def density_matrix(psi: np.ndarray) -> np.ndarray:
    """Pure-state density matrix ``ρ = |ψ⟩⟨ψ|``.

    Canonical SSoT: von Neumann (1932) *Mathematische Grundlagen*;
    Sakurai *Modern QM* §3.4 eq 3.4.7.

    Args:
        psi: State vector (n,). Should be normalized.

    Returns:
        Density matrix (n, n), Hermitian PSD with trace = ⟨ψ|ψ⟩.
    """
    if psi.ndim != 1:
        raise ValueError(f"density_matrix: psi must be 1-D; got shape {psi.shape}")
    return dense_outer_complex(psi, psi.conj())


def liouville_evolve(rho: np.ndarray, H: np.ndarray, t: float) -> np.ndarray:
    """Liouville-von Neumann evolution ``ρ(t) = U(t) ρ(0) U†(t)``.

    Equivalent to integrating ``iℏ ∂_t ρ = [H, ρ]``.

    Canonical SSoT: von Neumann (1932) *Mathematische Grundlagen*;
    Sakurai *Modern QM* §3.4.2 eq 3.4.28.

    Args:
        rho: Initial density matrix (n × n).
        H: Hermitian Hamiltonian (n × n).
        t: Evolution time.

    Returns:
        ρ(t) of shape (n, n).
    """
    if rho.shape != H.shape:
        raise ValueError(
            f"liouville_evolve: rho and H must have same shape; "
            f"got rho={rho.shape} vs H={H.shape}"
        )
    # Class-L Hermitian eigendecomposition (srmech's own primitive); general
    # complex-Hermitian H, so V stays complex128.
    eigvals, V = hermitian_eigendecompose(H)
    phases = np.exp(-1j * eigvals * t)
    # U = V·diag(phases)·Vᴴ, then ρ(t) = U·ρ·Uᴴ — Class-L matmul cascade throughout.
    U = dense_matmul_complex(dense_matmul_complex(V, np.diag(phases)), V.conj().T)
    return dense_matmul_complex(dense_matmul_complex(U, rho), U.conj().T)


__all__ = [
    "commutator",
    "density_matrix",
    "heisenberg_evolve",
    "lattice_momentum",
    "liouville_evolve",
    "tdse_evolve",
    "tise_solve",
]
