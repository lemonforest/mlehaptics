"""rc126 (UPSTREAM §89, issue #1261, F1045/F1046) — the UNIFORMLY-KLEIN-4 KERNEL
HEADER: the on-disk kernel encoding is now 100 % Klein-4, so the O(1)
``genome_append_kernel`` FALLS OUT of ``genome_append``.

rc121's §60 header was a BYTE-TLV block (marker 0x4B, uint64/uint32 big-endian
fields) — the SOLE non-Klein-4 residue in a store that otherwise presents as uniform
Klein-4. It could NOT ride ``genome_append`` (unbinding the byte-TLV via klein4_bind
fails "must be in {0,1,2,3}"). rc126 (format v5 -> v6, option A) base-4-encodes the
header (true D + element_type + leaf_dim) into ONE Klein-4 LEAF, distinguished by a
SELF-DESCRIBING KERNEL TELOMERE (marker 0x6B) + reserved position (the first coupled
turn after it). A kernel chromosome becomes
``[kernel_telomere, coupled_klein4_header, content-turns…]`` — every data leaf 100 %
Klein-4, so the whole chromosome rides the plain coupled-turn append path and
``genome_append_kernel`` is O(1).

The distinguisher is option (a): a framing marker (0x6B) + fixed position, NOT in-band
magic — so it is COLLISION-FREE (no content leaf can ever be mistaken for the header).

Proven here (the ask's DoD):
  1. the v6 Klein-4-header round-trip EXACT (any D, incl. non-leaf_dim-aligned);
  2. O(1) genome_append_kernel (flat-time + tail-extend + preserves the header);
  3. the bare in-memory strand self-describes (recover D + element_type by scan, no
     manifest);
  4. v5 byte-TLV dual-read back-compat (a v5 header reads identically);
  5. no mixed-encoding smell — the store is uniformly Klein-4 (the header leaf is a
     Klein-4 leaf, not a byte-TLV);
  6. Python==C byte-identical on a v6 kernel round-trip AND a genome_append_kernel.

numpy-free per the genome module's discipline; no abs().
"""
from __future__ import annotations

import random
import time

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hv import HV

# aligned (256/8192), the classic non-multiple (1000), a tiny one (1), and an
# odd non-aligned mid-size (65537) — the true D self-records, so trim is exact.
_DODS = [1, 256, 1000, 8192, 65537]


def _kernel(D):
    r = random.Random(D * 7 + 1)
    return [r.randrange(4) for _ in range(D)]


# ── (1) the v6 Klein-4-header round-trip — any D, aligned or not ──────────────

@pytest.mark.parametrize("D", _DODS)
def test_v6_roundtrip_in_memory(D):
    x = _kernel(D)
    strand = G.kernel_pack(x)
    # v6 shape: [kernel_telomere(0x6B), coupled_klein4_header, *content]
    assert G._cap_kind(strand[0]) == G.KERNEL_TELOMERE_MARKER
    assert G._cap_kind(strand[1]) is None            # the header is a coupled turn
    back = G.kernel_unpack(strand)
    assert back == x
    assert len(back) == D                            # true D, not padded storage


@pytest.mark.parametrize("D", _DODS)
def test_v6_roundtrip_on_disk(tmp_path, D):
    x = _kernel(D)
    strand = G.kernel_pack(x)
    one = G._default_the_one(256)
    p = tmp_path / f"k{D}"
    man = G.genome_save(strand, p, the_one=one)
    assert man["format_version"] == 7                # the v7 writer (rc127 §127 stamps 7)
    assert G.kernel_unpack(p) == x                   # the_one from the manifest cache


def test_v6_leaf_dim_non_default_and_non_aligned(tmp_path):
    """A non-default leaf_dim (100) and a D that is NOT a multiple of it (250) still
    round-trip EXACT — the header self-records D=250 and leaf_dim=100."""
    x = _kernel(250)
    strand = G.kernel_pack(x, leaf_dim=100)          # 250 -> 3 content leaves (50 pad)
    hdr = G.recall(strand, G._default_the_one(100))[0]
    assert G._unpack_kernel_header_klein4(hdr) == (250, 100, G.ELEMENT_TYPE_KLEIN4)
    assert G.kernel_unpack(strand) == x
    p = tmp_path / "k"
    G.genome_save(strand, p, the_one=G._default_the_one(100))
    assert G.kernel_unpack(p) == x


def test_leaf_dim_below_header_size_rejected():
    """The §89 header needs leaf_dim >= 52 (the base-4 field count); a smaller leaf is
    rejected UP FRONT (unlike the v5 14-byte prefix)."""
    with pytest.raises(ValueError, match=r"leaf_dim must be an int >= 52"):
        G.kernel_pack([0, 1, 2, 3], leaf_dim=32)


# ── (2) the O(1) genome_append_kernel — the deliverable ──────────────────────

def _seed(tmp_path, one):
    """A genome seeded with one kernel chromosome, ready for O(1) kernel appends."""
    p = tmp_path / "g"
    G.genome_save(G.kernel_pack(_kernel(300), label="seed"), p, the_one=one)
    return p


