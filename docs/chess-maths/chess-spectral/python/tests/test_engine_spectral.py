"""Unit tests for the spectral channel-energy evaluators (PR-3).

Covers both :mod:`chess_spectral.engine.eval.spectral` (2D) and
:mod:`chess_spectral_4d.engine.eval.spectral` (4D). Same patterns:

  * Channel energies sum to ||v||^2 (Plancherel sanity)
  * Empty position scores 0
  * Non-empty position scores positive (energy is non-negative)
  * Side-to-move sign flip negates the score
  * Default weights produce equal-channel weighting (sum = total energy)
  * Custom weights dict re-weights correctly
  * load_weights_json with valid file works
  * load_weights_json with unknown channel name raises ValueError
  * evaluate_breakdown sums to evaluate
  * 4D-specific: pawn axis affects encoding (FA_PAWN_W vs FA_PAWN_Y
    channels populate differently for w-axis vs y-axis pawns)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import fen_to_pos, encode_640                  # noqa: E402
from chess_spectral.engine.eval import spectral as spectral_2d     # noqa: E402
from chess_spectral_4d.engine.eval import spectral as spectral_4d  # noqa: E402
from chess_spectral.encoder_4d import encode_4d                    # noqa: E402
from chess_spectral.fen_4d import parse as parse_fen4              # noqa: E402


# ---- 2D fixtures ----------------------------------------------------


@pytest.fixture(scope="module")
def starting_2d():
    return fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )


@pytest.fixture(scope="module")
def midgame_2d():
    """Mid-game position from Kasparov-Topalov 1999."""
    return fen_to_pos(
        "r4rk1/ppq1bppp/2n2n2/3p4/3P4/2N1BN2/PPQ1BPPP/R4RK1 w - - 0 1"
    )


# ---- 2D channel energies ----------------------------------------


def test_2d_channel_energies_plancherel(starting_2d):
    """Sum of per-channel L2 energies equals ||v||^2 -- the encoder is
    a straight basis transform, no Plancherel breakage."""
    v = encode_640(starting_2d).astype(np.float64)
    energies = spectral_2d.channel_energies(v)
    total = sum(energies.values())
    norm_sq = float(np.vdot(v, v).real)
    assert total == pytest.approx(norm_sq, rel=1e-12)


def test_2d_channel_energies_shape_check():
    """channel_energies on wrong-shape input raises."""
    with pytest.raises(ValueError):
        spectral_2d.channel_energies(np.zeros(641))
    with pytest.raises(ValueError):
        spectral_2d.channel_energies(np.zeros((10, 64)))


def test_2d_channel_energies_returns_all_channels(starting_2d):
    """Every channel name is in the output, even if its energy is 0."""
    v = encode_640(starting_2d).astype(np.float64)
    energies = spectral_2d.channel_energies(v)
    assert set(energies) == {
        'A1', 'A2', 'B1', 'B2', 'E', 'F1', 'F2', 'F3', 'FA', 'FD'
    }


def test_2d_channel_energies_non_negative(starting_2d, midgame_2d):
    """L2 energies are always non-negative."""
    for pos in (starting_2d, midgame_2d):
        v = encode_640(pos).astype(np.float64)
        energies = spectral_2d.channel_energies(v)
        for name, e in energies.items():
            assert e >= 0.0, f"{name}: energy {e} should be >= 0"


# ---- 2D evaluate ----------------------------------------------------


def test_2d_empty_position_scores_zero():
    """Encoder returns zero vector for empty position -> 0 score."""
    assert spectral_2d.evaluate({}, side_to_move=True) == 0.0
    assert spectral_2d.evaluate({}, side_to_move=False) == 0.0


def test_2d_non_empty_score_positive(starting_2d):
    """For default weights, score equals total energy = positive."""
    score = spectral_2d.evaluate(starting_2d, side_to_move=True)
    assert score > 0.0


def test_2d_side_to_move_flip(starting_2d):
    """White-to-move and black-to-move differ only in sign."""
    s_w = spectral_2d.evaluate(starting_2d, side_to_move=True)
    s_b = spectral_2d.evaluate(starting_2d, side_to_move=False)
    assert s_w == -s_b


def test_2d_default_weights_equal_total_energy(starting_2d):
    """With all weights = 1.0, score equals sum of channel energies."""
    v = encode_640(starting_2d).astype(np.float64)
    energies = spectral_2d.channel_energies(v)
    expected = sum(energies.values())
    score = spectral_2d.evaluate(starting_2d, side_to_move=True)
    assert score == pytest.approx(expected, rel=1e-12)


def test_2d_custom_weights_dict_reweights(starting_2d):
    """Custom weights re-scale channel contributions."""
    weights = {
        'A1': 0.0, 'A2': 0.0, 'B1': 0.0, 'B2': 0.0, 'E': 0.0,
        'F1': 0.0, 'F2': 0.0, 'F3': 0.0,
        'FA': 1.0, 'FD': 0.0,
    }
    score = spectral_2d.evaluate(starting_2d, side_to_move=True,
                                   weights=weights)
    v = encode_640(starting_2d).astype(np.float64)
    energies = spectral_2d.channel_energies(v)
    # Score should equal exactly FA channel's energy.
    assert score == pytest.approx(energies['FA'], rel=1e-12)


def test_2d_partial_weights_default_to_one(starting_2d):
    """Channels missing from the weights dict default to 1.0."""
    weights = {'A1': 2.0}   # only A1 specified; others default 1.0
    score = spectral_2d.evaluate(starting_2d, side_to_move=True,
                                   weights=weights)
    v = encode_640(starting_2d).astype(np.float64)
    energies = spectral_2d.channel_energies(v)
    expected = (
        2.0 * energies['A1']
        + sum(energies[c] for c in energies if c != 'A1')
    )
    assert score == pytest.approx(expected, rel=1e-12)


def test_2d_load_weights_json_roundtrip(starting_2d):
    """Write weights to JSON, load, evaluate -- score matches a
    direct dict-pass."""
    weights = {
        'A1': 0.5, 'A2': 0.5, 'B1': 0.3, 'B2': 0.3, 'E': 0.8,
        'F1': 0.4, 'F2': 0.4, 'F3': 0.4, 'FA': 0.6, 'FD': 0.7,
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump(weights, f)
        path = f.name
    try:
        loaded = spectral_2d.load_weights_json(path)
        assert loaded == weights
        score_dict = spectral_2d.evaluate(starting_2d,
                                           side_to_move=True,
                                           weights=weights)
        score_path = spectral_2d.evaluate(starting_2d,
                                           side_to_move=True,
                                           weights=path)
        assert score_dict == score_path
    finally:
        os.unlink(path)


def test_2d_load_weights_json_unknown_channel_raises():
    """Typo in channel name in JSON file raises ValueError -- catches
    silent miss-tunings before they hit production."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump({'A99': 1.0, 'A1': 0.5}, f)   # 'A99' is bogus
        path = f.name
    try:
        with pytest.raises(ValueError) as ei:
            spectral_2d.load_weights_json(path)
        assert 'A99' in str(ei.value)
    finally:
        os.unlink(path)


