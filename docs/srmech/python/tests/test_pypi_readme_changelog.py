"""MS #20 rc8 — the PyPI long-description is assembled dynamically.

srmech ships TWO build backends:

* ``pyproject.toml``        — scikit-build-core (platform wheels)
* ``pyproject-pure.toml``   — hatchling        (the py3-none-any wheel)

Both must render the SAME PyPI long-description: the full ``README.md``
followed by a ``## Changelog`` section sliced to ONLY the current-minor
``CHANGELOG.md`` entries, then a "Full changelog" link. The slice is driven
by HTML-comment markers in ``CHANGELOG.md`` so the changelog text is never
hand-duplicated (CHANGELOG.md stays the single source of truth).

⚠️ WHY THE SLICE ASSERTIONS WERE REWRITTEN AT rc453 (``#T1167``)
================================================================
This file ran GREEN while the published project page silently lost **six
consecutive releases** — rc447 through rc452, 132,112 characters. Measured on
the shipped artifact: ``test.pypi.org/pypi/srmech/0.9.0rc452/json`` reported an
``info.description`` whose newest ``## [0.9.0rcN]`` heading was ``[0.9.0rc446]``.

The mechanism: entries are PREPENDED to the top of ``CHANGELOG.md``, and the
start marker sat at line 1305. Everything written after the marker was last
moved therefore sat ABOVE the slice window and was cut.

**Every assertion this file made about the slice was existential or negative;
none was a completeness assertion.** "contains at least one current-minor
entry" and "every heading inside is current-minor" are both satisfied by ANY
NON-EMPTY SUFFIX of the entry list — which is exactly the shape the defect
produces. A loop over what is inside the slice structurally cannot see what was
left out of it. That is
``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``.

A SECOND vacuity sat beside it: the bounded-below sentinel was pinned to
``"## [0.5.0]"`` while the live prior minor was ``[0.8.2]``, so it could not
have fired until the end marker slid past THREE whole minor blocks. That literal
and the "(0.6.0)" the docstring used to repeat came from the version this file
was written at; ``_CURRENT_MINOR`` beside them was derived live and moved with
the package while they did not. ``test_readme_currency_rc419`` states the
lesson: a number written as a literal, with no tie to the value it describes,
rots — the same number written as a live lookup cannot.

These tests now guard:

1. the slice markers exist, are unique, and are correctly ordered;
2. **COMPLETENESS** — the slice's NEWEST heading equals ``srmech.__version__``,
   and the slice holds EVERY current-minor entry in the file (list equality, so
   a drop, a leak and a reordering are all visible);
3. **BOUNDEDNESS** — the prior-minor sentinel is DERIVED from the first heading
   below the end marker, never pinned;
4. both pyprojects declare ``dynamic = ["readme"]`` (no static ``readme``) +
   carry a byte-identical ``[tool.hatch.metadata.hooks.fancy-pypi-readme]``
   block + agree on ``[project].description``;
5. the assembled long-description (built via the ``hatch-fancy-pypi-readme``
   library, exactly as both backends do) starts with the README, contains the
   current-minor changelog header + entries, EXCLUDES the prior minor, and ends
   with the full-changelog link;
6. a RETRO-CHECK that runs the shipped predicates against the rc452 marker
   placement and requires them to FAIL — a gate that would not have caught the
   defect that motivated it is not the gate.

Every version-bearing value here is resolved live from ``srmech.__version__``
or read out of ``CHANGELOG.md``. Nothing in this file is pinned to a release.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# tomllib is stdlib on 3.11+; tomli is the back-port for 3.10. Mirror
# the package's own shim in srmech.dsl._catalog so this guard runs on
# every supported interpreter (the 3.10 wheel ships tomli as a dep).
try:
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover - 3.10 path
    import tomli as _toml  # type: ignore[no-redef]

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

_CURRENT_MINOR = ".".join(srmech.__version__.split(".")[:2]) + "."  # e.g. "0.9."

#: A changelog entry heading: ``## [0.9.0rc453] - ...`` -> ``0.9.0rc453``.
_ENTRY_HEADING = re.compile(r"^## \[([^\]]+)\]", re.MULTILINE)

#: Headings that are legitimately inside the slice while naming no version.
#:
#: ``[Unreleased]`` is the Keep a Changelog section holding work that landed
#: WITHOUT a version bump (CI topology, doc-only fixes). It belongs in the
#: published long-description — it describes shipped work — but it is not a
#: release, so the completeness comparison is made over VERSIONS and this set
#: is subtracted explicitly.
#:
#: ⚠️ This is a NAMED ALLOWANCE, not a wildcard. Anything else appearing in the
#: slice without a current-minor version is a LEAK and fails. Do not widen this
#: to "skip non-version headings" — that is how the leak direction gets lost.
_NON_VERSION_HEADINGS = frozenset({"Unreleased"})


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


def _slice_of(text: str) -> str:
    """The marker-delimited region of ``text``.

    Takes the text as a PARAMETER rather than reading the file, so the same
    predicates the live tests use can be pointed at a synthetic tree by the
    retro-check. A predicate that can only ever be run against the passing
    case cannot be shown to fail on the failing one.
    """
    start = text.index(START_MARKER) + len(START_MARKER)
    end = text.index(END_MARKER)
    assert start < end, "start marker must precede end marker"
    return text[start:end]


def _changelog_slice() -> str:
    return _slice_of(CHANGELOG.read_text(encoding="utf-8"))


def _slice_headings_of(text: str) -> list[str]:
    """Entry versions inside the slice, in file order."""
    return _ENTRY_HEADING.findall(_slice_of(text))


def _current_minor_headings_of(text: str, minor: str) -> list[str]:
    """EVERY current-minor entry version in the WHOLE file, in file order.

    This is the half the pre-rc453 gate had no expression for. Anything this
    returns which is absent from :func:`_slice_headings_of` was dropped from
    the published long-description.
    """
    return [v for v in _ENTRY_HEADING.findall(text) if v.startswith(minor)]


def _prior_minor_version_of(text: str) -> str:
    """DERIVED bounded-below sentinel: first entry version BELOW the end marker.

    Pinning this to a literal is what let the old check go three minors stale.
    """
    below = text[text.index(END_MARKER) + len(END_MARKER):]
    m = _ENTRY_HEADING.search(below)
    assert m, (
        "no entry heading below the end marker — either the end marker has "
        "reached EOF or the changelog has only one minor, and in both cases "
        "the boundedness check below is vacuous rather than passing"
    )
    return m.group(1)


# ---------------------------------------------------------------------------
# 1. CHANGELOG slice markers
# ---------------------------------------------------------------------------


def test_changelog_markers_exist_and_are_unique():
    text = CHANGELOG.read_text(encoding="utf-8")
    assert text.count(START_MARKER) == 1, "exactly one start marker expected"
    assert text.count(END_MARKER) == 1, "exactly one end marker expected"
    assert text.index(START_MARKER) < text.index(END_MARKER)


def test_slice_newest_entry_is_the_live_version():
    """COMPLETENESS, the direct predicate — THIS is the one that was missing.

    The newest heading inside the slice must be the version being released. It
    fails in the rc that writes an entry above the start marker, rather than
    six rcs later when somebody reads the project page.
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    # The FIRST VERSION heading, so the check is robust to where the
    # [Unreleased] section sits (Keep a Changelog puts it at the top; this file
    # has historically put it mid-list — neither placement is a defect).
    headings = [v for v in _slice_headings_of(text) if v.startswith(_CURRENT_MINOR)]
    assert headings, (
        "the changelog slice contains NO current-minor entry headings at all — "
        "the markers bracket nothing and the published long-description has no "
        "changelog"
    )
    assert headings[0] == srmech.__version__, (
        f"the changelog slice's newest entry is [{headings[0]}] but this tree "
        f"is {srmech.__version__}. New entries are PREPENDED, so an entry "
        f"written ABOVE the start marker is silently cut from the PyPI "
        f"long-description. Move the entry below "
        f"'{START_MARKER}' — do NOT move the marker down to meet it, which is "
        f"the maintenance schedule that dropped rc447-rc452."
    )


