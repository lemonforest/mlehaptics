"""rc462 — the ℚ(ζₑ) rep-payload dialect (`#T1179`, steps C5–C7).

**What this gate is for.**  rc460 deferred the ζ widening with a reason:
*a checker widened alone mints a dialect no producer can write and no
consumer can read.*  So the widening ships as ONE package — cell grammar,
payload keys, a domain-separated serializer branch, the ζ-vector trace
path, the Galois action, a PRODUCER, four widened consumers and three
refusals — and this file executes every part of it.

**The hash-stability half lives next door and must stay green.**
``tests/test_rep_hash_stability_rc462.py`` pins 25 ℚ payloads as literals
and was written BEFORE ``_rep_matrices_bytes`` moved.  Nothing here edits
it; the acceptance predicate for the whole package is that it still
passes with zero pin literals touched.

**Why a THIRD serializer branch and not a widened general branch.**  Two
acceptance requirements read as contradictory: *no shipped ℚ digest may
move*, and *no ℚ/ζ body may collide*.  Both horns belong to designs that
EDIT the general branch.  A third branch keyed on ``kind`` leaves both
existing branches untaken, so ℚ bytes are unmoved by construction, and
the ``zeta{e}`` prefix separates the domains unconditionally.  The
cross-conductor case is the one that needs it and is MEASURED here:
``φ(3) == φ(4) == φ(6) == 2``, so three different rings serialize to the
same body without the prefix — :func:`test_g05_negative_control_the_
unprefixed_spelling_collides` proves the collision gate can fire.

**Both producer witnesses ship, and neither is redundant.**  Q8 induced
from ⟨i⟩ exercises the ζ MATRIX path with a RATIONAL character (its
degree-2 irrep has Frobenius–Schur indicator −1, so it is quaternionic
and not ℝ-realizable, hence not ℚ-realizable — exactly the rep the old
payload could not hold).  C4 induced from itself exercises the ζ-VECTOR
character path (its two indicator-0 rows are the ℚ-unrealizability
certificate for a conjugate pair).  Dropping either leaves one of the two
new code paths untested.

**Every refusal is proved REACHABLE**: the payload it refuses is one the
widened checker ACCEPTS.  An instrument that could only ever be reached
by an already-invalid operand is not a measurement.

NO numpy.  NO ``hashlib``.  NO ``abs()``.  Digests go through
``srmech.amsc.format.sha256_bytes``; ring products go through the shipped
``zeta_mul`` / ``_zeta_mul``.
"""
from __future__ import annotations

import copy

import pytest

from srmech.amsc.format import sha256_bytes
from srmech.cascade import dihedral_group, unit_loop
from srmech.math.groups import (_check_rep_payload, _rep_matrices_bytes,
                                _table_bytes, _zeta_mul, character_of,
                                character_table, cyclic_group,
                                decompose_representation,
                                direct_sum_representation,
                                frobenius_schur_indicator,
                                induced_representation, intertwiner_space,
                                isotypic_projector,
                                permutation_representation,
                                semidirect_product,
                                tensor_product_representation, zeta_conjugate,
                                zeta_mul)
from srmech.math.poly import cyclotomic_polynomial
from srmech.math.q import Q
from srmech.math.qalg import Qalg

# ── the corpus, DERIVED from the shipped constructors ────────────────────

C = {n: cyclic_group(n)["cayley_table"] for n in range(2, 9)}
Q8 = unit_loop(4)["cayley_table"]
D4 = dihedral_group(4, "rotation_first")["cayley_table"]
S3 = semidirect_product(C[3], C[2], [[0, 1, 2], [0, 2, 1]])["cayley_table"]

#: ``H = <i> = {1, i, -1, -i}`` inside ``unit_loop(4)``, DERIVED by walking
#: the table rather than pinned — a pinned index set would silently become
#: a different subgroup if the constructor's element order ever moved.
def _cyclic_subgroup(tbl, generator):
    walk = [0]
    x = generator
    while x != 0:
        walk.append(x)
        x = tbl[x][generator]
    return sorted(walk)


Q8_I = _cyclic_subgroup(Q8, 1)
#: ``χ(i^k) = ζ₄^k`` on ``H``, in ASCENDING element order.
_POWERS_4 = ((1, 0), (0, 1), (-1, 0), (0, -1))


def _faithful_character(tbl, subgroup, generator, powers):
    """``χ`` over ``sorted(subgroup)``, built by walking the generator so
    the value lands on the element it belongs to."""
    value = {}
    x = 0
    for k in range(len(subgroup)):
        value[x] = powers[k % len(powers)]
        x = tbl[x][generator]
    return [value[h] for h in subgroup]


Q8_CHI = _faithful_character(Q8, Q8_I, 1, _POWERS_4)
C4_CHI = _faithful_character(C[4], [0, 1, 2, 3], 1, _POWERS_4)


def _q8_rep():
    return induced_representation(Q8, Q8_I, Q8_CHI, 4)


def _c4_rep():
    return induced_representation(C[4], [0, 1, 2, 3], C4_CHI, 4)


# ── G01 the construction check: zeta_mul against Qalg ────────────────────


