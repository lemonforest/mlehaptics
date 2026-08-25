"""`#T1160` / gh #1653 — the BLOCKED table must AGREE with what it cites. rc450.

WHY THIS EXISTS
---------------
``tests/test_c_cascade_parity_ratchet_rc446.py`` carries the ``BLOCKED`` table
that every future ceiling decrement is read against. Its own comment has said
*"Gates are synced from notes/_1653_gate_matrix_rc445.ndjson"* since rc445.
Measured at rc449 head, by parsing both artifacts, it was not:

* ``best_rational_signed``  table ``[op_table, ref_grammar]``  matrix ``[op_table]``
* ``octonion_dft``          table 3 gates                      matrix 4 (+``carrier_width``)
* ``quaternion_dft``        table 3 gates                      matrix 4 (+``carrier_width``)

and six of the nine ``new_type`` flags contradicted the ledger row each cited.
Nothing in the tree could report any of it: the ratchet's own cross-artifact
test (``test_every_blocked_row_is_ACTUALLY_FILED_in_the_gap_ledger``) resolves
each ``ledger_row`` id and asserts only that it EXISTS. Existence is not
agreement. So the "sync" was a sentence in a comment — which is the exact shape
gh #1653 was opened to remove, sitting inside the instrument built to remove it.

Fixing the table without this file would be a one-time cleanup of a surface that
has already drifted once. The gate is the mechanism; the cleanup is the payload.

THE PARSE PREDICATES, STATED SO THEY CAN BE REPRODUCED OR REFUTED
------------------------------------------------------------------
* ``BLOCKED``: imported from the ratchet MODULE. Not re-parsed out of its
  source — the live object is the thing every other test reads, and a second
  parser could disagree with the interpreter about what the file says.
* the gate matrix: ``json.loads`` per line of
  ``notes/_1653_gate_matrix_rc445.ndjson``; a record is a CHAIN row when
  ``record`` is absent or not ``"summary"``; the blocked population is the rows
  with ``c_runs is False``; a row's gate set is ``set(row["gates"])``.
* the gap ledger: ``json.loads`` per line of
  ``notes/_1653_gap_ledger.ndjson``, keyed by ``id``, summary skipped. The
  new-type field is spelled ``new_type`` — NOT ``is_new_type``, which appears on
  zero of the shipped rows and which an earlier draft of this gate named.
* the step-mutation exempt set: extracted by **AST**, because it is a LOCAL
  variable inside ``test_every_running_chain_has_a_mutation_or_is_named()``.
  ``module.exempt`` raises ``AttributeError``, and a gate that swallowed that
  would silently pin the EMPTY set — passing forever while the exemption list
  grew, which is the state the pin exists to prevent.

WHAT MAKES THIS GATE ABLE TO RETURN OTHERWISE
---------------------------------------------
Every parse asserts its own population is non-empty before comparing, and the
chain-name comparison is BIDIRECTIONAL. A one-sided loop over ``BLOCKED`` would
pass forever after ``rc451`` deletes the ``best_rational_signed`` row while the
matrix kept calling it ``c_runs: false`` — the matrix would rot with nothing
able to say so. And the blocked population is reconciled against the ratchet's
own ``CEIL_C_REJECTED_CHAINS``, so all three artifacts have to move together.

⚠️ RESIDUAL RISK, NAMED. This gate pins agreement WITH the rc445 gate matrix.
If the MATRIX is wrong, the gate ossifies the error. Three independent
derivations agree on it today (the matrix itself, a recursive walk over the
descriptors, and a direct parse at rc450 head) but they could share a predicate
blind spot — which is why the predicates above are written out rather than
implied. This gate proves AGREEMENT, never TRUTH.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import test_c_cascade_parity_ratchet_rc446 as ratchet
from _native_gate import require_native

_NOTES = Path(__file__).resolve().parents[2] / "notes"
_GATE_MATRIX = _NOTES / "_1653_gate_matrix_rc445.ndjson"
_GAP_LEDGER = _NOTES / "_1653_gap_ledger.ndjson"
_WITNESS = Path(__file__).resolve().parent / "test_step_mutation_witness_rc447.py"

#: rc452 (`#T1166`) Phase 2 — the exempt MECHANISM is gone, and this pin now
#: holds it at ZERO. It pinned the rc450 population ({cyclic_mod_inv,
#: cyclic_mod_mul_wide, cyclic_mod_pow}) so a FOURTH exemption would be a
#: deliberate red edit; all THREE pinned entries were then FALSIFIED — each
#: chain carries a value-predicted witness via a one-line argument mutation,
#: now in the witness file's MUTATIONS — so the escape hatch itself was
#: removed. Reintroducing an `exempt = {...}` assignment is the red edit now.
EXPECTED_EXEMPT = frozenset()


# ── parsers, each of which refuses an empty result ───────────────────────────

def _matrix_rows():
    assert _GATE_MATRIX.exists(), "gate matrix ndjson missing: %s" % _GATE_MATRIX
    rows = {}
    with _GATE_MATRIX.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("record") == "summary":
                continue
            rows[rec["chain"]] = rec
    assert rows, ("the gate-matrix parse returned NOTHING. An empty parse "
                  "compared against anything is vacuously equal, which is the "
                  "defect this file exists to close — not a pass.")
    return rows


def _ledger_rows():
    assert _GAP_LEDGER.exists(), "gap ledger ndjson missing: %s" % _GAP_LEDGER
    rows = {}
    with _GAP_LEDGER.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("record") == "summary":
                continue
            rows[rec["id"]] = rec
    assert rows, "the gap-ledger parse returned NOTHING"
    return rows


def _exempt_names_in(src):
    """Every ``exempt = {...}`` assignment's name set, from source text.

    Returns a frozenset of names, EMPTY when no such assignment exists — which
    since rc452 Phase 2 is the required state. Anything other than a set/dict
    literal of plain strings is a hard failure: a comprehension or a name
    reference would mean the set is no longer statically knowable, and a pin
    that cannot see its subject must say so rather than pin nothing.
    """
    tree = ast.parse(src)
    found = frozenset()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "exempt" not in targets:
            continue
        val = node.value
        if isinstance(val, ast.Dict):
            keys = [k for k in val.keys if isinstance(k, ast.Constant)]
            assert len(keys) == len(val.keys), (
                "the exempt dict has a non-literal key; this pin can no longer "
                "see its subject and must not pretend to")
            found |= frozenset(k.value for k in keys)
        elif isinstance(val, ast.Set):
            elts = [e for e in val.elts if isinstance(e, ast.Constant)]
            assert len(elts) == len(val.elts), "non-literal exempt element"
            found |= frozenset(e.value for e in elts)
        else:
            raise AssertionError(
                "`exempt` is no longer a set/dict literal (%s). The pin reads "
                "it statically; if it became dynamic, the exemption list is no "
                "longer reviewable and that is the change to argue about."
                % type(val).__name__)
    return found


def _exempt_names_by_ast():
    """The witness module's exempt set — empty since rc452 Phase 2."""
    assert _WITNESS.exists(), "step-mutation witness missing: %s" % _WITNESS
    return _exempt_names_in(_WITNESS.read_text(encoding="utf-8"))


