"""Tests for srmech.mcp — MCP server adapter (v0.5.0rc6).

Covers the JSON-RPC dispatch core (:class:`srmech.mcp.MCPServer`),
the ToolEntry -> MCP-def converter, the stdio transport (via
subprocess round-trip), the HTTP+SSE transport (via socket
round-trip), the ``srmech-mcp`` CLI entry, the ``--filter`` flag,
the ``--bus-endpoint`` proxy mode, and the MPR attestation
discipline carried on every tool-call response.
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import threading
import time
import urllib.request
from http.client import HTTPConnection
from typing import Any, Dict, Iterator, List, Tuple

import pytest

# Force bus tools to register so coverage matches the runtime baseline.
import srmech.bus  # noqa: F401 — import side-effect

import srmech
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

# rc430 (`#T1094`) — the (op, param)-keyed valid-argument provider. Lives in
# tools/ (not in the package) because test_selfhosting_import_ban holds a
# down-only CEIL on `json` imports under srmech/; same sys.path.insert(TOOLS)
# pattern as tests/test_worked_examples_execute_rc354.py.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import example_args as _ea  # noqa: E402
from srmech.mcp import (
    MCP_PROTOCOL_VERSION,
    MCPError,
    MCPServer,
    invoke_tool,
    serve_http_sse,
    tool_entries_to_mcp_defs,
)
from srmech.mcp._server import (
    JSONRPC_INVALID_PARAMS,
    JSONRPC_METHOD_NOT_FOUND,
    MCP_TOOL_ERROR,
    build_attestation,
)
from srmech.mcp._tools import (
    compile_filter,
    serialise_result,
    tool_entry_to_mcp_def,
)

# rc231 (#810) — make this tests/ directory importable when test_mcp is
# collected ALONE (`pytest tests/test_mcp.py`). ``tests/`` is a package
# (``__init__.py`` present), so pytest's prepend import-mode puts the package
# PARENT (``python/``) on sys.path, not ``tests/`` itself — a bare
# ``from conftest import ...`` then raises ``ModuleNotFoundError`` in isolation.
# In the full suite an earlier-collected sibling (test_immolation) happens to
# insert it first; standalone there is no such side-effect. Insert it here so
# the ``from conftest import return_type_agrees`` below resolves in BOTH modes
# (the same guard test_immolation.py already carries — the project's proven
# shared-helper path).
import os as _os
import sys as _sys
_TESTS_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _TESTS_DIR not in _sys.path:
    _sys.path.insert(0, _TESTS_DIR)


# ──────────────────────────────────────────────────────────────────────
# `#T1007` — the advertised-tool list, computed ONCE at COLLECTION time.
#
# The two exhaustive per-op smokes (this file's every-tool invocation smoke
# and test_immolation's return-type honesty gate) used to be a SINGLE function
# each, looping ``for entry in advertised: invoke_tool(...)`` over every
# ``mcp_callable`` ToolEntry. That is one atomic pytest node ~30 min long that
# ``--dist loadfile`` pins to ONE xdist worker and no runner-matrix can split —
# the single most expensive thing in the pure-Python CI cell. Parametrising
# over this list makes EACH advertised tool its own node (spread across workers
# under ``--dist load``), and a broken tool NAMES itself instead of hiding in an
# accumulated list.
#
# ``warmup_all()`` guarantees the registry is fully populated regardless of the
# order pytest happens to collect test modules in, so the parametrised node set
# equals the live ``describe()`` surface (and matches test_immolation, which
# imports this same list). It is idempotent (the whole suite calls it).
warmup_all()
_ADVERTISED = [e for e in get_tool_schema().tools if e.mcp_callable]

# rc414 (`#T1092`) — a FLOOR on the parametrisation size.
#
# ``_ADVERTISED`` drives the every-tool invocation smoke here and (imported)
# the return-type honesty sweep in test_immolation.py. It is a FILTER on
# ``mcp_callable``, so flipping an op to False silently removes it from both
# sweeps — and until rc414 nothing asserted the parametrised set had any
# particular size. Coverage could therefore drain away one flip at a time with
# every remaining test still green, which is the "a filter that hides ripple is
# the gate lying" shape.
#
# The floor is deliberately a floor and not an equality: ops are ADDED every
# rc, and an equality here would be one more count-pin to bump (there are 73
# of those already). It is set just under the live value so a mass exclusion
# trips it while ordinary growth does not.
assert len(_ADVERTISED) >= 550, (
    f"only {len(_ADVERTISED)} entries are mcp_callable — the every-tool "
    f"invocation smoke and test_immolation's return-type sweep are both "
    f"parametrised over this list, so a drop here silently shrinks TWO "
    f"coverage surfaces at once. If ops were legitimately excluded, lower "
    f"this floor deliberately and say why in the rc's CHANGELOG entry."
)


# ──────────────────────────────────────────────────────────────────────
# Tool conversion: every ToolEntry yields a valid MCP tool def
# ──────────────────────────────────────────────────────────────────────


def test_every_tool_entry_converts_to_valid_mcp_def() -> None:
    """Every registered ToolEntry must produce a well-formed MCP
    tool def (``name`` + ``description`` + ``inputSchema`` with
    object-type root)."""
    defs = list(tool_entries_to_mcp_defs())
    assert len(defs) > 50, (
        f"expected ~150 registered tools; got {len(defs)}"
    )
    seen_names = set()
    for d in defs:
        assert "name" in d and isinstance(d["name"], str) and d["name"]
        assert d["name"] not in seen_names, (
            f"duplicate MCP tool name {d['name']!r}"
        )
        seen_names.add(d["name"])
        assert "description" in d and isinstance(d["description"], str)
        assert "inputSchema" in d
        sch = d["inputSchema"]
        assert sch["type"] == "object"
        assert "properties" in sch and isinstance(sch["properties"], dict)
        assert "required" in sch and isinstance(sch["required"], list)


def test_tool_entry_to_mcp_def_known_shape() -> None:
    """A specific ToolEntry (``sha256_bytes``) renders the expected
    shape end-to-end."""
    entry = get_tool_schema().lookup("srmech.amsc.format.sha256_bytes")
    assert entry is not None
    d = tool_entry_to_mcp_def(entry)
    assert d["name"] == "srmech.amsc.format.sha256_bytes"
    assert "data" in d["inputSchema"]["properties"]
    assert "data" in d["inputSchema"]["required"]
    # Returned-type hint is in the description.
    assert "Returns: str" in d["description"]
    assert "category: format" in d["description"]


# ──────────────────────────────────────────────────────────────────────
# Property-key validity ratchet (v0.5.0rc10)
#
# BUG 1 (found by a LIVE Anthropic API test of the rc9 adapter, NOT by
# the mocks): ``srmech.math.hdc.polar_bundle`` / ``klein4_bundle`` were
# registered with the param name ``*vectors`` — the Python varargs sigil
# leaked into the ToolParameter NAME, so the MCP/Anthropic input_schema
# carried a property KEY ``*vectors``. Anthropic rejected the WHOLE
# catalog with ``400 — input_schema.properties: Property keys should
# match pattern '^[a-zA-Z0-9_.-]{1,64}$'``. The same converter feeds
# both adapters, so this single ratchet guards every tool on BOTH paths.
# ──────────────────────────────────────────────────────────────────────

#: The Anthropic / MCP property-key grammar (anchored).
_ANTHROPIC_PROPERTY_KEY_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")


def test_every_tool_property_key_matches_anthropic_grammar() -> None:
    """Every ``inputSchema.properties`` KEY of every registered tool
    must match Anthropic's ``^[a-zA-Z0-9_.-]{1,64}$`` grammar and
    contain no Python varargs/kwargs sigil (``*``).

    This is the ratchet that would have caught BUG 1 (the ``*vectors``
    leak). It runs through ``tool_entry_to_mcp_def`` — the converter
    BOTH the MCP server and the Anthropic SDK adapter use — so it
    locks down the property-key grammar for all ~155 tools on both
    transports at once.
    """
    schema = get_tool_schema()
    assert len(schema.tools) > 50, "tool registry unexpectedly small"
    offenders: List[Tuple[str, str]] = []
    for entry in schema.tools:
        mcp_def = tool_entry_to_mcp_def(entry)
        for key in mcp_def["inputSchema"]["properties"]:
            if "*" in key or not _ANTHROPIC_PROPERTY_KEY_RE.match(key):
                offenders.append((entry.name, key))
    assert not offenders, (
        "tool property keys violate Anthropic's "
        "'^[a-zA-Z0-9_.-]{1,64}$' grammar (a leaked Python varargs "
        f"sigil gets the whole catalog 400'd on the Anthropic path): "
        f"{offenders}"
    )


def test_required_keys_reference_real_properties() -> None:
    """Every name in ``inputSchema.required`` must be an actual key in
    ``inputSchema.properties`` — a sanity check that the defence-in-depth
    key sanitiser keeps ``required`` and ``properties`` in lockstep."""
    schema = get_tool_schema()
    for entry in schema.tools:
        mcp_def = tool_entry_to_mcp_def(entry)
        props = mcp_def["inputSchema"]["properties"]
        for req in mcp_def["inputSchema"]["required"]:
            assert req in props, (
                f"{entry.name}: required key {req!r} not in properties "
                f"{sorted(props)}"
            )


def test_filter_predicate_compiles_glob() -> None:
    """``compile_filter`` builds a callable that matches fnmatch
    patterns."""
    pred = compile_filter("srmech.cascade.*")
    assert pred is not None
    assert pred("srmech.cascade.chiral_flip")
    assert not pred("srmech.amsc.format.sha256_bytes")
    assert compile_filter(None) is None


def test_filter_reduces_exposed_tool_count() -> None:
    """``tool_entries_to_mcp_defs`` honours the filter predicate."""
    all_defs = list(tool_entries_to_mcp_defs())
    pred = compile_filter("srmech.cascade.*")
    cascade_defs = list(tool_entries_to_mcp_defs(name_filter=pred))
    assert 0 < len(cascade_defs) < len(all_defs)
    for d in cascade_defs:
        assert d["name"].startswith("srmech.cascade.")


# ──────────────────────────────────────────────────────────────────────
# Direct invocation
# ──────────────────────────────────────────────────────────────────────


def test_invoke_tool_chiral_flip_roundtrips() -> None:
    """A simple known tool round-trips through invoke_tool."""
    result = invoke_tool(
        "srmech.cascade.chiral_flip",
        {"seq": [1, 2, 3, 4]},
    )
    assert result == [4, 3, 2, 1]


def test_invoke_tool_sha256_bytes_with_base64_coercion() -> None:
    """bytes parameters arrive as base64 strings (MCP rides JSON, which
    has no bytes type; rc14 standardises bytes on base64 — binary-safe,
    unambiguous); ``invoke_tool`` decodes them back to raw bytes."""
    import base64

    # "abc" base64 -> "YWJj"
    result = invoke_tool(
        "srmech.amsc.format.sha256_bytes",
        {"data": base64.b64encode(b"abc").decode("ascii")},
    )
    assert isinstance(result, str)
    assert len(result) == 64
    # Compare against hashlib (route through sha256 of raw bytes —
    # the value the underlying callable computed).
    expected = hashlib.sha256(b"abc").hexdigest()
    assert result == expected


def test_invoke_tool_unknown_raises_mcp_tool_error() -> None:
    """Unknown tool name -> MCPToolError."""
    from srmech.mcp._tools import MCPToolError
    with pytest.raises(MCPToolError):
        invoke_tool("srmech.nope.does_not_exist", {})


# ──────────────────────────────────────────────────────────────────────
# Varargs dispatch (v0.5.0rc10)
#
# BUG 2 (found by the same LIVE Anthropic API test): ``invoke_tool``
# ended with ``fn(**coerced)`` — keyword-args only. For a variadic
# callable like ``hdc.polar_bundle(*vectors)``, ``fn(vectors=[...])``
# raises ``TypeError: got an unexpected keyword argument 'vectors'``.
# Both adapters route through ``invoke_tool``, so invoking either bundle
# tool was broken on BOTH paths. The fix detects a VAR_POSITIONAL slot
# via ``inspect.signature`` and unpacks the supplied list positionally.
#
# Vectors are built with the parity-test fixtures (``hdc.polar_random``
# / ``hdc.klein4_random``); each ndarray is ``tolist()``'d to emulate a
# JSON array (the wire form a real MCP / Anthropic client sends).
# ──────────────────────────────────────────────────────────────────────


def test_invoke_tool_polar_bundle_variadic_dispatches() -> None:
    """``hdc.polar_bundle`` (a ``*vectors`` variadic) invokes cleanly
    through ``invoke_tool`` — NOT a TypeError / MCPToolError.

    This is the test that would have caught BUG 2.
    """
    from srmech.math import hdc
    from srmech.mcp._tools import MCPToolError

    # JSON arrays decode to Python lists; emulate that wire form (numpy-free:
    # the seeded random ops + bundle are numpy-free; ``.tolist()`` flattens the
    # array('b') / HV carrier to the plain-list wire form).
    vectors = [hdc.polar_random(16, seed=11 + i).tolist() for i in range(3)]
    try:
        result = invoke_tool(
            "srmech.math.hdc.polar_bundle", {"vectors": vectors}
        )
    except (TypeError, MCPToolError) as exc:  # pragma: no cover
        pytest.fail(f"variadic dispatch broke: {type(exc).__name__}: {exc}")
    # A real bundled result: a length-16 polar vector over {-1, 0, +1}.
    res = list(result)
    assert len(res) == 16
    assert set(res) <= {-1, 0, 1}
    # Bit-exact against calling the reference directly with *args (plain lists).
    expected = list(hdc.polar_bundle(*[list(v) for v in vectors]))
    assert res == expected


def test_invoke_tool_klein4_bundle_variadic_dispatches() -> None:
    """``hdc.klein4_bundle`` (a ``*vectors`` variadic) invokes cleanly
    through ``invoke_tool``. Companion to the polar test for BUG 2."""
    from srmech.math import hdc
    from srmech.mcp._tools import MCPToolError

    # numpy-free wire form: seeded klein4 vectors, ``.tolist()``'d off the HV
    # carrier to plain lists (the JSON-array shape an MCP client sends).
    vectors = [hdc.klein4_expand(16, 11 + i).tolist() for i in range(3)]
    try:
        result = invoke_tool(
            "srmech.math.hdc.klein4_bundle", {"vectors": vectors}
        )
    except (TypeError, MCPToolError) as exc:  # pragma: no cover
        pytest.fail(f"variadic dispatch broke: {type(exc).__name__}: {exc}")
    res = list(result)
    assert len(res) == 16
    assert set(res) <= {0, 1, 2, 3}
    expected = list(hdc.klein4_bundle(*[list(v) for v in vectors]))
    assert res == expected


def test_invoke_tool_variadic_tolerates_legacy_sigil_key() -> None:
    """Belt-and-braces: a caller that still sends the historical
    sigil-prefixed key (``*vectors``) is tolerated (the dispatcher
    falls back to it), so no in-flight client breaks on the rename."""
    from srmech.math import hdc

    vectors = [hdc.polar_random(8, seed=7 + i).tolist() for i in range(3)]
    result = invoke_tool(
        "srmech.math.hdc.polar_bundle", {"*vectors": vectors}
    )
    res = list(result)
    assert len(res) == 8
    expected = list(hdc.polar_bundle(*[list(v) for v in vectors]))
    assert res == expected


# ──────────────────────────────────────────────────────────────────────
# Result serialisation
# ──────────────────────────────────────────────────────────────────────


def test_serialise_result_handles_bytes_tuples_paths() -> None:
    """JSON-text rendering of awkward Python objects (rc14: bytes ride as
    base64, tuples become lists)."""
    import base64

    out = serialise_result({"b": b"\x00\xff", "tup": (1, 2)})
    parsed = json.loads(out)
    assert parsed["b"] == base64.b64encode(b"\x00\xff").decode("ascii")
    assert parsed["tup"] == [1, 2]


def test_serialise_result_matrices_and_lists() -> None:
    """numpy-free (#564): ops return ``Mat`` / nested lists, not ndarrays.
    ``serialise_result`` renders a ``Mat`` via ``.tolist()`` and a nested
    list straight to JSON text — the wire form is identical to what the old
    ndarray ``tolist()`` fallback produced."""
    from srmech.math.mat import Mat

    # A Mat (numpy-free dense matrix) is .tolist()'d to nested JSON arrays.
    out = serialise_result(Mat.from_rows([[1.0, 2.0, 3.0]]))
    assert json.loads(out) == [[1.0, 2.0, 3.0]]

    # A plain nested list rides straight through.
    out2 = serialise_result([1.0, 2.0, 3.0])
    assert json.loads(out2) == [1.0, 2.0, 3.0]


# ──────────────────────────────────────────────────────────────────────
# MCPServer dispatch
# ──────────────────────────────────────────────────────────────────────


def test_initialize_handshake_returns_server_info() -> None:
    """``initialize`` returns serverInfo + capabilities + protocolVersion."""
    srv = MCPServer(name="test-srv")
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0.1"},
        },
    })
    assert resp is not None
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    result = resp["result"]
    assert result["serverInfo"]["name"] == "test-srv"
    assert result["serverInfo"]["version"] == srmech.__version__
    assert "tools" in result["capabilities"]
    assert result["protocolVersion"] == MCP_PROTOCOL_VERSION


def test_notifications_initialized_returns_none() -> None:
    """Notifications produce no response."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "method": "notifications/initialized",
    })
    assert resp is None


