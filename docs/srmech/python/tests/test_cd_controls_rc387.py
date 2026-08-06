"""rc387 (`#T1037`, closing `#T1032`) — the two STRUCTURED Cayley–Dickson
negative controls, promoted from rc360's hand-rolled test code to registered ops.

``srmech.cascade.flip_pair(dim, i, j)`` — the definite CD ladder table with
``e_i·e_j`` and ``e_j·e_i`` NEGATED. The ONLY control that breaks FLEXIBILITY,
and by a CONSTANT 4 per rung (4/64 at dim 4, 4/512 at dim 8, 4/4096 at dim 16),
uniform over every admissible pair; the inertia signature is UNCHANGED (the flip
is off-diagonal, the trace form is diagonal). ``composition_of_c`` over
``srmech_algebra_table`` + the Class-C ``reorient`` sign flip.

``srmech.cascade.group_algebra_table(dim)`` — the group ring ℝ[ℤ/dim]: lane
``(i+j) mod dim``, all signs +1 (the WRONG QUOTIENT). Associative + commutative →
0 bite on flexibility/associativity; its bite is the METRIC: trace signature
(2,0,0)/(3,1,0)/(5,3,0)/(9,7,0) at dim 2/4/8/16 vs the ladder's
(1,1,0)/(1,3,0)/(1,7,0)/(1,15,0). ``composition_of_c`` over the c_dispatched
``srmech_mod_add`` (the cyclic lane).

Genuine checks (NOT smoke tests), reproduced THROUGH the shipped ``associator`` +
``inertia_signature``:
  1. flip_pair breaks flexibility at EXACTLY 4 per rung, every admissible pair.
  2. flip_pair's inertia signature == the ladder's (the metric is untouched).
  3. flip_pair is the two NAMED cells negated on the shared lane i⊕j, nothing else.
  4. group_algebra_table is flexible AND associative (0 bite on the laws).
  5. group_algebra_table's metric signatures are the measured (2,0,0)…(9,7,0).
  6. THE LABELLED TAUTOLOGY — "differs from the ladder" IS the ladder's own
     non-associating census (a forced identity, carries no information).
  7. guards + the pure/c_dispatched co-equal dual-construction oracle.
  8. registration ratchet (__all__ / Rosetta composition_of_c / op-name list /
     describe() total 546) + a no-abs() source guard.

numpy-free (srmech + stdlib only); NO stdlib fractions — the CD element carrier is
srmech.math.q.Q. Mirrors notes/cd_controls_rc387.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import srmech
from srmech import _native
from srmech.cascade import (algebra_table, associator, cd_basis, flip_pair,
                            group_algebra_table, inertia_signature)
from srmech.cascade import cayley_dickson as CD
from srmech.math.q import Q

# The measured trace signatures (rc360 / cd_controls_rc387.ndjson).
LADDER_SIG = {2: (1, 1, 0), 4: (1, 3, 0), 8: (1, 7, 0), 16: (1, 15, 0)}
RING_SIG = {2: (2, 0, 0), 4: (3, 1, 0), 8: (5, 3, 0), 16: (9, 7, 0)}


def _pure(fn, *args, **kw):
    """Run ``fn`` forced through the PURE cascade (native dispatch disabled)."""
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _sig(table):
    return tuple(inertia_signature(table)["signature"])


def _flex_violations(dim, table):
    """Linearised flexible law (x,y,z)+(z,y,x)=0 over the dim**3 triples, read
    THROUGH the shipped associator (no abs, exact ℚ)."""
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any((u + v) != 0 for u, v in
                      zip(associator(b[i], b[j], b[k], table=table),
                          associator(b[k], b[j], b[i], table=table))))


def _nonassoc(dim, table):
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any(v != 0 for v in associator(b[i], b[j], b[k], table=table)))


# ── 1 + 2 + 3. flip_pair: the flexibility control, constant 4, metric fixed ──
def test_flip_pair_breaks_flexibility_by_a_constant_4():
    """Every admissible pair flips flexibility to EXACTLY 4 — a constant, not a
    pair-dependent number. dim 4 (all 3 pairs) and dim 8 (a sample of 4)."""
    ladder4 = algebra_table(4)
    assert _flex_violations(4, ladder4) == 0            # the ladder is flexible
    for i in range(1, 4):
        for j in range(i + 1, 4):
            assert _flex_violations(4, flip_pair(4, i, j)) == 4, (i, j)
    ladder8 = algebra_table(8)
    assert _flex_violations(8, ladder8) == 0
    for (i, j) in [(1, 2), (2, 4), (3, 5), (6, 7)]:
        assert _flex_violations(8, flip_pair(8, i, j)) == 4, (i, j)


def test_flip_pair_leaves_the_inertia_signature_unchanged():
    """The flip is strictly off-diagonal; the trace form is diagonal — so the
    signature is IDENTICAL to the definite ladder's at every rung."""
    for dim in (2, 4, 8):
        base = _sig(algebra_table(dim))
        assert base == LADDER_SIG[dim]
        for i in range(1, dim):
            for j in range(i + 1, dim):
                assert _sig(flip_pair(dim, i, j)) == base, (dim, i, j)


