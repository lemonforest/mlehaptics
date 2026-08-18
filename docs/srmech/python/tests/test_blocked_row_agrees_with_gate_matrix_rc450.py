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

#: The step-mutation witness's exempt set, pinned at its rc450 population. A
#: FOURTH exemption is then a deliberate red edit that must state its reason,
#: rather than a one-line escape from the mutation obligation.
EXPECTED_EXEMPT = frozenset({"cyclic_mod_inv", "cyclic_mod_mul_wide",
                             "cyclic_mod_pow"})


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


def _exempt_names_by_ast():
    """The exempt set, read out of the witness module's AST.

    It is a local ``exempt = {...}`` inside a test function, so there is no
    attribute to read. Anything other than a set literal of plain strings is a
    hard failure: a comprehension or a name reference would mean the set is no
    longer statically knowable, and a pin that cannot see its subject must say
    so rather than pin nothing.
    """
    assert _WITNESS.exists(), "step-mutation witness missing: %s" % _WITNESS
    tree = ast.parse(_WITNESS.read_text(encoding="utf-8"))
    found = None
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
            found = frozenset(k.value for k in keys)
        elif isinstance(val, ast.Set):
            elts = [e for e in val.elts if isinstance(e, ast.Constant)]
            assert len(elts) == len(val.elts), "non-literal exempt element"
            found = frozenset(e.value for e in elts)
        else:
            raise AssertionError(
                "`exempt` is no longer a set/dict literal (%s). The pin reads "
                "it statically; if it became dynamic, the exemption list is no "
                "longer reviewable and that is the change to argue about."
                % type(val).__name__)
        break
    assert found is not None, (
        "no `exempt = {...}` assignment found in %s — the extraction stopped "
        "matching, and an extraction that finds nothing must FAIL rather than "
        "pin the empty set" % _WITNESS.name)
    return found


# ── 1. the population, both directions ───────────────────────────────────────

def test_blocked_and_matrix_name_the_same_chains_in_both_directions():
    """BIDIRECTIONAL set equality, plus a non-empty floor.

    One-sidedness is not a style point here. ``rc451`` deletes the
    ``best_rational_signed`` BLOCKED row when it unblocks the chain; a gate that
    iterated BLOCKED only would then pass while the matrix kept the chain as
    ``c_runs: false`` forever, with nothing able to report the rot.
    """
    matrix = _matrix_rows()
    matrix_blocked = {n for n, r in matrix.items() if r.get("c_runs") is False}
    table = set(ratchet.BLOCKED)
    assert matrix_blocked, "no c_runs=false rows in the matrix"
    assert table, "BLOCKED is empty"
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
    rows (octonion_dft / quaternion_dft) legitimately differ at rc450."""
    ledger = _ledger_rows()
    differing = sorted(n for n, row in ratchet.BLOCKED.items()
                       if bool(row["new_type"]) !=
                       bool(ledger[row["ledger_row"]]["new_type"]))
    assert differing, (
        "no BLOCKED row differs from its cited ledger row, so the "
        "documented-contradiction branch above is never evaluated. If that is "
        "genuinely the new state, say so here deliberately — do not leave a "
        "branch that has stopped being exercised looking like it passes.")


# ── 4. the exempt-set pin ────────────────────────────────────────────────────

def test_step_mutation_exempt_set_is_pinned():
    """A FOURTH exemption must be a deliberate red edit.

    ``tests/test_step_mutation_witness_rc447.py`` requires every C-running chain
    to carry a mutation witness OR be named in a local ``exempt`` dict with a
    reason. That dict is a one-line escape hatch from the obligation, and rc451+
    is precisely when something will want to use it — so it is pinned before it
    is needed rather than after it is used.
    """
    got = _exempt_names_by_ast()
    assert got == EXPECTED_EXEMPT, (
        "the step-mutation exempt set is %s; the pin is %s. ADDING a name here "
        "means a chain that runs in C now has NO mutation witness — state the "
        "reason in the witness file and update this pin in the same change."
        % (sorted(got), sorted(EXPECTED_EXEMPT)))


def test_the_exempt_pin_would_notice_a_fourth_name():
    """RETRO-CHECK on the pin's own mechanism. Extraction is by AST over source
    text, so the check is run against a MUTATED copy of that source rather than
    against a description of one."""
    src = _WITNESS.read_text(encoding="utf-8")
    marker = "exempt = {"
    assert marker in src, "the exempt assignment spelling changed"
    mutated = src.replace(marker, 'exempt = {\n        "cyclic_gcd": "x",', 1)
    tree = ast.parse(mutated)
    names = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "exempt"
                for t in node.targets):
            names = frozenset(k.value for k in node.value.keys
                              if isinstance(k, ast.Constant))
            break
    assert names is not None and "cyclic_gcd" in names, (
        "the AST extraction did not see an added name, so the pin cannot "
        "detect the thing it exists to detect")
    assert names != EXPECTED_EXEMPT


# ── 5. visibility ────────────────────────────────────────────────────────────

def test_reports_the_agreement_state(capsys):
    require_native("the BLOCKED/gate-matrix agreement report reads the same "
                   "artifacts the C-parity ratchet measures")
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
