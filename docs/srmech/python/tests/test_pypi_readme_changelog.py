"""MS #20 rc8 — the PyPI long-description is assembled dynamically.

srmech ships TWO build backends:

* ``pyproject.toml``        — scikit-build-core (platform wheels)
* ``pyproject-pure.toml``   — hatchling        (the py3-none-any wheel)

Both must render the SAME PyPI long-description: the full ``README.md``
followed by a ``## Changelog`` section sliced to ONLY the current-minor
(0.6.0) ``CHANGELOG.md`` entries, then a "Full changelog" link. The slice
is driven by HTML-comment markers in ``CHANGELOG.md`` so the changelog
text is never hand-duplicated (CHANGELOG.md stays the single source of
truth).

These tests guard:

1. the slice markers exist + bracket ONLY the 0.6.0 entries;
2. both pyprojects declare ``dynamic = ["readme"]`` (no static ``readme``)
   + carry a byte-identical ``[tool.hatch.metadata.hooks.fancy-pypi-readme]``
   block + agree on ``[project].description``;
3. the assembled long-description (built via the ``hatch-fancy-pypi-readme``
   library, exactly as both backends do) starts with the README, contains
   the 0.6.0 changelog header + entries, EXCLUDES the prior-minor entries,
   and ends with the full-changelog link.

The current minor is read from ``srmech.version`` so the assertions track
the source-of-truth version rather than a hard-coded string (only the
"prior minor must be absent" sentinel — ``[0.5.0]`` — is pinned, since
that is the literal end-marker boundary).
"""

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path

import pytest

# tests/ -> python/  (the directory holding both pyprojects + README + CHANGELOG)
PY_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = PY_ROOT / "pyproject.toml"
PYPROJECT_PURE = PY_ROOT / "pyproject-pure.toml"
README = PY_ROOT / "README.md"
CHANGELOG = PY_ROOT / "CHANGELOG.md"

START_MARKER = "<!-- pypi-readme-changelog-start -->"
END_MARKER = "<!-- pypi-readme-changelog-end -->"

# The minor series the markers MUST bracket (derived from the package
# version SSOT so this test moves automatically at the next minor bump,
# at which point the markers themselves must be moved too — see the
# documenting HTML comment in CHANGELOG.md).
import srmech  # noqa: E402

_CURRENT_MINOR = ".".join(srmech.__version__.split(".")[:2]) + "."  # e.g. "0.6."
# The prior released minor sits immediately after the end-marker; its
# entry header must NOT be inside the slice (proves the slice is bounded).
_PRIOR_MINOR_HEADER = "## [0.5.0]"


def _hook_block(text: str) -> str:
    """Return the ``[tool.hatch.metadata.hooks.fancy-pypi-readme]`` TOML
    section verbatim (from its header to EOF, trailing newlines stripped).

    Matched on an exact full-line header so the same string appearing
    inside a comment doesn't false-match.
    """
    lines = text.splitlines()
    start = next(
        i
        for i, line in enumerate(lines)
        if line == "[tool.hatch.metadata.hooks.fancy-pypi-readme]"
    )
    return "\n".join(lines[start:]).rstrip("\n")


def _changelog_slice() -> str:
    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.index(START_MARKER) + len(START_MARKER)
    end = text.index(END_MARKER)
    assert start < end, "start marker must precede end marker"
    return text[start:end]


# ---------------------------------------------------------------------------
# 1. CHANGELOG slice markers
# ---------------------------------------------------------------------------


def test_changelog_markers_exist_and_are_unique():
    text = CHANGELOG.read_text(encoding="utf-8")
    assert text.count(START_MARKER) == 1, "exactly one start marker expected"
    assert text.count(END_MARKER) == 1, "exactly one end marker expected"
    assert text.index(START_MARKER) < text.index(END_MARKER)


def test_changelog_slice_brackets_only_current_minor():
    sliced = _changelog_slice()
    # Contains the current minor (e.g. a "## [0.6.0..." header).
    assert _CURRENT_MINOR in sliced, (
        f"changelog slice must contain the current minor {_CURRENT_MINOR!r}"
    )
    assert re.search(r"^## \[" + re.escape(_CURRENT_MINOR), sliced, re.MULTILINE), (
        "slice must contain at least one current-minor entry header"
    )
    # Does NOT bleed into the prior minor.
    assert _PRIOR_MINOR_HEADER not in sliced, (
        f"changelog slice must NOT contain the prior minor header "
        f"{_PRIOR_MINOR_HEADER!r} — the end marker is misplaced"
    )
    # Every entry header inside the slice is a current-minor header.
    for header in re.findall(r"^## \[[^\]]+\]", sliced, re.MULTILINE):
        assert _CURRENT_MINOR in header, f"non-current-minor entry leaked: {header}"


