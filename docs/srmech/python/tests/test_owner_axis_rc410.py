"""rc410 (`#T1085`) — the OWNER AXIS: gates that asked "how many tools?" when
they meant "how many tools does SRMECH OWN?".

THE NULL THIS RC IS BUILT ON — READ IT BEFORE EDITING ANY COUNT PIN
===================================================================
srmech's ~74 registry count assertions across ~67 files are **CORRECT and must
not be touched.** The measured owner census is a single key, ``{'srmech': N}``,
and nothing in srmech's suite or CI activates a profile, so

    len(get_tool_schema().tools) == len(get_tool_schema().by_owner("srmech"))

**identically**. Repointing those pins would edit 66 files, re-derive ~74
constants, fix zero live defects, and risk writing a wrong constant that CI
cannot catch precisely because the right and wrong values coincide today.

So the honest framing is NOT "srmech's gates are wrong". It is: **a small
number of gates measure on the wrong AXIS, which breaks any downstream consumer
that registers a profile and runs srmech's suite** — and it was true for 8
places, not 74. This module is the gate for those 8, plus the one genuine
product defect (the ``.mcpb`` attestation).

WHY THE SUITE COULD NOT SEE ANY OF THIS
=======================================
Because owned == total, a wrong-axis gate and a correct one are
indistinguishable by running the suite. ``tests/_profile_probe.py`` supplies the
one bit of state that tells them apart. Every assertion below is written as
``before == during == after`` around a live probe registration, so it cannot be
satisfied by an expression that merely stopped measuring.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import pytest

from srmech.introspect.tool_schema import RESERVED_OWNERS, get_tool_schema
from tests._profile_probe import PROBE_NAME, probe_registered

_SRMECH_PKG = Path(__file__).resolve().parents[1] / "srmech"

#: Python modules under ``srmech/`` that are GENERATED, not hand-written. Their
#: text is derived from ``ToolEntry`` prose + the C claim ledger, so a cardinal
#: appearing there is an artifact of its source, not hand-authored rot, and the
#: fix belongs upstream in the generator. Verified to exist by
#: ``test_the_generated_file_exemptions_all_exist`` so a rename cannot silently
#: widen the exemption into a hole.
_GENERATED_MODULES = (
    "introspect/_tool_docs.py",
    "introspect/_tool_docs_curated.py",
    "introspect/_c_claims.py",
)


def _owned_total() -> int:
    return len(get_tool_schema().by_owner("srmech"))


def _hand_written_modules() -> list[Path]:
    exempt = {(_SRMECH_PKG / rel).resolve() for rel in _GENERATED_MODULES}
    return [
        p
        for p in sorted(_SRMECH_PKG.rglob("*.py"))
        if "__pycache__" not in p.parts and p.resolve() not in exempt
    ]


#: Minimum element count for an all-numeric container literal to read as a DATA
#: TABLE rather than as a quantity wearing a container. Three is the smallest
#: width at which "this is a list of numbers" is unmistakable; below it,
#: ``_SHAPE = (569,)`` or ``_BOUNDS = [0, 569]`` are still plainly restatements
#: of a count and stay in scope. Pinned by ``test_the_restatement_scan_still_bites``
#: from BOTH sides.
_TABLE_MIN_ELEMENTS = 3


def _numeric_literal(node: ast.AST) -> Optional[float]:
    """The value of ``node`` if it is a NUMERIC literal, else ``None``.

    ``bool`` is excluded deliberately: ``True`` is an ``int`` to Python but is
    never an element of a numeric table, and admitting it would let
    ``(True, False, 569)`` read as one.

    A leading sign is part of the literal (``-1`` in a coefficient table), so a
    unary ``+``/``-`` over a numeric constant is unwrapped. That is NEGATION of
    a syntax node, not magnitude: nothing here erases a sign, so the Class-K
    pin-slot discipline is untouched.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return None
        if isinstance(node.value, (int, float)):
            return float(node.value)
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        inner = _numeric_literal(node.operand)
        if inner is None:
            return None
        return -inner if isinstance(node.op, ast.USub) else inner
    return None


