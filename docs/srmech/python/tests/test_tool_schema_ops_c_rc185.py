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
import re
from pathlib import Path

import pytest

#: ``docs/srmech/c`` — the hand-maintained C tree. Used by the rc362 lexicon
#: comparison at the foot of this file, which reads C SOURCE (so it runs in the
#: pure cell too) rather than calling into the built library.
_SR_C_ROOT = Path(__file__).resolve().parents[2] / "c"

from srmech import _native
from srmech.introspect.tool_schema import (
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
            explanation=t.get("explanation"),
            mcp_callable=t.get("mcp_callable", True),
            mcp_unavailable_reason=t.get("mcp_unavailable_reason"),
            # rc305 (#943): the compose/preserve cascade layer — omitted keys
            # rebuild to the empty-tuple leaf default.
            composes=tuple(t.get("composes", ())),
            preserves=tuple(t.get("preserves", ())),
            # rc347 (`#T985`): the lane axis — omitted keys rebuild to the
            # undeclared default (None + empty tuple). Both are emitted
            # together or not at all, so one `in` test would do; both are read
            # so a half-emitted pair fails here rather than silently
            # reconstructing a valid-looking entry.
            reads_lane=t.get("reads_lane"),
            reads_input=tuple(t.get("reads_input", ())),
            # rc430 (`#T1127`): the frame axis — same key-omission contract as
            # the lane pair above, and read for the same reason. This helper is
            # the one place a NEW ToolEntry field is caught by round-trip
            # rather than by byte comparison: the canonical JSON was already
            # byte-identical across Python and C, and this still failed,
            # because a reconstruction that silently drops a field rebuilds a
            # valid-LOOKING entry that is not the one it parsed.
            frame_scope=t.get("frame_scope"),
            frame_axis=tuple(t.get("frame_axis", ())),
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


# ──────────────────────────────────────────────────────────────────────
# 6. the two HAND-MIRRORED lexicons, compared DIRECTLY (rc362)
# ──────────────────────────────────────────────────────────────────────
#
# ⚠️ ``c/src/srmech_tool_schema.c`` IS NOT GENERATED. It is absent from
# ``tools/codegen_manifest.GENERATORS`` (six outputs, none of them this file),
# so ``tools/regen_all.py`` will never sync it and no codegen step can. The two
# copies of ``_TYPE_LEXICON`` / ``_ENCODING_HINT`` are kept in step BY HAND,
# under a C comment that says they "mirror ... EXACTLY".
#
# rc362 broke that: two entries were added to the Python maps (the ``Q``
# carrier and the acoustic-spectrum sequence over it) and not to C. The
# existing guard, ``test_mcp_defs_type_lexicon_and_hint_mapping``, DID catch
# it — but only because a live op happened to advertise the new type. It walks
# ops, not tables, so a lexicon entry added to one side and used by NO op stays
# invisible until some future op picks it up, at which point the failure
# surfaces far from the edit that caused it.
#
# This closes that: table vs table, whole sets, no op required. It is also the
# reason it runs in the PURE cell — it reads the C SOURCE rather than calling
# into the library, so a numpy-absent / native-absent host still checks it.

#: One C string literal: a quote, any run of non-quote / non-backslash chars or
#: backslash-escapes, a quote. Built as a named piece because it appears three
#: times and is exactly the sort of escape-dense expression that gets silently
#: mangled when a file is written through a shell heredoc.
_C_STR = r'"(?:[^"\\]|\\.)*"'

_MCP_KV_ENTRY = re.compile(
    r"\{\s*(" + _C_STR + r")\s*,\s*((?:" + _C_STR + r"\s*)+)\}", re.S)


def _c_unescape(literal: str) -> str:
    r"""Decode one C string literal to the ``str`` it denotes.

    The tables store non-ASCII as ``\xNN`` UTF-8 bytes (the em-dash in the
    SpectralHandle and rc362 spectrum hints), so decoding is byte-wise and then
    UTF-8, never char-wise — a char-wise reading would silently mangle exactly
    the entries most likely to drift.
    """
    body = literal[1:-1]
    out = bytearray()
    i = 0
    while i < len(body):
        if body[i] == "\\":
            nxt = body[i + 1]
            if nxt == "x":
                out.append(int(body[i + 2:i + 4], 16))
                i += 4
            elif nxt == "n":
                out.append(0x0A)
                i += 2
            elif nxt == "t":
                out.append(0x09)
                i += 2
            else:
                out.append(ord(nxt))
                i += 2
        else:
            out.extend(body[i].encode("utf-8"))
            i += 1
    return out.decode("utf-8")


def _c_table(name: str) -> "dict[str, str]":
    """Parse ``static const mcp_kv_t <name>[] = { {"k", "v"}, ... };``.

    Adjacent C string literals concatenate, so a value split across source
    lines is rejoined — that is how most of the hint table is written.
    """
    src = (_SR_C_ROOT / "src" / "srmech_tool_schema.c").read_text(encoding="utf-8")
    m = re.search(r"static const mcp_kv_t %s\[\] = \{(.*?)\n\};" % name, src, re.S)
    assert m is not None, (
        f"could not find the C table {name} — it was renamed or its "
        f"declaration shape changed, which would make this whole comparison "
        f"vacuous rather than passing.")
    table: "dict[str, str]" = {}
    seen: "list[str]" = []
    for ent in _MCP_KV_ENTRY.finditer(m.group(1)):
        key = _c_unescape(ent.group(1))
        val = "".join(_c_unescape(p) for p in
                      re.findall(_C_STR, ent.group(2)))
        table[key] = val
        seen.append(key)
    # rc363: a DUPLICATE row is invisible to the set comparison below — the
    # dict collapses it — while C's linear lookup returns the FIRST match. So a
    # duplicate whose two values disagree would make the C host answer one way
    # and this test agree with the other. Measured hazard, not hypothetical: a
    # rebase auto-merge produced exactly this in MCP_TYPE_LEXICON at rc363
    # (rc362 added {"Q","array"} near the top of the table while a concurrent
    # branch appended the same key at the bottom), and the strict-equality test
    # would have passed over it.
    dupes = sorted({k for k in seen if seen.count(k) > 1})
    assert not dupes, (
        f"{name} declares {dupes} more than once. C resolves the FIRST match "
        f"and this parser keeps the LAST, so the table and the host can "
        f"disagree while every comparison below still passes. Remove the "
        f"duplicate row.")
    return table


def test_the_c_and_python_mcp_lexicons_are_the_same_table() -> None:
    """STRICT EQUALITY, both directions, on both tables.

    Not "the C side has at least what Python has": an entry present only in C
    is equally a drift, and it is the direction a Python-side deletion
    produces.
    """
    from srmech.mcp._tools import _ENCODING_HINT, _TYPE_LEXICON

    for label, c_name, py in (("_TYPE_LEXICON", "MCP_TYPE_LEXICON", _TYPE_LEXICON),
                              ("_ENCODING_HINT", "MCP_ENCODING_HINT", _ENCODING_HINT)):
        c = _c_table(c_name)
        assert len(c) > 20, (
            f"{c_name} parsed to only {len(c)} entries — the parser has "
            f"stopped observing and this test is vacuous.")
        only_py = sorted(set(py) - set(c))
        only_c = sorted(set(c) - set(py))
        differs = sorted(k for k in set(py) & set(c) if py[k] != c[k])
        assert not (only_py or only_c or differs), (
            f"{label} and {c_name} have drifted apart. "
            f"c/src/srmech_tool_schema.c is HAND-MAINTAINED and is NOT a "
            f"regen_all output — edit it by hand, in the same commit.\n"
            f"  in Python but not C: {only_py}\n"
            f"  in C but not Python: {only_c}\n"
            f"  present in both but VALUE differs: {differs}")


def test_the_lexicon_comparison_can_actually_fail() -> None:
    """⚠️ NON-VACUITY. A parser that returned ``{}`` would make the test above
    pass only if Python were empty too — but a parser that silently dropped ONE
    entry would pass nothing and fail loudly, so the real risk is the reverse:
    a regex that matches nothing at all in a renamed table. Prove the parser
    reads real content, and that an injected difference is detected.
    """
    from srmech.mcp._tools import _TYPE_LEXICON

    c = _c_table("MCP_TYPE_LEXICON")
    assert c.get("Mat") == "array" and c.get("int") == "integer", (
        "the C type lexicon does not carry its two most stable entries — the "
        "parser is reading the wrong thing.")
    # the rc362 additions, named so a later removal from EITHER side is loud
    assert c.get("Q") == "array"
    assert c.get("Sequence[int | Q | Qalg]") == "array"
    # an injected divergence must be detectable
    mutated = dict(c)
    mutated["Mat"] = "object"
    assert mutated != _TYPE_LEXICON, (
        "a deliberately corrupted C table still compares equal to Python — "
        "the comparison above cannot fail and proves nothing.")
