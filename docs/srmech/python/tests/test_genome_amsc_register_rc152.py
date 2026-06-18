"""§43 (rc152): bundling↔AMSC compose — register a dir of loose .chr bundles as
AMSC attested sources (genome_register_attested).

The §43 NEXT after loose↔packed: a genome's exploded `.chr` dir becomes a set of
AMSC attested sources (one per chromosome, F729), so `list_attested_sources`
surfaces each chromosome. Composes the EXISTING AMSC catalog
(`register_attested_root` + the `literature_curated` descriptor contract); the
chromosome's own MPR attestation (its `.chr`'s `attestation.response_sha256` ==
the region hash, echoed into `row.ndjson`) IS the provenance — NO parallel
attestation is minted (F730).

numpy-free per the module's discipline (no numpy import, no np.*).
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import catalog
from srmech.amsc import descriptor as D
from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_random

DIM = 16


@pytest.fixture(autouse=True)
def _clean_registry():
    """Each test starts + ends with a clean external-root registry (the catalog
    registry is process-global state)."""
    catalog._clear_registered_roots()
    yield
    catalog._clear_registered_roots()


def _one(seed=7):
    return klein4_random(DIM, seed=seed)


def _build_chr_dir(labels_seeds):
    """Build a genome, explode it to a fresh .chr dir, return (chr_dir, one)."""
    one = _one()
    src, loose = tempfile.mkdtemp(), tempfile.mkdtemp()
    specs = [(lbl, [(lbl[0], [klein4_random(DIM, seed=s) for s in seeds])])
             for lbl, seeds in labels_seeds]
    G.genome_save(G.genome(chromosomes=specs, the_one=one), src, the_one=one)
    G.genome_explode(src, loose, the_one=one)
    return loose, one, src


def test_register_surfaces_each_chromosome_as_amsc_source():
    """genome_register_attested writes a per-chromosome descriptor + row and
    surfaces each chromosome in list_attested_sources (keyed by label)."""
    chr_dir, _one_hv, _src = _build_chr_dir(
        [("alpha", (1, 2)), ("beta", (3,)), ("gamma", (4, 5, 6))])
    amsc_root = tempfile.mkdtemp()

    before = catalog.list_attested_sources()["n_sources"]
    res = G.genome_register_attested(chr_dir, amsc_root, source="srmech.genome.test")
    assert res["ok"] is True
    assert res["register"]["ok"] is True
    assert sorted(c["label"] for c in res["chromosomes"]) == ["alpha", "beta", "gamma"]

    srcs = catalog.list_attested_sources()
    keys = {s["key"] for s in srcs["sources"]}
    assert {"alpha", "beta", "gamma"} <= keys
    assert srcs["n_sources"] == before + 3
    # each registered source is a literature_curated AMSC source for the row schema.
    mine = [s for s in srcs["sources"] if s["key"] in ("alpha", "beta", "gamma")]
    assert all(s["adapter"] == "literature_curated" for s in mine)
    assert all(s["data_schema_id"] == "srmech.genome_chromosome.row.v1" for s in mine)


def test_descriptor_validates_under_amsc_loader():
    """Each generated descriptor.toml is a VALID AMSC descriptor (load_descriptor
    accepts it — all required sections + fields present)."""
    chr_dir, _one_hv, _src = _build_chr_dir([("alpha", (1,)), ("beta", (2,))])
    amsc_root = tempfile.mkdtemp()
    res = G.genome_register_attested(chr_dir, amsc_root, source="srmech.genome.test")
    for c in res["chromosomes"]:
        desc = D.load_descriptor(Path(c["descriptor_path"]))
        assert desc.key == c["label"]
        assert desc.fetch["adapter"] == "literature_curated"
        assert desc.fetch["ndjson_path"] == "row.ndjson"


def test_no_parallel_attestation_row_carries_the_chr_provenance():
    """The row.ndjson's region_sha256 IS the .chr's existing attestation
    (response_sha256 == region hash) — composed, not re-minted (F730)."""
    chr_dir, _one_hv, _src = _build_chr_dir([("alpha", (1, 2))])
    amsc_root = tempfile.mkdtemp()
    res = G.genome_register_attested(chr_dir, amsc_root, source="srmech.genome.test")
    c = res["chromosomes"][0]
    # the .chr's own attestation.response_sha256
    chr_text = open(os.path.join(chr_dir, "alpha.chr"), encoding="utf-8").read()
    chr_rec = json.loads(chr_text)
    chr_region_sha = chr_rec["attestation"]["response_sha256"]
    assert chr_rec["data"]["region"]["sha256"] == chr_region_sha  # .chr self-consistent
    # the AMSC row echoes exactly that — no new hash minted
    row = json.loads(open(c["row_path"], encoding="utf-8").read().strip())
    assert row["region_sha256"] == chr_region_sha
    assert c["region_sha256"] == chr_region_sha


def test_empty_dir_rejected():
    """A directory with no .chr files is a ValueError."""
    empty, amsc_root = tempfile.mkdtemp(), tempfile.mkdtemp()
    with pytest.raises(ValueError, match="no .chr files"):
        G.genome_register_attested(empty, amsc_root, source="srmech.genome.test")


def test_register_is_idempotent():
    """Re-registering the same root is a no-op (register_attested_root idempotent);
    list_attested_sources does not double-count."""
    chr_dir, _one_hv, _src = _build_chr_dir([("alpha", (1,)), ("beta", (2,))])
    amsc_root = tempfile.mkdtemp()
    G.genome_register_attested(chr_dir, amsc_root, source="srmech.genome.test")
    n1 = catalog.list_attested_sources()["n_sources"]
    G.genome_register_attested(chr_dir, amsc_root, source="srmech.genome.test")
    n2 = catalog.list_attested_sources()["n_sources"]
    assert n1 == n2
