"""Stop / SubagentStop / PreToolUse(``git commit``) — the JPL Power-of-Ten
ratchet must be green at the moment work is declared done or committed.
(rc455, `#T1169`)

WHAT IT CATCHES
===============
``tests/test_jpl_audit.py`` is a **down-only** ratchet over the C library:
Rule 1 (no goto, no NEW recursion), Rule 3 (no malloc), Rule 4 (≤60-line
functions), Rule 5 (≥2 asserts), Rule 8 (no multi-line macros), Rule 9 (no NEW
function-pointer declarators), plus three seed-tightness checks and two
detector-vacuity checks. Violations may only go DOWN.

The failure mode it exists against is the one this tree keeps meeting: a rule
whose *unmeasured half* drifts and is discovered later, in prose, after the
work was called finished. Rule 1's recursion half was unmeasured until rc441
(9 cycles found on first look); Rule 9 was unmeasured until rc452 (12 sites
already present, and the first cut of that very rc grew them to 14 without
tripping anything). Both were found by a census, not by a gate. This hook puts
the gate at the moment of declaring done.

THE ENGINE: IMPORT THE AUDIT, DO NOT RE-IMPLEMENT AND DO NOT SHELL OUT
=====================================================================
This hook **imports** ``tests/test_jpl_audit.py`` and calls its own functions.
Not one rule regex is restated here. There is exactly one copy of the rule
logic in the tree, so this hook cannot drift from the gate CI runs — a
re-implementation would be a second copy with its own half-life, which is the
defect class the whole file is about.

It does not shell out to pytest either. Measured at rc454 on this tree:

======================================  ==========================
engine                                   cost
======================================  ==========================
``pytest tests/test_jpl_audit.py -q``    ~30 s native / ~53 s WSL
import + call each ``test_*`` naively    27.0 s
**import + call, with the audit's own
helpers memoised**                       **see the two rows below**
======================================  ==========================

⚠️ **THE COST IS A PROPERTY OF THE MOUNT, NOT OF THE HOOK, AND WRITING ONE
RANGE HID THAT.** Whole-invocation wall clock, ``subprocess`` launch to exit,
Stop payload, six spaced samples each:

=========================================  ==============================
environment                                min / median / max
=========================================  ==============================
WSL2 over the 9p mount, cache churned by   **4.5 / 5.4 / 9.5 s**
other work (5275, 4491, 5056, 5560,
**9507**, **8208** ms)
Windows-native on ``D:``, warm cache        **4.1 / 4.3 / 4.9 s**
(4285, 4090, 4320, 4883, 4278, 4261 ms)
=========================================  ==============================

This docstring previously stated the first row alone, as "4.5-9.5 s, median
5.4" with no environment attached, and it does **not** reproduce on a fresh
Windows-native run — the 9.5 s tail is absent there. That is not a retraction of
the tail: both rows are real, the predicate re-reads 9.4 MB of C on every call,
and a cold or contended page cache is what produces the long samples. It is a
correction of the *scope* of the claim. Read it as "**~4-5 s typically,
approaching ~9-10 s when the page cache is cold or the mount is slow**, once per
turn", against ~30 s for the engine it replaces and 18-20 s for
``ratchet_recount``, which is already wired.

Out of scope (any Bash command that is not a ``git commit``) it costs
**0.15 s** Windows-native (146/149/149 ms) and 0.15-0.21 s under WSL2
(152/214/161 ms). An earlier draft said 0.26-0.31 s, which reproduced in
neither.

The naive import is 27 s for a mechanical reason worth stating: the module's
three heavy helpers are called by thirteen check functions, and
``_mask_c_literals`` — a per-character Python state machine over 9.4 MB of C —
runs three times per file. Wrapping the audit's OWN helpers in
``functools.lru_cache`` collapses that to once per file and changes nothing
about what is computed. Measured per check, before → after:
``test_rule_1_no_new_recursion`` 2845 → 3524 ms (it now pays the one mask),
``test_rule_1_recursion_ceiling_is_not_slack`` 3114 → 0 ms,
``test_rule_4_function_length_under_60`` 2860 → 175 ms,
``test_rule_9_no_new_function_pointers`` 2785 → 0 ms.

**No disk cache.** A blob-OID cache buys roughly 4.5 s of the remaining 5.4 and
costs cache-invalidation bugs, which is a strictly worse trade for a gate whose
whole value is that it cannot be wrong about the tree in front of it.

⚠️ THE POPULATION IS THE **TRACKED** FILE SET, AND THAT IS NOT A DETAIL
======================================================================
The audit's helpers glob ``c/src/*.c``. This hook narrows that to the files
``git ls-files`` reports, reading their WORKING-TREE content. Two reasons, and
the second is a measured flake:

1. **It is the population CI measures.** CI audits a checkout. An untracked
   ``.c`` file cannot fail CI, so blocking on one would be a false positive
   against the very gate this hook mirrors. The moment it is staged it is in
   the index, and the ``git commit`` arm sees it before the commit lands.
2. **``check_hooks.py`` writes a Rule-5-violating C file into ``c/src`` as a
   fixture** (``_hook_fixture_rc452.c``, planted at line ~179 and removed in a
   ``finally``). A working-tree scan racing that fixture blocks for a reason
   nobody can reproduce afterwards — the "unexplained flake". The fixture is
   untracked, so a tracked-set scan cannot see it. Proven by running both
   concurrently; see ``check_hooks.py``'s concurrency case.

Modified tracked files ARE scanned from the working tree, so an edit is caught
the moment it is made, not after it is staged.

⚠️ **AN EMPTY TRACKED SET IS A REFUSAL.** The first cut skipped the narrowing
when git returned nothing, which degrades SILENTLY to the naive glob — the very
flake the narrowing closes. Measured with ``SRMECH_HOOK_GIT=/nonexistent/git``:
``_tracked_names`` returned ``{'src': 0, 'include': 0}``, ``_C_SRC_DIR`` stayed
a raw ``Path``, ``_c_files()`` returned all 139 on-disk files and nothing was
echoed. It now raises :class:`TrackedSetUnavailable` and the hook fails OPEN
with a loud note naming the git binary that could not answer.

SCOPE, AND WHY NOT ``PreToolUse(Bash)`` ON EVERYTHING
=====================================================
5 s on every Bash call would be ~7x the 0.69 s stale-native check and would get
the whole hook set switched off. So:

* **Stop / SubagentStop** — paid once per turn, like ``ratchet_recount`` (18 s)
  and ``derived_ledger_freshness`` (5 s).
* **PreToolUse(Bash)** only when a segment INVOKES ``git commit``. Every other
  Bash command exits at the floor (~0.35 s) without importing anything.

NO GIT PRE-COMMIT HOOK, AND THIS IS MEASURED, NOT PREFERRED
===========================================================
``core.hooksPath`` on this machine is ``D:\\GitHub\\mlehaptics\\.git\\hooks`` —
a Windows path. WSL2 is the standing build-subagent environment and cannot
resolve it, so a ``.git/hooks/pre-commit`` is a **silent no-op** there. A gate
that silently does nothing is worse than no gate, because it is believed. The
Claude Code ``PreToolUse`` arm above covers the same moment and reports.

OVERRIDE — EXPLICIT AND RECORDED, NEVER SILENT
==============================================
Both existing conventions in this directory are honored, each where it applies:

* ``SRMECH_ALLOW_JPL_VIOLATION=1`` — the ``stale_native_tripwire`` shape. The
  bypass is ECHOED to stderr with the violation count, so it lands in the
  transcript.
* ``[jpl-pending]`` — the ``ripple_stamp_before_push`` shape. In the ``git
  commit`` command's own text, or in the HEAD commit message at Stop. This one
  is RECORDED IN HISTORY and greppable, which is the stronger form: the goal is
  not to prevent a red ratchet, it is to prevent a red ratchet that PRESENTS AS
  GREEN.

  ⚠️ **The HEAD-commit-message form is a STANDING waiver, not a one-shot**, and
  the message used to say "allowing this stop", which understated it. The token
  is read off HEAD, so it allows EVERY subsequent Stop for as long as that
  commit stays HEAD. It stops applying at the next commit whose message omits
  it. The stderr note now says so and names the commit.

FAIL-OPEN BOUNDARY
==================
An INFRASTRUCTURE failure exits 0 with a loud note, per ``_hooklib``'s
contract; a MEASUREMENT failure (a check ran and was red) exits 2. The two are
never collapsed. Four infrastructure cases, each with its own note:

1. the audit file absent, or ``pytest`` not importable (the module imports it
   for ``pytest.fail`` and ``pytest.mark``) — the ``load_audit`` raise;
2. **the C tree not checked out** — ``docs/srmech/c/src`` is not a directory.
   This case was NAMED here from the first cut and NOT IMPLEMENTED: measured
   against a tree holding ``tests/test_jpl_audit.py`` with no ``docs/srmech/c/``
   present, the hook exited **2** with "6 of 13 JPL Power-of-Ten checks are
   RED";
3. **the audit declares ITSELF skipped** — :func:`audit_skip_reason` reads the
   module's own ``pytestmark``, which is the second copy of the scoping the
   "one copy of the rule logic" claim did not cover;
4. **git cannot name the tracked set** — :class:`TrackedSetUnavailable`, rather
   than a silent fall-back to the working-tree glob.

Cases 2 and 3 both invert "a SKIP is not a PASS" into "a SKIP is a BLOCK" if
left unhandled, which is the stricter error and still an error: pytest collects
nothing in that state, so blocking would be stricter than the gate this hook
mirrors. Neither is reported as a pass.
"""

