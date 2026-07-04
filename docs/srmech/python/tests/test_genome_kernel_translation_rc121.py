"""rc121 (UPSTREAM §60, issue #1245 REOPENED) — the SIZE-AGNOSTIC KERNEL
TRANSLATION LAYER: store / recall a Klein-4 kernel of ARBITRARY dimension D
through the genome, with D SELF-RECORDED in the strand, reconstruction EXACT for
any D, no dimension baked in.

siona uses 8192-dim Klein-4 kernels; the task #722 dive found the genome
quad-strand + HDC ops were ALREADY dimension-agnostic on storage/read (round-trips
exact to 1M+ bits; LEAF_CAP=256 is planning-only, never assumed on the read path).
Two gaps remained, closed here:

  * W1 — the manifest recorded leaf_dim x leaf_count but NOT the true kernel length
    D, so a non-multiple-of-leaf_dim kernel zero-padded and recall returned
    leaf_count x leaf_dim symbols (the caller had to externally remember D to trim).
    kernel_pack now writes a §60 KERNEL HEADER block (marker 0x4B) SELF-RECORDING
    the true D + element_type + leaf_dim, and kernel_unpack TRIMS to D — no caller
    length needed.
  * W2 — no shipped chunk/reconstruct op. kernel_pack / kernel_unpack are the
    single-call surface.

Proven here (the ask's own DoD):
  1. kernel_unpack(kernel_pack(x)) == x EXACT for x of dim 256 / 1000 / 8192 /
     65536 / one MB-scale, INCLUDING the non-multiple-of-leaf_dim case (W1 — the
     true D comes from the header, with NO caller-supplied length);
  2. the symbol-range guard ({0,1,2,3} validated UP FRONT);
  3. the §60 header layout (marker + true D + leaf_dim + element_type);
  4. Python==C byte-identical on the kernel round-trip (native-vs-forced-pure);
  5. back-compat — a body with NO 0x4B header reads as klein4 / full-dim
     (D = leaf_count x leaf_dim), so every pre-rc121 genome reads unchanged.

numpy-free per the genome module's discipline.
"""
from __future__ import annotations

import os
import random

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hv import HV

# The DoD dimensions — a multiple (256/8192/65536), the classic non-multiple
# (1000), and one MB-scale kernel (1,000,000 Klein-4 symbols, non-multiple).
_DODS = [256, 1000, 8192, 65536, 1_000_000]


def _kernel(D):
    """A deterministic flat Klein-4 kernel of dimension D (symbols {0,1,2,3})."""
    r = random.Random(D)
    return [r.randrange(4) for _ in range(D)]


# ── (1) exact round-trip at every DoD dimension, in-memory AND on disk ───────

@pytest.mark.parametrize("D", _DODS)
def test_roundtrip_exact_in_memory(D):
    """kernel_unpack(kernel_pack(x)) == x EXACT for any D — the true D is read
    from the §60 header, so the non-multiple case (1000, 1_000_000) trims with NO
    caller-supplied length (W1 closed)."""
    x = _kernel(D)
    strand = G.kernel_pack(x)
    back = G.kernel_unpack(strand)
    assert back == x
    assert len(back) == D                       # true D, not the padded storage


@pytest.mark.parametrize("D", _DODS)
def test_roundtrip_exact_on_disk(tmp_path, D):
    """Save the packed strand and unpack from the DIRECTORY (the_one resolved from
    the manifest cache) — exact for any D."""
    x = _kernel(D)
    strand = G.kernel_pack(x)
    one = G._default_the_one(256)
    p = tmp_path / f"k{D}"
    man = G.genome_save(strand, p, the_one=one)
    assert man["format_version"] == 10           # the v9 writer (rc130 §130 stamps 9)
    back = G.kernel_unpack(p)                    # no the_one — from the manifest
    assert back == x
    assert len(back) == D


