"""rc451 (`#T1164`, gh #1653 item 4) — THE ONE GATE THE VALUE CHANNEL CANNOT BE.

WHY A SOURCE-SHAPE GATE EXISTS HERE AT ALL
==========================================
Every other instrument in this arc judges VALUES, and for this defect class the
value channel is **provably blind**. Measured at rc451
(``notes/_1653_rca_probe_rc451.py`` block D): the fused
``srmech_cascade_best_rational_signed_f64`` and the six declared steps of the
``best_rational_signed`` descriptor agree on **all 10** shipped proof cases —
agree=10, disagree=0 — and the exhaustive branch walk in the costing found no
value-level observable separating them anywhere on the C-accepted domain. The
only residual differences are STATUS-position (the coarse symbol validates
``max_denominator``/``fine_scale`` up front and applies a 2^63 guard), and a
status routes to the pure path; it never produces a value.

So a dispatcher that recognised the descriptor's SHAPE and answered with the
fused symbol would score 9 BYTE_IDENTICAL under the rc450 comparator, drop both
declined-row ceilings onto their targets, and leave the chain's six steps
driving **nothing**. No input can expose it. The step-mutation witness bounds
the bypass but cannot close it: mutants route to the fine arms, so the witness
distinguishes "there is a correct fine interpreter in here" from "there is not"
— it cannot distinguish "fine always" from "fine only when the shape does not
match".

WHAT THIS GATE DOES, AND ITS HONEST LIMIT
=========================================
It PARSES the interpreter translation unit (``c/src/srmech_compose_run.c``) and
asserts it references no MULTI-STEP coarse cascade symbol.

The population is DERIVED, never listed: a descriptor is multi-step when its
declared chain has >= 2 steps, and a coarse symbol is an exported
``srmech_cascade_*`` whose name contains such a descriptor's name. At rc451 that
derives 5 symbols across 4 descriptors, and the gate asserts the derivation is
non-empty — an empty population would make this file agree with everything.

⚠️ ITS LIMIT, STATED RATHER THAN GLOSSED. This is a symbol-REFERENCE check, so
it does not stop someone pasting a duplicate of the fused body inline behind a
shape test. Nothing can: an inlined duplicate references no symbol and is value-
identical by construction. What rules that out is economics, not this pin — the
four fine arms must exist and be correct anyway for the mutation witness to pass
with its PREDICTED value, so an inlined fast path is strictly extra work buying
nothing. The pin closes the cheap route; the witness bounds the expensive one;
neither claims to be the other.

HOW IT RETURNS OTHERWISE
========================
:func:`test_the_pin_would_catch_a_coarse_dispatch` runs the same predicate over
an in-memory MUTATED copy of the TU with a coarse call spliced into the dispatch
chain, and asserts it reds. A detector that cannot fail on the defect it names
is not a detector.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat
from srmech.dsl._cascade_chain import cascade_chain_specs

_C_DIR = Path(__file__).resolve().parents[2] / "c"
_INTERPRETER = _C_DIR / "src" / "srmech_compose_run.c"
_HEADER = _C_DIR / "include" / "srmech.h"

#: The sibling DSL interpreter (``srmech_dsl_chain_run.c``) legitimately threads
#: values through coarse symbols and is NOT scanned: its chain contract declares
#: no interior, so a whole-op call there is the op, not a bypass of declared
#: steps. Naming the exemption rather than leaving the scope implicit.
_NOT_SCANNED = ("srmech_dsl_chain_run.c",)


def _read(path: Path) -> str:
    with io.open(path, "r", encoding="utf-8", errors="replace",
                 newline=None) as fh:
        return fh.read()


def _multi_step_descriptors() -> dict:
    """{descriptor name: declared step count} for every catalog descriptor whose
    chain has >= 2 steps. Read LIVE from the catalog, so a new composite joins
    this gate's population automatically."""
    out = {}
    for name, desc in _cat.load_catalog().items():
        if _cc.descriptor_status(desc) != "executable":
            continue
        steps = max(len(entry.get("steps") or [])
                    for _v, _s, entry in cascade_chain_specs(name))
        if steps >= 2:
            out[name] = steps
    return out


def _coarse_symbols() -> dict:
    """{exported symbol: descriptor it fuses}, derived from the header.

    PREDICATE: an exported ``srmech_cascade_<...>`` whose name contains the name
    of a multi-step descriptor. That deliberately catches
    ``srmech_cascade_kuramoto_step_general_f64`` as well as the plain one — a
    variant of a coarse symbol is still a coarse symbol.
    """
    header = _read(_HEADER)
    exported = set(re.findall(r"\b(srmech_cascade_[A-Za-z0-9_]+)\s*\(", header))
    multi = _multi_step_descriptors()
    return {sym: name for sym in exported for name in multi if name in sym}


