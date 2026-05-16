"""Gauge theory: Yang-Mills generators, structure constants, Casimirs, holonomies.

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites
canonical gauge-theory literature.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: gauge
operations are substrate-coupling operations on internal-symmetry
representation spaces. Class M (binding) for the generator-matrix
representation; Class L (eigendecomposition) for path-segment holonomies
via Hermitian-matrix exponentials.

Lie algebra conventions:

- ``[T^a, T^b] = i f^{abc} T^c`` (structure constants real, antisymmetric)
- Fundamental of SU(N): ``T^a = λ^a / 2`` (Gell-Mann normalization for SU(3));
  ``tr(T^a T^b) = (1/2) δ^{ab}``.
- Casimir ``C_2(R) = T^a T^a`` (sum over a). By Schur's lemma, on an
  irreducible representation this is a scalar multiple of the identity;
  for the fundamental of SU(N), ``C_2 = (N² - 1) / (2N)``.

Canonical SSoT:

- Yang, C.N. & Mills, R.L. (1954) *Phys. Rev.* 96, 191-195
  (non-abelian gauge fields).
- Gell-Mann, M. (1962) *Phys. Rev.* 125, 1067-1084 (SU(3) Gell-Mann
  matrices).
- Peskin, M.E. & Schroeder, D.V. (1995) *Intro QFT*, §15-16.
- Schwartz, M.D. (2014) *QFT and the SM*, §25-26.
- Weinberg, S. (1996) *Quantum Theory of Fields*, Vol. II, §15.
- Wilson, K.G. (1974) *Phys. Rev. D* 10, 2445-2459 (Wilson loop).
"""

from __future__ import annotations

import numpy as np
from typing import Tuple

from srmech.qm.spin import pauli_matrices


# ----------------------------------------------------------------------
# SU(2)
# ----------------------------------------------------------------------


def su2_generators() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """SU(2) fundamental generators ``T^a = σ^a / 2`` for a = 1, 2, 3.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.5 + 15.6;
    Sakurai *Modern QM* §3.2.

    Returns:
        ``(T1, T2, T3)``: three 2×2 Hermitian traceless matrices
        satisfying ``[T^a, T^b] = i ε^{abc} T^c`` and ``tr(T^a T^b) = δ^{ab}/2``.
    """
    sx, sy, sz = pauli_matrices()
    return 0.5 * sx, 0.5 * sy, 0.5 * sz


def su2_structure_constants() -> np.ndarray:
    """Levi-Civita ``ε^{abc}`` — SU(2) structure constants.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.4 (``[T^a, T^b] = i ε^{abc} T^c``).

    Returns:
        Real (3, 3, 3) tensor; ``f[a, b, c] = ε^{abc}``.
    """
    f = np.zeros((3, 3, 3))
    cyclic = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]
    for a, b, c in cyclic:
        f[a, b, c] = 1.0
        f[b, a, c] = -1.0
    return f


# ----------------------------------------------------------------------
# SU(3) — Gell-Mann
# ----------------------------------------------------------------------


def su3_gell_mann_matrices() -> Tuple[np.ndarray, ...]:
    """The eight Gell-Mann matrices ``λ^1, ..., λ^8`` (Hermitian traceless 3×3).

    Normalization: ``tr(λ^a λ^b) = 2 δ^{ab}``.

    Canonical SSoT: Gell-Mann (1962) *Phys. Rev.* 125, 1067 eq 16;
    Peskin-Schroeder eq 17.32; Schwartz §25.2.

    Returns:
        Tuple of eight 3×3 complex Hermitian traceless matrices.
    """
    lam = []
    # λ^1: (1,2) real symmetric
    lam.append(np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=complex))
    # λ^2: (1,2) imaginary antisymmetric
    lam.append(np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]], dtype=complex))
    # λ^3: diagonal SU(2) within 1-2
    lam.append(np.array([[1, 0, 0], [0, -1, 0], [0, 0, 0]], dtype=complex))
    # λ^4: (1,3) real
    lam.append(np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]], dtype=complex))
    # λ^5: (1,3) imaginary
    lam.append(np.array([[0, 0, -1j], [0, 0, 0], [1j, 0, 0]], dtype=complex))
    # λ^6: (2,3) real
    lam.append(np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=complex))
    # λ^7: (2,3) imaginary
    lam.append(np.array([[0, 0, 0], [0, 0, -1j], [0, 1j, 0]], dtype=complex))
    # λ^8: diagonal hypercharge-like
    lam.append((1.0 / np.sqrt(3.0)) * np.array(
        [[1, 0, 0], [0, 1, 0], [0, 0, -2]], dtype=complex
    ))
    return tuple(lam)


