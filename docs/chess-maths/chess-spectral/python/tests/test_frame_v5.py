"""Tests for v5 unified wire format I/O (PR-B scope: dense mode + dispatch).

Per ADR-001 (docs/adr/wire_format/ADR-001-v5-unified-encoding-modes.md).
"""
from __future__ import annotations

import gzip
import os
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Bootstrap (mirrors test_smoke_e2e.py's discovery convention).
HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
sys.path.insert(0, str(PY_DIR))

from chess_spectral import frame_v5  # noqa: E402
from chess_spectral.frame_v5 import (  # noqa: E402
    V5_MAGIC, V5_VERSION, V5_HEADER_SIZE,
    MODE_DENSE, MODE_PER_CHANNEL, MODE_XOR_STREAM,
    HeaderV5,
    pack_frame_2d_dense, unpack_frame_2d_dense,
    pack_frame_4d_dense, unpack_frame_4d_dense,
    write_v5_dense_2d, write_v5_dense_4d,
    peek_version, open_read_transparent,
    read_v5_header, iter_v5_frames_dense,
)


# ─── Header pack / unpack ───────────────────────────────────────────


def test_v5_header_size_is_256():
    """v5 header must be exactly 256 bytes (matches v2/v4 geometry)."""
    h = HeaderV5(encoding_dim=640, n_plies=0, n_dimensions=2)
    assert len(h.pack()) == V5_HEADER_SIZE


def test_v5_header_2d_dense_roundtrip():
    h = HeaderV5(encoding_dim=640, n_plies=42, n_dimensions=2,
                 encoding_mode=MODE_DENSE)
    raw = h.pack()
    h2 = HeaderV5.unpack(raw)
    assert h2.magic == V5_MAGIC
    assert h2.version == V5_VERSION
    assert h2.encoding_dim == 640
    assert h2.n_plies == 42
    assert h2.n_dimensions == 2
    assert h2.encoding_mode == MODE_DENSE
    assert h2.board_dim_side == 8


def test_v5_header_4d_dense_roundtrip():
    h = HeaderV5(encoding_dim=45056, n_plies=88, n_dimensions=4,
                 encoding_mode=MODE_DENSE)
    raw = h.pack()
    h2 = HeaderV5.unpack(raw)
    assert h2.magic == V5_MAGIC
    assert h2.version == V5_VERSION
    assert h2.encoding_dim == 45056
    assert h2.n_plies == 88
    assert h2.n_dimensions == 4
    assert h2.encoding_mode == MODE_DENSE


def test_v5_header_padding_is_zero():
    """The reserved[223] bytes must be zero-filled."""
    h = HeaderV5(encoding_dim=640, n_plies=0, n_dimensions=2)
    raw = h.pack()
    # Header struct fits in 33 bytes (8 magic + 6*4 fields + 1 mode).
    # Bytes 33..255 must be zero.
    assert raw[33:V5_HEADER_SIZE] == b"\x00" * (V5_HEADER_SIZE - 33)


def test_v5_header_rejects_bad_n_dimensions():
    with pytest.raises(ValueError, match="n_dimensions"):
        HeaderV5(encoding_dim=640, n_plies=0, n_dimensions=3)


def test_v5_header_rejects_bad_encoding_mode():
    with pytest.raises(ValueError, match="encoding_mode"):
        HeaderV5(encoding_dim=640, n_plies=0, n_dimensions=2,
                 encoding_mode=99)


def test_v5_header_rejects_dim_mismatch():
    """encoding_dim must match n_dimensions (2D=640, 4D=45056)."""
    with pytest.raises(ValueError, match="encoding_dim"):
        HeaderV5(encoding_dim=45056, n_plies=0, n_dimensions=2)
    with pytest.raises(ValueError, match="encoding_dim"):
        HeaderV5(encoding_dim=640, n_plies=0, n_dimensions=4)


def test_v5_unpack_rejects_bad_magic():
    raw = bytearray(V5_HEADER_SIZE)
    raw[:8] = b"BADMAGIC"
    with pytest.raises(ValueError, match="bad magic"):
        HeaderV5.unpack(bytes(raw))


def test_v5_unpack_rejects_bad_version():
    """A v2 header (version=2) must be rejected by the v5 unpacker;
    callers route to legacy reader instead."""
    raw = bytearray(V5_HEADER_SIZE)
    raw[:8] = V5_MAGIC
    struct.pack_into("<I", raw, 8, 2)  # version=2
    struct.pack_into("<I", raw, 12, 640)
    struct.pack_into("<I", raw, 16, 2568)
    struct.pack_into("<I", raw, 20, 0)
    struct.pack_into("<I", raw, 24, 8)
    struct.pack_into("<I", raw, 28, 2)
    with pytest.raises(ValueError, match="bad version"):
        HeaderV5.unpack(bytes(raw))


# ─── Dense frame pack / unpack — 2D ─────────────────────────────────


def test_v5_2d_dense_frame_roundtrip():
    rng = np.random.default_rng(seed=42)
    enc = rng.standard_normal(640).astype(np.float32)
    raw = pack_frame_2d_dense(enc, ply=7, move_from=12, move_to=28,
                              move_promo=0, move_flags=0)
    enc2, ply, mfrom, mto, mpromo, mflags = unpack_frame_2d_dense(raw)
    np.testing.assert_array_equal(enc, enc2)
    assert (ply, mfrom, mto, mpromo, mflags) == (7, 12, 28, 0, 0)


def test_v5_2d_dense_frame_size_matches_v2():
    """v5 dense 2D frame body size = 2568 bytes (= v2 frame size)."""
    enc = np.zeros(640, dtype=np.float32)
    raw = pack_frame_2d_dense(enc, 0, 0, 0, 0, 0)
    assert len(raw) == 2568


# ─── Dense frame pack / unpack — 4D ─────────────────────────────────


def test_v5_4d_dense_frame_roundtrip():
    rng = np.random.default_rng(seed=43)
    enc = rng.standard_normal(45056).astype(np.float32)
    raw = pack_frame_4d_dense(enc, ply=11, from_sq=(0, 0, 0, 1),
                              to_sq=(2, 2, 0, 1), promo=0, flags=0)
    enc2, ply, frm, to, promo, flags = unpack_frame_4d_dense(raw)
    np.testing.assert_array_equal(enc, enc2)
    assert ply == 11
    assert frm == (0, 0, 0, 1)
    assert to == (2, 2, 0, 1)
    assert (promo, flags) == (0, 0)


def test_v5_4d_dense_frame_size_matches_v4():
    """v5 dense 4D frame body size = 180238 = 45056*4 + 14 (= v4 frame)."""
    enc = np.zeros(45056, dtype=np.float32)
    raw = pack_frame_4d_dense(enc, 0, (0, 0, 0, 0), (0, 0, 0, 0), 0, 0)
    assert len(raw) == 45056 * 4 + 14


# ─── End-to-end write + read via dispatcher (2D) ───────────────────


def test_v5_2d_dense_write_then_read(tmp_path):
    rng = np.random.default_rng(seed=99)
    out = tmp_path / "test.spectralz"
    plies = [
        (rng.standard_normal(640).astype(np.float32),
         i, i, (i + 1) % 64, 0, 0)
        for i in range(5)
    ]
    n = write_v5_dense_2d(out, plies, compress=False)
    assert n == 5
    assert out.is_file()

    # peek_version should report v5
    assert peek_version(out) == V5_VERSION

    fp = open_read_transparent(out)
    try:
        hdr = read_v5_header(fp)
        assert hdr.version == V5_VERSION
        assert hdr.n_dimensions == 2
        assert hdr.encoding_mode == MODE_DENSE
        assert hdr.encoding_dim == 640
        assert hdr.n_plies == 5

        frames = list(iter_v5_frames_dense(fp, hdr))
        assert len(frames) == 5
        for i, raw in enumerate(frames):
            enc, ply, mfrom, mto, _, _ = unpack_frame_2d_dense(raw)
            np.testing.assert_array_equal(enc, plies[i][0])
            assert ply == i
    finally:
        fp.close()


def test_v5_2d_dense_write_compressed(tmp_path):
    """gzip-compressed v5 file round-trips through transparent reader."""
    out = tmp_path / "test.spectralz"
    enc = np.ones(640, dtype=np.float32)
    n = write_v5_dense_2d(out, [(enc, 0, 0xFF, 0xFF, 0, 0)], compress=True)
    assert n == 1

    # File starts with gzip magic
    with open(out, "rb") as fp:
        assert fp.read(2) == b"\x1f\x8b"

    # Transparent reader handles it
    assert peek_version(out) == V5_VERSION


# ─── End-to-end write + read (4D) ───────────────────────────────────


def test_v5_4d_dense_write_then_read(tmp_path):
    rng = np.random.default_rng(seed=101)
    out = tmp_path / "test.spectralz4"
    plies = [
        (rng.standard_normal(45056).astype(np.float32), i,
         (0, 0, 0, 0), (i % 8, 0, 0, 0), 0, 0)
        for i in range(3)
    ]
    n = write_v5_dense_4d(out, plies, compress=False)
    assert n == 3
    assert out.is_file()

    assert peek_version(out) == V5_VERSION

    fp = open_read_transparent(out)
    try:
        hdr = read_v5_header(fp)
        assert hdr.version == V5_VERSION
        assert hdr.n_dimensions == 4
        assert hdr.encoding_dim == 45056
        assert hdr.n_plies == 3

        frames = list(iter_v5_frames_dense(fp, hdr))
        assert len(frames) == 3
        for i, raw in enumerate(frames):
            enc, ply, frm, to, _, _ = unpack_frame_4d_dense(raw)
            np.testing.assert_array_equal(enc, plies[i][0])
            assert ply == i
            assert to == (i % 8, 0, 0, 0)
    finally:
        fp.close()


# ─── peek_version dispatcher: legacy formats ───────────────────────


def test_peek_version_detects_v2(tmp_path):
    """A v2 file (legacy 2D) yields version=2 from peek_version."""
    from chess_spectral.frame import Header, write_file, Frame

    out = tmp_path / "legacy.spectral"
    enc = np.zeros(640, dtype=np.float32)
    write_file(out, [Frame(encoding=enc, ply=0)], compress=False)
    assert peek_version(out) == 2


def test_peek_version_detects_v4(tmp_path):
    """A v4 file (legacy 4D) yields version=4 from peek_version."""
    from chess_spectral.frame_4d import (
        pack_header, pack_frame, ENCODING_DIM_4D,
    )

    out = tmp_path / "legacy.spectralz4"
    enc = np.zeros(ENCODING_DIM_4D, dtype=np.float32)
    frame_bytes = ENCODING_DIM_4D * 4 + 14
    body = pack_frame(enc, 0, (0, 0, 0, 0), (0, 0, 0, 0), 0, 0)
    with open(out, "wb") as fp:
        fp.write(pack_header(ENCODING_DIM_4D, frame_bytes, 1))
        fp.write(body)
    assert peek_version(out) == 4


def test_peek_version_handles_gzip(tmp_path):
    """gzip-compressed v5 file yields version=5 transparently."""
    out = tmp_path / "test.spectralz"
    enc = np.zeros(640, dtype=np.float32)
    write_v5_dense_2d(out, [(enc, 0, 0xFF, 0xFF, 0, 0)], compress=True)
    assert peek_version(out) == V5_VERSION


# ─── Mode 1 / 2 stubs raise NotImplementedError until PR-C/PR-D ─────


def test_v5_per_channel_mode_constant_exists():
    """Mode 1 constant defined; full implementation lands in PR-C."""
    assert MODE_PER_CHANNEL == 1


def test_v5_xor_stream_mode_constant_exists():
    """Mode 2 constant defined; full implementation lands in PR-D."""
    assert MODE_XOR_STREAM == 2


def test_v5_iter_dense_rejects_non_dense_mode():
    """iter_v5_frames_dense must refuse to read non-dense frames."""
    h = HeaderV5(encoding_dim=640, n_plies=0, n_dimensions=2,
                 encoding_mode=MODE_PER_CHANNEL)
    fp = tempfile.TemporaryFile()
    try:
        with pytest.raises(ValueError, match="encoding_mode=0"):
            list(iter_v5_frames_dense(fp, h))
    finally:
        fp.close()
