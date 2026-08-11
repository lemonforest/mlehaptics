"""rc361 (`#T1034`) — the op-name-SET witness: the instrument a rename trips.

WHY THIS EXISTS. ADR-0010 declustering moves ~73 modules between top-level
namespaces. Before rc361 the tree had **no gate that detects a rename**. It had
54 test files / 60 assertions pinning the op COUNT, and a count is the wrong
quantity: a rename relocates names and leaves cardinality untouched. Measured
2026-07-29 by simulating this ADR's own example move (``rational`` from
``srmech.amsc`` to ``srmech.math`` — the move rc373 has since actually made):
28 of 516 dotted names relocate, the total stays **516**, and every one of those
60 pins stays GREEN.

That is an **EMPTY** null about the pins, not a defect — `len(...)` measures
cardinality and measures it correctly. It is a real gap about the arc. This file
closes it by pinning the SET, not the size.

⚠️ THE MANIFEST IS HAND-COMMITTED ON PURPOSE — DO NOT WIRE IT INTO CODEGEN.
`tests/registered_op_names.txt` is NOT emitted by `tools/regen_all.py` or by
`tools/codegen_manifest.py`, and `test_the_manifest_is_not_codegen_emitted`
below asserts that it stays that way. The reason is the whole point of the
instrument: a rename arc runs `python tools/gen_*.py` as a matter of course, so
a codegen-emitted manifest would be rewritten by the very change it is meant to
detect and go green unconditionally — reproducing the exact failure mode
(a probe that cannot come out otherwise) that this file was written to fix.

TO CHANGE THE NAME SET DELIBERATELY, two edits are required, in the same commit:
  1. rewrite the manifest:
       python -c "from srmech.introspect.tool_schema import get_tool_schema; \
                  ns=sorted(e.name for e in get_tool_schema().tools); \
                  open('tests/registered_op_names.txt','w',encoding='utf-8', \
                       newline='\\n').write('\\n'.join(ns)+'\\n')"
  2. update `EXPECTED_NAME_SET_SHA256` and `EXPECTED_N` below to what the failure
     message prints.
Needing TWO edits is deliberate: a careless single-file regen cannot silently
pass, because the digest is pinned in source and the names are pinned on disk.
"""
from __future__ import annotations

from pathlib import Path

from srmech.amsc.format import sha256_bytes
from srmech.introspect.tool_schema import get_tool_schema

MANIFEST = Path(__file__).resolve().parent / "registered_op_names.txt"

#: Registered public-callable count, srmech-owned. Pinned here only so the
#: failure message can say "N -> N+1" instead of dumping every name; the SET
#: below is the actual contract.
#: (This illustrated the message with the frozen literals "516 -> 517" from
#: rc361 until rc410 (`#T1085`) — stale by 40 ops, in a comment whose only job
#: was to show the CURRENT value, sitting two lines above the real one. Written
#: symbolically now so it cannot go stale a second time.)
EXPECTED_N = 605  # rc422 (local task T1123): 598 -> 605, the centre/covering layer (5 srmech.math.covering ops) + the 2 Z(Spin(8)) rep-kernel anchor ops  # rc420 (local task T1114): 569 -> 598, the 29 cascade-catalog leaf-inventory + runner registrations