def test_g01_the_ring_kernel_agrees_with_qalg_over_eight_conductors():
    """The producer's arithmetic, checked against an INDEPENDENT engine.

    ``zeta_mul`` reduces an integer convolution mod the monic ``Φ_e``;
    :class:`srmech.math.qalg.Qalg` multiplies in ``ℚ[x]/Φ_e`` over exact
    rationals.  They share no code.  Agreement over eight conductors —
    including the three where ``φ(e) == 2`` and the deep rings ``e = 7, 9,
    12`` — is what licenses the producer to build its matrices with the
    kernel.  Every ``Qalg`` product is additionally asserted INTEGRAL,
    which is the ``ℤ[ζ_e]``-closure claim the cell grammar rests on.
    """
    total = mismatches = nonintegral = 0
    for e in (3, 4, 5, 6, 7, 8, 9, 12):
        entry = cyclotomic_polynomial(e)
        phi = list(entry["coefficients"])
        width = entry["degree"]
        vectors = []
        for s in range(-2, 4):
            for j in range(width):
                v = [0] * width
                v[j] = s
                vectors.append(tuple(v))
            vectors.append(tuple((s + t) % 5 - 2 for t in range(width)))
        for u in vectors:
            for v in vectors:
                got = zeta_mul(u, v, phi)
                want = (Qalg(phi, [Q(x, 1) for x in u])
                        * Qalg(phi, [Q(x, 1) for x in v]))
                pairs = [c.as_pair() for c in want.coords]
                if any(den != 1 for _, den in pairs):
                    nonintegral += 1
                if list(got) != [num for num, _ in pairs]:
                    mismatches += 1
                total += 1
    assert total >= 960, total
    assert (total, mismatches, nonintegral) == (7200, 0, 0)


# ── G02–G05 the serializer: domain separation, measured ──────────────────


def test_g02_the_cyclotomic_branch_refuses_to_serialize_without_its_ring():
    """The conductor is not defaultable.  A serialization that dropped it
    would content-address two DIFFERENT rings to one digest, silently."""
    cells = [[[((1, 1), (0, 1))]]]
    with pytest.raises(ValueError, match="domain-separation law"):
        _rep_matrices_bytes("cyclotomic", cells)
    with pytest.raises(ValueError, match="domain-separation law"):
        _rep_matrices_bytes("cyclotomic", cells, "4")
    assert _rep_matrices_bytes("cyclotomic", cells, 4) == b"zeta4\n1/1;0/1"


def test_g03_the_two_rational_branches_are_byte_identical_to_two_arg_calls():
    """The third branch is ADDITIVE.  Both ℚ branches must answer exactly
    what they answered before ``e`` existed as a parameter — this is the
    same claim ``test_rep_hash_stability_rc462`` pins as literals, checked
    here from the other side (call shape rather than digest value)."""
    perm = permutation_representation(C[3], C[3])["matrices"]
    general = [[[(3, 4), (0, 1)], [(-1, 2), (1, 1)]]]
    assert (_rep_matrices_bytes("permutation", perm)
            == _rep_matrices_bytes("permutation", perm, None))
    assert (_rep_matrices_bytes("general", general)
            == _rep_matrices_bytes("general", general, None))
    assert _rep_matrices_bytes("general", general) == b"3/4,0/1\n-1/2,1/1"
    # and the ζ body of the SAME numbers is a different object entirely
    zeta = [[[((3, 4), (0, 1)), ((-1, 2), (1, 1))]]]
    assert (_rep_matrices_bytes("cyclotomic", zeta, 4)
            == b"zeta4\n3/4;0/1,-1/2;1/1")


def _collision_corpus():
    """ℚ and ζ fixtures side by side, all but two DERIVED from the shipped
    constructors.  The two hand-written ones are the cross-conductor
    near-collision and are named as the exception."""
    bodies = {}
    for n in (2, 3, 4, 5, 6, 7, 8):
        bodies["C%d_reg" % n] = (
            "permutation", permutation_representation(C[n], C[n])["matrices"],
            None)
    for name, tbl in (("Q8", Q8), ("D4", D4), ("S3", S3)):
        bodies[name + "_reg"] = (
            "permutation", permutation_representation(tbl, tbl)["matrices"],
            None)
    bodies["S3_sign"] = ("general", [
        [[(1, 1)]] if i % 2 == 0 else [[(-1, 1)]] for i in range(6)], None)
    bodies["gen_3_4"] = ("general", [[[(3, 4)]]], None)
    for label, tbl, sub, chi, e in (
            ("Q8_i", Q8, Q8_I, Q8_CHI, 4),
            ("C4_full", C[4], [0, 1, 2, 3], C4_CHI, 4),
            ("C3_full", C[3], [0, 1, 2], _faithful_character(
                C[3], [0, 1, 2], 1, ((1, 0), (0, 1), (-1, -1))), 3),
            ("C6_full", C[6], [0, 1, 2, 3, 4, 5], _faithful_character(
                C[6], [0, 1, 2, 3, 4, 5], 1,
                ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))), 6),
            ("C5_full", C[5], [0, 1, 2, 3, 4], _faithful_character(
                C[5], [0, 1, 2, 3, 4], 1,
                ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1),
                 (-1, -1, -1, -1))), 5),
            ("C8_full", C[8], list(range(8)), _faithful_character(
                C[8], list(range(8)), 1,
                ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1),
                 (-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, -1, 0),
                 (0, 0, 0, -1))), 8)):
        rep = induced_representation(tbl, sub, chi, e)
        bodies["ind_" + label] = ("cyclotomic", rep["matrices"], e)
    # THE EXCEPTION, named: the same coordinates in three different rings.
    # phi(3) == phi(4) == phi(6) == 2, so these bodies are identical
    # WITHOUT the prefix, which is the whole reason the prefix exists.
    for e in (3, 4, 6):
        bodies["hand_zeta%d" % e] = (
            "cyclotomic", [[[((3, 4), (0, 1))]]], e)
    return bodies


