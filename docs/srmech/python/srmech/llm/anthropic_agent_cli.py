"""``srmech-agent`` console-script entry point (v0.5.0rc9).

Drives :class:`srmech.llm.anthropic_agent.AnthropicAgent` from the
shell. Secondary to :mod:`srmech.mcp` (the Claude Code primary
path); useful for ad-hoc API-only runs.

Usage::

    srmech-agent run "summarise the cascade catalog"
    srmech-agent run "use sha256_bytes on these bytes: aabb" \\
        --model claude-sonnet-4-6 \\
        --max-tokens 2048 \\
        --filter "srmech.amsc.format.*"

Requires the ``anthropic`` optional dep
(``pip install srmech[anthropic]``) and the ``ANTHROPIC_API_KEY``
environment variable.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from ..version import __version__ as _srmech_version


def build_parser() -> argparse.ArgumentParser:
    """Build the ``srmech-agent`` argparse tree."""
    parser = argparse.ArgumentParser(
        prog="srmech-agent",
        description=(
            "Anthropic SDK agent adapter for srmech. Secondary to "
            "srmech-mcp (primary for Claude Code users). v0.5.0rc9."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"srmech-agent {_srmech_version}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_run = subparsers.add_parser(
        "run",
        help="Run one prompt through Claude with srmech tools available.",
    )
    p_run.add_argument(
        "prompt",
        help="The user prompt to send to Claude.",
    )
    p_run.add_argument(
        "--model",
        default=None,
        help=(
            "Claude model identifier. Default: claude-sonnet-4-6 "
            "(per AnthropicAgentConfig)."
        ),
    )
    p_run.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Per-call generation cap. Default: 4096.",
    )
    p_run.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help=(
            "Cap on tool_use round-trips per run. Default: 10. The "
            "loop returns with stop_reason='max_iterations' if "
            "exceeded."
        ),
    )
    p_run.add_argument(
        "--filter",
        dest="name_filter",
        default=None,
        metavar="GLOB",
        help=(
            "Only expose tools whose srmech-name matches GLOB "
            "(fnmatch-style; e.g. 'srmech.amsc.cascade.*'). Default: "
            "expose everything (~149 tools)."
        ),
    )
    p_run.add_argument(
        "--system",
        dest="system_prompt",
        default=None,
        help="Override the default system prompt.",
    )
    return parser


def _render_run_result(result: dict) -> str:
    """Render the AnthropicAgent.run() return dict for CLI output.

    The ``final`` field contains Anthropic SDK content blocks (not
    JSON-serialisable directly); extract the .text from each
    ``text``-type block and concatenate. The tool_calls log is
    serialised verbatim (with the attestation block intact) so a
    consumer can re-verify the response_sha256 line by line.
    """
    final_blocks = result.get("final") or []
    final_text_parts: List[str] = []
    for b in final_blocks:
        # SDK objects expose .type / .text as attrs; fall back to
        # mapping access for the mocked dict cases.
        btype = getattr(b, "type", None) or (b.get("type") if isinstance(b, dict) else None)
        if btype == "text":
            text = getattr(b, "text", None) or (b.get("text") if isinstance(b, dict) else "")
            if text:
                final_text_parts.append(text)
    final_text = "\n".join(final_text_parts)

    transcript = {
        "stop_reason": result.get("stop_reason"),
        "iterations": result.get("iterations"),
        "tool_calls": [
            {
                "name": tc.get("name"),
                "srmech_name": tc.get("srmech_name"),
                "input": tc.get("input"),
                # Result may be a non-JSON Python value; coerce.
                "result": _safe_for_json(tc.get("result")),
                "attestation": tc.get("attestation"),
                "is_error": tc.get("is_error"),
            }
            for tc in result.get("tool_calls") or []
        ],
    }
    return (
        f"{final_text}\n"
        f"--- transcript ---\n"
        f"{json.dumps(transcript, indent=2, sort_keys=False)}\n"
    )


def _safe_for_json(value):
    """Best-effort JSON-coercion for tool results in the CLI render."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


def main(argv: Optional[List[str]] = None) -> int:
    """``srmech-agent`` console-script entry."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        # Lazy-import the agent so ``srmech-agent --help`` works even
        # without the anthropic SDK installed.
        from .anthropic_agent import (
            AnthropicAgent,
            AnthropicAgentConfig,
        )
        from ..mcp._tools import compile_filter

        cfg_kwargs = {}
        if args.model is not None:
            cfg_kwargs["model"] = args.model
        if args.max_tokens is not None:
            cfg_kwargs["max_tokens"] = args.max_tokens
        if args.max_iterations is not None:
            cfg_kwargs["max_tool_iterations"] = args.max_iterations
        if args.system_prompt is not None:
            cfg_kwargs["system_prompt"] = args.system_prompt
        name_filter = compile_filter(args.name_filter)
        if name_filter is not None:
            cfg_kwargs["tool_filter"] = name_filter

        try:
            agent = AnthropicAgent(AnthropicAgentConfig(**cfg_kwargs))
        except ImportError as exc:
            print(f"srmech-agent: {exc}", file=sys.stderr)
            return 2
        except ValueError as exc:
            print(f"srmech-agent: {exc}", file=sys.stderr)
            return 2
        result = agent.run(args.prompt)
        sys.stdout.write(_render_run_result(result))
        return 0

    parser.error(f"unknown command {args.command!r}")
    return 2  # unreachable


if __name__ == "__main__":  # pragma: no cover — exercised via subprocess
    sys.exit(main())
