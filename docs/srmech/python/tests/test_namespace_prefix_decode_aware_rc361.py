"""rc361 (`#T1034`) — the DECODE-AWARE namespace-prefix ratchet.

WHY THIS EXISTS. ADR-0010 moves ~73 modules out of ``srmech.amsc`` into seven
new top-level namespaces. The dotted prefix ``srmech.amsc.`` is therefore a
quantity that should DRAIN toward the four modules the ADR says ``amsc`` keeps
(``format`` / ``catalog`` / ``descriptor`` / ``gap_suggester``). To watch it
drain you have to be able to COUNT it — and in the generated artifacts you
cannot do that with a text search, because three of them do not store their
text as text.

THE MEASUREMENT (rc361, all six regen-all artifacts, prefix ``srmech.amsc.``):

    artifact                        as-text   DECODED
    ------------------------------  -------   -------
    srmech_carrier_registry.c           191       533   <- MIXED: decoded 2.8x text
    srmech_class_registry.c               0        40   <- 100% invisible to grep
    srmech_tool_registry.c             1219         4
    srmech_responsion_registry.c         72         0   (control: no byte arrays)
    _tool_docs.py                      1201         0   (control: not a .c file)
    _c_claims.py                        250         0   (control: not a .c file)
    ------------------------------  -------   -------
    TOTAL                              2933       577

THE MIXED ROW IS THE DANGEROUS ONE. A textual sweep over the carrier registry
reports 191 hits, "fixes" all 191, and exits successful — while 533 survive in
the compiled table that a bare-C host reads straight out of the binary. A flat
``0`` (the class registry) at least invites suspicion; ``191`` looks like a
finished job. This is the same shape as the rc359 finding one level over: a
measurement surface reporting a value it did not measure.

⚠️ WHAT EACH CHANNEL ACTUALLY COUNTS — READ THIS BEFORE RE-PINNING (rc362)
==========================================================================
**as-text counts CITATIONS. decoded counts POPULATION. Only the second is the
quantity ADR-0010 drains.** The two were treated as one measurement until
rc362 landed nine ops in ``srmech.music`` and this file went red on macOS
while the namespace it guards had not grown at all.

MEASURED at rc362, on this branch:

* ``srmech_tool_registry.c`` as-text 1219 → **1224** (+5)
* ``_tool_docs.py``          as-text 1201 → **1206** (+5)
* every other artifact, both channels: **unchanged**
* TOTAL as-text 2933 → **2943**; TOTAL decoded 577 → **577**
* registered ops NAMED ``srmech.amsc.*``: **396, unchanged**; the nine new ops
  are all ``srmech.music.*``

The +10 is 5 citations × the 2 artifacts that carry op DOCUMENTATION. All five
sit in the nine music ops' worked examples, and four of them are the same
line — ``from srmech.math.q import Q`` — because ``Q`` IS the operand carrier
those ops take. The fifth is ``from srmech.math.rational import best_rational``
in ``commensurability_verdict``, which exists to SHOW the sibling op that
silently converts an inharmonic spectrum into a harmonic one. These are import
statements in code that ``test_worked_examples_execute_rc354`` actually RUNS —
not decoration that could be trimmed.

**So the two gates are in direct opposition, and that is the finding.**
``test_worked_examples_strict_zero_rc353`` REQUIRES every op to name its
siblings; this family's siblings (``amsc.q``, ``amsc.rational.best_rational``,
``amsc.cyclic``) all live in the draining namespace. You cannot document an op
whose siblings are in ``srmech.amsc`` without raising the as-text count. An
instrument that forbids that is measuring the wrong thing — and this one
already SHIPS the right channel beside it.

**Consequence, stated so it is not rediscovered as a bug:** the as-text pins
will DRIFT UPWARD as documentation improves, and that is expected rather than a
regression. A rise here means "more prose cites amsc"; it does NOT mean the
namespace grew. **The decoded channel is the population measure.** A future rc
that adds a real ``srmech.amsc.*`` op must still go red on ``decoded`` —
``test_the_decoded_channel_tracks_population_not_citation`` below proves that
channel can still fire, using this rc's own artifacts as the experiment.

**When re-pinning as-text, the burden is to show the population did not move.**
Re-run the two measurements this docstring quotes (op-name count by namespace,
and the decoded totals). If decoded is flat and the op-name count is flat, the
rise is citation and the pin may be raised WITH THAT REASON RECORDED. If either
moved, it is a regression and the fix is upstream, not here.

⚠️ rc364 — THE ARC'S FIRST EXECUTION SLICE MOVED BOTH CHANNELS BY **ZERO**, AND
THAT IS A FINDING ABOUT THE PLAN, NOT A FAILURE OF THE MOVE
=============================================================================
rc364 executed ADR-0010's ``make_class`` re-homed clause: the built-in
``class_catalog`` / ``cascade_catalog`` / ``worked_instances`` descriptor
directories left ``srmech/amsc/_research/`` for ``srmech/cascade/catalogs/``,
and ``srmech/amsc/_research/`` was deleted. Measured after
``python3 tools/regen_all.py``:

    as-text  2957 -> 2957   (FLAT)
    decoded   577 ->  577   (FLAT)

Every per-artifact pair is unchanged; the only regen delta in the whole tree was
one line of header COMMENT in ``srmech_class_registry.c`` naming the new source
directory.

**Why, stated so the next slice is planned from it.** This ratchet counts the
DOTTED prefix ``srmech.amsc.`` — a *module-path* population. What rc364 moved
was *data files*, whose location is only ever written as a filesystem path with
slashes (``srmech/amsc/_research/class_catalog/``), which this prefix does not
match. And the descriptor BODIES are untouched: a ``[class]`` descriptor's
``op = "srmech.biology.genome.chromosome"`` names an op whose MODULE did not move,
so all 40 decoded hits in the class registry survive by construction.

The instrument is not broken — it measures exactly the population it names, and
it correctly reports that the population did not move. **The wrong belief was
the plan's**: ADR-0010 folds "move the catalogs" and "move the modules" into one
drain, and only the second contributes to this counter. A catalog move is
orthogonal to it.

**Consequence for the arc.** Do not read a flat rc here as "the slice did
nothing", and do not go looking for a pin to lower after a catalog-shaped slice.
The quantity rc364 actually reduced — ``srmech/amsc/`` went from 4 subpackages
to 3 — has NO ratchet in this tree. That measurement is the natural prerequisite
rc for the first MODULE-moving slice, and per ADR-0010's own ordering constraint
it must land in its own rc with a green baseline BEFORE any module moves; it was
deliberately NOT minted inside rc364, because an instrument built in the same
arc as the change it detects has no baseline to be attributed against.

WHAT IS PINNED, AND WHY IT IS A RATCHET AND NOT A SNAPSHOT
==========================================================
Each artifact pins BOTH channels, down-only, in the house pattern this tree
already uses for the sibling ref-notation ceilings: ``found <= ceiling`` fails
on a GAIN, and ``found < ceiling`` fails too, telling you to lower the pin so
the gain cannot be given back. So a module move shows up as a red test that
says "lower these numbers", which is exactly the signal the arc wants, and an
accidental REGROWTH cannot hide inside slack.

The decoded side is pinned SEPARATELY rather than summed with the textual side.
Merging them would let a drop in one channel mask a rise in the other — and the
whole point of this file is that the two channels are different measurements,
neither of which is wrong about what it counts. rc362 is the case that proves
the separation was worth having: the textual channel moved by 10 and the
decoded channel did not move at all, and only because they are pinned apart
could that be read as "documentation grew" rather than "the drain regressed".

⚠️ ``c/include/srmech.h`` IS NOT PINNED HERE, AND THE rc361 BRIEF WAS WRONG
ABOUT IT. The brief listed ``srmech.h`` (176 as-text) among the "generated
artifacts". It is not generated — ``tools/codegen_manifest.GENERATORS``
declares exactly SIX outputs and ``srmech.h`` is not one of them; it is
hand-maintained. Its 176 textual hits are real, but pinning a hand-edited
header in a codegen ratchet would produce a test that goes red on ordinary
authoring. The brief's "TOTAL 3109" is the six generated artifacts (2933) plus
that hand-written header (176). The generated-only total is 2933.

THE DECODER IS SHARED, NOT FORKED
=================================
``tests/c_byte_arrays.py``, extracted at rc361 from the rc359 work in
``test_ref_notation_emitted_rc348.py``. Introspected first, as instructed:
srmech ships NO op that decodes an int sequence to text (``tlv_unpack`` and
``byte_search`` both hard-``TypeError`` on non-bytes-like input and return
``bytes``/``int``; the decode-direction ops return bits/ints/labels), so a
test-side decoder is correct — but there was already ONE, and this file uses it
rather than minting a second. See that module's docstring for the full
introspection result.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SR_ROOT = _HERE.parent.parent          # docs/srmech
_TOOLS = _SR_ROOT / "python" / "tools"

for _p in (str(_HERE), str(_TOOLS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import codegen_manifest as cm  # noqa: E402

from c_byte_arrays import decoded_blobs, octal_escaped_name_chars  # noqa: E402

#: The namespace the ADR drains. Trailing dot on purpose: it counts MEMBER
#: references (``srmech.math.rational``), not the bare package name, so the four
#: modules ``amsc`` keeps are the floor this can honestly fall to — not zero.
PREFIX = "srmech.amsc."

#: DOWN-ONLY per-artifact ``(as_text, decoded)`` pins. MEASURED at rc361 on this
#: branch, both channels, every declared regen-all output.
#:
#: TO LOWER: move modules, run ``python3 tools/regen_all.py``, then set these to
#: what the failure message prints — in the SAME commit as the move.
#:
#: ⚠️ NEVER RAISE THE **DECODED** PIN. A rise there means the prefix POPULATION
#: grew — something was added back into ``srmech.amsc`` while the ADR is
#: draining it — and the fix is upstream, never here.
#:
#: The **as-text** pin is different, and rc362 is where that was established
#: (see the channel note in the module docstring). It counts CITATIONS, so it
#: rises when documentation improves. Raising it is legitimate ONLY with the
#: reason recorded at the pin, and only after showing BOTH: (a) the decoded
#: total did not move, and (b) the count of registered ops named
#: ``srmech.amsc.*`` did not move. Raising it silently is not.
CEIL_AMSC_PREFIX = {
    # The MIXED one, and the largest decoded population by 13x. 191 of its 724
    # total references are greppable; the other 533 are in four hoisted
    # long-string byte arrays (`cs_lstr_0..3`, the >4000-byte carrier JSON
    # fragments the generator hoists out of string literals).
    #
    # as-text 191 -> 204 at rc363 (+13), decoded UNCHANGED at 533. CITATION, not
    # population, and the burden this file sets was discharged before re-pinning:
    # ops named srmech.amsc.* stayed **396**, and the decoded TOTAL stayed 577
    # with every per-artifact decoded count flat. rc363 registered two carriers
    # the ADR-0012 C3 use-derivation gate found (`Theta`, `CarrierSpectrum`;
    # 26 -> 28) and widened eight ops' declared param types to the union they
    # already accepted. Both edits grow the DERIVED `ops.consumes/produces`
    # back-index, whose entries are full ToolEntry names — five of the eight
    # widened ops live in srmech.amsc, so their names now appear against
    # EllMonomial / Theta as well as EllRatio. Those back-index lists sit in the
    # SHORT string literals (greppable) rather than the four hoisted long-string
    # arrays, which is why this artifact moved on the text channel alone.
    # NOT a drain regression: no module moved into srmech.amsc and no op was
    # added there. The right fix for a genuine drain regression would be
    # upstream; here there is nothing upstream to fix.
    #
    # as-text 204 -> 203 at rc366 (-1), decoded 533 -> 529 (-4). THIS ONE IS A
    # DRAIN, and the good kind: srmech.amsc.harmonics moved to
    # srmech.music.harmonics — the FIRST real module move under ADR-0010. Four
    # harmonics op references live in the hoisted byte arrays (decoded) and one
    # in the short back-index strings (as-text); the move rewrote all five
    # amsc->music. This is the decoded POPULATION channel falling for the first
    # time — exactly the event this ratchet exists to force onto the record.
    # Re-pinned DOWN in the same commit as the move so the gain cannot be given
    # back.
    #
    # as-text 203 -> 201 at rc370 (-2), decoded UNCHANGED at 529. The
    # elliptic_partial_fraction slice (srmech.amsc.elliptic_partial_fraction ->
    # srmech.apokatastasis.elliptic_partial_fraction). The op is a CARRIER op —
    # it is named in the EllMonomial `consumes` and ThetaSum `produces`
    # back-indexes — but for those two SMALL carriers the JSON is an INLINE
    # string literal (as-text), NOT one of the four hoisted >4000-byte byte
    # arrays (cs_lstr_0..3, the decoded channel). So the move drops 2 as-text and
    # ZERO decoded, and the decoded amsc population stays 529 (contrast the rc366
    # harmonics move, whose refs DID live in the hoisted arrays). This is a real
    # drain of the citation channel; the population channel did not move because
    # this op was never in it.
    #
    # as-text 201 -> 156 at rc371 (-45), decoded 529 -> 516 (-13). THE WHOLE-FAMILY
    # drain (the 24 remaining elliptic / modular / theta / q-series modules ->
    # srmech.apokatastasis). This is the POPULATION channel falling HARD — unlike
    # rc370's single elliptic_partial_fraction (whose carrier refs were inline
    # as-text), this family includes ellbase / thetasum, the elliptic CARRIER
    # bases whose op refs DO live in the four hoisted >4000-byte byte arrays. 13
    # decoded refs move amsc->apokatastasis (measured: apokatastasis decoded goes
    # 0 -> 13, amsc 529 -> 516), plus 45 as-text back-index / carrier-name
    # citations. Re-pinned DOWN in the same commit as the move.
    #
    # as-text UNCHANGED at 156, decoded 516 -> 500 at rc372 (-16). THE srmech.math
    # SLICE (octonion / kepler / modular_linalg -> srmech.math). This is the
    # POPULATION channel again: octonion is a genome CARRIER op, and its 16
    # oct_mult / oct_bind / oct_conjugate back-index references live in the four
    # hoisted >4000-byte carrier-registry byte arrays (the decoded channel), NOT
    # in the short as-text back-index strings — so decoded amsc goes 516 -> 500
    # and srmech.math. rises 0 -> 16 (conserved). as-text stays 156 because the
    # octonion carrier's SHORT back-index citations were already outside this
    # artifact (its ToolEntry citations sit in the tool_registry / _tool_docs).
    # as-text 156 -> 100 at rc373 (-56), decoded 500 -> 202 (-298). THE A-N
    # PRIMITIVES batch (10 modules amsc->math). The decoded POPULATION channel
    # again: hdc / laplacian / cyclic / rational etc. carrier back-index refs in
    # the four hoisted byte arrays move amsc->math (decoded amsc 500 -> 202,
    # srmech.math. 16 -> 314, conserved). as-text drops 56 short back-index cites.
    # as-text 100 -> 75 at rc374 (-25), decoded 202 -> 196 (-6). THE CARRIERS batch
    # (15 modules amsc->math — the math bucket's last slice). Only 6 carrier-family
    # OP back-index refs (the poly / qpoly / qbipoly / tripoly / carrier_ladder /
    # carrier_spectrum ops) live in the hoisted byte arrays and move amsc->math
    # (decoded amsc 202 -> 196, srmech.math. 314 -> 320, conserved); the bulk of
    # the roster (mat / vec / hv / q / …) are pure CARRIERS with no ToolEntry op,
    # so they never entered the decoded back-index. as-text drops 25 short cites.
    # as-text 75 -> 68 at rc375 (-7), decoded 196 -> 97 (-99). THE BIOLOGY bucket
    # (coupling / genome / plasmid / q8 amsc->srmech.biology). UNLIKE rc374's pure
    # carriers, GENOME OPS ARE OPERATORS and their back-index refs DO live in the
    # four hoisted >4000-byte byte arrays: 99 genome / q8 / coupling op references
    # move amsc->biology (decoded amsc 196 -> 97, srmech.biology. 0 -> 99, conserved;
    # math / apokatastasis / music decoded all UNCHANGED at 320 / 13 / 13). This is
    # the decoded POPULATION channel falling by the arc's second-largest single move.
    # 7 short back-index citations drop on the as-text channel.
    # as-text 68 -> 67 at rc376 (-1), decoded UNCHANGED at 97. THE INTROSPECT/NATIVE
    # CORE (final slice): carrier_schema moved amsc->introspect and its ONE as-text
    # back-index citation here repointed; decoded 97 holds because compose /
    # carrier_schema are NOT carrier ops in the four hoisted byte arrays (the carrier
    # registry now carries 1 srmech.introspect. decoded ref in their place).
    # as-text 67 -> 0 at rc377 (-67), decoded 97 -> 2 (-95). THE CASCADE SUBPACKAGE
    # (the FINAL slice): the 15 cascade modules folded amsc->srmech.cascade. cascade
    # ops (one / cayley_dickson / sedenion_register / cd_register / hypercomplex_dft /
    # matrix_cascades / …) ARE carriers, so their back-index refs dominate this
    # artifact's hoisted byte arrays: 95 refs move amsc->cascade (decoded amsc 97 -> 2,
    # srmech.cascade. 0 -> 95, conserved), and all 67 short as-text back-index cites
    # repoint too. amsc's decoded population is now DRAINED to its 2 keeper residuals.
    "c/src/srmech_carrier_registry.c": (0, 2),
    # TEXT 0 is TRUE, and true about the wrong thing. Every one of the four
    # baked [class] descriptors (`cls_desc_0..3`) is a decimal byte array, so a
    # grep has nothing to read. 37 DISTINCT dotted names live in there.
    # decoded 40 -> 29 at rc375 (-11), as-text UNCHANGED at 0. THE BIOLOGY bucket:
    # the baked [class] Genome descriptor's op refs (op = "srmech.biology.genome.*")
    # move amsc->biology inside the decimal byte arrays (decoded amsc 40 -> 29,
    # srmech.biology. 0 -> 11, conserved). Still 100% invisible to a text grep.
    # decoded 29 -> 0 at rc377 (-29), as-text UNCHANGED at 0. THE CASCADE SUBPACKAGE:
    # the baked [class] One / SedenionRegister descriptors' op refs (op =
    # "srmech.cascade.one.*" / "srmech.cascade.sedenion_register.*") move amsc->cascade
    # inside the decimal byte arrays (decoded amsc 29 -> 0, srmech.cascade. 0 -> 28).
    # The class registry's amsc decoded population is now ZERO — the arc is COMPLETE;
    # the decode-only non-vacuity demonstration below rides srmech.cascade. from here.
    "c/src/srmech_class_registry.c": (0, 0),
    # Overwhelmingly textual: the ToolEntry summaries are string literals. The 4
    # decoded hits are in its own hoisted long strings.
    #
    # as-text 1219 -> 1224 at rc362 (+5), decoded UNCHANGED at 4. CITATION, not
    # population: the nine srmech.music ops' worked examples import their own
    # operand carrier (`from srmech.math.q import Q`, x4) and the sibling op the
    # explanation warns against (`from srmech.math.rational import
    # best_rational`, x1). Ops named srmech.amsc.* stayed 396. Verified against
    # the pre-branch commit: this artifact read exactly 1219 there.
    #
    # as-text 1224 -> 1225 at rc363 (+1), decoded UNCHANGED at 4. ONE citation,
    # and it is a CORRECTION rather than a new reference: genome_register_attested's
    # `source` param example read 'srmech.genome.<name>' — a module path that has
    # never existed (the module is srmech.biology.genome). The rc363 prose op-ref
    # gate (tests/test_prose_oprefs_resolve_rc363.py) found it and it was fixed,
    # which necessarily moves this counter up by one. Ops named srmech.amsc.*
    # stayed 396; decoded flat everywhere.
    #
    # as-text 1225 -> 1221 at rc366 (-4), decoded UNCHANGED at 4. The four
    # srmech.amsc.harmonics ToolEntry citations were rewritten to srmech.music.
    # by the ADR-0010 module move; the decoded 4 are this artifact's own hoisted
    # strings, untouched by the move.
    #
    # as-text 1221 -> 1219 at rc367 (-2), decoded UNCHANGED at 4. The naming
    # slice (srmech.amsc.naming -> srmech.introspect.naming). Only TWO as-text
    # here, not four like harmonics: naming's two ToolEntry `name=` citations
    # dropped, but its worked-example / SIBLINGS prose cites its own module by
    # the SLASH form (srmech/introspect/naming.py) and its siblings by slash too,
    # so no extra dotted `srmech.amsc.` refs live in its ToolEntry text. decoded
    # stays 4 — naming is not a carrier op, so it has no hoisted byte-array refs.
    #
    # as-text 1219 -> 1216 at rc368 (-3), decoded UNCHANGED at 4. The
    # responsion_schema slice (srmech.amsc.responsion_schema ->
    # srmech.introspect.responsion_schema). THREE as-text here: the responsion
    # ToolEntry `name=` citation, its worked-example import
    # `from srmech.amsc.responsion_schema import responsion_schema`, and the
    # carrier_schema ToolEntry's SIBLINGS prose which named responsion_schema by
    # its dotted path — all three rewritten amsc->introspect. decoded stays 4
    # (responsion_schema is not a carrier op; the 4 are this artifact's own
    # hoisted strings, untouched by the move).
    #
    # as-text 1216 -> 1202 at rc369 (-14), decoded UNCHANGED at 4. The
    # op_provenance slice (srmech.amsc.op_provenance -> srmech.introspect.
    # op_provenance) — the LARGEST doc move of the arc so far: 6 registered ops,
    # each with a dotted ToolEntry `name=` citation AND a worked-example import
    # (`from srmech.amsc.op_provenance import ...`), plus the sibling-prose refs
    # from format.sha256_bytes / genome.telomere_tick / gene_express / the four
    # op_provenance cross-references — 14 amsc. citations in all, rewritten
    # amsc->introspect. decoded stays 4 (op_provenance is not a carrier op; the 4
    # are this artifact's own hoisted strings, untouched by the move).
    #
    # as-text 1202 -> 1201 at rc370 (-1), decoded UNCHANGED at 4. The
    # elliptic_partial_fraction slice — exactly ONE as-text here: the op's single
    # ToolEntry `name=` citation, repointed amsc->apokatastasis. The SIBLINGS
    # refs in the three neighbouring ops (elliptic_determinant / cn_vwp_multisum_lhs
    # / an_vwp_multisum_lhs) name it in the SLASH form
    # (srmech/apokatastasis/elliptic_partial_fraction.py:60), which the dotted
    # prefix does not match; and its own explanation's carrier ref
    # (thetasum.ThetaSum) was still amsc at rc370. decoded stays 4.
    #
    # as-text 1201 -> 1151 at rc371 (-50), decoded UNCHANGED at 4. THE WHOLE-FAMILY
    # drain: the 24 modules' ToolEntry `name=` citations + their sibling-prose
    # dotted refs repointed amsc->apokatastasis. decoded stays 4 (this artifact's 4
    # are its own hoisted strings; the moved family's carrier back-index lives in
    # the CARRIER registry, which is where the -13 decoded drop landed).
    #
    # as-text 1151 -> 1111 at rc372 (-40), decoded UNCHANGED at 4. The srmech.math
    # slice: the 10 moved ops' ToolEntry `name=` citations + their worked-example
    # imports (`from srmech.math import kepler`, the `srmech.math.<m>.<op>` dotted
    # refs) + sibling-prose dotted refs repointed amsc->math. decoded stays 4 (this
    # artifact's 4 are its own hoisted strings; the octonion carrier back-index
    # decoded drop landed in the CARRIER registry).
    # as-text 1111 -> 577 at rc373 (-534), decoded 4 -> 0 (-4). The A-N primitives
    # batch: the 10 moved modules ToolEntry name= citations + worked-example
    # imports + sibling-prose dotted refs repointed amsc->math; the 4 hoisted
    # decoded refs were to moved-module ops and left too.
    # as-text 576 -> 440 at rc374 (-136), decoded UNCHANGED at 0. The CARRIERS
    # batch: the moved carrier-family ops' ToolEntry name= citations + worked-
    # example imports + sibling-prose dotted refs repointed amsc->math.
    # as-text 440 -> 282 at rc375 (-158), decoded UNCHANGED at 0. THE BIOLOGY bucket:
    # the moved genome / q8 / coupling / plasmid ops' ToolEntry name= citations +
    # worked-example imports + sibling-prose dotted refs repointed amsc->biology.
    # as-text 282 -> 257 at rc376 (-25), decoded UNCHANGED at 0. THE INTROSPECT/NATIVE
    # CORE: the 4 compose ToolEntry name= citations + the carrier_schema citation +
    # ~20 sibling-prose / worked-example dotted refs to the moved introspect-core
    # modules (tool_schema / _tool_docs / _native / carrier_schema) repointed
    # amsc->{cascade, introspect, srmech}. decoded stays 0 (this artifact carries none).
    # as-text 257 -> 69 at rc377 (-188), decoded UNCHANGED at 0. THE CASCADE SUBPACKAGE:
    # the 75 cascade ops' ToolEntry name= citations + worked-example imports +
    # sibling-prose dotted refs repointed amsc->cascade. decoded stays 0 (this
    # artifact carries no cascade back-index byte arrays — those live in the carrier
    # registry). The 69 residual as-text amsc cites are keeper-op documentation
    # (format.sha256_bytes and kin) that legitimately still name srmech.amsc.
    "c/src/srmech_tool_registry.c": (88, 0),  # rc436 (local task T1141): 86 -> 88, +2 as-text, CITATION only. Both burdens discharged: (a) decoded UNMOVED at 0 (and the decoded TOTAL unmoved at 2), (b) ops NAMED srmech.amsc.* FLAT -- the single registration this rc makes is srmech.cascade.octonion_associator_support. The +2 is that op naming srmech.amsc.format.sha256_bytes in its `composes` tuple and again in its curated explanation; Class-A content-addressing really is the last stage of the cascade, since the digest is taken over the assembled support set. Naming a sub-op is a REFERENCE, never a move INTO srmech.amsc.  # was: (86, 0)  # rc427 (local task T1130): 82 -> 86, +4 as-text, CITATION only. Both burdens are discharged: (a) decoded UNMOVED at 0, and (b) the count of ops NAMED srmech.amsc.* is FLAT at 9 — the six ops registered this rc live under srmech.math.cyclic and srmech.cascade, none under srmech.amsc. The +4 is exactly the four `composes` tuples that name srmech.amsc.format.sha256_bytes as a sub-op (finite_semiflow, conjugacy_census, reversal_law_census, anti_automorphism_witnesses) — every census in that rc content-addresses its hit SET, which is the whole point of the round, so Class-A really is a stage of those cascades. Unlike rc423 this does NOT move _tool_docs.py (flat at 79): the declarations ride the ToolEntry registration, not the curated docs. Naming a sub-op is a REFERENCE to srmech.amsc, never a move INTO it.  # was: (82, 0)  # rc423 (local task T1113): 72 -> 82, +10 as-text, CITATION only — the composes POPULATION pass. Both burdens this pin sets are discharged: (a) decoded UNMOVED at 0, and (b) NO op was registered (registry flat at 605; ops named srmech.amsc.* flat at 9). The +10 is exactly the ten `composes` tuples that now name an srmech.amsc op as a sub-op: 8 rows cite srmech.amsc.format.sha256_bytes (Class-A content-addressing is genuinely the first stage of those cascades), 1 cites srmech.amsc.catalog.get_attested_dataset, 1 cites srmech.amsc.catalog.register_attested_root. Each appears once per emitted artifact, which is why _tool_docs.py moves by the same +10. Naming a sub-op is a REFERENCE to srmech.amsc, never a move INTO it — the rc362/rc420 case exactly.  # was: (72, 0)  # rc420 (local task T1114): +3 as-text, DOCUMENTATION only (decoded flat, op-name count flat at 396) — the new cascade leaf docs legitimately cite srmech.amsc siblings: byte_slice + utf8_encode name srmech.amsc.format.sha256_raw (the stride hash between them), seq_get names srmech.amsc.catalog.get_attested_dataset (the keyed-lookup Class-E primitive it degenerates from). The rc362 case exactly.
    # rc368 — THE FIRST MODULE MOVE TO MOVE THIS ARTIFACT (the new data point).
    # This was the CONTROL row through harmonics/naming: "no byte arrays, decoded
    # 0 is a real zero". It is still a real zero on the decoded channel, but the
    # as-text channel is no longer inert here — responsion_schema IS the
    # responsion-registry schema, so the generated source-of-truth comment
    # (`Source of truth: srmech.<...>.responsion_schema._pure_responsion_schema()`,
    # emitted by gen_responsion_registry.py) repointed amsc->introspect. as-text
    # 72 -> 71 (-1), decoded UNCHANGED at 0. The 71 residual are the edge-OPERATOR
    # names (zeilberger / dispatch / coupling / laplacian / cascade / ...), whose
    # modules did NOT move — a rename of the schema op does not touch them.
    #
    # as-text 71 -> 41 at rc371 (-30), decoded UNCHANGED at 0. THE WHOLE-FAMILY
    # drain: the 24 modules ARE edge-OPERATOR names in the responsion registry
    # (zeilberger / q_zeilberger / gosper / thetasum / ellbase / eisenstein / ...),
    # so the generated source-of-truth comments for those operators repointed
    # amsc->apokatastasis. decoded stays 0 (this registry carries no byte arrays).
    # as-text 41 -> 6 at rc373 (-35), decoded UNCHANGED at 0. The A-N primitives
    # batch: dispatch / laplacian / cyclic etc. ARE edge-OPERATOR names in the
    # responsion registry, so their generated source-of-truth comments repointed
    # amsc->math. decoded stays 0 (this registry carries no byte arrays).
    # as-text 6 -> 3 at rc375 (-3), decoded UNCHANGED at 0. THE BIOLOGY bucket:
    # coupling / genome are edge-OPERATOR names in the responsion registry, so their
    # generated source-of-truth comments repointed amsc->biology.
    # as-text 3 -> 0 at rc377 (-3), decoded UNCHANGED at 0. THE CASCADE SUBPACKAGE:
    # `cascade` IS an edge-OPERATOR name in the responsion registry (chiral_flip /
    # net_chirality / … are cascade ops), so the generated source-of-truth comments
    # `Source of truth: srmech.cascade.<...>` repointed amsc->cascade — draining the
    # last amsc as-text residual here to 0.
    "c/src/srmech_responsion_registry.c": (0, 0),
    # CONTROL: generated .py, no embedded arrays. Their long integer runs were
    # inspected at rc361 and are worked-example OUTPUT VALUES (octonion basis
    # vectors, inertia signatures, index triples) — genuine numeric data, not a
    # hidden text channel. So these zeros are measured, not construction
    # artifacts of the decoder skipping non-.c files.
    # as-text 1201 -> 1206 at rc362 (+5), decoded UNCHANGED at 0. The SAME five
    # citations as the tool registry above — these two artifacts are the pair
    # that carry op documentation, which is why the drift is 5 x 2 and lands
    # nowhere else. Verified against the pre-branch commit: exactly 1201 there.
    # as-text 1206 -> 1202 at rc366 (-4), decoded UNCHANGED at 0. The SAME four
    # harmonics citations as the tool registry — this is the doc pair — rewritten
    # amsc->music by the module move.
    # as-text 1202 -> 1200 at rc367 (-2), decoded UNCHANGED at 0. The naming
    # slice — the SAME two ToolEntry `name=` citations as the tool registry (this
    # is the doc pair), rewritten amsc->introspect.
    # as-text 1200 -> 1197 at rc368 (-3), decoded UNCHANGED at 0. The
    # responsion_schema slice — the SAME three citations as the tool registry
    # (this is the doc pair): the responsion ToolEntry name, its worked-example
    # import, and the carrier_schema SIBLINGS prose ref — all amsc->introspect.
    # as-text 1197 -> 1183 at rc369 (-14), decoded UNCHANGED at 0. The
    # op_provenance slice — the SAME 14 citations as the tool registry (this is
    # the doc pair): the 6 ToolEntry names, their worked-example imports, and the
    # sibling-prose refs — all amsc->introspect.
    # as-text 1183 -> 1182 at rc370 (-1), decoded UNCHANGED at 0. The
    # elliptic_partial_fraction slice — the SAME single ToolEntry `name=` citation
    # as the tool registry (this is the doc pair), repointed amsc->apokatastasis;
    # the slash-form SIBLINGS refs do not match the dotted prefix.
    # as-text 1182 -> 1133 at rc371 (-49), decoded UNCHANGED at 0. THE WHOLE-FAMILY
    # drain — the doc-pair partner of the tool registry: the 24 modules' op
    # documentation (ToolEntry names + sibling-prose dotted refs) repointed
    # amsc->apokatastasis.
    # as-text 1133 -> 1093 at rc372 (-40), decoded UNCHANGED at 0. The srmech.math
    # slice — the SAME 40 citations as the tool registry (this is the doc pair):
    # the 10 moved ops' documentation (ToolEntry names + worked-example imports +
    # sibling-prose dotted refs) repointed amsc->math.
    # as-text 1093 -> 562 at rc373 (-531), decoded UNCHANGED at 0. The A-N
    # primitives batch, doc-pair partner of the tool registry: the 10 modules op
    # documentation repointed amsc->math.
    # as-text 562 -> 431 at rc374 (-131), decoded UNCHANGED at 0. The CARRIERS
    # batch, doc-pair partner of the tool registry: the moved carrier-family ops'
    # documentation repointed amsc->math.
    # as-text 431 -> 275 at rc375 (-156), decoded UNCHANGED at 0. THE BIOLOGY bucket,
    # doc-pair partner of the tool registry: the moved genome / q8 / coupling /
    # plasmid ops' documentation repointed amsc->biology.
    # as-text 275 -> 252 at rc376 (-23), decoded UNCHANGED at 0. THE INTROSPECT/NATIVE
    # CORE, doc-pair partner of the tool registry: the same compose / carrier_schema
    # ToolEntry documentation + sibling-prose dotted refs to the moved introspect-core
    # modules repointed amsc->{cascade, introspect}.
    # as-text 252 -> 66 at rc377 (-186), decoded UNCHANGED at 0. THE CASCADE SUBPACKAGE,
    # doc-pair partner of the tool registry: the same 75 cascade ops' documentation
    # (ToolEntry names + worked-example imports + sibling-prose dotted refs) repointed
    # amsc->cascade. decoded stays 0. The 66 residual as-text are keeper-op docs.
    "python/srmech/introspect/_tool_docs.py": (80, 0),  # rc436 (local task T1141): 79 -> 80, +1 as-text, CITATION only -- the merged `composes` declaration of srmech.cascade.octonion_associator_support naming srmech.amsc.format.sha256_bytes. Decoded UNMOVED at 0; no op registered under srmech.amsc. See the srmech_tool_registry.c note above.  # was: (79, 0)  # rc423 (local task T1113): 69 -> 79, +10 as-text, CITATION only — the composes POPULATION pass; the same ten sub-op references the tool registry gained, counted once per emitted artifact. Decoded UNMOVED at 0; no op registered (registry flat at 605, ops named srmech.amsc.* flat at 9). See the srmech_tool_registry.c note above for the per-citation breakdown.  # was: (69, 0)  # rc420 (local task T1114): +3 as-text, DOCUMENTATION only (decoded flat, op-name count flat at 396) — the new cascade leaf docs legitimately cite srmech.amsc siblings: byte_slice + utf8_encode name srmech.amsc.format.sha256_raw (the stride hash between them), seq_get names srmech.amsc.catalog.get_attested_dataset (the keyed-lookup Class-E primitive it degenerates from). The rc362 case exactly.
    # as-text 250 -> 248 at rc367 (-2), decoded UNCHANGED at 0. rc367 is the
    # FIRST module move to move THIS artifact — a departure from the harmonics
    # analog. _c_claims.py is the op -> C-symbol CLAIM manifest, keyed only for
    # ops the ledger classifies `c_dispatched`. harmonics' ops are compute (int
    # from a str), so they never appeared here; naming's lookup / reverse_order
    # ARE c_dispatched (srmech_catalog_lookup / srmech_reverse_order), so their
    # two keys moved amsc->introspect. The C SYMBOLS are unchanged — only the
    # Python-side dotted key repointed.
    # rc368 UNCHANGED at (248, 0) — the INVERSE of rc367. responsion_schema is
    # non_compute/composes_c (it has C REACH via srmech_responsion_schema but is
    # not itself a `c_dispatched` leaf), so it never had a key in this op->C-symbol
    # CLAIM manifest. A composes_c module move does not touch _c_claims.py.
    # as-text 248 -> 247 at rc369 (-1), decoded UNCHANGED at 0. BACK to the rc367
    # behaviour: op_provenance_hash IS a `c_dispatched` leaf (C peer
    # srmech_op_provenance_hash + a real ctypes binding in _native.py), so it has
    # exactly ONE key in this manifest, repointed amsc->introspect. The op's five
    # SIBLINGS (carry / op_verdict / family_verdict / reproject /
    # lossy_projection_record) are non_compute/composes_c and never appeared here.
    # The C SYMBOLS are unchanged — only the Python-side dotted key repointed.
    # as-text 247 -> 246 at rc370 (-1), decoded UNCHANGED at 0. Same shape as
    # rc367/rc369: elliptic_partial_fraction IS a `c_dispatched` leaf (C peer
    # srmech_elliptic_partial_fraction + a real ctypes binding), so it has exactly
    # ONE key here, repointed amsc->apokatastasis. The C SYMBOL is capability-named
    # and unchanged — only the Python-side dotted key moved.
    # as-text 246 -> 218 at rc371 (-28), decoded UNCHANGED at 0. THE WHOLE-FAMILY
    # drain: the family's c_dispatched leaves (the 27 op keys across the 24 modules
    # — apagodu_zeilberger / eisenstein / ellbase / elliptic_* / gosper /
    # harmonic_maass / q_* / riemann_theta* / thetasum / unary_theta / wz_* /
    # zeilberger) each repointed amsc->apokatastasis. The C SYMBOLS are
    # capability-named and unchanged — only the Python-side dotted keys moved.
    # as-text 218 -> 210 at rc372 (-8), decoded UNCHANGED at 0. The srmech.math
    # slice: the moved ops' c_dispatched leaves — kepler's 3 (equation_of_centre /
    # kepler_solve / pin_slot), octonion's 3 (oct_mult / oct_conjugate / oct_bind),
    # modular_linalg's gf_rref (C_CLAIMS) + crt_combine (UNVERIFIABLE_CLAIMS) = 8
    # keys — each repointed amsc->math. gf_solve / gf_nullspace are composition_of_c
    # (no C claim), so they never had a key here. The C SYMBOLS are capability-named
    # and unchanged — only the Python-side dotted keys moved.
    # as-text 210 -> 91 at rc373 (-119), decoded UNCHANGED at 0. The A-N
    # primitives batch: the moved modules c_dispatched leaves (cyclic / hdc /
    # laplacian / primes / rational / search / template / tlv / text / dispatch
    # op keys) repointed amsc->math. The C SYMBOLS are capability-named, unchanged.
    # as-text 91 -> 90 at rc374 (-1), decoded UNCHANGED at 0. The CARRIERS batch:
    # exactly one moved carrier-family op is a c_dispatched leaf keyed here
    # (carrier_spectrum's srmech_carrier_spectrum), repointed amsc->math. The bulk
    # of the roster are pure carriers with no ToolEntry / C claim.
    # as-text 90 -> 59 at rc375 (-31), decoded UNCHANGED at 0. THE BIOLOGY bucket:
    # genome / q8 / coupling ARE heavily c_dispatched, so 31 op keys in this op->C-
    # symbol CLAIM manifest (sourced from the Rosetta classification ledger)
    # repointed amsc->biology. The C SYMBOLS (srmech_genome_* / srmech_q8_* /
    # srmech_coupling_*) are capability-named and UNCHANGED — only the Python-side
    # dotted keys moved (ABI stays 10). The MCP dispatch vtable (srmech_invoke.c)
    # holds NO dotted op names for these, so it needed no repoint.
    # as-text 59 -> 58 at rc376 (-1), decoded UNCHANGED at 0. THE INTROSPECT/NATIVE
    # CORE: exactly one moved op is a c_dispatched leaf keyed here — carrier_schema's
    # srmech_carrier_schema — repointed amsc->introspect (the compose chain-runner ops
    # are composes_c, not c_dispatched leaves, so they were never keyed in this manifest).
    # as-text 58 -> 6 at rc377 (-52), decoded UNCHANGED at 0. THE CASCADE SUBPACKAGE:
    # the cascade ops that are c_dispatched leaves (cyclic_gcd / best_rational_signed /
    # autocorrelation / kuramoto_step / the cd_* / one_* / sed_* / hamming_* / dft
    # families) had their op->C-symbol claim keys repointed amsc->cascade (sourced
    # from the Rosetta ledger). The C SYMBOLS are capability-named and UNCHANGED —
    # only the Python-side dotted keys moved (ABI stays 10).
    "python/srmech/introspect/_c_claims.py": (6, 0),
}

#: The generated-artifact totals, pinned so a per-file edit cannot quietly move
#: the aggregate.
#:
#: Renamed from ``RC361_TOTAL_*`` at rc362: the as-text value is no longer an
#: rc361 measurement, and a constant whose NAME asserts a provenance its VALUE
#: no longer has is the quiet staleness this tree keeps repairing. The rc361
#: origin is recorded here instead, where it cannot go out of date.
#:
#: as-text 2933 (rc361) -> 2943 (rc362, +10 = the 5 citations x 2 artifacts).
#: decoded 577 (rc361)  ->  577 (rc362, FLAT — the population did not move).
TOTAL_AS_TEXT = 174    # rc436 (local task T1141): 171 -> 174, all three from the single new op's citations of srmech.amsc.format.sha256_bytes (+2 tool registry, +1 _tool_docs). Decoded UNMOVED at 2 and no op was registered under srmech.amsc (registry 655 -> 656, the one op under srmech.cascade), so this is the CITATION case, not a drain regression.  # was: 171    # rc427 (local task T1130): 167 -> 171, all four in the tool registry (_tool_docs flat at 79) — the four sha256_bytes `composes` citations of the ARROW + CENSUS registration. Decoded UNMOVED at 2 and no op was registered under srmech.amsc (registry 649 -> 655, all six elsewhere), so this is the CITATION case, not a drain regression.  # was: 167    # rc423 (local task T1113): 147 -> 167, +10 in the tool registry + +10 in _tool_docs — the composes POPULATION pass; ten `composes` tuples now name an srmech.amsc op as a sub-op, counted once per emitted artifact. Decoded UNMOVED at 2 and no op was registered (registry flat at 605), so this is the CITATION case, not a drain regression. See the per-file notes for the breakdown.  # was: 147    # rc420 (local task T1114): 141 -> 147, +3 in the tool registry + +3 in _tool_docs — the same three documentation citations counted once per emitted artifact (see the per-file notes); decoded UNMOVED at 2, so this is the documentation case, not a drain regression.  # was: 141    # rc376 637 -> rc377 141 (-496: THE CASCADE SUBPACKAGE, the FINAL slice — the 75 cascade ops' ToolEntry/doc citations repoint amsc->cascade across the tool_registry (-188) + _tool_docs (-186) + carrier (-67) + _c_claims (-52) + responsion (-3); class UNCHANGED at 0. The residual 141 are keeper-op docs that legitimately still name srmech.amsc.)
TOTAL_DECODED = 2      # rc376 126 -> rc377 2 (-124: THE CASCADE SUBPACKAGE — cascade ops ARE carriers, so 95 carrier back-index refs + 29 class descriptor refs move amsc->cascade in the hoisted byte arrays. amsc's decoded population is now DRAINED to 2 keeper residuals — ADR-0010 execution is COMPLETE)


def _counts(rel_path: str) -> "tuple[int, int]":
    """``(as_text, decoded)`` occurrences of ``PREFIX`` in one artifact."""
    path = _SR_ROOT / rel_path
    as_text = path.read_text(encoding="utf-8", errors="replace").count(PREFIX)
    decoded = sum(blob.count(PREFIX) for _, blob in decoded_blobs(path))
    return as_text, decoded


@pytest.mark.parametrize("rel_path", sorted(CEIL_AMSC_PREFIX))
def test_amsc_prefix_population_is_down_only(rel_path: str) -> None:
    """DOWN-ONLY ratchet on BOTH channels, per artifact."""
    as_text, decoded = _counts(rel_path)
    ceil_text, ceil_decoded = CEIL_AMSC_PREFIX[rel_path]

    assert as_text <= ceil_text, (
        f"{rel_path}: {as_text} as-text '{PREFIX}' references, ceiling "
        f"{ceil_text} — the CITATION count grew by {as_text - ceil_text}.\n"
        f"⚠️ This does NOT by itself mean the namespace grew. This channel "
        f"counts every textual mention, including op DOCUMENTATION that names "
        f"a sibling living in srmech.amsc — which the worked-example "
        f"informativeness bar (test_worked_examples_strict_zero_rc353) "
        f"REQUIRES authors to write. Decide which it is before touching "
        f"anything:\n"
        f"  1. did the DECODED total move? (that is the population measure)\n"
        f"  2. did the count of ops NAMED srmech.amsc.* move off 396?\n"
        f"If both are flat, this is documentation and the pin may be raised "
        f"WITH THAT REASON RECORDED at the pin — see the rc362 entries. If "
        f"either moved, something really was added back into srmech.amsc while "
        f"ADR-0010 is draining it: fix the UPSTREAM source, then re-run "
        f"`python3 tools/regen_all.py`. Never shorten an explanation to get "
        f"under this number.")
    assert decoded <= ceil_decoded, (
        f"{rel_path}: {decoded} DECODED '{PREFIX}' references (inside embedded "
        f"byte arrays), ceiling {ceil_decoded} — GREW by "
        f"{decoded - ceil_decoded}. These are invisible to a textual grep but "
        f"they ship: a bare-C host reads this table directly.")

    if (as_text, decoded) != (ceil_text, ceil_decoded):
        pytest.fail(
            f"{rel_path}: GOOD NEWS — the prefix population FELL.\n"
            f"  as-text  {ceil_text} -> {as_text}\n"
            f"  decoded  {ceil_decoded} -> {decoded}\n"
            f"Lower CEIL_AMSC_PREFIX['{rel_path}'] to ({as_text}, {decoded}) so "
            f"the gain cannot be given back. If modules just moved, do it in the "
            f"same commit as the move.")


def test_the_totals_are_pinned_too() -> None:
    """A per-file edit cannot quietly move the aggregate.

    Both channels summed across the six generated artifacts. This is the number
    the arc quotes, so it gets its own pin.
    """
    text_total = sum(_counts(r)[0] for r in CEIL_AMSC_PREFIX)
    decoded_total = sum(_counts(r)[1] for r in CEIL_AMSC_PREFIX)
    assert (text_total, decoded_total) == (TOTAL_AS_TEXT, TOTAL_DECODED), (
        f"generated-artifact '{PREFIX}' totals moved:\n"
        f"  as-text  {TOTAL_AS_TEXT} -> {text_total}\n"
        f"  decoded  {TOTAL_DECODED} -> {decoded_total}\n"
        "Update TOTAL_AS_TEXT / TOTAL_DECODED alongside the per-file pins.\n"
        "⚠️ WHICH CHANNEL MOVED DECIDES WHAT THIS MEANS. as-text alone rising "
        "is DOCUMENTATION citing srmech.amsc ops (the rc362 case: +10, decoded "
        "flat, op-name count flat at 396) and is not a drain regression — "
        "re-pin with the reason recorded. decoded rising means the POPULATION "
        "grew and the fix is upstream. NOTE: this total covers the six "
        "GENERATED artifacts only. It excludes c/include/srmech.h (176 "
        "as-text), which is hand-maintained and deliberately not ratcheted "
        "here.")


def test_the_decoder_sees_what_a_text_grep_cannot() -> None:
    """⚠️ NON-VACUITY, and the indictment of a text-only sweep.

    Three separate proofs that this instrument is a measurement and not a
    tautology:

    (a) the class registry has ZERO textual hits and 40 decoded ones — if the
        decoder returned nothing, this fails;
    (b) a specific dotted name is present decoded and ABSENT as text — so the
        decoded count is reading real content, not counting artifacts;
    (c) the carrier registry's decoded count EXCEEDS its textual count — the
        mixed case, where a text-only sweep looks successful and is not.
    """
    cls = _SR_ROOT / "c/src/srmech_class_registry.c"
    raw = cls.read_text(encoding="utf-8", errors="replace")
    blobs = decoded_blobs(cls)

    # (a) the invisible file
    assert raw.count(PREFIX) == 0, (
        "the class registry now has TEXTUAL prefix hits. That is not a failure "
        "of this test, but it means the '100% invisible' example has changed — "
        "re-read the pins and this docstring.")
    joined = "\n".join(b for _, b in blobs)
    # rc377: amsc's class-registry decoded population DRAINED to 0 (the cascade
    # subpackage — the last [class] descriptor op refs under amsc — folded into
    # srmech.cascade). The decode-only demonstration now rides srmech.cascade.:
    # 100% invisible to a text grep here (all four [class] descriptors are decimal
    # byte arrays) yet it decodes to 28.
    assert joined.count("srmech.cascade.") == 28, (
        f"decoded {joined.count('srmech.cascade.')} srmech.cascade. hits in the "
        f"class registry, expected 28 (rc377: the [class] One / SedenionRegister "
        f"op refs moved amsc->cascade — this is where the class registry's "
        f"decode-only population now lives). If this is 0, THE DECODER HAS STOPPED OBSERVING and "
        f"every assertion in this file is now vacuous — check whether the "
        f"generator changed its byte-array template (hex literals, a renamed "
        f"array, a different declaration).")

    # non-vacuity of the extraction itself: pin the SHAPE, as rc348 does
    assert len(blobs) == 4, (
        f"expected 4 embedded [class] descriptors, decoded {len(blobs)}")
    assert {n for n, _ in blobs} == {
        "cls_desc_0", "cls_desc_1", "cls_desc_2", "cls_desc_3"}

    # (b) a name that ONLY the decoder can see
    witness = "srmech.cascade.one.one_matrix"
    assert witness in joined, (
        f"the witness name {witness!r} is no longer in the decoded payload; "
        f"pick another from the decoded blobs and update this test.")
    assert witness not in raw, (
        f"{witness!r} is now present as TEXT in the class registry, so it no "
        f"longer witnesses the decode-only channel. Choose a name that is still "
        f"only reachable by decoding.")

    # (c) the MIXED case — the dangerous one
    car_text, car_decoded = _counts("c/src/srmech_carrier_registry.c")
    assert car_decoded > car_text, (
        f"the carrier registry no longer hides MORE than it shows "
        f"(text {car_text}, decoded {car_decoded}). The 'a textual sweep looks "
        f"successful and leaves the majority behind' claim in this file's "
        f"docstring depended on that ordering.")
    # rc373: the A-N primitives batch moved ~298 amsc-decoded carrier refs to
    # srmech.math, so carrier amsc-decoded fell 500 -> 202 while class held 40.
    # rc374: the carriers slice moved 6 more (202 -> 196); class still 40.
    # rc375: the BIOLOGY bucket moved 99 carrier-registry refs (196 -> 97) AND 11
    # class-registry refs (40 -> 29) amsc->biology. The carrier registry is STILL
    # the dominant amsc-decoded population (97 vs class's 29, ~3.3x), but the drop
    # narrowed the ratio below 4x — the factor is lowered to 3x (97 >= 87) to state
    # that honestly rather than assume a stale multiple.
    assert car_decoded >= 3 * max(
        d for r, (_, d) in CEIL_AMSC_PREFIX.items()
        if r != "c/src/srmech_carrier_registry.c"), (
        "the carrier registry is no longer the dominant decoded population by "
        "an order of magnitude; re-measure before trusting the docstring table.")


def test_the_decoded_channel_tracks_population_not_citation() -> None:
    """⚠️ NON-VACUITY OF THE POPULATION CHANNEL — can ``decoded`` still go red?

    rc362 raised two as-text pins. That is only defensible if the OTHER channel
    is still a live instrument, because the as-text one has just been declared
    unable to distinguish a citation from a new op. So this asserts, rather
    than assumes, that ``decoded`` responds to population and would fire.

    ⚠️ AND IT USES A REAL EXPERIMENT, NOT A SYNTHETIC ONE. rc362 added nine ops
    and wired three of them into ``Q.ops.consumes`` and three into
    ``Qalg.ops.consumes`` — INSIDE the carrier registry's hoisted byte arrays,
    i.e. inside the decoded channel itself. So the decoded payload genuinely
    grew by nine op references this rc, and ``srmech.amsc.`` decoded stayed at
    exactly 533. That is the discrimination the gate depends on, performed on
    shipped content: nine references entered the channel and the amsc count did
    not move, BECAUSE they are named ``srmech.music.``. Had they been named
    ``srmech.amsc.*``, this file would be red on decoded and the correct fix
    would have been upstream.

    The counterfactual is asserted below by re-namespacing the decoded text and
    watching the count move — which is what makes this a measurement rather
    than a restatement of the pin.

    rc366 UPGRADE — THE EXPERIMENT IS NO LONGER ONLY A COUNTERFACTUAL. The
    rc362 nine were named ``srmech.music`` from birth, so the amsc-count-holds
    result was a NEGATIVE control. rc366 supplied the POSITIVE one: the
    ``srmech.amsc.harmonics`` module actually moved to ``srmech.music.harmonics``
    (the first real ADR-0010 module drain), and FOUR of its op references live
    inside these hoisted byte arrays. The decoded ``srmech.amsc.`` population
    fell 533 -> **529** and ``srmech.music.`` rose 9 -> **13**, by exactly those
    four — a genuine population move tracked by the decoded channel, not a
    re-namespacing thought experiment. The pins read 529 / 13 through rc370.

    rc371 — THE LARGEST POSITIVE MOVE SO FAR, AND THE RECEIVING SIDE IS NOW PINNED
    TOO. The whole-family drain (24 modules -> srmech.apokatastasis) moved 13
    elliptic-carrier op references (ellbase / thetasum and kin) inside these
    hoisted byte arrays: decoded ``srmech.amsc.`` fell 529 -> **516** and
    ``srmech.apokatastasis.`` rose 0 -> **13**, conserving the count. amsc is now
    pinned at 516, apokatastasis at 13, music holds at 13; the music counterfactual
    (re-namespace all 13 music refs) lands at 529 = 516 + 13.

    rc372 — A SECOND POSITIVE POPULATION MOVE, into a THIRD receiving namespace.
    The srmech.math slice (octonion / kepler / modular_linalg) moved 16
    octonion-CARRIER op references (oct_mult / oct_bind / oct_conjugate, which the
    genome consumes) inside these hoisted byte arrays: decoded ``srmech.amsc.``
    fell 516 -> **500** and ``srmech.math.`` rose 0 -> **16**, conserving the
    count. amsc is now pinned at 500, math at 16, apokatastasis holds at 13, music
    holds at 13; the music counterfactual (re-namespace all 13 music refs) lands
    at 513 = 500 + 13.
    """
    car = _SR_ROOT / "c/src/srmech_carrier_registry.c"
    joined = "\n".join(b for _, b in decoded_blobs(car))

    amsc = joined.count(PREFIX)
    music = joined.count("srmech.music.")
    apokatastasis = joined.count("srmech.apokatastasis.")
    math = joined.count("srmech.math.")
    biology = joined.count("srmech.biology.")
    assert amsc == 2, (
        f"the carrier registry's decoded amsc population is {amsc}, expected "
        f"2 — the cascade subpackage drained it 97 -> 2 at rc377 (ADR-0010 "
        f"execution COMPLETE); re-read the pins before trusting anything else.")
    assert music == 19, (
        f"expected 19 srmech.music op references inside the DECODED channel "
        f"(9 from the rc362 Q / Qalg ops.consumes back-index + 4 from the rc366 "
        f"harmonics module move + 6 from the rc424 RELATIONS lane), found "
        f"{music}. If this is 0 the natural experiment below is inert and this "
        f"test proves nothing — re-measure and pick a live example.")
    # rc371 — THE POSITIVE POPULATION MOVE, on the SAME (decoded) channel. The
    # whole-family drain moved 13 elliptic-carrier op refs (ellbase / thetasum and
    # kin) OUT of the amsc decoded count (529 -> 516) and INTO apokatastasis
    # (0 -> 13) inside these hoisted byte arrays. This pins the receiving side so a
    # future regression that dropped an op from the walk (rather than moving it)
    # would show apokatastasis falling without amsc rising.
    assert apokatastasis == 13, (
        f"expected 13 srmech.apokatastasis op references inside the DECODED "
        f"channel (the rc371 whole-family drain's carrier back-index), found "
        f"{apokatastasis}. amsc fell 529 -> 516 by exactly these 13; if this is "
        f"not 13 the population move is not conserved — re-measure.")
    # rc372 — THE srmech.math RECEIVING SIDE, pinned like apokatastasis. The math
    # slice moved 16 octonion-carrier op refs (oct_mult / oct_bind / oct_conjugate)
    # OUT of the amsc decoded count (516 -> 500) and INTO math (0 -> 16) inside
    # these hoisted byte arrays. Conserved: -16 amsc = +16 math.
    # rc374 — the CARRIERS slice moved 6 more carrier-family op refs OUT of the
    # amsc decoded count (202 -> 196) and INTO math (314 -> 320) inside these
    # hoisted byte arrays. Conserved: -6 amsc = +6 math.
    # rc384 (`#T957`) then ADDED one NEW srmech.math op — octonion_laplacian (the 𝕆
    # gain Laplacian) — whose carrier back-index refs land 3× in these arrays, the
    # SAME per-op count as its sibling quaternion_laplacian / magnetic_laplacian. So
    # the live srmech.math decoded population is 320 + 3 = 323. This is a NEW-op
    # growth, not a move, so no amsc pin shifts.
    # rc388 (`#T963`) then ADDED two NEW srmech.math ops — oct_torsor_act +
    # oct_torsor_div (the ℍ-torsor act/div of the seam coset H·e) — whose carrier
    # back-index refs land 2× each in these arrays, so 323 + 4 = 327. NEW-op
    # growth, not a move; no amsc pin shifts.
    # rc399 (`#T1064` Tier 3) then ADDED one NEW srmech.math op —
    # generalized_ngon (the guarded generalized-n-gon incidence-graph /
    # Feit–Higman spectral read) — whose carrier back-index ref lands 1× in these
    # arrays (via its int-typed n_points / spectral_max_nodes params → the 'int'
    # carrier), so 327 + 1 = 328. NEW-op growth, not a move; no amsc pin shifts.
    # rc408 (`#T1078`) — a THIRD cause category, and the first of its kind on this
    # pin: neither a move nor a new op, but an EXISTING op declaring a parameter it
    # always accepted. srmech.math.laplacian.mat_eigvals declared only `a: Mat`,
    # while its real signature is mat_eigvals(a, max_sweeps=500). Declaring
    # `max_sweeps: int` puts the op into the 'int' carrier's consumes back-index
    # alongside 'Mat', so its refs in these arrays go 1 -> 2 and the population is
    # 328 + 1 = 329. Measured, not inferred: decoding the base and current registries
    # and diffing showed mat_eigvals as the ONLY name whose count changed. The
    # back-index is now MORE correct — it previously did not know an op that takes an
    # int operand takes one. No amsc pin shifts (this is growth, not a move).
    # rc422 (local task T1123) — NEW-op growth again, and the first row on this pin
    # where a registered op contributes ZERO. The centre/covering layer adds five
    # srmech.math.covering ops; MEASURED by decoding the registry and counting by
    # name rather than inferring one-ref-per-op: center_parity 2 (its int param AND
    # its int return both land in the 'int' carrier's back-index), center_lift 1,
    # lift_fibre 1, linking_number_cwf 1 — and covering_catalog **0**, because it
    # takes no parameters and returns a dict, so it has no carrier back-index ref at
    # all. 332 + 5 = 337. The non-covering residual was re-measured at exactly 332,
    # unchanged, so this is growth and not a move. (The rc's other two new ops are
    # srmech.physics.qm.triality.*, which this pin does not count.)
    #
    # rc427 (`#T1130`) — 337 -> 338, and this one is POPULATION, not citation.
    # `srmech.math.cyclic.mod_mul_arrow` is a genuinely new srmech.math op and
    # contributes exactly 1 carrier back-index ref (its two params are `int`
    # and it returns a dict, so only the 'int' consumes row moves). The rc's
    # other five ops are srmech.cascade.*, which this pin does not count, and
    # the `table=` extensions to unit_loop / loop_invariants add no op at all.
    # Contrast the srmech.amsc channel in the same rc, which moved on as-text
    # only with decoded flat — the two channels behaving differently in one rc
    # is what this file exists to make visible.
    assert math == 338, (
        f"expected 338 srmech.math op references inside the DECODED channel "
        f"(rc372 octonion 16 + rc373 A-N primitives 298 + rc374 carriers 6 + rc384 "
        f"octonion_laplacian 3 + rc388 oct_torsor_act/div 4 + rc399 generalized_ngon "
        f"1 + rc408 mat_eigvals max_sweeps:int 1 + rc420 scale_round_half_even "
            f"3 — the local task T1114 Class-N registration: its float+int consumes "
            f"rows and int produces row in the carrier back-index — + rc422 the "
            f"covering layer 5, of which covering_catalog contributes 0 "
            f"+ rc427 mod_mul_arrow 1), "
            f"found {math}. If this is not 338 "
        f"the population is not conserved — re-measure.")
    # rc375 — THE srmech.biology RECEIVING SIDE, the arc's SECOND-LARGEST positive
    # population move (after rc373's 298) and the FOURTH receiving namespace pinned
    # here. UNLIKE rc374's pure carriers, the biology bucket's genome / q8 / coupling
    # ops ARE OPERATORS whose back-index refs live in these hoisted byte arrays: 99
    # refs moved OUT of the amsc decoded count (196 -> 97) and INTO biology (0 -> 99)
    # inside the same arrays. Conserved: -99 amsc = +99 biology. math / apokatastasis
    # / music all held (320 / 13 / 13) — the biology move touched none of them.
    # rc390 (`#T961`) then ADDED one NEW srmech.biology op — split_defect (the
    # ORDER-carrying octonion associativity read) — whose carrier back-index refs land
    # 2× in these hoisted byte arrays (the same per-op count as its octonion peers), so
    # the live srmech.biology decoded population is 99 + 2 = 101. NEW-op growth, not a
    # move; no amsc pin shifts.
    # rc408 (`#T1078`) — 101 -> 106, the SAME third cause category as the math pin
    # above: no move, no new op, five EXISTING ops declaring parameters they always
    # accepted, whose types name a registered carrier. Measured by decoding the base
    # and current registries and diffing per name — these five are the only biology
    # names whose counts changed:
    #   chromosome                1 -> 2  gains the 'int' carrier from its
    #                                     newly-declared active_count / centromere /
    #                                     centromere_at (Optional[int]); it already
    #                                     held 'HV' via leaves / coupling.
    #   genome_catalog            0 -> 1  each of these four gains 'HV' from its
    #   genome_genes              0 -> 1  newly-declared coupling: Optional[HV].
    #   genome_load               0 -> 1  They held ZERO carrier refs before, because
    #   genome_window             0 -> 1  their only other param is `path: str` and
    #                                     there is no 'str' carrier.
    # `kernel: bool`, `catalog: Optional[dict]` and `attestation: dict` add nothing —
    # there is no 'bool' or 'dict' carrier. The back-index is now MORE correct: it
    # previously did not know that four ops taking an HV coupling take one. Growth,
    # not a move; no amsc pin shifts.
    assert biology == 106, (
        f"expected 106 srmech.biology op references inside the DECODED channel "
        f"(the rc375 biology bucket's genome / q8 / coupling carrier back-index 99 + "
        f"rc390 split_defect 2 + rc408 coupling/int declarations 5), found {biology}. "
        f"If this is not 106 the population is not conserved — re-measure.")
    # rc377 — THE srmech.cascade RECEIVING SIDE, the arc's FINAL and largest-carrier
    # population move. The 15 cascade modules folded amsc->srmech.cascade; their
    # carrier back-index refs (one / cayley_dickson / sedenion_register / cd_register
    # / hypercomplex_dft / matrix_cascades op refs) live in these hoisted byte
    # arrays: 95 refs moved OUT of the amsc decoded count (97 -> 2) and INTO cascade
    # (0 -> 95). amsc is now DRAINED to its 2 keeper residuals — ADR-0010 COMPLETE.
    # rc380 (`#T1055`) then ADDED two NEW cascade ops (cd_commutator + cd_cycle_holonomy,
    # the CD loop-defect ladder), and rc383 (`#T1054`) one more (defect_ladder, the
    # rung-indexed property-loss ladder + projector), so the live cascade decoded
    # population is the rc377 move's 95 + rc380's 2 + rc383's 1 = 98. The
    # move-conservation (95) stays a fact about the move; this pin measures the LIVE
    # count, which grows when new cascade ops land. rc384 (`#T957`) added one more —
    # octonion_frame_read (the 𝕆 frame-committed Hopf coherence read), +1 — and rc386
    # (`#T1062`) one more — cd_three_form (the exact-ℚ G₂ associative 3-form, the
    # scalar Re-twin of associator), +1 — and rc387 (`#T1037`, closing `#T1032`) two
    # more — flip_pair + group_algebra_table (the two STRUCTURED negative controls,
    # +2). rc395 (`#T1000`) then ADDED two more — cd_zero_divisor_witness +
    # cd_zero_divisor_witnesses (the dim-general zero-divisor ops that REPLACED the
    # hardwired sedenion_zero_divisor_witness), +2. The removed sedenion op had NO
    # decoded ref (0 on rc394, measured — it was never in this carrier namespace
    # index), so its removal is not an offset. rc398 (the Moufang loop-completion)
    # then ADDED five more — moufang_residue / is_moufang / malcev_defect /
    # unit_loop / loop_invariants (𝕆's Moufang-loop machinery promoted from
    # test-only to queryable), +5. So the live cascade decoded
    # population is 95 + 2 + 1 + 1 + 1 + 2 + 2 + 5 = 109.
    # rc399 (`#T1064` Tier 2) ADDED four NEW srmech.cascade ops — jordan_product /
    # cayley_plane_point / cayley_plane_incidence / octonion_hopf_base (the 𝕆P²
    # Cayley-plane surface) — but they add ZERO to THIS decoded count, so it HOLDS
    # at 109. The decoded-channel back-index only lists ops whose declared
    # param/return type-string carries an EMITTED carrier's name token; all four
    # take only `sequence` operands and return `Q` / `dict`, so they touch only
    # the `Q` carrier (not emitted to this const table) or no carrier at all —
    # unlike the rc398 Moufang ops, which each named the `int` carrier via a
    # `dim` / `list[list[list[int]]]` type. MEASURED 0 refs each (rc399, this
    # branch). A cascade op grows this count only when it declares an emitted
    # carrier token; these four legitimately do not.
    # rc427 (`#T1130`) — 154 -> 159, POPULATION: +1 for each of the five new
    # srmech.cascade ops (finite_semiflow, conjugacy_census, reversal_law_census,
    # anti_automorphism_witnesses, dihedral_group), every one of which declares
    # an emitted carrier token (`list[int]` / `list[list[int]]` / `int` / `str`).
    # The same rc's `table=` extensions to unit_loop / loop_invariants contribute
    # ZERO, measured: the back-index is keyed per (op, carrier) and not per
    # parameter, and both ops already carried an `int` ref through `dim`. That is
    # why the move is exactly +5 and not +7 — a parameter extension is invisible
    # here by construction, the same blind spot the op-name SET witness has.
    # rc430 repair (`#T1127`) — 159 -> 157, POPULATION, and a DECREASE for once.
    # `kuramoto_sin_term` / `kuramoto_gen_term` advertised `returns=float` and
    # actually return `Q` (the Class-N sin is exact); the repair corrects both.
    # `float` IS an emitted carrier and `Q` is NOT, so each op stops carrying an
    # emitted carrier token and leaves this back-index — exactly the mechanism
    # rc399 records four paragraphs up, where four new ops returning `Q` added
    # ZERO. Same rule, run backwards. -2, measured.
    #
    # Nothing was removed and no op was renamed: both ops are still registered
    # and still reachable; they are simply no longer claiming a carrier they
    # never produced. The count going DOWN here is the correction landing, and
    # the carrier registry moved with it (both ops left `float`'s `produces`
    # list for `Q`'s), which is also what moved the rc416 search-corpus witness.
    cascade = joined.count("srmech.cascade.")
    assert cascade == 157, (
        f"expected 157 srmech.cascade op references inside the DECODED channel "
        f"(the rc377 move's 95 + rc380's 2 loop-defect ops + rc383's defect_ladder + "
        f"rc384's octonion_frame_read + rc386's cd_three_form + rc387's flip_pair / "
        f"group_algebra_table + rc395's cd_zero_divisor_witness / _witnesses + rc398's "
        f"5 Moufang loop-completion ops + rc427's 5 arrow/census ops), found "
        f"{cascade}. The rc377 amsc->cascade move "
        f"conserved 95 (amsc 97 -> 2); rc380 grew it by 2, rc383 by 1, rc384 by 1, "
        f"rc386 by 1, rc387 by 2, rc395 by 2, rc398 by 5; rc420 (local task T1114) by 45 — the 27 cascade leaf-inventory registrations (12 leaves + 7 composites + 8 DFT leaves) land 45 consumes/produces rows in the carrier back-index; rc427 (local task T1130) by 5; the rc430 repair (local task T1127) SHRANK it by 2, the first decrease — kuramoto_sin_term / kuramoto_gen_term stopped advertising the emitted `float` carrier once their returns were corrected to the un-emitted `Q`. If this is not 157, re-measure.")
    # rc381 (`#T1052`) — THE srmech.physics.qm RECEIVING SIDE, pinned like biology
    # / cascade. UNLIKE every drain above, this move did NOT come out of the amsc
    # population — the qm subpackage was never under amsc. It is a whole-subpackage
    # RENAME (srmech.qm -> srmech.physics.qm), so 154 qm carrier back-index refs
    # (the octonion / quaternion / so8 / triality / gauge / sm op names the
    # genome + carriers consume) simply changed prefix in place inside these
    # hoisted byte arrays: srmech.qm. 154 -> 0, srmech.physics.qm. 0 -> 154, and
    # the amsc / math / biology / cascade / music / apokatastasis decoded counts
    # ALL held (this move touched none of them). Pinning the receiving side guards
    # against a regression that dropped a qm op from the walk (which would show
    # physics.qm falling with no matching rise elsewhere).
    # rc385 (`#T1048`) — two genuinely NEW physics.qm ops: quaternion_log (the
    # INVERSE of quaternion_exp) + quaternion_slerp (the exp/log S³ geodesic).
    # 154 -> 159: quaternion_log contributes 2 decoded references, quaternion_slerp
    # 3 (each op's back-index name + its HV-typed carrier slots — log has one HV
    # param, slerp two), so +5. No amsc pin moves (this is a genuine physics.qm
    # POPULATION add, tracked by the decoded channel exactly as designed).
    # rc396 (`#T1031`, position-operator half) then ADDED two more NEW physics.qm
    # ops — clock_operator (the Weyl clock U = diag(ω^k), the fenced position x̂) +
    # shift_operator (the cyclic shift V, the group-level momentum) — whose carrier
    # back-index refs land 2× EACH in these hoisted byte arrays (measured), so
    # 159 -> 163. NEW-op growth, not a move; no amsc pin shifts.
    physics_qm = joined.count("srmech.physics.qm.")
    assert physics_qm == 163, (
        f"expected 163 srmech.physics.qm op references inside the DECODED channel "
        f"(the rc381 qm-subpackage rename's carrier back-index — octonion / "
        f"quaternion / so8 / triality / gauge / sm op names — plus rc385's "
        f"quaternion_log (+2) / quaternion_slerp (+3) and rc396's clock_operator "
        f"(+2) / shift_operator (+2)), found {physics_qm}. "
        f"srmech.qm. fell to 0 by exactly the original 154; if this is not 163 the "
        f"population is not conserved — re-measure. (This is a physics.qm add, not "
        f"an amsc drain, so no amsc pin moves.)")
    assert joined.count("srmech.qm.") == 0, (
        f"the OLD srmech.qm. prefix still has "
        f"{joined.count('srmech.qm.')} decoded references — the rc381 rename left "
        f"stale qm names in the carrier back-index. Re-run tools/regen_all.py.")

    # THE COUNTERFACTUAL: had those music ops landed in the draining namespace,
    # the decoded channel would have seen every one of them.
    would_be = joined.replace("srmech.music.", PREFIX).count(PREFIX)
    assert would_be == amsc + music, (
        f"re-namespacing the 13 music references should raise the decoded amsc "
        f"count from {amsc} to {amsc + music}; got {would_be}. The decoded "
        f"counter is not responding to content, so the population half of this "
        f"ratchet is VACUOUS and the as-text pins raised at rc362 rest on "
        f"nothing.")
    assert would_be > CEIL_AMSC_PREFIX["c/src/srmech_carrier_registry.c"][1], (
        "the counterfactual population does not exceed the decoded ceiling, so "
        "this experiment would not actually have turned the gate red.")


def test_every_generated_artifact_is_pinned() -> None:
    """A seventh generator cannot ship an artifact this ratchet does not cover.

    DERIVED from the codegen manifest rather than hand-listed, so declaring a
    new output is what forces it to be measured. This is the same guard shape
    the sibling ref-notation ratchet uses, and it is the reason the two ``.py``
    artifacts are pinned here at all despite having no byte arrays: their
    textual channel is real.
    """
    declared = {g.output for g in cm.GENERATORS}
    pinned = set(CEIL_AMSC_PREFIX)
    assert declared == pinned, (
        "the regen-all output set and the pinned prefix ceilings disagree.\n"
        f"  declared but NOT pinned: {sorted(declared - pinned)}\n"
        f"  pinned but NOT declared: {sorted(pinned - declared)}\n"
        "Measure the new artifact with both channels and add it to "
        "CEIL_AMSC_PREFIX. Do NOT add c/include/srmech.h — it is hand-written, "
        "not generated.")


def test_the_as_text_channel_is_complete_no_name_char_is_octal_escaped() -> None:
    """⚠️ THE THIRD CHANNEL, closed by measurement rather than by assumption.

    The registries carry a third encoding: string literals with non-ASCII bytes
    written as ``\\NNN`` octal escapes (21,297 of them in the tool registry
    alone — the generator even suppresses an MSVC nag about them). A plain
    ``str.count`` is only a complete measure of the textual channel while no
    character OF A NAME is spelled as an escape.

    Measured at rc361: across the four registries, 21,474 octal escapes and
    NONE decodes into ``[A-Za-z0-9._]`` — every one is a non-ASCII UTF-8 byte.
    So two channels genuinely cover these files. If a generator ever escapes
    ASCII, this goes red and the as-text pins above have started undercounting.
    """
    offenders: list[str] = []
    total = 0
    for rel in sorted(r for r in CEIL_AMSC_PREFIX if r.endswith(".c")):
        found = octal_escaped_name_chars(_SR_ROOT / rel)
        total += 1
        if found:
            offenders.append(
                f"  {rel}: {len(found)} octal escape(s) decode to name "
                f"characters, e.g. {[chr(v) for v in found[:8]]}")
    assert total == 4, f"expected 4 C registries, scanned {total}"
    assert not offenders, (
        "octal escapes now hide dotted-name characters:\n" + "\n".join(offenders)
        + "\n\nThe as-text half of CEIL_AMSC_PREFIX is undercounting: part of a "
          "name is written as an escape, so str.count cannot see it. Either "
          "decode this channel too, or change the generator back.")
