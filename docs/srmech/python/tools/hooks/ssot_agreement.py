"""Stop / SubagentStop / PreToolUse(Bash: git commit) — the version and ABI
SSoT surfaces must agree. (rc452, `#T1166`)

WHAT IT CATCHES, WITH A SIX-LAG MEASURED HISTORY
================================================
The SSoT-lag class. ``docs/srmech/CLAUDE.md``'s ABI line enumerates its own
record: it "said 12 until rc420, 13 until rc425, 14 until rc438, 15 until rc439
and 16 until rc442 — one bump behind on each occasion", then rc447 made a sixth
and rc448 shipped over it, leaving it TWO bumps behind. ``c/README.md`` read
**3** from the v0.5.0 era until rc442 — fourteen bumps stale — under a note
saying "No gate covers c/README.md at all, which is exactly why it drifted the
furthest", and then drifted again five rcs later. On the version side, the
count of files that must agree was itself wrong: the orientation doc "said FOUR
until rc358".

⚠️ THIS HOOK BLOCKS ON THE TREE AS IT STANDS AT rc452. That is not a
contrived fixture. ``docs/srmech/python/README.md`` line 162 still reads
"**ABI 21** at this release" while ``SRMECH_ABI_VERSION`` is **22**, because
this rc's 21 -> 22 bump did not carry the prose. That README is the PyPI
long-description, so the false statement is shipped text. The existing gate
``tests/test_readme_currency_rc419.py`` is red on it (3 failed / 2 passed) —
this hook's contribution is not detection-where-there-was-none, it is moving
the detection to the moment of committing or stopping rather than a 27-minute
sweep the agent may run afterwards, or not at all.

THE NINE SURFACES
=================
FIVE version files (ADR-0007 §2.1 is the SSoT for this list):
  1. python/pyproject.toml
  2. python/pyproject-pure.toml
  3. python/srmech/version.py
  4. c/include/srmech.h            (SRMECH_VERSION)
  5. python/tests/test_signal_processing_scaffolding.py   (the literal pin)

FOUR ABI surfaces:
  6. c/include/srmech.h            (SRMECH_ABI_VERSION — the macro SSoT)
  7. python/srmech/_native/__init__.py  (EXPECTED_ABI_VERSION)
  8. docs/srmech/CLAUDE.md         "C ABI version is currently **N**"
  9. docs/srmech/c/README.md       "C ABI version is **N**"
 10. python/README.md              "(**ABI N** at this release"

Surfaces 8 and 9 are covered by ``test_abi_prose_currency_rc449``; 10 by
``test_readme_currency_rc419``. This hook reads all of them by regex in one
pass so that a disagreement is named at commit time in under a second, rather
than found by whichever gate happens to run.

WHAT IT DOES NOT DO
===================
It does not run a test, import ``srmech``, or judge prose for meaning. It
asserts one decidable thing per surface — the integer or version string these
sentences state — because that is the claim that keeps going wrong. A file that
is absent is reported as absent and skipped, never guessed at.

An ABI bump is NOT a version bump: the five version files stay put across one.
The two families are therefore checked independently and reported separately.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

Finding = Tuple[str, str]          # (surface label, value or "<absent>")

_VERSION_SURFACES: Tuple[Tuple[str, str, str], ...] = (
    ("python/pyproject.toml", "docs/srmech/python/pyproject.toml",
     r'(?m)^\s*version\s*=\s*"([^"]+)"'),
    ("python/pyproject-pure.toml", "docs/srmech/python/pyproject-pure.toml",
     r'(?m)^\s*version\s*=\s*"([^"]+)"'),
    ("python/srmech/version.py", "docs/srmech/python/srmech/version.py",
     r'__version__\s*[:=]\s*"([^"]+)"'),
    ("c/include/srmech.h", "docs/srmech/c/include/srmech.h",
     r'#define\s+SRMECH_VERSION\s+"([^"]+)"'),
    ("tests/test_signal_processing_scaffolding.py",
     "docs/srmech/python/tests/test_signal_processing_scaffolding.py",
     r'srmech\.__version__\s*==\s*"([^"]+)"'),
)

_ABI_SURFACES: Tuple[Tuple[str, str, str], ...] = (
    ("c/include/srmech.h (macro SSoT)", "docs/srmech/c/include/srmech.h",
     r'#define\s+SRMECH_ABI_VERSION\s+(\d+)'),
    ("srmech/_native/__init__.py", "docs/srmech/python/srmech/_native/__init__.py",
     r'EXPECTED_ABI_VERSION\s*:\s*int\s*=\s*(\d+)'),
    ("docs/srmech/CLAUDE.md", "docs/srmech/CLAUDE.md",
     r'C ABI version is currently \*\*(\d+)\*\*'),
    ("docs/srmech/c/README.md", "docs/srmech/c/README.md",
     r'C ABI version is \*\*(\d+)\*\*'),
    ("docs/srmech/python/README.md (PyPI long-description)",
     "docs/srmech/python/README.md",
     r'\*\*ABI (\d+)\*\* at this release'),
)


def _read_first(root: Path, rel: str, pattern: str) -> Optional[str]:
    p = root / rel
    if not p.is_file():
        return None
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _survey(root: Path,
            surfaces: Tuple[Tuple[str, str, str], ...]) -> List[Finding]:
    out: List[Finding] = []
    for label, rel, pat in surfaces:
        v = _read_first(root, rel, pat)
        if v is not None:
            out.append((label, v))
    return out


def _disagreement(found: List[Finding]) -> Optional[Tuple[str, List[Finding]]]:
    """Return (majority_value, odd_ones_out) when the surfaces disagree."""
    if len(found) < 2:
        return None
    counts: Dict[str, int] = {}
    for _, v in found:
        counts[v] = counts.get(v, 0) + 1
    if len(counts) == 1:
        return None
    majority = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
    odd = [(lbl, v) for lbl, v in found if v != majority]
    return majority, odd


def _is_commit(payload: Dict[str, Any]) -> bool:
    cmd = H.bash_command(payload)
    if not cmd:
        return False
    for seg in H.split_segments(cmd):
        args = H.leading_git_args(seg)
        if args and "commit" in args:
            return True
    return False


def body(payload: Dict[str, Any]) -> int:
    event = payload.get("hook_event_name") or ""
    if event == "PreToolUse" and not _is_commit(payload):
        return H.allow()
    if event in ("Stop", "SubagentStop") and H.stop_is_repeat(payload):
        return H.allow([
            "[ssot-agreement] WARNING: stop_hook_active — allowing this stop "
            "without re-checking the version/ABI surfaces."])

    root = H.repo_root()
    problems: List[str] = []

    for family, surfaces, note in (
        ("VERSION", _VERSION_SURFACES,
         "All five must carry the same string (ADR-0007 §2.1)."),
        ("ABI", _ABI_SURFACES,
         "c/include/srmech.h is the macro SSoT; every other surface must match it."),
    ):
        found = _survey(root, surfaces)
        if not found:
            continue
        d = _disagreement(found)
        if d is None:
            continue
        majority, odd = d
        problems.append(f"{family} surfaces disagree — {len(found)} read, "
                        f"{len(odd)} out of step (majority {majority!r}). {note}")
        for lbl, v in odd:
            problems.append(f"    ODD ONE OUT: {lbl} says {v!r}, expected {majority!r}")

    if not problems:
        return H.allow()

    return H.block([
        "BLOCKED (ssot-agreement): a version/ABI SSoT surface is out of step.",
        *problems,
        "",
        "Fix the odd file out, not the majority — unless the majority is the "
        "stale side, in which case say so explicitly and fix all of them.",
        "An ABI bump is NOT a version bump: the five version files stay put "
        "across a 21 -> 22 move, and the ABI prose surfaces must move WITH it, "
        "in the same commit.",
    ])


if __name__ == "__main__":
    H.run_hook(body)
