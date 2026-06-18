"""§44 follow-up (rc144): manifest.json is an OPTIONAL .fai cache, not mandatory.

UPSTREAM note (PR #687): the disk loaders hard-required manifest.json — delete it
and ``genome_load`` threw ``FileNotFoundError``. §44 says the strand (``turns.bin``)
is the SSoT and the manifest a rebuildable ``.fai`` cache. These tests prove every
loader reconstructs from ``turns.bin`` alone (given the_one for the leaf width), so a
genome can be shipped as ``turns.bin`` ONLY — the §43 "tar one file" goal.

numpy-free per the module's discipline (no numpy import, no np.*).
"""
import os
import shutil
import tempfile

import pytest

from srmech.amsc import genome as G
from srmech.amsc.genome import GenomeBoundingError
from srmech.amsc.hdc import klein4_random

DIM = 16


def _one():
    return klein4_random(DIM, seed=7)


def _build(path):
    """A 2-chromosome genome: a MULTI-GENE chromosome 'astro' + a single-kernel
    chromosome 'music'. Returns (the_one, save_data)."""
    one = _one()
    specs = [
        ("astro", [("orbits", [klein4_random(DIM, seed=s) for s in (1, 2)]),
                   ("spectra", [klein4_random(DIM, seed=3)])]),
        ("music", [("scales", [klein4_random(DIM, seed=9)])]),
    ]
    strand = G.genome(chromosomes=specs, the_one=one)
    data = G.genome_save(strand, path, the_one=one)
    return one, data


def _drop_manifest(path):
    os.remove(os.path.join(path, "manifest.json"))
    assert not os.path.exists(os.path.join(path, "manifest.json"))
    assert os.path.exists(os.path.join(path, "turns.bin"))


def test_catalog_rebuilt_by_scan_equals_saved_manifest():
    """The manifest-less rebuilt catalog == the genome_save manifest data EXACTLY —
    every field (offsets / hashes / leaf_counts / the_one) is derivable by scan."""
    d = tempfile.mkdtemp()
    try:
        one, saved = _build(d)
        with_manifest = G.genome_catalog(d)
        assert with_manifest == saved
        _drop_manifest(d)
        rebuilt = G.genome_catalog(d, the_one=one)
        assert rebuilt == saved, "rebuilt-by-scan catalog must equal the saved manifest"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_genome_load_whole_without_manifest():
    d = tempfile.mkdtemp()
    try:
        one, _ = _build(d)
        strand_ref, _, labels_ref = G.genome_load(d)          # manifest present
        _drop_manifest(d)
        strand, the_one, labels = G.genome_load(d, the_one=one)
        assert labels == labels_ref
        assert len(strand) == len(strand_ref)
        assert all(a == b for a, b in zip(strand, strand_ref))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_genome_load_subset_paged_without_manifest():
    d = tempfile.mkdtemp()
    try:
        one, _ = _build(d)
        _drop_manifest(d)
        strand, _, labels = G.genome_load(d, labels=["music"], the_one=one)
        assert labels == ["music"]
        assert len(strand) >= 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_genome_window_without_manifest():
    d = tempfile.mkdtemp()
    try:
        one, _ = _build(d)
        ref = G.genome_window(d, "astro")
        _drop_manifest(d)
        got = G.genome_window(d, "astro", the_one=one)
        assert len(got) == len(ref)
        assert all(a == b for a, b in zip(got, ref))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_genome_genes_without_manifest():
    d = tempfile.mkdtemp()
    try:
        one, _ = _build(d)
        ref = [(lbl, len(v)) for lbl, v in G.genome_genes(d, "astro")]
        _drop_manifest(d)
        got = [(lbl, len(v)) for lbl, v in G.genome_genes(d, "astro", the_one=one)]
        assert got == ref == [("orbits", 2), ("spectra", 1)]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_missing_manifest_without_the_one_raises_helpful_error():
    d = tempfile.mkdtemp()
    try:
        _build(d)
        _drop_manifest(d)
        with pytest.raises(GenomeBoundingError) as exc:
            G.genome_load(d)            # no the_one → cannot know leaf_dim
        assert "the_one" in str(exc.value)
        # NOT a bare FileNotFoundError
        assert not isinstance(exc.value, FileNotFoundError)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_tar_just_turns_bin_then_load():
    """The §43 goal: ship ONLY turns.bin (no sidecar) and load it elsewhere."""
    src = tempfile.mkdtemp()
    dst = tempfile.mkdtemp()
    try:
        one, _ = _build(src)
        ref, _, _ = G.genome_load(src)
        # "tar" exactly one file across to a fresh directory
        shutil.copy(os.path.join(src, "turns.bin"), os.path.join(dst, "turns.bin"))
        assert os.listdir(dst) == ["turns.bin"]
        strand, _, _ = G.genome_load(dst, the_one=one)
        assert all(a == b for a, b in zip(strand, ref))
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)


def test_genome_append_without_manifest_then_reindex():
    d = tempfile.mkdtemp()
    try:
        one, _ = _build(d)
        _drop_manifest(d)
        # append works manifest-less (the_one supplies the leaf width)
        new_data = G.genome_append(d, "extra", [klein4_random(DIM, seed=42)], one)
        labels = [c["label"] for c in new_data["chromosomes"]]
        assert labels == ["astro", "music", "extra"]
        # the append re-wrote the manifest (a fresh .fai cache)
        assert os.path.exists(os.path.join(d, "manifest.json"))
        assert G.genome_catalog(d) == new_data
    finally:
        shutil.rmtree(d, ignore_errors=True)
