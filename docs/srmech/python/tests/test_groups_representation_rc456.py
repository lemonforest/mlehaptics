"""rc456 — the representation stratum, tiers 1–2 (``srmech.math.groups``).

THE MEASUREMENT THIS FILE EXECUTES (the rc's founding example)
==============================================================
A shipped workflow claimed "products of cycles are abelian, hence carry no
irrep of dim > 1".  TRUE of the DIRECT product, FALSE of the SEMIDIRECT one —
same order 21, same two cycles::

    C7 x C3  (direct)      abelian      degrees [1]*21          max dim 1
    C7 : C3  (semidirect)  NON-abelian  degrees [1,1,1,3,3]     max dim 3
    Cn : C2 by INVERSION   NON-abelian  = dihedral              max dim 2

Every oracle below is a hand-derived exact value, a mathematical identity,
or a cross-check between two shipped ops.  NO sympy anywhere (the probe tool
never enters shipped tests); NO floats anywhere (character values are
cyclotomic integers on the ``ℤ[ζ_e]`` power-basis carrier).

The tests import the private ``_zeta_mul`` for the orthogonality arithmetic —
precedented (tests may reach a module-private helper when the public payload
is exactly what feeds it), and noted here per the test plan.
"""
from __future__ import annotations

import pathlib

import pytest

from srmech.cascade import conjugacy_census, dihedral_group, unit_loop
from srmech.math.groups import (_zeta_mul, abelianization, cayley_graph,
                                character_table, conjugacy_classes,
                                cyclic_group, derived_subgroup,
                                irrep_dimensions, quotient_group,
                                semidirect_product)

# ── shared constructors (each itself under test) ──────────────────────────

C2 = cyclic_group(2)["cayley_table"]
C3 = cyclic_group(3)["cayley_table"]
C4 = cyclic_group(4)["cayley_table"]
C7 = cyclic_group(7)["cayley_table"]


def _inversion_action(n: int):
    """``Cn ⋊ C2`` by inversion: h=0 the identity, h=1 the a ↦ −a flip."""
    return [list(range(n)), [(n - a) % n for a in range(n)]]


def _trivial_action(n: int, h: int):
    return [list(range(n)) for _ in range(h)]


def _dihedral_sd(n: int):
    return semidirect_product(cyclic_group(n)["cayley_table"], C2,
                              _inversion_action(n))


S3 = _dihedral_sd(3)
D4 = _dihedral_sd(4)
D7 = _dihedral_sd(7)

#: F21 = C7 ⋊ C3 with the mult-by-2 action: action[h][a] = a·2^h mod 7
#: (2³ = 8 ≡ 1 mod 7, so the action is a genuine C3 homomorphism).
F21 = semidirect_product(
    C7, C3, [[(a * pow(2, h, 7)) % 7 for a in range(7)] for h in range(3)])

#: C7 × C3 IS the trivial action — no separate direct-product op.
C21 = semidirect_product(C7, C3, _trivial_action(7, 3))

Q8 = unit_loop(4)["cayley_table"]


def _s4():
    """S4 = V4 ⋊ S3 (= Aut(Q8) as a table).  V4 = C2 × C2 (trivial action);
    its three involutions sit at indices 1 = (0,1), 2 = (1,0), 3 = (1,1).
    S3 (the ``_dihedral_sd(3)`` table, elements (a, h) at index a·2 + h)
    acts on them through ρ((a, h)) = c^a ∘ t^h where c is the 3-cycle
    1→2→3→1 and t the transposition 1↔2 — a homomorphism because
    ρ(r)³ = 1, ρ(s)² = 1 and ρ(s)ρ(r)ρ(s) = ρ(r)⁻¹ (t·c·t = c² in S3).
    The six rows below are those compositions, hand-derived:
        (0,0) → id        (0,1) → t         (1,0) → c
        (1,1) → c∘t       (2,0) → c²        (2,1) → c²∘t
    """
    v4 = semidirect_product(C2, C2, _trivial_action(2, 2))
    c = [0, 2, 3, 1]
    t = [0, 2, 1, 3]

    def compose(f, g):
        return [f[g[v]] for v in range(4)]

    powc = [list(range(4)), c, compose(c, c)]
    action = []
    for a in range(3):
        for h in range(2):
            action.append(powc[a] if h == 0 else compose(powc[a], t))
    return semidirect_product(v4["cayley_table"], S3["cayley_table"], action)


