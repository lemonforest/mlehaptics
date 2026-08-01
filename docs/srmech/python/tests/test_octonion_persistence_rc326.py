"""§55 / §𝕆-TURN / rc326 — GENOME_FORMAT_VERSION 18 -> 19, the octonion DATA-turn on-disk
migration.

rc324 shipped the 𝕆 (octonion) genome carrier + the 4-bit codec
(:func:`~srmech.biology.genome._pack_turn_block_octonion`) and rc325 the 𝕆 fiber CAP, but BOTH
deferred octonion DATA-turn ON-DISK persistence: ``_disk_block`` packed only klein4 / Q₈ turns,
so a genome FILE could not hold octonion DATA turns (only the fiber cap). rc326 closes that gap
— the exact third stage the Q₈ path took (carrier rc310 -> channel rc311 -> on-disk rc312). The
wire gains a THIRD data-turn packing: an octonion turn 4-bit-packs under
:data:`~srmech.biology.genome.OCTONION_PACKED_TURN_MARKER` (0x39), and the manifest ``carrier``
gains the ``"octonion"`` value. After rc326 the 𝕆 rung is END-TO-END: octonion turns persist to
``turns.bin`` and round-trip through a genome file.

Every gate is numpy-free (the module under test is numpy-free) and seeded (reproducible).

  P1  octonion DATA-turn disk round-trip — encode a genome whose turns INCLUDE the
      non-quaternionic indices 4..7 (e₄..e₇), save to disk, reopen, decode -> byte-identical
      turns; recall -> the exact octonion leaves. The body carries the 0x39 marker (never
      0x51 / 0x38). carrier == "octonion", format_version == 19.
  P2  the associator survives a disk round-trip — genome_octonion_associator over the reopened
      strand's data turns == over the original (the non-associativity is preserved on disk),
      with a genuinely nonzero defect present.
  P3  BACKWARD-COMPAT — a klein4 strand, a Q₈ strand, and an rc325 octonion-FIBER-CAP-only
      strand all open + round-trip byte-identically; klein4 / Q₈ on-disk turns are UNCHANGED
      (0x51 / 0x38, never 0x39); the format-version read-guard accepts an OLD (< 19) manifest.
  P4  Python<->C disk parity — the native save/load and the pure save/load produce a
      byte-identical ``turns.bin`` AND a byte-identical ``manifest.json`` for an octonion
      strand; the C disk walker classifies the 0x39 block width correctly; the C 4-bit codec
      is byte-identical to the Python codec over odd/partial leaf_dims.
  P5  the octonion fiber CAP now persists too — an octonion-fiber-bearing strand saves + reopens
      and its 0x4F fiber is readable back (the 𝕆 rung is end-to-end: turns AND fiber on disk).
"""
from __future__ import annotations

import ctypes
import json
import random
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.biology import genome as G
from srmech.biology.genome import (
    ELEMENT_TYPE_KLEIN4,
    ELEMENT_TYPE_OCTONION,
    ELEMENT_TYPE_Q8,
    GENOME_FORMAT_VERSION,
    OCT,
    OCTONION_PACKED_TURN_MARKER,
    OCTONION_SECTORS,
    OCT_FIBER_CAP_MARKER,
    PACKED_TURN_MARKER,
    QUAD,
    Q8_PACKED_TURN_MARKER,
    chromosome,
    genome_add_octonion_fiber,
    genome_load,
    genome_octonion_associator,
    genome_read_octonion_fiber,
    genome_save,
    recall,
    _cap_kind,
    _hv_bytes,
    _pack_turn_block_octonion,
    _packed_payload_len_octonion,
    _unpack_turn_payload_octonion,
)
from srmech.math.hv import HV


# ── helpers ──────────────────────────────────────────────────────────────────
def _lists(strand):
    return [list(hv.tolist()) for hv in strand]


def _oct_leaves(rng, n, leaf_dim, lo=0, hi=OCTONION_SECTORS):
    return [HV.from_sequence(bytes(rng.randrange(lo, hi) for _ in range(leaf_dim)),
                             sectors=OCTONION_SECTORS)
            for _ in range(n)]


def _q8_leaves(rng, n, leaf_dim):
    return [HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)), sectors=OCT)
            for _ in range(n)]


