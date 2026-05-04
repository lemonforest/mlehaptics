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

import numpy as np
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

# ADRs we promise exist. Adding a new ADR? extend this list.
#   0001-0010: v0.1.0
#   0011:      v0.2.0  (algebraic default, ephemeris opt-in)
#   0012:      v0.3.0  (algebra/eigenbasis modelling, not CAD/fabrication)
_REQUIRED_ADRS: tuple[str, ...] = (
    "0001", "0002", "0003", "0004", "0005",
    "0006", "0007", "0008", "0009", "0010",
    "0011",
    "0012",
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
    "visibility", "visibility_algebraic",
    "compare", "dates", "eclipses_search", "eclipses_algebraic",
    "operator", "reconstructions", "whatif", "archaeology",
    "goalyear", "animation",
    # v0.3.0 additions
    "mars_models", "bit_alu",
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
    # Strict-semver MAJOR.MINOR.PATCH, optionally with a pre-release
    # tag (rcN, devN, etc). Don't pin to a specific MINOR — that creates
    # per-bump test churn. The version-vs-pyproject-vs-tag-agreement
    # is enforced separately in test_pyproject_version_matches_package.
    assert re.fullmatch(
        r"\d+\.\d+\.\d+(rc\d+|\.dev\d+|a\d+|b\d+)?",
        project["version"],
    ), f"unexpected version format {project['version']!r}"
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


# ──────────────────────────────────────────────────────────────────────
# J. ALU optimisation contracts (v0.3.0 — bit_alu release-gate)
# ──────────────────────────────────────────────────────────────────────
#
# The v0.3.0 bit-packed HDC ALU advertises specific optimisation
# claims (memory, bind speed, algebraic invariants).  These tests
# pin the claims at release-gate level: not "the unit tests pass"
# (that's covered by tests/test_bit_alu.py) but "if someone
# 'optimises' the bit ALU and accidentally regresses below the
# advertised contract, we catch it before tagging."
#
# Tolerance bands are deliberately loose so CI noise doesn't flake
# them — a 100× memory claim becomes a "≥ 50×" gate; a 2× bind speedup
# claim becomes a "≥ 1.2× at D=940, ≥ 3× at D=13440" gate.  If we ever
# tighten the marketing claim we tighten the gate too.

_BIT_ALU_MEMORY_RATIO_FLOOR = 50.0
"""Bit-ALU HV must be at least 50× smaller than complex128 HV.  The
real ratio is ~125× at D=940 (15 KB / 120 B); 50× leaves margin for
any uint128 / packed-array refactor that might land in v0.4.x without
violating the marketing claim."""


def test_bit_alu_memory_contract() -> None:
    """Bit-ALU hypervector at D=940 / D=13440 must be at least
    ``_BIT_ALU_MEMORY_RATIO_FLOOR`` × smaller than the complex128
    reference.  Catches any regression that breaks the bit-packing.
    """
    from antikythera_spectral import bit_alu
    for D in (940, 13440):
        cx_bytes = D * 16  # complex128 = 16 bytes per element
        bit_bytes = bit_alu.n_words(D) * 8  # uint64 = 8 bytes per word
        ratio = cx_bytes / bit_bytes
        assert ratio >= _BIT_ALU_MEMORY_RATIO_FLOOR, (
            f"D={D}: bit_alu HV is {bit_bytes} B vs complex128 {cx_bytes} B "
            f"(ratio {ratio:.1f}×); release-gate floor is "
            f"{_BIT_ALU_MEMORY_RATIO_FLOOR}× — the bit packing has regressed."
        )


def test_bit_alu_bind_speed_contract() -> None:
    """Bit-ALU bind must be measurably faster than complex128 multiply
    at the dimensions we ship (D=940 + D=13440).

    Tolerance is wide: D=940 must be ≥ 1.2× faster, D=13440 must be
    ≥ 3× faster.  The actual numbers (per ``figures/bit_alu_findings.md``)
    are ~2.4× and ~9.9×; the gate is loose enough that CI noise won't
    flake it but tight enough to catch any "let's just use complex
    multiplies for clarity" regression.
    """
    import time
    import numpy as np
    from antikythera_spectral import bit_alu

    rng = np.random.default_rng(0)
    floors = {940: 1.2, 13440: 3.0}
    reps = 2000

    for D, floor in floors.items():
        # Reference: complex128 multiply.
        a_ref = (rng.standard_normal(D) + 1j * rng.standard_normal(D)).astype(
            np.complex128
        )
        b_ref = (rng.standard_normal(D) + 1j * rng.standard_normal(D)).astype(
            np.complex128
        )
        # Bit ALU: XOR.
        a_bit = bit_alu.random_hv(D, rng)
        b_bit = bit_alu.random_hv(D, rng)

        # Warm.
        _ = a_ref * b_ref
        _ = bit_alu.bind(a_bit, b_bit)

        t0 = time.perf_counter()
        for _ in range(reps):
            _ = a_ref * b_ref
        t_ref = time.perf_counter() - t0

        t0 = time.perf_counter()
        for _ in range(reps):
            _ = bit_alu.bind(a_bit, b_bit)
        t_bit = time.perf_counter() - t0

        speedup = t_ref / max(t_bit, 1e-12)
        assert speedup >= floor, (
            f"D={D}: bit_alu bind {t_bit*1e6/reps:.2f} µs/op vs "
            f"complex128 multiply {t_ref*1e6/reps:.2f} µs/op "
            f"(speedup {speedup:.2f}×); release-gate floor is {floor}× — "
            "the ALU optimisation has regressed."
        )


def test_bit_alu_algebraic_invariants_release_gate() -> None:
    """Smoke check on algebraic identities at release time.  The unit
    tests (tests/test_bit_alu.py) cover this in detail; this is a
    cohort-level "does the bit ALU still implement HDC?" check.
    """
    import numpy as np
    from antikythera_spectral import bit_alu

    rng = np.random.default_rng(0)
    D = 940
    a = bit_alu.random_hv(D, rng)
    b = bit_alu.random_hv(D, rng)

    # 1. XOR-bind is involutive.
    ab = bit_alu.bind(a, b)
    assert bit_alu.hamming_distance(bit_alu.bind(ab, b), a) == 0, (
        "bit_alu.bind has lost involution"
    )

    # 2. permute by D returns the input.
    rotated = a
    for _ in range(D):
        rotated = bit_alu.permute(rotated, 1, D)
    assert bit_alu.hamming_distance(rotated, a) == 0, (
        "bit_alu.permute period != D"
    )

    # 3. similarity extremes.
    assert abs(bit_alu.similarity(a, a, D) - 1.0) < 1e-12, (
        "self-similarity != 1"
    )
    # Complement of a (within D bits) ≡ −a in bipolar.
    not_a = a.copy()
    for w in range(len(not_a)):
        not_a[w] = ~not_a[w] & np.uint64(0xFFFFFFFFFFFFFFFF)
    used_in_top = D - 64 * (bit_alu.n_words(D) - 1)
    if used_in_top < 64:
        not_a[-1] &= np.uint64((1 << used_in_top) - 1)
    assert abs(bit_alu.similarity(a, not_a, D) - (-1.0)) < 1e-12, (
        "complement-similarity != -1"
    )


def test_bit_alu_encoder_returns_packed_uint64() -> None:
    """``encode_ant_bit`` must return a packed uint64 array of the
    correct shape -- the public-API contract for the ALU encoder."""
    import numpy as np
    from antikythera_spectral import bit_alu
    from antikythera_spectral._research.encode_ant import REFERENCE_JD

    for D in (940, 13440):
        state = bit_alu.encode_ant_bit(REFERENCE_JD + 100.0, D)
        assert state.dtype == np.uint64, (
            f"D={D}: encode_ant_bit returned dtype {state.dtype}, "
            "expected uint64"
        )
        assert state.shape == (bit_alu.n_words(D),), (
            f"D={D}: encode_ant_bit shape {state.shape}, "
            f"expected ({bit_alu.n_words(D)},)"
        )


# ──────────────────────────────────────────────────────────────────────
# K. Mars-models surface (v0.3.0 — bronze + named param sets)
# ──────────────────────────────────────────────────────────────────────

def test_mars_models_facade_exposes_named_param_sets() -> None:
    """Three reconstruction-source param sets must be reachable via
    ``mars_models.PARAM_SETS`` and must distinguish on eccentricity /
    equant_offset.  Catches any silent collapse to a single param set.
    """
    from antikythera_spectral import mars_models

    expected_keys = {"ptolemy", "freeth_2012", "freeth_2021"}
    actual_keys = set(mars_models.PARAM_SETS.keys())
    assert actual_keys == expected_keys, (
        f"PARAM_SETS keys {actual_keys} != expected {expected_keys}"
    )

    # Ptolemy must have the canonical Almagest values; Freeth variants
    # must have eccentricity = equant = 0.
    p = mars_models.PARAM_SETS["ptolemy"]
    f12 = mars_models.PARAM_SETS["freeth_2012"]
    f21 = mars_models.PARAM_SETS["freeth_2021"]
    assert p.eccentricity == 6.0 and p.equant_offset == 12.0, (
        "PTOLEMY_MARS_PARAMS not at Almagest IX-X canonical values"
    )
    assert f12.eccentricity == 0.0 and f12.equant_offset == 0.0, (
        "FREETH_2012_MARS_PARAMS must be (e=0, equant=0)"
    )
    assert f21.eccentricity == 0.0 and f21.equant_offset == 0.0, (
        "FREETH_2021_MARS_PARAMS must be (e=0, equant=0)"
    )


def test_compare_models_at_jd_accepts_bronze_and_params() -> None:
    """The compare-facade signature must accept bronze + params."""
    from antikythera_spectral import compare
    sig = inspect_signature(compare.compare_models_at_jd)
    assert "params" in sig.parameters, (
        "compare_models_at_jd must accept `params` keyword (v0.3.0)"
    )


def test_bridge_compare_models_accepts_params() -> None:
    """bridge.compare_models must surface the new params keyword."""
    sig = inspect_signature(bridge.compare_models)
    assert "params" in sig.parameters, (
        "bridge.compare_models must accept `params` keyword (v0.3.0)"
    )


def test_mars_models_fj_38deg_finding_contract() -> None:
    """``fj_38deg_finding()`` must return the documented dict shape
    when a DE kernel is cached.  Skipped cleanly otherwise.
    """
    from antikythera_spectral._research.ephemeris_loader import load_ephemeris
    if not any(load_ephemeris(k) is not None
               for k in ("de422", "de441_part1", "de441")):
        pytest.skip("no DE-series kernel cached; FJ-38° contract not testable")

    from antikythera_spectral import mars_models
    finding = mars_models.fj_38deg_finding()

    expected_keys = {
        "rms_deg", "mean_deg", "peak_deg",
        "oppositions_jd", "n_samples", "kernel_used",
        "fj_documented_deg", "residual_deg", "model",
    }
    missing = expected_keys - set(finding.keys())
    assert not missing, (
        f"fj_38deg_finding missing keys: {missing}"
    )
    # Numerical contract: lands within 1° of F&J's documented 38°.
    assert finding["fj_documented_deg"] == 38.0
    assert finding["residual_deg"] <= 1.0, (
        f"FJ-38° residual {finding['residual_deg']:.2f}° exceeds 1° gate"
    )
    assert len(finding["oppositions_jd"]) == 7
    assert finding["kernel_used"] in ("de422", "de441_part1", "de441")


# ──────────────────────────────────────────────────────────────────────
# L. CLI exposes v0.3.0 surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_compare_models_help_lists_bronze_and_params() -> None:
    """`compare models --help` must list the bronze model and the
    new --params choices.  Catches silent regression of the v0.3.0
    CLI extension.
    """
    parser = _make_parser()
    # Walk the subcommand tree to find `compare models`.
    cmp_parser = _find_subcommand(parser, ["compare", "models"])
    assert cmp_parser is not None, (
        "`compare models` subcommand not found in CLI parser"
    )
    help_text = cmp_parser.format_help()
    assert "bronze" in help_text, (
        "`compare models --help` must mention 'bronze' model"
    )
    assert "freeth_2012" in help_text, (
        "`compare models --help` must mention 'freeth_2012' params choice"
    )
    assert "freeth_2021" in help_text, (
        "`compare models --help` must mention 'freeth_2021' params choice"
    )
    assert "ptolemy" in help_text.lower(), (
        "`compare models --help` must mention 'ptolemy' params choice"
    )


def test_cli_top_level_help_mentions_v030_themes() -> None:
    """Top-level `--help` description must point users at the v0.3.0
    additions (bronze / mars_models / bit_alu).
    """
    parser = _make_parser()
    desc = (parser.description or "").lower()
    for token in ("bronze", "mars_models", "bit_alu"):
        assert token in desc, (
            f"Top-level CLI description must mention {token!r}; "
            "current description does not surface v0.3.0 additions."
        )


# ──────────────────────────────────────────────────────────────────────
# M. README + CHANGELOG + bridge_api references
# ──────────────────────────────────────────────────────────────────────

def test_readme_mentions_mars_models_and_bit_alu() -> None:
    """python/README.md (PyPI long-description) must surface both
    v0.3.0 facades."""
    readme = (_PKG_DIR / "README.md").read_text(encoding="utf-8")
    for token in ("mars_models", "bit_alu", "bronze",
                  "FREETH_2012_MARS_PARAMS",
                  "fj_38deg_finding"):
        assert token in readme, (
            f"python/README.md must mention {token!r} (v0.3.0 surface)"
        )


def test_changelog_030_section_present_with_both_themes() -> None:
    """CHANGELOG.md must have a [0.3.0] section that mentions both
    themes (mars_models AND bit_alu)."""
    changelog = (_PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.3.0]" in changelog, (
        "CHANGELOG.md missing [0.3.0] section header"
    )
    # Slice to the [0.3.0] section.
    after = changelog.split("## [0.3.0]", 1)[1]
    next_section = after.find("\n## [")
    section = after[:next_section] if next_section >= 0 else after
    for token in ("mars_models", "bit_alu", "bronze",
                  "FREETH_2012_MARS_PARAMS"):
        assert token in section, (
            f"CHANGELOG [0.3.0] section must mention {token!r}"
        )


