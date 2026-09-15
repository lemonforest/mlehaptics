"""How srmech's tooling addresses git WITHOUT the environment naming a repository.
(rc473 final round, `#T1188`)

ONE home for two things every git-calling test and tool needs, and it is not a
test module (no ``test_`` prefix, no assertions):

1. :data:`GIT_REPO_LOCAL_ENV` and :func:`scrub` — the environment variables that
   make a child ``git`` resolve, read or write a repository other than the one
   its working directory is in.
2. :func:`git_location_args` / :func:`pointer_git_args` — the per-invocation
   ``--git-dir`` / ``--work-tree`` pair that lets a git which cannot follow a
   worktree's ``.git`` pointer as written read that checkout anyway, so nobody
   has to EXPORT ``GIT_DIR`` to get an answer.

WHY THIS FILE EXISTS — THE LEAK
-------------------------------
From 2026-09-11 21:55 (commit ``e3720e256``) until 2026-09-14 the shared
``.git/config`` of the live repository held ``user.name = decoy identity`` /
``user.email = decoy@example.invalid``: the constants of
``tests/test_hook_fixture_env_isolation_rc471.py``. That file's own setup helper
ran ``git init`` and two ``git config --local`` with the INHERITED environment,
while ``GIT_DIR`` / ``GIT_WORK_TREE`` were exported at a worktree gitdir of the
live repository — and ``config --local`` from a worktree gitdir writes the
SHARED config (``extensions.worktreeConfig`` diverts only ``--worktree``
writes). Operators exported the pair because shipped remedy text told them to:
WSL git cannot follow a worktree pointer holding a Windows path, and "export
GIT_DIR and GIT_WORK_TREE" was the advice ``_hooklib.py`` and
``run_worked_examples.py`` printed. Measured in a sandbox replica
(``git rev-parse --local-env-vars`` identical on git 2.43.0 and
2.53.0.windows.2): an inherited ``GIT_DIR``, ``GIT_INDEX_FILE``,
``GIT_OBJECT_DIRECTORY`` or ``GIT_COMMON_DIR`` each moved a sentinel repository
from a fresh temp directory, and ``GIT_CONFIG`` redirected ``git config``
without ``--local``.

WHY IT LIVES IN ``tests/`` AND NOT IN ``tools/hooks/_hooklib.py``
------------------------------------------------------------------
``python/pyproject.toml``'s ``sdist.include`` ships ``tests/**`` and does NOT
ship ``tools/``. A suite guard that loaded its list from ``tools/`` would find
nothing in an sdist-installed cell and scrub nothing there, silently. This file
is reachable from both sides: ``tests/conftest.py`` imports the guard beside
it, and ``tools/hooks/_hooklib.py`` (present only in a repository checkout,
where ``tests/`` is always present too) loads THIS file by path and re-exports
it. The import has no side effects; the scrub of ``os.environ`` happens only in
``tests/_git_env_guard.py``.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Dict, List, MutableMapping, Optional, Sequence

#: ``git rev-parse --local-env-vars`` — git's OWN list of repository-local
#: variables, printed identically by git 2.43.0 (WSL2) and 2.53.0.windows.2 at
#: rc473. ``tests/test_git_env_cannot_reach_a_repository_rc473.py`` pins that
#: this tuple is a superset of what the RUNNING git prints, so a future git
#: that adds a name goes red rather than leaking.
GIT_LOCAL_ENV_VARS = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT", "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE", "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX",
    "GIT_SHALLOW_FILE", "GIT_COMMON_DIR",
)

#: Not on git's list, but each redirects where a write lands (a namespace
#: prefix on refs, or which global / system config file ``git config`` edits).
GIT_WRITE_REDIRECT_ENV = ("GIT_NAMESPACE", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM")

#: THE SSoT: every name :func:`scrub` removes, apart from the numbered
#: ``GIT_CONFIG_KEY_<n>`` / ``GIT_CONFIG_VALUE_<n>`` family it removes by prefix.
#: ``GIT_CEILING_DIRECTORIES`` is deliberately NOT here: it only NARROWS
#: discovery and never redirects a write, and removing an operator's ceiling
#: re-opens discovery of an unrelated repository above a tree (WSL2 carries one
#: at ``$HOME/.git``). A fixture that wants its own ceiling pins it itself.
GIT_REPO_LOCAL_ENV = GIT_LOCAL_ENV_VARS + GIT_WRITE_REDIRECT_ENV

_NUMBERED_CONFIG_PREFIXES = ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")


def scrub(environ: MutableMapping[str, str]) -> Dict[str, str]:
    """Remove every repository-selecting git variable from ``environ``.

    Mutates ``environ`` in place and returns what it removed, name to value,
    so a caller can report it. Nothing else in ``environ`` is touched — a child
    git that cannot find its own executable proves nothing.
    """
    removed: Dict[str, str] = {}
    for name in GIT_REPO_LOCAL_ENV:
        if name in environ:
            removed[name] = environ.pop(name)
    for name in [k for k in list(environ) if k.startswith(_NUMBERED_CONFIG_PREFIXES)]:
        removed[name] = environ.pop(name)
    return removed


def scrubbed(base: Optional[MutableMapping[str, str]] = None) -> Dict[str, str]:
    """A COPY of ``base`` (default ``os.environ``) with :func:`scrub` applied."""
    env = dict(os.environ if base is None else base)
    scrub(env)
    return env


# ── the worktree pointer, read per invocation ──────────────────────────────

_POINTER = re.compile(r"^\s*gitdir:\s*(?P<target>.+?)\s*$")
_WINDOWS_ABSOLUTE = re.compile(r"^(?P<drive>[A-Za-z]):[\\/](?P<rest>.*)$")


def pointer_git_args(pointer_text: str, checkout: str,
                     exists: Callable[[str], bool]) -> List[str]:
    """THE DECIDER, pure: the args a git needs to read ``checkout``, or ``[]``.

    ``pointer_text`` is the content of the checkout's ``.git`` FILE. The answer
    is non-empty in exactly one case: the pointer names an absolute WINDOWS
    path (``D:/...``) that does not exist on this host while its WSL mount twin
    (``/mnt/d/...``) does — the geometry in which WSL git exits 128 with
    ``fatal: not a git repository``. Then the twin is handed to that ONE
    invocation as ``--git-dir`` with the checkout as ``--work-tree``; nothing is
    exported, so a child git with another working directory is unaffected.

    Every other shape answers ``[]`` and git's own discovery is left alone: a
    pointer whose target exists as written (Windows git on a Windows worktree),
    a relative pointer, a non-Windows absolute path, or a twin that is absent.
    ``exists`` is injected so both directions are testable on any host.
    """
    first = pointer_text.splitlines()[0] if pointer_text else ""
    match = _POINTER.match(first)
    if match is None:
        return []
    target = match.group("target")
    if exists(target):
        return []
    win = _WINDOWS_ABSOLUTE.match(target)
    if win is None:
        return []
    twin = "/mnt/%s/%s" % (win.group("drive").lower(),
                           win.group("rest").replace("\\", "/"))
    if not exists(twin):
        return []
    return ["--git-dir=" + twin, "--work-tree=" + str(checkout)]


def _ceilings(environ: Optional[MutableMapping[str, str]] = None) -> List[Path]:
    raw = (os.environ if environ is None else environ).get("GIT_CEILING_DIRECTORIES", "")
    out: List[Path] = []
    for part in raw.split(os.pathsep):
        if part.strip():
            try:
                out.append(Path(part).resolve())
            except OSError:
                continue
    return out


def git_location_args(start: "os.PathLike[str] | str",
                      environ: Optional[MutableMapping[str, str]] = None,
                      exists: Callable[[str], bool] = os.path.exists) -> List[str]:
    """``--git-dir`` / ``--work-tree`` for the checkout ``start`` is in, or ``[]``.

    Walks up from ``start`` the way git's discovery does, stopping before any
    ``GIT_CEILING_DIRECTORIES`` entry. The first ``.git`` found decides: a
    directory answers ``[]`` (git reads it), a pointer FILE is handed to
    :func:`pointer_git_args`. Reads files only — it never runs git and never
    touches the environment.

    The first ``.git`` DIRECTORY ends the walk. A repository nested inside a
    worktree checkout (a test fixture under a WSL-read checkout) is its own
    repository, and handing its git the outer checkout's pointer twin would
    answer for a repository other than its own. ``exists`` is the pointer
    decider's, injected (rc473 final repair 1, `#T1188`) so a test can put a
    pointer checkout whose twin "exists" ABOVE a real repository on any host
    and see the walk stop.
    """
    try:
        here = Path(start).resolve()
    except OSError:
        return []
    ceilings = _ceilings(environ)
    for directory in (here, *here.parents):
        if directory in ceilings:
            return []
        dotgit = directory / ".git"
        if dotgit.is_dir():
            return []
        if dotgit.is_file():
            try:
                text = dotgit.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return []
            return pointer_git_args(text, str(directory), exists)
    return []


def git_argv(start: "os.PathLike[str] | str", args: Sequence[str],
             exe: str = "git") -> List[str]:
    """``[exe, *git_location_args(start), *args]`` — the one spelling callers use."""
    return [exe, *git_location_args(start), *args]
