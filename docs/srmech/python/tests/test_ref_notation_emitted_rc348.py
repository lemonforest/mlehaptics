"""rc348 (`#T986`) — the EMITTED-ARTIFACT reference-notation ratchet.

A bare ``#NNN`` in prose becomes a live GitHub hyperlink to whatever object
happens to hold that number. Local task IDs and this repo's issue numbers
occupy the same numeric range, so the collision is routine: ``#938`` written
as a local task renders as *"srmech v0.7.5rc13: numpy-math ratchet + lmmse
-> cascade"*, an unrelated merged PR.

**This is the class of defect no assertion could fail on.** A bare ref is
valid text that nothing computes over, so it survives every existing gate --
which is why it went undetected for many rcs. Measured at rc348: **15 such
false links had already SHIPPED inside published wheels** (``_tool_docs.py``
5, ``_c_claims.py`` 1, ``srmech_tool_registry.c`` 9), reaching users through
``describe()``, the MCP tool list and the compiled-in C registry.

WHY THIS GUARDS THE EMITTED ARTIFACTS AND NOT THE SOURCES
=========================================================
The convention itself is documented for humans and agents in the root
``CLAUDE.md`` ("Issue-reference notation"); rc348 established that its
absence from every readable doc -- not indiscipline -- was the root cause.
Documentation is the primary control. This test is the LAST line of
defence, and it is deliberately scoped to the files that physically ship:
a bad ref authored upstream in a docstring or a ``ToolEntry`` summary is
caught here at the next ``regen-all``, which is strictly before it can
reach a wheel. Policing the sources as well would be style enforcement on
text the documentation already covers.

THE THREE FORMS (root ``CLAUDE.md``)
====================================
====================  ==================================================
``gh #1293``          a real GitHub issue/PR in this repo
``#T986``             a LOCAL task-tracker item (NOT GitHub)
``#986``              NEVER -- autolinks onto an unrelated real issue
====================  ==================================================

WHAT IS PINNED, AND WHY THE SPLIT
=================================
1. **STRICT ZERO -- a known local task ID written bare.** This is the exact
   defect that shipped, and it is decidable WITHOUT reading prose: if the
   tree writes a number as ``#TNNN`` anywhere, that number is a local task
   ID, so the same number written bare in an emitted artifact is a false
   link by construction. Zero today; zero is the contract.

2. **DOWN-ONLY CEIL -- every other bare ref.** The residual population is
   real GitHub refs that predate the convention and still want their ``gh``
   prefix. They are NOT batch-convertible: "existence proves nothing,
   topicality decides", and a wrongly-converted working link is worse than
   an unconverted one because it looks deliberate. So the count is pinned
   and may only fall. A NEW bare ref fails the build and the author writes
   ``gh #NNNN`` (or ``#TNNN``) instead -- which is how the residual drains.

``CHANGELOG.md`` IS DELIBERATELY NOT COVERED
============================================
It holds ~360 bare refs across ~113 distinct numbers in the region the
``pypi-readme-changelog`` markers slice into the PyPI long-description.
Every one needs individual topicality adjudication against ``gh issue view``
before it can be converted, so it is tracked separately as **task T991**
rather than swept. It is still read as a SOURCE for the local-task-ID set
below (it is where ``#TNNN`` is most reliably written), just never checked
as a surface. This exclusion is intentional; it is not an oversight.
"""

from __future__ import annotations

import functools
import re
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SR_ROOT = _HERE.parent.parent          # docs/srmech
_TOOLS = _SR_ROOT / "python" / "tools"

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import codegen_manifest as cm  # noqa: E402


