"""rc356 (`#T953`) — the C tests must actually RUN.

At rc355 this repo had 30 files under ``docs/srmech/c/test/``, nine of them
wired into ``docs/srmech/CMakeLists.txt``, and **zero of them executed by any
automation.** There was no ``enable_testing()``, no ``add_test()``, and no
``ctest`` step in any workflow; the ``pedantic-build`` job was Configure +
Build, so CI compiled nine binaries and threw them away. The ``make test``
target — which ``c/README.md`` documents as *the* local flow — looked for
``test/test_srmech.c``, a file that has never existed in this tree, printed
``(Phase B1: no test_srmech.c yet — skipping)`` and exited 0.

Both supposedly-independent enforcement paths were therefore compile-only or
no-op green, and that shape did what it always does. rc307 reinterpreted the
``ws_len`` unit on the three fiedler symbols from a COUNT OF DOUBLES to BYTES —
a breaking wire-contract change that bumped ``SRMECH_ABI_VERSION`` 9 -> 10 — and
migrated two of the three test callers. The third, ``test_srmech_progress_tick.c``,
kept passing the doubles count, so its call was declined by the arena guard
before the tick loop was ever entered and the §101 cancel channel it exists to
exercise went untested. It returned ``SRMECH_ERR_BAD_INPUT`` where it asserted
``SRMECH_CANCELLED`` for roughly 48 rcs. CI built it every single time.

ADR-0003 says the C host stands alone. That was not a claim automation could
check, for any of the 30 tests. This file is what keeps it checkable.

Nothing here compiles or runs C — it reads the wiring. The running is what
``ctest`` and ``make test`` now do; these assertions are about the wiring not
quietly reverting to the shape that hid a red test for 48 rcs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SRMECH_DIR = _HERE.parent.parent                 # tests/ -> python/ -> docs/srmech/
_C_TEST_DIR = _SRMECH_DIR / "c" / "test"
_CMAKE = _SRMECH_DIR / "CMakeLists.txt"
_MAKEFILE = _SRMECH_DIR / "c" / "Makefile"
_WORKFLOW = _SRMECH_DIR.parent.parent / ".github" / "workflows" / "srmech-ci.yml"

pytestmark = pytest.mark.skipif(
    not _C_TEST_DIR.exists(),
    reason="C tree absent (pure-Python checkout) — nothing to assert about its wiring",
)

#: Down-only CEIL: how many ``c/test/test_srmech_*.c`` are NOT registered with
#: ctest. rc356 took this from 30 to 20 by wiring the nine already in the
#: pedantic matrix plus ``test_srmech_genome`` (the test `#T953` was filed
#: against). The residual 20 are green under gcc on WSL2 — all 30 pass, 0
#: warnings, 551 ms for the whole set — but they have never been built by MSVC,
#: and this matrix compiles with ``/WX``. Wiring 20 unverifiable files at once
#: is how a wiring rc lands red, which is the one outcome worse than the gap it
#: closes: a permanently-red gate everyone learns to ignore. They come in in
#: batches, each verified on the 3-OS matrix as it lands.
#:
#: **This number may only go DOWN.** Raising it means a new C test was added
#: without wiring, which is exactly the state rc356 exists to end.
CEIL_UNWIRED_C_TESTS = 20


def _c_tests() -> list[str]:
    """Every C test's stem, e.g. ``test_srmech_genome``.

    ``cascade_explorer.c`` is excluded by the glob on purpose: it is a tool, not
    a test, and it has no pass/fail exit contract to register with ctest.
    """
    return sorted(p.stem for p in _C_TEST_DIR.glob("test_srmech_*.c"))


def _cmake_text() -> str:
    """CMakeLists with whole-line ``#`` comments removed.

    COMMENTS ARE EXEMPT, and this is not fussiness — the first draft of this file
    searched the raw text, and the red-team run that commented out
    ``enable_testing()`` PASSED, because the substring was still there inside the
    comment. A guard that a ``#`` disarms is prose. The same applies to
    ``add_executable`` / ``add_test``: a commented-out registration must not count
    as a registration.

    Whole-line only. Stripping trailing ``#`` would have to reason about quoting,
    and every call CMake actually executes is on a line of its own here.
    """
    return "\n".join(
        ln for ln in _CMAKE.read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("#")
    )


def _added_executables() -> set[str]:
    return set(re.findall(r"add_executable\(\s*(test_srmech_\w+)", _cmake_text()))


def _registered_tests() -> set[str]:
    """Stems reachable by ``ctest``.

    ``add_test`` is written here as a ``foreach`` over a name list, so the plain
    ``add_test(NAME x ...)`` pattern alone would report zero and this whole file
    would pass by seeing nothing. Read the loop body's variable back to its list.
    """
    text = _cmake_text()
    direct = set(re.findall(r"add_test\(\s*NAME\s+(test_srmech_\w+)", text))
    loop = re.search(
        r"foreach\(\s*t\b(.*?)\)\s*\n\s*add_test\(\s*NAME\s+\$\{t\}", text, re.S)
    if loop is not None:
        direct |= set(re.findall(r"(test_srmech_\w+)", loop.group(1)))
    return direct


def test_enable_testing_is_declared():
    """No ``enable_testing()`` means every ``add_test`` is inert and ``ctest``
    finds nothing to run — the exact silence rc356 replaced."""
    assert "enable_testing()" in _cmake_text(), (
        "docs/srmech/CMakeLists.txt has no enable_testing(); add_test() calls are "
        "inert without it and `ctest` reports 'No tests were found', which is a "
        "PASS to any workflow that does not read the message"
    )


def test_every_built_c_test_is_also_registered_with_ctest():
    """Compiling a test proves that it compiles.

    This is the rc355-shaped half of the finding: an ``add_executable`` with no
    matching ``add_test`` is a test binary CI produces and discards. That is how
    ``test_srmech_progress_tick`` stayed red for ~48 rcs.
    """
    built, registered = _added_executables(), _registered_tests()
    compile_only = sorted(built - registered)
    assert not compile_only, (
        f"{len(compile_only)} C test(s) are BUILT by CMake but never RUN: "
        f"{compile_only}. A built-and-discarded test binary is the compile-only "
        f"gate rc356 removed; register it with add_test()"
    )


def test_registered_tests_all_exist():
    """A stale ``add_test`` name makes ``ctest`` fail for a reason unrelated to
    the code, which trains people to ignore it."""
    missing = sorted(_registered_tests() - set(_c_tests()))
    assert not missing, (
        f"CMakeLists registers C test(s) with no source file: {missing}")


def test_unwired_c_tests_ratchet_down_only():
    """The residual, draining.

    ``make test`` runs all 30 on POSIX, so nothing here is unrun by every path —
    but the 3-OS ``/WX`` matrix is the projection ADR-0003 is really about, and
    this is the number that says how far from it we still are.
    """
    unwired = sorted(set(_c_tests()) - _registered_tests())
    assert len(unwired) <= CEIL_UNWIRED_C_TESTS, (
        f"{len(unwired)} C tests are not registered with ctest, ceiling is "
        f"{CEIL_UNWIRED_C_TESTS}: {unwired}. This ratchet is DOWN-ONLY — if you "
        f"added a C test, wire it in docs/srmech/CMakeLists.txt (add_executable + "
        f"the add_test foreach list) rather than raising the ceiling"
    )


def test_ci_actually_runs_the_c_tests():
    """The run step itself.

    All the wiring above is inert if no workflow invokes ``ctest``. rc355's
    lesson was that a guard nobody calls is prose; this asserts the caller.
    """
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "ctest" in text, (
        ".github/workflows/srmech-ci.yml invokes no `ctest`. Every add_test() in "
        "CMakeLists is then unreachable and the pedantic matrix is compile-only "
        "again — the rc355 state this rc exists to end"
    )
    ctest_lines = [ln for ln in text.splitlines() if "ctest" in ln and "#" not in ln]
    assert ctest_lines, "the only `ctest` mentions in srmech-ci.yml are comments"
    for ln in ctest_lines:
        assert "|| true" not in ln, (
            f"the ctest step swallows its own failure: {ln.strip()!r}. A test run "
            f"that cannot fail the build is the compile-only gate wearing a run "
            f"step's name"
        )


def test_make_test_is_not_a_phase_b1_stub():
    """``c/README.md`` documents ``make test`` as the local flow. It printed a
    skip and exited 0 for every one of the 30 tests, on every run."""
    text = _MAKEFILE.read_text(encoding="utf-8")
    # COMMENTS ARE EXEMPT. The rc356 recipe documents the stub it replaced, in
    # prose, by quoting it — so a whole-file substring search matches the very
    # fix it is checking for. (This assertion failed exactly that way when first
    # written.) Same exemption discipline the ref-notation guard needs for code
    # spans: a mechanical check that cannot tell a description of the defect from
    # the defect reports the fix as the bug.
    recipe = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    assert "no test_srmech.c yet — skipping" not in recipe, (
        "c/Makefile's `test` target is back to looking for test/test_srmech.c — a "
        "file that has never existed here — and exiting 0. That is a false green "
        "on the documented developer path"
    )
    assert "$(TESTBINS)" in recipe, (
        "c/Makefile's `test` target no longer builds the c/test/test_srmech_*.c set")