# ---------------------------------------------------------------------------
# 2. Both pyprojects declare the dynamic readme + share the hook block
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [PYPROJECT, PYPROJECT_PURE])
def test_pyproject_declares_dynamic_readme(path: Path):
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data["project"]
    assert "readme" not in project, f"{path.name} must not carry a static readme key"
    assert "readme" in project.get("dynamic", []), (
        f"{path.name} must declare dynamic = ['readme']"
    )


@pytest.mark.parametrize("path", [PYPROJECT, PYPROJECT_PURE])
def test_pyproject_declares_fancy_pypi_readme_hook(path: Path):
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    hook = data["tool"]["hatch"]["metadata"]["hooks"]["fancy-pypi-readme"]
    assert hook["content-type"] == "text/markdown"
    fragments = hook["fragments"]
    # README first, full-changelog link last, a sliced CHANGELOG in between.
    assert fragments[0] == {"path": "README.md"}
    assert any(
        f.get("path") == "CHANGELOG.md"
        and f.get("start-after") == START_MARKER
        and f.get("end-before") == END_MARKER
        for f in fragments
    ), "a CHANGELOG.md slice fragment using the markers is required"
    assert "Full changelog" in fragments[-1].get("text", "")


@pytest.mark.parametrize("path", [PYPROJECT, PYPROJECT_PURE])
def test_pyproject_requires_fancy_pypi_readme_builder(path: Path):
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    requires = data["build-system"]["requires"]
    assert any(r.startswith("hatch-fancy-pypi-readme") for r in requires), (
        f"{path.name} build-system.requires must include hatch-fancy-pypi-readme"
    )


def test_both_pyprojects_share_byte_identical_hook_block():
    main = _hook_block(PYPROJECT.read_text(encoding="utf-8"))
    pure = _hook_block(PYPROJECT_PURE.read_text(encoding="utf-8"))
    assert main == pure, (
        "the [tool.hatch.metadata.hooks.fancy-pypi-readme] block must be "
        "byte-identical across pyproject.toml and pyproject-pure.toml"
    )


def test_both_pyprojects_agree_on_description():
    main = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["description"]
    pure = tomllib.loads(PYPROJECT_PURE.read_text(encoding="utf-8"))["project"][
        "description"
    ]
    assert main == pure
    # PyPI Summary hard limit is 512 chars; guard headroom.
    assert len(main) <= 512


def test_scikit_build_core_readme_provider_configured():
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    readme_meta = data["tool"]["scikit-build"]["metadata"]["readme"]
    assert readme_meta == {
        "provider": "scikit_build_core.metadata.fancy_pypi_readme"
    }, "scikit-build-core must use ONLY the fancy_pypi_readme provider (no inline config)"


# ---------------------------------------------------------------------------
# 3. The assembled long-description (built via the library, as both backends do)
# ---------------------------------------------------------------------------


def _assemble_long_description() -> str:
    """Build the long-description exactly the way both backends do:

    scikit-build-core's provider and hatchling's plugin both call
    ``hatch_fancy_pypi_readme``'s ``load_and_validate_config`` +
    ``build_text`` against this ``[tool.hatch...fancy-pypi-readme]``
    block. The path fragments are relative, so we chdir to PY_ROOT.
    """
    pytest.importorskip("hatch_fancy_pypi_readme")
    from hatch_fancy_pypi_readme._builder import build_text
    from hatch_fancy_pypi_readme._config import load_and_validate_config

    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    config = load_and_validate_config(
        data["tool"]["hatch"]["metadata"]["hooks"]["fancy-pypi-readme"]
    )
    cwd = os.getcwd()
    try:
        os.chdir(PY_ROOT)
        return build_text(
            config.fragments,
            getattr(config, "substitutions", []),
            version=srmech.__version__,
            package_name="srmech",
        )
    finally:
        os.chdir(cwd)


def test_long_description_starts_with_readme():
    text = _assemble_long_description()
    readme_head = README.read_text(encoding="utf-8").splitlines()[0]
    assert text.lstrip().startswith(readme_head)
    # The README body is present (not just the title).
    assert "Stored-Relationship Mechanism" in text


def test_long_description_has_sliced_changelog_and_link():
    text = _assemble_long_description()
    assert "## Changelog" in text
    # current-minor entries present...
    assert _CURRENT_MINOR in text.split("## Changelog", 1)[1]
    assert re.search(r"^## \[" + re.escape(_CURRENT_MINOR), text, re.MULTILINE)
    # ...prior-minor entry header absent (slice bounded correctly)...
    assert _PRIOR_MINOR_HEADER not in text
    # ...and the full-changelog link is the closing element.
    assert text.rstrip().endswith("CHANGELOG.md)**")
    assert "**[Full changelog" in text


def test_long_description_changelog_text_matches_changelog_source():
    """The changelog text in the long-description must come verbatim from
    CHANGELOG.md (single source of truth — no hand-maintained copy)."""
    text = _assemble_long_description()
    sliced = _changelog_slice().strip()
    assert sliced in text, "the long-description changelog must be the CHANGELOG.md slice"
