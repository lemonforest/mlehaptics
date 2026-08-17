"""§55 / §Q8 / rc312 — GENOME_FORMAT_VERSION 15 -> 16, the on-disk Q8 migration.

rc311 wired the Q₈ carrier into the GENOME as an ``element_type`` path but the on-disk
WIRE still assumed 2-bit klein4 turns. rc312 migrates the format: a Q₈ (winding-bearing)
genome can now be WRITTEN and READ from disk. The wire gains a SECOND data-turn packing —
a Q₈ turn 3-bit-packs under :data:`~srmech.biology.genome.Q8_PACKED_TURN_MARKER` (0x38) instead
of the klein4 2-bit :data:`~srmech.biology.genome.PACKED_TURN_MARKER` (0x51) — plus a manifest
``carrier`` field. klein4 keeps its 2-bit packer, so a klein4 body is BYTE-IDENTICAL to v15.

This file is the SIX non-negotiable migration prove-gates. Every gate is numpy-free (the
module under test is numpy-free) and seeded (reproducible). NO ``-k`` filter runs them.

  M1  v15->v16 auto-upgrade round-trip — a v15 klein4 genome upgrades and recovers its EXACT
      original sequence; q8_project_v4(upgrade) == v15 and all sign bits 0.
  M2  packed-turn repack differential — v15-unpack vs v16-unpack on the Lk-0 (winding-0) slice
      AGREE after V4 projection (the repack is faithful).
  M3  packer last-byte / padding platform-constant ASSERTION — the partial-final-byte pad is
      asserted with the exact constant; an odd-length strand (partial final byte) is tested.
  M4  v16 Q8 round-trip on disk — write a Q8 genome (nonzero winding) in v16, read it back,
      recall -> exact leaves; the winding survives the write/read.
  M5  manifest mirror byte-identity — the C srmech_json manifest writer stays byte-identical
      to json.dumps with the new format_version + carrier fields (klein4 AND q8).
  M6  klein4 v15 UNCHANGED end-to-end — a klein4 genome written+read+recalled matches, its
      body carries ONLY the 2-bit 0x51 marker (no 0x38), carrier == "klein4".
"""
from __future__ import annotations

import json
import random

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.biology.genome import (
    ELEMENT_TYPE_KLEIN4,
    ELEMENT_TYPE_Q8,
    GENOME_FORMAT_VERSION,
    OCT,
    PACKED_TURN_MARKER,
    QUAD,
    Q8_PACKED_TURN_MARKER,
    chromosome,
    genome_load,
    genome_save,
    recall,
    upgrade_v15_to_v16,
)
from srmech.math.hv import HV
from srmech.biology.q8 import q8_project_v4


# ── helpers ──────────────────────────────────────────────────────────────────
def _q8_leaves(rng, n, leaf_dim):
    return [HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)), sectors=OCT)
            for _ in range(n)]


def _k4_leaves(rng, n, leaf_dim):
    return [HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
            for _ in range(n)]


def _lists(hvs):
    return [h.tolist() for h in hvs]


def test_format_version_is_16():
    """The SSoT constant is bumped to 16 (mirrors SRMECH_GENOME_FORMAT_VERSION in C)."""
    assert GENOME_FORMAT_VERSION == 20
    assert Q8_PACKED_TURN_MARKER == 0x38
    assert PACKED_TURN_MARKER == 0x51            # klein4 marker UNCHANGED


# ── M2 — packed-turn repack differential (v15 vs v16 on the Lk-0 slice) ───────
def test_m2_repack_differential_lk0_slice_agrees():
    """The winding-0 slice (klein4 symbols 0..3) packed BOTH ways round-trips, and after the
    π: Q₈ → V4 projection the v15-unpack and v16-unpack AGREE — the 2-bit → 3-bit repack is
    faithful. Sign bits of the v16 unpack are all 0 (a winding-0 slice)."""
    rng = random.Random(31200)
    trials = 0
    for _ in range(400):
        n = rng.randrange(1, 260)
        v4 = bytes(rng.randrange(QUAD) for _ in range(n))          # winding-0 (0..3)
        v15_back = G._unpack_turn_payload(G._pack_turn_block(v4)[1:], n)
        v16_back = G._unpack_turn_payload_q8(G._pack_turn_block_q8(v4)[1:], n)
        assert bytes(q8_project_v4(v15_back)) == v4                # klein4 unpack is identity
        assert bytes(q8_project_v4(v16_back)) == v4                # Q8 unpack projects to v4
        assert all((b >> 2) == 0 for b in v16_back)                # no winding on the slice
        trials += 1
    assert trials == 400