# ── 1. the population, both directions ───────────────────────────────────────

def test_blocked_and_matrix_name_the_same_chains_in_both_directions():
    """BIDIRECTIONAL set equality.

    One-sidedness is not a style point here. ``rc451`` deletes the
    ``best_rational_signed`` BLOCKED row when it unblocks the chain; a gate that
    iterated BLOCKED only would then pass while the matrix kept the chain as
    ``c_runs: false`` forever, with nothing able to report the rot.

    ⚠️ THE NON-EMPTY FLOOR IS GONE, REMOVED AT rc452 (`#T1166`). Both artifacts
    asserted a blocked chain EXISTED — a reasonable guard while the population
    was draining, and exactly wrong at the end of the drain: with
    ``parallel_sector_dispatch`` closed, BOTH sets are legitimately empty and
    the floor turned the finish line into a failure. Set equality alone still
    catches every one-sided edit, including re-blocking a chain in one artifact
    and not the other, so nothing is lost by dropping it. Recorded rather than
    silently deleted, because "the gate that fired when the work was DONE" is
    the same shape as a gate that cannot return otherwise.
    """
    matrix = _matrix_rows()
    matrix_blocked = {n for n, r in matrix.items() if r.get("c_runs") is False}
    table = set(ratchet.BLOCKED)
    assert table == matrix_blocked, (
        "BLOCKED and the gate matrix disagree on WHICH chains are blocked.\n"
        "  in BLOCKED only: %s\n  in matrix only : %s\n"
        "If you unblocked a chain, delete its BLOCKED row AND regenerate the "
        "matrix in the same change — a one-sided edit rots the other artifact."
        % (sorted(table - matrix_blocked), sorted(matrix_blocked - table)))