def test_tools_list_returns_all_tools() -> None:
    """tools/list returns the full registered tool surface."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 2, "method": "tools/list",
    })
    assert resp is not None
    tools = resp["result"]["tools"]
    assert len(tools) > 50
    names = {t["name"] for t in tools}
    assert "srmech.cascade.chiral_flip" in names


def test_tools_list_honours_filter() -> None:
    """tools/list honours the constructor's name_filter."""
    pred = compile_filter("srmech.cascade.*")
    srv = MCPServer(name_filter=pred)
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 1, "method": "tools/list",
    })
    assert resp is not None
    tools = resp["result"]["tools"]
    assert all(t["name"].startswith("srmech.cascade.") for t in tools)


def test_tools_call_invokes_tool_and_returns_attestation() -> None:
    """tools/call returns content + isError=false + MPR attestation."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {
            "name": "srmech.cascade.chiral_flip",
            "arguments": {"seq": [1, 2, 3]},
        },
    })
    assert resp is not None
    result = resp["result"]
    assert result["isError"] is False
    assert result["content"][0]["type"] == "text"
    assert json.loads(result["content"][0]["text"]) == [3, 2, 1]
    att = result["attestation"]
    assert att["mpr_version"] == "1.0"
    assert att["tool_name"] == "srmech.cascade.chiral_flip"
    assert att["parser_version"].startswith("srmech ")
    assert len(att["response_sha256"]) == 64


def test_tools_call_bad_name_returns_invalid_params() -> None:
    """tools/call without a name -> JSON-RPC invalid-params error."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"arguments": {}},
    })
    assert resp is not None
    assert "error" in resp
    assert resp["error"]["code"] == JSONRPC_INVALID_PARAMS


def test_tools_call_filtered_tool_returns_method_not_found() -> None:
    """A tool filtered out by --filter is not callable."""
    pred = compile_filter("srmech.amsc.format.*")  # cascade excluded
    srv = MCPServer(name_filter=pred)
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {
            "name": "srmech.cascade.chiral_flip",
            "arguments": {"seq": [1, 2, 3]},
        },
    })
    assert resp is not None
    assert "error" in resp
    assert resp["error"]["code"] == JSONRPC_METHOD_NOT_FOUND


def test_tools_call_unknown_tool_returns_is_error_response() -> None:
    """tools/call of an unregistered name returns isError=true (not
    a JSON-RPC error — per MCP spec, tool errors are success-shaped).
    """
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 6, "method": "tools/call",
        "params": {"name": "srmech.does_not_exist", "arguments": {}},
    })
    assert resp is not None
    assert "result" in resp
    assert resp["result"]["isError"] is True
    assert resp["result"]["content"][0]["type"] == "text"


def test_tools_call_runtime_exception_returns_is_error_response() -> None:
    """A tool that raises at runtime surfaces as isError=true (not a
    JSON-RPC error)."""
    srv = MCPServer()
    # Pass invalid args to a real tool to provoke a TypeError.
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {
            "name": "srmech.cascade.chiral_flip",
            "arguments": {"not_the_param_name": 123},
        },
    })
    assert resp is not None
    assert resp["result"]["isError"] is True


def test_unknown_method_returns_method_not_found() -> None:
    """An unknown method (non-notification) yields method-not-found."""
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "id": 8, "method": "wat"})
    assert resp is not None
    assert resp["error"]["code"] == JSONRPC_METHOD_NOT_FOUND


def test_unknown_notification_silently_ignored() -> None:
    """Unknown notification — silent per spec."""
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "method": "notifications/anything"})
    assert resp is None


def test_ping_method_returns_empty_result() -> None:
    """ping (utility method) returns empty result."""
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "id": 9, "method": "ping"})
    assert resp is not None
    assert resp["result"] == {}


def test_build_attestation_reproducible() -> None:
    """build_attestation populates the MPR-style fields with a
    SHA-256 over the canonical concatenation."""
    att = build_attestation(tool_name="foo", result_text="bar")
    assert att["mpr_version"] == "1.0"
    assert att["tool_name"] == "foo"
    assert len(att["response_sha256"]) == 64
    # Hash must change when content changes.
    att2 = build_attestation(tool_name="foo", result_text="other")
    assert att["response_sha256"] != att2["response_sha256"]


# ──────────────────────────────────────────────────────────────────────
# stdio transport: subprocess round-trip
# ──────────────────────────────────────────────────────────────────────


def _send_one_recv_one(
    p: "subprocess.Popen", msg: Dict[str, Any]
) -> Dict[str, Any]:
    """Send one JSON-RPC line and read one line of response."""
    line = json.dumps(msg) + "\n"
    assert p.stdin is not None
    assert p.stdout is not None
    p.stdin.write(line)
    p.stdin.flush()
    raw = p.stdout.readline()
    assert raw, f"subprocess closed stdout: stderr={p.stderr.read() if p.stderr else ''!r}"
    return json.loads(raw)


def test_stdio_subprocess_full_handshake() -> None:
    """End-to-end MCP handshake over stdio via subprocess."""
    p = subprocess.Popen(
        [sys.executable, "-m", "srmech.mcp._cli"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        # initialize
        init_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1"},
            },
        })
        assert init_resp["result"]["serverInfo"]["name"] == "srmech-mcp"

        # tools/list
        list_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 2, "method": "tools/list",
        })
        tools = list_resp["result"]["tools"]
        assert len(tools) > 50

        # tools/call (chiral_flip — a guaranteed-present tool)
        call_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {
                "name": "srmech.cascade.chiral_flip",
                "arguments": {"seq": [10, 20, 30]},
            },
        })
        assert call_resp["result"]["isError"] is False
        assert json.loads(
            call_resp["result"]["content"][0]["text"]
        ) == [30, 20, 10]
    finally:
        if p.stdin is not None:
            p.stdin.close()
        try:
            p.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            p.kill()


def test_stdio_subprocess_exits_cleanly_on_eof() -> None:
    """Closing stdin shuts the server down with exit code 0."""
    p = subprocess.Popen(
        [sys.executable, "-m", "srmech.mcp._cli"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert p.stdin is not None
    p.stdin.close()
    rc = p.wait(timeout=5.0)
    assert rc == 0


# ──────────────────────────────────────────────────────────────────────
# HTTP+SSE transport
# ──────────────────────────────────────────────────────────────────────


def _sse_initial_events(host: str, port: int) -> Iterator[Tuple[str, str]]:
    """Open ``GET /sse``, yield ``(event-name, data)`` tuples as
    they arrive. Generator stops when the connection is closed
    upstream."""
    conn = HTTPConnection(host, port, timeout=5.0)
    conn.request("GET", "/sse", headers={"Accept": "text/event-stream"})
    resp = conn.getresponse()
    assert resp.status == 200
    buf = b""
    while True:
        chunk = resp.read1(4096)
        if not chunk:
            return
        buf += chunk
        while b"\n\n" in buf:
            event_chunk, buf = buf.split(b"\n\n", 1)
            evt_name = ""
            data_parts: List[str] = []
            for line in event_chunk.decode("utf-8").splitlines():
                if line.startswith("event: "):
                    evt_name = line[len("event: "):].strip()
                elif line.startswith("data: "):
                    data_parts.append(line[len("data: "):])
            yield (evt_name, "\n".join(data_parts))


def test_http_sse_round_trip() -> None:
    """End-to-end MCP round-trip over the HTTP+SSE transport."""
    handle = serve_http_sse(name="test-sse", port=0, background=True)
    try:
        host, port = handle.address
        # Spawn the SSE reader on a background thread so we can POST
        # the initialize request concurrently.
        received: List[Tuple[str, str]] = []
        endpoint_holder: List[str] = []
        reader_started = threading.Event()
        done = threading.Event()

        def _reader() -> None:
            reader_started.set()
            for evt, data in _sse_initial_events(host, port):
                received.append((evt, data))
                if evt == "endpoint" and not endpoint_holder:
                    endpoint_holder.append(data)
                if evt == "message":
                    done.set()
                    return

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        # Wait for the endpoint event.
        for _ in range(100):
            if endpoint_holder:
                break
            time.sleep(0.05)
        assert endpoint_holder, "no endpoint event received"
        endpoint_url = endpoint_holder[0]
        # POST one initialize request to that endpoint.
        body = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "sse-test", "version": "0.1"},
            },
        }).encode("utf-8")
        conn = HTTPConnection(host, port, timeout=5.0)
        conn.request(
            "POST", endpoint_url, body=body,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        assert resp.status == 202
        resp.read()
        # The actual response rides over SSE.
        assert done.wait(timeout=5.0), "no message event from /sse"
        # Find the message event.
        message_evt = next(
            (data for evt, data in received if evt == "message"), None
        )
        assert message_evt is not None
        parsed = json.loads(message_evt)
        assert parsed["result"]["serverInfo"]["name"] == "test-sse"
    finally:
        handle.stop()


def test_http_sse_healthz() -> None:
    """``GET /healthz`` returns 200 + ``{"status":"ok"}``."""
    handle = serve_http_sse(port=0, background=True)
    try:
        host, port = handle.address
        with urllib.request.urlopen(
            f"http://{host}:{port}/healthz", timeout=5.0
        ) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert body == {"status": "ok"}
    finally:
        handle.stop()


def test_http_sse_unknown_path_404() -> None:
    """Unknown GET path -> 404."""
    handle = serve_http_sse(port=0, background=True)
    try:
        host, port = handle.address
        conn = HTTPConnection(host, port, timeout=5.0)
        conn.request("GET", "/no-such-path")
        resp = conn.getresponse()
        assert resp.status == 404
        resp.read()
    finally:
        handle.stop()


# ──────────────────────────────────────────────────────────────────────
# Bus-endpoint proxy mode
# ──────────────────────────────────────────────────────────────────────


def test_bus_endpoint_invoke_proxies_through_bus(tmp_path) -> None:
    """``--bus-endpoint NAME`` mode: tool calls flow through a real
    srmech.bus endpoint. We register a handler that pretends to
    execute the tool and verify the proxy round-trip."""
    from srmech.bus import serve as bus_serve
    from srmech.mcp._cli import make_bus_proxy_invoke

    endpoint_name = f"mcp-rc6-test-{int(time.time() * 1000) % 100000}"

    invocations: List[Dict[str, Any]] = []

    def handler(event: Dict[str, Any]) -> Dict[str, Any]:
        if event["type"] != "mcp.tools.call":
            return {"type": "ignored"}
        invocations.append(event["payload"])
        # The bus reflects the WHOLE handler dict back as payload
        # (per srmech.bus.serve contract). Returning result/error at
        # the top level puts them at reply["payload"]["result"] and
        # reply["payload"]["error"] — which is the shape the proxy
        # invoke callable reads.
        return {
            "type": "mcp.tools.call.reply",
            "result": ["pretend", "result"],
            "error": None,
        }

    with bus_serve(endpoint_name, handler=handler):
        proxy_invoke = make_bus_proxy_invoke(endpoint_name)
        # Build a server that uses the proxy.
        srv = MCPServer(invoke_override=proxy_invoke)
        resp = srv.handle({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {
                "name": "srmech.cascade.chiral_flip",
                "arguments": {"seq": [1, 2]},
            },
        })

    assert resp is not None
    assert resp["result"]["isError"] is False
    assert json.loads(
        resp["result"]["content"][0]["text"]
    ) == ["pretend", "result"]
    assert len(invocations) == 1
    assert invocations[0]["name"] == "srmech.cascade.chiral_flip"
    assert invocations[0]["arguments"] == {"seq": [1, 2]}


# ──────────────────────────────────────────────────────────────────────
# CLI surface
# ──────────────────────────────────────────────────────────────────────


def test_cli_help_exits_zero() -> None:
    """``srmech-mcp --help`` exits 0 with the expected usage line."""
    p = subprocess.run(
        [sys.executable, "-m", "srmech.mcp._cli", "--help"],
        capture_output=True, text=True,
    )
    assert p.returncode == 0
    assert "srmech-mcp" in p.stdout
    assert "--transport" in p.stdout
    assert "--bus-endpoint" in p.stdout
    assert "--filter" in p.stdout


def test_cli_version_exits_zero() -> None:
    """``srmech-mcp --version`` exits 0 with the current version."""
    p = subprocess.run(
        [sys.executable, "-m", "srmech.mcp._cli", "--version"],
        capture_output=True, text=True,
    )
    assert p.returncode == 0
    assert srmech.__version__ in p.stdout


def test_cli_filter_flag_subprocess() -> None:
    """``srmech-mcp --filter`` only exposes matching tools end-to-end."""
    p = subprocess.Popen(
        [sys.executable, "-m", "srmech.mcp._cli",
         "--filter", "srmech.cascade.*"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        # initialize then tools/list
        _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {}, "clientInfo": {"name": "t", "version": "0"},
            },
        })
        list_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 2, "method": "tools/list",
        })
        tools = list_resp["result"]["tools"]
        assert all(t["name"].startswith("srmech.cascade.") for t in tools)
    finally:
        if p.stdin is not None:
            p.stdin.close()
        try:
            p.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            p.kill()