def _referenced(text: str, symbols) -> dict:
    """{symbol: [1-indexed line numbers]} for each symbol CALLED in `text`.

    PREDICATE, stated so it can be reproduced or refuted: the symbol name
    followed by optional whitespace and an opening parenthesis — i.e. a CALL,
    not a mention.

    ⚠️ THE DISTINCTION IS DELIBERATE AND IT WAS MEASURED. The first draft of
    this file matched a bare NAME anywhere in the line, and it immediately went
    red — on the interpreter's own comment explaining that the fused symbol is
    deliberately not called from that TU. Prose that NAMES the thing being
    refused is the documentation working, not the defect; a predicate that
    cannot tell a refusal from a call would push the next author to delete the
    explanation. Requiring the call shape keeps the real catch: a commented-out
    dispatch still carries its parenthesis, so it is still flagged.

    Comments are otherwise scanned exactly like code, on purpose — a
    commented-out coarse call is a thing somebody is about to uncomment.
    """
    hits = {}
    lines = text.split("\n")
    # The TABLE REGION, if present: under the first rc452 cut a function-pointer
    # column WIRED a symbol in without ever calling it, so inside this block a
    # bare mention IS a dispatch. The shipped A1 rows are enum data and cannot
    # name a symbol, but the wider predicate is KEPT — it costs nothing and
    # guards a regression to fn columns. See the rc452 note below.
    tbl_lo, tbl_hi = _table_line_span(lines)
    for sym in symbols:
        pat = re.compile(r"\b" + re.escape(sym) + r"\s*\(")
        bare = re.compile(r"\b" + re.escape(sym) + r"\b")
        found = []
        for i, ln in enumerate(lines):
            if pat.search(ln):
                found.append(i + 1)
            elif tbl_lo <= i <= tbl_hi and bare.search(ln):
                found.append(i + 1)
        if found:
            hits[sym] = found
    return hits


def _table_line_span(lines) -> tuple:
    """0-indexed [lo, hi] line span of the ``CR_OP_REG`` initialiser, or (-1,-2).

    ⚠️ ADDED AT rc452 (`#T1166`) BECAUSE THE REFACTOR THAT rc452 PERFORMS WOULD
    OTHERWISE HAVE DISARMED THIS GATE, AND ITS OWN RETRO-CHECK CAUGHT IT.

    The call-shaped predicate above is correct for an IF-CHAIN dispatch, which
    is what existed when it was written: a coarse dispatch there necessarily
    spells ``srmech_cascade_foo(...)``. rc452's first cut converted the
    dispatch to a name-to-FUNCTION-POINTER atom table, where wiring a coarse
    symbol in was a BARE IDENTIFIER in a row's ``fn`` column — no parenthesis
    anywhere. Measured while writing this rc: the retro-check spliced exactly
    such a row and ``_referenced`` returned ``{}``. The gate would have gone on
    reporting the file clean while a coarse dispatch was live in it.

    So the predicate widens for the table region ONLY. Scoping matters both
    ways: a bare match over the whole file re-creates the rc451 defect this
    file's own docstring records (it went red on the interpreter's COMMENT
    explaining that the fused symbol is deliberately not called), while a
    call-only match over the whole file misses the row-wiring shape. Prose
    outside the initialiser is still exempt; anything named inside it is data
    that the interpreter dispatches through. (The shipped A1 rows are enum
    data — a symbol cannot ride a row today — but the span rule is kept as a
    regression guard; the A1-realistic threat, a coarse CALL in an exec arm,
    is covered by the call predicate and its own retro-check splice.)
    """
    lo = -1
    for i, ln in enumerate(lines):
        if re.search(r"\}\s*CR_OP_REG\[\d+\]\s*=\s*\{", ln):
            lo = i
            break
    if lo < 0:
        return (-1, -2)          # no table in this TU — call-shape only
    for j in range(lo, len(lines)):
        if lines[j].startswith("};"):
            return (lo, j)
    return (lo, len(lines) - 1)


def test_the_derived_population_is_not_empty() -> None:
    """A gate whose population is empty agrees with everything.

    Both halves are asserted: there ARE multi-step descriptors, and there ARE
    exported coarse symbols fusing some of them. If the header stopped spelling
    them ``srmech_cascade_*``, this fires instead of quietly passing.
    """
    multi = _multi_step_descriptors()
    coarse = _coarse_symbols()
    assert len(multi) >= 5, (
        "only %d multi-step descriptors derived (%s) — the catalog walk has "
        "stopped seeing chains, and an empty population is not agreement"
        % (len(multi), sorted(multi)))
    assert len(coarse) >= 3, (
        "only %d coarse cascade symbols derived from %s. The predicate is an "
        "exported srmech_cascade_* whose name contains a multi-step "
        "descriptor's name; if the naming convention moved, re-point it rather "
        "than deleting the assertion." % (len(coarse), _HEADER.name))
    assert "srmech_cascade_best_rational_signed_f64" in coarse, (
        "the symbol this gate was written for is not in the derived set: %s"
        % sorted(coarse))


