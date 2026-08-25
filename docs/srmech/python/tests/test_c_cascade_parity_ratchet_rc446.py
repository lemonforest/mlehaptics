"""`#T1141` / gh #1653 — the C-projection cascade-parity ratchet. DOWN-ONLY.

srmech is a MULTI-IMPLEMENTATION codebase (ADR-0009): the scripting-coherency
projection (``python/srmech``) and the compiled-coherency projection (``c/src``)
are CO-EQUAL. The config-driven cascade surface violates that: of the 18
executable ``[cascade]`` descriptors, the C run loop accepted **0** when this
file landed at rc445, and accepts **17** as of the rc452 Phase-2 K3 slice
— measured by this file's own ``_measure()``, and equal to 18 minus
:data:`CEIL_C_REJECTED_CHAINS` three screens down.

*(This paragraph said "accepts **0**" in undated present tense through rc449,
while the same file's ceiling said 9. Corrected at rc450 (`#T1160`) under the
scoped-edit license, since the BLOCKED table below is being synced in the same
change. A present-tense count in a docstring is a live claim, and nothing in
this tree reads a docstring — so it went two drains stale with no detector.
Corrected AGAIN at rc452 (`#T1166`), 9 -> 11, for the same reason and by the
same license: the ceiling moved twice in one rc and this sentence does not
derive from it. It is now phrased as "18 minus the ceiling" so a reader who
meets only this paragraph is pointed at the literal rather than given a second
copy of it.)*

This file exists so that gap can never again be invisible or silently deferred.
It lands BEFORE the fix on purpose — `#T1141`'s own finding is that the causal
variable is THE GATE, NOT INTENT: ungated surfaces trickle, gated ones race.

WHAT IS GATED HERE
------------------
1. ``test_every_c_rejected_chain_is_enumerated`` — the INVARIANT, and the one
   that matters. Every chain the C projection cannot run must appear in
   :data:`BLOCKED` with a named gate and a disposition. A chain rejected for an
   UNLISTED reason FAILS. This is an invariant, not a pinned integer, so it does
   not rot as the catalog grows — a new descriptor that C cannot run is caught on
   arrival rather than silently widening a count.
2. ``test_c_rejected_chain_count_is_tight`` — down-only, pinned TIGHT (``==``,
   not ``<=``), house style. Fixing a chain FORCES the literal down; you cannot
   silently improve either.
3. ``test_surface_a_unsupported_step_forms_is_tight`` — same, for step forms.
4. ``test_all_executable_chains_run_in_c`` — the TARGET. Marked
   ``xfail(strict=True)``, so it is RED-but-expected now and, the moment the work
   lands, XPASS makes it FAIL until the marker is deleted. That is the drain: the
   gate removes itself when it is satisfied, instead of quietly passing forever.

⚠️ WHAT A SEEDED CEILING CANNOT DETECT — stated because this project has been
bitten by prose claiming otherwise (srmech notebook §3.54). :data:`CEIL_*` below
is seeded at the MEASURED rc445 population. A ceiling seeded at the live
population is a claim about the FUTURE, not a detection of the PAST: it catches
the REGRESSION, never the original. It is also blind to a gap CLASS that does not
exist yet — a new step form nobody has written cannot be counted. Gate 1 is the
partial remedy (it is shaped as an invariant), and the gap ledger
(``notes/_1653_gap_ledger.py``) is the rest: it enumerates what the complete
surface required, including the rows this ratchet cannot see.

TWO GRAMMARS — do not conflate them (measured, gh #1653):
  SURFACE A  ``[[cascade.chain.steps]]``  ``srmech/cascade/compose.py``, ADR-0008.
             ALL 21 packaged descriptors use this one. C executes 3 of 3 forms
             as of rc452 (`#T1166`) — plain, fold and map. *(This line read
             "1 of 3" from rc446 until rc452 and was correct for that whole
             span; it is a live claim in a docstring, so it is corrected in the
             same change that moved CEIL_SURFACE_A_UNSUPPORTED_FORMS to 0
             rather than left to drift the way the paragraph above did twice.)*
  SURFACE B  ``[[stage]]``  ``srmech/dsl/_toml_chain.py``, peer
             ``srmech_dsl_chain_run``. C executes 5 of 6; only ``parallel_body``
             is deferred, deliberately, as a host-thread affordance.
This file gates SURFACE A, because that is the one the shipped catalog uses.
"""
from __future__ import annotations

import ctypes
import json

import pytest

import srmech
from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat

