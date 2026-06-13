"""Carrier-contract smoke (#564 / rc130): the numpy-idiom surface of the
``Mat`` / ``Vec`` carriers — exercised on hand-built carriers AND on the actual
returns of carrier-returning registered ops — numpy-FREE.

**Why this file exists.** The registry-walk smoke (``test_registry_smoke_rc127``)
walks the full tool registry and asserts every tool *name resolves* to a callable
and every catalog class *describes*. That is a NAME-resolution + introspection
net: it never *calls* an op, and it never touches a returned ``Mat`` / ``Vec``.
So a carrier-method gap is structurally invisible to it — which is exactly how
the rc129→rc130 gaps slipped through: ``m[0]`` (single-index row) raised
``"Mat index must be (i, j)"`` and ``@`` matmul was unsupported on the carriers,
yet every tool still *resolved* and every class still *described*, so the smoke
stayed green. (See the rc130 CHANGELOG.)

This file closes that gap: it CALLS representative carrier-returning ops and
asserts that what they return is a real ``Mat`` / ``Vec`` exposing the full
documented numpy-idiom surface — ``.shape``, ``len()``, iteration, ``m[i, j]``,
``m[0]`` (→ ``Vec`` row), ``.T`` / ``.transpose()``, ``.conj()``, ``.tolist()``,
``.tobytes()``, value-``==``, and ``@`` (matmul / matvec / dot). A future op that
returns a bare ``list`` (the rc127 regression), or a carrier that drops an
idiom, fails HERE — loudly — instead of surfacing downstream as a user report.

Like the registry smoke, this module imports only ``srmech`` + stdlib, so the
whole carrier surface is certified reachable with numpy genuinely absent.
"""

import builtins

from srmech.amsc import laplacian as L
from srmech.amsc.mat import Mat
from srmech.amsc.vec import Vec


# ── the documented carrier-idiom contracts ────────────────────────────────────
def _assert_mat_idioms(m, *, expect_shape=None):
    """Assert ``m`` is a :class:`Mat` exposing the full numpy-idiom surface."""
    assert isinstance(m, Mat), f"expected Mat, got {type(m).__name__}"
    nr, nc = m.shape
    assert len(m.shape) == 2
    if expect_shape is not None:
        assert m.shape == expect_shape, (m.shape, expect_shape)
    assert len(m) == nr  # 2-D len == row count (numpy idiom)

    # 2-D scalar index m[i, j] → a PLAIN scalar (never a carrier / numpy scalar)
    if nr and nc:
        assert isinstance(m[0, 0], (int, float, complex))

    # single-index row m[0] → a Vec (the rc130 fix — NOT a bare list, NOT a raise)
    if nr:
        row0 = m[0]
        assert isinstance(row0, Vec), f"m[0] must be a Vec, got {type(row0).__name__}"
        assert row0.shape == (nc,)
        assert row0.tolist() == m.row(0)
        # negative single-index works too
        assert m[-1].tolist() == m.row(nr - 1)

    # iteration yields ROWS (as stdlib lists, numpy-free)
    rows = list(m)
    assert len(rows) == nr
    assert all(isinstance(r, list) for r in rows)

    # transpose (both spellings), conj, tolist, tobytes, value-equality
    assert m.T.shape == (nc, nr)
    assert m.transpose().shape == (nc, nr)
    assert isinstance(m.conj(), Mat)
    assert m.tolist() == [m.row(i) for i in range(nr)]
    assert isinstance(m.tobytes(), bytes)
    assert m == Mat.from_rows(m.tolist(), is_complex=m.is_complex)


def _assert_vec_idioms(v, *, expect_len=None):
    """Assert ``v`` is a :class:`Vec` exposing the full numpy-idiom surface."""
    assert isinstance(v, Vec), f"expected Vec, got {type(v).__name__}"
    (n,) = v.shape  # 1-D shape is a 1-tuple
    if expect_len is not None:
        assert n == expect_len, (n, expect_len)
    assert len(v) == n

    if n:
        assert isinstance(v[0], (int, float, complex))   # scalar index
        assert v[-1] == v.tolist()[-1]                   # negative index
    # iteration yields SCALARS (not rows)
    items = list(v)
    assert len(items) == n
    assert all(isinstance(x, (int, float, complex)) for x in items)

    assert isinstance(v.conj(), Vec)
    assert v.tolist() == list(v)
    assert isinstance(v.tobytes(), bytes)
    assert v == Vec.from_sequence(v.tolist(), is_complex=v.is_complex)