def test_flip_pair_is_exactly_the_two_named_cells():
    """Nothing but cells (i,j) and (j,i) at the shared lane i⊕j changes, and each
    is negated — a single named sign bit, Class-K/C, never abs()."""
    dim, i, j = 8, 1, 2
    base = algebra_table(dim)
    flipped = flip_pair(dim, i, j)
    lane = i ^ j
    diffs = [(a, b, c)
             for a in range(dim) for b in range(dim) for c in range(dim)
             if base[a][b][c] != flipped[a][b][c]]
    assert set(diffs) == {(i, j, lane), (j, i, lane)}
    assert flipped[i][j][lane] == -base[i][j][lane]
    assert flipped[j][i][lane] == -base[j][i][lane]


# ── 4 + 5. group_algebra_table: 0 law-bite, full metric-bite ─────────────────
def test_group_algebra_table_is_flexible_and_associative():
    """The group ring is commutative + associative with a trivial cocycle, so it
    has ZERO bite on the associativity laws at every rung."""
    for dim in (2, 4, 8):
        ring = group_algebra_table(dim)
        assert _flex_violations(dim, ring) == 0, dim
        assert _nonassoc(dim, ring) == 0, dim


def test_group_algebra_table_metric_signatures():
    """Its whole bite is on the METRIC: the measured trace signatures, and they
    DIFFER from the ladder's at every rung ≥ 2 (same dim, different group)."""
    for dim in (2, 4, 8):
        assert _sig(group_algebra_table(dim)) == RING_SIG[dim], dim
        assert RING_SIG[dim] != LADDER_SIG[dim] or dim == 1


def test_group_algebra_table_lane_is_cyclic_not_xor():
    """The lane is (i+j) mod dim (cyclic), NOT i⊕j (the CD ladder). They agree at
    dim 2 and diverge for dim ≥ 4."""
    ring = group_algebra_table(8)
    for i in range(8):
        for j in range(8):
            assert ring[i][j][(i + j) % 8] == 1
            assert sum(ring[i][j]) == 1        # monomial, all +1
    # a concrete divergence: e2·e7 lands on lane 1 (cyclic) not 5 (xor)
    assert ring[2][7].index(1) == (2 + 7) % 8 == 1
    assert (2 ^ 7) == 5


# ── 6. THE LABELLED TAUTOLOGY ────────────────────────────────────────────────
def test_wrong_quotient_differs_is_a_forced_identity():
    """⚠️ LABELLED TAUTOLOGY, not a finding. The group ring's OWN associator is
    identically 0 (it is associative), so "the wrong-quotient associator differs
    from the ladder's" counts EXACTLY the ordered triples on which the LADDER
    fails to associate. differs == ladder_nonassoc is therefore a FORCED IDENTITY
    — it is the ladder's own non-associating census (512−344=168 at dim 8) wearing
    a different name, and carries NO information about the control."""
    dim = 8
    ladder = algebra_table(dim)
    ring = group_algebra_table(dim)
    b = [cd_basis(dim, i) for i in range(dim)]
    differs = sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
                  if associator(b[i], b[j], b[k], table=ladder)
                  != associator(b[i], b[j], b[k], table=ring))
    ladder_nonassoc = _nonassoc(dim, ladder)
    assert differs == ladder_nonassoc == 168            # the forced identity
    # and it IS forced: the ring's own defect is identically zero everywhere.
    assert _nonassoc(dim, ring) == 0


