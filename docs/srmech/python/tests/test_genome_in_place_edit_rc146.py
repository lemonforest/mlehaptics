"""§45 (rc146): IN-PLACE genome edit — biology excises, it does not re-synthesize.

UPSTREAM GENOMEPLAN Stage 1: now that §44 (rc144/rc145) made the loaders reconstruct
the catalog by scanning ``turns.bin`` (the strand is the SSoT, ``manifest.json`` an
optional ``.fai`` cache), an in-place edit is a pure BYTE-level splice on the
self-describing body:

* ``genome_remove(path, label)`` splices the chromosome's ``[byte_offset,
  byte_offset+byte_len)`` span out of ``turns.bin`` and leaves every OTHER
  chromosome's coupled bytes byte-identical (only relocated) — NO kernel is decoded /
  re-coupled.
* ``genome_replace(path, label, leaves, the_one)`` splices a fresh chromosome in at
  the same position.

Both re-derive the optional manifest by scanning. These tests prove the splice is
EXACT (the new ``turns.bin`` is the survivor spans concatenated verbatim), so the edit
is genuinely in-place rather than a whole-genome re-pack.

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


def _read_body(path):
    with open(os.path.join(path, "turns.bin"), "rb") as f:
        return f.read()


def _span(body, entry):
    off = int(entry["byte_offset"])
    return body[off:off + int(entry["byte_len"])]


def _build3(path):
    """A 3-chromosome genome alpha/beta/gamma. Returns (the_one, save_data)."""
    one = _one()
    specs = [
        ("alpha", [("a", [klein4_random(DIM, seed=s) for s in (1, 2)])]),
        ("beta",  [("b", [klein4_random(DIM, seed=3)])]),
        ("gamma", [("c", [klein4_random(DIM, seed=s) for s in (4, 5, 6)])]),
    ]
    strand = G.genome(chromosomes=specs, the_one=one)
    data = G.genome_save(strand, path, the_one=one)
    return one, data


def _build1(path):
    one = _one()
    strand = G.genome(chromosomes=[("solo", [("g", [klein4_random(DIM, seed=1)])])],
                      the_one=one)
    data = G.genome_save(strand, path, the_one=one)
    return one, data


def _drop_manifest(path):
    os.remove(os.path.join(path, "manifest.json"))


# ───────────────────────────── genome_remove ─────────────────────────────


def test_remove_middle_is_pure_byte_splice():
    """Excising the MIDDLE chromosome yields turns.bin == survivor spans concatenated
    VERBATIM (the surviving coupled bytes are byte-identical, only relocated)."""
    d = tempfile.mkdtemp()
    try:
        _, saved = _build3(d)
        body0 = _read_body(d)
        by = {c["label"]: c for c in saved["chromosomes"]}
        ra, rc = _span(body0, by["alpha"]), _span(body0, by["gamma"])
        wa_ref, wc_ref = G.genome_window(d, "alpha"), G.genome_window(d, "gamma")

        new = G.genome_remove(d, "beta")

        assert _read_body(d) == ra + rc, "turns.bin must be the survivor spans verbatim"
        assert [c["label"] for c in new["chromosomes"]] == ["alpha", "gamma"]
        assert new["n_turns"] == saved["n_turns"] - by["beta"]["byte_len"] // DIM
        # survivors reload byte-for-byte (relocation did not re-couple them)
        assert G.genome_window(d, "alpha") == wa_ref
        assert G.genome_window(d, "gamma") == wc_ref
        # the manifest is a fresh .fai cache == the returned data
        assert G.genome_catalog(d) == new
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_remove_first_relocates_survivors_verbatim():
    """Excising the FIRST chromosome shifts every survivor's byte_offset but keeps its
    coupled bytes identical — the body is the remaining spans concatenated."""
    d = tempfile.mkdtemp()
    try:
        _, saved = _build3(d)
        body0 = _read_body(d)
        by = {c["label"]: c for c in saved["chromosomes"]}
        rb, rc = _span(body0, by["beta"]), _span(body0, by["gamma"])

        new = G.genome_remove(d, "alpha")

        assert _read_body(d) == rb + rc
        assert [c["label"] for c in new["chromosomes"]] == ["beta", "gamma"]
        assert int(new["chromosomes"][0]["byte_offset"]) == 0   # beta slid to the front
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_remove_only_chromosome_raises():
    d = tempfile.mkdtemp()
    try:
        _build1(d)
        with pytest.raises(ValueError) as exc:
            G.genome_remove(d, "solo")
        assert "only chromosome" in str(exc.value)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_remove_missing_label_raises():
    d = tempfile.mkdtemp()
    try:
        _build3(d)
        with pytest.raises(ValueError):
            G.genome_remove(d, "nope")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_remove_without_manifest_then_reindex():
    """§44: a remove on a manifest-less genome (turns.bin only) rebuilds the .fai."""
    d = tempfile.mkdtemp()
    try:
        one, saved = _build3(d)
        body0 = _read_body(d)
        by = {c["label"]: c for c in saved["chromosomes"]}
        ra, rc = _span(body0, by["alpha"]), _span(body0, by["gamma"])
        _drop_manifest(d)

        new = G.genome_remove(d, "beta", the_one=one)

        assert _read_body(d) == ra + rc
        assert [c["label"] for c in new["chromosomes"]] == ["alpha", "gamma"]
        assert os.path.exists(os.path.join(d, "manifest.json"))   # .fai rebuilt
        assert G.genome_catalog(d) == new
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_remove_then_tar_just_turns_bin():
    """After an in-place excise, the body alone (no sidecar) still reloads correctly."""
    src, dst = tempfile.mkdtemp(), tempfile.mkdtemp()
    try:
        one, _ = _build3(src)
        G.genome_remove(src, "beta")
        ref, _, ref_labels = G.genome_load(src)
        shutil.copy(os.path.join(src, "turns.bin"), os.path.join(dst, "turns.bin"))
        assert os.listdir(dst) == ["turns.bin"]
        strand, _, labels = G.genome_load(dst, the_one=one)
        assert labels == ref_labels == ["alpha", "gamma"]
        assert all(a == b for a, b in zip(strand, ref))
    finally:
        shutil.rmtree(src, ignore_errors=True)
        shutil.rmtree(dst, ignore_errors=True)


def test_remove_then_append_roundtrip():
    """Excise leaves a valid, re-derivable body — appending the kernel back works."""
    d = tempfile.mkdtemp()
    try:
        one, _ = _build3(d)
        G.genome_remove(d, "beta")
        new = G.genome_append(d, "beta", [klein4_random(DIM, seed=99)], one)
        assert [c["label"] for c in new["chromosomes"]] == ["alpha", "gamma", "beta"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ───────────────────────────── genome_replace ────────────────────────────


def test_replace_is_pure_byte_splice_in_place():
    """genome_replace swaps ONE chromosome's span for a fresh region; the OTHER
    chromosomes' bytes are byte-identical (in-place edit, not a re-pack)."""
    d = tempfile.mkdtemp()
    try:
        one, saved = _build3(d)
        body0 = _read_body(d)
        by = {c["label"]: c for c in saved["chromosomes"]}
        ra, rc = _span(body0, by["alpha"]), _span(body0, by["gamma"])
        wa_ref, wc_ref = G.genome_window(d, "alpha"), G.genome_window(d, "gamma")

        new_leaves = [klein4_random(DIM, seed=s) for s in (20, 21, 22, 23)]
        new_region = b"".join(G._leaf_blocks(G.chromosome(new_leaves, one, label="beta")))

        new = G.genome_replace(d, "beta", new_leaves, one)

        assert _read_body(d) == ra + new_region + rc
        assert [c["label"] for c in new["chromosomes"]] == ["alpha", "beta", "gamma"]
        # the new content is paged back; the neighbours are untouched
        assert len(G.genome_window(d, "beta")) == len(new_leaves)
        assert G.genome_window(d, "alpha") == wa_ref
        assert G.genome_window(d, "gamma") == wc_ref
        assert G.genome_catalog(d) == new
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_replace_missing_label_raises():
    d = tempfile.mkdtemp()
    try:
        one, _ = _build3(d)
        with pytest.raises(ValueError):
            G.genome_replace(d, "nope", [klein4_random(DIM, seed=1)], one)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_replace_wrong_the_one_dim_raises():
    d = tempfile.mkdtemp()
    try:
        _build3(d)
        wrong = klein4_random(DIM * 2, seed=1)          # wrong leaf width
        with pytest.raises(ValueError) as exc:
            G.genome_replace(d, "beta", [klein4_random(DIM, seed=1)], wrong)
        assert "leaf_dim" in str(exc.value)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_remove_rejects_corrupt_body():
    """The whole-body integrity bound fires before an in-place edit on a flipped byte."""
    d = tempfile.mkdtemp()
    try:
        _build3(d)
        body = bytearray(_read_body(d))
        body[-1] ^= 0x01                                 # flip one byte (Class K)
        with open(os.path.join(d, "turns.bin"), "wb") as f:
            f.write(bytes(body))
        with pytest.raises(GenomeBoundingError):
            G.genome_remove(d, "beta")
    finally:
        shutil.rmtree(d, ignore_errors=True)
