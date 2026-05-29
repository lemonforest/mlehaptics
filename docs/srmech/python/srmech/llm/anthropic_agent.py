"""Anthropic Claude SDK agent adapter (v0.5.0rc9; secondary).

For users who script the Anthropic Claude API directly outside Claude
Code (FastAPI servers, Jupyter notebooks, CI pipelines, etc.) using
the ``anthropic`` Python SDK.

For Claude Code users, the rc6 :mod:`srmech.mcp` adapter
(``srmech-mcp``) is the primary integration path — no API key needed,
billing handled by the Claude Code Max plan. This adapter is
SECONDARY for users who:

* Run Claude inside their own application (FastAPI server, Jupyter
  notebook, CI pipeline, …) using the ``anthropic`` Python SDK.
* Need programmatic control of the tool-use message-loop.
* Don't have Claude Code in their workflow.

Same tool catalog as MCP (the ~149 :class:`ToolEntry` registrations
in :mod:`srmech.amsc.tool_schema`); same MPR attestation discipline
per tool call (re-uses :func:`srmech.mcp._server.build_attestation`
so the two adapters emit byte-identical attestation envelopes for
the same tool/result pair).

Name mapping
------------
The Anthropic tool-name grammar is ``^[a-zA-Z0-9_-]{1,64}$``. srmech
tool names contain dots (``srmech.amsc.format.sha256_bytes``); the
adapter substitutes ``_`` for ``.`` when handing the tool catalog to
Claude, and reverses the substitution when invoking. Per-tool name
length stays well under the 64-char ceiling for the
``srmech.amsc.*`` catalog (the longest is currently 47 chars).

Optional dep
------------
The ``anthropic`` SDK is an OPTIONAL dependency. Install with
``pip install srmech[anthropic]``. Default install does NOT add it;
:func:`AnthropicAgent.__init__` raises :class:`ImportError` with a
helpful message if the SDK is absent.

Framework reading
-----------------
Class M (cross-class bind) ∘ Class E (catalog enumeration) ∘ Class
A (content-addressing via SHA-256 attestation) ∘ Class B (TLV-shaped
JSON-Schema framing). The substrate-class-instance is the direct
``anthropic`` SDK round-trip rather than MCP's stdio JSON-RPC; the
A–N composition is invariant.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# Optional dep — graceful import. We bind ``anthropic`` to None when
# unavailable so the rest of the module can reference the module-level
# name without NameError; AnthropicAgent.__init__ is the gate that
# raises ImportError with a useful install hint.
try:
    import anthropic  # type: ignore
    _HAVE_ANTHROPIC = True
except ImportError:  # pragma: no cover — default install
    anthropic = None  # type: ignore[assignment]
    _HAVE_ANTHROPIC = False


# ──────────────────────────────────────────────────────────────────────
# Anthropic tool-name grammar
# ──────────────────────────────────────────────────────────────────────


# Anthropic's tool-name grammar (per the SDK's request validation):
# ``^[a-zA-Z0-9_-]{1,64}$``. srmech tool names contain dots, so the
# adapter swaps ``.`` for ``_`` round-trip. The reverse map is
# rebuilt at agent-construction time from the live tool registry, so
# any future tool that introduces an underscore in its name still
# round-trips unambiguously (we never collide a synthesised name with
# a real srmech name because the reverse map is keyed on the SAME
# synthesised string we hand to Claude).
ANTHROPIC_TOOL_NAME_MAX_LEN: int = 64
"""Per the Anthropic SDK's tool-name validator."""


def _to_anthropic_name(srmech_name: str) -> str:
    """Map a srmech dotted name -> an Anthropic-grammar-safe name."""
    assert srmech_name, "name must be non-empty"
    out = srmech_name.replace(".", "_")
    assert len(out) <= ANTHROPIC_TOOL_NAME_MAX_LEN, (
        f"srmech tool name {srmech_name!r} maps to a string of length "
        f"{len(out)} > Anthropic's 64-char ceiling; truncating would "
        f"break round-trip"
    )
    return out


# ──────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────


