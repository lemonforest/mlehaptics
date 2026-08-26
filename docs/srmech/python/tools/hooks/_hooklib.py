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

⚠️ THE GIT A HOOK RUNS IS PART OF ITS ANSWER (rc455, `#T1169`)
==============================================================
``git status --porcelain`` IS NOT A PLATFORM-INDEPENDENT QUESTION on this
checkout, and two shipped hooks were reading it as though it were. Measured at
rc454 on ONE tree at ONE commit, with the worktree clean:

===========================================================  ==========  =======
query                                                        Windows git  WSL git
===========================================================  ==========  =======
``status --porcelain -- python/README.md CHANGELOG.md``               0        2
``status --porcelain -- docs/srmech/python/srmech``                   0      324
``derived_ledger_freshness.py`` exit status                           0        2
===========================================================  ==========  =======

The cause is not a bug in either git. This checkout has ``core.autocrlf=true``
in the *Windows user's* global config: the index blobs are LF, the working
files are CRLF (``git ls-files --eol`` reports ``i/lf  w/crlf`` for every one),
and the conversion that reconciles them lives in a config WSL git does not
read — different ``HOME``. So WSL git compares LF against CRLF and honestly
reports every text file modified. ``derived_ledger_freshness`` then declared
**266** modules changed and blocked all 581 ledger rows, on a tree where nothing
had been edited. *(That count read 263 in three places until the verification
pass. Predicate, so it is re-measurable without WSL: the DISTINCT results of
``derived_ledger_freshness._module_of`` over the tracked ``.py`` files under
``docs/srmech/python/srmech``, since under WSL git every one of them reports
modified. Two independent routes agree on 266 — the hook's own block message
enumerates 8 modules then says "(+258 more)", and ``git ls-files`` gives 266
tracked ``.py`` mapping to 266 distinct modules.)*

**Windows git is the authority for this checkout**, and the reason is not
preference: the worktree's own ``.git`` file holds ``gitdir:
D:/GitHub/mlehaptics/.git/worktrees/...``, a Windows path, so WSL git cannot
open this worktree at all without ``GIT_DIR``/``GIT_WORK_TREE`` overrides. The
git that owns the checkout is the git that can read it.

Pinning the binary alone would be brittle — a hook must still give the right
answer under a WSL agent, which is the standing build-subagent environment.
So the fix is at the QUERY: :func:`dirty_paths` asks git for the change in
CONTENT rather than in bytes-on-disk, via
``git diff HEAD --numstat --ignore-cr-at-eol``, keeping only rows whose
added/deleted counts are not both zero. Measured on the same tree, same
commit, both gits: 0 / 0 / 0 for the three queries above, and — the half that
matters, because an instrument that cannot return otherwise is not a
measurement — BOTH gits report ``2  0  tools/hooks/README.md`` for one real
planted two-line addition, while Windows ``status`` reported 1 file and WSL
``status`` reported 12 for that same state.

:data:`HOOK_GIT_ENV` remains as the explicit pin for anyone who needs it, and
:func:`describe_env` prints which git and which interpreter actually answered.
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


#: Explicit pin for the git binary a hook shells out to. Absent, ``git`` is
#: resolved from PATH — which is the ordinary case and is CORRECT, because
#: :func:`dirty_paths` is EOL-independent by construction. Set this only when
#: you need to force a specific binary (e.g. running WSL tooling against a
#: Windows checkout and wanting the checkout's own git to answer).
HOOK_GIT_ENV = "SRMECH_HOOK_GIT"


def git_exe() -> str:
    return os.environ.get(HOOK_GIT_ENV) or "git"


def git(args: Sequence[str], cwd: Path, timeout: float = 30.0) -> Tuple[int, str]:
    return run([git_exe(), *args], cwd=cwd, timeout=timeout)


def python_exe() -> str:
    """The interpreter to re-enter with. ``sys.executable`` keeps a hook on the
    same Python the harness launched it with, which avoids the classic
    python/python3 split on Windows."""
    return sys.executable or "python3"


