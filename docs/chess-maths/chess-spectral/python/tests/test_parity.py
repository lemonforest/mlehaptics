"""
Parity tests: Python encoder output must match the C encoder output
for the same .spectral files. Run with `python -m pytest tests/` or
invoke directly.

These tests require:
    - A reference .spectral file produced by the C CLI (we use
      docs/chess-maths/chessgame_1937789.spectral from the Carlsen-
      Caruana WCC 2018 Round 6 cache).
    - A reference .csv produced by the C CLI against that file.

The Carlsen-Caruana fixture is NOT committed to the tree (regenerate
from the corresponding PGN or fetch it from the cache). Tests that
depend on it are auto-skipped when the fixture is absent, so this file
never blocks a local pytest run. Byte-for-byte parity is still enforced
by `test_c_py_parity.py` (Kasparov-Topalov NDJSON, fixture committed).
"""
from __future__ import annotations

import os
import sys
import tempfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG  = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

CHESS_MATHS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
# Reference artifacts (captured from the C encoder) live in docs/chess-maths/.
# fen_to_pos used to live there too but has moved into the chess_spectral
# package — no sys.path gymnastics needed for it anymore.
REF_SPECTRAL = os.path.join(CHESS_MATHS, "chessgame_1937789.spectral")
REF_SPECTRALZ = os.path.join(CHESS_MATHS, "chessgame_1937789.spectralz")
REF_CSV = os.path.join(CHESS_MATHS, "chessgame_1937789.csv")

_FIXTURES_PRESENT = (
    os.path.exists(REF_SPECTRAL)
    and os.path.exists(REF_SPECTRALZ)
    and os.path.exists(REF_CSV)
)
_REQUIRES_FIXTURE = pytest.mark.skipif(
    not _FIXTURES_PRESENT,
    reason=(
        "Carlsen-Caruana fixture absent (chessgame_1937789.spectral[z]/.csv). "
        "Parity is still covered by test_c_py_parity.py — skipping."
    ),
)


@_REQUIRES_FIXTURE
def test_header_round_trip():
    from chess_spectral import read_all, FILE_VERSION, ENCODING_DIM
    hdr, frames = read_all(REF_SPECTRAL)
    assert hdr.version == FILE_VERSION
    assert hdr.encoding_dim == ENCODING_DIM
    assert hdr.n_plies == 161
    assert len(frames) == 161


@_REQUIRES_FIXTURE
def test_plain_and_gz_equal():
    from chess_spectral import read_encodings
    _, arr_plain = read_encodings(REF_SPECTRAL)
    _, arr_gz    = read_encodings(REF_SPECTRALZ)
    assert arr_plain.shape == arr_gz.shape
    assert np.array_equal(arr_plain, arr_gz)


@_REQUIRES_FIXTURE
def test_csv_matches_c_byte_for_byte():
    from chess_spectral import write_csv
    with tempfile.NamedTemporaryFile(
        prefix="py_csv_", suffix=".csv", delete=False, mode="wb"
    ) as f:
        out_path = f.name
    try:
        write_csv(REF_SPECTRAL, out_path)
        with open(out_path, "rb") as f:
            py_bytes = f.read()
        with open(REF_CSV, "rb") as f:
            c_bytes = f.read()
        assert len(py_bytes) == len(c_bytes), (
            f"size differs: py={len(py_bytes)} c={len(c_bytes)}"
        )
        assert py_bytes == c_bytes, "CSV output not byte-identical"
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass


def test_encoder_starting_position_channel_energies():
    """Sanity: encode the starting position and check the 10 channel
    energies match the known reference (derived from the C encoder)."""
    from chess_spectral import encode_640, channel_energies, fen_to_pos

    pos = fen_to_pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    enc = encode_640(pos)
    E = channel_energies(enc)

    expected = {
        "A1":    0.0,       "A2":   19.8450,
        "B1":   45.2825,    "B2":   45.2825,
        "E":   322.5700,
        "F1":   88.7728,    "F2": 1851.0100,
        "F3": 1507.6520,
        "FA":   19.9209,    "FD":    0.0,
    }
    for name, want in expected.items():
        got = E[name]
        assert abs(got - want) < 1e-3, f"{name}: got {got} expected {want}"


def test_empty_board_gives_zero_vector():
    from chess_spectral import encode_640
    enc = encode_640({})
    assert enc.shape == (640,)
    assert np.allclose(enc, 0.0)


if __name__ == "__main__":
    # Allow `python tests/test_parity.py` as a quick smoke-test runner.
    fixture_tests = [
        test_header_round_trip,
        test_plain_and_gz_equal,
        test_csv_matches_c_byte_for_byte,
    ]
    always_tests = [
        test_encoder_starting_position_channel_energies,
        test_empty_board_gives_zero_vector,
    ]
    tests = (fixture_tests if _FIXTURES_PRESENT else []) + always_tests
    if not _FIXTURES_PRESENT:
        print("[SKIP] fixture tests (chessgame_1937789.* absent); "
              "parity covered by test_c_py_parity.py")
    fails = 0
    for t in tests:
        try:
            t()
            print(f"[ OK ] {t.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"[FAIL] {t.__name__}: {e}")
        except Exception as e:
            fails += 1
            print(f"[ERR ] {t.__name__}: {type(e).__name__}: {e}")
    print()
    print("ALL PASSED" if fails == 0 else f"{fails} FAILURE(S)")
    raise SystemExit(0 if fails == 0 else 1)
