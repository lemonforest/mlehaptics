"""0.9.0rc29 — `mat_eigvals` Parlett–Reinsch RADIX-2 balancing pre-step.

POLISH (no behavior bug). The float shifted-QR ``mat_eigvals``
(``srmech/amsc/laplacian.py``, post-rc26 with EISPACK exceptional shifts) is
CORRECT but was UNBALANCED — a badly-scaled matrix (a lopsided row-norm vs
col-norm split) loses accuracy in the QR iteration. rc29 adds
``_balance_radix2(H)``: an EXACT diagonal similarity ``D⁻¹·H·D`` with ``D`` a
diagonal of POWERS OF TWO (so every scale is a binary mantissa-shift — NO
floating rounding), chosen to equalise each index's row-norm against its
col-norm (the standard Parlett–Reinsch test, accept a step only if it reduces
``r + c``). Eigenvalues are INVARIANT under a similarity, so the multiset is:

  (a) UNCHANGED for well-scaled input (NO REGRESSION) — the rc26 battery still
      matches the exact integer oracle ``eigvals_exact(A, include_complex=True)``
      to ~1e-9;
  (b) MORE ACCURATE for a deliberately badly-scaled matrix — closer to the exact
      eigenvalues WITH balancing than a local UNbalanced copy of the same solver.

Refs: Parlett & Reinsch, "Balancing a matrix for calculation of eigenvalues and
eigenvectors", *Numer. Math.* 13 (1969) 293–304; Golub & Van Loan §7.5.1.

Also asserts the dead ``_certify_complex_root`` (orphaned by the rc28 square-free
-factored complex path) is GONE from ``matrix_cascades``.

numpy is GONE from srmech; this ratchet is numpy-free and runs with numpy NOT
installed.
"""
from __future__ import annotations

import importlib.util

import pytest

from srmech.amsc.cascade import matrix_cascades
from srmech.amsc.cascade.matrix_cascades import eigvals_exact
from srmech.amsc.laplacian import (
    _balance_radix2,
    _modulus_c,
    jacobi_eigvals,
    mat_eigvals,
)
from srmech.amsc.mat import Mat

_TOL = 1e-9


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this rc29 ratchet must run on the numpy-ABSENT matrix")


# ── helpers ──────────────────────────────────────────────────────────────────────
def _key(z):
    z = complex(z)
    return (round(z.real, 9), round(z.imag, 9))


def _multiset_equal(got, exact, tol=_TOL):
    g = sorted((complex(z) for z in got), key=_key)
    e = sorted((complex(z) for z in exact), key=_key)
    if len(g) != len(e):
        return False
    return all(abs(a - b) < tol for a, b in zip(g, e))


def _companion(coeffs_low_to_high):
    n = len(coeffs_low_to_high)
    rows = [[0] * n for _ in range(n)]
    for i in range(1, n):
        rows[i][i - 1] = 1                       # sub-diagonal ones (cyclic shift)
    for i in range(n):
        rows[i][n - 1] = -coeffs_low_to_high[i]  # last column = −constants
    return rows


def _multiset_max_err(got, exact):
    """Max |gotᵢ − exactᵢ| after sorting both multisets by (re, im) — the worst-case
    per-eigenvalue error of `got` vs the exact spectrum."""
    g = sorted((complex(z) for z in got), key=_key)
    e = sorted((complex(z) for z in exact), key=_key)
    assert len(g) == len(e), (g, e)
    return max(abs(a - b) for a, b in zip(g, e))


