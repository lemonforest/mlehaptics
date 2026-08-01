"""rc299 (`#918`) — the GENERAL non-Hermitian eigensolver now exists in C.

Before rc299 the C surface had exactly three eigen-paths and none was general:

  * ``srmech_jacobi_eigvals``              — REAL SYMMETRIC (cyclic Jacobi)
  * ``srmech_hermitian_eigendecompose_ws`` — COMPLEX HERMITIAN (complex Jacobi)
  * ``srmech_eigvec_exact`` / ``srmech_complex_isolate`` — EXACT, INTEGER only

while ``laplacian.mat_eigvals`` was classified ``composition_of_c``, a bucket
whose annotation reads "standalone-ready". It was not. Its balancing, Hessenberg
reduction, deflation loop, Wilkinson shift ladder and ``{QR}`` were Python-only;
only the ``RQ`` recombine reached C via ``mat_matmul``. And because
``mat_eigvals`` has **no Hermitian fast path** — it never consults the Hermitian
C solver, even for Hermitian input — a bare-C host could not run it for **ANY**
input, not merely for non-Hermitian ones. rc285 filed that gap rather than
closing it, and named the close as its own rc. This is that rc.

``srmech_mat_eigvals_ws`` is the same algorithm in C, so the classification
moves ``composition_of_c`` → ``c_dispatched`` on a TRUE claim rather than being
narrowed to an honest smaller one.

PARITY CONTRACT — **NUMERIC (FPU-tol)**. Both projections run the same operation
sequence in IEEE double and share ``srmech_rational_sqrt`` bit-for-bit. The one
honest divergence is the complex MODULUS: Python roots an EXACT rational
sum-of-squares (Class-N, arbitrary-precision), C uses the scaled float form.
That is ~1 ulp feeding a shift estimate and a reflector phase. Measured below:
real symmetric Laplacians agree **bit-exactly**, and general complex input
agrees to ~1e-14 relative.
"""
import cmath
import random

import pytest

from tests._native_gate import require_native
from srmech.amsc import _native
from srmech.math import laplacian as LP
from srmech.math.laplacian import dense_laplacian, mat_eigvals
from srmech.math.mat import Mat


HAVE_C = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_mat_eigvals_ws")
)

requires_c = pytest.mark.skipif(
    not HAVE_C, reason="native srmech_mat_eigvals_ws not present in this build"
)


def _pure(a, max_sweeps=500):
    """Run ``mat_eigvals`` with the native peer forced OFF (the pure sweep)."""
    real = LP._mat_eigvals_native
    LP._mat_eigvals_native = lambda *args, **kw: None
    try:
        return mat_eigvals(a, max_sweeps=max_sweeps)
    finally:
        LP._mat_eigvals_native = real


def _multiset_dev(got, expect):
    """Max nearest-neighbour deviation — an eigenvalue list is a MULTISET, so
    the ORDER is not part of the contract on either projection."""
    pool = list(expect)
    worst = 0.0
    for v in got:
        i = min(range(len(pool)), key=lambda k: abs(pool[k] - v))
        d = abs(pool[i] - v)
        if d > worst:
            worst = d
        pool.pop(i)
    return worst


# ── the capability claim itself ──────────────────────────────────────────────

def test_the_c_symbol_exists_and_is_reachable():
    """The whole point of `#918`: the claim and the code must agree.

    If this fails, ``mat_eigvals`` is classified ``c_dispatched`` while no C
    entry point backs it — the exact false-claim shape this rc exists to end.

    rc351 (`#T1004`): the "is there a library at all" half moved to
    :func:`require_native`, which still FAILS (task `#T843`) unless the run has
    explicitly declared itself pure. The SYMBOL claim below is untouched — that is
    this test's own claim to make, and no signal can excuse it.
    """
    require_native("the mat_eigvals c_dispatched claim")
    assert hasattr(_native.LIB, "srmech_mat_eigvals_ws"), (
        "mat_eigvals is classified c_dispatched but srmech_mat_eigvals_ws is "
        "absent from the built library"
    )
    assert hasattr(_native.LIB, "srmech_mat_eigvals_ws_size")


