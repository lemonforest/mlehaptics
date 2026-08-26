"""Evaluate every srmech hook in BOTH directions. (rc452, `#T1166`)

    python tools/hooks/check_hooks.py             # all hooks
    python tools/hooks/check_hooks.py ssot        # substring-filtered

⚠️ ``python`` and NOT ``python3``: two different 3.14 installs answer those two
names on this machine (``C:\\Python314\\python.exe`` 3.14.4 vs a WindowsApps
shim at ``…\\Local\\Python\\pythoncore-3.14-64`` 3.14.3), resolved by PATH order.
Every figure in ``README.md`` was measured under the first. Sub-invocations use
``sys.executable``, so whichever you launch with is the one under test.

WHY THIS FILE EXISTS, AND WHY IT IS NOT NAMED ``test_*``
========================================================
A hook nobody has watched BLOCK has not been shown to work, and a hook nobody
has watched ALLOW has not been shown to be safe to enable. Each case below
therefore asserts an exact exit status — 2 for block, 0 for allow — against a
fixture that is described in the case name.

The name avoids ``test_`` deliberately. These hooks are delivered WRITTEN BUT
NOT ACTIVATED, and a ``test_*.py`` under ``tools/`` would be swept into the
suite by a bare ``pytest`` run, perturbing pinned collection counts in a slice
whose mandate is not to change the suite. Move it into ``tests/`` when the
hooks are switched on.

FIXTURE POLICY — REAL WHERE REAL EXISTS
=======================================
Two cases use the live tree because a real fixture beats a contrived one:

* ``ratchet-recount`` PASSES against this rc's genuine adjudicated state
  (``CEIL_CONFLATING_RETURN_LINES = 745``, measured 745, green) and BLOCKS
  against a genuinely planted ``return SRMECH_ERR_OVERFLOW;`` in a temporary
  ``c/src`` file, which is removed in a ``finally``.
* ``ssot-agreement`` BLOCKS against the tree exactly as it stands: at rc452
  ``python/README.md`` says "**ABI 21** at this release" while the macro says
  22. Nothing is planted. If that is repaired, this case flips to a
  self-announcing skip rather than silently passing.

Everything else runs against purpose-built fixture trees pointed at by
``CLAUDE_PROJECT_DIR`` — the harness's own variable — so the real repo is never
mutated.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

HOOKS = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS))
import _hooklib as H  # noqa: E402

REPO = H.repo_root()
PY = H.py_root(REPO)

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
_results: List[Tuple[str, str, str]] = []


# ── invocation ────────────────────────────────────────────────────────────

def invoke(script: str, payload: Dict[str, Any], *,
           project_dir: Optional[Path] = None,
           env_extra: Optional[Dict[str, str]] = None,
           timeout: float = 300.0) -> Tuple[int, str]:
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir or REPO)
    env.pop("SRMECH_ALLOW_STALE_NATIVE", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload).encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, timeout=timeout,
    )
    return proc.returncode, proc.stderr.decode("utf-8", "replace")


def case(name: str, script: str, payload: Dict[str, Any], expect: int,
         contains: Optional[str] = None, **kw) -> None:
    """Assert an exit status, and optionally that stderr NAMES something.

    ``contains`` is what turns "it blocked" into "it blocked FOR THIS REASON".
    Without it a fixture pair only proves the verdict logic — the exact
    insufficiency this file's README retracts — because a hook can block for a
    reason unrelated to the plant and look identical from outside.
    """
    try:
        code, err = invoke(script, payload, **kw)
    except Exception as exc:
        _results.append((name, FAIL, f"invocation raised {type(exc).__name__}: {exc}"))
        return
    if code != expect:
        _results.append((name, FAIL,
                         f"expected exit {expect}, got {code}. stderr: "
                         + " / ".join(err.strip().splitlines()[:3])))
        return
    if contains is not None and contains not in err:
        _results.append((name, FAIL,
                         f"exit {code} as expected, but stderr does not name "
                         f"{contains!r}: "
                         + " / ".join(err.strip().splitlines()[:3])))
        return
    first = (err.strip().splitlines() or [""])[0][:96]
    detail = f"exit {code} — {first}" if first else f"exit {code}"
    if contains is not None:
        detail += f"   [names {contains!r}]"
    _results.append((name, PASS, detail))


def skip(name: str, why: str) -> None:
    _results.append((name, SKIP, why))


def _cost_case(name: str, script: str, payload: Dict[str, Any],
               ceiling_s: float, **kw) -> None:
    """Assert an invocation finishes under ``ceiling_s``.

    Correctness is not the only way a hook fails. ``stale_native_tripwire``
    cost 43 s per Bash call as shipped, which no one would keep enabled, and
    its exit status said nothing about that. A wall-clock assertion is the
    only thing that can see it.
    """
    try:
        start = time.perf_counter()
        invoke(script, payload, **kw)
        dt = time.perf_counter() - start
    except Exception as exc:
        _results.append((name, FAIL, f"invocation raised {type(exc).__name__}: {exc}"))
        return
    status = PASS if dt < ceiling_s else FAIL
    _results.append((name, status,
                     f"{dt*1000:.0f} ms against a {ceiling_s*1000:.0f} ms ceiling"))


def _selftest_case(name: str, script: str, must_contain: str) -> None:
    """Run a hook's ``--selftest`` and require a population line.

    This is the vacuity check. ``generated_file_edit_blocker``'s manifest
    predicate returned ``[]`` on every invocation for its whole shipped life,
    and no exit status could reveal it: a dead predicate and a satisfied one
    both exit 0 on a hand-written file. Only the POPULATION distinguishes them.
    """
    proc = subprocess.run(
        [sys.executable, str(HOOKS / script), "--selftest"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(REPO)}, timeout=120)
    out = proc.stdout.decode("utf-8", "replace")
    if proc.returncode == 0 and must_contain in out:
        _results.append((name, PASS, must_contain))
    else:
        _results.append((name, FAIL,
                         f"exit {proc.returncode}; wanted {must_contain!r} in: "
                         + " / ".join(out.strip().splitlines()[:3])))


# ── fixture builders ──────────────────────────────────────────────────────

def _write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _git(args: List[str], cwd: Path) -> Tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=str(cwd),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q", "-b", "main"], root)
    _git(["config", "user.email", "hooks@example.invalid"], root)
    _git(["config", "user.name", "hook fixture"], root)


def _commit(root: Path, msg: str) -> None:
    _git(["add", "-A"], root)      # safe: throwaway fixture repo, not the real tree
    _git(["-c", "commit.gpgsign=false", "commit", "-q", "-m", msg], root)


# ── 1. ratchet-recount ────────────────────────────────────────────────────

def check_ratchet_recount() -> None:
    gate = PY / "tests" / "test_status_conflation_ratchet_rc404.py"
    if not gate.is_file():
        skip("ratchet-recount", "gate file absent")
        return

    case("ratchet-recount ALLOWS this rc's real adjudicated state (CEIL==measured)",
         "ratchet_recount.py", {"hook_event_name": "Stop"}, 0)

    planted = REPO / "docs" / "srmech" / "c" / "src" / "_hook_fixture_rc452.c"
    gate_before = gate.read_bytes()
    try:
        _write(planted,
               "/* TEMPORARY fixture written by tools/hooks/check_hooks.py.\n"
               "   Removed in a finally. A live return below RAISES the\n"
               "   tree-wide count above CEIL_CONFLATING_RETURN_LINES. */\n"
               "#include \"srmech.h\"\n"
               "int _hook_fixture_rc452(void) {\n"
               "    return SRMECH_ERR_OVERFLOW;\n"
               "}\n")
        case("ratchet-recount BLOCKS a planted un-adjudicated OVERFLOW return",
             "ratchet_recount.py", {"hook_event_name": "Stop"}, 2)
        case("ratchet-recount ALLOWS a repeat stop even while RED (loop guard)",
             "ratchet_recount.py",
             {"hook_event_name": "Stop", "stop_hook_active": True}, 0)

        # THE DISTINCTION THE HOOK EXISTS TO DRAW. Same planted line, now
        # ADJUDICATED: the ceiling constant is raised to meet the measured
        # count, which is the tree's own marker for "an agent accounted for
        # this". The gate goes green and the hook must allow. Nothing here is
        # an honor system — the marker IS the constant, and the gate asserts
        # equality in both directions, so it cannot be satisfied by a raise
        # that overshoots either.
        _raise_ceiling(gate, +1)
        case("ratchet-recount ALLOWS the SAME rise once the ceiling is "
             "adjudicated up to meet it",
             "ratchet_recount.py", {"hook_event_name": "Stop"}, 0)

        # And an OVERSHOOT is still red: the gate's second assertion forbids a
        # ceiling above the measured count, so "just add slack" is not an exit.
        _raise_ceiling(gate, +1)
        case("ratchet-recount BLOCKS a ceiling raised BEYOND the measured "
             "count (slack is not adjudication)",
             "ratchet_recount.py", {"hook_event_name": "Stop"}, 2)
    finally:
        planted.unlink(missing_ok=True)
        gate.write_bytes(gate_before)


_CEIL_NAME = "CEIL_CONFLATING_RETURN_LINES"


def _raise_ceiling(gate: Path, delta: int) -> None:
    """Bump the ratchet's ceiling constant by ``delta``, in place."""
    import re as _re
    text = gate.read_text(encoding="utf-8")
    m = _re.search(rf"(?m)^{_CEIL_NAME} = (\d+)$", text)
    if not m:
        raise RuntimeError(f"could not find {_CEIL_NAME} to adjust")
    new = int(m.group(1)) + delta
    gate.write_text(
        text[:m.start()] + f"{_CEIL_NAME} = {new}" + text[m.end():],
        encoding="utf-8", newline="",
    )


