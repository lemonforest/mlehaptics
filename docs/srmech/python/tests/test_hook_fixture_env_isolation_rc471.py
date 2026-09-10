"""The hook fixture may not reach a repository the ENVIRONMENT names.
(rc471, `#T1188`)

THE DEFECT THIS PINS, AND IT IS NOT HYPOTHETICAL
------------------------------------------------
rc471's own build session exported ``GIT_DIR`` / ``GIT_WORK_TREE`` at the live
repository so WSL git could open a worktree whose ``.git`` is a pointer file
holding a Windows path, and then ran pytest under it. ``tools/hooks/
check_hooks.py::_init_repo`` builds its repo in a ``TemporaryDirectory`` and
passes ``cwd=`` — which reads as isolation and is not, because git resolves its
repository from the environment BEFORE it looks at the working directory. Three
writes landed on the real repository, not one:

1. ``git init`` re-initialised the live gitdir and wrote ``core.worktree``.
2. ``git add -A`` + ``git commit`` put a fixture commit on the live branch.
3. ``git config user.email/user.name`` overwrote the SHARED ``.git/config``
   identity with ``hook fixture <hooks@example.invalid>``.

(1) and (2) announce themselves. (3) does not: it is silent until somebody
reads ``%an``, and it authored the next EIGHT commits, including the commit
that disclosed the incident. The rc471 CHANGELOG entry carries the numbers.

WHAT IS PINNED HERE
-------------------
Not "the operator should not export ``GIT_DIR``" — that is a rule, and a rule
is not a guard. What is pinned is that the FIXTURE cannot be steered by the
environment at all: :func:`check_hooks.fixture_git_env` scrubs every
repository-selecting variable and pins ``GIT_CEILING_DIRECTORIES`` so plain
upward discovery cannot leave the fixture either.

⚠️ **THE CAN-FAIL IS THE POINT.** ``test_the_decoy_IS_reachable_without_the_scrub``
runs the same three fixture commands through an UNSCRUBBED ``subprocess.run``
and asserts the decoy DOES get written. Without it, every other assertion here
is satisfied by a git that could not reach the decoy for some unrelated reason
— *an instrument that cannot return otherwise is not a measurement.*

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PY_ROOT = Path(__file__).resolve().parents[1]
HOOKS = PY_ROOT / "tools" / "hooks"

if not (HOOKS / "check_hooks.py").is_file():           # pragma: no cover
    pytest.skip("tools/hooks/check_hooks.py absent", allow_module_level=True)

sys.path.insert(0, str(HOOKS))
import check_hooks as CH                               # noqa: E402

DECOY_NAME = "decoy identity"
DECOY_EMAIL = "decoy@example.invalid"


def _git_plain(args, cwd, env=None):
    """``git`` with NO scrubbing — the shape the defect had."""
    return subprocess.run(["git", *args], cwd=str(cwd), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def _make_decoy(root: Path) -> Path:
    """A throwaway repository standing in for the real one."""
    root.mkdir(parents=True, exist_ok=True)
    _git_plain(["init", "-q", "-b", "main"], root)
    _git_plain(["config", "--local", "user.name", DECOY_NAME], root)
    _git_plain(["config", "--local", "user.email", DECOY_EMAIL], root)
    return root


def _decoy_identity(root: Path) -> tuple[str, str]:
    name = _git_plain(["config", "--local", "--get", "user.name"], root)
    mail = _git_plain(["config", "--local", "--get", "user.email"], root)
    return (name.stdout.decode("utf-8", "replace").strip(),
            mail.stdout.decode("utf-8", "replace").strip())


def _decoy_commit_count(root: Path) -> int:
    out = _git_plain(["rev-list", "--count", "--all"], root)
    text = out.stdout.decode("utf-8", "replace").strip()
    return int(text) if text.isdigit() else -1


# ── the pure function, which is where the decision lives ────────────────────

def test_fixture_git_env_removes_every_repository_selecting_name(tmp_path):
    poisoned = {name: "/somewhere/else" for name in CH.GIT_REPO_SELECTING_ENV}
    poisoned["PATH"] = os.environ.get("PATH", "")
    env = CH.fixture_git_env(tmp_path / "fixture", base=poisoned)
    leaked = [n for n in CH.GIT_REPO_SELECTING_ENV
              if n in env and n != "GIT_CEILING_DIRECTORIES"]
    assert leaked == [], (
        f"these repository-selecting variables survived the scrub and would "
        f"outrank cwd=: {leaked}")
    assert env["PATH"] == poisoned["PATH"], (
        "the scrub must remove the git-repository names and NOTHING else — "
        "a fixture git that cannot find its own executable proves nothing")


def test_fixture_git_env_pins_the_ceiling_to_the_fixtures_parent(tmp_path):
    root = tmp_path / "nested" / "fixture"
    env = CH.fixture_git_env(root, base={"PATH": os.environ.get("PATH", "")})
    assert env["GIT_CEILING_DIRECTORIES"] == str(root.resolve().parent), (
        "scrubbing alone leaves the ordinary upward walk open: a fixture "
        "created inside a checkout would discover that checkout by plain "
        "discovery, with no environment variable involved")


# ── the behaviour, end to end ───────────────────────────────────────────────

def test_the_fixture_cannot_write_a_repository_GIT_DIR_names(tmp_path):
    decoy = _make_decoy(tmp_path / "decoy")
    before_id = _decoy_identity(decoy)
    before_n = _decoy_commit_count(decoy)
    assert before_id == (DECOY_NAME, DECOY_EMAIL)

    saved = {n: os.environ.get(n) for n in ("GIT_DIR", "GIT_WORK_TREE")}
    os.environ["GIT_DIR"] = str(decoy / ".git")
    os.environ["GIT_WORK_TREE"] = str(decoy)
    try:
        fixture = tmp_path / "fixture"
        CH._init_repo(fixture)
        (fixture / "a.txt").write_text("x\n", encoding="utf-8")
        CH._commit(fixture, "fixture baseline")
    finally:
        for n, v in saved.items():
            if v is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = v

    assert _decoy_identity(decoy) == before_id, (
        "the fixture's `git config user.name/user.email` reached the "
        "repository GIT_DIR named — this is defect (3), the silent one, "
        "reproduced")
    assert _decoy_commit_count(decoy) == before_n, (
        "the fixture's `git add -A` + `git commit` reached the repository "
        "GIT_DIR named — defect (2)")
    assert (fixture / ".git").is_dir(), (
        "the fixture must still get its OWN repository; an isolation fix that "
        "stops the fixture working is not a fix")


def test_the_decoy_IS_reachable_without_the_scrub(tmp_path):
    """THE CAN-FAIL. Same three commands, unscrubbed — the decoy MUST move.

    If this ever passes-by-not-writing, the test above is vacuous and proves
    nothing about the scrub.
    """
    decoy = _make_decoy(tmp_path / "decoy")
    before_id = _decoy_identity(decoy)
    assert before_id == (DECOY_NAME, DECOY_EMAIL)

    env = dict(os.environ)
    env["GIT_DIR"] = str(decoy / ".git")
    env["GIT_WORK_TREE"] = str(decoy)

    fixture = tmp_path / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    _git_plain(["config", "user.email", "hooks@example.invalid"], fixture, env)
    _git_plain(["config", "user.name", "hook fixture"], fixture, env)

    assert _decoy_identity(decoy) == ("hook fixture", "hooks@example.invalid"), (
        "the unscrubbed control did NOT reach the decoy, so this environment "
        "cannot demonstrate the defect and the scrub test above is vacuous "
        "here — classify this as an inconclusive environment, not a pass")