def test_g04_distinct_digests_iff_distinct_bodies_across_the_whole_sweep():
    """The collision gate.  Over ℚ and ζ fixtures together, two digests are
    equal exactly when their canonical bodies are — the property a content
    address must have and the one the widening could have broken."""
    bodies = _collision_corpus()
    serialized = {k: _rep_matrices_bytes(*v) for k, v in bodies.items()}
    digests = {k: sha256_bytes(b) for k, b in serialized.items()}
    names = sorted(bodies)
    pairs = disagreements = 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pairs += 1
            if (serialized[a] == serialized[b]) != (digests[a] == digests[b]):
                disagreements += 1
    assert (len(names), pairs, disagreements) == (21, 210, 0)
    assert len({bytes(b) for b in serialized.values()}) == 21
    assert len(set(digests.values())) == 21


def test_g05_negative_control_the_unprefixed_spelling_collides():
    """A collision gate that cannot fire is not a measurement.

    The naive spelling — the same cell grammar with the ``zeta{e}`` prefix
    dropped — collides on exactly the three cross-conductor pairs, because
    ``φ(3) == φ(4) == φ(6) == 2``.  This is the defect the third branch
    was designed against, executed."""
    bodies = _collision_corpus()

    def naive(kind, matrices, e=None):
        if kind != "cyclotomic":
            return _rep_matrices_bytes(kind, matrices, e)
        return "\n\n".join(
            "\n".join(",".join(
                ";".join("%d/%d" % (c[0], c[1]) for c in cell)
                for cell in row) for row in mat)
            for mat in matrices).encode("utf-8")

    real = {k: _rep_matrices_bytes(*v) for k, v in bodies.items()}
    flat = {k: naive(*v) for k, v in bodies.items()}
    names = sorted(bodies)
    collided = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
                if flat[a] == flat[b] and real[a] != real[b]]
    assert len(collided) == 3, collided
    assert sorted(collided) == [("hand_zeta3", "hand_zeta4"),
                                ("hand_zeta3", "hand_zeta6"),
                                ("hand_zeta4", "hand_zeta6")]
    for a, b in collided:
        assert flat[a] == b"3/4;0/1"
        assert real[a] != real[b]


# ── G06–G10 the checker: every new law, each reachable and named ─────────


def test_g06_the_coupling_law_fires_in_BOTH_directions():
    """``kind == 'cyclotomic'`` iff ``field`` is a ``Q(zeta_N)`` spelling.
    A one-directional check would let a ℚ payload wear the ζ field (or the
    reverse) and be dispatched by the wrong branch."""
    zeta = copy.deepcopy(_q8_rep())
    zeta["field"] = "Q"
    with pytest.raises(ValueError, match="coupling law"):
        _check_rep_payload("probe", zeta)

    rational = dict(permutation_representation(C[3], C[3]))
    rational["field"] = "Q(zeta_3)"
    with pytest.raises(ValueError, match="coupling law"):
        _check_rep_payload("probe", rational)


def test_g07_the_field_law_still_refuses_a_foreign_field():
    """The rc458 message widened; it did not weaken.  ``'R'`` is neither
    ``'Q'`` nor a ``Q(zeta_N)`` spelling, and near-misses of the ζ
    spelling are refused by the same law rather than parsed loosely."""
    for bad in ("R", "C", "Q(zeta_)", "Q(zeta_x)", "Q(zeta_4", "GF(2)"):
        rep = dict(permutation_representation(C[3], C[3]))
        rep["field"] = bad
        with pytest.raises(ValueError, match="field law"):
            _check_rep_payload("probe", rep)


def test_g08_the_ring_law_pins_conductor_field_and_modulus():
    """``e >= 3`` (ℚ(ζ₁) = ℚ(ζ₂) = ℚ, which the general kind already
    spells), ``field`` determined by ``e``, and a MONIC modulus of degree
    ``φ(e) >= 2``."""
    for bad_e in (2, 1, 0, -4, True, "4"):
        rep = copy.deepcopy(_q8_rep())
        rep["e"] = bad_e
        with pytest.raises(ValueError, match="ring law"):
            _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    rep["e"] = 6                       # field still says 4
    with pytest.raises(ValueError, match="ring law"):
        _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    rep["phi_e"] = (1, 0, 2)           # not monic
    with pytest.raises(ValueError, match="ring law"):
        _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    rep["phi_e"] = (1, 1)              # degree 1 < 2
    with pytest.raises(ValueError, match="ring law"):
        _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    del rep["phi_e"]
    with pytest.raises(ValueError, match="payload-key law"):
        _check_rep_payload("probe", rep)


def test_g09_the_ring_width_and_canonical_pair_laws_reach_each_coordinate():
    """A ζ cell is ``φ(e)`` coordinates and each is a canonical pair — the
    SAME law the general kind enforces on its single entry, hoisted so
    there is one spelling of it."""
    rep = copy.deepcopy(_q8_rep())
    rep["matrices"][0][0][0] = ((1, 1),)
    with pytest.raises(ValueError, match="ring-width law"):
        _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    rep["matrices"][0][0][0] = ((2, 2), (0, 1))
    with pytest.raises(ValueError, match="canonical-pair law"):
        _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    rep["matrices"][0][0][0] = ((1, -1), (0, 1))
    with pytest.raises(ValueError, match="canonical-pair law"):
        _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    rep["matrices"][0][0][0] = ((Q(1, 1), 1), (0, 1))
    with pytest.raises(ValueError, match="canonical-pair law"):
        _check_rep_payload("probe", rep)

    rep = copy.deepcopy(_q8_rep())
    rep["matrices"][0][0][0] = ((True, 1), (0, 1))
    with pytest.raises(ValueError, match="canonical-pair law"):
        _check_rep_payload("probe", rep)


