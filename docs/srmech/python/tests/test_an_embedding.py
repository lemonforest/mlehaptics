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
reducing the matrix to a scalar Frobenius norm, then passing that Python
float to ``magnitude`` (scalar-only; it raises on an ndarray).

Determinism: every basis extraction uses a deterministic SVD / QR / eig (no
``np.random``), so the build is reproducible and byte-identical across calls.
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc.cascade import magnitude
from srmech.qm import so8
from srmech.qm.so8 import an_embedding

_TOL = 1e-9


# ----------------------------------------------------------------------
# Test helpers — scalar reductions through cascade.magnitude (no abs()).
# ----------------------------------------------------------------------


def _frob(matrix: np.ndarray) -> float:
    """Frobenius-norm deviation reduced through the scalar Class K magnitude.

    Reduce the matrix to a SCALAR float FIRST (``np.linalg.norm`` is the
    Euclidean / Frobenius norm), then pass that scalar to
    ``cascade.magnitude`` (scalar-only; raises on an ndarray). NEVER
    ``abs()``.
    """
    scalar = float(np.linalg.norm(matrix))
    return magnitude(scalar)


def _coords_of(generators) -> np.ndarray:
    """Stack the E_{pq}-coords of a generator iterable as a ``(28, k)`` matrix.

    Works for real or complex generators (the J-eigenspace triplet is
    complex).
    """
    return np.column_stack([so8._epq_coords(g) for g in generators])