# ── M3 — packer last-byte / padding platform-constant assertion ──────────────
def test_m3_packer_padding_constant_and_partial_final_byte():
    """The Q8 packer asserts the partial-final-byte pad with the EXACT constant
    ``pad_bits = ceil(leaf_dim*3/8)*8 - leaf_dim*3`` and that those low bits are zero. Every
    odd/partial length (a partial final byte) round-trips exactly, and the payload length is
    the pinned ``ceil(leaf_dim*3/8)`` — the packing constant lives in an assertion, not a
    comment (the macOS-cap-overflow lesson: platform/packing constants belong in an assert)."""
    rng = random.Random(31203)
    # every length 1..300 incl the odd/partial-final-byte cases
    for n in list(range(1, 301)):
        block = bytes(rng.randrange(OCT) for _ in range(n))
        packed = G._pack_turn_block_q8(block)
        assert packed[0] == Q8_PACKED_TURN_MARKER
        plen = len(packed) - 1
        assert plen == (n * 3 + 7) // 8 == G._packed_payload_len_q8(n)   # exact payload len
        pad_bits = plen * 8 - n * 3
        assert 0 <= pad_bits < 8
        if pad_bits and plen:
            assert packed[-1] & ((1 << pad_bits) - 1) == 0              # low pad bits zero
        assert G._unpack_turn_payload_q8(packed[1:], n) == block         # exact round-trip
    # a non-Q8 symbol (> 7) is rejected on the packing path
    with pytest.raises(ValueError):
        G._pack_turn_block_q8(bytes([8]))


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome peer required for the C↔Python packer parity")
def test_m3_c_python_packer_parity():
    """The exported C primitives srmech_genome_q8_pack_turn / _unpack_turn are BYTE-IDENTICAL
    to the pure Python codec over odd/partial leaf_dims (genome fully in C)."""
    import ctypes
    lib = _native.LIB
    if not (hasattr(lib, "srmech_genome_q8_pack_turn")
            and hasattr(lib, "srmech_genome_q8_unpack_turn")):
        pytest.skip("q8 pack/unpack turn C peers not in this lib")
    rng = random.Random(31299)
    for n in [1, 2, 3, 7, 8, 17, 63, 64, 100, 255, 256]:
        leaf = bytes(rng.randrange(OCT) for _ in range(n))
        py = G._pack_turn_block_q8(leaf)
        out = (ctypes.c_ubyte * (1 + (n * 3 + 7) // 8))()
        olen = ctypes.c_size_t(0)
        rc = lib.srmech_genome_q8_pack_turn(
            (ctypes.c_ubyte * n)(*leaf), ctypes.c_uint32(n), out, ctypes.byref(olen))
        assert rc == 0 and bytes(out[:olen.value]) == py
        ub = (ctypes.c_ubyte * n)()
        rc2 = lib.srmech_genome_q8_unpack_turn(
            (ctypes.c_ubyte * (len(py) - 1))(*py[1:]), ctypes.c_uint32(n), ub)
        assert rc2 == 0 and bytes(ub) == leaf


# ── M4 — v16 Q8 round-trip on disk (with nonzero winding) ────────────────────
def test_m4_q8_disk_round_trip_winding_survives(tmp_path):
    """Write a Q₈ genome with NONZERO winding to disk in v16, read it back, recall -> the exact
    original leaves; the winding (sign bits) survives the write/read. The manifest stamps
    format_version 16 + carrier "q8"; the body carries the 0x38 (never 0x51) marker."""
    rng = random.Random(31204)
    leaf_dim = 40
    for trial in range(30):
        one = HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(leaf_dim)), sectors=OCT)
        leaves = _q8_leaves(rng, rng.randrange(2, 9), leaf_dim)
        # ensure at least one nonzero-winding symbol is present in this trial
        if not any(b >= 4 for lf in leaves for b in lf.tolist()):
            leaves[0] = HV.from_sequence(bytes([4]) + leaves[0].tobytes()[1:], sectors=OCT)
        strand = chromosome(leaves, one, label=f"q8_{trial}", element_type=ELEMENT_TYPE_Q8)
        path = tmp_path / f"q8g_{trial}"
        genome_save(strand, path, one, element_type=ELEMENT_TYPE_Q8)
        man = json.loads((path / "manifest.json").read_text())["data"]
        assert man["format_version"] == 20 and man["carrier"] == "q8"
        st, _cp, _labs = genome_load(path)
        rec = recall(st, one, element_type=ELEMENT_TYPE_Q8)
        assert _lists(rec) == _lists(leaves)                       # exact recall
        assert any(b >= 4 for h in rec for b in h.tolist())        # winding survived
        # the on-disk body's data turns are Q8-packed (0x38), never klein4 (0x51)
        body = (path / "turns.bin").read_bytes()
        markers = {raw[0] for raw, _dec in G._walk_region_blocks(body, leaf_dim)
                   if raw[0] in (PACKED_TURN_MARKER, Q8_PACKED_TURN_MARKER)}
        assert markers == {Q8_PACKED_TURN_MARKER}


