"""v0.9.0rc449 (`#T1158`) — the last two UNGATED ABI CURRENCY surfaces.

Every other ABI surface is pinned. ``c/include/srmech.h`` is the macro SSoT;
``python/srmech/_native/__init__.py`` is pinned against it by the ctypes shim's
own load check; twenty-two test files pin the literal; ``python/README.md`` has
had :mod:`test_readme_currency_rc419` since rc419; and the research notebook's
``Live at rcNNN`` stamp has had :mod:`test_notebook_currency_rc420` since rc420.

TWO were left over, and both are PROSE a reader is entitled to read as CURRENT:
(``python/CHANGELOG.md`` and ``notes/*.md`` also state ABI numbers, but each is
a DATED record of the release it describes — historical by construction, and
correctly not gated.)

  1. ``docs/srmech/CLAUDE.md`` "ABI compatibility" — the **narrative SSoT**,
     the section every other ABI note in the tree cites as authoritative.
  2. ``docs/srmech/c/README.md`` "### ABI".

WHAT MEASURED IT. At rc449 head, before this gate, both said **17** while the
macro said **18** — one full release stale, and stale in the file that other
files name as the place to look.

⚠️ THE ARGUMENT FOR GATING IS THE FILES' OWN HISTORY, NOT A PREFERENCE.
CLAUDE.md's parenthetical enumerates its own lags: it "said 12 until rc420, 13
until rc425, 14 until rc438, 15 until rc439 and 16 until rc442 — one bump behind
on each occasion". rc447's bump made it a SIXTH, and rc448 shipped over it without
repair — so by rc449 that one lag had left the line TWO bumps behind, the first
time it was ever more than one. c/README.md is
worse and says so: it read **3** from the v0.5.0 era until rc442 — fourteen bumps
stale — under a note reading *"No gate covers c/README.md at all, which is
exactly why it drifted the furthest of any ABI statement in the tree."* It then
drifted again five rcs later. A file that documents why it drifts, and drifts
again, is the textbook *"ungated surfaces trickle; gated ones race to 100%"*.

WHAT THIS GATE IS NOT. It does not read the prose for meaning. It asserts one
decidable thing per file — the ABI integer these sentences state equals the
macro — because that is the claim that kept going wrong. The surrounding
rationale is deliberately unconstrained.
"""

from __future__ import annotations

import re
from pathlib import Path

_HERE = Path(__file__).resolve()
_SRMECH_ROOT = _HERE.parents[2]          # docs/srmech/
_HEADER = _SRMECH_ROOT / "c" / "include" / "srmech.h"
_CLAUDE_MD = _SRMECH_ROOT / "CLAUDE.md"
_C_README = _SRMECH_ROOT / "c" / "README.md"

#: "C ABI version is currently **19** (`SRMECH_ABI_VERSION = 19` in"
_CLAUDE_ABI = re.compile(
    r"C ABI version is currently \*\*(\d+)\*\*\s*\(`SRMECH_ABI_VERSION = (\d+)`")

#: "C ABI version is **19** (`SRMECH_ABI_VERSION 19` in"
_C_README_ABI = re.compile(
    r"C ABI version is \*\*(\d+)\*\*\s*\(`SRMECH_ABI_VERSION (\d+)`")

#: The SECOND cardinal in the SAME CLAUDE.md sentence — "; `EXPECTED_ABI_VERSION
#: = 26` in `python/srmech/_native/__init__.py`". rc473 (`#T1188`) added this,
#: because rc473 itself broke it: the ABI sweep moved the two cardinals
#: ``_CLAUDE_ABI`` covers and left this third one on 25, producing a sentence
#: that read "currently **26** (`SRMECH_ABI_VERSION = 26` …; `EXPECTED_ABI_VERSION
#: = 25` …)". The gate's own closing paragraph said it "asserts one decidable
#: thing per file"; this sentence carries TWO decidable things, and the second
#: one is exactly as decidable as the first. The line break between the clauses
#: is why ``\s*`` rather than a space.
_CLAUDE_EXPECTED_ABI = re.compile(r"`EXPECTED_ABI_VERSION = (\d+)`")


def _macro_abi() -> int:
    """SRMECH_ABI_VERSION as the C header defines it — the SSoT.

    Read from the header text rather than from ``_native.EXPECTED_ABI_VERSION``
    on purpose: the Python constant is the OTHER half of the pair these prose
    lines describe, and checking prose against it would leave the pair free to
    drift together. The macro is the thing both sides mirror.
    """
    m = re.search(r"^#define SRMECH_ABI_VERSION (\d+)",
                  _HEADER.read_text(encoding="utf-8"), re.M)
    assert m, f"no #define SRMECH_ABI_VERSION in {_HEADER}"
    return int(m.group(1))


def test_claude_md_abi_narrative_matches_the_macro() -> None:
    """The NARRATIVE SSoT states the live ABI.

    This is the file other ABI notes cite. A wrong number here is not a stale
    citation; it is the reference answer being wrong.
    """
    macro = _macro_abi()
    m = _CLAUDE_ABI.search(_CLAUDE_MD.read_text(encoding="utf-8"))
    assert m, (
        f"no 'C ABI version is currently **N** (`SRMECH_ABI_VERSION = N`' "
        f"sentence found in {_CLAUDE_MD}. If the section was reworded, update "
        f"this regex deliberately — do not delete the gate.")
    assert int(m.group(1)) == int(m.group(2)) == macro, (
        f"{_CLAUDE_MD} says ABI {m.group(1)} (macro-quote {m.group(2)}); "
        f"c/include/srmech.h says {macro}. This line has now been stale on "
        f"SIX consecutive bumps, the last of them for two releases running; that "
        f"is what this gate exists to stop.")


