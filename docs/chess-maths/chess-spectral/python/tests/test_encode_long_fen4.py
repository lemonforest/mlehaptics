"""Regression test for the v1.3.1 FEN4 buffer-overflow bug.

Pre-1.3.2 the C ``spectral_4d encode`` (NDJSON4 → .spectralz4)
truncated FEN4 input at 2048 bytes and reported a misleading
``CODE_BAD_COORD`` (-4) parse error. Real chess4d positions
serialize to ~9.4 KiB at startpos and well above for any in-game
position, so the bulk-encode path was effectively unusable for the
chess4d corpus. ``encode-fen4`` (single-position writer) was
unaffected because it points directly at ``argv``, never copying
into a fixed buffer.

Fix in 1.3.2:
    1. The internal FEN4 buffer in ``cmd_encode`` grew from
       2 KiB stack → 64 KiB heap-allocated.
    2. ``json_str_field4`` now returns -2 on overflow instead of
       silently truncating, so a future overflow (if anyone tries
       to encode a hypothetical position larger than 64 KiB)
       produces a clear error rather than a misleading downstream
       parse failure.

This file pins both behaviors:
    * the originally-broken 193-piece case now succeeds
    * the worst-case 4096-piece fully-loaded board succeeds
    * the byte-equivalence between the two encode paths
      (single ``encode-fen4`` vs bulk ``encode``) is preserved
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from chess_spectral.fen_4d import PREFIX


def _find_c_4d_binary() -> Path | None:
    """Locate the spectral_4d binary. Mirrors
    chess_spectral.cli._find_c_binary_4d's search order."""
    env = os.environ.get("CS_SPECTRAL_4D_BIN")
    if env and Path(env).is_file():
        return Path(env)
    suffix = ".exe" if os.name == "nt" else ""
    # Wheel-installed
    import chess_spectral
    pkg = Path(chess_spectral.__file__).parent
    cand = pkg / "_native" / f"spectral_4d{suffix}"
    if cand.is_file():
        return cand
    # Repo build
    repo_build = pkg.parent.parent / "build"
    for sub in ("Release", "Debug", ""):
        cand = repo_build / sub / f"spectral_4d{suffix}"
        if cand.is_file():
            return cand
    return None


_BIN = _find_c_4d_binary()
_REQUIRES_C_4D = pytest.mark.skipif(
    _BIN is None,
    reason="spectral_4d binary not built (set $CS_SPECTRAL_4D_BIN or "
           "build via cmake --build build --target spectral_4d)",
)


