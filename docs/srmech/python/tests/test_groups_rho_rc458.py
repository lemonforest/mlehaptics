"""rc458 — the representation stratum, tier 4 (``srmech.math.groups``):
the rho stratum.  ``zeta_mul`` + ``permutation_representation`` +
``character_of`` + ``decompose_representation`` + ``isotypic_projector`` +
``tensor_product_representation`` + ``direct_sum_representation`` +
``intertwiner_space``, plus the ``QMat`` carrier methods ``trace`` /
``kron`` / ``__pow__`` they ride.

Every oracle below is a hand-derived exact value, a mathematical identity,
or a cross-check between two shipped ops / two independent routes.  NO
sympy anywhere; NO floats anywhere; NO bools stored as counts.  **Every
test locates character-table rows by CONTENT (degree + value vector),
never by index** — measured trap: the trivial character sits at index 1 in
S3's payload and index 2 in C7⋊C3's.

PRESERVES-CLAIM → EXECUTING-TEST MAP (the property-gate discipline: no
ToolEntry ``preserves`` claim ships without its executor)
=========================================================================
  claim (all eight tier-4 ToolEntries carry the same one):
    "numpy-free; no abs() — sign-handling stays Class-K pin-slot + Class-C"
  executors:
    - test_no_alu_magnitude_and_no_float_in_the_source
      (tests/test_groups_representation_rc456.py — scans the WHOLE module
      source, so the tier-4 additions are covered automatically), and
    - test_qmat_pow_sign_branch_is_pin_slot_not_magnitude (below — the
      Class-K exponent pin is executed on both orientations).
  numpy-free is executed by the suite running in the numpy-ABSENT CI cell.
"""
from __future__ import annotations

import copy
import itertools

import pytest

from srmech.cascade import dihedral_group, unit_loop
from srmech.math.groups import (_zeta_mul, _zeta_power_table,
                                central_idempotents, character_of,
                                character_table, cyclic_group,
                                decompose_representation,
                                direct_sum_representation,
                                fusion_multiplicities, intertwiner_space,
                                isotypic_projector,
                                permutation_representation,
                                semidirect_product,
                                tensor_product_representation, zeta_mul)
from srmech.math.q import Q
from srmech.math.qmat import QMat

# ── shared fixtures (rc456/rc457 construction idioms) ─────────────────────

C2 = cyclic_group(2)["cayley_table"]
C3 = cyclic_group(3)["cayley_table"]
C4 = cyclic_group(4)["cayley_table"]
C6 = cyclic_group(6)["cayley_table"]
C7 = cyclic_group(7)["cayley_table"]

D4 = dihedral_group(4, "rotation_first")["cayley_table"]
Q8 = unit_loop(4)["cayley_table"]

S3 = semidirect_product(C3, C2, [[0, 1, 2], [0, 2, 1]])["cayley_table"]

#: F21 = C7 ⋊ C3, mult-by-2 action — the deep-ring lane (Φ₂₁, φ(21) = 12).
F21 = semidirect_product(
    C7, C3,
    [[(a * pow(2, h, 7)) % 7 for a in range(7)] for h in range(3)]
)["cayley_table"]


def _q16_table():
    """Q16, the generalized quaternion group of order 16 — rc457 named it
    a candidate for THIS promotion rc's test budget.  Built from the
    presentation ⟨a, b | a⁸ = 1, b² = a⁴, b·a = a⁻¹·b⟩ with element index
    ``idx(i, j) = i·2 + j`` for ``a^i b^j``; the construction is then
    VALIDATED as a group by permutation_representation's own operand-group
    guards (associativity + identity + inverses), so a bad table cannot
    silently seed the fixture."""
    def mul(x, y):
        i, j = divmod(x, 2)
        k, l = divmod(y, 2)
        if j == 0:
            return ((i + k) % 8) * 2 + l
        # a^i b a^k b^l = a^(i-k) b^(1+l); b^2 = a^4
        if l == 0:
            return ((i - k) % 8) * 2 + 1
        return ((i - k + 4) % 8) * 2
    return [[mul(x, y) for y in range(16)] for x in range(16)]


Q16 = _q16_table()

_CT_CACHE = {}


def _ct(name, table):
    if name not in _CT_CACHE:
        _CT_CACHE[name] = character_table(table)
    return _CT_CACHE[name]


def _nat_action():
    """The natural 3-point S3 action: idx(a, h) sends x ↦ a + (−1)^h·x."""
    return [[(a + (x if h == 0 else -x)) % 3 for x in range(3)]
            for a in range(3) for h in range(2)]


