"""Drift-prevention discipline for the PyPI-facing README.

Three invariants — same pattern as `test_native_version_string_matches_package_version`
(C-side header pinned to Python `__version__`) and `test_parity_smoke.py`'s
`PARITY_TARGETS` table (every bridge function classified, drift fails CI):

  1. **Status section completeness.** Every released version recorded
     in the package CHANGELOG must have a corresponding bullet in the
     README's `## Status` section. Catches the "Status section ends
     8 versions back" failure mode.

  2. **Current-version stamp accuracy.** The README's banner line under
     the H1 (`Status: vX.Y.Z`) and the `*(current)*` marker in the
     Status section must both equal `__version__`. Catches a stale
     "Status: v0.9.2" lingering after v0.9.3 ships.

  3. **CLI body-name examples are valid.** Every body name appearing
     in CLI example strings (`--body NAME`, `--departure NAME`,
     `--target NAME`, `--pair-a NAME`, `--pair-b NAME`) must be in
     `SUPPORTED_BODIES`. Catches the v0.9.0 fallout where leftover
     `--body earth` examples silently failed CLI validation.

What this does *not* enforce:

  - Whether prose is accurate / well-written (judgment-grade).
  - Whether Roadmap items are correctly classified as upcoming
    vs. shipped (we don't have a machine-readable Roadmap schema).
  - Whether the Status entries' descriptions are accurate beyond
    "the version is mentioned somewhere in the bullet."

Those stay in human review. CI catches the mechanical drift; humans
catch the rest.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ephemerides_spectral.bridge import SUPPORTED_BODIES
from ephemerides_spectral.version import __version__

# README + CHANGELOG live in the python/ directory; tests/ is a sibling.
_PYTHON_DIR = Path(__file__).resolve().parent.parent
_README = _PYTHON_DIR / "README.md"
_CHANGELOG = _PYTHON_DIR / "CHANGELOG.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing fixture: {path}"
    return path.read_text(encoding="utf-8")


# Recognises Keep-a-Changelog version headers like "## [0.9.2] — 2026-05-05".
# Excludes "[Unreleased]" / "[unreleased]" sections.
_CHANGELOG_VERSION_RE = re.compile(
    r"^##\s+\[(\d+\.\d+\.\d+)\]", re.MULTILINE
)

# Recognises Status-section version bullets:
#   * **v0.9.2** — ...
#   * **v0.9.2** *(current)* — ...
_README_STATUS_VERSION_RE = re.compile(
    r"^\*\s+\*\*v(\d+\.\d+\.\d+)\*\*", re.MULTILINE
)


def _versions_in_changelog() -> set[str]:
    text = _read(_CHANGELOG)
    return set(_CHANGELOG_VERSION_RE.findall(text))


def _status_section(text: str) -> str:
    """Return just the `## Status` section's body (up to the next H2)."""
    match = re.search(
        r"^##\s+Status\s*$(.+?)(?=^##\s+\w)",
        text, re.MULTILINE | re.DOTALL,
    )
    assert match is not None, "README missing `## Status` section"
    return match.group(1)


def _versions_in_readme_status() -> set[str]:
    body = _status_section(_read(_README))
    return set(_README_STATUS_VERSION_RE.findall(body))


# ──────────────────────────────────────────────────────────────────────
# Invariant 1: Status section completeness
# ──────────────────────────────────────────────────────────────────────

def test_every_changelog_version_appears_in_readme_status() -> None:
    """Every released version must be acknowledged in the README Status.

    The package CHANGELOG is the source of truth for what versions
    exist; the README mirrors it. New version → CHANGELOG entry +
    README bullet. Forgetting the bullet fails this test.
    """
    changelog_versions = _versions_in_changelog()
    readme_versions = _versions_in_readme_status()
    missing = changelog_versions - readme_versions
    assert not missing, (
        f"README Status section missing entries for {sorted(missing)}. "
        f"Every version in {_CHANGELOG.name} must have a corresponding "
        f"bullet under `## Status` in {_README.name}. Add the missing "
        f"entries before merging — the discipline that prevents the "
        f"8-version drift v0.9.3 had to mop up."
    )


def test_readme_status_does_not_invent_unreleased_versions() -> None:
    """Reverse direction: README can't claim versions that haven't shipped."""
    changelog_versions = _versions_in_changelog()
    readme_versions = _versions_in_readme_status()
    extra = readme_versions - changelog_versions
    assert not extra, (
        f"README Status section has bullets for {sorted(extra)} but "
        f"those versions don't appear in {_CHANGELOG.name}. Either "
        f"add the CHANGELOG entry or remove the README bullet."
    )