def _k4_leaves(rng, n, leaf_dim):
    return [HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
            for _ in range(n)]


def _data_turns(strand):
    """The STORED (coupled) data turns as raw bytes — every non-cap block."""
    return [_hv_bytes(hv) for hv in strand if _cap_kind(hv) is None]


def _turn_markers(path, leaf_dim):
    body = (Path(path) / "turns.bin").read_bytes()
    return {raw[0] for raw, _dec in G._walk_region_blocks(body, leaf_dim)
            if raw[0] in (PACKED_TURN_MARKER, Q8_PACKED_TURN_MARKER,
                          OCTONION_PACKED_TURN_MARKER)}


def _save_native_and_pure(strand, one, element_type, tmp_path):
    """Save the SAME strand twice — once via the native C path, once forcing the pure Python
    path — and return the two dirs (native, pure)."""
    native_path = tmp_path / "native"
    pure_path = tmp_path / "pure"
    genome_save(strand, native_path, one, element_type=element_type)   # native (if present)
    saved = G._native.has_native_genome
    G._native.has_native_genome = lambda: False
    try:
        genome_save(strand, pure_path, one, element_type=element_type)  # forced pure
    finally:
        G._native.has_native_genome = saved
    return native_path, pure_path


# ── P0 — the format-version pin ──────────────────────────────────────────────
def test_format_version_is_19():
    assert GENOME_FORMAT_VERSION == 19


# ── P1 — octonion DATA-turn disk round-trip (the point) ──────────────────────
def test_octonion_data_turn_disk_round_trip():
    """A genome whose data turns INCLUDE the non-quaternionic indices 4..7 (e₄..e₇ — e.g.
    e₄·e₅, e₆·e₇) is written to disk, reopened, and decodes byte-identically; recall recovers
    the exact octonion leaves. This is what rc325 could only do in-memory: the ``turns.bin``
    base is now a real strict-prefix and the octonion turns persist."""
    rng = random.Random(326001)
    leaf_dim = 20
    for trial in range(25):
        one = HV.from_sequence(bytes(rng.randrange(OCTONION_SECTORS) for _ in range(leaf_dim)),
                               sectors=OCTONION_SECTORS)
        # force high (non-quaternionic) indices 4..7 and their negatives 12..15 to appear
        leaves = _oct_leaves(rng, rng.randrange(2, 8), leaf_dim, lo=4, hi=16)
        strand = chromosome(leaves, one, label=f"oct_{trial}",
                            element_type=ELEMENT_TYPE_OCTONION)
        path = Path(tempfile.mkdtemp()) / f"g_{trial}"
        data = genome_save(strand, path, one, element_type=ELEMENT_TYPE_OCTONION)
        assert data["carrier"] == "octonion" and data["format_version"] == 19
        man = json.loads((path / "manifest.json").read_text())["data"]
        assert man["carrier"] == "octonion" and man["format_version"] == 19

        st, _cp, _labs = genome_load(path, coupling=one)
        assert _lists(st) == _lists(strand)                        # byte-identical turns
        rec = recall(st, one, element_type=ELEMENT_TYPE_OCTONION)
        assert _lists(rec) == _lists(leaves)                       # exact octonion recall
        assert any(b >= 4 for h in rec for b in h.tolist())        # e₄.. survived on disk
        # on-disk data turns are octonion-packed (0x39), never klein4 (0x51) or Q₈ (0x38)
        assert _turn_markers(path, leaf_dim) == {OCTONION_PACKED_TURN_MARKER}


def test_octonion_e4e5_e6e7_specific_products_persist():
    """The specific non-quaternionic products e₄·e₅ and e₆·e₇ round-trip through the file —
    the exact leaves the Q₈ 3-bit symbol could never carry (indices > 7 need the 4th bit)."""
    # bytes 4..7 == +e₄..+e₇; a coupled octonion turn over them exercises the high nibble
    leaf_dim = 8
    one = HV.from_sequence(bytes([1] * leaf_dim), sectors=OCTONION_SECTORS)
    leaves = [HV.from_sequence(bytes([4, 5, 6, 7, 4, 5, 6, 7]), sectors=OCTONION_SECTORS),
              HV.from_sequence(bytes([6, 7, 4, 5, 6, 7, 4, 5]), sectors=OCTONION_SECTORS)]
    strand = chromosome(leaves, one, label="e47", element_type=ELEMENT_TYPE_OCTONION)
    path = Path(tempfile.mkdtemp()) / "g"
    genome_save(strand, path, one, element_type=ELEMENT_TYPE_OCTONION)
    st, _cp, _labs = genome_load(path, coupling=one)
    rec = recall(st, one, element_type=ELEMENT_TYPE_OCTONION)
    assert _lists(rec) == _lists(leaves)
    assert _turn_markers(path, leaf_dim) == {OCTONION_PACKED_TURN_MARKER}


