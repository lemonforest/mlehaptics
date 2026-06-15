"""LLM-friendly introspection of the AMSC framework + profile extensions.

Task #198 — produces a single, structured description of every
callable surface srmech exposes (and, post-Task #199, every profile-
contributed callable), so an LLM consumer can discover what srmech
can do without reading the implementation. The same view powers
the profile loader's smoke-test auto-derivation (ADR-0001 §5.5).

Wire format
-----------
A `ToolSchema` is a dataclass mirroring this JSON shape:

    {
      "srmech_version": "0.3.0",
      "tool_schema_version": "1.0",
      "tools": [
        {
          "name": "srmech.amsc.format.sha256_bytes",
          "owner": "srmech",                  # "srmech" or a profile name
          "category": "format",               # free-form taxonomy hint
          "summary": "SHA-256 over raw bytes; returns lowercase hex.",
          "parameters": [
            {"name": "data", "type": "bytes", "required": true},
          ],
          "returns": {"type": "str", "shape": "64-char lowercase hex"},
          "smoke_test_hint": {"data": "b''"},  # minimal-input for §5.5
          "example": {
            "input":  {"data": "b'abc'"},
            "output": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
          },
        },
        ...
      ],
    }

The `tools` array is the load-bearing surface. Each entry is a
`ToolEntry`. The shape is identical for srmech's own tools and
for profile-contributed tools — only the `owner` field
disambiguates.

Discovery
---------
- `get_tool_schema()` returns the full assembled `ToolSchema` for
  the current process.
- `register_tool(entry)` is the imperative-API path that builtin
  modules use to declare themselves at import time. Idempotent;
  re-registration with an identical entry is a no-op; with a
  different entry it raises `ToolSchemaConflictError`.
- `register_profile_tools(profile_name, entries)` is the path
  profiles use (Task #199); same semantics but tags each entry
  with the contributing profile.
- `tool_schema_view()` returns a stable dict suitable for JSON
  serialisation (preserves insertion order; profile-contributed
  entries grouped after srmech's own).

Use with profile loader
-----------------------
ADR-0001 §5.5 — the profile loader reads each profile's
`[profile.tool_schema].extension_file` (a TOML file in the
profile's package) and feeds the entries through
`register_profile_tools(profile_name, entries_from_toml)`. The
extension-file TOML schema mirrors the JSON shape above modulo
TOML's syntactic differences (array of tables instead of array
of objects).
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover  (py3.10 only)
    import tomli as tomllib  # type: ignore[no-redef]


# ──────────────────────────────────────────────────────────────────────
# Format version
# ──────────────────────────────────────────────────────────────────────
TOOL_SCHEMA_VERSION: str = "1.0"

#: Inline discoverability note (v0.5.0rc7) appended to the ``summary``
#: of every emitting op's ToolEntry. Surfaces the opt-in path through
#: ``srmech.introspect.publish`` / ``SRMECH_PUBLISH_STATUS`` so the
#: MCP-adapter-facing tool catalog (rc6) tells the LLM where to flip
#: emission on. Without this opt-in, all srmech operations are silent
#: (zero overhead in the off-path).
PUBLISH_OPT_IN_NOTE: str = (
    " Events emitted only when wrapped in `srmech.introspect.publish()` "
    "or `SRMECH_PUBLISH_STATUS=1` env-var set; otherwise silent."
)

#: RESOLVED in v0.5.0rc16. This was the reason stamped on the 7
#: ``srmech.spectral.*`` ToolEntries marked ``mcp_callable=False`` in rc15
#: (their surface is a bare ``SpectralHandle`` / ``SpectralHandle | bytes``
#: opaque handle JSON-RPC cannot carry by value). rc16 ships the
#: by-reference id grammar (``$srmech_handle`` envelope + :mod:`srmech._handles`
#: registry), so all 7 are now ``mcp_callable=True`` and this constant is no
#: longer applied to any entry. Retained (unused) for changelog/history
#: legibility; safe to delete in a later release.
_SPECTRAL_HANDLE_PENDING_REASON: str = (
    "handle-pending (resolved in rc16): by-reference SpectralHandle id now "
    "rides as the $srmech_handle envelope via srmech._handles."
)


# ──────────────────────────────────────────────────────────────────────
# Error types
# ──────────────────────────────────────────────────────────────────────


class ToolSchemaError(Exception):
    """Base for tool-schema errors."""


class ToolSchemaConflictError(ToolSchemaError):
    """Raised when a tool entry's name collides with a different prior
    registration. Same-content re-registration is silent (idempotent)."""


class ToolSchemaValidationError(ToolSchemaError):
    """Raised when a tool entry fails internal validation (missing
    required fields, malformed shape, etc.)."""


# ──────────────────────────────────────────────────────────────────────
# Data shape
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ToolParameter:
    """One parameter of a tool entry's call signature."""

    name: str
    type: str
    required: bool = True
    summary: str = ""


@dataclass(frozen=True)
class ToolReturn:
    """Return-value description of a tool entry."""

    type: str
    shape: str = ""


@dataclass(frozen=True)
class ToolEntry:
    """One callable surface in the tool schema.

    `name` is the full dotted-path identifier (e.g.
    ``"srmech.amsc.format.sha256_bytes"`` or
    ``"chess.piece_graph_spectrum"`` for profile-contributed
    tools — the profile prefix matches `owner`).

    `owner` is either ``"srmech"`` (for srmech's own AMSC tools)
    or a profile name (for profile-contributed tools registered
    via :func:`register_profile_tools`).
    """

    name: str
    owner: str
    category: str
    summary: str
    parameters: Tuple[ToolParameter, ...] = field(default_factory=tuple)
    returns: Optional[ToolReturn] = None
    smoke_test_hint: Optional[Dict[str, Any]] = None
    example: Optional[Dict[str, Any]] = None
    #: v0.5.0rc15 — whether this tool is actually invocable across the
    #: JSON-RPC / Anthropic boundary. Default ``True`` (back-compat: every
    #: pre-rc15 ToolEntry stays callable). Set ``False`` for tools whose
    #: param/return types are an opaque in-process handle that JSON cannot
    #: carry by value (the 7 ``srmech.spectral.*`` tools whose surface is a
    #: bare ``SpectralHandle`` / ``SpectralHandle | bytes`` — rc14 left
    #: their coercion as an ``_identity`` pass-through, which the static
    #: ``has_coercer`` ratchet could not distinguish from a real handler).
    #: A ``False`` entry STAYS in ``get_tool_schema().tools`` for
    #: introspection but is EXCLUDED from the advertised MCP ``tools/list``
    #: + Anthropic catalogs so an LLM is never offered an uncallable tool.
    mcp_callable: bool = True
    #: Human-readable reason a tool is ``mcp_callable=False`` (surfaced to
    #: introspection consumers). ``None`` for callable tools.
    mcp_unavailable_reason: Optional[str] = None

    def to_jsonable(self) -> Dict[str, Any]:
        """Render as a JSON-serialisable dict. Used by
        :func:`tool_schema_view`."""
        out: Dict[str, Any] = {
            "name": self.name,
            "owner": self.owner,
            "category": self.category,
            "summary": self.summary,
            "parameters": [asdict(p) for p in self.parameters],
            "mcp_callable": self.mcp_callable,
        }
        if self.returns is not None:
            out["returns"] = asdict(self.returns)
        if self.smoke_test_hint is not None:
            out["smoke_test_hint"] = dict(self.smoke_test_hint)
        if self.example is not None:
            out["example"] = dict(self.example)
        if self.mcp_unavailable_reason is not None:
            out["mcp_unavailable_reason"] = self.mcp_unavailable_reason
        return out


@dataclass(frozen=True)
class ToolSchema:
    """The full tool-schema view for the current process."""

    srmech_version: str
    tool_schema_version: str
    tools: Tuple[ToolEntry, ...]

    def to_jsonable(self) -> Dict[str, Any]:
        return {
            "srmech_version": self.srmech_version,
            "tool_schema_version": self.tool_schema_version,
            "tools": [t.to_jsonable() for t in self.tools],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_jsonable(), indent=indent, sort_keys=False)

    def by_owner(self, owner: str) -> Tuple[ToolEntry, ...]:
        """Return all tools contributed by a given owner."""
        return tuple(t for t in self.tools if t.owner == owner)

    def lookup(self, name: str) -> Optional[ToolEntry]:
        """Look up one tool by full dotted name. Returns None if absent."""
        for t in self.tools:
            if t.name == name:
                return t
        return None

    def __iter__(self):
        """Iterate the registered tools directly (``for t in schema``).

        v0.6.0rc15 — closes the ``'ToolSchema' object is not iterable``
        footgun. ``get_tool_schema()`` returns this object; ``tool_schema_view()``
        returns the JSON dict — both stay, and now the object iterates too.
        """
        return iter(self.tools)

    def __len__(self) -> int:
        """Number of registered tools (``len(schema)``)."""
        return len(self.tools)

    def resolve(self, name: str) -> Optional[ToolEntry]:
        """Resolve a tool by full name OR by bare leaf / dotted suffix.

        v0.6.0rc15 — the "find a tool in ≤1 call" surface. Exact full-name
        match wins (same as :meth:`lookup`). Otherwise the bare leaf
        (``"kuramoto_step"``) or any dotted suffix (``"cascade.kuramoto_step"``)
        is matched against ``srmech.amsc.cascade.kuramoto_step``. Returns the
        single matching entry, or ``None`` when there is no match OR the name
        is AMBIGUOUS (resolves to >1 tool) — an ambiguous leaf is never
        silently resolved. Use :meth:`resolve_all` to enumerate the
        candidates for an ambiguous name.
        """
        exact = self.lookup(name)
        if exact is not None:
            return exact
        matches = self.resolve_all(name)
        return matches[0] if len(matches) == 1 else None

    def resolve_all(self, name: str) -> Tuple[ToolEntry, ...]:
        """Every tool whose full name is ``name`` or ends with ``.name``.

        The companion to :meth:`resolve` for the ambiguous case: a bare leaf
        mapping to more than one fully-qualified tool returns all of them
        here so the caller can disambiguate. Registration order preserved.
        """
        suffix = "." + name
        return tuple(
            t for t in self.tools
            if t.name == name or t.name.endswith(suffix)
        )


# ──────────────────────────────────────────────────────────────────────
# Registry
#
# Module-level for simplicity. JPL-discipline parallel: bounded
# (one entry per registered name; first-register-wins on identical
# repeats; raise on conflicts); no dynamic allocation in the
# hot path (lookup is a tuple iteration); no reflection-driven
# attribute lookup.
# ──────────────────────────────────────────────────────────────────────

_REGISTRY: Dict[str, ToolEntry] = {}


def register_tool(entry: ToolEntry) -> None:
    """Register one tool entry. Idempotent on identical re-registration;
    raises :class:`ToolSchemaConflictError` on a name collision with
    differing content."""
    assert isinstance(entry, ToolEntry), \
        f"register_tool: expected ToolEntry, got {type(entry).__name__}"
    assert entry.name, "register_tool: entry.name must be non-empty"
    existing = _REGISTRY.get(entry.name)
    if existing is None:
        _REGISTRY[entry.name] = entry
        return
    if existing == entry:
        return  # idempotent re-registration; silent
    raise ToolSchemaConflictError(
        f"tool {entry.name!r} already registered by owner "
        f"{existing.owner!r} (category {existing.category!r}); "
        f"re-registration by owner {entry.owner!r} would change content"
    )


def register_profile_tools(
    profile_name: str, entries: List[ToolEntry]
) -> None:
    """Register a batch of tool entries contributed by a profile.

    All entries' ``owner`` must equal ``profile_name`` — enforced
    here so the profile loader can't accidentally pass a profile's
    tool entries with the wrong owner tag set.

    Raises :class:`ToolSchemaValidationError` on owner mismatch,
    :class:`ToolSchemaConflictError` on name collision (see
    :func:`register_tool`).
    """
    assert profile_name, "profile_name must be non-empty"
    assert isinstance(entries, list), \
        f"entries must be list, got {type(entries).__name__}"
    for entry in entries:
        if entry.owner != profile_name:
            raise ToolSchemaValidationError(
                f"profile {profile_name!r} tried to register tool "
                f"{entry.name!r} with owner {entry.owner!r}; the owner "
                f"tag must match the registering profile's name"
            )
    for entry in entries:
        register_tool(entry)


def unregister_profile_tools(profile_name: str) -> int:
    """Remove every registered tool whose owner matches `profile_name`.

    Used by the profile loader when a profile is deactivated (e.g.
    smoke-test failure during re-validation). Returns the number of
    entries removed.
    """
    assert profile_name, "profile_name must be non-empty"
    to_remove = [n for n, e in _REGISTRY.items() if e.owner == profile_name]
    for n in to_remove:
        del _REGISTRY[n]
    return len(to_remove)


def get_tool_schema() -> ToolSchema:
    """Return the full tool-schema view assembled from all registered
    entries. srmech's own tools are listed first (in registration
    order); profile-contributed tools follow, grouped by owner
    (registration order within each profile)."""
    from .. import __version__ as srmech_version
    srmech_tools = tuple(e for e in _REGISTRY.values() if e.owner == "srmech")
    profile_tools = tuple(e for e in _REGISTRY.values() if e.owner != "srmech")
    return ToolSchema(
        srmech_version=srmech_version,
        tool_schema_version=TOOL_SCHEMA_VERSION,
        tools=srmech_tools + profile_tools,
    )


def tool_schema_view() -> Dict[str, Any]:
    """Convenience: return :func:`get_tool_schema` rendered as a
    JSON-serialisable dict. Used by the eventual `srmech --tool-schema`
    CLI invocation."""
    return get_tool_schema().to_jsonable()


# ──────────────────────────────────────────────────────────────────────
# TOML loader (for profile extension files)
#
# Used by the profile loader (Task #199). Reads a profile's
# extension file and returns a list of ToolEntry suitable for
# register_profile_tools.
#
# Schema (TOML):
#
#   [[tools]]
#   name = "chess.piece_graph_spectrum"
#   category = "spectrum"
#   summary = "Compute the spectrum of the chess piece-coupling graph"
#
#   [[tools.parameters]]
#   name = "board_id"
#   type = "str"
#   required = true
#
#   [tools.returns]
#   type = "list[float]"
#   shape = "13 channel eigenvalues"
#
#   [tools.smoke_test_hint]
#   board_id = "start"
# ──────────────────────────────────────────────────────────────────────


def load_extension_file(
    path: str, *, owner: str
) -> List[ToolEntry]:
    """Parse a profile's tool_schema extension TOML and return the
    list of :class:`ToolEntry` ready for :func:`register_profile_tools`.

    `owner` is stamped on every entry so the loader can't accidentally
    drop the profile-name tag.
    """
    assert path, "path must be non-empty"
    assert owner, "owner must be non-empty"

    with open(path, "rb") as f:
        data = tomllib.load(f)

    raw_tools = data.get("tools", [])
    if not isinstance(raw_tools, list):
        raise ToolSchemaValidationError(
            f"{path}: top-level 'tools' must be an array of tables"
        )

    out: List[ToolEntry] = []
    for i, raw in enumerate(raw_tools):
        if not isinstance(raw, dict):
            raise ToolSchemaValidationError(
                f"{path}: tools[{i}] must be a table"
            )
        for required in ("name", "category", "summary"):
            if required not in raw:
                raise ToolSchemaValidationError(
                    f"{path}: tools[{i}] missing required field {required!r}"
                )

        params = tuple(
            ToolParameter(
                name=p["name"],
                type=p["type"],
                required=p.get("required", True),
                summary=p.get("summary", ""),
            )
            for p in raw.get("parameters", [])
        )

        returns_raw = raw.get("returns")
        returns = None
        if returns_raw is not None:
            returns = ToolReturn(
                type=returns_raw["type"],
                shape=returns_raw.get("shape", ""),
            )

        out.append(
            ToolEntry(
                name=raw["name"],
                owner=owner,
                category=raw["category"],
                summary=raw["summary"],
                parameters=params,
                returns=returns,
                smoke_test_hint=raw.get("smoke_test_hint"),
                example=raw.get("example"),
            )
        )

    return out


# ──────────────────────────────────────────────────────────────────────
# srmech's own tool entries — registered at AMSC import time
# ──────────────────────────────────────────────────────────────────────


def _register_amsc_tools() -> None:
    """Register the AMSC framework's own tool entries. Called at
    import time by :mod:`srmech.amsc.__init__`."""
    entries: List[ToolEntry] = [
        ToolEntry(
            name="srmech.amsc.format.sha256_bytes",
            owner="srmech",
            category="format",
            summary="SHA-256 over raw bytes; returns 64-char lowercase hex. "
                    "Native C dispatch when available, hashlib fallback. "
                    "Used by every adapter's attest() step.",
            parameters=(
                ToolParameter("data", "bytes", required=True,
                              summary="Bytes to hash"),
            ),
            returns=ToolReturn(type="str", shape="64-char lowercase hex"),
            smoke_test_hint={"data": "b''"},
            example={
                "input": {"data": "b'abc'"},
                "output": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            },
        ),
        ToolEntry(
            name="srmech.amsc.format.sha256_batch",
            owner="srmech",
            category="format",
            summary="N-WAY SIMD SHA-256 of MANY messages at once (F292 "
                    "graft #1; v0.7.0rc10) — reach for this for BULK "
                    "attestation (fingerprint a whole catalog of upstream "
                    "response bytes in one call). Returns one 64-char "
                    "lowercase hex digest per input, each byte-identical to "
                    "sha256_bytes(d). A throughput surface, NOT a new "
                    "content-address shape. Native C dispatches to AVX2 "
                    "8-way / SSE2 4-way on x86 (scalar elsewhere); hashlib "
                    "fallback. SCOPE: energy/perf of srmech's own hashing — "
                    "NOT mining (SHA-256 has no PoW shortcut).",
            parameters=(
                ToolParameter("datas", "list[bytes]", required=True,
                              summary="The messages to hash"),
            ),
            returns=ToolReturn(type="list[str]",
                               shape="one 64-char lowercase hex digest per input"),
            smoke_test_hint={"datas": "[b'', b'abc']"},
            example={
                "input": {"datas": "[b'abc']"},
                "output": "['ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad']",
            },
        ),
        ToolEntry(
            name="srmech.amsc.format.read_ndjson",
            owner="srmech",
            category="format",
            summary="Stream MPRRecords line-by-line from an NDJSON file. "
                    "Native C dispatch for IO + line tokenisation when "
                    "available; stdlib fallback otherwise. JSON parsing "
                    "stays in Python." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                ToolParameter("path", "pathlib.Path", required=True,
                              summary="Path to an MPR-format NDJSON file"),
            ),
            returns=ToolReturn(
                type="Iterator[MPRRecord]",
                shape="Yields one MPRRecord per non-empty line",
            ),
        ),
        ToolEntry(
            name="srmech.amsc.descriptor.descriptor_hash",
            owner="srmech",
            category="descriptor",
            summary="SHA-256 over the canonical-serialised content of a "
                    "TOML descriptor. Insulated from whitespace / comment / "
                    "key-ordering changes by re-emitting parsed TOML with "
                    "sort_keys=True before hashing.",
            parameters=(
                ToolParameter("path", "pathlib.Path", required=True,
                              summary="Path to a TOML descriptor file"),
            ),
            returns=ToolReturn(type="str", shape="64-char lowercase hex"),
        ),
        ToolEntry(
            name="srmech.amsc.catalog.list_attested_sources",
            owner="srmech",
            category="catalog",
            summary="List every attested-data source registered into srmech's "
                    "universal catalog bridge, with adapter-class filtering.",
            parameters=(
                ToolParameter(
                    "adapter_class", "Optional[str]", required=False,
                    summary="Optional adapter-class filter "
                            "('fetched' or 'curated')",
                ),
            ),
            returns=ToolReturn(
                type="dict",
                shape="{'sources': [{source_key, name, license, ...}], 'n_sources': int}",
            ),
        ),
        ToolEntry(
            name="srmech.amsc.catalog.get_attested_dataset",
            owner="srmech",
            category="catalog",
            summary="Paginated read of an attested dataset's rows. T0+T1+T2+T3 "
                    "tiered: committed baseline + collect re-bake + user "
                    "runtime kernel + live query." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                ToolParameter("source_key", "str", required=True),
                ToolParameter("limit", "Optional[int]", required=False),
                ToolParameter("offset", "int", required=False),
            ),
            returns=ToolReturn(
                type="dict",
                shape="{'ok': bool, 'rows': list, 'total': int, 'next_offset': int}",
            ),
        ),
        ToolEntry(
            name="srmech.amsc.catalog.register_attested_root",
            owner="srmech",
            category="catalog",
            summary="Register a cross-package catalog SSOT root with srmech's "
                    "universal bridge. Used by downstream packages at import "
                    "time. Conflict policy: first-registered wins with warning.",
            parameters=(
                ToolParameter("path", "pathlib.Path", required=True,
                              summary="Path to the attested-data root"),
                ToolParameter("source", "str", required=True,
                              summary="Source label / package identifier"),
            ),
            returns=ToolReturn(type="None", shape=""),
        ),
        # ADR-0002 Phase 2 — operator-chain bridge surfaces (v0.4.1rc5).
        ToolEntry(
            name="srmech.amsc.catalog.list_catalog_chains", owner="srmech",
            category="catalog",
            summary="Enumerate [[catalog.operator_chain]] entries declared "
                    "by a registered catalog descriptor. ADR-0002 Phase 2 "
                    "bridge surface.",
            parameters=(ToolParameter("source_key", "str", required=True,
                                      summary="[source].key from descriptor"),),
            returns=ToolReturn(type="dict",
                               shape="{ok, source_key, n_chains, chains}"),
        ),
        ToolEntry(
            name="srmech.amsc.catalog.run_catalog_chain", owner="srmech",
            category="catalog",
            summary="Execute a declared operator chain on a catalog row. "
                    "ADR-0002 Phase 2 bridge surface; runs the linear "
                    "pipeline of class-op calls with @row.* / @input.* / "
                    "@step[N].output / @catalog.* reference resolution.",
            parameters=(
                ToolParameter("source_key", "str", required=True),
                ToolParameter("chain_name", "str", required=True),
                ToolParameter("row_index", "Optional[int]", required=False,
                              summary="row binding for @row.* refs"),
                ToolParameter("inputs", "Optional[dict]", required=False,
                              summary="runtime @input.* parameters"),
            ),
            returns=ToolReturn(type="Any",
                               shape="chain's `returns` type"),
        ),
        # ADR-0002 Phase 2 — composition engine surfaces.
        ToolEntry(
            name="srmech.amsc.compose.parse_chain_spec", owner="srmech",
            category="compose",
            summary="Parse and validate one [[catalog.operator_chain]] "
                    "entry into a ChainSpec.",
            parameters=(ToolParameter("chain_dict", "dict", required=True,
                                      summary="TOML-parsed chain entry"),),
            returns=ToolReturn(type="ChainSpec", shape=""),
        ),
        ToolEntry(
            name="srmech.amsc.compose.parse_catalog_chains", owner="srmech",
            category="compose",
            summary="Parse all [[catalog.operator_chain]] entries from a "
                    "catalog descriptor TOML dict. Requires "
                    "chain_schema_version = 1.",
            parameters=(ToolParameter("toml_dict", "dict", required=True),),
            returns=ToolReturn(type="list[ChainSpec]", shape=""),
        ),
        ToolEntry(
            name="srmech.amsc.compose.resolve_chain", owner="srmech",
            category="compose",
            summary="Resolve a ChainSpec to a callable by binding each "
                    "step's class.op against the registry. Raises "
                    "ChainSpecError on missing op.",
            parameters=(ToolParameter("spec", "ChainSpec", required=True),
                        ToolParameter("registry", "Optional[dict]",
                                      required=False,
                                      summary="class_id → module path map")),
            returns=ToolReturn(type="Callable", shape="run(row, **inputs)"),
        ),
        ToolEntry(
            name="srmech.amsc.compose.run_chain", owner="srmech",
            category="compose",
            summary="Top-level executor: resolve a ChainSpec and run its "
                    "linear pipeline. Returns the final step's output.",
            parameters=(ToolParameter("spec", "ChainSpec", required=True),
                        ToolParameter("row", "Optional[dict]", required=False),
                        ToolParameter("inputs", "Optional[dict]",
                                      required=False),
                        ToolParameter("registry", "Optional[dict]",
                                      required=False)),
            returns=ToolReturn(type="Any", shape="chain's `returns` type"),
        ),
    ]
    for e in entries:
        register_tool(e)


