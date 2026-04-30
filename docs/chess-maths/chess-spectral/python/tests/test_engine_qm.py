"""Unit tests for the QM-expectation evaluators (PR-4).

Covers both :mod:`chess_spectral.engine.eval.qm` (2D) and
:mod:`chess_spectral_4d.engine.eval.qm` (4D). Same patterns:

  * Empty position scores 0
  * Non-empty position returns a real-valued score
  * Side-to-move sign flip negates the score
  * Default weights produce a finite real
  * Custom weights dict re-weights correctly
  * load_weights_json round-trip; unknown observable raises
  * evaluate_breakdown sums to evaluate
  * observable_expectations: real-valued (Hermitian H)
  * observable_expectations: shape mismatch raises
  * Anti-podal kings (encoder kernel) score 0 by graceful empty fallback
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import fen_to_pos, qm_2d                       # noqa: E402
from chess_spectral.engine.eval import qm as qm_eval_2d            # noqa: E402
from chess_spectral_4d.engine.eval import qm as qm_eval_4d         # noqa: E402
from chess_spectral.fen_4d import parse as parse_fen4              # noqa: E402


# ---- 2D fixtures ----------------------------------------------------


@pytest.fixture(scope="module")
def starting_2d():
    return fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )


@pytest.fixture(scope="module")
def midgame_2d():
    return fen_to_pos(
        "r4rk1/ppq1bppp/2n2n2/3p4/3P4/2N1BN2/PPQ1BPPP/R4RK1 w - - 0 1"
    )


# ---- 2D observable_expectations -------------------------------------


def test_2d_observable_expectations_keys(starting_2d):
    """Output dict has all 5 piece names exactly."""
    psi = qm_2d.state_to_psi(starting_2d, side_to_move=True)
    out = qm_eval_2d.observable_expectations(psi)
    assert set(out) == {'rook', 'bishop', 'queen', 'king', 'knight'}


def test_2d_observable_expectations_real_valued(midgame_2d):
    """All expectations are real-valued floats (Hermitian H -> real
    expectation values)."""
    psi = qm_2d.state_to_psi(midgame_2d, side_to_move=True)
    out = qm_eval_2d.observable_expectations(psi)
    for piece, val in out.items():
        assert isinstance(val, float), f"{piece} expectation not float"


def test_2d_observable_expectations_shape_mismatch_raises():
    """Wrong-shape psi raises ValueError."""
    bad = np.zeros(641, dtype=np.complex128)
    with pytest.raises(ValueError):
        qm_eval_2d.observable_expectations(bad)


def test_2d_observable_expectations_zero_psi_zero_values():
    """Zero psi -> zero expectations across all pieces."""
    zero_psi = np.zeros(640, dtype=np.complex128)
    out = qm_eval_2d.observable_expectations(zero_psi)
    for v in out.values():
        assert v == 0.0


# ---- 2D evaluate ----------------------------------------------------


def test_2d_empty_position_scores_zero():
    """Empty position has zero psi -> 0 score."""
    assert qm_eval_2d.evaluate({}, side_to_move=True) == 0.0
    assert qm_eval_2d.evaluate({}, side_to_move=False) == 0.0


def test_2d_non_empty_score_is_finite_real(starting_2d):
    """Non-empty position scores a finite real."""
    score = qm_eval_2d.evaluate(starting_2d, side_to_move=True)
    assert isinstance(score, float)
    assert np.isfinite(score)


def test_2d_side_to_move_flip(starting_2d):
    """White-to-move and black-to-move differ only in score sign.

    Note: state_to_psi multiplies psi by +/-1 depending on
    side_to_move (Z_2 sector). Expectation values <psi|H|psi> are
    unchanged under psi -> -psi (sign cancels in the inner product).
    The score sign flip therefore comes entirely from evaluate's
    explicit side-to-move sign handling, not from state_to_psi's
    Z_2 mechanism."""
    s_w = qm_eval_2d.evaluate(starting_2d, side_to_move=True)
    s_b = qm_eval_2d.evaluate(starting_2d, side_to_move=False)
    assert s_w == pytest.approx(-s_b, rel=1e-12)


def test_2d_default_weights_sum_observables(starting_2d):
    """Default weights == 1 for all 5 pieces -> score == sum of
    all 5 observable expectations."""
    score = qm_eval_2d.evaluate(starting_2d, side_to_move=True)
    psi = qm_2d.state_to_psi(starting_2d, side_to_move=True)
    expectations = qm_eval_2d.observable_expectations(psi)
    expected = sum(expectations.values())
    assert score == pytest.approx(expected, rel=1e-12)


def test_2d_custom_weights_dict(starting_2d):
    """Custom weights re-scale observable contributions."""
    weights = {
        'rook': 0.0, 'bishop': 0.0, 'queen': 0.0, 'king': 0.0,
        'knight': 1.0,   # only knight contributes
    }
    score = qm_eval_2d.evaluate(starting_2d, side_to_move=True,
                                  weights=weights)
    psi = qm_2d.state_to_psi(starting_2d, side_to_move=True)
    expectations = qm_eval_2d.observable_expectations(psi)
    assert score == pytest.approx(expectations['knight'], rel=1e-12)


def test_2d_partial_weights_default_to_one(starting_2d):
    """Pieces missing from weights default to 1.0."""
    weights = {'rook': 2.0}   # only rook specified
    score = qm_eval_2d.evaluate(starting_2d, side_to_move=True,
                                  weights=weights)
    psi = qm_2d.state_to_psi(starting_2d, side_to_move=True)
    expectations = qm_eval_2d.observable_expectations(psi)
    expected = (
        2.0 * expectations['rook']
        + sum(v for k, v in expectations.items() if k != 'rook')
    )
    assert score == pytest.approx(expected, rel=1e-12)


def test_2d_load_weights_json_roundtrip(starting_2d):
    """JSON roundtrip and direct dict produce same score."""
    weights = {
        'rook': 1.5, 'bishop': 0.8, 'queen': 1.2,
        'king': 0.5, 'knight': 0.9,
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump(weights, f)
        path = f.name
    try:
        loaded = qm_eval_2d.load_weights_json(path)
        assert loaded == weights
        s_dict = qm_eval_2d.evaluate(starting_2d, side_to_move=True,
                                       weights=weights)
        s_path = qm_eval_2d.evaluate(starting_2d, side_to_move=True,
                                       weights=path)
        assert s_dict == s_path
    finally:
        os.unlink(path)


def test_2d_load_weights_json_unknown_raises():
    """Unknown observable name in JSON raises ValueError with the
    bad name in the message."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump({'pawn': 1.0, 'rook': 0.5}, f)   # 'pawn' is not
        path = f.name                               # in the basis
    try:
        with pytest.raises(ValueError) as ei:
            qm_eval_2d.load_weights_json(path)
        assert 'pawn' in str(ei.value)
    finally:
        os.unlink(path)


