"""rc457 — the representation stratum, tier 3 (``srmech.math.groups``):
``frobenius_schur_indicator`` + ``fusion_multiplicities`` +
``central_idempotents``, the readout layer over the rc456 payload.

Every oracle below is a hand-derived exact value, a mathematical identity,
or a cross-check between two shipped ops / two independent routes.  NO sympy
anywhere (the probe tool never enters shipped tests); NO floats anywhere; NO
bools stored as counts.  **Every test locates rows by CONTENT (degree +
value vector), never by index** — measured trap: the trivial character sits
at index 2 in C7⋊C3's payload, and S4's row 0 is the sign character.

PRESERVES-CLAIM → EXECUTING-TEST MAP (the property-gate discipline: no
ToolEntry ``preserves`` claim ships without its executor)
=========================================================================
  claim (all three tier-3 ToolEntries carry the same one):
    "numpy-free; no abs() — sign-handling stays Class-K pin-slot + Class-C"
  executors:
    - test_no_alu_magnitude_and_no_float_in_the_source
      (tests/test_groups_representation_rc456.py — scans the WHOLE module
      source, so the tier-3 additions are covered automatically), and
    - test_fs_three_point_pin_is_membership_not_magnitude (below — the
      Class-K pin is exact set membership, executed on both signs).
  numpy-free is executed by the suite running in the numpy-ABSENT CI cell.
"""
from __future__ import annotations

import pytest

from srmech.cascade import dihedral_group, unit_loop
from srmech.math.groups import (_zeta_mul, central_idempotents,
                                character_table, cyclic_group,
                                frobenius_schur_indicator,
                                fusion_multiplicities, semidirect_product)

# ── shared fixtures (rc456 construction idioms, each constructor itself
#    under test in the rc456 file) ─────────────────────────────────────────

C2 = cyclic_group(2)["cayley_table"]
C3 = cyclic_group(3)["cayley_table"]
C4 = cyclic_group(4)["cayley_table"]
C5 = cyclic_group(5)["cayley_table"]
C7 = cyclic_group(7)["cayley_table"]

D3 = dihedral_group(3, "rotation_first")["cayley_table"]
D4 = dihedral_group(4, "rotation_first")["cayley_table"]
D5 = dihedral_group(5, "rotation_first")["cayley_table"]

Q8 = unit_loop(4)["cayley_table"]


def _trivial_action(n: int, h: int):
    return [list(range(n)) for _ in range(h)]


#: F21 = C7 ⋊ C3 with the mult-by-2 action (2³ ≡ 1 mod 7 — a genuine C3
#: homomorphism); e = 21, φ(21) = 12 — the deep-ring exercise.
F21 = semidirect_product(
    C7, C3,
    [[(a * pow(2, h, 7)) % 7 for a in range(7)] for h in range(3)]
)["cayley_table"]

#: C7 × C3 IS the trivial action — no separate direct-product op.
C21 = semidirect_product(C7, C3, _trivial_action(7, 3))["cayley_table"]


def _s3_sd():
    """S3 as C3 ⋊ C2 by inversion — the operand the S4 action rows are
    hand-derived against (rc456's construction, kept verbatim)."""
    return semidirect_product(C3, C2, [[0, 1, 2], [0, 2, 1]])


def _s4():
    """S4 = V4 ⋊ S3 (rc456's hand-derived action rows, kept verbatim)."""
    s3 = _s3_sd()
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
    return semidirect_product(v4["cayley_table"], s3["cayley_table"],
                              action)["cayley_table"]


S4 = _s4()

ALL_GROUPS = [
    ("C3", C3), ("C4", C4), ("C5", C5), ("C7", C7),
    ("D3", D3), ("D4", D4), ("D5", D5), ("Q8", Q8),
    ("F21", F21), ("C7xC3", C21), ("S4", S4),
]

_CT_CACHE = {}


def _ct(name, table):
    if name not in _CT_CACHE:
        _CT_CACHE[name] = character_table(table)
    return _CT_CACHE[name]


