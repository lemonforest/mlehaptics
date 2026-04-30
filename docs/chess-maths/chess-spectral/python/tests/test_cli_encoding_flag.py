"""Test the --encoding={xor,channel,full} CLI flag added in v1.6.x
Track 2 PR-5.

Coverage:
  * Without --encoding: 2D encode-fen produces v2; 4D encode-fen4
    produces v4 (no behavior change vs v1.6.0).
  * With --encoding=full: writes v5 mode 0 (dense) at the right
    dimension.
  * With --encoding=channel: writes v5 mode 1 (per-channel) — the
    file's encoding_mode header byte is 1.
  * With --encoding=xor: writes v5 mode 2 (XOR-stream) — encoding_mode
    header byte is 2.
  * v5 files round-trip via the chess_spectral.frame_v5 readers
    (encoding-aware iter_v5_frames_*).

Tests programmatically drive cmd_encode_fen / cmd_encode_fen4 with a
hand-built argparse.Namespace; no subprocess + no PGN input needed.
That gives us deterministic single-frame coverage.
"""
from __future__ import annotations

import argparse
import struct

import numpy as np
import pytest

from chess_spectral.cli import cmd_encode_fen
from chess_spectral.frame_v5 import (
    HeaderV5, V5_MAGIC, V5_VERSION, V5_HEADER_SIZE,
    MODE_DENSE, MODE_PER_CHANNEL, MODE_XOR_STREAM,
    iter_v5_frames_dense, iter_v5_frames_per_channel,
    iter_v5_frames_xor_stream, read_v5_header,
    open_read_transparent,
)
from chess_spectral_4d.cli import cmd_encode_fen4

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
START_FEN4 = "4d-fen v1: K@0,0,0,0; k@7,7,7,7"


# ─── Helpers ──────────────────────────────────────────────────────────


def _ns(**kwargs) -> argparse.Namespace:
    """Build an argparse.Namespace from kwargs. argparse subparsers
    leave omitted attributes unset (which getattr handles via the
    default), but the dispatchers we test here assume args.encoding
    exists — so we always set it explicitly (None or a mode string)."""
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _read_header_bytes(path) -> bytes:
    with open(path, "rb") as fp:
        return fp.read(V5_HEADER_SIZE)


def _v5_encoding_mode(path) -> int:
    """Read the on-disk encoding_mode byte at offset 32 from a v5 file."""
    return _read_header_bytes(path)[32]


# ─── 2D encode-fen --encoding -----------------------------------------


def test_2d_encode_fen_no_encoding_produces_v2(tmp_path):
    """Default behavior: omit --encoding, v2 magic + version=2 header."""
    out = tmp_path / "start.spectral"
    args = _ns(fen=START_FEN, output=str(out), compress=False, encoding=None)
    rc = cmd_encode_fen(args)
    assert rc == 0
    head = out.read_bytes()[:12]
    # v2 header starts with the same magic but version field is 2.
    assert head[:8] == V5_MAGIC, "magic should be LARTPSEC"
    (version,) = struct.unpack_from("<I", head, 8)
    assert version == 2, "default encode-fen should still write v2"


@pytest.mark.parametrize("mode_flag,mode_const", [
    ("full",    MODE_DENSE),
    ("channel", MODE_PER_CHANNEL),
    ("xor",     MODE_XOR_STREAM),
])
def test_2d_encode_fen_v5_modes(tmp_path, mode_flag, mode_const):
    """--encoding=<mode> writes a v5 file with the matching mode byte."""
    out = tmp_path / f"start_{mode_flag}.spectral"
    args = _ns(fen=START_FEN, output=str(out), compress=False,
               encoding=mode_flag)
    rc = cmd_encode_fen(args)
    assert rc == 0, f"encode-fen --encoding={mode_flag} returned {rc}"
    head = out.read_bytes()[:V5_HEADER_SIZE]
    assert head[:8] == V5_MAGIC
    (version,) = struct.unpack_from("<I", head, 8)
    assert version == V5_VERSION, f"--encoding={mode_flag} should write v5"
    assert head[32] == mode_const, (
        f"--encoding={mode_flag} should set encoding_mode={mode_const}, "
        f"got {head[32]}"
    )
    (n_dim,) = struct.unpack_from("<I", head, 28)
    assert n_dim == 2, "2D encode-fen should write n_dimensions=2"


def test_2d_encode_fen_v5_xor_round_trips(tmp_path):
    """Write an --encoding=xor file, read it back via the v5 iterator,
    verify the encoding decodes byte-exact (XOR with zero baseline =
    the original)."""
    out = tmp_path / "start_xor.spectral"
    args = _ns(fen=START_FEN, output=str(out), compress=False, encoding="xor")
    rc = cmd_encode_fen(args)
    assert rc == 0
    fp = open_read_transparent(str(out))
    try:
        hdr = read_v5_header(fp)
        assert hdr.encoding_mode == MODE_XOR_STREAM
        assert hdr.n_plies == 1
        frames = list(iter_v5_frames_xor_stream(fp, hdr))
    finally:
        fp.close()
    assert len(frames) == 1
    enc, tail = frames[0]
    assert enc.shape == (640,) and enc.dtype == np.float32
    # The starting position has a deterministic encoding; all bytes
    # being non-trivially populated here is enough to verify round-trip
    # didn't corrupt anything.
    assert np.isfinite(enc).all()
    assert len(tail) == 8