# ── down-only ceilings, seeded at the MEASURED rc445 population ──────────────
# Re-measured at rc445 by notes/_1653_chain_census_rc444.py:
#   "CENSUS of 18 executable chains (20 chain-variants): ...
#    C srmech_chain_run ACCEPT=0 REJECT=18 ... UNATTRIBUTED=0"
CEIL_C_REJECTED_CHAINS = 0            # of 18 executable. TARGET REACHED.
#   1 -> 0 within rc452 (`#T1166`): parallel_sector_dispatch, all 4 proof cases
#   BYTE_IDENTICAL. ⚠️ AT ZERO THE STRICT-XFAIL ON
#   test_all_executable_chains_run_in_c IS DELETED and that test now ASSERTS —
#   the drain removing its own gate, which is what the marker was for.
#   All THREE of its gates fell together, which is why it could not be halved:
#   GATE_CARRIER to the `m` (mapping) and `o` (bool) wire kinds, GATE_OP_TABLE
#   to the one wave-F row, and GATE_REF_GRAMMAR to the `@op` namespace — which
#   is resolved as a CR_OP_REG row lookup plus a `un` column, NOT as a callable
#   registry. That distinction is the whole reason it could close: JPL Rule 9
#   bans function pointers, so the "callable registry" this file's own
#   GATE_REF_GRAMMAR comment predicted would be needed is not buildable here,
#   and naming the row's unary identity as data is what replaces it.
#
#   ⚠️ WHAT ZERO DOES NOT MEAN. Its four proof cases all collapse to
#   n_distinct == 1 (body=chiral_flip is symmetric under both Klein-4 axes), so
#   the collapse-lattice partition is executed only at its degenerate value.
#   Two silent-wrong-value defects in that partition were found by
#   differential-testing it against _distinct_classes directly and fixed before
#   landing; neither was reachable through any proof case, and neither would
#   have been caught by this ratchet or by the value comparator.
#   2 -> 1 within rc452 (`#T1166` Phase 2, the K3 slice): schur_complement,
#   all 3 proof cases BYTE_IDENTICAL. THE ONLY DRAIN IN THIS ARC THAT BUILT
#   NEW SUBSTRATE rather than dispatching an existing symbol: measured
#   before writing it, c/include/srmech.h declares ZERO schur / dirichlet /
#   neumann symbols and no c/src TU defines one — the op's name occurs in
#   the tree only as DATA in two generated registry tables, and it is one
#   of the six ABSENT ops in the gh #1653 symbol-gap census. The arm is
#   composed over srmech_dense_solve_f64_ws, the same Class-L float
#   primitive the Python op's float path composes over for the same
#   sub-problem, with the boundary combine transcribed in PYTHON'S
#   accumulation order because the comparator is bit-exact and float
#   addition is not associative. GATE_CARRIER fell to the `x` WIRE KIND
#   (the new type its `new_type: True` flag predicted); GATE_OP_TABLE fell
#   to the one wave-E row.
#   3 -> 2 within rc452 (`#T1166` Phase 2, the K1 slice): encode_loe_content,
#   all 4 proof cases BYTE_IDENTICAL under the rc450 typed comparator. Its
#   two gates closed together, which is why it could not be halved:
#   GATE_OP_TABLE fell to four wave-D atom rows (sha256_raw / mint_vector /
#   permute / bind, each delegating to ONE step-granular compiled export
#   the Python op itself composes — srmech_sha256_hex, srmech_mint_vector,
#   srmech_hdc_permute, srmech_hdc_bind), and GATE_CARRIER fell to the `b`
#   WIRE KIND, which is the new type this chain's `new_type: True` flag
#   predicted. The rc452 wave-C phase had placed a deliberate FINAL-decline
#   in cr_run_and_write for exactly this case; the `b` arm in cr_desc_scalar
#   replaces it, and ABI 21 -> 22 rides with the widened kind vocabulary.
#   The rc445 baseline was 18, verified against a PRISTINE origin/main .so with
#   THIS harness — so the drain is attributable to the code, not to the probe.
#   The drain, in full: 18 (rc445) -> 12 when the cr_dispatch arm closed the 6
#   Class-I cyclic chains -> 11 at rc446 (the fold FORM, for one body op) -> 9
#   at rc447 (CR_DBL and @step[N].output[K] element indexing, which between them
#   released `magnitude` and `chiral_dual`).
#
#   ⚠️ This narrative stopped at "12 -> 11" through rc449 and so explained a
#   constant TWO decrements behind the literal it sits above. Extended at rc450
#   (`#T1160`). rc450 itself moves it by ZERO, deliberately: it ships no C
#   capability, on the reasoning that the instrument which makes the next
#   decrement trustworthy has to predate the decrement it judges. That
#   instrument is tests/test_c_cascade_value_parity_rc450.py — until it landed,
#   "accepted" meant rc == 0 and nothing had ever decoded the returned VALUE.
#
#   4 -> 3 within rc452 (gh #1653, the registry-ripple phase): klein4_from_one,
#   BOTH variants, all 7 proof cases BYTE_IDENTICAL under the rc450 typed
#   comparator. Its one gate was GATE_OP_TABLE, and the blocker inside that
#   gate was REGISTRATION, not code: cr_args_keyset_ok refuses by design to
#   dispatch an op with no ToolEntry, and `render_template` carried none — so
#   the ToolEntry registration (with `sha256_raw` / `mint_vector` for the
#   sibling encode_loe_content chain) landed in the same change as the six
#   CR_OP_REG rows (render_template / utf8_encode / sha256_bytes / str_concat
#   / byte_slice / int_parse_le, wave C). The str/bytes boundary rides an
#   `is_bytes` carrier flag (the `is_tuple` precedent): NO new wire kind,
#   because the chain's FINAL value is a list of ints — a bytes FINAL still
#   declines until the `b` kind ships with encode_loe_content.
#
#   7 -> 4 within rc452 (`#T1166` Phase 3): kuramoto_step (BOTH variants),
#   quaternion_dft and octonion_dft, all with the value channel open — 23 of 23
#   representable proof-case rows BYTE_IDENTICAL under the rc450 typed
#   comparator, a step-mutation witness per chain (an interior bind/seed
#   literal the fused symbols have no parameter image of), and both witness
#   arms firing on every step (51/51 decline, 51/51 value-move). The atoms are
#   STEP-granular on purpose: the fused srmech_cascade_kuramoto_step_f64 /
#   _general_f64 / srmech_quaternion_dft / srmech_octonion_dft symbols are
#   NOT referenced by the interpreter TU (the no-coarse source gate widened to
#   pin all four). Two latent defects surfaced and fixed in the same stroke:
#   CR_BIND_MAX 8 declined the general variant's NINE-bind map frame (read as
#   an op-table gap until measured), and _spec_to_chain_dict could not spell a
#   MAP step at all — resolve_chain CRASHED (AttributeError) on every map
#   chain with a native lib present, invisibly to every ctypes-driven gate.
#   9 -> 8 at rc451 (`#T1164`, gh #1653 item 4): best_rational_signed. THE FIRST
#   DECREMENT THIS RATCHET HAS EVER MADE WITH THE VALUE CHANNEL OPEN — every
#   earlier one was rc == 0 and nothing more. Its 9 JSON-representable proof
#   cases are BYTE_IDENTICAL under the rc450 typed comparator (its 10th, a
#   non-finite x, never reaches C and stays in CEIL_NONFINITE), and the
#   comparator's population stayed 0-DIVERGENT.
#
#   ⚠️ AND THE OPEN VALUE CHANNEL IMMEDIATELY EARNED ITS KEEP. The first run of
#   the newly-accepted chain returned (22.0, 7) against Python's (22, 7): the
#   interpreter's `reorient` arm read every operand through cr_arg_dbl and
#   answered CR_DBL unconditionally, where the Python op's docstring states
#   "int in -> int out". A LATENT WRONG ANSWER that had been dispatchable since
#   rc447 and was invisible because no accepted chain had ever handed reorient
#   an integer. Under the pre-rc450 ratchet — rc == 0, no decode — this
#   decrement would have been recorded as a clean win. Fixed at root in the same
#   change (cr_op_reorient now branches on the carrier kind).
#
#   ⚠️ WHAT rc451 DELIBERATELY DID NOT DO. srmech_cascade_best_rational_signed_f64
#   already fuses this whole chain, and it is MEASURED value-identical to the
#   six declared steps over the entire C-accepted domain (notes/
#   _1653_rca_probe_rc451.py block D: agree=10 disagree=0). Dispatching it would
#   have moved this ceiling with one arm and left the descriptor's steps driving
#   nothing — and NO value-level gate could have seen the difference. The four
#   step ops are separate dispatch arms instead (rc451 put them in
#   cr_dispatch_real; they are rows in the shared CR_OP_REG table since the
#   rc452 A1 reshape deleted that function), and the interpreter
#   TU is pinned to reference no multi-step coarse cascade symbol
#   (test_no_coarse_cascade_symbol_in_the_interpreter_rc451.py), because for
#   this defect class the value channel is provably blind and a source-shape
#   gate is the only instrument that can still return otherwise.
CEIL_SURFACE_A_UNSUPPORTED_FORMS = 0   # TARGET REACHED. All three forms execute.
#
# ⚠️ 2 -> 1 -> 0 AT rc452 (`#T1166`), in two steps within the one rc, each
# forced by this gate's own `==`. The MAP half is the second: `cr_drive` is an
# explicit-frame-stack trampoline implementing compose.py's map contract — `n`
# pinned at entry, binds resolved ONCE in the enclosing scope, body-local step
# outputs, layered idx/bind environments, and the map returning the list of body
# finals. The `@idx` / `@bind` namespaces close with it; measured, they occur
# ONLY inside map bodies, so they are frame bindings rather than a wider path
# grammar, which is why they could not be closed before the form existed.
#
# ⚠️ THE FORM RUNNING IS NOT THE CHAINS RUNNING, and this ceiling has been
# careful about that distinction twice before. It says the three step FORMS
# execute. `CEIL_C_REJECTED_CHAINS` is the separate number, and the map chains
# still need their atoms.
#
# Verified on VALUES, not `rc == 0`: nested map with layered `@idx` shadowing,
# body-local `@step[0]` scoping (a chain step deliberately precedes the map, so
# a leaked scope would read it), `n` taken from len(map_over) rather than
# element values, the empty map returning `[]` without running the body (a live
# proof case on autocorrelation and kuramoto_step), and an unbound `@idx` name
# DECLINING rather than resolving to 0.
#
# ⚠️ WHAT WAS 2 -> 1: the fold half.
# Through rc451 this stayed at 2 with a real fold chain shipping, because the
# fold BODY dispatched through a PRIVATE single-entry table (``cr_fold_body``,
# ``orientation_compose`` only) rather than through the shared op table — so a
# fold over any other op declined, and the probe below folds ``gcd`` precisely
# to measure that. The old note said lowering it "on the strength of one working
# chain would be the looks-done-isn't move", and it was right.
#
# rc452 removes the condition rather than the measurement: ``CR_OP_REG`` becomes
# the shared atom table whose rows carry a ``bin`` enum column (the A1 dispatch —
# the first cut's function-pointer columns violated JPL Rule 9), and
# ``cr_fold_body`` resolves through THAT — the same table, the same matcher, as
# ``cr_dispatch``. The ``gcd`` probe now runs and returns 6, and
# tests/test_c_fold_step_form_rc446.py asserts the VALUE (plus an empty-fold
# case that proves the seed is read), not merely ``rc == 0``.
#
# ``map`` remains, and it is the whole residual: it needs the explicit frame
# stack JPL Rule 1 forces, which is filed as its own slice rather than
# half-done here.

