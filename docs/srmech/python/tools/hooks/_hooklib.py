"""Shared plumbing for the srmech Claude Code hooks (rc452, `#T1166`).

THE CONTRACT THESE SCRIPTS IMPLEMENT
====================================
A Claude Code hook is handed one JSON object on **stdin** and answers with an
**exit status**:

* ``0`` — allow. Anything on stdout is informational.
* ``2`` — BLOCK. stderr is fed back to the model as the reason.
* anything else — non-blocking error; the harness warns and continues.

Every hook here therefore has exactly two interesting outcomes, and every one
of them is exercised in both directions by ``check_hooks.py``.

WHY THE WRAPPER FAILS **OPEN** ON AN INTERNAL ERROR
===================================================
:func:`run_hook` catches any exception the hook body raises and exits ``0``
with a loud stderr note. This is deliberate and it is the one place the
"strictness" argument loses:

    a hook that crashes blocks EVERY stop or EVERY Bash call, and a hook that
    blocks legitimate work gets disabled within a day — which is strictly
    worse than no hook.

The distinction is between an INFRASTRUCTURE failure (a missing file, a
tempfile race, a git binary that is not there) and a MEASUREMENT failure (the
gate ran and was red). Infrastructure failures fail open. Measurement failures
fail closed — that is the whole point, and no ``except`` clause covers them,
because the hook bodies return a verdict rather than raising one.

REPO-ROOT RESOLUTION, AND WHY IT IS AN ENV VAR
==============================================
``CLAUDE_PROJECT_DIR`` is the harness's own documented variable. Honoring it is
not a test backdoor — it is the supported way a hook learns where the project
is, and it is what lets ``check_hooks.py`` point a hook at a purpose-built
fixture tree instead of mutating the real repo. When it is absent the root is
derived from this file's location, which is the ordinary interactive case.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

#: This file lives at ``<repo>/docs/srmech/python/tools/hooks/_hooklib.py``.
#: parents: [0]=hooks [1]=tools [2]=python [3]=srmech [4]=docs [5]=<repo>
_FALLBACK_ROOT = Path(__file__).resolve().parents[5]

BLOCK = 2
ALLOW = 0


# ── repo geography ────────────────────────────────────────────────────────

def repo_root() -> Path:
    """The project root, honoring the harness's ``CLAUDE_PROJECT_DIR``."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return _FALLBACK_ROOT


def py_root(root: Optional[Path] = None) -> Path:
    return (root or repo_root()) / "docs" / "srmech" / "python"


def c_root(root: Optional[Path] = None) -> Path:
    return (root or repo_root()) / "docs" / "srmech" / "c"


# ── stdin payload ─────────────────────────────────────────────────────────

def read_payload() -> Dict[str, Any]:
    """Parse the hook's stdin JSON. An unreadable payload is an empty dict —
    every hook body must treat missing keys as "not my case" and allow."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        obj = json.loads(raw)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def bash_command(payload: Dict[str, Any]) -> str:
    """The command string for a PreToolUse(Bash) event; ``""`` otherwise."""
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        return ""
    cmd = ti.get("command")
    return cmd if isinstance(cmd, str) else ""


def target_file(payload: Dict[str, Any]) -> str:
    """The edited path for Edit / Write / NotebookEdit; ``""`` otherwise."""
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        return ""
    for key in ("file_path", "notebook_path"):
        v = ti.get(key)
        if isinstance(v, str) and v:
            return v
    return ""


def stop_is_repeat(payload: Dict[str, Any]) -> bool:
    """True when this Stop is itself the result of a previous hook block.

    Consulting this is what bounds a Stop hook to exactly ONE block instead of
    an infinite "you are not done" loop.
    """
    return bool(payload.get("stop_hook_active"))


# ── shelling out ──────────────────────────────────────────────────────────

def run(argv: Sequence[str], cwd: Path, timeout: float = 120.0,
        env_extra: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    """Run a command, returning ``(returncode, combined_output)``.

    A timeout returns ``(-1, ...)`` so callers can distinguish "the instrument
    did not finish" from "the instrument said no" — the two must never be
    collapsed, because only the second is evidence.
    """
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            list(argv), cwd=str(cwd), env=env, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
    except subprocess.TimeoutExpired:
        return -1, f"timed out after {timeout:.0f}s"
    except FileNotFoundError as exc:
        return -2, f"not runnable: {exc}"
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def git(args: Sequence[str], cwd: Path, timeout: float = 30.0) -> Tuple[int, str]:
    return run(["git", *args], cwd=cwd, timeout=timeout)


def python_exe() -> str:
    """The interpreter to re-enter with. ``sys.executable`` keeps a hook on the
    same Python the harness launched it with, which avoids the classic
    python/python3 split on Windows."""
    return sys.executable or "python3"


# ── verdicts ──────────────────────────────────────────────────────────────

def block(lines: Sequence[str]) -> int:
    for line in lines:
        print(line, file=sys.stderr)
    return BLOCK


def allow(lines: Sequence[str] = ()) -> int:
    for line in lines:
        print(line, file=sys.stderr)
    return ALLOW


def run_hook(body: Callable[[Dict[str, Any]], int]) -> None:
    """Entry point every hook script ends with. See the module docstring for
    why an internal exception exits 0 rather than 2."""
    try:
        payload = read_payload()
        code = body(payload)
    except Exception as exc:  # infrastructure failure — fail OPEN, loudly
        print(f"[srmech-hook] {Path(sys.argv[0]).name} failed open: "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(ALLOW)
    sys.exit(code)


# ── shell-command splitting (shared by the Bash-matching hooks) ───────────

_SEPARATORS = ("&&", "||", ";", "|", "\n")


def split_segments(command: str) -> List[str]:
    """Split a Bash command line into rough segments on ``&& || ; |`` and
    newlines.

    This is deliberately NOT a shell parser. It exists so that a hook matching
    ``git push`` also matches it in ``cd x && git push``, while a mention
    inside ``echo "git push"`` is filtered out later by requiring the segment
    to START with the program name.
    """
    parts = [command]
    for sep in _SEPARATORS:
        nxt: List[str] = []
        for chunk in parts:
            nxt.extend(chunk.split(sep))
        parts = nxt
    return [p.strip() for p in parts if p.strip()]


_ENV_PREFIX_OK = ("sudo", "env", "time", "nohup", "exec")


def leading_git_args(segment: str) -> Optional[List[str]]:
    """If ``segment`` INVOKES git, return its argument list; else ``None``.

    Requiring git to be the invoked program — not merely mentioned — is what
    keeps ``echo "git add -A"`` and ``grep 'git commit -a' f`` from firing.
    ``VAR=1 git add`` and ``sudo git add`` still resolve.
    """
    try:
        import shlex
        toks = shlex.split(segment, posix=True)
    except ValueError:
        toks = segment.split()
    i = 0
    while i < len(toks):
        t = toks[i]
        if "=" in t and not t.startswith("-") and t.split("=", 1)[0].isidentifier():
            i += 1
            continue
        if t in _ENV_PREFIX_OK:
            i += 1
            continue
        break
    if i >= len(toks):
        return None
    prog = Path(toks[i]).name
    if prog not in ("git", "git.exe"):
        return None
    return toks[i + 1:]