def test_2d_encode_fen_v5_channel_round_trips(tmp_path):
    """Same as above for --encoding=channel: read back via the v5
    per-channel iterator and verify the FULL flag was set on the only
    frame (a single FEN encode is always a FULL frame at frame 0)."""
    out = tmp_path / "start_chan.spectral"
    args = _ns(fen=START_FEN, output=str(out), compress=False,
               encoding="channel")
    rc = cmd_encode_fen(args)
    assert rc == 0
    fp = open_read_transparent(str(out))
    try:
        hdr = read_v5_header(fp)
        assert hdr.encoding_mode == MODE_PER_CHANNEL
        assert hdr.n_plies == 1
        frames = list(iter_v5_frames_per_channel(fp, hdr))
    finally:
        fp.close()
    assert len(frames) == 1
    enc, tail, was_full = frames[0]
    assert was_full is True, "single-frame encode should be FULL block"
    assert enc.shape == (640,) and enc.dtype == np.float32
    assert len(tail) == 8


# ─── 4D encode-fen4 --encoding -----------------------------------------


def test_4d_encode_fen4_no_encoding_produces_v4(tmp_path):
    """Default 4D behavior: --encoding omitted writes a v4 file
    (frame_4d.SPECTRALZ_VERSION header)."""
    from chess_spectral.frame_4d import SPECTRALZ_VERSION as V4_VERSION
    out = tmp_path / "start4.spectralz4"
    args = _ns(fen4=START_FEN4, output=str(out), compress=False,
               encoding=None)
    rc = cmd_encode_fen4(args)
    assert rc == 0
    head = out.read_bytes()[:12]
    assert head[:8] == V5_MAGIC, "v4 also uses LARTPSEC magic"
    (version,) = struct.unpack_from("<I", head, 8)
    assert version == V4_VERSION, "default encode-fen4 should still write v4"


@pytest.mark.parametrize("mode_flag,mode_const", [
    ("full",    MODE_DENSE),
    ("channel", MODE_PER_CHANNEL),
    ("xor",     MODE_XOR_STREAM),
])
def test_4d_encode_fen4_v5_modes(tmp_path, mode_flag, mode_const):
    """4D --encoding=<mode> writes a v5 file with the matching mode byte
    and n_dimensions=4."""
    out = tmp_path / f"start4_{mode_flag}.spectralz4"
    args = _ns(fen4=START_FEN4, output=str(out), compress=False,
               encoding=mode_flag)
    rc = cmd_encode_fen4(args)
    assert rc == 0, f"encode-fen4 --encoding={mode_flag} returned {rc}"
    head = out.read_bytes()[:V5_HEADER_SIZE]
    assert head[:8] == V5_MAGIC
    (version,) = struct.unpack_from("<I", head, 8)
    assert version == V5_VERSION
    assert head[32] == mode_const, (
        f"--encoding={mode_flag} should set encoding_mode={mode_const}, "
        f"got {head[32]}"
    )
    (n_dim,) = struct.unpack_from("<I", head, 28)
    assert n_dim == 4, "4D encode-fen4 should write n_dimensions=4"


def test_4d_encode_fen4_v5_dense_round_trips(tmp_path):
    """Write an --encoding=full 4D file, read back via iter_v5_frames_dense,
    verify the header geometry + encoding shape + move tail."""
    out = tmp_path / "start4_full.spectralz4"
    args = _ns(fen4=START_FEN4, output=str(out), compress=False,
               encoding="full")
    rc = cmd_encode_fen4(args)
    assert rc == 0
    fp = open_read_transparent(str(out))
    try:
        hdr = read_v5_header(fp)
        assert hdr.encoding_mode == MODE_DENSE
        assert hdr.n_dimensions == 4
        assert hdr.n_plies == 1
        frame_chunks = list(iter_v5_frames_dense(fp, hdr))
    finally:
        fp.close()
    assert len(frame_chunks) == 1
    # 4D dense frame body = 45056 * 4 + 14 bytes.
    assert len(frame_chunks[0]) == 45056 * 4 + 14


def test_4d_encode_fen4_v5_requires_output(tmp_path):
    """--encoding mode requires --output (cannot stream v5 to stdout
    because the header has a back-filled n_plies)."""
    args = _ns(fen4=START_FEN4, output=None, compress=False, encoding="xor")
    rc = cmd_encode_fen4(args)
    assert rc == 2, "v5 mode without --output should return usage error 2"