SURFACE_A_STEP_FORMS = ("plain", "map", "fold")

# ── the five measured C-side gates (gh #1653) ────────────────────────────────
#
# ⚠️ Line numbers are deliberately NOT cited here any more. They were, and every
# one of them went stale within two rcs as the dispatch was split and the
# resolver grew — a citation that drifts is worse than none, because it reads as
# precise. Each gate names the FUNCTION instead, which survives an edit.
GATE_OP_TABLE = "op_table"          # cr_dispatch over CR_OP_REG -> NOT_IMPL
#                                     (cr_dispatch_real: deleted, rc452 A1).
#                                     Still the widest gate: it appears in ALL
#                                     THREE remaining BLOCKED rows. (Read "ALL
#                                     FOUR" until klein4_from_one closed late
#                                     in rc452, "ALL NINE" through the first
#                                     two phases of rc452 and "10 of 18" until
#                                     rc450 — each figure was correct when
#                                     written and moved with the drains.)
GATE_CARRIER = "carrier_width"      # cr_value_t kinds. NARROWED at rc447 —
#                                     CR_DBL + CR_LIST now ship, so this is down
#                                     to byte-buffer, dense-matrix and MAPPING
#                                     (parallel_sector_dispatch returns a dict).
GATE_REF_GRAMMAR = "ref_grammar"    # cr_resolve_ref. Element indexing
#                                     @step[N].output[K] SHIPPED at rc447; what
#                                     remains is the @op / @bind / @idx
#                                     namespaces, which need a callable registry
#                                     rather than a wider path walker.
GATE_REAL_ARG = "real_literal_arg"  # CLOSED at rc447 by CR_DBL. Kept as a name
#                                     so historical ndjson rows stay readable;
#                                     it must score ZERO from here on.
GATE_STEP_FORM = "step_form"        # surface-A forms. FOLD shipped at rc446 (for
#                                     one body op); MAP still needs the explicit
#                                     frame stack JPL Rule 1 forces.