# ── P2 — the associator survives a disk round-trip ───────────────────────────
def test_octonion_associator_survives_disk_round_trip():
    """genome_octonion_associator over the reopened strand's data turns EQUALS it over the
    original — the non-associativity (the fiber the per-turn store cannot carry) is preserved
    on disk — and the defect is genuinely nonzero for at least one construction."""
    rng = random.Random(326002)
    leaf_dim = 32
    saw_nonzero = False
    for trial in range(12):
        one = HV.from_sequence(bytes((1 + i) % 16 for i in range(leaf_dim)),
                               sectors=OCTONION_SECTORS)
        leaves = [HV.from_sequence(
            bytes((1 + 2 * i + 3 * t + trial) % 16 for i in range(leaf_dim)),
            sectors=OCTONION_SECTORS) for t in range(3)]
        strand = chromosome(leaves, one, label="assoc", element_type=ELEMENT_TYPE_OCTONION)
        path = Path(tempfile.mkdtemp()) / "g"
        genome_save(strand, path, one, element_type=ELEMENT_TYPE_OCTONION)
        st, _cp, _labs = genome_load(path, coupling=one)
        a_orig = genome_octonion_associator(_data_turns(strand))
        a_re = genome_octonion_associator(_data_turns(st))
        assert a_orig == a_re
        saw_nonzero = saw_nonzero or any(a_orig)
    assert saw_nonzero, "no non-associative defect appeared across the constructions"


# ── P3 — BACKWARD-COMPAT ─────────────────────────────────────────────────────
def test_backward_compat_klein4_unchanged():
    """A klein4 genome (the default) writes + reopens + recalls exactly; its on-disk data turns
    carry ONLY the 2-bit 0x51 marker (never 0x39), carrier == "klein4"."""
    rng = random.Random(326003)
    leaf_dim = 40
    one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
    leaves = _k4_leaves(rng, 6, leaf_dim)
    strand = chromosome(leaves, one, label="k4")
    path = Path(tempfile.mkdtemp()) / "g"
    data = genome_save(strand, path, one)
    assert data["carrier"] == "klein4" and data["format_version"] == 19
    st, _cp, _labs = genome_load(path, coupling=one)
    assert _lists(st) == _lists(strand)
    assert _lists(recall(st, one, element_type=ELEMENT_TYPE_KLEIN4)) == _lists(leaves)
    assert _turn_markers(path, leaf_dim) == {PACKED_TURN_MARKER}   # UNCHANGED, no 0x39


def test_backward_compat_q8_unchanged():
    """A Q₈ genome writes + reopens + recalls exactly; its on-disk data turns carry ONLY the
    3-bit 0x38 marker (never 0x39), carrier == "q8" — the rc312 wire is untouched by rc326."""
    rng = random.Random(326004)
    leaf_dim = 40
    one = HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)), sectors=OCT)
    leaves = _q8_leaves(rng, 5, leaf_dim)
    # ensure nonzero winding (a symbol >= 4) so it is a genuine Q₈ turn
    if not any(b >= 4 for lf in leaves for b in lf.tolist()):
        leaves[0] = HV.from_sequence(bytes([4]) + leaves[0].tobytes()[1:], sectors=OCT)
    strand = chromosome(leaves, one, label="q8", element_type=ELEMENT_TYPE_Q8)
    path = Path(tempfile.mkdtemp()) / "g"
    data = genome_save(strand, path, one, element_type=ELEMENT_TYPE_Q8)
    assert data["carrier"] == "q8" and data["format_version"] == 19
    st, _cp, _labs = genome_load(path, coupling=one)
    assert _lists(st) == _lists(strand)
    assert _lists(recall(st, one, element_type=ELEMENT_TYPE_Q8)) == _lists(leaves)
    assert _turn_markers(path, leaf_dim) == {Q8_PACKED_TURN_MARKER}   # UNCHANGED, no 0x39


