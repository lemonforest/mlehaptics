"""Tests for srmech.llm.anthropic_agent — Anthropic SDK secondary
adapter (v0.5.0rc9).

These tests NEVER make real Anthropic API calls; they use a mocked
``anthropic.Anthropic`` client injected via ``unittest.mock`` so the
suite runs without ``ANTHROPIC_API_KEY`` and without the
``anthropic`` SDK actually installed.

The MOCK_SDK fixture installs a fake ``anthropic`` module + flips
``_HAVE_ANTHROPIC`` to True so :class:`AnthropicAgent` instantiates
cleanly. The "no SDK" import-error path is tested by saving + clearing
the flag (and the fake module) for one specific test.
"""

from __future__ import annotations

import json
import os
import sys
import types
from typing import Any, Dict, List, Optional
from unittest import mock

import pytest

# Force bus tools to register so the catalog size matches what the
# MCP adapter sees in production. Same pattern as test_mcp.py.
import srmech.bus  # noqa: F401 — import side-effect

from srmech.amsc.tool_schema import get_tool_schema
from srmech.llm import anthropic_agent as aa
from srmech.llm.anthropic_agent import (
    ANTHROPIC_TOOL_NAME_MAX_LEN,
    AnthropicAgent,
    AnthropicAgentConfig,
    _to_anthropic_name,
)


# ──────────────────────────────────────────────────────────────────────
# Mock SDK plumbing
# ──────────────────────────────────────────────────────────────────────


class _MockTextBlock:
    """Mock of the Anthropic SDK's ``TextBlock``."""
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _MockToolUseBlock:
    """Mock of the Anthropic SDK's ``ToolUseBlock``."""
    type = "tool_use"

    def __init__(self, *, id: str, name: str, input: Dict[str, Any]) -> None:
        self.id = id
        self.name = name
        self.input = input


class _MockResponse:
    """Mock of the Anthropic SDK's ``Message`` return type."""

    def __init__(
        self,
        *,
        content: List[Any],
        stop_reason: str = "end_turn",
    ) -> None:
        self.content = content
        self.stop_reason = stop_reason


class _MockMessages:
    """Mock of the Anthropic SDK's ``client.messages`` namespace."""

    def __init__(self, responses: List[_MockResponse]) -> None:
        self._responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _MockResponse:
        self.calls.append(kwargs)
        if not self._responses:
            raise RuntimeError(
                "mock client ran out of canned responses"
            )
        return self._responses.pop(0)


class _MockAnthropicClient:
    """Mock of ``anthropic.Anthropic`` itself."""

    def __init__(self, *, api_key: str, responses: List[_MockResponse]) -> None:
        self.api_key = api_key
        self.messages = _MockMessages(responses)


@pytest.fixture
def mock_sdk(monkeypatch: pytest.MonkeyPatch):
    """Install a fake ``anthropic`` module and flip
    ``_HAVE_ANTHROPIC`` to True so AnthropicAgent instantiates.

    Yields a callable ``client_factory(responses)`` that constructs a
    :class:`_MockAnthropicClient` with the supplied canned responses
    list. The factory is wired into ``anthropic.Anthropic`` so
    AnthropicAgent's own ``anthropic.Anthropic(api_key=...)`` call
    routes through it.
    """
    fake = types.SimpleNamespace()
    captured: Dict[str, Any] = {"client": None, "responses": []}

    def Anthropic_ctor(*, api_key: str) -> _MockAnthropicClient:
        client = _MockAnthropicClient(
            api_key=api_key, responses=captured["responses"],
        )
        captured["client"] = client
        return client

    fake.Anthropic = Anthropic_ctor
    monkeypatch.setattr(aa, "anthropic", fake)
    monkeypatch.setattr(aa, "_HAVE_ANTHROPIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake")

    def factory(responses: List[_MockResponse]) -> _MockAnthropicClient:
        captured["responses"] = list(responses)
        return captured  # so test can inspect after agent.run()

    yield factory


# ──────────────────────────────────────────────────────────────────────
# Module-level: ImportError without anthropic SDK
# ──────────────────────────────────────────────────────────────────────


