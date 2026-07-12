"""η-pseudo-Hermitian QM and PT-symmetric framework.

Closes the framework gap surfaced by chess-spectral's ADR-005 (η-metric
pawn observable) — see `docs/srmech/notes/task_218_phase_c2_chess_spectral_qm_audit_2026-05-15.md`.

Per ``[[feedback_science_is_ssot_not_project]]``: sourced from canonical
non-Hermitian-QM literature, not from chess-spectral's stubbed
implementation. Chess-spectral becomes a *substrate-consumer* of these
primitives when ADR-005 is finished.

A linear operator ``O`` is **η-pseudo-Hermitian** with respect to a
positive operator ``η`` iff::

    O† η = η O    (equivalently, η^{-1} O† η = O).

This is the Mostafazadeh (2002) generalization that admits real-spectrum
operators that are not standardly Hermitian. The η-inner-product

    ⟨a|b⟩_η := ⟨a|η|b⟩

makes η-pseudo-Hermitian operators "η-Hermitian" — they have real
eigenvalues, orthogonal eigenvectors under ⟨·|·⟩_η, and unitary evolution
preserves the η-norm.

PT-symmetric operators (Bender & Boettcher 1998) are a subset: those
commuting with the antiunitary PT operator. Under unbroken PT symmetry,
PT-symmetric Hamiltonians have real spectra and admit an η of the form
η = C P (with C the "C operator").

**Carrier (v0.7.5rc124, #564):** numpy-free. Matrices are the framework-native
2-D :class:`srmech.amsc.mat.Mat`; state vectors are plain ``complex`` lists
(``Mat`` is 2-D only). Every linear-algebra step routes through the Class-L
``mat_*`` family — ``mat_matmul`` for the matvec/sandwich/Gram contractions,
``mat_eigvals`` for the spectrum, ``mat_solve`` for the (well-conditioned HPD)
metric inverse — and ``mat_norm`` for residuals. The η construction needs the
eigen*vectors* of a general (non-Hermitian, real-spectrum) operator: each is the
null vector of ``O − λI`` computed by deterministic Gaussian elimination (no
ill-conditioned shifted solve). Class-K magnitudes use an explicit sign-branch
(no ``abs()``).

Canonical SSoT:

- Bender, C.M. & Boettcher, S. (1998) *Phys. Rev. Lett.* 80, 5243-5246.
- Mostafazadeh, A. (2002) *J. Math. Phys.* 43, 205-214; 2814-2816; 3944.
- Mostafazadeh, A. (2010) *Int. J. Geom. Methods Mod. Phys.* 7, 1191-1306
  (review).
- Bender, C.M. (2007) *Rep. Prog. Phys.* 70, 947-1018 (review).
"""

from __future__ import annotations

from typing import List, Sequence

from srmech.amsc.mat import Mat
from srmech.amsc.laplacian import (
    mat_eigvals,
    mat_hermitian_eigendecompose,
    mat_matmul,
    mat_norm,
    mat_solve,
)


def _as_mat(m) -> "Mat":
    """Coerce a ``Mat`` (passthrough) or a list-of-rows into a complex ``Mat``."""
    if isinstance(m, Mat):
        return m
    return Mat.from_rows([[complex(x) for x in row] for row in m], is_complex=True)


def _matvec(m: "Mat", v: Sequence[complex]) -> List[complex]:
    """Class-L matvec ``m·v`` over a plain complex list (Mat is 2-D only)."""
    n_rows, n_cols = m.shape
    assert n_cols == len(v), "matvec: shape mismatch"
    return [sum((m[i, j] * v[j] for j in range(n_cols)), 0j) for i in range(n_rows)]


def _dagger_dot(a: Sequence[complex], w: Sequence[complex]) -> complex:
    """Class-L sesquilinear dot ``aᴴ·w = Σ conj(aᵢ)·wᵢ``."""
    assert len(a) == len(w), "dot: length mismatch"
    return sum((a[i].conjugate() * w[i] for i in range(len(a))), 0j)


def _im_magnitude(z: complex) -> float:
    """|Im z| via an explicit Class-K sign-branch (no ``abs()``)."""
    im = z.imag
    return im if im >= 0.0 else -im