def test_append_kernel_roundtrips_and_preserves_header(tmp_path):
    """genome_append_kernel appends a kernel WITH its §89 header; the appended kernel
    (and its self-describing D) recover EXACTLY."""
    one = G._default_the_one(256)
    p = _seed(tmp_path, one)
    x = _kernel(777)                                 # non-aligned D
    man = G.genome_append_kernel(p, "taught", x, the_one=one)
    assert man["chromosomes"][-1]["label"] == "taught"
    # recover the appended kernel: load, split to its chromosome, kernel_unpack it
    strand, one2, _labels = G.genome_load(p)
    by_label = dict(G._split_into_chromosomes(strand))
    assert G.kernel_unpack(by_label["taught"], one2) == x   # exact, D self-recorded


def test_append_kernel_is_tail_extend_prior_untouched(tmp_path):
    """The O(1) structural guarantee: the prior body is an EXACT prefix (no
    whole-body rewrite), and only ONE chromosome + region entry is appended, the
    body_sha256 chain extended in O(1) from its prior head."""
    one = G._default_the_one(256)
    p = _seed(tmp_path, one)
    man0 = G.genome_catalog(p)
    body0 = (p / "turns.bin").read_bytes()

    man1 = G.genome_append_kernel(p, "k1", _kernel(500), the_one=one)
    body1 = (p / "turns.bin").read_bytes()

    assert body1[:len(body0)] == body0                       # append-only prefix
    assert man1["chromosomes"][:1] == man0["chromosomes"]    # prior entry identical
    assert man1["regions"][:1] == man0["regions"]            # prior region identical
    region = body1[len(body0):]
    assert man1["chromosomes"][-1]["byte_offset"] == len(body0)
    # the region opens with the 0x6B kernel telomere (a kernel chromosome)
    assert region[0] == G.KERNEL_TELOMERE_MARKER


def test_append_kernel_flat_time(tmp_path):
    """Flat-time: appending a kernel to a genome with MANY chromosomes is not
    dramatically slower than to a small one (O(1) amortised, not O(N))."""
    one = G._default_the_one(256)
    p = _seed(tmp_path, one)
    kern = _kernel(400)

    def _timed_append(label):
        t0 = time.perf_counter()
        G.genome_append_kernel(p, label, kern, the_one=one)
        return time.perf_counter() - t0

    early = min(_timed_append(f"e{i}") for i in range(3))   # genome ~1..5 chroms
    for i in range(200):
        G.genome_append_kernel(p, f"bulk{i}", kern, the_one=one)
    late = min(_timed_append(f"l{i}") for i in range(3))    # genome ~208 chroms
    # O(N) would blow this ratio out; O(1) keeps it bounded (generous CI tolerance).
    assert late < early * 12 + 0.05, (early, late)


# ── (3) bare in-memory strand self-describes — no manifest, no the_one ────────

def test_bare_strand_self_describes(tmp_path):
    """§44 portability win: a bare in-memory strand recovers the true D +
    element_type by SCANNING its Klein-4 header leaf — no manifest, no the_one (the
    default all-ones is reconstructed from the leaf width)."""
    x = _kernel(1234)
    strand = G.kernel_pack(x, leaf_dim=128)
    # no the_one, no manifest, no external length
    assert G.kernel_unpack(strand) == x
    # the header self-records D + element_type + leaf_dim (scan the strand)
    hdr = G.recall(strand, G._default_the_one(128))[0]
    assert G._unpack_kernel_header_klein4(hdr) == (1234, 128, G.ELEMENT_TYPE_KLEIN4)


# ── (4) v5 byte-TLV dual-read back-compat ────────────────────────────────────

def _v5_strand(x, leaf_dim, one):
    """A pre-rc126 (v5) kernel strand: [telomere, 0x4B byte-TLV header, *turns] —
    exactly what the old kernel_pack produced, built here for the dual-read fixture."""
    leaves = [HV.from_sequence((x[i:i + leaf_dim] + [0] * leaf_dim)[:leaf_dim],
                               sectors=4)
              for i in range(0, len(x), leaf_dim)] or [HV.from_sequence(
                  [0] * leaf_dim, sectors=4)]
    strand = G.chromosome(leaves, one, label="legacy_v5")
    header = G._pack_kernel_header(len(x), leaf_dim, G.ELEMENT_TYPE_KLEIN4, leaf_dim)
    return [strand[0], header] + strand[1:]


def test_v5_byte_tlv_header_reads_identically(tmp_path):
    """A v5 0x4B byte-TLV header still reads EXACTLY (dual-read; the block walker
    gains one branch, NEVER breaks an existing genome) — in memory AND on disk."""
    one = G._default_the_one(256)
    x = _kernel(700)
    v5 = _v5_strand(x, 256, one)
    assert G._cap_kind(v5[1]) == G.KERNEL_HEADER_MARKER      # the v5 byte-TLV block
    assert G.kernel_unpack(v5, the_one=one) == x            # in-memory dual-read
    p = tmp_path / "v5"
    G.genome_save(v5, p, the_one=one)
    assert G.kernel_unpack(p) == x                          # on-disk dual-read