def _table_element_lines(source: str, path: str, total: int) -> Dict[int, int]:
    """Map line number -> how often ``total`` appears there AS A TABLE ELEMENT.

    An ``ast`` walk, so the decision is STRUCTURAL: a tuple / list / set
    literal all of whose elements are numeric literals is a data table, and an
    integer inside one means "the k-th entry", not "the registry total". A
    syntax error yields ``{}``, which subtracts nothing — the scan then applies
    unmodified, which is the fail-LOUD direction.
    """
    covered: Dict[int, int] = {}
    try:
        tree = ast.parse(source, path)
    except SyntaxError:
        return covered
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            continue
        values = [_numeric_literal(e) for e in node.elts]
        if len(values) < _TABLE_MIN_ELEMENTS or any(v is None for v in values):
            continue
        for element, value in zip(node.elts, values):
            if value == float(total):
                covered[element.lineno] = covered.get(element.lineno, 0) + 1
    return covered


def _restatement_lines(source: str, path: str, total: int) -> List[int]:
    """Line numbers where ``total`` is RESTATED as a count.

    The base scan stays a word-bounded TEXT scan over every line, because all
    three cardinals rc410 struck lived in PROSE — two in docstrings, one in a
    ``#`` comment — and an ``ast`` walk over integer constants would have found
    none of them. What the ``ast`` supplies is a SUBTRACTION: occurrences the
    syntax proves are elements of a numeric table are not restatements, so they
    are deducted per line rather than the line being skipped. A line therefore
    still fails if it carries one more occurrence than the table accounts for.
    """
    pattern = re.compile(rf"\b{re.escape(str(total))}\b")
    covered = _table_element_lines(source, path, total)
    return [
        i
        for i, line in enumerate(source.splitlines(), start=1)
        if len(pattern.findall(line)) > covered.get(i, 0)
    ]


# ──────────────────────────────────────────────────────────────────────
# The predicate itself
# ──────────────────────────────────────────────────────────────────────


def test_the_two_spellings_of_srmech_owned_agree() -> None:
    """``by_owner("srmech")`` and the ``RESERVED_OWNERS`` membership test are
    used interchangeably across this rc's changes. They agree today because
    ``RESERVED_OWNERS == {"srmech"}``. If that set ever grows, the two spellings
    diverge silently and half the fixes below would quietly change meaning —
    so pin the agreement rather than assume it."""
    schema = get_tool_schema()
    by_owner = [t.name for t in schema.by_owner("srmech")]
    by_reserved = [t.name for t in schema.tools if t.owner in RESERVED_OWNERS]
    assert by_owner == by_reserved, (
        "the two spellings of 'srmech's own' disagree — RESERVED_OWNERS has "
        f"probably grown beyond {{'srmech'}} (it is {sorted(RESERVED_OWNERS)}). "
        "Every filter this rc introduced must then be re-read deliberately."
    )


def test_the_probe_actually_moves_the_unfiltered_total() -> None:
    """NON-VACUITY GUARD for every other test in this file.

    If the probe stopped registering, all the invariance assertions below would
    pass trivially. This one fails in that case: it asserts the UNFILTERED total
    DOES move, which is the whole reason the filtered one must not.
    """
    before = len(get_tool_schema().tools)
    with probe_registered():
        during = len(get_tool_schema().tools)
        assert PROBE_NAME in {t.name for t in get_tool_schema().tools}
    after = len(get_tool_schema().tools)
    assert during == before + 1, (
        "the probe did not reach the registry — every invariance assertion in "
        "this module is vacuous until this passes"
    )
    assert after == before, "the probe leaked out of its context manager"


# ──────────────────────────────────────────────────────────────────────
# A1 — the .mcpb attestation (the only SILENT wrong answer in the set)
# ──────────────────────────────────────────────────────────────────────


