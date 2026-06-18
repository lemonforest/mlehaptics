"""§43 (rc148): the chromosome as a single bundleable, MPR-attested .chr file.

UPSTREAM GENOMEPLAN Stage 2: now that §44 made the strand self-describing and §45
made it editable in place, a chromosome can be EXPORTED as one self-contained,
content-addressed file (genome_export → .chr), shipped, and re-IMPORTED into a
genome (genome_import) self-verifying — the "tar one chromosome, ship it" goal.

A .chr is ONE MPR record (composes srmech.amsc.format — NOT a parallel
attestation): its `data` carries the chromosome's region (CHROM cap + coupled
turns) + the_one; its `attestation.response_sha256` IS the region hash, so an
import re-hashes the region and self-verifies.

numpy-free per the module's discipline (no numpy import, no np.*).
"""
import json
import os
import shutil
import tempfile

import pytest

from srmech.amsc import genome as G
from srmech.amsc.genome import GenomeBoundingError, GENOME_CHR_SCHEMA_ID
from srmech.amsc.format import MPRRecord, validate_mpr_record
from srmech.amsc.hdc import klein4_random

DIM = 16


def _one(seed=7):
    return klein4_random(DIM, seed=seed)


def _build3(path, one):
    specs = [
        ("alpha", [("a", [klein4_random(DIM, seed=s) for s in (1, 2)])]),
        ("beta",  [("b", [klein4_random(DIM, seed=3)])]),
        ("gamma", [("c", [klein4_random(DIM, seed=s) for s in (4, 5, 6)])]),
    ]
    return G.genome_save(G.genome(chromosomes=specs, the_one=one), path, the_one=one)


def _read_body(path):
    with open(os.path.join(path, "turns.bin"), "rb") as f:
        return f.read()


def _span(body, entry):
    off = int(entry["byte_offset"])
    return body[off:off + int(entry["byte_len"])]


def test_chr_is_a_valid_mpr_record():
    """A .chr is one MPR-v1 record (validates) tagged as a chromosome bundle, with
    response_sha256 == the region hash (content-addressed)."""
    d = tempfile.mkdtemp()
    try:
        one = _one()
        saved = _build3(d, one)
        chr_path = os.path.join(d, "beta.chr")
        cdata = G.genome_export(d, "beta", chr_path)
        payload = json.loads(open(chr_path, encoding="utf-8").read())
        rec = MPRRecord(mpr_version=payload["mpr_version"], data=payload["data"],
                        data_schema_id=payload["data_schema_id"],
                        attestation=payload["attestation"],
                        rendering=payload["rendering"])
        validate_mpr_record(rec)                       # MPR-v1 structure OK
        assert rec.data_schema_id == GENOME_CHR_SCHEMA_ID
        assert rec.attestation["response_sha256"] == cdata["region"]["sha256"]
        assert cdata["label"] == "beta" and cdata["leaf_dim"] == DIM
        # the .chr region == beta's body span in the source genome (byte-for-byte)
        by = {c["label"]: c for c in saved["chromosomes"]}
        assert bytes.fromhex(cdata["region"]["hex"]) == _span(_read_body(d), by["beta"])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_export_then_import_seeds_byte_identical_genome():
    """Importing a .chr into an empty dest SEEDS a 1-chromosome genome whose
    turns.bin == the exported region VERBATIM (the §43 tar-one-chromosome flow)."""
    src, dst = tempfile.mkdtemp(), tempfile.mkdtemp()
    shutil.rmtree(dst)                                 # dst must not exist yet
    try:
        one = _one()
        _build3(src, one)
        chr_path = os.path.join(src, "gamma.chr")
        cdata = G.genome_export(src, "gamma", chr_path)
        seeded = G.genome_import(chr_path, dst)
        assert [c["label"] for c in seeded["chromosomes"]] == ["gamma"]
        assert _read_body(dst) == bytes.fromhex(cdata["region"]["hex"])
        # the seeded genome pages gamma back identically to the source
        assert G.genome_window(dst, "gamma") == G.genome_window(src, "gamma")
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)


