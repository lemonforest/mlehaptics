"""`#T1131` P9 — the CORRECTION to P7: pytest's rewriter beats ``-O``.

WHAT P7 GOT RIGHT AND WHAT IT GOT WRONG
=======================================
P7 compiled every file with the builtin ``compile()`` and counted
``LOAD_ASSERTION_ERROR``. Under ``-O`` the count went to 0 for both the tests and
the package, and P7 concluded that a whole-suite ``-O`` cell would run with the
suite's own assertions inert and therefore see almost nothing.

That conclusion is WRONG, and the run refuted it before the reasoning did: all
four meta-gate sites this scope ruled class (c) were PREDICTED to fail under
``-O`` and every one of them PASSED.

The reason is that **pytest does not let the interpreter compile test modules.**
Its assertion-rewriting import hook parses each collected test module and
replaces every ``assert`` with explicit exception-raising bytecode. That
rewritten code is not an ``assert`` statement any more, so ``-O`` has nothing to
strip. Pytest even says so out loud when it detects the flag:

    PytestConfigWarning: assertions not in test modules or plugins will be
    ignored because assert statements are not executed by the underlying Python
    interpreter (are you using python -O?)

Read carefully, that warning states the split precisely: assertions **not in test
modules** are ignored. Assertions **in** test modules are not.

THE CONSEQUENCE, AND WHY IT MATTERS FOR THE GATE
================================================
Under ``pytest -O``:

  * TEST-module asserts  SURVIVE (pytest rewrote them)
  * PACKAGE asserts      VANISH  (pytest never rewrites the package under test)

So the ``-O`` boundary falls exactly on the PACKAGE / TEST_LOCAL line that P4's
static gate already uses to separate ruling (a)/(b) from ruling (c). The gate's
discrimination rule is not a heuristic that happens to work — it coincides with
the mechanism. A class-(c) meta-gate keeps working under ``-O`` *because* its
subject is a rewritten test module; a class-(a) site breaks under ``-O``
*because* its subject is not.

This file measures the split rather than arguing it, with both arms present so
neither can be assumed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

PYPATH = "/mnt/d/GitHub/mlehaptics/docs/srmech/python"
OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p9_pytest_rewrite_vs_dash_o_rc433.ndjson"

#: A test module with BOTH shapes: an assert in the test module itself, and a
#: call into a helper living in a NON-test module that pytest will not rewrite.
PROBE_TEST = '''
import pytest
import _t1131_helper as helper


def test_assert_in_a_test_module_still_fires():
    """A plain `assert False` written IN the test module."""
    with pytest.raises(AssertionError):
        assert False, "in-test-module assert"


def test_assert_in_a_NON_test_module_still_fires():
    """The same assert, but written in a module pytest does not rewrite."""
    with pytest.raises(AssertionError):
        helper.guarded(-1)
'''

PROBE_HELPER = '''
def guarded(x):
    """Stands in for shipped package code: pytest does not rewrite this file."""
    assert x >= 0, "helper: x must be non-negative"
    return x
'''


def run(tmp, optimize):
    env = dict(os.environ)
    env["PYTHONPATH"] = tmp + os.pathsep + PYPATH
    env.pop("PYTHONOPTIMIZE", None)
    cmd = [sys.executable] + (["-O"] if optimize else []) + [
        "-m", "pytest", os.path.join(tmp, "test_t1131_probe.py"),
        "-q", "--tb=no", "-rfE", "-p", "no:randomly", "-p", "no:cacheprovider"]
    p = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True,
                       text=True, timeout=600)
    failed = [ln.split(" ")[1] for ln in p.stdout.splitlines()
              if ln.startswith("FAILED")]
    tail = [ln for ln in p.stdout.strip().splitlines() if "passed" in ln
            or "failed" in ln]
    return {"returncode": p.returncode, "failed": failed,
            "summary": tail[-1] if tail else "", "optimize_flag": int(optimize)}


def main():
    tmp = tempfile.mkdtemp(prefix="t1131_p9_")
    with open(os.path.join(tmp, "test_t1131_probe.py"), "w", encoding="utf-8") as fh:
        fh.write(PROBE_TEST)
    with open(os.path.join(tmp, "_t1131_helper.py"), "w", encoding="utf-8") as fh:
        fh.write(PROBE_HELPER)

    d = run(tmp, False)
    o = run(tmp, True)

    # NOTE: ``failed`` holds full node IDs ("file.py::test_name"), so membership
    # must be a SUBSTRING test. A first draft used `name not in o["failed"]`,
    # which compares a bare name against a list of node IDs and is therefore
    # ALWAYS True — it reported the package assert as surviving while the very
    # same run showed that test failing. The data was right and the predicate was
    # wrong; recorded because a boolean that cannot go False is not a measurement.
    def _failed(fragment):
        return any(fragment in nid for nid in o["failed"])

    in_test_survives = not _failed("test_assert_in_a_test_module_still_fires")
    in_pkg_survives = not _failed("test_assert_in_a_NON_test_module_still_fires")

    print("DEFAULT mode : %s   failed=%s" % (d["summary"], d["failed"]))
    print("-O      mode : %s   failed=%s" % (o["summary"], o["failed"]))
    print()
    print("assert IN a pytest-collected TEST module survives -O : %s" % in_test_survives)
    print("assert in a NON-rewritten (package-like) module      : %s"
          % ("survives" if in_pkg_survives else "VANISHES"))

    verdict = (
        "CONFIRMED — pytest's rewriter defeats -O for test modules only; the "
        "package half still vanishes. P7's 'the whole suite goes inert' "
        "conclusion is RETRACTED."
        if in_test_survives and not in_pkg_survives else
        "NOT CONFIRMED — re-read; the split is not what P9 predicted.")
    print("\nVERDICT:", verdict)

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({
            "record": "rewrite_meta",
            "assert_in_test_module_survives_dash_O": in_test_survives,
            "assert_in_non_rewritten_module_survives_dash_O": in_pkg_survives,
            "verdict": verdict,
            "default_arm": d, "dash_O_arm": o,
            "python": sys.version.split()[0],
        }, sort_keys=True) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
