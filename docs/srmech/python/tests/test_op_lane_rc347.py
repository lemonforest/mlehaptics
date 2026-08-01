"""rc347 (`#T985`) — a declared LANE must be one a perturbation can CONTRADICT.

THE FALSE GREEN THIS EXISTS TO CATCH
------------------------------------
**A declared lane that nothing verifies.** That is exactly the shape rc339
shipped and rc343 removed: ``limits["capabilities"]["turn"]["bounded_by"] =
"associativity"`` asserted a property with no test that could contradict it,
because ``turn`` is DEFINED as the associativity condition. Anything
associative turns; anything that turns is associative; no carrier row could
falsify the field.

``ToolEntry.reads_lane`` is a claim of exactly that kind — "this op reads the
sign lane" — so it needs exactly that kind of rule. This module IS the rule,
and it is executable rather than documentary.

THE VERIFIER
------------
It rests on one measured fact: **CHIRALITY TOUCHES THE SIGN LANE ONLY.** Over
the basis products, three independent chirality operators move signs and move
ZERO indices — order reversal (the opposite algebra) 6/16 at H, 42/64 at O,
210/256 at S; ``cd_conjugate`` 14/64; ``q8_conjugate`` 24/64 — while the index
lane is ``i XOR j`` with zero violations at every rung (4/4, 16/16, 64/64,
256/256, and 64/64 on the shipped ``q8_mult``). So the two lanes can be
perturbed SEPARATELY, which is what makes a lane declaration falsifiable::

    SIGN-lane perturbation   algebra:  XOR the Q8 center bit (q ^ 4)
                             geometry: reverse orientation (reflect one axis)
    INDEX-lane perturbation  algebra:  relabel the V4 coset by rho in
                                       Aut(V4) = S3, sign bit fixed
                             geometry: positive-rational rescale (magnitude)

and the rule is:

* declares ``sign``  -> MOVES under the sigma flip, DOES NOT MOVE under the
  index relabel
* declares ``index`` -> MOVES under the index relabel, DOES NOT MOVE under the
  sigma flip
* declares ``both``  -> MOVES under both

An op declaring "sign only" that moves under a pure index relabel is
MIS-DECLARED and this module turns the build red.

**Applicability is half the rule.** An op may declare only if BOTH
perturbations can be built for its input. ``cascade.net_chirality`` takes bare
orientations (no index to move) and ``cascade.cd_basis_product`` takes bare
indices (no sign to move), so neither may declare — not because the answer is
unknown but because no measurement could contradict it, which is the defect
being removed rather than relocated.

**Verdicts are SWEPT, never sampled.** A single input can miss a real response:
an even number of sign flips CANCELS inside an ordered product, and only about
one gain vector in fifteen exposes the Lk index response. The first draw of the
rc347 probe reported ``cwf_consistency_mod2`` as index-blind on that basis, and
would have shipped a wrong declaration that this file would then have blessed.

No float, no numpy, no ``abs()`` — a sign is a Class-K pin-slot read composed
with Class C.

Generating code + NDJSON: ``docs/srmech/notes/op_lane_axis_rc347.py``.
"""

from __future__ import annotations

import itertools
import random
from fractions import Fraction

import pytest

from srmech.biology import genome as _genome
from srmech.biology import q8 as _q8
from srmech.amsc.cascade.cayley_dickson import cd_basis_product
from srmech.introspect.tool_schema import (
    LANE_INPUTS,
    LANES,
    ToolEntry,
    ToolSchemaValidationError,
    get_tool_schema,
    warmup_all,
)
from srmech.introspect import describe
from srmech.qm.quaternion import quaternion_cycle_holonomy

# ── the lane projections on a Q8 byte (srmech's layout, not this file's) ──
# q8_project_v4 IS `q & 3`; q8_mult documents `s = q >> 2`.
Q8_INDEX = 3
Q8_SIGN = 4

#: Aut(V4) = S3 — fixes the identity coset 0, permutes {1, 2, 3}.
RHOS = [(0,) + p for p in itertools.permutations((1, 2, 3))]

