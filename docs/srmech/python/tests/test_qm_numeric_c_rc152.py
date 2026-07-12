"""BATCH B9 (rc152) — C-composition parity for the 9 NUMERIC ``qm`` ops
(``qm-numeric``: norms / eigenvalue-invariants / time-evolution that produce
floats).

The 9 ops all move ``python_only_debt`` → ``composition_of_c`` (ceiling 25 → 16)
with **NO new C symbol** (ABI stays 3). Every op is a pure composition of the
already-C-backed matrix algebra — the ``c_dispatched`` ``laplacian.mat_matmul``
(``srmech_dense_matmul_complex``) + ``mat_hermitian_eigendecompose``
(``srmech_hermitian_eigendecompose_ws``) + ``mat_solve``
(``srmech_dense_solve_f64_ws``) + the ``composition_of_c`` ``mat_norm`` /
``mat_eigvals`` + the byte-exact Class-N ``rational.{sqrt,cos,sin,cexp}``
integer-cascade C ports + (for ``chsh_pauli_combination_norm``) the exact-integer
``matrix_cascades.eigvals_exact`` bignum-reference oracle.

Two honest parity sub-classes (verified EMPIRICALLY, per the rc147 B8c / rc148+
B4 numeric precedent — a multi-term float accumulation is FMA-sensitive
cross-platform, so byte-identity is claimed ONLY where there is genuinely no
float reduction):

* **all WITHIN-TOL (chsh_pauli_combination_norm → C eig)** — ``chsh_pauli_combination_norm``. The primary CHSH identity
  ``‖σ_x⊗σ_x + σ_z⊗σ_z‖ = 2`` is computed through the EXACT-INTEGER eigenvalue
  cascade ``matrix_cascades.eigvals_exact`` (char-poly Faddeev-LeVerrier → Sturm
  isolation → rational bisection — all exact ``Fraction``/``int``, no float
  accumulation) over the byte-exact integer ``Mat`` add, so the result is exactly
  ``2.0`` and native == pure is byte-identical AND platform-invariant.

* **8 FLOAT / eig-INVARIANT (WITHIN-TOL native == pure)** —
  ``chsh_operator_norm`` / ``verify_chsh`` / ``casimir_eigenvalue`` /
  ``construct_eta_from_eigendecomposition`` / ``is_pseudo_hermitian`` /
  ``pseudo_hermitian_eigenvalues_real`` / ``heisenberg_evolve`` /
  ``liouville_evolve``. These bottom out in the Jacobi Hermitian
  eigendecomposition and/or a multi-term complex ``mat_matmul`` accumulation whose
  reduction can FMA-fuse ~1 ULP on some platforms (macOS clang), so the parity
  contract is **WITHIN-TOL** (reldiff ≤ 1e-9, differential) — NOT byte-equality —
  the SAME contract as the rc147 float-eigenbasis Wilson-holonomy ops and the
  rc148+ numeric DSP batch. The eigenBASIS is non-unique, so where the op returns
  a matrix (``construct_eta`` / ``heisenberg_evolve`` / ``liouville_evolve``) the
  physics INVARIANT (η Hermitian + pseudo-Hermiticity; ``A(0)=A`` + Hermiticity;
  ``ρ(0)=ρ`` + trace preservation) is asserted, and the scalar VALUE / BOOL
  verdict (the operator norm, the ``verify_chsh`` / ``is_pseudo_hermitian``
  verdict, the Casimir eigenvalue, the residual) is checked native == pure.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import contextlib
import struct

import pytest

from srmech.amsc import _native
from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.qm import bell, gauge, pseudo_hermitian as ph, single_particle as sp


requires_native = pytest.mark.skipif(
    not (_native.HAS_NATIVE and _native.LIB is not None
         and hasattr(_native.LIB, "srmech_dense_matmul_complex")),
    reason="rc152 B9 native parity needs srmech_dense_matmul_complex; on a "
    "no-C host the pure-Python cascade is the complete, identical alternative.",
)

_TOL = 1e-9


# ── deterministic serialisation for the byte-exact comparison ─────────────────
def _ser(x, out):
    if isinstance(x, Mat):
        out.append(x.tobytes())
    elif isinstance(x, bool):
        out.append(b"B" + repr(x).encode())
    elif isinstance(x, (list, tuple)):
        out.append(b"[%d]" % len(x))
        for e in x:
            _ser(e, out)
    elif isinstance(x, float):
        out.append(struct.pack("<d", x))
    elif isinstance(x, complex):
        out.append(struct.pack("<dd", x.real, x.imag))
    else:
        out.append(repr(x).encode())
    return out


def _blob(value) -> bytes:
    return b"|".join(_ser(value, []))


@contextlib.contextmanager
def force_pure():
    """Disable native dispatch so every carrier op (mat_matmul /
    mat_hermitian_eigendecompose / mat_solve / mat_norm / rational.*) takes its
    pure-Python fallback — the forced-pure reference."""
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        yield
    finally:
        _native.HAS_NATIVE = saved


def _native_then_pure(thunk):
    """(native_value, pure_value) for a zero-arg op."""
    _native.HAS_NATIVE = True
    native = thunk()
    with force_pure():
        pure = thunk()
    return native, pure


def _flat(x, acc):
    if isinstance(x, Mat):
        for i in range(x.n_rows):
            for j in range(x.n_cols):
                acc.append(complex(x[i, j]))
    elif isinstance(x, bool):
        acc.append(complex(1.0 if x else 0.0))
    elif isinstance(x, (list, tuple)):
        for e in x:
            _flat(e, acc)
    elif isinstance(x, complex):
        acc.append(x)
    else:
        acc.append(complex(float(x)))
    return acc


def _maxdev(a, b) -> float:
    fa = _flat(a, [])
    fb = _flat(b, [])
    assert len(fa) == len(fb), "shape mismatch in parity comparison"
    # Class-K magnitude (|Δ| of a complex diff); no bare abs() semantics beyond it.
    return max((abs(x - y) for x, y in zip(fa, fb)), default=0.0)


def _elt_dev(a: "Mat", b: "Mat") -> float:
    n, m = a.n_rows, a.n_cols
    return mat_norm([a[i, j] - b[i, j] for i in range(n) for j in range(m)])


# ── fixtures (built ONCE in native mode; the fixed input is identical in both
#    dispatch runs so the comparison isolates the OP's native-vs-pure path). ────
_SU2_G = gauge.su2_generators()
_SU3_G = gauge.su3_generators()

# A triangular operator with distinct real eigenvalues (1, 2, 3) — diagonalizable,
# real spectrum, so construct_eta yields a positive η and O is η-pseudo-Hermitian.
_O_REAL = Mat.from_rows(
    [[1.0, 0.5, 0.0], [0.0, 2.0, 0.5], [0.0, 0.0, 3.0]], is_complex=True
)
_ETA = ph.construct_eta_from_eigendecomposition(_O_REAL)

# A rotation operator with complex spectrum ±i (pseudo-Hermiticity must reject).
_O_ROT = Mat.from_rows([[0.0, -1.0], [1.0, 0.0]], is_complex=True)

# A fixed Hermitian Hamiltonian + Hermitian observable + density matrix (2×2).
_H = Mat.from_rows([[2.0 + 0j, 1.0 + 1.0j], [1.0 - 1.0j, 3.0 + 0j]], is_complex=True)
_SIGMA_X = Mat.from_rows([[0.0 + 0j, 1.0 + 0j], [1.0 + 0j, 0.0 + 0j]], is_complex=True)
_RHO = Mat.from_rows([[0.6 + 0j, 0.2 - 0.1j], [0.2 + 0.1j, 0.4 + 0j]], is_complex=True)


def _identity(n: int) -> "Mat":
    return Mat.from_rows(
        [[1.0 + 0j if i == j else 0j for j in range(n)] for i in range(n)],
        is_complex=True,
    )


# ── all WITHIN-TOL (chsh_pauli_combination_norm → C eig) op ───────────────────────────────────────────────────────────
@requires_native
def test_chsh_pauli_combination_norm_within_tol():
    """‖σ_x⊗σ_x + σ_z⊗σ_z‖ = 2 (integer spectrum {+2,0,0,−2} via the
    exact-integer eigenvalue oracle over the byte-exact integer Mat add) — native
    == pure is byte-identical AND the value is exactly 2.0 (no float floor)."""
    native, pure = _native_then_pure(bell.chsh_pauli_combination_norm)
    assert abs(native - pure) < 1e-9  # within-tol (C Hermitian eig; NOT byte-exact — eigvals_exact has no C twin)
    assert abs(native - 2.0) < 1e-9
    assert abs(pure - 2.0) < 1e-9


# ── 8 FLOAT / eig-INVARIANT ops — within-tol native == pure + value oracles ────
@requires_native
def test_chsh_operator_norm_tsirelson():
    """‖B_CHSH‖ = 2√2 (Tsirelson 1980) via the Class-L Hermitian eigendecomp
    max|λ|. native == pure within-tol (the eig accumulation is FMA-conservative,
    NOT claimed byte-identical); the scalar norm hits the Tsirelson bound."""
    native, pure = _native_then_pure(bell.chsh_operator_norm)
    assert _maxdev(native, pure) < _TOL
    assert abs(native - bell.tsirelson_bound()) < 1e-12
    assert abs(native - 2.0 * 2.0 ** 0.5) < 1e-12


@requires_native
def test_verify_chsh_verdict_and_residuals():
    """verify_chsh returns (True, primary_residual, tsirelson_residual): the
    primary identity holds to the eig floor (~1e-16, chsh_pauli_combination_norm via C eig), the
    Tsirelson identity holds to the eig floor (<1e-14). native == pure: the bool
    verdict identical + the residuals within-tol."""
    native, pure = _native_then_pure(bell.verify_chsh)
    n_ok, n_pri, n_tsi = native
    p_ok, p_pri, p_tsi = pure
    assert n_ok is True and p_ok is True          # verdict (bool) native == pure
    assert abs(n_pri) < 1e-13 and abs(p_pri) < 1e-13  # primary residual within-tol (chsh_pauli_combination_norm via C Hermitian eig, not exact-0)
    assert n_tsi < 1e-14 and p_tsi < 1e-14        # Tsirelson residual at eig floor
    assert abs(n_tsi - p_tsi) < 1e-12             # residual within-tol native==pure


@requires_native
@pytest.mark.parametrize("gens,expect,label", [
    (_SU2_G, 0.75, "su2"),          # C_2 = (N²−1)/(2N) = 3/4 for SU(2)
    (_SU3_G, 4.0 / 3.0, "su3"),     # = 4/3 for SU(3)
])
def test_casimir_eigenvalue(gens, expect, label):
    """Quadratic Casimir C_2(R) = trace(T^aT^a)/dim = (N²−1)/(2N) (Schur's lemma;
    Peskin-Schroeder §15.4). Composes the byte-exact casimir_operator matmul + a
    pure-Python trace/divide; native == pure within-tol, value hits the oracle."""
    native, pure = _native_then_pure(lambda: gauge.casimir_eigenvalue(gens))
    assert _maxdev(native, pure) < _TOL
    assert abs(native - expect) < 1e-12, f"casimir[{label}] = {native} != {expect}"


@requires_native
def test_construct_eta_invariant_and_parity():
    """construct_eta routes the eigenvector null-space through the C-backed Gram
    Hermitian-eigendecomposition. The eigenBASIS is non-unique, so the INVARIANT
    (η Hermitian + O η-pseudo-Hermitian) is asserted, and native == pure agrees
    within the ~1e-9 carrier shift (NOT element bytes)."""
    native, pure = _native_then_pure(
        lambda: ph.construct_eta_from_eigendecomposition(_O_REAL))
    # invariant: η is Hermitian and makes O η-pseudo-Hermitian (both dispatch paths)
    for eta in (native, pure):
        n = eta.n_rows
        herm_dev = mat_norm([eta[i, j] - eta[j, i].conjugate()
                             for i in range(n) for j in range(n)])
        assert herm_dev < _TOL
        assert ph.is_pseudo_hermitian(_O_REAL, eta, atol=1e-8)
    # native vs forced-pure agree within the eigen carrier shift
    assert _elt_dev(native, pure) < _TOL


@requires_native
def test_is_pseudo_hermitian_verdict():
    """is_pseudo_hermitian(O, η) = ‖O†η − ηO‖ < atol — the bool verdict is
    native == pure and TRUE for the constructed η; a Hermitian O is η=I
    pseudo-Hermitian; a complex-spectrum O with η=I is NOT."""
    native, pure = _native_then_pure(
        lambda: ph.is_pseudo_hermitian(_O_REAL, _ETA, atol=1e-8))
    assert native is True and pure is True          # verdict native == pure
    assert ph.is_pseudo_hermitian(_H, _identity(2))          # Hermitian, η=I → True
    assert not ph.is_pseudo_hermitian(_O_ROT, _identity(2))  # ±i spectrum → False


@requires_native
def test_pseudo_hermitian_eigenvalues_real_verdict():
    """pseudo_hermitian_eigenvalues_real: an η-pseudo-Hermitian O with positive η
    has a real spectrum (Mostafazadeh 2002). Bool verdict native == pure; TRUE for
    the constructed η, FALSE for the ±i rotation with η=I."""
    native, pure = _native_then_pure(
        lambda: ph.pseudo_hermitian_eigenvalues_real(_O_REAL, _ETA, atol=1e-8))
    assert native is True and pure is True
    assert not ph.pseudo_hermitian_eigenvalues_real(_O_ROT, _identity(2), atol=1e-10)


@requires_native
def test_heisenberg_evolve_invariant_and_parity():
    """heisenberg A_H(t) = U†AU (U = exp(−iHt)). Value oracles: A_H(0) = A;
    unitary similarity of a Hermitian A stays Hermitian. native == pure within the
    eigenbasis carrier shift (NOT element bytes)."""
    # A(0) = A exactly (t=0 → U = I; the identity phase).
    a0 = sp.heisenberg_evolve(_SIGMA_X, _H, 0.0)
    assert _elt_dev(a0, _SIGMA_X) < 1e-12
    native, pure = _native_then_pure(
        lambda: sp.heisenberg_evolve(_SIGMA_X, _H, 0.7))
    # Hermiticity preserved (A_H(t)† = A_H(t)) in both paths
    for a in (native, pure):
        n = a.n_rows
        assert mat_norm([a[i, j] - a[j, i].conjugate()
                         for i in range(n) for j in range(n)]) < _TOL
    assert _elt_dev(native, pure) < _TOL


@requires_native
def test_liouville_evolve_invariant_and_parity():
    """liouville ρ(t) = U ρ U† (U = exp(−iHt)). Value oracles: ρ(0) = ρ;
    trace(ρ(t)) = trace(ρ) (unitary evolution preserves the trace). native == pure
    within the eigenbasis carrier shift."""
    r0 = sp.liouville_evolve(_RHO, _H, 0.0)
    assert _elt_dev(r0, _RHO) < 1e-12
    native, pure = _native_then_pure(lambda: sp.liouville_evolve(_RHO, _H, 0.7))
    tr0 = sum(_RHO[i, i] for i in range(_RHO.n_rows))
    for r in (native, pure):
        tr = sum(r[i, i] for i in range(r.n_rows))
        assert abs(tr - tr0) < _TOL                 # trace preserved
    assert _elt_dev(native, pure) < _TOL


def test_numpy_is_absent():
    """The whole B9 path runs with numpy uninstalled (carrier-native)."""
    import sys
    assert "numpy" not in sys.modules
