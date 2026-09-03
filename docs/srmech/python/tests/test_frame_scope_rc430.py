"""rc430 (`#T1127`) — a declared FRAME must be one a perturbation can CONTRADICT.

THE FALSE GREEN THIS EXISTS TO CATCH
------------------------------------
**A declared classification that nothing verifies.** rc339 shipped
``bounded_by = "associativity"`` on an op DEFINED as the associativity
condition — no carrier row could falsify it — and rc343 removed it. rc428
found ``row.schema.json`` declaring ``additionalProperties: false`` with
nothing validating against it, and three violating fields shipped green.

``ToolEntry.frame_scope`` is a claim of exactly that kind — "this op's frame is
welded in" — so it needs exactly that kind of rule. This module IS the rule,
and it is executable rather than documentary. It copies the shape of
``tests/test_op_lane_rc347.py`` section for section, because that field is the
one precedent in this tree that verifies its declaration instead of storing it.

WHAT IS PERTURBED
-----------------
The frame COORDINATE is translated and the output is watched::

    parametric   sweeping the named parameter MOVES the output; f(x + n) ==
                 f(x) for every swept n; and NO single constant period
                 survives the sweep.
    fixed        a least constant m > 1 with f(x + m) == f(x) across a dense
                 range, no parameter supplies m, and the op is not constant
                 along the coordinate.

SWEPT, NEVER SAMPLED — MEASURED, NOT ASSERTED
---------------------------------------------
The first draft of the instrument sampled six offsets and classified
``srmech.math.primes.is_prime`` as ``fixed`` with **period 6**. It is not
periodic; six draws agreed by chance. Had it shipped, this gate would have
been protecting a false declaration on a real op — the very defect the rc
exists to remove, reproduced by the tool built to remove it. §0 below
re-derives ``is_prime -> no period`` on every run, so that repair cannot
silently regress.

**Section 0 is not preamble.** Without it every verdict below is an artefact of
the instrument rather than a fact about the ops.

THE OPT-IN TRAP, AND WHY THIS FIELD DOES NOT FALL INTO IT
----------------------------------------------------------
``reads_lane`` reached **9 of 655 ops (1.4%) in 82 rcs**. A field nothing
computes the roster FOR is an ``__all__``-shaped escape hatch: the surfaces
that most need it are the least likely to opt in. So §4 does not ask which ops
declared. It DERIVES the admissible set behaviourally and asserts
``declared == admissible`` in BOTH directions. A declaration cannot escape by
staying silent.

No float, no numpy, no ``fractions``, no ``abs()`` — a sign is a Class-K
pin-slot read composed with Class C.

Instrument: ``tools/frame_probe.py``. Census + NDJSON:
``docs/srmech/notes/_frame_scope_census_rc430.py``.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG_ROOT / "tools"))

import example_args as ea      # noqa: E402
import frame_probe as fp       # noqa: E402

from srmech.cascade import cyclic_mod_add  # noqa: E402
from srmech.introspect import describe  # noqa: E402
from srmech.introspect.tool_schema import (  # noqa: E402
    FRAME_AXES,
    FRAME_SCOPES,
    ToolEntry,
    ToolSchemaValidationError,
    get_tool_schema,
    warmup_all,
)
from srmech.math.cyclic import mod_mul  # noqa: E402
from srmech.math.primes import is_prime  # noqa: E402

#: The REVIEWED roster. §4 derives the admissible set and compares against the
#: live declarations, which is the real gate; this pins the set a human
#: actually looked at, for the reason rc412 exists — a strict-zero check over a
#: SHRINKING set is vacuously true, so a sweep alone cannot see a declaration
#: disappear. Measured at rc430 over the harvested argument corpus.
REVIEWED_ROSTER: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "srmech.biology.genome.modulator_constraint_satisfies": ("fixed", ("modulus",)),
    "srmech.cascade.cyclic_gcd": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_add": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_mul": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_mul_wide": ("parametric", ("modulus",)),
    "srmech.cascade.cyclic_mod_pow": ("parametric", ("modulus",)),
    "srmech.cascade.odft_summand": ("parametric", ("modulus",)),
    "srmech.cascade.qdft_summand": ("parametric", ("modulus",)),
    "srmech.math.covering.center_parity": ("fixed", ("modulus",)),
    "srmech.math.covering.lift_fibre": ("parametric", ("modulus",)),
    # Added at the rc430 REPAIR, not at rc430: the probe's degeneracy screen
    # was foreclosing the parametric sweep whenever the base arguments made the
    # op constant along the swept coordinate, so `gcd` measured NOT_ADMISSIBLE
    # and the both-directions gate passed against a census short by one. Its
    # own delegating alias `srmech.cascade.cyclic_gcd` (below) had declared
    # parametric/modulus since rc430 — the primitive and the alias disagreed.
    "srmech.math.cyclic.gcd": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_add": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_mul": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_mul_arrow": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_mul_wide": ("parametric", ("modulus",)),
    "srmech.math.cyclic.mod_pow": ("parametric", ("modulus",)),
    "srmech.math.cyclic.three_cycle": ("fixed", ("modulus",)),
    "srmech.math.rational.rational_reconstruct": ("parametric", ("modulus",)),
    "srmech.music.interval_vector": ("fixed", ("modulus",)),
    "srmech.music.normal_order": ("fixed", ("modulus",)),
    "srmech.music.prime_form": ("fixed", ("modulus",)),
}

#: Ops the driver cannot reach, by class, held DOWN-ONLY. An undrivable op is
#: not a pass — it is an unadjudicated one, and a ceiling is what stops the
#: unadjudicated class from quietly becoming the whole registry.
CEIL_FRAME_UNADJUDICATED = {
    # rc436 (local task T1141): 274 -> 275 for
    # `srmech.cascade.octonion_associator_support`. The gate's own advice is
    # "drain NO_ARG by making the op's worked example bind its arguments",
    # and that is NOT AVAILABLE HERE, which is why this is a raise and not a
    # drain. MEASURED: the op takes ZERO parameters, so its harvested binding
    # is `args: {}` (tests/example_args_ledger.ndjson, status
    # no_jsonable_arg), and frame_probe.classify assigns NO_ARG on exactly
    # `if not base`. There is no argument to bind, so no worked example can
    # bind one.
    #
    # This is also the CORRECT verdict rather than a probe gap. The frame
    # axis asks whether an op translates along a frame when an INTEGER INPUT
    # is varied; an op with no inputs has nothing to vary, so it is genuinely
    # not frame-adjudicable. It joins an established class: 54 registered ops
    # are parameterless and all land here structurally.
    #
    # rc442 (local task T1150): 275 -> 276 for `srmech.biology.genome.genome_groups`,
    # and for the same structural reason in its other form. The op takes exactly ONE
    # parameter, `strand`, whose type is a sequence of HV carriers — MEASURED as
    # `status: no_jsonable_arg, unserializable: ["strand"]` in
    # tests/example_args_ledger.ndjson, from a worked example that DOES call it five
    # times with a real strand. So the binding is not missing because the example is
    # thin; it is missing because an HV sequence has no JSON encoding for the harvester
    # to record, which is the same wall the existing population sits behind.
    #
    # And, as above, NO_ARG is the CORRECT verdict rather than a probe gap. The frame
    # axis asks whether an op translates along a frame when an INTEGER INPUT is varied.
    # `genome_groups` has no integer input at all: it reads block[0] of each block and
    # returns container structure, so there is nothing to translate. Its sibling
    # `genome_group` DID drain — it binds `label` and `dim` — which is what shows this
    # raise is about the parameter's type and not about the pair being under-exampled.
    # rc452 (gh #1653, the registry-ripple phase): 276 -> 277 for
    # `srmech.amsc.format.sha256_raw`, and it is the rc442 raise VERBATIM --
    # third instance of one established structural class, not a new excuse.
    # The gate's own advice is "bind the op's arguments", and that is NOT
    # AVAILABLE HERE: the op takes exactly ONE parameter, `data`, whose type
    # is `bytes`, and its worked example DOES call it four times with a real
    # value (b"hello"). MEASURED as `status: no_jsonable_arg, unserializable:
    # ["data"]` in tests/example_args_ledger.ndjson -- so the binding is
    # missing because `bytes` has no JSON encoding for the harvester to
    # record, exactly the wall `genome_groups` sits behind, not because the
    # example is thin. `fp.classify` then assigns NO_ARG on `if not base`.
    #
    # And, as in both prior raises, NO_ARG is the CORRECT verdict rather than
    # a probe gap. The frame axis asks whether an op translates along a frame
    # when an INTEGER INPUT is varied; `sha256_raw` has no integer input at
    # all -- it consumes opaque bytes and returns a digest, and a content
    # address has no frame to move along BY DESIGN (that is what makes it an
    # address). Its two sibling registrations in the same change did NOT need
    # this raise, which is what shows the raise is about this parameter's
    # type and not about the triple being under-exampled.
    # rc461 (`#T1181`): 277 -> 278 for
    # `srmech.physics.qm.triality.triality_frame_action`, and it is the rc442 /
    # rc452 raise VERBATIM — the FOURTH instance of one established structural
    # class, not a fourth excuse. The gate's own advice is "bind the op's
    # arguments", and that is NOT AVAILABLE HERE: the op takes exactly ONE
    # parameter, `automorphism`, whose type is `Mat`, and its worked example
    # DOES call it four times with real matrices from `triality_automorphism()`
    # and `triality_swap()`. MEASURED as `status: no_jsonable_arg,
    # unserializable: ["automorphism"]` in tests/example_args_ledger.ndjson —
    # so the binding is missing because a 28×28 `Mat` has no JSON encoding the
    # harvester can record, exactly the wall `genome_groups` (HV sequence) and
    # `sha256_raw` (bytes) sit behind, and not because the example is thin.
    # `fp.classify` then assigns NO_ARG on `if not base`.
    #
    # And, as in all three prior raises, NO_ARG is the CORRECT verdict rather
    # than a probe gap. The frame axis asks whether an op translates along a
    # frame when an INTEGER INPUT is varied; `triality_frame_action` has no
    # integer input at all — it consumes a 28×28 exact-ℚ operator and returns a
    # PERMUTATION OF THREE LABELS, a discrete classification with no coordinate
    # to translate. Its sibling registration in the same rc did NOT need this
    # raise: `cyclic_laplacian_spectrum` binds `n` and `deep` and the harvester
    # records them (`status: ok`, 18 recorded calls), which is what shows the
    # raise is about this parameter's TYPE and not about the pair being
    # under-exampled.
    # rc461 part 2 (`#T1181`): 278 -> 280, and the split across the two
    # unadjudicated classes is the point rather than the total. THREE ops were
    # registered; only TWO land here, and the third DRAINED. MEASURED per op
    # over the refreshed ledger:
    #   epq_frame_address        -> NO_ARG. It takes NO ARGUMENTS AT ALL, so
    #     there is nothing for the harvester to bind and nothing for the frame
    #     axis to translate. Undrainable by construction, not under-exampled.
    #   so8_bracket_certificate  -> NO_ARG. Its worked example DOES call it
    #     three times with real values, but the operand is a 28x28 `Mat`, which
    #     the ledger records as `unserializable: ["operator"]` — the
    #     `genome_group` / `render_template` structural class: bound, but not
    #     JSON-able, so no binding reaches the probe.
    #   g2_membership            -> NO_INT_INPUT (see the note below). It DID
    #     drain out of NO_ARG: its example binds a plain 8x8 int matrix, the
    #     harvester records `status: ok`, and the probe reaches it.
    # That one of the three drained while two did not is what shows the raise
    # is about the operand's TYPE, not about the family being under-exampled.
    # rc464 (`#T1188`) DRAIN, 280 -> 279, and it is a REMOVAL rather than a
    # discharge — the same distinction this rc recorded when it lowered
    # CEIL_REGISTRY_GAPS 157 -> 145 and CEIL_OPEN_REGISTRATION 97 -> 85. The op
    # that left is `srmech.cascade.sedenion_register`, whose rc463 ledger row was
    # `{"status": "no_worked_snippet", "n_calls": 0}` -- classified NO_ARG by
    # frame_probe's `if not base`. Removing the 16-slot register removed it; the
    # census population moved 720 -> 733 (+14 cdr_* registrations, -1 this
    # factory) and NONE of the fourteen landed in NO_ARG, so the measured count
    # fell to 279 while the ceiling stayed at 280.
    # ⚠️ CAUGHT LATE, and worth naming: this rc raised NO_INT_INPUT and drained
    # BASE_RAISES in the same edit, and left the one bucket that moved for
    # neither reason untouched. A ceiling carrying a slot the tree can no longer
    # justify is a free pass for the next rc, which is the shape this file
    # exists to refuse.
    "NO_ARG": 279,          # no harvested argument binding at all
    # rc442 (local task T1150): 152 -> 153, `genome_group`. It DID drain out of NO_ARG
    # (it binds `label` and `dim`), and landed one tier along in the same structural
    # class: neither bound argument is an INTEGER the frame axis could translate —
    # `label` is a string and `dim` is a block WIDTH, not a coordinate. A group is a
    # container mark; there is no frame for it to move along.
    # rc452 (gh #1653, the registry-ripple phase): 153 -> 154,
    # `srmech.amsc.descriptor.render_template`. It DID drain out of NO_ARG --
    # its worked example binds both parameters and the harvester records them
    # (`status: ok`, four recorded calls) -- and it landed one tier along in
    # the same structural class as `genome_group`: neither bound argument is
    # an INTEGER the frame axis could translate. `template` is a string and
    # `context` is a Mapping; the integers INSIDE that mapping are payload
    # being serialised, not a coordinate the op reads, so varying one moves
    # the rendered TEXT without there being any frame it moves along. A
    # renderer is a serialisation step; there is no frame for it.
    # rc456: 154 -> 160, six of the ten representation-stratum registrations,
    # and it is the `render_template` structural class SIX TIMES OVER, not a
    # new excuse. MEASURED per op (fp.probe_from_ledger over the refreshed
    # ledger): semidirect_product / conjugacy_classes / derived_subgroup /
    # abelianization / character_table / irrep_dimensions -> NO_INT_INPUT.
    # Each binds its arguments (the harvester records real calls), but the
    # bound operand is a CAYLEY TABLE — list[list[int]] — whose integers are
    # element INDICES, i.e. payload naming positions in a finite group, not a
    # coordinate the op reads along any modulus/frame axis; varying one
    # corrupts the group rather than translating anything. The OTHER four ops
    # of the same rc did NOT need this raise (cyclic_group / quotient_group /
    # cayley_graph / cyclotomic_polynomial measured NOT_ADMISSIBLE — the
    # probe could drive their int/list inputs and measured no frame
    # translation), which is what shows the raise is about the operand's
    # type, not about the family being under-exampled.
    # rc457: 160 -> 163, the three tier-3 registrations, and it is the rc456
    # structural class a SEVENTH, EIGHTH and NINTH time. MEASURED per op
    # (fp.probe_from_ledger over the refreshed ledger):
    # frobenius_schur_indicator / fusion_multiplicities / central_idempotents
    # -> NO_INT_INPUT. Each binds its one argument (the harvester records the
    # worked example's real calls), but the bound operand is the whole
    # character_table PAYLOAD DICT, whose integers are class indices, character
    # coordinates and content-address echoes — payload naming structure inside
    # one measurement, not a coordinate the op reads along any modulus/frame
    # axis; varying one corrupts the payload (the ops' own divisibility guards
    # raise on exactly that) rather than translating anything.
    # rc458: 163 -> 170, seven of the eight tier-4 registrations, split
    # exactly along the two established structural classes. MEASURED per op
    # (fp.probe_from_ledger over the refreshed ledger):
    # permutation_representation -> NO_INT_INPUT (its bound operands are a
    # CAYLEY TABLE and an ACTION table — element indices and point images,
    # the rc456 semidirect_product class); character_of /
    # decompose_representation / isotypic_projector /
    # tensor_product_representation / direct_sum_representation /
    # intertwiner_space -> NO_INT_INPUT (the bound operands are whole REP /
    # character_table PAYLOAD DICTS, the rc457 class — their integers are
    # matrix entries, class indices and content-address echoes, payload
    # naming structure, not a coordinate on any frame axis). The EIGHTH op,
    # zeta_mul, needed NO raise: the probe drove its int-vector operands (73
    # calls) and measured NOT_ADMISSIBLE — no frame translation, exactly the
    # rc456 cyclic_group/quotient_group outcome — which is what shows the
    # seven raises are about operand TYPE, not about the family being
    # under-exampled.
    # rc461 part 2 (`#T1181`): 170 -> 171, exactly one op, and it is the
    # rc456/rc457 structural class again. `g2_membership` DID drain out of
    # NO_ARG — its worked example binds a plain 8x8 int matrix and the
    # harvester records `status: ok` — and it lands here because the bound
    # operand's integers are the matrix ENTRIES OF A GROUP ELEMENT, not a
    # coordinate the op reads along any modulus/frame axis. Varying one breaks
    # orthogonality and the op's own `g^T g == I` guard raises on exactly that,
    # rather than translating anything.
    # ⚠️ The first measurement of this raise said 172, and the extra +1 was NOT
    # an op of this rc: it came from re-harvesting the example-args ledger in
    # FULL, which flipped `srmech.math.rational.rational_div` out of
    # NOT_ADMISSIBLE. Re-harvesting with `--only-stale` leaves every unchanged
    # row byte-identical and the count is 171. See the longer note at
    # CEIL_UNSYNTHESIZABLE_PARAMS in tests/test_synth_args_provenance_rc430.py.
    # rc462 (`#T1179`, the ripple stage): 171 -> 172, and the raise comes with
    # the drain that makes it a net GAIN rather than a loss. MEASURED by
    # censusing the same tree twice, once against the committed ledger and once
    # against the full re-harvest, so every move below is attributed:
    #
    #     induced_representation   NO_ARG         -> NOT_ADMISSIBLE
    #     zeta_conjugate           NO_ARG         -> NOT_ADMISSIBLE
    #     triality_companions      NO_ARG         -> NO_INT_INPUT
    #     rational_div             NOT_ADMISSIBLE -> NO_ARG
    #
    # NO_ARG 282 -> 280, NO_INT_INPUT 171 -> 172. THE GATE WAS ALREADY RED AT
    # THIS RC'S HEAD and this stage is what turned it green: rc462 registered
    # two ops without an example-args row for either, so both landed in NO_ARG
    # and pushed it to 282 against its ceiling of 280. Regenerating the ledger
    # is what bound them, and a bound op gets a real verdict.
    #
    # The +1 here is `srmech.physics.qm.triality.triality_companions`, and it
    # is `genome_group` / `render_template` VERBATIM — an op that DRAINED OUT
    # of NO_ARG and landed one tier along in the same structural class, not a
    # new excuse. It is strictly MORE information than the row it replaces:
    # NO_ARG says the probe could not reach the op at all, NO_INT_INPUT says
    # the probe reached it and MEASURED that it has no integer input to
    # translate. Structurally correct too — the op returns the so(8) companion
    # maps for a fixed frame and takes no coordinate at all.
    #
    # `rational_div`'s move is the one genuine loss, and it is a FOSSIL being
    # corrected rather than a regression: its committed row recorded `(19, 20)`
    # / `(9991, 10000)` TUPLES, and the op's snippet has not passed tuples
    # since the Class-N precision migration made `rational_add` return `Q`.
    # rc461 met the same flip and chose `--only-stale` to preserve the row.
    # ⚠️ THAT ADVICE IS WITHDRAWN HERE, WITH THE MEASUREMENT THAT WITHDRAWS IT:
    # `--only-stale` keys on the snippet-text hash, so it also preserved six
    # tier-3/4 rows whose args predated rc460's `cayley_sha256` bind and now
    # make their ops RAISE — and an op that raises emits nothing, so SIXTEEN
    # shipped content addresses stayed invisible to
    # tests/test_content_address_class_rc462.py for a whole release. Keeping a
    # ceiling at 171 by declining to re-measure is the instrument-blind class,
    # not a saving.
    # rc463 (`#T1188`, the fix pass): 172 -> 182, TEN of this rc's eighteen
    # registrations, and it is the `render_template` / rc456 structural class
    # ten times over rather than a new excuse. ⚠️ The raise is stated with the
    # measurement that FORCES it, and with the drain that was taken instead
    # wherever one existed — the NO_ARG ceiling next door was NOT raised in this
    # same rc: `lstsq_exact` was over it at 281, and the cause was the ORDER of
    # its worked snippet (`harvest_op` keeps the FIRST returning call, and the
    # snippet led with a `Fraction` witness JSON cannot carry), so moving its
    # all-integer call to the front drained 281 -> 280 with the ceiling
    # untouched. That is the difference: NO_ARG had a drain and took it; this
    # class has none.
    #
    # MEASURED per op (`fp.probe_from_ledger` over the refreshed ledger, with
    # the harvested binding printed): eigvec_exact / eigvec_exact_float /
    # jordan_chains_exact (`a` binds a nested int matrix, `lam` is a `Qalg`),
    # separate_frame_curvature (`a`, `b` both nested int matrices),
    # gram_schmidt_exact (`basis`, a list of int row-vectors), and qmat_rank /
    # _det / _inverse / _rref / _nullspace (`rows` nested, `method` a string).
    # `fp.is_frame_coordinate` admits a scalar `int` or a FLAT int sequence;
    # every one of these ten reports ZERO frame-coordinate keys, so
    # `Driver.coordinates()` is empty and `classify` assigns NO_INT_INPUT on
    # exactly `if not coords`.
    #
    # And, as in every prior raise of this class, NO_INT_INPUT is the CORRECT
    # verdict rather than a probe gap. The frame axis asks whether an op
    # TRANSLATES along a frame when an integer input is varied — a modular
    # coordinate shift. A matrix is an OPERATOR, not a coordinate: perturbing
    # one of its entries changes which operator you asked about, so a probe
    # that translated nested sequences would be measuring a different question
    # and reporting the answer under this name. Draining these ten therefore
    # requires weakening the instrument, which is the one move this file exists
    # to refuse. The other eight of the eighteen ARE driven to a real verdict
    # (five NOT_ADMISSIBLE, one drained to NOT_ADMISSIBLE from NO_ARG), which is
    # what shows the ten are a property of their operands and not of the rc.
    # rc464 (`#T1188`): 182 -> 184, and the SPLIT across the fourteen new ops is
    # the whole justification. Fourteen cdr_* [class]-binding adapters were
    # registered; TWELVE are driven to a real verdict (all NOT_ADMISSIBLE) and
    # exactly TWO land here — so this is a property of two operands, not of the
    # rc, and it is stated with the arithmetic that shows it.
    #
    # MEASURED per op, and by the strongest available predicate — not "the
    # probe could not reach it" but "the op HAS NO INTEGER PARAMETER AT ALL",
    # which is readable off the signature without running anything:
    #   cdr_slots(slots)           — one parameter, a {slot: (key, sign)} map.
    #   cdr_clean(noisy, codebook) — two parameters, a bytes vector and a
    #                                {name: bytes} codebook.
    # The integers INSIDE those maps are slot INDICES and Class-C signs, i.e.
    # payload naming positions and orientations in a stored assignment, not a
    # coordinate the op reads along any modulus or frame. Varying one does not
    # translate the answer; it names a different slot or flips a stored sign.
    # This is exactly the `render_template` structural class the rc456 / rc457 /
    # rc461 raises recorded — the operand is a container whose ints are content.
    #
    # WHY THIS IS A RAISE AND NOT A DRAIN, stated because the gate's own advice
    # is to drain first and that advice WAS followed here for four sibling ops.
    # rc464's first harvest put cdr_element / cdr_materialize / cdr_navigate /
    # cdr_read_unbind in BASE_RAISES (56 -> 60), because each op's leading
    # worked call passed a minted bytes codebook that JSON cannot carry, so the
    # probe rebuilt a call with the argument missing. Those four WERE drained,
    # by reordering each row so its first RETURNING call is JSON-carryable —
    # including cdr_materialize, whose non-empty register is spelled in the
    # STR-keyed / LIST-paired WIRE form for exactly this reason. BASE_RAISES is
    # back at 56 and all four measure NOT_ADMISSIBLE. The same move is not
    # available to these two: no ordering of any example can give an op an
    # integer parameter it does not have.
    "NO_INT_INPUT": 184,    # nothing translatable along a frame axis
    "BASE_RAISES": 56,      # harvested binding does not execute
    # rc461 part 3 (`#T1183`): 15 -> 17, and the split across the five new ops
    # is the point rather than the total. FIVE ops were registered; only TWO
    # land here and the other three are DRIVEN to a real verdict. MEASURED
    # with the real Driver at SCREEN=24, per op:
    #   affine_modular_s_matrix        -> >90 s at call SIX, still climbing.
    #   verlinde_fusion_multiplicities -> >90 s at call TEN, still climbing.
    #   integrable_weights             -> 0.25 s. NOT skipped.
    #   alcove_fold                    -> 0.00 s. NOT skipped.
    #   affine_fusion_multiplicities   -> 0.02 s. NOT skipped.
    # The cause is the `level` sweep against a D4 base: |P_k| is 4 at level 1
    # and 658711 at level 72, and the Kac-Peterson sum is |P_k|^2 x |W| terms.
    # That three of the five screen in milliseconds is what shows the two
    # entries are about the Weyl-sum cost, not about the family being
    # unprobeable. ⚠️ One of the three only became cheap IN THIS DIFF:
    # `integrable_weights` used to filter a (level+1)^rank BOX, which at D4
    # level 72 is 73^4 = 28.4M tuples for a 658711-row answer. It now walks the
    # simplex directly. The probe is what surfaced that, so a would-be third
    # skip was drained by fixing the op rather than by naming it here.
    "SLOW_SKIP": 17,        # measured-slow, skipped BY NAME with a number
    # rc430 repair (`#T1127`): ops whose parameter carries a documented domain
    # contract the sweep cannot honour (the three GF(p) ops need PRIME p). The
    # native peer asserts it and CI took SIGABRT; the pure body silently
    # computes a wrong answer instead, which is why no local run saw it.
    # Drains when the rc431 per-parameter domain field lands and the probe can
    # READ the contract instead of being told it by name.
    "CONTRACT_SKIP": 3,
}

_CENSUS_CACHE: Dict[str, Any] = {}


def _census() -> Dict[str, Dict[str, Any]]:
    """Classify every registered op once, from the harvested ledger."""
    if not _CENSUS_CACHE:
        warmup_all()
        rows = ea.load_ledger()
        for entry in get_tool_schema().tools:
            _CENSUS_CACHE[entry.name] = fp.probe_from_ledger(entry.name, rows)
    return _CENSUS_CACHE


def _declared() -> Dict[str, ToolEntry]:
    warmup_all()
    return {e.name: e for e in get_tool_schema().tools if e.frame_scope is not None}


# ══════════════════════════════════════════════════════════════════════
# 0. INSTRUMENT PRECONDITION — without this, nothing below is evidence
# ══════════════════════════════════════════════════════════════════════

def _leak_a(x: int, y: int) -> int:
    """Modulus 12 WELDED IN. Must classify `fixed`, period 12."""
    return cyclic_mod_add(x, y, 12)


def _leak_b(x: int, y: int, n: int) -> int:
    """Modulus parametric, GENERATOR 7 welded in — the rc426 F12b blind spot.

    F12b files this CLEAN: it takes a modulus, is total, yields many distinct
    answers as ``n`` moves, and contains no literal 12. The generator clause is
    the whole reason this control exists.
    """
    return mod_mul(7, cyclic_mod_add(x, y, n), n)


def _clean(x: int, y: int, n: int, g: int) -> int:
    """Nothing welded in — both the modulus and the generator are inputs."""
    return mod_mul(g, cyclic_mod_add(x, y, n), n)


def test_the_period_finder_rejects_a_coincidence() -> None:
    """``is_prime`` is not periodic, and a six-point sample said it was.

    This is the known-answer probe. It is asserted on every run because the
    repair it protects — dense sweep plus a confirmation floor — is the single
    thing standing between this gate and blessing a false declaration.
    """
    vals = [fp.okey(is_prime(101 + d)) for d in range(fp.R)]
    m, _ = fp.least_period(vals)
    assert m is None, (
        f"is_prime(101+d) reports least period {m}. It is not periodic; a "
        f"short sample said 6 at rc430. The dense sweep or the "
        f"MIN_CONFIRMATIONS floor has regressed, and every `fixed` verdict "
        f"below is now suspect.")

    # and the sweep must still be able to FIND a period, or it is rejecting
    # everything and the check above passes for the wrong reason.
    good = [fp.okey(cyclic_mod_add(x, 3, 12)) for x in range(fp.R)]
    m2, conf = fp.least_period(good)
    assert (m2, conf > 24) == (12, True), (m2, conf)


def test_a_constant_function_does_not_classify_fixed() -> None:
    """PF8. A constant map has EVERY period, so a period-finder alone would
    call it maximally frame-fixed. The non-degeneracy guard is the answer."""
    rec = fp.classify("CONST", {"x": 0}, lambda x: 7)
    assert rec["verdict"] == "NOT_ADMISSIBLE", rec
    assert not rec["findings"]


def test_the_instrument_separates_the_two_leaks_and_the_clean_control() -> None:
    """PF6. LEAK_A `fixed`(12); LEAK_B `parametric` AND generator 7; CLEAN
    neither. If LEAK_B reads clean, the instrument has reproduced the very
    blind spot it was built to narrow and MUST NOT SHIP."""
    a = fp.classify("LEAK_A", {"x": 0, "y": 3}, _leak_a)
    b = fp.classify("LEAK_B", {"x": 0, "y": 3, "n": 11}, _leak_b)
    c = fp.classify("CLEAN", {"x": 0, "y": 3, "n": 11, "g": 3}, _clean)

    assert fp.declared_scope(a["findings"]) == "fixed", a
    assert {f["period"] for f in a["findings"]} == {12}, a

    assert fp.declared_scope(b["findings"]) == "parametric", b
    gens = {f.get("generator") for f in b["findings"]}
    assert gens == {7}, (
        f"LEAK_B welds in the generator 7 and the instrument reports {gens}. "
        f"rc426's F12b calls this op CLEAN; an instrument that agrees with "
        f"F12b here has no reason to exist.")
    assert "generator" in fp.declared_axis(b["findings"]), b

    assert fp.declared_scope(c["findings"]) == "parametric", c
    assert all("generator" not in (f.get("axis") or []) for f in c["findings"]), (
        f"CLEAN welds in nothing, so declaring a generator for it would mean "
        f"the clause fires on everything: {c}")


def test_the_instrument_moves_one_axis_at_a_time() -> None:
    """Translating the frame coordinate must not move the modulus, and
    sweeping the modulus must not move the coordinate. A perturbation that
    moves both cannot attribute what it sees."""
    base = {"x": 5, "y": 3, "n": 11}
    drv = fp.Driver("LEAK_B", base, _leak_b)
    assert drv.base == base, "the driver mutated its own base binding"
    assert fp.translate(5, 7) == 12 and fp.translate([1, 2, 3], 7) == [8, 2, 3]
    # sequence() must not leak state between overrides
    s1 = drv.sequence("x", {"n": 5}, length=12)
    s2 = drv.sequence("x", {"n": 7}, length=12)
    assert s1 != s2, "two different moduli produced identical sequences"
    assert drv.base == base


# ══════════════════════════════════════════════════════════════════════
# 1. VOCABULARY CLOSURE — the field is closed only if something closes it
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("kw", [
    {"frame_scope": "free", "frame_axis": ("modulus",)},        # unknown scope
    {"frame_scope": "fixed", "frame_axis": ("chart",)},         # unknown axis
    {"frame_scope": "fixed", "frame_axis": ()},                 # half: no axis
    {"frame_scope": None, "frame_axis": ("modulus",)},          # half: no scope
])
def test_a_malformed_frame_declaration_is_rejected_at_registration(kw) -> None:
    with pytest.raises(ToolSchemaValidationError):
        ToolEntry(name="x", owner="srmech", category="c", summary="s", **kw)


def test_there_is_deliberately_no_free_scope() -> None:
    """An op with no frame datum cannot be contradicted on one, so it declares
    NOTHING. ``"free"`` would be a value no measurement could refute — which is
    the rc339 defect this whole family of fields is a reaction to."""
    assert "free" not in FRAME_SCOPES
    assert set(FRAME_SCOPES) == {"parametric", "fixed"}
    assert set(FRAME_AXES) == {"modulus", "generator"}


# ══════════════════════════════════════════════════════════════════════
# 2. THE RATCHET — declared matches measured
# ══════════════════════════════════════════════════════════════════════

def assert_declaration_matches(entry: ToolEntry, rec: Dict[str, Any]) -> None:
    """THE COMPARISON, as ONE callable — the whole ratchet and nothing else.

    §2 below is this function applied to the live registry. §6's falsifiers are
    this same function applied to a DELIBERATELY MIS-DECLARED copy of an entry,
    required to raise.

    That sharing is the point, and it is a repair (`#T1127`). At rc430 the two
    §6 falsifiers RE-SPELLED the comparison inline instead of calling it, which
    made both of them dominated by §2: each concluded `measured != lie` from
    premises §2 had already established (`measured == entry.frame_scope` and
    `entry.frame_scope != lie`), so neither could fail in any state where §2
    passed. They could only go red AFTER the suite was already red — which is
    not a falsifier, it is an echo. Weakening the body below now breaks §6
    directly, because §6 has no copy of it to keep passing.
    """
    measured = fp.declared_scope(rec["findings"])
    assert measured == entry.frame_scope, (
        f"{entry.name} declares frame_scope={entry.frame_scope!r} but measures "
        f"{measured!r}. findings={json.dumps(rec['findings'])}. MIS-DECLARED.")
    measured_axis = fp.declared_axis(rec["findings"])
    assert tuple(entry.frame_axis) == measured_axis, (
        f"{entry.name} declares frame_axis={tuple(entry.frame_axis)} but "
        f"measures {measured_axis}. MIS-DECLARED.")


@pytest.mark.parametrize("op_name", sorted(REVIEWED_ROSTER))
def test_declared_frame_matches_measured_response(op_name: str) -> None:
    """THE RATCHET. Drive the op over a dense translation sweep and assert the
    response matches what its ToolEntry declares."""
    entry = get_tool_schema().lookup(op_name)
    assert entry is not None, f"{op_name} is not registered"
    assert entry.frame_scope is not None, (
        f"{op_name} is in the rc430 reviewed roster but declares no frame — "
        f"either declare it or drop it from the roster; a driver with nothing "
        f"to check is the dead-seam failure mode.")

    rec = _census()[op_name]
    assert rec["verdict"] == "ADMISSIBLE", (
        f"{op_name} declares frame_scope={entry.frame_scope!r} but the "
        f"instrument cannot reach it: verdict={rec['verdict']}. A declaration "
        f"nothing can drive is exactly the false green this file removes.")

    assert_declaration_matches(entry, rec)


# ══════════════════════════════════════════════════════════════════════
# 3. THE GENERATOR CLAUSE — narrowed, and honest about it
# ══════════════════════════════════════════════════════════════════════

def test_the_generator_clause_is_narrow_and_says_so() -> None:
    """It decides AFFINE ops only, and the payload must admit that.

    A non-affine op that hard-wires a generator stays undeclarable. Claiming
    rc427's G3b is CLOSED would be false, so the blind spot ships as data in
    ``describe()["frames"]["cannot_express"]`` and is asserted here.
    """
    # affine: the difference IS the generator, read mod the frame
    assert fp.first_difference([9, 4, 11, 6, 1, 8], mod=12) == 7
    # over the integers the same sequence is NOT constant — the bug that made
    # LEAK_B read clean in the first draft
    assert fp.first_difference([9, 4, 11, 6, 1, 8]) is None
    # non-affine: undeclarable, and reported as such rather than guessed
    assert fp.first_difference([1, 2, 4, 8, 16], mod=64) is None
    # a generator of 1 is "no generator"; 0 is degeneracy, not an affine step
    f: Dict[str, Any] = {}
    fp._add_generator(f, {}, [0, 1, 2, 3, 4], 12)
    assert "generator" not in f
    f = {}
    fp._add_generator(f, {}, [5, 5, 5, 5], 12)
    assert "generator" not in f
    # and a generator the CALLER supplies is not welded in — tested up to
    # congruence, because mod_mul(a=19, n=12) advances by 7.
    f = {}
    fp._add_generator(f, {"a": 19, "n": 12}, [9, 4, 11, 6, 1, 8], 12)
    assert "generator" not in f, (
        "a caller-supplied generator was declared welded-in; that is the "
        "false-`fixed` error one axis over")

    cannot = describe()["frames"]["cannot_express"]
    assert "non_affine_generator" in cannot
    assert "frame_free_vs_no_frame" in cannot
    # rc430 repair (`#T1127`) — the THIRD blind spot, added because it was
    # MEASURED rather than reasoned: the roster is derived from one argument
    # set per op, and srmech.math.cyclic.gcd was missing from it for exactly
    # that reason. A payload that names two of three blind spots reads as a
    # complete list of them.
    assert "base_argument_dependence" in cannot


def test_the_generator_axis_population_is_EMPTY_not_absent() -> None:
    """NULL CLASSIFICATION — ``EMPTY``, and that is a result.

    Zero shipped ops declare the generator axis: every generator the census
    found is supplied by a parameter. The axis stays in the vocabulary because
    LEAK_B exercises it in-test and because absence of instances is not
    absence of the phenomenon — the same reason rc426's tier table keeps
    ``SECONDARY-OA`` with 0 instances.
    """
    declared = _declared()
    with_gen = sorted(n for n, e in declared.items() if "generator" in e.frame_axis)
    print(f"\n[rc430] generator-axis declarers: {len(with_gen)} — EMPTY, not "
          f"absent. The axis is exercised by the LEAK_B control in §0.")
    assert with_gen == [], (
        f"ops now declare the generator axis: {with_gen}. That is a GOOD "
        f"outcome — update this test and the CHANGELOG to record the first "
        f"instances rather than deleting the assertion.")
    assert "generator" in FRAME_AXES


# ══════════════════════════════════════════════════════════════════════
# 4. NO DECLARATION ESCAPES — both directions
# ══════════════════════════════════════════════════════════════════════

def test_declared_equals_admissible_in_both_directions() -> None:
    """The anti-opt-in mechanism, and the reason this field will not stall at
    1.4% the way ``reads_lane`` did.

    The admissible set is COMPUTED from behaviour over every op the provider
    can drive. An admissible op that declares nothing fails here; a declaring
    op the instrument does not admit fails here. Neither can be fixed by
    staying quiet.
    """
    census = _census()
    admissible = {n for n, r in census.items() if r["verdict"] == "ADMISSIBLE"}
    declared = set(_declared())

    undeclared = sorted(admissible - declared)
    unmeasured = sorted(declared - admissible)
    print(f"\n[rc430] admissible {len(admissible)} · declared {len(declared)}")
    assert not undeclared, (
        f"{len(undeclared)} op(s) are behaviourally admissible but declare no "
        f"frame:\n  " + "\n  ".join(undeclared[:20])
        + "\n\nDeclare them. Do NOT narrow the predicate to match the roster — "
          "the predicate is the measurement and the roster is the record of it.")
    assert not unmeasured, (
        f"{len(unmeasured)} op(s) declare a frame the instrument does not "
        f"admit:\n  " + "\n  ".join(unmeasured[:20]))
    assert declared == set(REVIEWED_ROSTER), (
        f"the live declaring set differs from the reviewed roster; "
        f"added {sorted(declared - set(REVIEWED_ROSTER))}, "
        f"removed {sorted(set(REVIEWED_ROSTER) - declared)}")


def test_unadjudicated_ops_are_counted_under_a_down_only_ceiling() -> None:
    """An op the driver cannot reach is UNADJUDICATED, not passing.

    Without this the previous test is trivially satisfiable by making the
    driver reach nothing: an empty admissible set equals an empty declared set.
    The ceiling is what keeps §4 from being green by ignorance.
    """
    census = _census()
    counts: Dict[str, int] = {}
    for rec in census.values():
        counts[rec["verdict"]] = counts.get(rec["verdict"], 0) + 1
    print(f"\n[rc430] frame census verdicts: {json.dumps(counts, sort_keys=True)}")

    for cls, ceil in CEIL_FRAME_UNADJUDICATED.items():
        got = counts.get(cls, 0)
        assert got <= ceil, (
            f"{cls} rose to {got}, above CEIL_FRAME_UNADJUDICATED[{cls!r}]="
            f"{ceil}. The unadjudicated class is growing, which means the "
            f"frame axis is going UNMEASURED on more of the registry, not "
            f"less. Drain NO_ARG by making the op's worked example bind its "
            f"arguments; drain BASE_RAISES the same way. Raising a CEIL needs "
            f"a reason in the same diff.")
    # CONTRACT_SKIP is the one residual class a future rc could quietly abuse
    # to make a red go away, so it is held to its stated reason: every entry
    # must be a REGISTERED op that really does document the contract claimed
    # for it. A name that is not in the registry, or one whose declaration says
    # nothing about primality, is a skip with no evidence behind it.
    for name, reason in fp.CONTRACT_SKIP.items():
        entry = get_tool_schema().lookup(name)
        assert entry is not None, f"CONTRACT_SKIP names an unregistered op: {name}"
        assert "PRIME" in reason.upper(), reason
        declared_text = " ".join(p.summary or "" for p in entry.parameters)
        assert "prime" in declared_text.lower(), (
            f"{name} is skipped for a primality contract, but no parameter of "
            f"its own declaration mentions one: {declared_text!r}. Either the "
            f"skip is wrong or the declaration is.")

    reached = counts.get("ADMISSIBLE", 0) + counts.get("NOT_ADMISSIBLE", 0)
    assert reached >= 130, (
        f"only {reached} ops were actually DRIVEN. §4 compares two sets the "
        f"instrument can see; if it can see almost nothing, both are empty and "
        f"agree for the wrong reason.")


# ══════════════════════════════════════════════════════════════════════
# 5. THE PAYLOAD SAYS WHAT THE MEASUREMENTS SAY
# ══════════════════════════════════════════════════════════════════════

def test_describe_frames_is_derived_from_the_tool_schema() -> None:
    d = describe()
    frames = d["frames"]
    declared = _declared()
    assert frames["total"] == len(declared)
    assert set(frames["ops"]) == set(declared)
    for name, row in frames["ops"].items():
        assert row["scope"] == declared[name].frame_scope
        assert row["axis"] == list(declared[name].frame_axis)
    assert sum(frames["by_scope"].values()) == frames["total"]
    assert set(frames["by_scope"]) <= set(FRAME_SCOPES)
    assert set(frames["by_axis"]) <= set(FRAME_AXES)
    assert frames["definitions"] == dict(FRAME_SCOPES)
    assert frames["axes"] == dict(FRAME_AXES)
    # the admission rule ships as DATA and NAMES the file that enforces it
    assert frames["verified_by"]["test"] == "tests/test_frame_scope_rc430.py"
    assert frames["verified_by"]["instrument"] == "tools/frame_probe.py"
    assert "never sampled" in frames["verified_by"]["rule"]


def test_the_frame_axis_is_orthogonal_to_the_lane_axis() -> None:
    """Two different questions about one op, asserted rather than narrated.

    Lane says WHAT an op reads of its operand; frame says what it reduces that
    read IN. If the two declaring sets coincided, one of the fields would be a
    re-spelling of the other.
    """
    d = describe()
    lane_ops, frame_ops = set(d["lanes"]["ops"]), set(d["frames"]["ops"])
    assert lane_ops and frame_ops
    assert not (lane_ops & frame_ops), (
        f"an op declares BOTH a lane and a frame: {sorted(lane_ops & frame_ops)}. "
        f"That is allowed in principle — but at rc430 the sets are disjoint, "
        f"and a change wants recording rather than silence.")


# ══════════════════════════════════════════════════════════════════════
# 6. HOW IT FAILS — the both-sides bite, pre-registered
# ══════════════════════════════════════════════════════════════════════

def _mutated(entry: ToolEntry, **kw: Any) -> ToolEntry:
    """A copy of ``entry`` with a DELIBERATELY WRONG declaration. ToolEntry is a
    frozen dataclass, so this is a real object the real gate can be run against
    — not a local restatement of what the gate would have said."""
    return dataclasses.replace(entry, **kw)


def test_every_false_scope_fails_the_ratchet() -> None:
    """FALSIFIER F-1, exhaustive. For each declaring op, substitute every OTHER
    value in ``FRAME_SCOPES`` into a real ToolEntry copy and run the REAL
    comparison (``assert_declaration_matches``). REFUTED if any false value
    still passes — a gate that accepts a wrong answer is not a gate.

    rc430-repair note (`#T1127`): this used to compute
    ``[s for s in FRAME_SCOPES if s != entry.frame_scope and s == measured]``
    and assert the list was empty. With §2 having already established
    ``measured == entry.frame_scope``, that list is empty for the same reason a
    thing cannot differ from itself — the check was DOMINATED by §2 and could
    not go red in any state where the suite was green. It now calls the shipped
    comparison, so weakening that comparison shows up HERE.
    """
    census = _census()
    rows: List[str] = []
    non_discriminating: List[str] = []
    for name, entry in sorted(_declared().items()):
        rec = census[name]
        accepted = []
        for false_scope in FRAME_SCOPES:
            if false_scope == entry.frame_scope:
                continue
            try:
                assert_declaration_matches(
                    _mutated(entry, frame_scope=false_scope), rec)
            except AssertionError:
                continue                   # the gate bit, as it must
            accepted.append(false_scope)   # the gate ACCEPTED a lie
        rows.append(f"  {name:60s} {entry.frame_scope:11s} "
                    f"false_that_PASS={accepted or 'NONE (discriminating)'}")
        if accepted:
            non_discriminating.append(f"{name}: {accepted}")
    print("\n[rc430] F-1 exhaustive false-scope sweep\n" + "\n".join(rows))
    print(f"declarers {len(rows)} | fully discriminating "
          f"{len(rows) - len(non_discriminating)}/{len(rows)}")
    assert rows, "no declarers — F-1 would pass vacuously"
    assert not non_discriminating, (
        "REFUTED — a false frame_scope passes the ratchet for:\n  "
        + "\n  ".join(non_discriminating))


@pytest.mark.parametrize("op_name,lie", [
    ("srmech.music.interval_vector", "parametric"),
    ("srmech.cascade.cyclic_mod_add", "fixed"),
])
def test_gate_fires_on_a_planted_defect(op_name: str, lie: str) -> None:
    """FALSIFIER F-2 — the LIVE gate function, driven with an injected lie.

    A mis-declared ToolEntry copy is passed to the SAME
    ``assert_declaration_matches`` §2 uses, and it must raise. Both directions
    are planted: a hard-wired op claiming to be parametric, and a parametric op
    claiming to be hard-wired.

    rc430-repair note (`#T1127`): this used to open
    ``with pytest.raises(AssertionError): assert measured == lie`` over
    locally-computed values, having just asserted both ``measured ==
    entry.frame_scope`` and ``entry.frame_scope != lie``. The raise was
    therefore guaranteed by the preconditions rather than by the gate, and the
    gate itself was never invoked — the test would have stayed green if the
    shipped comparison had been deleted outright.
    """
    entry = get_tool_schema().lookup(op_name)
    assert entry is not None and entry.frame_scope != lie
    rec = _census()[op_name]

    # Precondition: the TRUTH passes the real gate.
    assert_declaration_matches(entry, rec)

    # The LIE must fail that same real gate.
    with pytest.raises(AssertionError):
        assert_declaration_matches(_mutated(entry, frame_scope=lie), rec)


def test_the_planted_axis_also_fails_the_ratchet() -> None:
    """FALSIFIER F-2b. The scope is not the only declared field — ``frame_axis``
    is compared too, and a falsifier that only ever plants a bad SCOPE leaves
    the axis half of the comparison unproven.

    The planted axis is a VALID vocabulary term that is the WRONG one for the
    op, never a made-up token. That distinction is the whole test: a nonsense
    token is rejected by the registration TYPE-VALIDATOR at construction, so a
    falsifier built on one never reaches the declared-vs-measured comparison and
    proves the validator works instead of the ratchet. Only a well-formed lie
    reaches the gate under test.
    """
    census = _census()
    survived = []
    planted = 0
    for name, entry in sorted(_declared().items()):
        declared_axis = tuple(entry.frame_axis)
        for axis in sorted(FRAME_AXES):
            if (axis,) == declared_axis:
                continue
            planted += 1
            try:
                assert_declaration_matches(
                    _mutated(entry, frame_axis=(axis,)), census[name])
            except AssertionError:
                continue                   # the gate bit, as it must
            survived.append(f"{name}: declared {declared_axis} accepted ({axis},)")
    assert planted, "no lie was planted — F-2b would pass vacuously"
    print(f"\n[rc430 repair] F-2b planted {planted} well-formed false axes")
    assert not survived, (
        "REFUTED — a false frame_axis passes the ratchet for:\n  "
        + "\n  ".join(survived))


def test_no_control_in_this_module_is_computed_and_then_ignored() -> None:
    """FALSIFIER F-3 — the DEAD-SEAM check. rc428's D1 computed its controls
    and never read them: ``main()`` returned 0 while printing ``DEAD SEAM``.

    Every control this module builds must be CONSUMED by an assertion, and the
    cheapest way to prove that is to re-derive them here and require they are
    non-trivial. A control that cannot come out any other way is not a control.
    """
    a = fp.classify("LEAK_A", {"x": 0, "y": 3}, _leak_a)
    b = fp.classify("LEAK_B", {"x": 0, "y": 3, "n": 11}, _leak_b)
    c = fp.classify("CLEAN", {"x": 0, "y": 3, "n": 11, "g": 3}, _clean)
    verdicts = {fp.declared_scope(r["findings"]) for r in (a, b, c)}
    assert verdicts == {"fixed", "parametric"}, (
        f"the three controls collapsed to {verdicts}; an instrument that "
        f"returns one verdict for every input is not measuring anything")
    # 20 at rc430; 21 at the rc430 repair (`#T1127`), when the probe's
    # degeneracy screen stopped foreclosing the parametric sweep and
    # srmech.math.cyclic.gcd became measurable. The count moved because the
    # INSTRUMENT was repaired, not because an op was hand-added to the roster.
    assert len(_declared()) == len(REVIEWED_ROSTER) == 21
    assert set(_census()) == {e.name for e in get_tool_schema().tools}, (
        "the census does not cover the registry, so §4's set comparison is "
        "over a subset it chose itself")
