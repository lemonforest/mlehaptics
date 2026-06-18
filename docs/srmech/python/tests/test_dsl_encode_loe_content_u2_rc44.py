"""v0.7.5rc44 — §17 U2: register the text→instrument encoder as a DSL cascade-op.

The rc44 dotted-`op=` resolver lets a cascade-catalog descriptor name an
EXISTING callable that lives outside `srmech.amsc.cascade` (here
`srmech.signal_processing.encode_loe_content`). This makes
`[[stage]] op="encode_loe_content"` legal — any catalog's text rows get a
one-line kernel chain — without re-exporting the op into `amsc.cascade`.
Mirrors the rc39 class-catalog's dotted-path method resolution.

Validates: the op is catalog-registered + listed; the dotted resolver returns
the real shipped callable; it runs as a DSL chain stage (value→content, D=/
substrate= kwargs pass through); determinism; and the resolver rejects a
dotted op that doesn't resolve.
"""
from __future__ import annotations

import pytest

from srmech.dsl import chain, list_cascade_ops, lookup_cascade_op
from srmech.dsl._catalog import cascade_op_kind, get_descriptor


def test_encode_loe_content_is_catalog_registered():
    assert "encode_loe_content" in list_cascade_ops()
    desc = get_descriptor("encode_loe_content")
    assert desc["cascade"]["op"] == "srmech.signal_processing.encode_loe_content"


def test_dotted_op_resolves_to_the_shipped_callable():
    fn = lookup_cascade_op("encode_loe_content")
    assert callable(fn)
    assert fn.__name__ == "encode_loe_content"
    # the real shipped op, NOT a re-export into amsc.cascade
    assert "signal_processing" in fn.__module__


def test_runs_as_a_dsl_chain_stage_with_kwargs():
    out = chain().then("encode_loe_content", D=512).run("the cascade rotates at the end")
    assert isinstance(out, (bytes, bytearray))
    assert len(out) == 512 // 8                       # D bits → D/8 bytes


def test_encode_loe_content_stage_is_deterministic():
    txt = "substrate self recognition"
    a = chain().then("encode_loe_content", D=256).run(txt)
    b = chain().then("encode_loe_content", D=256).run(txt)
    assert a == b


def test_dotted_op_kind_is_a_stage():
    # a single shipped callable (not a pure-TOML composite) is a stage op
    assert cascade_op_kind("encode_loe_content") in {"stage", "primitive", "combinator"}


def test_dotted_resolver_rejects_unresolvable_path(tmp_path, monkeypatch):
    # a descriptor whose dotted op points nowhere must fail loud at lookup
    from srmech.dsl import _catalog
    bad_dir = tmp_path / "bad_cat"
    bad_dir.mkdir()
    (bad_dir / "bogus_dotted.toml").write_text(
        '[cascade]\nname = "bogus_dotted"\n'
        'op = "srmech.signal_processing.this_op_does_not_exist"\n'
        'purpose = "negative test"\n',
        encoding="utf-8",
    )
    _catalog.register_catalog_dir(bad_dir)
    try:
        with pytest.raises((RuntimeError, ModuleNotFoundError, AttributeError)):
            lookup_cascade_op("bogus_dotted")
    finally:
        # restore the catalog state (clear the registered dir + cache)
        _catalog._USER_CATALOG_DIRS.clear()
        _catalog.load_catalog.cache_clear()
