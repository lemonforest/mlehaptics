"""Tests for chess_spectral.engine.tournament.agent_spec."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
sys.path.insert(0, str(PY_DIR))

from chess_spectral.engine.tournament.agent_spec import (  # noqa: E402
    AgentSpec, parse_spec, build_agent_2d, build_agent_4d,
)


# ─── parse_spec ─────────────────────────────────────────────────────


def test_parse_spec_minimal():
    s = parse_spec("evaluator=material")
    assert s.evaluator == "material"
    assert s.depth == 4
    assert s.weights is None
    assert s.no_tt is False
    assert s.label is None  # default applied at build time


def test_parse_spec_full_2d_form():
    s = parse_spec(
        "label=alpha,evaluator=spectral,depth=3,weights=spectral_v1.json,"
        "time_budget_ms=2000,quiescence_max_depth=6"
    )
    assert s.label == "alpha"
    assert s.evaluator == "spectral"
    assert s.depth == 3
    assert s.time_budget_ms == 2000
    assert s.weights == Path("spectral_v1.json")
    assert s.quiescence_max_depth == 6


def test_parse_spec_bool_flags_bare():
    """`no_tt` alone (no =) means True."""
    s = parse_spec("evaluator=material,no_tt,no_quiescence")
    assert s.no_tt is True
    assert s.no_mvv_lva is False
    assert s.no_quiescence is True


def test_parse_spec_bool_flags_explicit():
    s = parse_spec("evaluator=material,no_tt=true,no_mvv_lva=false")
    assert s.no_tt is True
    assert s.no_mvv_lva is False


def test_parse_spec_bool_flags_aliases():
    """Accepts true/1/yes/on and false/0/no/off."""
    for true_val in ("true", "1", "yes", "on", "TRUE", "True"):
        s = parse_spec(f"evaluator=material,no_tt={true_val}")
        assert s.no_tt is True, f"failed for {true_val!r}"
    for false_val in ("false", "0", "no", "off", "FALSE"):
        s = parse_spec(f"evaluator=material,no_tt={false_val}")
        assert s.no_tt is False, f"failed for {false_val!r}"


def test_parse_spec_whitespace_tolerant():
    s = parse_spec("  evaluator = qm , depth = 3 ")
    assert s.evaluator == "qm"
    assert s.depth == 3


def test_parse_spec_rejects_missing_evaluator():
    with pytest.raises(ValueError, match="evaluator"):
        parse_spec("depth=4")


def test_parse_spec_rejects_unknown_key():
    with pytest.raises(ValueError, match="unknown agent spec key"):
        parse_spec("evaluator=material,bogus=x")


def test_parse_spec_rejects_non_integer_depth():
    with pytest.raises(ValueError, match="not an integer"):
        parse_spec("evaluator=material,depth=hello")


def test_parse_spec_rejects_bad_bool():
    with pytest.raises(ValueError, match="boolean"):
        parse_spec("evaluator=material,no_tt=maybe")


def test_parse_spec_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        parse_spec("")


# ─── build_agent_2d ─────────────────────────────────────────────────


def test_build_agent_2d_material_default():
    s = parse_spec("evaluator=material")
    agent = build_agent_2d(s)
    assert agent.label == "material@4"
    assert callable(agent.evaluator)
    assert callable(agent.search_fn)
    # Default search options
    assert agent.search_options.max_depth == 4
    assert agent.search_options.use_tt is True


def test_build_agent_2d_spectral_no_weights():
    """Spectral without weights uses module DEFAULT_WEIGHTS implicitly
    via the evaluator's default arg."""
    s = parse_spec("evaluator=spectral,depth=2")
    agent = build_agent_2d(s)
    assert agent.label == "spectral@2"
    assert agent.search_options.max_depth == 2


def test_build_agent_2d_qm_with_ablations():
    s = parse_spec("evaluator=qm,depth=3,no_tt,no_quiescence")
    agent = build_agent_2d(s)
    assert agent.label == "qm@3"
    assert agent.search_options.use_tt is False
    assert agent.search_options.use_quiescence is False
    assert agent.search_options.use_mvv_lva is True


def test_build_agent_2d_explicit_label():
    s = parse_spec("label=challenger,evaluator=material,depth=2")
    agent = build_agent_2d(s)
    assert agent.label == "challenger"


def test_build_agent_2d_material_rejects_weights():
    """Material is unweighted by design; weights= should raise."""
    s = parse_spec("evaluator=material,weights=somefile.json")
    with pytest.raises(ValueError, match="does not accept weights"):
        build_agent_2d(s)


def test_build_agent_2d_unknown_evaluator():
    s = AgentSpec(evaluator="bogus")
    with pytest.raises(ValueError, match="unknown evaluator"):
        build_agent_2d(s)


# ─── build_agent_4d ─────────────────────────────────────────────────


def test_build_agent_4d_material():
    s = parse_spec("evaluator=material,depth=2")
    agent = build_agent_4d(s)
    assert agent.label == "material@2"
    assert callable(agent.evaluator)
    assert callable(agent.search_fn)
    assert agent.search_options.max_depth == 2


def test_build_agent_4d_qm():
    s = parse_spec("evaluator=qm,depth=1")
    agent = build_agent_4d(s)
    assert agent.label == "qm@1"
    assert agent.search_options.max_depth == 1


# ─── Asymmetric per-side configuration (the §16 requirement) ───────


def test_2d_white_and_black_can_be_independently_configured():
    """A tournament round with white=spectral@4, black=qm@3 produces
    two separately-configured agents in the same process.

    This is the §16 use case: empirically pit (evaluator, depth) cells
    against each other to compute Elo. The CLI surface must support
    asymmetric specs (white differs from black)."""
    white = build_agent_2d(parse_spec(
        "label=alpha,evaluator=spectral,depth=4,no_quiescence"
    ))
    black = build_agent_2d(parse_spec(
        "label=beta,evaluator=qm,depth=3"
    ))
    assert white.label == "alpha"
    assert black.label == "beta"
    assert white.search_options.max_depth == 4
    assert black.search_options.max_depth == 3
    assert white.search_options.use_quiescence is False
    assert black.search_options.use_quiescence is True
    # Different evaluator functions
    assert white.evaluator is not black.evaluator


def test_4d_white_and_black_independently_configured():
    """Same property holds for the 4D side."""
    white = build_agent_4d(parse_spec("evaluator=material,depth=2"))
    black = build_agent_4d(parse_spec("evaluator=spectral,depth=3,no_tt"))
    assert white.search_options.max_depth == 2
    assert black.search_options.max_depth == 3
    assert white.search_options.use_tt is True
    assert black.search_options.use_tt is False
