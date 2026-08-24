"""PreToolUse(Bash) + Stop — refuse to trust a parity result measured against a
stale ``libsrmech``. (rc452, `#T1166`)

WHAT IT CATCHES, MEASURED
=========================
The stale-artifact trap, hit FOUR times in this session alone: a library older
than ``c/src/*.c`` still reports ``HAS_NATIVE=True`` and ``ABI 21 == 21``. The
ABI check cannot see staleness — it compares a compiled-in integer against an
expected one, and a stale lib compiled at the same ABI answers correctly. Only
the clock distinguishes them.

WHY mtime HERE, WHEN THE TREE BANS mtime ELSEWHERE
==================================================
``tools/regen_all.py`` argues at length against mtime and it is RIGHT — for the
case it rules on:

    "mtime is not a dependency signal in a git checkout — clone, rebase and
    ``git checkout`` all set mtimes in arbitrary order, so such a guard
    false-fires constantly and gets suppressed."

Every file in that argument is GIT-TRACKED. The comparison here has exactly one
tracked side. ``libsrmech.{so,dll,dylib}`` is an untracked BUILD ARTIFACT: git
never writes it, so its mtime is not scrambled by checkout — it is set by the
compiler and by nothing else. The failure mode the ban describes therefore
cannot arise on the artifact side, and the artifact side is the one that
decides. A checkout that scrambles the SOURCE mtimes forward can only produce
"source newer than lib", which is the state this hook asks you to resolve by
rebuilding — cheap, and correct anyway after a branch switch.

The tree's own regen runner reaches the same conclusion by a different route:
it calls the compiled-library staleness a WARNING it must not treat as a
failure, "because a pure / Pyodide checkout has no library at all and must stay
green". This hook honors that: **no library found is ALLOW, never block.**

SCOPE — three predicates, all required to fire
==============================================
1. The event is a Bash command that would TRUST the native path (pytest, ctest,
   parity, ripple_check, HAS_NATIVE), or a Stop.
2. At Stop only: ``git status --porcelain -- docs/srmech/c`` is non-empty, so a
   pure-Python session never sees this hook at all.
3. A built library exists and is OLDER than the newest ``c/src`` / ``c/include``
   source.

OVERRIDE
========
``SRMECH_ALLOW_STALE_NATIVE=1`` bypasses the block and the bypass is ECHOED to
stderr. Deliberately exercising the pure path with a stale lib present is
legitimate; doing it silently is not.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

#: Bash commands whose RESULT would be misread if the lib were stale.
TRUSTING = ("pytest", "ctest", "parity", "has_native", "ripple_check",
            "native_status", "cmake --build", "srmech_chain_run")

SOURCE_GLOBS = (("src", "*.c"), ("include", "*.h"))

LIB_NAMES = ("libsrmech.so", "libsrmech.dylib", "libsrmech.dll", "srmech.dll")

OVERRIDE = "SRMECH_ALLOW_STALE_NATIVE"


def _newest_source(croot: Path) -> Optional[Tuple[Path, float]]:
    best: Optional[Tuple[Path, float]] = None
    for sub, pat in SOURCE_GLOBS:
        d = croot / sub
        if not d.is_dir():
            continue
        for p in d.glob(pat):
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if best is None or m > best[1]:
                best = (p, m)
    return best


def _built_libs(root: Path) -> List[Tuple[Path, float]]:
    """Every built library the tree could load, with its mtime.

    Searched: the shipped shim package, and any ``build*`` directory beside the
    C sources. Missing directories are simply absent — a pure checkout yields
    an empty list and the hook allows.
    """
    out: List[Tuple[Path, float]] = []
    seen = set()
    roots = [H.py_root(root) / "srmech" / "_native",
             *sorted((root / "docs" / "srmech").glob("build*"))]
    for base in roots:
        if not base.is_dir():
            continue
        for name in LIB_NAMES:
            for p in base.rglob(name):
                rp = p.resolve()
                if rp in seen:
                    continue
                seen.add(rp)
                try:
                    out.append((p, p.stat().st_mtime))
                except OSError:
                    continue
    return out


def _stamp(t: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def _relevant(payload: Dict[str, Any], root: Path) -> bool:
    event = payload.get("hook_event_name") or ""
    if event in ("Stop", "SubagentStop"):
        code, out = H.git(["status", "--porcelain", "--", "docs/srmech/c"], cwd=root)
        return code == 0 and bool(out.strip())
    cmd = H.bash_command(payload).lower()
    if not cmd:
        return False
    return any(tok in cmd for tok in TRUSTING)


def body(payload: Dict[str, Any]) -> int:
    root = H.repo_root()
    croot = H.c_root(root)
    if not croot.is_dir():
        return H.allow()
    if not _relevant(payload, root):
        return H.allow()

    newest = _newest_source(croot)
    if newest is None:
        return H.allow()
    src_path, src_m = newest

    libs = _built_libs(root)
    if not libs:
        # Pure / Pyodide checkout: nothing to be stale. Never a failure.
        return H.allow()

    stale = [(p, m) for p, m in libs if m < src_m]
    if not stale:
        return H.allow()

    if os.environ.get(OVERRIDE) == "1":
        return H.allow([
            f"[stale-native] {OVERRIDE}=1 — BYPASSING a real staleness block. "
            f"{len(stale)} built lib(s) predate {src_path.name}. Any native "
            f"result from this command measures the OLD bytes."])

    lines = [
        "BLOCKED (stale-native-tripwire): a built libsrmech is OLDER than the C "
        "sources, so any native or parity result from this command would "
        "measure bytes that are not the ones in the tree.",
        f"  newest source : {src_path.relative_to(root)}  ({_stamp(src_m)})",
    ]
    for p, m in stale[:5]:
        lines.append(f"  stale library : {p.relative_to(root)}  ({_stamp(m)})")
    lines += [
        "",
        "The ABI check CANNOT see this: a stale lib built at the same ABI still "
        "reports HAS_NATIVE=True and ABI N == N.",
        "Rebuild first:  cmake --build build -- -k     (-k so you see EVERY "
        "error, not just the first)",
        "Then print _native.HAS_NATIVE, NATIVE_ABI_VERSION, EXPECTED_ABI_VERSION, "
        "LOAD_ERROR before trusting a parity number.",
        f"Deliberately testing the pure path? Set {OVERRIDE}=1 — the bypass is "
        "echoed, not silent.",
    ]
    return H.block(lines)


if __name__ == "__main__":
    H.run_hook(body)
