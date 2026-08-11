"""composes — the COMPOSITION GRAIN (rc412, `#T1093`).

rc305 added ``ToolEntry.composes`` and one gate: every declared sub-op must be
a REGISTERED op (``test_composes_preserves_rc305.py:126``). That gate is real —
whole-registry, strict-zero, and it goes red on a phantom name. It has one
hole, and rc412 exists because the hole is the ADR-0012 §6.1 failure mode
verbatim: **a strict-zero sweep over a shrinking set is vacuously true.**

Measured before this file existed: ``cwf_consistency_mod2``'s declaration was
pinned by NOTHING. Every ``.composes`` field access under ``tests/`` was
enumerated; only ``test_composes_preserves_rc305.py`` (which names
``_EXPECTED_GENOME_COMPOSES`` — genome only) and
``test_tool_schema_ops_c_rc185.py:101`` (a round-trip reconstruction, not a
pin) touch the field. Delete cwf's entry at the SSoT, regenerate, and the
declared-edge total falls while the whole suite stays green.

WHAT THIS FILE ADDS — three clauses, and NO coverage floor
==========================================================

**There is deliberately no floor, and there will not be one.** ``tool_schema``
says of ``composes``: *"Empty for a LEAF op (the correct default)"*, and
``rc305:103`` actively pins ``sha256_bytes`` empty. A floor would demand
content on the majority of the registry, and the only way to satisfy it is to
invent composition partners — filler shipped into a surface ADR-0012 makes
load-bearing. **That half stands and rc423 did not weaken it.**

⚠️ **AMENDED rc423 (`#T1113`) — the sentence that followed was WRONG, and it
is left standing here rather than deleted so the correction is legible.** It
read: *"A ceiling is no better: a down-only ceiling on unpopulated rows
presumes the residual should reach zero, and here it must not."* The
conclusion is right about the DENOMINATOR it names and wrong about the one it
should have named. A ceiling over **unpopulated** rows is indeed incoherent,
exactly as written — leaves are permanently unpopulated and must stay so. But
"unpopulated" and "**unadjudicated**" are different sets, and only the first
was considered here. A row nobody has ever looked at and a row measured to
compose nothing are indistinguishable in this field — both are ``()`` — and
collapsing them is what let the population trickle 9 → 16 across ~45 rcs with
every gate green.

``tests/test_composes_population_rc423.py`` splits them. An op is ADJUDICATED
when it is declared, or measured to reach nothing (LEAF), or measured to reach
exactly one thing (SINGLE), or reviewed and deliberately refused. The residual
is then rows whose order a human has not traced — and **that** residual should
reach zero, so it carries a down-only ceiling. The population claim this file
declined to make is now made, and it is made against a denominator that can
honestly drain (rc419's lesson: a ceiling over an unfaithful denominator reads
as progress).

So the clauses gate DRIFT and TRUTH, never coverage:

1. **NON-VACUITY.** :data:`ROSTER` is the exact hand-maintained set of rows
   that declare a composition, with each one's ordered tuple. The registry's
   declaring set must equal ``ROSTER``'s keys EXACTLY — so deleting a
   declaration goes red, and so does adding one without review.
2. **VERIFIABILITY.** Every declared sub-op must actually be CALLED, checked
   against an identity-resolved AST call-graph over the live callables. This
   is what separates a *derived* population from an *asserted* one.
3. **SHAPE.** No self-reference, and the declared relation is acyclic — real
   properties of a "built-from" edge, cheap to hold.

WHAT TURNS EACH CLAUSE RED (each verified by mutation, rc412)
=============================================================

* clause 1 — delete ``cwf_consistency_mod2``'s ``"composes"`` from
  ``_tool_docs_curated.py``; or add a declaration to any row not in ROSTER.
* clause 2 — add a real registered op to any row's tuple that the row does
  not call, e.g. ``sha256_bytes`` onto ``kepler.pin_slot``. (The negative
  control below is the same mutation, run as an assertion.)
* clause 3 — make any row name itself.

AND THE READER, WITHOUT WHICH THE ROWS WOULD ONLY MOVE A HASH
============================================================
The last block of this file gates rc412's other half. Through rc411 the only
consumers of ``composes`` were ``ToolEntry.to_jsonable``, the curated merge
and the C serialiser — not one of them a question a caller asks — and the
REVERSE direction ("what is built FROM this op") had no reader at all.
``ToolSchema.composition()`` answers both in one call; ``search``'s index
gains the two fields. Removing either goes red here. The index half is the
weaker one and the tests say so out loud rather than overclaiming it.

WHY THE ORDER IS HAND-TRACED AND NOT DERIVED
============================================
The SET is derivable; the ORDER is not. Measured at rc412 over the whole
registry: identity-resolved depth-1 recovers 5 of the 7 rc305 ground-truth
targets, depth-3 recovers 7 of 7. But *lexical* first-call order matches
**0 of 2** ground-truth rows — ``genome_from_graph`` calls ``genome_save`` /
``genome_census`` inside a native fast-path that sits ABOVE the pure path a
human traced. The contract says ORDERED (``tool_schema.py``), so static
analysis supplies the set and a human supplies the order. That asymmetry is
why clause 2 checks ``declared ⊆ derived`` and NOT sequence equality.

numpy-free; stdlib ``ast`` / ``importlib`` / ``inspect`` / ``pathlib`` /
``functools`` only (none is a ledgered import — see
``tests/test_selfhosting_import_ban.py``). TOML is read through **srmech's own**
``srmech._toml``, not ``tomllib``: rc417 added a descriptor reader here, and a
gate about self-hosting that reached for the stdlib parser to do it would be
making the point backwards.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Set, Tuple

from composes_derive import (BY_NAME, DERIVE_DEPTH, SCHEMA, derived,
                             ledger_names, resolve_op)
from srmech import _toml as _srmech_toml
from srmech.dsl import _toml_chain

_SCHEMA = SCHEMA
_BY_NAME = BY_NAME


# ──────────────────────────────────────────────────────────────────────
# THE ROSTER — the SSoT of this gate.
#
# One entry per registry row that declares a composition, holding the exact
# ORDERED tuple. Adding a row to `_tool_docs_curated.py` without adding it
# here is a failure, and so is the reverse: the point is that population is
# a reviewed act, not a drift.
#
# rc305 shipped `genome_from_graph`; rc313 shipped `cwf_consistency_mod2`
# (8 rcs later, and unpinned until now). rc412 adds seven, every one traced
# by reading the implementation end to end against these four criteria:
#
#   (1) POOL — the depth-<=3 identity-resolved derived set holds >= 3
#       registered sub-ops. That is where a `composes` tuple carries
#       something a caller could not read off the summary; a one-hop row
#       does not.
#   (2) LINEAR TRACE — the pure path is a straight line, so "call order" is
#       a fact rather than a choice. Rows whose order depends on a branch,
#       a dispatch table, or a comprehension over caller data are OUT.
#   (3) NO FAST-PATH REORDERING — either there is no native fast-path, or
#       the fast-path is a WHOLE-op replacement that calls no registered
#       sub-op. A PARTIAL fast-path means two different call orders exist
#       and the tuple cannot be true of both. This is exactly the defect
#       that makes `genome_from_graph`'s lexical order wrong, and it is
#       what excluded `mat_svd` (native sigma, then the Gram route's ops)
#       and `hdc.cooccurrence_fold` (the native branch skips
#       `klein4_bundle_accumulate` entirely).
#   (4) VERIFIABLE — declared is a subset of derived, so clause 2 can
#       check it.
#
# What is NOT here is the rest of the registry, and that is the honest
# answer rather than a deferral: most rows either compose nothing (a leaf —
# the correct default) or compose through a private helper whose order a
# reader would have to guess. Guessing is the failure this field exists to
# prevent.
# ──────────────────────────────────────────────────────────────────────

ROSTER: Dict[str, Tuple[str, ...]] = {
    # ── rc305 / rc313 — the ground truth, now pinned on both rows ──────
    "srmech.biology.genome.genome_from_graph": (
        "srmech.biology.genome.genome_partition",
        "srmech.biology.genome.graph_to_kernel",
        "srmech.biology.genome.mint_strand",
        "srmech.biology.genome.genome_save",
        "srmech.biology.genome.genome_census",
    ),
    "srmech.biology.genome.cwf_consistency_mod2": (
        "srmech.biology.genome.discrete_writhe",
        "srmech.physics.qm.quaternion.quaternion_cycle_holonomy",
    ),
    # ── rc412 ─────────────────────────────────────────────────────────
    # Class K pin-slot -> Class N anchor -> Class C re-orient. The op's own
    # docstring names the cascade; the native branch returns a finished
    # pair without touching a registered op, so the pure order is the only
    # order.
    "srmech.cascade.best_rational_signed": (
        "srmech.cascade.pin_slot_at_zero",
        "srmech.math.rational.best_rational",
        "srmech.cascade.reorient",
    ),
    # phi = atan2(i*sin(theta), d + i*cos(theta)) — cos is evaluated first
    # (it builds x), then sin (y), then atan2. Native branch is one C call.
    "srmech.math.kepler.pin_slot": (
        "srmech.math.rational.cos",
        "srmech.math.rational.sin",
        "srmech.math.rational.atan2",
    ),
    # e^z = e^Re * (cos Im + i sin Im). No native branch at all.
    "srmech.math.rational.complex_exp": (
        "srmech.math.rational.exp",
        "srmech.math.rational.cos",
        "srmech.math.rational.sin",
    ),
    # bundle_i( bind( expand(D, byte_i), pos_key(D, i) ) ) — the argument
    # is evaluated before the bind, and the bundle folds last.
    "srmech.math.hdc.klein4_encode_bytes": (
        "srmech.math.hdc.klein4_expand",
        "srmech.math.hdc.klein4_bind",
        "srmech.math.hdc.klein4_bundle",
    ),
    # bind(address(D, preimage), sector_frame(D)) — Python evaluates the
    # two arguments left to right, then the bind.
    "srmech.math.hdc.klein4_from_one": (
        "srmech.math.hdc.klein4_address",
        "srmech.math.hdc.klein4_sector_frame",
        "srmech.math.hdc.klein4_bind",
    ),
    # The recursive rung of the same shape. `klein4_expand` IS reached, but
    # only inside the private `_klein4_pos_key`; the op's own prose says it
    # composes bind + bundle, and declaring the helper's internals would be
    # the same over-attribution the curators avoided on `genome_from_graph`
    # (which omits `write_packed_graph` although it really calls it).
    "srmech.math.hdc.klein4_compose": (
        "srmech.math.hdc.klein4_bind",
        "srmech.math.hdc.klein4_bundle",
    ),
    # Elimination over GF(p): invert the pivot, scale the pivot row, then
    # add the scaled row into each other row. Native branch is one C call.
    "srmech.math.modular_linalg.gf_rref": (
        "srmech.math.cyclic.mod_inv",
        "srmech.math.cyclic.mod_mul",
        "srmech.math.cyclic.mod_add",
    ),
    # rc419 (`#T1110`). Reviewed, and this edit IS the review.
    #
    # `dispatch` is the only one of the nine new signal_processing rows that
    # declares a composition, and it is the honest one: its body reads
    #
    #     chosen = resolve_path(op_name, explicit_path=path)
    #     entry  = lookup(op_name)
    #
    # in that order — RESOLVE the side, then FETCH the entry holding the two
    # implementations — before calling the selected one. Both are registered
    # ops in their own right as of this rc, which is what makes the edge
    # declarable at all; before rc419 neither had a ToolEntry, so `dispatch`
    # could not have named its own parts even if someone had wanted to.
    #
    # The other eight are LEAVES and stay empty, which is the correct default.
    # In particular `begin_cascade` is NOT declared as composing anything: it
    # INFLUENCES resolve_path through the per-thread context stack rather than
    # calling it, and "built from" is a call edge, not an influence edge —
    # declaring it would be exactly the over-attribution `klein4_compose`'s
    # note above refuses.
    "srmech.signal_processing.cascade_dispatcher.dispatch": (
        "srmech.signal_processing.cascade_dispatcher.resolve_path",
        "srmech.signal_processing.path_registry.lookup",
    ),

    # ── rc422 (`#T1123`) — the CENTRE / COVERING layer + the Z(Spin(8))
    # rep-kernel anchor. Six shipped ops had each hand-rolled the same
    # centre-parity shadow with no common surface; these rows are the surface.
    #
    # NOT DECLARED, deliberately: `covering_catalog` calls `spin8_center` to
    # recompute the two fields a reader would most want to disbelieve (the
    # spin8 row's centre order and the g2 rejection's measured basis), but the
    # catalog is not BUILT FROM it — the other three reached rows and all five
    # rejections stand without that call. Declaring it would over-attribute in
    # exactly the way `klein4_compose`'s note above refuses.
    "srmech.math.covering.center_parity": (
        "srmech.cascade.magnitude",
        "srmech.math.cyclic.mod_add",
        "srmech.cascade.reorient",
    ),
    "srmech.math.covering.center_lift": (
        "srmech.math.covering.center_parity",
    ),
    "srmech.math.covering.lift_fibre": (
        "srmech.cascade.magnitude",
    ),
    "srmech.math.covering.linking_number_cwf": (
        "srmech.math.covering.center_parity",
    ),
    "srmech.physics.qm.triality.spin8_center": (
        "srmech.physics.qm.octonion.octonion_mult_table",
    ),
    "srmech.physics.qm.triality.triality_rep_dictionary": (
        "srmech.physics.qm.triality.spin8_center",
    ),
}


# ──────────────────────────────────────────────────────────────────────
# Clause 1 — NON-VACUITY. The declaring set is exactly the roster.
# ──────────────────────────────────────────────────────────────────────


def _declaring() -> Dict[str, Tuple[str, ...]]:
    return {t.name: tuple(t.composes) for t in _SCHEMA.tools if t.composes}


def test_the_declaring_set_is_exactly_the_roster() -> None:
    """The rows that declare a composition are EXACTLY the two reviewed
    populations: this file's hand-traced ROSTER, plus rc423's forced-order
    SINGLE tier.

    This is the clause that closes the rc305 hole. A strict-zero sweep over
    "every declared entry resolves" cannot see a declaration DISAPPEAR; this
    can. It fails in both directions on purpose — an undeclared population is
    as much a drift as a deletion, because the field ships into the wheel and
    into the compiled-in C registry either way.

    rc423 (`#T1113`) — WHY THE UNION, AND WHY IT IS STILL EXACT
    ===========================================================
    Through rc422 this asserted ``live == set(ROSTER)``, which was the whole
    reviewed population because there was only one KIND of review. rc423 adds
    a second kind with a different admission rule, so the assertion takes the
    union of the two ledgers — and it stays an EQUALITY, which is the property
    that matters. A row still cannot appear in the registry without appearing
    in one of the two reviewed ledgers first.

    The two are disjoint by construction and
    ``test_the_two_populations_do_not_overlap`` in the rc423 file proves it,
    so a row cannot hop ledgers to dodge either gate.
    """
    live = set(_declaring())
    want = set(ROSTER) | _rc423_single_names()
    assert live == want, (
        "the set of rows declaring `composes` drifted from the reviewed "
        f"populations. Deleted: {sorted(want - live)}. "
        f"Added without a ledger entry: {sorted(live - want)}. "
        "If the change is intended: a HAND-TRACED multi-op row goes in ROSTER "
        "in this file (that edit IS the review); a FORCED-ORDER single-op row "
        "goes in tests/composes_adjudication_rc423.ndjson via the committed "
        "census script. Do not hand-write a row into either one."
    )


def test_every_roster_row_declares_its_exact_ordered_tuple() -> None:
    """Order included. ``composes`` is ORDERED by contract, so a reordering
    is a content change, not a formatting one."""
    live = _declaring()
    for name, want in ROSTER.items():
        assert live.get(name) == want, (
            f"{name}.composes is {live.get(name)!r}, roster says {want!r}"
        )


def test_the_roster_is_not_empty_and_every_target_is_registered() -> None:
    """Guards the guard: a roster that emptied itself would make both clauses
    above vacuously true."""
    assert ROSTER, "the roster is empty — every clause in this file is vacuous"
    for name, subs in ROSTER.items():
        assert name in _BY_NAME, f"roster names an unregistered op: {name}"
        assert subs, f"a roster entry may not be empty: {name}"
        for sub in subs:
            assert sub in _BY_NAME, f"{name} -> unregistered sub-op {sub}"


# ──────────────────────────────────────────────────────────────────────
# Clause 2 — VERIFIABILITY. declared ⊆ derived(call-graph).
#
# An identity-resolved AST call-graph. "Identity-resolved" is the load-bearing
# word: a callee expression is resolved to a LIVE OBJECT through the defining
# function's own globals plus its function-local imports, and matched by
# `id()` against the resolved registry. Name-matching would have collided the
# ~40 leaf names the registry spells more than once.
#
# It descends through UNREGISTERED `srmech.*` helpers to depth 3, because that
# is what the ground truth requires: `cwf_consistency_mod2`'s two declared
# sub-ops are not called in its own body at all — they sit inside
# `_cwf_compute_pure`, behind a function-local aliased import. Depth 1 scores
# 0/2 on that row and depth 3 scores 2/2.
#
# It is a LOWER BOUND by construction. Dynamic dispatch (getattr routing,
# table dispatch, a callable passed as an argument) is invisible to it, and so
# is any composition that happens on the C side of a thin Python shim. That is
# the right direction for this clause to be wrong in: an under-reading makes a
# TRUE declaration fail loudly and get investigated; an over-reading would
# quietly bless a false one.
# ──────────────────────────────────────────────────────────────────────

# rc423 (`#T1113`) — the machinery that used to live here MOVED to
# ``tests/composes_derive.py`` and is imported above. Nothing about it
# changed; it is shared because rc423's population tiers need the SAME
# call-graph this clause uses, and a copied instrument drifts from its
# original while both copies stay green (the failure
# ``tests/test_rosetta_roots_single_source_rc361.py`` exists to prevent).
# The full rationale — identity-resolution, the depth-3 default, and why it
# is a LOWER BOUND — is in that module's docstring.

_DERIVE_DEPTH = DERIVE_DEPTH
_resolve_op = resolve_op
_derived = derived


def _rc423_single_names() -> Set[str]:
    """The rc423 forced-order SINGLE tier — the second reviewed population.

    Read fresh rather than cached at import so a ledger edit is visible to
    clause 1 in the same run that makes it.
    """
    return ledger_names("SINGLE")


def test_the_instrument_discriminates() -> None:
    """⚠️ NEGATIVE CONTROL. A derivation that returned everything would make
    clause 2 vacuous, and one that returned nothing would make it fail closed
    but for the wrong reason. So: it must FIND the declared edges, and it must
    NOT find an op the row demonstrably does not call.

    ``kepler.pin_slot`` is trig-only — it never hashes anything. If
    ``sha256_bytes`` shows up in its derived set, the resolver is over-
    attributing and clause 2 below is not measuring what it claims.
    """
    found = _derived("srmech.math.kepler.pin_slot")
    assert "srmech.math.rational.atan2" in found, (
        "the instrument cannot see a call it must see — clause 2 is failing "
        "closed for an instrument reason, not a data reason"
    )
    assert "srmech.amsc.format.sha256_bytes" not in found, (
        "the instrument attributes an op that is never called — it is not "
        "discriminating and clause 2 would be vacuous"
    )


#: Where the shipped ``[cascade]`` TOML descriptors live. Resolved off the
#: module that loads them, not off ``srmech.__file__``, so an ADR-0010 move of
#: the catalog is a red here rather than a silently empty chain.
_CASCADE_CATALOG = (Path(_toml_chain.__file__).resolve().parent.parent
                    / "cascade" / "catalogs" / "cascade_catalog")

#: Characters that may appear inside an op name in an ``operation`` chain.
_OP_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


@lru_cache(maxsize=256)
def _descriptor_chain(name: str) -> "frozenset":
    """The leaf op names chained by ``name``'s own ``[cascade].operation``.

    ``frozenset()`` when the op ships no descriptor — an absent descriptor
    must admit NOTHING, never everything.

    Parsed with ``srmech._toml`` (the framework's own reader), and tokenised
    by hand rather than with ``re``: srmech ships no regex surface, and this
    file is inside the corpus ``tests/test_selfhosting_import_ban.py``
    watches. The chain is written as
    ``pin_slot_at_zero -> best_rational(a, b, c) -> reorient``, so every
    identifier-shaped token is harvested and the caller matches on leaf names.
    Over-harvesting argument names is harmless here: a token only ever
    *admits* a sub-op the roster already declares, and the roster is itself a
    reviewed, exactly-pinned population (clause 1).

    ⚠️ The field is ``[cascade.signature].operation``, **not**
    ``[cascade].operation``. The first draft of this reader assumed the
    latter, parsed cleanly, and returned an empty chain for every descriptor
    in the catalog — a silent no-op that behaved exactly like "no descriptor
    exists". :func:`test_the_descriptor_reader_actually_reads_something` is
    the assertion that caught it and is why it ships.
    """
    leaf = name.rsplit(".", 1)[-1]
    path = _CASCADE_CATALOG / f"{leaf}.toml"
    if not path.is_file():
        return frozenset()
    table = _srmech_toml.loads(path.read_bytes().decode("utf-8"))
    cascade = table.get("cascade", {})
    operation = str(cascade.get("signature", {}).get("operation", ""))
    tokens: Set[str] = set()
    buf: List[str] = []
    for ch in operation:
        if ch in _OP_NAME_CHARS:
            buf.append(ch)
        elif buf:
            tokens.add("".join(buf))
            buf = []
    if buf:
        tokens.add("".join(buf))
    return frozenset(tokens)


def test_every_declared_sub_op_is_actually_called() -> None:
    """CLAUSE 2. Every declared sub-op is either CALLED by the declaring op or
    CHAINED by that op's own cascade descriptor.

    A failure here means one of two things, and the message says which to
    check first: the declaration is WRONG (a sub-op the op does not call), or
    the call is real but invisible to static resolution (dynamic dispatch, or
    a C-side composition behind a thin shim). The second is a legitimate
    outcome — but it must be adjudicated, not assumed, which is why it fails
    rather than warns.

    rc417 (`#T1100`) — THE SECOND ADMISSION PATH, AND WHY IT IS NOT A LOOPHOLE
    ==========================================================================
    Through rc416 this clause admitted **one** kind of evidence: the sub-op is
    AST-call-reachable from the parent's source. That is correct DOWNWARD — a
    declared sub-op the parent genuinely never reaches is a false declaration,
    and the clause catches it.

    It is **structurally wrong LATERALLY**, and the shape is not hypothetical:
    a cascade can be declared in a TOML ``[cascade]`` descriptor whose
    ``operation`` field chains ops that the **DSL runner** invokes, not the
    parent. ``best_rational_signed.toml`` spells it
    ``pin_slot_at_zero -> best_rational(…) -> reorient``. Under the single
    admission path such a row fails clause 2 while being *entirely true* —
    the composition is real, it is simply executed by a chain interpreter
    rather than by a call in the parent's body. The gate would then be
    measuring *which execution mechanism a cascade uses*, not whether its
    declaration is honest.

    So a missing sub-op is also admitted when the parent's own descriptor
    chains it. That is a **second channel of the same evidence**, not a
    weakening: the descriptor is a shipped, parsed artefact under the same
    codegen ratchets as the registry, so the row is still being checked
    against something the tree can contradict.

    **Why this does not silently pass everything.** The descriptor is looked
    up by the parent's exact leaf name, only under
    ``srmech/cascade/catalogs/cascade_catalog/``, and only its ``operation``
    string is read. A parent with no descriptor gets no second path, and a
    sub-op absent from both the call graph and the chain still fails. The
    admission is reported (:func:`test_descriptor_admissions_are_reported`)
    rather than absorbed, so a row that starts leaning on it is visible.

    Today **every** ROSTER row passes on the call-graph path alone, so the
    second path admits nothing. It is landed before it is needed on purpose:
    a descriptor-sourced ``composes`` row would otherwise arrive as a red
    with a message accusing a correct declaration of being wrong.
    """
    offenders: Dict[str, List[str]] = {}
    for name, subs in ROSTER.items():
        found = _derived(name)
        chained = _descriptor_chain(name)
        missing = [s for s in subs
                   if s not in found and s.rsplit(".", 1)[-1] not in chained]
        if missing:
            offenders[name] = missing
    assert not offenders, (
        "declared sub-ops that no call-graph path reaches AND no cascade "
        f"descriptor chains: {offenders}. Either the declaration outran the "
        "code, or the call is dynamic / C-side and the row does not belong "
        "in ROSTER."
    )


def test_descriptor_admissions_are_reported() -> None:
    """Which rows lean on the descriptor path, PRINTED. Never a failure.

    An admission path nobody watches becomes the path everything takes. This
    prints the exact set each run, so "the call graph proves it" quietly
    turning into "the TOML says so" is visible at the moment it happens
    rather than at the next audit.
    """
    leaning: Dict[str, List[str]] = {}
    for name, subs in ROSTER.items():
        found = _derived(name)
        chained = _descriptor_chain(name)
        via = [s for s in subs
               if s not in found and s.rsplit(".", 1)[-1] in chained]
        if via:
            leaning[name] = via
    print(f"\n[rc417] clause-2 rows admitted via the DESCRIPTOR chain rather "
          f"than the call graph: {leaning or 'none'} "
          f"(of {len(ROSTER)} roster rows)\n")
    assert True


def test_the_descriptor_reader_actually_reads_something() -> None:
    """NON-VACUITY of the second admission path.

    A ``_descriptor_chain`` that always returned ``frozenset()`` would make
    the new path invisible — clause 2 would behave exactly as it did at
    rc416 and this rc's stated fix would be a no-op nobody could detect.
    ``best_rational_signed`` is the worked example the docstring names, so it
    is the one asserted.
    """
    chain = _descriptor_chain("srmech.cascade.best_rational_signed")
    assert {"pin_slot_at_zero", "best_rational", "reorient"} <= chain, (
        "the cascade descriptor for best_rational_signed did not yield its "
        f"own operation chain; got {sorted(chain)}. The catalog moved, the "
        "field was renamed, or the parse silently returned nothing — in any "
        "of those cases the second admission path is dead and clause 2 is "
        "back to being laterally wrong without saying so.")
    assert _descriptor_chain("srmech.biology.genome.genome_from_graph") == frozenset(), (
        "an op with no cascade descriptor must yield an EMPTY chain, not a "
        "fallback that admits anything")


# ──────────────────────────────────────────────────────────────────────
# Clause 3 — SHAPE. Directed, irreflexive, acyclic.
# ──────────────────────────────────────────────────────────────────────


def test_no_op_composes_itself() -> None:
    """``composes`` is "built FROM", so a self-edge is meaningless."""
    for name, subs in _declaring().items():
        assert name not in subs, f"{name} lists itself in composes"


def test_the_declared_relation_is_acyclic() -> None:
    """A cycle would say two ops are each built from the other. Depth-first,
    over the declared edges only — the derived graph is a different object
    and is NOT asserted acyclic (mutual recursion through helpers is legal
    code; a mutual BUILT-FROM claim is not)."""
    edges = _declaring()
    state: Dict[str, int] = {}          # 1 = on stack, 2 = done

    def walk(node: str, path: List[str]) -> None:
        state[node] = 1
        for nxt in edges.get(node, ()):
            if state.get(nxt) == 1:
                raise AssertionError(
                    f"composes cycle: {' -> '.join(path + [node, nxt])}")
            if state.get(nxt) != 2:
                walk(nxt, path + [node])
        state[node] = 2

    for start in edges:
        if state.get(start) != 2:
            walk(start, [])


# ──────────────────────────────────────────────────────────────────────
# The READER — rc412's other half, and the reason the population is allowed
# to be small.
#
# Populating a field nothing reads only moves a hash. Through rc411 the ONLY
# consumers of `composes` were `ToolEntry.to_jsonable`, the curated merge and
# the C serialiser — none of them a question a caller asks.
#
# `ToolSchema.composition()` is the reader, and the REVERSE direction is the
# capability it adds. Downward ("what is X built from") was always one
# attribute access away. Upward ("what is built from X") had no reader at
# all, and cannot be got without a full-registry pass — which is exactly the
# second call ADR-0012's autonomous-composition standard forbids.
# ──────────────────────────────────────────────────────────────────────


def test_the_reverse_edge_is_answerable_and_non_vacuous() -> None:
    """⚠️ NON-VACUITY. ``composed_by`` must actually name something.

    A reverse index that returned empty for every op would satisfy every
    consistency check below and be worthless. ``klein4_bind`` is the measured
    fan-in hub of the current roster.
    """
    got = _SCHEMA.composition("srmech.math.hdc.klein4_bind")
    assert got is not None
    assert got["composed_by"], (
        "the reverse edge is empty for an op three roster rows declare — the "
        "inversion is not happening")
    # rc423: klein4_bind's fan-in now spans BOTH populations (three ROSTER
    # rows plus rc423 SINGLE-tier rows), so the cross-check reads the live
    # declaring map rather than ROSTER alone — indexing ROSTER here would
    # KeyError on a perfectly valid rc423 parent.
    declaring = _declaring()
    for parent in got["composed_by"]:
        assert "srmech.math.hdc.klein4_bind" in declaring[parent]


def test_composition_agrees_with_the_registry_in_both_directions() -> None:
    """Every declared edge appears downward on the parent and upward on the
    child, over the WHOLE registry — not just the rows the roster names."""
    for name, subs in _declaring().items():
        down = _SCHEMA.composition(name)
        assert down is not None and down["composes"] == subs, name
        for sub in subs:
            up = _SCHEMA.composition(sub)
            assert up is not None, f"{sub} does not resolve"
            assert name in up["composed_by"], (
                f"{name} declares {sub} but {sub}.composed_by omits it")


def test_composition_distinguishes_a_leaf_from_a_missing_op() -> None:
    """A leaf answers with empty ``composes``; an unknown name answers ``None``.

    Collapsing those two would make "the registry has nothing for this" and
    "this op composes nothing" the same answer, and only one of them means
    the caller should stop looking.

    rc423 (`#T1113`) — WHY THIS TEST MOVED, AND WHAT IT WAS ACCIDENTALLY
    ASSERTING
    ====================================================================
    Through rc422 this pinned ``sha256_bytes`` to *both* tuples empty. Only
    the first was the property under test; the second was an artefact of a
    16-row population in which nothing yet declared the tree's most-composed
    primitive. rc423's seeding pass gives ``sha256_bytes`` **8** parents, all
    of them true, and the old assertion went red for a change that is the
    whole point of the rc — a textbook incidental pin.

    So the leaf-vs-missing distinction is now asserted on ``composes`` (the
    direction the docstring is actually about), and the two-empty-tuples
    shape is asserted separately on an op that genuinely has no edge in
    either direction. Both facts still ship; neither is now hostage to the
    population growing.
    """
    leaf = _SCHEMA.composition("srmech.amsc.format.sha256_bytes")
    assert leaf is not None
    assert leaf["name"] == "srmech.amsc.format.sha256_bytes"
    assert leaf["composes"] == ()          # a leaf DOWNWARD — the claim here
    assert leaf["composed_by"], (
        "sha256_bytes is the registry's most-composed primitive; an empty "
        "reverse edge means the inversion stopped working")

    # An op with no edge in EITHER direction still answers with two empty
    # tuples rather than None, which is the shape the reader promises.
    isolated = _SCHEMA.composition("srmech.amsc.format.read_ndjson")
    assert isolated == {
        "name": "srmech.amsc.format.read_ndjson",
        "composes": (),
        "composed_by": (),
    }
    assert _SCHEMA.composition("definitely_not_a_registered_op") is None


def test_composition_resolves_a_bare_leaf_name() -> None:
    """The reader inherits ``resolve``'s contract — a bare leaf works."""
    assert _SCHEMA.composition("gf_rref") == _SCHEMA.composition(
        "srmech.math.modular_linalg.gf_rref")


# ── the search index — the second, WEAKER half of the reader ──────────
#
# `search.py::_op_fields` indexed name / category / summary / explanation /
# example.* and stopped there, so the two structured fields were outside the
# retrieval corpus for no stated reason. rc412 puts them in.
#
# MEASURED, and worth stating because it bounds the claim: over the 27
# declared sub-op references shipped at rc412 the `composes` text wins the
# `why` attribution on ZERO of them, because a row's own prose almost always
# already names the ops it composes. So the INDEX is not where the value is —
# `composition()` above is. What the index buys is that the field is no
# longer silently excluded from the corpus, and that a future declaration
# naming an op the prose does NOT mention becomes findable at all.


def test_op_fields_carries_composes_for_a_declaring_row() -> None:
    """The index frame for a declaring row includes a ``composes`` field
    whose text holds the declared sub-op names."""
    from srmech.introspect.search import _op_fields

    name = "srmech.math.kepler.pin_slot"
    fields = dict(_op_fields(_BY_NAME[name]))
    assert "composes" in fields, (
        "the index does not carry composes — the reader is not wired")
    for sub in ROSTER[name]:
        assert sub in fields["composes"], (
            f"{sub} missing from the indexed composes text")


def test_op_fields_omits_the_field_for_a_leaf_op() -> None:
    """A leaf op contributes no ``composes`` label and no bytes — the same
    key-omission ``to_jsonable`` and the C serialiser perform. Empty is the
    correct default and must stay free."""
    from srmech.introspect.search import _op_fields

    fields = dict(_op_fields(_BY_NAME["srmech.amsc.format.sha256_bytes"]))
    assert "composes" not in fields
    assert "preserves" not in fields


def test_the_indexed_composes_text_is_reachable_by_a_query() -> None:
    """END TO END through the real index: a query built from a declared
    sub-op returns the composite that declares it.

    This does NOT assert ``why == "composes"`` — measured above, the row's own
    prose out-scores the tuple on every reference shipped today, and pinning
    an attribution the data does not support would be a test asserting a
    wish. What it does assert is that the frame carrying the tuple is in the
    corpus and reachable, which is the part rc412 changed.
    """
    from srmech.introspect.search import _build_frames

    frames, _witness = _build_frames("ops")
    by_name = {f.name: f for f in frames}
    for name, subs in ROSTER.items():
        labels = {label for label, _ in by_name[name].fields}
        assert "composes" in labels, (
            f"{name} declares a composition but its index frame has no "
            "composes field")
        blob = by_name[name].blob
        for sub in subs:
            assert sub.encode("utf-8") in blob, (
                f"{sub} is not in {name}'s indexed frame bytes")
