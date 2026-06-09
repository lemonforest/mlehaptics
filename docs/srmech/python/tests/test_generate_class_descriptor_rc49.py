"""generate_class_descriptor — the make_class inverse (§39, rc49).

RBS-LM UPSTREAM_NOTES §39: ``srmech.dsl.generate_class_descriptor`` renders a
``[class]`` TOML descriptor from its components (or by introspecting a
registered class), round-trippable through ``srmech.dsl.make_class``. The genome
seed proved the target shape (a [class] TOML → a constructed class); this closes
the loop the OTHER direction (components / a constructed class → its [class]
TOML). Class E (catalog enumeration) ∘ Class F (descriptor render) ∘ Class H
(self-introspection) — no new primitive class.

These tests pin: the introspection round-trip (Genome re-emits to a descriptor
that re-parses to the same [class] section, doc bit-identical), the explicit
round-trip (emit → register → make_class → construct → invoke), describe_class
agreement on the re-registered emission, quoted-key handling, the validation
guards, and the ToolEntry registration.
"""

from __future__ import annotations

import sys

import pytest

if sys.version_info >= (3, 11):
    import tomllib as _toml
else:  # pragma: no cover — 3.10-only branch
    import tomli as _toml  # type: ignore[no-redef]

from srmech.dsl import (
    describe_class,
    generate_class_descriptor,
    get_class_descriptor,
    make_class,
    register_class_dir,
)


@pytest.fixture
def isolated_class_catalog():
    """Snapshot + restore the user-class-dir registry so a register_class_dir in
    one test can't leak into another (the loader caches the merged catalog)."""
    from srmech.dsl import _class_catalog as cc

    saved = list(cc._USER_CLASS_DIRS)
    cc.load_class_catalog.cache_clear()
    try:
        yield cc
    finally:
        cc._USER_CLASS_DIRS[:] = saved
        cc.load_class_catalog.cache_clear()


# ── introspection mode: a registered class re-emits its own [class] TOML ──

def test_genome_introspection_roundtrips_to_same_class_section():
    text = generate_class_descriptor("Genome")
    reparsed = _toml.loads(text)["class"]
    # The catalog descriptor's "class" section IS the parsed genome.toml; an
    # introspect-then-emit-then-parse must reproduce it exactly.
    assert reparsed == get_class_descriptor("Genome")["class"]


def test_genome_doc_is_bit_identical_after_roundtrip():
    text = generate_class_descriptor("Genome")
    reparsed = _toml.loads(text)["class"]
    original_doc = get_class_descriptor("Genome")["class"]["doc"]
    # The seed doc is multi-line; the emitter writes it single-line with escaped
    # newlines, so tomllib decodes it back to the identical string.
    assert reparsed["doc"] == original_doc
    assert "\n" in reparsed["doc"]


def test_genome_emit_parses_to_valid_descriptor_shape():
    text = generate_class_descriptor("Genome")
    parsed = _toml.loads(text)
    assert set(parsed) == {"class"}
    cls = parsed["class"]
    assert cls["name"] == "Genome"
    assert cls["kind"] == "storage"
    assert cls["field"] == {"the_one": "hv", "chromosomes": "list"}
    assert cls["method"]["add_chromosome"]["appends"] == "chromosomes"
    assert cls["method"]["shape"]["op"] == "srmech.amsc.genome.encode_shape"


def test_introspection_doc_kind_overrides():
    text = generate_class_descriptor("Genome", doc="overridden", kind="custom")
    cls = _toml.loads(text)["class"]
    assert cls["doc"] == "overridden"
    assert cls["kind"] == "custom"


# ── explicit mode: components → TOML → make_class round-trip ──

_WIDGET_METHODS = {
    "shape": {
        "op": "srmech.amsc.genome.encode_shape",
        "binds": ["n"],
        "doc": "Decide the encode shape for a kernel of size n.",
    },
}