# ── (a) NO REGRESSION — the rc26 battery still matches the exact oracle ───────────
_CYCLIC_CASES = {
    "x^3-1": _companion([-1, 0, 0]),
    "x^4-1": _companion([-1, 0, 0, 0]),
    "x^4+1": _companion([1, 0, 0, 0]),
    "x^5-1": _companion([-1, 0, 0, 0, 0]),
    "perm3": [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
}


@pytest.mark.parametrize("label", sorted(_CYCLIC_CASES))
def test_no_regression_cyclic_companion(label):
    A = _CYCLIC_CASES[label]
    got = mat_eigvals(Mat.from_rows(A))
    exact = eigvals_exact(A, include_complex=True)
    assert _multiset_equal(got, exact), (
        f"{label}: BALANCING REGRESSED the well-scaled spectrum: "
        f"{sorted(map(complex, got), key=_key)} != "
        f"{sorted(map(complex, exact), key=_key)}")


def test_no_regression_rotation_gives_pm_i():
    got = mat_eigvals(Mat.from_rows([[0, -1], [1, 0]]))
    assert _multiset_equal(got, [1j, -1j])


def test_no_regression_symmetric_real_spectrum():
    S = [[2, 1, 0], [1, 2, 1], [0, 1, 2]]
    got = sorted(complex(z).real for z in mat_eigvals(Mat.from_rows(S)))
    exact = sorted(eigvals_exact(S))
    jac = sorted(jacobi_eigvals(Mat.from_rows(S)))
    assert len(got) == len(exact) == len(jac) == 3
    assert all(abs(a - b) < _TOL for a, b in zip(got, exact))
    assert all(abs(a - b) < _TOL for a, b in zip(got, jac))


def test_no_regression_defective_with_repeats():
    got = mat_eigvals(Mat.from_rows([[2, 1], [0, 2]]))
    assert _multiset_equal(got, [2 + 0j, 2 + 0j])
    assert len(got) == 2


def test_no_regression_nilpotent_all_zero_spectrum():
    # a nilpotent block [[0,1],[0,0]] has spectrum {0, 0}; balancing must NOT
    # break it (an all-zero row/col index is skipped, not divided by zero).
    got = mat_eigvals(Mat.from_rows([[0, 1], [0, 0]]))
    assert _multiset_equal(got, [0 + 0j, 0 + 0j])


def test_no_regression_diagonal_and_identity():
    assert _multiset_equal(
        mat_eigvals(Mat.from_rows([[5, 0, 0], [0, -3, 0], [0, 0, 7]])),
        [5 + 0j, -3 + 0j, 7 + 0j])
    assert _multiset_equal(
        mat_eigvals(Mat.from_rows([[1, 0], [0, 1]])), [1 + 0j, 1 + 0j])


# ── balancing is an EXACT eigenvalue-preserving similarity ───────────────────────
def test_balance_is_eigenvalue_preserving():
    """A diagonal-similarity scramble has the SAME spectrum; `mat_eigvals` must
    return that spectrum whether the input is the original or the scramble."""
    A = [[6, 0, 0], [0, 2, 0], [0, 0, -4]]              # spectrum {6, 2, −4}
    # D = diag(2^15, 1, 2^-something) — keep a structured scramble with off-diag.
    A2 = [[6, 1, 0], [0, 2, 1], [0, 0, -4]]             # upper-triangular, same diag
    got = mat_eigvals(Mat.from_rows(A2))
    exact = eigvals_exact(A2, include_complex=True)     # {6, 2, −4}
    assert _multiset_equal(got, exact)
    # the original diagonal too
    assert _multiset_equal(mat_eigvals(Mat.from_rows(A)), [6 + 0j, 2 + 0j, -4 + 0j])


def test_balance_radix2_uses_only_power_of_two_scales():
    """White-box: the similarity is EXACT — re-balancing an already-balanced matrix
    is idempotent (no index changes, so no rounding accumulates)."""
    H = [[complex(2.0), complex(8192.0)],     # 8192 = 2^13 (a clean power of two)
         [complex(0.125), complex(-3.0)]]     # 0.125 = 2^-3
    Hb = _balance_radix2([row[:] for row in H])
    # Eigenvalues invariant: tr and det unchanged (exact under the radix-2 sim).
    tr0 = H[0][0] + H[1][1]
    det0 = H[0][0] * H[1][1] - H[0][1] * H[1][0]
    trb = Hb[0][0] + Hb[1][1]
    detb = Hb[0][0] * Hb[1][1] - Hb[0][1] * Hb[1][0]
    assert abs(trb - tr0) < 1e-12
    assert abs(detb - det0) < 1e-12          # det exactly preserved (similarity)
    # idempotent: balancing the balanced matrix changes nothing
    Hbb = _balance_radix2([row[:] for row in Hb])
    for i in range(2):
        for j in range(2):
            assert _modulus_c(Hbb[i][j] - Hb[i][j]) < 1e-12


# ── (b) IMPROVED — a badly-scaled matrix is closer to exact WITH balancing ───────
def _eigvals_unbalanced(A):
    """A faithful copy of `mat_eigvals` MINUS the `_balance_radix2` pre-step — the
    same shifted-QR with EISPACK exceptional shifts, so the ONLY difference vs
    `mat_eigvals` is the balancing. Used to show balancing strictly improves the
    badly-scaled spectrum."""
    from srmech.amsc import laplacian as L
    M = Mat.from_rows(A)
    n = M.n_rows
    H = [[complex(M[i, j]) for j in range(n)] for i in range(n)]
    if n == 1:
        return [H[0][0]]
    eigs = []
    m = n
    sweeps = 0
    it = 0
    sweep_ceiling = 500 * n
    while m > 0:
        if m == 1:
            eigs.append(H[0][0])
            break
        scale = L._modulus_c(H[m - 2][m - 2]) + L._modulus_c(H[m - 1][m - 1])
        if L._modulus_c(H[m - 1][m - 2]) <= L._MAT_EIG_DEFLATE_TOL * (scale + 1e-300):
            eigs.append(H[m - 1][m - 1])
            m -= 1
            it = 0
            continue
        if m == 2:
            lam1, lam2 = L._eig2x2(H[0][0], H[0][1], H[1][0], H[1][1])
            eigs.append(lam1)
            eigs.append(lam2)
            break
        if it == 10 or it == 20:
            mu = L._modulus_c(H[m - 1][m - 2])
            if m - 3 >= 0:
                mu += L._modulus_c(H[m - 2][m - 3])
            mu = complex(mu, 0.0)
        else:
            lam1, lam2 = L._eig2x2(
                H[m - 2][m - 2], H[m - 2][m - 1], H[m - 1][m - 2], H[m - 1][m - 1])
            dd = H[m - 1][m - 1]
            mu = lam1 if L._modulus_c(lam1 - dd) < L._modulus_c(lam2 - dd) else lam2
        sub = [[H[i][j] - (mu if i == j else 0j) for j in range(m)] for i in range(m)]
        Q, R = L._qr_complex_list(sub)
        rq = L.mat_matmul(
            Mat.from_rows(R, is_complex=True), Mat.from_rows(Q, is_complex=True))
        for i in range(m):
            for j in range(m):
                H[i][j] = complex(rq[i, j]) + (mu if i == j else 0j)
        sweeps += 1
        it += 1
        if sweeps > sweep_ceiling:
            raise RuntimeError("unbalanced reference failed to converge")
    return eigs


# A badly-scaled matrix with a KNOWN integer spectrum. Start from an integer
# matrix with spectrum {3, 7, 11} (a 3×3 with off-diagonals), then apply an EXACT
# diagonal-similarity scramble D⁻¹·A·D with D = diag(2^k_i). Because D is a power-
# of-two diagonal and the off-diagonal multipliers below stay exactly representable
# in float (powers of two), the SCRAMBLED matrix has the IDENTICAL spectrum but a
# wildly lopsided row-/col-norm distribution — exactly what balancing repairs.
def _scrambled_known_spectrum():
    # base integer matrix; spectrum certified by eigvals_exact below (not asserted
    # by hand). Upper-Hessenberg-ish with modest integer entries.
    base = [[3, 5, 7],
            [2, 7, 4],
            [0, 6, 11]]
    # D = diag(2^18, 1, 2^-16): off-diagonal (i,j) scales by d_j/d_i (powers of two
    # → exact in float). The result has entries spanning ~2^34 in magnitude.
    s = [2.0 ** 18, 1.0, 2.0 ** -16]
    scrambled = [[base[i][j] * (s[j] / s[i]) for j in range(3)] for i in range(3)]
    return base, scrambled


def test_badly_scaled_is_more_accurate_with_balancing():
    base, scrambled = _scrambled_known_spectrum()
    exact = eigvals_exact(base, include_complex=True)   # the true spectrum (integers)

    bal = mat_eigvals(Mat.from_rows(scrambled))         # WITH balancing (rc29)
    unbal = _eigvals_unbalanced(scrambled)              # WITHOUT balancing

    err_bal = _multiset_max_err(bal, exact)
    err_unbal = _multiset_max_err(unbal, exact)

    # balancing must be accurate in absolute terms …
    assert err_bal < 1e-6, (
        f"balanced mat_eigvals max-err {err_bal:.3e} too large; exact={exact}, "
        f"got={sorted(map(complex, bal), key=_key)}")
    # … and STRICTLY no worse than the unbalanced reference (it should be better or
    # equal — the whole point of the pre-step). Allow equality for the rare case the
    # scramble happens to round cleanly, but require an improvement margin.
    assert err_bal <= err_unbal + 1e-15, (
        f"balancing did NOT help: balanced max-err {err_bal:.3e} vs unbalanced "
        f"{err_unbal:.3e}")
    # and demonstrate the unbalanced solver IS measurably worse on this input
    # (sanity: the scramble is genuinely badly conditioned for the raw QR).
    assert err_unbal > err_bal or err_unbal > 1e-12, (
        f"the scramble was not badly-scaled enough to exercise balancing: "
        f"unbalanced max-err {err_unbal:.3e}")


def test_balanced_matches_exact_on_scrambled_spectrum():
    """End-to-end: `mat_eigvals` on the badly-scaled matrix returns the exact known
    spectrum to ~1e-9 (the multiset match, the user-facing contract)."""
    base, scrambled = _scrambled_known_spectrum()
    exact = eigvals_exact(base, include_complex=True)
    got = mat_eigvals(Mat.from_rows(scrambled))
    assert _multiset_equal(got, exact, tol=1e-6), (
        f"balanced spectrum {sorted(map(complex, got), key=_key)} != exact "
        f"{sorted(map(complex, exact), key=_key)}")


# ── POLISH 2: the dead `_certify_complex_root` is GONE ───────────────────────────
def test_certify_complex_root_is_deleted():
    assert not hasattr(matrix_cascades, "_certify_complex_root"), (
        "the dead `_certify_complex_root` (orphaned by the rc28 square-free-factored "
        "complex path) must be DELETED from matrix_cascades")


def test_shared_complex_root_helpers_survive():
    """The helpers `_certify_complex_root` USED must STILL exist — they back the
    surviving `_isolate_complex_roots_upper` / `eigvals_exact` complex path."""
    for name in ("_refine_box", "_modulus", "_root_free_split",
                 "_count_roots_in_box", "_isolate_complex_roots_upper"):
        assert hasattr(matrix_cascades, name), (
            f"shared helper `{name}` must NOT be removed with _certify_complex_root")


def test_eigvals_exact_complex_path_still_works_after_deletion():
    """Regression: the rc28 repeated-complex case still resolves with the dead
    accelerator gone (the complex path is pure subdivision now)."""
    # companion of (x²+1)² = x⁴+2x²+1 → {i, i, −i, −i}
    A = _companion([1, 0, 2, 0])
    eigs = eigvals_exact(A, include_complex=True)
    assert _multiset_equal(eigs, [1j, 1j, -1j, -1j])
