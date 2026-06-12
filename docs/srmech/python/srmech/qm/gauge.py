"""Gauge theory: Yang-Mills generators, structure constants, Casimirs, holonomies (numpy-free).

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites
canonical gauge-theory literature.

numpy-FREE (v0.7.5rc119, #564): the SU(2)/SU(3) generators, the eight
Gell-Mann matrices, and every derived operator (connection, Casimir,
path-segment holonomy, Wilson loop) are held in the framework-native
:class:`~srmech.amsc.mat.Mat` carrier — the SU(2) generators are built from
the numpy-free Pauli 2×2 ``Mat`` blocks
(:func:`srmech.qm.spin.pauli_matrices`), the Gell-Mann matrices from exact
small-integer ``Mat`` (with the λ⁸ ``1/√3`` normaliser via the Class-N
:func:`srmech.amsc.rational.sqrt`). Every matrix product routes through the
Class-L :func:`~srmech.amsc.laplacian.mat_matmul`, residual norms through
:func:`~srmech.amsc.laplacian.mat_norm`, and the path-segment holonomy
``exp(i g A^a T^a)`` through the Class-L
:func:`~srmech.amsc.laplacian.mat_hermitian_eigendecompose`
(``V·diag(e^{iλ})·Vᴴ`` with the Class-N :func:`srmech.amsc.rational.cexp`
Euler phase) — **no numpy**. The structure constants ``f^{abc}`` are plain
nested Python lists (rank-3; ``Mat`` is 2-D only).

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

from typing import List, Sequence, Tuple

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import (
    mat_hermitian_eigendecompose,
    mat_matmul,
    mat_norm,
)
from srmech.amsc.mat import Mat
from srmech.qm.spin import pauli_matrices


# ----------------------------------------------------------------------
# numpy-free Mat helpers
# ----------------------------------------------------------------------


def _scale(s, m: "Mat") -> "Mat":
    """``s · M`` (scalar × ``Mat``) as a new complex ``Mat`` (numpy-free)."""
    rows = [[s * m[i, j] for j in range(m.n_cols)] for i in range(m.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


def _mat_add(a: "Mat", b: "Mat") -> "Mat":
    rows = [[a[i, j] + b[i, j] for j in range(a.n_cols)] for i in range(a.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


def _mat_sub(a: "Mat", b: "Mat") -> "Mat":
    rows = [[a[i, j] - b[i, j] for j in range(a.n_cols)] for i in range(a.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


def _mat_sum(mats: Sequence["Mat"]) -> "Mat":
    """Fold a non-empty sequence of same-shape ``Mat`` by element-wise add.

    Replaces the numpy ``sum(...)`` accumulator (which started at the int ``0``
    and only worked because ``0 + ndarray`` broadcasts) with an explicit
    numpy-free Class-M reduction over the ``Mat`` carrier.
    """
    acc = mats[0]
    for m in mats[1:]:
        acc = _mat_add(acc, m)
    return acc


def _eye(n: int) -> "Mat":
    """The ``n × n`` complex identity as a ``Mat`` (numpy-free)."""
    return Mat.from_rows(
        [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)],
        is_complex=True,
    )


def _trace(m: "Mat") -> complex:
    """Matrix trace ``Σ_i M[i, i]`` as a plain ``complex`` (numpy-free)."""
    return sum(m[i, i] for i in range(m.n_rows))


# ----------------------------------------------------------------------
# SU(2)
# ----------------------------------------------------------------------


def su2_generators() -> Tuple["Mat", "Mat", "Mat"]:
    """SU(2) fundamental generators ``T^a = σ^a / 2`` for a = 1, 2, 3.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.5 + 15.6;
    Sakurai *Modern QM* §3.2.

    Returns:
        ``(T1, T2, T3)``: three 2×2 Hermitian traceless ``Mat`` satisfying
        ``[T^a, T^b] = i ε^{abc} T^c`` and ``tr(T^a T^b) = δ^{ab}/2``.
    """
    # spin.pauli_matrices returns the numpy-free exact 2×2 complex `Mat`
    # (v0.7.5rc115); consume them directly as the σ-blocks — no numpy, no
    # boundary coercion (this module flipped numpy-free at rc119, so the rc115
    # `.to_numpy()` Mat→ndarray coercion it formerly carried is removed).
    sx, sy, sz = pauli_matrices()
    return _scale(0.5, sx), _scale(0.5, sy), _scale(0.5, sz)


def su2_structure_constants() -> List[List[List[float]]]:
    """Levi-Civita ``ε^{abc}`` — SU(2) structure constants.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.4 (``[T^a, T^b] = i ε^{abc} T^c``).

    Returns:
        Real (3, 3, 3) nested list; ``f[a][b][c] = ε^{abc}`` (``Mat`` is 2-D
        only, so the rank-3 tensor is a plain Python nested list).
    """
    f = [[[0.0] * 3 for _ in range(3)] for _ in range(3)]
    cyclic = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]
    for a, b, c in cyclic:
        f[a][b][c] = 1.0
        f[b][a][c] = -1.0
    return f


# ----------------------------------------------------------------------
# SU(3) — Gell-Mann
# ----------------------------------------------------------------------


def su3_gell_mann_matrices() -> Tuple["Mat", ...]:
    """The eight Gell-Mann matrices ``λ^1, ..., λ^8`` (Hermitian traceless 3×3).

    Normalization: ``tr(λ^a λ^b) = 2 δ^{ab}``.

    Canonical SSoT: Gell-Mann (1962) *Phys. Rev.* 125, 1067 eq 16;
    Peskin-Schroeder eq 17.32; Schwartz §25.2.

    Returns:
        Tuple of eight 3×3 complex Hermitian traceless ``Mat``.
    """
    lam = []
    # λ^1: (1,2) real symmetric
    lam.append(Mat.from_rows([[0, 1, 0], [1, 0, 0], [0, 0, 0]], is_complex=True))
    # λ^2: (1,2) imaginary antisymmetric
    lam.append(Mat.from_rows([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]], is_complex=True))
    # λ^3: diagonal SU(2) within 1-2
    lam.append(Mat.from_rows([[1, 0, 0], [0, -1, 0], [0, 0, 0]], is_complex=True))
    # λ^4: (1,3) real
    lam.append(Mat.from_rows([[0, 0, 1], [0, 0, 0], [1, 0, 0]], is_complex=True))
    # λ^5: (1,3) imaginary
    lam.append(Mat.from_rows([[0, 0, -1j], [0, 0, 0], [1j, 0, 0]], is_complex=True))
    # λ^6: (2,3) real
    lam.append(Mat.from_rows([[0, 0, 0], [0, 0, 1], [0, 1, 0]], is_complex=True))
    # λ^7: (2,3) imaginary
    lam.append(Mat.from_rows([[0, 0, 0], [0, 0, -1j], [0, 1j, 0]], is_complex=True))
    # λ^8: diagonal hypercharge-like; the 1/√3 normaliser is the Class-N
    # rational.sqrt (libm-free).
    lam.append(_scale(
        1.0 / _srn.sqrt(3.0),
        Mat.from_rows([[1, 0, 0], [0, 1, 0], [0, 0, -2]], is_complex=True),
    ))
    return tuple(lam)


def su3_generators() -> Tuple["Mat", ...]:
    """SU(3) fundamental generators ``T^a = λ^a / 2`` for a = 1, ..., 8.

    Satisfies ``[T^a, T^b] = i f^{abc} T^c`` and ``tr(T^a T^b) = δ^{ab}/2``.

    Canonical SSoT: Peskin-Schroeder eq 17.33; Schwartz §25.2.
    """
    return tuple(_scale(0.5, lam) for lam in su3_gell_mann_matrices())


def su3_structure_constants() -> List[List[List[float]]]:
    """SU(3) structure constants ``f^{abc}`` (totally antisymmetric).

    Non-zero values (Peskin-Schroeder eq 17.34; Schwartz Table 25.1)::

        f^{123} = 1
        f^{147} = f^{246} = f^{257} = f^{345} = 1/2
        f^{156} = f^{367} = -1/2
        f^{458} = f^{678} = √3/2

    All other independent components are zero; remaining entries fill in
    by total antisymmetry.

    Returns:
        Real (8, 8, 8) nested list (``Mat`` is 2-D only, so the rank-3 tensor
        is a plain Python nested list).
    """
    f = [[[0.0] * 8 for _ in range(8)] for _ in range(8)]
    seed_values = [
        (0, 1, 2, 1.0),
        (0, 3, 6, 0.5),
        (1, 3, 5, 0.5),
        (1, 4, 6, 0.5),
        (2, 3, 4, 0.5),
        (0, 4, 5, -0.5),
        (2, 5, 6, -0.5),
        (3, 4, 7, _srn.sqrt(3.0) / 2.0),
        (5, 6, 7, _srn.sqrt(3.0) / 2.0),
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
            f[i][j][k] = sign * val
    return f


# ----------------------------------------------------------------------
# Lie algebra verification + Casimir
# ----------------------------------------------------------------------


def lie_algebra_residual(
    generators: Tuple["Mat", ...],
    structure_constants: List[List[List[float]]],
) -> float:
    """Maximum Frobenius-norm violation of ``[T^a, T^b] = i f^{abc} T^c``.

    Should be at machine precision for the canonical SU(2) and SU(3)
    constructions above.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.4.

    Args:
        generators: Tuple of n_gen Hermitian generator ``Mat``.
        structure_constants: Real (n_gen, n_gen, n_gen) nested list.

    Returns:
        Maximum Frobenius residual across all (a, b) pairs.
    """
    n_gen = len(generators)
    f = structure_constants
    if not (
        len(f) == n_gen
        and all(
            len(plane) == n_gen and all(len(row) == n_gen for row in plane)
            for plane in f
        )
    ):
        raise ValueError(
            f"lie_algebra_residual: structure_constants must be shape "
            f"({n_gen}, {n_gen}, {n_gen})"
        )
    max_residual = 0.0
    for a in range(n_gen):
        for b in range(n_gen):
            comm = _mat_sub(
                mat_matmul(generators[a], generators[b]),
                mat_matmul(generators[b], generators[a]),
            )
            # rhs = i · Σ_c f^{abc} T^c — Class-K i-phase on the real-weighted
            # Class-M sum over the generator basis.
            weighted = _mat_sum(
                [_scale(f[a][b][c], generators[c]) for c in range(n_gen)]
            )
            rhs = _scale(1j, weighted)
            max_residual = max(max_residual, mat_norm(_mat_sub(comm, rhs)))
    return max_residual


def casimir_operator(generators: Tuple["Mat", ...]) -> "Mat":
    """Quadratic Casimir ``C_2 = T^a T^a`` (sum over generators).

    By Schur's lemma, on an irreducible representation R this equals
    ``C_2(R) · I``. For the fundamental of SU(N), the eigenvalue is
    ``(N² - 1) / (2N)``: 3/4 for SU(2), 4/3 for SU(3).

    Canonical SSoT: Peskin-Schroeder §15.4 eq 15.93;
    Schwartz §25.2.

    Returns:
        Casimir as a ``Mat`` in the representation of ``generators``.
    """
    if not generators:
        raise ValueError("casimir_operator: generators tuple is empty")
    return _mat_sum([mat_matmul(T, T) for T in generators])


def casimir_eigenvalue(generators: Tuple["Mat", ...]) -> float:
    """Scalar Casimir eigenvalue ``C_2(R)`` (assumes irreducible representation).

    Equals ``trace(C_2) / dim(R)`` since ``C_2 = C_2(R) · I``.

    Canonical SSoT: Peskin-Schroeder §15.4 eq 15.93.

    Returns:
        Real positive scalar.
    """
    C2 = casimir_operator(generators)
    dim = C2.n_rows
    return float(_trace(C2).real / dim)


# ----------------------------------------------------------------------
# Holonomy / Wilson-loop primitives
# ----------------------------------------------------------------------


def gauge_connection_matrix(
    A_components: Sequence[float],
    generators: Tuple["Mat", ...],
) -> "Mat":
    """Lie-algebra connection ``A = A^a T^a`` from component vector.

    For a Yang-Mills gauge potential ``A^a_μ``, given a fixed spacetime
    component ``μ``, this returns the matrix-valued ``A_μ = A^a_μ T^a``.

    Canonical SSoT: Peskin-Schroeder §15.1 eq 15.2.

    Args:
        A_components: Real length-n_gen sequence of Lie-algebra components.
        generators: Generator ``Mat``.

    Returns:
        Hermitian ``Mat`` ``A^a T^a`` in the representation of ``generators``.
    """
    n_gen = len(generators)
    A = [float(x) for x in A_components]
    if len(A) != n_gen:
        raise ValueError(
            f"gauge_connection_matrix: A_components length {len(A)} ≠ {n_gen}"
        )
    return _mat_sum([_scale(A[a], generators[a]) for a in range(n_gen)])


def gauge_path_segment(
    A_components: Sequence[float],
    generators: Tuple["Mat", ...],
    coupling: float = 1.0,
) -> "Mat":
    """Path-segment holonomy ``U = exp(i g A^a T^a)`` along a small loop step.

    Uses the Class-L Hermitian eigendecomposition of ``M = g A^a T^a`` — for
    any Hermitian M, ``exp(i M) = V·diag(exp(i λ))·V^H`` — so no scipy
    dependency and **no numpy**. Caller composes segments via matrix
    multiplication in path order to build a Wilson loop.

    Canonical SSoT: Wilson (1974) *Phys. Rev. D* 10, 2445 eq 2.3;
    Peskin-Schroeder §15.3 eq 15.55.

    Args:
        A_components: Connection components (length n_gen).
        generators: Hermitian generator ``Mat``.
        coupling: Gauge coupling ``g`` (real).

    Returns:
        Unitary segment-holonomy ``Mat`` in the representation.
    """
    M = _scale(coupling, gauge_connection_matrix(A_components, generators))
    # Class-L Hermitian eigendecomposition (srmech's own primitive). M is a
    # complex-Hermitian connection matrix (Gell-Mann generators are complex),
    # so V stays the complex unitary Mat.
    eigvals, V = mat_hermitian_eigendecompose(M)
    # exp(iM) = V·diag(e^{iλ})·Vᴴ — the per-mode phase e^{+iλ} is the Class-N
    # rational.cexp Euler cascade (cos + i·sin), NOT np.exp; the products are
    # the Class-L mat_matmul cascade.
    n = eigvals.n_rows
    diag = [[0j] * n for _ in range(n)]
    for k in range(n):
        diag[k][k] = _srn.cexp(eigvals[k, 0])    # e^{+iλ_k}
    D = Mat.from_rows(diag, is_complex=True)
    return mat_matmul(mat_matmul(V, D), V.conj().T)


def wilson_loop_from_segments(
    A_segments: Sequence[Sequence[float]],
    generators: Tuple["Mat", ...],
    coupling: float = 1.0,
) -> "Mat":
    """Wilson loop ``U(C) = P exp(i g ∮_C A) ≈ ∏_k exp(i g A_k)``.

    Discrete path-ordered approximation: multiply segment holonomies in
    path order. Caller provides ``A_segments`` as a sequence of ``n_segments``
    rows, each row the ``n_gen`` connection components along that segment.

    Canonical SSoT: Wilson (1974) *Phys. Rev. D* 10, 2445;
    Peskin-Schroeder §15.3.

    Args:
        A_segments: Sequence of rows; row k = ``A^a`` at segment k (each a
            length-n_gen sequence). An empty sequence → the identity loop.
        generators: Hermitian generator ``Mat``.
        coupling: Gauge coupling.

    Returns:
        Unitary Wilson-loop ``Mat`` in the representation.
    """
    n_gen = len(generators)
    segments = [list(row) for row in A_segments]
    for row in segments:
        if len(row) != n_gen:
            raise ValueError(
                f"wilson_loop_from_segments: each segment must have {n_gen} "
                f"components; got {len(row)}"
            )
    dim = generators[0].n_rows
    U = _eye(dim)
    for row in segments:
        U = mat_matmul(gauge_path_segment(row, generators, coupling), U)
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