def test_the_interpreter_calls_no_multi_step_coarse_cascade_symbol() -> None:
    """THE CLAIM. ``srmech_chain_run`` executes chains from their DECLARED
    STEPS, and never by recognising a chain and answering with a fused symbol.

    Measured 0 at rc450 (before the four step ops landed) and 0 at rc451 (after),
    so this starts true and holds; it is cheap precisely because it was never
    violated. The point is that it is now CHECKED — the temptation only exists
    once the fused symbol and the fine arms are both available, which is exactly
    the state this rc creates.
    """
    coarse = _coarse_symbols()
    hits = _referenced(_read(_INTERPRETER), coarse)
    assert not hits, (
        "the chain interpreter %s references coarse whole-chain cascade "
        "symbol(s): %s.\n"
        "A chain that runs because one fused symbol recognised its shape is not "
        "a chain the C host can run from its descriptor — and NO value-level "
        "gate can tell the difference: the fused best_rational_signed symbol is "
        "MEASURED value-identical to the six declared steps on all 10 shipped "
        "proof cases. Dispatch per STEP, at symbol granularity. Op-granular "
        "exports (srmech_cascade_dead_band_f64, "
        "srmech_cascade_scale_round_half_even_i64, the pin_slot / reorient / "
        "chiral_flip peers) are the honest shape and are not in this "
        "population.\n"
        "Not scanned, deliberately: %s."
        % (_INTERPRETER.name,
           {k: v for k, v in sorted(hits.items())}, ", ".join(_NOT_SCANNED)))


def test_the_pin_would_catch_a_coarse_dispatch() -> None:
    """RETRO-CHECK, on a MUTATED IN-MEMORY COPY. Splice a coarse dispatch into
    the TU's own dispatch chain and assert the predicate reds.

    Without this the gate above is an assertion about a file that happens to be
    clean, and nothing would notice if ``_coarse_symbols`` silently derived the
    empty set or ``_referenced`` stopped matching.
    """
    text = _read(_INTERPRETER)
    # ⚠️ RE-POINTED AT rc452 (`#T1166`), AS THIS TEST'S OWN MESSAGE INSTRUCTS.
    # The anchor was `if (cr_op_is(op, opl, "pair", 4u)) {` — a dispatch ARM of
    # the if-chain. rc452 converts the dispatch to a table, so there are no
    # arms left to splice into and the assertion fired exactly as designed: it
    # refused to run a retro-check whose mutation site no longer exists, rather
    # than silently mutating nothing and passing.
    #
    # TWO SPLICES since the A1 (Rule-9-clean) reshape, because the threat has
    # two shapes. Under the first rc452 cut a row's function-pointer column
    # wired a symbol in with NO parenthesis — the table-span bare-mention rule
    # exists for that, and splice 1 keeps it honest (also guarding a regression
    # to fn columns). Under the shipped A1 design rows are pure enum data and
    # cannot name a symbol at all; the realistic coarse dispatch is a CASE ARM
    # in a cr_exec_* CALLING the fused symbol — splice 2 models exactly that
    # and is caught by the call-shape predicate.
    anchor = ' { "pair",                4u, "srmech.cascade.pair",'
    assert anchor in text, (
        "the mutation anchor is gone from %s — re-point it at another CR_OP_REG "
        "row rather than deleting this retro-check" % _INTERPRETER.name)
    mutated = text.replace(
        anchor,
        ' { "best_rational_signed", 20u, "srmech.cascade.best_rational_signed",\n'
        '   srmech_cascade_best_rational_signed_f64, NULL },\n'
        + anchor,
        1)
    assert mutated != text, "the mutation did not change the source"
    coarse = _coarse_symbols()
    assert _referenced(mutated, coarse), (
        "the predicate did NOT flag a spliced coarse dispatch — it has stopped "
        "measuring, and the green above is therefore worth nothing")
    # splice 2: the A1-shaped threat — an exec case arm calling the fused symbol
    arm_anchor = "    case CR_CAS_PAIR:            return cr_op_pair(c, args, out);"
    assert arm_anchor in text, (
        "the exec-arm anchor is gone from %s — re-point it at another cr_exec_* "
        "case rather than deleting this retro-check" % _INTERPRETER.name)
    mutated2 = text.replace(
        arm_anchor,
        arm_anchor + "\n    case CR_CAS_BRS: return "
        "srmech_cascade_best_rational_signed_f64(c, args, out);",
        1)
    assert mutated2 != text, "the arm mutation did not change the source"
    assert _referenced(mutated2, coarse), (
        "the predicate did NOT flag a coarse CALL spliced into an exec arm — "
        "the call-shape half has stopped measuring")
    assert not _referenced(text, coarse), (
        "control: the UNMUTATED source must still be clean, or the retro-check "
        "above proves nothing about the mutation")
