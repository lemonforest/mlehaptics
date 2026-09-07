"""rc469 — the ledger WRITE-REFUSALS gate (`#T1188`).

WHY THIS FILE EXISTS
====================
rc469 removed this tool's stale-selector flag (the CHANGELOG entry for that rc
names it; nothing live does any more, so a grep hit outside a dated record is a
defect rather than a mention). It keyed on the SNIPPET-TEXT hash and was
therefore structurally blind to an implementation change.

Removing it was half the job. The other half was two refusals in
:func:`run_worked_examples.main`, which close the path the flag had left open:

* a selector that matches NOTHING must not fall through to ``write_ledger``,
  because that mints a fresh meta stamping ``verified_at = HEAD`` having
  executed nothing — and ``backfill()`` computes its moved set from
  ``meta.verified_at..HEAD``, so an empty pass moves the base a later
  ``--backfill`` trusts and launders every implementation-stale row into a
  clean stamp;
* an ``--only`` name that is not in the live registry must not be a silent
  empty pass, for the same reason.

Those two refusals ARE the item that closes the laundering path. They shipped
in rc469 with no coverage at all: deleting either one left every ledger gate in
the tree green. A fix nothing can see is a fix that erodes — this file is the
detector.

WHAT MAKES IT A MEASUREMENT AND NOT AN ASSERTION
================================================
Standing discipline in this tree: an instrument that cannot return otherwise is
not a measurement. Two arms here assert a REFUSAL — and a refusal test passes
trivially if the tool is broken, absent, or refuses everything. So a third arm
is a POSITIVE CONTROL: the same harness, the same monkeypatched ledger, a
selector naming a live op, must return 0 and must WRITE. If the control ever
stops writing, the two refusal arms stop meaning anything, and this file says
so out loud rather than staying green.

A fourth arm pins the control name against the committed ledger, so the control
cannot quietly become vacuous by naming an op that no longer exists. That is
the same failure rc469 found in the demotion census, where a witness at ``n=2``
multiplied the axis by exact zero and three rows read INSENSITIVE over a live
silent-wrong-answer.

MUTATION-TESTED, NOT ASSUMED
============================
Replacing the empty-selection ``return 2`` with a fallthrough takes
:func:`test_an_empty_selector_refuses_and_does_not_restamp` red with
``assert 0 == 2`` — the mutant WROTE where the shipped code refuses. Note for
anyone repeating it: shadowing the tool via ``PYTHONPATH`` does NOT work,
because :func:`_tool` does ``sys.path.insert(0, ...)`` and wins. A mutation
test that cannot load its mutant is itself the instrument that cannot return
otherwise.

THE LEDGER IS NEVER TOUCHED
===========================
Every arm monkeypatches ``run_worked_examples.LEDGER`` onto a tmp_path COPY.
The committed artifact is read once, for bytes, and never written.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PY_ROOT = Path(__file__).resolve().parents[1]
LEDGER = PY_ROOT / "tests" / "worked_examples_result.ndjson"

#: A live op, pinned by :func:`test_the_positive_control_name_is_still_live`
#: below so it cannot rot into a vacuous control.
POSITIVE_CONTROL_NAME = "srmech.cascade.as_quat4"


def _tool():
    sys.path.insert(0, str(PY_ROOT / "tools"))
    import run_worked_examples as rwe

    return rwe


def _meta_of(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("record") == "meta":
            return rec
    return None


def _names_in(path: Path):
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("record") != "meta" and rec.get("name"):
            out.add(rec["name"])
    return out


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    rwe = _tool()
    copy = tmp_path / "worked_examples_result.ndjson"
    copy.write_bytes(LEDGER.read_bytes())
    monkeypatch.setattr(rwe, "LEDGER", copy)
    return rwe, copy


def _main(rwe, argv, monkeypatch) -> int:
    monkeypatch.setattr(sys, "argv", ["run_worked_examples.py", *argv])
    return rwe.main()


def test_an_empty_selector_refuses_and_does_not_restamp(
    sandbox, tmp_path, monkeypatch, capsys
):
    rwe, copy = sandbox
    before = copy.read_bytes()
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")

    rc = _main(rwe, ["--names-file", str(empty)], monkeypatch)
    err = capsys.readouterr().err

    assert rc == 2, "an empty selector must REFUSE, not write"
    assert copy.read_bytes() == before, (
        "the ledger was rewritten by a run that executed nothing — this is the "
        "laundering path rc469 closed"
    )
    assert "matched NO snippet" in err, err
    assert "verified_at" in err, (
        "the refusal must say WHY it refuses; the reason is the base that "
        "--backfill trusts"
    )


def test_an_unknown_name_refuses_and_does_not_restamp(
    sandbox, monkeypatch, capsys
):
    rwe, copy = sandbox
    before = copy.read_bytes()

    rc = _main(rwe, ["--only", "srmech.no.such.op.rc469"], monkeypatch)
    err = capsys.readouterr().err

    assert rc == 2, "an unknown --only name must REFUSE"
    assert copy.read_bytes() == before
    assert "not in the live " in err, err
    assert "SILENT EMPTY PASS" in err, err


def test_the_refusals_can_return_otherwise(sandbox, monkeypatch, capsys):
    """POSITIVE CONTROL. Without this the two refusal arms are vacuous."""
    rwe, copy = sandbox
    before_meta = _meta_of(copy)

    rc = _main(rwe, ["--only", POSITIVE_CONTROL_NAME], monkeypatch)
    err = capsys.readouterr().err

    assert rc == 0, (
        "the positive control did not run: the refusal arms above now prove "
        "nothing, because this harness cannot reach a write at all"
    )
    assert "wrote " in err, err
    after_meta = _meta_of(copy)
    assert after_meta is not None
    assert after_meta["n"] == before_meta["n"], (
        (before_meta or {}).get("n"), (after_meta or {}).get("n")
    )


def test_the_positive_control_name_is_still_live():
    """Stop the control rotting into a vacuous one."""
    names = _names_in(LEDGER)
    assert POSITIVE_CONTROL_NAME in names, (
        "%s is no longer in the committed ledger, so "
        "test_the_refusals_can_return_otherwise would refuse for the WRONG "
        "reason and still look green. Repoint it at a live op."
        % POSITIVE_CONTROL_NAME
    )
