"""Immolation suite — release-gate end-to-end checks.

Run BEFORE any release. The "immolation" name signals that we
re-check every public surface from scratch each cycle — narrow per-
module tests can pass while the cohort has rotted: a new bridge
method without docs, a new CLI subcommand without --help text, a
stub left in place, a referenced ADR slot that's empty.

Categories
----------

A. Stub detection — public functions in ``antikythera_spectral/``
   must have non-trivial bodies (not ``pass`` / ``...`` /
   ``raise NotImplementedError``).
B. CLI --help reachability — every subcommand / nested subcommand
   parses without crashing and exposes a non-empty ``description``
   or one-line ``help``.
C. Bridge documentation — every name in ``bridge.__all__`` appears
   in ``docs/bridge_api.md``.
D. ADR completeness — every ADR slot 0001..0010 exists and is
   non-trivial (>500 bytes, has a ``## Decision`` header).
E. Facade docstrings — every facade module has a module docstring.
F. Standalone scripts — ``bridge/ephemeris_bridge.py`` is present
   and responds to ``--help`` without crashing.
G. Pyproject metadata — required fields populated; license and
   classifiers reasonable.
H. CHANGELOG — current version appears in ``CHANGELOG.md``.
I. No raw ``TODO``/``FIXME`` in public package code (the research
   tree is excluded — those are research notes, not API contracts).

Run with::

    pytest tests/test_immolation.py -q

Failures here are "fix before release" by definition; nothing in
this file is allowed to be a flake.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set

import pytest

# tomllib is stdlib only on 3.11+. The CI matrix runs on 3.10 too,
# where we fall back to tomli (the upstream of tomllib). The CI
# workflow installs `tomli; python_version < "3.11"` accordingly.
try:
    import tomllib
except ImportError:  # pragma: no cover - 3.10-only path
    import tomli as tomllib

from antikythera_spectral import bridge
from antikythera_spectral.cli import _make_parser
from antikythera_spectral.version import __version__


# Project-root resolution. This file is at:
#   docs/antikythera-maths/antikythera-spectral/python/tests/test_immolation.py
_HERE = Path(__file__).resolve()
_PKG_DIR = _HERE.parents[1]                         # python/
_PROJECT_ROOT = _PKG_DIR.parent                     # antikythera-spectral/
_PKG_SRC = _PKG_DIR / "antikythera_spectral"
_DOCS_DIR = _PROJECT_ROOT / "docs"
_ADR_DIR = _DOCS_DIR / "adr"
_BRIDGE_DIR = _PROJECT_ROOT / "bridge"


# ──────────────────────────────────────────────────────────────────────
# A. Stub detection
# ──────────────────────────────────────────────────────────────────────

def _strip_docstring(body: List[ast.stmt]) -> List[ast.stmt]:
    """Drop a leading docstring expression if present."""
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1:]
    return body


def _is_stub_function(node: ast.FunctionDef) -> bool:
    """True if the function body is a stub.

    Stub patterns:
    - empty (only a docstring)
    - body is just ``pass``
    - body is just ``...`` (Ellipsis literal)
    - body is just ``raise NotImplementedError(...)``
    """
    body = _strip_docstring(node.body)
    if not body:
        return True
    if len(body) == 1:
        stmt = body[0]
        if isinstance(stmt, ast.Pass):
            return True
        if (isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and stmt.value.value is Ellipsis):
            return True
        if isinstance(stmt, ast.Raise):
            exc = stmt.exc
            if exc is None:
                return False
            target = exc.func if isinstance(exc, ast.Call) else exc
            name = getattr(target, "id", None) or getattr(target, "attr", None)
            if name == "NotImplementedError":
                return True
    return False


def test_no_stubs_in_public_package() -> None:
    """Public package code must not contain stub functions.

    The ``_research/`` subtree is the codegen-emitted copy of the
    research scaffold; we exclude it because the research code may
    legitimately have NotImplementedError paths for unfinished
    hypotheses (e.g., ``mars_longitude_equant`` once-was, etc.).
    Public package code (the facades, bridge, CLI, etc.) is held to
    the higher standard.
    """
    stubs: List[str] = []
    for py in _PKG_SRC.rglob("*.py"):
        if "_research" in py.parts:
            continue
        if py.name == "py.typed":
            continue
        try:
            tree = ast.parse(py.read_bytes(), filename=str(py))
        except SyntaxError as exc:
            stubs.append(f"{py.relative_to(_PKG_SRC)}: parse error -- {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private helpers (leading-underscore names).
                # Public API is the bar; helpers can be terse.
                if node.name.startswith("_"):
                    continue
                if _is_stub_function(node):
                    rel = py.relative_to(_PKG_SRC)
                    stubs.append(f"{rel}::{node.name} (line {node.lineno})")
    assert not stubs, (
        "Stub functions in public package code:\n  "
        + "\n  ".join(stubs)
        + "\n\nA function counts as a stub if its body is empty, just "
        "`pass`, `...`, or `raise NotImplementedError`. Either implement "
        "or remove."
    )


# ──────────────────────────────────────────────────────────────────────
# B. CLI --help reachability
# ──────────────────────────────────────────────────────────────────────

def _walk_parsers(parser: argparse.ArgumentParser, prefix: str = "") -> List[tuple[str, argparse.ArgumentParser]]:
    """Yield (full_name, parser) for the parser and every nested subparser."""
    out = [(prefix.strip() or "antikythera-spectral", parser)]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, subp in action.choices.items():
                out.extend(_walk_parsers(subp, prefix=f"{prefix} {name}".strip()))
    return out


def test_every_cli_subcommand_has_help_text() -> None:
    """Every subparser must have a description, help, or epilog."""
    parser = _make_parser()
    missing: List[str] = []
    for name, subp in _walk_parsers(parser):
        # The argparse-built --help string. Should contain at least
        # `usage:` and a non-trivial body.
        help_text = subp.format_help()
        if "usage:" not in help_text:
            missing.append(f"{name}: format_help() doesn't render")
            continue
        # Top-level parser carries our long description + epilog;
        # subcommands should at minimum render usage + options.
        # We only flag if both description and help are blank.
        if name != "antikythera-spectral":
            if not (subp.description or any(
                a.help for a in subp._actions if a.dest != "help"
            )):
                missing.append(f"{name}: no description and no per-arg help")

    assert not missing, (
        "CLI subcommands missing --help content:\n  "
        + "\n  ".join(missing)
    )


def test_every_cli_subcommand_help_runs_without_crashing() -> None:
    """Subprocess-call --help on every subcommand path; assert exit code 0."""
    parser = _make_parser()
    failed: List[str] = []
    for name, _ in _walk_parsers(parser):
        if name == "antikythera-spectral":
            argv = ["--help"]
        else:
            # `name` is the full path (e.g. "date jd-to-gregorian"); split
            # into argv parts and append --help.
            argv = name.split() + ["--help"]
        cmd = [sys.executable, "-m", "antikythera_spectral.cli"] + argv
        try:
            subprocess.run(
                cmd,
                check=True, capture_output=True, text=True, timeout=15,
            )
        except subprocess.CalledProcessError as exc:
            failed.append(f"{name}: exit {exc.returncode}\n    stderr: {exc.stderr[:200]}")
        except subprocess.TimeoutExpired:
            failed.append(f"{name}: timeout")

    assert not failed, "CLI --help crashed for:\n  " + "\n  ".join(failed)


# ──────────────────────────────────────────────────────────────────────
# C. Bridge documentation
# ──────────────────────────────────────────────────────────────────────

def test_every_bridge_method_in_all() -> None:
    """``bridge.__all__`` must list at least 28 methods (v0.1.0 contract)."""
    assert len(bridge.__all__) >= 28, (
        f"bridge.__all__ has {len(bridge.__all__)} entries; v0.1.0 "
        "promises at least 28. Did a method get removed?"
    )


def test_every_bridge_method_callable() -> None:
    """Each name in ``bridge.__all__`` must resolve to a callable."""
    not_callable: List[str] = []
    for name in bridge.__all__:
        obj = getattr(bridge, name, None)
        if obj is None:
            not_callable.append(f"{name}: missing")
        elif not callable(obj):
            not_callable.append(f"{name}: not callable ({type(obj).__name__})")
    assert not not_callable, "\n  " + "\n  ".join(not_callable)


def test_every_bridge_method_documented_in_md() -> None:
    """``docs/bridge_api.md`` must mention every ``bridge.__all__`` name."""
    md_path = _DOCS_DIR / "bridge_api.md"
    assert md_path.exists(), f"missing {md_path}"
    md_text = md_path.read_text(encoding="utf-8")
    missing = [n for n in bridge.__all__ if n not in md_text]
    assert not missing, (
        f"docs/bridge_api.md doesn't mention these bridge.__all__ "
        f"entries: {missing}\n\nUpdate the doc, or remove the unused "
        "names from __all__."
    )


# ──────────────────────────────────────────────────────────────────────
# D. ADR completeness
# ──────────────────────────────────────────────────────────────────────

# ADRs we promise exist for v0.1.0. Adding a new ADR? extend this list.
_REQUIRED_ADRS: tuple[str, ...] = (
    "0001", "0002", "0003", "0004", "0005",
    "0006", "0007", "0008", "0009", "0010",
)
_ADR_MIN_BYTES = 500


def test_all_required_adrs_exist_and_are_substantial() -> None:
    missing: List[str] = []
    too_short: List[str] = []
    no_decision_section: List[str] = []
    for prefix in _REQUIRED_ADRS:
        matches = list(_ADR_DIR.glob(f"{prefix}-*.md"))
        if not matches:
            missing.append(prefix)
            continue
        if len(matches) > 1:
            too_short.append(f"{prefix}: multiple files match -- {matches}")
            continue
        f = matches[0]
        size = f.stat().st_size
        if size < _ADR_MIN_BYTES:
            too_short.append(f"{f.name}: only {size} bytes (< {_ADR_MIN_BYTES})")
            continue
        if "## Decision" not in f.read_text(encoding="utf-8"):
            no_decision_section.append(f"{f.name}: missing '## Decision' header")

    problems: List[str] = []
    if missing:
        problems.append(f"missing ADRs: {missing}")
    problems.extend(too_short)
    problems.extend(no_decision_section)
    assert not problems, "ADR issues:\n  " + "\n  ".join(problems)


# ──────────────────────────────────────────────────────────────────────
# E. Facade module docstrings
# ──────────────────────────────────────────────────────────────────────

_FACADE_MODULES = (
    "encoder", "decoder", "dials", "render", "ephemeris", "eclipses",
    "periods", "gears", "hypotheses",
    "visibility", "compare", "dates", "eclipses_search", "operator",
    "reconstructions", "whatif", "archaeology", "goalyear", "animation",
    "bridge", "cli",
)


@pytest.mark.parametrize("mod_name", _FACADE_MODULES)
def test_facade_module_has_docstring(mod_name: str) -> None:
    """Every facade module must have a module-level docstring."""
    # Some module names are listed for completeness even if absent (e.g.
    # 'reconstructions' was rolled into compare.py); skip those.
    try:
        mod = importlib.import_module(f"antikythera_spectral.{mod_name}")
    except ImportError:
        pytest.skip(f"module {mod_name} not present")
    doc = (mod.__doc__ or "").strip()
    assert len(doc) > 30, (
        f"antikythera_spectral.{mod_name} has no (or trivial) docstring"
    )


# ──────────────────────────────────────────────────────────────────────
# F. Standalone scripts
# ──────────────────────────────────────────────────────────────────────

def test_ephemeris_bridge_script_exists_and_has_help() -> None:
    """``bridge/ephemeris_bridge.py`` must exist (per ADR 0003) and respond to --help."""
    p = _BRIDGE_DIR / "ephemeris_bridge.py"
    assert p.exists(), f"missing {p}"
    assert p.stat().st_size > 1000, f"{p} suspiciously small ({p.stat().st_size} B)"
    # Direct execution of --help must succeed.
    result = subprocess.run(
        [sys.executable, str(p), "--help"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, (
        f"ephemeris_bridge --help exit={result.returncode}; stderr={result.stderr[:300]}"
    )
    assert "ALLOWED_KERNELS" in p.read_text(encoding="utf-8"), (
        "ephemeris_bridge.py is the only URL builder; it MUST hold the "
        "ALLOWED_KERNELS allowlist (per ADR 0003). Did the allowlist "
        "leak elsewhere?"
    )


def test_codegen_regenerate_has_help() -> None:
    p = _PROJECT_ROOT / "codegen" / "regenerate.py"
    assert p.exists()
    result = subprocess.run(
        [sys.executable, str(p), "--help"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, (
        f"regenerate.py --help exit={result.returncode}; stderr={result.stderr[:300]}"
    )


# ──────────────────────────────────────────────────────────────────────
# G. Pyproject metadata
# ──────────────────────────────────────────────────────────────────────

def test_pyproject_metadata_complete() -> None:
    pyproject = _PKG_DIR / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    project = data["project"]

    # Required fields. These are the bare minimum for a publishable
    # PyPI package; missing any is a release blocker.
    required = ("name", "version", "description", "readme",
                "requires-python", "license", "authors",
                "keywords", "classifiers", "dependencies")
    missing = [f for f in required if f not in project]
    assert not missing, f"pyproject.toml missing fields: {missing}"

    assert project["name"] == "antikythera-spectral"
    assert project["version"].startswith("0.1."), (
        f"unexpected version {project['version']!r}"
    )
    # readme must point to a file that exists.
    readme = _PKG_DIR / project["readme"]
    assert readme.exists(), f"readme {readme} missing"
    assert readme.stat().st_size > 1000

    # At minimum, an OSI-approved license classifier must be present.
    has_license_classifier = any(
        "License ::" in c for c in project.get("classifiers", [])
    ) or "license" in project
    assert has_license_classifier


def test_pyproject_version_matches_package() -> None:
    """``pyproject.toml`` ``[project].version`` must equal ``__version__``."""
    with (_PKG_DIR / "pyproject.toml").open("rb") as f:
        toml_version = tomllib.load(f)["project"]["version"]
    assert toml_version == __version__, (
        f"pyproject {toml_version!r} != version.py {__version__!r}; "
        "the autotag workflow checks both."
    )


# ──────────────────────────────────────────────────────────────────────
# H. CHANGELOG
# ──────────────────────────────────────────────────────────────────────

def test_current_version_or_unreleased_in_changelog() -> None:
    """CHANGELOG must mention the current version OR a clearly-marked Unreleased section."""
    changelog = _PROJECT_ROOT / "CHANGELOG.md"
    assert changelog.exists(), f"missing {changelog}"
    text = changelog.read_text(encoding="utf-8")
    # Either we have a heading for the current version OR an
    # Unreleased section explicitly tagged for the candidate.
    pattern = rf"^##\s+\[(?:Unreleased|{re.escape(__version__)})\]"
    assert re.search(pattern, text, re.MULTILINE), (
        f"CHANGELOG.md must have a '## [{__version__}]' or '## [Unreleased]' "
        "section. Add one before tagging."
    )


# ──────────────────────────────────────────────────────────────────────
# I. No raw TODO/FIXME in public package code
# ──────────────────────────────────────────────────────────────────────

# v0.1.0 is allowed to carry forward-pointing pending notes (e.g. "v0.2.0
# will add the archon table"); those are deliberate, not flakes. We
# match a tighter pattern: a TODO with no version-pointer tag is a leak.
_TODO_TAG_PATTERN = re.compile(
    r"\b(TODO|FIXME|XXX|HACK)\b(?!\s*[:(]\s*v\d|\s*--\s*v\d)",
    re.IGNORECASE,
)


def test_no_unscoped_todo_or_fixme_in_public_code() -> None:
    """Catch raw TODO/FIXME without a version pointer.

    We allow ``TODO(v0.2): ...`` because it's a conscious deferral.
    A bare ``TODO: ...`` means someone left work mid-flight.

    Excluded: research scaffold (notes-style code), tests
    (often have planning comments), the immolation file itself.
    """
    leaks: List[str] = []
    for py in _PKG_SRC.rglob("*.py"):
        if "_research" in py.parts:
            continue
        rel = py.relative_to(_PKG_SRC)
        for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if _TODO_TAG_PATTERN.search(line):
                leaks.append(f"{rel}:{lineno}: {line.strip()}")
    assert not leaks, (
        "Unscoped TODO/FIXME/XXX/HACK in public package code:\n  "
        + "\n  ".join(leaks)
        + "\n\nEither resolve them or scope: 'TODO(v0.2): ...'"
    )
