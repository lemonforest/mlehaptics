"""Smoke test for the tournament runner (1.16.0+).

The tournament runner itself (``tests/run_evaluator_tournament.py``)
is a research tool that can take minutes to hours depending on
parameters. This module's tests run the SMALLEST possible tournament
to verify the runner works without committing CI minutes to a full
empirical sweep.

Production sweeps run manually, e.g.::

    python tests/run_evaluator_tournament.py --depth 4 \\
        --games-per-pair 8 --output tournament_d4.json

Test scope
----------

  * Variant registry surfaces the expected 3 evaluator variants.
  * Single tournament (depth=2, games_per_pair=1, 2 variants only)
    runs without error and produces JSON-shape output.
  * Depth sweep (2 depths) runs without error and aggregates results.
  * CLI ``--help`` works.

The test budget is one game pair × one ply count × low depth — should
complete in a few seconds.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from tests.run_evaluator_tournament import (   # noqa: E402
    _build_evaluator_variants,
    run_one_tournament,
    run_depth_sweep,
)


# ─── Variant registry ───────────────────────────────────────────────


class TestVariantRegistry:
    def test_registry_has_expected_variants(self):
        registry = _build_evaluator_variants()
        for name in ('material', 'spectral_float64',
                     'spectral_hybrid_8bit_lru'):
            assert name in registry, (
                f"variant {name!r} missing from registry"
            )
            description, factory = registry[name]
            assert isinstance(description, str)
            assert callable(factory)

    def test_variant_factory_returns_label_plus_callable(self):
        registry = _build_evaluator_variants()
        for name, (_desc, factory) in registry.items():
            label, evaluator = factory()
            assert isinstance(label, str)
            assert callable(evaluator)


# ─── Single tournament ──────────────────────────────────────────────


class TestRunOneTournament:
    """Smallest viable tournament: depth=2, 1 game per pair, 2 variants."""

    def test_smoke_runs_without_error(self):
        """The cheapest possible tournament — depth=2, 1 game per pair,
        100-ply cap. Should finish in a few seconds."""
        result = run_one_tournament(
            ['material', 'spectral_float64'],
            depth=2,
            games_per_pair=1,
            max_plies=60,
        )
        assert isinstance(result, dict)
        assert result['depth'] == 2
        assert result['games_per_pair'] == 1
        assert result['n_games_played'] >= 1

    def test_output_dict_shape(self):
        result = run_one_tournament(
            ['material', 'spectral_float64'],
            depth=2,
            games_per_pair=1,
            max_plies=60,
        )
        for key in (
            'depth', 'games_per_pair', 'max_plies',
            'n_games_played', 'elapsed_seconds',
            'final_elos', 'pair_records', 'termination_by_pair',
            'mean_plies_per_game', 'mean_elapsed_per_game_ms',
        ):
            assert key in result, f"missing key {key!r}"
        # final_elos: every variant should have an ELO score.
        assert 'material' in result['final_elos']
        assert 'spectral_float64' in result['final_elos']
        # pair_records: 1 pair × 2 colors = at least 1 entry.
        assert len(result['pair_records']) >= 1

    def test_unknown_variant_raises(self):
        with pytest.raises(ValueError) as excinfo:
            run_one_tournament(
                ['material', 'nonexistent_variant'],
                depth=2,
                games_per_pair=1,
                max_plies=60,
            )
        assert 'unknown variant' in str(excinfo.value).lower()


# ─── Depth sweep ────────────────────────────────────────────────────


class TestRunDepthSweep:
    """Multi-depth sweep aggregates per-depth results."""

    def test_sweep_runs_without_error(self):
        """Sweep over 2 depths × 2 variants × 1 game per pair."""
        result = run_depth_sweep(
            ['material', 'spectral_float64'],
            depths=[2, 3],
            games_per_pair=1,
            max_plies=60,
        )
        assert isinstance(result, dict)
        assert result['variants'] == ['material', 'spectral_float64']
        assert result['depths'] == [2, 3]
        assert len(result['results']) == 2
        for tournament in result['results']:
            assert 'final_elos' in tournament
            assert 'pair_records' in tournament

    def test_sweep_is_json_serializable(self, tmp_path: Path):
        result = run_depth_sweep(
            ['material', 'spectral_float64'],
            depths=[2],
            games_per_pair=1,
            max_plies=60,
        )
        # JSON serialization must work — this is the runner's
        # archival format.
        out_path = tmp_path / "sweep.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f)
        # And round-trips.
        with open(out_path, 'r', encoding='utf-8') as f:
            recovered = json.load(f)
        assert recovered['variants'] == result['variants']
        assert recovered['depths'] == result['depths']


# ─── CLI ────────────────────────────────────────────────────────────


class TestCli:
    def test_cli_help_works(self):
        """``--help`` should exit 0 and print usage."""
        proc = subprocess.run(
            [sys.executable, str(HERE) + '/run_evaluator_tournament.py', '--help'],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 0
        assert 'usage' in proc.stdout.lower() or 'usage' in proc.stderr.lower()

    def test_cli_runs_minimal_tournament(self, tmp_path: Path):
        """CLI run with smallest possible tournament; verify JSON
        output is valid."""
        out_path = tmp_path / "smoke.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(HERE) + '/run_evaluator_tournament.py',
                '--variants', 'material,spectral_float64',
                '--depth', '2',
                '--games-per-pair', '1',
                '--max-plies', '60',
                '--output', str(out_path),
                '--quiet',
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert proc.returncode == 0, (
            f"CLI failed: stdout={proc.stdout}\nstderr={proc.stderr}"
        )
        assert out_path.exists()
        with open(out_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['depths'] == [2]
        assert data['variants'] == ['material', 'spectral_float64']
        assert len(data['results']) == 1
