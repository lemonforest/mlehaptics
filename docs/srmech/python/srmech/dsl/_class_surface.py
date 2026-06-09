"""Declarative, one-shot DSL surface for user-declared classes (rc40).

The DSL companion to :mod:`srmech.dsl._class_catalog` — the LLM-/CLI-ergonomic
entry points that introspect and *run* a user-declared ``[class]`` (the rc39
``CatalogClass``) in ONE call. The fluent surface holds a live instance and
chains method calls; that shape isn't tool-ergonomic, so this module exposes the
**stateless** surface instead: pass the instance state in as ``fields``, get the
result + the post-call state back (the name+UUID handle dual-grammar at the
functional level — the caller threads the state, no live handle required).

* :func:`describe_class` / :func:`list_class_surface` — JSON-able introspection
  (fields + methods + binds + provenance) so an LLM / CLI knows what a class
  offers before calling.
* :func:`run_class_method` — construct from ``fields``, invoke ``method`` with
  ``args``, return ``{"result", "fields", ...}``. The one-shot run entry point
  CLI (rc41) + the tool_schema/MCP surface (rc41) compose on.

Framework reading: Class E (catalog enumeration) ∘ Class F (descriptor render)
for the introspection; Class M (the CatalogClass bind-dispatch) for the run. No
new primitive — thin one-shot façades over the rc39 loader.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ._class_catalog import get_class_descriptor, list_classes, make_class


def describe_class(name: str) -> Dict[str, Any]:
    """Return a JSON-able description of the user-declared class ``name``.

    ``{"name", "kind", "doc", "fields": {field: type}, "methods": {method:
    {"op", "binds", "doc", ["appends"|"sets"]}}, "provenance"}``. Sourced from
    the on-disk ``[class]`` descriptor (the SSoT), so it's always in lockstep
    with what :func:`run_class_method` can actually construct + invoke.
    """
    desc = get_class_descriptor(name)
    cls = desc.get("class", {})
    methods: Dict[str, Any] = {}
    for mname, mspec in cls.get("method", {}).items():
        entry: Dict[str, Any] = {
            "op": str(mspec.get("op", "")),
            "binds": [str(b) for b in mspec.get("binds", [])],
            "doc": str(mspec.get("doc", "")),
        }
        if "appends" in mspec:
            entry["appends"] = str(mspec["appends"])
        if "sets" in mspec:
            entry["sets"] = str(mspec["sets"])
        methods[mname] = entry
    prov = str(desc.get("_provenance", "srmech"))
    return {
        "name": str(cls.get("name", name)),
        "kind": str(cls.get("kind", "")),
        "doc": str(cls.get("doc", "")),
        "fields": {str(k): str(v) for k, v in cls.get("field", {}).items()},
        "methods": methods,
        # MPM provenance tier: "srmech" (A-tier shipped seed) or "user"
        # (a bring-your-own register_class_dir class, attested to its hash).
        "provenance": "srmech" if prov == "srmech" else "user",
    }


def list_class_surface() -> List[Dict[str, Any]]:
    """Enumerate every user-declared class (the discovery companion).

    Returns ``[describe_class(name) for name in list_classes()]`` — the shipped
    seed (genome) PLUS any bring-your-own classes from a ``register_class_dir``
    dir. The introspection view CLI ``srmech class list`` + the LLM tool surface
    consume so a caller can pick a class + method before running.
    """
    return [describe_class(name) for name in list_classes()]


def run_class_method(
    class_name: str,
    method: str,
    *,
    fields: Optional[Dict[str, Any]] = None,
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct ``class_name`` from ``fields``, invoke ``method`` with ``args``.

    The stateless one-shot run: a fresh instance is built from the ``fields``
    dict, ``method`` is called with the ``args`` dict, and the result is returned
    alongside the instance's post-call field state — so a caller (CLI / LLM /
    bus) threads the state across calls without holding a live object.

    Returns ``{"class", "method", "result", "fields"}`` where ``fields`` is the
    instance's state AFTER the call (so an ``appends``/``sets`` method's mutation
    is visible). ``fields`` and ``args`` are plain dicts (MCP-grammar friendly:
    no ``**kwargs`` on the public signature).
    """
    factory = make_class(class_name)
    instance = factory(**(fields or {}))
    bound = getattr(instance, method)
    result = bound(**(args or {}))
    return {
        "class": class_name,
        "method": method,
        "result": result,
        "fields": instance.fields,
    }


__all__ = ["describe_class", "list_class_surface", "run_class_method"]
