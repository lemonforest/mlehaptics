"""rc471 (`#T1188`) — THE FIGURE-RUN CORE, and each defect it was lifted to fix.

``tools/figure_run.py`` is the apparatus every later rc of the "ALU All The Way"
arc runs to re-print its own figures. It was extracted from
``tools/rc470_figures.py``, which was **DEAD on ``main``** when rc471 opened —
``KeyError: 'R3_VOCABULARY'``, because it read its comparison baseline from the
moving ref ``main`` and ``main`` had become rc470.

Every test here pins one of the four defects the lift repaired, and each one
CAN FAIL — the can-fail is in the test, not in a comment:

* a moving baseline           → :func:`test_the_baseline_refuses_every_moving_ref`
* an instrument that cannot   → :func:`test_the_head_column_can_return_otherwise`
  return otherwise
* a cross-bucket extraction   → :func:`test_self_check_refuses_a_cross_bucket_name`
* a junit parse that assumed  → :func:`test_junit_grouping_is_on_classname`
  a ``file`` attribute

numpy-free. No ``abs()``.
"""

from __future__ import annotations

import re
import sys
import types
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_TOOLS = _HERE.parents[0] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import figure_run as fr  # noqa: E402  (tools/ is on sys.path just above)


# ── 1. the baseline cannot move ──────────────────────────────────────────────

@pytest.mark.parametrize("ref", ["main", "master", "HEAD", "ORIG_HEAD",
                                 "srmech-v0.9.0rc469", "rc469", "",
                                 "main:tools/demotion_probe.py", "1FD37C736"])
def test_the_baseline_refuses_every_moving_ref(ref) -> None:
    """A ref that can move is the defect the parameter exists to prevent.

    ``main`` is the one that actually bit; the tag is refused too, because a
    tag is a pointer and this file's own precedent (``fe3454677``) pins a raw
    commit SHA. Upper case is refused so the pin is byte-comparable.
    """
    with pytest.raises(ValueError):
        fr.assert_immutable_baseline(ref)


@pytest.mark.parametrize("ref", ["1fd37c736", "fe3454677", "fc717212d",
                                 "1fd37c736ab70a75629fa65f1ff4cc70715f574f"])
def test_the_baseline_accepts_an_abbreviated_or_full_sha(ref) -> None:
    assert fr.assert_immutable_baseline(ref) == ref


def test_the_shipped_caller_pins_an_immutable_sha() -> None:
    """``tools/rc470_figures.py`` must not reacquire a moving baseline.

    The direct predicate, on the shipped text rather than on a re-import: no
    ``git show`` of a REF-qualified path anywhere in the file.
    """
    import rc470_figures as rc
    fr.assert_immutable_baseline(rc.R3_BASELINE_COMMIT)
    text = (_TOOLS / "rc470_figures.py").read_text(encoding="utf-8")
    for moving in fr.MOVING_REFS:
        assert f'"{moving}:docs/' not in text and f"'{moving}:docs/" not in text, (
            f"tools/rc470_figures.py reads a path at the MOVING ref {moving!r}. "
            f"That is exactly how the harness died between rc470 and rc471.")


# ── 2. the == HEAD column can return otherwise ───────────────────────────────

def test_the_head_column_can_return_otherwise() -> None:
    """*An instrument that cannot return otherwise is not a measurement.*

    Through rc470 the column hashed the working file with ``git hash-object``,
    which applies no clean filter — so on a CRLF checkout every instrument
    disagreed with its LF ``HEAD`` blob and the column printed ``!= HEAD`` for
    ALL NINE on a tree ``git diff --ignore-cr-at-eol`` called empty. It could
    not say anything else. Both directions are pinned here.
    """
    lf = b"alpha\nbeta\n"
    crlf = b"alpha\r\nbeta\r\n"
    # the line-ending difference alone must NOT read as a content change
    assert fr.head_state_of(lf, crlf) == "== HEAD"
    assert fr.head_state_of(crlf, lf) == "== HEAD"
    assert fr.head_state_of(lf, lf) == "== HEAD"
    # ONE byte of real content must flip it — in either encoding
    assert fr.head_state_of(lf, b"alpha\nbetb\n") == "!= HEAD (content differs)"
    assert fr.head_state_of(crlf, b"alpha\r\nbetb\r\n") == (
        "!= HEAD (content differs)")