# ──────────────────────────────────────────────────────────────────────
# MCP tool-schema discoverability (v0.5.0rc9)
#
# Regression tests for the discoverability gap caught 2026-05-28: the
# MCP wrapper at ``srmech.mcp._tools`` only imported
# ``srmech.introspect.tool_schema`` and never triggered the side-effect
# imports of ``srmech.bus._tool_schema`` (which registers the bus
# tools) — so the bus discovery + decode surfaces and the introspect
# read surfaces were silently missing from the LLM-facing catalog.
#
# The fix: side-effect imports at the top of ``srmech.mcp._tools``
# plus two new ``register_tool`` calls in each of
# ``srmech.introspect.tool_schema._register_introspect_tools`` and
# ``srmech.bus._tool_schema._register_bus_tools``.
#
# These five tests lock the fix in — they all assert via
# ``srmech.mcp._tools`` import (the path Claude Code / MCP clients
# take), which is THE entry point the bug lived behind. The
# ``import srmech.bus`` line at the top of this file (added in rc6)
# does NOT cover the regression because the bug was the absence of
# that side-effect import in the MCP layer itself.
# ──────────────────────────────────────────────────────────────────────


def _names_after_mcp_import() -> set:
    """Return the set of tool names visible after importing the MCP
    tool wrapper (the path an MCP / Claude Code consumer takes).
    """
    # The import below is the SUT — importing ``srmech.mcp._tools``
    # must transitively trigger every side-effect registration that
    # the MCP-facing catalog depends on. Using ``noqa: F401`` so the
    # import isn't optimised away by a linter; same pattern as the
    # production code.
    from srmech.mcp import _tools  # noqa: F401 — side effect under test
    from srmech.introspect.tool_schema import get_tool_schema
    schema = get_tool_schema()
    return {e.name for e in schema.tools}


def test_introspect_list_in_tool_schema_via_mcp_import() -> None:
    """``srmech.introspect.list`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix: the read-side
    ``list`` surface complements ``srmech.introspect.publish`` and
    must be visible to MCP / Claude Code consumers.
    """
    names = _names_after_mcp_import()
    assert "srmech.introspect.list" in names, (
        "srmech.introspect.list missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — read-side introspect surface)"
    )


def test_introspect_by_pid_in_tool_schema_via_mcp_import() -> None:
    """``srmech.introspect.by_pid`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix.
    """
    names = _names_after_mcp_import()
    assert "srmech.introspect.by_pid" in names, (
        "srmech.introspect.by_pid missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — PID-lookup introspect surface)"
    )


def test_bus_decode_splice_in_tool_schema_via_mcp_import() -> None:
    """``srmech.bus.decode_splice`` is registered after MCP wrapper import.

    THIS IS THE PRIMARY REGRESSION TEST for the side-effect-import bug:
    ``srmech.bus.decode_splice`` HAS been registered in
    ``srmech.bus._tool_schema`` since v0.5.0rc7, but the MCP wrapper
    at ``srmech.mcp._tools`` never imported ``srmech.bus``, so the
    registration never fired and the tool was invisible to MCP /
    Claude Code consumers. The fix is the ``from .. import bus``
    side-effect import at the top of ``srmech.mcp._tools``; this
    test guards against it being removed.
    """
    names = _names_after_mcp_import()
    assert "srmech.bus.decode_splice" in names, (
        "srmech.bus.decode_splice missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — side-effect import of "
        "srmech.bus removed?)"
    )


def test_bus_list_endpoints_in_tool_schema_via_mcp_import() -> None:
    """``srmech.bus.list_endpoints`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix: bus endpoint
    enumeration surface must be visible to MCP / Claude Code
    consumers (paired with ``srmech.bus.by_name``).
    """
    names = _names_after_mcp_import()
    assert "srmech.bus.list_endpoints" in names, (
        "srmech.bus.list_endpoints missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — bus discovery enumerator)"
    )


def test_bus_by_name_in_tool_schema_via_mcp_import() -> None:
    """``srmech.bus.by_name`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix.
    """
    names = _names_after_mcp_import()
    assert "srmech.bus.by_name" in names, (
        "srmech.bus.by_name missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — bus by-name lookup)"
    )


def test_mcp_import_chain_does_not_loop() -> None:
    """``srmech.mcp._tools`` import must not trigger a circular
    import via ``srmech.bus`` -> ``srmech.introspect.tool_schema`` ->
    ``srmech.bus`` (the cycle the fix was careful to avoid)."""
    # If a cycle existed, this import would raise ImportError or
    # AttributeError on first import in a fresh interpreter. The
    # test suite as a whole exercises a non-fresh interpreter, so
    # this test is mostly a documentation guard — the assertion is
    # that the side-effect imports complete cleanly and the expected
    # tools are present.
    from srmech.mcp import _tools  # noqa: F401
    from srmech.introspect.tool_schema import get_tool_schema
    schema = get_tool_schema()
    # The full v0.5.0rc9 discoverability set is present in one shot.
    required = {
        "srmech.introspect.publish",
        "srmech.introspect.list",
        "srmech.introspect.by_pid",
        "srmech.bus.decode_splice",
        "srmech.bus.list_endpoints",
        "srmech.bus.by_name",
    }
    names = {e.name for e in schema.tools}
    missing = required - names
    assert not missing, (
        f"v0.5.0rc9 discoverability set incomplete after MCP "
        f"import; missing {sorted(missing)}"
    )


# ──────────────────────────────────────────────────────────────────────
# Self-recognition root (v0.5.0rc11)
#
# ``warmup_all()`` is THE single registration entry-point — it imports
# every submodule that registers ToolEntries so the registry is fully
# populated no matter how srmech was entered, permanently closing the
# orphan-registration bug class (the rc9 bus miss). ``describe()`` is
# the self-recognition ROOT: the package's at-a-glance map of its own
# shape, also registered as a tool so MCP / Anthropic consumers can ask
# "what is srmech / what can it do?".
# ──────────────────────────────────────────────────────────────────────


def test_warmup_all_populates_registry() -> None:
    """``warmup_all()`` imports every registration-bearing submodule so
    bus + introspect tools are present in the tool schema regardless of
    entry-path. Closes the orphan-registration bug class (rc9 bus miss).
    """
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()  # idempotent
    names = {e.name for e in get_tool_schema().tools}
    # bus tools (the rc9 orphan) + introspect tools must all be present.
    required = {
        "srmech.bus.decode_splice",
        "srmech.bus.list_endpoints",
        "srmech.bus.by_name",
        "srmech.introspect.publish",
        "srmech.introspect.list",
        "srmech.introspect.by_pid",
        "srmech.introspect.describe",
    }
    missing = required - names
    assert not missing, (
        f"warmup_all() left the registry incomplete; missing "
        f"{sorted(missing)}"
    )


def test_describe_shape() -> None:
    """``srmech.introspect.describe()`` returns the self-shape dict with
    all expected keys; the counts are internally consistent and agree
    with the live tool schema."""
    from srmech.introspect.tool_schema import get_tool_schema
    from srmech.introspect import describe

    d = describe()
    # Top-level keys (rc15 adds the handle_pending name list; v0.7.5rc41 adds
    # the user-declared "classes" surface — #962 Part 2; rc298 adds "carriers",
    # the operand nouns to tools' verbs — `#936`; rc300 adds "c_claims", which
    # answers what "native" cannot — whether the loaded library actually holds
    # the C symbols our c_dispatched ops claim to route to — `#938`; rc347 adds
    # "lanes", the OP-side complement of "carriers": what each op READS —
    # `#T985`; rc420 adds "cascade_catalog", the [cascade] descriptor state —
    # ADR-0012 clause C6 closed under local task `#T1114`; rc430 adds "frames",
    # the FRAME axis — whether the frame an op reduces in is an INPUT
    # ("parametric") or welded into the op ("fixed") — local task `#T1127`).
    #
    # This set is pinned EXHAUSTIVELY in THREE files, and all three must move
    # together: here, tests/test_describe_registry_pointer_rc407.py and
    # tests/test_domain_classes_rc298.py. rc430 shipped a green local ripple
    # sweep with all three red, because the ripple manifest named only the
    # first — see tests/test_describe_key_set_pins_rc430.py, which now derives
    # the pin sites instead of trusting a hand-maintained list.
    assert set(d.keys()) == {
        "srmech_version",
        "tool_schema_version",
        "native",
        "tools",
        "handle_pending",
        "categories",
        "classes",
        "cascade_catalog",
        "carriers",
        "limits",
        "c_claims",
        "lanes",
        "frames",
    }
    # Version agrees with the package attribute (no hardcoded literal).
    assert d["srmech_version"] == srmech.__version__
    assert isinstance(d["tool_schema_version"], str) and d["tool_schema_version"]

    # native block shape.
    native = d["native"]
    assert set(native.keys()) == {
        "has_native",
        "abi_version",
        "native_version",
    }
    assert isinstance(native["has_native"], bool)

    # tools.total agrees with the live schema length.
    schema = get_tool_schema()
    assert d["tools"]["total"] == len(schema.tools)

    # by_category sums to total.
    by_category = d["tools"]["by_category"]
    assert isinstance(by_category, dict)
    assert sum(by_category.values()) == d["tools"]["total"]

    # rc15 — the MCP-callability split is internally consistent.
    assert d["tools"]["mcp_callable"] + d["tools"]["handle_pending"] == \
        d["tools"]["total"]
    assert d["tools"]["mcp_callable"] == \
        sum(1 for e in schema.tools if e.mcp_callable)
    # The top-level handle_pending list agrees with the count and the
    # live schema's mcp_callable=False entries, and is sorted.
    hp = d["handle_pending"]
    assert hp == sorted(hp)
    assert len(hp) == d["tools"]["handle_pending"]
    assert set(hp) == {e.name for e in schema.tools if not e.mcp_callable}

    # categories are sorted + non-empty + match the by_category keys.
    cats = d["categories"]
    assert cats, "describe() returned no categories"
    assert cats == sorted(cats), "categories must be sorted"
    assert set(cats) == set(by_category.keys())


def test_describe_registered_as_tool() -> None:
    """``srmech.introspect.describe`` appears in the catalog after warmup
    (so MCP / Anthropic consumers can call the self-recognition root),
    with no parameters (keeps the property-key ratchet trivially happy).
    """
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    entry = get_tool_schema().lookup("srmech.introspect.describe")
    assert entry is not None, (
        "srmech.introspect.describe not registered as a ToolEntry"
    )
    assert entry.owner == "srmech"
    assert entry.category == "introspect"
    # No params — the self-recognition root takes no arguments.
    assert entry.parameters == ()
    # And it converts to a clean MCP def (guards both adapters).
    mcp_def = tool_entry_to_mcp_def(entry)
    assert mcp_def["inputSchema"]["properties"] == {}
    assert mcp_def["inputSchema"]["required"] == []


# ──────────────────────────────────────────────────────────────────────
# DSL surface (v0.5.0rc12)
#
# The rc8 cascade DSL is exposed declaratively as two ToolEntries so an
# LLM composes + runs a cascade in one call. These two tests keep the
# dsl entries in the MCP-import discoverability manifest (the path a
# Claude Code / MCP client takes); full DSL-tool coverage lives in
# test_dsl_tools.py.
# ──────────────────────────────────────────────────────────────────────


