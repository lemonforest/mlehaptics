"""0.9.0rc285 — the Laplacian KERNEL invariant, ratcheted over EVERY eigensolver.

Issue #1440. ``mat_eigvals`` returned a WRONG spectrum for a star graph's
Laplacian: ``K(1,3)`` came back as ``[2−√3, 1, 1, 2+√3]`` instead of
``[0, 1, 1, 4]``. The trace was right, the interior was right, and the extreme
pair kept its correct SUM while splitting about its mean incorrectly — so
nothing downstream looked obviously broken.

**The one-line property that catches it at any size, on any solver:**

    every graph Laplacian is positive-semidefinite with the constant vector in
    its kernel, so  min(eigvals(dense_laplacian(...))) == 0  EXACTLY (to FPU
    tolerance) — for every graph, every size, every eigensolver.

That invariant is free, it needs no oracle, and it would have red-flagged this
bug the day ``mat_eigvals`` landed. This module makes it a standing ratchet.

## Root cause (what the ratchet is actually guarding)

``mat_eigvals`` runs a shifted-QR iteration whose deflation test reads the
SINGLE subdiagonal entry ``H[m-1][m-2]`` and, when it is negligible, accepts
``H[m-1][m-1]`` as converged. That test is sound only for an **upper-Hessenberg**
matrix — and before rc285 the Householder reduction to Hessenberg form (Golub &
Van Loan §7.4.3) was simply **missing**. On an unreduced matrix the last row can
carry a large entry at ``H[m-1][j]`` for ``j < m-2`` while ``H[m-1][m-2]`` is
exactly 0, and the sweep then deflates a NON-eigenvalue and solves the wrong
leading block.

**So the trigger is not "hub dominance" — it is ``H[n-1][n-2] == 0``**, i.e. the
last two vertices being non-adjacent. A star hits it because its leaves are
pairwise non-adjacent, but so does a PATH under an unlucky labelling
(:func:`test_spectrum_is_invariant_under_vertex_relabelling` pins that, and is
the strongest of these ratchets: it is label-order invariance, of which the star
case is one instance).

## What this module asserts

1. ``min(eigvals) == 0`` for every (family, size, solver) triple — stars
   explicitly, since that is the reported trigger.
2. The full spectrum agrees across ALL solvers (they are the same operator).
3. The spectrum is invariant under vertex RELABELLING — the general statement of
   the defect.
4. Known closed-form spectra (star / path / cycle / complete) are matched.
5. **Phase-sensitivity**: a gauge-NONTRIVIAL charge on a cycle MUST move the
   spectrum, so the "solver silently ignores the imaginary part" failure class
   cannot silently return. (It also pins the correct dual fact — a charge on a
   TREE is gauge-trivial and must NOT move it.)
6. **Proof of redness** (:func:`test_pre_rc285_sweep_without_hessenberg_is_red`):
   a faithful copy of ``mat_eigvals`` MINUS the Hessenberg reduction, asserted to
   reproduce the historic wrong answer. A ratchet never shown to go red is not a
   ratchet; this keeps the redness demonstrable forever, in-suite, rather than as
   a claim in a commit message.

Numpy-free / math-free throughout (ADR-0005): the closed-form spectra use the
Class-N ``rational.cos`` cascade, never ``math.cos``.
"""

import itertools

import pytest

from srmech.amsc.cascade.matrix_cascades import eigvals as cascade_eigvals
from srmech.amsc.cascade.matrix_cascades import qr as cascade_qr
from srmech.amsc.laplacian import (
    _MAT_EIG_DEFLATE_TOL,
    _PI,
    _balance_radix2,
    _cmax_component,
    _eig2x2,
    _fhypot,
    _fsqrt,
    _hessenberg_complex,
    _householder_reflector,
    _modulus_c,
    dense_laplacian,
    hermitian_eigendecompose,
    jacobi_eigvals,
    magnetic_laplacian,
    mat_eigvals,
    mat_hermitian_eigendecompose,
    mat_matmul,
    symmetric_eigendecompose,
)
from srmech.amsc.mat import Mat
from srmech.amsc.rational import cos as _q_cos

# FPU tolerance for a float eigensolve. NOT loosened for any solver: the
# measured worst case across every case below is ~1e-13, so 1e-9 is slack, not a
# fitted threshold. (Tightening is welcome; loosening needs a written reason.)
_TOL = 1e-9


# ── graph families ────────────────────────────────────────────────────

def _star(n):
    """K(1,n-1) — the reported trigger. Leaves are pairwise non-adjacent."""
    return [(0, i) for i in range(1, n)]


def _path(n):
    return [(i, i + 1) for i in range(n - 1)]


def _cycle(n):
    return [(i, (i + 1) % n) for i in range(n)]


