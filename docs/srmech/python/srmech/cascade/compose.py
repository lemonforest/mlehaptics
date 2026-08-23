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
import inspect
import json
import logging
import re
import warnings
from collections.abc import Mapping
from functools import lru_cache
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from srmech import _json as _srmech_json


# Composition engine schema version this module implements.
#
# v0.9.0rc420 (`#T1114`, ADR-0008 Amendment A): the engine implements
# schema v2, a STRICT SUPERSET of v1 — every v1 chain is a valid v2 chain
# unchanged, so v1 catalogs keep working (SUPPORTED_SCHEMA_VERSIONS).
# v2 adds, each closing a census-measured blocker:
#
#   * DOTTED op names (BLK-REGMAP) — a step's ``op`` may be a fully-qualified
#     ``"srmech.cascade.leaves.seq_len"``; ``class`` stays required and
#     becomes CLASSIFICATION, not addressing (the letter->module registry
#     remains the resolution for bare names). Precedent: the srmech.dsl
#     dotted-op resolver (``_catalog.py`` §17 U2).
#   * the MAP step form (BLK-ITER-INDEXED) — ``{map_over, index?, bind?,
#     body}``: a general indexed map ``out[k] = body(k, ...)`` with
#     ``n = len(resolve(map_over))`` FIXED AT ENTRY (an unsized iterable is
#     rejected — the totality pin; the map is data-SIZED, never
#     data-DEPENDENT, so no predicate ever decides continuation).
#   * the FOLD step form (BLK-ITER-COMPOSE) — ``{fold_class, fold_op,
#     fold_init, over, fold_args?}``: the DSL surface's
#     catamorphism-with-seed, ported to this surface. ``fold_args`` is the
#     rc420 fix for the measured fold-contract defect: a binary POSITIONAL
#     fold could not bind a kw-only atom (``reorient(value, *,
#     orientation=)`` raised TypeError); naming the two argument slots
#     binds it.
#   * the ``@idx.<name>`` / ``@bind.<name>`` reference forms — required
#     because the v1 grammar hard-codes namespaces ``row|input|step|catalog``
#     and its ``[N]`` indexer is literal-only. SCOPING DECISION (stated,
#     per the rung-4 measurement): a map body's ``@step[N]`` is BODY-LOCAL
#     (a body is a chain in miniature — the same static bounds check applies
#     recursively), and outer data flows in ONLY through ``@bind`` /
#     ``@idx``, which makes every cross-boundary dependency EXPLICIT at the
#     map boundary — the same explicit-only rule §3.2 already imposes on
#     step-to-step flow (no magic implicit piping).
#   * the ``@op.<dotted.path>`` reference form (BLK-HIGHER-ORDER) — a
#     descriptor can name an op AS A VALUE (``chiral_dual`` /
#     ``parallel_sector_dispatch`` take op-valued parameters). Measured at
#     rung 3: a runtime callable already THREADS fine through ``@input``;
#     the gap was descriptor-level naming only.
ENGINE_SCHEMA_VERSION: int = 2

#: Schema versions this engine accepts — v2 is a superset of v1, so both
#: parse; a catalog declaring anything else is rejected at activation.
SUPPORTED_SCHEMA_VERSIONS: Tuple[int, ...] = (1, 2)

# Class → module mapping (Phase 1 §5).
DEFAULT_CLASS_REGISTRY: Dict[str, str] = {
    "A": "srmech.amsc.format",
    "B": "srmech.math.tlv",
    "C": "srmech.amsc.format",
    "D": "srmech.math.dispatch",
    "E": "srmech.amsc.catalog",
    "F": "srmech.math.template",
    "G": "srmech.math.search",
    "H": "srmech._native",
    "I": "srmech.math.cyclic",
    "J": "srmech.math.primes",
    "K": "srmech.math.kepler",
    "L": "srmech.math.laplacian",
    "M": "srmech.math.hdc",
    "N": "srmech.math.rational",
}

# Legal error-policy values.
LEGAL_ERROR_POLICIES: Tuple[str, ...] = ("raise", "warn_return_none", "skip")

# Reference DSL regex: ``@<namespace>.<path>``. `path` allows dotted
# fields and optional `[N]` indexers. v2 (rc420) adds three namespaces:
# ``idx`` (an enclosing map's index), ``bind`` (a map-entry-resolved
# closure value) and ``op`` (a dotted op-as-value reference).
_REFERENCE_PATTERN = re.compile(
    r"^@(row|input|step|catalog|idx|bind|op)"
    r"((?:\.[A-Za-z_][A-Za-z0-9_]*|\[\d+\])+)$"
)

#: The v2-only reference namespaces — a v1 chain never carries these.
_V2_NAMESPACES = ("idx", "bind", "op")

#: The v2-only step-form discriminator keys (map / fold). Any of these on a
#: step makes the chain a v2 chain; they are mutually exclusive with the
#: plain ``class``+``op``+``args`` form AND with each other.
_MAP_KEYS = ("map_over", "index", "bind", "body")
_FOLD_KEYS = ("fold_class", "fold_op", "fold_init", "over", "fold_args")


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
class MapStepSpec:
    """One INDEXED-MAP step (schema v2, rc420 — the `#T1114`
    BLK-ITER-INDEXED closure).

    ``out = [run(body) for k in range(len(resolve(map_over)))]`` with the
    reference form ``@idx.<index>`` bound to ``k`` inside the body and
    ``@bind.<name>`` bound to the entry-resolved ``bind`` values. Maps NEST;
    inner bodies see outer indices and binds (layered environments).

    TOTALITY (the invariant this form must protect, stated where it is
    declared): ``n = len(seq)`` is fixed BEFORE the first body run (an
    unsized iterable is rejected at run time); the body is a finite,
    descriptor-static step list; nesting depth is descriptor-static. So the
    step performs exactly a descriptor-static number of op calls per input
    element — total iff every leaf op is total, the SAME totality class the
    shipped DSL fold/reduce already run under (``make_fold_stage`` iterates
    ``for elem in input_seq`` over a runtime-length input). The map is
    data-SIZED, never data-DEPENDENT: no predicate decides continuation.

    Attributes:
      - ``map_over``: reference resolving to a SIZED sequence.
      - ``index``: the ``@idx`` name the body sees (default ``"k"``).
      - ``bind``: name → reference/literal, resolved ONCE at map entry.
      - ``body``: the body step tuple (BODY-LOCAL ``@step[N]`` numbering).
    """

    map_over: str
    index: str
    bind: Dict[str, Any]
    body: Tuple[Any, ...]
    on_error: Optional[str] = None


@dataclass(frozen=True)
class FoldStepSpec:
    """One FOLD step (schema v2, rc420 — the `#T1114` BLK-ITER-COMPOSE
    port of the DSL surface's catamorphism-with-seed).

    ``acc = fold_init; for elem in resolve(over): acc = op(acc, elem)`` —
    the exact ``make_fold_stage`` iteration contract. ``fold_args``, when
    given, is a 2-tuple of keyword names ``(acc_name, elem_name)`` so a
    kw-only binary op binds (the rc420 fold-contract fix: the shipped
    ``reorient(value, *, orientation=)`` raised TypeError under the
    positional fold call).

    Attributes:
      - ``fold_class``: single letter A–N (classification).
      - ``fold_op``: op name (bare → letter registry; dotted → direct).
      - ``fold_init``: the seed (literal or reference).
      - ``over``: reference resolving to the folded sequence.
      - ``fold_args``: optional ``(acc_kwarg, elem_kwarg)`` name pair.
    """

    fold_class: str
    fold_op: str
    fold_init: Any
    over: str
    fold_args: Optional[Tuple[str, str]] = None
    on_error: Optional[str] = None


@dataclass(frozen=True)
class ChainSpec:
    """One operator chain declared in a catalog descriptor.

    Mirrors the TOML ``[[catalog.operator_chain]]`` schema:
      - ``name``: chain name (snake_case identifier).
      - ``summary``: human-readable description.
      - ``returns``: typed string ``"<type>  # <comment>"``.
      - ``on_error``: chain-level error policy (default ``"raise"``).
      - ``steps``: list of :class:`StepSpec` (v1) — plus, in a v2 chain,
        :class:`MapStepSpec` / :class:`FoldStepSpec` — in execution order.
    """

    name: str
    summary: str
    returns: str
    steps: Tuple[Any, ...]
    on_error: str = "raise"