def test_export_then_import_appends_byte_for_byte():
    """Importing a .chr into an EXISTING genome (same the_one) appends the region
    byte-for-byte — the dest body == old body + the region VERBATIM."""
    src, dst = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        one = _one()
        _build3(src, one)                              # src has alpha/beta/gamma
        # a separate 1-chromosome dest coupled to the SAME the_one
        G.genome_save(G.genome(chromosomes=[("solo", [("s", [klein4_random(DIM, seed=9)])])],
                               the_one=one), dst, the_one=one)
        before = _read_body(dst)
        chr_path = os.path.join(src, "beta.chr")
        cdata = G.genome_export(src, "beta", chr_path)
        new = G.genome_import(chr_path, dst)
        assert [c["label"] for c in new["chromosomes"]] == ["solo", "beta"]
        assert _read_body(dst) == before + bytes.fromhex(cdata["region"]["hex"])
        assert G.genome_window(dst, "beta") == G.genome_window(src, "beta")
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)


def test_import_self_verifies_a_tampered_region():
    """A flipped byte in the .chr region breaks its content-address — genome_import
    raises GenomeBoundingError (self-verifying), not a silent bad import."""
    src, dst = tempfile.mkdtemp(), tempfile.mkdtemp()
    shutil.rmtree(dst)
    try:
        one = _one()
        _build3(src, one)
        chr_path = os.path.join(src, "beta.chr")
        G.genome_export(src, "beta", chr_path)
        payload = json.loads(open(chr_path, encoding="utf-8").read())
        # flip the last region hex nibble (Class K) WITHOUT updating response_sha256
        rh = payload["data"]["region"]["hex"]
        payload["data"]["region"]["hex"] = rh[:-1] + ("0" if rh[-1] != "0" else "1")
        with open(chr_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
        with pytest.raises(GenomeBoundingError):
            G.genome_import(chr_path, dst)
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)


def test_import_rejects_the_one_mismatch_and_dup_label():
    """Appending into a genome with a DIFFERENT the_one is rejected (coupled to a
    different invariant); a duplicate label is rejected too."""
    src, dst = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        one_a, one_b = _one(seed=7), _one(seed=8)
        _build3(src, one_a)                            # src coupled to one_a
        # dst coupled to a DIFFERENT invariant one_b
        G.genome_save(G.genome(chromosomes=[("beta", [("b", [klein4_random(DIM, seed=3)])])],
                               the_one=one_b), dst, the_one=one_b)
        chr_path = os.path.join(src, "beta.chr")
        G.genome_export(src, "beta", chr_path)
        with pytest.raises(GenomeBoundingError):        # the_one mismatch
            G.genome_import(chr_path, dst)
        # same-invariant dest with the label already present -> ValueError
        dst2 = tempfile.mkdtemp()
        G.genome_save(G.genome(chromosomes=[("beta", [("b", [klein4_random(DIM, seed=3)])])],
                               the_one=one_a), dst2, the_one=one_a)
        with pytest.raises(ValueError):
            G.genome_import(chr_path, dst2)
        shutil.rmtree(dst2, ignore_errors=True)
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)


def test_export_missing_label_raises():
    d = tempfile.mkdtemp()
    try:
        _build3(d, _one())
        with pytest.raises(ValueError):
            G.genome_export(d, "nope", os.path.join(d, "nope.chr"))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_chr_export_works_manifest_less():
    """§44: a .chr can be exported from a manifest-less source (turns.bin only),
    given the_one — and re-imports identically."""
    src, dst = tempfile.mkdtemp(), tempfile.mkdtemp()
    shutil.rmtree(dst)
    try:
        one = _one()
        _build3(src, one)
        os.remove(os.path.join(src, "manifest.json"))   # strand is the SSoT
        chr_path = os.path.join(src, "alpha.chr")
        cdata = G.genome_export(src, "alpha", chr_path, the_one=one)
        seeded = G.genome_import(chr_path, dst)
        assert [c["label"] for c in seeded["chromosomes"]] == ["alpha"]
        assert _read_body(dst) == bytes.fromhex(cdata["region"]["hex"])
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)
