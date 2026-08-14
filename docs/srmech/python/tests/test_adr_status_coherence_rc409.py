"""rc409 (`#T1080`) — the ADR status-coherence gate. THE FIRST TEST TO READ `adr/`.

Every ADR carries a status on **two** hand-written surfaces that must
agree — the file's own ``**Status:**`` header and its row in the
``adr/README.md`` index — plus a third that must *define* the glyph they use
(the README legend). Nothing computed over any of it.

*(This paragraph said "Twelve ADRs" until ADR-0013 landed and made it thirteen.
The count now lives in ``_EXPECTED_ADR_COUNT`` alone, so there is exactly one
place to update — a bare count in prose beside a constant that already holds it
is the stale-by-construction shape ADR-0013 §6.5 is about.)*

Census that motivated this file, basis named::

    git grep -n "adr/" -- 'python/tests/*.py' 'python/tools/*.py' 'c/tools/*.py'
    -> 3 hits, ALL prose in docstrings/comments. ZERO read the tree.

It had already failed, and **not in the way the filing predicted**. Measured at
rc408 (before this file existed):

  * **ADR-0010** — file header ``🟢 ACCEPTED — execution arc OPEN``; README row
    ``🔄 Proposed``. A straight DISAGREEMENT, live on `main`.
  * **``🟢`` was used by two ADRs and defined by none.** The legend listed only
    ``✅ 🔄 ⏳ 🗑``, so the glyph two ADRs had reached for was not in the
    vocabulary at all — and the two used it to mean DIFFERENT things (0010
    "accepted, execution arc open"; 0012 "accepted, standing policy").

THE FIFTH STATE IS THE FIX, NOT A RELABELLING
=============================================
The improvised ``🟢`` was a symptom: the documented lifecycle
(``⏳/🔄 → ✅ → 🗑``) has **no state for "decided, being built, shape still
being learned"**, so an ADR in that condition had to either overclaim ``✅`` or
underclaim ``🔄``. rc409 formalises it per user direction — *"we wanted to keep
it plyable until we knew the shape to fully define it. to prevent many
superseeded ADRs."* A ``🟢 Implementing`` ADR is deliberately revisable, so it
need not be SUPERSEDED merely to change while its execution arc runs.

v0.9.0rc415 (`#T1098`) — THE STATUS IS A **PAIR**, NOT A GLYPH
==============================================================
The rc409 gate compared **glyphs only**, and that is the defect this rc fixes
at root. Its ``_leading_glyph`` helper returned the leading non-ASCII run and
**discarded the remainder** at all three of its parse sites (the file header,
the index cell, the legend item). The legend at ``adr/README.md`` is literally
a glyph→word **mapping**; reducing it to a *set of glyphs* on the line that
reads it throws away exactly the half that makes a status checkable.

What that cost, measured live on `main` at rc414 with all four rc409 tests
**green in 1.50 s**: ADR-0012 carried ``🟢 **ACCEPTED**`` in its own header and
``🟢 Accepted`` in the index. 🟢 is defined as *Implementing*; ✅ is *Accepted*.
``(🟢, ACCEPTED)`` is a pair the legend does not define — **and it was
duplicated identically on both surfaces**, which is precisely why a glyph-only
comparison found the two in perfect agreement. Two hand-written surfaces
agreeing on an illegal value look exactly like two surfaces agreeing.

The fix is ``tests/adr_corpus.status_pair`` — the leading extended grapheme
cluster per **UAX #29** (from the shipped ``srmech.math.text.glyph_stream``,
against the vendored UCD 16.0.0 table) plus the first run of ASCII-letter
clusters after it. That also **retires the hand-reasoning this docstring used
to carry** about variation selectors: rc409 matched a *run* of non-ASCII
specifically because several of these emoji carry U+FE0F as a second codepoint
and slicing ``[0]`` would compare half a glyph against a whole one. A grapheme
cluster is the unit that reasoning was reaching for; srmech already ships it.

``_leading_glyph`` survives as ``status_pair(...)[0]`` so the four original
tests are unchanged in behaviour, not merely in name.

INJECTION PROOFS — RUN, NOT DESCRIBED
=====================================
All four applied to the live corpus and reverted. A gate that only ever goes
red proves nothing, and a gate that only ever goes green proves less.

  A. **It is not merely always-red.** Applying the rc415 §3 status correction
     (index row and file header both to `🟢 Implementing`) turned the whole
     file green: **14 passed**, 13/13 legal pairs on both surfaces. Before it,
     exactly four tests failed and each named a distinct real defect.
  B. **It is not merely always-green.** An unrelated break — ADR-0005's index
     cell set to `✅ Implementing` — fired INV-3 and INV-4 and nothing else
     (2 failed, 12 passed).
  C. **A missing legend CRASHES rather than passing.** Renaming
     `**Status legend:**` to `**Status key:**` exits on
     `AssertionError: no '**Status legend:**' line in adr/README.md`, not on a
     clean run over an empty legend.
  D. **The population is checked by identity, not by count.** Deleting
     ADR-0007 and appending an ADR-0014 keeps the count at 13; INV-10 fires.
     The shipped rc409 gate re-pointed at that same mutated corpus reported
     `4 passed in 0.04s`.

TWO CHECKS DELIBERATELY **NOT** SHIPPED, AND WHY
================================================
Both were built, measured, and rejected on their false-positive rate. They are
recorded here because "we did not check X" is a fact a reader of a gate needs,
and because an unrecorded near-miss gets re-proposed every few rcs.

1. **Index TITLE vs file H1.** Measured **8 of 13 differ**, and every one is a
   deliberate editorial short form — ADR-0003's index title is *"C-host-
   standalone — never assume a Python environment (C↔Python parity)"* against
   an H1 of *"srmech is a C-host-standalone deliverable — never assume a Python
   environment"*. 8/13 false positives on day one earns a ``-k`` filter within
   a week, and a filtered gate is a gate that lies.

2. **Class-D ``match`` over the WHOLE status line.** 100% false-positive: it
   fires on ADR-0001, whose header legitimately ends *"…it is what gates
   promotion to ✅ Accepted"* — a second glyph+word pair in narrative position.
   Scoped instead to the glyph+word **PREFIX**, which agrees on 26/26 surfaces.
   :func:`test_whole_line_scan_is_reported_not_asserted` prints the whole-line
   count every run rather than hiding the near-miss.

ENCODING
========
Every read is explicit ``utf-8``. Status glyphs are non-ASCII, and on Windows
the default ``cp1252`` raises ``UnicodeEncodeError`` on ``⏳``. Failure messages
render glyphs as ``U+XXXX`` escapes rather than raw characters so a RED result
is readable on every platform — a gate whose failure output itself crashes is a
gate nobody can act on.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from adr_corpus import (
    ADR_DIR,
    ADR_README,
    adr_files,
    adr_number,
    legend as _legend_pairs,
    lifecycle as _lifecycle_ranks,
    read_adr,
    resolve_path,
    status_pair,
    tables,
    text_lines,
)

_ADR_DIR = ADR_DIR
_README = ADR_README

#: The ADR count is pinned so a DELETED or unparseable ADR fails loudly instead
#: of shrinking the population every assertion below iterates over. A gate that
#: silently checks fewer things is the false-green shape this suite exists to
#: stop.
#:
#: ⚠️ rc415 note: this pins a COUNT, not an IDENTITY. Deleting ADR-0007 and
#: appending an ADR-0014 leaves the count at 13 and this constant green, which
#: is why :func:`test_adr_numbers_are_contiguous` (INV-10) ships beside it —
#: verified by injection, the shipped rc409 gate reported ``4 passed in 0.04s``
#: against exactly that mutated corpus.
_EXPECTED_ADR_COUNT = 13

#: Phrases that declare a clause OPEN and deliberately unimplemented. A closed
#: list on purpose — see :func:`test_accepted_adrs_declare_no_deliberately_open_clause`.
_DELIBERATELY_OPEN = (
    "deliberately not implemented",
    "deliberately unimplemented",
)


def _fmt(glyph: str) -> str:
    """Render a glyph as ``U+XXXX`` codepoints — ASCII-safe on every console."""
    return "+".join(f"U+{ord(c):04X}" for c in glyph) if glyph else "<none>"


def _pair(glyph: str, word: str) -> str:
    """Render a ``(glyph, word)`` pair for a failure message."""
    return f"({_fmt(glyph)}, {word or '<none>'!r})"


def _leading_glyph(text: str) -> str:
    """The status glyph at the START of ``text``, or ``""`` when there is none.

    Kept as the pair's first half so the four rc409 tests below are unchanged
    in BEHAVIOUR, not merely in name. The rc415 defect was never that this
    function returned the wrong glyph — it was that returning only a glyph was
    the wrong ANSWER.
    """
    return status_pair(text)[0]


def _adr_files() -> "List":
    """The ADR markdown files, README excluded, in numeric order."""
    return adr_files()


def _file_pairs() -> "Dict[str, Tuple[str, str]]":
    """``{"0001": (glyph, word)}`` from each ADR's own ``**Status:**`` header.

    Searched, never line-indexed: ``0008``'s ``**Status:**`` is on line **5**,
    not line 3 — a renumbering banner occupies :3. A naive line-3 parser is
    wrong on 1 of 13 and would have to be "fixed" by exempting the one file it
    cannot read.
    """
    out: Dict[str, Tuple[str, str]] = {}
    for path in _adr_files():
        for line in text_lines(read_adr(path)):
            if line.startswith("**Status:**"):
                out[adr_number(path)] = status_pair(line[len("**Status:**"):])
                break
        else:                                            # pragma: no cover
            raise AssertionError(
                f"{path.name}: no '**Status:**' line anywhere in the file")
    return out


def _index_rows() -> "Dict[str, List[str]]":
    """``{"0001": cells}`` — the ``adr/README.md`` index table, by ADR number."""
    out: Dict[str, List[str]] = {}
    for table in tables(read_adr(_README)):
        for _line_no, cells in table:
            if not cells or not cells[0].startswith("[ADR-"):
                continue
            assert len(cells) >= 4, f"malformed index row: {cells!r}"
            number = cells[0][5:9]
            out[number] = cells
    return out


def _index_pairs() -> "Dict[str, Tuple[str, str]]":
    """``{"0001": (glyph, word)}`` from the ``adr/README.md`` index table."""
    return {k: status_pair(v[2]) for k, v in _index_rows().items()}


def _file_statuses() -> "Dict[str, str]":
    """``{"0001": glyph}`` — the rc409 shape, preserved for its four tests."""
    return {k: g for k, (g, _w) in _file_pairs().items()}


def _index_statuses() -> "Dict[str, str]":
    """``{"0001": glyph}`` — the rc409 shape, preserved for its four tests."""
    return {k: g for k, (g, _w) in _index_pairs().items()}


def _legend_glyphs() -> "set":
    """Every glyph the README legend DEFINES.

    Split on the ``·`` separator FIRST, then take each item's leading glyph.
    A naive scan over the whole line also harvests the separator itself
    (``·`` is U+00B7, non-ASCII), which would silently admit ``·`` as a legal
    status — a legend that accidentally defines its own punctuation.
    """
    return set(_legend_pairs())


# ── non-vacuity: the parsers must actually parse ──────────────────────


def test_the_parsers_can_still_see_something() -> None:
    """Pin the SHAPE. Every assertion below passes trivially on a parser that
    silently returns nothing — a renamed header, a reformatted table, a moved
    legend. This is the seam that must fail loud when it stops observing.

    rc415 widens it in the one direction that mattered: the rc409 version
    asserted a non-empty **glyph** on every surface, which left INV-3 and
    INV-4 free to be vacuously green on a parser that had stopped finding
    WORDS. A pair check whose word half is always empty compares ``"" == ""``
    on all thirteen and reports a clean corpus.
    """
    files = _file_pairs()
    index = _index_pairs()
    legend = _legend_pairs()
    ranks = _lifecycle_ranks()

    assert len(files) == _EXPECTED_ADR_COUNT, (
        f"parsed {len(files)} ADR status headers, expected "
        f"{_EXPECTED_ADR_COUNT}. Either an ADR was added/removed (update "
        f"_EXPECTED_ADR_COUNT) or the '**Status:**' header format changed and "
        f"this gate has stopped observing. Parsed: {sorted(files)}")
    assert len(index) == _EXPECTED_ADR_COUNT, (
        f"parsed {len(index)} README index rows, expected "
        f"{_EXPECTED_ADR_COUNT}. Parsed: {sorted(index)}")

    assert len(legend) >= 4, (
        f"the legend parsed to {len(legend)} pair(s); the documented "
        f"lifecycle has five states. Parsed: {legend}")
    assert len(ranks) >= 4, (
        f"the lifecycle parsed to {len(ranks)} ranked glyph(s). Parsed: "
        + ", ".join(f"{_fmt(g)}={r}" for g, r in sorted(ranks.items())))

    for surface, table in (("file", files), ("index", index)):
        blank = [f"ADR-{a} {_pair(g, w)}" for a, (g, w) in sorted(table.items())
                 if not g or not w]
        assert not blank, (
            f"{len(blank)} {surface} status(es) did not parse to a COMPLETE "
            f"(glyph, word) pair: " + ", ".join(blank)
            + "\n\nAn empty half makes INV-3 and INV-4 vacuous rather than "
              "green — they would compare '' against '' and pass.")

    words = {w.casefold() for _g, w in files.values()}
    assert len(words) >= 3, (
        f"only {len(words)} distinct status word(s) in use across 13 ADRs: "
        f"{sorted(words)}. A corpus that has collapsed to one or two words is "
        "either mid-migration or the parser has stopped distinguishing them.")


# ── the three rc409 coherence invariants ──────────────────────────────


def test_every_adr_file_has_an_index_row() -> None:
    """The two surfaces must cover the SAME set of ADRs.

    An ADR present as a file but missing from the index is invisible to anyone
    reading the directory's front door; the converse is a dangling link.
    """
    files = set(_file_statuses())
    index = set(_index_statuses())
    assert files == index, (
        "the ADR files and the README index cover different ADRs.\n"
        f"  file but NOT indexed: {sorted(files - index)}\n"
        f"  indexed but NO file:  {sorted(index - files)}")


def test_file_status_equals_index_status() -> None:
    """STRICT ZERO. The defect this file was written for.

    FAILED BEFORE rc409 on **ADR-0010** — the file said ``🟢`` while the index
    said ``🔄``. Two hand-written surfaces, no computation between them.
    """
    files = _file_statuses()
    index = _index_statuses()

    mismatches = [
        f"  ADR-{adr}: file header {_fmt(files[adr])} != "
        f"README index row {_fmt(index[adr])}"
        for adr in sorted(files)
        if adr in index and files[adr] != index[adr]
    ]
    assert not mismatches, (
        f"{len(mismatches)} ADR(s) disagree between their own header and the "
        "README index:\n" + "\n".join(mismatches)
        + "\n\nBoth surfaces are hand-written and nothing else syncs them. "
          "Fix whichever is stale — the ADR file is normally the authority, "
          "since that is where the decision is actually recorded.")


def test_every_status_glyph_in_use_is_defined_in_the_legend() -> None:
    """STRICT ZERO. An improvised glyph is a vocabulary gap, not a typo.

    FAILED BEFORE rc409: ``🟢`` (U+1F7E2) was used by ADR-0010 and ADR-0012 and
    defined by nothing — and the two used it to mean different things, which is
    exactly what an undefined symbol licenses. rc409 formalises it as the fifth
    lifecycle state, ``🟢 Implementing``.
    """
    legend = _legend_glyphs()
    used: Dict[str, List[str]] = {}
    for source, table in (("file", _file_statuses()), ("index", _index_statuses())):
        for adr, glyph in table.items():
            if glyph and glyph not in legend:
                used.setdefault(glyph, []).append(f"ADR-{adr} ({source})")

    assert not used, (
        "status glyph(s) in use but NOT defined in the README legend:\n"
        + "\n".join(f"  {_fmt(g)} used by {', '.join(sorted(w))}"
                    for g, w in sorted(used.items()))
        + f"\n\nLegend defines: {', '.join(_fmt(g) for g in sorted(legend))}"
        + "\n\nEither add the glyph to '**Status legend:**' in adr/README.md "
          "(and to the lifecycle line, so its position is defined too), or use "
          "one of the states that already exists. An undefined glyph is how two "
          "ADRs came to spell two different meanings the same way.")


# ── rc415: the pair invariants (INV-3 … INV-11) ───────────────────────


def test_file_status_word_equals_index_status_word() -> None:
    """INV-3. STRICT ZERO on the WORD, case recorded separately.

    The glyph halves can agree while the words do not, and until rc415 nothing
    looked. Live at rc414: ADR-0010 file ``IMPLEMENTING`` vs index
    ``Implementing``; ADR-0012 file ``ACCEPTED`` vs index ``Accepted``.

    A case-only divergence is cosmetic and a different-word divergence is a
    contradiction, so they are reported apart — but both fail. Two surfaces
    that disagree about capitalisation are two surfaces nobody is diffing, and
    that is the same condition the word divergence would arrive by.
    """
    files = _file_pairs()
    index = _index_pairs()

    hard: List[str] = []
    cosmetic: List[str] = []
    for adr in sorted(files):
        if adr not in index:
            continue
        fw, iw = files[adr][1], index[adr][1]
        if fw == iw:
            continue
        entry = f"  ADR-{adr}: file {fw!r} vs index {iw!r}"
        (cosmetic if fw.casefold() == iw.casefold() else hard).append(entry)

    assert not (hard or cosmetic), (
        f"{len(hard)} word disagreement(s) and {len(cosmetic)} case-only "
        "divergence(s) between an ADR header and its index row:\n"
        + "\n".join(hard + cosmetic)
        + "\n\nThe glyph halves may well agree — that is the point. The rc409 "
          "gate compared glyphs only and stayed green through both of these.")


def test_status_pairs_are_legal_legend_pairs() -> None:
    """INV-4. STRICT ZERO. **The invariant the rc409 gate could not hold.**

    A status is a ``(glyph, word)`` PAIR and the legend defines which pairs
    exist. Checked on BOTH surfaces **independently**, because the live rc414
    defect was the same illegal pair duplicated on both: ADR-0012 read
    ``(🟢, ACCEPTED)`` in its header and ``(🟢, Accepted)`` in the index, and a
    surface-vs-surface comparison of glyphs alone reported perfect agreement.
    🟢 is *Implementing*; ✅ is *Accepted*. They are distinct positions in the
    lifecycle and the pair cannot be legal.

    Word comparison casefolds — INV-3 owns the case question, and having two
    invariants fail on one defect for two different reasons makes neither
    message actionable.
    """
    legend = {g: w.casefold() for g, w in _legend_pairs().items()}
    bad: List[str] = []
    for surface, table in (("file header", _file_pairs()),
                           ("index row", _index_pairs())):
        for adr, (glyph, word) in sorted(table.items()):
            if not glyph or not word:
                continue
            defined = legend.get(glyph)
            if defined is None:
                continue          # owned by the legend-membership test above
            if word.casefold() != defined:
                bad.append(
                    f"  ADR-{adr} ({surface}) pair ({_fmt(glyph)}, {word!r}) "
                    f"is ILLEGAL — the legend at adr/README.md defines "
                    f"{_fmt(glyph)} as {defined!r}.")

    assert not bad, (
        f"{len(bad)} illegal status pair(s):\n" + "\n".join(bad)
        + "\n\nFix ONE half. Changing both to agree on a word the legend does "
          "not pair is not a fix — it is the rc414 state, where both surfaces "
          "carried the same illegal pair and the glyph-only gate stayed green."
        + "\n\nLegend pairs: "
        + " · ".join(f"{_fmt(g)} {w}" for g, w in sorted(_legend_pairs().items())))


def test_every_legend_glyph_has_a_lifecycle_rank() -> None:
    """INV-5. A defined state with no POSITION is half a definition.

    The legend says what a glyph means; the lifecycle line says where it sits.
    A glyph in one and not the other can be used but cannot be ordered — which
    is exactly the hole ``🟢`` fell through before rc409, and the reason the
    rc409 conventions text asks an author to add a new glyph *to both lines*.
    """
    legend = _legend_pairs()
    ranks = _lifecycle_ranks()
    missing = sorted(g for g in legend if g not in ranks)
    assert not missing, (
        "legend glyph(s) with no position on the 'Status lifecycle:' line: "
        + ", ".join(f"{_fmt(g)} ({legend[g]})" for g in missing)
        + "\n\nAdd it to the lifecycle line too. A state that cannot be "
          "ordered cannot be promoted or demoted, only asserted.")


def test_was_narrations_name_a_defined_earlier_state() -> None:
    """INV-6. A ``*(Was <glyph> <Word> …)*`` narration is a status CLAIM.

    Live at rc414: ADR-0010's header closes *"(Was 🟡 Proposed — target design,
    deferred behind the precision migration.)"*. **🟡 is defined nowhere in the
    tree** — not in the legend, not in the lifecycle. The gate that checks
    status glyphs never looked at narration, so an undefined glyph survived in
    the same line as a defined one.

    Two clauses: the narrated glyph must be RANKED, and its rank must be
    strictly BELOW the ADR's current rank. "Was Accepted, now Implementing" is
    a demotion and wants saying out loud, not burying in a parenthesis.
    """
    ranks = _lifecycle_ranks()
    files = _file_pairs()
    bad: List[str] = []

    for path in _adr_files():
        adr = adr_number(path)
        for line in text_lines(read_adr(path)):
            at = line.find("(Was ")
            if at < 0:
                continue
            glyph, word = status_pair(line[at + len("(Was "):])
            if not glyph:
                continue
            if glyph not in ranks:
                bad.append(
                    f"  ADR-{adr}: narrates '(Was {_fmt(glyph)} {word})' — a "
                    f"glyph the tree defines NOWHERE")
                continue
            now = files.get(adr, ("", ""))[0]
            if now in ranks and ranks[glyph] >= ranks[now]:
                bad.append(
                    f"  ADR-{adr}: narrates '(Was {_fmt(glyph)} {word})' at "
                    f"rank {ranks[glyph]}, but its current state {_fmt(now)} "
                    f"is rank {ranks[now]} — not a forward transition")

    assert not bad, (
        f"{len(bad)} status narration problem(s):\n" + "\n".join(bad)
        + "\n\nRanked glyphs: "
        + " · ".join(f"{_fmt(g)}={r}" for g, r in sorted(ranks.items(),
                                                        key=lambda kv: kv[1])))


def test_superseded_by_implies_the_superseded_glyph() -> None:
    """INV-7. ``**Superseded-by:** NNNN`` and a live status contradict.

    Zero hits today — every ``Superseded-by:`` in the corpus reads ``none``.
    It ships anyway because the failure it catches is silent by construction:
    the field is set by the *superseding* ADR's author, in a file they are not
    otherwise editing, and nothing else in the tree reads it.
    """
    legend = _legend_pairs()
    superseded = [g for g, w in legend.items() if w.casefold() == "superseded"]
    assert superseded, (
        "the legend defines no 'Superseded' state, so this invariant cannot "
        "be evaluated — that is a corpus change, not a pass.")
    mark = superseded[0]

    files = _file_pairs()
    bad: List[str] = []
    for path in _adr_files():
        adr = adr_number(path)
        for line in text_lines(read_adr(path)):
            if not line.startswith("**Superseded-by:**"):
                continue
            value = line[len("**Superseded-by:**"):].strip().rstrip(".").strip()
            if not value or value.casefold() == "none":
                break
            glyph = files.get(adr, ("", ""))[0]
            if glyph != mark:
                bad.append(
                    f"  ADR-{adr}: 'Superseded-by: {value}' but its status is "
                    f"{_fmt(glyph)}, not {_fmt(mark)}")
            break

    assert not bad, (
        "ADR(s) naming a superseding ADR while still carrying a live status:\n"
        + "\n".join(bad))


def test_accepted_adrs_declare_no_deliberately_open_clause() -> None:
    """INV-8. ✅ Accepted means STANDING POLICY, not "mostly in force".

    An ADR that says somewhere in its body *"OPEN and deliberately
    unimplemented"* is describing an execution arc that is still running. The
    README defines exactly that condition as 🟢 Implementing — *"direction
    accepted, execution arc OPEN"* — and reserves ✅ for a shape that has
    settled.

    Live at rc414 this corroborated INV-4 from a second, independent
    direction: ADR-0012 claimed ✅ **ACCEPTED** in its header while §3.4 read
    *"Status: OPEN and deliberately unimplemented in rc363"* (C6) — a clause
    that was still open **51 rcs later** with no instrument and no expiry.
    Two unrelated checks pointing at one ADR is what a real defect looks like.

    The phrase list is CLOSED and short on purpose. It is a natural-language
    heuristic, which is the kind of rule that rots silently; treat any addition
    to :data:`_DELIBERATELY_OPEN` as a design change, not a fix.
    """
    files = _file_pairs()
    bad: List[str] = []
    for path in _adr_files():
        adr = adr_number(path)
        glyph, word = files.get(adr, ("", ""))
        if word.casefold() != "accepted":
            continue
        for n, line in enumerate(text_lines(read_adr(path)), start=1):
            folded = line.casefold()
            for phrase in _DELIBERATELY_OPEN:
                if phrase in folded:
                    bad.append(f"  ADR-{adr} ({_fmt(glyph)} {word}) :{n} — "
                               f"{line.strip()[:110]}")
                    break

    assert not bad, (
        f"{len(bad)} clause(s) declared deliberately open inside an ADR whose "
        "status is Accepted:\n" + "\n".join(bad)
        + "\n\nEither the clause is closed (fix the body), or the ADR is still "
          "Implementing (fix the status). ✅ is standing policy; 🟢 is exactly "
          "'direction accepted, execution arc OPEN'.")


def test_index_links_resolve_to_the_row_they_label() -> None:
    """INV-9. The index is the front door; a link is how anyone arrives.

    Two clauses, and the second is the one a link-checker misses: the target
    must EXIST, **and** the number in its filename must equal the row's own
    ADR label. A row labelled ADR-0011 pointing at ``0012-….md`` resolves
    perfectly and sends every reader to the wrong decision.

    Zero hits today — and it was a latent hole, not a hypothetical one: the
    rc409 index parser captured the link target and never used it.
    """
    bad: List[str] = []
    for adr, cells in sorted(_index_rows().items()):
        cell = cells[0]
        lo, hi = cell.find("("), cell.rfind(")")
        target = cell[lo + 1:hi].strip() if 0 <= lo < hi else ""
        if not target:
            bad.append(f"  ADR-{adr}: index row carries no link target")
            continue
        resolved = resolve_path(f"adr/{target}")
        if resolved is None:
            bad.append(f"  ADR-{adr}: link target {target!r} resolves to no file")
        elif target[:4] != adr:
            bad.append(f"  ADR-{adr}: row is labelled {adr} but links to "
                       f"{target!r} (ADR-{target[:4]})")

    assert not bad, (
        f"{len(bad)} broken or mislabelled index link(s):\n" + "\n".join(bad))


def test_adr_numbers_are_contiguous() -> None:
    """INV-10. The population is an IDENTITY, not a count.

    ``_EXPECTED_ADR_COUNT`` pins how many, which is silent about which.
    Verified by injection: deleting ADR-0007 and appending an ADR-0014 leaves
    the count at 13, and the shipped rc409 gate re-pointed at that corpus
    reported ``4 passed in 0.04s``.

    Numbering is append-only and permanent per the README "Conventions", so
    the sequence is ``0001..N`` with no holes.
    """
    numbers = sorted(int(adr_number(p)) for p in _adr_files())
    expected = list(range(1, len(numbers) + 1))
    assert numbers == expected, (
        "the ADR numbering is not contiguous 0001..N.\n"
        f"  present: {numbers}\n"
        f"  expected: {expected}\n"
        f"  missing: {sorted(set(expected) - set(numbers))}\n"
        f"  unexpected: {sorted(set(numbers) - set(expected))}\n\n"
        "Numbers are permanent and append-only (adr/README.md 'Conventions'). "
        "A hole means an ADR was deleted rather than superseded.")


def test_index_date_matches_the_file_date() -> None:
    """INV-11. The index date and the file's own ``**Date:**`` must agree.

    Searched, not line-indexed — ADR-0012's ``**Date:**`` is on line 36, well
    below its header block, because the header carries a multi-paragraph
    acceptance narrative first. A head-only scan is wrong on 1 of 13.

    Compares the LEADING ISO date only: a file may legitimately annotate its
    own line (*"2026-07-30. **Amended 2026-07-30 (rc363)**"*), and the index
    column is a single date by construction.
    """
    index = {a: cells[-1].strip() for a, cells in _index_rows().items()}
    bad: List[str] = []
    for path in _adr_files():
        adr = adr_number(path)
        found = None
        for line in text_lines(read_adr(path)):
            if line.startswith("**Date:**"):
                found = line[len("**Date:**"):].strip()[:10]
                break
        if found is None:
            bad.append(f"  ADR-{adr}: no '**Date:**' line anywhere in the file")
        elif adr in index and found != index[adr]:
            bad.append(f"  ADR-{adr}: file date {found!r} != index date "
                       f"{index[adr]!r}")

    assert not bad, (
        f"{len(bad)} date disagreement(s) between an ADR and the index:\n"
        + "\n".join(bad))


# ── the near-miss, reported rather than hidden ────────────────────────


def test_whole_line_scan_is_reported_not_asserted() -> None:
    """The rejected whole-line check, PRINTED every run. Never a failure.

    Class-D ``match`` over the whole status line is a 100% false-positive
    classifier on this corpus — ADR-0001's header ends *"…it is what gates
    promotion to ✅ Accepted"*, a second glyph+word pair in narrative position.
    The shipped invariants scope to the glyph+word PREFIX, which agrees 26/26.

    Printing the whole-line count is the honest form: the near-miss stays
    visible, so if it ever drops to zero someone can decide whether the
    stricter rule has become shippable — rather than the rule being silently
    re-proposed every few rcs because nobody recorded why it was dropped.
    """
    legend = _legend_pairs()
    extra = 0
    for path in _adr_files():
        for line in text_lines(read_adr(path)):
            if not line.startswith("**Status:**"):
                continue
            body = line[len("**Status:**"):]
            prefix_glyph = status_pair(body)[0]
            for glyph in legend:
                first = body.find(glyph)
                if first < 0:
                    continue
                if body.find(glyph, first + len(glyph)) >= 0 or glyph != prefix_glyph:
                    extra += 1
            break
    print(f"\n[rc415] whole-line status scan would report {extra} extra "
          f"glyph occurrence(s) across {_EXPECTED_ADR_COUNT} headers — "
          f"all narrative, all false positives at the prefix rule. "
          f"NOT asserted; see this module's docstring.")
    assert extra >= 0
