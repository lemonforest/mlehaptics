"""rc114 (issue #1245 / UPSTREAM §55, F1036/F833) — genome format v3: BIT-PACKED
data turns. "The 2-bit lane IS the format."

The §41–§45 genome surface stored every 2-bit Klein-4 symbol as a FULL BYTE — a
measured 4.03x bloat (a 1,024-leaf x 256-symbol chromosome, 64 KB of packed
payload, wrote 264,230 bytes at rc107). Format v3 packs **4 Klein-4 symbols per
byte**: a data turn is written on disk as ``[PACKED_TURN_MARKER (0x51 'Q')] +
ceil(leaf_dim/4)`` payload bytes; cap blocks keep their §44 ``leaf_dim``-byte
inline-label layout. A block's FIRST byte keys both its kind and its width, so
the strand stays SELF-DESCRIBING — and back-compat is STRUCTURAL, not a
converter: legacy v2 byte-per-symbol turns (first byte 0..3) remain readable in
the SAME walk, so old genomes AND mixed (old + appended) bodies read correctly.

Proven here:
  1. the DoD byte count — the issue's 1,024x256 chromosome writes a 66,816-byte
     body (~66 KB total; exact figures asserted) vs 264,230 B at rc107;
  2. round-trip EXACT (window + recall, leaf-for-leaf) in the packed format,
     including partial-final-byte widths (leaf_dim % 4 != 0);
  3. back-compat — a COMMITTED on-disk genome written by the PRE-rc114 code
     path (tests/data/genome_v2_fixture; format_version 2, byte-per-symbol,
     parser_version "srmech 0.9.0rc113" in its manifest) reads identically;
  4. a MIXED-format genome (v2 chromosomes + a v3 append) reads correctly,
     the append stays append-only, and the §44 rebuild-by-scan reproduces the
     mixed manifest exactly (the manifest stays an optional .fai cache);
  5. the packed block codec is exact and canonical both ways; a legacy .chr
     imports verbatim (never re-encoded).

numpy-free per the genome module's discipline.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_random

# ── the committed v2 fixture (written VERBATIM by the rc113 code path) ───────
#
# Generated from the pristine rc113 genome.py (GENOME_FORMAT_VERSION == 2) with
# these deterministic seeds — regenerable, never regenerated (its manifest's
# parser_version "srmech 0.9.0rc113" is the provenance):
#
#   one   = klein4_random(16, seed=7)
#   alpha = [klein4_random(16, seed=s) for s in (1, 2)]
#   g1    = [klein4_random(16, seed=s) for s in (3, 4)]
#   g2    = [klein4_random(16, seed=5)]
#   strand = genome(chromosomes=[("alpha", [("a", alpha)]),
#                                ("multi", [("g1", g1), ("g2", g2)])], the_one=one)
#   strand += chromosome(alpha, one, label="plain")
_FIXTURE = Path(__file__).parent / "data" / "genome_v2_fixture"
_V2_DIM = 16


def _v2_one():
    return klein4_random(_V2_DIM, seed=7)


def _v2_leaves():
    alpha = [klein4_random(_V2_DIM, seed=s) for s in (1, 2)]
    g1 = [klein4_random(_V2_DIM, seed=s) for s in (3, 4)]
    g2 = [klein4_random(_V2_DIM, seed=5)]
    return alpha, g1, g2


def _v2_strand(one, alpha, g1, g2):
    strand = G.genome(chromosomes=[
        ("alpha", [("a", alpha)]),
        ("multi", [("g1", g1), ("g2", g2)]),
    ], the_one=one)
    return strand + G.chromosome(alpha, one, label="plain")


def _copy_fixture(tmp_path) -> Path:
    d = tmp_path / "v2"
    d.mkdir()
    shutil.copyfile(_FIXTURE / "turns.bin", d / "turns.bin")
    shutil.copyfile(_FIXTURE / "manifest.json", d / "manifest.json")
    return d


def _as_lists(xs):
    return [list(x) for x in xs]


# ── (1) the DoD byte count — the issue's 1,024 x 256 chromosome ─────────────

def test_dod_1024x256_chromosome_writes_66kb(tmp_path):
    """Issue #1245 DoD: the 1,024-leaf x 256-symbol chromosome (64 KB of 2-bit
    payload) writes a 66,816-byte body — 256 (cap) + 1024 x 65 (marker +
    256/4 payload) — vs the measured 264,230 bytes at rc107 (4.03x bloat).
    Leaf CONTENT is irrelevant to the size, so a small pool is replicated."""
    dim = 256
    one = klein4_random(dim, seed=7)
    pool = [klein4_random(dim, seed=s) for s in range(8)]
    leaves = [pool[i % 8] for i in range(1024)]
    p = tmp_path / "g"
    man = G.genome_save(G.chromosome(leaves, one, label="kernel"), p, the_one=one)

    body_size = (p / "turns.bin").stat().st_size
    manifest_size = (p / "manifest.json").stat().st_size
    total = body_size + manifest_size

    assert body_size == 256 + 1024 * (1 + 256 // 4) == 66816
    assert total < 70_000                    # "~66 KB" — vs 264,230 B at rc107
    assert 264_230 / total > 3.8             # the 4.03x bloat removed
    assert man["format_version"] == 4        # rc115 (#1245(b)): v4 carries regions
    assert man["n_turns"] == 1025            # blocks: 1 cap + 1024 turns
    # rc115 (#1245(b)): one region entry per chromosome; body_sha256 is the chain
    assert [r["byte_offset"] for r in man["regions"]] == [0]
    assert man["regions"][0]["byte_len"] == body_size

    # round-trip EXACT: window + recall, leaf-for-leaf
    win = G.genome_window(p, "kernel")
    assert len(win) == 1024
    recalled = [G.quad_turn(t, one) for t in win]    # uncouple through the_one
    assert _as_lists(recalled) == _as_lists(leaves)


# ── (2) packed round-trips, including partial final bytes ────────────────────

@pytest.mark.parametrize("dim", [5, 6, 7, 10, 16, 64])
def test_packed_roundtrip_exact_any_width(tmp_path, dim):
    """Save → load → window round-trips leaf-for-leaf at widths where the final
    packed byte is partial (dim % 4 != 0) and where it is whole."""
    one = klein4_random(dim, seed=3)
    kernels = {
        "a": [klein4_random(dim, seed=s) for s in (1, 2, 3)],
        "b": [klein4_random(dim, seed=4)],
    }
    strand = G.genome(kernels, one)
    p = tmp_path / f"g{dim}"
    G.genome_save(strand, p, the_one=one)

    ls, lo, ll = G.genome_load(p)
    assert _as_lists(ls) == _as_lists(strand)
    part = G.partition(ls, lo, ll)
    for lbl, leaves in kernels.items():
        assert _as_lists(part[lbl]) == _as_lists(leaves)
    win = G.genome_window(p, "a")
    assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(kernels["a"])


def test_pack_codec_exact_and_canonical():
    """The 2-bit codec: pack(unpack) and unpack(pack) are identities; the
    partial final byte zero-pads its unused low lanes (canonical form)."""
    for dim in (1, 2, 3, 4, 5, 8, 13):
        for seed in range(4):
            mem = bytes(list(klein4_random(dim, seed=seed)))
            blk = G._pack_turn_block(mem)
            assert blk[0] == G.PACKED_TURN_MARKER
            assert len(blk) == 1 + (dim + 3) // 4
            assert G._unpack_turn_payload(blk[1:], dim) == mem
    # partial final byte: 5 symbols -> byte 2 carries ONE symbol in its top lane
    blk = G._pack_turn_block(bytes([1, 2, 3, 0, 3]))
    assert blk == bytes([G.PACKED_TURN_MARKER, 0b01101100, 0b11000000])
    # a non-Klein-4 symbol refuses to pack
    with pytest.raises(ValueError):
        G._pack_turn_block(bytes([0, 1, 7, 2]))


def test_multigene_chromosome_packed_roundtrip(tmp_path):
    """Inline GENE caps stay leaf_dim-wide between packed turns; genome_genes
    recovers the per-gene split exactly."""
    dim = 32
    one = klein4_random(dim, seed=9)
    rules = [klein4_random(dim, seed=s) for s in (1, 2)]
    board = [klein4_random(dim, seed=3)]
    strand = G.genome(chromosomes=[("chess", [("rules", rules), ("board", board)])],
                      the_one=one)
    p = tmp_path / "g"
    G.genome_save(strand, p, the_one=one)
    got = G.genome_genes(p, "chess")
    assert [lbl for lbl, _ in got] == ["rules", "board"]
    assert _as_lists(got[0][1]) == _as_lists(rules)
    assert _as_lists(got[1][1]) == _as_lists(board)


# ── (3) back-compat: the committed PRE-rc114 genome reads identically ───────

def test_v2_fixture_is_the_old_writers_output():
    """The committed fixture really is the rc113 writer's artifact: format 2,
    byte-per-symbol body (13 x 16 = 208 bytes), rc113 parser_version."""
    man = json.loads((_FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    assert man["data"]["format_version"] == 2
    assert man["attestation"]["parser_version"] == "srmech 0.9.0rc113"
    assert (_FIXTURE / "turns.bin").stat().st_size == 13 * _V2_DIM == 208


def test_v2_fixture_reads_identically(tmp_path):
    """catalog / load / window / genes on the v2 genome return exactly what the
    pre-rc114 reader returned (leaf-for-leaf against the regenerated strand)."""
    d = _copy_fixture(tmp_path)
    one = _v2_one()
    alpha, g1, g2 = _v2_leaves()
    expected = _v2_strand(one, alpha, g1, g2)

    cat = G.genome_catalog(d)
    assert cat["format_version"] == 2          # reading never rewrites
    assert [c["label"] for c in cat["chromosomes"]] == ["alpha", "multi", "plain"]
    assert cat["n_turns"] == 13

    ls, lo, ll = G.genome_load(d)
    assert _as_lists(ls) == _as_lists(expected)
    assert list(lo) == list(one)
    assert ll == ["alpha", "multi", "plain"]

    win = G.genome_window(d, "plain")
    assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(alpha)

    genes = G.genome_genes(d, "multi")
    assert [lbl for lbl, _ in genes] == ["g1", "g2"]
    assert _as_lists(genes[0][1]) == _as_lists(g1)
    assert _as_lists(genes[1][1]) == _as_lists(g2)

    sub, _o, sl = G.genome_load(d, labels=["multi"])
    assert sl == ["multi"]

    # the on-disk fixture bytes were never touched by any of the reads
    assert (d / "turns.bin").read_bytes() == (_FIXTURE / "turns.bin").read_bytes()
    assert (d / "manifest.json").read_bytes() == \
        (_FIXTURE / "manifest.json").read_bytes()


def test_v2_fixture_manifestless_rebuild_reads(tmp_path):
    """§44 held across the format bump: drop the v2 manifest and the catalog
    rebuilds by scanning the legacy body (given the_one for the width)."""
    d = _copy_fixture(tmp_path)
    (d / "manifest.json").unlink()
    one = _v2_one()
    cat = G.genome_catalog(d, the_one=one)
    # the rebuilt catalog is the CURRENT (v3) derivation of the same body —
    # every structural field identical to the stored v2 manifest's
    assert [c["label"] for c in cat["chromosomes"]] == ["alpha", "multi", "plain"]
    assert cat["n_turns"] == 13
    v2 = json.loads((_FIXTURE / "manifest.json").read_text(encoding="utf-8"))["data"]
    assert cat["chromosomes"] == v2["chromosomes"]
    # rc115 (#1245(b)): the rebuild derives the CURRENT (v4) manifest — the
    # structural chromosome fields are byte-identical to the stored v2 manifest's,
    # but body_sha256 is now the region CHAIN (not the v2 whole-body digest), and a
    # regions partition is derived (one per chromosome, tiling the body).
    assert cat["format_version"] == 4
    assert [(r["byte_offset"], r["byte_len"]) for r in cat["regions"]] == \
        [(c["byte_offset"], c["byte_len"]) for c in v2["chromosomes"]]
    assert cat["body_sha256"] != v2["body_sha256"]        # chain, not whole-body
    win = G.genome_window(d, "plain", the_one=one)
    alpha, _g1, _g2 = _v2_leaves()
    assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(alpha)


# ── (4) mixed-format: a v3 append onto the v2 genome ─────────────────────────

def test_v2_append_yields_mixed_body_reading_correctly(tmp_path):
    """Appending to a v2 genome writes a v3 (packed) region after the legacy
    blocks — append-only, prior manifest entries byte-identical, every
    chromosome (old and new) reads correctly, and the §44 rebuild-by-scan
    reproduces the mixed manifest exactly."""
    d = _copy_fixture(tmp_path)
    one = _v2_one()
    body_before = (d / "turns.bin").read_bytes()
    man_before = G.genome_catalog(d)

    new_leaves = [klein4_random(_V2_DIM, seed=s) for s in (30, 31, 32)]
    man2 = G.genome_append(d, "fresh", new_leaves, one)

    # append-only: the v2 bytes are an exact prefix; the tail is the v3 region
    body_after = (d / "turns.bin").read_bytes()
    assert body_after[:len(body_before)] == body_before
    tail = body_after[len(body_before):]
    assert tail[0] == G.CHROM_CAP_MARKER
    assert tail[_V2_DIM] == G.PACKED_TURN_MARKER          # first packed turn
    assert len(tail) == _V2_DIM + 3 * (1 + (_V2_DIM + 3) // 4)

    # the manifest went v4 (rc115 #1245(b)); prior entries byte-identical; n_turns
    # = blocks. Appending to a v2 genome migrates it to v4 (regions derived).
    assert man2["format_version"] == 4
    assert man2["chromosomes"][:3] == man_before["chromosomes"]
    assert man2["n_turns"] == man_before["n_turns"] + 1 + 3

    # every chromosome — legacy AND packed — reads correctly from the MIXED body
    alpha, g1, g2 = _v2_leaves()
    ls, lo, ll = G.genome_load(d)
    assert ll == ["alpha", "multi", "plain", "fresh"]
    part = G.partition(ls, lo, ll)
    assert _as_lists(part["alpha"]) == _as_lists(alpha)
    assert _as_lists(part["multi"]) == _as_lists(g1 + g2)
    assert _as_lists(part["fresh"]) == _as_lists(new_leaves)
    win = G.genome_window(d, "fresh")
    assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(new_leaves)

    # §44 on the MIXED body: rebuild-by-scan == the written manifest data
    (d / "manifest.json").unlink()
    assert G.genome_catalog(d, the_one=one) == man2

    # in-place edit on the mixed body: excise a LEGACY chromosome; the packed
    # survivor still reads (splice + rescan handle both block kinds)
    G.genome_remove(d, "multi", the_one=one)
    win2 = G.genome_window(d, "fresh", the_one=one)
    assert _as_lists([G.quad_turn(t, one) for t in win2]) == _as_lists(new_leaves)
    win3 = G.genome_window(d, "plain", the_one=one)
    assert _as_lists([G.quad_turn(t, one) for t in win3]) == _as_lists(alpha)


# ── (5) legacy .chr bundles import VERBATIM (never re-encoded) ───────────────

def test_legacy_chr_exports_and_imports_verbatim(tmp_path):
    """Exporting a chromosome from the v2 genome carries its LEGACY region
    bytes; importing it seeds/appends those bytes verbatim — the reader's
    dual-format walk makes re-encoding unnecessary (and wrong)."""
    d = _copy_fixture(tmp_path)
    one = _v2_one()
    alpha, _g1, _g2 = _v2_leaves()
    chr_path = tmp_path / "plain.chr"
    cdata = G.genome_export(d, "plain", chr_path)
    region = bytes.fromhex(cdata["region"]["hex"])
    assert region[0] == G.CHROM_CAP_MARKER
    assert len(region) == 3 * _V2_DIM                      # legacy blocks verbatim

    dest = tmp_path / "seeded"
    G.genome_import(chr_path, dest)
    assert (dest / "turns.bin").read_bytes() == region     # seeded VERBATIM
    win = G.genome_window(dest, "plain")
    assert _as_lists([G.quad_turn(t, one) for t in win]) == _as_lists(alpha)

    # explode/pack across the mixed world round-trips by content
    loose = tmp_path / "loose"
    G.genome_explode(d, loose)
    packed = tmp_path / "packed"
    G.genome_pack(loose, packed)
    got = G.genome_window(packed, "plain")
    assert _as_lists([G.quad_turn(t, one) for t in got]) == _as_lists(alpha)
