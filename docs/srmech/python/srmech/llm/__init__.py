"""srmech.llm — direct LLM SDK adapters (secondary integration path).

For Claude Code users, the ``srmech.mcp`` adapter (v0.5.0rc6) is the
primary integration path — no API key needed, billing handled by the
Claude Code Max plan. This subpackage is the SECONDARY adapter for
users who script Claude (or other LLM SDKs) directly outside Claude
Code: FastAPI servers, Jupyter notebooks, CI pipelines, etc.

Same ~149 tool catalog as MCP (the
:mod:`srmech.amsc.tool_schema` ToolEntries); same MPR attestation
discipline per tool call (the ``build_attestation`` helper from
:mod:`srmech.mcp._server` is shared so the two adapters emit
byte-identical attestation envelopes).

v0.5.0rc9 ships the Anthropic SDK adapter (:mod:`.anthropic_agent`).
The ``anthropic`` Python SDK is an OPTIONAL dependency — install with
``pip install srmech[anthropic]`` to get it. Default install does NOT
add it.

Framework reading
-----------------
Class M (cross-class bind) at the LLM substrate-class boundary,
specialised to the direct-SDK substrate-class-instance instead of
MCP's subprocess-protocol substrate-class-instance. Both adapters
bind the SAME tool catalog (so the framework-reading is invariant
across transport); only the substrate-class-instance of the consumer
differs.
"""

from __future__ import annotations

# Eager re-export. The optional dep (``anthropic``) is wrapped in a
# try/except inside :mod:`.anthropic_agent` so ``import srmech.llm``
# is always cheap and never fails — even without the SDK installed.
# AnthropicAgent.__init__ is the gate that raises ImportError.
from . import anthropic_agent

__all__ = ["anthropic_agent"]