def _validate_reference(
    ref: str, step_index: int,
    idx_names: frozenset = frozenset(),
    bind_names: frozenset = frozenset(),
) -> None:
    """Validate a single reference string against the DSL grammar.

    Raises :class:`ChainSpecError` on grammar failure, an out-of-bounds
    ``@step[N]`` reference (N >= current step index), or a v2 scoped
    reference (``@idx`` / ``@bind``) whose name no enclosing map binds —
    the static half of the rc420 scoping decision (a body-local grammar
    is only honest if an unbound name fails at ACTIVATION, not mid-run).
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
    elif namespace == "idx":
        name_match = re.match(r"^\.([A-Za-z_][A-Za-z0-9_]*)$", m.group(2))
        if name_match is None:
            raise ChainSpecError(
                f"step[{step_index}]: @idx reference {ref!r} must be a "
                f"single bare index name (@idx.<name>)"
            )
        if name_match.group(1) not in idx_names:
            raise ChainSpecError(
                f"step[{step_index}]: @idx.{name_match.group(1)}: no "
                f"enclosing map binds index {name_match.group(1)!r} "
                f"(bound here: {sorted(idx_names) or 'none'})"
            )
    elif namespace == "bind":
        name_match = re.match(r"^\.([A-Za-z_][A-Za-z0-9_]*)", m.group(2))
        if name_match is None or name_match.group(1) not in bind_names:
            got = name_match.group(1) if name_match else m.group(2)
            raise ChainSpecError(
                f"step[{step_index}]: @bind.{got}: no enclosing map binds "
                f"{got!r} (bound here: {sorted(bind_names) or 'none'})"
            )
    elif namespace == "op":
        if "[" in m.group(2) or m.group(2).count(".") < 2:
            raise ChainSpecError(
                f"step[{step_index}]: @op reference {ref!r} must be a "
                f"dotted module path with at least two components "
                f"(@op.<module...>.<callable>) and no [N] indexers"
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


# ──────────────────────────────────────────────────────────────────────
# Native PARSE + VALIDATE dispatch (0.9.0rc173; the ORCHESTRATION→C spine,
# batch 3). ``srmech_chain_spec_parse`` / ``srmech_chain_catalog_parse``
# validate a chain block (JSON) and return the normalized spec as canonical
# JSON; the Python caller re-attaches each step's ``args`` from the ORIGINAL
# dict so arg object identity/type is preserved. Any validation failure or
# non-JSON input → the C peer returns non-OK → the COMPLETE pure path runs
# (which raises the specific ``ChainSpecError``), never a rescue. Only the
# PARSE half is in C: resolve_chain / run_chain invoke ARBITRARY srmech ops
# over the live Python object graph — scoped rc174 (see srmech_compose.c).
# ──────────────────────────────────────────────────────────────────────


def _compose_lib(*symbols: str):
    """Return the native LIB iff HAS_NATIVE and every named rc173 symbol is
    bound (a stale ABI-3 lib missing them → ``None`` → the pure path)."""
    from .. import _native
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    lib = _native.LIB
    for sym in symbols:
        if not hasattr(lib, sym):
            return None
    return lib


def _chain_spec_from_native(
    chain_dict: Dict[str, Any], native: Dict[str, Any]
) -> ChainSpec:
    """Rebuild a :class:`ChainSpec` from the C-validated normalized dict,
    taking each step's ``args`` from the ORIGINAL ``chain_dict`` (so the arg
    object identity + type are byte-identical to the pure path's
    ``dict(raw_step["args"])``)."""
    raw_steps = chain_dict["steps"]
    steps = [
        StepSpec(
            class_id=s["class_id"], op=s["op"],
            args=dict(raw_steps[i]["args"]), on_error=s["on_error"],
        )
        for i, s in enumerate(native["steps"])
    ]
    return ChainSpec(
        name=native["name"], summary=native["summary"],
        returns=native["returns"], steps=tuple(steps),
        on_error=native["on_error"],
    )


def _call_compose_native(lib, arena_sym: str, call_sym: str,
                         payload: bytes) -> Optional[str]:
    """Run one caller-arena compose peer (arena-size → call → canonical JSON
    string) or ``None`` on any non-OK status. Shared by both parse ops."""
    import ctypes
    from .. import _native
    ws_bytes = int(getattr(lib, arena_sym)(len(payload)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = 2 * len(payload) + 8192
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = getattr(lib, call_sym)(
        payload, len(payload), ws, ws_bytes, out, out_cap,
        ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        return None
    return out.raw[:out_len.value].decode("utf-8")


def _chain_has_v2_forms(chain_dict: Any) -> bool:
    """True iff any step (recursively) carries a v2 discriminator key or a
    v2 reference namespace — the PYTHON-FIRST sequencing guard (rc420).

    The C parse peer (``srmech_chain_spec_parse``) is a REQUIRED-KEYS check,
    not a closed-key-set check: a step carrying BOTH a valid v1 skeleton and
    v2 keys would parse in C with the v2 keys SILENTLY DISCARDED — a chain
    that runs as if the map form were never written, the exact ADR-0009
    parity break the native-then-pure structure would otherwise hide. So any
    v2 content routes the WHOLE chain to the pure path, whose validator
    enforces the mutual-exclusion rule loudly. Measured shape: C-accepts /
    Python-rejects is the dangerous split; Python-first is safe (C returns
    BAD_INPUT → pure handles).
    """
    if not isinstance(chain_dict, dict):
        return False
    steps = chain_dict.get("steps")
    if not isinstance(steps, list):
        return False

    found = False

    def _scan_refs(a: Any) -> None:
        nonlocal found
        if found:
            return
        if isinstance(a, str) and a.startswith("@"):
            m = _REFERENCE_PATTERN.match(a)
            if m is not None and m.group(1) in _V2_NAMESPACES:
                found = True
        elif isinstance(a, dict):
            for v in a.values():
                _scan_refs(v)
        elif isinstance(a, (list, tuple)):
            for v in a:
                _scan_refs(v)

    def _scan_steps(raw_steps: Any) -> None:
        nonlocal found
        if found or not isinstance(raw_steps, list):
            return
        for st in raw_steps:
            if not isinstance(st, dict):
                continue
            if any(k in st for k in _MAP_KEYS) or \
                    any(k in st for k in _FOLD_KEYS):
                found = True
                return
            op = st.get("op")
            if isinstance(op, str) and "." in op:
                found = True                 # dotted op — v2 addressing
                return
            _scan_refs(st.get("args", {}))

    _scan_steps(steps)
    return found


def _parse_chain_spec_native(
    chain_dict: Dict[str, Any]
) -> Optional[ChainSpec]:
    """Native ``parse_chain_spec``: validate one chain block in C + rebuild
    the ChainSpec. ``None`` (→ pure path) on a non-dict input, a non-JSON
    payload, any C-side validation failure, or (rc420) a chain carrying any
    v2 form — see :func:`_chain_has_v2_forms` for why v2 must be
    Python-first."""
    if not isinstance(chain_dict, dict):
        return None
    if _chain_has_v2_forms(chain_dict):
        return None
    lib = _compose_lib("srmech_chain_spec_parse",
                       "srmech_chain_spec_parse_arena_bytes")
    if lib is None:
        return None
    try:
        payload = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError):
        return None
    text = _call_compose_native(
        lib, "srmech_chain_spec_parse_arena_bytes",
        "srmech_chain_spec_parse", payload)
    if text is None:
        return None
    return _chain_spec_from_native(chain_dict, _srmech_json.loads(text))


def _parse_catalog_chains_native(
    catalog: Dict[str, Any], chains_raw: List[Any]
) -> Optional[List[ChainSpec]]:
    """Native ``parse_catalog_chains``: validate the schema version + every
    chain in C. ``None`` (→ pure path) on a non-JSON payload or any C-side
    validation failure (the pure path raises the specific ChainSpecError)."""
    if any(_chain_has_v2_forms(c) for c in chains_raw
           if isinstance(c, dict)):
        return None                      # v2 forms are Python-first (rc420)
    lib = _compose_lib("srmech_chain_catalog_parse",
                       "srmech_chain_catalog_parse_arena_bytes")
    if lib is None:
        return None
    payload_obj = {
        "chain_schema_version": catalog.get("chain_schema_version"),
        "operator_chain": chains_raw,
    }
    try:
        payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError):
        return None
    text = _call_compose_native(
        lib, "srmech_chain_catalog_parse_arena_bytes",
        "srmech_chain_catalog_parse", payload)
    if text is None:
        return None
    native_list = _srmech_json.loads(text)
    if len(native_list) != len(chains_raw):
        return None
    return [_chain_spec_from_native(chains_raw[i], native_list[i])
            for i in range(len(native_list))]


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
    native = _parse_chain_spec_native(chain_dict)
    if native is not None:
        return native
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
    chain_name: str, step_idx: int, raw_step: Any,
    idx_names: frozenset = frozenset(),
    bind_names: frozenset = frozenset(),
):
    """Parse + validate one step dict from a chain's ``steps`` list.

    v2 (rc420): dispatches on the step's discriminator keys — the map form
    (any of ``map_over``/``index``/``bind``/``body``), the fold form (any of
    ``fold_*``/``over``), or the plain v1 ``class``+``op``+``args`` form.
    Mixing forms on one step is rejected (the mutual-exclusion rule that
    keeps the C parse peer's required-keys check honest: a step can never
    carry BOTH a valid v1 skeleton and silently-droppable v2 keys).
    """
    if not isinstance(raw_step, dict):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: must be dict; "
            f"got {type(raw_step).__name__}"
        )
    has_map = any(k in raw_step for k in _MAP_KEYS)
    has_fold = any(k in raw_step for k in _FOLD_KEYS)
    has_std = any(k in raw_step for k in ("class", "op", "args"))
    if (1 if has_map else 0) + (1 if has_fold else 0) + \
            (1 if has_std else 0) > 1:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: mixes step forms "
            f"(map keys {sorted(k for k in _MAP_KEYS if k in raw_step)}, "
            f"fold keys {sorted(k for k in _FOLD_KEYS if k in raw_step)}, "
            f"plain keys "
            f"{sorted(k for k in ('class', 'op', 'args') if k in raw_step)})"
            f"; a step is exactly ONE form"
        )
    if has_map:
        return _parse_map_step(chain_name, step_idx, raw_step,
                               idx_names, bind_names)
    if has_fold:
        return _parse_fold_step(chain_name, step_idx, raw_step,
                                idx_names, bind_names)
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
    # Validate reference grammar + step-reference bounds (+ v2 scopes).
    _walk_args(args, lambda r: _validate_reference(r, step_idx,
                                                   idx_names, bind_names))
    return StepSpec(class_id=class_id, op=op, args=dict(args),
                    on_error=step_on_error)


def _parse_map_step(
    chain_name: str, step_idx: int, raw_step: Dict[str, Any],
    idx_names: frozenset, bind_names: frozenset,
) -> MapStepSpec:
    """Parse + validate one v2 MAP step (see :class:`MapStepSpec`)."""
    for required in ("map_over", "body"):
        if required not in raw_step:
            raise ChainSpecError(
                f"chain {chain_name!r} step[{step_idx}]: map step missing "
                f"required key {required!r} (a map is map_over + body "
                f"[+ index, bind])"
            )
    map_over = raw_step["map_over"]
    if not (isinstance(map_over, str) and map_over.startswith("@")):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: map_over must be a "
            f"reference string; got {map_over!r}"
        )
    _validate_reference(map_over, step_idx, idx_names, bind_names)
    index = raw_step.get("index", "k")
    if not (isinstance(index, str)
            and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", index)):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: map index must be an "
            f"identifier; got {index!r}"
        )
    bind_raw = raw_step.get("bind", {})
    if not isinstance(bind_raw, dict):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: map bind must be a "
            f"dict; got {type(bind_raw).__name__}"
        )
    # Bind values resolve in the OUTER scope, at map entry.
    _walk_args(bind_raw, lambda r: _validate_reference(r, step_idx,
                                                       idx_names, bind_names))
    body_raw = raw_step["body"]
    if not isinstance(body_raw, list) or len(body_raw) == 0:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: map body must be a "
            f"non-empty step list"
        )
    step_on_error = raw_step.get("on_error")
    if step_on_error is not None and step_on_error not in LEGAL_ERROR_POLICIES:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: illegal on_error "
            f"{step_on_error!r}; legal: {LEGAL_ERROR_POLICIES}"
        )
    # The body scope: this map's index + binds LAYER over the enclosing
    # scope (inner maps see outer indices/binds); @step[N] restarts at the
    # body (body-local numbering — the rc420 scoping decision).
    inner_idx = idx_names | frozenset({index})
    inner_bind = bind_names | frozenset(str(k) for k in bind_raw)
    body = tuple(
        _parse_step(chain_name, body_idx, raw_body, inner_idx, inner_bind)
        for body_idx, raw_body in enumerate(body_raw)
    )
    return MapStepSpec(map_over=map_over, index=index, bind=dict(bind_raw),
                       body=body, on_error=step_on_error)


def _parse_fold_step(
    chain_name: str, step_idx: int, raw_step: Dict[str, Any],
    idx_names: frozenset, bind_names: frozenset,
) -> FoldStepSpec:
    """Parse + validate one v2 FOLD step (see :class:`FoldStepSpec`)."""
    for required in ("fold_class", "fold_op", "fold_init", "over"):
        if required not in raw_step:
            raise ChainSpecError(
                f"chain {chain_name!r} step[{step_idx}]: fold step missing "
                f"required key {required!r} (a fold is fold_class + fold_op "
                f"+ fold_init + over [+ fold_args])"
            )
    fold_class = str(raw_step["fold_class"])
    if fold_class not in DEFAULT_CLASS_REGISTRY:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: unknown fold_class "
            f"{fold_class!r}; legal: {sorted(DEFAULT_CLASS_REGISTRY)}"
        )
    fold_op = str(raw_step["fold_op"])
    over = raw_step["over"]
    if not (isinstance(over, str) and over.startswith("@")):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: over must be a "
            f"reference string; got {over!r}"
        )
    _validate_reference(over, step_idx, idx_names, bind_names)
    fold_init = raw_step["fold_init"]
    _walk_args(fold_init, lambda r: _validate_reference(r, step_idx,
                                                        idx_names,
                                                        bind_names))
    fold_args = raw_step.get("fold_args")
    if fold_args is not None:
        if (not isinstance(fold_args, (list, tuple)) or len(fold_args) != 2
                or not all(isinstance(a, str) for a in fold_args)):
            raise ChainSpecError(
                f"chain {chain_name!r} step[{step_idx}]: fold_args must be "
                f"a pair of kwarg names (acc_name, elem_name); got "
                f"{fold_args!r}"
            )
        fold_args = (fold_args[0], fold_args[1])
    step_on_error = raw_step.get("on_error")
    if step_on_error is not None and step_on_error not in LEGAL_ERROR_POLICIES:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{step_idx}]: illegal on_error "
            f"{step_on_error!r}; legal: {LEGAL_ERROR_POLICIES}"
        )
    return FoldStepSpec(fold_class=fold_class, fold_op=fold_op,
                        fold_init=fold_init, over=over,
                        fold_args=fold_args, on_error=step_on_error)


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


def _resolve_dotted_callable(dotted: str, *, what: str) -> Callable[..., Any]:
    """Resolve a fully-qualified dotted name to a callable.

    The BLK-REGMAP lever (rc420): ``class`` is CLASSIFICATION; a dotted
    ``op`` (or an ``@op.`` reference) is ADDRESSING. Mirrors the shipped
    srmech.dsl dotted-op resolver (``_catalog.py`` §17 U2): split at the
    last dot, import the module, getattr the attribute."""
    mod_path, _, attr = dotted.rpartition(".")
    if not mod_path:
        raise ChainSpecError(
            f"{what}: dotted name {dotted!r} needs at least "
            f"<module>.<callable>"
        )
    try:
        module = importlib.import_module(mod_path)
    except ImportError as exc:
        raise ChainSpecError(
            f"{what}: module {mod_path!r} not importable: {exc}"
        ) from exc
    fn = getattr(module, attr, None)
    if fn is None or not callable(fn):
        raise ChainSpecError(
            f"{what}: {dotted!r} does not resolve to a callable "
            f"(checked {mod_path}.{attr})"
        )
    return fn


def _resolve_reference(
    ref: str,
    *,
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
    step_outputs: List[Any],
    idx_env: Optional[Dict[str, int]] = None,
    bind_env: Optional[Dict[str, Any]] = None,
) -> Any:
    """Resolve one reference string at runtime."""
    m = _REFERENCE_PATTERN.match(ref)
    if not m:
        raise ValueError(f"reference {ref!r} does not match DSL")
    namespace = m.group(1)
    path = m.group(2)
    if namespace == "idx":
        name = path[1:]
        if idx_env is None or name not in idx_env:
            raise RuntimeError(
                f"reference {ref!r}: no enclosing map binds index {name!r}"
            )
        return idx_env[name]
    if namespace == "bind":
        if bind_env is None:
            raise RuntimeError(
                f"reference {ref!r}: no enclosing map binds anything"
            )
        return _resolve_dotted_path(bind_env, path)
    if namespace == "op":
        return _resolve_dotted_callable(path[1:], what=f"reference {ref!r}")
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
    from ..amsc import catalog as _catalog
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
    idx_env: Optional[Dict[str, int]] = None,
    bind_env: Optional[Dict[str, Any]] = None,
) -> Any:
    """Recursively resolve all references in an args structure."""
    if isinstance(args, str):
        if args.startswith("@"):
            return _resolve_reference(
                args, row=row, inputs=inputs, step_outputs=step_outputs,
                idx_env=idx_env, bind_env=bind_env,
            )
        return args
    if isinstance(args, dict):
        return {
            k: _resolve_args(v, row=row, inputs=inputs,
                             step_outputs=step_outputs,
                             idx_env=idx_env, bind_env=bind_env)
            for k, v in args.items()
        }
    if isinstance(args, list):
        return [
            _resolve_args(v, row=row, inputs=inputs,
                          step_outputs=step_outputs,
                          idx_env=idx_env, bind_env=bind_env)
            for v in args
        ]
    if isinstance(args, tuple):
        return tuple(
            _resolve_args(v, row=row, inputs=inputs,
                          step_outputs=step_outputs,
                          idx_env=idx_env, bind_env=bind_env)
            for v in args
        )
    return args


# ──────────────────────────────────────────────────────────────────────
# Native RUN LOOP dispatch (0.9.0rc174; the ORCHESTRATION→C spine, batch 4).
# ``srmech_chain_run`` runs a validated chain end-to-end in C to byte-identical
# OUTPUT, for chains whose ops are ALL in the BOUNDED Class-N dispatch table —
# the shipped apparatus: pi_cascade_digits / {exp,sin,cos,log1p,atan}_series_
# truncate / rational_{add,mul,div,pow_uint}. The C peer does NOT mirror the
# resolve_chain CLOSURE (a live-object-graph dispatch); parity is on the final
# VALUE, marshaled back as a canonical value DESCRIPTOR ({"k":"s"/"q"/"i"/"n"/
# "l", ...}; bignums as decimal strings). rc103 inform-don't-limit: any
# out-of-table op, @catalog ref, non-"raise" policy, non-i64 input, or C-side
# overflow → the sentinel _NATIVE_MISS so the COMPLETE pure path runs (never a
# wrong answer; the pure path raises the exact ChainSpecError / ValueError).
# ──────────────────────────────────────────────────────────────────────

_NATIVE_MISS = object()   # sentinel: C did NOT run (distinct from a None result)

# The op names the C dispatch table covers — ALL Class N (srmech.math.rational).
#: Ops the C chain runner's dispatch table handles. MUST track ``cr_dispatch``
#: in ``c/src/srmech_compose_run.c`` — and, since rc452 (`#T1166`), the shared
#: ``CR_OP_REG`` table it reads. *(This named ``cr_dispatch_real`` alongside it
#: until mid-rc452; the same rc's A1 reshape DELETED that function — it existed only to absorb arms
#: that would have pushed ``cr_dispatch`` past JPL Rule 4's 60 lines, and the
#: table made it unnecessary. The name survived here, and in one more docstring
#: below, in text that ships inside the wheel.)*
#: ``tests/test_c_chain_eligibility_rc447.py`` asserts the two agree, so a C
#: arm added without updating this set fails there rather than going unreachable.
#:
#: ⚠️ THIS SET WAS CLASS-N ONLY, AND THE CLASS FILTER BESIDE IT MADE THE WHOLE C
#: CHAIN RUNNER UNREACHABLE FROM PYTHON. ``_chain_c_eligible`` required
#: ``step.class_id == "N"``, so every Class-I / C / K / L chain returned
#: ``_NATIVE_MISS`` at the top of ``_run_chain_native`` — BEFORE the library was
#: ever consulted. Measured at rc447: the predicate answered "C-runnable" for
#: **0** of the 18 executable descriptors while **9** of them demonstrably run
#: under ``srmech_chain_run``; it was wrong on all nine. The C work was real and
#: correct and the package could not reach it, which no parity gate could see —
#: those call ``srmech_chain_run`` directly through ctypes and so bypass exactly
#: the predicate that was blocking it.
_RUN_C_OPS = frozenset({
    # Class N — the original set
    "pi_cascade_digits",
    "exp_series_truncate", "sin_series_truncate", "cos_series_truncate",
    "log1p_series_truncate", "atan_series_truncate",
    "rational_pow_uint", "rational_add", "rational_mul", "rational_div",
    # Class I — cyclic (rc447), bigint-carried
    "gcd", "mod_add", "mod_mul", "mod_mul_wide", "mod_pow", "mod_inv",
    # Class C / K / L — the real-sequence and pin-slot arms (rc447)
    "chiral_flip", "autocorrelation", "pin_slot_at_zero", "reorient",
    # ⚠️ `orientation_compose` WAS LISTED HERE AND WAS A PHANTOM (removed rc452,
    # `#T1166`). It has NEVER been a plain dispatch arm: measured at the rc452
    # branch point, neither `cr_dispatch` nor `cr_dispatch_real` carried an arm
    # for it — it existed only inside `cr_body_is_orient_compose`, a FOLD-FORM
    # predicate. It reached this set because the eligibility gate's scanner
    # matched `cr_op_is` over the WHOLE FILE and so read that form predicate as
    # a dispatch arm; the sibling gate in test_t1158 scoped its scan to the two
    # dispatch functions precisely to avoid this and said so in its docstring,
    # but the two scanners were never reconciled. Consequence while live: a
    # chain naming `orientation_compose` as a PLAIN step was admitted here,
    # marshalled to C, and declined NOT_IMPL — a full marshal-and-decline per
    # call, never a wrong answer. It stays in `_RUN_C_FOLD_OPS`, which is the
    # set that was always true of it. Surfaced by rc452's table-derived scan.
    # Class B / L / M — the autocorrelation CHAIN's own steps (rc452, `#T1166`).
    # Deliberately the fine steps, NOT a dispatch of srmech_autocorrelation_f64:
    # that fused kernel is what the `autocorrelation` OP row runs, and the
    # `autocorrelation` CHAIN is a different object whose steps never name it.
    "seq_len", "correlation_product", "compensated_sum",
    # Class K / N / B — the best_rational_signed steps (rc451, `#T1164`).
    # FOUR separate arms at step granularity in the CR_OP_REG table, deliberately
    # NOT one dispatch of the fused srmech_cascade_best_rational_signed_f64:
    # that symbol is value-identical to the fine pipeline over the whole
    # C-accepted domain, so a coarse dispatch would satisfy every value-level
    # gate while the descriptor's steps drove nothing.
    "dead_band", "scale_round_half_even", "best_rational", "pair",
    # Class E / M / N / C — the kuramoto_step and hypercomplex-DFT chains'
    # own steps (rc452 Phase 3, `#T1166`). Same discipline as above: the
    # fused srmech_cascade_kuramoto_step_f64 / _general_f64 /
    # srmech_quaternion_dft / srmech_octonion_dft symbols all exist and NONE
    # is dispatched — each summand/term arm delegates only to the
    # STEP-granular exports the Python op itself composes
    # (srmech_sin_q61, srmech_quaternion_twiddle + _left/right_mult,
    # srmech_octonion_twiddle + srmech_loop_{left,right}_op_f64).
    "seq_get", "vec_scale",
    "kuramoto_inv_n", "kuramoto_sin_term", "kuramoto_out_simple",
    "kuramoto_gen_term", "kuramoto_gen_out",
    "as_quat4", "as_oct8", "qdft_resolve_mu", "odft_resolve_mu",
    "dft_sigma", "dft_scale", "qdft_summand", "odft_summand",
})

#: Fold-body ops the C runner dispatches — the non-``CR_BIN_NONE`` ``bin``
#: column of the SHARED ``CR_OP_REG`` atom table (``cr_fold_body`` looks the
#: row up with the same matcher ``cr_dispatch`` uses).
#:
#: ⚠️ STILL ITS OWN SET, AND FOR A DIFFERENT REASON THAN BEFORE. Through rc451
#: this was separate because C's fold body was a PRIVATE single-entry table. As
#: of rc452 it shares the op table, but the two sets are still not equal: a fold
#: body takes two already-evaluated POSITIONAL carriers while a plain op pulls
#: named operands out of ``args``, so an op can be dispatchable as one and not
#: the other. ``orientation_compose`` is fold-body-ONLY (no shipped descriptor
#: names it as a plain step); most ops are plain-only. Keeping the sets distinct
#: states that difference instead of flattening it.
#: ``tests/test_c_chain_eligibility_rc447.py`` derives BOTH columns out of the C
#: table and asserts each against its Python peer, so a widened C row that is not
#: mirrored here is red rather than silently unreachable.
_RUN_C_FOLD_OPS = frozenset({"orientation_compose", "gcd",
                             # rc452 Phase 3: the Σ accumulators of the
                             # kuramoto (scalar) and DFT (vector) map chains.
                             "f64_add", "vec_add"})

_I64_MAX = (1 << 63) - 1
_I64_MIN = -(1 << 63)


def _i64(v: Any) -> bool:
    """True iff ``v`` (if an int) fits the C JSON parser's int64 width."""
    return (not isinstance(v, int)) or isinstance(v, bool) or (
        _I64_MIN <= v <= _I64_MAX)


