"""The cascade-catalog EXECUTABLE-CHAIN surface (v0.9.0rc420, `#T1114`).

Until rc420 the 20 ``[cascade]`` descriptors under
``srmech/cascade/catalogs/cascade_catalog/`` were prose records of
hand-rolled ops — none carried an executable step list. rc420 inverts
that: every descriptor now either declares an ADR-0008 §2 (schema v2)
chain under ``[[cascade.chain]]``, or declares itself an explicit LEAF
under ``[cascade.leaf]`` with a machine-readable reason. **Silence is not
a leaf declaration**; the no-third-state rule is gated by
``tests/test_cascade_catalog_executable_rc420.py``, which also EXECUTES
every declared chain against its shipped op (bit-identity over each
descriptor's authored proof cases, including its documented
``[cascade.boundary_cases]``).

Descriptor grammar (per ``[[cascade.chain]]`` entry):

- ``chain_schema_version`` — 2 (the rc420 engine schema; v1 also legal).
- ``variant`` — a short label, default ``"default"``. Most ops carry ONE
  chain; a parameter-dispatched op whose paths are float-order-distinct
  cascades carries one chain PER path (``kuramoto_step``: ``simple`` /
  ``general``) with ``applies_when`` documenting the dispatch condition —
  two cascades are declared as two chains, never papered over with one.
- ``summary`` / ``returns`` — the ADR-0008 chain header fields.
- ``[[cascade.chain.steps]]`` — the executable step list (plain / map /
  fold forms; dotted op addressing).
- ``[[cascade.chain.proof_cases]]`` — concrete input cases, each with a
  ``covers`` label tying it to a ``[cascade.boundary_cases]`` key (or a
  sweep label); the rc420 gate executes every one.

A LEAF declares::

    [cascade.leaf]
    irreducible = true
    reason = "<why nothing lower-level composes it>"
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, List, Optional

from ._catalog import get_descriptor, load_catalog

# The ONE public (registered) callable this module contributes; the
# loader/status helpers are internal plumbing consumed by srmech.introspect
# (the describe() cascade_catalog section), srmech.dsl._tool_surface (the
# per-descriptor status column) and the rc420 gate.
__all__ = [
    "run_cascade_chain",
]


def _chain_entries(desc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The raw ``[[cascade.chain]]`` entries of a loaded descriptor."""
    raw = desc.get("cascade", {}).get("chain", [])
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [e for e in raw if isinstance(e, dict)]
    return []


def _leaf_entry(desc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The ``[cascade.leaf]`` table of a loaded descriptor, or ``None``."""
    leaf = desc.get("cascade", {}).get("leaf")
    return leaf if isinstance(leaf, dict) else None


def descriptor_status(desc: Dict[str, Any]) -> str:
    """One descriptor's rc420 state: ``"executable"`` / ``"leaf"`` /
    ``"undeclared"``.

    ``"executable"`` — carries at least one ``[[cascade.chain]]``.
    ``"leaf"`` — carries ``[cascade.leaf]`` with ``irreducible = true``
    AND a non-empty ``reason`` (a bare marker is not a declaration).
    ``"undeclared"`` — the third state the rc420 gate holds at ZERO.
    """
    if _chain_entries(desc):
        return "executable"
    leaf = _leaf_entry(desc)
    if leaf is not None and leaf.get("irreducible") is True \
            and isinstance(leaf.get("reason"), str) and leaf["reason"].strip():
        return "leaf"
    return "undeclared"


def cascade_catalog_status() -> Dict[str, str]:
    """Per-descriptor status for the WHOLE cascade catalog (built-in +
    registered user tiers) — the ``describe()`` pull surface's source."""
    return {name: descriptor_status(desc)
            for name, desc in load_catalog().items()}


def cascade_chain_specs(op_name: str):
    """Parse every ``[[cascade.chain]]`` entry of ``op_name``'s descriptor
    into engine :class:`srmech.cascade.compose.ChainSpec` objects.

    Returns a list of ``(variant, spec, entry)`` triples in declaration
    order. Raises ``ValueError`` for an unknown op or a chain-less
    descriptor (a LEAF has no chain to parse — that is its point).
    """
    from srmech.cascade import compose as _compose
    desc = get_descriptor(op_name)
    entries = _chain_entries(desc)
    if not entries:
        status = descriptor_status(desc)
        raise ValueError(
            f"cascade op {op_name!r} declares no [[cascade.chain]] "
            f"(status: {status})"
        )
    out = []
    for entry in entries:
        version = entry.get("chain_schema_version", 2)
        if version not in _compose.SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                f"cascade op {op_name!r}: chain_schema_version {version!r} "
                f"not in {_compose.SUPPORTED_SCHEMA_VERSIONS}"
            )
        variant = entry.get("variant", "default")
        chain_dict = {
            "name": f"{op_name}.{variant}",
            "summary": entry.get("summary", desc.get("cascade", {}).get(
                "purpose", op_name)),
            "returns": entry.get("returns", ""),
            "steps": entry.get("steps", []),
        }
        spec = _compose.parse_chain_spec(chain_dict)
        out.append((variant, spec, entry))
    return out


