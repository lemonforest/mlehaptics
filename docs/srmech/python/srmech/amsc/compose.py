"""Operator-chain composition engine (ADR-0002 Phase 2 / v0.4.1rc5).

Implements the schema v1 candidate specified by
``docs/srmech/adr/0002-phase-1-operator-chain-schema.md``. A
"composition engine" is the runtime that takes a parsed TOML
``[[catalog.operator_chain]]`` declaration, validates it, resolves
the 4-namespace reference DSL, and executes the linear pipeline of
class-op calls.

v1 scope per Phase 1 §11 — linear pipeline only. No DAG, no
branching, no chain-level iteration. Per
``[[feedback_no_mvp_framing]]`` this v1 is a full-coverage ship of
the schema's v1 surface; open questions (branching / iteration /
cross-source reduction) are explicitly Phase 2-v2 scope and remain
documented in the schema doc §11.

Architecture
------------

The engine is class-registry-driven. The default registry maps each
single-letter class ID A–N to its ``srmech.amsc.<module>`` (lowercase
class home). Each step's ``class`` + ``op`` resolves to
``getattr(class_module, op)``; the engine calls it with the resolved
args dict.

Reference DSL (Phase 1 §3.7):

- ``@row.<dotted.field>`` — current MPR row's ``data`` block.
- ``@input.<name>`` — runtime parameter passed to :func:`run_chain`.
- ``@step[N].output`` — output of the zero-indexed Nth step.
- ``@catalog.<row_key>.<col>`` — cross-catalog lookup via
  ``srmech.amsc.catalog.get_attested_dataset``.

Error policy (Phase 1 §3.5):

- ``"raise"`` (default) — exceptions propagate.
- ``"warn_return_none"`` — log warning + return ``None`` for that step.
- ``"skip"`` — only valid in batch contexts; not implemented for
  single-chain calls (raises NotImplementedError).

Per-step ``on_error`` overrides the chain-level policy for that step.

Validation discipline (Phase 1 §7):

- Class identifiers are A–N.
- Module resolution: ``srmech.amsc.<module>`` imports cleanly.
- Operation existence: ``getattr(module, op)`` exists and is
  callable.
- Reference syntax: every ``@``-prefixed string matches the grammar.
- Step-reference bounds: every ``@step[N]`` has ``N <
  current_step_index``.

Failures raise :class:`ChainSpecError` at activation; no chain
executes with an invalid declaration.

References
----------

- ``docs/srmech/adr/0002-catalog-as-computation.md`` — parent ADR.
- ``docs/srmech/adr/0002-phase-1-operator-chain-schema.md`` — schema v1.
- ``docs/srmech/notes/adr_0002_phase_1_dsl_design_2026-05-16.md`` —
  Phase 1 design report.
- ``[[feedback_no_privileged_primitive_classes]]`` — class-promotion
  discipline.
- ``[[feedback_science_is_ssot_not_project]]`` — canonical-physics
  SSoT citations on each Class L op.
"""

from __future__ import annotations

import importlib
import logging
import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# Composition engine schema version this module implements.
ENGINE_SCHEMA_VERSION: int = 1

# Class → module mapping (Phase 1 §5).
DEFAULT_CLASS_REGISTRY: Dict[str, str] = {
    "A": "srmech.amsc.format",
    "B": "srmech.amsc.tlv",
    "C": "srmech.amsc.format",
    "D": "srmech.amsc.dispatch",
    "E": "srmech.amsc.catalog",
    "F": "srmech.amsc.template",
    "G": "srmech.amsc.search",
    "H": "srmech.amsc._native",
    "I": "srmech.amsc.cyclic",
    "J": "srmech.amsc.primes",
    "K": "srmech.amsc.kepler",
    "L": "srmech.amsc.laplacian",
    "M": "srmech.amsc.hdc",
    "N": "srmech.amsc.rational",
}

# Legal error-policy values.
LEGAL_ERROR_POLICIES: Tuple[str, ...] = ("raise", "warn_return_none", "skip")

