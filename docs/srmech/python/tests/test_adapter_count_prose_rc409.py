"""rc409 (`#T1080`) — the adapter cardinal, on THREE surfaces, tied to `ADAPTERS`.

`len(ADAPTERS) == 7`. Three hand-written surfaces said **six**, and one of them
renders on the public PyPI project page:

  1. `srmech/amsc/adapters/__init__.py:3`  — "Six adapter categories …"
  2. the bullet list right under it        — six bullets, seven adapters
  3. `python/README.md:506`                — "Six adapters cover the realistic
     source space", above a six-row table. Both pyprojects build the PyPI
     long-description from this file via the `fancy-pypi-readme` hook, so this
     copy ships to every visitor of the project page.

`substrate_parameterization` is the adapter none of the three mention.

THE GENERATIVE RULE — WHY THIS ONE ROTTED AND ITS NEIGHBOUR DID NOT
==================================================================
Four lines below the defect, `adapters/__init__.py:29` reads *"Notebook §18.3 —
five-adapter shared core spec."* That says **five**, and it is **CORRECT** —
`ephemerides_spectral_research_notebook.md:2646` says *"(small shared core, ~5
types covering the realistic source space)"* and tables exactly five. It is an
ATTRIBUTED CITATION to a dated source, and it is **deliberately not touched by
this gate**: "correct" for a citation means *faithful to what was cited*, not
*equal to today's count*. Editing it to 7 would inject a false citation — an MPM
violation, and a worse defect than the one being fixed.

Now read `:3`'s wording: *"cover the realistic source space"* is §18.3's own
phrase with the attribution **stripped**. The attributed copy stayed correct
across two adapter additions; the unattributed paraphrase drifted 5 → 6 and then
went stale at 7. **A cited number is anchored; the same number with its citation
removed rots.** That is why the gate keys on `len(ADAPTERS)` — a live value —
rather than on a literal, and why it must never be pointed at line 29.
"""

from __future__ import annotations

import re
from pathlib import Path

from srmech.amsc import adapters as _adapters
from srmech.amsc.adapters import ADAPTERS

_PY_ROOT = Path(__file__).resolve().parents[1]
_README = _PY_ROOT / "README.md"

_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

#: "Seven adapter categories cover ..." — the docstring's own cardinal.
_DOCSTRING_CARDINAL = re.compile(
    r"\b([A-Za-z]+)\s+adapter categories\b", re.IGNORECASE)

#: "Seven adapters cover the realistic source space:" — the README's.
_README_CARDINAL = re.compile(
    r"\b([A-Za-z]+)\s+adapters\s+cover\b", re.IGNORECASE)


def _word_to_int(word: str) -> int:
    key = word.lower()
    assert key in _WORDS, (
        f"cardinal {word!r} is not a number word this gate knows; add it to "
        f"_WORDS rather than rephrasing the prose to dodge the check.")
    return _WORDS[key]


def test_docstring_cardinal_matches_ADAPTERS() -> None:
    """The module docstring's spelled-out count == the live registry size."""
    doc = _adapters.__doc__ or ""
    m = _DOCSTRING_CARDINAL.search(doc)
    assert m, ("no 'N adapter categories' cardinal found in "
               "srmech/amsc/adapters/__init__.py's docstring - the sentence was "
               "rephrased and this gate has stopped observing.")
    assert _word_to_int(m.group(1)) == len(ADAPTERS), (
        f"adapters/__init__.py docstring says {m.group(1)!r} adapter "
        f"categories; len(ADAPTERS) == {len(ADAPTERS)} "
        f"({', '.join(sorted(ADAPTERS))}).")


def test_docstring_bullet_count_matches_ADAPTERS() -> None:
    """Every adapter gets a bullet.

    The cardinal and the bullets are INDEPENDENT surfaces: rc409 found the word
    "Six" above exactly six bullets and seven adapters, so fixing only the
    numeral would have left the list still missing an entry. Naming each adapter
    is what makes the omission visible.
    """
    doc = _adapters.__doc__ or ""
    named = {
        m.group(1)
        for line in doc.splitlines()
        if (m := re.match(r"\s*\*\s+``([a-z_]+)``", line))
    }
    assert named == set(ADAPTERS), (
        "the adapters docstring bullet list and ADAPTERS disagree.\n"
        f"  bulleted but NOT registered: {sorted(named - set(ADAPTERS))}\n"
        f"  registered but NO bullet:    {sorted(set(ADAPTERS) - named)}")


def test_readme_cardinal_and_table_match_ADAPTERS() -> None:
    """The PyPI long-description surface. This one is user-visible.

    Both pyprojects slice README.md into the published long-description, so a
    wrong count here is on the project page, not just in a docstring.
    """
    text = _README.read_text(encoding="utf-8")
    m = _README_CARDINAL.search(text)
    assert m, ("no 'N adapters cover' cardinal in python/README.md - the "
               "sentence was rephrased and this gate has stopped observing.")
    assert _word_to_int(m.group(1)) == len(ADAPTERS), (
        f"python/README.md says {m.group(1)!r} adapters; len(ADAPTERS) == "
        f"{len(ADAPTERS)}. This text ships as the PyPI long-description.")

    # The table under that sentence names one adapter per row in `backticks`.
    tail = text[m.end():]
    rows = {
        r.group(1)
        for line in tail.splitlines()[:40]
        if (r := re.match(r"\s*\|\s*`([a-z_]+)`\s*\|", line))
    }
    assert rows == set(ADAPTERS), (
        "the README adapter TABLE and ADAPTERS disagree.\n"
        f"  tabled but NOT registered: {sorted(rows - set(ADAPTERS))}\n"
        f"  registered but NO row:     {sorted(set(ADAPTERS) - rows)}")


def test_the_attributed_citation_is_left_alone() -> None:
    """REGRESSION GUARD, and the point of the whole file.

    `:29` cites Notebook §18.3 as a FIVE-adapter spec. That is accurate to the
    cited source and must survive every future adapter addition. A well-meaning
    sweep that "fixes" all the fives to sevens would fabricate a citation, which
    is a worse defect than the stale cardinal this file exists to catch.
    """
    doc = _adapters.__doc__ or ""
    assert "five-adapter shared core spec" in doc, (
        "the attributed Notebook §18.3 citation ('five-adapter shared core "
        "spec') was edited or removed. It is CORRECT at five - the notebook "
        "says '~5 types' and tables exactly five. Restore it: a citation is "
        "faithful to its source, not to today's count.")
