"""Carriers-C parity ratchet (rc141; Foundation F0 — the LAST C:Python
parity-backfill foundation).

Proves the C Mat/Vec carrier struct API (``srmech_mat_*`` / ``srmech_vec_*``)
is BYTE-IDENTICAL to the pure-Python ``Mat`` / ``Vec`` carrier for get/set +
elementwise (add/sub/mul/scale/conj/transpose), that the C carrier feeds the
existing compute kernel (``srmech_dense_matmul_complex``) ZERO-COPY and matches
the pure ``mat_matmul``, and that a bare C host's sizing helper
(``srmech_mat_buf_len``) agrees with the Python carrier's ``array('d')`` length.

This test is itself NUMPY-FREE (the module under test is numpy-free — a test
for a numpy-free module must itself import no numpy). The C-specific parity
checks skip cleanly on a no-C host (the pure-Python carrier is the complete
alternative + the byte-exact oracle there).

Also confirms the audit's two "≈ 0 work" claims:
  * ``Complex128`` IS C99 ``double _Complex`` (two float64, interleaved (re,im))
    — no rebuild needed;
  * ``HV`` ops already have C peers (``srmech_hdc`` / ``srmech_klein4``).
"""
from __future__ import annotations

import operator
import sys
from array import array

import pytest

from srmech.amsc import _native
from srmech.amsc.complex128 import Complex128
from srmech.amsc.mat import Mat
from srmech.amsc.vec import Vec

_NATIVE = _native.has_native_carriers()
requires_native = pytest.mark.skipif(
    not _NATIVE, reason="rc141 carrier C API not loaded (no-C host — the pure "
    "Python Mat/Vec carrier is the complete alternative)")


# ── independent Python-arithmetic oracles (NOT the carrier methods) ──────────
def _oracle_binary(a_rows, b_rows, op):
    return [[op(a_rows[i][j], b_rows[i][j]) for j in range(len(a_rows[0]))]
            for i in range(len(a_rows))]


_A_C = [[1 + 2j, 3 + 0j, -1 - 1j], [0 + 1j, 2 - 1j, 4 + 4j]]
_B_C = [[1 + 0j, 2 + 2j, 5 - 5j], [3 - 1j, 0 + 4j, -2 + 0j]]
_A_R = [[1.0, 2.0, 3.0], [4.0, -5.0, 6.0]]
_B_R = [[10.0, -20.0, 30.0], [0.5, 5.0, -6.0]]


# ── the audit's two ≈0-work confirmations ────────────────────────────────────
def test_complex128_is_double_complex():
    """Complex128 IS two float64 (re, im) = C99 double _Complex, the SAME
    interleaved layout the Mat/Vec carriers + the native kernels speak — so it
    needs ≈ 0 carrier-C work (confirm + skip, do NOT rebuild)."""
    z = Complex128(1.5, -2.25)
    assert z.as_pair() == (1.5, -2.25)
    assert isinstance(z.real, float) and isinstance(z.imag, float)
    assert complex(z) == complex(1.5, -2.25)
    assert z.conjugate().as_pair() == (1.5, 2.25)  # Class-K sign flip on imag
    # A 1-element complex Vec's interleaved buffer IS (re, im) — the same two
    # float64 Complex128 holds, i.e. the carrier + scalar layouts agree.
    v = Vec.from_sequence([1.5 - 2.25j])
    assert list(v.buffer) == [1.5, -2.25]


def test_hv_ops_already_have_c_peer():
    """HV (the 1-D hypervector carrier) already has its compute ops in C
    (srmech_hdc / srmech_klein4) — confirm + skip (no rebuild)."""
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        pytest.skip("no-C host")
    assert hasattr(_native.LIB, "srmech_hdc_bind")
    assert _native.has_native_klein4_bind()


# ── dispatched carrier methods match the independent oracle (any mode) ───────
def test_mat_elementwise_matches_oracle():
    for a_rows, b_rows in ((_A_C, _B_C), (_A_R, _B_R)):
        A = Mat.from_rows(a_rows)
        B = Mat.from_rows(b_rows)
        assert (A + B).tolist() == _oracle_binary(a_rows, b_rows, operator.add)
        assert (A - B).tolist() == _oracle_binary(a_rows, b_rows, operator.sub)
        assert (A * B).tolist() == _oracle_binary(a_rows, b_rows, operator.mul)


def test_mat_scalar_matches_oracle():
    A = Mat.from_rows(_A_C)
    for s in (3, -2.5, 2 + 1j, 0 + 4j):
        assert (A * s).tolist() == [[x * s for x in r] for r in _A_C]
        assert (s * A).tolist() == [[s * x for x in r] for r in _A_C]
        assert (A + s).tolist() == [[x + s for x in r] for r in _A_C]


def test_mat_conj_neg_transpose_match_oracle():
    A = Mat.from_rows(_A_C)
    assert A.conj().tolist() == [[x.conjugate() for x in r] for r in _A_C]
    assert (-A).tolist() == [[-x for x in r] for r in _A_C]
    assert A.T.tolist() == [[_A_C[i][j] for i in range(len(_A_C))]
                            for j in range(len(_A_C[0]))]


def test_vec_ops_match_oracle():
    a = [1 + 1j, 2 - 2j, 3 + 0j, -4 + 5j]
    b = [0 + 1j, 1 + 0j, 2 + 2j, 5 - 5j]
    u, w = Vec.from_sequence(a), Vec.from_sequence(b)
    assert (u + w).tolist() == [a[i] + b[i] for i in range(len(a))]
    assert (u - w).tolist() == [a[i] - b[i] for i in range(len(a))]
    assert (u * w).tolist() == [a[i] * b[i] for i in range(len(a))]
    assert (u * (2 + 1j)).tolist() == [x * (2 + 1j) for x in a]
    assert u.conj().tolist() == [x.conjugate() for x in a]
    assert (-u).tolist() == [-x for x in a]