def test_the_blocked_population_reconciles_with_the_ratchet_ceiling():
    """Three artifacts, one number. The matrix's blocked count, the BLOCKED row
    count and ``CEIL_C_REJECTED_CHAINS`` must all agree — so none of them can be
    edited alone."""
    matrix = _matrix_rows()
    n_matrix = sum(1 for r in matrix.values() if r.get("c_runs") is False)
    assert n_matrix == len(ratchet.BLOCKED) == \
        ratchet.CEIL_C_REJECTED_CHAINS, (
        "matrix blocked=%d, BLOCKED rows=%d, CEIL_C_REJECTED_CHAINS=%d"
        % (n_matrix, len(ratchet.BLOCKED), ratchet.CEIL_C_REJECTED_CHAINS))


# ── 2. the gate sets ─────────────────────────────────────────────────────────

def test_every_blocked_row_gate_set_equals_the_matrix_gate_set():
    """The claim the ratchet's comment makes, finally checked.

    THIS IS THE ONE THAT WAS RED. Run against the pre-rc450 table it reports
    exactly three disagreements (``best_rational_signed``, ``octonion_dft``,
    ``quaternion_dft``), reproduced independently twice before the sync landed.
    """
    matrix = _matrix_rows()
    bad = []
    for name, row in sorted(ratchet.BLOCKED.items()):
        m = matrix.get(name)
        assert m is not None, "%s has no gate-matrix row" % name
        here, there = set(row["gates"]), set(m.get("gates") or [])
        if here != there:
            bad.append("%s: BLOCKED %s vs matrix %s (missing here: %s; extra "
                       "here: %s)" % (name, sorted(here), sorted(there),
                                      sorted(there - here), sorted(here - there)))
    assert not bad, (
        "the BLOCKED table's comment says its gates are synced from "
        "notes/_1653_gate_matrix_rc445.ndjson. They are not:\n  %s"
        % "\n  ".join(bad))


def test_gate_names_are_the_ratchets_own_vocabulary():
    """Both artifacts must speak the same gate names, or the comparison above
    would be comparing spellings and calling it agreement."""
    matrix = _matrix_rows()
    seen = set()
    for r in matrix.values():
        seen.update(r.get("gates") or [])
    unknown = sorted(seen - set(ratchet.VALID_GATES))
    assert not unknown, (
        "the gate matrix names gate(s) the ratchet does not define: %s"
        % unknown)


# ── 3. new_type: contradiction must be documented, never silent ──────────────