def _run_ints_fit_i64(
    spec: ChainSpec,
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
) -> bool:
    """True iff every int the C run will read as int64 fits int64 — i.e. every
    literal int in an arg AND every ``@row`` / ``@input`` reference that
    resolves to an int. UNREFERENCED row fields (e.g. the bignum ``expected_*``
    columns the chain never touches) are irrelevant. ``@step`` refs read prior
    C-produced carriers (exact bignum, never an int64 JSON round-trip) and
    ``@catalog`` already routes to pure, so neither is checked here."""
    ok = True

    def _walk(a: Any) -> None:
        nonlocal ok
        if isinstance(a, str) and a.startswith("@"):
            m = _REFERENCE_PATTERN.match(a)
            if m is not None and m.group(1) in ("row", "input"):
                try:
                    v = _resolve_reference(a, row=row, inputs=inputs,
                                           step_outputs=[])
                except Exception:  # noqa: BLE001 — unresolved → C defers to pure
                    return
                if not _i64(v):
                    ok = False
            return
        if isinstance(a, bool):
            return
        if isinstance(a, int):
            if not _i64(a):
                ok = False
        elif isinstance(a, dict):
            for x in a.values():
                _walk(x)
        elif isinstance(a, (list, tuple)):
            for x in a:
                _walk(x)

    for step in spec.steps:
        if isinstance(step, StepSpec):
            _walk(step.args)
        else:
            # A FOLD step has no `args` — its literals live in `fold_init`
            # (`over` is a reference, resolved from the ctx, which this walk
            # covers separately). Guarding on the TYPE rather than hasattr so a
            # future step form fails loudly here instead of silently skipping
            # its int-width check.
            _walk(getattr(step, "fold_init", None))
    return ok