#: A ref token: ``#`` + digits, NOT already ``#T``-prefixed, and not the tail
#: of a longer word or of another ``#``-token. The ``gh `` prefix is checked
#: separately against the preceding text so that ``gh #1293`` is accepted
#: while a bare ``#1293`` on the same line is not.
#:
#: THREE-TO-FOUR DIGITS, and that bound is load-bearing rather than lazy.
#: This repo's issues/PRs run ~100-1530 and every local task ID minted so
#: far is three digits, so 3-4 digits IS the colliding range -- the only
#: range where "is this a task or an issue?" is a real question. Shorter
#: tokens are never refs in this tree and are provably other things:
#: ``UAX #29`` / ``UAX #15`` (Unicode Annex names), ``MS #20`` (milestone),
#: ``Spike #24``, ``F292 graft #1``. Bounding the DIGIT COUNT removes all
#: of them structurally, which is why there is no hand-maintained
#: exemption list here -- an earlier draft had one and it silently failed
#: to match ``UAX #29`` anyway.
_REF = re.compile(r"(?<![\w#])#(\d{3,4})(?!\d)")

# ── WHAT THIS DELIBERATELY EXEMPTS, AND WHY -- DO NOT "SIMPLIFY" ──────
#
# Three bad ref-greps were written during the rc348 session alone (wrong
# symbol prefix, wrong file path, and a version that missed the code-span
# case and went red on the changelog entry describing the fix). The
# exemptions below are each load-bearing; removing one produces a guard
# that fails on correct text, and a guard that cries wolf gets suppressed.
#
#   1. ``gh #1293``   -- the documented form for a real GitHub object.
#   2. ``#T986``      -- the documented form for a local task.
#   3. `` `#938` ``   -- a markdown/RST CODE SPAN. GitHub does NOT autolink
#                        inside a code span, so quoting a bad ref in order
#                        to DOCUMENT it is correct and must stay legal.
#                        This tree's prose quotes refs constantly, in both
#                        `single` and ``double`` backtick style.
#   4. ``UAX #29``    -- handled STRUCTURALLY by the 3-4 digit bound above,
#                        not by a list that has to be kept up to date.
#
# Only an UNQUOTED, UNPREFIXED ``#NNN`` is a violation.
#
# FENCED code blocks (```) are NOT handled, and that is a measured
# decision rather than an omission: all six covered artifacts contain
# ZERO fence markers (they are generated .py/.c, not markdown). Should a
# future generator emit fenced prose, fence-awareness must be added here.

#: A correctly-spelled local task ref, used to DERIVE the task-ID set.
_TREF = re.compile(r"(?<![\w#])#T(\d+)(?!\d)")

def _emitted_artifacts() -> "list[Path]":
    """The regen-all OUTPUT set, DERIVED from the manifest.

    Derived rather than listed so a seventh generator cannot ship an
    unguarded artifact: whatever ``regen-all`` writes is covered the moment
    it is declared.
    """
    return [_SR_ROOT / g.output for g in cm.GENERATORS]


@functools.lru_cache(maxsize=1)
def _local_task_ids() -> "frozenset[int]":
    """Every number the tree writes CORRECTLY as ``#TNNN``.

    Read from the whole srmech tree -- including ``CHANGELOG.md``, which is
    excluded as a checked SURFACE but is the most reliable SOURCE of the
    task-ID vocabulary.
    """
    ids: set[int] = set()
    for path in _SR_ROOT.rglob("*"):
        # PROSE suffixes only. ``.ndjson`` is deliberately excluded: those
        # are machine-written findings dumps (the largest is 14 MB, and they
        # dominated this test's runtime), and they were MEASURED to
        # contribute exactly zero `#TNNN` tokens -- the derived set is
        # byte-identical with and without them.
        if not path.is_file() or path.suffix not in {
                ".py", ".c", ".h", ".md", ".toml"}:
            continue
        if "__pycache__" in path.parts or "worktrees" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:                                    # pragma: no cover
            continue
        ids.update(int(n) for n in _TREF.findall(text))
    return frozenset(ids)


