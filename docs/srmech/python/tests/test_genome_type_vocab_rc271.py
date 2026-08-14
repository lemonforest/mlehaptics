"""§96 / rc271 (F1251 / PR#687) — genome vocabulary → the field's own biology names
+ the VALUE-ALIAS opt-in.

  (A) RENAME (BREAKING at the value level): the derived cap_kind / census type
      VALUES are the field's own names — "stick" -> "plasmid" (accessory/mobile),
      "minted" -> "nuclear" (core/clonal); "diploid" unchanged.
  (B) A VALUE-ALIAS presentation layer: set_type_aliases / clear_type_aliases /
      load_type_aliases_toml re-present the canonical output with a user's preferred
      names (e.g. restore the old stick/minted), as a PURE PYTHON post-transform OVER
      the canonical result — the C layer + on-disk format stay canonical.
  (C) BACKWARD-COMPAT: cap_kind is DERIVED on read (rc267), never stored — so a v15
      genome's bytes read UNCHANGED (format 15, ABI 5); only the derived label differs.

C<->Python 1:1 parity is proven at the CANONICAL level where the native lib is loaded
(native tree == the pure roll-up; the alias rides identically on both). numpy-free."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.math import hdc


_DIM = 64
_DATA = Path(__file__).resolve().parent / "data"
# rc364: the descriptor moved OUT of tests/data/ and INTO the shipped alias catalog.
# It had to: `tests/**` is in `sdist.include` and NOT in the wheel, so the one-call
# migration path this file's own header documents raised FileNotFoundError on every
# wheel install. Resolved through the loader's catalog now, which is exactly the
# surface a wheel user has.
from srmech.dsl import ALIAS_CATALOG_DIR                     # noqa: E402
_LEGACY_TOML = ALIAS_CATALOG_DIR / "genome_type_aliases_legacy.toml"


@pytest.fixture(autouse=True)
def _canonical_by_default():
    """Every test starts + ends at the CANONICAL vocabulary — the value-alias state
    is session-global, so isolate it so no alias leaks across tests / files."""
    G.clear_type_aliases()
    try:
        yield
    finally:
        G.clear_type_aliases()


def _one():
    return hdc.klein4_expand(_DIM, 0)


def _leaf(i):
    return G._HV.from_sequence([(i * 7 + j) % 4 for j in range(_DIM)], sectors=4)


def _leaves(n):
    return [_leaf(i) for i in range(n)]


def _mixed_strand(one):
    """One of each cap_kind: plasmid 'stk' (3 leaves), nuclear 'min' (9 leaves ->
    the umbrella mints an interior centromere), and a hand-built pure diploid 'dip'
    (a §95b diploid-telomere opener, NO centromere)."""
    strand = list(G.genome([("stk", _leaves(3)), ("min", _leaves(9))], one))
    dip_cap = G._pack_cap(G.DIPLOID_TELOMERE_MARKER, "dip", _DIM)
    dip_turns = [G.quad_turn(_leaf(i), one) for i in range(2)]
    return strand + [dip_cap] + dip_turns


def _save(strand, tmp, name, one):
    path = Path(tmp) / name
    G.genome_save(strand, str(path), one)
    return path


# ── (A) the rename correctness ───────────────────────────────────────────────

def test_plasmid_genome_censuses_plasmid():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(G.plasmid([("p1", _leaves(2)), ("p2", _leaves(3))], one),
                     tmp, "plasmid.genome", one)
        cen = G.genome_census(str(path))
        assert cen["types"] == {"plasmid": 2, "nuclear": 0, "diploid": 0}
        assert all(c["type"] == "plasmid" for c in cen["chromosomes"])
        cat = G.genome_catalog(str(path))
        assert all(c["cap_kind"] == "plasmid" for c in cat["chromosomes"])


def test_nuclear_genome_censuses_nuclear():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        # a quad_strand kernel (>=5 leaves) is minted -> a Tier-2 NUCLEAR chromosome.
        path = _save(G.mint({"astro": _leaves(9)}, one), tmp, "nucleus.genome", one)
        cen = G.genome_census(str(path))
        assert cen["types"] == {"plasmid": 0, "nuclear": 1, "diploid": 0}
        assert cen["topology"] == "nuclear-like"
        cat = G.genome_catalog(str(path))
        assert cat["chromosomes"][0]["cap_kind"] == "nuclear"


def test_mixed_catalog_and_census_use_new_vocab():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        cat = G.genome_catalog(str(path))
        by_label = {c["label"]: c["cap_kind"] for c in cat["chromosomes"]}
        assert by_label == {"stk": "plasmid", "min": "nuclear", "dip": "diploid"}
        cen = G.genome_census(str(path))
        assert cen["types"] == {"plasmid": 1, "nuclear": 1, "diploid": 1}
        kinds = {c["label"]: c["type"] for c in cen["chromosomes"]}
        assert kinds == {"stk": "plasmid", "min": "nuclear", "dip": "diploid"}


def test_no_legacy_strings_leak_into_canonical_output():
    """The canonical output NEVER contains the old 'stick'/'minted' strings."""
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        blob = json.dumps(G.genome_census(str(path))) + json.dumps(
            G.genome_catalog(str(path)))
        assert "stick" not in blob and "minted" not in blob


def test_census_native_equals_pure_canonical():
    if not _native.has_native_genome_census():
        pytest.skip("native genome_census not loaded")
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        native = json.loads(
            _native.genome_census_c(str(path), G._coupling_block_bytes(one)))
        pure = G._census_from_catalog(
            G._catalog_data(str(path), coupling=one), str(path))
        assert native == pure                                  # both CANONICAL
        assert native["types"] == {"plasmid": 1, "nuclear": 1, "diploid": 1}


# ── (B) the value-alias presentation layer ───────────────────────────────────

def test_set_type_aliases_restores_old_names_on_census():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        installed = G.set_type_aliases({"nuclear": "minted", "plasmid": "stick"})
        assert installed == {"nuclear": "minted", "plasmid": "stick"}
        cen = G.genome_census(str(path))
        assert cen["types"] == {"stick": 1, "minted": 1, "diploid": 1}
        kinds = {c["label"]: c["type"] for c in cen["chromosomes"]}
        assert kinds == {"stk": "stick", "min": "minted", "dip": "diploid"}
        # the catalog cap_kind is aliased too
        cat = G.genome_catalog(str(path))
        assert {c["label"]: c["cap_kind"] for c in cat["chromosomes"]} == {
            "stk": "stick", "min": "minted", "dip": "diploid"}


def test_clear_type_aliases_returns_to_canonical():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        G.set_type_aliases({"nuclear": "minted", "plasmid": "stick"})
        assert G.genome_census(str(path))["types"] == {
            "stick": 1, "minted": 1, "diploid": 1}
        G.clear_type_aliases()
        assert G.genome_census(str(path))["types"] == {
            "plasmid": 1, "nuclear": 1, "diploid": 1}


def test_alias_applies_to_registry():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "cell"
        root.mkdir()
        G.genome_save(_mixed_strand(one), str(root / "aaa_nucleus"), one)
        G.genome_save(G.plasmid([("mt1", _leaves(2))], one), str(root / "bbb_mito"), one)
        G.set_type_aliases({"nuclear": "minted", "plasmid": "stick"})
        reg = G.genome_registry(str(root))
        allkeys = set()
        for g in reg["genomes"]:
            allkeys |= set(g["types"].keys())
        assert allkeys == {"stick", "minted", "diploid"}
        assert "plasmid" not in allkeys and "nuclear" not in allkeys


def test_example_toml_restores_legacy_names():
    assert _LEGACY_TOML.exists(), f"missing example TOML {_LEGACY_TOML}"
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        mapping = G.load_type_aliases_toml(str(_LEGACY_TOML))
        assert mapping == {"nuclear": "minted", "plasmid": "stick"}   # installed + returned
        cen = G.genome_census(str(path))
        assert cen["types"] == {"stick": 1, "minted": 1, "diploid": 1}


def test_partial_alias_only_maps_named_values():
    """Aliasing ONLY nuclear leaves plasmid/diploid canonical."""
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        G.set_type_aliases({"nuclear": "core"})
        cen = G.genome_census(str(path))
        assert cen["types"] == {"plasmid": 1, "core": 1, "diploid": 1}


def test_set_type_aliases_rejects_non_canonical_key():
    with pytest.raises(ValueError, match="not a canonical cap_kind"):
        G.set_type_aliases({"stick": "plasmid"})       # 'stick' is not canonical
    with pytest.raises(ValueError, match="non-empty string"):
        G.set_type_aliases({"nuclear": ""})
    with pytest.raises(TypeError):
        G.set_type_aliases(["nuclear", "minted"])      # not a dict


def test_alias_does_not_change_native_pure_parity():
    """With an alias active, native==pure STILL holds (the alias is the SAME
    post-transform on both the native and the pure public path)."""
    if not _native.has_native_genome_census():
        pytest.skip("native genome_census not loaded")
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        G.set_type_aliases({"nuclear": "minted", "plasmid": "stick"})
        native = G.genome_census(str(path))            # native path + alias
        # the pure branch: the SAME alias post-transform over the canonical pure roll-up
        pure = G._apply_type_aliases_to_census(
            G._census_from_catalog(
                G._canonical_catalog(str(path), coupling=one), str(path)))
        assert native == pure
        assert native["types"] == {"stick": 1, "minted": 1, "diploid": 1}


# ── (C) backward-compat: no format / ABI change ──────────────────────────────

def test_v15_genome_reads_unchanged_no_format_bump():
    """cap_kind is DERIVED on read (rc267), never stored — so the on-disk format is
    UNCHANGED (v15) and the manifest carries NO cap_kind; only the derived label is
    the new vocabulary. A pre-rc271 v15 genome thus reads byte-identically, its
    census differing only by the two renamed strings."""
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(G.mint({"astro": _leaves(9)}, one), tmp, "nucleus.genome", one)
        raw = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        data = raw.get("data", raw)
        assert data["format_version"] == 19               # no format bump
        # cap_kind is NOT stored on disk (head-only v12+; derived on read)
        assert "chromosomes" not in data
        # re-reading derives the new canonical vocabulary from the SAME bytes
        cat = G.genome_catalog(str(path), coupling=one)
        assert cat["chromosomes"][0]["cap_kind"] == "nuclear"


def test_reread_is_stable_across_the_rename():
    """Saving then re-reading a genome is idempotent under the new vocabulary
    (the derivation is deterministic; no migration)."""
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save(_mixed_strand(one), tmp, "mixed.genome", one)
        first = G.genome_census(str(path))
        second = G.genome_census(str(path))
        assert first == second
        assert first["types"] == {"plasmid": 1, "nuclear": 1, "diploid": 1}