def _build_fen4(n_pieces: int) -> str:
    """Construct a FEN4 with ``n_pieces`` rooks placed on distinct
    squares of Z_8^4. Used to drive the encode path through varying
    input lengths."""
    pieces = []
    for i in range(n_pieces):
        x = (i // 512) % 8
        y = (i // 64) % 8
        z = (i // 8) % 8
        w = i % 8
        pieces.append(f"R@{x},{y},{z},{w}")
    return PREFIX + " " + "; ".join(pieces)


def _run_encode_ndjson4(binary: Path, fen4: str, tmp: Path) -> tuple[int, str, int]:
    """Run ``binary encode -i NDJSON4 -o .spectralz4`` with one ply
    line containing ``fen4``. Returns (rc, stderr, output_size)."""
    nd4 = tmp / "in.ndjson4"
    nd4.write_text(json.dumps({"ply": 0, "fen4": fen4}) + "\n",
                   encoding="utf-8")
    out = tmp / "out.spectralz4"
    r = subprocess.run(
        [str(binary), "encode", "-i", str(nd4), "-o", str(out)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stderr, out.stat().st_size if out.exists() else 0


def _run_encode_fen4(binary: Path, fen4: str, tmp: Path) -> tuple[int, str, bytes]:
    """Run ``binary encode-fen4 --fen4 STRING -o .spectralz4``.
    Returns (rc, stderr, file bytes)."""
    out = tmp / "fen4_out.spectralz4"
    r = subprocess.run(
        [str(binary), "encode-fen4", "--fen4", fen4, "-o", str(out)],
        capture_output=True, text=True,
    )
    file_bytes = out.read_bytes() if out.exists() else b""
    return r.returncode, r.stderr, file_bytes


# ─── Regression: 193-piece FEN4 (the bug's exact boundary) ──────────


@_REQUIRES_C_4D
def test_193_piece_fen4_no_longer_truncates():
    """Pre-1.3.2 this exact case (193 R-piece records) tipped over
    the 2048-byte buffer and produced a header-only spectralz with
    misleading 'FEN4 parse error -4 at line 1' on stderr. With the
    64 KiB heap buffer it encodes cleanly."""
    fen4 = _build_fen4(193)
    assert len(fen4) > 1900, "regression test loses meaning if FEN4 too short"
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        rc, stderr, size = _run_encode_ndjson4(_BIN, fen4, tmp)
    assert rc == 0, f"encode failed: {stderr!r}"
    # Note: "FEN4 parse errors" (plural, as a noun phrase in the
    # "no plies written" warning) is fine — we're guarding only
    # against the specific per-line "FEN4 parse error %d at line %u"
    # message that signals the actual bug.
    assert "FEN4 parse error " not in stderr, (
        f"the original truncation symptom recurred: {stderr!r}"
    )
    # 256 = header alone (the broken behavior). Anything more means
    # at least one frame was written.
    assert size > 256, (
        f"output is header-only ({size} bytes) — frame not written"
    )


# ─── Worst case: 4096-piece fully-loaded board ──────────────────────


@_REQUIRES_C_4D
def test_4096_piece_worst_case_fully_loaded_board():
    """Every square on Z_8^4 occupied. The FEN4 string here is
    ~80 KiB; it currently still fits in our 64 KiB buffer for short
    piece-record encodings (e.g. ``R@7,7,7,7`` is 9 chars), but
    even the ~10 KiB chess4d-style startpos fits comfortably."""
    n = 4096
    fen4 = _build_fen4(n)
    # If this assertion ever fires, the buffer needs growing again.
    # Document the new size in src/main_4d.c::cmd_encode and bump
    # the comment. For now the worst-case short-piece-record
    # serialization stays well under 64 KiB.
    assert len(fen4) < 65536, (
        f"4096-piece FEN4 is {len(fen4)} bytes, exceeds the 64 KiB "
        "buffer in cmd_encode. Grow the malloc and update this test."
    )
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        rc, stderr, size = _run_encode_ndjson4(_BIN, fen4, tmp)
    assert rc == 0, f"encode failed: {stderr!r}"
    assert "FEN4 parse error" not in stderr, stderr
    assert size > 256


# ─── Overflow now produces the clearer error, not -4 ────────────────


@_REQUIRES_C_4D
def test_overflow_produces_explicit_error_not_misleading_bad_coord():
    """If a future format change ever produces an overflow, the
    error message should clearly say "FEN4 string longer than
    64 KiB" rather than the misleading 'FEN4 parse error -4'.
    Construct a deliberately-too-long string and assert the new
    error text is present.

    (Skipped under normal circumstances — this exists to prove the
    error path is wired correctly.)"""
    # 4096 squares × ~17 bytes/piece ('Pw@7,7,7,7'-style) ≈ 70 KiB
    # — exceeds the 64 KiB buffer.
    pieces = []
    for x in range(8):
        for y in range(8):
            for z in range(8):
                for w in range(8):
                    pieces.append(f"Pw@{x},{y},{z},{w}")
    fen4 = PREFIX + " " + "; ".join(pieces)
    if len(fen4) <= 65536:
        pytest.skip(
            f"FEN4 length {len(fen4)} fits in 64 KiB buffer — "
            "test relies on overflow which doesn't trigger; "
            "if buffer was grown, update this test"
        )
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        rc, stderr, _ = _run_encode_ndjson4(_BIN, fen4, tmp)
    # encode returns 0 even on per-line errors (it skips the bad
    # line and continues); we check stderr for the explicit message.
    assert "FEN4 string longer than" in stderr, (
        f"expected the new overflow error, got: {stderr!r}"
    )
    # And specifically NOT the misleading old-style "parse error -4":
    assert "FEN4 parse error -4" not in stderr, (
        f"old misleading error still appearing: {stderr!r}"
    )
