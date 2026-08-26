"""PreToolUse(Bash) + Stop — refuse to trust a parity result measured against a
stale ``libsrmech``. (rc452, `#T1166`)

WHAT IT CATCHES, MEASURED
=========================
The stale-artifact trap, hit FOUR times in this session alone: a library older
than ``c/src/*.c`` still reports ``HAS_NATIVE=True`` and ``ABI 22 == 22``. The
ABI check cannot see staleness — it compares a compiled-in integer against an
expected one, and a stale lib compiled at the same ABI answers correctly. Only
the clock distinguishes them.

⚠️ THE RE-DERIVATION — READ THIS BEFORE WIDENING THE ARTIFACT SET
=================================================================
As first shipped this hook was **unsatisfiable and expensive**, and both halves
were disqualifying. Measured on the real tree at rc452:

* **43 s per invocation**, twice in a row. The cause was
  ``(root/"docs"/"srmech").glob("build*")`` followed by ``rglob`` for four
  library names in each hit: **16 build directories, ~4800 files**, so roughly
  19 000 path traversals per call on a 9p mount. 43 s of tax on every Bash
  command is not a usable hook.
* **It blocked unconditionally and permanently.** Not because anything was
  stale — the library Python ACTUALLY LOADS was fresh:

      python/srmech/_native/libsrmech.so   2026-08-24 23:55:31   (loaded)
      c/src/srmech_compose_run.c           2026-08-24 16:02:43   (newest src)

  ``HAS_NATIVE=True``, ``NATIVE_ABI 22 == EXPECTED 22``, ``LOAD_ERROR None``.
  The block came entirely from **14 abandoned rc-numbered snapshot trees**
  (``build_rc41`` … ``build_rc46`` from 2026-06-05, ``build_rc342*`` /
  ``build_rc349`` / ``build_rc355`` / ``build_rc359`` / ``build_rc363`` from
  July) plus two alternate-config trees (``build-msvc``, ``build-ped``). No
  rebuild refreshes any of them, so the block could never be cleared — which is
  the definition of a hook that gets switched off within a day.
* **It blocked the rebuild its own message recommends.** ``cmake --build`` was
  in :data:`TRUSTING`, so ``cmake --build build -- -k`` — the literal remedy
  printed in the block text — was itself refused. A rebuild does not TRUST a
  native result; it PRODUCES one. That was a category error, not a tuning
  problem.

The repair is to **ask the question the LOADER asks**. ``_native._find_library``
resolves ``srmech.__path__`` entries to ONE directory, ``srmech/_native/``, and
returns the first platform-named hit in it — it never consults a ``build*``
directory at all. So the set of libraries whose staleness can affect a Python
result has exactly one member, and ``ctest`` — which links against the CMake
tree instead — adds exactly one more, the canonical ``build/``. Naming those
two directories explicitly is both the correct predicate and a ~60x cost cut.

SCOPE — what is checked, and against what
=========================================
The artifact set is chosen BY THE COMMAND, because the two consumers load from
different places:

* ``ctest`` / ``cmake --test`` → :data:`CTEST_DIR` (``docs/srmech/build``),
  the tree those binaries link against.
* everything else that trusts the native path (pytest, parity, ``ripple_check``,
  ``native_status``, ``has_native``, ``srmech_chain_run``) →
  :data:`LOADED_DIR` (``python/srmech/_native``), which is what the loader reads.
* a Stop → both, since a session may have exercised either.

Rebuild commands (``cmake`` / ``make`` / ``ninja`` as the INVOKED program, not
merely mentioned) are exempt outright, in any position of a compound: in
``cmake --build build && pytest``, the rebuild runs first and the library the
pytest sees is by construction fresh.

**Deliberately NOT scanned:** ``build-*`` and ``build_rc*``. Their staleness
cannot affect any result, and including them is what made the shipped hook
permanently red. If a real second live build tree ever appears, add it to
:data:`EXTRA_BUILD_DIRS` by name — never re-introduce a ``build*`` glob.

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

COST
====
Measured with ``--selftest`` on the real tree: the predicate itself is a
handful of ``stat`` calls plus one ``os.scandir`` pass over ``c/src`` +
``c/include`` (139 files), with an early exit as soon as one source is found
newer than the oldest relevant library. ``os.scandir`` replaces the shipped
``Path.glob`` + per-file ``Path.stat`` because it reuses the directory entry
and measured 361 ms against 815 ms for the same 139 files.

At Stop the ``git status`` narrowing is evaluated LAST rather than first. It can
only ever make the hook allow MORE, so the verdict is identical either way —
but it costs 2.4-8.1 s on this mount and is now paid only on the rare path
where the mtime check has already decided to block.

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
#: ``cmake --build`` is deliberately ABSENT — see the re-derivation note.
TRUSTING = ("pytest", "ctest", "parity", "has_native", "ripple_check",
            "native_status", "srmech_chain_run")

#: Commands that PRODUCE a library rather than trusting one. Matched as the
#: invoked program of a segment, so ``echo "cmake --build"`` does not exempt.
REBUILD_PROGRAMS = ("cmake", "make", "ninja", "gmake", "msbuild")

#: Substrings that select the ctest artifact set rather than the loaded one.
CTEST_TOKENS = ("ctest", "cmake --test", "ctest.exe")

SOURCE_DIRS = (("src", ".c"), ("include", ".h"))

#: The directory ``_native._find_library`` actually reads, relative to
#: ``docs/srmech/python``.
LOADED_DIR = ("srmech", "_native")

#: The canonical CMake tree ``ctest`` binaries link against, relative to
#: ``docs/srmech``. NOT a glob — see the re-derivation note.
CTEST_DIR = "build"

#: Additional live build trees, by NAME. Empty by design.
EXTRA_BUILD_DIRS: Tuple[str, ...] = ()

OVERRIDE = "SRMECH_ALLOW_STALE_NATIVE"


def _lib_names() -> Tuple[str, ...]:
    """Mirror ``_native._candidate_lib_names()`` — plus the other platforms'
    names, because a Windows-built ``srmech.dll`` sitting in the loaded
    directory is still a stale artifact worth naming."""
    return ("libsrmech.so", "libsrmech.dylib", "srmech.dll", "libsrmech.dll")


def _libs_in(directory: Path) -> List[Tuple[Path, float]]:
    """Platform-named libraries directly in ``directory`` (no recursion), with
    their mtimes. A missing directory yields an empty list."""
    out: List[Tuple[Path, float]] = []
    for name in _lib_names():
        p = directory / name
        try:
            out.append((p, p.stat().st_mtime))
        except OSError:
            continue
    return out


def _artifact_dirs(root: Path, *, ctest: bool, loaded: bool) -> List[Path]:
    dirs: List[Path] = []
    sr = root / "docs" / "srmech"
    if loaded:
        dirs.append(H.py_root(root).joinpath(*LOADED_DIR))
    if ctest:
        dirs.append(sr / CTEST_DIR)
        # ctest on Windows/multi-config puts the binary one level deeper.
        dirs.append(sr / CTEST_DIR / "Release")
        dirs.extend(sr / d for d in EXTRA_BUILD_DIRS)
    return dirs


def _newer_source_than(croot: Path, threshold: float) -> Optional[Tuple[Path, float]]:
    """The first ``c/src`` / ``c/include`` file newer than ``threshold``.

    Early-exits on the first hit — in the stale case (the only one that
    blocks) there is no reason to keep scanning.
    """
    for sub, ext in SOURCE_DIRS:
        d = croot / sub
        if not d.is_dir():
            continue
        try:
            with os.scandir(d) as it:
                for entry in it:
                    if not entry.name.endswith(ext):
                        continue
                    try:
                        m = entry.stat().st_mtime
                    except OSError:
                        continue
                    if m > threshold:
                        return Path(entry.path), m
        except OSError:
            continue
    return None


def _stamp(t: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def _is_rebuild(cmd: str) -> bool:
    """True when any segment INVOKES a build program."""
    for seg in H.split_segments(cmd):
        try:
            import shlex
            toks = shlex.split(seg, posix=True)
        except ValueError:
            toks = seg.split()
        i = 0
        while i < len(toks):
            t = toks[i]
            if "=" in t and not t.startswith("-") and t.split("=", 1)[0].isidentifier():
                i += 1
                continue
            if t in ("sudo", "env", "time", "nohup", "exec"):
                i += 1
                continue
            break
        if i < len(toks):
            prog = Path(toks[i]).name.lower()
            if prog.removesuffix(".exe") in REBUILD_PROGRAMS:
                return True
    return False


def _scope(payload: Dict[str, Any]) -> Optional[Tuple[bool, bool]]:
    """``(check_ctest, check_loaded)``, or ``None`` when out of scope."""
    event = payload.get("hook_event_name") or ""
    if event in ("Stop", "SubagentStop"):
        if H.stop_is_repeat(payload):
            return None
        return (True, True)
    cmd = H.bash_command(payload).lower()
    if not cmd:
        return None
    if _is_rebuild(cmd):
        return None
    if not any(tok in cmd for tok in TRUSTING):
        return None
    ctest = any(tok in cmd for tok in CTEST_TOKENS)
    return (ctest, not ctest)


def _evaluate(root: Path, check_ctest: bool, check_loaded: bool):
    """``(stale_libs, source_path, source_mtime)`` or ``None`` if fresh."""
    croot = H.c_root(root)
    if not croot.is_dir():
        return None
    libs: List[Tuple[Path, float]] = []
    for d in _artifact_dirs(root, ctest=check_ctest, loaded=check_loaded):
        libs.extend(_libs_in(d))
    if not libs:
        # Pure / Pyodide checkout, or an unbuilt tree: nothing to be stale.
        return None
    oldest = min(m for _, m in libs)
    hit = _newer_source_than(croot, oldest)
    if hit is None:
        return None
    src_path, src_m = hit
    stale = [(p, m) for p, m in libs if m < src_m]
    if not stale:
        return None
    return stale, src_path, src_m


def body(payload: Dict[str, Any]) -> int:
    scope = _scope(payload)
    if scope is None:
        return H.allow()
    root = H.repo_root()
    verdict = _evaluate(root, *scope)
    if verdict is None:
        return H.allow()
    stale, src_path, src_m = verdict

    # NARROWING, EVALUATED LAST. A Stop in a session that touched no C source
    # is not this hook's business; the check costs 2.4-8.1 s on this mount, so
    # it is paid only once the cheap predicate has already decided to block.
    #
    # ⚠️ rc455: this narrowing read ``git status --porcelain -- docs/srmech/c``,
    # which is not a platform-independent question on this checkout — WSL git
    # reports every CRLF working file modified against its LF blob and the
    # narrowing then never narrows. It is now a CONTENT difference
    # (``_hooklib.dirty_paths``), measured identical under both gits. The
    # verdict only ever moves toward ALLOW, so the repair cannot introduce a
    # false block; what it removes is a false FAILURE TO NARROW.
    event = payload.get("hook_event_name") or ""
    if event in ("Stop", "SubagentStop"):
        if not H.dirty_paths(root, ["docs/srmech/c"]):
            return H.allow()

    if os.environ.get(OVERRIDE) == "1":
        return H.allow([
            f"[stale-native] {OVERRIDE}=1 — BYPASSING a real staleness block. "
            f"{len(stale)} loadable lib(s) predate {src_path.name}. Any native "
            f"result from this command measures the OLD bytes."])

    try:
        shown_src = src_path.relative_to(root)
    except ValueError:
        shown_src = src_path
    lines = [
        "BLOCKED (stale-native-tripwire): the libsrmech this command would "
        "LOAD is OLDER than the C sources, so any native or parity result "
        "from it would measure bytes that are not the ones in the tree.",
        f"  newer source  : {shown_src}  ({_stamp(src_m)})",
    ]
    for p, m in stale[:5]:
        try:
            shown = p.relative_to(root)
        except ValueError:
            shown = p
        lines.append(f"  stale library : {shown}  ({_stamp(m)})")
    lines += [
        "",
        "The ABI check CANNOT see this: a stale lib built at the same ABI still "
        "reports HAS_NATIVE=True and ABI N == N.",
        "Rebuild first (this hook does NOT block a build command):",
        "    cmake --build build -- -k     (-k so you see EVERY error, not "
        "just the first)",
        "Then print _native.HAS_NATIVE, NATIVE_ABI_VERSION, EXPECTED_ABI_VERSION, "
        "LOAD_ERROR before trusting a parity number.",
        f"Deliberately testing the pure path? Set {OVERRIDE}=1 — the bypass is "
        "echoed, not silent.",
    ]
    return H.block(lines)


def selftest() -> int:
    """Print the artifact set and the verdict, with timings.

    The shipped hook's two defects were both invisible from its exit status:
    a permanent block looks like a working block, and 43 s looks like a slow
    machine. Both are printed here.
    """
    root = H.repo_root()
    t0 = time.perf_counter()
    for label, (ct, ld) in (("Bash(pytest)", (False, True)),
                            ("Bash(ctest)", (True, False)),
                            ("Stop", (True, True))):
        t = time.perf_counter()
        dirs = _artifact_dirs(root, ctest=ct, loaded=ld)
        libs = [(p, m) for d in dirs for p, m in _libs_in(d)]
        verdict = _evaluate(root, ct, ld)
        dt = (time.perf_counter() - t) * 1000
        print(f"{label:14s} dirs={len(dirs)} libs={len(libs)} "
              f"verdict={'BLOCK' if verdict else 'allow'}  {dt:7.1f} ms")
        for p, m in libs:
            print(f"                 {_stamp(m)}  {p.relative_to(root)}")
    print(f"total predicate cost: {(time.perf_counter()-t0)*1000:.1f} ms")
    skipped = sorted(p.name for p in (root / "docs" / "srmech").glob("build*")
                     if p.is_dir() and p.name != CTEST_DIR
                     and p.name not in EXTRA_BUILD_DIRS)
    print(f"deliberately NOT scanned ({len(skipped)}): {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    H.run_hook(body)