def test_dsl_tools_in_tool_schema_via_mcp_import() -> None:
    """``srmech.dsl.run_toml_chain`` + ``srmech.dsl.list_catalog_ops``
    are registered after the MCP wrapper import (the path an MCP /
    Claude Code consumer takes) — the rc12 DSL surface voxel."""
    names = _names_after_mcp_import()
    for tool_name in (
        "srmech.dsl.run_toml_chain",
        "srmech.dsl.list_catalog_ops",
    ):
        assert tool_name in names, (
            f"{tool_name} missing from tool_schema after MCP import "
            f"(v0.5.0rc12 DSL surface voxel)"
        )


def test_dsl_run_toml_chain_one_shot_via_mcp_invoke() -> None:
    """``srmech.dsl.run_toml_chain`` is one-shot callable through the
    MCP ``invoke_tool`` path with a real TOML spec — composes + runs a
    cascade in a single call (rc12)."""
    spec = (
        "[chain]\n"
        'name = "rc12-mcp"\n'
        "\n"
        "[[stage]]\n"
        'op = "chiral_flip"\n'
    )
    result = invoke_tool(
        "srmech.dsl.run_toml_chain",
        {"spec": spec, "input_value": [10, 20, 30]},
    )
    assert result == [30, 20, 10]


# ──────────────────────────────────────────────────────────────────────
# MCP surface-correctness (v0.5.0rc13)
#
# Two real bugs surfaced by upstream MCP usage, plus the would-have-caught
# -it ratchet. Both bugs affect BOTH the MCP path and the Anthropic adapter
# (shared ``srmech.mcp._tools.invoke_tool``).
#
# BUG A — the Klein-4 / polar mints were seedable only via ``rng:
# numpy.random.Generator``, which cannot cross JSON-RPC nor be expressed in
# an Anthropic tool schema — so MCP / Anthropic callers could not get a
# DETERMINISTIC vector (breaking srmech's bit-exact / attestation
# discipline). Fix: an integer ``seed`` param; the ToolEntry advertises
# ``seed`` and DROPS the un-serialisable Generator.
#
# rc290 POSTSCRIPT (§102 / F1259): the rc13 fix put ``seed=`` on an op named
# ``klein4_random``, which delivered the capability and created a second
# defect — a call site could no longer be READ to find out whether it asked
# for a random value or a derived one. The deterministic regime is now
# ``klein4_expand``; ``klein4_random`` is STOCHASTIC-only and refuses a
# seed. These tests target the op that now carries each regime.
#
# BUG B — ``srmech.introspect.naming.lookup``'s ToolEntry declared a param
# (``entries``) the shipped ``lookup(key, pairs)`` does not accept, so the
# tool was uncallable (``TypeError: unexpected keyword argument 'entries'``).
# Fix: align the SCHEMA to the shipped signature (``pairs``).
# ──────────────────────────────────────────────────────────────────────


def test_klein4_expand_seed_reproducible() -> None:
    """``hdc.klein4_expand(8, 42)`` is DETERMINISTIC — twice directly, and
    twice through ``invoke_tool`` (the MCP / Anthropic shared path) — so a
    JSON-RPC / Anthropic caller can reproduce a Klein-4 vector (bit-exact /
    attestation discipline). This is the BUG A acceptance test.

    rc290: the CAPABILITY is unchanged, the OP SERVING IT is renamed. BUG A
    was 'MCP callers cannot get a deterministic vector'; the rc13 fix added
    ``seed=`` to ``klein4_random``, which fixed the capability and created
    F1259's defect — an op named 'random' that was not. The deterministic
    regime is now ``klein4_expand`` and the wire path targets it."""
    from srmech.math import hdc

    # Direct: identical vectors for the same seed (numpy-free — compare the
    # plain-list contents of the HV carrier).
    a = list(hdc.klein4_expand(8, 42))
    b = list(hdc.klein4_expand(8, 42))
    assert a == b
    assert set(a) <= {0, 1, 2, 3}

    # Through invoke_tool twice (the wire path): also identical.
    r1 = list(invoke_tool("srmech.math.hdc.klein4_expand", {"D": 8, "seed": 42}))
    r2 = list(invoke_tool("srmech.math.hdc.klein4_expand", {"D": 8, "seed": 42}))
    assert r1 == r2
    # And invoke_tool agrees bit-exactly with the direct seeded call.
    assert r1 == a

    # A different seed gives a different vector (the seed is load-bearing).
    c = list(hdc.klein4_expand(8, 43))
    assert a != c


def test_polar_random_seed_reproducible() -> None:
    """Companion to klein4: ``hdc.polar_random(seed=...)`` is deterministic
    directly and through ``invoke_tool`` (the second ``*_random`` op fixed
    for BUG A)."""
    from srmech.math import hdc

    a = list(hdc.polar_random(8, seed=7))
    b = list(hdc.polar_random(8, seed=7))
    assert a == b
    assert set(a) <= {-1, 0, 1}

    r1 = list(invoke_tool("srmech.math.hdc.polar_random", {"D": 8, "seed": 7}))
    r2 = list(invoke_tool("srmech.math.hdc.polar_random", {"D": 8, "seed": 7}))
    assert r1 == r2
    assert r1 == a


def test_random_ops_rng_takes_precedence_over_seed() -> None:
    """When BOTH ``rng`` and ``seed`` are given, the explicit ``rng`` wins
    (documented precedence), and the legacy ``rng=`` path stays back-compat
    for in-process Python callers.

    rc125 (#564): the hdc random ops are numpy-FREE — the ``rng=`` path now
    accepts a stdlib ``random.Random`` (a numpy ``Generator`` is still honoured
    via duck-typing), and the polar op returns an ``array('b')`` (was an int8
    ndarray). This test is itself numpy-free (a cluster-module test, per
    `[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`)."""
    import random

    from srmech.math import hdc

    # rng= path still works (back-compat) — stdlib Random.
    p = hdc.polar_random(8, rng=random.Random(0))
    assert p.typecode == "b" and len(p) == 8

    # polar_random keeps the documented rng-wins-over-seed precedence.
    rng_out = hdc.polar_random(8, rng=random.Random(999), seed=1)
    seed_out = hdc.polar_random(8, seed=1)
    assert list(rng_out) != list(seed_out)

    # rc292: the klein4 half of this test is gone with the op. `polar_random`
    # keeps `rng=` because its `seed=`/`rng=` precedence is DOCUMENTED and its
    # deterministic path is the C-dispatched one; klein4_random had neither —
    # it advertised NON-REPRODUCIBILITY while every real caller passed a
    # seeded generator. See test_klein4_regime_split_rc290.
    assert not hasattr(hdc, "klein4_random")


def test_random_ops_schema_drops_unserialisable_rng() -> None:
    """The DETERMINISTIC mint ToolEntries advertise the JSON-friendly ``seed``,
    and no client can ever be told to send an un-serialisable ``rng`` Generator
    (generator STATE has no JSON form).

    rc290: ``klein4_random`` left this set — it is the STOCHASTIC regime and
    has no ``seed`` to advertise. ``klein4_expand`` took its place.

    rc408 (`#T1078`) — HOW that is enforced changed. This test used to assert
    ``rng`` appeared in NO entry's ``parameters``. ``klein4_expand(D, seed)``
    has no ``rng`` at all, so for it the assertion is unchanged; but
    ``polar_random(D, rng=None, seed=None)`` DOES accept one, and omitting it
    from the contract hid a real capability from every in-process Python caller
    while the wire was already safe by other means. The honest split: the
    parameter is DECLARED, never REQUIRED, and publishes JSON-schema ``"null"``
    — so a schema-obedient client's only legal value is ``null``, which coerces
    to "absent" and runs the op on the ``seed`` path exactly as before. The wire
    limitation is a fact about the TYPE, not a licence to hide the PARAMETER.
    """
    from srmech.mcp._tools import _json_schema_type_for

    schema = get_tool_schema()
    for name in ("srmech.math.hdc.klein4_expand",
                 "srmech.math.hdc.polar_random"):
        entry = schema.lookup(name)
        assert entry is not None, f"{name} not registered"
        by_name = {p.name: p for p in entry.parameters}
        assert "seed" in by_name, f"{name} must advertise `seed`"
        rng = by_name.get("rng")
        if rng is None:
            continue                       # klein4_expand has no rng to declare
        assert not rng.required, f"{name}: `rng` must never be required"
        assert _json_schema_type_for(rng.type) == "null", (
            f"{name} must not advertise a fillable `rng` Generator; its "
            f"declared type {rng.type!r} publishes "
            f"{_json_schema_type_for(rng.type)!r}, want 'null'"
        )


def test_klein4_random_is_not_registered_rc292() -> None:
    """rc292 / F1259 — the STOCHASTIC regime is off the tool surface entirely.

    rc290 tried to make the op safe by starving its schema down to ``D``
    alone: no ``seed`` (which would restore the conflation) and no ``rng``
    (un-serialisable over JSON-RPC). That worked for MCP callers and did
    nothing for Python ones, who kept passing seeded generators through the
    ``rng=`` parameter the schema was hiding. Hiding a parameter from one
    projection is not removing a defect — it is removing the evidence.
    """
    assert get_tool_schema().lookup("srmech.math.hdc.klein4_random") is None


def test_klein4_regime_ops_are_registered_and_invokable() -> None:
    """rc290 — every regime op, the (1,3,7,3) frame and ONE-A14 are
    registered and callable over the MCP / Anthropic wire path."""
    schema = get_tool_schema()
    for name in ("srmech.math.hdc.klein4_expand",
                 "srmech.math.hdc.klein4_address",
                 "srmech.math.hdc.klein4_role",
                 "srmech.math.hdc.klein4_sector_frame",
                 "srmech.math.hdc.klein4_from_one"):
        assert schema.lookup(name) is not None, f"{name} not registered"

    # ADDRESSED: same content -> same vector over the wire; different content
    # -> a different vector. `content` is a `bytes` param, so it rides the
    # documented base64 wire form.
    cat = base64.b64encode(b"cat").decode("ascii")
    dog = base64.b64encode(b"dog").decode("ascii")
    a = list(invoke_tool("srmech.math.hdc.klein4_address",
                         {"D": 16, "content": cat}))
    b = list(invoke_tool("srmech.math.hdc.klein4_address",
                         {"D": 16, "content": cat}))
    assert a == b and set(a) <= {0, 1, 2, 3}
    assert a != list(invoke_tool("srmech.math.hdc.klein4_address",
                                 {"D": 16, "content": dog}))

    # ROLE: distinct role names give distinct keys; `base` re-namespaces.
    r1 = list(invoke_tool("srmech.math.hdc.klein4_role",
                          {"D": 32, "role": "subject"}))
    r2 = list(invoke_tool("srmech.math.hdc.klein4_role",
                          {"D": 32, "role": "object"}))
    r3 = list(invoke_tool("srmech.math.hdc.klein4_role",
                          {"D": 32, "role": "subject", "base": 7}))
    assert r1 != r2 and r1 != r3

    # The (1,3,7,3) frame is period-14 at ANY D (no 14-divisibility needed).
    f = list(invoke_tool("srmech.math.hdc.klein4_sector_frame", {"D": 30}))
    assert f[:14] == f[14:28]
    assert f[:14] == [1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3]


def test_naming_lookup_callable_via_invoke_tool() -> None:
    """``srmech.introspect.naming.lookup`` is callable through ``invoke_tool``
    and returns a real result — NOT a ``TypeError`` from a phantom param
    name. This is the BUG B acceptance test (the schema declared a param
    the shipped ``lookup(key, pairs)`` does not accept)."""
    pairs = [(b"a", b"x"), (b"b", b"y"), (b"c", b"z")]  # pre-sorted
    result = invoke_tool(
        "srmech.introspect.naming.lookup", {"key": b"b", "pairs": pairs}
    )
    assert result == b"y"
    # A miss returns None (still a real result, no TypeError).
    miss = invoke_tool(
        "srmech.introspect.naming.lookup", {"key": b"zzz", "pairs": pairs}
    )
    assert miss is None


def test_template_render_callable_via_invoke_tool() -> None:
    """``srmech.math.template.render`` is callable through ``invoke_tool``
    with the real ``mapping`` param — the second schema/signature drift the
    rc13 ratchet surfaced (the schema declared ``substitutions``)."""
    result = invoke_tool(
        "srmech.math.template.render",
        {"template_bytes": b"hi {n}", "mapping": {b"n": b"there"}},
    )
    assert result == b"hi there"


def test_schema_signature_alignment_no_drift() -> None:
    """THE RATCHET (v0.5.0rc13): for EVERY ToolEntry, the declared
    parameters must be BINDABLE to the resolved callable's signature —
    i.e. no schema/signature drift. A drift means the tool is uncallable
    via MCP / Anthropic (both route through ``invoke_tool``), exactly the
    BUG B failure mode.

    Tolerances:
      * a callable with ``**kwargs`` (VAR_KEYWORD) accepts any name;
      * the rc10 varargs convention exposes a ``*args`` slot under a clean
        name (e.g. ``vectors``), so a leading ``*`` on a declared param
        name is stripped before the membership check.

    This test would have caught both naming.lookup (``entries``) and
    template.render (``substitutions``). It guards all ~158 tools at once.
    """
    from srmech._resolve import resolve_dotted_callable

    schema = get_tool_schema()
    assert len(schema.tools) > 50, "tool registry unexpectedly small"

    drift: List[Tuple[str, str, List[str]]] = []
    for entry in schema.tools:
        fn = resolve_dotted_callable(entry.name)
        sig = __import__("inspect").signature(fn)
        params = sig.parameters.values()
        Parameter = __import__("inspect").Parameter
        has_var_kw = any(
            p.kind is Parameter.VAR_KEYWORD for p in params
        )
        accepted = {
            p.name
            for p in params
            if p.kind
            in (
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.KEYWORD_ONLY,
                Parameter.VAR_POSITIONAL,
            )
        }
        for p in entry.parameters:
            nm = p.name.lstrip("*")  # tolerate the rc10 varargs convention
            if not has_var_kw and nm not in accepted:
                drift.append((entry.name, p.name, sorted(accepted)))

    assert not drift, (
        "schema/signature drift — these declared ToolEntry params are not "
        "bindable to the resolved callable (the tool is uncallable via MCP "
        f"/ Anthropic): {drift}"
    )