def test_explicit_emit_register_make_class_construct_invoke(isolated_class_catalog, tmp_path):
    text = generate_class_descriptor(
        "WidgetRC49",
        fields={"label": "str"},
        methods=_WIDGET_METHODS,
        doc="A round-trip witness class.",
        kind="demo",
    )
    (tmp_path / "widget.toml").write_text(text, encoding="utf-8")
    register_class_dir(tmp_path)

    Widget = make_class("WidgetRC49")
    w = Widget(label="astronomy")
    out = w.shape(n=8)
    assert out["shape"] == "tome"
    assert w.fields["label"] == "astronomy"


def test_explicit_methods_only_defaults_fields_empty(isolated_class_catalog, tmp_path):
    # fields omitted (None) but methods given → explicit mode, fields default {}.
    text = generate_class_descriptor("BareRC49", methods=_WIDGET_METHODS)
    (tmp_path / "bare.toml").write_text(text, encoding="utf-8")
    register_class_dir(tmp_path)

    Bare = make_class("BareRC49")
    out = Bare().shape(n=2)
    assert out["n"] == 2


def test_describe_class_agrees_with_emitted_components(isolated_class_catalog, tmp_path):
    text = generate_class_descriptor(
        "AgreeRC49", fields={"label": "str"}, methods=_WIDGET_METHODS, kind="demo"
    )
    (tmp_path / "agree.toml").write_text(text, encoding="utf-8")
    register_class_dir(tmp_path)

    d = describe_class("AgreeRC49")
    assert d["name"] == "AgreeRC49"
    assert d["kind"] == "demo"
    assert d["fields"] == {"label": "str"}
    assert d["methods"]["shape"]["op"] == "srmech.amsc.genome.encode_shape"
    assert d["methods"]["shape"]["binds"] == ["n"]
    assert d["provenance"] == "user"


def test_appends_and_sets_routing_roundtrip(isolated_class_catalog, tmp_path):
    methods = {
        "cap": {"op": "srmech.amsc.genome.telomere", "binds": ["label"],
                "sets": "last_cap", "doc": "cap"},
    }
    text = generate_class_descriptor(
        "RouteRC49", fields={"last_cap": "any"}, methods=methods
    )
    cls = _toml.loads(text)["class"]
    assert cls["method"]["cap"]["sets"] == "last_cap"
    assert "appends" not in cls["method"]["cap"]


# ── quoted-key handling (non-bare-safe field / method names) ──

def test_hyphenated_method_name_stays_bare():
    # Hyphens ARE bare-key-legal in TOML, so a hyphenated name is NOT quoted.
    text = generate_class_descriptor(
        "HyphRC49", methods={"odd-name": {"op": "x.y", "binds": []}}
    )
    assert "[class.method.odd-name]" in text
    cls = _toml.loads(text)["class"]
    assert cls["method"]["odd-name"]["op"] == "x.y"


def test_spaced_method_name_is_quoted_and_roundtrips():
    # A space is NOT bare-key-legal → the key must be quoted in the table header.
    text = generate_class_descriptor(
        "SpaceRC49", methods={"odd name": {"op": "x.y", "binds": []}}
    )
    assert '[class.method."odd name"]' in text
    cls = _toml.loads(text)["class"]
    assert cls["method"]["odd name"]["op"] == "x.y"


def test_special_chars_in_doc_roundtrip():
    weird = 'has "quotes" and\ttabs and\nnewlines and \\ backslash'
    text = generate_class_descriptor(
        "EscRC49", methods={"m": {"op": "x.y", "binds": [], "doc": weird}}
    )
    cls = _toml.loads(text)["class"]
    assert cls["method"]["m"]["doc"] == weird


# ── validation guards ──

def test_empty_name_rejected():
    with pytest.raises(ValueError):
        generate_class_descriptor("", fields={}, methods={})


def test_method_without_op_rejected():
    with pytest.raises(ValueError):
        generate_class_descriptor("X", methods={"m": {"binds": ["a"]}})


def test_method_with_both_appends_and_sets_rejected():
    with pytest.raises(ValueError):
        generate_class_descriptor(
            "X", methods={"m": {"op": "a.b", "appends": "f", "sets": "g"}}
        )


def test_non_dict_method_spec_rejected():
    with pytest.raises(ValueError):
        generate_class_descriptor("X", methods={"m": ["not", "a", "dict"]})


# ── tool-schema registration ──

def test_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.dsl.generate_class_descriptor" in names
