"""TOML chain-spec loader for ``srmech dsl run <chain.toml>``.

The CLI subcommand reads a TOML chain spec (declarative pipeline) and
materialises it into a :class:`srmech.dsl.Chain`. The TOML schema is
flat-stages-with-nested-loop-sub-chains:

.. code-block:: toml

   [chain]
   name = "my-research-pipeline"

   [[stage]]
   op = "pin_slot_at_zero"

   [[stage]]
   op = "best_rational_signed"
   max_denominator = 100

   [[stage]]
   loop_n = 5
   [[stage.sub_chain]]
   op = "chiral_flip"

   [[stage]]
   fold_init = 0
   fold_op = "cyclic_gcd"

   [[stage]]
   reduce_op = "cyclic_gcd"

   [[stage]]
   parallel_body = "chiral_flip"
   n_sectors = 4
   combine = "bundle"        # recombine → composable stream (default)

One ``[[stage]]`` array element = one builder call. Mutually-exclusive
discriminators tell ``build_chain_from_toml`` which builder to invoke:

* ``op`` → ``chain.then(op, **kwargs)``
* ``loop_n`` + ``sub_chain`` → ``chain.loop(loop_n, build_chain_from_dict(sub_chain))``
* ``fold_init`` + ``fold_op`` → ``chain.fold(fold_init, fold_op, **kwargs)``
* ``reduce_op`` → ``chain.reduce(reduce_op, **kwargs)``
* ``parallel_body`` (+ optional ``n_sectors`` / ``combine``) → ``chain.parallel_sectors(parallel_body, n_sectors=n_sectors, combine=combine)``

The ``parallel`` discriminator (v0.6.0rc11; rc12 composability) is the
chain face of the Klein-4 four-sector fan-out
(:func:`srmech.amsc.cascade.parallel_sector_dispatch`): it runs the piped
value through the ``parallel_body`` op across ≤4 chirality sectors. A
special form like loop/fold/reduce, NOT a plain ``op`` (which is why
``op = "parallel_sector_dispatch"`` is rejected with a guided error
pointing here). ``combine`` (default ``"bundle"``; also ``"mean"`` /
``"sector0"`` / ``"concat"``) RECOMBINES the ≤4 sector results into ONE
value so the stage is ``stream → stream`` and chains / nests; the
sentinel ``combine = "none"`` instead yields the per-sector LIST (a
terminal 1→N fan-out — chaining past it raises a guided error).

Any kwargs beyond the discriminators are forwarded to the underlying
cascade op (``max_denominator``, ``fine_scale``, …).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Union

from ._chain import Chain, chain as _chain_factory

if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover — 3.10-only branch
    import tomli as _toml  # type: ignore[no-redef]


# Keys the TOML schema reserves as discriminators / control words —
# anything else in a stage dict is forwarded as cascade-op kwargs.
_RESERVED_STAGE_KEYS = frozenset({
    "op",
    "loop_n", "sub_chain",
    "fold_init", "fold_op",
    "reduce_op",
    "parallel_body", "n_sectors", "combine",
})


def _toml_loads_native(spec: str) -> "Any":
    """Parse a TOML chain spec via the C ``srmech_dsl_toml_chain_to_json`` bridge.

    Returns the parsed dict (the ``build_chain_from_dict`` IR) when the native
    lib is present AND the C ``srmech_toml`` parser accepts the document, else
    ``None`` so :func:`build_chain_from_toml_str` falls back to the stdlib
    ``tomllib`` parse (rc103 inform-don't-limit — the C parser is the DEFAULT
    path, the pure parser the fallback; both yield the same dict / raise the same
    ``TOMLDecodeError`` on genuine syntax errors). numpy-free, no import cost when
    native is absent.
    """
    try:
        from srmech.amsc import _native
    except Exception:
        return None
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    lib = _native.LIB
    if not (hasattr(lib, "srmech_dsl_toml_chain_to_json")
            and hasattr(lib, "srmech_dsl_toml_chain_to_json_arena_bytes")):
        return None
    import ctypes
    import json
    src = spec.encode("utf-8")
    ws_bytes = int(lib.srmech_dsl_toml_chain_to_json_arena_bytes(len(src)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = lib.srmech_dsl_toml_chain_to_json(
        src, len(src), ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
    if rc != _native.SRMECH_OK:
        return None
    try:
        data = json.loads(out.raw[:out_len.value].decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def load_chain_toml(path: Union[str, Path]) -> Dict[str, Any]:
    """Parse a TOML chain-spec file; return the raw parsed dict.

    Separated from :func:`build_chain_from_toml` so callers (tests,
    ``visualize``) can inspect / mutate the parsed dict before
    materialising it.
    """
    path = Path(path)
    with open(path, "rb") as fh:
        return _toml.load(fh)


def build_chain_from_toml(path: Union[str, Path]) -> Chain:
    """Load a TOML chain spec from disk and build the matching Chain.

    The host reads the file bytes (unavoidable host I/O); the TOML PARSE then
    routes through :func:`build_chain_from_toml_str` — the C
    ``srmech_dsl_toml_chain_to_json`` bridge when native is present (rc182), the
    stdlib ``tomllib`` otherwise.
    """
    spec = Path(path).read_text(encoding="utf-8")
    return build_chain_from_toml_str(spec)


def build_chain_from_toml_str(spec: str) -> Chain:
    """Build a Chain from an in-memory TOML chain-spec *string*.

    The string counterpart of :func:`build_chain_from_toml` (which reads
    from a path). Lets a caller author a chain spec inline and
    materialise it without writing a file first — the load-bearing entry
    point for the v0.5.0rc12 ``srmech.dsl.run_toml_chain`` ToolEntry, so
    an LLM can compose AND run a cascade in a single tool call.

    Parameters
    ----------
    spec
        A TOML document with a ``[chain]`` table + ``[[stage]]`` array
        entries (the same schema :func:`build_chain_from_toml` reads
        from disk).

    Returns
    -------
    Chain
        The constructed pipeline.

    Raises
    ------
    TypeError
        If ``spec`` is not a string.
    tomllib.TOMLDecodeError
        On malformed TOML.
    ValueError
        On schema mismatch (propagated from
        :func:`build_chain_from_dict`).
    """
    if not isinstance(spec, str):
        raise TypeError(
            f"build_chain_from_toml_str: spec must be a str of TOML; "
            f"got {type(spec).__name__}"
        )
    # rc182: the TOML parse routes through the C srmech_toml parser (the
    # build_chain_from_dict IR emitted as canonical JSON); a native-absent build
    # or a C-parser decline falls back to the stdlib tomllib (same dict / same
    # TOMLDecodeError on a genuine syntax error).
    data = _toml_loads_native(spec)
    if data is None:
        data = _toml.loads(spec)
    return build_chain_from_dict(data)


def build_chain_from_dict(data: Dict[str, Any]) -> Chain:
    """Materialise a Chain from an already-parsed TOML dict.

    Parameters
    ----------
    data
        Parsed TOML data with ``[chain]`` + ``[[stage]]`` array entries.

    Returns
    -------
    Chain
        The constructed pipeline.

    Raises
    ------
    ValueError
        On schema mismatch — missing required sections, ambiguous
        stage discriminators, unknown stage shape, etc.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"chain spec must be a TOML table; got {type(data).__name__}"
        )
    chain_section = data.get("chain", {})
    if not isinstance(chain_section, dict):
        raise ValueError(
            f"[chain] section must be a table; got "
            f"{type(chain_section).__name__}"
        )
    name = chain_section.get("name", "chain")
    if not isinstance(name, str):
        raise ValueError(
            f"[chain].name must be a string; got {type(name).__name__}"
        )

    stages: List[Dict[str, Any]] = data.get("stage", [])
    if not isinstance(stages, list):
        raise ValueError(
            f"[[stage]] must be an array of tables; got "
            f"{type(stages).__name__}"
        )

    ch = _chain_factory(name)
    for idx, stage in enumerate(stages):
        if not isinstance(stage, dict):
            raise ValueError(
                f"stage {idx} must be a table; got {type(stage).__name__}"
            )
        _apply_stage_to_chain(ch, stage, idx)
    return ch


