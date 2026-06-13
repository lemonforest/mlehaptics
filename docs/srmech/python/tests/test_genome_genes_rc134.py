"""rc134 (F730 / UPSTREAM S43) — genome file-management increment #1:
``tlv.tlv_unpack`` (the Class-B inverse reader) + the multi-gene
``genome.chromosome(genes=...)`` / ``genome.genes()`` surface.

Composed from existing AMSC (compose, don't reinvent): a gene is a Class-B
``tlv_pack`` frame carried as a byte ``HV`` inside ONE telomere-capped
chromosome; ``genes()`` walks the strand and reads each label back with
``tlv_unpack``. This test runs numpy-free (the whole genome surface is).
"""
from __future__ import annotations

import pytest

from srmech.amsc.tlv import TLV_PREFIX_BYTES, tlv_pack, tlv_unpack
from srmech.amsc.genome import (
    GENE_FRAME_TAG,
    chromosome,
    genes,
    recall,
    telomere,
)
from srmech.amsc.hdc import klein4_random


# ── tlv_unpack: the inverse reader ────────────────────────────────────────
def test_tlv_unpack_round_trips_tlv_pack():
    for tag, value in [(0, b""), (0x47, b"rules"), (255, b"\x00\xff\x10" * 9)]:
        out_tag, out_value, nxt = tlv_unpack(tlv_pack(tag, value))
        assert (out_tag, out_value) == (tag, value)
        assert nxt == TLV_PREFIX_BYTES + len(value)


def test_tlv_unpack_walks_a_concatenation_of_frames():
    buf = tlv_pack(1, b"a") + tlv_pack(2, b"bb") + tlv_pack(3, b"ccc")
    off, seen = 0, []
    while off < len(buf):
        tag, value, off = tlv_unpack(buf, off)
        seen.append((tag, value))
    assert seen == [(1, b"a"), (2, b"bb"), (3, b"ccc")]
    assert off == len(buf)


def test_tlv_unpack_rejects_truncated_prefix_and_value():
    with pytest.raises(ValueError):
        tlv_unpack(b"\x47\x00\x00")                 # prefix < 5 bytes
    with pytest.raises(ValueError):
        tlv_unpack(b"\x47\x00\x00\x00\x05ab")       # claims 5, has 2
    with pytest.raises(ValueError):
        tlv_unpack(tlv_pack(1, b"abc"), offset=99)  # offset past end


def test_tlv_unpack_type_guards():
    with pytest.raises(TypeError):
        tlv_unpack("not bytes")                      # type: ignore[arg-type]
    with pytest.raises(TypeError):
        tlv_unpack(tlv_pack(1, b"x"), offset=True)   # bool is not a plain int


# ── multi-gene chromosome(genes=) / genes() ───────────────────────────────
def _one(seed=1, dim=16):
    return klein4_random(dim, seed=seed)


def test_chromosome_genes_round_trips_labels_and_leaves():
    one = _one()
    la = [klein4_random(16, seed=10), klein4_random(16, seed=11)]
    lb = [klein4_random(16, seed=20)]
    strand = chromosome(genes=[("rules", la), ("board", lb)], the_one=one, label="chess")
    out = genes(strand, one)
    assert [lbl for lbl, _ in out] == ["rules", "board"]
    assert out[0][1][0] == la[0] and out[0][1][1] == la[1]
    assert out[1][1][0] == lb[0]


def test_gene_headers_are_distinguishable_from_klein4_turns():
    one = _one()
    strand = chromosome(genes=[("g", [klein4_random(16, seed=3)])], the_one=one)
    # The cap + the data turn are Klein-4 (every byte <= 3); the gene header is a
    # tlv frame whose first byte is GENE_FRAME_TAG (> 3) — the unambiguous marker.
    headers = [hv for hv in strand if len(hv) and int(hv[0]) == GENE_FRAME_TAG]
    assert len(headers) == 1
    for hv in strand:
        if int(hv[0]) != GENE_FRAME_TAG:
            assert max(hv.tolist()) <= 3, "a Klein-4 turn/cap must stay in {0,1,2,3}"


def test_empty_gene_and_single_gene():
    one = _one()
    strand = chromosome(genes=[("only", [])], the_one=one)
    assert genes(strand, one) == [("only", [])]


def test_chromosome_single_kernel_path_is_unchanged():
    one = _one()
    leaves = [klein4_random(16, seed=10), klein4_random(16, seed=11)]
    strand = chromosome(leaves, one, label="solo")
    assert recall(strand, one, telomere("solo", len(list(one)))) == leaves


def test_chromosome_requires_exactly_one_of_leaves_or_genes():
    one = _one()
    with pytest.raises(ValueError):
        chromosome(the_one=one)                                  # neither
    with pytest.raises(ValueError):
        chromosome([_one()], one, genes=[("a", [_one()])])       # both
    with pytest.raises(ValueError):
        chromosome([_one()])                                     # the_one missing
