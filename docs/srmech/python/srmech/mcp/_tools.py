"""Convert :class:`srmech.amsc.tool_schema.ToolEntry` -> MCP tool defs.

The MCP tool definition shape (per the spec)::

    {
      "name": "...",
      "description": "...",
      "inputSchema": {
        "type": "object",
        "properties": {<param-name>: <json-schema-prop>, ...},
        "required": [<param-name>, ...],
      },
    }

We derive ``inputSchema`` from each ToolEntry's parameter list.
:class:`ToolEntry` does NOT carry a Python callable handle (it's a
declarative descriptor), so we resolve the underlying callable by
dotted-name walk through the live module tree at invocation time.
Pure Python; no eval; no reflection on private attributes.

Type translation
----------------
The tool_schema's ``type`` field is a free-form string (it's a
documentation hint, not a JSON-schema). We map a small lexicon to
JSON-schema primitives so MCP clients get useful auto-complete; any
unknown type-string degrades to ``{"type": "string"}`` and the
underlying callable is responsible for coercion. This intentionally
preserves the ToolEntry surface as the SSoT.

Resolution rule
---------------
``srmech.amsc.format.sha256_bytes`` -> ``import srmech.amsc.format;
getattr(srmech.amsc.format, "sha256_bytes")``. Profile-contributed
tools follow the same dotted-name rule using their declared owner
(profile name). Any unresolvable name raises :class:`MCPToolError`
which the dispatcher converts to a JSON-RPC error response.
"""

from __future__ import annotations

import importlib
import json
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from ..amsc.tool_schema import (
    ToolEntry,
    ToolParameter,
    get_tool_schema,
)

# v0.5.0rc9 — side-effect imports: ensure all downstream tool_schema
# registrations fire before any MCP consumer queries the registry.
# - ``srmech.bus`` triggers ``srmech.bus._tool_schema._register_bus_tools()``
#   (registers ``srmech.bus.decode_splice`` / ``.list_endpoints`` /
#   ``.by_name``). srmech.bus is NOT transitively imported by
#   ``srmech.amsc.tool_schema``; without this warmup the bus tools
#   were silently missing from the LLM-facing catalog (root cause of
#   the discoverability bug).
# - ``srmech.introspect`` is already imported transitively from
#   ``srmech.__init__`` (which calls ``_introspect._maybe_auto_publish``)
#   so its tools are registered through that path, but adding the
#   explicit import here is belt-and-braces + readable: the MCP
#   wrapper now self-documents which sibling packages it surfaces.
from .. import bus as _bus  # noqa: F401 — side effect: registers srmech.bus.* tools
from .. import introspect as _introspect  # noqa: F401 — side effect: registers srmech.introspect.* tools


# ──────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────


class MCPToolError(Exception):
    """Raised when tool resolution or invocation fails."""


# ──────────────────────────────────────────────────────────────────────
# Type translation lexicon
# ──────────────────────────────────────────────────────────────────────


# Map ToolEntry param type-string -> JSON-schema primitive type.
# Anything not in this table degrades to "string" — the underlying
# Python callable is the canonical place that validates the value.
_TYPE_LEXICON: Dict[str, str] = {
    "int": "integer",
    "Optional[int]": "integer",
    "list[int]": "array",
    "float": "number",
    "Optional[float]": "number",
    "number": "number",
    "complex": "string",  # complex serialises as "a+bi" string
    "bool": "boolean",
    "str": "string",
    "Optional[str]": "string",
    "bytes": "string",  # MCP transports JSON; bytes ride as hex/b64
    "Sequence[bytes]": "array",
    "list[tuple[bytes, bytes]]": "array",
    "list[tuple[bytes, int]]": "array",
    "list[tuple[int, int]]": "array",
    "Mapping[bytes, bytes]": "object",
    "dict": "object",
    "Optional[dict]": "object",
    "list": "array",
    "sequence": "array",
    "iterable[int]": "array",
    "tuple[int, int]": "array",
    "tuple[np.ndarray, ...]": "array",
    "np.ndarray": "array",
    "Optional[np.ndarray]": "array",
    "Optional[list[float]]": "array",
    "Sequence[np.ndarray]": "array",
    "pathlib.Path": "string",
    "callable": "string",  # callables can't ride JSON; ride as name
    "ChainSpec": "object",
    "SpectralHandle": "object",
    "SpectralHandle | bytes": "string",
    "numpy.random.Generator": "object",
}


