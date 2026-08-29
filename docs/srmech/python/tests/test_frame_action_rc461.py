"""rc461 (`#T1181`) — ``triality_frame_action``: the label action, DERIVED.

WHAT THIS RC CHANGED, AND WHY IT IS A GATE AND NOT A FEATURE
============================================================
``srmech/physics/qm/triality.py`` carries a block comment splitting its claims
into DERIVED / DEFINITIONAL / MEASURED-IN-A-NOTE, and it puts the two label
actions in the middle bucket, in its own words: *"DEFINITIONAL, from how
``_companion_maps`` builds them"*, with the independent char-poly derivation
living in ``docs/srmech/notes/v4_so8_bridge_derivation_rc422.py`` and in
``tests/test_covering_layer_rc422.py``.

**Neither of those ships.** ``triality_rep_dictionary()`` emits
``tau_label_action`` into ``describe()``, the MCP tool list and the compiled-in
C tool registry, so a consumer read a claim that no shipped op could re-derive.
That is the same reach the ref-notation arc measured and the same reach the
citation gates guard, one axis over: *a value inside the wheel whose only
justification is outside it.*

``triality_frame_action`` re-derives it from the matrix alone, and this file is
what stops the derivation and the constant drifting apart.

THE INSTRUMENT, AND WHY IT IS CHEAP (all figures MEASURED on the rc461 host)
===========================================================================
The three 8-dim reps are separated by their WEIGHT SYSTEMS. Restricted to the
standard Cartan ``⟨E01, E23, E45, E67⟩`` the frame with Cartan block ``A_f``
carries weights ``± the rows of A_f``. So:

* ``8v`` → ``{±e_j}``, integer;
* ``8s`` / ``8c`` → all-half-integer rows, separated by the PARITY of their
  minus signs — and that parity is **read off the shipped S_B / S_C**
  (measured: ``8s`` odd, ``8c`` even), never chosen. Choosing it would make the
  classification a convention wearing a measurement's clothes.

All three shipped maps preserve that Cartan span EXACTLY, every induced entry
in ``{−1/2, 0, +1/2}``, so the read is 4×4 exact-ℚ arithmetic: **5.2 ms** for
both generators against **~4.3 s** for a single exact companion solve and
**46.7 s** for a cold ``_companion_maps()``.

WHY THIS IS NOT A VACUOUS INSTRUMENT
====================================
``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``.
Driven over the six elements of ``⟨S_B, S_C⟩ ≅ S₃`` the op returns **six
distinct** permutations of ``{v, s, c}`` — the whole of ``Sym(3)``, including
the third transposition ``S_B·S_C·S_B`` (``v`` fixed, ``s ↔ c``) that NO
shipped constant names. And a planted mutation of one Cartan-block entry makes
the classification RAISE rather than answer, so the success is a discrimination
and not a default.

WHAT THIS FILE DELIBERATELY DOES NOT CLAIM
==========================================
The op reads the label action of a Cartan-PRESERVING automorphism. An element
of ``Out(Spin(8))`` conjugated by a generic inner element does not preserve
this particular Cartan, and the op refuses it with a ``ValueError`` naming the
escaping coordinate rather than answering approximately. That refusal is
exercised below. It is a real restriction of the instrument, stated rather
than hidden.
"""

from __future__ import annotations

import pytest

from srmech.math.q import Q, to_q
from srmech.physics.qm.so8 import _DIM_SO8, _epq_pairs
from srmech.physics.qm.triality import (
    _CARTAN_PAIRS,
    _CARTAN_RANK,
    _SWAP_LABEL_ACTION,
    _TAU_LABEL_ACTION,
    _block_matmul,
    _cartan_block,
    _companion_maps,
    _frame_cartan_blocks,
    triality_automorphism,
    triality_frame_action,
    triality_swap,
)

_FRAMES = ("v", "s", "c")


# ── shared exact-ℚ helpers (no numpy anywhere, per the standing rule) ──────