def test_g10_the_content_address_law_covers_the_zeta_lane():
    """The recompute threads ``e``: a payload whose matrices moved, and a
    payload whose RING moved with identical matrices, are both refused."""
    rep = copy.deepcopy(_q8_rep())
    rep["matrices"][0][0][0] = ((0, 1), (0, 1))
    with pytest.raises(ValueError, match="content-address law"):
        _check_rep_payload("probe", rep)

    # same matrices, same field/e coupling, a DIFFERENT ring: refused only
    # because the digest carries the conductor.
    six = copy.deepcopy(_q8_rep())
    six["e"] = 6
    six["field"] = "Q(zeta_6)"
    six["phi_e"] = tuple(cyclotomic_polynomial(6)["coefficients"])
    with pytest.raises(ValueError, match="content-address law"):
        _check_rep_payload("probe", six)
    six["matrices_sha256"] = sha256_bytes(
        _rep_matrices_bytes("cyclotomic", six["matrices"], 6))
    _check_rep_payload("probe", six)      # now coherent, and a NEW address
    assert six["matrices_sha256"] != _q8_rep()["matrices_sha256"]


# ── G11–G16 the producer ─────────────────────────────────────────────────


def test_g11_the_q8_witness_is_a_homomorphism_by_a_second_route():
    """The op checks the homomorphism law on its MONOMIAL data (O(|G|²·m)
    ring products).  This is the INDEPENDENT route: dense matrix products
    over ``ℤ[ζ₄]``, all 64 pairs, sharing no code with the in-op check."""
    rep = _q8_rep()
    assert rep["degree"] == 2
    assert rep["field"] == "Q(zeta_4)"
    assert rep["kind"] == "cyclotomic"
    assert rep["subgroup"] == Q8_I == [0, 1, 4, 5]

    phi = list(rep["phi_e"])
    width = len(phi) - 1
    dense = [[[tuple(coord[0] for coord in cell) for cell in row]
              for row in mat] for mat in rep["matrices"]]
    for mat in rep["matrices"]:
        for row in mat:
            for cell in row:
                assert all(den == 1 for _, den in cell), cell

    def product(a, b):
        n = len(a)
        out = []
        for r in range(n):
            row = []
            for c in range(n):
                acc = [0] * width
                for k in range(n):
                    got = _zeta_mul(a[r][k], b[k][c], phi)
                    for t in range(width):
                        acc[t] += got[t]
                row.append(tuple(acc))
            out.append(row)
        return out

    checked = failures = 0
    for g in range(8):
        for h in range(8):
            checked += 1
            if product(dense[g], dense[h]) != dense[Q8[g][h]]:
                failures += 1
    assert (checked, failures) == (64, 0)


def test_g12_the_q8_character_is_the_shipped_degree_two_row():
    """⚠️ Compared against ``character_table(Q8)['table'][k]`` computed
    from the SAME table, never a hard-coded tuple: the class ORDER of a
    character tuple is derived from the operand table, so a literal pinned
    from one construction reds under another and reads as a real failure.
    """
    rep = _q8_rep()
    ct = character_table(Q8)
    chi = character_of(rep, ct)
    assert chi["kind"] == "cyclotomic"
    assert chi["degree"] == 2
    values = [tuple(v) for v in chi["character"]]
    matches = [i for i, row in enumerate(ct["table"])
               if [tuple(c) for c in row] == values]
    assert len(matches) == 1, matches
    assert ct["degrees"][matches[0]] == 2

    # the character came back RATIONAL, and the row is QUATERNIONIC:
    # Frobenius-Schur -1 means not R-realizable, hence not Q-realizable,
    # which is exactly the rep the exact-Q payload could never hold.
    assert all(v[1:] == (0,) * (len(v) - 1) for v in values)
    assert frobenius_schur_indicator(ct)["indicators"][matches[0]] == -1


def test_g13_the_c4_witness_carries_a_zeta_vector_character():
    """The second witness, and it is not redundant: here the CHARACTER
    itself leaves the rational lane, which is the code path
    ``_exact_zeta_trace`` and the ζ contraction exist for."""
    rep = _c4_rep()
    ct = character_table(C[4])
    assert rep["degree"] == 1 and rep["coset_representatives"] == [0]
    chi = character_of(rep, ct)
    values = [tuple(v) for v in chi["character"]]
    assert any(v[1:] != (0,) * (len(v) - 1) for v in values), values

    matches = [i for i, row in enumerate(ct["table"])
               if [tuple(c) for c in row] == values]
    assert len(matches) == 1
    indicators = frobenius_schur_indicator(ct)["indicators"]
    assert indicators[matches[0]] == 0
    assert indicators.count(0) == 2      # the conjugate PAIR

    dense_failures = 0
    phi = list(rep["phi_e"])
    for g in range(4):
        for h in range(4):
            left = _zeta_mul(
                tuple(c[0] for c in rep["matrices"][g][0][0]),
                tuple(c[0] for c in rep["matrices"][h][0][0]), phi)
            right = tuple(c[0] for c in rep["matrices"][C[4][g][h]][0][0])
            if left != right:
                dense_failures += 1
    assert dense_failures == 0