# ──────────────────────────────────────────────────────────────────────
# Full JSON<->native coercion (v0.5.0rc14)
#
# A live probe of the rc13 catalog proved 65/158 tools were advertised to
# MCP / Anthropic but UNCALLABLE because their params are bytes /
# np.ndarray / complex — types JSON-RPC cannot express. rc14 adds full
# BIDIRECTIONAL coercion (params in + results out) so every tool is
# MCP-callable. The type-coercibility ratchet below complements the rc13
# name-drift ratchet: rc13 guarantees a param NAME binds; rc14 guarantees
# a param TYPE is JSON-coercible.
# ──────────────────────────────────────────────────────────────────────


def test_all_param_types_json_coercible() -> None:
    """THE TYPE-COERCIBILITY RATCHET (v0.5.0rc14): every ToolEntry param's
    declared type MUST have an explicit handler in the coercion dispatch
    (``srmech.mcp._coercion``). This is the would-have-caught-it ratchet
    for the 65/158 uncallable-tool finding: no future tool can advertise a
    non-JSON-coercible param type unnoticed — a missing handler fails here.

    JSON-native and opaque-handle types are listed as explicit
    pass-throughs in the dispatch (not defaulted), so this ratchet proves
    the dispatch is EXHAUSTIVE over the advertised surface, not merely
    that the awkward types are covered.
    """
    from srmech.mcp._coercion import has_coercer

    schema = get_tool_schema()
    assert len(schema.tools) > 50, "tool registry unexpectedly small"
    unhandled: List[Tuple[str, str, str]] = []
    for entry in schema.tools:
        for p in entry.parameters:
            if not has_coercer(p.type):
                unhandled.append((entry.name, p.name, p.type))
    assert not unhandled, (
        "these declared ToolEntry param types have NO coercion handler "
        "(the tool may be uncallable via MCP / Anthropic — add a handler "
        f"in srmech.mcp._coercion._PARAM_COERCERS): {unhandled}"
    )


def test_rc452_registrations_are_actually_invocable_over_json() -> None:
    """rc452 (`#T1166`): the two rc452 ToolEntries EXECUTE over a JSON-only
    payload — ``has_coercer() is True`` is NOT the property that matters.

    WHY THIS IS NOT test_all_param_types_json_coercible. That gate is a
    static membership check, and ``tool_schema.py:356`` already records
    that the static ratchet "could not tell a pass-through from a
    handler". A type mapped to ``_identity`` satisfies it while the op
    stays broken. So this gate INVOKES both ops through the live
    ``invoke_tool`` coercion path with arguments that have provably
    survived ``json.dumps``/``json.loads``, and compares against a direct
    in-process call.

    THE DEFECT IT PINS, stated so a future reader can falsify it.
    ``render_template`` resolves a placeholder via ``cursor.get(part, "")``
    while ``cursor`` is a ``Mapping`` and ``getattr(cursor, part, "")``
    otherwise (``srmech/amsc/descriptor.py:334``). Give it a NON-mapping
    and every ``{key}`` renders as the empty string — no exception, no
    missing-key signal, just a plausible fully-formed string with every
    substitution dropped. That is a silent wrong answer, so the coercer's
    entire content is the refusal, and the refusal is asserted here.

    The ``bytes`` wire encoding is BASE64 and has been since rc14
    (``_b64_to_bytes``); ``sha256_raw`` inherits it rather than minting a
    second spelling. A hex payload is REJECTED by that same contract, and
    that rejection is asserted too — pinning hex for one op would have
    split one declared type across two encodings.
    """
    import base64
    import json

    from srmech.amsc.descriptor import render_template
    from srmech.amsc.format import sha256_raw
    from srmech.mcp._tools import invoke_tool

    # ── sha256_raw: JSON base64 in, the identical 32 digest bytes out ──
    raw = b"hello"
    args = json.loads(json.dumps({"data": base64.b64encode(raw).decode()}))
    via_mcp = invoke_tool("srmech.amsc.format.sha256_raw", args)
    assert isinstance(via_mcp, (bytes, bytearray))
    assert len(via_mcp) == 32, f"expected a 32-byte digest, got {len(via_mcp)}"
    assert bytes(via_mcp) == sha256_raw(raw), (
        "MCP-coerced sha256_raw disagrees with the direct call")

    # the encoding is base64, NOT hex — one declared type, one spelling.
    with pytest.raises(ValueError):
        invoke_tool("srmech.amsc.format.sha256_raw", {"data": raw.hex()})

    # ── render_template: a JSON object context renders identically ──
    tmpl = "cite {src.name} v{ver} ({n} rows)"
    ctx = {"src": {"name": "AMSC"}, "ver": "1.0", "n": 42}
    args2 = json.loads(json.dumps({"template": tmpl, "context": ctx}))
    via_mcp2 = invoke_tool("srmech.amsc.descriptor.render_template", args2)
    assert via_mcp2 == render_template(tmpl, ctx)
    # the dotted key really resolved — not the all-empty degenerate render
    assert "AMSC" in via_mcp2 and "42" in via_mcp2, via_mcp2

    # ── the silent-wrong-answer this handler exists to refuse ──
    # First MEASURE the raw op's behaviour, so the guard is not asserted
    # against a danger that does not exist (if this ever starts raising on
    # its own, the coercer's justification changes and this gate says so).
    degenerate = render_template(tmpl, ["src", "ver"])
    assert "AMSC" not in degenerate and "42" not in degenerate, (
        "render_template now REJECTS a non-mapping context on its own; the "
        "_to_mapping coercer's stated rationale is stale — re-adjudicate it")
    # ...and the coerced path refuses it instead of returning that string.
    with pytest.raises(ValueError):
        invoke_tool("srmech.amsc.descriptor.render_template",
                    {"template": tmpl, "context": ["src", "ver"]})


def test_coercion_roundtrips_scalar_leaf_types() -> None:
    """``coerce_param(serialise_native(x)) == x`` for representative
    bytes / complex / array-shaped values (the documented round-trip
    guarantee).

    numpy-free (#564): the ``"np.ndarray"`` wire-form NAME survives (it is
    the JSON-RPC type-string key), but there are no ndarrays. The matrix
    wire form is a nested list of plain floats; ``coerce_param(.., "np.ndarray")``
    returns that nested list UNCHANGED. Complex matrices serialise as
    ``[re, im]`` leaves and rebuild via the explicit
    ``complex_pairs_to_ndarray`` (now returning a ``list[complex]``)."""
    from srmech.math.mat import Mat
    from srmech.mcp._coercion import (
        coerce_param,
        complex_pairs_to_ndarray,
        serialise_native,
    )

    # bytes <-> base64 (incl. non-UTF-8 / NUL bytes).
    raw = b"\x00\xff\x10binary\x7f"
    assert coerce_param(serialise_native(raw), "bytes") == raw

    # complex <-> [re, im].
    z = complex(3.0, -2.5)
    assert coerce_param(serialise_native(z), "complex") == z
    # A bare JSON number decodes to complex(n, 0).
    assert coerce_param(5, "complex") == complex(5, 0)

    # real matrix <-> nested list (EXACT — values + shape). A Mat serialises
    # to a nested list; the "np.ndarray" inbound coercion returns it unchanged
    # (the numpy-free wire form).
    rows = [[1.0, 2.0], [3.0, 4.0]]
    back = coerce_param(serialise_native(Mat.from_rows(rows)), "np.ndarray")
    assert back == rows

    # complex matrix: serialised as [re, im] leaves, rebuilt via the explicit
    # complex builder which now returns a flat list[complex]. A 1xN complex Mat
    # serialises to [[[re,im],[re,im]]]; the builder takes the [re,im] pair list,
    # so pass the single row.
    cvals = [1 + 2j, 3 - 4j]
    row = serialise_native(Mat.from_rows([cvals]))[0]
    assert list(complex_pairs_to_ndarray(row)) == cvals
    # The bare pair-list form round-trips directly to list[complex].
    assert list(complex_pairs_to_ndarray([[1.0, 2.0], [3.0, -4.0]])) == [1 + 2j, 3 - 4j]


def test_serialise_native_emits_json_serialisable() -> None:
    """``serialise_native`` output is always JSON-serialisable for the
    awkward Python types ops return.

    numpy-free (#564): there is no ndarray branch in ``serialise_native``.
    The matrix carrier is ``Mat`` (``.tolist()``'d, complex entries → ``[re,
    im]`` leaves); scalars are plain Python ``int`` / ``float`` / ``complex``;
    containers (tuple / list / dict, incl. bytes keys) recurse."""
    from srmech.math.mat import Mat
    from srmech.mcp._coercion import serialise_native

    samples: List[Any] = [
        b"\x00\xff",
        complex(1, 2),
        Mat.from_rows([[1.0, 2.0, 3.0]]),         # real Mat
        Mat.from_rows([[1 + 1j, 2 - 2j]]),        # complex Mat
        7,
        1.5,
        255,
        (1, 2, b"ab"),
        {b"key": [1, 2]},
        {"nested": [3, complex(0, 1)]},
    ]
    for s in samples:
        # Must not raise — the load-bearing guarantee for the tool_result.
        json.dumps(serialise_native(s))


def test_invalid_base64_bytes_raises_clear_error() -> None:
    """A malformed base64 value for a ``bytes`` param raises a clear
    ValueError naming the param (per the rc14 contract)."""
    from srmech.mcp._coercion import coerce_param

    with pytest.raises(ValueError, match="base64"):
        # '!' is not a valid base64 alphabet char (validate=True).
        coerce_param("not!valid!base64!", "bytes", param="data")


def test_coerce_param_none_passthrough_for_optional() -> None:
    """A JSON ``null`` (Python ``None``) for an ``Optional[...]`` param
    passes through as ``None`` regardless of the declared element type —
    NOT a 0-d object array (which ``np.asarray(None)`` would build)."""
    from srmech.mcp._coercion import coerce_param

    assert coerce_param(None, "Optional[np.ndarray]") is None
    assert coerce_param(None, "np.ndarray") is None
    assert coerce_param(None, "bytes") is None
    assert coerce_param(None, "complex") is None


# ──────────────────────────────────────────────────────────────────────
# Targeted round-trip + live-path tests through invoke_tool (the shared
# MCP + Anthropic entry). Each asserts the result is JSON-serialisable.
# ──────────────────────────────────────────────────────────────────────


