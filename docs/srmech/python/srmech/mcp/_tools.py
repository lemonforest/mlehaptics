"""Convert :class:`srmech.introspect.tool_schema.ToolEntry` -> MCP tool defs.

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

import inspect
import json
import re
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from .._resolve import DottedNameError, resolve_dotted_callable
from ..introspect.tool_schema import (
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
# ``srmech.introspect.tool_schema``) — same effect (registry fully populated
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
    # rc113: qbipoly_from_coeffs `coeffs` (a Y-ascending list of integer x-cell
    # lists; also the rc44 gf_rref `rows` matrix, which previously degraded to
    # the "string" fallback).
    "list[list[int]]": "array",
    # 0.9.0rc362: srmech's exact-ℚ carrier and the acoustic-spectrum sequence
    # over it. Both are ARRAYS on the wire — a Q rides as [num, den] (the form
    # serialise_native already emits outbound), a spectrum as a list of those.
    # Registered here as well as in _coercion so the advertised inputSchema and
    # the runtime coercion agree; a coercer without a lexicon entry degrades the
    # schema to "string" and tells a client the opposite of what it must send.
    "Q": "array",
    "Sequence[int | Q | Qalg]": "array",
    # 0.9.0rc463 fix pass: the exact-ℚ matrix operand family. Without these
    # rows every one of them published JSON-schema "string" for a parameter
    # that must be an ARRAY — the schema-layer form of the same defect the
    # coercer-layer rows close. `QMat | Sequence[...]` has shipped since
    # rc379 (conservation_laws) with no row at all. Mirrored in
    # c/src/srmech_tool_schema.c in this same change; that table is
    # HAND-MAINTAINED and nothing syncs it for you.
    "QMat | Sequence[Sequence[int | Q]]": "array",
    "QMat | Sequence[Sequence[int | Q]] | Sequence[int | Q]": "array",
    "Mat | QMat | Sequence[Sequence[int | Q]]": "array",
    "Qalg": "object",
    # 0.9.0rc363: the C2 (ADR-0012 §3.1) type-honesty widenings keep the JSON-schema
    # token their pre-widening spelling advertised, so no client sees a narrower
    # schema than before. Both params are NUMBERS on the wire; the exact-ℚ arm
    # rides as the [num, den] pair `_to_q` already accepts, and (like the rc362
    # `Qalg` arm) is primarily an in-process form. A single-token lexicon cannot
    # express the union — recording that here is more honest than picking the
    # rarer arm and telling a schema-obedient client the wrong thing.
    "float | Q": "number",     # harmonics.classify_chirality_harmonic
    "number | Q": "number",    # coupling.fold_spectrum
    # rc465-fix (`#T1188`): the srmech.physics.qm coordinate-vector union. An
    # ARRAY on the wire exactly as bare `HV` is — each element a bare number or
    # the [num, den] pair `serialise_native` already emits — so the widening
    # costs a schema-obedient client nothing. Mirrored in
    # c/src/srmech_tool_schema.c in this same change; that table is
    # HAND-MAINTAINED and nothing syncs it for you.
    "HV | Sequence[int | Q]": "array",
    "Mapping[bytes, bytes]": "object",
    "dict": "object",
    "Optional[dict]": "object",
    "list": "array",
    "sequence": "array",
    "iterable[int]": "array",
    "tuple[int, int]": "array",
    # 0.9.0rc408 (`#T1078`): cascade.the_one `w`, the winding triad. An ARRAY,
    # like its pair sibling above — without this row it would default to
    # "string" and tell a schema-obedient client to send text for three ints.
    "tuple[int, int, int]": "array",
    # 0.9.0rc408: `Sequence[tuple]` has had a coercer (_seq_tuple) since
    # v0.7.5rc134 but never a lexicon row, so genome.chromosome `genes` and
    # plasmid `chromosomes` have been publishing "string" for what is plainly a
    # nested ARRAY — the ADR-0012 §4.2 silent-degradation row, found while
    # declaring genome.genome `chromosomes` against the same type. Fixed here
    # rather than deferred: it is a falsehood in a schema this rc is already
    # editing, and it costs one row.
    "Sequence[tuple]": "array",
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
    "list[list[list[int]]]": "array",  # rc116: tripoly_from_coeffs coeffs
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
    # ── 0.9.0rc408 (`#T1078`): the HOST-SIDE types. These publish JSON-schema
    #    ``"null"``, and they are the only types in the lexicon that do.
    #
    #    A host-side operand is a live Python object — a callback, an RNG — that
    #    cannot cross a process boundary by ANY encoding. There is no base64
    #    form, no name to resolve, no handle: the value IS the caller's own
    #    function or generator state. So the honest published type is the one
    #    JSON value a client may legally send: ``null``, meaning "absent", which
    #    ``coerce_param`` already passes through unchanged and which runs the op
    #    exactly as if the parameter had been omitted.
    #
    #    WHY NOT ``"string"`` (what the generic ``callable`` key publishes).
    #    ``callable`` means "rides as a NAME a registry resolves" — the
    #    ``operator_name`` pattern. A ``progress`` tick has no such registry, so
    #    publishing ``"string"`` would tell a schema-obedient client to send
    #    text that the op would then try to CALL: a guaranteed TypeError in a
    #    tool that works fine today. Telling a client to send a value that
    #    cannot work is worse than telling it to send nothing.
    #
    #    WHY DECLARE THEM AT ALL, then. Because ``parameters`` is the API
    #    CONTRACT, not only the wire schema — the same argument rc362 made for
    #    naming the in-process ``Qalg`` arm of ``Sequence[int | Q | Qalg]``.
    #    Omitting a host-side param hides a real capability from every consumer
    #    of the registry, INCLUDING the in-process Python callers who can
    #    actually pass it. rc408 measured 13 such parameters hidden across 13
    #    entries; §101 ``progress`` was 11 of them, and for a multi-hour genome
    #    encode it is the ONLY channel that reports working status or accepts a
    #    cancel. The wire limitation is a fact about the TYPE; it was never a
    #    licence to hide the PARAMETER.
    "host_callable": "null",
    "host_rng": "null",
    # rc466 (`#T1188`): the 70-row drain's widened operand types — every one
    # an ARRAY on the wire (the flux union is a number OR an array; the array
    # token is kept so a schema-obedient client can send the sequence form and
    # the exact [num, den] pair, which are both arrays). Mirrored in
    # c/src/srmech_tool_schema.c in this same change; that table is
    # HAND-MAINTAINED and nothing syncs it for you. Deliberately ASCII-only
    # hints (see the rc463 note above).
    "list[float] | list[Q]": "array",
    "Optional[list[int | Q | float]]": "array",
    "list[list[float]] | list[list[Q]]": "array",
    "Optional[list[list[float]] | list[list[Q]]]": "array",
    "Mat | Vec | Sequence[int | Q]": "array",
    "float | Q | Sequence[int | Q | float]": "array",
    "Vec | Sequence[int | Q]": "array",
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
    "HV | Sequence[int | Q]": (
        "flat JSON array of components. The LEAVES select the carrier: bare "
        "integers or [numerator, denominator] pairs take the EXACT-Q rung, "
        "floats take the float64 one"),
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
    "list[list[int]]": (
        "nested JSON array of integer lists (rows / coefficient cells)"
    ),
    "Sequence[bytes]": "array of base64-encoded byte strings",
    # 0.9.0rc408 (`#T1078`): the host-side operands. Both publish JSON-schema
    # "null" (see _TYPE_LEXICON) — this is the prose half, telling a consumer
    # WHY the only legal wire value is absence and what to do instead.
    "host_callable": (
        "a HOST-SIDE callable, supplied by the calling process. It cannot "
        "cross a process boundary in any encoding — there is no name to "
        "resolve and no serialised form — so over MCP / JSON-RPC the only "
        "legal value is null (absent), and the op then runs with the callback "
        "disabled, which is its default. In-process Python callers pass a real "
        "function; each parameter's own summary gives the exact signature"
    ),
    "host_rng": (
        "a HOST-SIDE random generator (``random.Random``, or a numpy "
        "``Generator``), supplied by the calling process. Generator STATE has "
        "no JSON form, so over MCP / JSON-RPC the only legal value is null "
        "(absent) — pass the integer ``seed`` parameter instead, which is "
        "advertised alongside it and gives a reproducible stream"
    ),
    # 0.9.0rc362: the exact-ℚ carrier + the acoustic-spectrum sequence over it.
    "Q": (
        "[numerator, denominator] as exact integers, or a bare integer; never "
        "a float (an exact rational is required)"
    ),
    "Sequence[int | Q | Qalg]": (
        "array of frequency ratios, each a bare integer or an exact "
        "[numerator, denominator] pair; never a float. The Qalg arm of the "
        "declared type (the exact algebraic-irrational carrier) has no JSON "
        "form and is reachable IN-PROCESS ONLY — over the wire, build a Tier-2 "
        "spectrum with equal_temperament_partials / stiff_string_partials and "
        "pass its result on directly"
    ),
    # 0.9.0rc463 fix pass: the exact-ℚ matrix operands + the algebraic
    # eigenvalue. Deliberately ASCII-only: every one of these strings is
    # mirrored BYTE-FOR-BYTE into MCP_ENCODING_HINT in
    # c/src/srmech_tool_schema.c, and the native / pure MCP-def parity gate
    # compares the emitted JSON, so a stray glyph is a divergence with no
    # upside in a wire hint.
    "QMat | Sequence[Sequence[int | Q]]": (
        "nested JSON array of rows, row-major; each entry a bare integer or an exact [numerator, denominator] pair -- never a float"
    ),
    "QMat | Sequence[Sequence[int | Q]] | Sequence[int | Q]": (
        "nested JSON array of rows (an (m, k) block) OR a flat JSON array of integers (an (m,) column); each entry exact -- never a float. A RATIONAL column must use the nested (m, 1) form, because [[a, b], [c, d]] is read as a 2-column block and not as a column of two rationals"
    ),
    "Mat | QMat | Sequence[Sequence[int | Q]]": (
        "nested JSON array of rows, row-major. The LEAVES select the carrier: integers / [numerator, denominator] pairs take the EXACT-Q rung, floats take the float64 one"
    ),
    "Qalg": (
        "JSON object {\"m\": [int, ...], \"coords\": [[num, den], ...], \"root\": <float | [re, im]>} -- the monic Z[x] minimal polynomial and the power-basis coordinates, both ASCENDING, plus the embedding that says WHICH root of m this element is. Omitting root builds a Qalg the op's own projection then refuses, rather than guessing a conjugate"
    ),
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
        'e.g. "srmech.cascade.chiral_flip"'
    ),
    # rc466 (`#T1188`): the 70-row drain's widened operand types. ASCII-only;
    # mirrored byte-for-byte into MCP_ENCODING_HINT in c/src/srmech_tool_schema.c.
    "list[float] | list[Q]": (
        "flat JSON array. The LEAVES select the carrier: bare integers or [numerator, denominator] pairs take the EXACT-Q rung, floats take the float64 one"
    ),
    "Optional[list[int | Q | float]]": (
        "flat JSON array (or null): each entry a bare integer, a float, or an exact [numerator, denominator] pair"
    ),
    "list[list[float]] | list[list[Q]]": (
        "JSON array of flat JSON arrays. The LEAVES select the carrier: bare integers or [numerator, denominator] pairs take the EXACT-Q rung, floats take the float64 one"
    ),
    "Optional[list[list[float]] | list[list[Q]]]": (
        "JSON array of flat JSON arrays, or null. The LEAVES select the carrier: bare integers or [numerator, denominator] pairs take the EXACT-Q rung, floats take the float64 one"
    ),
    "Mat | Vec | Sequence[int | Q]": (
        "nested JSON array of rows (2-D) OR a flat JSON array (1-D); complex elements as [re, im]. Integer leaves take the EXACT-Q rung IN-PROCESS (an exact [num, den] leaf is ambiguous with a 2-column row on the wire)"
    ),
    "float | Q | Sequence[int | Q | float]": (
        "a bare number (a scalar flux) or a JSON array (a flux sequence) whose entries are bare numbers or exact [numerator, denominator] pairs; the exact scalar flux is spelled as the one-element sequence [[num, den]]"
    ),
    "Vec | Sequence[int | Q]": (
        "flat JSON array (length-n). The LEAVES select the carrier: bare integers or [numerator, denominator] pairs take the EXACT-Q rung, floats take the float64 one"
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
    ``[re, im]`` for complex, the element hint for containers), so an
    MCP / Anthropic consumer knows how to encode the value.
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

    Entries marked ``mcp_callable=False`` are EXCLUDED here so a
    ``tools/list`` consumer is never offered a tool it cannot actually
    call. They remain in ``get_tool_schema().tools`` for introspection
    (``srmech.introspect.describe`` reports them under
    ``handle_pending``); only the advertised catalog hides them.

    The exclusion is LIVE as of v0.9.0rc414 (`#T1092`). It was a no-op from
    rc16 (when the ``$srmech_handle`` grammar returned the 7
    ``srmech.spectral.*`` tools to callable) until rc414, which excluded the
    first entry that no encoder can rescue — a context manager, whose
    obstruction is its shape in TIME rather than its type: a ``with``-block
    scope cannot span two JSON-RPC calls. Every entry excluded here MUST carry
    an ``mcp_unavailable_reason``, so a consumer that notices the absence can
    always find out why; that invariant is gated, and it is stated as an
    invariant precisely so no COUNT is restated in this docstring, where two
    previous literals went stale.

    (rc410, `#T1085`: an earlier version of this paragraph was self-refuting —
    it promised the literal was gone in the sentence after restating it. The
    literal is now actually gone, and ``tests/test_owner_axis_rc410.py``
    enforces that no shipped module restates it. The live values are
    ``len(get_tool_schema().by_owner("srmech"))`` for the registry and
    ``sum(1 for t in get_tool_schema().tools if t.mcp_callable)`` for the
    advertised catalog.)

    Parameters
    ----------
    name_filter
        Optional predicate ``str -> bool``. When supplied, only
        entries whose ``name`` passes the predicate are yielded.
        Used by the ``--filter`` CLI flag.

    v0.9.0rc185 — the UNFILTERED advertised catalog (no ``name_filter``)
    over an all-srmech registry is produced by the bare-C host op
    ``srmech_tool_entries_to_mcp_defs`` and parsed back, byte-identical to
    this pure projection. A ``name_filter``, any profile tool, a
    stale/absent lib, or a non-OK C status falls back to the pure
    per-entry path.
    """
    schema = get_tool_schema()
    if name_filter is None and all(t.owner == "srmech" for t in schema.tools):
        native = _native_mcp_defs()
        if native is not None:
            yield from native
            return
    for entry in schema.tools:
        if not entry.mcp_callable:
            continue
        if name_filter is not None and not name_filter(entry.name):
            continue
        yield tool_entry_to_mcp_def(entry)


