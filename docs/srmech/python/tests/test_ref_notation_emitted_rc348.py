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

rc359 — TWO WAYS THIS GUARD WAS ITSELF LYING
============================================
Both are the file's own theme turned on itself: a measurement surface
reporting a value it did not measure.

1. **THE DECODED PAYLOAD.** Three artifacts embed their text as decimal
   byte arrays (``{ 35, 57, 54, 50 }`` is ``#962``). The regex above reads
   integers and finds nothing, so ``srmech_class_registry.c`` pinned a
   perfectly true ``0`` while the compiled library shipped 5 bare refs a
   bare-C host reads straight out of the table. ``srmech_tool_registry.c``
   carried 3 more that nobody had filed. Fixed by a SECOND predicate with
   its own ceiling (``CEIL_BARE_REFS_DECODED``) rather than by raising the
   textual one -- the textual count was never wrong, it was counting a
   different thing, and a down-only ratchet you have to argue upward has
   stopped being a ratchet.

2. **THE TRIGGER GAP.** ``_local_task_ids`` rglobs ALL of ``docs/srmech``,
   but ``srmech-ci.yml`` only fires on ``python/**`` + ``c/**``. 846 tracked
   files -- 727 of them the high-churn ``notes/`` -- could mint a ``#TNNN``
   with no job running, and 3 of the 45 ids are decidable ONLY out there.
   Fixed by ``.github/workflows/srmech-ref-guard.yml`` (a dedicated ~1-2
   CI-min job; widening the full matrix would have cost ~213 billed min)
   plus the SCAN_ROOTS meta-test at the bottom of this file, which asserts
   the two sets cannot drift apart again.

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
# rc361: tests/ onto the path too, for the shared `c_byte_arrays` decoder.
# tests/ is a package, so pytest's prepend import-mode does not add it.
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

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
        # ⚠️ rc364 — THE EXCLUSION WAS COMPUTED ON THE ABSOLUTE PATH, AND THAT
        # MADE THIS GATE UNRUNNABLE INSIDE A WORKTREE. The intent is "skip other
        # sessions' `.claude/worktrees/` checkouts". Tested against
        # ``path.parts`` of the ABSOLUTE path, it also matched EVERY file when
        # the scan itself runs from a worktree — because ``worktrees`` is then a
        # component of the scan ROOT, not of anything below it. Result: the
        # derived task-ID set came back EMPTY and both strict-zero tests failed
        # on ``"derived no local task IDs at all - the scan is broken"``. The
        # non-vacuity assert did its job — this was loud, not silent — but the
        # gate could not go green in the environment the build discipline says
        # to build in.
        #
        # Computing the same test on the path RELATIVE to the scan root
        # preserves the intent exactly: `.claude/worktrees/` sits at the REPO
        # root, above ``docs/``, so nothing below ``docs/srmech`` can ever be a
        # worktree and the relative check can only ever fire on a genuine
        # nested one.
        rel_parts = path.relative_to(_SR_ROOT).parts
        if "__pycache__" in rel_parts or "worktrees" in rel_parts:
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
    #   srmech/introspect/tool_schema.py:9682 (one character, `#944` -> `#T944`),
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
    "python/srmech/introspect/_tool_docs.py": 7,
    "python/srmech/introspect/_c_claims.py": 0,
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
    # rc359 (`#T1035`): STAYS 0, and 0 is TRUE — for the TEXT predicate. This
    # artifact embeds its descriptors as DECIMAL BYTE ARRAYS, so the textual
    # scan above has nothing to read and reports a clean 0 while the compiled
    # library ships real bare refs inside the payload. That is not a wrong
    # count; it is a count of the wrong thing. The decoded population is pinned
    # SEPARATELY in CEIL_BARE_REFS_DECODED below rather than folded in here,
    # because merging them would force this number UP and a down-only ratchet
    # that has to be argued upward stops being a ratchet. Two predicates, two
    # ceilings, neither lying.
    "c/src/srmech_class_registry.c": 0,
}


# ── the DECODED payload — the same defect, one indirection down ───────
#
# rc359 (`#T1035`). Three of the six artifacts embed UTF-8 text as
# `static const unsigned char x[] = { 35, 32, 67, ... };`. To `_bare_refs`
# that is a wall of integers: `#962` is stored as `35, 57, 54, 50` and the
# regex never fires. The bytes still reach users — a bare-C host resolves a
# class name straight out of this table, and `describe()` surfaces the tool
# long-strings — so the text ships with exactly the autolink defect the
# textual ratchet exists to stop, while the ratchet reads green.
#
# MEASURED at rc359 across all four registry artifacts, not assumed:
#   srmech_class_registry.c      TEXT 0  DECODED 5  <- the blind spot
#   srmech_tool_registry.c       TEXT 126 DECODED 3  <- ALSO blind, unfiled
#   srmech_carrier_registry.c    TEXT 0  DECODED 0   (control: has byte arrays,
#                                                     and they are genuinely clean)
#   srmech_responsion_registry.c TEXT 0  DECODED 0   (control: no byte arrays)
# The tool-registry hits were NOT in the rc359 brief; they were found by
# running the decoder over every artifact instead of only the one filed. The
# carrier control matters as much as the finding: it proves the decoder can
# report zero, so a zero here is evidence rather than silence.
CEIL_BARE_REFS_DECODED = {
    # ADJUDICATED individually by reading the prose against `gh issue view`,
    # never swept. rc359 drained 3 of 5 from the class registry:
    #   `#962` -> `gh #962`. DECIDABLE (the tree spells `#T962`), so the
    #     strict-zero rule below REQUIRED it. gh #962 is "srmech: genome
    #     storage perspective + native A-N binding"; the prose is "Genome (the
    #     seed worked-instance)". TOPICAL — the `gh ` prefix, not the `T`.
    #   `#887` x2 -> `gh #887`. gh #887 is "The two alphabets — operator
    #     (1:3:7 cyclic) vs operand (2:4:8 spatial)"; the prose is "the
    #     substrate generator" / "the 1+3+7+3 = 14-D A–N substrate". TOPICAL.
    # LEFT BARE, deliberately, and this is the whole point of a CEIL:
    #   `#566` in genome.toml. gh #566 is "Spike #136 — Quantum computing
    #     without brute-forcing the universe"; the prose is the genome seed.
    #     Read the body: Clifford algorithms, Gottesman-Knill, T-gate density.
    #     NOT the genome. Converting it would mint a false link that looks
    #     deliberate, which is worse than leaving it.
    #   `#564` in hurwitz.toml. gh #564 is "research(MS-14 wave-2 integration):
    #     12 PRs merged + 6 stances"; the prose is "the numpy-Rosetta-peer
    #     dissolution POC". Body read: wave-2 spikes, MS #14 adapter scope.
    #     NOT the carrier arc. The rc359 research proposed converting this one;
    #     reading the issue body refuted it. Left bare on purpose.
    "c/src/srmech_class_registry.c": 2,
    # `#728` / `#729` / `#730`, one line of one long-string: "UPSTREAM §128 /
    # #728; §129 / #729 KLEIN-4 REGULATORY". None is spelled `#TNNN` anywhere,
    # so all three are pre-convention residual, not decidable. They drain by
    # individual adjudication like every other row here.
    "c/src/srmech_tool_registry.c": 3,
    "c/src/srmech_carrier_registry.c": 0,
    "c/src/srmech_responsion_registry.c": 0,
}

# rc361 (`#T1034`): the byte-array regex + decode step MOVED to
# tests/c_byte_arrays.py so the rc361 namespace-prefix ratchet
# (test_namespace_prefix_decode_aware_rc361.py) reads the payload through the
# SAME extraction this file proved out at rc359, instead of forking a second
# decoder that could drift into silently returning nothing. Behaviour here is
# unchanged — `_decoded_blobs` is the same function under the same name.
#
# `test_the_decoder_can_still_see_something` below is the non-vacuity guard for
# the shared decoder and stays HERE as well as in the rc361 file: two consumers,
# two independent shape pins, so neither gate depends on the other being run.
from c_byte_arrays import BYTE_ARRAY as _BYTE_ARRAY  # noqa: E402,F401
from c_byte_arrays import decoded_blobs as _decoded_blobs  # noqa: E402


def _bare_refs_in_text(text: str) -> "list[tuple[int, int, str]]":
    """``_bare_refs``' predicate, applied to a string instead of a file.

    Kept as the SAME rules (``gh `` prefix exempt, code spans exempt, 3-4 digit
    bound) so the decoded ceiling means the same thing as the textual one.
    """
    out: "list[tuple[int, int, str]]" = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in _REF.finditer(line):
            if line[:m.start()].endswith("gh "):
                continue
            if _in_code_span(line, m.start(), m.end()):
                continue
            out.append((lineno, int(m.group(1)), line.strip()[:100]))
    return out


def _decoded_bare_refs(path: Path) -> "list[tuple[str, int, int, str]]":
    """Every bare ref inside ``path``'s embedded byte arrays."""
    out: "list[tuple[str, int, int, str]]" = []
    for name, blob in _decoded_blobs(path):
        for lineno, number, line in _bare_refs_in_text(blob):
            out.append((name, lineno, number, line))
    return out


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


# ── rc359: the DECODED-payload pair ───────────────────────────────────

def test_the_decoder_can_still_see_something() -> None:
    """The decoder must actually decode. A seam that stops observing is a
    false green, and every assertion below would pass trivially on a decoder
    that silently returned nothing (a changed generator template, a switch to
    hex literals, a renamed array). Pin the SHAPE, not a ref count.
    """
    blobs = _decoded_blobs(_SR_ROOT / "c/src/srmech_class_registry.c")
    assert len(blobs) == 4, (
        f"expected 4 embedded [class] descriptors, decoded {len(blobs)} - the "
        "byte-array extraction has stopped matching the generator's output, "
        "so every decoded-payload assertion below is now vacuous."
    )
    names = {n for n, _ in blobs}
    assert names == {"cls_desc_0", "cls_desc_1", "cls_desc_2", "cls_desc_3"}
    joined = "\n".join(t for _, t in blobs)
    assert "[class]" in joined and "Genome" in joined, (
        "the decoded blobs no longer look like TOML [class] descriptors"
    )


def test_no_local_task_id_is_written_bare_in_a_DECODED_payload() -> None:
    """STRICT ZERO, one indirection down.

    The same rule as the textual strict-zero test, applied to text the
    artifacts carry as byte arrays. A `#962` stored as `35, 57, 54, 50` is
    still `#962` by the time a user reads it.
    """
    task_ids = _local_task_ids()
    assert task_ids, "derived no local task IDs at all - the scan is broken"

    violations: list[str] = []
    for path in _emitted_artifacts():
        rel = path.relative_to(_SR_ROOT).as_posix()
        for arr, lineno, number, line in _decoded_bare_refs(path):
            if number in task_ids:
                violations.append(
                    f"  {rel} [{arr}]:{lineno}: #{number} is a LOCAL TASK ID "
                    f"(the tree writes it as #T{number}) but is written bare "
                    f"INSIDE AN EMBEDDED BYTE ARRAY, where the textual scan "
                    f"cannot see it.\n      {line}")

    assert not violations, (
        f"{len(violations)} local task ID(s) written BARE inside an embedded "
        "payload:\n" + "\n".join(violations)
        + "\n\nFix the UPSTREAM source (a .toml descriptor under "
          "srmech/cascade/catalogs/class_catalog/, or a ToolEntry summary - not "
          "the generated file), then re-run:  python3 tools/regen_all.py"
    )


@pytest.mark.parametrize("rel_path", sorted(CEIL_BARE_REFS_DECODED))
def test_decoded_bare_ref_population_is_down_only(rel_path: str) -> None:
    """DOWN-ONLY CEIL on the residual inside embedded byte arrays."""
    path = _SR_ROOT / rel_path
    found = _decoded_bare_refs(path)
    ceiling = CEIL_BARE_REFS_DECODED[rel_path]

    assert len(found) <= ceiling, (
        f"{rel_path}: {len(found)} bare refs inside embedded byte arrays, "
        f"ceiling {ceiling} - the population GREW by {len(found) - ceiling}.\n"
        "These do not show up in the textual scan, but they ship: a bare-C "
        "host reads this table directly. Write `gh #NNNN` or `#TNNN` in the "
        "UPSTREAM source, then re-run `python3 tools/regen_all.py`.\n"
        + "\n".join(f"    [{a}]:{ln}: #{num}  {txt}"
                    for a, ln, num, txt in found[-8:]))

    if len(found) < ceiling:
        pytest.fail(
            f"{rel_path}: {len(found)} decoded bare refs but the ceiling says "
            f"{ceiling}. GOOD NEWS - lower CEIL_BARE_REFS_DECODED to "
            f"{len(found)} so the gain cannot be given back.")


def test_every_emitted_artifact_is_pinned_for_decoded_refs() -> None:
    """The decoded ceiling must cover the same artifact set as the textual one.

    Without this, adding a seventh generator that embeds byte arrays would
    ship an unguarded payload while every other test stayed green.
    """
    declared = {g.output for g in cm.GENERATORS}
    pinned = set(CEIL_BARE_REFS_DECODED)
    missing = {d for d in declared - pinned if d.endswith(".c")}
    assert not missing, (
        f"C artifacts not pinned in CEIL_BARE_REFS_DECODED: {sorted(missing)}. "
        "Measure each with _decoded_bare_refs and add it.")
    assert not pinned - declared, (
        f"pinned but no longer generated: {sorted(pinned - declared)}")


# ══════════════════════════════════════════════════════════════════════
# rc359 (`#T1035`) — SCAN ROOT vs CI TRIGGER
#
# This test exists because the two sets have now drifted TWICE. A test that
# READS a directory CI does not WATCH is a guard that cannot fire: the file it
# would have caught changes, no workflow runs, and the next unrelated PR
# inherits a red — or worse, the bad text ships and the guard reports green
# because it was never asked.
#
# The invariant: every directory a test scans must lie inside some workflow's
# trigger paths. Checked mechanically here rather than trusted to review,
# because the failure is SILENT by construction and review has already missed
# it twice.
# ══════════════════════════════════════════════════════════════════════

_REPO_ROOT = _SR_ROOT.parent.parent
_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"

#: The directories the suite READS, repo-relative POSIX, with the site that
#: does the reading. MEASURED by reading each expression, not inferred from
#: the filename. `parents[2]` from a test file is `docs/srmech`; anything
#: deeper than `docs/srmech/python` can escape the srmech-ci trigger.
SCAN_ROOTS = {
    # THE WIDE ONE: rglobs the entire subtree to derive the `#TNNN` vocabulary.
    "tests/test_ref_notation_emitted_rc348.py": ("docs/srmech",),
    # Reads the committed proof NDJSON under notes/ and re-measures against it.
    "tests/test_cd_register_ops_rc301.py": ("docs/srmech/notes",),
    # rc361 (`#T1034`): WIDE, and it has to be. The fifth-copy gate scans the
    # whole subtree because the fourth copy of the Rosetta root tuple lived in
    # notes/_rosetta_inventory.py — outside srmech-ci's python/+c/ trigger and
    # inside srmech-ref-guard's. A scan that stopped at python/ could not see a
    # copy re-inlined where the original one was.
    "tests/test_rosetta_roots_single_source_rc361.py": ("docs/srmech",),
    # rc361: reads the generated C registries + the two generated .py artifacts.
    "tests/test_namespace_prefix_decode_aware_rc361.py": (
        "docs/srmech/python", "docs/srmech/c"),
    # The rest stay inside python/ + c/, i.e. inside srmech-ci's own trigger.
    "tests/test_regen_all_rc346.py": ("docs/srmech/python", "docs/srmech/c"),
    # rc362: reads c/src/srmech_tool_schema.c to compare the two HAND-MIRRORED
    # MCP lexicons table-to-table. That file is NOT a regen_all output, so
    # nothing syncs the copies for you and only a direct comparison can see a
    # drift that no live op happens to expose.
    "tests/test_tool_schema_ops_c_rc185.py": ("docs/srmech/python", "docs/srmech/c"),
    "tests/test_c_cascade_coherence.py": ("docs/srmech/c",),
    "tests/test_carrier_capability_rc339.py": ("docs/srmech/c",),
    "tests/test_carrier_ceiling_rc343.py": ("docs/srmech/c",),
    "tests/test_fips_constants_attested.py": ("docs/srmech/c",),
    "tests/test_genome_add_plasmid_c_rc334.py": ("docs/srmech/c",),
    "tests/test_genome_marker_set_drift_rc351.py": ("docs/srmech/c",),
    "tests/test_rosetta_transitive_standalone.py": ("docs/srmech/c",),
    "tests/test_worked_examples_execute_rc354.py": ("docs/srmech/python",),
    "tests/test_laplacian_numpy_free.py": ("docs/srmech/python",),
    # rc403 (`#T1071`): loads c/tools/gen_ryu_tables.py and re-derives every row
    # of c/src/srmech_ryu_tables.h from it. Both live under c/, so the reach is
    # inside srmech-ci's own trigger; it is declared here because the generator
    # is DELIBERATELY excluded from the regen_all pass (a mathematical constant
    # cannot be staled by a tool-surface change), which makes this test the only
    # thing that would notice a hand-edited table limb.
    "tests/test_ryu_tables_attested_rc403.py": ("docs/srmech/c",),
    # rc404 (`#T1069`): counts `return SRMECH_ERR_OVERFLOW` across
    # c/src/*.c to hold the OVERFLOW/LIMIT conflation on a down-only ratchet.
    # Reads only C sources, so the reach is inside srmech-ci's own trigger.
    "tests/test_status_conflation_ratchet_rc404.py": ("docs/srmech/c",),
}

#: Reach expressions that can climb ABOVE `docs/srmech/python/`. `parents[1]`
#: from a test file is still `docs/srmech/python`, so it cannot escape and is
#: not listed. Each of these must appear in SCAN_ROOTS.
_REACH = re.compile(r"parents\[[23]\]|_SR_ROOT\s*=|_SRMECH_ROOT\s*=")


def _trigger_paths() -> "set[str]":
    """Every `paths:` entry under `on:` across the srmech workflows.

    Hand-parsed rather than via PyYAML: pyyaml is NOT a declared dependency of
    this package, and this suite must run in the numpy-absent / pure venv.
    The parser is deliberately narrow -- a `paths:` key, then the `- "..."`
    items indented under it -- and the caller asserts it found something, so a
    format change fails LOUD instead of silently returning an empty set that
    would make every assertion below vacuous.
    """
    found: "set[str]" = set()
    for wf in sorted(_WORKFLOWS.glob("srmech-*.yml")):
        in_paths = False
        indent = 0
        for raw in wf.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            cur = len(raw) - len(raw.lstrip())
            if in_paths:
                if stripped.startswith("- "):
                    found.add(stripped[2:].strip().strip('"').strip("'"))
                    continue
                if cur <= indent:
                    in_paths = False
            if stripped in ("paths:", "paths-ignore:"):
                in_paths = stripped == "paths:"
                indent = cur
    return found


def _covers(trigger: str, root: str) -> bool:
    """True when a workflow trigger path watches everything under ``root``."""
    prefix = trigger[:-3] if trigger.endswith("/**") else trigger
    return root == prefix or root.startswith(prefix + "/")


def test_the_trigger_parser_can_still_see_something() -> None:
    """The parser must parse. An empty result would make the coverage test
    below pass by vacuity -- the exact false-green shape this file guards.
    """
    paths = _trigger_paths()
    assert len(paths) >= 5, (
        f"parsed only {len(paths)} trigger paths from {_WORKFLOWS} - the "
        "workflow `paths:` format has changed and this parser has stopped "
        "observing.")
    assert "docs/srmech/python/**" in paths, (
        "the srmech-ci python trigger is missing from the parsed set")


def test_every_scanned_root_is_inside_a_ci_trigger_path() -> None:
    """A test that reads a directory no workflow watches cannot fire.

    This is the rc359 root cause, stated as an assertion: 846 tracked files
    under docs/srmech/ sat outside every trigger while two tests read them.
    """
    triggers = _trigger_paths()
    uncovered: list[str] = []
    for site, roots in sorted(SCAN_ROOTS.items()):
        for root in roots:
            if not any(_covers(t, root) for t in triggers):
                uncovered.append(
                    f"  {site} scans {root!r}, which NO workflow trigger "
                    f"watches - a change there runs nothing, so this guard is "
                    f"armed and silent.")
    assert not uncovered, (
        "scan roots outside every CI trigger:\n" + "\n".join(uncovered)
        + "\n\nEither narrow what the test reads, or add the path to a "
          "workflow trigger. Prefer a DEDICATED cheap job over widening the "
          "full matrix: .github/workflows/srmech-ref-guard.yml is the model "
          "(~1-2 CI-min vs ~213 billed min for the full matrix).")


def test_no_test_reaches_out_of_tree_without_declaring_it() -> None:
    """SCAN_ROOTS must stay complete, or the coverage test above goes blind.

    Declaring a root is what forces the author to check the trigger. A new
    `parents[2]` reach in an undeclared file is therefore RED here -- not
    because reaching is wrong, but because an UNDECLARED reach is exactly how
    the drift happened both previous times.
    """
    undeclared: list[str] = []
    for path in sorted(_HERE.glob("test_*.py")):
        rel = f"tests/{path.name}"
        if rel in SCAN_ROOTS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            m = _REACH.search(line)
            # A CODE SPAN is prose about a reach, not a reach -- the same
            # exemption the ref scanner above makes, for the same reason.
            # This test caught its own author writing "`parents[2]`" inside a
            # docstring explaining why that file deliberately does NOT reach.
            if m and not _in_code_span(line, m.start(), m.end()):
                undeclared.append(f"  {rel}:{lineno}: {line.strip()[:90]}")
                break
    assert not undeclared, (
        "test file(s) reach above docs/srmech/python/ without a SCAN_ROOTS "
        "entry:\n" + "\n".join(undeclared)
        + "\n\nAdd each to SCAN_ROOTS with the directory it actually reads, "
          "so test_every_scanned_root_is_inside_a_ci_trigger_path can check "
          "that CI watches it.")
