"""`#T1166` / gh #1653 — ctest COLLECTION PARITY. Strict, two-way, no ceiling.

WHAT THIS ASSERTS, AND WHY IT IS NOT ANOTHER CEILING
----------------------------------------------------
``tests/test_c_test_wiring_rc356.py`` carries ``CEIL_UNWIRED_C_TESTS``, a
``<=`` bound on how many ``c/test/test_srmech_*.c`` files are NOT registered
with ctest. rc452 drains it to 0. But a ``<=`` bound at 0 still cannot see a
future PARTIAL deregistration reported as a smaller number, and — more to the
point — a bound is a claim about a COUNT, while the thing that matters is WHICH
files. This file asserts SET EQUALITY in both directions:

  * a ``c/test/test_srmech_*.c`` with no ``add_test`` is UNREGISTERED — it
    compiles at best and runs nowhere;
  * an ``add_test`` naming a file that does not exist is a GHOST — CMake would
    fail to configure, but the registration would also silently outlive a
    deleted test and nothing else in the tree states that it should not.

THE MEASURED HISTORY THIS CLOSES
--------------------------------
rc356 found that **0 of 30** C test binaries were executed by ANY automation:
there was no ``enable_testing()``, no ``add_test()`` and no ctest step in any
workflow, so the pedantic matrix compiled nine of them and threw the binaries
away. Compiling a test proves only that it compiles — and the cost was
concrete: rc307 reinterpreted the fiedler ``ws_len`` unit and left
``test_srmech_progress_tick.c`` on the old convention, where it returned the
wrong status for ~48 rcs with nothing to notice.

rc356 fixed the mechanism and wired 18, leaving 20 behind a down-only ceiling
that was expected to drain in batches. Measured at the rc452 branch point, ~96
releases later: still 20, still running in no automation on any platform. The
batches never came. That is the finding this file is shaped around — the causal
variable is THE GATE, not intent, and a ceiling that permits a residual is not
the same instrument as an equality that forbids one.

⚠️ WHAT REGISTERING THE 20 IMMEDIATELY FOUND. ``test_srmech_config.c`` includes
the INTERNAL header ``srmech_platform.h`` (``c/src``, not the public
``c/include``) and had never been compiled by CMake at all, so the missing
include path had nowhere to surface; ``c/Makefile:81`` had carried the
``-I$(SRCDIR)`` note for it the whole time. One registration, one real build
break, found on the first configure.

⚠️ THE PARSE IS A PARSE, NOT A GREP. It reads the ``add_test(NAME ${t} ...)``
loops by resolving the ``foreach`` lists that feed them. A substring grep for
``test_srmech_`` over CMakeLists.txt would also match ``add_executable`` names,
comment prose and the ``target_include_directories`` line — and would therefore
report the set as complete while ``add_test`` was missing, which is precisely
the failure it exists to detect. (The rc348 lesson: a naive grep over one
diff produced 10 "violations" that were all correct.)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_SRMECH_DIR = Path(__file__).resolve().parents[2]
_C_TEST_DIR = _SRMECH_DIR / "c" / "test"
_CMAKE = _SRMECH_DIR / "CMakeLists.txt"

pytestmark = pytest.mark.skipif(
    not _C_TEST_DIR.exists(),
    reason="C tree absent (pure-Python checkout) — nothing to assert about wiring",
)


def _file_census() -> set:
    """Every C test stem on disk.

    ``cascade_explorer.c`` is excluded by the glob on purpose — it is a tool,
    not a test, and has no pass/fail exit contract to register.
    """
    return {p.stem for p in _C_TEST_DIR.glob("test_srmech_*.c")}


def _registered() -> set:
    """Every name ctest is told to RUN, resolved through the foreach lists.

    PREDICATE, stated so it can be reproduced or refuted: find each
    ``add_test(NAME ${VAR} ...)``; for each, take the ``foreach(VAR ...)``
    block that encloses it and expand the names inside — either written inline
    or supplied by a ``set(LIST ...)`` the foreach dereferences.
    """
    text = _CMAKE.read_text(encoding="utf-8")

    # `set(NAME a b c)` blocks, so a foreach over ${NAME} can be expanded.
    lists = {}
    for m in re.finditer(r"set\(\s*([A-Za-z_][A-Za-z0-9_]*)\s+(.*?)\)", text, re.S):
        lists[m.group(1)] = set(re.findall(r"test_srmech_[A-Za-z0-9_]+", m.group(2)))

    names: set = set()
    seen_add_test = 0
    for m in re.finditer(r"foreach\(\s*([A-Za-z_][A-Za-z0-9_]*)\b(.*?)\)(.*?)endforeach\(\)",
                         text, re.S):
        var, header, body = m.group(1), m.group(2), m.group(3)
        if "add_test(" not in body:
            continue
        seen_add_test += 1
        # names written straight into the foreach header
        found = set(re.findall(r"test_srmech_[A-Za-z0-9_]+", header))
        # ...or supplied via ${LIST}
        for ref in re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", header):
            found |= lists.get(ref, set())
        names |= found

    assert seen_add_test, (
        "no foreach block containing add_test() was found in CMakeLists.txt — "
        "the registration was reshaped and this parse has stopped observing. "
        "Re-point it; do not delete the assertion.")
    assert names, (
        "the ctest registration parsed to ZERO names. An empty parse is not an "
        "empty registration — it is this gate failing to measure.")
    return names


def test_the_parse_itself_is_not_vacuous() -> None:
    """Control. Both sides must be non-empty before their equality means anything.

    Stated separately because ``set() == set()`` is a passing assertion, and a
    gate whose two sides can both go empty together is the exact shape of an
    instrument that cannot return otherwise.
    """
    files, reg = _file_census(), _registered()
    assert len(files) >= 30, f"only {len(files)} C test files found — glob is wrong"
    assert len(reg) >= 30, f"only {len(reg)} ctest registrations parsed — parse is wrong"


def test_every_c_test_file_is_registered_with_ctest() -> None:
    """UNREGISTERED direction: a test file nobody runs."""
    missing = sorted(_file_census() - _registered())
    assert not missing, (
        f"{len(missing)} C test file(s) are not registered with ctest and "
        f"therefore run in NO automation: {missing}\n"
        f"Add each to the SRMECH_C_TESTS_RC452 list in CMakeLists.txt. "
        f"`make test` covering them is NOT coverage — no workflow invokes make.")


def test_every_ctest_registration_has_a_file() -> None:
    """GHOST direction: a registration that outlived its test."""
    ghosts = sorted(_registered() - _file_census())
    assert not ghosts, (
        f"ctest registers {len(ghosts)} name(s) with no c/test source: {ghosts}")


def test_the_two_sets_are_EQUAL_stated_as_one_assertion() -> None:
    """The invariant itself, so a reader meets it as one fact rather than two."""
    assert _file_census() == _registered(), (
        "the c/test census and the ctest registration have diverged; see the "
        "two directional tests above for which way")
