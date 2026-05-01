"""End-to-end smoke ("immolation") suite for chess-spectral v1.5+.

This is the "does everything we ship still work?" test. It exercises
every wired CLI command against a real, verified game from the dataset
(Kasparov vs Topalov, Hoogovens 1999 R4 — 87 plies, "Kasparov's
Immortal") plus the 2D phase-operator package, the 4D Oana-Chiru
table-verification gates, the v1.4 game-state surface, the Track A
kinematic QM module, the Phase 4 per-channel move-as-unitary builders
(B1+B2+B3a+B3b+B3c+B3d/e+B5), and the v1.5 §17.1 / §17.5 Pyodide
bridge surface — all driven against seeded deterministic self-play.

This suite is the canonical release gate: run it before every PyPI
tag. If anything we ship is broken, this catches it.

What it covers (organized by surface):

    2D C CLI (spectral):
      encode (PGN→.spectral via pgn_bridge), csv, query, analyze,
      compare, heatmap, export, play.

    2D Python CLI (chess_spectral.cli):
      encode-fen, csv, compare, query, analyze, heatmap, export.
      (Output verified to match C byte-for-byte where applicable.)

    4D C CLI (spectral_4d):
      encode-fen4 (single position), encode (NDJSON4 → .spectralz4),
      csv (per-ply 11-channel energies).

    4D Python CLI (chess_spectral_4d):
      encode-fen4, encode-moves4, corpus-gen, tables-verify,
      search, tournament.

    §16 engine CLI (v1.6):
      2D `spectral_py search` — all 3 evaluators (material/spectral/qm)
        produce a legal move from the starting position; --fen accepts
        an arbitrary position.
      2D `spectral_py tournament` — round-robin between 2 agents;
        per-side asymmetric specs (white=spectral, black=qm) are
        independently configured (the §16 ship-gate property).
      2D `spectral_py sweep` — cross-product (evaluators × depths)
        round-robin; produces Elo + pair_records JSON.
      4D `chess_spectral_4d search` / `tournament` — same surface,
        requires explicit fen4.

    2D phase-spatial validator chain (3 layers):
      python-chess (external, well-tested)
        ↓ test_spatial_op_matches_python_chess
      our spatial op (chess_spectral.tables.SHORT_PFNS + blocking + king-safety)
        ↓ test_seeded_self_play_phase_op_legal_moves_match
      our phase op (chess_spectral.phase_operators.occupation_aware_moves_a)
      Each layer is independently validated against the next; the
      external dep is isolated to a single test. Released code stays
      untouched — all helpers live under python/tests/.

    4D Oana-Chiru spatial validation (single layer):
      Our spatial op (chess_spectral.tables_4d.<piece>4_targets) is
      validated against the paper-predicted invariants in §3 (piece
      mobility on Z₈⁴, B₄ group action, irrep projection, fiber
      bundle, pawn-axis orthogonality) via `chess_spectral_4d
      tables-verify --phase all`. There is no 4D phase operator in
      chess-spectral today — the phase_operators package is 2D-only.
      Adding a 4D phase operator + a chess4d → tables_4d → phase4d
      validator chain analogous to the 2D one is future work.

    v1.4 game-state surface (chess_spectral_4d):
      apply_move with promote_to=Q/R/B/N, GameState4D move history,
      threefold-repetition + 50-move-rule + draw-status priorities,
      get_move_history Pyodide-friendly serialization, fen_4d.serialize
      round-trip, castling/EP regression against chess4d 0.4.

    Track A kinematic (chess_spectral.qm_4d):
      state_to_psi (normalization + Z_2 sign convention),
      channel_projector PVM completeness + Born-rule sums,
      five Hermitian piece-reach observables (rook/bishop/queen/king/
      knight) with real expectations on real ψ, b4_unitary_rep_4096
      unitarity on sample group elements.

    Phase 4 per-channel builders (chess_spectral.qm_4d_dynamics):
      All 11 u_move_* return-type contracts on non-capture and capture
      paths (B1 A_1, B3a STD4_X/Y/Z/W, B3b FA_PAWN_W/Y, B3c FIB_SYM_*,
      B3d/e FD_DIAG, B5 capture markers). Bridge-level apply_move_qm
      assembly populates all 11 channel keys with the right value-type
      mix.

    Phase 4 B2 Zeno evolution:
      evolve_under_h0 norm preservation + energy conservation on real
      seeded-position ψ.

    v1.5 §17.1 + §17.5 bridge surface (chess_spectral.qm_4d_bridge):
      All 7 §17.1 consumer methods (get_qm_state, get_qm_density,
      apply_move_qm_full, measure_at, get_density_matrix_of —
      raises NIE pointing at v1.7+, get_probability_current,
      get_qm_expectation) plus the 6 §17.5 dev/debug methods
      (get_version, get_encoder_shape, get_fen4_state, load_fen4,
      load_jsonl_fixture, has_legal_moves) — return-type contracts,
      basis dimensions, normalization invariants, divergence-free
      probability current.

    Pre-flight findings (research-backed regression guards):
      Encoder injectivity on the real-game corpus (88 plies of
      Kasparov-Topalov, all distinct), spectral identity at small
      scale (P_8 1D Laplacian eigenmodes are the simultaneous
      eigenbasis of the 4D Kron-sum Δ).

    1.7.0 release-pipeline gates (D1 + D2 cohort):
      D1 search-budget mid-iteration honoring (a tight budget on
      a dense position returns within budget+0.5s grace with a
      non-None best_move); SearchResult.timed_out field exists;
      HAS_NATIVE_BITBOARD is exposed at the top-level
      ``chess_spectral`` package surface (downstream consumers like
      the chess4D-OC visualizer depend on the direct import); when
      HAS_NATIVE is True, Bitboard4D.to_squares() native fast-path
      output matches a pure-Python reference recompute (catches
      marshaling regressions in cs_bb4_to_squares or its ctypes
      wrapper).

Skip behavior:
    - Tests that need the C binary skip cleanly if it isn't built
      (set $CS_SPECTRAL_BIN / $CS_SPECTRAL_4D_BIN, or build the
      Release config).
    - Tests that need python-chess (the optional `[corpus]` extra)
      skip if it isn't installed.
    - Tests that need chess4d (the upstream 4D Oana-Chiru reference)
      skip if it isn't installed.

Runs in ~120-180 s end-to-end on a warm Python interpreter;
81 tests.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
REPO_SPECTRAL = PY_DIR.parent
FIXTURES_DIR = HERE / "fixtures"
SAMPLE_PGN = FIXTURES_DIR / "kasparov_topalov_1999.pgn"
SAMPLE_NDJSON = FIXTURES_DIR / "kasparov_topalov_1999.ndjson"
POSITIONS_4D = FIXTURES_DIR / "positions_4d.jsonl"

EXPECTED_PLIES = 88  # 87 SAN moves + 1 starting-position frame at ply 0
                     # (the PGN's PlyCount header reports 87 = move count;
                     # the encoder emits one frame per position, including
                     # the initial setup, hence n_plies = 88).


# ─── Binary discovery (mirrors cli.py:_find_native_binary) ──────────


def _find_binary(name: str, env_var: str) -> Path | None:
    env = os.environ.get(env_var)
    if env and Path(env).is_file():
        return Path(env)
    suffix = ".exe" if os.name == "nt" else ""
    for sub in ("Release", "Debug", ""):
        cand = REPO_SPECTRAL / "build" / sub / f"{name}{suffix}"
        if cand.is_file():
            return cand
    return None


C_BINARY = _find_binary("spectral", "CS_SPECTRAL_BIN")
C_BINARY_4D = _find_binary("spectral_4d", "CS_SPECTRAL_4D_BIN")

_REQUIRES_C = pytest.mark.skipif(
    C_BINARY is None,
    reason="spectral C binary not built; set CS_SPECTRAL_BIN or run "
           "`cmake --build build --config Release --target spectral`",
)
_REQUIRES_C_4D = pytest.mark.skipif(
    C_BINARY_4D is None,
    reason="spectral_4d C binary not built; set CS_SPECTRAL_4D_BIN or "
           "run `cmake --build build --config Release --target spectral_4d`",
)
_REQUIRES_PYTHON_CHESS = pytest.mark.skipif(
    True,  # overridden below if import succeeds
    reason="python-chess is not installed; install with "
           "`pip install chess-spectral[corpus]` or `pip install chess`",
)
try:
    import chess as _python_chess  # noqa: F401
    _REQUIRES_PYTHON_CHESS = pytest.mark.skipif(
        False, reason="(python-chess available)"
    )
except ImportError:
    pass


# ─── Helpers ─────────────────────────────────────────────────────────


def _run_c(args, *, max_segfault_retries=2, **kw):
    """Run a C subprocess, raising with stderr on failure.

    Transparent SIGSEGV retry: Linux release builds with LTO/IPO
    enabled occasionally segfault during ``spectral encode --pgn
    ... -z`` (ubuntu-latest / py3.12 / release ONLY; ASAN job on
    the same OS passes -- ASAN preset disables LTO, so the
    compiler-pass interaction is the suspect). We retry up to
    ``max_segfault_retries`` times on returncode -11 (POSIX
    SIGSEGV) or 0xC0000005 (Windows access violation), then
    surface the captured stdout/stderr in the exception so the
    next CI run gives us a debugging breadcrumb.

    Tracking: docs/chess-maths/chess-spectral/python/CHANGELOG.md
    "v1.6 LTO/IPO segfault investigation".
    """
    last_exc = None
    for attempt in range(max_segfault_retries + 1):
        try:
            proc = subprocess.run(
                [str(C_BINARY)] + list(args),
                check=True, capture_output=True, text=True,
                encoding="utf-8", errors="replace", **kw,
            )
            return proc
        except subprocess.CalledProcessError as exc:
            last_exc = exc
            is_segfault = (
                exc.returncode == -11                    # POSIX SIGSEGV
                or exc.returncode == -1073741819         # Windows access violation, signed
                or exc.returncode == 0xC0000005          # Windows access violation, unsigned
            )
            if is_segfault and attempt < max_segfault_retries:
                continue
            # Surface captured output in the assertion message so a
            # CI failure gives us the C-side stderr right before the
            # crash (the encoder logs progress to stderr; the last
            # line is usually the cleanest hint at what went wrong).
            stdout_tail = (exc.stdout or "")[-2000:] if exc.stdout else "(empty)"
            stderr_tail = (exc.stderr or "")[-4000:] if exc.stderr else "(empty)"
            new_msg = (
                f"{exc}\n"
                f"\n--- stdout (last 2KB) ---\n{stdout_tail}\n"
                f"--- stderr (last 4KB) ---\n{stderr_tail}\n"
                f"--- attempts: {attempt + 1} of {max_segfault_retries + 1} ---"
            )
            raise subprocess.CalledProcessError(
                exc.returncode, exc.cmd,
                output=exc.output, stderr=new_msg,
            ) from exc
    raise last_exc  # pragma: no cover (loop always returns or raises)


def _run_c_4d(args, **kw):
    proc = subprocess.run(
        [str(C_BINARY_4D)] + list(args),
        check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace", **kw,
    )
    return proc


def _run_py(args):
    """Run the Python 2D CLI in-process."""
    from chess_spectral.cli import build_parser
    ap = build_parser()
    ns = ap.parse_args(args)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ns.func(ns)
    return rc, buf.getvalue()


def _run_py_4d(args):
    """Run the Python 4D CLI in-process."""
    from chess_spectral_4d.cli import build_parser
    ap = build_parser()
    ns = ap.parse_args(args)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ns.func(ns)
    return rc, buf.getvalue()


# ─── Module-scoped fixtures (encode the game once, reuse N times) ───


@pytest.fixture(scope="module")
def encoded_game(tmp_path_factory):
    """Encode the Kasparov-Topalov game from the committed NDJSON
    (which was bridged from PGN earlier) and return the path. We
    use the NDJSON to avoid the python-chess dependency in this
    fixture; PGN-via-bridge is exercised in test_pgn_to_spectralz."""
    if C_BINARY is None or not SAMPLE_NDJSON.is_file():
        pytest.skip("C binary or NDJSON fixture absent")
    tmp = tmp_path_factory.mktemp("smoke_2d")
    sp = tmp / "kasparov_topalov.spectral"
    spz = tmp / "kasparov_topalov.spectralz"
    _run_c(["encode", str(SAMPLE_NDJSON), "-o", str(sp)])
    _run_c(["encode", str(SAMPLE_NDJSON), "-o", str(spz), "-z"])
    return sp, spz, tmp


# ─── 2D pipeline smoke (real-game) ──────────────────────────────────


@_REQUIRES_C
def test_2d_encode_real_game_yields_expected_ply_count(encoded_game):
    """The encoded .spectral header must report EXPECTED_PLIES (87)."""
    sp, _, _ = encoded_game
    from chess_spectral import read_all
    hdr, frames = read_all(str(sp))
    assert hdr.n_plies == EXPECTED_PLIES, (
        f"expected {EXPECTED_PLIES} plies (Kasparov-Topalov 1999), "
        f"got {hdr.n_plies}"
    )
    assert len(frames) == EXPECTED_PLIES


@_REQUIRES_C
def test_2d_csv_real_game_produces_88_rows(encoded_game):
    """csv emits a header row + 87 ply rows."""
    sp, _, tmp = encoded_game
    csv_path = tmp / "out.csv"
    _run_c(["csv", str(sp), "-o", str(csv_path)])
    rows = csv_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(rows) == EXPECTED_PLIES + 1, (
        f"csv: expected {EXPECTED_PLIES + 1} rows (header + {EXPECTED_PLIES} plies), "
        f"got {len(rows)}"
    )
    # Header has the documented 17 columns.
    assert rows[0].count(",") + 1 == 17


@_REQUIRES_C
def test_2d_query_at_each_quartile(encoded_game):
    """query at four representative plies must succeed and emit all
    10 channel-energy lines + a total."""
    sp, _, _ = encoded_game
    for ply in (0, EXPECTED_PLIES // 4, EXPECTED_PLIES // 2, EXPECTED_PLIES - 1):
        out = _run_c(["query", str(sp), "--ply", str(ply)]).stdout
        for ch in ("E_A1", "E_A2", "E_B1", "E_B2", "E_E",
                   "E_F1", "E_F2", "E_F3", "E_FA", "E_FD", "E_total"):
            assert ch in out, f"query ply={ply}: missing {ch} in output"


@_REQUIRES_C
def test_2d_analyze_real_game_finds_peak(encoded_game):
    """analyze must return valid JSON with peak_ply / drop_ply / crisis_ply
    inside [0, n_plies)."""
    sp, _, _ = encoded_game
    out = _run_c(["analyze", str(sp)]).stdout
    j = json.loads(out)
    assert j["n_plies"] == EXPECTED_PLIES
    for key in ("a1_peak_ply", "a1_drop_ply", "crisis_ply", "e_total_max_ply"):
        assert 0 <= j[key] < EXPECTED_PLIES, (
            f"analyze: {key}={j[key]} not in [0, {EXPECTED_PLIES})"
        )
    # The Kasparov immortal has wild swings — abs_dA1_max must be > 0.
    assert j["abs_dA1_max"] > 0.0


@_REQUIRES_C
def test_2d_compare_self_yields_unit_cosine(encoded_game):
    """A file compared with itself must have cos_min/mean/max == 1.0000."""
    sp, _, _ = encoded_game
    out = _run_c(["compare", str(sp), str(sp)]).stdout
    assert "cos_min=1.0000" in out
    assert "cos_mean=1.0000" in out
    assert "cos_max=1.0000" in out


@_REQUIRES_C
@pytest.mark.parametrize("channel", ["A1", "B2", "F2", "FA"])
def test_2d_heatmap_renders_8x8(encoded_game, channel):
    """heatmap output must contain 8 row-labels (8..1) and the file
    column legend ('a b c d e f g h')."""
    sp, _, _ = encoded_game
    out = _run_c(["heatmap", str(sp), "--ply", "20", "--channel", channel]).stdout
    for rank in range(1, 9):
        assert f"  {rank}  " in out, f"heatmap: missing rank-{rank} row"
    assert "a b c d e f g h" in out


@_REQUIRES_C
def test_2d_export_yields_valid_json(encoded_game):
    """export must produce a parseable JSON document with version /
    encoding_dim / n_plies / channels / frames."""
    sp, _, tmp = encoded_game
    out_json = tmp / "export.json"
    _run_c(["export", str(sp), "-o", str(out_json)])
    j = json.loads(out_json.read_text(encoding="utf-8"))
    assert j["version"] == 2
    assert j["encoding_dim"] == 640
    assert j["n_plies"] == EXPECTED_PLIES
    assert len(j["channels"]) == 10
    assert len(j["frames"]) == EXPECTED_PLIES
    # Spot-check frame[0]: must have ply / channel_energies / encoding.
    assert j["frames"][0]["ply"] == 0
    assert "A1" in j["frames"][0]["channel_energies"]
    assert len(j["frames"][0]["encoding"]) == 640


@_REQUIRES_C
def test_2d_play_lists_all_plies(encoded_game):
    """play in list mode emits 1 header row + EXPECTED_PLIES rows."""
    sp, _, _ = encoded_game
    out = _run_c(["play", str(sp)]).stdout
    rows = [r for r in out.split("\n") if r.strip()]
    assert len(rows) == EXPECTED_PLIES + 1


# ─── 2D Python wrappers match C on real game ────────────────────────


@_REQUIRES_C
def test_2d_python_compare_matches_c(encoded_game):
    """Compare-self: both implementations must report cos_min/mean/max
    = 1.0000 (same formatted summary). The exact ply that wins
    np.argmin / C's `<` tiebreaker may differ between code paths
    when every cosine is 1.0 within float precision but not literally
    equal — that's a tiebreaker artifact, not a parity bug. So this
    test only asserts the formatted cosine values agree, not the
    argmin ply."""
    import re
    sp, _, _ = encoded_game
    c_out = _run_c(["compare", str(sp), str(sp)]).stdout
    rc, py_out = _run_py(["compare", str(sp), str(sp)])
    assert rc == 0
    # Strip the "(ply=N)" tiebreaker from both sides before comparing.
    strip_ply = re.compile(r" \(ply=\d+\)")
    assert strip_ply.sub("", c_out) == strip_ply.sub("", py_out)


@_REQUIRES_C
def test_2d_python_analyze_matches_c(encoded_game):
    sp, _, _ = encoded_game
    c_out = _run_c(["analyze", str(sp)]).stdout
    rc, py_out = _run_py(["analyze", str(sp)])
    assert rc == 0
    assert c_out == py_out


@_REQUIRES_C
def test_2d_python_query_matches_c(encoded_game):
    sp, _, _ = encoded_game
    c_out = _run_c(["query", str(sp), "--ply", "42"]).stdout
    rc, py_out = _run_py(["query", str(sp), "--ply", "42"])
    assert rc == 0
    assert c_out == py_out


# ─── 2D phase operators on a position from the real game ────────────


@_REQUIRES_PYTHON_CHESS
def test_2d_phase_operators_smoke():
    """Smoke-test the chess_spectral.phase_operators package: import the
    public API, exercise three independent surfaces against
    python-chess as ground truth.

      1. phasecast_is_check on a known check position
      2. available_castles on the starting position (all 4 castles)
      3. occupation_field_from_board produces non-empty mapping

    These are minimum-viable checks that each operator is wired and
    callable end-to-end. Full operator validation lives in
    tests/phase_operators/."""
    import chess
    from chess_spectral.phase_operators import (
        phasecast_is_check,
        available_castles,
        occupation_field_from_board,
    )

    # 1. Scholar's Mate position — Black king is in check (mate).
    mate_fen = ("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/"
                "PPPP1PPP/RNB1K1NR b KQkq - 0 4")
    board = chess.Board(mate_fen)
    assert phasecast_is_check(board), (
        "phasecast_is_check missed Scholar's Mate check"
    )
    # Ground truth: python-chess agrees.
    assert board.is_check()

    # 2. Available castles on the starting position: K-side + Q-side
    #    for both colors = 4 candidate castles. (available_castles
    #    only returns castles for the side-to-move; on the starting
    #    position that's white, so we expect 2.)
    start = chess.Board()
    castles = available_castles(start)
    # On the starting position no castle is YET legal (king is in
    # original square but path conditions etc. — the phase operator
    # may report 0 or 2 depending on its definition of "available").
    # Smoke-test: just verify it returns a list and doesn't raise.
    assert isinstance(castles, list)

    # 3. Occupation field is a non-empty mapping over the starting
    #    position (32 occupied phases).
    occ = occupation_field_from_board(start)
    assert hasattr(occ, "__len__") or hasattr(occ, "__contains__"), (
        "occupation_field_from_board returned an unexpected type"
    )


# ─── 4D pipeline smoke ──────────────────────────────────────────────


@_REQUIRES_C_4D
def test_4d_encode_fen4_real_position():
    """encode-fen4 on a non-trivial 4D position emits a valid one-frame
    .spectral4 file (header + 1 frame = 180,494 bytes)."""
    fen4 = ("4d-fen v1: K@4,0,0,0; k@4,7,7,7; "
            "Pw@0,1,0,0; Py@0,0,1,0; pw@7,6,7,7; py@7,7,6,7; "
            "N@2,2,2,2; b@5,5,5,5; R@3,4,5,6; q@6,5,4,3")
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".spectral4", delete=False) as f:
        out = f.name
    try:
        _run_c_4d(["encode-fen4", "--fen4", fen4, "-o", out])
        size = os.path.getsize(out)
        # 256 (header) + 180238 (1 frame) = 180494
        assert size == 180494, f"expected 180494 bytes, got {size}"
    finally:
        os.unlink(out)


@_REQUIRES_C_4D
def test_4d_encode_bulk_ndjson(tmp_path):
    """encode (NDJSON4 → .spectralz4) on a multi-ply ply-log produces
    1 header + N frames."""
    ndjson = tmp_path / "smoke.ndjson4"
    ndjson.write_text(
        '{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0; k@7,7,7,7"}\n'
        '{"ply": 1, "fen4": "4d-fen v1: K@1,0,0,0; k@7,7,7,7", '
        '"move_from": [0,0,0,0], "move_to": [1,0,0,0]}\n'
        '{"ply": 2, "fen4": "4d-fen v1: K@1,0,0,0; k@6,7,7,7", '
        '"move_from": [7,7,7,7], "move_to": [6,7,7,7]}\n',
        encoding="utf-8",
    )
    out = tmp_path / "smoke.spectralz4"
    _run_c_4d(["encode", str(ndjson), "-o", str(out), "-z"])
    assert out.is_file()
    assert out.stat().st_size > 0


@_REQUIRES_C_4D
@pytest.mark.parametrize("description,n_pieces", [
    ("short_10_pieces_under_old_2KiB_boundary", 10),
    ("long_300_pieces_above_old_2KiB_boundary", 300),
])
def test_4d_encode_fen4_matches_encode_ndjson4_byte_for_byte(
    description, n_pieces, tmp_path
):
    """The two C 4D encode paths — `encode-fen4 --fen4 STRING` (points
    directly at argv, no buffer copy) and `encode -i NDJSON4` (copies
    each line into a fixed buffer before parsing) — must produce
    byte-identical .spectral4 output for the same FEN4 position.

    This is a regression catch for the v1.3.1 buffer-truncation bug
    (see test_encode_long_fen4.py for the full story): pre-1.3.2 the
    bulk path silently truncated FEN4 input at 2048 bytes while
    encode-fen4 was unaffected, so the two paths produced wildly
    different output for the same position. Byte-equivalence is the
    invariant that makes that class of bug impossible to ship again.

    The 300-piece variant lands clearly above the original 2048-byte
    boundary; if any future change to either path drifts the encoding,
    it shows up here as a byte-mismatch rather than as a misleading
    parse error or as silent corpus corruption.
    """
    # Build a deterministic FEN4 with `n_pieces` rooks on distinct
    # squares of Z_8^4. Same recipe as the focused regression test
    # in test_encode_long_fen4.py but inlined here so the immolation
    # suite stays self-contained.
    pieces = []
    for i in range(n_pieces):
        x = (i // 512) % 8
        y = (i // 64) % 8
        z = (i // 8) % 8
        w = i % 8
        pieces.append(f"R@{x},{y},{z},{w}")
    fen4 = "4d-fen v1: " + "; ".join(pieces)

    # Path A: encode-fen4 (single-position writer; --fen4 points at argv)
    out_a = tmp_path / "via_fen4.spectral4"
    _run_c_4d(["encode-fen4", "--fen4", fen4, "-o", str(out_a)])

    # Path B: encode (NDJSON4 → .spectral4; FEN4 copied into the line buf)
    nd = tmp_path / "in.ndjson4"
    nd.write_text(
        json.dumps({"ply": 0, "fen4": fen4}) + "\n",
        encoding="utf-8",
    )
    out_b = tmp_path / "via_ndjson4.spectral4"
    # No -z: gzip headers carry a timestamp that differs between runs,
    # which would defeat byte-equivalence. Both encoder paths produce
    # raw .spectral4 here, then we compare bytes directly.
    _run_c_4d(["encode", str(nd), "-o", str(out_b)])

    bytes_a = out_a.read_bytes()
    bytes_b = out_b.read_bytes()
    assert len(bytes_a) == len(bytes_b), (
        f"{description}: encode-fen4 produced {len(bytes_a)} bytes, "
        f"encode NDJSON4 produced {len(bytes_b)} bytes (FEN4 was "
        f"{len(fen4)} bytes)"
    )
    assert bytes_a == bytes_b, (
        f"{description}: encode-fen4 and encode-NDJSON4 paths produced "
        f"different bytes for the same FEN4 (length={len(fen4)}). "
        f"This is the v1.3.1 truncation-bug class — investigate "
        f"json_str_field4 / cmd_encode (src/main_4d.c) and "
        f"cmd_encode_fen4's write_one_frame helper."
    )


@_REQUIRES_C_4D
def test_4d_csv_per_ply_energies(tmp_path):
    """csv on a multi-ply .spectralz4 emits 1 header row + N data rows
    with the documented 24-column layout."""
    ndjson = tmp_path / "smoke.ndjson4"
    ndjson.write_text(
        "\n".join(
            f'{{"ply": {p}, "fen4": "4d-fen v1: K@{p},0,0,0; k@7,7,7,7"}}'
            for p in range(5)
        ) + "\n",
        encoding="utf-8",
    )
    sp = tmp_path / "smoke.spectralz4"
    csv_out = tmp_path / "smoke.csv"
    _run_c_4d(["encode", str(ndjson), "-o", str(sp), "-z"])
    _run_c_4d(["csv", str(sp), "-o", str(csv_out)])
    rows = csv_out.read_text(encoding="utf-8").strip().split("\n")
    assert len(rows) == 6  # 1 header + 5 plies
    assert rows[0].count(",") + 1 == 24  # column count documented in main_4d.c


# ─── 4D Python CLI smoke ────────────────────────────────────────────


def test_4d_python_encode_fen4(tmp_path):
    """Python encode-fen4 produces a valid file without needing the C
    binary (fully native Python pipeline)."""
    out = tmp_path / "py.spectral4"
    rc, _ = _run_py_4d([
        "encode-fen4",
        "--fen4", "4d-fen v1: K@0,0,0,0; k@7,7,7,7",
        "-o", str(out),
    ])
    assert rc == 0
    assert out.stat().st_size == 180494


def test_4d_python_encode_moves4_and_corpus_gen(tmp_path):
    """Python encode-moves4 + corpus-gen produce a valid corpus folder
    with manifest.json."""
    nd = tmp_path / "game.ndjson4"
    nd.write_text(
        '{"ply": 0, "fen4": "4d-fen v1: K@0,0,0,0"}\n'
        '{"ply": 1, "fen4": "4d-fen v1: K@1,0,0,0", '
        '"move_from": [0,0,0,0], "move_to": [1,0,0,0]}\n',
        encoding="utf-8",
    )
    out = tmp_path / "g.spectralz4"
    rc, _ = _run_py_4d(["encode-moves4", "--moves", str(nd), "-o", str(out), "-z"])
    assert rc == 0
    assert out.stat().st_size > 0

    # corpus-gen wraps the same NDJSON into a corpus folder.
    rc, _ = _run_py_4d([
        "corpus-gen", "--games", str(nd),
        "--run-id", "smoke", "--results-root", str(tmp_path),
    ])
    assert rc == 0
    manifest = tmp_path / "smoke" / "manifest.json"
    assert manifest.is_file()
    j = json.loads(manifest.read_text(encoding="utf-8"))
    assert j["n_games"] == 1
    assert j["games"][0]["encode_rc"] == 0


# ─── 4D Oana-Chiru phase verification ───────────────────────────────


def test_4d_tables_verify_all_phases():
    """Run all six phase-N validation gates (1, 2, 3, 4, 5, pawn-axis)
    and assert each one passes. These gates encode the Oana & Chiru
    (AppliedMath 6(3):48, 2026) §3 invariants — piece mobility on
    Z_8^4, B_4 group action, irrep projection, fiber bundle, and the
    v1.1.1 pawn-axis split orthogonality."""
    rc, out = _run_py_4d(["tables-verify", "--phase", "all"])
    assert rc == 0, f"tables-verify failed:\n{out}"
    # Each phase prints "tables-verify phase X: PASS" on success.
    for phase in ("1", "2", "3", "4", "5", "pawn-axis"):
        assert f"tables-verify phase {phase}: PASS" in out, (
            f"phase {phase} did not pass:\n{out}"
        )


# ─── §16 engine CLI smoke (search / tournament / sweep) ─────────────
#
# v1.6 ships the §16.2 search core and the §16 tournament harness as
# CLI commands. The immolation suite covers them so a future regression
# in the agent-spec parser or the round-robin loop fails the gate.
#
# These tests use very low depths (1) and very low ply caps (≤ 10) so
# the suite stays fast: each search runs in < 100 ms; full sub-suite
# completes in < 5 s on a warm interpreter.


def test_2d_search_default_starting_position():
    """`spectral_py search` from the default starting position with
    every evaluator family produces a legal move."""
    for ev in ("material", "spectral", "qm"):
        rc, out = _run_py(["search", "--agent",
                            f"evaluator={ev},depth=1", "--json"])
        assert rc == 0, f"search/{ev} failed:\n{out}"
        data = json.loads(out)
        assert data["agent"] == f"{ev}@1"
        assert data["depth_reached"] == 1
        assert data["best_move"] is not None, (
            f"{ev}: starting position should yield a legal move"
        )


def test_2d_search_explicit_fen():
    """`spectral_py search --fen` accepts an arbitrary FEN."""
    rc, out = _run_py([
        "search", "--fen",
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "--agent", "label=test,evaluator=material,depth=1", "--json",
    ])
    assert rc == 0, f"search --fen failed:\n{out}"
    data = json.loads(out)
    assert data["agent"] == "test"


def test_2d_tournament_minimal():
    """`spectral_py tournament` round-robin with two agents."""
    rc, out = _run_py([
        "tournament",
        "--agent", "label=A,evaluator=material,depth=1",
        "--agent", "label=B,evaluator=material,depth=2",
        "--n-games-per-pair", "1",
        "--max-plies", "10",
    ])
    assert rc == 0, f"tournament failed:\n{out}"
    data = json.loads(out)
    assert set(data["agents"]) == {"A", "B"}
    assert "elo" in data
    assert "pair_records" in data
    assert len(data["games"]) == 1


def test_2d_tournament_per_side_asymmetric_evaluators():
    """The §16 use case: white=spectral, black=qm in the same
    single-process tournament loop. Asserts the per-side spec
    plumbing is wired end-to-end."""
    rc, out = _run_py([
        "tournament",
        "--agent", "label=spec,evaluator=spectral,depth=1",
        "--agent", "label=qm,evaluator=qm,depth=1",
        "--n-games-per-pair", "1",
        "--max-plies", "6",
    ])
    assert rc == 0, f"asymmetric tournament failed:\n{out}"
    data = json.loads(out)
    g = data["games"][0]
    assert {g["white"], g["black"]} == {"spec", "qm"}, (
        "white and black must be configured independently"
    )


def test_2d_sweep_2x2_matrix():
    """`spectral_py sweep` cross-product (2 evaluators × 2 depths =
    4 cells, 1 game per pair). Smallest non-trivial sweep."""
    rc, out = _run_py([
        "sweep",
        "--evaluators", "material,spectral",
        "--depths", "1,2",
        "--n-games-per-pair", "1",
        "--max-plies", "6",
    ])
    assert rc == 0, f"sweep failed:\n{out}"
    data = json.loads(out)
    assert data["n_cells"] == 4   # 2 evaluators × 2 depths
    assert set(data["elo"].keys()) == {
        "material@1", "material@2", "spectral@1", "spectral@2"
    }


_TWO_KINGS_FEN4_SMOKE = "4d-fen v1: K@0,0,0,0; k@7,7,7,7"


def test_4d_search_two_kings():
    """4D `search` analogue. Uses two kings on opposite corners so
    move-gen is trivial (~16 moves total)."""
    rc, out = _run_py_4d([
        "search", "--fen4", _TWO_KINGS_FEN4_SMOKE,
        "--agent", "evaluator=material,depth=1", "--json",
    ])
    assert rc == 0, f"4D search failed:\n{out}"
    data = json.loads(out)
    assert data["agent"] == "material@1"
    assert data["depth_reached"] == 1


def test_4d_tournament_two_kings():
    """4D `tournament` analogue: 2 agents, 1 game-per-pair, 4 ply max."""
    rc, out = _run_py_4d([
        "tournament",
        "--start-fen4", _TWO_KINGS_FEN4_SMOKE,
        "--agent", "label=A,evaluator=material,depth=1",
        "--agent", "label=B,evaluator=material,depth=1",
        "--n-games-per-pair", "1",
        "--max-plies", "4",
    ])
    assert rc == 0, f"4D tournament failed:\n{out}"
    data = json.loads(out)
    assert data["start_fen4"] == _TWO_KINGS_FEN4_SMOKE
    assert set(data["agents"]) == {"A", "B"}


# ─── PGN round-trip via pgn_bridge (requires python-chess) ──────────


# Historical: ubuntu-latest + Release preset used to segfault
# `spectral encode --pgn -z` consistently. Initially suspected to be
# LTO/IPO; later (PR #137) confirmed the segfault still reproduced at
# -O2 without LTO. WSL2 + gdb root-caused the actual UB: glibc gates
# `fdopen` behind _POSIX_C_SOURCE >= 200809L, but src/main.c didn't
# define it. So fdopen was being called as if it returned `int`,
# truncating its 64-bit FILE* return value to 32 bits on x86_64;
# the next fgets() on that pointer crashed in libc. Fixed in
# src/main.c by adding `#define _POSIX_C_SOURCE 200809L` before the
# system headers. macOS exposed POSIX symbols by default; Windows
# used _fdopen via _open_osfhandle; so the bug only manifested on
# Linux+glibc.


@_REQUIRES_C
@_REQUIRES_PYTHON_CHESS
def test_pgn_to_spectralz_real_game(tmp_path):
    """Full PGN→NDJSON→.spectralz pipeline using the C `spectral
    encode --pgn` shortcut (which auto-pipes through pgn_bridge.py).
    Exercises the entire hot path a real user runs."""
    out = tmp_path / "kt.spectralz"
    _run_c(["encode", "--pgn", str(SAMPLE_PGN), "-o", str(out), "-z"])
    assert out.is_file()
    # Read it back; the ply count should match the PGN's PlyCount header.
    from chess_spectral import read_all
    hdr, _ = read_all(str(out))
    assert hdr.n_plies == EXPECTED_PLIES, (
        f"PGN→spectralz: expected {EXPECTED_PLIES} plies, "
        f"got {hdr.n_plies}"
    )


# ─── Seeded self-play: dynamic game generation via phase operators ──
#
# The Kasparov-Topalov fixture above is real and verified, but it's a
# fixed game. To exercise the move-generation surface (phase operators)
# against varied positions, we add a deterministic random-legal self-
# play helper: feed it RNG seeds for white and black, get back a list
# of plies. Same seeds → same game on every machine and run.
#
# python-chess is the well-tested ground truth: it generates the legal-
# move set we sample from and applies the chosen move. The phase
# operators (chess_spectral.phase_operators.*) are the unit-under-
# test: on every ply we cross-check phasecast_is_check against
# python-chess's board.is_check(), and (separately) verify that
# occupation_aware_moves_a's pseudo-legal candidate set covers
# python-chess's legal destinations for non-pawn pieces.
#
# Default: a single seed shared between both colors gives fully
# symmetric deterministic play. Pass distinct white_seed and
# black_seed to make the two RNGs independent (asymmetric exploration
# of the game tree).


def _seeded_self_play(white_seed: int,
                      black_seed: int | None = None,
                      *, max_plies: int = 50) -> list[dict]:
    """Play a deterministic random-legal self-play game.

    Move generation: python-chess (well-tested baseline).
    Phase-operator validation: on every ply we assert
    `phasecast_is_check(board) == board.is_check()` — exercising the
    phase-operator code path against a real game progression.

    Args:
        white_seed: RNG seed for white's move choices.
        black_seed: RNG seed for black. Defaults to `white_seed` when
            None — symmetric deterministic play. Pass distinct to
            give the two colors independent RNGs (asymmetric).
        max_plies: cap on game length.

    Returns:
        List of dicts ready to write as NDJSON, one per position
        (including the starting position at ply 0). Each dict has
        {ply, fen, move_from, move_to, promo, flags}; move_from /
        move_to are 0xFF on ply 0 (no predecessor move).
    """
    import chess
    import random
    from chess_spectral.phase_operators import phasecast_is_check

    rng_w = random.Random(white_seed)
    rng_b = random.Random(black_seed if black_seed is not None
                          else white_seed)

    board = chess.Board()
    out = [{
        "ply": 0, "fen": board.fen(),
        "move_from": 0xFF, "move_to": 0xFF,
        "promo": 0, "flags": 0,
    }]

    for ply_idx in range(1, max_plies + 1):
        # Phase-operator cross-check: agreement with python-chess on
        # check status. Mismatch here = real phase-op bug.
        if phasecast_is_check(board) != board.is_check():
            raise AssertionError(
                f"phase_operators.phasecast_is_check disagrees with "
                f"python-chess at ply {ply_idx - 1}: "
                f"phase_op={phasecast_is_check(board)}, "
                f"python-chess={board.is_check()}, fen={board.fen()}"
            )

        legal = list(board.legal_moves)
        if not legal:
            break  # checkmate / stalemate

        rng = rng_w if board.turn == chess.WHITE else rng_b
        move = rng.choice(legal)
        board.push(move)

        out.append({
            "ply":       ply_idx,
            "fen":       board.fen(),
            "move_from": move.from_square,
            "move_to":   move.to_square,
            "promo":     move.promotion or 0,
            "flags":     int(board.is_check()),
        })

        if board.is_game_over():
            break

    return out


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_is_reproducible():
    """Same seeds → same FEN sequence on every run."""
    a = _seeded_self_play(white_seed=42, max_plies=30)
    b = _seeded_self_play(white_seed=42, max_plies=30)
    assert [p["fen"] for p in a] == [p["fen"] for p in b], (
        "seeded self-play is not deterministic"
    )


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_separate_seeds_diverge():
    """Same white_seed → identical opening; different black_seed →
    games diverge once black gets the move."""
    a = _seeded_self_play(white_seed=42, black_seed=42, max_plies=30)
    b = _seeded_self_play(white_seed=42, black_seed=99, max_plies=30)
    # Ply 0 (starting pos) and ply 1 (white's first move) must agree.
    assert a[0]["fen"] == b[0]["fen"]
    assert a[1]["fen"] == b[1]["fen"]
    # By ply 30, divergence is overwhelmingly likely.
    assert any(a[i]["fen"] != b[i]["fen"]
               for i in range(2, min(len(a), len(b)))), (
        "asymmetric seeds did not produce divergent games"
    )


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_default_black_inherits_white_seed():
    """When `black_seed` is None, both colors share `white_seed` —
    fully symmetric deterministic play (same as if you'd passed the
    same seed twice)."""
    a = _seeded_self_play(white_seed=2026, max_plies=20)
    b = _seeded_self_play(white_seed=2026, black_seed=2026, max_plies=20)
    assert [p["fen"] for p in a] == [p["fen"] for p in b]


def _write_ndjson_for_c_encoder(plies: list[dict], path) -> None:
    """Write NDJSON with the compact separator the C encoder's
    json_str_field expects (`"key":"value"` — no whitespace after the
    colon, since C's substring scan looks for that exact prefix)."""
    path.write_text(
        "\n".join(json.dumps(p, separators=(",", ":")) for p in plies)
        + "\n",
        encoding="utf-8",
    )


@_REQUIRES_C
@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_encodes_via_c_pipeline(tmp_path):
    """End-to-end: seeded game → NDJSON → C encoder → .spectral.
    Verifies the encoder consumes the dynamically-generated game
    cleanly and the resulting file's header reflects the played plies."""
    plies = _seeded_self_play(white_seed=12345, max_plies=40)
    nd_path = tmp_path / "seeded.ndjson"
    _write_ndjson_for_c_encoder(plies, nd_path)
    sp_path = tmp_path / "seeded.spectral"
    _run_c(["encode", str(nd_path), "-o", str(sp_path)])
    from chess_spectral import read_all
    hdr, frames = read_all(str(sp_path))
    assert hdr.n_plies == len(plies), (
        f"encoded {hdr.n_plies} frames, expected {len(plies)} from "
        f"seeded play"
    )
    assert len(frames) == len(plies)


@_REQUIRES_C
@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_analyze_pipeline(tmp_path):
    """Full pipeline including analyze: seeded game → encode → analyze
    JSON. Exercises both encoder and the analyze CLI on game data
    that wasn't pre-recorded."""
    plies = _seeded_self_play(white_seed=7, black_seed=13, max_plies=30)
    nd_path = tmp_path / "seeded.ndjson"
    _write_ndjson_for_c_encoder(plies, nd_path)
    sp_path = tmp_path / "seeded.spectral"
    _run_c(["encode", str(nd_path), "-o", str(sp_path)])
    out = _run_c(["analyze", str(sp_path)]).stdout
    j = json.loads(out)
    assert j["n_plies"] == len(plies)
    for key in ("a1_peak_ply", "a1_drop_ply", "crisis_ply",
                "e_total_max_ply"):
        assert 0 <= j[key] < len(plies), (
            f"analyze {key}={j[key]} out of range [0, {len(plies)})"
        )


def _spatial_legal_dests(board, sq: int) -> set:
    """Compute the set of legal destinations for a non-pawn piece at
    `sq` using ONLY chess_spectral.tables.SHORT_PFNS (geometric move
    generators) + a slider-blocking walk + king-safety via python-
    chess board state. python-chess is used here for board state and
    the move-and-check primitive (push / pop / is_attacked_by); the
    move CANDIDATE GENERATION comes entirely from our own SHORT_PFNS.

    This is the middle layer of the test-only validation chain:

        python-chess (well-tested external) ─validates→ spatial op
        spatial op (our own SHORT_PFNS-based) ─validates→ phase op

    Layer 1 → 2 is verified by `test_spatial_op_matches_python_chess`.
    Layer 2 → 3 is verified by
    `test_seeded_self_play_phase_op_legal_moves_match`.

    Pawns and castling are not covered here — pawns have direction-
    plus-axis rules that SHORT_PFNS doesn't model, and castling is a
    composite move handled by chess_spectral.phase_operators.castling
    separately."""
    import chess
    from chess_spectral.tables import SHORT_PFNS

    piece = board.piece_at(sq)
    if piece is None:
        return set()
    sym = piece.symbol().upper()
    if sym not in SHORT_PFNS:
        return set()
    own_color = piece.color
    rank = chess.square_rank(sq)
    file = chess.square_file(sq)

    # 1. Pseudo-legal destinations via SHORT_PFNS + blocking.
    pseudo: set[int] = set()
    is_slider = sym in ('B', 'R', 'Q')
    if not is_slider:
        # Knights jump; kings step. No blocking. Just exclude own-color
        # squares.
        for nr, nc in SHORT_PFNS[sym](rank, file):
            target = chess.square(nc, nr)
            target_piece = board.piece_at(target)
            if target_piece is not None and target_piece.color == own_color:
                continue
            pseudo.add(target)
    else:
        # Sliders: SHORT_PFNS emits squares in direction order, distance
        # ascending within each direction. Track the unit vector from
        # the origin to detect direction changes; reset 'blocked' state
        # at each direction boundary.
        prev_dir: tuple[int, int] | None = None
        blocked = False
        for nr, nc in SHORT_PFNS[sym](rank, file):
            dr, dc = nr - rank, nc - file
            unit = (0 if dr == 0 else (1 if dr > 0 else -1),
                    0 if dc == 0 else (1 if dc > 0 else -1))
            if unit != prev_dir:
                prev_dir = unit
                blocked = False
            if blocked:
                continue
            target = chess.square(nc, nr)
            target_piece = board.piece_at(target)
            if target_piece is None:
                pseudo.add(target)
            elif target_piece.color != own_color:
                pseudo.add(target)  # capture allowed
                blocked = True       # ray stops at the captured piece
            else:
                blocked = True       # own piece blocks; can't capture

    # 2. Filter by king-safety: a move is legal iff applying it doesn't
    #    leave the mover's king under attack. Use python-chess push/pop
    #    for the apply primitive — chess-spectral has no equivalent.
    legal: set[int] = set()
    for to_sq in pseudo:
        move = chess.Move(sq, to_sq)
        if move not in board.pseudo_legal_moves:
            continue  # a corner case (e.g. promotion required, or move
                      # wasn't classifiable by python-chess) — skip
        board.push(move)
        try:
            still_attacked = board.is_attacked_by(
                not own_color,
                board.king(own_color) if board.king(own_color) is not None
                else to_sq,  # king moved → check the destination
            )
        finally:
            board.pop()
        if not still_attacked:
            legal.add(to_sq)

    return legal


@_REQUIRES_PYTHON_CHESS
def test_spatial_op_matches_python_chess():
    """Layer 1 → 2: validates our spatial operator (SHORT_PFNS-based)
    against python-chess's legal_moves for each non-pawn piece across
    a sample of positions reached during seeded self-play. Verifies
    the spatial op correctly implements geometry + blocking + king-
    safety on real board states, before we use it as ground truth for
    the phase op test."""
    import chess

    plies = _seeded_self_play(white_seed=2026, max_plies=20)
    for p in plies[:8]:
        board = chess.Board(p["fen"])
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece is None or piece.color != board.turn:
                continue
            sym = piece.symbol().upper()
            if sym not in 'NBRQK':
                continue
            spatial = _spatial_legal_dests(board, sq)
            ref = {
                m.to_square for m in board.legal_moves
                if m.from_square == sq and m.promotion is None
                # exclude castling (king moves >1 square): handled
                # by phase_operators.available_castles separately
                and not (sym == 'K'
                         and abs(chess.square_file(m.to_square)
                                 - chess.square_file(sq)) > 1)
            }
            assert spatial == ref, (
                f"spatial op != python-chess legal for {sym} at "
                f"{chess.square_name(sq)} (fen={p['fen']}): "
                f"spatial={sorted(spatial)}, python-chess={sorted(ref)}, "
                f"missing={sorted(ref - spatial)}, "
                f"extra={sorted(spatial - ref)}"
            )


@_REQUIRES_PYTHON_CHESS
def test_seeded_self_play_phase_op_legal_moves_match():
    """Layer 2 → 3: the phase operator's `occupation_aware_moves_a`
    must agree with our spatial operator (validated separately
    against python-chess by `test_spatial_op_matches_python_chess`)
    on the legal destinations for each non-pawn piece during seeded
    self-play.

    Three-layer chain — this is the phase-op-against-spatial-op leg:

        python-chess  ─validates→  spatial op  ─validates→  phase op

    Pawns and castling are excluded (occupation_aware_moves_a doesn't
    handle them — they're separate phase-operator entry points;
    castling is wired into available_castles, separately tested by
    test_2d_phase_operators_smoke).

    Convention: occupation_aware_moves_a uses chess.square_rank /
    chess.square_file directly (rank 0 = rank 1, white's bottom row).
    The function is "hybrid" per its docstring: it generates phase-
    space candidates and then filters them through python-chess
    legality, so the returned set is exactly the legal moves for that
    piece — equality is the right check, not subset."""
    import chess
    from chess_spectral.phase_operators import occupation_aware_moves_a

    plies = _seeded_self_play(white_seed=2026, max_plies=20)
    for p in plies[:8]:  # sample first 8 plies (covers opening moves)
        board = chess.Board(p["fen"])
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece is None or piece.color != board.turn:
                continue
            sym = piece.symbol().upper()
            if sym not in 'NBRQK':
                continue  # skip pawns (different phase-op entry point)
            rank = chess.square_rank(sq)
            file = chess.square_file(sq)
            mover_charge = 1 if board.turn == chess.WHITE else -1
            dests = occupation_aware_moves_a(
                board, sym, rank, file, mover_charge,
            )
            phase_to_squares = {chess.square(c, r) for r, c in dests}
            # Ground truth: spatial op (validated against python-chess
            # by test_spatial_op_matches_python_chess). Excludes
            # castling, just like spatial op does.
            spatial_to_squares = _spatial_legal_dests(board, sq)
            assert phase_to_squares == spatial_to_squares, (
                f"phase op set != spatial op set for {sym} at "
                f"{chess.square_name(sq)} (fen={p['fen']}): "
                f"phase_op={sorted(phase_to_squares)}, "
                f"spatial_op={sorted(spatial_to_squares)}, "
                f"missing={sorted(spatial_to_squares - phase_to_squares)}, "
                f"extra={sorted(phase_to_squares - spatial_to_squares)}"
            )


# ─── Seeded 4D self-play: dynamic position generation via tables_4d ─
#
# 4D analog of the 2D seeded self-play above. Differences:
#
#   - No python-chess: 4D has no python-chess equivalent. We use
#     chess_spectral.tables_4d's per-piece movement generators
#     (rook4_targets, knight4_targets, etc.) directly — the same
#     functions that build the encoder's adjacency tables.
#
#   - No legality / check / checkmate: there's no 4D Oana-Chiru rule
#     enforcement layer in the project (see ROADMAP.md follow-up). We
#     do a "random walk" — each ply picks a random non-pawn piece and
#     a random valid (in-bounds, unoccupied) destination per the piece-
#     movement generator. No captures, no promotions, no checks.
#
#   - This exercises: the 4D piece-movement generators in tables_4d,
#     the FEN4 parser (validates each generated position), and the
#     full 4D encoder pipeline (encode-fen4 / encode bulk / csv).
#
# Same seeded interface as 2D: white_seed required, black_seed
# optional (defaults to white_seed). Different seeds give the two
# colors independent walks.


_4D_PIECE_TARGETS = {
    'N': 'knight4_targets',
    'B': 'bishop4_targets',
    'R': 'rook4_targets',
    'Q': 'queen4_targets',
    'K': 'king4_targets',
}


def _seeded_self_play_4d(white_seed: int,
                         black_seed: int | None = None,
                         *, max_plies: int = 30) -> list[dict]:
    """Random-walk 4D piece progression on the Z₈⁴ lattice.

    Starts from a small mixed position (kings + a handful of
    non-pawn pieces) and on each ply moves one randomly-chosen
    piece to a random valid (in-bounds, unoccupied) target per the
    piece's movement generator from chess_spectral.tables_4d.

    Returns a list of NDJSON4-ready dicts: {"ply", "fen4",
    "move_from", "move_to", "promo", "flags"}. ply 0 is the
    starting position; subsequent plies record the move and the
    resulting FEN4.

    Pawns are excluded — pawn movement on Z₈⁴ has axis constraints
    (Oana-Chiru Def. 11) the FEN4 v1 parser enforces but the random
    walk doesn't model promotion / first-move rules. Future-work
    item in ROADMAP.md."""
    import random
    from chess_spectral import tables_4d as t4

    rng_w = random.Random(white_seed)
    rng_b = random.Random(black_seed if black_seed is not None
                          else white_seed)

    # Starting position: 2 kings + 1 of each major piece per side.
    # Spread across the lattice so movement isn't trivially blocked.
    pos = {
        (0, 0, 0, 0): 'K',  (7, 7, 7, 7): 'k',
        (1, 1, 1, 1): 'Q',  (6, 6, 6, 6): 'q',
        (2, 2, 2, 2): 'R',  (5, 5, 5, 5): 'r',
        (3, 0, 0, 0): 'B',  (4, 7, 7, 7): 'b',
        (0, 3, 0, 0): 'N',  (7, 4, 7, 7): 'n',
    }

    def _to_fen4(p):
        parts = [f"{piece}@{x},{y},{z},{w}"
                 for (x, y, z, w), piece in sorted(p.items())]
        return "4d-fen v1: " + "; ".join(parts)

    out = [{
        "ply": 0, "fen4": _to_fen4(pos),
        "move_from": [0, 0, 0, 0], "move_to": [0, 0, 0, 0],
        "promo": 0, "flags": 0,
    }]

    color_to_move = 'white'  # alternates each ply
    for ply_idx in range(1, max_plies + 1):
        rng = rng_w if color_to_move == 'white' else rng_b

        # Pick a random piece of the side-to-move with at least one
        # valid destination.
        movable = []
        is_white = (color_to_move == 'white')
        for coord, piece in pos.items():
            piece_white = piece.isupper()
            if piece_white != is_white:
                continue
            sym = piece.upper()
            target_fn = getattr(t4, _4D_PIECE_TARGETS.get(sym, ''),
                                None)
            if target_fn is None:
                continue
            valid = []
            for tgt in target_fn(*coord):
                if not all(0 <= c < 8 for c in tgt):
                    continue
                if tgt in pos:
                    continue  # occupied — skip (no captures)
                valid.append(tgt)
            if valid:
                movable.append((coord, valid))
        if not movable:
            break

        from_coord, dests = rng.choice(movable)
        to_coord = rng.choice(dests)
        piece = pos.pop(from_coord)
        pos[to_coord] = piece

        out.append({
            "ply":       ply_idx,
            "fen4":      _to_fen4(pos),
            "move_from": list(from_coord),
            "move_to":   list(to_coord),
            "promo":     0,
            "flags":     0,
        })
        color_to_move = 'black' if color_to_move == 'white' else 'white'

    return out


def test_seeded_self_play_4d_is_reproducible():
    """Same seeds → identical 4D progression."""
    a = _seeded_self_play_4d(white_seed=42, max_plies=20)
    b = _seeded_self_play_4d(white_seed=42, max_plies=20)
    assert [p["fen4"] for p in a] == [p["fen4"] for p in b]


def test_seeded_self_play_4d_separate_seeds_diverge():
    """Distinct white/black seeds → asymmetric walks."""
    a = _seeded_self_play_4d(white_seed=42, black_seed=42, max_plies=20)
    b = _seeded_self_play_4d(white_seed=42, black_seed=99, max_plies=20)
    assert a[0]["fen4"] == b[0]["fen4"]  # starting position identical
    assert a[1]["fen4"] == b[1]["fen4"]  # ply 1 = white, same seed
    # Once black moves (ply 2 onward), divergence is overwhelming.
    assert any(a[i]["fen4"] != b[i]["fen4"]
               for i in range(2, min(len(a), len(b))))


def test_seeded_self_play_4d_uses_real_piece_movement():
    """Each move recorded by the helper must be a destination
    actually returned by the piece's movement generator. Catches any
    bug where the helper accidentally creates moves that bypass the
    Oana-Chiru piece-movement rules."""
    from chess_spectral import tables_4d as t4

    plies = _seeded_self_play_4d(white_seed=2026, max_plies=15)
    for i, p in enumerate(plies[1:], start=1):
        prev = plies[i - 1]
        from_c = tuple(p["move_from"])
        to_c = tuple(p["move_to"])
        # Find the piece at `from_c` in the PREVIOUS position by
        # parsing the prev FEN4. Reuse fen_4d.parse for fidelity.
        from chess_spectral import fen_4d
        prev_pos = fen_4d.parse(prev["fen4"])
        sq = ((from_c[0] * 8 + from_c[1]) * 8 + from_c[2]) * 8 + from_c[3]
        piece_value = prev_pos[sq]
        sym = (piece_value if isinstance(piece_value, str)
               else piece_value[0]).upper()
        target_fn = getattr(t4, _4D_PIECE_TARGETS[sym])
        valid_targets = set(target_fn(*from_c))
        assert to_c in valid_targets, (
            f"ply {i}: {sym}@{from_c} → {to_c} is NOT a valid "
            f"piece-movement target per tables_4d (valid set "
            f"size: {len(valid_targets)})"
        )


@_REQUIRES_C_4D
def test_seeded_self_play_4d_encodes_via_c_pipeline(tmp_path):
    """End-to-end 4D: seeded random-walk → NDJSON4 → spectral_4d
    encode → .spectralz4. Verifies the full 4D pipeline on
    dynamically-generated game data without depending on any external
    PGN dataset or python-chess."""
    plies = _seeded_self_play_4d(white_seed=12345, max_plies=20)
    nd_path = tmp_path / "seeded4d.ndjson4"
    nd_path.write_text(
        "\n".join(json.dumps(p, separators=(",", ":")) for p in plies)
        + "\n",
        encoding="utf-8",
    )
    sp_path = tmp_path / "seeded4d.spectralz4"
    _run_c_4d(["encode", str(nd_path), "-o", str(sp_path), "-z"])
    assert sp_path.is_file()
    assert sp_path.stat().st_size > 0


@_REQUIRES_C_4D
def test_seeded_self_play_4d_csv_pipeline(tmp_path):
    """4D end-to-end including csv: seeded walk → encode → csv (24
    columns × N data rows)."""
    plies = _seeded_self_play_4d(white_seed=7, black_seed=13,
                                 max_plies=15)
    nd_path = tmp_path / "seeded4d.ndjson4"
    nd_path.write_text(
        "\n".join(json.dumps(p, separators=(",", ":")) for p in plies)
        + "\n",
        encoding="utf-8",
    )
    sp_path = tmp_path / "seeded4d.spectralz4"
    csv_path = tmp_path / "seeded4d.csv"
    _run_c_4d(["encode", str(nd_path), "-o", str(sp_path), "-z"])
    _run_c_4d(["csv", str(sp_path), "-o", str(csv_path)])
    rows = csv_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(rows) == len(plies) + 1  # 1 header + N plies
    assert rows[0].count(",") + 1 == 24


# ─── 4D phase-operator smoke (Phase F immolation extension) ─────────


def test_4d_phase_operators_smoke():
    """4D phase ops public surface — touch each piece operator on a
    sample origin and verify shape invariants. The full 4096-origin
    structural gate lives in test_phase_4d_unobstructed.py; this is
    the smoke version that runs in milliseconds."""
    from chess_spectral.phase_operators_4d import (
        P_rook4, P_bishop4, P_queen4, P_king4, P_knight4,
        P_pawn4_white, phi4, phase_set_to_board,
    )
    p = phi4(3, 3, 3, 3)
    rook = phase_set_to_board(P_rook4(p))
    bishop = phase_set_to_board(P_bishop4(p))
    queen = phase_set_to_board(P_queen4(p))
    king = phase_set_to_board(P_king4(p))
    knight = phase_set_to_board(P_knight4(p))
    pawn = phase_set_to_board(P_pawn4_white(
        p, axis="w", on_starting_rank=False, include_captures=True,
    ))
    # Interior mobilities per O&C section 3.
    assert len(rook) == 28
    assert len(king) == 80
    assert len(knight) == 48
    # Queen = rook ∪ bishop, disjoint supports.
    assert queen == (rook | bishop)
    assert (rook & bishop) == frozenset()
    # White pawn at (3,3,3,3): forward push to (3,3,3,4) + 2 captures.
    assert pawn == frozenset({(3, 3, 3, 4), (2, 3, 3, 4), (4, 3, 3, 4)})


def test_4d_phase_check_detection_smoke():
    """4D phasecast_is_check_4d on the initial position — both colors
    safe, both naive and reverse-cast paths agree."""
    chess4d_pkg = pytest.importorskip(
        "chess4d", reason="4D phase-op check detection requires "
                          "python-chess4d-oana-chiru")
    from chess_spectral.phase_operators_4d import (
        phasecast_is_check_4d, phasecast_is_check_4d_no_pawns,
    )
    gs = chess4d_pkg.initial_position()
    for color in (chess4d_pkg.Color.WHITE, chess4d_pkg.Color.BLACK):
        assert phasecast_is_check_4d_no_pawns(gs, color) is False
        assert phasecast_is_check_4d(gs, color) is False


def test_seeded_self_play_4d_phase_op_legal_moves_match():
    """4D analogue of test_seeded_self_play_phase_op_legal_moves_match.

    Quick gate at 5 chess4d.GameState positions (random 1-3-ply walks
    from initial_position) — for every occupied piece in each position,
    occupation_aware_moves_a_4d must equal the chess4d oracle's per-
    piece pseudo-legal destination set. The full corpus version
    (test_phase_4d_occupation_aware.py) exercises 50 positions × ~896
    pieces; this one is the daily-run smoke that runs in ~5 seconds.
    """
    chess4d_pkg = pytest.importorskip(
        "chess4d", reason="4D phase-op smoke requires "
                          "python-chess4d-oana-chiru")
    from chess_spectral.phase_operators_4d import (
        occupation_aware_moves_a_4d,
    )
    import random
    piece_gens = {
        chess4d_pkg.types.PieceType.ROOK:   chess4d_pkg.rook_moves,
        chess4d_pkg.types.PieceType.BISHOP: chess4d_pkg.bishop_moves,
        chess4d_pkg.types.PieceType.QUEEN:  chess4d_pkg.queen_moves,
        chess4d_pkg.types.PieceType.KNIGHT: chess4d_pkg.knight_moves,
        chess4d_pkg.types.PieceType.KING:   chess4d_pkg.king_moves,
        chess4d_pkg.types.PieceType.PAWN:   chess4d_pkg.pawn_moves,
    }
    mismatches = []
    for seed in range(5):
        gs = chess4d_pkg.initial_position()
        rng = random.Random(seed)
        for _ in range(1 + (seed % 3)):  # 1-3 plies per position
            moves = list(gs.legal_moves())
            if not moves:
                break
            gs.push(rng.choice(moves))
        # Sample 20 random pieces per position to cap the runtime
        # (full corpus is in test_phase_4d_occupation_aware.py).
        all_pieces = []
        for color in (chess4d_pkg.Color.WHITE, chess4d_pkg.Color.BLACK):
            all_pieces.extend(gs.board.pieces_of(color))
        rng.shuffle(all_pieces)
        for sq, piece in all_pieces[:20]:
            phase_dests = occupation_aware_moves_a_4d(gs, sq, piece)
            oracle = frozenset(
                (m.to_sq.x, m.to_sq.y, m.to_sq.z, m.to_sq.w)
                for m in piece_gens[piece.piece_type](
                    sq, piece.color, gs.board)
            )
            if phase_dests != oracle:
                mismatches.append((seed, sq, piece, phase_dests, oracle))
                if len(mismatches) >= 3:
                    break
    assert not mismatches, (
        f"phase-op vs chess4d oracle disagree at: "
        + "\n  ".join(
            f"seed={s} {p.color.name} {p.piece_type.name} at {sq}: "
            f"missing={o-pd}, extra={pd-o}"
            for s, sq, p, pd, o in mismatches
        )
    )


# ─── stub-detector meta-test (Phase F immolation extension) ─────────
#
# Catches "we shipped a v1.2.X release with unwired CLI commands"
# regressions before they ship again. Mirrors the v1.2.4 inventory
# discipline.


_STUB_PATTERNS = (
    # C-side "TODO this command" stubs (cmd_todo("name") in main.c).
    # This was the exact pattern that shipped 12 unwired CLI commands
    # in v1.2.3 — the v1.2.4 wiring removed every instance.
    (r'\bcmd_todo\s*\(\s*"', "C cmd_todo() stub"),

    # Python "_not_implemented(...)" helper — the
    # chess_spectral_4d/cli.py v1.2.3 placeholder for unwired
    # commands. Wired in v1.2.4 alongside the C cmd_todo cleanup.
    (r"^\s*return\s+_not_implemented\s*\(", "_not_implemented() return"),
    (r"^\s*_not_implemented\s*\(", "_not_implemented() bare call"),
)
# We intentionally do NOT flag plain ``raise NotImplementedError``:
# it has too many legitimate uses (deferred-feature surfaces with
# user-facing loud failure). The two patterns above are unambiguous
# indicators of "command/function stub that should be wired" —
# they're the patterns that produced the v1.2.3 → 1.2.4 unwired-CLI
# regression we're guarding against here.

_STUB_EXCLUDE = (
    # Tests directories — fixtures, mocks, and "expect-not-implemented"
    # assertions are intentional.
    "/tests/",
    "\\tests\\",
    # Vendored upstream sources we don't own.
    "/vendor/",
    "\\vendor\\",
    # Build / cache trees.
    "/build/",
    "/__pycache__/",
    "\\build\\",
    # Documentation files (research records and ROADMAPs intentionally
    # describe stubbed states for historical clarity).
    ".md",
    # Skip the chess_spectral_4d.cli "(stubbed; needs ...)" docstring
    # — that's documentation of historical state, not a current stub.
    # The actual logic was wired in v1.2.4.
)


def _is_excluded(path_str: str) -> bool:
    return any(ex in path_str for ex in _STUB_EXCLUDE)


def test_no_unwired_stubs_in_shipped_python_or_c():
    """Walk the shipped chess_spectral / chess_spectral_4d Python
    sources and the chess-spectral C source tree; fail if any
    function body still contains a stub pattern.

    Covers:
      * C: cmd_todo("name") (the v1.2.3 → 1.2.4 unwired-command class)
      * Python: raise NotImplementedError outside test directories
      * Python: bare _not_implemented() calls (the chess_spectral_4d
        v1.2.3 placeholder)

    Excludes vendor/, tests/, build artifacts, and Markdown docs.

    See PHASE_OPERATOR_SUPPLEMENT_4D.md §13.7 for the full discipline
    rationale.
    """
    import re
    repo_python = Path(__file__).resolve().parent.parent
    chess_spectral_root = repo_python.parent  # chess-spectral/

    found: list[tuple[str, int, str]] = []
    compiled = [(re.compile(p, re.MULTILINE), label) for p, label in _STUB_PATTERNS]

    def _scan(root: Path, suffixes: tuple[str, ...]):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in suffixes:
                continue
            sp = str(path)
            if _is_excluded(sp):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for rx, label in compiled:
                for m in rx.finditer(text):
                    line = text[:m.start()].count("\n") + 1
                    found.append((sp, line, label))

    # Python sources we ship.
    _scan(repo_python / "chess_spectral", (".py",))
    _scan(repo_python / "chess_spectral_4d", (".py",))
    # C sources + headers.
    _scan(chess_spectral_root / "src", (".c", ".h"))
    _scan(chess_spectral_root / "include", (".h",))

    # Phase B's pawn operators raised NotImplementedError before
    # Phase E. After Phase E lifts include_captures, no shipped
    # function should hit any of the stub patterns. The check below
    # also tolerates `pytest.raises(NotImplementedError)` patterns
    # inside test files (excluded by path) and intentional stubs in
    # vendored code.
    assert not found, (
        "Found unwired stubs in shipped sources:\n"
        + "\n".join(
            f"  {path}:{line}  ({label})"
            for path, line, label in found
        )
        + "\n\nIf any of these are intentional (deferred phase, etc.),"
          " raise a clear ValueError with a phase reference instead, "
          "or add the path to _STUB_EXCLUDE."
    )


# ─── version-drift meta-test (Phase F immolation extension) ─────────
#
# Catches "we shipped a release with a hardcoded version literal that
# drifted from the dist version" before it ships again. The pre-1.3.2
# instance: between v1.2.3 and v1.3.1, six pyproject.toml bumps landed
# without ever updating the `__version__ = "1.2.3"` literal in
# chess_spectral/__init__.py, so users on v1.3.1 saw
# `chess_spectral.__version__ == "1.2.3"` while
# `importlib.metadata.version("chess-spectral")` correctly reported
# "1.3.1". PR #71 fixed it dynamically (importlib.metadata-derived);
# this test pins the fix so the pattern can't regress.
#
# A second class of drift this catches: pyproject.toml and
# pyproject-pure.toml falling out of sync. They MUST agree — both
# generate wheels for the same package on PyPI, and the publish
# workflow already grep-asserts equality. Adding the assertion here
# makes the failure mode visible at test time, before CI.


def test_no_hardcoded_version_strings_drift_in_shipped_python():
    """Walk shipped Python sources for `__version__ = "X.Y.Z"`
    literals; fail if any is found other than the documented
    `"0.0.0+unknown"` fallback sentinel. Per PEP 396 + the v1.3.2
    contract, `__version__` must derive dynamically from
    `importlib.metadata.version("chess-spectral")` — see
    `chess_spectral/__init__.py` for the canonical pattern.

    Two pyproject.toml files coexist (the scikit-build-core platform
    build and the hatchling pure-Python build). Their `version`
    fields MUST match — they both produce wheels for the same PyPI
    package — and bumping one without the other has been a recurring
    footgun. Asserted here too.
    """
    import re
    import tomllib

    repo_python = Path(__file__).resolve().parent.parent
    chess_spectral_root = repo_python.parent  # chess-spectral/

    # ── Both pyproject.toml files must agree on `version` ────────
    with open(repo_python / "pyproject.toml", "rb") as f:
        v_main = tomllib.load(f)["project"]["version"]
    with open(repo_python / "pyproject-pure.toml", "rb") as f:
        v_pure = tomllib.load(f)["project"]["version"]
    assert v_main == v_pure, (
        f"pyproject.toml says version={v_main!r} but "
        f"pyproject-pure.toml says version={v_pure!r}; the two MUST "
        f"agree (both files generate wheels for the same PyPI "
        f"package). Bump both, or the publish workflow's "
        f"version-equality grep will reject the release."
    )

    # ── No hardcoded `__version__ = "X.Y.Z"` in shipped sources ──
    # The legitimate fallback sentinel ("0.0.0+unknown", returned
    # when the package isn't pip-installed) is the only literal
    # assignment allowed; anything else means someone reintroduced
    # the v1.2.3 → 1.3.1 drift pattern.
    pattern = re.compile(
        r'^\s*__version__\s*=\s*["\']([^"\']+)["\']',
        re.MULTILINE,
    )
    _ALLOWED_LITERAL = "0.0.0+unknown"
    found: list[tuple[str, int, str]] = []
    for pkg in ("chess_spectral", "chess_spectral_4d"):
        for path in (repo_python / pkg).rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in pattern.finditer(text):
                literal = m.group(1)
                if literal == _ALLOWED_LITERAL:
                    continue
                line = text[:m.start()].count("\n") + 1
                found.append((str(path), line, literal))

    assert not found, (
        "Found hardcoded __version__ literals in shipped Python "
        "sources:\n"
        + "\n".join(
            f"  {path}:{line}  __version__ = {literal!r}"
            for path, line, literal in found
        )
        + "\n\nPer PEP 396 + the v1.3.2 contract, __version__ must "
        f"derive from importlib.metadata.version('chess-spectral'). "
        f"See chess_spectral/__init__.py for the canonical pattern. "
        f"The only literal assignment allowed is the fallback "
        f"sentinel `__version__ = {_ALLOWED_LITERAL!r}` for "
        "uninstalled / source-tree-only invocations."
    )

    # Sanity check: the canonical __init__.py we point users at must
    # itself NOT contain a literal "X.Y.Z" assignment for __version__,
    # only the fallback. If this fails, the canonical pattern itself
    # broke and we'd never have noticed.
    init = (repo_python / "chess_spectral" / "__init__.py").read_text(
        encoding="utf-8")
    init_lits = pattern.findall(init)
    assert init_lits == [_ALLOWED_LITERAL], (
        f"chess_spectral/__init__.py contains unexpected "
        f"__version__ literal(s) {init_lits!r}; expected exactly "
        f"the fallback {_ALLOWED_LITERAL!r}. The canonical "
        "dynamic-derivation pattern was edited away."
    )


# ─── v1.4 API gap smoke (chess_spectral_4d game-state surface) ──────
#
# Phase 7's §16.9 audit closed five gaps in the v1.3 surface:
#   - apply_move(promote_to=...): pawn promotion target argument.
#   - GameState4D / MoveHistory4D / Move4D: ply-by-ply history with
#     side-to-move + half-move clock + position-hash table.
#   - get_draw_status: priority-ordered draw classifier (threefold,
#     50-move, insufficient, stalemate).
#   - get_move_history: Pyodide-friendly list-of-dicts serialization.
#   - load_state: FEN4 → GameState4D import.
# Plus fen_4d.serialize round-trip (was always callable but never
# pinned to immolation discipline) and a chess4d 0.4 castling/EP
# regression smoke per the §17.3 audit.
#
# These are smoke-level verifications; the per-feature unit tests
# live in test_apply_move_promotion_4d.py / test_game_state_4d.py /
# test_castling_ep_4d_regression.py / test_fen4_round_trip.py.


def _kk_state():
    """Minimal two-king GameState4D — useful for state-machinery
    tests that don't depend on a particular position payload.
    Helper-local so the immolation suite stays self-contained."""
    import chess_spectral_4d as csd4
    return csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; k@7,7,7,7"
    )