# ── row-location helpers: CONTENT, never index ────────────────────────────

def _zero(ct):
    return (0,) * ct["degree"]


def _one(ct):
    return (1,) + (0,) * (ct["degree"] - 1)


def _trivial_row(ct):
    """The unique row whose every value is (1, 0, …, 0)."""
    hits = [i for i in range(ct["k"])
            if all(tuple(v) == _one(ct) for v in ct["table"][i])]
    assert len(hits) == 1
    return hits[0]


def _conj_row(ct):
    """conj_row[a] = the row holding the inverse-class permuted values of
    row a (χ̄ = χ∘inverse — a CONTENT match, no index assumption)."""
    k, invc = ct["k"], ct["inverse_class"]
    out = []
    for a in range(k):
        target = tuple(tuple(ct["table"][a][invc[j]]) for j in range(k))
        hits = [i for i in range(k)
                if tuple(tuple(v) for v in ct["table"][i]) == target]
        assert len(hits) == 1, f"row {a}: conjugate row not unique"
        out.append(hits[0])
    return out


def _identity_class(ct):
    """The unique column where every row equals its degree vector."""
    k, deg = ct["k"], ct["degree"]
    hits = [j for j in range(k)
            if all(tuple(ct["table"][i][j])
                   == (ct["degrees"][i],) + (0,) * (deg - 1)
                   for i in range(k))]
    assert len(hits) == 1
    return hits[0]


def _identity_element(table):
    n = len(table)
    hits = [e for e in range(n)
            if all(table[e][x] == x and table[x][e] == x for x in range(n))]
    assert len(hits) == 1
    return hits[0]


def _corrupt_cell(ct, row, col, delta_at=0):
    """A shallow payload copy with ONE table coordinate bumped by +1."""
    bad = dict(ct)
    tbl = [[tuple(cell) for cell in r] for r in ct["table"]]
    cell = list(tbl[row][col])
    cell[delta_at] += 1
    tbl[row][col] = tuple(cell)
    bad["table"] = tbl
    return bad


# ── 1. FS — the mandatory three-way separation, rows located by content ──

def test_fs_three_way_separation():
    """Q8 (quaternionic present) / D4 + D5 (all real) / C7⋊C3 (complex
    present) jointly separate the three outcomes; the ±1 rows are located
    by CONTENT."""
    ct = _ct("Q8", Q8)
    fs = frobenius_schur_indicator(ct)
    assert sorted(fs["indicators"]) == [-1, 1, 1, 1, 1]
    # the -1 sits EXACTLY on the degree-2 row
    for nu, d in zip(fs["indicators"], ct["degrees"]):
        if d == 2:
            assert nu == -1
        else:
            assert nu == 1
    assert (fs["num_real"], fs["num_complex"], fs["num_quaternionic"]) \
        == (4, 0, 1)

    for name, table in (("D4", D4), ("D5", D5)):
        ct = _ct(name, table)
        fs = frobenius_schur_indicator(ct)
        assert fs["indicators"] == (1,) * ct["k"], name
        assert fs["num_quaternionic"] == 0 and fs["num_complex"] == 0, name

    ct = _ct("F21", F21)
    fs = frobenius_schur_indicator(ct)
    assert sorted(fs["indicators"]) == [0, 0, 0, 0, 1]
    # the single +1 sits EXACTLY on the trivial (all-(1,0,…,0)) row
    assert fs["indicators"][_trivial_row(ct)] == 1
    # measured trap, recorded as an executed fact: that row is index 2 here
    assert _trivial_row(ct) == 2


@pytest.mark.parametrize("name,table,multiset", [
    ("C3", C3, [0, 0, 1]),
    ("C4", C4, [0, 0, 1, 1]),
    ("C5", C5, [0, 0, 0, 0, 1]),
    ("C7", C7, [0, 0, 0, 0, 0, 0, 1]),
    ("D3", D3, [1, 1, 1]),
    ("S4", S4, [1, 1, 1, 1, 1]),
    ("C7xC3", C21, [0] * 20 + [1]),
])
def test_fs_value_multisets(name, table, multiset):
    ct = _ct(name, table)
    fs = frobenius_schur_indicator(ct)
    assert sorted(fs["indicators"]) == multiset, name
    # the trivial row is always real
    assert fs["indicators"][_trivial_row(ct)] == 1, name


