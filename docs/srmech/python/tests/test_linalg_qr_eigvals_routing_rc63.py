"""rc63a — np.linalg.qr / np.linalg.eigvals → matrix_cascades cascades.

The first np.linalg.* sub-rc of the numpy-removal sweep. The substrate-native
matrix-decomposition cascades (shipped rc38/rc39 in
``srmech.amsc.cascade.matrix_cascades``) match the canonical decompositions
value-for-value: ``qr`` to round-off up to per-column SIGN, ``eigvals`` as a
MULTISET. rc63a routes the genuine callsites whose downstream consumption is
invariant to exactly those ambiguities:

* the 5 ``q, _ = qr(X)`` callsites in ``qm/so8.py`` use ``q`` only through
  ``q @ qᵀ`` projectors / its column span / a sum-of-squares leak — all
  invariant to QR's per-column sign;
* the 2 ``eigvals(X)`` callsites (``qm/pseudo_hermitian`` ``max|imag|``,
  ``signal_processing/.../esprit`` rotation set) consume the eigenvalue
  multiset, order-free.

numpy-FREE (#564): numpy is GONE from srmech, so this test runs with numpy NOT
installed. The cascade-faithfulness oracles are INVARIANTS, not a numpy peer:

* QR — reconstruction ``Q·R ≈ A`` + orthonormality ``Qᵀ·Q ≈ I`` + ``R``
  upper-triangular, all via plain-list matmul (these are exactly the
  properties the ``q @ qᵀ`` projector / column-span consumers rely on);
* eigvals — each returned eigenvalue is a ROOT of the cascade ``char_poly``
  (an order-free, numpy-free spectral oracle) and the count matches n.

Inputs are stdlib ``random.Random`` nested lists, never ndarrays.
"""

from __future__ import annotations

import math
import random
import re
import pathlib

import pytest

from srmech.amsc.cascade import matrix_cascades as mc


# ---------------------------------------------------------------------------
# plain-list helpers (numpy-free)
# ---------------------------------------------------------------------------

def _matmul(a, b):
    n, k, m = len(a), len(b), len(b[0])
    return [
        [sum(a[i][p] * b[p][j] for p in range(k)) for j in range(m)]
        for i in range(n)
    ]


def _transpose(a):
    return [[a[i][j] for i in range(len(a))] for j in range(len(a[0]))]


def _eval_poly(coeffs, x):
    """Horner evaluation; coeffs are highest-degree-first (char_poly order)."""
    acc = 0
    for c in coeffs:
        acc = acc * x + c
    return acc


def _rand_real(shape, rng):
    n, m = shape
    return [[rng.gauss(0.0, 1.0) for _ in range(m)] for _ in range(n)]


# ---------------------------------------------------------------------------
# 1. the cascade value-faithfulness the routes rely on (invariant oracles)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("shape", [(28, 14), (28, 6), (6, 6), (28, 1), (10, 4)])
def test_qr_reconstructs_and_is_orthonormal(shape):
    """``qr`` satisfies the invariants the so8.py ``q @ qᵀ`` consumers rely on:
    reconstruction Q·R = A, orthonormal columns Qᵀ·Q = I, and upper-triangular R
    — all checked via plain-list matmul (numpy-free; no np.linalg.qr oracle)."""
    n, ncol = shape
    rng = random.Random(sum(shape))
    a = _rand_real(shape, rng)
    q, r = mc.qr(a)
    k = len(q[0])  # reduced-mode column count = min(n, ncol)
    assert len(q) == n
    assert k == min(n, ncol)

    # reconstruction: Q·R == A
    recon = _matmul(q, r)
    for i in range(n):
        for j in range(ncol):
            assert abs(recon[i][j] - a[i][j]) < 1e-9

    # orthonormal columns: Qᵀ·Q == I_k
    gram = _matmul(_transpose(q), q)
    for i in range(k):
        for j in range(k):
            want = 1.0 if i == j else 0.0
            assert abs(gram[i][j] - want) < 1e-9

    # R upper-triangular (the entries below the diagonal vanish).
    for i in range(len(r)):
        for j in range(min(i, len(r[0]))):
            assert abs(r[i][j]) < 1e-9


@pytest.mark.parametrize("n", [3, 4, 5, 6, 8])
def test_eigvals_are_charpoly_roots(n):
    """Every cascade eigenvalue is a ROOT of the cascade ``char_poly`` (an
    order-free, numpy-free spectral oracle) and the count is n — the multiset
    faithfulness the order-free consumers rely on (no np.linalg.eigvals oracle)."""
    rng = random.Random(50 + n)
    m = [
        [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]
        for _ in range(n)
    ]
    ev = mc.eigvals(m)
    cp = mc.char_poly(m)
    assert len(ev) == n
    assert len(cp) == n + 1  # degree-n monic polynomial
    for e in ev:
        # |p(eigenvalue)| ≈ 0 — the eigenvalue annihilates the char-poly.
        assert abs(_eval_poly(cp, e)) < 1e-7


def test_eigvals_max_imag_is_consistent():
    """pseudo_hermitian's real-spectrum test reduces to max|imag(eigvals)|,
    which is order-free. For a REAL matrix the eigenvalues come in conjugate
    pairs, so the cascade max|imag| is itself an eigenvalue's imaginary part —
    verified by char-poly membership (numpy-free; no np.linalg.eigvals oracle)."""
    rng = random.Random(3)
    o = _rand_real((6, 6), rng)
    ev = mc.eigvals(o)
    cp = mc.char_poly(o)
    # every eigenvalue is a char-poly root (the spectral oracle)
    for e in ev:
        assert abs(_eval_poly(cp, e)) < 1e-6
    im_mc = max(abs(e.imag) for e in ev)
    # the max|imag| is the imaginary part of an actual root, hence finite + real.
    assert math.isfinite(im_mc)
    # a real matrix has a conjugate-symmetric spectrum: +im and −im both appear.
    ims = sorted(e.imag for e in ev)
    assert abs(ims[0] + ims[-1]) < 1e-6


# (op-level end-to-end correctness of the routed so8 / esprit / pseudo_hermitian
# functions is covered by their existing suites.)


# ---------------------------------------------------------------------------
# 2. no residual np.linalg.qr / np.linalg.eigvals callsites in routed modules
# ---------------------------------------------------------------------------

# NOTE (rc98/rc123/rc124, carrier-removal #564): esprit / qm.so8 /
# qm.pseudo_hermitian ALL GRADUATED to fully numpy-FREE (no top-level
# ``import numpy`` at all) — a strictly stronger guarantee than the rc63
# "cascade-routed" check. With every formerly-routed module now numpy-absent,
# this dict is empty: the residual-callsite guard is satisfied vacuously, and
# the per-module numpy-free guarantee is enforced by the carrier ratchet + the
# per-op numpy-free-reachable tests instead.
_ROUTED: dict = {}


def test_routed_modules_have_no_residual_callsites():
    import srmech

    pkg = pathlib.Path(srmech.__file__).parent
    for rel, pat in _ROUTED.items():
        txt = (pkg / rel).read_text(encoding="utf-8")
        assert not re.search(pat, txt), f"{rel} still has a routed np.linalg callsite"
        assert "matrix_cascades as _mc" in txt, f"{rel} missing the cascade import"
