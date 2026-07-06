"""BATCH B8a (rc145) — byte-identical C parity for the 6 EXACT qm Dirac-gamma /
Clifford ops.

`qm_exact_assembly` (B8, 24 exact `qm` ops) is batched by module. **B8a = the
relativistic + spin Dirac-gamma / Clifford family (6 ops)** — each builds EXACT
matrices whose entries are Gaussian integers ``{0, ±1, ±i}``, so the native path
is **byte-identical** to forced-pure: NO float tolerance, no libm, no ``abs()``
(Class-K sign lives in the value).

The 6 ops all move ``python_only_debt`` → ``composition_of_c`` (ceiling 68 → 62):
they are pure compositions of the already-C-backed matrix algebra — the
``c_dispatched`` ``laplacian.mat_matmul`` (``srmech_dense_matmul_complex``), the
rc141 C carrier ops ``srmech_mat_scale`` / ``srmech_mat_add`` / ``srmech_mat_sub``
(the ``Mat`` ``*`` / ``+`` / ``−`` operators), and the ``composition_of_c``
``laplacian.mat_norm`` — over the already-``composition_of_c`` γ / Pauli constant
builders. There is **no new C symbol** (the base γ / Pauli constants are already
standalone-ready ``composition_of_c`` data; re-emitting them in C would only have
to reproduce the Python literals' ``-0.0`` slots, a byte-identity hazard with no
standalone gain).

This test proves, for every op, that the native path (matmul + scale + add/sub in
C) equals the FORCED-pure path bit-for-bit, and cross-checks each against an
INDEPENDENT exact oracle (the Dirac-basis constants) — including the exact-zero
Clifford / Pauli residuals.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import contextlib

import pytest

from srmech.amsc import _native
from srmech.qm import relativistic as R
from srmech.qm import spin as S


requires_native = pytest.mark.skipif(
    not (_native.HAS_NATIVE and _native.has_native_carriers()),
    reason="rc145 B8a needs the native carrier surface (srmech_mat_scale/add/sub "
    "+ srmech_dense_matmul_complex); on a no-C host the pure-Python cascade is "
    "the complete, byte-identical alternative.",
)


@contextlib.contextmanager
def force_pure():
    """Temporarily disable native dispatch so every carrier op (mat_matmul +
    the Mat ``*`` / ``+`` / ``−`` carrier ops) takes its pure-Python fallback —
    the forced-pure reference the native path must match bit-for-bit."""
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        yield
    finally:
        _native.HAS_NATIVE = saved


# ── the 6 ops as thunks: matrix-valued (compare .tobytes()) + residual tuples ──
_MAT_OPS = {
    "gamma_5": R.gamma_5,
    "weyl_left_projector": R.weyl_left_projector,
    "weyl_right_projector": R.weyl_right_projector,
    "charge_conjugation_matrix": R.charge_conjugation_matrix,
}
_RESIDUAL_OPS = {
    "clifford_residuals": R.clifford_residuals,
    "pauli_clifford_residuals": S.pauli_clifford_residuals,
}


# ── independent exact oracles (Dirac basis; never touch native; no abs) ────────
_I = 1j
# γ₅ = [[0, I₂], [I₂, 0]]  (Peskin-Schroeder eq 3.72, Dirac rep)
_ORACLE_GAMMA5 = [
    [0, 0, 1, 0],
    [0, 0, 0, 1],
    [1, 0, 0, 0],
    [0, 1, 0, 0],
]
# P_L = (I − γ₅)/2
_ORACLE_PL = [
    [0.5, 0, -0.5, 0],
    [0, 0.5, 0, -0.5],
    [-0.5, 0, 0.5, 0],
    [0, -0.5, 0, 0.5],
]
# P_R = (I + γ₅)/2
_ORACLE_PR = [
    [0.5, 0, 0.5, 0],
    [0, 0.5, 0, 0.5],
    [0.5, 0, 0.5, 0],
    [0, 0.5, 0, 0.5],
]
# C = i γ² γ⁰  (Dirac rep; the code convention _scale(1j, mat_matmul(g2, g0)))
_ORACLE_C = [
    [0, 0, 0, -1],
    [0, 0, 1, 0],
    [0, -1, 0, 0],
    [1, 0, 0, 0],
]
_MAT_ORACLES = {
    "gamma_5": _ORACLE_GAMMA5,
    "weyl_left_projector": _ORACLE_PL,
    "weyl_right_projector": _ORACLE_PR,
    "charge_conjugation_matrix": _ORACLE_C,
}


# ──────────────────────────────────────────────────────────────────────────────
@requires_native
@pytest.mark.parametrize("name", sorted(_MAT_OPS))
def test_matrix_op_native_equals_forced_pure(name):
    """Each matrix-valued op: native (C matmul + carrier scale/add/sub) is
    BYTE-IDENTICAL to the forced-pure fallback (EXACT — Gaussian-integer
    entries, not a float tolerance)."""
    native_bytes = _MAT_OPS[name]().tobytes()
    with force_pure():
        pure_bytes = _MAT_OPS[name]().tobytes()
    assert native_bytes == pure_bytes, f"{name}: native != forced-pure bytes"


@requires_native
@pytest.mark.parametrize("name", sorted(_RESIDUAL_OPS))
def test_residual_op_native_equals_forced_pure(name):
    """Each residual op: native tuple == forced-pure tuple, bit-for-bit."""
    native_val = _RESIDUAL_OPS[name]()
    with force_pure():
        pure_val = _RESIDUAL_OPS[name]()
    assert native_val == pure_val, f"{name}: native != forced-pure"


@pytest.mark.parametrize("name", sorted(_MAT_OPS))
def test_matrix_op_matches_exact_oracle(name):
    """Each matrix op equals its independent Dirac-basis oracle EXACTLY (guards
    against a value that is wrong in BOTH the native and pure paths)."""
    got = _MAT_OPS[name]().tolist()
    assert got == _MAT_ORACLES[name], f"{name}: value != exact oracle"


def test_clifford_residuals_exact_zero():
    """The Cl(1,3) Clifford residuals are EXACTLY zero (the algebra holds)."""
    max_clifford, g5_sq, g5_anti = R.clifford_residuals()
    assert (max_clifford, g5_sq, g5_anti) == (0.0, 0.0, 0.0)


def test_pauli_clifford_residuals_exact_zero():
    """The Cl(0,3) Pauli anticommutator + commutator residuals are EXACTLY
    zero (the algebra holds)."""
    assert S.pauli_clifford_residuals() == (0.0, 0.0)


def test_gamma5_involutive_and_anticommuting():
    """A second independent structural check the C-dispatched matmul must
    satisfy: γ₅² = I₄ EXACTLY and {γ₅, γ^μ} = 0 EXACTLY (numpy-free)."""
    from srmech.amsc.laplacian import mat_matmul, mat_norm

    g5 = R.gamma_5()
    i4 = R._eye4()
    assert mat_norm(R._mat_sub(mat_matmul(g5, g5), i4)) == 0.0
    for g in R.gamma_matrices():
        anti = R._mat_add(mat_matmul(g5, g), mat_matmul(g, g5))
        assert mat_norm(anti) == 0.0


def test_numpy_is_absent():
    """The whole B8a path runs with numpy uninstalled (carrier-native)."""
    import sys

    assert "numpy" not in sys.modules