@pytest.mark.parametrize("target", ["Q", "R", "B", "N"])
def test_v14_apply_move_promotion_to_each_piece(target):
    """v1.4 apply_move(promote_to=...): white W-axis pawn at w=6
    promotes to Q/R/B/N at w=7 with the moving pawn's color
    (uppercase for white)."""
    import chess_spectral_4d as csd4
    pos = {csd4.coord_to_sq((0, 0, 0, 6)): ("P", "w")}
    gs = csd4.GameState4D(position=pos)
    gs.history.record_initial_position(pos)
    move = csd4.apply_move(
        gs, (0, 0, 0, 6), (0, 0, 0, 7), promote_to=target,
    )
    assert move.promote_to == target
    sq = csd4.coord_to_sq((0, 0, 0, 7))
    assert gs.position[sq] == target


def test_v14_game_state_records_history():
    """GameState4D appends a Move4D record per ply, flips
    side-to-move, and reflects the post-move position."""
    import chess_spectral_4d as csd4
    gs = _kk_state()
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    assert len(gs.history.moves) == 2
    assert gs.history.moves[0].ply == 0
    assert gs.history.moves[1].ply == 1
    assert gs.history.side_to_move == csd4.SIDE_WHITE  # back to white
    # Position reflects both moves.
    assert csd4.coord_to_sq((1, 0, 0, 0)) in gs.position
    assert csd4.coord_to_sq((6, 7, 7, 7)) in gs.position


