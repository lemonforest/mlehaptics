"""rc383 (`#T1054`) — ``defect_ladder``: the property-loss ladder in ONE pass + a
per-rung PROJECTOR.

WHAT LANDED
===========
``cascade.defect_ladder(x, y, z, table=None)`` — reads the whole Cayley–Dickson
property-loss ladder over the SAME three inputs (commutator [x,y], associator
[x,y,z], left alternator [x,x,y], flexibility floor [x,y,x], plus the
cycle-holonomy closed-read) and returns a per-rung PROJECTOR: ``rung_admits``
(structural mask) and ``projected`` (only the rung-meaningful defects). It is the
CD instance of the cross-substrate "declared-parallel-state ⊗ projector-excitation
→ rung-meaningful subset" instrument (QM measurement / genome chromatin / music
fingerboard are the domain peers — see notebook §3.29 + the rc383 provenance
script).

WHY EACH CHECK BELOW IS A DIFFERENTIAL AND NOT A TAUTOLOGY
==========================================================
* the FOUR defect fields are asserted EQUAL to the independently-called composer
  ops (cd_commutator / associator ×3 / cd_cycle_holonomy) — the ladder is exactly
  that composition, stated in the one place it cannot be mistaken for a
  measurement;
* the commutator census read THROUGH the ladder is compared to the CLOSED FORM
  ``(dim−1)(dim−2)`` (independent of the op);
* the RUNG-STAGGER (commutator on from ℍ, associator on from 𝕆) is asserted as
  the projector mask, and against a direct associator sweep;
* ⚠️ RUNG 4 IS NOT BASIS-VISIBLE: the basis-only left-alternator is 0 at 𝕊 while a
  SEAM-CROSSING a=e1+e10 makes [a,a,e4]=2·e15 — the crux that a basis-only probe
  falsely reports 𝕊 alternative;
* the ``table=`` split-octonion negative control reaches a genuinely different
  algebra;
* the export + Rosetta ``composition_of_c`` trap.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srmech.cascade import (algebra_table, associator, cd_add, cd_basis,
                                 cd_commutator, cd_cycle_holonomy, cd_mult,
                                 defect_ladder)
from srmech.math.q import Q


# ══════════════════════════════════════════════════════════════════════
# the four defect fields ARE the composed ops (the honest-composition identity)
# ══════════════════════════════════════════════════════════════════════

def test_defect_fields_are_the_composer_ops():
    """⚠️ THE COMPOSITION IDENTITY. Over every dim-4 basis triple and concrete
    dim-8 triples, each ladder field EQUALS the op it composes — stated as the
    identity it is, so the ladder cannot silently diverge from its parts."""
    for dim in (4, 8):
        b = [cd_basis(dim, i) for i in range(dim)]
        # dim 4: exhaustive; dim 8: a representative slice (i<3) to stay fast.
        irange = range(dim) if dim == 4 else range(3)
        for i in irange:
            for j in range(dim):
                for k in range(dim):
                    x, y, z = b[i], b[j], b[k]
                    r = defect_ladder(x, y, z)
                    assert r["defects"]["commutator"] == cd_commutator(x, y)
                    assert r["defects"]["associator"] == associator(x, y, z)
                    assert r["defects"]["flexibility"] == associator(x, y, x)
                    assert r["defects"]["left_alternator"] == associator(x, x, y)
                    assert r["holonomy_closed"] == cd_cycle_holonomy(x, y, z)["closed"]


def test_nonzero_flags_track_the_defect_tuples():
    """``nonzero[name]`` is True iff that defect tuple has a nonzero entry."""
    r = defect_ladder(cd_basis(8, 1), cd_basis(8, 2), cd_basis(8, 4))
    for name, tup in r["defects"].items():
        assert r["nonzero"][name] == any(v != 0 for v in tup)


# ══════════════════════════════════════════════════════════════════════
# the RUNG-indexed ladder — turn-on stagger read through the projector
# ══════════════════════════════════════════════════════════════════════

def _commutator_noncommuting(dim: int, table=None) -> int:
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim)
               if defect_ladder(b[i], b[j], b[0], table=table)["nonzero"]["commutator"])


def test_commutator_census_through_ladder_matches_closed_form():
    """The commutator field, censused THROUGH defect_ladder, reproduces
    ``(dim−1)(dim−2)`` — 0/0/6/42/210 at ℝ/ℂ/ℍ/𝕆/𝕊 — against a closed form
    derived from the anticommutation structure, not from the op."""
    for dim in (1, 2, 4, 8, 16):
        assert _commutator_noncommuting(dim) == (dim - 1) * (dim - 2), dim


def test_associator_turns_on_one_rung_above_the_commutator():
    """⚠️ THE STAGGER. The associator field is identically 0 through ℍ and only
    fires from 𝕆 (168/512) — one rung ABOVE the commutator, which is what makes
    the ladder a ladder and not a restatement."""
    for dim in (2, 4):
        b = [cd_basis(dim, i) for i in range(dim)]
        assert all(not defect_ladder(b[i], b[j], b[k])["nonzero"]["associator"]
                   for i in range(dim) for j in range(dim) for k in range(dim)), dim
    b8 = [cd_basis(8, i) for i in range(8)]
    n8 = sum(1 for i in range(8) for j in range(8) for k in range(8)
             if defect_ladder(b8[i], b8[j], b8[k])["nonzero"]["associator"])
    assert n8 == 168


def test_rung_admits_mask_is_purely_structural():
    """``rung_admits`` is a function of the RUNG alone (not the operands): order@1
    from ℂ, commutativity@2 from ℍ, associativity@3 from 𝕆, alt_zero_div@4 from
    𝕊 — and ``projected`` is exactly the admitted, non-floor defects."""
    expected = {1: [], 2: ["commutator"], 3: ["associator", "commutator"],
                4: ["associator", "commutator", "left_alternator"]}
    for dim, rung in ((2, 1), (4, 2), (8, 3), (16, 4)):
        r = defect_ladder(cd_basis(dim, 0), cd_basis(dim, 0), cd_basis(dim, 0))
        assert r["rung"] == rung
        assert r["rung_admits"]["order@1"] is True
        assert r["rung_admits"]["commutativity@2"] is (rung >= 2)
        assert r["rung_admits"]["associativity@3"] is (rung >= 3)
        assert r["rung_admits"]["alt_zero_div@4"] is (rung >= 4)
        assert sorted(r["projected"]) == expected[rung]
        # flexibility is the FLOOR — never admitted into the projected subset
        assert "flexibility" not in r["projected"]


def test_flexibility_is_the_floor_never_fires():
    """[x,y,x] = 0 at every rung — the floor beneath the whole ladder."""
    for dim in (2, 4, 8):
        b = [cd_basis(dim, i) for i in range(dim)]
        assert all(not defect_ladder(b[i], b[j], b[min(1, dim - 1)])["nonzero"]["flexibility"]
                   for i in range(dim) for j in range(dim)), dim


# ══════════════════════════════════════════════════════════════════════
# ⚠️ RUNG 4 IS NOT BASIS-VISIBLE — the 𝕊 seam-crossing crux
# ══════════════════════════════════════════════════════════════════════

def test_rung4_needs_a_seam_crosser_not_a_basis_probe():
    """A basis-only left-alternator [e_i,e_i,e_j] is 0 at 𝕊 exactly as at 𝕆 — so a
    basis probe FALSELY reports 𝕊 alternative. The failure needs a
    DOUBLING-SEAM-CROSSING input: a=e1+e10 gives [a,a,e4]=2·e15, and admits @4."""
    # basis-only probe: all zero (the false-negative a naive check would hit).
    b = [cd_basis(16, i) for i in range(16)]
    assert all(
        not defect_ladder(b[i], b[i], b[j])["nonzero"]["left_alternator"]
        for i in range(16) for j in range(16))
    # seam-crosser a = e1 + e10: the associator [a,a,e4] = 2·e15.
    a = cd_add(cd_basis(16, 1), cd_basis(16, 10))
    seam = defect_ladder(a, a, cd_basis(16, 4))
    assert seam["rung"] == 4
    assert seam["rung_admits"]["alt_zero_div@4"] is True
    assert seam["defects"]["associator"] == tuple(
        Q(2) if k == 15 else Q(0) for k in range(16))


def test_seam_crosser_is_a_zero_divisor():
    """The same seam element makes (e1+e10)(e4−e15)=0 — the zero-divisor half of
    the rung-4 loss (composition/division fails at 𝕊), read via cd_mult."""
    a = cd_add(cd_basis(16, 1), cd_basis(16, 10))
    y = tuple(Q(1) if k == 4 else (Q(-1) if k == 15 else Q(0)) for k in range(16))
    assert all(v == 0 for v in cd_mult(a, y))


# ══════════════════════════════════════════════════════════════════════
# table= reaches a genuinely different algebra (the STRUCTURED negative control)
# ══════════════════════════════════════════════════════════════════════

def test_ladder_reads_split_octonion_through_table():
    """table= sends the ladder onto a split γ-twist: still 42 noncommuting pairs
    at dim 8 (anticommutation survives), but its associator defect differs from
    the definite 𝕆 on 96/512 triples — a genuinely second algebra."""
    split = algebra_table(8, [1, -1, -1])
    assert _commutator_noncommuting(8, table=split) == 42
    b = [cd_basis(8, i) for i in range(8)]
    differ = sum(1 for i in range(8) for j in range(8) for k in range(8)
                 if defect_ladder(b[i], b[j], b[k])["defects"]["associator"]
                 != defect_ladder(b[i], b[j], b[k], table=split)["defects"]["associator"])
    assert differ == 96


# ══════════════════════════════════════════════════════════════════════
# operand validation (surfaced by the composed ops)
# ══════════════════════════════════════════════════════════════════════

def test_defect_ladder_rejects_mismatched_operands():
    with pytest.raises(ValueError, match="share dimension"):
        defect_ladder([1, 0], [1, 0], [1, 0, 0, 0])
    with pytest.raises(ValueError, match="power-of-two"):
        defect_ladder([1, 0, 0], [1, 0, 0], [1, 0, 0])
    with pytest.raises(ValueError, match="the table is dim"):
        defect_ladder([1, 0], [1, 0], [1, 0], table=algebra_table(4))


# ══════════════════════════════════════════════════════════════════════
# exported AND classified (the __all__ / Rosetta trap)
# ══════════════════════════════════════════════════════════════════════

def test_new_op_is_exported_and_classified():
    """A new public name is invisible to the ledger walk unless it is exported AND
    carries a Rosetta bucket. defect_ladder composes the c_dispatched defect ops,
    so it is ``composition_of_c`` — never a new C symbol."""
    import srmech.cascade as cascade
    assert "defect_ladder" in cascade.__all__
    ledger = (Path(__file__).resolve().parent
              / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    name = "srmech.cascade.cayley_dickson.defect_ladder"
    assert f'"{name}"' in ledger, f"{name} has no Rosetta bucket"
    row = next(l for l in ledger.splitlines() if f'"{name}"' in l)
    assert '"bucket": "composition_of_c"' in row, row