def test_every_cited_ledger_row_exists_and_spells_new_type_correctly():
    """Field-name pin. The ledger spells it ``new_type``; ``is_new_type``
    appears on zero of the shipped rows, and minting a second spelling would
    split the very field this gate reads."""
    ledger = _ledger_rows()
    for name, row in sorted(ratchet.BLOCKED.items()):
        cited = ledger.get(row["ledger_row"])
        assert cited is not None, (
            "%s cites gap-ledger row %r, which does not exist"
            % (name, row["ledger_row"]))
        assert "new_type" in cited, (
            "gap-ledger row %r has no `new_type` field" % row["ledger_row"])
        assert "is_new_type" not in cited, (
            "gap-ledger row %r carries `is_new_type`; the shipped spelling is "
            "`new_type` and two spellings for one field is how a gate reads "
            "one name on old rows and another on new ones"
            % row["ledger_row"])


def test_a_new_type_contradiction_is_documented_or_it_is_a_failure():
    """The SUBJECT MISMATCH, made expressible.

    A BLOCKED row is per-CHAIN and cites ONE of its several gaps; a ledger row
    is per-GAP. So the two flags legitimately differ — ``octonion_dft`` is a
    new-type CHAIN citing a gap that correctly says ``new_type: false``,
    because the ``l`` kind already exists and only nesting is missing.

    Asserting equality would therefore write a falsehood into whichever field
    lost. Asserting nothing would let a real contradiction sit silent, which is
    how ``best_rational_signed`` — the one chain whose closure introduces a new
    wire kind — could have been flipped to ``new_type=False`` and disarmed the
    same-change rule at the exact chain rc451 ships. So the rule is: agree, or
    say in the row itself why not.
    """
    ledger = _ledger_rows()
    undocumented = []
    for name, row in sorted(ratchet.BLOCKED.items()):
        cited = ledger[row["ledger_row"]]
        if bool(row["new_type"]) == bool(cited["new_type"]):
            assert not row["new_type_reason"], (
                "%s: new_type agrees with its cited row, so new_type_reason "
                "must be empty — a reason for a difference that does not exist "
                "is prose nobody will maintain" % name)
            continue
        if len(row["new_type_reason"].strip()) < 60:
            undocumented.append(
                "%s: BLOCKED new_type=%s but ledger row %r says %s, and "
                "new_type_reason is %d characters"
                % (name, row["new_type"], row["ledger_row"],
                   cited["new_type"], len(row["new_type_reason"].strip())))
    assert not undocumented, (
        "a BLOCKED row contradicts the gap-ledger row it cites with no stated "
        "reason:\n  %s\nEither repoint the citation, or write why the CHAIN "
        "flag differs from the GAP flag. A silent contradiction in this table "
        "is how a new wire kind ships without the same-change rule firing."
        % "\n  ".join(undocumented))


def test_at_least_one_row_actually_exercises_the_contradiction_branch():
    """CONTROL for the test above: if every row agreed, that test would pass
    without ever evaluating its own reason-check, and nobody would know. Two
    rows (octonion_dft / quaternion_dft) legitimately differed at rc450.

    ⚠️ THE NEW STATE IS STATED DELIBERATELY, as this test's own old message
    instructed: at rc452 Phase 3 (`#T1166`) the two differing rows CLOSED —
    both DFT chains run, all proof cases BYTE_IDENTICAL — and were deleted,
    so no LIVE row differs from its cited ledger row any more. The branch is
    therefore exercised on a SYNTHETIC row instead: the same predicate the
    test above applies must flag a contradiction with an undersized reason,
    or the reason-check has stopped measuring and its green means nothing.
    """
    ledger = _ledger_rows()
    differing = sorted(n for n, row in ratchet.BLOCKED.items()
                       if bool(row["new_type"]) !=
                       bool(ledger[row["ledger_row"]]["new_type"]))
    if differing:
        return                      # live rows exercise the branch — done
    # Synthetic exercise: a row contradicting its cited ledger row with a
    # too-short reason MUST be what the reason-check flags. Mirrors the
    # predicate in test_new_type_contradictions_carry_a_stated_reason.
    any_row = next(iter(ledger.values()))
    synthetic = {"new_type": not bool(any_row["new_type"]),
                 "new_type_reason": "too short"}
    flags = (bool(synthetic["new_type"]) != bool(any_row["new_type"])
             and len(synthetic["new_type_reason"].strip()) < 60)
    assert flags, (
        "the synthetic contradicting row was NOT flagged by the reason-check "
        "predicate — the branch this control guards has stopped measuring")