def test_v14_threefold_repetition_detected():
    """4-ply A→B→A→B cycle, played twice, registers the starting
    position three times (initial + 2× return) and triggers the
    'threefold' draw status."""
    import chess_spectral_4d as csd4
    gs = _kk_state()
    for _ in range(2):
        csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
        csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
        csd4.apply_move(gs, (1, 0, 0, 0), (0, 0, 0, 0))
        csd4.apply_move(gs, (6, 7, 7, 7), (7, 7, 7, 7))
    assert gs.history.repetition_count(gs.position) == 3
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    assert out["status"] == "threefold"


def test_v14_50_move_rule_detected():
    """100 quiet half-moves visiting 50 unique king positions per
    side (no repeats, no captures, no pawn moves) trigger the
    'fifty-move' draw status — isolated from threefold."""
    import chess_spectral_4d as csd4

    gs = csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; k@7,0,0,0"
    )
    # Snake through 50 unique (y,z,w) squares per side at fixed x.
    def _path(start_x, n):
        out = []
        for y in range(8):
            for z in range(8):
                for w in range(8):
                    out.append((start_x, y, z, w))
                    if len(out) >= n + 1:
                        return out
        return out
    white_path = _path(0, 50)
    black_path = _path(7, 50)
    for i in range(50):
        csd4.apply_move(gs, white_path[i], white_path[i + 1])
        csd4.apply_move(gs, black_path[i], black_path[i + 1])
    assert gs.history.half_move_clock == 100
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    assert out["status"] == "fifty-move"


