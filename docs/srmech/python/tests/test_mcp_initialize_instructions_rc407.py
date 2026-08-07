"""rc407 (`#T1076`) — the MCP handshake carries a start-here pointer, in BOTH
projections.

The gap
=======
``_handle_initialize`` returned exactly ``{capabilities, protocolVersion,
serverInfo}`` — verified by driving ``MCPServer.handle``, not by reading the
source — and the C peer ``mcp_build_initialize`` closed with
``"},\\"capabilities\\":{\\"tools\\":{}}}}``. So an MCP client received **no route
to the capability index before its first tool call**, and MCP offers no other
channel for one: ``resources/*``, ``prompts/*``, ``completion/*`` and
``logging/*`` all return "unknown method" from this server.

That matters more here than for a typical server, because ``tools/list``
descriptions are built from ``summary`` + an optional ``Returns:`` line + the
``[srmech category: …; owner: …]`` tag ONLY. The ``example`` and ``explanation``
fields — every registered entry carries both — have no MCP route at any granularity,
so a client that cannot find a capability has no way to learn that it is looking
at one field of fourteen.

What the instructions may say
=============================
Only checked claims, because an MCP-only client cannot verify any of them:

* ``srmech.introspect.describe`` and
  ``srmech.introspect.carrier_schema.carrier_schema`` are registered ToolEntries
  with ``mcp_callable=True`` — safe to tell a client to CALL.
* ``get_tool_schema`` is **not** a registered tool (no ToolEntry's last segment
  is ``get_tool_schema``), so it is named as a PYTHON route. Telling an MCP-only
  client to call it would be exactly the class of falsehood rc407 exists to
  drain.

ADR-0009 parity
===============
The capability is the invariant and the two projections are co-equal, so the
string is asserted **byte-identical** across them. The C literal is parsed out
of ``c/src/srmech_mcp.c`` rather than mirrored into a fixture here, so this test
cannot pass by agreeing with a stale copy of itself.

It is a file-scope ``static const char[]`` rather than a ``#define`` because a
multi-line macro violates JPL Power-of-Ten Rule 8, and those violations only
ever go DOWN (``tests/test_jpl_audit.py``). Confirmed by trying the macro first
and watching Rule 8 fail.

No exported function's wire format changes, so ``SRMECH_ABI_VERSION`` stays.

Pure stdlib + srmech; numpy-free; no ``abs()``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from srmech.mcp._server import MCP_INSTRUCTIONS, MCPServer

_HERE = Path(__file__).resolve().parent
_SR_ROOT = _HERE.parent.parent                      # docs/srmech
_MCP_C = _SR_ROOT / "c" / "src" / "srmech_mcp.c"


def _initialize_result() -> dict:
    """Drive the real server, rather than reading the handler's source."""
    server = MCPServer()
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05"},
    }
    response = server.handle(request)
    if isinstance(response, str):
        response = json.loads(response)
    assert response is not None, "initialize produced no response"
    return response["result"]


# ── 1. the field exists and routes somewhere real ─────────────────────────────

def test_initialize_returns_instructions() -> None:
    """The handshake carries ``instructions``. **Fails before rc407.**"""
    result = _initialize_result()
    assert "instructions" in result, (
        f"initialize result has no `instructions` field; got "
        f"{sorted(result)}. An MCP client gets no start-here pointer before "
        f"its first tool call, and no other MCP method on this server answers.")
    assert result["instructions"] == MCP_INSTRUCTIONS


def test_instructions_route_to_the_capability_index() -> None:
    """It must name the registered entry point, not just say something."""
    text = _initialize_result()["instructions"]
    assert "srmech.introspect.describe" in text, (
        "the instructions do not name `srmech.introspect.describe` — the one "
        "registered, mcp_callable capability index")


def test_instructions_only_promise_mcp_callable_tools() -> None:
    """Anything the instructions tell a client to CALL must be registered and
    ``mcp_callable``; anything unregistered must be framed as a Python route.

    v0.9.0rc411 (`#T1086`) — REVISITED, exactly as the rc407 tripwire below
    demanded. rc407 wrote: *"get_tool_schema is deliberately NOT callable over
    MCP; if it ever becomes a registered tool this assertion fires and the
    wording should be revisited."* rc411 registered it — the whole rc is that
    the registry did not contain its own front door — so the assertion fired on
    a shipped string that had become FALSE. ``example`` and ``explanation`` ARE
    reachable over MCP now, and the text said they were not.

    The wording was re-pointed at ``tool_schema_view`` rather than at
    ``get_tool_schema``, and that choice is load-bearing rather than
    cosmetic. Measured on this tree: over MCP, ``get_tool_schema``'s result
    serialises through ``dataclasses.asdict`` (2,572,811 bytes) and carries
    FIVE keys — ``composes`` / ``preserves`` / ``reads_input`` / ``reads_lane``
    / ``mcp_unavailable_reason`` — that the canonical ``to_jsonable`` rendering
    behind ``tool_schema_view`` (2,501,642 bytes) deliberately omits. Two
    disagreeing renderings of one registry over one protocol; the instructions
    must name the canonical one.

    ``get_tool_schema`` was deliberately left ``mcp_callable`` (the default):
    flipping it would make it the FIRST ``mcp_callable=False`` row in the
    registry, which ``test_no_mcp_callable_false_entries_and_docstring_states_
    no_count`` below asserts is empty, and would move ``describe()``'s
    published ``handle_pending``. That is `#T1092`'s question, not rc411's.
    """
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    schema = get_tool_schema()
    callable_names = {t.name for t in schema.tools if t.mcp_callable}

    text = _initialize_result()["instructions"]
    for promised in ("srmech.introspect.describe",
                     "srmech.introspect.search.search",
                     "srmech.introspect.tool_schema.tool_schema_view",
                     "srmech.introspect.carrier_schema.carrier_schema"):
        assert promised in text
        assert promised in callable_names, (
            f"the instructions tell a client to call {promised!r}, which is "
            f"not a registered mcp_callable ToolEntry")

    # The rc407 tripwire, re-aimed at what is now the live hazard. The text must
    # NOT send an MCP client to `get_tool_schema`: its over-the-wire rendering
    # is the non-canonical asdict shape documented above, so naming it here
    # would point clients at the schema that disagrees.
    assert "get_tool_schema" not in text, (
        "the instructions name `get_tool_schema` as an MCP route. Its MCP "
        "serialisation is dataclasses.asdict, which carries five keys "
        "to_jsonable omits — send clients to `tool_schema_view` instead.")