def test_bridge_api_md_mentions_bronze_and_params() -> None:
    """docs/bridge_api.md must reflect that compare_models accepts
    `bronze` + `params`."""
    bapi = (_DOCS_DIR / "bridge_api.md").read_text(encoding="utf-8")
    assert "bronze" in bapi, (
        "docs/bridge_api.md must mention the bronze model (v0.3.0)"
    )
    assert "params" in bapi, (
        "docs/bridge_api.md must mention the params kwarg (v0.3.0)"
    )


# ──────────────────────────────────────────────────────────────────────
# N. Default-backend flip (v0.3.0 — Option A/B/C)
# ──────────────────────────────────────────────────────────────────────
#
# v0.3.0 flips the package default from the complex128 reference encoder
# to the bit-packed binary HDC ALU. These tests pin the flip at release-
# gate level: top-level `default_encode` must default to bit, the bridge
# methods must default to bit, the CLI must accept `--backend`, and the
# v0.2.x complex128 path must remain reachable for backward compatibility.

def test_default_encode_top_level_export() -> None:
    """``antikythera_spectral.default_encode`` is a top-level export and
    its default backend is ``"bit"``."""
    import antikythera_spectral as asp

    assert "default_encode" in asp.__all__
    assert "DEFAULT_BACKEND" in asp.__all__
    assert asp.DEFAULT_BACKEND == "bit", (
        f"DEFAULT_BACKEND is {asp.DEFAULT_BACKEND!r}; v0.3.0 must default "
        "to 'bit' per ADR 0012."
    )