#: sha256 over the NORMALISED manifest body — "\n".join(sorted names) + "\n",
#: UTF-8. Normalised rather than raw-file-bytes so a CRLF checkout cannot make
#: the digest disagree between the Windows and Linux CI cells; that would be a
#: platform artifact masquerading as a rename.
# v0.9.0rc381 (`#T1052`) — regenerated for the ADR-0010 physics rename: the 99
# ``srmech.qm.*`` op names became ``srmech.physics.qm.*`` (the qm subpackage moved
# under the new srmech.physics domain). EXPECTED_N stayed 532 — a pure rename, the
# exact SAME-COUNT set change no count-pin can see and this witness exists to catch.
# v0.9.0rc383 (`#T1054`) — one genuinely NEW op: srmech.cascade.defect_ladder (the
# rung-indexed property-loss ladder + per-rung projector). 532 -> 533, digest below.
# v0.9.0rc384 (`#T957`) — two genuinely NEW ops: srmech.cascade.octonion_frame_read
# (the 𝕆 frame-committed quaternionic-Hopf coherence read) and
# srmech.math.laplacian.octonion_laplacian (the 𝕆 gain Laplacian measuring the
# frame-committed coherence ceiling). 533 -> 535, digest below.
# v0.9.0rc385 (`#T1048`) — two genuinely NEW ops: srmech.physics.qm.quaternion.quaternion_log
# (the INVERSE of quaternion_exp — the unit-quaternion log map) and
# srmech.physics.qm.quaternion.quaternion_slerp (the exp/log geodesic
# interpolation on S³). 535 -> 537, digest below.
# v0.9.0rc386 (`#T1062`) — one genuinely NEW op: srmech.cascade.cd_three_form (the
# exact-ℚ G₂ associative 3-form φ = Re(x̄·(y·z)), the scalar Re-twin of the vector
# associator). 537 -> 538, digest below.
# v0.9.0rc387 (`#T1037`, closing `#T1032`) — two genuinely NEW ops:
# srmech.cascade.flip_pair (the one-named-bit flexibility control) and
# srmech.cascade.group_algebra_table (the wrong-quotient group ring ℝ[ℤ/dim] metric
# control) — rc360's declared STRUCTURED-negative-control residual, promoted from
# hand-rolled test code to registered ops. 538 -> 540, digest below.
# v0.9.0rc388 (`#T963`) — two genuinely NEW ops: srmech.math.octonion.oct_torsor_act
# (the RIGHT ℍ-torsor action t <| g = oct_mult(t, g) of the quaternion group on a
# seam coset) and srmech.math.octonion.oct_torsor_div (the unique g with t1 <| g == t2,
# = oct_mult(t1^8, t2)). 540 -> 542, digest below.
# v0.9.0rc390 (`#T961`) — one genuinely NEW op: srmech.biology.genome.split_defect
# (the ORDER-carrying octonion associativity read — the complement of the order-BLIND
# genome_octonion_associator; signbit(fold(word)) ^ signbit(fold(word[:k]).fold(word[k:]))).
# 542 -> 543, digest below.
# v0.9.0rc395 (`#T1000`) — REPLACE, net +1: removed the hardwired
# srmech.cascade.sedenion_zero_divisor_witness and added the two dim-general
# ops srmech.cascade.cd_zero_divisor_witness (the first witness at any rung — at
# dim 16 the identical e1+e10 / e4−e15 payload) and
# srmech.cascade.cd_zero_divisor_witnesses (the complete basis-pair set, 168 at
# dim 16). 543 -> 544, digest below.
# v0.9.0rc396 (`#T1031`, position-operator half) — two genuinely NEW ops:
# srmech.physics.qm.single_particle.clock_operator (the Weyl clock U = diag(ω^k) —
# the fenced position x̂ on a ring) and srmech.physics.qm.single_particle.shift_operator
# (the cyclic shift V — the group-level momentum), obeying U V = ω V U. 544 -> 546,
# digest below.
# v0.9.0rc398 (`#T1064`) — five genuinely NEW ops: the octonion MOUFANG LOOP surface,
# srmech.cascade.{moufang_residue, is_moufang, malcev_defect, unit_loop, loop_invariants}
# (the loop 𝕆 already IS, promoted from a test-only proof + the unnamed closure(8,[1..7])
# data to queryable exact-ℚ ops). 546 -> 551, digest below.
# v0.9.0rc399 (`#T1064` Tier 2/3) — five genuinely NEW ops: the octonion CAYLEY
# PLANE 𝕆P² surface, srmech.cascade.{jordan_product, cayley_plane_point,
# cayley_plane_incidence, octonion_hopf_base} (the Albert-algebra Jordan product,
# 𝕆P² rank-1 idempotent points, the trace-form incidence pairing, the 𝕆P¹≅S⁸
# octonionic Hopf base), plus srmech.math.laplacian.generalized_ngon (the guarded
# generalized-n-gon incidence-graph / Feit–Higman spectral read). 551 -> 556,
# digest below.
# rc411 (`#T1086`): +3 — the introspect INDEX and the registry's own front door.
# srmech.introspect.search.search (the need-shaped ranked index over the tool +
# carrier registries) plus srmech.introspect.tool_schema.{get_tool_schema,
# tool_schema_view}, which were the functions that RETURN the registry and were
# not IN it: before this rc the name `get_tool_schema` matched 0 of 556 rows.
# 556 -> 559, digest below.
# rc414 (`#T1092`): +1 — srmech.biology.coupling.fold_identity. NOT a new op: it
# has been shipped and `coupling.__all__`-exported since task #723, and is named
# in RecoverableFold's own class docstring. It simply never carried a ToolEntry,
# while all seven of its `coupling` siblings did — so it was absent from
# describe(), from the MCP tool list, and from every registry-driven census.
# That invisibility has a measured cost: a research leg reading the coupling
# module concluded RecoverableFold "cannot be gated" while its purpose-built
# three-valued gate (EQUAL / NOT_EQUAL / UNKNOWN) sat 215 lines below the line
# it was reading. This witness could not have caught that, because an op absent
# from the registry is absent from the live set too — the gap was in what got
# REGISTERED, not in what drifted. 559 -> 560, digest below.
# rc419 (`#T1110`): +9 — the srmech.signal_processing DISPATCHER + PATH-REGISTRY
# read surface: cascade_dispatcher.{dispatch, begin_cascade, end_cascade,
# current_cascade, resolve_path, is_dispatch_table_locked} and
# path_registry.{has_path, lookup, registered_ops}. Same shape as rc414's
# fold_identity and not new code either — README.md demonstrates these BY NAME
# as the package's entry point, and every one of them was unregistered, so the
# MCP tool list carried 559 definitions of which ZERO mentioned
# signal_processing and introspect.search returned the op for 0 of 41 target
# queries (8/8 positive controls passed, so that null is REFUTED, not
# unsupported). These are the FIRST nine signal_processing rows in the registry.
# 560 -> 569, digest below.
# v0.9.0rc422 (`#T1123`) — the CENTRE / COVERING layer. Seven new names: the five
# srmech.math.covering ops (center_parity / center_lift / lift_fibre /
# linking_number_cwf / covering_catalog) and the two Z(Spin(8)) rep-kernel anchor
# ops (srmech.physics.qm.triality.spin8_center / triality_rep_dictionary). All
# ADDITIONS, no rename: srmech carried algebras and finite groups (local /
# quotient objects) with no way to hold the global (pi_1 / centre) datum, and six
# shipped ops had each hand-rolled the same centre-parity shadow. 598 -> 605,
# digest below.
EXPECTED_NAME_SET_SHA256 = (
    "4ce7dd526dfb5d97d4a4423e1c3ae29ee8a28568e9720d87454922e5832a32b5")


