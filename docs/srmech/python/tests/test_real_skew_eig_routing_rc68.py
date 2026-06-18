"""rc68 — real-skew eig → iS-Hermitian cascade route.

The 2 eig sites in `qm/so8.py` operate on **real antisymmetric** matrices (the
`J` complex-structure operator and `ad(H)` for a Cartan element — both with
purely-imaginary `±i·weight` spectra). For real skew `S`, `iS` is Hermitian, so
eigenpairs come from the numpy-free `mat_hermitian_eigendecompose(iS)`:
eigenvalues `λ_S = −i·μ` (μ real, ascending), eigenvectors the **same** `V`. The
private `so8._real_skew_eig` routes both onto that Hermitian cascade — no numpy
eig.

The eigenvector phase / degenerate-eigenspace basis is solver-chosen, so this is
only sound because so8 consumes `V` *invariantly*: the triplet uses the `+i`
eigenspace SPAN (projector basis-invariant), the weights use the scale/phase-
invariant Rayleigh quotient. Both invariances are checked here on a degenerate
(mult-3, like so8's `J`) real-skew matrix.

rc123 (numpy-free, #564): this test is itself numpy-FREE — `_real_skew_eig`
returns ``(eigenvalues: list[complex], columns: list[list[complex]])``; the
eigenrelation / unitarity / span / Rayleigh checks are pure-Python over those
lists (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""

from __future__ import annotations

import math
import random
import re
import pathlib

from srmech.qm.so8 import _real_skew_eig


def _matmul(a, b):
    """Nested-list matrix multiply (real or complex)."""
    m, k, n = len(a), len(a[0]), len(b[0])
    return [[sum(a[i][t] * b[t][j] for t in range(k)) for j in range(n)]
            for i in range(m)]


def _matvec(a, v):
    return [sum(a[i][t] * v[t] for t in range(len(v))) for i in range(len(a))]


def _transpose(a):
    return [[a[i][j] for i in range(len(a))] for j in range(len(a[0]))]


def _conj_T(a):
    return [[a[i][j].conjugate() if isinstance(a[i][j], complex) else a[i][j]
             for i in range(len(a))] for j in range(len(a[0]))]


def _orthonormal_random(rng, n):
    """A random real orthonormal n×n matrix via Gram-Schmidt on Gaussian columns."""
    cols = []
    for _ in range(n):
        v = [rng.gauss(0.0, 1.0) for _ in range(n)]
        for q in cols:
            proj = sum(q[i] * v[i] for i in range(n))
            v = [v[i] - proj * q[i] for i in range(n)]
        nrm = sum(x * x for x in v) ** 0.5
        cols.append([x / nrm for x in v])
    # columns → rows
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def _degenerate_real_skew(seed: int = 0, n_blocks: int = 3):
    """A real antisymmetric matrix with eigenvalues ±i each of multiplicity
    ``n_blocks`` (the so8-`J` shape), randomly conjugated to be dense.
    Returns a nested ``list[list[float]]`` (numpy-free)."""
    rng = random.Random(seed)
    n = 2 * n_blocks
    S = [[0.0] * n for _ in range(n)]
    for b in range(n_blocks):
        S[2 * b][2 * b + 1] = 1.0
        S[2 * b + 1][2 * b] = -1.0
    q = _orthonormal_random(rng, n)
    S = _matmul(_matmul(q, S), _transpose(q))
    # re-skew-symmetrise the round-off: 0.5·(S − Sᵀ).
    return [[0.5 * (S[i][j] - S[j][i]) for j in range(n)] for i in range(n)]


def test_eig_real_skew_reconstructs():
    """S·V = V·diag(λ), λ purely imaginary, on degenerate + non-degenerate skew."""
    for seed, nb in [(0, 3), (1, 2), (2, 1), (7, 4)]:
        S = _degenerate_real_skew(seed, nb)
        n = len(S)
        lam, cols = _real_skew_eig(S)
        # eigenrelation: S·v_k = λ_k·v_k for each column.
        for k in range(n):
            sv = _matvec(S, cols[k])
            lv = [lam[k] * cols[k][i] for i in range(n)]
            err = max(abs(sv[i] - lv[i]) for i in range(n))
            assert err < 1e-9
        # eigenvalues purely imaginary.
        assert all(abs(lam[k].real) < 1e-9 for k in range(n))
        # unitary: Vᴴ·V = I (columns orthonormal).
        for a in range(n):
            for b in range(n):
                dot = sum(cols[a][i].conjugate() * cols[b][i] for i in range(n))
                expected = 1.0 if a == b else 0.0
                assert abs(dot - expected) < 1e-9


def _plus_projector(lam, cols, n):
    """The projector onto the +i eigenspace (basis-invariant): P = Q·Qᴴ for an
    orthonormal Q spanning the +i columns (they are already orthonormal)."""
    plus = [cols[k] for k in range(n) if lam[k].imag > 0.5]
    # P[i][j] = Σ_c q_c[i]·conj(q_c[j]).
    P = [[sum(q[i] * q[j].conjugate() for q in plus) for j in range(n)]
         for i in range(n)]
    return P


def test_plus_eigenspace_span_is_basis_invariant():
    """The +i eigenspace PROJECTOR is invariant to the (degenerate) basis the
    cascade chooses — re-running the route twice yields the SAME projector,
    so so8's triplet span is well-defined despite the arbitrary degenerate basis."""
    S = _degenerate_real_skew(0, 3)
    n = len(S)
    lam1, cols1 = _real_skew_eig(S)
    lam2, cols2 = _real_skew_eig(S)
    P1 = _plus_projector(lam1, cols1, n)
    P2 = _plus_projector(lam2, cols2, n)
    worst = max(abs(P1[i][j] - P2[i][j]) for i in range(n) for j in range(n))
    assert worst < 1e-9
    # the projector has rank 3 (the +i multiplicity) — trace == 3 (real).
    trace = sum(P1[i][i] for i in range(n))
    assert abs(trace.real - 3.0) < 1e-9 and abs(trace.imag) < 1e-9


def test_rayleigh_weights_are_well_defined():
    """Per-column Rayleigh-quotient weights (so8's weight route; scale/phase-
    invariant) are the ±1 multiset (the ±i·weight spectrum), independent of the
    degenerate basis choice — two runs give the same sorted weight multiset."""
    S = _degenerate_real_skew(3, 3)
    n = len(S)

    def weights(cols):
        out = []
        for k in range(n):
            v = cols[k]
            # iS·v then the Hermitian Rayleigh quotient ⟨v, iS v⟩ / ⟨v, v⟩.
            isv = [1j * x for x in _matvec(S, v)]
            num = sum(v[i].conjugate() * isv[i] for i in range(n))
            den = sum(v[i].conjugate() * v[i] for i in range(n))
            out.append(round(float((num / den).real), 6))
        return sorted(out)

    _, cols1 = _real_skew_eig(S)
    _, cols2 = _real_skew_eig(S)
    assert weights(cols1) == weights(cols2)
    # the spectrum of iS is ±1 (mult 3 each), so the weight multiset is that.
    assert weights(cols1) == sorted([-1.0] * 3 + [1.0] * 3)


def test_no_np_linalg_eig_call_in_so8():
    """so8 no longer CALLS numpy eig (only _real_skew_eig); the helper is wired."""
    import srmech

    src = (pathlib.Path(srmech.__file__).parent / "qm" / "so8.py").read_text(encoding="utf-8")
    assert not re.search(r"\bnp\.linalg\.eig\s*\(", src)
    assert src.count("_real_skew_eig(") >= 3  # def + 2 call sites
