"""LLM tool-schema export for the bridge surface.

Introspects ``ephemerides_spectral.bridge`` and emits machine-readable
tool descriptions in the standard formats LLM tool-use clients expect
(Anthropic Claude, OpenAI function-calling, MCP / Model Context Protocol,
or plain JSON Schema).

The bridge surface (~240 public functions across 40+ ships) is the
single source of truth: each tool's name, description, parameter types,
and required-vs-optional status are derived from Python's
:mod:`inspect` module reading function signatures + docstrings. No
hand-maintained list — adding a new bridge function automatically
extends every emitted schema.

Bridge surfaces:

* :func:`get_tool_schema(format="anthropic", filter_prefix=None)` —
  Returns the full schema for the requested format. Optionally
  filter by name prefix (e.g. ``"get_cmb_"`` selects only the
  cosmology-instrument tools).
* :func:`list_tool_names(filter_prefix=None)` — Returns just the
  tool names, sorted, useful for inventory + tab-completion.
* :func:`get_one_tool_schema(name, format="anthropic")` — Returns
  a single tool's schema. Raises if name is unknown.

Supported formats:

* ``anthropic`` (default) — Claude tool-use spec: ``{name,
  description, input_schema: {type: "object", properties, required}}``.
* ``openai`` — OpenAI function-calling: ``{type: "function",
  function: {name, description, parameters}}``.
* ``mcp`` — Anthropic Model Context Protocol tools/list response:
  ``{name, description, inputSchema}`` (camelCase per the spec).
* ``jsonschema`` — Plain JSON Schema per tool: ``{name, description,
  parameters}`` (no LLM-vendor wrapping).

Type-hint mapping:

* ``int`` → ``{"type": "integer"}``
* ``float`` → ``{"type": "number"}``
* ``str`` → ``{"type": "string"}``
* ``bool`` → ``{"type": "boolean"}``
* ``Optional[X]`` → ``X`` with parameter marked optional (NOT in required list)
* ``List[X]`` / ``list[X]`` → ``{"type": "array", "items": X}``
* ``Dict[X, Y]`` / ``dict[X, Y]`` → ``{"type": "object"}`` (lossy; LLMs
  rarely use Dict-typed parameters anyway)
* ``Any`` / unrecognised → ``{}`` (no constraint)

The first line of each function's docstring becomes the tool description.
Functions without docstrings get a placeholder; this is a soft-warning
condition the ratchet tests can flag.

Reference: research notebook §0.0 The Mathematical Provenance Method —
the bridge surface IS the surface other systems consume; making it
self-describing to LLM tool-use clients is the natural completion of
the "machine-readable everywhere" discipline.
"""

from __future__ import annotations

import inspect
import re
import sys
import types
import typing
from typing import Any, Callable, Dict, List, Optional, Union


SUPPORTED_FORMATS = frozenset(["anthropic", "openai", "mcp", "jsonschema"])

# Bridge functions that should NOT be exposed as LLM tools.
#
#  - Functions starting with `_` are skipped automatically.
#  - These additional names cover decorators, internal helpers that
#    happen to be public, etc. Keep this list tight; default
#    inclusion + this excluded-set is more discoverable than the
#    inverse.
_EXCLUDED_NAMES: frozenset = frozenset([
    # Conventional non-tool exports that argparse / type-system noise
    # would otherwise surface. None known at v1 — placeholder for
    # future additions.
])


def _is_public_bridge_callable(name: str, value: Any, module_name: str) -> bool:
    """A name is a public bridge tool iff:

    1. Doesn't start with ``_``.
    2. Is callable.
    3. Defined in the bridge module itself (not re-imported).
    4. Not in the excluded set.
    """
    if name.startswith("_"):
        return False
    if not callable(value):
        return False
    if name in _EXCLUDED_NAMES:
        return False
    # Filter to functions defined in the bridge module to skip transitive
    # imports (typing.Any, Dict, dataclass decorators, etc.).
    if getattr(value, "__module__", None) != module_name:
        return False
    # Filter to actual functions (not classes, not modules).
    if not isinstance(value, (types.FunctionType, types.BuiltinFunctionType)):
        return False
    return True


