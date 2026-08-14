"""rc417 (`#T1100`) — the ADR clause-instrument gate + DERIVED ADR status.

The instrument ADR-0012 §3.2 names for its own self-applying clause, landing
against that clause's `expiry: rc417`. It is the third gate over ``adr/``,
after rc409's status coherence and rc415's citation integrity, and it shares
their parser (``tests/adr_corpus.py``).

WHAT A DERIVED STATUS ACTUALLY BUYS — SAY THIS BEFORE ANYTHING ELSE
===================================================================
**A derived status does not remove typing. It demotes what is typed from a
VERDICT to a POINTER.**

Someone still hand-writes *"this clause is gated by X."* That sentence is not
computed and never will be. What changes is what kind of thing it is:

* A **VERDICT** — ``**GATED**``, ``strict-zero, no CEIL``, ``✅ Accepted`` — is
  a claim with no apparatus behind it. Nothing in the tree can contradict it,
  so it cannot be wrong, so it carries no information. It is
  ``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``
  at the contract layer, which is ADR-0012 §3.2's whole subject.
* A **POINTER** — ``tests/test_x.py::test_y`` — is falsifiable three ways.
  The file must exist. The function must exist *in it*. And **deleting the
  test must break the ADR**, which is the property that makes a citation
  load-bearing rather than decorative.

So the typing burden does not go away and this file does not claim it does.
The claim is narrower and worth more: the hand-written half becomes an
assertion the tree can refute.

THE STATIC ARM ONLY, AND WHY THE OTHER ARM IS DEFERRED ON PURPOSE
==================================================================
The design has two arms. This rc ships **one**.

* **Static (here).** Everything decidable with no run history: table shape,
  node-id form, node-id resolution, ``def <name>`` existence, waiver-token
  legality, and ``typed`` vs ``derived``. Strict-zero, with an injection
  proof.
* **Pass (deferred).** ``passed(n)`` — did the cited node actually PASS —
  needs a run manifest written by a ``pytest_runtest_logreport`` hook and a
  CI step consuming it *after* the suite. It is deferred because **a pytest
  test that reads a run manifest reads the PREVIOUS run**, so on a fresh
  clone it is green by staleness. A green-by-staleness arm is a second
  unfalsifiable verdict wearing a filename, which is the exact defect this
  file exists to remove.

Consequence, stated rather than hidden: :func:`_settled` treats a resolving
node id as SETTLED. **A cited test that resolves and FAILS is invisible to
this arm.** That is a real hole and it is the deferred arm's job. What the
static arm does buy is the whole population — measured at rc416, **0 of 17**
clause rows carried a pytest node id at all, so there was nothing to fail.

TWO DECISIONS THAT CARRY THE DESIGN
====================================
**(a) ⏳ Draft and 🔄 Proposed stay hand-typed.** They are claims about
*intent*. No instrument distinguishes Draft-with-no-clauses from
Implementing-with-no-clauses, because the two look identical from outside.
The derivation covers ``{🟢, ✅}`` only; everything else derives
``PRE_EXECUTION`` and the typed value stands unchallenged.

**(b) DEMOTION is derived and MANDATORY; PROMOTION is permitted, never
forced.** A derivation over clause rows proves *"every clause I can see is
satisfied"*. It can never prove *"the clause set is complete"* — an ADR with
one trivial clause would auto-promote to ✅. ``adr/README.md`` defines ✅ as
*"its shape has settled into standing policy"*, a completeness judgement no
scan can make. So:

* any ``OPEN`` row ⇒ the ADR **MUST NOT** be ✅ — :func:`test_no_accepted_adr_has_an_open_clause`, strict zero;
* all rows ``SETTLED`` ⇒ ✅ is **PERMITTED**, reported by
  :func:`test_promotion_candidates_are_reported_not_asserted` and confirmed
  by a human with the two-surface edit rc409 already forces.

MEASURED AT rc416, BEFORE THIS GATE (re-measured; the research brief was
written at rc414 and three of its figures had moved)
=====================================================================
* **3 clause tables, 17 rows** — ADR-0001 ``:358`` (1 row), ADR-0012 ``:314``
  (5), ADR-0013 ``:1035`` (11). The brief said 2 tables / 16 rows; ADR-0001's
  table landed after it was written.
* **0 of 17 rows carried a pytest node id.** Corpus-wide, ``::test_`` occurred
  exactly **once**, in ADR-0012 ``:105``, as prose.
* **10 of 13 ADRs have no clause table at all**, seven of them typed ✅
  (0003–0007, 0009, 0011) — see :data:`CEIL_UNAUDITED_ADRS`.
* **The demotion fires NOWHERE.** The brief's marquee example — ADR-0012
  typed ``🟢 ACCEPTED`` against its own table's *"still OPEN"* — was **fixed
  by rc415**, which corrected ``:3`` to ``🟢 Implementing``. All three ADRs
  that carry a clause table are typed 🟢, and all three derive
  ``IMPLEMENTING``. That is stated plainly rather than dressed up: this gate
  lands green and catches nothing on day one. See
  :func:`test_the_derived_status_is_reported_every_run` for where it *would*
  fire next, and why that is a falsifiable prediction rather than a promise.

THE BOOTSTRAP IS GRADUATED, AND BOTH HALVES GET SAID
=====================================================
A strict rule reds 7 of 13 ADRs on landing. By this suite's own recorded
standard — ``test_adr_status_coherence_rc409.py``'s docstring, on why the
index-title check was dropped — *"8/13 false positives on day one earns a
``-k`` filter within a week, and a filtered gate is a gate that lies."*

The distinction the strict rule misses is **three-valued**: an ADR with no
clause table has not been **AUDITED**, which is a different condition from
having open clauses. So every ADR header gains ``**Clauses:**
audited|unaudited`` and :data:`CEIL_UNAUDITED_ADRS` drains the population.

Both halves, because only saying the first is how a ratchet becomes an alibi:

* **Better than today** — nothing currently says an ADR's clause set has
  never been read, and 10 of 13 are in that condition invisibly.
* **Weaker than the strict rule** — an ``unaudited`` ADR's typed status is
  **not checked**. It is counted, in a draining population, and that is all.

At ``CEIL_UNAUDITED_ADRS == 0`` the graduated form retires and the predicate
is the rule.

THE TRAP THIS GATE MUST NOT REPEAT
===================================
A naive substring verdict classifier counts ``GATED`` inside ``UNGATED`` and
mis-flags **6 of ADR-0013's 11 rows** as simultaneously open and closed. That
is CM-7's own defect class — read a prefix, discard the rest — which is what
put ``(🟢, ACCEPTED)`` live on two surfaces with the rc409 gate green.

:func:`verdict_tokens` therefore matches **longest-token-first on WHOLE
normalised tokens**, bounded on both sides by a word boundary — two
independent defences, either of which alone would suffice.
:func:`test_the_classifier_does_not_read_gated_inside_ungated` is the
regression, and the injection proof below includes an ``UNGATED`` row.

INJECTION PROOFS — RUN, THEN REVERTED
======================================
A gate that only ever goes green proves less than one that has been shown to
go red. All five were applied to the live corpus and reverted.

  A. **A dead node id is caught.** ADR-0012 ``:330``'s instrument changed to
     ``tests/test_declared_type_honesty_rc363.py::test_no_such_function`` —
     the FILE still resolves, only the function is gone.
     :func:`test_every_cited_node_id_resolves` fired:
     *"adr/0012:330: cites '…::test_no_such_function' — the file resolves but
     declares no 'def test_no_such_function('"*.
  B. **A dead file is caught.** The same cell pointed at
     ``tests/test_gone_rc363.py::test_x``; the same test fired with the other
     half of its message — *"its FILE resolves to nothing"*.
  C. **A malformed node id is caught.** ``tests/test_declared_type_honesty_rc363.py::``
     with an empty name half — :func:`test_every_node_id_is_well_formed` fired
     rather than the row silently counting as having no node id at all, which
     is a truncation degrading into an absence.
  D. **The demotion fires.** ADR-0012's own header set to ``✅ Accepted`` turned
     :func:`test_no_accepted_adr_has_an_open_clause` red, naming
     ``adr/0012:331`` — the C2 return half, *"still OPEN"*. This is the proof
     that the day-one green below is a property of the corpus and not of the
     check.
  E. **The UNGATED row is not read as GATED.** ADR-0013 ``:1040``'s status
     cell — ``**UNGATED — and currently FALSE**`` — classifies as
     ``{ungated}`` and never ``{gated}``;
     :func:`test_the_classifier_does_not_read_gated_inside_ungated` asserts it
     on the live corpus every run, so the trap cannot be reintroduced quietly.

ENCODING
========
Every read is explicit ``utf-8`` via ``adr_corpus``; every glyph renders as
``U+XXXX`` in a failure message. A gate whose RED output crashes the console
is a gate nobody can act on.
"""