def su3_generators() -> Tuple[np.ndarray, ...]:
    """SU(3) fundamental generators ``T^a = λ^a / 2`` for a = 1, ..., 8.

    Satisfies ``[T^a, T^b] = i f^{abc} T^c`` and ``tr(T^a T^b) = δ^{ab}/2``.

    Canonical SSoT: Peskin-Schroeder eq 17.33; Schwartz §25.2.
    """
    return tuple(0.5 * lam for lam in su3_gell_mann_matrices())


def su3_structure_constants() -> np.ndarray:
    """SU(3) structure constants ``f^{abc}`` (totally antisymmetric).

    Non-zero values (Peskin-Schroeder eq 17.34; Schwartz Table 25.1)::

        f^{123} = 1
        f^{147} = f^{246} = f^{257} = f^{345} = 1/2
        f^{156} = f^{367} = -1/2
        f^{458} = f^{678} = √3/2

    All other independent components are zero; remaining entries fill in
    by total antisymmetry.

    Returns:
        Real (8, 8, 8) tensor.
    """
    f = np.zeros((8, 8, 8))
    seed_values = [
        (0, 1, 2, 1.0),
        (0, 3, 6, 0.5),
        (1, 3, 5, 0.5),
        (1, 4, 6, 0.5),
        (2, 3, 4, 0.5),
        (0, 4, 5, -0.5),
        (2, 5, 6, -0.5),
        (3, 4, 7, np.sqrt(3.0) / 2.0),
        (5, 6, 7, np.sqrt(3.0) / 2.0),
    ]
    for a, b, c, val in seed_values:
        # Fill via total antisymmetry: f[π(abc)] = sign(π) val.
        perms = [
            ((a, b, c), 1.0),
            ((b, c, a), 1.0),
            ((c, a, b), 1.0),
            ((a, c, b), -1.0),
            ((c, b, a), -1.0),
            ((b, a, c), -1.0),
        ]
        for (i, j, k), sign in perms:
            f[i, j, k] = sign * val
    return f


# ----------------------------------------------------------------------
# Lie algebra verification + Casimir
# ----------------------------------------------------------------------


def lie_algebra_residual(
    generators: Tuple[np.ndarray, ...],
    structure_constants: np.ndarray,
) -> float:
    """Maximum Frobenius-norm violation of ``[T^a, T^b] = i f^{abc} T^c``.

    Should be at machine precision for the canonical SU(2) and SU(3)
    constructions above.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.4.

    Args:
        generators: Tuple of n_gen Hermitian generators.
        structure_constants: Real (n_gen, n_gen, n_gen) tensor.

    Returns:
        Maximum Frobenius residual across all (a, b) pairs.
    """
    n_gen = len(generators)
    if structure_constants.shape != (n_gen, n_gen, n_gen):
        raise ValueError(
            f"lie_algebra_residual: structure_constants shape "
            f"{structure_constants.shape} ≠ ({n_gen}, {n_gen}, {n_gen})"
        )
    max_residual = 0.0
    for a in range(n_gen):
        for b in range(n_gen):
            comm = generators[a] @ generators[b] - generators[b] @ generators[a]
            rhs = 1j * sum(
                structure_constants[a, b, c] * generators[c] for c in range(n_gen)
            )
            max_residual = max(max_residual, float(np.linalg.norm(comm - rhs)))
    return max_residual


def casimir_operator(generators: Tuple[np.ndarray, ...]) -> np.ndarray:
    """Quadratic Casimir ``C_2 = T^a T^a`` (sum over generators).

    By Schur's lemma, on an irreducible representation R this equals
    ``C_2(R) · I``. For the fundamental of SU(N), the eigenvalue is
    ``(N² - 1) / (2N)``: 3/4 for SU(2), 4/3 for SU(3).

    Canonical SSoT: Peskin-Schroeder §15.4 eq 15.93;
    Schwartz §25.2.

    Returns:
        Casimir as a matrix in the representation of ``generators``.
    """
    if not generators:
        raise ValueError("casimir_operator: generators tuple is empty")
    return sum(T @ T for T in generators)