def test_2d_load_weights_json_non_dict_raises():
    """Non-dict JSON top level raises."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump([1, 2, 3], f)
        path = f.name
    try:
        with pytest.raises(ValueError):
            qm_eval_2d.load_weights_json(path)
    finally:
        os.unlink(path)


def test_2d_breakdown_sums_to_evaluate(starting_2d):
    """sum(evaluate_breakdown(...)) == evaluate(...)."""
    weights = {'rook': 1.5, 'queen': 0.8}
    score = qm_eval_2d.evaluate(starting_2d, side_to_move=True,
                                  weights=weights)
    breakdown = qm_eval_2d.evaluate_breakdown(starting_2d,
                                                 side_to_move=True,
                                                 weights=weights)
    assert sum(breakdown.values()) == pytest.approx(score, rel=1e-12)


def test_2d_breakdown_side_to_move_flips_sign(starting_2d):
    """All breakdown values flip sign together with side_to_move."""
    bw = qm_eval_2d.evaluate_breakdown(starting_2d, side_to_move=True)
    bb = qm_eval_2d.evaluate_breakdown(starting_2d, side_to_move=False)
    for piece in bw:
        assert bw[piece] == pytest.approx(-bb[piece], rel=1e-12)


def test_2d_breakdown_empty_position_all_zeros():
    """Empty position breakdown returns {piece: 0.0} dict."""
    breakdown = qm_eval_2d.evaluate_breakdown({}, side_to_move=True)
    assert set(breakdown) == {'rook', 'bishop', 'queen', 'king',
                               'knight'}
    for v in breakdown.values():
        assert v == 0.0


# ---- 4D fixtures ----------------------------------------------------


@pytest.fixture(scope="module")
def starting_4d_offset_kings():
    """Non-antipodal kings -- avoids the encoder's central-inversion
    kernel (which encodes anti-podal kings to zero per Pre-flight 1)."""
    return parse_fen4("4d-fen v1: K@0,0,0,0; k@5,4,3,2")


@pytest.fixture(scope="module")
def midgame_4d():
    return parse_fen4(
        "4d-fen v1: K@0,0,0,0; k@5,4,3,2; "
        "Q@2,3,1,4; r@6,5,3,1; N@1,1,2,2"
    )


# ---- 4D observable_expectations + evaluator -----------------------


def test_4d_observable_expectations_keys(starting_4d_offset_kings):
    psi = qm_2d.state_to_psi   # placeholder ref to ensure import works
    from chess_spectral import qm_4d
    p = qm_4d.state_to_psi(starting_4d_offset_kings, side_to_move=True)
    out = qm_eval_4d.observable_expectations(p)
    assert set(out) == {'rook', 'bishop', 'queen', 'king', 'knight'}


def test_4d_observable_expectations_real_valued(midgame_4d):
    from chess_spectral import qm_4d
    p = qm_4d.state_to_psi(midgame_4d, side_to_move=True)
    out = qm_eval_4d.observable_expectations(p)
    for piece, val in out.items():
        assert isinstance(val, float)


def test_4d_observable_expectations_shape_mismatch_raises():
    bad = np.zeros(45057, dtype=np.complex128)
    with pytest.raises(ValueError):
        qm_eval_4d.observable_expectations(bad)


def test_4d_empty_position_scores_zero():
    assert qm_eval_4d.evaluate({}, side_to_move=True) == 0.0


def test_4d_non_empty_score_finite_real(starting_4d_offset_kings):
    score = qm_eval_4d.evaluate(starting_4d_offset_kings,
                                  side_to_move=True)
    assert isinstance(score, float)
    assert np.isfinite(score)


def test_4d_side_to_move_flip(starting_4d_offset_kings):
    s_w = qm_eval_4d.evaluate(starting_4d_offset_kings,
                                side_to_move=True)
    s_b = qm_eval_4d.evaluate(starting_4d_offset_kings,
                                side_to_move=False)
    assert s_w == pytest.approx(-s_b, rel=1e-12)


def test_4d_custom_weights_zero_out_all_but_one(starting_4d_offset_kings):
    weights = {p: 0.0 for p in qm_eval_4d.PIECE_NAMES_4D}
    weights['queen'] = 1.0
    score = qm_eval_4d.evaluate(starting_4d_offset_kings,
                                  side_to_move=True,
                                  weights=weights)
    from chess_spectral import qm_4d
    psi = qm_4d.state_to_psi(starting_4d_offset_kings, side_to_move=True)
    expectations = qm_eval_4d.observable_expectations(psi)
    assert score == pytest.approx(expectations['queen'], rel=1e-12)


def test_4d_load_weights_json_unknown_raises():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                       delete=False) as f:
        json.dump({'rook': 1.0, 'pawn': 0.5}, f)
        path = f.name
    try:
        with pytest.raises(ValueError) as ei:
            qm_eval_4d.load_weights_json(path)
        assert 'pawn' in str(ei.value)
    finally:
        os.unlink(path)


def test_4d_breakdown_sums_to_evaluate(starting_4d_offset_kings):
    weights = {'queen': 2.0, 'rook': 0.5}
    score = qm_eval_4d.evaluate(starting_4d_offset_kings,
                                  side_to_move=True,
                                  weights=weights)
    breakdown = qm_eval_4d.evaluate_breakdown(starting_4d_offset_kings,
                                                 side_to_move=True,
                                                 weights=weights)
    assert sum(breakdown.values()) == pytest.approx(score, rel=1e-12)


def test_4d_antipodal_kings_score_zero():
    """Anti-podal kings sit in the encoder's central-inversion kernel
    (Pre-flight 1) -> psi == zero vector -> graceful 0 score."""
    pos = parse_fen4("4d-fen v1: K@0,0,0,0; k@7,7,7,7")
    score = qm_eval_4d.evaluate(pos, side_to_move=True)
    assert score == 0.0


# ---- API surface ----------------------------------------------------


def test_2d_module_public_api():
    for name in ('evaluate', 'evaluate_breakdown',
                 'observable_expectations', 'load_weights_json',
                 'DEFAULT_WEIGHTS', 'PIECE_NAMES'):
        assert name in qm_eval_2d.__all__


def test_4d_module_public_api():
    for name in ('evaluate', 'evaluate_breakdown',
                 'observable_expectations', 'load_weights_json',
                 'DEFAULT_WEIGHTS_4D', 'PIECE_NAMES_4D'):
        assert name in qm_eval_4d.__all__


def test_engine_namespace_re_exports_qm():
    """Both engine.eval namespaces re-export the qm module."""
    from chess_spectral.engine import eval as eval_2d
    from chess_spectral_4d.engine import eval as eval_4d
    assert hasattr(eval_2d, 'qm')
    assert hasattr(eval_4d, 'qm')


# ---- Cross-evaluator family consistency -----------------------------


def test_all_three_evaluators_share_signature(starting_2d):
    """material, spectral, qm all expose evaluate(position,
    side_to_move) -> float at 2D."""
    from chess_spectral.engine.eval import material, spectral, qm
    s_mat = material.evaluate(starting_2d, side_to_move=True)
    s_spec = spectral.evaluate(starting_2d, side_to_move=True)
    s_qm = qm.evaluate(starting_2d, side_to_move=True)
    assert isinstance(s_mat, float)
    assert isinstance(s_spec, float)
    assert isinstance(s_qm, float)