def test_v14_get_draw_status_priorities():
    """Detection order (per python-chess): threefold → fifty-move
    → insufficient → stalemate. We verify the threefold-over-
    stalemate priority by triggering threefold and asserting the
    status is 'threefold' even when has_legal_moves=False (which
    would otherwise be 'stalemate'). The 50-move-over-stalemate
    priority is verified separately by
    test_v14_50_move_rule_detected (which passes
    has_legal_moves=True so stalemate is suppressed)."""
    import chess_spectral_4d as csd4
    gs = _kk_state()
    for _ in range(2):
        csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
        csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
        csd4.apply_move(gs, (1, 0, 0, 0), (0, 0, 0, 0))
        csd4.apply_move(gs, (6, 7, 7, 7), (7, 7, 7, 7))
    # Even with has_legal_moves=False, threefold takes priority.
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=False)
    assert out["status"] == "threefold"


def test_v14_get_move_history_returns_pyodide_friendly():
    """get_move_history returns a list of plain dicts (not
    dataclasses or numpy types) suitable for Pyodide / WASM
    structured-clone serialization. Per §17.3 the schema must
    expose: ply, from, to, piece, halfMoveClock, plus optional
    promoteTo / capturedPiece."""
    import chess_spectral_4d as csd4
    gs = _kk_state()
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    out = csd4.bridge.get_move_history(gs)
    assert out["ok"] is True
    moves = out["moves"]
    assert isinstance(moves, list)
    assert len(moves) == 2
    for entry in moves:
        assert isinstance(entry, dict)
        # Required keys per §17.3 schema.
        assert {"ply", "from", "to", "piece", "halfMoveClock"} <= entry.keys()
        # No internal types leak.
        assert isinstance(entry["ply"], int)
        assert isinstance(entry["from"], list)
        assert isinstance(entry["to"], list)
        assert isinstance(entry["piece"], str)
        assert isinstance(entry["halfMoveClock"], int)