@pytest.mark.skipif(not fr.git_available(),
                    reason="git cannot read the repo from this environment")
def test_the_head_column_is_live_on_a_real_tracked_file() -> None:
    """The wrapper, against git, on a file that is certainly in HEAD."""
    assert fr.head_state("tools/demotion_probe.py") in (
        "== HEAD", "!= HEAD (content differs)")
    assert fr.head_state("tools/no_such_tool_rc471.py") == "!= HEAD (not in HEAD)"


def test_the_head_column_refuses_rather_than_calling_everything_new(monkeypatch) -> None:
    """A git failure must NOT read as "not in HEAD".

    ``git show HEAD:<path>`` returns the same non-zero status for "the path is
    absent" and for "git cannot read this repository", so a wrapper that maps
    non-zero to "not in HEAD" reports EVERY instrument as brand new the moment
    git is unreachable — the silent-degradation shape that stamped an empty
    ``def_blob`` on 428 of 428 ops one layer down. Found by this test.
    """
    class _Dead:
        returncode = 128
        stdout = b""
        stderr = b"fatal: not a git repository"

    monkeypatch.setattr(fr.subprocess, "run", lambda *a, **k: _Dead())
    with pytest.raises(RuntimeError) as excinfo:
        fr.head_state("tools/demotion_probe.py")
    assert "not a git repository" in str(excinfo.value)
    assert "not in HEAD" in str(excinfo.value), (
        "the refusal must name the wrong answer it is refusing to give")


# ── 3. dependency closure — the check a line-coverage split cannot make ──────

def test_self_check_accepts_the_shipped_core() -> None:
    fr.self_check(fr)
    import rc470_figures as rc
    fr.self_check(rc)


def test_self_check_refuses_a_cross_bucket_name() -> None:
    """THE CAN-FAIL, and it is the exact defect the extraction had.

    The rc470 → rc471 split measured "0 unassigned non-blank lines" and still
    put a use of ``_native`` in the CORE bucket with its import in the other.
    Line coverage is not dependency closure.
    """
    mod = types.ModuleType("cross_bucket_victim")
    src = "def uses_it():\n    return _native.HAS_NATIVE\n"
    exec(compile(src, "<victim>", "exec"), vars(mod))
    with pytest.raises(NameError) as excinfo:
        fr.self_check(mod)
    assert "_native" in str(excinfo.value)


def test_self_check_does_not_walk_imported_third_party_code() -> None:
    """A module that merely IMPORTS a class must not inherit its globals.

    Measured: walking ``Path`` reported 13 phantom unresolved names
    (``_make_selector``, ``S_ISDIR``, ``ELOOP``, …) out of ``pathlib``'s
    namespace, which made the check unusable on its first run.
    """
    mod = types.ModuleType("importer_only")
    exec(compile("from pathlib import Path\n", "<importer>", "exec"), vars(mod))
    fr.self_check(mod)


# ── 4. the junit split, which a first parse got wrong ────────────────────────

_JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="0" failures="1" skipped="1" tests="4">
<testcase classname="tests.test_figure_run_rc471" name="a" time="0.1"/>
<testcase classname="tests.test_figure_run_rc471" name="b" time="0.1"/>
<testcase classname="tests.test_figure_run_rc471.TestX" name="c" time="0.1">
<failure message="boom">boom</failure></testcase>
<testcase classname="tests.test_figure_run_rc471" name="d" time="0.1">
<skipped message="nope"/></testcase>
</testsuite></testsuites>
"""


def test_junit_grouping_is_on_classname(tmp_path) -> None:
    """⚠️ pytest's junit XML has NO ``file`` attribute on ``<testcase>``.

    A first parse of this XML assumed one and returned ZERO for every gate. The
    grouping key is ``classname``, and a test CLASS appends a segment to it —
    both shapes must land on the same file.
    """
    xml = tmp_path / "u.xml"
    xml.write_text(_JUNIT, encoding="utf-8")
    tally = fr.parse_junit(xml)
    assert set(tally) == {"tests/test_figure_run_rc471.py"}, tally
    assert tally["tests/test_figure_run_rc471.py"] == {
        "passed": 2, "skipped": 1, "failed": 1, "error": 0, "collected": 3}
    assert "file=" not in _JUNIT, (
        "this fixture must reproduce the shipped XML's shape, which carries no "
        "file attribute — the whole point of grouping on classname")


def test_collected_is_the_cell_invariant_figure_and_passed_is_not(tmp_path) -> None:
    """⚠️ ``N passed`` is a property of the tree × THE CELL, not of the tree.

    A row that skips because ``libsrmech`` is absent PASSES on a host that has
    one, so an unchanged gate reports two different "N passed" figures on two
    hosts — MEASURED at 166 against 148 for one of this arc's gate sets.
    ``collected`` = ``passed + skipped`` is invariant across that difference,
    and this pins the arithmetic that makes it so.
    """
    xml = tmp_path / "u.xml"
    xml.write_text(_JUNIT, encoding="utf-8")
    pure = fr.parse_junit(xml)["tests/test_figure_run_rc471.py"]
    # the same file on a host where the skipped row runs and passes
    xml.write_text(_JUNIT.replace('<skipped message="nope"/>', ""),
                   encoding="utf-8")
    native = fr.parse_junit(xml)["tests/test_figure_run_rc471.py"]
    assert native["passed"] != pure["passed"], (
        "the fixture no longer models the cell difference it exists to model")
    assert native["collected"] == pure["collected"] == 3


def test_junit_grouping_reports_an_unmappable_classname(tmp_path) -> None:
    """A classname that resolves to nothing must not be silently dropped."""
    xml = tmp_path / "u.xml"
    xml.write_text(_JUNIT.replace("tests.test_figure_run_rc471",
                                  "nowhere.at.all"), encoding="utf-8")
    assert set(fr.parse_junit(xml)) == {""}
    assert fr._file_of_classname("nowhere.at.all") == ""


# ── 5. ONE walk of the population, every pattern ─────────────────────────────

def test_sweep_agrees_with_a_naive_two_pass_count() -> None:
    """The single-pass sweep must be EQUIVALENT to the per-regex walk it replaces.

    rc470 walked the whole ``.py`` population once per regex — 1020 files, 2040
    reads. The population is identical for every pattern, so it is walked once;
    this pins that the fusion changed no count.
    """
    wide = re.compile(r"\bno (?:more|worse|greater|larger) than\b", re.I)
    bare = re.compile(r"\bno more than\b", re.I)
    fused = fr.sweep_paths(sorted((fr.PY_ROOT / "tools").rglob("*.py")),
                           {"wide": wide, "bare": bare})
    for tag, rx in (("wide", wide), ("bare", bare)):
        occ = lines = files = 0
        for path in sorted((fr.PY_ROOT / "tools").rglob("*.py")):
            got = [len(rx.findall(s)) for s in
                   path.read_text(encoding="utf-8", errors="replace").split("\n")
                   if rx.search(s)]
            if got:
                files += 1
                lines += len(got)
                occ += sum(got)
        assert fused[tag] == (occ, lines, files), tag


# ── 6. the prose file is read ONCE per path ──────────────────────────────────

def test_prose_is_cached_by_path() -> None:
    """rc470 re-read a 4.27 MB CHANGELOG on every one of 29 figures."""
    run = fr.FigureRun(title="t", instruments=("CHANGELOG.md",),
                       baseline_commit="1fd37c736")
    first = run.prose("CHANGELOG.md")
    assert run.prose("CHANGELOG.md") is first, (
        "the second read returned a different object — the cache is not "
        "keyed by path, so the file is being re-read per figure")


def test_a_figure_can_be_diffed_against_several_files() -> None:
    """W1.7: rc470 hash-witnessed NINE instruments and read the prose of TWO."""
    run = fr.FigureRun(title="t", instruments=("CHANGELOG.md",),
                       baseline_commit="1fd37c736")
    run.figure("present in both", 470, "rc{v}",
               where=("CHANGELOG.md", "tools/figure_run.py"))
    assert run.failures == [], run.failures
    run.figure("absent from both", 999999, "rc{v}",
               where=("CHANGELOG.md", "tools/figure_run.py"))
    assert len(run.failures) == 2, (
        "a needle absent from BOTH named files must be reported against BOTH; "
        "reporting it once is how a widened population silently narrows again")