# ── 2. FS — the counting identity, character-free LHS off the table ──────
#
# CLASSIFICATION, stated honestly: #{g : g² = e} read off the CAYLEY TABLE
# equals Σ ν_i·d_i — this detects a WRONG TABLE for the given group, but a
# swapped group satisfies its own identity, so it cannot detect that; the
# pinned VALUE multisets above are the group-discriminating oracles.

@pytest.mark.parametrize("name,table,want", [
    ("Q8", Q8, 2), ("D4", D4, 6), ("D5", D5, 6), ("D3", D3, 4),
    ("F21", F21, 1), ("S4", S4, 10), ("C4", C4, 2), ("C7xC3", C21, 1),
])
def test_fs_counting_identity(name, table, want):
    e = _identity_element(table)
    table_count = sum(1 for g in range(len(table)) if table[g][g] == e)
    fs = frobenius_schur_indicator(_ct(name, table))
    assert table_count == want, name
    assert fs["square_roots_of_identity"] == want, name


def test_fs_self_conjugacy_identity():
    """ν ≠ 0 ⟺ the row is fixed under the inverse-class column permutation
    (self-conjugate), and conjugate row pairs carry equal ν — every
    fixture.  Measured F21 pairing recorded: linears 0↔1, degree-3 3↔4."""
    for name, table in ALL_GROUPS:
        ct = _ct(name, table)
        fs = frobenius_schur_indicator(ct)
        conj = _conj_row(ct)
        for i, nu in enumerate(fs["indicators"]):
            if conj[i] == i:
                assert nu != 0, (name, i)
            else:
                assert nu == 0, (name, i)
            assert nu == fs["indicators"][conj[i]], (name, i)
    assert _conj_row(_ct("F21", F21)) == [1, 0, 2, 4, 3]


def test_fs_three_point_pin_is_membership_not_magnitude():
    """The Class-K pin executes as exact membership on BOTH signs: -1 and
    +1 both pass through the pin unchanged (Q8 exercises both in one
    payload), and the payload echo carries them as plain ints."""
    fs = frobenius_schur_indicator(_ct("Q8", Q8))
    for nu in fs["indicators"]:
        assert nu in (-1, 0, 1)
        assert isinstance(nu, int) and not isinstance(nu, bool)
    assert -1 in fs["indicators"] and 1 in fs["indicators"]


def test_fs_negative_corruption_in_square_image_raises():
    """Corrupt ONE table cell in a square-image column of Q8's payload →
    the in-op |G|-divisibility guard raises.  (Corruption OUTSIDE the
    square image is mathematically invisible to ν — the counting identity
    above is the paired detector for that; documented, not fake-covered.)"""
    ct = _ct("Q8", Q8)
    square_image = set(ct["square_class"])
    col = next(iter(square_image))
    bad = _corrupt_cell(ct, 0, col)
    with pytest.raises(ValueError, match="divisib|rationality"):
        frobenius_schur_indicator(bad)


def test_payload_validation_names_the_law():
    """The shared payload validator refuses a missing key and a bool
    contamination, NAMING the law — all three ops share it."""
    ct = _ct("D3", D3)
    for op in (frobenius_schur_indicator, fusion_multiplicities,
               central_idempotents):
        bad = dict(ct)
        del bad["square_class"]
        with pytest.raises(ValueError, match="payload-key law"):
            op(bad)
    bad = dict(ct)
    tbl = [[tuple(c) for c in r] for r in ct["table"]]
    tbl[0][0] = (True,) + tuple(tbl[0][0][1:])
    bad["table"] = tbl
    with pytest.raises(ValueError, match="plain-int law"):
        frobenius_schur_indicator(bad)


# ── 3. fusion — pinned values, rows located by content ───────────────────