@requires_c
def test_native_path_is_actually_taken():
    """A symbol that exists but is never called would be a laundered gap."""
    L = dense_laplacian(5, [(0, 1), (1, 2), (2, 3), (3, 4)], [1.0] * 4)
    assert LP._mat_eigvals_native(
        [[complex(L[i, j]) for j in range(5)] for i in range(5)], 5, 500
    ) is not None, "the native peer declined a well-conditioned 5x5"


@requires_c
def test_workspace_size_is_honoured_and_undersize_is_refused():
    import ctypes
    n = 6
    need = int(_native.LIB.srmech_mat_eigvals_ws_size(ctypes.c_uint32(n)))
    assert need >= 3 * n * n * 2, "ws must cover H + the R/Q arena"
    a_il = (ctypes.c_double * (2 * n * n))()
    for i in range(n):
        a_il[(i * n + i) * 2] = float(i + 1)
    out = (ctypes.c_double * (2 * n))()
    small = (ctypes.c_double * (need - 1))()
    rc = _native.LIB.srmech_mat_eigvals_ws(
        ctypes.c_uint32(n), a_il, ctypes.c_uint32(500), out,
        small, ctypes.c_size_t(need - 1),
    )
    assert rc != _native.SRMECH_OK, "an undersize workspace must be REFUSED"


# ── the matrix classes C could not previously handle ─────────────────────────

@requires_c
@pytest.mark.parametrize("name,rows,expect", [
    ("rotation", [[0, -1], [1, 0]], [1j, -1j]),
    ("pauli_y", [[0, -1j], [1j, 0]], [1 + 0j, -1 + 0j]),
    ("defective_jordan", [[2, 1], [0, 2]], [2 + 0j, 2 + 0j]),
    ("upper_triangular", [[1, 9], [0, 5]], [1 + 0j, 5 + 0j]),
    ("real_nonsymmetric", [[0, 1], [-2, -3]], [-1 + 0j, -2 + 0j]),
])
def test_non_hermitian_closed_forms(name, rows, expect):
    """Each of these is OUTSIDE every pre-rc299 C eigen-path: not real
    symmetric, not Hermitian, and not an integer-exact case."""
    got = mat_eigvals(Mat.from_rows(rows, is_complex=True))
    assert _multiset_dev(got, expect) < 1e-12, f"{name}: got {got}"


@requires_c
@pytest.mark.parametrize("deg", [3, 4, 5, 6])
def test_companion_roots_of_unity(deg):
    """Equal-modulus spectra — the case that needs the EISPACK exceptional
    shift, and that returned all-zeros before the shift ladder existed."""
    rows = [[0] * deg for _ in range(deg)]
    for i in range(1, deg):
        rows[i][i - 1] = 1
    rows[0][deg - 1] = 1                       # companion of x^deg - 1
    expect = [cmath.exp(2j * cmath.pi * k / deg) for k in range(deg)]
    got = mat_eigvals(Mat.from_rows(rows, is_complex=True))
    assert _multiset_dev(got, expect) < 1e-9, f"deg={deg}: got {got}"


# ── C vs Python parity ───────────────────────────────────────────────────────

_GRAPHS = [
    ("star8", 8, [(0, i) for i in range(1, 8)]),
    ("path8", 8, [(i, i + 1) for i in range(7)]),
    ("cycle8", 8, [(i, (i + 1) % 8) for i in range(8)]),
    ("complete6", 6, [(i, j) for i in range(6) for j in range(i + 1, 6)]),
    ("broom11", 11,
     [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)] + [(5, i) for i in range(6, 11)]),
    ("disconnected7", 7, [(0, 1), (1, 2), (3, 4), (5, 6)]),
]


