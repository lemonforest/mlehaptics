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

    def to_jsonable(self) -> Dict[str, Any]:
        """Render as a JSON-serialisable dict. Used by
        :func:`tool_schema_view`."""
        out: Dict[str, Any] = {
            "name": self.name,
            "owner": self.owner,
            "category": self.category,
            "summary": self.summary,
            "parameters": [asdict(p) for p in self.parameters],
        }
        if self.returns is not None:
            out["returns"] = asdict(self.returns)
        if self.smoke_test_hint is not None:
            out["smoke_test_hint"] = dict(self.smoke_test_hint)
        if self.example is not None:
            out["example"] = dict(self.example)
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
            name="srmech.amsc.format.read_ndjson",
            owner="srmech",
            category="format",
            summary="Stream MPRRecords line-by-line from an NDJSON file. "
                    "Native C dispatch for IO + line tokenisation when "
                    "available; stdlib fallback otherwise. JSON parsing "
                    "stays in Python.",
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
                    "runtime kernel + live query.",
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
    ]
    for e in entries:
        register_tool(e)


# Call at module import so srmech's own tools are always present
# in the registry. Profile tools join via register_profile_tools
# at profile-activation time.
_register_amsc_tools()


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
]