#: A 6-node cycle: exactly ONE fundamental cycle, which cwf_consistency_mod2
#: requires, and node k indexes _EMB[k].
_EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]

#: A generic 6-vertex backbone with NON-ZERO writhe (-1). Non-zero is
#: load-bearing: a writhe-0 embedding is reflection-invariant for the trivial
#: reason and would read as "discrete_writhe ignores orientation".
_EMB = [(1, 5, 0), (-7, -6, 7), (4, -4, 1), (-5, 6, 4), (-8, -7, 8), (9, 1, 1)]

#: Five positive rational scale factors, including a shrink and a non-integer.
_RESCALES = ((1, 1), (3, 1), (100, 1), (1, 7), (999, 4))


def _sigma(q: int) -> int:
    """SIGN-lane perturbation: flip the center bit. Index untouched."""
    return q ^ Q8_SIGN


def _relabel(q: int, rho) -> int:
    """INDEX-lane perturbation: relabel the V4 coset by rho. Sign untouched."""
    return (q & Q8_SIGN) | rho[q & Q8_INDEX]


def _gain(q: int):
    """Q8 byte -> unit-quaternion 4-vector for the qm.quaternion surface."""
    s = -1 if (q >> 2) & 1 else 1
    x = q & Q8_INDEX
    v = [0, 0, 0, 0]
    v[x] = s
    return v


def _reflect(emb):
    return [(-x, y, z) for (x, y, z) in emb]


def _rescale(emb, num, den):
    return [(Fraction(x * num, den), Fraction(y * num, den),
             Fraction(z * num, den)) for (x, y, z) in emb]


# ══════════════════════════════════════════════════════════════════════
# 0. The perturbations themselves move ONE lane each
# ══════════════════════════════════════════════════════════════════════


def test_each_perturbation_moves_exactly_one_lane() -> None:
    """The verifier's own precondition. If sigma moved an index, every
    "sign-only" verdict below would be an artifact of the instrument."""
    for q in range(8):
        s, r = _sigma(q), _relabel(q, RHOS[2])
        assert (s & Q8_INDEX) == (q & Q8_INDEX), f"sigma moved the index of {q}"
        assert (s >> 2) != (q >> 2), f"sigma did not move the sign of {q}"
        assert (r >> 2) == (q >> 2), f"relabel moved the sign of {q}"
    # rho must actually relabel something, or the index perturbation is a no-op
    # and every "index-blind" verdict is vacuous.
    assert any(_relabel(q, RHOS[2]) != q for q in range(8))


def test_index_lane_is_xor_at_every_granularity() -> None:
    """The INDEX lane is Z_2^n under XOR, exact at every rung — which is why
    lane is ORTHOGONAL to granularity: the same statement holds at every
    addressing width."""
    for dim in (2, 4, 8, 16):
        for i in range(dim):
            for j in range(dim):
                idx, sign = cd_basis_product(dim, i, j)
                assert idx == (i ^ j), (dim, i, j, idx)
                assert sign in (1, -1)
    for a in range(8):
        for b in range(8):
            assert (_q8.q8_mult(a, b) & Q8_INDEX) == (
                (a & Q8_INDEX) ^ (b & Q8_INDEX))


def test_chirality_moves_signs_and_never_an_index() -> None:
    """Order reversal is the purest statement of the split: the index lane is
    order-BLIND, the sign lane order-CARRYING. Measured 6/16 at H, 42/64 at O,
    210/256 at S — and 0 index moves at all three."""
    expected_sign_moves = {4: 6, 8: 42, 16: 210}
    for dim, want in expected_sign_moves.items():
        moved = 0
        for i in range(dim):
            for j in range(dim):
                ia, sa = cd_basis_product(dim, i, j)
                ib, sb = cd_basis_product(dim, j, i)
                assert ia == ib, f"order reversal moved an index at dim {dim}"
                if sa != sb:
                    moved += 1
        assert moved == want, (dim, moved, want)


