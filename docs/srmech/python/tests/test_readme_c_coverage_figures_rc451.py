"""rc451 (`#T1164`, closing `#T1163`) — the two UNGATED C-coverage cardinals in
``python/README.md``, tied to the values they describe.

THE DEFECT, MEASURED
====================
One shipped sentence in the PyPI long-description carried two undated literals:

    The shared dispatch table `CR_OP_REG` holds **20 op spellings** at
    v0.9.0rc450 ... a bare-C host runs **9 of the 18** chains from their
    descriptors today, measured by execution.

Both were TRUE at rc450 and both went FALSE the moment rc451 landed (24 and 10).
Neither had a gate: grepping ``tests/`` for ``CR_OP_REG``, ``op spellings`` and
``9 of the 18`` at rc450 found only
``test_t1158_registry_param_order_rc449.py``'s own docstring and marker
literals, none of which reads the README. The "9 of the 18" half was already
FILED as `#T1163` — *true but undated and ungated, so it goes stale the moment
the ceiling moves* — and the "20 op spellings" half was filed nowhere, a second
undated figure in the same sentence with the same failure mode.

WHY A GATE RATHER THAN A FIX
============================
Fixing the numbers is what rc451 would have done anyway; it does not stop rc452
from repeating it. This is the tree's own answer to that shape — "a number
written as a literal, with no tie to the value it describes, rots, while the
same number written as a live lookup cannot" (``test_readme_currency_rc419``'s
docstring). "Ungated surfaces trickle; gated ones race to 100%."

WHAT EACH ASSERTION KEYS ON — nothing here compares a literal to a literal:
  * the op-spelling count is PARSED out of ``CR_OP_REG``'s initialiser in
    ``c/src/srmech_compose_run.c`` (the initialiser, not a grep — a grep also
    catches the ``cr_op_is`` arms and over-counts, which is what the README
    sentence itself says);
  * the running-chain count is DERIVED as ``executable - CEIL_C_REJECTED_CHAINS``
    from the live catalog and the rc446 ratchet, the two artifacts that actually
    own it.

rc454 (`#T1159`, gh #1653) — FOUR MORE README CLAIMS, THREE OF THEM UNGATED
==========================================================================
The rc453 sweep found the same failure mode three doors down from the paragraph
this file already owns, so the widening lands here rather than in a new file:
this module is already declared in ``SCAN_ROOTS`` for both ``docs/srmech/python``
and ``docs/srmech/c``, and it already parses the C tree. ``test_readme_currency_rc419``
was the wrong home — its scope is literally ``README.md`` and it reaches above
``python/`` nowhere, so adding a header read there would red
``test_no_test_reaches_out_of_tree_without_declaring_it``.

  * **the worked ``describe()["cascade_catalog"]`` block** printed SIX keys while
    the live mapping returns SEVEN — ``c_runnable`` was missing. A worked block is
    captured OUTPUT; an omitted key is a fabricated result, not a stale citation
    (the rc419 ruling, applied to a second block). Both the KEY SET and the
    integers are pinned live.
  * **"one projection today — a declarative oracle whose executable projection is
    Python"** led the paragraph below it while that paragraph's own body said a
    bare-C host runs 18 of the 18 chains. Self-refuting on the page, live-refuted
    by ``c_runnable == executable``. Pinned as a forbidden PHRASE keyed to that
    equality — rc452's ``_MAP_DENIALS`` pattern, second instance — so the denial
    becomes legal again the moment the C projection genuinely falls behind.
  * **"a host with no Python present can ... run cascades"** in the opening
    two-implementations paragraph. TRUE today and false at rc446, when
    ``c_runnable`` was 9 against 18 executable; rc452 cured it and nothing
    watches it. Same equality, opposite polarity: the sentence's presence
    REQUIRES the equality.
  * **"14 of the 21 descriptors name a dedicated ``libsrmech`` symbol ... 5 of the
    remaining 7 are ``cyclic_mod_*`` wrappers"**. Measured TRUE, undated, ungated.
    ⚠️ The 14 was flagged as a 12 during the rc453 sweep and the flag was
    REFUTED — it was two cancelling miscounts. It is derived live here from the
    descriptors themselves so nobody has to re-adjudicate it, and the restated
    "all 14 verified present in ``c/include/srmech.h``" is checked by actually
    resolving every declared symbol against the header rather than trusting the
    restatement (rc452's lesson: a figure and its restatement were different
    strings, so nothing compared them).

THE DATED-CLAUSE CARVE-OUT, AND WHY IT IS NOT APPLIED GLOBALLY
=============================================================
``README.md:330`` reads *"At v0.9.0rc447: **21 descriptors — 18 executable, 3
leaf**"*. That dates itself, and it is currently live-equal by coincidence.
Keying it to the live catalog would fabricate history the day the catalog grows,
so :func:`_search_undated` skips any match preceded on its own line by an
``At/as of/Measured at v0.9.0rcN`` clause — the same carve-out
``test_readme_currency_rc419`` documents for narrative rc citations.

**It is applied to the two rc454 census patterns ONLY, deliberately.** The
paragraph the rc451 assertions above own contains the words "as of v0.9.0rc452"
in its own body, so a globally-applied line-scoped carve-out would silently
excuse every cardinal in the single most defect-prone sentence in this document.
A carve-out wide enough to protect a dated ledger row is wide enough to blind the
gate; scope it per-pattern, not per-file.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat
from srmech.introspect import describe

_README = Path(__file__).resolve().parents[1] / "README.md"
_COMPOSE_C = (Path(__file__).resolve().parents[2] / "c" / "src"
              / "srmech_compose_run.c")
#: rc454 — the public header the README's "all 14 verified present" restates.
_SRMECH_H = (Path(__file__).resolve().parents[2] / "c" / "include"
             / "srmech.h")

#: "... holds **24 op spellings** at v0.9.0rc451 ..."
_OP_SPELLINGS = re.compile(r"\*\*(\d+) op spellings\*\*")

#: "... runs **10 of the 18** chains from their descriptors today ..."
_CHAINS_RUN = re.compile(r"runs \*\*(\d+) of the (\d+)\*\* chains")

#: rc452 (`#T1171`) — "... `CEIL_C_REJECTED_CHAINS`, which is **7** ...". The
#: rc451 gate derived the running count from this ceiling but never read the
#: ceiling's own literal where the README RESTATES it, so mid-rc452 prose
#: said `8` beside a gated `11 of the 18` and satisfied every assertion here.
#: The two were self-refuting on one line — `18 - 8 = 10`, not 11 — and nothing
#: compared them, because the derivation and the restatement were different
#: strings.
_REJECTED_CEIL = re.compile(r"`CEIL_C_REJECTED_CHAINS`, which is \*\*(\d+)\*\*")

#: rc452 — "... counts **0 of 3 forms unsupported** ...". rc452 drove
#: CEIL_SURFACE_A_UNSUPPORTED_FORMS to 0 in the same change that added the map
#: form and left the README saying 2.
_FORMS_UNSUPPORTED = re.compile(
    r"\*\*(\d+) of (\d+) forms unsupported\*\*")

#: rc452 — the PROSE claim, not a cardinal. Through rc451 the README said the C
#: peer "does not execute `map` at all"; rc452 added `cr_step_map` and the
#: sentence survived the release. A number gate cannot see this one, so it is
#: pinned as a forbidden phrase keyed to the live form ceiling.
_MAP_DENIALS = (
    "does not execute `map` at all",
    "`map` does not run at all",
)

#: rc454 — the SECOND instance of the forbidden-phrase shape, and the same
#: conditioning. Through rc453 the paragraph opened by declaring the declarative
#: oracle to have one executable projection, Python, while its own body two
#: sentences later said a bare-C host runs 18 of the 18 chains. Keyed to
#: ``c_runnable == executable``, matched case-insensitively.
_ONE_PROJECTION_DENIALS = (
    "one projection today",
    "whose executable projection is python",
)

#: rc454 — README:36, the opening two-implementations paragraph.
_NO_PYTHON_CLAIM = re.compile(
    r"no Python present\*\* can serve tools, run cascades, and speak the bus")

#: rc454 — README:340, "14 of the 21 descriptors name a dedicated `libsrmech`
#: symbol in `[cascade.native]`".
_NATIVE_CENSUS = re.compile(
    r"(\d+) of the (\d+) descriptors name a dedicated `libsrmech` symbol")

#: rc454 — the RESTATEMENT of the same figure on the same line, "(all 14
#: verified present in `c/include/srmech.h`)". rc452's lesson was that a figure
#: and its restatement are different strings and nothing compares them.
_NATIVE_VERIFIED = re.compile(
    r"\(all (\d+) verified present in `c/include/srmech\.h`\)")

#: rc454 — "5 of the remaining 7 are `cyclic_mod_*` wrappers".
_DELEGATE_CENSUS = re.compile(
    r"(\d+) of the remaining (\d+) are `cyclic_mod_\*` wrappers")

#: rc454 (conductor, post-verification) — the bare-C ctest host whose ``ROWS[]``
#: table the README's chain/row pair restates.
_HOST_C = (Path(__file__).resolve().parents[2] / "c" / "test"
           / "test_srmech_cascade_toml_host.c")

#: rc454 — "... all **18** executable chains (**20** rows: ...". THE TAIL OF THE
#: SENTENCE THE rc454 GATE WAS ALREADY STANDING ON. Slice 3 keyed the
#: ``14 of the 21`` and ``5 of the remaining 7`` clauses EARLIER IN THIS SAME
#: LINE to live values and stopped there; the chain/row pair a few clauses later
#: said ``15 running chains (16 rows`` — false since rc452 — and the closing
#: clause said ``the 3 blocked chains still decline in C`` while the paragraph
#: three lines above said ``18 of the 18`` and ``CEIL_C_REJECTED_CHAINS, which
#: is 0``. A stranger read both inside one screen. Two adversarial verifiers
#: found it independently after the build slices reported done, which is the
#: whole argument for the verify phase.
_CTEST_CHAINS = re.compile(
    r"all \*\*(\d+)\*\* executable chains \(\*\*(\d+)\*\* rows")

#: rc454 — the THIRD instance of the forbidden-phrase shape. Conditioned on
#: ``CEIL_C_REJECTED_CHAINS == 0``: while chains really do decline, the sentence
#: is legitimate history; once the ceiling reaches 0 the clause has no subject
#: and must be gone. Keyed to the ceiling, never to a release token.
_BLOCKED_DENIALS = (
    "blocked chains still decline",
    "chains still decline in c",
)

#: rc454 — the dated-clause carve-out. See the module docstring: applied to the
#: two census patterns ONLY, never file-wide.
_DATED_CLAUSE = re.compile(
    r"(?:\bAt\b|\bat\b|\bAs of\b|\bas of\b|\bMeasured at\b|\bmeasured at\b)"
    r"\s+v0\.9\.0rc\d+")

#: rc454 — a top-level ``'key':`` inside the worked comment block.
_BLOCK_KEY = re.compile(r"'([A-Za-z_][A-Za-z0-9_]*)'\s*:")


def _text(path: Path) -> str:
    with io.open(path, "r", encoding="utf-8", errors="replace",
                 newline=None) as fh:
        return fh.read()


def _cr_op_reg_size() -> int:
    """The op-spelling count, PARSED from the C initialiser.

    PREDICATE: find ``} CR_OP_REG[`` ... ``= {``, take the text to the closing
    ``};``, and count the ``{ "bare", <len>u, "full" }`` rows. Deliberately the
    row count and not the declared array size, so a declared size that outran
    its rows could not satisfy this.
    """
    text = _text(_COMPOSE_C)
    m = re.search(r"\}\s*CR_OP_REG\[(\d+)\]\s*=\s*\{", text)
    assert m, ("CR_OP_REG's initialiser was not found in %s — the declaration "
               "was reshaped and this parse has stopped observing. Re-point it; "
               "do not delete the assertion." % _COMPOSE_C.name)
    body = text[m.end():text.index("};", m.end())]
    rows = re.findall(r'\{\s*"([A-Za-z0-9_]+)"\s*,\s*(\d+)u\s*,\s*"', body)
    assert rows, "CR_OP_REG parsed to ZERO rows; an empty parse is not a count"
    declared = int(m.group(1))
    assert declared == len(rows), (
        "CR_OP_REG declares size %d but its initialiser holds %d rows"
        % (declared, len(rows)))
    return len(rows)


def _chains_running_in_c() -> tuple:
    """(running, executable), derived from the catalog and the rc446 ceiling."""
    import test_c_cascade_parity_ratchet_rc446 as ratchet
    catalog = _cat.load_catalog()
    executable = sum(1 for d in catalog.values()
                     if _cc.descriptor_status(d) == "executable")
    return executable - ratchet.CEIL_C_REJECTED_CHAINS, executable


def _ratchet():
    import test_c_cascade_parity_ratchet_rc446 as ratchet
    return ratchet


def _live_cascade_catalog() -> dict:
    """``describe()["cascade_catalog"]``, with ``c_runnable``'s EXISTENCE asserted.

    ``c_runnable`` carries exactly one other guard tree-wide (the key-set pin in
    ``test_notebook_currency_rc420``), so a ``.get("c_runnable", 0)`` here would
    make two rc454 assertions silently vacuous the day the key is dropped. Read
    it by subscript, and say so if it is gone.
    """
    live = describe()["cascade_catalog"]
    assert "c_runnable" in live, (
        "describe()['cascade_catalog'] no longer reports 'c_runnable'. Two "
        "README claims are keyed to c_runnable == executable; without the key "
        "they are not weaker, they are unmeasurable. Re-point them at whatever "
        "replaced it; do not default the value.")
    return live


def _search_undated(pattern: "re.Pattern[str]", text: str):
    """First match of ``pattern`` that is NOT inside a dated clause.

    A match is skipped when its own line carries an ``At/as of/Measured at
    v0.9.0rcN`` clause BEFORE it — that is a ledger row recording what was true
    at a named release, and keying it live would fabricate history the moment
    the value moves. README:330 is the site this exists for.
    """
    for m in pattern.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        if _DATED_CLAUSE.search(text[line_start:m.start()]):
            continue
        return m
    return None


def _comment_block_keys(block: str) -> set:
    """Top-level keys of a ``#``-commented dict transcript.

    The nested ``status`` mapping is collapsed FIRST (``{[^{}]*}`` matches only
    an innermost brace pair), so descriptor names inside it are not mistaken for
    keys of the outer mapping.
    """
    flat = re.sub(r"\{[^{}]*\}", "{}", block)
    return set(_BLOCK_KEY.findall(flat))


def _worked_cascade_block(text: str) -> str:
    """The commented transcript printed under ``describe()["cascade_catalog"]``."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == 'describe()["cascade_catalog"]':
            body = []
            for nxt in lines[i + 1:]:
                if not nxt.lstrip().startswith("#"):
                    break
                body.append(nxt.lstrip().lstrip("#").strip())
            return " ".join(body)
    return ""


def _native_symbol_census() -> dict:
    """Per-descriptor native backing, DERIVED from the shipped descriptors.

    ``with_c_symbol`` — descriptors whose ``[cascade.native]`` carries any key
    beginning ``c_symbol`` (``c_symbol``, ``c_symbol_f64``, ``c_symbol_i64``, …;
    one descriptor may declare several, which is why this counts DESCRIPTORS and
    collects the symbol strings separately).
    ``cyclic_delegates`` — of the remainder, those named ``cyclic_mod_*`` that
    declare ``[cascade.delegates_to].primitive_c_symbol``. ``cyclic_gcd`` also
    declares one but is not in the remainder, because it carries a dedicated
    symbol of its own; that is exactly the distinction the README sentence draws.
    """
    catalog = _cat.load_catalog()
    with_c, symbols, remainder = [], [], []
    for name in sorted(catalog):
        cascade = catalog[name].get("cascade") or {}
        native = cascade.get("native") or {}
        declared = [v for k, v in sorted(native.items())
                    if k.startswith("c_symbol")]
        if declared:
            with_c.append(name)
            symbols.extend(declared)
        else:
            remainder.append(name)
    cyclic = [n for n in remainder
              if n.startswith("cyclic_mod_")
              and ((catalog[n].get("cascade") or {}).get("delegates_to")
                   or {}).get("primitive_c_symbol")]
    return {"total": len(catalog), "with_c_symbol": with_c,
            "symbols": symbols, "remainder": remainder,
            "cyclic_delegates": cyclic}


def test_readme_rejected_chain_ceiling_matches_the_ratchet() -> None:
    """rc452 (`#T1171`). The README RESTATES `CEIL_C_REJECTED_CHAINS` inline;
    pin that literal to the ratchet that owns it.

    This is the assertion whose absence let mid-rc452 prose say `8` beside a gated
    `11 of the 18`. The derivation below is the same one
    ``test_readme_running_chain_cardinal_matches_the_live_ceiling`` uses, so if
    both figures are present they cannot disagree with each other either.
    """
    m = _REJECTED_CEIL.search(_text(_README))
    assert m, ("no '`CEIL_C_REJECTED_CHAINS`, which is **N**' clause found in "
               "python/README.md — it was rephrased and this gate has stopped "
               "observing. Re-point the regex; do not delete the assertion.")
    live = _ratchet().CEIL_C_REJECTED_CHAINS
    assert int(m.group(1)) == live, (
        "python/README.md restates CEIL_C_REJECTED_CHAINS as %s; the ratchet "
        "holds %d. This text ships as the PyPI long-description, and the "
        "restated figure is the one a reader subtracts — at rc452 it said 8 "
        "beside a gated '11 of the 18', inviting 18-8=10."
        % (m.group(1), live))


def test_readme_unsupported_form_count_matches_the_ceiling() -> None:
    """rc452 (`#T1171`). One rc452 commit drove CEIL_SURFACE_A_UNSUPPORTED_FORMS to 0 and
    left the README advertising 2."""
    m = _FORMS_UNSUPPORTED.search(_text(_README))
    assert m, ("no '**N of M forms unsupported**' cardinal found in "
               "python/README.md — it was rephrased and this gate has stopped "
               "observing.")
    ratchet = _ratchet()
    live = ratchet.CEIL_SURFACE_A_UNSUPPORTED_FORMS
    total = len(ratchet.SURFACE_A_STEP_FORMS)
    assert (int(m.group(1)), int(m.group(2))) == (live, total), (
        "python/README.md says %s of %s step forms are unsupported; the live "
        "ceiling is %d of %d (CEIL_SURFACE_A_UNSUPPORTED_FORMS over "
        "SURFACE_A_STEP_FORMS)."
        % (m.group(1), m.group(2), live, total))


def test_readme_does_not_deny_a_form_the_c_peer_now_runs() -> None:
    """rc452 (`#T1171`). The PROSE half of the same defect.

    Numbers were not the only thing rc452 falsified: the README still said the
    C peer "does not execute `map` at all" in the release that added
    `cr_step_map`. A cardinal gate cannot see a sentence, so this keys the
    forbidden phrasing to the live form ceiling — the denial is only a defect
    while the ceiling says every form runs, and the assertion says so rather
    than banning the words unconditionally.
    """
    ratchet = _ratchet()
    if ratchet.CEIL_SURFACE_A_UNSUPPORTED_FORMS != 0:
        return  # a form really is unsupported; the denial may be accurate
    text = _text(_README)
    present = [p for p in _MAP_DENIALS if p in text]
    assert not present, (
        "python/README.md still denies the C peer executes `map` (%s) while "
        "CEIL_SURFACE_A_UNSUPPORTED_FORMS is 0 and SURFACE_A_STEP_FORMS lists "
        "%r — every form executes. rc452 added `cr_step_map` and shipped this "
        "sentence unchanged in the PyPI long-description."
        % ("; ".join(repr(p) for p in present), list(ratchet.SURFACE_A_STEP_FORMS)))


def test_readme_op_spelling_cardinal_matches_the_c_table() -> None:
    m = _OP_SPELLINGS.search(_text(_README))
    assert m, ("no '**N op spellings**' cardinal found in python/README.md — "
               "the sentence was rephrased and this gate has stopped "
               "observing. Re-point the regex; do not delete the assertion.")
    live = _cr_op_reg_size()
    assert int(m.group(1)) == live, (
        "python/README.md advertises %s op spellings in CR_OP_REG; the C "
        "initialiser holds %d. This text ships as the PyPI long-description. "
        "It was an UNDATED literal with no gate until rc451, and rc451's four "
        "new arms are exactly the kind of change that falsifies it silently."
        % (m.group(1), live))


def test_readme_running_chain_cardinal_matches_the_live_ceiling() -> None:
    """`#T1163`, closed. The sentence is now keyed to the ratchet that owns the
    number instead of restating it."""
    m = _CHAINS_RUN.search(_text(_README))
    assert m, ("no 'runs **N of the M** chains' sentence found in "
               "python/README.md — it was rephrased and this gate has stopped "
               "observing.")
    running, executable = _chains_running_in_c()
    assert (int(m.group(1)), int(m.group(2))) == (running, executable), (
        "python/README.md says a bare-C host runs %s of the %s chains; the "
        "live derivation is %d of %d (executable descriptors minus "
        "CEIL_C_REJECTED_CHAINS). Filed as `#T1163` at rc450 precisely because "
        "the sentence was true, undated and ungated — so it would go stale on "
        "the next decrement, which is what rc451 is."
        % (m.group(1), m.group(2), running, executable))


def _ctest_host_rows() -> tuple:
    """``(distinct_descriptors, rows)`` parsed from the ctest host's ``ROWS[]``.

    Parsed from the INITIALISER, not grepped file-wide: a bare grep for
    ``"*.toml"`` also catches the header comment and the per-row error strings
    and over-counts. Two descriptors contribute two rows each
    (``kuramoto_step``'s general variant and ``klein4_from_one``'s wound
    variant, each driven from its own ``[[cascade.chain]]`` entry), so the two
    numbers are genuinely different quantities and BOTH are pinned.
    """
    src = _text(_HOST_C)
    start = src.index("ROWS[] = {")
    end = src.index("\n};", start)
    body = src[start:end]
    names = re.findall(r'"([a-z0-9_]+\.toml)"', body)
    return len(set(names)), len(names)


def test_readme_ctest_chain_and_row_cardinals_match_the_host_table() -> None:
    """rc454 — the tail of the sentence the gate was already standing on.

    Slice 3 keyed the two clauses at the START of README:340 to live values and
    stopped; the chain/row pair a few clauses later still read ``15 running
    chains (16 rows`` — false since rc452 — and nothing compared it to anything.
    Both cardinals are now derived from the ctest host's own ``ROWS[]`` table,
    so the prose and the C fixture cannot drift apart again.
    """
    m = _CTEST_CHAINS.search(_text(_README))
    assert m, ("no 'all **N** executable chains (**M** rows' clause found in "
               "python/README.md — it was rephrased and this gate has stopped "
               "observing. Re-point the regex; do not delete the assertion.")
    distinct, rows = _ctest_host_rows()
    assert (int(m.group(1)), int(m.group(2))) == (distinct, rows), (
        "python/README.md says the bare-C ctest host covers %s chains over %s "
        "rows; c/test/test_srmech_cascade_toml_host.c's ROWS[] holds %d "
        "distinct descriptors over %d rows. This clause read '15 running "
        "chains (16 rows' until rc454 — false since rc452 — while the same "
        "section said '18 of the 18' three lines above."
        % (m.group(1), m.group(2), distinct, rows))


def test_readme_does_not_claim_blocked_chains_while_the_ceiling_is_zero() -> None:
    """rc454 — a claim a NUMBER gate cannot see, so it is a forbidden phrase.

    README:340 ended '...and the 3 blocked chains still decline in C for the
    op-level reasons enumerated above'. That clause lost its subject when
    ``CEIL_C_REJECTED_CHAINS`` reached 0 at rc452, and it directly contradicted
    the paragraph three lines above it. Conditioned on the ceiling rather than
    banned outright: while chains really do decline the sentence is legitimate.
    """
    running, executable = _chains_running_in_c()
    if running != executable:
        pytest.skip(
            "chains genuinely decline in C (%d of %d run), so a sentence "
            "saying so is true and this gate has nothing to forbid"
            % (running, executable))
    # ⚠️ CODE SPANS ARE EXEMPT, and this is the tree's own standing convention
    # rather than a convenience: the ref-notation rule says a bad ref quoted as
    # a code span is "the legitimate way to *quote* a bad ref while documenting
    # it", and any mechanical check "MUST exempt code spans". The same applies
    # here — rc454's retraction note quotes the removed clause verbatim so a
    # reader can see what changed, and a gate that forbade the quotation would
    # forbid documenting the fix. Stripping spans BEFORE the search keeps the
    # live-prose predicate strict while leaving the retraction sayable.
    low = re.sub(r"`[^`]*`", "", _text(_README)).lower()
    hits = [p for p in _BLOCKED_DENIALS if p in low]
    assert not hits, (
        "python/README.md still claims chains decline in C — %r — while every "
        "one of the %d executable chains runs there (CEIL_C_REJECTED_CHAINS is "
        "0). The same section already says '%d of the %d', so the file "
        "contradicts itself on the PyPI long-description surface."
        % (hits, executable, running, executable))


def test_readme_worked_cascade_catalog_block_prints_every_live_key() -> None:
    """rc454 (`#T1159`). The worked block is captured OUTPUT, so an omitted key
    is a fabricated result — the rc419 ruling, applied to a second block.

    Through rc453 it printed six keys against a live seven, dropping exactly the
    one (``c_runnable``) that refutes the paragraph four lines below it. Both the
    KEY SET and the integers are pinned, because either half can rot alone.
    """
    block = _worked_cascade_block(_text(_README))
    assert block, (
        "no worked transcript found under `describe()[\"cascade_catalog\"]` in "
        "python/README.md — the block was reshaped and this gate has stopped "
        "observing. Re-point the locator; do not delete the assertion.")
    live = _live_cascade_catalog()
    printed = _comment_block_keys(block)
    assert printed == set(live), (
        "the worked describe()['cascade_catalog'] block prints keys %r; the "
        "live mapping returns %r. A worked block is captured OUTPUT — a missing "
        "key is a fabricated result, not a stale citation. It printed six of "
        "seven through rc453, omitting c_runnable."
        % (sorted(printed), sorted(live)))
    for key in ("total", "executable", "leaf", "c_runnable"):
        m = re.search(r"'%s':\s*(\d+)" % key, block)
        assert m, (
            "the worked block no longer prints an integer for %r" % key)
        assert int(m.group(1)) == live[key], (
            "the worked block prints %s=%s; describe()['cascade_catalog'] "
            "returns %s." % (key, m.group(1), live[key]))


def test_readme_does_not_deny_the_c_projection_it_now_has() -> None:
    """rc454 (`#T1159`). The PROSE half again — ``_MAP_DENIALS``, second instance.

    Through rc453 the catalog paragraph opened *"one projection today — a
    declarative oracle whose executable projection is Python"* while its own body
    said a bare-C host runs 18 of the 18 chains, and README:340 described a ctest
    running the descriptors with no Python process anywhere. Self-refuting on the
    page. The ban is CONDITIONED on ``c_runnable == executable``, so the sentence
    becomes legal again the moment the C projection genuinely falls behind —
    which is the difference between a gate and a word filter.
    """
    live = _live_cascade_catalog()
    if live["c_runnable"] != live["executable"]:
        return  # the C projection really is behind; the claim may be accurate
    lowered = _text(_README).lower()
    present = [p for p in _ONE_PROJECTION_DENIALS if p in lowered]
    assert not present, (
        "python/README.md still says the declarative catalog has one executable "
        "projection (%s) while describe()['cascade_catalog'] reports "
        "c_runnable=%d against executable=%d. This text ships as the PyPI "
        "long-description, and the same paragraph already says a bare-C host "
        "runs every chain."
        % ("; ".join(repr(p) for p in present),
           live["c_runnable"], live["executable"]))


def test_readme_no_python_present_claim_is_backed_by_c_runnable() -> None:
    """rc454 (`#T1159`). README:36 — *"a host with no Python present can serve
    tools, run cascades, and speak the bus"*.

    Same equality, opposite polarity to the test above: here the sentence's
    PRESENCE requires ``c_runnable == executable``. It was FALSE at rc446, when
    9 of 18 executable descriptors ran in C, and rc452 cured it without anything
    starting to watch it. This is the opening orientation paragraph — the third
    sentence of the project page — so a silent re-falsification is the highest-
    reach version of this defect in the document.
    """
    m = _NO_PYTHON_CLAIM.search(_text(_README))
    assert m, ("no 'no Python present** can serve tools, run cascades, and "
               "speak the bus' claim found in python/README.md — the sentence "
               "was rephrased and this gate has stopped observing. Re-point the "
               "regex; do not delete the assertion.")
    live = _live_cascade_catalog()
    assert live["c_runnable"] == live["executable"], (
        "python/README.md's opening paragraph claims a host with no Python "
        "present can run cascades, but describe()['cascade_catalog'] reports "
        "c_runnable=%d against executable=%d — %d declared chain(s) do not run "
        "in C. Either the coverage regressed or the sentence needs the shortfall "
        "named, which is what README:38 promises the reader."
        % (live["c_runnable"], live["executable"],
           live["executable"] - live["c_runnable"]))


def test_readme_native_symbol_census_matches_the_descriptors() -> None:
    """rc454 (`#T1159`). README:340's two cardinals, derived from the descriptors.

    ⚠️ The first figure was flagged as *"should be 12"* during the rc453 sweep
    and the flag was REFUTED — 14 is correct, and the 12 was two cancelling
    miscounts. Deriving it live is how that adjudication stops needing to be
    remembered. The sentence's own restatement ("all 14 verified present in
    `c/include/srmech.h`") is checked by RESOLVING every declared symbol against
    the header, not by comparing the two literals: rc452 shipped a figure and a
    restatement that disagreed precisely because they were different strings.
    """
    text = _text(_README)
    census = _native_symbol_census()
    live_total = _live_cascade_catalog()["total"]
    assert census["total"] == live_total, (
        "load_catalog() holds %d descriptors while describe()"
        "['cascade_catalog']['total'] says %d — the two catalog readings "
        "disagree, which is a defect in the package, not in the prose."
        % (census["total"], live_total))

    m = _search_undated(_NATIVE_CENSUS, text)
    assert m, ("no undated 'N of the M descriptors name a dedicated `libsrmech` "
               "symbol' cardinal found in python/README.md — the sentence was "
               "rephrased and this gate has stopped observing. Re-point the "
               "regex; do not delete the assertion.")
    assert (int(m.group(1)), int(m.group(2))) == (
        len(census["with_c_symbol"]), census["total"]), (
        "python/README.md says %s of the %s descriptors name a dedicated "
        "libsrmech symbol; the descriptors themselves declare %d of %d "
        "(a [cascade.native] key beginning 'c_symbol'). Descriptors WITH one: "
        "%r. Without: %r."
        % (m.group(1), m.group(2), len(census["with_c_symbol"]),
           census["total"], census["with_c_symbol"], census["remainder"]))

    restated = _NATIVE_VERIFIED.search(text)
    assert restated, (
        "python/README.md no longer restates the census as '(all N verified "
        "present in `c/include/srmech.h`)' — the restatement this gate pairs "
        "with the header read has been rephrased away.")
    assert int(restated.group(1)) == len(census["with_c_symbol"]), (
        "python/README.md restates the native-symbol census as %s where the "
        "cardinal beside it derives to %d. rc452's defect was exactly this "
        "shape: a figure and its restatement in one sentence, compared by "
        "nothing." % (restated.group(1), len(census["with_c_symbol"])))
    header = _text(_SRMECH_H)
    missing = [s for s in census["symbols"] if s not in header]
    assert not missing, (
        "python/README.md says all %d are verified present in "
        "c/include/srmech.h; %d declared symbol(s) do not appear there: %r. "
        "The claim is checked by resolving the symbols, not by trusting the "
        "sentence." % (len(census["with_c_symbol"]), len(missing), missing))

    m = _search_undated(_DELEGATE_CENSUS, text)
    assert m, ("no undated 'N of the remaining M are `cyclic_mod_*` wrappers' "
               "cardinal found in python/README.md — it was rephrased and this "
               "gate has stopped observing.")
    assert (int(m.group(1)), int(m.group(2))) == (
        len(census["cyclic_delegates"]), len(census["remainder"])), (
        "python/README.md says %s of the remaining %s are cyclic_mod_* "
        "wrappers; the descriptors give %d of %d. Remainder: %r. Delegating: "
        "%r."
        % (m.group(1), m.group(2), len(census["cyclic_delegates"]),
           len(census["remainder"]), census["remainder"],
           census["cyclic_delegates"]))


def test_the_gate_would_have_fired_on_the_rc450_text() -> None:
    """RETRO-CHECK. A gate that would not have caught the defect that motivated
    it is not the gate. The rc450 strings are reproduced VERBATIM and run
    through the SHIPPED regexes, so loosening either predicate fails here.
    """
    rc450_ops = ("The shared dispatch table `CR_OP_REG` holds **20 op "
                 "spellings** at v0.9.0rc450 across Classes N / I / K / C")
    rc450_chains = ("a bare-C host runs **9 of the 18** chains from their "
                    "descriptors today, measured by execution.")
    m = _OP_SPELLINGS.search(rc450_ops)
    assert m and int(m.group(1)) == 20
    assert int(m.group(1)) != _cr_op_reg_size(), (
        "the rc450 op-spelling figure (20) equals the live count, so this "
        "retro-check is vacuous — the defect it replays no longer exists as "
        "stated and the carve-out needs re-basing, not deleting")
    m = _CHAINS_RUN.search(rc450_chains)
    assert m and (int(m.group(1)), int(m.group(2))) == (9, 18)
    running, executable = _chains_running_in_c()
    assert (int(m.group(1)), int(m.group(2))) != (running, executable), (
        "the rc450 running-chain figure (9 of 18) equals the live derivation, "
        "so this retro-check is vacuous")


def test_the_gate_would_have_fired_on_the_rc453_text() -> None:
    """RETRO-CHECK for the rc454 assertions, same discipline as the rc450 one.

    The two rc453 strings are reproduced VERBATIM and run through the SHIPPED
    predicates, so loosening either one fails here. Each carries the vacuity
    escape: if the replayed defect now equals the live value, RE-BASE the
    retro-check rather than deleting it — a retro-check that cannot distinguish
    the defect from the fix has stopped being evidence.
    """
    live = _live_cascade_catalog()

    rc453_worked = ("# {'total': 21, 'executable': 18, 'leaf': 3,\n"
                    "#  'status': {'magnitude': 'executable', "
                    "'reorient': 'leaf', ...},\n"
                    "#  'run': 'srmech.dsl.run_cascade_chain',\n"
                    "#  'enumerate': 'srmech.dsl.list_catalog_ops'}")
    printed = _comment_block_keys(
        " ".join(ln.lstrip().lstrip("#").strip()
                 for ln in rc453_worked.splitlines()))
    assert printed == {"total", "executable", "leaf", "status", "run",
                       "enumerate"}, (
        "the worked-block key parser stopped seeing the rc453 transcript's six "
        "keys; it parsed %r" % sorted(printed))
    assert printed != set(live), (
        "the rc453 six-key block now equals the live key set, so this "
        "retro-check demonstrates nothing — re-base it, do not delete it.")

    rc453_denial = ("**⚠️ One projection today — a declarative "
                    "oracle whose executable projection is Python, with the C "
                    "coverage enumerated rather than assumed.**")
    hits = [p for p in _ONE_PROJECTION_DENIALS if p in rc453_denial.lower()]
    assert len(hits) == 2, (
        "the one-projection denial predicate no longer matches the rc453 "
        "sentence it was written for; it caught %r" % hits)
    assert live["c_runnable"] == live["executable"], (
        "c_runnable no longer equals executable, so the denial ban above is "
        "correctly inert — re-base this retro-check to say so rather than "
        "asserting an equality the tree no longer has.")
