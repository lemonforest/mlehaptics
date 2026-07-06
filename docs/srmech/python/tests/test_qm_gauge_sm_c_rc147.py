"""BATCH B8c (rc147) — C-composition parity for the 9 gauge / bell / sm / misc
``qm`` ops (``qm_exact_assembly`` part 3 — CLOSES B8).

The 9 ops all move ``python_only_debt`` → ``composition_of_c`` (ceiling 53 → 44)
with **NO new C symbol** (ABI stays 3). Every op is a pure composition of the
already-C-backed matrix algebra — the ``c_dispatched`` ``laplacian.mat_matmul``
(``srmech_dense_matmul_complex``) + ``mat_hermitian_eigendecompose`` + the rc141
C carrier ops ``srmech_mat_{add,sub,scale}`` that back the ``Mat`` ``+ - *``
operators + the ``composition_of_c`` ``laplacian.mat_norm`` (whose only dispatch
is the Class-N ``rational.sqrt`` C kernel) + the Class-N ``rational.{sqrt,cos,
sin,cexp}`` byte-exact integer-cascade C ports.

Two honest sub-classes (verified EMPIRICALLY, not assumed):

* **6 BYTE-IDENTICAL (+ ckm now float-invariant, FMA-sensitive)** — ``chsh_pauli_combination`` / ``chsh_operator`` /
  ``casimir_operator`` / ``lie_algebra_residual`` /
  ``harmonic_oscillator_hamiltonian`` / ``single_particle.commutator`` /
  ``ckm_unitarity_residual``. The C ``srmech_dense_matmul_complex`` accumulates
  the real / imag parts SEPARATELY over ``p = 0 .. k−1`` — bit-for-bit the same
  reduction CPython's ``complex`` ``s += a*b`` performs — and the ``rational.
  {sqrt,cos,sin}`` C kernels are byte-exact ports of the pure integer cascades,
  so the native path is **byte-identical** to forced-pure EVEN for the
  irrational-valued entries (``σ_z⊗σ_z``'s ``1/√2``; ``λ⁸``'s ``1/√3``; the
  ladder ``√n``; the CKM ``cos/sin``). Two are exact-integer (``chsh_pauli_
  combination``, ``commutator`` on Pauli input); four are float-VALUED yet
  byte-identical native==pure. (Honest: ``ckm_unitarity_residual``'s value is a
  small ~1e-16 FLOAT — unitarity holds to float precision, NOT exact-zero — but
  its native-vs-pure PARITY is FLOAT-INVARIANT (FMA-sensitive, NOT byte-exact); ``lie_algebra_residual`` is
  exact-``0.0`` when the algebra holds.)
* **3 FLOAT-INVARIANT (incl. ckm — FMA-sensitive)** — ``gauge_path_segment`` / ``wilson_loop_from_
  segments`` build the Wilson-line holonomy ``exp(iM) = V·diag(e^{iλ})·Vᴴ``
  through the C-backed ``mat_hermitian_eigendecompose`` (``srmech_jacobi_*``) ∘
  the Class-N ``rational.cexp`` Euler phase ∘ ``mat_matmul`` — the SAME
  ``composition_of_c`` float-eigenbasis pattern as the rc146 so7 / an_embedding
  ops. The Jacobi eigenBASIS is non-unique, so native vs forced-pure agree on
  every INVARIANT (unitarity ``U·Uᴴ = I``, and — since ``exp(iM)`` is itself
  basis-INDEPENDENT — the reconstructed holonomy within the accepted ~1e-9
  carrier shift), NOT element-wise byte-for-byte.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import contextlib
import struct

import pytest

from srmech.amsc import _native
from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.qm import bell, gauge, potentials, single_particle, sm
from srmech.qm.spin import pauli_matrices


requires_native = pytest.mark.skipif(
    not (_native.HAS_NATIVE and _native.LIB is not None
         and hasattr(_native.LIB, "srmech_dense_matmul_complex")),
    reason="rc147 B8c native parity needs srmech_dense_matmul_complex; on a "
    "no-C host the pure-Python cascade is the complete, identical alternative.",
)

_TOL = 1e-9


# ── deterministic serialisation for the byte-exact comparison ─────────────────
def _ser(x, out):
    if isinstance(x, Mat):
        out.append(x.tobytes())
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
    """Disable native dispatch so every carrier op (mat_matmul / the Mat
    +,-,* carrier ops / mat_norm's rational.sqrt / rational.{cos,sin,cexp})
    takes its pure-Python fallback — the forced-pure reference."""
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


# The generator / matrix fixtures are built ONCE (in native mode) so the byte
# comparison isolates the OP's native-vs-pure dispatch (the fixed input is
# identical in both runs).
_SU2_G = gauge.su2_generators()
_SU2_F = gauge.su2_structure_constants()
_SU3_G = gauge.su3_generators()
_SU3_F = gauge.su3_structure_constants()
_SX, _SY, _SZ = pauli_matrices()
_CKM_V = sm.ckm_matrix(0.2265, 0.0037, 0.0405, 1.2)   # PDG-scale Wolfenstein angles


# ── the 8 BYTE-IDENTICAL fixtures (6 ops; ckm moved to float-invariant) ──────────────────────────────────────────────────
_BYTE_EXACT = {
    "chsh_pauli_combination": bell.chsh_pauli_combination,
    "chsh_operator": bell.chsh_operator,
    "casimir_operator[su2]": lambda: gauge.casimir_operator(_SU2_G),
    "casimir_operator[su3]": lambda: gauge.casimir_operator(_SU3_G),
    "lie_algebra_residual[su2]": lambda: gauge.lie_algebra_residual(_SU2_G, _SU2_F),
    "lie_algebra_residual[su3]": lambda: gauge.lie_algebra_residual(_SU3_G, _SU3_F),
    "harmonic_oscillator_hamiltonian": lambda: potentials.harmonic_oscillator_hamiltonian(8, 1.3),
    "commutator[pauli]": lambda: single_particle.commutator(_SX, _SY),
    # NOTE: ckm_unitarity_residual is NOT in _BYTE_EXACT — its 3-term V†V
    # accumulation over generic-float CKM entries is FMA-sensitive (macOS clang
    # fuses a*b+c to one rounding; the pure path uses two), so native-vs-pure is
    # byte-identical on Linux but diverges ~1 ULP on macOS. It is a genuine
    # FLOAT-INVARIANT op (within-tol parity below), NOT byte-exact.
}


@requires_native
@pytest.mark.parametrize("name", sorted(_BYTE_EXACT))
def test_byte_exact_native_equals_forced_pure(name):
    """Each of the 6 ops (8 fixtures incl. the su2/su3 pairs): native (C matmul /
    carrier ops / byte-exact rational.{sqrt,cos,sin} ports) is BYTE-IDENTICAL to
    the forced-pure fallback — for the exact-integer AND the float-VALUED ops
    alike (the C reductions are bit-for-bit mirrors of the pure cascades)."""
    native, pure = _native_then_pure(_BYTE_EXACT[name])
    assert _blob(native) == _blob(pure), f"{name}: native != forced-pure bytes"


# ── value / structural oracles (guard a value wrong in BOTH dispatch paths) ────
@requires_native
def test_chsh_norm_identities():
    """‖σ_x⊗σ_x + σ_z⊗σ_z‖ = 2 (integer spectrum) and ‖B_CHSH‖ = 2√2 (Tsirelson)
    — the framework identity signature holds after the rc147 C-carrier routing."""
    pc = bell.chsh_pauli_combination()
    # Hermitian, integer entries {0, ±1, ±2}; operator norm exactly 2.
    assert abs(bell.operator_norm(pc) - 2.0) < 1e-12
    op = bell.chsh_operator()
    # Hermitian (B_CHSH = B_CHSH†) and ‖B_CHSH‖ = 2√2.
    herm = mat_norm([op[i, j] - op[j, i].conjugate()
                     for i in range(4) for j in range(4)])
    assert herm == 0.0
    assert abs(bell.chsh_operator_norm() - bell.tsirelson_bound()) < 1e-12


@requires_native
def test_lie_algebra_residual_exact_zero_su2():
    """[T^a, T^b] = i ε^{abc} T^c holds EXACTLY for the dyadic SU(2) generators —
    the residual is exact ``0.0`` (not a float floor), byte-identical native==pure.
    SU(3) (with λ⁸'s 1/√3) holds to ~1e-16 and is likewise byte-identical."""
    native, pure = _native_then_pure(lambda: gauge.lie_algebra_residual(_SU2_G, _SU2_F))
    assert native == 0.0 and pure == 0.0
    n3, p3 = _native_then_pure(lambda: gauge.lie_algebra_residual(_SU3_G, _SU3_F))
    assert n3 < 1e-14 and n3 == p3


@requires_native
def test_casimir_eigenvalues():
    """C_2 = T^a T^a = C_2(R)·I with C_2 = (N²−1)/(2N): 3/4 for SU(2), 4/3 for
    SU(3) — Schur's lemma (Peskin-Schroeder §15.4)."""
    assert abs(gauge.casimir_eigenvalue(_SU2_G) - 0.75) < 1e-12
    assert abs(gauge.casimir_eigenvalue(_SU3_G) - 4.0 / 3.0) < 1e-12


@requires_native
def test_harmonic_oscillator_spectrum():
    """H = ω(a†a + ½): diagonal ω(n+½). The ladder √n rides the byte-exact
    Class-N rational.sqrt, so the Hamiltonian is byte-identical native==pure and
    the diagonal is exactly ω(n+½) for ω=2 → [1,3,5,...] (n+½ integer-doubled)."""
    H = potentials.harmonic_oscillator_hamiltonian(6, 2.0)
    for n in range(6):
        assert abs(H[n, n].real - 2.0 * (n + 0.5)) < 1e-12
        assert abs(H[n, n].imag) < 1e-15


@requires_native
def test_commutator_pauli_identity():
    """[σ_x, σ_y] = 2i σ_z (Sakurai §1.4) — exact Gaussian-integer matmul."""
    comm = single_particle.commutator(_SX, _SY)
    expect = [[2j, 0j], [0j, -2j]]
    for i in range(2):
        for j in range(2):
            assert comm[i, j] == expect[i][j]


@requires_native
def test_ckm_residual_is_small_float_not_exact_zero():
    """V V† − I: unitarity holds to FLOAT precision (~1e-16) — a small float, NOT
    exact-zero (honest: the CKM matrix is built from irrational cos/sin, so the
    residual is a genuine float floor). native-vs-pure PARITY is FLOAT-INVARIANT
    (within-tol), NOT byte-identical: the 3-term V†V accumulation over generic-
    float entries is FMA-sensitive (byte-identical on Linux, ~1 ULP on macOS)."""
    r = sm.ckm_unitarity_residual(_CKM_V)
    assert 0.0 < r < 1e-12    # small but genuinely nonzero (not exact-0)
    # native-vs-pure agree to float tol (FLOAT-INVARIANT, not byte-exact)
    native, pure = _native_then_pure(lambda: sm.ckm_unitarity_residual(_CKM_V))
    assert abs(native - pure) < 1e-12


# ── the 2 FLOAT-COMPOSITION ops — unitarity invariant + within-tol parity ─────
def _unitarity_dev(U: Mat) -> float:
    n = U.n_rows
    UUh = mat_matmul(U, U.conj().T)
    return mat_norm([UUh[i, j] - (1.0 if i == j else 0.0)
                     for i in range(n) for j in range(n)])


def _elt_dev(a: Mat, b: Mat) -> float:
    n, m = a.n_rows, a.n_cols
    return mat_norm([a[i, j] - b[i, j] for i in range(n) for j in range(m)])


@requires_native
def test_gauge_path_segment_float_invariant_parity():
    """gauge_path_segment U = exp(iM) composes mat_hermitian_eigendecompose ∘
    rational.cexp ∘ mat_matmul; native & forced-pure each yield a UNITARY holonomy
    and — since exp(iM) is basis-independent — agree within the ~1e-9 eigen carrier
    shift (NOT element bytes: the Jacobi basis is free)."""
    native, pure = _native_then_pure(
        lambda: gauge.gauge_path_segment([0.3, 0.5, 0.2], _SU2_G, 1.0))
    assert _unitarity_dev(native) < _TOL
    assert _unitarity_dev(pure) < _TOL
    assert _elt_dev(native, pure) < _TOL


@requires_native
def test_wilson_loop_float_invariant_parity():
    """wilson_loop_from_segments = ∏ gauge_path_segment: a product of unitaries is
    unitary; native & forced-pure agree within the ~1e-9 carrier shift."""
    segs = [[0.3, 0.5, 0.2], [0.1, 0.0, 0.4]]
    native, pure = _native_then_pure(
        lambda: gauge.wilson_loop_from_segments(segs, _SU2_G, 1.0))
    assert _unitarity_dev(native) < _TOL
    assert _unitarity_dev(pure) < _TOL
    assert _elt_dev(native, pure) < _TOL


def test_numpy_is_absent():
    """The whole B8c path runs with numpy uninstalled (carrier-native)."""
    import sys
    assert "numpy" not in sys.modules
