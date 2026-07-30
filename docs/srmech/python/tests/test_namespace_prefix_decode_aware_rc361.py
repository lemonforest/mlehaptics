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
neither of which is wrong about what it counts.

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
#: NEVER RAISE. A rise means the prefix population GREW, i.e. something was
#: added back into ``srmech.amsc`` while the ADR is draining it.
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
    "c/src/srmech_tool_registry.c": (1219, 4),
    # CONTROL: has no byte arrays at all, so decoded 0 is a real zero rather
    # than a decoder that stopped working.
    "c/src/srmech_responsion_registry.c": (72, 0),
    # CONTROL: generated .py, no embedded arrays. Their long integer runs were
    # inspected at rc361 and are worked-example OUTPUT VALUES (octonion basis
    # vectors, inertia signatures, index triples) — genuine numeric data, not a
    # hidden text channel. So these zeros are measured, not construction
    # artifacts of the decoder skipping non-.c files.
    "python/srmech/amsc/_tool_docs.py": (1201, 0),
    "python/srmech/amsc/_c_claims.py": (250, 0),
}

#: The rc361 totals, pinned so a per-file edit cannot quietly move the aggregate.
RC361_TOTAL_TEXT = 2933
RC361_TOTAL_DECODED = 577


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
        f"{ceil_text} — the population GREW by {as_text - ceil_text}. ADR-0010 "
        f"drains this namespace; something was added back into srmech.amsc. Fix "
        f"the UPSTREAM source, then re-run `python3 tools/regen_all.py`.")
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
    assert (text_total, decoded_total) == (RC361_TOTAL_TEXT, RC361_TOTAL_DECODED), (
        f"generated-artifact '{PREFIX}' totals moved:\n"
        f"  as-text  {RC361_TOTAL_TEXT} -> {text_total}\n"
        f"  decoded  {RC361_TOTAL_DECODED} -> {decoded_total}\n"
        "Update RC361_TOTAL_TEXT / RC361_TOTAL_DECODED alongside the per-file "
        "pins. NOTE: this total covers the six GENERATED artifacts only. It "
        "excludes c/include/srmech.h (176 as-text), which is hand-maintained "
        "and deliberately not ratcheted here.")


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
