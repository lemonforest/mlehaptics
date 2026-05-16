"""Relativistic QM: Dirac γ-matrix algebra + Klein-Gordon + Weyl + Majorana.

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites
canonical relativistic QM / QFT literature.

Metric convention: **mostly-minus** ``η^{μν} = diag(+1, -1, -1, -1)``
(Peskin-Schroeder convention; the standard QFT-side choice).

γ-matrix representation: **Dirac (standard) basis** per Peskin-Schroeder
eq A.18. Other representations (Weyl/chiral, Majorana) derivable from this
via similarity transformations; the Dirac basis is the most common
textbook starting point.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]`` + the
Spike #24 14-class vocabulary: γ-matrices are a **Class M Clifford
binding** primitive — they bind the Dirac spinor space ``ℂ^4`` into
Lorentz-covariant form. Cl(1,3) Clifford algebra: ``{γ^μ, γ^ν} = 2 η^{μν} I_4``.

Canonical SSoT:

- Dirac, P.A.M. (1928) *Proc. Roy. Soc. A* 117, 610-624; 118, 351-361.
- Klein, O. (1926) *Zeitschrift für Physik* 37, 895-906;
  Gordon, W. (1926) *Zeitschrift für Physik* 40, 117-133.
- Weyl, H. (1929) *Zeitschrift für Physik* 56, 330.
- Majorana, E. (1937) *Nuovo Cimento* 14, 171.
- Peskin, M.E. & Schroeder, D.V. (1995) *An Introduction to Quantum Field
  Theory*, Westview / Addison-Wesley. Chapters 3-4.
- Bjorken, J.D. & Drell, S.D. (1964) *Relativistic Quantum Mechanics*.
- Weinberg, S. (1995) *The Quantum Theory of Fields*, Volume I.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple

from srmech.qm.spin import pauli_matrices, pauli_identity


def minkowski_metric() -> np.ndarray:
    """Mostly-minus Minkowski metric ``η^{μν} = diag(+1, -1, -1, -1)``.

    Canonical SSoT: Peskin-Schroeder §3.1 eq 3.4 (mostly-minus convention).
    """
    return np.diag([1.0, -1.0, -1.0, -1.0])


def gamma_matrices() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Dirac γ-matrices ``(γ^0, γ^1, γ^2, γ^3)`` in the Dirac representation.

    In ``2 × 2`` block form using Pauli σ-matrices and the 2×2 identity::

        γ^0 = [[ I_2,  0  ],
               [  0, -I_2 ]]

        γ^i = [[  0,   σ_i ],
               [ -σ_i, 0  ]]   for i = 1, 2, 3.

    Canonical SSoT: Peskin-Schroeder §3.2 eq 3.25 + A.6;
    Bjorken-Drell §3.2 eq 3.8.

    Returns:
        ``(g0, g1, g2, g3)``: four 4×4 complex matrices satisfying the
        Clifford algebra ``{γ^μ, γ^ν} = 2 η^{μν} I_4``.
    """
    I2 = pauli_identity()
    Z2 = np.zeros((2, 2), dtype=complex)
    sx, sy, sz = pauli_matrices()
    g0 = np.block([[I2, Z2], [Z2, -I2]])
    g1 = np.block([[Z2, sx], [-sx, Z2]])
    g2 = np.block([[Z2, sy], [-sy, Z2]])
    g3 = np.block([[Z2, sz], [-sz, Z2]])
    return g0, g1, g2, g3


def gamma_5() -> np.ndarray:
    """``γ_5 = i γ^0 γ^1 γ^2 γ^3`` — chirality matrix.

    In the Dirac representation::

        γ_5 = [[ 0, I_2 ],
               [ I_2, 0 ]]

    Properties: ``γ_5² = I_4``, ``{γ_5, γ^μ} = 0`` for all μ, ``γ_5† = γ_5``.

    Canonical SSoT: Peskin-Schroeder §3.4 eq 3.72; Bjorken-Drell §6.1.
    """
    g0, g1, g2, g3 = gamma_matrices()
    return 1j * g0 @ g1 @ g2 @ g3


def clifford_residuals() -> Tuple[float, float, float]:
    """Numerical residuals for the Cl(1,3) Clifford algebra relations.

    Verifies at machine precision:

    1. ``{γ^μ, γ^ν} = 2 η^{μν} I_4`` for all μ, ν.
    2. ``γ_5² = I_4``.
    3. ``{γ_5, γ^μ} = 0`` for all μ.

    Canonical SSoT: Peskin-Schroeder §3.2 eq 3.21 + §3.4 eq 3.72.

    Returns:
        ``(max_clifford_dev, gamma5_squared_dev, gamma5_anticomm_dev)``:
        all should be at ~1e-14 in double precision.
    """
    gammas = gamma_matrices()
    eta = minkowski_metric()
    I4 = np.eye(4, dtype=complex)
    max_clifford = 0.0
    for mu in range(4):
        for nu in range(4):
            anti = gammas[mu] @ gammas[nu] + gammas[nu] @ gammas[mu]
            expected = 2.0 * eta[mu, nu] * I4
            max_clifford = max(max_clifford, np.linalg.norm(anti - expected))
    g5 = gamma_5()
    g5_sq_dev = float(np.linalg.norm(g5 @ g5 - I4))
    g5_anti_dev = max(
        np.linalg.norm(g5 @ gammas[mu] + gammas[mu] @ g5) for mu in range(4)
    )
    return max_clifford, g5_sq_dev, g5_anti_dev


