"""Dotted-name -> live callable resolution (core; rc413, `#T1094`).

This is the **robust** dotted-name walker: given ``a.b.c.d`` it tries every
split point from the most-specific module prefix backwards, importing what
imports cleanly and walking the remainder as attributes. It therefore resolves
names whose tail is more than one attribute hop deep — ``module.Class.method``,
``module.obj.attr.fn`` — which a naive last-dot ``rpartition`` cannot.

WHY IT LIVES IN CORE
====================
Three call sites need it and only one of them is peripheral:

* :func:`srmech._handles.resolve_operator_name` — the ``chiral_dual`` operator
  name-grammar arm (core).
* :func:`srmech.dsl._alias._resolve_target` — the ``[[alias]]`` config rung
  (core).
* :func:`srmech.mcp._tools.invoke_tool` — every ToolEntry invocation (the
  peripheral MCP adapter, and by volume the largest caller).

Through rc412 the function was defined in ``srmech.mcp._tools``, so the two
core callers imported *upward* into the MCP adapter — ``rm -rf srmech/mcp``
took the alias rung and the operator-name grammar down with it. ADR-0009 §4
exempts ``srmech.mcp`` / ``srmech.llm`` from the capability invariant precisely
because they are host glue; core depending on host glue inverts that. Moving
the walker here makes every edge point INTO core and leaves the MCP adapter
genuinely removable.

RELATIONSHIP TO THE `[class]` RUNG'S OWN RESOLVER
=================================================
:func:`srmech.dsl._class_catalog._resolve_op` is a **separate, deliberately
weaker** resolver: it splits on the last dot only. It is NOT a duplicate to be
folded into this one. Measured at rc413 over real
``module.Class.method`` triples enumerated from the shipped package
(N = 307, every class defined in its own module, public methods only): this
walker resolves all of them and ``_resolve_op`` raises ``ModuleNotFoundError``
on all of them. Unifying them would therefore *widen* what a user-registered
``[class]`` TOML may bind — a behaviour change to the class rung with its own
design question and its own test, not a refactor. Over every population the
package actually ships — the whole ToolEntry registry, the class-catalog
op-refs, the alias targets, the cascade-catalog dotted ops — the two agree
exactly, with ZERO divergent names in any of them. (A zero census is
basis-free, so no denominator is restated here; the registry total in
particular is deliberately never written as a literal in shipped source, per
``tests/test_owner_axis_rc410.py``. The per-population counts as measured at
rc413 are in the CHANGELOG entry.) The split costs nothing today and is left
standing on purpose.

THE ``ismodule`` INNER FALLBACK IS LOAD-BEARING — DO NOT "CLEAN IT UP"
======================================================================
It looks dead and is not. It rescues the shape "submodule ``X`` re-exports a
callable also named ``X``, and the parent package's attribute ``X`` is bound to
the MODULE rather than the function". Measured at rc413: 27 such name
collisions exist in the tree, and for 24 of them the parent attribute is the
module. Two are reachable in a bare ``import srmech`` interpreter and resolve
ONLY via this fallback — ``srmech.apokatastasis.zeilberger`` and
``srmech.introspect.search``; both raise without it. (The
``srmech.cascade.sedenion_register`` case cited in the original comment is
NOT one of them — ``srmech/cascade/__init__.py``'s ``from .sedenion_register
import sedenion_register`` rebinds the package attribute back to the function,
so that name resolves without the fallback. The fallback was justified by an
example that had since stopped needing it, which is how it came to look dead.)
``tests/test_resolve_dotted_callable_rc413.py`` pins both survivors. (That
path is NOT importable as ``srmech.tests.*`` — the suite lives BESIDE the
package, not inside it.)
"""

from __future__ import annotations

import importlib
import inspect
from typing import Any, Callable

__all__ = ["DottedNameError", "resolve_dotted_callable"]


class DottedNameError(Exception):
    """Raised when a dotted name does not resolve to a live callable."""


def resolve_dotted_callable(name: str) -> Callable[..., Any]:
    """Walk a dotted name to its live callable.

    For ``a.b.c.d``: try ``import a.b.c`` then ``getattr(mod, "d")``;
    fall back to splitting at successively earlier dots and importing whatever
    prefix imports cleanly, walking the remainder as attributes. Raises
    :class:`DottedNameError` on failure.
    """
    assert name, "resolve: name must be non-empty"
    parts = name.split(".")
    if len(parts) < 2:
        raise DottedNameError(
            f"tool name {name!r} has no module prefix; "
            f"cannot resolve to a Python callable"
        )

    # Try the most-specific module prefix first, then back off.
    # e.g. for "srmech.cascade.chiral_flip" we try
    # importing "srmech.cascade" then attr "chiral_flip".
    for split_idx in range(len(parts) - 1, 0, -1):
        mod_name = ".".join(parts[:split_idx])
        attr_path = parts[split_idx:]
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        obj: Any = mod
        try:
            for a in attr_path:
                obj = getattr(obj, a)
        except AttributeError:
            continue
        if not callable(obj):
            # Name-collision case: a submodule whose name equals a
            # re-exported callable. Importing the submodule makes Python bind
            # the package attribute to the module object, so ``getattr`` here
            # yields a non-callable module. Prefer the same-named callable
            # defined inside it — the "module X re-exports callable X"
            # convention. LIVE, not dead: see the module docstring for the two
            # measured names that resolve only through this branch.
            if inspect.ismodule(obj):
                inner = getattr(obj, attr_path[-1], None)
                if callable(inner):
                    return inner
            continue
        return obj
    raise DottedNameError(
        f"tool name {name!r} did not resolve to any importable callable"
    )