def _b64(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode("ascii")


def _assert_json_serialisable(raw: Any) -> None:
    """A tool result must JSON-serialise through ``serialise_result`` (the
    server slot is textual JSON)."""
    text = serialise_result(raw)
    json.loads(text)  # round-trips through json; raises on failure


def test_invoke_naming_lookup_base64_params() -> None:
    """``naming.lookup`` with base64 key + base64 (key, value) pairs
    returns the matching value — no TypeError — and serialises to JSON."""
    raw = invoke_tool(
        "srmech.introspect.naming.lookup",
        {
            "key": _b64(b"A"),
            "pairs": [[_b64(b"A"), _b64(b"content-addressing")]],
        },
    )
    assert raw == b"content-addressing"
    _assert_json_serialisable(raw)


def test_invoke_template_render_base64_mapping() -> None:
    """``template.render`` with base64 template + base64->base64 mapping
    renders the bytes; the result base64-encodes in JSON."""
    import base64

    raw = invoke_tool(
        "srmech.math.template.render",
        {"template_bytes": _b64(b"Class {x}"), "mapping": {_b64(b"x"): _b64(b"A")}},
    )
    assert raw == b"Class A"
    text = serialise_result(raw)
    assert json.loads(text) == base64.b64encode(b"Class A").decode("ascii")


def test_invoke_hdc_bind_base64_roundtrips() -> None:
    """``hdc.bind`` of two base64 byte-vectors returns bound bytes; the
    base64 result round-trips back to the same bytes."""
    import base64

    from srmech.mcp._coercion import coerce_param

    a = bytes([1, 2, 3, 4])
    b = bytes([5, 6, 7, 8])
    raw = invoke_tool(
        "srmech.math.hdc.bind", {"a": _b64(a), "b": _b64(b)}
    )
    assert raw == bytes(x ^ y for x, y in zip(a, b))
    text = serialise_result(raw)
    encoded = json.loads(text)
    assert encoded == base64.b64encode(raw).decode("ascii")
    # The serialised base64 coerces straight back to the bound bytes.
    assert coerce_param(encoded, "bytes") == raw


def test_invoke_jacobi_eigvals_nested_list_matrix() -> None:
    """``laplacian.jacobi_eigvals`` with a nested-list real symmetric
    matrix returns an eigenvalue list (JSON array)."""
    matrix = [
        [2.0, -1.0, 0.0],
        [-1.0, 2.0, -1.0],
        [0.0, -1.0, 2.0],
    ]
    raw = invoke_tool(
        "srmech.math.laplacian.jacobi_eigvals", {"matrix": matrix}
    )
    vals = sorted(raw)
    assert len(vals) == 3
    # Oracle = the substrate-native EXACT real-symmetric eigvals cascade
    # (``eigvals_exact``, numpy-free), NOT np.linalg.eigvalsh. (The closed form
    # of this tridiagonal is 2 ± √2, 2: {0.5858…, 2.0, 3.4142…}.)
    from srmech.cascade.matrix_cascades import eigvals_exact

    expected = sorted(eigvals_exact(matrix))
    assert len(expected) == 3
    for got, want in zip(vals, expected):
        assert abs(got - want) < 1e-9
    text = serialise_result(raw)
    assert isinstance(json.loads(text), list)


def test_invoke_higgs_potential_complex_phi() -> None:
    """``qm.sm.higgs_potential`` with phi=[re, im] returns a real float;
    the result is JSON-serialisable."""
    raw = invoke_tool(
        "srmech.physics.qm.sm.higgs_potential",
        {"phi": [1.0, 0.5], "mu_squared": 2.0, "lam": 1.0},
    )
    # V = -mu^2 |phi|^2 + lam |phi|^4; |phi|^2 = 1.25.
    assert isinstance(raw, float)
    assert abs(raw - (-2.0 * 1.25 + 1.0 * 1.25 ** 2)) < 1e-12
    _assert_json_serialisable(raw)


def test_invoke_dispatch_match_base64_rules() -> None:
    """``dispatch.match`` with base64 input + [base64, int] rules returns
    a serialisable result (the (matched, tag) tuple -> JSON list)."""
    raw = invoke_tool(
        "srmech.math.dispatch.match",
        {"input_bytes": _b64(b"hello"), "rules": [[_b64(b"he"), 1], [_b64(b"xyz"), 2]]},
    )
    _assert_json_serialisable(raw)


def test_invoke_klein4_expand_seed_reproducible_rc14_path() -> None:
    """rc13 seeded-mint reproducibility still holds through the rc14
    coercion path (carrier result -> JSON list, bit-identical). rc290
    retargets it from ``klein4_random(seed=)`` to ``klein4_expand`` — the
    same MT19937 stream under the name that describes it."""
    r1 = serialise_result(
        invoke_tool("srmech.math.hdc.klein4_expand", {"D": 8, "seed": 42})
    )
    r2 = serialise_result(
        invoke_tool("srmech.math.hdc.klein4_expand", {"D": 8, "seed": 42})
    )
    assert r1 == r2
    assert set(json.loads(r1)) <= {0, 1, 2, 3}


# ──────────────────────────────────────────────────────────────────────
# Schema rendering hints (v0.5.0rc14, STEP 3) — so an LLM learns HOW to
# encode bytes / ndarray / complex / containers.
# ──────────────────────────────────────────────────────────────────────


def test_schema_renders_encoding_hints() -> None:
    """The MCP/Anthropic schema property for a non-JSON native type
    carries its JSON-encoding hint in the description, and the rc13
    property-key grammar + rc10 name discipline stay intact."""
    schema = get_tool_schema()

    def _prop(tool_name: str, param: str) -> Dict[str, Any]:
        entry = schema.lookup(tool_name)
        assert entry is not None, f"{tool_name} not registered"
        return tool_entry_to_mcp_def(entry)["inputSchema"]["properties"][param]

    # bytes -> string + base64 hint.
    p = _prop("srmech.amsc.format.sha256_bytes", "data")
    assert p["type"] == "string"
    assert "base64" in p["description"]

    # np.ndarray -> array + nested-array hint.
    p = _prop("srmech.math.laplacian.jacobi_eigvals", "matrix")
    assert p["type"] == "array"
    assert "nested JSON array" in p["description"]

    # complex -> array + [real, imaginary] hint.
    p = _prop("srmech.physics.qm.sm.higgs_potential", "phi")
    assert p["type"] == "array"
    assert "real, imaginary" in p["description"]

    # Mapping[bytes, bytes] -> object + base64 key/value hint.
    p = _prop("srmech.math.template.render", "mapping")
    assert p["type"] == "object"
    assert "base64" in p["description"]

    # list[tuple[bytes, int]] -> array + [base64, integer] hint.
    p = _prop("srmech.math.dispatch.match", "rules")
    assert p["type"] == "array"
    assert "base64" in p["description"]


def test_encoding_hints_preserve_property_key_grammar() -> None:
    """Adding encoding hints must not perturb the rc13 property-key
    grammar ratchet — every property key still matches Anthropic's
    ``^[a-zA-Z0-9_.-]{1,64}$`` (the hint lives in the VALUE's description,
    never the KEY)."""
    schema = get_tool_schema()
    for entry in schema.tools:
        mcp_def = tool_entry_to_mcp_def(entry)
        for key in mcp_def["inputSchema"]["properties"]:
            assert _ANTHROPIC_PROPERTY_KEY_RE.match(key), (
                f"{entry.name}: property key {key!r} violates grammar"
            )


# ──────────────────────────────────────────────────────────────────────
# Every-tool invocation smoke (v0.5.0rc15; upstream §10.1)
#
# THE GAP rc14's static ratchet missed: ``has_coercer(type)`` proves a
# declared type has *a* coercion handler, but ``SpectralHandle``'s handler
# was ``_identity`` (pass-through) — so the static ratchet went GREEN even
# though the tool was not actually invocable across the JSON boundary.
# rc15 closes this with an EMPIRICAL smoke: synthesise minimal valid args
# from each advertised tool's schema (using the rc14 encodings per declared
# type) and actually CALL it through ``invoke_tool``.
#
# We test CALLABILITY, not domain validity:
#   * a BINDING error (TypeError: unexpected/missing kwarg) is a FAILURE —
#     the schema declares a param the callable can't bind;
#   * a COERCION error (the synth value won't coerce to the native type) is
#     a FAILURE — the encoding the schema advertises doesn't round-trip;
#   * a DOMAIN error (ValueError / non-square matrix / length mismatch /
#     ZeroDivision / a real op-internal AssertionError) is TOLERATED — it
#     PROVES the tool was reached with bindable + coercible args.
#
# The 7 ``mcp_callable=False`` handle-pending spectral tools are NOT in the
# advertised surface, so they are not synthesised here (and a companion
# assertion proves they are absent from both advertised catalogs).
# ──────────────────────────────────────────────────────────────────────


def _synth_spectral_handle_envelope() -> Dict[str, Any]:
    """Mint a real ``SpectralHandle`` (decompose a 2-node state on a 2x2
    Hermitian Laplacian) and return its registered ``$srmech_handle`` id
    envelope — the by-reference wire value for a ``SpectralHandle`` param.

    The handle is registered in the SAME process-wide registry the inbound
    coercer resolves against (via ``serialise_native``), so a downstream
    ``invoke_tool`` call binds AND resolves a genuine handle (the smoke's
    contract: any descriptor-hash mismatch vs a different synth laplacian is
    a TOLERATED domain error, proving the tool was reached)."""
    from srmech.spectral import decompose
    from srmech.mcp._coercion import serialise_native

    # numpy-free: decompose accepts plain lists.
    state = [1.0, 0.0]
    laplacian = [[1.0, -1.0], [-1.0, 1.0]]
    handle = decompose(state, laplacian)
    return serialise_native(handle)


def _synth_chain_spec_wire() -> Dict[str, Any]:
    """A GENUINE minimal chain — one Class-I step, ``gcd(12, 18)`` -> 6 — as the
    JSON object a client puts on the wire for a ``ChainSpec`` param.

    rc414 (`#T1092`) — this row was ``"ChainSpec": {}``, an empty dict, and it
    was adequate ONLY because nothing downstream validated it: ``coerce_param``
    mapped ``ChainSpec`` to the ``_identity`` pass-through, so ``{}`` sailed
    through coercion and the op then raised a TOLERATED domain error. rc414
    gives the type a real coercer (``_to_chain_spec`` -> ``parse_chain_spec``),
    and a real coercer correctly REJECTS ``{}`` with
    ``ChainSpecError: chain entry missing required key 'name'``.

    THE FIX IS THE SYNTH VALUE, NOT THE COERCER. Widening ``_to_chain_spec`` to
    accept ``{}`` would restore the exact anti-pattern rc408 named — advertising
    a value that cannot work — one layer further down, and it is the anti-pattern
    this whole rc exists to remove.

    THIS IS THE THIRD INSTANCE OF THE SAME SHAPE. ``"callable": "abs"`` became
    ``"operator_name": "srmech.cascade.chiral_flip"`` at rc16 for exactly this
    reason (a str that is not callable, tolerated as a TypeError), and
    ``SpectralHandle`` became a freshly-minted registered envelope in the same
    rc. A placeholder is only ever "fine" until something starts checking it,
    and then it reads as a product bug rather than as test scaffolding.

    The same table has a fourth, still-live instance, tracked separately as
    `#T1094`: the fall-through ``return table.get(type_string, "a")`` hands the
    literal ``"a"`` to EVERY undeclared string param — including filesystem
    paths — so a smoke run writes a stray 16-byte file named ``a`` into the
    package directory. Not fixed here; it needs its own rc, and gitignoring the
    file would close the symptom while preserving the defect.

    The chain is chosen so it genuinely EXECUTES: class ``I`` resolves to
    ``srmech.math.cyclic`` (not ``srmech.cascade`` — the class registry maps
    letters to owning modules), ``gcd`` is a real op on it, and both consumers
    of this value work — ``run_chain`` returns ``6`` and ``resolve_chain``
    returns a callable that returns ``6``.
    """
    return {
        "name": "smoke_gcd",
        "summary": "one Class-I step: gcd(12, 18)",
        "returns": "int",
        "steps": [{"class": "I", "op": "gcd", "args": {"a": 12, "b": 18}}],
    }


def _synth_value_for_type(type_string: str) -> Any:
    """Synthesise ONE minimal, schema-valid JSON-wire value for a declared
    ToolEntry param type, using the rc14 coercion encodings.

    Returns the value an MCP / Anthropic client would put on the wire
    (base64 ``str`` for bytes, nested list for ndarray, ``[re, im]`` for
    complex, etc.) — ``invoke_tool``'s inbound coercion turns it native.
    A type with no explicit case falls through to a JSON string (the
    lexicon's own degrade-to-string default), so a never-before-seen type
    still gets *a* value rather than a KeyError in the test harness.
    """
    import base64

    # 2x2 identity as a nested list (valid square matrix for the
    # Laplacian / Hermitian ops; also a valid length-2 row vector source).
    mat2 = [[1.0, 0.0], [0.0, 1.0]]
    # A short flat vector (valid for matvec / state / 1-D array ops).
    vec = [1.0, 0.0]
    b64 = base64.b64encode(b"abcd").decode("ascii")

    table: Dict[str, Any] = {
        "int": 1,
        "Optional[int]": 1,
        "float": 1.0,
        "Optional[float]": 1.0,
        "number": 1.0,
        "bool": True,
        # rc430 (`#T1094`): was ``"a"``. Any literal is equally arbitrary for a
        # label-shaped string, but a SELF-DESCRIBING one is traceable: if this
        # value ever escapes into a file, a log or an error message, its name
        # says where it came from. Path-shaped params never reach this row —
        # tier 3 of ``_synth_args_for_entry`` diverts them to a sandbox path.
        "str": "srmech_synth",
        "Optional[str]": "srmech_synth",
        "bytes": b64,
        "complex": [1.0, 0.0],
        # ndarray: a 2x2 identity (square — satisfies the most ops; the
        # vector ops accept it as a 2-row matrix or re-shape internally;
        # any shape complaint is a tolerated DOMAIN error).
        # rc42 zeilberger BiPoly operand: a minimal valid nonzero bivariate ratio
        # — k-slot 0 is the Poly-in-n [1, 1] (= 1 + n). Coerces + binds cleanly;
        # any "no recurrence" is a tolerated DOMAIN result, not a binding error.
        "BiPoly": [[1, 1]],
        # rc53 apagodu_zeilberger TriPoly operand: a minimal valid nonzero
        # trivariate ratio — j-slot 0 is the BiPoly [[1, 1]] (= 1 + n). Coerces
        # + binds cleanly; any "no recurrence" is a tolerated DOMAIN result.
        "TriPoly": [[[1, 1]]],
        # rc55 q_gosper QPoly operand: a minimal valid nonzero Laurent-in-x ℚ[q]
        # term ratio — a single x⁰ cell carrying the constant ℚ[q] coefficient 2
        # (the q-geometric Σ 2ᵏ numerator). [[2]] avoids the 2-element-list
        # (num, den) ambiguity of QPoly's own cell coercion; coerces + binds
        # cleanly, and as a term-ratio numerator yields a DOMAIN-valid certificate.
        "QPoly": [[2]],
        # rc56 q_zeilberger QBiPoly operand: a minimal valid nonzero bivariate-q
        # term ratio — a single Y⁰ cell carrying the QPoly [[2]] (one X⁰ cell, the
        # constant ℚ[q] coefficient 2; the q-geometric numerator). The q-analog of
        # the BiPoly [[1, 1]] sample; coerces + binds cleanly, and as a term-ratio
        # numerator yields a DOMAIN-valid (k-free q-geometric) recurrence.
        "QBiPoly": [[[2]]],
        # rc61 elliptic_gosper EllRatio operand: a minimal valid term ratio — the
        # exact-ℚ SCALAR (3, 2) (the elliptic-geometric constant ratio r = 3/2). The
        # coercer builds EllRatio.monomial(EllMonomial.scalar(3/2)); coerces + binds
        # cleanly, and as a term ratio yields a DOMAIN-valid certificate R = 2 (the
        # elliptic-geometric closed form 1/(z−1) = z_den/(z_num−z_den)).
        "EllRatio": [3, 2],
        # rc290 hdc.klein4_from_one One operand: the One's OWN canonical
        # JSON-native dict (the shape _to_jsonable emits / one_from_jsonable
        # reads) — sigma=+1, theta=1/4, default terms. Coerces + binds cleanly
        # and yields a real ONE-A14 coupling vector.
        "One": {"sigma": 1, "theta": [1, 4], "terms": 24},
        # rc231 (#810) elliptic_jackson_an z / a variable vectors: a list of
        # symbol-NAME strings — the natural minimal operand for the Aₙ variables
        # (each lifts to EllMonomial.symbol via _to_ellmonomial). Both z and a get
        # this same value, so len(a) != len(z)+1 is a TOLERATED domain ValueError
        # (the op was CALLED with bindable + coercible args — the property tested).
        "list[EllMonomial]": ["z0", "z1"],
        # rc362 music.stiff_string_partials `inharmonicity`: the exact-ℚ carrier
        # rides as [num, den]. B = 1/1000 is a realistic piano stiffness and is
        # in-domain (B >= 0), so the op returns a genuine Tier-2 spectrum rather
        # than a tolerated domain error.
        "Q": [1, 1000],
        # rc462 (`#T1179`) the UNION spelling, which is a different table key
        # from either half: `srmech.math.rational.rational_div`'s `a` / `b`
        # declare `Q | tuple[int, int]`, and the rows for `Q` and for
        # `tuple[int, int]` beside it do not answer for it. It went
        # unsynthesizable only when a FULL example-args re-harvest measured
        # what that op's snippet now passes — `rational_add` returns a `Q`
        # since the Class-N precision migration, so the two args arrive as `Q`
        # objects and the tier-1 ledger route stops supplying them. Value is
        # the `Q` row's, which is a proper nonzero rational: it is a valid
        # divisor, so the op returns an answer rather than a tolerated domain
        # error.
        "Q | tuple[int, int]": [1, 1000],
        # rc463 fix pass — the exact-ℚ matrix operand family. rc463 registered
        # eighteen new ToolEntries and TEN of their required parameters had no
        # row here, pushing the unsynthesizable residual 52 -> 62. The ceiling
        # is DOWN-ONLY and raising it is exactly the move the gate exists to
        # prevent, so the rows are added instead; measured after, the residual
        # is back at 52 and the skipped-op count back at 34, both AT their
        # ceilings rather than under a raised one.
        #
        # A 2x2 diagonal integer matrix, which is the intersection of what all
        # eight consumers need: SQUARE (qmat_det / _inverse / _rref / _solve),
        # NONSINGULAR (qmat_inverse, qmat_solve, and lstsq_exact's AᵀA),
        # m >= n (lstsq_exact), and INTEGER (singular_values_exact refuses a
        # float by name). Every one of them returns a real answer on it rather
        # than a tolerated domain error.
        "QMat | Sequence[Sequence[int | Q]]": [[2, 0], [0, 3]],
        # The right-hand side of the same two solvers, as the FLAT exact column
        # the ops accept — length 2, matching the matrix above, so qmat_solve
        # returns [[2], [3]] and lstsq_exact an exact list[Q]. This is the arm
        # `qmat_solve`'s own shipped smoke_test_hint uses and could not reach
        # through the wire before the fix pass.
        "QMat | Sequence[Sequence[int | Q]] | Sequence[int | Q]": [4, 9],
        # separate_frame_curvature's dual-rung operand. INTEGER leaves on
        # purpose: they select the exact-ℚ QMat rung, which is the rung the
        # entry advertises and the one the wire could not reach while the
        # param was declared `Mat`. The 2x2 identity commutes with itself, so
        # the op returns is_flat True rather than raising.
        "Mat | QMat | Sequence[Sequence[int | Q]]": [[1, 0], [0, 1]],
        # rc467 (`#T1188`): the same union with the exact-complex leaf --
        # hermitian_eigendecompose's operand, widened so a real `Qi` entry
        # can reach the exact route it has always shipped. The synthesised
        # value stays INTEGER for the same reason as the row above (it
        # selects the exact rung), and the 2x2 identity is Hermitian, so
        # the op answers rather than raising on its own symmetry check.
        "Mat | QMat | Sequence[Sequence[int | Q]] | list[list[Qi]]":
            [[1, 0], [0, 1]],
        # The exact eigensolver's algebraic eigenvalue (eigvec_exact /
        # eigvec_exact_float / jordan_chains_exact `lam`), in the canonical
        # JSON mapping _to_qalg reads: λ = 1 as an element of ℚ[x]/(x − 1),
        # with m and coords ASCENDING and `root` present — a Qalg built
        # WITHOUT root is refused by the op's own projection rather than
        # silently naming a different conjugate, so omitting it here would
        # synthesise an argument that cannot be used. λ = 1 is a genuine
        # eigenvalue of the 2x2 identity these three ops get for `a`, so each
        # returns a real eigenvector rather than an empty domain answer.
        "Qalg": {"m": [-1, 1], "coords": [[1, 1]], "root": 1.0},
        # rc362 the acoustic-spectrum wire form (music.spectrum_tier /
        # commensurability_verdict / common_period `partials`): the Fletcher &
        # Rossing tuned-bell profile — hum 1/2, prime 1, tierce 6/5, quint 3/2,
        # nominal 2. In-domain for all three ops, so each returns a real answer
        # (tier 1 / verdict "harmonic" / period 10) instead of raising.
        "Sequence[int | Q | Qalg]": [[1, 2], [1, 1], [6, 5], [3, 2], [2, 1]],
        "np.ndarray": mat2,
        "Optional[np.ndarray]": mat2,
        # v0.7.5rc72 Mat carrier (mat_matmul): a 2x2 list-of-rows -> real Mat;
        # square so mat_matmul(a, b) returns cleanly.
        "Mat": mat2,
        # v0.7.5rc132 carrier-spirit param types. The carrier is AGNOSTIC about
        # input, so each synth is the DEGENERATE Python form (flat list / nested
        # list); the op's own acceptance builds the final carrier.
        #   Vec  -> a short flat vector (valid for matvec / state / k / dot ops).
        #   HV   -> a length-8 hypervector valid for BOTH the Klein-4 byte ops
        #           ({0,1,2,3}) AND the power-of-two octonion ops (length 8 is a
        #           power of two; polar/int8 ops tolerate a tolerated domain error
        #           on a 2/3 element, but length-8 {0,1,2,3} is in-domain for the
        #           dominant klein4 / octonion families).
        "Vec": vec,
        "HV": [0, 1, 2, 3, 0, 1, 2, 3],
        # rc465-fix (`#T1188`): the widened qm coordinate-vector union. The
        # SAME value as the `HV` row above, deliberately — the union's first arm
        # IS `HV`, and the widening changed what the ops ACCEPT, not what a
        # minimal valid argument looks like. Without this row `quaternion_slerp`
        # `q1` (the one param of the ten with no harvested value) fell through to
        # UNSYNTHESIZABLE and `test_synth_args_provenance_rc430` went 52 -> 53
        # over its down-only ceiling — a type-table gap reported as a coverage
        # regression, which is exactly what that ceiling is for.
        "HV | Sequence[int | Q]": [0, 1, 2, 3, 0, 1, 2, 3],
        "Optional[Vec]": vec,
        "Optional[HV]": [0, 1, 2, 3, 0, 1, 2, 3],
        "Mat | Vec": mat2,   # the 2-D arm satisfies the most ops; 1-D is tolerated
        # 0.9.0rc466 (`#T1188`) stage 3: the five PARAM spellings the seventy-row
        # drain widened (the leaves select the carrier; floats keep the float
        # route, so the synth value is the SAME value the narrower spelling got
        # and every op that returned under it still returns).
        "Vec | Sequence[int | Q]": vec,
        "Mat | Vec | Sequence[int | Q]": mat2,
        "list[float] | list[Q]": [1.0, 2.0],
        "list[list[float]] | list[list[Q]]": mat2,
        "float | Q": 1.0,
        # v0.7.5rc155: the §50 holographic-bundle accumulator (klein4_bundle_*).
        #   accumulate's `acc` synths to None — accumulate(None, v) is the clean
        #   fold-start (creates a fresh accumulator sized to v); resolve's `acc`
        #   synths to a minimal valid (1 + 2*D) uint32 accumulator (D=1, n=1).
        "array('I')|None": None,
        "array('I')": [1, 0, 0],
        # container element-recursions (minimal valid shapes).
        "Sequence[bytes]": [b64, b64],
        "list[bytes]": [b64, b64],   # v0.7.0rc10: format.sha256_batch `datas`
        "Sequence[Vec]": [vec, vec],
        "Sequence[HV]": [[0, 1, 2, 3], [0, 1, 2, 3]],
        "tuple[Mat, ...]": [mat2, mat2],
        # rank-3 nested list (gauge structure constants f^abc); a minimal 1x1x1.
        "list[list[list[float]]]": [[[0.0]]],
        # rc113 qbipoly_from_coeffs `coeffs` (also modular_linalg.gf_rref
        # `rows`): a minimal Y-ascending list of integer x-cell lists — Y⁰ cell
        # 1 + 2X, Y¹ cell 3 (a valid nonzero QBiPoly; the same shape is a valid
        # 2-row GF matrix for gf_rref, whose non-prime synth `p` stays a
        # tolerated domain error).
        "list[list[int]]": [[1, 2], [3]],
        # rc113 theta_coefficients `theta`: the named g₃ shadow — the MCP
        # coercer builds unary_theta('minus12', 1, 1, 0, 24) from the string
        # (also drives harmonic_maass's `shadow` with a genuine UnaryTheta).
        "UnaryTheta": "g3",
        # legacy numpy-free wire-form keys (no param advertises them now).
        "Sequence[np.ndarray]": [vec, vec],
        "tuple[np.ndarray, ...]": [mat2, mat2],
        # v0.7.0rc36 spectral_cascades: each complex scalar rides as [re, im].
        # dft/idft take a 1-D complex vector; kron takes two complex matrices.
        "list[complex]": [[1.0, 0.0], [0.0, 1.0]],
        "list[list[complex]]": [[[1.0, 0.0], [0.0, 0.0]],
                                [[0.0, 0.0], [1.0, 0.0]]],
        "Mapping[bytes, bytes]": {b64: b64},
        "list[tuple[bytes, int]]": [[b64, 1]],
        "list[tuple[bytes, bytes]]": [[b64, b64]],
        # a self-loop on node 0 — a valid edge for any graph size n >= 1
        # (so the laplacian ops, whose `n` synths to 1, return cleanly).
        "list[tuple[int, int]]": [[0, 0]],
        "tuple[int, int]": [1, 1],
        # rc430 (`#T1094`): kept as the declared row, but it is no longer what
        # a Path param actually receives — ``_synth_args_for_entry`` tier 3
        # overrides every path-SHAPED param with a sandbox path. A bare
        # relative filename here would be created in whatever directory the
        # suite happens to run from, which is the same defect as ``"a"``
        # wearing a longer name.
        # JSON-native-ish.
        "dict": {},
        "Optional[dict]": {},
        "list": [1, 2],
        "list[int]": [1, 2, 3],
        "Optional[list[float]]": [1.0, 2.0],
        "iterable[int]": [1, -1, 1],
        "sequence": [1, 2, 3],
        "pathlib.Path": "smoke_nonexistent_path.toml",
        "int | float | str | list | dict": 1,
        # opaque in-process handles. ``callable`` / ``numpy.random.Generator``
        # bind as a name / None and let the op raise a tolerated DOMAIN error.
        # rc414 (`#T1092`) — ``ChainSpec`` synths to a GENUINE, EXECUTABLE chain
        # (was ``{}``, adequate only while the coercer was the ``_identity``
        # pass-through; a real coercer rightly rejects an empty dict). See
        # ``_synth_chain_spec_wire`` for why the synth value is the fix and
        # widening the coercer would not be.
        "ChainSpec": _synth_chain_spec_wire(),
        "callable": "abs",
        # rc16 — ``operator_name`` synths to a GENUINE unary seq->seq op so
        # chiral_dual is driven cleanly (was the old "callable"->"abs"
        # str-not-callable tolerated TypeError). The srmech-namespace
        # allow-list resolves it; chiral_flip is a real seq->seq operator.
        "operator_name": "srmech.cascade.chiral_flip",
        # rc16 — a SpectralHandle synths to a FRESHLY-MINTED, registered
        # by-reference id envelope so recompose/predict/truncate_sparse bind
        # + RESOLVE a genuine handle (any descriptor-hash mismatch vs the 2x2
        # synth laplacian is a TOLERATED domain ValueError). The union keeps
        # the base64 bytes arm (delta/similarity/prediction_error exercise
        # the raw-bytes path; the handle arm is covered by a dedicated unit).
        "SpectralHandle": _synth_spectral_handle_envelope(),
        "SpectralHandle | bytes": b64,
        "numpy.random.Generator": None,
    }
    # rc430 (`#T1094`): the blind fall-through is GONE. It was
    # ``table.get(type_string, "a")``, which handed the literal ``"a"`` to
    # every type this table does not name — including filesystem paths, so a
    # smoke run wrote a stray 16-byte file named ``a`` into the package
    # directory. Substituting a plausible-looking value for a type nobody
    # declared is not a default, it is a silent guess, and the guess was
    # destructive. An unnamed type is now VISIBLE and COUNTED (the caller
    # skips and records the reason) rather than papered over.
    return table.get(type_string, _ea.UNSYNTHESIZABLE)


def _synth_args_for_entry(entry: Any) -> Dict[str, Any]:
    """Build a minimal valid args dict for one ToolEntry: fill every
    REQUIRED param with a synth value; omit optionals (we are testing the
    minimal-required call path).

    rc430 (`#T1094`) — THREE TIERS, most-justified first:

    1. **The harvest**, keyed by ``(op, param)``. An argument recorded from
       this op's own published worked example, in a call that RETURNED, is
       valid BY CONSTRUCTION. This is the only tier that can tell
       ``cyclic_mod_add``'s ``n`` from ``is_prime``'s ``n``, or
       ``genome_save``'s ``path`` from ``normal_order``'s ``convention`` —
       a type-keyed table cannot, which is why this one accreted 61 rows.
    2. **The type table** above, for the types it names.
    3. **A sandbox path** for anything path-SHAPED, so the op may write and
       the write lands in a temp directory nothing reads. Measured at rc430:
       the harvest closes only **3 of 33** path-ish parameters, because the
       genome worked snippets deliberately leave ``path`` unbound (the
       shipped ``worked_examples_result.ndjson`` has been recording that as
       ``NameError: name 'path' is not defined`` all along). So tier 3 is not
       a nicety — without it this fix would cover a tenth of its own subject.

    Anything left is :data:`UNSYNTHESIZABLE`, and the caller SKIPS with a
    recorded reason. Absence is a value here; a fabricated argument is not.
    """
    prov = _ea.provider()
    args: Dict[str, Any] = {}
    for p in entry.parameters:
        if not p.required:
            continue
        val = prov.get(entry.name, p.name)                       # tier 1
        if val is _ea.UNSYNTHESIZABLE:
            val = _synth_value_for_type(p.type)                  # tier 2
        if val is _ea.UNSYNTHESIZABLE or _ea.is_path_shaped(p.name, p.type):
            # tier 3 — path-shaped wins over the table, because the table's
            # ``pathlib.Path`` row is a bare relative filename and creating
            # THAT in the package directory is the same defect wearing a
            # longer name.
            if _ea.is_path_shaped(p.name, p.type):
                val = _ea.sandbox_path(p.name)
        args[p.name] = val
    return args


def _unsynthesizable_params(args: Dict[str, Any]) -> List[str]:
    """Params in a synth map with no justified value (rc430, `#T1094`)."""
    return sorted(k for k, v in args.items() if v is _ea.UNSYNTHESIZABLE)


def _is_binding_error(exc: BaseException) -> bool:
    """A TypeError that signals a kwarg-binding mismatch (the failure mode
    the every-tool smoke exists to catch) — as opposed to a TypeError
    raised by the op's own domain logic (e.g. an arithmetic on an
    incompatible synth value)."""
    if not isinstance(exc, TypeError):
        return False
    msg = str(exc).lower()
    binding_markers = (
        "unexpected keyword argument",
        "required positional argument",
        "required keyword-only argument",
        "missing",
        "got multiple values",
        "takes no arguments",
        "positional arguments but",
        "takes",  # "...takes N positional arguments but M were given"
    )
    return any(m in msg for m in binding_markers)


def test_advertised_tool_registry_not_small() -> None:
    """Aggregate guard split out of the (now parametrized) every-tool smoke
    (`#T1007`): the advertised registry must not have silently shrunk. The
    per-op nodes below name any single broken tool; this asserts the SET is
    the expected size (the old ``assert len(advertised) > 50``)."""
    assert len(_ADVERTISED) > 50, "advertised tool registry unexpectedly small"


@pytest.mark.parametrize("entry", _ADVERTISED, ids=lambda e: e.name)
def test_advertised_tool_invocable(entry: Any) -> None:
    """§10.1 — THE EVERY-TOOL INVOCATION SMOKE, one node PER advertised tool
    (`#T1007`; was a single ~30-min loop over every ``mcp_callable`` ToolEntry —
    an atomic node ``--dist loadfile`` could not split).

    For THIS ``mcp_callable=True`` ToolEntry: synthesise minimal valid args from
    its schema (rc14 encodings per declared type), then invoke it via
    ``invoke_tool``. FAIL on a BINDING error (the schema declares a param the
    callable can't bind), a COERCION error (the advertised encoding doesn't
    round-trip), a non-serialisable result, or a RETURN-TYPE mismatch. DOMAIN
    errors (ValueError, non-square matrix, length mismatch, ZeroDivision,
    op-internal AssertionError / TypeError) are TOLERATED — they prove the tool
    was CALLED with bindable + coercible args (we test callability, not domain
    validity). The tolerance logic and the exact fail conditions are UNCHANGED
    from the pre-`#T1007` accumulate-then-assert loop; only the granularity is
    finer (a broken tool NAMES itself instead of hiding in an accumulated list).

    This is the empirical complement to the rc14 ``has_coercer`` ratchet,
    which could not tell a real coercer from the ``_identity`` pass-through
    that left the SpectralHandle tools statically-green but uninvocable.
    """
    from srmech.mcp._tools import _coerce_arguments

    synth = _synth_args_for_entry(entry)

    # rc430 (`#T1094`): a param with no justified value is SKIPPED and NAMED,
    # never filled with a guess. The population of such params is held under a
    # down-only ceiling by tests/test_synth_args_provenance_rc430.py, so this
    # skip cannot quietly become the normal case — which is the only thing
    # that would make it worse than the literal ``"a"`` it replaces.
    missing = _unsynthesizable_params(synth)
    if missing:
        pytest.skip(
            f"{entry.name}: no justified value for required param(s) "
            f"{missing} — types {[p.type for p in entry.parameters if p.name in missing]}. "
            f"Counted by test_synth_args_provenance_rc430.py "
            f"(CEIL_UNSYNTHESIZABLE); NOT silently defaulted.")

    # Phase 1 — coercion in isolation. A failure here means the advertised
    # wire-encoding for some declared type does not coerce to the native type
    # (a real, fixable surface bug).
    try:
        _coerce_arguments(entry, synth)
    except Exception as exc:  # noqa: BLE001 — classify below
        pytest.fail(
            f"{entry.name}: COERCION {type(exc).__name__}: {exc}\n"
            f"      args={synth!r}"
        )

    # Phase 2 — full invoke (coerce + resolve + call). Tolerate domain errors;
    # flag only binding errors. The result itself must JSON-serialise (the
    # server slot is textual JSON) — a result that cannot serialise is also a
    # real surface bug.
    try:
        raw = invoke_tool(entry.name, synth)
    except TypeError as exc:
        if _is_binding_error(exc):
            pytest.fail(
                f"{entry.name}: BINDING TypeError: {exc}\n      args={synth!r}"
            )
        return  # op-internal TypeError == reached the op (tolerated domain)
    except Exception:  # noqa: BLE001 — tolerated domain error
        # ValueError / ZeroDivisionError / AssertionError /
        # MCPToolError-from-domain etc. — the tool WAS called with bindable +
        # coercible args. That is the property under test; the domain rejection
        # is expected for synth data.
        return

    # Reached the op AND returned — the result must be serialisable.
    try:
        serialise_result(raw)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            f"{entry.name}: RESULT not serialisable "
            f"{type(exc).__name__}: {exc}\n      args={synth!r}"
        )

    # rc131 — RETURN-TYPE AGREEMENT. Assert ``type(raw)`` AGREES with the
    # advertised ``returns.type`` (the immolation gate owns the canonical
    # guard; this folds the inspection into the every-tool harness). ``None``
    # agreement (an unassertable handle / unknown type) is skipped, exactly as
    # the immolation gate skips it.
    if entry.returns is not None:
        from conftest import return_type_agrees
        agrees = return_type_agrees(raw, entry.returns.type)
        if agrees is False:
            pytest.fail(
                f"{entry.name}: RETURN-TYPE mismatch: observed "
                f"{type(raw).__name__!r} does not match advertised "
                f"{entry.returns.type!r}\n      args={synth!r}"
            )


