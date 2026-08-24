"""PreToolUse(Bash: git push) — do not push an op-touching branch whose ripple
sweep has not been run at this commit. (rc452, `#T1166`)

WHAT IT CATCHES, MEASURED
=========================
This session's exact sequence. The standing instruction is "RUN
``tools/ripple_check.py`` BEFORE COMMITTING, not after" — the previous agent ran
it after, discovered 12 reds, and had to report them as residual. The
CHANGELOG's own OPEN section says the branch "must not be pushed as a closed
slice until they are". The sweep costs ~27 minutes, which is precisely why it
gets deferred past the moment it was supposed to gate.

THE DECIDABLE QUESTION
======================
``tools/hooks/ripple_stamp.py`` writes ``.git/srmech_ripple_stamp.json``
recording ``{sha, status}`` after a sweep. This hook requires
``stamp.sha == HEAD`` and ``stamp.status == 0`` whenever the outgoing commits
touch ``docs/srmech/python/srmech`` or ``docs/srmech/c/src``. A commit made
after the sweep invalidates the stamp — the sweep vouches for a tree, not for
an intention.

⚠️ THIS IS THE MOST INTRUSIVE HOOK HERE. SHIP IT LAST AND WATCH IT.
===================================================================
Its false-positive profile is genuinely MODERATE-HIGH and it collides with a
standing instruction rather than a mere convenience: quota discipline says
COMMIT AND PUSH INCREMENTALLY, because a prior 3h34m run died on a weekly limit
with everything uncommitted. A hook that forbids an incremental push would
trade a 27-minute cost for the risk of losing hours of work — a bad trade, and
one that would get it disabled within a day.

The ``[ripple-pending]`` token in the HEAD commit message is what reconciles
the two. It lets the push through and the hook ECHOES it. That converts a
silent omission into a recorded, greppable admission in history, which is the
actual goal: not to prevent un-swept pushes, but to prevent un-swept pushes
that PRESENT AS SWEPT.

If it turns out to be bypassed routinely, the documented narrowing is to fire
only on pushes whose head commit message claims closure — that is a one-line
change to :func:`_claims_closure`, left in place and unused for exactly that
reason.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

import ripple_stamp  # noqa: E402  (sibling module; stamp location SSoT)

OP_PATHS = ("docs/srmech/python/srmech", "docs/srmech/c/src")

PENDING_TOKEN = "[ripple-pending]"

#: Reserved for the documented narrowing described in the module docstring.
CLOSURE_WORDS = ("closes", "closed slice", "at zero", "final", "ready to merge")


def _is_push(payload: Dict[str, Any]) -> bool:
    cmd = H.bash_command(payload)
    if not cmd:
        return False
    for seg in H.split_segments(cmd):
        args = H.leading_git_args(seg)
        if args and "push" in args:
            return True
    return False


def _outgoing_files(root: Path) -> Optional[List[str]]:
    """Files in the commits this push would send, or None if undeterminable."""
    for ref in ("@{upstream}", "origin/main", "HEAD~1"):
        code, out = H.git(["rev-parse", "--verify", "--quiet", ref], cwd=root)
        if code != 0 or not out.strip():
            continue
        code, out = H.git(["diff", "--name-only", f"{ref}..HEAD"], cwd=root)
        if code == 0:
            return [l.strip() for l in out.splitlines() if l.strip()]
    return None


def _head_message(root: Path) -> str:
    code, out = H.git(["log", "-1", "--format=%B"], cwd=root)
    return out if code == 0 else ""


def _claims_closure(msg: str) -> bool:
    low = msg.lower()
    return any(w in low for w in CLOSURE_WORDS)


def body(payload: Dict[str, Any]) -> int:
    if not _is_push(payload):
        return H.allow()

    root = H.repo_root()
    files = _outgoing_files(root)
    if files is None:
        return H.allow([
            "[ripple-stamp] could not determine the outgoing commit range; "
            "allowing the push without a ripple check."])

    touching = [f for f in files if any(f.startswith(p) for p in OP_PATHS)]
    if not touching:
        return H.allow()

    msg = _head_message(root)
    if PENDING_TOKEN in msg:
        return H.allow([
            f"[ripple-stamp] {PENDING_TOKEN} found in the HEAD commit message — "
            "allowing an UNSWEPT push of "
            f"{len(touching)} op-touching file(s). This is now a recorded "
            "admission in history, not a silent omission. Run "
            "tools/hooks/ripple_stamp.py before presenting this branch as a "
            "closed slice."])

    code, head_out = H.git(["rev-parse", "HEAD"], cwd=root)
    head = head_out.strip() if code == 0 else ""

    sp = ripple_stamp.stamp_path(root)
    stamp: Dict[str, Any] = {}
    if sp.is_file():
        try:
            stamp = json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            stamp = {}

    if stamp.get("sha") == head and stamp.get("status") == 0 and head:
        return H.allow()

    if not stamp:
        why = f"no ripple stamp at {sp.relative_to(root)}"
    elif stamp.get("sha") != head:
        why = (f"the stamp is for {str(stamp.get('sha'))[:12]}, but HEAD is "
               f"{head[:12]} — commits were made after the sweep")
    else:
        why = (f"the recorded sweep FAILED (status {stamp.get('status')}"
               + (f", {stamp['failed']} gate(s) red" if stamp.get("failed") else "")
               + ")")

    return H.block([
        f"BLOCKED (ripple-stamp-before-push): {len(touching)} op-touching "
        f"file(s) are in this push and {why}.",
        f"  first touched: {', '.join(touching[:4])}"
        + (f" (+{len(touching) - 4} more)" if len(touching) > 4 else ""),
        "",
        "Run the sweep and stamp it (~27 min):",
        "    python3 tools/hooks/ripple_stamp.py",
        "",
        f"Or, if this is a deliberate incremental / work-in-progress push, put "
        f"{PENDING_TOKEN} in the HEAD commit message. The push then goes "
        "through and the un-swept state is RECORDED in history rather than "
        "silently assumed — which is the point. Quota discipline says commit "
        "and push incrementally; this hook is not trying to stop that.",
    ])


if __name__ == "__main__":
    H.run_hook(body)