def test_fusion_s3_two_tensor_two():
    """S3: 2 ⊗ 2 = 1 + 1' + 2 — every character once."""
    ct = _ct("D3", D3)
    fu = fusion_multiplicities(ct)
    two = ct["degrees"].index(2)
    assert len([d for d in ct["degrees"] if d == 2]) == 1
    assert fu["multiplicities"][two][two] == (1, 1, 1)


def test_fusion_q8_two_tensor_two():
    """Q8: 2 ⊗ 2 = the four linears, 0 on the degree-2 row itself."""
    ct = _ct("Q8", Q8)
    fu = fusion_multiplicities(ct)
    two = ct["degrees"].index(2)
    for c in range(ct["k"]):
        want = 0 if ct["degrees"][c] == 2 else 1
        assert fu["multiplicities"][two][two][c] == want


def test_fusion_f21_deep_ring():
    """C7⋊C3 over Φ₂₁ (φ(21) = 12 — the deep-ring exercise): 3 ⊗ 3̄ = every
    character once; 3 ⊗ 3 = 3 + 2·3̄ and its mirror.  The two degree-3 rows
    are told apart by the CONTENT-derived conjugation map, not by index."""
    ct = _ct("F21", F21)
    fu = fusion_multiplicities(ct)["multiplicities"]
    conj = _conj_row(ct)
    d3 = [i for i, d in enumerate(ct["degrees"]) if d == 3]
    assert len(d3) == 2
    r1, r2 = d3
    assert conj[r1] == r2 and conj[r2] == r1
    assert fu[r1][r2] == (1,) * ct["k"]                 # 3 ⊗ 3̄ = all five
    want_11 = [0] * ct["k"]
    want_11[r1], want_11[r2] = 1, 2                      # 3 ⊗ 3 = 3 + 2·3̄
    assert fu[r1][r1] == tuple(want_11)
    want_22 = [0] * ct["k"]
    want_22[r1], want_22[r2] = 2, 1                      # the mirror
    assert fu[r2][r2] == tuple(want_22)


@pytest.mark.parametrize("name,table", [
    ("C3", C3), ("C4", C4), ("C5", C5), ("C7", C7)])
def test_fusion_abelian_is_the_dual_group(name, table):
    """Abelian fixtures: every product is exactly ONE character (value),
    and the (a, b) → c map IS dual-group multiplication — the pointwise
    ζ-ring product of rows a and b equals row c cell-for-cell (structural
    law, executed in ℤ[ζ_e])."""
    ct = _ct(name, table)
    k, phi = ct["k"], ct["phi_e"]
    fu = fusion_multiplicities(ct)["multiplicities"]
    for a in range(k):
        for b in range(k):
            hits = [c for c in range(k) if fu[a][b][c] == 1]
            assert len(hits) == 1, (name, a, b)
            assert sum(fu[a][b]) == 1, (name, a, b)
            c = hits[0]
            for j in range(k):
                assert _zeta_mul(ct["table"][a][j], ct["table"][b][j],
                                 phi) == tuple(ct["table"][c][j]), \
                    (name, a, b, j)


def test_fusion_identities_every_group():
    """N_abc = N_bac; Σ_c N_abc·d_c = d_a·d_b; the trivial-component law
    N_ab,triv = [b == conj(a)]; N_a,triv,c = δ_ac; every entry a
    non-negative plain int — every fixture."""
    for name, table in ALL_GROUPS:
        ct = _ct(name, table)
        k, degrees = ct["k"], ct["degrees"]
        fu = fusion_multiplicities(ct)["multiplicities"]
        conj = _conj_row(ct)
        triv = _trivial_row(ct)
        for a in range(k):
            for b in range(k):
                for c in range(k):
                    n = fu[a][b][c]
                    assert isinstance(n, int) and not isinstance(n, bool)
                    assert n >= 0, (name, a, b, c)
                    assert n == fu[b][a][c], (name, a, b, c)
                assert sum(fu[a][b][c] * degrees[c] for c in range(k)) \
                    == degrees[a] * degrees[b], (name, a, b)
                assert fu[a][b][triv] == (1 if b == conj[a] else 0), \
                    (name, a, b)
            for c in range(k):
                assert fu[a][triv][c] == (1 if c == a else 0), (name, a, c)