def run_cascade_chain(
    op_name: str,
    inputs: Optional[Dict[str, Any]] = None,
    *,
    variant: Optional[str] = None,
    **kw: Any,
) -> Any:
    """Run a cascade-catalog descriptor's DECLARED chain (v0.9.0rc420).

    The executable half of the `#T1114` catalog inversion: the descriptor
    is no longer a prose record — this parses its ``[[cascade.chain]]``
    step list through the ADR-0008 §2 engine
    (:mod:`srmech.cascade.compose`, schema v2) and runs it. Every shipped
    chain is proven bit-identical to its shipped op by
    ``tests/test_cascade_catalog_executable_rc420.py``, so this is the
    op's OWN cascade run declaratively, not a re-implementation.

    Args:
        op_name: the descriptor name (``[cascade].name``).
        inputs: the chain's ``@input.*`` bindings (dict form).
        variant: which declared chain to run when the descriptor carries
            more than one (``kuramoto_step``: ``"simple"`` /
            ``"general"``). Default: the descriptor's single chain, or an
            error naming the variants when several exist.
        **kw: additional ``@input.*`` bindings (merged over ``inputs``).

    Returns:
        The chain's final-step output.
    """
    from srmech.cascade import compose as _compose
    specs = cascade_chain_specs(op_name)
    if variant is None:
        if len(specs) > 1:
            raise ValueError(
                f"cascade op {op_name!r} declares {len(specs)} chain "
                f"variants ({[v for v, _s, _e in specs]}); pass variant="
            )
        _v, spec, _entry = specs[0]
    else:
        matches = [s for v, s, _e in specs if v == variant]
        if not matches:
            raise ValueError(
                f"cascade op {op_name!r} has no chain variant {variant!r}; "
                f"declared: {[v for v, _s, _e in specs]}"
            )
        spec = matches[0]
    entry = next((e for v, s, e in specs if s is spec), None)
    bound = chain_input_defaults(entry)
    bound.update(inputs or {})
    bound.update(kw)
    return _compose.run_chain(spec, inputs=bound)


def chain_input_defaults(entry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The declared default ``@input.*`` bindings for one chain entry.

    rc452 (`#T1171`). A chain may `bind` inputs that not every proof case
    supplies — ``kuramoto_step``/``general`` binds ``adjacency``, ``alpha``,
    ``pin_anchor`` and ``pin_strength``, and only its ``pinning`` case supplies
    all four. ``@input.X`` raises on an absent X, so before this the variant was
    not executable from shipped configuration at all: the four values existed
    only as a ``CASE_DEFAULTS`` dict inside two Python TEST files. That is a
    descriptor defect, not a fact about the op — `#T1114`'s whole claim is that
    the TOML is the SSoT — so the defaults moved into the descriptor and this is
    the reader BOTH projections key on.

    Two declarations, because there are two genuinely different cases:

    * ``input_defaults`` — a table of values TOML can spell, merged UNDER
      anything the caller passes.
    * ``optional_inputs`` — names whose default is ABSENT (Python ``None``).
      TOML has no null literal, which is precisely why these leaked into Python
      in the first place; declaring the NAMES lets the descriptor say "absent"
      without inventing a sentinel value that every reader would have to decode.

    Returns a fresh dict; callers merge their own inputs OVER it.
    """
    if not isinstance(entry, Mapping):
        return {}
    out: Dict[str, Any] = {}
    for name in entry.get("optional_inputs", ()) or ():
        if not isinstance(name, str):
            raise ValueError(
                f"optional_inputs must be a list of input NAMES; got "
                f"{type(name).__name__}"
            )
        out[name] = None
    declared = entry.get("input_defaults", {}) or {}
    if not isinstance(declared, Mapping):
        raise ValueError(
            f"input_defaults must be a table; got {type(declared).__name__}"
        )
    out.update(declared)
    return out
