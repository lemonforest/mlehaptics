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
* ARM 2 is the can-fail of the instrument itself: a planted one-line writer, run
  OUTSIDE this tree's conftest, MUST move the sentinel unguarded (else this
  environment cannot see a write and ARM 1 is vacuous — inconclusive, not a
  pass) and must NOT move it with ``-p tests._git_env_guard``.
* ARM 3 runs ``tools/hooks/check_hooks.py ledger`` DIRECTLY — no pytest, so no
  conftest guard — under the same export. Every case must pass and the sentinel
  must not move. This is the operator who runs the self-check by hand, and it
  is where the read-side defect lived: the hook child inherited the export and
  answered for the sentinel, so BLOCK cases read ALLOW.
* The PIN: the guard's list is a superset of what the RUNNING git prints for
  ``git rev-parse --local-env-vars``, so a future git that adds a name reds.
* The DECIDER: the worktree-pointer lookup answers in both directions.

numpy-free. No ``abs()``. No ``hashlib`` — bytes are compared, not digested.
"""

from __future__ import annotations

import os
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


# ── ARM 2 ────────────────────────────────────────────────────────────────────

PLANTED_WRITER = (
    "import subprocess\n\n"
    "def test_planted_writer(tmp_path):\n"
    "    subprocess.run(['git', 'config', '--local', 'user.name', 'planted'],\n"
    "                   cwd=str(tmp_path))\n")


@_NEEDS_GIT
@pytest.mark.parametrize("guarded", [False, True], ids=["unguarded", "guarded"])
def test_the_sentinel_sees_a_write_and_the_guard_stops_it(tmp_path, guarded) -> None:
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
    plugin = ["-p", "tests._git_env_guard"] if guarded else []
    proc = _pytest(["-c", str(planted / "pytest.ini"), "--rootdir", str(planted),
                    *plugin, f"--basetemp={tmp_path / 'bt'}", str(planted)],
                   planted, env, 300)
    text = proc.stdout.decode("utf-8", "replace")
    moved = _moved(before, _state(repo))
    # The planted test must have RUN in both arms. A plugin that failed to load
    # stops pytest before any test, and a sentinel nobody wrote to is then a
    # vacuous "the guard stopped it".
    assert proc.returncode == 0 and "1 passed" in text, (
        "the planted writer did not run to a pass, so this arm measured "
        "nothing:\n" + text[-800:])
    if guarded:
        assert moved == [], f"-p tests._git_env_guard did not stop the write: {moved}"
    else:
        assert moved, (
            "the UNGUARDED planted writer did not move the sentinel, so this "
            "environment cannot see a write and ARM 1 is vacuous here — "
            "inconclusive, not a pass:\n" + text[-800:])


# ── ARM 3 ────────────────────────────────────────────────────────────────────

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
    summary = [line for line in err.splitlines() if "passed," in line]
    assert summary and " 0 passed," not in summary[-1], (
        f"check_hooks.py ledger ran no cases under the export: {err[-600:]!r}")
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