# ── the C path specifically is BYTE-IDENTICAL to the pure carrier ────────────
@requires_native
def test_c_mat_elementwise_byte_identical():
    for a_rows, b_rows in ((_A_C, _B_C), (_A_R, _B_R)):
        A, B = Mat.from_rows(a_rows), Mat.from_rows(b_rows)
        for kind, op in (("add", operator.add), ("sub", operator.sub),
                         ("mul", operator.mul)):
            out, cplx = _native.mat_binary_c(A.buffer, A.is_complex, B.buffer,
                                             B.is_complex, A.n_rows, A.n_cols,
                                             kind)
            pure = A._elementwise(B, op)  # the pure path (no dispatch)
            assert out.tobytes() == pure.buffer.tobytes(), f"C {kind} bytes"
            assert bool(cplx) == pure.is_complex


@requires_native
def test_c_mat_scalar_and_unary_byte_identical():
    A = Mat.from_rows(_A_C)
    # scale (× (2+1j)) and add_scalar (+ 5)
    out, _ = _native.mat_scalar_c(A.buffer, A.is_complex, A.n_rows, A.n_cols,
                                  2.0, 1.0, "scale")
    pure = A._elementwise(2 + 1j, lambda a, b: a * b)
    assert out.tobytes() == pure.buffer.tobytes()
    out, _ = _native.mat_scalar_c(A.buffer, A.is_complex, A.n_rows, A.n_cols,
                                  5.0, 0.0, "add")
    pure = A._elementwise(5, lambda a, b: a + b)
    assert out.tobytes() == pure.buffer.tobytes()
    # conj / neg / transpose
    for kind, oracle in (
        ("conj", Mat.from_rows([[x.conjugate() for x in r] for r in _A_C],
                               is_complex=True)),
        ("neg", Mat.from_rows([[-x for x in r] for r in _A_C], is_complex=True)),
        ("transpose", Mat.from_rows(
            [[_A_C[i][j] for i in range(len(_A_C))]
             for j in range(len(_A_C[0]))], is_complex=True)),
    ):
        res = _native.mat_unary_c(A.buffer, A.n_rows, A.n_cols, A.is_complex, kind)
        out, orows, ocols = res
        assert out.tobytes() == oracle.buffer.tobytes(), f"C {kind} bytes"
        assert (orows, ocols) == oracle.shape


@requires_native
def test_c_vec_byte_identical():
    a = [1 + 1j, 2 - 2j, 3 + 0j]
    b = [0 + 1j, 1 + 0j, 2 + 2j]
    u, w = Vec.from_sequence(a), Vec.from_sequence(b)
    out, _ = _native.vec_binary_c(u.buffer, u.is_complex, w.buffer,
                                  w.is_complex, len(a), "mul")
    pure = u._elementwise(w, lambda x, y: x * y)
    assert out.tobytes() == pure.buffer.tobytes()
    out = _native.vec_unary_c(u.buffer, len(a), u.is_complex, "conj")
    oracle = Vec.from_sequence([x.conjugate() for x in a], is_complex=True)
    assert out.tobytes() == oracle.buffer.tobytes()


@requires_native
def test_c_ctor_getset_roundtrip_byte_identical():
    """srmech_mat_zeros + srmech_mat_set (build) then read back == the Python
    Mat.from_rows(...) buffer, byte-for-byte — the ctor + get/set a bare C host
    performs, proven layout-identical to the Python carrier."""
    for rows, cplx in ((_A_C, True), (_A_R, False)):
        buf = _native.mat_roundtrip_c(rows, cplx)
        expect = Mat.from_rows(rows, is_complex=cplx)
        assert buf.tobytes() == expect.buffer.tobytes()


@requires_native
def test_mat_buf_len_agrees_with_carrier():
    assert _native.mat_buf_len_c(2, 3, False) == len(Mat.from_rows(_A_R).buffer)
    cplx = Mat.from_rows(_A_C)  # genuinely complex
    assert _native.mat_buf_len_c(2, 3, True) == len(cplx.buffer)
    assert _native.mat_buf_len_c(2, 3, True) == 12
    assert _native.mat_buf_len_c(2, 3, False) == 6


@requires_native
def test_kernel_bridge_matmul_zero_copy():
    """The C carrier buffer feeds srmech_dense_matmul_complex ZERO-COPY (via
    srmech_mat_matmul_c128) and matches the pure Class-L mat_matmul byte-for-
    byte."""
    from srmech.amsc import laplacian as L
    A = Mat.from_rows([[1 + 2j, 3 + 0j], [0 + 1j, 2 - 1j]])
    B = Mat.from_rows([[1 + 0j, 2 + 2j], [3 - 1j, 0 + 4j]])
    out = _native.mat_matmul_c128_c(A.buffer, B.buffer, 2, 2, 2)
    pure = L.mat_matmul(A, B)
    assert out.tobytes() == pure.buffer.tobytes()


# ── the numpy-free identity ──────────────────────────────────────────────────
def test_numpy_not_imported():
    assert "numpy" not in sys.modules


def test_carrier_result_is_a_carrier_not_a_list():
    """Dispatch must PRESERVE the carrier type (never bail to a list)."""
    A = Mat.from_rows(_A_C)
    assert isinstance(A + A, Mat) and isinstance(A.conj(), Mat)
    assert isinstance(A.T, Mat) and isinstance(-A, Mat)
    u = Vec.from_sequence([1 + 1j, 2 + 0j])
    assert isinstance(u + u, Vec) and isinstance(u.conj(), Vec)
    # array('d') buffer preserved (interleaved complex).
    assert isinstance((A + A).buffer, array)
