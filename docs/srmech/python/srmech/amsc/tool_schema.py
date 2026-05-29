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
            returns=R("np.ndarray", "n × n dense matrix"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.dense_laplacian", owner="srmech",
            category="laplacian",
            summary="Graph Laplacian L = D - A. Native C dispatch when "
                    "n ≤ 256; numpy fallback otherwise.",
            parameters=(P("n", "int", True), P("edges", "list", True),
                        P("weights", "Optional[list[float]]", False)),
            returns=R("np.ndarray", "n × n symmetric matrix"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.normalized_laplacian", owner="srmech",
            category="laplacian",
            summary="Symmetric normalized Laplacian L_sym = I - D^{-1/2} A D^{-1/2}. "
                    "Isolated vertices have diagonal entry 0.",
            parameters=(P("n", "int", True), P("edges", "list", True),
                        P("weights", "Optional[list[float]]", False)),
            returns=R("np.ndarray", "n × n symmetric matrix"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.jacobi_eigvals", owner="srmech",
            category="laplacian",
            summary="Symmetric Jacobi eigendecomposition; pi-free closed-form "
                    "c/s computation. Native C dispatch when n ≤ 256.",
            parameters=(P("matrix", "np.ndarray", True, "n × n symmetric"),
                        P("max_sweeps", "int", False, "default 100"),
                        P("tolerance", "float", False)),
            returns=R("np.ndarray", "n eigenvalues (unsorted)"),
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
                    "n ≤ 256; numpy.linalg.eigh fallback. Sakurai §2.1.5; "
                    "Golub & Van Loan §8.5.",
            parameters=(P("H", "np.ndarray", True,
                          "n × n complex Hermitian matrix"),),
            returns=R("tuple[np.ndarray, np.ndarray]",
                      "(eigvals_ascending, V_unitary)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.symmetric_eigendecompose",
            owner="srmech", category="laplacian",
            summary="Real-symmetric eigendecomposition L = V diag(eigvals) "
                    "Vᵀ via numpy.linalg.eigh. Real-input specialisation of "
                    "hermitian_eigendecompose: guarantees real float64 "
                    "eigvals AND eigvecs (no ComplexWarning for a real "
                    "Laplacian). Golub & Van Loan §8.3.",
            parameters=(P("L", "np.ndarray", True,
                          "n × n real symmetric matrix"),),
            returns=R("tuple[np.ndarray, np.ndarray]",
                      "(eigvals_ascending, V_orthogonal); both float64"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.dense_matvec_complex",
            owner="srmech", category="laplacian",
            summary="Dense complex matrix-vector multiplication M @ v. "
                    "Golub & Van Loan §1.1.",
            parameters=(P("M", "np.ndarray", True, "rows × cols complex"),
                        P("v", "np.ndarray", True, "length-cols complex")),
            returns=R("np.ndarray", "length-rows complex128"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.elementwise_multiply_complex",
            owner="srmech", category="laplacian",
            summary="Elementwise complex multiplication a * b with "
                    "broadcasting.",
            parameters=(P("a", "np.ndarray", True),
                        P("b", "np.ndarray", True)),
            returns=R("np.ndarray", "complex128, broadcasted shape"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.elementwise_transcendental",
            owner="srmech", category="laplacian",
            summary="Array-vectorised transcendental: exp / cos / sin / "
                    "log over real input, or exp_i(x) = exp(1j*x) "
                    "(TDSE-relevant complex exponential). ANSI C99 §7.12.",
            parameters=(P("arr", "np.ndarray", True),
                        P("op_name", "str", True,
                          "exp / cos / sin / log / exp_i")),
            returns=R("np.ndarray",
                      "float64 (real ops) or complex128 (exp_i)"),
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
            parameters=(P("key", "bytes", True),
                        P("entries", "list[tuple[bytes, bytes]]", True)),
            returns=R("Optional[bytes]", "value or None"),
        ),

        # ────────────────────────────────────────────────────────────
        # Class F — substitution / templating
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.template.render", owner="srmech", category="template",
            summary="Render a template with {key} placeholders. Plain bytes "
                    "pass through; unknown key raises ValueError.",
            parameters=(P("template_bytes", "bytes", True),
                        P("substitutions", "Mapping[bytes, bytes]", True)),
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
                    "{-1, 0, +1} (the 3-state Class-M variant alphabet).",
            parameters=(P("D", "int", True, "dimension"),
                        P("rng", "numpy.random.Generator", False)),
            returns=R("np.ndarray", "int8 in {-1,0,+1}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_bind", owner="srmech", category="hdc",
            summary="Polar bind: element-wise sign-product with 0 absorbing "
                    "(0·x = 0). Commutative, associative; self-inverse on ±1.",
            parameters=(P("a", "np.ndarray", True, "int8 {-1,0,+1}"),
                        P("b", "np.ndarray", True, "same length")),
            returns=R("np.ndarray", "int8 {-1,0,+1}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_unbind", owner="srmech", category="hdc",
            summary="Polar unbind (= sign-product). Recovers b from "
                    "bind(a,b) where a≠0; 0 is destructive.",
            parameters=(P("c", "np.ndarray", True, "int8 {-1,0,+1}"),
                        P("a", "np.ndarray", True)),
            returns=R("np.ndarray", "int8 {-1,0,+1}"),
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
            parameters=(P("vectors", "Sequence[np.ndarray]", True,
                          "one or more int8 {-1,0,+1} vectors of equal "
                          "length"),),
            returns=R("np.ndarray", "int8 {-1,0,+1}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_similarity", owner="srmech", category="hdc",
            summary="Polar match-fraction in [0,1]. skip_zero=True (default) "
                    "counts only jointly non-zero positions; False counts all "
                    "(0==0 a match).",
            parameters=(P("a", "np.ndarray", True), P("b", "np.ndarray", True),
                        P("skip_zero", "bool", False, "default True")),
            returns=R("float", "in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_density", owner="srmech", category="hdc",
            summary="Fraction of non-zero (informative) positions in [0,1]; "
                    "1.0 = fully bipolar, lower = more dead-band.",
            parameters=(P("v", "np.ndarray", True, "int8 {-1,0,+1}"),),
            returns=R("float", "in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_from_real", owner="srmech", category="hdc",
            summary="Bridge real data to a polar HDC vector via sign_quantise "
                    "(Class-K threshold projection); dead_band>0 maps the "
                    "near-threshold zone to 0.",
            parameters=(P("arr", "np.ndarray", True),
                        P("threshold", "float", False, "default 0.0"),
                        P("dead_band", "float", False, "default 0.0")),
            returns=R("np.ndarray", "int8 {-1,0,+1}"),
        ),
        # ────────────────────────────────────────────────────────────
        # Class M — Klein-4 {0,1,2,3} variant (v0.4.3rc2). Rank-2 abelian
        # over (F₂)²; the four states are the four (γ₅, iω₇) chirality
        # sectors. uint8 hypervectors.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.hdc.klein4_random", owner="srmech", category="hdc",
            summary="Random Klein-4 hypervector: uint8 array of D elements in "
                    "{0,1,2,3} (the rank-2 Class-M variant alphabet).",
            parameters=(P("D", "int", True), P("rng", "numpy.random.Generator", False)),
            returns=R("np.ndarray", "uint8 in {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_bind", owner="srmech", category="hdc",
            summary="Klein-4 bind: component-wise (F₂)²-XOR. Commutative, "
                    "associative, self-inverse; identity 0.",
            parameters=(P("a", "np.ndarray", True, "uint8 {0,1,2,3}"),
                        P("b", "np.ndarray", True, "same length")),
            returns=R("np.ndarray", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_unbind", owner="srmech", category="hdc",
            summary="Klein-4 unbind (= self-inverse XOR): recovers b from "
                    "bind(a,b).",
            parameters=(P("c", "np.ndarray", True), P("a", "np.ndarray", True)),
            returns=R("np.ndarray", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_bundle", owner="srmech", category="hdc",
            summary="Klein-4 bundle: per-bit majority on each of the 2 bits "
                    "independently; exact ties → 0 for that bit.",
            # Variadic ``klein4_bundle(*vectors)``: exposed under the clean
            # name ``vectors`` (the ``*`` sigil is illegal in an Anthropic
            # property key). See polar_bundle note above.
            parameters=(P("vectors", "Sequence[np.ndarray]", True,
                          "one or more uint8 {0,1,2,3} vectors of equal "
                          "length"),),
            returns=R("np.ndarray", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_similarity", owner="srmech", category="hdc",
            summary="Klein-4 similarity: fraction of positions where a==b in "
                    "[0,1] (1 identical, 0 orthogonal).",
            parameters=(P("a", "np.ndarray", True), P("b", "np.ndarray", True)),
            returns=R("float", "in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_chirality_flip_gamma5", owner="srmech",
            category="hdc",
            summary="Flip the γ₅ chirality axis (XOR with sector mask 2).",
            parameters=(P("v", "np.ndarray", True, "uint8 {0,1,2,3}"),),
            returns=R("np.ndarray", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_chirality_flip_omega7", owner="srmech",
            category="hdc",
            summary="Flip the iω₇ chirality axis (XOR with sector mask 1).",
            parameters=(P("v", "np.ndarray", True, "uint8 {0,1,2,3}"),),
            returns=R("np.ndarray", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_cpt_mirror", owner="srmech", category="hdc",
            summary="CPT mirror: flip BOTH chirality axes (XOR with 3).",
            parameters=(P("v", "np.ndarray", True, "uint8 {0,1,2,3}"),),
            returns=R("np.ndarray", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_sector_count", owner="srmech", category="hdc",
            summary="Per-sector occupancy [n0,n1,n2,n3] — chirality-sector "
                    "distribution attestation.",
            parameters=(P("v", "np.ndarray", True, "uint8 {0,1,2,3}"),),
            returns=R("np.ndarray", "int64 length-4 counts"),
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
            parameters=(P("sources", "Sequence[np.ndarray]", True,
                          "non-empty, equal-length 1-D arrays of bits {0,1}"),),
            returns=R("np.ndarray", "int64 squared signed-sum per position"),
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
                    "orientation < 0). Pairs with pin_slot_at_zero."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("orientation", "int", True, "in {-1,0,+1}"),
                        P("value", "number", True, "magnitude to re-sign")),
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
            parameters=(P("op", "callable", True, "unary sequence→sequence operator"),
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
            parameters=(P("state", "np.ndarray", True, "(n,) state vector"),
                        P("laplacian", "np.ndarray", True, "(n, n) Hermitian"),
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
                    "via inverse projection ``V @ coeffs``. Class chain: "
                    "Class L (inverse eigendecomposition; Chung 1997) ∘ "
                    "Class M (SHA-256 content integrity check on handle)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("handle", "SpectralHandle", True),
                        P("laplacian", "np.ndarray", True),
                        P("encoder_tag", "str", False, "default 'default'")),
            returns=R("np.ndarray", "(n_modes,) complex128"),
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
                        P("laplacian", "np.ndarray", True),
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
            parameters=(P("H", "np.ndarray", True, "Hermitian (n, n)"),
                        P("psi", "np.ndarray", True, "(n,)"),
                        P("t", "float", True)),
            returns=R("np.ndarray", "(n,) complex"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.tise_solve", owner="srmech",
            category="qm.single_particle",
            summary="Time-Independent Schrödinger H ψ_n = E_n ψ_n. "
                    "Schrödinger (1926); Sakurai §2.1.3.",
            parameters=(P("H", "np.ndarray", True, "Hermitian (n, n)"),),
            returns=R("tuple[np.ndarray, np.ndarray]",
                      "(eigenvalues, eigenvectors)"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.commutator", owner="srmech",
            category="qm.single_particle",
            summary="Operator commutator [A, B] = AB − BA. Sakurai §1.4.",
            parameters=(P("A", "np.ndarray", True), P("B", "np.ndarray", True)),
            returns=R("np.ndarray", "(n, n)"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.heisenberg_evolve", owner="srmech",
            category="qm.single_particle",
            summary="Heisenberg-picture operator evolution A_H(t) = U†(t) A U(t). "
                    "Heisenberg (1925); Sakurai §2.2.",
            parameters=(P("A", "np.ndarray", True), P("H", "np.ndarray", True),
                        P("t", "float", True)),
            returns=R("np.ndarray", "(n, n) complex"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.lattice_momentum", owner="srmech",
            category="qm.single_particle",
            summary="Lattice momentum p̂ = -i ∂_x via central-difference; "
                    "Hermitian. Sakurai §1.6; Wilson (1974).",
            parameters=(P("n", "int", True, "n_sites ≥ 2"),
                        P("dx", "float", False, "default 1.0")),
            returns=R("np.ndarray", "(n, n) Hermitian complex"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.density_matrix", owner="srmech",
            category="qm.single_particle",
            summary="Pure-state density matrix ρ = |ψ⟩⟨ψ|. "
                    "von Neumann (1932); Sakurai §3.4.",
            parameters=(P("psi", "np.ndarray", True, "(n,)"),),
            returns=R("np.ndarray", "(n, n) Hermitian PSD"),
        ),
        ToolEntry(
            name="srmech.qm.single_particle.liouville_evolve", owner="srmech",
            category="qm.single_particle",
            summary="Liouville-von Neumann ρ(t) = U(t) ρ(0) U†(t). "
                    "von Neumann (1932); Sakurai §3.4.2.",
            parameters=(P("rho", "np.ndarray", True), P("H", "np.ndarray", True),
                        P("t", "float", True)),
            returns=R("np.ndarray", "(n, n)"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.spin
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.spin.pauli_matrices", owner="srmech", category="qm.spin",
            summary="Pauli matrices σ_x, σ_y, σ_z. Cl(0,3) Clifford generators. "
                    "Pauli (1927); Sakurai §3.2.",
            parameters=(),
            returns=R("tuple[np.ndarray, np.ndarray, np.ndarray]",
                      "each 2×2 Hermitian"),
        ),
        ToolEntry(
            name="srmech.qm.spin.pauli_identity", owner="srmech", category="qm.spin",
            summary="2×2 identity (Cl(0,3) scalar).",
            parameters=(),
            returns=R("np.ndarray", "2×2 identity"),
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
            parameters=(P("direction", "np.ndarray", True, "3-vector"),),
            returns=R("np.ndarray", "2×2 Hermitian, eigenvalues ±½"),
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
            returns=R("np.ndarray", "(4, 4) Hermitian complex"),
        ),
        ToolEntry(
            name="srmech.qm.bell.chsh_operator", owner="srmech",
            category="qm.bell",
            summary="Tsirelson-optimal CHSH operator B_CHSH = A_0⊗B_0 + "
                    "A_0⊗B_1 + A_1⊗B_0 − A_1⊗B_1 with A_0=σ_z, A_1=σ_x, "
                    "B_{0,1}=(σ_z±σ_x)/√2. Cirel'son (1980).",
            parameters=(),
            returns=R("np.ndarray", "(4, 4) Hermitian complex"),
        ),
        ToolEntry(
            name="srmech.qm.bell.operator_norm", owner="srmech",
            category="qm.bell",
            summary="Spectral norm max|λ_i| of a Hermitian matrix via Class L "
                    "hermitian_eigendecompose. Golub & Van Loan §8.5.",
            parameters=(P("H", "np.ndarray", True, "Hermitian square"),),
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
            returns=R("tuple[np.ndarray, np.ndarray, np.ndarray]",
                      "(r, energies, eigenvectors)"),
        ),
        ToolEntry(
            name="srmech.qm.potentials.harmonic_oscillator_ladder", owner="srmech",
            category="qm.potentials",
            summary="Ladder operators (a, a†) truncated at n_dim. "
                    "Heisenberg (1925); Sakurai §2.3.",
            parameters=(P("n_dim", "int", False, "default 30"),
                        P("omega", "float", False, "default 1.0")),
            returns=R("tuple[np.ndarray, np.ndarray]", "(a, a†)"),
        ),
        ToolEntry(
            name="srmech.qm.potentials.harmonic_oscillator_hamiltonian",
            owner="srmech", category="qm.potentials",
            summary="Harmonic-oscillator Hamiltonian H = ℏω (a†a + 1/2). "
                    "Sakurai §2.3.",
            parameters=(P("n_dim", "int", False), P("omega", "float", False)),
            returns=R("np.ndarray", "Hermitian (n_dim, n_dim)"),
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
            returns=R("np.ndarray", "(4, 4)"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.gamma_matrices", owner="srmech",
            category="qm.relativistic",
            summary="Dirac γ-matrices in the Dirac (standard) representation. "
                    "Cl(1,3) generators. Dirac (1928); Peskin-Schroeder §3.2.",
            parameters=(),
            returns=R("tuple[np.ndarray, ...]", "four 4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.gamma_5", owner="srmech",
            category="qm.relativistic",
            summary="γ_5 = i γ^0 γ^1 γ^2 γ^3 — chirality matrix. "
                    "Peskin-Schroeder §3.4.",
            parameters=(),
            returns=R("np.ndarray", "4×4 Hermitian"),
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
            returns=R("np.ndarray", "4×4 idempotent"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.weyl_right_projector", owner="srmech",
            category="qm.relativistic",
            summary="Right-chirality projector P_R = (I + γ_5)/2. "
                    "Peskin-Schroeder §3.4.",
            parameters=(),
            returns=R("np.ndarray", "4×4 idempotent"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.charge_conjugation_matrix", owner="srmech",
            category="qm.relativistic",
            summary="Charge-conjugation matrix C = i γ^2 γ^0. "
                    "Majorana (1937); Peskin-Schroeder eq A.27.",
            parameters=(),
            returns=R("np.ndarray", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.dirac_operator_momentum_space",
            owner="srmech", category="qm.relativistic",
            summary="Dirac operator (γ^μ k_μ − m I_4) in momentum space. "
                    "Dirac (1928); Peskin-Schroeder §3.2.",
            parameters=(P("k", "np.ndarray", True, "4-vector"),
                        P("m", "float", True, "mass")),
            returns=R("np.ndarray", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.klein_gordon_dispersion",
            owner="srmech", category="qm.relativistic",
            summary="Klein-Gordon dispersion E = +√(|k|² + m²). "
                    "Klein/Gordon (1926); Peskin-Schroeder §2.3.",
            parameters=(P("k_spatial", "np.ndarray", True, "3-vector"),
                        P("m", "float", True, "≥ 0")),
            returns=R("float", "positive on-shell energy"),
        ),
        ToolEntry(
            name="srmech.qm.relativistic.four_momentum_squared", owner="srmech",
            category="qm.relativistic",
            summary="Lorentz-invariant k² = k_μ k^μ (mostly-minus convention).",
            parameters=(P("k", "np.ndarray", True, "4-vector"),),
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
            parameters=(P("k", "np.ndarray", True, "4-vector"),
                        P("m", "float", True),
                        P("epsilon", "float", False)),
            returns=R("np.ndarray", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.propagators.feynman_photon_propagator",
            owner="srmech", category="qm.propagators",
            summary="Photon Feynman propagator D^{μν}(k) = -i g^{μν}/k² (Feynman "
                    "gauge); ξ-gauge with explicit k. Peskin-Schroeder §4.8.",
            parameters=(P("k_squared", "float", True),
                        P("gauge_xi", "float", False, "default 0 ⇒ Feynman"),
                        P("epsilon", "float", False),
                        P("k", "Optional[np.ndarray]", False)),
            returns=R("np.ndarray", "4×4 complex"),
        ),
        ToolEntry(
            name="srmech.qm.propagators.feynman_massive_vector_propagator",
            owner="srmech", category="qm.propagators",
            summary="Massive vector propagator D^{μν}(k) = -i (g^{μν} − k^μ k^ν/m²) "
                    "/ (k² − m² + iε). Peskin-Schroeder §20.1.",
            parameters=(P("k", "np.ndarray", True),
                        P("m", "float", True, "> 0"),
                        P("epsilon", "float", False)),
            returns=R("np.ndarray", "4×4 complex"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.pseudo_hermitian
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.inner_product_eta", owner="srmech",
            category="qm.pseudo_hermitian",
            summary="η-deformed inner product ⟨a|b⟩_η = a^† η b. "
                    "Mostafazadeh (2002).",
            parameters=(P("a", "np.ndarray", True), P("b", "np.ndarray", True),
                        P("eta", "np.ndarray", True)),
            returns=R("complex", ""),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.expectation_eta", owner="srmech",
            category="qm.pseudo_hermitian",
            summary="η-expectation ⟨O⟩_η = ⟨ψ|η O|ψ⟩ / ⟨ψ|η|ψ⟩. "
                    "Mostafazadeh (2002).",
            parameters=(P("O", "np.ndarray", True), P("psi", "np.ndarray", True),
                        P("eta", "np.ndarray", True)),
            returns=R("complex", ""),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.is_pseudo_hermitian", owner="srmech",
            category="qm.pseudo_hermitian",
            summary="Check O† η = η O (η-pseudo-Hermiticity). "
                    "Mostafazadeh (2002).",
            parameters=(P("O", "np.ndarray", True), P("eta", "np.ndarray", True),
                        P("atol", "float", False)),
            returns=R("bool", ""),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.construct_eta_from_eigendecomposition",
            owner="srmech", category="qm.pseudo_hermitian",
            summary="Construct positive η = (V V†)^{-1} from O's eigendecomposition "
                    "so that O is η-pseudo-Hermitian. Mostafazadeh (2002).",
            parameters=(P("O", "np.ndarray", True),
                        P("atol", "float", False)),
            returns=R("np.ndarray", "Hermitian η"),
        ),
        ToolEntry(
            name="srmech.qm.pseudo_hermitian.pseudo_hermitian_eigenvalues_real",
            owner="srmech", category="qm.pseudo_hermitian",
            summary="Verify η-pseudo-Hermitian O has real eigenvalues (Mostafazadeh "
                    "theorem). Bender-Boettcher (1998); Mostafazadeh (2002).",
            parameters=(P("O", "np.ndarray", True), P("eta", "np.ndarray", True),
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
            returns=R("tuple[np.ndarray, np.ndarray, np.ndarray]", "three 2×2"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su2_structure_constants", owner="srmech",
            category="qm.gauge",
            summary="Levi-Civita ε^{abc} — SU(2) structure constants.",
            parameters=(),
            returns=R("np.ndarray", "(3, 3, 3) real"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su3_gell_mann_matrices", owner="srmech",
            category="qm.gauge",
            summary="Eight Gell-Mann matrices λ^1..λ^8 (Hermitian traceless 3×3). "
                    "Gell-Mann (1962).",
            parameters=(),
            returns=R("tuple[np.ndarray, ...]", "eight 3×3"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su3_generators", owner="srmech", category="qm.gauge",
            summary="SU(3) fundamental generators T^a = λ^a/2.",
            parameters=(),
            returns=R("tuple[np.ndarray, ...]", "eight 3×3"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.su3_structure_constants", owner="srmech",
            category="qm.gauge",
            summary="SU(3) totally-antisymmetric f^{abc} (Gell-Mann). "
                    "Peskin-Schroeder eq 17.34.",
            parameters=(),
            returns=R("np.ndarray", "(8, 8, 8) real"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.lie_algebra_residual", owner="srmech",
            category="qm.gauge",
            summary="Max Frobenius violation of [T^a, T^b] = i f^{abc} T^c. "
                    "Peskin-Schroeder §15.1.",
            parameters=(P("generators", "tuple[np.ndarray, ...]", True),
                        P("structure_constants", "np.ndarray", True)),
            returns=R("float", ""),
        ),
        ToolEntry(
            name="srmech.qm.gauge.casimir_operator", owner="srmech",
            category="qm.gauge",
            summary="Quadratic Casimir C_2 = T^a T^a (sum). Peskin-Schroeder §15.4.",
            parameters=(P("generators", "tuple[np.ndarray, ...]", True),),
            returns=R("np.ndarray", "= C_2(R) · I by Schur"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.casimir_eigenvalue", owner="srmech",
            category="qm.gauge",
            summary="Scalar Casimir eigenvalue C_2(R) for irreducible rep. "
                    "Fundamental: 3/4 (SU(2)), 4/3 (SU(3)).",
            parameters=(P("generators", "tuple[np.ndarray, ...]", True),),
            returns=R("float", "≥ 0"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.gauge_connection_matrix", owner="srmech",
            category="qm.gauge",
            summary="Lie-algebra connection A = A^a T^a (Hermitian).",
            parameters=(P("A_components", "np.ndarray", True),
                        P("generators", "tuple[np.ndarray, ...]", True)),
            returns=R("np.ndarray", ""),
        ),
        ToolEntry(
            name="srmech.qm.gauge.gauge_path_segment", owner="srmech",
            category="qm.gauge",
            summary="Path-segment holonomy U = exp(i g A^a T^a) via Hermitian "
                    "eigendecomp (no scipy). Wilson (1974); Peskin-Schroeder §15.3.",
            parameters=(P("A_components", "np.ndarray", True),
                        P("generators", "tuple[np.ndarray, ...]", True),
                        P("coupling", "float", False, "default 1.0")),
            returns=R("np.ndarray", "unitary"),
        ),
        ToolEntry(
            name="srmech.qm.gauge.wilson_loop_from_segments", owner="srmech",
            category="qm.gauge",
            summary="Discrete Wilson loop U(C) = ∏_k exp(i g A_k^a T^a) in path "
                    "order. Wilson (1974).",
            parameters=(P("A_segments", "np.ndarray", True,
                          "(n_segments, n_gen)"),
                        P("generators", "tuple[np.ndarray, ...]", True),
                        P("coupling", "float", False)),
            returns=R("np.ndarray", "unitary"),
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
                    "Peskin-Schroeder §20.2.",
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
            returns=R("np.ndarray", "3×3 unitary"),
        ),
        ToolEntry(
            name="srmech.qm.sm.ckm_unitarity_residual", owner="srmech",
            category="qm.sm",
            summary="Frobenius norm of V V† − I. PDG §12.1.",
            parameters=(P("V", "np.ndarray", True),),
            returns=R("float", "~0"),
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
                "tool count + a per-category breakdown, and the sorted "
                "list of category names. This is a ROOT / INDEX — it "
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
                    "'tools': {'total': int, 'by_category': {category: "
                    "count, ...}}, 'categories': [sorted category "
                    "names]}"
                ),
            ),
        )
    )


def _register_dsl_tools() -> None:
    """Register the declarative cascade-DSL surface (v0.5.0rc12 — DSL voxel).

    The rc8 cascade DSL (``srmech.dsl.*``) composes the 8 cascade-catalog
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
    * ``srmech.dsl.list_catalog_ops()`` — enumerate the 8 cascade-catalog
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
                "from `srmech.dsl.list_catalog_ops` (the 8-op cascade "
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
                "ops the runner can actually resolve (8 ops: "
                "best_rational_signed, chiral_dual, chiral_flip, "
                "cyclic_gcd, magnitude, net_chirality, pin_slot_at_zero, "
                "reorient). Framework reading: Class E (catalog "
                "enumeration) ∘ Class F (descriptor render). No "
                "parameters." + rc12
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
