#!/usr/bin/env python3
"""analyze_safety.py — replay a PGN, compute per-ply spectral safety field
and compare ΔS against the Lichess-annotated Δeval.

Usage:
    python analyze_safety.py <game.pgn> [-o out.csv]

Reports:
    - Per-ply table: S_before, S_after, ΔS_mover, eval, ΔEval_mover, NAG
    - Spearman(ΔS_mover, ΔEval_mover) overall and per side
    - Rank of Lichess-flagged ?/??/?! plies within the ΔS_mover distribution
    - Companion: ΔE channel-energy row per ply in the CSV

Also writes a CSV for plotting / follow-up analysis.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

import numpy as np
import chess
import chess.pgn

# Package layout: this driver lives next to the chess_spectral package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from chess_spectral import channel_energies, encode_640
from chess_spectral.safety_field import compute_safety_field, side_most_exposed

# ─── NAG / eval extraction (mirrors pgn_bridge.py) ───────────────────────

_NAG_MAP      = {4: "??", 2: "?", 6: "?!", 5: "!?", 1: "!", 3: "!!"}
_NAG_PRIORITY = (4, 2, 6, 5, 3, 1)


def _nag_tag(nags):
    for n in _NAG_PRIORITY:
        if n in nags:
            return _NAG_MAP[n]
    return None


def _eval_from_node(node):
    """Return (numeric_pawns, raw_str) or (None, None). Mate is treated as
    ±100 pawns so the numeric field is always finite for ranking."""
    pov = node.eval()
    if pov is None:
        return None, None
    sc = pov.white()
    m = sc.mate()
    if m is not None:
        return (100.0 if m > 0 else -100.0), f"#{m}"
    cp = sc.score()
    if cp is None:
        return None, None
    return cp / 100.0, f"{cp / 100.0:.2f}"


def _board_to_pos(board):
    """python-chess board → encoder pos dict. Square convention matches
    pgn_bridge.fen_to_pos (row 0 = rank 8)."""
    pos = {}
    for square, piece in board.piece_map().items():
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        idx = (7 - rank) * 8 + file
        pos[idx] = piece.symbol()
    return pos


def _sqname(idx):
    if idx is None:
        return ''
    row, col = idx // 8, idx % 8
    return chr(ord('a') + col) + str(8 - row)


def _piece_moved(san: str) -> str:
    """Single-char piece type from a SAN. Castling (O-O / O-O-O) -> 'K';
    uppercase leading letter in {N,B,R,Q,K} -> that letter; otherwise pawn."""
    if not san:
        return 'P'
    if san.startswith('O-O'):
        return 'K'
    c = san[0]
    return c if c in 'NBRQK' else 'P'


# ─── Analysis driver ─────────────────────────────────────────────────────

def analyze(pgn_path: str, out_csv: str | None = None) -> int:
    text = Path(pgn_path).read_text(encoding='utf-8')
    game = chess.pgn.read_game(io.StringIO(text))
    if game is None:
        print("Could not parse PGN", file=sys.stderr)
        return 1

    board = game.board()

    pos_before = _board_to_pos(board)
    sf_before  = compute_safety_field(pos_before)
    ce_before  = channel_energies(encode_640(pos_before))

    # Starting-position smoke assertion: mirror symmetry → S_total ≈ 0.
    if abs(sf_before['S_total']) > 1e-9:
        print(f"WARNING: starting position S_total = {sf_before['S_total']:.6g} "
              f"(expected 0 by mirror symmetry)", file=sys.stderr)

    eval_before_num, eval_before_str = 0.0, "0.00"

    records: list[dict] = []
    node, ply = game, 1
    while node.variations:
        nxt  = node.variation(0)
        move = nxt.move
        side = 'w' if board.turn == chess.WHITE else 'b'
        san  = board.san(move)
        nag  = _nag_tag(nxt.nags) if nxt.nags else None
        pm   = _piece_moved(san)
        me_before = side_most_exposed(sf_before, side)

        board.push(move)
        pos_after = _board_to_pos(board)
        sf_after  = compute_safety_field(pos_after)
        ce_after  = channel_energies(encode_640(pos_after))
        eval_after_num, eval_after_str = _eval_from_node(nxt)

        dS        = sf_after['S_total'] - sf_before['S_total']
        dS_mover  = dS if side == 'w' else -dS

        if eval_after_num is not None and eval_before_num is not None:
            dEval       = eval_after_num - eval_before_num
            dEval_mover = dEval if side == 'w' else -dEval
        else:
            dEval_mover = None

        dE = {k: ce_after[k] - ce_before[k] for k in ce_before}

        rec = {
            'ply':           ply,
            'side':          side,
            'san':           san,
            'piece_moved':   pm,
            'nag':           nag or '',
            'eval_before':   eval_before_str or '',
            'eval_after':    eval_after_str or '',
            'dEval_mover':   f"{dEval_mover:.3f}" if dEval_mover is not None else '',
            'S_before':      f"{sf_before['S_total']:.4f}",
            'S_after':       f"{sf_after['S_total']:.4f}",
            'dS':            f"{dS:.4f}",
            'dS_mover':      f"{dS_mover:.4f}",
            'mover_exposed': _sqname(me_before),
            **{f'dE_{k}': f"{v:.4f}" for k, v in dE.items()},
        }
        records.append(rec)

        sf_before = sf_after
        ce_before = ce_after
        if eval_after_num is not None:
            eval_before_num, eval_before_str = eval_after_num, eval_after_str
        node, ply = nxt, ply + 1

    if out_csv:
        with open(out_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
        print(f"Wrote {len(records)} plies -> {out_csv}", file=sys.stderr)

    _print_summary(records)
    return 0


# ─── Reporting ───────────────────────────────────────────────────────────

def _print_table(records, limit=None):
    hdr = f"{'Ply':>3} {'Side':>4} {'Move':<8} {'S_bef':>8} {'S_aft':>8} {'dS_m':>8} " \
          f"{'Eval':>7} {'dEv_m':>7} {'NAG':<3} {'Exp':>4}"
    print(hdr)
    print("-" * len(hdr))
    rows = records if limit is None else records[:limit]
    for r in rows:
        flag = " <--" if r['nag'] in ("??", "?") else ""
        print(f"{r['ply']:>3} {r['side']:>4} {r['san']:<8} "
              f"{r['S_before']:>8} {r['S_after']:>8} {r['dS_mover']:>8} "
              f"{r['eval_after']:>7} {r['dEval_mover']:>7} "
              f"{r['nag']:<3} {r['mover_exposed']:>4}{flag}")


def _print_summary(records):
    print()
    print("Per-ply safety field:")
    print()
    _print_table(records)

    try:
        from scipy.stats import spearmanr
    except ImportError:
        print("\nscipy not installed — skipping correlation analysis")
        return

    # Overall correlation
    with_eval = [r for r in records if r['dEval_mover'] != '']
    if len(with_eval) < 4:
        print("\nNot enough eval-annotated plies for correlation.")
        return

    ds = np.array([float(r['dS_mover'])    for r in with_eval])
    de = np.array([float(r['dEval_mover']) for r in with_eval])
    rho, p = spearmanr(ds, de)
    print(f"\nSpearman(dS_mover, dEval_mover), n={len(ds)}: rho = {rho:+.3f}, p = {p:.4g}")

    for color, label in (('w', 'white'), ('b', 'black')):
        sub = [r for r in with_eval if r['side'] == color]
        if len(sub) < 4:
            continue
        ds_s = np.array([float(r['dS_mover'])    for r in sub])
        de_s = np.array([float(r['dEval_mover']) for r in sub])
        rho_s, p_s = spearmanr(ds_s, de_s)
        print(f"  {label} moves (n={len(ds_s)}): rho = {rho_s:+.3f}, p = {p_s:.4g}")

    # Rank of flagged moves within the dS_mover distribution.
    print("\ndS_mover rank of Lichess-flagged plies (rank 1 = worst dS):")
    sorted_asc = sorted(records, key=lambda r: float(r['dS_mover']))
    flagged = [(i, r) for i, r in enumerate(sorted_asc)
               if r['nag'] in ("??", "?", "?!")]
    if not flagged:
        print("  (no NAG-annotated plies)")
    n = len(records)
    for i, r in flagged:
        pct = 100.0 * (i + 1) / n
        print(f"  rank {i+1:>3}/{n}  ({pct:>5.1f}% tail)  "
              f"ply {r['ply']:>3} {r['side']} {r['san']:<8} {r['nag']:<3}  "
              f"dS_mover={r['dS_mover']:>8}  dEv_mover={r['dEval_mover']:>7}")

    # Blunder precision/recall at the 10%-tail per-side threshold.
    def _bottom_tail_set(color: str, frac: float = 0.10):
        sub = [r for r in records if r['side'] == color]
        if not sub:
            return set()
        sub_sorted = sorted(sub, key=lambda r: float(r['dS_mover']))
        k = max(1, int(round(frac * len(sub_sorted))))
        return {id(r) for r in sub_sorted[:k]}

    alerts = _bottom_tail_set('w') | _bottom_tail_set('b')
    truth = {id(r) for r in records
             if r['nag'] in ("??", "?")
             or (r['dEval_mover'] and abs(float(r['dEval_mover'])) > 1.0
                 and float(r['dEval_mover']) < 0)}

    tp = len(alerts & truth)
    fp = len(alerts - truth)
    fn = len(truth - alerts)
    if alerts or truth:
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall    = tp / (tp + fn) if (tp + fn) else 0.0
        print(f"\nBlunder detection (bottom-10% dS per side vs NAG in {{??,?}} "
              f"or dEv_mover<-1.0):")
        print(f"  precision = {precision:.2f}  recall = {recall:.2f}  "
              f"(tp={tp}, fp={fp}, fn={fn})")


# ─── Entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    ap.add_argument("pgn", help="Path to PGN file")
    ap.add_argument("-o", "--out", help="Output CSV path", default=None)
    args = ap.parse_args()
    sys.exit(analyze(args.pgn, args.out))
