"""rc158 — C standalone-complete honor: the dense-solve node cap is GONE.

`srmech_dense_solve.c` carried `SRMECH_DENSE_SOLVE_MAX_N / _MAX_RHS = 256` plus
a 1 MiB thread-local *static* augmented `[A|B]` buffer, and the Python
`mat_solve` bounds-gated on `n,w ≤ 256` then RESCUED an over-cap / singular
native return into the pure-Python exact-rational solve (the rc153 anti-pattern).

Unlike rc156/rc157, the augmented matrix is GENUINE scratch (Gauss–Jordan
mutates a copy of the `const` A and B), so it cannot be eliminated — rc158
carves it from a CALLER arena (`srmech_dense_solve_f64_ws` +
`srmech_dense_solve_arena_bytes`, the genome rc154 precedent). The bound is now
the caller's RAM, not a compiled-in 256. Native is authoritative when present;
the pure-Python exact-rational solve is the COMPLETE alternative for no-C hosts.

This proves it at n = 300 > 256 (the old cap). Per
[[feedback_c_must_be_standalone_complete_no_python_fallback]]. numpy-free.
"""

import pytest

from srmech.amsc import _native
from srmech.amsc import laplacian as L
from srmech.amsc.mat import Mat


def _force_pure(fn):
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def _max_abs_diff(a, b):
    nr, nc = a.shape
    m = 0.0
    for i in range(nr):
        for j in range(nc):
            d = a[i, j] - b[i, j]
            d = d if d >= 0 else -d
            if d > m:
                m = d
    return m


def test_mat_solve_accepts_n300_dense_native_correct():
    # n = 300 > old 256 cap. A strongly diagonally-dominant (well-conditioned)
    # dense system; build B = A·X_known (float, fast) and check the native
    # solve recovers X_known. This proves the native kernel ACCEPTS n > 256 —
    # the old cap forbade it. The dense exact-rational pure path is infeasible
    # at n=300 (Fraction fill-in blows up), so this is a native-path property.
    if not _native.HAS_NATIVE:
        pytest.skip("native-only: dense exact-rational solve is infeasible at n=300")
    n, w = 300, 3
    a_rows = [
        [(100.0 + (i % 7)) if i == j else (((i + j) % 5) * 0.01)
         for j in range(n)]
        for i in range(n)
    ]
    x_rows = [[((i * 2 + j) % 9) * 0.5 - 2.0 for j in range(w)] for i in range(n)]
    A = Mat.from_rows(a_rows, is_complex=False)
    Xk = Mat.from_rows(x_rows, is_complex=False)
    B = L.mat_matmul(A, Xk)               # (n, w) = A·X_known
    X = L.mat_solve(A, B)                 # native, no cap
    assert X.shape == (n, w)
    assert _max_abs_diff(X, Xk) < 1e-6


def test_mat_solve_diag_n300_native_matches_pure():
    # n = 300 honor + parity on a DIAGONAL system: both the native Gauss–Jordan
    # and the pure exact-rational path stay cheap (no elimination fill-in), so
    # native == forced-pure can be checked across the full 300×300 at n > 256.
    n, w = 300, 2
    diag = [float(i + 2) for i in range(n)]      # nonzero, non-unit
    a_rows = [[diag[i] if i == j else 0.0 for j in range(n)] for i in range(n)]
    b_rows = [[float((i * 3 + j) % 11) for j in range(w)] for i in range(n)]
    A = Mat.from_rows(a_rows, is_complex=False)
    B = Mat.from_rows(b_rows, is_complex=False)
    native = L.mat_solve(A, B)
    pure = _force_pure(lambda: L.mat_solve(A, B))
    assert native.shape == (n, w)
    assert _max_abs_diff(native, pure) < 1e-9


def test_mat_solve_dense_small_native_matches_pure():
    # The full pivot+eliminate kernel matches the exact-rational path at a
    # feasible dense size (small integer entries keep Fraction growth bounded).
    n, w = 12, 3
    a_rows = [
        [float((i * 5 + j * 3) % 7 + (10 if i == j else 0)) for j in range(n)]
        for i in range(n)
    ]
    b_rows = [[float((i + 2 * j) % 9) for j in range(w)] for i in range(n)]
    A = Mat.from_rows(a_rows, is_complex=False)
    B = Mat.from_rows(b_rows, is_complex=False)
    native = L.mat_solve(A, B)
    pure = _force_pure(lambda: L.mat_solve(A, B))
    assert _max_abs_diff(native, pure) < 1e-9


def test_mat_solve_singular_raises_on_both_paths():
    # A genuinely singular A (a wholly-zero pivot column) is the same contract
    # for both impls: native SRMECH_ERR_BAD_INPUT → ZeroDivisionError, and the
    # exact path raises ZeroDivisionError too. Native is authoritative — it is
    # NOT rescued into the exact path.
    a_rows = [[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [1.0, 1.0, 1.0]]  # row2 = 2·row1
    b_rows = [[1.0], [2.0], [3.0]]
    A = Mat.from_rows(a_rows, is_complex=False)
    B = Mat.from_rows(b_rows, is_complex=False)
    with pytest.raises(ZeroDivisionError):
        L.mat_solve(A, B)
    with pytest.raises(ZeroDivisionError):
        _force_pure(lambda: L.mat_solve(A, B))
