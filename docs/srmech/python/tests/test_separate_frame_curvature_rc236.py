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

**rc463 (`#T1188`) — the tests follow the carrier, they do not shim it.** The
op now returns the exact-ℚ :class:`~srmech.math.qmat.QMat` for exact operands,
and ``QMat`` spells its read-out ``to_lists()`` (exact ``Q`` entries) rather than
``Mat.tolist()`` (float64), and has no ``.buffer`` because it is not a dense
float buffer. Every exact-operand assertion below is therefore rewritten onto
the ``QMat`` surface. No ``tolist`` alias, no ``Mat`` fallback and no compat
shim was added to ``QMat`` to keep the old spelling working — the carrier
changed and the callers follow it.

The float rung is still exercised, on the operands that genuinely belong to it
(complex / Gaussian-integer entries), and those tests keep the ``Mat`` API.

⚠️ **``is_flat`` did not merely LOSE PRECISION through rc462 — it FLIPPED.**
:func:`test_the_flatness_flag_flipped_not_merely_truncated` is the witness: a
non-commuting integer pair whose float64 products collide entry-for-entry, so
the float route computes an identically-zero curvature and publishes
``is_flat True`` for genuinely non-commuting operators. A test that only
compared curvature VALUES could not have seen it — the float curvature is not
imprecise here, it is EXACTLY the zero matrix, and the published boolean
follows correctly from it. The flag is what inverted, so the flag needs its
own witness.
"""
from __future__ import annotations

from srmech.cascade.matrix_cascades import separate_frame_curvature
from srmech.math.mat import Mat
from srmech.math.q import Q
from srmech.math.qmat import QMat


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
    # both operands are exact ints -> the exact-ℚ rung (rc463).
    assert isinstance(res["curvature"], QMat)
    # ½(σxσz − σzσx) = ½·[[0,-2],[2,0]] = [[0,-1],[1,0]]
    assert res["curvature"].to_lists() == [[Q(0, 1), Q(-1, 1)],
                                           [Q(1, 1), Q(0, 1)]]
    # ½(σxσz + σzσx) = ½·[[0,0],[0,0]] = 0  (σx, σz anticommute → zero metric part)
    assert res["fixed_frame"].to_lists() == [[Q(0, 1), Q(0, 1)],
                                             [Q(0, 1), Q(0, 1)]]


def test_reconstruction_is_byte_exact_pauli():
    """fixed_frame + curvature == σx·σz exactly (representable-regime theorem)."""
    res = separate_frame_curvature(SX, SZ)
    recon = res["fixed_frame"] + res["curvature"]
    assert recon.to_lists() == [[Q(x, 1) for x in row]
                                for row in _matmul(SX, SZ)]


def test_commuting_diagonal_curvature_exactly_zero_is_flat_true():
    """σz commutes with a diagonal D → curvature is EXACTLY the zero carrier."""
    D = [[2, 0], [0, 3]]
    res = separate_frame_curvature(SZ, D)
    assert res["is_flat"] is True
    # curvature is literally the zero QMat (exact vanishing, both directions).
    # ``.buffer`` was the float64 dense-carrier read-out and QMat has none: the
    # exact peer of "every stored value is 0.0" is "every entry IS Q(0, 1)".
    assert res["curvature"] == QMat.zeros(2, 2)
    assert all(q == Q(0, 1) for row in res["curvature"].to_lists() for q in row)
    # fixed_frame == the product itself (metric part == A·B when they commute)
    assert res["fixed_frame"].to_lists() == [[Q(x, 1) for x in row]
                                             for row in _matmul(SZ, D)]


def test_commuting_shared_eigenbasis_integer_is_flat_true():
    """Two symmetric integer matrices sharing an eigenbasis commute → flat."""
    A = [[2, 1], [1, 2]]
    B = [[3, 1], [1, 3]]
    res = separate_frame_curvature(A, B)
    assert res["is_flat"] is True
    assert res["curvature"] == QMat.zeros(2, 2)
    # reconstruction: fixed_frame == A·B == B·A
    assert res["fixed_frame"].to_lists() == [[Q(x, 1) for x in row]
                                             for row in _matmul(A, B)]


def test_noncommuting_integer_reconstruct_and_flag():
    """Two non-commuting integer shears: nonzero half-integer curvature + exact
    reconstruction to the (integer) product."""
    A = [[1, 1], [0, 1]]
    B = [[1, 0], [1, 1]]
    res = separate_frame_curvature(A, B)
    assert res["is_flat"] is False
    # ½[A,B] = ½·[[1,0],[0,-1]] — exact HALVES on the ℚ carrier, not float64
    # dyadic approximations of them.
    assert res["curvature"].to_lists() == [[Q(1, 2), Q(0, 1)],
                                           [Q(0, 1), Q(-1, 2)]]
    recon = res["fixed_frame"] + res["curvature"]
    assert recon.to_lists() == [[Q(x, 1) for x in row] for row in _matmul(A, B)]


def test_self_pairing_is_flat_and_anticommutator_is_square():
    """{σx, σx} = 2 σx² = 2·I → fixed_frame = σx² = I; [σx,σx]=0 → is_flat True."""
    res = separate_frame_curvature(SX, SX)
    assert res["is_flat"] is True
    assert res["fixed_frame"].to_lists() == [[Q(1, 1), Q(0, 1)],
                                             [Q(0, 1), Q(1, 1)]]
    # σx is exact → the curvature is the exact-ℚ zero carrier
    assert res["curvature"] == QMat.zeros(2, 2)


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
    assert res["curvature"] == QMat.zeros(3, 3)


# ── the FLIP, which is the defect rc463 actually repaired ─────────────────
#: A = diag(2⁵³, 2⁵³+1) and B = σx do NOT commute: [A, B] = [[0, −1], [1, 0]], so
#: the true curvature is [[0, −½], [½, 0]] and the true ``is_flat`` is False. But
#: every entry of A·B and of B·A is either 2⁵³ or 2⁵³+1, and float64 rounds 2⁵³+1
#: to 2⁵³ — so on the float carrier the two products are IDENTICAL, the computed
#: curvature is the exact zero matrix, and ``is_flat`` comes back True.
FLIP_A = [[2 ** 53, 0], [0, 2 ** 53 + 1]]
FLIP_B = [[0, 1], [1, 0]]


def test_the_flatness_flag_flipped_not_merely_truncated():
    """rc462 published ``is_flat True`` for a genuinely NON-COMMUTING pair.

    This is the witness the rc236 suite lacked. Every other test in this file
    compares curvature VALUES, and a value comparison cannot see this defect:
    the float route does not return an *imprecise* curvature, it returns the
    EXACT ZERO MATRIX, from which the published boolean follows correctly. The
    flag is what inverted, so the flag needs its own witness.
    """
    res = separate_frame_curvature(FLIP_A, FLIP_B)
    assert isinstance(res["curvature"], QMat)
    assert res["curvature"].to_lists() == [[Q(0, 1), Q(-1, 2)],
                                           [Q(1, 2), Q(0, 1)]]
    assert res["is_flat"] is False, (
        "is_flat is True for a pair whose commutator is [[0,-1],[1,0]] — the "
        "rc462 FLIP has returned. The exact rung is the fix; a wider tolerance "
        "is not, because the float carrier's curvature here is EXACTLY zero.")


def test_the_flip_is_a_property_of_the_float_carrier_not_of_the_operators():
    """The same operators, entered as floats, still report flat — and must.

    Handing the op float entries is ELECTING the continuous carrier, where
    ``is_flat`` is a statement about the COMPUTED curvature (which really is
    zero here) rather than about the true commutator. Pinning that keeps the
    two rungs honestly separated: rc463 did not make the float route right, it
    made the exact question ASKABLE. It is also the negative control for the
    test above — without it, a build in which the exact rung silently stopped
    being selected would still look fixed.
    """
    a_f = [[float(x) for x in row] for row in FLIP_A]
    b_f = [[float(x) for x in row] for row in FLIP_B]
    res = separate_frame_curvature(a_f, b_f)
    assert isinstance(res["curvature"], Mat)
    assert res["curvature"].tolist() == [[0.0, 0.0], [0.0, 0.0]]
    assert res["is_flat"] is True