VALID_GATES = frozenset({GATE_OP_TABLE, GATE_CARRIER, GATE_REF_GRAMMAR,
                         GATE_REAL_ARG, GATE_STEP_FORM})
#: ⚠️ "OPEN" WAS HERE AND IS GONE (rc447). ADR-0009 §5 names THREE dispositions,
#: and "OPEN" is not one of them — it is the unfiled decline spelled legally.
#: Every BLOCKED row below carried it, which meant this ratchet enumerated the
#: rejected chains (good) while permitting each one to say nothing about what
#: was being DONE about it (not good). Enumeration without disposition is
#: exactly the ADR-0009 §5 failure gh #1653 was opened to close, reproduced
#: inside the instrument built to close it.
VALID_DISPOSITIONS = frozenset({"CLOSED_IN_THIS_RC", "FILED_AS_NEW_ITEM",
                                "DECLINED_WITH_REASON"})

#: Every executable chain the C run loop cannot run, with its gate set.
#: ZERO ROWS MAY BE SILENT (ADR-0009 §5 forbids an unfiled decline, and this
#: issue exists *because* one went unfiled). Delete a row only when C runs it.
#
# ⚠️ SYNCED AT rc450 (`#T1160`), AND NOW GATED — read this before editing a row.
#
# The comment below has said "Gates are synced from
# notes/_1653_gate_matrix_rc445.ndjson" since rc445. It was not true. Measured
# at rc449 head by parsing both artifacts, THREE of the nine gate sets
# disagreed with the matrix they claimed to be synced from:
#   best_rational_signed   here [op_table, ref_grammar]   matrix [op_table]
#   octonion_dft           here 3 gates                   matrix 4 (+carrier_width)
#   quaternion_dft         here 3 gates                   matrix 4 (+carrier_width)
# Nothing could report it: test_every_blocked_row_is_ACTUALLY_FILED checks that
# each ``ledger_row`` id EXISTS and never that any field AGREES. So the sync was
# a claim in a comment, which is the shape this whole arc exists to remove.
# tests/test_blocked_row_agrees_with_gate_matrix_rc450.py now asserts the
# agreement in both directions, so the sentence below is checkable.
#
# ⚠️ ``new_type`` IS NOT SYNCED TO THE CITED LEDGER ROW, DELIBERATELY. The two
# fields have DIFFERENT SUBJECTS. A BLOCKED row is per-CHAIN and carries 1–4
# gates while citing exactly ONE ledger row; a ledger row is per-GAP. Setting
# the chain flag equal to one arbitrarily-chosen gap's flag would have written
# ``new_type=False`` onto ``best_rational_signed`` — the one chain whose closure
# definitionally introduces a new wire kind — and thereby disarmed the standing
# "a new TYPE closes its projection gap in the SAME change" rule at exactly the
# chain the next rc ships. Where the chain flag and the cited row's flag differ,
# the row MUST carry ``new_type_reason`` saying why; the rc450 gate enforces
# that, so a contradiction is expressible and documented but never silent.
BLOCKED = {
    # Each row: the measured gates, ONE ADR-0009 disposition, whether closing it
    # is a NEW TYPE (which must close its projection gap in the SAME change), and
    # the gap-ledger row that files it. Gates are synced from
    # notes/_1653_gate_matrix_rc445.ndjson, which cross-checks itself against
    # execution and against this file's ceiling.
    # autocorrelation's row was DELETED at rc452 (`#T1166`) — the chain runs,
    # all 5 proof cases BYTE_IDENTICAL. It carried all THREE of its gates being
    # closed in one rc: GATE_STEP_FORM (the map form, `cr_drive`),
    # GATE_REF_GRAMMAR (`@idx` / `@bind`, which are map-frame bindings and so
    # could not close before the form did) and GATE_OP_TABLE (seq_len,
    # correlation_product, compensated_sum as atom-table rows). It was
    # new_type=True against ledger row `step_form_map`, and that flag was
    # load-bearing exactly as the note above predicts: the MAP STEP FORM is the
    # new type, and it closed in the same change as the chain.
    # best_rational_signed's row was DELETED at rc451 (`#T1164`, gh #1653 item
    # 4) — the chain runs. It carried new_type=True against ledger row
    # wire_tuple_kind_absent, and that flag was load-bearing exactly as the
    # note above predicted: closing the chain DID widen a discriminator set
    # (srmech_chain_run's output-kind vocabulary gained `t`), and the projection
    # gap closed in the SAME change (the C `is_tuple` flag, the Python `t`
    # branch in _reconstruct_value, and ABI 19 -> 20 together).
    # encode_loe_content's row was DELETED at rc452 Phase 2 (`#T1166`, the K1
    # slice) — the chain runs, 4/4 proof cases BYTE_IDENTICAL. It carried
    # new_type=True against ledger row `carrier_bytes`, and that flag was
    # load-bearing exactly as the note above predicts: closing the chain DID
    # widen a discriminator set (srmech_chain_run's output-kind vocabulary
    # gained `b`), and the projection gap closed in the SAME change — the C
    # `cr_desc_scalar` bytes arm, the Python `b` branch in _reconstruct_value,
    # the EXPECTED_WIRE_KINDS pin and ABI 21 -> 22 together, with the chain's
    # own proof cases as the executed emitter so the kind is never declared
    # without something emitting it (the rc450 q/n/s hole, not re-created).
    # kuramoto_step's, quaternion_dft's and octonion_dft's rows were DELETED
    # at rc452 Phase 3 (`#T1166`) — all three run, 23/23 representable proof
    # cases BYTE_IDENTICAL, a mutation witness per chain and both step-drive
    # arms firing on every step. kuramoto closed through GATE_OP_TABLE +
    # GATE_STEP_FORM (five term ops at step granularity, the exact-ℚ Q61-sin
    # middle reproduced on the bigint carrier, the fold seed widened to
    # float/list); the DFTs additionally through GATE_CARRIER (nested-list
    # ingest/marshal already landed earlier in rc452; the as_quat4/as_oct8
    # coercion arms landed with the chains). Their step ops delegate ONLY to
    # the step-granular exports the Python ops themselves compose
    # (srmech_sin_q61 / srmech_sqrt_q61 / srmech_quaternion_twiddle +
    # _{left,right}_mult / srmech_octonion_twiddle +
    # srmech_loop_{left,right}_op_f64) — never the fused whole-transform
    # symbols, which the no-coarse source gate now pins by name.
    # klein4_from_one's row was DELETED at rc452 (gh #1653, the registry-ripple
    # phase) — the chain runs, BOTH variants, 7/7 proof cases BYTE_IDENTICAL.
    # Its one gate was GATE_OP_TABLE and the load-bearing half of that gate was
    # the ToolEntry REGISTRATION (render_template had none, and the key-set
    # validator refuses an unregistered op by design); the six wave-C atom rows
    # and the `is_bytes` carrier flag were the code half. Its `new_type` flag
    # pointed at ledger row `step_form_map`, which had already closed at Phase
    # 3 — the residual closure needed no new type, exactly as the mechanism
    # census predicted ("needs NO new wire kind").
    # parallel_sector_dispatch's row was DELETED at rc452 (`#T1166`) — the chain
    # runs, all 4 proof cases BYTE_IDENTICAL, and it was the LAST one, so this
    # table is now EMPTY. It carried new_type=True against ledger row
    # `carrier_mapping`, and that flag was load-bearing exactly as the note
    # above predicts: closing the chain DID widen a discriminator set
    # (srmech_chain_run's output-kind vocabulary gained `m` AND `o` — the only
    # closure in this arc to need two letters), and both projection gaps closed
    # in the SAME change: the C `is_map`/`is_bool` carrier flags, the Python `m`
    # and `o` branches in _reconstruct_value, the EXPECTED_WIRE_KINDS bijection,
    # REQUIRED_EMITTED_KINDS (which gained `b` and `x` in the same commit — a
    # verifier found they had never been added when those kinds landed) and
    # ABI 22 -> 23 together.
    # schur_complement's row was DELETED at rc452 Phase 2 (`#T1166`, the K3
    # slice) — the chain runs, 3/3 proof cases BYTE_IDENTICAL. It carried
    # new_type=True against ledger row `carrier_matrix`, and that flag was
    # load-bearing exactly as the note above predicts: closing the chain DID
    # widen a discriminator set (srmech_chain_run's output-kind vocabulary
    # gained `x`), and the projection gap closed in the SAME change — the C
    # `is_matrix` flag on cr_desc_close, the Python `x` branch rebuilding the
    # Mat carrier, the EXPECTED_WIRE_KINDS pin and the emitted-kind gate, all
    # under the ABI 22 the K1 slice already paid for (ONE bump for the rc, not
    # one per kind). Its chain is ONE step, so it contributes nothing to the
    # no-coarse population — that gate derives multi-step descriptors only,
    # and here the op IS the chain.
}