S4 = _s4()

#: Every (name, table) pair the cross-op identity sweep runs over.
ALL_GROUPS = [
    ("C3", C3), ("C4", C4), ("C6", cyclic_group(6)["cayley_table"]),
    ("S3", S3["cayley_table"]), ("D4", D4["cayley_table"]),
    ("D7", D7["cayley_table"]), ("Q8", Q8),
    ("F21", F21["cayley_table"]), ("C7xC3", C21["cayley_table"]),
    ("S4", S4["cayley_table"]),
]


# ── 1. cyclic_group is a VALUE, not a shape ──────────────────────────────

def test_cyclic_group_c3_exact_values():
    c3 = cyclic_group(3)
    assert c3["cayley_table"] == [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
    assert c3["inverses"] == [0, 2, 1]
    assert c3["identity"] == 0
    assert c3["order"] == 3


def test_cyclic_group_refuses_below_one():
    with pytest.raises(ValueError):
        cyclic_group(0)


# ── 2. dihedral equivalence — the rc's motivating measurement, executed ──
#
# INTROSPECTED FIRST (the plan's instruction): dihedral_group(3)'s two
# conventions were printed and the semidirect table compared under
# σ(a·2 + h) = h·n + a against BOTH.  MEASURED: the match is EXACT for
# convention="rotation_first" (labels rⁱ·s) on all n tested, and fails for
# "reflection_first".  That is the left-action orientation: the semidirect
# product (a1,h1)·(a2,h2) = (a1 + φ_{h1}(a2), h1+h2) reproduces the
# rotation_first products (rᵃ·s)·rᵇ = r^{a−b}·s etc.  Recorded here rather
# than "fixed" — the test pins the measured convention.

@pytest.mark.parametrize("n", [3, 4, 7])
def test_semidirect_by_inversion_is_dihedral_exactly(n):
    sd = _dihedral_sd(n)["cayley_table"]
    dg = dihedral_group(n, "rotation_first")["cayley_table"]
    order = 2 * n
    sigma = [0] * order
    for a in range(n):
        for h in range(2):
            sigma[a * 2 + h] = h * n + a
    for x in range(order):
        for y in range(order):
            assert dg[sigma[x]][sigma[y]] == sigma[sd[x][y]], (
                f"D{n}: relabelled product mismatch at ({x}, {y})")


# ── 3. semidirect_product negatives + the trivial action ─────────────────

def test_semidirect_rejects_non_bijective_action_row():
    with pytest.raises(ValueError, match="bijection"):
        semidirect_product(C4, C2, [list(range(4)), [0, 0, 1, 2]])


def test_semidirect_rejects_non_automorphism():
    # swapping only elements 1 and 2 of C4 is a bijection but not an
    # automorphism (1+1=2 maps to 1+... breaks additivity).
    with pytest.raises(ValueError, match="automorphism"):
        semidirect_product(C4, C2, [list(range(4)), [0, 2, 1, 3]])


def test_semidirect_rejects_non_homomorphism():
    # mult-by-2 on C5 is an automorphism of order 4; C2 cannot carry it.
    c5 = cyclic_group(5)["cayley_table"]
    with pytest.raises(ValueError, match="homomorphism"):
        semidirect_product(c5, C2,
                           [list(range(5)), [(2 * a) % 5 for a in range(5)]])


def test_semidirect_rejects_identity_acting_nontrivially():
    with pytest.raises(ValueError, match="identity"):
        semidirect_product(C3, C2, [[0, 2, 1], [0, 2, 1]])


def test_trivial_action_is_the_direct_product():
    census = conjugacy_census(C21["cayley_table"])
    assert census["is_group"]
    assert census["k_classes"] == 21
    assert census["commuting_pairs"] == 441          # 21² — fully abelian


# ── 4. conjugacy_classes — values, consistency, refusal ──────────────────

def test_f21_classes():
    cc = conjugacy_classes(F21["cayley_table"])
    assert cc["k"] == 5
    assert sorted(cc["class_sizes"]) == [1, 3, 3, 7, 7]


def test_s3_classes_against_the_table_literal():
    # The exact S3 table the constructor emits (pinned as a VALUE so the
    # conventions in 3.2's docstring cannot drift silently).
    assert S3["cayley_table"] == [
        [0, 1, 2, 3, 4, 5], [1, 0, 5, 4, 3, 2], [2, 3, 4, 5, 0, 1],
        [3, 2, 1, 0, 5, 4], [4, 5, 0, 1, 2, 3], [5, 4, 3, 2, 1, 0]]
    cc = conjugacy_classes(S3["cayley_table"])
    assert cc["k"] == 3
    assert sorted(cc["class_sizes"]) == [1, 2, 3]
    assert cc["classes"] == [[0], [1, 3, 5], [2, 4]]


def test_q8_classes():
    cc = conjugacy_classes(Q8)
    assert cc["k"] == 5
    assert sorted(cc["class_sizes"]) == [1, 1, 2, 2, 2]


def test_class_of_is_consistent_with_classes():
    for name, table in ALL_GROUPS:
        cc = conjugacy_classes(table)
        for ci, block in enumerate(cc["classes"]):
            for x in block:
                assert cc["class_of"][x] == ci, (name, x)
        assert cc["representatives"] == [b[0] for b in cc["classes"]], name
        assert cc["class_sizes"] == [len(b) for b in cc["classes"]], name


def test_non_group_is_refused():
    # M16 (the sedenion-free octonion unit loop) is NON-associative: the
    # census reports it, and the group-only op must REFUSE, not answer.
    m16 = unit_loop(8)["cayley_table"]
    with pytest.raises(ValueError, match="not a group"):
        conjugacy_classes(m16)
    with pytest.raises(ValueError, match="not a group"):
        derived_subgroup(m16)
    with pytest.raises(ValueError, match="not a group"):
        cayley_graph(m16, [1], "right")


# ── 5. derived_subgroup ──────────────────────────────────────────────────

def test_derived_subgroups():
    assert derived_subgroup(S3["cayley_table"])["subgroup_order"] == 3
    q8_ds = derived_subgroup(Q8)
    assert q8_ds["subgroup_order"] == 2
    # {identity, the unique order-2 element}: the identity plus the one
    # element x != e with x² = e.
    e = conjugacy_classes(Q8)["identity"]
    order2 = [x for x in range(8) if x != e and Q8[x][x] == e]
    assert len(order2) == 1
    assert q8_ds["elements"] == sorted([e, order2[0]])
    assert derived_subgroup(F21["cayley_table"])["subgroup_order"] == 7
    assert derived_subgroup(
        cyclic_group(6)["cayley_table"])["subgroup_order"] == 1


# ── 6. quotient_group ────────────────────────────────────────────────────

def test_s3_mod_rotations():
    rotations = derived_subgroup(S3["cayley_table"])["elements"]
    q = quotient_group(S3["cayley_table"], rotations)
    assert q["order"] == 2
    assert q["cayley_table"] == [[0, 1], [1, 0]]


def test_s3_mod_a_reflection_is_refused_as_non_normal():
    # element 1 = (0, 1) is a reflection; {e, s} is a subgroup but NOT
    # normal in S3 — the negative that could fail.
    with pytest.raises(ValueError, match="not normal"):
        quotient_group(S3["cayley_table"], [0, 1])


def test_quotient_rejects_a_non_subgroup():
    with pytest.raises(ValueError, match="not a subgroup"):
        quotient_group(S3["cayley_table"], [0, 2])    # not closed: 2·2 = 4


# ── 7. abelianization ────────────────────────────────────────────────────

@pytest.mark.parametrize("table,want", [
    (S3["cayley_table"], [2]),
    (Q8, [2, 2]),
    (F21["cayley_table"], [3]),
    (C21["cayley_table"], [21]),
    (D4["cayley_table"], [2, 2]),
])
def test_invariant_factors(table, want):
    ab = abelianization(table)
    assert ab["invariant_factors"] == want
    # cross-op identity: |Q| == ∏ d_i == |G| // |[G,G]|
    prod = 1
    for d in ab["invariant_factors"]:
        prod *= d
    assert ab["order"] == prod
    ds = derived_subgroup(table)
    assert ab["order"] == ds["order"] // ds["subgroup_order"]
    # divisibility chain d_1 | d_2 | …
    factors = ab["invariant_factors"]
    for a, b in zip(factors, factors[1:]):
        assert b % a == 0


# ── 8. cayley_graph ──────────────────────────────────────────────────────

def test_c4_graph_exact_edges():
    g = cayley_graph(C4, [1], "right")
    assert g["edges"] == [(0, 1), (1, 2), (2, 3), (3, 0)]
    assert g["edge_generator"] == [1, 1, 1, 1]
    assert g["is_connected"] is True


def test_s3_rotation_only_is_disconnected():
    # element 2 = (1, 0) is the rotation r; ⟨r⟩ has index 2, so the
    # rotation-only graph cannot reach the reflections.
    g = cayley_graph(S3["cayley_table"], [2], "right")
    assert g["is_connected"] is False


def test_s3_rotation_plus_reflection_connects():
    g = cayley_graph(S3["cayley_table"], [2, 1], "right")
    assert g["is_connected"] is True
    assert len(g["edges"]) == 12                     # |G|·|gens| = 6·2


def test_graph_determinism_and_negatives():
    a = cayley_graph(C4, [1], "right")
    b = cayley_graph(C4, [1], "right")
    assert a["edges_sha256"] == b["edges_sha256"]
    with pytest.raises(ValueError):
        cayley_graph(C4, [], "right")
    with pytest.raises(ValueError):
        cayley_graph(C4, [1, 1], "right")
    with pytest.raises(ValueError):
        cayley_graph(C4, [1], "sideways")


def test_left_and_right_graphs_differ_on_a_non_abelian_group():
    right = cayley_graph(S3["cayley_table"], [1], "right")
    left = cayley_graph(S3["cayley_table"], [1], "left")
    assert right["edges"] != left["edges"]


# ── 9. tier 2 — the mandatory degree oracles, all hand-verified ──────────

@pytest.mark.parametrize("name,table,want", [
    ("C7xC3", C21["cayley_table"], [1] * 21),
    ("F21", F21["cayley_table"], [1, 1, 1, 3, 3]),
    ("D3", S3["cayley_table"], [1, 1, 2]),
    ("D4", D4["cayley_table"], [1, 1, 1, 1, 2]),
    ("D7", D7["cayley_table"], [1, 1, 2, 2, 2]),
    ("Q8", Q8, [1, 1, 1, 1, 2]),
    ("S4", S4["cayley_table"], [1, 1, 2, 3, 3]),
])
def test_irrep_degrees(name, table, want):
    assert character_table(table)["degrees"] == want, name


def test_s4_structure():
    assert S4["order"] == 24
    cc = conjugacy_classes(S4["cayley_table"])
    assert cc["k"] == 5
    assert sorted(cc["class_sizes"]) == [1, 3, 6, 6, 8]
    assert derived_subgroup(S4["cayley_table"])["subgroup_order"] == 12
    assert abelianization(S4["cayley_table"])["invariant_factors"] == [2]


# ── 10. identities on EVERY group in this file ───────────────────────────

def test_cross_op_identities_on_every_group():
    for name, table in ALL_GROUPS:
        ct = character_table(table)
        n = ct["order"]
        assert sum(d * d for d in ct["degrees"]) == n, name
        assert ct["k"] == conjugacy_classes(table)["k"], name
        assert len(ct["degrees"]) == ct["k"], name
        assert ct["degrees"].count(1) == abelianization(table)["order"], name
        for d in ct["degrees"]:
            assert n % d == 0, name
        assert ct["degrees"] == sorted(ct["degrees"]), name


# ── 11. value-level cyclotomic assertions (shapes are not tests) ─────────

def test_c3_values_exactly():
    ct = character_table(C3)
    assert ct["exponent"] == 3
    assert ct["phi_e"] == (1, 1, 1)                  # Φ_3 = 1 + x + x²
    assert ct["degree"] == 2                         # φ(3)
    flat = [cell for row in ct["table"] for cell in row]
    assert (0, 1) in flat                            # ζ_3 itself
    assert (-1, -1) in flat                          # ζ_3² = −1 − ζ_3
    # χ(identity) is always the degree vector (d, 0, …)
    e_col = ct["class_of"][conjugacy_classes(C3)["identity"]]
    for d, row in zip(ct["degrees"], ct["table"]):
        assert row[e_col] == (d, 0)


def test_c4_values_exactly():
    ct = character_table(C4)
    assert ct["exponent"] == 4
    assert ct["phi_e"] == (1, 0, 1)                  # Φ_4 = 1 + x²; basis {1, i}
    gen_col = ct["class_of"][1]                      # the generator's class
    two_col = ct["class_of"][2]                      # the order-2 element
    gen_vals = sorted(row[gen_col] for row in ct["table"])
    assert (0, 1) in gen_vals and (0, -1) in gen_vals
    faithful = [row for row in ct["table"] if row[gen_col] in ((0, 1), (0, -1))]
    assert len(faithful) == 2
    for row in faithful:
        assert row[two_col] == (-1, 0)               # i² = −1


def test_f21_the_founding_example_values():
    """The two degree-3 rows of F21 = C7⋊C3, hand-derived, no oracle package.

    They vanish on both size-7 classes; on the size-3 classes their values
    are η = ζ7 + ζ7² + ζ7⁴ and its conjugate, which satisfy η² + η + 2 = 0 —
    executed below as v1+v2 = −1, v1·v2 = 2, v1² + v1 = −2 in ℤ[ζ21].
    """
    ct = character_table(F21["cayley_table"])
    assert ct["exponent"] == 21
    assert ct["degree"] == 12                        # φ(21)
    phi = ct["phi_e"]
    deg = ct["degree"]
    zero = tuple([0] * deg)
    d3_rows = [row for d, row in zip(ct["degrees"], ct["table"]) if d == 3]
    assert len(d3_rows) == 2
    size7 = [j for j, s in enumerate(ct["class_sizes"]) if s == 7]
    size3 = [j for j, s in enumerate(ct["class_sizes"]) if s == 3]
    assert len(size7) == 2 and len(size3) == 2
    for row in d3_rows:
        for j in size7:
            assert row[j] == zero
    for j in size3:
        v1, v2 = d3_rows[0][j], d3_rows[1][j]
        assert tuple(a + b for a, b in zip(v1, v2)) == (
            (-1,) + (0,) * (deg - 1))                # η + η̄ = −1
        assert _zeta_mul(v1, v2, phi) == ((2,) + (0,) * (deg - 1))
        sq = _zeta_mul(v1, v1, phi)
        assert tuple(a + b for a, b in zip(sq, v1)) == (
            (-2,) + (0,) * (deg - 1))                # η² + η = −2


# ── 12. orthogonality, executed in ℤ[ζ_e] ────────────────────────────────
#
# Conjugation is the class-of-inverse permutation: χ̄(g) = χ(g⁻¹), so the
# weighted row product needs NO Galois machinery — just inverse_class.

@pytest.mark.parametrize("name,table", [
    ("D4", D4["cayley_table"]),
    ("Q8", Q8),
    ("F21", F21["cayley_table"]),
])
def test_row_and_column_orthogonality(name, table):
    ct = character_table(table)
    phi, deg, k, n = ct["phi_e"], ct["degree"], ct["k"], ct["order"]
    sizes, invc = ct["class_sizes"], ct["inverse_class"]
    for i in range(k):
        for j in range(k):
            acc = [0] * deg
            for m in range(k):
                prod = _zeta_mul(ct["table"][i][m],
                                 ct["table"][j][invc[m]], phi)
                acc = [a + sizes[m] * b for a, b in zip(acc, prod)]
            want = tuple([n if i == j else 0] + [0] * (deg - 1))
            assert tuple(acc) == want, (name, "row", i, j)
    for m in range(k):
        acc = [0] * deg
        for i in range(k):
            prod = _zeta_mul(ct["table"][i][m],
                             ct["table"][i][invc[m]], phi)
            acc = [a + b for a, b in zip(acc, prod)]
        want = tuple([n // sizes[m]] + [0] * (deg - 1))
        assert tuple(acc) == want, (name, "col", m)


def test_f21_centralizer_orders():
    # the column-orthogonality diagonal IS the centralizer order |G|/|C_k|:
    # for F21 that multiset is {21, 7, 7, 3, 3}.
    ct = character_table(F21["cayley_table"])
    assert sorted(ct["order"] // s for s in ct["class_sizes"]) == [
        3, 3, 7, 7, 21]


# ── 13. irrep_dimensions delegates — one SSoT — and hashes are stable ────

def test_irrep_dimensions_is_the_character_table_readout():
    for name, table in ALL_GROUPS:
        ct = character_table(table)
        ir = irrep_dimensions(table)
        assert ir["degrees"] == ct["degrees"], name
        assert ir["k"] == ct["k"], name
        assert ir["order"] == ct["order"], name
        assert ir["num_linear"] == ct["degrees"].count(1), name
        assert ir["sum_of_squares"] == ct["order"], name


def test_table_sha_is_deterministic():
    a = character_table(S3["cayley_table"])["table_sha256"]
    b = character_table(S3["cayley_table"])["table_sha256"]
    assert a == b and len(a) == 64


# ── 14. the executed form of the exact-arithmetic claim ──────────────────

def test_no_alu_magnitude_and_no_float_in_the_source():
    """An ASSERTED algebraic property is not a MEASURED one: the module
    claims exact-only arithmetic with Class-K/Class-C sign handling, and
    this test executes that claim against the source — the banned ALU
    magnitude call and the float constructor appear nowhere outside
    comments (docstrings avoid the spellings entirely)."""
    import srmech.math.groups as groups_module
    src = pathlib.Path(groups_module.__file__).read_text(encoding="utf-8")
    code = "\n".join(line.split("#", 1)[0] for line in src.splitlines())
    assert "abs(" not in code
    assert "float(" not in code


def test_semidirect_tables_pass_the_census_oracle():
    """3.2's validation laws entail associativity; the shipped census is
    run as the INDEPENDENT oracle of that entailment."""
    for sd in (S3, D4, D7, F21, C21, S4):
        census = conjugacy_census(sd["cayley_table"])
        assert census["is_group"], sd["order"]


# ── 15. the documented division-lift recipe, executed VERBATIM ───────────

def test_docstring_qalg_lift_executes_verbatim():
    """The module's ONLY documented division recipe (the header says "two
    lines, shown in :func:`character_table`'s docstring", and both emitted
    introspect surfaces point at it) is extracted from the LIVE docstring
    and executed — not a copy, so the recipe cannot drift from the carrier
    again.  The rc456 repair pass measured the originally shipped spelling
    raising ``TypeError`` on every call (``Qalg``'s modulus is its FIRST
    positional), and it survived 56 green tests because no other gate
    executes docstring code blocks."""
    import re
    import textwrap

    from srmech.math.qalg import Qalg

    doc = character_table.__doc__
    blocks = [b for b in re.findall(r"::\n\n((?:[ ]{8}.*\n)+)", doc)
              if "Qalg(" in b]
    assert len(blocks) == 1, "the docstring lost its Qalg code block"
    snippet = textwrap.dedent(blocks[0])
    namespace = {"character_table": character_table,
                 "table": C3, "i": 1, "j": 1}
    exec(compile(snippet, "<character_table docstring>", "exec"), namespace)
    value = namespace["value"]
    assert isinstance(value, Qalg)
    # The lift landed in the right ring: the C3 cell (1,1) is zeta_3 —
    # it cubes to one, and the DIVISION the recipe exists for executes.
    assert value == Qalg(list(namespace["ct"]["phi_e"]),
                         namespace["ct"]["table"][1][1])
    assert (value * value * value) == value.one()
    assert (value * value.inverse()) == value.one()