def _map_body_c_eligible(step: "MapStepSpec") -> bool:
    """True iff every step of a map body (recursively) is C-runnable.

    A map body is "a chain in miniature", so the test is the chain test applied
    to the body — including NESTED maps, which is why this recurses rather than
    walking the body flat. A FLAT walk is a known-wrong census on this tree:
    measured over the packaged descriptors, it sees 72 of 134 steps, and on
    ``autocorrelation`` it sees 2 of 6. A predicate built on the flat walk would
    admit a chain whose inner body C declines, costing a marshal-and-decline on
    every call.

    C's own frame stack caps map nesting at ``CR_MAP_DEPTH`` (4); the deepest
    shipped nesting is 2. The cap is not mirrored here because C returns
    ``NOT_IMPL`` past it and the chain then takes the complete pure path — a
    decline, never a wrong answer.
    """
    for st in step.body:
        if isinstance(st, MapStepSpec):
            if not _map_body_c_eligible(st):
                return False
            continue
        if not isinstance(st, StepSpec):
            fold_op = getattr(st, "fold_op", None)
            if fold_op is None:
                return False
            if str(fold_op).rpartition(".")[2] not in _RUN_C_FOLD_OPS:
                return False
            if getattr(st, "fold_args", None) is not None:
                return False
            continue
        if st.on_error not in (None, "raise"):
            return False
        if st.op.rpartition(".")[2] not in _RUN_C_OPS:
            return False
        if not _step_args_are_bindable(st):
            return False
    return True


