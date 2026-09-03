"""rc413 (`#T1094`) — the dotted-callable walker after its move to core.

Three things are pinned here, each of which a plausible future cleanup breaks.

1. **The walker lives in core and the MCP adapter no longer defines it.** The
   purity claim rc413 serves is that ``rm -rf srmech/mcp srmech/llm`` leaves a
   working core, and the walker had two *core* callers importing upward into
   ``srmech.mcp``.

2. **The ``inspect.ismodule`` inner fallback is LIVE.** It reads as dead code —
   the original comment justified it with the 16-slot register's module/factory
   collision — a case that stopped needing it, and that rc464 removed outright
   (``srmech.cascade.cd_register`` is the same collision and also does not need
   it) — and a sweep over the ToolEntry
   registry never fires it. Both observations are true and the conclusion
   "therefore remove it" is wrong: two shipped names resolve *only* through
   that branch. This test is the evidence, so the claim cannot be re-made
   without a red build.

3. **The `[class]` rung's weaker resolver still diverges.** Not a bug — a
   deliberate narrower contract (ADR-0004 §4). Pinned so that "unify the two
   resolvers" has to be a decision someone makes on purpose.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import subprocess
import sys
import textwrap

import pytest

import srmech
from srmech._resolve import DottedNameError, resolve_dotted_callable


# ── 1. the relocation itself ──────────────────────────────────────────


def test_walker_is_defined_in_core_not_in_the_mcp_adapter() -> None:
    """The function's home is ``srmech._resolve``, a top-level core module."""
    assert resolve_dotted_callable.__module__ == "srmech._resolve"


def test_mcp_tools_no_longer_defines_its_own_walker() -> None:
    """No ``_resolve_dotted_callable`` survives in the adapter.

    A re-export left behind "for compatibility" would keep the old import
    working and quietly re-establish the edge this rc removed.
    """
    from srmech.mcp import _tools

    assert not hasattr(_tools, "_resolve_dotted_callable"), (
        "srmech.mcp._tools still exposes _resolve_dotted_callable — rc413 "
        "moved it to srmech._resolve with no legacy alias (no-legacy-path "
        "discipline); a shim here re-creates the core -> mcp import edge."
    )


def test_core_modules_do_not_import_the_mcp_adapter_for_resolution() -> None:
    """``srmech._handles`` / ``srmech.dsl._alias`` reach into core, not mcp."""
    for mod_name in ("srmech._handles", "srmech.dsl._alias"):
        src = inspect.getsource(importlib.import_module(mod_name))
        assert "srmech.mcp._tools import" not in src, (
            f"{mod_name} still imports from srmech.mcp._tools — the whole "
            f"point of rc413 is that core does not depend on the ADR-0009 §4 "
            f"host-glue layer."
        )


def test_resolution_failure_raises_the_core_error_not_the_mcp_one() -> None:
    with pytest.raises(DottedNameError):
        resolve_dotted_callable("srmech.does.not.exist.at_all")
    with pytest.raises(DottedNameError):
        resolve_dotted_callable("nodots")


def test_invoke_tool_still_surfaces_resolution_failure_as_mcp_error() -> None:
    """The MCP layer's own contract is unchanged: ``_server.handle`` and the
    Anthropic adapter both catch ``MCPToolError`` to turn a bad name into a
    JSON-RPC error response rather than a traceback."""
    from srmech.mcp._tools import MCPToolError, invoke_tool

    with pytest.raises(MCPToolError):
        invoke_tool("srmech.definitely.not.a.tool", {})


# ── 2. the ismodule fallback is live ──────────────────────────────────

#: Names measured at rc413 to resolve ONLY via the ``inspect.ismodule`` inner
#: fallback: a submodule whose name equals a callable it exports, where the
#: parent package's attribute is bound to the MODULE. 27 such collisions exist
#: in the tree; 24 leave the parent attribute shadowed; these two are reachable
#: from a bare ``import srmech`` interpreter.
ISMODULE_FALLBACK_SURVIVORS = (
    "srmech.apokatastasis.zeilberger",
    "srmech.introspect.search",
)


@pytest.mark.parametrize("dotted", ISMODULE_FALLBACK_SURVIVORS)
def test_ismodule_fallback_names_resolve_to_a_callable(dotted: str) -> None:
    fn = resolve_dotted_callable(dotted)
    assert callable(fn)
    assert not inspect.ismodule(fn), (
        f"{dotted} resolved to a MODULE, not the same-named callable inside "
        f"it — the ismodule inner fallback is what distinguishes these"
    )
    assert fn.__name__ == dotted.rpartition(".")[2]


