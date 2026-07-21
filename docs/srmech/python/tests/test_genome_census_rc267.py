"""§96 / rc267 (PR#687 UPSTREAM_NOTES) — genome introspection, biology-native:

  (A) per-chromosome ``cap_kind`` ∈ {"plasmid","nuclear","diploid"} in genome_catalog,
      derived on the SAME §44 body scan (nuclear > diploid > plasmid; rc271 F1251
      renamed stick->plasmid, minted->nuclear).
  (B) genome_census(path) — the per-genome roll-up {path, n_chromosomes, types,
      chromosomes, total_leaves, topology} (nuclear/organelle/plasmid topology).
  (C) genome_registry(root) — the cell/melange census over a root of genomes.

srmech reads the SHAPE (the inline cap markers); the caller assigns the ROLE.
C↔Python 1:1 parity is proven where the native lib is loaded (native tree ==
the pure roll-up). numpy-free (stdlib json + the genome surface)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import hdc


_DIM = 64


def _one():
    return hdc.klein4_expand(_DIM, 0)


def _leaf(i):
    return G._HV.from_sequence([(i * 7 + j) % 4 for j in range(_DIM)], sectors=4)


def _leaves(n):
    return [_leaf(i) for i in range(n)]


def _mixed_genome_strand(one):
    """A strand with one of EACH cap_kind: plasmid 'stk' (3 leaves, plasmid-scale),
    nuclear 'min' (9 leaves → the umbrella mints an interior centromere), and a
    hand-built diploid 'dip' (a §95b diploid-telomere opener, NO centromere — the
    only way to get a pure "diploid" cap_kind, since diploid() carries a centromere
    and so reads "nuclear")."""
    strand = list(G.genome([("stk", _leaves(3)), ("min", _leaves(9))], one))
    dip_cap = G._pack_cap(G.DIPLOID_TELOMERE_MARKER, "dip", _DIM)
    dip_turns = [G.quad_turn(_leaf(i), one) for i in range(2)]
    return strand + [dip_cap] + dip_turns


def _save_mixed(tmp, one):
    path = Path(tmp) / "nucleus.genome"
    G.genome_save(_mixed_genome_strand(one), str(path), one)
    return path


def _save_organelle(tmp, one):
    """A small all-plasmid genome (2 plasmid chromosomes, ≤4 leaves each) → the
    mitochondrion/chloroplast plasmid analogue."""
    path = Path(tmp) / "mito.genome"
    G.genome_save(G.plasmid([("mt1", _leaves(2)), ("mt2", _leaves(3))], one),
                  str(path), one)
    return path


# ── (A) cap_kind in the catalog ────────────────────────────────────────────

def test_catalog_cap_kind_plasmid_nuclear_diploid():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save_mixed(tmp, one)
        cat = G.genome_catalog(str(path))
        by_label = {c["label"]: c["cap_kind"] for c in cat["chromosomes"]}
        assert by_label == {"stk": "plasmid", "min": "nuclear", "dip": "diploid"}, by_label


def test_catalog_cap_kind_native_equals_pure():
    """The native catalog cap_kind == the pure-Python derivation (C==Python)."""
    if not _native.has_native_genome():
        pytest.skip("native genome surface not loaded")
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save_mixed(tmp, one)
        native = json.loads(
            _native.genome_catalog_c(str(path), G._coupling_block_bytes(one)))["data"]
        pure = G._catalog_data(str(path), coupling=one)
        nk = {c["label"]: c["cap_kind"] for c in native["chromosomes"]}
        pk = {c["label"]: c["cap_kind"] for c in pure["chromosomes"]}
        assert nk == pk == {"stk": "plasmid", "min": "nuclear", "dip": "diploid"}


def test_v12_head_only_manifest_has_no_cap_kind_on_disk():
    """cap_kind is a DERIVED-on-read field — the head-only manifest.json on disk
    carries NO chromosomes array (so no cap_kind), keeping the format additive."""
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save_mixed(tmp, one)
        raw = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        data = raw.get("data", raw)
        assert "chromosomes" not in data       # v12+ head-only (derived on read)
        # but the read-derived catalog DOES carry it:
        assert all("cap_kind" in c for c in G.genome_catalog(str(path))["chromosomes"])


# ── (B) genome_census ───────────────────────────────────────────────────────

def test_census_mixed_nucleus():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save_mixed(tmp, one)
        cen = G.genome_census(str(path))
        assert cen["n_chromosomes"] == 3
        assert cen["types"] == {"plasmid": 1, "nuclear": 1, "diploid": 1}
        assert cen["total_leaves"] == 3 + 9 + 2
        assert cen["topology"] == "nuclear-like"
        assert cen["path"] == str(path)
        kinds = {c["label"]: c["type"] for c in cen["chromosomes"]}
        assert kinds == {"stk": "plasmid", "min": "nuclear", "dip": "diploid"}


def test_census_organelle_is_small_all_plasmid():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save_organelle(tmp, one)
        cen = G.genome_census(str(path))
        assert cen["types"] == {"plasmid": 2, "nuclear": 0, "diploid": 0}
        assert cen["topology"] == "organelle-like"       # total_leaves 5 <= 8*2


def test_census_plasmid_prokaryote_like():
    """A LARGE all-plasmid genome (many leaves per chromosome, > 8*n) is not
    organelle-scale → plasmid/prokaryote-like."""
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "prok.genome"
        # 1 plasmid chromosome with 20 leaves: 20 > 8*1 → not organelle-scale.
        strand = [G._pack_cap(G.CHROM_CAP_MARKER, "big", _DIM)] + \
                 [G.quad_turn(_leaf(i), one) for i in range(20)]
        G.genome_save(strand, str(path), one)
        cen = G.genome_census(str(path))
        assert cen["types"] == {"plasmid": 1, "nuclear": 0, "diploid": 0}
        assert cen["topology"] == "plasmid/prokaryote-like"


def test_census_native_equals_pure():
    if not _native.has_native_genome_census():
        pytest.skip("native genome_census not loaded")
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        path = _save_mixed(tmp, one)
        native = json.loads(
            _native.genome_census_c(str(path), G._coupling_block_bytes(one)))
        pure = G._census_from_catalog(
            G._catalog_data(str(path), coupling=one), str(path))
        assert native == pure


# ── (C) genome_registry ─────────────────────────────────────────────────────

def _build_cell(tmp, one):
    """A root with 2 genome dirs (nucleus + organelle) + a non-genome dir."""
    root = Path(tmp) / "cell"
    root.mkdir()
    G.genome_save(_mixed_genome_strand(one), str(root / "aaa_nucleus"), one)
    G.genome_save(G.plasmid([("mt1", _leaves(2)), ("mt2", _leaves(3))], one),
                  str(root / "bbb_mito"), one)
    (root / "not_a_genome").mkdir()                # ignored (no turns.bin/manifest)
    (root / "not_a_genome" / "readme.txt").write_text("x", encoding="utf-8")
    return root


def test_registry_cell_census():
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        root = _build_cell(tmp, one)
        reg = G.genome_registry(str(root))
        assert reg["n_genomes"] == 2                # the non-genome dir is ignored
        assert reg["root"] == str(root)
        names = [Path(g["path"]).name for g in reg["genomes"]]
        assert names == ["aaa_nucleus", "bbb_mito"]  # sorted by name
        topo = {Path(g["path"]).name: g["topology"] for g in reg["genomes"]}
        assert topo["aaa_nucleus"] == "nuclear-like"
        assert topo["bbb_mito"] == "organelle-like"


def test_registry_empty_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "empty"
        root.mkdir()
        reg = G.genome_registry(str(root))
        assert reg == {"root": str(root), "n_genomes": 0, "genomes": []}


def test_registry_native_equals_pure(monkeypatch):
    if not _native.has_native_genome_registry():
        pytest.skip("native genome_registry not loaded")
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        root = _build_cell(tmp, one)
        native = json.loads(
            _native.genome_registry_c(str(root), G._coupling_block_bytes(one)))
        # pure = the REAL fallback (native registry forced off) — the same os/pathlib
        # roll-up a no-native host runs. It must equal the C tree byte-for-byte,
        # INCLUDING the "root/name" child-path join (regression: on Windows pathlib's
        # "\\" join diverged from the native "/" — §96 parity).
        monkeypatch.setattr(_native, "has_native_genome_registry", lambda: False)
        pure = G.genome_registry(str(root), coupling=one)
        assert native == pure