def test_module_loads_without_anthropic_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Importing :mod:`srmech.llm.anthropic_agent` is always safe
    even when the optional SDK is absent."""
    # The module imports cleanly regardless; this asserts the runtime
    # surface stays well-defined.
    assert hasattr(aa, "AnthropicAgent")
    assert hasattr(aa, "AnthropicAgentConfig")
    assert hasattr(aa, "_HAVE_ANTHROPIC")


def test_agent_init_raises_importerror_without_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """:class:`AnthropicAgent` raises :class:`ImportError` with a
    useful hint when the SDK is not installed."""
    monkeypatch.setattr(aa, "_HAVE_ANTHROPIC", False)
    with pytest.raises(ImportError) as excinfo:
        AnthropicAgent()
    assert "pip install srmech[anthropic]" in str(excinfo.value)


def test_agent_init_raises_valueerror_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the SDK loaded but no API key is reachable, init
    raises :class:`ValueError`."""
    fake = types.SimpleNamespace(Anthropic=lambda *, api_key: None)
    monkeypatch.setattr(aa, "anthropic", fake)
    monkeypatch.setattr(aa, "_HAVE_ANTHROPIC", True)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError) as excinfo:
        AnthropicAgent()
    assert "ANTHROPIC_API_KEY" in str(excinfo.value)


# ──────────────────────────────────────────────────────────────────────
# Name-mapping
# ──────────────────────────────────────────────────────────────────────


def test_name_mapping_dot_to_underscore() -> None:
    """`.` characters in a srmech tool name are mapped to `_` so the
    name passes Anthropic's grammar."""
    assert _to_anthropic_name("srmech.amsc.format.sha256_bytes") == \
        "srmech_amsc_format_sha256_bytes"


def test_name_mapping_under_64_char_ceiling() -> None:
    """Every registered srmech tool name maps to a string within
    Anthropic's 64-char ceiling."""
    schema = get_tool_schema()
    for entry in schema.tools:
        mapped = _to_anthropic_name(entry.name)
        assert len(mapped) <= ANTHROPIC_TOOL_NAME_MAX_LEN, (
            f"srmech tool {entry.name!r} maps to {mapped!r} which "
            f"exceeds Anthropic's 64-char ceiling"
        )


# ──────────────────────────────────────────────────────────────────────
# Catalog conversion
# ──────────────────────────────────────────────────────────────────────


def test_tool_catalog_includes_every_registered_tool(mock_sdk) -> None:
    """The catalog handed to Claude has one entry per registered
    ToolEntry; the count matches the MCP adapter."""
    mock_sdk([])  # no responses needed; we only construct the agent
    agent = AnthropicAgent()
    expected = len(get_tool_schema().tools)
    assert len(agent.tools) == expected
    assert expected > 50, (
        f"expected ~149 registered tools; got {expected}"
    )


def test_tool_catalog_entries_have_anthropic_shape(mock_sdk) -> None:
    """Each catalog entry has Anthropic-required fields: ``name``,
    ``description``, ``input_schema``."""
    mock_sdk([])
    agent = AnthropicAgent()
    for tool in agent.tools:
        assert "name" in tool and isinstance(tool["name"], str)
        assert "description" in tool and isinstance(tool["description"], str)
        assert "input_schema" in tool
        sch = tool["input_schema"]
        assert sch["type"] == "object"
        assert "properties" in sch
        assert "required" in sch


def test_tool_filter_narrows_catalog(mock_sdk) -> None:
    """``tool_filter`` removes non-matching entries."""
    mock_sdk([])
    cfg = AnthropicAgentConfig(
        tool_filter=lambda name: name.startswith("srmech.amsc.format."),
    )
    agent = AnthropicAgent(cfg)
    # At least one match, far fewer than the full catalog.
    full = len(get_tool_schema().tools)
    assert 0 < len(agent.tools) < full
    for tool in agent.tools:
        # The reverse map's srmech name must satisfy the filter.
        srmech_name = agent._name_map[tool["name"]]
        assert srmech_name.startswith("srmech.amsc.format.")


def test_reverse_name_map_round_trips(mock_sdk) -> None:
    """Every Anthropic-name in the catalog reverse-maps to a real
    srmech-name in the registry."""
    mock_sdk([])
    agent = AnthropicAgent()
    schema = get_tool_schema()
    valid_names = {e.name for e in schema.tools}
    for anthropic_name, srmech_name in agent._name_map.items():
        assert srmech_name in valid_names
        assert _to_anthropic_name(srmech_name) == anthropic_name


# ──────────────────────────────────────────────────────────────────────
# Message-loop: no tool_use
# ──────────────────────────────────────────────────────────────────────