_STATUS = {0: "SRMECH_OK", 2: "SRMECH_ERR_BAD_INPUT", 5: "SRMECH_ERR_NOT_IMPL"}


def _executable_chains():
    """The executable descriptors, read LIVE — never a hard-coded list."""
    catalog = _cat.load_catalog()
    return sorted(n for n, d in catalog.items()
                  if _cc.descriptor_status(d) == "executable"), catalog


def _c_runs(chain_dict, ctx):
    """Drive the shipped ``srmech_chain_run``. Returns (rc, status).

    ⚠️ THE CTX MUST BE WRAPPED — ``{"row": …, "inputs": …}``. ``srmech_chain_run``
    reads ``srmech_json_object_get(ctx, "inputs")`` (srmech_compose_run.c:809), so
    a BARE ``{"a": 12}`` leaves ``c->inputs`` NULL and every ``@input.*`` ref
    fails to resolve — the whole chain then returns NOT_IMPL and looks like a
    grammar gap when it is a harness gap.

    This bit the gh #1653 round-1 census, and its "harness proven" controls did
    NOT catch it because both controls passed their args as LITERALS and so never
    exercised the ref path at all. A positive control only proves the path it
    actually walks. The controls below therefore use ``@input.*`` refs.
    """
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        pytest.skip("no native library — this gate measures the C projection")
    try:
        cj = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
        xj = json.dumps({"inputs": ctx}, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError):
        return None, "PY_JSON_DUMPS_FAILED"
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, ws_bytes,
                                  out, out_cap, ctypes.byref(out_len)))
    return rc, _STATUS.get(rc, "rc=%d" % rc)