# ══════════════════════════════════════════════════════════════════════
# 1. The closed vocabulary is actually closed
# ══════════════════════════════════════════════════════════════════════


def test_lane_vocabulary_is_closed_and_rejects_at_registration() -> None:
    with pytest.raises(ToolSchemaValidationError):
        ToolEntry(name="t", owner="srmech", category="c", summary="s",
                  reads_lane="cocycle", reads_input=("algebra",))
    with pytest.raises(ToolSchemaValidationError):
        ToolEntry(name="t", owner="srmech", category="c", summary="s",
                  reads_lane="sign", reads_input=("topology",))
    # A lane with no input is half a declaration; so is an input with no lane.
    with pytest.raises(ToolSchemaValidationError):
        ToolEntry(name="t", owner="srmech", category="c", summary="s",
                  reads_lane="sign")
    with pytest.raises(ToolSchemaValidationError):
        ToolEntry(name="t", owner="srmech", category="c", summary="s",
                  reads_input=("algebra",))


def test_every_declaration_is_in_vocabulary() -> None:
    warmup_all()
    for entry in get_tool_schema().tools:
        if entry.reads_lane is None:
            assert entry.reads_input == (), entry.name
            continue
        assert entry.reads_lane in LANES, entry.name
        assert entry.reads_input, entry.name
        for src in entry.reads_input:
            assert src in LANE_INPUTS, (entry.name, src)


# ══════════════════════════════════════════════════════════════════════
# 2. THE RATCHET — the response must match the declaration
# ══════════════════════════════════════════════════════════════════════
#
# Each driver takes (strand-or-gains, embedding) already perturbed, so the
# harness never has to know an op's signature at the call site.

_ONE12 = bytes([1] * 12)


def _drivers():
    """(op name, kind, callable). ``kind`` selects which perturbation family
    the harness applies; an op appears once per input it declares."""
    g = _genome
    return {
        "srmech.biology.q8.q8_project_v4": ("algebra", _q8.q8_project_v4),
        "srmech.biology.q8.q8_conjugate":
            ("algebra", lambda s: bytes(_q8.q8_conjugate(b) for b in s)),
        "srmech.biology.q8.q8_mult":
            ("algebra",
             lambda s: bytes(_q8.q8_mult(a, b) for a, b in zip(s, _ONE12))),
        "srmech.biology.q8.q8_bind": ("algebra", lambda s: _q8.q8_bind(s, _ONE12)),
        "srmech.biology.genome.genome_fiber_holonomy":
            ("algebra", lambda s: g.genome_fiber_holonomy(s, leaf_dim=4)),
        "srmech.biology.genome.codon_read": ("algebra", g.codon_read),
        "srmech.qm.quaternion.quaternion_cycle_holonomy":
            ("gains",
             lambda gg: quaternion_cycle_holonomy(
                 _EDGES, [_gain(x) for x in gg], n=6)),
        "srmech.biology.genome.cwf_consistency_mod2":
            ("gains+geometry", None),
        "srmech.biology.genome.discrete_writhe": ("geometry", g.discrete_writhe),
    }


def _cwf(gains, emb):
    return _genome.cwf_consistency_mod2(
        _EDGES, [_gain(x) for x in gains], n=6, embedding=emb)


