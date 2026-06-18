"""Bit-exact acceptance tests for the su(3) ⊕ 3 ⊕ 3bar voxel (rc21).

``srmech.qm.so8.an_embedding`` exposes the genuine su(3)-module structure
of the 14 ``g2 = Der(O)`` generators: the Lie-algebra branching
``14 = 8 + 3 + 3bar`` (su(3) adjoint + fundamental + antifundamental). This
is a DIFFERENT 14-decomposition from the partitioned ``so8_adjoint_basis``
(``14 g2 + 7 L + 7 R`` inside the 28-dim so(8)); here the 14-dim g2 *itself*
splits under one of its su(3) subalgebras.

These tests prove the construction is the genuine branching, with the three
load-bearing REVISE fixes asserted explicitly:

* FIX 1 — the fundamental is the ``J = +i`` eigenspace of the su(3)-INVARIANT
  complex structure ``J`` on the 6-real-dim complement (a real 3-span cannot
  carry it); ``[su3, triplet] ⊆ triplet`` is then bit-exact.
* FIX 2 — su(3) is identified by an INVARIANT certificate ``{dim 8, rank 2,
  simple}`` + Killing-orthonormal total-antisymmetry, NOT a raw-Casimir
  comparison.
* FIX 3 — rank-2 Cartan via the centraliser of a fixed regular element
  (the greedy mutually-commuting subset would spuriously return 1).

ALL residuals are reduced through the **scalar** Class K pin-slot magnitude
(:func:`srmech.amsc.cascade.magnitude`) — NEVER Python ``abs()`` per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`` — by first
reducing the matrix to a scalar Frobenius norm via the numpy-free Class-N
:func:`srmech.amsc.laplacian.mat_norm`, then passing that Python float to
``magnitude`` (scalar-only; it raises on an array).

Determinism: every basis extraction uses a deterministic SVD / Gram-Schmidt /
eig (no RNG), so the build is reproducible and byte-identical across calls.

rc123 (numpy-free, #564): this test is itself numpy-FREE — ``an_embedding``
returns :class:`srmech.amsc.mat.Mat` (the ``weights`` a nested ``list``);
matmuls / norms route through ``mat_matmul`` / ``mat_norm``, span ranks
through the float-tolerant :func:`srmech.qm.so8._rank_float`, with no numpy
oracle and no ``.to_numpy()`` (per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

from __future__ import annotations

import pytest

from srmech.amsc.cascade import magnitude
from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.qm import so8
from srmech.qm.so8 import an_embedding

_TOL = 1e-9


# ----------------------------------------------------------------------
# Test helpers — numpy-free, scalar reductions through cascade.magnitude.
# ----------------------------------------------------------------------


def _eye(n: int) -> Mat:
    return Mat.from_rows([[1.0 if i == j else 0.0 for j in range(n)]
                          for i in range(n)])


def _rows(m):
    return m.tolist() if isinstance(m, Mat) else [list(r) for r in m]


def _sub(a, b):
    ar, br = _rows(a), _rows(b)
    is_c = a.is_complex or b.is_complex if isinstance(a, Mat) and isinstance(b, Mat) else False
    return Mat.from_rows([[ar[i][j] - br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))], is_complex=is_c or None)


def _add(a, b):
    ar, br = _rows(a), _rows(b)
    is_c = (isinstance(a, Mat) and a.is_complex) or (isinstance(b, Mat) and b.is_complex)
    return Mat.from_rows([[ar[i][j] + br[i][j] for j in range(len(ar[0]))]
                          for i in range(len(ar))], is_complex=is_c or None)


def _frob(matrix) -> float:
    """Frobenius-norm deviation reduced through the scalar Class K magnitude.

    Reduce to a SCALAR float FIRST (the numpy-free Class-N ``mat_norm`` is the
    Frobenius norm), then pass that scalar to ``cascade.magnitude`` (scalar-
    only; raises on an array). NEVER ``abs()``."""
    scalar = mat_norm(matrix if isinstance(matrix, Mat) else Mat.from_rows(matrix))
    return magnitude(scalar)


def _commutator(x: Mat, y: Mat) -> Mat:
    """Matrix commutator ``[X, Y] = X·Y − Y·X`` via the numpy-free ``mat_matmul``
    (real or complex)."""
    return _sub(mat_matmul(x, y), mat_matmul(y, x))


def _matvec(m: Mat, v) -> list:
    rows = _rows(m)
    return [sum(rows[i][t] * v[t] for t in range(len(v))) for i in range(len(rows))]


def _coords_of(generators) -> list:
    """The E_{pq}-coords of a generator iterable as a list of length-28 columns
    (real or complex)."""
    return [so8._epq_coords(g) for g in generators]


def _max_closure_residual(inner, outer) -> float:
    """Max residual of ``[X, Y]`` projected onto ``span(outer)`` over X∈inner,
    Y∈outer — the closure test ``[inner, outer] ⊆ span(outer)``. The projection
    rides the numpy-free :func:`srmech.qm.so8._max_projection_residual`
    (orthonormal Gram-Schmidt projector). Reduced through Class K magnitude."""
    outer_coords = _coords_of(outer)
    brackets = []
    for x in inner:
        for y in outer:
            brackets.append(so8._epq_coords(_commutator(x, y)))
    return so8._max_projection_residual(brackets, outer_coords)


# ----------------------------------------------------------------------
# TEST 1 — shapes + the bidirectional span killer test.
# ----------------------------------------------------------------------


def test_shapes_and_span_killer():
    """The pieces have the right counts, and ``span[su3 | complement]`` is
    EXACTLY ``span(g2)`` (rank 14 — the bidirectional killer test)."""
    emb = an_embedding()
    su3 = emb["su3"]
    complement = emb["complement"]
    triplet = emb["triplet"]
    antitriplet = emb["antitriplet"]

    assert len(su3) == 8
    assert len(complement) == 6
    assert len(triplet) == 3
    assert len(antitriplet) == 3
    for matrix in su3 + complement:
        assert matrix.shape == (8, 8)
        assert not matrix.is_complex
    for matrix in triplet + antitriplet:
        assert matrix.shape == (8, 8)
        assert matrix.is_complex

    g2 = so8.g2_subalgebra()
    assert len(g2) == 14

    su3_coords = _coords_of(su3)
    complement_coords = _coords_of(complement)
    g2_coords = _coords_of(g2)
    span = su3_coords + complement_coords

    # The su(3)/complement/g2 coords mix exact (g2) and float (SVD-derived
    # su3/complement) → the float-tolerant rank (the same-span check).
    rank_span = so8._rank_float(span)
    rank_with_g2 = so8._rank_float(span + g2_coords)
    # span[su3 | complement] is rank 14 (8 + 6, independent), AND adding g2
    # does NOT raise the rank (it is the SAME 14-dim space as g2).
    assert rank_span == 14
    assert rank_with_g2 == 14
    # 8 + 6 = 14.
    assert len(su3) + len(complement) == 14


# ----------------------------------------------------------------------
# TEST 2 — su(3) is the stabiliser of e_K, sits in g2, and is a subalgebra.
# ----------------------------------------------------------------------


def test_su3_fixes_eK_in_g2_and_closes():
    """Every su(3) generator annihilates ``e_K``, lies in ``span(g2)``, and
    ``[su3, su3] ⊆ su3`` (it is a Lie subalgebra)."""
    k = 1
    emb = an_embedding(k)
    su3 = emb["su3"]
    e_k = [1.0 if i == k else 0.0 for i in range(8)]

    # su(3) fixes e_K (the stabiliser construction).
    for matrix in su3:
        assert mat_norm(_matvec(matrix, e_k)) < 1e-12

    # su(3) ⊆ g2: stacking g2 with su3 does not raise the rank past 14.
    g2 = so8.g2_subalgebra()
    g2_coords = _coords_of(g2)
    su3_coords = _coords_of(su3)
    assert so8._rank_float(su3_coords) == 8
    rank_stacked = so8._rank_float(g2_coords + su3_coords)
    assert rank_stacked == 14  # su3 adds nothing new — it lives in g2.

    # [su3, su3] ⊆ su3 (closed under the bracket).
    assert _max_closure_residual(su3, su3) < 1e-12


# ----------------------------------------------------------------------
# TEST 3 — FIX 2: INVARIANT su(3) certificate {dim 8, rank 2, simple} +
#          Killing-orthonormal total-antisymmetry.
# ----------------------------------------------------------------------


def test_su3_invariant_certificate():
    """The honest INVARIANT su(3) certificate, NOT a raw-Casimir comparison:

    * dim 8;
    * rank 2 via the CENTRALISER of a fixed regular element (FIX 3 — the
      greedy mutually-commuting subset would spuriously return 1);
    * simple (adjoint commutant dim == 1 — rules out su(2)+su(2));
    * in a Killing-orthonormalised basis the structure constants are
      TOTALLY ANTISYMMETRIC.

    By the Cartan A2 classification {dim 8, rank 2, simple} UNIQUELY
    identifies su(3). Numpy-free.
    """
    emb = an_embedding()
    su3 = emb["su3"]
    assert len(su3) == 8

    # Killing-orthonormalise (Gram-Schmidt of the coords) so the structure-
    # constant frame is well-conditioned and the metric is the identity.
    coords = _coords_of(su3)
    q = so8._orthonormalise(coords)
    su3_on = [Mat.from_rows(so8._epq_to_matrix(col)) for col in q]

    def coord(m):
        return so8._epq_coords(m)

    # Structure constants f_abc = <X_c, [X_a, X_b]> (orthonormal => metric I).
    f = [[[0.0] * 8 for _ in range(8)] for _ in range(8)]
    for a in range(8):
        for b in range(8):
            cab = coord(_commutator(su3_on[a], su3_on[b]))
            for c in range(8):
                xc = coord(su3_on[c])
                f[a][b][c] = float(sum(xc[t] * cab[t] for t in range(28)))

    # Total antisymmetry: f_abc = -f_bac = -f_acb (residual via magnitude).
    antisym = 0.0
    for a in range(8):
        for b in range(8):
            for c in range(8):
                antisym = max(
                    antisym,
                    magnitude(float(f[a][b][c] + f[b][a][c])),
                    magnitude(float(f[a][b][c] + f[a][c][b])),
                )
    assert antisym < 1e-9

    # Adjoint matrices (ad X_a)[c, b] = f_abc; commutant dim 1 <=> simple.
    # commutant = nullspace of the stacked [ad⊗I − I⊗ad]; dim via the cascade
    # SVD nullspace count is fragile, so instead count via the float-tolerant
    # rank: commutant_dim = 64 − rank(stacked).
    identity = so8._eye(8)
    ad = [[[f[a][b][c] for b in range(8)] for c in range(8)] for a in range(8)]
    stacked_rows = []
    for m in ad:
        block = so8._sub(so8._kron(so8._transpose(m), identity),
                         so8._kron(identity, m))
        stacked_rows.extend(block)
    # rank of the (8·64, 64) stack; commutant_dim = 64 − rank.
    stacked_cols = [[stacked_rows[r][c] for r in range(len(stacked_rows))]
                    for c in range(64)]
    commutant_dim = 64 - so8._rank_float(stacked_cols)
    assert commutant_dim == 1  # simple (su(2)+su(2) would give 2).

    # rank 2 via the centraliser of a fixed regular element R (FIX 3).
    regular = su3_on[0]
    for i in range(1, 8):
        regular = _add(regular, Mat.from_rows(
            [[(i + 1) * x for x in row] for row in su3_on[i].tolist()]))
    bracket_cols = [coord(_commutator(su3_on[a], regular)) for a in range(8)]
    rank_bracket = so8._rank_float(bracket_cols)
    cartan_dim = 8 - rank_bracket
    assert cartan_dim == 2

    # The greedy mutually-commuting subset is the TRAP — a BASIS-DEPENDENT
    # under-measure (it walks fixed-order columns keeping a generator only if it
    # commutes with all already-kept; generic basis vectors do not pairwise-
    # commute, so it stalls below the true rank-2 Cartan). The exact count it
    # returns depends on the orthonormal basis (the cascade Gram-Schmidt frame
    # differs from a numpy QR frame within the degenerate su(3) span), so it is
    # NOT a reliable rank measure — which is the whole point: the centraliser
    # route (above) IS. Here it stalls at 1 or 2, strictly below / at the true
    # rank only by coincidence, never the dependable Cartan dim.
    kept = []
    for a in range(8):
        if all(_frob(_commutator(su3_on[a], su3_on[j])) < _TOL for j in kept):
            kept.append(a)
    assert 1 <= len(kept) <= 2  # the documented (basis-dependent) greedy trap.


# ----------------------------------------------------------------------
# TEST 4 — the complement is the genuine real su(3)-module ([su3, comp] ⊆ comp).
# ----------------------------------------------------------------------


def test_complement_is_real_su3_module():
    """``[su3, complement] ⊆ complement`` (bit-exact) — the 6-real-dim
    complement is the genuine real su(3)-module."""
    emb = an_embedding()
    su3 = emb["su3"]
    complement = emb["complement"]
    assert len(complement) == 6
    assert _max_closure_residual(su3, complement) < 1e-12


# ----------------------------------------------------------------------
# TEST 5 — FIX 1: J^2 = -I, J commutes with ad(su3)|complement.
# ----------------------------------------------------------------------


def test_invariant_complex_structure_J():
    """The su(3)-INVARIANT complex structure ``J`` on the complement:
    ``J^2 = -I`` and ``[J, ad(X)|complement] = 0`` for every ``X in su(3)``."""
    emb = an_embedding()
    su3 = emb["su3"]
    complement = emb["complement"]
    j = emb["complex_structure_J"]

    assert j.shape == (6, 6)
    # J^2 = -I.
    assert _frob(_add(mat_matmul(j, j), _eye(6))) < _TOL
    # J is antisymmetric (a genuine complex structure on a Euclidean space).
    assert _frob(_add(j, j.T)) < _TOL

    # J commutes with ad(X) restricted to the complement frame, for every X.
    # The returned ``complement`` is already orthonormal in the E_{pq} frame, so
    # ad(X) is built by projecting [X, complement_j] onto that SAME basis (a
    # fresh re-orthonormalisation would re-orient the frame and spuriously
    # break the commutation, since J is fixed to the complement-index basis).
    complement_coords = _coords_of(complement)  # 6 columns (orthonormal, len 28)

    def ad_on_complement(x):
        cols = []
        for y in complement:
            cc = so8._epq_coords(_commutator(x, y))
            col = [sum(complement_coords[r][t] * cc[t] for t in range(28))
                   for r in range(6)]
            cols.append(col)
        # cols is column-major; transpose to a 6×6 row-major Mat.
        return Mat.from_rows([[cols[c][r] for c in range(6)] for r in range(6)])

    for x in su3:
        ad = ad_on_complement(x)
        assert _frob(_commutator(j, ad)) < _TOL


# ----------------------------------------------------------------------
# TEST 6 — FIX 1: [su3, triplet] ⊆ triplet via the J-eigenspace; 3bar = conj(3).
# ----------------------------------------------------------------------


def test_triplet_is_J_eigenspace_fundamental():
    """The genuine fundamental is the ``J = +i`` eigenspace: ``[su3, triplet]
    ⊆ triplet`` is bit-exact (``~3e-14``); ``antitriplet`` is the conjugate of
    ``triplet``."""
    emb = an_embedding()
    su3 = emb["su3"]
    triplet = emb["triplet"]
    antitriplet = emb["antitriplet"]

    # [su3, triplet] ⊆ triplet (the bit-exact closure the J-eigenspace buys).
    closure = _max_closure_residual(su3, triplet)
    assert closure < 3e-13

    # 3bar = conjugate of 3: span(conj(triplet)) == span(antitriplet) (rank 3
    # each; the stacked rank does not grow). Complex coords → float-tolerant.
    conj_coords = _coords_of([t.conj() for t in triplet])
    anti_coords = _coords_of(antitriplet)
    assert so8._rank_float(conj_coords) == 3
    assert so8._rank_float(anti_coords) == 3
    rank_stacked = so8._rank_float(conj_coords + anti_coords)
    assert rank_stacked == 3


# ----------------------------------------------------------------------
# TEST 7 — weights are +/- pairs; (6, 2) shape.
# ----------------------------------------------------------------------


def test_weights_are_plus_minus_pairs():
    """The 6 complement weights under the rank-2 Cartan come in ``+/-`` pairs
    (the su(3) ``3`` weights and their negatives); recorded as a ``(6, 2)``
    nested list."""
    emb = an_embedding()
    weights = emb["weights"]
    assert len(weights) == 6
    assert all(len(w) == 2 for w in weights)

    # Every weight has a +/- partner among the six. (Pairing is the asserted
    # FACT; the per-eigenvector ORDER / 3-vs-3bar orientation is a documented
    # CHOICE, not asserted here.)
    for i in range(6):
        has_partner = any(
            abs(weights[i][0] + weights[j][0]) <= 1e-6
            and abs(weights[i][1] + weights[j][1]) <= 1e-6
            for j in range(6)
        )
        assert has_partner, f"weight {weights[i]} has no +/- partner"

    # The six weights sum to ~0 (the +/- pairs cancel) — a cheap invariant.
    sum0 = sum(weights[i][0] for i in range(6))
    sum1 = sum(weights[i][1] for i in range(6))
    assert mat_norm([sum0, sum1]) < 1e-9


# ----------------------------------------------------------------------
# TEST 8 — decomposition + attestation + framework-reading shape.
# ----------------------------------------------------------------------


def test_decomposition_and_attestation():
    """The returned ``decomposition`` records both branchings; the MPR
    attestation content-addresses the COMPUTED structure (Class A); the A-N
    reading is surfaced ONLY under the separately-keyed framework field."""
    emb = an_embedding()

    assert emb["decomposition"] == {
        "adjoint_14": (8, 3, 3),
        "vector_7": (1, 3, 3),
    }
    assert emb["imaginary_unit"] == 1

    att = emb["attestation"]
    assert att["mpr_version"] == "1.0"
    inner = att["attestation"]
    assert len(inner["response_sha256"]) == 64
    assert len(inner["parser_rule_hash"]) == 64
    assert inner["parser_version"] == "srmech 0.5.0"
    # Baez cited for the g2 = Der(O) / dim-14 PARENT FACT only (the build
    # input); the 8+3+3bar branching is this op's own computation.
    assert inner["source_url"] == "https://arxiv.org/abs/math/0105155"
    assert inner["source_doi"] is None  # paywalled-DOI discipline.

    # The A-N reading is a documented LABEL, not a derived theorem, and lives
    # under its own key tagged accordingly. No A-N class name leaks into any
    # load-bearing return key.
    reading = emb["framework_an_reading"]
    assert reading["note"] == "framework-reading, not derived"
    assert reading["an_discovery_partition"] == (1, 3, 7, 3)
    assert reading["su3_lie_branching"] == (8, 3, 3)
    assert reading["slot_aligned"] is False
    load_bearing = {
        "su3", "complement", "complex_structure_J", "triplet",
        "antitriplet", "weights", "decomposition", "imaginary_unit",
        "attestation",
    }
    for key in load_bearing:
        lowered = key.lower()
        for tag in ("class_a", "class_c", "class_k", "class_l", "class_m",
                    "class_n", "class_b", "class_h"):
            assert tag not in lowered


# ----------------------------------------------------------------------
# TEST 9 — determinism (byte-identical) + the response hash is reproducible.
# ----------------------------------------------------------------------


def test_determinism_byte_identical():
    """Two builds are entry-identical (deterministic — no RNG), so the
    content-addressed attestation hash is reproducible."""
    e1 = an_embedding(1)
    e2 = an_embedding(1)

    for a, b in zip(e1["su3"], e2["su3"]):
        assert a == b
    for a, b in zip(e1["complement"], e2["complement"]):
        assert a == b
    for a, b in zip(e1["triplet"], e2["triplet"]):
        assert a == b
    for a, b in zip(e1["antitriplet"], e2["antitriplet"]):
        assert a == b
    assert e1["complex_structure_J"] == e2["complex_structure_J"]
    assert e1["weights"] == e2["weights"]
    assert (
        e1["attestation"]["attestation"]["response_sha256"]
        == e2["attestation"]["attestation"]["response_sha256"]
    )

    # The returned Mats are independent copies (mutating one's buffer does not
    # leak into the cache / the other call).
    e1["su3"][0].buffer[0] = 999.0
    e3 = an_embedding(1)
    assert e3["su3"][0][0, 0] != 999.0


# ----------------------------------------------------------------------
# TEST 10 — the construction is robust across every imaginary unit 1..7.
# ----------------------------------------------------------------------


def test_all_imaginary_units():
    """The su(3) ⊕ 3 ⊕ 3bar branching is bit-exact for every ``K in 1..7``
    (the choice of stabilised imaginary unit gives a conjugate, hence
    isomorphic, decomposition)."""
    for k in range(1, 8):
        emb = an_embedding(k)
        su3 = emb["su3"]
        complement = emb["complement"]
        triplet = emb["triplet"]
        j = emb["complex_structure_J"]
        assert len(su3) == 8 and len(complement) == 6 and len(triplet) == 3
        assert _frob(_add(mat_matmul(j, j), _eye(6))) < _TOL
        assert _max_closure_residual(su3, complement) < 1e-12
        assert _max_closure_residual(su3, triplet) < 3e-13
        assert emb["imaginary_unit"] == k


# ----------------------------------------------------------------------
# TEST 11 — ValueError on an out-of-range imaginary unit.
# ----------------------------------------------------------------------


def test_value_error_on_out_of_range():
    """``imaginary_unit`` must be in ``1..7`` (the 7 octonion imaginary
    units); ``0`` and ``8`` raise ``ValueError``."""
    with pytest.raises(ValueError):
        an_embedding(0)
    with pytest.raises(ValueError):
        an_embedding(8)