def _json_schema_type_for(param_type: str) -> str:
    """Map a ToolEntry param type-string to a JSON-schema type token."""
    return _TYPE_LEXICON.get(param_type, "string")


# ──────────────────────────────────────────────────────────────────────
# Conversion: ToolEntry -> MCP tool definition
# ──────────────────────────────────────────────────────────────────────


def _parameter_to_schema_prop(p: ToolParameter) -> Dict[str, Any]:
    """Convert one ToolParameter -> JSON-schema property dict."""
    prop: Dict[str, Any] = {
        "type": _json_schema_type_for(p.type),
        # Keep the original ToolEntry type-string in the description
        # so an LLM client can read the canonical (richer) type-hint
        # even when the JSON-schema type lossily degraded.
        "description": (
            f"{p.summary} (srmech-type: {p.type})"
            if p.summary
            else f"srmech-type: {p.type}"
        ),
    }
    return prop


def tool_entry_to_mcp_def(entry: ToolEntry) -> Dict[str, Any]:
    """Convert one ToolEntry to an MCP tool definition dict."""
    props: Dict[str, Any] = {}
    required: List[str] = []
    for p in entry.parameters:
        props[p.name] = _parameter_to_schema_prop(p)
        if p.required:
            required.append(p.name)

    # Description carries the summary + return-type hint + owner +
    # category so the LLM has all the context the registry tracks.
    desc_parts = [entry.summary]
    if entry.returns is not None:
        ret_str = f"Returns: {entry.returns.type}"
        if entry.returns.shape:
            ret_str += f" ({entry.returns.shape})"
        desc_parts.append(ret_str)
    desc_parts.append(f"[srmech category: {entry.category}; owner: {entry.owner}]")
    description = " — ".join(desc_parts)

    mcp_def: Dict[str, Any] = {
        "name": entry.name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": props,
            "required": required,
        },
    }
    return mcp_def


def tool_entries_to_mcp_defs(
    *,
    name_filter: Optional[Callable[[str], bool]] = None,
) -> Iterator[Dict[str, Any]]:
    """Yield an MCP tool definition for every registered ToolEntry.

    Parameters
    ----------
    name_filter
        Optional predicate ``str -> bool``. When supplied, only
        entries whose ``name`` passes the predicate are yielded.
        Used by the ``--filter`` CLI flag.
    """
    schema = get_tool_schema()
    for entry in schema.tools:
        if name_filter is not None and not name_filter(entry.name):
            continue
        yield tool_entry_to_mcp_def(entry)


# ──────────────────────────────────────────────────────────────────────
# Filter-glob compilation
# ──────────────────────────────────────────────────────────────────────


def compile_filter(pattern: Optional[str]) -> Optional[Callable[[str], bool]]:
    """Compile a glob-ish filter pattern -> name predicate.

    Patterns:

    * ``None`` (default) -> ``None`` (no filter).
    * ``"srmech.amsc.cascade.*"`` -> matches the cascade sub-tree.
    * ``"srmech.amsc.*"`` -> matches everything under AMSC.
    * A bare prefix without ``"*"`` -> exact-name match.

    Uses :mod:`fnmatch` for the actual matching (so it understands
    standard glob metacharacters ``*`` / ``?`` / ``[abc]``).
    """
    if pattern is None:
        return None
    import fnmatch

    pat = pattern
    return lambda name: fnmatch.fnmatchcase(name, pat)


# ──────────────────────────────────────────────────────────────────────
# Resolution: dotted name -> live callable
# ──────────────────────────────────────────────────────────────────────


def _resolve_dotted_callable(name: str) -> Callable[..., Any]:
    """Walk a dotted name to its live callable.

    For ``a.b.c.d``: try ``import a.b.c`` then ``getattr(mod, "d")``;
    fall back to splitting at the last ``.`` and importing whatever
    prefix imports cleanly. Raises :class:`MCPToolError` on failure.
    """
    assert name, "resolve: name must be non-empty"
    parts = name.split(".")
    if len(parts) < 2:
        raise MCPToolError(
            f"tool name {name!r} has no module prefix; "
            f"cannot resolve to a Python callable"
        )

    # Try the most-specific module prefix first, then back off.
    # e.g. for "srmech.amsc.cascade.chiral_flip" we try
    # importing "srmech.amsc.cascade" then attr "chiral_flip".
    for split_idx in range(len(parts) - 1, 0, -1):
        mod_name = ".".join(parts[:split_idx])
        attr_path = parts[split_idx:]
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        obj: Any = mod
        try:
            for a in attr_path:
                obj = getattr(obj, a)
        except AttributeError:
            continue
        if not callable(obj):
            continue
        return obj
    raise MCPToolError(
        f"tool name {name!r} did not resolve to any importable callable"
    )