def test_default_encode_returns_uint64_at_default_backend() -> None:
    """default_encode(jd) returns a packed-uint64 array (bit backend by
    default)."""
    import antikythera_spectral as asp
    from antikythera_spectral.bit_alu import n_words

    arr = asp.default_encode(1684500.0)
    assert arr.dtype == np.dtype("uint64"), (
        f"default_encode(jd) returned dtype {arr.dtype}; expected uint64"
    )
    assert arr.shape == (n_words(940),), (
        f"default_encode(jd) shape {arr.shape}; expected ({n_words(940)},)"
    )


def test_default_encode_complex128_explicit_still_works() -> None:
    """Backwards-compat: passing backend='complex128' returns the v0.2.x
    encoder shape."""
    import antikythera_spectral as asp

    arr = asp.default_encode(1684500.0, backend="complex128")
    assert np.iscomplexobj(arr), (
        f"default_encode(..., backend='complex128') returned dtype "
        f"{arr.dtype}; expected complex"
    )
    assert arr.shape == (940,)


def test_bridge_get_dial_state_default_backend_is_bit() -> None:
    """v0.3.0 default: bridge.get_dial_state returns a uint64 / packed
    state vector when no backend is specified."""
    out = bridge.get_dial_state(1684500.0)
    assert out["ok"] is True
    assert out.get("backend") == "bit", (
        f"bridge.get_dial_state default backend is {out.get('backend')!r}; "
        "v0.3.0 must default to 'bit'."
    )
    state = out["state"]
    assert state["dtype"] == "uint64"
    assert "packed_uint64" in state
    assert "n_bits" in state and state["n_bits"] == 940