def test_g13b_a_degree_three_witness_decomposes_into_three_constituents():
    """Both headline witnesses are irreducible, which makes ``norm == 1``
    and hides whether the ζ contraction can count PAST one.  ``C3 × C3``
    has exponent 3, so its table ring and the rep ring agree, and
    ``Ind`` from one factor is degree 3 splitting into THREE distinct
    linear characters — the multiplicity vector the irreducible cases
    cannot produce."""
    c3c3 = semidirect_product(C[3], C[3], [[0, 1, 2]] * 3)["cayley_table"]
    generator = next(g for g in range(1, 9)
                     if _cyclic_subgroup(c3c3, g) != [0])
    members = _cyclic_subgroup(c3c3, generator)
    assert len(members) == 3
    chi = _faithful_character(c3c3, members, generator,
                              ((1, 0), (0, 1), (-1, -1)))
    rep = induced_representation(c3c3, members, chi, 3)
    assert rep["degree"] == 3

    ct = character_table(c3c3)
    assert ct["exponent"] == 3 and tuple(ct["phi_e"]) == (1, 1, 1)
    out = decompose_representation(rep, ct)
    assert out["norm"] == 3 and out["is_irreducible"] is False
    assert sorted(out["multiplicities"]) == [0] * 6 + [1] * 3
    assert sum(m * d for m, d in zip(out["multiplicities"],
                                     ct["degrees"])) == 3
    # the completeness and trace laws run in-op on a degree-3 ζ operand
    assert isotypic_projector(rep, ct)["denominator"] == 9
    # and the Galois action moves ALL THREE constituents
    twisted = decompose_representation(zeta_conjugate(rep, 2), ct)
    assert twisted["multiplicities"] != out["multiplicities"]
    assert sorted(twisted["multiplicities"]) == sorted(out["multiplicities"])


def test_g13c_a_SUBFIELD_rep_is_refused_and_that_is_a_named_scope_boundary():
    """⚠️ THE HONEST GAP, executed rather than described.

    ``F21 = C7⋊C3`` has exponent 21, so ``character_table`` works over
    ``ℚ(ζ₂₁)``; ``Ind_{C7}^{F21}`` of a faithful ``C7`` character is a
    perfectly well-formed degree-3 rep over ``ℚ(ζ₇)``, and ``ζ₇ = ζ₂₁³``
    embeds one ring in the other.  This rc does NOT perform that
    embedding, and the compatible-ring law refuses the pairing rather than
    multiplying mod the wrong modulus.  The refusal is the shipped state;
    this test is what stops it being a silent one, and it is here so a
    later rc that lifts the restriction has a red to turn green."""
    f21 = semidirect_product(
        C[7], C[3], [[(a * pow(2, h, 7)) % 7 for a in range(7)]
                     for h in range(3)])["cayley_table"]
    generator = next(g for g in range(1, 21)
                     if len(_cyclic_subgroup(f21, g)) == 7)
    members = _cyclic_subgroup(f21, generator)
    entry = cyclotomic_polynomial(7)
    powers = []
    current = [0] * entry["degree"]
    current[0] = 1
    for _ in range(7):
        powers.append(tuple(current))
        carry = current[-1]
        nxt = [0] * entry["degree"]
        for i in range(entry["degree"] - 1, 0, -1):
            nxt[i] = current[i - 1]
        if carry:
            for i in range(entry["degree"]):
                nxt[i] -= carry * entry["coefficients"][i]
        current = nxt
    chi = _faithful_character(f21, members, generator, tuple(powers))

    rep = induced_representation(f21, members, chi, 7)
    assert rep["degree"] == 3                      # the rep IS well-formed
    _check_rep_payload("probe", rep)               # and the checker takes it

    ct = character_table(f21)
    assert ct["exponent"] == 21
    assert len(ct["phi_e"]) - 1 == 12 != len(rep["phi_e"]) - 1 == 6
    with pytest.raises(ValueError, match="compatible-ring law"):
        character_of(rep, ct)


def test_g14_the_trivial_character_reduces_to_the_permutation_rep():
    """The op's own Class-L claim, executed: ``Ind_H^G 1`` IS the
    permutation representation on the cosets, cell for cell.  If this
    failed, the coset indexing or the pinned matrix convention would have
    drifted between the two producers."""
    for tbl, sub in ((Q8, Q8_I), (C[8], [0, 2, 4, 6]), (S3, [0, 2, 4])):
        width = cyclotomic_polynomial(4)["degree"]
        trivial = [(1,) + (0,) * (width - 1)] * len(sub)
        induced = induced_representation(tbl, sub, trivial, 4)
        reps = induced["coset_representatives"]
        n = len(tbl)
        inv = [next(y for y in range(n)
                    if tbl[x][y] == 0 and tbl[y][x] == 0) for x in range(n)]
        members = set(sub)
        action = [[next(i for i, s in enumerate(reps)
                        if tbl[inv[s]][tbl[g][t]] in members)
                   for t in reps] for g in range(n)]
        perm = permutation_representation(tbl, action)
        lifted = [[[((v, 1),) + ((0, 1),) * (width - 1) for v in row]
                   for row in mat] for mat in perm["matrices"]]
        assert [[[tuple(c) for c in row] for row in mat]
                for mat in induced["matrices"]] == lifted


def test_g15_the_producer_laws_are_each_reachable_and_named():
    """Every guard the producer states, executed."""
    with pytest.raises(ValueError, match="cyclotomic-conductor law"):
        induced_representation(Q8, Q8_I, Q8_CHI, 2)
    with pytest.raises(ValueError, match="cyclotomic-conductor law"):
        induced_representation(Q8, Q8_I, Q8_CHI, True)

    with pytest.raises(ValueError, match="subgroup law"):
        induced_representation(Q8, [0, 1, 2], Q8_CHI[:3], 4)     # not closed
    with pytest.raises(ValueError, match="subgroup law"):
        induced_representation(Q8, [1, 4, 5], Q8_CHI[:3], 4)     # no identity
    with pytest.raises(ValueError, match="subgroup law"):
        induced_representation(Q8, [0, 0, 1, 4, 5], Q8_CHI + [(1, 0)], 4)
    with pytest.raises(ValueError, match="subgroup law"):
        induced_representation(Q8, [0, 99], [(1, 0), (1, 0)], 4)

    with pytest.raises(ValueError, match="element-count law"):
        induced_representation(Q8, Q8_I, Q8_CHI[:3], 4)
    with pytest.raises(ValueError, match="carrier-width law"):
        induced_representation(Q8, Q8_I, [(1, 0, 0)] * 4, 4)
    with pytest.raises(ValueError, match="plain-int law"):
        induced_representation(
            Q8, Q8_I, [(Q(1, 1), 0)] + list(Q8_CHI[1:]), 4)
    with pytest.raises(ValueError, match="plain-int law"):
        induced_representation(Q8, Q8_I, [(True, 0)] + list(Q8_CHI[1:]), 4)

    with pytest.raises(ValueError, match="unital law"):
        induced_representation(Q8, Q8_I, [(0, 1)] + list(Q8_CHI[1:]), 4)
    with pytest.raises(ValueError, match="character-homomorphism law"):
        # χ(i) = ζ₄ but χ(−1) forced to +1: no longer a homomorphism.
        broken = list(Q8_CHI)
        broken[Q8_I.index(4)] = (1, 0)
        induced_representation(Q8, Q8_I, broken, 4)


