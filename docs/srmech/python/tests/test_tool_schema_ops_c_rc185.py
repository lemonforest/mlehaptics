"""rc185 — the C tool-schema PROJECTION ops (the HOST-GLUE tier).

A bare-C host (no Python) must produce the three tool-schema projections a
Python host does — ``get_tool_schema`` / ``tool_schema_view`` (the whole-schema
JSON) and ``tool_entries_to_mcp_defs`` (the advertised MCP tool-def array) —
over the rc184 const registry table. This test pins:

1. **native == pure.**
   - ``srmech_get_tool_schema`` / ``srmech_tool_schema_view`` are BYTE-IDENTICAL
     to the rc184 canonical (sorted) whole-schema JSON, and json-parse back
     EQUAL to ``get_tool_schema().to_jsonable()`` (structural identity). The C
     JSON reconstructs the ToolSchema OBJECT equal to the pure one (proves the
     C path realises the data — the option-(a) evidence, without runtime-routing
     get_tool_schema through C, which would make the rc184 hash-ratchet circular).
   - ``srmech_tool_entries_to_mcp_defs`` is BYTE-IDENTICAL to
     ``json.dumps(list(tool_entries_to_mcp_defs()), separators=(",", ":"))``.
2. **runtime dispatch.** ``tool_schema_view()`` + ``tool_entries_to_mcp_defs()``
   return values equal to their pure forms whether native or pure (the dispatch
   is value-transparent).
3. **the two-pass buffer contract** (size-query == fill length; too-small →
   OVERFLOW; NULL out_len → NULL_ARG).

The native-requiring assertions ``skipif`` cleanly when the rc185 C peer is
absent (a pure / numpy-absent / stale-lib host uses the Python path). The
pure-path structural checks always run. numpy-free.
"""

from __future__ import annotations

import json

import pytest

from srmech.amsc import _native
from srmech.amsc.tool_schema import (
    ToolEntry,
    ToolParameter,
    ToolReturn,
    ToolSchema,
    get_tool_schema,
    tool_schema_view,
    warmup_all,
)
from srmech.mcp._tools import tool_entries_to_mcp_defs

warmup_all()

_needs_native = pytest.mark.skipif(
    not _native.has_native_tool_schema_ops(),
    reason="rc185 tool-schema projection C peers not loaded (pure / stale host)",
)