def test_non_multiple_needs_no_external_trim(tmp_path):
    """W1, spelled out: a D=1000 kernel stores as 4 x 256 = 1024 symbols (24 pad),
    but kernel_unpack returns exactly 1000 — the true length lives in the header,
    the caller supplies nothing."""
    x = _kernel(1000)
    strand = G.kernel_pack(x)                    # leaf_dim 256 default
    # §89/v6: recall returns [klein4_header, *content]; the CONTENT leaves are the
    # padded storage (4 leaves x 256 = 1024, 24 pad symbols) — the header is leaves[0].
    leaves = G.recall(strand, G._default_the_one(256))
    content = leaves[1:]
    assert sum(len(l) for l in content) == 1024  # 4 leaves x 256, 24 pad symbols
    # ... but unpack trims to the TRUE D with no external knowledge of 1000
    assert G.kernel_unpack(strand) == x
    assert len(G.kernel_unpack(strand)) == 1000


# ── (2) the symbol-range guard (the sharp-edge from the dive) ────────────────

def test_symbol_guard_rejects_non_klein4_up_front():
    """HV.from_sequence(sectors=4) silently accepts symbols > 3 in memory, but only
    Klein-4 turns bit-pack — so kernel_pack validates {0,1,2,3} UP FRONT with a
    clean error naming the offending symbol + position."""
    with pytest.raises(ValueError, match=r"symbol 4 at position 4 is not a Klein-4"):
        G.kernel_pack([0, 1, 2, 3, 4, 2])
    # bytes carrying a >3 value are rejected the same way
    with pytest.raises(ValueError, match=r"not a Klein-4 sector"):
        G.kernel_pack(bytes([0, 1, 200]))
    # a clean Klein-4 kernel (as bytes / HV / list) all pack + round-trip
    for src in ([0, 1, 2, 3, 2, 1], bytes([0, 1, 2, 3, 2, 1]),
                HV.from_sequence([0, 1, 2, 3, 2, 1], sectors=4)):
        assert G.kernel_unpack(G.kernel_pack(src)) == [0, 1, 2, 3, 2, 1]


# ── (3) the §60 header layout ────────────────────────────────────────────────

def test_kernel_header_layout():
    """The §60 header block: marker 0x4B, then the true D (uint64 BE), leaf_dim
    (uint32 BE) and element_type (uint8 enum) — fixed-width, big-endian, NUL-padded
    to leaf_dim. An 8192 / 65536 / MB-scale D all fit the 8-byte length field."""
    for D, leaf_dim in [(1000, 256), (8192, 256), (65536, 128), (13_720_000, 256)]:
        strand = G.kernel_pack(_kernel(min(D, 4)) if D > 4 else _kernel(D),
                               leaf_dim=leaf_dim)
        # rebuild a header for the pure-layout check (avoid packing a 13.7M kernel)
        hv = G._pack_kernel_header(D, leaf_dim, G.ELEMENT_TYPE_KLEIN4, leaf_dim)
        raw = hv.tobytes()
        assert len(raw) == leaf_dim                       # fixed-width block
        assert raw[0] == G.KERNEL_HEADER_MARKER == 0x4B
        assert int.from_bytes(raw[1:9], "big") == D       # uint64 BE true length
        assert int.from_bytes(raw[9:13], "big") == leaf_dim
        assert raw[13] == G.ELEMENT_TYPE_KLEIN4 == 0
        assert set(raw[14:]) <= {0}                       # NUL padding
        assert G._unpack_kernel_header(hv) == (D, leaf_dim, G.ELEMENT_TYPE_KLEIN4)
        del strand