def _chain_only(entry):
    """The chain document the runner CONTRACT takes — header + steps, without
    the descriptor's test metadata.

    ⚠️ Passing the whole catalog entry into the runner couples a chain's
    executability to its own PROOF CASES, and rc447 measured that biting:
    ``magnitude`` declares non-finite cases (``nan`` / ``inf`` / ``-inf``), and
    ``json.dumps`` spells those as bare ``NaN`` / ``Infinity`` — which are NOT
    valid JSON. srmech's parser is strict RFC 8259 and rejects the document, so
    the whole chain returned BAD_INPUT and read as a grammar gap when every one
    of its STEPS ran correctly. ``proof_cases`` therefore stays stripped.

    ⚠️ ``summary`` / ``returns`` DO travel now — rc452 (gh #1653 finding (b)).
    This function used to strip them too, with the comment "the runner never
    reads them", and the raw ``[[cascade.chain]]`` entries carry no ``name``
    at all — so every chain this harness drove was HEADERLESS, and
    ``srmech_chain_run`` ACCEPTED it while Python's ``parse_chain_spec``
    raises ``ChainSpecError`` on the same dict. The disagreement was the
    finding; the CONTRACT (the runner's own header doc plus BOTH parse peers)
    backs Python, so the runner now refuses the headerless form and this
    harness synthesizes the header the way ``cascade_chain_specs`` does.

    (The non-finite limit itself is real and stays filed — see the gap ledger's
    ``non_finite_doubles_cannot_cross_json`` row. It bounds which INPUTS can
    reach C, not which chains exist.)
    """
    out = {k: v for k, v in entry.items()
           if k in ("name", "summary", "returns", "steps", "on_error",
                    "chain_schema_version")}
    out.setdefault("name", str(entry.get("variant", "chain")))
    out.setdefault("summary", "")
    out.setdefault("returns", "")
    return out


def _measure():
    """(rejected, accepted) chain-name sets, measured against the C run loop."""
    names, catalog = _executable_chains()
    rejected, accepted = set(), set()
    for name in names:
        entries = _cc._chain_entries(catalog[name])
        ok_any = False
        for entry in entries:
            cases = entry.get("proof_cases") or [{}]
            ctx = dict((cases[0] or {}).get("inputs") or {})
            rc, _ = _c_runs(_chain_only(entry), ctx)
            if rc == 0:
                ok_any = True
        (accepted if ok_any else rejected).add(name)
    return rejected, accepted


def test_harness_resolves_input_refs():
    """HARNESS CONTROL, and it walks the REF path deliberately.

    Round 1's controls used literal args and therefore proved nothing about
    ``@input.*`` resolution — the exact path a wrong ctx shape breaks. If this
    fails, every rejection below is suspect and none of them is evidence.
    """
    # Deliberately uses rational_add — an op the C table has carried since long
    # before gh #1653 — so this control isolates REF RESOLUTION from op
    # availability. A control built on an op this same rc adds would pass or fail
    # for the wrong reason and could not separate the two.
    rc, status = _c_runs(
        {"name": "ctl", "summary": "s", "returns": "r",
         "steps": [{"class": "N", "op": "rational_add",
                    "args": {"a": "@input.a", "b": "@input.b"}}]},
        {"a": [1, 2], "b": [1, 3]})
    assert rc == 0, (
        "the harness cannot resolve @input.* refs (rc=%s %s) — fix the ctx shape "
        "before trusting any rejection in this file" % (rc, status))