# Reference DSL regex: ``@<namespace>.<path>``. `path` allows dotted
# fields and optional `[N]` indexers.
_REFERENCE_PATTERN = re.compile(
    r"^@(row|input|step|catalog)((?:\.[A-Za-z_][A-Za-z0-9_]*|\[\d+\])+)$"
)


class ChainSpecError(ValueError):
    """Raised when an operator-chain declaration fails validation."""


@dataclass(frozen=True)
class StepSpec:
    """One step in an operator chain.

    Attributes mirror the TOML schema:
      - ``class_id``: single letter A–N (TOML key is ``class``).
      - ``op``: operation name; must exist on ``DEFAULT_CLASS_REGISTRY[class_id]``.
      - ``args``: free-form dict; values are literals or references.
      - ``on_error``: optional override of chain-level policy.
    """

    class_id: str
    op: str
    args: Dict[str, Any]
    on_error: Optional[str] = None


@dataclass(frozen=True)
class ChainSpec:
    """One operator chain declared in a catalog descriptor.

    Mirrors the TOML ``[[catalog.operator_chain]]`` schema:
      - ``name``: chain name (snake_case identifier).
      - ``summary``: human-readable description.
      - ``returns``: typed string ``"<type>  # <comment>"``.
      - ``on_error``: chain-level error policy (default ``"raise"``).
      - ``steps``: list of :class:`StepSpec` in execution order.
    """

    name: str
    summary: str
    returns: str
    steps: Tuple[StepSpec, ...]
    on_error: str = "raise"


def _validate_reference(
    ref: str, step_index: int
) -> None:
    """Validate a single reference string against the DSL grammar.

    Raises :class:`ChainSpecError` on grammar failure or out-of-bounds
    ``@step[N]`` reference (N >= current step index).
    """
    m = _REFERENCE_PATTERN.match(ref)
    if not m:
        raise ChainSpecError(
            f"step[{step_index}]: reference {ref!r} does not match the "
            f"DSL grammar; expected @<namespace>.<path>"
        )
    namespace = m.group(1)
    if namespace == "step":
        # Extract the leading [N] index.
        idx_match = re.match(r"\[(\d+)\]", m.group(2))
        if idx_match is None:
            raise ChainSpecError(
                f"step[{step_index}]: @step reference {ref!r} must "
                f"start with [N] indexer"
            )
        target_idx = int(idx_match.group(1))
        if target_idx >= step_index:
            raise ChainSpecError(
                f"step[{step_index}]: @step[{target_idx}] references a "
                f"step that has not yet executed (must be < {step_index})"
            )


def _walk_args(args: Any, fn: Callable[[str], None]) -> None:
    """Recursively walk an args structure invoking `fn` on every
    string that begins with ``@`` (a reference). Literals are skipped.
    """
    if isinstance(args, str):
        if args.startswith("@"):
            fn(args)
        return
    if isinstance(args, dict):
        for v in args.values():
            _walk_args(v, fn)
        return
    if isinstance(args, (list, tuple)):
        for v in args:
            _walk_args(v, fn)
        return
    # Scalars + None: nothing to walk.