def test_slice_holds_every_current_minor_entry():
    """COMPLETENESS, the set form — a drop, a leak or a reorder all fail here.

    List equality rather than set equality on purpose: the slice is contiguous
    and in file order, so order-preserving comparison costs nothing and catches
    one more class.
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    slice_all = _slice_headings_of(text)
    in_slice = [v for v in slice_all if v.startswith(_CURRENT_MINOR)]
    in_file = _current_minor_headings_of(text, _CURRENT_MINOR)
    missing = [v for v in in_file if v not in in_slice]
    leaked = [
        v for v in slice_all
        if not v.startswith(_CURRENT_MINOR) and v not in _NON_VERSION_HEADINGS
    ]
    assert in_slice == in_file, (
        f"the changelog slice does not hold every {_CURRENT_MINOR}x entry.\n"
        f"  in file : {len(in_file)}\n"
        f"  in slice: {len(in_slice)}\n"
        f"  DROPPED from the published long-description: {missing or 'none'}\n"
        f"Six releases were dropped this way before rc453; the gate was green "
        f"throughout because it only ever asked what was INSIDE the slice."
    )
    assert not leaked, (
        f"headings leaked INTO the slice that are neither {_CURRENT_MINOR}x "
        f"entries nor the named non-version allowances "
        f"{sorted(_NON_VERSION_HEADINGS)}: {leaked}. The end marker is too low."
    )


def test_end_marker_is_bounded_against_the_real_prior_minor():
    """BOUNDEDNESS, with a DERIVED sentinel rather than a pinned literal.

    The old check pinned ``## [0.5.0]`` while the live neighbour was
    ``[0.8.2]``, so it could not have fired until the end marker slid past
    three whole minor blocks.
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    prior = _prior_minor_version_of(text)
    assert not prior.startswith(_CURRENT_MINOR), (
        f"the first entry below the end marker is [{prior}], which is itself a "
        f"{_CURRENT_MINOR}x entry — the end marker is too high and is cutting "
        f"current-minor entries out of the slice"
    )
    assert f"## [{prior}]" not in _slice_of(text), (
        f"the prior-minor header '## [{prior}]' is inside the slice — the end "
        f"marker is misplaced"
    )


