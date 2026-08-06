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

WHY THE PARSER IS A SEARCH AND NOT A LINE INDEX
===============================================
``0008``'s ``**Status:**`` is on line **5**, not line 3 — a renumbering banner
occupies :3. A naive line-3 parser is wrong on 1 of 12 and would have to be
"fixed" by exempting the one file it cannot read. Search for the FIRST status
line instead; that is correct for all twelve without an exemption list.

``0001-profile-pattern.schema.json`` is a COMPANION ARTIFACT sharing ADR-0001's
number (README "Conventions"), not a second ADR — hence the ``*.md`` glob, which
is what keeps it out of the population regardless of how many ADRs exist.

ENCODING
========
Every read is explicit ``utf-8``. Status glyphs are non-ASCII, and on Windows
the default ``cp1252`` raises ``UnicodeEncodeError`` on ``⏳``. Failure messages
render glyphs as ``U+XXXX`` escapes rather than raw characters so a RED result
is readable on every platform — a gate whose failure output itself crashes is a
gate nobody can act on.
"""

from __future__ import annotations

import re
from pathlib import Path

_SR_ROOT = Path(__file__).resolve().parents[2]      # docs/srmech
_ADR_DIR = _SR_ROOT / "adr"
_README = _ADR_DIR / "README.md"

#: The ADR count is pinned so a DELETED or unparseable ADR fails loudly instead
#: of shrinking the population every assertion below iterates over. A gate that
#: silently checks fewer things is the false-green shape this suite exists to
#: stop.
_EXPECTED_ADR_COUNT = 13

#: ``**Status:**`` then the rest of the line. Searched, never line-indexed.
_STATUS_LINE = re.compile(r"^\*\*Status:\*\*\s*(.+)$")

#: A README index row: ``| [ADR-0001](0001-....md) | Title | GLYPH Word | date |``
_INDEX_ROW = re.compile(r"^\|\s*\[ADR-(\d{4})\]\([^)]*\)\s*\|")

#: The legend line, e.g. ``**Status legend:** ✅ Accepted · 🔄 Proposed · ...``
_LEGEND_LINE = re.compile(r"^\*\*Status legend:\*\*\s*(.+)$")

#: A status glyph: a run of non-ASCII, non-space characters. Matching a RUN
#: (not one character) is load-bearing — several of these emoji carry a
#: variation selector (U+FE0F) as a second codepoint, and slicing ``[0]`` would
#: silently compare half a glyph against a whole one and report a mismatch that
#: is really an encoding artefact.
_GLYPH = re.compile(r"[^\x00-\x7F]+")


def _fmt(glyph: str) -> str:
    """Render a glyph as ``U+XXXX`` codepoints — ASCII-safe on every console."""
    return "+".join(f"U+{ord(c):04X}" for c in glyph) if glyph else "<none>"


def _leading_glyph(text: str) -> str:
    """The status glyph at the START of ``text``, or ``""`` when there is none."""
    m = _GLYPH.match(text.strip())
    return m.group(0) if m else ""


def _adr_files() -> "list[Path]":
    """The twelve ADR markdown files, README excluded, in numeric order."""
    return sorted(p for p in _ADR_DIR.glob("[0-9]*.md"))


def _file_statuses() -> "dict[str, str]":
    """``{"0001": glyph}`` parsed from each ADR's own ``**Status:**`` header."""
    out: dict[str, str] = {}
    for path in _adr_files():
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            m = _STATUS_LINE.match(line)
            if m:
                out[path.name[:4]] = _leading_glyph(m.group(1))
                break
        else:                                            # pragma: no cover
            raise AssertionError(
                f"{path.name}: no '**Status:**' line anywhere in the file")
    return out


def _index_statuses() -> "dict[str, str]":
    """``{"0001": glyph}`` parsed from the ``adr/README.md`` index table."""
    out: dict[str, str] = {}
    for line in _README.read_text(encoding="utf-8").splitlines():
        m = _INDEX_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells: ['', '[ADR-0001](...)', 'Title', 'GLYPH Word', 'date', '']
        assert len(cells) >= 5, f"malformed index row: {line[:80]!r}"
        out[m.group(1)] = _leading_glyph(cells[3])
    return out


def _legend_glyphs() -> "set[str]":
    """Every glyph the README legend DEFINES.

    Split on the ``·`` separator FIRST, then take each item's LEADING glyph.
    A naive ``findall`` over the whole line also harvests the separator itself
    (``·`` is U+00B7, non-ASCII), which would silently admit ``·`` as a legal
    status — a legend that accidentally defines its own punctuation.
    """
    for line in _README.read_text(encoding="utf-8").splitlines():
        m = _LEGEND_LINE.match(line)
        if m:
            return {
                g for g in (_leading_glyph(item)
                            for item in m.group(1).split("·"))
                if g
            }
    raise AssertionError(                                # pragma: no cover
        "no '**Status legend:**' line in adr/README.md")


# ── non-vacuity: the parsers must actually parse ──────────────────────


def test_the_parsers_can_still_see_something() -> None:
    """Pin the SHAPE. Every assertion below passes trivially on a parser that
    silently returns nothing — a renamed header, a reformatted table, a moved
    legend. This is the seam that must fail loud when it stops observing.
    """
    files = _file_statuses()
    index = _index_statuses()
    legend = _legend_glyphs()

    assert len(files) == _EXPECTED_ADR_COUNT, (
        f"parsed {len(files)} ADR status headers, expected "
        f"{_EXPECTED_ADR_COUNT}. Either an ADR was added/removed (update "
        f"_EXPECTED_ADR_COUNT) or the '**Status:**' header format changed and "
        f"this gate has stopped observing. Parsed: {sorted(files)}")
    assert len(index) == _EXPECTED_ADR_COUNT, (
        f"parsed {len(index)} README index rows, expected "
        f"{_EXPECTED_ADR_COUNT}. Parsed: {sorted(index)}")
    assert legend, "the legend parsed to an EMPTY glyph set"
    assert all(files.values()), (
        "an ADR status header carried NO glyph: "
        + ", ".join(f"{k}={_fmt(v)}" for k, v in sorted(files.items()) if not v))


# ── the three coherence invariants ────────────────────────────────────


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
    used: dict[str, list[str]] = {}
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