# ── M5 — manifest mirror byte-identity (C srmech_json == json.dumps) ──────────
def _save_native_and_pure(strand, one, element_type, tmp_path):
    """Save the SAME strand twice — once via the native C manifest writer, once forcing the
    pure Python json.dumps writer — and return the two on-disk manifest byte strings."""
    native_path = tmp_path / "native"
    pure_path = tmp_path / "pure"
    genome_save(strand, native_path, one, element_type=element_type)   # C srmech_json
    saved = G._native.has_native_genome
    G._native.has_native_genome = lambda: False
    try:
        genome_save(strand, pure_path, one, element_type=element_type)  # json.dumps
    finally:
        G._native.has_native_genome = saved
    return ((native_path / "manifest.json").read_bytes(),
            (pure_path / "manifest.json").read_bytes())


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome peer required for the C manifest mirror gate")
def test_m5_manifest_mirror_byte_identity_klein4(tmp_path):
    """The C srmech_json manifest writer is byte-identical to json.dumps(sort_keys=True) with
    the new format_version + carrier fields — the klein4 carrier."""
    rng = random.Random(31205)
    one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(40)), sectors=QUAD)
    strand = chromosome(_k4_leaves(rng, 5, 40), one, label="k4")
    c_bytes, py_bytes = _save_native_and_pure(strand, one, ELEMENT_TYPE_KLEIN4, tmp_path)
    assert c_bytes == py_bytes
    assert b'"carrier": "klein4"' in c_bytes
    assert b'"format_version": 20' in c_bytes


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome peer required for the C manifest mirror gate")
def test_m5_manifest_mirror_byte_identity_q8(tmp_path):
    """The C srmech_json manifest writer is byte-identical to json.dumps with the new fields —
    the q8 carrier (the C body-scan detects the 0x38 turn and stamps carrier "q8")."""
    rng = random.Random(31206)
    one = HV.from_sequence(bytes(rng.randrange(OCT) for _ in range(40)), sectors=OCT)
    strand = chromosome(_q8_leaves(rng, 5, 40), one, label="q8", element_type=ELEMENT_TYPE_Q8)
    c_bytes, py_bytes = _save_native_and_pure(strand, one, ELEMENT_TYPE_Q8, tmp_path)
    assert c_bytes == py_bytes
    assert b'"carrier": "q8"' in c_bytes
    assert b'"format_version": 20' in c_bytes


