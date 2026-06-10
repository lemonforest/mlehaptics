"""v0.7.0rc6 — bring-your-own (BYO) cascade-TOML (F289 D2).

A domain specialist drops their own ``*.toml`` cascade descriptors in a dir and
registers it (``register_catalog_dir``) — or points ``SRMECH_CASCADE_PATH`` at
it — and the ops then resolve / run / surface identically to shipped ops,
flagged ``provenance="user"`` (B-tier, attested to their own descriptor hash,
NOT a shipped A-tier primitive). A user descriptor may be a PURE-TOML
**composite** (a ``[composite]`` body = a chain of named ops, no Python) or a
primitive. User op-names may NOT shadow shipped ones (raises at load).
Composites validate at load: every referenced op resolves + the graph is
acyclic — a typo fails loud there, not silently at run.
"""

import os
import textwrap

import pytest

from srmech import dsl
from srmech.dsl import _catalog


@pytest.fixture(autouse=True)
def _reset_catalog_state():
    """Keep BYO tests hermetic: a shipped-only catalog before AND after each
    test (clear registered dirs + env-var + the lru cache)."""
    _catalog._USER_CATALOG_DIRS.clear()
    os.environ.pop("SRMECH_CASCADE_PATH", None)
    _catalog.load_catalog.cache_clear()
    try:
        yield
    finally:
        _catalog._USER_CATALOG_DIRS.clear()
        os.environ.pop("SRMECH_CASCADE_PATH", None)
        _catalog.load_catalog.cache_clear()


def _write(dirpath, fname, body):
    p = dirpath / fname
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


# A pure-TOML composite: two chiral_flips (an involution composed with itself).
_DOUBLE_FLIP = """
    [cascade]
    name = "byo_double_flip"
    class_composition = "C ∘ C"
    purpose = "two chiral flips (identity) — a bring-your-own composite demo"
    kind = "stage"

    [composite]
    [[composite.stage]]
    op = "chiral_flip"

    [[composite.stage]]
    op = "chiral_flip"
"""


def test_register_then_resolve_and_run_composite(tmp_path):
    _write(tmp_path, "double_flip.toml", _DOUBLE_FLIP)
    dsl.register_catalog_dir(str(tmp_path))
    assert "byo_double_flip" in dsl.list_cascade_ops()
    seq = [1, 2, 3]  # chiral_flip = sequence reversal; two flips = identity
    # resolves + runs via the fluent builder
    assert list(dsl.chain().then("byo_double_flip").run(seq)) == seq
    # and via the one-shot TOML surface (op= references the user composite)
    spec = '[chain]\nname = "t"\n[[stage]]\nop = "byo_double_flip"\n'
    assert list(dsl.run_toml_chain(spec, seq)) == seq


def test_env_var_catalog_path(tmp_path):
    _write(tmp_path, "double_flip.toml", _DOUBLE_FLIP)
    os.environ["SRMECH_CASCADE_PATH"] = str(tmp_path)
    _catalog.load_catalog.cache_clear()  # env is read on (re)load
    assert "byo_double_flip" in dsl.list_cascade_ops()
    assert list(dsl.chain().then("byo_double_flip").run([4, 5, 6])) == [4, 5, 6]


def test_provenance_tags_user_vs_shipped(tmp_path):
    _write(tmp_path, "double_flip.toml", _DOUBLE_FLIP)
    dsl.register_catalog_dir(str(tmp_path))
    ops = {o["name"]: o for o in dsl.list_catalog_ops()}
    assert ops["byo_double_flip"]["provenance"] == "user"
    assert ops["chiral_flip"]["provenance"] == "srmech"


def test_user_may_not_shadow_shipped_op(tmp_path):
    _write(tmp_path, "shadow.toml", """
        [cascade]
        name = "chiral_flip"
        purpose = "shadow attempt — must be rejected"
        [composite]
        [[composite.stage]]
        op = "magnitude"
    """)
    dsl.register_catalog_dir(str(tmp_path))
    with pytest.raises(ValueError, match="conflict"):
        _catalog.load_catalog()


def test_composite_unknown_op_fails_loud_at_load(tmp_path):
    _write(tmp_path, "bad.toml", """
        [cascade]
        name = "byo_bad"
        purpose = "references a nonexistent op"
        [composite]
        [[composite.stage]]
        op = "no_such_op"
    """)
    dsl.register_catalog_dir(str(tmp_path))
    with pytest.raises(ValueError, match="unknown op"):
        _catalog.load_catalog()


def test_composite_cycle_fails_loud_at_load(tmp_path):
    _write(tmp_path, "cycle.toml", """
        [cascade]
        name = "byo_cycle"
        purpose = "self-referential composite"
        [composite]
        [[composite.stage]]
        op = "byo_cycle"
    """)
    dsl.register_catalog_dir(str(tmp_path))
    with pytest.raises(ValueError, match="cycle"):
        _catalog.load_catalog()


def test_missing_name_fails_at_load(tmp_path):
    _write(tmp_path, "noname.toml", """
        [cascade]
        purpose = "no name field"
        [composite]
        [[composite.stage]]
        op = "chiral_flip"
    """)
    dsl.register_catalog_dir(str(tmp_path))
    with pytest.raises(ValueError, match="name"):
        _catalog.load_catalog()


def test_register_dir_rejects_nonexistent_path(tmp_path):
    with pytest.raises(AssertionError):
        dsl.register_catalog_dir(str(tmp_path / "does_not_exist"))


def test_shipped_catalog_intact_and_describe_unchanged():
    # fixture cleared all user dirs — the shipped-only catalog must be intact,
    # every shipped op still resolves, and the tool count is unchanged (the BYO
    # surface is a config API, not a new ToolEntry).
    shipped = dsl.list_cascade_ops()
    assert {"chiral_flip", "magnitude", "cyclic_gcd"} <= set(shipped)
    for name in shipped:
        assert callable(dsl.lookup_cascade_op(name))
    for o in dsl.list_catalog_ops():
        assert o["provenance"] == "srmech"
    import srmech.introspect as introspect
    assert introspect.describe()["tools"]["total"] == 285