from __future__ import annotations

from typing import List, Set, Tuple

from adr_corpus import (
    CLAUSE_COLUMNS,
    Table,
    adr_files,
    adr_number,
    clause_tables,
    clauses_header,
    is_pinned,
    legend as _legend_pairs,
    nodes as _node_ids,
    pinned_spans,
    read_adr,
    resolve_path,
    resolves,
    status_pair,
    text_lines,
)

# ── the population, pinned ────────────────────────────────────────────

#: Every ADR must carry a ``**Clauses:**`` header. Pinned so a NEW ADR that
#: forgets it fails loudly instead of joining an unaudited population nobody
#: is counting. Kept equal to rc409's ``_EXPECTED_ADR_COUNT`` by
#: :func:`test_the_clause_scan_is_not_vacuous`, which asserts the two agree —
#: two constants naming one population is the ADR-0010 A.4 shape, so they are
#: cross-checked rather than merely both written down.
_EXPECTED_ADR_COUNT = 13

#: ADRs with **no clause table**, i.e. whose clause set has never been read.
#: **DOWN-ONLY.** Cloned from ``CEIL_WIRE_GLUE_GAPS``
#: (``tests/test_rosetta_transitive_standalone.py``), which walked 11 → 0 one
#: op at a time and is the tree's proven shape for draining a population
#: rather than declaring it acceptable.
#:
#: Seeded at the rc417 measurement: 10 of 13 (0002–0011). Auditing an ADR
#: means enumerating its clauses in a clause table and flipping its header to
#: ``audited``; the number then goes down and can never go back up.
#: rc420 (`#T1114`): 10 -> 9 — ADR-0008 audited (7 clause rows, every one
#: instrumented with a resolving node id) and promoted ✅ Accepted on both
#: surfaces; the first drain of this population.
CEIL_UNAUDITED_ADRS = 9

