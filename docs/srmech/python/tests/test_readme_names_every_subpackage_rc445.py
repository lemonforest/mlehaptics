"""rc445 (`#T1153`) — the README's two-tier map must cover ``srmech.__path__``.

DECIDABLE, AND ONLY DECIDABLE. This compares a SET of subpackage names against
the shipped README. It makes NO claim that any description is true — that is not
decidable and nothing here attempts it. Naming a package is not describing it
correctly, and this gate deliberately cannot tell the difference; the value it
adds is that a whole subpackage can no longer be silently absent.

WHAT IT WAS WRITTEN FOR. At rc444 the README opened *"a research package shipping
six load-bearing surfaces"* and the six named SEVEN of eighteen top-level
subpackages. ``srmech.apokatastasis`` — ADR-0010's own "LARGEST" reclassified
block, 25 modules and 28 registered ops — had ZERO occurrences in the 709-line
file, as did ``chemistry``, ``rbs_lm``, ``llm`` and the dotted ``srmech.cli``.
The count had been maintained exactly once (five -> six) while the package gained
ten more subpackages, which is what a hand-maintained cardinal does.

This README IS the PyPI long-description (``tests/test_pypi_readme_changelog.py``
pins it as fragment 0), so line 3 is the first sentence a stranger reads on the
project page.

THE BACKTICKED FORM IS LOAD-BEARING, per ``test_init_docstring_surfaces_rc407``:
a bare ``name in text`` check passes trivially on substrings (``math`` matches
inside "mathematics"), so the pattern requires the dotted, backticked spelling.

⚠️ PRIVATE NAMES ARE FILTERED, NOT ALLOWLISTED. ``srmech.__path__`` includes
``_native``. Scoping the gate to the raw walk would compel documenting every
future PRIVATE subpackage in the PyPI front matter, which is a scope decision a
hygiene gate has no business forcing. Only non-underscore names are REQUIRED;
``_native`` is documented anyway (ADR-0010's fifth bucket) and the roster below
records that as a deliberate inclusion rather than an obligation.
"""

from __future__ import annotations

import pkgutil
import re
from pathlib import Path

import srmech

_README = Path(__file__).resolve().parents[1] / "README.md"
_BEGIN, _END = "<!-- SURFACES:BEGIN -->", "<!-- SURFACES:END -->"

#: name -> WHY it is infrastructure and not a headline surface.
#: EMPTY at rc445: the two-tier map names every public subpackage. An entry here
#: is an admission, not a convenience — the roster test below refuses a
#: placeholder reason and refuses to excuse a package that IS in the map.
_ALLOWLIST: "dict[str, str]" = {}

#: Private subpackages the map documents anyway. NOT required by the gate; listed
#: so that removing one from the README is a deliberate edit rather than a silent
#: regression flagged nowhere.
_PRIVATE_DOCUMENTED = ("_native",)


def _subpackages() -> "list[str]":
    """Every top-level subpackage, private ones included."""
    return sorted(m.name for m in pkgutil.iter_modules(srmech.__path__) if m.ispkg)


def _public_subpackages() -> "list[str]":
    return [n for n in _subpackages() if not n.startswith("_")]


def _map_text() -> str:
    text = _README.read_text(encoding="utf-8")
    assert _BEGIN in text and _END in text, (
        "the SURFACES fences are gone from python/README.md — the two-tier map "
        "this gate observes has been rephrased away. Re-point the fences; do "
        "NOT delete the assertion."
    )
    return text[text.index(_BEGIN):text.index(_END)]


def _named(block: str, name: str) -> bool:
    return bool(re.search(rf"`srmech\.{re.escape(name)}\b", block))


def test_every_public_subpackage_is_named_in_the_map_or_excused_with_a_reason():
    block = _map_text()
    missing = [n for n in _public_subpackages()
               if not _named(block, n) and n not in _ALLOWLIST]
    assert missing == [], (
        f"top-level subpackages absent from the README's two-tier map and "
        f"carrying no allowlist reason: {missing}"
    )


def test_the_allowlist_cannot_rot_and_cannot_be_a_dumping_ground():
    live, block = set(_subpackages()), _map_text()
    for name, reason in _ALLOWLIST.items():
        assert name in live, f"allowlist excuses {name!r}, which no longer exists"
        assert not _named(block, name), (
            f"{name!r} is BOTH named in the map and excused; drop the excuse so "
            f"the gate keeps covering it"
        )
        assert len(reason) >= 40 and not re.search(
            r"todo|tbd|later|wip|placeholder|n/?a", reason, re.I
        ), f"the allowlist reason for {name!r} is not a reason: {reason!r}"


def test_the_documented_private_roster_still_holds():
    """A private package the map DOES document must stay documented.

    Not an obligation to document private packages — an obligation not to drop
    one by accident once it is in.
    """
    live, block = set(_subpackages()), _map_text()
    for name in _PRIVATE_DOCUMENTED:
        assert name in live, f"{name!r} is no longer a subpackage; update the roster"
        assert _named(block, name), (
            f"`srmech.{name}` was documented in the two-tier map and has been "
            f"dropped. Restore it, or remove it from _PRIVATE_DOCUMENTED "
            f"deliberately."
        )


def test_the_gate_would_have_fired_on_the_rc444_text():
    """The verbatim rc444 header names none of the five holes.

    A gate that passes on the text it was written for is not the gate.
    """
    rc444 = ("`srmech` (Stored-Relationship Mechanism) is a research package "
             "shipping six load-bearing surfaces:")
    for name in ("apokatastasis", "chemistry", "rbs_lm", "llm", "cli"):
        assert not _named(rc444, name), name


def test_the_backticked_form_is_required_not_a_bare_substring():
    """The pattern must not be satisfiable by an incidental prose word.

    ``test_init_docstring_surfaces_rc407`` documents this trap; re-proving it
    here keeps a future "simplification" of `_named` from going vacuous.
    """
    assert not _named("srmech does a lot of mathematics", "math")
    assert _named("- **`srmech.math`** - the vocabulary", "math")
