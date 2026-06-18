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
import inspect
import json
import re
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from ..amsc.tool_schema import (
    ToolEntry,
    ToolParameter,
    get_tool_schema,
    warmup_all,
)
from ._coercion import coerce_param, serialise_native

# v0.5.0rc11 — Self-recognition root. The rc9 fix scattered explicit
# side-effect imports here (``from .. import bus`` / ``introspect``) to
# ensure every downstream tool_schema registration fired before any MCP
# consumer queried the registry. Those are now funnelled through the
# single canonical entry-point ``warmup_all()`` (in
# ``srmech.amsc.tool_schema``) — same effect (registry fully populated
# before ``get_tool_schema()``), but the warmup list is now maintained
# in ONE place. ``srmech.__init__`` already calls ``warmup_all()`` at
# import; calling it again here is idempotent and keeps the MCP wrapper
# robust even if it is ever imported by an entry-path that bypasses the
# package ``__init__``.
warmup_all()


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
    "complex": "array",  # complex rides as [real, imaginary] (rc14)
    "bool": "boolean",
    "str": "string",
    "Optional[str]": "string",
    "bytes": "string",  # MCP transports JSON; bytes ride as base64 (rc14)
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
    # numpy-free carrier-spirit param types (v0.7.5rc132) — all ride JSON as a
    # nested (Mat / Mat-tuple) or flat (Vec / HV) array; never named numpy.
    "Mat": "array",
    "Vec": "array",
    "HV": "array",
    "Optional[Vec]": "array",
    "Optional[HV]": "array",
    "Mat | Vec": "array",
    "Sequence[Vec]": "array",
    "Sequence[HV]": "array",
    "tuple[Mat, ...]": "array",
    "list[list[list[float]]]": "array",
    # legacy numpy-free wire-form keys (no param advertises them now; kept for
    # the round-trip / coercion tests).
    "tuple[np.ndarray, ...]": "array",
    "np.ndarray": "array",
    "Optional[np.ndarray]": "array",
    "Optional[list[float]]": "array",
    "Sequence[np.ndarray]": "array",
    "pathlib.Path": "string",
    "callable": "string",  # callables can't ride JSON; ride as name
    # rc16 — operator_name rides as a dotted srmech.* operator-name string.
    "operator_name": "string",
    "ChainSpec": "object",
    # rc16 — a SpectralHandle rides BY REFERENCE as the $srmech_handle id
    # object; the union also accepts base64 bytes (still resolvable at
    # runtime, but the primary wire form is now the handle object).
    "SpectralHandle": "object",
    "SpectralHandle | bytes": "object",
    "numpy.random.Generator": "object",
}


def _json_schema_type_for(param_type: str) -> str:
    """Map a ToolEntry param type-string to a JSON-schema type token."""
    return _TYPE_LEXICON.get(param_type, "string")


