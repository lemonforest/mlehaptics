"""Unit tests for srmech.amsc.tool_schema (Task #198)."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from srmech.amsc import tool_schema as ts
from srmech.amsc.tool_schema import (
    TOOL_SCHEMA_VERSION,
    ToolEntry,
    ToolParameter,
    ToolReturn,
    ToolSchemaConflictError,
    ToolSchemaValidationError,
    get_tool_schema,
    load_extension_file,
    register_profile_tools,
    register_tool,
    tool_schema_view,
    unregister_profile_tools,
)


def test_amsc_builtin_tools_registered_at_import() -> None:
    """At import time tool_schema._register_amsc_tools() registers the
    AMSC framework's own entries. They should be visible without any
    further setup."""
    view = get_tool_schema()
    assert view.srmech_version
    assert view.tool_schema_version == TOOL_SCHEMA_VERSION
    names = {t.name for t in view.tools}
    assert "srmech.amsc.format.sha256_bytes" in names
    assert "srmech.amsc.format.read_ndjson" in names
    assert "srmech.amsc.catalog.register_attested_root" in names
    # All builtin tools have owner == "srmech"
    for t in view.tools:
        if t.name.startswith("srmech."):
            assert t.owner == "srmech"


def test_get_tool_schema_serialisable_to_json() -> None:
    """tool_schema_view() must produce a JSON-serialisable dict."""
    view = tool_schema_view()
    # Round-trip through json
    s = json.dumps(view)
    parsed = json.loads(s)
    assert parsed["tool_schema_version"] == TOOL_SCHEMA_VERSION
    assert isinstance(parsed["tools"], list)
    assert len(parsed["tools"]) > 0


def test_idempotent_re_registration_is_silent() -> None:
    """Re-registering an identical entry is a no-op (idempotent)."""
    entry = ToolEntry(
        name="test.idempotent",
        owner="srmech",
        category="test",
        summary="idempotent test entry",
    )
    try:
        register_tool(entry)
        register_tool(entry)  # should not raise
    finally:
        # cleanup: the entry has owner "srmech", so unregister_profile_tools is a
        # no-op for it — pop it from the global registry directly so it does NOT
        # leak into the schema singleton and inflate other tests' tools.total.
        ts._REGISTRY.pop("test.idempotent", None)


def test_conflicting_re_registration_raises() -> None:
    """Registering an entry with the same name but different content
    raises ToolSchemaConflictError."""
    e1 = ToolEntry(
        name="test.conflicting",
        owner="srmech",
        category="test",
        summary="first version",
    )
    e2 = ToolEntry(
        name="test.conflicting",
        owner="srmech",
        category="test",
        summary="DIFFERENT version",
    )
    try:
        register_tool(e1)
        with pytest.raises(ToolSchemaConflictError):
            register_tool(e2)
    finally:
        # cleanup: pop the injected entry so it does NOT leak into the schema
        # singleton (owner "srmech" → unregister_profile_tools can't remove it).
        ts._REGISTRY.pop("test.conflicting", None)


def test_register_profile_tools_enforces_owner_tag() -> None:
    """The owner field on every entry must match the profile_name
    passed to register_profile_tools."""
    entries = [
        ToolEntry(
            name="alpha.thing",
            owner="alpha",
            category="test",
            summary="thing in profile alpha",
        ),
        ToolEntry(
            name="alpha.other",
            owner="beta",   # WRONG — owner mismatch
            category="test",
            summary="thing claiming to be in beta",
        ),
    ]
    with pytest.raises(ToolSchemaValidationError):
        register_profile_tools("alpha", entries)
    # cleanup any partial state
    unregister_profile_tools("alpha")
    unregister_profile_tools("beta")


def test_unregister_profile_tools_removes_all() -> None:
    """unregister_profile_tools removes every entry owned by the
    named profile."""
    entries = [
        ToolEntry(name="gamma.a", owner="gamma", category="test", summary="a"),
        ToolEntry(name="gamma.b", owner="gamma", category="test", summary="b"),
    ]
    register_profile_tools("gamma", entries)

    view_before = get_tool_schema()
    assert len(view_before.by_owner("gamma")) == 2

    n = unregister_profile_tools("gamma")
    assert n == 2

    view_after = get_tool_schema()
    assert len(view_after.by_owner("gamma")) == 0


def test_by_owner_filter() -> None:
    """ToolSchema.by_owner returns only tools owned by the given owner."""
    entries = [
        ToolEntry(name="delta.x", owner="delta", category="test", summary="x"),
    ]
    register_profile_tools("delta", entries)
    try:
        view = get_tool_schema()
        srmech_tools = view.by_owner("srmech")
        delta_tools = view.by_owner("delta")
        assert all(t.owner == "srmech" for t in srmech_tools)
        assert all(t.owner == "delta" for t in delta_tools)
        assert len(srmech_tools) > 0  # builtins exist
        assert len(delta_tools) == 1
    finally:
        unregister_profile_tools("delta")


def test_lookup() -> None:
    """ToolSchema.lookup returns the entry by full dotted name."""
    view = get_tool_schema()
    entry = view.lookup("srmech.amsc.format.sha256_bytes")
    assert entry is not None
    assert entry.owner == "srmech"
    assert entry.category == "format"
    assert view.lookup("nonexistent.thing.somewhere") is None


def test_load_extension_file(tmp_path: Path) -> None:
    """load_extension_file parses a TOML extension and returns
    correctly-owned ToolEntry list."""
    toml_content = textwrap.dedent("""
        [[tools]]
        name = "test_profile.do_thing"
        category = "test"
        summary = "Test that the loader works"

        [[tools.parameters]]
        name = "x"
        type = "int"
        required = true

        [tools.returns]
        type = "str"
        shape = "echoed string"

        [tools.smoke_test_hint]
        x = 1

        [[tools]]
        name = "test_profile.another"
        category = "test"
        summary = "Another tool"
    """).strip()
    f = tmp_path / "ext.toml"
    f.write_text(toml_content, encoding="utf-8")

    entries = load_extension_file(str(f), owner="test_profile")
    assert len(entries) == 2
    assert entries[0].name == "test_profile.do_thing"
    assert entries[0].owner == "test_profile"
    assert entries[0].returns is not None
    assert entries[0].returns.type == "str"
    assert entries[0].parameters[0].name == "x"
    assert entries[0].smoke_test_hint == {"x": 1}
    assert entries[1].name == "test_profile.another"
    assert entries[1].returns is None


def test_load_extension_file_missing_required_field(tmp_path: Path) -> None:
    """load_extension_file raises ToolSchemaValidationError when a
    required field is missing from any tool entry."""
    toml_content = textwrap.dedent("""
        [[tools]]
        name = "incomplete.thing"
        # MISSING category + summary
    """).strip()
    f = tmp_path / "bad.toml"
    f.write_text(toml_content, encoding="utf-8")

    with pytest.raises(ToolSchemaValidationError):
        load_extension_file(str(f), owner="incomplete")


def test_tool_entry_serialisation_roundtrip() -> None:
    """A ToolEntry's to_jsonable() output round-trips through json
    without loss of structure."""
    entry = ToolEntry(
        name="roundtrip.test",
        owner="srmech",
        category="test",
        summary="A round-trip test entry",
        parameters=(
            ToolParameter("x", "int", required=True, summary="An integer"),
            ToolParameter("y", "Optional[str]", required=False),
        ),
        returns=ToolReturn(type="dict", shape="some output shape"),
        smoke_test_hint={"x": 1, "y": "hello"},
    )
    payload = entry.to_jsonable()
    s = json.dumps(payload)
    parsed = json.loads(s)
    assert parsed["name"] == "roundtrip.test"
    assert parsed["parameters"][0]["name"] == "x"
    assert parsed["parameters"][1]["required"] is False
    assert parsed["returns"]["type"] == "dict"
    assert parsed["smoke_test_hint"]["x"] == 1
