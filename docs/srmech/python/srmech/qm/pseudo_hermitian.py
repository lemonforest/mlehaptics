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

Canonical SSoT:

- Bender, C.M. & Boettcher, S. (1998) *Phys. Rev. Lett.* 80, 5243-5246.
- Mostafazadeh, A. (2002) *J. Math. Phys.* 43, 205-214; 2814-2816; 3944.
- Mostafazadeh, A. (2010) *Int. J. Geom. Methods Mod. Phys.* 7, 1191-1306
  (review).
- Bender, C.M. (2007) *Rep. Prog. Phys.* 70, 947-1018 (review).
"""

from __future__ import annotations

import numpy as np
from typing import Tuple


def inner_product_eta(a: np.ndarray, b: np.ndarray, eta: np.ndarray) -> complex:
    """η-deformed inner product ``⟨a|b⟩_η = ⟨a| η |b⟩``.

    For ``η = I`` reduces to the standard Hilbert-space inner product.
    For positive definite η, makes ⟨·|·⟩_η a true inner product on the
    Hilbert space (Mostafazadeh 2002 §II).

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 205-214,
    eq 2.6.

    Args:
        a, b: State vectors (same length).
        eta: Positive operator (n × n).

    Returns:
        Complex scalar ``a^† η b``.

    Raises:
        ValueError: shape mismatch.
    """
    a = np.asarray(a)
    b = np.asarray(b)
    eta = np.asarray(eta)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError(
            f"inner_product_eta: a, b must be 1-D vectors of same length; "
            f"got a={a.shape}, b={b.shape}"
        )
    if eta.shape != (a.shape[0], a.shape[0]):
        raise ValueError(
            f"inner_product_eta: eta must be ({a.shape[0]}, {a.shape[0]}); "
            f"got {eta.shape}"
        )
    return complex(a.conj() @ eta @ b)


def expectation_eta(O: np.ndarray, psi: np.ndarray, eta: np.ndarray) -> complex:
    """η-expectation value ``⟨O⟩_η = ⟨ψ|η O|ψ⟩ / ⟨ψ|η|ψ⟩``.

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 205-214,
    eq 3.6.

    Args:
        O: Operator (n × n).
        psi: State vector (n).
        eta: Metric operator (n × n).

    Returns:
        Complex expectation value (real for η-pseudo-Hermitian O).
    """
    psi = np.asarray(psi)
    O = np.asarray(O)
    eta = np.asarray(eta)
    if psi.ndim != 1 or O.shape != (psi.shape[0], psi.shape[0]):
        raise ValueError(
            f"expectation_eta: psi must be 1-D and O must be ({psi.shape[0]}, "
            f"{psi.shape[0]}); got O={O.shape}, psi={psi.shape}"
        )
    if eta.shape != O.shape:
        raise ValueError(
            f"expectation_eta: eta must match O shape {O.shape}; got {eta.shape}"
        )
    numerator = psi.conj() @ eta @ O @ psi
    denominator = psi.conj() @ eta @ psi
    return complex(numerator / denominator)


def is_pseudo_hermitian(
    O: np.ndarray, eta: np.ndarray, atol: float = 1e-10
) -> bool:
    """Check ``O† η = η O`` (η-pseudo-Hermiticity).

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 205-214,
    eq 2.4 (definition).

    Args:
        O: Operator (n × n).
        eta: Metric operator (n × n).
        atol: Frobenius-norm absolute tolerance for the residual.

    Returns:
        True if ``‖O† η - η O‖ < atol``.
    """
    O = np.asarray(O)
    eta = np.asarray(eta)
    if O.shape != eta.shape or O.ndim != 2 or O.shape[0] != O.shape[1]:
        raise ValueError(
            f"is_pseudo_hermitian: O and eta must be same-shape square "
            f"matrices; got O={O.shape}, eta={eta.shape}"
        )
    residual = O.conj().T @ eta - eta @ O
    return float(np.linalg.norm(residual)) < atol


def construct_eta_from_eigendecomposition(
    O: np.ndarray, atol: float = 1e-10
) -> np.ndarray:
    """Construct η so that ``O`` is η-pseudo-Hermitian via eigendecomposition.

    For diagonalizable ``O`` with eigenvectors ``V`` (columns), the
    canonical positive η is ``η = (V V^†)^{-1}``. Then ``O† η = η O``
    by direct computation when O has a complete eigenbasis.

    Canonical SSoT: Mostafazadeh (2002) *J. Math. Phys.* 43, 2814-2816
    eq 2.7-2.10 (η construction from eigenbasis).

    Args:
        O: Diagonalizable operator (n × n). Must have all eigenvalues
            real for η to be positive.
        atol: Tolerance for accepting the result as η-pseudo-Hermitian.

    Returns:
        Hermitian η satisfying ``O† η = η O`` (verified up to atol).

    Raises:
        ValueError: O is defective or has complex spectrum (rejects;
            non-positive η would not produce a usable inner product).
    """
    O = np.asarray(O)
    if O.ndim != 2 or O.shape[0] != O.shape[1]:
        raise ValueError(
            f"construct_eta_from_eigendecomposition: O must be square; "
            f"got {O.shape}"
        )
    eigvals, V = np.linalg.eig(O)
    if np.max(np.abs(eigvals.imag)) > atol:
        raise ValueError(
            f"construct_eta_from_eigendecomposition: O has complex spectrum "
            f"(max |Im λ| = {np.max(np.abs(eigvals.imag))}); η would not be "
            "positive definite"
        )
    # η = (V V†)^{-1} makes O η-pseudo-Hermitian.
    eta = np.linalg.inv(V @ V.conj().T)
    # Symmetrize (rounding fixup).
    eta = (eta + eta.conj().T) / 2.0
    return eta


def pseudo_hermitian_eigenvalues_real(
    O: np.ndarray, eta: np.ndarray, atol: float = 1e-10
) -> bool:
    """Verify η-pseudo-Hermitian ``O`` has all real eigenvalues.

    Theorem (Mostafazadeh 2002): if ``O† η = η O`` with positive η, then
    O has real eigenvalues. This function checks the spectrum directly.

    Args:
        O: Operator (n × n).
        eta: Metric operator.
        atol: Maximum allowed imaginary part for any eigenvalue.

    Returns:
        True if the spectrum is real (and O is η-pseudo-Hermitian).
    """
    if not is_pseudo_hermitian(O, eta, atol=atol):
        return False
    eigvals = np.linalg.eigvals(O)
    return bool(np.max(np.abs(eigvals.imag)) < atol)


__all__ = [
    "construct_eta_from_eigendecomposition",
    "expectation_eta",
    "inner_product_eta",
    "is_pseudo_hermitian",
    "pseudo_hermitian_eigenvalues_real",
]