# Per-type JSON-encoding hint (v0.5.0rc14). Appended to a param's
# ``description`` so an MCP / Anthropic consumer learns HOW to encode a
# non-JSON native type (base64 for bytes, nested array for ndarray,
# ``[re, im]`` for complex, and the element-hint for the containers). The
# bidirectional coercer in ``srmech.mcp._coercion`` is the runtime half;
# this is how the LLM learns the wire form up front. Types not in this
# map (plain int / float / str / ...) carry no extra hint.
_ENCODING_HINT: Dict[str, str] = {
    "bytes": "base64-encoded bytes",
    "complex": "[real, imaginary]",
    # numpy-free carrier-spirit param types (v0.7.5rc132). The carrier ACCEPTS
    # every degenerate form the no-math plan uses (list / array.array / tuple /
    # nested-list), so the wire form is just a plain JSON array.
    "Mat": (
        "nested JSON array of rows, row-major; complex elements as [re, im]"
    ),
    "Vec": "flat JSON array (length-n); complex elements as [re, im]",
    "HV": "flat JSON array of integers (the hypervector elements)",
    "Optional[Vec]": (
        "flat JSON array (length-n) or null; complex elements as [re, im]"
    ),
    "Optional[HV]": "flat JSON array of integers, or null",
    "Mat | Vec": (
        "nested JSON array of rows (2-D) OR a flat JSON array (1-D); "
        "complex elements as [re, im]"
    ),
    "Sequence[Vec]": "array of flat JSON arrays (each a 1-D vector)",
    "Sequence[HV]": "array of flat JSON integer arrays (each a hypervector)",
    "tuple[Mat, ...]": (
        "array of nested JSON arrays (each a row-major matrix; complex as "
        "[re, im])"
    ),
    "list[list[list[float]]]": (
        "rank-3 nested JSON array of real numbers"
    ),
    "Sequence[bytes]": "array of base64-encoded byte strings",
    # legacy numpy-free wire-form keys (no param advertises them now).
    "np.ndarray": (
        "nested JSON array, row-major; complex elements as [re, im]"
    ),
    "Optional[np.ndarray]": (
        "nested JSON array, row-major; complex elements as [re, im]"
    ),
    "Sequence[np.ndarray]": (
        "array of nested JSON arrays (each row-major; complex as [re, im])"
    ),
    "tuple[np.ndarray, ...]": (
        "array of nested JSON arrays (each row-major; complex as [re, im])"
    ),
    "Mapping[bytes, bytes]": (
        "object mapping base64-encoded key bytes to base64-encoded "
        "value bytes"
    ),
    "list[tuple[bytes, int]]": (
        "array of [base64-encoded bytes, integer] pairs"
    ),
    "list[tuple[bytes, bytes]]": (
        "array of [base64-encoded key, base64-encoded value] pairs"
    ),
    # rc16 — by-reference handle dual-grammar. The LLM copies a producer
    # tool's returned id object verbatim into the next tool's input.
    "SpectralHandle": (
        'an opaque handle id {"$srmech_handle": {"uuid": ..., "name": ...}} '
        "returned by a producing spectral tool (decompose / predict / "
        "truncate_sparse) — pass it back verbatim"
    ),
    "SpectralHandle | bytes": (
        'an opaque handle id {"$srmech_handle": {"uuid": ..., "name": ...}} '
        "returned by a producing spectral tool, OR base64-encoded bytes"
    ),
    "operator_name": (
        "dotted import path of a unary sequence->sequence srmech operator, "
        'e.g. "srmech.amsc.cascade.chiral_flip"'
    ),
}


# ──────────────────────────────────────────────────────────────────────
# Conversion: ToolEntry -> MCP tool definition
# ──────────────────────────────────────────────────────────────────────


# Anthropic (and the MCP JSON-schema convention) require every
# ``input_schema.properties`` KEY to match this pattern. A leaked Python
# varargs/kwargs sigil (``*vectors`` / ``**opts``) violates it and gets
# the WHOLE catalog rejected with a 400 on the Anthropic path. The SSoT
# fix is to register clean ToolParameter names (no sigil); this regex +
# sanitiser is belt-and-braces so a future sloppy registration can never
# again ship an illegal key to either adapter. (rc10 lesson — a live
# Anthropic API test, not the mocks, caught the original ``*vectors``.)
_PROPERTY_KEY_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")


def _sanitise_property_key(key: str) -> str:
    """Strip leading Python varargs/kwargs sigils and clamp a property
    key to the Anthropic/MCP ``^[a-zA-Z0-9_.-]{1,64}$`` grammar.

    ``*vectors`` -> ``vectors``; ``**opts`` -> ``opts``; any other
    out-of-grammar character is replaced with ``_`` and the result is
    truncated to 64 chars. A key that is already valid is returned
    unchanged (the common path)."""
    if _PROPERTY_KEY_RE.match(key):
        return key
    cleaned = key.lstrip("*")
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", cleaned)[:64]
    # Guard the empty / still-invalid edge (e.g. key was all sigils).
    return cleaned if _PROPERTY_KEY_RE.match(cleaned) else "arg"


