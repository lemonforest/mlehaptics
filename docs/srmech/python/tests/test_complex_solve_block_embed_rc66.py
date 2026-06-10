"""rc66 — complex inv → real 2n×2n block embedding of native ``dense_solve``.

The numpy-removal ``linalg_fft`` sweep's first NEW-capability step (the trivial
carrier-swaps are exhausted at the rc65 floor). The lone complex
``np.linalg.inv`` site — ``qm/pseudo_hermitian.py`` ``construct_eta_from_
eigendecomposition``'s ``η = (V·Vᴴ)⁻¹`` — routes onto a new private Class-L
helper ``laplacian._dense_solve_complex``.

A complex system ``(Aᵣ + i Aᵢ)(u + i v) = (bᵣ + i bᵢ)`` is, splitting real and
imaginary parts, the **real** ``2n×2n`` system::

    [[Aᵣ, −Aᵢ], [Aᵢ, Aᵣ]] · [u; v] = [bᵣ; bᵢ]

so ``X = u + i v``. The embedding is exact (NumPy a carrier only — ``concatenate``
/ slice / ``.real`` / ``.imag``) and rides the shipped *native* real
``dense_solve``; for a well-conditioned ``A`` (the Gram matrix ``V·Vᴴ`` is HPD)
it is value-faithful to NumPy's complex ``inv`` / ``solve`` to ~1e-9. The
complex inverse is ``_dense_solve_complex(A, eye(n))`` (``A·X = I``).
"""

from __future__ import annotations

import re
import pathlib

import numpy as np

from srmech.amsc.laplacian import _dense_solve_complex


def test_block_solve_matches_numpy_inv_hpd():
    """_dense_solve_complex(M, I) == numpy.linalg.inv(M) for HPD Gram M = V·Vᴴ."""
    rng = np.random.default_rng(0)
    for n in (2, 3, 5, 8):
        V = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
        M = V @ V.conj().T  # Hermitian positive-definite
        inv_blk = _dense_solve_complex(M, np.eye(n, dtype=np.complex128))
        np.testing.assert_allclose(inv_blk, np.linalg.inv(M), atol=1e-9)
        # defining identity M·M⁻¹ = I
        np.testing.assert_allclose(M @ inv_blk, np.eye(n), atol=1e-9)


def test_block_solve_matches_numpy_general_solve():
    """_dense_solve_complex(A, b) == numpy.linalg.solve(A, b) (general complex)."""
    rng = np.random.default_rng(7)
    for n in (2, 4, 6):
        A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
        # vector RHS
        b = rng.standard_normal(n) + 1j * rng.standard_normal(n)
        np.testing.assert_allclose(
            _dense_solve_complex(A, b), np.linalg.solve(A, b), atol=1e-9
        )
        # matrix RHS
        B = rng.standard_normal((n, 3)) + 1j * rng.standard_normal((n, 3))
        np.testing.assert_allclose(
            _dense_solve_complex(A, B), np.linalg.solve(A, B), atol=1e-9
        )


def test_construct_eta_still_pseudo_hermitian():
    """The routed η construction still produces a valid η-metric (O†η = ηO)."""
    from srmech.qm.pseudo_hermitian import (
        construct_eta_from_eigendecomposition,
        is_pseudo_hermitian,
    )

    # A real-spectrum non-Hermitian operator (PT-symmetric-style 2×2).
    O = np.array([[2.0, 1.0], [0.0, 3.0]], dtype=np.complex128)
    eta = construct_eta_from_eigendecomposition(O)
    # η Hermitian
    np.testing.assert_allclose(eta, eta.conj().T, atol=1e-9)
    # O is η-pseudo-Hermitian: O† η = η O
    assert is_pseudo_hermitian(O, eta, atol=1e-9)


def test_no_residual_np_linalg_inv_in_pseudo_hermitian():
    """No `np.linalg.inv(` survives in pseudo_hermitian; the route is in place."""
    import srmech

    src = (
        pathlib.Path(srmech.__file__).parent / "qm" / "pseudo_hermitian.py"
    ).read_text(encoding="utf-8")
    assert not re.search(r"\b(?:np|numpy)\.linalg\.inv\s*\(", src)
    assert "_dense_solve_complex(" in src