def test_a_headerless_chain_is_refused_in_both_projections():
    """rc452 (gh #1653) — finding (b), pinned in BOTH directions.

    Measured before the fix: ``srmech_chain_run`` ACCEPTED a chain object
    carrying neither ``name`` nor ``summary`` (this file's own ``_chain_only``
    fed it exactly those for four rcs) while ``parse_chain_spec`` REJECTS the
    same dict with ChainSpecError. Co-equal projections must agree on what
    they REFUSE, and the contract — the runner's own header doc plus both
    parse peers — backs the refusal. So: each required header key missing
    must be BAD_INPUT in C AND ChainSpecError in Python, and the full-header
    control must run in C, so the refusal cannot be a harness artifact.
    """
    base = {"name": "h", "summary": "s", "returns": "r",
            "steps": [{"class": "I", "op": "gcd",
                       "args": {"a": 12, "b": 18}}]}
    rc, status = _c_runs(dict(base), {})
    assert rc == 0, (
        "the FULL-HEADER control did not run (rc=%s %s) — the refusals below "
        "would then prove nothing" % (rc, status))
    for missing in ("name", "summary", "returns"):
        broken = {k: v for k, v in base.items() if k != missing}
        rc, status = _c_runs(broken, {})
        assert rc == 2, (
            "C accepted a chain missing %r (rc=%s %s); through rc452 Phase 3 "
            "it RAN such chains, which is the co-equal divergence this test "
            "pins closed" % (missing, rc, status))
        with pytest.raises(_compose.ChainSpecError):
            _compose.parse_chain_spec(broken)


def test_every_c_rejected_chain_is_enumerated():
    """THE INVARIANT: no silent row. An unlisted rejection fails.

    This is deliberately NOT a count. A count rots as the catalog grows; an
    invariant does not. ADR-0009 §5 forbids an unfiled decline, and gh #1653
    exists precisely because one went unfiled.
    """
    rejected, accepted = _measure()

    unenumerated = sorted(rejected - set(BLOCKED))
    assert not unenumerated, (
        "C cannot run these chains and they are NOT enumerated in BLOCKED: %s\n"
        "Add a row with its gate(s) %s and a disposition %s, or fix the chain. "
        "Zero rows may be silent." % (unenumerated, sorted(VALID_GATES),
                                      sorted(VALID_DISPOSITIONS)))

    stale = sorted(set(BLOCKED) & accepted)
    assert not stale, (
        "these chains now RUN in C but are still listed as BLOCKED: %s\n"
        "Delete their rows — a stale block-list hides a closed gap." % stale)

    for name, row in sorted(BLOCKED.items()):
        bad = sorted(set(row["gates"]) - VALID_GATES)
        assert not bad, "%s names unknown gate(s) %s" % (name, bad)
        assert row["gates"], "%s must name at least one gate" % name
        assert row["disposition"] in VALID_DISPOSITIONS, (
            "%s has disposition %r, not one of %s"
            % (name, row["disposition"], sorted(VALID_DISPOSITIONS)))


def test_c_rejected_chain_count_is_tight():
    """Down-only, pinned TIGHT — fixing a chain FORCES this literal down."""
    rejected, _ = _measure()
    assert len(rejected) == CEIL_C_REJECTED_CHAINS, (
        "C-rejected chain count is %d, ceiling is %d. If you FIXED chains, lower "
        "CEIL_C_REJECTED_CHAINS to %d and delete their BLOCKED rows. If this grew, "
        "a chain regressed."
        % (len(rejected), CEIL_C_REJECTED_CHAINS, len(rejected)))


def test_surface_a_unsupported_step_forms_is_tight():
    """Surface A has 3 step forms; C executes ``plain`` generally and ``fold``
    only for one body op. Down-only.

    The fold probe deliberately folds ``gcd`` — an op the shared dispatch table
    DOES have — so a decline here isolates the fold BODY table from op
    availability. If it used ``orientation_compose`` it would pass and this
    gate would stop measuring anything.
    """
    supported = set()
    for form, chain in (
        ("plain", {"name": "p", "summary": "s", "returns": "r", "steps": [
            {"class": "N", "op": "rational_add",
             "args": {"a": [1, 2], "b": [1, 3]}}]}),
        ("map", {"name": "m", "summary": "s", "returns": "r", "steps": [
            {"map_over": "@input.xs", "index": "i", "body": [
                {"class": "I", "op": "mod_add",
                 "args": {"a": "@idx.i", "b": 0, "n": 2}}]}]}),
        ("fold", {"name": "f", "summary": "s", "returns": "r", "steps": [
            {"fold_class": "I", "fold_op": "gcd", "fold_init": 0,
             "over": "@input.xs"}]}),
    ):
        rc, _ = _c_runs(chain, {"xs": [1, 2, 3]})
        if rc == 0:
            supported.add(form)
    unsupported = sorted(set(SURFACE_A_STEP_FORMS) - supported)
    assert len(unsupported) == CEIL_SURFACE_A_UNSUPPORTED_FORMS, (
        "surface-A step forms C cannot execute: %s (%d); ceiling %d. Lower the "
        "ceiling when you implement one."
        % (unsupported, len(unsupported), CEIL_SURFACE_A_UNSUPPORTED_FORMS))


