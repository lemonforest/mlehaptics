"""Evaluate every srmech hook in BOTH directions. (rc452, `#T1166`)

    python3 tools/hooks/check_hooks.py            # all hooks
    python3 tools/hooks/check_hooks.py ssot       # substring-filtered

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
         **kw) -> None:
    try:
        code, err = invoke(script, payload, **kw)
    except Exception as exc:
        _results.append((name, FAIL, f"invocation raised {type(exc).__name__}: {exc}"))
        return
    if code == expect:
        first = (err.strip().splitlines() or [""])[0][:96]
        _results.append((name, PASS, f"exit {code} — {first}" if first else f"exit {code}"))
    else:
        _results.append((name, FAIL,
                         f"expected exit {expect}, got {code}. stderr: "
                         + " / ".join(err.strip().splitlines()[:3])))


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


# ── driver ────────────────────────────────────────────────────────────────

CHECKS: List[Tuple[str, Callable[[], None]]] = [
    ("ratchet-recount", check_ratchet_recount),
    ("stale-native-tripwire", check_stale_native),
    ("git-add-all-blocker", check_git_add_all),
    ("generated-file-edit-blocker", check_generated_edit),
    ("ssot-agreement", check_ssot_agreement),
    ("derived-ledger-freshness", check_ledger_freshness),
    ("ripple-stamp-before-push", check_ripple_stamp),
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