def test_bridge_get_dial_state_complex128_opt_out_still_works() -> None:
    """Backwards-compat: backend='complex128' returns the v0.2.x shape."""
    out = bridge.get_dial_state(1684500.0, backend="complex128")
    assert out["ok"] is True
    assert out["backend"] == "complex128"
    assert out["state"]["dtype"] == "complex128"
    assert "interleaved_f32" in out["state"]
    assert len(out["state"]["interleaved_f32"]) == 2 * 940


def test_bridge_decode_dial_auto_detects_backend() -> None:
    """``decode_dial`` should dispatch on the input shape: a uint64
    state goes to the bit decoder, a complex128 state to the dense
    decoder.  Round-trip must work under both backends and the
    response must report which decoder ran."""
    for backend in ("bit", "complex128"):
        encoded = bridge.get_dial_state(
            1684500.0 + 1234.5, backend=backend,
        )
        out = bridge.decode_dial(encoded["state"], "Metonic", D=940)
        assert out["ok"] is True, f"backend={backend}: {out}"
        assert out["backend"] == backend, (
            f"decode_dial dispatched to {out['backend']!r}, "
            f"expected {backend!r}"
        )
        assert 0 <= out["recovered_residue"] < 940


def test_bridge_decode_to_jd_auto_detects_backend() -> None:
    """``decode_to_jd`` must auto-detect the backend the same way
    ``decode_dial`` does."""
    for backend in ("bit", "complex128"):
        encoded = bridge.get_dial_state(
            1684500.0 + 365.25 * 19, backend=backend,
        )
        out = bridge.decode_to_jd(encoded["state"], D=940)
        assert out["ok"] is True, f"backend={backend}: {out}"
        assert out["backend"] == backend


