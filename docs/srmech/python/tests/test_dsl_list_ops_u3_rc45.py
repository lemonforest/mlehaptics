"""§17 U3 — `srmech.dsl.list_ops` unified op-discovery (v0.7.5rc45).

RBS-LM UPSTREAM_NOTES §17 ("catalog → kernel → DSL unification") U3 asks
that the two previously-disjoint op-discovery registries — the DSL's
value-transform cascade ops (`list_catalog_ops`) and the AMSC
catalog-declared operator chains (`catalog.list_catalog_chains`) — be
reachable through ONE call so an LLM / CLI sees the whole authorable
surface at once. `list_ops` is that call.

These tests pin the unification contract: the cascade-op half is a
superset-equal of `list_catalog_ops`, every record has the uniform
five-key shape, the catalog-chain half is empty on a base install (no
catalog registered) yet tolerant of bad/unknown source keys, and the
result is deterministically ordered.
"""

from __future__ import annotations

from srmech.dsl import list_catalog_ops, list_ops

_KEYS = {"name", "class", "purpose", "kind", "provenance"}


def test_list_ops_uniform_record_shape():
    ops = list_ops()
    assert ops, "list_ops returned nothing"
    for r in ops:
        assert _KEYS <= set(r), f"record missing keys: {r}"
        assert all(isinstance(r[k], str) for k in _KEYS), f"non-str field: {r}"


def test_list_ops_superset_of_catalog_ops():
    """The cascade-op half is exactly list_catalog_ops (base install)."""
    cat = {r["name"] for r in list_catalog_ops()}
    got = {r["name"] for r in list_ops() if r["kind"] != "catalog-chain"}
    assert cat <= got, f"missing cascade ops: {cat - got}"
    # No AMSC catalog is registered in the test env, so the two coincide.
    assert got == cat


def test_list_ops_kinds_are_known():
    for r in list_ops():
        assert r["kind"] in {"stage", "combinator", "catalog-chain"}, r


def test_list_ops_sorted_by_kind_then_name():
    ops = list_ops()
    keyed = [(r["kind"], r["name"]) for r in ops]
    assert keyed == sorted(keyed), "list_ops not sorted by (kind, name)"


def test_list_ops_bad_source_key_is_safe():
    """An unknown source_key yields no chains and never raises."""
    base = list_ops()
    restricted = list_ops(source_keys=["definitely_not_a_real_source"])
    # No catalog chains resolve → identical to the cascade-op-only base.
    assert restricted == base


def test_list_ops_empty_source_keys_is_cascade_ops_only():
    restricted = list_ops(source_keys=[])
    assert all(r["kind"] != "catalog-chain" for r in restricted)
    assert {r["name"] for r in restricted} == {
        r["name"] for r in list_catalog_ops()
    }


def test_list_ops_deterministic():
    assert list_ops() == list_ops()


def test_list_ops_includes_rc44_encode_loe_content():
    """The §17 U2 op (rc44) is visible through the unified surface."""
    assert any(r["name"] == "encode_loe_content" for r in list_ops())


def test_list_ops_tool_entry_registered():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.dsl.list_ops" in names
