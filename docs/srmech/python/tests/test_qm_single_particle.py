"""Tests for srmech.qm.single_particle.

numpy-FREE (v0.7.5rc117, #564): the single-particle ops hold their working
matrices in :class:`~srmech.amsc.mat.Mat` and return ``Mat`` / plain
``complex`` lists; these tests use **no numpy** — Hermitian inputs come from
a tiny deterministic PRNG, the time-evolution phase from the Class-N
``rational`` cascade, and every assertion is a canonical *physical identity*
(norm / energy / trace / hermiticity / unitarity preservation), NOT
element-wise parity against a numpy oracle (numpy is never a validation
reference per ``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

from __future__ import annotations

import pytest

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.qm import single_particle as sp


# ----------------------------------------------------------------------
# numpy-free fixtures + helpers
# ----------------------------------------------------------------------


def _lcg(seed: int):
    """Tiny deterministic PRNG → floats in [-1, 1) (numpy-free)."""
    state = (seed * 2654435761 + 12345) & 0x7FFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield (state / 0x3FFFFFFF) - 1.0


def _hermitian(n: int, seed: int) -> "Mat":
    """A deterministic complex-Hermitian (n, n) ``Mat`` — H = (A + Aᴴ)/2."""
    g = _lcg(seed)
    a = [[complex(next(g), next(g)) for _ in range(n)] for _ in range(n)]
    h = [
        [(a[i][j] + complex(a[j][i]).conjugate()) / 2.0 for j in range(n)]
        for i in range(n)
    ]
    return Mat.from_rows(h, is_complex=True)


def _vec_norm(v) -> float:
    """‖v‖₂ via the Class-N sqrt cascade (numpy-free)."""
    s = 0.0
    for x in v:
        z = complex(x)
        s += z.real * z.real + z.imag * z.imag
    return _srn.sqrt(s)


def _unit(n: int, seed: int):
    """A deterministic normalized complex vector (numpy-free) as a plain list."""
    g = _lcg(seed + 777)
    v = [complex(next(g), next(g)) for _ in range(n)]
    nrm = _vec_norm(v)
    return [x / nrm for x in v]


def _matvec(m: "Mat", v):
    """``M·v`` → plain list (numpy-free, via the native mat_matmul)."""
    col = Mat.from_rows([[x] for x in v], is_complex=True)
    out = mat_matmul(m, col)
    return [out[i, 0] for i in range(out.n_rows)]


def _vdot(a, b) -> complex:
    """⟨a|b⟩ = Σ conj(a_i)·b_i (numpy-free)."""
    return sum(complex(a[i]).conjugate() * b[i] for i in range(len(a)))


def _expectation(h: "Mat", psi) -> float:
    """⟨ψ|H|ψ⟩ real part (numpy-free)."""
    return _vdot(psi, _matvec(h, psi)).real


def _max_abs_diff(a: "Mat", b: "Mat") -> float:
    """max |a[i,j] − b[i,j]| over two same-shape ``Mat`` (numpy-free)."""
    return max(
        abs(a[i, j] - b[i, j])
        for i in range(a.n_rows)
        for j in range(a.n_cols)
    )


def _max_dev_identity(m: "Mat") -> float:
    """max |m[i,j] − δ_ij| over a square ``Mat`` (numpy-free)."""
    return max(
        abs(m[i, j] - (1.0 if i == j else 0.0))
        for i in range(m.n_rows)
        for j in range(m.n_cols)
    )


def _trace_real(m: "Mat") -> float:
    return sum(complex(m[i, i]).real for i in range(m.n_rows))


def _eye(n: int) -> "Mat":
    return Mat.from_rows(
        [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)], is_complex=True
    )


# ----------------------------------------------------------------------
# tdse_evolve
# ----------------------------------------------------------------------


def test_tdse_zero_time_identity():
    n = 6
    H = _hermitian(n, 0)
    psi = _unit(n, 1)
    psi_0 = sp.tdse_evolve(H, psi, 0.0)
    assert max(abs(psi_0[i] - psi[i]) for i in range(n)) < 1e-12


def test_tdse_preserves_norm():
    n = 8
    H = _hermitian(n, 2)
    psi = _unit(n, 3)
    for t in (0.1, 0.5, 1.0, 5.0, 10.0):
        psi_t = sp.tdse_evolve(H, psi, t)
        assert abs(_vec_norm(psi_t) - 1.0) < 1e-9


def test_tdse_preserves_energy():
    """⟨H⟩ is conserved under TDSE evolution (H is time-independent)."""
    n = 7
    H = _hermitian(n, 4)
    psi = _unit(n, 5)
    E0 = _expectation(H, psi)
    for t in (0.3, 1.5, 4.7):
        psi_t = sp.tdse_evolve(H, psi, t)
        assert abs(_expectation(H, psi_t) - E0) < 1e-9


def test_tdse_evolves_eigenstate_with_phase():
    """An eigenstate evolves as exp(-iE t) |E⟩ — only a global phase."""
    n = 5
    H = _hermitian(n, 6)
    eigvals, V = sp.tise_solve(H)
    psi0 = [V[i, 2] for i in range(n)]            # third eigenstate (column 2)
    lam = eigvals[2, 0]
    psi_t = sp.tdse_evolve(H, psi0, 1.3)
    phase = _srn.cexp(-(lam * 1.3))               # e^{-iλt} (Class-N cascade)
    expected = [phase * psi0[i] for i in range(n)]
    assert max(abs(psi_t[i] - expected[i]) for i in range(n)) < 1e-9


# ----------------------------------------------------------------------
# tise_solve
# ----------------------------------------------------------------------


def test_tise_orthonormal_eigenvectors():
    n = 6
    H = _hermitian(n, 7)
    _eigvals, V = sp.tise_solve(H)
    # Vᴴ·V = I (numpy-free, via the native mat_matmul).
    assert _max_dev_identity(mat_matmul(V.conj().T, V)) < 1e-10


def test_tise_satisfies_eigen_relation():
    n = 8
    H = _hermitian(n, 8)
    eigvals, V = sp.tise_solve(H)
    for k in range(n):
        vk = [V[i, k] for i in range(n)]
        Hvk = _matvec(H, vk)
        lam = eigvals[k, 0]
        assert max(abs(Hvk[i] - lam * vk[i]) for i in range(n)) < 1e-9


def test_tise_eigenvalues_ascending():
    n = 10
    H = _hermitian(n, 9)
    eigvals, _V = sp.tise_solve(H)
    for i in range(n - 1):
        assert eigvals[i + 1, 0] - eigvals[i, 0] >= -1e-12


# ----------------------------------------------------------------------
# commutator
# ----------------------------------------------------------------------


def test_commutator_self_zero():
    A = _hermitian(5, 10)
    assert mat_norm(sp.commutator(A, A)) < 1e-12


def test_commutator_antisymmetric():
    A = _hermitian(4, 11)
    B = _hermitian(4, 12)
    ab = sp.commutator(A, B)
    ba = sp.commutator(B, A)
    # [A,B] = -[B,A] → max |ab[i,j] + ba[i,j]| ~ 0.
    assert max(
        abs(ab[i, j] + ba[i, j]) for i in range(4) for j in range(4)
    ) < 1e-12


def test_commutator_with_identity_zero():
    A = _hermitian(6, 13)
    I = _eye(6)
    assert mat_norm(sp.commutator(A, I)) < 1e-12


# ----------------------------------------------------------------------
# heisenberg_evolve
# ----------------------------------------------------------------------


def test_heisenberg_zero_time_identity():
    n = 5
    A = _hermitian(n, 14)
    H = _hermitian(n, 15)
    assert _max_abs_diff(sp.heisenberg_evolve(A, H, 0.0), A) < 1e-10


def test_heisenberg_commutes_with_self():
    """If A = H, A_H(t) = H always (H is conserved in Heisenberg picture)."""
    n = 6
    H = _hermitian(n, 16)
    for t in (0.1, 1.0, 5.0):
        H_t = sp.heisenberg_evolve(H, H, t)
        assert _max_abs_diff(H_t, H) < 1e-9


# ----------------------------------------------------------------------
# lattice_momentum
# ----------------------------------------------------------------------


def test_lattice_momentum_hermitian():
    p = sp.lattice_momentum(16, dx=0.1)
    assert _max_abs_diff(p, p.conj().T) < 1e-14


def test_lattice_momentum_zero_diagonal():
    p = sp.lattice_momentum(20)
    assert max(abs(p[i, i]) for i in range(20)) < 1e-14


def test_lattice_momentum_invalid_n():
    with pytest.raises(ValueError):
        sp.lattice_momentum(1)


def test_lattice_momentum_invalid_dx():
    with pytest.raises(ValueError):
        sp.lattice_momentum(10, dx=0.0)


# ----------------------------------------------------------------------
# density_matrix
# ----------------------------------------------------------------------


def test_density_matrix_trace_normalized():
    psi = _unit(8, 17)
    rho = sp.density_matrix(psi)
    assert abs(_trace_real(rho) - 1.0) < 1e-13


def test_density_matrix_hermitian():
    psi = _unit(6, 18)
    rho = sp.density_matrix(psi)
    assert _max_abs_diff(rho, rho.conj().T) < 1e-14


def test_density_matrix_pure_idempotent():
    """For a pure state, ρ² = ρ."""
    psi = _unit(5, 19)
    rho = sp.density_matrix(psi)
    assert _max_abs_diff(mat_matmul(rho, rho), rho) < 1e-12


# ----------------------------------------------------------------------
# liouville_evolve
# ----------------------------------------------------------------------


def test_liouville_preserves_trace():
    n = 6
    H = _hermitian(n, 20)
    psi = _unit(n, 21)
    rho = sp.density_matrix(psi)
    for t in (0.0, 0.5, 2.0):
        rho_t = sp.liouville_evolve(rho, H, t)
        assert abs(_trace_real(rho_t) - 1.0) < 1e-9


def test_liouville_preserves_purity():
    """A pure state stays pure under unitary evolution."""
    n = 5
    H = _hermitian(n, 22)
    psi = _unit(n, 23)
    rho = sp.density_matrix(psi)
    rho_t = sp.liouville_evolve(rho, H, 1.7)
    assert _max_abs_diff(mat_matmul(rho_t, rho_t), rho_t) < 1e-9


def test_liouville_zero_time_identity():
    n = 4
    H = _hermitian(n, 24)
    psi = _unit(n, 25)
    rho = sp.density_matrix(psi)
    assert _max_abs_diff(sp.liouville_evolve(rho, H, 0.0), rho) < 1e-10