def inner_product_eta(
    a: Sequence[complex], b: Sequence[complex], eta
) -> complex:
    """η-deformed inner product ``⟨a|b⟩_η = ⟨a| η |b⟩``.

    For ``η = I`` reduces to the standard Hilbert-space inner product.
    For positive definite η, makes ⟨·|·⟩_η a true inner product on the
    Hilbert space (Mostafazadeh 2002 §II).

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 205-214,
    eq 2.6.

    Args:
        a, b: State vectors (plain complex sequences, same length).
        eta: Positive operator (n × n :class:`Mat` or list-of-rows).

    Returns:
        Complex scalar ``aᴴ η b``.

    Raises:
        ValueError: shape mismatch.
    """
    eta = _as_mat(eta)
    if len(a) != len(b):
        raise ValueError(
            f"inner_product_eta: a, b must be vectors of same length; "
            f"got a={len(a)}, b={len(b)}"
        )
    n = len(a)
    if eta.shape != (n, n):
        raise ValueError(
            f"inner_product_eta: eta must be ({n}, {n}); got {eta.shape}"
        )
    # ⟨a|η|b⟩ = aᴴ·(η·b): Class-L matvec then Class-L sesquilinear dot.
    return _dagger_dot(a, _matvec(eta, b))


def expectation_eta(O, psi: Sequence[complex], eta) -> complex:
    """η-expectation value ``⟨O⟩_η = ⟨ψ|η O|ψ⟩ / ⟨ψ|η|ψ⟩``.

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 205-214,
    eq 3.6.

    Args:
        O: Operator (n × n :class:`Mat` or list-of-rows).
        psi: State vector (plain complex sequence, length n).
        eta: Metric operator (n × n).

    Returns:
        Complex expectation value (real for η-pseudo-Hermitian O).
    """
    O = _as_mat(O)
    eta = _as_mat(eta)
    n = len(psi)
    if O.shape != (n, n):
        raise ValueError(
            f"expectation_eta: psi length {n} and O must be ({n}, {n}); "
            f"got O={O.shape}"
        )
    if eta.shape != O.shape:
        raise ValueError(
            f"expectation_eta: eta must match O shape {O.shape}; got {eta.shape}"
        )
    # ⟨ψ|ηO|ψ⟩ / ⟨ψ|η|ψ⟩ — each contraction is a Class-L matvec/dot cascade.
    numerator = _dagger_dot(psi, _matvec(eta, _matvec(O, psi)))
    denominator = _dagger_dot(psi, _matvec(eta, psi))
    return complex(numerator / denominator)


def is_pseudo_hermitian(O, eta, atol: float = 1e-10) -> bool:
    """Check ``O† η = η O`` (η-pseudo-Hermiticity).

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 205-214,
    eq 2.4 (definition).

    Args:
        O: Operator (n × n :class:`Mat` or list-of-rows).
        eta: Metric operator (n × n).
        atol: Frobenius-norm absolute tolerance for the residual.

    Returns:
        True if ``‖O† η - η O‖ < atol``.
    """
    O = _as_mat(O)
    eta = _as_mat(eta)
    if O.shape != eta.shape or O.shape[0] != O.shape[1]:
        raise ValueError(
            f"is_pseudo_hermitian: O and eta must be same-shape square "
            f"matrices; got O={O.shape}, eta={eta.shape}"
        )
    n = O.shape[0]
    lhs = mat_matmul(O.conj().T, eta)   # O† η
    rhs = mat_matmul(eta, O)            # η O
    residual = Mat.from_rows(
        [[lhs[i, j] - rhs[i, j] for j in range(n)] for i in range(n)],
        is_complex=True,
    )
    return float(mat_norm(residual)) < atol


def _null_vector(rows: List[List[complex]], n: int) -> List[complex]:
    """A null vector of the (rank-(n−1)) matrix ``rows`` via the C-backed Gram
    Hermitian eigendecomposition (the standalone-ready null-space route).

    For an operator with a simple eigenvalue λ, ``M = O − λI`` has a
    one-dimensional null space spanned by the eigenvector. The null direction is
    the right-singular vector of ``M`` with the smallest singular value —
    equivalently the eigenvector of the Hermitian PSD Gram matrix ``G = Mᴴ M`` for
    its smallest eigenvalue. Both the Gram product and the Hermitian
    eigendecomposition route through the ``c_dispatched`` Class-L carriers
    (:func:`mat_matmul` = ``srmech_dense_matmul_complex`` +
    :func:`mat_hermitian_eigendecompose` = ``srmech_hermitian_eigendecompose_ws``),
    so a bare-C host reproduces this null-space with **no extra kernel** — the
    same SVD/Gram-eig null-space pattern the so(8) subalgebra builders
    (:func:`srmech.qm.so8._svd_nullspace`) use, per
    ``[[feedback_cascade_svd_nullspace_accuracy_not_route_matrix_rank]]``. This
    replaces the former hand-rolled float Gaussian-elimination RREF (a Python-only
    kernel with no C twin). Ascending eigenvalues ⇒ column 0 of the eigenvector
    matrix is the smallest-eigenvalue (null) direction.
    """
    m = Mat.from_rows(
        [[complex(rows[i][j]) for j in range(n)] for i in range(n)],
        is_complex=True,
    )
    gram = mat_matmul(m.conj().T, m)                 # Mᴴ M — Hermitian PSD (c_dispatched)
    _evals, v_cols = mat_hermitian_eigendecompose(gram)   # ascending λ; c_dispatched
    return [v_cols[i, 0] for i in range(n)]          # smallest-λ eigenvector = null dir


