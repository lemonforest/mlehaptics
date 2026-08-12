"""v0.9.0rc415 (`#T1098`) — the ADR citation-integrity gate.

An ADR that cites `file.py:NNN` is making a checkable claim: *there is
something at that address, and it is the thing this sentence says it is.*
Until this file, nothing in the tree checked either half — and the corpus had
drifted accordingly. Two rcs of insertions (rc408 moved `_tools.py`, rc412
inserted 52 lines into `tool_schema.py`) silently repointed a dozen citations,
and one pointer named a symbol, `_merge_docs`, that has **never existed** in
any commit.

⚠️ **THIS GATE'S RECALL IS NOT 100%, AND SAYING SO IS PART OF SHIPPING IT.**
=========================================================================
Two violations confirmed by hand during the research that produced this file
are **not caught by the checks below**, and the reasons are structural rather
than fixable-by-tuning:

* The **enclosing-scope widening** that V3 uses to avoid punishing a citation
  for pointing at line 170 of a 239-line docstring also widens *past* a real
  drift. A pointer that has slid within its own function still lands inside
  the evidence window, and the gate calls it clean.
* The **quote extractor mangles a multi-line quotation.** When an ADR wraps a
  quoted sentence across markdown lines, the first `"` on the continuation
  line is a CLOSING quote; pairing it with the next opening quote captures the
  prose *between* two quotations. :data:`_QUOTE_REJECT` filters the worst of
  that shape, not all of it.

A gate that claimed completeness it does not have is the exact failure class
this whole arc exists to close — an ADR sentence asserting a clause is gated
turning out to be the only evidence anyone had that it was. So: **V1/V2 are
strict-zero and decidable. V3/V4 are a down-only CEIL, and the CEIL is honest
about containing both real violations and the gate's own false positives.**

WHY V3/V4 ARE A CEIL AND NOT STRICT ZERO
========================================
Not caution — measurement. The V3 prototype's own text normalisation stripped
`_` as markdown emphasis, which turned **every snake_case claim** in the
corpus (`_needs_native`, `body_sha256`, `to_jsonable`, `GENERATED_DATA_FILES`)
into a false absence: 20 reported violations of which roughly 13 were the
gate's own bug, found only by hand-verifying every hit. The normalisation a
prose-vs-source comparison needs is itself a silent-wrong-answer surface, so
the arm that depends on it does not get to fail a build to zero. It gets a
ceiling that drains.

:func:`test_no_prose_evidence_regression` therefore fails when the count goes
UP and prints the drain when it goes down. Lowering a CEIL is a normal commit;
raising one requires saying why in the same diff.

THE ADJACENCY WINDOW IS A DIAL, AND NEITHER SETTING DOMINATES
=============================================================
:data:`_WINDOW` is 55 columns. Measured against the pre-correction corpus: at
**90** columns the gate also catches two further real drifts (`0010:189`,
`0010:196`) at a cost of roughly six more false positives; at **55** it misses
them. There is no setting that catches everything and invents nothing, and the
honest thing is to ship one, name the trade, and let the CEIL record where the
line fell. If this gate ever gets `-k`-filtered, the window was the wrong call.

WHAT V5 IS FOR, AND WHY IT NEVER FAILS
======================================
:func:`test_mid_block_citations_are_reported` prints citations that point
*inside* a comment block or `def` rather than at its first line. On this corpus
that is roughly 5/17 signal, and **its clearest hit is a repair**: ADR-0013
`:186` cites `tool_schema.py:314` and `:318` — deliberate pointers at the two
individual sentences whose excision caused the §1.7.1 defect, both interior to
the `#:` block that starts at `:313`. A strict block-start rule would flag the
sentence written to fix the defect. So it reports and never asserts.

INJECTION PROOFS — RUN, NOT DESCRIBED
=====================================
Each mutation applied to `adr/0011-single-encoding-no-cache.md:101` (the ADR's
only citation) against the corrected rc415 corpus, then reverted::

  A. `genome.py` -> `genome_nonexistent.py`
       -> V1 red: "1 citation(s) name a file that does not exist"  (1 failed)
  B. `:9137-9142` -> `:999137`
       -> V2 red: "1 citation(s) point past the end of their file" (2 failed —
          V3 goes with it, because an evidence window past EOF is empty)
  C. a backticked `no_such_symbol_here` added beside the citation
       -> V3 red: "violations rose to 9, above CEIL_TOKEN_EVIDENCE=8",
          naming the token, the kind (ABSENT_FROM_FILE) and the evidence span

A fourth is structural rather than injected: :func:`test_the_basis_pinned_allowlist_is_exact`
fired for real during this rc. The allowlist was first keyed on the line
WITHIN the ADR, and adding three completion markers to ADR-0010 §A.5 — 600
lines away — shifted `:796` to `:810` and took both V1 arms red at once. The
key is now the CITED address, which does not move when the citing document is
edited. A citation-drift gate whose own allowlist drifts is not a hypothetical.

NO REGEX
========
The whole parse is Class-G (`srmech.math.search.byte_search`) via
`tests/adr_corpus.py`. That module records the capability gaps this cost —
no `byte_search_all`, no `start=` offset, no offset→line op, no anchored
`match` — as findings rather than working around them silently.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from adr_corpus import (
    Citation,
    all_citations,
    all_markdown,
    file_line_count,
    read_adr,
    resolve_candidates,
    text_lines,
)

# ── tunables, each with its measured justification above ──────────────

#: Columns either side of a citation that count as "adjacent" prose.
#: See THE ADJACENCY WINDOW IS A DIAL in the module docstring.
_WINDOW = 55

#: Shortest normalised quotation V4 will test. Below this, a quoted run is
#: idiom rather than evidence ("the SSoT", "no such name") and testing it
#: produces noise proportional to how well-written the ADR is.
_MIN_QUOTE = 12

# ── the CEIL seeds — measured at v0.9.0rc415 against the corrected corpus ──

#: Down-only. Backticked identifiers adjacent to a citation that do not occur
#: in the citation's evidence window. Seeded AFTER the rc415 corrections, so
#: this number is the honest residual and not a pre-correction high-water mark.
#:
#: **Composition of the seed at rc415, hand-verified entry by entry.** Stating
#: it is the whole point of a CEIL: an unexamined ceiling is a number, an
#: examined one is a queue.
#:
#:   * **2 — NEGATIVE-EXISTENCE claims.** `all_entries` at ADR-0013 `:79` and
#:     `:1132`, where the prose says the name *"exists nowhere"* and being
#:     absent from the file is the POINT. A guard keyed on English phrasing
#:     ("exists nowhere", "no such name", "used to") would catch these and
#:     would rot silently; the CEIL absorbs them instead.
#:   * **2 — ADR-0010 Amendment rows correct at their declared basis sha.**
#:     `_live_ops` (`:196`) and `_needs_native` (`:268`). Amendment A opens
#:     *"Measured against srmech 0.9.0rc360 at 7b313407b"* and A.3 says
#:     rewriting a path in a dated record FALSIFIES it. These drain only if
#:     the convention for basis-marking changes.
#:   * **2 — adjacency false positives.** `c_dispatched` (`0010:92`) and
#:     `dev_tooling` (`0010:176`) are Rosetta BUCKET names, prose about a
#:     classification, that happen to sit within :data:`_WINDOW` of a
#:     citation about something else. This is the window's measured cost.
#:   * **1 — an adjacency FP the rc415 fix itself created.** `tool_schema_view`
#:     at `0013:79`. Correcting that row put two citations ~30 columns apart
#:     (`:673` for `get_tool_schema`, `:697` for `tool_schema_view`), so each
#:     now falls inside the other's window. Recorded rather than tuned away:
#:     the window is a dial and this is what the dial costs.
#:   * **1 — a genuine imprecision, left for a later rc.** `0013:1178` cites
#:     `c/include/srmech.h:5378-5437` for `srmech_tool_entry_t`; that range is
#:     the tool-schema-registry doc BANNER and the struct is at `:5457-5467`.
#:     Not in this rc's correction list, correctly non-zero here.
#:
#: **8 -> 7 at v0.9.0rc425 (`#T1112`), and the residual is now STRUCTURAL.**
#: The last drainable-by-re-anchoring entry is gone, so what remains is exactly
#: the three kinds re-anchoring cannot touch: 2 negative-existence claims
#: (`all_entries`, where absence IS the assertion), 2 ADR-0010 Amendment rows
#: correct at their declared basis sha (`_live_ops`, `_needs_native` — A.3 says
#: rewriting a path in a dated record FALSIFIES it), and 3 adjacency false
#: positives (`c_dispatched`, `dev_tooling`, `tool_schema_view`). Draining any
#: of the seven needs a DECISION — change the negative-existence phrasing,
#: re-base a dated Amendment, or narrow :data:`_WINDOW` — not a line number.
#:
#: ⚠️ THE rc415 SEED'S EIGHTH ENTRY IS NOT THE ONE THAT DRAINED HERE. The
#: `0013:1178` imprecision above drained on its own between rc415 and rc424
#: (the ADR's citation was corrected to `:5444-5523`), and a NEW entry took the
#: free slot: `0013:286` citing `test_composes_grain_rc412.py:516`, six lines
#: ABOVE the `def` it names, so the token sat outside the cited function's
#: scope. rc425 pointed it at the `def` itself. The count held at 8 across that
#: swap, which is the thing to notice — **a CEIL that does not move is not
#: evidence that its composition did not**, and only the entry-by-entry listing
#: above makes the substitution visible at all.
#:
#: HOW rc425 CAME TO TOUCH THIS AT ALL — the complement of `#T1107`. That task
#: recorded that a bare path with no line number is COMPLETELY UNGATED here.
#: The other edge is the one rc425 hit: a `path:line` citation is BRITTLE to
#: any insertion above it, so the only gated form is also the only form that
#: rots on edits that have nothing to do with it. Registering 37 ToolEntries
#: added 28 lines to `c/include/srmech.h` and 145 to
#: `test_composes_grain_rc412.py`, which moved 12 citations and took 5 of them
#: over this CEIL. Whoever picks up `#T1107` needs BOTH halves; any future bulk
#: registration will re-trigger this exact failure.
#:
#: ⚠️ AND THE GATE SAW ONLY 5 OF THE 12. A drifted citation is reported here
#: only when a backticked token happens to sit in its adjacency window AND the
#: widened block no longer covers it; the other 7 moved SILENTLY. So repairing
#: only what this gate prints leaves stale pointers behind and quietly converts
#: a detectable staleness into an undetectable one. rc425 re-anchored all 12,
#: found by diffing every cited line's CONTENT against the previous release
#: rather than by reading this list.
#:
#: LOWERING THIS IS A NORMAL COMMIT. Raising it needs a reason in the diff.
CEIL_TOKEN_EVIDENCE = 7

#: Down-only. Quoted runs adjacent to a citation not found in its evidence
#: window.
#:
#: The one at rc415 is real signal: ADR-0013 `:990` quotes *"DSL-declared
#: class"* against `srmech.h:5977`, and that phrase occurs **nowhere in
#: srmech.h** — `:5977` reads *"constructs a DSL [class] instance from its
#: packaged TOML descriptor"*. It is the ADR's own paraphrase wearing
#: quotation marks. Left in the CEIL rather than corrected here because the
#: fix is a wording decision, not one of the seven measured citation drifts
#: this rc drains.
#:
#: See the recall caveat in the module docstring: the multi-line-quotation
#: shape is a known extractor limitation, and :data:`_QUOTE_REJECT` filters
#: the worst of it rather than all of it.
CEIL_QUOTE_EVIDENCE = 1

#: Citations whose file genuinely does not resolve, and MUST NOT be "fixed".
#: Each entry is ``(adr, cited-path, cited-start-line)`` plus a reason. The
#: gate asserts this list is EXACT — an entry that stops firing must be
#: deleted, so the allowlist cannot quietly outlive its justification.
#:
#: ⚠️ **KEYED ON THE CITED TARGET, NEVER ON THE ADR LINE.** The first cut keyed
#: on the line WITHIN the ADR, and adding three completion markers to ADR-0010
#: §A.5 — an edit 600 lines away, in the same rc — shifted `:796` to `:810` and
#: took the gate red on both arms at once. An allowlist for a citation-drift
#: gate must not itself be a position that drifts; the cited address is stable
#: under every edit to the citing document, which is the property wanted.
_BASIS_PINNED: Dict[Tuple[str, str, int], str] = {
    ("0010", "srmech/amsc/tool_schema.py", 436):
        "ADR-0010 Amendment A is a DATED per-slice execution record: A opens "
        "'Measured against srmech 0.9.0rc360 at 7b313407b'. This citation was "
        "correct at that sha. A.3 says of exactly this class that rewriting "
        "paths in a dated record FALSIFIES it. The module moved under this "
        "ADR's own arc, which is what the record exists to describe.",
    ("0010", "srmech/amsc/responsion_schema.py", 392):
        "A META-MENTION of the citation FORM, not a citation. The sentence "
        "reads '...its cross-citations are slash-form "
        "srmech/amsc/responsion_schema.py:392 (excluded as filenames)' — it "
        "is prose ABOUT what a citation looks like. Structurally "
        "indistinguishable from a dead link without reading the sentence.",
}

#: Quoted spans V4 refuses to test. Anything containing a citation suffix is
#: the multi-line-quotation artefact described in the recall caveat: the
#: extractor has paired a CLOSING quote with the next OPENING one and captured
#: the prose in between, which of course contains the citation.
_QUOTE_REJECT = (".py:", ".c:", ".h:", ".md:", ".toml:")

#: Words that look like identifiers but are English. Kept SHORT deliberately:
#: a long list is a second unreviewed heuristic, and V3 is a CEIL precisely so
#: that a residual false positive costs a number rather than a build.
_ENGLISH = frozenset({
    "true", "false", "none", "self", "type", "name", "list", "dict",
    "bytes", "tuple", "print", "open", "this", "that", "with", "from",
    "into", "over", "when", "what", "then", "else", "always", "never",
})

_IDENT_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


# ── helpers ───────────────────────────────────────────────────────────


def _backticked(text: str) -> List[str]:
    """Every ``` `code span` ``` in ``text``, in order. Class-G shaped."""
    out: List[str] = []
    buf: List[str] = []
    on = False
    for ch in text:
        if ch == "`":
            if on:
                out.append("".join(buf))
                buf = []
            on = not on
        elif on:
            buf.append(ch)
    return out


def _looks_like_identifier(token: str) -> bool:
    """Is this code span a SYMBOL claim rather than prose or a path?

    Deliberately conservative. A token that is not clearly an identifier is
    skipped, because a false ABSENCE reads as a corpus defect and costs a
    reader's trust, while a missed identifier costs only recall — which this
    module has already declared it does not have in full.
    """
    token = token.strip()
    if token.endswith("()"):
        token = token[:-2]
    if len(token) < 4 or token.lower() in _ENGLISH:
        return False
    if not all(c in _IDENT_CHARS for c in token):
        return False
    if token[0].isdigit():
        return False
    if "_" in token:
        return True
    if token[0].isupper() and any(c.isupper() for c in token[1:]):
        return True
    return token.islower() and len(token) >= 6


def _quoted(text: str) -> List[str]:
    """Quoted runs in ``text`` — ASCII and typographic pairs alike."""
    out: List[str] = []
    for opener, closer in (('"', '"'), ("“", "”")):
        i = 0
        while True:
            a = text.find(opener, i)
            if a < 0:
                break
            b = text.find(closer, a + 1)
            if b < 0:
                break
            out.append(text[a + 1:b])
            i = b + 1
    return out


def _norm(text: str) -> str:
    """Normalise prose for comparison against source text.

    ⚠️ **MUST NOT strip ``_``.** The prototype did — treating it as markdown
    emphasis — and thereby turned every snake_case claim in the corpus into a
    false absence. That single character is the difference between a gate and
    a noise generator, and it is why V3/V4 are a CEIL.
    """
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("`", "").replace("*", "")
    return " ".join(text.split())


def _py_scope(path: Path, line_no: int) -> Optional[Tuple[int, int]]:
    """The innermost ``def``/``class`` containing ``line_no``, via stdlib ast.

    ⚠️ Recorded as a reach, not smuggled: srmech ships no Python-source
    structure surface, and it SHOULD NOT — `srmech.introspect` is about the
    tool registry, not about source text. Using stdlib ``ast`` here is
    correct; the note exists so the reach is visible rather than silent.
    ``ast`` cannot see comments at all, which is why :func:`_text_block` has
    to exist beside it.
    """
    try:
        tree = ast.parse(path.read_bytes())
    except (SyntaxError, ValueError):        # pragma: no cover
        return None
    best: Optional[Tuple[int, int]] = None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        lo = node.lineno
        hi = getattr(node, "end_lineno", None) or node.lineno
        if lo <= line_no <= hi:
            if best is None or (hi - lo) < (best[1] - best[0]):
                best = (lo, hi)
    return best


def _text_block(body: List[str], line_no: int) -> Tuple[int, int]:
    """The contiguous run of non-blank lines around ``line_no``.

    The comment-block widener. A `#:` documentation block or a C `/* … */`
    banner is one unit of meaning, and a citation naming its third line is
    naming the block.
    """
    lo = hi = max(1, min(line_no, len(body)))
    while lo > 1 and body[lo - 2].strip():
        lo -= 1
    while hi < len(body) and body[hi].strip():
        hi += 1
    return lo, hi


def _comment_block(body: List[str], line_no: int) -> Tuple[int, int]:
    """The enclosing run of ``#``-prefixed lines around ``line_no``.

    NOT the same widener as :func:`_text_block`. This one is the unit ADR-0013
    §1.7.1 is about: a ``#:`` documentation block is one statement, and the
    defect that section records was two sentences EXCISED from the middle of
    one. The non-vacuity probe reports this block's start, because "the class
    that contains it" (which is what the ``ast`` scope returns, 269..411 here)
    is not an address anyone can check the repair against.
    """
    lo = hi = max(1, min(line_no, len(body)))
    if not body[lo - 1].lstrip().startswith("#"):
        return (lo, hi)
    while lo > 1 and body[lo - 2].lstrip().startswith("#"):
        lo -= 1
    while hi < len(body) and body[hi].lstrip().startswith("#"):
        hi += 1
    return (lo, hi)


def _evidence(path: Path, cit: Citation) -> Tuple[str, str, Tuple[int, int]]:
    """``(evidence_window, whole_file, (lo, hi))`` for one citation.

    The cited range widened to its enclosing scope. Widening is what stops the
    gate punishing the only useful form of citation into a 239-line docstring
    — "block start = 1" is not an address. It is also the reason recall is
    imperfect: a pointer that drifted WITHIN its own function still lands
    inside the window. Both facts are properties of the same decision.
    """
    body = path.read_bytes().decode("utf-8", "replace").split("\n")
    lo, hi = cit.start_line, cit.end_line
    scope = _py_scope(path, cit.start_line) if path.suffix == ".py" else None
    if scope is None:
        scope = _text_block(body, cit.start_line)
    lo, hi = min(lo, scope[0]), max(hi, scope[1])
    return ("\n".join(body[max(0, lo - 1):hi]), "\n".join(body), (lo, hi))


def _resolvable() -> List[Tuple[Citation, Path]]:
    """Every citation that resolves to exactly one file, with that file."""
    out: List[Tuple[Citation, Path]] = []
    for cit in all_citations():
        hits = resolve_candidates(cit.path)
        if len(hits) == 1:
            out.append((cit, hits[0]))
    return out


def _adr_line(cit: Citation) -> str:
    """The markdown line a citation sits on."""
    for path in all_markdown():
        name = path.name[:4] if path.name != "README.md" else "READ"
        if name == cit.adr:
            return text_lines(read_adr(path))[cit.line_no - 1]
    return ""                                # pragma: no cover


def _adjacent(cit: Citation) -> str:
    """The +/- :data:`_WINDOW` columns of prose around a citation."""
    line = _adr_line(cit)
    lo = max(0, cit.column - _WINDOW)
    hi = min(len(line), cit.column + len(cit.raw) + _WINDOW)
    return line[lo:hi]


# ── clause 0: the gate must have looked at something ──────────────────


def test_the_citation_scan_is_not_vacuous() -> None:
    """FOUR clauses, and clause 4 is the live non-vacuity probe.

    Everything below is an assertion over a POPULATION. A parser that silently
    returns an empty population makes every one of them green, which is the
    exact false-green this suite exists to stop. Fails as an
    ``AssertionError`` before any verdict, so a broken parser CRASHES rather
    than reporting a clean corpus.

    Clause 4 is the part that makes this a measurement rather than a shape
    check: ADR-0013 §1.7.1's anchor citation, `introspect/tool_schema.py:313`,
    has a KNOWN correct answer — the `#:` block containing 313 starts at
    exactly 313 — and the gate cannot report a green corpus without having
    looked at it. The computed block start is printed on every run, so a
    regression in the widener is visible even when nothing fails.
    """
    files = all_markdown()
    cits = all_citations()
    py = [c for c in cits if c.path.endswith(".py")]

    assert len(files) >= 13, (
        f"only {len(files)} markdown file(s) under adr/ — the corpus is 13 "
        f"ADRs plus README.md. Found: {[f.name for f in files]}")
    assert len(cits) >= 60, (
        f"extracted only {len(cits)} citation(s); the corpus carried 78 at "
        f"rc415. A citation parser that has stopped observing reports a "
        f"perfectly clean corpus.")
    assert len(py) >= 30, (
        f"only {len(py)} of {len(cits)} citations are .py — the shape of this "
        f"corpus is Python-heavy, and losing that means the suffix scan has "
        f"lost a token.")

    anchor = [c for c in cits
              if c.path.endswith("tool_schema.py") and c.start_line == 313]
    assert anchor, (
        "the ADR-0013 §1.7.1 anchor citation `introspect/tool_schema.py:313` "
        "is NOT in the extracted set. That citation is this gate's known-"
        "answer probe: without it the gate can report a clean corpus without "
        "having looked at the one address whose correct value is known.")

    cit = anchor[0]
    hits = resolve_candidates(cit.path)
    assert len(hits) == 1, f"anchor citation resolves to {len(hits)} files"
    body = hits[0].read_bytes().decode("utf-8", "replace").split("\n")
    lo, hi = _comment_block(body, cit.start_line)
    _ev, _whole, scope = _evidence(hits[0], cit)
    print(f"\n[rc415] §1.7.1 anchor {cit.path}:{cit.start_line} — its `#:` "
          f"block is {lo}..{hi}; the ast scope V3 actually widens to is "
          f"{scope[0]}..{scope[1]}.")
    assert lo == 313, (
        f"the `#:` block containing {cit.path}:313 now starts at {lo}, not "
        f"313. That block is ADR-0013 §1.7.1's subject: the defect it records "
        f"was two sentences excised from its middle, and the 2d2c13a50 repair "
        f"restored them. A moved block start means either the repair was "
        f"undone or the block was re-cut — check before adjusting this "
        f"number, because it is the one address in this corpus whose correct "
        f"value is independently known.")


# ── V1 / V2: strict zero, decidable ───────────────────────────────────


def test_no_citation_names_a_missing_file() -> None:
    """V1 STRICT ZERO. A cited path that resolves to no file.

    Zero false positives measured on this corpus once shortened path
    fragments resolve by ``/``-aligned suffix — the corpus writes
    `introspect/tool_schema.py`, not the full repo path, and a resolver that
    only joins against roots calls 27 of 78 citations dead when none is.

    Two citations are exempt and both are recorded in :data:`_BASIS_PINNED`
    with their reason. The allowlist is asserted EXACT below, so an entry
    cannot outlive the condition that justified it.
    """
    dead: List[str] = []
    for cit in all_citations():
        if resolve_candidates(cit.path):
            continue
        if (cit.adr, cit.path, cit.start_line) in _BASIS_PINNED:
            continue
        dead.append(f"  ADR-{cit.adr}:{cit.line_no} -> {cit.raw}")

    assert not dead, (
        f"{len(dead)} citation(s) name a file that does not exist:\n"
        + "\n".join(dead)
        + "\n\nA reader following one of these lands nowhere. Either the file "
          "moved (update the path), or the citation was never right (say so "
          "in the ADR rather than deleting the sentence — see ADR-0012 §3.2).")


def test_the_basis_pinned_allowlist_is_exact() -> None:
    """An allowlist entry that no longer fires MUST be deleted.

    A stale exemption is indistinguishable from a check that was never
    written, and it is the cheaper of the two to leave lying around. This
    makes the allowlist down-only in the direction that matters: entries leave
    when the condition does.
    """
    live = {(c.adr, c.path, c.start_line) for c in all_citations()
            if not resolve_candidates(c.path)}
    stale = sorted(k for k in _BASIS_PINNED if k not in live)
    assert not stale, (
        f"{len(stale)} _BASIS_PINNED entr(ies) no longer describe a live "
        "violation:\n"
        + "\n".join(f"  {k} — {_BASIS_PINNED[k][:80]}..." for k in stale)
        + "\n\nDelete them. An exemption that exempts nothing is a comment "
          "wearing a data structure.")


def test_no_citation_points_past_end_of_file() -> None:
    """V2 STRICT ZERO. A cited line number past EOF.

    The cheapest possible check and the one with no judgement in it at all:
    either the file has that many lines or it does not. Zero hits at rc415,
    and it ships anyway because a file SHRINKING is the one drift shape that
    produces a pointer into nothing rather than a pointer at the wrong thing.
    """
    over: List[str] = []
    for cit, path in _resolvable():
        total = file_line_count(path)
        if cit.end_line > total:
            over.append(
                f"  ADR-{cit.adr}:{cit.line_no} -> {cit.raw} "
                f"but {path.name} has {total} lines")

    assert not over, (
        f"{len(over)} citation(s) point past the end of their file:\n"
        + "\n".join(over))


# ── V3 / V4: down-only CEIL ───────────────────────────────────────────


def _token_violations() -> List[str]:
    """Backticked identifiers adjacent to a citation, absent from its evidence."""
    out: List[str] = []
    for cit, path in _resolvable():
        window = _adjacent(cit)
        tokens = [t for t in _backticked(window) if _looks_like_identifier(t)]
        if not tokens:
            continue
        evidence, whole, span = _evidence(path, cit)
        for token in tokens:
            token = token.strip()
            if token.endswith("()"):
                token = token[:-2]
            if token in evidence:
                continue
            kind = "ELSEWHERE_IN_FILE" if token in whole else "ABSENT_FROM_FILE"
            out.append(f"  ADR-{cit.adr}:{cit.line_no} `{token}` {kind} — "
                       f"{cit.path}:{cit.start_line} (evidence "
                       f"{span[0]}..{span[1]})")
    return out


def _quote_violations() -> List[str]:
    """Quoted runs adjacent to a citation, absent from its evidence window."""
    out: List[str] = []
    for cit, path in _resolvable():
        window = _adjacent(cit)
        evidence = whole = None
        for quote in _quoted(window):
            normalised = _norm(quote)
            if len(normalised) < _MIN_QUOTE:
                continue
            if any(marker in quote for marker in _QUOTE_REJECT):
                continue                      # the multi-line-quote artefact
            if evidence is None:
                evidence, whole, _span = _evidence(path, cit)
                evidence, whole = _norm(evidence), _norm(whole)
            if normalised in evidence:
                continue
            kind = "ELSEWHERE_IN_FILE" if normalised in whole else "ABSENT_FROM_FILE"
            out.append(f"  ADR-{cit.adr}:{cit.line_no} {kind} "
                       f"{normalised[:70]!r} — {cit.path}:{cit.start_line}")
    return out


def test_no_prose_evidence_regression() -> None:
    """V3 + V4 as a DOWN-ONLY CEIL. Read this test's docstring before raising it.

    The ceiling exists because the comparison is prose-against-source and that
    comparison's normalisation step is a silent-wrong-answer surface — the
    prototype's own `_norm` produced roughly 13 false violations out of 20 by
    stripping a single underscore. An arm whose failure mode is "confidently
    reports a defect that is not there" does not get to fail a build to zero.

    Going DOWN is the whole point. Every rc415 correction — `_merge_docs` ->
    `_apply_docs`, `:645` -> `:673`/`:697`, `genome.py:8986` -> `:9137-9142` —
    was found by this arm firing and drained it.
    """
    tokens = _token_violations()
    quotes = _quote_violations()

    print(f"\n[rc415] V3 token-evidence: {len(tokens)} "
          f"(CEIL {CEIL_TOKEN_EVIDENCE}) · V4 quote-evidence: {len(quotes)} "
          f"(CEIL {CEIL_QUOTE_EVIDENCE})")
    for entry in tokens + quotes:
        print(entry)

    assert len(tokens) <= CEIL_TOKEN_EVIDENCE, (
        f"V3 token-evidence violations rose to {len(tokens)}, above "
        f"CEIL_TOKEN_EVIDENCE={CEIL_TOKEN_EVIDENCE}:\n" + "\n".join(tokens)
        + "\n\nA backticked symbol beside a citation is a claim that the "
          "symbol is AT that address. Either fix the pointer, or move the "
          "symbol name out of the citation's adjacency window if the sentence "
          "is about something else. Raising the CEIL needs a reason in the "
          "same diff.")
    assert len(quotes) <= CEIL_QUOTE_EVIDENCE, (
        f"V4 quote-evidence violations rose to {len(quotes)}, above "
        f"CEIL_QUOTE_EVIDENCE={CEIL_QUOTE_EVIDENCE}:\n" + "\n".join(quotes))

    assert len(tokens) >= 1 or len(quotes) >= 1 or True  # see next test


def test_the_ceils_are_not_slack() -> None:
    """A CEIL far above the live count is a ratchet that ratchets nothing.

    Prints the headroom every run. This is not an assertion — a drained CEIL
    is a GOOD outcome and must not fail — but an unremarked gap between the
    ceiling and the count is how a ratchet stops being one.
    """
    tokens, quotes = len(_token_violations()), len(_quote_violations())
    print(f"\n[rc415] CEIL headroom — V3 {CEIL_TOKEN_EVIDENCE - tokens}, "
          f"V4 {CEIL_QUOTE_EVIDENCE - quotes}. Lower the CEIL to the live "
          f"count when headroom appears; that is a normal commit.")
    assert tokens >= 0 and quotes >= 0


# ── V5: reported, never asserted ──────────────────────────────────────


def test_mid_block_citations_are_reported() -> None:
    """V5 REPORT-ONLY. Citations pointing INTO a block rather than at its head.

    Never a failure, and the reason is the corpus's clearest example: ADR-0013
    `:186` cites `tool_schema.py:314` and `:318`, two deliberate pointers at
    the individual sentences whose excision caused the §1.7.1 defect. Both are
    interior to the `#:` block starting at `:313`. A strict block-start rule
    flags the sentence written to FIX the defect — which is a good working
    definition of a rule that should not be a gate.
    """
    inside: List[str] = []
    for cit, path in _resolvable():
        if path.suffix != ".py":
            continue
        scope = _py_scope(path, cit.start_line)
        if scope and cit.start_line != scope[0]:
            inside.append(f"  ADR-{cit.adr}:{cit.line_no} -> {cit.path}:"
                          f"{cit.start_line} (scope starts {scope[0]})")

    print(f"\n[rc415] V5 mid-block citations: {len(inside)} — REPORTED, not "
          f"asserted. Roughly 5/17 signal on this corpus; the clearest hit is "
          f"a repair, not a defect.")
    for entry in inside:
        print(entry)
    assert len(inside) >= 0
