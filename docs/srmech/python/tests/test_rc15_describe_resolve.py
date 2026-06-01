"""v0.6.0rc15 — the self-recognition READS voxel.

Top-level ``srmech.describe()`` (graduated from ``srmech.introspect``), fuzzy
``ToolSchema.resolve()`` / ``resolve_all()`` (a bare leaf or dotted suffix
resolves to its fully-qualified name), and an iterable ``ToolSchema``. All
pure-Python introspection surface — no native dependency, runs regardless of
whether ``libsrmech`` is present.
"""

from collections import Counter

import pytest

import srmech
from srmech.amsc.tool_schema import get_tool_schema, warmup_all


def _schema():
    warmup_all()
    return get_tool_schema()


# ── top-level describe() help-anchor (graduated, not forked) ──────────────

def test_describe_is_top_level_and_in_all():
    assert hasattr(srmech, "describe"), "srmech.describe must be top-level"
    assert callable(srmech.describe)
    assert "describe" in srmech.__all__
    assert "describe" in dir(srmech)


def test_describe_is_the_introspect_function():
    # graduated to the top namespace, NOT a fork
    assert srmech.describe is srmech.introspect.describe


def test_describe_shape_and_agreement():
    d = srmech.describe()
    assert isinstance(d, dict)
    assert d["srmech_version"] == srmech.__version__
    assert {"has_native", "abi_version", "native_version"} <= set(d["native"])
    assert "total" in d["tools"] and "by_category" in d["tools"]
    assert isinstance(d["categories"], list)
    # the help-anchor's count agrees with the registry it summarises
    assert d["tools"]["total"] == len(get_tool_schema().tools)


# ── ToolSchema iterability + len (the 'object is not iterable' footgun) ───

def test_toolschema_is_iterable_and_sized():
    schema = _schema()
    listed = [t for t in schema]            # `for t in schema` no longer raises
    assert listed == list(schema.tools)
    assert len(schema) == len(schema.tools) == len(listed)
    assert len(schema) > 0


# ── fuzzy resolve() / resolve_all() ───────────────────────────────────────

def test_resolve_exact_full_name_matches_lookup():
    schema = _schema()
    first = schema.tools[0]
    assert schema.resolve(first.name) is first
    assert schema.lookup(first.name) is first  # exact path unchanged


def test_resolve_unique_leaf_and_dotted_suffix():
    schema = _schema()
    leaves = Counter(t.name.rsplit(".", 1)[-1] for t in schema.tools)
    unique_leaf = next(
        t.name.rsplit(".", 1)[-1]
        for t in schema.tools
        if leaves[t.name.rsplit(".", 1)[-1]] == 1
    )
    target = next(
        t for t in schema.tools if t.name.rsplit(".", 1)[-1] == unique_leaf
    )
    # a bare leaf resolves in one call
    assert schema.resolve(unique_leaf) is target
    # any dotted suffix resolves too
    if "." in target.name:
        suffix = target.name.split(".", 1)[1]
        assert schema.resolve(suffix) is target


def test_resolve_miss_returns_none():
    schema = _schema()
    assert schema.resolve("definitely_not_a_real_tool_xyz") is None
    assert schema.resolve_all("definitely_not_a_real_tool_xyz") == ()


def test_resolve_ambiguous_never_silently_picks():
    schema = _schema()
    leaves = Counter(t.name.rsplit(".", 1)[-1] for t in schema.tools)
    ambiguous = [leaf for leaf, n in leaves.items() if n >= 2]
    if not ambiguous:
        pytest.skip("no ambiguous leaf in the current registry")
    leaf = ambiguous[0]
    assert schema.resolve(leaf) is None            # never silently picks one
    assert len(schema.resolve_all(leaf)) >= 2       # but lists all candidates