# ── 2. ADR-0009 — the two projections are co-equal ────────────────────────────

#: One C string literal, with its surrounding quotes.
_C_STRING = re.compile(r'\s*"((?:[^"\\]|\\.)*)"')


def _c_instructions() -> str:
    """The C literal, reassembled from adjacent string literals in the .c file.

    Walks the literals one at a time from the ``=`` to the terminating ``;``.
    A ``(.*?);`` capture is WRONG here and silently truncates: the text itself
    contains a semicolon ("...the `summary` field only; each op also has..."),
    so a non-greedy scan to the first ``;`` returned 211 of 646 characters and
    made the parity assertion fail against a correct tree."""
    source = _MCP_C.read_text(encoding="utf-8")
    anchor = re.search(
        r"static\s+const\s+char\s+srmech_mcp_instructions\s*\[\s*\]\s*=",
        source,
    )
    assert anchor, (
        f"could not find `srmech_mcp_instructions` in {_MCP_C} — if it was "
        f"renamed, this parity gate must be updated with it")

    pos = anchor.end()
    parts = []
    while True:
        piece = _C_STRING.match(source, pos)
        if piece is None:
            break
        parts.append(piece.group(1))
        pos = piece.end()
    assert parts, "the declaration holds no string literal"
    assert source[pos:].lstrip()[:1] == ";", (
        "the declaration did not end at a `;` after its string literals — the "
        "reassembly is out of step with the source")
    return "".join(parts)


def test_c_peer_carries_the_same_instructions_byte_for_byte() -> None:
    """**ADR-0009.** The capability is the invariant; a one-sided edit is a
    parity break, not a Python-only change."""
    assert _c_instructions() == MCP_INSTRUCTIONS, (
        "the C and Python `instructions` strings have diverged.\n"
        f"  C      : {_c_instructions()!r}\n"
        f"  Python : {MCP_INSTRUCTIONS!r}\n"
        "Edit BOTH projections in the same commit.")


def test_c_peer_emits_the_field_in_the_initialize_payload() -> None:
    """Byte-equality of the literal is not enough — the C builder must actually
    put it in the response, or the two projections still disagree on the wire."""
    source = _MCP_C.read_text(encoding="utf-8")
    builder = re.search(
        r"static void mcp_build_initialize\(.*?\n\}", source, re.S)
    assert builder, "mcp_build_initialize not found"
    body = builder.group(0)
    assert '\\"instructions\\":' in body, (
        "mcp_build_initialize does not emit an `instructions` key — the Python "
        "projection returns one, so the C peer would answer a different "
        "handshake")
    assert "srmech_mcp_instructions" in body, (
        "mcp_build_initialize does not emit the shared literal")


# ── 3. the excluded-tools docstring must not restate a stale count ────────────

def test_no_mcp_callable_false_entries_and_docstring_states_no_count() -> None:
    """The rc407 incidental: ``tool_entries_to_mcp_defs`` claimed 7 excluded
    ``srmech.spectral.*`` handle-pending tools; the measured count is 0."""
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    from srmech.mcp._tools import tool_entries_to_mcp_defs

    warmup_all()
    schema = get_tool_schema()
    excluded = [t.name for t in schema.tools if not t.mcp_callable]
    assert excluded == [], (
        f"{len(excluded)} entries are mcp_callable=False: {excluded}. That is "
        f"legitimate, but the docstring deliberately states no count — record "
        f"the reason for the handle-pending entries instead.")
    assert len(list(tool_entries_to_mcp_defs())) == len(schema.tools)

    # Assert POSITIVELY that the correction is recorded. A "the 7 is absent"
    # check would be brittle in the other direction: the docstring legitimately
    # QUOTES the stale wording in order to say what changed, so the substring
    # is present on purpose.
    doc = tool_entries_to_mcp_defs.__doc__ or ""
    assert "== 0" in doc, (
        "the docstring no longer records that the measured mcp_callable=False "
        "count is 0; it claimed 7 from v0.5.0rc15 until rc407, and a bare "
        "count here is exactly what went stale")
