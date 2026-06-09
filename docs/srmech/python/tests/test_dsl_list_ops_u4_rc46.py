"""§17 U4 — catalog→DSL auto-registration bridge (v0.7.5rc46).

RBS-LM UPSTREAM_NOTES §17 U4 asks that a ``register_attested_root(...)``
text-catalog with a declared operator chain (or one dropped on
``SRMECH_CASCADE_PATH``) **auto-appear** in the U3 ``list_ops()`` discovery
surface, tagged ``catalog:<source_key>`` — collapsing the "three doors"
(``list_catalog_chains`` + ``SRMECH_CASCADE_PATH`` D2 + ``use_local_kernel``)
into ONE path.

The rc45 U3 surface auto-discovers registered attested sources, but read the
WRONG source-key field (``source_key``/``name`` instead of the shipped ``key``),
so the packaged catalog sources never surfaced. rc46 fixes the field — these
tests pin the bridge: the packaged sources' declared chains appear in
``list_ops()`` tagged ``catalog:<key>``, an explicit ``source_keys`` filter
restricts to the named source, and a freshly ``register_attested_root``-ed
catalog with a declared chain shows up too.
"""

from __future__ import annotations

from srmech.amsc.catalog import list_attested_sources, list_catalog_chains
from srmech.dsl import list_ops


def _catalog_chain_records():
    return [r for r in list_ops() if r["kind"] == "catalog-chain"]


def test_packaged_catalog_chains_surface_in_list_ops():
    """The packaged attested sources' declared chains auto-appear.

    asymptotic_calculus / cosmos_validation / pi_digits each declare
    ``[[catalog.operator_chain]]`` entries; the auto-discovery bridge must
    surface them without any explicit ``source_keys`` argument.
    """
    cc = _catalog_chain_records()
    assert cc, "no catalog-chains surfaced — the U4 bridge is not routing"
    provs = {r["provenance"] for r in cc}
    # At least the three shipped chain-declaring sources.
    assert "catalog:pi_digits" in provs
    assert "catalog:asymptotic_calculus" in provs
    assert "catalog:cosmos_validation" in provs


def test_catalog_chain_count_matches_registry():
    """list_ops's catalog-chain half == sum of list_catalog_chains."""
    srcs = list_attested_sources()["sources"]
    expected = 0
    for s in srcs:
        res = list_catalog_chains(s["key"])
        if res.get("ok"):
            expected += res.get("n_chains", 0)
    assert len(_catalog_chain_records()) == expected


def test_catalog_chain_records_are_well_formed():
    for r in _catalog_chain_records():
        assert r["kind"] == "catalog-chain"
        assert r["provenance"].startswith("catalog:")
        assert r["name"]
        # `class` is the per-step A–N class sequence rendered as a string.
        assert isinstance(r["class"], str)


def test_explicit_source_keys_restricts_catalog_half():
    """source_keys=['pi_digits'] surfaces only that source's chains."""
    only = [r for r in list_ops(source_keys=["pi_digits"])
            if r["kind"] == "catalog-chain"]
    assert only, "pi_digits declares a chain; it must surface when named"
    assert {r["provenance"] for r in only} == {"catalog:pi_digits"}


def test_register_attested_root_bridges_into_list_ops(tmp_path):
    """A freshly-registered catalog's declared chain auto-appears.

    The end-to-end U4 contract: register_attested_root → its declared
    operator chain shows up in list_ops tagged catalog:<key>, one path.
    Mirrors a packaged descriptor (pi_digits) into a temp root under a
    fresh source key, registers it, asserts the chain surfaces, then
    unregisters to keep global state clean.
    """
    from srmech.amsc import catalog as _cat

    # Find a packaged descriptor that declares a chain, to clone its shape.
    srcs = list_attested_sources()["sources"]
    donor_key = next(
        s["key"] for s in srcs
        if list_catalog_chains(s["key"]).get("n_chains", 0) > 0
    )
    donor = next(s for s in srcs if s["key"] == donor_key)
    # The descriptor path lives in the registry; re-point a copy at a new key.
    import shutil
    from pathlib import Path

    # Locate the donor descriptor on disk via the packaged attested tree.
    pkg_root = Path(_cat.__file__).parent / "attested" / donor_key
    if not (pkg_root / "descriptor.toml").exists():
        # Some sources live elsewhere; skip rather than assert a layout.
        import pytest
        pytest.skip(f"donor {donor_key!r} descriptor not at packaged path")

    new_key = "u4_bridge_probe_src"
    dst = tmp_path / new_key
    shutil.copytree(pkg_root, dst)
    desc = (dst / "descriptor.toml").read_text(encoding="utf-8")
    # Rebind the source key so it doesn't collide with the donor.
    desc = desc.replace(f'key = "{donor_key}"', f'key = "{new_key}"', 1)
    (dst / "descriptor.toml").write_text(desc, encoding="utf-8")

    try:
        _cat.register_attested_root(tmp_path, source="u4-bridge-test")
        provs = {r["provenance"] for r in _catalog_chain_records()}
        assert f"catalog:{new_key}" in provs, (
            "registered catalog's declared chain did not bridge into list_ops"
        )
    finally:
        _cat._clear_registered_roots()