@pytest.mark.parametrize("dotted", ISMODULE_FALLBACK_SURVIVORS)
def test_these_names_are_genuinely_module_shadowed(dotted: str) -> None:
    """The premise of the test above: the parent attribute IS the module.

    Without this, the parametrised test would pass vacuously if the tree ever
    stopped shadowing these names — it would be pinning nothing, and the
    "the branch is dead" claim would become true without anything saying so.
    """
    pkg_name, _, leaf = dotted.rpartition(".")
    pkg = importlib.import_module(pkg_name)
    attr = getattr(pkg, leaf, None)
    assert inspect.ismodule(attr), (
        f"{dotted}: parent attribute is no longer the module ({attr!r}). The "
        f"ismodule fallback may now be genuinely unreachable — RE-MEASURE the "
        f"whole collision set before concluding that, and if it is, remove "
        f"the branch and this test together."
    )


def test_removing_the_ismodule_fallback_would_break_those_names() -> None:
    """Counterfactual, run in a subprocess: monkeypatch ``inspect.ismodule``
    to a constant ``False`` inside the resolver's module — the exact
    observable effect of deleting the branch — and show the survivors stop
    resolving. A branch you cannot make fail is not a branch you have tested.
    """
    code = textwrap.dedent(
        """
        import srmech
        from srmech import _resolve
        _resolve.inspect.ismodule = lambda o: False   # == delete the branch
        broke = []
        for n in %r:
            try:
                _resolve.resolve_dotted_callable(n)
            except _resolve.DottedNameError:
                broke.append(n)
        print(len(broke), len(%r))
        """
        % (ISMODULE_FALLBACK_SURVIVORS, ISMODULE_FALLBACK_SURVIVORS)
    )
    res = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert res.returncode == 0, res.stderr
    broke, total = (int(x) for x in res.stdout.split())
    assert broke == total > 0, (
        f"disabling the ismodule branch broke only {broke}/{total} of the "
        f"survivors — the branch is not doing what this test claims it does"
    )


# ── 3. the [class] rung's resolver stays narrower, on purpose ─────────


def _real_module_class_method_triples(limit: int = 40) -> list:
    """Real ``module.Class.method`` names from the shipped package."""
    out: list = []
    for mi in pkgutil.walk_packages(srmech.__path__, "srmech."):
        try:
            mod = importlib.import_module(mi.name)
        except Exception:
            continue
        for cn, cls in vars(mod).items():
            if cn.startswith("_") or not inspect.isclass(cls):
                continue
            if getattr(cls, "__module__", "") != mod.__name__:
                continue
            for mn, meth in vars(cls).items():
                if mn.startswith("_") or not callable(meth):
                    continue
                out.append(f"{mod.__name__}.{cn}.{mn}")
                if len(out) >= limit:
                    return sorted(set(out))
    return sorted(set(out))


def test_class_rung_resolver_is_narrower_than_the_core_walker() -> None:
    """ADR-0004 §4: an ``[[alias]]`` target may bind ``module.Class.method``;
    a ``[class]`` descriptor's ``op`` may not. Unifying them would WIDEN the
    class rung — a behaviour change with its own test, not a refactor."""
    from srmech.dsl._class_catalog import _resolve_op

    triples = _real_module_class_method_triples()
    assert triples, "found no module.Class.method triples — the walk is blind"

    for t in triples:
        assert callable(resolve_dotted_callable(t)), f"core walker failed {t}"
        with pytest.raises(Exception):
            _resolve_op(t)


def test_class_rung_resolver_keeps_its_cache_clear_attribute() -> None:
    """``_resolve_op`` is ``lru_cache``d and tests call ``.cache_clear()``
    after mutating the catalog. rc413 left R2 alone; pin the attribute so a
    later "just unify them" cannot silently drop it."""
    from srmech.dsl._class_catalog import _resolve_op

    assert hasattr(_resolve_op, "cache_clear")


def test_shipped_populations_show_zero_divergence() -> None:
    """The two resolvers disagree totally on ``module.Class.method`` and not
    at all on anything srmech ships. Both halves matter: the first is why they
    are not interchangeable, the second is why keeping them split costs
    nothing. If this ever goes non-zero, a shipped descriptor has started
    depending on a resolver difference.
    """
    from srmech.dsl._class_catalog import _resolve_op
    from srmech.introspect.tool_schema import get_tool_schema

    names = [e.name for e in get_tool_schema().tools]
    assert names, "empty registry — this guard would observe nothing"

    divergent = []
    for n in names:
        try:
            a = resolve_dotted_callable(n)
        except Exception:
            a = None
        try:
            b = _resolve_op(n)
        except Exception:
            b = None
        if a is not b:
            divergent.append(n)

    assert not divergent, (
        f"{len(divergent)}/{len(names)} ToolEntry names now resolve "
        f"differently under the two resolvers: {divergent[:5]}"
    )