@dataclass
class AnthropicAgentConfig:
    """Configuration for :class:`AnthropicAgent`.

    Parameters
    ----------
    model
        Claude model identifier. Defaults to ``"claude-sonnet-4-6"``
        (current recommended Sonnet line as of 2026-05).
    max_tokens
        Per-call generation cap for the SDK ``messages.create`` calls
        the agent issues. Default 4096.
    api_key
        If supplied, used verbatim; otherwise falls back to the
        ``ANTHROPIC_API_KEY`` environment variable.
        :class:`AnthropicAgent` raises :class:`ValueError` if neither
        is set.
    tool_filter
        Optional ``str -> bool`` predicate over tool names. When
        supplied, only tools whose srmech-name passes the predicate
        are exposed to Claude. Useful for narrowing the catalog (e.g.
        only the cascade subtree) on slower model lines.
    system_prompt
        System prompt prepended to every conversation. The default
        names srmech and the A–N vocabulary so Claude has the right
        framing without the caller having to re-introduce it.
    max_tool_iterations
        Safety cap on the number of tool_use round-trips per
        :meth:`AnthropicAgent.run` call. Default 10. If Claude is
        still requesting tool calls after this many round-trips,
        :meth:`run` returns with ``stop_reason="max_iterations"`` and
        the caller can inspect the partial transcript.
    """

    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096
    api_key: Optional[str] = None
    tool_filter: Optional[Callable[[str], bool]] = None
    system_prompt: str = (
        "You are a research assistant with access to srmech tools "
        "(Stored-Relationship Mechanism — 14-class A-N primitive "
        "vocabulary, cascade catalog, signal processing, etc.). "
        "Use the tools when they help."
    )
    max_tool_iterations: int = 10


# ──────────────────────────────────────────────────────────────────────
# AnthropicAgent
# ──────────────────────────────────────────────────────────────────────


