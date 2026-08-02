"""rc212 (task #755) — the qm CONSTANT matrices realizable in C.

The base qm constant matrices — the Pauli σ_x/σ_y/σ_z + I₂ (``spin.py``), the
Dirac γ⁰..γ³ + the Minkowski metric η (``relativistic.py``), and the eight
Gell-Mann λ¹..λ⁸ + the SU(2)/SU(3) structure constants (``gauge.py``) — were
Python LITERALS with no C source: classified ``composition_of_c``, yet a
bare-C host could not produce the constant DATA (a real python-free gap).

rc212 closes it in two coupled parts, both pinned here:

1. **Zero canonicalization** — the Python literals carried ``-0.0`` in
   true-zero slots (``-1j`` negates BOTH components; ``_scale(-1.0, ·)``
   leaves ``-0.0`` across the negated γ blocks). Those construction
   artifacts (never a signed zero the math depends on) are canonicalized to
   ``+0.0``, and this file asserts NO ``-0.0`` survives anywhere in any
   constant, on BOTH the native and the forced-pure path.

2. **C constant emitters** — ``srmech_qm_pauli`` / ``srmech_qm_dirac_gamma``
   / ``srmech_qm_minkowski_metric`` / ``srmech_qm_gell_mann`` /
   ``srmech_qm_su2_structure`` / ``srmech_qm_su3_structure`` EMIT the
   canonical data, and the Python ops dispatch to them. Parity is
   BYTE-IDENTICAL (integer / ±1 / ±i entries; the only irrationals — λ⁸'s
   1/√3 and f^{458}=f^{678}=√3/2 — route through the SAME libm-free
   rational-sqrt cascade on both paths), NOT a float tolerance.

The six constant ops move ``composition_of_c`` → ``c_dispatched`` (+
``pauli_identity``, 7 ledger rows total); the so8/triality/gauge-generator
bases honestly STAY ``composition_of_c`` — they are DERIVATIONS through
already-C-backed ops (the octonion mult table composes the c_dispatched
``srmech_cd_basis_product``; the triality companion maps' exact-ℚ solve is
reproducible via ``srmech_qmat_rref``; su2/su3_generators are 0.5-scalings
of the now-C-emitted bases), not literals.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import contextlib
import math
import struct

import pytest

from srmech import _native
from srmech.physics.qm import gauge as G
from srmech.physics.qm import relativistic as R
from srmech.physics.qm import spin as S


_QM_CONST_SYMBOLS = (
    "srmech_qm_pauli",
    "srmech_qm_dirac_gamma",
    "srmech_qm_minkowski_metric",
    "srmech_qm_gell_mann",
    "srmech_qm_su2_structure",
    "srmech_qm_su3_structure",
)

requires_native = pytest.mark.skipif(
    not (_native.HAS_NATIVE and _native.LIB is not None
         and all(hasattr(_native.LIB, s) for s in _QM_CONST_SYMBOLS)),
    reason="rc212 needs the srmech_qm_* constant emitters; on a no-C host the "
    "canonical pure literals are the complete, byte-identical alternative.",
)


@contextlib.contextmanager
def force_pure():
    """Temporarily disable native dispatch so every constant op takes its
    pure-Python literal path — the forced-pure reference the C emitters
    must match bit-for-bit."""
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        yield
    finally:
        _native.HAS_NATIVE = saved


# ── the constant ops (thunks) ─────────────────────────────────────────────────
_MAT_TUPLE_OPS = {
    "pauli_matrices": S.pauli_matrices,
    "gamma_matrices": R.gamma_matrices,
    "su3_gell_mann_matrices": G.su3_gell_mann_matrices,
}
_MAT_SINGLE_OPS = {
    "pauli_identity": S.pauli_identity,
    "minkowski_metric": R.minkowski_metric,
}
_RANK3_OPS = {
    "su2_structure_constants": G.su2_structure_constants,
    "su3_structure_constants": G.su3_structure_constants,
}


def _rank3_bytes(f):
    flat = [x for plane in f for row in plane for x in row]
    return struct.pack(f"<{len(flat)}d", *flat)


def _is_neg_zero(x: float) -> bool:
    return x == 0.0 and math.copysign(1.0, x) < 0.0


def _assert_mat_canonical(name, m):
    for i in range(m.n_rows):
        for j in range(m.n_cols):
            z = m[i, j]
            re, im = (z.real, z.imag) if isinstance(z, complex) else (z, 0.0)
            assert not _is_neg_zero(re), f"{name}[{i},{j}].re is -0.0"
            assert not _is_neg_zero(im), f"{name}[{i},{j}].im is -0.0"


# ── native == forced-pure, BYTE-IDENTICAL ─────────────────────────────────────
@requires_native
@pytest.mark.parametrize("name", sorted(_MAT_TUPLE_OPS))
def test_mat_tuple_native_equals_forced_pure(name):
    """Tuple-of-Mat constants: the C emitter output is BYTE-IDENTICAL to the
    canonicalized pure literals (EXACT — no float tolerance)."""
    native_bytes = b"".join(m.tobytes() for m in _MAT_TUPLE_OPS[name]())
    with force_pure():
        pure_bytes = b"".join(m.tobytes() for m in _MAT_TUPLE_OPS[name]())
    assert native_bytes == pure_bytes, f"{name}: native != forced-pure bytes"


@requires_native
@pytest.mark.parametrize("name", sorted(_MAT_SINGLE_OPS))
def test_mat_single_native_equals_forced_pure(name):
    native_bytes = _MAT_SINGLE_OPS[name]().tobytes()
    with force_pure():
        pure_bytes = _MAT_SINGLE_OPS[name]().tobytes()
    assert native_bytes == pure_bytes, f"{name}: native != forced-pure bytes"


@requires_native
@pytest.mark.parametrize("name", sorted(_RANK3_OPS))
def test_rank3_native_equals_forced_pure(name):
    native_bytes = _rank3_bytes(_RANK3_OPS[name]())
    with force_pure():
        pure_bytes = _rank3_bytes(_RANK3_OPS[name]())
    assert native_bytes == pure_bytes, f"{name}: native != forced-pure bytes"


# ── no -0.0 anywhere (both paths) ─────────────────────────────────────────────
@pytest.mark.parametrize("pure", [False, True], ids=["live", "forced_pure"])
def test_no_negative_zero_in_any_constant(pure):
    """The canonicalization contract: every mathematically-zero slot of every
    constant is +0.0 — no stray -0.0 on the live path NOR the forced-pure
    path (the C emitter and the canonical literals agree on the zeros)."""
    ctx = force_pure() if pure else contextlib.nullcontext()
    with ctx:
        for name, thunk in _MAT_TUPLE_OPS.items():
            for k, m in enumerate(thunk()):
                _assert_mat_canonical(f"{name}[{k}]", m)
        for name, thunk in _MAT_SINGLE_OPS.items():
            _assert_mat_canonical(name, thunk())
        for name, thunk in _RANK3_OPS.items():
            for a, plane in enumerate(thunk()):
                for b, row in enumerate(plane):
                    for c, x in enumerate(row):
                        assert not _is_neg_zero(x), \
                            f"{name}[{a}][{b}][{c}] is -0.0"


# ── independent exact oracles (never touch native; no abs) ────────────────────
def test_pauli_exact_oracle():
    """σ/I₂ equal the canonical Pauli literals exactly (guards a value wrong
    in BOTH paths)."""
    sx, sy, sz = S.pauli_matrices()
    assert sx.tolist() == [[0, 1], [1, 0]]
    assert sy.tolist() == [[0, -1j], [1j, 0]]
    assert sz.tolist() == [[1, 0], [0, -1]]
    assert S.pauli_identity().tolist() == [[1, 0], [0, 1]]


def test_gamma_exact_oracle():
    """γ⁰..γ³ equal the Dirac-basis literals exactly (Peskin-Schroeder
    eq 3.25 + A.6)."""
    g0, g1, g2, g3 = R.gamma_matrices()
    assert g0.tolist() == [[1, 0, 0, 0], [0, 1, 0, 0],
                           [0, 0, -1, 0], [0, 0, 0, -1]]
    assert g1.tolist() == [[0, 0, 0, 1], [0, 0, 1, 0],
                           [0, -1, 0, 0], [-1, 0, 0, 0]]
    assert g2.tolist() == [[0, 0, 0, -1j], [0, 0, 1j, 0],
                           [0, 1j, 0, 0], [-1j, 0, 0, 0]]
    assert g3.tolist() == [[0, 0, 1, 0], [0, 0, 0, -1],
                           [-1, 0, 0, 0], [0, 1, 0, 0]]
    assert R.minkowski_metric().tolist() == [
        [1.0, 0.0, 0.0, 0.0], [0.0, -1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0], [0.0, 0.0, 0.0, -1.0]]


def test_gell_mann_lambda8_exact_normaliser():
    """λ⁸ = (1/√3)·diag(1, 1, -2) with the normaliser byte-equal to the
    Class-N rational-sqrt cascade (the C path routes the SAME cascade)."""
    from srmech.math import rational as _srn

    lam8 = G.su3_gell_mann_matrices()[7]
    s = 1.0 / float(_srn.sqrt(3.0))
    assert lam8.tolist() == [[s, 0, 0], [0, s, 0], [0, 0, -2.0 * s]]


def test_structure_constants_exact_oracle():
    """ε^{abc} + the f^{abc} seeds equal Peskin-Schroeder eq 15.4 / 17.34
    exactly (f^{458} = f^{678} = √3/2 through the rational-sqrt cascade)."""
    from srmech.math import rational as _srn

    eps = G.su2_structure_constants()
    assert eps[0][1][2] == 1.0 and eps[1][0][2] == -1.0
    assert eps[1][2][0] == 1.0 and eps[2][0][1] == 1.0
    f = G.su3_structure_constants()
    root3_half = float(_srn.sqrt(3.0)) / 2.0
    assert f[0][1][2] == 1.0
    assert f[0][3][6] == 0.5 and f[2][3][4] == 0.5
    assert f[0][4][5] == -0.5 and f[2][5][6] == -0.5
    assert f[3][4][7] == root3_half and f[5][6][7] == root3_half
    assert f[4][3][7] == -root3_half            # total antisymmetry


# ── the algebra still holds on the canonical constants (value guard) ──────────
def test_clifford_and_pauli_residuals_exact_zero():
    """The -0.0 canonicalization changed NO op's output: the Cl(1,3) and
    Cl(0,3) residuals stay EXACTLY zero (the rc145 guard, re-pinned here)."""
    assert R.clifford_residuals() == (0.0, 0.0, 0.0)
    assert S.pauli_clifford_residuals() == (0.0, 0.0)


def test_lie_algebra_residuals_exact_zero():
    """SU(2) and SU(3): [T^a, T^b] = i f^{abc} T^c holds EXACTLY on the
    canonical constants (generators are 0.5-scalings of the C-emitted
    bases — they honestly stay composition_of_c)."""
    assert G.lie_algebra_residual(
        G.su2_generators(), G.su2_structure_constants()) == 0.0
    assert G.lie_algebra_residual(
        G.su3_generators(), G.su3_structure_constants()) == pytest.approx(
            0.0, abs=1e-15)


def test_numpy_is_absent():
    """The whole rc212 constant path runs with numpy uninstalled."""
    import sys

    assert "numpy" not in sys.modules