def _native_mcp_defs() -> Optional[List[Dict[str, Any]]]:
    """The rc185 C ``srmech_tool_entries_to_mcp_defs`` output parsed to a
    list of MCP tool-def dicts, or ``None`` when the native peer is
    unavailable / returns non-OK (caller uses the pure per-entry path)."""
    try:
        from .. import _native
    except Exception:  # pragma: no cover — defensive; _native always imports
        return None
    raw = _native.tool_entries_to_mcp_defs_c()
    if raw is None:
        return None
    # stdlib json by PROTOCOL-BOUNDARY decision, not neglect (`#T1008`): this is the
    # MCP JSON-RPC wire — untrusted external input on a published protocol contract.
    # Self-hosting it onto srmech._json is a separate decision with a different risk
    # profile from reading srmech's own descriptors, so the READ self-host stops here.
    return json.loads(raw.decode("utf-8"))


# ──────────────────────────────────────────────────────────────────────
# Filter-glob compilation
# ──────────────────────────────────────────────────────────────────────


def compile_filter(pattern: Optional[str]) -> Optional[Callable[[str], bool]]:
    """Compile a glob-ish filter pattern -> name predicate.

    Patterns:

    * ``None`` (default) -> ``None`` (no filter).
    * ``"srmech.cascade.*"`` -> matches the cascade sub-tree.
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
#
# rc413 (`#T1094`): the walker itself now lives in ``srmech._resolve`` — core,
# not this adapter. It had two CORE callers (``srmech._handles`` and
# ``srmech.dsl._alias``) importing upward into ``srmech.mcp``, which made the
# ADR-0009 §4 host-glue layer non-removable. ``invoke_tool`` below re-wraps the
# core :class:`DottedNameError` as :class:`MCPToolError` so the JSON-RPC
# dispatcher's ``except MCPToolError`` keeps catching resolution failures
# unchanged; the MCP error type stays an MCP-layer concern.
# ──────────────────────────────────────────────────────────────────────


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
    try:
        fn = resolve_dotted_callable(name)
    except DottedNameError as exc:
        # Preserve the MCP-layer contract: _server.handle / anthropic_agent
        # both catch MCPToolError to turn a resolution failure into a
        # JSON-RPC error response rather than a traceback.
        raise MCPToolError(str(exc)) from exc

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
    the bidirectional coercion) so ``bytes`` -> base64, ``Mat`` / ``Vec`` /
    ``HV`` -> nested or flat list, ``Q`` -> ``[num, den]``, ``complex`` ->
    ``[re, im]``, and tuples/sets -> lists — round-trippable with the
    inbound :func:`_coerce_arguments`.
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
    untouched (it handles bytes / complex / Q / Mat / Vec / HV /
    array.array / tuples / dicts / Path). This catches the remaining structured cases —
    dataclasses — and degrades anything else to ``repr`` so an LLM
    consumer still sees the value without losing the call."""
    # serialise_native already covers bytes / complex / Q / Mat / Vec / HV /
    # array.array / tuple / set / Path; re-run it defensively in case a
    # nested ``default=`` invocation surfaces one of those. Since rc414 it
    # also covers the framework carriers (the ``$srmech_carrier`` envelope),
    # so most of what used to reach the ``repr`` line below no longer does.
    prepared = serialise_native(obj)
    if prepared is not obj:
        return prepared
    # rc414 (`#T1092`) — an object that ships its OWN canonical JSON view
    # uses it, ahead of the generic dataclass arm. The motivating case is
    # ``ToolSchema``: ``dataclasses.asdict`` rendered it with FIVE extra keys
    # and at a different size from the canonical ``to_jsonable`` (2,572,811 vs
    # 2,501,642 bytes), so the same object had two disagreeing renderings and
    # the one a consumer got depended on which door it came through. The
    # canonical view is the API contract (ADR-0012); ``asdict`` is a Python
    # implementation detail leaking through the wire.
    to_jsonable = getattr(obj, "to_jsonable", None)
    if callable(to_jsonable) and not isinstance(obj, type):
        try:
            return serialise_native(to_jsonable())
        except TypeError:
            pass          # a to_jsonable that needs arguments is not this one
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