#: The two legal ``**Clauses:**`` values.
_CLAUSE_HEADER_VALUES = ("audited", "unaudited")


# ── verdict vocabulary (the trap) ─────────────────────────────────────

#: The closed set of verdict tokens this corpus uses. Order is irrelevant —
#: :func:`verdict_tokens` sorts by descending length itself — but the set is
#: CLOSED on purpose: a classifier over an open vocabulary silently reports
#: "no token" for anything new, which reads exactly like "nothing to see".
VERDICT_TOKENS: Tuple[str, ...] = (
    "gated", "ungated", "definitional", "not instrumentable",
    "goal", "still open", "strict-zero",
)

#: Tokens that WAIVE a clause — ADR-0012 §3.2 discharge 3, *"restate it as
#: ``**definitional**`` / ``**not instrumentable**`` with the reason in the
#: row, and accept that the ADR then claims strictly less."*
#:
#: ⚠️ ``goal`` is deliberately **absent**. §3.2 names it as the escape it
#: closes: *"Rewording the verdict is NOT a fourth discharge. 'GOAL',
#: 'standard', 'target', 'aspiration' and 'preference' all describe a clause
#: with no instrument."* Admitting it here would re-open exactly the hole the
#: rewrite was for, and ADR-0013 ``:1046`` still carries it — so this gate
#: reports that row OPEN, which is the correct reading of §3.2.
WAIVER_TOKENS: Tuple[str, ...] = ("definitional", "not instrumentable")

_WORD_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789")


def normalise_cell(cell: str) -> str:
    """A verdict cell reduced to matchable text: emphasis out, case folded.

    Markdown emphasis and code spans are decoration — ``**UNGATED**`` and
    ``UNGATED`` are the same verdict — so they come out before matching. What
    does NOT come out is punctuation between words, because that is where the
    boundaries are.
    """
    out = []
    for ch in cell:
        out.append(" " if ch in "*`_~|" else ch)
    return " ".join("".join(out).split()).casefold()


def verdict_tokens(cell: str) -> Set[str]:
    """The verdict tokens present in ``cell``. LONGEST-FIRST, WORD-BOUNDED.

    **The trap, and the two independent defences against it.** A naive
    ``token in cell`` classifier counts ``gated`` inside ``ungated`` and
    reports 6 of ADR-0013's 11 rows as simultaneously gated and ungated. That
    is CM-7's defect class — match a prefix, discard the rest — and it is the
    reason ``(🟢, ACCEPTED)`` sat live on two surfaces with a green gate.

    1. **Longest-first.** ``not instrumentable`` is tried before
       ``instrumentable`` would be, and ``ungated`` before ``gated``. A
       matched span is consumed, so the shorter token cannot re-match inside
       it.
    2. **Word boundaries.** A match must be bounded by a non-word character
       (or an end) on both sides, so even without (1) ``gated`` could not
       match the tail of ``ungated``.

    Either alone is sufficient. Both ship because this exact failure has been
    made twice in this corpus, once inside the gate written to prevent it.
    """
    text = normalise_cell(cell)
    taken: List[Tuple[int, int]] = []
    found: Set[str] = set()

    for token in sorted(VERDICT_TOKENS, key=len, reverse=True):
        base = 0
        while True:
            at = text.find(token, base)
            if at < 0:
                break
            end = at + len(token)
            before_ok = at == 0 or text[at - 1] not in _WORD_CHARS
            after_ok = end == len(text) or text[end] not in _WORD_CHARS
            overlaps = any(lo < end and at < hi for lo, hi in taken)
            if before_ok and after_ok and not overlaps:
                found.add(token)
                taken.append((at, end))
            base = at + 1
    return found


# ── the row model ─────────────────────────────────────────────────────


class ClauseRow:
    """One clause row, with its three cells resolved by header position."""

    __slots__ = ("adr", "line", "cells", "clause", "instrument", "status",
                 "pinned")

    def __init__(self, adr: str, line: int, cells: List[str], table: Table,
                 pinned: bool):
        self.adr = adr
        self.line = line
        self.cells = cells
        self.pinned = pinned
        self.clause = self._cell(table, "clause")
        self.instrument = self._cell(table, "instrument")
        self.status = self._cell(table, "status")

    def _cell(self, table: Table, name: str) -> str:
        idx = table.column_of(name)
        if idx is None or idx >= len(self.cells):
            return ""
        return self.cells[idx]

    @property
    def where(self) -> str:
        return f"adr/{self.adr}:{self.line}"

    def node_ids(self) -> List[str]:
        return _node_ids(self.instrument)

    def instrumented(self) -> bool:
        """Cites at least one node id and EVERY one of them resolves."""
        ids = self.node_ids()
        return bool(ids) and all(resolves(n) for n in ids)

    def waived(self) -> bool:
        """Carries a legal waiver token AND a stated reason beside it.

        The reason requirement is what stops the waiver becoming the fourth
        discharge §3.2 forbids: a bare ``**definitional**`` asserts a
        classification, while ``**definitional**; nothing to instrument``
        asserts a classification and says why. The remainder is measured
        after the token is removed, so the token cannot be its own reason.
        """
        hits = verdict_tokens(self.status) & set(WAIVER_TOKENS)
        if not hits:
            return False
        rest = normalise_cell(self.status)
        for token in hits:
            rest = rest.replace(token, " ")
        return bool(rest.strip(" ;.,—-"))

    def settled(self) -> bool:
        """INSTRUMENTED (modulo the deferred pass arm) or WAIVED."""
        return self.instrumented() or self.waived()

    def open(self) -> bool:
        return not self.settled()