def construct_eta_from_eigendecomposition(O, atol: float = 1e-10):
    """Construct η so that ``O`` is η-pseudo-Hermitian via eigendecomposition.

    For diagonalizable ``O`` with eigenvectors ``V`` (columns), the
    canonical positive η is ``η = (V V†)^{-1}``. Then ``O† η = η O``
    by direct computation when O has a complete eigenbasis (and the identity
    holds for any column scaling of V).

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 2814-2816
    eq 2.7-2.10 (η construction from eigenbasis).

    Args:
        O: Diagonalizable operator (n × n :class:`Mat` or list-of-rows). Must
            have all eigenvalues real for η to be positive.
        atol: Tolerance for accepting an eigenvalue's imaginary part as zero.

    Returns:
        Hermitian η (:class:`Mat`) satisfying ``O† η = η O``.

    Raises:
        ValueError: O has complex spectrum (rejects; non-positive η would not
            produce a usable inner product).
    """
    O = _as_mat(O)
    if O.shape[0] != O.shape[1]:
        raise ValueError(
            f"construct_eta_from_eigendecomposition: O must be square; "
            f"got {O.shape}"
        )
    n = O.shape[0]
    eigvals = mat_eigvals(O)
    max_im = max((_im_magnitude(lam) for lam in eigvals), default=0.0)
    if max_im > atol:
        raise ValueError(
            f"construct_eta_from_eigendecomposition: O has complex spectrum "
            f"(max |Im λ| = {max_im}); η would not be positive definite"
        )
    o_rows = [[O[i, j] for j in range(n)] for i in range(n)]
    # V columns = eigenvectors (null vector of O − λI, real part of λ used —
    # the spectrum is real to within atol).
    cols: List[List[complex]] = []
    for lam in eigvals:
        shifted = [
            [o_rows[i][j] - (lam.real if i == j else 0.0) for j in range(n)]
            for i in range(n)
        ]
        cols.append(_null_vector(shifted, n))
    v = Mat.from_rows(
        [[cols[j][i] for j in range(n)] for i in range(n)], is_complex=True
    )
    # η = (V V†)^{-1}: V V† is HPD (simple spectrum ⟹ V invertible) ⟹ the solve
    # is well-conditioned (no rank-deficiency, unlike a general companion solve).
    gram = mat_matmul(v, v.conj().T)
    identity = Mat.from_rows(
        [[1.0 + 0j if i == j else 0j for j in range(n)] for i in range(n)],
        is_complex=True,
    )
    eta = mat_solve(gram, identity)
    # Symmetrize (rounding fixup): η ← (η + η†)/2.
    eta_h = eta.conj().T
    return Mat.from_rows(
        [[(eta[i, j] + eta_h[i, j]) / 2.0 for j in range(n)] for i in range(n)],
        is_complex=True,
    )


def pseudo_hermitian_eigenvalues_real(O, eta, atol: float = 1e-10) -> bool:
    """Verify η-pseudo-Hermitian ``O`` has all real eigenvalues.

    Theorem (Mostafazadeh 2002): if ``O† η = η O`` with positive η, then
    O has real eigenvalues. This function checks the spectrum directly.

    Args:
        O: Operator (n × n :class:`Mat` or list-of-rows).
        eta: Metric operator.
        atol: Maximum allowed imaginary part for any eigenvalue.

    Returns:
        True if the spectrum is real (and O is η-pseudo-Hermitian).
    """
    O = _as_mat(O)
    eta = _as_mat(eta)
    if not is_pseudo_hermitian(O, eta, atol=atol):
        return False
    eigvals = mat_eigvals(O)
    max_im = max((_im_magnitude(lam) for lam in eigvals), default=0.0)
    return bool(max_im < atol)


__all__ = [
    "construct_eta_from_eigendecomposition",
    "expectation_eta",
    "inner_product_eta",
    "is_pseudo_hermitian",
    "pseudo_hermitian_eigenvalues_real",
]
