"""rc464 (`#T1188`) — CDRegister is the PREFERRED register shape, as a gate.

"Prefer X" is the kind of statement that lives in prose, goes stale silently, and
is then quoted years later by a reader who had no way to know. srmech has already
paid for exactly that: the sentence "the make_class contract is one-op-per-method
plus a single appends/sets field" sat in three ungated files for ~330 rcs after
it stopped being true and steered a build decision (rc464 CHANGELOG). So the
preference is measured here rather than asserted in a docstring alone.

WHAT IS MEASURED

1. WHICH SURFACES HAND BACK A REGISTER, pinned as an EQUALITY over the shipped
   tool schema. That is the set a reader chooses from, so it is the set the
   preference has to be about. An equality (rather than a subset check) means a
   new register-shaped entry cannot appear unremarked, and the entry that leaves
   when the 16-slot class is removed cannot leave unremarked either.
2. THE PREFERRED ENTRY SAYS SO, in the shipped summary AND in the docstrings a
   reader reaches through ``help()`` — with the SUBSUMING SPELLING, because
   "prefer CDRegister" without ``namespace=`` and the two OPT flags is advice
   that silently changes behaviour at dim 16.
3. EVERY OTHER REGISTER-RETURNING ENTRY POINTS AT IT — a reader who lands on a
   special case must be told where the general one is, in the summary AND in the
   carrier description. ⚠️ THIS POPULATION IS EMPTY AS OF rc464, because the
   16-slot register was removed in the same arc, so the guard is DORMANT: there
   is no second register-returning entry to check. It is kept as a forward guard
   and made to prove itself against a SYNTHETIC pair, because a loop over an
   empty set passes whether or not its body is correct — the shape that let
   clause 3 read green while asserting nothing at all. Clause 1's equality is
   what would report a second register quietly reappearing.
4. THE CARRIER ONTOLOGY AGREES. ``carrier_schema()`` exposes carrier descriptions
   on a different path from ToolEntry summaries; both are read by consumers, so
   both are checked rather than one standing in for the other.
5. THE PROSE ACTUALLY SHIPS. The steer is asserted in the two GENERATED
   artifacts a consumer reads without ever importing the module — the wheel's
   ``_tool_docs.py`` explanation and the compiled-in C tool registry — because
   prose that is only in a Python docstring is not what an MCP client or a
   bare-C host sees.

The negative control at the end proves the steering predicate can fail: a
summary that merely MENTIONS the register does not pass it.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from srmech import cascade
from srmech.introspect.tool_schema import get_tool_schema
from srmech.introspect.carrier_schema import carrier_schema

#: The op that constructs the preferred shape.
PREFERRED = "srmech.cascade.cd_register"

#: Every registered op whose declared return type is a register carrier, pinned
#: as an EQUALITY. rc464 ships exactly one: the 16-slot special case it subsumes
#: was removed in the same arc, so "prefer this one" is no longer a steer between
#: two live options — it is the only option, and the equality is what would
#: report a second register quietly reappearing.
REGISTER_RETURNING = {
    "srmech.cascade.cd_register",
}

#: The spelling that makes "prefer CDRegister" a behaviour-preserving swap at
#: dim 16. Without the namespace the address mint differs (a measurable
#: read-collision difference at starved D); without the flags the two OPT layers
#: raise where the 16-slot register returned. Quote style varies by surface
#: (Python docstrings use ", ToolEntry summaries use '), so the check is
#: quote-insensitive — see :func:`_says_the_subsuming_spelling`.
SUBSUMING_SPELLING_TOKENS = ("namespace=SEDENION", "coupling=True",
                             "error_correction=True")


def _says_the_subsuming_spelling(text: str) -> bool:
    flat = text.replace("'", "").replace('"', "").replace("``", "")
    return all(tok in flat for tok in SUBSUMING_SPELLING_TOKENS)


def _register_entries():
    return {t.name: t for t in get_tool_schema().tools
            if t.returns is not None and t.returns.type.endswith("Register")}


def _steers_to_preferred(text: str) -> bool:
    """Does this prose actually send a reader to the preferred shape?

    Naming ``cd_register`` is not enough — every register entry mentions it in
    passing. The test is that the prose says to PREFER it."""
    return ("cd_register" in text or "CDRegister" in text) and "PREFER" in text.upper()


def test_the_register_returning_surface_is_exactly_what_is_pinned():
    """The set a reader chooses a register from. An equality, so that a new
    register-shaped entry — or the removal of the dim-16 one — is reported."""
    assert set(_register_entries()) == REGISTER_RETURNING
    assert PREFERRED in REGISTER_RETURNING


def test_the_preferred_entry_declares_itself_preferred_with_the_full_spelling():
    """The shipped ToolEntry summary — what an MCP client, ``describe()`` and the
    compiled-in C tool registry all read."""
    entry = _register_entries()[PREFERRED]
    summary = entry.summary
    assert "PREFERRED" in summary, (
        "the preferred register entry does not say it is preferred, so nothing "
        "a consumer reads distinguishes it from the special case")
    assert "cd_register(16" in summary and _says_the_subsuming_spelling(summary), (
        "the summary recommends the general register without the spelling that "
        "makes the swap behaviour-preserving at dim 16 — namespace= decides the "
        "address mint and the two flags gate the value-operations")


def test_the_python_docstrings_carry_the_same_preference():
    """A reader at ``help(cascade.CDRegister)`` must get the same steer as a
    reader of the tool schema; they are different paths to the same decision."""
    cls_doc = inspect.getdoc(cascade.CDRegister) or ""
    factory_doc = inspect.getdoc(cascade.cd_register) or ""
    module_doc = inspect.getdoc(
        __import__("srmech.cascade.cd_register", fromlist=["_"])) or ""
    for label, doc in (("CDRegister", cls_doc),
                       ("cd_register()", factory_doc),
                       ("cd_register module", module_doc)):
        assert "preferred" in doc.lower(), (
            f"{label} does not present itself as the preferred register shape")
    assert _says_the_subsuming_spelling(module_doc), (
        "the module docstring omits the subsuming spelling")


def _steer_offenders(named_summaries, carriers):
    """The clause-3 check, as a FUNCTION over an explicit population.

    Extracted so the rule can be exercised against a synthetic pair while the
    real population is empty. Returns the list of failures; empty means clean.
    """
    bad = []
    for name, summary, carrier_name in named_summaries:
        if not _steers_to_preferred(summary):
            bad.append(f"{name} summary does not steer to {PREFERRED}")
        desc = carriers.get(carrier_name, {}).get("description", "")
        if not _steers_to_preferred(desc):
            bad.append(f"{carrier_name} carrier description does not steer")
    return bad


def test_every_other_register_surface_points_at_the_preferred_one():
    """⚠️ DORMANT BY CONSTRUCTION, and the dormancy is asserted rather than
    accidental.

    The 16-slot register was the only other register-returning entry and this rc
    removed it, so ``others`` is empty and the loop that used to carry this
    clause now runs ZERO times — it passed while asserting nothing. The rule is
    therefore extracted into :func:`_steer_offenders` and exercised below against
    a synthetic pair, so that the day a second register-returning entry lands,
    the check it meets is one that has been proved to work.
    """
    entries = _register_entries()
    others = {name: e for name, e in entries.items() if name != PREFERRED}
    assert not others, (
        f"a second register-returning surface appeared: {sorted(others)}. The "
        f"clause-3 guard below is no longer dormant — feed the real population "
        f"through _steer_offenders() here instead of asserting emptiness."
    )
    # The rule still applies to the real population when there IS one.
    carriers = carrier_schema()
    real = [(n, e.summary, e.returns.type) for n, e in others.items()]
    assert _steer_offenders(real, carriers) == []


def test_the_clause_three_rule_actually_catches_a_non_steering_surface():
    """The loop body clause 3 relies on, executed — against a constructed pair.

    Without this, ``_steer_offenders`` is dead code reached by no test, and the
    dormant guard above would be certifying a rule nothing had ever run.
    """
    carriers = {
        "GoodCarrier": {"description": "PREFER cd_register — it is THE register "
                                       "carrier and subsumes this one."},
        "BadCarrier": {"description": "A 16-slot register carrier."},
    }
    steering = ("srmech.cascade.other_register",
                "PREFER cd_register(16, ...) — it is the general shape.",
                "GoodCarrier")
    not_steering = ("srmech.cascade.other_register",
                    "Construct a register. Related: cd_register, cd_navmap.",
                    "BadCarrier")

    assert _steer_offenders([steering], carriers) == []
    offences = _steer_offenders([not_steering], carriers)
    assert len(offences) == 2, offences
    assert any("summary" in o for o in offences)
    assert any("carrier description" in o for o in offences)


def test_the_preferred_carrier_description_says_it_is_the_register_carrier():
    cdr = carrier_schema()["CDRegister"]["description"]
    assert "THE register carrier" in cdr, (
        "the carrier ontology does not mark CDRegister as the register carrier")


def test_the_steering_predicate_can_fail():
    """A guard that cannot fail is not a guard. Mentioning the preferred register
    is NOT steering to it; every register entry does that in passing."""
    assert not _steers_to_preferred(
        "Construct a 16-slot register. Related: cd_register, cd_navmap.")
    assert not _steers_to_preferred("PREFER the other one.")
    assert _steers_to_preferred("PREFER cd_register(16, ...) — it is this "
                                "instrument byte-for-byte.")


def test_the_preference_ships_in_the_generated_artifacts():
    """The steer has to reach a consumer who never imports the module.

    Two surfaces carry the shipped prose and neither is a docstring: the wheel's
    generated ``_tool_docs.py`` (what ``TOOL_DOCS`` serves) and the compiled-in
    C tool registry (what a bare-C host reads). The tree's ref-notation
    discipline measured 15 false links shipping inside published wheels through
    exactly these two files (2026-07-27), which is why they are checked directly
    rather than trusted to follow the source."""
    from srmech.introspect._tool_docs import TOOL_DOCS
    doc = TOOL_DOCS[PREFERRED]["explanation"]
    assert "PREFERRED" in doc, (
        "the shipped explanation does not mark the preferred register shape")
    assert _says_the_subsuming_spelling(doc)

    registry_c = (Path(__file__).resolve().parents[2]
                  / "c" / "src" / "srmech_tool_registry.c")
    if not registry_c.exists():             # source checkout only
        pytest.skip("C tool registry source not present in this layout")
    text = registry_c.read_text(encoding="utf-8")
    assert "PREFERRED shape since rc464" in text, (
        "the compiled-in C tool registry does not carry the preference — a "
        "bare-C host reading its own registry would not be told")
    # Through rc464 stage 2 this also asserted that the 16-slot entry's baked
    # summary carried "PREFER srmech.cascade.cd_register" — the steer FROM the
    # special case TO the general one. That entry is removed in this same rc, so
    # the assertion would now be vacuous-true against a string nobody writes.
    # What replaces it is the fact the removal actually established: the C
    # registry carries exactly ONE register-returning entry, so there is nothing
    # left to steer FROM. A second one reappearing is what this must catch.
    baked = [n for n in REGISTER_RETURNING if n in text]
    assert baked == [PREFERRED], (
        f"the C tool registry bakes {baked} as register-returning entries; the "
        f"preference is only meaningful over the set REGISTER_RETURNING pins, "
        f"and after rc464 that set is exactly {{{PREFERRED!r}}}")
    assert "srmech.cascade.sedenion_register" not in text, (
        "the compiled-in C tool registry still names the 16-slot register that "
        "rc464 removed — a bare-C host would be told to reach for an entry the "
        "table no longer holds")