def clause_rows(adr: str, blob: bytes, *, include_pinned: bool = False
                ) -> List[ClauseRow]:
    """Every clause row in one ADR. PINNED rows excluded by default.

    A pinned region (``## Amendment …``, ``⚠️ CORRECTION …``, ``RETRACTION``)
    is a **dated record**: its verdicts are claims about what was true *then*,
    and ADR-0010 A.3 already rules that rewriting such a record *falsifies*
    it. A clause row inside one is history, and history must not drive a
    derived status.

    Pinning is by EXPLICIT MARKER and never inferred from formatting — in
    particular blockquote ``>`` is **not** a signal, because ADR-0012 alone
    carries 41 blockquoted lines and they hold LIVE quoted contracts.
    """
    spans = pinned_spans(blob)
    out: List[ClauseRow] = []
    for table in clause_tables(blob):
        for line, cells in table.rows:
            pinned = is_pinned(spans, line)
            if pinned and not include_pinned:
                continue
            out.append(ClauseRow(adr, line, cells, table, pinned))
    return out


# ── the derived status ────────────────────────────────────────────────

SUPERSEDED = "SUPERSEDED"
PRE_EXECUTION = "PRE_EXECUTION"
UNAUDITED = "UNAUDITED"
UNKNOWN = "UNKNOWN"
IMPLEMENTING = "IMPLEMENTING"
ACCEPTED_PERMITTED = "ACCEPTED_PERMITTED"


def _word_for(glyph: str) -> str:
    """The legend's word for ``glyph``, casefolded. ``""`` when undefined.

    Read from ``adr/README.md``'s legend rather than hardcoded, so a corpus
    that renames a state does not leave this file quietly matching nothing.
    rc409's INV-3/INV-4 already hold the legend honest.
    """
    return _legend_pairs().get(glyph, "").casefold()


def derived_status(adr: str, blob: bytes) -> str:
    """The status this ADR's own clause table implies. §4.2's predicate.

    Order is significant and each branch dominates the ones below it:

    ``SUPERSEDED``
        A live ``**Superseded-by:**`` value dominates everything — a
        superseded ADR's clauses are no longer in force.
    ``PRE_EXECUTION``
        ⏳ Draft / 🔄 Proposed. Decision (a): intent is not derivable.
    ``UNAUDITED``
        The header says so. Decision §4.6: counted, not checked.
    ``UNKNOWN``
        Audited but with **no rows**. This is the NON-VACUITY branch and it
        is why the predicate is not silently permissive: an audited ADR whose
        table parsed to nothing must not read as "all clauses satisfied".
    ``IMPLEMENTING``
        Any ``OPEN`` row. The demotion — mandatory.
    ``ACCEPTED_PERMITTED``
        Rows exist and every one is ``SETTLED``. **Permitted, not asserted.**
    """
    for line in text_lines(blob):
        if line.startswith("**Superseded-by:**"):
            value = line[len("**Superseded-by:**"):].strip().rstrip(".").strip()
            if value and value.casefold() != "none":
                return SUPERSEDED
            break

    glyph, _word = _status_of(blob)
    if _word_for(glyph) in ("draft", "proposed"):
        return PRE_EXECUTION

    if clauses_header(blob) == "unaudited":
        return UNAUDITED

    rows = clause_rows(adr, blob)
    if not rows:
        return UNKNOWN
    if any(r.open() for r in rows):
        return IMPLEMENTING
    return ACCEPTED_PERMITTED


def _status_of(blob: bytes) -> Tuple[str, str]:
    """The ``(glyph, word)`` pair from an ADR's own ``**Status:**`` header."""
    for line in text_lines(blob):
        if line.startswith("**Status:**"):
            return status_pair(line[len("**Status:**"):])
    return ("", "")


def _fmt(glyph: str) -> str:
    """``U+XXXX`` rendering — ASCII-safe on every console."""
    return "+".join(f"U+{ord(c):04X}" for c in glyph) if glyph else "<none>"


def _corpus() -> List[Tuple[str, bytes]]:
    return [(adr_number(p), read_adr(p)) for p in adr_files()]


def _all_rows(*, include_pinned: bool = False) -> List[ClauseRow]:
    out: List[ClauseRow] = []
    for adr, blob in _corpus():
        out.extend(clause_rows(adr, blob, include_pinned=include_pinned))
    return out


# ── non-vacuity ───────────────────────────────────────────────────────