def _parameter_to_schema_prop(p: ToolParameter) -> Dict[str, Any]:
    """Convert one ToolParameter -> JSON-schema property dict.

    The description carries (1) the param's summary, (2) the canonical
    srmech type-string (so an LLM sees the richer hint even when the
    JSON-schema ``type`` lossily degraded), and (3) — for the non-JSON
    native types — the rc14 JSON-encoding hint (base64 for bytes,
    nested array for ndarray, ``[re, im]`` for complex, the element
    hint for containers), so an MCP / Anthropic consumer knows how to
    encode the value.
    """
    base = (
        f"{p.summary} (srmech-type: {p.type})"
        if p.summary
        else f"srmech-type: {p.type}"
    )
    hint = _ENCODING_HINT.get(p.type)
    description = f"{base} ({hint})" if hint else base
    prop: Dict[str, Any] = {
        "type": _json_schema_type_for(p.type),
        "description": description,
    }
    return prop


def tool_entry_to_mcp_def(entry: ToolEntry) -> Dict[str, Any]:
    """Convert one ToolEntry to an MCP tool definition dict."""
    props: Dict[str, Any] = {}
    required: List[str] = []
    for p in entry.parameters:
        # Sanitise the property KEY (defence-in-depth — see
        # ``_sanitise_property_key``); the ``required`` list must use the
        # SAME sanitised key so it still references a real property.
        key = _sanitise_property_key(p.name)
        props[key] = _parameter_to_schema_prop(p)
        if p.required:
            required.append(key)

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
    """Yield an MCP tool definition for every ADVERTISED registered
    ToolEntry.

    v0.5.0rc15 — entries marked ``mcp_callable=False`` (the 7
    ``srmech.spectral.*`` handle-pending tools) are EXCLUDED here so a
    ``tools/list`` consumer is never offered a tool it cannot actually
    call. They remain in ``get_tool_schema().tools`` for introspection
    (``srmech.introspect.describe`` reports them under
    ``handle_pending``); only the advertised catalog hides them.

    Parameters
    ----------
    name_filter
        Optional predicate ``str -> bool``. When supplied, only
        entries whose ``name`` passes the predicate are yielded.
        Used by the ``--filter`` CLI flag.
    """
    schema = get_tool_schema()
    for entry in schema.tools:
        if not entry.mcp_callable:
            continue
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
            # Name-collision case: a submodule whose name equals a
            # re-exported callable (e.g. ``cascade.sedenion_register`` the
            # MODULE vs the ``sedenion_register`` factory). Importing the
            # submodule makes Python rebind the package attribute from the
            # re-exported function to the module object, so ``getattr`` here
            # yields a non-callable module. Prefer the same-named callable
            # defined inside it — the "module X re-exports callable X"
            # convention — so the registry's flat ``...sedenion_register``
            # ToolEntry resolves regardless of import order (the W7
            # schema/signature drift this otherwise trips post-import).
            if inspect.ismodule(obj):
                inner = getattr(obj, attr_path[-1], None)
                if callable(inner):
                    return inner
            continue
        return obj
    raise MCPToolError(
        f"tool name {name!r} did not resolve to any importable callable"
    )


# ──────────────────────────────────────────────────────────────────────
# Inbound parameter coercion (JSON -> native)
#
# v0.5.0rc14: full bidirectional coercion. The per-type coercer table
# lives in ``srmech.mcp._coercion`` (importable for the type-coercibility
# ratchet + round-trip tests). ``bytes`` ride as base64, ``np.ndarray``
# as a nested JSON list (complex elements as ``[re, im]``), ``complex`` as
# ``[re, im]``, plus the container element-recursions. The callable
# remains the canonical validator and will raise on a real mismatch.
# ──────────────────────────────────────────────────────────────────────