# ── 2. stale-native-tripwire ──────────────────────────────────────────────

def _native_fixture(tmp: Path, lib_older: bool, with_lib: bool = True,
                    abandoned_build: bool = False,
                    build_lib_older: Optional[bool] = None) -> Path:
    """A minimal tree carrying the three artifact locations that matter.

    ``abandoned_build`` plants an ancient ``build_rc342/libsrmech.so`` — the
    shape that made the shipped hook permanently unsatisfiable on the real
    tree, where 14 such rc-numbered snapshots (oldest 2026-06-05) sat beside
    a genuinely fresh loaded library. No rebuild can ever refresh them, so a
    hook that reads them can never go green.
    """
    root = tmp / "repo"
    src = _write(root / "docs/srmech/c/src/srmech_core.c", "int x(void){return 0;}\n")
    _write(root / "docs/srmech/c/include/srmech.h", "#define SRMECH_ABI_VERSION 22\n")
    now = time.time()
    os.utime(src, (now, now))
    if with_lib:
        lib = _write(root / "docs/srmech/python/srmech/_native/libsrmech.so", "ELF\n")
        os.utime(lib, (now - 600, now - 600) if lib_older else (now + 600, now + 600))
    if build_lib_older is not None:
        b = _write(root / "docs/srmech/build/libsrmech.so", "ELF\n")
        os.utime(b, (now - 600, now - 600) if build_lib_older else (now + 600, now + 600))
    if abandoned_build:
        old = _write(root / "docs/srmech/build_rc342/libsrmech.so", "ELF\n")
        os.utime(old, (now - 5_000_000, now - 5_000_000))
    return root