def _canonical_sorted() -> bytes:
    schema = get_tool_schema()
    return json.dumps(
        schema.to_jsonable(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _pure_mcp_defs_bytes() -> bytes:
    return json.dumps(
        list(tool_entries_to_mcp_defs()), separators=(",", ":")
    ).encode("utf-8")


def _schema_from_jsonable(d: dict) -> ToolSchema:
    """Rebuild a ToolSchema from a to_jsonable()-shaped dict (the C JSON parsed
    back) — the object-reconstruction the native path would use under option
    (a); here it PROVES the C DATA realises the pure object."""
    tools = []
    for t in d["tools"]:
        params = tuple(
            ToolParameter(
                name=p["name"], type=p["type"],
                required=p["required"], summary=p.get("summary", ""),
            )
            for p in t["parameters"]
        )
        returns = None
        if "returns" in t:
            returns = ToolReturn(
                type=t["returns"]["type"], shape=t["returns"].get("shape", "")
            )
        tools.append(ToolEntry(
            name=t["name"], owner=t["owner"], category=t["category"],
            summary=t["summary"], parameters=params, returns=returns,
            smoke_test_hint=t.get("smoke_test_hint"), example=t.get("example"),
            mcp_callable=t.get("mcp_callable", True),
            mcp_unavailable_reason=t.get("mcp_unavailable_reason"),
        ))
    return ToolSchema(
        srmech_version=d["srmech_version"],
        tool_schema_version=d["tool_schema_version"],
        tools=tuple(tools),
    )


# ──────────────────────────────────────────────────────────────────────
# 1. native == pure — the whole-schema ops
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_get_tool_schema_c_byte_identical_to_canonical() -> None:
    c = _native.get_tool_schema_c()
    assert c is not None
    assert c == _canonical_sorted()


@_needs_native
def test_tool_schema_view_c_byte_identical_to_canonical() -> None:
    """srmech_tool_schema_view emits the SAME bytes as get_tool_schema
    (Python tool_schema_view() IS get_tool_schema().to_jsonable())."""
    c = _native.tool_schema_view_c()
    assert c is not None
    assert c == _canonical_sorted()
    assert c == _native.get_tool_schema_c()


@_needs_native
def test_get_tool_schema_c_parses_back_equal_to_to_jsonable() -> None:
    """Structural identity: the C JSON json-parses back EQUAL to
    get_tool_schema().to_jsonable() (dict equality is order-insensitive)."""
    c = _native.get_tool_schema_c()
    assert c is not None
    assert json.loads(c.decode("utf-8")) == get_tool_schema().to_jsonable()


@_needs_native
def test_get_tool_schema_c_reconstructs_the_object() -> None:
    """The strongest native==pure evidence: rebuilding the ToolSchema OBJECT
    from the C JSON yields a value-equal object (frozen-dataclass equality over
    tools / parameters / returns) — the C path realises the data."""
    c = _native.get_tool_schema_c()
    assert c is not None
    recon = _schema_from_jsonable(json.loads(c.decode("utf-8")))
    assert recon == get_tool_schema()


# ──────────────────────────────────────────────────────────────────────
# 2. native == pure — the MCP-defs projection
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_mcp_defs_c_byte_identical_to_python() -> None:
    c = _native.tool_entries_to_mcp_defs_c()
    assert c is not None
    assert c == _pure_mcp_defs_bytes()


@_needs_native
def test_mcp_defs_c_parses_back_equal() -> None:
    c = _native.tool_entries_to_mcp_defs_c()
    assert c is not None
    assert json.loads(c.decode("utf-8")) == list(tool_entries_to_mcp_defs())


@_needs_native
def test_mcp_defs_type_lexicon_and_hint_mapping() -> None:
    """The C static type-lexicon + wire-hint table mirror the Python maps: a
    known type maps to its JSON-schema token + carries its hint; an unknown type
    degrades to 'string' with no hint. Checked THROUGH the emitted defs so the
    C and Python lexicons must agree exactly."""
    from srmech.mcp._tools import _ENCODING_HINT, _TYPE_LEXICON

    defs = json.loads(_native.tool_entries_to_mcp_defs_c().decode("utf-8"))
    by_name = {d["name"]: d for d in defs}
    for entry in get_tool_schema().tools:
        if not entry.mcp_callable:
            continue
        props = by_name[entry.name]["inputSchema"]["properties"]
        for p in entry.parameters:
            prop = props[p.name]
            assert prop["type"] == _TYPE_LEXICON.get(p.type, "string")
            hint = _ENCODING_HINT.get(p.type)
            if hint is not None:
                assert f"({hint})" in prop["description"]


# ──────────────────────────────────────────────────────────────────────
# 3. runtime dispatch is value-transparent
# ──────────────────────────────────────────────────────────────────────


def test_tool_schema_view_dispatch_equals_pure() -> None:
    """tool_schema_view() (which runtime-dispatches to native when available)
    is VALUE-equal to the pure get_tool_schema().to_jsonable() either way."""
    assert tool_schema_view() == get_tool_schema().to_jsonable()


def test_mcp_defs_dispatch_equals_pure() -> None:
    """tool_entries_to_mcp_defs() (which runtime-dispatches to native) yields
    the SAME def list as the pure per-entry projection either way."""
    got = list(tool_entries_to_mcp_defs())
    pure = [
        _pure_def(e) for e in get_tool_schema().tools if e.mcp_callable
    ]
    assert got == pure


def _pure_def(entry: ToolEntry) -> dict:
    from srmech.mcp._tools import tool_entry_to_mcp_def
    return tool_entry_to_mcp_def(entry)


def test_mcp_defs_name_filter_still_filters() -> None:
    """A name_filter takes the pure path (native only serves the unfiltered
    catalog) and still filters correctly."""
    only = "srmech.amsc.format.sha256_bytes"
    got = list(tool_entries_to_mcp_defs(name_filter=lambda n: n == only))
    assert len(got) == 1 and got[0]["name"] == only


# ──────────────────────────────────────────────────────────────────────
# 4. the two-pass buffer contract
# ──────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("sym", [
    "srmech_get_tool_schema",
    "srmech_tool_schema_view",
    "srmech_tool_entries_to_mcp_defs",
])
def test_size_query_matches_fill_and_overflow(sym: str) -> None:
    import ctypes

    fn = getattr(_native.LIB, sym)
    need = ctypes.c_size_t(0)
    rc = fn(None, ctypes.c_size_t(0), ctypes.byref(need))
    assert rc == _native.SRMECH_OK
    assert need.value > 0

    raw = (ctypes.c_char * need.value)()
    got = ctypes.c_size_t(0)
    rc = fn(ctypes.cast(raw, ctypes.c_void_p),
            ctypes.c_size_t(need.value), ctypes.byref(got))
    assert rc == _native.SRMECH_OK
    assert got.value == need.value

    # too-small buffer overflows cleanly (never writes past the buffer)
    small = (ctypes.c_char * 8)()
    g2 = ctypes.c_size_t(0)
    rc = fn(ctypes.cast(small, ctypes.c_void_p),
            ctypes.c_size_t(8), ctypes.byref(g2))
    assert rc == _native.SRMECH_ERR_OVERFLOW

    # NULL out_len -> NULL_ARG
    rc = fn(None, ctypes.c_size_t(0), None)
    assert rc == _native.SRMECH_ERR_NULL_ARG


# ──────────────────────────────────────────────────────────────────────
# 5. pure-path invariants (always run — no native required)
# ──────────────────────────────────────────────────────────────────────


def test_mcp_defs_shape_is_valid() -> None:
    for d in tool_entries_to_mcp_defs():
        assert set(d.keys()) == {"name", "description", "inputSchema"}
        schema = d["inputSchema"]
        assert schema["type"] == "object"
        assert isinstance(schema["properties"], dict)
        assert isinstance(schema["required"], list)
        # every required key references a real property
        for r in schema["required"]:
            assert r in schema["properties"]


def test_reconstruction_helper_round_trips_pure() -> None:
    """Sanity: the object-reconstruction helper round-trips the PURE canonical
    JSON (independent of native) — so the native reconstruction test is testing
    the C bytes, not a broken helper."""
    recon = _schema_from_jsonable(json.loads(_canonical_sorted().decode("utf-8")))
    assert recon == get_tool_schema()