def parse_chain_spec(chain_dict: Dict[str, Any]) -> ChainSpec:
    """Parse and validate one ``[[catalog.operator_chain]]`` entry.

    Parameters
    ----------
    chain_dict
        Dict parsed from TOML (single chain entry, with ``steps``
        as a list of ``[[catalog.operator_chain.steps]]`` entries).

    Returns
    -------
    ChainSpec

    Raises
    ------
    ChainSpecError
        On missing keys, unknown class identifiers, malformed
        reference syntax, or out-of-bounds step references.
    """
    if not isinstance(chain_dict, dict):
        raise ChainSpecError(
            f"chain entry must be a dict; got {type(chain_dict).__name__}"
        )
    for required in ("name", "summary", "returns", "steps"):
        if required not in chain_dict:
            raise ChainSpecError(
                f"chain entry missing required key {required!r}"
            )
    name = str(chain_dict["name"])
    summary = str(chain_dict["summary"])
    returns = str(chain_dict["returns"])
    on_error = str(chain_dict.get("on_error", "raise"))
    if on_error not in LEGAL_ERROR_POLICIES:
        raise ChainSpecError(
            f"chain {name!r}: illegal on_error {on_error!r}; "
            f"legal: {LEGAL_ERROR_POLICIES}"
        )
    raw_steps = chain_dict["steps"]
    if not isinstance(raw_steps, list) or len(raw_steps) == 0:
        raise ChainSpecError(
            f"chain {name!r}: steps must be non-empty list"
        )
    steps: List[StepSpec] = []
    for idx, raw_step in enumerate(raw_steps):
        steps.append(_parse_step(name, idx, raw_step))
    return ChainSpec(
        name=name, summary=summary, returns=returns,
        steps=tuple(steps), on_error=on_error,
    )


def _parse_step(
    chain_name: str, step_idx: int, raw_step: Any
) -> StepSpec:
    """Parse + validate one step dict from a chain's ``steps`` list."""
    if not isinstance(raw_step, dict):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: must be dict; "
            f"got {type(raw_step).__name__}"
        )
    for required in ("class", "op", "args"):
        if required not in raw_step:
            raise ChainSpecError(
                f"chain {chain_name!r} step[{step_idx}]: missing "
                f"required key {required!r}"
            )
    class_id = str(raw_step["class"])
    if class_id not in DEFAULT_CLASS_REGISTRY:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: unknown class "
            f"{class_id!r}; legal: {sorted(DEFAULT_CLASS_REGISTRY)}"
        )
    op = str(raw_step["op"])
    args = raw_step["args"]
    if not isinstance(args, dict):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: args must be "
            f"dict; got {type(args).__name__}"
        )
    step_on_error = raw_step.get("on_error")
    if step_on_error is not None and step_on_error not in LEGAL_ERROR_POLICIES:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: illegal on_error "
            f"{step_on_error!r}; legal: {LEGAL_ERROR_POLICIES}"
        )
    # Validate reference grammar + step-reference bounds.
    _walk_args(args, lambda r: _validate_reference(r, step_idx))
    return StepSpec(class_id=class_id, op=op, args=dict(args),
                    on_error=step_on_error)


def _resolve_dotted_path(obj: Any, path: str) -> Any:
    """Walk a dotted path (with optional ``[N]`` indexers) into ``obj``.

    ``path`` is the post-namespace portion of a reference, leading
    with ``.<key>`` or ``[N]``. Empty path returns ``obj`` unchanged.
    """
    remaining = path
    current = obj
    while remaining:
        # Match either .<key> or [N].
        m = re.match(r"^\.([A-Za-z_][A-Za-z0-9_]*)", remaining)
        if m:
            key = m.group(1)
            if isinstance(current, dict):
                if key not in current:
                    raise KeyError(f"path element .{key} not found")
                current = current[key]
            else:
                current = getattr(current, key)
            remaining = remaining[m.end():]
            continue
        m = re.match(r"^\[(\d+)\]", remaining)
        if m:
            idx = int(m.group(1))
            current = current[idx]
            remaining = remaining[m.end():]
            continue
        raise ValueError(f"malformed path remainder {remaining!r}")
    return current


