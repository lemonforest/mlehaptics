"""v0.7.5rc137 — make_class richer contract: ``dict`` fields + ``mutates`` routing.

The genome seed proved the make_class contract with the *single*-field state
routes (``appends`` = list.append, ``sets`` = replace one field) over None-/
list-typed fields. Richer domain objects — a register whose ``write`` touches a
codebook AND a slot-map at once — need two more things: a ``dict``-typed field
(defaults to ``{}`` at construction) and a *multi*-field state route. rc137 adds
``mutates`` (a field-name list): the op returns ``(return_value, {field: new})``
and each named field is replaced, the bare ``return_value`` flows back to the
caller. ``appends`` / ``sets`` / ``mutates`` stay mutually exclusive.

This pins: the dict-field default, the multi-field route, ``describe_class``
surfacing ``mutates``, the ``generate_class_descriptor`` round-trip, and the
fail-loud guards (bad op return-shape, an update outside the declared set, an
undeclared mutates field, and the appends/sets/mutates exclusivity).

The methods bind to a synthetic ops module injected into ``sys.modules`` (the
dotted-path resolver imports it like any shipped op) — no new shipped op needed
to exercise the contract.
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


# ── synthetic flat cascade-ops the [class] TOML binds to ─────────────────────

def _write_op(value, store, slots, *, key):
    """A two-field mutator: stash ``value`` under ``key`` in the codebook AND
    record the slot. Returns ``(key, {field: new_value})`` — the mutates shape."""
    new_store = dict(store)
    new_store[key] = value
    new_slots = dict(slots)
    new_slots[len(new_slots)] = key
    return key, {"store": new_store, "slots": new_slots}


def _bad_return_op(value, store, *, key=None):
    """Violates the mutates contract: returns a bare value, not a 2-tuple."""
    return value


def _stray_field_op(value, store, *, key=None):
    """Violates the mutates contract: updates a field outside the declared set."""
    return value, {"store": {"x": value}, "phantom": 1}


_OPS_MODULE = "srmech_rc137_testops"


@pytest.fixture
def isolated_class_catalog():
    """Inject the synthetic ops module + snapshot/restore the user-class-dir
    registry so a register_class_dir here can't leak into another test."""
    from srmech.dsl import _class_catalog as cc

    mod = types.ModuleType(_OPS_MODULE)
    mod.write_op = _write_op
    mod.bad_return_op = _bad_return_op
    mod.stray_field_op = _stray_field_op
    sys.modules[_OPS_MODULE] = mod

    saved = list(cc._USER_CLASS_DIRS)
    cc.load_class_catalog.cache_clear()
    try:
        yield cc
    finally:
        cc._USER_CLASS_DIRS[:] = saved
        cc.load_class_catalog.cache_clear()
        cc._resolve_op.cache_clear()
        sys.modules.pop(_OPS_MODULE, None)


_REGISTER_TOML = f"""
[class]
name = "RC137Register"
kind = "storage"
doc = "A user-declared register with dict state + a two-field mutator."

[class.field]
store = "dict"
slots = "dict"

[class.method.write]
op = "{_OPS_MODULE}.write_op"
binds = ["value", "store", "slots"]
mutates = ["store", "slots"]
doc = "Write value under key; mutate both the codebook and the slot-map."
"""


def _register(tmp_path, toml_text, fname="reg.toml"):
    (tmp_path / fname).write_text(toml_text, encoding="utf-8")
    register_class_dir(tmp_path)


# ── dict-typed fields default to {} ──────────────────────────────────────────

def test_dict_field_defaults_to_empty_dict(isolated_class_catalog, tmp_path):
    _register(tmp_path, _REGISTER_TOML)
    r = make_class("RC137Register")()
    assert r.fields["store"] == {}
    assert r.fields["slots"] == {}
    # distinct objects per instance (no shared-mutable-default aliasing)
    r2 = make_class("RC137Register")()
    r.fields["store"]["a"] = 1
    assert r2.fields["store"] == {}


# ── the multi-field mutates route ────────────────────────────────────────────

def test_mutates_updates_both_fields_and_returns_value(isolated_class_catalog, tmp_path):
    _register(tmp_path, _REGISTER_TOML)
    r = make_class("RC137Register")()
    ret = r.write(value=42, key="alpha")          # value from call; store/slots from fields
    assert ret == "alpha"                         # the bare return_value, not the tuple
    assert r.fields["store"] == {"alpha": 42}     # field 1 replaced
    assert r.fields["slots"] == {0: "alpha"}      # field 2 replaced
    # a second write threads the updated state through again
    ret2 = r.write(value=99, key="beta")
    assert ret2 == "beta"
    assert r.fields["store"] == {"alpha": 42, "beta": 99}
    assert r.fields["slots"] == {0: "alpha", 1: "beta"}