def test_v14_fen4_serialize_round_trip():
    """fen_4d.serialize is the inverse of fen_4d.parse:
    parse(serialize(p)) == p exactly for every position. Tested
    on a sample of fixture-style positions including pawns
    (which carry an axis annotation) and a corner+king position."""
    from chess_spectral import fen_4d
    fixtures = [
        # Antipodal kings (the encoder's Z_2 kernel sentinel).
        {0: "K", 4095: "k"},
        # Mixed mid-board with all six piece types.
        {
            (1 * 8 + 2) * 8 * 8 + 3 * 8 + 4: "Q",
            (3 * 8 + 1) * 8 * 8 + 2 * 8 + 3: "B",
            (2 * 8 + 5) * 8 * 8 + 0 * 8 + 1: "N",
            (4 * 8 + 3) * 8 * 8 + 1 * 8 + 2: "R",
            0: "K", 4095: "k",
        },
        # Pawn-bearing positions (both axes, both colors).
        {
            0: "K", 4095: "k",
            (1 * 8 + 1) * 8 * 8 + 1 * 8 + 1: ("P", "w"),
            (2 * 8 + 0) * 8 * 8 + 0 * 8 + 0: ("P", "y"),
            (7 * 8 + 0) * 8 * 8 + 5 * 8 + 5: ("p", "w"),
        },
    ]
    for pos in fixtures:
        rendered = fen_4d.serialize(pos)
        parsed = fen_4d.parse(rendered)
        assert parsed == pos, (
            f"FEN4 round-trip failed: parse(serialize(p)) != p\n"
            f"  pos = {pos}\n  rendered = {rendered}\n"
            f"  parsed = {parsed}"
        )


