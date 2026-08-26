"""PreToolUse(Edit / Write / MultiEdit) — no NEW direct ``hashlib.sha256(...)``
call site may be added to the shipped package. (rc455, `#T1169`)

WHAT IT ENFORCES
================
``docs/srmech/CLAUDE.md``, Phase-B5 discipline: *"Do not introduce a new
``hashlib.sha256(...)`` direct call; route through
``format.sha256_bytes(...)``."* The reason is not style — ``sha256_bytes``
dispatches to native C (``srmech_sha256_hex``, or the SHA-NI single-stream peer
on hosts carrying the Intel SHA extensions), and a direct ``hashlib`` call
silently opts out of all of it while still returning the right answer. A silent
performance/dispatch regression with a correct result is exactly the class this
tree ranks worst, because nothing downstream can see it.

⚠️ THE FIRST DESIGN OF THIS HOOK WAS A FALSE-POSITIVE ENGINE. MEASURED.
=======================================================================
As scoped, it blocked any edit to a file CONTAINING ``hashlib.sha256``, with
allowances applied before scope.

**THE PREDICATE, because a count without one cannot be re-measured:** tracked
``.py`` files under ``docs/srmech/python`` whose text contains the substring
``hashlib.sha256``. Run it yourself with::

    git grep -l 'hashlib\\.sha256' HEAD -- 'docs/srmech/python/*.py' | wc -l

**AND THE FIGURE MOVES, SO IT IS PINNED TO A COMMIT RATHER THAN STATED FLATLY.**
Measured **at HEAD ``84270a8a2`` (rc454), before this slice's own files**:

  =================================================  ======  ==============
  design                                             blocks  true violations
  =================================================  ======  ==============
  as scoped (file CONTAINS the substring)                38               0
  ...of which OUT of package scope (tests/, tools/)      23               —
  **redesigned: scope first, literals masked,
  compare BEFORE vs AFTER**                          **0**           **0**
  =================================================  ======  ==============

⚠️ **An earlier draft of this table said 38/23 with no anchor and was already
false when it shipped**: the live ``--selftest`` on the same tree printed
**40 / 25**, and ``README.md`` predicted a third number, 39/24. Three readings
of one census. The cause is not drift over time but SELF-REFERENCE — a docstring
that documents this rule contains the substring, so it enrols itself in its own
population. ``comm`` names the two files exactly: ``tools/hooks/_hooklib.py``
and ``tools/hooks/check_hooks.py``, both written by this slice. Committing
``sha256_routing_gate.py`` itself moves it again.

So the first-design count is quoted ONLY with its commit, and **the live number
is not restated in prose anywhere** — :func:`selftest` prints it, at both
anchors, with the delta named. The one figure that is stable, load-bearing and
gated is the REDESIGNED column: exactly **1** file holds a real call site
(``srmech/amsc/format.py``, the sanctioned fallback), which ``check_hooks.py``
asserts as a vacuity check.

Every one of the 38 was a false positive, and the reason is what matters: inside
``srmech/`` the substring occurs **7 times in code-shaped text and 0 times as a
banned call**. Five are documentation *warning the reader off it*
(``_tool_docs.py``: *"WHAT YOU WOULD OTHERWISE WRONGLY HAND-ROLL:
hashlib.sha256(data).hexdigest()"*), and the remaining two are the sanctioned
fallback implementation in ``srmech/amsc/format.py`` — the one place that MUST
call hashlib, because it is what ``sha256_bytes`` falls back TO.

So the ordering the repair turns on: **scope is applied BEFORE allowances.** A
file outside ``srmech/`` is never examined at all, so 23 of the 38 stop at the
first branch and no allowance row is consulted for them. That ordering is the
difference between an allowance list that has to enumerate every test file that
ever hashes something, and one with a single entry.

THE PREDICATE — WHAT IS BEING ADDED, NOT WHAT IS ALREADY THERE
==============================================================
A ``PreToolUse`` payload carries the text about to be written
(``tool_input.new_string`` / ``.content`` / ``.edits``). So this hook SIMULATES
the edit, masks Python string literals and comments in the BEFORE and AFTER
text with the same masker, counts real call sites in each, and blocks only when
the count **increases**. Consequences worth naming:

* A file that already holds a call site can still be edited freely — the hook
  has no opinion about existing debt, which is what made the first design
  unusable.
* Writing *documentation* that mentions ``hashlib.sha256(...)`` is not a
  violation, because the mention lands inside a string literal or a comment and
  the mask removes it. That is not a carve-out; it is the difference the rule
  is actually about.
* A new file (Write, no prior content) is compared against an empty before, so
  a fresh module cannot smuggle one in.

FAIL-OPEN BOUNDARY
==================
If the edit cannot be reproduced (``old_string`` absent, an unknown tool shape,
a mask that degrades on one side only), the hook exits 0 with a note. It never
guesses: a guess in this direction blocks legitimate work, and a hook that
blocks legitimate work is disabled within a day.

COST
====
One file read plus two ``tokenize`` passes over a single module. Everything
outside ``srmech/`` exits at the ``_hooklib`` floor without reading anything.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

#: SCOPE, APPLIED FIRST. The shipped package only — ``tests/`` and ``tools/``
#: hash things legitimately and are not what the discipline binds.
SCOPE_REL = ("docs", "srmech", "python", "srmech")

#: ALLOWANCE, CONSULTED ONLY FOR IN-SCOPE FILES. Exactly one entry, and it is
#: the fallback ``sha256_bytes`` itself dispatches to.
ALLOWED = ("srmech/amsc/format.py",)

#: The banned CALL. Run over literal-masked text, so a mention is not a match.
CALL_RE = re.compile(r"\bhashlib\s*\.\s*sha256\s*\(")

OVERRIDE_ENV = "SRMECH_ALLOW_RAW_HASHLIB"


def _in_scope(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    n = len(SCOPE_REL)
    for i in range(len(parts) - n + 1):
        if parts[i:i + n] == list(SCOPE_REL):
            return True
    return False


def _rel_for_allowance(path: Path) -> str:
    parts = list(path.parts)
    for i in range(len(parts)):
        if [p.lower() for p in parts[i:i + 4]] == list(SCOPE_REL):
            return "/".join(parts[i + 3:])
    return path.name


def call_sites(text: str) -> Tuple[int, bool]:
    masked, exact = H.mask_python_literals(text)
    return len(CALL_RE.findall(masked)), exact


def simulate(payload: Dict[str, Any], before: str) -> Optional[str]:
    """The file text this tool call would produce, or ``None`` if unknowable."""
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        return None
    if isinstance(ti.get("content"), str):          # Write
        return ti["content"]

    edits: List[Dict[str, Any]] = []
    if isinstance(ti.get("edits"), list):           # MultiEdit
        edits = [e for e in ti["edits"] if isinstance(e, dict)]
    elif isinstance(ti.get("new_string"), str):     # Edit
        edits = [ti]
    if not edits:
        return None

    text = before
    for e in edits:
        old = e.get("old_string")
        new = e.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            return None
        if old == "":
            text = new + text
            continue
        if old not in text:
            return None                              # cannot reproduce — fail open
        text = text.replace(old, new) if e.get("replace_all") \
            else text.replace(old, new, 1)
    return text


def body(payload: Dict[str, Any]) -> int:
    tool = payload.get("tool_name") or ""
    if tool not in ("Edit", "Write", "MultiEdit"):
        return H.allow()
    raw = H.target_file(payload)
    if not raw or not raw.endswith(".py"):
        return H.allow()
    path = Path(raw)

    # ── SCOPE FIRST. 23 of the original 38 false positives stop here. ─────
    if not _in_scope(path):
        return H.allow()

    # ── ALLOWANCE SECOND, and it has exactly one row. ─────────────────────
    rel = _rel_for_allowance(path)
    if rel in ALLOWED:
        return H.allow([
            f"[sha256-routing] {rel} is the sanctioned hashlib fallback "
            "sha256_bytes dispatches to — not checked."])

    try:
        before = path.read_text(encoding="utf-8") if path.is_file() else ""
    except OSError as exc:
        return H.allow([f"[sha256-routing] cannot read {rel}: {exc}"])

    after = simulate(payload, before)
    if after is None:
        return H.allow([
            "[sha256-routing] could not reproduce this edit "
            f"({tool}) against {rel}; not checked."])

    n_before, exact_before = call_sites(before)
    n_after, exact_after = call_sites(after)
    if exact_before != exact_after:
        return H.allow([
            f"[sha256-routing] {rel}: one side of the comparison could not be "
            "tokenised, so before/after are not commensurable; not checked."])
    if n_after <= n_before:
        return H.allow()

    if os.environ.get(OVERRIDE_ENV) == "1":
        return H.allow([
            f"[sha256-routing] {OVERRIDE_ENV}=1 — BYPASSING: this edit adds "
            f"{n_after - n_before} direct hashlib.sha256(...) call site(s) to "
            f"{rel}, which silently opt out of the native SHA-256 dispatch."])

    return H.block([
        f"BLOCKED (sha256-routing): this edit adds {n_after - n_before} NEW "
        f"direct hashlib.sha256(...) call site(s) to {rel} "
        f"({n_before} -> {n_after}).",
        "",
        "Route it through the dispatching wrapper instead:",
        "    from srmech.amsc.format import sha256_bytes   # 64-char hex str",
        "    from srmech.amsc.format import sha256_raw     # raw 32 bytes",
        "    from srmech.amsc.format import sha256_batch   # N-way SIMD bulk",
        "",
        "WHY, and it is not style: sha256_bytes dispatches to native C "
        "(srmech_sha256_hex, or srmech_sha256_shani on hosts with the Intel "
        "SHA extensions). A direct hashlib call returns the SAME digest while "
        "silently opting out of that path — a correct answer at the wrong "
        "cost, which nothing downstream can detect.",
        "",
        "The one sanctioned direct call is srmech/amsc/format.py, which is what "
        "sha256_bytes falls back TO. Documentation that MENTIONS "
        "hashlib.sha256(...) is not blocked — string literals and comments are "
        "masked before counting.",
        "",
        f"Genuinely need a second one? {OVERRIDE_ENV}=1 bypasses and is echoed, "
        "or add the file to ALLOWED in this hook with a written rationale.",
    ])


def _head_census(root: Path) -> Tuple[int, int]:
    """``(blocked, out_of_scope)`` for the first design, measured at HEAD.

    The working-tree census moves whenever a file that DOCUMENTS this rule is
    edited — the substring enrols the documentation in its own population. Two
    anchors printed side by side make that legible instead of mysterious, and
    stop a reader concluding that one of the two numbers is a lie.
    """
    code, out = H.git(["grep", "-l", r"hashlib\.sha256", "HEAD", "--",
                       "docs/srmech/python/*.py"], cwd=root)
    if code != 0:
        return -1, -1
    rels = [l.strip()[5:] if l.strip().startswith("HEAD:") else l.strip()
            for l in out.splitlines() if l.strip()]
    return len(rels), len([r for r in rels
                           if not r.startswith("docs/srmech/python/srmech/")])


def selftest() -> int:
    """Census both designs over the tracked tree — the measurement that
    rejected the first one."""
    root = H.repo_root()
    for line in H.describe_env(root):
        print(line)
    print()
    print("PREDICATE (first design): tracked .py under docs/srmech/python whose")
    print("           text CONTAINS the substring 'hashlib.sha256'.")
    print()
    pyr = H.py_root(root)
    files = H.tracked_files(root, ("docs/srmech/python",))
    py = [f for f in files if f.endswith(".py")]
    as_scoped: List[str] = []
    in_scope = 0
    real: List[Tuple[str, int]] = []
    for rel in py:
        p = root / rel
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "hashlib.sha256" in text:
            as_scoped.append(rel)
        if not _in_scope(p):
            continue
        in_scope += 1
        n, _ = call_sites(text)
        if n:
            real.append((rel, n))
    out_of_scope = [f for f in as_scoped if not _in_scope(root / f)]
    h_blocked, h_out = _head_census(root)
    code, head_sha = H.git(["rev-parse", "--short=9", "HEAD"], cwd=root)
    head_sha = head_sha.strip().splitlines()[-1].strip() if code == 0 else "?"
    print(f"tracked .py under docs/srmech/python : {len(py)}")
    print(f"in the shipped-package SCOPE          : {in_scope}")
    print(f"AS SCOPED, at HEAD {head_sha:<11s}        : "
          + (f"{h_blocked} blocked, {h_out} of them OUT of scope"
             if h_blocked >= 0 else "(git grep HEAD unavailable)"))
    print(f"AS SCOPED, WORKING TREE               : {len(as_scoped)} blocked, "
          f"{len(out_of_scope)} of them OUT of scope")
    if h_blocked >= 0 and h_blocked != len(as_scoped):
        moved = len(as_scoped) - h_blocked
        print(f"   ^ the two anchors differ by {moved:+d}. This census is "
              "SELF-REFERENTIAL: a file that")
        print("     documents the rule contains the substring and enrols "
              "itself. Not drift, not a lie —")
        print("     which is why no prose in this tree restates the live "
              "number.")
    print(f"REDESIGNED (scope-first + masked call): {len(real)} file(s) with a "
          "real call site   <- the STABLE, gated figure")
    for rel, n in real:
        allowed = _rel_for_allowance(root / rel) in ALLOWED
        print(f"    {rel}  sites={n}  "
              f"{'ALLOWANCE (sanctioned fallback)' if allowed else 'VIOLATION'}")
    print(f"\n=> would block on a no-op edit: "
          f"{len([r for r, _ in real if _rel_for_allowance(root / r) not in ALLOWED])}")
    print("   (the hook blocks on an INCREASE, so even that number is not a "
          "block — it is the standing debt the hook deliberately ignores)")
    _ = pyr
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    H.run_hook(body)
