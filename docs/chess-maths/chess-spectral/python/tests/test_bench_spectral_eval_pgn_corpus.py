"""Tests for the PGN-sourced corpus flag in bench_spectral_eval (1.19.0+).

The bench harness ``tests/bench_spectral_eval.py`` historically used
hand-picked OPENING / MIDGAME / ENDGAME FEN lists. The 1.16.0
:mod:`chess_spectral.phase_classifier` module provides a data-driven
alternative — k-means on log-channel-energy fingerprints from PGN
games — but until 1.19.0 the bench harness wasn't wired to it.

These tests exercise the ``--pgn-corpus`` CLI flag and the
:func:`build_pgn_sourced_corpora` helper:

  1. CLI smoke test — running with ``--pgn-corpus`` produces valid
     JSON with the expected phase keys and provenance metadata.
  2. Determinism — same seed → identical FEN sample.
  3. Provenance — output JSON carries ``corpus_provenance.source =
     "pgn"`` and the classifier's cluster counts.

The PGN fixture is embedded inline so these tests don't depend on
the ``.pgn_cache`` directory or external corpus files (mirroring the
pattern used by ``tests/test_phase_classifier.py``).
"""
from __future__ import annotations

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

from tests.bench_spectral_eval import (   # noqa: E402
    build_pgn_sourced_corpora,
    run_bench,
)


# Embedded PGN — 4 games (more positions than the 2-game fixture in
# test_phase_classifier.py) to give k-means a healthier per-cluster
# population. Each phase needs ≥ 1 sampled FEN; with 4 modest-length
# games the classifier reliably recovers all three.
_TEST_PGN = """\
[Event "Test Game 1"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4 Bxb4 5. c3 Ba5 6. d4 exd4
7. O-O Nf6 8. e5 d5 9. exf6 dxc4 10. Re1+ Be6 11. fxg7 Rg8 12. cxd4 Rxg7
13. Nc3 Bd5 14. Nxd5 Qxd5 15. Be3 Qxd4 16. Bxd4 Nxd4 17. Nxd4 Rxg2+
18. Kxg2 Bb6 19. Re8+ Kd7 20. Rxa8 Kc6 21. Rxa7 1-0

[Event "Test Game 2"]
[Result "0-1"]

1. d4 d5 2. c4 e6 3. Nc3 Nf6 4. Bg5 Be7 5. e3 O-O 6. Nf3 Nbd7
7. Rc1 c6 8. Bd3 dxc4 9. Bxc4 Nd5 10. Bxe7 Qxe7 11. O-O Nxc3
12. Rxc3 e5 13. dxe5 Nxe5 14. Nxe5 Qxe5 15. f4 Qe4 16. Rcc1 Bf5
17. Bd3 Qd4+ 18. Kh1 Bxd3 19. Qxd3 Qxd3 20. Rfd1 Qe4 21. b3 Rfd8
22. Rxd8+ Rxd8 23. Kg1 Rd2 24. h3 Rxa2 25. Rc8+ Kh7 26. Rxc6 Rxg2+
27. Kf1 Rh2 28. Kg1 Rxh3 29. Rc7 b5 30. Rxa7 b4 31. Ra8 b6
32. Rb8 b3 33. Rxb6 Rxe3 34. Rxb3 Re1+ 35. Kg2 0-1

[Event "Test Game 3"]
[Result "1-0"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 6. Be2 e5
7. Nb3 Be7 8. O-O O-O 9. Be3 Be6 10. Nd5 Nbd7 11. Qd3 Bxd5
12. exd5 Nb6 13. c4 a5 14. Rfc1 a4 15. Nd2 Nfxd5 16. cxd5 Nxd5
17. Bd1 Qa5 18. Nb1 Nxe3 19. Qxe3 Bf6 20. Bxa4 Rfd8 21. Bb3 Rd7
22. Nd2 Qb4 23. a3 Qxa3 24. Rxa3 Rxa3 25. Qxa3 Rxd2 26. Qa8+ Kg7
27. Qxb7 Rxb2 28. Bxf7 Kxf7 29. Qxb2 1-0

[Event "Test Game 4"]
[Result "0-1"]

1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Nf3 O-O 6. Be2 e5
7. O-O Nc6 8. d5 Ne7 9. Nd2 a5 10. a3 Nd7 11. Rb1 f5 12. b4 Kh8
13. f3 Ng8 14. Qc2 Ngf6 15. Nb5 axb4 16. axb4 Nh5 17. g3 Nf6
18. c5 Nxe4 19. Nxe4 fxe4 20. fxe4 Rxf1+ 21. Bxf1 Bf5 22. exf5 Nf6
23. fxg6 hxg6 24. cxd6 cxd6 25. Nxd6 Qxd6 26. Bg2 Re8 27. Bd2 Bf8
28. Bb4 Qd7 29. Re1 Rxe1+ 30. Bxe1 Qxd5 31. Qd1 Qxd1 32. Bxd1 Bd6
33. Bf3 Nd7 34. Bxd6 Nf6 35. Bb8 Kg7 36. Ba7 Kf7 37. Be3 Ke6
38. Kf2 Kd5 39. Kf1 Ne4 40. Bd1 Nxg3+ 41. hxg3 b6 42. Bf4 Kc4
43. Bxg6 Kxb4 44. Bf7 Ka3 45. Bd5 Kb2 46. Bxb6 Kxd5 0-1
"""


