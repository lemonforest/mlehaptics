"""A curated worked-example output that was WRONG BY ONE ULP, and shipped
green for 39 releases because a ``# ->`` comment is not an assertion
(rc469, `#T1188`).

⚠️ **rc477 (`#T1188`) TURNED THIS FILE INSIDE OUT, and that is worth reading
before the rest.** rc469 found the curated snippet claiming
``[0.0, 0.6, 0.0, 0.8]`` while the op served
``[0.0, 0.6000000000000001, 0.0, 0.8]``, repaired the PROSE to match the
implementation, and pinned the miss as a CAPTURE so nobody would tidy it back.
The reasoning was *"that is where the Class-N sqrt cascade lands"* — and it was
not. It is where THREE roundings land: the axis was normalised by taking the
root of the sum of squares, taking its RECIPROCAL and multiplying each
component. rc477 puts the ``1/√S`` inside the radicand over an integer
direction, and the op serves the correctly rounded ``3/5``, which IS ``0.6``.

So the literal this file named ``_TIDY_FALSEHOOD`` is the TRUE value now, and
the value it pinned is the one that must never come back. Everything below is
inverted accordingly — nothing is deleted, because the property worth guarding
is unchanged in both directions: **the prose and the implementation must agree,
and neither half may be edited to match the other without being measured.**
The original finding stands exactly as written: it shipped green for 39
releases because a ``# ->`` comment is inert to the interpreter. What rc469 got
wrong was not the gate; it was believing the value it was pinning.

THE FALSEHOOD (as rc469 found it)
=================================
``srmech/introspect/_tool_docs_curated.py`` is the SSoT for the hand-curated
introspection docs, and its own header says every example there "is a REAL
executed result ... never typed". One was not::

    qdft_resolve_mu([0.0, 3.0, 0.0, 4.0])
        # -> [0.0, 0.6, 0.0, 0.8]      <- shipped through rc468

The executed value THROUGH rc476 was ``[0.0, 0.6000000000000001, 0.0, 0.8]``.
Component ``[1]`` was ``0x1.3333333333334p-1`` where ``0.6`` is
``0x1.3333333333333p-1`` — a gap of exactly one ULP. Component ``[3]`` is
EXACTLY ``0.8``, which is why the repair was a ONE-value edit then and a
one-value edit now: a two-value "tidy" replaces one falsehood with another in
either direction. :func:`test_component_1_lands_exactly_on_three_fifths_now`
is that guard, inverted at rc477 and still refusing a two-value edit.

WHY IT SHIPPED GREEN, WHICH IS THE ACTUAL FINDING
=================================================
The falsehood travelled to users on two surfaces — ``_tool_docs.py`` (merged
into every ``ToolEntry.explanation`` / ``example``, so it reaches the MCP tool
list) and the compiled-in ``c/src/srmech_tool_registry.c``. Both are GENERATED
from the curated SSoT, so both carried it verbatim.

And ``tests/worked_examples_result.ndjson`` recorded the row as ``status: ok``
with ``problems: []`` — correctly. ``tools/run_worked_examples.py`` EXECUTES
every curated snippet and reports what raised; it does not, and cannot, compare
a ``# ->`` COMMENT against what the line returned. **Asserting prose is not a
test.** A comment is inert to the interpreter, so a snippet whose stated output
is wrong executes exactly as cleanly as one whose stated output is right.

THE FIX IS A PAIRED WITNESS, AND WHY IT IS PAIRED
=================================================
Editing the literal inside the comment changes nothing about whether anything is
checked: after the edit the ledger still records ``ok`` / ``problems: []``, and
the next drift is as invisible as this one was. So the two halves are asserted
SEPARATELY and each can fail on its own:

  * :func:`test_the_executed_value_is_what_the_curated_snippet_claims` runs the
    call and compares against the literal PARSED OUT OF the curated string. It
    fails if the implementation moves.
  * :func:`test_the_curated_snippet_carries_the_executed_literal` and
    :func:`test_no_curated_snippet_still_claims_the_tidy_value` fail if the
    prose moves — including if someone "tidies" ``0.6000000000000001`` back.
  * :func:`test_the_shipped_surfaces_carry_the_repaired_literal` fails if the
    SSoT was fixed and the generated artifacts were not regenerated, which is
    the half-done shape this rc is most exposed to.

WHAT THIS DELIBERATELY DOES **NOT** CLOSE — measured, not estimated
==================================================================
It closes the class for ONE line. Measured on this tree at 0.9.0rc469: **732**
curated rows, **649** of them carrying a ``worked`` snippet, **839** ``# ->``
comment lines in total, of which **154** carry a float literal — the subclass in
which a ULP falsehood can hide at all — spread across **89** distinct ops. This
file asserts one of the 839. The other 838 remain un-assertable prose.

Closing the class properly needs a general instrument: execute each ``# ->``
line's expression in the snippet's accumulated namespace and compare against the
``ast.literal_eval`` of the comment, skipping the lines whose comment is prose
rather than a literal. That is a real build with its own failure modes (a
half-built version that silently skips everything would pass on all 839 lines
and read as coverage), and it is FILED rather than half-landed here.

The one thing NOT done, deliberately: this snippet is **not** converted to an
executed ``assert``. The ``# ->`` comment is the dialect of all 649 curated
snippets, and those snippets ship as PEDAGOGY through the MCP tool list and the
compiled-in C registry. Rewriting one of them in another dialect would fork that
surface and close the un-assertable class for 1 of 839 while reading as though
it had closed the class.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from srmech.cascade import qdft_resolve_mu
from srmech.introspect._tool_docs_curated import CURATED
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

warmup_all()

_OP = "srmech.cascade.qdft_resolve_mu"

#: The general-axis call whose output was misquoted. Kept as source text so the
#: same string can be located inside the curated snippet AND evaluated.
_CALL_SRC = "qdft_resolve_mu([0.0, 3.0, 0.0, 4.0])"

#: The value the op SERVES. rc469 named this ``_TIDY_FALSEHOOD`` — the
#: tidy-looking literal the curated snippet claimed while the op served one ULP
#: above it — and rc477 (`#T1188`) made it the truth by putting the ``1/√S``
#: inside the radicand. The names below are kept in the direction they now
#: point, so a reader is never asked to hold "falsehood" and "true value" as
#: the same string.
_SERVED = "[0.0, 0.6, 0.0, 0.8]"

#: The value served THROUGH rc476, and the one that must never come back: it is
#: the float-detour signature (a root, a reciprocal and a multiply). Named so
#: the strict-zero sweep below has something concrete to refuse.
_PRE_RC477 = "[0.0, 0.6000000000000001, 0.0, 0.8]"

_HERE = Path(__file__).resolve().parent
_PKG_ROOT = _HERE.parent                       # docs/srmech/python
_SRMECH_ROOT = _PKG_ROOT.parent                # docs/srmech
_GENERATED = (
    _PKG_ROOT / "srmech" / "introspect" / "_tool_docs.py",
    _SRMECH_ROOT / "c" / "src" / "srmech_tool_registry.c",
)


def _curated_worked() -> str:
    return CURATED[_OP]["example"]["worked"]


def _claimed_literal(worked: str) -> str:
    """The list literal the curated snippet states for :data:`_CALL_SRC`.

    Read out of the prose rather than hardcoded, so the executed-value test
    below compares against WHAT THE DOC SAYS and not against a second copy of
    the answer written in this file. A test that compared the implementation to
    a literal typed here would stay green while the doc drifted — which is the
    exact failure this file exists to end.
    """
    lines = worked.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == _CALL_SRC:
            nxt = lines[i + 1].strip()
            m = re.search(r"# ->\s*(\[.*\])", nxt)
            assert m is not None, (
                f"the line after {_CALL_SRC!r} in the curated snippet is "
                f"{nxt!r}; expected a '# -> [...]' output comment"
            )
            return m.group(1)
    raise AssertionError(
        f"{_CALL_SRC!r} is no longer a line of the curated worked snippet for "
        f"{_OP}; this gate's subject moved and the gate must move with it"
    )


# ── the executed half ─────────────────────────────────────────────────────


def test_the_executed_value_is_what_the_curated_snippet_claims():
    """The implementation, run, against the literal parsed out of the doc."""
    claimed = ast.literal_eval(_claimed_literal(_curated_worked()))
    actual = qdft_resolve_mu([0.0, 3.0, 0.0, 4.0])
    assert actual == claimed, (
        f"{_CALL_SRC} returns {actual!r}; the curated worked example claims "
        f"{claimed!r}. A '# ->' comment is inert to the interpreter, so this "
        f"disagreement ships silently in the wheel, the MCP tool list and the "
        f"compiled-in C registry unless this assertion catches it."
    )
    # float equality, deliberately: these are the same bit patterns or they are
    # not the same value, and a tolerance here would re-open the ULP gap.
    assert [float.hex(v) for v in actual] == [float.hex(v) for v in claimed]


def test_component_1_lands_exactly_on_three_fifths_now():
    """✅ **rc477 (`#T1188`): component ``[1]`` MOVED, and this gate inverts.**

    Through rc476 it landed ONE ULP ABOVE ``0.6`` — ``0x1.3333333333334p-1``
    against ``0.6 = 0x1.3333333333333p-1`` — and this file asserted that
    ``out[1] != 0.6``, pinning the miss as a CAPTURE so nobody would "tidy" it
    back. The miss was not where the cascade lands; it was where THREE
    roundings land. The axis is normalised over its integer direction now, with
    the ``1/√S`` inside the radicand, so an exactly representable unit
    survives: ``3/5`` is a dyadic-free rational whose nearest double IS
    ``0.6``, and the op serves it.

    The assertion is INVERTED rather than deleted, because the property worth
    guarding is the same one in the other direction: a regression to the float
    detour brings ``0x1.3333333333334p-1`` straight back, and this fires.
    Component ``[3]`` is EXACTLY ``0.8`` and always was — a reader repairing
    "the 0.6/0.8 line" by moving both would still mint a falsehood there.
    """
    out = qdft_resolve_mu([0.0, 3.0, 0.0, 4.0])
    assert out[0] == 0.0 and out[2] == 0.0
    assert out[1] == 0.6, (
        "component [1] is not 0.6 — if it is 0x1.3333333333334p-1 the float "
        "axis detour is back (a root, a reciprocal and a multiply); if it is "
        "something else again, re-measure before touching the doc")
    assert float.hex(out[1]) == "0x1.3333333333333p-1"
    assert float.hex(out[1]) != "0x1.3333333333334p-1", (
        "this is the pre-rc477 value, one ULP above 3/5")
    assert out[3] == 0.8, (
        "component [3] is EXACTLY 0.8 — if this fires, either the cascade "
        "moved or someone 'tidied' both components when only [1] ever moved"
    )


# ── the prose half ────────────────────────────────────────────────────────


def test_the_curated_snippet_carries_the_executed_literal():
    worked = _curated_worked()
    assert _claimed_literal(worked) == _SERVED
    assert "0x1.3333333333334p-1" in worked, (
        "the curated snippet must still SAY what the value USED to be and why "
        "it moved. rc469 asked for that sentence so the next reader would not "
        "tidy the ULP away; rc477 keeps asking for it so the next reader does "
        "not read 0.6 as an eternal fact. The history is the pedagogy."
    )


def test_no_curated_snippet_still_claims_the_pre_rc477_value():
    """Strict zero, over the whole curated corpus, for the value rc477 removed.

    Inverted from rc469's sweep, which refused ``[0.0, 0.6, 0.0, 0.8]``. That
    string is what the op serves now; the one to refuse is the float detour's,
    because a curated row still claiming it would mean either the prose was
    never re-run or the implementation regressed."""
    offenders = sorted(
        name for name, row in CURATED.items()
        if isinstance(row.get("example"), dict)
        and _PRE_RC477 in (row["example"].get("worked") or "")
    )
    assert offenders == [], (
        f"{_PRE_RC477} is the PRE-rc477 value — a root, a reciprocal and a "
        f"multiply, one ULP above 3/5. Still claimed by: {offenders}"
    )


# ── the emission half: the SSoT reached the artifacts ─────────────────────


def test_the_live_registry_entry_carries_the_repaired_literal():
    """``_tool_docs.py`` is merged into the live ``ToolEntry`` — regen ran."""
    entry = next(t for t in get_tool_schema().tools if t.name == _OP)
    worked = entry.example["worked"]
    assert _SERVED in worked
    assert _PRE_RC477 not in worked, (
        "the curated SSoT was repaired and the generated _tool_docs.py was "
        "not regenerated — run `python3 tools/regen_all.py`"
    )


@pytest.mark.parametrize("path", _GENERATED, ids=lambda p: p.name)
def test_the_shipped_surfaces_carry_the_repaired_literal(path: Path):
    """The two files the falsehood actually TRAVELLED in.

    ``_tool_docs.py`` reaches users through ``describe()`` and the MCP tool
    list; ``srmech_tool_registry.c`` is compiled into the native library. Both
    are generated, so this arm goes red on a repaired SSoT with a stale regen —
    the "applied without being fixed" shape.
    """
    if not path.exists():                     # pure/Pyodide checkout: no C tree
        pytest.skip(f"{path} not present in this checkout")
    text = path.read_text(encoding="utf-8")
    assert _SERVED in text
    assert _PRE_RC477 not in text, (
        f"{path.name} still ships the rc468 falsehood — regen_all.py has not "
        f"run since the curated SSoT was repaired"
    )