def _register_primitive_class_tools() -> None:
    """Register tool entries for the 14 Spike #24 primitive classes
    (Task #217 Phase C1 / Task #220).

    Class A (content-addressing) + Class C (streaming) are already covered
    by ``_register_amsc_tools()`` (sha256_bytes + read_ndjson). This
    function adds the remaining 12 classes (B, D, E, F, G, H, I, J, K, L,
    M, N) — every primitive-class operation exposed via ``srmech.amsc.*``.
    """
    P = ToolParameter
    R = ToolReturn

    entries: List[ToolEntry] = [
        # ────────────────────────────────────────────────────────────
        # Class I — cyclic-group / modular arithmetic
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.cyclic.gcd", owner="srmech", category="cyclic",
            summary="Greatest common divisor of two non-negative integers.",
            parameters=(P("a", "int", True), P("b", "int", True)),
            returns=R("int", "≥ 0"),
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.lcm", owner="srmech", category="cyclic",
            summary="Least common multiple of two non-negative integers; "
                    "0 when either input is 0.",
            parameters=(P("a", "int", True), P("b", "int", True)),
            returns=R("int", "≥ 0"),
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.mod_add", owner="srmech", category="cyclic",
            summary="(a + b) mod n — overflow-safe modular addition.",
            parameters=(P("a", "int", True), P("b", "int", True),
                        P("n", "int", True, "modulus > 0")),
            returns=R("int", "in [0, n)"),
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.mod_mul", owner="srmech", category="cyclic",
            summary="(a * b) mod n via russian-peasant doubling; portable "
                    "across platforms without __int128.",
            parameters=(P("a", "int", True), P("b", "int", True),
                        P("n", "int", True, "modulus > 0")),
            returns=R("int", "in [0, n)"),
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.mod_pow", owner="srmech", category="cyclic",
            summary="(a ** k) mod n via square-and-multiply.",
            parameters=(P("a", "int", True), P("k", "int", True),
                        P("n", "int", True, "modulus > 0")),
            returns=R("int", "in [0, n)"),
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.mod_inv", owner="srmech", category="cyclic",
            summary="Modular inverse of a in Z/nZ via extended Euclidean. "
                    "Requires gcd(a, n) == 1 and n ≤ INT64_MAX.",
            parameters=(P("a", "int", True), P("n", "int", True)),
            returns=R("int", "in [1, n)"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class L — graph Laplacian
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.dense_adjacency", owner="srmech",
            category="laplacian",
            summary="Build the dense adjacency matrix from an edge list. "
                    "Self-loops add 2w to the diagonal (standard convention).",
            parameters=(P("n", "int", True, "number of nodes"),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False,
                          "None ⇒ unit weights")),
            returns=R("Mat", "n × n dense matrix (numpy-free 2-D carrier)"),
        ),
        # §40 (rc50): the text→graph stage primitives — the K1 chain's missing
        # front, now in srmech.amsc.text (ingestion module; laplacian stays
        # purely spectral). `tokenize → cooccurrence_edges → dense_laplacian → …`
        # authorable end-to-end; retires the hand-rolled Counter() idiom. The
        # rc43 versions FAILED the §40 acceptance bar 3/3 (ASCII tokenize /
        # silent vocab cap / no doc-boundary reset) — rc50 fixes all three.
        # Both pure-Python.
        ToolEntry(
            name="srmech.amsc.text.tokenize", owner="srmech",
            category="text",
            summary="Segment text into casefolded Unicode content tokens (Class "
                    "B/G text-segmentation; §40/F698): keep runs of Unicode "
                    "letter|mark codepoints (so café / Москва / 日本語 survive, "
                    "NOT an ASCII word pattern), casefold, drop length<2 or "
                    "stoplist words. NFC-normalises by default. The text→tokens "
                    "front of the K1 text→graph→spectral chain.",
            parameters=(P("text", "str", True),
                        P("stoplist", "list", False,
                          "function words to drop (casefolded); default "
                          "DEFAULT_STOPLIST. None/empty = raw mode"),
                        P("unicode_normalize", "bool", False,
                          "NFC-normalise text first (default True)")),
            returns=R("list[str]", "casefolded Unicode content-token stream"),
        ),
        ToolEntry(
            name="srmech.amsc.text.cooccurrence_edges", owner="srmech",
            category="text",
            summary="Weighted co-occurrence graph from documents (Class-L "
                    "precursor; §40): slide a window over EACH document (resets "
                    "at every document boundary — never crosses one), count "
                    "unordered co-occurring vocab pairs. vocab is the FULL ranked "
                    "vocabulary by default (no silent cap — F708 fix); a top-K "
                    "vocab_size cap is an explicit, logged opt-in. Returns "
                    "(n, edges, weights) for dense_laplacian; retires Counter().",
            parameters=(P("docs", "list", True,
                          "Sequence[Sequence[str]] (one per document; window "
                          "resets per doc) or a flat token Sequence[str]"),
                        P("window", "int", False, "co-occurrence window (default 2)"),
                        P("vocab", "list", False,
                          "explicit ranked vocab (index=position); None builds "
                          "the full vocab from frequency"),
                        P("vocab_size", "int", False,
                          "explicit top-K cap (logged); None = no cap (all)")),
            returns=R("tuple[int, list[tuple[int, int]], list[int]]",
                      "(n nodes, edge list, integer co-occurrence counts)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.dense_laplacian", owner="srmech",
            category="laplacian",
            summary="Graph Laplacian L = D - A. Native C dispatch when "
                    "n ≤ 256; numpy fallback otherwise.",
            # rc15: declare `edges` as list[tuple[int, int]] (matching the
            # shipped `dense_laplacian(n, edges: Iterable[Tuple[int, int]])`
            # signature + the sibling `dense_adjacency` entry). The earlier
            # bare `list` type advertised an edge-list shape too loose for an
            # LLM to populate correctly — surfaced by the rc15 every-tool
            # invocation smoke (a bare-`list` synth fed [1, 2] tripped the
            # op's 2-tuple unpack). Schema-accuracy fix only; signature
            # unchanged.
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False)),
            returns=R("Mat", "n × n symmetric matrix (numpy-free 2-D carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.normalized_laplacian", owner="srmech",
            category="laplacian",
            summary="Symmetric normalized Laplacian L_sym = I - D^{-1/2} A D^{-1/2}. "
                    "Isolated vertices have diagonal entry 0.",
            # rc15: declare `edges` as list[tuple[int, int]] (matching the
            # shipped signature + the dense_adjacency entry). Schema-accuracy
            # fix surfaced by the rc15 every-tool invocation smoke; signature
            # unchanged.
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False)),
            returns=R("Mat", "n × n symmetric matrix (numpy-free 2-D carrier)"),
        ),
        # #797 op (b): directed / signed Laplacian (rc26). The dissolved
        # Class-O signed-metric absorbed into L + the directed-navigation
        # leg (magnetic / Hermitian Laplacian). Heavy eigen runs on the
        # existing native symmetric/hermitian solvers; the standalone-C
        # builder peers are the tracked next voxel.
        ToolEntry(
            name="srmech.amsc.laplacian.signed_laplacian", owner="srmech",
            category="laplacian",
            summary="Signed graph Laplacian L = D̄ − A (real-symmetric, PSD); "
                    "off-diagonal weights may be negative. Signed degree "
                    "D̄_ii = Σ|A_ij| is the Class-K magnitude of the "
                    "signed-metric (the dissolved Class O, now a Class-L "
                    "sub-op). Kunegis et al. (2010).",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False,
                          "may be negative")),
            returns=R("Mat", "n × n real-symmetric PSD signed Laplacian (numpy-free Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.magnetic_laplacian", owner="srmech",
            category="laplacian",
            summary="Magnetic (Hermitian) Laplacian of a DIRECTED graph "
                    "(#797 op (b)): direction encoded as phase "
                    "exp(i·2π·q·(W−Wᵀ)) so the graph stays Hermitian and "
                    "hermitian_eigendecompose diagonalises it; the complex "
                    "eigenpair is the directed-navigation signature. q=0 → "
                    "real symmetrised Laplacian (undirected control).",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True,
                          "directed u → v"),
                        P("weights", "Optional[list[float]]", False),
                        P("q", "float", False,
                          "flux in turns per unit net flow; default 0.25")),
            returns=R("Mat", "n × n complex Hermitian matrix (numpy-free Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.fiedler_vector", owner="srmech",
            category="laplacian",
            summary="The Fiedler navigation embedding: eigenvector of the "
                    "second-smallest eigenvalue (λ₂) of a Laplacian. "
                    "Dispatches real→symmetric_eigendecompose, "
                    "complex→hermitian_eigendecompose (both native).",
            parameters=(P("matrix", "Mat", True,
                          "n × n real-symmetric or complex-Hermitian Laplacian"),),
            returns=R("Vec", "length-n λ₂ eigenvector (numpy-free 1-D carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.jacobi_eigvals", owner="srmech",
            category="laplacian",
            summary="Symmetric Jacobi eigendecomposition; pi-free closed-form "
                    "c/s computation. Native C dispatch when n ≤ 256.",
            parameters=(P("matrix", "Mat", True, "n × n symmetric"),
                        P("max_sweeps", "int", False, "default 100"),
                        P("tolerance", "float", False)),
            returns=R("Vec", "n eigenvalues ascending (numpy-free 1-D carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.spectral_block_dispatch", owner="srmech",
            category="laplacian",
            summary="The 1024-node 4-sector spectral one-call (RBS-LM Ask-3; "
                    "F233 4-rung): eigendecompose ≤4 dense symmetric blocks "
                    "(each n ≤ 256) on a 4-worker thread pool — the threaded-"
                    "Klein-4-streams pattern. 4 × 256 = 1024 nodes within the "
                    "native dense-eig bound. Each block on its own thread (0 "
                    "cross-thread reads → parallel == serial bit-for-bit). "
                    "Class L over the 4-rung parallel dispatch; numpy-free.",
            parameters=(
                P("blocks", "list", True, "1..4 symmetric matrices, each n ≤ 256"),
                P("max_sweeps", "int", False, "per-block, default 100"),
                P("tolerance", "float", False),
                P("combine", "bool", False, "also return merged-sorted spectrum"),
            ),
            returns=R("dict", "{ok, n_blocks, block_sizes, n_nodes, "
                              "blocks (per-block Vec spectra), combined (Vec)}"),
        ),
        # v0.7.1rc3 (#897 §26): the reusable dense linear solve A·X = B the
        # Schur/DtN float path composes over (its interior solve IS an
        # A·X = B). Native C peer srmech_dense_solve_f64_ws (Gauss–Jordan,
        # partial pivoting, augmented [A|B] scratch from a caller arena — no
        # size cap, rc158 standalone-complete honor); exact-rational Fraction
        # Gauss–Jordan numpy-absent / exact=True. Golub & Van Loan §3.
        ToolEntry(
            name="srmech.amsc.laplacian.dense_solve", owner="srmech",
            category="laplacian",
            summary="Class-L dense linear solve A·X = B (A n×n; B/X n×w matrix "
                    "or length-n vector). The reusable solve schur_complement "
                    "composes over. Native C peer (Gauss–Jordan, partial "
                    "pivoting, n,w ≤ 256) on the scientific tier; exact-rational "
                    "Fraction solve (Class-N core, numpy-absent or exact=True).",
            parameters=(P("A", "Mat", True,
                          "n × n coefficient matrix; nested JSON list over MCP"),
                        P("B", "Mat | Vec", True,
                          "right-hand side: n × w matrix or length-n vector"),
                        P("exact", "bool", False,
                          "force the exact Fraction solve (default False)")),
            returns=R("Mat | Vec | list[list[Fraction]] | list[Fraction]",
                      "X solving A·X = B (shape of B)"),
        ),
        # UPSTREAM §26 (#897): the Schur complement / Dirichlet-to-Neumann
        # map — the operator|operand FUSION op (F412/F417/F419). Canonical
        # SSoT: Zhang, *The Schur Complement and Its Applications* (2005) §0;
        # Golub & Van Loan §3.2.
        ToolEntry(
            name="srmech.amsc.laplacian.schur_complement", owner="srmech",
            category="laplacian",
            summary="Class-L Schur complement / discrete Dirichlet-to-Neumann "
                    "map S = L_∂∂ − L_∂i·L_ii⁻¹·L_i∂ (the bulk integrated out; "
                    "the operator|operand FUSION op). Exact-rational Fraction "
                    "solve (Class-N core, numpy-absent or exact=True); "
                    "NumPy solve float realization on the scientific tier.",
            parameters=(P("L", "Mat", True,
                          "n × n SPD operator (a graph Laplacian); nested JSON "
                          "list over MCP"),
                        P("boundary_idx", "list[int]", True,
                          "boundary node indices ∂ (1 ≤ |∂| ≤ n)"),
                        P("exact", "bool", False,
                          "force the exact Fraction solve (default False)")),
            returns=R("Mat | list[list[Fraction]]",
                      "|∂| × |∂| boundary effective operator (DtN map)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.dirichlet_to_neumann", owner="srmech",
            category="laplacian",
            summary="Alias for schur_complement — the discrete "
                    "Dirichlet-to-Neumann map: boundary values ⟹ the boundary "
                    "normal-derivative of their harmonic interior extension.",
            parameters=(P("L", "Mat", True,
                          "n × n SPD operator (a graph Laplacian); nested JSON "
                          "list over MCP"),
                        P("boundary_idx", "list[int]", True,
                          "boundary node indices ∂ (1 ≤ |∂| ≤ n)"),
                        P("exact", "bool", False,
                          "force the exact Fraction solve (default False)")),
            returns=R("Mat | list[list[Fraction]]",
                      "|∂| × |∂| boundary effective operator (DtN map)"),
        ),
        # ADR-0002 Phase 2 broadening: complex Hermitian + matvec +
        # elementwise complex multiply + array-vectorised transcendentals.
        # Per [[feedback_no_privileged_primitive_classes]] these dissolve
        # into Class L (no new class promoted). Canonical SSoT: Golub &
        # Van Loan §1.1 / §8.5; ANSI C99 §7.12 libm; Sakurai §2.1.5.
        ToolEntry(
            name="srmech.amsc.laplacian.hermitian_eigendecompose",
            owner="srmech", category="laplacian",
            summary="Hermitian eigendecomposition H = V diag(eigvals) V^H "
                    "via complex-Jacobi rotations. Native C dispatch when "
                    "n ≤ 256; NumPy eigh fallback. Sakurai §2.1.5; "
                    "Golub & Van Loan §8.5.",
            parameters=(P("H", "Mat", True,
                          "n × n complex Hermitian matrix"),),
            returns=R("tuple[Vec, Mat]",
                      "(eigvals_ascending Vec, V_unitary complex Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.symmetric_eigendecompose",
            owner="srmech", category="laplacian",
            summary="Real-symmetric eigendecomposition L = V diag(eigvals) "
                    "Vᵀ via NumPy eigh. Real-input specialisation of "
                    "hermitian_eigendecompose: guarantees real float64 "
                    "eigvals AND eigvecs (no ComplexWarning for a real "
                    "Laplacian). Golub & Van Loan §8.3.",
            parameters=(P("L", "Mat", True,
                          "n × n real symmetric matrix"),),
            returns=R("tuple[Vec, Mat]",
                      "(eigvals_ascending Vec, V_orthogonal real Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_matmul",
            owner="srmech", category="laplacian",
            summary="Numpy-FREE dense matrix multiply A times B over the Mat "
                    "carrier (carrier-removal #564): Mat.buffer feeds the native "
                    "srmech_dense_matmul_complex zero-copy (real interleaved "
                    "once), pure-Python triple-loop fallback with no native lib. "
                    "Golub & Van Loan §1.1.",
            parameters=(P("a", "Mat", True, "m × k (real or complex) Mat"),
                        P("b", "Mat", True, "k × n (real or complex) Mat")),
            returns=R("Mat", "m × n Mat (complex iff either input is)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_solve",
            owner="srmech", category="laplacian",
            summary="Numpy-FREE dense linear solve A·X = B over the Mat carrier "
                    "(carrier-removal #564): real Mat.buffers feed the native "
                    "srmech_dense_solve_f64_ws zero-copy; exact-rational "
                    "Gauss-Jordan fallback with no native lib. Complex A/B route "
                    "through the real 2n×2n block embedding (rc95), riding the "
                    "same native real solve. Golub & Van Loan §3.4.",
            parameters=(P("a", "Mat", True, "n × n real or complex Mat (square)"),
                        P("b", "Mat", True, "n × w real or complex Mat (rhs)")),
            returns=R("Mat", "n × w Mat solution X (complex iff inputs are)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_lstsq",
            owner="srmech", category="laplacian",
            summary="Numpy-FREE least-squares A·X ≈ B over the Mat carrier "
                    "(carrier-removal #564): the normal equations "
                    "X = solve(A^H·A, A^H·B) composed from the native mat_matmul "
                    "and mat_solve trio (complex-capable via rc95), real and "
                    "complex. Overdetermined/square m>=n, full column rank. "
                    "Golub & Van Loan §5.3.",
            parameters=(P("a", "Mat", True, "m × n real or complex Mat (m >= n)"),
                        P("b", "Mat", True, "m × w real or complex Mat (rhs)")),
            returns=R("Mat", "n × w Mat solution X (complex iff inputs are)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_hermitian_eigendecompose",
            owner="srmech", category="laplacian",
            summary="Numpy-FREE Hermitian eigendecomposition H = V diag(λ) V^H "
                    "over the Mat carrier (carrier-removal #564, bridge #3): "
                    "Mat.buffer feeds the native srmech_hermitian_eigendecompose_ws "
                    "zero-copy; pure-Python cyclic-Jacobi fallback with no native "
                    "lib (real-symmetric direct, complex-Hermitian via the real "
                    "2n×2n embedding). Golub & Van Loan §8.5.",
            parameters=(P("h", "Mat", True,
                          "n × n Hermitian Mat (real-symmetric or complex)"),),
            returns=R("tuple[Mat, Mat]",
                      "(eigvals (n,1) real Mat ascending, eigvecs (n,n) "
                      "complex unitary Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_eigvals",
            owner="srmech", category="laplacian",
            summary="Numpy-FREE eigenvalue multiset of a general (non-Hermitian) "
                    "square matrix over the Mat carrier (carrier-removal #564, "
                    "foundation #4): a Wilkinson-shifted QR iteration in plain "
                    "complex with per-step Householder QR and the RQ recombine "
                    "routed through the native mat_matmul; n=1/2 closed form. "
                    "Multiset matches NumPy eigvals to ~1e-9. Prefer "
                    "mat_hermitian_eigendecompose for Hermitian A. Golub & Van "
                    "Loan §7.5.",
            parameters=(P("a", "Mat", True,
                          "n × n real or complex Mat (square, any non-Hermitian)"),),
            returns=R("list[complex]",
                      "length-n eigenvalue multiset (unique only as a set)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_svd",
            owner="srmech", category="laplacian",
            summary="Numpy-FREE FULL singular-value decomposition A = U diag(S) "
                    "V^H over the Mat carrier (carrier-removal #564, foundation "
                    "#5): the right vectors are eigenvectors of the Hermitian PSD "
                    "Gram A^H·A via mat_hermitian_eigendecompose, S = sqrt(lambda) "
                    "(Class-N rational.sqrt), the left vectors are u_j = A·v_j/s_j "
                    "with an orthonormal Gram-Schmidt completion of the null block. "
                    "Value-faithful (reconstruction + S match) NOT bit-identical "
                    "(SVD null/degenerate basis is free); large S ~1e-9, small ~1e-7 "
                    "— do not route a matrix_rank consumer here. Golub & Van Loan "
                    "§8.6.",
            parameters=(P("a", "Mat", True,
                          "m × n real or complex Mat (the matrix to decompose)"),),
            returns=R("tuple",
                      "(U (m,m) complex Mat, S list[float] descending len min(m,n), "
                      "Vh (n,n) complex Mat) matching full_matrices=True"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_norm",
            owner="srmech", category="laplacian",
            summary="numpy-FREE Euclidean (2-norm) / Frobenius norm sqrt(sum "
                    "|x_i|^2) → float over the Mat / HV carrier: Class N (rational "
                    "sqrt) of the Class M self-bind sum|x|^2 (pure-Python reduction, "
                    "complex |z|^2 = re^2+im^2, no abs). The numpy-absent peer of "
                    "dense_norm (which is a numpy carrier). Golub & Van Loan §2.3.",
            parameters=(P("x", "Mat", True,
                          "Mat / HV / flat real-or-complex sequence (flattened)"),),
            returns=R("float", "sqrt(sum |x_i|^2)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_dot",
            owner="srmech", category="laplacian",
            summary="numpy-FREE dtype-polymorphic bilinear inner product sum "
                    "a_i b_i over the Mat / Vec / HV carriers: float for real "
                    "operands, complex if either is complex (plain bilinear, NOT "
                    "the conjugating vdot). The single consolidated dot (v0.7.6 "
                    "carrier consolidation, unifies the rc114 real/complex split). "
                    "Golub & Van Loan §1.1.",
            parameters=(P("a", "Mat", True, "Mat / Vec / HV / flat sequence"),
                        P("b", "Mat", True, "Mat / Vec / HV / flat sequence")),
            returns=R("float", "scalar sum a_i b_i (complex when either operand is complex)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_matvec",
            owner="srmech", category="laplacian",
            summary="numpy-FREE dtype-polymorphic dense matrix-vector product "
                    "M times v over the Mat / Vec carriers (complex iff either "
                    "operand is): rides mat_matmul over a column Mat. The single "
                    "consolidated matvec (v0.7.6 carrier consolidation). Golub & "
                    "Van Loan §1.1.",
            parameters=(P("m", "Mat", True, "rows x cols (real or complex)"),
                        P("v", "Vec", True, "length-cols (real or complex)")),
            returns=R("Vec", "length-rows Vec (complex iff either input is)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.mat_outer",
            owner="srmech", category="laplacian",
            summary="numpy-FREE dtype-polymorphic outer product a-tensor-b -> "
                    "out[i,j]=a_i b_j over the Mat / Vec carriers (complex iff "
                    "either operand is). Plain bilinear, does NOT conjugate b. The "
                    "single consolidated outer (v0.7.6 carrier consolidation). "
                    "Golub & Van Loan §1.1.",
            parameters=(P("a", "Vec", True, "length-m (real or complex) column"),
                        P("b", "Vec", True, "length-n (real or complex) row")),
            returns=R("Mat", "m x n a_i b_j (complex iff either input is)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.elementwise_multiply_complex",
            owner="srmech", category="laplacian",
            summary="Elementwise complex multiplication a * b (equal-shape; "
                    "shape-polymorphic — Mat in → Mat out, Vec in → Vec out).",
            parameters=(P("a", "Mat | Vec", True, "Mat (2-D) or Vec (1-D) complex"),
                        P("b", "Mat | Vec", True, "same-shape complex operand")),
            returns=R("Mat", "Mat (2-D in) or Vec (1-D in), complex; rank-preserving"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.elementwise_transcendental",
            owner="srmech", category="laplacian",
            summary="Array-vectorised transcendental: exp / cos / sin / "
                    "log over real input, or exp_i(x) = exp(1j*x) "
                    "(TDSE-relevant complex exponential). Shape-polymorphic "
                    "(Mat in → Mat out, Vec in → Vec out). ANSI C99 §7.12.",
            parameters=(P("arr", "Mat | Vec", True, "Mat (2-D) or Vec (1-D) real/complex"),
                        P("op_name", "str", True,
                          "exp / cos / sin / log / exp_i")),
            returns=R("Mat",
                      "Mat/Vec (rank-preserving); complex for exp_i/complex input"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.elementwise_hypot",
            owner="srmech", category="laplacian",
            summary="Array Euclidean magnitude sqrt(a_i^2 + b_i^2) via the "
                    "Class-N hypot cascade (per-element rational.hypot; native "
                    "srmech_rational_sqrt-dispatched). The numpy-free |z| = "
                    "sqrt(re^2+im^2) op the DSP modules route through — numpy "
                    "carries the array only. Golub & Van Loan §1.1.",
            parameters=(P("a", "Mat | Vec", True, "Mat (2-D) or Vec (1-D) real (e.g. z.real)"),
                        P("b", "Mat | Vec", True, "same-shape real (e.g. z.imag)")),
            returns=R("Mat", "Mat/Vec sqrt(a_i^2 + b_i^2) (rank-preserving real carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.elementwise_sqrt",
            owner="srmech", category="laplacian",
            summary="Array element-wise sqrt(arr_i) via the Class-N rational "
                    "sqrt cascade (per-element rational.sqrt; native "
                    "srmech_rational_sqrt-dispatched). The numpy-free array "
                    "square-root op (companion to elementwise_hypot) for "
                    "non-negative reals — numpy carries the array only. Rejects "
                    "arr_i < 0. Golub & Van Loan §1.1.",
            parameters=(P("arr", "Mat | Vec", True,
                          "Mat (2-D) or Vec (1-D) real, all entries >= 0"),),
            returns=R("Mat", "Mat/Vec sqrt(arr_i), rank-preserving real carrier"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class J — prime-factorisation / period
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.primes.is_prime", owner="srmech", category="primes",
            summary="Trial-division primality test for n ≤ 2**64. False for n < 2.",
            parameters=(P("n", "int", True),),
            returns=R("bool", ""),
        ),
        ToolEntry(
            name="srmech.amsc.primes.factor", owner="srmech", category="primes",
            summary="Prime factorisation by trial division. Returns ascending "
                    "(prime, exponent) pairs. n < 2 returns empty list.",
            parameters=(P("n", "int", True),),
            returns=R("list[tuple[int, int]]", "[(prime, exponent), ...]"),
        ),
        ToolEntry(
            name="srmech.amsc.primes.cyclic_period", owner="srmech", category="primes",
            summary="Multiplicative order of a in (Z/nZ)*: smallest k > 0 "
                    "with a^k ≡ 1 (mod n). Requires gcd(a mod n, n) == 1.",
            parameters=(P("a", "int", True), P("n", "int", True),
                        P("max_k", "int", False)),
            returns=R("int", "≥ 1"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class B — tagged-tuple TLV
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.tlv.tlv_pack", owner="srmech", category="tlv",
            summary="Pack (tag, value) into [u8 tag][u32 length BE][value] "
                    "byte-canonical form. Wire-format-specific big-endian length.",
            parameters=(P("tag", "int", True, "0..255"),
                        P("value", "bytes", True)),
            returns=R("bytes", "5 + len(value) bytes"),
        ),
        ToolEntry(
            name="srmech.amsc.tlv.tlv_unpack", owner="srmech", category="tlv",
            summary="Read one TLV frame back out — the inverse of tlv_pack (Class B). Reads the [u8 tag][u32 length BE][value] frame beginning at offset and returns (tag, value, next_offset); feed next_offset back in to walk a concatenation of frames. Exact round-trip with tlv_pack: tlv_unpack(tlv_pack(t, v)) == (t, v, 5 + len(v)). Raises on a truncated prefix or a claimed length that runs past the end of the buffer — never returns partial data.",
            parameters=(P("buffer", "bytes", True, "the byte buffer holding one or more TLV frames"),
                        P("offset", "int", False, "where the frame begins (default 0); pass the returned next_offset to read the following frame")),
            returns=R("tuple", "(tag:int, value:bytes, next_offset:int)"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class G — discovery / search
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.search.byte_search", owner="srmech", category="search",
            summary="Find first occurrence of `needle` in `haystack`; "
                    "matches Python's `bytes.find(b'')` (empty needle ⇒ 0).",
            parameters=(P("haystack", "bytes", True), P("needle", "bytes", True)),
            returns=R("Optional[int]", "offset of match or None"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class D — late-binding dispatch
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.dispatch.match", owner="srmech", category="dispatch",
            summary="Multi-needle byte-pattern dispatcher. Returns first matching "
                    "rule's tag, or None on no match.",
            parameters=(P("input_bytes", "bytes", True),
                        P("rules", "list[tuple[bytes, int]]", True,
                          "[(pattern, tag), ...]")),
            returns=R("Optional[int]", "matched rule's tag"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class E — catalog / naming (primitive lookup)
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.naming.lookup", owner="srmech", category="naming",
            summary="Binary search over a sorted (key, value) catalog. Keys MUST "
                    "be pre-sorted ascending lexicographic by caller.",
            # rc13 drift fix: the param is `pairs` (the iterable of
            # (key, value) tuples) — the shipped `naming.lookup(key, pairs)`
            # signature. The earlier `entries` name made the tool uncallable
            # via MCP / Anthropic (TypeError: unexpected keyword 'entries').
            parameters=(P("key", "bytes", True),
                        P("pairs", "list[tuple[bytes, bytes]]", True,
                          "sorted (key, value) pairs")),
            returns=R("Optional[bytes]", "value or None"),
        ),

        # ────────────────────────────────────────────────────────────
        # F150 chirality-harmonic variants (rc12) + §2.2 alignment.
        # Per-operator harmonic classification + the chirality-aware
        # variants placed next to their base Class op (no privileged
        # namespace, per [[feedback_no_privileged_primitive_classes]]).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.harmonics.classify_harmonic", owner="srmech",
            category="harmonics",
            summary="Chirality-harmonic order (1/2/3) of an A–N class operator "
                    "(F150): H1=ABFHN invariant, H2=CDEGKM mirror, H3=IJL 3-cycle.",
            parameters=(P("class_letter", "str", True, "single A–N letter"),),
            returns=R("int", "harmonic order 1, 2, or 3"),
        ),
        ToolEntry(
            name="srmech.amsc.harmonics.classify_chirality_harmonic", owner="srmech",
            category="harmonics",
            summary="Classify an encoded hypervector into chirality-harmonic 1/2/3 "
                    "by its spectral symmetry signature (F150 §6.2).",
            parameters=(P("hv", "HV", True, "encoded vector"),
                        P("dc_threshold", "float", False)),
            returns=R("int", "harmonic order 1, 2, or 3"),
        ),
        ToolEntry(
            name="srmech.amsc.dispatch.mirror_pattern", owner="srmech",
            category="dispatch",
            summary="Harmonic-2 chiral mirror of a dispatch pattern (F150): the "
                    "byte-reversed needle; period-2 involution. Companion to match.",
            parameters=(P("pattern", "bytes", True),),
            returns=R("bytes", "byte-reversed pattern"),
        ),
        ToolEntry(
            name="srmech.amsc.naming.reverse_order", owner="srmech", category="naming",
            summary="Harmonic-2 chiral mirror of a sorted Class-E catalog (F150): "
                    "the order-reversed (key, value) list; period-2 involution.",
            parameters=(P("sorted_pairs", "list[tuple[bytes, bytes]]", True,
                          "sorted (key, value) pairs"),),
            returns=R("list", "order-reversed pairs"),
        ),
        ToolEntry(
            name="srmech.amsc.search.byte_search_backward", owner="srmech",
            category="search",
            summary="Harmonic-2 chiral mirror of byte_search (F150): offset of the "
                    "LAST occurrence of `needle` in `haystack`, or None.",
            parameters=(P("haystack", "bytes", True), P("needle", "bytes", True)),
            returns=R("Optional[int]", "offset of last match or None"),
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.three_cycle", owner="srmech", category="cyclic",
            summary="Harmonic-3 Z/3 cyclic shift (F150): (value+1)%3 on {0,1,2}; "
                    "period-3 order-3 generator. Companion to the modular ops.",
            parameters=(P("value", "int", True, "any non-negative int; read mod 3"),),
            returns=R("int", "(value + 1) % 3"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.three_fold_eigvec_groups", owner="srmech",
            category="laplacian",
            summary="Harmonic-3 three-fold spectral reading (F150): partition the "
                    "eigenvectors of a real-symmetric Laplacian into low/mid/high.",
            parameters=(P("L", "Mat", True, "real-symmetric matrix"),),
            returns=R("dict", "low/mid/high eigenvector bands (each a real Mat)"),
        ),
        # NOTE: srmech.amsc.compose.greedy_bipartite_alignment (§2.2) is NOT
        # registered — it takes a Python `similarity_fn` callable that cannot
        # cross the JSON-RPC boundary, so it is not an MCP tool. It is exempt
        # in tests/test_tool_schema_coverage.py::_EXEMPT_FUNCTION_NAMES.

        # ────────────────────────────────────────────────────────────
        # Class F — substitution / templating
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.template.render", owner="srmech", category="template",
            summary="Render a template with {key} placeholders. Plain bytes "
                    "pass through; unknown key raises ValueError.",
            # rc13 drift fix: the param is `mapping` (the bytes->bytes
            # substitution map) — the shipped `template.render(template_bytes,
            # mapping)` signature. The earlier `substitutions` name made the
            # tool uncallable via MCP / Anthropic (TypeError: unexpected
            # keyword 'substitutions'); surfaced by the rc13 drift ratchet.
            parameters=(P("template_bytes", "bytes", True),
                        P("mapping", "Mapping[bytes, bytes]", True,
                          "key -> value substitution map")),
            returns=R("bytes", "rendered output"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class H — self-introspection (already shipped via srmech_version /
        # srmech_abi_version in srmech.amsc._native; no public Python wrapper
        # to register here).
        # ────────────────────────────────────────────────────────────

        # ────────────────────────────────────────────────────────────
        # Class N — rational-approximation
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.rational.continued_fraction", owner="srmech",
            category="rational",
            summary="Simple continued-fraction expansion of p/q = [a_0; a_1, ...] "
                    "via Euclidean recurrence.",
            parameters=(P("numerator", "int", True),
                        P("denominator", "int", True, "> 0")),
            returns=R("list[int]", "ascending CF terms"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.best_rational", owner="srmech",
            category="rational",
            summary="Best rational p'/q' with q' ≤ max_denominator approximating "
                    "p/q via continued-fraction convergents (Stern-Brocot path).",
            parameters=(P("numerator", "int", True), P("denominator", "int", True),
                        P("max_denominator", "int", True, "> 0")),
            returns=R("tuple[int, int]", "(p', q')"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.exp_series_truncate", owner="srmech",
            category="rational",
            summary="Exp Taylor partial sum S_N(p/q) = Σ_{k=0..N} (p/q)^k / k! as "
                    "exact rational via Class N rational + Class J integer factorial "
                    "chain composition. Integer arithmetic only; no floating-point. "
                    "Seeds the asymptotic_calculus catalog (Spike #28 §10/§11 PR #447).",
            parameters=(P("numerator", "int", True, "p of x = p/q (may be negative)"),
                        P("denominator", "int", True, "q of x = p/q (must be > 0)"),
                        P("num_terms", "int", True, "truncation N >= 0, <= 512")),
            returns=R("tuple[int, int]", "(out_num, out_den) of S_N reduced to lowest terms"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.rational_add", owner="srmech",
            category="rational",
            summary="Add two rationals (a_num, a_den) + (b_num, b_den) and "
                    "return reduced (p, q). Pure integer arithmetic; Python "
                    "bignum-capable; C-standalone for u64-fit inputs.",
            parameters=(P("a", "tuple[int, int]", True, "(num, den) of first operand"),
                        P("b", "tuple[int, int]", True, "(num, den) of second operand")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.rational_mul", owner="srmech",
            category="rational",
            summary="Multiply two rationals (a_num, a_den) * (b_num, b_den) and "
                    "return reduced (p, q). Pure integer arithmetic; Python "
                    "bignum-capable; C-standalone for u64-fit inputs.",
            parameters=(P("a", "tuple[int, int]", True, "(num, den) of first operand"),
                        P("b", "tuple[int, int]", True, "(num, den) of second operand")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.rational_div", owner="srmech",
            category="rational",
            summary="Divide two rationals (a_num, a_den) / (b_num, b_den) and "
                    "return reduced (p, q). Pure integer arithmetic; raises "
                    "ZeroDivisionError on b_num==0; Python bignum-capable.",
            parameters=(P("a", "tuple[int, int]", True, "(num, den) of dividend"),
                        P("b", "tuple[int, int]", True, "(num, den) of divisor")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.rational_pow_uint", owner="srmech",
            category="rational",
            summary="Raise rational (base_num, base_den) to non-negative integer "
                    "exponent. Pure integer arithmetic; Python bignum-capable; "
                    "C-standalone for u64-fit inputs + exp <= 64.",
            parameters=(P("base", "tuple[int, int]", True, "(num, den) of base"),
                        P("exp", "int", True, "non-negative integer exponent")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.sin_series_truncate", owner="srmech",
            category="rational",
            summary="Sin Taylor partial sum sin(p/q) = Σ (-1)^k (p/q)^(2k+1) / (2k+1)! as exact rational. Class N + Class J + Class I (sign) composition; Python bignum-capable.",
            parameters=(P("numerator", "int", True, "p of x = p/q"),
                        P("denominator", "int", True, "q of x = p/q (must be > 0)"),
                        P("num_terms", "int", True, "truncation N, 0 <= N <= 50")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.cos_series_truncate", owner="srmech",
            category="rational",
            summary="Cos Taylor partial sum cos(p/q) = Σ (-1)^k (p/q)^(2k) / (2k)! as exact rational. Class N + Class J + Class I (sign) composition; Python bignum-capable.",
            parameters=(P("numerator", "int", True, "p of x = p/q"),
                        P("denominator", "int", True, "q of x = p/q (must be > 0)"),
                        P("num_terms", "int", True, "truncation N, 0 <= N <= 50")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.log1p_series_truncate", owner="srmech",
            category="rational",
            summary="log(1+x) Taylor partial sum Σ (-1)^(k+1) x^k / k for |x|<1 as exact rational. Class N + Class I composition; Python bignum-capable.",
            parameters=(P("numerator", "int", True, "p of x = p/q (|p/q| < 1 for convergence)"),
                        P("denominator", "int", True, "q of x = p/q (must be > 0)"),
                        P("num_terms", "int", True, "truncation N, 0 <= N <= 64")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.atan_series_truncate", owner="srmech",
            category="rational",
            summary="atan(x) Taylor partial sum Σ (-1)^k x^(2k+1) / (2k+1) for |x|<=1 as exact rational. Class N + Class I composition; Python bignum-capable.",
            parameters=(P("numerator", "int", True, "p of x = p/q (|p/q| <= 1 typical)"),
                        P("denominator", "int", True, "q of x = p/q (must be > 0)"),
                        P("num_terms", "int", True, "truncation N, 0 <= N <= 64")),
            returns=R("tuple[int, int]", "(out_num, out_den) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.cos", owner="srmech", category="rational",
            summary="cos(x) (radians) via the Class-N rational cascade: range-reduce into [-π, π] with the π-cascade rational, cos Taylor partial sum, then project the exact rational to float. Substrate-native replacement for math.cos / np.cos (no math.cos in the call graph); matches libm to ~1e-15.",
            parameters=(P("x", "float", True, "angle in radians"),
                        P("terms", "int", False, "Taylor terms (keyword-only); default 24")),
            returns=R("float", "cos(x) projected from the exact rational"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.sin", owner="srmech", category="rational",
            summary="sin(x) (radians) via the Class-N rational cascade (π-cascade range reduction + sin Taylor, projected to float). Substrate-native replacement for math.sin / np.sin; matches libm to ~1e-15.",
            parameters=(P("x", "float", True, "angle in radians"),
                        P("terms", "int", False, "Taylor terms (keyword-only); default 24")),
            returns=R("float", "sin(x) projected from the exact rational"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.tan", owner="srmech", category="rational",
            summary="tan(x) = sin(x)/cos(x) via the Class-N rational cascade (raises if cos(x) == 0). Substrate-native replacement for math.tan / np.tan.",
            parameters=(P("x", "float", True, "angle in radians"),
                        P("terms", "int", False, "Taylor terms (keyword-only); default 24")),
            returns=R("float", "tan(x) projected from the exact rational"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.atan", owner="srmech", category="rational",
            summary="atan(x) via the Class-N atan cascade with three-band argument reduction (√2∓1 edges → every series argument |·|<=√2−1; Class-K magnitude, no abs()). Substrate-native replacement for math.atan / np.arctan; machine-ε accurate.",
            parameters=(P("x", "float", True, "argument"),
                        P("terms", "int", False, "atan Taylor terms (keyword-only); default 40")),
            returns=R("float", "atan(x) in (-π/2, π/2)"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.atan2", owner="srmech", category="rational",
            summary="atan2(y, x) via the Class-N atan cascade with full quadrant logic. Substrate-native replacement for math.atan2 / np.arctan2; machine-ε accurate.",
            parameters=(P("y", "float", True, "ordinate"),
                        P("x", "float", True, "abscissa"),
                        P("terms", "int", False, "atan Taylor terms (keyword-only); default 40")),
            returns=R("float", "atan2(y, x) in (-π, π]"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.exp", owner="srmech", category="rational",
            summary="e^x (real) via the Q61 Class-N exp cascade with Cody-Waite ln2 reduction (x = n*ln2 + r, |r| <= ln2/2; exp(r) the Q61 integer Taylor, 2^n folded into the IEEE exponent). Bit-exact with the native peer srmech_exp; dispatches to C when available. Substrate-native replacement for math.exp / np.exp (real).",
            parameters=(P("x", "float", True, "real exponent"),
                        P("terms", "int", False, "exact-rational reference Taylor terms (keyword-only); default 24")),
            returns=R("float", "e^x projected from the Q61 cascade"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.log", owner="srmech", category="rational",
            summary="ln(x) (natural log, x > 0) via the Q61 Class-N atanh cascade: x = m*2^e read from the bit pattern, m folded into [1/sqrt2, sqrt2), log(m) = 2*atanh((m-1)/(m+1)) the Q61 series, e*ln2 recombined with a two-word ln2. Bit-exact with the native peer srmech_log; dispatches to C when available. Domain: x < 0 -> NaN, x == 0 -> -Inf. Substrate-native replacement for math.log / np.log (real).",
            parameters=(P("x", "float", True, "argument, x > 0"),
                        P("terms", "int", False, "exact-rational reference Taylor terms (keyword-only); default 13")),
            returns=R("float", "ln(x) projected from the Q61 cascade"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.cexp", owner="srmech", category="rational",
            summary="e^(i*theta) = cos(theta) + i*sin(theta) via the Class-N cascade (Euler). Class-N trig composed with Class-C imaginary-unit rotation — the DFT twiddle factor and the quantum time-evolution phase. Substrate-native replacement for np.exp / cmath.exp of 1j*theta.",
            parameters=(P("theta", "float", True, "phase angle in radians"),
                        P("terms", "int", False, "trig Taylor terms (keyword-only); default 24")),
            returns=R("complex", "e^(i*theta) on the unit circle"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.complex_exp", owner="srmech", category="rational",
            summary="e^z for complex z = e^(z.real)*(cos(z.imag) + i*sin(z.imag)) via the Class-N cascade. Class-N exp + trig composed with Class-C i-rotation. Substrate-native replacement for np.exp / cmath.exp on a complex argument.",
            parameters=(P("z", "complex", True, "complex exponent"),
                        P("terms", "int", False, "trig Taylor terms (keyword-only); default 24")),
            returns=R("complex", "e^z projected from the exact rational"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.sqrt", owner="srmech", category="rational",
            summary="sqrt(x) for x >= 0 via the Class-N rational sqrt cascade — IEEE-bit x = M*2^e, root = isqrt(M << 2K) (K=27), projected by 2^(e/2 - K). Bit-exact with the native peer srmech_rational_sqrt; dispatches to C. precision_bits=N selects the higher-precision bignum reference (as_integer_ratio + scaled floor-isqrt). No math.sqrt / np.sqrt in the call graph; negative x raises a domain error.",
            parameters=(P("x", "float", True, "radicand, x >= 0"),
                        P("precision_bits", "int", False, "higher-precision bignum reference (keyword-only); default None = C-bit-exact K=27 cascade")),
            returns=R("float", "sqrt(x) projected from the integer root"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.hypot", owner="srmech", category="rational",
            summary="hypot(a, b) = sqrt(a^2 + b^2) via the Class-N sqrt cascade — Class-M sum-of-squares bind composed with the Class-N sqrt. Substrate-native replacement for math.hypot / np.hypot (the complex modulus |z| = hypot(z.real, z.imag)).",
            parameters=(P("a", "float", True, "first leg"),
                        P("b", "float", True, "second leg"),
                        P("precision_bits", "int", False, "scaled-integer precision (keyword-only); default 64")),
            returns=R("float", "Euclidean norm sqrt(a^2 + b^2)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.spectral_cascades.dft", owner="srmech", category="cascade",
            summary="Discrete Fourier transform as the Antikythera epicycle-sum X_k = sum_n x_n * e^(-2pi*i*(k*n mod N)/N): Class I (cyclic index) + Class N (twiddle) + Class C (i-rotation) + Class M (bundle). Pure-Python O(N^2); substrate-native replacement for NumPy fft on a 1-D sequence.",
            parameters=(P("x", "list[complex]", True, "input samples"),
                        P("inverse", "bool", False, "keyword-only; conjugate twiddle + 1/N scale; default False")),
            returns=R("list[complex]", "DFT spectrum (or inverse)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.spectral_cascades.idft", owner="srmech", category="cascade",
            summary="Inverse DFT — dft() with the conjugate twiddle and a 1/N scale. Substrate-native replacement for NumPy ifft on a 1-D sequence.",
            parameters=(P("x", "list[complex]", True, "input spectrum"),),
            returns=R("list[complex]", "time-domain samples"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.spectral_cascades.fft", owner="srmech", category="cascade",
            summary="Fast Fourier transform — the radix-2 Cooley-Tukey butterfly. Same value as dft() but O(N log N) when N is a power of two, adding Class J (radix N=2*(N/2) factorization) + Class K (butterfly recursion depth) on top of the DFT cascade. Falls back to direct dft() for non-power-of-2 N, so it is a drop-in for NumPy fft at ANY length.",
            parameters=(P("x", "list[complex]", True, "input samples"),
                        P("inverse", "bool", False, "keyword-only; conjugate twiddle + 1/N scale; default False")),
            returns=R("list[complex]", "FFT spectrum (or inverse)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.spectral_cascades.ifft", owner="srmech", category="cascade",
            summary="Inverse FFT — fft() with the conjugate twiddle and a 1/N scale. Substrate-native replacement for NumPy ifft on a 1-D sequence.",
            parameters=(P("x", "list[complex]", True, "input spectrum"),),
            returns=R("list[complex]", "time-domain samples"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.spectral_cascades.kron", owner="srmech", category="cascade",
            summary="Kronecker product A (x) B of two 2-D matrices: (A(x)B)[i*p+k, j*q+l] = A[i,j]*B[k,l] — Class I (mixed-radix index) + Class M (element products). Pure-Python; substrate-native replacement for the NumPy Kronecker product.",
            parameters=(P("a", "list[list[complex]]", True, "left matrix (list of rows)"),
                        P("b", "list[list[complex]]", True, "right matrix (list of rows)")),
            returns=R("list[list[complex]]", "Kronecker product block matrix"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.exact_dft.exact_dft", owner="srmech", category="cascade",
            summary="Exact cyclotomic-integer DFT of an integer / Gaussian-integer power-of-two signal: the twiddles e^(-2pi*i*j/N) are roots of unity (algebraic integers in Z[zeta_N]); for power-of-two N, zeta^(N/2) = -1 (a Class-K sign-flip) collapses the ring to the negacyclic integers Z[x]/(x^(N/2)+1), so the transform is PURE INTEGER add/subtract — no floats. Returns the exact spectrum (one integer (real_vec, imag_vec) pair of length N/2 per bin); call lift() for the single FPU rotation to complex. Class I (cyclic index) + Class K (zeta^(N/2)=-1 reduction) + Class M (integer bundle). Rides the native srmech_exact_dft_i64 int64 twin; arbitrary-precision magnitudes use the Python bignum path. Raises on non-integer / non-power-of-two input (use dft there).",
            parameters=(P("signal", "list[complex]", True, "integer / Gaussian-integer power-of-two-length sequence (integer-valued)"),
                        P("inverse", "bool", False, "keyword-only; conjugate exponent zeta^(-nk); default False")),
            returns=R("list[tuple[list[int], list[int]]]", "exact Z[zeta_N] integer spectrum (per-bin (real_vec, imag_vec))"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.exact_dft.exact_idft", owner="srmech", category="cascade",
            summary="Inverse exact cyclotomic-integer DFT — exact_dft() with the conjugate exponent zeta^(-nk). Unnormalised: the 1/N scale is a Class-N rational applied at lift() time (lift(exact_idft(x), scale=N)), keeping this core pure integer.",
            parameters=(P("signal", "list[complex]", True, "integer / Gaussian-integer power-of-two-length sequence (integer-valued)"),),
            returns=R("list[tuple[list[int], list[int]]]", "exact Z[zeta_N] integer inverse spectrum"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.exact_dft.lift", owner="srmech", category="cascade",
            summary="The single FPU lift: rotate an exact Z[zeta_N] integer spectrum (from exact_dft) to complex at zeta_N = e^(-2pi*i/N). This is the ONLY place a float is produced — the projection from the exact discrete substrate to the continuous observable (floats are for the FPU lift, not the math). scale divides the result (use scale=N for a normalised inverse). Class C (i-rotation) over the Class-N substrate-native cexp.",
            parameters=(P("spectrum", "list[tuple[list[int], list[int]]]", True, "exact Z[zeta_N] integer spectrum from exact_dft / exact_idft"),
                        P("scale", "int", False, "keyword-only; divide the lifted result (scale=N normalises an inverse); default 1")),
            returns=R("list[complex]", "lifted complex spectrum / samples"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.qr", owner="srmech", category="cascade",
            summary="Householder QR factorization A = Q*R: Q a product (Class M) of elementary reflectors H = I - beta*v*v^H, each Class K (sign-flip across a hyperplane) + Class M (outer-product bind) + Class N (1/(v^H v) scale, with the column norm a rational.sqrt). numpy as CONTAINER only — no NumPy QR in the call graph. mode='reduced' (default, matching NumPy QR) or 'complete'. QR is unique only up to signs; the invariants (Q*R=A, Q^H Q=I, R upper-triangular) hold to round-off.",
            parameters=(P("a", "Mat", True, "(m, n) real or complex 2-D matrix"),
                        P("mode", "str", False, "keyword-only; 'reduced' (default) or 'complete'")),
            returns=R("tuple[Mat, Mat]", "(Q, R): orthonormal-column Q + upper-triangular R"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.svd", owner="srmech", category="cascade",
            summary="Singular value decomposition A = U*diag(s)*V^H via the Gram-matrix Hermitian eigendecomposition: Class L (eig of A^H A or A A^H, srmech's hermitian_eigendecompose) + Class N+K (s = sqrt(eigvals), via rational.sqrt) + Class M (U = A*V*Sigma^-1). numpy as CONTAINER only — no NumPy SVD. full_matrices=False (reduced form). Singular values match NumPy SVD to round-off for well-conditioned inputs (the Gram route squares the condition number); U/V unique only up to signs.",
            parameters=(P("a", "Mat", True, "(m, n) real or complex 2-D matrix"),
                        P("full_matrices", "bool", False, "keyword-only; only False (reduced form) is supplied")),
            returns=R("tuple[Mat, Vec, Mat]", "(U, s, Vh): singular vectors + descending singular values"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.lstsq", owner="srmech", category="cascade",
            summary="Least-squares solution of A x = b (minimising ||A x - b||): {QR} factorization + Class M (the Qᴴ b product) + Class I (back-substitution = the ordered triangular solve). Overdetermined/square m>=n, full column rank; b a vector or stack of RHS. numpy as CONTAINER only — no NumPy lstsq. Matches NumPy lstsq(a,b)[0] to round-off.",
            parameters=(P("a", "Mat", True, "(m, n) coefficient matrix, m>=n"),
                        P("b", "Mat | Vec", True, "(m,) or (m, k) right-hand side(s)")),
            returns=R("Mat | Vec", "least-squares solution x, shape (n,) or (n, k)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.einsum", owner="srmech", category="cascade",
            summary="Einstein-summation tensor contraction via the general index-iteration definition: Class B/D (the subscript spec is a typed index-pattern) + Class I (iterate over free + summed index tuples) + Class M (sum-of-products bundle). Handles any subscript string (matmul ij,jk->ik / trace ii-> / transpose ij->ji / dot i,i-> / outer i,j->ij / arbitrary contraction), implicit output supported. Value-faithful to the NumPy einsum.",
            parameters=(P("subscripts", "str", True, "einsum subscript string, e.g. 'ij,jk->ik'"),
                        P("operands", "tuple[Mat, ...]", False, "the input arrays (variadic)")),
            returns=R("Mat | Vec | complex | float | list", "the contracted tensor"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.eigvals", owner="srmech", category="cascade",
            summary="Eigenvalues of a general (non-Hermitian) square matrix via the shifted-QR iteration: Class K (iterate-to-convergence asymptotic-DoF) + Class L (spectral content) + {QR} (per-step Householder factorization) + Class C (Wilkinson spectral shifts). Runs in complex arithmetic so complex eigenvalues of real matrices fall out directly. numpy as CONTAINER only — no NumPy eig/eigvals. Eigenvalues unique as a SET; the multiset matches NumPy eigvals to ~1e-12 for moderate sizes.",
            parameters=(P("a", "Mat", True, "(n, n) real or complex square matrix"),
                        P("max_sweeps", "int", False, "keyword-only; per-eigenvalue iteration cap factor (default 500)")),
            returns=R("Vec", "length-n complex eigenvalue array"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.char_poly", owner="srmech", category="cascade",
            summary="Exact integer characteristic polynomial det(xI - A) via Faddeev-Leverrier. For an INTEGER matrix returns the EXACT integer coefficients (monic, high->low [1, c1, ..., cn]) in arbitrary-precision integer arithmetic — the exact ALGEBRAIC substrate of the eigenproblem: exact trace = -c1, exact determinant = (-1)^n*cn, all elementary symmetric functions of the spectrum, NO floating point. The eigenvalues are the ROOTS of this exact polynomial (extract them with eigvals_exact, which avoids the Wilkinson ill-conditioning of float root-finding by staying in exact arithmetic). Non-integer matrices fall back to a float Faddeev-Leverrier. Class L (algebraic content) + Class M (matrix-product/trace accumulate) + Class K (exact //k step division).",
            parameters=(P("a", "Mat", True, "(n, n) square matrix (integer entries → exact integer coefficients)"),),
            returns=R("list", "characteristic-polynomial coefficients, monic high→low [1, c1, ..., cn]"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.eigvals_exact", owner="srmech", category="cascade",
            summary="Exact REAL eigenvalues of an integer matrix — the well-conditioned exact-until-rotation cascade (no Wilkinson ill-conditioning, because the eigenvalues are ALGEBRAIC and we never leave exact arithmetic). char_poly (exact integer) + Yun square-free factorization (exact multiplicities) + Sturm sign-sequence isolation (Class C sign-count at Class K interval boundaries) + rational bisection (Class N anchors → the algebraic asymptote), all in exact Fraction arithmetic, then ONE FPU lift. bits sets refinement precision; return_intervals=True yields the exact (lo, hi) rational isolating intervals. Returns the real eigenvalues ascending WITH multiplicity (symmetric matrices are all-real/complete; matrices with complex eigenvalues return only the real ones — complex isolation is a follow-up).",
            parameters=(P("a", "Mat", True, "(n, n) integer square matrix"),
                        P("bits", "int", False, "keyword-only; bisection refinement precision in bits (default 64)"),
                        P("return_intervals", "bool", False, "keyword-only; return exact (lo, hi) rational intervals instead of floats; default False")),
            returns=R("list", "real eigenvalues ascending with multiplicity (floats, or (lo, hi) Fraction intervals)"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.continued_fraction_convergents",
            owner="srmech",
            category="rational",
            summary="Produce the convergent ladder [(h_0, k_0), ...] from a continued-fraction coefficient list via the canonical CF recurrence. Anchors `[[user_stance_pi_spectral_shape_scalar_invariant]]` — the convergent ladder IS π's substrate identity. Canonical SSoT: Hardy & Wright *Theory of Numbers* §10.6 (best-rational property) + Khinchin *Continued Fractions* §10 (canonical π CF).",
            parameters=(P("coef_list", "list[int]", True,
                          "CF coefficients [a_0; a_1, ..., a_n]; a_0 may be negative, a_k > 0 for k > 0"),),
            returns=R("list[tuple[int, int]]",
                      "convergent ladder (h_k, k_k) per CF coefficient"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.pi_cascade_digits",
            owner="srmech",
            category="rational",
            summary="Stream decimal digits of π via integer-cyclic geometric cascade (Archimedes hexagon-doubling with integer-floor √ via math.isqrt at fixed precision). Returns '3.141592...' as a string without invoking math.pi anywhere in the call graph (AST-verified discipline gate per `[[user_stance_pi_spectral_shape_scalar_invariant]]`; Spike #32 / PR #460). rc13 cap-expansion (Task #248): num_digits up to 1000 with auto-scaled cascade depth + precision_bits. Canonical SSoT: Archimedes *Measurement of a Circle* (c. 250 BCE) for the algorithm; Khinchin *Continued Fractions* §10 for canonical π reference.",
            parameters=(P("num_digits", "int", True, "0 <= num_digits <= 1000"),
                        P("max_cascade_depth", "int", False,
                          "default None (auto-scaled from num_digits); cascade doubling depth in [1, 2000]"),
                        P("precision_bits", "int", False,
                          "default None (auto-scaled from num_digits); scaled-integer √ bit precision in [64, 32768]")),
            returns=R("str", "'3.{num_digits}' decimal expansion of π"),
        ),

        # ────────────────────────────────────────────────────────────
        # Genome-storage surface — biological-structure names as cascade
        # names (genome / chromosome / telomere / quad-strand). Part 2 of
        # #962; validated as F711-F715 on the research subtree.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.genome.encode_shape", owner="srmech", category="genome",
            summary="The genome encode CRITERION (F715): decide how to store a kernel of size n. n<=256 -> a 'tome' (one dense 2**8 leaf); n<=1024 -> a 'mobius' (one quad-turn = the 4 Klein-4 sectors); n>1024 -> a 'quad_strand' (a helix of quad-turns, a chromosome). depth = ceil(log4(ceil(n/256))) is the number of base-4 quad levels over the leaves; computed in pure integer arithmetic (Class I/N; no float log). Thresholds attested to 256=2**8 and the Klein-4 order 4 — no magic. Returns a dict {n, shape, leaves, depth, leaf_cap}.",
            parameters=(P("n", "int", True, "kernel size (positive int — number of elements/leaves to store)"),),
            returns=R("dict", "{n, shape: 'tome'|'mobius'|'quad_strand', leaves, depth, leaf_cap}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.quad_turn", owner="srmech", category="genome",
            summary="Couple one helix turn through the_one — the genome's turn operation (F713). The turn is bound to the_one (the held invariant) by the REVERSIBLE Klein-4 bind (V4=(F2)^2 XOR, so quad_turn(quad_turn(t, one), one) == t): the duality held WITHOUT collapse, numpy-free. the_one is the shared invariant in every turn's coupling, so a chromosome navigates across its turns through the_one and recovers any turn by re-binding. Each turn sits in the native 4-sector biaxial '+' (cascade.parallel_sector_dispatch, CAP=4) — per F712 the 4-way is ONE chirality level, the deeper leaf-tree is base-4 radix addressing. Class M (bind) composed with Class C (the Klein-4 chirality).",
            parameters=(P("turn", "HV", True, "a Klein-4 vector (uint8 {0,1,2,3}) — the helix turn (e.g. from hdc.klein4_random)"),
                        P("the_one", "HV", True, "a Klein-4 vector (uint8 {0,1,2,3}) — the held invariant coupled into every turn")),
            returns=R("HV", "the coupled turn (re-apply quad_turn with the same the_one to recover turn)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.telomere", owner="srmech", category="genome",
            summary="The non-data content-address CAP that delimits a chromosome (F715) — biology's repetitive non-coding chromosome-end cap. A deterministic, content-addressed Klein-4 sentinel derived from a label (Class A content-address via sha256_bytes -> a seed -> a Klein-4 carrier). Same label gives the same cap (so a chromosome is recalled / partitioned by matching its cap), distinct labels give distinct caps. It marks + protects a partition boundary and carries no kernel data. dim is the Klein-4 vector length (match the turns it caps).",
            parameters=(P("label", "str", True, "the chromosome label — content-addressed to a deterministic cap"),
                        P("dim", "int", False, "Klein-4 vector length (default 64); match the turns the cap delimits")),
            returns=R("HV", "the telomere cap (a Klein-4 vector, deterministic per label)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.chromosome", owner="srmech", category="genome",
            summary="Pack a kernel — or SEVERAL genes — into a telomere-capped strand (F713/F715/F730). Single kernel (unchanged): pass leaves (Klein-4 vectors, one tome each); they become a helix of quad-turns coupled through the_one, led by a telomere cap from label; recover with recall. Several genes (F730/S43): pass genes=[(gene_label, gene_leaves), ...] instead — each gene's leaves are framed by a tlv gene-header (the cheaper internal delimiter, label recoverable via tlv_unpack) inside ONE telomere-capped chromosome; recover with genes(). Pass exactly one of leaves or genes; the_one is always required. Class A (cap) + Class B (gene frame) + Class M (bind) + Class C (the Klein-4 chirality).",
            parameters=(P("leaves", "Sequence[HV]", False, "single-kernel mode: the kernel's leaves — Klein-4 vectors, one tome (<=256) each (pass leaves OR genes)"),
                        P("the_one", "HV", True, "the held invariant every turn is coupled through"),
                        P("label", "str", False, "keyword-only; the chromosome label for the telomere cap (default 'chromosome')"),
                        P("genes", "Sequence[tuple]", False, "keyword-only; multi-gene mode (F730): [(gene_label, gene_leaves), ...] — each gene tlv-framed inside one telomere-capped chromosome (pass leaves OR genes)")),
            returns=R("list", "the strand: [telomere_cap, coupled turn, ...] (single-kernel) or [telomere_cap, gene_header, coupled turn, ..., gene_header, ...] (multi-gene)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.recall", owner="srmech", category="genome",
            summary="Recover a kernel's leaves from a telomere-capped chromosome strand (F713/F715) — the exact inverse of chromosome. Walk the strand; skip every element equal to the telomere cap (the non-data delimiter) and re-bind the_one (the reversible quad_turn again) on each coupled data turn to recover the original leaf. recall(chromosome(leaves, one, label=L), one, telomere(L, len(one))) == leaves. Matching the cap by VALUE (not position) is what lets one recall reach into a multi-chromosome genome strand.",
            parameters=(P("strand", "Sequence[HV]", True, "a telomere-capped chromosome strand (from chromosome)"),
                        P("the_one", "HV", True, "the held invariant the turns were coupled through"),
                        P("telomere", "HV", True, "the telomere cap delimiting the chromosome (skipped, not decoded)")),
            returns=R("list", "the recovered kernel leaves (Klein-4 vectors), in order"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genes", owner="srmech", category="genome",
            summary="Recover [(gene_label, gene_leaves), ...] from a multi-gene chromosome (F730/S43) — the inverse of chromosome(genes=..., the_one). Walk the strand: a GENE_FRAME_TAG header (first byte > 3, so never a Klein-4 turn whose bytes are all <= 3) opens a new gene whose label is read back with tlv_unpack; each coupled data turn until the next header (or the end) is re-bound through the_one (the reversible quad_turn) to recover that gene's leaf. Leading element(s) before the first gene header are the chromosome's telomere cap (a delimiter, not data) and are skipped — so genes needs only the strand + the_one, no cap argument. Use genes (not recall) on a multi-gene chromosome.",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-gene chromosome strand (from chromosome(genes=...))"),
                        P("the_one", "HV", True, "the held invariant the gene turns were coupled through")),
            returns=R("list", "[(gene_label:str, gene_leaves:list[HV]), ...] in strand order"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome", owner="srmech", category="genome",
            summary="Pack many kernels into ONE telomere-partitioned strand — the top-level genome / chromosome set (F715). Each (label, leaves) kernel becomes a telomere-capped chromosome (coupled through the_one), all concatenated into a single strand; the per-kernel telomere caps delimit + protect the partitions, so one strand holds many kernels (F715 verified: astronomy / geography / music). A genome strand IS a strand (list of Klein-4 vectors), just with multiple caps; recover with partition. kernels is a dict {label: leaves} or a sequence of (label, leaves) pairs (insertion order = strand order). Composes chromosome (Class A cap + Class M coupling).",
            parameters=(P("kernels", "dict", True, "{label: leaves} — each kernel's leaves are Klein-4 vectors (one tome each)"),
                        P("the_one", "HV", True, "the held invariant every turn of every chromosome is coupled through")),
            returns=R("list", "the flat genome strand: concatenated [cap, turns...] per kernel"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.partition", owner="srmech", category="genome",
            summary="Recover every kernel from a multi-kernel genome strand — the inverse of genome (F715). Walk the strand; each element equal to one of labels' telomere caps starts a new chromosome partition, and the coupled turns until the next cap are that kernel's leaves (re-bound through the_one — reversible quad_turn). Returns {label: leaves}. partition knows ALL the caps, so (unlike a single-cap recall) it does not mistake one chromosome's cap for another's data: partition(genome({a:A,b:B}, one), one, [a,b]) == {a:A, b:B}.",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-kernel genome strand (from genome)"),
                        P("the_one", "HV", True, "the held invariant the turns were coupled through"),
                        P("labels", "list", True, "the chromosome labels whose telomere caps partition the strand")),
            returns=R("dict", "{label: leaves} — each kernel's recovered Klein-4 leaves, in order"),
        ),

        # ────────────────────────────────────────────────────────────
        # Genome persistence — UPSTREAM §41. The helix grows ON DISK: a
        # genome directory holds a fixed-width append-only body (turns.bin)
        # + an MPR-attested manifest catalog. Reads are paged + BOUNDED
        # (every read re-hashes the bytes it touched vs the manifest).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.genome.genome_save", owner="srmech", category="genome",
            summary="Persist a genome strand to a directory (UPSTREAM §41 / §44). SCANS the strand for its inline CHROM caps (§44 — the strand self-describes; chromosome labels are recovered inline), writes a SELF-DESCRIBING fixed-width body to path/turns.bin (every strand element is a leaf_dim-byte block — a CHROM/GENE cap or a coupled data turn — no length prefixes), and writes a DERIVED MPR-attested catalog to path/manifest.json (format_version, leaf_dim, n_turns, the_one hash+hex, body_sha256, and per-chromosome cap_sha256 / leaf_count / byte_offset / byte_len). The strand is the SSoT; the manifest is an optional .fai-style cache, rebuildable by scanning the body. Multi-gene chromosomes carry their gene boundaries INLINE as GENE caps (no gene-index sidecar). the_one (the held invariant) is content-addressed into the manifest so a load re-anchors without re-deriving it. Returns the manifest data dict. numpy-free; hashes via sha256_bytes.",
            parameters=(P("strand", "Sequence[HV]", True, "the flat genome strand to persist (from genome)"),
                        P("path", "str", True, "the genome DIRECTORY to write (created if absent; gets manifest.json + turns.bin)"),
                        P("the_one", "HV", True, "the held invariant every turn is coupled through (content-addressed into the manifest)"),
                        P("labels", "list", False, "optional, back-compat; when given VALIDATES the scanned chromosome set (labels are discovered inline)")),
            returns=R("dict", "the manifest data {format_version, leaf_dim, n_turns, the_one, body_sha256, chromosomes}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_load", owner="srmech", category="genome",
            summary="Reconstruct a genome from a directory (UPSTREAM §41) — returns (strand, the_one, labels). labels=None loads the WHOLE genome: streams turns.bin block-by-block (RAM bounded by the active block, not the whole file) and re-hashes the streamed body against the manifest body_sha256. A subset labels=[...] is a PAGED read: it seeks to each requested chromosome's byte_offset and reads only its byte_len bytes (RAM bounded by the largest single chromosome), re-hashing that region's cap against cap_sha256. Bounding IS integrity — a flipped / truncated / re-ordered byte raises GenomeBoundingError. The returned strand is byte-for-byte the saved strand for the requested chromosomes; the_one is rebuilt from the manifest's stored block and verified against its hash.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("labels", "list", False, "keyword-only; chromosome subset to page in (None = load all, streamed)")),
            returns=R("tuple", "(strand, the_one, labels) — the reconstructed genome (byte-exact for the requested chromosomes)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_catalog", owner="srmech", category="genome",
            summary="Read the catalog of a genome (UPSTREAM §41 / §44). When manifest.json is present this is the cheap, body-free read — it returns the manifest data dict (leaf_dim, n_turns, body_sha256, the_one hash+hex, and per-chromosome cap_sha256 / leaf_count / byte_offset / byte_len) WITHOUT opening turns.bin. §44: when the manifest is ABSENT the catalog is REBUILT by scanning the self-describing body (the strand is the SSoT, the manifest an optional .fai cache); that rebuild needs the_one= (its length is the leaf width) and reads turns.bin once. The manifest is an MPRRecord (MPR v1) that passes validate_mpr_record (its response_sha256 IS the body hash). numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),),
            returns=R("dict", "the manifest data (chromosome index + integrity hashes), read from manifest.json or rebuilt by scanning turns.bin"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_append", owner="srmech", category="genome",
            summary="Append ONE chromosome to an existing genome (UPSTREAM §41) — the helix grows. Packs leaves into a telomere-capped chromosome (coupled through the_one), appends its fixed-width blocks to the END of turns.bin (APPEND-ONLY — prior chromosomes' body bytes are never rewritten), and rewrites the manifest with the new chromosome entry plus a recomputed body_sha256 / n_turns. Every EXISTING chromosome's manifest entry (cap_sha256 / byte_offset / leaf_count / byte_len) stays byte-identical. Verifies the body it appends TO against body_sha256 first (never grows a corrupt body). Returns the updated manifest data dict. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the new chromosome's label (must not already exist in the genome)"),
                        P("leaves", "Sequence[HV]", True, "the new kernel's Klein-4 leaf vectors"),
                        P("the_one", "HV", True, "the held invariant the new turns are coupled through (dim must match leaf_dim)")),
            returns=R("dict", "the updated manifest data (with the appended chromosome + recomputed body_sha256)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_window", owner="srmech", category="genome",
            summary="Page in ONLY one chromosome's leaves from a genome (UPSTREAM §41). Seeks to the chromosome label's byte_offset and reads only its byte_len bytes (RAM bounded by that one chromosome), re-hashing the region's cap against the manifest cap_sha256 — a mismatch raises GenomeBoundingError. Returns the chromosome's stored leaves (the coupled data turns, the cap excluded) as a list of Klein-4 vectors, in order — the disk-paging counterpart of reaching into one partition of the genome without loading the rest.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the chromosome label whose leaves to page in")),
            returns=R("list", "the chromosome's stored leaves (coupled turns, cap excluded), in order"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_genes", owner="srmech", category="genome",
            summary="Page ONE multi-gene chromosome's genes back from a genome (F732 / UPSTREAM §44) — the disk counterpart of the in-memory genes(). Pages in only that chromosome's region (RAM-bounded + cap-integrity-checked), then SCANS it for the inline GENE caps (§44 — no gene-index sidecar; the gene boundaries + labels live in the body) and re-binds the_one (rebuilt + hash-verified from the manifest cache, or a the_one override) to recover a list of (gene_label, gene_leaves) — exactly what genes(chromosome(genes=…)) returns in memory. Raises ValueError on a single-kernel chromosome (no inline GENE caps; use genome_window / partition). numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the multi-gene chromosome label whose genes to page in")),
            returns=R("list", "the chromosome's genes as a list of (gene_label, gene_leaves) tuples, in order"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_remove", owner="srmech", category="genome",
            summary="Excise ONE chromosome from a genome IN PLACE (UPSTREAM §45) — biology excises, it does not re-synthesize. Finds the chromosome label's region in the self-describing body (§44 — its CHROM cap + data turns occupy [byte_offset, byte_offset+byte_len)) and splices THAT byte span out of turns.bin, leaving every OTHER chromosome's coupled body bytes byte-identical (no kernel is decoded / re-coupled — the survivors are the same bytes, only relocated). The derived .fai manifest is then rebuilt by scanning the spliced body (§44 — body_sha256 / n_turns and every survivor's byte_offset recomputed; the manifest stays an optional cache). Re-hashes the whole on-disk body against the committed body_sha256 BEFORE the edit (never splice a corrupt body — GenomeBoundingError). the_one= is needed only when manifest.json is absent (its length is the leaf width for the rebuild-by-scan). Raises ValueError if the label is absent or is the genome's only chromosome. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the chromosome label to excise (must not be the genome's only chromosome)"),
                        P("the_one", "HV", False, "the held invariant (only required when manifest.json is absent — its length is the leaf width for the §44 rebuild-by-scan)")),
            returns=R("dict", "the updated manifest data (the excised chromosome gone, survivors' byte_offsets + body_sha256 recomputed)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_replace", owner="srmech", category="genome",
            summary="Replace ONE chromosome's content IN PLACE (UPSTREAM §45). Splices the chromosome label's old byte span out of turns.bin and a FRESH telomere-capped chromosome (leaves coupled through the_one, same label) IN at the same position — every OTHER chromosome's coupled body bytes stay byte-identical (an in-place edit, NOT a whole-genome re-pack). The derived manifest is rebuilt by scanning the new body (§44 — the strand is the SSoT). the_one is REQUIRED (it both re-couples the new leaves AND supplies the leaf width for the §44 rebuild) and must match the genome's leaf_dim. Re-hashes the on-disk body against body_sha256 before the edit (GenomeBoundingError on mismatch). Raises ValueError if the label is absent. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the chromosome label whose content to replace"),
                        P("leaves", "Sequence[HV]", True, "the replacement kernel's Klein-4 leaf vectors"),
                        P("the_one", "HV", True, "the held invariant the new turns are coupled through (dim must match leaf_dim)")),
            returns=R("dict", "the updated manifest data (the chromosome's content replaced in place, body_sha256 recomputed)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_export", owner="srmech", category="genome",
            summary="Export ONE chromosome as a single self-contained .chr file (UPSTREAM §43). Reads the chromosome label's fixed-width region (CHROM cap + coupled data turns; the cap re-hashed against the manifest cap_sha256) and writes it — together with the_one — to out as ONE MPR-attested record (MPR v1; response_sha256 IS the region hash). So a chromosome becomes a self-contained, content-addressed unit: tar it, ship it, genome_import it self-verifying — realising the §43 'chromosome as a bundleable file' goal on top of the §44 self-describing strand. Composes srmech.amsc.format (the MPRRecord + sha256 content-address), NOT a parallel attestation. §44: pass the_one= to export from a manifest-less source genome. Raises ValueError if the label is absent. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the chromosome label to export as a .chr bundle"),
                        P("out", "str", True, "the output file path for the .chr (one MPR-attested JSON record)"),
                        P("the_one", "HV", False, "the held invariant (only required when the source genome's manifest.json is absent — its length is the leaf width for the §44 rebuild-by-scan)")),
            returns=R("dict", "the .chr data block (format_version / leaf_dim / label / leaf_count / cap_sha256 / the_one hash+hex / region hash+hex)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_import", owner="srmech", category="genome",
            summary="Import a .chr chromosome bundle into a genome at dest (UPSTREAM §43). Reads the MPR-attested .chr (genome_export's output), RE-HASHES its region and its the_one and compares them against the bundle's own attestation — a mismatch is a GenomeBoundingError (self-verifying). Then: if dest has no genome yet, the .chr SEEDS a fresh one (its region becomes turns.bin verbatim, its the_one the coupling invariant); if dest already holds a genome, the chromosome is APPENDED byte-for-byte — which REQUIRES the same coupling invariant (the dest the_one must match the .chr the_one) and a fresh label. The manifest is re-derived by scanning the grown body (§44 — the strand is the SSoT). numpy-free.",
            parameters=(P("chr_path", "str", True, "the .chr bundle file written by genome_export"),
                        P("dest", "str", True, "the dest genome directory (seeded fresh if it has no genome, else appended to)"),
                        P("the_one", "HV", False, "the held invariant (only consulted for a manifest-less EXISTING dest — the §44 rebuild width; the bundle carries its own the_one)")),
            returns=R("dict", "the dest manifest data (the seeded genome, or the existing genome with the imported chromosome appended)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_explode", owner="srmech", category="genome",
            summary="Explode a packed genome into a directory of loose .chr files (UPSTREAM §43; the packed->loose half of git's object model). A genome's turns.bin (the 'packfile') is written out as ONE self-contained, content-addressed .chr bundle per chromosome (the 'loose objects'), named <out_dir>/<label>.chr — each is genome_export's MPR-attested, self-verifying output, so the loose form is inspectable and shippable chromosome-by-chromosome. genome_pack is the inverse. Returns a list of {label, path, region_sha256} dicts in chromosome order. §44: pass the_one= to explode a manifest-less source. Raises ValueError if a chromosome label is not filename-safe. numpy-free.",
            parameters=(P("path", "str", True, "the packed genome directory written by genome_save"),
                        P("out_dir", "str", True, "the output directory for the loose <label>.chr bundles (created if absent)"),
                        P("the_one", "HV", False, "the held invariant (only required when the source genome's manifest.json is absent — the §44 rebuild width)")),
            returns=R("list", "a list of {label, path, region_sha256} dicts, one per chromosome (in the genome's chromosome order)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_pack", owner="srmech", category="genome",
            summary="Pack a directory of loose .chr files into one packed genome (UPSTREAM §43; the loose->packed inverse of genome_explode, git repack-like). Every *.chr bundle in loose_dir is genome_import-ed into dest in CANONICAL sorted-label order, so the packed turns.bin is a well-defined function of the chromosome SET — like a content-addressed packfile, insertion order is NOT preserved (a packed genome is canonicalised to sorted-label order). The first import SEEDS dest (when it has no genome yet); the rest APPEND byte-for-byte; all the bundles MUST share one coupling invariant (the same the_one) — a mismatched .chr is a GenomeBoundingError, a duplicate label a ValueError. Byte-identical to the source iff the source was already in canonical sorted-label order; otherwise re-canonicalises while preserving every chromosome's bytes. Raises ValueError if loose_dir holds no .chr files. numpy-free.",
            parameters=(P("loose_dir", "str", True, "the directory of loose .chr bundles (e.g. genome_explode's output)"),
                        P("dest", "str", True, "the dest packed genome directory (seeded fresh if it has no genome, else appended/merged into)"),
                        P("the_one", "HV", False, "the held invariant (only consulted for a manifest-less EXISTING dest — the §44 rebuild width; each .chr carries its own the_one)")),
            returns=R("dict", "the dest manifest data (the assembled packed genome)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_register_attested", owner="srmech", category="genome",
            summary="Register a directory of loose .chr bundles as AMSC attested sources (UPSTREAM §43; the bundling->AMSC compose, F729). For every <label>.chr in chr_dir (a genome_explode output) it writes a per-chromosome <amsc_root>/<label>/descriptor.toml + row.ndjson, then calls srmech.amsc.catalog.register_attested_root so each chromosome appears in srmech.amsc.catalog.list_attested_sources (one AMSC source per chromosome, keyed by its label, literature_curated adapter). The chromosome's OWN MPR attestation — carried in its .chr (attestation.response_sha256 == the region hash) and echoed into its row.ndjson — IS the provenance; this surfaces it through the AMSC catalog, it does NOT mint a parallel attestation (F730). Returns {ok, amsc_root, source, chromosomes:[{label, source_key, descriptor_path, row_path, region_sha256}], register}. Raises ValueError if chr_dir holds no .chr files or a label is not a filename-safe source key. numpy-free.",
            parameters=(P("chr_dir", "str", True, "the directory of loose .chr bundles to register (e.g. genome_explode's output)"),
                        P("amsc_root", "str", True, "where the per-chromosome <label>/descriptor.toml + row.ndjson AMSC root is written"),
                        P("source", "str", True, "the AMSC source identifier recorded for the registration (e.g. 'srmech.genome.<name>')")),
            returns=R("dict", "{ok, amsc_root, source, chromosomes, register} — the per-chromosome AMSC sources registered"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class K — equation-of-centre / pin-slot
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.kepler.pin_slot", owner="srmech", category="kepler",
            summary="Antikythera pin-and-slot transform: phi = atan2(i sin θ, "
                    "d + i cos θ). Continuous projection-shadow of Class I "
                    "cyclic-group upstream (Freeth 2021 Supp S9).",
            parameters=(P("theta", "float", True, "input shaft angle (radians)"),
                        P("pin_offset", "float", True, "pin radius i"),
                        P("pin_distance", "float", True, "axis separation d")),
            returns=R("float", "follower angle phi (radians)"),
        ),
        ToolEntry(
            name="srmech.amsc.kepler.kepler_solve", owner="srmech", category="kepler",
            summary="Newton-Raphson on Kepler's equation M = E - e sin E. "
                    "Smith (1979) starter; converges in 4-6 iter for e < 0.5.",
            parameters=(P("M_rad", "float", True, "mean anomaly (radians)"),
                        P("e", "float", True, "eccentricity, 0 ≤ e < 1"),
                        P("tolerance", "float", False, "default 1e-12"),
                        P("max_iter", "int", False, "default 30")),
            returns=R("float", "eccentric anomaly E (radians)"),
        ),
        ToolEntry(
            name="srmech.amsc.kepler.equation_of_centre", owner="srmech",
            category="kepler",
            summary="Fourier-series ν − M = Σ c_k e^k sin(k M) for k = 1..n_terms; "
                    "Brouwer & Clemence (1961) §3.2 coefficients up to k=6.",
            parameters=(P("M_rad", "float", True), P("e", "float", True),
                        P("n_terms", "int", False, "1..6, default 4")),
            returns=R("float", "ν − M (radians)"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class M — HDC binary spatter codes
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.hdc.bind", owner="srmech", category="hdc",
            summary="HDC bind: component-wise XOR of two BSC vectors. "
                    "Commutative, associative, self-inverse.",
            parameters=(P("a", "bytes", True), P("b", "bytes", True,
                          "same length as a")),
            returns=R("bytes", "bound vector"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.bundle", owner="srmech", category="hdc",
            summary="HDC bundle: bitwise majority across an odd number of vectors "
                    "(BSC convention). Even counts rejected.",
            parameters=(P("vectors", "Sequence[bytes]", True,
                          "odd-count, all same length"),),
            returns=R("bytes", "bundled vector"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.permute", owner="srmech", category="hdc",
            summary="HDC permute: cyclic bit-rotation by rotate_bits. Preserves "
                    "popcount; involutive with -rotate_bits.",
            parameters=(P("a", "bytes", True),
                        P("rotate_bits", "int", True, "may be negative")),
            returns=R("bytes", "rotated vector"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.similarity", owner="srmech", category="hdc",
            summary="HDC similarity: 1 − 2 hamming(a, b)/D ∈ [−1, 1]. "
                    "+1 identical, 0 orthogonal, −1 complementary.",
            parameters=(P("a", "bytes", True), P("b", "bytes", True)),
            returns=R("float", "in [-1, 1]"),
        ),
        # ────────────────────────────────────────────────────────────
        # Class M — polar {-1, 0, +1} variant (v0.4.3rc1). Rank-1 Class M
        # with an absorbing zero (Class M ∘ Class K): int8 {-1,0,+1}
        # hypervectors; 0 is the dead-band the pin-slot rejects.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.hdc.polar_random", owner="srmech", category="hdc",
            summary="Random polar hypervector: int8 array of D elements in "
                    "{-1, 0, +1} (the 3-state Class-M variant alphabet). "
                    "Pass an integer `seed` for a DETERMINISTIC vector "
                    "(bit-exact / attestation discipline).",
            # rc13: advertise the JSON-friendly integer `seed`, NOT the
            # un-serialisable `rng: numpy.random.Generator` (a Generator has
            # no valid JSON-Schema type and cannot cross JSON-RPC / an
            # Anthropic tool schema). In-process Python callers still have
            # the `rng=` kwarg on the function; the schema exposes only the
            # serialisable path.
            parameters=(P("D", "int", True, "dimension"),
                        P("seed", "int", False,
                          "integer seed for a deterministic vector")),
            returns=R("array", "int8 in {-1,0,+1}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_bind", owner="srmech", category="hdc",
            summary="Polar bind: element-wise sign-product with 0 absorbing "
                    "(0·x = 0). Commutative, associative; self-inverse on ±1.",
            parameters=(P("a", "HV", True, "int8 {-1,0,+1}"),
                        P("b", "HV", True, "same length")),
            returns=R("array", "int8 {-1,0,+1}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_unbind", owner="srmech", category="hdc",
            summary="Polar unbind (= sign-product). Recovers b from "
                    "bind(a,b) where a≠0; 0 is destructive.",
            parameters=(P("c", "HV", True, "int8 {-1,0,+1}"),
                        P("a", "HV", True)),
            returns=R("array", "int8 {-1,0,+1}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_bundle", owner="srmech", category="hdc",
            summary="Polar bundle: per-position sticky majority "
                    "(sign of the sum); exact ties resolve to 0. No "
                    "odd-count restriction.",
            # Variadic ``polar_bundle(*vectors)``: tool-schema exposes the
            # one-or-more-vectors VAR_POSITIONAL under a CLEAN name
            # ``vectors`` (NOT ``*vectors`` — the ``*`` sigil is illegal in
            # an Anthropic input_schema property key
            # ``^[a-zA-Z0-9_.-]{1,64}$``). Sequence type matches the
            # sibling ``srmech.amsc.hdc.bundle`` convention; the dispatcher
            # (``srmech.mcp._tools.invoke_tool``) unpacks it positionally.
            parameters=(P("vectors", "Sequence[HV]", True,
                          "one or more int8 {-1,0,+1} vectors of equal "
                          "length"),),
            returns=R("array", "int8 {-1,0,+1}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_similarity", owner="srmech", category="hdc",
            summary="Polar match-fraction in [0,1]. skip_zero=True (default) "
                    "counts only jointly non-zero positions; False counts all "
                    "(0==0 a match).",
            parameters=(P("a", "HV", True), P("b", "HV", True),
                        P("skip_zero", "bool", False, "default True")),
            returns=R("float", "in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_density", owner="srmech", category="hdc",
            summary="Fraction of non-zero (informative) positions in [0,1]; "
                    "1.0 = fully bipolar, lower = more dead-band.",
            parameters=(P("v", "HV", True, "int8 {-1,0,+1}"),),
            returns=R("float", "in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_from_real", owner="srmech", category="hdc",
            summary="Bridge real data to a polar HDC vector via sign_quantise "
                    "(Class-K threshold projection); dead_band>0 maps the "
                    "near-threshold zone to 0.",
            parameters=(P("arr", "HV", True),
                        P("threshold", "float", False, "default 0.0"),
                        P("dead_band", "float", False, "default 0.0")),
            returns=R("array", "int8 {-1,0,+1}"),
        ),
        # ────────────────────────────────────────────────────────────
        # Class M — Klein-4 {0,1,2,3} variant (v0.4.3rc2). Rank-2 abelian
        # over (F₂)²; the four states are the four (γ₅, iω₇) chirality
        # sectors. uint8 hypervectors.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.hdc.klein4_random", owner="srmech", category="hdc",
            summary="Random Klein-4 hypervector: uint8 array of D elements in "
                    "{0,1,2,3} (the rank-2 Class-M variant alphabet). "
                    "Pass an integer `seed` for a DETERMINISTIC vector "
                    "(bit-exact / attestation discipline).",
            # rc13: advertise the JSON-friendly integer `seed`, NOT the
            # un-serialisable `rng: numpy.random.Generator` (see polar_random).
            parameters=(P("D", "int", True, "dimension"),
                        P("seed", "int", False,
                          "integer seed for a deterministic vector")),
            returns=R("HV", "uint8 in {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_bind", owner="srmech", category="hdc",
            summary="Klein-4 bind: component-wise (F₂)²-XOR. Commutative, "
                    "associative, self-inverse; identity 0. rc13 sectors=/"
                    "parallel=/mode= fans it across ≤4 concurrent lanes "
                    "(default-ON at ≥4 cores; value-preserving). mode='chunk' "
                    "(default) splits positions, bit-identical; mode='chirality' "
                    "runs the F233 4-sector dispatch.",
            parameters=(P("a", "HV", True, "uint8 {0,1,2,3}"),
                        P("b", "HV", True, "same length"),
                        P("sectors", "int", False, "lanes 1..4; default-on (4 "
                          "at ≥4 cores, else 1)"),
                        P("parallel", "bool", False, "True→4 lanes / False→1 "
                          "(alias for sectors=)"),
                        P("mode", "str", False, "'chunk' (default, bit-exact) "
                          "or 'chirality' (F233 4-sector)")),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_unbind", owner="srmech", category="hdc",
            summary="Klein-4 unbind (= self-inverse XOR): recovers b from "
                    "bind(a,b).",
            parameters=(P("c", "HV", True), P("a", "HV", True)),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_bundle", owner="srmech", category="hdc",
            summary="Klein-4 bundle: per-bit majority on each of the 2 bits "
                    "independently; accepts any count n>=1 (even or odd); "
                    "exact ties (only possible for even n) → 0 for that bit. "
                    "rc13 sectors=/parallel=/mode= fans the reduction across ≤4 "
                    "concurrent lanes (default-ON at ≥4 cores). mode='chunk' "
                    "(default) splits positions, bit-identical; mode='chirality' "
                    "runs the F233 4-sector dispatch.",
            # Variadic ``klein4_bundle(*vectors)``: exposed under the clean
            # name ``vectors`` (the ``*`` sigil is illegal in an Anthropic
            # property key). See polar_bundle note above.
            parameters=(P("vectors", "Sequence[HV]", True,
                          "one or more uint8 {0,1,2,3} vectors of equal "
                          "length"),
                        P("sectors", "int", False, "lanes 1..4; default-on (4 "
                          "at ≥4 cores, else 1)"),
                        P("parallel", "bool", False, "True→4 lanes / False→1 "
                          "(alias for sectors=)"),
                        P("mode", "str", False, "'chunk' (default, bit-exact) "
                          "or 'chirality' (F233 4-sector)")),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_similarity", owner="srmech", category="hdc",
            summary="Klein-4 similarity: fraction of positions where a==b in "
                    "[0,1] (1 identical, 0 orthogonal). rc13 sectors=/parallel=/"
                    "mode= fans the comparison across ≤4 lanes (default-ON at ≥4 "
                    "cores); ALWAYS returns the serial float (chunk sums "
                    "per-slice matches; chirality recombines via sector-0).",
            parameters=(P("a", "HV", True), P("b", "HV", True),
                        P("sectors", "int", False, "lanes 1..4; default-on (4 "
                          "at ≥4 cores, else 1)"),
                        P("parallel", "bool", False, "True→4 lanes / False→1 "
                          "(alias for sectors=)"),
                        P("mode", "str", False, "'chunk' (default) or "
                          "'chirality'")),
            returns=R("float", "in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_bundle_accumulate", owner="srmech",
            category="hdc",
            summary="STREAMING klein4_bundle (UPSTREAM §50): fold ONE Klein-4 "
                    "vector into a fixed-width (1+2*D uint32) per-coordinate tally, "
                    "so a holographic store never materialises its inputs and stays "
                    "fixed-width (grows with D, not the #folded vectors). acc=None "
                    "auto-creates; returns acc (mutated in place). Native-dispatched "
                    "standalone-C kernel; the caller owns acc (no compiled-in cap).",
            parameters=(P("acc", "array('I')|None", True,
                          "the (1+2*D) uint32 accumulator, or None to create one "
                          "sized to v"),
                        P("v", "HV", True, "uint8 {0,1,2,3} vector of length D")),
            returns=R("array('I')", "the (1+2*D) uint32 accumulator"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_bundle_resolve", owner="srmech",
            category="hdc",
            summary="Resolve a klein4_bundle_accumulate accumulator to the bundled "
                    "Klein-4 vector — strict per-bit majority over n=acc[0] folded "
                    "vectors (tie → 0), BIT-IDENTICAL to klein4_bundle. Returns the "
                    "HV carrier, so a resolved bundle drops into a genome tome-leaf "
                    "or a klein4_similarity cleanup. Native-dispatched.",
            parameters=(P("acc", "array('I')", True,
                          "a (1+2*D) uint32 accumulator"),),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.cooccurrence_fold", owner="srmech",
            category="hdc",
            summary="Holographic co-occurrence store (UPSTREAM §50) — the DUAL of "
                    "the explicit-edge §17-U1 cooccurrence_edges. Folds every "
                    "(token, neighbour) within ±window into a per-token fixed-width "
                    "Klein-4 bundle WITHOUT building the edge list, so the store "
                    "grows with VOCAB (Heaps) not edges. Read out a relationship "
                    "with klein4_similarity(bundles[a], codes[b]). LOSSY "
                    "(superposition crosstalk) — the bounded associative tail.",
            parameters=(P("tokens", "Sequence[str]", True, "the token stream"),
                        P("window", "int", True, "co-occurrence radius (>= 1)"),
                        P("dim", "int", True, "Klein-4 width D (one byte/coord)"),
                        P("seed", "int", False,
                          "base seed for the deterministic per-token codes")),
            returns=R("dict",
                      "{'bundles': {token: HV}, 'codes': {token: HV}, "
                      "'vocab': [token, ...], 'n_tokens': int}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_chirality_flip_gamma5", owner="srmech",
            category="hdc",
            summary="Flip the γ₅ chirality axis (XOR with sector mask 2).",
            parameters=(P("v", "HV", True, "uint8 {0,1,2,3}"),),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_chirality_flip_omega7", owner="srmech",
            category="hdc",
            summary="Flip the iω₇ chirality axis (XOR with sector mask 1).",
            parameters=(P("v", "HV", True, "uint8 {0,1,2,3}"),),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_cpt_mirror", owner="srmech", category="hdc",
            summary="CPT mirror: flip BOTH chirality axes (XOR with 3).",
            parameters=(P("v", "HV", True, "uint8 {0,1,2,3}"),),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_project_axis", owner="srmech",
            category="hdc",
            summary="Project a Klein-4 store onto ONE chirality axis → bipolar "
                    "{-1,+1} (the F350/F354 asymptotic-DoF render): the 2-DoF "
                    "γ₅⊕iω₇ carrier collapses to a 1-DoF bipolar vector, dropping "
                    "the OTHER axis + its self-EC (F354 axis-split). `axis` is "
                    "co-equal ('gamma5'=bit 1 / 'iomega7'=bit 0; default gamma5 "
                    "is a documented non-privileged convention). Class K "
                    "(bipolar sign render) ∘ Class C (axis select); no abs().",
            parameters=(
                P("v", "HV", True, "uint8 {0,1,2,3}"),
                P("axis", "str", False, "'gamma5' (bit 1) or 'iomega7' (bit 0)"),
            ),
            returns=R("list", "bipolar {-1,+1}, one per element"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_triality_cycle", owner="srmech",
            category="hdc",
            summary="Order-3 S₃=Aut(V₄) triality cycle of the three Klein-4 "
                    "involutions (iω₇→γ₅→CPT, identity fixed); the V₄-carrier "
                    "image of the so(8) 8v→8s→8c triality. Class I; T∘T∘T=id.",
            parameters=(
                P("v", "HV", True, "uint8 {0,1,2,3}"),
                P("inverse", "bool", False, "reverse the 3-cycle (T⁻¹ = T²)"),
            ),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_sector_count", owner="srmech", category="hdc",
            summary="Per-sector occupancy [n0,n1,n2,n3] — chirality-sector "
                    "distribution attestation.",
            parameters=(P("v", "HV", True, "uint8 {0,1,2,3}"),),
            returns=R("list[int]", "int64 length-4 counts"),
        ),
        # #797 op (a2): holographic erasure code (rc27; F353 substitute).
        # The order-2 store is k=2-DETECT; this adds k=3-CORRECT with no Z3.
        ToolEntry(
            name="srmech.amsc.hdc.klein4_holographic_encode", owner="srmech",
            category="hdc",
            summary="Holographic erasure-encode a Klein-4 store into `replicas` "
                    "copies (#797 op (a2), F353): any one replica-subregion "
                    "(1/replicas) reconstructs the whole — k=3-CORRECT with no "
                    "Z3. replicas=4 → 3/4 known-erasure, 1/4 blind correction.",
            parameters=(P("v", "HV", True, "uint8 {0,1,2,3}"),
                        P("replicas", "int", False, "redundant copies; default 4")),
            returns=R("HV", "uint8 store of length len(v)*replicas"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_holographic_decode", owner="srmech",
            category="hdc",
            summary="Reconstruct a Klein-4 store from a holographic erasure "
                    "encoding. erased=mask → first-surviving-replica (exact up "
                    "to (replicas-1)/replicas known erasure); erased=None → "
                    "per-position majority (blind, corrects ≤floor((r-1)/2)).",
            parameters=(P("store", "HV", True, "uint8; len % replicas == 0"),
                        P("replicas", "int", False, "replica count from encode"),
                        P("erased", "Optional[HV]", False,
                          "bool mask over store; True = erased")),
            returns=R("HV", "uint8 reconstructed length len(store)//replicas"),
        ),
        # #797 op (a1): explicit order-3 triality corrector (rc28; F359 contract).
        # The k=2-DETECT order-2 store gains k=3-CORRECT from the order-3 triality
        # orbit — the EXPLICIT path (op (a2) is the measured no-Z3 substitute).
        ToolEntry(
            name="srmech.amsc.hdc.klein4_triality_encode", owner="srmech",
            category="hdc",
            summary="Encode a Klein-4 store as its order-3 triality orbit "
                    "[v,T(v),T²(v)] (#797 op (a1), F359): the third block T²v is "
                    "the order-3 third vote past the order-2 4-cap, NOT an "
                    "external 3rd render. Paired with klein4_triality_correct.",
            parameters=(P("v", "HV", True, "uint8 {0,1,2,3}"),),
            returns=R("HV", "uint8 store of length len(v)*3 = [v|T(v)|T²(v)]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_triality_correct", owner="srmech",
            category="hdc",
            summary="Correct a Klein-4 store via the order-3 triality 2-of-3 "
                    "majority (#797 op (a1), F359): invert the triality to the "
                    "common v-frame (T⁻¹/T) then majority-vote — k=3-CORRECT vs "
                    "the bare order-2 k=2-DETECT. depth!=1 raises (width-only; the "
                    "continuum count-recursion is open math, F359 bar 5).",
            parameters=(P("store", "HV", True, "uint8; len % 3 == 0"),
                        P("depth", "int", False, "only 1 (the width-step) in-domain")),
            returns=R("HV", "uint8 reconstructed length len(store)//3"),
        ),
        # ────────────────────────────────────────────────────────────
        # Loop bind (Moufang) — the k=7 gauge ARITHMETIC (v0.7.0 / MS #21).
        # M∘C with a Class-K associator residue; NO new class. Baez 2002.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.hdc.loop_bind", owner="srmech", category="hdc",
            summary="The loop bind (Moufang) = the octonion / Cayley-Dickson "
                    "product. Non-commutative + non-associative ⟹ (ab)c≠a(bc): "
                    "the k=7 gauge ARITHMETIC triality is blind to (F271). M∘C "
                    "with a Class-K associator residue; NO new class. Baez 2002.",
            parameters=(
                P("x", "HV", True, "power-of-two vector (dim 8 = octonion)"),
                P("y", "HV", True, "same length as x"),
            ),
            returns=R("list[float]", "the product x·y, same length"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_conj", owner="srmech", category="hdc",
            summary="Octonion conjugate x̄ — negate the imaginary part, keep the "
                    "real anchor x[0]. The Class-C flip powering the unbind.",
            parameters=(P("x", "HV", True, "power-of-two vector"),),
            returns=R("list[float]", "conjugate, same length"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_inv", owner="srmech", category="hdc",
            summary="Moufang inverse x⁻¹ = x̄/⟨x,x⟩ — the unbind key; "
                    "loop_bind(x, loop_inv(x))=e₀. Class-K norm² gate, no abs().",
            parameters=(P("x", "HV", True, "nonzero power-of-two vector"),),
            returns=R("list[float]", "inverse, same length"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_left_op", owner="srmech", category="hdc",
            summary="Left-multiplication operator L_a(x)=a·x (the (4:3) "
                    "ordering) as a dim×dim matrix. L_a≠R_a≠R_aᵀ.",
            parameters=(P("a", "HV", True, "power-of-two vector"),),
            returns=R("Mat", "dim×dim matrix"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_right_op", owner="srmech", category="hdc",
            summary="Right-multiplication operator R_a(x)=x·a (the (3:4) mirror "
                    "ordering) as a dim×dim matrix.",
            parameters=(P("a", "HV", True, "power-of-two vector"),),
            returns=R("Mat", "dim×dim matrix"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_associator", owner="srmech", category="hdc",
            summary="(a·b)·c − a·(b·c) = the Class-K associator RESIDUE of the "
                    "loop bind (zero on a Fano line, nonzero off it = the "
                    "(4:3)|(3:4) boundary). =−([L_a,R_b]·c-style residue).",
            parameters=(
                P("a", "HV", True, "power-of-two vector"),
                P("b", "HV", True, "same length"),
                P("c", "HV", True, "same length"),
            ),
            returns=R("list[float]", "the associator, same length"),
        ),
        # ────────────────────────────────────────────────────────────
        # 7-D cross product + G₂ associative 3-form (v0.7.0rc2 / MS #21 #813).
        # Ground-truth derived FROM the shipped loop_bind (F281). No new class.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.hdc.cross7", owner="srmech", category="hdc",
            summary="The 7-D cross product x×y = Im(loop_bind(x,y)) (drop the e₀ "
                    "real anchor). Antisymmetric; for imaginary x,y = ½(xy−yx). "
                    "M (bind) ∘ C (imaginary-part ordering). Identity "
                    "‖x×y‖²=‖x‖²‖y‖²−⟨x,y⟩². Baez 2002 §4.",
            parameters=(
                P("x", "HV", True, "power-of-two vector (dim 8 = octonion)"),
                P("y", "HV", True, "same length as x"),
            ),
            returns=R("list[float]", "x×y, same length (e₀ component zero)"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.g2_three_form", owner="srmech", category="hdc",
            summary="The associative calibration 3-form φ(x,y,z)=⟨x, cross7(y,z)⟩ "
                    "=⟨x, Im(y·z)⟩. Fully antisymmetric; nonzero ±1 on exactly the "
                    "7 Fano associative 3-planes, 0 on the other 28 triples. "
                    "(M∘C)∘⟨·,·⟩ contraction (Class-L/M). Harvey–Lawson 1982.",
            parameters=(
                P("x", "HV", True, "power-of-two vector"),
                P("y", "HV", True, "same length"),
                P("z", "HV", True, "same length"),
            ),
            returns=R("float", "the 3-form value (scalar)"),
        ),
        # ────────────────────────────────────────────────────────────
        # Block-octonion HD tiling (v0.7.0rc4 / MS #21 #811). Direct sum of
        # NB dim-8 loop_binds; block-diagonal; capacity-free vs Klein-4 (#812).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.hdc.loop_bind_hd", owner="srmech", category="hdc",
            summary="Block-octonion HD bind: D=NB·8 hypervector bound block-wise "
                    "by the octonion loop_bind = the direct sum ⊕ of NB independent "
                    "dim-8 Moufang binds (block-diagonal, no coupling). Carries "
                    "order/tree/direction at no capacity cost vs the Klein-4 XOR "
                    "bind (capacity-free, #812). M over a direct-sum tile; no new "
                    "class. F289.",
            parameters=(
                P("x", "HV", True, "length = positive multiple of 8"),
                P("y", "HV", True, "same length as x"),
            ),
            returns=R("list[float]", "the block-wise product, same length"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_unbind_hd", owner="srmech", category="hdc",
            summary="HD unbind: per-block Moufang left-division conj(a_k)·b_k. "
                    "Recovers v from loop_bind_hd(a, v) for unit-per-block a "
                    "(conj(a)·(a·v)=v by alternativity). Class-K clean; no abs(). "
                    "F289.",
            parameters=(
                P("a", "HV", True, "length = positive multiple of 8"),
                P("b", "HV", True, "same length as a"),
            ),
            returns=R("list[float]", "the unbound vector, same length"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_conj_hd", owner="srmech", category="hdc",
            summary="Per-block HD octonion conjugate: the direct sum ⊕ of NB "
                    "dim-8 loop_conjs — THE missing atom under loop_bind_hd / "
                    "loop_unbind_hd. The single-element loop_conj is global and "
                    "silently wrong on an HD block vector; this is per-block. "
                    "Class C; no new class. F-§12.1.",
            parameters=(
                P("x", "HV", True, "length = positive multiple of 8"),
            ),
            returns=R("list[float]", "the per-block conjugate, same length"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_inv_hd", owner="srmech", category="hdc",
            summary="Per-block HD Moufang inverse: the direct sum ⊕ of NB dim-8 "
                    "loop_invs (x̄_k/⟨x_k,x_k⟩ per block) — the per-block unbind "
                    "key. The single-element loop_inv is global and silently "
                    "wrong on an HD block vector; this is per-block. Class-K "
                    "clean (per-block norm² gate, no abs()). F-§12.1.",
            parameters=(
                P("x", "HV", True, "length = positive multiple of 8"),
            ),
            returns=R("list[float]", "the per-block inverse, same length"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.loop_runbind_hd", owner="srmech", category="hdc",
            summary="HD RIGHT-unbind: per-block Moufang right-division "
                    "b_k·conj(a_k). Where loop_unbind_hd peels the LEFT factor, "
                    "this peels the RIGHT — recovers v from loop_bind_hd(v, a) "
                    "for unit-per-block a ((v·a)·conj(a)=v by alternativity). "
                    "Right-division for a left-fold sequence store. Class-K "
                    "clean; no abs(). F-§12.2.",
            parameters=(
                P("a", "HV", True, "length = positive multiple of 8"),
                P("b", "HV", True, "same length as a"),
            ),
            returns=R("list[float]", "the right-unbound vector, same length"),
        ),
        # ────────────────────────────────────────────────────────────
        # Class K ∘ L composition — signed-sum coupling score (v0.4.3rc3).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.coupling.signed_sum_squared", owner="srmech",
            category="coupling",
            summary="Per-element (Σ_sources (2·bit−1))² across a stack of "
                    "bit-arrays. Class K (bipolar sign-projection) ∘ Class L "
                    "(signed-magnitude-squared) composition; squared coupling "
                    "strength in [0, n_sources²].",
            parameters=(P("sources", "Sequence[Vec]", True,
                          "non-empty, equal-length 1-D arrays of bits {0,1}"),),
            returns=R("Vec", "squared signed-sum per position (numpy-free 1-D "
                             "carrier; integer scores exact as float64)"),
        ),
        # ────────────────────────────────────────────────────────────
        # Foundational cross-domain cascade catalog (v0.4.3rc6).
        # The cascades recurring across every/most domains, promoted so a
        # named cascade is the default and a math-library call the exception.
        # Compositions of existing A–N primitives; no new C symbol.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.cascade.pin_slot_at_zero", owner="srmech",
            category="cascade",
            summary="Class K pin-slot at zero: split x into (orientation ∈ "
                    "{-1,0,+1}, magnitude ≥ 0). Sign-flip IS the canonical "
                    "Class K phase-boundary; the cascade-honest split that "
                    "replaces a bare abs()." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("x", "float", True, "a real value"),),
            returns=R("tuple[int, float]", "(orientation, magnitude)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.reorient", owner="srmech",
            category="cascade",
            summary="Class C cascade-orientation: re-apply a captured "
                    "orientation {-1,0,+1} to a value (negates iff "
                    "orientation < 0). Data-first DSL stage — value is "
                    "positional, orientation is keyword-only (op=\"reorient\" "
                    "+ orientation=-1). Pairs with pin_slot_at_zero."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("value", "number", True, "magnitude to re-sign (data arg, first)"),
                        P("orientation", "int", True, "in {-1,0,+1}; keyword-only")),
            returns=R("number", "value, negated iff orientation < 0"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.magnitude", owner="srmech",
            category="cascade",
            summary="Class K pin-slot at zero, magnitude only (orientation "
                    "discarded). The cascade-honest replacement for Python "
                    "abs() when only |x| is needed." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("x", "float", True, "a real value"),),
            returns=R("float", "|x| as the Class K pin-slot magnitude"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.best_rational_signed", owner="srmech",
            category="cascade",
            summary="Class K ∘ N ∘ C: float → signed small-denominator "
                    "rational. Strip sign at the Class K pin-slot, find the "
                    "Class N best-rational of the magnitude, re-apply the "
                    "sign as Class C (no abs(); sign lives in numerator)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("x", "float", True, "the float to anchor"),
                        P("max_denominator", "int", False, "Class N ceiling; default 100"),
                        P("fine_scale", "int", False, "magnitude→int-pair scale; default 1e6")),
            returns=R("tuple[int, int]", "(signed_numerator, positive_denominator)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cyclic_gcd", owner="srmech",
            category="cascade",
            summary="Class I cyclic gcd (delegates to srmech.amsc.cyclic.gcd). "
                    "The cascade-named alias for reaching the Class I primitive "
                    "instead of math.gcd." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "int", True), P("b", "int", True)),
            returns=R("int", "gcd(a, b)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.kuramoto_step", owner="srmech",
            category="cascade",
            summary="Advance N COUPLED OSCILLATORS one synchronization step "
                    "(the canonical Kuramoto model) — reach for this for "
                    "coupled-phase / synchronization dynamics. A plain DSL "
                    "stage-op (kind='stage'): the piped value is `theta`; "
                    "pass `omega=` (+ optional `coupling`/`dt`) as stage "
                    "kwargs. One forward-Euler step: "
                    "theta_i <- theta_i + dt*(omega_i + (K/n)*Σ_j "
                    "sin(theta_j - theta_i)). The coupled-oscillator dispatch-"
                    "clock Euler step the spectral-research arc hand-rolled in "
                    "Python (F141/F231/R-95/F234) — now C-parity'd "
                    "(srmech_cascade_kuramoto_step_f64, O(n²) sin-coupling "
                    "native; libm sin like kepler) so srmech runs it with NO "
                    "host Python. Honest composition: Class I cyclic phase + "
                    "sin coupling + sum-reduce + Class-C Euler add; NOT a new "
                    "privileged primitive. No abs(). Dispatches to C when "
                    "HAS_NATIVE (libm-trig tolerance parity); pure-Python "
                    "fallback otherwise. n==1 is pure drift; n==0 is []. rc14 "
                    "(§11.1): the GENERALISED Kuramoto-Sakaguchi step — pass "
                    "`adjacency` (n×n coupling matrix; non-symmetric → DIRECTED "
                    "coupling, Laplacian → graph-structured; None → all-to-all "
                    "uniform K/n), `alpha` (Sakaguchi phase frustration, "
                    "sin(θ_j−θ_i−α)), and/or `pin_anchor`+`pin_strength` (per-"
                    "oscillator pinning +p_i·sin(ψ_i−θ_i)). Co-equal C peer "
                    "srmech_cascade_kuramoto_step_general_f64 (additive; ABI "
                    "stays 3). Defaults reproduce the plain step byte-for-byte."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("theta", "sequence", True, "current phases (radians)"),
                        P("omega", "sequence", True,
                          "natural frequencies; same length as theta"),
                        P("coupling", "float", False, "global coupling K; default 1.0"),
                        P("dt", "float", False, "forward-Euler time step; default 0.01"),
                        P("adjacency", "list", False,
                          "optional n×n coupling matrix; A[i][j] weights "
                          "sin(θ_j−θ_i−α); non-symmetric=directed; None=uniform K/n"),
                        P("alpha", "float", False,
                          "Sakaguchi phase frustration (radians); default 0.0"),
                        P("pin_anchor", "Optional[list[float]]", False,
                          "optional length-n anchor phases ψ (None=no pinning)"),
                        P("pin_strength", "number", False,
                          "pinning strength p (scalar or length-n); default 1.0")),
            returns=R("list[float]", "phases after one forward-Euler Kuramoto step"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.autocorrelation", owner="srmech",
            category="cascade",
            summary="Class L CIRCULAR AUTOCORRELATION (Wiener-Khinchin) of a "
                    "real sequence — reach for this for the autocorrelation ↔ "
                    "power-spectrum object. A plain DSL stage-op (kind='stage'): "
                    "the piped value is the signal `x`; returns the length-n "
                    "autocorrelation r with r[k] = Σ_i x[i]·x[(i+k) mod n] and "
                    "r[0] = Σ x² = energy. EXACTLY the spectral object "
                    "r = Re(IFFT(|FFT(x)|²)) (circular-convolution theorem) — "
                    "that identity is WHY it is Class L. The F290 §C 'un-flatten' "
                    "composite (autocorr → difference-graph → conservation-"
                    "validate) consumes r (the r[0] energy for its conservation "
                    "check), so this primitive lets that catalog be authored as "
                    "pure-TOML composites. Honest shape: a Σ-reduce of products, "
                    "NO abs(), NOT a new privileged primitive. Dispatches to the "
                    "co-equal C peer srmech_autocorrelation_f64 (the DIRECT O(n²) "
                    "multiply-add sum — JPL-clean: no FFT, no recursion, no "
                    "transcendentals, embedded-ready) when HAS_NATIVE; the no-"
                    "native fallback computes the SAME direct sum in pure Python "
                    "(math.fsum; numpy-free since v0.7.0rc30, UPSTREAM §22). Parity "
                    "of the native sum to FFT round-off (~1e-12, NOT bit-exact — "
                    "different accumulation order). n==0 is []." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("x", "sequence", True, "the real signal (length n)"),),
            returns=R("list[float]",
                      "length-n circular autocorrelation r; r[0] = Σ x² = energy"),
        ),
        # Quaternion / octonion DFT composites (v0.7.0rc31; #863, F380) — the
        # native transform for a Klein-4 object. COMPOSITES over qm.octonion
        # left/right-mult atoms; scientific tier (§22: numpy on call).
        ToolEntry(
            name="srmech.amsc.cascade.quaternion_dft", owner="srmech",
            category="cascade",
            summary="QUATERNION discrete Fourier transform (QDFT) — the native "
                    "transform for a Klein-4 object. A Klein-4 object has TWO Z₂ "
                    "chirality axes (Klein-4 = Q₈/{±1} ≅ Z₂×Z₂, F380); a COMPLEX "
                    "FFT first projects it to ℂ and collapses one axis (the flat "
                    "shadow). The QDFT's ℍ coefficient algebra MATCHES the object's "
                    "value algebra, so BOTH axes survive. Composite over the "
                    "qm.octonion left/right-mult atoms (the ℍ non-commutativity is "
                    "load-bearing → genuine left/right forms; the twiddle "
                    "exp(μθ)=cos θ+μ·sin θ cannot be factored out as in the complex "
                    "FFT). X[k]=Σ_n exp(σ·μ·2πkn/N)·x[n]; inverse(forward(x))=x to "
                    "float round-off, recovering ALL FOUR components. Class M (Clifford/"
                    "HDC multiply) ∘ C (twiddle ±μ orientation) ∘ N (rational angle "
                    "kn/N); no new primitive class, no abs(). Scientific tier "
                    "(UPSTREAM §22): requires numpy on call. Sangwine & Ell (2012), "
                    "arXiv:1001.4379." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True,
                  "N quaternion samples, each [q0,q1,q2,q3] (or 8-vec octonion with e4..e7=0)"),
                P("form", "str", False, "'left' (W·x) or 'right' (x·W); default 'left'"),
                P("mu_axis", "str", False, "transform axis μ: 'i'|'j'|'k'|'ijk'; default 'i'"),
                P("inverse", "bool", False, "inverse QDFT (conjugate twiddle + 1/N); default False"),
            ),
            returns=R("list[list[float]]", "N quaternions (4-component lists)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.octonion_dft", owner="srmech",
            category="cascade",
            summary="OCTONION discrete Fourier transform (ODFT) — the (8:7) rung "
                    "above the QDFT. Composite over the qm.octonion left/right-mult "
                    "atoms. Carries the F378 NON-ASSOCIATIVITY as an EXPLICIT declared "
                    "field: the two-sided ODFT (W_l·x·W_r) is not unique, so "
                    "`bracketing` ∈ {'left_associated','right_associated'} "
                    "((W_l·x)·W_r vs W_l·(x·W_r)) MUST be stated — these differ for "
                    "octonions. The one-sided forms ('left'/'right') round-trip "
                    "(inverse(forward(x))=x); the two-sided form is forward-only "
                    "(its inverse is open under non-associativity → raises). Class M "
                    "(octonion multiply) ∘ C (twiddle orientation) ∘ N (rational "
                    "angle); no new primitive class, no abs(). Scientific tier "
                    "(UPSTREAM §22): requires numpy on call. Błaszczyk (2019), "
                    "arXiv:1905.12631; origin Hahn & Snopek (2011), Bull. Polish "
                    "Acad. Sci. 59(2):167–181." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True, "N octonion samples, each 8-component [e0..e7]"),
                P("form", "str", False, "'left'|'right'|'two_sided'; default 'left'"),
                P("mu_axis", "str", False, "left/single axis μ: 'i'|'j'|'k'|'ijk'; default 'i'"),
                P("bracketing", "str", False,
                  "two-sided association: 'left_associated'|'right_associated' (F378); default 'left_associated'"),
                P("two_sided_right_axis", "str", False, "right twiddle axis μ_r; default 'j'"),
                P("inverse", "bool", False, "inverse ODFT (one-sided only); default False"),
            ),
            returns=R("list[list[float]]", "N octonions (8-component lists)"),
        ),
        # Bidirectional (σ,θ,μ) hypercomplex coupler (v0.7.2rc1; #908, F436/F437).
        # Registered under its STABLE FLAT public name
        # ``srmech.amsc.cascade.hypercomplex_couple``; the submodule-dotted
        # ``srmech.amsc.cascade.hypercomplex_dft.hypercomplex_couple`` is the same
        # object re-exported flat (exempt in test_tool_schema_coverage).
        ToolEntry(
            name="srmech.amsc.cascade.hypercomplex_couple", owner="srmech",
            category="cascade",
            summary="Bidirectional (σ,θ,μ) hypercomplex coupler — bind ≥3 streams "
                    "into one quaternion/octonion + a JOINT coherence channel, and "
                    "unbind losslessly (#908, F436/F437). Where quaternion_dft / "
                    "octonion_dft CARRY N streams along named single axes, this "
                    "COUPLES them: it packs `streams` into the imaginary slots of a "
                    "carrier q and applies T=exp(σ_eff·μ·θ). A DIAGONAL μ "
                    "((i+j+k)/√3 for ℍ, (Σeₙ)/√7 for 𝕆) folds the streams into the "
                    "real/anchor channel as a coherence detector (F436: coherent "
                    "add ∝ n·s, incoherent cancel ∝ √n → anchor-energy ratio ≈ n). "
                    "Bind (sigma=+1) then unbind (sigma=-1, the CONJUGATE twiddle "
                    "exp(-μθ)) recovers q exactly via the division-algebra identity "
                    "x̄·(x·y)=‖x‖²·y — GUARANTEED reversible only up to 𝕆 (the "
                    "Hurwitz boundary; sedenion zero-divisors break it) → lossless "
                    "for ≤7 streams. forward/reverse/left/right are discrete points "
                    "of the continuous (σ,θ,μ) family = the_one's 𝕊(σ,θ) (F420) plus "
                    "the axis μ. Class M (octonion multiply) ∘ C (σ/conjugation "
                    "orientation) ∘ N (rational phase θ); no new algebra, no abs(). "
                    "Scientific tier (UPSTREAM §22): requires numpy on call."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("streams", "sequence", True,
                  "≤3 reals → quaternion imag carrier; 4–7 → octonion imag; a "
                  "length-4/8 sequence is a literal quaternion/octonion (feeds back "
                  "in to unbind)"),
                P("axis", "str", False,
                  "coupling axis μ: 'diagonal' (default) | 'i'|'j'|'k'|'ijk' | a unit "
                  "pure-imaginary vector. A single named axis carries, not couples"),
                P("theta", "float", False,
                  "continuous coupling phase; default π/2 (the F436 quarter-turn fold)"),
                P("sigma", "int", False, "chirality σ ∈ {+1,-1}: +1 binds, -1 unbinds; default +1"),
                P("form", "str", False, "'left' (T·q) or 'right' (q·T); default 'left'"),
                P("inverse", "bool", False, "flip the effective sign (≡ toggling sigma); default False"),
            ),
            returns=R("list[float]",
                      "the coupled value — a 4-component quaternion (≤3 streams) or "
                      "8-component octonion"),
        ),
        # Hamming / GF(2) linear block-code family (v0.7.2rc2; #910 / §30,
        # F442/F449) — the CARRY/EC half of the sedenion front-loader. Rosetta
        # PAIR: pure-Python spec + JPL-clean srmech_hamming_* C peer, attested
        # bit-exact by tests/test_cascade_hamming_parity.py.
        ToolEntry(
            name="srmech.amsc.cascade.hamming_encode", owner="srmech",
            category="cascade",
            summary="Encode k = 2ⁿ−1−n data bits into a Hamming(2ⁿ−1, k) "
                    "single-error-correcting GF(2) codeword (#910 / §30). The "
                    "CARRY/EC half of the sedenion front-loader: where "
                    "hypercomplex_couple (COUPLE) binds ≤7 streams reversibly into "
                    "an octonion (capped at 𝕆 by Hurwitz), the Hamming code CARRIES "
                    ">7 data items + error-correction in one structure using the "
                    "sedenion's CODE geometry (its Fano/PG structure, NOT its broken "
                    "chirality). Canonical 1-indexed construction: parity bits at the "
                    "power-of-two positions, each the even-parity XOR of the positions "
                    "it covers. Lean-ALU XOR-native (GF(2) add = parity = XOR); no "
                    "float, no libm, no abs(). Hamming(7,4) IS the octonion's own Fano "
                    "plane (F441). Class B (structure framing) ∘ I (cyclic index "
                    "arithmetic) ∘ A (content integrity). SSoT: Hamming (1950)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("data_bits", "sequence", True,
                  "exactly 2ⁿ−1−n data bits, each 0/1 (4 for H(7,4), 11 for H(15,11))"),
                P("n", "int", True, "parity-bit count, 2 ≤ n ≤ 16; codeword length is 2ⁿ−1"),
            ),
            returns=R("list[int]", "the 2ⁿ−1-bit codeword (0/1 list)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.hamming_syndrome", owner="srmech",
            category="cascade",
            summary="Compute the Hamming syndrome — the 1-indexed position of the "
                    "single flipped bit (0 = clean) (#910 / §30). Recompute each "
                    "power-of-two parity; the failed set read as a binary number IS "
                    "the error position (Hamming's construction). Lean-ALU XOR; no "
                    "float, no libm. Class A (content-addressed error locator)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("codeword", "sequence", True, "a 2ⁿ−1-bit codeword (0/1 list)"),
            ),
            returns=R("int", "1-indexed flipped-bit position; 0 if the word is clean"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.hamming_decode_correct", owner="srmech",
            category="cascade",
            summary="Locate + correct any single-bit error and recover the data "
                    "payload (#910 / §30). Single-error-correcting (minimum distance "
                    "3): a clean or single-error word recovers exactly. The located "
                    "bit is flipped (Class K sign-flip at the syndrome slot, GF(2)). "
                    "Lean-ALU XOR; no float, no libm, no abs()."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("codeword", "sequence", True, "a 2ⁿ−1-bit codeword (0/1 list)"),
            ),
            returns=R("dict",
                      "{'data': k corrected payload bits, 'error_position': int "
                      "(0=clean), 'corrected_codeword': the repaired 2ⁿ−1-bit word}"),
        ),
        # Cayley–Dickson open-exterior boundary-demonstrator (v0.7.3rc1; #915 /
        # MFO §VII.6.23) — the deliberately NON-reversible object past the Hurwitz
        # wall. Registered under STABLE flat names ``srmech.amsc.cascade.cd_*`` etc.;
        # the submodule-dotted ``cascade.cayley_dickson.*`` are the same objects
        # re-exported flat (exempt in test_tool_schema_coverage).
        ToolEntry(
            name="srmech.amsc.cascade.cd_mult", owner="srmech",
            category="cascade",
            summary="Exact-rational Cayley–Dickson product of two equal-dimension "
                    "elements (#915 / MFO §VII.6.23). Generic ℝ→ℂ→ℍ→𝕆→𝕊(16)→… "
                    "doubling, numpy-free, each component a Fraction. This is the "
                    "OPEN-EXTERIOR demonstrator, NOT a substrate extension: the_one / "
                    "hypercomplex_couple live in the reversible interior (≤𝕆); this is "
                    "the non-division object past the Hurwitz wall where the product "
                    "loses its inverse. Class M (bilinear bind) ∘ C (conjugation-ordered "
                    "cross terms) ∘ K (sign-flip; no abs())."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("a", "sequence", True, "first element — a power-of-two-length sequence of ints/Fractions"),
                P("b", "sequence", True, "second element — same dimension as a"),
            ),
            returns=R("tuple", "the product, a tuple of exact Fractions"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_conjugate", owner="srmech",
            category="cascade",
            summary="Cayley–Dickson conjugation — negate the imaginary part (Class K "
                    "sign-flip, no abs()). Defined at EVERY rung: x·x̄ = N(x)·1 even "
                    "where the product has no inverse (§VII.6.23.3: chirality persists; "
                    "its reversing power does not)." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("a", "sequence", True, "a power-of-two-length element"),
            ),
            returns=R("tuple", "the conjugate, a tuple of exact Fractions"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_norm_sq", owner="srmech",
            category="cascade",
            summary="The squared norm N(x) = Σ xᵢ² (exact rational; x·x̄ = N(x)·1). "
                    "Positive-definite at every rung. The composition identity "
                    "N(x·y) = N(x)·N(y) holds for dims ≤ 8 and FAILS at 16 (a "
                    "zero-divisor pair has N(x·y)=0 while N(x)·N(y)≠0; §VII.6.23 C3)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("a", "sequence", True, "a power-of-two-length element"),
            ),
            returns=R("Fraction", "the squared norm Σ xᵢ²"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_basis_product", owner="srmech",
            category="cascade",
            summary="The integer structural core — basis-unit cocycle e_i·e_j = "
                    "sign·e_index (the result index is i⊕j; the sign carries the Fano/"
                    "orientation structure). Integer-only; the JPL-clean C peer "
                    "srmech_cd_basis_product returns the identical (index, sign) "
                    "(Rosetta-attested by test_cascade_cayley_dickson_parity.py)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("dim", "int", True, "algebra dimension (power of two ≤ 64)"),
                P("i", "int", True, "first basis index in [0, dim)"),
                P("j", "int", True, "second basis index in [0, dim)"),
            ),
            returns=R("tuple", "(index, sign) with index in [0, dim), sign in {+1,-1}"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.sedenion_zero_divisor_witness", owner="srmech",
            category="cascade",
            summary="Exhibit a concrete sedenion (dim 16) zero divisor: x, y both "
                    "nonzero with x·y = 0 — found from OUR OWN multiplication table "
                    "(own-work-first, not a literature transcription). The executable "
                    "form of '§VII.6.23: zero divisors first appear at 16 and never "
                    "heal'. Division algebras (dims 1,2,4,8) provably have none."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(),
            returns=R("dict",
                      "{'dim':16, 'x','y': Fraction tuples, 'x_form','y_form': "
                      "'e_i ± e_j' strings, 'x_norm_sq','y_norm_sq': nonzero, "
                      "'product': all-zero, 'product_is_zero': True}"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.left_mult_kernel", owner="srmech",
            category="cascade",
            summary="Exact-rational kernel basis of the map u ↦ x·u. NONEMPTY ⟺ x is "
                    "a left zero divisor ⟺ multiply-by-x is non-injective ⟺ no inverse "
                    "map exists — the 'no backward direction to point' of §VII.6.23.4 "
                    "(anything past and unobserved is lost). Empty for every nonzero "
                    "element of a division algebra (≤𝕆). Class L (linear-algebra rank)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True, "a power-of-two-length element"),
            ),
            returns=R("list", "kernel-basis vectors (Fraction tuples); empty if invertible"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.left_mult_is_invertible", owner="srmech",
            category="cascade",
            summary="True iff u ↦ x·u is a bijection (a backward direction exists). "
                    "Always True for nonzero x at dims ≤ 8; False for a zero divisor at "
                    "dim ≥ 16 — the reversibility that ends at the Hurwitz wall."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True, "a power-of-two-length element"),
            ),
            returns=R("bool", "True iff multiply-by-x has a (two-sided) inverse map"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.is_division_algebra_dim", owner="srmech",
            category="cascade",
            summary="True iff the dim-D Cayley–Dickson algebra is a normed division "
                    "algebra (Hurwitz 1898): the reversible interior is exactly dims "
                    "1, 2, 4, 8. The boundary between the simulable ≤𝕆 substrate and "
                    "the open exterior (≥16)." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("dim", "int", True, "an algebra dimension"),
            ),
            returns=R("bool", "True for dim in {1,2,4,8}, else False"),
        ),
        # Sedenion-addressable hyper-loop RBS-HDC instrument (v0.7.4rc1; UPSTREAM
        # §31 of PR #687; F465 + F468). Registered under the STABLE flat factory
        # name ``srmech.amsc.cascade.sedenion_register``; the submodule-dotted
        # ``cascade.sedenion_register.sedenion_register`` is the same object
        # re-exported flat (exempt in test_tool_schema_coverage). The class
        # SedenionRegister is not a module-level function (not coverage-walked).
        ToolEntry(
            name="srmech.amsc.cascade.sedenion_register", owner="srmech",
            category="cascade",
            summary="Construct a SedenionRegister — the sedenion (dim-16) ADDRESSABLE "
                    "RBS-HDC instrument (UPSTREAM §31; F465/F468). The sedenion box "
                    "made into a named-register instrument: 16 slots e0..e15 — the "
                    "octonion block e0..e7 is the ≤7 REVERSIBLE working word "
                    "(hypercomplex_couple, bit-exact ≤𝕆), e8..e15 the EC/CARRY block "
                    "(Hamming GF(2), §30). HDC ops INSTEAD of ALU: random-access-by-name "
                    "(hdc.bind + nearest-codebook clean = associative superposition, "
                    "classical, no quantum cost). The genuinely-new surface is "
                    ".navigate(j) — the address↔Cayley–Dickson homomorphism (right-mult "
                    "every slot-name by e_j so addressing respects e_i·e_j=±e_k, the "
                    "cd_basis_product cocycle) — and .is_navigable(direction) the "
                    "reversibility gate (left_mult_is_invertible): single-basis nav is "
                    "always a signed permutation, composite-direction nav reversible "
                    "ONLY ≤𝕆 (the Hurwitz horizon). Pure composition of shipped "
                    "primitives — no new algebra, no abs() (sign is Class C chiral_flip). "
                    "Storage + coupler are the scientific tier (numpy on call); "
                    "navigate/is_navigable/carry/correct are numpy-free."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("D", "int", False, "hypervector width in bits (default 8192; the RBS-HDC dimension)"),
                P("codebook", "dict", False, "optional preset {name: bytes} value-vectors for read cleanup"),
            ),
            returns=R("SedenionRegister",
                      "the instrument — .write/.read (addressable storage), "
                      ".couple_working/.uncouple_working (≤7 reversible word), "
                      ".carry/.correct (EC block), .navigate/.is_navigable (hyper-loop)"),
        ),
        # Three RBS-LM UPSTREAM_NOTES candidate-additions (v0.7.4rc2; PR #687
        # §1.2 / §1.3 / rbs_nn Note 1) — pure compositions, no new primitive class.
        # The two compose ops register under flat ``cascade.*`` names (submodule-
        # dotted ``cascade.compose.*`` exempt in coverage); bundle_with_ties is a
        # Class-M op registered under its real ``srmech.amsc.hdc.*`` name.
        ToolEntry(
            name="srmech.amsc.cascade.signed_sum_squared", owner="srmech",
            category="cascade",
            summary="Element-wise squared signed-sum across a stack of bit sources "
                    "— the coupling-score composite (UPSTREAM §1.2). Per position: "
                    "s = Σ_sources (2·bit−1) (Class K bipolar transform); out = s² "
                    "(Class L signed-magnitude-square). Large where sources agree "
                    "(coherent |Σ|≈N), ~0 where they cancel — the coupling score. "
                    "No abs(): the square carries the sign boundary. Operates on a "
                    "stack of source arrays, not a single graph." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("sources", "sequence", True,
                  "non-empty sequence of equal-length 0/1 bit sequences"),
            ),
            returns=R("list[int]", "per-position squared signed-sum"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.top_k_by_score", owner="srmech",
            category="cascade",
            summary="Indices of the k highest- (or lowest-) scoring items — the "
                    "catalog selection composite (UPSTREAM §1.3). Class E (sorted-key "
                    "order) ∘ Class K (sparse truncate to top/bottom k). Stable: ties "
                    "keep ascending index order. The band-selection / weak-coupling-"
                    "prune step (top-K bands by magnitude; bottom-K bits by coupling-"
                    "square)." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("scores", "sequence", True, "one comparable score per item"),
                P("k", "int", True, "how many indices to return (0 ≤ k ≤ len(scores))"),
                P("largest", "bool", False, "True (default) → highest k; False → lowest k"),
            ),
            returns=R("list[int]", "k indices, best-first"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.bundle_with_ties", owner="srmech",
            category="hdc",
            summary="Bitwise majority across ANY number of BSC vectors, with the tie "
                    "state surfaced (UPSTREAM rbs_nn Note 1). Unlike bundle (odd N "
                    "only, no ties), accepts any N and returns (majority, ties): "
                    "majority bit = 1 where strictly >half are set (tie→0; for odd N "
                    "equals bundle exactly); ties bit = 1 where the counts are exactly "
                    "equal (even N only). A tie is a Class K event — the bundle "
                    "accumulator crossing zero (the phase-boundary / derivative-sign-"
                    "flip of MFO §VII.6.12.1), surfaced without changing the binary-"
                    "byte storage form. No abs(); counts only." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("vectors", "sequence", True,
                  "sequence of equal-length BSC byte vectors; any count (odd or even)"),
            ),
            returns=R("tuple", "(majority_bytes, ties_bytes) — each the input length"),
        ),
        # The One — S(σ,θ), the single generator of the 1+3+7+3 = 14 substrate
        # (#887). Registered under its STABLE FLAT public name
        # ``srmech.amsc.cascade.the_one``; the submodule-dotted
        # ``srmech.amsc.cascade.one.the_one`` + its ``s_generator`` alias are the
        # same object re-exported flat (exempt in test_tool_schema_coverage).
        ToolEntry(
            name="srmech.amsc.cascade.the_one", owner="srmech",
            category="cascade",
            summary="The One — S(σ,θ), the single generator of the 1+3+7+3 = 14 "
                    "substrate (#887). Builds the Hurwitz division-algebra ladder "
                    "⨁_{n=1}^{3} (ℝ·1 ⊕ σ·e^{Î_nθ}·Im 𝔸_n) (𝔸₁=ℂ, 𝔸₂=ℍ, 𝔸₃=𝕆) "
                    "as one (σ,θ)-parameterised `One` of three Blocks tiling the A–N "
                    "partition: the imaginary dims 1/3/7 carry A / I,C,J / "
                    "D,E,F,G,K,L,M, and the three ℝ·1 reals are the +3 grammar "
                    "B,H,N. e^{Î_nθ}=cosθ+Î_n sinθ is the exact-rational Class-N "
                    "epicycle (rational.{cos,sin}_series_truncate); σ is Class K "
                    "sign ∘ Class C apply (never abs()); ⨁ over n is Class I. At "
                    "n=1 (Im ℂ one-dimensional) the seed coincides with the "
                    "rotation axis so θ is inert and only σ survives. Numpy-free, "
                    "exact-rational; the opt-in One.to_numpy()/to_matrix() float "
                    "realisations are the scientific tier (§22). No new primitive "
                    "class. SSoT: Hurwitz (1898); the parallelizable-sphere ladder "
                    "S¹,S³,S⁷.",
            parameters=(
                P("sigma", "int", True, "chirality σ ∈ {+1,-1} (Class K·C sign-flip)"),
                P("theta_num", "int", True, "epicycle angle numerator (radians)"),
                P("theta_den", "int", False, "epicycle angle denominator > 0; default 1"),
                P("terms", "int", False, "Class-N Taylor depth for cos/sin; default 24"),
            ),
            returns=R("One", "structured generator: three Blocks tiling 1+3+7+3 = 14"),
        ),
        # chirality mini-set (v0.4.4): the chiral dual of an A-N operator is
        # SAME SHAPE, INVERSE (MFO §VIII.31.11; spike-verified). Compositions
        # of Class C orientation + Class K sign; no new class, no C symbol.
        ToolEntry(
            name="srmech.amsc.cascade.chiral_flip", owner="srmech",
            category="cascade",
            summary="Class C orientation reversal: reverse a sequence's "
                    "traversal order (seq[::-1]). The value-level Class C "
                    "operator; reversing a real signal is the FFT-level "
                    "chirality operator (magnitude preserved, phase inverted)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("seq", "sequence", True, "sliceable sequence"),),
            returns=R("sequence", "orientation-reversed sequence (type preserved)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.chiral_dual", owner="srmech",
            category="cascade",
            summary="Class C ∘ op ∘ Class C: run an operator in the opposite "
                    "Class-C orientation. Conjugating any operator by "
                    "chiral_flip yields its chiral dual — same spectral shape, "
                    "inverted orientation (MFO §VIII.31.11). Reduces to Class K "
                    "-1 for the sign operators; identity for real-symmetric ops."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("op", "operator_name", True,
                          "dotted NAME of a unary sequence→sequence operator "
                          "(e.g. srmech.amsc.cascade.chiral_flip); resolved "
                          "to its callable through the srmech-namespace "
                          "operator-name resolver"),
                        P("x", "sequence", True, "input sequence")),
            returns=R("sequence", "chiral_flip(op(chiral_flip(x)))"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.net_chirality", owner="srmech",
            category="cascade",
            summary="Class C net handedness of a cascade: product of per-op "
                    "orientations in {-1,0,+1} via composed reorient (no "
                    "abs-free sign multiply). Returns +1 (right), -1 (left), or "
                    "0 if any operator is orientation-neutral."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("orientations", "iterable[int]", True, "orientations in {-1,0,+1}"),),
            returns=R("int", "net handedness in {-1, 0, +1}"),
        ),
        # Klein-4 four-sector PARALLEL dispatch (v0.6.0rc6; F233 / the 4-rung).
        # A Python ORCHESTRATION layer over the C-parity'd cascade.atoms — it
        # composes ONLY chiral_flip / reorient / chiral_dual / net_chirality /
        # magnitude (no Python-only cascade capability; only the thread
        # fan-out is Python). C-orchestration parity tracked by issue #771.
        ToolEntry(
            name="srmech.amsc.cascade.parallel_sector_dispatch", owner="srmech",
            category="cascade",
            summary="PARALLELISE a cascade body instead of running it "
                    "serially: fan one cascade `body` across its ≤4 Klein-4 "
                    "chirality sectors CONCURRENTLY (ThreadPoolExecutor, "
                    "max_workers=4) — the F233 4-thread speedup. Reach for "
                    "this when you have an independent cascade body to fan "
                    "out, instead of getting locked into one thread per "
                    "cascade cycle. HIGHER-ORDER COMBINATOR (a 1→N fan-out, "
                    "kind='combinator'): it takes a *body* op + data and "
                    "returns N per-sector results, so it is NOT a plain "
                    "value→value DSL `op=` stage — in a chain, drive it via "
                    "the `parallel` discriminator "
                    "(`chain.parallel_sectors(body=…, n_sectors=4)` in "
                    "Python, or a `[[stage]]` with `parallel_body='…'` in a "
                    "TOML spec). COMPOSABLE (rc12): by default it returns the "
                    "rich per-sector dict (a leaf) — pass `combine=` "
                    "('bundle'/'mean'/'sector0'/'concat' or a callable) to "
                    "recombine the ≤4 sectors into ONE value at result['combined'] "
                    "so the dispatch is stream→stream and CHAINS / NESTS (the DSL "
                    "`parallel` stage recombines by default; `sectorize(body, "
                    "combine=…)` wraps a body as a nesting callable). Mechanism: "
                    "each sector s = inv_T_s(body(T_s(x))) on its OWN "
                    "sector-transformed input — 0 cross-thread reads (the F233 "
                    "4-way independence), so parallel == serial bit-for-bit. "
                    "T_s composes the two commuting Class-C involutions: γ₅ = "
                    "chiral_flip (reversal), iω₇ = reorient(·, orientation=-1) (per-element "
                    "sign-flip); sector 2 (γ₅-only) == cascade.chiral_dual "
                    "bit-exact (the F232 2-rung object). Z₄ quarter-turn dispatch "
                    "slots [0,1,2,3] (cyclic-order-4 TIMING, distinct from the "
                    "order-2×order-2 Klein-4 IDENTITY). Hard-capped at 4 — "
                    "Klein-4 has no order-4+ element; 8+ needs the order-3 "
                    "triality (srmech.qm.triality, F220), NOT done here. "
                    "Usefulness collapse-lattice 4/2/2/1 (bi-axial→4 distinct; "
                    "iω₇-sym→2; γ₅-sym→2; bi-sym→1). No abs() (Class K "
                    "magnitude / Class C net_chirality). The thread-count ladder "
                    "IS the chirality-access ladder (1→2→4→triality) is a "
                    "framework-reading (framework_thread_ladder_reading), NOT a "
                    "derived theorem. Composes ONLY C-parity'd cascade.atoms; "
                    "C-orchestration parity tracked by issue #771. Class C/K. "
                    "F233/R-RBS-LM-FINDING_233; F219; F220." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("body", "operator_name", True,
                          "dotted NAME of a unary sequence→sequence cascade "
                          "operator (resolved to its callable through the "
                          "srmech-namespace operator-name resolver)"),
                        P("x", "sequence", True, "input sequence"),
                        P("n_sectors", "int", False,
                          "how many of the 4 Klein-4 sectors to dispatch "
                          "(1..4; default 4; hard-capped at 4)"),
                        P("combine", "str", False,
                          "rc12 recombine: None (default; leaf dict, combined "
                          "None) | 'bundle'/'mean'/'sector0'/'concat' → one "
                          "composable value at result['combined'] so the "
                          "dispatch chains / nests")),
            returns=R("dict",
                      "{sectors:{s:{label:(γ₅,iω₇), result}}, combined "
                      "(rc12: recombined value when combine= given, else None), "
                      "z4_dispatch_slots:[0,1,2,3], independence "
                      "(cross_sector_reads 0, parallel_equals_serial, "
                      "sector2_is_chiral_dual), collapse_lattice "
                      "(n_distinct/classes/label/useful 4/2/2/1), cap "
                      "(sector_cap 4, beyond_4_needs triality), "
                      "framework_thread_ladder_reading}"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.coupled.coupled_wave", owner="srmech",
            category="cascade",
            summary="The coupled EM-quadrature DRIVE at phase theta — the "
                    "full-chirality (E, B) pair instead of a collapsed 1-bit "
                    "sign (W17 / F577 verb-flip fix). A flat sign(wave) gate "
                    "flips hard at every zero-crossing (2/cycle); the coupled "
                    "(E=sin, B=cos, 90° apart) rotates MONOTONICALLY → 0 hard "
                    "reversals, so a driven chiral/relational element (a verb) "
                    "keeps a stable bearing. The four (sign E, sign B) quadrants "
                    "ARE the four Klein-4 (γ₅, iω₇) sectors. HANDEDNESS IS A "
                    "SETTABLE CONVENTION, never hardcoded: left/right are both "
                    "first-class (the endianness posture — the substrate "
                    "privileges neither byte-order nor chirality); -handedness "
                    "is a Class-K phase sign-flip theta→-theta (no abs), and the "
                    "chosen convention is echoed back STABLE (it does not flip "
                    "with theta). Composition of calculus.{sin,cos} (C-dispatched) "
                    "+ Class-K pin_slot_at_zero — no new primitive class. "
                    "F577/F552; #928 W17." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("theta", "float", True,
                          "phase angle in radians"),
                        P("handedness", "int", False,
                          "rotation-sense convention +1 or -1 (both first-class; "
                          "default +1 is an ARBITRARY convention; -1 = Class-K "
                          "phase flip theta→-theta)"),
                        P("components", "sequence", False,
                          "the (E_fn, B_fn) quadrature pair, each 'sin' or 'cos' "
                          "and distinct; default ('sin','cos') → E=sin, B=cos")),
            returns=R("tuple",
                      "(E, B, handedness, klein4_quadrant) — the quadrature "
                      "legs (float, C-dispatched), the STABLE chosen handedness, "
                      "and (sign E, sign B) the Klein-4 sector"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.coupled.multiplex_streams", owner="srmech",
            category="cascade",
            summary="Recombine N steering WAVES into one driver — the multiplex "
                    "(W18 / F573-F577). A 'stream' is a per-step real-valued "
                    "DRIVER WAVE (a steering signal that decides which content "
                    "gets selected downstream), NOT tokens — the output is a "
                    "single steering driver; emission (the fluency-ear + manifold "
                    "gate) is a SEPARATE consumer. Ideally each stream is a "
                    "coupled (E,B) wave from coupled_wave so it carries a stable "
                    "bearing (W17+W18 compose). Per F577 the multi-stream is for "
                    "correct sentence STRUCTURE (S-V-O clause-role assignment), "
                    "not richness. Modes: 'roundrobin' (default; the validated-"
                    "best t mod N multiplex — stream t%N drives step t), "
                    "'superpose' (real-field interference: elementwise SUM + "
                    "renormalise by max magnitude — the weakest combiner, not "
                    "hdc.bundle, which is a different layer), 'pickbest' "
                    "(strongest-bearing wave each step via Class-K magnitude — a "
                    "wave pick, distinct from a content-fluency pick). roles=("
                    "'S','V','O') binds each stream to clause-slot k; the verb "
                    "stream should be a coupled bearing so its which-way can't "
                    "flip mid-clause; the role tag is stored via Class-M hdc.bind "
                    "for unbindability. No new primitive class. F573/F577; #928 "
                    "W18." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("streams", "sequence", True,
                          "N equal-length real-valued sequences (the steering "
                          "waves; ideally each a coupled_wave bearing)"),
                        P("mode", "str", False,
                          "'roundrobin' (default) | 'superpose' (real "
                          "interference sum + renorm) | 'pickbest' (max-magnitude "
                          "bearing)"),
                        P("roles", "sequence", False,
                          "optional N clause-role labels e.g. ('S','V','O'); role "
                          "k steers clause-slot k, tagged via Class-M hdc.bind")),
            returns=R("dict",
                      "{driver (the single recombined steering wave), mode, "
                      "n_streams, length, roles, role_bound (clause-slot tagging "
                      "when roles given), layer}"),
        ),
    ]
    for e in entries:
        register_tool(e)


def _register_spectral_runtime_tools() -> None:
    """Register tool entries for the ``srmech.spectral`` runtime layer
    (MS #14 rcN+1 + rcN+2 ship; v0.4.1rc14 + v0.4.2rc4).

    Covers the runtime spectral-decomposition + delta-encoding surface:
    rcN+1 entries (``decompose`` / ``delta`` / ``recompose`` /
    ``similarity``) plus rcN+2 entries (``predict`` / ``prediction_error``
    / ``truncate_sparse``). Each operation is class-operator composition
    over the existing 14-class A-N vocabulary per
    ``[[feedback_no_privileged_primitive_classes]]``; no new primitive
    class is introduced.

    v0.5.0rc16 — every one of these 7 entries is now ``mcp_callable=True``
    (the default; the rc15 ``mcp_callable=False`` +
    :data:`_SPECTRAL_HANDLE_PENDING_REASON` markers are removed). Their
    param/return surface is a ``SpectralHandle`` (or ``SpectralHandle |
    bytes``) — an opaque, frozen, bytes-bearing dataclass JSON-RPC cannot
    carry by VALUE. rc16 carries it BY REFERENCE: a producer's returned
    handle is intercepted by ``serialise_native`` and emitted as a tagged
    id object ``{"$srmech_handle": {"uuid", "name", "kind"}}`` (registered
    in the package-scope :mod:`srmech._handles` registry), and a consumer
    param is resolved back to the live object by ``coerce_param``. The union
    ``SpectralHandle | bytes`` still accepts a bare base64 ``str`` for raw
    bytes. The spectral functions THEMSELVES are byte-for-byte untouched —
    the whole voxel is wire-marshalling + registry only.
    """
    P = ToolParameter
    R = ToolReturn

    entries: List[ToolEntry] = [
        # ────────────────────────────────────────────────────────────
        # rcN+1 — decompose / delta / recompose / similarity
        # (Spike #115 design; v0.4.1rc14 ship)
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.spectral.decompose", owner="srmech",
            category="spectral",
            summary="Project a node-domain substrate state onto the "
                    "eigenbasis of a Hermitian Laplacian; return a "
                    "SpectralHandle (substrate_descriptor_hash + encoded "
                    "coefficients + content_sha + n_modes). Class chain: "
                    "Class L (Hermitian eigendecomposition; Chung 1997) ∘ "
                    "Class A (SHA-256 content-addressing for cache + "
                    "integrity)." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("state", "Vec", True, "(n,) state vector"),
                        P("laplacian", "Mat", True, "(n, n) Hermitian"),
                        P("encoder_tag", "str", False, "default 'default'")),
            returns=R("SpectralHandle", "frozen dataclass"),
        ),
        ToolEntry(
            name="srmech.spectral.delta", owner="srmech",
            category="spectral",
            summary="Bit-exact XOR delta of two coefficient byte vectors "
                    "(SpectralHandle or raw bytes). Class M (HDC bind / "
                    "XOR self-inverse) per Plate 1995 + Kanerva 2009; "
                    "Spike #114 Option B (direct on encoded coefficient "
                    "bytes). bind(a, bind(a, b)) = b." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("ref", "SpectralHandle | bytes", True),
                        P("current", "SpectralHandle | bytes", True)),
            returns=R("bytes", "same length as inputs"),
        ),
        ToolEntry(
            name="srmech.spectral.recompose", owner="srmech",
            category="spectral",
            summary="Reconstruct the node-domain state from a SpectralHandle "
                    "via inverse projection ``V·coeffs``. Class chain: "
                    "Class L (inverse eigendecomposition; Chung 1997) ∘ "
                    "Class M (SHA-256 content integrity check on handle)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("handle", "SpectralHandle", True),
                        P("laplacian", "Mat", True),
                        P("encoder_tag", "str", False, "default 'default'")),
            returns=R("list[complex]", "(n_modes,) complex128"),
        ),
        ToolEntry(
            name="srmech.spectral.similarity", owner="srmech",
            category="spectral",
            summary="HDC similarity ``1 − 2·hamming(a, b) / D`` in "
                    "[−1, +1]. Class M per Kanerva 2009 §3.2; direct on "
                    "coefficient bytes. +1 = identical, 0 = orthogonal, "
                    "−1 = anti-correlated." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "SpectralHandle | bytes", True),
                        P("b", "SpectralHandle | bytes", True)),
            returns=R("float", "in [-1, +1]"),
        ),
        # ────────────────────────────────────────────────────────────
        # rcN+2 — predict / prediction_error / truncate_sparse
        # (MS #14 rcN+2; v0.4.2rc4 ship; user direction 2026-05-19)
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.spectral.predict", owner="srmech",
            category="spectral",
            summary="Cascade-extrapolate a SpectralHandle forward ``steps`` "
                    "substrate-natural ticks via per-mode complex-phase "
                    "evolution ``exp(-i·λ_k·steps·dt)`` on the eigenbasis. "
                    "Class chain: Class C (cascade-extrapolate) ∘ Class L "
                    "(Hermitian Laplacian eigenstructure). Spike #113 + "
                    "MS #14 rcN+2 anchor. Magnitudes preserved (unitary); "
                    "phase evolves per eigenmode." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("handle", "SpectralHandle", True),
                        P("laplacian", "Mat", True),
                        P("steps", "int", False, "default 1; ticks forward"),
                        P("dt", "float", False, "default 1.0; tick magnitude"),
                        P("encoder_tag", "str", False, "default 'default'")),
            returns=R("SpectralHandle", "phase-evolved coefficients"),
        ),
        ToolEntry(
            name="srmech.spectral.prediction_error", owner="srmech",
            category="spectral",
            summary="XOR delta between predicted and observed coefficient "
                    "byte vectors; gate-by-threshold on popcount density. "
                    "Class chain: Class M (HDC XOR-bind delta) ∘ Class K "
                    "(gate-by-threshold projection). ``threshold=0.0`` "
                    "default (no gating; raw delta) per user decision "
                    "2026-05-18. When ``popcount(delta) / (8·len) <= "
                    "threshold``, returns all-zero bytes (prediction "
                    "sufficient). Composes with :func:`predict` to close "
                    "the predictive-coding cascade." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("predicted", "SpectralHandle | bytes", True),
                        P("observed", "SpectralHandle | bytes", True),
                        P("threshold", "float", False,
                          "default 0.0; in [0.0, 1.0]")),
            returns=R("bytes", "delta or all-zeros if gated"),
        ),
        ToolEntry(
            name="srmech.spectral.truncate_sparse", owner="srmech",
            category="spectral",
            summary="Sparse-truncate a SpectralHandle's coefficients: keep "
                    "the top-``keep_k`` highest-magnitude modes OR every "
                    "mode with ``|coeff| >= threshold``; zero the rest. "
                    "Class K (magnitude-band sparse-truncate / "
                    "threshold-gate) per Mallat 2008 §9.2 (best k-term "
                    "approximation) + Spike #117 anchor. Exactly one of "
                    "``keep_k`` / ``threshold`` must be supplied."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("handle", "SpectralHandle", True),
                        P("keep_k", "Optional[int]", False,
                          "top-k modes by magnitude"),
                        P("threshold", "Optional[float]", False,
                          "magnitude floor; modes >= kept")),
            returns=R("SpectralHandle", "truncated coefficients"),
        ),
    ]
    for e in entries:
        register_tool(e)


def _register_qm_tools() -> None:
    """Register tool entries for the canonical QM/QFT/SM operations layer
    (Task #217 Phase C1 / Task #220).

    Covers `srmech.qm.*` — single-particle / spin / potentials / relativistic /
    propagators / pseudo_hermitian / gauge / sm. Each entry cites the
    operation's canonical physics SSoT in its summary per
    ``[[feedback_science_is_ssot_not_project]]``.
    """
    P = ToolParameter
    R = ToolReturn

    entries: List[ToolEntry] = [
        # ────────────────────────────────────────────────────────────
        # srmech.qm.single_particle
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.single_particle.tdse_evolve", owner="srmech",
            category="qm.single_particle",
            summary="Closed-form TDSE evolution ψ(t) = V·diag(exp(-iλt))·V^H ψ(0) "
                    "via Hermitian eigenbasis. Schrödinger (1926); Sakurai §2.1.5.",
            parameters=(P("H", "Mat", True, "Hermitian (n, n)"),
                        P("psi", "Vec", True, "(n,)"),
                        P("t", "float", True)),
            returns=R("list[complex]", "(n,) complex"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.tise_solve", owner="srmech",
            category="qm.single_particle",
            summary="Time-Independent Schrödinger H ψ_n = E_n ψ_n. "
                    "Schrödinger (1926); Sakurai §2.1.3.",
            parameters=(P("H", "Mat", True, "Hermitian (n, n)"),),
            returns=R("tuple[Mat, Mat]",
                      "(eigenvalues, eigenvectors)"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.commutator", owner="srmech",
            category="qm.single_particle",
            summary="Operator commutator [A, B] = AB − BA. Sakurai §1.4.",
            parameters=(P("A", "Mat", True), P("B", "Mat", True)),
            returns=R("Mat", "(n, n)"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.heisenberg_evolve", owner="srmech",
            category="qm.single_particle",
            summary="Heisenberg-picture operator evolution A_H(t) = U†(t) A U(t). "
                    "Heisenberg (1925); Sakurai §2.2.",
            parameters=(P("A", "Mat", True), P("H", "Mat", True),
                        P("t", "float", True)),
            returns=R("Mat", "(n, n) complex"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.lattice_momentum", owner="srmech",
            category="qm.single_particle",
            summary="Lattice momentum p̂ = -i ∂_x via central-difference; "
                    "Hermitian. Sakurai §1.6; Wilson (1974).",
            parameters=(P("n", "int", True, "n_sites ≥ 2"),
                        P("dx", "float", False, "default 1.0")),
            returns=R("Mat", "(n, n) Hermitian complex"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.density_matrix", owner="srmech",
            category="qm.single_particle",
            summary="Pure-state density matrix ρ = |ψ⟩⟨ψ|. "
                    "von Neumann (1932); Sakurai §3.4.",
            parameters=(P("psi", "Vec", True, "(n,)"),),
            returns=R("Mat", "(n, n) Hermitian PSD"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.liouville_evolve", owner="srmech",
            category="qm.single_particle",
            summary="Liouville-von Neumann ρ(t) = U(t) ρ(0) U†(t). "
                    "von Neumann (1932); Sakurai §3.4.2.",
            parameters=(P("rho", "Mat", True), P("H", "Mat", True),
                        P("t", "float", True)),
            returns=R("Mat", "(n, n)"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.spin
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.spin.pauli_matrices", owner="srmech", category="qm.spin",
            summary="Pauli matrices σ_x, σ_y, σ_z. Cl(0,3) Clifford generators. "
                    "Pauli (1927); Sakurai §3.2.",
            parameters=(),
            returns=R("tuple[Mat, Mat, Mat]",
                      "each 2×2 Hermitian"),
        ),
        ToolEntry(
            name="srmech.qm.spin.pauli_identity", owner="srmech", category="qm.spin",
            summary="2×2 identity (Cl(0,3) scalar).",
            parameters=(),
            returns=R("Mat", "2×2 identity"),
        ),
        ToolEntry(
            name="srmech.qm.spin.pauli_clifford_residuals", owner="srmech",
            category="qm.spin",
            summary="Numerical residuals for {σ_i, σ_j} = 2 δ_ij I and "
                    "[σ_i, σ_j] = 2i ε_ijk σ_k. Sakurai §3.2.",
            parameters=(),
            returns=R("tuple[float, float]",
                      "(max_anticomm_dev, max_comm_dev)"),
        ),
        ToolEntry(
            name="srmech.qm.spin.pauli_spin_operator", owner="srmech",
            category="qm.spin",
            summary="Spin-½ projection S_n = (1/2) σ · n̂ for arbitrary axis. "
                    "Sakurai §3.2 eq 3.2.51.",
            parameters=(P("direction", "Vec", True, "3-vector"),),
            returns=R("Mat", "2×2 Hermitian, eigenvalues ±½"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.bell — Bell-CHSH + Tsirelson bound 2√2 bit-exact
        # identity signature (Spike #128.1, Class L ∘ I ∘ M ∘ C ∘ A).
        # Per [[user_stance_bell_inequality_as_canonical_identity_signature]]:
        # framework's strongest single identity-not-implementation signature.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.bell.chsh_pauli_combination", owner="srmech",
            category="qm.bell",
            summary="σ_x ⊗ σ_x + σ_z ⊗ σ_z as 4×4 Hermitian. Closed-form "
                    "spectrum {+2, 0, 0, −2}. Bell (1964); Sakurai §3.10.",
            parameters=(),
            returns=R("Mat", "(4, 4) Hermitian complex"),
        ),
        ToolEntry(
            name="srmech.qm.bell.chsh_operator", owner="srmech",
            category="qm.bell",
            summary="Tsirelson-optimal CHSH operator B_CHSH = A_0⊗B_0 + "
                    "A_0⊗B_1 + A_1⊗B_0 − A_1⊗B_1 with A_0=σ_z, A_1=σ_x, "
                    "B_{0,1}=(σ_z±σ_x)/√2. Cirel'son (1980).",
            parameters=(),
            returns=R("Mat", "(4, 4) Hermitian complex"),
        ),
        ToolEntry(
            name="srmech.qm.bell.operator_norm", owner="srmech",
            category="qm.bell",
            summary="Spectral norm max|λ_i| of a Hermitian matrix via Class L "
                    "hermitian_eigendecompose. Golub & Van Loan §8.5.",
            parameters=(P("H", "Mat", True, "Hermitian square"),),
            returns=R("float", "largest absolute eigenvalue"),
        ),
        ToolEntry(
            name="srmech.qm.bell.chsh_pauli_combination_norm", owner="srmech",
            category="qm.bell",
            summary="‖σ_x ⊗ σ_x + σ_z ⊗ σ_z‖ = 2 bit-exact (integer "
                    "eigenvalue spectrum). Bell (1964).",
            parameters=(),
            returns=R("float", "exactly 2.0"),
        ),
        ToolEntry(
            name="srmech.qm.bell.chsh_operator_norm", owner="srmech",
            category="qm.bell",
            summary="‖B_CHSH‖ = 2√2 bit-exact Tsirelson bound. Cirel'son "
                    "(1980); Peres §6.3.",
            parameters=(),
            returns=R("float", "≈ 2.8284271247461903"),
        ),
        ToolEntry(
            name="srmech.qm.bell.tsirelson_bound", owner="srmech",
            category="qm.bell",
            summary="Framework-asserted Tsirelson constant 2√2. "
                    "Cirel'son (1980) *Lett. Math. Phys.* 4, 93.",
            parameters=(),
            returns=R("float", "2 · sqrt(2)"),
        ),
        ToolEntry(
            name="srmech.qm.bell.classical_chsh_bound", owner="srmech",
            category="qm.bell",
            summary="Classical (Bell) CHSH upper bound = 2. Bell (1964); "
                    "CHSH (1969).",
            parameters=(),
            returns=R("float", "2.0"),
        ),
        ToolEntry(
            name="srmech.qm.bell.verify_chsh", owner="srmech",
            category="qm.bell",
            summary="Bit-exact verification of both Bell-CHSH identities: "
                    "‖σ_x⊗σ_x + σ_z⊗σ_z‖=2 and ‖B_CHSH‖=2√2. Framework's "
                    "strongest identity-level attestation per Spike #128.1.",
            parameters=(P("tolerance", "float", False, "default 1e-14"),),
            returns=R("tuple[bool, float, float]",
                      "(verified, primary_residual, tsirelson_residual)"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.potentials
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.potentials.hydrogen_radial", owner="srmech",
            category="qm.potentials",
            summary="Hydrogen-atom radial Schrödinger eigenstates via finite-"
                    "difference. Bohr (1913); Sakurai §3.7.",
            parameters=(P("n_grid", "int", False, "default 400"),
                        P("r_max", "float", False, "default 80.0"),
                        P("l_quantum", "int", False, "default 0")),
            returns=R("tuple[list[float], list[float], Mat]",
                      "(r, energies, eigenvectors)"),
        ),
        ToolEntry(
            name="srmech.qm.potentials.harmonic_oscillator_ladder", owner="srmech",
            category="qm.potentials",
            summary="Ladder operators (a, a†) truncated at n_dim. "
                    "Heisenberg (1925); Sakurai §2.3.",
            parameters=(P("n_dim", "int", False, "default 30"),
                        P("omega", "float", False, "default 1.0")),
            returns=R("tuple[Mat, Mat]", "(a, a†)"),
        ),
        ToolEntry(
            name="srmech.qm.potentials.harmonic_oscillator_hamiltonian",
            owner="srmech", category="qm.potentials",
            summary="Harmonic-oscillator Hamiltonian H = ℏω (a†a + 1/2). "
                    "Sakurai §2.3.",
            parameters=(P("n_dim", "int", False), P("omega", "float", False)),
            returns=R("Mat", "Hermitian (n_dim, n_dim)"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.relativistic
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.relativistic.minkowski_metric", owner="srmech",
            category="qm.relativistic",
            summary="Mostly-minus Minkowski metric η^{μν} = diag(+1, -1, -1, -1). "
                    "Peskin-Schroeder §3.1.",
            parameters=(),
            returns=R("Mat", "(4, 4)"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.gamma_matrices", owner="srmech",
            category="qm.relativistic",
            summary="Dirac γ-matrices in the Dirac (standard) representation. "
                    "Cl(1,3) generators. Dirac (1928); Peskin-Schroeder §3.2.",
            parameters=(),
            returns=R("tuple[Mat, ...]", "four 4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.gamma_5", owner="srmech",
            category="qm.relativistic",
            summary="γ_5 = i γ^0 γ^1 γ^2 γ^3 — chirality matrix. "
                    "Peskin-Schroeder §3.4.",
            parameters=(),
            returns=R("Mat", "4×4 Hermitian"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.clifford_residuals", owner="srmech",
            category="qm.relativistic",
            summary="Numerical residuals for {γ^μ, γ^ν} = 2 η^{μν} I, γ_5² = I, "
                    "and {γ_5, γ^μ} = 0. Peskin-Schroeder §3.2.",
            parameters=(),
            returns=R("tuple[float, float, float]", "all ~1e-14"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.weyl_left_projector", owner="srmech",
            category="qm.relativistic",
            summary="Left-chirality projector P_L = (I − γ_5)/2. "
                    "Peskin-Schroeder §3.4.",
            parameters=(),
            returns=R("Mat", "4×4 idempotent"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.weyl_right_projector", owner="srmech",
            category="qm.relativistic",
            summary="Right-chirality projector P_R = (I + γ_5)/2. "
                    "Peskin-Schroeder §3.4.",
            parameters=(),
            returns=R("Mat", "4×4 idempotent"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.charge_conjugation_matrix", owner="srmech",
            category="qm.relativistic",
            summary="Charge-conjugation matrix C = i γ^2 γ^0. "
                    "Majorana (1937); Peskin-Schroeder eq A.27.",
            parameters=(),
            returns=R("Mat", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.dirac_operator_momentum_space",
            owner="srmech", category="qm.relativistic",
            summary="Dirac operator (γ^μ k_μ − m I_4) in momentum space. "
                    "Dirac (1928); Peskin-Schroeder §3.2.",
            parameters=(P("k", "Vec", True, "4-vector"),
                        P("m", "float", True, "mass")),
            returns=R("Mat", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.klein_gordon_dispersion",
            owner="srmech", category="qm.relativistic",
            summary="Klein-Gordon dispersion E = +√(|k|² + m²). "
                    "Klein/Gordon (1926); Peskin-Schroeder §2.3.",
            parameters=(P("k_spatial", "Vec", True, "3-vector"),
                        P("m", "float", True, "≥ 0")),
            returns=R("float", "positive on-shell energy"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.four_momentum_squared", owner="srmech",
            category="qm.relativistic",
            summary="Lorentz-invariant k² = k_μ k^μ (mostly-minus convention).",
            parameters=(P("k", "Vec", True, "4-vector"),),
            returns=R("float", "may be negative for spacelike k"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.propagators
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.propagators.feynman_scalar_propagator",
            owner="srmech", category="qm.propagators",
            summary="Scalar Feynman propagator G_F(k²) = i / (k² − m² + iε). "
                    "Feynman (1949); Peskin-Schroeder §4.2.",
            parameters=(P("k_squared", "float", True),
                        P("m", "float", True, "≥ 0"),
                        P("epsilon", "float", False, "iε regulator")),
            returns=R("complex", ""),
        ),
        ToolEntry(
            name="srmech.qm.propagators.feynman_fermion_propagator",
            owner="srmech", category="qm.propagators",
            summary="Fermion Feynman propagator S_F(k) = i(γ^μ k_μ + m) / "
                    "(k² − m² + iε). Peskin-Schroeder §4.7.",
            parameters=(P("k", "Vec", True, "4-vector"),
                        P("m", "float", True),
                        P("epsilon", "float", False)),
            returns=R("Mat", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.propagators.feynman_photon_propagator",
            owner="srmech", category="qm.propagators",
            summary="Photon Feynman propagator D^{μν}(k) = -i g^{μν}/k² (Feynman "
                    "gauge); ξ-gauge with explicit k. Peskin-Schroeder §4.8.",
            parameters=(P("k_squared", "float", True),
                        P("gauge_xi", "float", False, "default 0 ⇒ Feynman"),
                        P("epsilon", "float", False),
                        P("k", "Optional[Vec]", False)),
            returns=R("Mat", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.propagators.feynman_massive_vector_propagator",
            owner="srmech", category="qm.propagators",
            summary="Massive vector propagator D^{μν}(k) = -i (g^{μν} − k^μ k^ν/m²) "
                    "/ (k² − m² + iε). Peskin-Schroeder §20.1.",
            parameters=(P("k", "Vec", True),
                        P("m", "float", True, "> 0"),
                        P("epsilon", "float", False)),
            returns=R("Mat", "4×4 complex"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.pseudo_hermitian
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.inner_product_eta", owner="srmech",
            category="qm.pseudo_hermitian",
            summary="η-deformed inner product ⟨a|b⟩_η = a^† η b. "
                    "Mostafazadeh (2002).",
            parameters=(P("a", "Vec", True), P("b", "Vec", True),
                        P("eta", "Mat", True)),
            returns=R("complex", ""),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.expectation_eta", owner="srmech",
            category="qm.pseudo_hermitian",
            summary="η-expectation ⟨O⟩_η = ⟨ψ|η O|ψ⟩ / ⟨ψ|η|ψ⟩. "
                    "Mostafazadeh (2002).",
            parameters=(P("O", "Mat", True), P("psi", "Vec", True),
                        P("eta", "Mat", True)),
            returns=R("complex", ""),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.is_pseudo_hermitian", owner="srmech",
            category="qm.pseudo_hermitian",
            summary="Check O† η = η O (η-pseudo-Hermiticity). "
                    "Mostafazadeh (2002).",
            parameters=(P("O", "Mat", True), P("eta", "Mat", True),
                        P("atol", "float", False)),
            returns=R("bool", ""),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.construct_eta_from_eigendecomposition",
            owner="srmech", category="qm.pseudo_hermitian",
            summary="Construct positive η = (V V†)^{-1} from O's eigendecomposition "
                    "so that O is η-pseudo-Hermitian. Mostafazadeh (2002).",
            parameters=(P("O", "Mat", True),
                        P("atol", "float", False)),
            returns=R("Mat", "Hermitian η"),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.pseudo_hermitian_eigenvalues_real",
            owner="srmech", category="qm.pseudo_hermitian",
            summary="Verify η-pseudo-Hermitian O has real eigenvalues (Mostafazadeh "
                    "theorem). Bender-Boettcher (1998); Mostafazadeh (2002).",
            parameters=(P("O", "Mat", True), P("eta", "Mat", True),
                        P("atol", "float", False)),
            returns=R("bool", ""),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.gauge
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.gauge.su2_generators", owner="srmech", category="qm.gauge",
            summary="SU(2) fundamental generators T^a = σ^a/2. "
                    "Peskin-Schroeder §15.1.",
            parameters=(),
            returns=R("tuple[Mat, Mat, Mat]", "three 2×2"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su2_structure_constants", owner="srmech",
            category="qm.gauge",
            summary="Levi-Civita ε^{abc} — SU(2) structure constants.",
            parameters=(),
            returns=R("list[list[list[float]]]", "(3, 3, 3) real"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su3_gell_mann_matrices", owner="srmech",
            category="qm.gauge",
            summary="Eight Gell-Mann matrices λ^1..λ^8 (Hermitian traceless 3×3). "
                    "Gell-Mann (1962).",
            parameters=(),
            returns=R("tuple[Mat, ...]", "eight 3×3"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su3_generators", owner="srmech", category="qm.gauge",
            summary="SU(3) fundamental generators T^a = λ^a/2.",
            parameters=(),
            returns=R("tuple[Mat, ...]", "eight 3×3"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su3_structure_constants", owner="srmech",
            category="qm.gauge",
            summary="SU(3) totally-antisymmetric f^{abc} (Gell-Mann). "
                    "Peskin-Schroeder eq 17.34.",
            parameters=(),
            returns=R("list[list[list[float]]]", "(8, 8, 8) real"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.lie_algebra_residual", owner="srmech",
            category="qm.gauge",
            summary="Max Frobenius violation of [T^a, T^b] = i f^{abc} T^c. "
                    "Peskin-Schroeder §15.1.",
            parameters=(P("generators", "tuple[Mat, ...]", True),
                        P("structure_constants", "list[list[list[float]]]", True)),
            returns=R("float", ""),
        ),
        ToolEntry(
            name="srmech.qm.gauge.casimir_operator", owner="srmech",
            category="qm.gauge",
            summary="Quadratic Casimir C_2 = T^a T^a (sum). Peskin-Schroeder §15.4.",
            parameters=(P("generators", "tuple[Mat, ...]", True),),
            returns=R("Mat", "= C_2(R) · I by Schur"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.casimir_eigenvalue", owner="srmech",
            category="qm.gauge",
            summary="Scalar Casimir eigenvalue C_2(R) for irreducible rep. "
                    "Fundamental: 3/4 (SU(2)), 4/3 (SU(3)).",
            parameters=(P("generators", "tuple[Mat, ...]", True),),
            returns=R("float", "≥ 0"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.gauge_connection_matrix", owner="srmech",
            category="qm.gauge",
            summary="Lie-algebra connection A = A^a T^a (Hermitian).",
            parameters=(P("A_components", "Vec", True),
                        P("generators", "tuple[Mat, ...]", True)),
            returns=R("Mat", ""),
        ),
        ToolEntry(
            name="srmech.qm.gauge.gauge_path_segment", owner="srmech",
            category="qm.gauge",
            summary="Path-segment holonomy U = exp(i g A^a T^a) via Hermitian "
                    "eigendecomp (no scipy). Wilson (1974); Peskin-Schroeder §15.3.",
            parameters=(P("A_components", "Vec", True),
                        P("generators", "tuple[Mat, ...]", True),
                        P("coupling", "float", False, "default 1.0")),
            returns=R("Mat", "unitary"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.wilson_loop_from_segments", owner="srmech",
            category="qm.gauge",
            summary="Discrete Wilson loop U(C) = ∏_k exp(i g A_k^a T^a) in path "
                    "order. Wilson (1974).",
            parameters=(P("A_segments", "Mat", True,
                          "(n_segments, n_gen)"),
                        P("generators", "tuple[Mat, ...]", True),
                        P("coupling", "float", False)),
            returns=R("Mat", "unitary"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.sm
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.sm.higgs_potential", owner="srmech", category="qm.sm",
            summary="Mexican-hat V(φ) = -μ²|φ|² + λ|φ|⁴. Higgs (1964); "
                    "Peskin-Schroeder §20.1.",
            parameters=(P("phi", "complex", True),
                        P("mu_squared", "float", True, "> 0"),
                        P("lam", "float", True, "> 0")),
            returns=R("float", ""),
        ),
        ToolEntry(
            name="srmech.qm.sm.higgs_vev", owner="srmech", category="qm.sm",
            summary="Higgs vacuum expectation value v = √(μ²/(2λ)). "
                    "Peskin-Schroeder §20.1.",
            parameters=(P("mu_squared", "float", True),
                        P("lam", "float", True)),
            returns=R("float", "> 0"),
        ),
        ToolEntry(
            name="srmech.qm.sm.weak_mixing_angle", owner="srmech", category="qm.sm",
            summary="Weinberg mixing angle θ_W = atan(g'/g). Weinberg (1967); "
                    "Peskin-Schroeder §20.2. Returns the angle in RADIANS "
                    "(not sin²θ_W, not degrees).",
            parameters=(P("g", "float", True, "SU(2)_L coupling > 0"),
                        P("g_prime", "float", True, "U(1)_Y coupling")),
            returns=R("float", "radians"),
        ),
        ToolEntry(
            name="srmech.qm.sm.w_boson_mass", owner="srmech", category="qm.sm",
            summary="W boson mass M_W = g v / 2. Peskin-Schroeder §20.2.",
            parameters=(P("g", "float", True), P("vev", "float", True)),
            returns=R("float", "> 0"),
        ),
        ToolEntry(
            name="srmech.qm.sm.z_boson_mass", owner="srmech", category="qm.sm",
            summary="Z boson mass M_Z = v √(g² + g'²) / 2. Peskin-Schroeder §20.2.",
            parameters=(P("g", "float", True), P("g_prime", "float", True),
                        P("vev", "float", True)),
            returns=R("float", "> 0"),
        ),
        ToolEntry(
            name="srmech.qm.sm.weinberg_relation_residual", owner="srmech",
            category="qm.sm",
            summary="Verify |M_W − M_Z cos θ_W| (tree-level identity). "
                    "Peskin-Schroeder §20.2.",
            parameters=(P("g", "float", True), P("g_prime", "float", True),
                        P("vev", "float", True)),
            returns=R("float", "~0"),
        ),
        ToolEntry(
            name="srmech.qm.sm.electroweak_summary", owner="srmech", category="qm.sm",
            summary="Bundle M_W, M_Z, θ_W, sin/cos, Weinberg residual in one dict.",
            parameters=(P("g", "float", True), P("g_prime", "float", True),
                        P("vev", "float", True)),
            returns=R("dict[str, float]", ""),
        ),
        ToolEntry(
            name="srmech.qm.sm.fermion_mass_from_yukawa", owner="srmech",
            category="qm.sm",
            summary="Fermion mass m_f = y_f v / √2 from Yukawa coupling. "
                    "Peskin-Schroeder §20.2.",
            parameters=(P("yukawa", "float", True), P("vev", "float", True)),
            returns=R("float", ""),
        ),
        ToolEntry(
            name="srmech.qm.sm.ckm_matrix", owner="srmech", category="qm.sm",
            summary="CKM quark-mixing matrix (Chau-Keung parameterization). "
                    "Cabibbo (1963); Kobayashi-Maskawa (1973); PDG §12.1.",
            parameters=(P("theta_12", "float", True), P("theta_13", "float", True),
                        P("theta_23", "float", True),
                        P("delta_cp", "float", False, "default 0")),
            returns=R("Mat", "3×3 unitary"),
        ),
        ToolEntry(
            name="srmech.qm.sm.ckm_unitarity_residual", owner="srmech",
            category="qm.sm",
            summary="Frobenius norm of V V† − I. PDG §12.1.",
            parameters=(P("V", "Mat", True),),
            returns=R("float", "~0"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.octonion — the MPR-attested Cayley-Dickson-from-H
        # octonion algebra (foundational layer of the so(8)/triality
        # engine, v0.5.0rc17). Class A (table + attestation), Class M
        # (L/R binders), Class C (conjugate), Class K∘C (norm, no abs()).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.octonion.octonion_mult_table", owner="srmech",
            category="qm.octonion",
            summary="The (8,8,8) int8 structure-constant tensor C with "
                    "e_i·e_j = Σ_k C[i,j,k] e_k (fixed Cayley-Dickson-from-H "
                    "convention; MPR-attested). Class A. Baez (2002) §2.",
            parameters=(),
            returns=R("list[list[list[int]]]", "(8,8,8) int8 structure constants"),
        ),
        ToolEntry(
            name="srmech.qm.octonion.octonion_table_attestation",
            owner="srmech", category="qm.octonion",
            summary="MPR v1 self-attestation dict for the structure-constant "
                    "table; response_sha256 content-addresses the int8 table "
                    "bytes via sha256_bytes (Class A). Baez (2002), "
                    "arXiv:math/0105155.",
            parameters=(),
            returns=R("dict", "MPR v1 attestation block"),
        ),
        ToolEntry(
            name="srmech.qm.octonion.octonion_left_mult", owner="srmech",
            category="qm.octonion",
            summary="Left-multiplication matrix L_a (x → a·x) as 8×8 real; "
                    "L_{e_i} (i≥1) is antisymmetric ∈ so(8). Class M "
                    "(binding). Baez (2002) §2.3-2.4.",
            parameters=(P("a", "HV", True, "8-vector octonion"),),
            returns=R("Mat", "8×8 L_a"),
        ),
        ToolEntry(
            name="srmech.qm.octonion.octonion_right_mult", owner="srmech",
            category="qm.octonion",
            summary="Right-multiplication matrix R_a (x → x·a) as 8×8 real; "
                    "R_{e_i} (i≥1) is antisymmetric ∈ so(8). Class M "
                    "(binding). Baez (2002) §2.3-2.4.",
            parameters=(P("a", "HV", True, "8-vector octonion"),),
            returns=R("Mat", "8×8 R_a"),
        ),
        ToolEntry(
            name="srmech.qm.octonion.octonion_conjugate", owner="srmech",
            category="qm.octonion",
            summary="Octonion conjugate conj(x) = (x_0, -x_1, …, -x_7); flips "
                    "the imaginary-axis signs. Class C (orientation). "
                    "Baez (2002) §2.1.",
            parameters=(P("x", "HV", True, "8-vector"),),
            returns=R("list[float]", "8-vector"),
        ),
        ToolEntry(
            name="srmech.qm.octonion.octonion_norm", owner="srmech",
            category="qm.octonion",
            summary="Octonion norm √(Σ x_i²) via the scalar Class K pin-slot "
                    "magnitude (cascade.magnitude) then sqrt — never abs(). "
                    "Class K∘C. Baez (2002) §2.1.",
            parameters=(P("x", "HV", True, "8-vector"),),
            returns=R("float", "≥ 0; Class K+C, never abs()"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.hurwitz — the octonion-native matrix realisation of
        # "the One" S(σ,θ) (#887); the qm-tier Rosetta peer of the
        # numpy-free srmech.amsc.cascade.the_one. The Fano planes of each
        # rotation are DERIVED from octonion_mult_table (not hardcoded), so
        # the 14×14 matrix agrees bit-for-bit with One.to_matrix.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.hurwitz.hurwitz_planes", owner="srmech",
            category="qm.hurwitz",
            summary="The oriented Fano planes (a,b,sign) each Hurwitz block "
                    "(ℂ/ℍ/𝕆) turns by θ, DERIVED from octonion_mult_table — "
                    "0/1/3 planes (the octonion epicycle). Matches the "
                    "hardcoded srmech.amsc.cascade.one.FANO_PLANES bit-for-bit "
                    "(the structure cross-derivation). Class A "
                    "(content-addressing the octonion convention). Scientific "
                    "tier (§22): numpy. Baez (2002) §2." + PUBLISH_OPT_IN_NOTE,
            parameters=(),
            returns=R("tuple",
                      "((), ((1,2,1),), ((1,6,-1),(2,5,1),(3,4,1)))"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.so8 — the 28-generator so(8) adjoint, partitioned
        # 14 (g2 = Der O) + 7 (L-type) + 7 (R-type). The 14 = the A-N
        # 1+3+7+3 partition. Class M (g2 + L/R binders); Class C (so7).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.so8.so8_adjoint_basis", owner="srmech",
            category="qm.so8",
            summary="The 28 antisymmetric 8×8 so(8) generators in partitioned "
                    "order 14 (g2 = Der O) + 7 (L-type L_{e_i}) + 7 (R-type "
                    "R_{e_i}). Class M. Baez (2002) §2.4 + §4.1.",
            parameters=(),
            returns=R("tuple[Mat, ...]",
                      "28 antisymmetric 8×8, partitioned 14+7+7"),
        ),
        ToolEntry(
            name="srmech.qm.so8.g2_subalgebra", owner="srmech",
            category="qm.so8",
            summary="The 14 octonion derivations Der(O) = g2 (deterministic "
                    "rank-revealing numpy subset of the 21 D_{e_i,e_j}; rank "
                    "exactly 14). The Fix(τ) killer-test target. Class M. "
                    "Baez (2002) §4.1; Schafer (1966).",
            parameters=(),
            returns=R("tuple[Mat, ...]", "14 derivations (antisym 8×8)"),
        ),
        ToolEntry(
            name="srmech.qm.so8.so7_subalgebra", owner="srmech",
            category="qm.so8",
            summary="The 21-dim so(7) fixed space ker(S_B − I) (D4 → B3 Z2 "
                    "fold), as antisymmetric 8×8 generators (deterministic "
                    "SVD nullspace). Class C. Baez (2002) §2.4.",
            parameters=(),
            returns=R("tuple[Mat, ...]", "21 generators (antisym 8×8)"),
        ),
        ToolEntry(
            name="srmech.qm.so8.an_embedding", owner="srmech",
            category="qm.so8",
            summary="The bit-exact su(3) ⊕ 3 ⊕ 3bar Lie decomposition of the "
                    "14 g2 = Der(O) generators (the su(3) adjoint 8 + the "
                    "J-eigenspace fundamental 3 + antifundamental 3bar; the "
                    "7-dim octonion-vector branches 1+3+3bar over the same "
                    "su(3)). su(3) = stabiliser {D : D·e_K = 0}; the genuine "
                    "fundamental is the +i eigenspace of the su(3)-invariant "
                    "complex structure J (J²=−I); [su3,3]⊆3 bit-exact. "
                    "su(3) identified by the invariant certificate {dim 8, "
                    "rank 2, simple} (Cartan A2), never abs(). bit-exact "
                    "computed; A-N class names are a documented "
                    "framework-reading label (NOT a derived theorem). "
                    "Class C-L. Baez (2002) §4.1 (g2 = Der O, dim 14).",
            parameters=(P("imaginary_unit", "int", False,
                          "fixed imaginary octonion unit 1..7 (default 1)"),),
            returns=R("dict",
                      "{su3:[8 8x8], complement:[6 8x8], "
                      "complex_structure_J, triplet:[3], antitriplet:[3], "
                      "weights:(6,2), decomposition, imaginary_unit, "
                      "attestation}"),
        ),
        ToolEntry(
            name="srmech.qm.so8.quaternion_subalgebra_stabilizer",
            owner="srmech",
            category="qm.so8",
            summary="The bit-exact 6-dim so(4) = su(2) ⊕ su(2) subalgebra of "
                    "g2 = Der(O) stabilising a quaternion subalgebra H ⊂ O "
                    "(the ℍ-reading sibling of an_embedding). H = "
                    "span(e0,e_a,e_b,e_c) for a Fano line; so(4) = "
                    "{D in g2 : D·span(H_imag) ⊆ span(H_imag)} (SVD nullspace, "
                    "orthonormalised; dim 6). Certificate: Killing-form rank 6 "
                    "(semisimple, Cartan), the two-triplet Killing spectrum "
                    "(two eigenvalues ×3 = su(2) ⊕ su(2)), the two su(2) ideals "
                    "via the self-dual / anti-self-dual split on H^⊥ ≅ R^4 "
                    "([su2_+,su2_-]=0, each closes), and ℍ-choice-invariance "
                    "(spectrum bit-identical across the 7 Fano-line H). The "
                    "su(2) ⊕ su(2) split is this op's own computation, NOT a "
                    "cited theorem; never abs(). F215: this Lie SYMMETRY surface "
                    "is distinct from the 6 cascade.atoms group-element ops "
                    "(6=6 is coincidence; 0/6 atoms are Lie generators) — a "
                    "framework-reading label, NOT a derived theorem. Class C-L. "
                    "Baez (2002) §4.1 (g2 = Der O, dim 14).",
            parameters=(P("quaternion_index", "int", False,
                          "1-based Fano-line index 1..7 selecting H "
                          "(default 1 = line (1,2,3))"),),
            returns=R("dict",
                      "{so4:[6 8x8], su2_plus:[3 8x8], su2_minus:[3 8x8], "
                      "killing_form:(6,6), killing_rank:6, killing_spectrum:(6,), "
                      "decomposition, quaternion_fano_line, "
                      "quaternion_imaginary_units, attestation}"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.triality — the Spin(8) triality engine. The 28×28
        # order-3 outer automorphism τ = S_B·S_C (Fix(τ) = g2 = 14),
        # the Z2 swap, Cartan companions + residual. Class I (cyclic),
        # Class C (swap), Class M (companions), Class K∘C (residual).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.triality.triality_automorphism", owner="srmech",
            category="qm.triality",
            summary="The 28×28 order-3 outer automorphism τ = S_B·S_C "
                    "(product of the two companion involutions); τ³ = I, "
                    "τ ≠ I, Fix(τ) = g2 dim 14 (D4 →Z3 G2). Class I. "
                    "Baez (2002) §2.4; Cartan (1925).",
            parameters=(),
            returns=R("Mat", "28×28 τ, τ³ = I"),
        ),
        ToolEntry(
            name="srmech.qm.triality.triality_swap", owner="srmech",
            category="qm.triality",
            summary="The 28×28 Z2 companion involution S_B; S_B² = I, "
                    "Fix(S_B) = so(7) dim 21 (D4 →Z2 B3). With τ generates "
                    "S3 = Out(Spin(8)). Class C. Baez (2002) §2.4.",
            parameters=(),
            returns=R("Mat", "28×28 Z2 involution"),
        ),
        ToolEntry(
            name="srmech.qm.triality.triality_cycle", owner="srmech",
            category="qm.triality",
            summary="The next frame in the order-3 rep-permutation "
                    "8v → 8s → 8c → 8v (Class-I mod-3 cyclic step via "
                    "srmech.amsc.cyclic.mod_add). Raises on an unknown frame. "
                    "Baez (2002) §2.4.",
            parameters=(P("frame", "str", True, "8v/8s/8c frame label"),),
            returns=R("str", "next frame in 8v → 8s → 8c"),
        ),
        ToolEntry(
            name="srmech.qm.triality.triality_apply", owner="srmech",
            category="qm.triality",
            summary="Carry an 8-vector between irrep frames per the cycle "
                    "distance (Class I frame-transport ∘ Class M companions). "
                    "Raises on a wrong shape or unknown frame. "
                    "Baez (2002) §2.4; Cartan (1925).",
            parameters=(P("x", "HV", True, "8-vector"),
                        P("from_frame", "str", True, "source frame label"),
                        P("to_frame", "str", True, "target frame label")),
            returns=R("list[float]", "8-vector in to_frame"),
        ),
        ToolEntry(
            name="srmech.qm.triality.triality_companions", owner="srmech",
            category="qm.triality",
            summary="The (g_s, g_c) companions solving Cartan's relation "
                    "g_v(x·y) = g_s(x)·y + x·g_c(y) by deterministic "
                    "least-squares; for a g2 derivation g_s = g_c = g_v. "
                    "Class M. Baez (2002) §2.4.",
            parameters=(P("g_v", "Mat", True, "8×8 so(8) generator"),),
            returns=R("tuple[Mat, ...]", "(g_s, g_c) companions"),
        ),
        ToolEntry(
            name="srmech.qm.triality.triality_relation_residual",
            owner="srmech", category="qm.triality",
            summary="Scalar Cartan-relation deviation Σ_ij ‖g_v(e_i·e_j) − "
                    "g_s(e_i)·e_j − e_i·g_c(e_j)‖ via the scalar Class K "
                    "pin-slot magnitude (never abs()); 0 when correct. "
                    "Class K∘C. Baez (2002) §2.4.",
            parameters=(P("g_v", "Mat", True, "8×8 generator"),
                        P("g_s", "Mat", True, "8×8 8_s companion"),
                        P("g_c", "Mat", True, "8×8 8_c companion")),
            returns=R("float", "0 when the Cartan relation holds"),
        ),
        ToolEntry(
            name="srmech.qm.triality.lean_isa_seventh_primitive",
            owner="srmech", category="qm.triality",
            summary="The order-3 triality as the 7th lean-ISA primitive, "
                    "completing the chirality-complete A-N core: 6 order-2 "
                    "cascade.atoms (pin_slot_at_zero / reorient / magnitude / "
                    "chiral_flip / chiral_dual / net_chirality) + 1 order-3 "
                    "triality (triality_automorphism) = 7 — the only access to "
                    "the 3rd chiral axis (F220). BIT-EXACT certificate: τ has "
                    "order exactly 3 (‖τ³−I‖≈0, τ≠I, τ²≠I) via the engine, plus "
                    "the Lagrange arithmetic 3∤8 / 3∣3 (never abs(); scalar "
                    "Class K pin-slot magnitude). The 6 atoms commute (abelian "
                    "Z2×Z2×Z2, |G|=8) so 3∤8 ⇒ no order-3 element ⇒ the order-3 "
                    "axis is unreachable from them — a documented "
                    "framework-reading (scope hierarchy endianness ⊂ Class C ⊂ "
                    "Klein-4 ⊂ Spin(8) triality), NOT a derived theorem, "
                    "surfaced under framework_chirality_complete_reading. "
                    "Class I (cyclic order-3). Baez (2002) §2.4 "
                    "(Out(Spin(8))=S3); F220 is the framework finding.",
            parameters=(),
            returns=R("dict",
                      "{order_two_atoms:(6,), order_three_primitive, "
                      "triality:28×28 τ, certificate (bit-exact: triality_order "
                      "3, residuals, abelian_group_order 8, lagrange_obstruction, "
                      "chirality_complete_core 7), attestation, "
                      "framework_chirality_complete_reading}"),
        ),
    ]
    for e in entries:
        register_tool(e)


def _register_introspect_tools() -> None:
    """Register the opt-in introspection surface (v0.5.0rc7).

    Discoverability fix per user direction 2026-05-28: srmech's
    cascade-op / AMSC-fetch / signal-processing dispatch sites
    can all emit per-op events to a status file (consumed by
    ``srmech status`` / ``srmech bus tap``), but emission is OFF
    by default — wrapping in :func:`srmech.introspect.publish` or
    setting ``SRMECH_PUBLISH_STATUS=1`` before ``import srmech``
    turns it on. LLMs reading the tool catalog (via the rc6 MCP
    adapter) should see the opt-in path inline.
    """
    register_tool(
        ToolEntry(
            name="srmech.introspect.publish",
            owner="srmech",
            category="introspect",
            summary=(
                "Opt-in context manager that enables per-op event "
                "emission for `srmech status` / `srmech bus tap` "
                "consumers. Wrap your sweep in `with "
                "srmech.introspect.publish():` OR set "
                "`SRMECH_PUBLISH_STATUS=1` env-var before importing "
                "srmech to enable per-op events. Without this opt-in, "
                "all srmech operations are silent (no overhead). "
                "Designed for research sessions where you want to "
                "observe a long-running sweep from a second process "
                "via `srmech status` or via `srmech bus tap`. Events "
                "land in `~/.srmech/run-{pid}-{start_time_ns}.ndjson` "
                "(NDJSON, one MPR-shaped event per line). v0.4.6+ "
                "(out-of-band introspection); v0.5.0rc7 (catalog "
                "discoverability)."
            ),
            parameters=(
                ToolParameter(
                    "remove_on_exit", "bool", required=False,
                    summary=(
                        "If True, the status file is unlinked when "
                        "the with-block exits. Default False — leave "
                        "the file for `srmech status` to auto-clean "
                        "on next read."
                    ),
                ),
            ),
            returns=ToolReturn(
                type="contextmanager[_PublishHandle]",
                shape=(
                    "Yields a handle exposing pid, start_time_ns, "
                    "file_path of the active writer."
                ),
            ),
        )
    )
    # v0.5.0rc9: register the read-side "status" surface so MCP /
    # Claude Code consumers can discover the live-run enumerator and
    # the by-pid lookup. Without these, the introspection surface was
    # write-only from the LLM's catalog perspective — publish was
    # visible but the matching read API was invisible.
    register_tool(
        ToolEntry(
            name="srmech.introspect.list",
            owner="srmech",
            category="introspect",
            summary=(
                "Enumerate active (and recently-died) srmech runs "
                "owned by the current user by scanning "
                "`~/.srmech/run-{pid}-{start_time_ns}.ndjson`. The "
                "read-side complement to `srmech.introspect.publish`: "
                "use this from a second process to observe a "
                "long-running sweep. Side effect: dead-PID files "
                "whose `session_end` event committed cleanly are "
                "removed on read (auto-cleanup); their Run records "
                "are still returned in the result so the caller can "
                "inspect the final state. Most-recent first (sorted "
                "descending by `start_time_ns`). Returns `[]` on "
                "Pyodide / WASM (no filesystem). v0.5.0rc9 "
                "(MCP / catalog discoverability)."
            ),
            parameters=(),
            returns=ToolReturn(
                type="list[Run]",
                shape=(
                    "Each Run is a frozen dataclass: pid (int), "
                    "start_time_ns (int), script_name (str), "
                    "current_op (str), current_class (str), "
                    "elapsed_ms (int), status ('running' | "
                    "'finished' | 'died'), event_count (int), "
                    "file_path (pathlib.Path). Sorted most-recent "
                    "first."
                ),
            ),
        )
    )
    register_tool(
        ToolEntry(
            name="srmech.introspect.by_pid",
            owner="srmech",
            category="introspect",
            summary=(
                "Look up the most-recent srmech run for one PID. "
                "PID-recycling defence: if two status files share "
                "the same PID because the OS reused it, the one "
                "with the larger `start_time_ns` wins (the more-"
                "recent run; the `start_time_ns` suffix in the "
                "filename defeats PID recycling). Returns `None` if "
                "no file matches, or on Pyodide / WASM (no "
                "filesystem). v0.5.0rc9 (MCP / catalog "
                "discoverability)."
            ),
            parameters=(
                ToolParameter(
                    "pid", "int", required=True,
                    summary="Process ID to look up.",
                ),
            ),
            returns=ToolReturn(
                type="Run | None",
                shape=(
                    "Frozen dataclass with pid (int), start_time_ns "
                    "(int), script_name (str), current_op (str), "
                    "current_class (str), elapsed_ms (int), status "
                    "('running' | 'finished' | 'died'), event_count "
                    "(int), file_path (pathlib.Path). `None` when "
                    "no file matches the PID."
                ),
            ),
        )
    )
    # v0.5.0rc11: the self-recognition ROOT. Register
    # ``srmech.introspect.describe`` so MCP / Anthropic consumers can
    # ask "what is srmech / what can it do?" and get the package's own
    # at-a-glance shape (version + native status + tool total +
    # by-category + sorted category names) in one call. No parameters.
    register_tool(
        ToolEntry(
            name="srmech.introspect.describe",
            owner="srmech",
            category="introspect",
            summary=(
                "The self-recognition ROOT (v0.5.0rc11): a structured, "
                "at-a-glance map of srmech's own shape. Start here to "
                "discover 'what is srmech / what can it do?' without "
                "reading the implementation. Calls `warmup_all()` first "
                "so the counts are complete no matter how srmech was "
                "entered (library / CLI / MCP / Anthropic adapter), "
                "then returns the package version, the tool-schema "
                "version, the native-dispatch status (has_native / "
                "abi_version / native_version), the total registered "
                "tool count split into mcp_callable (advertised over "
                "JSON-RPC / Anthropic) vs handle_pending (registered for "
                "introspection but not advertised — the SpectralHandle "
                "by-reference tools, rc16) + a per-category breakdown, "
                "and the sorted list of category names. This is a ROOT / "
                "INDEX — it "
                "surfaces the SHAPE; per-tool JSON schemas, env, and "
                "error-type detail come from later voxels. Framework "
                "reading: Class H (self-introspection) at package scale "
                "— the package recognising the shape of its own A–N "
                "tool surface. No parameters."
            ),
            parameters=(),
            returns=ToolReturn(
                type="dict",
                shape=(
                    "{'srmech_version': str, 'tool_schema_version': "
                    "str, 'native': {'has_native': bool, 'abi_version': "
                    "int | None, 'native_version': str | None}, "
                    "'tools': {'total': int, 'mcp_callable': int, "
                    "'handle_pending': int, 'by_category': {category: "
                    "count, ...}}, 'handle_pending': [sorted "
                    "handle-pending tool names], 'categories': [sorted "
                    "category names]}"
                ),
            ),
        )
    )


def _register_dsl_tools() -> None:
    """Register the declarative cascade-DSL surface (v0.5.0rc12 — DSL voxel).

    The rc8 cascade DSL (``srmech.dsl.*``) composes the 14 cascade-catalog
    ops via a fluent builder (``chain().then(...).loop(...)...``). That
    method-chaining shape is NOT LLM-tool-ergonomic — a single tool call
    can't chain builder methods. So this voxel exposes the *declarative*
    surface: tools that do real work in ONE call.

    Two entries, both with plain keyword parameters (no ``*args`` /
    ``**kwargs`` — the rc10 property-key grammar holds and
    ``invoke_tool``'s ``fn(**coerced)`` calls them directly):

    * ``srmech.dsl.run_toml_chain(spec, input_value)`` — author an inline
      TOML chain spec + run it atomically; an LLM composes AND runs a
      cascade in one call.
    * ``srmech.dsl.list_catalog_ops()`` — enumerate the 14 cascade-catalog
      ops + their A–N class + purpose, so an LLM knows which op names a
      spec may use.

    Framework reading: the DSL composes Class M (cross-class bind) over
    the cascade catalog; ``list_catalog_ops`` is Class E (catalog
    enumeration) ∘ Class F (render of each descriptor's class + purpose).
    No new primitive class is introduced.

    NOTE on the import-cycle: this function builds *declarative*
    ``ToolEntry`` data only — it does NOT import ``srmech.dsl`` (whose
    ``_chain`` pulls ``srmech.introspect._writer`` and whose ``_catalog``
    lazily pulls ``srmech.amsc.cascade``). The dotted-name targets are
    resolved by :mod:`srmech.mcp._tools` at *invoke* time, not here, so
    registering at this module's import is cycle-free. ``warmup_all()``
    additionally imports ``srmech.dsl`` for manifest completeness; that
    import is also cycle-free (verified — neither ``srmech.dsl`` nor
    ``srmech.introspect`` imports ``srmech.amsc.tool_schema`` at module
    load).
    """
    rc12 = " (v0.5.0rc12 — DSL surface voxel)."
    register_tool(
        ToolEntry(
            name="srmech.dsl.run_toml_chain",
            owner="srmech",
            category="dsl",
            summary=(
                "Compose AND run a cascade in ONE call: author an inline "
                "TOML chain spec, feed an input value, get the chain "
                "result. The declarative, one-shot face of the rc8 "
                "cascade DSL (the fluent `chain().then(...).loop(...)` "
                "builder is not tool-callable — a tool call can't chain "
                "methods). The `spec` is a TOML document with a `[chain]` "
                "table + `[[stage]]` array entries; each stage carries "
                "exactly one discriminator: `op` (then), `loop_n` + "
                "`sub_chain` (loop), `fold_init` + `fold_op` (fold), or "
                "`reduce_op` (reduce); any other key forwards as a "
                "cascade-op kwarg (e.g. `max_denominator`). Op names come "
                "from `srmech.dsl.list_catalog_ops` (the 15-op cascade "
                "catalog). Example spec: `[chain]\\nname='demo'\\n\\n"
                "[[stage]]\\nop='chiral_flip'`. Framework reading: the "
                "DSL composes Class M (cross-class bind) over the cascade "
                "catalog; each stage is one A–N primitive-class instance, "
                "the chain is the composition." + rc12
            ),
            parameters=(
                ToolParameter(
                    "spec", "str", required=True,
                    summary=(
                        "TOML chain spec: a [chain] table + [[stage]] "
                        "array (one builder call per stage)."
                    ),
                ),
                ToolParameter(
                    "input_value", "int | float | str | list | dict",
                    required=True,
                    summary=(
                        "Seed value fed to the first stage (a JSON-shaped "
                        "value: number / string / list / dict). Passed to "
                        "Chain.run unchanged."
                    ),
                ),
            ),
            returns=ToolReturn(
                type="Any",
                shape=(
                    "Output of the final stage (an empty chain returns "
                    "the input unchanged)."
                ),
            ),
        )
    )
    register_tool(
        ToolEntry(
            name="srmech.dsl.list_catalog_ops",
            owner="srmech",
            category="dsl",
            summary=(
                "Enumerate the cascade-catalog ops a chain spec may use. "
                "The discovery companion to `srmech.dsl.run_toml_chain`: "
                "returns one record per op so an LLM can pick valid `op` "
                "/ `fold_op` / `reduce_op` names and read each op's A–N "
                "class composition + 1-line purpose BEFORE authoring a "
                "spec. Sourced from the on-disk cascade-catalog TOML "
                "descriptors (the SSoT), so it stays in lockstep with the "
                "ops the runner can actually resolve (15 ops: "
                "autocorrelation, best_rational_signed, chiral_dual, "
                "chiral_flip, cyclic_gcd, encode_loe_content, kuramoto_step, "
                "magnitude, net_chirality, octonion_dft, "
                "parallel_sector_dispatch, pin_slot_at_zero, quaternion_dft, "
                "reorient, schur_complement). Each record "
                "also carries a `kind` "
                "(`stage` | `combinator`) and `provenance` (`srmech` | "
                "`user`). Framework reading: Class E (catalog enumeration) "
                "∘ Class F (descriptor render). No parameters." + rc12
            ),
            parameters=(),
            returns=ToolReturn(
                type="list[dict]",
                shape=(
                    "[{'name': str, 'class': <A–N class composition>, "
                    "'purpose': str}, ...] sorted ascending by name."
                ),
            ),
        )
    )
    register_tool(
        ToolEntry(
            name="srmech.dsl.list_ops",
            owner="srmech",
            category="dsl",
            summary=(
                "Unify the two op-discovery registries into ONE list (§17 U3): "
                "BOTH the value-transform cascade ops (`list_catalog_ops`) AND "
                "the AMSC catalog-declared operator chains "
                "(`catalog.list_catalog_chains`), each record tagged a uniform "
                "`kind` (`stage` | `combinator` | `catalog-chain`) and "
                "`provenance` (`srmech` | `user` | `catalog:<source_key>`). "
                "Before this the DSL op list and the catalog-chain registry "
                "were disjoint — a kernel chain declared on a text-catalog was "
                "invisible to the DSL. `source_keys` restricts the "
                "catalog-chain half; omit to auto-discover every registered "
                "attested source. Framework reading: Class E (catalog "
                "enumeration) over both registries at once. "
                "(v0.7.5rc45 — §17 U3 unified op-discovery.)"
            ),
            parameters=(
                ToolParameter(
                    "source_keys", "list", required=False,
                    summary="restrict the catalog-chain half to these source "
                            "keys; omit to auto-discover all registered sources.",
                ),
            ),
            returns=ToolReturn(
                type="list[dict]",
                shape=(
                    "[{'name': str, 'class': str, 'purpose': str, 'kind': "
                    "'stage'|'combinator'|'catalog-chain', 'provenance': str}, "
                    "...] sorted by (kind, name)."
                ),
            ),
        )
    )
    rc41 = " (v0.7.5rc41 — class-from-TOML surface; #962 Part 2)."
    register_tool(
        ToolEntry(
            name="srmech.dsl.list_class_surface",
            owner="srmech",
            category="dsl",
            summary=(
                "Enumerate the user-declared srmech CLASSES (the class-from-TOML "
                "surface) — the discovery companion for class construction. A "
                "researcher authors a [class] TOML (fields + methods-as-cascade-"
                "op-refs) and srmech.dsl.make_class builds a generic class-aware "
                "object; this lists each declared class as a JSON-able record "
                "(name, kind, doc, fields, methods with their bound cascade op + "
                "binds, provenance) so an LLM picks a class + method BEFORE "
                "constructing it. The shipped seed is `Genome` (genome / "
                "chromosome / telomere storage); bring-your-own classes from a "
                "register_class_dir / SRMECH_CLASS_PATH dir surface here too. "
                "Framework reading: Class E (catalog enumeration) ∘ Class F "
                "(descriptor render). No parameters." + rc41
            ),
            parameters=(),
            returns=ToolReturn(
                type="list[dict]",
                shape=(
                    "[{'name', 'kind', 'doc', 'fields': {field: type}, "
                    "'methods': {method: {'op', 'binds', ...}}, 'provenance'}, "
                    "...] one record per declared class."
                ),
            ),
        )
    )
    register_tool(
        ToolEntry(
            name="srmech.dsl.describe_class",
            owner="srmech",
            category="dsl",
            summary=(
                "Describe ONE user-declared srmech class by name — the focused "
                "companion to `srmech.dsl.list_class_surface`. Returns the "
                "JSON-able descriptor (name, kind, doc, fields, methods with each "
                "method's bound cascade op + binds + appends/sets, provenance) "
                "for the shipped seed `Genome` or any bring-your-own class. The "
                "shape srmech.dsl.make_class(name) constructs and "
                "srmech.dsl.run_class_method runs. Framework reading: Class F "
                "(descriptor render) over the [class] catalog." + rc41
            ),
            parameters=(
                ToolParameter(
                    "name", "str", required=True,
                    summary="the class name to describe (e.g. 'Genome').",
                ),
            ),
            returns=ToolReturn(
                type="dict",
                shape=(
                    "{'name', 'kind', 'doc', 'fields', 'methods', "
                    "'provenance'} — the full class descriptor."
                ),
            ),
        )
    )
    register_tool(
        ToolEntry(
            name="srmech.dsl.generate_class_descriptor",
            owner="srmech",
            category="dsl",
            summary=(
                "Render a [class] TOML descriptor string — the INVERSE of "
                "srmech.dsl.make_class (§39). Two modes: (explicit) pass `fields` "
                "({field: type}) + `methods` ({method: {op: dotted-cascade-op, "
                "binds: [...], doc, appends|sets}} — the describe_class method "
                "shape) and it renders straight from the components; "
                "(introspection) pass ONLY `name` of a registered class (e.g. "
                "'Genome') and it recovers the descriptor via describe_class and "
                "re-emits it — a constructed class rendering its OWN [class] TOML "
                "back out. The emitted string is round-trippable: drop it in a "
                "register_class_dir dir and make_class constructs the identical "
                "class (docs re-emit single-line with escaped newlines, so a "
                "multi-line seed doc decodes back bit-identically). Closes the "
                "make_class loop the other direction. Framework reading: Class E "
                "(catalog enumeration) ∘ Class F (descriptor render) ∘ Class H "
                "(self-introspection) — no new primitive class. "
                "(v0.7.5rc49 — §39 make_class inverse; #962 Part 2.)"
            ),
            parameters=(
                ToolParameter(
                    "name", "str", required=True,
                    summary="the class name (introspected if fields/methods "
                            "omitted; else the emitted [class].name).",
                ),
                ToolParameter(
                    "fields", "dict", required=False,
                    summary="{field: type} declarations; omit (with methods) to "
                            "introspect a registered class instead.",
                ),
                ToolParameter(
                    "methods", "dict", required=False,
                    summary="{method: {op, binds, doc, appends|sets}} — methods "
                            "as dotted cascade-op refs.",
                ),
                ToolParameter(
                    "doc", "str", required=False,
                    summary="class docstring (overrides the introspected doc).",
                ),
                ToolParameter(
                    "kind", "str", required=False,
                    summary="class kind tag (overrides the introspected kind).",
                ),
            ),
            returns=ToolReturn(
                type="str",
                shape=(
                    "A [class] TOML descriptor string (name/kind/doc + "
                    "[class.field] + [class.method.*]) round-trippable through "
                    "srmech.dsl.make_class."
                ),
            ),
        )
    )


# ──────────────────────────────────────────────────────────────────────
# Single registration entry-point (v0.5.0rc11 — Self-recognition root)
# ──────────────────────────────────────────────────────────────────────


def warmup_all() -> None:
    """Import every srmech submodule that registers ToolEntries, so the
    registry is fully populated no matter how srmech was entered (library,
    CLI, MCP, Anthropic adapter). Idempotent. THE single place future
    voxels add their registration import — replaces scattered side-effect
    imports. Closes the orphan-registration bug class (v0.5.0rc9 bus miss).

    ``srmech.amsc`` (this module's package) and ``srmech.qm`` register
    their tools at *this* module's import time via the
    ``_register_*_tools()`` calls below, so they are always present once
    ``srmech.amsc.tool_schema`` is imported. The submodules listed here
    are the ones whose registration is NOT transitively guaranteed by
    importing ``srmech.amsc.tool_schema``:

    * ``srmech.bus`` fires ``srmech.bus._tool_schema._register_bus_tools``
      (the rc9 orphan — bus tools were silently missing from the
      LLM-facing catalog because no entry-path imported the bus).
    * ``srmech.introspect`` is belt-and-braces — its tool entries are
      registered by ``_register_introspect_tools()`` at this module's
      import, but importing the module keeps the warmup list a complete,
      self-documenting manifest of the registration-bearing submodules.
    * ``srmech.dsl`` is belt-and-braces (v0.5.0rc12) — its tool entries
      are registered by ``_register_dsl_tools()`` at this module's
      import (declarative data only — no ``srmech.dsl`` import there, so
      no cycle), but importing the module keeps the manifest complete
      and confirms the package is importable. The import is cycle-free:
      neither ``srmech.dsl`` nor ``srmech.introspect`` imports
      ``srmech.amsc.tool_schema`` at module load (``srmech.dsl._catalog``
      only references it in a docstring; ``srmech.introspect`` imports it
      lazily inside ``describe()``).
    """
    import importlib

    for mod in ("srmech.bus", "srmech.introspect", "srmech.dsl"):
        try:
            importlib.import_module(mod)
        except Exception:  # pragma: no cover - defensive; optional submodules
            pass


# Call at module import so srmech's own tools are always present
# in the registry. Profile tools join via register_profile_tools
# at profile-activation time.
_register_amsc_tools()
_register_primitive_class_tools()
_register_spectral_runtime_tools()
_register_qm_tools()
_register_introspect_tools()
_register_dsl_tools()


__all__ = [
    "TOOL_SCHEMA_VERSION",
    "ToolEntry",
    "ToolParameter",
    "ToolReturn",
    "ToolSchema",
    "ToolSchemaConflictError",
    "ToolSchemaError",
    "ToolSchemaValidationError",
    "get_tool_schema",
    "load_extension_file",
    "register_profile_tools",
    "register_tool",
    "tool_schema_view",
    "unregister_profile_tools",
    "warmup_all",
]