def test_handle_pending_absent_from_advertised_catalogs() -> None:
    """v0.5.0rc16 (held through rc17) — the rc15 catalog-EXCLUSION ratchet is
    INVERTED to a catalog-INCLUSION ratchet. The 7 ``srmech.spectral.*`` tools
    became ``mcp_callable=True`` once the by-reference ``$srmech_handle``
    grammar landed, so there are now ZERO handle-pending tools and all 7
    spectral names are PRESENT in BOTH advertised surfaces (MCP ``tools/list``
    via ``tool_entries_to_mcp_defs`` AND the Anthropic ``_build_tool_catalog``
    seam). (If a residual handle-pending tool is ever introduced later, a
    fresh exclusion assertion can be re-added for it.)

    v0.9.0rc414 (`#T1092`) — that parenthetical is now cashed in. The rc16
    assertion was ``pending == set()``, i.e. "zero excluded, forever"; rc414
    excludes ``srmech.introspect.publish``, whose obstruction is not a type an
    encoder can fix but a SHAPE IN TIME (a ``with``-block scope cannot span two
    JSON-RPC calls). The rc16 property that actually matters — the 7 spectral
    tools are PRESENT in both advertised surfaces, because the ``$srmech_handle``
    grammar rescued them — is untouched below and is what this test still
    guards. What replaces the strict-zero is the EXCLUSION-IS-HONOURED pair:
    whatever is excluded must be absent from BOTH advertised catalogs (not
    merely flagged in the registry), so the field and the seams cannot drift
    apart."""
    schema = get_tool_schema()
    pending = {e.name for e in schema.tools if not e.mcp_callable}

    # THE EXCLUSION IS HONOURED, not just declared. A flip that the seams
    # ignore is worse than no flip: the tool stays advertised while the
    # registry says it is not callable.
    advertised_mcp = {d["name"] for d in tool_entries_to_mcp_defs()}
    leaked = pending & advertised_mcp
    assert leaked == set(), (
        f"entries marked mcp_callable=False are STILL advertised over MCP: "
        f"{leaked}. The exclusion filter did not take effect — on a native "
        f"host the compiled registry is the live path, so this also means "
        f"srmech_tool_registry.c needs regenerating and libsrmech rebuilding."
    )

    spectral_names = {
        "srmech.spectral.decompose",
        "srmech.spectral.delta",
        "srmech.spectral.recompose",
        "srmech.spectral.similarity",
        "srmech.spectral.predict",
        "srmech.spectral.prediction_error",
        "srmech.spectral.truncate_sparse",
    }

    # MCP advertised surface (the tools/list seam) — the 7 are PRESENT.
    mcp_names = {d["name"] for d in tool_entries_to_mcp_defs()}
    assert spectral_names <= mcp_names, (
        f"spectral tools missing from the MCP advertised catalog: "
        f"{spectral_names - mcp_names}"
    )

    # Anthropic catalog seam — replicate _build_tool_catalog's filter
    # exactly (it excludes mcp_callable=False, then synthesises names) — the
    # 7 are PRESENT.
    anthropic_srmech_names = {
        e.name for e in schema.tools if e.mcp_callable
    }
    assert spectral_names <= anthropic_srmech_names, (
        f"spectral tools missing from the Anthropic catalog: "
        f"{spectral_names - anthropic_srmech_names}"
    )
    assert not (pending & anthropic_srmech_names), (
        f"excluded entries leaked into the Anthropic catalog seam: "
        f"{pending & anthropic_srmech_names}"
    )

    # rc414 — the advertised catalog is EXACTLY the callable subset. rc16's
    # ``spectral_names <= mcp_names`` is a SUBSET check over 7 hardcoded names,
    # so it cannot see the advertised catalog silently losing entries it does
    # not name. (Measured during the rc414 research: a stale libsrmech
    # advertised 556 against a 559-entry registry, and no gate reported it —
    # two of the three missing names were ops MCP_INSTRUCTIONS tells a client
    # to call.) This equality is the missing half.
    assert advertised_mcp == {
        e.name for e in schema.tools if e.mcp_callable
    }, (
        "the advertised MCP catalog is not exactly the mcp_callable subset; "
        "on a native host this usually means the compiled registry in "
        "libsrmech is stale against the Python registry — rebuild it"
    )


