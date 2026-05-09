"""Tests for chess_spectral.phase_classifier (1.16.0+).

Three layers:

  * **Unit** — k-means correctness on synthetic data, fingerprint
    shape contract, label_phases heuristic on hand-crafted centroids.
  * **Integration** — train classifier from a small embedded PGN
    and verify the centroids recover sensible phase semantics.
  * **Round-trip** — PhaseClassifier serialization (to_dict /
    from_dict).
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import fen_to_pos    # noqa: E402
from chess_spectral.phase_classifier import (   # noqa: E402
    extract_fingerprint_2d,
    extract_fingerprints_from_pgn,
    kmeans_cluster,
    label_phases,
    PhaseClassifier,
    train_phase_classifier_from_pgn,
    N_FINGERPRINT_DIMS_2D,
)


# Embedded test PGN — 2 short games, enough plies to land in midgame
# and endgame phases. Used by integration tests so they don't depend
# on the .pgn_cache directory or external corpus files.
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
"""


@pytest.fixture
def tmp_pgn(tmp_path: Path) -> Path:
    p = tmp_path / "test.pgn"
    p.write_text(_TEST_PGN, encoding="utf-8")
    return p


# ─── Fingerprint extraction ─────────────────────────────────────────


class TestExtractFingerprint:
    """``extract_fingerprint_2d`` returns the canonical 10-dim
    log-channel-energy vector."""

    def test_shape_and_dtype(self):
        pos = fen_to_pos(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        fp = extract_fingerprint_2d(pos)
        assert fp.shape == (N_FINGERPRINT_DIMS_2D,)
        assert fp.shape == (10,)
        assert fp.dtype == np.float64

    def test_log_transform_is_applied(self):
        """The fingerprint must use log1p — raw energies span 4-5
        orders of magnitude and would dominate clustering. We check
        that the values are bounded above by ~log(max_raw_energy + 1),
        which for typical positions is ≤ ~10."""
        pos = fen_to_pos(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        fp = extract_fingerprint_2d(pos)
        assert (fp >= 0).all()  # log1p(non-negative) ≥ 0
        assert fp.max() <= 12   # ~exp(12) = 1.6e5; channel energies < 5e3

    def test_empty_position_returns_zero_fingerprint(self):
        fp = extract_fingerprint_2d({})
        # log1p(0) = 0
        assert np.allclose(fp, 0.0)


# ─── k-means correctness ────────────────────────────────────────────


class TestKMeansCluster:
    """Pure-numpy k-means: correctness on synthetic data."""

    def test_separated_clusters_recovered(self):
        """Three well-separated clusters → k=3 recovers them exactly
        (modulo cluster index permutation)."""
        rng = np.random.default_rng(0)
        cluster_a = rng.normal(loc=[0, 0], scale=0.1, size=(50, 2))
        cluster_b = rng.normal(loc=[10, 0], scale=0.1, size=(50, 2))
        cluster_c = rng.normal(loc=[0, 10], scale=0.1, size=(50, 2))
        X = np.vstack([cluster_a, cluster_b, cluster_c])
        centroids, labels = kmeans_cluster(X, k=3, seed=0)
        assert centroids.shape == (3, 2)
        assert labels.shape == (150,)
        # Each true cluster should have all points labeled the same.
        for i, true_idx in enumerate([0, 1, 2]):
            slice_labels = labels[i*50:(i+1)*50]
            assert len(np.unique(slice_labels)) == 1, (
                f"true cluster {i} split across labels {set(slice_labels)}"
            )

    def test_k_equals_n_returns_each_point_as_centroid(self):
        """When k = n, each point becomes its own cluster (degenerate
        case — should at least not crash)."""
        X = np.array([[0.0, 0], [1, 0], [2, 0]])
        centroids, labels = kmeans_cluster(X, k=3, seed=0)
        assert centroids.shape == (3, 2)
        assert set(labels.tolist()) == {0, 1, 2}

    def test_k_too_large_raises(self):
        X = np.array([[0.0, 0], [1, 1]])
        with pytest.raises(ValueError):
            kmeans_cluster(X, k=5, seed=0)

    def test_deterministic_with_seed(self):
        rng = np.random.default_rng(42)
        X = rng.normal(size=(30, 5))
        c1, l1 = kmeans_cluster(X, k=3, seed=7)
        c2, l2 = kmeans_cluster(X, k=3, seed=7)
        np.testing.assert_array_equal(c1, c2)
        np.testing.assert_array_equal(l1, l2)


# ─── Phase labeling heuristic ───────────────────────────────────────


class TestLabelPhases:
    """``label_phases`` recovers open/mid/end labels from centroid
    structure."""

    def test_synthetic_centroids_recovered(self):
        """Hand-craft 3 centroids — opening (high A1+B1+B2), endgame
        (low total), midgame (in between) — and verify the heuristic
        labels them correctly."""
        # Channel order: A1 A2 B1 B2 E F1 F2 F3 FA FD
        opening_centroid = np.array(
            [5.0, 4.0, 5.0, 5.0, 6.0, 4.0, 4.0, 4.0, 2.0, 1.0]
        )
        midgame_centroid = np.array(
            [3.0, 3.0, 3.0, 3.0, 5.0, 4.0, 5.0, 5.0, 4.0, 4.0]
        )
        endgame_centroid = np.array(
            [0.5, 0.5, 0.5, 0.5, 1.0, 0.5, 0.5, 0.5, 1.0, 0.5]
        )
        centroids = np.stack([
            midgame_centroid,
            opening_centroid,
            endgame_centroid,
        ])
        labels = label_phases(centroids)
        assert labels[0] == 'midgame'
        assert labels[1] == 'opening'
        assert labels[2] == 'endgame'

    def test_k_not_3_raises(self):
        c2 = np.zeros((2, 10))
        c4 = np.zeros((4, 10))
        with pytest.raises(ValueError):
            label_phases(c2)
        with pytest.raises(ValueError):
            label_phases(c4)


# ─── PGN extraction integration ─────────────────────────────────────


class TestExtractFingerprintsFromPgn:
    """``extract_fingerprints_from_pgn`` walks a PGN file and emits
    (FEN, fingerprint) pairs."""

    def test_extracts_positions(self, tmp_pgn):
        fps = extract_fingerprints_from_pgn(tmp_pgn)
        # Game 1 has 21 plies × 2 (each move = 2 plies-ish in PGN
        # convention but counted simply) — actually mainline_moves
        # iterates each ply, so 21 plies for game 1 + some for game 2.
        assert len(fps) > 5
        for fen, fp in fps:
            assert isinstance(fen, str)
            assert fp.shape == (10,)
            assert fp.dtype == np.float64

    def test_max_games_caps_count(self, tmp_pgn):
        all_fps = extract_fingerprints_from_pgn(tmp_pgn)
        first_only = extract_fingerprints_from_pgn(tmp_pgn, max_games=1)
        assert 0 < len(first_only) < len(all_fps)

    def test_sample_every_subsamples(self, tmp_pgn):
        full = extract_fingerprints_from_pgn(tmp_pgn, sample_every=1)
        every_other = extract_fingerprints_from_pgn(
            tmp_pgn, sample_every=2,
        )
        # every-other should be roughly half the size.
        assert len(every_other) <= len(full) // 2 + 2

    def test_skip_initial_plies(self, tmp_pgn):
        no_skip = extract_fingerprints_from_pgn(
            tmp_pgn, sample_every=1, skip_initial_plies=0,
        )
        skip_4 = extract_fingerprints_from_pgn(
            tmp_pgn, sample_every=1, skip_initial_plies=4,
        )
        assert len(skip_4) == len(no_skip) - 4 - 4  # 4 plies × 2 games


# ─── End-to-end training ────────────────────────────────────────────


class TestTrainPhaseClassifierFromPgn:
    """Full pipeline: PGN file → trained classifier."""

    def test_trains_without_error(self, tmp_pgn):
        classifier, labeled = train_phase_classifier_from_pgn(
            tmp_pgn, sample_every=1, skip_initial_plies=2,
        )
        assert classifier.centroids.shape == (3, 10)
        assert set(classifier.phase_map.values()) == {
            'opening', 'midgame', 'endgame'
        }
        assert len(labeled) > 5
        for fen, fp, cluster in labeled:
            assert cluster in (0, 1, 2)
            assert classifier.phase_map[cluster] in (
                'opening', 'midgame', 'endgame'
            )

    def test_classifier_distinguishes_dense_vs_sparse(self, tmp_pgn):
        """Train on the small PGN; verify the classifier gives
        DIFFERENT labels for a dense mid-board position vs a sparse
        K+P endgame position. Doesn't assert which label is which —
        the small training set may not perfectly recover semantic
        labels, but it MUST distinguish piece-rich from piece-poor.
        """
        classifier, _ = train_phase_classifier_from_pgn(
            tmp_pgn, sample_every=1, skip_initial_plies=0,
        )
        # Dense midboard position (15+ pieces, mixed)
        dense_pos = fen_to_pos(
            "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11"
        )
        # Sparse K+P vs K endgame (3 pieces)
        sparse_pos = fen_to_pos("8/8/8/4k3/4P3/4K3/8/8 w - - 0 1")
        dense_label = classifier.classify(dense_pos)
        sparse_label = classifier.classify(sparse_pos)
        # Dense and sparse positions should not classify the same.
        assert dense_label != sparse_label, (
            f"dense and sparse positions both classified as "
            f"{dense_label!r}; classifier failed to distinguish "
            f"piece-rich from piece-poor"
        )
        # Sanity: both labels must be in the canonical set.
        assert dense_label in ('opening', 'midgame', 'endgame')
        assert sparse_label in ('opening', 'midgame', 'endgame')

    def test_too_few_positions_raises(self, tmp_path):
        empty_pgn = tmp_path / "empty.pgn"
        empty_pgn.write_text(
            '[Event "tiny"]\n[Result "*"]\n\n1. e4 *\n', encoding="utf-8"
        )
        # Only 1 ply, k=3 needs ≥3 fingerprints.
        with pytest.raises(ValueError):
            train_phase_classifier_from_pgn(empty_pgn, skip_initial_plies=0)


# ─── Serialization round-trip ───────────────────────────────────────


class TestPhaseClassifierSerialization:
    def test_to_dict_from_dict_round_trip(self, tmp_pgn):
        classifier, _ = train_phase_classifier_from_pgn(
            tmp_pgn, skip_initial_plies=0,
        )
        as_dict = classifier.to_dict()
        # Should be JSON-serializable.
        as_json = json.dumps(as_dict)
        recovered = PhaseClassifier.from_dict(json.loads(as_json))
        np.testing.assert_array_equal(
            recovered.centroids, classifier.centroids,
        )
        assert recovered.phase_map == classifier.phase_map
        assert recovered.channel_names == classifier.channel_names

    def test_classifier_classifies_consistently_after_round_trip(self, tmp_pgn):
        classifier, _ = train_phase_classifier_from_pgn(
            tmp_pgn, skip_initial_plies=0,
        )
        recovered = PhaseClassifier.from_dict(
            json.loads(json.dumps(classifier.to_dict()))
        )
        pos = fen_to_pos(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )
        assert classifier.classify(pos) == recovered.classify(pos)
