"""rc236 (#834) — separate_frame_curvature: the connection/curvature decomposition
of a two-operator product into its FIXED-FRAME (metric, ½{A,B}) part ⊕ its
CURVATURE / RESPONSION (holonomy, ½[A,B]) residue, with the EXACT ``is_flat``
vanishing certificate.

The soundness proof runs on the exactly-float-representable (integer / dyadic /
Gaussian-integer) regime — the quantum-operator regime the decomposition is for
(Pauli σ, integer matrices) — where ``mat_matmul`` is bit-exact, so the computed
curvature IS the true ½[A,B]: commuting → curvature EXACTLY the zero carrier +
``is_flat True``; non-commuting → nonzero + ``is_flat False``; and
``fixed_frame + curvature == A·B`` byte-for-byte.
"""
from __future__ import annotations

from srmech.amsc.cascade.matrix_cascades import separate_frame_curvature
from srmech.amsc.mat import Mat


# ── the Pauli operators (Gaussian integers {0, ±1, ±i} — exactly representable) ─
SX = [[0, 1], [1, 0]]
SY = [[0, -1j], [1j, 0]]
SZ = [[1, 0], [0, -1]]
IDENT = [[1, 0], [0, 1]]


def _matmul(a, b):
    """A plain reference product (exact for the integer / Gaussian-integer test
    matrices) to check reconstruction against, independent of the op."""
    n = len(a)
    m = len(b[0])
    k = len(b)
    return [[sum(a[i][p] * b[p][j] for p in range(k)) for j in range(m)]
            for i in range(n)]


def test_noncommuting_pauli_curvature_nonzero_is_flat_false():
    """[σx, σz] ≠ 0 → curvature = ½[σx,σz] = −i σy nonzero + is_flat False."""
    res = separate_frame_curvature(SX, SZ)
    assert res["is_flat"] is False
    # ½(σxσz − σzσx) = ½·[[0,-2],[2,0]] = [[0,-1],[1,0]]
    assert res["curvature"].tolist() == [[0j, -1 + 0j], [1 + 0j, 0j]]
    # ½(σxσz + σzσx) = ½·[[0,0],[0,0]] = 0  (σx, σz anticommute → zero metric part)
    assert res["fixed_frame"].tolist() == [[0j, 0j], [0j, 0j]]


def test_reconstruction_is_byte_exact_pauli():
    """fixed_frame + curvature == σx·σz exactly (representable-regime theorem)."""
    res = separate_frame_curvature(SX, SZ)
    recon = res["fixed_frame"] + res["curvature"]
    assert recon.tolist() == [[complex(x) for x in row] for row in _matmul(SX, SZ)]


def test_commuting_diagonal_curvature_exactly_zero_is_flat_true():
    """σz commutes with a diagonal D → curvature is EXACTLY the zero carrier."""
    D = [[2, 0], [0, 3]]
    res = separate_frame_curvature(SZ, D)
    assert res["is_flat"] is True
    # curvature is literally the zero Mat (byte-exact vanishing, both directions)
    assert res["curvature"] == Mat.from_rows([[0, 0], [0, 0]])
    assert all(x == 0.0 for x in res["curvature"].buffer)
    # fixed_frame == the product itself (metric part == A·B when they commute)
    assert res["fixed_frame"].tolist() == [[complex(x) for x in row]
                                           for row in _matmul(SZ, D)]


def test_commuting_shared_eigenbasis_integer_is_flat_true():
    """Two symmetric integer matrices sharing an eigenbasis commute → flat."""
    A = [[2, 1], [1, 2]]
    B = [[3, 1], [1, 3]]
    res = separate_frame_curvature(A, B)
    assert res["is_flat"] is True
    assert res["curvature"] == Mat.from_rows([[0, 0], [0, 0]])
    # reconstruction: fixed_frame == A·B == B·A
    assert res["fixed_frame"].tolist() == [[float(x) for x in row]
                                           for row in _matmul(A, B)]


def test_noncommuting_integer_reconstruct_and_flag():
    """Two non-commuting integer shears: nonzero half-integer curvature + exact
    reconstruction to the (integer) product."""
    A = [[1, 1], [0, 1]]
    B = [[1, 0], [1, 1]]
    res = separate_frame_curvature(A, B)
    assert res["is_flat"] is False
    # ½[A,B] = ½·[[1,0],[0,-1]] = [[0.5,0],[0,-0.5]]  (exact dyadic half-integers)
    assert res["curvature"].tolist() == [[0.5, 0.0], [0.0, -0.5]]
    recon = res["fixed_frame"] + res["curvature"]
    assert recon.tolist() == [[float(x) for x in row] for row in _matmul(A, B)]


def test_self_pairing_is_flat_and_anticommutator_is_square():
    """{σx, σx} = 2 σx² = 2·I → fixed_frame = σx² = I; [σx,σx]=0 → is_flat True."""
    res = separate_frame_curvature(SX, SX)
    assert res["is_flat"] is True
    assert res["fixed_frame"].tolist() == [[1.0, 0.0], [0.0, 1.0]]
    # σx is real → the curvature is the REAL zero carrier
    assert res["curvature"] == Mat.from_rows([[0, 0], [0, 0]])


def test_complex_entries_pauli_curvature_exact():
    """The genuinely-COMPLEX (Gaussian-integer) path: [σx, σy] = 2i σz →
    curvature = i σz nonzero + is_flat False; and σy commutes with itself → flat.
    Exercises the complex interleaved-(re,im) Mat buffer through the op."""
    res = separate_frame_curvature(SX, SY)
    assert res["is_flat"] is False
    # ½[σx,σy] = ½·[[2i,0],[0,-2i]] = [[i,0],[0,-i]] = i σz (exact Gaussian ints)
    assert res["curvature"].tolist() == [[1j, 0j], [0j, -1j]]
    # σy with itself commutes → the complex zero carrier + is_flat True
    self_res = separate_frame_curvature(SY, SY)
    assert self_res["is_flat"] is True
    assert all(x == 0.0 for x in self_res["curvature"].buffer)


def test_accepts_mat_inputs_directly():
    """A Mat (not just a nested list) is accepted, same result."""
    res_list = separate_frame_curvature(SX, SZ)
    res_mat = separate_frame_curvature(Mat.from_rows(SX), Mat.from_rows(SZ))
    assert res_mat["is_flat"] == res_list["is_flat"]
    assert res_mat["curvature"] == res_list["curvature"]
    assert res_mat["fixed_frame"] == res_list["fixed_frame"]


def test_shape_validation():
    """Non-square or mismatched-shape operands raise ValueError."""
    import pytest
    with pytest.raises(ValueError):
        separate_frame_curvature([[1, 2, 3], [4, 5, 6]], [[1, 2, 3], [4, 5, 6]])
    with pytest.raises(ValueError):
        separate_frame_curvature([[1, 0], [0, 1]], [[1, 0, 0], [0, 1, 0],
                                                    [0, 0, 1]])


def test_larger_integer_commuting_powers_are_flat():
    """A and A² always commute → the responsion of an operator with its own
    square is exactly flat (a 3×3 integer witness)."""
    A = [[0, 1, 0], [0, 0, 1], [1, 0, 0]]        # a cyclic permutation
    A2 = _matmul(A, A)
    res = separate_frame_curvature(A, A2)
    assert res["is_flat"] is True
    assert res["curvature"] == Mat.from_rows([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
