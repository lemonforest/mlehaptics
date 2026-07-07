"""Qalg TAIL Batch 9 — THE CAPSTONE (0.9.0rc166): the last 2 exact-symbolic
oracles ``eig_exact`` + ``jordan_form_exact`` earn a standalone-C path, driving
``CEIL_BIGNUM_REFERENCE`` 2 → 0 — the ENTIRE exact-algebra tail is now python-free.

By rc165 every COMPUTE dependency of the two turnkey capstones is a ``srmech_*``
C twin: ``char_poly`` (``srmech_faddeev_leverrier``), ``factor_integer_poly``
(``srmech_factor_integer_poly``, Zassenhaus), ``eigvals_exact``
(``srmech_sturm_isolate`` / ``srmech_complex_isolate`` /
``srmech_poly_root_box_certify``), ``eigvec_exact`` (``srmech_eigvec_exact`` over
the ℚ(λ) field), ``jordan_chains_exact`` (``srmech_jordan_chains``). So
``eig_exact`` and ``jordan_form_exact`` are now THIN Python orchestrations that
ONLY compose already-``c_dispatched`` ops with trivial glue (assemble / sort /
build P+J / the ONE terminal Qalg→float projection / self-validate) — there is NO
irreducible compute kernel left in the orchestration, so both move
``bignum_reference`` → ``composition_of_c`` (the ``mat_dot`` / factor-Yun /
``esprit`` precedent: a bare-C host orchestrates the C leaves the same way). NO
new C symbol; ABI stays 3; ``tools.total`` stays 403.

This test pins:
  1. the native lib + every C dependency symbol is actually loaded (so the parity
     below exercises C on the native side, not a silent pure fallback on BOTH);
  2. ``eig_exact`` / ``jordan_form_exact`` native == FORCED-PURE is
     BYTE/STRUCTURALLY-IDENTICAL — the same eigenvalues, eigenvectors, {P, J},
     Qalg reps, ordering + block structure — for ``project=True`` AND
     ``project=False``, across the value oracles;
  3. the value oracles — ``diag(1,2,3)`` → {1,2,3} + standard eigenvectors +
     ``J = diag``; symmetric ``[[2,1],[1,2]]`` → {1,3}; a defective
     ``[[λ,1],[0,λ]]`` → a size-2 Jordan block with ``A·P == P·J``; an
     irrational-spectrum ``[[0,1],[1,1]]`` → the ℚ(√5) golden-ratio Qalg reps;
  4. ``A·P == P·J`` holds EXACTLY (the internal exact-Qalg self-validation)
     AND ~1e-9 in the float read-out;
  5. the Rosetta rows: ``eig_exact`` / ``jordan_form_exact`` → ``composition_of_c``,
     the down-only ``CEIL_BIGNUM_REFERENCE`` ratchet is 0, and the
     ``bignum_reference`` bucket is EMPTY (the milestone — the exact-algebra tail
     is python-free).

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade.matrix_cascades import eig_exact, jordan_form_exact


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "the capstone C ratchet must run on the numpy-ABSENT matrix")


# ── native symbol presence: the parity is only meaningful if C is loaded ─────
def test_native_dependency_symbols_are_loaded():
    """Every COMPUTE leaf the two capstones orchestrate must be a loaded C symbol
    — otherwise the native side silently falls back to pure and parity proves
    nothing. char_poly / factor / eigvals / eigvec / jordan_chains are all C."""
    assert _native.HAS_NATIVE, "native lib not loaded — build libsrmech first"
    assert hasattr(_native, "char_poly_int_c")
    assert _native.has_native_factor_integer_poly(), (
        "srmech_factor_integer_poly not loaded — rebuild libsrmech (rc165)")
    assert hasattr(_native, "sturm_isolate_c") and hasattr(_native, "complex_isolate_c")
    assert _native.has_native_eigvec_exact(), (
        "srmech_eigvec_exact not loaded — rebuild libsrmech (rc163)")
    assert _native.has_native_jordan_chains(), (
        "srmech_jordan_chains not loaded — rebuild libsrmech (rc164)")


def _force(has_native, fn, *args, **kw):
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


# ── the matrices under test (integer, square; a mix of diagonalizable /
#    symmetric / DEFECTIVE / irrational-spectrum) ────────────────────────────
_MATS = {
    "diag123": [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
    "sym2112": [[2, 1], [1, 2]],
    "defective_jordan2": [[5, 1], [0, 5]],       # J: one size-2 block, λ=5
    "sqrt5_golden": [[0, 1], [1, 1]],            # eigenvalues (1±√5)/2
    "defective_3x3": [[2, 1, 0], [0, 2, 0], [0, 0, 3]],
    "companion_x3": [[0, 0, 2], [1, 0, 1], [0, 1, 0]],  # a cubic char-poly
    "rot90": [[0, -1], [1, 0]],                  # ±i complex spectrum
}


@pytest.mark.parametrize("name", list(_MATS))
@pytest.mark.parametrize("project", [True, False])
def test_eig_exact_native_equals_forced_pure(name, project):
    """eig_exact native == FORCED-PURE, byte/structurally-identical (same
    eigenvalues, eigenvectors, min-polys, multiplicities, jordan_blocks,
    generalized vectors, ordering — Qalg reps when project=False)."""
    A = _MATS[name]
    nat = _force(True, eig_exact, A, project=project)
    pur = _force(False, eig_exact, A, project=project)
    assert nat == pur, f"eig_exact({name}, project={project}) native != pure"


@pytest.mark.parametrize("name", list(_MATS))
@pytest.mark.parametrize("project", [True, False])
def test_jordan_form_native_equals_forced_pure(name, project):
    """jordan_form_exact native == FORCED-PURE, byte/structurally-identical
    (same blocks, same P columns, same J block structure — Qalg reps when
    project=False)."""
    A = _MATS[name]
    nat = _force(True, jordan_form_exact, A, project=project)
    pur = _force(False, jordan_form_exact, A, project=project)
    assert nat == pur, f"jordan_form_exact({name}, project={project}) native != pure"


# ── value oracles ───────────────────────────────────────────────────────────
def test_diag_eigenvalues_and_jordan_is_diagonal():
    A = _MATS["diag123"]
    eig = eig_exact(A)
    assert sorted(round(e["value"].real, 9) for e in eig) == [1.0, 2.0, 3.0]
    assert all(abs(e["value"].imag) < 1e-12 for e in eig)
    # non-defective → every jordan block is size 1
    assert all(e["jordan_blocks"] == [1] for e in eig)
    J = jordan_form_exact(A)
    # diagonal Jordan: no super-diagonal 1s
    n = len(A)
    for i in range(n):
        for j in range(n):
            if i != j:
                assert abs(J["J"][i][j]) < 1e-12
    assert sorted(round(v.real, 9) for (v, _s) in J["blocks"]) == [1.0, 2.0, 3.0]
    assert all(s == 1 for (_v, s) in J["blocks"])


def test_symmetric_eigenvalues_1_and_3():
    eig = eig_exact(_MATS["sym2112"])
    assert sorted(round(e["value"].real, 9) for e in eig) == [1.0, 3.0]


def test_defective_has_size2_jordan_block_and_AP_equals_PJ():
    """A defective [[5,1],[0,5]] → ONE size-2 Jordan block; jordan_form_exact's
    internal A·P == P·J self-validation passes (exact over Qalg + ~1e-9 float),
    and we re-check A·P == P·J from the returned float {P, J}."""
    A = _MATS["defective_jordan2"]
    eig = eig_exact(A)
    # one eigenvalue λ=5, algebraic mult 2, defective, a single size-2 chain
    assert len(eig) == 1
    e = eig[0]
    assert round(e["value"].real, 9) == 5.0
    assert e["algebraic_multiplicity"] == 2 and e["geometric_multiplicity"] == 1
    assert e["defective"] is True and e["jordan_blocks"] == [2]
    J = jordan_form_exact(A)                    # raises if A·P != P·J
    assert J["blocks"] == [((5 + 0j), 2)]
    # J has the genuine super-diagonal 1 of the defective block
    assert abs(J["J"][0][1] - (1 + 0j)) < 1e-12
    # re-verify A·P == P·J from the returned floats (independent of the internal check)
    P, Jm = J["P"], J["J"]
    n = len(A)
    for i in range(n):
        for c in range(n):
            ap = sum(A[i][k] * P[k][c] for k in range(n))
            pj = sum(P[i][k] * Jm[k][c] for k in range(n))
            assert abs(ap - pj) < 1e-9, f"A·P != P·J at ({i},{c})"


def test_irrational_spectrum_qsqrt5_golden_ratio():
    """[[0,1],[1,1]] has char-poly x²−x−1 (irreducible over ℚ) → the two
    eigenvalues are the golden ratio (1±√5)/2, carried as EXACT Qalg over the
    same min-poly (-1,-1,1). project=False returns the exact Qalg reps."""
    eig = eig_exact(_MATS["sqrt5_golden"], project=False)
    assert len(eig) == 2
    for e in eig:
        assert e["min_poly"] == (-1, -1, 1)     # x²−x−1
    floats = sorted(round(e["value_qalg"].to_float(), 6) for e in eig)
    assert floats == [-0.618034, 1.618034]      # (1−√5)/2, (1+√5)/2
    # native == pure on the exact Qalg objects
    assert _force(True, eig_exact, _MATS["sqrt5_golden"], project=False) == \
           _force(False, eig_exact, _MATS["sqrt5_golden"], project=False)


def test_complex_spectrum_rot90_plus_minus_i():
    """[[0,-1],[1,0]] → eigenvalues ±i (min-poly x²+1), exercising the complex
    isolation (srmech_complex_isolate) path inside eig_exact."""
    eig = eig_exact(_MATS["rot90"])
    vals = sorted((round(e["value"].real, 9), round(e["value"].imag, 9)) for e in eig)
    assert vals == [(0.0, -1.0), (0.0, 1.0)]
    for e in eig_exact(_MATS["rot90"], project=False):
        assert e["min_poly"] == (1, 0, 1)       # x²+1


def test_defective_3x3_block_structure():
    A = _MATS["defective_3x3"]
    J = jordan_form_exact(A)                    # raises if A·P != P·J
    blocks = sorted((round(v.real, 9), s) for (v, s) in J["blocks"])
    assert blocks == [(2.0, 2), (3.0, 1)]


# ── the Rosetta ledger: the milestone ───────────────────────────────────────
_LEDGER = Path(__file__).resolve().parent / "rosetta_classification.ndjson"


def _ledger_rows():
    return [json.loads(l) for l in _LEDGER.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def test_rosetta_rows_are_composition_of_c():
    rows = {r["defined_at"]: r["bucket"] for r in _ledger_rows()}
    for key in ("srmech.amsc.cascade.matrix_cascades.eig_exact",
                "srmech.amsc.cascade.matrix_cascades.jordan_form_exact"):
        assert rows[key] == "composition_of_c", (
            f"{key} should be composition_of_c after rc166; got {rows[key]}")


def test_bignum_reference_bucket_is_empty():
    """THE MILESTONE: no op remains classified bignum_reference — the entire
    exact-algebra tail is python-free (every leaf a srmech_* C twin)."""
    bignum = [r["defined_at"] for r in _ledger_rows()
              if r["bucket"] == "bignum_reference"]
    assert bignum == [], f"bignum_reference bucket is NOT empty: {bignum}"


def test_ceiling_is_zero():
    import importlib.util as _u
    path = Path(__file__).resolve().parent / "test_rosetta_completeness.py"
    spec = _u.spec_from_file_location("_rosetta_ceiling_probe_rc166", path)
    mod = _u.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.CEIL_BIGNUM_REFERENCE == 0
    assert mod.CEIL_PYTHON_ONLY_DEBT == 0
    assert mod.CEIL_C_EXISTS_UNBOUND == 0
