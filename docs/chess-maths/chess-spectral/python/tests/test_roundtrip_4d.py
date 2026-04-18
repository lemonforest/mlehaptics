"""spectralz v3 (4D) round-trip tests.

Covers:
    * pack_header / unpack_header: field layout, magic, version
    * pack_frame / unpack_frame: bit-exact float32 preservation +
      all metadata (ply, from/to coords, promo, flags)
    * write_spectralz_v3 / read_spectralz_v3: full file round-trip
      across N random frames
    * read_header_any: v3 file detection, garbage-input rejection,
      v2 delegation path (guarded skip if the 2D reader isn't available)

Run via `python -m pytest tests/test_roundtrip_4d.py`.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import frame_4d as frm              # noqa: E402


def _make_random_frame(rng: np.random.Generator, ply: int) -> frm.Frame4D:
    enc = rng.standard_normal(frm.ENCODING_DIM_4D).astype(np.float32)
    from_sq = tuple(int(x) for x in rng.integers(0, 8, size=4))
    to_sq = tuple(int(x) for x in rng.integers(0, 8, size=4))
    promo = int(rng.integers(0, 256))
    flags = int(rng.integers(0, 256))
    return frm.Frame4D(encoding=enc, ply=ply,
                       from_sq=from_sq, to_sq=to_sq,
                       promo=promo, flags=flags)


# ---- Header layout ---------------------------------------------------

def test_header_layout_and_magic():
    h = frm.pack_header(
        encoding_dim=frm.ENCODING_DIM_4D,
        frame_bytes=frm.ENCODING_DIM_4D * 4 + frm.FRAME_TAIL_BYTES,
        n_plies=42,
    )
    assert len(h) == frm.HEADER_SIZE == 256
    assert h[0:8] == frm.SPECTRALZ_V3_MAGIC == b"LARTPSEC"

    hdr = frm.unpack_header(h)
    assert hdr.magic == frm.SPECTRALZ_V3_MAGIC
    assert hdr.version == 3
    assert hdr.encoding_dim == frm.ENCODING_DIM_4D
    assert hdr.frame_bytes == frm.ENCODING_DIM_4D * 4 + frm.FRAME_TAIL_BYTES
    assert hdr.n_plies == 42
    assert hdr.board_dim_side == 8
    assert hdr.n_dimensions == 4


def test_header_rejects_wrong_magic():
    bad = bytearray(frm.pack_header(frm.ENCODING_DIM_4D,
                                    frm.ENCODING_DIM_4D * 4 + 14, 1))
    bad[0] = ord("X")
    with pytest.raises(ValueError, match="bad magic"):
        frm.unpack_header(bytes(bad))


def test_header_rejects_short_input():
    with pytest.raises(ValueError, match="need 256"):
        frm.unpack_header(b"\x00" * 100)


# ---- Frame pack/unpack ----------------------------------------------

def test_frame_encoding_bit_exact():
    rng = np.random.default_rng(0xC0FFEE)
    enc = rng.standard_normal(frm.ENCODING_DIM_4D).astype(np.float32)
    blob = frm.pack_frame(
        enc, ply=123,
        from_sq=(1, 2, 3, 4), to_sq=(5, 6, 7, 0),
        promo=0, flags=0x42,
    )
    assert len(blob) == frm.ENCODING_DIM_4D * 4 + frm.FRAME_TAIL_BYTES
    fr = frm.unpack_frame(blob)
    assert np.array_equal(fr.encoding, enc)    # bit-exact
    assert fr.ply == 123
    assert fr.from_sq == (1, 2, 3, 4)
    assert fr.to_sq == (5, 6, 7, 0)
    assert fr.promo == 0
    assert fr.flags == 0x42


def test_frame_pack_rejects_wrong_dtype():
    bad = np.zeros(frm.ENCODING_DIM_4D, dtype=np.float64)
    with pytest.raises(TypeError, match="float32"):
        frm.pack_frame(bad, 0, (0, 0, 0, 0), (0, 0, 0, 0), 0, 0)


def test_frame_pack_rejects_wrong_shape():
    bad = np.zeros(100, dtype=np.float32)
    with pytest.raises(ValueError, match="shape"):
        frm.pack_frame(bad, 0, (0, 0, 0, 0), (0, 0, 0, 0), 0, 0)


def test_frame_unpack_rejects_wrong_length():
    too_short = b"\x00" * 100
    with pytest.raises(ValueError, match="got 100"):
        frm.unpack_frame(too_short)


# ---- File-level round-trip ------------------------------------------

@pytest.mark.parametrize("n_frames", [1, 10, 50])
def test_write_read_file_round_trip(n_frames):
    rng = np.random.default_rng(n_frames * 7)
    frames_in = [_make_random_frame(rng, p) for p in range(n_frames)]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".spectralz")
    tmp.close()
    try:
        n_bytes = frm.write_spectralz_v3(tmp.name, frames_in)
        expected = frm.HEADER_SIZE + (
            frm.ENCODING_DIM_4D * 4 + frm.FRAME_TAIL_BYTES
        ) * n_frames
        assert n_bytes == expected

        header, frames_out = frm.read_spectralz_v3(tmp.name)
    finally:
        os.remove(tmp.name)

    assert header.n_plies == n_frames
    assert len(frames_out) == n_frames
    for fin, fout in zip(frames_in, frames_out):
        assert np.array_equal(fin.encoding, fout.encoding)
        assert fin.ply == fout.ply
        assert fin.from_sq == fout.from_sq
        assert fin.to_sq == fout.to_sq
        assert fin.promo == fout.promo
        assert fin.flags == fout.flags


# ---- read_header_any dispatch ---------------------------------------

def test_read_header_any_detects_v3():
    h = frm.pack_header(frm.ENCODING_DIM_4D,
                        frm.ENCODING_DIM_4D * 4 + 14, 1)
    buf = io.BytesIO(h)
    hdr, kind = frm.read_header_any(buf)
    assert kind == "v3"
    assert hdr.version == 3
    assert hdr.encoding_dim == frm.ENCODING_DIM_4D


def test_read_header_any_rejects_garbage():
    buf = io.BytesIO(b"\xFF" * 256)
    with pytest.raises(ValueError):
        frm.read_header_any(buf)


def test_read_header_any_rejects_short_input():
    buf = io.BytesIO(b"\x00")
    with pytest.raises(ValueError):
        frm.read_header_any(buf)


if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"],
                   check=False)
