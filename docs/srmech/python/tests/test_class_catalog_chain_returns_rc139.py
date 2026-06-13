"""v0.7.5rc139 — make_class contract extension #2: ``chain`` + ``returns="self"``.

The last two method-routing primitives a rich domain object needs (the
SedenionRegister-class blockers per [[feedback_prefer_config_driven_toml_classes]]):

- **``chain``** — a method declared as a VISIBLE multi-op pipeline: a list of
  ``{op, binds, as}`` stages (instead of a single ``op``). Each stage's ``binds``
  resolve from a prior stage's ``as`` result, then call kwargs, then instance
  fields; non-(op/binds/as) keys are static stage kwargs; the method returns the
  last stage's result. The cascade composition is declared IN THE TOML (the
  config-driven point), not buried inside one flat op.
- **``returns = "self"``** — a self-returning method: the op/chain returns the new
  instance's ``{field: value}`` state-dict and a FRESH same-class instance is
  constructed (the ``navigate`` shape); ``self`` is untouched.

Pins: the chain pipeline (prior-stage threading + static stage kwargs + field/
call binds), the self-return (fresh instance, self unchanged, chainable),
``op``/``chain`` exclusivity, the widened 4-way routing exclusivity, the
``describe_class`` surfacing, the ``generate_class_descriptor`` round-trip, and
the fail-loud guards.
"""

from __future__ import annotations

import sys
import types

import pytest

if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover — 3.10-only branch
    import tomli as _toml  # type: ignore[no-redef]

from srmech.dsl import (
    describe_class,
    generate_class_descriptor,
    make_class,
    register_class_dir,
)


# ── synthetic flat ops the [class] TOML binds to ─────────────────────────────

def _add_op(a, b):
    return a + b


def _scale_op(v, factor=1):
    return v * factor


def _bump_op(count):
    """A self-returning op: returns the NEW instance's full field-dict."""
    return {"count": count + 1}


def _bad_return_op(count):
    """Violates returns="self": returns a bare value, not a field-dict."""
    return count + 1


def _stray_field_op(count):
    """Violates returns="self": names a field the class did not declare."""
    return {"ghost": 1}


_OPS = "srmech_rc139_testops"


@pytest.fixture
def isolated_class_catalog():
    from srmech.dsl import _class_catalog as cc

    mod = types.ModuleType(_OPS)
    mod.add_op = _add_op
    mod.scale_op = _scale_op
    mod.bump_op = _bump_op
    mod.bad_return_op = _bad_return_op
    mod.stray_field_op = _stray_field_op
    sys.modules[_OPS] = mod

    saved = list(cc._USER_CLASS_DIRS)
    cc.load_class_catalog.cache_clear()
    try:
        yield cc
    finally:
        cc._USER_CLASS_DIRS[:] = saved
        cc.load_class_catalog.cache_clear()
        cc._resolve_op.cache_clear()
        sys.modules.pop(_OPS, None)


_CHAIN_TOML = f"""
[class]
name = "RC139Chain"
[class.field]
base = "int"

[class.method.compute]
chain = [
  {{ op = "{_OPS}.add_op", binds = ["base", "x"], as = "s" }},
  {{ op = "{_OPS}.scale_op", binds = ["s"], factor = 3 }},
]
doc = "compute = 3 * (base + x)"
"""

_RETURNS_TOML = f"""
[class]
name = "RC139Returns"
[class.field]
count = "int"

[class.method.bump]
op = "{_OPS}.bump_op"
binds = ["count"]
returns = "self"

[class.method.bump_bad]
op = "{_OPS}.bad_return_op"
binds = ["count"]
returns = "self"

[class.method.bump_stray]
op = "{_OPS}.stray_field_op"
binds = ["count"]
returns = "self"

[class.method.both]
op = "{_OPS}.scale_op"
chain = [ {{ op = "{_OPS}.scale_op", binds = ["count"] }} ]
binds = ["count"]

[class.method.bad_route]
op = "{_OPS}.bump_op"
binds = ["count"]
sets = "count"
returns = "self"
"""


def _register(tmp_path, text, fname="reg.toml"):
    (tmp_path / fname).write_text(text, encoding="utf-8")
    register_class_dir(tmp_path)


# ── chain: the visible multi-op pipeline ─────────────────────────────────────