# ──────────────────────────────────────────────────────────────────────
# rc16 — by-reference handle dual-grammar coercion (empirical proof the
# rc14/15 ``_identity`` pass-throughs are now REAL resolvers, which the
# static ``has_coercer`` ratchet structurally cannot see).
# ──────────────────────────────────────────────────────────────────────


def test_spectral_handle_param_coercer_resolves() -> None:
    """``coerce_param(envelope, 'SpectralHandle')`` returns the LIVE
    ``SpectralHandle`` whose content_sha matches the original — i.e. the
    coercer is no longer the rc14 ``_identity`` pass-through."""
    from srmech.spectral import SpectralHandle, decompose
    from srmech.mcp._coercion import coerce_param, serialise_native

    state = [1.0, 2.0]
    laplacian = [[1.0, -1.0], [-1.0, 1.0]]
    handle = decompose(state, laplacian)

    env = serialise_native(handle)
    # Outbound is a by-reference id object, NOT the inline 4-field dict.
    assert "$srmech_handle" in env
    assert "coefficients_bytes" not in json.dumps(env)

    resolved = coerce_param(env, "SpectralHandle")
    assert isinstance(resolved, SpectralHandle)
    assert resolved.content_sha == handle.content_sha


def test_spectral_handle_or_bytes_discriminates() -> None:
    """The union coercer resolves a ``$srmech_handle`` envelope to a
    ``SpectralHandle`` AND decodes a bare base64 ``str`` to ``bytes`` —
    both arms, so raw-bytes callers are preserved."""
    import base64

    from srmech.spectral import SpectralHandle, decompose
    from srmech.mcp._coercion import coerce_param, serialise_native

    handle = decompose([1.0, 2.0], [[1.0, -1.0], [-1.0, 1.0]])
    env = serialise_native(handle)

    # Handle arm.
    resolved = coerce_param(env, "SpectralHandle | bytes")
    assert isinstance(resolved, SpectralHandle)
    # Bytes arm.
    b64 = base64.b64encode(b"\x01\x02\x03\x04").decode("ascii")
    raw = coerce_param(b64, "SpectralHandle | bytes")
    assert raw == b"\x01\x02\x03\x04"


def test_operator_name_param_resolves_callable() -> None:
    """``coerce_param('srmech.cascade.chiral_flip', 'operator_name')``
    returns a callable; ``invoke_tool`` drives chiral_dual end-to-end with
    NO TypeError (the rc15 over-advertisement is now honest); an unknown /
    out-of-namespace op name raises a clean error."""
    from srmech.mcp._coercion import coerce_param

    fn = coerce_param("srmech.cascade.chiral_flip", "operator_name")
    assert callable(fn)

    # End-to-end through invoke_tool: chiral_dual(chiral_flip, [1,2,3]) =
    # chiral_flip(chiral_flip(chiral_flip(x))) — three reversals net to ONE
    # reversal, so the result is the reversed sequence.
    res = invoke_tool(
        "srmech.cascade.chiral_dual",
        {"op": "srmech.cascade.chiral_flip", "x": [1.0, 2.0, 3.0]},
    )
    assert list(res) == [3.0, 2.0, 1.0]

    # Out-of-namespace op (os.system) is rejected at coercion time.
    with pytest.raises(ValueError):
        coerce_param("os.system", "operator_name")


def test_evicted_handle_in_invoke_gives_clean_error() -> None:
    """Referencing a handle envelope whose uuid is NOT in the registry
    (e.g. evicted) yields a clean ``HandleNotFoundError`` (a tolerated
    domain error), not an opaque crash."""
    from srmech._handles import HandleNotFoundError, encode_envelope

    stale = encode_envelope("0" * 32, "spectral:deadbeefdead", "spectral")
    with pytest.raises(HandleNotFoundError):
        invoke_tool(
            "srmech.spectral.recompose",
            {"handle": stale, "laplacian": [[1.0, -1.0], [-1.0, 1.0]]},
        )