class AnthropicAgent:
    """Build the tool catalog from :mod:`srmech.amsc.tool_schema`,
    hand to the Anthropic SDK, run the tool_use message-loop, return
    the final assistant message + per-tool-call MPR attestation
    transcript.

    Construction is the gate that requires the ``anthropic`` SDK. If
    you only want to *introspect* the adapter (e.g. probe
    :data:`_HAVE_ANTHROPIC` or import :class:`AnthropicAgentConfig`)
    the import itself is always safe.

    Parameters
    ----------
    config
        Optional :class:`AnthropicAgentConfig`. Defaults applied
        per-field if omitted.

    Raises
    ------
    ImportError
        If the ``anthropic`` SDK is not installed.
    ValueError
        If neither ``config.api_key`` nor ``ANTHROPIC_API_KEY`` env
        is set.
    """

    def __init__(self, config: Optional[AnthropicAgentConfig] = None) -> None:
        if not _HAVE_ANTHROPIC:
            raise ImportError(
                "anthropic SDK not installed. "
                "Install with: pip install srmech[anthropic]"
            )
        self.config = config or AnthropicAgentConfig()
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set and no api_key in config"
            )
        # The ``anthropic`` module-level name is bound when
        # _HAVE_ANTHROPIC is True; the type: ignore lets mypy see this
        # path is only taken when the SDK loaded cleanly.
        self.client = anthropic.Anthropic(api_key=api_key)  # type: ignore[union-attr]
        # Build the catalog AFTER client construction so any catalog
        # failure surfaces with a useful Claude-side trace.
        self.tools, self._name_map = self._build_tool_catalog()

    # ──────────────────────────────────────────────────────────────
    # Catalog assembly
    # ──────────────────────────────────────────────────────────────

    def _build_tool_catalog(
        self,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Convert srmech ToolEntries -> Anthropic tool definitions.

        Returns
        -------
        (tools, name_map)
            ``tools`` is the list handed to ``messages.create``.
            ``name_map`` is the Anthropic-name -> srmech-name reverse
            lookup used by :meth:`_invoke_tool`.
        """
        from ..amsc.tool_schema import get_tool_schema
        from ..mcp._tools import tool_entry_to_mcp_def

        ts = get_tool_schema()
        tools: List[Dict[str, Any]] = []
        name_map: Dict[str, str] = {}
        for entry in ts.tools:
            if self.config.tool_filter is not None and not \
                    self.config.tool_filter(entry.name):
                continue
            mcp_def = tool_entry_to_mcp_def(entry)
            anthropic_name = _to_anthropic_name(entry.name)
            name_map[anthropic_name] = entry.name
            tools.append({
                "name": anthropic_name,
                "description": mcp_def["description"],
                # Anthropic uses ``input_schema`` (snake_case);
                # MCP uses ``inputSchema``. Same JSON-Schema body.
                "input_schema": mcp_def["inputSchema"],
            })
        return tools, name_map

    # ──────────────────────────────────────────────────────────────
    # Message loop
    # ──────────────────────────────────────────────────────────────

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """Execute the agent loop: prompt -> Claude -> tool_use ->
        invoke -> ... -> final message.

        Returns a dict with keys::

            {
              "final": <final-assistant content list or None>,
              "stop_reason": <Anthropic stop_reason str or
                              "max_iterations">,
              "tool_calls": [
                {"name": <anthropic-name>,
                 "srmech_name": <dotted srmech-name>,
                 "input": <dict>,
                 "result": <Python result>,
                 "attestation": <MPR attestation dict>,
                 "is_error": <bool>},
                ...
              ],
              "iterations": <int>,
            }

        The ``attestation`` block per tool call is the SAME MPR
        envelope shape MCP emits (re-uses
        :func:`srmech.mcp._server.build_attestation`).
        """
        assert isinstance(user_prompt, str) and user_prompt, \
            "run: user_prompt must be a non-empty string"

        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": user_prompt},
        ]
        tool_call_log: List[Dict[str, Any]] = []

        for iteration in range(self.config.max_tool_iterations):
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=self.config.system_prompt,
                tools=self.tools,
                messages=messages,
            )
            tool_uses = [
                b for b in response.content
                if getattr(b, "type", None) == "tool_use"
            ]
            if not tool_uses:
                # No tool_use blocks => final assistant message.
                return {
                    "final": response.content,
                    "stop_reason": response.stop_reason,
                    "tool_calls": tool_call_log,
                    "iterations": iteration + 1,
                }
            # Append the assistant turn before the tool_result turn so
            # the SDK accepts the multi-turn message list.
            messages.append({
                "role": "assistant",
                "content": response.content,
            })
            tool_results = []
            for tool_use in tool_uses:
                result, attestation, is_error = self._invoke_tool(
                    tool_use.name, dict(tool_use.input or {})
                )
                tool_call_log.append({
                    "name": tool_use.name,
                    "srmech_name": self._name_map.get(
                        tool_use.name, tool_use.name
                    ),
                    "input": dict(tool_use.input or {}),
                    "result": result,
                    "attestation": attestation,
                    "is_error": is_error,
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(result),
                    "is_error": is_error,
                })
            messages.append({"role": "user", "content": tool_results})

        # Hit the iteration cap with tool_use still outstanding.
        return {
            "final": None,
            "stop_reason": "max_iterations",
            "tool_calls": tool_call_log,
            "iterations": self.config.max_tool_iterations,
        }

    # ──────────────────────────────────────────────────────────────
    # Tool dispatch
    # ──────────────────────────────────────────────────────────────

    def _invoke_tool(
        self, anthropic_name: str, arguments: Dict[str, Any],
    ) -> Tuple[Any, Dict[str, Any], bool]:
        """Invoke one srmech tool by its Anthropic-compat name.

        Returns ``(result, attestation, is_error)``. On underlying
        exception, ``result`` is the error message text and
        ``is_error`` is True; the attestation block still covers the
        error text so the caller has a content-addressed record of
        the failure.
        """
        from ..mcp._server import build_attestation
        from ..mcp._tools import (
            MCPToolError,
            invoke_tool as mcp_invoke_tool,
            serialise_result,
        )

        # Reverse the synthesised Anthropic name -> srmech dotted
        # name. Fall through to the literal name if the reverse map
        # has no entry (defensive — e.g. a tool that came in via a
        # tool_filter change between catalog build and invoke).
        srmech_name = self._name_map.get(anthropic_name)
        if srmech_name is None:
            srmech_name = anthropic_name.replace("_", ".")

        try:
            raw = mcp_invoke_tool(srmech_name, arguments)
        except MCPToolError as exc:
            text = f"MCPToolError: {exc}"
            attestation = build_attestation(
                tool_name=srmech_name, result_text=text,
            )
            return text, attestation, True
        except Exception as exc:
            text = f"{type(exc).__name__}: {exc}"
            attestation = build_attestation(
                tool_name=srmech_name, result_text=text,
            )
            return text, attestation, True

        # Serialise the result the same way MCP does so the
        # attestation digest is invariant across adapters for the
        # same (tool, result) pair.
        result_text = serialise_result(raw)
        attestation = build_attestation(
            tool_name=srmech_name, result_text=result_text,
        )
        return raw, attestation, False


__all__ = [
    "ANTHROPIC_TOOL_NAME_MAX_LEN",
    "AnthropicAgent",
    "AnthropicAgentConfig",
    "_HAVE_ANTHROPIC",
    "_to_anthropic_name",
]