def casimir_eigenvalue(generators: Tuple[np.ndarray, ...]) -> float:
    """Scalar Casimir eigenvalue ``C_2(R)`` (assumes irreducible representation).

    Equals ``trace(C_2) / dim(R)`` since ``C_2 = C_2(R) · I``.

    Canonical SSoT: Peskin-Schroeder §15.4 eq 15.93.

    Returns:
        Real positive scalar.
    """
    C2 = casimir_operator(generators)
    dim = C2.shape[0]
    return float(np.trace(C2).real / dim)


# ----------------------------------------------------------------------
# Holonomy / Wilson-loop primitives
# ----------------------------------------------------------------------


def gauge_connection_matrix(
    A_components: np.ndarray,
    generators: Tuple[np.ndarray, ...],
) -> np.ndarray:
    """Lie-algebra connection ``A = A^a T^a`` from component vector.

    For a Yang-Mills gauge potential ``A^a_μ``, given a fixed spacetime
    component ``μ``, this returns the matrix-valued ``A_μ = A^a_μ T^a``.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.2.

    Args:
        A_components: Real (n_gen,) array of Lie-algebra components.
        generators: Generator matrices.

    Returns:
        Hermitian matrix ``A^a T^a`` in the representation of ``generators``.
    """
    n_gen = len(generators)
    A = np.asarray(A_components, dtype=float)
    if A.shape != (n_gen,):
        raise ValueError(
            f"gauge_connection_matrix: A_components shape {A.shape} ≠ "
            f"({n_gen},)"
        )
    return sum(A[a] * generators[a] for a in range(n_gen))


def gauge_path_segment(
    A_components: np.ndarray,
    generators: Tuple[np.ndarray, ...],
    coupling: float = 1.0,
) -> np.ndarray:
    """Path-segment holonomy ``U = exp(i g A^a T^a)`` along a small loop step.

    Uses the Hermitian eigendecomposition of ``M = g A^a T^a`` — for any
    Hermitian M, ``exp(i M) = V·diag(exp(i λ))·V^H`` — so no scipy
    dependency. Caller composes segments via matrix multiplication in
    path order to build a Wilson loop.

    Canonical SSoT: Wilson (1974) *Phys. Rev. D* 10, 2445 eq 2.3;
    Peskin-Schroeder §15.3 eq 15.55.

    Args:
        A_components: Connection components (n_gen,).
        generators: Hermitian generators.
        coupling: Gauge coupling ``g`` (real).

    Returns:
        Unitary segment-holonomy matrix in the representation.
    """
    M = coupling * gauge_connection_matrix(A_components, generators)
    eigvals, V = np.linalg.eigh(M)
    return V @ np.diag(np.exp(1j * eigvals)) @ V.conj().T


def wilson_loop_from_segments(
    A_segments: np.ndarray,
    generators: Tuple[np.ndarray, ...],
    coupling: float = 1.0,
) -> np.ndarray:
    """Wilson loop ``U(C) = P exp(i g ∮_C A) ≈ ∏_k exp(i g A_k)``.

    Discrete path-ordered approximation: multiply segment holonomies in
    path order. Caller provides ``A_segments`` of shape ``(n_segments, n_gen)``
    where each row is the connection components along that segment.

    Canonical SSoT: Wilson (1974) *Phys. Rev. D* 10, 2445;
    Peskin-Schroeder §15.3.

    Args:
        A_segments: (n_segments, n_gen) array; row k = ``A^a`` at segment k.
        generators: Hermitian generators.
        coupling: Gauge coupling.

    Returns:
        Unitary Wilson-loop matrix in the representation.
    """
    A_segments = np.asarray(A_segments, dtype=float)
    if A_segments.ndim != 2 or A_segments.shape[1] != len(generators):
        raise ValueError(
            f"wilson_loop_from_segments: A_segments shape {A_segments.shape} "
            f"must be (n_segments, {len(generators)})"
        )
    dim = generators[0].shape[0]
    U = np.eye(dim, dtype=complex)
    for k in range(A_segments.shape[0]):
        U = gauge_path_segment(A_segments[k], generators, coupling) @ U
    return U


__all__ = [
    "casimir_eigenvalue",
    "casimir_operator",
    "gauge_connection_matrix",
    "gauge_path_segment",
    "lie_algebra_residual",
    "su2_generators",
    "su2_structure_constants",
    "su3_gell_mann_matrices",
    "su3_generators",
    "su3_structure_constants",
    "wilson_loop_from_segments",
]