def _chain_c_eligible(spec: ChainSpec) -> bool:
    """True iff every step is a "raise"-policy, in-table op — the
    precondition for the C run loop (else the complete pure path runs).

    ⚠️ This line said "raise"-policy, **Class-N**, in-table until rc448. The
    Class-N conjunct was the rc447 defect itself (`#T1141`): it refused every
    Class-I/C/K/L chain at the door and answered 0 where 9 chains run. rc447
    deleted the gate — see the comment in the loop below — but left this
    docstring asserting it, so the function's contract still named a test its
    body no longer performs. Membership is by op NAME, suffix-matched.

    rc420: a v2 step (map / fold — not a plain :class:`StepSpec`) is never
    C-run-eligible; the type check comes FIRST so the guard cannot
    AttributeError on a spec kind it predates."""
    if spec.on_error != "raise":
        return False
    for step in spec.steps:
        if not isinstance(step, StepSpec):
            # A v2 step (map / fold). C implements BOTH since rc452: the FOLD
            # form since rc446 (body now via the shared atom table), and the MAP
            # form via `cr_drive`'s explicit frame stack.
            #
            # ⚠️ MAP MUST BE ADMITTED HERE OR THE C CAPABILITY IS UNREACHABLE.
            # `_run_chain_native` returns `_NATIVE_MISS` when this predicate says
            # False, BEFORE the library is consulted — which is exactly the rc447
            # defect (`#T1141`): the C work was real and correct and the package
            # could not reach it, and no parity gate could see it, because those
            # drive `srmech_chain_run` through ctypes and bypass this function.
            if isinstance(step, MapStepSpec):
                if not _map_body_c_eligible(step):
                    return False
                continue
            fold_op = getattr(step, "fold_op", None)
            if fold_op is None:
                return False
            if str(fold_op).rpartition(".")[2] not in _RUN_C_FOLD_OPS:
                return False
            if getattr(step, "fold_args", None) is not None:
                return False       # the keyword-named fold is a different arm
            continue
        if step.on_error not in (None, "raise"):
            return False
        # The CLASS is no longer part of the test — C dispatches on the op NAME
        # (by suffix), and gating on class_id is what made every Class-I/C/K/L
        # chain unreachable. The op set is the honest predicate.
        if step.op.rpartition(".")[2] not in _RUN_C_OPS:
            return False
        if not _step_args_are_bindable(step):
            return False
    return True