@pytest.fixture
def tmp_pgn(tmp_path: Path) -> Path:
    p = tmp_path / "test.pgn"
    p.write_text(_TEST_PGN, encoding="utf-8")
    return p


# ─── Library API ────────────────────────────────────────────────────


class TestBuildPgnSourcedCorpora:
    """Direct tests for :func:`build_pgn_sourced_corpora`."""

    def test_returns_three_phases(self, tmp_pgn):
        corpora, prov = build_pgn_sourced_corpora(
            tmp_pgn,
            max_games=10,
            positions_per_phase=2,
            seed=42,
            sample_every=1,
            skip_initial_plies=2,
        )
        assert set(corpora.keys()) == {"opening", "midgame", "endgame"}
        for phase, fens in corpora.items():
            assert len(fens) >= 1, f"phase {phase!r} has zero FENs"
            assert len(fens) <= 2, f"phase {phase!r} oversampled"
            for fen in fens:
                # Each FEN should be parseable as a string with 6 fields.
                assert isinstance(fen, str)
                assert len(fen.split()) >= 4

    def test_provenance_metadata(self, tmp_pgn):
        _, prov = build_pgn_sourced_corpora(
            tmp_pgn,
            max_games=4,
            positions_per_phase=2,
            seed=42,
            sample_every=1,
            skip_initial_plies=2,
        )
        assert prov["source"] == "pgn"
        assert prov["pgn_path"] == str(tmp_pgn)
        assert prov["max_games"] == 4
        assert prov["positions_per_phase"] == 2
        assert prov["seed"] == 42
        assert prov["training_position_count"] > 0
        assert isinstance(prov["cluster_counts"], dict)
        assert set(prov["cluster_counts"].keys()) == {
            "opening", "midgame", "endgame",
        }

    def test_determinism_same_seed(self, tmp_pgn):
        """Same PGN + same seed → identical FEN sample order."""
        corpora_a, _ = build_pgn_sourced_corpora(
            tmp_pgn, max_games=4, positions_per_phase=3,
            seed=42, sample_every=1, skip_initial_plies=2,
        )
        corpora_b, _ = build_pgn_sourced_corpora(
            tmp_pgn, max_games=4, positions_per_phase=3,
            seed=42, sample_every=1, skip_initial_plies=2,
        )
        assert corpora_a == corpora_b

    def test_different_seeds_yield_different_samples(self, tmp_pgn):
        """Different seed → at least one phase samples differ.

        Caveat: with small clusters, two seeds might happen to draw
        the same N items. Use larger positions_per_phase to make a
        collision very unlikely; assert that at least one phase
        differs.
        """
        corpora_42, _ = build_pgn_sourced_corpora(
            tmp_pgn, max_games=4, positions_per_phase=3,
            seed=42, sample_every=1, skip_initial_plies=2,
        )
        corpora_99, _ = build_pgn_sourced_corpora(
            tmp_pgn, max_games=4, positions_per_phase=3,
            seed=99, sample_every=1, skip_initial_plies=2,
        )
        differs = any(
            corpora_42[phase] != corpora_99[phase]
            for phase in corpora_42
        )
        assert differs, (
            "Different seeds produced identical samples across all "
            "phases — implausible unless the sampler ignored the seed."
        )

    def test_run_bench_with_pgn_corpus_overrides(self, tmp_pgn):
        """End-to-end: corpora dict feeds run_bench cleanly."""
        corpora, prov = build_pgn_sourced_corpora(
            tmp_pgn,
            max_games=4,
            positions_per_phase=2,
            seed=42,
            sample_every=1,
            skip_initial_plies=2,
        )
        result = run_bench(
            variants=["material"],
            iters=10,
            corpus_overrides=corpora,
            corpus_provenance=prov,
        )
        assert result["corpus_provenance"]["source"] == "pgn"
        assert "material" in result["summary"]
        for phase in ("opening", "midgame", "endgame"):
            assert phase in result["summary"]["material"]
            # Median latency must be finite & positive.
            assert result["summary"]["material"][phase] > 0