def _resolve_reference(
    ref: str,
    *,
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
    step_outputs: List[Any],
) -> Any:
    """Resolve one reference string at runtime."""
    m = _REFERENCE_PATTERN.match(ref)
    if not m:
        raise ValueError(f"reference {ref!r} does not match DSL")
    namespace = m.group(1)
    path = m.group(2)
    if namespace == "row":
        if row is None:
            raise RuntimeError(
                f"reference {ref!r} requires a row binding but row=None"
            )
        return _resolve_dotted_path(row, path)
    if namespace == "input":
        return _resolve_dotted_path(inputs, path)
    if namespace == "step":
        idx_match = re.match(r"^\[(\d+)\](.*)", path)
        if idx_match is None:
            raise ValueError(f"@step reference {ref!r} missing [N]")
        target_idx = int(idx_match.group(1))
        if target_idx >= len(step_outputs):
            raise RuntimeError(
                f"reference {ref!r}: step[{target_idx}] has not "
                f"executed yet (have {len(step_outputs)} outputs)"
            )
        remainder = idx_match.group(2)
        # ``.output`` resolves to the step's return value itself;
        # ``.output.<field>`` then walks into that value. Other
        # accessors (e.g. ``.V`` for a named-tuple-style output) walk
        # via getattr / item access normally.
        if remainder.startswith(".output"):
            remainder = remainder[len(".output"):]
        return _resolve_dotted_path(step_outputs[target_idx], remainder)
    if namespace == "catalog":
        return _resolve_catalog_reference(path)
    raise ValueError(f"unknown namespace {namespace!r}")


def _resolve_catalog_reference(path: str) -> Any:
    """Resolve ``@catalog.<row_key>.<col>`` lazily via catalog bridge.

    v1 implementation: imports ``srmech.amsc.catalog`` and walks
    every registered source for a row whose ``data.<row_key>`` field
    matches ``<row_key>``. This is the simplest defensible semantics
    for the schema's v1 cross-catalog reference; richer search
    semantics are Phase 2 open question 11.4.
    """
    # First path component is the row_key, remainder is the field path.
    m = re.match(r"^\.([A-Za-z_][A-Za-z0-9_]*)(.*)", path)
    if m is None:
        raise ValueError(f"@catalog path {path!r} malformed")
    row_key = m.group(1)
    field_path = m.group(2)
    from . import catalog as _catalog
    sources = _catalog.list_attested_sources().get("sources", [])
    for source in sources:
        ds = _catalog.get_attested_dataset(source["key"])
        if not ds.get("ok"):
            continue
        for row in ds.get("rows", []):
            data = row.get("data", {})
            if data.get(row_key) is not None or row_key in data:
                target = data.get(row_key, data)
                if field_path:
                    return _resolve_dotted_path(target, field_path)
                return target
    raise RuntimeError(
        f"@catalog reference: row_key {row_key!r} not found in any "
        f"registered catalog"
    )


def _resolve_args(
    args: Any,
    *,
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
    step_outputs: List[Any],
) -> Any:
    """Recursively resolve all references in an args structure."""
    if isinstance(args, str):
        if args.startswith("@"):
            return _resolve_reference(
                args, row=row, inputs=inputs, step_outputs=step_outputs,
            )
        return args
    if isinstance(args, dict):
        return {
            k: _resolve_args(v, row=row, inputs=inputs,
                             step_outputs=step_outputs)
            for k, v in args.items()
        }
    if isinstance(args, list):
        return [
            _resolve_args(v, row=row, inputs=inputs,
                          step_outputs=step_outputs)
            for v in args
        ]
    if isinstance(args, tuple):
        return tuple(
            _resolve_args(v, row=row, inputs=inputs,
                          step_outputs=step_outputs)
            for v in args
        )
    return args