def _step_args_are_bindable(step: "StepSpec") -> bool:
    """True unless the step declares an ``args`` key the op does not accept.

    ⚠️ rc449 (`#T1158`, gh #1653). Until now NOTHING on this path compared
    ``step.args`` keys to the op's signature — ``_chain_c_eligible`` gated on
    ``on_error`` and membership in ``_RUN_C_OPS`` and nothing else, and there was
    no ``_op_accepts`` equivalent anywhere in this module, while
    ``_run_chain_native`` is tried FIRST. So a chain declaring ``gcd{a, b, bogus}``
    went to C, which silently dropped the key and computed — measured bare-C at
    rc448: ``OK`` and ``6``.

    rc449's C validator now refuses that, and this predicate simply stops the
    Python side proposing a chain it can already tell C will decline. It is the
    Surface-A twin of ``srmech.dsl._chain._op_accepts``, and like it, it is a
    builder-honesty edit rather than the thing that closes the gap: without it
    the C refusal still collapses to ``_NATIVE_MISS`` and the pure path raises the
    same ``TypeError``.

    Conservative in the same two places as its DSL twin: an op whose callable
    cannot be resolved or whose signature cannot be read is NOT judged (an
    unreadable signature is not evidence of rejection), and ``**kwargs`` accepts
    anything. Unlike the DSL twin there is no data-carrier exclusion — on this
    surface every operand arrives BY NAME inside ``args``, so ``params[0]`` is a
    perfectly legal key. That asymmetry is the same one the C validators encode
    (``params[*]`` here, ``params[1..]`` there) and it is pinned in
    ``c/test/test_srmech_chain_run.c``.
    """
    args = getattr(step, "args", None)
    if not isinstance(args, dict) or not args:
        return True
    legal = _legal_arg_names(step.op, step.class_id)
    if legal is None:                    # unreadable / open namespace → not judged
        return True
    return all(k in legal for k in args)


@lru_cache(maxsize=512)
def _legal_arg_names(op: str, class_id: str) -> Optional[frozenset]:
    """Legal ``args`` key names for one step op, or ``None`` when not judgeable.

    CACHED because ``_chain_c_eligible`` runs on the hot path — once per chain
    run, per step — and ``inspect.signature`` is not cheap. The key is the pair
    the resolution actually depends on, and both halves of the resolution
    (dotted-import and the class-letter registry) are stable for a given pair
    within a process, so this cannot go stale against anything a caller can
    change mid-run.

    ``None`` means "do not judge": an op whose callable will not resolve, whose
    signature will not read, or which takes ``**kwargs``. Guessing "unbindable"
    in any of those cases would defer a chain that runs perfectly well — the
    stricter-than-Python failure, arriving from the Python side instead of C.
    """
    fn = None
    if "." in op:
        try:
            fn = _resolve_dotted_callable(op, what="c-eligibility probe")
        except Exception:
            return None
    else:
        module_name = DEFAULT_CLASS_REGISTRY.get(class_id)
        if module_name is None:
            return None
        try:
            fn = getattr(importlib.import_module(module_name), op, None)
        except Exception:
            return None
    if fn is None or not callable(fn):
        return None
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return None
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return None
    return frozenset(
        n for n, p in params.items()
        if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                      inspect.Parameter.KEYWORD_ONLY))


def _steps_to_dicts(steps) -> list:
    """Serialise a step tuple (recursively — map bodies are step tuples too)
    to the raw-dict shape ``srmech_chain_run`` reads.

    ⚠️ THE MAP BRANCH WAS MISSING THROUGH THE FIRST TWO PHASES OF rc452, AND
    THAT WAS A LIVE CRASH, NOT A MISS. ``_chain_c_eligible`` admits map chains
    (it must — otherwise the C map capability is unreachable, the rc447
    defect), and ``_run_chain_native`` then serialises the spec through here —
    where a ``MapStepSpec`` fell into the fold branch and raised
    ``AttributeError: 'MapStepSpec' object has no attribute 'fold_op'``.
    Measured on the rc452 branch head with the freshly built ``.so``:
    ``resolve_chain(autocorrelation)(x=[1.0, 2.0, 3.0])`` CRASHED, while every
    ctypes-driven gate stayed green — those reach around ``resolve_chain``,
    which is exactly the blind spot the rc447 eligibility gate documents. The
    end-to-end ``run_cascade_chain`` gate did not catch it because its driver
    swallows per-case exceptions as "routing, not values".
    """
    out: list = []
    for s in steps:
        if isinstance(s, StepSpec):
            out.append({"class": s.class_id, "op": s.op, "args": s.args})
        elif isinstance(s, MapStepSpec):
            step: Dict[str, Any] = {
                "map_over": s.map_over,
                "index": s.index,
                "body": _steps_to_dicts(s.body),
            }
            if s.bind:
                step["bind"] = s.bind
            out.append(step)
        else:
            # A FOLD step (rc447). Key names mirror the ADR-0008 §2 fold step
            # the C classifier reads. ``fold_args`` chains are never admitted
            # by ``_chain_c_eligible``, so the keyword-named form is not
            # spelled here.
            out.append({
                "fold_class": getattr(s, "fold_class", None)
                or getattr(s, "class_id", "C"),
                "fold_op": s.fold_op,
                "fold_init": s.fold_init,
                "over": s.over,
            })
    return out


def _spec_to_chain_dict(spec: ChainSpec) -> Dict[str, Any]:
    """Serialise a ChainSpec back to the chain-dict shape srmech_chain_run reads
    (name / summary / returns / on_error / steps[{class, op, args}])."""
    return {
        "name": spec.name, "summary": spec.summary, "returns": spec.returns,
        "on_error": spec.on_error,
        "steps": _steps_to_dicts(spec.steps),
    }


#: Cached :class:`srmech.math.q.Q`. Bound LAZILY and once: ``srmech.math.q``
#: imports ``srmech.math.rational``, which is itself reachable from the chain
#: op registry, so a module-level import here would put the reader inside that
#: cycle for no gain. One ``if`` on a hot path is the whole cost.
_Q_CLS = None


def _Q(num: int, den: int):
    """The exact-ℚ carrier for a ``q`` descriptor. See :func:`_reconstruct_value`."""
    global _Q_CLS
    if _Q_CLS is None:
        from srmech.math.q import Q as _QC
        _Q_CLS = _QC
    return _Q_CLS(num, den)


def _reconstruct_value(desc: Dict[str, Any]) -> Any:
    """Rebuild a Python value from the C value descriptor. Bignums arrive as
    decimal strings (exact); a rational rebuilds as the exact-ℚ carrier
    :class:`srmech.math.q.Q` (matching the Class-N ops' return type)."""
    k = desc.get("k")
    if k == "s":
        return desc["v"]
    if k == "q":
        # rc452 (`#T1166`): the exact-ℚ carrier, NOT a ``(num, den)`` tuple.
        #
        # THE DEFECT WAS NEVER IN THE WIRE. The shipped C has built CR_RATIONAL
        # inside three op bodies since long before this rc (srmech_compose_run.c
        # cr_op_rat / cr_op_pow / cr_op_series) and two live attested catalogs
        # (asymptotic_calculus, cosmos_validation) dispatch those ops, so `q`
        # was on the wire all along. The collapse lived HERE: this line rebuilt
        # an exact rational as a generic 2-tuple of ints, which is also what a
        # Class-K pin pair and a Class-B `pair` step rebuild as — so the value
        # arrived type-erased and no comparator downstream could tell an exact
        # ℚ chain from an integer-pair chain. Config C's controlled two-arm
        # experiment isolated the causal variable with the wire held constant:
        # Python returning tuples gave 39/39 DIVERGENT, Python returning Q gave
        # 39/39 BYTE_IDENTICAL. The Python-side TYPE is what discrimination
        # turns on, not the spelling.
        #
        # The docstring above pinned the tuple contract in prose and shipped
        # inside the wheel; it is corrected in this same change rather than
        # left to drift.
        #
        # ABI 20 -> 21 rides with this: a STALE reader paired with a current
        # .so would rebuild a tuple from a q SILENTLY — the silent-wrong-value
        # class, strictly worse than the raise-class condition rc451 bumped for.
        return _Q(int(desc["n"]), int(desc["d"]))
    if k == "i":
        return int(desc["v"])
    if k == "n":
        return None
    if k == "l":
        # rc451: the payload key is "v", changed from "items" in lockstep with
        # the C writer (cr_desc_list) and the ABI 19 -> 20 bump. Closes gap-
        # ledger row wire_l_payload_key_divergence, which had the chain-run wire
        # spelling this kind's payload "items" while the sibling DSL wire spelled
        # the SAME kind's payload "v". The `t` kind below forced the decision:
        # leaving `l` on "items" would have made one wire internally inconsistent
        # or grown the cross-wire divergence from one kind to two.
        return [_reconstruct_value(it) for it in desc["v"]]
    if k == "t":
        # A TUPLE, not a list — the distinction the wire could not spell until
        # rc451 (`#T1164`, gh #1653 item 4). `best_rational_signed` declares
        # ``tuple[int, int]`` and is the only executable descriptor that returns
        # one, so it was the chain this gap blocked; the shipped value-parity
        # comparator pins ``tuple != list`` as a required-DIVERGENT witness, so
        # answering `l` here would be a wrong value, not a missing capability.
        # Lands with the C-side ``is_tuple`` flag in the SAME change — a kind
        # that reached this reader before its branch existed would raise below,
        # and ABI 20 enforces the converse for a stale ``.so``.
        return tuple(_reconstruct_value(it) for it in desc["v"])
    if k == "f":
        # A real-valued result. EXACT, not approximate: the C writer formats
        # doubles via ``srmech_double_repr`` (an integer-only Ryu matching
        # CPython ``repr(float)`` byte for byte), so this round-trips with no
        # last-bit drift and a bit-identical parity claim holds. Added in
        # lockstep with the C-side ``CR_DBL`` — a new descriptor kind that
        # reached this reader before the branch existed would raise below, so
        # the two halves cannot ship apart (ABI 17 -> 18 enforces it for a
        # stale ``.so`` paired with a current Python).
        return float(desc["v"])
    raise ValueError(f"unknown chain-run value descriptor kind {k!r}")