# ── EOL-INDEPENDENT git queries (see the module docstring) ────────────────

def dirty_paths(root: Path, paths: Sequence[str]) -> List[str]:
    """Repo-relative paths under ``paths`` whose CONTENT differs from HEAD.

    Staged and unstaged alike (the diff is against ``HEAD``, not the index),
    plus untracked-and-not-ignored files. A file whose only difference is its
    line terminator is NOT dirty — that is the whole point, and it is git's own
    judgement via ``--ignore-cr-at-eol``, not a heuristic of ours.

    Binary files report ``-`` for both counts; those are kept, because a binary
    difference is never EOL noise.
    """
    out_paths: List[str] = []
    code, out = git(["diff", "HEAD", "--numstat", "--ignore-cr-at-eol", "--",
                     *paths], cwd=root)
    if code == 0:
        for line in out.splitlines():
            parts = line.rstrip().split("\t")
            if len(parts) < 3:
                continue
            adds, dels, path = parts[0], parts[1], parts[-1]
            if adds == "0" and dels == "0":
                continue                      # EOL-only: not a content change
            out_paths.append(path.strip().strip('"'))
    code, out = git(["ls-files", "--others", "--exclude-standard", "--",
                     *paths], cwd=root)
    if code == 0:
        out_paths.extend(l.strip() for l in out.splitlines() if l.strip())
    return out_paths


def tracked_files(root: Path, paths: Sequence[str]) -> List[str]:
    """Repo-relative paths git has in the index under ``paths``.

    Index membership is EOL-agnostic — measured identical (151 entries for
    ``c/src`` + ``c/include``) under both gits — so this is safe to build a
    scan population from.
    """
    code, out = git(["ls-files", "--", *paths], cwd=root)
    if code != 0:
        return []
    return [l.strip().strip('"') for l in out.splitlines() if l.strip()]


def eol_noise(root: Path, paths: Sequence[str]) -> Tuple[int, int]:
    """``(porcelain_count, content_count)`` for the same pathspec.

    The canary. When these differ wildly the running git disagrees with the
    checkout's EOL policy, and any hook keyed on ``status --porcelain`` is
    about to false-fire. Reported by :func:`describe_env`; never used to
    decide a verdict, because :func:`dirty_paths` already answers correctly.
    """
    code, out = git(["status", "--porcelain", "--", *paths], cwd=root)
    porcelain = len([l for l in out.splitlines() if l.strip()]) if code == 0 else -1
    return porcelain, len(dirty_paths(root, paths))


# ── pytest summary parsing — a SKIP IS NOT A PASS ─────────────────────────

_COUNT_RE = None


def pytest_counts(output: str) -> Dict[str, int]:
    """Parse pytest's terminal summary into ``{passed, failed, error, skipped,
    xfailed, ...}``.

    Exists because **exit status alone cannot tell a green run from a vacuous
    one**. Measured at rc454, the same four prose gates on the same tree:
    ``55 passed, 1 skipped`` under Windows (no compiled ``srmech.dll``) and
    ``56 passed, 0 skipped`` under WSL2 (the ``.so`` loads). Both exit 0. A
    hook that reads only the status reports the first as "all green" while one
    assertion never ran.
    """
    global _COUNT_RE
    if _COUNT_RE is None:
        import re
        _COUNT_RE = re.compile(
            r"(\d+)\s+(passed|failed|error|errors|skipped|xfailed|xpassed|deselected)")
    counts: Dict[str, int] = {}
    for line in output.strip().splitlines()[::-1]:
        if "passed" not in line and "failed" not in line and "error" not in line \
                and "skipped" not in line and "no tests ran" not in line:
            continue
        for n, what in _COUNT_RE.findall(line):
            key = "error" if what == "errors" else what
            counts[key] = counts.get(key, 0) + int(n)
        if counts:
            break
    return counts