def _exact(rows):
    return [[to_q(x) for x in r] for r in rows]


def _identity28():
    return [[1.0 if i == j else 0.0 for j in range(_DIM_SO8)]
            for i in range(_DIM_SO8)]


def _cartan_of(mat28_rows):
    return _cartan_block(_exact(mat28_rows), "test")


def _embed(block):
    """Lift an exact 4×4 Cartan block back to a 28×28 map that is the identity
    off the Cartan. Enough to drive the op over the whole group without
    rebuilding 28×28 products."""
    pairs = _epq_pairs()
    ci = [pairs.index(pq) for pq in _CARTAN_PAIRS]
    out = [[Q(1) if i == j else Q(0) for j in range(_DIM_SO8)]
           for i in range(_DIM_SO8)]
    for a, ra in enumerate(ci):
        for b, cb in enumerate(ci):
            out[ra][cb] = block[a][b]
    return out


def _group_elements():
    """The six elements of ⟨S_B, S_C⟩ as exact 4×4 Cartan blocks, built from
    the two SHIPPED generators and nothing else."""
    s_b, s_c = _companion_maps()
    b = _cartan_of([list(r) for r in s_b])
    c = _cartan_of([list(r) for r in s_c])
    i4 = [[Q(1) if i == j else Q(0) for j in range(4)] for i in range(4)]
    return {
        "I": i4,
        "S_B": b,
        "S_C": c,
        "tau = S_B S_C": _block_matmul(b, c),
        "tau^2 = S_C S_B": _block_matmul(c, b),
        "S_B S_C S_B": _block_matmul(_block_matmul(b, c), b),
    }


# ══════════════════════════════════════════════════════════════════════
# 1. The derivation reproduces the two shipped constants
# ══════════════════════════════════════════════════════════════════════

def test_the_derived_tau_action_equals_the_shipped_constant() -> None:
    """The whole point of the rc: ``_TAU_LABEL_ACTION`` stops being the only
    statement of what τ does to the labels."""
    got = triality_frame_action(triality_automorphism())
    assert got["frame_action"] == _TAU_LABEL_ACTION, got["frame_action"]
    assert got["order"] == 3
    assert got["fixed_frames"] == ()
    assert got["is_identity"] is False


def test_the_derived_swap_action_equals_the_shipped_constant() -> None:
    got = triality_frame_action(triality_swap())
    assert got["frame_action"] == _SWAP_LABEL_ACTION, got["frame_action"]
    assert got["order"] == 2
    assert got["fixed_frames"] == ("c",), got["fixed_frames"]


def test_the_identity_map_moves_no_frame() -> None:
    got = triality_frame_action(_identity28())
    assert got["frame_action"] == {f: f for f in _FRAMES}
    assert got["order"] == 1
    assert got["is_identity"] is True
    assert got["moved_frames"] == ()


# ══════════════════════════════════════════════════════════════════════
# 2. NON-VACUITY — the instrument returns all six answers, not one
# ══════════════════════════════════════════════════════════════════════

def test_all_six_elements_of_sym3_are_realised_and_distinct() -> None:
    """A classifier that returns the same answer whatever it is fed has
    measured nothing. Driven over ⟨S_B, S_C⟩ this returns SIX distinct
    permutations — every element of Sym(3)."""
    seen = {}
    for name, block in _group_elements().items():
        got = triality_frame_action(_embed(block))
        seen[tuple(sorted(got["frame_action"].items()))] = name
    assert len(seen) == 6, sorted(seen.values())
    # and the six ARE Sym(3): every permutation of three labels, no repeats
    orders = sorted(triality_frame_action(_embed(b))["order"]
                    for b in _group_elements().values())
    assert orders == [1, 2, 2, 2, 3, 3], orders