def _complete(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def _double_star(n):
    """Two hubs joined, leaves split between them — hub-dominated, not a star."""
    mid = n // 2
    e = [(0, mid)]
    e += [(0, i) for i in range(1, mid)]
    e += [(mid, i) for i in range(mid + 1, n)]
    return e


def _broom(n):
    """A path with a star glued on the end — mixed degree profile."""
    half = n // 2
    return _path(half) + [(half - 1, i) for i in range(half, n)]


_FAMILIES = {
    "star": _star,
    "path": _path,
    "cycle": _cycle,
    "complete": _complete,
    "double_star": _double_star,
    "broom": _broom,
}

_SIZES = (3, 4, 5, 6, 7, 8, 11, 16)


def _graphs():
    """(label, n, edges) over every family × size that is well-defined."""
    for name, fn in _FAMILIES.items():
        for n in _SIZES:
            if name == "cycle" and n < 3:
                continue
            if name in ("double_star", "broom") and n < 4:
                continue
            yield f"{name}-{n}", n, fn(n)


# ── solver adapters: every one returns a sorted list of real eigenvalues ──

def _s_mat_eigvals(L):
    return sorted(complex(z).real for z in mat_eigvals(L))


def _s_jacobi(L):
    return sorted(float(v) for v in jacobi_eigvals(L))


def _s_hermitian(L):
    return sorted(float(v) for v in hermitian_eigendecompose(L)[0])


def _s_symmetric(L):
    return sorted(float(v) for v in symmetric_eigendecompose(L)[0])


def _s_mat_hermitian(L):
    """``mat_hermitian_eigendecompose`` wants a COMPLEX Mat and returns its
    eigenvalues as an n×1 real Mat (not a Vec)."""
    Hm = Mat.from_rows(
        [[complex(L[i, j]) for j in range(L.n_cols)] for i in range(L.n_rows)],
        is_complex=True,
    )
    evals, _V = mat_hermitian_eigendecompose(Hm)
    return sorted(float(evals[i, 0]) for i in range(evals.n_rows))


def _s_cascade_eigvals(L):
    """The PUBLIC ``matrix_cascades.eigvals`` op — it delegates to
    ``mat_eigvals`` and therefore inherited the defect verbatim. Covered here
    because a caller reaching the bug through this name would have seen the
    identical wrong spectrum."""
    rows = [[L[i, j] for j in range(L.n_cols)] for i in range(L.n_rows)]
    v = cascade_eigvals(rows)
    return sorted(complex(v[i]).real for i in range(v.shape[0]))


_SOLVERS = {
    "mat_eigvals": _s_mat_eigvals,
    "jacobi_eigvals": _s_jacobi,
    "hermitian_eigendecompose": _s_hermitian,
    "symmetric_eigendecompose": _s_symmetric,
    "mat_hermitian_eigendecompose": _s_mat_hermitian,
    "matrix_cascades.eigvals": _s_cascade_eigvals,
}

# Solvers that accept a COMPLEX Hermitian operand (the magnetic Laplacian).
_COMPLEX_SOLVERS = (
    "mat_eigvals",
    "hermitian_eigendecompose",
    "mat_hermitian_eigendecompose",
    "matrix_cascades.eigvals",
)


# ── 1. the kernel invariant, every solver × every graph ───────────────

@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_laplacian_lambda_min_is_zero(solver):
    """THE ratchet: every graph Laplacian has λ_min == 0 exactly, because the
    all-ones vector spans its kernel (each row sums to deg − Σ weights = 0).

    A strictly positive λ_min is not a rounding artefact — it means the solver
    reported an operator that is not a Laplacian. This is what #1440 was.

    Parametrized by SOLVER (the axis #1440 lived on — one solver of six was
    wrong while five were right) and looped over every family × size inside, so
    a failure names the offending graph without paying pytest's per-case
    collection cost 288 times.
    """
    fn = _SOLVERS[solver]
    for label, n, edges in _graphs():
        ev = fn(dense_laplacian(n, edges))
        assert len(ev) == n, (
            f"{solver} on {label}: expected {n} eigenvalues, got {len(ev)}"
        )
        assert abs(ev[0]) < _TOL, (
            f"{solver} on {label}: λ_min = {ev[0]!r}, must be 0 — the constant "
            f"vector spans every graph Laplacian's kernel. Full spectrum: {ev}"
        )
        # PSD: no eigenvalue may be negative beyond FPU noise.
        assert ev[0] > -_TOL, f"{solver} on {label}: negative eigenvalue {ev[0]!r}"


# ── 2. all solvers agree (they are the same operator) ─────────────────

@pytest.mark.parametrize("solver", sorted(set(_SOLVERS) - {"hermitian_eigendecompose"}))
def test_all_eigensolvers_agree(solver):
    """Cross-solver differential oracle. The rotating-oracle rule of ADR-0009 §2:
    no solver is the reference — they must simply agree, and #1440 was exactly a
    disagreement nobody was positioned to see."""
    fn = _SOLVERS[solver]
    ref_fn = _SOLVERS["hermitian_eigendecompose"]
    for label, n, edges in _graphs():
        L = dense_laplacian(n, edges)
        got, ref = fn(L), ref_fn(L)
        for a, b in zip(got, ref):
            assert abs(a - b) < _TOL, (
                f"{solver} disagrees with hermitian_eigendecompose on "
                f"{label}: {got} != {ref}"
            )


# ── 3. relabelling invariance — the GENERAL form of the defect ────────

_RELABELLINGS = {
    "identity": lambda n: list(range(n)),
    "reversed": lambda n: list(range(n - 1, -1, -1)),
    "swap_last_two": lambda n: list(range(n - 2)) + [n - 1, n - 2],
    "interleave": lambda n: (
        [i for i in range(n) if i % 2 == 0] + [i for i in range(n) if i % 2 == 1]
    ),
    "rotate": lambda n: [(i + 1) % n for i in range(n)],
}


@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_spectrum_is_invariant_under_vertex_relabelling(solver):
    """A relabelling is a PERMUTATION similarity ``PᵀLP`` — the spectrum is
    invariant, full stop.

    This is the strongest ratchet in the module and the general statement of
    #1440: the pre-rc285 sweep was **label-order dependent**, because its
    deflation test read the (n-1, n-2) entry of an unreduced matrix. The star
    was merely the case someone happened to try. A PATH relabelled so its last
    two vertices are non-adjacent — e.g. 0-2-1-3, which
    ``_path`` + ``interleave`` produces — was equally wrong, returning
    ``[1, 1, 1, 3]`` for a true spectrum of ``[0, 2−√2, 2, 2+√2]``.
    """
    fn = _SOLVERS[solver]
    for label, n, edges in _graphs():
        a = fn(dense_laplacian(n, edges))
        for perm_name in sorted(_RELABELLINGS):
            perm = _RELABELLINGS[perm_name](n)
            b = fn(dense_laplacian(n, [(perm[u], perm[v]) for (u, v) in edges]))
            for x, y in zip(a, b):
                assert abs(x - y) < _TOL, (
                    f"{solver} on {label}: spectrum CHANGED under the "
                    f"'{perm_name}' relabelling — a permutation similarity "
                    f"cannot move eigenvalues. {a} != {b}"
                )


# ── 4. known closed-form spectra ──────────────────────────────────────

def _cos(x):
    """Class-N ``cos`` cascade → float (no ``math.cos``): ``rational.cos``
    returns an exact ``Q``, projected to float once at the end."""
    return float(_q_cos(x))


@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_star_spectrum_closed_form(solver):
    """Star K(1,n−1): spectrum is exactly ``{0, 1 (×n−2), n}``. This is the
    #1440 repro, generalised — pre-rc285 it returned ``{2−√3, 1, 1, 2+√3}`` for
    n=4."""
    for n in (3, 4, 5, 6, 8, 11, 16):
        ev = _SOLVERS[solver](dense_laplacian(n, _star(n)))
        expect = [0.0] + [1.0] * (n - 2) + [float(n)]
        for got, want in zip(ev, expect):
            assert abs(got - want) < _TOL, f"{solver} star n={n}: {ev} != {expect}"


@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_complete_graph_spectrum_closed_form(solver):
    """K_n: spectrum is ``{0, n (×n−1)}``."""
    for n in (3, 4, 5, 6, 8, 11):
        ev = _SOLVERS[solver](dense_laplacian(n, _complete(n)))
        expect = [0.0] + [float(n)] * (n - 1)
        for got, want in zip(ev, expect):
            assert abs(got - want) < _TOL, f"{solver} K_{n}: {ev} != {expect}"


@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_cycle_spectrum_closed_form(solver):
    """C_n: eigenvalues ``2 − 2·cos(2πk/n)``, k = 0..n−1."""
    for n in (3, 4, 5, 6, 8, 11):
        ev = _SOLVERS[solver](dense_laplacian(n, _cycle(n)))
        expect = sorted(2.0 - 2.0 * _cos(2.0 * _PI * k / n) for k in range(n))
        for got, want in zip(ev, expect):
            assert abs(got - want) < 1e-7, f"{solver} C_{n}: {ev} != {expect}"


# ── 5. phase-sensitivity — the dtype-honesty guard ────────────────────

def test_gauge_nontrivial_charge_MOVES_the_spectrum():
    """A charge around a CYCLE is gauge-NONTRIVIAL (the holonomy is an
    invariant), so it MUST move the spectrum. If a solver ever starts discarding
    the imaginary part of a complex Hermitian operand, this goes red.

    Guards the failure class #1440 reported as its "second defect". (The report
    was mistaken about the mechanism — see
    :func:`test_gauge_trivial_charge_on_a_tree_does_not_move_the_spectrum` — but
    the class is real and worth a permanent ratchet.)
    """
    edges = _cycle(4)
    base = magnetic_laplacian(4, edges, charges=[0.0, 0.0, 0.0, 0.0])
    charged = magnetic_laplacian(4, edges, charges=[0.25, 0.0, 0.0, 0.0])
    for name in _COMPLEX_SOLVERS:
        fn = _SOLVERS[name]
        a, b = fn(base), fn(charged)
        moved = max(abs(x - y) for x, y in zip(a, b))
        assert moved > 1e-6, (
            f"{name} is PHASE-BLIND: a gauge-nontrivial charge around a cycle "
            f"left the spectrum unchanged ({a} vs {b}). The solver is "
            f"discarding the imaginary part of a complex Hermitian operand."
        )


def test_gauge_trivial_charge_on_a_tree_does_not_move_the_spectrum():
    """The dual fact, and the correction to #1440's "second defect" claim.

    A star is a TREE: it has no independent cycle, so EVERY charge assignment on
    it is gauge-equivalent to the zero assignment and the spectrum is genuinely
    phase-INVARIANT. The identical outputs #1440 observed for charges on edge 0
    / 1 / 2 / none were therefore a CORRECT invariance being reported through a
    (then) wrong solver — not evidence that the imaginary part was discarded.
    ``mat_eigvals`` reads the imaginary part correctly; see
    :func:`test_mat_eigvals_reads_the_imaginary_part`.
    """
    edges = [(0, 1), (1, 2), (1, 3)]
    ref = _s_hermitian(magnetic_laplacian(4, edges, charges=[0.0, 0.0, 0.0]))
    for k in range(3):
        c = [0.0, 0.0, 0.0]
        c[k] = 0.1
        for name in _COMPLEX_SOLVERS:
            got = _SOLVERS[name](magnetic_laplacian(4, edges, charges=c))
            for x, y in zip(got, ref):
                assert abs(x - y) < _TOL, (
                    f"{name}: a charge on tree edge {k} MOVED the spectrum "
                    f"({got} != {ref}) — every charge on a tree is gauge-trivial"
                )
            # ...and it is still a Laplacian: λ_min == 0.
            assert abs(got[0]) < _TOL


def test_mat_eigvals_reads_the_imaginary_part():
    """Direct disproof of the "phase-blind / silently discards the imaginary
    part" reading: a real-matrix answer is impossible for these operands.

    If the imaginary part were dropped, the rotation would report ``{0, 0}``
    (the discarded-imag matrix ``[[0,-1],[1,0]]`` is real already, so use the
    Hermitian Pauli-Y, whose real part is the ZERO matrix)."""
    pauli_y = Mat.from_rows([[0, -1j], [1j, 0]], is_complex=True)
    ev = sorted(complex(z).real for z in mat_eigvals(pauli_y))
    assert abs(ev[0] + 1.0) < _TOL and abs(ev[1] - 1.0) < _TOL, (
        f"mat_eigvals(Pauli-Y) = {ev}, expected [-1, 1]. Its real part is the "
        f"ZERO matrix, so a phase-blind solver would return [0, 0]."
    )
    rot = Mat.from_rows([[0, -1], [1, 0]], is_complex=True)
    got = sorted(complex(z).imag for z in mat_eigvals(rot))
    assert abs(got[0] + 1.0) < _TOL and abs(got[1] - 1.0) < _TOL, (
        f"mat_eigvals([[0,-1],[1,0]]) imag parts {got}, expected [-1, 1] (±i)"
    )


# ── 6. Hessenberg structure + PROOF the ratchet goes red pre-rc285 ────

def test_hessenberg_reduction_is_a_similarity_and_is_structurally_hessenberg():
    """The rc285 fix itself: ``_hessenberg_complex`` must (a) zero the
    sub-subdiagonal EXACTLY — the deflation test's soundness is structural, not
    a tolerance — and (b) preserve the spectrum, being a unitary similarity.

    The spectrum check uses ``hermitian_eigendecompose`` as an INDEPENDENT
    oracle on both the input and its reduction. Deliberately not ``mat_eigvals``
    on both sides: that would check the fix against itself, and re-feeding a
    reduced matrix to ``mat_eigvals`` also re-runs balancing over a
    now-non-symmetric operand, which is slow and tests nothing about the
    reduction.
    """
    for label, n, edges in _graphs():
        L = dense_laplacian(n, edges)
        A = [[complex(L[i, j]) for j in range(n)] for i in range(n)]
        H = _hessenberg_complex(A)
        for i in range(n):
            for j in range(i - 1):
                assert H[i][j] == 0j, (
                    f"{label}: _hessenberg_complex left H[{i}][{j}] = "
                    f"{H[i][j]!r}; the sub-subdiagonal must be EXACTLY zero"
                )
        before = _s_hermitian(L)
        after = sorted(
            float(v) for v in
            hermitian_eigendecompose(Mat.from_rows(H, is_complex=True))[0]
        )
        for a, b in zip(before, after):
            assert abs(a - b) < _TOL, (
                f"{label}: the reduction MOVED the spectrum — it is not a "
                f"similarity. {before} != {after}"
            )


def test_householder_reflector_is_a_reflector_at_every_scale():
    """``_householder_reflector`` must satisfy its DEFINING property —
    ``P·x = α·e₁`` with ``|α| = ‖x‖`` — for every input scale.

    This is the second defect rc285 found (not in #1440). ``_fhypot`` is a
    bounded-denominator Class-N rational cascade, NOT libm ``hypot``: it carries
    ≈ −2e−5 relative error at 1e-12 and returns **exactly 0.0** below ≈1e-17. So
    the old unscaled ``phase = x0 / _fhypot(x0)`` was not a unit complex number
    for a small ``x0`` (measured 1.25 at ``x0 = 6.9e-17``), ``|α| ≠ ‖x‖``, and
    ``P`` was not a reflector — which made the Hessenberg reduction a
    NON-similarity that moved the spectrum by 1.4e-2.

    The ``tiny-x0`` case below is the exact shape the 11-vertex broom drives.
    """
    cases = {
        "plain real": [3.0 + 0j, 4.0 + 0j, 0j],
        "complex": [1 + 2j, 3 - 1j, 0.5 + 0.25j],
        "tiny x0, O(1) tail": [6.938893903907228e-17 + 0j, 0.7385489458759964 + 0j],
        "x0 exactly zero": [0j, 1.0 + 0j, 2.0 + 0j],
        "uniformly tiny": [1e-17 + 0j, 2e-17 + 0j, 3e-17 + 0j],
        "uniformly huge": [1e17 + 0j, 2e17 + 0j, 3e17 + 0j],
        "complex tiny": [1e-18 + 1e-18j, 4e-18 - 2e-18j],
    }
    for label, x in cases.items():
        refl = _householder_reflector(list(x))
        assert refl is not None, f"{label}: reflector unexpectedly declined"
        v, beta = refl
        # P·x, computed as x − β·v·(vᴴ·x) on the SCALED v the helper returns.
        # v is scaled by 1/s, so rescale x the same way (P is scale-invariant).
        s = max(_cmax_component(z) for z in x)
        xs = [z / s for z in x]
        dot = sum(v[i].conjugate() * xs[i] for i in range(len(xs))) * beta
        Px = [xs[i] - v[i] * dot for i in range(len(xs))]
        nrm = _fsqrt(sum((z.conjugate() * z).real for z in xs))  # Class-N √
        for i in range(1, len(Px)):
            assert _modulus_c(Px[i]) < 1e-13 * (nrm + 1.0), (
                f"{label}: P·x component {i} = {Px[i]!r} not annihilated "
                f"(‖x‖={nrm}); P is not a reflector"
            )
        assert abs(_modulus_c(Px[0]) - nrm) < 1e-13 * (nrm + 1.0), (
            f"{label}: |α| = {_modulus_c(Px[0])} != ‖x‖ = {nrm} — the phase is "
            f"not unit-modulus, so P is not a reflector"
        )


def test_complex_qr_is_unitary_at_every_scale():
    """``matrix_cascades.qr`` carried the SAME unsafe ``x0/_modulus(x0)``
    division as the Hessenberg reduction — a third site, found by grepping for
    the pattern rather than by a failing test.

    Only COMPLEX input reaches that loop (real input dispatches to the native
    ``srmech_qr_f64``), so it is the complex QR that must be pinned: ``Q`` must
    be unitary and ``Q·R`` must reproduce ``A``, at every input magnitude. On
    the ``tiny x0`` row the pre-rc285 reflector left a residual tail of 1.6e-1
    and produced ``|α| = 0.7205`` against ``‖x‖ = 0.7385``.
    """
    cases = {
        "plain complex": [[1 + 2j, 3 - 1j], [0.5 + 0.25j, 2 + 0j]],
        "tiny x0": [[6.938893903907228e-17 + 0j, 1 + 0j],
                    [0.7385489458759964 + 0j, 2 + 0j]],
        "uniformly tiny": [[1e-17 + 0j, 2e-17 + 0j], [3e-17 + 0j, 4e-17 + 0j]],
        "uniformly huge": [[1e17 + 0j, 2e17 + 0j], [3e17 + 0j, 4e17 + 0j]],
        "zeros in pivot": [[0j, 1 + 0j, 2 + 0j], [0j, 0j, 3 + 1j], [1 + 0j, 0j, 0j]],
    }
    for label, rows in cases.items():
        A = Mat.from_rows(rows, is_complex=True)
        Q, R = cascade_qr(A)
        m, kk, nn = Q.n_rows, Q.n_cols, R.n_cols
        scale = max(_cmax_component(complex(z)) for r in rows for z in r)
        for i in range(kk):                       # QᴴQ == I
            for j in range(kk):
                s = sum(Q[t, i].conjugate() * Q[t, j] for t in range(m))
                want = 1.0 if i == j else 0.0
                assert _modulus_c(s - want) < 1e-12, (
                    f"{label}: QᴴQ[{i}][{j}] = {s!r}, expected {want} — Q is "
                    f"not unitary, so the reflector is not a reflector"
                )
        for i in range(m):                        # Q·R == A
            for j in range(nn):
                s = sum(Q[i, t] * R[t, j] for t in range(kk))
                assert _modulus_c(s - complex(rows[i][j])) < 1e-12 * scale, (
                    f"{label}: (Q·R)[{i}][{j}] = {s!r} != A = {rows[i][j]!r}"
                )


def test_hessenberg_of_a_symmetric_matrix_is_symmetric_tridiagonal():
    """A Householder-Hessenberg reduction of a HERMITIAN matrix must come out
    Hermitian TRIDIAGONAL — that is the structural signature of a genuine
    unitary similarity, and it is what broke when the reflector's phase was not
    unit-modulus (1.6e-1 asymmetry on the 11-vertex broom).

    A cheap, total structural check: no tolerance-fitting, no oracle.
    """
    for label, n, edges in _graphs():
        L = dense_laplacian(n, edges)
        A = [[complex(L[i, j]) for j in range(n)] for i in range(n)]
        H = _hessenberg_complex(A)
        asym = max(
            _modulus_c(H[i][j] - H[j][i].conjugate())
            for i in range(n) for j in range(n)
        )
        assert asym < 1e-12, (
            f"{label}: Hessenberg reduction of a symmetric Laplacian left "
            f"|H − Hᴴ| = {asym:.3e}; the reduction is not a similarity"
        )
        offtri = max(
            [
                _modulus_c(H[i][j])
                for i in range(n) for j in range(n) if j - i > 1 or i - j > 1
            ]
            or [0.0]
        )
        assert offtri < 1e-12, (
            f"{label}: Hermitian input must reduce to TRIDIAGONAL form; "
            f"max off-tridiagonal = {offtri:.3e}"
        )


def _qr_complex_list_pre_rc285(rows):
    """The pre-rc285 ``_qr_complex_list``: identical Householder QR except that
    the reflector is built from the UNSCALED column, so ``phase = x0/_fhypot(x0)``
    is not unit-modulus for a small ``x0`` (defect 3). Inlined so the control
    below is a complete rc282 reproduction and can be asserted against the exact
    numbers #1440 reported."""
    m = len(rows)
    R = [[complex(rows[i][j]) for j in range(m)] for i in range(m)]
    Q = [[1 + 0j if i == j else 0j for j in range(m)] for i in range(m)]
    for k in range(m):
        normx2 = 0.0
        for i in range(k, m):
            normx2 += (R[i][k].conjugate() * R[i][k]).real
        if normx2 <= 0.0:
            continue
        normx = _fsqrt(normx2)
        x0 = R[k][k]
        modx0 = _fhypot(x0.real, x0.imag)
        phase = (x0 / modx0) if modx0 > 0.0 else complex(1.0, 0.0)
        alpha = -phase * normx
        v = [R[i][k] for i in range(k, m)]
        v[0] = v[0] - alpha
        vhv = 0.0
        for vi in v:
            vhv += (vi.conjugate() * vi).real
        if vhv == 0.0:
            continue
        beta = 2.0 / vhv
        for j in range(m):
            s = 0j
            for idx, i in enumerate(range(k, m)):
                s += v[idx].conjugate() * R[i][j]
            s *= beta
            for idx, i in enumerate(range(k, m)):
                R[i][j] -= v[idx] * s
        for i in range(m):
            s = 0j
            for idx, jj in enumerate(range(k, m)):
                s += Q[i][jj] * v[idx]
            s *= beta
            for idx, jj in enumerate(range(k, m)):
                Q[i][jj] -= s * v[idx].conjugate()
    return Q, R


def _mat_eigvals_pre_rc285(a, *, max_sweeps=500):
    """A faithful copy of :func:`mat_eigvals` MINUS the ``_hessenberg_complex``
    pre-step — i.e. the shipped algorithm as it stood at 0.9.0rc282 and earlier.

    Same balancing, same Wilkinson/EISPACK shift ladder, same single-subdiagonal
    deflation test, same ``_eig2x2`` closed form. Kept so the ratchet's redness
    is a live, executing fact rather than a claim in a commit message. (Mirrors
    the ``_mat_eigvals_unbalanced`` control in
    ``test_mat_eigvals_balancing_rc29.py``.)

    It is a COMPLETE rc282 reproduction: no Hessenberg reduction (defect 1), the
    QR step over the whole leading block with a single-subdiagonal deflation
    test (defect 2), and ``_qr_complex_list_pre_rc285``'s unscaled reflectors
    (defect 3). That is what lets the assertions below pin the EXACT numbers
    #1440 reported, rather than merely "something is wrong".
    """
    n = a.n_rows
    H = [[complex(a[i, j]) for j in range(n)] for i in range(n)]
    if n == 1:
        return [H[0][0]]
    H = _balance_radix2(H)
    # <<< the missing line: H = _hessenberg_complex(H) >>>
    eigs = []
    m = n
    sweeps = 0
    it = 0
    ceiling = max_sweeps * n
    while m > 0:
        if m == 1:
            eigs.append(H[0][0])
            break
        scale = _modulus_c(H[m - 2][m - 2]) + _modulus_c(H[m - 1][m - 1])
        if _modulus_c(H[m - 1][m - 2]) <= _MAT_EIG_DEFLATE_TOL * (scale + 1e-300):
            eigs.append(H[m - 1][m - 1])
            m -= 1
            it = 0
            continue
        if m == 2:
            l1, l2 = _eig2x2(H[0][0], H[0][1], H[1][0], H[1][1])
            eigs.append(l1)
            eigs.append(l2)
            break
        if it == 10 or it == 20:
            mu = _modulus_c(H[m - 1][m - 2])
            if m - 3 >= 0:
                mu += _modulus_c(H[m - 2][m - 3])
            mu = complex(mu, 0.0)
        else:
            l1, l2 = _eig2x2(
                H[m - 2][m - 2], H[m - 2][m - 1], H[m - 1][m - 2], H[m - 1][m - 1]
            )
            dd = H[m - 1][m - 1]
            mu = l1 if _modulus_c(l1 - dd) < _modulus_c(l2 - dd) else l2
        sub = [[H[i][j] - (mu if i == j else 0j) for j in range(m)] for i in range(m)]
        Q, R = _qr_complex_list_pre_rc285(sub)
        rq = mat_matmul(
            Mat.from_rows(R, is_complex=True), Mat.from_rows(Q, is_complex=True)
        )
        for i in range(m):
            for j in range(m):
                H[i][j] = complex(rq[i, j]) + (mu if i == j else 0j)
        sweeps += 1
        it += 1
        if sweeps > ceiling:
            raise RuntimeError("pre-rc285 control failed to converge")
    return eigs


def test_pre_rc285_sweep_without_hessenberg_is_red():
    """PROOF OF REDNESS. The pre-rc285 algorithm reproduces the reported wrong
    answer, so the ratchet above is demonstrably not vacuous.

    On #1440's exact edge list ``[(0,1), (1,2), (1,3)]`` — a star with the hub at
    vertex **1** — the sweep sees ``H[3][2] == 0`` (leaves 2 and 3 are
    non-adjacent), deflates ``H[3][3] = 1`` as if converged, and then returns the
    spectrum of the WRONG leading 3×3 block, whose extreme roots solve
    ``x² − 4x + 1``: ``2 ∓ √3`` ≈ 0.267949 / 3.732051. Exactly the issue's
    numbers.

    **And the SAME star with the hub at vertex 0 fails differently** — ``2 ∓ √2``
    ≈ 0.585786 / 3.414214, from a leading block with determinant 2 instead of 1.
    Two labellings of one graph, two different wrong answers: the defect is
    label-order dependent, which is the sharpest statement of it and the reason
    :func:`test_spectrum_is_invariant_under_vertex_relabelling` is the strongest
    ratchet in this module.
    """
    issue_edges = [(0, 1), (1, 2), (1, 3)]            # #1440's exact repro
    L = dense_laplacian(4, issue_edges)
    old = sorted(complex(z).real for z in _mat_eigvals_pre_rc285(L))
    new = sorted(complex(z).real for z in mat_eigvals(L))

    # The invariant this module ratchets is VIOLATED by the old code...
    assert old[0] > 0.2, (
        f"the pre-rc285 control no longer reproduces #1440 (λ_min={old[0]!r}); "
        f"if the control drifted out of faithfulness, the redness proof is void"
    )
    assert abs(old[0] - 0.2679491924311227) < 1e-9, f"expected 2−√3, got {old[0]}"
    assert abs(old[3] - 3.7320508075688776) < 1e-9, f"expected 2+√3, got {old[3]}"
    # ...and SATISFIED by the shipped code.
    assert abs(new[0]) < _TOL, f"rc285 mat_eigvals λ_min = {new[0]!r}, must be 0"
    assert abs(new[3] - 4.0) < _TOL, f"rc285 mat_eigvals λ_max = {new[3]!r}, must be 4"

    # The signature the issue described: trace preserved, interior exact, the
    # extreme PAIR keeping its correct sum while splitting about the mean wrongly.
    assert abs(sum(old) - sum(new)) < _TOL, "trace should have been preserved"
    assert abs((old[0] + old[3]) - (new[0] + new[3])) < _TOL, "extreme sum preserved"

    # Same graph, hub relabelled to vertex 0: a DIFFERENT wrong answer.
    L0 = dense_laplacian(4, _star(4))
    old0 = sorted(complex(z).real for z in _mat_eigvals_pre_rc285(L0))
    assert abs(old0[0] - 0.5857864376269049) < 1e-9, f"expected 2−√2, got {old0[0]}"
    assert abs(old0[3] - 3.4142135623730945) < 1e-9, f"expected 2+√2, got {old0[3]}"
    assert abs(old0[0] - old[0]) > 0.3, (
        "the two labellings must fail DIFFERENTLY — that is the label-order "
        "dependence this ratchet exists to catch"
    )
    # rc285 gives the same, correct answer for both labellings.
    new0 = sorted(complex(z).real for z in mat_eigvals(L0))
    for a, b in zip(new0, new):
        assert abs(a - b) < _TOL, f"rc285 still label-dependent: {new0} != {new}"


def test_pre_rc285_control_is_red_on_a_relabelled_path_too():
    """The defect was never star-specific. A PATH relabelled so its last two
    vertices are non-adjacent (0-2-1-3) was equally wrong — pre-rc285 it
    returned ``[1, 1, 1, 3]`` for a true spectrum of ``[0, 2−√2, 2, 2+√2]``."""
    L = dense_laplacian(4, [(0, 2), (2, 1), (1, 3)])
    old = sorted(complex(z).real for z in _mat_eigvals_pre_rc285(L))
    assert old[0] > 0.5, f"expected the historic wrong λ_min ≈ 1, got {old[0]}"
    new = sorted(complex(z).real for z in mat_eigvals(L))
    ref = _s_hermitian(L)
    assert abs(new[0]) < _TOL
    for a, b in zip(new, ref):
        assert abs(a - b) < _TOL, f"{new} != {ref}"


def test_pre_rc285_control_agrees_with_shipped_code_where_the_bug_does_not_bite():
    """Faithfulness check on the control: where ``H[n-1][n-2] != 0`` the missing
    reduction changes nothing, and the two must agree. Without this, the control
    could be red for the wrong reason."""
    for n in (3, 4, 5, 6):
        for name in ("path", "cycle", "complete"):
            edges = _FAMILIES[name](n)
            L = dense_laplacian(n, edges)
            old = sorted(complex(z).real for z in _mat_eigvals_pre_rc285(L))
            new = sorted(complex(z).real for z in mat_eigvals(L))
            for a, b in zip(old, new):
                assert abs(a - b) < 1e-8, f"{name}-{n}: control {old} vs {new}"


# ── 7. weighted + disconnected coverage ───────────────────────────────

@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_weighted_star_lambda_min_is_zero(solver):
    """Weights do not change the kernel — row sums are still zero."""
    n = 7
    edges = _star(n)
    weights = [0.5, 3.0, 1e-3, 12.0, 0.25, 7.5]
    ev = _SOLVERS[solver](dense_laplacian(n, edges, weights))
    assert abs(ev[0]) < _TOL, f"{solver} weighted star: λ_min={ev[0]!r}, spectrum={ev}"


@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_disconnected_forest_has_one_zero_per_COMPONENT(solver):
    """A k-component graph has a k-dimensional kernel. Two disjoint stars → the
    two smallest eigenvalues are both 0. This is the multiplicity form of the
    invariant, and it is where a premature deflation shows up loudest."""
    edges = [(0, 1), (0, 2), (0, 3)] + [(4, 5), (4, 6), (4, 7)]
    ev = _SOLVERS[solver](dense_laplacian(8, edges))
    assert abs(ev[0]) < _TOL and abs(ev[1]) < _TOL, (
        f"{solver}: a 2-component forest must have a 2-D kernel; got {ev}"
    )
    assert ev[2] > 0.5, f"{solver}: kernel should be exactly 2-D; got {ev}"


@pytest.mark.parametrize("solver", sorted(_SOLVERS))
def test_isolated_vertex_star(solver):
    """A star plus an isolated vertex — the isolated vertex contributes a zero
    row/column, which is precisely an ``H[n-1][n-2] == 0`` shape."""
    ev = _SOLVERS[solver](dense_laplacian(6, _star(5)))
    assert abs(ev[0]) < _TOL and abs(ev[1]) < _TOL, f"{solver}: {ev}"


def test_every_shipped_eigensolver_is_covered():
    """Coverage ratchet: if a new public eigensolver lands in
    ``srmech.amsc.laplacian``, it must be added to ``_SOLVERS`` here. #1440
    existed because one solver of four sat outside everyone's mental test
    matrix."""
    import srmech.amsc.laplacian as _lap

    shipped = {
        name for name in _lap.__all__
        if ("eigvals" in name or "eigendecompose" in name)
        and not name.startswith("_")
    }
    covered = set(_SOLVERS) - {"matrix_cascades.eigvals"}
    missing = shipped - covered
    assert not missing, (
        f"eigensolver(s) {sorted(missing)} are exported from "
        f"srmech.amsc.laplacian but are NOT covered by the λ_min == 0 ratchet. "
        f"Add them to _SOLVERS in this module — #1440 is exactly what happens "
        f"when a solver sits outside the test matrix."
    )


def test_no_pair_of_solvers_is_secretly_the_same_object():
    """Sanity: the six adapters must reach six distinct callables, or 'every
    solver agrees' is a tautology."""
    fns = [
        mat_eigvals, jacobi_eigvals, hermitian_eigendecompose,
        symmetric_eigendecompose, mat_hermitian_eigendecompose, cascade_eigvals,
    ]
    for a, b in itertools.combinations(fns, 2):
        assert a is not b