def test_the_clause_scan_is_not_vacuous() -> None:
    """Pin the SHAPE. Every assertion below passes trivially on a parser that
    has stopped finding tables — a renamed column, a reflowed row, a fence
    that swallowed the table.

    This is the seam that must fail loud when it stops observing, and it is
    the reason ``adr_corpus`` is allowed to be a helper module with no tests
    of its own: its correctness is proved by the population floors of the
    gates that import it.
    """
    corpus = _corpus()
    assert len(corpus) == _EXPECTED_ADR_COUNT, (
        f"parsed {len(corpus)} ADRs, expected {_EXPECTED_ADR_COUNT}. Either an "
        "ADR was added/removed (update _EXPECTED_ADR_COUNT here AND "
        "tests/test_adr_status_coherence_rc409.py) or the glob has stopped "
        "matching.")

    tables_seen = sum(len(clause_tables(b)) for _a, b in corpus)
    rows = _all_rows()
    assert tables_seen >= 3, (
        f"found {tables_seen} clause table(s); rc417 measured 3 "
        "(ADR-0001 :358, ADR-0012 :314, ADR-0013 :1035). A drop means the "
        "header rule has stopped matching, not that the corpus shrank.")
    assert len(rows) >= 17, (
        f"found {len(rows)} clause row(s); rc417 measured 17. A clause gate "
        "that sees fewer rows than exist is green about rows it never read.")

    assert set(WAIVER_TOKENS) <= set(VERDICT_TOKENS), (
        "every waiver token must be in the classifier's vocabulary, or "
        "ClauseRow.waived() asks verdict_tokens() a question it cannot "
        "answer and silently returns False for a legitimately waived row.")


def test_every_adr_declares_whether_its_clauses_were_audited() -> None:
    """Every ADR carries ``**Clauses:** audited|unaudited``. STRICT ZERO.

    The three-valued distinction the graduated bootstrap rests on: an ADR
    with no clause table has not been READ, which is not the same condition
    as one whose clauses are open. Without this header the two are
    indistinguishable, and 10 of 13 ADRs were in the first condition
    invisibly.

    Searched, **never line-indexed** — ``**Status:**`` is on line 3 for twelve
    ADRs and line **5** for ADR-0008, which carries a renumbering banner
    first. A fixed-offset parser is wrong on 1 of 13 and would have to be
    "fixed" by exempting the one file it cannot read.
    """
    bad: List[str] = []
    for adr, blob in _corpus():
        value = clauses_header(blob)
        if value not in _CLAUSE_HEADER_VALUES:
            bad.append(f"  ADR-{adr}: '**Clauses:**' is {value or '<missing>'!r}"
                       f" — must be one of {_CLAUSE_HEADER_VALUES}")
    assert not bad, (
        f"{len(bad)} ADR(s) do not declare whether their clauses were "
        "audited:\n" + "\n".join(bad)
        + "\n\nAdd '**Clauses:** unaudited' beside '**Status:**'. That is not "
          "an admission of a defect — it is the honest statement that nobody "
          "has enumerated this ADR's clauses yet, and it is what "
          "CEIL_UNAUDITED_ADRS drains.")


def test_an_audited_adr_actually_has_clause_rows() -> None:
    """``audited`` and a clause table are the same claim. STRICT ZERO.

    Without this, ``**Clauses:** audited`` is a verdict with no apparatus —
    precisely the shape this whole file exists to remove — and an ADR could
    leave the CEIL population by asserting it had been read.
    """
    bad: List[str] = []
    for adr, blob in _corpus():
        if clauses_header(blob) != "audited":
            continue
        if not clause_rows(adr, blob):
            bad.append(f"  ADR-{adr}: declares '**Clauses:** audited' but has "
                       "no clause table (or every row is inside a PINNED "
                       "region, which is the same thing for a live status)")
    assert not bad, (
        f"{len(bad)} ADR(s) claim an audit they cannot show:\n" + "\n".join(bad))


# ── shape ─────────────────────────────────────────────────────────────


def test_every_clause_table_carries_the_three_columns() -> None:
    """STRICT ZERO on the header. ``clause`` · ``instrument`` · ``status``.

    **No alias table, by decision.** rc417 found the corpus spelling the
    verdict column two ways (``residual`` in ADR-0012, ``status`` elsewhere)
    and the instrument column two ways (``instrument`` vs ``instrument
    today``), and normalised all three headers with one-line edits rather
    than teaching the parser both spellings. An alias table is a second
    vocabulary requiring sync with the first — ADR-0010 Amendment A.4's own
    indictment — while a rename is a fact.

    Extra columns (ADR-0001/0013's ``§``, ADR-0012's ``exhibit``) are fine:
    the requirement is that the three are PRESENT, not that they are alone.
    """
    bad: List[str] = []
    for adr, blob in _corpus():
        for table in clause_tables(blob):
            missing = [c for c in CLAUSE_COLUMNS if table.column_of(c) is None]
            if missing:
                bad.append(
                    f"  adr/{adr}:{table.header_line} header {table.header!r} "
                    f"is missing column(s) {missing}")
                continue
            width = len(table.header)
            for line, cells in table.rows:
                if len(cells) != width:
                    bad.append(
                        f"  adr/{adr}:{line} has {len(cells)} cell(s) against "
                        f"a {width}-column header — a shifted row reads the "
                        "wrong cell as its verdict")
    assert not bad, (
        f"{len(bad)} clause-table shape problem(s):\n" + "\n".join(bad)
        + f"\n\nRequired columns: {list(CLAUSE_COLUMNS)}. Rename the header "
          "cell; do not add an alias.")