def test_run_with_no_tool_use_returns_final(mock_sdk) -> None:
    """When Claude replies with no tool_use blocks, ``run`` returns
    the final assistant content immediately after one iteration."""
    handle = mock_sdk([
        _MockResponse(
            content=[_MockTextBlock("Hello from Claude.")],
            stop_reason="end_turn",
        ),
    ])
    agent = AnthropicAgent()
    out = agent.run("Hi")
    assert out["iterations"] == 1
    assert out["stop_reason"] == "end_turn"
    assert out["tool_calls"] == []
    assert out["final"][0].text == "Hello from Claude."
    # And the SDK was called once with the catalog attached.
    calls = handle["client"].messages.calls
    assert len(calls) == 1
    assert calls[0]["tools"] is agent.tools


# ──────────────────────────────────────────────────────────────────────
# Message-loop: one tool_use round-trip
# ──────────────────────────────────────────────────────────────────────


def test_run_with_one_tool_use_dispatches_then_finishes(mock_sdk) -> None:
    """One tool_use round-trip: Claude asks for sha256, the agent
    invokes it, second turn returns a final text."""
    tool_use = _MockToolUseBlock(
        id="toolu_1",
        # The Anthropic-grammar name for sha256_bytes.
        name="srmech_amsc_format_sha256_bytes",
        # rc14: bytes ride as base64 over the wire (was hex).
        input={"data": "3q2+7w=="},  # base64 of b"\xde\xad\xbe\xef"
    )
    handle = mock_sdk([
        _MockResponse(
            content=[tool_use],
            stop_reason="tool_use",
        ),
        _MockResponse(
            content=[_MockTextBlock("The SHA-256 is computed.")],
            stop_reason="end_turn",
        ),
    ])
    agent = AnthropicAgent()
    out = agent.run("hash deadbeef please")
    assert out["iterations"] == 2
    assert out["stop_reason"] == "end_turn"
    assert len(out["tool_calls"]) == 1
    tc = out["tool_calls"][0]
    assert tc["name"] == "srmech_amsc_format_sha256_bytes"
    assert tc["srmech_name"] == "srmech.amsc.format.sha256_bytes"
    assert tc["is_error"] is False
    # The result of sha256_bytes on the base64-decoded bytes is a hex
    # digest; we don't pin the value, just that it's a 64-char hex.
    assert isinstance(tc["result"], str) and len(tc["result"]) == 64
    # Attestation block is the MPR envelope shape.
    att = tc["attestation"]
    assert att["mpr_version"] == "1.0"
    assert att["tool_name"] == "srmech.amsc.format.sha256_bytes"
    assert "response_sha256" in att and len(att["response_sha256"]) == 64
    # SDK was called twice; second call carried both turns of history.
    calls = handle["client"].messages.calls
    assert len(calls) == 2
    assert len(calls[1]["messages"]) == 3  # user, assistant, user(tool_result)


# ──────────────────────────────────────────────────────────────────────
# Message-loop: multiple tool_uses in one turn
# ──────────────────────────────────────────────────────────────────────


def test_run_with_multiple_tool_uses_invokes_each(mock_sdk) -> None:
    """Two tool_use blocks in one assistant turn: both get invoked,
    both appear in the log, both produce attestation blocks."""
    handle = mock_sdk([
        _MockResponse(
            content=[
                _MockToolUseBlock(
                    id="toolu_1",
                    name="srmech_amsc_format_sha256_bytes",
                    input={"data": "qg=="},  # base64 of b"\xaa"
                ),
                _MockToolUseBlock(
                    id="toolu_2",
                    name="srmech_amsc_format_sha256_bytes",
                    input={"data": "uw=="},  # base64 of b"\xbb"
                ),
            ],
            stop_reason="tool_use",
        ),
        _MockResponse(
            content=[_MockTextBlock("Both hashes are computed.")],
            stop_reason="end_turn",
        ),
    ])
    agent = AnthropicAgent()
    out = agent.run("hash aa and bb")
    assert out["iterations"] == 2
    assert len(out["tool_calls"]) == 2
    # Distinct results since inputs differ.
    assert out["tool_calls"][0]["result"] != out["tool_calls"][1]["result"]
    # tool_result block per tool_use was packed in the user turn.
    last_user = handle["client"].messages.calls[1]["messages"][-1]
    assert last_user["role"] == "user"
    assert len(last_user["content"]) == 2
    assert {b["tool_use_id"] for b in last_user["content"]} == \
        {"toolu_1", "toolu_2"}