def _one(ct):
    return (1,) + (0,) * (ct["degree"] - 1)


def _trivial_row(ct):
    """The unique row whose every value is (1, 0, …, 0) — CONTENT, never
    index."""
    hits = [i for i in range(ct["k"])
            if all(tuple(ct["table"][i][j]) == _one(ct)
                   for j in range(ct["k"]))]
    assert len(hits) == 1
    return hits[0]


def _identity_col(ct):
    """The unique identity-class column — CONTENT, never index."""
    deg = ct["degree"]
    hits = [j for j in range(ct["k"])
            if all(tuple(ct["table"][i][j]) ==
                   (ct["degrees"][i],) + (0,) * (deg - 1)
                   for i in range(ct["k"]))]
    assert len(hits) == 1
    return hits[0]


# ══════════════════════════════════════════════════════════════════════
# zeta_mul — the public promotion of the private ring kernel
# ══════════════════════════════════════════════════════════════════════

PHI12 = (1, 0, -1, 0, 1)          # Φ₁₂, low→high


def test_zeta_mul_worked_example_i_times_i():
    assert zeta_mul((0, 1), (0, 1), (1, 0, 1)) == (-1, 0)


def test_zeta_mul_public_op_is_the_shipped_kernel_byte_identical():
    """The public op and the private kernel every tier-2/3 contraction
    rides must agree byte-identically — the promotion moved a NAME, not a
    value (the fusion regression, executed at the kernel grain)."""
    vectors = [(1, 2, 0, -1), (0, 3, -2, 5), (7, 0, 1, 1), (0, 0, 0, 0)]
    for u in vectors:
        for v in vectors:
            assert zeta_mul(u, v, PHI12) == _zeta_mul(u, v, PHI12)


def test_zeta_mul_ring_laws_executed():
    a, b, c = (1, 2, 0, -1), (0, 3, -2, 5), (7, 0, 1, 1)
    assert zeta_mul(a, b, PHI12) == zeta_mul(b, a, PHI12)
    assert (zeta_mul(zeta_mul(a, b, PHI12), c, PHI12)
            == zeta_mul(a, zeta_mul(b, c, PHI12), PHI12))
    apc = tuple(x + y for x, y in zip(a, c))
    ab = zeta_mul(a, b, PHI12)
    cb = zeta_mul(c, b, PHI12)
    assert zeta_mul(apc, b, PHI12) == tuple(x + y for x, y in zip(ab, cb))


def test_zeta_mul_against_qalg_co_equal_dual_route():
    """Co-equal dual construction as a consistency oracle: the shipped
    ``Qalg`` field arithmetic is an INDEPENDENT code path (polynomial
    arithmetic over Q, not integer convolution) — a disagreement would be
    a finding, and there is none."""
    from srmech.math.qalg import Qalg
    u, v = (2, -1, 3, 0), (1, 1, 0, -2)
    got = zeta_mul(u, v, PHI12)
    prod = Qalg(list(PHI12), list(u)) * Qalg(list(PHI12), list(v))
    pairs = [q.as_pair() for q in prod._coords]
    assert all(den == 1 for _num, den in pairs)
    assert tuple(num for num, _den in pairs) == got


def test_zeta_mul_zeta_power_table_cross_check():
    """ζ_e · ζ_e^{e−1} == 1, the power table built by the SHIPPED
    ``_zeta_power_table`` (a second independent reduction route)."""
    for e, phi in ((7, (1, 1, 1, 1, 1, 1, 1)), (12, PHI12)):
        table = _zeta_power_table(list(phi), e)
        assert zeta_mul(table[1], table[e - 1], phi) == table[0]
        assert table[0] == (1,) + (0,) * (len(phi) - 2)


@pytest.mark.parametrize("bad", [True, "1", None])
def test_zeta_mul_plain_int_law_rejects_contaminants(bad):
    with pytest.raises((ValueError, TypeError), match="plain-int law"):
        zeta_mul((0, bad), (0, 1), (1, 0, 1))
    with pytest.raises((ValueError, TypeError), match="plain-int law"):
        zeta_mul((0, 1), (bad,), (1, 0, 1))
    with pytest.raises((ValueError, TypeError), match="plain-int law"):
        zeta_mul((0, 1), (0, 1), (1, bad, 1))


def test_zeta_mul_monic_modulus_law():
    with pytest.raises(ValueError, match="monic-modulus law"):
        zeta_mul((0, 1), (0, 1), (1, 0, 2))
    with pytest.raises(ValueError, match="monic-modulus law"):
        zeta_mul((0, 1), (0, 1), (1,))