def test_no_header_back_compat(tmp_path):
    """A header-less body (pre-rc121) reads as klein4 / full-dim (D = leaf_count x
    leaf_dim) — no trim, no migration."""
    one = G._default_the_one(256)
    x = _kernel(1000)
    leaves = [HV.from_sequence((x[i:i + 256] + [0] * 256)[:256], sectors=4)
              for i in range(0, 1000, 256)]
    plain = G.chromosome(leaves, one, label="legacy")
    back = G.kernel_unpack(plain, the_one=one)
    assert len(back) == 4 * 256 and back[:1000] == x


# ── (5) no mixed-encoding smell — the store is uniformly Klein-4 ──────────────

def test_no_mixed_encoding_smell(tmp_path):
    """The v6 store is UNIFORMLY Klein-4: the only cap is the 0x6B kernel telomere;
    every DATA turn (header included) is a bit-packed Klein-4 turn (marker 0x51) whose
    unpacked content is entirely {0,1,2,3}. NO 0x4B byte-TLV residue anywhere."""
    one = G._default_the_one(256)
    x = _kernel(1500)
    p = tmp_path / "g"
    G.genome_save(G.kernel_pack(x), p, the_one=one)
    body = (p / "turns.bin").read_bytes()
    # walk the body: the ONLY block kinds are the 0x6B kernel telomere cap and 0x51
    # bit-packed Klein-4 turns — NO 0x4B byte-TLV header BLOCK anywhere (the 0x4B
    # byte may appear INSIDE a packed payload, but never as a block-kind marker).
    caps, turns = 0, 0
    for raw, decoded in G._walk_region_blocks(body, 256, context="test"):
        assert raw[0] != G.KERNEL_HEADER_MARKER             # no 0x4B byte-TLV block
        if decoded[0] == G.KERNEL_TELOMERE_MARKER:
            caps += 1
        else:
            assert raw[0] == G.PACKED_TURN_MARKER            # bit-packed data turn
            assert set(int(s) for s in decoded) <= {0, 1, 2, 3}   # Klein-4 content
            turns += 1
    assert caps == 1 and turns == 1 + 6                     # 1 header + 6 content leaves


# ── (6) Python==C byte-identical ──────────────────────────────────────────────

@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("D", [256, 1000, 8192])
def test_python_equals_c_v6_kernel(tmp_path, D):
    """The native save/load writes turns.bin + manifest.json BYTE-IDENTICALLY to the
    pure-Python path on a v6 kernel genome, and both round-trip exactly."""
    x = _kernel(D)
    strand = G.kernel_pack(x)
    one = G._default_the_one(256)

    dn = tmp_path / "native"
    G.genome_save(strand, dn, the_one=one)
    n_body = (dn / "turns.bin").read_bytes()
    n_man = (dn / "manifest.json").read_bytes()
    back_n = G.kernel_unpack(dn)

    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        dp = tmp_path / "pure"
        G.genome_save(strand, dp, the_one=one)
        p_body = (dp / "turns.bin").read_bytes()
        p_man = (dp / "manifest.json").read_bytes()
        back_p = G.kernel_unpack(dp, the_one=one)
    finally:
        _native.has_native_genome = real

    assert n_body == p_body
    assert n_man == p_man
    assert back_n == x == back_p


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
def test_python_equals_c_append_kernel(tmp_path):
    """genome_append_kernel is byte-identical native-vs-pure (the O(1) append writes
    the same turns.bin tail + manifest either way) and recovers the kernel exactly."""
    one = G._default_the_one(256)
    x = _kernel(999)

    def _build(root):
        G.genome_save(G.kernel_pack(_kernel(300), label="seed"), root, the_one=one)
        G.genome_append_kernel(root, "taught", x, the_one=one)
        return (root / "turns.bin").read_bytes(), (root / "manifest.json").read_bytes()

    dn = tmp_path / "native"
    n_body, n_man = _build(dn)

    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        dp = tmp_path / "pure"
        p_body, p_man = _build(dp)
    finally:
        _native.has_native_genome = real

    assert n_body == p_body
    assert n_man == p_man
    # the appended kernel recovers exactly from the native store
    strand, one2, _ = G.genome_load(dn)
    by_label = dict(G._split_into_chromosomes(strand))
    assert G.kernel_unpack(by_label["taught"], one2) == x


# ── extra guards: duplicate label + symbol range ──────────────────────────────

def test_append_kernel_rejects_duplicate_and_non_klein4(tmp_path):
    one = G._default_the_one(256)
    p = _seed(tmp_path, one)
    G.genome_append_kernel(p, "a", _kernel(100), the_one=one)
    with pytest.raises(ValueError, match="already exists"):
        G.genome_append_kernel(p, "a", _kernel(100), the_one=one)
    with pytest.raises(ValueError, match=r"not a Klein-4 sector"):
        G.genome_append_kernel(p, "b", [0, 1, 2, 9], the_one=one)
