"""Canonical single-particle QM operations (numpy-free).

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites
canonical physics literature.

numpy-FREE (v0.7.5rc117, #564): the working matrices are held in the
framework-native :class:`~srmech.math.mat.Mat` carrier and every
linear-algebra step routes through the Class-L ``mat_*`` family
(:func:`~srmech.math.laplacian.mat_matmul` and
:func:`~srmech.math.laplacian.mat_hermitian_eigendecompose`, native dense
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

from srmech.math import rational as _srn
from srmech.math.laplacian import mat_hermitian_eigendecompose, mat_matmul
from srmech.math.mat import Mat
from srmech.physics.qm.quaternion import quaternion_twiddle as _quaternion_twiddle

# The four quarter-turn roots of unity ``exp(2πi·m/4)`` for m = 0, 1, 2, 3 —
# exact Gaussian integers ``{1, i, −1, −i}``. The literal signs ARE the Class-K
# pin-slot phase boundary baked into the table (no ``abs()``, no float trig).
_QUARTER_TURNS = (1 + 0j, 1j, -1 + 0j, -1j)


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


def _root_of_unity(k: int, n: int) -> complex:
    """``ω^k = exp(2πi·k/n)`` — the ``k``-th power of the primitive ``n``-th root
    of unity ``ω = e^{2πi/n}``; equivalently the ``k``-th DFT twiddle factor.

    EXACT Gaussian-integer value (``{1, i, −1, −i}``) whenever the phase is a
    whole number of quarter-turns (``4k ≡ 0 mod n``): the angle is an integer
    multiple of 90°, a pure Class-C reorientation with no transcendental part.
    This is why the ``n = 2`` and ``n = 4`` clocks are bit-exact (they reduce to
    ``σ_z`` and ``diag(1, i, −1, −i)``), and why every ``n = 8`` entry whose
    phase lands on a quarter-turn is exact too.

    A genuine sub-quarter angle (``n = 3``, ``n = 5``, the odd ``n = 8`` entries)
    is the DFT twiddle ``exp(σ·μ·2πjk/N)`` at ``j = 1``, ``σ = +1``, ``μ = i`` —
    so it routes through srmech's OWN C-backed roots-of-unity primitive
    :func:`~srmech.physics.qm.quaternion.quaternion_twiddle` (``srmech_quaternion_twiddle``):
    the index is reduced in the cyclic group ``Z_n`` FIRST (Class I), then π
    enters ONCE as the Class-N ``4·atan(1)`` cascade at the float64 boundary —
    the same boundary :func:`lattice_momentum`'s ``sin(2πk/n)`` spectrum sits on,
    and NEVER stdlib ``cmath`` / ``math``.
    """
    k %= n
    quarters = 4 * k
    if quarters % n == 0:                      # whole quarter-turns → exact
        return _QUARTER_TURNS[(quarters // n) % 4]
    # sub-quarter angle → the C-backed DFT twiddle exp(+i·2πk/n) = [cos, sin, 0, 0]
    tw = _quaternion_twiddle(1, k, n, mu="i", sigma=1)
    return complex(tw[0], tw[1])


def clock_operator(n: int) -> "Mat":
    """The Weyl **clock** operator ``U = diag(ω^k)``, ``ω = e^{2πi/n}``, ``k = 0..n−1``.

    This is the topology-respecting **position** ``x̂`` on a ring of ``n`` sites.
    A naive linear ``x̂ = diag(k·dx)`` is multi-valued on a periodic lattice — it
    jumps at the seam ``n−1 → 0`` — so it is physically wrong; the single-valued
    stand-in is the phase-position clock, whose eigenvalue winds once around the
    unit circle and closes. ``U`` is unitary with ``U**n = I``. Its partner is
    :func:`shift_operator` ``V`` (the group-level momentum / one-site
    translation), and together they obey the **Weyl commutation relation**

        ``U V = ω V U``

    — the compact, finite-dimensional form of the canonical ``[x̂, p̂] = iℏ``.
    At ``n = 2`` the clock IS ``σ_z``; at ``n = 4`` it is ``diag(1, i, −1, −i)``
    (both bit-exact — see :func:`_root_of_unity`).

    RESONANCE — clock and shift are the two eigenbases of ONE transform srmech
    already computes exactly in C. The exact DFT (:func:`srmech.cascade.exact_dft`,
    ``c_dispatched``) is the change of basis ``F`` that rotates the clock
    (position) eigenbasis into the shift (momentum) eigenbasis: ``F V Fᴴ = U``.
    So this op adds NO new machinery — its diagonal entries ARE that transform's
    roots-of-unity twiddle factors, and the sub-quarter ones are read straight
    off the C-backed ``quaternion_twiddle`` (see :func:`_root_of_unity`).

    Canonical SSoT: Schwinger, J. (1960) "Unitary Operator Bases",
    *Proc. Natl. Acad. Sci. USA* **46**, 570–579 (the clock-and-shift finite QM);
    Weyl, H. (1931) *The Theory of Groups and Quantum Mechanics*, Dover
    (the commutation relation).

    Args:
        n: Number of ring sites (Hilbert-space dimension); ``n ≥ 2``.

    Returns:
        The ``(n, n)`` diagonal unitary clock ``U`` as a complex ``Mat``.

    Raises:
        ValueError: ``n < 2``.
    """
    if n < 2:
        raise ValueError(f"clock_operator: n must be ≥ 2; got {n}")
    rows = [[0j] * n for _ in range(n)]
    for k in range(n):
        rows[k][k] = _root_of_unity(k, n)
    return Mat.from_rows(rows, is_complex=True)


def shift_operator(n: int) -> "Mat":
    """The Weyl **shift** operator ``V`` — the cyclic one-site translation
    ``V|k⟩ = |k+1 mod n⟩`` on a ring of ``n`` sites.

    This is the group-level **momentum**: ``V`` is the exponentiated generator
    of translation, the finite-lattice partner of the continuous ``p̂`` that
    :func:`lattice_momentum` differentiates. As a matrix ``V[i, j] = 1`` iff
    ``i ≡ j+1 (mod n)`` (unit sub-diagonal plus the top-right corner that closes
    the ring), a real permutation matrix carried as complex. ``V`` is unitary
    with ``V**n = I`` (exactly, for every ``n`` — the entries are integers).
    With the clock ``U`` of :func:`clock_operator` it satisfies the Weyl relation
    ``U V = ω V U`` (``ω = e^{2πi/n}``), the compact form of ``[x̂, p̂] = iℏ``. At
    ``n = 2`` the shift IS ``σ_x``, and ``i·(V·U) = σ_y`` — the chirality third
    ``Y = iXZ`` falls straight out of the shipped Pauli surface.

    Canonical SSoT: Schwinger, J. (1960) "Unitary Operator Bases",
    *Proc. Natl. Acad. Sci. USA* **46**, 570–579 (the clock-and-shift finite QM);
    Weyl, H. (1931) *The Theory of Groups and Quantum Mechanics*, Dover.

    Args:
        n: Number of ring sites (Hilbert-space dimension); ``n ≥ 2``.

    Returns:
        The ``(n, n)`` cyclic-shift unitary ``V`` as a complex ``Mat``.

    Raises:
        ValueError: ``n < 2``.
    """
    if n < 2:
        raise ValueError(f"shift_operator: n must be ≥ 2; got {n}")
    rows = [[0j] * n for _ in range(n)]
    for j in range(n):
        rows[(j + 1) % n][j] = 1 + 0j          # V|j⟩ = |j+1 mod n⟩
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
    "clock_operator",
    "commutator",
    "density_matrix",
    "heisenberg_evolve",
    "lattice_momentum",
    "liouville_evolve",
    "shift_operator",
    "tdse_evolve",
    "tise_solve",
]
