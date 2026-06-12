"""rc63a — np.linalg.qr / np.linalg.eigvals → matrix_cascades cascades.

The first np.linalg.* sub-rc of the numpy-removal sweep. The substrate-native
matrix-decomposition cascades (shipped rc38/rc39 in
``srmech.amsc.cascade.matrix_cascades``) already match NumPy value-for-value:
``qr`` to round-off up to per-column SIGN, ``eigvals`` to ~1e-12 as a
MULTISET. rc63a routes the genuine callsites whose downstream consumption is
invariant to exactly those ambiguities:

* the 5 ``q, _ = np.linalg.qr(X)`` callsites in ``qm/so8.py`` use ``q`` only
  through ``q @ q.T`` projectors / its column span / a sum-of-squares leak —
  all invariant to QR's per-column sign;
* the 2 ``np.linalg.eigvals(X)`` callsites (``qm/pseudo_hermitian`` ``max|imag|``,
  ``signal_processing/.../esprit`` rotation set) consume the eigenvalue
  multiset, order-free.

This pins the two value-faithfulness properties the routes rely on, plus that
the routed modules carry no residual ``np.linalg.qr`` / ``np.linalg.eigvals``
callsites.
"""

from __future__ import annotations

import re
import pathlib

import numpy as np
import pytest

from srmech.amsc.cascade import matrix_cascades as mc


# ---------------------------------------------------------------------------
# 1. the cascade value-faithfulness the routes rely on
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("shape", [(28, 14), (28, 6), (6, 6), (28, 1), (10, 4)])
def test_qr_projector_matches_numpy_sign_invariant(shape):
    """q @ q.T (the only way so8.py consumes Q) is QR-sign-invariant and
    matches NumPy to round-off."""
    rng = np.random.default_rng(sum(shape))
    a = rng.standard_normal(shape)
    q_np, _ = np.linalg.qr(a)
    q_mc, _ = mc.qr(a)
    q_mc = np.asarray(q_mc)
    assert q_mc.shape == q_np.shape
    np.testing.assert_allclose(q_mc @ q_mc.T, q_np @ q_np.T, atol=1e-9)


@pytest.mark.parametrize("n", [3, 4, 5, 6, 8])
def test_eigvals_multiset_matches_numpy(n):
    rng = np.random.default_rng(50 + n)
    m = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    e_np = np.sort_complex(np.linalg.eigvals(m))
    e_mc = np.sort_complex(np.asarray(mc.eigvals(m)))
    np.testing.assert_allclose(e_np, e_mc, atol=1e-7)


def test_eigvals_max_imag_matches_numpy():
    """pseudo_hermitian's real-spectrum test reduces to max|imag(eigvals)|,
    which is order-free."""
    rng = np.random.default_rng(3)
    o = rng.standard_normal((6, 6))
    im_np = float(np.max(np.abs(np.linalg.eigvals(o).imag)))
    im_mc = float(np.max(np.abs(np.asarray(mc.eigvals(o)).imag)))
    assert abs(im_np - im_mc) < 1e-7


# (op-level end-to-end correctness of the routed so8 / esprit / pseudo_hermitian
# functions is covered by their existing suites — 83 tests pass post-route.)


# ---------------------------------------------------------------------------
# 2. no residual np.linalg.qr / np.linalg.eigvals callsites in routed modules
# ---------------------------------------------------------------------------

# NOTE (rc98, carrier-removal #564): esprit GRADUATED off the matrix_cascades
# (_mc) cascade route onto the NATIVE Mat-carrier foundation — it now routes
# through mat_hermitian_eigendecompose / mat_lstsq / mat_eigvals and is numpy-FREE
# (no top-level ``import numpy`` at all), a strictly stronger guarantee than the
# rc63 "cascade-routed" check below. So esprit is no longer in this dict.
# NOTE (rc123, carrier-removal #564): qm/so8.py likewise GRADUATED to fully
# numpy-FREE — its QR projectors are the numpy-free Gram-Schmidt
# (so8._orthonormalise), its rank counts the EXACT RREF / float Gram-Schmidt
# rank, and its nullspace/SVD geometry the numpy-free `mat_svd`; so8 no longer
# imports `matrix_cascades as _mc` at all (the strictly-stronger numpy-absent
# guarantee). So so8 is no longer in this dict.
# NOTE (rc124, carrier-removal #564): qm/pseudo_hermitian.py was the LAST entry
# and likewise GRADUATED to fully numpy-FREE — its general non-Hermitian eig (for
# the η = (V V†)⁻¹ construction) now routes through the Mat-carrier `mat_eigvals`
# + a deterministic Gaussian-elimination null-vector eigenvector cascade, and it
# no longer imports `matrix_cascades as _mc`. With every formerly-routed module
# now numpy-absent, this dict is empty — the residual-callsite guard is satisfied
# vacuously, and the per-module numpy-free guarantee is enforced by the carrier
# ratchet + the per-op numpy-free-reachable tests instead.
_ROUTED: dict = {}


def test_routed_modules_have_no_residual_callsites():
    import srmech

    pkg = pathlib.Path(srmech.__file__).parent
    for rel, pat in _ROUTED.items():
        txt = (pkg / rel).read_text(encoding="utf-8")
        assert not re.search(pat, txt), f"{rel} still has a routed np.linalg callsite"
        assert "matrix_cascades as _mc" in txt, f"{rel} missing the cascade import"