# ── hand-built carriers: the full idiom surface, incl. the rc130 gaps ─────────
def test_mat_numpy_idiom_surface():
    """A hand-built ``Mat`` exposes ``.shape`` / ``m[i, j]`` / ``m[0]`` → Vec /
    ``@`` — real and complex. The two rc130 gaps (``m[0]`` raised, ``@``
    unsupported) are asserted FIXED here."""
    A = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    _assert_mat_idioms(A, expect_shape=(2, 2))

    B = Mat.from_rows([[5.0, 6.0], [7.0, 8.0]])
    # Mat @ Mat → Mat (the rc130 @ fix)
    C = A @ B
    assert isinstance(C, Mat)
    assert C.tolist() == [[19.0, 22.0], [43.0, 50.0]]

    # Mat @ Vec → Vec
    v = Vec.from_sequence([1.0, 2.0])
    mv = A @ v
    assert isinstance(mv, Vec)
    assert mv.tolist() == [5.0, 11.0]

    # complex carrier: m[0] preserves the complex layout; @ stays complex
    Ac = Mat.from_rows([[1j, 2.0], [3.0, 4j]], is_complex=True)
    _assert_mat_idioms(Ac, expect_shape=(2, 2))
    assert Ac[0].is_complex
    vc = Vec.from_sequence([1j, 1.0], is_complex=True)
    out = Ac @ vc
    assert isinstance(out, Vec) and out.is_complex
    assert out.tolist() == [1 + 0j, 7j]


def test_vec_numpy_idiom_surface():
    """A hand-built ``Vec`` exposes ``.shape`` / scalar ``v[i]`` / scalar
    iteration / ``@`` — ``Vec @ Vec`` → scalar dot, ``Vec @ Mat`` → Vec."""
    v = Vec.from_sequence([1.0, 2.0, 3.0])
    _assert_vec_idioms(v, expect_len=3)

    # Vec @ Vec → a PLAIN scalar inner product (the rc130 @ fix)
    d = v @ Vec.from_sequence([4.0, 5.0, 6.0])
    assert isinstance(d, float)
    assert d == 1 * 4 + 2 * 5 + 3 * 6  # 32

    # Vec @ Mat → Vec (row-vector · matrix)
    M = Mat.from_rows([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    vm = v @ M  # [1,2,3] @ 3x2 = [1+6+15, 2+8+18] = [22, 28]
    assert isinstance(vm, Vec)
    assert vm.tolist() == [22.0, 28.0]


# ── the load-bearing addition: REAL op returns expose the idiom surface ───────
def test_carrier_returning_ops_expose_numpy_idioms_numpy_free():
    """CALL representative carrier-returning registered ops and assert their
    RETURNS expose the documented numpy-idiom surface — the check the registry
    walk cannot do (it never invokes an op). A path-graph ``0-1-2-3``."""
    n = 4
    edges = [(0, 1), (1, 2), (2, 3)]

    # Class-L matrix builders → Mat
    Lap = L.dense_laplacian(n, edges)
    _assert_mat_idioms(Lap, expect_shape=(n, n))
    Adj = L.dense_adjacency(n, edges)
    _assert_mat_idioms(Adj, expect_shape=(n, n))

    # eigenvalues / Fiedler vector → Vec
    eigs = L.jacobi_eigvals(Lap)
    _assert_vec_idioms(eigs, expect_len=n)
    fied = L.fiedler_vector(Lap)
    _assert_vec_idioms(fied, expect_len=n)

    # dense contraction ops → Mat / Vec / scalar
    A = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    B = Mat.from_rows([[5.0, 6.0], [7.0, 8.0]])
    _assert_mat_idioms(L.dense_matmul_real(A, B), expect_shape=(2, 2))
    _assert_vec_idioms(
        L.dense_matvec_real(A, Vec.from_sequence([1.0, 1.0])), expect_len=2
    )
    _assert_mat_idioms(
        L.dense_outer_real([1.0, 2.0, 3.0], [4.0, 5.0]), expect_shape=(3, 2)
    )
    assert isinstance(L.dense_dot_real([1.0, 2.0], [3.0, 4.0]), float)

    # and the carrier returns CHAIN through the @ idiom (op-return @ op-return)
    chained = L.dense_laplacian(n, edges) @ L.fiedler_vector(Lap)
    _assert_vec_idioms(chained, expect_len=n)


def test_carrier_contract_is_itself_numpy_free():
    """The carrier idiom surface needs NO numpy: re-exercise it with numpy hard-
    blocked at import (this module is part of the numpy-FREE surface it certifies,
    #564). Mirrors ``test_registry_smoke_rc127``'s numpy-block pattern."""
    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "numpy" or name.startswith("numpy."):
            raise ImportError("numpy is removed (#564 numpy-zero gate)")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = _blocked
    try:
        A = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
        _assert_mat_idioms(A, expect_shape=(2, 2))
        assert isinstance(A[0], Vec)                 # m[0] → Vec, numpy-absent
        assert isinstance(A @ A, Mat)                # @ matmul, numpy-absent
        v = Vec.from_sequence([1.0, 2.0])
        _assert_vec_idioms(v, expect_len=2)
        assert isinstance(v @ v, float)              # Vec@Vec dot, numpy-absent
        Lap = L.dense_laplacian(3, [(0, 1), (1, 2)])
        _assert_mat_idioms(Lap, expect_shape=(3, 3))
    finally:
        builtins.__import__ = real_import
