"""Follow-up iv+ — Othello per-game Pearson(E_A1, E_E) distribution.

Open-7 on chess revealed a Simpson's paradox: per-game Pearson
(E_A1, E_E) is negative (median -0.18 to -0.58 across chess
corpora) but pooling washes it to near-zero (pooled +0.04).
The A1/E mirror IS present in chess within games but hidden by
between-game variation when pooled.

This runner runs the same per-game analysis for Othello on the 4
committed PGN corpora, so we can compare the two species.

Magnitudes to expect:
  - Pooled Othello (from phase1e_replay_*): a1_occ_vs_e_occ ~-0.07
    to -0.14 at trajectory level.
  - If per-game Pearson is also more negative than pooled, Othello
    has the same Simpson structure as chess.
  - If per-game Pearson matches pooled, Othello is genuinely less
    Simpson-paradox-prone than chess (possibly because of its
    simpler state space, single piece type).
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

from othello_spectral import encode_768
from othello_spectral.tables import CHANNEL_NAMES
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)

_ensure_utf8_stdio()


def _iter_pgn_games(pgn_path: Path):
    """Replay PGN on the fly; yield per-game encoding stack."""
    games = parse_pgn_file(pgn_path)
    for gi, g in enumerate(games):
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        if len(states) < 5:
            continue
        encs = np.array(
            [encode_768(st) for st in states], dtype=np.float64,
        )
        yield encs
        if (gi + 1) % 100 == 0:
            print(f"  processed {gi + 1} games", flush=True)


# Channel indices in encoder order (see othello_spectral.tables).
# Per the encoder layout:
#   0..4: magn_{A1,A2,B1,B2,E}minus on magnetisation s
#   5..9: occ_{A1,A2,B1,B2,E}plus  on occupation s^2
IDX = {name: i for i, name in enumerate(CHANNEL_NAMES)}


def _per_game_pearson(encs: np.ndarray, ch_a: int, ch_b: int) -> float | None:
    """Compute per-game Pearson between the energies of two channels
    across plies.  Each frame's energy for channel k is the squared
    norm of its 64-dim block."""
    n = encs.shape[0]
    if n < 10:
        return None
    a = np.array([
        np.dot(encs[i, ch_a * 64:(ch_a + 1) * 64],
               encs[i, ch_a * 64:(ch_a + 1) * 64])
        for i in range(n)
    ])
    b = np.array([
        np.dot(encs[i, ch_b * 64:(ch_b + 1) * 64],
               encs[i, ch_b * 64:(ch_b + 1) * 64])
        for i in range(n)
    ])
    if a.std() < 1e-9 or b.std() < 1e-9:
        return None
    return float(pearsonr(a, b).statistic)


PAIRS = [
    ("a1_minus_vs_e_minus",         IDX["magn_A1minus"], IDX["magn_Eminus"]),
    ("occ_a1_vs_occ_e",             IDX["occ_A1plus"],   IDX["occ_Eplus"]),
    ("a1_minus_vs_b2_minus",        IDX["magn_A1minus"], IDX["magn_B2minus"]),
    ("occ_a1_vs_occ_b2",            IDX["occ_A1plus"],   IDX["occ_B2plus"]),
    ("fiber_ortho_vs_fiber_diag",   IDX["fiber_ortho_s"],IDX["fiber_diag_s"]),
]


def analyse(corpora: list[tuple[str, Path]]) -> dict:
    out: dict = {"per_corpus": {}}
    for tag, pgn_path in corpora:
        print(f"\n=== {tag}  ({pgn_path.name}) ===")
        corpus_rec: dict = {}
        per_pair: dict[str, list[float]] = {name: [] for name, _, _ in PAIRS}
        n_games = 0
        for encs in _iter_pgn_games(pgn_path):
            n_games += 1
            for name, ca, cb in PAIRS:
                r = _per_game_pearson(encs, ca, cb)
                if r is not None:
                    per_pair[name].append(r)
        for name, vals in per_pair.items():
            arr = np.array(vals)
            if arr.size:
                corpus_rec[name] = {
                    "n_games": int(arr.size),
                    "mean":   float(arr.mean()),
                    "median": float(np.median(arr)),
                    "std":    float(arr.std()),
                    "min":    float(arr.min()),
                    "max":    float(arr.max()),
                    "q25":    float(np.percentile(arr, 25)),
                    "q75":    float(np.percentile(arr, 75)),
                }
        corpus_rec["n_games_total"] = n_games
        out["per_corpus"][tag] = corpus_rec
        print(f"  {'pair':28s}  {'N':>4s}  {'mean':>8s}  {'median':>8s}  {'q25':>7s}  {'q75':>7s}  {'range':>16s}")
        for name in [p[0] for p in PAIRS]:
            r = corpus_rec.get(name)
            if r is None:
                continue
            print(
                f"  {name:28s}  {r['n_games']:>4d}  {r['mean']:+8.4f}  "
                f"{r['median']:+8.4f}  {r['q25']:+7.3f}  {r['q75']:+7.3f}  "
                f"[{r['min']:+.3f}, {r['max']:+.3f}]"
            )
    return out


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    results_dir = research_dir.parent / "results"
    default_out = results_dir / "phase1e_othello_a1_e_per_game.json"
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--out", type=Path, default=default_out,
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    research_dir = Path(__file__).resolve().parent
    dataset = research_dir.parent / "dataset"
    corpora = [
        ("barcelona_35",   dataset / "liveothello_Barcelona_EGP_2026.pgn"),
        ("wc2005_23",      dataset / "liveothello_World_Championships_2005.pgn"),
        ("apr2026_414",    dataset / "liveothello-2026-APR.pgn"),
        ("all2025_2178",   dataset / "liveothello_2025_all.pgn"),
    ]
    corpora = [(t, p) for t, p in corpora if p.exists()]
    if not corpora:
        print("no corpora found", file=sys.stderr)
        return 2
    summary = analyse(corpora)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