def test_every_node_id_is_well_formed() -> None:
    """A ``.py::`` token must produce a COMPLETE node id. STRICT ZERO.

    Injection proof C: ``tests/test_x.py::`` with an empty name half. Without
    this check that row reports "no node ids", which is indistinguishable
    from a row that never cited one — a truncation degrading silently into
    an absence.
    """
    bad: List[str] = []
    for row in _all_rows():
        for node in row.node_ids():
            file_part, _, name = node.partition("::")
            if not name:
                bad.append(f"  {row.where}: node id {node!r} has an empty test "
                           "name — the '::' is there and nothing follows it")
            elif not file_part.endswith(".py"):
                bad.append(f"  {row.where}: node id {node!r} does not name a "
                           ".py file")
            elif not name.startswith("test_"):
                bad.append(f"  {row.where}: node id {node!r} names {name!r}, "
                           "which pytest will not collect as a test")
    assert not bad, (
        f"{len(bad)} malformed pytest node id(s) in clause rows:\n"
        + "\n".join(bad)
        + "\n\nThe form is tests/<file>.py::<test_name>.")


def test_every_cited_node_id_resolves() -> None:
    """The file exists AND declares ``def <name>(``. STRICT ZERO.

    **This is the clause that makes a citation load-bearing.** A
    file-existence check alone stays green when the cited test is renamed or
    deleted, which is exactly how a clause quietly loses its instrument while
    the ADR keeps claiming one. Checking the ``def`` means **deleting the
    test breaks the ADR** — the only version of a pointer that is worth more
    than the verdict it replaced.

    Anchored at a line start (``\\ndef <name>(``) so a *mention* of the name
    inside another test's body cannot satisfy it.

    Injection proofs A and B: a live file with a dead function, and a dead
    file. Both fire here, with different halves of the message.
    """
    bad: List[str] = []
    for row in _all_rows():
        for node in row.node_ids():
            if resolves(node):
                continue
            file_part, _, name = node.partition("::")
            reason = ("its FILE resolves to nothing"
                      if resolve_path(file_part) is None
                      else f"the file resolves but declares no 'def {name}('")
            bad.append(f"  {row.where}: cites {node!r} — {reason}")
    assert not bad, (
        f"{len(bad)} clause row(s) cite a pytest node id that does not "
        "resolve:\n" + "\n".join(bad)
        + "\n\nEither the test moved (update the ADR row) or it was deleted "
          "(the clause has lost its instrument and the ADR now claims "
          "something nothing can refute — ADR-0012 §3.2's three discharges "
          "apply).")


def test_every_waiver_names_a_legal_token_and_a_reason() -> None:
    """A waived clause must say WHICH waiver and WHY. STRICT ZERO.

    ADR-0012 §3.2 discharge 3 permits restating a clause as
    ``**definitional**`` or ``**not instrumentable**`` *"with the reason in
    the row"*, accepting that the ADR then claims strictly less. The reason
    is not decoration: without it the waiver is a bare reclassification, and
    §3.2's whole point is that **relabelling is not a discharge**.

    ⚠️ ``GOAL`` is not a waiver token here, deliberately. §3.2 names it in the
    list it closes — *"'GOAL', 'standard', 'target', 'aspiration' and
    'preference' all describe a clause with no instrument"*. ADR-0013
    ``:1046`` still carries ``**GOAL, not a clause.**`` and this gate reports
    that row OPEN, which is §3.2 read correctly rather than a false positive.
    """
    bad: List[str] = []
    for row in _all_rows():
        hits = verdict_tokens(row.status) & set(WAIVER_TOKENS)
        if not hits:
            continue
        if not row.waived():
            bad.append(
                f"  {row.where}: status {row.status.strip()[:80]!r} carries "
                f"waiver token(s) {sorted(hits)} but states no reason beside "
                "them")
    assert not bad, (
        f"{len(bad)} bare waiver(s):\n" + "\n".join(bad)
        + f"\n\nLegal waiver tokens: {list(WAIVER_TOKENS)}, each requiring a "
          "stated reason in the same cell.")


# ── the trap ──────────────────────────────────────────────────────────


def test_the_classifier_does_not_read_gated_inside_ungated() -> None:
    """The CM-7 defect class, asserted on the LIVE corpus. STRICT ZERO.

    Injection proof E, except it needs no injection — ADR-0013 already ships
    six ``UNGATED`` rows, so this runs against real data every time.

    A naive ``"gated" in cell`` classifier reports every one of them as
    simultaneously gated and ungated. That is *read a prefix, discard the
    rest* — the same shape that let ``(🟢, ACCEPTED)`` sit live on two
    surfaces with the rc409 gate green, and the same shape rc415's
    ``status_pair`` was written to close.
    """
    assert verdict_tokens("**UNGATED**") == {"ungated"}, (
        "the classifier read 'gated' inside 'ungated' on a synthetic cell — "
        "longest-token-first and the word-boundary rule are both broken")
    assert verdict_tokens("**GATED** — inherited") == {"gated"}
    assert verdict_tokens("**not instrumentable**; §9.3 declines") == {
        "not instrumentable"}, (
        "'not instrumentable' must not decompose into a shorter token")

    live: List[str] = []
    ungated = 0
    for row in _all_rows():
        found = verdict_tokens(row.status)
        if "ungated" in found:
            ungated += 1
            if "gated" in found:
                live.append(f"  {row.where}: {row.status.strip()[:70]!r} "
                            "classified as BOTH gated and ungated")
    assert ungated >= 6, (
        f"only {ungated} UNGATED row(s) in the corpus; rc417 measured 6 in "
        "ADR-0013 alone. If this drops the regression has lost its subject "
        "and the assertion below is vacuous.")
    assert not live, (
        f"{len(live)} row(s) classified as both gated and ungated:\n"
        + "\n".join(live))