def test_backward_compat_octonion_fiber_cap_only_strand():
    """An rc325 octonion-FIBER-CAP-only strand (data turns in 0..7, plus the 0x4F fiber cap)
    opens + round-trips byte-identically, and its 0x4F octonion fiber is readable back — the
    fiber cap coexists with the new data-turn wiring."""
    rng = random.Random(326005)
    leaf_dim = 28
    one = HV.from_sequence(bytes((1 + i) % 8 for i in range(leaf_dim)), sectors=OCTONION_SECTORS)
    leaves = _oct_leaves(rng, 3, leaf_dim, lo=0, hi=8)     # 0..7 → valid for the octonion fold
    strand = chromosome(leaves, one, label="fibchr", element_type=ELEMENT_TYPE_OCTONION)
    strand = genome_add_octonion_fiber(strand)             # append the 0x4F fiber cap
    assert any(_cap_kind(hv) == OCT_FIBER_CAP_MARKER for hv in strand)
    path = Path(tempfile.mkdtemp()) / "g"
    genome_save(strand, path, one, element_type=ELEMENT_TYPE_OCTONION)
    st, _cp, _labs = genome_load(path, coupling=one)
    assert _lists(st) == _lists(strand)                    # fiber cap AND turns round-trip
    assert any(_cap_kind(hv) == OCT_FIBER_CAP_MARKER for hv in st)
    assert genome_read_octonion_fiber(st) is not None      # the 0x4F fiber reads back


def test_backward_compat_read_guard_accepts_old_version():
    """The format-version read-guard accepts an OLD (< 19) manifest: a genome whose manifest is
    downgraded to a pre-rc326 format_version still opens + round-trips (a v≤18 genome opens on a
    v19 build — the marker-keyed body is self-describing, not gated on the manifest version)."""
    rng = random.Random(326006)
    leaf_dim = 24
    one = HV.from_sequence(bytes((2 + i) % 16 for i in range(leaf_dim)), sectors=OCTONION_SECTORS)
    leaves = _oct_leaves(rng, 4, leaf_dim, lo=4, hi=16)
    strand = chromosome(leaves, one, label="old", element_type=ELEMENT_TYPE_OCTONION)
    path = Path(tempfile.mkdtemp()) / "g"
    genome_save(strand, path, one, element_type=ELEMENT_TYPE_OCTONION)
    mpath = path / "manifest.json"
    man = json.loads(mpath.read_text())
    for old_fmt in (16, 17, 18):
        man["data"]["format_version"] = old_fmt
        mpath.write_text(json.dumps(man))
        st, _cp, _labs = genome_load(path, coupling=one)
        assert _lists(st) == _lists(strand)                # opens unchanged at every old fmt


