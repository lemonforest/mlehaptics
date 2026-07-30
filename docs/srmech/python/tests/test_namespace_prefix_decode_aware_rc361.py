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
line — ``from srmech.amsc.q import Q`` — because ``Q`` IS the operand carrier
those ops take. The fifth is ``from srmech.amsc.rational import best_rational``
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
#: references (``srmech.amsc.rational``), not the bare package name, so the four
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
    "c/src/srmech_carrier_registry.c": (191, 533),
    # TEXT 0 is TRUE, and true about the wrong thing. Every one of the four
    # baked [class] descriptors (`cls_desc_0..3`) is a decimal byte array, so a
    # grep has nothing to read. 37 DISTINCT dotted names live in there.
    "c/src/srmech_class_registry.c": (0, 40),
    # Overwhelmingly textual: the ToolEntry summaries are string literals. The 4
    # decoded hits are in its own hoisted long strings.
    #
    # as-text 1219 -> 1224 at rc362 (+5), decoded UNCHANGED at 4. CITATION, not
    # population: the nine srmech.music ops' worked examples import their own
    # operand carrier (`from srmech.amsc.q import Q`, x4) and the sibling op the
    # explanation warns against (`from srmech.amsc.rational import
    # best_rational`, x1). Ops named srmech.amsc.* stayed 396. Verified against
    # the pre-branch commit: this artifact read exactly 1219 there.
    "c/src/srmech_tool_registry.c": (1224, 4),
    # CONTROL: has no byte arrays at all, so decoded 0 is a real zero rather
    # than a decoder that stopped working.
    "c/src/srmech_responsion_registry.c": (72, 0),
    # CONTROL: generated .py, no embedded arrays. Their long integer runs were
    # inspected at rc361 and are worked-example OUTPUT VALUES (octonion basis
    # vectors, inertia signatures, index triples) — genuine numeric data, not a
    # hidden text channel. So these zeros are measured, not construction
    # artifacts of the decoder skipping non-.c files.
    # as-text 1201 -> 1206 at rc362 (+5), decoded UNCHANGED at 0. The SAME five
    # citations as the tool registry above — these two artifacts are the pair
    # that carry op documentation, which is why the drift is 5 x 2 and lands
    # nowhere else. Verified against the pre-branch commit: exactly 1201 there.
    "python/srmech/amsc/_tool_docs.py": (1206, 0),
    "python/srmech/amsc/_c_claims.py": (250, 0),
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
TOTAL_AS_TEXT = 2943
TOTAL_DECODED = 577


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
    assert joined.count(PREFIX) == 40, (
        f"decoded {joined.count(PREFIX)} prefix hits in the class registry, "
        f"expected 40. If this is 0, THE DECODER HAS STOPPED OBSERVING and "
        f"every assertion in this file is now vacuous — check whether the "
        f"generator changed its byte-array template (hex literals, a renamed "
        f"array, a different declaration).")

    # non-vacuity of the extraction itself: pin the SHAPE, as rc348 does
    assert len(blobs) == 4, (
        f"expected 4 embedded [class] descriptors, decoded {len(blobs)}")
    assert {n for n, _ in blobs} == {
        "cls_desc_0", "cls_desc_1", "cls_desc_2", "cls_desc_3"}

    # (b) a name that ONLY the decoder can see
    witness = "srmech.amsc.cascade.one.one_matrix"
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
    assert car_decoded >= 10 * max(
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
    """
    car = _SR_ROOT / "c/src/srmech_carrier_registry.c"
    joined = "\n".join(b for _, b in decoded_blobs(car))

    amsc = joined.count(PREFIX)
    music = joined.count("srmech.music.")
    assert amsc == 533, (
        f"the carrier registry's decoded amsc population is {amsc}, expected "
        f"533 — re-read the pins before trusting anything else in this file.")
    assert music == 9, (
        f"expected the 9 rc362 srmech.music op references inside the DECODED "
        f"channel (the Q / Qalg ops.consumes back-index), found {music}. If "
        f"this is 0 the natural experiment below is inert and this test proves "
        f"nothing — re-measure and pick a live example.")

    # THE COUNTERFACTUAL: had those nine ops landed in the draining namespace,
    # the decoded channel would have seen every one of them.
    would_be = joined.replace("srmech.music.", PREFIX).count(PREFIX)
    assert would_be == amsc + music, (
        f"re-namespacing the 9 music references should raise the decoded amsc "
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