# ── M6 — klein4 v15 UNCHANGED end-to-end ─────────────────────────────────────
def test_m6_klein4_unchanged_end_to_end(tmp_path):
    """A klein4 genome written+read+recalled is exact; its body carries ONLY the 2-bit 0x51
    marker (never the 0x38 Q8 marker), and its carrier is "klein4" — no regression on the
    shipped path (the 2-bit packer is byte-untouched)."""
    rng = random.Random(31207)
    leaf_dim = 40
    one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
    leaves = _k4_leaves(rng, 7, leaf_dim)
    strand = chromosome(leaves, one, label="k6")
    path = tmp_path / "k4g"
    genome_save(strand, path, one)
    man = json.loads((path / "manifest.json").read_text())["data"]
    assert man["carrier"] == "klein4" and man["format_version"] == 20
    st, _cp, _labs = genome_load(path)
    rec = recall(st, one, element_type=ELEMENT_TYPE_KLEIN4)
    assert _lists(rec) == _lists(leaves)
    body = (path / "turns.bin").read_bytes()
    markers = {raw[0] for raw, _dec in G._walk_region_blocks(body, leaf_dim)
               if raw[0] in (PACKED_TURN_MARKER, Q8_PACKED_TURN_MARKER)}
    assert markers == {PACKED_TURN_MARKER}          # ONLY 2-bit klein4 turns


# ── M1 — v15 -> v16 auto-upgrade round-trip ──────────────────────────────────
def _make_v15_klein4_genome(tmp_path, rng):
    """Save a klein4 genome, then rewrite its manifest to LOOK v15 (format_version 15, no
    carrier field) — the on-disk shape an rc311 (v15) writer produced (its klein4 body is
    byte-identical to v16's, so this is a faithful v15 fixture)."""
    leaf_dim = 40
    one = HV.from_sequence(bytes(rng.randrange(QUAD) for _ in range(leaf_dim)), sectors=QUAD)
    leaves = _k4_leaves(rng, 6, leaf_dim)
    strand = chromosome(leaves, one, label="v15")
    path = tmp_path / "v15g"
    genome_save(strand, path, one)
    mpath = path / "manifest.json"
    full = json.loads(mpath.read_text())
    full["data"]["format_version"] = 15
    full["data"].pop("carrier", None)
    mpath.write_text(json.dumps(full, sort_keys=True, ensure_ascii=False) + "\n",
                     encoding="utf-8", newline="\n")
    return path, one, leaves, leaf_dim


def test_m1_v15_to_v16_auto_upgrade_round_trip(tmp_path):
    """An existing v15 (klein4) genome upgrades and recovers its EXACT original sequence;
    q8_project_v4(upgrade) == v15 and every sign bit is 0; the body is BYTE-IDENTICAL (a v15
    klein4 turn is the winding-0 slice of a v16 Q₈ turn, so no bytes move), only the manifest
    format_version + carrier fields change."""
    rng = random.Random(31201)
    path, one, leaves, leaf_dim = _make_v15_klein4_genome(tmp_path, rng)

    body_before = (path / "turns.bin").read_bytes()
    data = upgrade_v15_to_v16(path)
    body_after = (path / "turns.bin").read_bytes()

    # the manifest re-stamps to v16 + carrier; the body is byte-identical (klein4 no repack)
    assert body_after == body_before
    assert data["format_version"] == 20 and data["carrier"] == "klein4"
    man = json.loads((path / "manifest.json").read_text())["data"]
    assert man["format_version"] == 20 and man["carrier"] == "klein4"

    # recall recovers the EXACT original sequence after the upgrade
    st, _cp, _labs = genome_load(path)
    rec = recall(st, one, element_type=ELEMENT_TYPE_KLEIN4)
    assert _lists(rec) == _lists(leaves)

    # q8_project_v4(upgrade) == v15 and all sign bits 0 (the winding-0 slice property)
    for raw, dec in G._walk_region_blocks(body_after, leaf_dim):
        if raw[0] == PACKED_TURN_MARKER:                       # a klein4 data turn
            assert bytes(q8_project_v4(dec)) == dec            # V4 projection is identity
            assert all((b >> 2) == 0 for b in dec)             # every sign bit is 0


def test_m1_upgrade_is_idempotent(tmp_path):
    """Upgrading an already-v16 genome re-stamps to itself (idempotent) — the body and the
    manifest stay byte-identical across a second upgrade."""
    rng = random.Random(31208)
    path, one, _leaves, _ld = _make_v15_klein4_genome(tmp_path, rng)
    upgrade_v15_to_v16(path)
    body1 = (path / "turns.bin").read_bytes()
    man1 = (path / "manifest.json").read_bytes()
    upgrade_v15_to_v16(path)                                    # second upgrade — no-op
    assert (path / "turns.bin").read_bytes() == body1
    assert (path / "manifest.json").read_bytes() == man1