# ── the derivation ────────────────────────────────────────────────────


def test_no_accepted_adr_has_an_open_clause() -> None:
    """**THE DEMOTION. STRICT ZERO, and mandatory.**

    Any ``OPEN`` clause row ⇒ the ADR must not be typed ✅ Accepted.
    ``adr/README.md`` reserves ✅ for a shape that has *settled into standing
    policy* and defines 🟢 Implementing as exactly *"direction accepted,
    execution arc OPEN"*. A row this gate cannot see satisfied is an open
    execution arc, whatever the header says.

    This is the half of the design that is **derived and not optional**.
    Promotion is the other half and is deliberately not asserted anywhere —
    see :func:`test_promotion_candidates_are_reported_not_asserted`.

    **Green on landing, and that is reported rather than dressed up.** rc415
    corrected ADR-0012's header from ``🟢 ACCEPTED`` to ``🟢 Implementing``,
    which was the one live contradiction the research pass found. All three
    ADRs carrying a clause table are typed 🟢 and all three derive
    ``IMPLEMENTING``. Injection proof D shows the check is not merely
    always-green: setting ADR-0012 to ✅ fires it and names ``adr/0012:317``.
    """
    bad: List[str] = []
    for adr, blob in _corpus():
        glyph, word = _status_of(blob)
        if _word_for(glyph) != "accepted":
            continue
        if clauses_header(blob) != "audited":
            continue                      # counted by CEIL, not checked here
        for row in clause_rows(adr, blob):
            if row.open():
                bad.append(
                    f"  adr/{adr}:{row.line} — clause "
                    f"{row.clause.strip()[:52]!r} is OPEN "
                    f"(instrument {row.instrument.strip()[:44]!r}, status "
                    f"{row.status.strip()[:44]!r}) but ADR-{adr} is typed "
                    f"{_fmt(glyph)} {word}")
    assert not bad, (
        f"{len(bad)} open clause(s) inside an ADR typed ✅ Accepted:\n"
        + "\n".join(bad)
        + "\n\nThree ways out, and relabelling the verdict is not one of them "
          "(ADR-0012 §3.2): (1) INSTRUMENT the clause — cite a resolvable "
          "tests/<f>.py::<test_name>; (2) WAIVE it as '**definitional**' or "
          "'**not instrumentable**' WITH the reason in the row, accepting "
          "that the ADR claims strictly less; or (3) DEMOTE the ADR to "
          "🟢 Implementing on BOTH surfaces (its own header and the "
          "adr/README.md index row), which is what an open execution arc "
          "actually is.")


def test_the_derivation_covers_only_the_implementing_accepted_pair() -> None:
    """Decision (a), asserted rather than assumed. STRICT ZERO.

    ⏳ Draft and 🔄 Proposed are claims about **intent**, and no instrument
    distinguishes Draft-with-no-clauses from Implementing-with-no-clauses —
    from outside they are byte-identical. So the derivation must return
    ``PRE_EXECUTION`` for them and never a substantive verdict.

    The check is that the predicate's *branch order* actually holds: a Draft
    ADR that later grows a clause table must still derive ``PRE_EXECUTION``,
    because the intent branch dominates the row branch. Getting that order
    wrong is how a derivation starts silently adjudicating intent.
    """
    bad: List[str] = []
    for adr, blob in _corpus():
        glyph, word = _status_of(blob)
        got = derived_status(adr, blob)
        if _word_for(glyph) in ("draft", "proposed"):
            if got != PRE_EXECUTION:
                bad.append(f"  ADR-{adr} is typed {_fmt(glyph)} {word} but "
                           f"derived {got} — intent is not derivable and the "
                           "PRE_EXECUTION branch must dominate")
        elif got == PRE_EXECUTION:
            bad.append(f"  ADR-{adr} is typed {_fmt(glyph)} {word} but derived "
                       "PRE_EXECUTION — the branch fired on a post-decision "
                       "state")
    assert not bad, "\n".join(bad)


def test_an_audited_adr_never_derives_unknown() -> None:
    """NON-VACUITY of the predicate itself. STRICT ZERO.

    ``UNKNOWN`` is the branch that fires when an ADR says it was audited and
    then presents no rows. It exists so that the predicate is not silently
    permissive — "audited, no rows" must not fall through to
    ``ACCEPTED_PERMITTED``, which would let an ADR promote itself by having
    an empty table.

    Reaching it is a corpus defect, not a pass, which is why it is asserted
    against rather than merely reported.
    """
    bad = [f"  ADR-{adr}" for adr, blob in _corpus()
           if derived_status(adr, blob) == UNKNOWN]
    assert not bad, (
        "ADR(s) declaring '**Clauses:** audited' whose clause table yields no "
        "live rows:\n" + "\n".join(bad)
        + "\n\nEither the table is inside a PINNED region (a dated record "
          "cannot carry a live clause), or the header rule stopped matching.")