def test_claude_md_expected_abi_cardinal_matches_the_shim() -> None:
    """The SECOND cardinal in the same sentence — the one rc473 broke.

    ``_CLAUDE_ABI`` stops at the ``;``. Everything after it was unconstrained,
    and rc473's own ABI sweep moved the first two cardinals to 26 and left this
    one on 25 — so the shipped sentence read *"C ABI version is currently
    **26** (`SRMECH_ABI_VERSION = 26` in `c/include/srmech.h`;
    `EXPECTED_ABI_VERSION = 25` in `python/srmech/_native/__init__.py`)"*. At
    ``b398b8c46`` all three read 25 and all three were correct, so this is not
    an inherited lag; it was minted by the sweep that fixed the other two.

    Asserted against the SHIM's own constant rather than against the macro,
    because that is what the sentence claims: the sentence names
    ``python/srmech/_native/__init__.py`` by path. Checking it against the
    macro would pass in the one state that matters least (macro and shim
    already agree) and say nothing about the state the sentence describes.

    Every ``EXPECTED_ABI_VERSION = N`` in the file is checked, not just the
    first. There is one today; a second stale copy is exactly the shape this
    gate keeps meeting.
    """
    import re as _re
    from srmech import _native

    text = _CLAUDE_MD.read_text(encoding="utf-8")
    found = [int(n) for n in _CLAUDE_EXPECTED_ABI.findall(text)]
    assert found, (
        f"no '`EXPECTED_ABI_VERSION = N`' cardinal found in {_CLAUDE_MD}. The "
        f"ABI sentence names that constant by path; if the section was "
        f"reworded, update this regex deliberately — do not delete the gate. "
        f"An empty scan is not a clean file.")
    live = int(_native.EXPECTED_ABI_VERSION)
    wrong = sorted({n for n in found if n != live})
    assert not wrong, (
        f"{_CLAUDE_MD} states EXPECTED_ABI_VERSION = {wrong} in "
        f"{len(found)} cardinal(s); python/srmech/_native/__init__.py says "
        f"{live}. rc473 shipped exactly this — the same sentence carrying a "
        f"correct **{_macro_abi()}** and a stale {wrong[0] if wrong else '?'} "
        f"— which is why this assertion exists.")
    # Non-vacuity: the sentence this gate reads must be the ABI sentence, not
    # some other line that happens to spell the constant.
    assert _re.search(r"C ABI version is currently \*\*\d+\*\*", text), (
        "the 'C ABI version is currently **N**' sentence is gone from "
        f"{_CLAUDE_MD}; this gate would then be reading a cardinal out of "
        "unrelated prose.")


def test_c_readme_abi_matches_the_macro() -> None:
    """``c/README.md`` states the live ABI — the surface that drifted furthest."""
    macro = _macro_abi()
    m = _C_README_ABI.search(_C_README.read_text(encoding="utf-8"))
    assert m, (
        f"no 'C ABI version is **N** (`SRMECH_ABI_VERSION N`' sentence found "
        f"in {_C_README}. If the section was reworded, update this regex "
        f"deliberately — do not delete the gate.")
    assert int(m.group(1)) == int(m.group(2)) == macro, (
        f"{_C_README} says ABI {m.group(1)} (macro-quote {m.group(2)}); "
        f"c/include/srmech.h says {macro}. This file read ABI 3 for fourteen "
        f"bumps, was repaired at rc442, and was stale again by rc447.")


def test_the_gate_would_have_fired_on_the_rc448_text() -> None:
    """RETRO-CHECK. A gate that would not have caught the defect that motivated
    it is not the gate.

    The rc448-head strings are reproduced VERBATIM rather than described, and
    each is run through the SHIPPED regex, so this fails if either predicate is
    ever loosened past the point where the original staleness would slip by.
    """
    rc448_claude = ("C ABI version is currently **17** "
                    "(`SRMECH_ABI_VERSION = 17` in\n`c/include/srmech.h`;")
    rc448_c_readme = ("C ABI version is **17** (`SRMECH_ABI_VERSION 17` in\n"
                      "`c/include/srmech.h`).")

    m = _CLAUDE_ABI.search(rc448_claude)
    assert m and int(m.group(1)) == 17, "the CLAUDE.md ABI regex stopped matching"
    assert int(m.group(1)) != _macro_abi(), (
        "the rc448 CLAUDE.md text now equals the live macro, so this "
        "retro-check no longer demonstrates anything — re-anchor it.")

    m = _C_README_ABI.search(rc448_c_readme)
    assert m and int(m.group(1)) == 17, "the c/README.md ABI regex stopped matching"
    assert int(m.group(1)) != _macro_abi(), (
        "the rc448 c/README.md text now equals the live macro, so this "
        "retro-check no longer demonstrates anything — re-anchor it.")
