"""PGN-sourced channel-energy phase classifier (1.16.0+).

Replaces the hand-picked open/mid/end FEN corpora used by
``tests/bench_spectral_eval.py`` (1.13.0+) and the §20.21 §20.15
acceptance bench with **data-driven** phase labels learned from real
games.

The framing
-----------

The 1.14.0 amendment 1 stress-test commit raised an honest gap: the
hand-picked 7-FEN corpus was unprincipled. The pedantic 1500-position
random-corpus stress tests addressed scale-of-evidence, but didn't
address the **phase classification** question — the open/mid/end
labels themselves were still hand-assigned. This module ships the
data-driven alternative.

Method
------

For each position in a PGN corpus:

  1. Encode via :func:`chess_spectral.encoder.encode_640` (or its 4D
     analog).
  2. Compute per-channel L2 energies via
     :func:`chess_spectral.encoder.channel_energies`.
  3. **Log-transform** the energies (``log1p`` to handle the wide
     dynamic range — energies span 4-5 orders of magnitude, k-means
     in raw space is dominated by the largest channels).
  4. The fingerprint is the 10-dim log-channel-energy vector (2D)
     or 11-dim (4D).

Cluster all fingerprints with **pure-numpy k-means** (k=3 by
default — open / mid / end). The centroids are interpreted by
heuristic post-processing:

  * Cluster with **highest A1 + B1 + B2** centroid (high castling-
    rights structural channels) → "opening"
  * Cluster with **lowest total energy** (sparse pieces) → "endgame"
  * Remaining cluster → "midgame"

The classifier is then a function from FEN/position → phase label
that uses the trained centroids.

Why this matters
----------------

The §20.15 acceptance bench numbers and the §20.21 amendment's
"opening 1.64× SLOWER, endgame 1.50× FASTER" framing both rest on
the hand-picked corpus partition. With data-driven labels, we can
re-run those benchmarks on a PGN-sourced corpus and confirm (or
challenge) those findings. This module provides the infrastructure;
the actual re-bench is the next ship.

Dependencies
------------

  * ``python-chess`` for PGN parsing (already a test-time dep).
  * ``numpy`` for k-means + log-transform (already a runtime dep).
  * No sklearn — k-means is ~30 LOC of pure numpy.

Usage
-----

CLI::

    cd docs/chess-maths/chess-spectral/python
    python -m chess_spectral.phase_classifier <pgn_path> --max-games 100 --output classified_corpus.json

Library::

    from chess_spectral.phase_classifier import (
        extract_fingerprints_from_pgn,
        kmeans_cluster, label_phases, classify_position,
    )
    fps = extract_fingerprints_from_pgn('games.pgn', max_games=50)
    centroids, labels = kmeans_cluster([fp[1] for fp in fps], k=3)
    phase_map = label_phases(centroids)
    # phase_map: {0: 'opening', 1: 'midgame', 2: 'endgame'} (order varies)
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from .encoder import encode_640, channel_energies, CHANNELS
from .fen import fen_to_pos


# Channel order used for fingerprints (mirrors CHANNELS).
_CHANNEL_NAMES_2D: Tuple[str, ...] = tuple(name for name, _ in CHANNELS)
N_FINGERPRINT_DIMS_2D: int = len(_CHANNEL_NAMES_2D)


# ─── Fingerprint extraction ─────────────────────────────────────────


def extract_fingerprint_2d(pos: Dict[int, str]) -> np.ndarray:
    """Compute the 10-dim log-channel-energy fingerprint for a 2D
    position dict.

    Returns
    -------
    np.ndarray, shape (10,), dtype float64
        ``log1p`` of the per-channel L2 energies, in the canonical
        :data:`chess_spectral.encoder.CHANNELS` order
        (A1, A2, B1, B2, E, F1, F2, F3, FA, FD).

    Notes
    -----
    log1p (= ln(1+x)) is used instead of raw energy because the
    energies span 4-5 orders of magnitude — F2 / F3 dominate at
    midgame, A1 / E dominate at opening, FA / FD dominate at endgame.
    Without the log transform, k-means clustering is dominated by
    whichever channel has the largest absolute scale, which destroys
    the phase signal.
    """
    vec = encode_640(pos)
    energies = channel_energies(vec)
    # Order matters — use the canonical channel order.
    raw = np.array(
        [energies[name] for name in _CHANNEL_NAMES_2D],
        dtype=np.float64,
    )
    return np.log1p(raw)


def extract_fingerprints_from_pgn(
    pgn_path: str | Path,
    *,
    max_games: Optional[int] = None,
    sample_every: int = 1,
    skip_initial_plies: int = 0,
) -> List[Tuple[str, np.ndarray]]:
    """Walk a PGN file, sub-sample positions, return (FEN, fingerprint)
    pairs.

    Parameters
    ----------
    pgn_path
        Path to a PGN file (any size; iterated game-by-game).
    max_games : int, optional
        If set, stop after this many games.
    sample_every : int, optional
        Sub-sample plies — keep every Nth ply. Default 1 (every ply).
        Use larger values (e.g., 3) on big PGNs to keep the
        fingerprint count manageable.
    skip_initial_plies : int, optional
        Skip the first N plies of every game. The opening positions
        are highly correlated across games (every game has the same
        starting position) so sub-sampling there can over-represent
        the opening cluster.

    Returns
    -------
    list of (fen, fingerprint) tuples
        ``fen`` is the FEN string at the sampled ply; ``fingerprint``
        is the 10-dim log-energy vector. Caller iterates this list.

    Raises
    ------
    ImportError
        If ``python-chess`` is not installed.
    """
    try:
        import chess
        import chess.pgn
    except ImportError:
        raise ImportError(
            "extract_fingerprints_from_pgn requires python-chess; "
            "install via `pip install python-chess`."
        )

    fingerprints: List[Tuple[str, np.ndarray]] = []
    games_seen = 0
    with open(pgn_path, "r", encoding="utf-8", errors="replace") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            games_seen += 1
            board = game.board()
            ply_idx = 0
            for move in game.mainline_moves():
                board.push(move)
                ply_idx += 1
                if ply_idx <= skip_initial_plies:
                    continue
                if (ply_idx - skip_initial_plies) % sample_every != 0:
                    continue
                fen = board.fen()
                pos = fen_to_pos(fen)
                fp = extract_fingerprint_2d(pos)
                fingerprints.append((fen, fp))
            if max_games is not None and games_seen >= max_games:
                break
    return fingerprints


# ─── Pure-numpy k-means ─────────────────────────────────────────────


def kmeans_cluster(
    points: List[np.ndarray] | np.ndarray,
    k: int = 3,
    *,
    max_iter: int = 100,
    seed: int = 42,
    tol: float = 1e-6,
) -> Tuple[np.ndarray, np.ndarray]:
    """Pure-numpy k-means clustering on a list of fingerprint vectors.

    Lloyd's algorithm with k-means++ initialization. ~30 LOC, no
    sklearn dependency.

    Parameters
    ----------
    points
        List of ``(d,)``-shape arrays, or a single ``(N, d)`` array.
        All points must have the same dimension.
    k : int, optional
        Number of clusters. Default 3 (open/mid/end).
    max_iter : int, optional
        Lloyd-iteration cap.
    seed : int, optional
        RNG seed for reproducible initialization.
    tol : float, optional
        Stop when centroid movement drops below this Frobenius-norm
        threshold.

    Returns
    -------
    centroids : ndarray, shape (k, d), dtype float64
    labels : ndarray, shape (N,), dtype int64
        Cluster index in ``[0, k)`` for each input point.
    """
    rng = np.random.default_rng(seed)
    if isinstance(points, list):
        if not points:
            return (
                np.zeros((k, 0), dtype=np.float64),
                np.zeros(0, dtype=np.int64),
            )
        X = np.stack(points).astype(np.float64)
    else:
        X = np.asarray(points, dtype=np.float64)
    n, d = X.shape
    if n < k:
        raise ValueError(
            f"k-means: need at least k={k} points, got {n}"
        )

    # k-means++ init: first center uniform; subsequent centers weighted
    # by squared distance to nearest already-chosen center.
    centroids = np.empty((k, d), dtype=np.float64)
    centroids[0] = X[rng.integers(n)]
    for i in range(1, k):
        dists = np.min(
            np.linalg.norm(X[:, None, :] - centroids[:i, :], axis=2) ** 2,
            axis=1,
        )
        if dists.sum() == 0:
            centroids[i] = X[rng.integers(n)]
        else:
            probs = dists / dists.sum()
            centroids[i] = X[rng.choice(n, p=probs)]

    # Lloyd iterations.
    labels = np.zeros(n, dtype=np.int64)
    for _it in range(max_iter):
        dists = np.linalg.norm(X[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = np.argmin(dists, axis=1)
        new_centroids = np.empty_like(centroids)
        for i in range(k):
            mask = new_labels == i
            if mask.any():
                new_centroids[i] = X[mask].mean(axis=0)
            else:
                # Empty cluster — re-seed from a random point.
                new_centroids[i] = X[rng.integers(n)]
        movement = float(np.linalg.norm(new_centroids - centroids))
        centroids = new_centroids
        labels = new_labels
        if movement < tol:
            break

    return centroids, labels


# ─── Phase labeling heuristic ───────────────────────────────────────


def label_phases(
    centroids: np.ndarray,
    *,
    channel_names: Tuple[str, ...] = _CHANNEL_NAMES_2D,
) -> Dict[int, str]:
    """Map cluster indices to {'opening', 'midgame', 'endgame'} labels
    by inspecting the centroids.

    Heuristic (k=3 only):

      * The cluster with **highest sum of structural channels**
        (A1+B1+B2 — castling/D₄-symmetric channels active in opening)
        → "opening"
      * The cluster with **lowest total energy** → "endgame"
      * The remaining cluster → "midgame"

    For k != 3, raises :class:`ValueError` — the heuristic doesn't
    generalize. Callers wanting K > 3 should inspect centroids
    themselves.

    Parameters
    ----------
    centroids : ndarray, shape (k, d)
    channel_names : tuple of str, optional
        Channel names in the order matching the centroid dimensions.
        Defaults to the 10-channel 2D order.

    Returns
    -------
    dict mapping cluster_index → 'opening' / 'midgame' / 'endgame'

    Raises
    ------
    ValueError
        If the centroids array doesn't have shape ``(3, len(channel_names))``.
    """
    k, d = centroids.shape
    if k != 3:
        raise ValueError(
            f"label_phases is k=3-specific; got centroids with k={k}. "
            f"For k > 3 inspect centroids yourself."
        )
    if d != len(channel_names):
        raise ValueError(
            f"centroid dim {d} != len(channel_names) {len(channel_names)}"
        )

    # Find structural-channel indices (A1 + B1 + B2).
    structural_idx = [
        channel_names.index(c) for c in ('A1', 'B1', 'B2')
        if c in channel_names
    ]
    structural_sum = centroids[:, structural_idx].sum(axis=1)
    total_energy = centroids.sum(axis=1)

    opening_idx = int(np.argmax(structural_sum))
    # Endgame: cluster with lowest total energy among remaining clusters.
    remaining = [i for i in range(k) if i != opening_idx]
    endgame_idx = int(remaining[
        np.argmin([total_energy[i] for i in remaining])
    ])
    midgame_idx = int(next(
        i for i in range(k) if i not in (opening_idx, endgame_idx)
    ))

    return {
        opening_idx: 'opening',
        midgame_idx: 'midgame',
        endgame_idx: 'endgame',
    }


# ─── Trained classifier ─────────────────────────────────────────────


@dataclass
class PhaseClassifier:
    """A trained phase classifier — encapsulates centroids + label map.

    Use :func:`train_phase_classifier_from_pgn` to build one from a
    PGN corpus, then :meth:`classify` on individual positions.
    """
    centroids: np.ndarray
    phase_map: Dict[int, str]
    channel_names: Tuple[str, ...]

    def classify(self, pos: Dict[int, str]) -> str:
        """Classify a position dict into a phase label.

        Returns one of 'opening', 'midgame', 'endgame'.
        """
        fp = extract_fingerprint_2d(pos)
        dists = np.linalg.norm(self.centroids - fp, axis=1)
        cluster = int(np.argmin(dists))
        return self.phase_map[cluster]

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict."""
        return {
            'centroids': self.centroids.tolist(),
            'phase_map': {str(k): v for k, v in self.phase_map.items()},
            'channel_names': list(self.channel_names),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PhaseClassifier":
        return cls(
            centroids=np.asarray(data['centroids'], dtype=np.float64),
            phase_map={int(k): v for k, v in data['phase_map'].items()},
            channel_names=tuple(data['channel_names']),
        )


def train_phase_classifier_from_pgn(
    pgn_path: str | Path,
    *,
    max_games: Optional[int] = None,
    sample_every: int = 3,
    skip_initial_plies: int = 4,
    seed: int = 42,
) -> Tuple[PhaseClassifier, List[Tuple[str, np.ndarray, int]]]:
    """End-to-end: PGN file → trained PhaseClassifier.

    Returns
    -------
    classifier : PhaseClassifier
        The trained classifier, ready for ``.classify(pos)`` calls.
    fingerprints : list of (fen, fingerprint, cluster_idx)
        The training corpus with cluster assignments — useful for
        diagnostic output, the CLI's JSON dump, and re-using the
        labeled corpus for benchmarks.
    """
    fps = extract_fingerprints_from_pgn(
        pgn_path,
        max_games=max_games,
        sample_every=sample_every,
        skip_initial_plies=skip_initial_plies,
    )
    if len(fps) < 3:
        raise ValueError(
            f"Need at least 3 fingerprints for k=3 clustering; got "
            f"{len(fps)} from {pgn_path}"
        )
    fp_array = np.stack([fp for _, fp in fps])
    centroids, labels = kmeans_cluster(fp_array, k=3, seed=seed)
    phase_map = label_phases(centroids)
    classifier = PhaseClassifier(
        centroids=centroids,
        phase_map=phase_map,
        channel_names=_CHANNEL_NAMES_2D,
    )
    labeled = [
        (fen, fp, int(labels[i]))
        for i, (fen, fp) in enumerate(fps)
    ]
    return classifier, labeled


# ─── CLI ────────────────────────────────────────────────────────────


def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="chess_spectral.phase_classifier",
        description=(
            "Train a data-driven phase classifier from a PGN corpus. "
            "Clusters position fingerprints (log-channel-energies) "
            "into k=3 phases, labels them via heuristic, dumps "
            "labeled corpus + classifier as JSON."
        ),
    )
    parser.add_argument(
        "pgn_path", type=Path,
        help="Path to a PGN file.",
    )
    parser.add_argument(
        "--max-games", type=int, default=None,
        help="Stop after N games (default: all)."
    )
    parser.add_argument(
        "--sample-every", type=int, default=3,
        help="Sub-sample every Nth ply (default: 3)."
    )
    parser.add_argument(
        "--skip-initial-plies", type=int, default=4,
        help=(
            "Skip the first N plies of every game (default: 4) — "
            "every game starts from the same FEN, so over-sampling "
            "the early plies skews the opening cluster."
        ),
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed for k-means initialization (default: 42)."
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help=(
            "Write classifier + labeled corpus as JSON to this path. "
            "If omitted, only summary statistics are printed."
        ),
    )

    args = parser.parse_args(argv)
    classifier, labeled = train_phase_classifier_from_pgn(
        args.pgn_path,
        max_games=args.max_games,
        sample_every=args.sample_every,
        skip_initial_plies=args.skip_initial_plies,
        seed=args.seed,
    )

    # Summary
    n_total = len(labeled)
    counts = {phase: 0 for phase in classifier.phase_map.values()}
    for _, _, cluster in labeled:
        counts[classifier.phase_map[cluster]] += 1

    print(f"Trained on {n_total} positions from {args.pgn_path}", file=sys.stderr)
    print(f"  centroids shape: {classifier.centroids.shape}", file=sys.stderr)
    print(f"  cluster phase labels: {classifier.phase_map}", file=sys.stderr)
    print(f"  position counts:", file=sys.stderr)
    for phase, count in sorted(counts.items()):
        pct = 100.0 * count / n_total
        print(f"    {phase}: {count} ({pct:.1f}%)", file=sys.stderr)

    if args.output is not None:
        with open(args.output, "w", encoding="utf-8") as f:
            payload = {
                'classifier': classifier.to_dict(),
                'labeled_corpus': [
                    {'fen': fen, 'fingerprint': fp.tolist(), 'cluster': cluster,
                     'phase': classifier.phase_map[cluster]}
                    for fen, fp, cluster in labeled
                ],
            }
            json.dump(payload, f, indent=2)
        print(f"Wrote {args.output} ({n_total} entries)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "extract_fingerprint_2d",
    "extract_fingerprints_from_pgn",
    "kmeans_cluster",
    "label_phases",
    "PhaseClassifier",
    "train_phase_classifier_from_pgn",
    "N_FINGERPRINT_DIMS_2D",
]
