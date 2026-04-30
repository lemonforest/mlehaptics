"""End-to-end tests for the search + tournament CLI commands.

Covers both the 2D (chess_spectral.cli) and 4D (chess_spectral_4d.cli)
sides, with the same agent-spec syntax across dimensions. The test
that demonstrates per-side asymmetric configuration is the §16
ship-gate property: white can be one (evaluator, depth) and black
another, in the same single-process tournament.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
sys.path.insert(0, str(PY_DIR))

from chess_spectral.cli import main as main_2d  # noqa: E402
from chess_spectral_4d.cli import main as main_4d  # noqa: E402


# ─── 2D search ──────────────────────────────────────────────────────


def _capture_stdout_2d(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main_2d(argv)
    return rc, buf.getvalue()


def test_2d_search_default_starting_position():
    rc, out = _capture_stdout_2d([
        "search", "--agent", "evaluator=material,depth=1",
    ])
    assert rc == 0
    assert "best:" in out
    assert "depth: 1" in out


def test_2d_search_explicit_fen():
    rc, out = _capture_stdout_2d([
        "search",
        "--fen", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "--agent", "label=alpha,evaluator=material,depth=1",
    ])
    assert rc == 0
    assert "agent: alpha" in out


def test_2d_search_json_output():
    rc, out = _capture_stdout_2d([
        "search",
        "--agent", "evaluator=material,depth=1",
        "--json",
    ])
    assert rc == 0
    data = json.loads(out)
    assert data["agent"] == "material@1"
    assert data["depth_reached"] == 1
    assert data["best_move"] is not None  # opening position has legal moves
    assert isinstance(data["nodes_searched"], int)


def test_2d_search_supports_qm_evaluator():
    rc, out = _capture_stdout_2d([
        "search",
        "--agent", "evaluator=qm,depth=1",
        "--json",
    ])
    assert rc == 0
    data = json.loads(out)
    assert data["agent"] == "qm@1"


def test_2d_search_supports_spectral_evaluator():
    rc, out = _capture_stdout_2d([
        "search",
        "--agent", "evaluator=spectral,depth=1",
        "--json",
    ])
    assert rc == 0
    data = json.loads(out)
    assert data["agent"] == "spectral@1"


def test_2d_search_ablations_disable_features():
    """Disabling all ablations should still find a move (search core
    handles each independently)."""
    rc, out = _capture_stdout_2d([
        "search",
        "--agent",
        "evaluator=material,depth=2,no_tt,no_mvv_lva,no_quiescence",
        "--json",
    ])
    assert rc == 0
    data = json.loads(out)
    assert data["best_move"] is not None
    # TT off → no tt entries logged
    assert data["tt_size"] == 0


# ─── 2D tournament ──────────────────────────────────────────────────


def test_2d_tournament_two_agents_minimal():
    rc, out = _capture_stdout_2d([
        "tournament",
        "--agent", "label=A,evaluator=material,depth=1",
        "--agent", "label=B,evaluator=material,depth=2",
        "--n-games-per-pair", "1",
        "--max-plies", "10",
    ])
    assert rc == 0
    data = json.loads(out)
    assert set(data["agents"]) == {"A", "B"}
    assert data["n_games_per_pair"] == 1
    assert "elo" in data
    assert "pair_records" in data
    assert len(data["games"]) == 1


def test_2d_tournament_white_and_black_can_be_different_evaluators():
    """The §16 use case: pit material@1 vs spectral@1 for one game."""
    rc, out = _capture_stdout_2d([
        "tournament",
        "--agent", "label=mat,evaluator=material,depth=1",
        "--agent", "label=spec,evaluator=spectral,depth=1",
        "--n-games-per-pair", "1",
        "--max-plies", "8",
    ])
    assert rc == 0
    data = json.loads(out)
    # The single game has one of {mat, spec} as white and the other as black.
    g = data["games"][0]
    assert {g["white"], g["black"]} == {"mat", "spec"}


def test_2d_tournament_rejects_single_agent():
    rc, out = _capture_stdout_2d([
        "tournament",
        "--agent", "evaluator=material,depth=1",
        "--n-games-per-pair", "1",
    ])
    assert rc == 2


def test_2d_tournament_writes_to_output_file(tmp_path):
    out_path = tmp_path / "tournament.json"
    rc, _stdout = _capture_stdout_2d([
        "tournament",
        "--agent", "label=A,evaluator=material,depth=1",
        "--agent", "label=B,evaluator=material,depth=1",
        "--n-games-per-pair", "1",
        "--max-plies", "6",
        "-o", str(out_path),
    ])
    assert rc == 0
    assert out_path.is_file()
    data = json.loads(out_path.read_text())
    assert "elo" in data
    assert len(data["games"]) >= 1


# ─── 4D search ──────────────────────────────────────────────────────


def _capture_stdout_4d(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main_4d(argv)
    return rc, buf.getvalue()


_TWO_KINGS_FEN4 = "4d-fen v1: K@0,0,0,0; k@7,7,7,7"


def test_4d_search_two_kings_fen4():
    rc, out = _capture_stdout_4d([
        "search",
        "--fen4", _TWO_KINGS_FEN4,
        "--agent", "evaluator=material,depth=1",
    ])
    assert rc == 0
    assert "best:" in out
    assert "->" in out  # 4D move format includes -> arrow


def test_4d_search_requires_fen4():
    """4D has no canonical starting position — fen4 is required.
    argparse rejects the missing required arg with SystemExit(2)."""
    with pytest.raises(SystemExit) as exc_info:
        main_4d(["search", "--agent", "evaluator=material,depth=1"])
    assert exc_info.value.code == 2


def test_4d_search_json_output():
    rc, out = _capture_stdout_4d([
        "search",
        "--fen4", _TWO_KINGS_FEN4,
        "--agent", "evaluator=material,depth=1",
        "--json",
    ])
    assert rc == 0
    data = json.loads(out)
    assert data["agent"] == "material@1"
    assert data["depth_reached"] == 1


# ─── 4D tournament ──────────────────────────────────────────────────


def test_4d_tournament_minimal(tmp_path):
    """A 1-ply, 1-game-per-pair 4D tournament smoke test. Uses two
    kings on opposite corners so move-gen is fast."""
    out_path = tmp_path / "t4d.json"
    rc, _stdout = _capture_stdout_4d([
        "tournament",
        "--start-fen4", _TWO_KINGS_FEN4,
        "--agent", "label=A,evaluator=material,depth=1",
        "--agent", "label=B,evaluator=material,depth=1",
        "--n-games-per-pair", "1",
        "--max-plies", "4",
        "-o", str(out_path),
    ])
    assert rc == 0
    assert out_path.is_file()
    data = json.loads(out_path.read_text())
    assert data["n_games_per_pair"] == 1
    assert data["start_fen4"] == _TWO_KINGS_FEN4
    assert set(data["agents"]) == {"A", "B"}


def test_4d_tournament_white_black_different_evaluators(tmp_path):
    """The §16 4D analogue: per-side asymmetric configuration works."""
    out_path = tmp_path / "t4d_mixed.json"
    rc, _ = _capture_stdout_4d([
        "tournament",
        "--start-fen4", _TWO_KINGS_FEN4,
        "--agent", "label=mat,evaluator=material,depth=1",
        "--agent", "label=qm,evaluator=qm,depth=1",
        "--n-games-per-pair", "1",
        "--max-plies", "4",
        "-o", str(out_path),
    ])
    assert rc == 0
    data = json.loads(out_path.read_text())
    g = data["games"][0]
    assert {g["white"], g["black"]} == {"mat", "qm"}