def check_stale_native() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        stale = _native_fixture(tmp / "a", lib_older=True)
        fresh = _native_fixture(tmp / "b", lib_older=False)
        pure = _native_fixture(tmp / "c", lib_older=True, with_lib=False)

        pytest_cmd = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                      "tool_input": {"command": "PYTHONPATH=. pytest tests/ -q"}}

        case("stale-native BLOCKS pytest when the LOADED lib predates c/src",
             "stale_native_tripwire.py", pytest_cmd, 2, project_dir=stale)
        case("stale-native ALLOWS pytest when the lib is newer",
             "stale_native_tripwire.py", pytest_cmd, 0, project_dir=fresh)
        case("stale-native ALLOWS a pure checkout with no library at all",
             "stale_native_tripwire.py", pytest_cmd, 0, project_dir=pure)
        case("stale-native ALLOWS a non-native command (ls) with a stale lib",
             "stale_native_tripwire.py",
             {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": "ls -la docs"}}, 0, project_dir=stale)
        case("stale-native ALLOWS with the documented override set",
             "stale_native_tripwire.py", pytest_cmd, 0, project_dir=stale,
             env_extra={"SRMECH_ALLOW_STALE_NATIVE": "1"})

        # ── the two defects this hook shipped with ────────────────────────
        # 1. It read every ``build*`` directory, so 14 abandoned rc snapshots
        #    that nothing can load and no rebuild refreshes held it red
        #    forever, while the library actually loaded was fresh.
        abandoned = _native_fixture(tmp / "d", lib_older=False,
                                    abandoned_build=True)
        case("stale-native ALLOWS a fresh LOADED lib beside an abandoned "
             "build_rc342 snapshot (the permanent-block regression)",
             "stale_native_tripwire.py", pytest_cmd, 0, project_dir=abandoned)

        # 2. It listed ``cmake --build`` as a command that TRUSTS the native
        #    path, so the rebuild printed in its own block message was itself
        #    refused. A hook that cannot be satisfied gets disabled.
        for cmd in ("cmake --build build -- -k",
                    "cmake --build build && PYTHONPATH=. pytest tests/ -q",
                    "make -C build",
                    "ninja -C build"):
            case(f"stale-native ALLOWS the rebuild path: {cmd[:38]}",
                 "stale_native_tripwire.py",
                 {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                  "tool_input": {"command": cmd}}, 0, project_dir=stale)

        # ...but a MENTION of cmake must not launder a trusting command.
        case("stale-native BLOCKS pytest that merely MENTIONS cmake in a string",
             "stale_native_tripwire.py",
             {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": 'echo "run cmake --build first"; pytest -q'}},
             2, project_dir=stale)

        # The artifact set is chosen BY THE COMMAND: ctest links against
        # build/, pytest loads srmech/_native/. A stale one must not
        # implicate the other in either direction.
        ct = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": "cd build && ctest --output-on-failure"}}
        split = _native_fixture(tmp / "e", lib_older=False, build_lib_older=True)
        case("stale-native BLOCKS ctest when build/ is stale though the "
             "loaded lib is fresh", "stale_native_tripwire.py", ct, 2,
             project_dir=split)
        case("stale-native ALLOWS pytest in that same tree (different artifact)",
             "stale_native_tripwire.py", pytest_cmd, 0, project_dir=split)

        # COST is the other disqualifying half: 43 s per Bash call is not a
        # usable tax. This ceiling is ~8x the measured 0.4-0.7 s and ~1/8 of
        # the shipped cost, so it separates the two without being brittle.
        _cost_case("stale-native costs well under the 5 s usability ceiling",
                   "stale_native_tripwire.py", pytest_cmd, 5.0)


# ── 3. git-add-all-blocker ────────────────────────────────────────────────

def check_git_add_all() -> None:
    def bash(cmd: str) -> Dict[str, Any]:
        return {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": cmd}}

    for cmd in ("git add -A",
                "git add --all",
                "git add .",
                "git commit -am 'wip'",
                "cd docs/srmech/python && git add -A"):
        case(f"git-add-all BLOCKS: {cmd}", "git_add_all_blocker.py", bash(cmd), 2)

    for cmd in ("git add docs/srmech/python/srmech/math/rational.py",
                "git add -u",
                "git status --porcelain",
                'echo "never run git add -A here"',
                "git commit -m 'explicit paths only'"):
        case(f"git-add-all ALLOWS: {cmd}", "git_add_all_blocker.py", bash(cmd), 0)


# ── 4. generated-file-edit-blocker ────────────────────────────────────────

def check_generated_edit() -> None:
    def edit(path: Path) -> Dict[str, Any]:
        return {"hook_event_name": "PreToolUse", "tool_name": "Edit",
                "tool_input": {"file_path": str(path)}}

    # THE VACUITY CHECK. The manifest predicate returned [] on every
    # invocation as shipped — a dataclass in codegen_manifest.py raised
    # because the module was never put in sys.modules, and a bare
    # `except Exception: return []` swallowed it. The hook ran on its banner
    # alone and no exit status could show that.
    _selftest_case("generated-edit manifest predicate is NON-EMPTY (vacuity)",
                   "generated_file_edit_blocker.py",
                   "manifest predicate population: 6")

    gen = PY / "srmech" / "introspect" / "_tool_docs.py"
    if gen.is_file():
        case("generated-edit BLOCKS a hand-edit to _tool_docs.py",
             "generated_file_edit_blocker.py", edit(gen), 2)
    else:
        skip("generated-edit BLOCKS _tool_docs.py", "generated file absent")

    reg = REPO / "docs" / "srmech" / "c" / "src" / "srmech_tool_registry.c"
    if reg.is_file():
        case("generated-edit BLOCKS a hand-edit to srmech_tool_registry.c",
             "generated_file_edit_blocker.py", edit(reg), 2)

    # THE FILE THE SHIPPED HOOK MISSED. `_c_claims.py` is a real regen_all
    # output that spells its banner in lower case, so neither predicate saw
    # it: the manifest was dead and the banner match was case-SENSITIVE.
    # Measured against the HEAD hook: exit 0. It ships in the wheel and
    # reaches users through describe(), MCP and the compiled-in C registry.
    claims = PY / "srmech" / "introspect" / "_c_claims.py"
    if claims.is_file():
        case("generated-edit BLOCKS _c_claims.py — the output the shipped "
             "hook ALLOWED (manifest dead + lowercase banner)",
             "generated_file_edit_blocker.py", edit(claims), 2)

    # An EXCLUDED-generator output: not in the manifest, lowercase banner,
    # so it exercises the banner predicate alone. Also exit 0 at HEAD.
    fold = PY / "srmech" / "math" / "_unicode_fold_tables.py"
    if fold.is_file():
        case("generated-edit BLOCKS an EXCLUDED-generator output via the "
             "banner alone: _unicode_fold_tables.py",
             "generated_file_edit_blocker.py", edit(fold), 2)

    # THE FALSE POSITIVE THE CONJUNCTION REMOVES. This file's third line is
    # the prose "Do not edit srmech package files in this session." — a
    # sentence about OTHER files. A case-insensitive banner match ALONE would
    # block it; requiring "generated" as well does not.
    notes = REPO / "docs" / "srmech" / "rbs_nn_research" / "UPSTREAM_NOTES.md"
    if notes.is_file():
        case("generated-edit ALLOWS prose that says 'do not edit' but is not "
             "a generated-file banner: UPSTREAM_NOTES.md",
             "generated_file_edit_blocker.py", edit(notes), 0)

    # Documented exemption: its own banner licenses hand-curated rows.
    carrier = PY / "srmech" / "introspect" / "_carrier_examples.py"
    if carrier.is_file():
        case("generated-edit ALLOWS _carrier_examples.py (banner licenses "
             "hand-curation) and says so",
             "generated_file_edit_blocker.py", edit(carrier), 0)

    for p, label in ((PY / "srmech" / "math" / "rational.py", "a hand-written module"),
                     (PY / "tools" / "gen_tool_docs.py", "the GENERATOR itself"),
                     (PY / "tools" / "gen_c_claims.py", "the generator of _c_claims"),
                     (PY / "tests" / "test_status_conflation_ratchet_rc404.py", "a test")):
        if p.is_file():
            case(f"generated-edit ALLOWS {label}: {p.name}",
                 "generated_file_edit_blocker.py", edit(p), 0)


# ── 5. ssot-agreement ─────────────────────────────────────────────────────

def _ssot_fixture(tmp: Path, abi: int = 22, ver: str = "0.9.0rc452",
                  readme_abi: Optional[int] = None) -> Path:
    root = tmp / "repo"
    r_abi = abi if readme_abi is None else readme_abi
    _write(root / "docs/srmech/python/pyproject.toml", f'[project]\nversion = "{ver}"\n')
    _write(root / "docs/srmech/python/pyproject-pure.toml", f'[project]\nversion = "{ver}"\n')
    _write(root / "docs/srmech/python/srmech/version.py", f'__version__ = "{ver}"\n')
    _write(root / "docs/srmech/c/include/srmech.h",
           f'#define SRMECH_VERSION "{ver}"\n#define SRMECH_ABI_VERSION {abi}\n')
    _write(root / "docs/srmech/python/tests/test_signal_processing_scaffolding.py",
           f'assert srmech.__version__ == "{ver}"\n')
    _write(root / "docs/srmech/python/srmech/_native/__init__.py",
           f"EXPECTED_ABI_VERSION: int = {abi}\n")
    _write(root / "docs/srmech/CLAUDE.md",
           f"C ABI version is currently **{abi}** (`SRMECH_ABI_VERSION = {abi}` in\n")
    _write(root / "docs/srmech/c/README.md",
           f"C ABI version is **{abi}** (`SRMECH_ABI_VERSION {abi}` in\n")
    _write(root / "docs/srmech/python/README.md",
           f"its ABI matched (**ABI {r_abi}** at this release — ...)\n")
    return root


def check_ssot_agreement() -> None:
    stop = {"hook_event_name": "Stop"}
    commit = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": "git commit -m 'rc452'"}}

    # REAL fixture: the tree as it stands. python/README.md says ABI 21; macro says 22.
    readme = PY / "README.md"
    header = REPO / "docs" / "srmech" / "c" / "include" / "srmech.h"
    real_disagrees = False
    if readme.is_file() and header.is_file():
        import re
        m1 = re.search(r"\*\*ABI (\d+)\*\* at this release",
                       readme.read_text(encoding="utf-8", errors="replace"))
        m2 = re.search(r"#define\s+SRMECH_ABI_VERSION\s+(\d+)",
                       header.read_text(encoding="utf-8", errors="replace"))
        real_disagrees = bool(m1 and m2 and m1.group(1) != m2.group(1))
    if real_disagrees:
        case("ssot-agreement BLOCKS the REAL tree (README ABI 21 vs macro 22)",
             "ssot_agreement.py", stop, 2)
        case("ssot-agreement BLOCKS a real `git commit` while surfaces disagree",
             "ssot_agreement.py", commit, 2)
    else:
        skip("ssot-agreement BLOCKS the REAL tree",
             "the ABI prose lag has been repaired — re-plant a fixture to re-verify")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        good = _ssot_fixture(tmp / "good")
        bad_abi = _ssot_fixture(tmp / "bad_abi", readme_abi=21)
        bad_ver = _ssot_fixture(tmp / "bad_ver")
        _write(bad_ver / "docs/srmech/python/srmech/version.py",
               '__version__ = "0.9.0rc451"\n')

        case("ssot-agreement ALLOWS a fully agreeing tree",
             "ssot_agreement.py", stop, 0, project_dir=good)
        case("ssot-agreement BLOCKS a planted ABI prose lag (21 vs 22)",
             "ssot_agreement.py", stop, 2, project_dir=bad_abi)
        case("ssot-agreement BLOCKS a planted version disagreement",
             "ssot_agreement.py", stop, 2, project_dir=bad_ver)
        case("ssot-agreement ALLOWS a non-commit Bash command",
             "ssot_agreement.py",
             {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": "ls"}}, 0, project_dir=bad_abi)
        case("ssot-agreement ALLOWS a repeat stop (loop guard)",
             "ssot_agreement.py",
             {"hook_event_name": "Stop", "stop_hook_active": True}, 0,
             project_dir=bad_abi)


# ── 6. derived-ledger-freshness ───────────────────────────────────────────

def _ledger_fixture(tmp: Path) -> Path:
    root = tmp / "repo"
    _init_repo(root)
    _write(root / "docs/srmech/python/srmech/math/rational.py",
           "def rational_mul(a, b):\n    return (a[0] * b[0], a[1] * b[1])\n")
    _write(root / "docs/srmech/python/srmech/amsc/catalog.py", "X = 1\n")
    rows = [
        {"n": 2, "record": "meta", "native": True, "python": "3.10"},
        {"name": "srmech.math.rational.rational_mul", "status": "ok",
         "src_sha256": "a" * 64},
        {"name": "srmech.math.rational.exp_series_truncate", "status": "ok",
         "src_sha256": "b" * 64},
        {"name": "srmech.amsc.catalog.get_attested_dataset", "status": "ok",
         "src_sha256": "c" * 64},
    ]
    _write(root / "docs/srmech/python/tests/worked_examples_result.ndjson",
           "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    _commit(root, "baseline: ledger written against these sources")
    return root


def check_ledger_freshness() -> None:
    stop = {"hook_event_name": "Stop"}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        clean = _ledger_fixture(tmp / "clean")
        case("ledger-freshness ALLOWS a ledger written against current sources",
             "derived_ledger_freshness.py", stop, 0, project_dir=clean)

        # The real defect, reproduced: the implementation flips, the SNIPPET does not.
        drift = _ledger_fixture(tmp / "drift")
        _write(drift / "docs/srmech/python/srmech/math/rational.py",
               "from srmech.math.q import Q\n\n"
               "def rational_mul(a, b):\n"
               "    return Q(a[0] * b[0], a[1] * b[1])   # no longer subscriptable\n")
        case("ledger-freshness BLOCKS after an implementation flip "
             "(the case src_sha256 CANNOT see)",
             "derived_ledger_freshness.py", stop, 2, project_dir=drift)

        committed = _ledger_fixture(tmp / "committed")
        _write(committed / "docs/srmech/python/srmech/math/rational.py", "# changed\n")
        _commit(committed, "change rational.py without re-running the ledger")
        case("ledger-freshness BLOCKS when the drift is COMMITTED, not just dirty",
             "derived_ledger_freshness.py", stop, 2, project_dir=committed)

        other = _ledger_fixture(tmp / "other")
        _write(other / "docs/srmech/python/srmech/signal_processing.py", "Y = 2\n")
        case("ledger-freshness ALLOWS a change to a module NO ledger row uses",
             "derived_ledger_freshness.py", stop, 0, project_dir=other)

        repaired = _ledger_fixture(tmp / "repaired")
        _write(repaired / "docs/srmech/python/srmech/math/rational.py", "# changed\n")
        _write(repaired / "docs/srmech/python/tests/worked_examples_result.ndjson",
               json.dumps({"n": 0, "record": "meta"}) + "\n"
               + json.dumps({"name": "srmech.math.rational.rational_mul",
                             "status": "ok", "src_sha256": "d" * 64}) + "\n")
        _commit(repaired, "re-ran the ledger alongside the source change")
        case("ledger-freshness ALLOWS once the ledger is re-run and committed with it",
             "derived_ledger_freshness.py", stop, 0, project_dir=repaired)

        loop = _ledger_fixture(tmp / "loop")
        _write(loop / "docs/srmech/python/srmech/math/rational.py", "# changed\n")
        case("ledger-freshness ALLOWS a repeat stop (loop guard)",
             "derived_ledger_freshness.py",
             {"hook_event_name": "Stop", "stop_hook_active": True}, 0,
             project_dir=loop)


# ── 7. ripple-stamp-before-push ───────────────────────────────────────────

def _push_fixture(tmp: Path, *, op_touching: bool, msg: str = "rc452 work") -> Path:
    root = tmp / "repo"
    _init_repo(root)
    _write(root / "README.md", "seed\n")
    _commit(root, "seed")
    if op_touching:
        _write(root / "docs/srmech/python/srmech/math/rational.py", "# op change\n")
    else:
        _write(root / "docs/notes.md", "prose only\n")
    _commit(root, msg)
    return root


def _head(root: Path) -> str:
    return _git(["rev-parse", "HEAD"], root)[1].strip()


def check_ripple_stamp() -> None:
    push = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
            "tool_input": {"command": "git push origin HEAD"}}

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        unswept = _push_fixture(tmp / "unswept", op_touching=True)
        case("ripple-stamp BLOCKS an op-touching push with no stamp",
             "ripple_stamp_before_push.py", push, 2, project_dir=unswept)

        stamped = _push_fixture(tmp / "stamped", op_touching=True)
        _write(stamped / ".git" / "srmech_ripple_stamp.json",
               json.dumps({"sha": _head(stamped), "status": 0,
                           "finished_at": int(time.time()), "failed": 0}))
        case("ripple-stamp ALLOWS an op-touching push stamped green at HEAD",
             "ripple_stamp_before_push.py", push, 0, project_dir=stamped)

        moved = _push_fixture(tmp / "moved", op_touching=True)
        _write(moved / ".git" / "srmech_ripple_stamp.json",
               json.dumps({"sha": "0" * 40, "status": 0}))
        case("ripple-stamp BLOCKS when the stamp is for an older commit",
             "ripple_stamp_before_push.py", push, 2, project_dir=moved)

        red = _push_fixture(tmp / "red", op_touching=True)
        _write(red / ".git" / "srmech_ripple_stamp.json",
               json.dumps({"sha": _head(red), "status": 1, "failed": 12}))
        case("ripple-stamp BLOCKS when the recorded sweep FAILED",
             "ripple_stamp_before_push.py", push, 2, project_dir=red)

        pending = _push_fixture(tmp / "pending", op_touching=True,
                                msg="rc452 wip [ripple-pending]")
        case("ripple-stamp ALLOWS an incremental push admitting [ripple-pending]",
             "ripple_stamp_before_push.py", push, 0, project_dir=pending)

        prose = _push_fixture(tmp / "prose", op_touching=False)
        case("ripple-stamp ALLOWS a docs-only push with no stamp",
             "ripple_stamp_before_push.py", push, 0, project_dir=prose)

        case("ripple-stamp ALLOWS a non-push Bash command",
             "ripple_stamp_before_push.py",
             {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": "git status"}}, 0, project_dir=unswept)


# ── 8. jpl-audit-gate ─────────────────────────────────────────────────────
#
# THIRTEEN PLANTS, ONE PER PREDICATE. The README's retraction is the whole
# design brief for this section: "Watching a hook block and allow is necessary
# and not sufficient: it proves the verdict logic, not that each predicate is
# live." `test_jpl_audit.py` carries THIRTEEN check functions, and a fixture
# pair exercising one of them would say nothing about the other twelve — which
# is exactly how `generated_file_edit_blocker` shipped with a dead predicate
# and a clean bill of health.
#
# So each plant below targets ONE named check, and `contains=` requires the
# hook's block message to NAME that check. Overlap is expected and tolerated
# (planting a goto also adds a 0-assert function unless you write the asserts
# in); what is asserted is that the named predicate FIRED, not that it fired
# alone. A predicate that can never fire cannot satisfy its row.
#
# The fixture is a COPY of the real c/ tree plus the real audit file, in its
# own git repo. It has to be the real tree: the seeded populations are exact
# (9 recursion cycles, 10 function-pointer sites, 12 Rule-4 rows measured to
# the line), and `*_ceiling_is_not_slack` asserts EQUALITY, so a toy C tree
# cannot produce a green baseline without doctoring the gate — and a doctored
# gate is not the gate.

_JPL = "jpl_audit_gate.py"
_JPL_TARGET = "docs/srmech/c/src/srmech_meta.c"
_JPL_AUDIT_REL = "docs/srmech/python/tests/test_jpl_audit.py"

#: The Rule-5-violating C file `check_hooks.py` itself plants into the REAL
#: `c/src` at line ~179. Reproduced verbatim as a fixture so the collision is
#: tested rather than hoped about.
_RATCHET_FIXTURE_NAME = "_hook_fixture_rc452.c"
_RATCHET_FIXTURE_BODY = (
    "/* TEMPORARY fixture written by tools/hooks/check_hooks.py. */\n"
    "#include \"srmech.h\"\n"
    "int _hook_fixture_rc452(void) {\n"
    "    return SRMECH_ERR_OVERFLOW;\n"
    "}\n")


def _jpl_fixture(dest: Path) -> Path:
    """A git repo holding the real C tree and the real audit file."""
    root = dest / "repo"
    _init_repo(root)
    shutil.copytree(REPO / "docs" / "srmech" / "c",
                    root / "docs" / "srmech" / "c", dirs_exist_ok=True)
    tests = root / "docs" / "srmech" / "python" / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PY / "tests" / "test_jpl_audit.py", tests / "test_jpl_audit.py")
    _commit(root, "jpl fixture: the real C tree, tracked")
    return root


def _long_c_function(name: str, body_lines: int) -> str:
    """A well-formed C function of a chosen length, carrying two asserts so it
    trips Rule 4 ALONE rather than Rule 4 and Rule 5 together."""
    inner = "\n".join(f"    x += {i % 7};" for i in range(body_lines))
    return (f"\nint {name}(int x)\n{{\n"
            f"    assert(x >= 0);\n    assert(x < 1000000);\n"
            f"{inner}\n    return x;\n}}\n")


#: ``(check name, how to plant it)``. ``plant`` receives the fixture root.
def _plants() -> "list[tuple[str, str, Callable[[Path], None]]]":
    def append_c(text: str):
        def go(root: Path) -> None:
            p = root / _JPL_TARGET
            p.write_text(p.read_text(encoding="utf-8") + text, encoding="utf-8",
                         newline="")
        return go

    def edit_audit(old: str, new: str):
        def go(root: Path) -> None:
            p = root / _JPL_AUDIT_REL
            t = p.read_text(encoding="utf-8")
            if old not in t:
                raise RuntimeError(f"audit fixture has no {old!r}")
            p.write_text(t.replace(old, new, 1), encoding="utf-8", newline="")
        return go

    def untrack(rel: str):
        def go(root: Path) -> None:
            _git(["rm", "--cached", "-q", "--", rel], root)
        return go

    def rename_in(rel: str, old: str, new: str):
        def go(root: Path) -> None:
            p = root / rel
            p.write_text(p.read_text(encoding="utf-8").replace(old, new),
                         encoding="utf-8", newline="")
        return go

    def drop_audit_doc(root: Path) -> None:
        (root / "docs" / "srmech" / "c" / "JPL_AUDIT.md").unlink()

    return [
        ("test_rule_1_no_goto", "a goto",
         append_c("\nint _hk_goto_probe(int x)\n{\n    assert(x >= 0);\n"
                  "    assert(x < 99);\n    if (x) goto done;\n"
                  "done:\n    return x;\n}\n")),
        ("test_rule_1_recursion_detector_is_not_vacuous",
         "the file holding the dv_* cycles untracked",
         untrack("docs/srmech/c/src/srmech_dsl_chain_run.c")),
        ("test_rule_1_no_new_recursion", "a NEW self-recursive function",
         append_c("\nint _hk_recur_probe(int n)\n{\n    assert(n >= 0);\n"
                  "    assert(n < 64);\n"
                  "    return n ? _hk_recur_probe(n - 1) : 0;\n}\n")),
        ("test_rule_1_recursion_ceiling_is_not_slack",
         "the recursion ceiling raised above the measurement",
         edit_audit("CEIL_RULE_1_RECURSION: int = 9",
                    "CEIL_RULE_1_RECURSION: int = 10")),
        ("test_rule_3_no_dynamic_allocation", "a malloc",
         append_c("\nvoid *_hk_alloc_probe(int n)\n{\n    assert(n > 0);\n"
                  "    assert(n < 999);\n    return malloc((size_t)n);\n}\n")),
        ("test_rule_4_function_length_under_60", "a 68-line function",
         append_c(_long_c_function("_hk_long_probe", 62))),
        ("test_rule_4_seed_is_tight_and_drains",
         "a seeded Rule-4 length that no longer matches",
         edit_audit('"srmech_q_zeilberger": 141', '"srmech_q_zeilberger": 142')),
        ("test_rule_5_minimum_two_asserts_per_function",
         "a function with zero asserts",
         append_c("\nint _hk_bare_probe(int x)\n{\n    return x + 1;\n}\n")),
        ("test_rule_8_no_multiline_macros", "a token-pasting macro",
         append_c("\n#define _HK_CAT_PROBE(a, b) a ## b\n")),
        ("test_rule_9_detector_is_not_vacuous",
         "the documented ndjson callback renamed out from under the scanner",
         rename_in("docs/srmech/c/include/srmech.h",
                   "srmech_ndjson_line_cb", "srmech_ndjson_line_cb_renamed")),
        ("test_rule_9_no_new_function_pointers",
         "a NEW function-pointer typedef",
         append_c("\ntypedef int (*_hk_fnptr_probe)(int, int);\n")),
        ("test_rule_9_ceiling_is_not_slack",
         "the Rule-9 ceiling raised above the measurement",
         edit_audit("CEIL_RULE_9_FN_PTR: int = 10",
                    "CEIL_RULE_9_FN_PTR: int = 11")),
        ("test_audit_doc_present_and_mentions_all_rules", "JPL_AUDIT.md deleted",
         drop_audit_doc),
    ]


def check_jpl_audit() -> None:
    audit = PY / "tests" / "test_jpl_audit.py"
    if not audit.is_file():
        skip("jpl-audit-gate", "tests/test_jpl_audit.py absent")
        return

    stop = {"hook_event_name": "Stop"}
    commit = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
              "tool_input": {"command": "git commit -m 'rc455 work'"}}

    # ── the REAL tree, which must be green ────────────────────────────────
    case("jpl-audit ALLOWS the real tree at this commit (ratchets green)",
         _JPL, stop, 0)
    case("jpl-audit ALLOWS a real `git commit` while the ratchets are green",
         _JPL, commit, 0)
    case("jpl-audit ALLOWS a non-commit Bash command WITHOUT scanning",
         _JPL, {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": "ls -la docs"}}, 0)
    case("jpl-audit ALLOWS `echo \"git commit\"` — a mention is not an "
         "invocation", _JPL,
         {"hook_event_name": "PreToolUse", "tool_name": "Bash",
          "tool_input": {"command": 'echo "remember to git commit later"'}}, 0)

    # ⚠️ THE COMMIT ARM WAS NARROWER THAN ITS SIBLING IN THIS DIRECTORY.
    # `_commit_segment` required `args[0] == "commit"`, but git takes options
    # BEFORE the subcommand and three of them are ordinary here. Measured by
    # calling `_scope` directly, with the first cut:
    #     git -C docs/srmech commit -m x   -> None      (out of scope)
    #     git --no-pager commit -m x       -> None      (out of scope)
    #     git -c user.name=z commit -m x   -> None      (out of scope)
    # `git -C` is the normal invocation for an agent working from another cwd.
    # `ssot_agreement._is_commit` and `ripple_stamp_before_push` both use
    # membership and never had the hole; matching them is the fix. This row is a
    # direct census rather than an exit-status pair, because against a GREEN
    # tree an out-of-scope call and an in-scope call both exit 0 — the exact
    # reason the narrowing was invisible. The end-to-end proof is below, under
    # the goto plant, where in-scope BLOCKS and out-of-scope does not.
    sys.path.insert(0, str(HOOKS))
    import jpl_audit_gate as JAG  # noqa: E402
    _must_fire = ("git commit -m x",
                  "cd d && git commit -m x",
                  "git -C docs/srmech commit -m x",
                  "git --no-pager commit -m x",
                  "git -c user.name=z commit -m x")
    _must_not = ('echo "remember to git commit later"',
                 "ls -la docs",
                 "git status --porcelain",
                 "grep -n commit tools/hooks/check_hooks.py")

    def _scope_of(cmd: str):
        return JAG._scope({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                           "tool_input": {"command": cmd}})
    missed = [c for c in _must_fire if _scope_of(c) is None]
    spurious = [c for c in _must_not if _scope_of(c) is not None]
    _results.append((
        "jpl-audit commit arm catches every `git [opts] commit` form, and no "
        "mention (5 in scope / 4 out, censused directly)",
        PASS if not missed and not spurious else FAIL,
        f"missed={missed or 'none'}, spurious={spurious or 'none'}"))

    # COST. The engine this replaces — shelling out to pytest — measured ~30 s
    # native and ~53 s under WSL2. This engine measured 4.5-9.5 s over six
    # spaced samples (median 5.4 s); the tail is real and is stated in the
    # README rather than rounded away. 20 s is ~2.1x the observed max and still
    # well under the shell-out, so this ceiling separates the two DESIGNS
    # without flaking on a churned page cache.
    _cost_case("jpl-audit costs well under the 20 s pytest-shell-out ceiling",
               _JPL, stop, 20.0)

    with tempfile.TemporaryDirectory() as td:
        root = _jpl_fixture(Path(td))
        target = root / _JPL_TARGET
        audit_fx = root / _JPL_AUDIT_REL
        hdr = root / "docs" / "srmech" / "c" / "include" / "srmech.h"
        doc = root / "docs" / "srmech" / "c" / "JPL_AUDIT.md"
        snapshot = {p: p.read_bytes() for p in (target, audit_fx, hdr, doc)}

        def restore() -> None:
            for p, b in snapshot.items():
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b)
            _git(["add", "-A"], root)
            _git(["reset", "-q", "--mixed"], root)
            _git(["add", "-A"], root)

        case("jpl-audit ALLOWS the untouched fixture copy (clean baseline)",
             _JPL, stop, 0, project_dir=root)

        # ⚠️ THE CONCURRENCY HAZARD, TESTED RATHER THAN ASSUMED.
        # check_hooks.py writes a Rule-5-violating C file into the audited
        # c/src as a ratchet fixture. It is UNTRACKED, and this hook scans the
        # tracked set, so the two cannot collide. Without that narrowing this
        # case exits 2 and the real-world symptom is an unreproducible flake.
        planted_untracked = root / "docs" / "srmech" / "c" / "src" / \
            _RATCHET_FIXTURE_NAME
        _write(planted_untracked, _RATCHET_FIXTURE_BODY)
        case("jpl-audit ALLOWS check_hooks' own UNTRACKED Rule-5 fixture "
             "sitting in c/src (the concurrency collision, closed)",
             _JPL, stop, 0, project_dir=root)
        # ...and the SAME file, once tracked, is a genuine violation. Without
        # this the row above would be indistinguishable from a dead scanner.
        _git(["add", "--", f"docs/srmech/c/src/{_RATCHET_FIXTURE_NAME}"], root)
        case("jpl-audit BLOCKS that same file once it is TRACKED — the "
             "narrowing is a scope, not a hole", _JPL, stop, 2,
             contains="test_rule_5_minimum_two_asserts_per_function",
             project_dir=root)
        _git(["rm", "-q", "-f", "--",
              f"docs/srmech/c/src/{_RATCHET_FIXTURE_NAME}"], root)
        planted_untracked.unlink(missing_ok=True)

        # ── ONE PLANT PER PREDICATE ───────────────────────────────────────
        for check_name, what, plant in _plants():
            try:
                plant(root)
                case(f"jpl-audit BLOCKS {what} -> {check_name}",
                     _JPL, stop, 2, contains=check_name, project_dir=root)
            finally:
                restore()

        # ── the loop guard and both documented overrides ──────────────────
        plant = _plants()[0][2]
        plant(root)
        try:
            case("jpl-audit ALLOWS a repeat stop even while RED (loop guard)",
                 _JPL, {"hook_event_name": "Stop", "stop_hook_active": True}, 0,
                 project_dir=root)
            case("jpl-audit ALLOWS with SRMECH_ALLOW_JPL_VIOLATION=1, and "
                 "ECHOES the bypass", _JPL, stop, 0,
                 contains="BYPASSING", project_dir=root,
                 env_extra={"SRMECH_ALLOW_JPL_VIOLATION": "1"})
            case("jpl-audit ALLOWS a commit carrying [jpl-pending], and "
                 "records it", _JPL,
                 {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                  "tool_input": {"command":
                                 "git commit -m 'wip [jpl-pending]'"}}, 0,
                 contains="[jpl-pending]", project_dir=root)
            case("jpl-audit BLOCKS the same commit WITHOUT the token",
                 _JPL, {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                        "tool_input": {"command": "git commit -m 'wip'"}}, 2,
                 contains="test_rule_1_no_goto", project_dir=root)

            # END TO END, on the three forms that used to escape. Against a RED
            # tree the difference is decisive: in scope -> 2, out of scope -> 0.
            # Every one of these exited 0 before the membership repair.
            for cmd in ("git -C docs/srmech commit -m 'wip'",
                        "git --no-pager commit -m 'wip'",
                        "git -c user.name=z commit -m 'wip'"):
                case(f"jpl-audit BLOCKS the option-carrying commit form: "
                     f"{cmd[:34]}", _JPL,
                     {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                      "tool_input": {"command": cmd}}, 2,
                     contains="test_rule_1_no_goto", project_dir=root)

            # ⚠️ THE SILENT DEGRADATION, WHICH REINSTATED THE FLAKE IT CLOSES.
            # The first cut read `if names["src"]:` and simply skipped the
            # tracked-set narrowing when git could not answer, falling back to
            # the naive working-tree glob — measured with a nonexistent git:
            # `_tracked_names` -> {'src': 0, 'include': 0}, `_C_SRC_DIR` left a
            # raw Path, `_c_files()` returning all 139 on-disk files, and
            # NOTHING echoed. It now refuses, loudly. Note it fails OPEN (0)
            # while the tree is RED: an infrastructure failure is never
            # reported as a measurement, in either direction.
            case("jpl-audit REFUSES to scan (loudly, exit 0) when git cannot "
                 "name the tracked set, instead of silently using the naive "
                 "glob", _JPL, stop, 0, contains="REFUSING to scan",
                 project_dir=root,
                 env_extra={"SRMECH_HOOK_GIT": "/nonexistent/git"})
        finally:
            restore()

        # ── VACUITY: the populations, not the verdict ─────────────────────
        _selftest_case("jpl-audit recursion population is 9 (vacuity)",
                       _JPL, "_recursion_cycles()       :     9 cycles")
        _selftest_case("jpl-audit function-pointer population is 10 (vacuity)",
                       _JPL, "_fn_ptr_sites()           :    10 sites")
        _selftest_case("jpl-audit scans a non-empty function population",
                       _JPL, "_scan_functions() total   :  3574 funcs")

    # A missing audit file is an INFRASTRUCTURE failure and must fail OPEN.
    # ⚠️ The fixture carries a C tree ON PURPOSE. It used to be `python/` alone,
    # i.e. BOTH the audit file and the C tree absent, so it could not tell which
    # of the two boundaries answered — and once the C-tree boundary was
    # implemented it answered first and this case failed on its `contains=`.
    # One fixture, one missing thing.
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td) / "repo"
        (empty / "docs" / "srmech" / "python").mkdir(parents=True)
        _write(empty / "docs/srmech/c/src/srmech_stub.c",
               "int stub(void) { return 0; }\n")
        _write(empty / "docs/srmech/c/include/srmech.h", "#define X 1\n")
        case("jpl-audit FAILS OPEN (loudly) when the audit file is absent "
             "(C tree present, so only ONE thing is missing)",
             _JPL, stop, 0, contains="could not load", project_dir=empty)

    # ⚠️ THE FAIL-OPEN CASE THE DOCSTRING NAMED AND THE CODE DID NOT IMPLEMENT.
    # jpl_audit_gate.__doc__ has said since the first cut that "the C tree not
    # checked out" exits 0 with a loud note. Measured against a tree holding
    # tests/test_jpl_audit.py with no docs/srmech/c/ present, it exited **2**
    # with "6 of 13 JPL Power-of-Ten checks are RED" — both
    # *_ceiling_is_not_slack (live population 0 against ceilings 9 and 10),
    # both *_detector_is_not_vacuous, test_rule_4_seed_is_tight_and_drains and
    # test_audit_doc_present_and_mentions_all_rules. `load_audit` checked only
    # that the audit .py existed.
    #
    # The audit itself declares `pytestmark = pytest.mark.skipif(not
    # _C_SRC_DIR.exists())`, so pytest SKIPS in this state. The hook never
    # consulted it — which makes "there is exactly one copy of the rule logic
    # in the tree" false on the SKIP axis: pytest's collection semantics are a
    # second copy of the scoping. Blocking here also inverts this slice's own
    # "a SKIP is not a PASS" into the worse "a SKIP is a BLOCK".
    with tempfile.TemporaryDirectory() as td:
        noc = Path(td) / "repo"
        _init_repo(noc)
        tests = noc / "docs" / "srmech" / "python" / "tests"
        tests.mkdir(parents=True)
        shutil.copy2(PY / "tests" / "test_jpl_audit.py",
                     tests / "test_jpl_audit.py")
        _commit(noc, "the audit, with no C tree beside it")
        case("jpl-audit FAILS OPEN when the C tree is not checked out — the "
             "case its own docstring named (was: exit 2, '6 of 13 RED')",
             _JPL, stop, 0, contains="C source tree is not checked out",
             project_dir=noc)
        case("...and it says NOT a pass rather than reporting green",
             _JPL, stop, 0, contains="NOT a pass", project_dir=noc)


# ── 9. prose-currency-gate ────────────────────────────────────────────────

_PROSE = "prose_currency_gate.py"

#: A stand-in for `test_readme_currency_rc419.py`: one assertion, over the
#: fixture's own README, red exactly when the shipped ABI sentence is stale.
#: Real enough to be run by pytest end to end, small enough to run in ~1 s.
_STUB_GATE = '''\
"""Fixture stand-in for tests/test_readme_currency_rc419.py."""
from pathlib import Path


def test_readme_abi_sentence_is_current():
    readme = Path(__file__).resolve().parent.parent / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "**ABI 22** at this release" in text, (
        "shipped README states a stale ABI against the macro")
'''


def _committed_prose_case(PCG) -> None:
    """The committed-lag case, end to end: plant -> COMMIT -> stop -> block.

    Every other prose fixture plants an UNCOMMITTED edit, which is why none of
    them could see that the trigger went silent on commit.
    """
    with tempfile.TemporaryDirectory() as td:
        fx = Path(td) / "repo"
        _init_repo(fx)
        rel = "docs/srmech/python/README.md"
        _write(fx / rel, "its ABI matched (**ABI 22** at this release)\n")
        _write(fx / "docs/srmech/python/tests/test_readme_currency_rc419.py",
               _STUB_GATE)
        _commit(fx, "baseline: README agrees with the macro")
        # A second commit so HEAD~1 — the documented base FLOOR for a repo with
        # no upstream ref and no srmech-v* tag — resolves at all.
        _write(fx / "docs/srmech/python/pad.txt", "pad\n")
        _commit(fx, "pad")

        stop = {"hook_event_name": "Stop"}
        case("prose-currency ALLOWS a committed tree whose prose did NOT move "
             "(no gate is run)", _PROSE, stop, 0, project_dir=fx)

        _write(fx / rel, "its ABI matched (**ABI 20** at this release)\n")
        _commit(fx, "plant an ABI prose lag AND COMMIT IT")

        # The two halves, side by side, in the SAME state. This is the defect
        # stated as a measurement rather than as prose.
        working = H.dirty_paths(fx, PCG.all_watched())
        union, how = PCG.changed_prose_paths(fx)
        _results.append((
            "prose-currency trigger SEES a COMMITTED prose lag that the "
            "working-tree half cannot (the blindness this repaired)",
            PASS if (not working and union) else FAIL,
            f"working-tree half={working or '[]'} (blind), "
            f"union={union} via {how}"))

        case("prose-currency BLOCKS a COMMITTED prose lag — the ordinary "
             "session shape (edit, commit, stop) and rc452's actual defect",
             _PROSE, stop, 2, contains="BLOCKED (prose-currency)",
             project_dir=fx)
        case("...and the block NAMES the base it measured committed drift from",
             _PROSE, stop, 2, contains="base     : HEAD~1 (floor)",
             project_dir=fx)
        case("prose-currency ALLOWS that COMMITTED lag with "
             "SRMECH_ALLOW_PROSE_LAG=1, and ECHOES it",
             _PROSE, stop, 0, contains="BYPASSING", project_dir=fx,
             env_extra={"SRMECH_ALLOW_PROSE_LAG": "1"})


def check_prose_currency() -> None:
    stop = {"hook_event_name": "Stop"}
    readme = PY / "README.md"

    # (b) THE TRIGGER. As designed it was `git status --porcelain --
    # README.md CHANGELOG.md`, which returns 2 under WSL git and 0 under
    # Windows git on the same clean tree, so under WSL it armed on every stop
    # forever. The repaired trigger is content-based and measured identical
    # under both. Proven here in BOTH directions against a fixture repo whose
    # working files are CRLF and whose blobs are LF — the exact shape.
    sys.path.insert(0, str(HOOKS))
    import prose_currency_gate as PCG  # noqa: E402
    with tempfile.TemporaryDirectory() as td:
        fx = Path(td) / "repo"
        _init_repo(fx)
        rel = "docs/srmech/python/README.md"
        p = fx / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"line one\nline two\n")
        _commit(fx, "LF baseline")
        p.write_bytes(b"line one\r\nline two\r\n")          # EOL-ONLY change
        porcelain, content = H.eol_noise(fx, [rel])
        if porcelain > 0 and content == 0:
            _results.append(("prose-currency trigger IGNORES an EOL-only "
                             "difference that `status --porcelain` reports",
                             PASS, f"porcelain={porcelain}, content={content}"))
        elif porcelain == 0 and content == 0:
            skip("prose-currency trigger IGNORES an EOL-only difference",
                 "this git normalises the fixture's EOLs itself "
                 f"(porcelain={porcelain}) — the poisoning cannot be staged "
                 "here; the real-tree measurement is in the hook docstring")
        else:
            _results.append(("prose-currency trigger IGNORES an EOL-only "
                             "difference", FAIL,
                             f"porcelain={porcelain}, content={content}"))

        p.write_bytes(b"line one\r\nline two\r\nline THREE\r\n")   # REAL change
        real = H.dirty_paths(fx, [rel])
        armed = PCG.armed_gates(fx, real)
        _results.append((
            "prose-currency trigger DOES arm on a real content change "
            "(the instrument can return otherwise)",
            PASS if real else FAIL,
            f"dirty={real}, armed={armed or '(no gate file in fixture)'}"))

    # (b2) THE STATE THE TRIGGER WAS BLIND TO. `dirty_paths` diffs the WORKING
    # TREE against HEAD, so the moment a prose edit is COMMITTED it returned []
    # and no gate armed. This repo commits per step and never squash-merges, so
    # "edit README, commit, stop" is the ORDINARY session shape — and rc452's
    # real defect (the shipped "**ABI 21** at this release" against macro 22)
    # was a COMMITTED falsehood that had survived a release. Every fixture in
    # the section above plants an UNCOMMITTED edit, so none of them could see
    # this: good tests of the wrong verb.
    #
    # Measured on this fixture before the repair: [] / [README] / [] for
    # clean / uncommitted / COMMITTED. After: [] / [README] / [README].
    _committed_prose_case(PCG)

    # (c) A SKIP IS NOT A PASS — on the real tree, with a real skip.
    # Measured at rc454: these four gates give 55 passed / 1 skipped on
    # Windows (no compiled srmech.dll) and 56 passed / 0 skipped under WSL2.
    # Both exit 0. The hook must name the skip rather than call it green.
    if not readme.is_file():
        skip("prose-currency", "python/README.md absent")
        return

    case("prose-currency ALLOWS a stop that touched no prose surface "
         "(no gate is run at all)", _PROSE, stop, 0)
    case("prose-currency ALLOWS a repeat stop (loop guard)", _PROSE,
         {"hook_event_name": "Stop", "stop_hook_active": True}, 0)
    case("prose-currency ALLOWS a PreToolUse event (Stop-scoped only)",
         _PROSE, {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                  "tool_input": {"command": "pytest -q"}}, 0)

    # THE SKIP ARM. The skip lives in the cascade-catalog gate, which is armed
    # by `srmech/introspect` — NOT by README.md. An untracked probe file there
    # arms exactly that one gate and mutates nothing that exists.
    # NOT `.tmp` — `.gitignore:40` excludes `*.tmp`, so an ignored probe is
    # invisible to `ls-files --others --exclude-standard` and the case would
    # silently measure nothing. Measured: the .tmp form armed no gate at all.
    probe = PY / "srmech" / "introspect" / "_prose_currency_probe.fixture"
    try:
        _write(probe, "arms the cascade-catalog prose gate; removed in finally\n")
        counts = H.pytest_counts(
            H.run([sys.executable, "-m", "pytest",
                   "tests/test_cascade_catalog_prose_currency_rc454.py",
                   "-q", "-rs"], cwd=PY, timeout=300.0,
                  env_extra={"PYTHONPATH": "."})[1])
        if counts.get("skipped", 0):
            case("prose-currency ALLOWS a green run but NAMES the SKIP "
                 "instead of calling it green (55 passed / 1 skipped both "
                 "exit 0)", _PROSE, stop, 0, contains="SKIPPED")
        else:
            skip("prose-currency NAMES the skip",
                 "no gate skips on this interpreter "
                 f"({counts}) — the skip is native-library-dependent, so it is "
                 "present on Windows and absent under WSL2; the cross-platform "
                 "measurement is in the hook docstring")
    finally:
        probe.unlink(missing_ok=True)

    before = readme.read_bytes()
    try:
        # THE BLOCK. Plant the same class of falsehood rc452 found shipped:
        # README says one ABI, the macro says another.
        text = readme.read_text(encoding="utf-8")
        import re as _re
        m = _re.search(r"\*\*ABI (\d+)\*\* at this release", text)
        if m:
            lag = text[:m.start(1)] + str(int(m.group(1)) - 2) + text[m.end(1):]
            readme.write_text(lag, encoding="utf-8", newline="")
            case("prose-currency BLOCKS a planted ABI prose lag in the "
                 "SHIPPED README (rc452's real defect class)",
                 _PROSE, stop, 2, contains="BLOCKED (prose-currency)")
            case("prose-currency ALLOWS that same lag with "
                 "SRMECH_ALLOW_PROSE_LAG=1, and ECHOES it",
                 _PROSE, stop, 0, contains="BYPASSING",
                 env_extra={"SRMECH_ALLOW_PROSE_LAG": "1"})
        else:
            skip("prose-currency BLOCKS a planted ABI prose lag",
                 "README.md no longer carries the '**ABI N** at this release' "
                 "sentence — re-target the plant")
    finally:
        readme.write_bytes(before)

    # VACUITY, PINNED TO A NON-EMPTY POPULATION. This asserted only that the
    # literal `counts=` appeared, which would still have passed if
    # `pytest_counts` returned `{}` — a dead parser and a working one print the
    # same line. The `VACUITY: counts parsed, passed=N > 0` form can only be
    # emitted with a non-zero pass count.
    #
    # The pass count is deliberately NOT pinned to a literal, unlike the three
    # JPL cases ('9 cycles', '10 sites', '3574 funcs'). Those are stable
    # properties of the C tree; this one is not: 55 passed / 1 skipped on
    # Windows and 56 / 0 under WSL2, because one assertion needs the compiled
    # library. An exact pin would be a false red on whichever platform it was
    # not written on — and the point of the whole hook is that the skip is real.
    _selftest_case("prose-currency selftest pins a NON-ZERO pass count, not "
                   "merely the string 'counts=' (vacuity)",
                   _PROSE, "VACUITY: counts parsed, passed=")


# ── 10. sha256-routing-gate ───────────────────────────────────────────────
#
# The design this replaces blocked 38 of 972 tracked .py files with ZERO true
# violations, 23 of them outside the package scope entirely. The redesign
# applies SCOPE FIRST and compares literal-masked BEFORE vs AFTER, so the
# question is "does this edit ADD one", not "does this file contain one".

_SHA = "sha256_routing_gate.py"


def _sha_fixture(tmp: Path) -> Path:
    root = tmp / "repo"
    _write(root / "docs/srmech/python/srmech/math/rational.py",
           "def q(a, b):\n    return (a, b)\n")
    _write(root / "docs/srmech/python/srmech/amsc/format.py",
           "import hashlib\n\n\ndef sha256_bytes(d):\n"
           "    return hashlib.sha256(d).hexdigest()\n")
    _write(root / "docs/srmech/python/srmech/spectral/existing.py",
           "import hashlib\n\n\ndef f(d):\n"
           "    return hashlib.sha256(d).hexdigest()\n")
    _write(root / "docs/srmech/python/tests/test_thing.py",
           "def test_x():\n    assert True\n")
    return root


def check_sha256_routing() -> None:
    def edit(root: Path, rel: str, old: str, new: str) -> Dict[str, Any]:
        return {"hook_event_name": "PreToolUse", "tool_name": "Edit",
                "tool_input": {"file_path": str(root / rel),
                               "old_string": old, "new_string": new}}

    def write(root: Path, rel: str, content: str) -> Dict[str, Any]:
        return {"hook_event_name": "PreToolUse", "tool_name": "Write",
                "tool_input": {"file_path": str(root / rel),
                               "content": content}}

    with tempfile.TemporaryDirectory() as td:
        root = _sha_fixture(Path(td))
        RAT = "docs/srmech/python/srmech/math/rational.py"
        FMT = "docs/srmech/python/srmech/amsc/format.py"
        EXI = "docs/srmech/python/srmech/spectral/existing.py"
        TST = "docs/srmech/python/tests/test_thing.py"

        case("sha256-routing BLOCKS an edit that ADDS a direct "
             "hashlib.sha256( to an in-scope module",
             _SHA, edit(root, RAT, "    return (a, b)\n",
                        "    import hashlib\n"
                        "    return hashlib.sha256(b'x').hexdigest()\n"),
             2, contains="0 -> 1", project_dir=root)

        # THE FALSE POSITIVE THE MASK REMOVES, and it is not hypothetical:
        # five of the seven in-package occurrences on the real tree are
        # documentation warning the reader OFF the call.
        case("sha256-routing ALLOWS a docstring that MENTIONS "
             "hashlib.sha256(...) — a mention is not a call",
             _SHA, edit(root, RAT, "def q(a, b):\n",
                        'def q(a, b):\n    """Do not hand-roll '
                        'hashlib.sha256(data).hexdigest() here."""\n'),
             0, project_dir=root)
        case("sha256-routing ALLOWS a `# hashlib.sha256(x)` comment",
             _SHA, edit(root, RAT, "def q(a, b):\n",
                        "# never write hashlib.sha256(x) directly\n"
                        "def q(a, b):\n"), 0, project_dir=root)

        # SCOPE FIRST: this is the branch that dropped 23 of the 38.
        case("sha256-routing ALLOWS the same real call in an OUT-OF-SCOPE "
             "test file (scope is applied before allowances)",
             _SHA, edit(root, TST, "    assert True\n",
                        "    import hashlib\n"
                        "    assert hashlib.sha256(b'x').hexdigest()\n"),
             0, project_dir=root)

        case("sha256-routing ALLOWS an edit to the sanctioned fallback "
             "srmech/amsc/format.py, and says why",
             _SHA, edit(root, FMT, "def sha256_bytes(d):\n",
                        "def sha256_bytes(d):\n    # second site\n"),
             0, contains="sanctioned", project_dir=root)

        case("sha256-routing ALLOWS an unrelated edit to a module that "
             "ALREADY holds a call site (no opinion on standing debt)",
             _SHA, edit(root, EXI, "def f(d):\n", "def f(d):  # touched\n"),
             0, project_dir=root)
        case("sha256-routing BLOCKS an edit that adds a SECOND call site to "
             "that same module",
             _SHA, edit(root, EXI, "def f(d):\n",
                        "def g(d):\n    return hashlib.sha256(d).digest()\n\n\n"
                        "def f(d):\n"),
             2, contains="1 -> 2", project_dir=root)

        case("sha256-routing BLOCKS a Write creating a NEW in-scope module "
             "with a direct call",
             _SHA, write(root, "docs/srmech/python/srmech/newmod.py",
                         "import hashlib\n\n\ndef h(d):\n"
                         "    return hashlib.sha256(d).hexdigest()\n"),
             2, contains="0 -> 1", project_dir=root)
        case("sha256-routing ALLOWS a Write of the same module routed through "
             "sha256_bytes",
             _SHA, write(root, "docs/srmech/python/srmech/newmod.py",
                         "from srmech.amsc.format import sha256_bytes\n\n\n"
                         "def h(d):\n    return sha256_bytes(d)\n"),
             0, project_dir=root)

        case("sha256-routing FAILS OPEN when the edit cannot be reproduced "
             "(old_string absent)",
             _SHA, edit(root, RAT, "NOT PRESENT IN THE FILE\n", "x\n"), 0,
             contains="could not reproduce", project_dir=root)

        case("sha256-routing ALLOWS with SRMECH_ALLOW_RAW_HASHLIB=1, and "
             "ECHOES the bypass",
             _SHA, edit(root, RAT, "    return (a, b)\n",
                        "    import hashlib\n"
                        "    return hashlib.sha256(b'x').hexdigest()\n"),
             0, contains="BYPASSING", project_dir=root,
             env_extra={"SRMECH_ALLOW_RAW_HASHLIB": "1"})

        case("sha256-routing ALLOWS a non-Python file",
             _SHA, write(root, "docs/srmech/python/srmech/notes.md",
                         "hashlib.sha256(x)\n"), 0, project_dir=root)

    # VACUITY on the REAL tree: the census that rejected the first design.
    # A predicate that found nothing anywhere would print 0 here and every
    # exit status above would still be correct.
    _selftest_case("sha256-routing census finds the ONE real call site on the "
                   "live tree (vacuity)", _SHA,
                   "REDESIGNED (scope-first + masked call): 1 file(s)")


# ── driver ────────────────────────────────────────────────────────────────

CHECKS: List[Tuple[str, Callable[[], None]]] = [
    ("ratchet-recount", check_ratchet_recount),
    ("stale-native-tripwire", check_stale_native),
    ("git-add-all-blocker", check_git_add_all),
    ("generated-file-edit-blocker", check_generated_edit),
    ("ssot-agreement", check_ssot_agreement),
    ("derived-ledger-freshness", check_ledger_freshness),
    ("ripple-stamp-before-push", check_ripple_stamp),
    ("jpl-audit-gate", check_jpl_audit),
    ("prose-currency-gate", check_prose_currency),
    ("sha256-routing-gate", check_sha256_routing),
]


def main(argv: List[str]) -> int:
    only = argv[0] if argv else ""
    if shutil.which("git") is None:
        print("git is required for these fixtures", file=sys.stderr)
        return 1

    for name, fn in CHECKS:
        if only and only not in name:
            continue
        print(f"\n=== {name} ===", file=sys.stderr)
        start = len(_results)
        fn()
        for label, status, detail in _results[start:]:
            print(f"  [{status}] {label}\n        {detail}", file=sys.stderr)

    n_pass = sum(1 for _, s, _ in _results if s == PASS)
    n_fail = sum(1 for _, s, _ in _results if s == FAIL)
    n_skip = sum(1 for _, s, _ in _results if s == SKIP)
    print(f"\n{n_pass} passed, {n_fail} failed, {n_skip} skipped "
          f"({len(_results)} cases)", file=sys.stderr)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
