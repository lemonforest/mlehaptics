"""Tool-schema registration for srmech.bus (v0.5.0rc7).

Registers the UTLP Bio-TOTP wire-format decoder
(:func:`srmech.bus._bio_totp.decode_splice`) as a
:class:`srmech.amsc.tool_schema.ToolEntry` so LLM / agent consumers
can introspect (and call) the cipher's pure decoder surface without
reading the implementation. Load-bearing for the rc6 MCP-adapter
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
                "Decode one frame of a UTLP Bio-TOTP bus channel "
                "(Claim 255 alignment) given the per-channel DNA "
                "secret. Pure function (no side effects); suitable "
                "for LLM / agent introspection of mid-stream "
                "traffic. Returns (plaintext, used_time_ns); the "
                "plaintext is the original JSON-encoded bus Event "
                "and the used_time_ns is the candidate time-bucket "
                "value that successfully decoded (the current bucket "
                "or ±1 bucket for clock-skew tolerance). Cipher: "
                "AES-128-CTR when ``pip install srmech[crypto]`` "
                "extra is installed (UTLP-exact path); HMAC-SHA-256 "
                "counter-mode keystream by default (stdlib-only, "
                "structurally equivalent for the defensive-scope "
                "threat model). Key derivation rolls every 250 ms "
                "(WINDOW_NS=250_000_000; configurable via "
                "``SRMECH_BUS_TOTP_WINDOW_NS`` env var); the receiver "
                "tolerates ±1 window for clock skew. Frame layout: "
                "[nonce:16][ciphertext]; nonce = sender_id_u64 || "
                "channel_id_u32 || packet_seq_u32. Pass ZERO_DNA "
                "(b'\\x00'*32) for herd-immunity / public mode. "
                "v0.5.0rc7 (Bio-TOTP wire format; UTLP Claim 255)."
            ),
            parameters=(
                ToolParameter(
                    "framed", "bytes", required=True,
                    summary=(
                        "Frame body (nonce[16] || ciphertext) — the "
                        "unwrapped TLV payload."
                    ),
                ),
                ToolParameter(
                    "dna", "bytes", required=True,
                    summary=(
                        "32+ byte pre-shared Bio-TOTP secret. Pass "
                        "ZERO_DNA (b'\\x00'*32) for herd-immunity / "
                        "public mode (same code path; deterministic "
                        "ciphertext recoverable by anyone)."
                    ),
                ),
                ToolParameter(
                    "window_ns", "int", required=False,
                    summary=(
                        "Optional time-window override in "
                        "nanoseconds (default 250_000_000 = 250 ms; "
                        "env-var ``SRMECH_BUS_TOTP_WINDOW_NS`` "
                        "honoured)."
                    ),
                ),
                ToolParameter(
                    "time_ns", "int", required=False,
                    summary=(
                        "Optional explicit wall-clock override "
                        "(defaults to time.time_ns()). Useful for "
                        "replaying historical captures."
                    ),
                ),
            ),
            returns=ToolReturn(
                type="tuple[bytes, int]",
                shape=(
                    "(plaintext, used_time_ns) — JSON-encoded bus "
                    "Event bytes, and the candidate time value that "
                    "decoded successfully."
                ),
            ),
            smoke_test_hint={
                # Smoke hint is intentionally not a real frame — the
                # tool-schema smoke-test layer doesn't synthesise valid
                # framed bytes on its own. Real usage threads through
                # BioTotpChannel.encrypt() to produce framed inputs.
                "framed": "b'<framed-bytes>'",
                "dna": "b'<32-byte-dna>'",
            },
        )
    )
    # v0.5.0rc9: register the bus discovery surfaces so MCP /
    # Claude Code consumers can enumerate live endpoints owned by
    # the current user and look up a specific endpoint by name.
    # These were previously invisible to the LLM catalog even though
    # the public Python API at ``srmech.bus.list_endpoints`` /
    # ``srmech.bus.by_name`` has been load-bearing since v0.5.0rc1.
    register_tool(
        ToolEntry(
            name="srmech.bus.list_endpoints",
            owner="srmech",
            category="bus",
            summary=(
                "Enumerate currently-running srmech.bus endpoints "
                "owned by the current user by scanning the "
                "`~/.srmech/bus-*.sock` (POSIX) / `~/.srmech/bus-*.txt` "
                "(Windows) registry directory. Best-effort liveness "
                "check per endpoint (POSIX: UDS connect probe; "
                "Windows: TCP loopback connect or WaitNamedPipeW "
                "probe). Side effect (when `cleanup_dead=True`, the "
                "default): registration files for endpoints whose "
                "server is no longer accepting connections are "
                "removed from disk on read. Returns `[]` on Pyodide "
                "/ WASM (no socket support). Sorted alphabetically "
                "by endpoint name. v0.5.0rc9 (MCP / catalog "
                "discoverability; backing function shipped since "
                "v0.5.0rc1)."
            ),
            parameters=(
                ToolParameter(
                    "cleanup_dead", "bool", required=False,
                    summary=(
                        "When True (default), registration files "
                        "for endpoints with no live server are "
                        "removed from disk as a side effect."
                    ),
                ),
            ),
            returns=ToolReturn(
                type="list[Endpoint]",
                shape=(
                    "Each Endpoint is a frozen dataclass: name "
                    "(str), path (pathlib.Path), transport ('uds' "
                    "POSIX / 'pipe' or 'tcp' Windows), alive "
                    "(bool), pid (Optional[int], currently always "
                    "None — reserved for a future rc that records "
                    "owner PID in the registry file)."
                ),
            ),
        )
    )
    register_tool(
        ToolEntry(
            name="srmech.bus.by_name",
            owner="srmech",
            category="bus",
            summary=(
                "Look up one srmech.bus endpoint by name. Same "
                "registry scan as `srmech.bus.list_endpoints` but "
                "returns just the matching record (or `None` if no "
                "endpoint of that name is registered for the current "
                "user). Does NOT auto-clean dead-endpoint "
                "registration files (the caller may want to inspect "
                "a dead endpoint's record). Returns `None` on "
                "Pyodide / WASM. v0.5.0rc9 (MCP / catalog "
                "discoverability; backing function shipped since "
                "v0.5.0rc1)."
            ),
            parameters=(
                ToolParameter(
                    "name", "str", required=True,
                    summary=(
                        "Endpoint name (matches the name passed to "
                        "`srmech.bus.serve(name, ...)`)."
                    ),
                ),
            ),
            returns=ToolReturn(
                type="Endpoint | None",
                shape=(
                    "Frozen dataclass with name (str), path "
                    "(pathlib.Path), transport ('uds' / 'pipe' / "
                    "'tcp'), alive (bool), pid (Optional[int]). "
                    "`None` when no matching endpoint is "
                    "registered."
                ),
            ),
        )
    )


# Fire the registration at module-import time. srmech.bus.__init__
# imports this module so importing srmech.bus is sufficient.
_register_bus_tools()


__all__ = [
    "_register_bus_tools",
]