def _sweep_response(name, kind, fn, trials=120, seed=347):
    """Return (sign_moved, index_moved) over a SWEEP. A single sample can miss
    a real response, so a False here is a verdict over the whole sweep."""
    rng = random.Random(seed)
    sign_moved = index_moved = False
    if kind == "geometry":
        base = fn(_EMB)
        sign_moved = fn(_reflect(_EMB)) != base
        index_moved = any(
            fn(_rescale(_EMB, nu, de)) != base for nu, de in _RESCALES)
        return sign_moved, index_moved
    for _ in range(trials):
        rho = RHOS[rng.randrange(1, 6)]
        if kind == "algebra":
            base_in = bytes(rng.randrange(8) for _ in range(12))
            at = rng.randrange(12)
            sig = bytearray(base_in)
            sig[at] = _sigma(sig[at])
            rel = bytes(_relabel(b, rho) for b in base_in)
            base = fn(base_in)
            sign_moved = sign_moved or fn(bytes(sig)) != base
            index_moved = index_moved or fn(rel) != base
        elif kind == "gains":
            gg = [rng.randrange(8) for _ in range(6)]
            at = rng.randrange(6)
            sig = list(gg)
            sig[at] = _sigma(sig[at])
            rel = [_relabel(x, rho) for x in gg]
            base = fn(gg)
            sign_moved = sign_moved or fn(sig) != base
            index_moved = index_moved or fn(rel) != base
        else:  # gains + geometry
            gg = [rng.randrange(8) for _ in range(6)]
            at = rng.randrange(6)
            sig = list(gg)
            sig[at] = _sigma(sig[at])
            rel = [_relabel(x, rho) for x in gg]
            base = _cwf(gg, _EMB)
            sign_moved = sign_moved or _cwf(sig, _EMB) != base
            sign_moved = sign_moved or _cwf(gg, _reflect(_EMB)) != base
            index_moved = index_moved or _cwf(rel, _EMB) != base
        if sign_moved and index_moved:
            break                       # both already witnessed
    return sign_moved, index_moved


@pytest.mark.parametrize("op_name", sorted(_drivers()))
def test_declared_lane_matches_measured_response(op_name) -> None:
    """THE RATCHET. Drive the op through a sigma flip and an Aut index relabel
    and assert the response matches what its ToolEntry declares."""
    warmup_all()
    entry = get_tool_schema().lookup(op_name)
    assert entry is not None, f"{op_name} is not registered"
    assert entry.reads_lane is not None, (
        f"{op_name} is in the rc347 verifier but declares no lane — either "
        f"declare it or drop it from the harness; a driver with nothing to "
        f"check is the dead-seam failure mode")
    kind, fn = _drivers()[op_name]
    sign_moved, index_moved = _sweep_response(op_name, kind, fn)

    want_sign = entry.reads_lane in ("sign", "both")
    want_index = entry.reads_lane in ("index", "both")
    assert sign_moved == want_sign, (
        f"{op_name} declares reads_lane={entry.reads_lane!r} so it should "
        f"{'MOVE' if want_sign else 'NOT move'} under a sign-lane "
        f"perturbation, but sign_moved={sign_moved}. MIS-DECLARED.")
    assert index_moved == want_index, (
        f"{op_name} declares reads_lane={entry.reads_lane!r} so it should "
        f"{'MOVE' if want_index else 'NOT move'} under a pure INDEX relabel, "
        f"but index_moved={index_moved}. MIS-DECLARED.")


def test_every_declaring_op_is_in_the_verifier() -> None:
    """No declaration may escape the ratchet. A field that only SOME rows are
    checked against is the same false green one row at a time."""
    warmup_all()
    declared = {e.name for e in get_tool_schema().tools
                if e.reads_lane is not None}
    assert declared == set(_drivers()), (
        f"undriven declarations: {sorted(declared - set(_drivers()))}; "
        f"drivers with no declaration: {sorted(set(_drivers()) - declared)}")


# ══════════════════════════════════════════════════════════════════════
# 3. The geometry-side sign check — Wr discards the magnitude it computed
# ══════════════════════════════════════════════════════════════════════


def test_writhe_is_magnitude_blind_and_orientation_sensitive() -> None:
    """Wr reads the SIGN of each orientation determinant and DISCARDS the
    magnitude. Pinned at five positive rational scales including a shrink and
    a non-integer; and it NEGATES under a reflection, so the invariance is not
    the trivial "this op ignores its input"."""
    base = _genome.discrete_writhe(_EMB)
    assert base["writhe"] != (0, 1), (
        "the fixture must have non-zero writhe or the reflection check below "
        "passes for the trivial reason")
    identical = 0
    for nu, de in _RESCALES:
        got = _genome.discrete_writhe(_rescale(_EMB, nu, de))
        assert got["writhe"] == base["writhe"], (nu, de, got["writhe"])
        identical += 1
    assert identical == len(_RESCALES) == 5
    mirror = _genome.discrete_writhe(_reflect(_EMB))
    assert mirror["writhe"] == (-base["writhe"][0], base["writhe"][1])