# ══════════════════════════════════════════════════════════════════════
# permutation_representation — the constructor
# ══════════════════════════════════════════════════════════════════════

def _matmul_int(A, B):
    n = len(A)
    return [[sum(A[i][t] * B[t][j] for t in range(n)) for j in range(n)]
            for i in range(n)]


def test_homomorphism_law_all_pairs_s3():
    """ρ(g·h) == ρ(g)·ρ(h) over ALL 36 pairs, executed on the matrices
    themselves — the payload's construction-time law re-derived from the
    minted object."""
    reg = permutation_representation(S3, S3)
    for g, h in itertools.product(range(6), repeat=2):
        assert (reg["matrices"][S3[g][h]]
                == _matmul_int(reg["matrices"][g], reg["matrices"][h]))


def test_identity_matrix_and_one_per_row_and_column():
    nat = permutation_representation(S3, _nat_action())
    eye = [[1 if i == j else 0 for j in range(3)] for i in range(3)]
    assert nat["matrices"][0] == eye          # idx(0,0) is the identity
    for mat in nat["matrices"]:
        for row in mat:
            assert sum(row) == 1
        for c in range(3):
            assert sum(mat[r][c] for r in range(3)) == 1


def test_regular_representation_is_the_table_acting_on_itself():
    reg = permutation_representation(Q8, Q8)
    assert reg["order"] == reg["degree"] == 8
    assert reg["action"] == [list(r) for r in Q8]


def test_corrupted_action_raises_naming_the_law():
    bad = _nat_action()
    bad[3][0] = bad[3][1]
    with pytest.raises(ValueError, match="bijection law"):
        permutation_representation(S3, bad)
    skew = _nat_action()
    skew[3], skew[4] = skew[4], skew[3]       # break the left-action law
    with pytest.raises(ValueError, match="left-action law"):
        permutation_representation(S3, skew)
    with pytest.raises(ValueError, match="operand-group law"):
        permutation_representation([[0, 1], [1, 1]], [[0, 1], [1, 0]])


# ══════════════════════════════════════════════════════════════════════
# character_of — the bridge back, the free consistency oracle
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("name,table", [
    ("S3", S3), ("C4", C4), ("D4", D4), ("Q8", Q8), ("F21", F21),
])
def test_regular_character_is_order_at_identity_zero_elsewhere(name, table):
    ct = _ct(name, table)
    reg = permutation_representation(table, table)
    chi = character_of(reg, ct)["character"]
    identity = _identity_col(ct)
    for j in range(ct["k"]):
        assert chi[j] == (ct["order"] if j == identity else 0)


def test_natural_character_is_fixed_point_count_two_routes():
    """Trace route (character_of) vs matrix-free fixed-point count off the
    action — two routes to the same class function."""
    ct = _ct("S3", S3)
    action = _nat_action()
    nat = permutation_representation(S3, action)
    chi = character_of(nat, ct)["character"]
    by_class = {}
    for g in range(6):
        fixed = sum(1 for x in range(3) if action[g][x] == x)
        j = ct["class_of"][g]
        assert by_class.setdefault(j, fixed) == fixed
    assert tuple(by_class[j] for j in range(ct["k"])) == chi
    assert sorted(chi) == [0, 1, 3]


def test_character_content_matches_the_shipped_table_rows():
    """χ_nat lifted to ζ-vectors equals Σ_i m_i · table[i] cell-for-cell —
    the rep-side character meeting the shipped table's own rows."""
    ct = _ct("S3", S3)
    nat = permutation_representation(S3, _nat_action())
    chi = character_of(nat, ct)["character"]
    m = decompose_representation(nat, ct)["multiplicities"]
    deg = ct["degree"]
    for j in range(ct["k"]):
        acc = [0] * deg
        for i in range(ct["k"]):
            for t in range(deg):
                acc[t] += m[i] * ct["table"][i][j][t]
        assert tuple(acc) == (chi[j],) + (0,) * (deg - 1)


