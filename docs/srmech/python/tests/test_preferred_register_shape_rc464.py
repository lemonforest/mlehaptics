"""rc464 → rc465 (`#T1188`) — CDRegister is the PREFERRED register shape, as a
gate that can actually fail.

"Prefer X" is the kind of statement that lives in prose, goes stale silently, and
is then quoted years later by a reader who had no way to know. srmech has already
paid for exactly that: the sentence "the make_class contract is one-op-per-method
plus a single appends/sets field" sat in three ungated files for ~330 rcs after
it stopped being true and steered a build decision (rc464 CHANGELOG).

WHAT rc464 SHIPPED, AND WHY IT WAS NOT A GATE
---------------------------------------------
rc464's clause 3 (``test_every_other_register_surface_points_at_the_preferred_one``)
had an ENTIRE LOOP BODY THAT NEVER EXECUTED, so both of its assertions were
unreachable. EXECUTED at rc465 with ``sys.settrace`` over the rc464 file on the
rc464 tree: lines hit = ``[82, 83, 137, 138, 144, 158, 159, 160, 166, 167, 168]``
— the ``for`` header at 138 and ``return bad`` at 144 ran, and the two
``if not _steers_to_preferred`` checks at 139-143 did not. Two causes, and the
second is the one that matters:

1. THE POPULATION WAS ONE CHANNEL AND ONE PREDICATE. ``_register_entries()``
   kept ToolEntries whose ``returns.type.endswith("Register")``. Exactly ONE of
   733 entries declares such a return, so ``others`` was empty and the loop
   iterated zero times.
2. THE EMPTINESS ASSERTION PRE-EMPTED THE LOOP. ``assert not others`` sat ABOVE
   the ``_steer_offenders`` call, so in the world where the population IS
   non-empty the test fails at the emptiness line and the steer check is STILL
   never reached. The clause was dead in both worlds, not merely dormant.

And the population definition was itself wrong: a register does not have to
declare a ``*Register`` ToolEntry return type to BE one. A ``SedenionRegister``
``[class]`` TOML — the exact channel the 16-slot register shipped through from
rc140 to rc464 — registers, constructs, reads and writes, and passed every test
in this file and in ``test_domain_classes_rc298.py`` unremarked (EXECUTED at
rc465 through ``dsl.register_class_dir``; the shipped catalog uses the same
``sorted(base.glob("*.toml"))`` loader at ``srmech/dsl/_class_catalog.py:121``).

WHAT IS MEASURED NOW — SIX CHANNELS, TWO PREDICATES
---------------------------------------------------
A reader can be pointed at a register through several independent surfaces, and
a second register shape can appear on any one of them without touching the
others. So the population is derived from all of them and each is pinned as an
EQUALITY:

P1 THE TOOL SCHEMA, by three predicates rather than one: the return type names a
   register carrier, OR a parameter type does (``cdr_element_of`` takes
   ``"CDRegister | dict"`` and rc464's ``endswith`` missed it), OR the entry is
   bound as a method/chain step of a register-shaped ``[class]``. Twenty entries
   today.
P2 THE CLASS CATALOG — the only check that catches the rc140 TOML channel. A
   class is register-shaped if its name ends ``Register`` or its method set
   covers the register verbs ``{write, read, navigate}``.
P3 THE CARRIER ONTOLOGY (``carrier_schema()``), read by consumers on a different
   path from ToolEntry summaries.
P4 THE MCP WIRE handle-kind map. A second register class needs a row here to
   cross the wire, and NOTHING pinned it before rc465.
P5 THE GENERATED ARTIFACTS — the wheel's ``_tool_docs.py``, the curated docs and
   their generator, and both compiled-in C registries. A consumer who never
   imports the module reads these.
P6 SHIPPED REGISTRY PROSE. A summary may not present another register class as a
   live alternative even when the types are clean.

Over that population two predicates run, and BOTH iterate on the shipped tree:

A. OWNED SURFACES — the 20 entries the preferred register owns — must NAME it.
   This loop executes 20 times today; it is the body rc464's never reached.
B. NON-OWNED REGISTER SURFACES must steer to the preferred shape, in the summary
   AND in the carrier description. Zero today. It runs on whatever the SAME
   derivation produced, with no emptiness assertion above it, so the day a
   second register surface lands the check it meets is the one that runs — and
   it is not pre-empted by the equality pins, which live in other tests.

MUTATIONS PLANTED, RED VERIFIED, REVERTED (rc465, EXECUTED)
------------------------------------------------------------
M1 an in-memory second ``*Register``-returning ToolEntry with a non-steering
   summary → RED at predicate B with 2 offences (summary + carrier description).
   Under rc464 this failed at the emptiness assertion and never reached the
   steer.
M2 a ``SedenionRegister`` ``[class]`` TOML registered through a scratch class
   dir → RED at P2. Under rc464 this was GREEN.
M3 a second row in ``_HANDLE_SHAPED_CARRIERS`` → RED at P4. Under rc464 nothing
   read that map at all.
M4 a ``cdr_*`` summary presenting the 16-slot register as a live alternative →
   RED at P6. Under rc464 this was GREEN.
Negative control: all of it green on the shipped tree.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from srmech import cascade, dsl
from srmech.introspect.tool_schema import get_tool_schema
from srmech.introspect.carrier_schema import carrier_schema

#: The op that constructs the preferred shape.
PREFERRED = "srmech.cascade.cd_register"

#: The carrier the preferred shape hands back.
PREFERRED_CARRIER = "CDRegister"

#: A class is register-SHAPED if it covers these verbs, whatever it is called.
#: Name-only detection is what let the TOML channel through: a descriptor is
#: free to call itself anything.
REGISTER_VERBS = frozenset({"write", "read", "navigate"})

#: Any CamelCase token ending in ``Register``. Used as a token scan rather than
#: ``endswith`` so that a union type — ``"CDRegister | dict"`` — is caught.
REGISTER_TOKEN = re.compile(r"\b[A-Z][A-Za-z0-9_]*Register\b")

#: The full register surface, pinned as an EQUALITY over all three P1
#: predicates. Nineteen adapters (14 ``cdr_*`` + ``cd_navmap`` + the four
#: carrier-arithmetic ops the class binds) plus the constructor.
REGISTER_SURFACE_OPS = frozenset({
    "srmech.cascade.cd_register",
    "srmech.cascade.cd_conjugate",
    "srmech.cascade.cd_mult",
    "srmech.cascade.cd_navmap",
    "srmech.cascade.cd_norm_sq",
    "srmech.cascade.cdr_carry",
    "srmech.cascade.cdr_carry_block",
    "srmech.cascade.cdr_clean",
    "srmech.cascade.cdr_correct",
    "srmech.cascade.cdr_couple_working",
    "srmech.cascade.cdr_element",
    "srmech.cascade.cdr_element_of",
    "srmech.cascade.cdr_materialize",
    "srmech.cascade.cdr_navigate",
    "srmech.cascade.cdr_read_unbind",
    "srmech.cascade.cdr_slots",
    "srmech.cascade.cdr_uncouple_working",
    "srmech.cascade.cdr_working_block",
    "srmech.cascade.cdr_write",
    "srmech.cascade.left_mult_is_invertible",
})

#: The five files a consumer reads without importing the module. Paths are
#: relative to ``docs/srmech/``.
GENERATED_ARTIFACTS = (
    "python/srmech/introspect/_tool_docs.py",
    "python/srmech/introspect/_tool_docs_curated.py",
    "python/tools/gen_curated_probe.py",
    "c/src/srmech_tool_registry.c",
    "c/src/srmech_carrier_registry.c",
)

#: The ONE place a removed register class is legitimately named in those files:
#: the curated-probe oracle explaining that its subject is gone and that it
#: therefore compares against a recorded fixture. Pinned as an equality with the
#: exact sentence, so a SECOND historical mention — or this one turning into a
#: claim that the class is live — is reported rather than absorbed.
HISTORICAL_REGISTER_MENTIONS = frozenset({
    ("python/tools/gen_curated_probe.py", "SedenionRegister",
     "The 16-slot ``SedenionRegister`` is gone"),
})

#: The spelling that makes "prefer CDRegister" a behaviour-preserving swap at
#: dim 16. Without the namespace the address mint differs (a measurable
#: read-collision difference at starved D); without the flags the two OPT layers
#: raise where the 16-slot register returned. Quote style varies by surface
#: (Python docstrings use ", ToolEntry summaries use '), so the check is
#: quote-insensitive — see :func:`_says_the_subsuming_spelling`.
SUBSUMING_SPELLING_TOKENS = ("namespace=SEDENION", "coupling=True",
                             "error_correction=True")

_ROOT = Path(__file__).resolve().parents[2]


def _says_the_subsuming_spelling(text: str) -> bool:
    flat = text.replace("'", "").replace('"', "").replace("``", "")
    return all(tok in flat for tok in SUBSUMING_SPELLING_TOKENS)


def _register_tokens(text: str) -> set:
    return set(REGISTER_TOKEN.findall(text or ""))


def _entry_prose(entry) -> str:
    """Everything a consumer reads on one ToolEntry, as one string."""
    parts = [entry.summary or "", getattr(entry, "explanation", "") or ""]
    for p in (entry.parameters or []):
        parts += [p.type or "", p.summary or ""]
    if entry.returns is not None:
        parts.append(entry.returns.type or "")
    return " ".join(parts)


def _register_shaped_classes() -> dict:
    """P2: every ``[class]`` descriptor that IS a register, by name or by verbs.

    Detection is deliberately not name-only: the rc140 channel ships a TOML that
    may call itself anything, and it is the channel that went unremarked.
    """
    out = {}
    for name in dsl.list_classes():
        desc = dsl.describe_class(name)
        methods = set(desc.get("methods") or {})
        if name.endswith("Register") or REGISTER_VERBS <= methods:
            out[name] = desc
    return out


def _class_adapter_ops(desc: dict, registry_names) -> set:
    """The registry entries a ``[class]`` descriptor binds.

    The TOML spells ops by MODULE path (``srmech.cascade.cd_register.cdr_write``)
    while the registry names them by PACKAGE path
    (``srmech.cascade.cdr_write``), so the join is on the leaf.
    """
    bound = set()
    for method in (desc.get("methods") or {}).values():
        for step in [method] + list(method.get("chain") or []):
            if step.get("op"):
                bound.add(step["op"].rsplit(".", 1)[-1])
    return {n for n in registry_names if n.rsplit(".", 1)[-1] in bound}


def _register_surface(tools=None):
    """P1: the full register surface, and which register each member belongs to.

    Returns ``(entries, owner)`` where ``entries`` maps op name → ToolEntry and
    ``owner`` maps op name → the set of register carriers that claim it. An op
    with ``PREFERRED_CARRIER`` among its owners is OWNED; anything else on the
    surface belongs to some OTHER register and faces the steer predicate.
    """
    tools = list(get_tool_schema().tools) if tools is None else list(tools)
    by_name = {t.name: t for t in tools}
    owner: dict = {}

    for t in tools:
        toks = set()
        if t.returns is not None:
            toks |= _register_tokens(t.returns.type)
        for p in (t.parameters or []):
            toks |= _register_tokens(p.type)
        if toks:
            owner.setdefault(t.name, set()).update(toks)

    for cls_name, desc in _register_shaped_classes().items():
        for op in _class_adapter_ops(desc, by_name):
            owner.setdefault(op, set()).add(cls_name)

    entries = {n: by_name[n] for n in owner}
    return entries, owner


def _steers_to_preferred(text: str) -> bool:
    """Does this prose actually send a reader to the preferred shape?

    Naming ``cd_register`` is not enough — every register entry mentions it in
    passing. The test is that the prose says to PREFER it."""
    return ("cd_register" in text or "CDRegister" in text) and "PREFER" in text.upper()


def _names_the_preferred_register(text: str) -> bool:
    return "cd_register" in text or PREFERRED_CARRIER in text


def _steer_offenders(named_summaries, carriers):
    """Predicate B, as a FUNCTION over an explicit population.

    Extracted so the rule can also be exercised against a synthetic pair.
    Returns the list of failures; empty means clean.
    """
    bad = []
    for name, summary, carrier_name in named_summaries:
        if not _steers_to_preferred(summary):
            bad.append(f"{name} summary does not steer to {PREFERRED}")
        desc = carriers.get(carrier_name, {}).get("description", "")
        if not _steers_to_preferred(desc):
            bad.append(f"{carrier_name} carrier description does not steer")
    return bad


# --------------------------------------------------------------------------
# The two predicates, over the REAL population. Neither is guarded by an
# equality or an emptiness assertion — those live in their own tests below, so
# that a second register shape reaches these bodies rather than short-circuiting
# at a pin. That ordering IS the rc464 defect, restated.
# --------------------------------------------------------------------------

def test_every_register_surface_owned_by_the_preferred_shape_names_it():
    """Predicate A. Twenty iterations on the shipped tree.

    A reader who lands on ``cdr_correct`` or ``cd_navmap`` must be told which
    register it operates on; an adapter that stops naming its own class is how a
    surface quietly detaches from the shape it belongs to.
    """
    entries, owner = _register_surface()
    owned = sorted(n for n, owners in owner.items()
                   if PREFERRED_CARRIER in owners)
    assert owned, (
        "no surface at all is owned by the preferred register — the derivation "
        "that feeds both predicates returned nothing, so this loop would pass "
        "by iterating zero times (the rc464 defect)")
    checked = 0
    offences = []
    for name in owned:
        checked += 1
        if not _names_the_preferred_register(_entry_prose(entries[name])):
            offences.append(name)
    assert checked == len(owned) and checked >= 20, (
        f"predicate A ran {checked} times over {len(owned)} owned surfaces")
    assert offences == [], (
        f"these surfaces operate on {PREFERRED_CARRIER} without naming it, so a "
        f"reader who lands on one is not told which register it belongs to: "
        f"{offences}")


def test_every_register_surface_not_owned_by_the_preferred_shape_steers_to_it():
    """Predicate B — the forward guard, reachable in BOTH worlds.

    rc464 asserted emptiness ABOVE the equivalent call, so when the population
    was non-empty the test failed at the emptiness line and this check was never
    reached. There is no such assertion here: the population is whatever the
    shared derivation produced, and the equality pins live in their own tests.

    Today the non-owned population is empty because the 16-slot register was
    removed in rc464. What makes that emptiness honest rather than vacuous is
    that the SAME derivation is asserted non-empty above (20 owned surfaces),
    the rule is exercised against a synthetic pair below, and rc465 planted a
    second register-returning entry in memory and verified this assertion goes
    red with two offences.
    """
    entries, owner = _register_surface()
    assert entries, "the register-surface derivation returned nothing"
    carriers = carrier_schema()
    others = [(n, entries[n].summary or "",
               sorted(owner[n] - {PREFERRED_CARRIER})[0])
              for n, owners in sorted(owner.items())
              if PREFERRED_CARRIER not in owners]
    assert _steer_offenders(others, carriers) == [], (
        "a register surface that does NOT belong to the preferred shape fails "
        "to point a reader at it")


# --------------------------------------------------------------------------
# The channel equalities. Each catches an addition the others cannot see.
# --------------------------------------------------------------------------

def test_the_register_surface_population_is_exactly_what_is_pinned():
    """P1. An equality over three predicates, not one ``endswith``."""
    entries, _ = _register_surface()
    assert set(entries) == set(REGISTER_SURFACE_OPS), (
        f"register surface drifted; "
        f"added={sorted(set(entries) - REGISTER_SURFACE_OPS)} "
        f"removed={sorted(REGISTER_SURFACE_OPS - set(entries))}")
    assert PREFERRED in entries


def test_the_class_catalog_holds_exactly_one_register_shaped_class():
    """P2 — the rc140 TOML channel, and the ONLY check that sees it.

    A descriptor dropped into the class catalog registers, constructs and works
    without touching the tool schema, the carrier ontology or the wire map.
    """
    shaped = _register_shaped_classes()
    assert set(shaped) == {PREFERRED_CARRIER}, (
        f"a second register-shaped [class] descriptor is live: "
        f"{sorted(set(shaped) - {PREFERRED_CARRIER})}. This is the channel the "
        f"16-slot register shipped through from rc140 to rc464.")
    assert REGISTER_VERBS <= set(shaped[PREFERRED_CARRIER].get("methods") or {})


def test_the_carrier_ontology_holds_exactly_one_register_carrier():
    """P3."""
    keys = {k for k in carrier_schema() if _register_tokens(k)}
    assert keys == {PREFERRED_CARRIER}, sorted(keys)


def test_the_mcp_wire_handle_map_holds_exactly_one_register_carrier():
    """P4. A second register class needs a row here to cross the wire, and no
    test read this map before rc465."""
    from srmech.mcp import _coercion
    keys = {k for k in _coercion._HANDLE_SHAPED_CARRIERS if _register_tokens(k)}
    assert keys == {PREFERRED_CARRIER}, (
        f"the MCP handle-kind map exposes register carriers {sorted(keys)}; "
        f"only {PREFERRED_CARRIER} crosses the wire as a register")


def test_no_register_class_but_the_preferred_one_is_named_in_shipped_prose():
    """P6. Types can be clean while the prose offers a live alternative."""
    seen: dict = {}
    for t in get_tool_schema().tools:
        for tok in _register_tokens(_entry_prose(t)):
            seen.setdefault(tok, []).append(t.name)
    others = {k: v for k, v in seen.items() if k != PREFERRED_CARRIER}
    assert set(seen) == {PREFERRED_CARRIER}, (
        f"shipped ToolEntry prose names register classes other than "
        f"{PREFERRED_CARRIER}: {others}")
    carrier_seen = set()
    for name, spec in carrier_schema().items():
        carrier_seen |= _register_tokens(
            name + " " + (spec.get("description") or ""))
    assert carrier_seen == {PREFERRED_CARRIER}, sorted(carrier_seen)


def test_the_generated_artifacts_name_no_other_register():
    """P5. Every ``*Register`` token in the files a consumer reads without
    importing the module, pinned — with the one historical mention held to its
    exact sentence rather than waved through by a substring rule."""
    found = set()
    checked = 0
    for rel in GENERATED_ARTIFACTS:
        path = _ROOT / rel
        if not path.exists():                # source checkout only
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            for tok in _register_tokens(line):
                if tok == PREFERRED_CARRIER:
                    continue
                sentence = next(
                    (s for _, _, s in HISTORICAL_REGISTER_MENTIONS if s in line),
                    line.strip())
                found.add((rel, tok, sentence))
        assert "srmech.cascade.sedenion_register" not in text, (
            f"{rel} still names the 16-slot register op that rc464 removed")
    assert checked >= 3, f"only {checked} generated artifacts were present"
    assert found == set(HISTORICAL_REGISTER_MENTIONS), (
        f"unexpected register classes named in generated artifacts: "
        f"{sorted(found - set(HISTORICAL_REGISTER_MENTIONS))}; "
        f"missing pinned historical mentions: "
        f"{sorted(set(HISTORICAL_REGISTER_MENTIONS) - found)}")


# --------------------------------------------------------------------------
# The preference itself, on each surface a reader can land on.
# --------------------------------------------------------------------------

def test_the_preferred_entry_declares_itself_preferred_with_the_full_spelling():
    """The shipped ToolEntry summary — what an MCP client, ``describe()`` and the
    compiled-in C tool registry all read."""
    entries, _ = _register_surface()
    summary = entries[PREFERRED].summary
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


def test_the_steer_rule_actually_catches_a_non_steering_surface():
    """Predicate B's body, executed against a constructed pair.

    This is a NEGATIVE CONTROL on the rule, not the gate: predicate B's real
    population is empty today, so without this the rule would be certified by
    nothing. It is no longer the only thing that runs — predicate A iterates 20
    times on the shipped tree — but it is what proves the two-offence shape the
    rc465 M1 mutation was verified against.
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
    cdr = carrier_schema()[PREFERRED_CARRIER]["description"]
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