@requires_c
@pytest.mark.parametrize("name,n,edges", _GRAPHS)
def test_graph_laplacian_parity_is_bit_exact(name, n, edges):
    """On a REAL symmetric Laplacian the two projections agree EXACTLY.

    The modulus of a real number is exact on both sides, so the FPU-tol
    allowance is not even consumed here.
    """
    rng = random.Random(hash(name) & 0xFFFF)
    for _ in range(5):
        perm = list(range(n))
        rng.shuffle(perm)
        e = [(perm[u], perm[v]) for u, v in edges]
        L = dense_laplacian(n, e, [1.0] * len(e))
        assert mat_eigvals(L) == _pure(L), (
            f"{name}: native and pure projections diverged on a real "
            "symmetric Laplacian, where they should be bit-identical"
        )


@requires_c
def test_general_complex_parity_within_fpu_tolerance():
    """Random general complex + real non-symmetric across 12 orders of scale."""
    rng = random.Random(23)
    worst = 0.0
    worst_at = None
    for n in (2, 3, 4, 5, 6, 8, 10):
        for trial in range(20):
            cplx = trial % 2 == 0
            scale = 10.0 ** rng.randint(-6, 6)
            rows = [[complex(rng.uniform(-1, 1) * scale,
                             rng.uniform(-1, 1) * scale if cplx else 0.0)
                     for _ in range(n)] for _ in range(n)]
            A = Mat.from_rows(rows, is_complex=True)
            c = mat_eigvals(A)
            p = _pure(A)
            span = max(1e-300, max(abs(z) for z in p))
            rel = _multiset_dev(c, p) / span
            if rel > worst:
                worst, worst_at = rel, (n, trial, cplx, scale)
    assert worst < 1e-12, (
        f"worst C-vs-Python relative multiset deviation {worst:.3e} at "
        f"n/trial/complex/scale={worst_at} — the NUMERIC (FPU-tol) parity "
        "contract allows ~1 ulp of modulus divergence, not this"
    )


# ── the invariant that caught #1440, now asserted on the NATIVE path ─────────

@requires_c
@pytest.mark.parametrize("name,n,edges", _GRAPHS)
def test_lambda_min_is_zero_on_the_native_path(name, n, edges):
    """Every graph Laplacian is singular. The rc285 ratchet asserts this over
    the PYTHON projection; it must hold on the compiled one too, or the two
    projections are not the same capability."""
    L = dense_laplacian(n, edges, [1.0] * len(edges))
    assert min(abs(z) for z in mat_eigvals(L)) < 1e-9


@requires_c
@pytest.mark.parametrize("name,n,edges", _GRAPHS)
def test_relabelling_invariance_on_the_native_path(name, n, edges):
    """Relabelling a graph cannot change its spectrum. This is the general form
    of the missing-Hessenberg defect (#1440) and the property that caught it —
    pinned here against the C peer so the compiled projection cannot acquire
    the defect the Python one shed."""
    rng = random.Random(4242)
    base = sorted(mat_eigvals(dense_laplacian(n, edges, [1.0] * len(edges))),
                  key=lambda z: (z.real, z.imag))
    for _ in range(5):
        perm = list(range(n))
        rng.shuffle(perm)
        e = [(perm[u], perm[v]) for u, v in edges]
        got = sorted(mat_eigvals(dense_laplacian(n, e, [1.0] * len(e))),
                     key=lambda z: (z.real, z.imag))
        assert _multiset_dev(got, base) < 1e-9, (
            f"{name}: spectrum moved under relabelling on the native path"
        )


@requires_c
def test_non_convergence_falls_back_rather_than_returning_a_wrong_spectrum():
    """A starved sweep budget must NOT yield the raw diagonal.

    The C peer returns SRMECH_ERR_OVERFLOW, the Python wrapper then runs the
    pure sweep, which raises. Either way the caller never receives the
    un-converged diagonal — that was the historic all-zero companion bug.
    """
    rows = [[0] * 6 for _ in range(6)]
    for i in range(1, 6):
        rows[i][i - 1] = 1
    rows[0][5] = 1                              # companion of x^6 - 1
    A = Mat.from_rows(rows, is_complex=True)
    with pytest.raises(RuntimeError):
        mat_eigvals(A, max_sweeps=1)
