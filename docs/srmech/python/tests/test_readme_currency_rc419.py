"""rc419 (`#T1110`) — THE README CURRENCY GATE, tied to LIVE values.

WHY THIS EXISTS — two measured falsehoods, on the PyPI project page
==================================================================
``python/README.md`` is the PyPI long-description: both pyprojects slice it into
the published metadata, so every sentence here is shipped text a stranger reads
before they read any code. Two of its numbers were wrong at rc418:

1. line 16 — *"in-C tool dispatch over the **543-entry** tool registry"*. The
   live registry held **560**. Stale by 17 ops, i.e. by seventeen separate rcs
   each of which registered something and left this sentence alone.
2. line 142 — *"**ABI 10** at this release"*, plus the worked ``native_status()``
   block below it printing ``'abi_version': 10, 'expected_abi': 10,
   'native_version': '0.9.0rc389'``. The live ABI was **13**. The file
   CONTRADICTED ITSELF: line 450 of the same README already said
   ``SRMECH_ABI_VERSION`` moves *"12 → 13"*.

Neither is a typo. Both are the shape ``test_adapter_count_prose_rc409``
diagnosed and named: **a number written as a literal, with no tie to the value
it describes, rots** — while the same number written as a live lookup cannot.
That file fixed the adapter cardinal the same way and for the same reason; this
one closes the two remaining literals in the same document.

WHAT IT KEYS ON, AND WHY THAT IS THE WHOLE POINT
================================================
Nothing here compares one literal against another literal. Every assertion
resolves the LIVE value — ``len(get_tool_schema().by_owner("srmech"))`` and
``srmech._native.EXPECTED_ABI_VERSION`` — and reads the README's claim out of
the shipped file. So the gate cannot itself go stale: an rc that registers an op
or bumps the ABI fails HERE, at the moment the prose stops being true, rather
than seventeen rcs later when somebody happens to read it.

THE INTERNAL-CONSISTENCY CHECK IS SEPARATE ON PURPOSE
=====================================================
:func:`test_readme_does_not_contradict_itself_about_abi` asserts the narrative
"N → M" bump sentence lands on the SAME ABI the header claims. That is a
different failure from either number being stale: at rc418 the two sentences
disagreed with each other, which means a reader could have caught the defect
from the README alone with no access to the source. A gate that only checked
each number against the source would have reported one failure where there were
two independent ones.

DELIBERATELY NOT CHECKED: the ``native_version`` string in the worked block is
asserted to match ``srmech.__version__``, but the surrounding *narrative* rc
numbers (``v0.9.0rc381`` moved qm, ``rc414`` did X) are historical CITATIONS and
are left alone — exactly the ``five-adapter shared core spec`` carve-out
``test_adapter_count_prose_rc409`` documents. Editing a dated claim to today's
value would fabricate history, which is a worse defect than the stale cardinal.
"""

from __future__ import annotations

import re
from pathlib import Path

import srmech
from srmech._native import EXPECTED_ABI_VERSION
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

_README = Path(__file__).resolve().parents[1] / "README.md"

#: "... over the 569-entry tool registry ..."
_REGISTRY_CARDINAL = re.compile(r"\b(\d+)-entry tool registry\b")

#: "... its ABI matched (**ABI 13** at this release ..."
_ABI_HEADER = re.compile(r"\*\*ABI (\d+)\*\*\s+at this release")

#: "`SRMECH_ABI_VERSION` moves **12 → 13**" — the narrative bump sentence.
_ABI_BUMP = re.compile(r"SRMECH_ABI_VERSION`? moves \*\*(\d+)\s*(?:→|->)\s*(\d+)\*\*")

#: the worked native_status() block's own printed values
_WORKED_ABI = re.compile(r"'abi_version':\s*(\d+),")
_WORKED_EXPECTED_ABI = re.compile(r"'expected_abi':\s*(\d+),")
_WORKED_NATIVE_VERSION = re.compile(r"'native_version':\s*'([^']+)'")


def _text() -> str:
    return _README.read_text(encoding="utf-8")


def _live_op_count() -> int:
    """srmech-OWNED rows, the same basis ``registered_op_names.txt`` uses.

    ``get_tool_schema().tools`` is the unfiltered view and can carry a
    third party's profile rows; keying on that would make this gate fail for a
    reason that has nothing to do with the prose.
    """
    warmup_all()
    return len(get_tool_schema().by_owner("srmech"))


def test_readme_registry_cardinal_matches_the_live_registry() -> None:
    """The shipped PyPI sentence's op count == the live registry size."""
    m = _REGISTRY_CARDINAL.search(_text())
    assert m, ("no 'N-entry tool registry' cardinal found in python/README.md — "
               "the sentence was rephrased and this gate has stopped observing. "
               "Re-point the regex; do not delete the assertion.")
    assert int(m.group(1)) == _live_op_count(), (
        f"python/README.md advertises a {m.group(1)}-entry tool registry; the "
        f"live registry holds {_live_op_count()} srmech-owned ops. This text "
        f"ships as the PyPI long-description — it was stale by 17 at rc418, "
        f"which is how this gate came to exist.")