def test_class_constancy_negative_control():
    """A tampered class partition that merges a transposition into a
    3-cycle class must trip the class-constancy law — the honest
    same-group mismatch DETECTOR, firing on the exact quantity it
    watches (unequal traces inside one claimed class)."""
    ct = copy.deepcopy(_ct("S3", S3))
    nat = permutation_representation(S3, _nat_action())
    chi = character_of(nat, ct)["character"]
    # find one element from a class with trace 0 and one with trace 1
    donor = next(g for g in range(6) if chi[ct["class_of"][g]] == 1)
    target = next(g for g in range(6) if chi[ct["class_of"][g]] == 0)
    ct["class_of"] = list(ct["class_of"])
    ct["class_of"][donor] = ct["class_of"][target]
    with pytest.raises(ValueError, match="class-constancy law"):
        character_of(nat, ct)


def test_order_law_raises_on_different_orders():
    ct = _ct("S3", S3)
    rep = permutation_representation(C4, C4)
    with pytest.raises(ValueError, match="order law"):
        character_of(rep, ct)


# ══════════════════════════════════════════════════════════════════════
# decompose_representation — the fusion-slot projection
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("name,table", [
    ("S3", S3), ("C4", C4), ("D4", D4), ("Q8", Q8), ("F21", F21),
    ("Q16", Q16),
])
def test_regular_rep_theorem_m_i_equals_d_i(name, table):
    """The regular representation decomposes with every multiplicity equal
    to its irrep's degree — including Q16, the generalized-quaternion
    fixture rc457 deferred to this rc's budget."""
    ct = _ct(name, table)
    reg = permutation_representation(table, table)
    dec = decompose_representation(reg, ct)
    assert list(dec["multiplicities"]) == list(ct["degrees"])
    assert dec["norm"] == sum(d * d for d in ct["degrees"])
    assert dec["is_irreducible"] is False


def test_burnside_trivial_multiplicity_is_the_orbit_count():
    ct = _ct("S3", S3)
    nat = permutation_representation(S3, _nat_action())
    dec = decompose_representation(nat, ct)
    assert dec["multiplicities"][_trivial_row(ct)] == 1   # one orbit
    assert sum(m * d for m, d in zip(dec["multiplicities"],
                                     ct["degrees"])) == 3
    assert dec["norm"] == 2
    assert dec["is_irreducible"] is False


def test_decompose_corruption_negative_control():
    """A tampered table cell produces a payload the shared validator
    cannot see (character values are not validated) — the in-op
    divisibility / non-scalar guards are the detectors, and one of them
    must fire."""
    ct = copy.deepcopy(_ct("S3", S3))
    nat = permutation_representation(S3, _nat_action())
    row = _trivial_row(ct)
    col = (_identity_col(ct) + 1) % ct["k"]   # NOT the identity column —
    # tampering that one trips the identity-location law first, which is
    # a different (also live) guard than the one under test here
    cell = list(ct["table"][row][col])
    cell[0] += 1
    ct["table"][row][col] = tuple(cell)
    with pytest.raises(ValueError,
                       match="divisibility law|non-scalar-sum law"):
        decompose_representation(nat, ct)


def test_is_irreducible_is_a_bool_field_not_an_int():
    ct = _ct("S3", S3)
    nat = permutation_representation(S3, _nat_action())
    dec = decompose_representation(nat, ct)
    assert isinstance(dec["is_irreducible"], bool)
    for m in dec["multiplicities"]:
        assert isinstance(m, int) and not isinstance(m, bool)


# ══════════════════════════════════════════════════════════════════════
# isotypic_projector — the op rc457 declined, two independent routes
# ══════════════════════════════════════════════════════════════════════

def _zmatmul(P1, P2, phi, deg_ring):
    """ζ-vector matrix product — route (i)'s contraction, riding the
    SHIPPED public zeta_mul (independent of the op's internal class-sum
    grouping)."""
    n = len(P1)
    out = []
    for r in range(n):
        row = []
        for c in range(n):
            acc = [0] * deg_ring
            for t in range(n):
                prod = zeta_mul(P1[r][t], P2[t][c], phi)
                for x in range(deg_ring):
                    acc[x] += prod[x]
            row.append(tuple(acc))
        out.append(row)
    return out


def _scaled(P, factor):
    return [[tuple(factor * x for x in cell) for cell in row] for row in P]


def _zero_mat(d, deg_ring):
    return [[tuple([0] * deg_ring) for _ in range(d)] for _ in range(d)]