def test_the_mcpb_attestation_speaks_only_for_srmech() -> None:
    """FAILS BEFORE (rc409): ``tool_count`` 556 -> 557 and
    ``tool_schema_sha256`` changes, inside a block stamped
    ``parser_version: "srmech <version>"``.

    This is the one item on the rc410 list that is not a test failure. It
    escapes the process as a shipped, signed-looking MPM attestation asserting a
    third party's tool surface as srmech's own — and it is **not re-verifiable**,
    which is the specific property the MPM discipline exists to guarantee: a
    consumer re-running the hash against a plain ``pip install srmech`` could
    never reproduce it.
    """
    from srmech.mcp._mcpb import _owned_tool_schema, build_manifest
    from srmech.mcp._tools import tool_entries_to_mcp_defs

    before = build_manifest()["attestation"]
    with probe_registered():
        during = build_manifest()["attestation"]
    after = build_manifest()["attestation"]

    for key in ("tool_count", "tool_schema_sha256", "tool_schema_version"):
        assert during[key] == before[key] == after[key], (
            f"a profile-owned row moved attestation[{key!r}]: "
            f"{before[key]!r} -> {during[key]!r}. The attestation may only "
            "speak for rows srmech OWNS."
        )

    # rc414 (`#T1092`) — this read ``== _owned_total()``, and that was correct
    # only while EXCLUSION WAS IMPOSSIBLE. ``owned_def_count`` in _mcpb.py is
    # owned AND ADVERTISED; ``_owned_total()`` is owned, full stop. The two
    # coincided for every release up to rc413 because ``mcp_callable=False``
    # had zero entries tree-wide, so no srmech-owned row was ever un-advertised.
    #
    # rc414 excludes ``srmech.introspect.publish`` (a with-block scope cannot
    # span two JSON-RPC calls), and the two bases separate by exactly that one
    # row. The PRODUCTION code is right: an attestation that counted a tool the
    # server will not serve would be a false MPM claim, which is the very
    # failure this test exists to prevent. So the assertion is re-derived on the
    # attestation's own basis rather than on the registry's.
    #
    # Both halves are derived live — no literal, and the SECOND half is what
    # keeps this honest: asserting only ``<= _owned_total()`` would pass if the
    # attestation silently counted nothing.
    owned = {t.name for t in _owned_tool_schema().tools}
    owned_and_advertised = sum(
        1 for d in tool_entries_to_mcp_defs() if d["name"] in owned)
    assert during["tool_count"] == owned_and_advertised, (
        f"attestation tool_count {during['tool_count']} != the owned AND "
        f"advertised count {owned_and_advertised}. The attestation vouches for "
        f"what srmech OWNS and SERVES; counting an owned-but-excluded row "
        f"would assert a tool the server does not offer."
    )
    excluded_owned = _owned_total() - owned_and_advertised
    assert excluded_owned == sum(
        1 for t in _owned_tool_schema().tools if not t.mcp_callable), (
        "the gap between the owned registry and the owned+advertised "
        "attestation is not accounted for by mcp_callable=False rows"
    )


def test_the_advertised_surface_still_includes_profile_tools() -> None:
    """The COUNTERPART to the test above — and the reason this rc is not a
    blanket "filter everything by owner".

    ``tools[]`` is the spec-mandated description of what the server actually
    serves, and it really will serve an active profile's tools. Filtering it
    would make the manifest wrong in the spec's own terms. The attestation is a
    different claim with a different scope. Pinning both directions keeps a
    later reader from "tidying" one into the other.
    """
    from srmech.mcp._mcpb import build_manifest

    before = build_manifest()
    with probe_registered():
        during = build_manifest()
    assert len(during["tools"]) == len(before["tools"]) + 1
    assert PROBE_NAME in {t["name"] for t in during["tools"]}
    assert during["attestation"]["tool_count"] == len(before["tools"])