def test_readme_abi_header_matches_the_live_abi() -> None:
    """The '**ABI N** at this release' claim == ``EXPECTED_ABI_VERSION``."""
    m = _ABI_HEADER.search(_text())
    assert m, ("no '**ABI N** at this release' claim found in python/README.md "
               "— the sentence was rephrased and this gate has stopped "
               "observing.")
    assert int(m.group(1)) == EXPECTED_ABI_VERSION, (
        f"python/README.md says ABI {m.group(1)} at this release; "
        f"EXPECTED_ABI_VERSION is {EXPECTED_ABI_VERSION}.")


def test_readme_does_not_contradict_itself_about_abi() -> None:
    """INTERNAL CONSISTENCY — the independent second failure at rc418.

    The header said ABI 10 while the narrative bump sentence in the same file
    said 12 → 13. A reader could have caught that with no access to the source,
    which is what makes it its own defect rather than a symptom of the first.
    """
    text = _text()
    header = _ABI_HEADER.search(text)
    bump = _ABI_BUMP.search(text)
    assert header and bump, (
        "python/README.md no longer carries BOTH an '**ABI N** at this "
        "release' claim and a 'SRMECH_ABI_VERSION moves **N → M**' sentence; "
        "one of the two surfaces this gate compares has been rephrased away.")
    assert int(bump.group(2)) == int(header.group(1)) == EXPECTED_ABI_VERSION, (
        f"python/README.md contradicts itself: the header says ABI "
        f"{header.group(1)}, the bump sentence lands on {bump.group(2)}, and "
        f"the live EXPECTED_ABI_VERSION is {EXPECTED_ABI_VERSION}. All three "
        f"must agree.")


def test_readme_worked_native_status_block_is_current() -> None:
    """The worked ``native_status()`` transcript is OUTPUT, not narrative.

    A worked block prints values; when those values are wrong it is not a stale
    citation, it is a fabricated result — the exact thing the worked-example
    gates exist to refuse. So all three of its fields are pinned live.
    """
    text = _text()
    for label, pat in (("abi_version", _WORKED_ABI),
                       ("expected_abi", _WORKED_EXPECTED_ABI)):
        m = pat.search(text)
        assert m, f"the worked native_status() block no longer prints {label}"
        assert int(m.group(1)) == EXPECTED_ABI_VERSION, (
            f"the worked native_status() block prints {label}="
            f"{m.group(1)}; EXPECTED_ABI_VERSION is {EXPECTED_ABI_VERSION}. A "
            f"worked block is captured OUTPUT — a wrong value here is a "
            f"fabricated result, not a stale citation.")
    m = _WORKED_NATIVE_VERSION.search(text)
    assert m, "the worked native_status() block no longer prints native_version"
    assert m.group(1) == srmech.__version__, (
        f"the worked native_status() block prints native_version="
        f"{m.group(1)!r}; srmech.__version__ is {srmech.__version__!r}. It read "
        f"'0.9.0rc389' at rc418 — thirty rcs behind.")


def test_the_gate_would_have_fired_on_the_rc418_text() -> None:
    """RETRO-CHECK. A gate that would not have caught the defect that motivated
    it is not the gate.

    The rc418 strings are reproduced verbatim rather than described, and each is
    run through the SHIPPED regex — so this fails if the predicate is ever
    loosened to the point where the original defect would slip past.
    """
    rc418_registry = ("with in-C tool dispatch over the 543-entry tool "
                      "registry, the CLI arg-parser,")
    m = _REGISTRY_CARDINAL.search(rc418_registry)
    assert m and int(m.group(1)) == 543, "the registry regex stopped matching"
    assert int(m.group(1)) != _live_op_count(), (
        "543 now equals the live op count, so the retro-check no longer "
        "demonstrates anything — re-point it at the historical value.")

    rc418_abi = ("its ABI matched (**ABI 10** at this release — v9 gave "
                 "`srmech_genome_section_counts` its caller-arena params)")
    m = _ABI_HEADER.search(rc418_abi)
    assert m and int(m.group(1)) == 10, "the ABI-header regex stopped matching"
    assert int(m.group(1)) != EXPECTED_ABI_VERSION, (
        "the live ABI is back to 10; re-point this retro-check.")

    rc418_worked = ("# {'has_native': True, 'dispatching': True, "
                    "'abi_version': 10,\n#  'expected_abi': 10, "
                    "'native_version': '0.9.0rc389', 'load_error': None}")
    assert int(_WORKED_ABI.search(rc418_worked).group(1)) == 10
    assert (_WORKED_NATIVE_VERSION.search(rc418_worked).group(1)
            != srmech.__version__)
