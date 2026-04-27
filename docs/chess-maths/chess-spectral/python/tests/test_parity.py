"""
Parity tests: Python encoder output must match the C encoder output
for the same .spectral files. Run with `python -m pytest tests/` or
invoke directly.

Two fixture sources are supported (v1.2.4):
  1. **Pre-generated Carlsen-Caruana** at
     docs/chess-maths/chessgame_1937789.{spectral,spectralz,csv}.
     Used preferentially when present (preserves existing dev workflow).
  2. **CI-generated synthetic fixture**: a small NDJSON sequence is
     encoded via the C binary on demand. Triggered when the
     Carlsen-Caruana fixture is absent AND the C binary is locatable.

Either fixture source produces a real assertion; the test no longer
silently skips when the local fixture is missing. (AUDIT inventory #22.)
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG  = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

CHESS_MATHS = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPO_SPECTRAL = Path(os.path.abspath(os.path.join(HERE, "..", "..")))

# Reference artifacts (captured from the C encoder) live in docs/chess-maths/.
REF_SPECTRAL = os.path.join(CHESS_MATHS, "chessgame_1937789.spectral")
REF_SPECTRALZ = os.path.join(CHESS_MATHS, "chessgame_1937789.spectralz")
REF_CSV = os.path.join(CHESS_MATHS, "chessgame_1937789.csv")

_CARLSEN_CARUANA_PRESENT = (
    os.path.exists(REF_SPECTRAL)
    and os.path.exists(REF_SPECTRALZ)
    and os.path.exists(REF_CSV)
)


def _find_c_binary() -> Path | None:
    """Locate the C `spectral` binary for fixture-on-demand generation.
    Mirrors chess_spectral.cli._find_c_binary."""
    env = os.environ.get("CS_SPECTRAL_BIN")
    if env and Path(env).is_file():
        return Path(env)
    suffix = ".exe" if os.name == "nt" else ""
    for sub in ("Release", "Debug", ""):
        cand = REPO_SPECTRAL / "build" / sub / f"spectral{suffix}"
        if cand.is_file():
            return cand
    return None


# A small synthetic NDJSON ply-log used when the Carlsen-Caruana fixture
# is absent. Three plies of a king-pawn opening — gives the parity test
# something concrete to compare even on a fresh CI runner.
_SYNTH_NDJSON = (
    '{"fen":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1","ply":0}\n'
    '{"fen":"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",'
    '"ply":1,"move_from":12,"move_to":28}\n'
    '{"fen":"rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",'
    '"ply":2,"move_from":52,"move_to":36}\n'
)


@pytest.fixture(scope="module")
def parity_fixture(tmp_path_factory):
    """Resolve the parity-test fixture. Returns (spectral_path,
    spectralz_path, csv_path, n_plies) — paths to .spectral/.spectralz/.csv
    files plus the expected ply count."""
    if _CARLSEN_CARUANA_PRESENT:
        return REF_SPECTRAL, REF_SPECTRALZ, REF_CSV, 161

    c_bin = _find_c_binary()
    if c_bin is None:
        pytest.skip(
            "no parity fixture: Carlsen-Caruana absent AND C binary not "
            "found. Build chess-spectral/build/Release/spectral or set "
            "CS_SPECTRAL_BIN."
        )

    tmp = tmp_path_factory.mktemp("synth_parity_fixture")
    nd_path = tmp / "synth.ndjson"
    nd_path.write_text(_SYNTH_NDJSON, encoding="utf-8")
    sp_path = tmp / "synth.spectral"
    spz_path = tmp / "synth.spectralz"
    csv_path = tmp / "synth.csv"
    subprocess.run([str(c_bin), "encode", str(nd_path), "-o", str(sp_path)],
                   check=True, capture_output=True)
    subprocess.run([str(c_bin), "encode", str(nd_path), "-o", str(spz_path), "-z"],
                   check=True, capture_output=True)
    subprocess.run([str(c_bin), "csv", str(sp_path), "-o", str(csv_path)],
                   check=True, capture_output=True)
    return str(sp_path), str(spz_path), str(csv_path), 3


def test_header_round_trip(parity_fixture):
    sp, _, _, n_plies = parity_fixture
    from chess_spectral import read_all, FILE_VERSION, ENCODING_DIM
    hdr, frames = read_all(sp)
    assert hdr.version == FILE_VERSION
    assert hdr.encoding_dim == ENCODING_DIM
    assert hdr.n_plies == n_plies
    assert len(frames) == n_plies


def test_plain_and_gz_equal(parity_fixture):
    sp, spz, _, _ = parity_fixture
    from chess_spectral import read_encodings
    _, arr_plain = read_encodings(sp)
    _, arr_gz    = read_encodings(spz)
    assert arr_plain.shape == arr_gz.shape
    assert np.array_equal(arr_plain, arr_gz)


def test_csv_matches_c_byte_for_byte(parity_fixture):
    sp, _, ref_csv, _ = parity_fixture
    from chess_spectral import write_csv
    with tempfile.NamedTemporaryFile(
        prefix="py_csv_", suffix=".csv", delete=False, mode="wb"
    ) as f:
        out_path = f.name
    try:
        write_csv(sp, out_path)
        with open(out_path, "rb") as f:
            py_bytes = f.read()
        with open(ref_csv, "rb") as f:
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
    energies match the known reference (derived from the C encoder).

    Refreshed 2026-04-25 (v1.2.4): B1 and B2 expected values were stale
    (B1=45.2825 / B2=45.2825 — likely from a pre-PATCH-6 audit version).
    Current C and Python encoders agree on B1=0 / B2=19.8450; the C
    output is the authority and these expected values are derived from
    `spectral encode` + `spectral csv` on the starting FEN. See AUDIT
    inventory item #24b."""
    from chess_spectral import encode_640, channel_energies, fen_to_pos

    pos = fen_to_pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    enc = encode_640(pos)
    E = channel_energies(enc)

    expected = {
        "A1":    0.0,       "A2":   19.8450,
        "B1":    0.0,       "B2":   19.8450,
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