# ──────────────────────────────────────────────────────────────────────
# Invariant 2: Current-version stamp accuracy
# ──────────────────────────────────────────────────────────────────────

def test_readme_status_banner_matches_package_version() -> None:
    """The 'Status: vX.Y.Z[rcN]' banner under the H1 must equal __version__."""
    text = _read(_README)
    match = re.search(
        # PEP 440 pre-release form: optional rcN suffix with no separator.
        # The README banner stamps the actual __version__ so during an
        # rc cycle (e.g. 0.26.1rc1 verifying srmech compatibility on
        # TestPyPI) the marker tracks the rc, not the stable predecessor.
        r"\*\*Status:\s*v(\d+\.\d+\.\d+(?:rc\d+)?)[^*]*\*\*",
        text,
    )
    assert match is not None, (
        "README missing the 'Status: vX.Y.Z' banner under the H1. "
        "Add a single-line bold status banner immediately after the "
        "blockquote subtitle."
    )
    banner = match.group(1)
    assert banner == __version__, (
        f"README Status banner says v{banner}, but __version__ is "
        f"{__version__!r}. Bump the banner in lockstep with the "
        f"version bump in version.py / pyproject.toml."
    )


def test_readme_current_marker_matches_package_version() -> None:
    """The `*(current)*` marker in the Status section must equal __version__."""
    body = _status_section(_read(_README))
    match = re.search(
        # PEP 440 pre-release form: optional rcN suffix with no separator.
        r"\*\*v(\d+\.\d+\.\d+(?:rc\d+)?)\*\*\s*\*\(current\)\*",
        body,
    )
    assert match is not None, (
        "README `## Status` section has no version marked `*(current)*`. "
        "The most recent entry should carry the marker so readers can "
        "tell at a glance which version they're looking at."
    )
    current = match.group(1)
    assert current == __version__, (
        f"README marks v{current} as `*(current)*`, but __version__ "
        f"is {__version__!r}. Move the marker in lockstep with the "
        f"version bump."
    )


# ──────────────────────────────────────────────────────────────────────
# Invariant 3: CLI body-name examples are valid
# ──────────────────────────────────────────────────────────────────────

# Matches body-name flag values in CLI example strings:
#   --body NAME           --departure NAME       --target NAME
#   --pair-a NAME         --pair-b NAME
# Captures the literal NAME after the flag (any non-space token, but
# we exclude shell continuations and angle-bracket placeholders).
_CLI_BODY_FLAG_RE = re.compile(
    r"(?:--body|--departure|--target|--pair-a|--pair-b)\s+([a-z][a-z0-9_-]*)"
)


def test_readme_cli_body_examples_use_valid_body_names() -> None:
    """Every body referenced in a README CLI example must be in SUPPORTED_BODIES.

    Catches the v0.9.0 fallout where leftover `--body earth` examples
    pointed at a name that had been removed from the body roster.
    Argparse would have rejected the example at runtime — but the docs
    happily showed it for nine versions.
    """
    text = _read(_README)
    referenced = set(_CLI_BODY_FLAG_RE.findall(text))
    valid = set(SUPPORTED_BODIES)
    invalid = referenced - valid
    assert not invalid, (
        f"README CLI examples reference body names {sorted(invalid)} "
        f"that are not in SUPPORTED_BODIES. After v0.9.0 the body "
        f"roster uses Latin proper nouns (`terra`, `luna`); generic "
        f"English `earth` / `moon` are no longer valid. Update the "
        f"examples to use the current body names. Valid set: "
        f"{sorted(valid)}."
    )


def test_readme_actually_has_cli_examples() -> None:
    """Sanity check: the regex must find *some* matches.

    Otherwise invariant 3 silently passes against an empty set —
    a classic empty-passing-test failure mode. If the README ever
    stops shipping CLI examples, this test fails loudly so we
    notice instead of silently losing coverage.
    """
    text = _read(_README)
    referenced = set(_CLI_BODY_FLAG_RE.findall(text))
    assert referenced, (
        "README CLI body-name regex found zero matches. Either the "
        "README has stopped shipping CLI examples (so this test no "
        "longer covers anything) or the regex stopped matching the "
        "current example syntax. Investigate before relying on the "
        "valid-body-names invariant."
    )
