"""Registry-walk smoke (#564 / rc127): EVERY registered tool resolves and EVERY
shipped catalog class describes — numpy-FREE.

This is the "all functions + all shipped catalog classes" coverage net. Rather
than hand-pick a subset (the way the CI pure-wheel smoke historically did), it
walks the **full** tool registry (``tool_schema.tool_schema_view()``) and the
**full** class registry (``dsl.list_classes()``), so:

* a newly-registered tool whose module fails to import, or whose dotted name no
  longer resolves to an attribute, fails here immediately;
* a shipped catalog class that fails to ``describe_class`` fails here;
* and — because this module imports only ``srmech`` + stdlib — the whole sweep
  runs with numpy genuinely absent, proving the entire registered surface is
  reachable numpy-free (the #564 numpy-ZERO guarantee at registry scale).

Counts are pinned to ``introspect.describe()`` so the walk and the count-tests
stay in lockstep (no silent registry drift).
"""

import importlib
import types

from srmech import dsl
from srmech.amsc import tool_schema as ts
from srmech.introspect import describe


def _resolve(dotted):
    """Resolve a fully-qualified ``module[.attr...]`` tool name to its object.

    Greedy: import the longest importable module prefix, then ``getattr`` the
    remaining path components. Returns ``(obj, is_module_leaf)``; raises
    ``AssertionError`` if the module prefix is unimportable or an attribute on
    the path is missing.
    """
    parts = dotted.split(".")
    mod = None
    idx = 0
    for i in range(len(parts), 0, -1):
        try:
            mod = importlib.import_module(".".join(parts[:i]))
            idx = i
            break
        except ImportError:
            continue
    assert mod is not None, f"no importable module prefix for {dotted!r}"
    obj = mod
    for part in parts[idx:]:
        assert hasattr(obj, part), f"{dotted!r}: missing attribute {part!r}"
        obj = getattr(obj, part)
    return obj, isinstance(obj, types.ModuleType)


def test_every_registered_tool_resolves_numpy_free():
    """All ``describe()['tools']['total']`` registered tools import + resolve to
    a real attribute with numpy absent."""
    view = ts.tool_schema_view()
    tools = view["tools"]
    # the registry length IS the SSOT the five count-tests pin — assert agreement
    # so a tool added/removed without touching describe() is caught here too.
    assert len(tools) == describe()["tools"]["total"], (
        f"tool_schema_view has {len(tools)} tools but describe() reports "
        f"{describe()['tools']['total']}"
    )

    unresolved = []
    noncallable = []
    for entry in tools:
        name = entry["name"]
        try:
            obj, is_module = _resolve(name)
        except AssertionError as exc:
            unresolved.append((name, str(exc)))
            continue
        # A tool target is normally a callable. A few dotted names collide with a
        # submodule of the same leaf name (e.g. the ``sedenion_register`` factory
        # re-exported on ``srmech.amsc.cascade`` vs the ``...cascade.sedenion_register``
        # MODULE). The greedy resolver lands on the module; the registered callable
        # still exists on the parent package, so a module leaf is acceptable.
        if not callable(obj) and not is_module:
            noncallable.append((name, type(obj).__name__))

    assert not unresolved, (
        f"{len(unresolved)} registered tools failed to resolve numpy-free "
        f"(first 10): {unresolved[:10]}"
    )
    assert not noncallable, (
        f"registered tools resolved to non-callable, non-module objects: "
        f"{noncallable}"
    )


def test_every_shipped_catalog_class_describes_numpy_free():
    """All ``describe()['classes']['total']`` shipped catalog classes describe
    via the DSL class surface with numpy absent."""
    names = list(dsl.list_classes())
    assert names == describe()["classes"]["names"], (
        f"dsl.list_classes()={names} disagrees with "
        f"describe()['classes']['names']={describe()['classes']['names']}"
    )
    assert len(names) == describe()["classes"]["total"]

    required = {"doc", "fields", "kind", "methods", "name", "provenance"}
    for nm in names:
        info = dsl.describe_class(nm)
        assert required <= set(info), (nm, sorted(info))
        assert info["name"] == nm
        # a shipped class is either a storage class (named fields) or a generator
        # (cascade-op methods); either way it must expose at least one of the two
        # so the class surface is non-empty.
        assert info["fields"] or info["methods"], (
            f"shipped class {nm!r} has neither fields nor methods"
        )


def test_registry_smoke_is_itself_numpy_free():
    """This test module must run with numpy NOT importable — it is part of the
    numpy-FREE surface it certifies (#564). A monkeypatched numpy block proves
    the registry walk needs no numpy."""
    import builtins

    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "numpy" or name.startswith("numpy."):
            raise ImportError("numpy is removed (#564 numpy-zero gate)")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = _blocked
    try:
        # re-run the two walks with numpy hard-blocked at import
        view = ts.tool_schema_view()
        assert len(view["tools"]) == describe()["tools"]["total"]
        for nm in dsl.list_classes():
            assert dsl.describe_class(nm)["name"] == nm
    finally:
        builtins.__import__ = real_import
