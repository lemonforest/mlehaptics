"""Spin-½ operators: Pauli matrices + Clifford algebra Cl(0,3).

The Pauli matrices σ_x, σ_y, σ_z generate the Clifford algebra ``Cl(0,3)``
with anti-commutation ``{σ_i, σ_j} = 2 δ_{ij} I`` and commutation
``[σ_i, σ_j] = 2i ε_{ijk} σ_k``. Per
``[[user_stance_1d_collapse_to_loe_identity_not_action]]`` + Spike #24:
Pauli matrices are a **Class M Clifford binding** primitive — they bind
the 2-spinor space into substrate-localised form. Foundational to the
Dirac equation (relativistic QM, rc10) and to qubit / quantum-information
primitives.

Canonical SSoT:

- Pauli, W. (1927) *Zeitschrift für Physik* 43, 601-623.
- Sakurai, J.J. *Modern QM* §3.2.
- Cohen-Tannoudji *QM* §IV.A.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple

from srmech.amsc.laplacian import dense_matmul_complex


def pauli_matrices() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the three Pauli matrices ``(σ_x, σ_y, σ_z)``.

    Canonical SSoT: Pauli (1927) *Zeitschrift für Physik* 43, 601;
    Sakurai *Modern QM* §3.2 eq 3.2.1.

    Returns:
        ``(sigma_x, sigma_y, sigma_z)``: each a 2×2 complex Hermitian
        traceless matrix satisfying ``σ_i² = I`` and the Clifford algebra.
    """
    sigma_x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    sigma_y = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
    sigma_z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    return sigma_x, sigma_y, sigma_z


def pauli_identity() -> np.ndarray:
    """The 2×2 identity (Cl(0,3) scalar)."""
    return np.eye(2, dtype=complex)


def pauli_clifford_residuals() -> Tuple[float, float]:
    """Numerical residuals for the Clifford algebra relations on σ_i.

    Verifies:

    - **Anticommutation**: ``{σ_i, σ_j} = 2 δ_{ij} I`` for all i, j.
    - **Commutation**: ``[σ_i, σ_j] = 2i ε_{ijk} σ_k`` (cyclic).

    Canonical SSoT: Sakurai *Modern QM* §3.2 eq 3.2.2-3.2.3.

    Returns:
        ``(max_anticomm_dev, max_comm_dev)``: maximum Frobenius-norm
        deviation from the expected relations. Both should be at machine
        precision (~1e-15).
    """
    sx, sy, sz = pauli_matrices()
    I = pauli_identity()
    # Anticommutator residuals — Class-L matmul cascade for every Pauli product.
    mm = dense_matmul_complex
    anti_off = [mm(sx, sy) + mm(sy, sx),
                mm(sx, sz) + mm(sz, sx),
                mm(sy, sz) + mm(sz, sy)]
    anti_diag = [mm(sx, sx) - I, mm(sy, sy) - I, mm(sz, sz) - I]
    max_anti = max(
        np.linalg.norm(c) for c in (anti_off + anti_diag)
    )
    # Commutator residuals (cyclic).
    comm = [
        (mm(sx, sy) - mm(sy, sx)) - 2j * sz,
        (mm(sy, sz) - mm(sz, sy)) - 2j * sx,
        (mm(sz, sx) - mm(sx, sz)) - 2j * sy,
    ]
    max_comm = max(np.linalg.norm(c) for c in comm)
    return max_anti, max_comm


def pauli_spin_operator(direction: np.ndarray) -> np.ndarray:
    """Spin-½ projection onto an arbitrary axis: ``S_n = (ℏ/2) σ · n̂``.

    Returns ``σ · n̂ / 2`` (ℏ = 1 convention) where ``n̂`` is the unit
    vector along the chosen direction.

    Canonical SSoT: Sakurai *Modern QM* §3.2 eq 3.2.51; Griffiths
    *Intro QM* §4.4.

    Args:
        direction: 3-vector (need not be unit; will be normalized).

    Returns:
        2×2 Hermitian matrix with eigenvalues ±½.

    Raises:
        ValueError: zero-magnitude direction or wrong shape.
    """
    direction = np.asarray(direction, dtype=float)
    if direction.shape != (3,):
        raise ValueError(
            f"pauli_spin_operator: direction must be a 3-vector; "
            f"got shape {direction.shape}"
        )
    norm = np.linalg.norm(direction)
    if norm == 0.0:
        raise ValueError("pauli_spin_operator: direction must be non-zero")
    nhat = direction / norm
    sx, sy, sz = pauli_matrices()
    return 0.5 * (nhat[0] * sx + nhat[1] * sy + nhat[2] * sz)


__all__ = [
    "pauli_clifford_residuals",
    "pauli_identity",
    "pauli_matrices",
    "pauli_spin_operator",
]
