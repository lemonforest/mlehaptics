"""Tests for the LLM tool-schema export surface.

Pins:
  - Every bridge tool has a non-empty description.
  - All 4 formats (anthropic / openai / mcp / jsonschema) wrap the
    same tool dict differently but consistently.
  - The newly-shipped CMB cosmology tools are enumerated.
  - Filter-by-prefix works.
  - Type-hint mapping handles int / str / Optional / List / Dict.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge


def test_list_tool_names_returns_sorted_inventory() -> None:
    result = bridge.list_tool_names()
    assert result["ok"] is True
    assert result["filter_prefix"] is None
    assert result["n_tools"] > 200  # Bridge has ~240 public functions
    names = result["tool_names"]
    assert names == sorted(names), "tool names must be sorted"
    # All names must be valid Python identifiers (no underscore prefix)
    for name in names:
        assert name.isidentifier()
        assert not name.startswith("_")


def test_list_tool_names_filter_prefix() -> None:
    result = bridge.list_tool_names(filter_prefix="get_cmb_")
    assert result["ok"] is True
    assert result["filter_prefix"] == "get_cmb_"
    # cmb_power_spectrum + cmb_anomalies ship at least:
    # get_cmb_power_at_ell, get_cmb_first_acoustic_peak, get_cmb_anomaly
    assert result["n_tools"] >= 3
    for name in result["tool_names"]:
        assert name.startswith("get_cmb_")


def test_get_tool_schema_anthropic_default() -> None:
    result = bridge.get_tool_schema()
    assert result["ok"] is True
    assert result["format"] == "anthropic"
    assert result["n_tools"] > 200
    # Spot-check the first tool's anthropic shape
    first = result["tools"][0]
    assert set(first.keys()) >= {"name", "description", "input_schema"}
    assert first["input_schema"]["type"] == "object"
    assert "properties" in first["input_schema"]
    assert "required" in first["input_schema"]


def test_get_tool_schema_openai_wrapper() -> None:
    result = bridge.get_tool_schema(format="openai")
    assert result["ok"] is True
    first = result["tools"][0]
    assert first["type"] == "function"
    assert set(first["function"].keys()) >= {"name", "description", "parameters"}


def test_get_tool_schema_mcp_wrapper() -> None:
    result = bridge.get_tool_schema(format="mcp")
    assert result["ok"] is True
    first = result["tools"][0]
    # MCP uses camelCase inputSchema (vs anthropic's input_schema)
    assert "inputSchema" in first
    assert "name" in first
    assert "description" in first


def test_get_tool_schema_jsonschema_no_wrapper() -> None:
    result = bridge.get_tool_schema(format="jsonschema")
    assert result["ok"] is True
    first = result["tools"][0]
    # Plain format uses `parameters` directly, no LLM-vendor wrapping
    assert set(first.keys()) == {"name", "description", "parameters"}


def test_get_tool_schema_rejects_unknown_format() -> None:
    result = bridge.get_tool_schema(format="not-a-real-format")
    assert result["ok"] is False
    assert "unknown format" in result["reason"]


def test_cmb_cosmology_tools_present() -> None:
    """The first cosmology-instrument pair should be enumerated."""
    names = set(bridge.list_tool_names()["tool_names"])
    expected_cmb_tools = {
        "get_cmb_power_at_ell",
        "get_cmb_first_acoustic_peak",
        "list_cmb_power_spectrum",
        "get_cmb_anomaly",
        "list_cmb_anomalies",
    }
    assert expected_cmb_tools.issubset(names)


def test_int_typed_parameter_maps_to_integer() -> None:
    """get_cmb_power_at_ell takes ell: int — should map to integer."""
    result = bridge.get_one_tool_schema("get_cmb_power_at_ell", format="anthropic")
    assert result["ok"] is True
    schema = result["tool"]["input_schema"]
    assert "ell" in schema["properties"]
    assert schema["properties"]["ell"]["type"] == "integer"
    assert "ell" in schema["required"]


def test_str_typed_parameter_maps_to_string() -> None:
    """get_cmb_anomaly takes anomaly_id: str — should map to string."""
    result = bridge.get_one_tool_schema("get_cmb_anomaly", format="anthropic")
    assert result["ok"] is True
    schema = result["tool"]["input_schema"]
    assert "anomaly_id" in schema["properties"]
    assert schema["properties"]["anomaly_id"]["type"] == "string"
    assert "anomaly_id" in schema["required"]


def test_optional_parameter_not_in_required_list() -> None:
    """list_tool_names takes filter_prefix: Optional[str] = None — must
    appear in properties but NOT in required."""
    result = bridge.get_one_tool_schema("list_tool_names", format="anthropic")
    assert result["ok"] is True
    schema = result["tool"]["input_schema"]
    assert "filter_prefix" in schema["properties"]
    assert "filter_prefix" not in schema["required"]


def test_get_one_tool_schema_unknown_name() -> None:
    result = bridge.get_one_tool_schema("definitely_not_a_real_bridge_function")
    assert result["ok"] is False
    assert "unknown tool" in result["reason"]


def test_get_one_tool_schema_unknown_format() -> None:
    result = bridge.get_one_tool_schema(
        "get_cmb_first_acoustic_peak", format="not-a-format"
    )
    assert result["ok"] is False
    assert "unknown format" in result["reason"]


def test_every_tool_has_non_empty_description() -> None:
    """Discipline check: every bridge function must have a docstring."""
    result = bridge.get_tool_schema(format="anthropic")
    missing = []
    for tool in result["tools"]:
        desc = tool["description"]
        if not desc or "no description" in desc:
            missing.append(tool["name"])
    assert not missing, (
        f"Bridge functions without docstrings (LLM tool-use clients "
        f"won't know what they do): {missing[:10]}"
        + (f" ... and {len(missing) - 10} more" if len(missing) > 10 else "")
    )


def test_tool_schema_count_matches_list_names() -> None:
    """list_tool_names and get_tool_schema must enumerate the same set."""
    names = bridge.list_tool_names()["tool_names"]
    schema_names = [t["name"] for t in bridge.get_tool_schema()["tools"]]
    assert sorted(names) == sorted(schema_names)
