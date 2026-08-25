"""PreToolUse(Bash) — refuse a stage-everything in a repo where that is never
correct. (rc452, `#T1166`)

WHAT IT CATCHES, MEASURED
=========================
``git status --porcelain -uall`` on this tree returns **36,833** entries
(measured 2026-08-24). ``--porcelain`` without ``-uall`` collapses untracked
directories and reports only 38 lines, which is why the hazard reads smaller
than it is — but ``git add -A`` expands them, so 36,833 is the number that
would land in the index. Among the collapsed directories are
``docs/srmech/build-msvc/`` and ``docs/srmech/build-ped/``, which the standing
brief says explicitly must NEVER be committed, plus ``node_modules/``, ``bin/``
and ``lib/``.

The pressure that makes a hasty stage-all likely is documented too: a prior
3h34m run died on a weekly quota limit with everything uncommitted, so the
standing advice is to commit incrementally — and "commit incrementally" plus
"36k untracked files" is exactly the combination that produces a reflexive
``git add -A``.

WHAT IS AND IS NOT BLOCKED
==========================
BLOCKED: ``git add -A``, ``git add --all``, ``git add .``, ``git add :/``, and
``git commit -a`` / ``-am`` (which stages every tracked modification without
review).

NOT blocked, and this matters for the false-positive rate:

* ``git add <explicit paths>`` — the desired behavior.
* ``git add -u`` — updates TRACKED files only. It cannot sweep an untracked
  file, so it is not this hazard, and blocking it would be the kind of
  over-reach that gets a hook disabled.
* ``echo "git add -A"`` / ``grep 'git commit -a' f`` — the segment must INVOKE
  git, not merely mention it.

COST
====
Regex and string handling only. No filesystem or git I/O — the 36,833 figure is
a recorded measurement, not a live count, precisely so this hook stays free.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

#: Measured 2026-08-24 with ``git status --porcelain -uall | wc -l``.
UNTRACKED_MEASURED = 36833

#: ``git add`` flags that mean "everything".
ADD_ALL_FLAGS = {"-A", "--all", "--no-ignore-removal"}

#: Path arguments that mean "the whole tree" from any cwd.
ADD_ALL_PATHS = {".", "./", ":/", "*"}


def _offence(args: List[str]) -> Optional[str]:
    """Return a human reason if this git argv is a stage-everything, else None."""
    if not args:
        return None
    # Skip global options like -C <dir> / -c k=v so `git -C x add -A` resolves.
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] in ("-C", "-c", "--git-dir", "--work-tree"):
            i += 2
            continue
        i += 1
    if i >= len(args):
        return None
    sub = args[i]
    rest = args[i + 1:]

    if sub == "add":
        for a in rest:
            if a in ADD_ALL_FLAGS:
                return f"`git add {a}` stages every untracked file"
            if a in ADD_ALL_PATHS:
                return f"`git add {a}` stages the whole tree from here"
            # bundled short flags, e.g. -Av
            if (a.startswith("-") and not a.startswith("--")
                    and "A" in a[1:] and a[1:].isalpha()):
                return f"`git add {a}` bundles -A, which stages every untracked file"
        return None

    if sub == "commit":
        for a in rest:
            if a in ("-a", "--all"):
                return f"`git commit {a}` stages every tracked modification unreviewed"
            if (a.startswith("-") and not a.startswith("--")
                    and "a" in a[1:] and a[1:].isalpha()):
                return f"`git commit {a}` bundles -a, staging every tracked modification"
        return None

    return None


def body(payload: Dict[str, Any]) -> int:
    cmd = H.bash_command(payload)
    if not cmd:
        return H.allow()

    for seg in H.split_segments(cmd):
        args = H.leading_git_args(seg)
        if args is None:
            continue
        why = _offence(args)
        if why is None:
            continue
        return H.block([
            f"BLOCKED (git-add-all-blocker): {why}.",
            f"This repo has {UNTRACKED_MEASURED:,} untracked/changed entries "
            "(measured 2026-08-24), including docs/srmech/build-msvc/ and "
            "docs/srmech/build-ped/, which must never be committed.",
            "",
            "Stage explicit paths instead — list the files you actually changed:",
            "    git add docs/srmech/python/srmech/<file>.py docs/srmech/c/src/<file>.c",
            "",
            "`git add -u` is fine if you want every TRACKED modification: it "
            "cannot sweep an untracked file, and this hook does not block it.",
        ])

    return H.allow()


if __name__ == "__main__":
    H.run_hook(body)
