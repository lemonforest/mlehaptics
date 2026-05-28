"""Tool-schema registration for srmech.bus (v0.5.0rc3).

Registers the state-chained wire-format decoder as a
:class:`srmech.amsc.tool_schema.ToolEntry` so LLM / agent consumers
can introspect (and call) the cipher's pure decoder surface without
reading the implementation. Load-bearing for the rc5 MCP-adapter
work where the bus apparatus is exposed to Claude Code over MCP.

Idempotent: registration goes through :func:`register_tool` which
silently no-ops on re-registration of an identical entry.

Framework reading: the tool-schema is itself a Class A surface
(content-addressed callable identifier) ∘ Class E (catalog enumeration);
mounting the bus cipher's decoder into it composes the wire-layer
substrate-self-recognition (Class A + I + K) with the LLM-facing
catalog substrate-self-recognition (Class A + E).
"""

from __future__ import annotations

from ..amsc.tool_schema import (
    ToolEntry,
    ToolParameter,
    ToolReturn,
    register_tool,
)


def _register_bus_tools() -> None:
    """Register srmech.bus's LLM-facing tool entries.

    Called once at import time from :mod:`srmech.bus.__init__`.
    """
    register_tool(
        ToolEntry(
            name="srmech.bus.decode_splice",
            owner="srmech",
            category="bus",
            summary=(
                "Decode one frame of a state-chained bus channel "
                "given the held chain state + last-accepted counter. "
                "Pure function (no side effects); suitable for LLM / "
                "agent introspection of mid-stream traffic. Returns "
                "(plaintext, new_state, new_counter); the caller "
                "holds the new state + counter for the next call. "
                "Cipher: SHA-256 keystream + HMAC-SHA-256 integrity; "
                "state advances as state_{N+1} = sha256(state_N || "
                "'st' || ciphertext_N). v0.5.0rc3 (state-chained "
                "wire format; UTLP-inspired)."
            ),
            parameters=(
                ToolParameter(
                    "framed", "bytes", required=True,
                    summary=(
                        "Frame body (mac[16] || counter_be8[8] || "
                        "ciphertext) — the unwrapped TLV payload."
                    ),
                ),
                ToolParameter(
                    "state", "bytes", required=True,
                    summary=(
                        "32-byte chain state the sender used for this "
                        "frame (the held state on the caller's side)."
                    ),
                ),
                ToolParameter(
                    "counter", "int", required=True,
                    summary=(
                        "Last-accepted counter on this direction. "
                        "Pass -1 for the first frame in a chain. "
                        "Inbound frame's counter must be strictly "
                        "greater (replay protection)."
                    ),
                ),
            ),
            returns=ToolReturn(
                type="tuple[bytes, bytes, int]",
                shape=(
                    "(plaintext, new_state, new_counter) — plaintext "
                    "bytes, 32-byte next chain state, just-accepted "
                    "counter."
                ),
            ),
            smoke_test_hint={
                # Smoke hint is intentionally not a real frame — the
                # tool-schema smoke-test layer doesn't synthesise valid
                # framed bytes on its own. Real usage threads through
                # ChainState.encrypt() to produce framed inputs.
                "framed": "b'<framed-bytes>'",
                "state": "b'<32-byte-state>'",
                "counter": "-1",
            },
        )
    )


# Fire the registration at module-import time. srmech.bus.__init__
# imports this module so importing srmech.bus is sufficient.
_register_bus_tools()


__all__ = [
    "_register_bus_tools",
]