def test_fusion_negative_corruption_raises():
    ct = _ct("D3", D3)
    bad = _corrupt_cell(ct, 0, 1)
    with pytest.raises(ValueError, match="divisib|integrality"):
        fusion_multiplicities(bad)


# ── 4. central_idempotents — two INDEPENDENT verification routes ─────────
#
# Route 1 (all fixtures incl. the Φ₂₁ ring): e_i·e_j = δ_ij·e_i and
# Σ e_i = δ_e executed in the CLASS-SUM basis via the payload's
# class_algebra structure constants.  Route 2 (S3 + Q8): the same two
# identities via FULL group-algebra convolution over the Cayley table —
# the co-equal-dual consistency oracle; a disagreement is a finding.
# All arithmetic is integer ℤ[ζ_e] on numerators (denominators cleared
# symbolically: comparing e_i·e_j against e_i/δ over the common
# denominator order² means comparing numerator sums against
# order·numerators[i]).

@pytest.mark.parametrize("name,table", [
    ("C4", C4), ("D3", D3), ("D4", D4), ("Q8", Q8), ("F21", F21)])
def test_idempotents_orthogonality_class_basis(name, table):
    ct = _ct(name, table)
    k, deg, order, phi = ct["k"], ct["degree"], ct["order"], ct["phi_e"]
    A = ct["class_algebra"]
    ci = central_idempotents(ct)
    num = ci["numerators"]
    assert ci["denominator"] == order
    zero = (0,) * deg
    for i in range(k):
        for j in range(k):
            for l in range(k):
                acc = [0] * deg
                for p in range(k):
                    for q in range(k):
                        if A[p][q][l]:
                            prod = _zeta_mul(num[i][p], num[j][q], phi)
                            w = A[p][q][l]
                            for t in range(deg):
                                acc[t] += w * prod[t]
                if i == j:
                    want = tuple(order * c for c in num[i][l])
                else:
                    want = zero
                assert tuple(acc) == want, (name, i, j, l)


@pytest.mark.parametrize("name,table", [("D3", D3), ("Q8", Q8)])
def test_idempotents_group_algebra_convolution(name, table):
    """Route 2 — per-element expansion via class_of, full convolution over
    the Cayley table.  Independent of class_algebra entirely."""
    ct = _ct(name, table)
    k, deg, order, phi = ct["k"], ct["degree"], ct["order"], ct["phi_e"]
    ci = central_idempotents(ct)
    num = ci["numerators"]
    class_of = ci["class_of"]
    n = len(table)
    e_idx = _identity_element(table)
    zero = (0,) * deg
    # per-element numerator: E[i][g] = num[i][class_of[g]]
    E = [[num[i][class_of[g]] for g in range(n)] for i in range(k)]
    for i in range(k):
        for j in range(k):
            conv = [[0] * deg for _ in range(n)]
            for x in range(n):
                for y in range(n):
                    prod = _zeta_mul(E[i][x], E[j][y], phi)
                    row = conv[table[x][y]]
                    for t in range(deg):
                        row[t] += prod[t]
            for g in range(n):
                if i == j:
                    want = tuple(order * c for c in E[i][g])
                else:
                    want = zero
                assert tuple(conv[g]) == want, (name, i, j, g)
    # Σ_i e_i = δ_e, per element
    for g in range(n):
        acc = [0] * deg
        for i in range(k):
            for t in range(deg):
                acc[t] += E[i][g][t]
        want = (order,) + (0,) * (deg - 1) if g == e_idx else zero
        assert tuple(acc) == want, (name, g)