def _drop_oversized_ints(obj: Any) -> "tuple[Any, bool]":
    """Strip out-of-int64 ints from the ctx tree bound for the C run loop.

    Returns ``(cleaned, ok)``; ``ok`` False means the caller must take
    ``_NATIVE_MISS`` because the value could not be dropped safely.

    **Why this exists (rc402, `#T1068`).** :func:`_run_ints_fit_i64` has already
    guaranteed that every int the C run will actually READ fits int64, so by
    construction any oversized int still in the tree is UNREFERENCED — exactly
    the ``expected_num`` / ``expected_den`` bignum columns that docstring names
    as "irrelevant". They were irrelevant only because ``srmech_json`` used to
    parse an out-of-int64 literal by silently CLAMPING it to ``INT64_MAX``: the
    clamped value was never read, so nobody saw the wrong number, and the fast
    path stayed available. rc402 makes that literal DECLINE with
    ``SRMECH_ERR_OVERFLOW`` — correctly — which would otherwise cost the C fast
    path on 10 of the 51 shipped catalog chain rows purely because of a column
    the chain never touches.

    Dropping the KEY is the honest way to keep that property: C never reads the
    field, and if one ever WERE referenced the lookup finds nothing, yields NULL
    and the whole chain defers to the pure runner — a miss, never a wrong
    answer. A bare int inside a LIST is different: removing an element would
    renumber the ones after it and silently corrupt an ``[N]`` index, so that
    case reports ``ok=False`` and the caller defers to pure instead.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, int) and not isinstance(v, bool) and not _i64(v):
                continue                     # unreferenced bignum column: drop
            cleaned, ok = _drop_oversized_ints(v)
            if not ok:
                return obj, False
            out[k] = cleaned
        return out, True
    if isinstance(obj, list):
        out_list = []
        for v in obj:
            if isinstance(v, int) and not isinstance(v, bool) and not _i64(v):
                return obj, False            # cannot drop without renumbering
            cleaned, ok = _drop_oversized_ints(v)
            if not ok:
                return obj, False
            out_list.append(cleaned)
        return out_list, True
    return obj, True


def _run_chain_native(
    spec: ChainSpec,
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
) -> Any:
    """Run the chain in C → the final value, or ``_NATIVE_MISS`` (→ pure)."""
    if not _chain_c_eligible(spec):
        return _NATIVE_MISS
    lib = _compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        return _NATIVE_MISS
    from .. import _native
    import ctypes
    if not _run_ints_fit_i64(spec, row, inputs or {}):
        return _NATIVE_MISS
    chain_dict = _spec_to_chain_dict(spec)
    ctx, ctx_ok = _drop_oversized_ints({"row": row, "inputs": inputs or {}})
    if not ctx_ok:
        return _NATIVE_MISS
    try:
        chain_json = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
        ctx_json = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError):
        return _NATIVE_MISS
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(
        len(chain_json), len(ctx_json)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = lib.srmech_chain_run(
        chain_json, len(chain_json), ctx_json, len(ctx_json),
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        return _NATIVE_MISS
    desc = _srmech_json.loads(out.raw[:out_len.value].decode("utf-8"))
    return _reconstruct_value(desc)


def _resolve_step_op(
    chain_name: str, idx: int, class_id: str, op: str,
    reg: Dict[str, str],
) -> Callable[..., Any]:
    """Resolve one step's op name to a callable.

    A DOTTED op resolves by import (the rc420 BLK-REGMAP lever — ``class``
    is classification, the dotted name is addressing); a bare op resolves
    through the letter->module registry exactly as v1 did."""
    if "." in op:
        return _resolve_dotted_callable(
            op, what=f"chain {chain_name!r} step[{idx}]")
    module_name = reg.get(class_id)
    if module_name is None:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{idx}]: class "
            f"{class_id!r} has no registered module"
        )
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise ChainSpecError(
            f"chain {chain_name!r} step[{idx}]: module "
            f"{module_name!r} not importable: {exc}"
        ) from exc
    op_callable = getattr(module, op, None)
    if op_callable is None or not callable(op_callable):
        raise ChainSpecError(
            f"chain {chain_name!r} step[{idx}]: op {op!r} "
            f"not found on {module_name!r}"
        )
    return op_callable


def _resolve_steps(
    chain_name: str, steps, reg: Dict[str, str],
) -> List[Tuple[Any, Any]]:
    """Resolve a step tuple to an execution tree.

    Each entry is ``(spec, payload)``: a plain step's payload is its
    callable; a fold step's payload is its fold-op callable; a map step's
    payload is its recursively-resolved BODY tree. Resolution happens once,
    up front — activation-time failure, never mid-run (Phase 1 §7)."""
    resolved: List[Tuple[Any, Any]] = []
    for idx, step in enumerate(steps):
        if isinstance(step, MapStepSpec):
            resolved.append(
                (step, _resolve_steps(chain_name, step.body, reg)))
        elif isinstance(step, FoldStepSpec):
            resolved.append(
                (step, _resolve_step_op(chain_name, idx, step.fold_class,
                                        step.fold_op, reg)))
        else:
            resolved.append(
                (step, _resolve_step_op(chain_name, idx, step.class_id,
                                        step.op, reg)))
    return resolved


def resolve_chain(
    spec: ChainSpec,
    registry: Optional[Dict[str, str]] = None,
) -> Callable[..., Any]:
    """Resolve a chain to a callable.

    Validates that each step's ``op`` exists on the registered class
    module (or, dotted, resolves by import); raises
    :class:`ChainSpecError` on missing op. Map bodies resolve recursively.

    Returns a callable with signature
    ``f(row: Optional[dict] = None, **inputs) -> Any`` that executes
    the chain.
    """
    reg = registry or DEFAULT_CLASS_REGISTRY
    resolved_ops = _resolve_steps(spec.name, spec.steps, reg)

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
    """Execute a resolved chain. Output of the final step is returned.

    A chain whose ops are ALL in the bounded Class-N C dispatch table runs
    end-to-end in C to byte-identical OUTPUT (0.9.0rc174); any out-of-table op /
    non-raise policy / non-i64 input / C overflow falls through to the pure
    loop below (rc103 inform-don't-limit — never a wrong answer)."""
    native = _run_chain_native(spec, row, inputs)
    if native is not _NATIVE_MISS:
        return native
    return _run_resolved_steps(spec, resolved_ops, row, inputs,
                               idx_env={}, bind_env={})


def _run_map_step(
    spec: ChainSpec,
    step: MapStepSpec,
    resolved_body: List[Tuple[Any, Any]],
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
    step_outputs: List[Any],
    idx_env: Dict[str, int],
    bind_env: Dict[str, Any],
) -> List[Any]:
    """Run one indexed-map step: exactly ``n`` body runs, ``n`` pinned at
    entry (the totality pin — see :class:`MapStepSpec`)."""
    seq = _resolve_reference(step.map_over, row=row, inputs=inputs,
                             step_outputs=step_outputs,
                             idx_env=idx_env, bind_env=bind_env)
    try:
        n = len(seq)                  # n FIXED AT ENTRY — the totality pin
    except TypeError:
        raise ChainSpecError(
            f"chain {spec.name!r}: map_over {step.map_over!r} must resolve "
            f"to a SIZED sequence (len()-able); an unsized iterable would "
            f"make n data-dependent at run time"
        )
    binds = {
        name: _resolve_args(ref, row=row, inputs=inputs,
                            step_outputs=step_outputs,
                            idx_env=idx_env, bind_env=bind_env)
        for name, ref in step.bind.items()
    }
    inner_bind = {**bind_env, **binds}
    out: List[Any] = []
    for k in range(n):                # exactly n body runs, no predicate
        inner_idx = dict(idx_env)
        inner_idx[step.index] = k
        out.append(_run_resolved_steps(spec, resolved_body, row, inputs,
                                       idx_env=inner_idx,
                                       bind_env=inner_bind))
    return out


def _run_resolved_steps(
    spec: ChainSpec,
    resolved_ops: List[Tuple[Any, Any]],
    row: Optional[Dict[str, Any]],
    inputs: Dict[str, Any],
    *,
    idx_env: Dict[str, int],
    bind_env: Dict[str, Any],
) -> Any:
    """The (recursive) v2 execution spine: run one resolved step list.

    A map body runs through this same function with its OWN (body-local)
    ``step_outputs`` and a layered idx/bind environment — a body is a chain
    in miniature (the rc420 scoping decision)."""
    step_outputs: List[Any] = []
    final_output: Any = None
    for idx, (step, payload) in enumerate(resolved_ops):
        policy = step.on_error or spec.on_error
        if policy == "skip":
            raise NotImplementedError(
                "on_error='skip' is only valid in batch-execution "
                "contexts; not supported by run_chain()"
            )
        try:
            if isinstance(step, MapStepSpec):
                result = _run_map_step(spec, step, payload, row, inputs,
                                       step_outputs, idx_env, bind_env)
            elif isinstance(step, FoldStepSpec):
                seq = _resolve_reference(step.over, row=row, inputs=inputs,
                                         step_outputs=step_outputs,
                                         idx_env=idx_env, bind_env=bind_env)
                acc = _resolve_args(step.fold_init, row=row, inputs=inputs,
                                    step_outputs=step_outputs,
                                    idx_env=idx_env, bind_env=bind_env)
                if step.fold_args is not None:
                    acc_name, elem_name = step.fold_args
                    for elem in seq:      # the make_fold_stage contract
                        acc = payload(**{acc_name: acc, elem_name: elem})
                else:
                    for elem in seq:
                        acc = payload(acc, elem)
                result = acc
            else:
                args = _resolve_args(step.args, row=row, inputs=inputs,
                                     step_outputs=step_outputs,
                                     idx_env=idx_env, bind_env=bind_env)
                result = payload(**args)
        except Exception as exc:  # pragma: no cover (policy branches)
            if policy == "warn_return_none":
                what = (f"{step.class_id}.{step.op}"
                        if isinstance(step, StepSpec) else
                        type(step).__name__)
                warnings.warn(
                    f"chain {spec.name!r} step[{idx}] "
                    f"({what}) failed: {exc!r}; "
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

    Raises:
        ChainSpecError: ``toml_dict`` (or its ``[catalog]`` table) is not a
            mapping, or a chain is present without a supported
            ``[catalog].chain_schema_version``. ``ChainSpecError`` subclasses
            ``ValueError``, so existing ``except ValueError`` callers are
            unaffected.

    0.9.0rc434 (`#T1134`): the two shape guards below are new. Through
    0.9.0rc433 a non-mapping argument reached ``.get`` and leaked a bare
    ``AttributeError("'str' object has no attribute 'get'")`` out of a PUBLIC
    entry point — an ambush whose TYPE misattributes a caller's malformed
    input to an internal fault in srmech. Ruling (a): the CODE was wrong, so
    the code is what changed.
    """
    if not isinstance(toml_dict, Mapping):
        raise ChainSpecError(
            "parse_catalog_chains: expected a parsed TOML mapping; got "
            f"{type(toml_dict).__name__}. Parse the descriptor first "
            "(tomllib.loads / tomli.loads) and pass the resulting dict."
        )
    catalog = toml_dict.get("catalog", {})
    if not isinstance(catalog, Mapping):
        raise ChainSpecError(
            "parse_catalog_chains: [catalog] must be a table; got "
            f"{type(catalog).__name__}"
        )
    chains_raw = catalog.get("operator_chain", [])
    if not chains_raw:
        return []
    native = _parse_catalog_chains_native(catalog, chains_raw)
    if native is not None:
        return native
    schema_version = catalog.get("chain_schema_version")
    if schema_version is None:
        raise ChainSpecError(
            "catalog declares operator_chain entries but is missing "
            "[catalog].chain_schema_version"
        )
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ChainSpecError(
            f"catalog chain_schema_version = {schema_version!r}; this "
            f"engine implements {SUPPORTED_SCHEMA_VERSIONS} (v2 is a "
            f"strict superset of v1)"
        )
    return [parse_chain_spec(c) for c in chains_raw]


def greedy_bipartite_alignment(table_a, table_b, similarity_fn):
    """Greedy bipartite alignment between two ordered tables by content
    similarity (UPSTREAM_NOTES §2.2; the Rosetta-layer cross-substrate kernel
    matcher used from 54c onward). For each row of ``table_a`` in turn, pick the
    highest-``similarity_fn`` not-yet-used row of ``table_b``. Returns a dict
    mapping each A-index to ``(b_index, similarity)``; each B-row is used at most
    once, so when ``len(table_b) < len(table_a)`` the later A-rows go unmatched
    (absent from the result). ``similarity_fn(a_row, b_row) -> float``.

    A composition utility (greedy argmax + used-set), NOT an A–N primitive — it
    composes over whatever similarity the caller supplies (e.g.
    :func:`srmech.math.hdc.similarity`); lives in the compose layer rather than
    a class module for that reason.
    """
    # rc154 (BATCH B10, ``composition_of_c``): greedy argmax + used-set is a pure
    # **Class-K** selection (the ``s > best_s`` pin-slot decision) over a
    # caller-supplied ``similarity_fn`` — NOT an irreducible numeric kernel and NOT
    # an A–N primitive. It reaches no non-standalone-ready srmech leaf (the
    # similarity is the caller's; the control flow is standalone-trivial), the
    # SAME status as ``cascade.compose.top_k_by_score`` (Class-E ∘ Class-K
    # selection). Value-verified by a known-table alignment oracle; no new C symbol.
    if not callable(similarity_fn):
        raise TypeError("similarity_fn must be callable")
    a_rows = list(table_a)
    b_rows = list(table_b)
    used = set()
    mapping = {}
    for i, a_row in enumerate(a_rows):
        best_j = -1
        best_s = None
        for j, b_row in enumerate(b_rows):
            if j in used:
                continue
            s = float(similarity_fn(a_row, b_row))
            if best_s is None or s > best_s:
                best_s = s
                best_j = j
        if best_j >= 0:
            used.add(best_j)
            mapping[i] = (best_j, best_s)
    return mapping


__all__ = [
    "ChainSpec",
    "greedy_bipartite_alignment",
    "ChainSpecError",
    "DEFAULT_CLASS_REGISTRY",
    "ENGINE_SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "LEGAL_ERROR_POLICIES",
    "StepSpec",
    "parse_catalog_chains",
    "parse_chain_spec",
    "resolve_chain",
    "run_chain",
]