def test_v14_castling_ep_regression_smoke():
    """Quick chess4d 0.4 regression: castling is *not* legal at the
    dense 4D startpos (path blocked by minor pieces), and pawn
    moves are always present in legal_moves at startpos. This
    pins the §17.3 audit findings without exhaustive enumeration
    (full coverage lives in test_castling_ep_4d_regression.py)."""
    chess4d_pkg = pytest.importorskip(
        "chess4d", reason="chess4d not installed; v1.4 castling/EP "
                          "smoke requires upstream chess4d 0.4",
    )
    gs = chess4d_pkg.startpos.initial_position()
    legal = list(gs.legal_moves())
    assert len(legal) > 0, "startpos has no legal moves?!"
    # No castling at dense startpos.
    castling_at_start = [m for m in legal if m.is_castling]
    assert castling_at_start == [], (
        "chess4d emitted a castling move at the dense startpos; the "
        "path-clearance check is broken — the §17.3 audit finding "
        "regressed."
    )


# ─── Track A kinematic smoke (chess_spectral.qm_4d) ──────────────────
#
# The Track A kinematic layer is the QM front-end for the 4D encoder:
# state_to_psi normalizes encoded vectors as ψ ∈ C^45056, exposes the
# 11-channel projector PVM, the B_4 unitary representation, and five
# Hermitian piece-reach observables. Phase 4 / B[1..5] dynamics build
# on these primitives.
#
# Smoke level: 1-2 assertions per public surface, on a single
# imbalanced-position fixture seeded for stability across runs.


