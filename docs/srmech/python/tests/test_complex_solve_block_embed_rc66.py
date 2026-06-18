"""rc66 — complex inv → real 2n×2n block embedding of native ``dense_solve``.

The numpy-removal ``linalg_fft`` sweep's first NEW-capability step (the trivial
carrier-swaps are exhausted at the rc65 floor). The lone complex
``np.linalg.inv`` site — ``qm/pseudo_hermitian.py`` ``construct_eta_from_
eigendecomposition``'s ``η = (V·Vᴴ)⁻¹`` — routes onto a new private Class-L
helper ``laplacian._dense_solve_complex``.

A complex system ``(Aᵣ + i Aᵢ)(u + i v) = (bᵣ + i bᵢ)`` is, splitting real and
imaginary parts, the **real** ``2n×2n`` system::

    [[Aᵣ, −Aᵢ], [Aᵢ, Aᵣ]] · [u; v] = [bᵣ; bᵢ]

so ``X = u + i v``. The embedding is exact and rides the shipped *native* real
``dense_solve``; for a well-conditioned ``A`` (the Gram matrix ``V·Vᴴ`` is HPD)
the complex inverse is ``_dense_solve_complex(A, eye(n))`` (``A·X = I``).

numpy-FREE (#564): numpy is GONE from srmech, so this test runs with numpy NOT
installed. The solve oracle is the DEFINING IDENTITY (``M·M⁻¹ = I`` / ``A·x = b``)
checked via plain-list COMPLEX matmul — never ``np.linalg.solve``/``inv``. Inputs
are stdlib ``random.Random`` complex nested lists, never ndarrays.
"""

from __future__ import annotations

import random
import re
import pathlib

from srmech.amsc.laplacian import _dense_solve_complex


def _cmatmul(a, b):
    """Plain-list complex matrix product a·b (b is a matrix)."""
    n, k, m = len(a), len(b), len(b[0])
    return [
        [sum(a[i][p] * b[p][j] for p in range(k)) for j in range(m)]
        for i in range(n)
    ]


def _cmatvec(a, x):
    """Plain-list complex matrix·vector a·x."""
    n, k = len(a), len(x)
    return [sum(a[i][p] * x[p] for p in range(k)) for i in range(n)]


def _rand_cmat(n, m, rng):
    return [
        [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(m)]
        for _ in range(n)
    ]


def _hpd_gram(n, rng):
    """An HPD Gram matrix M = V·Vᴴ (Hermitian positive-definite)."""
    v = _rand_cmat(n, n, rng)
    return [
        [sum(v[i][p] * v[j][p].conjugate() for p in range(n)) for j in range(n)]
        for i in range(n)
    ]


def test_block_solve_inverse_satisfies_defining_identity():
    """_dense_solve_complex(M, I) is M⁻¹ for HPD Gram M = V·Vᴴ — verified by the
    defining identity M·M⁻¹ = I via plain-list complex matmul (no np.linalg.inv
    oracle)."""
    rng = random.Random(0)
    for n in (2, 3, 5, 8):
        m = _hpd_gram(n, rng)
        eye = [[complex(1.0 if i == j else 0.0) for j in range(n)] for i in range(n)]
        inv_blk = _dense_solve_complex(m, eye)
        prod = _cmatmul(m, inv_blk)
        for i in range(n):
            for j in range(n):
                want = complex(1.0 if i == j else 0.0)
                assert abs(prod[i][j] - want) < 1e-9


def test_block_solve_general_residual_is_zero():
    """_dense_solve_complex(A, b) solves A·x = b (general complex) — verified by
    the residual ``A·x − b ≈ 0`` over plain-list complex matmul, vector AND
    matrix RHS (no np.linalg.solve oracle)."""
    rng = random.Random(7)
    for n in (2, 4, 6):
        A = _rand_cmat(n, n, rng)
        # vector RHS
        b = [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]
        x = _dense_solve_complex(A, b)
        resid = [(_cmatvec(A, x)[i] - b[i]) for i in range(n)]
        assert max(abs(r) for r in resid) < 1e-9
        # matrix RHS
        B = _rand_cmat(n, 3, rng)
        X = _dense_solve_complex(A, B)
        prod = _cmatmul(A, X)
        for i in range(n):
            for j in range(3):
                assert abs(prod[i][j] - B[i][j]) < 1e-9


def test_construct_eta_still_pseudo_hermitian():
    """The η construction still produces a valid η-metric (O†η = ηO).

    numpy-FREE since rc124 — pseudo_hermitian flipped onto the Mat carrier, so the
    η = (V·Vᴴ)⁻¹ solve routes through ``mat_solve`` (not ``_dense_solve_complex``);
    the operator + oracle are numpy-free here too."""
    from srmech.amsc.mat import Mat
    from srmech.qm.pseudo_hermitian import (
        construct_eta_from_eigendecomposition,
        is_pseudo_hermitian,
    )

    # A real-spectrum non-Hermitian operator (PT-symmetric-style 2×2).
    O = Mat.from_rows([[2.0, 1.0], [0.0, 3.0]], is_complex=True)
    eta = construct_eta_from_eigendecomposition(O)
    # η Hermitian (direct Mat-entry check, no numpy oracle).
    n = eta.shape[0]
    herm_dev = max(
        abs(eta[i, j] - eta[j, i].conjugate()) for i in range(n) for j in range(n)
    )
    assert herm_dev < 1e-9
    # O is η-pseudo-Hermitian: O† η = η O
    assert is_pseudo_hermitian(O, eta, atol=1e-9)


def test_no_residual_np_linalg_inv_in_pseudo_hermitian():
    """No `np.linalg.inv(` survives in pseudo_hermitian; the numpy-free route is
    in place (rc124: the η solve now rides the Mat-carrier ``mat_solve``)."""
    import srmech

    src = (
        pathlib.Path(srmech.__file__).parent / "qm" / "pseudo_hermitian.py"
    ).read_text(encoding="utf-8")
    assert not re.search(r"\b(?:np|numpy)\.linalg\.inv\s*\(", src)
    assert "mat_solve(" in src