# ──────────────────────────────────────────────────────────────────────
# Message-loop: max iterations safety cap
# ──────────────────────────────────────────────────────────────────────


def test_max_iterations_cap_fires(mock_sdk) -> None:
    """If Claude keeps asking for tools past the cap, the loop
    returns with ``stop_reason='max_iterations'`` and ``final=None``."""
    # 3 canned responses, all tool_use; cap at 3.
    looped = [
        _MockResponse(
            content=[_MockToolUseBlock(
                id=f"toolu_{i}",
                name="srmech_amsc_format_sha256_bytes",
                input={"data": "qg=="},  # base64 of b"\xaa"
            )],
            stop_reason="tool_use",
        )
        for i in range(3)
    ]
    mock_sdk(looped)
    cfg = AnthropicAgentConfig(max_tool_iterations=3)
    agent = AnthropicAgent(cfg)
    out = agent.run("loop please")
    assert out["stop_reason"] == "max_iterations"
    assert out["final"] is None
    assert out["iterations"] == 3
    assert len(out["tool_calls"]) == 3


# ──────────────────────────────────────────────────────────────────────
# Tool-error handling
# ──────────────────────────────────────────────────────────────────────


def test_tool_error_is_captured_with_attestation(mock_sdk) -> None:
    """If a tool invocation raises, the loop continues with the
    error text + an attestation covering the error text + is_error
    set on both the tool_result and the transcript entry."""
    bad_tool = _MockToolUseBlock(
        id="toolu_bad",
        # Unknown tool name -> MCPToolError on dispatch.
        name="not_a_real_tool",
        input={},
    )
    handle = mock_sdk([
        _MockResponse(
            content=[bad_tool],
            stop_reason="tool_use",
        ),
        _MockResponse(
            content=[_MockTextBlock("I'll try something else.")],
            stop_reason="end_turn",
        ),
    ])
    agent = AnthropicAgent()
    out = agent.run("try a bad tool")
    assert out["iterations"] == 2
    tc = out["tool_calls"][0]
    assert tc["is_error"] is True
    assert isinstance(tc["result"], str)
    assert "MCPToolError" in tc["result"] or "not a real" in tc["result"].lower() \
        or "no registered tool" in tc["result"].lower()
    assert tc["attestation"]["mpr_version"] == "1.0"
    # And the tool_result block carried is_error=True back to Claude.
    last_user = handle["client"].messages.calls[1]["messages"][-1]
    assert last_user["content"][0]["is_error"] is True


# ──────────────────────────────────────────────────────────────────────
# API-key resolution precedence
# ──────────────────────────────────────────────────────────────────────


