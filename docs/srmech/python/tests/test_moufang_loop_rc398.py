"""rc398 (`#T1064`) — the octonion MOUFANG LOOP surface.

𝕆 is a Moufang loop and srmech ships it twice with C parity, but the three
Moufang identities were proven ONLY inside ``test_loop_bind_moufang.py``, the
Mal'cev-not-Lie tangent fact likewise, and the 16-element unit loop M16 lived
only as the unnamed DATA ``closure(8, [1..7])``. This gate exercises the five
ops that promote that latent, proven machinery to first-class queryable ops:
``moufang_residue`` / ``is_moufang`` / ``malcev_defect`` / ``unit_loop`` /
``loop_invariants``.

Exact-ℚ end to end (Class-K clean — zero-tests via ⟨v,v⟩, never ``abs()``);
this test is itself numpy-free (the numpy-absent CI cell), per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`.
"""
from __future__ import annotations

from srmech.cascade import (
    moufang_residue,
    is_moufang,
    malcev_defect,
    unit_loop,
    loop_invariants,
    cd_basis,
    cd_mult,
    associator,
    algebra_table,
)
from srmech.cascade.cayley_dickson import closure
from srmech.math.q import Q


# ── moufang_residue: 0 on 𝕆, nonzero on the sedenion control ──────────

def test_moufang_residue_zero_on_all_octonion_basis_triples():
    b = [cd_basis(8, i) for i in range(8)]
    for i in range(8):
        for j in range(8):
            for k in range(8):
                assert moufang_residue(b[i], b[j], b[k]) == 0


def test_moufang_residue_nonzero_on_sedenion_control():
    s = [cd_basis(16, i) for i in range(16)]
    # 𝕊 is not even alternative, so not Moufang; (e1,e2,e12) is a witness.
    assert moufang_residue(s[1], s[2], s[12]) == 4


def test_moufang_residue_exact_Q_not_float():
    e = [cd_basis(8, i) for i in range(8)]
    r = moufang_residue(e[1], e[2], e[4])
    assert isinstance(r, Q)


def test_moufang_residue_split_octonion_still_moufang():
    # split-𝕆 IS alternative, so it stays Moufang (residue 0) — table= reaches it.
    e = [cd_basis(8, i) for i in range(8)]
    split = algebra_table(8, [1, -1, -1])
    assert moufang_residue(e[1], e[2], e[4], table=split) == 0


# ── is_moufang: whole-loop boolean, True to 𝕆, False from 𝕊 ───────────

def test_is_moufang_true_through_octonions():
    assert is_moufang(dim=2) is True   # ℂ
    assert is_moufang(dim=4) is True   # ℍ
    assert is_moufang(dim=8) is True   # 𝕆 — non-associative yet Moufang


def test_is_moufang_false_on_sedenion():
    assert is_moufang(dim=16) is False


def test_is_moufang_reads_split_octonion_table():
    # split-𝕆 is alternative → still a Moufang loop.
    assert is_moufang(table=algebra_table(8, [1, -1, -1])) is True


# ── malcev_defect: Mal'cev-not-Lie tangent algebra ────────────────────

def test_malcev_not_lie_on_octonions():
    e = [cd_basis(8, i) for i in range(8)]
    d = malcev_defect(e[1], e[2], e[4])
    assert d["jacobi"] == 144      # J = 12·e7 ⇒ not a Lie algebra
    assert d["malcev"] == 0        # the weaker Mal'cev identity holds


def test_malcev_holds_on_every_octonion_basis_triple():
    # The Mal'cev identity is a Mal'cev-algebra law: 0 on every triple.
    b = [cd_basis(8, i) for i in range(8)]
    worst_jacobi = Q(0)
    for i in range(8):
        for j in range(8):
            for k in range(8):
                d = malcev_defect(b[i], b[j], b[k])
                assert d["malcev"] == 0
                if d["jacobi"] > worst_jacobi:
                    worst_jacobi = d["jacobi"]
    assert worst_jacobi > 0        # some triple fails Jacobi ⇒ NOT Lie


# ── unit_loop: the named M16 handle + Cayley table ────────────────────

def test_unit_loop_m16_named_and_ordered():
    U = unit_loop(8)
    assert U["name"] == "M16"
    assert U["order"] == 16
    assert U["dim"] == 8
    assert U["elements"][:3] == [(1, 0), (1, 1), (1, 2)]


def test_unit_loop_elements_are_the_closure_result():
    # NOT duplicated data — the ordered closure(8,[1..7]).
    U = unit_loop(8)
    assert set(U["elements"]) == closure(8, list(range(1, 8)))


def test_unit_loop_cayley_is_a_latin_square():
    U = unit_loop(8)
    rows = U["cayley_table"]
    assert len(rows) == 16 and all(len(r) == 16 for r in rows)
    for r in rows:                                  # every row a permutation
        assert sorted(r) == list(range(16))
    for c in range(16):                             # every column a permutation
        assert sorted(rows[i][c] for i in range(16)) == list(range(16))


def test_unit_loop_dim4_is_the_quaternion_group_q8():
    Q8 = unit_loop(4)
    assert Q8["name"] == "Q8"
    assert Q8["order"] == 8


# ── loop_invariants: nucleus / commutant / center + Mlt(L) ────────────

def test_m16_nucleus_commutant_center_are_plus_minus_one():
    inv = loop_invariants(8)
    assert inv["nucleus"] == [(1, 0), (-1, 0)]      # {±1}
    assert inv["commutant"] == [(1, 0), (-1, 0)]
    assert inv["center"] == [(1, 0), (-1, 0)]


def test_loop_invariants_mlt_generators_are_permutations():
    inv = loop_invariants(8)
    left, right = inv["left_translations"], inv["right_translations"]
    assert len(left) == 16 and len(right) == 16
    for perm in left + right:
        assert sorted(perm) == list(range(16))


def test_associator_is_minus_left_right_translation_commutator():
    # The surfaced identity: associator(a, x, b) = −[L_a, R_b]·x.
    a, x, b = cd_basis(8, 1), cd_basis(8, 4), cd_basis(8, 2)
    lhs = associator(a, x, b)                        # (a·x)·b − a·(x·b)
    LRx = [p - q for p, q in                         # [L_a,R_b]x = a·(x·b) − (a·x)·b
           zip(cd_mult(a, cd_mult(x, b)), cd_mult(cd_mult(a, x), b))]
    assert list(lhs) == [-v for v in LRx]


# ── discipline: registered as composition_of_c, exact, no new C symbol ─

def test_registered_and_composition_of_c():
    import json
    from pathlib import Path
    from srmech.introspect.tool_schema import get_tool_schema

    names = {e.name for e in get_tool_schema().tools}
    for op in ("moufang_residue", "is_moufang", "malcev_defect", "unit_loop",
               "loop_invariants"):
        assert f"srmech.cascade.{op}" in names

    ledger = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
    buckets = {}
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        buckets[row["exposed_as"]] = row["bucket"]
    for op in ("moufang_residue", "is_moufang", "malcev_defect", "unit_loop",
               "loop_invariants"):
        assert buckets[f"srmech.cascade.{op}"] == "composition_of_c"