def test_header_is_klein4_leaf_after_kernel_telomere(tmp_path):
    """§89/v6: a kernel chromosome opens with a KERNEL telomere (0x6B); the FIRST
    coupled turn after it is the uniformly-Klein-4 header LEAF (a DATA turn — it
    bit-packs + counts like content, NOT a verbatim byte-TLV marker block)."""
    x = _kernel(1000)
    strand = G.kernel_pack(x, label="siona")
    one = G._default_the_one(256)
    # strand shape: [kernel_telomere, coupled_klein4_header, 4 coupled content turns]
    assert G._cap_kind(strand[0]) == G.KERNEL_TELOMERE_MARKER
    assert G._cap_kind(strand[1]) is None                 # the header is a coupled turn
    assert len(strand) == 2 + 4                           # 4 content leaves for D=1000
    # the uncoupled header leaf is 100 % Klein-4 and self-records D / leaf_dim / etype
    hdr = G.recall(strand, one)[0]
    assert set(int(s) for s in hdr) <= {0, 1, 2, 3}       # uniformly Klein-4
    assert G._unpack_kernel_header_klein4(hdr) == (1000, 256, G.ELEMENT_TYPE_KLEIN4)
    p = tmp_path / "g"
    man = G.genome_save(strand, p, the_one=one)
    # §89: leaf_count counts DATA turns — the v6 header IS a coupled turn (counted)
    assert man["chromosomes"][0]["leaf_count"] == 1 + 4   # header + 4 content
    assert man["n_turns"] == 6                            # cap + header + 4 turns
    # the kernel-telomere cap is stored verbatim (leaf_dim bytes, first byte 0x6B);
    # the header turn right after it is bit-packed (marker 0x51 — uniformly Klein-4)
    body = (p / "turns.bin").read_bytes()
    assert body[0] == G.KERNEL_TELOMERE_MARKER            # the 0x6B kernel telomere
    assert body[256] == G.PACKED_TURN_MARKER             # the bit-packed header turn


# ── (4) Python==C byte-identical on the kernel round-trip ─────────────────────

@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("D", _DODS)
def test_python_equals_c_byte_identical(tmp_path, D):
    """The native save/load writes turns.bin + manifest.json BYTE-IDENTICALLY to
    the pure-Python path, and both round-trip the kernel exactly (native-vs-
    forced-pure differential)."""
    x = _kernel(D)
    strand = G.kernel_pack(x)
    one = G._default_the_one(256)

    dn = tmp_path / "native"
    G.genome_save(strand, dn, the_one=one)
    n_body = (dn / "turns.bin").read_bytes()
    n_man = (dn / "manifest.json").read_bytes()
    back_n = G.kernel_unpack(dn)

    real = _native.has_native_genome
    _native.has_native_genome = lambda: False        # force the pure-Python path
    try:
        dp = tmp_path / "pure"
        G.genome_save(strand, dp, the_one=one)
        p_body = (dp / "turns.bin").read_bytes()
        p_man = (dp / "manifest.json").read_bytes()
        back_p = G.kernel_unpack(dp, the_one=one)
    finally:
        _native.has_native_genome = real

    assert n_body == p_body                          # turns.bin byte-identical
    assert n_man == p_man                            # manifest.json byte-identical
    assert back_n == x == back_p                     # both round-trip exactly


# ── (5) back-compat: a NO-header body reads as klein4 / full-dim ──────────────

def test_no_header_body_reads_as_klein4_full_dim(tmp_path):
    """A header-less body (any pre-rc121 genome — here a plain chromosome with no
    §60 header) reads as element_type=klein4 with D = leaf_count x leaf_dim —
    today's exact behaviour, no trim, no migration (the rc114 dual-read pattern)."""
    one = G._default_the_one(256)
    x = _kernel(1000)
    # a PLAIN chromosome (chromosome(), NOT kernel_pack) has no §60 header
    leaves = [HV.from_sequence((x[i:i + 256] + [0] * 256)[:256], sectors=4)
              for i in range(0, 1000, 256)]
    plain = G.chromosome(leaves, one, label="legacy")
    assert all(G._cap_kind(hv) != G.KERNEL_HEADER_MARKER for hv in plain)

    # in-memory: full-dim (leaf_count x leaf_dim), the padded storage
    back_mem = G.kernel_unpack(plain, the_one=one)
    assert len(back_mem) == 4 * 256 == 1024
    assert back_mem[:1000] == x                       # the true kernel is the prefix

    # on disk (a v5 body with NO header) reads the same full-dim way
    p = tmp_path / "legacy"
    G.genome_save(plain, p, the_one=one)
    back_disk = G.kernel_unpack(p)
    assert back_disk == back_mem == list(back_mem)


def test_empty_body_default_the_one_is_reconstructed():
    """When no the_one is supplied for an in-memory strand, kernel_unpack
    reconstructs the deterministic all-ones invariant from the header's leaf_dim —
    so the round-trip needs neither a length nor a the_one."""
    x = _kernel(300)
    strand = G.kernel_pack(x, leaf_dim=100)           # 3 leaves x 100
    assert G.kernel_unpack(strand) == x               # no the_one passed
