"""§43 (rc150): loose↔packed — explode a packed genome to a dir of .chr files and
pack a dir of .chr files back into one packed genome (git's object model).

`genome_explode` is the packed→loose half: a genome's turns.bin (the "packfile")
becomes one self-contained, MPR-attested `.chr` bundle per chromosome (the "loose
objects"), named `<out_dir>/<label>.chr`. `genome_pack` is the loose→packed inverse
(git ``repack``-like): every `*.chr` in a dir is imported into one packed genome in
CANONICAL sorted-label order — so a packed genome is a well-defined function of the
chromosome SET (insertion order is not preserved; pack re-canonicalises). The
round-trip is byte-identical when the source is already in canonical sorted-label
order, and content-preserving (window-equal per chromosome) otherwise.

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


def _one(seed=7):
    return klein4_random(DIM, seed=seed)


def _build(path, one, labels_seeds):
    specs = [(lbl, [(lbl[0], [klein4_random(DIM, seed=s) for s in seeds])])
             for lbl, seeds in labels_seeds]
    return G.genome_save(G.genome(chromosomes=specs, the_one=one), path, the_one=one)


def _body(path):
    with open(os.path.join(path, "turns.bin"), "rb") as f:
        return f.read()


def _manifest(path):
    with open(os.path.join(path, "manifest.json"), "rb") as f:
        return f.read()


def test_explode_writes_one_chr_per_chromosome():
    """explode writes <out_dir>/<label>.chr for every chromosome; each is a valid,
    self-verifying bundle (re-importable)."""
    d, loose = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        one = _one()
        _build(d, one, [("alpha", (1, 2)), ("beta", (3,)), ("gamma", (4, 5, 6))])
        written = G.genome_explode(d, loose)
        assert [w["label"] for w in written] == ["alpha", "beta", "gamma"]
        for w in written:
            assert os.path.isfile(w["path"])
            assert w["path"].endswith(f"{w['label']}.chr")
        files = sorted(f for f in os.listdir(loose) if f.endswith(".chr"))
        assert files == ["alpha.chr", "beta.chr", "gamma.chr"]
    finally:
        shutil.rmtree(d, ignore_errors=True)
        shutil.rmtree(loose, ignore_errors=True)


def test_explode_then_pack_round_trips_byte_identical():
    """A canonical (sorted-label) genome → explode → pack reproduces turns.bin AND
    manifest.json BYTE-IDENTICALLY (the lossless loose↔packed round-trip)."""
    src, loose, dst = (tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp())
    shutil.rmtree(dst)                              # pack seeds a fresh dest
    try:
        one = _one()
        _build(src, one, [("alpha", (1, 2)), ("beta", (3,)), ("gamma", (4, 5, 6))])
        G.genome_explode(src, loose)
        packed = G.genome_pack(loose, dst)
        assert [c["label"] for c in packed["chromosomes"]] == ["alpha", "beta", "gamma"]
        assert _body(dst) == _body(src)             # turns.bin byte-identical
        assert _manifest(dst) == _manifest(src)     # manifest.json byte-identical
    finally:
        for p in (src, loose, dst):
            shutil.rmtree(p, ignore_errors=True)


def test_pack_canonicalises_a_non_sorted_genome():
    """A genome built OUT of sorted-label order → explode → pack RE-CANONICALISES to
    sorted-label order (different bytes) while preserving every chromosome's data
    (per-chromosome window equality)."""
    src, loose, dst = (tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp())
    shutil.rmtree(dst)
    try:
        one = _one()
        _build(src, one, [("gamma", (4, 5, 6)), ("alpha", (1, 2)), ("beta", (3,))])
        G.genome_explode(src, loose)
        packed = G.genome_pack(loose, dst)
        assert [c["label"] for c in packed["chromosomes"]] == ["alpha", "beta", "gamma"]
        # re-canonicalised: NOT byte-identical, but every chromosome round-trips.
        assert _body(dst) != _body(src)
        for lbl in ("alpha", "beta", "gamma"):
            assert G.genome_window(dst, lbl) == G.genome_window(src, lbl)
    finally:
        for p in (src, loose, dst):
            shutil.rmtree(p, ignore_errors=True)


def test_pack_rejects_mixed_the_one_and_empty_dir():
    """Two .chr coupled to DIFFERENT invariants cannot pack into one genome
    (GenomeBoundingError); an empty loose dir is a ValueError."""
    a, b, loose, dst = (tempfile.mkdtemp(), tempfile.mkdtemp(),
                        tempfile.mkdtemp(), tempfile.mkdtemp())
    shutil.rmtree(dst)
    try:
        _build(a, _one(seed=7), [("alpha", (1, 2))])
        _build(b, _one(seed=8), [("beta", (3,))])    # different the_one
        G.genome_export(a, "alpha", os.path.join(loose, "alpha.chr"))
        G.genome_export(b, "beta", os.path.join(loose, "beta.chr"))
        with pytest.raises(GenomeBoundingError):
            G.genome_pack(loose, dst)
        empty = tempfile.mkdtemp()
        with pytest.raises(ValueError):
            G.genome_pack(empty, dst)
        shutil.rmtree(empty, ignore_errors=True)
    finally:
        for p in (a, b, loose, dst):
            shutil.rmtree(p, ignore_errors=True)


def test_pack_rejects_duplicate_label():
    """Two .chr with the SAME label (same the_one) cannot both pack — the second is
    a duplicate (ValueError)."""
    src, loose, dst = (tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp())
    shutil.rmtree(dst)
    try:
        one = _one()
        _build(src, one, [("alpha", (1, 2))])
        G.genome_export(src, "alpha", os.path.join(loose, "alpha.chr"))
        # a second bundle with the same label but a different filename
        G.genome_export(src, "alpha", os.path.join(loose, "alpha-copy.chr"))
        with pytest.raises(ValueError):
            G.genome_pack(loose, dst)
    finally:
        for p in (src, loose, dst):
            shutil.rmtree(p, ignore_errors=True)


def test_explode_rejects_unsafe_label():
    """A chromosome label that is not filename-safe cannot become a <label>.chr
    loose object (ValueError)."""
    d, loose = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        one = _one()
        _build(d, one, [("a/b", (1,)), ("ok", (2,))])
        with pytest.raises(ValueError):
            G.genome_explode(d, loose)
    finally:
        shutil.rmtree(d, ignore_errors=True)
        shutil.rmtree(loose, ignore_errors=True)


def test_explode_manifest_less_source():
    """§44: explode works from a manifest-less source (turns.bin only) given the_one;
    the loose bundles round-trip via pack identically to a manifest-present explode."""
    src, loose, dst = (tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp())
    shutil.rmtree(dst)
    try:
        one = _one()
        _build(src, one, [("alpha", (1, 2)), ("beta", (3,))])
        os.remove(os.path.join(src, "manifest.json"))   # strand is the SSoT
        written = G.genome_explode(src, loose, the_one=one)
        assert [w["label"] for w in written] == ["alpha", "beta"]
        packed = G.genome_pack(loose, dst)
        assert [c["label"] for c in packed["chromosomes"]] == ["alpha", "beta"]
        for lbl in ("alpha", "beta"):
            assert G.genome_window(dst, lbl) == G.genome_window(src, lbl, the_one=one)
    finally:
        for p in (src, loose, dst):
            shutil.rmtree(p, ignore_errors=True)


def test_pack_ignores_non_chr_files():
    """pack globs *.chr only — stray files in the loose dir are ignored."""
    src, loose, dst = (tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp())
    shutil.rmtree(dst)
    try:
        one = _one()
        _build(src, one, [("alpha", (1, 2)), ("beta", (3,))])
        G.genome_explode(src, loose)
        with open(os.path.join(loose, "README.txt"), "w") as f:
            f.write("not a chromosome bundle")
        packed = G.genome_pack(loose, dst)
        assert [c["label"] for c in packed["chromosomes"]] == ["alpha", "beta"]
    finally:
        for p in (src, loose, dst):
            shutil.rmtree(p, ignore_errors=True)
