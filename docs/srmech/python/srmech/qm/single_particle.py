"""Canonical single-particle QM operations (numpy-free).

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites
canonical physics literature.

numpy-FREE (v0.7.5rc117, #564): the working matrices are held in the
framework-native :class:`~srmech.amsc.mat.Mat` carrier and every
linear-algebra step routes through the Class-L ``mat_*`` family
(:func:`~srmech.amsc.laplacian.mat_matmul` and
:func:`~srmech.amsc.laplacian.mat_hermitian_eigendecompose`, native dense
kernels with a pure-Python cascade fallback) — **no numpy**. State vectors
are plain Python sequences of ``complex`` (``Mat`` is 2-D only); the
per-mode time-evolution phase ``e^{-iλt}`` is the substrate-native Class-N
``rational.cexp`` (Euler cascade ``cos + i·sin``), **not** ``np.exp``.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: these
substrate-coupling operations act on Hilbert-space content; the
LoE-content itself lives at 1D_t per MFO §VII.1.2.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import mat_hermitian_eigendecompose, mat_matmul
from srmech.amsc.mat import Mat


# ----------------------------------------------------------------------
# numpy-free Mat / vector helpers
# ----------------------------------------------------------------------


def _matvec(m: "Mat", v: Sequence[complex]) -> List[complex]:
    """``M·v`` for a ``Mat`` ``M`` and a plain vector ``v`` → plain list.

    Routes through :func:`mat_matmul` (native dense kernel / pure-Python
    cascade fallback) by treating ``v`` as an ``(n, 1)`` column ``Mat`` —
    numpy-free, the 2-D carrier standing in for the absent ``mat_matvec``.
    """
    col = Mat.from_rows([[x] for x in v], is_complex=True)
    out = mat_matmul(m, col)
    return [out[i, 0] for i in range(out.n_rows)]


def _mat_sub(a: "Mat", b: "Mat") -> "Mat":
    """``A − B`` element-wise as a new ``Mat`` (numpy-free)."""
    rows = [[a[i, j] - b[i, j] for j in range(a.n_cols)] for i in range(a.n_rows)]
    return Mat.from_rows(rows, is_complex=a.is_complex or b.is_complex)


def _phase_diag(eigvals: "Mat", t: float) -> "Mat":
    """``diag(e^{-iλt})`` as an ``(n, n)`` complex ``Mat``.

    ``eigvals`` is the ``(n, 1)`` **real** ``Mat`` from
    :func:`mat_hermitian_eigendecompose`; each phase is the Class-N
    ``rational.cexp`` Euler cascade (``e^{-iλt} = cexp(−λt)``), not ``np.exp``.
    """
    n = eigvals.n_rows
    rows = [[0j] * n for _ in range(n)]
    for i in range(n):
        rows[i][i] = _srn.cexp(-(eigvals[i, 0] * t))
    return Mat.from_rows(rows, is_complex=True)


# ----------------------------------------------------------------------
# operations
# ----------------------------------------------------------------------


def tdse_evolve(H: "Mat", psi: Sequence[complex], t: float) -> List[complex]:
    """Closed-form Time-Dependent Schrödinger evolution.

    Solves ``iℏ ∂_t ψ = H ψ`` (ℏ = 1) via eigenbasis-diagonal closed form:
    ``ψ(t) = V·diag(exp(-iλt))·V^H ψ(0)`` where ``(λ, V) = eigh(H)``.

    Canonical SSoT: Schrödinger (1926) *Annalen der Physik* 79, 489;
    Sakurai *Modern QM* §2.1.5 eq 2.1.40; Cohen-Tannoudji *QM* §III.D.2.

    Args:
        H: Hermitian Hamiltonian (n × n ``Mat``).
        psi: Initial state, a length-n sequence of complex amplitudes.
        t: Evolution time (in units of ℏ / energy).

    Returns:
        ψ(t) as a length-n list of ``complex``.
    """
    n = H.n_rows
    if H.n_cols != n:
        raise ValueError(f"tdse_evolve: H must be square; got shape {H.shape}")
    if len(psi) != n:
        raise ValueError(
            f"tdse_evolve: psi length {len(psi)} incompatible with H shape {H.shape}"
        )
    # Class-L Hermitian eigendecomposition (srmech's own primitive). H is a
    # general complex-Hermitian Hamiltonian, so V is the complex unitary Mat.
    eigvals, V = mat_hermitian_eigendecompose(H)
    psi_eig = _matvec(V.conj().T, psi)            # Vᴴ·ψ  (Class-L matvec cascade)
    # e^{-iλt} per-mode phase via the Class-N Euler cascade (rational.cexp).
    phases = [_srn.cexp(-(eigvals[k, 0] * t)) for k in range(n)]
    psi_t_eig = [phases[k] * psi_eig[k] for k in range(n)]
    return _matvec(V, psi_t_eig)                  # V·(...)  (Class-L matvec cascade)


def tise_solve(H: "Mat") -> Tuple["Mat", "Mat"]:
    """Time-Independent Schrödinger Equation ``H ψ_n = E_n ψ_n``.

    Canonical SSoT: Schrödinger (1926) *Annalen der Physik* 79, 361;
    Sakurai *Modern QM* §2.1.3; Griffiths *Intro QM* §2.1.

    Args:
        H: Hermitian Hamiltonian (n × n ``Mat``).

    Returns:
        ``(eigvals, eigvecs)``: the ``(n, 1)`` **real** ``Mat`` of ascending
        eigenvalues and the ``(n, n)`` **complex** unitary ``Mat`` whose columns
        are the orthonormal eigenvectors — exactly the
        :func:`mat_hermitian_eigendecompose` contract (this op *is* the
        Hermitian eigenproblem).
    """
    n = H.n_rows
    if H.n_cols != n:
        raise ValueError(f"tise_solve: H must be square; got shape {H.shape}")
    # Class-L Hermitian eigendecomposition (srmech's own primitive).
    return mat_hermitian_eigendecompose(H)


def commutator(A: "Mat", B: "Mat") -> "Mat":
    """Operator commutator ``[A, B] = A B - B A``.

    Canonical SSoT: Sakurai *Modern QM* §1.4 eq 1.4.6.
    """
    if A.shape != B.shape or A.n_rows != A.n_cols:
        raise ValueError(
            f"commutator: A and B must be square and same shape; "
            f"got {A.shape} vs {B.shape}"
        )
    # Class-L matmul cascade throughout; numpy-free Mat subtraction.
    return _mat_sub(mat_matmul(A, B), mat_matmul(B, A))


def heisenberg_evolve(A: "Mat", H: "Mat", t: float) -> "Mat":
    """Heisenberg-picture operator evolution ``A_H(t) = U†(t) A U(t)``.

    With ``U(t) = exp(-iHt/ℏ)`` and ℏ = 1. Equivalent to integrating the
    Heisenberg equation ``dA_H/dt = (i/ℏ) [H, A_H]``.

    Canonical SSoT: Sakurai *Modern QM* §2.2 eq 2.2.15; Heisenberg (1925)
    *Zeitschrift für Physik* 33, 879.

    Args:
        A: Operator to evolve (n × n ``Mat``).
        H: Hermitian Hamiltonian (n × n ``Mat``).
        t: Evolution time.

    Returns:
        ``A_H(t)`` as an (n, n) complex ``Mat``.
    """
    if A.shape != H.shape:
        raise ValueError(
            f"heisenberg_evolve: A and H must have same shape; "
            f"got A={A.shape} vs H={H.shape}"
        )
    # Class-L Hermitian eigendecomposition (srmech's own primitive).
    eigvals, V = mat_hermitian_eigendecompose(H)
    D = _phase_diag(eigvals, t)                    # diag(e^{-iλt}) — Class-N cexp
    # U = V·diag(phases)·Vᴴ, then A_H = Uᴴ·A·U — Class-L matmul cascade throughout.
    U = mat_matmul(mat_matmul(V, D), V.conj().T)
    Uh = U.conj().T
    return mat_matmul(mat_matmul(Uh, A), U)


def lattice_momentum(n: int, dx: float = 1.0) -> "Mat":
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
        Hermitian (n, n) momentum operator as a complex ``Mat``.
    """
    if n < 2:
        raise ValueError(f"lattice_momentum: n must be ≥ 2; got {n}")
    if dx <= 0:
        raise ValueError(f"lattice_momentum: dx must be positive; got {dx}")
    rows = [[0j] * n for _ in range(n)]
    coef = 1j / (2.0 * dx)
    for i in range(n):
        rows[i][(i + 1) % n] = -coef
        rows[i][(i - 1) % n] = coef
    return Mat.from_rows(rows, is_complex=True)