def test_all_executable_chains_run_in_c():
    """THE TARGET, AND IT NOW ASSERTS. Co-equal projections means every declared
    chain runs in C.

    ⚠️ THE ``xfail(strict=True)`` MARKER IS GONE, DELETED AT rc452 (`#T1166`).
    It read "the C projection runs 0 of 18 executable cascade chains at rc445"
    and was strict precisely so that the moment the work landed it would XPASS,
    which FAILS, which forces the marker's removal. That is what happened when
    ``parallel_sector_dispatch`` closed and :data:`CEIL_C_REJECTED_CHAINS`
    reached 0. The gate removed itself when satisfied instead of quietly passing
    forever, which is the whole reason it was written that way — so this
    docstring records the transition rather than letting the file read as though
    the test had always asserted.

    From here the test is a plain invariant: a NEW descriptor that C cannot run
    fails on arrival. That is a stronger position than the ceiling ever was,
    because it has no seeded population to hide behind.
    """
    rejected, _ = _measure()
    assert not rejected, (
        "%d executable chains do not run in the C projection: %s"
        % (len(rejected), sorted(rejected)))


def test_every_blocked_row_carries_a_REAL_disposition_and_a_new_type_flag():
    """ADR-0009 §5: enumeration alone is not filing.

    ⚠️ THIS IS THE FAILURE gh #1653 WAS OPENED TO CLOSE, AND IT WAS LIVE IN HERE.
    Until rc447 ``VALID_DISPOSITIONS`` accepted ``"OPEN"`` and every row used it,
    so the ratchet listed each rejected chain (which is the visibility half) while
    letting every one of them say NOTHING about what was being done about it.
    "OPEN" is the unfiled decline, spelled legally. It is gone; the only
    admissible values are the three ADR-0009 names.

    ``new_type`` is required per row for the same reason: the standing rule is
    that a new type widens a discriminator set and closes its projection gap in
    the SAME change, and a row that cannot express whether it IS one cannot be
    checked against that rule. ALL NINE are, as of the rc450 sync — three rows
    (autocorrelation / klein4_from_one / kuramoto_step) read False while citing
    ``step_form_map``, whose own ledger row has said ``new_type: true`` all
    along. Closing a map chain requires the MAP step form, and the MAP step form
    is the new type; the rows said otherwise and nothing compared them.
    """
    for name, row in sorted(BLOCKED.items()):
        assert set(row) == {"gates", "disposition", "new_type", "ledger_row",
                            "new_type_reason"}, (
            "%s: a BLOCKED row must carry exactly gates / disposition / "
            "new_type / ledger_row / new_type_reason; got %s"
            % (name, sorted(row)))
        assert isinstance(row["new_type_reason"], str), name
        assert row["disposition"] in VALID_DISPOSITIONS, (
            "%s has disposition %r. ADR-0009 §5 admits only %s — a row with no "
            "real disposition is an UNFILED DECLINE, which is the defect this "
            "whole issue exists to remove."
            % (name, row["disposition"], sorted(VALID_DISPOSITIONS)))
        assert isinstance(row["new_type"], bool), (
            "%s: new_type must be an explicit bool, not %r — 'unknown' is not a "
            "state the same-change rule can be checked against"
            % (name, row["new_type"]))
        assert row["ledger_row"], "%s: no gap-ledger row named" % name


def test_every_blocked_row_is_ACTUALLY_FILED_in_the_gap_ledger():
    """The disposition must be TRUE, not merely well-formed.

    A row may say ``FILED_AS_NEW_ITEM`` and be filed nowhere — which would make
    the field above a formality rather than a fact. So resolve each
    ``ledger_row`` against notes/_1653_gap_ledger.ndjson and require it to
    exist. This is the same cross-artifact tie the gate matrix uses against this
    file's ceiling: a claim checked only within the artifact that makes it will
    agree with itself.
    """
    import json
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "..", "notes", "_1653_gap_ledger.ndjson")
    if not os.path.exists(path):
        pytest.skip("gap ledger ndjson not generated in this tree")
    ids = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("record") != "summary":
                ids.add(rec.get("id"))
    missing = sorted((n, r["ledger_row"]) for n, r in BLOCKED.items()
                     if r["ledger_row"] not in ids)
    assert not missing, (
        "these BLOCKED rows claim FILED_AS_NEW_ITEM against a gap-ledger row "
        "that does not exist: %s\nRegenerate the ledger "
        "(python3 notes/_1653_gap_ledger.py) or fix the reference — a "
        "disposition pointing at nothing is not a filing." % missing)


def test_ratchet_reports_the_full_state(capsys):
    """Visibility: print the per-chain state every run, so it is never invisible."""
    rejected, accepted = _measure()
    with capsys.disabled():
        print("\n  C-projection cascade parity @ srmech %s (ABI %s)"
              % (srmech.__version__, srmech.native_status()["abi_version"]))
        print("  accepted by srmech_chain_run : %d" % len(accepted))
        print("  rejected                     : %d" % len(rejected))
        for name in sorted(rejected):
            row = BLOCKED.get(name, {})
            print("    %-26s gates=%-46s %s"
                  % (name, ",".join(row.get("gates", ["UNENUMERATED"])),
                     row.get("disposition", "!!")))
    assert len(accepted) + len(rejected) == len(_executable_chains()[0])
