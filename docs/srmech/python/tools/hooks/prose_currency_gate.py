"""Stop / SubagentStop — shipped prose that a gate already covers must not be
left red at the moment work is declared done. (rc455, `#T1169`)

WHAT IT CATCHES
===============
Prose in this tree SHIPS. ``python/README.md`` is the PyPI long-description;
``_tool_docs.py`` prose is emitted into the wheel and reaches users through
the MCP tool list and the compiled-in C registry. Four gates
already cover four slices of it — and coverage without repair is what rc452
found: ``test_readme_currency_rc419.py`` was RED on a shipped "**ABI 21** at
this release" sentence while the macro said 22, and had been for a release.
This hook runs those gates at the moment of declaring done, and only for the
surfaces the session actually touched.

THE FOUR GATES, AND THE PATHS THAT ARM EACH ONE
===============================================
=========================================  ====================================
gate                                       fires when these are dirty
=========================================  ====================================
``test_readme_currency_rc419``             ``python/README.md``
``test_pypi_readme_changelog``             ``python/README.md``, ``CHANGELOG.md``
``test_readme_c_coverage_figures_rc451``   ``python/README.md``, ``c/src``,
                                           ``c/include``
``test_cascade_catalog_prose_currency``    ``srmech/introspect``,
``_rc454``                                 ``srmech/cascade/catalogs``
=========================================  ====================================

Per-gate scoping keeps the tax proportional, the way
``derived_ledger_freshness`` scopes per ledger row: editing one README does not
buy the whole 13.8 s.

⚠️ DEFECT 1, REPAIRED: THE TRIGGER WAS WSL-GIT POISONED
=======================================================
As designed, the trigger was ``git status --porcelain -- README.md
CHANGELOG.md``. Measured at rc454 on ONE clean tree at ONE commit:

  ==========================  ===========  ========
  query                       Windows git  WSL git
  ==========================  ===========  ========
  ``status --porcelain``                0         2
  :func:`_hooklib.dirty_paths`          0         0
  ==========================  ===========  ========

Under WSL — the standing build-subagent environment — the original trigger
fires **unconditionally**, on every stop, forever, because the index blobs are
LF and the working files CRLF and WSL git does not read the Windows global
``core.autocrlf=true``. A trigger that is always true is not a trigger.
:func:`_hooklib.dirty_paths` asks git for the change in CONTENT
(``diff HEAD --numstat --ignore-cr-at-eol``, dropping rows that are 0/0) and
measured identical under both gits — including ``2  0  README.md`` for one real
planted two-line edit, so it can still return otherwise.

⚠️ DEFECT 2, REPAIRED: THE TRIGGER COULD NOT SEE THE STATE IT WAS BUILT FOR
===========================================================================
The first cut armed on :func:`_hooklib.dirty_paths` ALONE — the WORKING TREE
against ``HEAD``. So the trigger went silent the moment a prose edit was
COMMITTED. Measured on a purpose-built git fixture (``probe`` in
``check_hooks.py``'s prose section), one file, three states:

  ==================================  ==========================================
  state                               ``dirty_paths`` said
  ==================================  ==========================================
  clean                               ``[]``
  README carrying a planted ABI lag,
  UNCOMMITTED                         ``['docs/srmech/python/README.md']``
  **the SAME lag, COMMITTED**         **``[]``**  <- no gate armed, silent allow
  ==================================  ==========================================

This repo commits per step and never squash-merges, so *edit README, commit,
stop* is the ORDINARY session shape and the hook did nothing in it. Worse,
rc452's actual defect — the shipped "**ABI 21** at this release" against macro
22 — was a COMMITTED falsehood that had survived a release, i.e. precisely the
state the trigger was blind to. A currency gate that only fires on uncommitted
work is blind to exactly the case that ships.

Its own peer next door already had this right: ``derived_ledger_freshness``
unions ``git diff --name-only base..HEAD`` (COMMITTED drift) WITH the
working-tree half. :func:`changed_prose_paths` now does the same, over a base
resolved in a stated order (:func:`resolve_base`) — merge-base with the
upstream default branch, else the newest reachable ``srmech-v*`` tag, else
``HEAD~1`` as an explicit floor. **A base that cannot be resolved at all is
ECHOED, never swallowed**, because a trigger that quietly narrows itself is the
defect this section is about.

Measured after the repair, same fixture, same three states: ``[]`` /
``['docs/srmech/python/README.md']`` / ``['docs/srmech/python/README.md']``.

⚠️ DEFECT 3, REPAIRED: A SKIP IS NOT A PASS
===========================================
Measured at rc454, the same four gates, same tree, same commit:

    Windows :  55 passed, 1 skipped     (no compiled ``srmech.dll``)
    WSL2    :  56 passed, 0 skipped     (the ``.so`` loads)

**Both exit 0.** A hook that reads the exit status calls the first one green
while one assertion never ran — and the skipped case is precisely the one that
needs the native library, i.e. the arm most likely to have moved. So this hook
parses the counts (:func:`_hooklib.pytest_counts`) and:

* ``failed`` or ``error`` above zero, or a non-zero exit  ->  **BLOCK**.
* ``passed == 0`` while anything was collected  ->  **BLOCK**. A wholly-skipped
  run is a vacuous run; an instrument that cannot return otherwise is not a
  measurement.
* ``skipped > 0``  ->  ALLOW, but the skip COUNT AND REASON are printed to
  stderr, so no turn can end on an unqualified "prose gates green" when one of
  them did not run.
* a timeout  ->  ALLOW with "did not finish", never reported as a pass.

COST
====
Measured native at rc454: all four gates in one pytest call, 13.8 s wall
(11.25 s inside pytest). Stop-only, so it is paid once per turn — the same
bracket as ``ratchet_recount`` (18 s). A single-gate arming is 5-10 s.

OVERRIDE
========
``SRMECH_ALLOW_PROSE_LAG=1`` bypasses the block and the bypass is ECHOED with
the failing gate names, per the ``stale_native_tripwire`` convention.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

#: ``(gate file, pathspecs that arm it)``. The pathspecs are repo-relative.
GATES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("tests/test_readme_currency_rc419.py",
     ("docs/srmech/python/README.md",)),
    ("tests/test_pypi_readme_changelog.py",
     ("docs/srmech/python/README.md", "docs/srmech/python/CHANGELOG.md")),
    ("tests/test_readme_c_coverage_figures_rc451.py",
     ("docs/srmech/python/README.md", "docs/srmech/c/src",
      "docs/srmech/c/include")),
    ("tests/test_cascade_catalog_prose_currency_rc454.py",
     ("docs/srmech/python/srmech/introspect",
      "docs/srmech/python/srmech/cascade/catalogs")),
)

TIMEOUT_S = 300.0
OVERRIDE_ENV = "SRMECH_ALLOW_PROSE_LAG"

#: Explicit pin for the commit this session's prose drift is measured FROM.
#: Set it when neither an upstream branch nor an ``srmech-v*`` tag is the right
#: answer (a detached CI checkout, a fixture repo, a bisect).
PROSE_BASE_ENV = "SRMECH_PROSE_BASE"

#: Upstream refs tried, in order, for ``git merge-base HEAD <ref>``.
UPSTREAM_REFS = ("origin/main", "origin/HEAD", "origin/master")


def all_watched() -> List[str]:
    seen: List[str] = []
    for _, paths in GATES:
        for p in paths:
            if p not in seen:
                seen.append(p)
    return seen


def resolve_base(root: Path) -> Tuple[str, str]:
    """``(commit_or_empty, how_it_was_found)`` — what "since this session began"
    means for the COMMITTED half of the trigger.

    The order is stated rather than inferred, and the last entry of it is a
    deliberate floor rather than a guess:

    1. ``SRMECH_PROSE_BASE`` — an explicit pin, so a caller who knows better
       always wins.
    2. ``git merge-base HEAD <upstream>`` for the first of
       :data:`UPSTREAM_REFS` that resolves. This is the branch point, so every
       commit this session made is inside the window and nothing before it is.
       Measured on this worktree: ``origin/main`` resolves and the merge-base
       IS ``HEAD``, so the committed half is empty and nothing false-arms.
    3. the newest reachable ``srmech-v*`` tag — the previous release, for work
       done directly on ``main`` in a checkout with no remote.
    4. ``HEAD~1`` — at minimum, the commit that was just made. A repo with one
       commit and no remote (a fixture) has nothing earlier, and returning ""
       there would be indistinguishable from "nothing changed".

    An empty return is a REAL failure to resolve and the caller must say so.
    """
    pinned = os.environ.get(PROSE_BASE_ENV, "").strip()
    if pinned:
        code, out = H.git(["rev-parse", "--verify", "-q", pinned + "^{commit}"],
                          cwd=root)
        if code == 0 and out.strip():
            return out.strip().splitlines()[-1].strip(), f"{PROSE_BASE_ENV}={pinned}"
    for ref in UPSTREAM_REFS:
        code, out = H.git(["merge-base", "HEAD", ref], cwd=root)
        if code == 0 and out.strip():
            return out.strip().splitlines()[-1].strip(), f"merge-base with {ref}"
    code, out = H.git(["describe", "--tags", "--match", "srmech-v*",
                       "--abbrev=0"], cwd=root)
    if code == 0 and out.strip():
        tag = out.strip().splitlines()[-1].strip()
        return tag, f"newest reachable tag {tag}"
    code, out = H.git(["rev-parse", "--verify", "-q", "HEAD~1"], cwd=root)
    if code == 0 and out.strip():
        return out.strip().splitlines()[-1].strip(), "HEAD~1 (floor)"
    return "", "UNRESOLVED"


def changed_prose_paths(root: Path) -> Tuple[List[str], str]:
    """``(paths, base_note)`` — watched prose that moved since the base, in the
    COMMITTED half as well as the working tree.

    ``derived_ledger_freshness._changed_paths`` is the shape being matched: the
    committed half is ``diff --name-only base..HEAD`` (both sides are index
    blobs, so EOL policy cannot enter) and the working-tree half is
    :func:`_hooklib.dirty_paths`, which is EOL-immune by construction.
    """
    watched = all_watched()
    base, how = resolve_base(root)
    seen: List[str] = []
    if base:
        code, out = H.git(["diff", "--name-only", f"{base}..HEAD", "--",
                           *watched], cwd=root)
        if code == 0:
            seen.extend(l.strip() for l in out.splitlines() if l.strip())
    for p in H.dirty_paths(root, watched):
        if p not in seen:
            seen.append(p)
    return seen, how


def armed_gates(root: Path, dirty: Sequence[str]) -> List[str]:
    """The gate files whose watched paths carry a real content change."""
    out: List[str] = []
    for gate, paths in GATES:
        if not (H.py_root(root) / gate).is_file():
            continue
        for watched in paths:
            if any(d == watched or d.startswith(watched.rstrip("/") + "/")
                   for d in dirty):
                out.append(gate)
                break
    return out


def body(payload: Dict[str, Any]) -> int:
    event = payload.get("hook_event_name") or ""
    if event not in ("Stop", "SubagentStop"):
        return H.allow()
    if H.stop_is_repeat(payload):
        return H.allow([
            "[prose-currency] WARNING: stop_hook_active — allowing this stop "
            "without re-running the prose gates."])

    root = H.repo_root()
    dirty, base_how = changed_prose_paths(root)
    unresolved: List[str] = []
    if base_how == "UNRESOLVED":
        # NOT a silent narrowing. Without a base the committed half cannot be
        # asked at all, so the trigger degrades to the working tree — the very
        # blindness DEFECT 2 repaired — and that has to be said out loud.
        unresolved = [
            "[prose-currency] could not resolve a base commit (no upstream ref, "
            f"no srmech-v* tag, no HEAD~1). Set {PROSE_BASE_ENV}=<commit> to pin "
            "one. COMMITTED prose drift is NOT being checked on this stop; only "
            "the working tree is."]
    gates = armed_gates(root, dirty)
    if not gates:
        return H.allow(unresolved)

    code, out = H.run(
        [H.python_exe(), "-m", "pytest", *gates, "-q", "-rs"],
        cwd=H.py_root(root), timeout=TIMEOUT_S, env_extra={"PYTHONPATH": "."},
    )
    counts = H.pytest_counts(out)
    n_pass = counts.get("passed", 0)
    n_fail = counts.get("failed", 0) + counts.get("error", 0)
    n_skip = counts.get("skipped", 0)

    if code < 0:
        return H.allow([
            f"[prose-currency] the gates did not finish ({out.strip()[:120]}); "
            "allowing the stop. This is NOT a pass — re-run by hand: "
            f"pytest {' '.join(gates)} -q", *unresolved])

    # A SKIP IS NOT A PASS. Say so, every time, whatever the verdict.
    skip_note: List[str] = []
    if n_skip:
        reasons = [l.strip() for l in out.splitlines()
                   if l.strip().startswith("SKIPPED")]
        skip_note = [
            f"[prose-currency] {n_pass} passed, {n_skip} SKIPPED of "
            f"{n_pass + n_skip + n_fail} — the skipped assertion(s) did NOT "
            "run, so this turn cannot claim these gates are green:",
            *[f"    {r}" for r in reasons[:4]],
        ]

    vacuous = (n_pass == 0 and n_skip > 0 and n_fail == 0)
    if code == 0 and n_fail == 0 and not vacuous:
        return H.allow(skip_note + unresolved)

    if os.environ.get(OVERRIDE_ENV) == "1":
        return H.allow([
            f"[prose-currency] {OVERRIDE_ENV}=1 — BYPASSING a real prose-gate "
            f"failure ({n_fail} failed / {n_pass} passed / {n_skip} skipped) "
            f"in: {', '.join(gates)}. Shipped prose is wrong at this commit.",
            *skip_note, *unresolved])

    tail = "\n".join(out.strip().splitlines()[-30:])
    why = ("every collected test SKIPPED — the gates measured nothing"
           if vacuous else f"{n_fail} failed")
    return H.block([
        f"BLOCKED (prose-currency): {why} in the prose gate(s) armed by this "
        "session's edits, so shipped text is not ready to be called done.",
        f"  armed by : {', '.join(sorted(set(dirty))[:6])}"
        + (f" (+{len(set(dirty)) - 6} more)" if len(set(dirty)) > 6 else ""),
        f"  base     : {base_how}  (committed drift since it counts, not just "
        "the working tree)",
        f"  gates    : {', '.join(gates)}",
        "",
        tail,
        "",
        *skip_note,
        *unresolved,
        "",
        "This prose SHIPS: python/README.md is the PyPI long-description and "
        "the emitted ToolEntry text travels inside the wheel to describe(), "
        "the MCP tool list and the compiled-in C registry. rc452 found a live "
        "shipped falsehood here (\"**ABI 21** at this release\" against macro "
        "22) with the gate ALREADY RED — coverage existed, the repair did not.",
        "",
        # The RUNNING interpreter, not a literal — `python3` is not `python`
        # on this machine and advice naming either can send the reader to the
        # wrong pytest.
        f"Re-run:  {H.python_exe()} -m pytest {' '.join(gates)} -q -rs",
        f"Deliberate? {OVERRIDE_ENV}=1 bypasses and is echoed, not silent.",
    ])


def selftest() -> int:
    root = H.repo_root()
    for line in H.describe_env(root, all_watched()):
        print(line)
    print()
    working = H.dirty_paths(root, all_watched())
    base, how = resolve_base(root)
    dirty, _ = changed_prose_paths(root)
    committed = [p for p in dirty if p not in working]
    print(f"watched pathspecs : {len(all_watched())}")
    print(f"base commit       : {base[:12] or '(none)'}  via {how}")
    print(f"COMMITTED half    : {len(committed)}  "
          f"{', '.join(committed[:8]) or '(none)'}")
    print(f"working-tree half : {len(working)}  "
          f"{', '.join(working[:8]) or '(none)'}")
    print(f"trigger (union)   : {len(dirty)}  {', '.join(dirty[:8]) or '(none)'}")
    if how == "UNRESOLVED":
        print("   ^ NO BASE: the committed half is not being asked at all. "
              f"Pin one with {PROSE_BASE_ENV}=<commit>.")
    porcelain, content = H.eol_noise(root, all_watched())
    print(f"status --porcelain would have said {porcelain}; content-diff says "
          f"{content}"
          + ("   <- the WSL-git poisoning this hook was repaired for"
             if porcelain > content else ""))
    print(f"armed gates       : {', '.join(armed_gates(root, dirty)) or '(none)'}")
    print()
    print("all four gates, counts (this is the SKIP-is-not-a-PASS surface):")
    code, out = H.run([H.python_exe(), "-m", "pytest",
                       *[g for g, _ in GATES], "-q", "-rs"],
                      cwd=H.py_root(root), timeout=TIMEOUT_S,
                      env_extra={"PYTHONPATH": "."})
    counts = H.pytest_counts(out)
    print(f"  exit={code}  counts={counts}")
    # THE VACUITY LINE, and its wording is the assertion.
    # `counts=` alone would still be printed if pytest_counts returned {} — the
    # parser could die and this selftest would look identical. Only the first
    # form below can be emitted with a non-zero pass count, so check_hooks.py
    # keys on it. The pass count itself is deliberately NOT pinned to a
    # literal: it is 55 passed / 1 skipped on Windows and 56 / 0 under WSL2
    # (the compiled library gates one assertion), so an exact pin would be a
    # false red on whichever platform it was not written on.
    n_pass = counts.get("passed", 0)
    n_coll = n_pass + counts.get("skipped", 0) + counts.get("failed", 0) \
        + counts.get("error", 0)
    if not counts:
        print("  VACUITY: NOTHING PARSED — pytest_counts returned {}")
    elif n_pass <= 0:
        print(f"  VACUITY: passed=0 of {n_coll} collected — a wholly-skipped "
              "or empty run measures nothing")
    else:
        print(f"  VACUITY: counts parsed, passed={n_pass} > 0 "
              f"(of {n_coll} collected)")
    for line in out.splitlines():
        if line.strip().startswith("SKIPPED"):
            print(f"  {line.strip()}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    H.run_hook(body)