def _coerce_arguments(
    entry: ToolEntry, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """Coerce each inbound JSON argument to the native Python type the
    ToolEntry's declared parameter type names (via
    :func:`srmech.mcp._coercion.coerce_param`).

    Unknown / extra arguments (those with no matching ToolParameter) pass
    through unchanged so the underlying callable raises a real TypeError —
    surfaced to the consumer as an MCP error response.
    """
    type_by_name: Dict[str, str] = {p.name: p.type for p in entry.parameters}
    out: Dict[str, Any] = {}
    for k, v in arguments.items():
        type_string = type_by_name.get(k)
        if type_string is None:
            out[k] = v  # extra arg; let the callable reject it
        else:
            out[k] = coerce_param(v, type_string, param=k)
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
       JSON-RPC has no positional notion) — UNLESS the callable has
       a ``*args`` (VAR_POSITIONAL) parameter, in which case the
       tool-schema exposes that variadic under a clean single name
       (e.g. ``vectors`` for ``hdc.polar_bundle(*vectors)``) and we
       unpack the supplied sequence positionally (``fn(*seq)``).
    5. Return the raw Python result (the server layer JSON-serialises
       and wraps in MCP envelope).

    Exceptions raised by the underlying callable propagate unchanged
    so the dispatcher can surface them as MCP error responses.
    """
    entry = _entry_by_name(name)
    coerced = _coerce_arguments(entry, arguments or {})
    fn = _resolve_dotted_callable(name)

    # Variadic dispatch: ``fn(**coerced)`` cannot call a function with a
    # ``*args`` (VAR_POSITIONAL) parameter — Python raises
    # ``TypeError: got an unexpected keyword argument`` for the variadic
    # name. The tool-schema deliberately exposes the variadic under a
    # clean property name (e.g. ``vectors``), so when the resolved
    # callable has a VAR_POSITIONAL slot, pop the supplied sequence and
    # unpack it positionally; remaining args stay keyword. Found by a
    # live Anthropic API test of the rc9 adapter (hdc.polar_bundle /
    # hdc.klein4_bundle were uncallable on BOTH the MCP and Anthropic
    # paths because both route through this dispatcher).
    sig = inspect.signature(fn)
    var_pos = next(
        (p for p in sig.parameters.values()
         if p.kind is inspect.Parameter.VAR_POSITIONAL),
        None,
    )
    if var_pos is not None:
        seq = coerced.pop(var_pos.name, None)
        if seq is None:
            # Tolerate the historical sigil-prefixed key (``*vectors``)
            # in case any out-of-date caller still sends it, and the
            # plain ``vectors`` fallback the schema now publishes.
            seq = coerced.pop("*" + var_pos.name, None)
            if seq is None:
                seq = coerced.pop("vectors", [])
        return fn(*seq, **coerced)
    return fn(**coerced)


# ──────────────────────────────────────────────────────────────────────
# Result serialisation
# ──────────────────────────────────────────────────────────────────────


def serialise_result(result: Any) -> str:
    """Render a tool result as a JSON-text string suitable for the
    MCP ``content[].text`` slot.

    v0.5.0rc14: the result is first walked through
    :func:`srmech.mcp._coercion.serialise_native` (the outbound half of
    the bidirectional coercion) so ``bytes`` -> base64, ``np.ndarray`` ->
    nested list (complex elements as ``[re, im]``), ``complex`` ->
    ``[re, im]``, numpy scalars -> Python scalars, and tuples/sets ->
    lists — round-trippable with the inbound :func:`_coerce_arguments`.
    Anything ``serialise_native`` leaves untouched is handed to
    ``json.dumps`` with the :func:`_json_fallback` ``default=`` for the
    last-resort cases (dataclasses, exotic objects). Falls back to
    ``repr(result)`` only if even that cannot serialise.
    """
    try:
        prepared = serialise_native(result)
        return json.dumps(prepared, default=_json_fallback, sort_keys=False)
    except (TypeError, ValueError):
        return repr(result)


def _json_fallback(obj: Any) -> Any:
    """``json.dumps`` ``default=`` for objects ``serialise_native`` left
    untouched (it handles bytes / ndarray / complex / numpy-scalars /
    tuples / dicts / Path). This catches the remaining structured cases —
    dataclasses — and degrades anything else to ``repr`` so an LLM
    consumer still sees the value without losing the call."""
    # serialise_native already covers ndarray / numpy-scalar / bytes /
    # complex / tuple / set / Path; re-run it defensively in case a
    # nested ``default=`` invocation surfaces one of those.
    prepared = serialise_native(obj)
    if prepared is not obj:
        return prepared
    # Dataclasses -> their asdict view if available.
    import dataclasses
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return serialise_native(dataclasses.asdict(obj))
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
