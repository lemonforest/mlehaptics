"""rc115 (issue #1245 ask (b), UPSTREAM §56) — genome O(1)-AMORTISED append +
non-quadratic pack + the region-chain hash contract (format v4).

rc114 made a data turn 4 Klein-4 symbols/byte (ask (a)); it deliberately kept the
whole-body ``body_sha256`` — which cannot be recomputed in O(1) on append. ask (b)
changes that contract:

  * the manifest gains a ``regions`` array — one {byte_offset, byte_len, sha256}
    per chromosome (its FULL-region digest, == the chromosome's ``.chr`` / AMSC
    provenance unit), so a region hash is the O(1) provenance unit;
  * ``body_sha256`` becomes the REGION CHAIN Hn = sha256(Hn-1 || region_n) seeded
    by H0 = sha256("") — O(1)-maintainable on append (extend the head), yet
    re-verifiable from the file (re-hash each region, re-fold) AND body-derivable
    by a §44 scan (so a rebuild-by-scan reproduces it byte-identically);
  * ``genome_append`` TAIL-EXTENDS turns.bin + updates the manifest in O(1) — it
    never reads / rewrites / re-hashes the whole body; and
  * ``genome_pack`` compacts in a SINGLE pass (linear), not the old O(N²) import.

Proven here: the contract's shape, the O(1)-append invariants (prior entries
byte-identical, chain extension, no whole-body rewrite), the re-verifiability
(a flipped region byte fails), the §44 rebuild==written invariant on v4, the
provenance-unit unification (region sha == the .chr region hash), and pack
round-trip exactness. Timings live in notes/rc114_genome_bitpack_bench.py.

numpy-free per the genome module's discipline.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from srmech.amsc import genome as G
from srmech.amsc.format import sha256_bytes
from srmech.amsc.hdc import klein4_random

_DIM = 24


def _one():
    return klein4_random(_DIM, seed=7)


def _leaves(n, base=0):
    pool = [klein4_random(_DIM, seed=s + base) for s in range(8)]
    return [pool[i % 8] for i in range(n)]


def _as_lists(xs):
    return [list(x) for x in xs]


# ── the v4 manifest shape + the region chain ────────────────────────────────

def test_save_writes_v4_regions_and_chain(tmp_path):
    """A fresh save writes format_version 5 (rc121 §60 writer) with a regions
    array (one per chromosome, tiling the body) and body_sha256 = the region
    chain (the §56/v4 regions machinery is unchanged under the v5 writer)."""
    one = _one()
    strand = G.genome({"a": _leaves(5), "b": _leaves(3, base=10)}, one)
    man = G.genome_save(strand, tmp_path / "g", the_one=one)

    assert man["format_version"] == 6
    assert [r["byte_offset"] for r in man["regions"]] == \
        [c["byte_offset"] for c in man["chromosomes"]]
    # regions tile the body contiguously from 0
    off = 0
    body = (tmp_path / "g" / "turns.bin").read_bytes()
    for r in man["regions"]:
        assert r["byte_offset"] == off
        assert r["sha256"] == sha256_bytes(body[off:off + r["byte_len"]])
        off += r["byte_len"]
    assert off == len(body)
    # body_sha256 IS the chain over the region digests (H0 = sha256(b""))
    acc = sha256_bytes(b"")
    for r in man["regions"]:
        acc = sha256_bytes(bytes.fromhex(acc) + bytes.fromhex(r["sha256"]))
    assert man["body_sha256"] == acc
    # the MPR attestation.response_sha256 IS the chain head (still re-verifiable)
    import json
    rec = json.loads((tmp_path / "g" / "manifest.json").read_text("utf-8"))
    assert rec["attestation"]["response_sha256"] == man["body_sha256"]


# ── O(1) append: prior bytes/entries untouched, chain extended ──────────────

def test_append_is_tail_extend_prior_untouched(tmp_path):
    """Append tail-extends turns.bin (prior bytes an EXACT prefix) and only
    APPENDS a chromosome + region entry + extends the chain — every prior entry
    byte-identical, n_turns grows by the appended block count."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  the_one=one)
    man0 = G.genome_catalog(tmp_path / "g")
    body0 = (tmp_path / "g" / "turns.bin").read_bytes()

    new = _leaves(6, base=20)
    man1 = G.genome_append(tmp_path / "g", "c1", new, one)
    body1 = (tmp_path / "g" / "turns.bin").read_bytes()

    assert body1[:len(body0)] == body0                    # append-only prefix
    region = body1[len(body0):]
    assert man1["chromosomes"][:1] == man0["chromosomes"]  # prior entry identical
    assert man1["regions"][:1] == man0["regions"]          # prior region identical
    assert man1["chromosomes"][1]["byte_offset"] == len(body0)
    assert man1["regions"][1]["sha256"] == sha256_bytes(region)
    # the chain extended in O(1) from the prior head
    assert man1["body_sha256"] == sha256_bytes(
        bytes.fromhex(man0["body_sha256"]) + bytes.fromhex(sha256_bytes(region)))
    assert man1["n_turns"] == man0["n_turns"] + 1 + 6      # 1 cap + 6 turns
    # the appended chromosome reads back leaf-for-leaf
    win = G.genome_window(tmp_path / "g", "c1")
    assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(new)