def test_explicit_api_key_takes_precedence_over_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit ``config.api_key`` overrides the env var."""
    fake_calls = {}

    def Anthropic_ctor(*, api_key: str):
        fake_calls["api_key"] = api_key
        return _MockAnthropicClient(api_key=api_key, responses=[])

    fake = types.SimpleNamespace(Anthropic=Anthropic_ctor)
    monkeypatch.setattr(aa, "anthropic", fake)
    monkeypatch.setattr(aa, "_HAVE_ANTHROPIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
    cfg = AnthropicAgentConfig(api_key="sk-explicit")
    AnthropicAgent(cfg)
    assert fake_calls["api_key"] == "sk-explicit"


def test_env_api_key_used_when_no_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``config.api_key`` is None, ``ANTHROPIC_API_KEY`` env is
    used."""
    fake_calls = {}

    def Anthropic_ctor(*, api_key: str):
        fake_calls["api_key"] = api_key
        return _MockAnthropicClient(api_key=api_key, responses=[])

    fake = types.SimpleNamespace(Anthropic=Anthropic_ctor)
    monkeypatch.setattr(aa, "anthropic", fake)
    monkeypatch.setattr(aa, "_HAVE_ANTHROPIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
    AnthropicAgent()
    assert fake_calls["api_key"] == "sk-from-env"


# ──────────────────────────────────────────────────────────────────────
# Cross-adapter MPR-envelope invariance
# ──────────────────────────────────────────────────────────────────────


def test_attestation_matches_mcp_adapter_for_same_call(mock_sdk) -> None:
    """The MPR attestation block emitted by the LLM adapter is the
    same shape MCP emits (re-uses build_attestation). The
    response_sha256 is computed over the same canonical form so the
    two adapters are mutually verifiable for the same (tool, result)
    pair."""
    from srmech.mcp._server import build_attestation
    from srmech.mcp._tools import invoke_tool, serialise_result

    # Drive one tool_use round-trip via the agent.
    handle = mock_sdk([
        _MockResponse(
            content=[_MockToolUseBlock(
                id="toolu_x",
                name="srmech_amsc_format_sha256_bytes",
                input={"data": "3q2+7w=="},  # base64 of b"\xde\xad\xbe\xef"
            )],
            stop_reason="tool_use",
        ),
        _MockResponse(
            content=[_MockTextBlock("done")],
            stop_reason="end_turn",
        ),
    ])
    agent = AnthropicAgent()
    out = agent.run("hash deadbeef")
    agent_att = out["tool_calls"][0]["attestation"]
    # Independently compute the MCP attestation shape for the same
    # call. We pin the result_text to the same serialise_result(...)
    # the agent used and compare structural keys; the timestamp
    # naturally drifts between the two calls so we don't pin
    # response_sha256 equality, only structure.
    raw = invoke_tool("srmech.amsc.format.sha256_bytes", {"data": "3q2+7w=="})
    mcp_att = build_attestation(
        tool_name="srmech.amsc.format.sha256_bytes",
        result_text=serialise_result(raw),
    )
    assert set(agent_att.keys()) == set(mcp_att.keys())
    assert agent_att["mpr_version"] == mcp_att["mpr_version"]
    assert agent_att["tool_name"] == mcp_att["tool_name"]
    assert agent_att["parser_version"] == mcp_att["parser_version"]
    # response_sha256 hex strings are both 64 chars.
    assert len(agent_att["response_sha256"]) == 64


# ──────────────────────────────────────────────────────────────────────
# CLI: --help works without anthropic SDK installed
# ──────────────────────────────────────────────────────────────────────


def test_cli_help_works_without_sdk(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """``srmech-agent --help`` exits 0 even when the SDK is absent
    (lazy-import of the agent class makes the help text reachable
    without the optional dep)."""
    from srmech.llm import anthropic_agent_cli

    monkeypatch.setattr(aa, "_HAVE_ANTHROPIC", False)
    with pytest.raises(SystemExit) as excinfo:
        anthropic_agent_cli.main(["--help"])
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "srmech-agent" in captured.out


def test_cli_run_reports_importerror_cleanly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """``srmech-agent run`` without the SDK exits 2 with a clean
    error on stderr (not a Python traceback)."""
    from srmech.llm import anthropic_agent_cli

    monkeypatch.setattr(aa, "_HAVE_ANTHROPIC", False)
    rc = anthropic_agent_cli.main(["run", "hello"])
    assert rc == 2
    captured = capsys.readouterr()
    assert "pip install srmech[anthropic]" in captured.err


def test_cli_run_dispatches_to_agent(
    monkeypatch: pytest.MonkeyPatch,
    mock_sdk,
    capsys: pytest.CaptureFixture,
) -> None:
    """``srmech-agent run "prompt"`` constructs the agent, runs the
    prompt through the mocked SDK, and prints the final text + the
    JSON transcript on stdout."""
    from srmech.llm import anthropic_agent_cli

    mock_sdk([
        _MockResponse(
            content=[_MockTextBlock("Mocked reply.")],
            stop_reason="end_turn",
        ),
    ])
    rc = anthropic_agent_cli.main(["run", "hi there"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Mocked reply." in captured.out
    assert "transcript" in captured.out


def test_cli_run_applies_filter_and_options(
    monkeypatch: pytest.MonkeyPatch,
    mock_sdk,
    capsys: pytest.CaptureFixture,
) -> None:
    """``--filter`` narrows the catalog; ``--model`` / ``--max-tokens``
    flow through to the SDK call."""
    from srmech.llm import anthropic_agent_cli

    handle = mock_sdk([
        _MockResponse(
            content=[_MockTextBlock("Filtered.")],
            stop_reason="end_turn",
        ),
    ])
    rc = anthropic_agent_cli.main([
        "run",
        "do stuff",
        "--filter", "srmech.amsc.format.*",
        "--model", "claude-haiku-4-6",
        "--max-tokens", "1024",
        "--max-iterations", "5",
    ])
    assert rc == 0
    call = handle["client"].messages.calls[0]
    assert call["model"] == "claude-haiku-4-6"
    assert call["max_tokens"] == 1024
    # tools list is narrowed.
    assert 0 < len(call["tools"]) < len(get_tool_schema().tools)
    for tool in call["tools"]:
        assert tool["name"].startswith("srmech_amsc_format_")