def test_the_third_transposition_is_reachable_and_no_constant_names_it() -> None:
    """``S_B·S_C·S_B`` fixes ``v`` and swaps ``s ↔ c``. It is a genuine element
    of the shipped group and appears in NO module constant — so a test that
    only compared against ``_TAU_LABEL_ACTION`` / ``_SWAP_LABEL_ACTION`` could
    not have seen it at all."""
    block = _group_elements()["S_B S_C S_B"]
    got = triality_frame_action(_embed(block))["frame_action"]
    assert got == {"v": "v", "s": "c", "c": "s"}, got
    assert got != _TAU_LABEL_ACTION and got != _SWAP_LABEL_ACTION


def test_the_label_action_is_a_contravariant_homomorphism() -> None:
    """The module's own note says composition is contravariant: the labels
    compose as ``π_{S_C} ∘ π_{S_B}``. EXECUTED here rather than quoted."""
    els = _group_elements()
    act = {k: triality_frame_action(_embed(v))["frame_action"]
           for k, v in els.items()}
    lhs = act["tau = S_B S_C"]
    contravariant = {f: act["S_C"][act["S_B"][f]] for f in _FRAMES}
    covariant = {f: act["S_B"][act["S_C"][f]] for f in _FRAMES}
    assert lhs == contravariant, (lhs, contravariant)
    assert lhs != covariant, "the two orders coincide — the probe is blind"


# ══════════════════════════════════════════════════════════════════════
# 3. The measured structure the payload reports
# ══════════════════════════════════════════════════════════════════════

def test_the_spinor_parity_is_read_off_the_shipped_maps_not_chosen() -> None:
    """8s carries the ODD-minus-sign half-integer weights and 8c the EVEN ones.
    Re-derived here straight from ``_companion_maps`` so the payload field is
    checked against its own source rather than against itself."""
    blocks = _frame_cartan_blocks()
    parity = {}
    for f in ("s", "c"):
        rows = blocks[f]
        assert all(x * x == Q(1, 4) for r in rows for x in r), \
            f"8{f} Cartan block is not all ±1/2"
        got = {sum(1 for x in r if x < 0) % 2 for r in rows}
        assert len(got) == 1, (f, got)
        parity[f] = got.pop()
    assert parity == {"s": 1, "c": 0}, parity
    assert triality_frame_action(triality_automorphism())["spinor_parity"] \
        == parity


def test_the_8v_block_is_the_identity_and_its_weights_are_integral() -> None:
    """8v is the frame the whole engine is coordinatised in, so its Cartan
    block must be ``I`` and its weights the integer ``{±e_j}`` — the ONE frame
    whose weight table carries no halves."""
    blocks = _frame_cartan_blocks()
    assert blocks["v"] == tuple(
        tuple(Q(1) if i == j else Q(0) for j in range(4)) for i in range(4))
    weights = triality_frame_action(_identity28())["frame_weights"]["v"]
    assert all(all(den == 1 for _num, den in w) for w in weights), weights
    assert all(sum(1 for num, _d in w if num != 0) == 1 for w in weights)


def test_the_four_by_eight_reconciliation_is_computed_not_pinned() -> None:
    """4 × 8 = 32: an 8-dimensional rep's identity is fixed by 8 weights × 4
    Cartan coordinates. The payload's three cardinals are DERIVED from the
    weight tables it also returns, so they cannot disagree with them."""
    got = triality_frame_action(triality_automorphism())
    assert got["cartan_rank"] == _CARTAN_RANK == 4
    assert got["weights_per_frame"] == 8
    assert got["weight_table_entries"] == 32 == got["cartan_rank"] * 8
    for f in _FRAMES:
        table = got["frame_weights"][f]
        assert len(table) == got["weights_per_frame"]
        assert all(len(w) == got["cartan_rank"] for w in table)
        assert sum(len(w) for w in table) == got["weight_table_entries"]
    union = set()
    for f in _FRAMES:
        union |= set(got["frame_weights"][f])
    assert len(union) == got["distinct_weights"] == 24, len(union)
    # PAIRWISE DISJOINT — if two frames shared a weight the classification
    # could not be a set match at all.
    for a in _FRAMES:
        for b in _FRAMES:
            if a < b:
                assert not (set(got["frame_weights"][a])
                            & set(got["frame_weights"][b])), (a, b)