# ── P4 — Python<->C disk parity ──────────────────────────────────────────────
@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome peer required for the C disk-parity gate")
def test_python_c_disk_parity_turns_bin_and_manifest():
    """Native and pure saves of an octonion strand produce a byte-identical ``turns.bin`` AND a
    byte-identical ``manifest.json`` — the C disk walker classifies the 0x39 block width
    correctly and the C srmech_json writer stamps ``carrier "octonion"`` + format_version 19
    byte-identically to json.dumps."""
    rng = random.Random(326007)
    leaf_dim = 21                                          # odd → a partial final nibble byte
    one = HV.from_sequence(bytes(rng.randrange(OCTONION_SECTORS) for _ in range(leaf_dim)),
                           sectors=OCTONION_SECTORS)
    leaves = _oct_leaves(rng, 6, leaf_dim, lo=4, hi=16)
    strand = chromosome(leaves, one, label="oct", element_type=ELEMENT_TYPE_OCTONION)
    tmp = Path(tempfile.mkdtemp())
    native_path, pure_path = _save_native_and_pure(strand, one, ELEMENT_TYPE_OCTONION, tmp)
    tb_n = (native_path / "turns.bin").read_bytes()
    tb_p = (pure_path / "turns.bin").read_bytes()
    assert tb_n == tb_p                                    # byte-identical body
    m_n = (native_path / "manifest.json").read_bytes()
    m_p = (pure_path / "manifest.json").read_bytes()
    assert m_n == m_p                                      # byte-identical manifest (C == json.dumps)
    assert b'"carrier": "octonion"' in m_n
    assert b'"format_version": 19' in m_n
    # native reload decodes byte-identically
    st, _cp, _labs = genome_load(native_path, coupling=one)
    assert _lists(st) == _lists(strand)


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native octonion codec symbols required for the byte-parity gate")
def test_c_octonion_codec_byte_parity_over_odd_leaf_dims():
    """The exported C 4-bit octonion codec (srmech_genome_octonion_pack_turn / _unpack_turn) is
    BYTE-IDENTICAL to the Python codec over odd/partial leaf_dims (the partial-final-nibble-byte
    alignment risk) — the genome-fully-in-C parity the Q₈ codec proved one rung down."""
    lib = _native.LIB
    assert hasattr(lib, "srmech_genome_octonion_pack_turn")
    assert hasattr(lib, "srmech_genome_octonion_unpack_turn")
    rng = random.Random(326008)
    for leaf_dim in (1, 2, 3, 5, 7, 8, 15, 16, 17, 31, 40, 63, 256):
        leaf = bytes(rng.randrange(OCTONION_SECTORS) for _ in range(leaf_dim))
        py_block = _pack_turn_block_octonion(leaf)
        plen = _packed_payload_len_octonion(leaf_dim)
        out = (ctypes.c_ubyte * (1 + plen))()
        out_len = ctypes.c_size_t(0)
        rc = lib.srmech_genome_octonion_pack_turn(
            (ctypes.c_ubyte * leaf_dim)(*leaf), leaf_dim, out, ctypes.byref(out_len))
        assert rc == 0 and out_len.value == 1 + plen
        assert bytes(out[:out_len.value]) == py_block          # C pack == Python pack
        # C unpack of the (Python) payload recovers the leaf
        payload = py_block[1:]
        uout = (ctypes.c_ubyte * leaf_dim)()
        rc2 = lib.srmech_genome_octonion_unpack_turn(
            (ctypes.c_ubyte * len(payload))(*payload), leaf_dim, uout)
        assert rc2 == 0 and bytes(uout[:leaf_dim]) == leaf
        # Python unpack round-trips too (self-consistency)
        assert _unpack_turn_payload_octonion(payload, leaf_dim) == leaf


# ── P5 — the 𝕆 rung is end-to-end (turns AND fiber on disk) ──────────────────
def test_octonion_rung_is_end_to_end_turns_and_fiber():
    """The full 𝕆 rung on disk: an octonion-turn genome that ALSO carries a 0x4F fiber cap
    persists BOTH — the data turns (0x39) and the fiber cap (0x4F) — and reopens with the turns
    byte-identical, the fiber readable, and carrier "octonion"."""
    rng = random.Random(326009)
    leaf_dim = 30
    one = HV.from_sequence(bytes((1 + i) % 8 for i in range(leaf_dim)), sectors=OCTONION_SECTORS)
    leaves = _oct_leaves(rng, 4, leaf_dim, lo=0, hi=8)
    strand = genome_add_octonion_fiber(
        chromosome(leaves, one, label="e2e", element_type=ELEMENT_TYPE_OCTONION))
    path = Path(tempfile.mkdtemp()) / "g"
    data = genome_save(strand, path, one, element_type=ELEMENT_TYPE_OCTONION)
    assert data["carrier"] == "octonion" and data["format_version"] == 19
    st, _cp, _labs = genome_load(path, coupling=one)
    assert _lists(st) == _lists(strand)
    assert genome_read_octonion_fiber(st) is not None
    # both markers present on disk: the 0x39 data turn AND the 0x4F fiber cap
    body = (path / "turns.bin").read_bytes()
    kinds = {raw[0] for raw, _dec in G._walk_region_blocks(body, leaf_dim)}
    assert OCTONION_PACKED_TURN_MARKER in kinds and OCT_FIBER_CAP_MARKER in kinds