def test_the_owner_filter_is_a_byte_level_noop_on_a_clean_registry() -> None:
    """THE REGRESSION PROOF for A1.

    The attestation hash is a published, ratcheted value (the rc184 C
    hash-ratchet locks the C const table against this exact pre-image). A fix
    that changed it on a clean tree would be a silent breaking change dressed as
    a bug fix. Byte equality — not hash equality — because the hash is the thing
    under test.
    """
    from srmech.mcp._mcpb import _owned_tool_schema

    unfiltered = json.dumps(
        get_tool_schema().to_jsonable(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    filtered = json.dumps(
        _owned_tool_schema().to_jsonable(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assert filtered == unfiltered, (
        "the owner filter changed the attestation pre-image on a CLEAN "
        "registry. It must be a no-op there — owned == total when no profile "
        "is active, and the emitted hash is ratcheted."
    )


# ──────────────────────────────────────────────────────────────────────
# A2 — the C-table count basis
# ──────────────────────────────────────────────────────────────────────


def test_the_c_table_count_basis_is_owner_filtered() -> None:
    """FAILS BEFORE: ``test_generated_table_declares_every_entry`` reads N+1
    live while the artifact correctly holds N, and reports staleness that does
    not exist.

    Post-rc409 the generator REFUSES to emit a profile-owned row, so owner
    purity is an ENFORCED write-side invariant of the artifact. Comparing it
    against an unfiltered live count is a basis mismatch.
    """
    from tests.test_tool_registry_c_rc184 import _owned_entry_count

    before = _owned_entry_count()
    with probe_registered():
        during = _owned_entry_count()
    after = _owned_entry_count()
    assert before == during == after == _owned_total()


# ──────────────────────────────────────────────────────────────────────
# A3 — the op-name SET witness (the strongest gate in the tree)
# ──────────────────────────────────────────────────────────────────────


def test_the_op_name_set_witness_is_owner_filtered() -> None:
    """FAILS BEFORE: ``test_the_live_name_SET_matches_the_manifest`` reports
    ``added(1): ['<probe>.op']`` — a false RENAME report.

    Note this one is NOT reachable by repointing a count constant: the SET
    assertion fires before the count assertion, so ``EXPECTED_N`` never gets a
    say. That is also why the gate is worth protecting — it catches same-count
    renames that no count pin can see.
    """
    from tests.test_op_name_set_witness_rc361 import EXPECTED_N, _live_names

    before = _live_names()
    with probe_registered():
        during = _live_names()
    after = _live_names()
    assert before == during == after
    assert PROBE_NAME not in during
    assert len(during) == EXPECTED_N


# ──────────────────────────────────────────────────────────────────────
# K5 — the prior, WRONG answer to exactly this question
# ──────────────────────────────────────────────────────────────────────

_NAME_PREFIX_AXIS = re.compile(r'startswith\(\s*["\']test\.["\']\s*\)')


def test_no_test_file_filters_srmech_s_own_tools_by_name_prefix() -> None:
    """STRICT ZERO, no exemptions.

    Six count gates filtered "srmech's own tools" by excluding names that BEGIN
    WITH ``test.`` — a name-prefix answer to an OWNER question. They carried
    justifying docstrings, so they read as already fixed, and anyone grepping
    for the literal count would have rewritten the number and left the axis
    broken.

    (The offending call is deliberately not spelled out anywhere in this file:
    this gate is strict-zero with NO exemption list, and an exemption for "the
    test that documents the pattern" is the first hole every such ratchet
    acquires.)

    The prefix was neither necessary nor sufficient: the two ``test.*``
    injections in ``test_tool_schema.py`` are owner ``"srmech"`` and have been
    ``try``/``finally``-protected since rc409 (so they do not leak), while the
    one genuinely unprotected leak in that file registered owner ``"gamma"``
    — whose names a ``test.`` prefix test does not match at all.
    """
    tests_dir = Path(__file__).resolve().parent
    offenders = [
        f"{p.name}:{i}"
        for p in sorted(tests_dir.glob("*.py"))
        for i, line in enumerate(
            p.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _NAME_PREFIX_AXIS.search(line)
    ]
    assert not offenders, (
        "a test filters srmech's own tools by NAME PREFIX instead of by "
        f"owner: {offenders}. Use get_tool_schema().by_owner('srmech')."
    )


# ──────────────────────────────────────────────────────────────────────
# K8 — shipped prose cardinals
# ──────────────────────────────────────────────────────────────────────


def test_the_generated_file_exemptions_all_exist() -> None:
    """An exemption naming a file that does not exist is a silent hole. If a
    generated module is renamed, this fails rather than quietly widening the
    scan's blind spot."""
    missing = [rel for rel in _GENERATED_MODULES if not (_SRMECH_PKG / rel).exists()]
    assert not missing, f"generated-file exemptions no longer exist: {missing}"


def test_no_shipped_module_restates_the_registry_total() -> None:
    """The registry total was written as a literal into THREE shipped modules —
    ``mcp/_tools.py``, and ``introspect/__init__.py`` twice. These travel inside
    the wheel and reach users through ``describe()`` and the MCP tool list.

    The first was self-refuting in adjacent sentences: it stated the total as a
    literal and then promised "the COUNT is no longer stated here, so it cannot
    go stale again". rc409 set the precedent for stripping exactly this rot from
    ``gen_tool_registry.py:10``.

    ⚠️ BRITTLENESS, NAMED (rc410): this scanned for the CURRENT total as a
    word-bounded number. At rc410 that was a 3-digit value with no legitimate
    use as a constant in hand-written srmech source. The note said: should the
    total ever land on a value that IS a common constant, this gate will start
    reporting false positives — and it will do so LOUDLY, which is the correct
    failure mode. **Re-scope it then; do not add blanket exemptions to quiet
    it.**

    THE PREDICTION CAME TRUE AT rc419 (`#T1110`), AND THIS IS THE RE-SCOPE
    =====================================================================
    rc419's nine ``signal_processing`` registrations moved the total to
    **569, which is prime** — so it appears in ``apokatastasis/thetasum.py``'s
    ``_STRUCT_PRIMES``, a 113-entry table of the primes up to 617, between 563
    and 571. Nothing there restates anything; the total merely landed on a
    value with a legitimate life of its own. One offender, exactly the
    predicted shape.

    THE RE-SCOPE, AND WHY IT IS NOT AN EXEMPTION
    ============================================
    No file is named, no line is named, no substring is skipped, and no
    ``noqa`` exists. The gate now distinguishes the two cases by SYNTAX:

    * a **restatement** is the number standing alone as a quantity — an
      assignment, a comparison, a default argument, an f-string, or a sentence
      of prose that says how many there are;
    * a **table element** is an integer inside a tuple / list / set literal
      whose elements are ALL numeric literals, where its meaning is its
      POSITION in a data table.

    ``_restatement_lines`` keeps the word-bounded text scan — which is what
    catches prose, and all three cardinals rc410 struck WERE prose (two
    docstrings and a ``#`` comment; an ``ast`` walk over integer constants
    would have found none of them) — and subtracts, per line, the occurrences
    the ``ast`` proves are table elements. A line carrying one more occurrence
    than the table accounts for still fails.

    ``test_the_restatement_scan_still_bites`` pins that this still bites, from
    both sides.
    """
    total = _owned_total()
    offenders = [
        f"{p.relative_to(_SRMECH_PKG).as_posix()}:{i}"
        for p in _hand_written_modules()
        for i in _restatement_lines(
            p.read_text(encoding="utf-8"), str(p), total
        )
    ]
    assert not offenders, (
        f"the registry total ({total}) is restated as a literal in shipped "
        f"source: {offenders}. It ships in the wheel and goes stale on the "
        "next op added. Point at the live value instead: "
        "len(get_tool_schema().by_owner('srmech'))."
    )


def test_the_restatement_scan_still_bites() -> None:
    """⚠️ NEGATIVE CONTROL for the re-scope above.

    A gate that stopped firing on the thing it exists for is worse than the
    false positive that prompted the re-scope, and this tree has shipped that
    failure before. So the predicate is driven directly, over sources written
    HERE, and must decide both ways:

    * MUST FIND every shape a restatement actually takes — including the two
      that the real defect took (a docstring sentence and a ``#`` comment),
      which is why the base scan is still a text scan and not an ``ast`` walk
      over integer constants;
    * MUST NOT FIND the same integer sitting in a numeric data table, which is
      the rc419 false positive.

    The subject is the shipped helper, not a re-implementation of it.
    """
    total = _owned_total()

    must_find = {
        "assignment": f"_TOTAL = {total}",
        "comparison": f"assert n == {total}",
        "default argument": f"def f(n: int = {total}) -> None: ...",
        "f-string": f'msg = f"{{n}} of {total} ops"',
        "comment prose": f"# the registry carries {total} ops",
        "docstring prose": f'"""The registry carries {total} ops."""',
        "narrow container": f"_SHAPE = ({total},)",
        "extra occurrence on a table line": (
            f"_T = (2, {total}, 3)  # {total} of them"
        ),
    }
    for label, src in must_find.items():
        assert _restatement_lines(src, f"<{label}>", total) == [1], (
            f"the re-scoped scan no longer bites on a {label} restatement "
            f"({src!r}) — it has become decorative, which is strictly worse "
            f"than the false positive it was re-scoped to remove"
        )

    must_not_find = {
        "tuple of ints": f"_PRIMES = (563, {total}, 571)",
        "list of ints": f"_T = [563, {total}, 571]",
        "set of ints": f"_S = {{563, {total}, 571}}",
        "signed / float table": f"_C = (-1, {total}, 2.5)",
        "nested table": f"_N = [[1, 2, 3], [563, {total}, 571]]",
    }
    for label, src in must_not_find.items():
        assert _restatement_lines(src, f"<{label}>", total) == [], (
            f"the re-scoped scan still fires on a {label} ({src!r}) — the "
            f"rc419 false positive is not actually fixed"
        )

    # …and the real exhibit, read from the shipped file rather than described.
    #
    # rc420 RE-SCOPE (`#T1114`): the total moved off a prime (569 -> 598 =
    # 2·13·23), so the rc419 exhibit — "the CURRENT total sits inside
    # thetasum's prime table and the AST accounts for it" — predicted its own
    # expiry ("the exhibit must be re-chosen"). The re-choice keeps BOTH
    # halves live with neither branch a skip:
    #
    #   * when the current total IS in the shipped prime table (a prime
    #     <= 617), the original exhibit runs unchanged: present AND silent;
    #   * when it is NOT, that absence is asserted as a definite fact (the
    #     main gate then has no table false-positive to fear for this file)
    #     AND the AST-subtraction path is still exercised against the LIVE
    #     file by scanning for 569 — the rc419 value known to sit in
    #     _STRUCT_PRIMES — so the "silent because accounted, not because the
    #     scan stopped looking" property keeps a real shipped exhibit at all
    #     times, whatever the current total is.
    thetasum = _SRMECH_PKG / "apokatastasis" / "thetasum.py"
    source = thetasum.read_text(encoding="utf-8")
    if re.search(rf"\b{total}\b", source):
        assert _restatement_lines(source, str(thetasum), total) == [], (
            f"thetasum.py contains {total} inside _STRUCT_PRIMES and the "
            f"AST no longer accounts for it — the rc419 false positive is "
            f"back"
        )
    else:
        # The definite complementary fact + the live AST exhibit at 569.
        assert re.search(r"\b569\b", source), (
            "thetasum.py no longer contains 569 (_STRUCT_PRIMES changed) — "
            "re-choose the live exhibit value for this branch"
        )
        assert _restatement_lines(source, str(thetasum), 569) == [], (
            "the AST table-subtraction no longer silences thetasum's prime "
            "table for a value KNOWN to be a table element — the re-scope "
            "has regressed"
        )


# ──────────────────────────────────────────────────────────────────────
# K9 — a failing test must not leak rows into every later test
# ──────────────────────────────────────────────────────────────────────


def test_a_failing_unregister_test_cleans_up_after_itself() -> None:
    """FAILS BEFORE: 2 rows leak, so ONE genuine defect is reported as THREE
    failures — the real one plus two later count assertions reading N+2 and
    naming unrelated modules.

    ``test_unregister_profile_tools_removes_all`` registered two profile rows
    and then asserted BEFORE the only call that removes them. Under CI's
    ``--dist load`` the collateral set is worker-dependent, so the noise is not
    even reproducible.

    This drives the real test function through its own failure path rather than
    re-implementing it, so the subject under test is the shipped one.
    """
    import srmech.introspect.tool_schema as ts
    from srmech.introspect.tool_schema import ToolSchema

    import tests.test_tool_schema as tts

    snapshot = dict(ts._REGISTRY)
    original = ToolSchema.by_owner
    try:
        # Induce a genuine-looking defect: by_owner lies once, so the FIRST
        # assertion in the test body fails — before any cleanup could run.
        ToolSchema.by_owner = lambda self, owner: ()  # type: ignore[assignment]
        with pytest.raises(AssertionError):
            tts.test_unregister_profile_tools_removes_all()
        ToolSchema.by_owner = original  # type: ignore[assignment]

        leaked = sorted(set(ts._REGISTRY) - set(snapshot))
        assert not leaked, (
            f"a failing test leaked {leaked} into the process-global registry. "
            "Every later count assertion in the same worker now reads "
            f"+{len(leaked)} and fails for a reason that has nothing to do "
            "with it. Wrap the body in try/finally."
        )
    finally:
        ToolSchema.by_owner = original  # type: ignore[assignment]
        ts._REGISTRY.clear()
        ts._REGISTRY.update(snapshot)