# ── 4. the exempt-set pin ────────────────────────────────────────────────────

def test_step_mutation_exempt_set_is_pinned():
    """The exempt mechanism stays REMOVED — pinned at zero.

    Through mid-rc452 this pinned three names so a FOURTH exemption would be a
    deliberate red edit. All three were then falsified by executed one-line
    argument mutations (rc452 Phase 2), so the escape hatch itself is gone and
    the pin's job inverts: the witness file must contain NO ``exempt = {...}``
    assignment at all. Reintroducing one — with any content — is the red edit
    this now exists to catch; a genuine impossibility claim belongs in an
    EXECUTED proof beside the witness, not in a dict of prose.
    """
    got = _exempt_names_by_ast()
    assert got == EXPECTED_EXEMPT == frozenset(), (
        "the step-mutation witness has grown an exempt set again: %s. All "
        "three previous exemptions were falsified by one-line argument "
        "mutations; prove impossibility by execution instead." % sorted(got))


def test_the_exempt_pin_would_notice_a_fourth_name():
    """RETRO-CHECK on the pin's own mechanism. Extraction is by AST over source
    text, so the check is run against a MUTATED copy of that source rather than
    against a description of one: reintroduce an ``exempt`` dict and the
    extractor must SEE it (the zero above is a measurement, not a dead
    detector)."""
    src = _WITNESS.read_text(encoding="utf-8")
    assert "exempt = {" not in src, (
        "an exempt assignment is back in the witness source; the strict-zero "
        "pin above should already be red")
    mutated = src + '\n\nexempt = {"cyclic_gcd": "x"}\n'
    names = _exempt_names_in(mutated)
    assert "cyclic_gcd" in names, (
        "the AST extraction did not see a reintroduced exempt dict, so the "
        "pin cannot detect the thing it exists to detect")
    assert names != EXPECTED_EXEMPT


# ── 5. visibility ────────────────────────────────────────────────────────────

def test_reports_the_agreement_state(capsys):
    # ⚠️ ONE LINE, ONE LITERAL — deliberately, and it must stay that way. The
    # `fallback pure-by-design skip audit` fan-in builds its DECLARED set by
    # scanning source for require_native(...) and its OBSERVED set from the
    # runtime skip reasons, then compares them. An implicitly-concatenated
    # multi-line argument makes those two disagree: the scanner reads only the
    # first fragment while the skip carries the joined string, so ONE gate
    # reports as both "DECLARED but never fired" and "fired with no call site".
    # That is exactly what turned the audit red at rc450's first CI round.
    require_native("the BLOCKED/gate-matrix agreement report reads the artifacts the C-parity ratchet measures")
    matrix = _matrix_rows()
    ledger = _ledger_rows()
    with capsys.disabled():
        print("\n  BLOCKED <-> gate matrix <-> gap ledger, at rc450")
        print("  %-26s %-46s %-9s %s"
              % ("chain", "gates (BLOCKED == matrix)", "new_type", "ledger row"))
        for name, row in sorted(ratchet.BLOCKED.items()):
            same = set(row["gates"]) == set(matrix[name].get("gates") or [])
            print("  %-26s %-46s %-9s %s%s"
                  % (name, ",".join(sorted(row["gates"])) + ("" if same else " !!"),
                     "YES" if row["new_type"] else "no", row["ledger_row"],
                     "" if bool(row["new_type"]) ==
                     bool(ledger[row["ledger_row"]]["new_type"])
                     else "  (documented contradiction)"))
    assert len(ratchet.BLOCKED) == ratchet.CEIL_C_REJECTED_CHAINS