@pytest.mark.parametrize("name,table", [("S3", S3), ("Q8", Q8)])
def test_isotypic_idempotence_orthogonality_equivariance(name, table):
    """Route (i): P_i² == denominator·P_i, P_iP_j == 0, and equivariance
    P_i·ρ(g) == ρ(g)·P_i for every g — executed with the public zeta_mul
    contraction."""
    ct = _ct(name, table)
    reg = permutation_representation(table, table)
    iso = isotypic_projector(reg, ct)
    phi, deg_ring = list(ct["phi_e"]), ct["degree"]
    den, d, k = iso["denominator"], iso["degree"], iso["k"]
    projectors = [[list(row) for row in P] for P in iso["projectors"]]
    for i in range(k):
        assert (_zmatmul(projectors[i], projectors[i], phi, deg_ring)
                == _scaled(projectors[i], den))
    for i in range(k):
        for j in range(i + 1, k):
            assert (_zmatmul(projectors[i], projectors[j], phi, deg_ring)
                    == _zero_mat(d, deg_ring))
    lift = lambda M: [[(v,) + (0,) * (deg_ring - 1) for v in row]
                      for row in M]
    for i in range(k):
        for g in range(iso["order"]):
            R = lift(reg["matrices"][g])
            assert (_zmatmul(projectors[i], R, phi, deg_ring)
                    == _zmatmul(R, projectors[i], phi, deg_ring))


@pytest.mark.parametrize("name,table", [("S3", S3), ("Q8", Q8)])
def test_isotypic_cross_op_route_equals_central_idempotents(name, table):
    """Route (ii): on the REGULAR representation the projector family must
    equal central_idempotents' numerators expanded per element via
    class_of — the shipped universal element meeting the evaluation its
    own docstring promised.  A disagreement between the two routes is a
    finding; there is none."""
    ct = _ct(name, table)
    reg = permutation_representation(table, table)
    iso = isotypic_projector(reg, ct)
    ci = central_idempotents(ct)
    assert iso["denominator"] == ci["denominator"]
    deg_ring = ct["degree"]
    n = ct["order"]
    for i in range(ct["k"]):
        expect = []
        for r in range(n):
            row = []
            for c in range(n):
                acc = [0] * deg_ring
                for g in range(n):
                    if reg["matrices"][g][r][c]:
                        vec = ci["numerators"][i][ct["class_of"][g]]
                        for t in range(deg_ring):
                            acc[t] += vec[t]
                row.append(tuple(acc))
            expect.append(tuple(row))
        assert tuple(expect) == iso["projectors"][i]


def test_isotypic_trace_law_cross_read_vs_decompose():
    ct = _ct("F21", F21)
    reg = permutation_representation(F21, F21)
    iso = isotypic_projector(reg, ct)
    dec = decompose_representation(reg, ct)
    assert iso["multiplicities"] == dec["multiplicities"]
    deg_ring = ct["degree"]
    for i in range(ct["k"]):
        acc = [0] * deg_ring
        for r in range(iso["degree"]):
            for t in range(deg_ring):
                acc[t] += iso["projectors"][i][r][r][t]
        assert acc[0] == (iso["denominator"] * dec["multiplicities"][i]
                          * ct["degrees"][i])
        assert not any(acc[1:])


def _general_sign_plus_trivial():
    """A GENERAL-kind rep with non-trivial entry denominators: sign ⊕
    trivial conjugated by S = [[1/2, 1/3], [0, 1]] — exact, exercises the
    |G|·L denominator derivation (the R5 silent-wrong-answer lane)."""
    reg = permutation_representation(S3, S3)
    from srmech.math.groups import _rep_matrices_bytes
    from srmech.amsc.format import sha256_bytes
    S = QMat.from_rows([[(1, 2), (1, 3)], [0, 1]])
    Sinv = S.inverse()
    mats = []
    for idx in range(6):
        sign = (1, 1) if idx % 2 == 0 else (-1, 1)
        D = QMat.from_rows([[sign, (0, 1)], [(0, 1), (1, 1)]])
        M = S.matmul(D).matmul(Sinv)
        mats.append([[M[r, c].as_pair() for c in range(2)]
                     for r in range(2)])
    return {
        "order": 6, "degree": 2, "field": "Q", "kind": "general",
        "matrices": mats,
        "cayley_sha256": reg["cayley_sha256"],
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("general", mats)),
    }


