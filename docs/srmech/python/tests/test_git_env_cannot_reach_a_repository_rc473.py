"""The git-writing tests may not reach a repository an exported variable names.
(rc473 final round, `#T1188`)

THE INCIDENT THIS PINS
----------------------
From 2026-09-11 21:55 (commit ``e3720e256``, the first of 60 commits on the
rc473 branch authored that way) until 2026-09-14 the live repository's SHARED
``.git/config`` held ``user.name = decoy identity``. The writer was
``tests/test_hook_fixture_env_isolation_rc471.py``'s own ``_make_decoy``: it ran
``git init`` and ``git config --local`` with the inherited environment while
``GIT_DIR`` / ``GIT_WORK_TREE`` were exported at a worktree gitdir of the live
repository, and ``config --local`` from a worktree gitdir writes the shared
config. The fix is three layers (``tests/_git_env.py`` explains each): the
writers scrub at their source, ``tests/_git_env_guard.py`` scrubs the whole
pytest process, and the tools locate a worktree per invocation so nobody has to
export anything.

WHAT EACH TEST PROVES, AND HOW IT CAN FAIL
------------------------------------------
* ARM 1 runs the two git-WRITING test files in a child pytest with ``GIT_DIR`` /
  ``GIT_WORK_TREE`` exported at a SENTINEL repository's worktree gitdir, and
  asserts every byte of the sentinel's gitdir outside ``objects/`` (plus its
  object set) is unchanged — and that the child PASSED, because a guard that
  stops the writers working is not a fix. Measured red on ``52371629a``, the
  tree before this repair: the sentinel config gained ``worktree = …`` and
  ``[user] name = decoy identity``.
* ARM 1b is the same run with ``--noconftest``: the writers scrubbing at their
  SOURCE, with no suite guard in the process. ARM 1's child runs from this
  tree, so this tree's conftest scrubs the export before any writer runs, and
  ARM 1 only ever saw the two layers together — the rc471 helpers could go
  back to the inherited environment with ARM 1 green (measured at the final
  round's gate). The child must collect and PASS at least one test per writer
  file, with nothing skipped, or the arm measured nothing.
* ARM 2 is the can-fail of the instrument itself: a planted one-line writer, run
  OUTSIDE this tree's conftest, MUST move the sentinel unguarded (else this
  environment cannot see a write and ARM 1 is vacuous — inconclusive, not a
  pass) and must NOT move it with ``-p tests._git_env_guard``.
* ARM 2b loads the guard the way the SUITE does: the same planted writer with
  ``-p tests.conftest``, so the scrub reaches it only through conftest's own
  import line. ARM 2's ``-p tests._git_env_guard`` loads the module whether or
  not conftest imports it, so it pinned the guard's body and not its wiring —
  deleting that import line left every gate green (measured at the final
  round's gate). The sentinel must not move and the writer must pass.
* ARM 3 runs ``tools/hooks/check_hooks.py ledger`` DIRECTLY — no pytest, so no
  conftest guard — under the same export. Every case must pass and the sentinel
  must not move. This is the operator who runs the self-check by hand, and it
  is where the read-side defect lived: the hook child inherited the export and
  answered for the sentinel, so BLOCK cases read ALLOW. The case count is
  PARSED from check_hooks' summary and must be at least one: a run that
  selects no check prints ``0 passed, 0 failed, 0 skipped (0 cases)`` and exits
  0, and every other assertion of the arm is then vacuously true.
* ARM 3a and ARM 3b (rc473 instrument round) pin the two hook-side scrubs ONE AT
  A TIME. ARM 3 needs both removed before it reds, because each hides the
  other's removal: ``check_hooks.invoke()``'s scrub is pinned by a probe child
  that runs no git and reports the ``GIT_*`` names it was handed, and
  ``_hooklib.git()``'s — the only layer for a hook the harness launches
  directly — by calling it in this process under the export, where it must
  answer for its cwd and write only there.
* The PIN: the guard's list is a superset of what the RUNNING git prints for
  ``git rev-parse --local-env-vars``, so a future git that adds a name reds.
  The three write-redirect names git does not list are pinned LITERALLY, with a
  per-name control that the running git honours each one and the scrub stops it.
* The DECIDER: the worktree-pointer lookup answers in both directions.
* The WALK: a real ``.git`` directory ends the walk, and does so under a
  worktree-pointer checkout whose ``/mnt`` twin exists — the geometry in which
  continuing past it would hand a nested repository's git the outer
  checkout's gitdir.

numpy-free. No ``abs()``. No ``hashlib`` — bytes are compared, not digested.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests import _git_env

PY_ROOT = Path(__file__).resolve().parents[1]
CHECKER = PY_ROOT / "tools" / "hooks" / "check_hooks.py"

#: The test files that WRITE git repositories. Found by an AST scan of every
#: ``*.py`` under ``docs/srmech`` at ``52371629a`` (39 writing call sites): the
#: rc471 file's own setup, and ``check_hooks.py``'s fixtures, which this ledger
#: gate drives.
WRITERS = (
    "tests/test_hook_fixture_env_isolation_rc471.py",
    "tests/test_ledger_freshness_hook_rc468.py",
)

_NEEDS_GIT = pytest.mark.skipif(shutil.which("git") is None,
                                reason="the sentinel is a real git repository")


def _child_env(**extra: str) -> dict:
    """The environment for a nested run: the parent's, minus the runner state
    a nested pytest must not inherit, plus ``extra``."""
    env = dict(os.environ)
    for name in [k for k in env if k.startswith(("PYTEST_XDIST_", "PYTEST_CURRENT_TEST"))]:
        env.pop(name)
    env.update(extra)
    return env


def _git(args, cwd: Path) -> None:
    env = _git_env.scrubbed()
    env["GIT_CEILING_DIRECTORIES"] = str(Path(cwd).resolve().parent)
    proc = subprocess.run(["git", *args], cwd=str(cwd), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert proc.returncode == 0, (
        f"sentinel setup `git {' '.join(args)}` failed: {proc.stdout!r}")


def _make_sentinel(base: Path):
    """A repository shaped like the live one: ``extensions.worktreeConfig`` on,
    and a worktree whose gitdir is the thing an operator exported."""
    repo, worktree = base / "sentinel", base / "sentinel_wt"
    repo.mkdir(parents=True)
    _git(["init", "-q", "-b", "main"], repo)
    _git(["config", "--local", "user.name", "Sentinel Owner"], repo)
    _git(["config", "--local", "user.email", "sentinel@example.invalid"], repo)
    _git(["config", "--local", "extensions.worktreeConfig", "true"], repo)
    (repo / "f.txt").write_bytes(b"x\n")
    _git(["add", "--", "f.txt"], repo)
    _git(["-c", "commit.gpgsign=false", "commit", "-q", "-m", "sentinel"], repo)
    _git(["worktree", "add", "-q", "-b", "w", str(worktree)], repo)
    return repo, worktree, repo / ".git" / "worktrees" / worktree.name


def _state(repo: Path) -> dict:
    """Every byte of the gitdir outside ``objects/``, plus the object SET."""
    gitdir = repo / ".git"
    out: dict = {}
    objects = []
    for path in sorted(gitdir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(gitdir).as_posix()
        if rel.startswith("objects/"):
            objects.append(rel)
        else:
            out[rel] = path.read_bytes()
    out["<object set>"] = "\n".join(objects).encode()
    return out


def _moved(before: dict, after: dict) -> list:
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def _pytest(args, cwd: Path, env: dict, timeout: float):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "-p", "no:xdist", "-p", "no:randomly", *args],
        cwd=str(cwd), env=env, timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


_TALLY_LINE = re.compile(r"\b(?:passed|failed|errors?|skipped|no tests ran)\b.* in [0-9.]+s")
_TALLY_ITEM = re.compile(
    r"(\d+) (passed|failed|skipped|deselected|xfailed|xpassed|errors?|warnings?)\b")


def _tally(text: str) -> dict:
    """pytest's final tally line, parsed — ``{"passed": 5}`` — or ``{}`` if none.

    Warnings are dropped: they say nothing about whether a test RAN. ``error`` /
    ``errors`` fold to ``error``.
    """
    for line in reversed(text.splitlines()):
        if _TALLY_LINE.search(line):
            out: dict = {}
            for count, kind in _TALLY_ITEM.findall(line):
                if kind.startswith("warning"):
                    continue
                kind = "error" if kind.startswith("error") else kind
                out[kind] = out.get(kind, 0) + int(count)
            return out
    return {}


# ── ARM 1 ────────────────────────────────────────────────────────────────────

@_NEEDS_GIT
def test_the_git_writing_tests_cannot_reach_a_repository_GIT_DIR_names(tmp_path) -> None:
    repo, worktree, gitdir = _make_sentinel(tmp_path)
    before = _state(repo)
    env = _child_env(GIT_DIR=str(gitdir), GIT_WORK_TREE=str(worktree))
    proc = _pytest([f"--basetemp={tmp_path / 'bt'}", *WRITERS], PY_ROOT, env, 1200)
    text = proc.stdout.decode("utf-8", "replace")
    moved = _moved(before, _state(repo))
    assert moved == [], (
        f"the git-writing tests WROTE the repository GIT_DIR named: {moved}. "
        f"Its config now reads:\n{(repo / '.git' / 'config').read_text()}\n"
        + text[-1500:])
    assert proc.returncode == 0, (
        "the sentinel is intact but the writers did not pass under the exported "
        "variables — a guard that stops them working is not a fix:\n" + text[-2500:])


# ── ARM 1b ───────────────────────────────────────────────────────────────────

@_NEEDS_GIT
def test_the_git_writing_tests_scrub_at_their_source_without_the_suite_guard(tmp_path) -> None:
    assert CHECKER.is_file(), f"{CHECKER} is missing, so the writers cannot run"
    repo, worktree, gitdir = _make_sentinel(tmp_path)
    before = _state(repo)
    env = _child_env(GIT_DIR=str(gitdir), GIT_WORK_TREE=str(worktree))
    proc = _pytest(["--noconftest", f"--basetemp={tmp_path / 'bt'}", *WRITERS],
                   PY_ROOT, env, 1200)
    text = proc.stdout.decode("utf-8", "replace")
    moved = _moved(before, _state(repo))
    assert moved == [], (
        f"with no conftest in the process, the git-writing tests WROTE the "
        f"repository GIT_DIR named: {moved} — a writer is not scrubbing at its "
        f"source. Its config now reads:\n{(repo / '.git' / 'config').read_text()}\n"
        + text[-1500:])
    tally = _tally(text)
    assert proc.returncode == 0 and set(tally) == {"passed"} and tally["passed"] >= len(WRITERS), (
        f"the writers did not all collect and pass under --noconftest (tally "
        f"{tally}), so this arm measured nothing, or a guard stopped them "
        f"working:\n" + text[-2500:])


# ── ARM 2 ────────────────────────────────────────────────────────────────────

PLANTED_WRITER = (
    "import subprocess\n\n"
    "def test_planted_writer(tmp_path):\n"
    "    subprocess.run(['git', 'config', '--local', 'user.name', 'planted'],\n"
    "                   cwd=str(tmp_path))\n")


def _run_planted_writer(tmp_path: Path, plugin: list):
    """The planted writer in its own rootdir, OUTSIDE this tree's conftest, under
    the sentinel export, with ``plugin`` (``-p`` arguments) loaded. Returns the
    child's output and the sentinel keys that moved."""
    repo, worktree, gitdir = _make_sentinel(tmp_path)
    before = _state(repo)
    planted = tmp_path / "planted"
    planted.mkdir()
    (planted / "test_planted_writer.py").write_text(PLANTED_WRITER, encoding="utf-8")
    (planted / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    pythonpath = os.pathsep.join(
        [str(PY_ROOT)] + ([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else []))
    env = _child_env(GIT_DIR=str(gitdir), GIT_WORK_TREE=str(worktree),
                     PYTHONPATH=pythonpath)
    proc = _pytest(["-c", str(planted / "pytest.ini"), "--rootdir", str(planted),
                    *plugin, f"--basetemp={tmp_path / 'bt'}", str(planted)],
                   planted, env, 300)
    text = proc.stdout.decode("utf-8", "replace")
    # The planted test must have RUN. A plugin that failed to load stops pytest
    # before any test, and a sentinel nobody wrote to is then a vacuous "the
    # guard stopped it".
    assert proc.returncode == 0 and "1 passed" in text, (
        "the planted writer did not run to a pass, so this arm measured "
        "nothing:\n" + text[-800:])
    return text, _moved(before, _state(repo))


@_NEEDS_GIT
@pytest.mark.parametrize("guarded", [False, True], ids=["unguarded", "guarded"])
def test_the_sentinel_sees_a_write_and_the_guard_stops_it(tmp_path, guarded) -> None:
    plugin = ["-p", "tests._git_env_guard"] if guarded else []
    text, moved = _run_planted_writer(tmp_path, plugin)
    if guarded:
        assert moved == [], f"-p tests._git_env_guard did not stop the write: {moved}"
    else:
        assert moved, (
            "the UNGUARDED planted writer did not move the sentinel, so this "
            "environment cannot see a write and ARM 1 is vacuous here — "
            "inconclusive, not a pass:\n" + text[-800:])


# ── ARM 2b ───────────────────────────────────────────────────────────────────

@_NEEDS_GIT
def test_the_suite_conftest_loads_the_guard_before_a_writer_runs(tmp_path) -> None:
    assert (PY_ROOT / "tests" / "conftest.py").is_file(), "tests/conftest.py is missing"
    text, moved = _run_planted_writer(tmp_path, ["-p", "tests.conftest"])
    assert moved == [], (
        f"loaded through tests/conftest.py, the planted writer WROTE the "
        f"repository GIT_DIR named: {moved}. The suite guard is not wired: "
        f"conftest must import tests._git_env_guard at import time.\n" + text[-800:])


# ── ARM 3 ────────────────────────────────────────────────────────────────────

_CHECK_HOOKS_SUMMARY = re.compile(
    r"^\s*(\d+) passed, (\d+) failed, (\d+) skipped \((\d+) cases\)\s*$")


@_NEEDS_GIT
def test_check_hooks_ledger_under_an_exported_GIT_DIR_passes_and_writes_nothing(tmp_path) -> None:
    assert CHECKER.is_file(), f"{CHECKER} is missing"
    repo, worktree, gitdir = _make_sentinel(tmp_path)
    before = _state(repo)
    env = _child_env(GIT_DIR=str(gitdir), GIT_WORK_TREE=str(worktree))
    proc = subprocess.run([sys.executable, str(CHECKER), "ledger"], cwd=str(PY_ROOT),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=900)
    err = proc.stderr.decode("utf-8", "replace")
    moved = _moved(before, _state(repo))
    assert moved == [], f"check_hooks.py ledger WROTE the exported repository: {moved}"
    # rc473 final repair 1 (`#T1188`): the count is PARSED. Until then this read
    # `" 0 passed," not in summary[-1]`, and check_hooks prints the summary with
    # the count at the START of its line, so a zero-case run never matched.
    counts = [m for m in map(_CHECK_HOOKS_SUMMARY.match, err.splitlines()) if m]
    assert counts and int(counts[-1].group(4)) >= 1 and int(counts[-1].group(1)) >= 1, (
        f"check_hooks.py ledger ran no cases under the export, so the assertions "
        f"below would be vacuously true: {err[-600:]!r}")
    assert proc.returncode == 0 and "[FAIL]" not in err, (
        "a hook fixture case gave a WRONG VERDICT under an exported GIT_DIR — the "
        "hook child answered for the exported repository instead of its fixture:\n"
        + "\n".join(line for line in err.splitlines()
                    if "[FAIL]" in line or "passed," in line))


# ── the pin ──────────────────────────────────────────────────────────────────

@_NEEDS_GIT
def test_the_guard_list_covers_every_name_the_running_git_calls_repository_local(tmp_path) -> None:
    proc = subprocess.run(["git", "rev-parse", "--local-env-vars"], cwd=str(tmp_path),
                          env=_git_env.scrubbed(), stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    names = proc.stdout.decode("utf-8", "replace").split()
    assert proc.returncode == 0 and len(names) >= 10, (
        f"`git rev-parse --local-env-vars` did not answer: {proc.stdout!r}")
    missing = sorted(set(names) - set(_git_env.GIT_REPO_LOCAL_ENV))
    assert missing == [], (
        f"this git declares {missing} repository-local and the guard does not "
        f"remove them. Add them to tests/_git_env.py:GIT_LOCAL_ENV_VARS.")
    assert "GIT_CEILING_DIRECTORIES" not in _git_env.GIT_REPO_LOCAL_ENV, (
        "the ceiling only narrows discovery; scrubbing an operator's ceiling "
        "re-opens discovery of an unrelated repository above the tree")


def test_the_scrub_removes_the_list_and_the_numbered_config_family_and_nothing_else() -> None:
    env = {name: "/somewhere/else" for name in _git_env.GIT_REPO_LOCAL_ENV}
    env.update({"GIT_CONFIG_KEY_0": "user.name", "GIT_CONFIG_VALUE_0": "planted",
                "GIT_CEILING_DIRECTORIES": "/ceiling", "PATH": "/bin",
                "GIT_EDITOR": "true"})
    removed = _git_env.scrub(env)
    assert sorted(env) == ["GIT_CEILING_DIRECTORIES", "GIT_EDITOR", "PATH"], sorted(env)
    assert "GIT_CONFIG_KEY_0" in removed and "GIT_DIR" in removed


# ── ARM 3a / 3b: each hook-side scrub ALONE (rc473 instrument round) ────────

def _hook_modules():
    hooks = PY_ROOT / "tools" / "hooks"
    if str(hooks) not in sys.path:
        sys.path.insert(0, str(hooks))
    import _hooklib as H
    import check_hooks as CH
    return CH, H


def _git_out(args, cwd: Path, env=None):
    """``(exit, stripped stdout)`` of a git call; ``env`` defaults to the scrubbed
    environment with a ceiling, as :func:`_git` uses."""
    if env is None:
        env = _git_env.scrubbed()
        env["GIT_CEILING_DIRECTORIES"] = str(Path(cwd).resolve().parent)
    proc = subprocess.run(["git", *args], cwd=str(cwd), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").strip()


def _make_fixture(path: Path) -> Path:
    path.mkdir(parents=True)
    for args in (["init", "-q", "-b", "main"],
                 ["config", "--local", "user.name", "Fixture Owner"],
                 ["config", "--local", "user.email", "fixture@example.invalid"]):
        _git(args, path)
    (path / "f.txt").write_bytes(b"fixture\n")
    _git(["add", "--", "f.txt"], path)
    _git(["-c", "commit.gpgsign=false", "commit", "-q", "-m", "fixture"], path)
    return path


def test_invoke_hands_the_hook_child_no_repository_selecting_variable(tmp_path, monkeypatch) -> None:
    """ARM 3a — ``check_hooks.invoke()``'s scrub, with no other layer in the path.

    ARM 3 sees this scrub only together with ``_hooklib.git()``'s: measured at
    the rc473 instrument round, removing either one alone left this file green,
    because every hook git call ALSO goes through the other. So the child here
    is a probe script that runs no git at all and reports the ``GIT_*`` names it
    was handed. The control first shows the probe DOES see the planted names
    when it is launched without the scrub.
    """
    import json

    CH, _H = _hook_modules()
    probe = tmp_path / "probe_env.py"
    probe.write_text("import json, os, sys\nsys.stdin.read()\nsys.stderr.write(json.dumps("
                     "sorted(k for k in os.environ if k.startswith('GIT_'))))\n", encoding="utf-8")
    planted = {name: str(tmp_path / "elsewhere") for name in _git_env.GIT_REPO_LOCAL_ENV}
    planted.update({"GIT_CONFIG_KEY_0": "user.name", "GIT_CONFIG_VALUE_0": "planted"})
    for name, value in planted.items():
        monkeypatch.setenv(name, value)
    control = subprocess.run([sys.executable, str(probe)], input=b"{}", env=dict(os.environ),
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    unscrubbed = json.loads(control.stderr.decode("utf-8").strip().splitlines()[-1])
    assert set(planted) <= set(unscrubbed), (
        f"control: the probe did not see the planted names unscrubbed: {unscrubbed}")
    code, err = CH.invoke(str(probe), {})
    assert code == 0, err
    handed = json.loads(err.strip().splitlines()[-1])
    leaked = sorted(set(handed) & set(planted))
    assert leaked == [], f"check_hooks.invoke() handed the hook child {leaked}"


@_NEEDS_GIT
def test_hooklib_git_answers_for_its_cwd_and_writes_nothing_else_under_an_exported_GIT_DIR(tmp_path, monkeypatch) -> None:
    """ARM 3b — ``_hooklib.git()``'s scrub, in this process, with no suite guard
    and no ``invoke()`` in the path: the variables are set by this test after
    conftest ran. It is the only layer for a hook the harness launches directly.

    Under the export at a sentinel worktree gitdir, ``git rev-parse HEAD`` must
    answer the FIXTURE's HEAD and ``git config --local`` must land in the fixture;
    the sentinel's gitdir must not move a byte. The last assertion is the
    control that the write happened at all.
    """
    _CH, H = _hook_modules()
    repo, worktree, gitdir = _make_sentinel(tmp_path)
    fixture = _make_fixture(tmp_path / "fixture")
    want = _git_out(["rev-parse", "HEAD"], fixture)[1]
    before = _state(repo)
    monkeypatch.delenv(H.HOOK_GIT_ENV, raising=False)
    monkeypatch.setenv("GIT_DIR", str(gitdir))
    monkeypatch.setenv("GIT_WORK_TREE", str(worktree))
    head_code, head = H.git(["rev-parse", "HEAD"], cwd=fixture)
    write_code, write_out = H.git(["config", "--local", "user.name", "hooklib planted"], cwd=fixture)
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_WORK_TREE")
    moved = _moved(before, _state(repo))
    assert moved == [], f"_hooklib.git() wrote the repository GIT_DIR named: {moved}"
    assert head_code == 0 and head.strip() == want, (
        f"_hooklib.git() answered {head.strip()!r}; its cwd's HEAD is {want!r}")
    assert write_code == 0 and _git_out(["config", "--local", "--get", "user.name"], fixture)[1] \
        == "hooklib planted", f"control: the write landed nowhere visible ({write_out!r})"


# ── the write-redirect names, pinned literally and by behaviour ─────────────

#: Named HERE, not read from ``_git_env.GIT_WRITE_REDIRECT_ENV``: the scrub test
#: above builds its input FROM the tuple, so emptying the tuple emptied the
#: test's own input and it stayed green (measured at the rc473 instrument round).
_REDIRECT_NAMES = ("GIT_NAMESPACE", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM")


def test_the_scrub_removes_the_write_redirect_names_named_literally() -> None:
    env = {name: "/elsewhere" for name in _REDIRECT_NAMES}
    env.update({"GIT_CONFIG_COUNT": "3",
                "GIT_CONFIG_KEY_0": "user.name", "GIT_CONFIG_VALUE_0": "planted",
                "GIT_CONFIG_KEY_1": "user.email", "GIT_CONFIG_VALUE_1": "p@example.invalid",
                "GIT_CONFIG_KEY_12": "core.worktree", "GIT_CONFIG_VALUE_12": "/elsewhere",
                "PATH": "/bin"})
    removed = _git_env.scrub(env)
    assert sorted(env) == ["PATH"], sorted(env)
    missing = sorted(set(_REDIRECT_NAMES) - set(removed))
    assert missing == [], f"scrub() no longer removes {missing}"


def _redirect_env(cwd: Path, home: Path) -> dict:
    env = _git_env.scrubbed()
    env.pop("GIT_CONFIG_NOSYSTEM", None)
    env["GIT_CEILING_DIRECTORIES"] = str(Path(cwd).resolve().parent)
    env.update({"HOME": str(home), "USERPROFILE": str(home),
                "XDG_CONFIG_HOME": str(home / ".config")})
    return env


@_NEEDS_GIT
@pytest.mark.parametrize("name", ["GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM",
                                  "GIT_CONFIG_COUNT", "GIT_NAMESPACE"])
def test_each_redirect_moves_what_the_running_git_reads_or_writes_and_the_scrub_stops_it(tmp_path, name) -> None:
    """Per name: the RUNNING git honours it (the control — else the literal pin
    above guards a name this git ignores) and the scrubbed environment does not."""
    home = tmp_path / "home"
    home.mkdir()
    fixture = _make_fixture(tmp_path / "fixture")
    base = _redirect_env(fixture, home)
    if name in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
        target = tmp_path / "redirected.cfg"
        target.write_text("[user]\n\tname = redirected\n", encoding="utf-8")
        args = ["config", "--global" if name == "GIT_CONFIG_GLOBAL" else "--system",
                "--get", "user.name"]
        planted = dict(base, **{name: str(target)})
        control = _git_out(args, fixture, planted)
        scrubbed = dict(planted)
        _git_env.scrub(scrubbed)
        got = _git_out(args, fixture, scrubbed)
        assert control == (0, "redirected"), f"control: this git ignores {name}: {control}"
        assert got[1] != "redirected", f"the scrubbed environment still honours {name}: {got}"
    elif name == "GIT_CONFIG_COUNT":
        args = ["config", "--get", "user.name"]
        planted = dict(base, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="user.name",
                       GIT_CONFIG_VALUE_0="redirected")
        control = _git_out(args, fixture, planted)
        scrubbed = dict(planted)
        _git_env.scrub(scrubbed)
        got = _git_out(args, fixture, scrubbed)
        assert control[1] == "redirected", f"control: this git ignores the numbered pair: {control}"
        assert got == (0, "Fixture Owner"), f"the scrubbed environment still honours it: {got}"
    else:
        bares = [tmp_path / "bare_planted.git", tmp_path / "bare_scrubbed.git"]
        for bare in bares:
            _git(["init", "-q", "--bare", str(bare)], tmp_path)
        planted = dict(base, GIT_NAMESPACE="planted_ns")
        scrubbed = dict(planted)
        _git_env.scrub(scrubbed)
        pushed = [_git_out(["push", "-q", str(bares[0]), "HEAD:refs/heads/x"], fixture, planted),
                  _git_out(["push", "-q", str(bares[1]), "HEAD:refs/heads/x"], fixture, scrubbed)]
        refs = [sorted(p.relative_to(b).as_posix() for p in (b / "refs").rglob("*") if p.is_file())
                for b in bares]
        assert pushed[0][0] == 0 and "refs/namespaces/planted_ns/refs/heads/x" in refs[0], (
            f"control: the namespace did not redirect the push: {pushed[0]} {refs[0]}")
        assert pushed[1][0] == 0 and refs[1] == ["refs/heads/x"], (
            f"the scrubbed environment still honours GIT_NAMESPACE: {pushed[1]} {refs[1]}")


# ── the decider, both directions ─────────────────────────────────────────────

def test_the_worktree_pointer_lookup_returns_otherwise_in_both_directions() -> None:
    windows = "gitdir: D:/GitHub/mlehaptics/.git/worktrees/wf_x\n"
    twin = "/mnt/d/GitHub/mlehaptics/.git/worktrees/wf_x"
    checkout = "/mnt/d/GitHub/mlehaptics/.claude/worktrees/wf_x"
    only_twin = lambda path: path == twin                       # noqa: E731
    # WSL git on a Windows-made worktree: the twin is handed to the invocation
    assert _git_env.pointer_git_args(windows, checkout, only_twin) == [
        "--git-dir=" + twin, "--work-tree=" + checkout]
    # backslash spelling of the same pointer
    assert _git_env.pointer_git_args(
        "gitdir: D:\\GitHub\\mlehaptics\\.git\\worktrees\\wf_x", checkout, only_twin
    ) == ["--git-dir=" + twin, "--work-tree=" + checkout]
    # Windows git: the path exists as written -> leave discovery alone
    assert _git_env.pointer_git_args(windows, checkout, lambda path: True) == []
    # neither the path nor its twin exists -> nothing to hand over
    assert _git_env.pointer_git_args(windows, checkout, lambda path: False) == []
    # a relative pointer, a POSIX absolute pointer, and garbage -> []
    assert _git_env.pointer_git_args("gitdir: ../main/.git/worktrees/w", checkout, only_twin) == []
    assert _git_env.pointer_git_args("gitdir: /srv/repo/.git/worktrees/w", checkout, only_twin) == []
    assert _git_env.pointer_git_args("not a pointer", checkout, only_twin) == []
    assert _git_env.pointer_git_args("", checkout, only_twin) == []


def test_the_walk_answers_nothing_for_an_ordinary_repository_directory(tmp_path) -> None:
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    (tmp_path / "repo" / "sub").mkdir()
    assert _git_env.git_location_args(tmp_path / "repo" / "sub") == []
    pointer_checkout = tmp_path / "wt"
    pointer_checkout.mkdir()
    (pointer_checkout / ".git").write_text("gitdir: Q:/nowhere/at/all\n", encoding="utf-8")
    assert _git_env.git_location_args(pointer_checkout) == [], (
        "a pointer whose path and /mnt twin are both absent must leave git's own "
        "discovery (and its own error) alone")


def test_the_walk_stops_at_a_repository_directory_nested_under_a_pointer_checkout(tmp_path) -> None:
    """A real ``.git`` directory ends the walk even when the checkout ABOVE it is
    a worktree pointer whose twin exists (rc473 final repair 1, `#T1188`).

    The test above put nothing above its repository, so stopping at the ``.git``
    directory and continuing past it gave the same ``[]``: the stop replaced by
    ``continue`` left this file green, and the walk then answered a nested
    repository with the outer checkout's gitdir (measured at the final round's
    gate). Here the outer checkout's answer is shown first — so a walk that
    continues has a wrong answer to give — and then the nested repository must
    get none of it.
    """
    twin = "/mnt/d/GitHub/outer/.git/worktrees/w"
    only_twin = lambda path: path == twin                       # noqa: E731
    outer = tmp_path / "outer"
    (outer / "plain").mkdir(parents=True)
    (outer / ".git").write_text("gitdir: D:/GitHub/outer/.git/worktrees/w\n", encoding="utf-8")
    handed = ["--git-dir=" + twin, "--work-tree=" + str(outer.resolve())]
    # the control: inside the pointer checkout, its twin IS handed over
    assert _git_env.git_location_args(outer / "plain", environ={}, exists=only_twin) == handed
    nested = outer / "fixture_repo"
    (nested / ".git").mkdir(parents=True)
    (nested / "sub").mkdir()
    for start in (nested, nested / "sub"):
        assert _git_env.git_location_args(start, environ={}, exists=only_twin) == [], (
            f"the walk went past {nested / '.git'} (a repository directory) and "
            f"handed its git the outer checkout's gitdir")