from __future__ import annotations

import functools
import importlib.util
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

#: The gate whose functions this hook calls. One copy of the rule logic.
AUDIT_REL = "tests/test_jpl_audit.py"

#: Repo-relative pathspecs whose TRACKED members form the scan population.
C_PATHS = ("docs/srmech/c/src", "docs/srmech/c/include")

#: Audit helpers memoised so thirteen checks pay each scan once. Names that are
#: absent are skipped, so a rename in the audit degrades to "slow", not "wrong".
MEMOISE = ("_mask_c_literals", "_function_bodies", "_scan_functions",
           "_recursion_cycles", "_fn_ptr_sites", "_c_files", "_rule9_files")

OVERRIDE_ENV = "SRMECH_ALLOW_JPL_VIOLATION"
PENDING_TOKEN = "[jpl-pending]"

MAX_SHOWN = 6


# ── the tracked-set narrowing ─────────────────────────────────────────────

class _TrackedDir:
    """A directory that globs only the names git has in the index.

    Duck-typed against the three ``Path`` operations the audit performs on
    ``_C_SRC_DIR`` / ``_C_INCLUDE_DIR``: ``glob``, ``exists`` and ``.parent``
    (for ``JPL_AUDIT.md``). It deliberately does NOT subclass ``Path`` — the
    point is to be obviously a filter, not to look like a directory.
    """

    def __init__(self, real: Path, allowed_names: "set[str]") -> None:
        self._real = real
        self._allowed = allowed_names

    def glob(self, pattern: str) -> "list[Path]":
        return [p for p in self._real.glob(pattern) if p.name in self._allowed]

    def exists(self) -> bool:
        return self._real.exists()

    def is_dir(self) -> bool:
        return self._real.is_dir()

    @property
    def parent(self) -> Path:
        return self._real.parent

    def __truediv__(self, other: str) -> Path:
        return self._real / other

    def __fspath__(self) -> str:
        return str(self._real)

    def __str__(self) -> str:
        return str(self._real)


