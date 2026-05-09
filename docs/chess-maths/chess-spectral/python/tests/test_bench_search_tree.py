"""Smoke test for the search-tree bench harness (1.16.0+).

The bench itself (``tests/bench_search_tree.py``) is a research tool
that takes minutes at depth 4-5. This test module runs the smallest
possible bench — depth=2, reps=1, 1 variant — to verify the harness
itself works.

Production runs are manual::

    python tests/bench_search_tree.py --depth 4 --reps 3 \\
        --output bench_results.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from tests.bench_search_tree import (   # noqa: E402
    _build_variants,
    bench_one_search,
    run_sweep,
)


class TestVariantRegistry:
    def test_registry_has_variants(self):
        registry = _build_variants()
        for name in (
            'material',
            'spectral_float64',
            'spectral_hybrid_8bit_lru',
        ):
            assert name in registry
            factory = registry[name]
            evaluator = factory()
            assert callable(evaluator)


class TestBenchOneSearch:
    def test_smoke_runs(self):
        registry = _build_variants()
        result = bench_one_search(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            registry['material'],
            depth=2,
            reps=1,
            warmup=0,
        )
        assert result['mean_nodes'] > 0
        assert result['mean_elapsed_ms'] > 0
        assert result['nodes_per_sec'] > 0
        assert result['depth_reached'] >= 1  # may go deeper via quiescence

    def test_per_rep_elapsed_recorded(self):
        registry = _build_variants()
        result = bench_one_search(
            "8/8/8/4k3/4P3/4K3/8/8 w - - 0 1",
            registry['material'],
            depth=2,
            reps=2,
            warmup=0,
        )
        assert len(result['per_rep_elapsed_ms']) == 2


class TestRunSweep:
    def test_smoke_runs_minimal_sweep(self):
        result = run_sweep(
            ['material'],
            depth=2,
            reps=1,
            corpora={
                'opening': ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"],
                'endgame': ["8/8/8/4k3/4P3/4K3/8/8 w - - 0 1"],
            },
            verbose=False,
        )
        assert result['depth'] == 2
        assert result['variants'] == ['material']
        assert 'material' in result['aggregates']
        for corpus in ('opening', 'endgame'):
            assert corpus in result['aggregates']['material']
            cell = result['aggregates']['material'][corpus]
            assert cell['mean_nodes_per_sec'] > 0

    def test_unknown_variant_raises(self):
        with pytest.raises(ValueError):
            run_sweep(
                ['nonexistent'],
                depth=2,
                reps=1,
                corpora={'a': ["8/8/8/4k3/4P3/4K3/8/8 w - - 0 1"]},
                verbose=False,
            )

    def test_sweep_is_json_serializable(self, tmp_path: Path):
        result = run_sweep(
            ['material'],
            depth=2,
            reps=1,
            corpora={'a': ["8/8/8/4k3/4P3/4K3/8/8 w - - 0 1"]},
            verbose=False,
        )
        out = tmp_path / "sweep.json"
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(result, f)
        with open(out, 'r', encoding='utf-8') as f:
            recovered = json.load(f)
        assert recovered['depth'] == 2
