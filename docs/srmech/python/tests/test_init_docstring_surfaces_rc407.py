"""rc407 (`#T1076`) — ``srmech``'s module docstring must index its own exports.

THE DEFECT. ``srmech/__init__.py`` opens with a ~1,523-character docstring whose
"Public surfaces" section was exactly two bullets — ``srmech.amsc`` and
``srmech.__version__``. A census over the 15 names in ``srmech.__all__`` found
ONE of them (``__version__``) in the docstring and fourteen absent, including
``describe``, the surface the whole self-recognition arc points readers at.

IT IS NOT A ``help()`` BUG. pydoc renders ``__all__`` regardless, and
``describe`` occurs 13 times in the dump — nothing was hidden. The defect is
BURIAL and CURATION. Measured rc407: the pydoc dump is ~45,900 characters over
~1,018 lines; the DESCRIPTION block a reader scans is characters 122-2,283; the
first FUNCTIONS entry for ``describe()`` lands at character ~19,600, 43% in,
below nine profile-loader symbols. A reader who scans the top and stops sees
only what this docstring lists, so what it lists is the whole surface for them.

SECOND, INDEPENDENT STALENESS in the same docstring: it described "the Phase 3
cutover (planned)" that rewires ephemerides-spectral's bridge to import from
``srmech.amsc.*`` instead of its in-tree mirror. That cutover SHIPPED —
``ephemerides_spectral/bridge.py`` today reads ``from srmech.amsc import
catalog``. The v0.1.x migration narrative (Phase 2, Phase 3, the task ref, the
``_research/`` mirror) occupied about a third of the docstring, above a
two-item index.

THE BACKTICKED FORM IS LOAD-BEARING IN THIS TEST. A bare ``n in doc`` check
passes trivially the moment any ``Profile*`` name is listed, because
``"Profile"`` is a substring of ``"ProfileError"``, ``"ProfileStatus"`` and
four more. Pinning ``f"``srmech.{n}``"`` is what makes the census real.

FAILS BEFORE / PASSES AFTER: against the rc406 docstring,
``test_every_exported_name_is_indexed_in_the_docstring`` fails naming 14 absent
entries and ``test_the_shipped_phase_3_cutover_is_no_longer_called_planned``
fails on the live "Phase 3" string.
"""

import inspect

import srmech


def _doc() -> str:
    doc = inspect.getdoc(srmech)
    assert doc, "srmech has no module docstring"
    return doc


def test_every_exported_name_is_indexed_in_the_docstring():
    """All 15 ``__all__`` names, each in the ``srmech.<name>`` form."""
    doc = _doc()
    missing = [n for n in srmech.__all__ if f"``srmech.{n}``" not in doc]

    assert missing == [], (
        "srmech.__all__ names absent from the module docstring's index: "
        f"{missing}"
    )


def test_the_index_leads_with_the_entry_point():
    """``describe()`` must be the FIRST surface named, not the fourteenth."""
    doc = _doc()

    assert "START HERE" in doc
    first = doc.index("``srmech.describe")
    for name in srmech.__all__:
        if name == "describe":
            continue
        assert first < doc.index(f"``srmech.{name}``"), (
            f"'{name}' is indexed before describe(); the entry point must lead"
        )


def test_the_drill_down_route_is_named_in_the_docstring():
    """An index that never names the registry sends the reader nowhere."""
    doc = _doc()

    assert "srmech.introspect.tool_schema.get_tool_schema()" in doc


def test_the_shipped_phase_3_cutover_is_no_longer_called_planned():
    """The ephemerides bridge cutover SHIPPED; the docstring said 'planned'."""
    doc = _doc()

    assert "Phase 3" not in doc
    assert "Phase 2" not in doc
    assert "_research/" not in doc
    assert "planned" not in doc


def test_the_amsc_naming_note_survived_the_rewrite():
    """Deleting the migration narrative must not take live content with it."""
    doc = _doc()

    assert "Collector or Catalog" in doc
    assert "register_attested_root" in doc


def test_the_docstring_still_carries_no_bare_local_task_ref():
    """Local task IDs autolink to unrelated GitHub issues; this prose ships."""
    import re

    doc = _doc()
    bare = re.findall(r"(?<![`\w])#(\d{2,4})\b", doc)

    assert bare == [], f"bare #NNN refs in a shipped docstring: {bare}"


def test_registry_size_is_unchanged_by_this_rc():
    """No public callable was added, removed or renamed here."""
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    assert len(get_tool_schema().tools) == 559