def test_isotypic_general_kind_denominator_and_idempotence():
    """The general-kind lane: the denominator is |G|·L with L DERIVED from
    the entry denominators, and idempotence holds over the scaled
    numerators — the non-negotiable R5 oracle (a mis-scale produces
    well-formed WRONG integers; the ζ-contraction catches scaling
    exactly)."""
    ct = _ct("S3", S3)
    rep = _general_sign_plus_trivial()
    iso = isotypic_projector(rep, ct)
    assert iso["denominator"] % ct["order"] == 0
    assert iso["denominator"] > ct["order"]        # L > 1: dens engaged
    phi, deg_ring = list(ct["phi_e"]), ct["degree"]
    den = iso["denominator"]
    projectors = [[list(row) for row in P] for P in iso["projectors"]]
    for i in range(ct["k"]):
        assert (_zmatmul(projectors[i], projectors[i], phi, deg_ring)
                == _scaled(projectors[i], den))
    dec = decompose_representation(rep, ct)
    assert sorted(dec["multiplicities"]) == [0, 1, 1]  # sign + trivial


# ══════════════════════════════════════════════════════════════════════
# tensor_product_representation — the rep-level fusion witness
# ══════════════════════════════════════════════════════════════════════

def test_tensor_decompose_matches_the_shipped_fusion_tensor():
    """decompose(ρ_a ⊗ ρ_b) == Σ m_a m_b N_abc against the SHIPPED
    fusion_multiplicities — the bound module meeting the character-level
    tensor it realises."""
    ct = _ct("S3", S3)
    fus = fusion_multiplicities(ct)
    nat = permutation_representation(S3, _nat_action())
    m = decompose_representation(nat, ct)["multiplicities"]
    tp = tensor_product_representation(nat, nat)
    got = decompose_representation(tp, ct)["multiplicities"]
    k = ct["k"]
    predicted = [
        sum(m[a] * m[b] * fus["multiplicities"][a][b][c]
            for a in range(k) for b in range(k))
        for c in range(k)]
    assert list(got) == predicted == [1, 2, 3]


def test_tensor_characters_multiply_pointwise():
    ct = _ct("Q8", Q8)
    reg = permutation_representation(Q8, Q8)
    chi = character_of(reg, ct)["character"]
    tp = tensor_product_representation(reg, reg)
    chi_tp = character_of(tp, ct)["character"]
    assert list(chi_tp) == [a * a for a in chi]


def test_tensor_perm_perm_action_is_revalidated_and_coherent():
    """perm⊗perm output re-passes the constructor-grade payload checks —
    executed here through the ops that consume it, plus the pinned pair
    index (x1, x2) ↦ x1·d2 + x2 checked cell-for-cell against
    QMat.kron."""
    nat = permutation_representation(S3, _nat_action())
    tp = tensor_product_representation(nat, nat)
    assert tp["kind"] == "permutation"
    for g in range(6):
        A = QMat.from_rows(nat["matrices"][g])
        assert QMat.from_rows(tp["matrices"][g]) == A.kron(A)


def test_same_group_law_raises_across_groups():
    rep_s3 = permutation_representation(S3, S3)
    rep_c6 = permutation_representation(C6, C6)
    with pytest.raises(ValueError, match="same-group law"):
        tensor_product_representation(rep_s3, rep_c6)
    with pytest.raises(ValueError, match="same-group law"):
        direct_sum_representation(rep_s3, rep_c6)
    with pytest.raises(ValueError, match="same-group law"):
        intertwiner_space(rep_s3, rep_c6)


# ══════════════════════════════════════════════════════════════════════
# direct_sum_representation — Class B, blocks recoverable
# ══════════════════════════════════════════════════════════════════════

def test_direct_sum_characters_and_multiplicities_add():
    ct = _ct("S3", S3)
    nat = permutation_representation(S3, _nat_action())
    reg = permutation_representation(S3, S3)
    ds = direct_sum_representation(nat, reg)
    chi_n = character_of(nat, ct)["character"]
    chi_r = character_of(reg, ct)["character"]
    assert (list(character_of(ds, ct)["character"])
            == [a + b for a, b in zip(chi_n, chi_r)])
    m_n = decompose_representation(nat, ct)["multiplicities"]
    m_r = decompose_representation(reg, ct)["multiplicities"]
    assert (list(decompose_representation(ds, ct)["multiplicities"])
            == [a + b for a, b in zip(m_n, m_r)])


def test_direct_sum_blocks_are_recoverable():
    """The Class-B (TLV) claim, executed: the leading block is ρ1(g)
    VERBATIM and the trailing block is ρ2(g) VERBATIM, every g."""
    nat = permutation_representation(S3, _nat_action())
    reg = permutation_representation(S3, S3)
    ds = direct_sum_representation(nat, reg)
    assert ds["degree"] == 9
    for g in range(6):
        assert ([row[:3] for row in ds["matrices"][g][:3]]
                == nat["matrices"][g])
        assert ([row[3:] for row in ds["matrices"][g][3:]]
                == reg["matrices"][g])


