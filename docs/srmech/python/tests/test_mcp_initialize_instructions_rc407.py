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
    cosmetic. Over MCP, ``get_tool_schema``'s result serialises through
    ``dataclasses.asdict`` and carries keys that the canonical ``to_jsonable``
    rendering behind ``tool_schema_view`` deliberately omits. Two disagreeing
    renderings of one registry over one protocol; the instructions must name
    the canonical one.

    ⚠️ **The count in this paragraph read FIVE until rc430, and it was stale in
    both directions.** Re-measured at rc430 — asdict **3,026,848** bytes vs
    view **2,923,519** — the per-entry omission covers **NINE** keys:
    ``composes`` (452 entries) · ``frame_axis`` (635) · ``frame_scope`` (635) ·
    ``mcp_unavailable_reason`` (651) · ``preserves`` (592) · ``reads_input``
    (646) · ``reads_lane`` (646) · ``returns`` (1) · ``smoke_test_hint`` (609).
    Two of those are rc430's frame axis; but ``returns`` and
    ``smoke_test_hint`` were in the class all along and the rc411 list simply
    missed them, because it enumerated the always-empty-default fields and not
    the ``Optional`` ones. The rc411 byte figures are kept nowhere — they were
    a live claim, not a dated ledger entry, so they are replaced rather than
    struck.

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


# ── 3. the excluded-tools contract must not restate a stale count ─────────────

def test_every_excluded_entry_carries_a_reason_and_no_count_is_restated() -> None:
    """The rc407 incidental, re-aimed at rc414 (`#T1092`).

    rc407 deleted a hardcoded ``7`` from ``tool_entries_to_mcp_defs``'s
    docstring — a count that had been wrong since rc16 — and replaced it with
    ``excluded == []`` plus ``"== 0" in doc``. Those two assertions fixed the
    stale-count defect by pinning the OTHER literal: "zero, forever". That is
    the same failure shape rc407 was correcting, one release later, and rc414
    is the release that trips it — it ships the first legitimately-excluded
    entry (``srmech.introspect.publish``: a ``with``-block scope cannot span two
    JSON-RPC calls).

    So the assertion is re-aimed at the PROPERTY rc407 was really protecting,
    which no literal can express and no future count can invalidate: **an
    excluded entry must say why**. A consumer that notices a tool missing from
    ``tools/list`` can always recover the reason from the introspection surface,
    and the advertised catalog is exactly the callable subset. Neither clause
    names a number, so neither can go stale."""
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    from srmech.mcp._tools import tool_entries_to_mcp_defs

    warmup_all()
    schema = get_tool_schema()
    excluded = [t for t in schema.tools if not t.mcp_callable]

    # (a) EXCLUSION IS ALWAYS EXPLAINED. A bare False with a NULL reason is what
    #     c/include/srmech.h documents as the CALLABLE case, so an unexplained
    #     exclusion is also a C-side ambiguity, not only an unhelpful one.
    unexplained = [t.name for t in excluded if not t.mcp_unavailable_reason]
    assert unexplained == [], (
        f"{len(unexplained)} entries are mcp_callable=False with no "
        f"mcp_unavailable_reason: {unexplained}. Excluding a tool is "
        f"legitimate; excluding it silently is not — the reason IS the "
        f"consumer's only route from 'this tool is missing' to 'and here is "
        f"what to call instead'.")

    # (b) The reverse: a reason with no exclusion is an orphan claim.
    orphaned = [t.name for t in schema.tools
                if t.mcp_callable and t.mcp_unavailable_reason]
    assert orphaned == [], (
        f"{len(orphaned)} advertised entries carry an mcp_unavailable_reason: "
        f"{orphaned}. A reason that explains nothing has outlived the "
        f"exclusion it described.")

    # (c) The advertised catalog is EXACTLY the callable subset — derived on
    #     both sides, never a literal.
    advertised = len(list(tool_entries_to_mcp_defs()))
    callable_n = sum(1 for t in schema.tools if t.mcp_callable)
    assert advertised == callable_n, (
        f"advertised catalog has {advertised} defs but {callable_n} entries "
        f"are mcp_callable — the exclusion filter and the field disagree")

    # (d) NO COUNT IS RESTATED in the docstring. rc407 removed a stale ``7``;
    #     rc410 removed a restated registry total; this keeps both gone. The
    #     docstring may still QUOTE the historical wording to say what changed,
    #     which is why the check is on a bare-integer pattern rather than on
    #     any particular substring being absent.
    doc = tool_entries_to_mcp_defs.__doc__ or ""
    restated = re.findall(r"==\s*\d+", doc)
    assert restated == [], (
        f"the docstring restates a literal count {restated}; that is exactly "
        f"what went stale in rc15 (7) and again in rc410 (the registry total). "
        f"State the invariant, not the number.")