def test_g16_the_producer_output_passes_the_widened_checker():
    """Never trusted by construction (the ⊗/⊕ precedent).  Stated here as
    an independent re-validation so a future change to the builder that
    stopped calling the validator would still be caught."""
    for rep in (_q8_rep(), _c4_rep()):
        _check_rep_payload("probe", rep)
        assert rep["cayley_sha256"] == sha256_bytes(_table_bytes(
            [list(r) for r in (Q8 if rep["order"] == 8 else C[4])]))
        assert rep["matrices_sha256"] == sha256_bytes(
            _rep_matrices_bytes("cyclotomic", rep["matrices"], rep["e"]))


# ── G17–G20 the four widened consumers ───────────────────────────────────


def test_g17_the_scalar_contraction_would_have_been_SILENTLY_wrong():
    """The measured trap, executed rather than described.

    ``decompose_representation``'s ℚ path computes ``sizes[j] *
    character[j]``.  On a ζ-vector character that is not a type error —
    Python REPEATS the tuple, raises nothing, and the wrong object dies
    two lines later on a shape that no longer names its cause.  This test
    exists so the branch that avoids it can never be "simplified" away."""
    assert 2 * (1, 0) == (1, 0, 1, 0)
    assert len(2 * (1, 0)) != 2

    rep = _c4_rep()
    ct = character_table(C[4])
    character = character_of(rep, ct)["character"]
    sizes = ct["class_sizes"]
    assert all(isinstance(v, tuple) for v in character)
    assert len(sizes[1] * character[1]) == len(character[1]) * sizes[1]


def test_g18_decompose_reads_the_zeta_lane_by_a_ring_product():
    """Both witnesses decompose to an irreducible, and the dimension law
    ``Σ m_i·d_i == degree`` holds on each."""
    for rep, tbl in ((_q8_rep(), Q8), (_c4_rep(), C[4])):
        ct = character_table(tbl)
        out = decompose_representation(rep, ct)
        assert out["norm"] == 1 and out["is_irreducible"] is True
        assert sum(m for m in out["multiplicities"]) == 1
        assert sum(m * d for m, d in zip(out["multiplicities"],
                                         ct["degrees"])) == rep["degree"]
        # located by CONTENT, never by index
        hit = [i for i, m in enumerate(out["multiplicities"]) if m]
        assert len(hit) == 1
        assert ct["degrees"][hit[0]] == rep["degree"]


def test_g19_isotypic_projector_is_idempotent_orthogonal_equivariant():
    """The in-op completeness and trace laws already ran (they are raises).
    This is the SECOND route the docstring promises, on the ζ lane:
    ``P_i·P_i == D·P_i``, ``P_i·P_j == 0`` and ``P_i·rho(g) ==
    rho(g)·P_i``, contracted through the shipped ring kernel."""
    rep = _q8_rep()
    ct = character_table(Q8)
    out = isotypic_projector(rep, ct)
    phi = list(ct["phi_e"])
    width = ct["degree"]
    d = out["degree"]
    denominator = out["denominator"]
    assert denominator == 8            # |G| * lcm(entry denominators) = 8*1

    def matmul(a, b):
        result = []
        for r in range(d):
            row = []
            for c in range(d):
                acc = [0] * width
                for k in range(d):
                    got = _zeta_mul(a[r][k], b[k][c], phi)
                    for t in range(width):
                        acc[t] += got[t]
                row.append(tuple(acc))
            result.append(row)
        return result

    rho = [[[tuple(coord[0] for coord in cell) for cell in row]
            for row in mat] for mat in rep["matrices"]]
    projectors = [[[tuple(cell) for cell in row] for row in proj]
                  for proj in out["projectors"]]

    idempotent = orthogonal = equivariant = 0
    for i, p_i in enumerate(projectors):
        scaled = [[tuple(denominator * x for x in cell) for cell in row]
                  for row in p_i]
        idempotent += matmul(p_i, p_i) == scaled
        for j, p_j in enumerate(projectors):
            if i != j:
                zero = matmul(p_i, p_j)
                orthogonal += all(all(x == 0 for x in cell)
                                  for row in zero for cell in row)
        for g in range(rep["order"]):
            equivariant += matmul(p_i, rho[g]) == matmul(rho[g], p_i)
    k = out["k"]
    assert (idempotent, orthogonal, equivariant) == (k, k * (k - 1),
                                                     k * rep["order"])