def resolve_chain(
    spec: ChainSpec,
    registry: Optional[Dict[str, str]] = None,
) -> Callable[..., Any]:
    """Resolve a chain to a callable.

    Validates that each step's ``op`` exists on the registered class
    module; raises :class:`ChainSpecError` on missing op.

    Returns a callable with signature
    ``f(row: Optional[dict] = None, **inputs) -> Any`` that executes
    the chain.
    """
    reg = registry or DEFAULT_CLASS_REGISTRY
    resolved_ops: List[Tuple[StepSpec, Callable[..., Any]]] = []
    for idx, step in enumerate(spec.steps):
        module_name = reg.get(step.class_id)
        if module_name is None:
            raise ChainSpecError(
                f"chain {spec.name!r} step[{idx}]: class "
                f"{step.class_id!r} has no registered module"
            )
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise ChainSpecError(
                f"chain {spec.name!r} step[{idx}]: module "
                f"{module_name!r} not importable: {exc}"
            ) from exc
        op_callable = getattr(module, step.op, None)
        if op_callable is None or not callable(op_callable):
            raise ChainSpecError(
                f"chain {spec.name!r} step[{idx}]: op {step.op!r} "
                f"not found on {module_name!r}"
            )
        resolved_ops.append((step, op_callable))

    def _run(row: Optional[Dict[str, Any]] = None,
             **inputs: Any) -> Any:
        return _execute_resolved(spec, resolved_ops, row, inputs)

    _run.__name__ = f"run_{spec.name}"
    _run.__doc__ = spec.summary
    return _run


def _execute_resolved(
    spec: ChainSpec,
    resolved_ops: List[Tuple[StepSpec, Callable[..., Any]]],
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
) -> Any:
    """Execute a resolved chain. Output of the final step is returned."""
    step_outputs: List[Any] = []
    final_output: Any = None
    for idx, (step, op_callable) in enumerate(resolved_ops):
        policy = step.on_error or spec.on_error
        if policy == "skip":
            raise NotImplementedError(
                "on_error='skip' is only valid in batch-execution "
                "contexts; not supported by run_chain()"
            )
        try:
            args = _resolve_args(step.args, row=row, inputs=inputs,
                                 step_outputs=step_outputs)
            result = op_callable(**args)
        except Exception as exc:  # pragma: no cover (policy branches)
            if policy == "warn_return_none":
                warnings.warn(
                    f"chain {spec.name!r} step[{idx}] "
                    f"({step.class_id}.{step.op}) failed: {exc!r}; "
                    f"returning None per on_error policy",
                    RuntimeWarning, stacklevel=2,
                )
                result = None
            else:
                raise
        step_outputs.append(result)
        final_output = result
    return final_output


def run_chain(
    spec: ChainSpec,
    *,
    row: Optional[Dict[str, Any]] = None,
    inputs: Optional[Dict[str, Any]] = None,
    registry: Optional[Dict[str, str]] = None,
) -> Any:
    """Top-level executor: parse + resolve + run a chain.

    Convenience wrapper over :func:`resolve_chain` that builds the
    callable and invokes it. Use :func:`resolve_chain` directly when
    the same chain will be invoked many times (avoids re-importing
    class modules per call).
    """
    runner = resolve_chain(spec, registry)
    return runner(row=row, **(inputs or {}))


def parse_catalog_chains(
    toml_dict: Dict[str, Any],
) -> List[ChainSpec]:
    """Parse all chains in a catalog descriptor's TOML dict.

    Returns a list of :class:`ChainSpec` (possibly empty) from
    ``toml_dict["catalog"]["operator_chain"]``. Validates that the
    catalog declares ``chain_schema_version = 1`` when any chain is
    present.
    """
    catalog = toml_dict.get("catalog", {})
    chains_raw = catalog.get("operator_chain", [])
    if not chains_raw:
        return []
    schema_version = catalog.get("chain_schema_version")
    if schema_version is None:
        raise ChainSpecError(
            "catalog declares operator_chain entries but is missing "
            "[catalog].chain_schema_version"
        )
    if schema_version != ENGINE_SCHEMA_VERSION:
        raise ChainSpecError(
            f"catalog chain_schema_version = {schema_version!r}; this "
            f"engine implements v{ENGINE_SCHEMA_VERSION} only"
        )
    return [parse_chain_spec(c) for c in chains_raw]


__all__ = [
    "ChainSpec",
    "ChainSpecError",
    "DEFAULT_CLASS_REGISTRY",
    "ENGINE_SCHEMA_VERSION",
    "LEGAL_ERROR_POLICIES",
    "StepSpec",
    "parse_catalog_chains",
    "parse_chain_spec",
    "resolve_chain",
    "run_chain",
]