def _live_names() -> list[str]:
    """The op names SRMECH ITSELF registers.

    v0.9.0rc410 (`#T1085`) — this read `get_tool_schema().tools`, the UNFILTERED
    view, which deliberately publishes `srmech_tools + profile_tools`. The
    manifest next door is a witness to SRMECH's op names, so comparing it
    against a set that can contain a third party's rows is a basis mismatch:
    with any profile active, `test_the_live_name_SET_matches_the_manifest` fails
    on `added(1): ['<profile>.op']` — a false rename report.

    Note this is NOT reachable by repointing `EXPECTED_N`: the SET assertion
    fires first, so the count pin never gets a say. The count is the weaker
    check here; the SET is the contract.
    """
    return sorted(e.name for e in get_tool_schema().by_owner("srmech"))


def _manifest_names() -> list[str]:
    text = MANIFEST.read_text(encoding="utf-8")
    return [ln for ln in text.splitlines() if ln.strip()]


def _normalised(names: list[str]) -> bytes:
    return ("\n".join(names) + "\n").encode("utf-8")


def test_manifest_exists_and_is_line_per_name() -> None:
    assert MANIFEST.exists(), (
        f"{MANIFEST.name} is missing — it is the rename witness and it is "
        f"HAND-COMMITTED, so nothing regenerates it for you. See this module's "
        f"docstring for the two-edit procedure.")
    names = _manifest_names()
    assert names == sorted(names), "the manifest must be sorted"
    assert len(names) == len(set(names)), "the manifest has duplicate names"