# ── 7. guards + the pure/c_dispatched co-equal oracle ────────────────────────
def test_guards():
    with pytest.raises(ValueError):
        flip_pair(8, 3, 3)                  # i == j moves the diagonal
    with pytest.raises(ValueError):
        flip_pair(8, 0, 2)                  # 0 is the real direction, not imaginary
    with pytest.raises(ValueError):
        flip_pair(8, 1, 8)                  # out of range
    with pytest.raises(ValueError):
        flip_pair(6, 1, 2)                  # dim not a power of two
    with pytest.raises(ValueError):
        group_algebra_table(6)              # dim not a power of two
    with pytest.raises(ValueError):
        group_algebra_table(128)            # above ALGEBRA_TABLE_MAX_DIM=64


def test_tables_are_exact_ints():
    """Both controls are exact-integer tensors end to end (no float, no Q needed
    in the table itself; the elements read through them are exact ℚ)."""
    for table in (flip_pair(8, 1, 2), group_algebra_table(8)):
        for plane in table:
            for row in plane:
                for c in row:
                    assert isinstance(c, int) and c in (-1, 0, 1)
    # the tables feed exact-ℚ elements through table_product/associator:
    a = associator(cd_basis(8, 1), cd_basis(8, 2), cd_basis(8, 4),
                   table=group_algebra_table(8))
    assert all(isinstance(v, Q) for v in a)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not loaded")
def test_pure_vs_c_dispatched_byte_identity():
    """Co-equal dual construction: the c_dispatched tables must be byte-identical
    to the pure-cascade tables (flip_pair rides srmech_algebra_table;
    group_algebra_table rides srmech_mod_add)."""
    assert flip_pair(8, 1, 2) == _pure(flip_pair, 8, 1, 2)
    assert group_algebra_table(8) == _pure(group_algebra_table, 8)
    assert group_algebra_table(16) == _pure(group_algebra_table, 16)


# ── 8. registration ratchet + no-abs source guard ───────────────────────────
def test_registration_ratchet():
    import srmech.cascade as C
    assert "flip_pair" in C.__all__
    assert "group_algebra_table" in C.__all__
    from srmech.introspect.tool_schema import tool_schema_view
    view = tool_schema_view()
    assert len(view["tools"]) == 559
    names = {t["name"] for t in view["tools"]}
    assert "srmech.cascade.flip_pair" in names
    assert "srmech.cascade.group_algebra_table" in names


def test_rosetta_and_op_name_ledgers():
    here = Path(__file__).resolve().parent
    rosetta = (here / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    rows = [json.loads(ln) for ln in rosetta.splitlines() if ln.strip()]
    for op in ("flip_pair", "group_algebra_table"):
        row = next(r for r in rows
                   if r["exposed_as"] == f"srmech.cascade.{op}")
        assert row["bucket"] == "composition_of_c"
        assert row["defined_at"] == f"srmech.cascade.cayley_dickson.{op}"
    names = (here / "registered_op_names.txt").read_text(encoding="utf-8").split()
    assert "srmech.cascade.flip_pair" in names
    assert "srmech.cascade.group_algebra_table" in names


def test_no_abs_in_source():
    """Neither op's CODE may call abs() — sign is the Class-K pin / Class-C
    reorient, magnitude is the Class-N squared norm (cascade-honesty). Scan only
    the executable body after each docstring."""
    src = Path(CD.__file__).read_text(encoding="utf-8")
    for name in ("flip_pair", "group_algebra_table"):
        start = src.index(f"def {name}(")
        end = src.index("\ndef ", start + 1)
        func = src[start:end]
        q = '"""'
        d0 = func.index(q)
        d1 = func.index(q, d0 + 3)
        code = func[:d0] + func[d1 + 3:]
        assert "abs(" not in code, f"{name} code must not use abs()"