# ── Python literal masking (a mention is not a call) ──────────────────────

def mask_python_literals(text: str) -> Tuple[str, bool]:
    """``(masked_text, exact)`` — string literals and comments blanked.

    Returns ``exact=False`` when the text could not be tokenised (a fragment,
    or a half-written file). Callers must compare only maskings of the SAME
    exactness, because a degraded mask and an exact one are not commensurable.

    Why it exists: the difference between ``hashlib.sha256(x)`` and a docstring
    that SAYS ``hashlib.sha256(x)`` is the whole difference between a violation
    and the documentation warning you off it.

    ⚠️ **THIS DOCSTRING USED TO QUOTE THE RAW CENSUS, AND THE SENTENCE
    FALSIFIED ITSELF.** It read "the raw substring appears in **38** files, of
    which **23 are outside the shipped package**" — flatly, with no anchor —
    while the live ``sha256_routing_gate.py --selftest`` on the same tree
    printed **40 / 25**, and ``tools/hooks/README.md`` predicted a third
    number. The cause is that this very paragraph contains the substring, so
    the file enrols ITSELF in the population it is describing; ``comm`` named
    the two additions as ``tools/hooks/_hooklib.py`` (this file) and
    ``tools/hooks/check_hooks.py``. A self-referential count cannot be pinned
    by restating it, so it is no longer restated here.

    The number that IS stable and IS gated: after masking and scoping,
    **1** file holds a real call site — ``srmech/amsc/format.py``, the
    sanctioned fallback implementation itself. ``check_hooks.py`` asserts that
    one as a vacuity check. For the raw census, with both anchors and the delta
    named, run ``python tools/hooks/sha256_routing_gate.py --selftest``.
    """
    import io
    import tokenize
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except Exception:
        # Degraded: blank whole-line ``#`` comments only. Enough to keep a
        # before/after comparison honest; never presented as exact.
        out = []
        for line in text.splitlines(keepends=True):
            stripped = line.lstrip()
            out.append(" " * len(line.rstrip("\r\n")) + line[len(line.rstrip("\r\n")):]
                       if stripped.startswith("#") else line)
        return "".join(out), False
    buf = list(text.splitlines(keepends=True))
    interesting = {tokenize.STRING, tokenize.COMMENT}
    fstring_mid = getattr(tokenize, "FSTRING_MIDDLE", None)
    if fstring_mid is not None:
        interesting.add(fstring_mid)
    for tok in toks:
        if tok.type not in interesting:
            continue
        (sr, sc), (er, ec) = tok.start, tok.end
        for r in range(sr, min(er, len(buf)) + 1):
            if r - 1 >= len(buf):
                break
            line = buf[r - 1]
            a = sc if r == sr else 0
            b = ec if r == er else len(line)
            b = min(b, len(line))
            if b > a:
                buf[r - 1] = line[:a] + (" " * (b - a)) + line[b:]
    return "".join(buf), True


def describe_env(root: Path, probe_paths: Sequence[str] = ()) -> List[str]:
    """One block naming the interpreter, the git, and the EOL verdict.

    Printed by every hook's ``--selftest``. A hook that gives different answers
    on two machines must be able to say WHICH machine it thinks it is on.
    """
    code, ver = git(["--version"], cwd=root)
    _, crlf = git(["config", "--get", "core.autocrlf"], cwd=root)
    lines = [
        f"interpreter : {sys.executable}  ({sys.version.split()[0]})",
        f"git binary  : {git_exe()}  -> {ver.strip() or '(not runnable)'}",
        f"core.autocrlf: {crlf.strip() or '(unset)'}",
        f"repo root   : {root}",
    ]
    if probe_paths:
        porcelain, content = eol_noise(root, probe_paths)
        lines.append(
            f"dirty probe : status --porcelain says {porcelain}, "
            f"content-diff says {content}"
            + ("   <- EOL NOISE: this git disagrees with the checkout"
               if porcelain > content else ""))
    return lines


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