def test_the_owned_naming_predicate_can_fail():
    """Predicate A's rule, exercised on prose that does not name the class."""
    assert _names_the_preferred_register("Materialize the CDRegister bundle.")
    assert _names_the_preferred_register("Delegates to cd_register().")
    assert not _names_the_preferred_register(
        "Materialize the 16-slot bundle. See cd_navmap.")


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

    registry_c = _ROOT / "c" / "src" / "srmech_tool_registry.c"
    if not registry_c.exists():             # source checkout only
        pytest.skip("C tool registry source not present in this layout")
    text = registry_c.read_text(encoding="utf-8")
    assert "PREFERRED shape since rc464" in text, (
        "the compiled-in C tool registry does not carry the preference — a "
        "bare-C host reading its own registry would not be told")
    # Through rc464 stage 2 this also asserted that the 16-slot entry's baked
    # summary carried "PREFER srmech.cascade.cd_register" — the steer FROM the
    # special case TO the general one. That entry is removed, so the assertion
    # would now be vacuous-true against a string nobody writes. What replaces it
    # is the fact the removal established: the C registry carries exactly ONE
    # register-CONSTRUCTING entry, and rc465's P5 scan above pins every
    # ``*Register`` token in this same file.
    assert PREFERRED in text
    assert "srmech.cascade.sedenion_register" not in text, (
        "the compiled-in C tool registry still names the 16-slot register that "
        "rc464 removed — a bare-C host would be told to reach for an entry the "
        "table no longer holds")