def test_idempotents_value_anchors():
    """Q8's degree-2 idempotent is ½δ_e − ½δ₋₁ (numerators (4,0) at the
    identity class, (−4,0) at the other size-1 class, zero elsewhere, over
    denominator 8); S3's trivial idempotent is (1,0) at every class over
    denominator 6.  Classes located by CONTENT (size + identity column)."""
    ct = _ct("Q8", Q8)
    ci = central_idempotents(ct)
    two = ct["degrees"].index(2)
    id_class = _identity_class(ct)
    minus_one = [j for j in range(ct["k"])
                 if ct["class_sizes"][j] == 1 and j != id_class]
    assert len(minus_one) == 1
    for j in range(ct["k"]):
        if j == id_class:
            assert ci["numerators"][two][j] == (4, 0)
        elif j == minus_one[0]:
            assert ci["numerators"][two][j] == (-4, 0)
        else:
            assert ci["numerators"][two][j] == (0, 0)
    assert ci["denominator"] == 8

    ct = _ct("D3", D3)
    ci = central_idempotents(ct)
    triv = _trivial_row(ct)
    assert ci["numerators"][triv] == ((1, 0),) * ct["k"]
    assert ci["denominator"] == 6


def test_idempotents_negatives():
    """A perturbed numerator FAILS route-1 orthogonality (the corruption is
    detectable, executed); corrupt payload degrees → the in-op guard
    raises."""
    ct = _ct("D3", D3)
    k, deg, order, phi = ct["k"], ct["degree"], ct["order"], ct["phi_e"]
    A = ct["class_algebra"]
    ci = central_idempotents(ct)
    num = [list(row) for row in ci["numerators"]]
    cell = list(num[0][1])
    cell[0] += order                      # keep it plausible-sized
    num[0][1] = tuple(cell)
    broken = False
    for l in range(k):
        acc = [0] * deg
        for p in range(k):
            for q in range(k):
                if A[p][q][l]:
                    prod = _zeta_mul(num[0][p], num[0][q], phi)
                    w = A[p][q][l]
                    for t in range(deg):
                        acc[t] += w * prod[t]
        if tuple(acc) != tuple(order * c for c in num[0][l]):
            broken = True
    assert broken, "route-1 orthogonality failed to detect the perturbation"

    bad = dict(ct)
    bad["degrees"] = [2 if d == 1 else d for d in ct["degrees"]]
    with pytest.raises(ValueError):
        central_idempotents(bad)


def test_idempotents_column_orthogonality_guard_fires():
    """Corrupt one table cell in a NON-identity column so the column sums
    move → the in-op Σ e_i = δ_e (column-orthogonality) guard raises."""
    ct = _ct("Q8", Q8)
    non_id = next(j for j in range(ct["k"]) if j != _identity_class(ct))
    bad = _corrupt_cell(ct, 0, non_id)
    with pytest.raises(ValueError, match="column-orthogonality"):
        central_idempotents(bad)


# ── 5. cross-op identities + determinism ─────────────────────────────────

def test_content_addresses_are_deterministic_and_echoed():
    ct = _ct("D3", D3)
    a = frobenius_schur_indicator(ct)
    b = frobenius_schur_indicator(ct)
    assert a["indicators_sha256"] == b["indicators_sha256"]
    assert len(a["indicators_sha256"]) == 64
    assert a["table_sha256"] == ct["table_sha256"]
    fu = fusion_multiplicities(ct)
    assert fu["table_sha256"] == ct["table_sha256"]
    assert len(fu["multiplicities_sha256"]) == 64
    ci = central_idempotents(ct)
    assert ci["table_sha256"] == ct["table_sha256"]
    assert len(ci["idempotents_sha256"]) == 64
    assert ci["phi_e"] == ct["phi_e"]


def test_fs_num_counts_partition_k():
    for name, table in ALL_GROUPS:
        fs = frobenius_schur_indicator(_ct(name, table))
        assert (fs["num_real"] + fs["num_complex"]
                + fs["num_quaternionic"]) == fs["k"], name
        for field in ("num_real", "num_complex", "num_quaternionic",
                      "square_roots_of_identity", "k", "order"):
            value = fs[field]
            assert isinstance(value, int) and not isinstance(value, bool), \
                (name, field)