# ── describe_class surfaces mutates ──────────────────────────────────────────

def test_describe_class_surfaces_mutates(isolated_class_catalog, tmp_path):
    _register(tmp_path, _REGISTER_TOML)
    d = describe_class("RC137Register")
    assert d["fields"] == {"store": "dict", "slots": "dict"}
    assert d["methods"]["write"]["mutates"] == ["store", "slots"]
    assert "appends" not in d["methods"]["write"]
    assert "sets" not in d["methods"]["write"]


# ── generate_class_descriptor round-trips mutates ────────────────────────────

def test_generate_class_descriptor_roundtrips_mutates(isolated_class_catalog):
    methods = {
        "write": {
            "op": f"{_OPS_MODULE}.write_op",
            "binds": ["value", "store", "slots"],
            "mutates": ["store", "slots"],
            "doc": "two-field mutator",
        },
    }
    text = generate_class_descriptor(
        "EmitRC137", fields={"store": "dict", "slots": "dict"}, methods=methods
    )
    assert 'mutates = ["store", "slots"]' in text
    cls = _toml.loads(text)["class"]
    assert cls["method"]["write"]["mutates"] == ["store", "slots"]
    assert "appends" not in cls["method"]["write"]
    assert "sets" not in cls["method"]["write"]


def test_generate_class_descriptor_rejects_sets_and_mutates_together():
    with pytest.raises(ValueError, match="at most one"):
        generate_class_descriptor(
            "X",
            methods={"m": {"op": "a.b", "sets": "f", "mutates": ["g"]}},
        )


def test_generate_class_descriptor_rejects_non_list_mutates():
    with pytest.raises(ValueError, match="list of field-name"):
        generate_class_descriptor(
            "X", methods={"m": {"op": "a.b", "mutates": "store"}}
        )


# ── fail-loud invoke guards ──────────────────────────────────────────────────

_BAD_RETURN_TOML = f"""
[class]
name = "RC137BadReturn"
[class.field]
store = "dict"
[class.method.write]
op = "{_OPS_MODULE}.bad_return_op"
binds = ["value", "store"]
mutates = ["store"]
"""

_STRAY_FIELD_TOML = f"""
[class]
name = "RC137Stray"
[class.field]
store = "dict"
[class.method.write]
op = "{_OPS_MODULE}.stray_field_op"
binds = ["value", "store"]
mutates = ["store"]
"""

_UNDECLARED_TOML = f"""
[class]
name = "RC137Undeclared"
[class.field]
store = "dict"
slots = "dict"
[class.method.write]
op = "{_OPS_MODULE}.write_op"
binds = ["value", "store", "slots"]
mutates = ["store", "ghost"]
"""

_BOTH_ROUTES_TOML = f"""
[class]
name = "RC137BothRoutes"
[class.field]
store = "dict"
slots = "dict"
[class.method.write]
op = "{_OPS_MODULE}.write_op"
binds = ["value", "store", "slots"]
sets = "store"
mutates = ["store"]
"""


def test_mutates_op_must_return_value_and_dict(isolated_class_catalog, tmp_path):
    _register(tmp_path, _BAD_RETURN_TOML)
    r = make_class("RC137BadReturn")()
    with pytest.raises(TypeError, match="must return"):
        r.write(value=1, key="k")


def test_mutates_update_outside_declared_set_rejected(isolated_class_catalog, tmp_path):
    _register(tmp_path, _STRAY_FIELD_TOML)
    r = make_class("RC137Stray")()
    with pytest.raises(ValueError, match="not in declared mutates"):
        r.write(value=1, key="k")


def test_mutates_names_undeclared_field_rejected(isolated_class_catalog, tmp_path):
    _register(tmp_path, _UNDECLARED_TOML)
    r = make_class("RC137Undeclared")()
    with pytest.raises(ValueError, match="undeclared"):
        r.write(value=1, key="k")


def test_method_with_sets_and_mutates_rejected_at_invoke(isolated_class_catalog, tmp_path):
    _register(tmp_path, _BOTH_ROUTES_TOML)
    r = make_class("RC137BothRoutes")()
    with pytest.raises(ValueError, match="at most one"):
        r.write(value=1, key="k")