def _in_code_span(line: str, start: int, end: int) -> bool:
    """True when the ref at ``[start:end)`` sits inside a backtick code span.

    GitHub does not autolink inside a code span, so `` `#938` `` is the
    CORRECT way to quote a bad ref while documenting it. Two shapes are
    recognised because this tree uses both:

      * IMMEDIATE wrap -- `` `#938` `` and RST's `` ``#938`` ``. Checking
        the adjacent characters handles the double-backtick form, which a
        naive backtick COUNT gets wrong (two leading backticks read as
        "even", i.e. outside, when the ref is plainly inside).
      * ENCLOSING span -- ``a #938 b``, where the ref sits mid-span. Here
        an odd number of backticks before the ref means "inside".
    """
    if start > 0 and line[start - 1] == "`" and line[end:end + 1] == "`":
        return True
    return line[:start].count("`") % 2 == 1


def _bare_refs(path: Path) -> "list[tuple[int, int, str]]":
    """Every bare ref in ``path`` as ``(lineno, number, line)``.

    A ref is BARE when it is neither ``gh #NNN`` nor ``#TNNN``.
    """
    out: list[tuple[int, int, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in _REF.finditer(line):
            if line[:m.start()].endswith("gh "):
                continue                                   # a real GitHub ref
            if _in_code_span(line, m.start(), m.end()):
                continue                                   # `#938` -- quoted
            out.append((lineno, int(m.group(1)), line.strip()[:100]))
    return out


# ── the pinned residual ───────────────────────────────────────────────
#
# MEASURED on the rc348 branch, not guessed. These are pre-convention real
# GitHub refs still awaiting their `gh ` prefix; each drains by individual
# topicality adjudication, never by a sweep. DOWN-ONLY: lowering a number
# here is always correct; RAISING one is a defect unless the added ref is
# provably a real GitHub object AND could not be written `gh #NNNN`.
CEIL_BARE_REFS_EMITTED = {
    # rc353 (`#T1006`) STANDING NOTE — READ BEFORE LOWERING THESE TWO.
    # The worked-example curation arc rewrites hundreds of auto-seeded
    # explanations, so these two numbers move on every regeneration until the
    # arc lands, and the NET can hide moves in OPPOSITE directions. Measured
    # mid-arc by diffing the emitted refs against HEAD rather than trusting
    # the total (75 -> 74 at that instant):
    #   DRAINED 3 — #1407 (x2) and #1245, carried by stale genome auto-seeds
    #     that regeneration simply re-derived away. Nobody swept refs; the
    #     tree had not been regenerated since those docstrings moved.
    #   ADDED 2 — #447 and #460, newly EMITTED by worked-example curation on
    #     `rational.exp_series_truncate` / `rational.pi_cascade_digits`.
    # The two ADDED refs are NOT adjudicated. They pass the strict-zero rule
    # (neither number is spelled `#TNNN` anywhere in the tree, so neither is a
    # decidable local-task ID) and so ride as pre-convention residual pending
    # topicality review — read the surrounding prose, never batch-convert.
    # Recorded here because a net "-1" would otherwise bury them.
    #   CLASS-L family (56 laplacian ops) measured against HEAD the same way:
    #     DRAINED 27 from _tool_docs.py, ADDED 0. All 27 were auto-seed
    #     carry-through from the laplacian docstrings — #1390 (x6), #564 (x6),
    #     #897 (x3), #1234 (x2), #1097 (x2), #741, plus #1-#5 which are the
    #     "issue #NNNN Item 3" style false positives the same docstrings carry.
    #     Curation replaced every one of those explanations, so the laplacian
    #     category now emits ZERO bare refs. Nothing was adjudicated and nothing
    #     was swept; the refs left with the text that carried them.
    #   rc353 DELIVERABLE ASSEMBLY — the ten-family measurement, and the
    #   topicality review this note left PENDING is now DONE. Measured against
    #   HEAD by ref MULTISET (not by total), both artifacts identically:
    #     _tool_docs.py          75 -> 48   (DRAINED 31, ADDED 4)
    #     srmech_tool_registry.c 199 -> 172 (DRAINED 31, ADDED 4)
    #   The net -27 hides the four additions exactly as this note predicted.
    #   ADDED, each adjudicated by reading the surrounding prose:
    #     #447 gh MERGED "Spike #28 — falsify infinity + asymptotic_calculus
    #          catalog" <- rational.exp_series_truncate cites it as the catalog
    #          seed. TOPICAL. Should be written `gh #447` in the upstream prose.
    #     #460 gh MERGED "spike-32: pi spectral shape is scalar-invariant"
    #          <- rational.pi_cascade_digits cites it as the no-math.pi gate.
    #          TOPICAL. Should be written `gh #460`.
    #     #812 gh CLOSED "[srmech][glue/gauge] Loop-bind capacity
    #          characterization vs Klein-4" <- hdc.loop_bind_hd cites it for the
    #          measured capacity claim. TOPICAL. Should be written `gh #812`.
    #     #437 gh MERGED "docs(mfo): AoE / hyperbubble / dark-sector-
    #          oscillation" <- reaches the wheel through dsl.list_ops's CAPTURED
    #          OUTPUT, which quotes the cosmos_validation descriptor's own
    #          purpose string ("Spike #27 PR #437"). UPSTREAM DATA, NOT
    #          AUTHORED PROSE: editing it would fabricate a captured output.
    #          Fix at srmech/amsc/attested/cosmos_validation/descriptor.toml or
    #          leave it; do NOT touch the emitted example.
    #   THE ARC HAS NOW LANDED — rc353 close-out, 2026-07-28. The note below
    #   used to say these two "stay at 75 / 199 for now BY DESIGN … until the
    #   arc lands", because pinning a MID-arc measurement asserts as settled a
    #   count the next family's curation moves again. That condition is
    #   discharged: tests/test_worked_examples_strict_zero_rc353.py is GREEN,
    #   0 of 513 examples remain un-authored, so this is the final post-arc
    #   regen and the ratchet is lowered ONCE, here, from it.
    #   Measured against HEAD with THIS suite's own _bare_refs predicate (code
    #   spans exempt, `gh ` prefix exempt, 3-4 digit bound) by ref MULTISET —
    #   never by total, since the net hides moves in opposite directions.
    #   Both artifacts moved identically:
    #     _tool_docs.py           75 -> 7    (DRAINED 72, ADDED 4)
    #     srmech_tool_registry.c 199 -> 130  (DRAINED 72 + 1, ADDED 4)
    #   The C registry's extra -1 is NOT curation: draining the example/
    #   explanation copies of `#944` left the SUMMARY copy alone in the
    #   registry (the C artifact embeds summaries, _tool_docs.py does not) and
    #   the strict-zero test above went red on it — correctly, since the tree
    #   spells the same number `#T944` at srmech_research_notebook.md:179.
    #   ADJUDICATED by reading the prose both sides: the notebook's `#T944` is
    #   the finding "𝕆 measured to have no frame-free invariant" and the
    #   summary's is the BUILD TASK that shipped quaternion_cycle_holonomy —
    #   the same LOCAL task, no GitHub object. Fixed upstream at
    #   srmech/amsc/tool_schema.py:9682 (one character, `#944` -> `#T944`),
    #   then regenerated. HEAD carried THREE copies of this false link across
    #   the two shipped artifacts; it now carries none.
    #   DRAINED 72, every one of them auto-seed carry-through that left with
    #   the docstring text curation replaced — no ref was adjudicated and none
    #   was swept: #1390 (x8), #1248 (x7), #564 (x6), #1234 (x5), #718 /
    #   #1239 / #733 / #1407 (x4 each), #712 / #897 (x3 each), #697 / #719 /
    #   #723 / #741 / #863 / #1097 / #1273 (x2 each), and one each of #698,
    #   #726, #728, #730, #732, #736, #797, #944, #1245, #1261.
    #   ADDED 4 — exactly the four already adjudicated in the block above
    #   (#437, #447, #460, #812) and NOT one more: the final family (the 31
    #   carrier_ladder / carrier_schema / carrier_spectrum / coupling /
    #   octonion / q8 / responsion_schema / srmech.spectral entries) emitted
    #   ZERO bare refs. Their `gh ` prefixes remain the open follow-up; the
    #   #437 one is CAPTURED OUTPUT and must be fixed at
    #   srmech/amsc/attested/cosmos_validation/descriptor.toml, never in the
    #   emitted example.
    #   The two artifacts do NOT hold the same population — the C registry
    #   also embeds each op's SUMMARY, which _tool_docs.py does not — but they
    #   move together, and here they moved by exactly -68 each (the rc346
    #   measurement: bytes injected into _tool_docs.py propagate exactly into
    #   srmech_tool_registry.c).
    "python/srmech/amsc/_tool_docs.py": 7,
    "python/srmech/amsc/_c_claims.py": 0,
    # rc358 (`#T1022`): 130 -> 129. The SAME shape as the rc353 `#944` note
    # above, and the second instance of it — so treat it as the pattern, not
    # the exception. `#914` rode here as pre-convention residual because the
    # tree spelled `#T914` NOWHERE, leaving it undecidable; it is the LOCAL
    # task (all six copies read "the #914 order-discard", the rc322 §Q8-FIBER
    # Q8 storage-coupling finding), while `gh #914` is the topically
    # unrelated MERGED PR "srmech v0.7.2 - production graduation to PyPI".
    # Adjudicated by reading the prose at all six sites, not swept.
    # Converting them made 914 decidable, which is why this is ATOMIC: the
    # instant any ONE site is written `#T914`, the strict-zero test above
    # demands zero bare `#914` in the emitted artifacts, so the upstream fix
    # and the regen must land in the same commit. Only the C registry moved
    # (-1) - it embeds each op's SUMMARY, which is where the `tool_schema.py`
    # copy lives; `_tool_docs.py` carries no copy and stays at 7.
    #
    # rc358 also drains `#962` (x3), a PRE-EXISTING strict-zero RED on `main`
    # that the rc358 brief did not file - this test was already failing at
    # 6f2ca3bb5 and would have kept failing. `#T962` is spelled in the TRACKED
    # note docs/srmech/notes/t962_cwf_tw_is_not_absent.py, which makes 962
    # decidable; the naive reading is therefore "convert to `#T962`", and that
    # would have been WRONG. Adjudicated by reading the prose BOTH sides -
    # this is the `#943` collision the convention warns about, live:
    #   gh #962 = a real CLOSED issue, "srmech: genome storage perspective +
    #     native A-N binding - dev-session tracker (F708-F715, UPSTREAM
    #     §37/§38)". The three emitting sites cite exactly that ("Part 2 of
    #     #962; validated as F711-F715", "class-from-TOML surface; #962
    #     Part 2"). TOPICAL -> they are REAL GitHub refs.
    #   #T962 in the note = an unrelated LOCAL task asking whether `Tw` is
    #     algebraically absent from `cwf_consistency_mod2`. Same number,
    #     different object.
    # So the fix is the `gh ` prefix, NOT the `T` - written upstream at
    # tool_schema.py (the `rc41` string x2 emissions + the §39 make_class
    # inverse summary), which is why this drains 3 rather than converting 3.
    # 129 -> 126.
    "c/src/srmech_tool_registry.c": 126,
    # rc352: 2 -> 0. Both were the SAME pre-convention `#845`, emitted twice
    # from one upstream string (`carrier_schema.py`, the `Q` carrier
    # description). It sat here legitimately until this rc: the strict-zero
    # rule above only covers refs the tree spells `#TNNN` SOMEWHERE, and
    # nothing did until rc352's CHANGELOG cited `#T845` — at which point the
    # ref became decidable and the pair went red. Fixed upstream, one
    # character, then re-emitted. This artifact is now CLEAN; the number can
    # never go back up.
    "c/src/srmech_carrier_registry.c": 0,
    "c/src/srmech_responsion_registry.c": 0,
    "c/src/srmech_class_registry.c": 0,
}


def test_every_emitted_artifact_is_pinned() -> None:
    """A new generator cannot ship an artifact this ratchet does not cover.

    The mirror of ``test_every_generator_is_classified``: forgetting to pin
    a new output is a RED test, not a silent gap.
    """
    declared = {g.output for g in cm.GENERATORS}
    pinned = set(CEIL_BARE_REFS_EMITTED)
    assert declared == pinned, (
        "the regen-all output set and the pinned ceiling set disagree.\n"
        f"  declared but NOT pinned: {sorted(declared - pinned)}\n"
        f"  pinned but NOT declared: {sorted(pinned - declared)}\n"
        "Add the new artifact to CEIL_BARE_REFS_EMITTED with its measured "
        "count (0 for anything written after the convention landed)."
    )


def test_no_local_task_id_is_written_bare_in_an_emitted_artifact() -> None:
    """STRICT ZERO. The exact defect that shipped 15 false links.

    Decidable without reading prose: a number the tree spells ``#TNNN``
    somewhere is a local task ID, so the same number spelled bare in a file
    that ships is a false link by construction.
    """
    task_ids = _local_task_ids()
    assert task_ids, "derived no local task IDs at all - the scan is broken"

    violations: list[str] = []
    for path in _emitted_artifacts():
        rel = path.relative_to(_SR_ROOT).as_posix()
        for lineno, number, line in _bare_refs(path):
            if number in task_ids:
                violations.append(
                    f"  {rel}:{lineno}: #{number} is a LOCAL TASK ID "
                    f"(the tree writes it as #T{number}) but is written "
                    f"bare here, so it autolinks onto an unrelated GitHub "
                    f"object.\n      {line}")

    assert not violations, (
        f"{len(violations)} local task ID(s) written BARE in a SHIPPED "
        "artifact:\n" + "\n".join(violations)
        + "\n\nFix the UPSTREAM prose (a docstring, a ToolEntry summary or "
          "a generator template - not the generated file, which is "
          "overwritten), then re-run:  python3 tools/regen_all.py"
    )


@pytest.mark.parametrize("rel_path", sorted(CEIL_BARE_REFS_EMITTED))
def test_bare_ref_population_is_down_only(rel_path: str) -> None:
    """DOWN-ONLY CEIL on every other bare ref in a shipped artifact.

    The residual is pre-convention real GitHub refs. They may only ever
    decrease. A new one fails here, and the author writes ``gh #NNNN``.
    """
    path = _SR_ROOT / rel_path
    found = _bare_refs(path)
    ceiling = CEIL_BARE_REFS_EMITTED[rel_path]

    assert len(found) <= ceiling, (
        f"{rel_path}: {len(found)} bare refs, ceiling {ceiling} - the "
        f"population GREW by {len(found) - ceiling}.\n"
        "A bare `#NNN` in a shipped artifact autolinks onto whatever GitHub "
        "object holds that number. Write `gh #NNNN` for a real issue/PR or "
        "`#TNNN` for a local task, in the UPSTREAM prose, then re-run "
        "`python3 tools/regen_all.py`.\n"
        "New bare refs:\n"
        + "\n".join(f"    {ln}: #{num}  {txt}" for ln, num, txt in found[-8:])
    )

    if len(found) < ceiling:
        pytest.fail(
            f"{rel_path}: {len(found)} bare refs but the ceiling says "
            f"{ceiling}. This is GOOD NEWS - the ratchet must be lowered "
            f"to {len(found)} in CEIL_BARE_REFS_EMITTED so the gain cannot "
            f"be given back."
        )