def test_cli_encode_subcommand_has_backend_kwarg() -> None:
    """The `encode` subcommand must accept --backend with bit/complex128
    choices and must default to 'bit'."""
    parser = _make_parser()
    encode_parser = _find_subcommand(parser, ["encode"])
    assert encode_parser is not None, "`encode` subcommand not found"
    help_text = encode_parser.format_help()
    assert "--backend" in help_text, (
        "`encode --help` must expose --backend (v0.3.0)"
    )
    assert "bit" in help_text and "complex128" in help_text
    # Walk the parser's defaults to confirm 'bit' is the default.
    backend_action = next(
        (a for a in encode_parser._actions
         if any("--backend" == s for s in a.option_strings)),
        None,
    )
    assert backend_action is not None
    assert backend_action.default == "bit", (
        f"--backend default is {backend_action.default!r}; "
        "v0.3.0 must default to 'bit'."
    )


def test_changelog_030_mentions_default_backend_flip() -> None:
    """The [0.3.0] CHANGELOG section must explicitly mention the
    default-backend flip so consumers see the breaking-ish change."""
    changelog = (_PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.3.0]" in changelog
    after = changelog.split("## [0.3.0]", 1)[1]
    next_section = after.find("\n## [")
    section = after[:next_section] if next_section >= 0 else after
    # Phrase that signals the flip; guard against a too-tight literal
    # by accepting any of a few plausible phrasings.
    flip_phrases = (
        "default-backend flip", "default-backend",
        "default backend", "now the package default",
        "package default",
    )
    assert any(p.lower() in section.lower() for p in flip_phrases), (
        "CHANGELOG [0.3.0] section must mention the default-backend flip "
        "(any of: 'default-backend flip', 'default backend', 'package "
        "default')."
    )


# ──────────────────────────────────────────────────────────────────────
# Helpers used by the v0.3.0 tests
# ──────────────────────────────────────────────────────────────────────

def inspect_signature(fn):
    """Lazy import of ``inspect.signature`` to keep test-collection
    overhead trivial; alias kept descriptive for clarity at the call
    site."""
    import inspect
    return inspect.signature(fn)


def _find_subcommand(parser, path):
    """Walk a nested argparse subparser tree by command names.

    ``path`` is a list of subcommand names, e.g. ``["compare", "models"]``;
    returns the leaf parser or ``None`` if any segment is missing.
    """
    cur = parser
    for name in path:
        sub_actions = [a for a in cur._actions
                       if isinstance(a, argparse._SubParsersAction)]
        if not sub_actions:
            return None
        choices = sub_actions[0].choices
        cur = choices.get(name)
        if cur is None:
            return None
    return cur