# ---------------------------------------------------------------------------
# 2. Both pyprojects declare the dynamic readme + share the hook block
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [PYPROJECT, PYPROJECT_PURE])
def test_pyproject_declares_dynamic_readme(path: Path):
    data = _toml.loads(path.read_text(encoding="utf-8"))
    project = data["project"]
    assert "readme" not in project, f"{path.name} must not carry a static readme key"
    assert "readme" in project.get("dynamic", []), (
        f"{path.name} must declare dynamic = ['readme']"
    )


@pytest.mark.parametrize("path", [PYPROJECT, PYPROJECT_PURE])
def test_pyproject_declares_fancy_pypi_readme_hook(path: Path):
    data = _toml.loads(path.read_text(encoding="utf-8"))
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
    data = _toml.loads(path.read_text(encoding="utf-8"))
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
    main = _toml.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["description"]
    pure = _toml.loads(PYPROJECT_PURE.read_text(encoding="utf-8"))["project"][
        "description"
    ]
    assert main == pure
    # PyPI Summary hard limit is 512 chars; guard headroom.
    assert len(main) <= 512


def test_scikit_build_core_readme_provider_configured():
    data = _toml.loads(PYPROJECT.read_text(encoding="utf-8"))
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

    data = _toml.loads(PYPROJECT.read_text(encoding="utf-8"))
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
    # ...INCLUDING the newest one. The assembled description is the artifact
    # that actually ships, so the completeness claim is re-checked HERE rather
    # than only against the slice: rc447-rc452 proved the slice and the
    # description can agree with each other and both be short.
    assembled = _ENTRY_HEADING.findall(text)
    assert assembled and assembled[0] == srmech.__version__, (
        f"the assembled long-description's newest changelog entry is "
        f"[{assembled[0] if assembled else 'NONE'}], not {srmech.__version__} "
        f"— this is the artifact PyPI renders"
    )
    # ...prior-minor entry header absent (slice bounded correctly), against the
    # DERIVED neighbour rather than a pinned literal...
    prior = _prior_minor_version_of(CHANGELOG.read_text(encoding="utf-8"))
    assert f"## [{prior}]" not in text
    # ...and the full-changelog link is the closing element.
    assert text.rstrip().endswith("CHANGELOG.md)**")
    assert "**[Full changelog" in text