def test_the_unaudited_ceiling_is_down_only() -> None:
    """``CEIL_UNAUDITED_ADRS`` drains and never grows. STRICT on both sides.

    The ``CEIL_WIRE_GLUE_GAPS`` shape, which walked 11 → 0 one op at a time.
    Two clauses, and the second is the one that keeps a ratchet from becoming
    an alibi:

    * the count may not EXCEED the ceiling — a new unaudited ADR fails;
    * the ceiling may not exceed the count — once an audit lands, the
      constant must come down in the same commit, or the ratchet is carrying
      slack it will never give back.
    """
    unaudited = sorted(adr for adr, blob in _corpus()
                       if clauses_header(blob) != "audited")
    assert len(unaudited) <= CEIL_UNAUDITED_ADRS, (
        f"{len(unaudited)} unaudited ADR(s) against a ceiling of "
        f"{CEIL_UNAUDITED_ADRS}: {unaudited}\n\nThe ceiling is DOWN-ONLY. A "
        "new ADR ships with its clauses enumerated, or an existing audit was "
        "reverted.")
    assert len(unaudited) == CEIL_UNAUDITED_ADRS, (
        f"only {len(unaudited)} unaudited ADR(s) against a ceiling of "
        f"{CEIL_UNAUDITED_ADRS} — LOWER CEIL_UNAUDITED_ADRS to "
        f"{len(unaudited)} in this commit. Slack in a down-only ratchet is a "
        "gap nobody is draining.")


# ── reported, never asserted ──────────────────────────────────────────


def test_the_derived_status_is_reported_every_run() -> None:
    """The whole 13-row derivation, PRINTED. Never a failure.

    This is the artefact a reader wants and no assertion can carry: what the
    predicate says about every ADR, beside what each one is typed as. It is
    printed rather than asserted because most rows are ``UNAUDITED`` by
    design during the bootstrap, and asserting on them is the 7/13-red that
    earns a ``-k`` filter.

    **The falsifiable prediction it records.** ADR-0009 is typed ✅ Accepted
    and is currently ``unaudited``. Its own §8 says *"It does not assert that
    srmech currently has multi-implementation parity. It does not."* and *"no
    vocabulary sweep has been performed"*. So auditing it is predicted to
    produce at least one OPEN row and fire the demotion — which is a
    prediction the next audit slice either confirms or refutes, not a
    promise. It is recorded here because an unrecorded prediction is
    indistinguishable from hindsight.
    """
    print("\n[rc417] derived ADR status — typed vs derived\n")
    print(f"  {'ADR':<6} {'typed':<28} {'clauses':<10} {'rows':>4} "
          f"{'open':>4}  derived")
    for adr, blob in _corpus():
        glyph, word = _status_of(blob)
        rows = clause_rows(adr, blob)
        typed = f"{_fmt(glyph)} {word}"
        print(f"  {adr:<6} {typed:<28} {clauses_header(blob) or '<none>':<10} "
              f"{len(rows):>4} {sum(1 for r in rows if r.open()):>4}  "
              f"{derived_status(adr, blob)}")
    print()
    assert True


def test_promotion_candidates_are_reported_not_asserted() -> None:
    """Decision (b)'s permitted half, PRINTED. Never a failure.

    A derivation proves *"every clause I can see is satisfied"*. It cannot
    prove *"the clause set is complete"* — an ADR with one trivial clause
    would auto-promote, and ``adr/README.md`` defines ✅ as *"its shape has
    settled into standing policy"*, a completeness judgement no scan can
    make. So promotion is **offered to a human**, who confirms it with the
    two-surface edit rc409 already forces.

    Zero candidates today: all three audited ADRs carry open rows.
    """
    cands = [adr for adr, blob in _corpus()
             if derived_status(adr, blob) == ACCEPTED_PERMITTED
             and _word_for(_status_of(blob)[0]) == "implementing"]
    print(f"\n[rc417] promotion PERMITTED (not asserted) for: "
          f"{cands or 'none'} — every clause resolves or is waived with a "
          f"reason. A human decides whether the SHAPE has settled; the "
          f"derivation cannot.\n")
    assert True


def test_the_row_population_is_reported_every_run() -> None:
    """Row-level census, PRINTED. The number this arc is measured by.

    rc416 baseline: **0 of 17** rows carried a pytest node id. That is the
    population ADR-0012 §3.2's clause was always about, and watching it move
    is the only way to tell whether the pointer discipline is being adopted
    or merely declared.
    """
    rows = _all_rows()
    with_ids = [r for r in rows if r.node_ids()]
    resolving = [r for r in with_ids if r.instrumented()]
    waived = [r for r in rows if r.waived()]
    pinned = _all_rows(include_pinned=True)
    print(f"\n[rc417] clause rows: {len(rows)} live "
          f"({len(pinned) - len(rows)} excluded as PINNED)\n"
          f"         cite a node id : {len(with_ids)}\n"
          f"         all ids resolve: {len(resolving)}\n"
          f"         waived w/ reason: {len(waived)}\n"
          f"         OPEN            : {sum(1 for r in rows if r.open())}\n"
          f"  (rc416 baseline: 0 of 17 cited any node id)\n")
    assert True