# ══════════════════════════════════════════════════════════════════════
# 4. The Tw / Wr / Lk adjudication, on the shipped op
# ══════════════════════════════════════════════════════════════════════


def test_tw_wr_lk_read_the_lanes_the_payload_claims() -> None:
    """Tw and Wr are NOT one quantity at two resolutions: they read DIFFERENT
    INPUTS and share the LANE. Lk is the only mixer. Read per-FIELD off
    cwf_consistency_mod2, the one shipped op that computes all three."""
    rng = random.Random(11)
    seen = {"tw_sign": False, "tw_index": False, "tw_geo": False,
            "wr_sign": False, "wr_index": False, "wr_geo": False,
            "lk_sign": False, "lk_index": False, "lk_geo": False}
    for _ in range(400):
        g = [rng.randrange(8) for _ in range(6)]
        at = rng.randrange(6)
        rho = RHOS[rng.randrange(1, 6)]
        sig = list(g)
        sig[at] = _sigma(sig[at])
        rel = [_relabel(x, rho) for x in g]
        base, a_s, a_i = _cwf(g, _EMB), _cwf(sig, _EMB), _cwf(rel, _EMB)
        a_g = _cwf(g, _reflect(_EMB))
        for tag, field in (("tw", "tw_mod2"), ("wr", "wr"), ("lk", "lk_mod2")):
            seen[f"{tag}_sign"] |= base[field] != a_s[field]
            seen[f"{tag}_index"] |= base[field] != a_i[field]
            seen[f"{tag}_geo"] |= base[field] != a_g[field]

    # Tw — SIGN lane, ALGEBRA input.
    assert seen["tw_sign"] and not seen["tw_index"] and not seen["tw_geo"]
    # Wr — SIGN lane, GEOMETRY input. Algebra-blind in BOTH lanes.
    assert seen["wr_geo"] and not seen["wr_sign"] and not seen["wr_index"]
    # Lk — BOTH lanes, ALGEBRA input. The ONLY read that answers to a pure
    # index relabel; that is what "the only mixer" means operationally.
    assert seen["lk_sign"] and seen["lk_index"] and not seen["lk_geo"]


# ══════════════════════════════════════════════════════════════════════
# 5. The payload says what the measurements say
# ══════════════════════════════════════════════════════════════════════


def test_describe_lanes_is_derived_from_the_tool_schema() -> None:
    warmup_all()
    d = describe()
    lanes = d["lanes"]
    declared = {e.name: e for e in get_tool_schema().tools
                if e.reads_lane is not None}
    assert lanes["total"] == len(declared)
    assert set(lanes["ops"]) == set(declared)
    for name, row in lanes["ops"].items():
        assert row["lane"] == declared[name].reads_lane
        assert row["reads"] == list(declared[name].reads_input)
    assert sum(lanes["by_lane"].values()) == lanes["total"]
    assert set(lanes["by_lane"]) <= set(LANES)
    assert set(lanes["by_input"]) <= set(LANE_INPUTS)
    assert lanes["definitions"] == dict(LANES)
    assert lanes["inputs"] == dict(LANE_INPUTS)
    # The admission rule ships as DATA, and names the file that enforces it.
    assert lanes["verified_by"]["test"] == "tests/test_op_lane_rc347.py"
    assert set(lanes["verified_by"]["sign"]) == {"algebra", "geometry"}
    assert set(lanes["verified_by"]["index"]) == {"algebra", "geometry"}