def test_2d_load_weights_json_non_dict_raises():
    """JSON file containing a list / string raises."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump([1, 2, 3], f)
        path = f.name
    try:
        with pytest.raises(ValueError):
            spectral_2d.load_weights_json(path)
    finally:
        os.unlink(path)


def test_2d_breakdown_sums_to_evaluate(starting_2d):
    """sum(evaluate_breakdown(...)) == evaluate(...)."""
    weights = {'A1': 1.5, 'FD': 0.5}
    score = spectral_2d.evaluate(starting_2d, side_to_move=True,
                                  weights=weights)
    breakdown = spectral_2d.evaluate_breakdown(starting_2d,
                                                 side_to_move=True,
                                                 weights=weights)
    assert sum(breakdown.values()) == pytest.approx(score, rel=1e-12)


def test_2d_breakdown_side_to_move_flips_sign(starting_2d):
    """All breakdown values flip sign together when side_to_move flips."""
    bw = spectral_2d.evaluate_breakdown(starting_2d, side_to_move=True)
    bb = spectral_2d.evaluate_breakdown(starting_2d, side_to_move=False)
    for c in bw:
        assert bw[c] == -bb[c]


# ---- 4D fixtures ----------------------------------------------------


@pytest.fixture(scope="module")
def starting_4d_kings_only():
    """Two kings at non-antipodal positions. Anti-podal kings sit in
    the kernel of the encoder's central inversion symmetry (Pre-flight
    1) and produce a zero vector -- not useful as a non-empty test
    fixture. Use offset positions instead."""
    return parse_fen4("4d-fen v1: K@0,0,0,0; k@5,4,3,2")


@pytest.fixture(scope="module")
def w_axis_pawn_4d():
    return parse_fen4("4d-fen v1: K@0,0,0,0; k@7,7,7,7; Pw@1,1,1,1")


@pytest.fixture(scope="module")
def y_axis_pawn_4d():
    return parse_fen4("4d-fen v1: K@0,0,0,0; k@7,7,7,7; Py@1,1,1,1")


# ---- 4D channel energies + evaluator -------------------------------


def test_4d_channel_energies_plancherel(starting_4d_kings_only):
    """4D Plancherel sanity: sum of channel energies == ||v||^2."""
    v = encode_4d(starting_4d_kings_only).astype(np.float64)
    energies = spectral_4d.channel_energies(v)
    total = sum(energies.values())
    norm_sq = float(np.vdot(v, v).real)
    assert total == pytest.approx(norm_sq, rel=1e-12)


def test_4d_channel_energies_returns_all_channels(starting_4d_kings_only):
    v = encode_4d(starting_4d_kings_only).astype(np.float64)
    energies = spectral_4d.channel_energies(v)
    assert set(energies) == {
        'A1', 'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
        'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
        'FA_PAWN_W', 'FA_PAWN_Y', 'FD_DIAG',
    }


def test_4d_empty_position_scores_zero():
    """Empty 4D position scores 0."""
    assert spectral_4d.evaluate({}, side_to_move=True) == 0.0


def test_4d_non_empty_score_positive(starting_4d_kings_only):
    """Non-empty position scores positive with default weights."""
    score = spectral_4d.evaluate(starting_4d_kings_only,
                                  side_to_move=True)
    assert score > 0.0


def test_4d_side_to_move_flip(starting_4d_kings_only):
    s_w = spectral_4d.evaluate(starting_4d_kings_only, side_to_move=True)
    s_b = spectral_4d.evaluate(starting_4d_kings_only, side_to_move=False)
    assert s_w == -s_b


def test_4d_pawn_axis_distinguishes_channels(w_axis_pawn_4d,
                                                y_axis_pawn_4d):
    """A W-axis pawn populates FA_PAWN_W; a Y-axis pawn populates
    FA_PAWN_Y. Same-position-with-different-axis pawns produce
    different channel-energy profiles even though the king positions
    are identical."""
    v_w = encode_4d(w_axis_pawn_4d).astype(np.float64)
    v_y = encode_4d(y_axis_pawn_4d).astype(np.float64)
    energies_w = spectral_4d.channel_energies(v_w)
    energies_y = spectral_4d.channel_energies(v_y)
    # FA_PAWN_W has energy from the w-pawn but not the y-pawn.
    # FA_PAWN_Y has energy from the y-pawn but not the w-pawn.
    # (At least one of these inequalities must hold; the encoder
    # routes pawn axis to the matching FA_PAWN channel.)
    assert energies_w['FA_PAWN_W'] != energies_y['FA_PAWN_W']
    assert energies_w['FA_PAWN_Y'] != energies_y['FA_PAWN_Y']


def test_4d_custom_weights_zero_out_channels(w_axis_pawn_4d):
    weights = {name: 0.0 for name, _ in __import__(
        'chess_spectral.encoder_4d', fromlist=['CHANNELS_4D']
    ).CHANNELS_4D}
    weights['FD_DIAG'] = 1.0
    score = spectral_4d.evaluate(w_axis_pawn_4d, side_to_move=True,
                                   weights=weights)
    v = encode_4d(w_axis_pawn_4d).astype(np.float64)
    energies = spectral_4d.channel_energies(v)
    assert score == pytest.approx(energies['FD_DIAG'], rel=1e-12)


def test_4d_load_weights_json_unknown_channel_raises():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump({'A1': 1.0, 'NOT_A_CHANNEL': 0.5}, f)
        path = f.name
    try:
        with pytest.raises(ValueError) as ei:
            spectral_4d.load_weights_json(path)
        assert 'NOT_A_CHANNEL' in str(ei.value)
    finally:
        os.unlink(path)


def test_4d_breakdown_sums_to_evaluate(starting_4d_kings_only):
    weights = {'A1': 2.0, 'FD_DIAG': 0.5}
    score = spectral_4d.evaluate(starting_4d_kings_only,
                                  side_to_move=True,
                                  weights=weights)
    breakdown = spectral_4d.evaluate_breakdown(
        starting_4d_kings_only, side_to_move=True, weights=weights
    )
    assert sum(breakdown.values()) == pytest.approx(score, rel=1e-12)


# ---- API surface ----------------------------------------------------


def test_2d_module_public_api():
    for name in ('evaluate', 'evaluate_breakdown', 'channel_energies',
                 'load_weights_json', 'DEFAULT_WEIGHTS'):
        assert name in spectral_2d.__all__


def test_4d_module_public_api():
    for name in ('evaluate', 'evaluate_breakdown', 'channel_energies',
                 'load_weights_json', 'DEFAULT_WEIGHTS_4D'):
        assert name in spectral_4d.__all__


def test_engine_namespace_re_exports_spectral():
    """chess_spectral.engine.eval includes spectral; same for 4D."""
    from chess_spectral.engine import eval as eval_2d
    from chess_spectral_4d.engine import eval as eval_4d
    assert hasattr(eval_2d, 'spectral')
    assert hasattr(eval_4d, 'spectral')