# ─── CLI ────────────────────────────────────────────────────────────


class TestBenchCli:
    """End-to-end CLI invocation via ``python tests/bench_spectral_eval.py``."""

    def _run_cli(self, *args: str, cwd: Path) -> "tuple[int, str, str]":
        """Run the bench CLI from the python package dir; return
        (returncode, stdout, stderr)."""
        cmd = [sys.executable, "tests/bench_spectral_eval.py", *args]
        proc = subprocess.run(
            cmd, cwd=str(cwd),
            capture_output=True, text=True, timeout=120,
        )
        return proc.returncode, proc.stdout, proc.stderr

    @pytest.fixture
    def python_pkg_dir(self) -> Path:
        # tests/ -> python/
        return Path(HERE).parent

    def test_pgn_corpus_flag_produces_valid_json(
        self, tmp_pgn, tmp_path, python_pkg_dir,
    ):
        out_json = tmp_path / "bench_out.json"
        rc, _stdout, stderr = self._run_cli(
            "--variants", "material",
            "--iters", "5",
            "--quiet",
            "--pgn-corpus", str(tmp_pgn),
            "--pgn-max-games", "4",
            "--pgn-positions-per-phase", "2",
            "--pgn-seed", "42",
            "--output", str(out_json),
            cwd=python_pkg_dir,
        )
        assert rc == 0, f"CLI failed: stderr={stderr!r}"
        assert out_json.exists()
        data = json.loads(out_json.read_text(encoding="utf-8"))
        # Standard keys.
        assert "results" in data
        assert "summary" in data
        assert "corpus_provenance" in data
        # Provenance reflects PGN source.
        assert data["corpus_provenance"]["source"] == "pgn"
        assert "cluster_counts" in data["corpus_provenance"]
        # Summary has the three phases.
        assert "material" in data["summary"]
        for phase in ("opening", "midgame", "endgame"):
            assert phase in data["summary"]["material"]

    def test_handpicked_path_unchanged(
        self, tmp_path, python_pkg_dir,
    ):
        """Without --pgn-corpus, the bench uses the hand-picked
        CORPORA dict and stamps ``source = "hand_picked"``. Ensures
        we didn't break the legacy code path."""
        out_json = tmp_path / "bench_legacy.json"
        rc, _stdout, stderr = self._run_cli(
            "--variants", "material",
            "--iters", "5",
            "--quiet",
            "--output", str(out_json),
            cwd=python_pkg_dir,
        )
        assert rc == 0, f"CLI failed: stderr={stderr!r}"
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["corpus_provenance"]["source"] == "hand_picked"
        # All three phases present.
        for phase in ("opening", "midgame", "endgame"):
            assert phase in data["summary"]["material"]