def _apply_stage_to_chain(
    ch: Chain, stage: Dict[str, Any], idx: int,
) -> None:
    """Dispatch one parsed stage-dict to the right Chain builder method."""
    # Discriminator priority: op > loop > fold > reduce. Exactly one
    # discriminator must be present per stage.
    has_op = "op" in stage
    has_loop = "loop_n" in stage or "sub_chain" in stage
    has_fold = "fold_init" in stage or "fold_op" in stage
    has_reduce = "reduce_op" in stage
    has_parallel = "parallel_body" in stage
    chosen = sum([has_op, has_loop, has_fold, has_reduce, has_parallel])
    if chosen == 0:
        raise ValueError(
            f"stage {idx} has no discriminator; expected one of "
            f"`op`, `loop_n`+`sub_chain`, `fold_init`+`fold_op`, "
            f"`reduce_op`, or `parallel_body`"
        )
    if chosen > 1:
        raise ValueError(
            f"stage {idx} has multiple discriminators "
            f"(op / loop_n / fold_op / reduce_op / parallel_body); "
            f"pick exactly one"
        )

    kwargs = {k: v for k, v in stage.items() if k not in _RESERVED_STAGE_KEYS}

    if has_op:
        op_name = stage["op"]
        if not isinstance(op_name, str):
            raise ValueError(
                f"stage {idx} `op` must be a string; got "
                f"{type(op_name).__name__}"
            )
        ch.then(op_name, **kwargs)
        return

    if has_loop:
        if "loop_n" not in stage or "sub_chain" not in stage:
            raise ValueError(
                f"stage {idx} loop requires both `loop_n` and `sub_chain`"
            )
        loop_n = stage["loop_n"]
        if not isinstance(loop_n, int) or isinstance(loop_n, bool):
            raise ValueError(
                f"stage {idx} `loop_n` must be a non-negative int; got "
                f"{loop_n!r}"
            )
        # sub_chain may be either a list of stage dicts (the natural
        # TOML nesting `[[stage.sub_chain]]`) or a fully-shaped chain
        # dict with its own [chain] section.
        sub_raw = stage["sub_chain"]
        if isinstance(sub_raw, list):
            sub_chain = build_chain_from_dict({
                "chain": {"name": f"{ch.name}.sub{idx}"},
                "stage": sub_raw,
            })
        elif isinstance(sub_raw, dict):
            sub_chain = build_chain_from_dict(sub_raw)
        else:
            raise ValueError(
                f"stage {idx} `sub_chain` must be a list of stages or "
                f"a chain dict; got {type(sub_raw).__name__}"
            )
        ch.loop(loop_n, sub_chain)
        return

    if has_fold:
        if "fold_init" not in stage or "fold_op" not in stage:
            raise ValueError(
                f"stage {idx} fold requires both `fold_init` and `fold_op`"
            )
        fold_op = stage["fold_op"]
        if not isinstance(fold_op, str):
            raise ValueError(
                f"stage {idx} `fold_op` must be a string; got "
                f"{type(fold_op).__name__}"
            )
        ch.fold(stage["fold_init"], fold_op, **kwargs)
        return

    if has_reduce:
        reduce_op = stage["reduce_op"]
        if not isinstance(reduce_op, str):
            raise ValueError(
                f"stage {idx} `reduce_op` must be a string; got "
                f"{type(reduce_op).__name__}"
            )
        ch.reduce(reduce_op, **kwargs)
        return

    # has_parallel — the Klein-4 four-sector fan-out special form.
    parallel_body = stage["parallel_body"]
    if not isinstance(parallel_body, str):
        raise ValueError(
            f"stage {idx} `parallel_body` must be a string (the NAME of a "
            f"unary cascade op to fan across sectors); got "
            f"{type(parallel_body).__name__}"
        )
    n_sectors = stage.get("n_sectors", 4)
    if not isinstance(n_sectors, int) or isinstance(n_sectors, bool):
        raise ValueError(
            f"stage {idx} `n_sectors` must be an int in 1..4; got {n_sectors!r}"
        )
    # rc12 composability: `combine` decides the stage output shape. Default
    # "bundle" (recombine → composable stream, chains / nests); the string
    # "none"/"null" maps to Python None (the per-sector list, a TERMINAL
    # fan-out). TOML can't express None directly, hence the sentinel.
    combine = stage.get("combine", "bundle")
    if not isinstance(combine, str):
        raise ValueError(
            f"stage {idx} `combine` must be a string (a reducer name "
            f"'bundle'/'mean'/'sector0'/'concat', or 'none' for the "
            f"per-sector list); got {type(combine).__name__}"
        )
    combine_arg = None if combine.lower() in ("none", "null") else combine
    # Forward non-reserved stage keys as the body op's bound kwargs (e.g.
    # `orientation = -1` for parallel_body="reorient") — UPSTREAM_NOTES §16.1
    # parallel_body= completion; mirrors the `op=` → then(**kwargs) path.
    ch.parallel_sectors(
        parallel_body, n_sectors=n_sectors, combine=combine_arg, **kwargs,
    )


__all__ = [
    "load_chain_toml",
    "build_chain_from_toml",
    "build_chain_from_toml_str",
    "build_chain_from_dict",
]