def density_matrix(psi: Sequence[complex]) -> "Mat":
    """Pure-state density matrix ``ρ = |ψ⟩⟨ψ|``.

    Canonical SSoT: von Neumann (1932) *Mathematische Grundlagen*;
    Sakurai *Modern QM* §3.4 eq 3.4.7.

    Args:
        psi: State vector, a length-n sequence of complex amplitudes
            (should be normalized).

    Returns:
        Density matrix as an (n, n) complex ``Mat``, Hermitian PSD with
        trace = ⟨ψ|ψ⟩.
    """
    n = len(psi)
    if n == 0:
        raise ValueError("density_matrix: psi must be a non-empty sequence")
    # ρ = |ψ⟩⟨ψ| = outer(ψ, conj(ψ)) via the column·row Class-L matmul cascade.
    col = Mat.from_rows([[complex(psi[i])] for i in range(n)], is_complex=True)      # (n,1)
    row = Mat.from_rows(
        [[complex(psi[j]).conjugate() for j in range(n)]], is_complex=True           # (1,n)
    )
    return mat_matmul(col, row)


def liouville_evolve(rho: "Mat", H: "Mat", t: float) -> "Mat":
    """Liouville-von Neumann evolution ``ρ(t) = U(t) ρ(0) U†(t)``.

    Equivalent to integrating ``iℏ ∂_t ρ = [H, ρ]``.

    Canonical SSoT: von Neumann (1932) *Mathematische Grundlagen*;
    Sakurai *Modern QM* §3.4.2 eq 3.4.28.

    Args:
        rho: Initial density matrix (n × n ``Mat``).
        H: Hermitian Hamiltonian (n × n ``Mat``).
        t: Evolution time.

    Returns:
        ρ(t) as an (n, n) complex ``Mat``.
    """
    if rho.shape != H.shape:
        raise ValueError(
            f"liouville_evolve: rho and H must have same shape; "
            f"got rho={rho.shape} vs H={H.shape}"
        )
    # Class-L Hermitian eigendecomposition (srmech's own primitive).
    eigvals, V = mat_hermitian_eigendecompose(H)
    D = _phase_diag(eigvals, t)                    # diag(e^{-iλt}) — Class-N cexp
    # U = V·diag(phases)·Vᴴ, then ρ(t) = U·ρ·Uᴴ — Class-L matmul cascade throughout.
    U = mat_matmul(mat_matmul(V, D), V.conj().T)
    return mat_matmul(mat_matmul(U, rho), U.conj().T)


__all__ = [
    "commutator",
    "density_matrix",
    "heisenberg_evolve",
    "lattice_momentum",
    "liouville_evolve",
    "tdse_evolve",
    "tise_solve",
]