class TrackedSetUnavailable(RuntimeError):
    """git could not name the tracked C files, so the narrowing cannot be done.

    Raised rather than shrugged off. See :func:`load_audit`.
    """


def _tracked_names(root: Path) -> "dict[str, set[str]]":
    """``{'src': {names...}, 'include': {names...}}`` from the git index."""
    out: "dict[str, set[str]]" = {"src": set(), "include": set()}
    for rel in H.tracked_files(root, C_PATHS):
        parts = rel.replace("\\", "/").split("/")
        if len(parts) < 2:
            continue
        if parts[-2] == "src":
            out["src"].add(parts[-1])
        elif parts[-2] == "include":
            out["include"].add(parts[-1])
    return out


# ── loading + preparing the audit module ──────────────────────────────────

def load_audit(root: Path, *, restrict_to_tracked: bool = True):
    """Import the audit, memoise its helpers, narrow it to the tracked set.

    ``sys.modules[spec.name] = mod`` before ``exec_module`` is not optional —
    ``generated_file_edit_blocker`` shipped an entire dead predicate for want
    of that one line (rc452), because a module loaded outside ``sys.modules``
    cannot resolve its own string annotations.
    """
    path = H.py_root(root) / AUDIT_REL
    if not path.is_file():
        raise FileNotFoundError(f"{AUDIT_REL} not present under {H.py_root(root)}")
    spec = importlib.util.spec_from_file_location("srmech_jpl_audit_hook", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    for name in MEMOISE:
        fn = getattr(mod, name, None)
        if callable(fn):
            setattr(mod, name, functools.lru_cache(maxsize=None)(fn))

    if restrict_to_tracked:
        names = _tracked_names(root)
        # ⚠️ AN EMPTY TRACKED SET IS A REFUSAL, NOT A SHRUG.
        # The first cut read `if names["src"]:` and skipped the narrowing when
        # git could not answer. That degrades SILENTLY to the naive
        # working-tree glob — which is the exact flake the narrowing exists to
        # close, so the failure mode reinstated the defect and said nothing.
        # Measured with `SRMECH_HOOK_GIT=/nonexistent/git`: `_tracked_names`
        # -> {'src': 0, 'include': 0}, `mod._C_SRC_DIR` stayed a raw
        # WindowsPath, `_c_files()` returned all 139 on-disk files, and NOTHING
        # was echoed. Combined with the counterfactual in check_hooks.py
        # (naive glob + the planted untracked fixture -> 1 RED), an
        # unresolvable git during a check_hooks.py run reproduces exactly the
        # unreproducible block the section above calls "closed by
        # construction".
        missing = [k for k in ("src", "include") if not names[k]]
        if missing:
            raise TrackedSetUnavailable(
                f"git listed 0 tracked files under c/{' and c/'.join(missing)} "
                f"(git binary: {H.git_exe()!r}, root: {root}). The scan "
                "population cannot be narrowed to the tracked set, and falling "
                "back to the working-tree glob would silently reinstate the "
                "fixture-collision flake this narrowing closes.")
        mod._C_SRC_DIR = _TrackedDir(mod._C_SRC_DIR, names["src"])
        mod._C_INCLUDE_DIR = _TrackedDir(mod._C_INCLUDE_DIR, names["include"])
    return mod


def audit_skip_reason(mod) -> Optional[str]:
    """The audit's OWN ``pytestmark`` reason, when it declares itself skipped.

    ⚠️ **THE "ONE COPY OF THE RULE LOGIC" CLAIM WAS TRUE OF THE RULES AND FALSE
    OF THE SCOPING.** ``tests/test_jpl_audit.py`` opens with::

        pytestmark = pytest.mark.skipif(not _C_SRC_DIR.exists(), reason=...)

    pytest honors that; a direct call to the ``test_*`` functions does not. So
    a checkout with no ``docs/srmech/c/`` SKIPS in CI and — measured against a
    tree holding only the audit file — **exited 2 here** with "6 of 13 JPL
    Power-of-Ten checks are RED": both ``*_ceiling_is_not_slack`` (live
    population 0 against ceilings 9 and 10), both ``*_detector_is_not_vacuous``,
    ``test_rule_4_seed_is_tight_and_drains`` and
    ``test_audit_doc_present_and_mentions_all_rules``. That is the docstring's
    own named fail-open case ("the C tree not checked out") behaving as a BLOCK,
    and it inverts this slice's own principle — a SKIP is not a PASS — into the
    strictly worse "a SKIP is a BLOCK".

    Reading the mark rather than restating its condition keeps the single-copy
    property on this axis too: the condition is evaluated at the audit's own
    import time, so whatever pytest would have seen is what this returns.
    """
    marks = getattr(mod, "pytestmark", None)
    if marks is None:
        return None
    for mark in (marks if isinstance(marks, (list, tuple)) else [marks]):
        m = getattr(mark, "mark", mark)
        if getattr(m, "name", "") != "skipif":
            continue
        args = getattr(m, "args", ()) or ()
        if args and args[0]:
            return str(getattr(m, "kwargs", {}).get("reason", "")
                       or "the audit declares itself skipped")
    return None


def check_names(mod) -> List[str]:
    return sorted(n for n in dir(mod) if n.startswith("test_"))


def run_checks(mod) -> "list[tuple[str, str, float]]":
    """Call every ``test_*`` in the audit. Returns ``(name, reason, ms)`` for
    the RED ones only. All thirteen run — an early exit would hide which other
    predicates were live at the same moment."""
    reds: "list[tuple[str, str, float]]" = []
    for name in check_names(mod):
        t = time.perf_counter()
        try:
            getattr(mod, name)()
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as exc:          # pytest.fail raises BaseException
            reason = str(exc).strip().splitlines()[0] if str(exc).strip() else \
                type(exc).__name__
            reds.append((name, reason[:400], (time.perf_counter() - t) * 1000))
    return reds


# ── scope ─────────────────────────────────────────────────────────────────

def _commit_segment(payload: Dict[str, Any]) -> Optional[str]:
    """The segment that INVOKES ``git commit``, or ``None``.

    ``_hooklib.leading_git_args`` is what keeps ``echo "git commit"`` from
    firing while ``cd x && git commit -m ...`` does: it requires git to be the
    invoked PROGRAM, not merely a word in the line.

    ⚠️ **THE MEMBERSHIP TEST IS NOT SLOPPINESS — ``args[0] == "commit"`` WAS A
    MEASURED HOLE.** git takes options before the subcommand, and three of them
    are ordinary in this tree. Measured by calling :func:`_scope` directly, with
    the first cut of this function::

        git commit -m x                  -> ('committing', ...)
        cd d && git commit -m x          -> ('committing', ...)
        git -C docs/srmech commit -m x   -> None      <- out of scope
        git --no-pager commit -m x       -> None      <- out of scope
        git -c user.name=z commit -m x   -> None      <- out of scope

    ``git -C <dir> commit`` is the normal invocation for an agent working from
    another cwd, so the arm was silently off for a routine shape. Its two peers
    in this directory never had the bug — ``ssot_agreement._is_commit`` and
    ``ripple_stamp_before_push`` both use membership — and matching them is the
    fix. Measured after: all five above return ``('committing', ...)`` and
    ``echo "git commit"`` still returns ``None``.

    The Stop / SubagentStop arm always covered end-of-turn, so the hole narrowed
    the commit-time arm rather than removing the gate.
    """
    cmd = H.bash_command(payload)
    if not cmd:
        return None
    for seg in H.split_segments(cmd):
        args = H.leading_git_args(seg)
        if args and "commit" in args:
            return seg
    return None


def _scope(payload: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """``(why, admission_text)`` or ``None`` when out of scope."""
    event = payload.get("hook_event_name") or ""
    if event in ("Stop", "SubagentStop"):
        if H.stop_is_repeat(payload):
            return None
        return ("declaring done", "")
    seg = _commit_segment(payload)
    if seg is None:
        return None
    return ("committing", seg)


# ── body ──────────────────────────────────────────────────────────────────

def body(payload: Dict[str, Any]) -> int:
    scope = _scope(payload)
    if scope is None:
        return H.allow()
    why, admission = scope

    root = H.repo_root()

    # ── FAIL-OPEN BOUNDARY 1: the C tree is not checked out ───────────────
    # The docstring has named this case since the first cut; it was not
    # implemented, and the hook exited 2 on it. Checked BEFORE the import so an
    # absent C tree never reaches the tracked-set refusal below, which would
    # otherwise answer the same state with the wrong reason.
    c_src = H.c_root(root) / "src"
    if not c_src.is_dir():
        return H.allow([
            f"[jpl-audit] the C source tree is not checked out ({c_src} is not "
            "a directory), so there is nothing to audit. Fails OPEN, as "
            "documented. NOT a pass — pytest SKIPS this gate in the same "
            "state, and a SKIP is not a PASS either."])

    try:
        mod = load_audit(root)
    except TrackedSetUnavailable as exc:      # INFRASTRUCTURE — fail open, loud
        return H.allow([
            f"[jpl-audit] REFUSING to scan: {exc}",
            "NOT a pass, and deliberately not a silent fall-back to the "
            "working-tree glob. Fix the git this hook resolves "
            f"({H.HOOK_GIT_ENV}=<path> pins one), or run "
            f"`pytest {AUDIT_REL} -q` by hand."])
    except Exception as exc:                  # INFRASTRUCTURE — fail open, loud
        return H.allow([
            f"[jpl-audit] could not load {AUDIT_REL}: "
            f"{type(exc).__name__}: {exc}. NOT a pass — run "
            f"`pytest {AUDIT_REL} -q` by hand."])

    # ── FAIL-OPEN BOUNDARY 2: the audit declares ITSELF out of scope ──────
    skipped = audit_skip_reason(mod)
    if skipped:
        return H.allow([
            f"[jpl-audit] {AUDIT_REL} declares itself SKIPPED at this checkout: "
            f"{skipped[:200]}. pytest would collect nothing here, so blocking "
            "would be stricter than the gate this hook mirrors. NOT a pass."])

    reds = run_checks(mod)
    if not reds:
        return H.allow()

    # ── the two documented, recorded overrides ────────────────────────────
    if os.environ.get(OVERRIDE_ENV) == "1":
        return H.allow([
            f"[jpl-audit] {OVERRIDE_ENV}=1 — BYPASSING {len(reds)} RED JPL "
            f"check(s): {', '.join(n for n, _, _ in reds[:MAX_SHOWN])}. The C "
            "library does not pass its own ratchet at this commit."])

    if PENDING_TOKEN in admission:
        return H.allow([
            f"[jpl-audit] {PENDING_TOKEN} in the commit command — allowing a "
            f"commit with {len(reds)} RED JPL check(s). This is now a recorded "
            "admission in the commit itself, not a silent omission."])
    if not admission:
        code, head_msg = H.git(["log", "-1", "--format=%H%n%B"], cwd=root)
        head_sha = head_msg.strip().splitlines()[0][:12] if code == 0 and \
            head_msg.strip() else "?"
        if PENDING_TOKEN in head_msg:
            return H.allow([
                f"[jpl-audit] {PENDING_TOKEN} in the HEAD commit message "
                f"({head_sha}) — allowing this stop with {len(reds)} RED JPL "
                "check(s), recorded in history.",
                # SAY WHAT IT ACTUALLY DOES. "allowing this stop" reads as a
                # one-shot; it is not. The token is read off HEAD, so it allows
                # EVERY subsequent Stop for as long as that commit stays HEAD —
                # which, on a branch that keeps working after the admission,
                # can be the rest of the session.
                f"⚠️ This is NOT a one-shot: the token is read off HEAD, so "
                f"every Stop is allowed while {head_sha} remains HEAD. It stops "
                "applying at the next commit whose message omits the token. It "
                "is greppable in history, which is the point — but it is a "
                "standing waiver, not a single one."])

    lines = [
        f"BLOCKED (jpl-audit-gate): {len(reds)} of {len(check_names(mod))} JPL "
        f"Power-of-Ten checks are RED, so this work is not ready for "
        f"{why}.",
    ]
    for name, reason, _ms in reds[:MAX_SHOWN]:
        lines.append(f"  {name}")
        lines.append(f"      {reason}")
    if len(reds) > MAX_SHOWN:
        lines.append(f"  (+{len(reds) - MAX_SHOWN} more)")
    lines += [
        "",
        "These ratchets are DOWN-ONLY. The legitimate exits are:",
        "  1. ROOT-FIX — split the function, add the asserts, unwind the "
        "recursion to an explicit bounded stack, replace the function pointer "
        "with the A1 shape (small-int enum + bounded switch, NO default arm).",
        "  2. ADJUDICATE — for a seeded population only: extend the seed set "
        "AND move its ceiling in the same commit, with the per-entry rationale "
        "in docs/srmech/c/JPL_AUDIT.md. A ceiling above the measured count is "
        "itself red (`*_ceiling_is_not_slack`), so slack is not an exit.",
        "",
        "Re-run just this gate:",
        # The RUNNING interpreter, not a literal. `python3` is not `python` on
        # this machine (two 3.14 installs, resolved by PATH order), so advice
        # naming either one can send the reader to the wrong pytest.
        f"    {H.python_exe()} -m pytest {AUDIT_REL} -q",
        f"Population + timings:  {H.python_exe()} "
        f"tools/hooks/{Path(__file__).name} --selftest",
        "",
        f"Deliberate, and you want it on the record? Put {PENDING_TOKEN} in the "
        f"commit message, or set {OVERRIDE_ENV}=1 — both are echoed, neither is "
        "silent.",
    ]
    return H.block(lines)


# ── selftest: POPULATIONS, not just a verdict ─────────────────────────────

def selftest() -> int:
    """Print what each predicate actually SAW.

    The rc452 lesson in one function: a dead predicate and a satisfied one are
    the same shape from outside. ``generated_file_edit_blocker`` returned ``[]``
    from one of its two predicates for its whole shipped life and every exit
    status was correct. Only a population can tell them apart.
    """
    root = H.repo_root()
    for line in H.describe_env(root, C_PATHS):
        print(line)
    print()

    t0 = time.perf_counter()
    try:
        mod = load_audit(root)
    except Exception as exc:
        print(f"LOAD FAILED: {type(exc).__name__}: {exc}")
        return 1
    t_import = (time.perf_counter() - t0) * 1000

    tracked = _tracked_names(root)
    on_disk_src = sorted(p.name for p in (H.c_root(root) / "src").glob("*.c"))
    on_disk_src += sorted(p.name for p in (H.c_root(root) / "src").glob("*.h"))
    excluded = [n for n in on_disk_src if n not in tracked["src"]]

    print(f"load + memoise            : {t_import:7.1f} ms")
    print(f"tracked c/src   population: {len(tracked['src'])}")
    print(f"tracked c/include         : {len(tracked['include'])}")
    print(f"on-disk c/src (.c + .h)   : {len(on_disk_src)}")
    print(f"UNTRACKED, excluded ({len(excluded)}) : "
          f"{', '.join(excluded) or '(none)'}")
    print("   ^ this is the check_hooks.py fixture collision, closed by "
          "construction")
    print()

    t = time.perf_counter()
    files = mod._c_files()
    print(f"_c_files()                : {len(files):5d} files   "
          f"{(time.perf_counter()-t)*1000:7.1f} ms")
    t = time.perf_counter()
    r9 = mod._rule9_files()
    print(f"_rule9_files()            : {len(r9):5d} files   "
          f"{(time.perf_counter()-t)*1000:7.1f} ms")
    t = time.perf_counter()
    cycles = mod._recursion_cycles()
    print(f"_recursion_cycles()       : {len(cycles):5d} cycles  "
          f"{(time.perf_counter()-t)*1000:7.1f} ms   "
          f"(ceiling {mod.CEIL_RULE_1_RECURSION})")
    t = time.perf_counter()
    sites = mod._fn_ptr_sites()
    print(f"_fn_ptr_sites()           : {len(sites):5d} sites   "
          f"{(time.perf_counter()-t)*1000:7.1f} ms   "
          f"(ceiling {mod.CEIL_RULE_9_FN_PTR})")
    t = time.perf_counter()
    nfun = sum(len(mod._scan_functions(f))
               for f in sorted(mod._C_SRC_DIR.glob("*.c")))
    print(f"_scan_functions() total   : {nfun:5d} funcs   "
          f"{(time.perf_counter()-t)*1000:7.1f} ms")
    print()

    reds = run_checks(mod)
    names = check_names(mod)
    print(f"checks run: {len(names)}   RED: {len(reds)}")
    for name, reason, ms in reds:
        print(f"  RED  {name}  ({ms:.0f} ms)\n       {reason[:200]}")
    print(f"\nTOTAL PREDICATE COST: {(time.perf_counter()-t0)*1000:.0f} ms "
          "(add ~350 ms of interpreter start for a real invocation)")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    H.run_hook(body)