def test_the_live_name_SET_matches_the_manifest() -> None:
    """⚠️ THE RENAME GATE. Set equality, not cardinality.

    A rename shows up here as one name in `added` and one in `removed` while the
    counts are identical — which is precisely the case every count-pin in the
    tree is blind to.
    """
    live, pinned = _live_names(), _manifest_names()
    added = sorted(set(live) - set(pinned))
    removed = sorted(set(pinned) - set(live))
    assert not (added or removed), (
        "the registered op-name SET changed.\n"
        f"  live {len(live)}  pinned {len(pinned)}"
        f"{'  (SAME COUNT — a rename, which no count-pin can see)' if len(live) == len(pinned) else ''}\n"
        f"  added({len(added)}):   {added[:12]}\n"
        f"  removed({len(removed)}): {removed[:12]}\n"
        "If this is a DELIBERATE rename or an intended new op, follow the "
        "two-edit procedure in this module's docstring — rewrite the manifest "
        "AND update EXPECTED_NAME_SET_SHA256 / EXPECTED_N in the same commit.")
    assert len(live) == EXPECTED_N, (
        f"count moved {EXPECTED_N} -> {len(live)}; update EXPECTED_N")


def test_the_manifest_digest_is_pinned_in_source() -> None:
    """The second of the two required edits. Pinning the digest in SOURCE means
    a rewrite of the data file alone cannot pass."""
    got = sha256_bytes(_normalised(_manifest_names()))
    assert got == EXPECTED_NAME_SET_SHA256, (
        f"manifest digest drifted.\n  expected {EXPECTED_NAME_SET_SHA256}\n"
        f"  got      {got}\n"
        "Update EXPECTED_NAME_SET_SHA256 to the 'got' value IN THE SAME COMMIT "
        "as the manifest rewrite.")


def test_the_witness_can_actually_fail_on_a_rename() -> None:
    """⚠️ NON-VACUITY. A gate that cannot fail is not evidence.

    Mutate one name with the SAME cardinality — exactly what declustering does —
    and prove (a) the set comparison catches it and (b) a count comparison does
    NOT. The second half is the measured indictment of the count-pins, asserted
    rather than asserted-about.
    """
    pinned = _manifest_names()
    renamed = sorted(
        ["srmech.zzzns.rational" + n[len("srmech.math.rational"):]
         if n.startswith("srmech.math.rational") else n
         for n in pinned])

    assert len(renamed) == len(pinned), "the simulation must preserve cardinality"
    moved = sum(1 for n in pinned if n.startswith("srmech.math.rational"))
    assert moved > 0, "the simulated prefix matches nothing — probe is inert"

    # (a) the SET witness sees it
    assert set(renamed) != set(pinned)
    assert sha256_bytes(_normalised(renamed)) != EXPECTED_NAME_SET_SHA256
    # (b) a COUNT witness is blind to it — this is why this file exists
    assert len(renamed) == EXPECTED_N


def test_the_manifest_is_not_codegen_emitted() -> None:
    """⚠️ If codegen ever writes this file, the witness dies silently.

    The rename arc runs the generators as routine work. A generated manifest
    would be rewritten by the change it is meant to detect and go green
    unconditionally. Keep it hand-committed.
    """
    tools = Path(__file__).resolve().parents[1] / "tools"
    assert tools.is_dir(), tools
    writers = [p.name for p in sorted(tools.glob("*.py"))
               if MANIFEST.name in p.read_text(encoding="utf-8", errors="replace")]
    assert writers == [], (
        f"{MANIFEST.name} is referenced by codegen tool(s) {writers}. If a "
        f"generator now writes it, this witness can no longer detect a rename — "
        f"it would be regenerated by the same command the rename arc runs. Keep "
        f"the manifest hand-committed and review-gated.")