def test_g20_the_compatible_ring_law_is_reachable_with_a_VALID_payload():
    """The group bind proves ONE GROUP and says nothing about the ring, and
    a width check separates nothing (``φ(3) == φ(4) == φ(6) == 2``).  The
    payload below PASSES the widened checker and is then refused."""
    c6 = [list(r) for r in C[6]]
    matrices = [[[((1, 1), (0, 1))]] for _ in range(6)]
    trivial_in_the_wrong_ring = {
        "order": 6, "degree": 1, "field": "Q(zeta_4)", "kind": "cyclotomic",
        "e": 4, "phi_e": tuple(cyclotomic_polynomial(4)["coefficients"]),
        "matrices": matrices,
        "cayley_sha256": sha256_bytes(_table_bytes(c6)),
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("cyclotomic", matrices, 4)),
    }
    _check_rep_payload("probe", trivial_in_the_wrong_ring)   # ACCEPTED
    ct = character_table(C[6])
    assert ct["exponent"] == 6 and len(ct["phi_e"]) - 1 == 2
    with pytest.raises(ValueError, match="compatible-ring law"):
        character_of(trivial_in_the_wrong_ring, ct)
    with pytest.raises(ValueError, match="compatible-ring law"):
        decompose_representation(trivial_in_the_wrong_ring, ct)
    with pytest.raises(ValueError, match="compatible-ring law"):
        isotypic_projector(trivial_in_the_wrong_ring, ct)


# ── G21–G22 the three refusals ───────────────────────────────────────────


@pytest.mark.parametrize("op,law", [
    (tensor_product_representation, "dialect law"),
    (direct_sum_representation, "dialect law"),
    (intertwiner_space, "carrier law"),
])
def test_g21_the_three_unwidened_consumers_refuse_with_a_named_law(op, law):
    """Each refusal is proved REACHABLE: the operand PASSES the widened
    checker first, so the raise is this op's own decision and not a
    validator rejection wearing its name."""
    rep = _q8_rep()
    _check_rep_payload("probe", rep)
    with pytest.raises(ValueError, match=law):
        op(rep, rep)


@pytest.mark.parametrize("op,law", [
    (tensor_product_representation, "dialect law"),
    (direct_sum_representation, "dialect law"),
    (intertwiner_space, "carrier law"),
])
def test_g22_a_mixed_pair_is_refused_though_the_same_group_law_passes(op, law):
    """``_same_group_guard`` does NOT discriminate the dialect — a ℚ
    payload and a ζ payload of the same group carry EQUAL
    ``cayley_sha256``, so a mixed pair sails through the same-group law
    and would die in the arithmetic.  Measured, then refused."""
    zeta = _q8_rep()
    rational = permutation_representation(Q8, Q8)
    assert zeta["cayley_sha256"] == rational["cayley_sha256"]
    assert zeta["order"] == rational["order"]
    with pytest.raises(ValueError, match=law):
        op(rational, zeta)
    with pytest.raises(ValueError, match=law):
        op(zeta, rational)


def test_g23_the_widened_consumers_still_answer_the_rational_lane():
    """The widening is ADDITIVE: the three ops that refuse ζ still do their
    ℚ work, and the four that read ζ still read ℚ identically."""
    nat = permutation_representation(
        S3, [[(a + (x if h == 0 else -x)) % 3 for x in range(3)]
             for a in range(3) for h in range(2)])
    ct = character_table(S3)
    assert character_of(nat, ct)["character"] == (3, 1, 0)
    out = decompose_representation(nat, ct)
    # ⚠️ located by CONTENT, never by index: payload rows sort (degree,
    # lex), so the trivial character is NOT at index 0.
    assert sorted(out["multiplicities"]) == [0, 1, 1]
    assert sum(m * d for m, d in zip(out["multiplicities"],
                                     ct["degrees"])) == 3
    assert [ct["degrees"][i]
            for i, m in enumerate(out["multiplicities"]) if m] == [1, 2]
    assert intertwiner_space(nat, nat)["dimension"] == 2
    assert tensor_product_representation(nat, nat)["degree"] == 9
    assert direct_sum_representation(nat, nat)["degree"] == 6
    assert isotypic_projector(nat, ct)["denominator"] == 6


# ── G24–G26 the Galois action ────────────────────────────────────────────


def test_g24_sigma_three_swaps_the_conjugate_pair_and_is_an_involution():
    """The executable form of "it swaps 3 and 3̄".  ⚠️ NOT executable at
    ``e = 4`` in its literal 3-dimensional form — no shipped group has a
    conjugate pair of 3-dimensional irreps over ℚ(ζ₄) — so the degree-1
    C4 swap IS the measurement."""
    rep = _c4_rep()
    ct = character_table(C[4])
    twisted = zeta_conjugate(rep, 3)

    before = decompose_representation(rep, ct)["multiplicities"]
    after = decompose_representation(twisted, ct)["multiplicities"]
    assert sorted(before) == sorted(after)
    assert before != after
    moved = [i for i in range(len(before)) if before[i] != after[i]]
    assert len(moved) == 2
    indicators = frobenius_schur_indicator(ct)["indicators"]
    assert all(indicators[i] == 0 for i in moved)   # the COMPLEX pair

    back = zeta_conjugate(twisted, 3)
    assert back["matrices_sha256"] == rep["matrices_sha256"]
    assert back["matrices"] == rep["matrices"]


def test_g25_the_commuting_square_holds_by_content_address():
    """``zeta_conjugate(Ind χ, t) == Ind(σ_t ∘ χ)``.  The right-hand side
    conjugates the INPUT character (at ``e = 4``, ``σ₃`` negates the ζ
    coordinate) and induces; the left conjugates the induced rep.  Equal
    as objects, compared by the Class-A address."""
    conjugated = [(a, -b) for a, b in C4_CHI]
    right = induced_representation(C[4], [0, 1, 2, 3], conjugated, 4)
    left = zeta_conjugate(_c4_rep(), 3)
    assert left["matrices_sha256"] == right["matrices_sha256"]
    assert left["matrices"] == right["matrices"]

    # and on the DEGREE-2 witness, where the square is a real matrix claim
    q8_conjugated = [(a, -b) for a, b in Q8_CHI]
    assert (zeta_conjugate(_q8_rep(), 3)["matrices_sha256"]
            == induced_representation(
                Q8, Q8_I, q8_conjugated, 4)["matrices_sha256"])


