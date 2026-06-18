"""Declarative, one-shot DSL entry points for LLM tool use (v0.5.0rc12).

The fluent :class:`srmech.dsl.Chain` builder composes a cascade by
method-chaining (``chain().then(...).loop(...)...``). That shape is NOT
LLM-tool-ergonomic — a single tool call cannot chain builder methods.
This module exposes the *declarative* surface instead: callables that do
real work in ONE call, so an LLM can author a TOML cascade spec AND run
it atomically.

The two ToolEntries registered in
:func:`srmech.amsc.tool_schema._register_dsl_tools` resolve (via the
dotted-name walk in :mod:`srmech.mcp._tools`) to:

* :func:`run_toml_chain` — ``srmech.dsl.run_toml_chain`` — parse an
  inline TOML chain spec, build the :class:`Chain`, run it against an
  input value, return the result.
* :func:`list_catalog_ops` — ``srmech.dsl.list_catalog_ops`` — enumerate
  the 11 cascade-catalog ops with their A–N class + 1-line purpose, so an
  LLM knows which op names a spec may use.

Both take plain keyword parameters (``spec`` / ``input_value`` and no
params respectively) — no ``*args`` / ``**kwargs`` — so the rc10
property-key grammar holds and ``invoke_tool``'s ``fn(**coerced)`` can
call them directly (no VAR_POSITIONAL unpack needed).

Framework reading
-----------------
The DSL composes Class M (cross-class bind) over the cascade catalog;
:func:`list_catalog_ops` is Class E (catalog enumeration) ∘ Class F
(render of each descriptor's class + purpose). No new primitive class is
introduced — these are thin one-shot façades over the rc8 DSL.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ._catalog import get_descriptor, list_cascade_ops
from ._toml_chain import build_chain_from_toml_str


def run_toml_chain(spec: str, input_value: Any) -> Any:
    """Build a cascade from an inline TOML chain spec and run it.

    The one-shot LLM entry point: author a chain spec as a TOML string,
    feed an input value, get the chain result — all in a single call.
    Equivalent to ``build_chain_from_toml_str(spec).run(input_value)``.

    Parameters
    ----------
    spec
        A TOML chain spec: a ``[chain]`` table plus ``[[stage]]`` array
        entries. Each stage carries exactly one discriminator — ``op``
        (``chain.then``), ``loop_n`` + ``sub_chain`` (``chain.loop``),
        ``fold_init`` + ``fold_op`` (``chain.fold``), or ``reduce_op``
        (``chain.reduce``); any other keys forward as cascade-op kwargs.
        Example::

            [chain]
            name = "demo"

            [[stage]]
            op = "chiral_flip"

    input_value
        The seed value fed to the first stage. A JSON-shaped value
        (number / string / list / dict) on the MCP / Anthropic wire;
        passed through to ``Chain.run`` unchanged.

    Returns
    -------
    Any
        The output of the final stage. An empty chain returns
        ``input_value`` unchanged (the identity chain).

    Raises
    ------
    TypeError
        If ``spec`` is not a string.
    ValueError
        On a malformed spec or an unknown cascade op (propagated from
        the builder / the catalog lookup).
    """
    chain = build_chain_from_toml_str(spec)
    return chain.run(input_value)


def list_catalog_ops() -> List[Dict[str, str]]:
    """Enumerate the cascade-catalog ops available to a chain spec.

    The discovery companion to :func:`run_toml_chain`: returns one
    record per op so an LLM can pick valid ``op`` / ``fold_op`` /
    ``reduce_op`` names (and read each op's A–N class + purpose) before
    authoring a spec. Sourced from the on-disk TOML descriptors (the
    cascade-catalog SSoT), so the list is always in lockstep with the
    ops the runner can actually resolve.

    Returns
    -------
    list[dict]
        ``[{"name": str, "class": <A–N class composition>, "purpose":
        str, "kind": "stage" | "combinator", "provenance": "srmech" |
        "user"}, ...]``, sorted ascending by ``name``. Includes the 11
        shipped ops (the 8 lean-ISA atoms/composites + the v0.7.0rc8
        autocorrelation + the v0.6.0 parallel_sector_dispatch + kuramoto_step)
        PLUS any bring-your-own
        ops from a registered catalog dir (F289 D2). ``kind`` is the DSL
        role: ``"stage"`` = a plain ``op=`` value→value stage;
        ``"combinator"`` = a higher-order special form (``parallel_sector_dispatch``)
        driven by its own discriminator (the ``parallel`` fan-out), NOT
        usable as a plain ``op=`` stage. ``provenance`` is the MPM tier:
        ``"srmech"`` (A-tier shipped) or ``"user"`` (B-tier, attested to the
        user's own descriptor — a bring-your-own op).
    """
    out: List[Dict[str, str]] = []
    for name in list_cascade_ops():
        desc = get_descriptor(name)
        cascade = desc.get("cascade", {})
        kind = str(cascade.get("kind", "stage")) or "stage"
        prov = str(desc.get("_provenance", "srmech"))
        out.append({
            "name": name,
            "class": str(cascade.get("class_composition", "")),
            "purpose": str(cascade.get("purpose", "")),
            # DSL role: "stage" (a plain `op=` value→value stage) or
            # "combinator" (a higher-order special form — drive via its
            # own discriminator, e.g. the `parallel` fan-out, NOT `op=`).
            "kind": kind,
            # MPM provenance tier: "srmech" (A-tier shipped op) or "user"
            # (a bring-your-own catalog-dir op, attested to its own
            # descriptor hash, NOT a shipped primitive; F289 D2).
            "provenance": "srmech" if prov == "srmech" else "user",
        })
    return out


def list_ops(*, source_keys: Any = None) -> List[Dict[str, str]]:
    """Unify the two op-discovery registries into ONE list (RBS-LM §17 U3).

    Before this, the DSL's value-transform cascade ops (:func:`list_catalog_ops`)
    and the AMSC catalog-declared operator chains
    (:func:`srmech.amsc.catalog.list_catalog_chains`) were **two disjoint
    surfaces** — a kernel chain declared on a text-catalog was invisible to the
    DSL op list. ``list_ops`` returns BOTH, every record carrying a uniform
    ``kind`` + ``provenance`` so an LLM / CLI sees the whole authorable surface
    in one call.

    Each record is ``{"name", "class", "purpose", "kind", "provenance"}``:

    * **cascade-ops** — every :func:`list_catalog_ops` record, with its existing
      ``kind`` (``"stage"`` / ``"combinator"``) and ``provenance``
      (``"srmech"`` A-tier / ``"user"`` B-tier BYO).
    * **catalog-chains** — for each registered attested source (or each key in
      ``source_keys``), every declared chain, tagged ``kind="catalog-chain"``
      and ``provenance=f"catalog:{source_key}"`` (``class`` = the chain's A–N
      class list, ``purpose`` = its summary).

    ``source_keys`` (an iterable of source-key strings) restricts the
    catalog-chain half; ``None`` (default) auto-discovers every registered
    attested source. A base srmech install with no registered catalog returns
    just the cascade-ops (the catalog-chain half is empty — correct; nothing is
    registered). Sorted by ``(kind, name)``. Framework reading: Class E
    (catalog enumeration) over BOTH registries at once — the unification the
    §17 ask names.
    """
    out: List[Dict[str, str]] = list(list_catalog_ops())
    keys = source_keys
    if keys is None:
        try:  # auto-discover every registered attested source
            from srmech.amsc.catalog import list_attested_sources
            srcs = list_attested_sources()
            if isinstance(srcs, dict):
                pool = srcs.get("sources")
                if isinstance(pool, dict):
                    keys = list(pool.keys())
                elif isinstance(pool, list):
                    # The shipped shape is a list of source dicts whose
                    # source-key field is `key` (NOT `source_key`/`name`);
                    # fall back to the alternates for robustness.
                    keys = [
                        (s.get("key") or s.get("source_key") or s.get("name"))
                        if isinstance(s, dict) else s
                        for s in pool
                    ]
                    keys = [k for k in keys if k]
                else:
                    keys = list(srcs.get("source_keys", []) or [])
            else:
                keys = []
        except Exception:  # no AMSC catalogs registered → cascade-ops only
            keys = []
    try:
        from srmech.amsc.catalog import list_catalog_chains
    except Exception:
        list_catalog_chains = None  # type: ignore[assignment]
    for sk in keys or []:
        if not sk or list_catalog_chains is None:
            continue
        try:
            res = list_catalog_chains(sk)
        except Exception:
            continue
        if not isinstance(res, dict) or not res.get("ok"):
            continue
        for c in res.get("chains", []) or []:
            classes = c.get("classes")
            out.append({
                "name": str(c.get("name", "")),
                "class": ", ".join(classes) if isinstance(classes, list) else str(classes or ""),
                "purpose": str(c.get("summary", "")),
                "kind": "catalog-chain",
                "provenance": f"catalog:{sk}",
            })
    out.sort(key=lambda r: (r.get("kind", ""), r.get("name", "")))
    return out


__all__ = ["run_toml_chain", "list_catalog_ops", "list_ops"]