# ══════════════════════════════════════════════════════════════════════
# intertwiner_space — the Schur readout, two independent routes
# ══════════════════════════════════════════════════════════════════════

def test_intertwiner_dimension_two_routes():
    """dimension == Σ m_i(ρ1)·m_i(ρ2), the QMat rational-nullspace route
    against the cyclotomic decompose route — a disagreement is a
    finding."""
    ct = _ct("S3", S3)
    nat = permutation_representation(S3, _nat_action())
    iw = intertwiner_space(nat, nat)
    m = decompose_representation(nat, ct)["multiplicities"]
    assert iw["dimension"] == sum(x * x for x in m) == 2


def test_intertwiner_basis_equivariance_executed_raw():
    """Every returned basis element re-checked against RAW matrix products
    over Q — the independent route a Kronecker-convention defect inside
    the op could not survive."""
    nat = permutation_representation(S3, _nat_action())
    iw = intertwiner_space(nat, nat)
    for mat in iw["basis"]:
        X = QMat.from_rows([[tuple(c) for c in row] for row in mat])
        for g in range(6):
            R = QMat.from_rows(nat["matrices"][g])
            assert R.matmul(X) == X.matmul(R)


def test_intertwiner_schur_zero_is_a_classified_return():
    """Two inequivalent irreducible constituents → dimension 0 with basis
    [] — a CLASSIFIED verdict, not a failure (an instrument that cannot
    return otherwise is not a measurement)."""
    triv = permutation_representation(S3, [[0]] * 6)
    sign = _general_sign_plus_trivial()
    # extract the SIGN corner as its own 1-dim general rep: conjugation
    # kept the (1,1) corner mixed, so build the plain sign rep directly.
    from srmech.math.groups import _rep_matrices_bytes
    from srmech.amsc.format import sha256_bytes
    mats = [[[(1, 1)]] if idx % 2 == 0 else [[(-1, 1)]]
            for idx in range(6)]
    sign_rep = {
        "order": 6, "degree": 1, "field": "Q", "kind": "general",
        "matrices": mats,
        "cayley_sha256": triv["cayley_sha256"],
        "matrices_sha256": sha256_bytes(
            _rep_matrices_bytes("general", mats)),
    }
    iw = intertwiner_space(triv, sign_rep)
    assert iw["dimension"] == 0
    assert iw["basis"] == []
    ct = _ct("S3", S3)
    dec = decompose_representation(sign_rep, ct)
    assert dec["is_irreducible"] is True


def test_intertwiner_between_isotypic_twins_counts_shared_content():
    ct = _ct("S3", S3)
    nat = permutation_representation(S3, _nat_action())
    reg = permutation_representation(S3, S3)
    iw = intertwiner_space(nat, reg)
    m1 = decompose_representation(nat, ct)["multiplicities"]
    m2 = decompose_representation(reg, ct)["multiplicities"]
    assert iw["dimension"] == sum(a * b for a, b in zip(m1, m2)) == 3


# ══════════════════════════════════════════════════════════════════════
# the rep-payload validator — negative controls, each naming its law
# ══════════════════════════════════════════════════════════════════════

def _nat():
    return permutation_representation(S3, _nat_action())


def test_payload_key_law():
    rep = _nat()
    del rep["matrices"]
    with pytest.raises(ValueError, match="payload-key law"):
        character_of(rep, _ct("S3", S3))
    rep2 = _nat()
    del rep2["action"]
    with pytest.raises(ValueError, match="payload-key law"):
        character_of(rep2, _ct("S3", S3))


def test_field_and_kind_laws():
    rep = _nat()
    rep["field"] = "R"
    with pytest.raises(ValueError, match="field law"):
        character_of(rep, _ct("S3", S3))
    rep = _nat()
    rep["kind"] = "unitary"
    with pytest.raises(ValueError, match="kind law"):
        character_of(rep, _ct("S3", S3))


def test_matrix_entry_law_rejects_bool_contamination():
    """True == 1 must NOT ride the 0/1 integer lane."""
    rep = _nat()
    g = 1
    r = rep["action"][g][0]
    rep["matrices"][g][r][0] = True
    with pytest.raises(ValueError, match="matrix-entry law"):
        character_of(rep, _ct("S3", S3))