def test_g26_the_galois_laws_are_each_reachable_and_named():
    """A non-unit exponent names no automorphism; a ℚ payload has no twist
    to take; a payload whose modulus is not the TRUE ``Φ_e`` would build a
    wrong power table and answer silently, so it is refused."""
    rep = _q8_rep()
    for bad_t in (0, 2, 4, 6):
        with pytest.raises(ValueError, match="Galois law"):
            zeta_conjugate(rep, bad_t)
    with pytest.raises(ValueError, match="Galois law"):
        zeta_conjugate(rep, True)
    # t and t + e name ONE automorphism
    assert (zeta_conjugate(rep, 7)["matrices_sha256"]
            == zeta_conjugate(rep, 3)["matrices_sha256"])
    assert (zeta_conjugate(rep, -1)["matrices_sha256"]
            == zeta_conjugate(rep, 3)["matrices_sha256"])

    with pytest.raises(ValueError, match="dialect law"):
        zeta_conjugate(permutation_representation(C[3], C[3]), 2)

    liar = copy.deepcopy(rep)
    liar["phi_e"] = (1, 1, 1)          # monic, degree 2, and NOT Phi_4
    with pytest.raises(ValueError, match="cyclotomic-modulus law"):
        zeta_conjugate(liar, 3)


def test_g27_conjugation_over_a_deeper_ring_permutes_the_characters():
    """``e = 4`` is the shallow case where σ₃ looks like "negate the
    imaginary part".  At ``e = 5`` the power basis is NOT closed under a
    sign flip, so this is the case that would catch a hand-rolled
    conjugation — the Galois group is cyclic of order 4 and its orbit on
    the faithful character of C5 has length 4."""
    powers = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1),
              (-1, -1, -1, -1))
    chi = _faithful_character(C[5], [0, 1, 2, 3, 4], 1, powers)
    rep = induced_representation(C[5], [0, 1, 2, 3, 4], chi, 5)
    ct = character_table(C[5])
    orbit = {rep["matrices_sha256"]}
    seen = [decompose_representation(rep, ct)["multiplicities"]]
    for t in (2, 3, 4):
        twisted = zeta_conjugate(rep, t)
        orbit.add(twisted["matrices_sha256"])
        seen.append(decompose_representation(twisted, ct)["multiplicities"])
    assert len(orbit) == 4
    assert len({tuple(m) for m in seen}) == 4
    assert all(sum(m) == 1 for m in seen)
    # the naive "negate the imaginary coordinate" is NOT the conjugate here
    naive = tuple((-c[0], c[1]) if j else c
                  for j, c in enumerate(rep["matrices"][1][0][0]))
    assert naive != zeta_conjugate(rep, 4)["matrices"][1][0][0]


# ── G28 the payload-leak walk ────────────────────────────────────────────


def _walk(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)
    else:
        yield value


#: Matched BY NAME rather than by ``isinstance`` — importing ``fractions``
#: here to name it is itself the strict-zero violation
#: ``tests/test_selfhosting_import_ban.py`` forbids, and naming is strictly
#: WIDER: it catches srmech's OWN ``Q`` / ``Qalg`` / ``QMat`` leaking.
RATIONAL_CARRIER_NAMES = ("Fraction", "Q", "Qalg", "QMat")


def test_g28_no_float_and_no_rational_carrier_reaches_a_zeta_payload():
    """rc461's named enforcer is scoped to six hard-coded ``weight_lattice``
    payloads and will NEVER see a ``groups.py`` producer, so the constraint
    would ship unenforced on this surface without a peer walk.  This is
    that peer walk."""
    ct = character_table(Q8)
    ct4 = character_table(C[4])
    payloads = [
        _q8_rep(), _c4_rep(), zeta_conjugate(_c4_rep(), 3),
        character_of(_q8_rep(), ct), character_of(_c4_rep(), ct4),
        decompose_representation(_q8_rep(), ct),
        isotypic_projector(_q8_rep(), ct),
    ]
    visited = 0
    for payload in payloads:
        for item in _walk(payload):
            visited += 1
            assert not isinstance(item, float), item
            assert type(item).__name__ not in RATIONAL_CARRIER_NAMES, item

    # CONTROL, both ways: a green above would otherwise only mean the
    # walker found nothing to judge.
    assert type(Q(1, 1)).__name__ in RATIONAL_CARRIER_NAMES
    assert type(Qalg([1, 0, 1], [Q(1, 1), Q(0, 1)])).__name__ \
        in RATIONAL_CARRIER_NAMES
    assert type(1).__name__ not in RATIONAL_CARRIER_NAMES
    assert visited > 0


# ── G29 the surface is reachable through the shipped introspect ──────────


def test_g29_both_new_ops_are_public_and_registered():
    """An op the registry cannot see is an op no consumer can find, and a
    ``composes`` target that is not registered reds the resolvability
    gate."""
    from srmech.introspect.tool_schema import get_tool_schema
    import srmech.math.groups as groups

    names = {t.name: t for t in get_tool_schema().tools}
    for short in ("induced_representation", "zeta_conjugate"):
        assert short in groups.__all__
        full = "srmech.math.groups." + short
        assert full in names
        entry = names[full]
        assert entry.owner == "srmech" and entry.category == "groups"
        for target in entry.composes:
            assert target in names, target
