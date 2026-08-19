"""v0.9.0rc196 — the genome CAP FOUNDATION gets its C peers (#887).

The SECOND leaf-batch of the make_class → C arc. The genome.toml [class]
descriptor binds 10 leaf ops; rc196 ships the C peers of the two smallest
in-memory leaves (+ the shared cap byte-TLV helpers rc197/rc198 reuse):

  * ``srmech_genome_encode_shape`` — the pure-INTEGER shape planner. ``n`` →
    ``(leaves, depth)`` where ``leaves = ceil(n / 256)`` and ``depth =
    ceil(log4(leaves))``. ``genome.encode_shape`` DISPATCHES to it when
    HAS_NATIVE (the caller maps depth → shape + builds the dict) → the dict is
    BYTE-IDENTICAL to the pure Python (this pins that dispatch).

  * ``srmech_genome_telomere`` — the CHROM boundary cap WRITER: the fixed-width
    ``dim``-byte §44 cap leaf ``[0x43] + label, NUL-padded``. BYTE-IDENTICAL to
    the bytes the pure ``telomere`` wraps in ``HV(sectors=256)``.
    ``genome.telomere`` DISPATCHES to it when HAS_NATIVE.

The genome in-memory ops are byte-exact (cap framing + reversible Klein-4 XOR),
so everything here is byte-identical portable — NOT within-tol. Additive C
symbols → SRMECH_ABI_VERSION stays 4. numpy-free.
"""
from __future__ import annotations

import pytest

from srmech.biology import genome
from srmech import _native


_NS = ([1, 2, 3, 255, 256, 257, 512, 1023, 1024, 1025, 4095, 4096, 4097, 5000,
        65535, 65536, 1_000_000, 1_770_000, 16_777_216, 16_777_217]
       + list(range(1, 1200))
       + [(1 << 32), (1 << 40) + 7, (1 << 56) - 1, (1 << 56), (1 << 63),
          (1 << 64) - 1])
_LABELS = ["", "a", "chromosome", "chr-1", "telomere_end", "TTAGGG",
           "unicode-éè", "z" * 62, "z" * 63, "n" * 30]
_DIMS = [8, 16, 32, 64, 256]


def _pure_encode_shape(n: int) -> dict:
    leaves = (n + genome.LEAF_CAP - 1) // genome.LEAF_CAP
    depth = genome._ceil_log4(leaves)
    shape = "tome" if depth == 0 else "mobius" if depth == 1 else "quad_strand"
    return {"n": n, "shape": shape, "leaves": leaves, "depth": depth,
            "leaf_cap": genome.LEAF_CAP}


# ── the C peers are actually loaded (so parity exercises C, not both-pure) ─────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_cap_foundation_symbols_present():
    assert _native.has_native_genome_encode_shape()
    assert _native.has_native_genome_telomere()
    assert _native.genome_encode_shape_c(5000) == (20, 3)   # ceil(5000/256)=20, log4→3
    assert _native.genome_telomere_c("chrX", 64) is not None
    # ABI is 13 as of rc418 (`#T1108` widened nine exported signatures; this
    # genome surface is additive-unchanged).
    assert _native.EXPECTED_ABI_VERSION == 20


# ── (i) srmech_genome_encode_shape → the dict is BYTE-IDENTICAL native-vs-pure ─

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_encode_shape_native_equals_pure_byte_identical():
    saved = _native.HAS_NATIVE
    try:
        for n in _NS:
            _native.HAS_NATIVE = True
            native = genome.encode_shape(n)
            _native.HAS_NATIVE = False
            pure = genome.encode_shape(n)
            assert native == pure == _pure_encode_shape(n), n
            # the native tuple itself matches the arithmetic (in uint64 range)
            if n < (1 << 64):
                _native.HAS_NATIVE = True
                assert _native.genome_encode_shape_c(n) == (pure["leaves"],
                                                            pure["depth"]), n
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_encode_shape_big_n_routes_to_pure():
    # n >= 2**64 is out of the uint64 fast path → the wrapper returns None and the
    # exact pure ceil-div/ceil-log4 handles it (byte-identical result).
    big = (1 << 64) + 987654321
    assert _native.genome_encode_shape_c(big) is None
    assert genome.encode_shape(big) == _pure_encode_shape(big)


# ── (ii) srmech_genome_telomere → the cap bytes are BYTE-IDENTICAL native-vs-pure

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_telomere_native_equals_pure_byte_identical():
    saved = _native.HAS_NATIVE
    try:
        for label in _LABELS:
            raw = label.encode("utf-8")
            for dim in _DIMS:
                if len(raw) > dim - 1:
                    continue
                _native.HAS_NATIVE = True
                native = genome.telomere(label, dim)
                nb = _native.genome_telomere_c(label, dim)   # direct native bytes
                _native.HAS_NATIVE = False
                pure = genome.telomere(label, dim)
                assert native.tobytes() == pure.tobytes(), (label, dim)
                # the native bytes match the exact §44 framing
                assert nb == pure.tobytes()
                assert nb[0] == genome.CHROM_CAP_MARKER == 0x43
                assert nb[1:1 + len(raw)] == raw
                assert nb[1 + len(raw):] == b"\x00" * (dim - 1 - len(raw))
                assert len(nb) == dim
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_telomere_overlong_label_raises_in_both_paths():
    # native returns None for an over-long label so the pure _pack_cap raises the
    # exact ValueError — identical error semantics native or pure.
    assert _native.genome_telomere_c("x" * 64, 64) is None
    saved = _native.HAS_NATIVE
    try:
        for flag in (True, False):
            _native.HAS_NATIVE = flag
            with pytest.raises(ValueError):
                genome.telomere("x" * 64, 64)
    finally:
        _native.HAS_NATIVE = saved


# ── (iii) the PURE path is correct on its own (runs numpy-free, no-C hosts too) ─

def test_encode_shape_pure_known_values():
    # the F715 attested table (docstring): 200→tome, 800→mobius, 5000→depth 3,
    # 1_770_000→depth 7.
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        assert genome.encode_shape(200)["shape"] == "tome"
        assert genome.encode_shape(800)["shape"] == "mobius"
        s = genome.encode_shape(5000)
        assert s["shape"] == "quad_strand" and s["depth"] == 3
        assert genome.encode_shape(1_770_000)["depth"] == 7
        # boundaries: 256→tome (1 leaf, depth 0), 1024→mobius (4 leaves, depth 1),
        # 1025→quad_strand (5 leaves, depth 2).
        assert genome.encode_shape(256)["shape"] == "tome"
        assert genome.encode_shape(1024)["shape"] == "mobius"
        assert genome.encode_shape(1025)["shape"] == "quad_strand"
    finally:
        _native.HAS_NATIVE = saved


def test_encode_shape_rejects_nonpositive():
    for bad in (0, -1, -256):
        with pytest.raises(ValueError):
            genome.encode_shape(bad)


def test_telomere_cap_format_pure():
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        cap = genome.telomere("chrX", 64)
        raw = cap.tobytes()
        assert len(raw) == 64
        assert raw[0] == 0x43
        assert raw[1:5] == b"chrX"
        assert raw[5:] == b"\x00" * 59
        # same label → same cap; distinct labels → distinct caps (§44 self-describe)
        assert genome.telomere("chrX", 64).tobytes() == raw
        assert genome.telomere("chrY", 64).tobytes() != raw
    finally:
        _native.HAS_NATIVE = saved