def test_rebuild_by_scan_equals_written_manifest_v4(tmp_path):
    """§44 held across the v4 contract: after several appends, deleting the
    manifest and rebuilding-by-scan reproduces the WRITTEN manifest EXACTLY
    (regions + chain included) — the chain is a pure function of the body."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  the_one=one)
    for k in range(1, 5):
        written = G.genome_append(tmp_path / "g", f"c{k}", _leaves(k + 2, base=k),
                                  one)
    (tmp_path / "g" / "manifest.json").unlink()
    rebuilt = G.genome_catalog(tmp_path / "g", the_one=one)
    assert rebuilt == written


# ── re-verifiability: a flipped region byte fails the integrity bound ────────

def test_flipped_region_byte_fails_integrity(tmp_path):
    """The region chain is re-verifiable: corrupting one body byte fails the
    whole-genome load (a GenomeBoundingError) — the region hash + chain catch it."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  the_one=one)
    G.genome_append(tmp_path / "g", "c1", _leaves(6, base=20), one)
    body = bytearray((tmp_path / "g" / "turns.bin").read_bytes())
    body[-1] ^= 0x01                                       # flip a tail byte
    (tmp_path / "g" / "turns.bin").write_bytes(bytes(body))
    with pytest.raises(G.GenomeBoundingError):
        G.genome_load(tmp_path / "g")


# ── provenance-unit unification: region sha == the .chr region hash ─────────

def test_region_sha_is_the_chr_region_hash(tmp_path):
    """The manifest's per-chromosome region sha256 IS the .chr bundle's region
    hash (the AMSC provenance unit register_attested uses) — one hash, two views."""
    one = _one()
    G.genome_save(G.chromosome(_leaves(4), one, label="c0"), tmp_path / "g",
                  the_one=one)
    G.genome_append(tmp_path / "g", "c1", _leaves(6, base=20), one)
    man = G.genome_catalog(tmp_path / "g")
    by_label = {c["label"]: r for c, r in zip(man["chromosomes"], man["regions"])}
    for label in ("c0", "c1"):
        cdata = G.genome_export(tmp_path / "g", label, tmp_path / f"{label}.chr")
        assert cdata["region"]["sha256"] == by_label[label]["sha256"]


# ── non-quadratic pack: single-pass, round-trip EXACT ───────────────────────

def test_pack_single_pass_roundtrip_exact(tmp_path):
    """genome_pack compacts a directory of .chr bundles in one pass; every
    chromosome round-trips leaf-for-leaf and the packed manifest is v4."""
    one = _one()
    kernels = {f"c{k}": _leaves(k + 3, base=k) for k in range(6)}
    G.genome_save(G.genome(kernels, one), tmp_path / "g", the_one=one)
    G.genome_explode(tmp_path / "g", tmp_path / "loose", the_one=one)
    man = G.genome_pack(tmp_path / "loose", tmp_path / "packed", the_one=one)
    assert man["format_version"] == 6
    assert len(man["regions"]) == len(kernels)
    for label, leaves in kernels.items():
        win = G.genome_window(tmp_path / "packed", label, the_one=one)
        assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(leaves)


def test_many_appends_all_read_back(tmp_path):
    """A helix grown by MANY O(1) appends loads back whole, every chromosome
    leaf-for-leaf, and the body integrity bound passes (the chain covers all)."""
    one = _one()
    want = {}
    lv0 = _leaves(4)
    G.genome_save(G.chromosome(lv0, one, label="c000"), tmp_path / "g", the_one=one)
    want["c000"] = _as_lists(lv0)
    for k in range(1, 30):
        lv = _leaves((k % 9) + 2, base=k)
        G.genome_append(tmp_path / "g", f"c{k:03d}", lv, one)
        want[f"c{k:03d}"] = _as_lists(lv)
    strand, lo, labels = G.genome_load(tmp_path / "g")      # verifies the chain
    part = G.partition(strand, lo, labels)                  # decodes leaves inline
    for label, leaves in want.items():
        assert _as_lists(part[label]) == leaves