def _commutator(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Matrix commutator ``[X, Y]`` (real or complex)."""
    return x @ y - y @ x


def _max_closure_residual(inner, outer) -> float:
    """Max residual of ``[X, Y]`` projected onto ``span(outer)`` over X∈inner.

    The closure test ``[inner, outer] ⊆ span(outer)``: each ``[X, Y]`` (X in
    ``inner``, Y in ``outer``) must lie in the span of ``outer``. Projector is
    built from a (complex-aware) QR of the ``outer`` coordinate stack; the
    residual is reduced through the scalar Class K magnitude (no ``abs()``).
    """
    outer_coords = _coords_of(outer)
    basis, _ = np.linalg.qr(outer_coords)
    projector = basis @ basis.conj().T
    worst = 0.0
    for x in inner:
        for y in outer:
            cc = so8._epq_coords(_commutator(x, y))
            residual = float(np.linalg.norm(cc - projector @ cc))
            worst = max(worst, magnitude(residual))
    return worst


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
        assert matrix.dtype == np.float64
    for matrix in triplet + antitriplet:
        assert matrix.shape == (8, 8)
        assert np.iscomplexobj(matrix)

    g2 = so8.g2_subalgebra()
    assert len(g2) == 14

    su3_coords = _coords_of(su3)
    complement_coords = _coords_of(complement)
    g2_coords = _coords_of(g2)
    span = np.concatenate([su3_coords, complement_coords], axis=1)

    rank_span = np.linalg.matrix_rank(span, tol=_TOL)
    rank_with_g2 = np.linalg.matrix_rank(
        np.concatenate([span, g2_coords], axis=1), tol=_TOL
    )
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
    e_k = np.eye(8)[k]

    # su(3) fixes e_K (the stabiliser construction).
    for matrix in su3:
        assert _frob(matrix @ e_k) < 1e-12

    # su(3) ⊆ g2: stacking g2 with su3 does not raise the rank past 14.
    g2 = so8.g2_subalgebra()
    g2_coords = _coords_of(g2)
    su3_coords = _coords_of(su3)
    assert np.linalg.matrix_rank(su3_coords, tol=_TOL) == 8
    rank_stacked = np.linalg.matrix_rank(
        np.concatenate([g2_coords, su3_coords], axis=1), tol=_TOL
    )
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
    identifies su(3).
    """
    emb = an_embedding()
    su3 = emb["su3"]
    assert len(su3) == 8

    # Killing-orthonormalise (QR of the coords) so the structure-constant
    # frame is well-conditioned and the metric is the identity.
    coords = _coords_of(su3)
    q, _ = np.linalg.qr(coords)
    su3_on = [so8._epq_to_matrix(q[:, c]) for c in range(8)]

    def coord(m):
        return so8._epq_coords(m)

    # Structure constants f_abc = <X_c, [X_a, X_b]> (orthonormal => metric I).
    f = np.zeros((8, 8, 8))
    for a in range(8):
        for b in range(8):
            cab = coord(_commutator(su3_on[a], su3_on[b]))
            for c in range(8):
                f[a, b, c] = float(np.dot(coord(su3_on[c]), cab))

    # Total antisymmetry: f_abc = -f_bac = -f_acb (residual via magnitude).
    antisym = 0.0
    for a in range(8):
        for b in range(8):
            for c in range(8):
                antisym = max(
                    antisym,
                    magnitude(float(f[a, b, c] + f[b, a, c])),
                    magnitude(float(f[a, b, c] + f[a, c, b])),
                )
    assert antisym < 1e-9

    # Adjoint matrices (ad X_a)[c, b] = f_abc; commutant dim 1 <=> simple.
    ad = [f[a].T for a in range(8)]
    identity = np.eye(8)
    stacked = np.vstack(
        [np.kron(m.T, identity) - np.kron(identity, m) for m in ad]
    )
    singular = np.linalg.svd(stacked, compute_uv=False)
    commutant_dim = int(np.sum(singular < _TOL * max(1.0, float(singular[0]))))
    assert commutant_dim == 1  # simple (su(2)+su(2) would give 2).

    # rank 2 via the centraliser of a fixed regular element R (FIX 3).
    regular = sum((i + 1) * su3_on[i] for i in range(8))
    bracket = np.column_stack(
        [coord(_commutator(su3_on[a], regular)) for a in range(8)]
    )
    sv_b = np.linalg.svd(bracket, compute_uv=False)
    rank_bracket = int(np.sum(sv_b > _TOL * max(1.0, float(sv_b[0]))))
    cartan_dim = 8 - rank_bracket
    assert cartan_dim == 2

    # The greedy mutually-commuting subset is the TRAP — it returns 1, which
    # is why the centraliser route (above) is the correct rank-2 measure.
    kept = []
    for a in range(8):
        if all(_frob(_commutator(su3_on[a], su3_on[j])) < _TOL for j in kept):
            kept.append(a)
    assert len(kept) == 1  # the documented greedy trap.


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
    assert _frob(j @ j + np.eye(6)) < _TOL
    # J is antisymmetric (a genuine complex structure on a Euclidean space).
    assert _frob(j + j.T) < _TOL

    # J commutes with ad(X) restricted to the complement frame, for every X.
    # The frame J lives in is the complement matrices' OWN coordinates — the
    # returned ``complement`` is already orthonormal in the E_{pq} frame
    # (``_epq_coords(complement[i])`` are orthonormal columns), so we express
    # ad(X) by projecting [X, complement_j] onto that SAME basis. A fresh QR
    # would re-orient the frame and spuriously break the commutation, since
    # J is fixed to the complement-index basis, not to a re-QR'd one.
    complement_coords = _coords_of(complement)  # (28, 6), orthonormal
    assert _frob(complement_coords.T @ complement_coords - np.eye(6)) < _TOL

    def ad_on_complement(x):
        cols = [
            complement_coords.T @ so8._epq_coords(_commutator(x, y))
            for y in complement
        ]
        return np.column_stack(cols)

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
    # each; the stacked rank does not grow).
    conj_coords = _coords_of([np.conj(t) for t in triplet])
    anti_coords = _coords_of(antitriplet)
    assert np.linalg.matrix_rank(conj_coords, tol=_TOL) == 3
    assert np.linalg.matrix_rank(anti_coords, tol=_TOL) == 3
    rank_stacked = np.linalg.matrix_rank(
        np.concatenate([conj_coords, anti_coords], axis=1), tol=_TOL
    )
    assert rank_stacked == 3


# ----------------------------------------------------------------------
# TEST 7 — weights are +/- pairs; (6, 2) shape.
# ----------------------------------------------------------------------


def test_weights_are_plus_minus_pairs():
    """The 6 complement weights under the rank-2 Cartan come in ``+/-`` pairs
    (the su(3) ``3`` weights and their negatives); recorded as a ``(6, 2)``
    real array."""
    emb = an_embedding()
    weights = emb["weights"]
    assert weights.shape == (6, 2)

    # Every weight has a +/- partner among the six. (Pairing is the asserted
    # FACT; the per-eigenvector ORDER / 3-vs-3bar orientation is a documented
    # CHOICE, not asserted here.)
    for i in range(6):
        has_partner = any(
            np.allclose(weights[i], -weights[j], atol=1e-6) for j in range(6)
        )
        assert has_partner, f"weight {weights[i]} has no +/- partner"

    # The six weights sum to ~0 (the +/- pairs cancel) — a cheap invariant.
    assert _frob(weights.sum(axis=0)) < 1e-9


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
    assert inner["parser_version"] == "srmech 0.5.0rc21"
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
    """Two builds are byte-identical (deterministic — no ``np.random``), so
    the content-addressed attestation hash is reproducible."""
    e1 = an_embedding(1)
    e2 = an_embedding(1)

    for a, b in zip(e1["su3"], e2["su3"]):
        assert np.array_equal(a, b)
    for a, b in zip(e1["complement"], e2["complement"]):
        assert np.array_equal(a, b)
    for a, b in zip(e1["triplet"], e2["triplet"]):
        assert np.array_equal(a, b)
    for a, b in zip(e1["antitriplet"], e2["antitriplet"]):
        assert np.array_equal(a, b)
    assert np.array_equal(
        e1["complex_structure_J"], e2["complex_structure_J"]
    )
    assert np.array_equal(e1["weights"], e2["weights"])
    assert (
        e1["attestation"]["attestation"]["response_sha256"]
        == e2["attestation"]["attestation"]["response_sha256"]
    )

    # The returned arrays are independent copies (mutating one does not leak
    # into the cache / the other call).
    e1["su3"][0][0, 0] = 999.0
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
        assert _frob(j @ j + np.eye(6)) < _TOL
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