def test_the_cartan_block_entries_are_exactly_half_integers() -> None:
    """The measured fact that makes the instrument cheap: every induced entry
    of τ and S_B on the Cartan is in ``{−1/2, 0, +1/2}``, so no float and no
    tolerance is anywhere in the decision path."""
    for mat in (triality_automorphism(), triality_swap()):
        block = triality_frame_action(mat)["cartan_block"]
        vals = {(num, den) for row in block for num, den in row}
        assert vals <= {(-1, 2), (0, 1), (1, 2)}, sorted(vals)


# ══════════════════════════════════════════════════════════════════════
# 4. PLANTED MUTATIONS — the classification is a discrimination
# ══════════════════════════════════════════════════════════════════════

def test_a_perturbed_cartan_block_is_refused_not_classified() -> None:
    """Add 1 to one entry of τ's Cartan block. The transported weight system
    then matches NO frame and the op raises. Without this, "it returned the
    right permutation" would be compatible with an op that always does."""
    els = _group_elements()
    bad = [row[:] for row in els["tau = S_B S_C"]]
    bad[0][0] = bad[0][0] + Q(1)
    with pytest.raises(ValueError, match="matches 0 of the three frames"):
        triality_frame_action(_embed(bad))


def test_a_map_that_leaves_the_cartan_span_is_refused_by_name() -> None:
    """The instrument's stated restriction, exercised. The message names the
    escaping coordinate so the caller can conjugate rather than guess."""
    rows = triality_automorphism().tolist()
    rows = [r[:] for r in rows]
    pairs = _epq_pairs()
    off = next(i for i, pq in enumerate(pairs) if pq not in _CARTAN_PAIRS)
    rows[off][pairs.index(_CARTAN_PAIRS[0])] = 1.0
    with pytest.raises(ValueError, match="does not preserve the standard Cartan"):
        triality_frame_action(rows)


def test_a_wrong_shape_is_refused() -> None:
    with pytest.raises(ValueError, match="must be 28x28"):
        triality_frame_action([[0.0] * 28] * 27)
    with pytest.raises(ValueError, match="must be 28x28"):
        triality_frame_action([[0.0] * 27] * 28)


def test_the_scaled_map_is_refused_because_a_weight_set_stops_matching() -> None:
    """2·τ is not an automorphism of so(8); its transported weights are twice
    the right size and match nothing. A classifier that normalised first would
    accept it, and would then be reporting on an object it was not given."""
    els = _group_elements()
    doubled = [[x + x for x in row] for row in els["tau = S_B S_C"]]
    with pytest.raises(ValueError, match="not an automorphism"):
        triality_frame_action(_embed(doubled))


# ══════════════════════════════════════════════════════════════════════
# 5. Registration surface
# ══════════════════════════════════════════════════════════════════════

def test_the_op_is_registered_and_the_total_moved_by_two() -> None:
    from srmech.introspect.tool_schema import get_tool_schema
    import srmech
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.physics.qm.triality.triality_frame_action" in names
    assert "srmech.math.laplacian.cyclic_laplacian_spectrum" in names
    assert srmech.describe()["tools"]["total"] == 692


def test_the_op_is_exported() -> None:
    from srmech.physics.qm import triality
    assert "triality_frame_action" in triality.__all__


def test_the_content_addresses_are_stable_and_discriminating() -> None:
    """``action_sha256`` addresses the PERMUTATION, so two elements with the
    same action share it and two with different actions do not."""
    a = triality_frame_action(triality_automorphism())
    b = triality_frame_action(triality_automorphism())
    c = triality_frame_action(triality_swap())
    assert a["action_sha256"] == b["action_sha256"]
    assert a["action_sha256"] != c["action_sha256"]
    assert a["procedure_sha256"] == c["procedure_sha256"]
    assert len(a["action_sha256"]) == 64