def test_the_completeness_predicates_would_have_fired_on_the_rc452_placement():
    """RETRO-CHECK — a gate that would not have caught the defect is not the gate.

    Reconstructs the rc452 file SHAPE (start marker BELOW the newest entries,
    which is where it sat at ``CHANGELOG.md:1305``) and runs the SHIPPED
    predicates against it. Both completeness assertions must fail, and — the
    part that matters — the two predicates this file used BEFORE rc453 must
    still PASS on that same text, which is the demonstration that they were
    the wrong measurement rather than a correct one badly applied.
    """
    minor = "0.9."
    rc452_shape = (
        "# srmech changelog\n\n"
        "## [0.9.0rc452] - newest, written ABOVE the marker\n\nbody\n\n"
        "## [0.9.0rc451] - also above\n\nbody\n\n"
        f"{START_MARKER}\n\n"
        "## [0.9.0rc450] - the first one the slice can see\n\nbody\n\n"
        "## [0.9.0rc449]\n\nbody\n\n"
        f"{END_MARKER}\n"
        "## [0.8.2] - the prior minor\n\nbody\n"
    )

    in_slice = _slice_headings_of(rc452_shape)
    in_file = _current_minor_headings_of(rc452_shape, minor)

    # --- the SHIPPED predicates: both must FAIL on this text ---
    assert in_slice[0] != "0.9.0rc452", (
        "the newest-entry predicate no longer detects the rc452 placement — it "
        "has been loosened and the defect can return"
    )
    assert in_slice != in_file, (
        "the every-entry predicate no longer detects the rc452 placement — it "
        "has been loosened and the defect can return"
    )
    assert [v for v in in_file if v not in in_slice] == ["0.9.0rc452", "0.9.0rc451"], (
        "the retro-check's own fixture stopped reproducing the defect shape"
    )

    # --- the PRE-rc453 predicates: both PASS on the very same text ---
    # This is the finding, made executable. They are not weak versions of the
    # right check; they range over a population the defect itself selects.
    sliced_text = _slice_of(rc452_shape)
    assert minor in sliced_text, "old predicate 1 was 'contains the current minor'"
    assert re.search(r"^## \[" + re.escape(minor), sliced_text, re.MULTILINE), (
        "old predicate 2 was 'at least one current-minor entry header'"
    )
    for header in re.findall(r"^## \[[^\]]+\]", sliced_text, re.MULTILINE):
        assert minor in header, "old predicate 3 was 'nothing foreign leaked IN'"

    # --- and the pinned sentinel could not fire either ---
    # '## [0.5.0]' is absent from this text no matter where the end marker sits,
    # which is exactly why a pinned boundary is not a boundary check.
    assert "## [0.5.0]" not in sliced_text
    assert _prior_minor_version_of(rc452_shape) == "0.8.2", (
        "the DERIVED sentinel must name the real neighbour, not a stale literal"
    )


def test_long_description_changelog_text_matches_changelog_source():
    """The changelog text in the long-description must come verbatim from
    CHANGELOG.md (single source of truth — no hand-maintained copy)."""
    text = _assemble_long_description()
    sliced = _changelog_slice().strip()
    assert sliced in text, "the long-description changelog must be the CHANGELOG.md slice"