def test_worked_example_matches_the_lanes_it_reports() -> None:
    """The Tw/Wr/Lk rows in the payload must agree with their own counts —
    a row whose numbers contradict its verdict is the failure this axis is
    about."""
    rows = describe()["lanes"]["worked_example"]["reads"]
    assert [r["name"] for r in rows] == ["Tw", "Wr", "Lk"]
    for r in rows:
        moved_sign = r["sign_algebra"] > 0 or r["sign_geometry"] > 0
        moved_index = r["index_algebra"] > 0
        want = {("sign", True, False), ("index", False, True),
                ("both", True, True)}
        assert (r["lane"], moved_sign, moved_index) in want, r
        assert r["input"] in LANE_INPUTS
    tw, wr, lk = rows
    # The structural point, asserted rather than narrated.
    assert tw["lane"] == wr["lane"] == "sign" and tw["input"] != wr["input"]
    assert lk["lane"] == "both"
    assert lk["index_algebra"] > 0
    assert tw["index_algebra"] == 0 and wr["index_algebra"] == 0


# ══════════════════════════════════════════════════════════════════════
# 6. The 2:4:8 CONFLATION GUARD is in the payload, not a comment
# ══════════════════════════════════════════════════════════════════════


def test_granularity_labels_which_248_reading_it_is() -> None:
    """BLOCK_DIMS (2,4,8) = the dims of THREE algebras. The granularity slot
    counts (8,4,2) = ONE algebra at three widths. Same three numbers,
    different objects — a report that does not label which is which teaches
    the confusion, so the label is asserted here."""
    from srmech.amsc.cascade.one import BLOCK_DIMS

    gran = describe()["lanes"]["granularity"]
    assert gran["reading"] == "one_algebra_three_widths"
    assert gran["algebra"] == "O" and gran["algebra_real_dim"] == 8
    other = gran["not_this_reading"]
    assert other["value"] == list(BLOCK_DIMS) == [2, 4, 8]
    assert other["symbol"].endswith("BLOCK_DIMS")
    assert "THREE" in other["means"]
    # The two readings must be distinguishable from the payload alone.
    assert [w["slots"] for w in gran["widths"]] == [8, 4, 2]
    assert sorted(w["slots"] for w in gran["widths"]) == sorted(BLOCK_DIMS)
    assert "different objects" in gran["collision_note"]


def test_granularity_is_one_anchor_plus_n_minus_one_torsors() -> None:
    """MEASURED against the shipped cd_basis_product: at every width exactly
    ONE slot is closed under the product, and it is the one holding the
    identity. Closure is an INDEX-lane fact (XOR), which is the concrete
    sense in which lane is orthogonal to granularity."""
    slots_by_width = {
        "R": [[i] for i in range(8)],
        "C": [[0, 1], [2, 3], [4, 5], [6, 7]],
        "H": [[0, 1, 2, 3], [4, 5, 6, 7]],
    }
    labels = {"H": ["H_L", "H_R"],
              "C": ["C_LL", "C_LR", "C_RL", "C_RR"],
              "R": [f"R_{k}" for k in range(8)]}

    def closes(slot):
        s = set(slot)
        return all(cd_basis_product(8, i, j)[0] in s
                   for i in slot for j in slot)

    gran = describe()["lanes"]["granularity"]
    by_over = {w["over"]: w for w in gran["widths"]}
    for over, slots in slots_by_width.items():
        verdicts = [closes(s) for s in slots]
        assert sum(verdicts) == 1, f"{over}: expected exactly ONE anchor slot"
        assert verdicts[0] is True, f"{over}: the anchor must hold the identity"
        row = by_over[over]
        assert row["slots"] == len(slots)
        assert row["real_dims_per_slot"] == len(slots[0])
        assert row["anchor_slots"] == 1
        assert row["torsor_slots"] == len(slots) - 1
        assert row["real_dims_per_slot"] * row["slots"] == 8
        for k, lab in enumerate(labels[over]):
            assert row["closes"][lab] is verdicts[k], (over, lab)
    # The specific measured verdicts the brief named.
    assert by_over["H"]["closes"] == {"H_L": True, "H_R": False}
    assert by_over["C"]["closes"] == {
        "C_LL": True, "C_LR": False, "C_RL": False, "C_RR": False}