def test_matrix_action_coherence_law():
    rep = _nat()
    # swap two rows of one matrix: still 0/1, one per row/col, but no
    # longer coherent with the action table
    rep["matrices"][1][0], rep["matrices"][1][1] = (
        rep["matrices"][1][1], rep["matrices"][1][0])
    # keep the content address honest so the coherence law (not the
    # content-address law) is what fires
    from srmech.math.groups import _rep_matrices_bytes
    from srmech.amsc.format import sha256_bytes
    rep["matrices_sha256"] = sha256_bytes(
        _rep_matrices_bytes("permutation", rep["matrices"]))
    with pytest.raises(ValueError, match="matrix-action coherence law"):
        character_of(rep, _ct("S3", S3))


def test_canonical_pair_law_rejects_unreduced_and_str():
    rep = _general_sign_plus_trivial()
    bad = copy.deepcopy(rep)
    bad["matrices"][0][0][0] = (2, 4)          # unreduced
    with pytest.raises(ValueError, match="canonical-pair law"):
        character_of(bad, _ct("S3", S3))
    bad2 = copy.deepcopy(rep)
    bad2["matrices"][0][0][0] = ("1", 1)       # str contaminant
    with pytest.raises(ValueError, match="canonical-pair law"):
        character_of(bad2, _ct("S3", S3))
    bad3 = copy.deepcopy(rep)
    bad3["matrices"][0][0][0] = (1, -1)        # sign on the denominator
    with pytest.raises(ValueError, match="canonical-pair law"):
        character_of(bad3, _ct("S3", S3))


def test_content_address_law_fires_on_tamper():
    rep = _nat()
    rep["matrices_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="content-address law"):
        character_of(rep, _ct("S3", S3))
    rep2 = _nat()
    rep2["cayley_sha256"] = "zz"
    with pytest.raises(ValueError, match="content-address-shape law"):
        character_of(rep2, _ct("S3", S3))


# ══════════════════════════════════════════════════════════════════════
# QMat carrier methods — trace / kron / __pow__
# ══════════════════════════════════════════════════════════════════════

A = QMat.from_rows([[Q(1, 3), Q(2, 5)], [Q(0, 1), Q(1, 7)]])
B = QMat.from_rows([[Q(2, 1), Q(1, 2)], [Q(3, 4), Q(1, 1)]])
C = QMat.from_rows([[Q(1, 2), Q(0, 1)], [Q(5, 6), Q(1, 3)]])
D = QMat.from_rows([[Q(1, 1), Q(2, 3)], [Q(0, 1), Q(4, 5)]])


def test_qmat_trace_similarity_invariance_and_additivity():
    assert A.matmul(B).trace() == B.matmul(A).trace()
    assert (A + B).trace() == A.trace() + B.trace()
    assert QMat.identity(3).trace() == Q(3, 1)
    with pytest.raises(ValueError, match="square"):
        QMat.from_rows([[1, 2, 3], [4, 5, 6]]).trace()


def test_qmat_kron_mixed_product_and_determinant_laws():
    assert (A.kron(B).matmul(C.kron(D))
            == A.matmul(C).kron(B.matmul(D)))
    assert A.kron(B).det() == A.det() ** 2 * B.det() ** 2
    assert A.kron(B).shape == (4, 4)
    # the pinned ROW-MAJOR index: out[r1*p + r2][c1*q + c2]
    assert A.kron(B)[1 * 2 + 0, 0 * 2 + 1] == A[1, 0] * B[0, 1]
    with pytest.raises(TypeError):
        A.kron([[1]])


def test_qmat_pow_positive_zero_negative():
    assert A ** 3 == A.matmul(A).matmul(A)
    assert A ** 0 == QMat.identity(2)
    assert A ** 1 == A
    assert A ** -1 == A.inverse()
    assert A ** -2 == A.inverse().matmul(A.inverse())
    assert (A ** -3).matmul(A ** 3) == QMat.identity(2)


def test_qmat_pow_sign_branch_is_pin_slot_not_magnitude():
    """The Class-K pin executor: both orientations walk the SAME
    square-and-multiply magnitude loop; the negative side re-enters
    through inverse() and the singular case raises through inverse()'s
    own guard rather than any magnitude call."""
    singular = QMat.from_rows([[1, 2], [2, 4]])
    with pytest.raises(ValueError, match="singular"):
        singular ** -1
    assert singular ** 0 == QMat.identity(2)   # the pin at the boundary
    assert singular ** 2 == singular.matmul(singular)
    with pytest.raises(TypeError):
        A ** True                              # bool is not an exponent
    with pytest.raises(ValueError, match="square"):
        QMat.from_rows([[1, 2, 3], [4, 5, 6]]) ** 2