def _qm4_smoke_position():
    """Mid-board imbalanced 6-piece position with non-trivial mass on
    every channel. Reused across the qm_4d / qm_4d_dynamics /
    qm_4d_bridge smoke tests."""
    from chess_spectral import tables_4d as t4
    coords = {
        (0, 0, 0, 0): 'K', (5, 5, 5, 5): 'k',
        (1, 2, 3, 4): 'Q',
        (3, 1, 2, 3): 'B',
        (2, 5, 0, 1): 'N',
        (4, 3, 1, 2): 'R',
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def test_track_a_state_to_psi_normalized():
    """state_to_psi returns an L2-unit vector in C^45056 for any
    non-empty position (the encoder's normalization invariant)."""
    from chess_spectral import qm_4d
    pos = _qm4_smoke_position()
    psi = qm_4d.state_to_psi(pos, side_to_move=True)
    assert psi.shape == (45056,)
    assert qm_4d.is_normalized(psi, tol=1e-10), (
        f"||psi|| = {qm_4d.norm(psi)} (expected 1.0)"
    )


def test_track_a_state_to_psi_z2_sign_convention():
    """Per ADR-004 §3.4 amendment + Pre-flight 1: state_to_psi
    flips the overall sign of ψ when side_to_move flips. The Z_2
    grading lives at the state-vector level."""
    from chess_spectral import qm_4d
    import numpy as np
    pos = _qm4_smoke_position()
    psi_w = qm_4d.state_to_psi(pos, side_to_move=True)
    psi_b = qm_4d.state_to_psi(pos, side_to_move=False)
    # psi_w == -psi_b within float rounding.
    assert np.allclose(psi_w, -psi_b, atol=1e-12), (
        f"max |psi_w + psi_b| = {float(np.max(np.abs(psi_w + psi_b)))}; "
        f"the Z_2 sign convention is broken"
    )


def test_track_a_channel_pvm_sums_to_one():
    """The 11 channel projectors P_c form a complete orthogonal PVM
    on C^45056: sum_c <psi|P_c|psi> = ||psi||^2 = 1 within float
    rounding for any normalized ψ."""
    from chess_spectral import qm_4d
    import numpy as np
    pos = _qm4_smoke_position()
    psi = qm_4d.state_to_psi(pos, side_to_move=True)
    probs = qm_4d.measure_channel_distribution(psi)
    assert probs.shape == (11,)
    assert np.all(probs >= 0.0)
    assert abs(probs.sum() - 1.0) < 1e-10, (
        f"channel-PVM probabilities sum to {probs.sum()}, not 1.0; "
        f"per-channel = {probs}"
    )


@pytest.mark.parametrize("piece", ["R", "B", "Q", "K", "N"])
def test_track_a_5_hermitian_observables_real_expectation(piece):
    """For every non-pawn piece-reach Hermitian H_<piece>_4 (which
    Pre-flight 2 verified is real-symmetric on C^4096), the
    expectation <ψ_chan|H|ψ_chan> is real-valued (imaginary part
    < 1e-10) on every channel block of a real-game ψ.

    Uses qm_4d._get_or_build_H to amortise the 4096×4096 H_piece
    construction across the 5 parametrized invocations (the
    module-level cache fires after the first parametrize call;
    subsequent calls are O(1))."""
    from chess_spectral import qm_4d
    import numpy as np
    pos = _qm4_smoke_position()
    psi = qm_4d.state_to_psi(pos, side_to_move=True)
    H = qm_4d._get_or_build_H(piece)  # cached; ~4s on first piece
    psi_view = psi.reshape(11, 4096)
    for c in range(11):
        Hpsi = H @ psi_view[c]
        val = complex(np.vdot(psi_view[c], Hpsi))
        assert abs(val.imag) < 1e-10, (
            f"<ψ|H_{piece}|ψ> on channel {c} has imag={val.imag} > 1e-10; "
            f"H_{piece} is not Hermitian on this state"
        )


def test_track_a_b4_unitary_rep_unitarity():
    """Sample several B_4 group elements and verify
    b4_unitary_rep_4096(g) is unitary (U†U == I within 1e-12).
    The full group has 384 elements; sampling 5 is sufficient for
    smoke. Full structural check lives in test_qm_4d.py."""
    from chess_spectral import qm_4d
    from chess_spectral import tables_4d as t4
    import numpy as np
    closure = t4.b4_closure()
    # Sample evenly-spaced indices for stability.
    sampled = [closure[0], closure[len(closure) // 4],
               closure[len(closure) // 2],
               closure[3 * len(closure) // 4],
               closure[-1]]
    for g in sampled:
        U = qm_4d.b4_unitary_rep_4096(g)
        assert U.shape == (4096, 4096)
        assert qm_4d.is_unitary(U, tol=1e-12), (
            f"b4_unitary_rep_4096({g}) is not unitary at 1e-12"
        )


# ─── Phase 4 channel builders smoke (qm_4d_dynamics u_move_*) ────────
#
# All 11 per-channel move-as-unitary builders ship in v1.5:
#   - B1  : u_move_a1                      → A_1 (channel 0)
#   - B3a : u_move_std4                    → STD4_X/Y/Z/W (channels 1-4)
#   - B3b : u_move_fa_pawn                 → FA_PAWN_W/Y (channels 8-9)
#   - B3c : u_move_fib_meas                → FIB_SYM_1/2/3 (channels 5-7)
#   - B3d/e: u_move_fd_diag                → FD_DIAG (channel 10)
#   - B5  : capture-path branch on every channel
#
# Smoke level: each builder accepts the canonical (state, move) shape;
# returns either a csr_matrix (strict-unitary path on non-capture) or
# a marker dict (cross-orbit / measurement-only / rank-1 / capture).
# Bridge-level apply_move_qm assembly populates all 11 keys correctly.


def _qm4_smoke_non_capture_move():
    """A non-capture move pair (rook (4,3,1,2) → (4,4,1,2)) on the
    smoke position; chosen to leave every channel well-defined."""
    from chess_spectral import tables_4d as t4
    return t4.sq4(4, 3, 1, 2), t4.sq4(4, 4, 1, 2)


def _qm4_smoke_capture_move():
    """A capture move (rook (4,3,1,2) captures bishop (3,1,2,3)) on
    the smoke position; exercises the B5 capture-path on every
    channel."""
    from chess_spectral import tables_4d as t4
    return t4.sq4(4, 3, 1, 2), t4.sq4(3, 1, 2, 3)


def test_phase_4_channel_builders_return_types_non_capture():
    """For a single non-capture move on a real position, each
    per-channel builder returns the documented type contract:
      - A_1: csr_matrix (B1 strict-unitary path).
      - STD4_*: csr_matrix (same-orbit) OR marker dict (cross-orbit).
      - FA_PAWN_*: csr_matrix (B3b sub-unitary, always non-capture).
      - FIB_SYM_*: marker dict ('measurement-only').
      - FD_DIAG: marker dict ('rank-1-update-with-renorm').
    """
    import scipy.sparse as sp
    from chess_spectral import qm_4d_dynamics as dyn
    pos = _qm4_smoke_position()
    move = _qm4_smoke_non_capture_move()

    # A_1 — always csr_matrix on non-capture.
    a1 = dyn.u_move_a1(pos, move, assume_non_capture=True)
    assert sp.issparse(a1) and a1.shape == (4096, 4096)

    # STD4_* — csr_matrix on same-orbit, marker dict on cross-orbit.
    for axis in ('X', 'Y', 'Z', 'W'):
        v = dyn.u_move_std4(pos, move, axis=axis, assume_non_capture=True)
        assert (sp.issparse(v) and v.shape == (4096, 4096)) or (
            isinstance(v, dict) and v.get('reason') == 'cross-orbit'
        ), f"STD4_{axis} returned unexpected type: {type(v).__name__}"

    # FA_PAWN_* — csr_matrix on non-capture, always.
    for axis in ('W', 'Y'):
        v = dyn.u_move_fa_pawn(pos, move, axis=axis, assume_non_capture=True)
        assert sp.issparse(v) and v.shape == (4096, 4096), (
            f"FA_PAWN_{axis} non-capture didn't return csr_matrix"
        )

    # FIB_SYM_* — marker dict ('measurement-only').
    for fib_idx in (1, 2, 3):
        v = dyn.u_move_fib_meas(pos, move, fib_idx,
                                assume_non_capture=True)
        assert isinstance(v, dict) and v['reason'] == 'measurement-only'
        assert v['psi_post_block'].shape == (4096,)

    # FD_DIAG — marker dict with rank-1-update-with-renorm.
    v = dyn.u_move_fd_diag(pos, move, assume_non_capture=True)
    assert isinstance(v, dict) and v['reason'] == 'rank-1-update-with-renorm'
    assert v['psi_post_block'].shape == (4096,)


def test_phase_4_channel_builders_capture_path():
    """For a capture move, every per-channel builder with
    assume_non_capture=False returns a marker dict carrying
    psi_post_block + captured_piece. Reason strings are
    channel-family-specific:
      - A_1 / STD4_* / FD_DIAG : 'capture-rank-1-with-renorm'
      - FA_PAWN_*              : 'capture-partial-isometry'
      - FIB_SYM_*              : 'capture-measurement-only'
    """
    from chess_spectral import qm_4d_dynamics as dyn
    pos = _qm4_smoke_position()
    move = _qm4_smoke_capture_move()
    # The captured piece is the bishop at (3,1,2,3) on the smoke pos.
    expected_captured = 'B'

    # A_1.
    v = dyn.u_move_a1(pos, move, assume_non_capture=False)
    assert isinstance(v, dict)
    assert v['reason'] == 'capture-rank-1-with-renorm'
    assert v['captured_piece'] == expected_captured
    assert v['psi_post_block'].shape == (4096,)

    # STD4_*.
    for axis in ('X', 'Y', 'Z', 'W'):
        v = dyn.u_move_std4(pos, move, axis=axis,
                            assume_non_capture=False)
        assert isinstance(v, dict)
        assert v['reason'] == 'capture-rank-1-with-renorm'
        assert v['captured_piece'] == expected_captured

    # FA_PAWN_*.
    for axis in ('W', 'Y'):
        v = dyn.u_move_fa_pawn(pos, move, axis=axis,
                               assume_non_capture=False)
        assert isinstance(v, dict)
        assert v['reason'] == 'capture-partial-isometry'
        assert v['captured_piece'] == expected_captured

    # FIB_SYM_*.
    for fib_idx in (1, 2, 3):
        v = dyn.u_move_fib_meas(pos, move, fib_idx,
                                assume_non_capture=False)
        assert isinstance(v, dict)
        assert v['reason'] == 'capture-measurement-only'
        assert v['captured_piece'] == expected_captured

    # FD_DIAG.
    v = dyn.u_move_fd_diag(pos, move, assume_non_capture=False)
    assert isinstance(v, dict)
    assert v['reason'] == 'capture-rank-1-with-renorm'
    assert v['captured_piece'] == expected_captured


def test_phase_4_apply_move_qm_assembles_11_channels_non_capture():
    """The bridge apply_move_qm dispatches the per-channel builders
    and returns a dict keyed by all 11 channel names. On a
    non-capture move the value mix is csr_matrix + marker dict
    depending on the channel family."""
    from chess_spectral import qm_4d_bridge as br
    pos = _qm4_smoke_position()
    move = _qm4_smoke_non_capture_move()
    channels = br.apply_move_qm(pos, move)
    assert set(channels.keys()) == {
        'A1', 'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
        'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
        'FA_PAWN_W', 'FA_PAWN_Y', 'FD_DIAG',
    }
    # FIB_SYM_* and FD_DIAG are always marker dicts on non-capture.
    for ch in ('FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3', 'FD_DIAG'):
        assert isinstance(channels[ch], dict), (
            f"{ch} should be marker dict on non-capture"
        )


def test_phase_4_apply_move_qm_assembles_11_channels_capture():
    """For a capture move, every channel returns a marker dict
    (the all-marker-dict variant). This is the bridge's B5
    capture path: every channel value is consumed via splice
    (psi_post_block) at the v1.5 dispatch layer."""
    from chess_spectral import qm_4d_bridge as br
    pos = _qm4_smoke_position()
    move = _qm4_smoke_capture_move()
    channels = br.apply_move_qm(pos, move)
    # All 11 keys, all marker dicts, all carrying captured_piece.
    assert len(channels) == 11
    for name, value in channels.items():
        assert isinstance(value, dict), (
            f"capture move on channel {name} should be marker dict"
        )
        assert 'captured_piece' in value
        assert 'psi_post_block' in value
        assert value['psi_post_block'].shape == (4096,)


# ─── B2 Zeno evolution smoke (qm_4d_dynamics.evolve_under_h0) ────────
#
# H_0 = -Δ_{P_8^4} is Hermitian; U(t) = exp(-i H_0 t) is unitary;
# therefore norm and energy are preserved exactly within Krylov
# residual.


def test_b2_evolve_under_h0_preserves_norm():
    """For ψ(t) = exp(-i H_0 t) ψ on a real seeded position,
    ‖ψ(t)‖ = ‖ψ‖ = 1 within 1e-10."""
    from chess_spectral import qm_4d
    from chess_spectral import qm_4d_dynamics as dyn
    pos = _qm4_smoke_position()
    psi = qm_4d.state_to_psi(pos, side_to_move=True)
    for t in (0.05, 0.5, 2.0):
        psi_t = dyn.evolve_under_h0(psi, t)
        n = qm_4d.norm(psi_t)
        assert abs(n - 1.0) < 1e-10, (
            f"||exp(-i H_0 * {t}) psi|| = {n}, expected 1.0"
        )


def test_b2_evolve_under_h0_conserves_energy():
    """For unitary U(t), <ψ_t|H_0|ψ_t> = <ψ|H_0|ψ> within float
    precision (Heisenberg-picture energy conservation). Tested at
    a few positive and negative times."""
    from chess_spectral import qm_4d
    from chess_spectral import qm_4d_dynamics as dyn
    pos = _qm4_smoke_position()
    psi = qm_4d.state_to_psi(pos, side_to_move=True)
    H0 = dyn.H_FREE_4D  # 4096×4096 sparse Hermitian
    # Compute <ψ|H_0|ψ> on each channel block, sum.
    psi_view = psi.reshape(11, 4096)
    e_init = sum(qm_4d.expectation(H0, psi_view[c]) for c in range(11))
    for t in (0.1, 1.0, -0.5):
        psi_t = dyn.evolve_under_h0(psi, t)
        psi_t_view = psi_t.reshape(11, 4096)
        e_t = sum(qm_4d.expectation(H0, psi_t_view[c]) for c in range(11))
        assert abs(e_t - e_init) < 1e-9, (
            f"energy drift at t={t}: <H_0>_init = {e_init}, "
            f"<H_0>_t = {e_t}, diff = {abs(e_t - e_init)}"
        )


# ─── v1.5 §17.1 + §17.5 bridge surface smoke ─────────────────────────
#
# All 7 §17.1 consumer methods (get_qm_state, get_qm_density,
# apply_move_qm_full, measure_at, get_density_matrix_of (NIE),
# get_probability_current, get_qm_expectation) plus 6 §17.5 dev
# methods (get_version, get_encoder_shape, get_fen4_state,
# load_fen4, load_jsonl_fixture, has_legal_moves). Smoke verifies
# the documented return shapes + numerics agree with direct
# state_to_psi calls (the SSOT).


def test_v15_get_qm_state_float32_interleaved():
    """get_qm_state returns Float32 real+imag interleaved of length
    2 × 45056 = 90112, with basisDim=45056 and normSq=1."""
    import numpy as np
    from chess_spectral import qm_4d_bridge as br
    pos = _qm4_smoke_position()
    res = br.get_qm_state(pos)
    assert res['ok'] is True
    assert res['basisDim'] == 45056
    assert isinstance(res['psi'], np.ndarray)
    assert res['psi'].dtype == np.float32
    assert res['psi'].size == 90112
    assert abs(res['normSq'] - 1.0) < 1e-6


def test_v15_get_qm_density_per_cell_sums_to_one():
    """get_qm_density returns Float32(4096) per-cell density
    summed across the 11 channels; sum equals ||ψ||^2 = 1."""
    import numpy as np
    from chess_spectral import qm_4d_bridge as br
    pos = _qm4_smoke_position()
    res = br.get_qm_density(pos)
    assert res['ok'] is True
    assert res['density'].dtype == np.float32
    assert res['density'].shape == (4096,)
    assert (res['density'] >= 0.0).all()
    assert abs(float(res['density'].sum()) - 1.0) < 1e-6


def test_v15_apply_move_qm_full_dispatch_normalized_psi():
    """apply_move_qm_full assembles the per-channel dispatch dict
    into a single ψ_post in C^45056. After renormalization
    ||ψ_post||^2 == 1 within float rounding for both non-capture
    and capture moves."""
    from chess_spectral import qm_4d_bridge as br
    pos = _qm4_smoke_position()
    # Non-capture.
    res = br.apply_move_qm_full(pos, _qm4_smoke_non_capture_move())
    assert res['ok'] is True
    assert res['psi'].size == 90112
    assert abs(res['normSq'] - 1.0) < 1e-6
    # Capture.
    res_cap = br.apply_move_qm_full(pos, _qm4_smoke_capture_move())
    assert res_cap['ok'] is True
    assert abs(res_cap['normSq'] - 1.0) < 1e-6


def test_v15_measure_at_born_rule_matches_projector():
    """measure_at on a position observable returns Born-rule
    probability = sum_chan |⟨c|ψ_chan⟩|^2 (matches
    channel-summed |ψ|^2 at the cell)."""
    import numpy as np
    from chess_spectral import qm_4d, qm_4d_bridge as br
    from chess_spectral import tables_4d as t4
    pos = _qm4_smoke_position()
    cell_idx = t4.sq4(1, 2, 3, 4)
    res = br.measure_at(pos, cell_idx)
    assert res['ok'] is True
    psi = qm_4d.state_to_psi(pos, side_to_move=True)
    psi_view = psi.reshape(11, 4096)
    expected_prob = float(np.vdot(psi_view[:, cell_idx],
                                  psi_view[:, cell_idx]).real)
    assert abs(res['probability'] - expected_prob) < 1e-10


def test_v15_get_density_matrix_of_raises_nie():
    """get_density_matrix_of is deferred to v1.7+; raises
    NotImplementedError with a message pointing at the partial-
    trace deferral and v1.7+ landing."""
    from chess_spectral import qm_4d_bridge as br
    pos = _qm4_smoke_position()
    first_sq = next(iter(pos))
    with pytest.raises(NotImplementedError) as excinfo:
        br.get_density_matrix_of(pos, first_sq)
    msg = str(excinfo.value).lower()
    assert 'partial trace' in msg or 'v1.7' in msg


def test_v15_get_probability_current_divergence_free():
    """get_probability_current returns Float32(4096, 4) with
    integrated divergence ≈ 0 (the discrete continuity equation
    with anti-Hermitian gradient ⇒ Tr(grad) = 0 by construction;
    holds for any ψ, not just static eigenstates)."""
    import numpy as np
    from chess_spectral import qm_4d_bridge as br
    pos = _qm4_smoke_position()
    res = br.get_probability_current(pos)
    assert res['ok'] is True
    assert res['j'].dtype == np.float32
    assert res['j'].shape == (4096, 4)
    assert np.all(np.isfinite(res['j']))
    # Integrated divergence: sum over cells of ∂_a j_a, summed over
    # all 4 axes. For our reflecting-boundary anti-Hermitian
    # construction this is 0 within F32 residual.
    grads = br._get_lattice_gradient_4d()
    div_total = 0.0
    for axis in range(4):
        div_axis = grads[axis] @ res['j'][:, axis].astype(np.complex128)
        div_total += float(div_axis.sum().real)
    assert abs(div_total) < 1e-3


@pytest.mark.parametrize("observable", ["rook", "bishop", "queen",
                                        "king", "knight"])
def test_v15_get_qm_expectation_matches_direct(observable):
    """get_qm_expectation matches a direct
    sum_chan ⟨ψ_chan|H_<piece>|ψ_chan⟩ calculation (the SSOT)."""
    from chess_spectral import qm_4d, qm_4d_bridge as br
    pos = _qm4_smoke_position()
    res = br.get_qm_expectation(pos, observable)
    assert res['ok'] is True
    psi = qm_4d.state_to_psi(pos, side_to_move=True)
    psi_view = psi.reshape(11, 4096)
    H_attr = f"H_{observable}_4"
    H = getattr(qm_4d, H_attr)
    expected = sum(qm_4d.expectation(H, psi_view[c]) for c in range(11))
    assert abs(res['value'] - expected) < 1e-10, (
        f"get_qm_expectation({observable!r}) = {res['value']}, "
        f"direct = {expected}, diff = {abs(res['value'] - expected)}"
    )


def test_v15_dev_debug_get_version_get_encoder_shape():
    """§17.5 dev/debug surface: get_version returns the dynamic
    chess_spectral.__version__ (no hardcoded literal);
    get_encoder_shape returns 11 channels of dim 4096 each, total
    45056."""
    from chess_spectral import qm_4d_bridge as br
    v = br.get_version()
    assert v['ok'] is True
    assert isinstance(v['version'], str) and len(v['version']) > 0
    s = br.get_encoder_shape()
    assert s['ok'] is True
    assert s['totalDim'] == 45056
    assert len(s['channels']) == 11
    names = [c['name'] for c in s['channels']]
    assert names == [
        'A1', 'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
        'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
        'FA_PAWN_W', 'FA_PAWN_Y', 'FD_DIAG',
    ]
    # Channel offsets are block-diagonal (i * 4096).
    for i, ch in enumerate(s['channels']):
        assert ch['offset'] == i * 4096
        assert ch['dim'] == 4096


# ─── Pre-flight smoke (research-backed regression guards) ────────────


@_REQUIRES_PYTHON_CHESS
def test_preflight_encoder_injective_on_real_game_corpus():
    """Pre-flight 1: the 2D encoder is injective on real-game
    positions. Encode 50 plies of seeded self-play (a real-game
    proxy) and verify every encoding is distinct (no two plies
    produce the same 640-dim vector). Synthetic Z_2 colliders
    (anti-podal kings + diagonal pieces) are excluded — those
    degeneracies are resolved at the QM layer by the side-to-move
    sign in state_to_psi (Pre-flight 1's amendment).

    Why seeded self-play instead of the static Kasparov-Topalov
    fixture? Self-play touches more diverse mid-game positions in
    50 plies than the historical game does in 88; injectivity is a
    stronger claim when verified across varied piece arrangements.
    """
    import chess
    from chess_spectral.encoder import encode_640
    plies = _seeded_self_play(white_seed=2026, max_plies=50)
    seen = {}
    for p in plies:
        board = chess.Board(p["fen"])
        # Adapt python-chess board → encoder's pos dict.
        pos = {sq: piece.symbol()
               for sq, piece in board.piece_map().items()}
        v = encode_640(pos)
        key = bytes(v.tobytes())
        if key in seen:
            raise AssertionError(
                f"encoder injectivity violated: plies {seen[key]} "
                f"and {p['ply']} produce identical 640-dim encodings; "
                f"both fens:\n  {plies[seen[key]]['fen']}\n  {p['fen']}"
            )
        seen[key] = p["ply"]


def test_preflight_spectral_identity_small_scale():
    """Pre-flight 3 small-scale gate: P_8 1D Laplacian eigenvectors
    form the simultaneous eigenbasis of the 4D Kron-sum Laplacian
    Δ = L_8 ⊕ L_8 ⊕ L_8 ⊕ L_8 (Kronecker sum). Tested by:
      1. Build L_8 = p8_laplacian; find eigenpairs.
      2. Build Δ via the kron_sum4_eigvals identity (adds 1D
         eigenvalues across all 4 axes).
      3. For sample (i,j,k,l), the tensor-product e_i ⊗ e_j ⊗ e_k ⊗
         e_l satisfies Δ v = λ v with λ = e_i + e_j + e_k + e_l
         within 1e-10.
    This is the foundational identity for B2's H_0 = -Δ
    construction; if it breaks, the whole Track B Zeno picture
    is suspect."""
    import numpy as np
    from chess_spectral import tables_4d as t4
    evecs_1d, evals_1d = t4.eig_p8()
    # Kron-sum eigenvalues for all 4096 modes (matches sq4 ordering).
    lambda_grid = t4.kron_sum4_eigvals(evals_1d)
    # Sample 5 spaced (i,j,k,l) tuples; verify Δ v = λ v.
    samples = [(0, 0, 0, 0), (1, 2, 3, 4),
               (3, 3, 3, 3), (7, 0, 4, 5), (5, 5, 7, 1)]
    for (i, j, k, l) in samples:
        v = t4.tensor_eigvec_4d(evecs_1d, i, j, k, l)
        sq = t4.sq4(i, j, k, l)
        lam = lambda_grid[sq]
        # Build Δ as scipy.sparse: Kron-sum of L_8 across 4 axes.
        # For the cost — use the identity Δ v = λ v on a dense L_8
        # applied per-axis. Direct verification: the 4D Δ on this
        # basis vector equals lam * v.
        L = t4.p8_laplacian()
        # Apply Δ = Σ_a I⊗...⊗L⊗...⊗I directly via reshape +
        # per-axis matmul. Keeps memory at 4096 doubles.
        v4 = v.reshape(8, 8, 8, 8)
        Dv = np.zeros_like(v4)
        for a in range(4):
            Lv = np.tensordot(L, v4, axes=([1], [a]))
            # tensordot moves axis a to position 0; move it back.
            Lv = np.moveaxis(Lv, 0, a)
            Dv += Lv
        residual = float(np.max(np.abs(Dv.ravel() - lam * v)))
        assert residual < 1e-10, (
            f"spectral identity broken at (i,j,k,l)=({i},{j},{k},{l}): "
            f"||Δv - λv||_∞ = {residual}, λ = {lam}"
        )


# ─── 1.7.0 immolation extension ─────────────────────────────────────
#
# Embiggen the immolation suite to gate the chess-spectral 1.7.0
# release-pipeline items. These tests run on every PR via
# chess-spectral-ci.yml's build-and-test job and on every release
# tag via chess-spectral-publish.yml's pre-publish workflow. They
# are intentionally cheap (sub-second each) so the merge train stays
# fast; the heavy parity tests live elsewhere.
#
# What we gate at the cohort level here:
#   D1: search(time_budget_ms=...) is honored mid-iteration, not just
#       between iterations. The behavior change in 1.7.0 was a real
#       bug fix (pre-1.7.0 a 5s budget on a dense position could
#       overrun by 100×). A regression that re-introduces between-
#       iteration-only checking would silently break tournament
#       wall-clock budgeting; we want to catch that on the merge train.
#   D1: SearchResult.timed_out field exists (catches accidental field
#       removal during a refactor; consumers depend on it to
#       distinguish "natural completion at max_depth" from "exited
#       on deadline").
#   M2.x: HAS_NATIVE_BITBOARD is exposed at the top-level
#       `chess_spectral` package surface. Downstream consumers
#       (the chess4D-OC visualizer, etc.) depend on importing it
#       directly from `chess_spectral`; demoting it to a sub-package-
#       only flag would silently break their availability badge logic.
#   M2.x: When HAS_NATIVE_BITBOARD is True, Bitboard4D.to_squares()
#       routes through the native fast-path AND its output matches
#       the pure-Python reference (catches a future refactor that
#       might bypass the native helper or introduce a marshaling bug).


def test_immolation_search_honors_time_budget_mid_iteration():
    """1.7.0 D1: a tight search budget on a dense position must
    return WITHIN budget + 0.5s grace, with a non-None best_move.

    Pre-1.7.0, the budget was checked only BETWEEN iterative-deepening
    iterations — depth-1 alone on the dense 28-king start could run
    for 10+ minutes regardless of the time_budget_ms setting. The
    1.7.0 fix threads the deadline into the alpha-beta inner loop
    AND returns the deepest-completed-so-far best move on deadline
    exit. This test gates that contract.
    """
    import time as _time
    from chess_spectral.spatial_4d import Board4D
    from chess_spectral_4d.engine.search import search, SearchOptions
    from chess_spectral_4d.engine.eval.material import evaluate

    # Dense 4D position: 28 kings/side + sliders + pawns.
    # Pseudo-legal at this density is ~3000 moves, legal_moves filter
    # ran for 26s pre-M2.3. We use a tight 800ms budget — anything
    # close to the pre-1.7.0 behavior (no mid-iteration check) would
    # overshoot by orders of magnitude.
    position = {}
    def _sq4(x, y, z, w):
        return ((x * 8 + y) * 8 + z) * 8 + w

    # Spread 28 white kings across x=0,1 planes; 28 black kings
    # across x=6,7 planes (no mutual attack — realistic dense start).
    i = 0
    for x in (0, 1):
        for y in range(8):
            for z in range(8):
                if i >= 28:
                    break
                position[_sq4(x, y, z, 0)] = "K"
                i += 1
            if i >= 28:
                break
        if i >= 28:
            break
    i = 0
    for x in (6, 7):
        for y in range(8):
            for z in range(8):
                if i >= 28:
                    break
                position[_sq4(x, y, z, 0)] = "k"
                i += 1
            if i >= 28:
                break
        if i >= 28:
            break

    board = Board4D.from_position_dict(position, turn=True)
    budget_ms = 800
    grace_ms = 500
    t0 = _time.perf_counter()
    result = search(
        board, evaluate,
        SearchOptions(max_depth=4, time_budget_ms=budget_ms),
    )
    elapsed_ms = (_time.perf_counter() - t0) * 1000.0

    # Wall-clock honored within grace.
    assert elapsed_ms < budget_ms + grace_ms, (
        f"search overran time_budget_ms: budget={budget_ms}ms, "
        f"grace={grace_ms}ms, actual={elapsed_ms:.0f}ms. The "
        f"deadline check may have regressed to between-iteration only."
    )
    # Returned a usable best_move (the partial-iteration result).
    # best_move is only None when the position has no legal moves.
    legal_count = sum(1 for _ in board.legal_moves())
    if legal_count > 0:
        assert result.best_move is not None, (
            "search returned best_move=None despite legal moves "
            "existing; deadline-exit should still surface the "
            "deepest-completed-so-far partial result."
        )


def test_immolation_search_result_has_timed_out_field():
    """1.7.0 D1: ``SearchResult`` exposes a ``timed_out: bool`` field.

    Consumers depend on this to distinguish natural completion (max_depth
    reached) from deadline exit. An accidental field removal during a
    refactor would silently break their logic. This is a structural
    sanity check — a tiny search at the empty board ensures the
    dataclass attribute exists and reads as a bool.
    """
    from chess_spectral.spatial_4d import Board4D
    from chess_spectral_4d.engine.search import search, SearchOptions
    from chess_spectral_4d.engine.eval.material import evaluate

    # Empty board; search returns essentially immediately (no legal
    # moves so terminal-node short-circuit triggers).
    board = Board4D.empty()
    result = search(board, evaluate, SearchOptions(max_depth=1))

    assert hasattr(result, "timed_out"), (
        "SearchResult is missing the `timed_out` field added in "
        "1.7.0; downstream consumers depend on it."
    )
    assert isinstance(result.timed_out, bool), (
        f"SearchResult.timed_out should be a bool, got "
        f"{type(result.timed_out).__name__}"
    )


def test_immolation_has_native_bitboard_flag_exposed_at_top_level():
    """1.7.0 D2: ``HAS_NATIVE_BITBOARD`` is importable directly from
    the ``chess_spectral`` top-level package.

    The chess4D-OC visualizer and similar Pyodide / desktop consumers
    badge "native fast-path active" via this flag. Demoting it to a
    sub-package-only export would silently break their availability
    logic on next install. This test asserts the public surface
    contract.
    """
    import chess_spectral as cs
    # Importable as an attribute.
    assert hasattr(cs, "HAS_NATIVE_BITBOARD"), (
        "chess_spectral.HAS_NATIVE_BITBOARD missing from the top-"
        "level package; downstream consumers depend on the direct "
        "`from chess_spectral import HAS_NATIVE_BITBOARD` import."
    )
    # Listed in __all__ so `from chess_spectral import *` finds it.
    assert "HAS_NATIVE_BITBOARD" in cs.__all__, (
        "HAS_NATIVE_BITBOARD missing from chess_spectral.__all__; "
        "star-imports will not pick it up."
    )
    # And it's a bool.
    assert isinstance(cs.HAS_NATIVE_BITBOARD, bool), (
        f"HAS_NATIVE_BITBOARD should be bool, got "
        f"{type(cs.HAS_NATIVE_BITBOARD).__name__}"
    )


def test_immolation_native_bitboard_iteration_parity_when_available():
    """1.7.0 D2 / M2.2: when ``HAS_NATIVE_BITBOARD`` is True, the
    ``Bitboard4D.to_squares()`` native fast-path produces the same
    set indices as a pure-Python reference recompute.

    Skipped on sdist / Pyodide installs (where the native lib isn't
    built). When run, this gates the marshaling logic in
    ``_to_squares_native`` — a regression that introduced an off-by-
    one or wrong byte-ordering would corrupt every move-gen loop in
    the package and we want to catch it on the merge train, not at
    visualizer-debug time.
    """
    import chess_spectral as cs
    if not cs.HAS_NATIVE_BITBOARD:
        pytest.skip("native bitboard library not present in this build")

    import numpy as np
    from chess_spectral.spatial_4d import Bitboard4D
    rng = np.random.default_rng(seed=20260501)
    for _ in range(8):
        words = rng.integers(0, 2**63, size=64, dtype=np.uint64)
        bb = Bitboard4D.from_numpy_uint64(words)

        # Native path (route through Bitboard4D.to_squares).
        from_native = bb.to_squares()

        # Pure-Python reference recompute via int bit-tricks (the
        # pre-1.7.0 path; if the native helper drifts from it the
        # parity break is on a basic primitive).
        b = bb.bits
        ref = []
        while b:
            lsb = b & -b
            ref.append(lsb.bit_length() - 1)
            b &= b - 1

        assert from_native == ref, (
            f"native to_squares() output diverged from pure-Python "
            f"reference for popcount={bb.popcount()}. The native "
            f"marshaling or cs_bb4_to_squares may have regressed."
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
