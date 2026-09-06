"""The ledger-freshness hook's own fixtures must RUN, and must still be able
to FAIL. (rc468, `#T1188`)

WHY THIS FILE EXISTS
====================
``tools/hooks/check_hooks.py`` is the only instrument that drives the shipped
hooks against planted repositories, and until now it ran **only when a human
typed it**. Nothing in CI executed it, so its cases could rot, be deleted, or
quietly stop asserting, and every board would stay green. A hook self-check
nobody runs is documentation.

⚠️ IT PRINTS TO **stderr**, NOT stdout.
``check_hooks.py`` writes every ``[PASS]`` / ``[FAIL]`` line and its summary
through ``print(..., file=sys.stderr)``. An assertion written against
``proc.stdout`` — which is what both rc468 plans specified — would be
vacuously true on an EMPTY string and would keep passing after the cases were
deleted. That is the precise shape of "an instrument that cannot return
otherwise", inside a test written to prevent it.

WHAT IT PINS
============
1. The ledger subset exits 0 (every case passes).
2. The three cases rc468 added are NAMED in the output. A count would not do:
   the point is that these particular plants are still driven, and a count can
   be held constant while a case is swapped for a weaker one.
3. Non-vacuity: the summary line is present and reports a nonzero case count.

SCOPE: the ``ledger`` subset only. ``check_hooks.py ratchet`` and ``jpl`` write
fixture files into the REAL tree (``docs/srmech/c/src/_hook_fixture_rc452.c``
and friends) and remove them in a ``finally``; a pytest worker that is killed
mid-case would leave them behind. The ledger subset builds every fixture inside
``tempfile.TemporaryDirectory`` and touches nothing tracked, so it is the one
subset that is safe to run unattended.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PY_ROOT = Path(__file__).resolve().parents[1]
CHECKER = PY_ROOT / "tools" / "hooks" / "check_hooks.py"

#: the plants rc468 added, by the exact substring each case name carries.
#: Each one FAILED against the rc467 hook and passes against rc468's — measured
#: by restoring the old hook beside these fixtures: 7 passed, 2 failed.
REQUIRED_CASES = (
    "the rc468 blind spot",          # re-exported row, defining module changed
    "the union's other half",        # package __init__ still claims its rows
    "PARTIAL re-run",                # both rows present, one stamp stale
)


@pytest.mark.skipif(shutil.which("git") is None,
                    reason="the hook fixtures build throwaway git repos")
def test_ledger_freshness_hook_fixtures_all_pass() -> None:
    assert CHECKER.is_file(), f"{CHECKER} is missing"
    proc = subprocess.run([sys.executable, str(CHECKER), "ledger"],
                          cwd=str(PY_ROOT), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=900)
    err = proc.stderr.decode("utf-8", "replace")

    assert proc.returncode == 0, (
        "check_hooks.py ledger reported a FAILING case:\n"
        + "\n".join(l for l in err.splitlines() if "[FAIL]" in l or "passed," in l))

    # NON-VACUITY. Without this the two assertions below could both be true of
    # an empty run that skipped everything.
    summary = [l for l in err.splitlines() if "passed," in l]
    assert summary, ("check_hooks.py printed no summary line — it did not run. "
                     f"stderr was {err[:400]!r}")
    assert " 0 passed," not in summary[-1], (
        f"the ledger subset ran ZERO cases: {summary[-1]!r}")
    assert "[FAIL]" not in err

    missing = [c for c in REQUIRED_CASES if c not in err]
    assert not missing, (
        "the ledger self-check no longer drives the rc468 plants: "
        f"{missing}. Those three cases are the only ones that distinguish a "
        "hook that resolves a row to its DEFINING module from one that matches "
        "its published name. Deleting or renaming one takes the guard with it.\n"
        + err[-2000:])