def test_chain_threads_stages_fields_and_static_kwargs(isolated_class_catalog, tmp_path):
    _register(tmp_path, _CHAIN_TOML)
    r = make_class("RC139Chain")(base=10)
    # stage0 add_op(base=10, x=5)=15 (as 's') → stage1 scale_op(15, factor=3)=45
    assert r.compute(x=5) == 45
    assert r.compute(x=0) == 30
    # describe_class surfaces the chain stages (not an `op`)
    d = describe_class("RC139Chain")
    m = d["methods"]["compute"]
    assert "op" not in m
    assert [st["op"] for st in m["chain"]] == [f"{_OPS}.add_op", f"{_OPS}.scale_op"]
    assert m["chain"][0]["as"] == "s"


def test_chain_unresolvable_bind_raises(isolated_class_catalog, tmp_path):
    toml = f"""
[class]
name = "RC139ChainBad"
[class.field]
base = "int"
[class.method.compute]
chain = [ {{ op = "{_OPS}.add_op", binds = ["base", "missing"] }} ]
"""
    _register(tmp_path, toml)
    r = make_class("RC139ChainBad")(base=1)
    with pytest.raises(ValueError, match="cannot resolve bind"):
        r.compute()


# ── returns="self": the self-returning method ────────────────────────────────

def test_returns_self_yields_fresh_instance_self_untouched(isolated_class_catalog, tmp_path):
    _register(tmp_path, _RETURNS_TOML)
    Cls = make_class("RC139Returns")
    r = Cls(count=5)
    r2 = r.bump()
    assert r2.fields["count"] == 6           # the new instance advanced
    assert r.fields["count"] == 5            # self untouched (not in-place)
    assert r2.class_name == r.class_name == "RC139Returns"
    assert type(r2).__name__ == type(r).__name__
    # chainable — a fresh instance each hop
    assert r.bump().bump().fields["count"] == 7
    assert r.fields["count"] == 5


def test_returns_self_op_must_return_field_dict(isolated_class_catalog, tmp_path):
    _register(tmp_path, _RETURNS_TOML)
    r = make_class("RC139Returns")(count=5)
    with pytest.raises(TypeError, match="must.*return a"):
        r.bump_bad()


def test_returns_self_undeclared_field_rejected(isolated_class_catalog, tmp_path):
    _register(tmp_path, _RETURNS_TOML)
    r = make_class("RC139Returns")(count=5)
    with pytest.raises(ValueError, match="undeclared"):
        r.bump_stray()


def test_describe_class_surfaces_returns(isolated_class_catalog, tmp_path):
    _register(tmp_path, _RETURNS_TOML)
    d = describe_class("RC139Returns")
    assert d["methods"]["bump"]["returns"] == "self"
    assert d["methods"]["bump"]["op"] == f"{_OPS}.bump_op"


# ── exclusivity guards (at invoke) ───────────────────────────────────────────

def test_op_and_chain_both_rejected(isolated_class_catalog, tmp_path):
    _register(tmp_path, _RETURNS_TOML)
    r = make_class("RC139Returns")(count=5)
    with pytest.raises(ValueError, match="exactly one of"):
        r.both()


def test_sets_and_returns_both_rejected(isolated_class_catalog, tmp_path):
    _register(tmp_path, _RETURNS_TOML)
    r = make_class("RC139Returns")(count=5)
    with pytest.raises(ValueError, match="at most one"):
        r.bad_route()


# ── generate_class_descriptor round-trips chain + returns ────────────────────

def test_generate_descriptor_roundtrips_chain_and_returns(isolated_class_catalog):
    methods = {
        "compute": {
            "chain": [
                {"op": f"{_OPS}.add_op", "binds": ["base", "x"], "as": "s"},
                {"op": f"{_OPS}.scale_op", "binds": ["s"], "factor": 3},
            ],
            "doc": "3*(base+x)",
        },
        "bump": {
            "op": f"{_OPS}.bump_op", "binds": ["count"], "returns": "self",
        },
    }
    text = generate_class_descriptor(
        "EmitRC139", fields={"base": "int", "count": "int"}, methods=methods
    )
    assert "chain = [" in text
    assert 'returns = "self"' in text
    cls = _toml.loads(text)["class"]
    assert cls["method"]["compute"]["chain"][0]["as"] == "s"
    assert cls["method"]["compute"]["chain"][1]["op"] == f"{_OPS}.scale_op"
    assert "op" not in cls["method"]["compute"]
    assert cls["method"]["bump"]["returns"] == "self"


def test_generate_descriptor_rejects_op_and_chain_together():
    with pytest.raises(ValueError, match="exactly one of"):
        generate_class_descriptor(
            "X", methods={"m": {"op": "a.b", "chain": [{"op": "c.d"}]}}
        )


def test_generate_descriptor_rejects_sets_and_returns_together():
    with pytest.raises(ValueError, match="at most one"):
        generate_class_descriptor(
            "X", methods={"m": {"op": "a.b", "sets": "f", "returns": "self"}}
        )