# ──────────────────────────────────────────────────────────────────────
# Bytes/path coercion helpers (the JSON-typed args need light coercion
# before they can reach the underlying Python callables)
# ──────────────────────────────────────────────────────────────────────


def _coerce_arg(value: Any, type_hint: str) -> Any:
    """Light coercion of a JSON-typed arg to the Python type the
    callable expects. Pure best-effort; the callable is the canonical
    validator and will raise on a real mismatch.
    """
    # bytes ride as hex strings (lowercase) over JSON.
    if type_hint == "bytes" and isinstance(value, str):
        try:
            return bytes.fromhex(value)
        except ValueError:
            # If it's not hex, pass the str through; the callable will
            # see a TypeError and the dispatcher will surface it as an
            # MCP error.
            return value
    if type_hint == "pathlib.Path" and isinstance(value, str):
        import pathlib
        return pathlib.Path(value)
    if type_hint == "tuple[int, int]" and isinstance(value, list):
        return tuple(value)
    # Everything else: pass through. The underlying callable is the
    # canonical validator.
    return value


def _coerce_arguments(
    entry: ToolEntry, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply ``_coerce_arg`` per-parameter using the ToolEntry's
    declared types. Unknown / extra arguments pass through unchanged
    so the underlying callable raises a real TypeError."""
    type_by_name: Dict[str, str] = {p.name: p.type for p in entry.parameters}
    out: Dict[str, Any] = {}
    for k, v in arguments.items():
        out[k] = _coerce_arg(v, type_by_name.get(k, "str"))
    return out


# ──────────────────────────────────────────────────────────────────────
# Invocation
# ──────────────────────────────────────────────────────────────────────


def _entry_by_name(name: str) -> ToolEntry:
    """Look up a ToolEntry by name. Raises MCPToolError if absent."""
    schema = get_tool_schema()
    entry = schema.lookup(name)
    if entry is None:
        raise MCPToolError(f"no registered tool named {name!r}")
    return entry


def invoke_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Invoke one registered tool by name.

    1. Look up the ToolEntry (raises MCPToolError if missing).
    2. Coerce the JSON-typed arguments to the Python types the
       callable expects.
    3. Resolve the dotted name to a live callable.
    4. Call it with ``**arguments`` (keyword-arguments only;
       JSON-RPC has no positional notion).
    5. Return the raw Python result (the server layer JSON-serialises
       and wraps in MCP envelope).

    Exceptions raised by the underlying callable propagate unchanged
    so the dispatcher can surface them as MCP error responses.
    """
    entry = _entry_by_name(name)
    coerced = _coerce_arguments(entry, arguments or {})
    fn = _resolve_dotted_callable(name)
    return fn(**coerced)


# ──────────────────────────────────────────────────────────────────────
# Result serialisation
# ──────────────────────────────────────────────────────────────────────


def serialise_result(result: Any) -> str:
    """Render a tool result as a JSON-text string suitable for the
    MCP ``content[].text`` slot.

    Falls back to ``repr(result)`` for objects json.dumps cannot
    handle (e.g. numpy arrays, dataclasses, tuples-of-bytes). The
    MCP content slot is fundamentally textual; this is the
    appropriate place to lossy-serialise.
    """
    try:
        return json.dumps(result, default=_json_fallback, sort_keys=False)
    except (TypeError, ValueError):
        return repr(result)


def _json_fallback(obj: Any) -> Any:
    """json.dumps default= callable for objects we can't natively
    serialise. Preserves enough info that an LLM consumer can read
    the result without losing structure."""
    # numpy arrays -> list
    try:
        import numpy as np  # type: ignore
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
    except ImportError:  # pragma: no cover — numpy is a hard dep
        pass
    # bytes -> hex
    if isinstance(obj, (bytes, bytearray)):
        return obj.hex()
    # tuples / sets -> list
    if isinstance(obj, (tuple, set, frozenset)):
        return list(obj)
    # pathlib.Path -> str
    import pathlib
    if isinstance(obj, pathlib.PurePath):
        return str(obj)
    # Dataclasses -> their asdict view if available.
    import dataclasses
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    # Last resort: repr
    return repr(obj)


__all__ = [
    "MCPToolError",
    "compile_filter",
    "invoke_tool",
    "serialise_result",
    "tool_entries_to_mcp_defs",
    "tool_entry_to_mcp_def",
]