def _annotation_to_json_schema(annotation: Any) -> Dict[str, Any]:
    """Map a Python type annotation to a JSON Schema fragment.

    Handles ``int``, ``float``, ``str``, ``bool``, ``list[X]``,
    ``dict[X, Y]``, ``Optional[X]`` (= ``Union[X, None]``),
    ``Union[X, Y, ...]`` (lossy — picks first non-None branch).
    Unknown / ``Any`` falls through to ``{}`` (no constraint).

    Also handles string-form annotations (PEP 563) by stripping
    common wrappers — ``"int"`` → integer, ``"Optional[int]"`` →
    integer with optional flag. Used because some bridge modules
    use ``from __future__ import annotations`` and so signatures
    expose strings instead of resolved types.
    """
    if annotation is inspect.Signature.empty:
        return {}

    # Forward-reference / string annotation handling
    if isinstance(annotation, str):
        return _annotation_string_to_json_schema(annotation)

    # None / NoneType
    if annotation is None or annotation is type(None):
        return {"type": "null"}

    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is Union or origin is types.UnionType:
        # Optional[X] = Union[X, None]
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _annotation_to_json_schema(non_none[0])
        # Multi-branch Union: lossy, take first branch
        return _annotation_to_json_schema(non_none[0]) if non_none else {}

    if origin in (list, typing.List):
        if args:
            return {"type": "array", "items": _annotation_to_json_schema(args[0])}
        return {"type": "array"}

    if origin in (dict, typing.Dict):
        # JSON Schema doesn't natively express Dict[X, Y]; LLM tool-use
        # APIs rarely use dict parameters. Mark as generic object.
        return {"type": "object"}

    if origin in (tuple, typing.Tuple):
        return {"type": "array"}

    # Plain types
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}
    if annotation is str:
        return {"type": "string"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is list:
        return {"type": "array"}
    if annotation is dict:
        return {"type": "object"}

    # Fallback: unknown / Any
    return {}


_STRING_ANNOTATION_PATTERNS = {
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "str": {"type": "string"},
    "bool": {"type": "boolean"},
    "list": {"type": "array"},
    "dict": {"type": "object"},
    "Any": {},
    "None": {"type": "null"},
}


def _annotation_string_to_json_schema(annotation: str) -> Dict[str, Any]:
    """Parse a string-form annotation. Best-effort; falls back to {}."""
    a = annotation.strip()

    # Strip Optional[...] wrapper (treat as the inner type — the
    # required-vs-optional status is carried separately in the schema).
    m = re.match(r"^Optional\[(.+)\]$", a)
    if m:
        return _annotation_string_to_json_schema(m.group(1))

    # Strip Union[...] — take first branch (lossy)
    m = re.match(r"^Union\[(.+)\]$", a)
    if m:
        first = m.group(1).split(",")[0].strip()
        if first in ("None", "type(None)"):
            # Union[None, X, ...] — take X
            parts = [p.strip() for p in m.group(1).split(",")]
            non_none = [p for p in parts if p not in ("None", "type(None)")]
            if non_none:
                return _annotation_string_to_json_schema(non_none[0])
        return _annotation_string_to_json_schema(first)

    # List[X] / list[X]
    m = re.match(r"^(?:List|list)\[(.+)\]$", a)
    if m:
        return {"type": "array", "items": _annotation_string_to_json_schema(m.group(1))}

    # Dict[X, Y] / dict[X, Y]
    if re.match(r"^(?:Dict|dict)\[.+\]$", a):
        return {"type": "object"}

    # Tuple[X, ...]
    if re.match(r"^(?:Tuple|tuple)\[.+\]$", a):
        return {"type": "array"}

    return _STRING_ANNOTATION_PATTERNS.get(a, {})


def _first_doc_line(fn: Callable[..., Any]) -> str:
    """First non-empty line of the function's docstring."""
    doc = inspect.getdoc(fn) or ""
    for line in doc.splitlines():
        line = line.strip()
        if line:
            return line
    return f"(no description; function `{fn.__name__}` has no docstring)"


def _parameter_schema(param: inspect.Parameter) -> Dict[str, Any]:
    """JSON Schema fragment for one function parameter."""
    schema = _annotation_to_json_schema(param.annotation)
    return schema


def _function_to_tool_dict(name: str, fn: Callable[..., Any]) -> Dict[str, Any]:
    """Build the format-agnostic tool dict (name, description, parameters).

    Uses the explicit ``name`` argument (the bridge namespace binding)
    rather than ``fn.__name__`` because some bridge functions are
    factory-generated with shared inner-closure names. Each format
    wrapper (anthropic / openai / mcp / jsonschema) reshapes this
    same dict differently.
    """
    sig = inspect.signature(fn)
    properties: Dict[str, Dict[str, Any]] = {}
    required: List[str] = []

    for pname, param in sig.parameters.items():
        # Skip *args / **kwargs — JSON Schema doesn't model them, and
        # bridge functions don't use them anyway.
        if param.kind in (inspect.Parameter.VAR_POSITIONAL,
                           inspect.Parameter.VAR_KEYWORD):
            continue
        properties[pname] = _parameter_schema(param)
        if param.default is inspect.Parameter.empty:
            required.append(pname)

    return {
        "name": name,
        "description": _first_doc_line(fn),
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def _wrap_anthropic(tool: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": tool["name"],
        "description": tool["description"],
        "input_schema": tool["parameters"],
    }


def _wrap_openai(tool: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }


def _wrap_mcp(tool: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": tool["name"],
        "description": tool["description"],
        "inputSchema": tool["parameters"],
    }


def _wrap_jsonschema(tool: Dict[str, Any]) -> Dict[str, Any]:
    return tool


_WRAPPERS = {
    "anthropic": _wrap_anthropic,
    "openai": _wrap_openai,
    "mcp": _wrap_mcp,
    "jsonschema": _wrap_jsonschema,
}


def _enumerate_bridge_tools(
    filter_prefix: Optional[str] = None,
) -> List[tuple]:
    """Return all public bridge tools as (namespace_name, callable) pairs.

    Uses the bridge module's NAMESPACE binding name (not ``fn.__name__``)
    as the tool name. Necessary because some bridge functions are
    factory-generated and share an inner ``_impl`` closure — the public
    contract is the namespace binding (e.g., ``jd_to_sol_jupiter_adrastea_time``),
    not the closure's intrinsic ``__name__``.

    Resolved at call time so adding a new bridge function automatically
    extends every emitted schema. Lazy import avoids circular dependency
    (bridge.py imports tool_schema; tool_schema must not import bridge
    at module load).
    """
    from ephemerides_spectral import bridge as _bridge

    bridge_module_name = _bridge.__name__
    tools = []
    for name in sorted(dir(_bridge)):
        value = getattr(_bridge, name)
        if not _is_public_bridge_callable(name, value, bridge_module_name):
            continue
        if filter_prefix is not None and not name.startswith(filter_prefix):
            continue
        tools.append((name, value))
    return tools


def list_tool_names(filter_prefix: Optional[str] = None) -> Dict[str, Any]:
    """List all bridge tool names, optionally filtered by prefix.

    Returns ``{"ok": True, "n_tools": N, "tool_names": [...], "filter_prefix": ...}``.
    """
    tools = _enumerate_bridge_tools(filter_prefix=filter_prefix)
    return {
        "ok": True,
        "filter_prefix": filter_prefix,
        "n_tools": len(tools),
        "tool_names": [name for name, _fn in tools],
    }


def get_tool_schema(
    format: str = "anthropic",
    filter_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the bridge surface as an LLM tool-schema list.

    Args:
        format: One of ``"anthropic"``, ``"openai"``, ``"mcp"``, ``"jsonschema"``.
        filter_prefix: If given, only include tools whose name starts with
            this prefix. Useful for selecting catalog-specific subsets
            (e.g. ``"get_cmb_"`` for the cosmology-instrument tools).

    Returns ``{"ok": True, "format": ..., "n_tools": N, "tools": [...]}`` on
    success; ``{"ok": False, "reason": ...}`` for unknown format.
    """
    if format not in SUPPORTED_FORMATS:
        return {
            "ok": False,
            "reason": f"unknown format '{format}'; supported: {sorted(SUPPORTED_FORMATS)}",
        }

    wrapper = _WRAPPERS[format]
    tools = _enumerate_bridge_tools(filter_prefix=filter_prefix)
    wrapped = [wrapper(_function_to_tool_dict(name, fn)) for name, fn in tools]

    return {
        "ok": True,
        "format": format,
        "filter_prefix": filter_prefix,
        "n_tools": len(wrapped),
        "tools": wrapped,
    }


def get_one_tool_schema(name: str, format: str = "anthropic") -> Dict[str, Any]:
    """Return the schema for a single bridge tool by name.

    Returns ``{"ok": True, "format": ..., "tool": {...}}`` on success;
    ``{"ok": False, "reason": ...}`` if the name is unknown or the
    format is unsupported.
    """
    if format not in SUPPORTED_FORMATS:
        return {
            "ok": False,
            "reason": f"unknown format '{format}'; supported: {sorted(SUPPORTED_FORMATS)}",
        }

    tools = _enumerate_bridge_tools()
    by_name = {tool_name: fn for tool_name, fn in tools}
    if name not in by_name:
        return {
            "ok": False,
            "reason": f"unknown tool '{name}'; use list_tool_names() to discover available tools",
        }

    wrapper = _WRAPPERS[format]
    return {
        "ok": True,
        "format": format,
        "tool": wrapper(_function_to_tool_dict(name, by_name[name])),
    }
