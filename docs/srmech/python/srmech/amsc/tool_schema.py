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
# The LANE axis (rc347, `#T985`) — what each op READS
# ──────────────────────────────────────────────────────────────────────
#
# rc339 published what each CARRIER can DO. This is the complement, and it is
# a different axis, not a finer grain of the same one: the Cayley-Dickson
# product FACTORS into two lanes, and an op consumes one, the other, or both.
#
#   INDEX lane   e_i * e_j -> e_(i XOR j). ABELIAN, ORDER-BLIND, exact at every
#                rung, unbounded. MEASURED index == XOR with 0 violations at
#                dims 2/4/8/16 (4/4, 16/16, 64/64, 256/256) and on the shipped
#                q8_mult (64/64).
#   SIGN lane    the cocycle over it. ORDER-CARRYING. Every ceiling srmech
#                publishes lives here (rc343 `#T972`).
#
# CHIRALITY IS A SIGN-LANE OPERATION, measured three ways over the basis
# products and moving ZERO indices in all of them: order reversal (the opposite
# algebra) moves 6/16 signs at H, 42/64 at O, 210/256 at S; cd_conjugate 14/64;
# q8_conjugate 24/64. Index preserved 100%. Generating code + NDJSON:
# ``docs/srmech/notes/op_lane_axis_rc347.py``.
#
# THE ADMISSION RULE, and why the field is not just an assertion
# --------------------------------------------------------------
# A declared lane is a claim about behaviour, so it has to be one a measurement
# can CONTRADICT. rc339's ``bounded_by: "associativity"`` is the counter-example
# this rc is written against: it restated the capability's own definition, so no
# carrier row could ever falsify it. ``reads_lane`` is admissible only when both
# of these hold, and ``tests/test_op_lane_rc347.py`` drives every declaring op
# through both:
#
#   1. BOTH perturbations are APPLICABLE to the op's input — the harness can
#      build an input pair differing ONLY in the sign lane, and another
#      differing ONLY in the index lane. An op whose input carries just one of
#      the two cannot declare: ``cascade.net_chirality`` takes bare orientations
#      (no index to move) and ``cascade.cd_basis_product`` takes bare indices
#      (no sign to move), so both are INADMISSIBLE rather than trivially
#      "sign" / "index". A check that cannot fail is the thing being removed.
#   2. The RESPONSE MATCHES THE DECLARATION. Declaring ``sign`` means the output
#      moves under a sigma flip and does NOT move under an index relabel;
#      ``index`` is the mirror; ``both`` must move under both. An op declaring
#      "sign" that moves under a pure index relabel is MIS-DECLARED and the
#      build goes red.
#
# Verdicts are SWEPT, never sampled. A single input can miss a real response —
# an even number of sign flips cancels inside an ordered product, and only about
# one gain vector in fifteen exposes the Lk index response.
#
# THE WORKED EXAMPLE — Tw / Wr / Lk
# ---------------------------------
# ``genome.cwf_consistency_mod2`` is the one shipped op that computes all three,
# so its per-FIELD response IS the adjudication (3000 trials):
#
#   Tw  tw_mod2  sign(algebra) 3000/3000   index 0/3000     -> SIGN,  ALGEBRA
#   Wr  wr       sign(geometry) 3000/3000  algebra 0/3000   -> SIGN,  GEOMETRY
#   Lk  lk_mod2  sign 735/3000             index 182/3000   -> BOTH,  ALGEBRA
#
# The structural point: **Tw and Wr are not one quantity at two resolutions.**
# They read DIFFERENT INPUTS — a coset-sign count over the algebra vs the sign
# of orientation determinants over the geometry — and what they share is the
# LANE. Lk is the only one of the three that responds to an index relabel, so
# it is the only mixer. Wr's magnitude-blindness is the geometry-side proof it
# reads the sign and nothing else: ``discrete_writhe`` is IDENTICAL under
# positive rational rescale x1, x3, x100, x1/7, x999/4 (5/5) while NEGATING
# under a reflection.

#: The closed lane vocabulary. Not free text — an unknown lane is a
#: registration error, exactly as an unknown ``bounded_by`` is in rc343's
#: :data:`srmech.amsc.carrier_schema.CEILING_MECHANISMS`.
LANES: Dict[str, str] = {
    "index": (
        "reads the XOR address only: the output moves under an index relabel "
        "and is UNCHANGED by a sign flip. Abelian, order-blind, unbounded"),
    "sign": (
        "reads the cocycle only: the output moves under a sign flip and is "
        "UNCHANGED by an index relabel. Order-carrying; every published "
        "ceiling lives here"),
    "both": (
        "reads the address AND the cocycle: the output moves under both "
        "perturbations. The mixer case"),
}

#: What the lane is read OF. An op can read one lane over two different inputs
#: (Tw and Wr both read the sign lane; one reads the algebra, the other the
#: geometry), so the input is a SEPARATE axis and not a refinement of the lane.
LANE_INPUTS: Dict[str, str] = {
    "algebra": (
        "a Q8 / Cayley-Dickson element: the index lane is the V4 coset "
        "(q & 3), the sign lane is the center bit (q >> 2)"),
    "geometry": (
        "an exact-rational embedding: the sign lane is the ORIENTATION of the "
        "determinants, the sign-free half is their MAGNITUDE. The magnitude "
        "is the geometry-side ANALOG of the index lane — named as an analogy, "
        "not claimed as the same object"),
}


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
    #: v0.9.0rc240 (#T838) — a human-readable EXPLANATION of what the tool
    #: does / when to use it, beyond the one-line `summary`. ``None`` when
    #: no explanation is registered (introspection consumers fall back to
    #: `summary`). Auto-seeded from each op's docstring + hand-curated for
    #: the central ops; grows toward full coverage under a monotone floor
    #: ratchet. C-mirrored (srmech_tool_entry_t.explanation) → flows through
    #: the tool_schema_sha256 attestation like `summary`/`example`.
    explanation: Optional[str] = None
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
    #: v0.9.0rc305 (`#T943`) — the Siona compose-a-cascade capstone. ``describe()``
    #: / ``example`` are PER-OP; a cascade is CROSS-OP. These two fields carry the
    #: chaining knowledge that otherwise lives only in CHANGELOG prose Siona
    #: cannot read as data.
    #:
    #: ``composes`` — the ORDERED sub-ops this op is built from (or that a
    #: declared cascade chains). Empty for a LEAF op (the correct default); the
    #: call-order sequence of registered op names for a composite. Every listed
    #: name MUST be a real registered tool (the `#T943` claim-is-true contract —
    #: ``test_composes_preserves_rc305.py`` fails otherwise). C-mirrored
    #: (``srmech_tool_entry_t.composes``) → flows through the tool_schema_sha256
    #: attestation like ``summary``/``example``.
    composes: Tuple[str, ...] = ()
    #: ``preserves`` — the INVARIANTS an op / cascade maintains (e.g. "byte-exact
    #: per-community round-trip via kernel_to_graph"). The guarantees a composer
    #: respects and a verifier checks. Each entry is a non-empty claim string.
    #: Empty for a leaf op with no stated invariant. C-mirrored
    #: (``srmech_tool_entry_t.preserves``).
    preserves: Tuple[str, ...] = ()
    #: v0.9.0rc347 (`#T985`) — the LANE axis: which lane of its input this op's
    #: output DEPENDS ON. One of :data:`LANES` (``"index"`` / ``"sign"`` /
    #: ``"both"``), or ``None`` when the op declares no lane. ``None`` is the
    #: correct default and the honest one for the great majority of the
    #: surface: an op whose input carries only ONE of the two lanes cannot
    #: declare, because no measurement could contradict it (see the admission
    #: rule above). Verified executably by ``tests/test_op_lane_rc347.py``,
    #: which drives every declaring op through a sigma flip and an Aut index
    #: relabel and fails the build on a mismatch. C-mirrored
    #: (``srmech_tool_entry_t.reads_lane``).
    reads_lane: Optional[str] = None
    #: v0.9.0rc347 (`#T985`) — WHAT the lane is read of, drawn from
    #: :data:`LANE_INPUTS`. A tuple because an op can read both an algebra and
    #: a geometry input (``cwf_consistency_mod2`` does), and because the
    #: Tw/Wr contrast is precisely that two ops share a LANE while reading
    #: different INPUTS. Empty iff ``reads_lane`` is ``None``; non-empty
    #: whenever it is not — a lane with no input is half a declaration.
    #: C-mirrored (``srmech_tool_entry_t.reads_input``).
    reads_input: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject a malformed lane declaration AT REGISTRATION.

        A closed vocabulary is only closed if something closes it. Both halves
        must be present together: a lane with no input names a behaviour with
        no subject, and an input with no lane names a subject with no claim.
        """
        if self.reads_lane is not None and self.reads_lane not in LANES:
            raise ToolSchemaValidationError(
                f"{self.name}: reads_lane {self.reads_lane!r} is not in LANES "
                f"({sorted(LANES)}) — a lane must be one a perturbation can "
                f"contradict")
        for src in self.reads_input:
            if src not in LANE_INPUTS:
                raise ToolSchemaValidationError(
                    f"{self.name}: reads_input {src!r} is not in LANE_INPUTS "
                    f"({sorted(LANE_INPUTS)})")
        if (self.reads_lane is None) != (not self.reads_input):
            raise ToolSchemaValidationError(
                f"{self.name}: reads_lane and reads_input must be declared "
                f"together or not at all; got reads_lane="
                f"{self.reads_lane!r}, reads_input={self.reads_input!r}")

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
        if self.explanation is not None:
            out["explanation"] = self.explanation
        if self.mcp_unavailable_reason is not None:
            out["mcp_unavailable_reason"] = self.mcp_unavailable_reason
        # v0.9.0rc305 (`#T943`): the compose/preserve layer. Optional keys —
        # omitted when empty (the leaf-op default), mirroring the C serialiser's
        # key-omission (ts_emit_entry) so the byte-identity contract holds. A
        # JSON array of op-name / invariant strings, order-preserving.
        if self.composes:
            out["composes"] = list(self.composes)
        if self.preserves:
            out["preserves"] = list(self.preserves)
        # rc347 (`#T985`): the lane axis. Optional keys, omitted when the op
        # declares no lane (the correct default) — the same key-omission the C
        # serialiser mirrors, so the byte-identity contract holds. Both keys
        # sort between "preserves" and "returns".
        if self.reads_lane is not None:
            out["reads_input"] = list(self.reads_input)
            out["reads_lane"] = self.reads_lane
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

# v0.9.0rc240 (#T838) — the generated introspection docs floor: per-tool
# EXPLANATION (docstring-seeded) + EXAMPLE (executed I/O where safe, else an
# honest signature snippet), hand-curation merged in at generation time. A
# guarded import so a stripped/missing _tool_docs never breaks package import.
try:  # pragma: no cover - trivial import guard
    from ._tool_docs import TOOL_DOCS as _TOOL_DOCS
except Exception:  # noqa: BLE001
    _TOOL_DOCS: Dict[str, Dict[str, Any]] = {}


def _apply_docs(entry: ToolEntry) -> ToolEntry:
    """Merge the generated `_TOOL_DOCS` floor into a ToolEntry: fill
    ``explanation`` / ``example`` / ``composes`` / ``preserves`` only when the
    entry does not already carry its own (a hand-written literal on the
    registration always wins). No-op when the tool has no docs entry."""
    doc = _TOOL_DOCS.get(entry.name)
    if not doc:
        return entry
    from dataclasses import replace
    expl = entry.explanation if entry.explanation is not None \
        else doc.get("explanation")
    ex = entry.example if entry.example is not None else doc.get("example")
    # v0.9.0rc305 (`#T943`): the compose/preserve layer rides the same
    # curation floor as explanation/example. A non-empty tuple on the
    # registration wins; else the curated list (coerced to a tuple so the
    # ToolEntry stays hashable / frozen-friendly) fills in.
    composes = entry.composes if entry.composes \
        else tuple(doc.get("composes", ()))
    preserves = entry.preserves if entry.preserves \
        else tuple(doc.get("preserves", ()))
    if (expl is entry.explanation and ex is entry.example
            and composes == entry.composes and preserves == entry.preserves):
        return entry
    return replace(entry, explanation=expl, example=ex,
                   composes=composes, preserves=preserves)


def register_tool(entry: ToolEntry) -> None:
    """Register one tool entry. Idempotent on identical re-registration;
    raises :class:`ToolSchemaConflictError` on a name collision with
    differing content."""
    assert isinstance(entry, ToolEntry), \
        f"register_tool: expected ToolEntry, got {type(entry).__name__}"
    assert entry.name, "register_tool: entry.name must be non-empty"
    entry = _apply_docs(entry)
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
    (registration order within each profile).

    Kept a PURE constructor over the live registry (v0.9.0rc185 dispatch
    boundary, option (b)): this is the independent Python SSoT the rc184
    hash-ratchet locks the C const table against, so it must NOT itself
    route through the C table (that would make the ratchet circular). The
    bare-C host peer ``srmech_get_tool_schema`` realises the SAME data —
    proven equivalent by object reconstruction in
    ``tests/test_tool_schema_ops_c_rc185.py``.
    """
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
    CLI invocation.

    v0.9.0rc185 — when no profile tools are registered (the C const table
    IS the live srmech registry, locked by the rc184 hash-ratchet) and the
    rc185 C peer is loaded, the view is produced by the bare-C host op
    ``srmech_tool_schema_view`` and parsed back — VALUE-identical to the
    pure ``get_tool_schema().to_jsonable()`` (dict equality is
    order-insensitive; the native keys are in canonical/sorted order). Any
    profile tool, a stale/absent lib, or a non-OK C status falls back to
    the pure path.
    """
    if not any(e.owner != "srmech" for e in _REGISTRY.values()):
        native = _native_tool_schema_view()
        if native is not None:
            return native
    return get_tool_schema().to_jsonable()


def _native_tool_schema_view() -> Optional[Dict[str, Any]]:
    """The rc185 C ``srmech_tool_schema_view`` output parsed to a dict, or
    ``None`` when the native peer is unavailable / returns non-OK."""
    try:
        from . import _native
    except Exception:  # pragma: no cover — defensive; _native always imports
        return None
    raw = _native.tool_schema_view_c()
    if raw is None:
        return None
    return json.loads(raw.decode("utf-8"))


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
            # NO literal ``example=`` here on purpose (`#T1006`). A hand-written
            # example on the REGISTRATION always wins the ``_apply_docs`` merge
            # (see :func:`_apply_docs`), so a stub here permanently SHADOWS
            # ``_tool_docs_curated.py`` — the file the project designates as the
            # one to hand-edit. Both this op and ``sha256_batch`` carried a
            # one-call ``{input, output}`` stub that silently outranked the
            # worked, executed, sibling-disambiguating entry curation supplies.
            # Curate in ``_tool_docs_curated.py``; leave this field absent.
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
            # NO literal ``example=`` here on purpose (`#T1006`) — see the note
            # on ``sha256_bytes`` above. A registration literal outranks
            # ``_tool_docs_curated.py``, so a stub here makes curation
            # unreachable for this tool.
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

    # rc340 (#T965) — the genome CARRIER parameter, published on the wire.
    #
    # Every genome op whose Python surface takes `element_type` declares THIS
    # parameter, so the MCP/tool-schema surface offers the same rung choice the
    # library does. Before rc340 the two disagreed: `quad_turn` (and 18 more) took
    # element_type in Python while their tool entries did not publish it, so a remote
    # caller silently got the DEFAULT rung — KLEIN-4, which is ABELIAN and therefore
    # carries no which-way — with no way to ask for another and no error saying so.
    # A silently-wrong carrier is worse than an absent parameter, so this is the same
    # parity crack as #T954, across the Python/MCP boundary instead of Python/C.
    #
    # Declared as `str` (the NAME) because that is the form an LLM consumer can read
    # and write; `genome._element_type_code` accepts the int enum equally, so a caller
    # holding a code is not shut out.
    ET_PARAM = P(
        "element_type", "str", False,
        "keyword-only; the CARRIER rung the turns are coupled through — a CAPABILITY "
        "LADDER, not a size knob: 'klein4' (0, the DEFAULT; V4, abelian — every turn "
        "composes and none carries a which-way), 'q8' (1; the only rung where a "
        "NON-COMMUTING turn still folds), 'octonion' (2; addressing reaches e4..e7, "
        "but turn composition degrades to abelian-only). The int code works too. "
        "Read the measured verdicts + the evidence each was derived from in "
        "introspect.describe()['limits']['element_types'].")

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
            summary="Modular multiply — (a * b) mod n — overflow-safe via "
                    "russian-peasant doubling; portable across platforms "
                    "without __int128. Capped at uint64; use mod_mul_wide for "
                    "a wider modulus (e.g. the 128-bit PCG64 step).",
            parameters=(P("a", "int", True), P("b", "int", True),
                        P("n", "int", True, "modulus > 0")),
            returns=R("int", "in [0, n)"),
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.mod_pow", owner="srmech", category="cyclic",
            summary="Modular exponentiation — (a ** k) mod n — via "
                    "square-and-multiply. Bounded by uint64.",
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
        ToolEntry(
            name="srmech.amsc.cyclic.bigint_mul", owner="srmech", category="cyclic",
            summary="Bignum multiply — the uncapped integer product a * b "
                    "(arbitrary precision) on srmech's own C bignum "
                    "(srmech_bigint_mul); the building block a > 64-bit "
                    "modular cascade (the PCG64 step) needs before the "
                    "mod-reduce. No uint64 cap; Python a*b fallback when "
                    "native is absent.",
            parameters=(P("a", "int", True), P("b", "int", True)),
            returns=R("int", "the exact product a * b"),
            smoke_test_hint={"a": "6", "b": "7"},
        ),
        ToolEntry(
            name="srmech.amsc.cyclic.mod_mul_wide", owner="srmech",
            category="cyclic",
            summary="Wide modular multiply — (a * b) mod n with NO uint64 cap "
                    "(the 128-bit-capable modular multiply). Routes the "
                    "product through srmech's C bignum (srmech_bigint_mul) "
                    "and reduces mod n, so a > 64-bit modulus (the raw PCG64 "
                    "LCG step at n = 2**128) is expressible where the capped "
                    "mod_mul cannot. a / b non-negative, n > 0, any width.",
            parameters=(P("a", "int", True, "non-negative, any width"),
                        P("b", "int", True, "non-negative, any width"),
                        P("n", "int", True, "modulus > 0, any width")),
            returns=R("int", "in [0, n)"),
            smoke_test_hint={"a": "2**64", "b": "3", "n": "2**128"},
        ),
        # ────────────────────────────────────────────────────────────
        # Class I — modular linear algebra: GF(p) reduced row-echelon form
        # (rc44, rung 1 of the CRT-QMat re-fibration arc).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.modular_linalg.gf_rref", owner="srmech",
            category="modular_linalg",
            summary="Reduced row-echelon form of an integer matrix over the finite "
                    "field GF(p) — Gaussian elimination over a prime field (cf. "
                    "Cohen, *A Course in Computational Algebraic Number Theory*, "
                    "1993, Algorithm 2.3.1; von zur Gathen & Gerhard, *Modern "
                    "Computer Algebra*, 3rd ed. 2013, §5.4). The swell-free core of "
                    "the rc44 CRT re-fibration: exact-ℚ Gauss-Jordan grows numerators "
                    "and denominators at every pivot (a Hadamard-bounded arena, ~GB "
                    "for the order-2 Franel system), whereas GF(p) elimination has "
                    "ZERO coefficient swell — every residue stays in [0, p). Input: "
                    "an integer matrix (list of equal-length int rows; entries may be "
                    "negative, reduced into [0, p) first) and a prime p with "
                    "2 <= p < 2**31 (so a*b fits uint64; primality is the caller's "
                    "contract). p = 2 is in domain as of rc350 — characteristic 2 "
                    "needs no division (1⁻¹ = 1) and the row op is XOR, and GF(2) is "
                    "the grading field of every Cayley–Dickson rung srmech ships "
                    "(e_i·e_j lands on index i XOR j at every dim in CD_DIMS), so "
                    "index-lane questions about ℂ / ℍ / 𝕆 / 𝕊 are GF(2) linear "
                    "algebra. Class I (composes mod_inv / mod_mul / mod_add); "
                    "Class-K sign/zero handling (compare-to-0, never abs()); bounded "
                    "machine-int, no fraction growth, no bignum, no float, no numpy / "
                    "math. 1:1 C peer srmech_gf_rref (in-place int64 caller-arena; "
                    "native when present, pure-Python the complete alternative).",
            parameters=(P("rows", "list[list[int]]", True,
                          "the integer matrix as a list of equal-length int rows "
                          "(entries may be negative)"),
                        P("p", "int", True,
                          "a prime with 2 <= p < 2**31 (the field modulus; "
                          "GF(2) included)")),
            returns=R("dict",
                      "{'rref': [[int]] (every entry in [0, p)), 'rank': int, "
                      "'pivots': [int] (the pivot column of each pivot row, "
                      "ascending)}"),
        ),
        # ────────────────────────────────────────────────────────────
        # Class I — CRT combine (rc45, rung 2 of the CRT-QMat re-fibration
        # arc). The per-prime-residues → one-residue-mod-product closer.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.modular_linalg.crt_combine", owner="srmech",
            category="modular_linalg",
            summary="Chinese-Remainder-combine per-prime residues into one residue "
                    "modulo the product of the primes — the CRT (cf. Knuth, *The "
                    "Art of Computer Programming*, vol. 2, 3rd ed. 1997, §4.3.2; von "
                    "zur Gathen & Gerhard, *Modern Computer Algebra*, 3rd ed. 2013, "
                    "§5.4). The Class-I combine of the rc45 CRT re-fibration: after "
                    "gf_rref solves modulo several machine-int primes (each a "
                    "swell-free GF(p) elimination), this merges the per-prime "
                    "residues back into one congruence. Input: residues [r_0..r_k-1] "
                    "and pairwise-coprime moduli [m_0..m_k-1] (distinct primes from "
                    "the CRT sequence). Returns {'residue': int, 'modulus': int} with "
                    "residue ≡ r_i (mod m_i) for all i and modulus = ∏ m_i, residue "
                    "in [0, modulus). Iterative Garner CRT composing mod_inv / "
                    "mod_mul; the combined modulus exceeds 64 bits for k ≳ 3 of the "
                    "~31-bit primes, so the accumulator is bignum (Python int, no "
                    "ceiling) while the per-step inverse stays in uint64. Class-K "
                    "sign/zero handling (non-negative %, never abs()); no float, no "
                    "numpy / math. 1:1 C peer srmech_crt_combine (over srmech_bigint, "
                    "caller-arena; native when present, pure-Python the complete "
                    "alternative).",
            parameters=(P("residues", "list[int]", True,
                          "the per-prime residues [r_0..r_k-1]"),
                        P("moduli", "list[int]", True,
                          "the pairwise-coprime moduli [m_0..m_k-1] (distinct "
                          "primes), same length as residues")),
            returns=R("dict",
                      "{'residue': int (≡ r_i mod m_i for all i, in [0, modulus)), "
                      "'modulus': int (∏ m_i)}"),
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
        # front, in srmech.amsc.text (ingestion module; laplacian stays purely
        # spectral). `glyph_stream → cooccurrence_edges → dense_laplacian → …`
        # authorable end-to-end; retires the hand-rolled Counter() idiom. The
        # rc43 versions FAILED the §40 acceptance bar 3/3 (ASCII tokenize /
        # silent vocab cap / no doc-boundary reset) — rc50 fixed all three.
        # rc287: the UNIT changed from the word to the UAX #29 grapheme
        # cluster (BREAKING — `tokenize` and DEFAULT_STOPLIST are gone, with no
        # shim). All three dispatch to BYTE-IDENTICAL C peers
        # (srmech_text_glyph_stream / _cooccurrence_edges / _cooccurrence_topk
        # + _topk_extract) — the corpus-linear hot loops run in C; the pure
        # bodies remain the complete alternative + parity oracle.
        # rc293 (#928 / F1258 / UPSTREAM_NOTES §106): the FOLD gap - the one
        # domain-agnostic piece of the downstream tokenizer srmech did not
        # already own. Its own op, NOT a mode on glyph_stream: glyph_stream
        # documents a losslessness invariant that a fold flag would break for
        # one flag value, and the two have different shapes (str -> list[str]
        # vs str -> str). Ordinary composition keeps both honest. The table is
        # vendored (UCD 16.0.0) on the ADR-0003 argument - a bare-C host has no
        # unicodedata - and BOTH projections read it, so they cannot diverge.
        ToolEntry(
            name="srmech.amsc.text.fold_marks", owner="srmech",
            category="text",
            summary="Drop combining marks by Unicode CATEGORY - Mn/Mc/Me and "
                    "nothing else (Class B/G text-framing; §106/F1258; "
                    "rc293). The name is the contract: a VIRAMA is a mark, not "
                    "an accent, so `fold_accents` would have been wrong in "
                    "exactly the Indic cases that matter most while quietly "
                    "re-scoping the op toward Latin - fold_marks('क्षि') = "
                    "'कष', not just fold_marks('naïve') = 'naive'. Scope is "
                    "category only: no case change, no locale tailoring, no "
                    "NFKD/compatibility folding, no ligature expansion - so "
                    "'ø' and the OHM SIGN are unchanged (a stroke is part of "
                    "the letter; a mark-free singleton is not this op's "
                    "business) and Hangul is unchanged in either "
                    "normalization form. Needs NO normalizer: precomposed "
                    "characters are handled by the table's replacement rows "
                    "and decomposed sequences by its drop rows, so the same "
                    "marks fall out whichever form is supplied. Idempotent - "
                    "the vendored table is closed, so one pass is complete. "
                    "A SEPARATE op, not a glyph_stream mode: folding is lossy "
                    "and glyph_stream is contractually lossless; compose them "
                    "as glyph_stream(fold_marks(s)).",
            parameters=(P("text", "str", True),),
            returns=R("str", "text with combining marks dropped and "
                             "precomposed mark-bearing characters reduced to "
                             "their base"),
        ),
        ToolEntry(
            name="srmech.amsc.text.glyph_stream", owner="srmech",
            category="text",
            summary="Segment text into UAX #29 EXTENDED GRAPHEME CLUSTERS — the "
                    "language-agnostic glyph stream (Class B/G "
                    "text-segmentation; §40/F698; rc287). A cluster is what a "
                    "reader perceives as ONE character, and it is the only unit "
                    "well-defined in every script, so there is no per-language "
                    "word decision: no length floor, no casefold, no stoplist. "
                    "It REPLACES the former `tokenize`, whose word decision "
                    "carried four Latin-shaped assumptions — scriptio-continua "
                    "scripts collapsed into single 45-96 character tokens with "
                    "~89% of types singletons, single-codepoint CJK content "
                    "words and the Hawaiian okina were deleted outright, and "
                    "every emoji sequence returned empty. Emoji ZWJ sequences "
                    "(GB11), flag pairs (GB12/13) and Indic conjuncts (GB9c) "
                    "each come back as ONE cluster. Lossless: ''.join(result) "
                    "reconstructs the NFC-normalised input exactly. Scores "
                    "1093/1093 on the official UAX #29 GraphemeBreakTest in "
                    "both coherency projections; the break table is vendored "
                    "(UCD 16.0.0) because Extended_Pictographic and InCB are "
                    "not derivable from unicodedata at any fidelity. The "
                    "text→glyphs front of the K1 text→graph→spectral chain.",
            parameters=(P("text", "str", True),
                        P("unicode_normalize", "bool", False,
                          "NFC-normalise text first (default True)")),
            returns=R("list[str]", "the UAX #29 grapheme-cluster stream"),
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
                    "(n, edges, weights) for dense_laplacian; directed=True adds "
                    "a metric+charge SUPERSET for magnetic_laplacian; retires "
                    "Counter().",
            parameters=(P("docs", "list", True,
                          "Sequence[Sequence[str]] (one per document; window "
                          "resets per doc) or a flat token Sequence[str]"),
                        P("window", "int", False, "co-occurrence window (default 2)"),
                        P("vocab", "list", False,
                          "explicit ranked vocab (index=position); None builds "
                          "the full vocab from frequency"),
                        P("vocab_size", "int", False,
                          "explicit top-K cap (logged); None = no cap (all)"),
                        P("directed", "bool", False,
                          "False (default) returns (n, edges, weights); True "
                          "returns the (n, edges, metric, charge) superset — "
                          "metric == the undirected weights, charge = w_fwd − "
                          "w_bwd (for magnetic_laplacian; #1390 item 1)")),
            returns=R("tuple[int, list[tuple[int, int]], list[int]]",
                      "(n nodes, edge list, integer co-occurrence counts); "
                      "directed=True → (n, edges, metric, charge) with a fourth "
                      "signed-integer charge list"),
        ),
        # §52 (F793): the streaming / bounded LOW-RAM ENCODE peer of
        # cooccurrence_edges — for building the spectral-clump graph on an edge
        # device (encode trades RAM for chunked streaming).
        ToolEntry(
            name="srmech.amsc.text.cooccurrence_topk", owner="srmech",
            category="text",
            summary="Streaming / bounded top-K co-occurrence — the LOW-RAM "
                    "ENCODE peer of cooccurrence_edges (§52/F793). Streams docs "
                    "one at a time (never all resident) and keeps only a bounded "
                    "top-K-per-node store via chunked merge (per-node cap "
                    "k*cap_slack), so the encode peak is O(vocab × k·cap_slack) "
                    "not the full ~edge list. Bit-exact when a node's degree "
                    "stays under the cap; heavy hitters keep full summed weight. "
                    "The explicit bounded analog of the §50 holographic "
                    "cooccurrence_fold; returns a drop-in (n, edges, weights) for "
                    "fiedler_sparse + the {token:[(neighbour,weight)…]} view.",
            parameters=(P("docs", "list", True,
                          "stream of token sequences (per-document) or a flat "
                          "token Sequence[str]; consumed lazily, never all resident"),
                        P("window", "int", False, "co-occurrence window (default 2)"),
                        P("k", "int", False, "top-K neighbours kept per node (default 20)"),
                        P("vocab", "list", False,
                          "explicit vocab (index=position); None builds it "
                          "incrementally (first-seen order)"),
                        P("cap_slack", "int", False,
                          "per-node cap = k*cap_slack before truncation (default 4)"),
                        P("chunk_docs", "int", False,
                          "documents per bounded merge chunk (default 2048)")),
            returns=R("dict",
                      "{n, vocab, edges, weights, topk} — bounded sparse graph + "
                      "per-token top-K view"),
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
        # rc328 (task #893 / #888 rec (c)): the Laplace–Beltrami α-family.
        # mass_normalized_laplacian generalises normalized_laplacian from
        # degree-D to an arbitrary diagonal mass M (α=0 connectivity vs α=1
        # metric / discrete LB); cotangent_weights emits the LB stiffness
        # edge weights that feed dense_laplacian. Both are c_dispatched.
        ToolEntry(
            name="srmech.amsc.laplacian.mass_normalized_laplacian", owner="srmech",
            category="laplacian",
            summary="Mass-normalized (Laplace–Beltrami α-family) Laplacian: "
                    "M^{-1/2}(D-W)M^{-1/2} (kind='symmetric', PSD) or "
                    "M^{-1}(D-W) (kind='rw', rows sum to 0). masses=None → "
                    "M=degree D (α=0 connectivity; recovers normalized_laplacian); "
                    "masses=Voronoi areas → α=1 metric / discrete Laplace–Beltrami "
                    "spectrum. The M^{-1/2} sqrt is the Class-N rational cascade; "
                    "native C dispatch. #888 scoping.",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False),
                        P("masses", "Optional[list[float]]", False,
                          "diagonal mass M; None → degree D (α=0)"),
                        P("kind", "str", False,
                          "'symmetric' (default) or 'rw' (random-walk)")),
            returns=R("Mat", "n × n real mass-normalized Laplacian (numpy-free Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.cotangent_weights", owner="srmech",
            category="laplacian",
            summary="Cotangent-weight Laplacian weights — the discrete "
                    "Laplace–Beltrami edge weights on a triangulated manifold "
                    "(Pinkall & Polthier 1993). Per triangle emits the three "
                    "per-corner ½·cot(θ) contributions cot θ = (u·v)/|u×v| "
                    "(|u×v| via the Lagrange identity; NO trig, NO abs, one "
                    "algebraic sqrt/corner). Returns (edges, weights) whose "
                    "parallel-edge accumulation in dense_laplacian gives the "
                    "standard ½(cot α + cot β). positions are given data, NOT "
                    "CAD mesh geometry. #888.",
            parameters=(P("triangles", "list[tuple[int, int, int]]", True,
                          "vertex-index triples (i, j, k) per triangle"),
                        P("positions", "list[list[float]]", True,
                          "vertex coordinates, 2-D or 3-D")),
            returns=R("tuple", "(edges: list[tuple[int, int]], weights: list[float]) "
                               "— feed straight to dense_laplacian(n_vertices, ...)"),
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
                    "real symmetrised Laplacian (undirected control). "
                    "rc105 (#1234 Item 3 / F1006 / F1007): per-edge charges= "
                    "is the CHIRAL Laplacian for dual-sense knowledge graphs "
                    "— edge (u,v,w,c) contributes the conjugate pair "
                    "−(w/2)e^{±i·2π·c}, so an is-a/is-not-a pair (a,+q)+(b,−q) "
                    "SURVIVES as −[(a+b)/2·cos2πq + i(a−b)/2·sin2πq] (the "
                    "imbalance in the imaginary residue) instead of "
                    "annihilating as in signed_laplacian. q and charges are "
                    "mutually exclusive. Native standalone-C "
                    "srmech_graph_magnetic_laplacian (both modes; Q61 trig "
                    "cascade → bit-identical to the pure path).",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True,
                          "directed u → v"),
                        P("weights", "Optional[list[float]]", False),
                        P("q", "float", False,
                          "flux in turns per unit net flow; default 0.25; "
                          "mutually exclusive with charges"),
                        P("charges", "Optional[list[float]]", False,
                          "per-edge charge in turns, parallel to edges "
                          "(len(charges) == len(edges)); (u,v,c) ≡ (v,u,−c); "
                          "mutually exclusive with q")),
            returns=R("Mat", "n × n complex Hermitian matrix (numpy-free Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.quaternion_laplacian", owner="srmech",
            category="laplacian",
            summary="Quaternion (ℍ) gain Laplacian — the ASSOCIATIVE dim-4 rung "
                    "of magnetic_laplacian (the ℂ dim-2 complex-unit-gain "
                    "Laplacian). A 4n×4n REAL-SYMMETRIC matrix whose (u,v) block "
                    "is the 4×4 real left-mult rep L(g) of a unit-quaternion "
                    "gain g∈Sp(1), (v,u) block L(conj g)=L(g)ᵀ, diagonal block "
                    "(Σ w/2)·I₄. Feed to mat_hermitian_eigendecompose. TWO "
                    "spectral facts: the spectrum is GAUGE-INVARIANT under the "
                    "node-wise unit-quaternion gauge g_uv→s_u·g_uv·conj(s_v) "
                    "(~3.3e-15; the ℍ generalisation of the U(1) gauge "
                    "invariance), and every eigenvalue is ×4 DEGENERATE (a "
                    "THEOREM: ℍ associativity ⇒ the left-built matrix commutes "
                    "with the fixed right-ℍ Sp(1) commutant — callers dedupe "
                    "every 4th). gains=None → identity gain (½·dense-L ⊗ I₄). "
                    "Class L composing Class-M quaternion_left_mult "
                    "(srmech_quaternion_left_mult); no new C symbol. DERIVED: "
                    "Reff (2012) LAA 436, 3165–3176 (arXiv:1110.4554) one "
                    "Cayley–Dickson rung up; ℍ per Baez (2002) "
                    "arXiv:math/0105155 §1.",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False),
                        P("gains", "Optional[list[list[float]]]", False,
                          "per-edge unit quaternions (4-vectors) parallel to "
                          "edges; default identity gain (1,0,0,0); normalised "
                          "to Sp(1) via quaternion_norm")),
            returns=R("Mat",
                      "4n × 4n real-symmetric quaternion gain Laplacian "
                      "(numpy-free Mat)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.hypercomplex_perspectives",
            owner="srmech", category="laplacian",
            summary="Split each eigenvector into a scalar channel e0 + (dim−1) "
                    "imaginary phase channels — the hypercomplex reader for "
                    "quaternion_laplacian (dim=4, ℍ, 4=1+3) that ALSO closes "
                    "the latent dim-2 read of magnetic_laplacian (dim=2, ℂ, "
                    "2=1+1). eigvecs is the (N×M) eigenvector Mat (columns = "
                    "eigenvectors, the 2nd return of "
                    "mat_hermitian_eigendecompose). dim=2 → each complex entry "
                    "is one number (e0=re, e1=im); dim=4 → each block of 4 real "
                    "entries is one quaternion at one node (e0 scalar, e1/e2/e3 "
                    "imaginary axes); dim=1 → real scalar. Returns a dict "
                    "{dim, n_vectors, n_blocks, channel_names, vectors} with one "
                    "channel-dict per eigenvector. Class L (spectral read-out; a "
                    "pure structural split).",
            parameters=(P("eigvecs", "Mat", True,
                          "the (N×M) eigenvector Mat (columns = eigenvectors)"),
                        P("dim", "int", False,
                          "real components per hypercomplex unit: 1 (ℝ), 2 (ℂ) "
                          "or 4 (ℍ); default 4")),
            returns=R("dict",
                      "{dim, n_vectors, n_blocks, channel_names, vectors}"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc229 (#687) — the fuller asymmetric-halves lattice handle: the
        # V4-gain (Klein-4-sector) Laplacian (EVEN channel; C peer
        # srmech_graph_klein4_gain_laplacian) + its joint read-out +
        # cycle_holonomy (ODD channel; C peer srmech_graph_cycle_holonomy).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.klein4_gain_laplacian", owner="srmech",
            category="laplacian",
            summary="The V₄-gain (Klein-4-sector) Laplacian (#687): the "
                    "EVEN-channel fuller partner of magnetic_laplacian. Each "
                    "edge carries a V₄ = ℤ₂×ℤ₂ gain (TWO sign bits, int 0..3 "
                    "or a 2-tuple), and V₄'s FOUR real characters "
                    "χ_ab(g)=(−1)^(a·g0+b·g1) decompose the object into FOUR "
                    "real signed Laplacians L_χ = D̄ − χ(g_e)·A — the two-bit "
                    "generalization of the one-bit signed_laplacian. The two "
                    "gain bits are SYMMETRIC (neither privileged). Signed "
                    "degree D̄=Σ|A_ij| is the Class-K magnitude (no abs()) and "
                    "is character-independent, so χ00 (trivial) == "
                    "dense_laplacian for unit gains; the four sectors drop into "
                    "spectral_block_dispatch, and their spectrum equals the "
                    "ordinary Laplacian spectrum of the V₄ abelian COVER (4n "
                    "nodes). Native standalone-C srmech_graph_klein4_gain_"
                    "laplacian (all four sectors in one call; else four "
                    "signed_laplacian builds — byte-identical). Reff LAA 436 "
                    "(2012), arXiv:1110.4554. numpy-free.",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False,
                          "may be negative"),
                        P("gains", "Optional[list[int | tuple[int, int]]]",
                          False,
                          "per-edge V₄ gain parallel to edges — int 0..3 "
                          "(g1<<1|g0) or a 2-tuple (g0, g1); None → all "
                          "identity (the four sectors coincide)")),
            returns=R("dict[str, Mat]",
                      "{'chi00','chi01','chi10','chi11'} → the four n×n "
                      "real-symmetric PSD sector Laplacians"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.klein4_relational_structure",
            owner="srmech", category="laplacian",
            summary="The joint EVEN-channel read-out of a V₄-gain relational "
                    "graph (#687): per-sector spectral tensions (λ_min = "
                    "frustration, 0 iff balanced) + coherences (λ₂ = algebraic "
                    "connectivity) + the Class-K sector-asymmetry meter between "
                    "the two MIXED sectors χ10/χ01 — the (4:3)|(3:4) sector-"
                    "occupancy diagnostic (F552: a chirality-collapse deviation "
                    "lands here, random noise does not). Diagnostic, not "
                    "predictive — the orientation LABEL needs the ODD-channel "
                    "cycle_holonomy. Composes klein4_gain_laplacian + "
                    "symmetric_eigendecompose (one eigensolve per sector); no "
                    "dedicated C symbol. numpy-free; no abs().",
            parameters=(P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False),
                        P("gains", "Optional[list[int | tuple[int, int]]]",
                          False, "per-edge V₄ gains (see klein4_gain_laplacian)"),
                        P("n", "Optional[int]", False,
                          "node count; inferred from edges when None")),
            returns=R("dict",
                      "{'sectors', 'tension': {sector: λ_min}, 'coherence': "
                      "{sector: λ₂}, 'sector_asymmetry': |Δ tension χ10,χ01|}"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.cycle_holonomy", owner="srmech",
            category="laplacian",
            summary="The cycle holonomies of a gain graph (#687): the ODD "
                    "channel the (Hermitian/signed) SPECTRUM provably cannot "
                    "carry (a conjugated Hermitian matrix has the same "
                    "eigenvalues, so the which-way ± sign is invisible to any "
                    "spectral read — F552). A gain graph is determined up to "
                    "switching by its cycle gains (Zaslavsky). Builds a "
                    "spanning forest (union-find; first-encountered edge = tree "
                    "edge) → the fundamental cycle per co-tree edge → that "
                    "cycle's NET charge (per-edge charges in TURNS, exact "
                    "Fraction, reduced mod 1) — Class I (mod-1 cyclic) ∘ "
                    "Class L (graph); NO eigensolve. Invariant under node "
                    "re-gauging (a coboundary telescopes); 0 for every cycle "
                    "IFF balanced (Zaslavsky's criterion); distinguishes +c "
                    "from −c (1/4 vs 3/4 mod 1) — the chirality the sector "
                    "spectra cannot. Pairs with klein4_gain_laplacian (even) "
                    "to complete the read. Native standalone-C "
                    "srmech_graph_cycle_holonomy (exact int64 rational, "
                    "caller-arena); else the exact-Fraction cascade (handles "
                    "any denominator). Zaslavsky, DAM 4 (1982) 47–74. "
                    "numpy-free; no abs().",
            parameters=(P("edges", "list[tuple[int, int]]", True,
                          "a self-loop is a 1-cycle; a parallel edge a digon"),
                        P("charges", "Optional[list[int | Q | float]]",
                          False,
                          "per-edge charge in TURNS parallel to edges; None → "
                          "all 0 (balanced); (u,v,c) ≡ (v,u,−c)"),
                        P("n", "Optional[int]", False,
                          "node count; inferred from edges when None")),
            returns=R("dict",
                      "{'n_cycles', 'holonomies': list[Q] in [0,1), "
                      "'cycle_edges': list[(u,v)], 'balanced': bool}"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.eulerian_path", owner="srmech",
            category="laplacian",
            summary="The Eulerian TRAIL of a DIRECTED edge multiset (#1390 item "
                    "3): the ordered node walk that consumes every edge exactly "
                    "once, or None if no single Eulerian trail exists. The "
                    "Hierholzer walk-reconstruction the directed Class-L genome "
                    "store recovers a sequence with (the sandroing/word round-"
                    "trip). Feasibility is CHECKED (degree balance + full-edge-"
                    "consumption connectivity) — an infeasible / disconnected "
                    "graph returns None, never a partial walk. Deterministic "
                    "start: the unique out=in+1 node (a path) or the min out-"
                    "bearing node (a circuit; start overrides). Nodes any "
                    "hashable; repeats / self-loops ok. O(|E|). Native "
                    "srmech_eulerian_walk (byte-identical for integer nodes); "
                    "else the pure Hierholzer. numpy-free; no abs().",
            parameters=(P("edges", "list[tuple[int, int]]", True,
                          "the directed edge multiset [(u,v),...] (repeats / "
                          "self-loops ok; nodes any hashable)"),
                        P("start", "Optional[int]", False,
                          "the start node (honoured for a circuit; a path forces "
                          "the +1 node); None = derived")),
            returns=R("list | None",
                      "the Eulerian trail (node list, len |edges|+1), or None if "
                      "no single Eulerian trail exists"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.eulerian_circuit", owner="srmech",
            category="laplacian",
            summary="The Eulerian CIRCUIT of a DIRECTED edge multiset (#1390 "
                    "item 3): as eulerian_path but REQUIRES a closed circuit "
                    "(every node balanced) — returns a walk with start == end, "
                    "or None if the graph is not balanced + connected. Same "
                    "Hierholzer, node-agnostic; the directed Class-L genome "
                    "recovers a cyclic sequence with it. Native "
                    "srmech_eulerian_walk (circuit_only; byte-identical for "
                    "integer nodes). numpy-free; no abs().",
            parameters=(P("edges", "list[tuple[int, int]]", True,
                          "the directed edge multiset [(u,v),...] (repeats / "
                          "self-loops ok; nodes any hashable)"),
                        P("start", "Optional[int]", False,
                          "the start (== end) node; None = the min out-bearing "
                          "node")),
            returns=R("list | None",
                      "the Eulerian circuit (node list, start == end), or None if "
                      "not balanced + connected"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.recover_check", owner="srmech",
            category="laplacian",
            summary="The packaged round-trip integrity check of a stored "
                    "directed Class-L graph (#1390 item 4): the FOUR faculties a "
                    "genome must recover — op (L=D−A eigendecomposes, PSD, a ~0 "
                    "null mode), operand (weighted edges present, non-degenerate, "
                    "uncapped — not a top-K amputation), responsion (the "
                    "propagator e^{−zL} is excitable, reach>0), and curvature (a "
                    "DIRECTED store keeps its charge; a symmetric bag has exactly "
                    "zero curvature — PASSES the metric faculties, FLAGGED "
                    "directionless, F1210). ok == op and operand and responsion — "
                    "curvature is REPORTED honestly, NOT a hard gate, so a "
                    "legitimately acyclic (F1218) / coherent net-zero (F1146) "
                    "directed graph is never a false failure. Integer charge is "
                    "phase-scaled (q=1/(2·max|c|+1)) so it does not alias to 0 "
                    "mod 1. A domain-free composition of shipped C-routed ops "
                    "(dense_laplacian / symmetric_eigendecompose / "
                    "magnetic_laplacian / responsion / cycle_holonomy) — the "
                    "dense op/responsion need vocab_size<=256; use "
                    "recover_check_structural / _spectral at corpus scale "
                    "(F1227). numpy-free; no abs().",
            parameters=(P("vocab_size", "int", True, "node count"),
                        P("edges", "list[tuple[int, int]]", True, "directed edge list"),
                        P("weights", "list", True, "parallel int metric"),
                        P("charges", "Optional[list[int | Q | float]]",
                          False, "parallel signed direction; None = undirected")),
            returns=R("dict",
                      "{ok, op, operand, responsion, curvature:{directed, "
                      "n_cycles, holonomy_nonzero, verdict}, diagnostics}"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.recover_check_structural", owner="srmech",
            category="laplacian",
            summary="The O(edges) integrity faculties only — operand (edges "
                    "present / valid) + a SAMPLED curvature read (a cheap "
                    "triangle probe) — so a directed Class-L store is integrity-"
                    "checkable at ANY vocab size (the dense op/responsion "
                    "faculties do not scale past the native n<=256 / O(n^3) wall). "
                    "The F1227 sparse peer of recover_check_spectral (#1390 item "
                    "4). numpy-free; no abs() (Class-K magnitude).",
            parameters=(P("vocab_size", "int", True, "node count"),
                        P("edges", "list[tuple[int, int]]", True, "directed edge list"),
                        P("weights", "list", True, "parallel int metric"),
                        P("charges", "Optional[list[int | Q | float]]",
                          False, "parallel signed direction; None = undirected"),
                        P("cycle_sample", "int", False,
                          "keyword-only; the triangle-probe budget (default 48)")),
            returns=R("dict",
                      "{operand, directed, curvature_sampled_nonzero, ok_structural}"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.recover_check_spectral", owner="srmech",
            category="laplacian",
            summary="The op + responsion (spectral) integrity faculties on a "
                    "BOUNDED principal submatrix — the first min(vocab_size, "
                    "max_dim) nodes + the edges within that block — so the dense "
                    "n×n eigendecompose stays within the native n<=256 wall at "
                    "ANY corpus vocab. The F1227 bounded-spectral peer of "
                    "recover_check_structural (#1390 item 4). numpy-free; no "
                    "abs().",
            parameters=(P("vocab_size", "int", True, "node count"),
                        P("edges", "list[tuple[int, int]]", True, "directed edge list"),
                        P("weights", "list", True, "parallel int metric"),
                        P("charges", "Optional[list[int | Q | float]]",
                          False, "parallel signed direction; None = undirected"),
                        P("max_dim", "int", False,
                          "keyword-only; the principal-submatrix bound (default 256)")),
            returns=R("dict", "{op, responsion, dim, diagnostics}"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.order_fingerprint", owner="srmech",
            category="laplacian",
            summary="The path-ORDERED octonion product along a walk — an "
                    "order-sensitive fingerprint of the fiber, 8 ints, "
                    "INDEPENDENT of walk length (#1390 item 4b; F1229/F1231; the "
                    "ℍ/𝕆 grade of the walk). It CATCHES a graph-preserving "
                    "reorder the op/operand/responsion/ℂ-curvature faculties are "
                    "BLIND to (two orders can share the identical directed graph, "
                    "F1079/F1230 — even the ℂ magnetic Laplacian passes both). A "
                    "VERIFIER (lossy by pigeonhole), NEVER a store. Composes the "
                    "C-routed qm.so8.octonion_mult_table (Cayley-Dickson "
                    "structure constants) with a GENERIC per-node octonion "
                    "(non-basis, non-uniform-component — basis units are "
                    "degenerate, F1230); EXACT integer products (no mod). "
                    "numpy-free; no abs().",
            parameters=(P("fiber_ids", "list", True,
                          "the walk = the ordered node-id sequence (the fiber)"),),
            returns=R("list", "the 8-int order fingerprint (length-independent)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.recover_check_order", owner="srmech",
            category="laplacian",
            summary="PASS (True) iff a recovered fiber reproduces the stored "
                    "order fingerprint (#1390 item 4b) — the order-integrity "
                    "guard on top of the graph faculties. Store order_fingerprint "
                    "of the true walk beside the genome; on recall recompute it "
                    "from the eulerian_path reconstruction and compare. A "
                    "mismatch flags an order corruption / F1079 graph-ambiguity "
                    "(the fiber must be stored explicitly) that op / operand / "
                    "responsion / ℂ-curvature all pass. numpy-free; no abs().",
            parameters=(P("true_fingerprint", "list", True,
                          "the stored order_fingerprint of the true walk"),
                        P("recovered_fiber_ids", "list", True,
                          "the recovered walk (node-id sequence) to verify")),
            returns=R("bool", "True iff the recovered order matches the stored fingerprint"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc108 (#1234 Item 2 / F1007) — the spectral theta / heat trace
        # + the ground-state flux reader, Class-L composites with the 1:1
        # C peers srmech_heat_trace / srmech_ground_state_flux_response.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.heat_trace", owner="srmech",
            category="laplacian",
            summary="The spectral theta / heat trace Θ(t) = Tr(e^{−tL}) = "
                    "Σₖ e^{−t·λₖ} of a Laplacian — a theta function of L (on "
                    "a cycle, the Jacobi-θ family) and the READ-INDEPENDENT "
                    "spectral summary (eigenvalue multiset only; no read "
                    "basis). Dispatches real-symmetric → jacobi_eigvals, "
                    "complex-Hermitian → hermitian_eigendecompose; ONE "
                    "eigensolve serves every t (pass a sequence of t values "
                    "for the cheap multi-t read). The exp is the Class-N Q61 "
                    "cascade (rational.exp / srmech_exp — libm-free) at the "
                    "spectral-summary boundary; Θ is a float summary, never "
                    "an exact decision. F1007: under magnetic flux the full "
                    "trace is flux-invariant (Poisson → the modular/"
                    "holomorphic part); the flux shadow lives only in the "
                    "ground state — see ground_state_flux_response. 1:1 C "
                    "peer srmech_heat_trace (native when present, pure-"
                    "Python the complete alternative). numpy-free; no abs().",
            parameters=(P("L", "Mat", True,
                          "an n×n real-symmetric or complex-Hermitian "
                          "Laplacian"),
                        P("t", "float | Sequence[float]", True,
                          "diffusion time(s); scalar → float, sequence → "
                          "Vec (one eigensolve, many t)")),
            returns=R("float | Vec", "Θ(t) — a float for scalar t, a real "
                                     "Vec (one Θ per t) for a sequence"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.ground_state_flux_response",
            owner="srmech",
            category="laplacian",
            summary="λ_min(Φ) — the magnetic ground state as a function of "
                    "flux: the F1007 SHADOW reader. The full heat trace of a "
                    "magnetic Laplacian is flux-invariant (the modular/"
                    "holomorphic part); the flux shadow lives ONLY in the "
                    "ground state (on a flux-threaded cycle λ_min moves 0 → "
                    "positive as Φ: 0 → 1/2 turn; periodic in integer flux — "
                    "integer holonomy is gauge-equivalent to none). Per flux "
                    "Φ each edge k gets charge Φ·charges[k] (the rc105 "
                    "chiral charges= pattern, composable as-is; default = "
                    "uniform 1/n_edges so a single cycle's total holonomy is "
                    "Φ turns), then magnetic_laplacian + "
                    "hermitian_eigendecompose → λ_min. 1:1 C peer "
                    "srmech_ground_state_flux_response (native when present, "
                    "pure-Python the complete alternative). numpy-free; no "
                    "abs().",
            parameters=(P("n", "int", True, "node count (>= 1)"),
                        P("edges", "list[tuple[int, int]]", True,
                          "directed u → v (the magnetic_laplacian "
                          "convention)"),
                        P("weights", "Optional[list[float]]", False,
                          "per-edge magnitudes; default 1.0 each"),
                        P("fluxes", "float | Sequence[float]", True,
                          "total flux value(s) in turns; scalar → float, "
                          "sequence → Vec"),
                        P("charges", "Optional[list[float]]", False,
                          "per-edge charge PATTERN (turns), parallel to "
                          "edges — scaled by each flux; default uniform "
                          "1/n_edges")),
            returns=R("float | Vec", "λ_min(Φ) — a float for scalar fluxes, "
                                     "a real Vec (one λ_min per Φ) for a "
                                     "sequence"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc136 (siona gh#1274) — EPH, the complex-time Wick-rotation
        # propagator harvest = e^{-zL}·u0 + the EPH cascade read, Class-L
        # composites with the 1:1 C peer srmech_eph_propagate.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.propagate", owner="srmech",
            category="laplacian",
            summary="EPH — the complex-time Wick-rotation propagator "
                    "harvest = e^{−zL}·u0 (siona gh#1274). The thermal "
                    "e^{−tL} and coherent e^{−itL} are NOT two ops — they are "
                    "the ONE complex-time propagator e^{−zL} with z COMPLEX, "
                    "the `i` being the WICK-ROTATION PHASE. arg(z) is the "
                    "coherence dial: z real → thermal diffusion (decoherent, "
                    "real damping), z imaginary → coherent unitary quantum "
                    "walk (‖harvest‖ = ‖u0‖ conserved), arg(z) BETWEEN → "
                    "PARTIAL coherence (z = t·e^{iφ} — the regime only the "
                    "unified form can name). RBS-SNN = EPH-with-a-synaptic-"
                    "propagator (P = connectome/weight matrix); no privileged "
                    "instance. ONE eigensolve → project c = V^H·u0 → per-mode "
                    "scale c_k·e^{−z·λ_k} → recombine V·(scaled c). The "
                    "per-mode scalar e^{−zλ_k} = e^{−Re(z)·λ_k}·(cos(Im(z)·"
                    "λ_k) − i·sin(Im(z)·λ_k)) uses the Class-N exp/cos/sin "
                    "series with the MANDATORY 2π SEAM-FOLD of the oscillation "
                    "argument (Machin-2π = 32·atan(1/5) − 8·atan(1/239)) — "
                    "the raw trig series blow up past a convergence radius; "
                    "the fold keeps propagate EXACT at any t·λ. Composes the "
                    "Class-L Wick rotation (signed-Laplacian variant). 1:1 C "
                    "peer srmech_eph_propagate (native when present, pure-"
                    "Python the complete alternative; harvest is basis-"
                    "invariant → Python == C to the eigensolve tolerance). "
                    "numpy-free; no abs() (Class-K magnitude / Class-C sign).",
            parameters=(P("L", "Mat", True,
                          "an n×n real-symmetric or complex-Hermitian "
                          "Laplacian / operator"),
                        P("u0", "Vec", True,
                          "the excitation vector (length n, real or complex) "
                          "— the seed the propagator acts on"),
                        P("z", "complex", True,
                          "the complex time z = Re(z) + i·Im(z); arg(z) is "
                          "the coherence dial (real → thermal, imaginary → "
                          "coherent, between → partial)")),
            returns=R("Vec", "the harvest e^{−zL}·u0 — a length-n complex Vec "
                             "(the coherent/partial part is genuinely "
                             "complex)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.eph_harvest", owner="srmech",
            category="laplacian",
            summary="The EPH cascade read (siona gh#1274) — excite → "
                    "propagate → Born-rule harvest-rank the reaction center. "
                    "A composition op: excite (seed u0 — Class-M grounding, "
                    "content-neutral) → propagate (harvest = e^{−zL}·u0 with "
                    "the arg(z) coherence dial) → the Born-rule harvest "
                    "|harvest_i|² per node (the reaction-center energy; energy "
                    "= relevance) → rank the nodes by energy. Returns the "
                    "ranked node indices + per-node energies + the reaction "
                    "center + the total energy (= the coherence budget: "
                    "conserved in the coherent limit, damped below it in the "
                    "thermal limit — the monotonic Wick dial) + the raw "
                    "complex harvest. The neuron is one propagator choice "
                    "(RBS-SNN); this is the generic retrieval / inference "
                    "cascade one layer up. Composes propagate (c_dispatched) "
                    "+ the Born magnitude + rank — no new C symbol. numpy-"
                    "free; no abs().",
            parameters=(P("L", "Mat", True,
                          "an n×n real-symmetric or complex-Hermitian "
                          "Laplacian / operator"),
                        P("u0", "Vec", True,
                          "the excitation vector (length n, real or complex)"),
                        P("z", "complex", True,
                          "the complex time / coherence dial (as propagate)")),
            returns=R("dict", "ranked_nodes / energies / reaction_center / "
                              "total_energy / harvest_re / harvest_im "
                              "(JSON-native)"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc206 (siona gh#1274 item 1c) — the SPARSE-SCALED EPH
        # propagator: the corpus-scale residual, Class-L with the 1:1 C
        # peer srmech_eph_propagate_sparse.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.propagate_sparse", owner="srmech",
            category="laplacian",
            summary="EPH SPARSE — the sparse-scaled propagator harvest = "
                    "e^{−zL}·u0 (siona gh#1274 item 1c, the corpus-scale "
                    "residual). The SAME harvest as propagate (same complex-z "
                    "convention, same arg(z) coherence dial: z real → thermal, "
                    "z imaginary → coherent, between → partial; same "
                    "seam-folded Wick factor) computed by a CHEBYSHEV "
                    "polynomial of the operator applied with MATRIX-VECTOR "
                    "PRODUCTS ONLY — no eigendecomposition, no dense e^{−zL} "
                    "— so it runs on a corpus-scale L past the n ≤ 256 "
                    "dense-eigensolve cap (O(m·n_edges) time, O(n) memory, m "
                    "= the Chebyshev degree). The operator is the SIGNED "
                    "graph Laplacian read off the edge list (the "
                    "signed_laplacian / fiedler_sparse sparse-input "
                    "convention; deg = Σ|w| by Class-K sign branch, never "
                    "abs(); self-loops skipped; duplicate edges read "
                    "per-edge). Spectral interval [0, 2·max deg] by "
                    "Gershgorin (deterministic), affine-mapped to [−1, 1]; "
                    "Chebyshev coefficients of e^{−z·λ(s)} from the Chebyshev "
                    "nodes (the rc136 Wick machinery — Class-N exp + the "
                    "MANDATORY Machin-2π seam-folded cos/sin), node count "
                    "adaptively doubled 64 → the HARD CAP max_degree+1, "
                    "accepted when the coefficient tail (top eighth) falls "
                    "below tol·max|e^{−z·λ}|; then the forward T_{k+1} = "
                    "2·L̃·T_k − T_{k−1} vector recurrence (‖T_k‖ ≤ 1 → "
                    "stable). Not converged within max_degree → an HONEST "
                    "ValueError (raise max_degree or shrink |z|), never a "
                    "silently degraded tolerance. 1:1 C peer "
                    "srmech_eph_propagate_sparse (native when present, "
                    "pure-Python the complete alternative — same algorithm, "
                    "same accumulation order, within-tol parity). numpy-free; "
                    "no abs().",
            parameters=(P("n", "int", True, "number of graph nodes"),
                        P("edges", "list[tuple[int, int]]", True,
                          "undirected edges (u, v), 0 ≤ u, v < n (the "
                          "fiedler_sparse / signed_laplacian convention)"),
                        P("weights", "Optional[list[float]]", False,
                          "per-edge weights (default all 1.0); may be "
                          "negative — the signed degree keeps L PSD"),
                        P("u0", "Vec", True,
                          "the excitation vector (length n, real or complex) "
                          "— the seed the propagator acts on (keyword-only)"),
                        P("z", "complex", True,
                          "the complex time; arg(z) is the coherence dial "
                          "(as propagate; keyword-only)"),
                        P("tol", "float", False,
                          "relative coefficient-tail tolerance (default "
                          "1e-10)"),
                        P("max_degree", "int", False,
                          "the HARD Chebyshev degree cap, 1..2^28 (default "
                          "2048 — covers |z|·λ_max up to ~4000)")),
            returns=R("Vec", "the harvest e^{−zL}·u0 — a length-n complex Vec "
                             "(the propagate return contract)"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc207 (siona gh#1276) — the WOUND EPH propagator: the 2π
        # seam-fold's divmod quotient KEPT (the #741 mod-should-be-
        # divmod audit's first concrete instance), Class-L with the 1:1
        # C peer srmech_eph_propagate_wound.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.propagate_wound", owner="srmech",
            category="laplacian",
            summary="EPH WOUND — propagate with the 2π seam-fold's DIVMOD "
                    "quotient KEPT (siona gh#1276; the #741 mod-should-be-"
                    "divmod audit's first concrete instance). propagate's "
                    "mandatory seam-fold argument-reduces each per-mode "
                    "oscillation argument Im(z)·λ_k modulo 2π; that fold IS "
                    "a divmod — quotient w_k = round(Im(z)·λ_k / 2π) = the "
                    "METACYCLE winding (the whole 2π turns propagate throws "
                    "away, the mod-collapse), remainder θ_k = the EPICYCLE "
                    "residue (|θ| ≤ π, what propagate keeps). "
                    "propagate_wound keeps the GRADING: BOTH harvests at "
                    "the seam, from the SAME fold (the exact Machin-2π "
                    "divmod pure / the Q61 2/π quarter-turn machinery "
                    "native — no forked 2π constant). Carrying w does NOT "
                    "perturb the epicycle harvest — byte-identical to "
                    "propagate at the same dispatch tier (same cascade, "
                    "same order). The readout is the One's the_one(σ, θ, w) "
                    "CRANK vocabulary per mode (the winding fills the fast "
                    "metacycle dial as the triad (w_k, 0, 0)): winding = "
                    "the whole-ℤ metacycle turns (never % 2); theta = the "
                    "epicycle phase, with 2π·w_k + θ_k reconstructing "
                    "Im(z)·λ_k LOSSLESSLY on the fold grid (the "
                    "One.unwrapped_phase reconstruction); sigma_effective = "
                    "the tower-graded chirality dial ±1 via the winding's "
                    "divmod binary tower (the EXISTING One.sigma_effective "
                    "readout — NOT the melding bare w mod 2; w=5 and w=7 "
                    "are DISTINGUISHED); spinor_sign = the double-cover "
                    "(−1)^{w_k} (the EXISTING One.spinor_sign readout). 1:1 "
                    "C peer srmech_eph_propagate_wound (ONE native call: "
                    "the srmech_eph_propagate cascade + srmech_winding_fold "
                    "+ the existing srmech_sigma_effective / "
                    "srmech_spinor_sign winding peers per mode); pure "
                    "Python the complete alternative. numpy-free; no "
                    "abs().",
            parameters=(P("L", "Mat", True,
                          "(n, n) real-symmetric or complex-Hermitian "
                          "operator (as propagate)"),
                        P("u0", "Vec", True,
                          "the excitation vector (length n, real or "
                          "complex) — the seed the propagator acts on"),
                        P("z", "complex", True,
                          "the complex time; arg(z) is the coherence dial "
                          "(as propagate)")),
            returns=R("dict", "JSON-native, per-mode arrays in eigensolve "
                              "mode order: harvest_re / harvest_im (the "
                              "epicycle harvest, byte-identical to "
                              "propagate) / eigenvalues / winding (the "
                              "metacycle turns, int) / theta (the folded "
                              "epicycle residue, |θ| ≤ π) / sigma_effective "
                              "(±1, tower-graded) / spinor_sign (±1, "
                              "double-cover)"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc208 (F1186) — RESPONSION, the response-function family of a
        # generator L on an excitation u0: the op⊗operand⊗responsion
        # k=3 completion (the stored relationship itself), Class-L with
        # the 1:1 C peer srmech_responsion.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.responsion", owner="srmech",
            category="laplacian",
            summary="RESPONSION — the response-function family of a "
                    "generator L acting on an excitation u0 (F1186: the "
                    "op⊗operand⊗responsion k=3 completion — the "
                    "answering-correspondence between successive "
                    "op-on-operand applications, the stored relationship "
                    "itself; srmech = Stored-RELATIONSHIP Mechanism). "
                    "Generalizes EPH's e^{−zL} to the general response "
                    "function; the two canonical continuous-form members "
                    "are LAPLACE-TRANSFORM DUALS: kind='propagator' (time "
                    "domain) = e^{−zL}·u0 — DELEGATES verbatim to the "
                    "shipped propagate (rc136; same arg(z) coherence dial, "
                    "same mandatory 2π seam-fold — responsion SUBSUMES "
                    "propagate as its time-domain member, propagate stays "
                    "the named EPH surface); kind='resolvent' (frequency/"
                    "energy domain, the Green's function) = (zI−L)^{−1}·u0 "
                    "— NEW: the Laplace transform of the semigroup "
                    "propagator, (zI−L)^{−1} = ∫₀^∞ e^{−zt}·e^{tL} dt for "
                    "Re z > max λ(L), per eigenmode the dual pair "
                    "e^{−z·λ} ⟷ 1/(z−λ). Realised as a REAL complex "
                    "linear solve via the real 2n×2n block embedding "
                    "[[Aᵣ,−Aᵢ],[Aᵢ,Aᵣ]] over the shipped Gauss–Jordan "
                    "kernel. z exactly in spec(L) is a resolvent POLE and "
                    "raises ZeroDivisionError honestly (the pole IS the "
                    "physics). 1:1 C peer srmech_responsion (kind 0 "
                    "delegates to srmech_eph_propagate; kind 1 composes "
                    "srmech_dense_solve_f64_ws — a bare-C host runs BOTH "
                    "members); pure Python the complete alternative (the "
                    "SAME embedding via mat_solve). numpy-free; no abs() "
                    "(z−L is Class-C signed arithmetic; the solve pivot "
                    "is the composed kernel's Class-K sign branch).",
            parameters=(P("L", "Mat", True,
                          "an n×n real-symmetric or complex-Hermitian "
                          "operator (as propagate)"),
                        P("u0", "Vec", True,
                          "the excitation vector (length n, real or "
                          "complex) — the seed the response acts on"),
                        P("z", "complex", True,
                          "the complex argument: the complex time for the "
                          "propagator (arg(z) = the coherence dial), the "
                          "complex frequency/energy for the resolvent "
                          "(poles at spec(L))"),
                        P("kind", "str", False,
                          "'propagator' (default; e^{−zL}·u0, delegates "
                          "to propagate) or 'resolvent' ((zI−L)^{−1}·u0, "
                          "the Laplace-dual Green's function; "
                          "keyword-only)")),
            returns=R("Vec", "the response — a length-n complex Vec (the "
                             "propagate return contract)"),
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
        # §51 (issue #1097): the SPARSE / iterative normalized-cut Fiedler —
        # the n-unbounded peer of fiedler_vector. Native standalone-C matvec
        # power iteration; breaks the n≤256 dense-eig wall for graph partition.
        ToolEntry(
            name="srmech.amsc.laplacian.fiedler_sparse", owner="srmech",
            category="laplacian",
            summary="Sparse / iterative normalized-cut Fiedler vector — the "
                    "n-unbounded peer of fiedler_vector (issue #1097, §51). "
                    "Power iteration on B = I + D^-1/2 W D^-1/2 (= 2I - L_sym, "
                    "eigenvalues in [0,2]) deflating the √deg λ₀ mode; the "
                    "converged direction's SIGN is the normalized-cut bisection. "
                    "Matvec-only (O(edges), n unbounded) — breaks the n≤256 "
                    "dense-eig wall for corpus-scale graph partitioning (spectral "
                    "clumping). Native standalone-C (caller-arena, no caps); "
                    "pure-Python is the complete alternative.",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False),
                        P("max_iters", "int", False,
                          "power-iteration cap (default 250; sign-stability "
                          "usually stops earlier)")),
            returns=R("Vec", "length-n sign-bearing Fiedler vector (numpy-free "
                             "1-D carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.normalized_cut_bisect", owner="srmech",
            category="laplacian",
            summary="Sparse normalized-cut bisection: split the nodes by the "
                    "sign of fiedler_sparse (issue #1097, §51). Returns "
                    "(left, right) node-index lists (left = negative-sign). The "
                    "O(edges), n-unbounded recursion primitive for spectral "
                    "clumping — bisect, then recurse on each side. A composition "
                    "of fiedler_sparse + a Class-K sign split.",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False),
                        P("max_iters", "int", False)),
            returns=R("tuple[list[int], list[int]]",
                      "(left, right) node-index partition"),
        ),
        # §52 Part 2 (F793): the OUT-OF-CORE streaming Fiedler + its on-disk graph
        # writer. The bounded edge SET (cooccurrence_topk) is written to a packed
        # file, and the partition streams it — so the partition's RAM is bounded
        # the way the edge set is, for a fully low-RAM corpus-scale encode.
        ToolEntry(
            name="srmech.amsc.laplacian.write_packed_graph", owner="srmech",
            category="laplacian",
            summary="Write a packed binary edge file for the out-of-core "
                    "streaming Fiedler (§52 Part 2, F793) — one 16-byte record "
                    "per edge (uint32 u | uint32 v | double w, host byte order). "
                    "The on-disk adjacency fiedler_sparse_file (and the recursive "
                    "out-of-core driver) reads; the edge list lives on DISK, never "
                    "fully resident, so a low-RAM target can build + partition a "
                    "corpus-scale co-occurrence graph. Streams rows out as it goes "
                    "(peak RAM = one chunk). Returns the edge-record count.",
            parameters=(P("path", "str", True,
                          "destination file (overwritten)"),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False)),
            returns=R("int", "number of edge records written"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.fiedler_sparse_file", owner="srmech",
            category="laplacian",
            summary="Out-of-core sparse normalized-cut Fiedler — the streaming "
                    "peer of fiedler_sparse that reads its adjacency from a packed "
                    "edge FILE (§52 Part 2, F793). Identical power iteration (so "
                    "the result equals fiedler_sparse on the same graph), but the "
                    "edges NEVER become resident: each matvec streams the file via "
                    "the PAL, so only the O(n) working vectors are in RAM — a "
                    "low-RAM target can partition a graph whose edge list exceeds "
                    "RAM (the low-RAM ENCODE for graph partition; composes §52.1 "
                    "cooccurrence_topk). Native standalone-C streaming when "
                    "HAS_NATIVE (the bounded path); the no-C path reads the file "
                    "in + runs the in-RAM cascade (correct, not bounded).",
            parameters=(P("n", "int", True),
                        P("graph_path", "str", True,
                          "packed edge file written by write_packed_graph"),
                        P("max_iters", "int", False,
                          "power-iteration cap (default 250)")),
            returns=R("Vec", "length-n sign-bearing Fiedler vector (numpy-free "
                             "1-D carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.recursive_cut", owner="srmech",
            category="laplacian",
            summary="Out-of-core recursive spectral partition into community "
                    "TOMES (§52 Part 2, F793) — the same recursion as bisecting "
                    "with normalized_cut_bisect and recursing on each side, but "
                    "executed OUT-OF-CORE: the adjacency, every pending sub-graph, "
                    "and every finished tome live on DISK, so peak RAM is the "
                    "single largest sub-graph being bisected (the top-level O(n) "
                    "working vectors), not the whole structure. A disk-backed work "
                    "queue drives the recursion; each step streams its sub-graph's "
                    "induced edges (relabelled) through fiedler_sparse_file and "
                    "recurses until |S| ≤ max_tome. A composition of "
                    "fiedler_sparse_file (C-dispatched) + write_packed_graph + the "
                    "disk-spilled recursion. Returns the tome node-sets + their "
                    "on-disk paths + the work_dir + a status key. §101 (rc275): an "
                    "in-process progress= callable (a Python-only kwarg, NOT an MCP "
                    "wire param) fires a per-bisection heartbeat + graceful abort — a "
                    "truthy return CANCELS and returns the clean partial partition "
                    "(status 'cancelled').",
            parameters=(P("n", "int", True),
                        P("edges", "list[tuple[int, int]]", True),
                        P("weights", "Optional[list[float]]", False),
                        P("max_tome", "int", False,
                          "a sub-graph with ≤ max_tome nodes is a leaf tome "
                          "(default 256)")),
            returns=R("dict",
                      "{n_tomes, tome_paths, tomes, work_dir} — the community "
                      "partition (tomes = node-id lists; tome_paths on disk)"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.jacobi_eigvals", owner="srmech",
            category="laplacian",
            summary="Symmetric Jacobi eigendecomposition; pi-free closed-form "
                    "c/s computation. Native C dispatch when n ≤ 256.",
            parameters=(P("matrix", "Mat", True, "n × n symmetric"),
                        P("max_sweeps", "int", False, "default 100"),
                        P("tolerance", "float", False),
                        P("exact", "bool", False,
                          "exact eigvals_exact route for integer/rational "
                          "symmetric input (default float-Jacobi)")),
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
            returns=R("Mat | Vec | list[list[Q]] | list[Q]",
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
            returns=R("Mat | list[list[Q]]",
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
            returns=R("Mat | list[list[Q]]",
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
                    "foundation #4): radix-2 balancing, Householder reduction to "
                    "upper-Hessenberg form, then a Wilkinson-shifted QR iteration "
                    "with EISPACK exceptional shifts on the active block; n=1/2 "
                    "closed form. Native-dispatched to srmech_mat_eigvals_ws "
                    "(rc299) — the whole-op C peer, so a bare-C host runs this "
                    "too; the pure sweep is the complete fallback. NUMERIC "
                    "(FPU-tol) parity: bit-exact against the pure projection on "
                    "real symmetric input, ~1e-14 relative on general complex "
                    "(the one divergence is the exact-rational vs scaled-float "
                    "modulus). Multiset matches NumPy eigvals to ~1e-9. Prefer "
                    "mat_hermitian_eigendecompose for Hermitian A. Golub & Van "
                    "Loan §7.4.3 + §7.5 + §7.5.1.",
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
        ToolEntry(
            name="srmech.amsc.primes.next_prime", owner="srmech", category="primes",
            summary="The prime successor (Class J): the smallest prime strictly "
                    "greater than n. Trial-division primality (cf. Crandall & "
                    "Pomerance, *Prime Numbers: A Computational Perspective*, 2nd "
                    "ed. 2005, §1.3) walked over the odd candidates above n; 0/1 "
                    "step to 2 and 2 steps to 3. Used by the rc44 CRT re-fibration "
                    "arc to enumerate the GF(p) reduction primes. 1:1 C peer "
                    "srmech_next_prime (native when present; pure-Python complete). "
                    "Exact integer; no float, no abs(), no numpy / math.",
            parameters=(P("n", "int", True, "non-negative integer"),),
            returns=R("int", "the smallest prime > n"),
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
        # ────────────────────────────────────────────────────────────
        # rc204 (gh#1324 / F1167–F1169) — the spectral SPINE + the
        # relational-structure sugar, the DOMINANT-mode read-out that
        # completes the community/spine pair with the LOW-mode
        # fiedler_sparse / three_fold_eigvec_groups. C peer
        # srmech_spectral_spine.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.laplacian.spectral_spine", owner="srmech",
            category="laplacian",
            summary="The spectral SPINE of a relational graph: the top-|component| "
                    "nodes of the DOMINANT (largest-λ) eigenvector of the (signed) "
                    "Laplacian L = D̄ − A. The largest-eigenvalue eigenvector "
                    "concentrates on the structurally CENTRAL items, so its "
                    "top-magnitude nodes ARE the spine — the dominant-mode "
                    "read-out that completes the community/spine PAIR with the "
                    "LOW-mode fiedler_vector / fiedler_sparse (2-way) + "
                    "three_fold_eigvec_groups (3-way). Domain-free (edges = any "
                    "relational graph: siona describe-spine, ephemerides central "
                    "bodies). n is inferred as one past the largest endpoint. "
                    "Ranking is Class-K |component|² (re²+im², no abs / no sqrt), "
                    "descending, ties by ascending index. 1:1 C peer "
                    "srmech_spectral_spine (native when present, pure-Python — "
                    "signed_laplacian + symmetric_eigendecompose + top-k — the "
                    "complete alternative). NUMERIC within-tol native==pure; "
                    "numpy-free; no abs().",
            parameters=(P("edges", "list[tuple[int, int]]", True,
                          "undirected relational edges; n inferred from endpoints"),
                        P("weights", "Optional[list[float]]", False,
                          "per-edge weights (default 1.0); may be negative"),
                        P("k", "int", False,
                          "spine cap (keyword-only; default 8); returns "
                          "min(k, n) indices")),
            returns=R("list[int]", "up to k central node indices, descending "
                                   "|component| of the dominant eigenvector"),
        ),
        ToolEntry(
            name="srmech.amsc.laplacian.relational_structure", owner="srmech",
            category="laplacian",
            summary="The full spectral structure of a relational graph in ONE "
                    "call: {spine, communities, coherence} from a single "
                    "eigendecomposition of the (signed) Laplacian. spine = the "
                    "top-8 central nodes (the DOMINANT mode, spectral_spine); "
                    "communities = [left, right] the Fiedler 2-way sign bisection "
                    "(the LOW mode, the normalized_cut_bisect convention — a "
                    "Class-K sign split); coherence = λ₂ the algebraic "
                    "connectivity (small ⇒ near-disconnected). Ergonomic sugar "
                    "that COMPOSES signed_laplacian + symmetric_eigendecompose + "
                    "the spectral_spine top-k + the Fiedler sign split (no "
                    "dedicated C symbol — a pure composition of the C-backed "
                    "atoms). numpy-free; no abs().",
            parameters=(P("edges", "list[tuple[int, int]]", True,
                          "undirected relational edges; n inferred from endpoints"),
                        P("weights", "Optional[list[float]]", False,
                          "per-edge weights (default 1.0); may be negative")),
            returns=R("dict", "{spine: list[int], communities: [list[int], "
                              "list[int]], coherence: float}"),
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
                    "p/q via continued-fraction convergents (Stern-Brocot path). "
                    "Inputs are non-negative ints with NO uint64 ceiling (#898): "
                    "u64-fit inputs take the fast native path (byte-identical to "
                    "the pure walk); a bignum coordinate (> 2**64 — e.g. an exact "
                    "Class-N log anchor) carries Python bigints, bounded only by "
                    "max_denominator (Lamé caps the CF depth). with_path=True ALSO "
                    "emits the Stern-Brocot / continued-fraction partial-quotient "
                    "path (the Class-N approximation holonomy) whose landing "
                    "convergent equals (p', q') — the walk was always computed and, "
                    "before rc336, discarded.",
            parameters=(P("numerator", "int", True, "≥ 0; arbitrary magnitude"),
                        P("denominator", "int", True, "> 0; arbitrary magnitude"),
                        P("max_denominator", "int", True, "> 0; arbitrary magnitude"),
                        P("with_path", "bool", False, "keyword-only (rc336); default "
                          "False → the pinned (p', q') 2-tuple. True → ALSO return "
                          "the compact CF [a_0, a_1, ...] of the accepted convergents "
                          "(the RLE of the Stern-Brocot L/R mediant walk = the Class-N "
                          "approximation holonomy)")),
            returns=R("tuple[int, int] | tuple[int, int, list[int]]",
                      "(p', q') — or (p', q', path) when with_path=True, path = the "
                      "CF partial quotients, whose folded convergent is (p', q')"),
        ),
        # ────────────────────────────────────────────────────────────
        # Class N — rational reconstruction (rc45, rung 2 of the
        # CRT-QMat re-fibration arc). The residue→bounded-p/q closer.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.rational.rational_reconstruct", owner="srmech",
            category="rational",
            summary="Recover the rational p/q congruent to a residue modulo M — "
                    "rational reconstruction (cf. Wang 1981, *An improved Monte "
                    "Carlo algorithm for computing exact rational solutions*; von "
                    "zur Gathen & Gerhard, *Modern Computer Algebra*, 3rd ed. 2013, "
                    "§5.10). The Class-N closer of the rc45 CRT re-fibration: after "
                    "crt_combine merges the per-prime residues into one residue mod "
                    "M, this recovers the exact rational answer. Returns the reduced "
                    "SIGNED (p, q) with p/q ≡ residue (mod M), |p| ≤ num_bound, "
                    "0 < q ≤ den_bound, gcd(q, M) == 1, gcd(|p|, q) == 1 — or None "
                    "if no such rational exists in the bounds. The default symmetric "
                    "bound num_bound = den_bound = isqrt(M // 2) is the standard Wang "
                    "bound guaranteeing uniqueness. Half-GCD / extended-Euclidean "
                    "reconstruction (the best_rational / continued_fraction Class-N "
                    "family, but the distinct residue→bounded-p/q algorithm); sign "
                    "is Class-K (an explicit sign-branch, never abs()); arbitrary-"
                    "precision / bignum (M and p/q may exceed 2**64); no float, no "
                    "numpy / math. 1:1 C peer srmech_rational_reconstruct (over "
                    "srmech_bigint, caller-arena; native when present, pure-Python "
                    "the complete alternative).",
            parameters=(P("residue", "int", True,
                          "the residue r (reduced into [0, M) internally)"),
                        P("modulus", "int", True, "the modulus M >= 2"),
                        P("num_bound", "Optional[int]", False,
                          "|p| ceiling; default isqrt(M // 2) (the Wang bound)"),
                        P("den_bound", "Optional[int]", False,
                          "q ceiling; default isqrt(M // 2) (the Wang bound)")),
            returns=R("Optional[tuple[int, int]]",
                      "the reduced signed (p, q), or None if no rational fits the "
                      "bounds"),
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
            name="srmech.amsc.rational.jacobi_sncndn_series_truncate",
            owner="srmech", category="rational",
            summary="Jacobi elliptic sn/cn/dn Maclaurin partial sums at u=p/q, modulus m=m_p/m_q, as a triple of exact rationals. Coeffs from the coupled ODE sn'=cn*dn, cn'=-sn*dn, dn'=-m*sn*cn (Abramowitz & Stegun §16.4). Rotation-last exact-Q sibling of sin/cos_series_truncate: sn^2+cn^2=1 and dn^2+m*sn^2=1 hold exactly; m=0 -> sin/cos, m=1 -> tanh/sech. Class N + Class J + Class I (sign) composition; native C peer srmech_jacobi_sncndn; Python bignum-capable.",
            parameters=(P("numerator", "int", True, "p of u = p/q"),
                        P("denominator", "int", True, "q of u = p/q (must be > 0)"),
                        P("m_numerator", "int", True, "m_p of modulus m = m_p/m_q"),
                        P("m_denominator", "int", True, "m_q of m (must be > 0)"),
                        P("num_terms", "int", True, "truncation N, 0 <= N <= 50")),
            returns=R("tuple[tuple[int, int], tuple[int, int], tuple[int, int]]",
                      "((sn_num, sn_den), (cn_num, cn_den), (dn_num, dn_den)) reduced"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.relative_writhe", owner="srmech", category="rational",
            summary="rc317 (#1308) — Fuller's Second-Theorem exact-rational RELATIVE WRITHE Wr(C)-Wr(C0), the single-integral peer of the O(n^2) discrete_writhe double sum. Given two closed polygonal curves as EXACT-RATIONAL 3D vertices (int / Fraction / (num,den) per coord; floats rejected), reference=C0 (base) and embedding=C (deformed), it evaluates Fuller's single integral (1/2pi) oint (t0 x t).d(t0+t)/(1+t0.t) ds over the closed polygon, t0/t the central-difference UNIT tangents. CERTIFIED TRUNCATION, NOT the exact writhe: the true relative writhe is generically TRANSCENDENTAL (the pi normalisation + irrational unit-tangent lengths), so it returns an EXACT rational + a STATED remainder_bound on |value-true| — a Class-N best_rational anchor across the writhe's inharmonic responsion seam (F1308). DUAL-PRECISION contract (rc317 PILOT): precision=None -> PLATFORM-BOUNDED (value's num/den ride a native int64 word; the fast hardware-last-mile read; FLOAT-FREE, a bounded rational); precision=P int -> SRMECH-NATIVE BIGINT lengthed by P (remainder_bound ~ 2^-P tightening MONOTONICALLY; the bigint num/den lengthen with P). The +/-2 obstruction (antipodal_events flags the near-antipodal band 1+t0.t < 2^-4; for TRUE unit tangents 1+t0.t in [0,2], =0 only at the exact measure-zero antipode, so the literal <=0 the float spike reads via FP rounding is degenerate under exact rationals) IS the SAME Z->>Z/2 (kernel 2Z) reduction cwf_consistency_mod2 reads via the Q8 center-parity — the SO(3)/SU(2) double cover, a writhe +/-2 vs a spinor sign (DERIVED/argued; the integer lift needs the O(n^2) discrete_writhe). Class N (rational sqrt / pi-cascade / best_rational) . Class K (sign-branch magnitudes + antipodal pole detection, never abs()) . Class I (cyclic wrap); float NOWHERE (atan2 excluded — it projects to float; atan_series_truncate's angle reformulation is a different discretisation). composition_of_c (sqrt/pi/best_rational are C-backed): NO new C symbol, ABI stays 10, GENOME_FORMAT_VERSION stays 16 (a pure geometry READ). CAD-ban-clear: closed-form on the integer ALU, NOT mesh/FEA/GPU. Cites F. Brock Fuller PNAS 68(4):815-819 (1971, doi 10.1073/pnas.68.4.815, PMC389050) + PNAS 75(8):3557-3561 (1978, doi 10.1073/pnas.75.8.3557, PMC392823), both OA.",
            parameters=(P("embedding", "list", True, "the deformed curve C — vertices [(x,y,z), ...]; each coordinate an int / fractions.Fraction / (num,den) integer pair (exact rational — floats rejected)"),
                        P("reference", "list", True, "the base curve C0 — SAME vertex count as embedding (Fuller's integral pairs t0_i with t_i by index)"),
                        P("closed", "bool", False, "keyword-only; True (default) wraps the polygon (central-difference tangents with the P[n-1]<->P[0] closure); False = an open polyline"),
                        P("precision", "int", False, "keyword-only; None (default) -> the platform-bounded projection; a positive int P -> the srmech-native bigint projection lengthed by P")),
            returns=R("dict", "{value:(num,den) the relative writhe in turns, remainder_bound:(num,den) stated bound on |value-true|, mode:'platform'|'bigint', precision:int effective bits, antipodal_events:int (steps in the near-antipodal band, the +/-2-obstruction flag), min_one_plus_dot:(num,den) the closest antiparallel approach}"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.cos", owner="srmech", category="rational",
            summary="cos(x) (radians) via the Class-N rational cascade: range-reduce into [-π, π] with the π-cascade rational, cos Taylor partial sum, returning the EXACT rational Q (the integer-ALU value; float(q) projects to the FPU at the display edge). Substrate-native replacement for math.cos / np.cos (no math.cos in the call graph); float(q) matches libm to ~1e-15.",
            parameters=(P("x", "float", True, "angle in radians"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("Q", "cos(x) as an exact rational (Class-N Q carrier); float(q) projects at the display edge"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.sin", owner="srmech", category="rational",
            summary="sin(x) (radians) via the Class-N rational cascade (π-cascade range reduction + sin Taylor, returned as an EXACT rational Q). Substrate-native replacement for math.sin / np.sin; float(q) matches libm to ~1e-15.",
            parameters=(P("x", "float", True, "angle in radians"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("Q", "sin(x) as an exact rational (Class-N Q carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.tan", owner="srmech", category="rational",
            summary="tan(x) = sin(x)/cos(x) via the Class-N rational cascade (raises if cos(x) == 0). Substrate-native replacement for math.tan / np.tan.",
            parameters=(P("x", "float", True, "angle in radians"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("Q", "tan(x) = sin/cos as an exact rational (Class-N Q carrier)"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.atan", owner="srmech", category="rational",
            summary="atan(x) via the Class-N atan cascade with three-band argument reduction (√2∓1 edges → every series argument |·|<=√2−1; Class-K magnitude, no abs()). Substrate-native replacement for math.atan / np.arctan; machine-ε accurate.",
            parameters=(P("x", "float", True, "argument"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("Q", "atan(x) as an exact rational (Class-N Q carrier) in (-π/2, π/2)"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.atan2", owner="srmech", category="rational",
            summary="atan2(y, x) via the Class-N atan cascade with full quadrant logic. Substrate-native replacement for math.atan2 / np.arctan2; machine-ε accurate.",
            parameters=(P("y", "float", True, "ordinate"),
                        P("x", "float", True, "abscissa"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("Q", "atan2(y, x) as an exact rational (Class-N Q carrier) in (-π, π]"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.exp", owner="srmech", category="rational",
            summary="e^x (real) via the Q61 Class-N exp cascade with Cody-Waite ln2 reduction (x = n*ln2 + r, |r| <= ln2/2; exp(r) the Q61 integer Taylor, 2^n folded in as an EXACT power-of-two scale → an exact rational Q, no float-collapsed recombine and no DBL_MAX overflow gate). Bit-exact with the native peer srmech_exp_q61; dispatches to C when available. Substrate-native replacement for math.exp / np.exp (real).",
            parameters=(P("x", "float", True, "real exponent"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("Q", "e^x as an exact rational (Class-N Q carrier) from the Q61 cascade"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.log", owner="srmech", category="rational",
            summary="ln(x) (natural log, x > 0) via the Q61 Class-N atanh cascade: x = m*2^e read from the bit pattern, m folded into [1/sqrt2, sqrt2), log(m) = 2*atanh((m-1)/(m+1)) the Q61 series, e*ln2 recombined exactly in the Q61 model → an exact rational Q. Bit-exact with the native peer srmech_log_q61; dispatches to C when available. Domain: x <= 0 raises ValueError (log 0 = -Inf is not a rational); non-finite raises. Substrate-native replacement for math.log / np.log (real).",
            parameters=(P("x", "float", True, "argument, x > 0"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("Q", "ln(x) as an exact rational (Class-N Q carrier) from the Q61 cascade"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.cexp", owner="srmech", category="rational",
            summary="e^(i*theta) = cos(theta) + i*sin(theta) via the Class-N cascade (Euler). Class-N trig composed with Class-C imaginary-unit rotation — the DFT twiddle factor and the quantum time-evolution phase. Substrate-native replacement for np.exp / cmath.exp of 1j*theta.",
            parameters=(P("theta", "float", True, "phase angle in radians"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("complex", "e^(i*theta) on the unit circle"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.complex_exp", owner="srmech", category="rational",
            summary="e^z for complex z = e^(z.real)*(cos(z.imag) + i*sin(z.imag)) via the Class-N cascade. Class-N exp + trig composed with Class-C i-rotation. Substrate-native replacement for np.exp / cmath.exp on a complex argument.",
            parameters=(P("z", "complex", True, "complex exponent"),
                        P("precision", "int", False, "None (default) = the Q61 fast path, byte-identical to prior rcs; P>=1 = the exact-rational reference at P fractional bits, error < 2**-P (keyword-only)")),
            returns=R("complex", "e^z projected from the exact rational"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.sqrt", owner="srmech", category="rational",
            summary="sqrt(x) for x >= 0 via the Class-N rational sqrt cascade — IEEE-bit x = M*2^e, root = isqrt(M << 2K) (K=27), projected by 2^(e/2 - K). Bit-exact with the native peer srmech_rational_sqrt; dispatches to C. precision=N selects the higher-precision bignum reference (as_integer_ratio + scaled floor-isqrt). No math.sqrt / np.sqrt in the call graph; negative x raises a domain error.",
            parameters=(P("x", "float", True, "radicand, x >= 0"),
                        P("precision", "int", False, "higher-precision bignum reference (keyword-only); default None = C-bit-exact K=27 cascade")),
            returns=R("Q", "sqrt(x) as an exact rational (Class-N Q carrier) from the integer root"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.hypot", owner="srmech", category="rational",
            summary="hypot(a, b) = sqrt(a^2 + b^2) via the Class-N sqrt cascade — Class-M sum-of-squares bind composed with the Class-N sqrt. Substrate-native replacement for math.hypot / np.hypot (the complex modulus |z| = hypot(z.real, z.imag)).",
            parameters=(P("a", "float", True, "first leg"),
                        P("b", "float", True, "second leg"),
                        P("precision", "int", False, "scaled-integer precision (keyword-only); default 64")),
            returns=R("Q", "Euclidean norm sqrt(a^2 + b^2) as an exact rational (Class-N Q carrier)"),
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
            summary="Exact eigenvalues of an integer matrix — the well-conditioned exact-until-rotation cascade (no Wilkinson ill-conditioning, because the eigenvalues are ALGEBRAIC and we never leave exact arithmetic). char_poly (exact integer) + Yun square-free factorization (exact multiplicities) + Sturm sign-sequence isolation (Class C sign-count at Class K interval boundaries) + rational bisection (Class N anchors → the algebraic asymptote), all in exact Fraction arithmetic, then ONE FPU lift. bits sets refinement precision; return_intervals=True yields the exact (lo, hi) rational isolating intervals (real-only path). Returns the real eigenvalues ascending WITH multiplicity. With include_complex=True the COMPLEX eigenvalues are also returned, EXACTLY ISOLATED: a float-QR candidate is certified as a unique root of the exact integer char-poly in a rational box by the argument-principle root-count (winding number in exact Fraction arithmetic — no float in the count), refined to bits, the float being the single terminal projection of the certified box center — distinct from the unconditioned float-QR spectrum of mat_eigvals it merely seeds. Returns all n eigenvalues (reals first ascending as float, then complex sorted by (re, im) as complex; conjugate pairs).",
            parameters=(P("a", "Mat", True, "(n, n) integer square matrix"),
                        P("bits", "int", False, "keyword-only; bisection refinement precision in bits (default 64)"),
                        P("return_intervals", "bool", False, "keyword-only; return exact (lo, hi) rational intervals instead of floats (real-only path); default False"),
                        P("include_complex", "bool", False, "also isolate+return the complex eigenvalues (default: real only)")),
            returns=R("list", "real eigenvalues ascending with multiplicity (floats, or (lo, hi) exact-ℚ intervals); with include_complex=True, all n eigenvalues (reals as float then certified complex)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.matrix_cascades.lll_reduce", owner="srmech", category="cascade",
            summary="EXACT-ℚ LLL lattice-basis reduction — the classic Lenstra–Lenstra–Lovász (1982) reduction of an integer lattice basis, in exact rational arithmetic (no float anywhere), and the foundation for a future van Hoeij polynomial-factorization knapsack (the LLL recombination that supersedes the exponential Zassenhaus subset search in factor_integer_poly). Input basis is m integer row-vectors (length n) spanning a rank-m lattice; delta=(num, den) is the Lovász parameter in (1/4, 1] (default 3/4). Returns the LLL-reduced basis (m integer row-vectors): SAME lattice (a unimodular change of basis, det = ±1), size-reduced (|μ_{k,j}| ≤ 1/2 for j<k), Lovász-satisfying (‖b*_k‖² ≥ (δ − μ²_{k,k−1})·‖b*_{k−1}‖²), so the first vector is provably short. The engine is exact throughout: a Gram-matrix Gram–Schmidt orthogonalization over ℚ (μ, ‖b*‖² as exact Fraction / arbitrary-precision srmech_bigint rationals in the C peer), size reduction by exact nearest-integer rounding of μ (round(a/b) = floor((2a+b)/(2b)) — never a float rint, never abs: the |μ| ≤ 1/2 guard is a Class-K sign branch on 2·num vs den), and the Lovász swap decided on the exact ℚ inequality. Integer-in, integer-out; rotation-last-trivial (no projection). Class L (the lattice / Gram–Schmidt spectral content) ∘ Class K (the size-reduction sign pin-slots + the swap-sign boundary — never an ALU abs) ∘ Class N (the exact nearest-integer rational rounding) ∘ Class I (the ordered integer vector row operations). Native-dispatched (srmech_lll_reduce, byte-identical to the pure body — both exact). Raises on a degenerate (linearly dependent) basis or a delta outside (1/4, 1]. Canonical SSoT: A. K. Lenstra, H. W. Lenstra Jr., L. Lovász, 'Factoring polynomials with rational coefficients', Math. Ann. 261 (1982), 515–534; algorithm as in H. Cohen, A Course in Computational Algebraic Number Theory (1993), Algorithm 2.6.3.",
            parameters=(P("basis", "list", True, "a list of m integer row-vectors (each length n, arbitrary-precision ints) — an independent lattice basis"),
                        P("delta", "tuple[int, int]", False, "the Lovász parameter as an exact rational pair (num, den) in (1/4, 1]; default (3, 4)")),
            returns=R("list", "the LLL-reduced basis: m integer row-vectors (same lattice, size-reduced, Lovász-satisfying)"),
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
            summary="Stream decimal digits of π via integer-cyclic geometric cascade (Archimedes hexagon-doubling with integer-floor √ via math.isqrt at fixed precision). Returns '3.141592...' as a string without invoking math.pi anywhere in the call graph (AST-verified discipline gate per `[[user_stance_pi_spectral_shape_scalar_invariant]]`; Spike #32 / PR #460). rc13 cap-expansion (Task #248): num_digits up to 1000 with auto-scaled cascade depth + precision. Canonical SSoT: Archimedes *Measurement of a Circle* (c. 250 BCE) for the algorithm; Khinchin *Continued Fractions* §10 for canonical π reference.",
            parameters=(P("num_digits", "int", True, "0 <= num_digits <= 1000"),
                        P("max_cascade_depth", "int", False,
                          "default None (auto-scaled from num_digits); cascade doubling depth in [1, 2000]"),
                        P("precision", "int", False,
                          "default None (auto-scaled from num_digits); scaled-integer √ bit precision in [64, 32768]")),
            returns=R("str", "'3.{num_digits}' decimal expansion of π"),
        ),
        ToolEntry(
            name="srmech.amsc.rational.pi_chudnovsky_digits",
            owner="srmech",
            category="rational",
            summary="Stream decimal digits of π via the ROTATION-LAST Chudnovsky series — the canonical srmech cascade shape: the body stays bit-exact (exact integer add/sub/mul/floor-divmod accumulating the Chudnovsky linear series on arbitrary-precision integers — the caller-arena srmech_bigint in C), and the SINGLE continuous/frame projection ('rotation') happens ONCE, terminally, as one isqrt(10005·one²) followed by one division and a base-10 render. NO float, NO math, NO per-term square root — the opposite of pi_cascade_digits (Archimedes), which projects every step. ~14.18 digits land per term. Native C path srmech_pi_chudnovsky when present (byte-identical to the pure-Python bignum oracle; C==Python validated at 1000 + 10000 digits); pure Python is the complete fallback + the parity oracle. Returns '3.141592...' as a string. Canonical SSoT: D. V. & G. V. Chudnovsky, 'Approximations and complex multiplication according to Ramanujan' (1988).",
            parameters=(P("num_digits", "int", True, "0 <= num_digits <= 100000"),),
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
            summary="Couple one helix turn through coupling — the genome's turn operation (F713). The turn is bound to the_one (the held invariant) by the REVERSIBLE Klein-4 bind (V4=(F2)^2 XOR, so quad_turn(quad_turn(t, one), one) == t): the duality held WITHOUT collapse, numpy-free. coupling is the shared invariant in every turn's coupling, so a chromosome navigates across its turns through coupling and recovers any turn by re-binding. Each turn sits in the native 4-sector biaxial '+' (cascade.parallel_sector_dispatch, CAP=4) — per F712 the 4-way is ONE chirality level, the deeper leaf-tree is base-4 radix addressing. Class M (bind) composed with Class C (the Klein-4 chirality). CAPABILITY (rc339 / #T967): this MCP surface is the KLEIN-4 rung of the genome's element_type ladder — V4 is ABELIAN, so every turn here composes and none of them carries a which-way. The library kwarg element_type selects the rung: klein4=0 (abelian), q8=1 (the ONLY rung where a NON-COMMUTING turn still folds — 24 such pairs measured), octonion=2 (addressing reaches e4..e7 and composition is still zero-divisor-free, but turn composition DEGRADES TO ABELIAN-ONLY: the turn-composing set and the commuting set are the same 88 pairs). See introspect.describe()['limits'].",
            parameters=(P("turn", "HV", True, "a Klein-4 vector (uint8 {0,1,2,3}) — the helix turn (e.g. from hdc.klein4_expand)"),
                        P("coupling", "HV", True, "a Klein-4 vector (uint8 {0,1,2,3}) — the held invariant coupled into every turn"),
                        ET_PARAM),
            returns=R("HV", "the coupled turn (re-apply quad_turn with the same coupling to recover turn)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.telomere", owner="srmech", category="genome",
            summary="The non-data content-address CAP that delimits a chromosome (F715) — biology's repetitive non-coding chromosome-end cap. A deterministic, content-addressed Klein-4 sentinel derived from a label (Class A content-address via sha256_bytes -> a seed -> a Klein-4 carrier). Same label gives the same cap (so a chromosome is recalled / partitioned by matching its cap), distinct labels give distinct caps. It marks + protects a partition boundary and carries no kernel data. dim is the Klein-4 vector length (match the turns it caps).",
            parameters=(P("label", "str", True, "the chromosome label — content-addressed to a deterministic cap"),
                        P("dim", "int", False, "Klein-4 vector length (default 64); match the turns the cap delimits")),
            returns=R("HV", "the telomere cap (a Klein-4 vector, deterministic per label)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.active_telomere", owner="srmech", category="genome",
            summary="The ACTIVE TELOMERE (UPSTREAM §127 / #726) — a chromosome cap made op(x)operand: it opens + governs a chromosome (the OPERATOR — a gating rule, like telomere) AND carries an exact non-negative Hayflick COUNT inline in the strand (the OPERAND — the descending replicative counter; Harley/Futcher/Greider 1990 Nature 345:458, Hayflick 1965 Exp Cell Res 37:614). The count MODULATES a downstream op (telomere_tick): count>0 -> a divide proceeds + decrements; count==0 -> honest senescence. That is what makes the chromosome GENUINELY op(x)operand (a plain telomere is a PASSIVE op-slot — #726). Same (operand, op) pattern as op_provenance.carry (value, operation) and coupling.RecoverableFold (lossy_bundle, exact_seed_R) but with an ACTIVE op. Marker byte 0x74; layout [0x74] + utf-8 label + NUL + count(uint64 big-endian) + NUL-pad; count is an exact Class-I/N integer (no float, never abs). Same label + count give the same cap.",
            parameters=(P("label", "str", True, "the chromosome label — read back inline (bytes [1:] up to the first NUL), uniform with telomere"),
                        P("count", "int", True, "the exact non-negative Hayflick count (allowed divides before senescence); Class-I/N, no float"),
                        P("dim", "int", False, "Klein-4 vector length (default 64); match the turns the cap delimits — must fit label + 10 bytes")),
            returns=R("HV", "the active-telomere cap (a fixed-width cap leaf carrying the count inline)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.telomere_tick", owner="srmech", category="genome",
            summary="The DIVIDE/GATE op (UPSTREAM §127 / #726) — the ACTIVE TELOMERE's count MODULATES the operator. strand is a chromosome that opens with an active_telomere cap (0x74); this reads the count (the operand) and its behaviour (the operator) is SELECTED by it: count>0 -> DIVIDE (decrement the count by exactly 1 — the telomere SHORTENS — and return the DAUGHTER strand: the same coupled leaves led by an active telomere of count-1; the telomere governs the leaves WITHOUT decoding them, like biology shortening the cap not re-synthesising the genes), status 'divided'; count==0 -> SENESCENCE (refuse HONESTLY, no daughter, status 'senescent' — the Hayflick limit, Hayflick & Moorhead 1961 Exp Cell Res 25:585 / Hayflick 1965). An active telomere of count N allows EXACTLY N divides, then the N+1-th refuses. THE op(x)operand duality made testable — same call, operator behaviour set by the operand. Needs no the_one (the count lives in the cap; §44 bare-strand self-description). Returns {status, label, count_before, count_after, daughter}. Native-dispatched (byte-identical C peer srmech_genome_telomere_tick).",
            parameters=(P("strand", "Sequence[HV]", True, "a chromosome strand opening with an active_telomere cap (from chromosome(leaves, coupling, active_count=N))"),),
            returns=R("dict", "{status: 'divided'|'senescent', label, count_before, count_after, daughter: strand|None}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.gene_express", owner="srmech", category="genome",
            summary="CELL-STATE-MODULATED GENE EXPRESSION (UPSTREAM §128 / #728; §129 / #729 KLEIN-4 REGULATORY ROLES; §130 / #730 BOOLEAN GATE-TYPE) — a READ-TIME FILTER over a multi-gene chromosome: the cell_state OPERAND modulates which genes the gene_express OPERATOR includes, dispatching on each gene's declared GATE-TYPE. §130 GATE-TYPE FAMILY: gate_type=klein4_mask (E1, the DEFAULT/FAST common case; a plain 0x47 gene or a Klein-4-mask 0x67 regulatory gene) OR gate_type=boolean (E2, the GENERAL escape hatch; a 0x62 boolean gene). klein4_mask rule: a gene EXPRESSES iff (cell_state & activator_mask) == activator_mask (ALL activator conditions PRESENT) AND (cell_state & repressor_mask) == 0 (NO repressor condition PRESENT). §129: each regulatory CONDITION (bit) is a KLEIN-4 sector — the genome's native alphabet — with role given by the (act_bit, rep_bit) pair: (0,0) don't-care / (1,0) activator (require-present) / (0,1) repressor (require-absent) / (1,1) never (present AND absent = contradiction -> auto-silenced). The lac operon is the exemplar (activator=lactose-bit, repressor=glucose-bit -> expresses iff lactose present AND glucose absent). §130 boolean rule: a 0x62 gene carries ARBITRARY boolean logic as a DNF (disjunctive normal form — an OR of (require-present, require-absent) AND-clauses) and EXPRESSES iff ANY clause matches; DNF is functionally complete, so AND / OR / NOT / XOR / any boolean function over the conditions is representable. E1 subset E2: the klein4_mask (activator, repressor) two-mask IS a 1-CLAUSE DNF, so E1 is the compact fast special case of E2's general disjunction (combinatorial cis-regulatory logic; Alberts et al., MBoC 4th ed., How Genetic Switches Work, NCBI NBK26872). ENCODING = two parallel bitmasks (activator_mask, repressor_mask), the two Klein-4 bit-planes, carried inline in a REGULATORY GENE cap (marker 0x67; [0x67] + label + NUL + activator(uint64 BE) [+ repressor(uint64 BE)] + NUL-pad); a boolean gene is carried in a BOOLEAN GENE cap (marker 0x62; [0x62] + label + NUL + gate_type(uint8) + n_terms(uint16 BE) + n_terms x (activator(uint64 BE) + repressor(uint64 BE)) + NUL-pad; a NEW block KIND -> genome format v8 -> v9). §131 GATE-TYPE 3 (E4 the LINEAR-THRESHOLD gate): a THRESHOLD gene (marker 0x77) carries a perceptron — a per-condition SIGNED integer weight vector + an integer threshold — and EXPRESSES iff Sum_i (weight_i * bit_i(cell_state)) >= threshold (the decision is the SIGN of Sum minus threshold — Class-K, never abs; SIGNED weights allow an inhibitory input). GENUINELY DISTINCT from E2: a linear-threshold function (MAJORITY-of-n = all-ones weights with threshold=ceil(n/2), or a weighted morphogen dose-sum) needs an EXPONENTIALLY-large DNF, so E4 captures COMPACTLY what E2's DNF cannot (linear-threshold functions subset-not small-DNF; the additive / morphogen-gradient threshold enhancer model, Alberts et al., MBoC 4th ed., Drosophila and the Molecular Genetics of Pattern Formation, NCBI NBK26906 — the Dorsal morphogen turns genes on/off depending on its concentration). Layout: [0x77] + label + NUL + gate_type(uint8) + n_weights(uint16 BE) + threshold(int64 BE signed) + n_weights x weight(int64 BE signed) + NUL-pad; a NEW block KIND -> genome format v9 -> v10. DUAL-READ / back-compat: the repressor lives in what was NUL padding, so a rc128 single-mask cap reads as activator=mask, repressor=0 (a pure all-activator AND-gate, IDENTICAL behaviour) and an activator-only gene is BYTE-IDENTICAL to rc128; a PLAIN gene (0x47, no masks) is UNREGULATED = (0,0) = ALWAYS EXPRESSED. SAME DNA, DIFFERENT cell_state -> DIFFERENT expressed subset — the op(x)operand theorem one scale up from the rc127 active telomere. Same (operand, op) pattern as op_provenance.carry / coupling.RecoverableFold, now with a CELL-STATE operand + an EXPRESSION operator. NEVER MUTATES THE STRAND (a READ — biology does not rewrite DNA to regulate it; the strand is byte-identical after). Returns the expressed subset [(gene_label, gene_leaves), ...] (the genes() shape, filtered), gene_leaves uncoupled through coupling. Class-I exact bitwise (no float, never abs). Native-dispatched (byte-identical C peer srmech_genome_gene_express). Attests differential gene expression as ONE facet — the CELL-TYPE-SELECTION facet (Alberts et al., Molecular Biology of the Cell 4th ed., How Genetic Switches Work, NCBI NBK26872: 'Different selections of gene regulatory proteins are present in different cell types and thereby direct the patterns of gene expression that give each cell type its unique characteristics'); the activator/repressor operon model — Jacob & Monod 1961, J Mol Biol 3:318-356.",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-gene chromosome strand (from chromosome(genes=[(label, leaves) | (label, leaves, activator_mask) | (label, leaves, activator_mask, repressor_mask), ...], coupling))"),
                        P("coupling", "HV", True, "the held invariant the gene turns were coupled through (the expressed leaves are uncoupled through it)"),
                        P("cell_state", "int", True, "the exact non-negative cell-state bitmask; each set bit a present regulatory condition (Class-I bitwise; no float)"),
                        ET_PARAM),
            returns=R("list", "the EXPRESSED subset [(gene_label:str, gene_leaves:list[HV]), ...] in strand order (plain genes always; regulatory genes iff (cell_state & activator) == activator AND (cell_state & repressor) == 0)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.gene_express_levels", owner="srmech", category="genome",
            summary="GRADED / ANALOG gene expression LEVEL (UPSTREAM §132 / #732 — the E3 rung) — the ORTHOGONAL companion to gene_express, a READ-TIME FILTER over a multi-gene chromosome. Where gene_express decides IF each gene expresses (a BINARY set, dispatching on each gene's E1/E2/E4 gate-type) and returns [(gene_label, gene_leaves), ...], this op returns each EXPRESSED gene WITH its exact-rational expression LEVEL [(gene_label, gene_leaves, (num, den)), ...] — HOW MUCH it expresses (real biology is quantitative/analog, not just on/off). The LEVEL axis is ORTHOGONAL to the gate-type family — it composes with EVERY gene kind: a BINARY gene (plain 0x47 / klein4-mask 0x67 / boolean 0x62 / threshold 0x77) is the DEGENERATE {0,1} case, included at LEVEL exact-rational 1 = (1,1) iff its gate PASSES (the SAME §128/§130/§131 decision gene_express uses) and ABSENT otherwise; a GRADED gene (a NEW 0x64 cap, §132) carries a per-condition SIGNED integer LEVEL-WEIGHT vector + a POSITIVE integer DENOMINATOR, and its LEVEL is the reduced exact rational Sum_i (level_weight_i * bit_i(cell_state)) / denom CLAMPED to [0,1] (a Class-K sign-branch, never abs — raw dose <=0 -> 0, raw dose >= denom -> 1, else the reduced in-range fraction; the fraction reduced by the Class-I gcd), included iff its LEVEL > 0 (the dose-response IS the gate — a zero dose = off). So every gene gene_express returns appears here at level 1, and vice versa. NEW 0x64 cap layout: [0x64] + label + NUL + gate_type(uint8=3) + n_weights(uint16 BE) + denom(uint64 BE POSITIVE) + n_weights x level_weight(int64 BE signed) + NUL-pad; a NEW block KIND -> genome format v10 -> v11. THE THEOREM (op(x)operand, refined to a QUANTITY): the cell_state OPERAND modulates the LEVEL the gene_express_levels operator reports — SAME DNA, DIFFERENT cell_state -> DIFFERENT expression LEVELS (not just a different on/off subset); a morphogen at a graded concentration drives a graded transcriptional output. NEVER MUTATES THE STRAND (a READ — the strand is byte-identical after). Returns the expressed subset [(gene_label, gene_leaves, (num, den)), ...] in strand order — (num, den) is the reduced exact-rational level (a JSON-native 2-tuple of ints); gene_leaves uncoupled through coupling. Class-N exact rational (no float, never abs); Class-I gcd-reduce; Class-K clamp. Native-dispatched (byte-identical C peer srmech_genome_gene_express_levels). Attests graded / dose-response gene expression as ONE facet (Alberts et al., Molecular Biology of the Cell 4th ed., How Genetic Switches Work -> Gene Activator Proteins Work Synergistically, NCBI NBK26872 — the joint effect of several activators on the transcription RATE is not merely the sum but the product: a graded, analog modulation of the expression level, not a binary switch).",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-gene chromosome strand (from chromosome(genes=[...], coupling)); may mix plain / regulatory / boolean / threshold / graded genes"),
                        P("coupling", "HV", True, "the held invariant the gene turns were coupled through (the expressed leaves are uncoupled through it)"),
                        P("cell_state", "int", True, "the exact non-negative cell-state bitmask; each set bit a present condition (Class-I bitwise; no float)"),
                        ET_PARAM),
            returns=R("list", "the EXPRESSED subset [(gene_label:str, gene_leaves:list[HV], level:(num:int, den:int)), ...] in strand order — a BINARY gene at level (1,1) iff its gate passes; a GRADED gene at its reduced dose-response rational in (0,1] (absent when the level is 0)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.gene_express_plan", owner="srmech", category="genome",
            summary="DEMAND-LOAD gene-expression PLAN (UPSTREAM §134 / #1273, siona green-light — the #736 probe made shippable) — the OFFSET-ONLY load plan that computes the EXPRESSED set + each expressed unit's ON-DISK byte-range WITHOUT reading content (never decodes a leaf), so a partial-load reader (genome_genes_expressed) can SEEK only the expressed byte-ranges. Returns [(label, byte_offset, byte_len), ...] for the EXPRESSED genes / regions. TWO variants, dispatched on the input: PATH variant (variant b — the PRIMARY demand-load case): strand_or_path is a genome DIRECTORY (with the rc115 v4 manifest). For each chromosome REGION the plan seeks to the manifest byte_offset and reads ONLY the region's head GATE cap (the SECOND block, one leaf_dim-byte cap right after the CHROM cap), evaluates its inline gate (E1 0x67 / E2 0x62 / E4 0x77 / E3 0x64 — the delivered gates) against cell_state, and includes the EXPRESSED regions' (chromosome_label, byte_offset, byte_len). It MUST NOT read the region body — bounded RAM AND bounded I/O (bytes-touched << full body). A region with no head gene cap (a single-kernel chromosome, byte_len < 2*leaf_dim) is not a gated community and is skipped. This is the siona community=chromosome layout: the per-chromosome head gate IS the community gate. Mixed E1/E2/E4/E3 gate-types across chromosomes are the delivered gates — the plan gates by the inline mask regardless of kind. §98/rc269 chromatin OUTER gate: if the head slot is a CHROMATIN cap (0x48), it gates the whole region — a CONDENSED (silenced, accessibility numerator 0) region is SKIPPED at plan time having touched ONLY the chromatin cap (its gene gate cap is NEVER read — even fewer bytes than the §134 read); an OPEN (accessible) region advances one slot and reads the gene gate as before; a chromatin-FREE region is byte-for-byte the rc135 read. STRAND variant (variant a — the in-memory fallback): strand_or_path is an in-memory strand. The plan SKELETON-SCANS it — walking blocks, computing each block's ON-DISK byte span (a cap is leaf_dim bytes; a data turn is the §55/v3 bit-packed 1 + ceil(leaf_dim/4) bytes — the payload is SEEKED PAST, never decoded), splitting on the inline GENE caps, and delimiting each EXPRESSED gene's byte-range (gene_label, byte_offset, byte_len) in the on-disk layout genome_save would write. The expressed-label set equals gene_express's on the same strand + cell_state. A READ — the strand / file is byte-identical after. cell_state is a non-negative exact int (Class-I bitwise; no float, never abs). The PATH variant is native-dispatched (byte-identical C peer srmech_genome_gene_express_plan reads only the head gate caps + emits the same offset plan); pure Python is the complete alternative. NO format addition — the ops read the existing caps / manifest (genome format v11 stays). Attests demand-loaded differential gene expression — bounded RAM WITHOUT bounded availability, the epigenetic on-demand-transcription facet (Alberts et al., Molecular Biology of the Cell 4th ed., How Genetic Switches Work, NCBI NBK26872: different cell types express different gene selections; the demand-load reads only the promoter / regulatory cap to decide, not the gene body).",
            parameters=(P("strand_or_path", "list|str", True, "PATH variant (b): a genome DIRECTORY (written by genome_save) — the demand-load case, reads only each region's head gate cap via the manifest offset. STRAND variant (a): an in-memory strand (list of Klein-4 vectors) — the skeleton-scan fallback."),
                        P("coupling", "HV", True, "the held invariant (the leaf-width anchor; the plan reads only the gate caps, which are not coupled through it)"),
                        P("cell_state", "int", True, "the exact non-negative cell-state bitmask; each set bit a present regulatory condition (Class-I bitwise; no float)"),
                        ET_PARAM),
            returns=R("list", "the offset-only load plan [(label:str, byte_offset:int, byte_len:int), ...] for the EXPRESSED genes / regions — PATH variant: per expressed chromosome REGION; STRAND variant: per expressed GENE. NEVER decodes / returns leaf content."),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_genes_expressed", owner="srmech", category="genome",
            summary="DEMAND-LOAD partial-load READER (UPSTREAM §134 / #1273, siona green-light) — the companion to gene_express_plan. Uses the PATH (variant-b) plan to SEEK + load + decode ONLY the EXPRESSED chromosome regions, then filters each region's genes by gene_express — returning [(gene_label, gene_leaves), ...] BYTE-IDENTICAL to the expressed subset of a full genome_genes / gene_express over the WHOLE genome, WITHOUT loading the unexpressed regions (bounded RAM AND bounded I/O). In the siona community=chromosome layout the per-chromosome head gate IS the community gate, so an unexpressed community (head gate off) contributes no expressed gene — skipping its region is exact. A READ — the file is byte-identical after (biology reads the regulatory region, it does not rewrite the DNA). cell_state is a non-negative exact int (Class-I bitwise; no float, never abs). The plan is native-dispatched (the C peer srmech_genome_gene_express_plan); the per-region load + gene_express decode are the exact pure path — the leaves are byte-identical whether the plan came from C or Python. NO format addition (reads the existing v4 manifest + caps; genome format v11 stays). Attests demand-loaded gene expression: the expressed subset is materialised on demand, the unexpressed genes never paged in (Alberts et al., MBoC 4th ed., NCBI NBK26872).",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("coupling", "HV", True, "the held invariant the gene turns were coupled through (the expressed leaves are uncoupled through it)"),
                        P("cell_state", "int", True, "the exact non-negative cell-state bitmask; each set bit a present condition (Class-I bitwise; no float)")),
            returns=R("list", "the EXPRESSED subset [(gene_label:str, gene_leaves:list[HV]), ...] across the whole genome in body order — BYTE-IDENTICAL to the expressed subset of a full gene_express, but with only the expressed regions paged in (the unexpressed communities never loaded)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.modulator_recover", owner="srmech", category="genome",
            summary="MODULATOR-RECOVERY M1 (UPSTREAM §133 / #733) — the INVERSE of gene_express. gene_express is the FORWARD map (cell_state -> expressed genes); this recovers the TWO-SIDED cell-state FLOOR from an OBSERVED expressed-label set (+ the strand's gene regulatory specs). It is UNDER-DETERMINED (many cell_states -> the SAME expressed subset), so the exact cell_state is IRRECOVERABLE BY CONSTRUCTION and the only honest form is a ONE-SIDED floor — the SAME recoverability discipline / op_verdict EQUAL/UNKNOWN contract as op_provenance (rc117) / RecoverableFold / the #725 null: recover the EXACT complement we can PROVE, flag the rest UNKNOWN. THE FLOOR (sharpened by the rc129 activator/repressor two-mask): certain_on = the bits every consistent cell_state MUST have SET — each EXPRESSED E1 gene (klein4-mask 0x67 / plain 0x47) proves its activator bits are on (OR their activator masks); each EXPRESSED E2 gene (boolean DNF 0x62) proves >=1 clause matched, so the bits set in EVERY clause's activator (the INTERSECTION-over-clauses activator) are certain-on. certain_off = the bits every consistent state MUST have CLEAR: OR of expressed E1 repressor masks + the intersection-over-clauses repressor of expressed E2 genes. E4 threshold (0x77) / E3 graded (0x64) / UN-expressed genes give NO clean single-bit certainty (a failed threshold / an absent gene is a DISJUNCTION — that is M3's job) so they contribute NOTHING to the clean floor (SOUND, not over-claiming). undetermined = the referenced condition bits (the union of bits ANY gene reads) minus (certain_on | certain_off). verdict = EXACT if certain_on | certain_off covers ALL referenced bits (the floor fully determines the state), PARTIAL if some pinned, UNKNOWN if none — mirroring op_verdict's one-sidedness (NEVER claim a bit's value it can't prove). SOUNDNESS (the load-bearing contract): for EVERY cell_state modulator_consistent reports CONSISTENT, (state & certain_on) == certain_on AND (state & certain_off) == 0; a gene's floor is applied only when its label is expressed AND UNIQUE among the strand's gene caps (a duplicated label cannot be attributed). NEVER MUTATES the strand (a READ — byte-identical after). coupling is the leaf-width anchor (M1 reads only the gene CAPS, which are not coupled). Class-I exact bitwise (no float, never abs). Native-dispatched (byte-identical C peer srmech_genome_modulator_recover). Attests gene-regulatory-network (GRN) inference — reverse-engineering the regulatory state from an expression pattern — as ONE FACET of a real biological-computational problem (the inverse of expression; #728 discipline — NOT a claim srmech reproduces it): Marbach D, Costello JC, Kuffner R, et al., Wisdom of crowds for robust gene network inference, Nature Methods 9(8):796-804 (2012), DOI 10.1038/nmeth.2016 (OA: NIH PMC3512113).",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-gene chromosome strand (from chromosome(genes=[...], coupling)); may mix plain / regulatory / boolean / threshold / graded genes"),
                        P("coupling", "HV", True, "the held invariant (the leaf-width anchor; M1 reads only the gene caps, which are not coupled through it)"),
                        P("expressed_labels", "Sequence[str]", True, "the OBSERVED expressed gene labels (a set / list of the gene names that expressed — the recovery input)")),
            returns=R("dict", "{certain_on: int (bits every consistent state must have SET), certain_off: int (bits every consistent state must have CLEAR), undetermined: int (referenced-but-unpinned bits), verdict: str (EXACT / PARTIAL / UNKNOWN)} — all JSON-native; the floor is SOUND (never over-claims a bit)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.modulator_consistent", owner="srmech", category="genome",
            summary="MODULATOR-RECOVERY M2 (UPSTREAM §133 / #733) — the candidate consistency verdict for the INVERSE of gene_express. Forward-CHECK one candidate cell_state: is set(labels of gene_express(strand, coupling, candidate)) == set(expressed_labels)? -> CONSISTENT else INCONSISTENT. ONE-SIDED (the op_verdict EQUAL/UNKNOWN reuse): CONSISTENT means 'could be the state' (MANY candidates may be — expression is under-determined), NEVER 'it IS the state'. Reuses the FORWARD gene_express (no new gate logic — it dispatches on each gene's E1/E2/E4 gate-type exactly as the forward map does). Pairs with modulator_recover: M1's floor is SOUND precisely because every state M2 calls CONSISTENT satisfies it (every consistent state has certain_on set and certain_off clear). NEVER MUTATES the strand (a READ). candidate_cell_state is a non-negative exact int (Class-I bitwise; each set bit a present condition; no float, never abs). Native-dispatched (byte-identical C peer srmech_genome_modulator_consistent). Attests GRN-inference / consistency-checking of a candidate regulatory state as ONE FACET (the inverse of expression; #728 discipline — NOT a claim srmech reproduces it): Marbach et al., Nature Methods 9(8):796-804 (2012), DOI 10.1038/nmeth.2016 (OA: NIH PMC3512113).",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-gene chromosome strand (from chromosome(genes=[...], coupling))"),
                        P("coupling", "HV", True, "the held invariant the gene turns were coupled through (gene_express uncouples the expressed leaves through it)"),
                        P("expressed_labels", "Sequence[str]", True, "the OBSERVED expressed gene labels (the set to check the candidate against)"),
                        P("candidate_cell_state", "int", True, "the candidate cell-state bitmask to forward-check (Class-I bitwise; non-negative; no float)"),
                        ET_PARAM),
            returns=R("str", "'CONSISTENT' iff gene_express(candidate) produces exactly expressed_labels (could be the state — many may be), else 'INCONSISTENT' (one-sided; never a false positive-identification)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.modulator_constraint", owner="srmech", category="genome",
            summary="MODULATOR-CONSTRAINT M3 (UPSTREAM §133 / #733 — the LAST rung of the E-M ladder) — the COMPLETE inverse of gene_express. Where M1 (modulator_recover) gives the SOUND two-sided FLOOR from the EXPRESSED genes and M2 (modulator_consistent) forward-CHECKS one candidate, M3 returns the EXACT CONSTRAINT characterizing the WHOLE set of cell-states consistent with an observed expression — a COMPACT structured constraint, NEVER an enumeration (the consistent set can be exponential). It ADDS what M1 left out: (a) the DISJUNCTIVE clauses from UN-expressed genes — an un-expressed E1 gene (activator a, repressor r) PROVES (cs & a) != a OR (cs & r) != 0 (some activator absent OR some repressor present) = a nand-clause; an un-expressed E2 gene ANDs one nand-clause per DNF term (all clauses must fail); (b) the FULL expressed-E2 disjunction (M1 only took the SOUND intersection-over-clauses; M3 adds the exact or_terms disjunction — an expressed label with >= 2 boolean terms expresses iff >= 1 term fully matches); (c) the general-gate inverse — an EXPRESSED E4 threshold gene -> Sum w_i*bit_i(cs) >= theta (a linear inequality), UN-expressed -> Sum < theta; an E3 graded gene EXPRESSED -> Sum w_i*bit_i(cs) >= 1 (level > 0), UN-expressed -> Sum <= 0 (level 0). These are CONSTRAINT-SATISFACTION, not a mask-OR. Returns a JSON-native dict {certain_on:int, certain_off:int (M1's floor pins), clauses:[{kind:'nand', any_absent:int, any_present:int} | {kind:'or_terms', terms:[{present:int, absent:int}, ...]}, ...], inequalities:[{weights:[int,...], threshold:int, sense:'>='|'<'}, ...], levels:[{weights:[int,...], denom:int, positive:bool}, ...], satisfiable:bool, free_bits:int, solution_note:str, sound_complete:bool, sound_only_labels:[str, ...]}. ALL clauses / inequalities / levels are ANDed (a conjunction); check a candidate with modulator_constraint_satisfies. SOUND: every cell_state modulator_consistent reports CONSISTENT satisfies the constraint. COMPLETE (satisfies <=> M2-CONSISTENT) for the BOOLEAN gate-types E1/E2 at ANY label multiplicity AND for a UNIQUE single E4/E3 gene; SOUND-ONLY (an over-approximation, HONESTLY reported in sound_only_labels with sound_complete=False) for an EXPRESSED label that is a genuine CROSS-TYPE disjunction (a duplicated label spanning boolean AND threshold/graded, or >= 2 threshold/graded genes) — that OR has no exact flat-clause form, so its expressed requirement is DROPPED to stay sound. UN-expressed labels are COMPLETE for EVERY gate-type (a conjunction of exact silence constraints). satisfiable is True iff SOME cell-state satisfies (a real came-from-a-state expression is always satisfiable; a hand-supplied inconsistent set — e.g. two genes that can't co-express — is False): FALSE is always a PROOF, and within the free-bit bound it is decided EXACTLY (see solution_note). free_bits = the count of referenced-but-unpinned condition bits; solution_note characterizes the solution-set SIZE HONESTLY and NEVER enumerates it. NEVER MUTATES the strand (a READ — byte-identical after). Native-dispatched: the C peer srmech_genome_modulator_constraint emits the BOOLEAN part (floor + clauses) byte-identically; the inequalities / levels / satisfiability are the exact pure Class-N/I path (the owed-C = the E4/E3 emit). Class-I bitwise; Class-N integer sums; the inequality SENSE is a Class-K sign (never abs). Attests gene-regulatory-network (GRN) inference — inferring the COMPLETE regulatory-input constraint from an expression profile, a constraint-satisfaction view of the inverse problem — as ONE FACET (#728 discipline, NOT a claim srmech reproduces it): Marbach D, Costello JC, Kuffner R, et al., Wisdom of crowds for robust gene network inference, Nature Methods 9(8):796-804 (2012), DOI 10.1038/nmeth.2016 (OA: NIH PMC3512113).",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-gene chromosome strand (from chromosome(genes=[...], coupling)); may mix plain / regulatory / boolean / threshold / graded genes"),
                        P("coupling", "HV", True, "the held invariant (the leaf-width anchor; M3 reads only the gene caps, which are not coupled through it)"),
                        P("expressed_labels", "Sequence[str]", True, "the OBSERVED expressed gene labels (a set / list of the gene names that expressed — the constraint input)")),
            returns=R("dict", "{certain_on:int, certain_off:int (M1 floor), clauses:[nand / or_terms dicts], inequalities:[E4 linear inequalities], levels:[E3 level constraints], satisfiable:bool, free_bits:int, solution_note:str, sound_complete:bool, sound_only_labels:[str]} — all JSON-native; the EXACT constraint on the consistent-state set (SOUND everywhere; COMPLETE for E1/E2 + unique E4/E3), NEVER an enumeration"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.modulator_constraint_satisfies", owner="srmech", category="genome",
            summary="MODULATOR-CONSTRAINT M3 checker (UPSTREAM §133 / #733) — does a candidate cell_state satisfy an M3 constraint? The runnable predicate that makes the SOUND-AND-COMPLETE claim TESTABLE. Evaluates the WHOLE constraint modulator_constraint returned: the floor pins ((cs & certain_on) == certain_on AND (cs & certain_off) == 0) AND every nand clause ((cs & any_absent) != any_absent OR (cs & any_present) != 0) AND every or_terms clause (>= 1 term fully matches: (cs & present) == present AND (cs & absent) == 0) AND every E4 inequality (Sum w_i*bit_i(cs) >= threshold for sense '>=', < threshold for sense '<') AND every E3 level (Sum >= 1 for positive, Sum <= 0 else), ALL ANDed. On the COMPLETE gate-types this EQUALS modulator_consistent(strand, coupling, expressed_labels, candidate) == 'CONSISTENT' exactly; for a SOUND-ONLY cross-type-OR label it is a sound over-approximation (True for every consistent state, possibly True for a few inconsistent ones — the dropped disjunct). NEVER MUTATES anything (a READ). candidate_cell_state is a non-negative exact int (Class-I bitwise; no float, never abs). Native-dispatched (the C peer srmech_genome_modulator_constraint_satisfies checks the BOOLEAN part byte-identically; the inequality / level checks are the exact pure Class-N path). The inequality SENSE is a Class-K sign-branch, never abs. Returns bool. Attests GRN-inference consistency-checking of a regulatory state against the recovered constraint as ONE FACET (#728 discipline): Marbach et al., Nature Methods 9(8):796-804 (2012), DOI 10.1038/nmeth.2016 (OA: NIH PMC3512113).",
            parameters=(P("constraint", "dict", True, "the constraint dict modulator_constraint returned (certain_on / certain_off / clauses / inequalities / levels)"),
                        P("candidate_cell_state", "int", True, "the candidate cell-state bitmask to check (Class-I bitwise; non-negative; no float)")),
            returns=R("bool", "True iff candidate_cell_state satisfies EVERY floor pin + clause + inequality + level of the constraint (== M2-CONSISTENT on the complete gate-types; a sound over-approximation on a sound-only cross-type-OR label)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.chromosome", owner="srmech", category="genome",
            summary="Pack a kernel — or SEVERAL genes — into a telomere-capped strand (F713/F715/F730). Single kernel (unchanged): pass leaves (Klein-4 vectors, one tome each); they become a helix of quad-turns coupled through coupling, led by a telomere cap from label; recover with recall. Several genes (F730/S43): pass genes=[(gene_label, gene_leaves), ...] instead — each gene's leaves are framed by a tlv gene-header (the cheaper internal delimiter, label recoverable via tlv_unpack) inside ONE telomere-capped chromosome; recover with genes(). Pass exactly one of leaves or genes; coupling is always required. Class A (cap) + Class B (gene frame) + Class M (bind) + Class C (the Klein-4 chirality).",
            parameters=(P("leaves", "Sequence[HV]", False, "single-kernel mode: the kernel's leaves — Klein-4 vectors, one tome (<=256) each (pass leaves OR genes)"),
                        P("coupling", "HV", True, "the held invariant every turn is coupled through"),
                        P("label", "str", False, "keyword-only; the chromosome label for the telomere cap (default 'chromosome')"),
                        P("genes", "Sequence[tuple]", False, "keyword-only; multi-gene mode (F730): [(gene_label, gene_leaves), ...] inside one telomere-capped chromosome (pass leaves OR genes). §128/§129/§130 REGULATORY genes carry inline Class-I logic that gene_express filters on: a 4-tuple (gene_label, gene_leaves, activator_mask, repressor_mask) is the §129 two Klein-4 bit-planes / klein4_mask gate (require-present + require-absent conditions); a 3-tuple with an INT third element (gene_label, gene_leaves, activator_mask) is §128 activator-only (repressor 0, byte-identical to rc128); a 3-tuple with a DICT third element (gene_label, gene_leaves, {'gate':'boolean','dnf':[(act,rep),...]}) is a §130 BOOLEAN gene (arbitrary boolean logic as a DNF — an OR of (require-present, require-absent) AND-clauses; AND/OR/NOT/XOR; E1 klein4_mask subset E2 boolean); a 3-tuple with a DICT (gene_label, gene_leaves, {'gate':'threshold','weights':[w0,w1,...],'threshold':theta}) is a §131 THRESHOLD gene (E4 — a linear-threshold / perceptron gate: SIGNED integer weight per condition + an integer threshold; expresses iff Sum weight_i*bit_i(cell_state) >= theta; SIGNED weights = inhibitory inputs; GENUINELY DISTINCT from E2 — a MAJORITY-of-n / weighted dose-sum needs an exponential DNF, so linear-threshold subset-not small-DNF); a 3-tuple with a DICT (gene_label, gene_leaves, {'gate':'graded','weights':[w0,w1,...],'denom':D}) is a §132 GRADED gene (E3 — the ORTHOGONAL analog LEVEL axis / dose-response: a SIGNED integer level-weight per condition + a POSITIVE denominator; gene_express_levels reports the reduced exact-rational LEVEL Sum weight_i*bit_i(cell_state) / D clamped to [0,1]); a 2-tuple is UNREGULATED (always expressed)"),
                        ET_PARAM),
            returns=R("list", "the strand: [telomere_cap, coupled turn, ...] (single-kernel) or [telomere_cap, gene_header, coupled turn, ..., gene_header, ...] (multi-gene)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.centromere", owner="srmech", category="genome",
            summary="Build a CENTROMERE cap (§95a / #1407 / F1243) — a chromosome's INTERIOR global-orientation anchor. A telomere caps a chromosome's ENDS; the centromere is the interior constriction BETWEEN its two arms (the segregation / melange-coupling split point) and carries the per-chromosome GLOBAL orientation-chirality (the strand's handedness, distinct from Klein-4's LOCAL per-leaf chirality, ADR-0004). Where it sits in the strand IS the p:q arm-ratio (biology: the centromere position defines the arms); the orientation rides as biology's alpha-satellite REPEAT-ARRAY (repeats copies of the 4-way sector, majority-decoded on read — klein4_triality_correct's 2-of-3 generalised to R; Class-K sector count, no abs/float). Measured (F1243 §1): recovers the global which-way at ~15x fewer bits than per-leaf Klein-4 (R=15 -> 39 bits vs 600) with matching random-noise robustness. handle is the inline no-sidecar epigenetic address (CENP-A analog). Place it at mint time with chromosome(leaves, one, centromere=orientation); recover with centromere_of. Native-dispatched (byte-identical C peer srmech_genome_centromere). Class A (cap) + Class C (the orientation chirality) + Class K (the repeat-array EC read).",
            parameters=(P("orientation", "int", True, "the global 4-way orientation — a Klein-4 sector 0..3 (the which-way)"),
                        P("repeats", "int", False, "keyword-only; the alpha-satellite repeat-array size R (default 15; uint8 1..255 — R=1 is the single-index centromere, cheapest but fragile)"),
                        P("handle", "str", False, "keyword-only; the inline epigenetic handle / CENP-A-analog address (default 'cen')"),
                        P("dim", "int", False, "keyword-only; the leaf width in bytes (default 64; match the turns — chromosome passes len(coupling))")),
            returns=R("HV", "the centromere cap leaf (a fixed-width dim-byte sectors=256 HV: [0x58] + handle + NUL + R + R orientation votes, NUL-padded)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.centromere_of", owner="srmech", category="genome",
            summary="Recover a NUCLEAR chromosome's GLOBAL orientation + p:q arm-ratio from its centromere (§95a) — the inverse read of the centromere anchor. Scans the strand for the interior 0x58 cap, majority-decodes the global 4-way orientation from its alpha-satellite repeat-array (the EC read — klein4_triality_correct's 2-of-3 generalised to R), and reads the p:q arm-ratio from the cap's POSITION: p = data turns BEFORE it (the short arm), q = data turns AFTER (the long arm). Position IS the arm-ratio (biology: the centromere position defines the arms), so nothing double-encodes. Returns None for a Tier-1 plasmid chromosome (no centromere). NEVER MUTATES (a READ). Native-dispatched (the C peer srmech_genome_centromere_of does the majority + arm-ratio scan byte-identically; the handle/repeats are read inline in Python — the composition).",
            parameters=(P("strand", "Sequence[HV]", True, "a chromosome strand (from chromosome(..., centromere=o) or mint)"),),
            returns=R("dict", "{orientation: int 0..3, arm_ratio: (p, q), handle: str, repeats: int} — or None if the strand has no centromere"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.diploid", owner="srmech", category="genome",
            summary="Build a DIPLOID chromosome (§95b / #1407 / F1244) — biology's diploid pair, the erasure/break specialist. Stores TWO homologous copies of the kernel (maternal | paternal) split by an interior centromere whose orientation is the which-template MARK: [diploid_telomere(label), copyA turns…, centromere(orientation), copyB turns…], copyA == copyB. 2 copies + 1 mark = 3 = the k=3 triality (F291). A deterministic content-addressed store writes identical homologs; the redundancy is READ-time EC (recover_diploid): on a DETECTABLE loss (an erased leaf — a double-strand break) it fills from the intact homolog, reaching triality-level fidelity at 2x not 3x (measured R-RBS-LM-DIPLOID-EC); on a substitution disagreement the centromere mark is the tiebreak. This is the erasure specialist of the k=3 coherency tower (triality is the substitution specialist). Marker 0x44 'D' opens the chromosome like the CHROM cap. Native-dispatched (byte-identical C peer srmech_genome_diploid). Class A (content-address) + Class C (orientation) + Class K (the EC read).",
            parameters=(P("leaves", "Sequence[HV]", True, "the kernel's leaves — Klein-4 vectors, one tome (<=256) each; stored as two homologous copies"),
                        P("coupling", "HV", True, "the held invariant every turn is coupled through"),
                        P("label", "str", False, "keyword-only; the chromosome label for the diploid telomere cap (default 'diploid')"),
                        P("orientation", "Optional[int]", False, "keyword-only; the which-template mark + global orientation, a Klein-4 sector 0..3 (default the kernel's content-address folded to a sector)"),
                        P("repeats", "int", False, "keyword-only; the centromere alpha-satellite repeat-array size (default 15)"),
                        ET_PARAM),
            returns=R("list", "the diploid strand: [diploid_telomere, copyA turns…, centromere, copyB turns…] (2*len(leaves)+2 blocks), recovered with recover_diploid"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.recover_diploid", owner="srmech", category="genome",
            summary="Recover a DIPLOID chromosome's content via the two-copy EC (§95b) — the inverse of diploid. Splits the strand at its interior centromere into copyA | copyB (homologs) and error-corrects per leaf: both agree -> use it; exactly one ERASED (an all-zero leaf — a detectable double-strand break) -> fill from the intact homolog (the erasure specialist, 2x not 3x); both present but DISAGREE (a substitution) -> trust the centromere which-template mark (parity selects copyA or copyB). Re-binds each surviving turn through coupling. Returns the recovered leaves (half the raw turn count). Raises ValueError if the strand is not a diploid chromosome (no leading 0x44) or is malformed (missing centromere / unequal homolog arms). NEVER MUTATES (a READ). Native-dispatched (byte-identical C peer srmech_genome_recover_diploid).",
            parameters=(P("strand", "Sequence[HV]", True, "a diploid chromosome strand (from diploid())"),
                        P("coupling", "HV", True, "the held invariant the copies were coupled through"),
                        ET_PARAM),
            returns=R("list", "the recovered kernel leaves (Klein-4 vectors), in order — half the raw diploid turn count"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.condense", owner="srmech", category="genome",
            summary="CONDENSE a region — SET the chromatin ACCESS marker (0x48 'H') on an EXISTING chromosome (§98 / #1422 / F1246-F1247). Biology's epigenetic packaging gate: the modify-WITHOUT-changing-the-DNA layer ABOVE the coupled-turn content. condense SPLICES the marker into the strand IN-PLACE (a byte-splice, like genome_remove/genome_replace) and PRESERVES the centromere + body sequence — a NUCLEAR chromosome comes out still nuclear (the 0x58 centromere byte-identical, centromere_of unchanged). NO re-mint; reversible with decondense. state = the access state: True/'condensed' -> binary heterochromatin (silenced, level 0); False/'open' -> binary euchromatin (accessible, level 1); a (num, den) tuple -> a GRADED accessibility level in [0,1] (exact reduced rational; composes multiplicatively with a graded gene in gene_express_levels; Class-N, NO float, NEVER abs). PLACEMENT is scope: region=None (default) -> HEAD scope, the marker goes right after the opening telomere and silences the WHOLE chromosome (the X-inactivation / master case); region=k (int) -> INTERIOR STRETCH before the k-th data turn; region='<gene_label>' -> before that gene's cap (silences that gene onward). label picks the chromosome in a multi-chromosome strand. Native-dispatched cap bytes (srmech_genome_chromatin). Class A (cap) + Class C (the access which-way) + Class N (the level).",
            parameters=(P("strand", "Sequence[HV]", True, "an in-memory chromosome / genome strand (from chromosome / mint / diploid / genome)"),
                        P("coupling", "HV", False, "keyword-only; the held invariant (gives the leaf width dim; defaults to the strand's block width)"),
                        P("state", "bool | tuple", False, "keyword-only; True/'condensed' (silenced) [default], False/'open' (accessible), or a (num, den) graded level in [0,1]"),
                        P("region", "int | str | None", False, "keyword-only; None -> whole chromosome (head scope), an int -> before the k-th data turn, a gene-label str -> before that gene's cap (interior stretch)"),
                        P("handle", "str", False, "keyword-only; the inline epigenetic handle (default 'chr')"),
                        P("label", "str", False, "keyword-only; which chromosome in a multi-chromosome strand (required when there is more than one)")),
            returns=R("list", "a NEW strand with the chromatin cap spliced in (the input is unchanged); recover the state with chromatin_of, clear it with decondense"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.decondense", owner="srmech", category="genome",
            summary="DECONDENSE — CLEAR the chromatin ACCESS marker(s), the inverse of condense (§98 / #1422). Splices out every 0x48 chromatin cap (or only those inside the label chromosome), PRESERVING the centromere + body sequence — so a condensed-then-decondensed NUCLEAR chromosome is byte-identical to the original mint (NO re-mint). Returns a NEW strand (the input is unchanged). coupling is accepted for signature symmetry (the clear is a pure byte-splice). This is biology's chromatin remodelling back to accessible euchromatin — modify the ACCESS, not the DNA. Class C (the splice) over the strand.",
            parameters=(P("strand", "Sequence[HV]", True, "an in-memory chromosome / genome strand carrying one or more 0x48 chromatin caps"),
                        P("coupling", "HV", False, "keyword-only; accepted for signature symmetry with condense (the clear is a pure splice; unused)"),
                        P("label", "str", False, "keyword-only; clear only the chromatin marks inside this chromosome (default None = the whole strand)")),
            returns=R("list", "a NEW strand with the chromatin cap(s) spliced out (the input is unchanged)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.chromatin_of", owner="srmech", category="genome",
            summary="Recover a chromosome's FIRST chromatin ACCESS state (§98 / #1422) — the inverse read of the chromatin gate, or None if it carries no chromatin marker (an all-euchromatin, fully-accessible chromosome; the default). Scans for the interior 0x48 cap, reads its (chromatin_type, num, den) accessibility level + the number of DATA TURNS before it (the scope: 0 -> whole-chromosome, >0 -> a stretch). Returns {type: 'binary'|'graded', state: 'open'|'condensed'|'graded', level: (num, den), handle: str, at: int, scope: 'chromosome'|'stretch'} or None. NEVER MUTATES (a READ — biology reads the packaging, it does not rewrite the DNA). Native-dispatched (the C peer srmech_genome_chromatin_of does the scan; the handle is read inline in Python — the composition).",
            parameters=(P("strand", "Sequence[HV]", True, "a chromosome strand (possibly carrying a 0x48 chromatin cap, from condense)"),
                        P("coupling", "HV", False, "the held invariant (optional; the leaf width is read from the strand's block width)")),
            returns=R("dict", "{type, state, level: (num, den), handle, at, scope} — or None if the strand has no chromatin marker"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.accessible", owner="srmech", category="genome",
            summary="The COMPUTED accessibility LEVEL (num, den) of a chromosome under cell_state (§98.1/G1 / rc274) — the op⊗operand theorem at the CHROMATIN scale, the parallel of gene_express one gate OUTWARD: the SAME genome under a DIFFERENT cell_state reads a DIFFERENT accessible level (facultative heterochromatin — the Barr body / X-inactivation). Scans for the FIRST interior chromatin cap (0x48, the region head gate) and returns its computed accessibility: a CONSTITUTIVE cap (access_gate_type == NONE — the pre-rc274 default; centromeric / telomeric H3K9me3 heterochromatin) reads its STATIC stored level, CONSTANT in cell_state (EXACTLY the pre-rc274 read); a FACULTATIVE cap (a klein4 / boolean / threshold gate set via condense(state={...}) — the H3K27me3-Polycomb X-inactivation analog) reads its WHEN-OPEN level iff the gate FIRES under cell_state (the SAME §129/§130/§131 gene-gate evaluators applied to the chromatin cap), else (0, 1) (silenced); a chromatin-FREE strand reads (1, 1) (default euchromatin, fully accessible). num > 0 is 'open' (Class-K: the sign of the level numerator). A READ — the strand is byte-identical after (biology reads the packaging, it does not rewrite the DNA). cell_state is a non-negative exact int (Class-I bitwise; each set bit a present condition; no float, never abs). This makes gene_express / the rc269 demand-load skip cell-state-conditional — WHICH regions are condensed is now a function of cell_state, evaluated on a SINGLE seek from the already-paged chromatin cap (bounded I/O preserved). Native-dispatched per-cap (byte-identical C peer srmech_genome_chromatin_access); the pure _chromatin_access is the complete alternative + oracle. Attests facultative heterochromatin as ONE facet (X-inactivation / the Barr body — Chadwick & Willard 2004, PNAS 101:17450, PMC534659, OA; constitutive-vs-facultative — Brown, Genomes, NBK21137, OA). Class-M (read / projection) over Class-K (the num>0 sign) + Class-I (bitwise cs&act) + Class-N (the exact-rational level).",
            parameters=(P("strand", "Sequence[HV]", True, "a chromosome / genome strand (possibly carrying a 0x48 chromatin cap, from condense with a constitutive or §98.1/G1 facultative state)"),
                        P("cell_state", "int", True, "the applied cell-state — a non-negative exact int (Class-I bitwise; each set bit a present condition); the facultative access gate is evaluated under it (a constitutive cap ignores it)"),
                        P("coupling", "HV", False, "keyword-only; the held invariant (optional; the leaf width is read from the strand's block width)")),
            returns=R("tuple", "(num, den) — the computed accessibility level in [0, 1]; num > 0 is open (accessible), (0, 1) is silenced under this cell_state, (1, 1) is a chromatin-free / fully-open default"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.mint", owner="srmech", category="genome",
            summary="The explicit alias of genome() — the biology-aware tooling-picks build (rc260 rename / §95c / #1407 / F1244). BYTE-IDENTICAL to genome(): per kernel the attested encode_shape criterion (F715, no magic number) decides plasmid-vs-nuclear — a plasmid-scale kernel (tome/mobius, <=4 leaves) stays a Tier-1 PLASMID chromosome (the same shape plasmid() builds); a eukaryotic-chromosome-scale kernel (quad_strand, >=5 leaves) is MINTED as a Tier-2 NUCLEAR chromosome with an interior centromere carrying its global orientation (content-address folded to a Klein-4 sector, sha256(raw leaves)[0] & 3). RC260 NAMING: genome() is the umbrella noun (default smart constructor); mint() is the explicit 'structured build' name for the SAME behaviour (the mint-vs-append vocabulary); plasmid() is the pure all-plasmid builder. See the picks first with mint_plan. The chromosomes= multi-gene form defers to plasmid() (all plasmids). Native-dispatched (byte-identical C peer srmech_genome_mint — a C-only host mints end-to-end). Class A (content-address) + Class C (orientation) + composition of chromosome/centromere. §101 (rc275): an in-process progress= callable (Python-only kwarg, NOT an MCP wire param) fires a per-kernel MINTING heartbeat + graceful abort — a truthy return CANCELS and returns the VALID PARTIAL strand (the whole chromosomes minted so far); on the native path via the srmech_genome_mint_progress ctypes trampoline (byte-parity with the pure loop).",
            parameters=(P("kernels", "dict", False, "{label: leaves} mapping OR [(label, leaves), ...] sequence (insertion order = strand order); pass kernels OR chromosomes"),
                        P("coupling", "HV", True, "the held invariant every turn is coupled through"),
                        P("chromosomes", "Sequence[tuple]", False, "keyword-only; the multi-gene form [(label, [(gene_label, gene_leaves), ...]), ...] — defers to plasmid() (all plasmids); pass kernels OR chromosomes"),
                        ET_PARAM),
            returns=R("list", "the genome strand (a flat list of Klein-4 vectors: per kernel a plasmid chromosome or a centromere-minted nuclear one), recovered with partition"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.mint_plan", owner="srmech", category="genome",
            summary="WATCH the tooling pick each kernel's chromosome SHAPE (§95c / #1407 / F1244) — introspection that BUILDS NOTHING (so the choice is visible before committing; 'we watch it happen so we know it does it'). The genome architecture builds into chromosomes as they fit: we don't pick the shape, the kernel's biology-analog scale (via the ATTESTED encode_shape, no magic number) does — tome/mobius (<=4 leaves) is plasmid-scale -> Tier-1 plasmid; quad_strand (>=5 leaves) is eukaryotic-chromosome-scale -> Tier-2 nuclear with a centromere (orientation = the content-address sha256(raw leaves)[0] & 3). NEVER MUTATES (a pure classification read). Composes encode_shape (C-dispatched) + the content-address.",
            parameters=(P("kernels", "dict", True, "the mint() input — {label: leaves} mapping OR [(label, leaves), ...] sequence"),),
            returns=R("list", "[{label, n_leaves, shape, tier, centromere: bool, orientation: int|None, reason}, ...] in kernel order (shape is the derived cap_kind plasmid/nuclear; orientation is the assigned global which-way for nuclear kernels, None for plasmids)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.integrate", owner="srmech", category="genome",
            summary="Integrate a PROVIRUS (a chromosome strand) INTO a host genome strand — the viral-integration analog (§95.1d / #1407 / F1244), the coherency-translation-layer. Biology: a retrovirus (a Tier-1 PLASMID genome — telomere-capped, no centromere) integrates into a eukaryote's DNA (Tier-2 — NUCLEAR / DIPLOID) and is thereafter part of it; we watch it, so ONE shared cascade spans the levels. In srmech that coherence is FREE: rc258 centromere, rc259 diploid, and the mint umbrella ALL couple every turn through the SAME the_one (one k=3 cascade at different rungs), so a plasmid provirus simply becomes another chromosome and EVERYTHING still recovers — partition recovers every chromosome, centromere_of still reads the host's nuclear chromosome, recover_diploid still recovers its diploid, and the provirus recovers too. That is the translation between the Tier-1 and Tier-2 levels: no conversion needed because they are the same cascade. §135/rc273 (F1251) COMPATIBILITY GATE: horizontal transfer has EMPIRICAL BOUNDARIES — attested bacterial genomics (Shropshire et al.) measured CG307 plasmids shared with other clonal groups EXCEPT CG258 (segregated), so HGT is NOT universal. integrate now CHECKS host<->provirus compatibility BEFORE splicing and HONEST-DECLINES on incompatibility (returns None — a clean refuse, inform-don't-crash, mirroring telomere_tick senescence — leaving the host UNCHANGED, not forcing every element into every host). The DEFAULT predicate is the F1244 coherence contract made checkable: host + provirus must share the COUPLING WIDTH (== coupling / leaf_dim) — two genomes at different widths were coupled through different invariants and cannot cohere (an incompatible replicon, the CG258 analog); this is a Class-K/C equality read, never abs(). Python callers may ALSO pass a compatible=(host, provirus)->bool hook to add a domain replicon/lineage barrier (checked IN ADDITION to width; both must pass) — this is an IN-PROCESS Python affordance, NOT an MCP wire parameter (a callable cannot cross JSON-RPC), so it is not in the parameter list. A COMPATIBLE provirus integrates EXACTLY as rc262 (the gate adds ONLY a refuse path — full back-compat). host is a genome strand (any mix of plasmid/nuclear/diploid); provirus is a chromosome strand opening with a boundary cap (from chromosome / plasmid / mint / diploid); at is the host CHROMOSOME INDEX to insert before (0-based; default None = after the last). BOTH must share the_one (the coherence contract). Strand splicing (no re-coupling); a C-only host integrates identically via the srmech_genome_integrate C peer (rc276 / #891 / G4 — the stage-2 SPLICE primitive: it scans the host's boundary caps, resolves the same at->locus, applies the same width-coherence gate, and concatenates the two genomes' self-describing chromosome regions byte-identically), and when HAS_NATIVE this Python path DISPATCHES the splice to that peer (byte-identical whether native or pure). Class C (the integration) o Class K (the coherency-width gate) composing the C-built chromosome strands.",
            parameters=(P("host", "Sequence[HV]", True, "a genome strand — any mix of plasmid / nuclear / diploid chromosomes (from genome / plasmid / mint)"),
                        P("provirus", "Sequence[HV]", True, "a chromosome strand opening with a boundary cap (from chromosome / plasmid / mint / diploid), coupled through the SAME coupling as host"),
                        P("at", "Optional[int]", False, "keyword-only; the host CHROMOSOME INDEX to insert the provirus before (0-based; default None = integrate after the last chromosome)")),
            returns=R("Optional[list]", "the combined genome strand (host with the provirus spliced in at the chromosome boundary, recovered with partition) on a COMPATIBLE integration, else None (the honest-decline; host unchanged) on an incompatible one"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.amplify", owner="srmech", category="genome",
            summary="Set a gene's COPY NUMBER (multiplicity) — the IS26-amplification analog (UPSTREAM §135/rc273 / F1251). F1251 read attested bacterial genomics (Shropshire et al.): IS26-mediated amplification RAISES a resistance gene's COPY NUMBER — the genome stores HOW MANY COPIES, a MULTIPLICITY annotation (a count), NOT N physical duplicated strands. amplify walks chrom (a chromosome strand from chromosome(genes=...), or any genome strand), finds the FIRST plain GENE cap (0x47) whose inline label == label, and returns a NEW strand with that cap rewritten to carry n inline (the gene's data turns + every other block byte-copied unchanged; the strand LENGTH is unchanged — a count, not N strands). The count rides in what was the cap's NUL padding, RIGHT AFTER the label's NUL (the §129 regulatory-mask / §127 active-count placement), so partition / recall / gene_express / genome_census all still read the cap as the SAME always-expressed plain gene (the copy-number is TRANSPARENT to them, Python AND C — srmech_genome_gene_express returns on the 0x47 marker before reading any field), and the count survives genome_save / reload / integrate byte-exact. n == 1 (the default present-once) rewrites to the BYTE-IDENTICAL plain gene cap (no field spent), so amplifying to 1 is an identity and a plain gene IS copy-number 1; only n >= 2 spends the 8-byte uint64 BE field (the §129 dual-read discipline, one field over). The on-disk genome format version STAYS 15 (an additive field in existing NUL padding, NO new marker / block kind). Read the count back with copy_number_of. n is a Class-I/N exact integer >= 1 (a multiplicity is never signed — no float, never abs). Raises ValueError if n < 1 or no plain gene named label is found. Pure composition over the C-built strand (a cap rewrite + byte-copy, like mint_strand) — byte-identical whether chrom came from the native or pure builders. C-DISPATCHED since rc281 (srmech_genome_amplify): the whole op has its own C entry point, so a bare-C host can WRITE the copy-number axis (rc273 shipped it Python-only because the field is transparent to existing C readers — transparent-to-readers is not C-host parity).",
            parameters=(P("chrom", "Sequence[HV]", True, "a chromosome strand (from chromosome(genes=[(label, leaves), ...], coupling)) or any genome strand carrying the plain gene to amplify"),
                        P("label", "str", True, "the plain gene's inline label (the 0x47 GENE cap whose copy-number to set)"),
                        P("n", "int", True, "the copy number (multiplicity) to record — a Class-I/N exact integer >= 1 (n == 1 is byte-identical to a plain gene; n >= 2 spends the uint64 BE field)")),
            returns=R("list", "a NEW strand with the named gene's cap carrying copy-number n (same length as chrom; every other block byte-identical)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.copy_number_of", owner="srmech", category="genome",
            summary="Read a gene's COPY NUMBER (multiplicity) — the reader companion to amplify (UPSTREAM §135/rc273 / F1251). Walks chrom (a chromosome / genome strand), finds the FIRST plain GENE cap (0x47) whose inline label == label, and returns its exact copy-number: the uint64 big-endian count carried RIGHT AFTER the label's NUL, or 1 (present-once, the DEFAULT) for a plain gene / a pre-rc273 genome (all-NUL padding == stored 0 == copy-number 1). So a gene that was never amplified — and every gene in a genome written before rc273 — reads as copy-number 1 (back-compat), and a gene amplified to n reads back exactly n. A READ — the strand is byte-identical after. Class-I/N exact integer (no float, never abs). Raises ValueError if no plain gene named label is found. C-DISPATCHED since rc281 (srmech_genome_copy_number): the READ half of the same parity correction, so a bare-C host can GET the axis and not just skip past it.",
            parameters=(P("chrom", "Sequence[HV]", True, "a chromosome / genome strand carrying the plain gene whose copy-number to read"),
                        P("label", "str", True, "the plain gene's inline label (the 0x47 GENE cap to read)")),
            returns=R("int", "the gene's exact copy number (multiplicity) — 1 for a plain / un-amplified / pre-rc273 gene, else the amplified count n"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.recall", owner="srmech", category="genome",
            summary="Recover a kernel's leaves from a telomere-capped chromosome strand (F713/F715) — the exact inverse of chromosome. Walk the strand; skip every element equal to the telomere cap (the non-data delimiter) and re-bind the_one (the reversible quad_turn again) on each coupled data turn to recover the original leaf. recall(chromosome(leaves, one, label=L), one, telomere(L, len(one))) == leaves. Matching the cap by VALUE (not position) is what lets one recall reach into a multi-chromosome genome strand.",
            parameters=(P("strand", "Sequence[HV]", True, "a telomere-capped chromosome strand (from chromosome)"),
                        P("coupling", "HV", True, "the held invariant the turns were coupled through"),
                        P("telomere", "HV", True, "the telomere cap delimiting the chromosome (skipped, not decoded)"),
                        ET_PARAM),
            returns=R("list", "the recovered kernel leaves (Klein-4 vectors), in order"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genes", owner="srmech", category="genome",
            summary="Recover [(gene_label, gene_leaves), ...] from a multi-gene chromosome (F730/S43) — the inverse of chromosome(genes=..., coupling). Walk the strand: a GENE_FRAME_TAG header (first byte > 3, so never a Klein-4 turn whose bytes are all <= 3) opens a new gene whose label is read back with tlv_unpack; each coupled data turn until the next header (or the end) is re-bound through the_one (the reversible quad_turn) to recover that gene's leaf. Leading element(s) before the first gene header are the chromosome's telomere cap (a delimiter, not data) and are skipped — so genes needs only the strand + coupling, no cap argument. Use genes (not recall) on a multi-gene chromosome.",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-gene chromosome strand (from chromosome(genes=...))"),
                        P("coupling", "HV", True, "the held invariant the gene turns were coupled through"),
                        ET_PARAM),
            returns=R("list", "[(gene_label:str, gene_leaves:list[HV]), ...] in strand order"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome", owner="srmech", category="genome",
            summary="Build a genome — the BIOLOGY-AWARE UMBRELLA that lets the tooling PICK each chromosome's shape by modeling biology (rc260 rename, §95.2 / #1407). The umbrella noun + default smart constructor: per kernel the attested encode_shape criterion (F715, no magic number) decides plasmid-vs-nuclear — a plasmid-scale kernel (tome/mobius, <=4 leaves) stays a Tier-1 PLASMID chromosome (no centromere), a eukaryotic-chromosome-scale kernel (quad_strand, >=5 leaves) is MINTED as a Tier-2 NUCLEAR chromosome with an interior centromere carrying its global orientation (content-address folded to a sector). A genome strand IS a strand (list of Klein-4 vectors); recover with partition (the reader is format-agnostic). RC260 RENAME (breaking): genome was the pure all-plasmid builder — that is now plasmid(); mint() is the explicit alias of this umbrella. kernels is a dict {label: leaves} or (label, leaves) pairs. Composes chromosome + centromere (Class A + Class C + Class M).",
            parameters=(P("kernels", "dict", True, "{label: leaves} — each kernel's leaves are Klein-4 vectors (one tome each)"),
                        P("coupling", "HV", True, "the held invariant every turn of every chromosome is coupled through"),
                        ET_PARAM),
            returns=R("list", "the flat genome strand: per kernel a plasmid chromosome or a centromere-minted nuclear one, recovered with partition"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.plasmid", owner="srmech", category="genome",
            summary="Build a genome of pure PLASMID chromosomes — biology's plasmid (F715; the rc260 rename of the old all-plasmid genome, §95.2 / #1407). The explicit 'I want plain plasmids' builder: each (label, leaves) kernel becomes a telomere-capped Tier-1 plasmid chromosome (append-friendly, NO centromere — biology's small, appendable plasmid), all concatenated into one self-describing strand; recover with partition. genome() is the biology-aware umbrella that PICKS plasmid-vs-nuclear per kernel; mint() is its explicit alias; plasmid() is the pure-plasmid constructor. kernels is a dict {label: leaves} or (label, leaves) pairs (insertion order = strand order). Native-dispatched (byte-identical C peer srmech_genome_genome). Composes chromosome (Class A cap + Class M coupling).",
            parameters=(P("kernels", "dict", False, "{label: leaves} — each kernel's leaves are Klein-4 vectors (one tome each); pass kernels OR chromosomes"),
                        P("coupling", "HV", True, "the held invariant every turn of every chromosome is coupled through"),
                        P("chromosomes", "Sequence[tuple]", False, "keyword-only; the multi-gene form [(label, [(gene_label, gene_leaves), ...]), ...] (pass kernels OR chromosomes)"),
                        ET_PARAM),
            returns=R("list", "the flat genome strand: concatenated [telomere cap, turns...] per plasmid chromosome"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.partition", owner="srmech", category="genome",
            summary="Recover every kernel from a multi-kernel genome strand — the inverse of genome (F715). Walk the strand; each element equal to one of labels' telomere caps starts a new chromosome partition, and the coupled turns until the next cap are that kernel's leaves (re-bound through coupling — reversible quad_turn). Returns {label: leaves}. partition knows ALL the caps, so (unlike a single-cap recall) it does not mistake one chromosome's cap for another's data: partition(genome({a:A,b:B}, one), one, [a,b]) == {a:A, b:B}.",
            parameters=(P("strand", "Sequence[HV]", True, "a multi-kernel genome strand (from genome)"),
                        P("coupling", "HV", True, "the held invariant the turns were coupled through"),
                        P("labels", "list", True, "the chromosome labels whose telomere caps partition the strand"),
                        ET_PARAM),
            returns=R("dict", "{label: leaves} — each kernel's recovered Klein-4 leaves, in order"),
        ),

        # ────────────────────────────────────────────────────────────
        # Genome persistence — UPSTREAM §41. The helix grows ON DISK: a
        # genome directory holds a self-describing append-only body
        # (turns.bin; §55/v3 bit-packs data turns 4 Klein-4 symbols/byte)
        # + an MPR-attested manifest catalog. Reads are paged + BOUNDED
        # (every read re-hashes the bytes it touched vs the manifest).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.genome.genome_save", owner="srmech", category="genome",
            summary="Persist a genome strand to a directory (UPSTREAM §41 / §44 / §55 / §56). SCANS the strand for its inline CHROM caps (§44 — the strand self-describes; chromosome labels are recovered inline), writes a SELF-DESCRIBING body to path/turns.bin (§55/v3: each block's FIRST byte keys its kind + width — a leaf_dim-byte CHROM/GENE cap, or a BIT-PACKED data turn of 1+ceil(leaf_dim/4) bytes carrying 4 Klein-4 symbols per byte; legacy v2 byte-per-symbol turns stay readable in the same walk — no length prefixes), and writes a DERIVED MPR-attested catalog to path/manifest.json (§56/v4: format_version=4, leaf_dim, n_turns = strand block count, coupling hash+hex, a regions array {byte_offset, byte_len, sha256} one per chromosome — the full-region digest, == the chromosome's .chr/AMSC provenance unit — and body_sha256 = the REGION CHAIN Hn=sha256(Hn-1||region_n) that an append maintains in O(1); plus per-chromosome cap_sha256 / leaf_count / byte_offset / byte_len). The strand is the SSoT; the manifest is an optional .fai-style cache, rebuildable by scanning the body (the chain is body-derivable). v2/v3 manifests stay READ-compatible. Multi-gene chromosomes carry their gene boundaries INLINE as GENE caps (no gene-index sidecar). coupling is content-addressed into the manifest so a load re-anchors without re-deriving it. Returns the manifest data dict. numpy-free; hashes via sha256_bytes.",
            parameters=(P("strand", "Sequence[HV]", True, "the flat genome strand to persist (from genome)"),
                        P("path", "str", True, "the genome DIRECTORY to write (created if absent; gets manifest.json + turns.bin)"),
                        P("coupling", "HV", True, "the held invariant every turn is coupled through (content-addressed into the manifest)"),
                        P("labels", "list", False, "optional, back-compat; when given VALIDATES the scanned chromosome set (labels are discovered inline)"),
                        ET_PARAM),
            returns=R("dict", "the manifest data {format_version=4, leaf_dim, n_turns, coupling, body_sha256 (region chain), regions, chromosomes}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.upgrade_v15_to_v16", owner="srmech", category="genome",
            summary="Migrate a v<=15 genome directory to on-disk format v16 IN PLACE (UPSTREAM §55 / §Q8; rc312) — the Q8 on-disk-format upgrade. rc311 wired the Q8 carrier into the genome as an element_type coupling path but the on-disk WIRE still assumed 2-bit klein4 turns; v16 adds a SECOND data-turn packing (a Q8 turn 3-bit-packs under Q8_PACKED_TURN_MARKER 0x38, the klein4 turn keeps the 2-bit PACKED_TURN_MARKER 0x51) + a manifest carrier field. A v15 genome is ALWAYS klein4 (2-bit turns), and v16's klein4 packer is BYTE-IDENTICAL, so the turns.bin BODY needs NO repack: a v15 turn (bytes 0..3, sign bit 0) is EXACTLY the winding-0 / Lk-0 slice of a v16 Q8 turn (q8_project_v4(turn) == turn and every winding sign bit is 0). The upgrade is therefore a manifest RE-STAMP — re-derive the .fai head by SCANNING the unchanged body (§44 — the strand is the SSoT), which now stamps format_version=16 + the derived carrier ('klein4' / 'q8'). Because the body is untouched and body_sha256 is a pure function of the body (the region CHAIN since v4), the ONLY on-disk bytes that MOVE are the manifest's format_version + carrier fields; turns.bin is byte-identical. Idempotent — a v16 genome re-stamps to itself; REFUSES to downgrade a genome newer than this build. coupling= is only needed for a manifest-LESS genome (its length is the leaf width — you can upgrade a turns.bin shipped alone). Returns the re-derived manifest data dict (format_version=16). The migrate-on-read precedent of the v11->v12 head-only upgrade; numpy-free; hashes via sha256_bytes.",
            parameters=(P("path", "str", True, "the genome DIRECTORY to upgrade in place (its manifest.json is re-stamped to v16; turns.bin is byte-untouched for a klein4 genome)"),
                        P("coupling", "HV", False, "keyword-only; the held invariant — only needed to rebuild a manifest-LESS genome (its length is the leaf width)")),
            returns=R("dict", "the re-derived manifest data (format_version=16, carrier, leaf_dim, n_turns, coupling, body_sha256, regions, chromosomes)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_load", owner="srmech", category="genome",
            summary="Reconstruct a genome from a directory (UPSTREAM §41) — returns (strand, coupling, labels). labels=None loads the WHOLE genome: streams turns.bin block-by-block (RAM bounded by the active block, not the whole file) and re-hashes the streamed body against the manifest body_sha256. A subset labels=[...] is a PAGED read: it seeks to each requested chromosome's byte_offset and reads only its byte_len bytes (RAM bounded by the largest single chromosome), re-hashing that region's cap against cap_sha256. Bounding IS integrity — a flipped / truncated / re-ordered byte raises GenomeBoundingError. The returned strand is byte-for-byte the saved strand for the requested chromosomes; coupling is rebuilt from the manifest's stored block and verified against its hash.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("labels", "list", False, "keyword-only; chromosome subset to page in (None = load all, streamed)")),
            returns=R("tuple", "(strand, coupling, labels) — the reconstructed genome (byte-exact for the requested chromosomes)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_catalog", owner="srmech", category="genome",
            summary="Read the catalog of a genome (UPSTREAM §41 / §44 / §56 / §96). When manifest.json is present this is the cheap, body-free read — it returns the manifest data dict (§56/v4: leaf_dim, n_turns, body_sha256 = the region CHAIN, coupling hash+hex, a regions array {byte_offset, byte_len, sha256}, and per-chromosome cap_sha256 / leaf_count / byte_offset / byte_len / §96 cap_kind) WITHOUT opening turns.bin. §96: cap_kind ∈ {plasmid, nuclear, diploid} is the per-chromosome classification DERIVED on the SAME §44 scan (plasmid = plasmid-scale / nuclear = an interior centromere / diploid = a diploid-telomere opener; nuclear > diploid > plasmid) — a NEW additive field, no format bump (v12 head-only manifests derive it on read). rc271 (F1251) adopts the field's own names — plasmid (was 'stick') / nuclear (was 'minted'); opt back into the old names with genome.set_type_aliases / load_type_aliases_toml (a pure Python presentation layer; the C output stays canonical). §44: when the manifest is ABSENT the catalog is REBUILT by scanning the self-describing body (the strand is the SSoT, the manifest an optional .fai cache; the region chain is body-derivable, so the rebuild reproduces the manifest byte-identically); that rebuild needs coupling= (its length is the leaf width) and reads turns.bin once. The manifest is an MPRRecord (MPR v1) that passes validate_mpr_record (its response_sha256 IS the body_sha256 chain head). v2/v3 manifests read compatibly. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),),
            returns=R("dict", "the manifest data (chromosome index + integrity hashes + §96 per-chromosome cap_kind), read from manifest.json or rebuilt by scanning turns.bin"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_census", owner="srmech", category="genome",
            summary="Census ONE genome — the biology-native per-genome roll-up (UPSTREAM §96). Answers what is IN a genome and how it partitions the way biology asks: how many chromosomes, of which TYPE (plasmid = a plasmid-scale accessory/mobile append-only chromosome / nuclear = a core Tier-2 chromosome with an interior centromere / diploid = a diploid-telomere pair), how many total leaves, and a STRUCTURAL nuclear-vs-organelle topology read. A thin roll-up over genome_catalog (the TYPE rides the catalog's ONE body scan via the §96 cap_kind — NO O(n) per-chromosome loads). Returns {path, n_chromosomes, types:{plasmid,nuclear,diploid}, chromosomes:[{label,type,leaf_count}], total_leaves, topology}. topology (INTEGER read, no libm): any nuclear/diploid → 'nuclear-like' (a eukaryotic nucleus); else n>0 and total_leaves<=8*n → 'organelle-like' (a small all-plasmid mitochondrion/chloroplast plasmid genome); else n>0 → 'plasmid/prokaryote-like'; else 'empty'. rc271 (F1251) adopts the field's own names — plasmid (was 'stick') / nuclear (was 'minted'); genome.set_type_aliases / load_type_aliases_toml re-present the old names (a pure Python layer; the C output stays canonical). srmech reads the SHAPE (the inline cap markers); the caller assigns the ROLE. coupling= is only needed for a manifest-less genome. C↔Python 1:1 (srmech_genome_census). numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("coupling", "HV", False, "keyword-only; the held invariant — only needed to rebuild a manifest-less genome (its length is the leaf width)")),
            returns=R("dict", "the census {path, n_chromosomes, types, chromosomes, total_leaves, topology}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_content", owner="srmech", category="genome",
            summary="The genome's CONTENT count, DERIVED from the strand (rc345, task T964) — the count that survives REPARTITIONING. Returns {path, n_turns, n_chromosomes, n_content} with n_content = n_turns - n_chromosomes. WHY THE SUBTRACTION IS EXACT: every chromosome opens with exactly ONE boundary (telomere) cap, and a cap is a leaf_dim-wide BLOCK — i.e. a turn — like any other strand element, so the boundary caps are IN n_turns and subtracting the chromosome count removes the container overhead with NO residual (one cap per chromosome, one turn per cap). Cut fixed content into chromosomes N different ways and n_chromosomes changes (it IS the cut), n_turns changes (one turn per added boundary) and body_sha256 changes (the caps are in the bytes) — so none of the three tells you two genomes hold the same thing; n_content does, exactly. MEASURED over 8 partitionings of 24 leaves at DIM=64 (scratchpad/fusion_test.py): n_turns 25/26/27/28/30/32/36/48, n_content 24 in all eight, 8 distinct body_sha256. READ IT AS 'NOT A CONTAINER', NOT AS 'LEAVES': n_content counts every NON-BOUNDARY block, INCLUDING inline §44 GENE caps and §95a centromeres, so it equals genome_census's total_leaves (which excludes ALL caps) only for a genome whose chromosomes carry no inline caps — the same 24 leaves as 4 genes of one chromosome give n_content 28 against total_leaves 24, and the general law is n_content == total_leaves + n_inline_caps. Use genome_census when you want leaves; use this when you want how much of a strand is not framing. DERIVED, NOT CACHED: n_content is exactly recoverable from the strand, so it is NOT a manifest field and GENOME_FORMAT_VERSION does not move for it (one encoding per datum — a stored copy of a derivable value is a second encoding that can go stale). It reads the counts the §44 way, by SCANNING the self-describing body rather than trusting the head's cached scalars, and therefore inherits the rc342 READ-SIDE INTEGRITY BOUND for free: the scan re-derives the region chain anyway, so holding it against the head's committed body_sha256 costs no extra open, parse, or hash, and a turns.bin modified out of band raises GenomeBoundingError exactly as in genome_catalog / genome_census. A manifest-LESS genome passes through UNBOUND (nothing committed to compare against) and needs coupling= for the leaf width. C↔Python 1:1 (srmech_genome_content). Class-N exact integers; no abs(). numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("coupling", "HV", False, "keyword-only; the held invariant — only needed to scan a manifest-less genome (its length is the leaf width)")),
            returns=R("dict", "the content counts {path, n_turns, n_chromosomes, n_content}, where n_content = n_turns - n_chromosomes is invariant under repartitioning"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_registry", owner="srmech", category="genome",
            summary="Census a ROOT of genomes — the cell / melange census (UPSTREAM §96, ADR-0006). Scans root for genome directories (a dir holding BOTH turns.bin and manifest.json), censuses each (genome_census), and returns them sorted by name: {root, n_genomes, genomes:[<census per genome>]}. This is the 'cell': which genome is the NUCLEUS (nuclear/diploid chromosomes) vs an ORGANELLE (a small all-plasmid plasmid-like genome — a mitochondrion/chloroplast). A dir that OPENS but has no genome subdirs yields n_genomes 0; a root that CANNOT be opened (absent / permission denied / not a directory) raises GenomeBoundingError in BOTH projections (rc294 — through rc292 the native path answered n_genomes 0 with a success status there, so a typo'd corpus path read as an empty corpus). The native path scans via the PAL directory surface (srmech_plat_dir_*, no #ifdef); the pure path uses os/pathlib. coupling= is only needed for manifest-less genomes. C↔Python 1:1 (srmech_genome_registry). numpy-free.",
            parameters=(P("root", "str", True, "a directory holding genome subdirectories (each written by genome_save)"),
                        P("coupling", "HV", False, "keyword-only; the held invariant — only needed to rebuild manifest-less genomes")),
            returns=R("dict", "the cell census {root, n_genomes, genomes} (each genome a genome_census dict), sorted by name"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_append", owner="srmech", category="genome",
            summary="Append ONE chromosome to an existing genome in O(1)-AMORTISED time (UPSTREAM §41 / §55 / §56 — #1245 ask (b)) — the helix grows. Packs leaves into a telomere-capped chromosome (coupled through coupling) and TAIL-EXTENDS turns.bin with its blocks in the §55/v3 packed form (caps verbatim, data turns bit-packed 4 symbols/byte; APPEND-ONLY — prior body bytes are NEVER read, rewritten, or re-hashed, so appending to a v2 genome yields a MIXED body the walk reads as-is). The manifest is updated by APPENDING one chromosome entry + one region entry and EXTENDING the body_sha256 region CHAIN from its prior head in O(1) — no whole-body re-hash, no whole-body re-scan; n_turns grows by the appended block count. Every EXISTING chromosome / region entry stays byte-identical. §56: the per-append cost is bounded by the NEW chromosome's encoding + the (small) manifest rewrite, NOT the genome's total size — so N appends are O(N) total, not O(N²) (the F833 super-linear wall closed). Appending to a legacy v2/v3 genome migrates it to v4 once. Returns the updated manifest data dict. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the new chromosome's label (must not already exist in the genome)"),
                        P("leaves", "Sequence[HV]", True, "the new kernel's Klein-4 leaf vectors"),
                        P("coupling", "HV", True, "the held invariant the new turns are coupled through (dim must match leaf_dim)")),
            returns=R("dict", "the updated manifest data (with the appended chromosome + region entry + O(1)-extended body_sha256 chain)"),
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
            summary="Page ONE multi-gene chromosome's genes back from a genome (F732 / UPSTREAM §44) — the disk counterpart of the in-memory genes(). Pages in only that chromosome's region (RAM-bounded + cap-integrity-checked), then SCANS it for the inline GENE caps (§44 — no gene-index sidecar; the gene boundaries + labels live in the body) and re-binds the_one (rebuilt + hash-verified from the manifest cache, or a coupling override) to recover a list of (gene_label, gene_leaves) — exactly what genes(chromosome(genes=…)) returns in memory. Raises ValueError on a single-kernel chromosome (no inline GENE caps; use genome_window / partition). numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the multi-gene chromosome label whose genes to page in")),
            returns=R("list", "the chromosome's genes as a list of (gene_label, gene_leaves) tuples, in order"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_remove", owner="srmech", category="genome",
            summary="Excise ONE chromosome from a genome IN PLACE (UPSTREAM §45) — biology excises, it does not re-synthesize. Finds the chromosome label's region in the self-describing body (§44 — its CHROM cap + data turns occupy [byte_offset, byte_offset+byte_len)) and splices THAT byte span out of turns.bin, leaving every OTHER chromosome's coupled body bytes byte-identical (no kernel is decoded / re-coupled — the survivors are the same bytes, only relocated). The derived .fai manifest is then rebuilt by scanning the spliced body (§44 — body_sha256 / n_turns and every survivor's byte_offset recomputed; the manifest stays an optional cache). Re-hashes the whole on-disk body against the committed body_sha256 BEFORE the edit (never splice a corrupt body — GenomeBoundingError). coupling= is needed only when manifest.json is absent (its length is the leaf width for the rebuild-by-scan). Raises ValueError if the label is absent or is the genome's only chromosome. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the chromosome label to excise (must not be the genome's only chromosome)"),
                        P("coupling", "HV", False, "the held invariant (only required when manifest.json is absent — its length is the leaf width for the §44 rebuild-by-scan)")),
            returns=R("dict", "the updated manifest data (the excised chromosome gone, survivors' byte_offsets + body_sha256 recomputed)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_replace", owner="srmech", category="genome",
            summary="Replace ONE chromosome's content IN PLACE (UPSTREAM §45). Splices the chromosome label's old byte span out of turns.bin and a FRESH telomere-capped chromosome (leaves coupled through coupling, same label) IN at the same position — every OTHER chromosome's coupled body bytes stay byte-identical (an in-place edit, NOT a whole-genome re-pack). The derived manifest is rebuilt by scanning the new body (§44 — the strand is the SSoT). coupling is REQUIRED (it both re-couples the new leaves AND supplies the leaf width for the §44 rebuild) and must match the genome's leaf_dim. Re-hashes the on-disk body against body_sha256 before the edit (GenomeBoundingError on mismatch). Raises ValueError if the label is absent. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the chromosome label whose content to replace"),
                        P("leaves", "Sequence[HV]", True, "the replacement kernel's Klein-4 leaf vectors"),
                        P("coupling", "HV", True, "the held invariant the new turns are coupled through (dim must match leaf_dim)")),
            returns=R("dict", "the updated manifest data (the chromosome's content replaced in place, body_sha256 recomputed)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_export", owner="srmech", category="genome",
            summary="Export ONE chromosome as a single self-contained .chr file (UPSTREAM §43). Reads the chromosome label's fixed-width region (CHROM cap + coupled data turns; the cap re-hashed against the manifest cap_sha256) and writes it — together with the_one — to out as ONE MPR-attested record (MPR v1; response_sha256 IS the region hash). So a chromosome becomes a self-contained, content-addressed unit: tar it, ship it, genome_import it self-verifying — realising the §43 'chromosome as a bundleable file' goal on top of the §44 self-describing strand. Composes srmech.amsc.format (the MPRRecord + sha256 content-address), NOT a parallel attestation. §44: pass the_one= to export from a manifest-less source genome. Raises ValueError if the label is absent. numpy-free.",
            parameters=(P("path", "str", True, "the genome directory written by genome_save"),
                        P("label", "str", True, "the chromosome label to export as a .chr bundle"),
                        P("out", "str", True, "the output file path for the .chr (one MPR-attested JSON record)"),
                        P("coupling", "HV", False, "the held invariant (only required when the source genome's manifest.json is absent — its length is the leaf width for the §44 rebuild-by-scan)")),
            returns=R("dict", "the .chr data block (format_version / leaf_dim / label / leaf_count / cap_sha256 / coupling hash+hex / region hash+hex)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_import", owner="srmech", category="genome",
            summary="Import a .chr chromosome bundle into a genome at dest (UPSTREAM §43). Reads the MPR-attested .chr (genome_export's output), RE-HASHES its region and its coupling and compares them against the bundle's own attestation — a mismatch is a GenomeBoundingError (self-verifying). Then: if dest has no genome yet, the .chr SEEDS a fresh one (its region becomes turns.bin verbatim, its coupling the coupling invariant); if dest already holds a genome, the chromosome is APPENDED byte-for-byte — which REQUIRES the same coupling invariant (the dest coupling must match the .chr coupling) and a fresh label. The manifest is re-derived by scanning the grown body (§44 — the strand is the SSoT). numpy-free.",
            parameters=(P("chr_path", "str", True, "the .chr bundle file written by genome_export"),
                        P("dest", "str", True, "the dest genome directory (seeded fresh if it has no genome, else appended to)"),
                        P("coupling", "HV", False, "the held invariant (only consulted for a manifest-less EXISTING dest — the §44 rebuild width; the bundle carries its own coupling)")),
            returns=R("dict", "the dest manifest data (the seeded genome, or the existing genome with the imported chromosome appended)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_explode", owner="srmech", category="genome",
            summary="Explode a packed genome into a directory of loose .chr files (UPSTREAM §43; the packed->loose half of git's object model). A genome's turns.bin (the 'packfile') is written out as ONE self-contained, content-addressed .chr bundle per chromosome (the 'loose objects'), named <out_dir>/<label>.chr — each is genome_export's MPR-attested, self-verifying output, so the loose form is inspectable and shippable chromosome-by-chromosome. genome_pack is the inverse. Returns a list of {label, path, region_sha256} dicts in chromosome order. §44: pass coupling= to explode a manifest-less source. Raises ValueError if a chromosome label is not filename-safe. numpy-free.",
            parameters=(P("path", "str", True, "the packed genome directory written by genome_save"),
                        P("out_dir", "str", True, "the output directory for the loose <label>.chr bundles (created if absent)"),
                        P("coupling", "HV", False, "the held invariant (only required when the source genome's manifest.json is absent — the §44 rebuild width)")),
            returns=R("list", "a list of {label, path, region_sha256} dicts, one per chromosome (in the genome's chromosome order)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_pack", owner="srmech", category="genome",
            summary="Pack a directory of loose .chr files into one packed genome (UPSTREAM §43; the loose->packed inverse of genome_explode, git repack-like). Every *.chr bundle in loose_dir is genome_import-ed into dest in CANONICAL sorted-label order, so the packed turns.bin is a well-defined function of the chromosome SET — like a content-addressed packfile, insertion order is NOT preserved (a packed genome is canonicalised to sorted-label order). The first import SEEDS dest (when it has no genome yet); the rest APPEND byte-for-byte; all the bundles MUST share one coupling invariant (the same the_one) — a mismatched .chr is a GenomeBoundingError, a duplicate label a ValueError. Byte-identical to the source iff the source was already in canonical sorted-label order; otherwise re-canonicalises while preserving every chromosome's bytes. Raises ValueError if loose_dir holds no .chr files. numpy-free.",
            parameters=(P("loose_dir", "str", True, "the directory of loose .chr bundles (e.g. genome_explode's output)"),
                        P("dest", "str", True, "the dest packed genome directory (seeded fresh if it has no genome, else appended/merged into)"),
                        P("coupling", "HV", False, "the held invariant (only consulted for a manifest-less EXISTING dest — the §44 rebuild width; each .chr carries its own coupling)")),
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
        ToolEntry(
            name="srmech.amsc.genome.kernel_pack", owner="srmech", category="genome",
            summary="Pack a flat Klein-4 kernel of ANY dimension D into a self-describing strand (UPSTREAM §60 / format v5 — issue #1245 REOPENED, the SIZE-AGNOSTIC KERNEL TRANSLATION LAYER). data is the flat kernel (a sequence of Klein-4 sector symbols {0,1,2,3} — an HV / list / bytes; siona's 8192-dim Klein-4 kernel is the driving case). It is chunked into leaf_dim-wide leaves (ceil(D/leaf_dim); the final leaf zero-padded — encode_shape's criterion generalised to leaf_dim), coupled through coupling into a telomere-capped chromosome, and a §60 KERNEL HEADER block (marker 0x4B, right after the telomere) SELF-RECORDS the kernel's TRUE length D, its element_type (declared enum; 'klein4' today), and its leaf_dim — so kernel_unpack recovers the EXACT kernel with NO caller-supplied length (D lives in the strand, the §44 SSoT — not only the rebuildable manifest cache). Symbols are validated {0,1,2,3} UP FRONT (HV accepts >3 in memory but only Klein-4 turns bit-pack). Returns the flat strand [telomere, kernel_header, turn0, ...]; persist with genome_save. leaf_dim defaults to 256 (>= 14 so the 14-byte header fits); coupling defaults to a deterministic all-ones invariant kernel_unpack reconstructs. numpy-free; no abs(); C peer via genome_save's srmech_genome_* walkers (the 0x4B block is one more self-describing kind).",
            parameters=(P("data", "Sequence[int]", True, "the flat Klein-4 kernel — symbols {0,1,2,3} (HV / list / bytes) of any dimension D"),
                        P("leaf_dim", "int", False, "keyword-only; the leaf (tome) width to chunk into (default 256; must be >= 14 so the §60 header fits)"),
                        P("label", "str", False, "keyword-only; the chromosome label for the packed kernel (default 'kernel')"),
                        P("coupling", "HV", False, "keyword-only; the coupling invariant (width leaf_dim; default the deterministic all-ones invariant kernel_unpack reconstructs)"),
                        P("element_type", "str", False, "keyword-only; the declared element-type enum recorded in the header (default 'klein4' — the genome-native 2-bit symbol)")),
            returns=R("list", "the flat self-describing strand [telomere, §60 kernel_header, coupled turns] — persist with genome_save, recover with kernel_unpack"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.kernel_unpack", owner="srmech", category="genome",
            summary="Recover the EXACT flat Klein-4 kernel from a §60 strand or genome path (UPSTREAM §60 / format v5) — the inverse of kernel_pack. strand_or_path is either the in-memory strand kernel_pack returned, or a genome DIRECTORY a genome_save of one wrote. Reads the §60 KERNEL HEADER (marker 0x4B) for the TRUE length D, recalls the coupled leaves (skipping every cap AND the header), flattens them, and TRIMS to D — so the returned list[int] equals the exact packed kernel of ANY dimension, with NO caller-supplied length (W1 closed: a D=1000 kernel returns 1000 symbols, not the 1024 padded storage). coupling is optional: for a genome PATH with a present manifest it is resolved from the manifest cache; otherwise it defaults to the deterministic all-ones invariant reconstructed from the header's recorded leaf_dim (matching kernel_pack). BACK-COMPAT (the rc114 dual-read pattern): a strand / body with NO 0x4B header (any pre-rc121 genome) reads as element_type=klein4 with D = leaf_count * leaf_dim — no trim, no migration. numpy-free; no abs().",
            parameters=(P("strand_or_path", "list|str", True, "the in-memory kernel_pack strand, OR a genome directory written by genome_save of one"),
                        P("coupling", "HV", False, "the coupling invariant (optional; resolved from a present manifest, else reconstructed as the all-ones default from the header's leaf_dim)"),
                        ET_PARAM),
            returns=R("list", "the exact flat Klein-4 kernel (list[int] of the TRUE length D — trimmed of the final-leaf zero-padding)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_append_kernel", owner="srmech", category="genome",
            summary="Append a newly-taught kernel — WITH its §89 header — to a genome in O(1) AMORTISED (UPSTREAM §89 / format v6 — issue #1261, F1045/F1046). The uniformly-Klein-4 payoff. hv is the flat kernel (Klein-4 sector symbols {0,1,2,3} — an HV / list / bytes) of ANY dimension D; it is chunked into the genome's leaf_dim-wide leaves (final leaf zero-padded) LED by the UNIFORMLY-KLEIN-4 §89 header LEAF (base-4-encoded D + element_type + leaf_dim — _pack_kernel_header_klein4). Because that header is a 100%-Klein-4 leaf, [header, *content] is just a list of Klein-4 leaves — so this FALLS OUT of genome_append (kernel=True, a KERNEL telomere 0x6B opens the chromosome): the chromosome tail-extends turns.bin and folds one region onto the body_sha256 chain in O(1), no whole-body re-hash / re-scan. This is the deliverable a downstream 'teach a kernel -> append it' loop was about to hand-roll: before v6 the §60 0x4B byte-TLV header could NOT ride genome_append (unbinding it via klein4_bind failed 'must be in {0,1,2,3}'); v6 makes the header a Klein-4 leaf so appending a kernel WITH its header is native. Recover the EXACT kernel (trimmed to D) with kernel_unpack. coupling is optional when path has a manifest (resolved from the cache), required for a manifest-less genome (its length is the leaf width). Raises ValueError on a duplicate label or a non-Klein-4 symbol. numpy-free; no abs(); the C peer is genome_append's srmech_genome_append (the 0x6B kernel telomere is one more self-describing cap).",
            parameters=(P("path", "str", True, "the genome directory written by genome_save (grown in O(1))"),
                        P("label", "str", True, "the new kernel chromosome's label (must not already exist in the genome)"),
                        P("hv", "Sequence[int]", True, "the flat Klein-4 kernel to append — symbols {0,1,2,3} (HV / list / bytes) of any dimension D"),
                        P("element_type", "str", False, "keyword-only; the declared element-type enum recorded in the §89 header (default 'klein4')"),
                        P("coupling", "HV", False, "keyword-only; the coupling invariant (optional when a manifest is present; its length is the leaf width for a manifest-less genome)")),
            returns=R("dict", "the updated manifest data (with the appended kernel chromosome + region entry + O(1)-extended body_sha256 chain)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.graph_to_kernel", owner="srmech", category="genome",
            summary="Serialise a sparse SIGNED INTEGER graph (the directed Class-L Laplacian) into a packed genome chromosome + its true symbol count (#1390 item 2). vocab_size + edges [(i,j),...] + int weights[metric] + optional signed charges[direction] + optional node_ids label table + optional extras metadata are folded into a SELF-DESCRIBING (count-headered) flat Klein-4 symbol stream — each int base-4 digits behind a 2-symbol length header (<=15 digits = 30 bits; Class-K zig-zag sign on the charge) — then kernel_pack'd into leaf_dim-wide leaves. Returns (strand, n_syms): persist the strand with genome_save, pass n_syms to kernel_to_graph. The domain-free 'store a directed graph as a genome' primitive #231 needs; undirected (charges=None) / unlabeled (node_ids=None) / metadata-free (extras=()) all round-trip. Klein-4 is ONLY the 2-bit on-disk alphabet (no bind/bundle HV stored — F1221 disk rule). numpy-free; no abs() (Class-K zig-zag); byte-identical C peer srmech_graph_kernel_encode.",
            parameters=(P("vocab_size", "int", True, "node count of the graph"),
                        P("edges", "list", True, "[(i, j), ...] directed edge list"),
                        P("weights", "list", True, "parallel int metric (co-occurrence counts)"),
                        P("charges", "list", False, "parallel signed-int direction (w_fwd - w_bwd); None = undirected (all 0)"),
                        P("node_ids", "list", False, "keyword-only; a label table (e.g. glyph ids); None = none"),
                        P("extras", "list", False, "keyword-only; caller metadata ints (e.g. a start anchor); default ()"),
                        P("leaf_dim", "int", True, "keyword-only; the leaf (tome) width to chunk into"),
                        P("label", "str", True, "keyword-only; the chromosome label"),
                        P("coupling", "HV", True, "keyword-only; the coupling invariant (width leaf_dim)"),
                        ET_PARAM),
            returns=R("tuple", "(strand, n_syms) — the packed self-describing strand + its true symbol count (pass both to genome_save / kernel_to_graph)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.kernel_to_graph", owner="srmech", category="genome",
            summary="Recover the directed signed graph from a packed chromosome (or genome path) + its n_syms (#1390 item 2) — the inverse of graph_to_kernel. kernel_unpack's the Klein-4 leaves, trims the leaf-dim padding to n_syms, and decodes the self-describing (count-headered) base-4 payload back into {vocab_size, edges, weights, charges, node_ids, extras} BYTE-EXACT (Class-K un-zig-zag on the charge). coupling is the coupling invariant graph_to_kernel packed with (resolved from a manifest for a genome path). numpy-free; no abs(); byte-identical C peer srmech_graph_kernel_decode.",
            parameters=(P("chroms", "list|str", True, "the graph_to_kernel strand, OR a genome directory a genome_save of one wrote"),
                        P("coupling", "HV", True, "the coupling invariant (as passed to graph_to_kernel; resolved from a manifest for a path)"),
                        P("n_syms", "int", True, "the true symbol count graph_to_kernel returned (trims the leaf-dim padding)"),
                        ET_PARAM),
            returns=R("dict", "{vocab_size, edges, weights, charges, node_ids, extras} — the exact directed signed graph"),
        ),
        ToolEntry(
            name="srmech.amsc.plasmid.plasmid_extract", owner="srmech", category="plasmid",
            summary="STAGE 1 EXTRACT (F1252 / §102) — stream documents into APPEND-ONLY plasmid sections, RETIRING the loose monolithic co-occurrence JSON at the graph-L layer. Each ingest DOCUMENT (a token sequence) becomes ONE Tier-1 PLASMID chromosome: its LOCAL window co-occurrence graph (cooccurrence_topk — window / top-k / cap_slack) is encoded to a §89/v6 KERNEL chromosome (Klein-4 leaves, a 0x6B kernel telomere, NO centromere) and APPENDED to section_store (a genome directory) in §v12 O(1) HEAD-only time — so adding a document appends ONE bounded plasmid section + bumps the head, NEVER re-extracts, and NEVER dumps a 916 MB monolith (this IS persist-genome-native-not-loose-JSON one layer up). The first document SEEDS the store (genome_save); the rest append. Edges use LOCAL node indices but the section's node_ids label table maps each to a GLOBAL vocab id (via the append-only vocab) — so a word shared across sections carries the SAME id (the precondition stage-2 conservation reads); a shared VOCAB chromosome (the karyotype index) records the global word->id table. The heavy per-section compute (graph_kernel_encode -> the §89 KERNEL-region build -> genome_append) rides the ONE bare-C orchestrator srmech_genome_plasmid_extract when HAS_NATIVE (genome-must-exist-in-C: a bare-C host runs stage-1 end-to-end as cooccurrence_topk -> plasmid_extract, zero Python); the pure body (_graph_kernel_encode + genome_append_kernel) is the numpy-free alternative + BYTE-PARITY oracle (the section turns.bin is byte-identical whether native or pure). §101: an in-process progress= callable (a Python-only kwarg, NOT an MCP wire parameter — a callable cannot cross JSON-RPC) fires between whole SECTIONS with phase EXTRACTING (done=sections so far, total=n docs); a truthy return CANCELS cleanly, truncating at a valid chromosome boundary (a partial section is never left; status='cancelled'). Returns {section_store, vocab (grown, append-only), section_count {global_id: n_sections} the integer accumulator stage-2 promotes on, n_sections, sections, status}. leaf_dim (len(coupling)) must be >= 52 (the §89 uniformly-Klein-4 kernel header fits one leaf). Integer/exact (Class-N); no abs(); numpy-free; genome-native (no loose JSON).",
            parameters=(P("docs", "list", True, "the corpus — an iterable of documents, each a token sequence (one section per document, D1)"),
                        P("section_store", "str", True, "the sections genome directory (created on the first document; appended thereafter)"),
                        P("coupling", "HV", True, "the coupling invariant; its length is the store's leaf_dim, which must be >= 52 (the §89 kernel header)"),
                        P("vocab", "list", False, "keyword-only; a mutable GLOBAL word list (append-only), returned grown; None starts fresh"),
                        P("window", "int", False, "keyword-only; the co-occurrence window (default 2)"),
                        P("k", "int", False, "keyword-only; the bounded top-k per node (default 20)"),
                        P("cap_slack", "int", False, "keyword-only; the top-k store cap slack (cap = k*cap_slack; default 4)"),
                        P("label_prefix", "str", False, "keyword-only; the section label prefix (default 'sec')")),
            returns=R("dict", "{section_store, vocab, section_count {global_id: n_sections}, n_sections, sections, status}"),
        ),
        ToolEntry(
            name="srmech.amsc.plasmid.section_counts", owner="srmech", category="plasmid",
            summary="Derive {global_id: n_sections} — how many distinct PLASMID sections each GLOBAL node appears in — by SCANNING a plasmid_extract store's sections (their GLOBAL node_ids tables). The genome-native, SSoT read stage-2 (F1252 rc279) promotes on: a node is CONSERVED iff its section-occurrence count >= k (a plain integer accumulator, no spectral solve — the section-level, extract-time-available analog of the F1250 cross-community participation read). HIGH section-count = shared across many plasmids = the conserved core (NUCLEAR); count == 1 = accessory (stays PLASMID). A node counts ONCE per section it appears in; the shared VOCAB chromosome (the karyotype index) is excluded. rc280 (§102 / F1253) made this scan READ ONLY WHAT IT NEEDS, fixing the ~22-hour derivation the field measured at 240,881 sections (~0.33 s/section). Two costs were removed. FIRST, the catalog was re-derived PER SECTION: a v12 head-only manifest stores no chromosome table, so genome_window derives it by scanning the whole body and re-folding its Merkle chain — once per section is O(P x whole body), quadratic in corpus size, and it dominated everything else; the catalog is now derived ONCE for the whole scan. SECOND, every section's full graph was decoded — edges, weights and charges — to reach a node_ids table that the §89 payload places BEFORE all of them ([vocab_size, n_node_ids] + node_ids + ...); the read is now TARGETED, paging only the node_ids prefix of each region and never touching the edge bytes, so per-section cost is O(node_ids) not O(section). NO FORMAT CHANGE WAS NEEDED (GENOME_FORMAT_VERSION stays 15): the sections were already self-describing, quad_turn uncouples each leaf independently of every other so a prefix of coupled leaves uncouples to exactly the prefix of the symbol stream, and the region's leading-cap integrity bound lives in the first block so a prefix pays the SAME bound as a whole-region read — the targeted read is not a weaker read, it is the same bound over fewer bytes. Together the scan goes from O(P^2 x body) to O(P x node_ids); the counts are BYTE-IDENTICAL to the full-decode derivation and that equivalence is the pinned SSoT check. §101: an in-process progress= callable (a Python-only kwarg, NOT an MCP wire parameter) fires between whole SECTIONS with phase EXTRACTING; a truthy return RAISES SectionCountsCancelled rather than returning a partial — unlike a cancelled encode, whose chromosomes-so-far are a valid shorter genome, a partial COUNT is not a smaller valid count but a wrong one that would silently shift every downstream conservation threshold. STILL THE DELIBERATE FALLBACK, NOT THE HOT PATH: plasmid_extract returns section_count as a free streamed accumulator, so passing it to genome_integrate_plasmids means no scan happens at all; this op exists to RESUME against a store you did not just build and to VERIFY the accumulator against the on-disk SSoT. Dispatches the whole scan to the srmech_genome_section_counts C peer when HAS_NATIVE (a bare-C host derives the counts end-to-end); the pure body is the numpy-free alternative + byte-parity oracle. Integer/exact (Class-N); no abs(); numpy-free.",
            parameters=(P("section_store", "str", True, "a plasmid_extract sections genome directory"),
                        P("coupling", "HV", False, "keyword-only; the coupling invariant (only needed for a manifest-less store — its length is the leaf width)")),
            returns=R("dict", "{global_id: n_sections} — the section-occurrence integer accumulator (stage-2's conservation >= k input)"),
        ),
        ToolEntry(
            name="srmech.amsc.plasmid.conserved_core", owner="srmech", category="plasmid",
            summary="CONSERVE (F1252 / §102 STAGE 2 step 1) — read the section-count distribution and return the CONSERVED CORE node set + the threshold k DERIVED FROM THE DATA. section_count is the {global_id: n_sections} integer accumulator plasmid_extract returns for free (or section_counts re-derives). A node is CONSERVED iff its count >= k -> it joins the NUCLEAR core; the rest stay accessory PLASMID. Expect the ASYMMETRIC minority core (~16/84 — F1251), not a 50/50 split. k IS DERIVED OR DECLINED — NEVER MANUFACTURED: with k='auto' (the default; None is an accepted alias) this MEASURES the ANTIMODE of the section-count histogram — the same gap walk, the same qualifying predicate (a gap at least one bin WIDE with a real mode >= 2 nodes on EACH side) and the same widest-gap tie-break as the rc272 participation antimode (genome._partition_antimode), applied in the count domain. NOTE THE METRIC INVERSION vs participation: there HIGH participation = a community-bridging PLASMID, here HIGH section-count = shared across many plasmid sections = the conserved NUCLEAR core; the metric flips direction, the antimode discipline does not. If no qualifying antimode exists the result is k_source='declined': an EMPTY core, k=0, one_dna_type=True, and NO threshold is invented — the split is NOT forced (the F1250 discipline). THIS DECLINE IS A FIRST-CLASS OUTCOME, NOT A FAILURE, AND THE REAL CORPUS TAKES IT: F1253 measured the section-count curve over the full simplewiki store (1,100,189 ids across 240,881 sections) as singleton 64.6%, >=2 35.4%, >=5 14.5%, >=10 8.4%, >=25 4.3%, >=50 2.7%, >=100 1.7% — successive ratios ~2.4, 1.7, 2.0, 1.6, 1.6 decaying SMOOTHLY, i.e. a heavy-tailed near-power-law shape. A scale-free distribution has no characteristic scale and therefore NO natural antimode, so on such a curve this correctly DECLINES; reporting 'no natural split in this distribution' IS the finding. An explicit integer k yields k_source='policy' — a STATED POLICY CHOICE THE CALLER OWNS, never presented as measured. In particular, choosing k because it reproduces F1251's ~16% core fraction would be POST-HOC NUMEROLOGY, not a derivation: on the F1253 curve k>=5 gives 14.5% against an attested ~16%, but that correspondence is threshold-dependent and is NOT used here to select k. k_source is one of 'derived' / 'declined' / 'policy'. Dispatches the whole read to the srmech_genome_conserved_core C peer when HAS_NATIVE (a bare-C host runs the CONSERVE step end-to-end); the pure body is the numpy-free alternative + parity oracle. HONEST SCOPE: this conservation criterion is a DIFFERENT discriminator from F1250's global cross-community participation antimode (cross-DOCUMENT sharing vs cross-COMMUNITY boundary mass) and their convergence is PENDING validation on the real corpus — it is not claimed here. Class-N exact integer arithmetic; no float, no abs(), no spectral solve.",
            parameters=(P("section_count", "dict", True, "the {global_id: n_sections} integer accumulator (from plasmid_extract, or section_counts)"),
                        P("k", "str", False, "keyword-only; 'auto' (default) ATTEMPTS the antimode derivation and DECLINES when the distribution admits no qualifying split; a positive int is a STATED POLICY CHOICE the caller owns (k_source='policy')")),
            returns=R("dict", "{k, k_source (derived|declined|policy), bimodal, one_dna_type, core, accessory, n_core, n_accessory, histogram, threshold, gap} — core/accessory are sorted GLOBAL id lists"),
        ),
        ToolEntry(
            name="srmech.amsc.plasmid.genome_integrate_plasmids", owner="srmech", category="plasmid",
            summary="STAGE 2 ORGANIZE (F1252 / §102) — sections -> a minted NUCLEAR CORE + retained PLASMIDS. The op that structurally REMOVES the monolithic from-scratch partition from the encode path: it CONSERVES (read the section-count distribution, DERIVE k via the antimode — see conserved_core), PROMOTES (mint the induced core subgraph via genome.mint_strand — the 0x58 centromere at the metacentric p:q split), and MERGES (fold the retained plasmid sections in via genome.integrate). recursive_cut is NEVER called and nothing is ever re-extracted; cost is O(|E|) incremental against O(D*|E|*log n) from-scratch. PASS section_count — IT IS FREE, AND THE ALTERNATIVE IS NOT: plasmid_extract already returns section_count as a streamed integer accumulator built during the append pass, so chaining stage 1 -> stage 2 should hand it straight through (zero re-scan). When omitted this falls back to section_counts, which RE-DERIVES the counts from the sections on disk; rc280 made that fallback O(P x node_ids) instead of the O(P^2 x body) it was (the catalog is derived once, and only each section's node_ids prefix is paged — see section_counts), but it is still a disk scan and still the deliberate path, never the hot one: it exists for RESUMING against a store you did not just build and for VERIFYING the accumulator against the on-disk SSoT. Same for core_edges: supply the per-section global edge lists (as add_plasmid maintains them) to skip the core-harvest read entirely. rc280 also removed the same per-section catalog re-derivation from THIS op's own two reads (the core-subgraph harvest and the section-strand fold), which were each independently O(P x body); the harvest itself still reads whole section bodies, because the edges ARE its payload — the node_ids-prefix technique does not apply there. k='auto' (default) DERIVES the threshold or DECLINES; the returned k_source ('derived' / 'declined' / 'policy') records WHICH, so a caller can never mistake a stated policy choice for a measured one. A declining or UNIMODAL distribution yields ONE-DNA-TYPE: no core is promoted and the plasmids fold as-is (the split is not forced) — and on the real F1253 corpus curve, which is heavy-tailed/near-power-law, that IS the outcome. §101: an in-process progress= callable (a Python-only kwarg, NOT an MCP wire parameter) fires between whole CHROMOSOMES — once with phase MINTING for the core promote, then per section with phase INTEGRATING (done = sections merged, total = P); there is NO scan phase when section_count is supplied. A truthy return CANCELS cleanly: the returned strand is the minted core plus the sections merged so far — a valid, readable shorter organized genome truncated at a chromosome boundary — and out_path is NOT written. Dispatches the mint + fold to the srmech_genome_integrate_plasmids C peer when HAS_NATIVE (byte-identical to the pure fold; a bare-C host runs stage 2 end-to-end). HONEST SCOPE: the conservation criterion (section-count >= k) is a DIFFERENT discriminator from F1250's global participation antimode and their convergence is PENDING validation on the real corpus — this is NOT claimed to reproduce the F1250 participation split. numpy-free; integer/exact; no abs().",
            parameters=(P("section_store", "str", True, "the plasmid_extract sections genome directory"),
                        P("coupling", "HV", True, "the coupling invariant; its length is the store's leaf_dim"),
                        P("section_count", "dict", False, "keyword-only; the FREE streamed accumulator from plasmid_extract — pass it. Omitting it triggers the deliberate O(P*section) section_counts re-derivation"),
                        P("k", "str", False, "keyword-only; 'auto' (default) derives-or-declines; a positive int is a stated policy choice (reported as k_source='policy')"),
                        P("core_edges", "list", False, "keyword-only; the per-section GLOBAL edge lists, to skip the core-harvest read"),
                        P("out_path", "str", False, "keyword-only; genome_save the organized genome here (skipped on cancel)")),
            returns=R("dict", "{strand, k, k_source (derived|declined|policy), bimodal, one_dna_type, core, counts {nuclear, plasmid}, n_sections, n_integrated, histogram, status}"),
        ),
        ToolEntry(
            name="srmech.amsc.plasmid.add_plasmid", owner="srmech", category="plasmid",
            summary="INCREMENTAL STAGE 1 + 2 (F1252 / §102) — add ONE document to an organized genome. The incremental face of the two-stage encode, and the reason there is no monolithic block left to be blind inside: adding a document is (1) a stage-1 append — extract its LOCAL co-occurrence graph and append ONE plasmid section (plasmid_extract; O(doc), O(1) HEAD rewrite), (2) an O(section) integer count bump, (3) a core delta — re-derive k and re-mint ONLY the small conserved core. A global recursive_cut is NEVER run and no document is ever re-extracted; every plasmid section, and the core when it did not change, stay byte-untouched. state is the running organize state this function threads — pass None to start, then feed the returned state back on each subsequent call; it carries {section_count, vocab, labels, core, k, sections}. With cache_edges (default True) the per-section GLOBAL edge lists are kept in state, so a threshold crossing re-filters them in memory and NOTHING is re-read from disk (cost: O(|E|) resident); cache_edges=False trades that memory back for a re-read of the store when core membership changes (the counts and the fast path are unaffected either way). EQUIVALENCE CONTRACT (pinned by the rc279 test): calling add_plasmid D times over D documents produces a BYTE-IDENTICAL organized genome to one genome_integrate_plasmids over the same D sections — the incremental rule is EXACT, not an approximation, because the core subgraph sums per-section edge multiplicities and emits them in canonical sorted order, making it independent of accumulation order. §101 progress= is a Python-only kwarg (NOT an MCP wire param) firing between whole chromosomes. numpy-free; integer/exact; no abs().",
            parameters=(P("section_store", "str", True, "the sections genome directory (created on the first document)"),
                        P("coupling", "HV", True, "the coupling invariant; its length is the store's leaf_dim (>= 52)"),
                        P("tokens", "list", True, "the ONE document being added — a token sequence"),
                        P("state", "dict", True, "keyword-only; the running organize state (None to start; feed the returned state back each call)"),
                        P("k", "str", False, "keyword-only; 'auto' (default) derives-or-declines each add; a positive int is a stated policy choice"),
                        P("window", "int", False, "keyword-only; the co-occurrence window (default 2)"),
                        P("top_k", "int", False, "keyword-only; the bounded top-k per node (default 20)"),
                        P("cap_slack", "int", False, "keyword-only; the top-k store cap slack (default 4)"),
                        P("label_prefix", "str", False, "keyword-only; the section label prefix (default 'sec')"),
                        P("cache_edges", "bool", False, "keyword-only; keep per-section global edge lists in state so a threshold crossing re-filters in memory (default True)")),
            returns=R("dict", "{strand, state, section, k, k_source, core_changed, core, bimodal, one_dna_type, counts {nuclear, plasmid}, n_sections, n_integrated, status}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.mint_strand", owner="srmech", category="genome",
            summary="MINT an ALREADY-PACKED strand — splice a §95a interior CENTROMERE (0x58) into it at the p:q arm-split, turning a Tier-1 PLASMID into a Tier-2 NUCLEAR chromosome (§100 GAP 1 / PR#687 F1249). mint() mints AT BUILD TIME from raw leaves; mint_strand mints a strand that is ALREADY PACKED — a kernel_pack / graph_to_kernel strand (the corpus directed-graph store), any chromosome, or one nuclear community — WITHOUT re-minting it from leaves. This is the capability §100 GAP 1 named as missing: chromosome(packed_strand, centromere=…) REJECTS an already-packed strand (it treats the strand as raw leaves and quad_turn binds the 256-sector telomere cap -> 'klein-4 elements must be in {0,1,2,3}'), and there was no centromere= hook on graph_to_kernel — so a directed-graph chromosome could not be given a p:q centromere (its genome censused {plasmid:2, nuclear:0}). The centromere is an INTERIOR cap; recall / kernel_unpack / kernel_to_graph ALL skip caps (§44), so minting is TRANSPARENT to the payload — the recovered kernel / graph is BYTE-IDENTICAL with or without the centromere. centromere_at is the arm-split in DATA TURNS (default the metacentric midpoint n_turns//2, matching chromosome()'s mint default — position IS the p:q arm-ratio: a 30-turn strand mints (15,15), a 9-turn strand (4,5)); orientation is the global 4-way which-way 0..3 (default sha256(recovered leaves)[0]&3 — the SAME Class-A->Class-C rule mint() assigns via _mint_orientation, applied to the strand's own recovered leaves). rc277 (#891-peer / G5) DISPATCHES the WHOLE op — data-turn scan → content-address orientation (recall → sha256&3) → centromere cap → single-block splice — to the byte-identical C peer srmech_genome_mint_strand when HAS_NATIVE, so a bare-C host PROMOTES a strand end-to-end via that ONE call (closing the rc270 mint_strand C-host GAP: the cap-writer srmech_genome_centromere had a C peer, its glue did not). The pure path (the native-dispatched centromere cap-writer + a block splice, like integrate — self-describing blocks concatenated, no re-coupling) is the numpy-free fallback + parity oracle, so the minted strand is byte-identical whether native or pure. After minting, genome_save + genome_census report the chromosome as 'nuclear' (rc271 F1251; was 'minted'). Raises if the strand is empty, does not OPEN with a chromosome-boundary cap (pass a packed strand, NOT raw leaves), or ALREADY carries a centromere. Foundation for §100 GAP 2 (mint each nuclear community) + the streaming reader (a nuclear chromosome IS the eukaryotic/nuclear DNA). Class A (content-address orientation) + Class C (which-way) + Class K (position = p:q). numpy-free; no abs(). §101 (rc275): an in-process progress= callable (Python-only kwarg, NOT an MCP wire param) fires a single pre-op MINTING gate — a truthy return DECLINES cleanly and returns the valid UNMODIFIED pre-mint strand (a splice has no meaningful partial).",
            parameters=(P("strand", "Sequence[HV]", True, "an ALREADY-PACKED chromosome strand that OPENS with a boundary cap (from chromosome / kernel_pack / graph_to_kernel); NOT raw leaves"),
                        P("coupling", "HV", True, "the coupling invariant the strand was packed with (its width is the leaf/centromere dim)"),
                        P("orientation", "Optional[int]", False, "keyword-only; the global 4-way which-way, a Klein-4 sector 0..3 (default the content-address fold sha256(recovered leaves)[0]&3 — the same rule mint() uses)"),
                        P("centromere_at", "Optional[int]", False, "keyword-only; the arm-split index in DATA turns, 0..n_turns (default the metacentric midpoint n_turns//2 — position IS the p:q arm-ratio)"),
                        P("repeats", "int", False, "keyword-only; the alpha-satellite repeat-array size R (default 15; uint8 1..255)"),
                        P("handle", "str", False, "keyword-only; the inline CENP-A epigenetic handle (default 'cen')"),
                        ET_PARAM),
            returns=R("list", "the MINTED strand — the input strand with one interior centromere cap (0x58) spliced at the p:q arm-split; recover the orientation + arm-ratio with centromere_of, census as 'nuclear' after genome_save"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_partition", owner="srmech", category="genome",
            summary="PARTITION a directed relational GRAPH into nuclear-core vs plasmid-periphery BY ITS OWN STRUCTURE (§100 GAP 2 / PR#687 / F1250 / F1251) — an introspectable READ that BUILDS NOTHING (like mint_plan, 'we watch it happen'; genome_from_graph is the builder). Where mint_plan decides a kernel's shape by LEAF-COUNT (<=4 -> plasmid, >=5 -> nuclear), this finds the split from the graph's relational TOPOLOGY. Runs the out-of-core spectral community partition (laplacian.recursive_cut -> fiedler_sparse_file; peak RAM = the largest sub-graph, NEVER the dense n*n structure), measures each node's degree-normalized PARTICIPATION = the fraction of its incident edge-mass that CROSSES a community boundary (HIGH = a community-bridging PLASMID / mobile accessory, F1059's power source; LOW = a NUCLEAR node embedded in ONE community, the stable topical core), then MEASURES the antimode of that distribution. NOTE (§100.1 / F1250): participation — not the clustering coefficient (F1053) — is the read-INDEPENDENT discriminator that survives at scale (clustering measured unimodal on the 831k word-graph). DECISION: genuinely BIMODAL (a clean, wide, empty-relative antimode valley: 2*valley < min(peak_low,peak_high)) -> SPLIT into nuclear (low participation) + plasmid (high); UNIMODAL (no clean antimode) -> ACCEPT ONE-DNA-TYPE, do NOT force a split (F1250: 'one bridged content mass'). The split is per-NODE (robust even when recursive_cut absorbs a bridge node into a community — a bridge still crosses to the other community), then each community is sliced into its embedded-core nuclear group + its bridging plasmid group. SHAPE: an ASYMMETRIC minority nuclear core + majority plasmid remainder (F1251 attested bacterial genomics: a small stable core + a large mobile accessory), NEVER forced 50/50. weights are the INTEGER edge metric (participation is an exact rational, Class-N; no float, never abs); charges (signed direction) ride through for the builder. Returns {n, n_communities, bimodal, one_dna_type, antimode:{bins,counts,threshold_bin,peak_low_bin,peak_high_bin,valley_count,gap}, participation:[(num,den) per node], communities:[[node,...]], groups:[{community,type,nodes,size,participation}], counts:{nuclear,plasmid}, node_counts, work_dir}. Composes the C-dispatched recursive_cut with a thin PURE participation + antimode read (O(|E|)+O(n), exact integer) -> native==pure (the read is deterministic over the native community assignment). Class L (spectral community) + Class N (the exact participation rational) + Class K (the antimode boundary). §101 (rc275): the return carries a status key ('ok' / 'cancelled'); an in-process progress= callable (Python-only kwarg, NOT an MCP wire param) threads the PARTITIONING heartbeat into recursive_cut — a truthy return CANCELS and returns a clean partial (the valid community assignment, empty groups, status 'cancelled').",
            parameters=(P("n", "int", True, "node count (nodes are 0..n-1)"),
                        P("edges", "list", True, "directed edges [(u, v), ...] (treated as undirected for community detection + boundary-crossing)"),
                        P("weights", "list", False, "per-edge INTEGER metric (co-occurrence count); None = unit multiplicity"),
                        P("charges", "list", False, "per-edge signed direction; carried through for genome_from_graph (unused by the participation read)"),
                        P("work_dir", "str", False, "keyword-only; scratch dir for recursive_cut's on-disk tomes (caller owns it)"),
                        P("max_tome", "int", False, "keyword-only; recursive_cut leaf size — a sub-graph with <= max_tome nodes is a community (default 256)"),
                        P("n_bins", "int", False, "keyword-only; participation-histogram resolution for the antimode (default 16)"),
                        P("max_iters", "int", False, "keyword-only; per-bisection power-iteration cap (default 250)")),
            returns=R("dict", "the introspectable partition: {n, n_communities, bimodal, one_dna_type, antimode, participation, communities, groups, counts:{nuclear,plasmid}, node_counts, work_dir}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_from_graph", owner="srmech", category="genome",
            summary="BUILD a multi-chromosome genome from a directed graph, PARTITIONED BY ITS OWN STRUCTURE (§100 GAP 2 / PR#687 / F1250 / F1251) — 'hand a graph, get nuclear + plasmid from its structure'. Runs genome_partition, then for EACH classified group packs its INDUCED sub-graph (graph_to_kernel) into a chromosome: a NUCLEAR community is MINTED (mint_strand splices a 0x58 centromere -> a Tier-2 nuclear chromosome, the stable clonal core); a PLASMID community is KEPT as a Tier-1 plasmid chromosome (append-only, no centromere -> the mobile accessory). All chromosomes concatenate into one self-describing strand (each opens with its kernel-telomere boundary cap). If path is given the strand is persisted (genome_save) and censused — genome_census reports the MEASURED {nuclear:N, plasmid:M}. BYTE-EXACT per community: kernel_to_graph on any chromosome (with its n_syms) recovers that community's induced sub-graph exactly (the interior centromere is skipped on read, §44). A cross-community bridge edge is not in any single induced sub-graph — it is represented by the bridge node's PLASMID classification. Returns {strand, chromosomes:[{label,type,community,n_syms,nodes}], partition, counts:{nuclear,plasmid}, path?, census?}. Composes genome_partition + the C-dispatched graph_to_kernel + mint_strand + genome_save; numpy-free, no abs(). Class L (partition) + Class A/C/K (the mint). §101 (rc275): the return carries a status key ('ok' / 'cancelled'); an in-process progress= callable (Python-only kwarg, NOT an MCP wire param) threads the heartbeat through the partition (PARTITIONING) AND the per-group mint loop (MINTING) — a truthy return CANCELS and returns the whole chromosomes minted so far (a valid shorter genome) WITHOUT genome_save (nothing half-written hits disk). §113 (rc304, #1466): a caller attestation= (a dict) OVERRIDES the srmech-default source written into manifest.json when path is given — override-only over the five MPR SOURCE-identity fields (source_doi / source_url / license / retrieved_at / response_sha256), the four ENCODER fields stay srmech-owned — so an attested corpus genome (e.g. a simplewiki dump whose true source is https://dumps.wikimedia.org/simplewiki/latest/ under CC-BY-SA-4.0) records its REAL provenance genome-natively, in the only legitimate place (the directory is the SSoT, no sidecar files). The default is byte-identical to before when attestation is omitted; a malformed override raises before any bytes hit disk.",
            parameters=(P("n", "int", True, "node count (nodes are 0..n-1)"),
                        P("edges", "list", True, "directed edges [(u, v), ...]"),
                        P("weights", "list", False, "per-edge INTEGER metric; None = unit"),
                        P("charges", "list", False, "per-edge signed direction; None = undirected (all 0)"),
                        P("coupling", "HV", True, "keyword-only; the coupling invariant (width leaf_dim); required"),
                        P("path", "str", False, "keyword-only; if given, genome_save the strand there + include the census in the return"),
                        P("leaf_dim", "int", False, "keyword-only; the leaf (tome) width to chunk each chromosome into (default len(coupling); must be >= 52)"),
                        P("max_tome", "int", False, "keyword-only; forwarded to genome_partition (default 256)"),
                        P("n_bins", "int", False, "keyword-only; forwarded to genome_partition (default 16)"),
                        P("centromere_at", "int", False, "keyword-only; the nuclear arm-split forwarded to mint_strand (default the metacentric midpoint)"),
                        P("attestation", "dict", False, "keyword-only; when path is given, a caller MPR SOURCE-attestation forwarded to genome_save whose fields OVERRIDE the srmech default written into manifest.json (override-only over the five source-identity fields source_doi / source_url / license / retrieved_at / response_sha256; the four ENCODER-identity fields parser_version / parser_rule_hash / collector_descriptor_path / collector_descriptor_hash stay srmech-owned). Records an attested corpus genome's REAL source (e.g. a simplewiki dump under CC-BY-SA-4.0) genome-natively — the genome directory is the SSoT, no sidecar files (§41/F1300), so the manifest is the only legitimate home for it. A malformed override (non-dict / unknown key / value that makes the merged block an invalid MPR) RAISES before any bytes hit disk; omitted -> the srmech default is written unchanged."),
                        ET_PARAM),
            returns=R("dict", "{strand, chromosomes:[{label,type,community,n_syms,nodes}], partition, counts:{nuclear,plasmid}, path?, census?} — genome_census reports the measured {nuclear, plasmid} when path is given"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.discrete_writhe", owner="srmech", category="genome",
            summary="rc313 — the EXACT-rational DIRECTIONAL discrete writhe of a polygonal backbone (the physical-topology peer of the intrinsic mod-2 center-parity holonomy quaternion_cycle_holonomy, rc309). Given a supplied 3D embedding (each vertex an EXACT RATIONAL — int / Fraction / (num,den) per coord), Wr = the discrete Gauss double-sum over non-adjacent segment PAIRS in the z-drop projection: Wr = sum of eps_ij, eps_ij = sign((B-A).((D-C)x(C-A))) when segments i,j cross in the xy-projection (four exact 2D orientation determinants decide the crossing), else 0. HONEST BOUNDING: this is the directional (single-projection) writhe — the signed CROSSING NUMBER, an exact INTEGER — NOT the smooth solid-angle Gauss writhe (which is transcendental and cannot be a rational; the smooth value is this integer averaged over the direction sphere, out of exact-rational/libm-free scope). The mod-2 CWF check uses only its PARITY (+1 == -1). EXACT (W4): every crossing decision + every eps is the SIGN of an INTEGER determinant (the 4 pair-vertices scaled to a common positive integer denominator per axis) over srmech_bigint -> native == pure byte-identical; no float, no libm, no abs (sign is Class K . Class C). CAD-ban-clear: the closed-form discrete Gauss integral in Class-N integers, NOT GPU/mesh/FEA sim. Raises on a non-generic projection or a strand meeting itself in 3D (nudge the embedding). Dispatches to standalone-C srmech_genome_discrete_writhe (caller arena) when HAS_NATIVE, else srmech's own integer-determinant cascade.",
            parameters=(P("embedding", "list", True, "the backbone vertices [(x,y,z), ...]; each coordinate an int / fractions.Fraction / (num,den) integer pair (exact rational — floats rejected)"),
                        P("closed", "bool", False, "keyword-only; True (default) closes the loop with the wrap segment P[n-1]->P[0]; False = an open polyline")),
            returns=R("dict", "{num, den (the writhe as a reduced rational — den is always 1, the directional writhe being integer-valued), writhe:(num,den), n_points, closed}"),
            #  rc347 (`#T985`) LANE: Wr. It keeps the SIGN of each orientation
            # determinant and DISCARDS the magnitude it computed — MEASURED
            # identical under positive rational rescale x1, x3, x100, x1/7,
            # x999/4 (5/5), and NEGATING under a reflection (-1 -> +1). Sign
            # lane over a GEOMETRY input, where Tw is the sign lane over an
            # ALGEBRA input: same lane, different subject
            reads_lane="sign",
            reads_input=("geometry",),
        ),
        ToolEntry(
            name="srmech.amsc.genome.cwf_consistency_mod2", owner="srmech", category="genome",
            summary="rc313 — the mod-2 Calugareanu-White-Fuller consistency check on a strand: Lk == Tw + Wr (mod 2). Three INDEPENDENTLY-computed reads: Lk = the intrinsic mod-2 center-parity holonomy (rc309) — the center_parity of the strand's single fundamental cycle from quaternion_cycle_holonomy over the Q8 gains (center_parity -1 -> Lk==1; +1 -> Lk==0; 0 = pure-imaginary NON-central holonomy -> mod-2 Lk UNDEFINED, flagged); Tw = the framing twist read from the Q8 SIGN accumulation (parity of the count of negative-coset {-1,-i,-j,-k} gains); Wr = the directional writhe of the supplied embedding (discrete_writhe), computed from GEOMETRY, NEVER as Lk-Tw. The geometric independence gives the check teeth: the writhe supplies the non-abelian Q8 cocycle (e.g. i.i=-1) that the per-turn sign-sum Tw misses. HONEST BOUNDING (form not identity): a finite group (Q8) pins Lk only MOD 2 (center-parity), NOT the integer Gauss linking number; the Tw<->Q8-sign map is UNPINNED at integer level (parity only); no claim that DNA IS a quaternion or an integer-level CWF. No-embedding path: returns ONLY the intrinsic mod-2 Lk (+ Tw); wr / wr_mod2 / consistent are None, no Wr fabricated. Composition of C: quaternion_cycle_holonomy . discrete_writhe (both C-dispatched) . mod-2 integer arithmetic.",
            parameters=(P("edges", "list", True, "the strand connectivity [(u,v), ...] — a single fundamental cycle"),
                        P("gains", "list", True, "per-edge unit-quaternion Q8 gains (4-vectors) parallel to edges — the stored physical turns"),
                        P("n", "int", False, "keyword-only; node count (inferred from the edges when None)"),
                        P("embedding", "list", False, "keyword-only; the backbone vertices (node k -> embedding[k]), each an exact rational 3-tuple; None -> intrinsic mod-2 Lk only"),
                        P("closed", "bool", False, "keyword-only; forwarded to discrete_writhe (default True)")),
            returns=R("dict", "{lk_mod2 (0/1 or None if non-central), lk_center_parity (+1/-1/0), tw_mod2, wr:(num,den) or None, wr_mod2 or None, consistent (bool or None), note}"),
            #  rc347 (`#T985`) LANE: the mixer, and the op the whole axis was
            # adjudicated on. Per-field over 3000 trials: tw_mod2
            # sign(algebra) 3000/3000 index 0/3000 (SIGN, ALGEBRA); wr
            # sign(geometry) 3000/3000 algebra 0/3000 (SIGN, GEOMETRY);
            # lk_mod2 sign 735/3000 index 182/3000 (BOTH) — Lk is the only
            # read that responds to an index relabel
            reads_lane="both",
            reads_input=("algebra", "geometry"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.codon_read", owner="srmech", category="genome",
            summary="rc314 — the CODON READ-LAYER. Biology reads the genome in CODONS (triplets — the genetic code), and that is a READING PROCESS the ribosome IMPOSES over the stored strand, not stored substrate — so this is a PURE READ (stores nothing, changes no format; GENOME_FORMAT_VERSION stays 16, additive). q8_project_v4 is applied FIRST (biology reads 4 BASES, not 8 signed states — the winding/center SIGN BIT must NOT leak into amino-acid identity: a Q8 strand with nonzero winding and its V4-projection give BYTE-IDENTICAL codons). Then a 3-slot window slides from the reading-frame offset phase in {0,1,2}, forming a base-4 codon index i = 16*b0 + 4*b1 + b2 in [0,64) over the 3 projected symbols (coset 0->U/T, 1->C, 2->A, 3->G, so i is IDENTICAL to the NCBI transl_table=1 index), and a Class-E dense-catalog lookup i -> amino acid against the ATTESTED Standard Genetic Code (NCBI translation table 1; Elzanowski & Ostell, The Genetic Codes, NCBI; ncbieaa cross-verified byte-identical across wprintgc.cgi + gc.prt; resource DOI 10.1093/database/baaa062, open access) shipped as the MPR-attested datum srmech/amsc/attested/genetic_code/ — NEVER an inline invented dict. '*' denotes a stop. The reading-frame phase is a genuine cyclic C3 (Class I), DISTINCT from klein4_triality_cycle (the base-axis automorphism) and from the winding Lk (cwf_consistency_mod2; the sign bit). Class I (q8_project_v4 + Z3 frame) . Class E (codon catalog). Dispatches to the whole-op C peer srmech_genome_codon_read (c_dispatched, genome-fully-in-C; byte-identical pure fallback); ADDITIVE symbol, SRMECH_ABI_VERSION stays 10, GENOME_FORMAT_VERSION stays 16.",
            parameters=(P("strand", "list", True, "a 1-D sequence of Q8 base symbols (bytes / bytearray / list / tuple of ints in [0,8); V4 symbols in [0,4) are the sign-free case), or an HV (read via tobytes)"),
                        P("phase", "int", False, "the reading-frame offset in {0,1,2} (the C3 phase); default 0"),
                        P("with_indices", "bool", False, "keyword-only; if True also return the raw codon indices"),
                        P("stop_at_stop", "bool", False, "keyword-only; if True stop reading at the first stop codon (inclusive)")),
            returns=R("str", "the amino-acid string (one char per codon; '*' = stop), or (amino_acids, codon_indices) when with_indices"),
            #  rc347 (`#T985`) LANE: q8_project_v4 runs FIRST so the
            # winding/center sign bit cannot reach amino-acid identity.
            # MEASURED 0/400 response to a sigma flip, 400/400 to an index
            # relabel — the design intent is now a ratchet, not a comment
            reads_lane="index",
            reads_input=("algebra",),
        ),
        ToolEntry(
            name="srmech.amsc.genome.codon_frame_monodromy", owner="srmech", category="genome",
            summary="rc314 — the Z3 reading-frame MONODROMY of a CIRCULAR strand: going once around shifts the reading frame phi -> phi + L (mod 3), where L is the number of base symbols; returns L mod 3. A REAL Z3 invariant, DISTINCT from klein4_triality_cycle (the base-axis automorphism) and from the winding Lk (cwf_consistency_mod2; the sign bit) — there is NO codon copy of the integer Lk (the codon layer is frame topology in Z3, the winding lives in the sign bit). When L mod 3 == 0 the frame CLOSES on a clean loop (a circular ORF reads in one consistent frame); otherwise a single lap advances the frame by 1 or 2 (the monodromy is additive around laps). Class I (cyclic Z3). A pure read; stores nothing. q8_project_v4 is applied so L counts sign-free BASE symbols (projection preserves length). Dispatches to the whole-op C peer srmech_genome_codon_frame_monodromy (c_dispatched, genome-fully-in-C; byte-identical pure fallback); ADDITIVE symbol, SRMECH_ABI_VERSION stays 10.",
            parameters=(P("strand", "list", True, "a 1-D sequence of Q8 base symbols (see codon_read), or an HV"),),
            returns=R("int", "L mod 3 in {0,1,2} — the reading-frame shift accrued per lap around the circular strand"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_fiber_holonomy", owner="srmech", category="genome",
            summary="rc322 (§Q8-FIBER, F-HOLO-MISLOCATED) — the strand's TOPOLOGY/FIBER channel: the ORDERED accumulated Q8 holonomy of the coupled turns along a strand. The base/sequence channel (the per-turn coupled store quad_turn, stored[i]=q8_mult(turn[i], one[i])) is a function of that turn + the shared `one` ALONE, never of prior turns — so it is winding-INVARIANT (a reorder is a pure positional permutation, the #914 order-discard; the abelian Watson-Crick sequence / codon read is unchanged). This op ADDS the non-abelian complement: fold the ordered per-slot Q8 product acc[s] = q8_mult(acc[s], turn_t[s]) along the strand (identity +1 == byte 0). Because Q8 is NON-abelian (i.j=+k but j.i=-k), REORDERING the turns CHANGES the fold — this is the fiber/gauge = the accumulated Lk (biology's supercoiling channel, Lk=Tw+Wr accumulating along DNA; cwf_consistency_mod2). The per-slot center-sign holonomy[s]>>2 IS the accumulated Lk mod 2 (no abs(); the sign is a group xor-bit). Class-M (Q8 bind) ordered fold. Dispatches to the whole-op C peer srmech_genome_fiber_holonomy (c_dispatched; byte-identical pure q8_bind fallback); ADDITIVE symbol, SRMECH_ABI_VERSION stays 10 (the fiber CAP storage bumps GENOME_FORMAT_VERSION 16->17).",
            parameters=(P("turns", "list", True, "the stored/coupled data turns — a flat bytes of n_turns*leaf_dim Q8 bytes (leaf_dim required), or a sequence of per-turn buffers (HV / bytes / list[int] of leaf_dim Q8 bytes)"),
                        P("leaf_dim", "int", False, "the per-turn width (inferred from the first buffer when a sequence of buffers is given; required for a flat buffer)")),
            returns=R("bytes", "the accumulated per-slot Q8 holonomy (leaf_dim bytes); the center-sign of each byte is that slot's accumulated Lk mod 2"),
            #  rc347 (`#T985`) LANE: the ORDERED non-abelian fold reads the
            # index (which slot the walk lands in) and the sign (the
            # accumulated Lk parity). MEASURED 400/400 sign, 399/400 index
            reads_lane="both",
            reads_input=("algebra",),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_add_fiber", owner="srmech", category="genome",
            summary="rc322 (§Q8-FIBER) — return `strand` with a FIBER cap appended so the genome register HOLDS BOTH SIDES OF THE FIBRATION. Scans the strand's DATA turns (caps skipped), folds their ORDERED Q8 holonomy (genome_fiber_holonomy), and appends a FIBER_CAP_MARKER (0x46) cap holding it (layout [0x46]+label+NUL+n_holo(u16 BE)+3-bit-packed holonomy). The base/sequence channel is UNTOUCHED — the returned strand's data turns are the SAME blocks in the SAME order, and the fiber cap is an INTERIOR cap every codon/data-turn walk skips — so a genome that never calls this is BYTE-IDENTICAL to a pre-rc322 genome (the fiber is OPT-IN). ADDITIVE: it stores the gauge (the accumulated Lk) the winding-invariant base cannot carry. Class-M fiber fold . Class-B cap framing. Composition over the C fiber op + the cap packer.",
            parameters=(P("strand", "list", True, "a genome strand (a sequence of HV leaf blocks — caps + Q8 data turns)"),
                        P("label", "str", False, "keyword-only; the fiber cap's inline label (default 'fiber')")),
            returns=R("list", "the strand with one trailing FIBER cap (the fibration's second side, held in the strand)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_read_fiber", owner="srmech", category="genome",
            summary="rc322 (§Q8-FIBER) — read the FIBER cap back and RECONSTRUCT the gauge from the pair (base + fiber). Finds the strand's FIBER_CAP_MARKER (0x46) cap (the stored gauge), RE-DERIVES the ordered holonomy from the base DATA turns (genome_fiber_holonomy), and reports whether the pair is consistent — the gauge reconstructs from base bytes + the fiber holonomy. The per-slot lk_mod2 (center-sign) is the accumulated Lk (Lk=Tw+Wr) the winding-invariant base channel structurally cannot hold. Composition over the cap unpacker + the C fiber op.",
            parameters=(P("strand", "list", True, "a genome strand carrying exactly one FIBER cap (from genome_add_fiber)"),),
            returns=R("dict", "{label, holonomy (stored gauge bytes), recomputed (re-derived from the base), consistent (bool — stored==recomputed), lk_mod2 (bytes, one 0/1 per slot)}"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_octonion_holonomy", owner="srmech", category="genome",
            summary="rc325 (§𝕆-FIBER) — the OCTONION analog of genome_fiber_holonomy ONE Cayley–Dickson rung up (Q8 -> 𝕆): the strand's ORDERED accumulated OCTONION holonomy of the coupled turns along a strand. Folds the ordered per-slot octonion LEFT product acc[s] = oct_mult(acc[s], turn_t[s]) along the strand (identity +e0 == byte 0), REUSING the rc324 oct_mult (NOT a reimplemented product). Because 𝕆 is non-commutative AND non-associative, REORDERING the turns CHANGES the fold — the fiber the winding-INVARIANT per-turn octonion store cannot carry. Class-M (octonion bind) ordered fold; no abs() (the sign is a group ⊕-bit). Dispatches to the whole-op C peer srmech_genome_octonion_holonomy (c_dispatched; byte-identical pure oct_bind fallback); ADDITIVE symbol, SRMECH_ABI_VERSION stays 10 (the octonion fiber CAP storage bumps GENOME_FORMAT_VERSION 17->18).",
            parameters=(P("turns", "list", True, "the stored/coupled data turns — a flat bytes of n_turns*leaf_dim octonion bytes (leaf_dim required), or a sequence of per-turn buffers (HV / bytes / list[int] of leaf_dim octonion bytes)"),
                        P("leaf_dim", "int", False, "the per-turn width (inferred from the first buffer when a sequence of buffers is given; required for a flat buffer)")),
            returns=R("bytes", "the accumulated per-slot octonion holonomy (leaf_dim bytes)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_octonion_associator", owner="srmech", category="genome",
            summary="rc325 (§𝕆-FIBER) — the per-slot OCTONION associator DEFECT: the non-associativity Q8 (associative) cannot express. A COMPOSED op (non_compute; two pure-Python folds) — computes the fully-LEFT-associated fold L[s] and the fully-RIGHT-associated fold R[s] of the same ordered turns; because the octonion index lane is ⊕-associative, L[s] and R[s] share the same index and differ ONLY in the center sign bit, so defect[s] = (L[s]>>3) ^ (R[s]>>3) ∈ {0,1}. Identically 0 for n<3 (any two units associate, Artin) and for any all-quaternionic strand (indices ⊆ {0,1,2,3}); nonzero exactly when the ordered turns break associativity — the 𝕆 analog of rc322's lk_mod2. Class-K (⊕ sign-bit compare) ∘ Class-M (two octonion folds); no abs().",
            parameters=(P("turns", "list", True, "the ordered data turns — a flat bytes of n_turns*leaf_dim octonion bytes (leaf_dim required), or a sequence of per-turn buffers"),
                        P("leaf_dim", "int", False, "the per-turn width (inferred from the first buffer when a sequence of buffers is given; required for a flat buffer)")),
            returns=R("bytes", "one 0/1 associator-defect bit per slot (leaf_dim bytes)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_add_octonion_fiber", owner="srmech", category="genome",
            summary="rc325 (§𝕆-FIBER) — return `strand` with an OCTONION FIBER cap appended so the genome register HOLDS BOTH SIDES of the 𝕆 fibration (the 𝕆 analog of genome_add_fiber). Scans the strand's DATA turns (caps skipped), folds their ORDERED octonion holonomy (genome_octonion_holonomy), and appends an OCT_FIBER_CAP_MARKER (0x4F) cap holding it (layout [0x4F]+label+NUL+n_holo(u16 BE)+4-bit-packed holonomy — the octonion codec, NOT the 3-bit Q8 packing). The base/sequence channel is UNTOUCHED (same data turns, same order; the octonion fiber cap is an INTERIOR cap every codon/data-turn walk skips), so a genome that never calls this is BYTE-IDENTICAL to a pre-rc325 genome (the fiber is OPT-IN). ADDITIVE. Class-M fiber fold ∘ Class-B cap framing; composition over the C octonion fiber op + the cap packer.",
            parameters=(P("strand", "list", True, "a genome strand (a sequence of HV leaf blocks — caps + octonion data turns)"),
                        P("label", "str", False, "keyword-only; the octonion fiber cap's inline label (default 'octonion')")),
            returns=R("list", "the strand with one trailing OCTONION FIBER cap (the 𝕆 fibration's second side, held in the strand)"),
        ),
        ToolEntry(
            name="srmech.amsc.genome.genome_read_octonion_fiber", owner="srmech", category="genome",
            summary="rc325 (§𝕆-FIBER) — read the OCTONION FIBER cap back and RECONSTRUCT the fiber from the pair (base + fiber). Finds the strand's OCT_FIBER_CAP_MARKER (0x4F) cap (the stored gauge), RE-DERIVES the ordered holonomy from the base DATA turns (genome_octonion_holonomy), reports whether the pair is consistent, and reads the per-slot associator defect (genome_octonion_associator) — the non-associativity the base (and the Q8 fiber) cannot hold. Composition over the cap unpacker + the C octonion fiber op + the associator.",
            parameters=(P("strand", "list", True, "a genome strand carrying exactly one OCTONION FIBER cap (from genome_add_octonion_fiber)"),),
            returns=R("dict", "{label, holonomy (stored gauge bytes), recomputed (re-derived from the base), consistent (bool — stored==recomputed), associator_defect (bytes, one 0/1 per slot)}"),
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
            summary="HDC similarity: 1 − 2 hamming(a, b)/D ∈ [−1, 1] as the EXACT "
                    "Q rational (v0.9.0 F868 stay-rational; (D−2·hamming)/D, "
                    "collapses to a decimal only via float(s)). +1 identical, 0 "
                    "orthogonal, −1 complementary. Use hamming for the integer key.",
            parameters=(P("a", "bytes", True), P("b", "bytes", True)),
            returns=R("Q", "exact rational (D−2·hamming)/D in [-1, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.hamming", owner="srmech", category="hdc",
            summary="HDC bit-Hamming distance: the RAW INTEGER count of differing "
                    "bits between two BSC byte vectors (UPSTREAM §61; F868). "
                    "similarity = 1 − 2·hamming/(8·len(a)). The float-free, "
                    "blow-up-free recall-ranking key — argmax over integer "
                    "distances needs no division. Native-dispatched "
                    "(srmech_hdc_hamming).",
            parameters=(P("a", "bytes", True), P("b", "bytes", True)),
            returns=R("int", "count of differing bits in [0, 8·len(a)]"),
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
            summary="Polar match-fraction in [0,1] as the EXACT Q rational "
                    "(v0.9.0 F868 stay-rational; collapses to a decimal only via "
                    "float(s)). skip_zero=True (default) counts only jointly "
                    "non-zero positions; False counts all (0==0 a match).",
            parameters=(P("a", "HV", True), P("b", "HV", True),
                        P("skip_zero", "bool", False, "default True")),
            returns=R("Q", "exact rational matches/informative in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.polar_density", owner="srmech", category="hdc",
            summary="Fraction of non-zero (informative) positions in [0,1] as the "
                    "EXACT Q rational (v0.9.0 F868); 1.0 = fully bipolar, lower = "
                    "more dead-band. Collapses to a decimal only via float(d).",
            parameters=(P("v", "HV", True, "int8 {-1,0,+1}"),),
            returns=R("Q", "exact rational nonzero/n in [0, 1]"),
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
        # ── §102 / F1259 / F1260 (rc290): the Klein-4 mint SPLIT BY REGIME ──
        # One op used to serve four regimes with DIFFERENT correctness
        # criteria, and the call site never declared which. A `seed=` spanning
        # both "magic number" and "content address" is what let a DRAWN value
        # be mistaken for a DERIVED one. Four ops; the regime is declared.
        ToolEntry(
            name="srmech.amsc.hdc.klein4_expand", owner="srmech", category="hdc",
            summary="EXPAND regime — deterministically expand an integer seed "
                    "to a Klein-4 hypervector (D elements in {0,1,2,3}, the "
                    "rank-2 Class-M alphabet). CRITERION: REPRODUCIBILITY — "
                    "same (D, seed) gives the same bytes on every host and in "
                    "every implementation. Use it when you hold an integer "
                    "that already means something (a byte value, a position, a "
                    "table row). Do NOT use a hand-picked constant to stand in "
                    "for 'some vector, doesn't matter which' — that is the "
                    "DRAWN anti-pattern (an undeclared draw from an undeclared "
                    "ensemble). For data use klein4_address; for a named slot "
                    "klein4_role; for a genuinely per-run value draw your own "
                    "bytes and use klein4_encode_bytes. rc290 rename of "
                    "klein4_random(D, seed=…); the MT19937 stream is "
                    "byte-for-byte unchanged.",
            parameters=(P("D", "int", True, "dimension"),
                        P("seed", "int", True,
                          "integer seed (any sign, any width)")),
            returns=R("HV", "uint8 in {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_address", owner="srmech", category="hdc",
            summary="ADDRESSED regime — the Class-A content address of "
                    "`content` as a Klein-4 hypervector. Two-stage counter-mode "
                    "SHA-256: h = sha256(content), then sha256(h|i) for "
                    "i = 0,1,2,… expanded to D crumbs (the fold-first shape is "
                    "what lets the C peer run out of a FIXED buffer for content "
                    "of any size — no malloc, no ceiling). CRITERION: IDENTITY "
                    "AND STRUCTURELESSNESS — equal content gives an equal "
                    "vector, unequal content gives vectors at the 0.25 "
                    "orthogonality floor. Sitting at the floor and being "
                    "incompressible are the TARGETS, not defects. Use it for a "
                    "namespace key / store identity / coupling. NEVER use it to "
                    "represent content you intend to COMPARE: SHA-256 avalanche "
                    "flips ~48.8% of output bits per 1-char edit, so at D=8192 "
                    "'cat'/'cats' scores 0.2589 against a 0.2454 'cat'/'dog' "
                    "control, while klein4_encode_bytes scores 0.6597 on the "
                    "same pair. High diffusion is exactly what makes a good "
                    "ADDRESS and exactly what disqualifies it as a "
                    "REPRESENTATION — one property, two opposite requirements.",
            parameters=(P("D", "int", True, "dimension"),
                        P("content", "bytes", True,
                          "the bytes to address (str is UTF-8 encoded; may be "
                          "empty)")),
            returns=R("HV", "uint8 in {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_role", owner="srmech", category="hdc",
            summary="ROLE regime — the binding key for a NAMED SLOT (the role "
                    "half of a role-filler bind). The role name is folded to a "
                    "32-bit seed by the FNV-1a token hash under `base`, then "
                    "expanded. CRITERION: NEAR-ORTHOGONALITY BETWEEN DISTINCT "
                    "ROLES — two different names must land at the 0.25 floor so "
                    "binding by one role cannot be read out by another. Unlike "
                    "the ADDRESSED regime, near-orthogonality here is not merely "
                    "acceptable, it IS the functional requirement. Use it when "
                    "the vector names a POSITION IN A STRUCTURE (a field name, "
                    "a slot label, a co-occurrence role) rather than data. Not "
                    "a content address: `base` deliberately re-namespaces the "
                    "same name to a different vector.",
            parameters=(P("D", "int", True, "dimension"),
                        P("role", "str", True, "the slot name"),
                        P("base", "int", False,
                          "namespace seed — distinct values give an independent "
                          "codebook over the same role names")),
            returns=R("HV", "uint8 in {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_sector_frame", owner="srmech",
            category="hdc",
            summary="The (1,3,7,3) SECTOR FRAME of dimension D — the "
                    "substrate's own period-14 Klein-4 position structure. "
                    "Position j carries the Class-C sector flip of the "
                    "Cayley-Dickson block that slot (j mod 14) belongs to: "
                    "C -> iω₇ (1), H -> γ₅ (2), O -> CPT (3). The partition "
                    "enters as a MASK, not as vector content, because it is "
                    "OPERATOR structure (how G(σ,θ) acts) while any projection "
                    "target is an operand — tiling the 14 slots into D "
                    "positions is measurably catastrophic (0.82 mean "
                    "similarity, 1054 collisions across 120 θ, wrong-coupling "
                    "cross-read at 64/64). As a period-14 mask it is "
                    "well-defined at EVERY D, so nothing requires D divisible "
                    "by 14 and nothing gains from it. HONEST DISCLOSURE: the "
                    "frame is STATISTICALLY INERT — XOR-by-constant is a "
                    "Hamming isometry, so masking changes no pairwise "
                    "statistic. It is carried for structural legibility and "
                    "attestation, and it gives a falsifiable invariant: XOR it "
                    "back off and the raw Class-A expansion reappears.",
            parameters=(P("D", "int", True, "dimension"),),
            returns=R("HV", "uint8 in {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_from_one", owner="srmech",
            category="hdc",
            summary="ONE-A14 — the One's Klein-4 COUPLING projection. Class-A "
                    "address of the One's canonical (σ, θ, terms) serialisation, "
                    "XORed with the period-14 (1,3,7,3) sector frame. Derivable "
                    "from the three constructor integers alone: no stored bytes, "
                    "no seed table, no label. THIS IS A ROLE, NOT A "
                    "REPRESENTATION: genome.quad_turn applies the coupling as a "
                    "uniform klein4_bind, and XOR-by-constant is a Hamming "
                    "isometry, so a coupling MATHEMATICALLY CANNOT transmit "
                    "structure into stored content. The 0.25 floor and "
                    "incompressibility are therefore the CORRECT targets, and a "
                    "structure-preserving coupling is a LEAK (the naive slot "
                    "projection reads one genome with another's key at 64/64). "
                    "At D=64 over 120 distinct θ (7140 pairs): mean similarity "
                    "0.2501, ZERO identical pairs — statistically "
                    "indistinguishable from the magic-integer draw it replaces "
                    "(0.2498). The gain is a DECLARED FUNCTION of substrate "
                    "parameters replacing an undeclared draw; it is not a "
                    "quality improvement and is not offered as one.",
            parameters=(P("one", "One", True,
                          "a cascade One (exposes .sigma, .theta=(num, den), "
                          ".terms)"),
                        P("D", "int", True,
                          "dimension — free; nothing requires or gains from "
                          "divisibility by 14")),
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
            name="srmech.amsc.hdc.klein4_unbundle", owner="srmech", category="hdc",
            summary="Klein-4 unbundle: recover a bound value from a bundle "
                    "(superposition) by binding the key back (= unbind on the "
                    "bundle). Exact for a single bound pair; inside a multi-pair "
                    "bundle returns value+crosstalk — clean up with "
                    "klein4_similarity against a codebook (recoverable up to HDC "
                    "capacity). bundle's dual = unbundle + similarity-cleanup.",
            parameters=(P("bundle", "HV", True), P("key", "HV", True)),
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
            name="srmech.amsc.hdc.klein4_phase_key", owner="srmech", category="hdc",
            summary="Continuous-phase Klein-4 key (UPSTREAM §59; F861): the V4 "
                    "code `elem` (default 2 = γ₅) on a `width`-wide circular "
                    "slot-window starting at round(frac·D) mod D, identity (0) "
                    "elsewhere — 'continuous phase from discrete-per-slot sectors "
                    "via population coding', the chirality-native analogue of "
                    "HRR/polar phase. Default width is the half-window D//2.",
            parameters=(P("D", "int", True, "dimension"),
                        P("frac", "float", True,
                          "phase fraction in [0,1) (wraps mod 1)"),
                        P("elem", "int", False,
                          "Klein-4 code in {0,1,2,3} (default 2 = γ₅)"),
                        P("width", "int", False,
                          "window width in slots (default D//2)")),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_phase_bind", owner="srmech", category="hdc",
            summary="Bind a continuous phase into a Klein-4 vector (UPSTREAM §59): "
                    "klein4_bind(hv, klein4_phase_key(len(hv), frac, …)). "
                    "Reversible (same phase twice = identity); σ-mirror (±φ "
                    "equidistant from base); and similarity(phase_bind(h,0), "
                    "phase_bind(h,Δφ)) is the EXACT rational 1 − 2·circ_dist(Δφ) "
                    "(an integer half-window overlap over D → a Q, never a lossy "
                    "float). Native-dispatched via srmech_klein4_phase_key.",
            parameters=(P("hv", "HV", True, "uint8 {0,1,2,3}"),
                        P("frac", "float", True,
                          "phase fraction in [0,1) (wraps mod 1)"),
                        P("elem", "int", False,
                          "Klein-4 code in {0,1,2,3} (default 2 = γ₅)"),
                        P("width", "int", False,
                          "window width in slots (default D//2)")),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_chunk_bundle", owner="srmech", category="hdc",
            summary="Build a CAPACITY-BOUNDED chunk-set (UPSTREAM §58; F837): "
                    "split a list of (bound) vectors into consecutive groups of "
                    "≤ `capacity` and klein4_bundle each. Returns a list of HV "
                    "chunks — the VSA cleanup-memory that avoids the single-"
                    "bundle crosstalk (resolver read 3.3% → 96.7% rank-1). "
                    "`capacity` is exposed (a non-monotonic per-tome sweet-spot, "
                    "F839), not hardcoded.",
            parameters=(P("vectors", "Sequence[HV]", True,
                          "one or more uint8 {0,1,2,3} vectors of equal length"),
                        P("capacity", "int", True,
                          "max binds per chunk (≥ 1)")),
            returns=R("list[HV]", "≤ ceil(len(vectors)/capacity) bundle chunks"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_chunk_resolve", owner="srmech", category="hdc",
            summary="Max-resonance read over a capacity-bounded chunk-set "
                    "(UPSTREAM §58; F837): for each candidate, the MAX over "
                    "chunks of klein4_similarity(klein4_bind(chunk, key), "
                    "candidate). Returns one EXACT Q per candidate (stay-rational "
                    "F868: ranks on the integer match-count; Q(count,D) names the "
                    "fraction). The LM-agnostic VSA cleanup-memory; routing/argmax "
                    "stay in the caller. Native-dispatched (the recall hot path).",
            parameters=(P("chunks", "Sequence[HV]", True,
                          "the capacity-bounded bundle chunks (from "
                          "klein4_chunk_bundle)"),
                        P("key", "HV", True,
                          "the probe key (e.g. an encoded context)"),
                        P("candidates", "Sequence[HV]", True,
                          "the bounded candidate atom set to score")),
            returns=R("list[Q]", "per-candidate max-resonance score"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_encode_bytes", owner="srmech", category="hdc",
            summary="Byte-composed Klein-4 vector (UPSTREAM §60; F864): a bundle "
                    "of POSITION-BOUND per-byte random vectors — byte b → "
                    "klein4_expand(D, b) (the 256-byte vocab), bound with "
                    "klein4_pos_key(D, i), all bundled. Restores MORPHOLOGY "
                    "(sim('cat','cats') ≈ 0.66 ≫ the ~0.25 chance level) while "
                    "stripping the word-atomic English/whitespace privilege (it "
                    "hashes raw UTF-8). Composes klein4_expand + bind + bundle.",
            parameters=(P("data", "bytes", True,
                          "the byte string to encode (non-empty)"),
                        P("D", "int", True, "dimension")),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_compose", owner="srmech", category="hdc",
            summary="Scale-invariant role-filler compositor (F900/F901; the "
                    "byte/glyph LM 'C1'): bundle_i( klein4_bind(part_i, "
                    "klein4_pos_key(D, i)) ) over ARBITRARY pre-composed HV "
                    "parts. Where klein4_encode_bytes mints byte atoms (byte→"
                    "word), this is the RECURSIVE rung (word→phrase→sentence): "
                    "the parts at level n+1 are the composed vectors of level n. "
                    "Position-binding makes it order-sensitive + similarity-"
                    "PRESERVING (a one-part change degrades gracefully — same "
                    "fractal coherence signature at every scale), unlike a bare "
                    "chained klein4_bind fold (→ ~0.25 chance). Composes "
                    "klein4_bind + klein4_bundle.",
            parameters=(P("parts", "Sequence[HV]", True,
                          "a non-empty sequence of equal-length uint8 {0,1,2,3} "
                          "Klein-4 parts"),),
            returns=R("HV", "uint8 {0,1,2,3}"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_similarity", owner="srmech", category="hdc",
            summary="Klein-4 similarity: fraction of positions where a==b in "
                    "[0,1] (1 identical, 0 orthogonal). v0.9.0 (F868 stay-"
                    "rational): returns the EXACT Q rational matches/D (compares "
                    "like a float, collapses to a decimal only via float(s)); use "
                    "klein4_match_count for the raw integer key. rc13 sectors=/"
                    "parallel=/mode= fans the comparison across ≤4 lanes (default-"
                    "ON at ≥4 cores); ALWAYS returns the serial value.",
            parameters=(P("a", "HV", True), P("b", "HV", True),
                        P("sectors", "int", False, "lanes 1..4; default-on (4 "
                          "at ≥4 cores, else 1)"),
                        P("parallel", "bool", False, "True→4 lanes / False→1 "
                          "(alias for sectors=)"),
                        P("mode", "str", False, "'chunk' (default) or "
                          "'chirality'")),
            returns=R("Q", "exact rational matches/D in [0, 1]"),
        ),
        ToolEntry(
            name="srmech.amsc.hdc.klein4_match_count", owner="srmech", category="hdc",
            summary="Klein-4 match count: the RAW INTEGER number of positions "
                    "where a==b (UPSTREAM §61; F868). klein4_similarity = "
                    "match_count / len(a). This is the float-free, blow-up-free "
                    "recall-ranking key — argmax over integer counts needs no "
                    "division and never leaves the integers. Native-dispatched "
                    "(srmech_klein4_match_count).",
            parameters=(P("a", "HV", True), P("b", "HV", True),
                        P("sectors", "int", False, "lanes 1..4; default-on (4 "
                          "at ≥4 cores, else 1)"),
                        P("parallel", "bool", False, "True→4 lanes / False→1 "
                          "(alias for sectors=)"),
                        P("mode", "str", False, "'chunk' (default) or "
                          "'chirality'")),
            returns=R("int", "count of matching positions in [0, len(a)]"),
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
            name="srmech.amsc.hdc.klein4_bundle_sector_scores", owner="srmech",
            category="hdc",
            summary="NON-COLLAPSING read of a klein4_bundle_accumulate "
                    "accumulator (§102/F1265): all FOUR sector scores per "
                    "coordinate instead of the one symbol klein4_bundle_resolve "
                    "collapses to, so a caller RANKS where the resolved read "
                    "could only MATCH. score(s) = a0(s)*a1(s), the agreement "
                    "product (= n^2 * P(s) under bit independence, the ML "
                    "estimate the marginals support) — exact integers, no "
                    "division. uint64 because a0*a1 reaches n^2. A READ change "
                    "over storage already paid for: no store is rebuilt. "
                    "Native-dispatched.",
            parameters=(P("acc", "array('I')", True,
                          "a (1+2*D) uint32 accumulator"),),
            returns=R("array('Q')",
                      "4*D uint64, row-major: out[4*i + s] scores sector s at "
                      "coordinate i (bit0 = s & 1, bit1 = (s >> 1) & 1)"),
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
        # The resonant-spectrum closure (§75 / F928) — a Class-L coupling
        # composite over the eigensolve + best_rational + factor kernels,
        # with the 1:1 C peer srmech_resonant_spectrum.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.coupling.resonant_spectrum", owner="srmech",
            category="coupling",
            summary="Read a real-symmetric coupling Laplacian L as a STORED "
                    "(excitation-free) resonant object (§75 / F928). Returns the "
                    "eigenvalue 'tensions' ASCENDING (the stored 'dark' tension "
                    "spectrum = the MFO field, no pluck), the eigenvector 'modes' "
                    "(columns = the excitation modes), the force-orders "
                    "[L, L², …, Lᵒ] via Lᵏ = V·diag(Λᵏ)·Vᵀ reconstructed from the "
                    "ONE eigensolve (L² = biharmonic/tidal forces-of-forces), and "
                    "the 'resonances' — each adjacent nonzero-tension ratio as a "
                    "Class-N best_rational (num, den) with a Class-J lock verdict "
                    "(smooth/2-adic den = LOCK on the Laplace ladder; large-prime "
                    "den = libration off-lock). Composes symmetric_eigendecompose "
                    "(L) + mat_matmul (L) + best_rational (N) + primes.factor (J); "
                    "1:1 C peer srmech_resonant_spectrum (native when present, "
                    "pure-Python the complete alternative). numpy-free; no abs().",
            parameters=(P("L", "Mat", True,
                          "an n×n real-symmetric coupling Laplacian"),
                        P("orders", "int", False,
                          "how many force-orders [L¹…Lᵒ]; default 2 (≥1)"),
                        P("max_den", "int", False,
                          "best_rational denominator ceiling; default 64")),
            returns=R("dict", "{'tensions': Vec (ascending), 'modes': Mat "
                              "(columns = eigenvectors), 'force_orders': "
                              "list[Mat] [L,…,Lᵒ], 'resonances': list of "
                              "{pair, ratio (num,den), den_coords, locked}}"),
        ),
        ToolEntry(
            name="srmech.amsc.coupling.resonant_spectrum_sparse", owner="srmech",
            category="coupling",
            summary="Read the resonant storage signature at UNBOUNDED n — the "
                    "streaming / out-of-core k-extreme-mode peer of "
                    "resonant_spectrum (issue #698). resonant_spectrum reads the "
                    "signature only through the DENSE Class-L eigensolve "
                    "(native-capped at MAX_NATIVE_NODES=256; O(n²) RAM, O(n³) "
                    "eig). This reads the SAME signature restricted to the k "
                    "EXTREME modes — the k lowest-tension + k highest-tension "
                    "eigenpairs of the COMBINATORIAL Laplacian L = D − W — via "
                    "streaming power iteration + Gram-Schmidt deflation on the "
                    "packed edge stream (bottom-k ride the shift σI − L, top-k "
                    "ride L; each mode deflates against all found). RAM O(k·n), "
                    "time O(k·|E|·iters), n UNBOUNDED — breaks the n≤256 dense "
                    "wall the way fiedler_sparse breaks it for the 2-way cut. The "
                    "k tensions feed the SAME _resonances_from_tensions lock/"
                    "libration read resonant_spectrum uses (Class-N best_rational "
                    "+ Class-J prime-coordinate factor; smooth-den LOCK vs large-"
                    "prime-den libration) — reused, so the verdicts are IDENTICAL "
                    "to the dense read on the same tensions. Composes "
                    "write_packed_graph + the fiedler_sparse streaming matvec, "
                    "extended from one mode to bottom-k + top-k. 1:1 C peer "
                    "srmech_laplacian_k_extreme_modes_file (streams the packed "
                    "file via the PAL; caller-arena, no node cap). numpy-free; no "
                    "abs(). (Accurate for extremes SEPARATED from the bulk; near-"
                    "degenerate boundary clusters converge slowly — an iterative-"
                    "method property. No force_orders — dense Lᵏ is not "
                    "materialisable at unbounded n.)",
            parameters=(P("edges_or_path", "list|str", True,
                          "an undirected edge list [(u,v),…] OR a str path to a "
                          "packed edge file (write_packed_graph; streamed)"),
                        P("weights", "sequence", False,
                          "per-edge weights (default 1.0); ignored for a path"),
                        P("k", "int", False,
                          "modes per extreme side; default 8 (up to 2k tensions)"),
                        P("n", "int", False,
                          "node count; None → inferred (max endpoint+1 / from file)"),
                        P("max_iters", "int", False,
                          "per-mode power-iteration cap; default 1000"),
                        P("max_den", "int", False,
                          "best_rational denominator ceiling; default 64")),
            returns=R("dict", "{'tensions': Vec (ascending, the k extreme "
                              "eigenvalues), 'modes': Mat (columns = the extreme "
                              "eigenvectors), 'resonances': list of {pair, ratio "
                              "(num,den), den_coords, locked}, 'k', 'n', "
                              "'n_modes'}"),
        ),
        ToolEntry(
            name="srmech.amsc.coupling.from_bodies", owner="srmech",
            category="coupling",
            summary="Build the gravity coupling-graph (n, edges, weights) for a "
                    "body set — the m_i·m_j/r² Newtonian-weight builder feeding "
                    "resonant_spectrum (the F928 Jupiter+Galilean convention: a "
                    "central body at index 0/position 0, a moon-pair gap "
                    "otherwise). Feeds laplacian.dense_laplacian. numpy-free.",
            parameters=(P("masses", "sequence", True, "body masses (flat list)"),
                        P("positions", "sequence", True,
                          "1-D body positions, flat list (central body at 0)")),
            returns=R("tuple[int, list[tuple[int,int]], list[float]]",
                      "(n, edges, weights) for dense_laplacian"),
        ),
        # ────────────────────────────────────────────────────────────
        # fractal_spectrum — the Ch-2 (quasi-periodic / fractal) DUAL of
        # resonant_spectrum. Pure orchestration over already-C-backed ops
        # (Poly.derivative/.eval + Class-N log/best_rational + the F974
        # |q|-meter) — NO new numerical kernel, so it ships non_compute (the
        # from_bodies / cooccurrence_edges precedent; no dedicated C peer).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.coupling.fractal_spectrum", owner="srmech",
            category="coupling",
            summary="Read a self-similar lattice's SPECTRAL-DECIMATION structure "
                    "— the Ch-2 (quasi-periodic / fractal) DUAL of "
                    "resonant_spectrum (F686 / F974). Where resonant_spectrum(L) "
                    "reads a symmetric Laplacian's FLAT eigenspectrum (one "
                    "eigensolve), fractal_spectrum(R, branches) reads the ITERATED "
                    "PREIMAGE of the renormalization Poly R (the decimation map, "
                    "R(0)=0), NOT a flat list. Grounded on the Sierpinski gasket: "
                    "on the NORMALIZED Laplacian the decimation is exactly "
                    "R(z)=z(5−4z) (measured — Rammal 1984 / Fukushima–Shima 1992, "
                    "Potential Analysis 1 (1992) 1–35, OA-attested via "
                    "arXiv:1505.05855). Returns the exact scale R'(0), the fracton "
                    "(spectral) dimension d_s = 2·log(branches)/log(scale) as a "
                    "Class-N best_rational anchor (2·log3/log5 ≈ 1.36521 for the "
                    "gasket), the F974 bit-exact |q|-meter q_octaves_per_level = "
                    "ceil(log2(scale)) (3 for the gasket), rung_class 'constant' "
                    "(one R iterated = self-similar), log_period_over_2pi = "
                    "1/log(scale) (the discrete-scale-invariance complex-dimension "
                    "period; 1/ln5 ≈ 0.6213 for the gasket), and the honest "
                    "spectrum_open — the full spectrum is the JULIA SET of R "
                    "(operand-IRREPRESENTABLE OPEN; no finite exact carrier decides "
                    "λ∈spectrum). Composes Poly.derivative/.eval (L) + log (N) + "
                    "best_rational (N); PURE orchestration over already-C-backed "
                    "ops → non_compute (no dedicated C peer; the from_bodies / "
                    "cooccurrence_edges precedent). Exact-ℚ; numpy-free; no abs().",
            parameters=(P("R", "Poly", True,
                          "the spectral-decimation map — a degree≥2 Poly with "
                          "R(0)=0 and R'(0)>1 (or an ascending-degree coefficient "
                          "sequence coerced with Poly.from_coeffs)"),
                        P("branches", "int", True,
                          "the number of self-similar copies (≥2)"),
                        P("log_terms", "int", False,
                          "the Class-N log series-truncation depth; default 25")),
            returns=R("dict", "{'decimation_map': Poly, 'scale': Q (R'(0)), "
                              "'branches': int, 'self_similarity_dim': (num,den) "
                              "d_s anchor, 'q_octaves_per_level': int (F974 "
                              "|q|-meter), 'rung_class': 'constant', "
                              "'log_period_over_2pi': (num,den), 'spectrum_open': "
                              "str (the Julia-set operand-IRREPRESENTABLE OPEN)}"),
        ),
        # ────────────────────────────────────────────────────────────
        # fold_encode / fold_spectrum — the BIDIRECTIONAL translation
        # between a stored HDC fold and a self-similar lattice's spectral-
        # decimation structure (#697; the "Q2 reader made LITERAL"). Pure
        # orchestration over shipped Klein-4 HDC + Poly + fractal_spectrum
        # ops — NO new numerical kernel, so BOTH ship non_compute (the
        # cooccurrence_fold / from_bodies precedent; no dedicated C peer).
        # The two directions are ASYMMETRIC: EXACT encode / SIMILARITY read.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.coupling.fold_encode", owner="srmech",
            category="coupling",
            summary="Encode a spectral-decimation structure INTO a stored HDC "
                    "fold — the EXACT / total FORWARD half of the #697 "
                    "bidirectional translation (the 'Q2 reader made LITERAL'). "
                    "Where fractal_spectrum(R, branches) reads the decimation "
                    "from an EXPLICIT Poly R, fold_encode folds R's coefficients "
                    "+ the branch count into a single lossy Klein-4 bundle — a "
                    "role-filler record in the cooccurrence_fold store shape "
                    "(F584/F758). Each coefficient slot c{i} (and 'branches') "
                    "gets a deterministic klein4_role code; each distinct "
                    "coefficient VALUE gets a deterministic FILLER code (keyed by "
                    "its 'num/den' token); the fold is the klein4_bundle "
                    "superposition of the role⊗value binds. EXACT + total + "
                    "deterministic (seed-keyed) — the LOSSINESS lives entirely in "
                    "the READ (fold_spectrum), the HDC asymmetry. Composes "
                    "klein4_role/bind/bundle (M) + Poly.from_coeffs (L); PURE "
                    "orchestration over already-C-backed ops → non_compute (the "
                    "cooccurrence_fold / from_bodies precedent; no dedicated C "
                    "peer). numpy-free; no abs().",
            parameters=(P("R", "Poly", True,
                          "the spectral-decimation map — a degree>=2 Poly with "
                          "R(0)=0 (or an ascending-degree coefficient sequence "
                          "coerced with Poly.from_coeffs)"),
                        P("branches", "int", True,
                          "the number of self-similar copies (>=2)"),
                        P("dim", "int", True,
                          "the Klein-4 width D of the fold (>=1; pick well above "
                          "4*(degree+2) for a confident round-trip)"),
                        P("seed", "int", False,
                          "base seed for the deterministic role/value codes "
                          "(default 0)")),
            returns=R("dict",
                      "{'fold': HV (the lossy Klein-4 bundle), 'roles': "
                      "{slot: HV}, 'codes': {value_token: HV} (the cleanup "
                      "alphabet), 'coeff_slots': [c0,…], 'branch_slot': "
                      "'branches', 'slots': [...], 'dim': int, 'seed': int, "
                      "'n_pairs': int}"),
        ),
        ToolEntry(
            name="srmech.amsc.coupling.fold_spectrum", owner="srmech",
            category="coupling",
            summary="Read a stored HDC fold BACK to its spectral-decimation "
                    "params — the SIMILARITY / CLEANUP-MEMORY READ half of the "
                    "#697 bidirectional translation. NOT the exact inverse of "
                    "fold_encode (the fold is a LOSSY Klein-4 superposition, "
                    "F584): each slot binds the role back against the fold "
                    "(klein4_unbundle = self-inverse XOR) and cleans the "
                    "value-plus-crosstalk estimate up against the value codebook "
                    "(argmax_token similarity(unbundle, codes[token]) — the "
                    "cooccurrence_fold cleanup pattern). The recovered tokens "
                    "rebuild R + branches and feed the SAME fractal_spectrum "
                    "orchestration → the IDENTICAL decimation dict. The honesty "
                    "boundary is load-bearing — NEVER a silent wrong Poly: a "
                    "recovery is accepted ONLY when (1) dim>=capacity_mult*n_pairs "
                    "(default 4*n_pairs, the HDC bundle-capacity floor), (2) every "
                    "slot's winner beats the runner-up by >=margin_floor (default "
                    "1/10; chance is 1/4), AND (3) re-bundling the recovered binds "
                    "reproduces the fold BIT-FOR-BIT (fold_consistency==1, the "
                    "op_provenance EQUAL self-check). Any gate failing → the honest "
                    "'unrecovered' verdict (op_provenance UNKNOWN, #717 "
                    "honestly-inexact) with NO decimation Poly. Composes "
                    "klein4_bind/bundle/match_count/similarity (M) + Poly + "
                    "fractal_spectrum; PURE orchestration → non_compute. "
                    "numpy-free; no abs() (exact-Q Class-K similarity reads).",
            parameters=(P("fold", "dict", True,
                          "a fold store from fold_encode (the Klein-4 values may "
                          "be HV or JSON-serialised uint8 lists)"),
                        P("log_terms", "int", False,
                          "the Class-N log series-truncation depth forwarded to "
                          "fractal_spectrum on a confident recovery (default 25)"),
                        P("margin_floor", "number", False,
                          "override the separation gate (Q / (num,den) / int; "
                          "default 1/10)"),
                        P("capacity_mult", "int", False,
                          "override the capacity-floor multiple (default 4)")),
            returns=R("dict",
                      "on recovery: the fractal_spectrum dict PLUS {'verdict': "
                      "'recovered', 'op_provenance': 'EQUAL', 'similarity': Q, "
                      "'confidence': Q, 'fold_consistency': Q (==1), 'per_slot': "
                      "{slot: {value, similarity, margin}}}; on failure: "
                      "{'verdict': 'unrecovered', 'op_provenance': 'UNKNOWN', "
                      "'similarity', 'confidence', 'fold_consistency', 'per_slot', "
                      "'reason', 'spectrum_open'} with NO decimation Poly"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc125 (task #723): the RECOVERABLE FOLD as a HarmonicMaass-shaped
        # PAIR carrier. rc124's fold_spectrum reads a LOSSY bundle by a
        # similarity/cleanup pass (exact WHEN the fold has capacity, honest-
        # unrecovered below the dim>=4·n_pairs floor). fold_encode_recoverable
        # ATTACHES the exact complement (the generating decimation R) so a
        # generated fold recovers EXACTLY at ANY dim — the field–excitation
        # recoverability principle. The RecoverableFold pair MIRRORS
        # HarmonicMaass(hol, shadow): lossy_bundle ↔ hol, exact_seed_R ↔ shadow
        # ("storing R IS storing the recovery"). Pure orchestration + data over
        # shipped ops → non_compute (no new C peer; the carrier is data).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.coupling.fold_encode_recoverable", owner="srmech",
            category="coupling",
            summary="Encode a spectral-decimation structure into a RECOVERABLE "
                    "PAIR — the HarmonicMaass-shaped follow-on to fold_encode "
                    "(rc125; task #723). Returns a RecoverableFold PAIR: the "
                    "rc124 lossy Klein-4 fold store (.lossy_bundle ↔ "
                    "HarmonicMaass.hol) AND the exact generating decimation R "
                    "(.exact_seed_R ↔ HarmonicMaass.shadow). Because R is "
                    "CARRIED, fold_spectrum on the pair recovers EXACTLY at ANY "
                    "dim — INCLUDING dim < 4·n_pairs, where the rc124 bare read "
                    "honestly fails (crosstalk overwhelms the lossy bundle). "
                    "'Storing R IS storing the recovery' (the recoverability "
                    "principle: a lossy projection is recoverable iff you attach "
                    "the exact complement it dropped). rc124's bare fold_encode "
                    "is UNCHANGED (still returns the bare fold-store dict); this "
                    "is the additive recoverable path. Composes fold_encode + "
                    "Poly; PURE orchestration + data → non_compute (no dedicated "
                    "C peer; the carrier is data). numpy-free; no abs().",
            parameters=(P("R", "Poly", True,
                          "the spectral-decimation map — a degree>=2 Poly with "
                          "R(0)=0 (or an ascending-degree coefficient sequence "
                          "coerced with Poly.from_coeffs)"),
                        P("branches", "int", True,
                          "the number of self-similar copies (>=2)"),
                        P("dim", "int", True,
                          "the Klein-4 width D of the lossy bundle (>=1); "
                          "recovery is exact at ANY dim (the seed is carried)"),
                        P("seed", "int", False,
                          "base seed for the deterministic role/value codes "
                          "(default 0)")),
            returns=R("RecoverableFold",
                      "the pair carrier (.lossy_bundle ↔ hol / .exact_seed_R ↔ "
                      "shadow / .has_seed / .branches / .dim / .complement() / "
                      ".recover() / .identity()); read via fold_spectrum(pair)"),
        ),
        # ────────────────────────────────────────────────────────────
        # The §76 "telescope" Σ-row closed-form prover (F929) — Gosper's
        # indefinite hypergeometric summation, the FIRST public op of the row.
        # Class-N rational arithmetic over the Class-J prime-field on the
        # exact-ℚ[k] Poly substrate; 1:1 C peer srmech_gosper.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.gosper.gosper", owner="srmech",
            category="gosper",
            summary="Gosper's indefinite hypergeometric summation (Gosper 1978, "
                    "PNAS 75(1):40–42; Petkovšek–Wilf–Zeilberger *A=B* 1996, "
                    "ch. 5) — the FIRST public op of the §76 'telescope' Σ-row "
                    "closed-form prover (F929). Input: a hypergeometric term given "
                    "by its TERM RATIO t(k+1)/t(k) = num(k)/den(k) (two exact-ℚ[k] "
                    "Poly). Decides whether Σ t(k) has a hypergeometric "
                    "antidifference T(k)=R(k)·t(k) (so T(k+1)−T(k)=t(k), and the "
                    "sum telescopes: Σ_{a}^{b} t = T(b+1)−T(a)); if so returns the "
                    "rational certificate R={'num':Poly,'den':Poly}, else None (no "
                    "closed form — e.g. the harmonic t(k)=1/k). Exact over ℚ via "
                    "the Gosper–Petkovšek normal form (Poly dispersion/gcd/divmod) "
                    "+ the bounded-degree undetermined-coefficient solve (exact "
                    "Gauss-Jordan over ℚ, QMat). 1:1 C peer srmech_gosper "
                    "(orchestrates srmech_poly_*/srmech_qmat_rref; native when "
                    "present, pure-Python the complete alternative). Exact bigint; "
                    "no float, no abs() (Class-K sign), no numpy / math.",
            parameters=(P("num", "Poly", True,
                          "the term-ratio NUMERATOR num(k) — an exact-ℚ[k] Poly "
                          "(or an ascending-degree coefficient list)"),
                        P("den", "Poly", True,
                          "the term-ratio DENOMINATOR den(k) — a NONZERO exact-ℚ[k] "
                          "Poly (or coefficient list)")),
            returns=R("dict | None",
                      "{'num': Poly, 'den': Poly} (the rational certificate R(k) "
                      "with antidifference T(k)=R(k)·t(k)), or None when no "
                      "hypergeometric closed form exists"),
        ),
        # ────────────────────────────────────────────────────────────
        # The §76 "telescope" Σ-row closed-form prover (F929) — Zeilberger's
        # creative telescoping, the SECOND public op of the row. Builds on gosper
        # (Gosper-in-k) + Poly + QMat (the exact-ℚ parametrized solve); 1:1 C peer
        # srmech_zeilberger.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.zeilberger.zeilberger", owner="srmech",
            category="zeilberger",
            summary="Zeilberger's creative telescoping (Zeilberger 1990, Discrete "
                    "Math. 80(2):207–211; 1991, J. Symbolic Computation 11(3):195–"
                    "204; Petkovšek–Wilf–Zeilberger *A=B* 1996, ch. 6) — the SECOND "
                    "public op of the §76 'telescope' Σ-row closed-form prover "
                    "(F929). For a DEFINITE hypergeometric sum f(n)=Σ_k F(n,k) of a "
                    "proper term F(n,k), produces the minimal-order LINEAR "
                    "RECURRENCE with polynomial coefficients Σ_{j=0}^{L} a_j(n)·"
                    "f(n+j)=0. Input: F's two term ratios r_n(n,k)=F(n+1,k)/F(n,k) "
                    "and r_k(n,k)=F(n,k+1)/F(n,k), each a rational function of (n,k) "
                    "given as two bivariate exact-ℚ[n,k] BiPoly (a Poly-in-k whose "
                    "coeffs are Poly-in-n; a plain Poly is read as a k-polynomial). "
                    "Method: creative telescoping — for L=0,1,…,max_order run "
                    "Gosper-in-k on T=Σ_j a_j(n)F(n+j,k) with the a_j(n) carried as "
                    "unknowns; the first nonzero exact-ℚ kernel (via QMat RREF) is "
                    "the recurrence + the rational certificate R(n,k). Returns "
                    "{'order':L,'coeffs':[Poly_in_n,…],'certificate':BiPoly}, or "
                    "None when none ≤ max_order. 1:1 C peer srmech_zeilberger "
                    "(orchestrates srmech_poly_*/srmech_qmat_rref; native "
                    "accelerates the common low-order case, pure-Python the "
                    "complete alternative). Exact bigint; no float, no abs() "
                    "(Class-K sign), no numpy / math.",
            parameters=(P("rn_num", "BiPoly", True,
                          "r_n NUMERATOR — F(n+1,k)/F(n,k) numerator, a bivariate "
                          "exact-ℚ[n,k] BiPoly (or a Poly / coefficient list)"),
                        P("rn_den", "BiPoly", True,
                          "r_n DENOMINATOR — a NONZERO bivariate BiPoly"),
                        P("rk_num", "BiPoly", True,
                          "r_k NUMERATOR — F(n,k+1)/F(n,k) numerator BiPoly"),
                        P("rk_den", "BiPoly", True,
                          "r_k DENOMINATOR — a NONZERO bivariate BiPoly"),
                        P("max_order", "int", False,
                          "the largest ansatz recurrence order to try (default 6)")),
            returns=R("dict | None",
                      "{'order': int, 'coeffs': [Poly, ...], 'certificate': BiPoly} "
                      "— the minimal-order recurrence Σ_j coeffs[j](n)·f(n+j)=0 plus "
                      "the WZ certificate, or None when none of order ≤ max_order"),
        ),
        # ────────────────────────────────────────────────────────────
        # The §76 "telescope" Σ-row closed-form prover (F929) — the
        # Wilf–Zeilberger pair method, the THIRD and FINAL public op of the row
        # (the Σ-row CLOSER: gosper → zeilberger → wz_certificate). FINDs via
        # zeilberger at the forced recurrence + VERIFIES the WZ equation as an
        # exact bivariate rational identity; 1:1 C peer srmech_wz_verify is the
        # COMPLETE verify mirror (degree-bounded, no order cap).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.wz_certificate.wz_certificate", owner="srmech",
            category="wz_certificate",
            summary="The Wilf–Zeilberger pair method (Wilf & Zeilberger 1990, "
                    "*Rational functions certify combinatorial identities*, J. Amer. "
                    "Math. Soc. 3(1):147–158; Petkovšek–Wilf–Zeilberger *A=B* 1996, "
                    "ch. 7) — the THIRD and FINAL public op of the §76 'telescope' "
                    "Σ-row closed-form prover (F929), the row CLOSER. PROVES a "
                    "terminating hypergeometric identity Σ_k F(n,k)=const by producing "
                    "AND verifying its WZ certificate. Input: F's two term ratios "
                    "r_n(n,k)=F(n+1,k)/F(n,k) and r_k(n,k)=F(n,k+1)/F(n,k), each a "
                    "bivariate exact-ℚ[n,k] BiPoly num/den pair (a plain Poly is read "
                    "as a k-polynomial). The WZ method is Zeilberger at the FORCED "
                    "n-recurrence f(n+1)−f(n)=0: it FINDs the certificate R(n,k) "
                    "(=zeilberger at max_order=1, the order-1 recurrence of a "
                    "constant sum) such that G=R·F makes the WZ equation F(n+1,k)−"
                    "F(n,k)=G(n,k+1)−G(n,k) telescope, then VERIFIES that equation as "
                    "an EXACT bivariate rational-function identity (clearing "
                    "denominators to a polynomial identity — no solve, no order "
                    "bound). Returns {'certificate':{'num':BiPoly,'den':BiPoly}, "
                    "'verified':True}, or None when the term is not WZ-summable. 1:1 "
                    "C peer srmech_wz_verify is the COMPLETE verify mirror (the "
                    "degree-bounded exact bivariate-ℚ identity check; native when "
                    "present, pure-Python the complete alternative). Exact bigint; no "
                    "float, no abs() (Class-K sign), no numpy / math.",
            parameters=(P("rn_num", "BiPoly", True,
                          "r_n NUMERATOR — F(n+1,k)/F(n,k) numerator, a bivariate "
                          "exact-ℚ[n,k] BiPoly (or a Poly / coefficient list)"),
                        P("rn_den", "BiPoly", True,
                          "r_n DENOMINATOR — a NONZERO bivariate BiPoly"),
                        P("rk_num", "BiPoly", True,
                          "r_k NUMERATOR — F(n,k+1)/F(n,k) numerator BiPoly"),
                        P("rk_den", "BiPoly", True,
                          "r_k DENOMINATOR — a NONZERO bivariate BiPoly")),
            returns=R("dict | None",
                      "{'certificate': {'num': BiPoly, 'den': BiPoly}, 'verified': "
                      "True} — the WZ certificate R(n,k)=num/den (verified to satisfy "
                      "the WZ equation), or None when the term is not WZ-summable"),
        ),
        # ────────────────────────────────────────────────────────────
        # The WEIGHT-axis modular-forms-ring reducer (rc84) — the level-1
        # ℂ[E₄,E₆] MEMBERSHIP DECISION. The structure-theorem analog of the Σ-row
        # gosper/zeilberger/wz_certificate reducers: a q-series → its UNIQUE exact-ℚ
        # polynomial-in-(E₄,E₆) rep, or honest OPEN (None). Built on the rc83
        # Eisenstein carrier + the rc40 QMat exact-ℚ Gauss-Jordan; 1:1 C peer
        # srmech_modular_forms_ring_represent (dispatches to srmech_qmat_solve).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.modular_forms_ring.modular_forms_ring_represent",
            owner="srmech", category="modular_forms_ring",
            summary="The level-1 modular-forms-ring MEMBERSHIP DECISION — the "
                    "structure theorem M_*(SL₂(ℤ)) = ℂ[E₄,E₆] made executable "
                    "(Serre, *A Course in Arithmetic*, GTM 7 (1973), Ch. VII §3; "
                    "Zagier, *Elliptic Modular Forms and Their Applications*, in "
                    "*The 1-2-3 of Modular Forms*, Springer (2008), §2.2). The "
                    "WEIGHT-axis REDUCER, the analog of the §76 Σ-row "
                    "gosper/zeilberger/wz_certificate reducers (and the THIRD weight "
                    "rung after the rc82 eta-quotient + rc83 Eisenstein carriers). "
                    "Given an exact q-series (a list of exact-ℚ / int / (num,den) "
                    "coefficients) claimed to be a weight-k level-1 modular form, "
                    "SOLVES the exact-ℚ linear system Σ_{a,b} c_{a,b}·(E₄^a E₆^b)[n] "
                    "= f[n] over the weight-k monomial basis {(a,b): 4a+6b=k} "
                    "(built from the rc83 Eisenstein E₄/E₆ q-series + exact-ℚ "
                    "truncated q-series multiply), VERIFIES the solution reproduces "
                    "EVERY provided term, and returns the UNIQUE exact-ℚ polynomial "
                    "rep {(a,b): Q} — or None when no representation exists (a "
                    "non-modular series, or the honest LEVEL-axis OPEN of a "
                    "genuinely higher-level Γ₀(N) form, N>1, which needs more "
                    "generators). The construction/solve IS the decision "
                    "(decompose-and-compute over the monomial basis via exact "
                    "Gauss-Jordan, QMat — NOT a search). Level 1 is a "
                    "representability CLOSURE (every in-ring form is representable); "
                    "the OPEN is only the level axis. Keystones: Δ=(E₄³−E₆²)/1728 at "
                    "weight 12 → {(3,0):1/1728,(0,2):−1/1728}; E₈ → {(2,0):1}; E₁₀ → "
                    "{(1,1):1}; E₁₄ → {(2,1):1}. ≥ dim(k)+2 terms required. 1:1 C "
                    "peer srmech_modular_forms_ring_represent (dispatches the square "
                    "subsystem to srmech_qmat_solve; native when present, "
                    "pure-Python the complete alternative + parity oracle). Exact "
                    "bigint; no float, no abs() (Class-K sign), no numpy / math.",
            parameters=(P("q_series", "list", True,
                          "the q-series claimed to be a weight-k level-1 modular "
                          "form — a list of exact-ℚ Q / int / (num, den) pairs "
                          "(no float), ascending q-power; needs ≥ dim(k)+2 terms"),
                        P("k", "int", True,
                          "the (even) claimed weight — the grading of ℂ[E₄,E₆]"),
                        P("n_terms", "int", False,
                          "optional cap on the number of provided terms USED "
                          "(default: all provided)")),
            returns=R("dict | None",
                      "{(a, b): Q} — the unique exact-ℚ polynomial-in-(E₄,E₆) "
                      "representation (c_{a,b} = coefficient of E₄^a E₆^b), or None "
                      "when the q-series is not a level-1 weight-k modular form "
                      "(the honest membership/level OPEN)"),
        ),
        # ────────────────────────────────────────────────────────────
        # The WEIGHT-axis QUASIMODULAR-forms-ring reducer (rc89) — the level-1
        # ℂ[E₂,E₄,E₆] MEMBERSHIP DECISION, the rc84 ModularFormsRing pattern ONE
        # generator up (adds E₂, the weight-2 quasimodular generator). The structure-
        # theorem analog of the Σ-row gosper/zeilberger/wz_certificate reducers: a
        # q-series → its UNIQUE exact-ℚ polynomial-in-(E₂,E₄,E₆) rep, or honest OPEN
        # (None). Built on the rc83 Eisenstein E₄/E₆ + the new E₂ (eisenstein_e2) +
        # the rc40 QMat exact-ℚ Gauss-Jordan; 1:1 C peer
        # srmech_quasimodular_forms_ring_represent (dispatches to srmech_qmat_solve).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.quasimodular_forms_ring."
                 "quasimodular_represent",
            owner="srmech", category="quasimodular_forms_ring",
            summary="The level-1 QUASIMODULAR-forms-ring MEMBERSHIP DECISION — the "
                    "Kaneko–Zagier ring M̃_*(SL₂(ℤ)) = ℂ[E₂,E₄,E₆] made executable "
                    "(Kaneko & Zagier, *The Moduli Space of Curves*, Progr. Math. "
                    "129 (1995), pp. 165–172; Zagier, *Elliptic Modular Forms and "
                    "Their Applications*, in *The 1-2-3 of Modular Forms*, Springer "
                    "(2008), §5.3). The WEIGHT-axis REDUCER one generator up from the "
                    "rc84 modular_forms_ring_represent (it ADDS E₂, the weight-2 "
                    "quasimodular generator E₂ = 1 − 24·Σσ₁(n)qⁿ); the analog of the "
                    "§76 Σ-row gosper/zeilberger/wz_certificate reducers. Given an "
                    "exact q-series (a list of exact-ℚ / int / (num,den) "
                    "coefficients) claimed to be a weight-k quasimodular form, SOLVES "
                    "the exact-ℚ linear system Σ_{a,b,c} c_{a,b,c}·(E₂^a E₄^b E₆^c)[n] "
                    "= f[n] over the weight-k monomial basis {(a,b,c): 2a+4b+6c=k} "
                    "(built from the E₂/E₄/E₆ q-series + exact-ℚ truncated q-series "
                    "multiply), VERIFIES the solution reproduces EVERY provided term, "
                    "and returns the UNIQUE exact-ℚ polynomial rep {(a,b,c): Q} — or "
                    "None when no representation exists. The construction/solve IS the "
                    "decision (decompose-and-compute over the monomial basis via "
                    "exact Gauss-Jordan, QMat — NOT a search). This ring genuinely "
                    "EXTENDS the modular ℂ[E₄,E₆] (the a=0 subring): e.g. E₂² at "
                    "weight 4 → {(2,0,0):1} here, but rc84 represent → None. "
                    "KEYSTONES (Ramanujan's Serre-derivative identities, D=q·d/dq): "
                    "DE₂=(E₂²−E₄)/12 @4 → {(2,0,0):1/12,(0,1,0):−1/12}; "
                    "DE₄=(E₂E₄−E₆)/3 @6 → {(1,1,0):1/3,(0,0,1):−1/3}; "
                    "DE₆=(E₂E₆−E₄²)/2 @8 → {(1,0,1):1/2,(0,2,0):−1/2}. The honest "
                    "OPENs are the Jacobi-form (τ–z two-variable) + level (N>1) "
                    "boundaries. ≥ dim(k)+2 terms required. 1:1 C peer "
                    "srmech_quasimodular_forms_ring_represent (dispatches the square "
                    "subsystem to srmech_qmat_solve; native when present, pure-Python "
                    "the complete alternative + parity oracle). Exact bigint; no "
                    "float, no abs() (Class-K sign), no numpy / math.",
            parameters=(P("q_series", "list", True,
                          "the q-series claimed to be a weight-k quasimodular form — "
                          "a list of exact-ℚ Q / int / (num, den) pairs (no float), "
                          "ascending q-power; needs ≥ dim(k)+2 terms"),
                        P("k", "int", True,
                          "the (even) claimed weight — the grading of ℂ[E₂,E₄,E₆]"),
                        P("n_terms", "int", False,
                          "optional cap on the number of provided terms USED "
                          "(default: all provided)")),
            returns=R("dict | None",
                      "{(a, b, c): Q} — the unique exact-ℚ polynomial-in-(E₂,E₄,E₆) "
                      "representation (c_{a,b,c} = coefficient of E₂^a E₄^b E₆^c, "
                      "nonzero monomials only), or None when the q-series is not a "
                      "level-1 weight-k quasimodular form (the honest membership OPEN)"),
        ),
        # ────────────────────────────────────────────────────────────
        # The MULTIVARIATE "sums of sums" row of the §76 telescope Σ-row prover —
        # the Apagodu–Zeilberger double-sum creative-telescoping recurrence-finder
        # (CLOSES the multivariate F929 reduction row). Generalizes zeilberger to a
        # DOUBLE sum over the rc52 TriPoly ℚ[n,j,k] carrier; 1:1 C peer
        # srmech_apagodu_zeilberger (accelerates the order ≤ 1 textbook case).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.apagodu_zeilberger.apagodu_zeilberger",
            owner="srmech", category="apagodu_zeilberger",
            summary="The Apagodu–Zeilberger multivariate 'sums of sums' creative "
                    "telescoping (M. Apagodu & D. Zeilberger, 'Multi-variable "
                    "Zeilberger and Almkvist–Zeilberger algorithms and the "
                    "sharpening of Wilf–Zeilberger theory', Adv. Appl. Math. "
                    "37(2):139–152, 2006; H. Wilf & D. Zeilberger, 'An algorithmic "
                    "proof theory for hypergeometric (ordinary and q) multisum/"
                    "integral identities', Invent. Math. 108(1):575–633, 1992) — the "
                    "op that CLOSES the multivariate F929 reduction row, the double-"
                    "sum generalization of zeilberger. For a DEFINITE DOUBLE "
                    "hypergeometric sum f(n)=Σ_{j,k} F(n,j,k) of a proper term "
                    "F(n,j,k), produces the minimal-order LINEAR RECURRENCE with "
                    "polynomial coefficients Σ_{i=0}^{L} a_i(n)·f(n+i)=0. Input: F's "
                    "THREE term ratios r_n(n,j,k)=F(n+1,j,k)/F(n,j,k), "
                    "r_j=F(n,j+1,k)/F(n,j,k), r_k=F(n,j,k+1)/F(n,j,k), each a "
                    "rational function of (n,j,k) given as two trivariate exact-"
                    "ℚ[n,j,k] TriPoly (the rc52 carrier this op consumes; a BiPoly / "
                    "Poly / scalar coerces). Method: the two-certificate creative-"
                    "telescoping ansatz Σ_i a_i(n)·ρ_i = Δ_j(R_j·F)/F + Δ_k(R_k·F)/F "
                    "with rational certificates R_j=x_j/D_P, R_k=x_k/D_P over the "
                    "shared LHS denominator D_P=Π_i ρ_den_i; clearing denominators "
                    "gives a homogeneous exact-ℚ linear system (QMat RREF), and the "
                    "first nonzero a-block kernel is the recurrence + the two "
                    "certificates; summing over j,k collapses the telescoping RHS. "
                    "Returns {'order':L,'coeffs':[Poly_in_n,…],'certificate_j':"
                    "TriPoly,'certificate_k':TriPoly}, or None when none ≤ max_order. "
                    "1:1 C peer srmech_apagodu_zeilberger (orchestrates the "
                    "trivariate poly algebra + srmech_qmat_rref; native accelerates "
                    "the order ≤ 1 textbook double-sum case, e.g. Σ_{j,k} "
                    "C(n,j)C(j,k)→3ⁿ, pure-Python the complete alternative — a "
                    "genuinely-2D higher-order term like Σ C(n,j)C(n,k)C(j+k,j) is "
                    "proved on the pure path). Exact bigint; no float, no abs() "
                    "(Class-K sign), no numpy / math.",
            parameters=(P("rn_num", "TriPoly", True,
                          "r_n NUMERATOR — F(n+1,j,k)/F(n,j,k) numerator, a "
                          "trivariate exact-ℚ[n,j,k] TriPoly (or a coercible value)"),
                        P("rn_den", "TriPoly", True,
                          "r_n DENOMINATOR — a NONZERO trivariate TriPoly"),
                        P("rj_num", "TriPoly", True,
                          "r_j NUMERATOR — F(n,j+1,k)/F(n,j,k) numerator TriPoly"),
                        P("rj_den", "TriPoly", True,
                          "r_j DENOMINATOR — a NONZERO trivariate TriPoly"),
                        P("rk_num", "TriPoly", True,
                          "r_k NUMERATOR — F(n,j,k+1)/F(n,j,k) numerator TriPoly"),
                        P("rk_den", "TriPoly", True,
                          "r_k DENOMINATOR — a NONZERO trivariate TriPoly"),
                        P("max_order", "int", False,
                          "the largest ansatz recurrence order to try (default 4)")),
            returns=R("dict | None",
                      "{'order': int, 'coeffs': [Poly, ...], 'certificate_j': "
                      "TriPoly, 'certificate_k': TriPoly} — the minimal-order "
                      "recurrence Σ_i coeffs[i](n)·f(n+i)=0 plus the two rational "
                      "certificates, or None when none of order ≤ max_order"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc113 (#1239 / F1027 / UPSTREAM §85): the PROSE-SIDE carrier
        # constructors. The conversational grounded-inference loop (siona)
        # binds utterance-expressible operands (ints / floats / strs / bytes /
        # edge-pairs) and chains RETURNED carriers via its result register —
        # but nothing in the registry RETURNED a Poly / QPoly / QBiPoly, so
        # the Σ-row + q-row engines were unreachable by prose. These three
        # non_compute BUILDERS (the from_bodies / cooccurrence_edges
        # precedent) close that gap: integer coefficient lists in → the exact
        # carrier out, register-chainable into gosper / zeilberger /
        # wz_certificate / q_gosper / q_zeilberger / q_wz_certificate.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.poly.poly_from_coeffs", owner="srmech",
            category="poly",
            summary="PROSE-SIDE carrier constructor (#1239 / F1027 / UPSTREAM "
                    "§85): build the exact-ℚ polynomial carrier Poly from an "
                    "ascending-degree list of INTEGER coefficients — coeffs[i] "
                    "is the coefficient of k**i ([0, 1] is k; [1, 1] is 1+k). "
                    "The utterance-expressible builder that makes the Σ-row "
                    "engines' Poly term-ratio operands (gosper / zeilberger / "
                    "wz_certificate) REGISTER-CHAINABLE from a conversational "
                    "loop: before rc113 no registered tool RETURNED a Poly a "
                    "result register could chain. Ints only — the exact-ℚ "
                    "prose discipline (integers ARE exact; a float / bool / "
                    "str coefficient is an honest TypeError; exact rationals "
                    "enter via the in-process Poly.from_coeffs). A non_compute "
                    "BUILDER (the coupling.from_bodies / text."
                    "cooccurrence_edges precedent — it constructs an operand; "
                    "every computation lives in the ops that consume it). "
                    "numpy-free; no float; no abs().",
            parameters=(P("coeffs", "list[int]", True,
                          "ascending-degree integer coefficients "
                          "(coeffs[i] is the coefficient of k**i)"),),
            returns=R("Poly",
                      "the exact-ℚ polynomial carrier (chainable into the "
                      "gosper / zeilberger / wz_certificate Poly params)"),
            smoke_test_hint={"coeffs": "[0, 1]"},
        ),
        ToolEntry(
            name="srmech.amsc.qpoly.qpoly_from_coeffs", owner="srmech",
            category="qpoly",
            summary="PROSE-SIDE carrier constructor (#1239 / F1027 / UPSTREAM "
                    "§85): build the exact ℚ[q] q-shift carrier QPoly (Laurent "
                    "in x=qᵏ) from an ascending-x list of INTEGER-LEAF cells — "
                    "coeffs[i] is the ℚ[q] coefficient of x**(x_low+i), each "
                    "cell an int (a constant-in-q coefficient) OR a list of "
                    "ints (the ASCENDING-q-DEGREE coefficient: [0, 1] is q, "
                    "[0, 2] is 2q, [0, 0, 1] is q²). Worked forms: the "
                    "q-geometric ratio x = [0, 1]; the order-3 MOCK-THETA term "
                    "ratio q·x²/(1+q·x)² = numerator [0, 0, [0, 1]] over "
                    "denominator [1, [0, 2], [0, 0, 1]] — the operands that "
                    "make 'find the sparse form of a mock theta equation' a "
                    "register-chained pipeline into q_gosper. NOTE the prose "
                    "grammar is deliberately UNAMBIGUOUS: a list cell is "
                    "ALWAYS ascending-q ints (never the in-process carrier's "
                    "(num, den) rational-pair reading); a float / bool / str "
                    "leaf is an honest TypeError (integers ARE exact ℚ). "
                    "x_low (optional, default 0) is the lowest x-exponent (a "
                    "negative value = a genuine Laurent tail). A non_compute "
                    "BUILDER (the from_bodies / cooccurrence_edges precedent). "
                    "numpy-free; no float; no abs().",
            parameters=(P("coeffs", "list", True,
                          "ascending-x cells: each an int (constant in q) or "
                          "an ascending-q-degree list of ints ([0, 1] = q)"),
                        P("x_low", "int", False,
                          "the lowest x-exponent (default 0; negative = "
                          "Laurent tail)")),
            returns=R("QPoly",
                      "the exact ℚ[q] q-shift carrier (chainable into the "
                      "q_gosper rn_num / rn_den params)"),
            smoke_test_hint={"coeffs": "[0, 1]"},
        ),
        ToolEntry(
            name="srmech.amsc.qbipoly.qbipoly_from_coeffs", owner="srmech",
            category="qbipoly",
            summary="PROSE-SIDE carrier constructor (#1239 / F1027 / UPSTREAM "
                    "§85): build the exact bivariate-q carrier QBiPoly (a "
                    "polynomial in Y=qᵏ whose coefficients are QPoly in X=qⁿ) "
                    "from a Y-ascending list of INTEGER-LEAF x-cell lists — "
                    "coeffs[d] is the Y**d coefficient, itself an ascending-X "
                    "list whose entries follow the qpoly_from_coeffs cell "
                    "grammar (int = constant in q; list of ints = ascending-q "
                    "degree, so [0, 1] is q — never a rational pair). Worked "
                    "forms — the q-binomial-theorem term F(n,k)=[n,k]_q·"
                    "q^{C(k,2)} (the rc56 keystone) written entirely with "
                    "integer leaves: r_k num X−Y = [[0, 1], [-1]]; r_k den "
                    "qY−1 = [[-1], [[0, 1]]]; r_n num (qX−1)·Y = [[0], [-1, "
                    "[0, 1]]]; r_n den qX−Y = [[0, [0, 1]], [-1]] → "
                    "q_zeilberger certifies the ORDER-1 recurrence (1+qⁿ)f(n)"
                    "−f(n+1)=0. THE PIPELINE OPENER: before rc113 no "
                    "registered tool RETURNED a QBiPoly, so the definite-q-sum "
                    "engine (q_zeilberger / q_wz_certificate) was unreachable "
                    "by prose. A non_compute BUILDER (the from_bodies / "
                    "cooccurrence_edges precedent); a float / bool / str leaf "
                    "is an honest TypeError (integers ARE exact ℚ). numpy-"
                    "free; no float; no abs().",
            parameters=(P("coeffs", "list[list[int]]", True,
                          "Y-ascending list of x-cell lists; each x-entry an "
                          "int (constant in q) or an ascending-q-degree list "
                          "of ints ([0, 1] = q)"),),
            returns=R("QBiPoly",
                      "the exact bivariate-q carrier (chainable into the "
                      "q_zeilberger / q_wz_certificate rn/rk params)"),
            smoke_test_hint={"coeffs": "[[0, 1], [-1]]"},
        ),
        # ────────────────────────────────────────────────────────────
        # rc116 (#1248 / F1038): the CARRIER CONVERSION LADDER — the ORPHAN
        # FIX + the promote/project rungs. The tool_schema producer/consumer
        # census found BiPoly (consumed by zeilberger + wz_certificate) and
        # TriPoly (consumed by apagodu_zeilberger) ORPHANS — consumed, never
        # PRODUCED from the registry (rc113 shipped only the q-side). These
        # two non_compute BUILDERS close that gap so the classic non-q
        # Zeilberger / WZ / Apagodu row is buildable by prose. Then the
        # promote/project ops (variable ladder Poly↔BiPoly↔TriPoly +
        # QPoly↔QBiPoly, plus the Hurwitz cd_promote/cd_project) let a driver
        # auto-route a lower-rung carrier UP to a higher-rung consumer (a
        # univariate IS trivially bivariate), and the ladder descriptor is the
        # declarative coherency map that routing reads. All non_compute (pure
        # carrier restructuring — trivial embed / drop; no numerical kernel;
        # the from_bodies / cooccurrence_edges precedent).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.zeilberger.bipoly_from_coeffs", owner="srmech",
            category="zeilberger",
            summary="PROSE-SIDE carrier constructor (#1248 / F1038; the ORPHAN "
                    "FIX): build the exact-ℚ[n,k] bivariate carrier BiPoly "
                    "from a k-ascending list of INTEGER-LEAF n-coefficient "
                    "lists — coeffs[d] is the k**d coefficient, itself an "
                    "ascending-n integer list (a Poly in n). "
                    "bipoly_from_coeffs([[1, 1], [-1]]) is (1+n)−k. Worked "
                    "forms — the F(n,k)=C(n,k) term ratios (the rc42 keystone): "
                    "r_n num n+1 = [[1, 1]]; r_n den (n+1)−k = [[1, 1], [-1]]; "
                    "r_k num n−k = [[0, 1], [-1]]; r_k den k+1 = [[1], [1]] → "
                    "zeilberger certifies f(n+1)−2f(n)=0 for ΣC(n,k)=2ⁿ. THE "
                    "ORPHAN FIX: BiPoly was CONSUMED by zeilberger / "
                    "wz_certificate but nothing in the registry RETURNED one "
                    "(rc113 shipped only the q-side qbipoly_from_coeffs), so "
                    "the classic non-q Zeilberger/WZ row was unreachable by "
                    "prose. A non_compute BUILDER (the from_bodies / "
                    "cooccurrence_edges precedent); ints only (a float / bool / "
                    "str leaf is an honest TypeError). numpy-free; no float; no "
                    "abs().",
            parameters=(P("coeffs", "list[list[int]]", True,
                          "k-ascending list of n-coefficient lists (coeffs[d] "
                          "is the ascending-n Poly coefficient of k**d)"),),
            returns=R("BiPoly",
                      "the exact-ℚ[n,k] bivariate carrier (chainable into the "
                      "zeilberger / wz_certificate rn/rk params)"),
            smoke_test_hint={"coeffs": "[[1, 1], [-1]]"},
        ),
        ToolEntry(
            name="srmech.amsc.tripoly.tripoly_from_coeffs", owner="srmech",
            category="tripoly",
            summary="PROSE-SIDE carrier constructor (#1248 / F1038; the ORPHAN "
                    "FIX): build the exact-ℚ[n,j,k] trivariate carrier TriPoly "
                    "from a j-ascending list of k-ascending lists of "
                    "INTEGER-LEAF n-coefficient lists — coeffs[dj] is the j**dj "
                    "block (a BiPoly in (n,k)), coeffs[dj][dk] its k**dk "
                    "coefficient (an ascending-n Poly-in-n int list). "
                    "tripoly_from_coeffs([[[0, 1]], [[1]]]) is n+j. The "
                    "bipoly_from_coeffs grammar recursed one level. THE ORPHAN "
                    "FIX: TriPoly was CONSUMED by apagodu_zeilberger but never "
                    "PRODUCED from the registry, so the multivariate "
                    "sums-of-sums row was unreachable by prose. A non_compute "
                    "BUILDER (the from_bodies / cooccurrence_edges precedent); "
                    "ints only (a float / bool / str leaf is an honest "
                    "TypeError). numpy-free; no float; no abs().",
            parameters=(P("coeffs", "list[list[list[int]]]", True,
                          "j-ascending list of j-blocks; each a k-ascending "
                          "list of ascending-n integer lists (coeffs[dj][dk] is "
                          "the Poly-in-n coefficient of j**dj·k**dk)"),),
            returns=R("TriPoly",
                      "the exact-ℚ[n,j,k] trivariate carrier (chainable into "
                      "the apagodu_zeilberger rn/rj/rk params)"),
            smoke_test_hint={"coeffs": "[[[0, 1]], [[1]]]"},
        ),
        ToolEntry(
            name="srmech.amsc.carrier_ladder.poly_promote", owner="srmech",
            category="carrier_ladder",
            summary="Promote an ordinary-ladder carrier UP the variable ladder "
                    "Poly(k) → BiPoly(n,k) → TriPoly(n,j,k) by the TRIVIAL "
                    "EMBEDDING (#1248 / F1038): add a degree-0 variable so the "
                    "polynomial is unchanged as a function but gains a formal "
                    "variable it does not depend on. n_vars is the target rung "
                    "(1/2/3; default one rung up); must be ≥ the current rung. "
                    "This is the 'a univariate IS trivially bivariate' fact "
                    "that lets a Poly feed zeilberger — a driver auto-routes a "
                    "lower-rung carrier UP to a higher-rung consumer. TOTAL "
                    "(a no-op when n_vars equals the current rung); the inverse "
                    "of poly_project (poly_project(poly_promote(x))==x EXACT). "
                    "Pure carrier restructuring (re-wrap embed; no numerical "
                    "kernel) → non_compute (the from_bodies / cooccurrence_edges "
                    "precedent). Exact-ℚ; numpy-free; no float; no abs().",
            parameters=(P("p", "Poly | BiPoly", True,
                          "the carrier to promote (Poly rung 1 / BiPoly rung 2 "
                          "/ TriPoly rung 3)"),
                        P("n_vars", "int", False,
                          "target rung 1/2/3 (default one rung up); must be ≥ "
                          "the current rung")),
            returns=R("BiPoly | TriPoly",
                      "the promoted carrier one-or-more rungs up (or the input "
                      "unchanged when n_vars == the current rung)"),
            smoke_test_hint={"p": "srmech.amsc.poly.Poly.from_coeffs([1, 1])"},
        ),
        ToolEntry(
            name="srmech.amsc.carrier_ladder.poly_project", owner="srmech",
            category="carrier_ladder",
            summary="Project an ordinary-ladder carrier DOWN one rung TriPoly → "
                    "BiPoly → Poly — the inverse of poly_promote (#1248 / "
                    "F1038). Drops the highest-rung variable IFF the carrier is "
                    "genuinely trivial in it (TriPoly drops j iff j_degree ≤ 0; "
                    "BiPoly drops n iff every k-coefficient is constant in n). "
                    "When the variable is genuinely PRESENT, raises a coherency "
                    "error that NAMES it (the beat-relation diagnostic style; "
                    "NEVER a silent truncation — the rc104 lesson). A rung-1 "
                    "Poly has no higher variable to drop → error. "
                    "poly_project(poly_promote(x))==x EXACT at every rung. Pure "
                    "carrier restructuring (trivial-check + drop; no numerical "
                    "kernel) → non_compute. Exact-ℚ; numpy-free; no float; no "
                    "abs().",
            parameters=(P("p", "BiPoly | TriPoly", True,
                          "the carrier to project down one rung (BiPoly → Poly, "
                          "or TriPoly → BiPoly)"),),
            returns=R("Poly | BiPoly",
                      "the projected carrier one rung down (raises a NAMING "
                      "coherency error if the dropped variable is non-trivial)"),
            smoke_test_hint={
                "p": "srmech.amsc.zeilberger.BiPoly.from_k_poly("
                     "srmech.amsc.poly.Poly.from_coeffs([1, 1]))"},
        ),
        ToolEntry(
            name="srmech.amsc.carrier_ladder.qpoly_promote", owner="srmech",
            category="carrier_ladder",
            summary="Promote a q-ladder carrier UP the variable ladder "
                    "QPoly(x=qⁿ) → QBiPoly(X=qⁿ, Y=qᵏ) by the trivial embedding "
                    "(#1248 / F1038) — the q-analog of poly_promote. Adds the "
                    "degree-0 variable Y=qᵏ (a single Y**0 cell). n_vars is the "
                    "target rung (1/2; default one rung up). TOTAL; the inverse "
                    "of qpoly_project (qpoly_project(qpoly_promote(x))==x "
                    "EXACT). Pure carrier restructuring → non_compute. Exact "
                    "over ℚ[q]; numpy-free; no float; no abs().",
            parameters=(P("p", "QPoly", True,
                          "the QPoly (rung 1) to promote to QBiPoly (rung 2)"),
                        P("n_vars", "int", False,
                          "target rung 1/2 (default one rung up)")),
            returns=R("QBiPoly",
                      "the promoted q-carrier one rung up (or the input "
                      "unchanged when n_vars == the current rung)"),
            smoke_test_hint={"p": "srmech.amsc.qpoly.QPoly.from_coeffs([0, 1])"},
        ),
        ToolEntry(
            name="srmech.amsc.carrier_ladder.qpoly_project", owner="srmech",
            category="carrier_ladder",
            summary="Project a q-ladder carrier DOWN one rung QBiPoly → QPoly — "
                    "the inverse of qpoly_promote (#1248 / F1038). Drops the "
                    "variable Y=qᵏ IFF the QBiPoly is genuinely trivial in it "
                    "(y_degree ≤ 0); returns that Y**0 cell (a QPoly in X=qⁿ). "
                    "When Y is genuinely present, raises a coherency error that "
                    "NAMES it (never a silent truncation). A rung-1 QPoly has no "
                    "higher variable to drop → error. "
                    "qpoly_project(qpoly_promote(x))==x EXACT. Pure carrier "
                    "restructuring → non_compute. Exact over ℚ[q]; numpy-free; "
                    "no float; no abs().",
            parameters=(P("p", "QBiPoly", True,
                          "the QBiPoly (rung 2) to project to QPoly (rung 1)"),),
            returns=R("QPoly",
                      "the projected q-carrier one rung down (raises a NAMING "
                      "coherency error if the dropped variable Y is non-trivial)"),
            smoke_test_hint={
                "p": "srmech.amsc.qbipoly.QBiPoly.from_x_qpoly("
                     "srmech.amsc.qpoly.QPoly.from_coeffs([0, 1]))"},
        ),
        ToolEntry(
            name="srmech.amsc.carrier_ladder.carrier_ladder_descriptor",
            owner="srmech", category="carrier_ladder",
            summary="The declarative CARRIER-LADDER coherency map (#1248 / "
                    "F1038; rc120 #1254 / F1041 adds the per-op contract) — a "
                    "small static descriptor a driver (siona's result register, "
                    "F1024) reads to auto-route a lower-rung carrier UP to any "
                    "consumer accepting a higher rung, AND to read the exact "
                    "rung each op consumes/produces. Returns {'carriers': "
                    "{<carrier>: {'ladder', 'rung'}}, 'ladders': {<ladder>: "
                    "{'rungs', 'adds_variable', 'promote', 'project'}}, 'ops': "
                    "{<op-leaf>: {'tool', 'consumes', 'produces'}}}. Three "
                    "ladders: 'variable' (Poly/BiPoly/TriPoly), 'variable_q' "
                    "(QPoly/QBiPoly), and 'cayley_dickson' (ℝ/ℂ/ℍ/𝕆/𝕊, keyed by "
                    "dimension — the dim cd_promote takes). The 'ops' map makes "
                    "the per-op carrier RUNG machine-readable so a driver routes "
                    "WITHOUT a name-map: ops['octonion_conjugate'] consumes "
                    "cayley_dickson rung 8; ops['cd_promote'] consumes 'any' "
                    "(variadic) and produces 'arg:dim' (rung-from-argument). Each "
                    "int rung agrees with the ladders rungs table. No compute (a "
                    "fixed table) → non_compute. numpy-free; no float.",
            parameters=(),
            returns=R("dict",
                      "{'carriers': {name: {'ladder', 'rung'}}, 'ladders': "
                      "{name: {'rungs', 'adds_variable', 'promote', "
                      "'project'}}, 'ops': {op-leaf: {'tool', 'consumes', "
                      "'produces'}}}"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc205 (gh #1293): the CARRIER (operand) introspection surface
        # — the noun-side DUAL of tool_schema (Siona / RBS-LM finding
        # 1110; UPSTREAM_NOTES §91): tool_schema exposes the ops (verbs)
        # richly, but the carrier TYPES (the operand nouns) were not
        # first-class introspectable — a consumer had to scrape
        # carrier_ladder_descriptor's ladder/rung INTS with no
        # human-readable description, so introspection could not say
        # what a TriPoly IS beyond "rung 3".
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.carrier_schema.carrier_schema",
            owner="srmech", category="carrier_schema",
            summary="The CARRIER (operand) introspection registry (gh "
                    "#1293) — the noun-side DUAL of tool_schema: per "
                    "carrier TYPE (the operand nouns Poly/BiPoly/TriPoly/"
                    "QPoly/QBiPoly, the Cayley–Dickson rungs float/complex/"
                    "quaternion/octonion/sedenion, Mat/Vec/HV, the exact "
                    "scalars int/Fraction/Q, the elliptic EllMonomial/"
                    "EllRatio/ThetaSum, the weight-axis UnaryTheta/"
                    "MockQSeries/HarmonicMaass, and the HDC objects One/"
                    "SedenionRegister) returns {'name', a one-line "
                    "human-readable 'description' (what it is, its variable "
                    "semantics, when to use it), 'ladder', 'rung', "
                    "'variables', 'ops': {'consumes', 'produces'}} keyed by "
                    "carrier name. The ops back-index is DERIVED (never "
                    "hand-maintained) from the ToolEntry param/return type "
                    "strings + the rc120 per-op carrier contract; ladder/"
                    "rung agree with carrier_ladder_descriptor. With "
                    "tool_schema this lets ANY consumer (Siona's "
                    "introspect_carriers; a human reader) discover BOTH the "
                    "verbs and the nouns and distinguish carriers that "
                    "differ only by a rung number. Native-dispatched to the "
                    "C peer srmech_carrier_schema over the compiled-in "
                    "srmech_carrier_registry const table (canonical JSON "
                    "byte-identical to the pure path — the sha256 "
                    "hash-ratchet); pure fallback complete → composes_c. "
                    "numpy-free; no float math.",
            parameters=(),
            returns=R("dict",
                      "{<carrier>: {'name', 'description', 'ladder', "
                      "'rung', 'variables', 'ops': {'consumes': [tool "
                      "names], 'produces': [tool names]}}}"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc225 (user design 2026-07-12): the RESPONSION (stored-
        # relationship) introspection surface — the k=3 completion of
        # the introspection triad. tool_schema exposes the OPS (verbs),
        # carrier_schema the OPERANDS (nouns) — the k=2 pair of NODES;
        # responsion_schema exposes the EDGES binding them: "this op,
        # on this operand, answers THIS way" (op⊗operand⊗responsion,
        # F1131/F1186 — the relationships the Stored-RELATIONSHIP
        # Mechanism is named for, previously un-introspectable).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.responsion_schema.responsion_schema",
            owner="srmech", category="responsion_schema",
            summary="The RESPONSION (stored-relationship) introspection "
                    "registry (rc225; user design 2026-07-12) — the k=3 "
                    "completion of the introspection triad: ops (tool_"
                    "schema) + operands (carrier_schema) are the k=2 pair "
                    "of NODES; the responsion is the EDGE that binds them "
                    "— this op, on this operand, answers THIS way. Keyed "
                    "by the '<operator>|<carrier>' EDGE (operator = a real "
                    "tool_schema key, carrier = a real carrier_schema key "
                    "— never a bare-name flat registry), each edge carries "
                    "one-or-more responsions {'operator', 'carrier', "
                    "'kind', 'regime', 'answers_with', 'status'}. TWO "
                    "REGIMES OF ONE RESPONSION held in unity: "
                    "discrete_algebraic = the F929 reduce-back rows "
                    "(gosper/zeilberger/wz_certificate, apagodu_"
                    "zeilberger, q_*, elliptic_wz_certificate, "
                    "multivariate_elliptic_jackson, resonant_spectrum, "
                    "coupling — operand → verified closed form; the OPEN "
                    "residues ride the infer router with answers_with "
                    "VERBATIM from dispatch._OPEN_HINTS, the honest F934 "
                    "sustain); continuous_spectral = the response-function "
                    "family of a generator L on an excitation u0 "
                    "(laplacian.responsion's propagator e^{-zL}·u0 ⊗ "
                    "resolvent (zI-L)^{-1}·u0 LAPLACE-DUAL PAIR on one "
                    "edge, propagate, heat_trace, ground_state_flux_"
                    "response). The genome tie-back: storage = carrier, "
                    "query = op excite, response = responsion. Native-"
                    "dispatched to the C peer srmech_responsion_schema "
                    "over the compiled-in srmech_responsion_registry "
                    "const table (canonical JSON byte-identical to the "
                    "pure path — the sha256 hash-ratchet); pure fallback "
                    "complete → composes_c. numpy-free; no float math.",
            parameters=(),
            returns=R("dict",
                      "{'<operator>|<carrier>': [{'operator', 'carrier', "
                      "'kind', 'regime', 'answers_with', 'status'}, ...]}"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc117 (dives #718/#719): OPERATORS⊗OPERANDS as ONE addressable
        # object — the op-carrying carrier (srmech.amsc.op_provenance).
        # The value of an inexact-frontier op is a PROJECTION; the exact
        # generating operation is the SSOT. carry() attaches the operation
        # to the result over a name-keyed registry (the genome op-log /
        # DSL run_toml_chain re-run-by-name model; existing signatures
        # untouched); op_provenance_hash is the Class-A canonical hasher
        # (C peer srmech_op_provenance_hash); op_verdict/family_verdict
        # are the honest ONE-SIDED verdict pair (EQUAL/SAME_TARGET or
        # UNKNOWN — never a false UNEQUAL: equality of programs is
        # undecidable); reproject re-runs the carried operation at a
        # different rung (the operation-as-SSOT win).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.op_provenance.carry", owner="srmech",
            category="op_provenance",
            summary="Run a registered value-inexact-frontier op AND attach "
                    "its exact generating operation — the op-carrying "
                    "carrier (rc117; dives #718/#719: the value is a "
                    "PROJECTION, the operation is the SSOT). Returns "
                    "{'value': the op's normal result, 'inputs': the "
                    "canonicalised pinned inputs, 'provenance': the record "
                    "{op, params, input_sha256, family, rung, leaves_exact, "
                    "chain_sha256}}. The registry covers the rc117 frontier: "
                    "the Class-N series_truncate family (sin/cos/exp/log1p/"
                    "atan; INTERIOR Taylor towers, rung=num_terms) + "
                    "best_rational (EDGE continued-fraction tower, rung="
                    "max_denominator) + the Class-L float64 producers "
                    "(jacobi_eigvals / symmetric_eigendecompose / "
                    "hermitian_eigendecompose / heat_trace / "
                    "resonant_spectrum; EDGE rotation-composition towers). "
                    "family = (NAMED target_id, tower_kind) — the "
                    "attestation-registry namespace: derived from exact "
                    "inputs (e.g. 'sin(1/1)', 'eigvals(sha256:<hash>)') or "
                    "caller-attested via family=; unnamed/float-leaf targets "
                    "get family None (instance-only) with leaves_exact False "
                    "recorded honestly. Param defaults are MATERIALISED so a "
                    "default and an explicit-default call carry ONE address. "
                    "Existing op signatures untouched (opt-in wrapper over a "
                    "name-keyed registry — the genome op-log / DSL "
                    "run_toml_chain model). numpy-free; no abs().",
            parameters=(P("op", "str", True,
                          "registered dotted op name (e.g. 'srmech.amsc."
                          "rational.sin_series_truncate')"),
                        P("inputs", "dict", True,
                          "pinned operand inputs keyed by name (series ops: "
                          "numerator/denominator; Class-L: matrix / L (+t))"),
                        P("params", "dict", False,
                          "op params (num_terms, tolerance, …); defaults "
                          "materialised into the record"),
                        P("family", "dict", False,
                          "optional caller-attested family naming "
                          "{'target_id': <named target>}; tower_kind is "
                          "op-intrinsic and not overridable")),
            returns=R("dict",
                      "{'value': op result, 'inputs': canonicalised inputs, "
                      "'provenance': {op, params, input_sha256, family, "
                      "rung, leaves_exact, chain_sha256}}"),
        ),
        ToolEntry(
            name="srmech.amsc.op_provenance.op_provenance_hash",
            owner="srmech", category="op_provenance",
            summary="The canonical op-provenance record hasher (Class A; "
                    "rc117): SHA-256 of the record's MPRRecord-style "
                    "canonical byte image json.dumps(record, sort_keys=True, "
                    "ensure_ascii=False), EXCLUDING the record's own cached "
                    "chain_sha256 field. This hash IS the operation address "
                    "op_verdict compares: two records hash equal IFF their "
                    "canonical images are byte-identical. The record must be "
                    "float-free canonical JSON — floats ride as "
                    "{'__float64__': float.hex(x)} exact-bit-pattern tags, "
                    "ints beyond int64 as {'__bigint__': '<decimal>'} "
                    "(carry() builds records in this form); raw floats are "
                    "REJECTED, never silently forked (C %.17g doubles are "
                    "not byte-identical to Python repr). 1:1 C peer "
                    "srmech_op_provenance_hash (srmech_json_parse → "
                    "canonical rewrite → srmech_sha256_hex; the IDENTICAL "
                    "digest from ANY JSON formatting of the same record; "
                    "native-authoritative when present, pure Python the "
                    "complete alternative). No raw hashlib (routes "
                    "sha256_bytes); numpy-free; no abs().",
            parameters=(P("record", "dict", True,
                          "the provenance record (float-free canonical "
                          "JSON-shaped dict; a chain_sha256 field is "
                          "ignored)"),),
            returns=R("str", "the 64-hex SHA-256 of the canonical record "
                             "image"),
        ),
        ToolEntry(
            name="srmech.amsc.op_provenance.op_verdict", owner="srmech",
            category="op_provenance",
            summary="The honest ONE-SIDED op-equality verdict (rc117; dive "
                    "#718 — the load-bearing contract): 'EQUAL' when the two "
                    "provenances' canonical chain hashes agree (recomputed, "
                    "never trusting the cached field) — identical generating "
                    "program + identical pinned inputs ⟹ the same ideal "
                    "object BY CONSTRUCTION, sound even where the float "
                    "readouts diverge in the last ulp (platform divergence "
                    "is a projection artifact, not a different object; when "
                    "leaves_exact is False the EQUAL means same-op-on-same-"
                    "bit-pattern, stated in the records). 'UNKNOWN' "
                    "otherwise — equality of programs is UNDECIDABLE, so a "
                    "different chain proves nothing: an algebraically-equal "
                    "but syntactically-different cascade, a different rung, "
                    "or a coincidentally-equal value from a different op all "
                    "stay UNKNOWN. NEVER a false 'UNEQUAL' and never a false "
                    "EQUAL — this asymmetry IS the contract. Accepts bare "
                    "records or full carry() results. numpy-free; no abs().",
            parameters=(P("p1", "dict", True,
                          "a provenance record or carry() result"),
                        P("p2", "dict", True,
                          "a provenance record or carry() result")),
            returns=R("str", "'EQUAL' | 'UNKNOWN' (one-sided; never a "
                             "false UNEQUAL)"),
        ),
        ToolEntry(
            name="srmech.amsc.op_provenance.family_verdict", owner="srmech",
            category="op_provenance",
            summary="The honest ONE-SIDED family verdict (rc117; dive #719): "
                    "'SAME_TARGET' when BOTH provenances carry a family (a "
                    "NAMED/ATTESTED target — the attestation-registry "
                    "namespace) and the full family addresses agree (same "
                    "target_id AND same tower_kind) — every truncation rung "
                    "of one target in one tower shares this address (the "
                    "asymptote addressed by its generator: N truncations = "
                    "1 family address + N instance addresses). 'UNKNOWN' "
                    "otherwise — NEVER a false 'DIFFERENT'. The tower "
                    "distinction is part of the address: the SAME named "
                    "target approached by the interior (Taylor additive) and "
                    "the edge (continued-fraction/rotation multiplicative) "
                    "towers is two DIFFERENT families (the shared target "
                    "stays visible by comparing target_id directly). Unnamed "
                    "targets (family None — float-leaf inputs) are "
                    "instance-only and always UNKNOWN here: family-equality "
                    "is decidable exactly when targets are named. Accepts "
                    "bare records or full carry() results. numpy-free; no "
                    "abs().",
            parameters=(P("p1", "dict", True,
                          "a provenance record or carry() result"),
                        P("p2", "dict", True,
                          "a provenance record or carry() result")),
            returns=R("str", "'SAME_TARGET' | 'UNKNOWN' (one-sided; never "
                             "a false DIFFERENT)"),
        ),
        ToolEntry(
            name="srmech.amsc.op_provenance.reproject", owner="srmech",
            category="op_provenance",
            summary="Re-run the carried operation at a (possibly different) "
                    "rung — the value RE-COMPUTED from the operation-as-SSOT "
                    "(rc117; dive #718: recompute the projection from the "
                    "carried exact operation, e.g. a series_truncate carrier "
                    "from N=3 to N=12 sharpening toward its named target). "
                    "Takes a carry() result (which carries the pinned "
                    "inputs) or a bare record + explicit inputs=; the "
                    "supplied inputs are RE-VERIFIED against the record's "
                    "input_sha256 before anything runs (the MPM "
                    "re-verification: a provenance that can't be re-verified "
                    "is broken). ONLY the op's declared rung (precision) "
                    "params may be overridden — overriding a non-rung param "
                    "would change the target (a different operation, not a "
                    "re-projection); an empty override re-derives the "
                    "carried value verbatim. The family address is "
                    "PRESERVED (rung-independent by construction): "
                    "family_verdict(carried, reprojected) == 'SAME_TARGET'. "
                    "Returns a fresh {'value','inputs','provenance'} "
                    "carry-result. Registry dispatch (the genome op-log / "
                    "DSL run_toml_chain re-run-by-name model). numpy-free; "
                    "no abs().",
            parameters=(P("provenance", "dict", True,
                          "a carry() result (carries inputs) or a bare "
                          "provenance record"),
                        P("overrides", "dict", False,
                          "rung (precision) param overrides, e.g. "
                          "{'num_terms': 12}"),
                        P("inputs", "dict", False,
                          "explicit pinned inputs when passing a bare "
                          "record (re-verified against input_sha256)")),
            returns=R("dict",
                      "a fresh {'value', 'inputs', 'provenance'} "
                      "carry-result at the new rung (same family)"),
        ),
        ToolEntry(
            name="srmech.amsc.op_provenance.lossy_projection_record",
            owner="srmech", category="op_provenance",
            summary="Build the exact op-address RECORD for a LOSSY-PROJECTION op "
                    "whose recovery is EXACT from its CARRIED complement (rc125; "
                    "task #723) — the DUAL face of the float/asymptotic-tower "
                    "projections carry() addresses. Where carry() addresses a "
                    "VALUE-INEXACT op (a float readout / a series truncation) "
                    "whose exactness lives in the ASYMPTOTIC generator, a "
                    "lossy-PROJECTION op is exact-in/exact-out: its projection "
                    "(the Klein-4 superposition collapse of a fold_encode) drops "
                    "information recoverable ONLY when the exact complement is "
                    "CARRIED alongside (the field–excitation recoverability "
                    "principle). So this record has family=None (NO asymptotic "
                    "target — not a tower converging to a limit), rung={} (NO "
                    "precision rung — recovery is EXACT at ANY dim because the "
                    "complement is carried, not decoded), and "
                    "projection_kind='hdc' (the genuine NON-ASYMPTOTIC kind, "
                    "recorded honestly rather than faking an interior/edge "
                    "tower_kind). It hashes via the SAME rc117 op_provenance_hash "
                    "canonical machinery to the projection's IDENTITY: two lossy "
                    "projections with byte-identical EXACT inputs share the "
                    "address (EQUAL), different exact inputs give a different "
                    "address — and because the inputs are EXACT a different "
                    "address is a genuinely different object, so NOT-EQUAL is "
                    "DECIDABLE here (unlike op_verdict's undecidable "
                    "program-equality, EQUAL/UNKNOWN only). The presence-of-"
                    "complement decidability IS the point. Widens the "
                    "op_provenance scope from 'value-inexact frontier' to "
                    "'lossy-projection'. numpy-free; no abs(); no raw hashlib "
                    "(routes sha256_bytes).",
            parameters=(P("op", "str", True,
                          "the dotted op name being addressed (e.g. "
                          "'srmech.amsc.coupling.fold_encode')"),
                        P("inputs", "dict", True,
                          "the EXACT operand inputs keyed by name (canonicalised "
                          "with the rc117 float-free canon; Q / int / rational "
                          "leaves ride as exact tags)")),
            returns=R("dict",
                      "the record {op, params: {}, input_sha256, family: None, "
                      "rung: {}, projection_kind: 'hdc', leaves_exact, "
                      "chain_sha256}"),
        ),
        # ────────────────────────────────────────────────────────────
        # The q-HYPERGEOMETRIC row of the §76 telescope Σ-row prover (F929) —
        # q-Gosper, the FIRST public op of the q-row (the q-analog of gosper).
        # Decides q-Gosper-summability of a q-hypergeometric term over the rc54
        # QPoly ℚ[q]-carrier (Laurent in x=qᵏ); 1:1 C peer srmech_q_gosper.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.q_gosper.q_gosper", owner="srmech",
            category="q_gosper",
            summary="The q-analog of Gosper's indefinite hypergeometric summation "
                    "(T.H. Koornwinder, 'On Zeilberger's algorithm and its "
                    "q-analogue', J. Comput. Appl. Math. 48:91–111, 1993; textbook "
                    "anchor Gasper & Rahman, *Basic Hypergeometric Series*) — the "
                    "FIRST public op of the q-hypergeometric F929 reduction row, the "
                    "q-analog of the §76 gosper. Input: a q-hypergeometric term given "
                    "by its TERM RATIO t(k+1)/t(k)=r(x)=num(x)/den(x), x=qᵏ, σ:x↦q·x "
                    "(the q-shift) — two Laurent polynomials in x over ℚ[q], each a "
                    "QPoly (the rc54 carrier this op consumes; a Poly-in-q / the "
                    "nested-list form coerces). Decides whether Σ t(k) has a "
                    "q-hypergeometric antidifference T(k)=R(qᵏ)·t(k) (so T(k+1)−T(k)="
                    "t(k), and the sum telescopes: Σ_{a}^{b} t = T(b+1)−T(a), with "
                    "R(qx)·r(x)−R(x)=1); if so returns the rational certificate "
                    "R={'num':QPoly,'den':QPoly}, else None (no q-hypergeometric "
                    "closed form). Exact over the FIELD ℚ(q) via the q-Gosper–"
                    "Petkovšek normal form (q-gcd/q-dispersion over ℚ(q)[x]) + the "
                    "bounded-degree undetermined-coefficient q-Gosper equation a(x)·"
                    "y(qx)−b(x/q)·y(x)=c(x) solved by exact Gauss-Jordan (QMat). 1:1 "
                    "C peer srmech_q_gosper (orchestrates srmech_qpoly_*/srmech_qmat_"
                    "rref; native completes the canonical constant-ratio q-geometric "
                    "case, pure-Python the complete alternative + the byte-identical "
                    "parity oracle — a has=0 is never a definitive 'no certificate'). "
                    "Exact bigint; no float, no abs() (Class-K sign), no numpy / math.",
            parameters=(P("rn_num", "QPoly", True,
                          "the term-ratio NUMERATOR num(x) — a Laurent-in-x exact-ℚ[q] "
                          "QPoly (or a Poly-in-q / nested-list ℚ[q] cell sequence)"),
                        P("rn_den", "QPoly", True,
                          "the term-ratio DENOMINATOR den(x) — a NONZERO QPoly")),
            returns=R("dict | None",
                      "{'num': QPoly, 'den': QPoly} (the rational certificate R(x) "
                      "with antidifference T(k)=R(qᵏ)·t(k)), or None when no "
                      "q-hypergeometric closed form exists"),
        ),
        # ────────────────────────────────────────────────────────────
        # The q-HYPERGEOMETRIC row of the §76 telescope Σ-row prover (F929) —
        # q-Zeilberger, the SECOND public op of the q-row (the q-analog of
        # zeilberger). Finds the linear q-recurrence of a DEFINITE q-sum over the
        # new bivariate-q QBiPoly carrier (Laurent in X=qⁿ, ascending in Y=qᵏ);
        # parametrizes the rc55 q-Gosper ℚ(q) solve. 1:1 C peer srmech_q_zeilberger.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.q_zeilberger.q_zeilberger", owner="srmech",
            category="q_zeilberger",
            summary="The q-analog of Zeilberger's creative telescoping (T.H. "
                    "Koornwinder, 'On Zeilberger's algorithm and its q-analogue', J. "
                    "Comput. Appl. Math. 48:91–111, 1993; textbook anchor Gasper & "
                    "Rahman, *Basic Hypergeometric Series*) — the SECOND public op of "
                    "the q-hypergeometric F929 reduction row, the q-analog of the §76 "
                    "zeilberger (and the recurrence-finder the q-WZ proof op rc57 "
                    "builds on). Input: a proper q-hypergeometric term F(n,k) given by "
                    "its TWO bivariate-q term ratios over (X,Y)=(qⁿ,qᵏ): r_n(X,Y)="
                    "F(n+1,k)/F(n,k) and r_k(X,Y)=F(n,k+1)/F(n,k), each a QBiPoly (a "
                    "polynomial in Y=qᵏ whose coefficients are QPoly in X=qⁿ; a QPoly "
                    "in Y / a Poly-in-q / a nested-list form coerces). Produces the "
                    "minimal-order linear q-recurrence Σ_{j=0}^{L} a_j(qⁿ)·f(n+j)=0 "
                    "(f(n)=Σ_k F(n,k)), the a_j exact QPoly in X=qⁿ over ℚ(q), plus the "
                    "q-Gosper certificate x(X,Y) (R=x/D_P; the q-WZ relation Σ_j a_j "
                    "F(n+j,k)=Δ_q(R·F) holds exactly), or None when no recurrence of "
                    "order ≤ max_order exists. Exact over the FIELD ℚ(q) via the "
                    "PARAMETRIZED rc55 q-Gosper undetermined-coefficient solve (reuses "
                    "the q-Gosper _Cq ℚ(q) field + Gauss-Jordan with the a_j(qⁿ) as "
                    "extra unknowns; a homogeneous ℚ(q) kernel with a nonzero a-block "
                    "is the recurrence). 1:1 C peer srmech_q_zeilberger (orchestrates "
                    "the srmech_qpoly q-algebra + srmech_qmat_rref; native completes "
                    "the canonical k-free q-geometric order-1 case, pure-Python the "
                    "complete alternative + the byte-identical parity oracle — a has=0 "
                    "is never a definitive 'no recurrence'). Exact bigint; no float, no "
                    "abs() (Class-K sign), no numpy / math.",
            parameters=(P("rn_num", "QBiPoly", True,
                          "r_n NUMERATOR — the F(n+1,k)/F(n,k) numerator, a bivariate-q "
                          "QBiPoly (or a QPoly-in-Y / Poly-in-q / nested-list form)"),
                        P("rn_den", "QBiPoly", True,
                          "r_n DENOMINATOR — a NONZERO bivariate-q QBiPoly"),
                        P("rk_num", "QBiPoly", True,
                          "r_k NUMERATOR — the F(n,k+1)/F(n,k) numerator, a QBiPoly"),
                        P("rk_den", "QBiPoly", True,
                          "r_k DENOMINATOR — a NONZERO bivariate-q QBiPoly"),
                        P("max_order", "int", False,
                          "the largest ansatz recurrence order to try (default 6)")),
            returns=R("dict | None",
                      "{'order': int, 'coeffs': [QPoly, ...], 'certificate': QBiPoly} "
                      "— the minimal-order q-recurrence Σ_j coeffs[j](qⁿ)·f(n+j)=0 plus "
                      "the q-Gosper rational certificate x(X,Y), or None when none of "
                      "order ≤ max_order"),
        ),
        # ────────────────────────────────────────────────────────────
        # The q-HYPERGEOMETRIC row of the §76 telescope Σ-row prover (F929) —
        # q-WZ, the THIRD and FINAL public op of the q-row (the q-analog of
        # wz_certificate; the q-row CLOSER, and the closer of the WHOLE
        # multivariate + q-hypergeometric reduction-theory arc). FINDs via
        # q_zeilberger at the forced recurrence + VERIFIES the q-WZ equation as
        # an exact bivariate-ℚ[q] rational identity; 1:1 C peer srmech_q_wz_verify
        # is the COMPLETE verify mirror (degree-bounded, no order cap).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.q_wz_certificate.q_wz_certificate", owner="srmech",
            category="q_wz_certificate",
            summary="The q-analog of the Wilf–Zeilberger pair method (T.H. "
                    "Koornwinder, 'On Zeilberger's algorithm and its q-analogue', J. "
                    "Comput. Appl. Math. 48:91–111, 1993; the q-WZ pair anchor is H. "
                    "Wilf & D. Zeilberger, 'An algorithmic proof theory for "
                    "hypergeometric (ordinary and q) multisum/integral identities', "
                    "Invent. Math. 108:575–633, 1992; textbook anchor Gasper & Rahman, "
                    "*Basic Hypergeometric Series*) — the THIRD and FINAL public op of "
                    "the q-hypergeometric F929 reduction row, the q-row CLOSER (and the "
                    "closer of the whole multivariate + q-hypergeometric reduction-"
                    "theory arc): q_gosper (indefinite) → q_zeilberger (recurrence) → "
                    "q_wz_certificate (proof). PROVES a terminating q-hypergeometric "
                    "identity Σ_k F(n,k)=const by producing AND verifying its q-WZ "
                    "certificate. Input: F's two bivariate-q term ratios over "
                    "(X,Y)=(qⁿ,qᵏ): r_n(X,Y)=F(n+1,k)/F(n,k) and r_k(X,Y)=F(n,k+1)/"
                    "F(n,k), each a QBiPoly num/den pair (the SAME operands "
                    "q_zeilberger takes; a QPoly in Y / a Poly-in-q / a nested-list "
                    "coerces). The q-WZ method is q-Zeilberger at the FORCED "
                    "n-recurrence f(n+1)−f(n)=0: it FINDs the certificate R(X,Y) "
                    "(=q_zeilberger at max_order=1, the order-1 recurrence of a constant "
                    "q-sum, scaled to the [−1,+1] WZ recurrence) such that G=R·F makes "
                    "the q-WZ equation F(n+1,k)−F(n,k)=G(n,k+1)−G(n,k) q-telescope "
                    "(G(n,k+1)=(σ_y R)·(σ_y F), σ_y:Y↦qY), then VERIFIES that equation "
                    "as an EXACT bivariate-ℚ[q] rational-function identity (clearing "
                    "denominators to a polynomial identity — no solve, no order bound). "
                    "Returns {'certificate':{'num':QBiPoly,'den':QBiPoly},'verified':"
                    "True}, or None when the term is not q-WZ-summable (incl. a term "
                    "q_zeilberger cannot reduce on its supported path). 1:1 C peer "
                    "srmech_q_wz_verify is the COMPLETE verify mirror (the degree-"
                    "bounded exact bivariate-ℚ[q] identity check, NOT order-bounded — "
                    "unlike the rc56 q_zeilberger order-≤1 peer; native when present, "
                    "pure-Python the complete alternative + the byte-identical parity "
                    "oracle). Exact bigint; no float, no abs() (Class-K sign), no "
                    "numpy / math.",
            parameters=(P("rn_num", "QBiPoly", True,
                          "r_n NUMERATOR — F(n+1,k)/F(n,k) numerator, a bivariate-q "
                          "QBiPoly (or a QPoly-in-Y / Poly-in-q / nested-list form)"),
                        P("rn_den", "QBiPoly", True,
                          "r_n DENOMINATOR — a NONZERO bivariate-q QBiPoly"),
                        P("rk_num", "QBiPoly", True,
                          "r_k NUMERATOR — F(n,k+1)/F(n,k) numerator QBiPoly"),
                        P("rk_den", "QBiPoly", True,
                          "r_k DENOMINATOR — a NONZERO bivariate-q QBiPoly")),
            returns=R("dict | None",
                      "{'certificate': {'num': QBiPoly, 'den': QBiPoly}, 'verified': "
                      "True} — the q-WZ certificate R(X,Y)=num/den (verified to satisfy "
                      "the q-WZ equation), or None when the term is not q-WZ-summable"),
        ),
        # ────────────────────────────────────────────────────────────
        # The ELLIPTIC row of the F929 Σ-row prover — elliptic-Gosper, the FIRST
        # ENGINE op of the ELLIPTIC row (the top of the base-axis degeneration tower
        # elliptic → q → ordinary). Indefinite elliptic-hypergeometric summation over
        # the modified-theta EllRatio carrier (rc59 ellbase + rc60 EllRatio); the
        # elliptic analogue of gosper / q_gosper, ONE algebra up. 1:1 C peer
        # srmech_elliptic_gosper.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_gosper.elliptic_gosper", owner="srmech",
            category="elliptic_gosper",
            summary="The ELLIPTIC analog of Gosper's indefinite hypergeometric "
                    "summation (George Gasper & Michael Schlosser, 'Summation, "
                    "transformation, and expansion formulas for multibasic theta "
                    "hypergeometric series', Adv. Stud. Contemp. Math. (Kyungshang) "
                    "11, no. 1 (2005), 67–84, arXiv:math/0505215 — derived 'using "
                    "indefinite summation', the theta/elliptic analogue of Gosper's "
                    "telescoping; secondary anchor S.O. Warnaar, Constr. Approx. 18 "
                    "(2002) 479–502; keystone the Frenkel–Turaev ₁₀E₉ sum) — the "
                    "FIRST engine op of the ELLIPTIC F929 reduction row, the top of "
                    "the base-axis degeneration tower elliptic→q→ordinary, the "
                    "elliptic analogue of gosper / q_gosper ONE algebra up. Input: an "
                    "elliptic-hypergeometric term given by its TERM RATIO t(n+1)/t(n)="
                    "r(x), x=qⁿ, σ:x↦q·x (the summation shift) — an EllRatio (the rc60 "
                    "theta-quotient carrier ∏θ(αx;p)/∏θ(βx;p) over an exact-ℚ monomial "
                    "prefactor; an EllMonomial / Theta lifts). Gates on the balancing / "
                    "very-well-poised predicate (r.is_elliptic(), Gasper–Schlosser Eq. "
                    "(2.4)); an unbalanced ratio is out of the row → None. Decides "
                    "whether Σ t(n) has an elliptic-hypergeometric antidifference T(n)="
                    "R(x)·t(n) (so T(n+1)−T(n)=t(n), the sum telescopes, and the "
                    "elliptic Gosper equation R(qx)·r(x)−R(x)=1 holds); if so returns "
                    "the certificate R (an EllRatio), else None. The GENUINE structural "
                    "finder (decompose-and-compute): PEEL the q-shift coboundary to the "
                    "theta-Gosper–Petkovšek normal form r=(A/B)·(σC/C), then SOLVE the "
                    "Weierstrass three-term key equation (Rosengren arXiv:1608.06161 §1.4 "
                    "Eq.(1.12)) for the certificate R=(B(x/q)/C)·y with the ≤8 chiral "
                    "endianness combos resolved against the exact verifier. Exact over the "
                    "modified-theta algebra (no float); the additive Gosper equation is "
                    "decided structurally via the additive ThetaSum.is_zero (the theta-"
                    "quotient carrier is multiplicatively but not additively closed — never "
                    "a converging-eval witness). 1:1 C peer srmech_elliptic_gosper mirrors "
                    "the peel-solve structure (peel the coboundary over the integer theta-"
                    "exponent lattice, build the ≤8 endianness candidates, verify via the "
                    "native srmech_thetasum is_zero); pure-Python is the complete "
                    "alternative + the byte-identical parity oracle — a has=0 is never a "
                    "definitive 'no certificate'. Exact bigint; no float, no abs() (Class-K "
                    "sign), no numpy / math.",
            parameters=(P("r", "EllRatio", True,
                          "the elliptic-hypergeometric TERM RATIO t(n+1)/t(n)=r(x), "
                          "x=qⁿ — an EllRatio (a theta-quotient over an exact-ℚ monomial "
                          "prefactor; an EllMonomial / Theta is lifted)"),),
            returns=R("dict | None",
                      "{'prefactor': {'coeff': (num, den), 'exps': {sym: exp}}, 'num': "
                      "[{sym: exp}, …], 'den': [{sym: exp}, …], 'certificate': EllRatio} "
                      "— the certificate R(x) satisfying R(qx)·r(x)−R(x)=1 (so T(n)="
                      "R(qⁿ)·t(n) is the antidifference), or None when no elliptic-"
                      "hypergeometric antidifference exists / r is unbalanced"),
        ),
        # ────────────────────────────────────────────────────────────
        # The #712 Dzhanibekov harmonic⊗subharmonic HALF-PERIOD readers on the
        # EllRatio carrier (rc119): the torque-free (tennis-racket) rotation's
        # Jacobi sn/cn/dn map to theta quotients (DLMF 22.2/22.4; bridge
        # w=e^{iζ}, x=w², carrier-p=q_c²); its two-torus has TWO half-beats.
        # half_shift_response is a C-dispatched compute op (srmech_ellratio_
        # half_shift_response); chirality_parity + beat_relation_residue are
        # thin structural readers (non_compute). In-repo SSoT: the #712 probes.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.ellbase.half_shift_response", owner="srmech",
            category="ellbase",
            summary="The exact monomial MULTIPLIER an EllRatio theta-quotient carrier "
                    "acquires under a HALF-period translation of the torque-free "
                    "(Dzhanibekov / tennis-racket) rotation torus (#712; DLMF 22.4). "
                    "The Jacobi sn/cn/dn map to EllRatio theta quotients under the "
                    "bridge w=e^{iζ}, x=w², carrier-p=q_c² (DLMF 22.2/20.5); the "
                    "solution two-torus has TWO independent half-beats. axis 'real'/"
                    "'2K' → the double-cover deck transformation var↦−var (z↦z+2K ⇔ "
                    "w↦−w): the multiplier is the pure Class-K sign (−1)^{var-parity "
                    "of the prefactor} (default var 'w', the subharmonic half-var); "
                    "bare iff every theta arg is EVEN in var. axis 'nome'/\"2iK'\" → "
                    "the carrier PERIOD shift var↦p·var (z↦z+2iK' ⇔ x↦p·x): the "
                    "multiplier is the −x⁻¹-type Theta.canonicalize quasi-periodicity "
                    "prefactor (default var 'x'). The EDGE-relationship read — exact "
                    "even where the theta value is transcendental (the full pshift "
                    "already exists; this is the HALF + reads only the multiplier). "
                    "Reproduces the #712 probe dzhan_q2 (sn/cn/dn real-2K −1/−1/+1; "
                    "nome pshift theta-parts q/−q/−1). 1:1 C peer srmech_ellratio_"
                    "half_shift_response (the multiplier EQUALS the pure-Python "
                    "EllMonomial byte-for-byte). Exact-ℚ theta algebra; no float, no "
                    "abs() (sign is Class-K), no numpy / math.",
            parameters=(
                P("ratio", "EllRatio", True,
                  "the theta-quotient carrier ∏θ(αx;p)/∏θ(βx;p) over an exact-ℚ "
                  "monomial prefactor (an EllMonomial / Theta is lifted)"),
                P("axis", "str", True,
                  "the half-beat axis: 'real'/'2K' (the real 2K half-beat) or "
                  "'nome'/\"2iK'\" (the nome 2iK′ half-beat); case-/apostrophe-"
                  "insensitive"),
                P("var", "str", False,
                  "the shift variable (default 'w' for the real axis — the "
                  "subharmonic half-variable; 'x' for the nome axis — the summation "
                  "variable)"),
            ),
            returns=R("EllMonomial",
                      "the exact edge multiplier as an EllMonomial (Class-K ±1 "
                      "coefficient; p/x/q-power exponents); ValueError when the ratio "
                      "is not half-shift-covariant along axis/var (the multiplier is "
                      "not a bare monomial)"),
        ),
        ToolEntry(
            name="srmech.amsc.ellbase.chirality_parity", owner="srmech",
            category="ellbase",
            summary="The CHIRALITY parity of an EllRatio theta-quotient carrier under "
                    "the #712 harmonic⊗subharmonic reading: 'even' (a HARMONIC reader "
                    "— closes under a SINGLE 2K half-beat, like dn: real period 2K) "
                    "vs 'odd' (a SUBHARMONIC reader — needs 4K / the PAIR, like sn/cn: "
                    "real period 4K, half the harmonic frequency). Read as the parity "
                    "of the var-exponent of the prefactor (default var 'w'): EVEN ⇔ "
                    "the real-2K half_shift_response is +1 (boundary-blind — cannot "
                    "see the Dzhanibekov flip); ODD ⇔ it is −1 (holds the flip). A "
                    "thin structural read (Class-K parity; non_compute). Reproduces "
                    "the #712 probes dzhan_q3/q4 (sn/cn odd, dn even; every quadratic/"
                    "intensity observable sn²/cn²/sn·cn/… even — boundary-blind).",
            parameters=(
                P("ratio", "EllRatio", True,
                  "the theta-quotient carrier to classify"),
                P("var", "str", False,
                  "the subharmonic half-variable whose prefactor-exponent parity is "
                  "the chirality (default 'w')"),
            ),
            returns=R("str",
                      "'even' (harmonic; closes under one 2K half-beat) or 'odd' "
                      "(subharmonic; needs 4K / the pair)"),
        ),
        ToolEntry(
            name="srmech.amsc.ellbase.beat_relation_residue", owner="srmech",
            category="ellbase",
            summary="The exact BEAT-RELATION residue of an EllRatio written on the "
                    "HARMONIC (x) frame: the nome-axis (period-shift var↦p·var) "
                    "mismatch monomial that RECOVERS the #712 beat relation p=q_c² "
                    "(the harmonic torus nome is the SQUARE of the subharmonic half-"
                    "step). For the harmonic sn² object x⁻¹·θ(x)²/θ(q·x)² the residue "
                    "is exactly q²·p⁻¹ — the coherence residue the carrier surfaces "
                    "unprompted (is_elliptic honestly declines it; the residue is "
                    "unity ⇔ p=q²). Equivalent to half_shift_response(ratio,'nome') "
                    "read as the beat-relation constraint; a thin structural read "
                    "(composes the carrier period-shift; non_compute). Reproduces the "
                    "#712 probe dzhan_q4 (residue q²·p⁻¹; closes at q=3/7, p=9/49).",
            parameters=(
                P("ratio", "EllRatio", True,
                  "the theta-quotient carrier (the harmonic-frame square, e.g. sn²)"),
                P("var", "str", False,
                  "the summation variable of the harmonic frame (default 'x')"),
            ),
            returns=R("EllMonomial",
                      "the exact beat-relation residue as an EllMonomial (q²·p⁻¹ for "
                      "the harmonic sn²; evaluates to 1 exactly at p=q_c²)"),
        ),
        # ────────────────────────────────────────────────────────────
        # The ELLIPTIC Σ-row ORDER-1 RECURRENCE op for the Frenkel–Turaev ₈ω₇
        # summation — a STRUCTURAL (beat-decomposition) finder that builds the
        # order-1 recurrence coefficient ρ(n) from the elementary symmetric
        # functions of the free params (NOT a coefficient nullspace solve —
        # provably dead for the elliptic case; the anti-brute-force discipline).
        # 1:1 C peer srmech_elliptic_recurrence_8w7.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7",
            owner="srmech", category="elliptic_recurrence",
            summary="The ELLIPTIC Σ-row ORDER-1 RECURRENCE op for the Frenkel–"
                    "Turaev ₈ω₇ summation (S. Ole Warnaar, 'Summation and "
                    "transformation formulas for elliptic hypergeometric series', "
                    "Constr. Approx. 18 (2002) 479–502, arXiv:math/0001006, "
                    "Corollary 2.2 — the ₈ω₇ closed product form "
                    "(aq, aq/bc, aq/bd, aq/cd; q,p)_n / (aq/b, aq/c, aq/d, aq/bcd; "
                    "q,p)_n; balancing bcde=a²q^{n+1}). A STRUCTURAL (beat-"
                    "decomposition) finder: it RECOGNIZES a canonical ₈ω₇ term "
                    "ratio t(n+1)/t(n)=r(x) (x=qⁿ — the very-well-poised core "
                    "θ(aq²x²)θ(ax)/[θ(ax²)θ(qx)] over five Pochhammer pairs θ(ux)/"
                    "θ(aqx/u) with the balancing) as an EllRatio, DECOMPOSES it "
                    "into the base a + the three FREE params [b,c,d], and "
                    "CONSTRUCTS the order-1 recurrence coefficient ρ(n) (an "
                    "EllRatio in y=qⁿ, 4 num + 4 den thetas) from the elementary "
                    "symmetric functions s2={bc,bd,cd}, s3=bcd: num endpoints "
                    "{aq}∪{aq/bc,aq/bd,aq/cd}, den {aq/b,aq/c,aq/d}∪{aq/bcd}. The "
                    "construction IS the answer (decompose-and-compute, NOT a "
                    "coefficient nullspace solve — provably dead for the elliptic "
                    "case; the anti-brute-force discipline). Returns {'order':1, "
                    "'coeffs':[-ρ,1], 'rho':ρ, …} (f(n+1)=ρ(n)·f(n)) only after "
                    "VERIFYING ρ(n)==f(n+1)/f(n) for the ₈ω₇ sum to <1e-9 (the "
                    "closed product form the independent oracle, via the carrier's "
                    "exact-ℚ truncated-theta eval — NOT a standalone numeric "
                    "theta); a non-₈ω₇ (unbalanced / wrong very-well-poised shape / "
                    "≠3 free params) or a ρ that fails the gate → None (the honest "
                    "out-of-class residue). 1:1 C peer srmech_elliptic_recurrence_"
                    "8w7 mirrors the recognize-decompose-construct over the integer "
                    "theta-exponent lattice (the shared srmech_ellbase_* monomial "
                    "algebra + er_build); the Python trusts a native ρ ONLY after a "
                    "byte-for-byte rebuild + the gate (a has=0 → Python pure path). "
                    "Exact bigint; no float, no abs() (Class-K sign), no numpy / "
                    "math.",
            parameters=(P("r", "EllRatio", True,
                          "the ₈ω₇ summand's TERM RATIO t(n+1)/t(n)=r(x), x=qⁿ — an "
                          "EllRatio (the very-well-poised theta-quotient over an "
                          "exact-ℚ monomial prefactor; an EllMonomial / Theta is "
                          "lifted)"),),
            returns=R("dict | None",
                      "{'order': 1, 'coeffs': [-ρ, 1], 'rho': EllRatio, "
                      "'prefactor': {'coeff': (num, den), 'exps': {sym: exp}}, "
                      "'num': [{sym: exp}, …], 'den': [{sym: exp}, …]} — the order-1 "
                      "recurrence f(n+1)=ρ(n)·f(n) (ρ an EllRatio in y=qⁿ, 4 num + 4 "
                      "den thetas, verified ρ(n)==f(n+1)/f(n)), or None when r is not "
                      "a canonical ₈ω₇ / the recurrence fails the gate"),
        ),
        # ────────────────────────────────────────────────────────────
        # The ELLIPTIC Σ-row CREATIVE-TELESCOPING op for the Frenkel–Turaev
        # ₈ω₇ summation — the order-1 recurrence ρ(n) PLUS an EXACT connection-
        # coefficient certificate that PROVES it (the ThetaSum.is_zero decision,
        # NOT rc68's 1e-9 numerical convergence gate). The third elliptic Σ-row
        # rung after elliptic_gosper (indefinite) + elliptic_recurrence_8w7
        # (the order-1 finder). 1:1 C peer srmech_elliptic_zeilberger.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_zeilberger.elliptic_zeilberger",
            owner="srmech", category="elliptic_zeilberger",
            summary="The ELLIPTIC Σ-row CREATIVE-TELESCOPING op for the Frenkel–"
                    "Turaev ₈ω₇ summation — the order-1 recurrence f(n+1)=ρ(n)·"
                    "f(n) PLUS an EXACT connection-coefficient certificate that "
                    "PROVES it (Hjalmar Rosengren, 'Elliptic Hypergeometric "
                    "Functions', arXiv:1608.06161v3 [math.CA] (2017), §2.3 Eqs. "
                    "(2.12)–(2.14) — the connection-coefficient expansion + the "
                    "elliptic binomial coefficient + the elliptic Pascal "
                    "recurrence, which reduce to §1.4 Eq. (1.12), the Weierstrass "
                    "three-term theta relation; the closed product form + ρ are "
                    "Warnaar, Constr. Approx. 18 (2002) 479–502, Cor 2.2). The "
                    "GENUINE elliptic analogue of zeilberger / q_zeilberger, the "
                    "THIRD rung of the elliptic Σ-row after elliptic_gosper "
                    "(indefinite) + elliptic_recurrence_8w7 (the order-1 finder, "
                    "whose verification gate was a 1e-9 numerical convergence "
                    "check). Where elliptic_recurrence_8w7 only checked ρ(n) "
                    "numerically, this op REPLACES that gate with an EXACT proof: "
                    "it RECOGNIZES the ₈ω₇ term ratio r(x)=t(n+1)/t(n) (x=qⁿ — an "
                    "EllRatio), DECOMPOSES it into a + [b,c,d], CONSTRUCTS ρ "
                    "(Warnaar Cor 2.2), and CERTIFIES the recurrence by deciding "
                    "the connection-coefficient inductive-step identity ≡ 0 in the "
                    "exact additive ThetaSum carrier (the cleared ±-pair split "
                    "θ(bcN,(b/c)K²/N)·θ(aN·x^±) − θ(acN²/K,(a/c)K)·θ(bK·x^±) + "
                    "(b/c)(K²/N)·θ(abNK,(a/b)N/K)·θ(cN/K·x^±) ≡ 0, N=qⁿ, K=qᵏ — "
                    "every term two clean ±-pairs the ThetaSum.is_zero reduces). "
                    "Returns {'order':1, 'coeffs':[-ρ,1], 'rho':ρ, 'certificate':"
                    "{'kind':'connection_coefficient_split', 'exact':True, …}, "
                    "'verified':True, …} (f(n+1)=ρ(n)·f(n) with the EXACT "
                    "certificate) ONLY when r is a canonical ₈ω₇ AND the "
                    "certificate decides ≡ 0; else None (the honest out-of-class "
                    "residue / certificate-did-not-close). 1:1 C peer "
                    "srmech_elliptic_zeilberger orchestrates the same recognize-"
                    "decompose pipeline + builds the connection-coefficient split "
                    "terms and decides them via the shared srmech_thetasum_is_zero "
                    "kernel; the Python trusts a native has=1 ONLY after the pure "
                    "path agrees AND the certificate re-decides ≡ 0 in exact ℚ. "
                    "Exact over the modified-theta algebra (no float on the "
                    "decision path), no abs() (Class-K sign), no numpy / math.",
            parameters=(P("r", "EllRatio", True,
                          "the ₈ω₇ summand's TERM RATIO t(n+1)/t(n)=r(x), x=qⁿ — an "
                          "EllRatio (the very-well-poised theta-quotient over an "
                          "exact-ℚ monomial prefactor; an EllMonomial / Theta is "
                          "lifted)"),),
            returns=R("dict | None",
                      "{'order': 1, 'coeffs': [-ρ, 1], 'rho': EllRatio, "
                      "'certificate': {'kind': 'connection_coefficient_split', "
                      "'exact': True, …}, 'verified': True, 'prefactor': …, "
                      "'num': [{sym: exp}, …], 'den': […]} — the order-1 recurrence "
                      "f(n+1)=ρ(n)·f(n) PLUS the EXACT connection-coefficient "
                      "certificate (decided ≡ 0 in the additive ThetaSum carrier), "
                      "or None when r is not a canonical ₈ω₇ / the certificate fails "
                      "to close"),
        ),
        # ────────────────────────────────────────────────────────────
        # The ELLIPTIC Σ-row IDENTITY-PROOF op for the Frenkel–Turaev ₈ω₇
        # SUMMATION — proves Σ_k F(n,k) = cf(n) EXACTLY and returns the closed
        # form cf(n). The CAPSTONE elliptic Σ-row rung after elliptic_gosper
        # (indefinite), elliptic_recurrence_8w7 (the order-1 finder) +
        # elliptic_zeilberger (the recurrence + EXACT certificate). Where
        # elliptic_zeilberger proves the RECURRENCE, this proves the full
        # SUMMATION (the elliptic analogue of wz_certificate). 1:1 C peer
        # srmech_elliptic_wz_certificate (same certificate decision).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate",
            owner="srmech", category="elliptic_wz_certificate",
            summary="The ELLIPTIC Σ-row IDENTITY-PROOF op for the Frenkel–Turaev "
                    "₈ω₇ SUMMATION — proves Σ_{k=0}^n F(n,k)=cf(n) EXACTLY and "
                    "returns the closed form cf(n)=(aq, aq/bc, aq/bd, aq/cd; q,p)_n "
                    "/ (aq/b, aq/c, aq/d, aq/bcd; q,p)_n (Hjalmar Rosengren, "
                    "'Elliptic Hypergeometric Functions', arXiv:1608.06161v3 "
                    "[math.CA] (2017), Thm 2.3.1; §2.3 Eqs. (2.12)–(2.15) reduce "
                    "to §1.4 Eq. (1.12), the Weierstrass three-term theta relation; "
                    "the closed product form is Warnaar, Constr. Approx. 18 (2002) "
                    "479–502, Cor 2.2). The CAPSTONE rung of the elliptic Σ-row "
                    "after elliptic_gosper (indefinite), elliptic_recurrence_8w7 "
                    "(the order-1 finder) and elliptic_zeilberger (the recurrence + "
                    "EXACT certificate) — the GENUINE elliptic analogue of "
                    "wz_certificate (the §76 ordinary/q identity-proof rung). Where "
                    "elliptic_zeilberger proves the RECURRENCE f(n+1)=ρ(n)·f(n), "
                    "this op proves the full SUMMATION IDENTITY by connection-"
                    "coefficient INDUCTION: the BASE CASE (the terminating "
                    "(q^{-n})_k factor leaves only k=0, so Σ_{k=0}^0 F(0,k)=cf(0)=1) "
                    "+ the EXACT inductive-step certificate (the SAME cleared "
                    "connection-coefficient ±-pair split elliptic_zeilberger builds, "
                    "decided ≡ 0 in the exact additive ThetaSum carrier via "
                    "ThetaSum.is_zero — never a 1e-9 numerical witness). A literal "
                    "Wilf–Zeilberger pair is provably dead for the elliptic case "
                    "(the squared-lattice Gosper–Petkovšek certificate); the proof "
                    "is the literature's connection-coefficient induction. Returns "
                    "{'identity': '…', 'closed_form': {'num': [4 bases], 'den': "
                    "[4 bases]}, 'certificate': {'method': "
                    "'connection_coefficient_induction', 'exact': True, …}, "
                    "'verified': True} ONLY when r is a canonical ₈ω₇ AND the "
                    "certificate decides ≡ 0; else None (the honest out-of-class "
                    "residue). 1:1 C peer srmech_elliptic_wz_certificate runs the "
                    "same recognize-decompose pipeline + decides the certificate via "
                    "the shared srmech_thetasum_is_zero kernel; the Python builds the "
                    "closed-form endpoints on its side and trusts a native has=1 ONLY "
                    "after the pure path agrees AND the certificate re-decides ≡ 0 in "
                    "exact ℚ. Exact over the modified-theta algebra (no float on the "
                    "decision path), no abs() (Class-K sign), no numpy / math.",
            parameters=(P("r", "EllRatio", True,
                          "the ₈ω₇ summand's TERM RATIO t(n+1)/t(n)=r(x), x=qⁿ — an "
                          "EllRatio (the very-well-poised theta-quotient over an "
                          "exact-ℚ monomial prefactor; an EllMonomial / Theta is "
                          "lifted)"),),
            returns=R("dict | None",
                      "{'identity': str, 'closed_form': {'num': [{sym: exp}, …4], "
                      "'den': [{sym: exp}, …4]}, 'certificate': {'method': "
                      "'connection_coefficient_induction', 'base_case': '…', "
                      "'inductive_step': '…', 'exact': True}, 'verified': True} — the "
                      "closed form cf(n) = (aq, aq/bc, aq/bd, aq/cd; q,p)_n / "
                      "(aq/b, aq/c, aq/d, aq/bcd; q,p)_n PLUS the EXACT connection-"
                      "coefficient-induction proof of the summation identity, or None "
                      "when r is not a canonical ₈ω₇ / the certificate fails to close"),
        ),
        # ────────────────────────────────────────────────────────────
        # The ELLIPTIC-DETERMINANT primitive — Frobenius's elliptic Cauchy
        # determinant evaluation, the FOUNDATION of the multivariable (root-
        # system Cₙ) elliptic reduction row. A CONSTRUCTIVE elliptic identity
        # op (the peer of ThetaSum.three_term): it builds the exact closed
        # form of det[θ(t·x_i·y_j)/θ(x_i·y_j)] as a single EllRatio. 1:1 C
        # peer srmech_elliptic_cauchy_determinant.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_determinant.elliptic_cauchy_determinant",
            owner="srmech", category="elliptic_determinant",
            summary="The ELLIPTIC-DETERMINANT primitive — Frobenius's elliptic Cauchy "
                    "DETERMINANT evaluation, the exact closed form of "
                    "det_{1≤i,j≤n}[θ(t·x_i·y_j; p)/θ(x_i·y_j; p)] as a single theta-"
                    "quotient (Hjalmar Rosengren, 'Elliptic Hypergeometric Functions', "
                    "arXiv:1608.06161v3 [math.CA] (2017), Exercise 1.6.6 — Frobenius's "
                    "determinant evaluation, classically Frobenius 1882, proved via the "
                    "elliptic partial-fraction expansion Eq. (1.22)). The FOUNDATION of "
                    "the multivariable (root-system Cₙ) elliptic reduction row: where the "
                    "single-variable ₈ω₇ reduces to the Weierstrass THREE-TERM relation "
                    "(ThetaSum.three_term), the multivariable Cₙ objects reduce to the "
                    "elliptic PARTIAL-FRACTION expansion + this DETERMINANT (a genuinely "
                    "larger primitive; Warnaar's Cₙ elliptic Jackson summation rests on "
                    "the same determinant family). For distinct x₁…xₙ, y₁…yₙ and a "
                    "parameter t it CONSTRUCTS the exact closed form "
                    "θ(t)^{n-1}·θ(t·∏x·∏y)·∏_{i<j}[x_j·y_j·θ(x_i/x_j)·θ(y_i/y_j)] / "
                    "∏_{i,j}θ(x_i·y_j) as an EllRatio: the exact EllMonomial prefactor "
                    "∏_{i<j} x_j·y_j, the numerator thetas (θ(t)×(n-1), θ(t·∏x·∏y), and "
                    "θ(x_i/x_j), θ(y_i/y_j) for i<j) and the denominator thetas θ(x_i·y_j) "
                    "for all i,j; the EllRatio constructor folds each theta's "
                    "canonicalize prefactor, cancels matching thetas, sorts the "
                    "survivors. A CONSTRUCTIVE elliptic identity op (the peer of "
                    "ThetaSum.three_term). Verified at build: the constructed closed form "
                    "equals the theta-matrix determinant at n=1..4 (exact-ℚ truncated-"
                    "theta eval vs a Leibniz determinant of the same matrix). 1:1 C peer "
                    "srmech_elliptic_cauchy_determinant constructs the SAME EllRatio over "
                    "the shared srmech_ellbase_* monomial algebra + er_build (byte-exact "
                    "to the Python carrier, trusted when loaded); the pure-Python body is "
                    "the complete alternative + the parity oracle. Exact over the "
                    "modified-theta algebra (no float), no abs() (Class-K sign), no numpy "
                    "/ math.",
            parameters=(
                P("t", "EllMonomial", True,
                  "the parameter t of the elliptic Cauchy determinant (an EllMonomial "
                  "over the exact-ℚ argument-lattice)"),
                P("xs", "Sequence[EllMonomial]", True,
                  "the n distinct row variables x₁…xₙ (each an EllMonomial)"),
                P("ys", "Sequence[EllMonomial]", True,
                  "the n distinct column variables y₁…yₙ (each an EllMonomial); "
                  "len(ys) must equal len(xs)"),
            ),
            returns=R("EllRatio",
                      "the exact closed form θ(t)^{n-1}·θ(t·∏x·∏y)·∏_{i<j}[x_j·y_j·"
                      "θ(x_i/x_j)·θ(y_i/y_j)] / ∏_{i,j}θ(x_i·y_j) as a single canonical "
                      "EllRatio (the Frobenius elliptic Cauchy determinant). Raises "
                      "ValueError if xs / ys are empty or unequal length"),
        ),
        # ────────────────────────────────────────────────────────────
        # The ELLIPTIC PARTIAL-FRACTION expansion — the reduction ENGINE of
        # the multivariable (root-system Cₙ) elliptic reduction row (Rosengren
        # Prop. 1.6.1 + Eq. 1.22). Where the single-variable ₈ω₇ reduces to the
        # Weierstrass THREE-TERM relation, the Cₙ objects (the elliptic Cauchy
        # determinant, Warnaar's Lemma 2.2, the Cₙ elliptic Jackson summation)
        # all reduce to THIS. It CONSTRUCTS the partial-fraction SUM of the
        # product ∏_k θ(x/z_k)/θ(x/y_k) as an exact ThetaSum (a SUM of n theta-
        # quotient terms). 1:1 C peer srmech_elliptic_partial_fraction.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_partial_fraction.elliptic_partial_fraction",
            owner="srmech", category="elliptic_partial_fraction",
            summary="The ELLIPTIC PARTIAL-FRACTION expansion — the reduction ENGINE of "
                    "the multivariable (root-system Cₙ) elliptic reduction row (Hjalmar "
                    "Rosengren, 'Elliptic Hypergeometric Functions', arXiv:1608.06161v3 "
                    "[math.CA] (2017), Proposition 1.6.1 + Eq. (1.22)). Where the single-"
                    "variable ₈ω₇ reduces to the Weierstrass THREE-TERM relation "
                    "(ThetaSum.three_term), the multivariable Cₙ objects — the elliptic "
                    "Cauchy / Frobenius determinant (elliptic_cauchy_determinant), "
                    "Warnaar's Lemma 2.2, the Cₙ elliptic Jackson summation — all reduce "
                    "to THIS. For the variable x and distinct z₁…zₙ, y₁…yₙ it CONSTRUCTS "
                    "the partial-fraction expansion of the product ∏_k θ(x/z_k)/θ(x/y_k) "
                    "as an exact ThetaSum (a SUM of n theta-quotient terms): "
                    "1/θ(Y/Z)·Σ_j [∏_k θ(y_j/z_k) / ∏_{k≠j}θ(y_j/y_k)]·[θ(x·Y/(y_j·Z)) / "
                    "θ(x/y_j)], with Y = ∏y and Z = ∏z (the 1/θ(Y/Z) factor is load-"
                    "bearing — the 1/θ(t) of the Prop. 1.6.1 interpolation with t = Y/Z). "
                    "Each summand j is an EllRatio; the returned ThetaSum is their exact "
                    "carrier sum. Verified at build: the constructed sum equals the left-"
                    "hand product at n=1..4 (exact-ℚ truncated-theta eval). 1:1 C peer "
                    "srmech_elliptic_partial_fraction constructs the SAME n EllRatio terms "
                    "over the shared srmech_ellbase_* monomial algebra + er_build (byte-"
                    "exact to the Python carrier; the native ThetaSum is trusted only "
                    "after it == the pure ThetaSum, which is the complete alternative + "
                    "the parity oracle). Exact over the modified-theta algebra (no float), "
                    "no abs() (Class-K sign), no numpy / math.",
            parameters=(
                P("x", "EllMonomial", True,
                  "the variable x of the elliptic partial-fraction expansion (an "
                  "EllMonomial over the exact-ℚ argument-lattice)"),
                P("zs", "Sequence[EllMonomial]", True,
                  "the n distinct numerator parameters z₁…zₙ (each an EllMonomial)"),
                P("ys", "Sequence[EllMonomial]", True,
                  "the n distinct denominator parameters y₁…yₙ (each an EllMonomial); "
                  "len(ys) must equal len(zs)"),
            ),
            returns=R("ThetaSum",
                      "the exact partial-fraction expansion 1/θ(Y/Z)·Σ_j [∏_k θ(y_j/z_k) "
                      "/ ∏_{k≠j}θ(y_j/y_k)]·[θ(x·Y/(y_j·Z)) / θ(x/y_j)] as a ThetaSum (a "
                      "sum of n theta-quotient terms), equal to ∏_k θ(x/z_k)/θ(x/y_k). "
                      "Raises ValueError if zs / ys are empty or unequal length"),
        ),
        # ────────────────────────────────────────────────────────────
        # The MULTIVARIABLE ELLIPTIC JACKSON summation — the CAPSTONE of
        # the multivariable (root-system Cₙ) elliptic reduction row. The
        # eq-5 Cₙ REDUCER: it CONSTRUCTS the closed-form theta-quotient
        # PRODUCT the balanced Cₙ elliptic Jackson summation reduces to
        # (Rosengren Thm 2.1, Eq 5) as a single EllRatio. Peer of rc94's
        # single-EllRatio elliptic_cauchy_determinant. 1:1 C peer
        # srmech_multivariate_elliptic_jackson.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_jackson.multivariate_elliptic_jackson",
            owner="srmech", category="elliptic_jackson",
            summary="The MULTIVARIABLE ELLIPTIC JACKSON summation — the eq-5 Cₙ REDUCER, "
                    "the CAPSTONE of the multivariable (root-system Cₙ) elliptic reduction "
                    "row (Hjalmar Rosengren, 'A multivariable elliptic summation formula', "
                    "arXiv:math/0101073 [math.CA], Theorem 2.1, Eq. 5). Where the single-"
                    "variable ₈ω₇ elliptic Jackson summation reduces to a scalar theta-"
                    "quotient (the Frenkel–Turaev sum), the balanced Cₙ very-well-poised "
                    "elliptic Jackson summation reduces an n-FOLD sum over the partitions "
                    "N ≥ λ₁ ≥ … ≥ λₙ ≥ 0 to a theta-quotient PRODUCT. For the parameters "
                    "a, b, c, d and the base variables x, q it CONSTRUCTS the closed-form "
                    "right-hand side (aq, aq/bc, aq/bd, aq/cd; q, x)_{Nⁿ} / "
                    "(aq/b, aq/c, aq/d, aq/bcd; q, x)_{Nⁿ} — the vector elliptic Pochhammer "
                    "(u; q, x)_{Nⁿ} = ∏_{j=1}^n ∏_{i=0}^{N-1} θ(u·x^{1-j}·qⁱ; p) — as a "
                    "single EllRatio (the remaining parameter e is fixed by the balancing "
                    "e = a²q^{N+1}/(bcd·x^{n-1}), so the sum is balanced by construction). "
                    "The n=1 case is the Frenkel–Turaev ₈ω₇ sum; the induction on N runs "
                    "through Warnaar's Lemma 2.2 + the elliptic partial-fraction expansion "
                    "(elliptic_partial_fraction). Verified at build: the closed form equals "
                    "the actual n-fold Cₙ sum at n=2 (N=1,2) + n=3 (N=1) via an independent "
                    "exact-ℚ theta oracle. 1:1 C peer srmech_multivariate_elliptic_jackson "
                    "constructs the SAME EllRatio over the shared srmech_ellbase_* monomial "
                    "algebra + er_build (byte-exact to the Python carrier; the native "
                    "EllRatio is trusted only after it == the pure EllRatio, which is the "
                    "complete alternative + the parity oracle). Exact over the modified-"
                    "theta algebra (no float), no abs() (Class-K sign), no numpy / math.",
            parameters=(
                P("a", "EllMonomial", True,
                  "the parameter a of the balanced Cₙ elliptic Jackson summation (an "
                  "EllMonomial over the exact-ℚ argument-lattice)"),
                P("b", "EllMonomial", True, "the parameter b (an EllMonomial)"),
                P("c", "EllMonomial", True, "the parameter c (an EllMonomial)"),
                P("d", "EllMonomial", True, "the parameter d (an EllMonomial)"),
                P("x", "EllMonomial", True,
                  "the base variable x of the vector elliptic Pochhammer (an EllMonomial)"),
                P("q", "EllMonomial", True,
                  "the base q of the vector elliptic Pochhammer (an EllMonomial)"),
                P("N", "int", True,
                  "the partition ceiling N (a positive int; N ≥ λ₁ ≥ … ≥ λₙ ≥ 0)"),
                P("n", "int", True,
                  "the rank / number of variables n (a positive int)"),
            ),
            returns=R("EllRatio",
                      "the exact closed-form theta-quotient product "
                      "(aq, aq/bc, aq/bd, aq/cd; q, x)_{Nⁿ} / "
                      "(aq/b, aq/c, aq/d, aq/bcd; q, x)_{Nⁿ} as a single canonical EllRatio "
                      "(the balanced Cₙ elliptic Jackson summation, Rosengren Thm 2.1 Eq 5). "
                      "Raises ValueError if N < 1 or n < 1"),
        ),
        # ────────────────────────────────────────────────────────────
        # The SYMBOLIC Cₙ VWP MULTISUM LHS builder — the LEFT-hand side of
        # the Cₙ elliptic Jackson summation as an exact ThetaSum (the rc96
        # test oracle → rc101 symbolic-verify engine promoted public,
        # rc216). The other side of the Thm 2.1 identity from
        # multivariate_elliptic_jackson (the RHS reducer): LHS − RHS
        # |> is_zero IS the rc101 per-call proof. 1:1 C peer
        # srmech_cn_vwp_multisum_lhs (the rc95 multi-term wire form).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_jackson.cn_vwp_multisum_lhs",
            owner="srmech", category="elliptic_jackson",
            summary="The SYMBOLIC Cₙ VERY-WELL-POISED (VWP) elliptic multisum LHS "
                    "builder — the LEFT-hand side of the Cₙ elliptic Jackson summation "
                    "(Hjalmar Rosengren, 'A proof of a multivariable elliptic summation "
                    "formula conjectured by Warnaar', arXiv:math/0101073v1 [math.CA] "
                    "(9 Jan 2001), Theorem 2.1, Eq. 5) built SYMBOLICALLY as an exact "
                    "ThetaSum over the modified-theta algebra. For the parameters "
                    "a, b, c, d and the base variables x, q it constructs the n-fold Cₙ "
                    "VWP sum over the partitions Λ_{nN} = {N ≥ λ₁ ≥ … ≥ λₙ ≥ 0}: per "
                    "partition, the diagonal θ(a·x^{2(1-i)}q^{2λᵢ})/θ(a·x^{2(1-i)}) "
                    "quotients with the monomial prefactor ∏ᵢ q^{λᵢ}x^{2(i-1)λᵢ}, the "
                    "off-diagonal (i<j) root-system coupling quartet, and the six num / "
                    "six den vector theta-Pochhammer bases (a·x^{1-n}, b, c, d, e, "
                    "q^{-N}; q, x)_λ / (q·x^{n-1}, aq/b, aq/c, aq/d, aq/e, a·q^{N+1}; "
                    "q, x)_λ, with e fixed by the balancing bcde·x^{n-1} = a²q^{N+1}. "
                    "Each summand is an EllRatio; the returned ThetaSum is their exact "
                    "carrier sum (C(N+n, n) terms). This is the rc96 test-oracle / "
                    "rc101 symbolic-verify LHS builder (_cn_lhs_thetasum) promoted to a "
                    "first-class public op: by Thm 2.1 it EQUALS the closed form "
                    "multivariate_elliptic_jackson constructs, so (LHS − RHS).is_zero "
                    "is the rc101 per-call proof with both sides now first-class. 1:1 C "
                    "peer srmech_cn_vwp_multisum_lhs builds the SAME per-partition "
                    "EllRatio terms over the shared srmech_ellbase_* monomial algebra + "
                    "er_build in the same lexicographic partition order (byte-exact to "
                    "the Python carrier; the native ThetaSum is trusted only after it "
                    "== the pure ThetaSum, which is the complete alternative + the "
                    "parity oracle). Exact over the modified-theta algebra (no float), "
                    "no abs() (Class-K sign), no numpy / math.",
            parameters=(
                P("a", "EllMonomial", True,
                  "the parameter a of the balanced Cₙ elliptic Jackson summation (an "
                  "EllMonomial over the exact-ℚ argument-lattice)"),
                P("b", "EllMonomial", True, "the parameter b (an EllMonomial)"),
                P("c", "EllMonomial", True, "the parameter c (an EllMonomial)"),
                P("d", "EllMonomial", True, "the parameter d (an EllMonomial)"),
                P("x", "EllMonomial", True,
                  "the base variable x of the vector elliptic Pochhammer (an "
                  "EllMonomial)"),
                P("q", "EllMonomial", True,
                  "the base q of the vector elliptic Pochhammer (an EllMonomial)"),
                P("N", "int", True,
                  "the partition ceiling N (a positive int; N ≥ λ₁ ≥ … ≥ λₙ ≥ 0)"),
                P("n", "int", True,
                  "the rank / number of variables n (a positive int)"),
            ),
            returns=R("ThetaSum",
                      "the exact n-fold Cₙ VWP elliptic sum over the partitions Λ_{nN} "
                      "as a ThetaSum of C(N+n, n) theta-quotient terms (the Rosengren "
                      "Thm 2.1 Eq 5 LEFT-hand side; equal, by the theorem, to the "
                      "multivariate_elliptic_jackson closed form). Raises ValueError "
                      "if N < 1 or n < 1"),
        ),
        # ────────────────────────────────────────────────────────────
        # The Aₙ (type-A / Milne) elliptic Jackson REDUCER — the sibling
        # root-system member beside the Cₙ capstone (rc227): the closed-form
        # theta-quotient the Aₙ elliptic Jackson summation over the SIMPLEX
        # reduces to (Rosengren math/0305379 Eq. 6), with the per-call
        # verify=True proof. 1:1 C peer
        # srmech_multivariate_elliptic_jackson_an.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_jackson_an.multivariate_elliptic_jackson_an",
            owner="srmech", category="elliptic_jackson_an",
            summary="The Aₙ (type-A) MULTIVARIABLE ELLIPTIC JACKSON summation reducer — "
                    "the elliptic analogue of Milne's Aₙ Jackson summation (Hjalmar "
                    "Rosengren, 'New transformations for elliptic hypergeometric series "
                    "on the root system Aₙ', arXiv:math/0305379v1 [math.CA] (27 May "
                    "2003), Eq. 6; extracted-PDF sha256 299d2738c4539a390a437c795a0b0084"
                    "a5c82d403566c4f549db39482e3076ce). Where the Cₙ row sums over the "
                    "partitions Λ_{nN}, the Aₙ summation sums over the SIMPLEX (the "
                    "compositions y₁+…+yₙ = N, C(N+n−1, n−1) terms) with the type-A "
                    "Weyl-denominator factor Δ(z·q^y)/Δ(z). For the variables z₁..zₙ, "
                    "the parameters a₁..a_{n+1}, the base q and the COMPUTED balancing "
                    "w = z₁⋯zₙ·a₁⋯a_{n+1} it CONSTRUCTS the closed-form right-hand side "
                    "∏_{j=1}^{n+1}(w/aⱼ)_N / [∏_{j=1}^{n}(w·zⱼ)_N·(q)_N] — the elliptic "
                    "shifted factorial (u)_k = ∏_{i=0}^{k-1} θ(u·qⁱ; p) — as a single "
                    "EllRatio. With verify=True it also PROVES the reduction per call "
                    "(builds the symbolic LHS simplex sum via an_vwp_multisum_lhs, "
                    "subtracts, and decides the exact multi-variable elliptic "
                    "ThetaSum.is_zero) and returns {closed_form, verified} — True = "
                    "per-call proof (measured feasible through 6 compositions, incl. "
                    "genuine n = 2, 3, 4 cross-variable instances), False = a "
                    "wrong/perturbed closed form is caught, None = honest "
                    "too-large-to-decide-in-budget (the constructive closed form is "
                    "returned in every case). NOTE the n = 1 case is a trivial "
                    "single-term degeneration (NOT the ₈ω₇); the genuine proof burden "
                    "is n ≥ 2. 1:1 C peer srmech_multivariate_elliptic_jackson_an "
                    "constructs the SAME EllRatio over the shared srmech_ellbase_* "
                    "monomial algebra + er_build (byte-exact; trusted only after == "
                    "the pure EllRatio, the complete alternative + parity oracle). "
                    "Exact over the modified-theta algebra (no float), no abs() "
                    "(Class-K sign), no numpy / math.",
            parameters=(
                P("z", "list[EllMonomial]", True,
                  "the length-n vector of variables (z₁, …, zₙ) — the rank n is "
                  "len(z)"),
                P("a", "list[EllMonomial]", True,
                  "the length-(n+1) vector of parameters (a₁, …, a_{n+1})"),
                P("q", "EllMonomial", True,
                  "the base q of the elliptic shifted factorial (an EllMonomial)"),
                P("N", "int", True,
                  "the simplex ceiling N (a positive int; the sum runs over "
                  "y₁+…+yₙ = N)"),
                P("verify", "bool", False,
                  "False (default): return the bare closed-form EllRatio. True: "
                  "also PROVE the reduction per call and return "
                  "{'closed_form': EllRatio, 'verified': True|False|None}"),
            ),
            returns=R("EllRatio | dict",
                      "the exact closed-form theta-quotient "
                      "∏(w/aⱼ)_N / [∏(w·zⱼ)_N·(q)_N] as a single canonical EllRatio "
                      "(the Aₙ elliptic Jackson summation, Rosengren math/0305379 "
                      "Eq. 6); with verify=True a dict {'closed_form', 'verified'}. "
                      "Raises TypeError/ValueError on a malformed operand (len(a) "
                      "must be len(z)+1; N ≥ 1)"),
        ),
        # ────────────────────────────────────────────────────────────
        # The SYMBOLIC Aₙ MULTISUM LHS builder — the LEFT-hand side of the
        # Aₙ elliptic Jackson summation as an exact ThetaSum over the
        # simplex (rc227; the rc216 Cₙ precedent with both sides
        # first-class). LHS − RHS |> is_zero IS the per-call proof. 1:1 C
        # peer srmech_an_vwp_multisum_lhs (the rc216 multi-term wire form).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.elliptic_jackson_an.an_vwp_multisum_lhs",
            owner="srmech", category="elliptic_jackson_an",
            summary="The SYMBOLIC Aₙ elliptic multisum LHS builder — the LEFT-hand "
                    "side of the Aₙ (type-A / Milne) elliptic Jackson summation "
                    "(Hjalmar Rosengren, 'New transformations for elliptic "
                    "hypergeometric series on the root system Aₙ', "
                    "arXiv:math/0305379v1 [math.CA] (27 May 2003), Eq. 6) built "
                    "SYMBOLICALLY as an exact ThetaSum over the modified-theta "
                    "algebra. For the variables z₁..zₙ, the parameters a₁..a_{n+1}, "
                    "the base q and the COMPUTED balancing w = z₁⋯zₙ·a₁⋯a_{n+1} it "
                    "constructs the sum over the SIMPLEX (the compositions "
                    "y₁, …, yₙ ≥ 0 with y₁+…+yₙ = N, in ascending lexicographic "
                    "order): per composition, the type-A Vandermonde ratio "
                    "Δ(z·q^y)/Δ(z) = ∏_{j<k} q^{yⱼ}·θ(zₖq^{yₖ}/zⱼq^{yⱼ})/θ(zₖ/zⱼ) "
                    "(its monomial part in the Class-K EllRatio prefactor) times "
                    "∏ₖ ∏ⱼ(aⱼ·zₖ)_{yₖ} / [(w·zₖ)_{yₖ}·∏ⱼ(q·zₖ/zⱼ)_{yₖ}]. Each "
                    "summand is an EllRatio; the returned ThetaSum is their exact "
                    "carrier sum (C(N+n−1, n−1) terms). By Eq. 6 it EQUALS the "
                    "closed form multivariate_elliptic_jackson_an constructs, so "
                    "(LHS − RHS).is_zero is the per-call proof with both sides "
                    "first-class (the rc216 Cₙ precedent). 1:1 C peer "
                    "srmech_an_vwp_multisum_lhs builds the SAME per-composition "
                    "EllRatio terms over the shared srmech_ellbase_* monomial "
                    "algebra + er_build in the same ascending lexicographic "
                    "composition order (byte-exact; the native ThetaSum is trusted "
                    "only after it == the pure ThetaSum, the complete alternative + "
                    "parity oracle). Exact over the modified-theta algebra (no "
                    "float), no abs() (Class-K sign), no numpy / math.",
            parameters=(
                P("z", "list[EllMonomial]", True,
                  "the length-n vector of variables (z₁, …, zₙ) — the rank n is "
                  "len(z)"),
                P("a", "list[EllMonomial]", True,
                  "the length-(n+1) vector of parameters (a₁, …, a_{n+1})"),
                P("q", "EllMonomial", True,
                  "the base q of the elliptic shifted factorial (an EllMonomial)"),
                P("N", "int", True,
                  "the simplex ceiling N (a positive int; the sum runs over "
                  "y₁+…+yₙ = N)"),
            ),
            returns=R("ThetaSum",
                      "the exact Aₙ elliptic sum over the simplex y₁+…+yₙ = N as a "
                      "ThetaSum of C(N+n−1, n−1) theta-quotient terms (the Rosengren "
                      "math/0305379 Eq. 6 LEFT-hand side; equal, by the identity, to "
                      "the multivariate_elliptic_jackson_an closed form). Raises "
                      "TypeError/ValueError on a malformed operand (len(a) must be "
                      "len(z)+1; N ≥ 1)"),
        ),
        # ────────────────────────────────────────────────────────────
        # The HIGHER-GENUS (genus-g Riemann theta) theta-multisum reduction
        # row (rc232) — the GENUS-AXIS lift of the elliptic (genus-1) Aₙ / Cₙ
        # Jackson rows. Spiridonov math/0408366 the Theorem (Eq. sum): a
        # multiparameter summation formula for genus-g odd Riemann theta
        # functions, proved by Fay-identity telescoping. Both sides first-class
        # (the rc216/rc227 precedent). 1:1 C peer srmech_riemann_theta_multisum.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.riemann_theta_multisum.multivariate_riemann_theta_sum",
            owner="srmech", category="riemann_theta_multisum",
            summary="The HIGHER-GENUS (genus-g Riemann theta) THETA MULTISUM reducer "
                    "— the genus-axis lift of the elliptic (genus-1) Aₙ/Cₙ Jackson "
                    "rows (V. P. Spiridonov, 'A multiparameter summation formula for "
                    "Riemann theta functions', arXiv:math/0408366v2 [math.CA] (2004); "
                    "Contemp. Math. 417 (2006), 345–353, the Theorem, Eq. sum; "
                    "extracted-source PDF sha256 8478af7407d26d0b0504d381cbe3c32a00f9"
                    "50c3b0c6ab8001a023b7e0c4c319). For n+1 free vectors z_k and 4n+4 "
                    "distinct points a_k,b_k,c_k,d_k on a Riemann surface of arbitrary "
                    "genus g, with the odd theta [u] ([-u]=-[u]) and the abelian "
                    "integral v(a,b), it CONSTRUCTS the closed-form right-hand side "
                    "∏_k [z_k, z_k+v(a_k,c_k)+v(b_k,d_k), v(c_k,d_k), v(a_k,b_k)] − "
                    "∏_k [z_k+v(a_k,c_k), z_k+v(b_k,d_k), v(c_k,b_k), v(a_k,d_k)] "
                    "(= ∏ g_k − ∏ h_k) as a ThetaBracketSum. With verify=True it also "
                    "PROVES the reduction per call: it builds the symbolic LHS multisum "
                    "(riemann_theta_multisum_lhs), rewrites each summand's leading "
                    "factor L_k → g_k − h_k by the genus-g Fay trisecant identity (the "
                    "ONE attested input, Spiridonov Eq. Fay; J. Fay, LNM 353, 1973), "
                    "subtracts, and decides .is_zero — after Fay the residual "
                    "telescopes to EXACTLY zero (a ring identity; free-monomial "
                    "cancellation), returning {closed_form, verified}: True = proven, "
                    "False = a wrong/perturbed closed form is caught. For g=1 the "
                    "identity is Warnaar's elliptic formula. 1:1 C peer "
                    "srmech_riemann_theta_multisum builds the SAME bracket-product "
                    "monomials (byte-exact; trusted only after == the pure "
                    "ThetaBracketSum, the complete alternative + parity oracle). Exact "
                    "over the theta-bracket algebra (no float), no abs() (Class-K "
                    "odd-theta sign), no numpy / math.",
            parameters=(
                P("z", "list[EllMonomial]", True,
                  "the length-(n+1) list of free vectors (z_0,…,z_n) — the summation "
                  "ceiling n is len(z) − 1"),
                P("points", "list[tuple[EllMonomial×4]]", True,
                  "the length-(n+1) list of 4-tuples (a_k, b_k, c_k, d_k) of distinct "
                  "points on the Riemann surface (each an EllMonomial)"),
                P("verify", "bool", False,
                  "False (default): return the bare closed-form ThetaBracketSum. True: "
                  "also PROVE the reduction per call (Fay + telescoping) and return "
                  "{'closed_form': ThetaBracketSum, 'verified': True|False|None}"),
            ),
            returns=R("ThetaBracketSum | dict",
                      "the exact closed-form difference of products ∏ g_k − ∏ h_k as a "
                      "ThetaBracketSum (the Spiridonov math/0408366 Eq. sum right-hand "
                      "side); with verify=True a dict {'closed_form', 'verified'}. "
                      "Raises TypeError/ValueError on a malformed operand (len(points) "
                      "must be len(z); each points[k] a 4-tuple)"),
        ),
        # ────────────────────────────────────────────────────────────
        # The SYMBOLIC higher-genus MULTISUM LHS builder — the LEFT-hand
        # side of the Spiridonov theta multisum as an exact ThetaBracketSum
        # (rc232; both sides first-class). LHS − RHS |> Fay-reduce |> is_zero
        # IS the per-call proof. 1:1 C peer srmech_riemann_theta_multisum.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.riemann_theta_multisum.riemann_theta_multisum_lhs",
            owner="srmech", category="riemann_theta_multisum",
            summary="The SYMBOLIC higher-genus theta-multisum LHS builder — the "
                    "LEFT-hand side of Spiridonov's multiparameter summation formula "
                    "for genus-g Riemann theta functions (arXiv:math/0408366v2 "
                    "[math.CA] (2004); Contemp. Math. 417 (2006), 345–353, the "
                    "Theorem, Eq. sum) built SYMBOLICALLY as an exact ThetaBracketSum "
                    "over the genus-g odd-theta algebra. For n+1 free vectors z_k and "
                    "the distinct points a_k,b_k,c_k,d_k it constructs the n+1-term sum "
                    "Σ_{k=0}^n L_k · ∏_{j<k} g_j · ∏_{j>k} h_j, with the summand "
                    "leading factor L_k = [z_k+v(b_k,c_k), z_k+v(a_k,d_k), v(a_k,c_k), "
                    "v(b_k,d_k)], g_j = [z_j, z_j+v(a_j,c_j)+v(b_j,d_j), v(c_j,d_j), "
                    "v(a_j,b_j)] and h_j = [z_j+v(a_j,c_j), z_j+v(b_j,d_j), v(c_j,b_j), "
                    "v(a_j,d_j)] (the odd theta [u], [-u]=-[u]; v the abelian "
                    "integral). By Eq. sum it EQUALS the closed form "
                    "multivariate_riemann_theta_sum constructs, so its Fay-reduction "
                    "minus that closed form telescopes to zero — the per-call proof, "
                    "with both sides first-class (the rc216/rc227 precedent). 1:1 C "
                    "peer srmech_riemann_theta_multisum builds the SAME bracket-product "
                    "monomials (byte-exact; the native ThetaBracketSum is trusted only "
                    "after it == the pure one, the complete alternative + parity "
                    "oracle). Exact over the theta-bracket algebra (no float), no abs() "
                    "(Class-K odd-theta sign), no numpy / math.",
            parameters=(
                P("z", "list[EllMonomial]", True,
                  "the length-(n+1) list of free vectors (z_0,…,z_n) — the summation "
                  "ceiling n is len(z) − 1"),
                P("points", "list[tuple[EllMonomial×4]]", True,
                  "the length-(n+1) list of 4-tuples (a_k, b_k, c_k, d_k) of distinct "
                  "points on the Riemann surface (each an EllMonomial)"),
            ),
            returns=R("ThetaBracketSum",
                      "the exact higher-genus multisum Σ_{k=0}^n L_k·∏_{j<k}g_j·"
                      "∏_{j>k}h_j as a ThetaBracketSum of n+1 bracket-product terms "
                      "(the Spiridonov math/0408366 Eq. sum LEFT-hand side; equal, by "
                      "the identity, to the multivariate_riemann_theta_sum closed "
                      "form). Raises TypeError/ValueError on a malformed operand"),
        ),
        # ────────────────────────────────────────────────────────────
        # The F929 OPEN/infer ROUTER — the meta-dispatcher that makes the
        # three shipped reduction-theory rows (cyclic / spectral / Σ) ONE
        # callable. Pure orchestration over the already-C-mirrored reducers
        # (coupling / resonant_spectrum / telescope) — NO new math, so it is
        # non_compute (the from_bodies / cooccurrence_edges precedent; no
        # srmech_infer C symbol). The capstone of the dispatch table (F929).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.dispatch.infer", owner="srmech",
            category="dispatch",
            summary="The F929 OPEN/infer ROUTER — the meta-dispatcher over "
                    "srmech's three shipped closed-form reduction-theory rows "
                    "(cyclic / spectral / Σ), the capstone that makes the F929 "
                    "dispatch table (14 A–N classes as a table of closed-form "
                    "reduction theories) ONE callable. Given an arbitrary STORED "
                    "RELATIONSHIP (a descriptor dict), DETECTS which row its "
                    "structure matches (an explicit row=/kind= tag wins; else "
                    "structural sniff: the four (n,k) term-ratios rn_num/rn_den/"
                    "rk_num/rk_den or a term_ratio_num/term_ratio_den → Σ; an "
                    "edges/adjacency/laplacian/matrix payload → spectral; a sigma/"
                    "theta_num/period/generator payload → cyclic), TRIES the "
                    "matching shipped reducer AND VERIFIES it actually reduced — "
                    "reads the reducer's OWN verification: wz_certificate's "
                    "verified flag (Σ), the force-orders L²==L·L contract "
                    "(spectral, resonant_spectrum), the (1,3,7,3) partition + "
                    "n1_is_sigma_only invariant (cyclic, the_one) — and returns the "
                    "verified closed form, else an honest OPEN. Composes the "
                    "EXISTING verified reducers — NO new math; NEVER returns "
                    "reducible:True for a reduction it did not verify (the "
                    "executable no-magic-numbers / no-hallucination discipline). "
                    "On success: {reducible:True, row, reducer, closed_form, "
                    "verified:True}; on no verified match: {reducible:False, "
                    "row:None, reason, candidate_next_theory:<honest hint>}. A "
                    "Class-D late-binding op one rung above dispatch.match; "
                    "non_compute orchestration (no srmech_infer C peer — every "
                    "computation rides an already-C-mirrored reducer). numpy-free; "
                    "no abs() (the Λ² verify reads the magnitude by Class-K "
                    "comparison). Cites F929.",
            parameters=(P("relationship", "dict", True,
                          "the stored-relationship descriptor — an optional row=/"
                          "kind= tag ('sigma'/'spectral'/'cyclic') plus the "
                          "row-specific payload: Σ → rn_num/rn_den/rk_num/rk_den "
                          "(definite sum) or term_ratio_num/term_ratio_den "
                          "(indefinite); spectral → edges (+weights,+n) / adjacency "
                          "/ laplacian / matrix; cyclic → sigma + theta_num "
                          "(+theta_den) or period / generator"),),
            returns=R("dict",
                      "{'reducible': True, 'row': str, 'reducer': str, "
                      "'closed_form': <reducer output>, 'verified': True} on a "
                      "VERIFIED reduction, else {'reducible': False, 'row': None, "
                      "'reason': str, 'candidate_next_theory': str} (the honest "
                      "OPEN residue)"),
        ),
        # ────────────────────────────────────────────────────────────
        # carrier_spectrum — the OPERAND-side dual of the_one. Reads a
        # carrier element's harmonic occupancy under the shift-Laplacian
        # (the Class-L eigenbasis of the carrier's shape) and exposes the
        # block structure that makes the elliptic key-equation solve
        # genuinely block-decomposed. 1:1 C peer srmech_carrier_spectrum.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.carrier_spectrum.carrier_spectrum",
            owner="srmech", category="carrier_spectrum",
            summary="The OPERAND-side dual of the_one (S(σ,θ) is the OPERATOR "
                    "generator — its shape IS the A–N verbs; carrier_spectrum is "
                    "the OPERAND object — its shape is the carrier's Class-L "
                    "shift-Laplacian eigenbasis; operator↔operand = algebra↔module "
                    "= field↔excitation). READS a carrier element (an EllRatio "
                    "theta-quotient) in TWO orthogonal channels: Channel 1 (Class-"
                    "I) cyclic σ-EIGENSPECTRUM — σ=qshift (x↦q·x) is DIAGONAL on "
                    "monomials, σ(x^k)=q^k·x^k, so the x-exponents present are the "
                    "σ-eigen-occupancy with eigenvalue q^k (k=0 the shift-Laplacian "
                    "L=σ−1 kernel / DC mode; the x² very-well-poised DOUBLED-BEAT "
                    "shows as the k=±2 entries); Channel 2 (Class-L) quasi-periodic "
                    "p-CHARACTER BLOCKS — the σ-invariant net-period quasi-"
                    "periodicity class (Rosengren Eq. 1.6, q-stripped) partitioning "
                    "the theta-factors; σ PRESERVES the block (the channels are "
                    "orthogonal). The block partition is the lever that makes the "
                    "elliptic KEY EQUATION A·σ(Y)−B(x/q)·Y=RHS (Gasper–Schlosser, "
                    "arXiv:math/0505215) solve genuinely BLOCK-DECOMPOSED — "
                    "CarrierSpectrum.solve_key_equation groups the certificate "
                    "basis by p-character block and solves each block as an "
                    "INDEPENDENT small QMat system (block(A)==block(B(x/q)) → block-"
                    "DIAGONAL), reproducing the dense QMat solve EXACTLY but as "
                    "Σ_b(n_b×n_b) instead of one dense n×n — NOT brute force. Refs: "
                    "Rosengren arXiv:1608.06161v3 §1.3 Lemma 1.3.2 (period-annulus "
                    "degree bound) + §1.4 Eq. 1.12 (Weierstrass three-term). Returns "
                    "{'cyclic': {x-exp k: 'q**k'}, 'blocks': {block: [theta-arg "
                    "maps]}, 'n_blocks': …, 'spectrum': CarrierSpectrum}. 1:1 C peer "
                    "srmech_carrier_spectrum mirrors the channel read + the block-"
                    "grouped solve over the integer theta-exponent lattice (shared "
                    "srmech_ellbase_* + srmech_qmat_rref); the Python trusts a "
                    "native result ONLY after the pure rebuild reproduces the same "
                    "spectrum (a miss → pure path). Exact bigint; no float, no abs() "
                    "(Class-K sign), no numpy / math.",
            parameters=(P("r", "EllRatio", True,
                          "the carrier element to read — an EllRatio (a theta-"
                          "quotient over an exact-ℚ monomial prefactor; an "
                          "EllMonomial / Theta is lifted)"),),
            returns=R("dict",
                      "{'cyclic': {x-exponent k: 'q**k'} (the σ-eigenspectrum, "
                      "Channel 1), 'blocks': {block label: [[theta-arg exponent "
                      "map], …]} (the σ-invariant p-character partition, Channel 2), "
                      "'n_blocks': int, 'spectrum': CarrierSpectrum (the live carrier "
                      "for inspect / solve_key_equation)}"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc70: the FIRST WEIGHT-GRADED carrier (srmech.amsc.unary_theta). The
        # operand ladder (Q / Poly / QPoly / EllRatio / ThetaSum) was entirely
        # WEIGHT-0; unary_theta augments it with a WEIGHT axis (= 1/2 + poly-
        # degree j), making the harmonic-Maass / mock-theta SHADOW representable
        # in-carrier (research item #9). 1:1 C peer srmech_unary_theta.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.unary_theta.unary_theta",
            owner="srmech", category="unary_theta",
            summary="Construct a UNARY THETA SERIES g(τ) = Σ_{n∈support} χ(n)·"
                    "n^j·q^{(a·n²+b·n)/D} — the FIRST WEIGHT-GRADED operand "
                    "carrier (the ladder Q/Poly/QPoly/EllRatio/ThetaSum was all "
                    "WEIGHT-0). Its WEIGHT = 1/2 + j (exact Q): j=0 ⇒ weight 1/2 "
                    "(a Jacobi theta), j=1 ⇒ weight 3/2 (a mock-theta SHADOW), "
                    "j=2 ⇒ weight 5/2 — THE WEIGHT AXIS. This makes the "
                    "harmonic-Maass / mock-theta program (research item #9) "
                    "representable in-carrier: the order-3 mock theta f(q) has "
                    "SHADOW g₃ = Σ_{n≥1} (−12/n)·n·q^{n²/24} (Zagier, Astérisque "
                    "326 (2009), Exp. 986, p. 150), a weight-3/2 unary theta a "
                    "weight-0 carrier cannot hold. .q_series(N) returns the EXACT "
                    "INTEGER coefficients after factoring the leading q-power: θ₃ "
                    "(triv χ, j=0, a=1,b=0,D=1, support='all') → [1,2,0,0,2,…] "
                    "(Σ_{n∈ℤ}q^{n²}); g₃ ('minus12', j=1, a=1,b=0,D=24, "
                    "support='positive') → [1,−5,−7,0,0,11,0,13,…] (the Zagier "
                    "coeffs at q^{1/24}). χ is a Character (period M, values in "
                    "{−1,0,1}); 'trivial' / 'minus12' are the named anchors. 1:1 "
                    "C peer srmech_unary_theta computes the integer q-series over "
                    "caller-arena srmech_bigint (n^j full bignum, no int64 "
                    "ceiling; byte-identical to Python). Exact integers + exact-Q "
                    "weight; no float, no abs() (the χ sign is the Class-K pin-"
                    "slot), no numpy / math.",
            parameters=(P("char", "str", True,
                          "the character χ: 'trivial' (χ≡1) or 'minus12' (the "
                          "(−12/·) Kronecker character of g₃); an in-process "
                          "caller may also pass a Character or a residue table"),
                        P("j", "int", True,
                          "the polynomial degree of the n^j factor (j ≥ 0); the "
                          "weight is 1/2 + j"),
                        P("a", "int", True,
                          "the quadratic coefficient of the q-exponent (a > 0)"),
                        P("b", "int", True,
                          "the linear coefficient of the q-exponent"),
                        P("D", "int", True,
                          "the q-exponent denominator (D > 0); the exponent is "
                          "(a·n²+b·n)/D"),
                        P("support", "str", False,
                          "the summation support: 'all' (n∈ℤ), 'positive' (n≥1, "
                          "the default), or 'nonneg' (n≥0)")),
            returns=R("UnaryTheta",
                      "the weight-graded carrier (.weight = Q(1,2)+j; "
                      ".q_series(N) → exact integer coefficients; "
                      ".leading_power() → the factored-out q-power)"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc113 (#1239 / F1027 / UPSTREAM §85): theta_coefficients — the FIRST
        # registered CONSUMER of the UnaryTheta carrier (a conversationally-
        # built shadow was a dead end after display). COMPUTE, dispatched
        # through the EXISTING rc70 1:1 C peer srmech_unary_theta (q_series
        # routes to it) — no new C symbol; the mirror already ships.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.unary_theta.theta_coefficients",
            owner="srmech", category="unary_theta",
            summary="READ a UnaryTheta's exact integer q-expansion — the FIRST "
                    "registered CONSUMER of the UnaryTheta carrier (#1239 / "
                    "F1027 / UPSTREAM §85: before rc113 no tool ACCEPTED a "
                    "UnaryTheta, so a conversationally-built shadow was a dead "
                    "end after display). Returns [c_0, …, c_n_max] — the exact "
                    "INTEGER coefficients after factoring out the leading "
                    "q-power (exactly UnaryTheta.q_series): θ₃ → [1, 2, 0, 0, "
                    "2, …]; the g₃ order-3 mock-theta shadow → the Zagier "
                    "coefficients [1, −5, −7, 0, 0, 11, 0, 13, …] (Astérisque "
                    "326 (2009), Exp. 986, p. 150 — the rc70 anchors, the SSOT "
                    "citation). The q-SIDE coefficient read dual to the "
                    "Laplacian-side theta trace (laplacian.heat_trace reads "
                    "Tr e^{−tL}, the spectral theta; this reads the carrier's "
                    "own q-series). COMPUTE, C-DISPATCHED through the EXISTING "
                    "rc70 1:1 peer srmech_unary_theta (byte-identical exact-"
                    "integer mirror over caller-arena srmech_bigint; a bare C "
                    "host calls srmech_unary_theta directly) — no new C symbol "
                    "needed, the mirror already ships. A JSON caller may pass "
                    "theta='g3' (the named shadow — the MCP coercer builds "
                    "it); an in-process / result-register caller chains the "
                    "UnaryTheta returned by unary_theta. Exact bignum ints; "
                    "no float, no abs() (the χ sign is the Class-K pin-slot), "
                    "no numpy / math.",
            parameters=(P("theta", "UnaryTheta", True,
                          "the unary theta to read — a UnaryTheta chained "
                          "from unary_theta's return, or the named shadow "
                          "string 'g3'"),
                        P("n_max", "int", True,
                          "the highest q-power to read (inclusive, ≥ 0) — "
                          "returns n_max+1 coefficients")),
            returns=R("list[int]",
                      "[c_0, …, c_n_max] exact integer coefficients after the "
                      "leading-power factor-out"),
            smoke_test_hint={"theta": "'g3'", "n_max": "7"},
        ),
        # ────────────────────────────────────────────────────────────
        # rc71: the HARMONIC (weak) MAASS form PAIR carrier
        # (srmech.amsc.harmonic_maass). A harmonic Maass form f of weight k is
        # determined by the pair (f⁺ holomorphic mock part, g = ξ_k(f) shadow);
        # the non-holomorphic completion f⁻ is the Eichler integral of the shadow,
        # recoverable not stored (Bruinier–Funke Prop. 3.2). Closes research item
        # #9: the harmonic-Maass non-holomorphic completion (the operand-side
        # "irrepresentable" target) is now a finite exact PAIR. 1:1 C peer
        # srmech_harmonic_maass (the holomorphic Eulerian f(q) q-series).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.harmonic_maass.harmonic_maass",
            owner="srmech", category="harmonic_maass",
            summary="Construct a HARMONIC (weak) MAASS form as the FINITE EXACT "
                    "PAIR (hol holomorphic mock part, shadow g = ξ_k(f)) it is "
                    "determined by — closing research item #9 (the harmonic-Maass "
                    "non-holomorphic completion, the operand-side 'irrepresentable' "
                    "target, becomes a finite exact PAIR). A harmonic Maass form "
                    "f of weight k decomposes uniquely f = f⁺ + f⁻ (Bruinier–Funke, "
                    "arXiv:math/0212286v4, p.9 eqs 3.2a/3.2b); the completion f⁻ is "
                    "the EICHLER (period) integral of the shadow g = ξ_k(f) "
                    "(Prop. 3.2 p.10: ξ_k : H_{k,L}→M^!_{2−k}, kernel = holomorphic "
                    "forms), recoverable NOT stored — storing the shadow IS storing "
                    "the completion (the honest treatment of a transcendental: no "
                    "float, never numerically evaluated). The #9 KEYSTONE: "
                    "Ramanujan's order-3 mock theta f(q) = Σ q^{n²}/∏(1+qʲ)² "
                    "(Zagier, Astérisque 326 (2009) p.145) has shadow g₃ = "
                    "Σ_{n≥1}(−12/n)·n·q^{n²/24} (weight 3/2, a rc70 UnaryTheta, "
                    "p.150), so it is the pair (eulerian_f, g₃), weight 2−3/2 = 1/2 "
                    "— ONE finite exact carrier. hol is a MockQSeries (a thin "
                    "q-series carrier: leading q-power + a finite GENERATING RULE — "
                    "'eulerian_f' for the keystone, or a closed-form 'qpoly') or the "
                    "string 'eulerian_f'; shadow is the weight-(2−k) UnaryTheta. "
                    ".weight = 2 − shadow.weight, .xi() returns the shadow (the hol "
                    "part is in ξ's kernel), .hol_q_series(N) / .shadow_q_series(N) "
                    "the exact coefficients. A mock part with NO finite rule is an "
                    "honest OPEN (the carrier's named boundary). 1:1 C peer "
                    "srmech_harmonic_maass computes the Eulerian f(q) integer "
                    "q-series over caller-arena srmech_bigint (byte-identical to "
                    "Python). Exact integers / exact-ℚ + exact-Q weight; no float, "
                    "no abs() (the Class-K pin-slot carries any sign), no numpy / "
                    "math.",
            parameters=(P("hol", "MockQSeries", True,
                          "the holomorphic mock part f⁺: a MockQSeries (leading "
                          "q-power + a finite generating rule) or the string "
                          "'eulerian_f' (Ramanujan's order-3 f(q), the #9 keystone)"),
                        P("shadow", "UnaryTheta", True,
                          "the shadow g = ξ_k(f): a weight-(2−k) UnaryTheta (e.g. "
                          "unary_theta('minus12',1,1,0,24,support='positive') for "
                          "g₃ at weight 3/2)")),
            returns=R("HarmonicMaass",
                      "the pair carrier (.weight = 2 − shadow.weight; .hol / "
                      ".shadow; .xi() → the shadow; .hol_q_series(N) / "
                      ".shadow_q_series(N) → exact coefficients)"),
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
            summary="Absolute value |x| (magnitude) — Class K pin-slot at "
                    "zero, magnitude only (orientation discarded). The "
                    "cascade-honest replacement for Python abs() when only "
                    "|x| is needed." + PUBLISH_OPT_IN_NOTE,
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
        # Class I modular-arithmetic cascade ops (§110 / #1460) — the DSL-
        # declarable face of the cyclic modular family, so a modular cascade
        # (an LCG step = cyclic_mod_mul ∘ cyclic_mod_add) can be authored in a
        # chain spec. Each delegates to the c_dispatched cyclic.* primitive
        # (composition_of_c). DSL chain contract: the piped value is `a`; the
        # operands (`b`/`k`/`n`) are bound stage kwargs.
        ToolEntry(
            name="srmech.amsc.cascade.cyclic_mod_mul", owner="srmech",
            category="cascade",
            summary="Modular multiply as a cascade stage — (a * b) mod n "
                    "(delegates to srmech.amsc.cyclic.mod_mul). The DSL-"
                    "declarable multiply stage of an LCG cascade: pipe the "
                    "state as `a`, bind `b`=multiplier and `n`=modulus. Capped "
                    "at uint64 (use cyclic_mod_mul_wide for a wider modulus)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "int", True, "the piped state"),
                        P("b", "int", True, "multiplier"),
                        P("n", "int", True, "modulus > 0")),
            returns=R("int", "in [0, n)"),
            smoke_test_hint={"a": "7", "b": "6", "n": "10"},
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cyclic_mod_add", owner="srmech",
            category="cascade",
            summary="Modular addition as a cascade stage — (a + b) mod n "
                    "(delegates to srmech.amsc.cyclic.mod_add). The DSL-"
                    "declarable increment stage of an LCG cascade: pipe the "
                    "state as `a`, bind `b`=increment and `n`=modulus. Chained "
                    "after cyclic_mod_mul it IS one linear-congruential step."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "int", True, "the piped state"),
                        P("b", "int", True, "addend"),
                        P("n", "int", True, "modulus > 0")),
            returns=R("int", "in [0, n)"),
            smoke_test_hint={"a": "7", "b": "6", "n": "10"},
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cyclic_mod_pow", owner="srmech",
            category="cascade",
            summary="Modular exponentiation as a cascade stage — (a ** k) mod "
                    "n via square-and-multiply (delegates to "
                    "srmech.amsc.cyclic.mod_pow). The DSL-declarable power "
                    "stage of a multiplicative-hash / modular-power cascade: "
                    "pipe the base as `a`, bind `k`=exponent and `n`=modulus."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "int", True, "the piped base"),
                        P("k", "int", True, "exponent"),
                        P("n", "int", True, "modulus > 0")),
            returns=R("int", "in [0, n)"),
            smoke_test_hint={"a": "3", "k": "4", "n": "10"},
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cyclic_mod_inv", owner="srmech",
            category="cascade",
            summary="Modular inverse as a cascade stage — a**-1 mod n via "
                    "extended Euclidean (delegates to "
                    "srmech.amsc.cyclic.mod_inv). The DSL-declarable un-do "
                    "stage of a modular cascade: pipe the value as `a`, bind "
                    "`n`=modulus. Requires gcd(a, n) == 1 and n <= INT64_MAX."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "int", True, "the piped value to invert"),
                        P("n", "int", True, "modulus >= 2")),
            returns=R("int", "in [1, n)"),
            smoke_test_hint={"a": "3", "n": "7"},
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cyclic_mod_mul_wide", owner="srmech",
            category="cascade",
            summary="Wide modular multiply as a cascade stage — (a * b) mod n "
                    "with NO uint64 cap (delegates to "
                    "srmech.amsc.cyclic.mod_mul_wide). The DSL-declarable "
                    "multiply-and-reduce half of a 128-bit LCG (the raw PCG64 "
                    "step at n = 2**128): pipe the state as `a`, bind "
                    "`b`=multiplier and `n`=modulus, any width. The product "
                    "rides srmech's C bignum (srmech_bigint_mul)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "int", True, "the piped state, any width"),
                        P("b", "int", True, "multiplier, any width"),
                        P("n", "int", True, "modulus > 0, any width")),
            returns=R("int", "in [0, n)"),
            smoke_test_hint={"a": "2**64", "b": "3", "n": "2**128"},
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
        # Quaternion / octonion DFTs (#863, F380) — the native transform for a
        # Klein-4 object. quaternion_dft GRADUATED first-class at 0.9.0rc110
        # (#1234 Item 1b): rc109 qm.quaternion foundation + the whole-transform
        # C peer srmech_quaternion_dft. octonion_dft remains the composite tier
        # over qm.octonion. Both numpy-free (rc125 #564).
        ToolEntry(
            name="srmech.amsc.cascade.quaternion_dft", owner="srmech",
            category="cascade",
            summary="QUATERNION discrete Fourier transform (QDFT) — the native "
                    "transform for a Klein-4 object, GRADUATED first-class "
                    "(0.9.0rc110; #1234 Item 1b / #863). A Klein-4 object has TWO "
                    "Z₂ chirality axes (Klein-4 = Q₈/{±1} ≅ Z₂×Z₂, F380); a COMPLEX "
                    "FFT first projects it to ℂ and collapses one axis (the flat "
                    "shadow). The QDFT's ℍ coefficient algebra MATCHES the object's "
                    "value algebra, so BOTH axes survive. THE CONVENTION (forward "
                    "σ=−1): left form X[k]=Σ_n exp(σ·μ·2πkn/N)·x[n] (twiddle LEFT); "
                    "right form X[k]=Σ_n x[n]·exp(σ·μ·2πkn/N) (twiddle RIGHT) — "
                    "genuinely different transforms (ℍ non-commutative; equal iff "
                    "the signal lies in ℝ[μ]); inverse = σ=+1 + 1/N, same side; "
                    "each form round-trips exactly, recovering ALL FOUR components. "
                    "Parseval: Σ‖X‖²=N·Σ‖x‖². API SPLIT (F1000→F1001): this FULL "
                    "transform is the SPREAD-SPECTRUM ENCODING/analysis surface; "
                    "the READ path is the separate lightweight phase_coherent_peak "
                    "op (later rc). Composes the rc109 qm.quaternion foundation "
                    "(quaternion_twiddle + 4×4 L_q/R_q); dispatches the whole "
                    "O(N²) exact-reference transform to the same-rc C peer "
                    "srmech_quaternion_dft (byte-exact composed fallback; FFT "
                    "factorisation is future work). Class M ∘ C ∘ N ∘ I; no new "
                    "primitive class, no abs(); numpy-free. Sangwine & Ell (2012), "
                    "arXiv:1001.4379 (PDF-verified)." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True,
                  "N quaternion samples, each [q0,q1,q2,q3] (or 8-vec octonion "
                  "with e4..e7=0), or a real (N,4) Mat"),
                P("form", "str", False, "'left' (W·x) or 'right' (x·W); default 'left'"),
                P("mu_axis", "str", False,
                  "transform axis μ: 'i'|'j'|'k'|'ijk'|'diagonal' or a unit "
                  "pure-imaginary 4-vector; default 'i'"),
                P("inverse", "bool", False, "inverse QDFT (conjugate twiddle + 1/N); default False"),
            ),
            returns=R("list[list[float]]", "N quaternions (4-component lists)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.octonion_dft", owner="srmech",
            category="cascade",
            summary="OCTONION discrete Fourier transform (ODFT) — the (8:7) rung "
                    "above the QDFT, GRADUATED first-class (0.9.0rc111; #1234 "
                    "Item 1c / #863) over the qm.octonion foundation "
                    "(octonion_twiddle + 8×8 L_a/R_a atoms) with the "
                    "whole-transform C peer srmech_octonion_dft (ALL THREE forms; "
                    "byte-exact composed fallback). 𝕆 is NON-ASSOCIATIVE (F378) → "
                    "the ODFT is NOT unique until its bracketing is DECLARED — an "
                    "explicit ATTESTED field (octonion_dft.toml "
                    "[cascade.bracketing]): per-summand-single-product; inverse = "
                    "conjugate twiddle on the SAME declared side; two-sided "
                    "association `bracketing` ∈ {'left_associated' (W_l·x)·W_r, "
                    "'right_associated' W_l·(x·W_r)} — these DIFFER for distinct "
                    "axes (load-bearing, tested). ALTERNATIVITY finding (Artin, "
                    "verified): the one-sided round-trip lives in the 2-generator "
                    "⟨μ, x⟩ and is EXACT; non-associativity bites only at ≥3 "
                    "generators. One-sided forms round-trip; two-sided is "
                    "forward-only (inverse raises). Class M∘C∘N∘I; numpy-free; "
                    "no abs(). Błaszczyk (2019), arXiv:1905.12631 (PDF re-verified "
                    "rc111 — its own Eq (2.8) declares 'multiplication … done from "
                    "left to right'); origin Hahn & Snopek (2011), Bull. Polish "
                    "Acad. Sci. 59(2):167–181." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True,
                  "N octonion samples, each 8-component [e0..e7] (4-component "
                  "quaternions zero-extended), or a real (N, 8) Mat"),
                P("form", "str", False, "'left'|'right'|'two_sided'; default 'left'"),
                P("mu_axis", "str", False,
                  "left/single axis μ: 'i'|'j'|'k' (= 'e1'|'e2'|'e3') | 'e4'..'e7' "
                  "| 'ijk' | 'diagonal', or a unit pure-imaginary 4-/8-vector; "
                  "default 'i'"),
                P("bracketing", "str", False,
                  "the DECLARED two-sided association: 'left_associated'|"
                  "'right_associated' (F378; the attested field); default "
                  "'left_associated'"),
                P("two_sided_right_axis", "str", False, "right twiddle axis μ_r; default 'j'"),
                P("inverse", "bool", False, "inverse ODFT (one-sided only); default False"),
            ),
            returns=R("list[list[float]]", "N octonions (8-component lists)"),
        ),
        # The lightweight matched-filter PEAK READ (v0.9.0rc112; #1234 Item 1d,
        # the F1000→F1001→F1002 refinement) — the READ counterpart to the full
        # quaternion_dft / octonion_dft ENCODING transforms above, deliberately
        # its OWN op (NOT a kwarg on the transforms). c_dispatched C peer.
        ToolEntry(
            name="srmech.amsc.cascade.phase_coherent_peak", owner="srmech",
            category="cascade",
            summary="The LIGHTWEIGHT matched-filter PEAK READ over a rung/mode "
                    "ladder — the RBS-LM READ reduction, kept API-DISTINCT from "
                    "the full quaternion_dft / octonion_dft ENCODING transforms "
                    "(0.9.0rc112; #1234 Item 1d, the F1000→F1001→F1002 "
                    "refinement). THE READ-vs-ENCODE SPLIT: the full transforms "
                    "(rc110/rc111) are the spread-spectrum ENCODING surface (the "
                    "whole length-N spectrum); for the RBS-LM single-rung fold "
                    "F1001 measured the full complex QDFT WORSE than the peak — "
                    "the target's cross-rung response is a SPIKE, so the PEAK "
                    "(max phase-coherent energy over the rung ladder) IS the "
                    "matched filter (rejects off-rung noise), while the full "
                    "transform coherently combines ALL rungs incl. the off-rung "
                    "noise (a spike's spectrum is flat → coherent combination "
                    "gains nothing, forfeits the max's noise-rejection). F1002 "
                    "settled it read-independently (elliptic −z⁻¹ is circulant/"
                    "GENERATIVE but recall-equivalent to independent keys — the "
                    "transform's value is encoding, not read-amplification). So "
                    "the read wants ONLY this peak reduction; there is NO twiddle "
                    "here — its absence IS what distinguishes the read from the "
                    "transform. COMPUTATION: per-rung phase-coherent energy E_r = "
                    "Σ_i ladder[r][i]² (keys=None, identity filter = the F1001 "
                    "read) or (Σ_i keys[r][i]·ladder[r][i])² (explicit per-rung "
                    "template); peak = argmax_r E_r (ties→lowest index). Class K "
                    "(squared-magnitude energy + argmax magnitude comparison; no "
                    "abs(), no libm); numpy-free; same-rc byte-exact C peer "
                    "srmech_phase_coherent_peak. The findings F999–F1002 are the "
                    "in-repo SSOT (no external citation)." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("ladder", "sequence", True,
                  "n_rungs per-rung samples along the rung/mode axis (each a "
                  "real scalar, complex scalar, or a quaternion/octonion/Klein-4 "
                  "component vector — all the same dimension d), or a real "
                  "(n_rungs, d) Mat"),
                P("keys", "sequence", False,
                  "optional matched-filter template — the expected per-rung "
                  "phase pattern, one per rung (same shape as ladder); default "
                  "None = the identity filter (the ladder IS the per-rung "
                  "matched-filter output, the F1001 read)"),
            ),
            returns=R("dict",
                      "{rung_index: peak rung, score: its phase-coherent energy "
                      "(squared magnitude), scores: every rung's energy}"),
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
                    "of the continuous (σ,θ,μ) family = coupling's 𝕊(σ,θ) (F420) plus "
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
        # Literal exp(μθ) unit hypercomplex twiddle (v0.9.0rc10; F882, srmech #205).
        # Registered FLAT as srmech.amsc.cascade.hypercomplex_exp; native C peer
        # srmech_hypercomplex_exp_q61 is byte-exact Q61 (test_hypercomplex_exp_rc10).
        ToolEntry(
            name="srmech.amsc.cascade.hypercomplex_exp", owner="srmech",
            category="cascade",
            summary="Literal exp(μθ) = cos θ + μ·sin θ unit hypercomplex twiddle — the "
                    "GENUINE hypercomplex exponential as an exact Q61 8-tuple (F882, "
                    "srmech #205). μ is the equal-weight UNIT pure-imaginary over the "
                    "first k_axes octonion axes: k_axes ∈ {1,3,7} = ℂ/ℍ/𝕆. Returns 8 "
                    "exact Q [cos θ, sin θ/√k ×k, 0 ×(7−k)] with |q|=1. Feed it into "
                    "cd_mult to rotate a hypercomplex value IN the algebra, then project "
                    "once — the literal QDFT/ODFT twiddle that beats composing scalar "
                    "phase_binds on the projected carrier (F882: ℂ 0.78 = the spirit's "
                    "ℍ rung; 𝕆/ODFT 0.81, a new routing high). Class N (Q61 cos/sin) ∘ "
                    "Class K (1/√k unit norm via integer-sqrt) ∘ Class C (sign); no "
                    "abs(), no libm, no bignum — fixed-width Q61. Native peer "
                    "srmech_hypercomplex_exp_q61 is byte-exact with the pure cascade.",
            parameters=(
                P("theta", "float", True, "the rotation angle θ (radians)"),
                P("k_axes", "int", True,
                  "imaginary-axis count: 1 (ℂ) | 3 (ℍ / QDFT) | 7 (𝕆 / ODFT)"),
            ),
            returns=R("tuple[Q, ...]",
                      "8-tuple of exact Q (Q61, denominator 2^61): "
                      "[cos θ, sin θ/√k ×k_axes, 0 ×(7−k_axes)]"),
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
                    "doubling, numpy-free, each component a Q. This is the "
                    "OPEN-EXTERIOR demonstrator, NOT a substrate extension: coupling / "
                    "hypercomplex_couple live in the reversible interior (≤𝕆); this is "
                    "the non-division object past the Hurwitz wall where the product "
                    "loses its inverse. Class M (bilinear bind) ∘ C (conjugation-ordered "
                    "cross terms) ∘ K (sign-flip; no abs())."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("a", "sequence", True, "first element — a power-of-two-length sequence of ints/Fractions"),
                P("b", "sequence", True, "second element — same dimension as a"),
            ),
            returns=R("tuple", "the product, a tuple of exact Q"),
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
            returns=R("tuple", "the conjugate, a tuple of exact Q"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_norm_sq", owner="srmech",
            category="cascade",
            summary="The norm form N(x) = Re(x·x̄) of a Cayley–Dickson algebra "
                    "(exact rational; x·x̄ = N(x)·1 at every rung). GAMMAS DECLARES "
                    "WHICH ALGEBRA, and the declaration is load-bearing (rc352, "
                    "`#T1001`): None — the default — is the DEFINITE ladder, on "
                    "which N collapses to the coordinate sum Σ xᵢ² and IS "
                    "positive-definite; a supplied gammas names a generalised twist "
                    "(see algebra_table), and on a SPLIT twist the coordinate sum is "
                    "simply the wrong function. MEASURED: before the gate this op "
                    "was Σ xᵢ² unconditionally and reported N([1,−1]) = 2 for a "
                    "GENUINE null vector of split-ℂ ((1+j)(1−j) = 0), unable to see "
                    "isotropy at all. cd_norm_sq([1,-1]) is still 2 (the definite ℂ "
                    "answer, right for the algebra the default declares); "
                    "cd_norm_sq([1,-1], gammas=[1]) is 0. ON A SPLIT TWIST THE "
                    "RESULT CAN BE NEGATIVE OR ZERO FOR A NONZERO ELEMENT — the form "
                    "is indefinite there, and reading '_sq' as non-negative is the "
                    "trap the parameter removes. The twisted read is O(dim), not "
                    "O(dim³): the generalised product is monomial with index i⊕j, so "
                    "N(x) = Σᵢ xᵢ·x̄ᵢ·sign_γ(i,i). The composition identity "
                    "N(x·y) = N(x)·N(y) holds for dims ≤ 8 and FAILS at 16 (a "
                    "zero-divisor pair has N(x·y)=0 while N(x)·N(y)≠0; §VII.6.23 C3)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("a", "sequence", True, "a power-of-two-length element"),
                P("gammas", "Sequence[int] | None", False,
                  "the per-doubling ±1 twist in LADDER order (gammas[0] = ℝ→ℂ), "
                  "log2(len(a)) entries. None (default) is the definite ladder — "
                  "the unchanged, C-dispatched coordinate fast path"),
            ),
            returns=R("Q", "the exact N(x); negative or zero is possible on a "
                           "declared SPLIT twist"),
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
        # rc349 (`#T987`, consolidating `#T968`): the ℝ→ℂ rung of the Hurwitz
        # loss ladder — the one rung with no instrument. It reads the rank-3
        # structure-constant TABLE, never a declared dimension, so split algebras
        # and arbitrary tables answer honestly (split-𝕆 → (5,3,0), not (1,7,0)).
        ToolEntry(
            name="srmech.amsc.cascade.inertia_signature", owner="srmech",
            category="cascade",
            summary="Sylvester inertia of the TRACE form q(x) = Re(x·x), read off a "
                    "rank-3 structure-constant table, with the negative pivot "
                    "direction attached. IT READS THE TABLE, NEVER A DECLARED "
                    "DIMENSION and never the coordinate form a²−|v|² (that "
                    "substitution is input-blind: it matches the real read 4000/4000 "
                    "on 𝕆 but 854/4000 on split-𝕆, and stays wrong at infinite "
                    "precision). Measured trace/norm: ℝ (1,0,0)/(1,0,0) · ℂ "
                    "(1,1,0)/(2,0,0) · ℍ (1,3,0)/(4,0,0) · 𝕆 (1,7,0)/(8,0,0) · "
                    "split-𝕆 (5,3,0)/(4,4,0) — the literature's (4,4) is the NORM "
                    "form, so both ship named. SCOPE: this reads the inertia of one "
                    "quadratic form and NOTHING ELSE — n₋ == 0 does NOT mean "
                    "orderable (split-ℂ answers (2,0,0) yet (1+j)(1−j)=0), and a "
                    "diagonal-pinned scrambled table answers exactly as 𝕆 does, so "
                    "it certifies nothing about associativity, alternativity, "
                    "composition or division. Exact integers end to end: no float, "
                    "no epsilon, no abs() (sign is the Class K pin-slot ∘ Class C "
                    "re-orientation). Same-rc C peer "
                    "srmech_algebra_inertia_signature (bit-identical signature AND "
                    "witness). Class K ∘ C ∘ L ∘ I. SSoT: Sylvester (1852); "
                    "Springer & Veldkamp (2000) §1.7."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("table", "list[list[list[int]]]", True,
                  "the dim × dim × dim structure-constant tensor; table[i][j][k] is "
                  "the coefficient of e_k in e_i·e_j (basis 0 is the real "
                  "direction). The shape qm.octonion_mult_table / "
                  "qm.quaternion_mult_table already return"),
            ),
            returns=R("dict",
                      "{'dim', 'form' ('trace'), 'signature' (n₊,n₋,n₀), 'n_plus', "
                      "'n_minus', 'n_zero', 'norm_signature' (the N read), "
                      "'has_negative_direction' (bool — n₋ > 0; False proves "
                      "NOTHING about orderability), 'witness' (list[int] | None), "
                      "'witness_real_square' (int | None — Re(w·w) < 0), "
                      "'witness_square' (list[int] | None — the full w·w), "
                      "'witness_certifies_nonorderable' (bool — w·w is a negative "
                      "real multiple of the identity)}"),
        ),
        # rc352 (`#T997`): the GAMMA-parameterised Cayley–Dickson doubling —
        # the CONTROL constructor. The `−` hard-wired into cd_mult's recursion
        # IS the γ, pinned to −1; this exposes it per rung so the negative
        # controls (split-𝕆 / split-ℂ / split-ℍ) stop being hand-rolled.
        ToolEntry(
            name="srmech.amsc.cascade.algebra_table", owner="srmech",
            category="cascade",
            summary="The rank-3 structure-constant TABLE of the GENERALISED "
                    "Cayley–Dickson algebra: (a1,a2)(b1,b2) = (a1·b1 + γ·conj(b2)·a2, "
                    "b2·a1 + a2·conj(b1)) with one γ ∈ {+1, −1} PER DOUBLING, in "
                    "LADDER order (gammas[0] = ℝ→ℂ). γ = −1 everywhere is the "
                    "definite ladder ℝ→ℂ→ℍ→𝕆→𝕊…; a +1 anywhere makes the algebra "
                    "SPLIT from that rung up. THE DEFAULT IS THE SHIPPED ALGEBRA, "
                    "BIT-IDENTICALLY: gammas=None reproduces cd_basis_product at "
                    "every (dim, i, j) to dim 64, algebra_table(8) IS "
                    "qm.octonion_mult_table() and algebra_table(4) IS "
                    "qm.quaternion_mult_table(), and table_product over it "
                    "reproduces cd_mult 300/300 (int) + 200/200 (exact-ℚ) — the "
                    "same C cocycle engine, called with and without a γ vector. "
                    "MEASURED at dim 8 over all eight γ-triples: exactly TWO "
                    "answers — (−1,−1,−1) → trace (1,7,0) / norm (8,0,0) = 𝕆, and "
                    "every other triple → (5,3,0) / (4,4,0) = split-𝕆. WHY IT "
                    "SHIPS: CONTROLS, not capability — every negative control this "
                    "arc needed was hand-rolled for want of a constructor, while "
                    "the whole γ-family is sign-cocycle-degenerate the same "
                    "344/512 way and every associative twist is a matrix algebra "
                    "the Mat carrier already publishes. The table is MONOMIAL "
                    "(e_i·e_j = ±e_{i⊕j}), exact integers, no float / no abs(). "
                    "Same-rc C peer srmech_algebra_table. Class K ∘ C ∘ A. SSoT: "
                    "Schafer (1966) §III.4; Springer & Veldkamp (2000) §1.5–1.7."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("dim", "int", True,
                  "a power of two in [1, ALGEBRA_TABLE_MAX_DIM=64]. That ceiling "
                  "bounds MATERIALISING the dim³ tensor — not addressing "
                  "(CD_MAX_DIM=256), not composition (CD_COMPOSE_MAX_DIM=8), not "
                  "turn-folding (CD_TURN_MAX_DIM=4)"),
                P("gammas", "Sequence[int] | None", False,
                  "log2(dim) entries, each +1 (SPLIT at that doubling) or −1 "
                  "(definite), in LADDER order: gammas[0] is ℝ→ℂ, gammas[1] is "
                  "ℂ→ℍ, … None (default) is −1 everywhere"),
            ),
            returns=R("list", "dim × dim × dim nested list[int]; table[i][j][k] "
                              "is the coefficient of e_k in e_i·e_j — the shape "
                              "inertia_signature reads and octonion_mult_table "
                              "returns"),
        ),
        # rc352 (`#T997`): cd_mult's TABLE-DRIVEN sibling. Two table-driven
        # products already existed in-tree (a private dim-8 loop in laplacian
        # with one caller, and a test-local oracle that existed BECAUSE no
        # shipped product took a table) and zero shipped; this is the one both
        # now route through.
        ToolEntry(
            name="srmech.amsc.cascade.table_product", owner="srmech",
            category="cascade",
            summary="The product of two elements read off a STRUCTURE-CONSTANT "
                    "TABLE: (x·y)_k = Σ_ij table[i][j][k]·x_i·y_j — exact, "
                    "table-sensitive, and defined for algebras srmech has no "
                    "hard-wired product for (a split twist from algebra_table, a "
                    "hand-built control, a random table with no algebraic "
                    "structure at all). cd_mult computes the ONE Cayley–Dickson "
                    "product its recursion is wired for; this computes whichever "
                    "algebra the caller names. IT AGREES WITH THE SHIPPED PRODUCT "
                    "WHERE BOTH ARE DEFINED — table_product(algebra_table(dim), x, "
                    "y) == cd_mult(x, y), 300/300 on random dim-8 integer pairs "
                    "and 200/200 on random exact-ℚ pairs — and the two routes are "
                    "genuinely different (a triple loop over a materialised tensor "
                    "versus a recursive doubling), so the agreement is a "
                    "differential, not a tautology. Returns exact Q, the same "
                    "carrier cd_mult returns, so the two are directly comparable. "
                    "Zero coefficients are skipped, so a MONOMIAL table costs "
                    "O(dim²) rather than O(dim³). No float, no epsilon, no abs(). "
                    "Same-rc C peer srmech_algebra_table_product — the SAME "
                    "exact-ℚ element domain as srmech_cd_mult, so no int64 "
                    "element ceiling and no decline. Class M ∘ K ∘ N."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("table", "list[list[list[int]]]", True,
                  "the dim × dim × dim structure-constant tensor of exact int; "
                  "the dimension is len(table) and nothing else supplies it"),
                P("x", "sequence", True,
                  "the left element, len(table) exact-rational components (int / "
                  "Q / Fraction / float → its EXACT ratio / (num, den))"),
                P("y", "sequence", True, "the right element, same length"),
            ),
            returns=R("tuple", "dim-tuple of exact Q — the k-th entry is "
                               "Σ_ij table[i][j][k]·x_i·y_j"),
        ),
        # rc310: the DISCRETE quaternion group Q8 = {+-1,+-i,+-j,+-k} as 3-bit
        # bytes — the discrete peer of the continuous ℍ surface (qm.quaternion).
        # The cascade-faithful Q8-genome foundation (ADDITIVE; no genome wiring).
        # q8_project_v4 is the EXACT F380/R21 homomorphism π: Q8 → V4 collapsing
        # this onto hdc.klein4_bind: π(q8_bind(a,b)) == klein4_bind(π a, π b).
        ToolEntry(
            name="srmech.amsc.q8.q8_mult", owner="srmech", category="q8",
            summary="The Q₈ group product a·b of two 3-bit bytes "
                    "(q=(sign<<2)|coset; 0=+1,1=+i,2=+j,3=+k,4=−1,…,7=−k). "
                    "Non-abelian (q8_mult(1,2)=3 but q8_mult(2,1)=7); i²=j²=k²=4 "
                    "(−1); associative over all 8×8×8. The sign is the "
                    "Cayley–Dickson cocycle (derived from cd_basis_product) xored "
                    "with the two center bits — never an abs(). The abelian "
                    "projection is exact: (a·b)&3 == (a&3)^(b&3). Class M∘I. "
                    "Same-rc C peer srmech_q8_mult (byte-exact).",
            parameters=(P("a", "int", True, "a Q₈ element in [0, 8)"),
                        P("b", "int", True, "a Q₈ element in [0, 8)")),
            returns=R("int", "the product a·b as a Q₈ byte in [0, 8)"),
            #  rc347 (`#T985`) LANE: the product factors into exactly the two
            # lanes: index = xa XOR xb, sign = sa XOR sb XOR F[xa][xb].
            # MEASURED 400/400 to both
            reads_lane="both",
            reads_input=("algebra",),
        ),
        ToolEntry(
            name="srmech.amsc.q8.q8_conjugate", owner="srmech", category="q8",
            summary="The Q₈ conjugate / group inverse: conj(a)=a for the center "
                    "(coset 0, self-inverse), else a^4 (flip an imaginary coset's "
                    "sign bit). q8_mult(a, q8_conjugate(a))==0 for every a. "
                    "Class C (orientation; a plain sign-bit flip, no abs()). "
                    "Same-rc C peer srmech_q8_conjugate (byte-exact).",
            parameters=(P("a", "int", True, "a Q₈ element in [0, 8)"),),
            returns=R("int", "conj(a) as a Q₈ byte in [0, 8)"),
            #  rc347 (`#T985`) LANE: reads the index to DECIDE (the center
            # coset is self-inverse) and flips the sign. MEASURED 400/400 to
            # both perturbations
            reads_lane="both",
            reads_input=("algebra",),
        ),
        ToolEntry(
            name="srmech.amsc.q8.q8_bind", owner="srmech", category="q8",
            summary="Elementwise Q₈ bind out[i]=q8_mult(turn[i], one[i]) over two "
                    "equal-length Q₈ byte buffers (the buffer form of q8_mult). "
                    "Class M (group bind). Same-rc C peer srmech_q8_bind "
                    "(documents the out-aliasing contract; byte-exact).",
            parameters=(P("turn", "bytes", True, "left operand Q₈ byte buffer"),
                        P("one", "bytes", True, "right operand, same length")),
            returns=R("bytes", "the elementwise product, length len(turn)"),
            #  rc347 (`#T985`) LANE: the buffer form of q8_mult, so it reads
            # both lanes elementwise. MEASURED 400/400 to both
            reads_lane="both",
            reads_input=("algebra",),
        ),
        ToolEntry(
            name="srmech.amsc.q8.q8_project_v4", owner="srmech", category="q8",
            summary="The abelian projection π: Q₈ → V4 elementwise: out[i]=q[i]&3 "
                    "(drop the center sign bit, keep the {1,i,j,k} coset). The "
                    "exact F380/R21 homomorphism onto hdc.klein4's value algebra: "
                    "π(q8_bind(a,b)) == klein4_bind(π a, π b). Class I (abelian "
                    "coset read). Same-rc C peer srmech_q8_project_v4 (byte-exact).",
            parameters=(P("q", "bytes", True, "a Q₈ byte buffer"),),
            returns=R("bytes", "the V4 cosets, each in {0, 1, 2, 3}"),
            #  rc347 (`#T985`) LANE: the abelian coset read IS the index-lane
            # projection: out = q & 3 masks the center bit away. MEASURED
            # 0/400 response to a sigma flip, 400/400 to an Aut(V4) index
            # relabel
            reads_lane="index",
            reads_input=("algebra",),
        ),
        # rc315 (§Q8 completeness): the OCT one MINTER — the Q₈ analogue of
        # hdc.klein4_from_one, so a Q₈ (substrate) genome can be MINTED + read
        # through the normal genome API (mint_strand/genes/gene_express/partition
        # gained an element_type=ELEMENT_TYPE_Q8 path this rc) with NO hand-
        # construction of the coupling. Native+pure BY COMPOSITION of two already-
        # C-peered ops (klein4_from_one + klein4_address) → no new C symbol, ABI 10.
        ToolEntry(
            name="srmech.amsc.q8.q8_from_one", owner="srmech", category="q8",
            summary="ONE-OCT — the One's Q₈ COUPLING projection (the Q₈ analogue of "
                    "hdc.klein4_from_one). Mints the sectors=8 (OCT) coupling one of "
                    "leaf dim D (bytes 0..7) so a Q₈ (substrate) genome can be MINTED "
                    "+ read through the normal genome API with NO hand-construction. "
                    "Two DECLARED planes of the One's (σ, θ, terms): the V4 COSET "
                    "plane (bits 0..1) IS klein4_from_one's output — so "
                    "q8_project_v4(q8_from_one(one,D)) == klein4_from_one(one,D) "
                    "EXACTLY (the F380/R21 backward-faithful bridge, by "
                    "construction); the Z₂ SIGN plane (bit 2) is a domain-separated "
                    "Class-A klein4_address of the same One (bit 0 per slot) — a "
                    "declared function, so the coupling is a GENUINE non-abelian Q₈ "
                    "one, not a degenerate all-positive one. The sign is a group ⊕-bit "
                    "(Class-I parity), never an abs(). Class A (both planes) ∘ Class C "
                    "(sign) ∘ Class M (byte interleave). Native+pure BY COMPOSITION of "
                    "the C-peered srmech_klein4_from_one + srmech_klein4_address (a "
                    "bare-C host mints by the same composition) — no dedicated C "
                    "symbol; ABI 10.",
            parameters=(P("one", "One", True,
                          "a cascade One (exposes .sigma, .theta=(num, den), "
                          ".terms)"),
                        P("D", "int", True,
                          "dimension — free; nothing requires or gains from "
                          "divisibility by 14")),
            returns=R("HV", "the OCT coupling one, sectors=8, uint8 in {0..7}"),
        ),
        # rc324: the DISCRETE octonion Moufang loop {±e₀..±e₇} as 4-bit bytes —
        # the Cayley–Dickson rung ABOVE Q8 (the byte-exact carrier peer of the
        # float srmech.qm.octonion ODFT). The genome's 𝕆 element-type carrier
        # (ELEMENT_TYPE_OCTONION): stores the FULL octonion (indices 0..7, incl.
        # the non-quaternionic 4..7). ADDITIVE; carrier only (the associator /
        # fiber channel is a later rc). oct_mult's sign is the cd_basis_product
        # cocycle at dim 8 xored with the two center bits — never an abs().
        ToolEntry(
            name="srmech.amsc.octonion.oct_mult", owner="srmech",
            category="octonion",
            summary="The octonion Moufang-loop product a·b of two 4-bit bytes "
                    "(o=(sign<<3)|index; 0=+e₀,…,7=+e₇,8=−e₀,…,15=−e₇). The "
                    "Cayley–Dickson rung above q8_mult: NON-associative for ≥3 "
                    "independent units (the octonion associator), e_i²=−1 (byte "
                    "8) for i≠0. The sign is the cd_basis_product cocycle at dim "
                    "8 xored with the two center bits — never an abs(); the index "
                    "lane is exact (a·b)&7 == (a&7)^(b&7). Class M∘I. Same-rc C "
                    "peer srmech_oct_mult (byte-exact).",
            parameters=(P("a", "int", True, "an octonion element in [0, 16)"),
                        P("b", "int", True, "an octonion element in [0, 16)")),
            returns=R("int", "the product a·b as an octonion byte in [0, 16)"),
        ),
        ToolEntry(
            name="srmech.amsc.octonion.oct_conjugate", owner="srmech",
            category="octonion",
            summary="The octonion conjugate / loop inverse: conj(a)=a for the "
                    "real center (index 0, self-inverse), else a^8 (flip an "
                    "imaginary unit's sign bit). oct_mult(a, oct_conjugate(a))==0 "
                    "for every a (the Moufang inverse property). Class C "
                    "(orientation; a plain sign-bit flip, no abs()). Same-rc C "
                    "peer srmech_oct_conjugate (byte-exact).",
            parameters=(P("a", "int", True, "an octonion element in [0, 16)"),),
            returns=R("int", "conj(a) as an octonion byte in [0, 16)"),
        ),
        ToolEntry(
            name="srmech.amsc.octonion.oct_bind", owner="srmech",
            category="octonion",
            summary="Elementwise octonion bind out[i]=oct_mult(turn[i], one[i]) "
                    "over two equal-length octonion byte buffers (the buffer form "
                    "of oct_mult). Class M (loop bind). Same-rc C peer "
                    "srmech_oct_bind (documents the out-aliasing contract; "
                    "byte-exact).",
            parameters=(P("turn", "bytes", True, "left operand octonion buffer"),
                        P("one", "bytes", True, "right operand, same length")),
            returns=R("bytes", "the elementwise product, length len(turn)"),
        ),
        # rc116 (#1248 / F1038): the Hurwitz rung of the CARRIER CONVERSION
        # LADDER — promote / project between ℝ↪ℂ↪ℍ↪𝕆↪𝕊, the algebra-one-level-up
        # analog of the srmech.amsc.carrier_ladder variable ladder. Pure
        # carrier restructuring (zero-pad up / trivial-check + drop down; no
        # numerical kernel) → non_compute.
        ToolEntry(
            name="srmech.amsc.cascade.cd_promote", owner="srmech",
            category="cascade",
            summary="Promote a Cayley–Dickson element UP one-or-more rungs "
                    "ℝ↪ℂ↪ℍ↪𝕆↪𝕊 by the trivial SUBALGEBRA EMBEDDING (#1248 / "
                    "F1038): zero-pad the higher imaginary half, x ↦ (x, 0). "
                    "dim is the target power-of-two dimension (≥ the element's "
                    "dim). TOTAL (a no-op when dim == the element's dim). This "
                    "is the SAME embedding the qm.octonion/quaternion "
                    "restriction tests exercise (a quaternion q₄ sits in 𝕆 as "
                    "q₄⊕0₄ under the shared cd_basis_product cocycle — ℍ is the "
                    "top-4 of 𝕆). The inverse of cd_project: "
                    "cd_project(cd_promote(x, 2·dim))==x EXACT. Pure carrier "
                    "restructuring → non_compute. Exact-rational; no float; no "
                    "abs()." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True, "a power-of-two-length element"),
                P("dim", "int", True,
                  "target power-of-two dimension (≥ the element's dim, ≤ 64)"),
            ),
            returns=R("tuple",
                      "the element zero-padded up to dim, a tuple of exact "
                      "Q"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_project", owner="srmech",
            category="cascade",
            summary="Project a Cayley–Dickson element DOWN one doubling "
                    "(dim → dim/2) by REALIFYING IFF the higher "
                    "(imaginary-doubling) half all vanish (#1248 / F1038) — the "
                    "inverse of cd_promote. If the top half is zero, returns the "
                    "bottom half (a complex (a,0) IS the real a); if a higher "
                    "component is genuinely present, raises a coherency error "
                    "NAMING that component (never a silent truncation — the "
                    "rc104 lesson). A real (dim 1) element has no higher half → "
                    "error. cd_project(cd_promote(x, 2·d))==x EXACT. Pure "
                    "carrier restructuring → non_compute. Exact-rational (the "
                    "vanishing test is a Q!=0 Class-K comparison); no "
                    "float; no abs()." + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True,
                  "a power-of-two-length element (dim ≥ 2)"),
            ),
            returns=R("tuple",
                      "the bottom half (the realified element), a tuple of "
                      "exact Q; raises a NAMING coherency error if the "
                      "higher half is non-zero"),
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
                      "{'dim':16, 'x','y': Q tuples, 'x_form','y_form': "
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
                    "element of a division algebra (≤𝕆). Class L (linear-algebra rank). "
                    "rc352 (`#T997`): pass a structure-constant TABLE and this becomes a "
                    "zero-divisor WITNESS on any algebra a table can express — split-𝕆 "
                    "exhibits one at dim 8, where the shipped ladder has none. Witness "
                    "half ONLY: zero divisors are measure-zero (left_mult_is_invertible "
                    "returned True on 300/300 random dim-16 elements), so FINDING a "
                    "candidate is a separate problem this op does not solve."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True, "a power-of-two-length element"),
                P("table", "list[list[list[int]]] | None", False,
                  "the dim × dim × dim structure-constant tensor naming the algebra "
                  "(e.g. from algebra_table). None (default) is the shipped "
                  "Cayley–Dickson product, unchanged"),
            ),
            returns=R("list", "kernel-basis vectors (Q tuples); empty if invertible"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.left_mult_is_invertible", owner="srmech",
            category="cascade",
            summary="True iff u ↦ x·u is a bijection (a backward direction exists). "
                    "Always True for nonzero x at dims ≤ 8 ON THE DEFINITE LADDER; False "
                    "for a zero divisor at dim ≥ 16 — the reversibility that ends at the "
                    "Hurwitz wall. rc352 (`#T997`): hand it a SPLIT table and False "
                    "appears at dim 2 already, which is the honest answer and the "
                    "ladder's own wall is not it. With a table the rc12 modular-rank gate "
                    "does not apply (it rebuilds the signed XOR-circulant from the "
                    "shipped cocycle, so it is Cayley–Dickson-specific by construction) "
                    "and the op takes the exact-kernel route instead — NOT a degradation: "
                    "srmech_qmat_nullspace over the srmech_algebra_table_product-composed "
                    "L(x) is C the whole way down and exact at any magnitude, so a bare-C "
                    "host answers identically (ADR-0009 — a different C route, not a "
                    "decline)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("x", "sequence", True, "a power-of-two-length element"),
                P("table", "list[list[list[int]]] | None", False,
                  "the dim × dim × dim structure-constant tensor naming the algebra "
                  "(e.g. from algebra_table). None (default) is the shipped "
                  "Cayley–Dickson product, unchanged"),
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
        # The GENERAL N-slot Cayley–Dickson register (v0.9.0rc297; `#934`) — the
        # 16-slot instrument above generalised to any power-of-two dim in
        # [1, CD_MAX_DIM]. Registered under STABLE flat names; the submodule-dotted
        # ``cascade.cd_register.*`` are the same objects re-exported flat (exempt in
        # test_tool_schema_coverage). The class CDRegister is not a module-level
        # function (not coverage-walked). SedenionRegister deliberately REMAINS an
        # independent class, not an n=16 alias — it is the oracle the general
        # register's faithfulness is gated against.
        ToolEntry(
            name="srmech.amsc.cascade.cd_register", owner="srmech",
            category="cascade",
            summary="Construct a CDRegister — the GENERAL N-slot Cayley–Dickson "
                    "ADDRESSABLE RBS-HDC register (`#934`). The dim-16 "
                    "sedenion_register generalised to any power-of-two dim in "
                    "[1, 64]: dim named slots e0..e{dim-1}, with e0..e7 the octonion "
                    "reversible working block at EVERY rung and the remainder the "
                    "carry/EC block (more slots buy ADDRESS SPACE, never a longer "
                    "reversible word — the Hurwitz cap stays 7). The slot bound is the "
                    "ONLY generalisation: every sign and index rule is shared with the "
                    "16-slot register through cd_basis_product, so there is no second "
                    "algebra. LEGITIMATE PAST THE HURWITZ WALL because addressing rides "
                    "on the basis product being a SIGNED PERMUTATION (e_i·e_j=±e_k), "
                    "while zero divisors are built from SUMS of basis elements — "
                    "disjoint properties, so the boundary that breaks composition at "
                    "dim≥16 (and ~95% of generic pairs at 32) leaves addressing intact "
                    "(F1274/F1275). namespace= selects the address-mint namespace "
                    "(default 'CD{dim}'); namespace='SEDENION' at dim=16 reproduces the "
                    "shipped SedenionRegister BIT-EXACTLY at every D — the faithfulness "
                    "gate. Capacity is D-bounded and MORE SLOTS NEED MORE D: a shortfall "
                    "at fixed D is a capacity fact, not an algebra fact — sweep D. "
                    "numpy-free; no abs() (sign is Class-K pin-slot ∘ Class-C)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("dim", "int", True, "slot count — a Cayley–Dickson algebra dimension; a power of two in [1, 64] (8 𝕆 / 16 𝕊 / 32 𝕋 / 64)"),
                P("D", "int", False, "hypervector width in bits (default 8192; the RBS-HDC dimension)"),
                P("codebook", "dict", False, "optional preset {name: bytes} value-vectors for read cleanup"),
                P("namespace", "Optional[str]", False, "address-mint namespace (default 'CD{dim}'); 'SEDENION' at dim=16 reproduces the shipped register bit-exactly"),
                P("coupling", "bool", False, "opt into OPT layer 1 — the reversible working word (couple_working / uncouple_working, Class M, cap min(dim,8)−1). Default False (bare = pure addressing)"),
                P("error_correction", "bool", False, "opt into OPT layer 2 — the Hamming EC/carry block (carry / correct, an axis independent of dim). Default False"),
            ),
            returns=R("CDRegister",
                      "the register — CORE: .write/.read (addressable storage), "
                      ".element/.norm/.conjugate/.multiply/.add (per-rung carrier "
                      "arithmetic over the slot-held signed-basis element Σ sign_i·e_i "
                      "— the method-form of cd_norm_sq/cd_conjugate/cd_mult/cd_add; "
                      "`#948`), .navmap/.navigate (the address↔Cayley–Dickson "
                      "homomorphism), .is_navigable (reversibility gate), "
                      ".working_block/.carry_block (the block split); OPT (opt-in): "
                      ".couple_working/.uncouple_working (reversible word), "
                      ".carry/.correct (EC block)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_navmap", owner="srmech",
            category="cascade",
            summary="The signed pointer-advance permutation for right-multiply-by-e_j "
                    "over dim slots: maps each slot i to (k, sign) where e_i·e_j = "
                    "sign·e_k (the cd_basis_product cocycle). The general-rung form of "
                    "SedenionRegister.navmap; at dim=16 bit-identical to it. ALWAYS a "
                    "signed permutation — reversible at EVERY rung for a single basis "
                    "direction, including past the Hurwitz wall (F1275). Integer-only; "
                    "the JPL-clean C peer srmech_cd_navmap returns the identical map."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("dim", "int", True, "algebra dimension — a power of two in [1, 64]"),
                P("j", "int", True, "navigation basis direction in [0, dim)"),
            ),
            returns=R("dict", "{i: (dest, sign)} over all dim slots; sign in {+1,-1}"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_navigate", owner="srmech",
            category="cascade",
            summary="Route occupied (slot, sign) records through the ×e_j permutation "
                    "at dim slots, composing the CLASS-C signs: out_signs[m] = "
                    "signs[m]·s where e_{slots[m]}·e_j = s·e_{out_slots[m]}. The numeric "
                    "core of CDRegister.navigate (the key strings ride alongside in the "
                    "caller); at dim=16 bit-identical to the sedenion navigate routing. "
                    "Integer-only; the JPL-clean C peer srmech_cd_navigate returns the "
                    "identical routing. No abs() — the sign is composed, never dropped."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("dim", "int", True, "algebra dimension — a power of two in [1, 64]"),
                P("j", "int", True, "navigation basis direction in [0, dim)"),
                P("slots", "Sequence[int]", True, "occupied slot indices, each in [0, dim)"),
                P("signs", "Sequence[int]", True, "the Class-C sign of each record, each in {+1,-1}"),
            ),
            returns=R("tuple", "(out_slots, out_signs) — two lists, parallel to the input"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_navmap_is_signed_permutation", owner="srmech",
            category="cascade",
            summary="THE STRUCTURAL INVARIANT ADDRESSING RIDES ON, checked rather than "
                    "assumed (F1274/F1275): for EVERY direction j in [0, dim), is "
                    "i→(dest, sign) a bijection on [0, dim) with every sign in {+1,-1}? "
                    "This is what makes an N-slot register legitimate past the Hurwitz "
                    "boundary — composition fails at dim≥16 and for ~95% of generic "
                    "pairs at 32, while addressing is untouched, because zero divisors "
                    "are built from SUMS of basis elements and this property is about a "
                    "SINGLE basis pair. SCOPE: verifies the bijection + sign-domain of "
                    "the navmap AS COMPUTED BY the cd_basis_product cocycle; it does NOT "
                    "independently re-derive e_i·e_j from a full Cayley–Dickson "
                    "multiplication — that cross-path check (cocycle vs full cd_mult, "
                    "4096/4096 pairs at dim 64) is enforced in the Python test suite. "
                    "The JPL-clean C peer srmech_cd_navmap_is_signed_permutation returns "
                    "the identical bool, so a bare-C host can verify its own address "
                    "layer before trusting it."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("dim", "int", True, "algebra dimension — a power of two in [1, 64]"),
            ),
            returns=R("bool", "True iff the premise holds at this rung"),
        ),
        # The two OPTIONAL layers of the general N-slot register as pure functions
        # (v0.9.0rc301; `#T938`) — the reversible working word (couple/uncouple) +
        # the Hamming EC block (carry/correct), ported from SedenionRegister onto
        # CDRegister as its dim-scaled generalisation. Registered under STABLE flat
        # names ``srmech.amsc.cascade.cd_{couple_working,uncouple_working,carry,
        # correct}``; the submodule-dotted ``cascade.cd_register.*`` are the same
        # objects re-exported flat (exempt in test_tool_schema_coverage). These take
        # content-agnostic list/int args (MCP-coercible), UNLIKE the sed_* adapters'
        # structured slots/codebook state — which is why they are first-class tools
        # while the sed_* peers stay TOML-class-only. composition_of_c in the Rosetta
        # ledger (they compose the C-backed hypercomplex_couple / hamming — no new C
        # symbol, ABI stays 8).
        ToolEntry(
            name="srmech.amsc.cascade.cd_couple_working", owner="srmech",
            category="cascade",
            summary="Bind ≤ min(dim,8)−1 real streams into one REVERSIBLE working "
                    "word — THE canonical Class-M bind on the Cayley–Dickson register "
                    "(`#T938`). The dim-scaled generalisation of the sedenion's ≤7 "
                    "working word: the cap is min(dim,8)−1, DERIVED from Hurwitz, "
                    "never a hardcoded 7 — dim 2 couples 1 imaginary slot, dim 4 "
                    "couples 3, dim 8/16/…/256 couple 7 (the e0..e7 octonion "
                    "subalgebra of every higher rung), dim 1 (ℝ) couples nothing (the "
                    "degenerate base: empty in → empty out). Composes "
                    "hypercomplex_couple (axis='diagonal', the F436 coupling axis; its "
                    "octonion multiply dispatches to the standalone-C "
                    "srmech_hypercomplex_couple_q61) — reversed exactly by "
                    "cd_uncouple_working (T̄·(T·q)=‖T‖²·q, F437). At dim 16 bit-exact "
                    "with the shipped SedenionRegister.couple_working. No abs() (the "
                    "coupler's sign is Class-K ∘ Class-C). Class M ∘ C ∘ N."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("vals", "sequence", True,
                  "≤ min(dim,8)−1 real streams to fold into the working word"),
                P("dim", "int", False,
                  "register rung (power of two in [1, 256]); sets the cap. Default 8 "
                  "(the octonion working word, cap 7)"),
            ),
            returns=R("list[float]",
                      "the coupled working word — a 4-component quaternion (≤3 "
                      "streams) or 8-component octonion (4–7 streams); [] if empty"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_uncouple_working", owner="srmech",
            category="cascade",
            summary="Recover the streams bound by cd_couple_working — the EXACT "
                    "inverse (the Class-M unbind; `#T938`). Applies the conjugate "
                    "twiddle (inverse=True) and drops the anchor slot, returning the "
                    "carrier's imaginary components (7 for an octonion word, 3 for a "
                    "quaternion word). Empty in → empty out (the dim-1 boundary). "
                    "Recovery is exact to float round-off (the division-algebra "
                    "identity T̄·(T·q)=‖T‖²·q, F437), matching the shipped register's "
                    "tolerance. Composes hypercomplex_couple; no abs(). Class M ∘ C ∘ N."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("word", "sequence", True,
                  "a coupled working word (4-component quaternion / 8-component "
                  "octonion) from cd_couple_working"),
            ),
            returns=R("list[float]",
                      "the recovered streams (the carrier's imaginary slots); [] if "
                      "empty"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_carry", owner="srmech",
            category="cascade",
            summary="Encode overflow bits (past the reversible working set) into a "
                    "Hamming(2ⁿ−1) single-error-correcting GF(2) codeword — the "
                    "EC/carry layer of the register (`#T938`). The EC axis is "
                    "INDEPENDENT of the register's dim: the block size is set by n "
                    "(parity-bit count; codeword 2ⁿ−1, data 2ⁿ−1−n), NOT by the slot "
                    "count. Composes hamming_encode (the srmech_hamming_encode C "
                    "peer). Lean-ALU XOR-native (GF(2) add = parity = XOR); no float, "
                    "no libm, no abs(). Class B ∘ I ∘ A. SSoT: Hamming (1950)."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("overflow_bits", "sequence", True,
                  "exactly 2ⁿ−1−n data bits, each 0/1 (4 for H(7,4), 11 for H(15,11))"),
                P("n", "int", False,
                  "parity-bit count, 2 ≤ n ≤ 16; codeword length 2ⁿ−1. Default 3 "
                  "(Hamming(7,4) — the octonion's own Fano plane)"),
            ),
            returns=R("list[int]", "the 2ⁿ−1-bit codeword (0/1 list)"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.cd_correct", owner="srmech",
            category="cascade",
            summary="Locate + correct a single-bit error in an EC-block codeword and "
                    "recover the carried payload — the EC/carry layer's read (`#T938`). "
                    "Single-error-correcting (minimum distance 3): a clean or "
                    "single-error word recovers exactly. Composes "
                    "hamming_decode_correct (the syndrome dispatches to "
                    "srmech_hamming_syndrome). Lean-ALU XOR; no float, no libm, no "
                    "abs() (the located bit is a Class-K GF(2) flip). Class B ∘ I ∘ A."
                    + PUBLISH_OPT_IN_NOTE,
            parameters=(
                P("codeword", "sequence", True, "a 2ⁿ−1-bit codeword (0/1 list)"),
            ),
            returns=R("dict",
                      "{'data': k corrected payload bits, 'error_position': int "
                      "(0=clean), 'corrected_codeword': the repaired 2ⁿ−1-bit word}"),
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
        # ────────────────────────────────────────────────────────────
        # rc215 (the #741 divmod audit, finding F-2) — the 2π seam-fold
        # DIVMOD as a first-class public op: the exact fold existed
        # natively (srmech_winding_fold, rc207/gh#1276) and pure (the
        # laplacian _eph_seam_fold) but was reachable only through
        # propagate_wound; an external consumer with an accumulated
        # angle had to hand-roll a float `theta % 2π` — BOTH the
        # grading-collapse the audit hunts AND a precision hazard.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.cascade.winding_fold", owner="srmech",
            category="cascade",
            summary="The 2π seam-fold as the DIVMOD it is: theta → (w, "
                    "theta_res) with theta = 2π·w + theta_res, the quotient "
                    "KEPT (the #741 mod-should-be-divmod audit, finding F-2). "
                    "w = round(theta/2π) (round-half-toward-+∞) is the "
                    "METACYCLE winding — the whole 2π turns a bare float "
                    "`theta % (2*pi)` throws away (the grading-collapse the "
                    "audit hunts, and a precision hazard vs the exact fold); "
                    "theta_res is the EPICYCLE residue (|theta_res| ≤ π). The "
                    "op an external consumer folds an accumulated angle with "
                    "(a Kuramoto phase, an Im(z)·λ from its own solve) — the "
                    "SAME fold propagate/propagate_wound run at the seam (no "
                    "forked 2π constant), exposed first-class. The winding "
                    "feeds the One's metacycle dial directly (the_one(σ, "
                    "θ_num, θ_den, w=(w,0,0)) → sigma_effective / spinor_sign "
                    "/ unwrapped_phase). Cascade: Class-I divmod (quotient "
                    "retained) over the exact Class-N 2π (Machin-2π rational "
                    "pure / Q61 2/π native); residue sign Class K/C, never "
                    "abs(). Dispatches to the native srmech_winding_fold "
                    "(rc207) inside its |theta| < 2^55 domain; the pure "
                    "exact-rational Machin-2π divmod is the COMPLETE "
                    "alternative at any finite float. Native == pure: w "
                    "exact-integer equal; theta_res to the fold grids' "
                    "common resolution. Complex input rejected (real-axis "
                    "fold); non-finite rejected (finite-angle domain).",
            parameters=(
                P("theta", "float", True,
                  "the accumulated angle in radians — any finite real"),
            ),
            returns=R("tuple", "(w, theta_res) — w the whole-ℤ metacycle "
                               "winding (int), theta_res the folded epicycle "
                               "residue (float, |theta_res| ≤ π); 2π·w + "
                               "theta_res reconstructs theta on the fold "
                               "grid"),
        ),
        # ────────────────────────────────────────────────────────────
        # rc238 (#1385 F-thread) — the FRAME-CARRYING CARRIER: augment a
        # 2π-periodic truncated-Taylor value with its local beat-frame
        # (σ, w) so a cross-seam compare PARALLEL-TRANSPORTS the frame
        # first → bit-exact where the un-framed compare only sometimes
        # matched. NOT a re-wrap of winding_fold (float residue) / the_one
        # (folds w away): the transport is an EXACT-rational 2π divmod over
        # the Machin-2π anchor _EPH_TWO_PI, feeding the exact series.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.amsc.cascade.frame_carrier.frame_carrier",
            owner="srmech", category="cascade",
            summary="The FRAME-CARRYING CARRIER: augment a 2π-periodic "
                    "truncated Taylor series (sin/cos_series_truncate) with "
                    "its local beat-frame (sigma, winding) so cross-seam "
                    "compares can parallel-transport it (rc238). The raw "
                    "series truncates the argument p/q DIRECTLY (it does NOT "
                    "fold), so sin at theta vs theta+2π drifts — exact WITHIN "
                    "a beat (|x|≤π, w=0) but NOT bit-exact across the 2π seam. "
                    "This returns the (value, frame) pair — the rc125 "
                    "recoverable-fold (lossy, exact_seed) analogue with the "
                    "FRAME as the exact second leg: value = the raw local "
                    "series (drifts across the seam); winding/residue/sigma = "
                    "the exact frame (connection element) a compare transports. "
                    "residue is the canonical in-beat representative (|r|≤π, "
                    "theta folded to w=0); transported = the seam-invariant "
                    "value the compare aligns on. Cascade (composition_of_c, "
                    "no new C symbol): the c_dispatched Class-N sin/cos "
                    "series; the transport is the EXACT-rational 2π divmod "
                    "over the Machin-2π anchor _EPH_TWO_PI (Class-I quotient- "
                    "retained divmod over the exact Class-N 2π; residue sign "
                    "Class K/C, never abs()) — NOT winding_fold's float "
                    "residue; reduction rides the c_dispatched Class-I "
                    "rational reduce.",
            parameters=(
                P("func", "str", True,
                  "'sin' or 'cos' — the 2π-periodic series to frame"),
                P("numerator", "int", True,
                  "the argument angle numerator (radians, exact rational p/q)"),
                P("denominator", "int", True,
                  "the argument angle denominator (non-zero)"),
                P("num_terms", "int", True, "Taylor truncation depth N (0..50)"),
                P("sigma", "int", False,
                  "chirality frame component: +1 or -1 (default +1)"),
            ),
            returns=R("dict", "{func, arg, sigma, winding, residue, "
                              "num_terms, value, transported} — value the "
                              "raw (drifting) leg, winding/residue/sigma the "
                              "exact frame, transported the seam-invariant "
                              "in-beat value; rationals are reduced (num, den) "
                              "pairs"),
        ),
        ToolEntry(
            name="srmech.amsc.cascade.frame_carrier.frame_carrier_compare",
            owner="srmech", category="cascade",
            summary="Cross-seam compare of two frame-carrying carriers: "
                    "PARALLEL-TRANSPORT the frame, THEN compare, with the "
                    "exact is_aligned certificate (rc238). Reports raw_equal "
                    "(the UN-framed compare A.value==B.value — the 'sometimes "
                    "not bit-exact across the seam' drift symptom) AND "
                    "transported_equal (the FRAMED compare "
                    "A.transported==B.transported — each argument "
                    "exact-rational-folded to its canonical residue first: "
                    "bit-exact across the seam where the raw compare only "
                    "sometimes matched). aligned = True iff the transport "
                    "lands in the value's winding-stabilizer (canonical "
                    "residues EQUAL — a whole number of 2π turns apart, a zero "
                    "residue_delta by its Class-K magnitude — AND chiralities "
                    "match); aligned then PROVES the transported values are "
                    "byte-identical (the rc236 is_flat / Stab shape one level "
                    "up). When not aligned it carries the real residual "
                    "(non-zero residue_delta holonomy or chirality mismatch) "
                    "— so a genuinely different value is never falsely aligned "
                    "(soundness). Cascade: composition_of_c over the "
                    "c_dispatched series + the Class-K magnitude (real |x|, "
                    "never abs()) + the exact-rational Machin-2π fold.",
            parameters=(
                P("func", "str", True, "'sin' or 'cos' (same series for both)"),
                P("num_a", "int", True, "carrier A argument numerator"),
                P("den_a", "int", True, "carrier A argument denominator"),
                P("num_b", "int", True, "carrier B argument numerator"),
                P("den_b", "int", True, "carrier B argument denominator"),
                P("num_terms", "int", True, "shared Taylor truncation depth N"),
                P("sigma_a", "int", False, "carrier A chirality (+1/-1, default +1)"),
                P("sigma_b", "int", False, "carrier B chirality (+1/-1, default +1)"),
            ),
            returns=R("dict", "{func, raw_equal, transported_equal, aligned, "
                              "transport_turns, transport_magnitude, "
                              "residue_delta, chirality_match} — the drift "
                              "(raw_equal), the fix (transported_equal), the "
                              "exact cert (aligned) + its residual "
                              "(residue_delta)"),
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
            summary="HDC similarity ``1 − 2·hamming(a, b) / D`` in [−1, +1] as "
                    "the EXACT Q rational (v0.9.0 F868). Class M per Kanerva "
                    "2009 §3.2; direct on coefficient bytes. +1 = identical, 0 = "
                    "orthogonal, −1 = anti-correlated." + PUBLISH_OPT_IN_NOTE,
            parameters=(P("a", "SpectralHandle | bytes", True),
                        P("b", "SpectralHandle | bytes", True)),
            returns=R("Q", "exact rational (D−2·hamming)/D in [-1, +1]"),
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
        # The rc111 ODFT twiddle family (#1234 Item 1c, re-raise of #863) —
        # the dim-8 mirror of the rc109 qm.quaternion foundation. Same-rc C
        # peers srmech_octonion_{exp,twiddle}.
        ToolEntry(
            name="srmech.qm.octonion.octonion_exp", owner="srmech",
            category="qm.octonion",
            summary="The octonion Euler formula exp(μθ) = cos θ·1 + sin θ·μ̂ "
                    "for a UNIT pure imaginary μ̂ (μ̂²=−1) — the ODFT twiddle at "
                    "the float64 boundary (the dim-8 quaternion_exp mirror). "
                    "Lives in the commutative ℝ[μ̂] ≅ ℂ; by Artin's theorem the "
                    "2-generator ⟨μ̂, x⟩ associates, so the one-sided ODFT "
                    "round-trip is exact despite 𝕆 non-associativity. "
                    "‖exp(μθ)‖=1; exp(μθ₁)exp(μθ₂)=exp(μ(θ₁+θ₂)); "
                    "exp(μ2π/N)^N=1. Trig = the Q61 Class-N cascade projected "
                    "once (no libm, no math.pi); exact tiers: "
                    "octonion_exp_series_truncate (rational) / "
                    "cascade.hypercomplex_exp k_axes=7 (Q61). Class N∘C∘M. "
                    "Same-rc C peer srmech_octonion_exp (byte-exact).",
            parameters=(
                P("theta", "float", True, "rotation angle θ (radians), finite"),
                P("mu", "str", False,
                  "axis μ̂: 'i'|'j'|'k' (= 'e1'|'e2'|'e3') | 'e4'..'e7' | 'ijk' "
                  "| 'diagonal' (named, exact) or a pure-imaginary 4-/8-vector "
                  "(normalised via the Class-N sqrt cascade); default 'i'"),
            ),
            returns=R("list[float]",
                      "unit octonion [cos θ, sin θ·μ̂₁, …, sin θ·μ̂₇]"),
        ),
        ToolEntry(
            name="srmech.qm.octonion.octonion_exp_series_truncate",
            owner="srmech", category="qm.octonion",
            summary="EXACT-rational exp(e_axis·θ) for a RATIONAL angle θ=p/q — "
                    "the series-truncate tier of the ODFT twiddle (the dim-8 "
                    "quaternion_exp_series_truncate mirror). Composes the "
                    "Class-N calculus series cos/sin_series_truncate (exact "
                    "bignum (num,den) pairs) with an exactly-representable "
                    "basis axis e_axis (axis ∈ {1..7}). π is NOT rational: a "
                    "2πjk/N angle enters only as a caller-chosen rational "
                    "approximant (e.g. best_rational over the π cascade); the "
                    "float64 projection is octonion_twiddle. Class N "
                    "(bignum_reference oracle of the Q61/float paths).",
            parameters=(
                P("theta_num", "int", True, "angle numerator p (radians p/q)"),
                P("theta_den", "int", True, "angle denominator q (nonzero)"),
                P("num_terms", "int", True, "Taylor terms N"),
                P("axis", "int", False, "basis axis e_axis, 1..7; default 1"),
            ),
            returns=R("tuple",
                      "8 exact (num, den) pairs: cos at slot 0, sin at slot "
                      "axis, (0,1) elsewhere"),
        ),
        ToolEntry(
            name="srmech.qm.octonion.octonion_twiddle", owner="srmech",
            category="qm.octonion",
            summary="The ODFT twiddle factor exp(σ·μ·2πjk/N) — the DFT-facing "
                    "octonion_exp (the dim-8 quaternion_twiddle mirror). The "
                    "index product is reduced in Z_N FIRST (Class I, exact), "
                    "then π enters ONCE as the Class-N 4·atan(1) cascade at the "
                    "float64 boundary (never math.pi). σ=−1 (default) = forward "
                    "DFT (matches cascade.octonion_dft); σ=+1 = inverse. "
                    "Twiddle closure: exp(μ2π/N)^N = 1. Class I∘N∘C∘M. Same-rc "
                    "C peer srmech_octonion_twiddle (byte-exact).",
            parameters=(
                P("j", "int", True, "frequency index (non-negative)"),
                P("k", "int", True, "sample index (non-negative)"),
                P("n_points", "int", True, "DFT length N, 1 ≤ N < 2³²"),
                P("mu", "str", False,
                  "axis μ̂: 'i'|'j'|'k' (= 'e1'|'e2'|'e3') | 'e4'..'e7' | 'ijk' "
                  "| 'diagonal', or a pure-imaginary 4-/8-vector; default 'i'"),
                P("sigma", "int", False, "−1 forward (default) | +1 inverse"),
            ),
            returns=R("list[float]", "the unit-octonion twiddle (8 components)"),
        ),

        # ────────────────────────────────────────────────────────────
        # srmech.qm.quaternion — the QDFT/ODFT foundation (0.9.0rc109;
        # #1234 Item 1a, re-raise of #863 BX-5/6/7; F380 / the R21 proof:
        # Q₈/{±1} ≅ Z₂×Z₂ = Klein-4, so ℍ is a Klein-4 object's native
        # coefficient algebra). ℍ = the dim-4 rung of the SAME Cayley-
        # Dickson ladder as qm.octonion (the table IS the octonion table
        # restricted to e0..e3 — tested). Same-rc C peers
        # srmech_quaternion_{left_mult,right_mult,exp,twiddle}.
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_mult_table", owner="srmech",
            category="qm.quaternion",
            summary="The (4,4,4) int8 structure-constant tensor C of ℍ with "
                    "e_i·e_j = Σ_k C[i,j,k] e_k (the SAME fixed Cayley-Dickson "
                    "convention as qm.octonion, restricted to e0..e3; the "
                    "signed units close into Q₈ and Q₈/{±1} is the Klein-4 XOR "
                    "table — F380/R21). Class A. Baez (2002) §1.",
            parameters=(),
            returns=R("list[list[list[int]]]", "(4,4,4) int8 structure constants"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_table_attestation",
            owner="srmech", category="qm.quaternion",
            summary="MPR v1 self-attestation dict for the ℍ structure-constant "
                    "table; response_sha256 content-addresses the 64 int8 table "
                    "bytes via sha256_bytes (Class A). Baez (2002), "
                    "arXiv:math/0105155 §1.",
            parameters=(),
            returns=R("dict", "MPR v1 attestation block"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_left_mult", owner="srmech",
            category="qm.quaternion",
            summary="Left-multiplication matrix L_q (x → q·x) as 4×4 real; "
                    "L_{e_i} (i≥1) is antisymmetric; L(pq)=L(p)L(q) and "
                    "L(p)R(q)=R(q)L(p) (the ℍ associativity witness). The "
                    "basis-column sign structure IS the Klein-4 bridge (row "
                    "index = i⊕j; Q₈/{±1}, F380). Class M (binding). Same-rc "
                    "C peer srmech_quaternion_left_mult.",
            parameters=(P("q", "HV", True, "4-vector quaternion"),),
            returns=R("Mat", "4×4 L_q"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_right_mult", owner="srmech",
            category="qm.quaternion",
            summary="Right-multiplication matrix R_q (x → x·q) as 4×4 real; "
                    "the ANTI-homomorphism R(pq)=R(q)R(p) (ℍ non-commutative "
                    "⟹ L_q ≠ R_q — the genuinely distinct left/right QDFT "
                    "forms stand on this). Class M (binding). Same-rc C peer "
                    "srmech_quaternion_right_mult.",
            parameters=(P("q", "HV", True, "4-vector quaternion"),),
            returns=R("Mat", "4×4 R_q"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_conjugate", owner="srmech",
            category="qm.quaternion",
            summary="Quaternion conjugate conj(x) = (x_0, -x_1, -x_2, -x_3); "
                    "for a unit twiddle it is the inverse (conj(exp(μθ)) = "
                    "exp(−μθ) — the inverse-QDFT twiddle). Class C "
                    "(orientation). Same-rc C peer srmech_quaternion_conjugate "
                    "(byte-exact).",
            parameters=(P("x", "HV", True, "4-vector"),),
            returns=R("list[float]", "4-vector"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_norm", owner="srmech",
            category="qm.quaternion",
            summary="Quaternion norm √(Σ x_i²) via the scalar Class K pin-slot "
                    "magnitude (cascade.magnitude) then sqrt — never abs(). "
                    "Class K∘C.",
            parameters=(P("x", "HV", True, "4-vector"),),
            returns=R("float", "≥ 0; Class K+C, never abs()"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_exp", owner="srmech",
            category="qm.quaternion",
            summary="The quaternion Euler formula exp(μθ) = cos θ·1 + sin θ·μ̂ "
                    "for a UNIT pure imaginary μ̂ (μ̂²=−1) — the QDFT twiddle at "
                    "the float64 boundary. Lives in the commutative ℝ[μ̂] ≅ ℂ "
                    "(why the one-sided QDFT inverts); ‖exp(μθ)‖=1; "
                    "exp(μθ₁)exp(μθ₂)=exp(μ(θ₁+θ₂)); exp(μ2π/N)^N=1. Trig = "
                    "the Q61 Class-N cascade projected once (no libm, no "
                    "math.pi); exact tiers: quaternion_exp_series_truncate "
                    "(rational) / cascade.hypercomplex_exp (Q61). Class N∘C∘M. "
                    "Same-rc C peer srmech_quaternion_exp (byte-exact).",
            parameters=(
                P("theta", "float", True, "rotation angle θ (radians), finite"),
                P("mu", "str", False,
                  "axis μ̂: 'i'|'j'|'k'|'ijk' (named, exact) or a pure-imaginary "
                  "4-vector (normalised via the Class-N sqrt cascade); default 'i'"),
            ),
            returns=R("list[float]",
                      "unit quaternion [cos θ, sin θ·μ̂₁, sin θ·μ̂₂, sin θ·μ̂₃]"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_exp_series_truncate",
            owner="srmech", category="qm.quaternion",
            summary="EXACT-rational exp(e_axis·θ) for a RATIONAL angle θ=p/q — "
                    "the series-truncate tier of the twiddle (the exactness "
                    "convention's exact form). Composes the Class-N calculus "
                    "series cos/sin_series_truncate (exact bignum (num,den) "
                    "pairs) with an exactly-representable basis axis e_axis "
                    "(axis ∈ {1,2,3} = i/j/k). π is NOT rational: a 2πjk/N "
                    "angle enters only as a caller-chosen rational approximant "
                    "(e.g. best_rational over the π cascade); the float64 "
                    "projection is quaternion_twiddle. Class N "
                    "(bignum_reference oracle of the Q61/float paths).",
            parameters=(
                P("theta_num", "int", True, "angle numerator p (radians p/q)"),
                P("theta_den", "int", True, "angle denominator q (nonzero)"),
                P("num_terms", "int", True, "Taylor terms N"),
                P("axis", "int", False, "basis axis: 1 (i) | 2 (j) | 3 (k); default 1"),
            ),
            returns=R("tuple",
                      "4 exact (num, den) pairs: cos at slot 0, sin at slot "
                      "axis, (0,1) elsewhere"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_twiddle", owner="srmech",
            category="qm.quaternion",
            summary="The QDFT twiddle factor exp(σ·μ·2πjk/N) — the DFT-facing "
                    "quaternion_exp. The index product is reduced in Z_N FIRST "
                    "(Class I, exact), then π enters ONCE as the Class-N "
                    "4·atan(1) cascade at the float64 boundary (never math.pi). "
                    "σ=−1 (default) = forward DFT (matches cascade."
                    "quaternion_dft); σ=+1 = inverse. Twiddle closure: "
                    "exp(μ2π/N)^N = 1. Class I∘N∘C∘M. Same-rc C peer "
                    "srmech_quaternion_twiddle (byte-exact).",
            parameters=(
                P("j", "int", True, "frequency index (non-negative)"),
                P("k", "int", True, "sample index (non-negative)"),
                P("n_points", "int", True, "DFT length N, 1 ≤ N < 2³²"),
                P("mu", "str", False,
                  "axis μ̂: 'i'|'j'|'k'|'ijk' or a pure-imaginary 4-vector; "
                  "default 'i'"),
                P("sigma", "int", False, "−1 forward (default) | +1 inverse"),
            ),
            returns=R("list[float]", "the unit-quaternion twiddle (4 components)"),
        ),
        ToolEntry(
            name="srmech.qm.quaternion.quaternion_cycle_holonomy",
            owner="srmech", category="qm.quaternion",
            summary="The NON-ABELIAN cycle holonomies of a quaternion gain "
                    "graph (#T944 follow-on) — the k=2 discrete which-way / "
                    "Lk-analog channel, the associative sibling of the abelian "
                    "laplacian.cycle_holonomy. Edge gains are UNIT quaternions "
                    "(Q₈ = {±1,±i,±j,±k} or a continuous re-gauge). Per "
                    "fundamental cycle H = P_u·g_uv·conj(P_v) (ordered product; "
                    "P_x = the tree-path root→x product, reversed edge = "
                    "conj). A node re-gauge g→s_u·g·conj(s_v) telescopes to "
                    "H→s_root·H·conj(s_root), so the CONJUGACY CLASS is "
                    "gauge-invariant. class_index = the SU(2) class from the "
                    "scalar part w=Re(H): 0={1}(w≈+1), 1={−1}(w≈−1, the spinor/"
                    "Lk half-twist), 2={±i,±j,±k}(w≈0). MEASURED (the rc309 "
                    "proof gate): the finer 5-class Q₈ split is invariant only "
                    "under DISCRETE Q₈ re-gauge — continuous SU(2) merges the "
                    "three axes, so only the scalar-part class is frame-free. "
                    "center_parity = the {1}/{−1} central sign. Native "
                    "standalone-C srmech_quaternion_cycle_holonomy "
                    "(caller-arena); else the byte-exact quaternion cascade. "
                    "numpy-free; no abs(). Class M∘L∘C.",
            parameters=(P("edges", "list[tuple[int, int]]", True,
                          "a self-loop is a 1-cycle; a parallel edge a digon"),
                        P("gains", "Optional[list[list[float]]]", False,
                          "per-edge UNIT quaternion 4-vector parallel to edges; "
                          "None → identity (balanced); (u,v,g) ≡ (v,u,conj(g))"),
                        P("n", "Optional[int]", False,
                          "node count; inferred from edges when None")),
            returns=R("dict",
                      "{'n_cycles', 'class_index': list[int] (SU(2) class), "
                      "'center_parity': list[int] (+1/−1/0), 'cycle_edges': "
                      "list[(u,v)], 'holonomies': list[list[float]] (raw ℍ), "
                      "'balanced': bool}"),
            #  rc347 (`#T985`) LANE: Lk. The ordered product around the cycle
            # reads both lanes; the center_parity read is what survives the
            # mod-2 reduction. MEASURED 400/400 sign, 308/400 index
            reads_lane="both",
            reads_input=("algebra",),
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

        # ────────────────────────────────────────────────────────────
        # srmech.qm.so9 — the so(9)/Spin(9) rung one Cayley-Dickson step
        # above so(8): the 36-dim so(9) adjoint, the 16-dim real spinor
        # Δ₉ (9 octonion-built Clifford Γ), the Spin(8) ⊂ Spin(9)
        # branching 16 = 8_s ⊕ 8_c, and the honest tiered associator ↔
        # Spin(9)-holonomy conjecture at the sedenion 𝕊 rung. Class M
        # (Clifford binders); Class C (chiral split); Class D∘L∘K (conj).
        # ────────────────────────────────────────────────────────────
        ToolEntry(
            name="srmech.qm.so9.so9_adjoint_basis", owner="srmech",
            category="qm.so9",
            summary="The 36 antisymmetric 9×9 so(9) generators E_{pq} (the "
                    "vector / defining rep; dim so(9) = C(9,2) = 36), rank "
                    "exactly 36 (EXACT over ℚ). One rung above so8_adjoint_basis "
                    "(dim 28); so(9) ⊃ so(8) as the E_{pq} with p,q≤7. Class M. "
                    "Baez (2002) §2.",
            parameters=(),
            returns=R("tuple[Mat, ...]", "36 antisymmetric 9×9 spanning so(9)"),
        ),
        ToolEntry(
            name="srmech.qm.so9.spin9_gamma_matrices", owner="srmech",
            category="qm.so9",
            summary="The 9 real symmetric 16×16 Clifford generators Γ_a of the "
                    "16-dim real spinor Δ₉ of Spin(9): Γ_a = [[0, L_{e_a}], "
                    "[L_{e_a}^T, 0]] (a=0..7, from octonion_left_mult) + Γ_8 = "
                    "diag(I_8, −I_8). Satisfy {Γ_a,Γ_b} = 2 δ_{ab} I_16 "
                    "bit-exact (max residual 0; entries in {−1,0,+1}) — the "
                    "construction proves Δ₉ is a 16-dim REAL rep. Class M. "
                    "Baez (2002) §2.3-2.4 + §3.4.",
            parameters=(),
            returns=R("tuple[Mat, ...]",
                      "9 real symmetric 16×16 with {Γ_a,Γ_b}=2δ_ab I"),
        ),
        ToolEntry(
            name="srmech.qm.so9.spin9_spinor_generators", owner="srmech",
            category="qm.so9",
            summary="The 36 spin(9) generators Σ_{ab} = ¼[Γ_a,Γ_b] in the 16-dim "
                    "real spinor Δ₉ (antisymmetric 16×16, dyadic entries). Rank "
                    "exactly 36 (over ℚ) and obey the SAME so(9) structure "
                    "constants as the 9×9 vector rep (bracket residual bit-exact "
                    "0) — Δ₉ is a genuine spin(9) ≅ so(9) rep. Class M. "
                    "Baez (2002) §2.4.",
            parameters=(),
            returns=R("tuple[Mat, ...]",
                      "36 antisymmetric 16×16 spanning spin(9) in Δ₉"),
        ),
        ToolEntry(
            name="srmech.qm.so9.spin8_in_spin9_branching", owner="srmech",
            category="qm.so9",
            summary="The bit-exact Spin(8) ⊂ Spin(9) embedding + the 16 = 8_s ⊕ "
                    "8_c spinor branching. The 28 Σ_{ab} (a,b≤7) are all "
                    "block-diagonal on Δ₉ = O ⊕ O (off-block residual 0), so the "
                    "chirality operator Γ_8 = diag(I,−I) commutes with the whole "
                    "Spin(8) and its projectors ½(I±Γ_8) split Δ₉ into two "
                    "invariant 8-dim half-spinors 8_s (top) / 8_c (bottom), each "
                    "a faithful so(8) (rank 28) with DIFFERENT actions "
                    "(bit-exact distinct-action witness). The 8_s ≇ 8_c "
                    "inequivalence is the recognized rep-theory fact (Baez); the "
                    "block structure + projector commutation + 28+28 ranks are "
                    "this op's own bit-exact computation. Class C ∘ L. "
                    "Baez (2002) §2.4 + §3.4.",
            parameters=(),
            returns=R("dict",
                      "{spinor_rep:{spinor_dim 16, spin9_dim 36, "
                      "clifford_max_residual, spinor_rank 36, "
                      "so9_bracket_max_residual}, branching:{branch (8,8), "
                      "branch_labels (8_s,8_c), chirality_operator, "
                      "off_block_max_residual, projector_commutator_max_residual, "
                      "half_spinor_ranks (28,28), half_spinors_distinct_actions}, "
                      "attestation}"),
        ),
        ToolEntry(
            name="srmech.qm.so9.sedenion_holonomy_conjecture", owner="srmech",
            category="qm.so9",
            summary="HONEST tiered test (verdict PARTIAL): does the octonion "
                    "associator curvature (g₂ = Der O) reappear as a Spin(9) "
                    "holonomy at the sedenion 𝕊 (dim 16) rung? RECOGNIZED: "
                    "dim Δ₉ = 16 = dim_R 𝕊 (shared O⊕O carrier, NOT a Spin(9) "
                    "automorphism action). DERIVED (bit-exact): Der(𝕊) = g₂ "
                    "(dim 14) persists + embeds in spin(9) as the "
                    "triality-diagonal diag(D,D) (all 14 lifts have sedenion-"
                    "Leibniz residual 0); dim(spin(9) ∩ Der(𝕊)) = 14. NULL "
                    "(the honest bound Spin(9) ≠ Aut(𝕊)): only 14 of the 36 "
                    "spin(9) directions preserve 𝕊 multiplication (0/36 "
                    "individual generators are derivations) — the holonomy is "
                    "valued in g₂ (dim 14), NOT Spin(9) (dim 36). FORM not "
                    "identity; never abs(). Class D ∘ L ∘ K. Baez (2002); "
                    "Schafer (1954) Der(𝕊)=g₂.",
            parameters=(),
            returns=R("dict",
                      "{verdict 'PARTIAL', dimensions:{spinor_delta9 16, "
                      "sedenion_real 16, spin9 36, g2 14, der_sedenion 14, "
                      "spin9_cap_der_sedenion 14, aut_sedenion_approx 14}, "
                      "certificate (bit-exact), tiers "
                      "{RECOGNIZED,DERIVED,NULL}, framework_reading, "
                      "attestation}"),
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
                "tool surface. No parameters. "
                "rc339 (#T967) — CAPABILITY, not just size. The report also "
                "carries `classes` (every shipped domain class + its "
                "declaration route), `carriers` (every operand carrier WITH "
                "what it can do), `limits` (the dimensional ceilings, keyed "
                "BY CAPABILITY), and `c_claims` (whether the C symbols the "
                "ops claim are really in the loaded library). READ `limits` "
                "BEFORE ASSUMING A DIMENSION IS USABLE: srmech's carriers "
                "have THREE different ceilings and they are not the same "
                "number. ADDRESS (content-key an element; e_i*e_j = "
                "+/- e_(i XOR j)) is effectively unbounded — verified exact "
                "to dim 64, the build admits 256. COMPOSE (multiply with no "
                "zero divisors) stops at dim 8, Hurwitz. TURN (fold two "
                "turns into one: L_x o L_y == L_(x*y)) stops at dim 4. So "
                "the permissive 256 is an ADDRESSING number and says nothing "
                "about turning: at dim 8 and above only the COMMUTING turns "
                "still compose (measured: at the octonion rung the "
                "turn-composing set and the commuting set are the same 88 "
                "pairs), so non-commuting turn composition is gone there. "
                "`limits['element_types']` gives the same ladder per genome "
                "element_type rung (klein4 / q8 / octonion) with the "
                "exhaustive measurement each verdict was read from."
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
                    "category names], "
                    "'classes': {'total': int, 'names': [sorted class "
                    "names], 'routes': {name: 'toml' | 'python', ...}, "
                    "'toml_total': int}, "
                    "'carriers': {'total': int, 'capabilities': {carrier: "
                    "{'product': str | None, 'address': 'exact' | None, "
                    "'compose': 'full' | 'zero_divisors' | 'unclassified' | "
                    "None, 'turn': 'non_commuting' | 'abelian_only' | "
                    "'unclassified' | None, 'commutative': bool | None, "
                    "'varies_with': 'dim' | 'element_type' | None}, ...}}, "
                    "'limits': {'capabilities': {'address' | 'compose' | "
                    "'turn': {'means': str, 'max_dim': int, "
                    "'beyond_ceiling': str | None, 'bounded_by': str, "
                    "'holds_through': str | None, ...}}, 'element_types': "
                    "[{'code': int, 'name': str, 'algebra': str, 'order': "
                    "int, 'cd_dim': int | None, 'commutative': bool, "
                    "'address': str, 'compose': str, 'turn': str, "
                    "'commutes': [pass, total], 'associates': [pass, "
                    "total], 'turns_compose': [pass, total]}, ...]}, "
                    "'c_claims': {'native': bool, 'checked_ops': int, "
                    "'checked_symbols': int, 'unresolved': {op: [symbol, "
                    "...]}, 'unverifiable': int, 'consistent': bool}}"
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
                "from `srmech.dsl.list_catalog_ops` (the 20-op cascade "
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
                "ops the runner can actually resolve (20 ops: "
                "autocorrelation, best_rational_signed, chiral_dual, "
                "chiral_flip, cyclic_gcd, cyclic_mod_add, cyclic_mod_inv, "
                "cyclic_mod_mul, cyclic_mod_mul_wide, cyclic_mod_pow, "
                "encode_loe_content, kuramoto_step, "
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


def _register_rbs_lm_tools() -> None:
    """Register the §112 / F1008 df-gated aboutness grounding encoder
    (v0.9.0rc303). The RBS-LM substrate's :func:`srmech.rbs_lm.encode_aboutness`
    is the FIRST rbs_lm op promoted to the LLM-facing tool_schema: it turns a
    natural "which op does X?" utterance (or an op's name+summary) into ONE
    structure-bearing Klein-4 aboutness vector, so grounding "ask Siona which
    op" is one call. Declarative ToolEntry data only — no ``srmech.rbs_lm``
    import here (resolved at invoke time), so no import cycle."""
    P = ToolParameter
    R = ToolReturn
    register_tool(
        ToolEntry(
            name="srmech.rbs_lm.encode_aboutness",
            owner="srmech",
            category="rbs_lm",
            summary=(
                "Doc-frequency-GATED ABOUTNESS encoder — encode a natural "
                "utterance (or an op's name+summary) as ONE structure-bearing "
                "Klein-4 aboutness hypervector for grounding \"which srmech op "
                "does this?\" by klein4_similarity. The F1008 recipe (78% top-1 "
                "over the tool_schema, zero training) the plain encode_sentence_l3 "
                "lacks: (1) a doc-frequency aboutness GATE (down-weight tokens "
                "that appear catalog-wide — 'matrix', 'of'), (2) NAME-weighting "
                "(an op's own name tokens count 3x + 2x bigram; F769 identity), "
                "(3) order-aware BIGRAMS (so (klein,4) != (klein,gordon); never a "
                "bag), plus letter-digit tokenization (klein4->klein 4). Tokens "
                "are minted via the STRUCTURE-BEARING klein4_encode_bytes (default "
                "token_mode='byteglyph'), NOT the high-diffusion word-hash "
                "address (F1260: a hash avalanche destroys morphology — a good "
                "ADDRESS but a bad REPRESENTATION), so cat/cats stays "
                "distinguishable from cat/dog. Pass df/n_docs from a corpus to "
                "enable the gate; name= for an op's identity tokens; None df for "
                "the single-word case. composition_of_c (klein4_encode_bytes -> "
                "bind/bundle); numpy-free, no abs()."
            ),
            parameters=(
                P("text", "str", required=True,
                  summary="the utterance / description body (its tokens are "
                          "df-gated)"),
                P("D", "int", required=True,
                  summary="Klein-4 dimension (F1008 used 8192)"),
                P("df", "dict", required=False,
                  summary="token -> doc-frequency table (the aboutness-gate "
                          "corpus stats); None disables the gate"),
                P("n_docs", "int", required=False,
                  summary="document count paired with df (gate threshold = "
                          "int(n_docs * func_frac))"),
                P("name", "str", required=False,
                  summary="an op's IDENTITY string; its tokens are never gated "
                          "and are name-weighted"),
                P("name_weight", "int", required=False,
                  summary="unigram repeat for name tokens (default 3)"),
                P("name_bigram_weight", "int", required=False,
                  summary="bigram repeat for name tokens (default 2)"),
                P("func_frac", "float", required=False,
                  summary="gate threshold as a fraction of n_docs (default 0.35)"),
                P("token_mode", "str", required=False,
                  summary="'byteglyph' (default, structure-bearing) or 'address' "
                          "(F1008 orthogonal dual)"),
            ),
            returns=R("HV", "uint8 in {0,1,2,3}"),
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
_register_rbs_lm_tools()


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