def weyl_left_projector() -> np.ndarray:
    """Left-chirality projector ``P_L = (I - γ_5) / 2``.

    Projects a Dirac spinor onto its left-handed Weyl component.
    Properties: ``P_L² = P_L``, ``P_L P_R = 0``, ``P_L + P_R = I``.

    Canonical SSoT: Peskin-Schroeder §3.4 eq 3.71.
    """
    return 0.5 * (np.eye(4, dtype=complex) - gamma_5())


def weyl_right_projector() -> np.ndarray:
    """Right-chirality projector ``P_R = (I + γ_5) / 2``.

    Canonical SSoT: Peskin-Schroeder §3.4 eq 3.71.
    """
    return 0.5 * (np.eye(4, dtype=complex) + gamma_5())


def charge_conjugation_matrix() -> np.ndarray:
    """Charge-conjugation matrix ``C = i γ^2 γ^0`` (Dirac representation).

    Used to define charge conjugation ``ψ_c = C ψ̄^T`` and the Majorana
    self-conjugacy condition ``ψ = ψ_c``.

    Canonical SSoT: Peskin-Schroeder eq A.27; Bjorken-Drell §5.2.
    """
    g0, g1, g2, g3 = gamma_matrices()
    return 1j * g2 @ g0


def dirac_operator_momentum_space(k: np.ndarray, m: float) -> np.ndarray:
    """Dirac operator in momentum space: ``γ^μ k_μ - m I_4``.

    With mostly-minus metric, ``γ^μ k_μ = γ^0 k_0 - γ^1 k_1 - γ^2 k_2 - γ^3 k_3``.
    A Dirac spinor ψ satisfies the momentum-space Dirac equation
    ``(γ^μ k_μ - m) ψ(k) = 0`` on-shell ``k² = m²``.

    Canonical SSoT: Peskin-Schroeder §3.2 eq 3.45 + 3.46.

    Args:
        k: 4-momentum ``(k_0, k_1, k_2, k_3)``.
        m: Mass (rest energy in natural units).

    Returns:
        ``(γ^μ k_μ - m I_4)`` as a 4×4 complex matrix.
    """
    k = np.asarray(k, dtype=float)
    if k.shape != (4,):
        raise ValueError(f"dirac_operator_momentum_space: k must be 4-vector; got {k.shape}")
    g0, g1, g2, g3 = gamma_matrices()
    eta = minkowski_metric()
    # k_μ = η_{μν} k^ν (mostly-minus metric)
    k_lower = eta @ k
    slash_k = k_lower[0] * g0 + k_lower[1] * g1 + k_lower[2] * g2 + k_lower[3] * g3
    return slash_k - m * np.eye(4, dtype=complex)


def klein_gordon_dispersion(k_spatial: np.ndarray, m: float) -> float:
    """Klein-Gordon on-shell energy ``E = +sqrt(|k|² + m²)``.

    Positive-frequency solution of the relativistic dispersion
    ``E² = |k|² + m²`` (mostly-minus metric: ``k² = E² - |k|² = m²``
    on-shell).

    Canonical SSoT: Klein (1926) eq 5; Gordon (1926) eq 1;
    Peskin-Schroeder §2.3 eq 2.39.

    Args:
        k_spatial: 3-momentum vector.
        m: Mass.

    Returns:
        Positive-frequency on-shell energy.
    """
    k_spatial = np.asarray(k_spatial, dtype=float)
    if k_spatial.shape != (3,):
        raise ValueError(
            f"klein_gordon_dispersion: k_spatial must be 3-vector; "
            f"got {k_spatial.shape}"
        )
    if m < 0:
        raise ValueError(f"klein_gordon_dispersion: m must be ≥ 0; got {m}")
    return float(np.sqrt(np.dot(k_spatial, k_spatial) + m * m))


def four_momentum_squared(k: np.ndarray) -> float:
    """Lorentz-invariant squared 4-momentum ``k² = k_μ k^μ = k_0² - |k|²``.

    Mostly-minus convention. On-shell: ``k² = m²``.

    Canonical SSoT: Peskin-Schroeder §3.1 eq 3.4.
    """
    k = np.asarray(k, dtype=float)
    if k.shape != (4,):
        raise ValueError(f"four_momentum_squared: k must be 4-vector; got {k.shape}")
    eta = minkowski_metric()
    return float(k @ eta @ k)


__all__ = [
    "charge_conjugation_matrix",
    "clifford_residuals",
    "dirac_operator_momentum_space",
    "four_momentum_squared",
    "gamma_5",
    "gamma_matrices",
    "klein_gordon_dispersion",
    "minkowski_metric",
    "weyl_left_projector",
    "weyl_right_projector",
]
