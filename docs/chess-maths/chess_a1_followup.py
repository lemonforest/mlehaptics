#!/usr/bin/env python3
"""
A1 Depth-Gap Follow-Up Experiments
====================================

Three experiments building on the A1 discovery (rho=+0.452, p=0.0005):
  1. Symmetry-breaking channels vs static evaluation (Z2 spin symmetry)
  2. Game trajectory analysis (ply-by-ply spectral evolution)
  3. Othello preparation (design document, no code)

Key finding from depth-gap experiment: A1 energy (D4-invariant channel)
significantly predicts which positions reward deep Stockfish search.
Fiber energy did NOT replicate (rho=+0.166, p=0.23).

Z2 insight: The full symmetry group is D4 x Z2 (16 elements).
  - Channel ENERGY (norm) is D4 x Z2 invariant -> predicts complexity
  - Channel SIGNED SUM is Z2-antisymmetric -> predicts advantage

Dependencies: numpy, scipy, python-chess, stockfish engine
Imports infrastructure from encoder_512.py and chess_depth_gap_expanded.py
"""

import sys
import os
import io

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force unbuffered output for progress visibility
os.environ['PYTHONUNBUFFERED'] = '1'

# Import from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from encoder_512 import (
    sq, rc, VALS, SPECTRAL_VALS, MATERIAL_CP,
    board_signal, project_irrep,
    encode_512_spectral, encode_A1_spectral,
    pos_to_fen, stockfish_eval_batch, cosine,
    STOCKFISH_PATH,
)
from chess_depth_gap_expanded import (
    fen_to_pos, partial_spearman, build_position_corpus,
    evaluate_corpus, piece_count, significance_flag,
    SF_DEPTH_SHALLOW, SF_DEPTH_DEEP,
    IRREP_DIM_END, FIBER_DIM_START, TOTAL_DIM,
    SIGNIFICANCE_ALPHA, TRENDING_ALPHA,
)
import numpy as np
from scipy.stats import spearmanr
import chess
import chess.pgn


# ═══════════════════════════════════════════════════════════════
# CONSTANTS (no magic numbers)
# ═══════════════════════════════════════════════════════════════

IRREP_NAMES = ['A1', 'A2', 'B1', 'B2', 'E']
IRREP_DIM = 64                          # Dimensions per irrep channel
BREAKING_IRREPS = ['A2', 'B1', 'B2', 'E']  # Symmetry-breaking channels

SF_DEPTH_TRAJECTORY = 12                # SF eval depth for game trajectories
COMPUTE_DEEP_GAP = True                 # Set False to skip d20 in trajectories (saves time)
MIN_PLY_FOR_CORRELATION = 10            # Minimum plies for per-game correlation

# Number of top-percentile plies for peak alignment test
PEAK_PERCENTILE = 25                    # Top 25% of plies count as "peaks"


# ═══════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════

def compute_channel_metrics(pos):
    """Compute both energy (Z2-invariant) and signed sum (Z2-antisymmetric)
    for each D4 irrep channel, plus fiber and combined breaking energy.

    Returns dict with keys:
      '{name}_energy': float  -- norm of irrep projection (Z2-invariant)
      '{name}_signed': float  -- sum of irrep projection (Z2-antisymmetric)
      'breaking_energy': float -- norm of concatenated A2+B1+B2+E
      'breaking_signed': float -- sum of concatenated A2+B1+B2+E
      'fiber_energy': float    -- norm of fiber channels (indices 320:512)
    """
    sig = board_signal(pos, vals=SPECTRAL_VALS)
    enc_full = encode_512_spectral(pos)

    result = {}
    breaking_channels = []

    for name in IRREP_NAMES:
        proj = project_irrep(sig, name)
        result[f'{name}_energy'] = float(np.linalg.norm(proj))
        result[f'{name}_signed'] = float(np.sum(proj))
        if name in BREAKING_IRREPS:
            breaking_channels.append(proj)

    breaking_concat = np.concatenate(breaking_channels)
    result['breaking_energy'] = float(np.linalg.norm(breaking_concat))
    result['breaking_signed'] = float(np.sum(breaking_concat))
    result['fiber_energy'] = float(np.linalg.norm(enc_full[FIBER_DIM_START:]))

    return result


def spectral_material_balance(pos):
    """Material balance using SPECTRAL_VALS (not centipawns).

    This is the appropriate control variable for partial correlations
    on signed channel sums, since the signal itself uses SPECTRAL_VALS.
    """
    return sum(SPECTRAL_VALS[p] for p in pos.values())


def stockfish_eval_fens(fen_list, depth):
    """Evaluate FEN strings directly with Stockfish, preserving
    side-to-move, castling rights, and en passant from the FEN.

    Unlike stockfish_eval_batch (which uses pos_to_fen with 'w - - 0 1'),
    this function passes each FEN to the engine as-is.

    Returns list of centipawn scores (white's perspective), or None entries
    for invalid/failed positions.
    """
    try:
        import chess.engine
    except ImportError:
        return [None] * len(fen_list)

    scores = []
    engine = None

    for fen in fen_list:
        board = chess.Board(fen)
        if not board.is_valid():
            scores.append(None)
            continue
        try:
            if engine is None:
                engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
            info = engine.analyse(board, chess.engine.Limit(depth=depth))
            score = info['score'].white()
            if score.is_mate():
                cp = 10000 * (1 if score.mate() > 0 else -1)
            else:
                cp = score.score()
            scores.append(cp)
        except Exception:
            scores.append(None)
            try:
                engine.quit()
            except Exception:
                pass
            engine = None

    if engine is not None:
        try:
            engine.quit()
        except Exception:
            pass

    return scores


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 1: SYMMETRY-BREAKING CHANNELS VS STATIC EVALUATION
#
# Z2 spin symmetry: D4 x Z2 is the full symmetry group.
#   - Channel ENERGY (norm) is D4 x Z2 invariant -> complexity
#   - Channel SIGNED SUM is Z2-antisymmetric -> advantage
#
# Test: A1 energy -> depth gap (complexity)
#       Breaking signed sum -> signed SF eval (advantage)
#       Partial correlation controlling for material balance
# ═══════════════════════════════════════════════════════════════

def run_experiment_1(evaluated):
    """Symmetry-breaking channels vs static evaluation.

    evaluated: list of (pos, category, label, sf_d1, sf_d20) from evaluate_corpus.
    """
    print("\n" + "=" * 70)
    print("  EXPERIMENT 1: Symmetry-Breaking Channels vs Static Evaluation")
    print("  Z2 spin symmetry: energy -> complexity, signed sum -> advantage")
    print("=" * 70)

    n = len(evaluated)
    print(f"\n  Using {n} positions from depth-gap corpus")

    # ── Compute per-position metrics ────────────────────────────
    all_metrics = []
    for pos, category, label, sf_d1, sf_d20 in evaluated:
        ch = compute_channel_metrics(pos)
        ch['sf_d1'] = sf_d1
        ch['sf_d20'] = sf_d20
        ch['depth_gap'] = abs(sf_d20 - sf_d1)
        ch['n_pieces'] = piece_count(pos)
        ch['mat_balance'] = spectral_material_balance(pos)
        all_metrics.append(ch)

    # ── Build arrays ────────────────────────────────────────────
    def col(key):
        return np.array([m[key] for m in all_metrics])

    depth_gap = col('depth_gap')
    sf_d20_signed = col('sf_d20')
    sf_d20_abs = np.abs(sf_d20_signed)
    sf_d1_signed = col('sf_d1')
    sf_d1_abs = np.abs(sf_d1_signed)
    n_pieces = col('n_pieces')
    mat_balance = col('mat_balance')

    # ── Table 1: Energy (Z2-invariant) vs unsigned targets ──────
    print("\n  ── Table 1: Channel ENERGY (Z2-invariant) vs unsigned targets ──")
    print(f"  N = {n} positions. Spearman rho (** p<0.05, * p<0.10)")
    print()
    header = f"  {'Channel':>12s}  {'|Gap|':>10s}  {'|SF_d1|':>10s}  {'|SF_d20|':>10s}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    energy_channels = IRREP_NAMES + ['breaking', 'fiber']
    for ch_name in energy_channels:
        key = f'{ch_name}_energy'
        vals = col(key)
        results = []
        for target, target_name in [(depth_gap, '|Gap|'),
                                     (sf_d1_abs, '|SF_d1|'),
                                     (sf_d20_abs, '|SF_d20|')]:
            rho, p = spearmanr(vals, target)
            flag = '**' if p < SIGNIFICANCE_ALPHA else ('*' if p < TRENDING_ALPHA else '  ')
            results.append(f"{rho:+.3f}{flag}")
        print(f"  {ch_name:>12s}  {'  '.join(f'{r:>10s}' for r in results)}")

    # ── Table 2: Signed sum (Z2-antisymmetric) vs signed eval ───
    print("\n  ── Table 2: Channel SIGNED SUM (Z2-antisymmetric) vs signed eval ──")
    print(f"  N = {n} positions. Spearman rho (** p<0.05, * p<0.10)")
    print()
    header2 = f"  {'Channel':>12s}  {'SF_d1':>10s}  {'SF_d20':>10s}  {'Partial':>10s}"
    print(header2)
    print("  " + "-" * (len(header2) - 2))

    signed_channels = IRREP_NAMES + ['breaking']
    for ch_name in signed_channels:
        key = f'{ch_name}_signed'
        vals = col(key)
        rho1, p1 = spearmanr(vals, sf_d1_signed)
        flag1 = '**' if p1 < SIGNIFICANCE_ALPHA else ('*' if p1 < TRENDING_ALPHA else '  ')
        rho20, p20 = spearmanr(vals, sf_d20_signed)
        flag20 = '**' if p20 < SIGNIFICANCE_ALPHA else ('*' if p20 < TRENDING_ALPHA else '  ')

        # Partial correlation controlling for material balance
        rho_part, p_part = partial_spearman(vals, sf_d20_signed, mat_balance)
        flag_part = '**' if p_part < SIGNIFICANCE_ALPHA else ('*' if p_part < TRENDING_ALPHA else '  ')

        print(f"  {ch_name:>12s}  {rho1:+.3f}{flag1:>4s}  "
              f"{rho20:+.3f}{flag20:>4s}  {rho_part:+.3f}{flag_part:>4s}")

    # ── Partial correlations: energy vs |gap| controlling piece count ─
    print("\n  ── Partial: Energy vs |depth_gap|, controlling piece count ──")
    for ch_name in energy_channels:
        key = f'{ch_name}_energy'
        vals = col(key)
        rho_raw, p_raw = spearmanr(vals, depth_gap)
        rho_part, p_part = partial_spearman(vals, depth_gap, n_pieces)
        flag_raw = significance_flag(p_raw)
        flag_part = significance_flag(p_part)
        print(f"  {ch_name:>12s}  raw: rho={rho_raw:+.3f} (p={p_raw:.4f}) {flag_raw:>12s}"
              f"  | partial: rho={rho_part:+.3f} (p={p_part:.4f}) {flag_part:>12s}")

    # ── Summary ─────────────────────────────────────────────────
    print("\n  ── Experiment 1 Summary ──")
    a1_rho, a1_p = spearmanr(col('A1_energy'), depth_gap)
    brk_rho, brk_p = spearmanr(col('breaking_signed'), sf_d20_signed)
    brk_part_rho, brk_part_p = partial_spearman(
        col('breaking_signed'), sf_d20_signed, mat_balance)
    print(f"  A1 energy vs |depth_gap|:       rho={a1_rho:+.3f} (p={a1_p:.4f})")
    print(f"  Breaking signed vs SF_d20:      rho={brk_rho:+.3f} (p={brk_p:.4f})")
    print(f"  Breaking signed vs SF_d20 (partial, ctrl material): "
          f"rho={brk_part_rho:+.3f} (p={brk_part_p:.4f})")
    if a1_p < SIGNIFICANCE_ALPHA and brk_p < SIGNIFICANCE_ALPHA:
        print("  --> A1 captures COMPLEXITY, breaking captures ADVANTAGE (both significant)")
    elif a1_p < SIGNIFICANCE_ALPHA:
        print("  --> A1 captures COMPLEXITY (significant). Breaking -> advantage not confirmed.")
    else:
        print("  --> A1 result did not replicate. Investigate.")


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 2: GAME TRAJECTORY ANALYSIS
#
# Replay 5 famous games ply-by-ply. For each position compute
# spectral quantities and SF evaluation. Look for A1 energy
# peaking at the critical middlegame moment.
# ═══════════════════════════════════════════════════════════════

# ── PGN data for 5 famous games ─────────────────────────────

TRAJECTORY_PGNS = {
    'Kasparov-Topalov 1999': (
        "Wijk aan Zee — attacking masterpiece with Rxd4!! sacrifice",
        """[Event "Hoogovens"]
[Site "Wijk aan Zee"]
[Date "1999.01.20"]
[Round "4"]
[White "Kasparov, Garry"]
[Black "Topalov, Veselin"]
[Result "1-0"]

1. e4 d6 2. d4 Nf6 3. Nc3 g6 4. Be3 Bg7 5. Qd2 c6 6. f3 b5 7. Nge2 Nbd7
8. Bh6 Bxh6 9. Qxh6 Bb7 10. a3 e5 11. O-O-O Qe7 12. Kb1 a6 13. Nc1 O-O-O
14. Nb3 exd4 15. Rxd4 c5 16. Rd1 Nb6 17. g3 Kb8 18. Na5 Ba8 19. Bh3 d5
20. Qf4+ Ka7 21. Rhe1 d4 22. Nd5 Nbxd5 23. exd5 Qd6 24. Rxd4 cxd4
25. Re7+ Kb6 26. Qxd4+ Kxa5 27. b4+ Ka4 28. Qc3 Qxd5 29. Ra7 Bb7
30. Rxb7 Qc4 31. Qxf6 Kxa3 32. Qxa6+ Kxb4 33. c3+ Kxc3 34. Qa1+ Kd2
35. Qb2+ Kd1 36. Bf1 Rd2 37. Rd7 Rxd7 38. Bxc4 bxc4 39. Qxh8 Rd3
40. Qa8 c3 41. Qa4+ Ke1 42. f4 f5 43. Kc1 Rd2 44. Qa7 1-0"""
    ),

    'Carlsen-Anand WCC 2013 G5': (
        "World Championship — Carlsen's first win, endgame grind",
        """[Event "WCC 2013"]
[Site "Chennai"]
[Date "2013.11.15"]
[Round "5"]
[White "Carlsen, Magnus"]
[Black "Anand, Viswanathan"]
[Result "1-0"]

1. c4 e6 2. d4 d5 3. Nc3 c6 4. e4 dxe4 5. Nxe4 Bb4+ 6. Nc3 c5 7. a3 Ba5
8. Nf3 Nf6 9. Be3 Nc6 10. Qd3 cxd4 11. Nxd4 Ng4 12. O-O-O Nxe3 13. fxe3 Bc7
14. Nxc6 bxc6 15. Qxd8+ Bxd8 16. Be2 Ke7 17. Bf3 Bd7 18. Ne4 Bb6 19. c5 f5
20. cxb6 fxe4 21. b7 Rab8 22. Bxe4 Rxb7 23. Rhf1 Rb5 24. Rf4 g5 25. Rf3 h5
26. Rdf1 Be8 27. Bc2 Rc5 28. Rf6 h4 29. e4 a5 30. Kd2 Rb5 31. b3 Bh5
32. Kc3 Rc5+ 33. Kb2 Rd8 34. R1f2 Rd4 35. Rh6 Bd1 36. Bb1 Rb5 37. Kc3 c5
38. Rb2 e5 39. Rg6 a4 40. Rxg5 Rxb3+ 41. Rxb3 Bxb3 42. Rxe5+ Kd6 43. Rh5 Rd1
44. e5+ Kd5 45. Bh7 Rc1+ 46. Kb2 Rg1 47. Bg8+ Kc6 48. Rh6+ Kd7 49. Bxb3 axb3
50. Kxb3 Rxg2 51. Rxh4 Ke6 52. a4 Kxe5 53. a5 Kd6 54. Rh7 Kd5 55. a6 c4+
56. Kc3 Ra2 57. a7 Kc5 58. h4 1-0"""
    ),

    'Fischer-Spassky 1972 G6': (
        "World Championship — Fischer's Queen's Gambit positional masterpiece",
        """[Event "WCh 1972"]
[Site "Reykjavik"]
[Date "1972.07.23"]
[Round "6"]
[White "Fischer, Robert James"]
[Black "Spassky, Boris Vasilievich"]
[Result "1-0"]

1. c4 e6 2. Nf3 d5 3. d4 Nf6 4. Nc3 Be7 5. Bg5 O-O 6. e3 h6 7. Bh4 b6
8. cxd5 Nxd5 9. Bxe7 Qxe7 10. Nxd5 exd5 11. Rc1 Be6 12. Qa4 c5 13. Qa3 Rc8
14. Bb5 a6 15. dxc5 bxc5 16. O-O Ra7 17. Be2 Nd7 18. Nd4 Qf8 19. Nxe6 fxe6
20. e4 d4 21. f4 Qe7 22. e5 Rb8 23. Bc4 Kh8 24. Qh3 Nf8 25. b3 a5
26. f5 exf5 27. Rxf5 Nh7 28. Rcf1 Qd8 29. Qg3 Re7 30. h4 Rbb7 31. e6 Rbc7
32. Qe5 Qe8 33. a4 Qd8 34. R1f2 Qe8 35. R2f3 Qd8 36. Bd3 Qe8 37. Qe4 Nf6
38. Rxf6 gxf6 39. Rxf6 Kg8 40. Bc4 Kh8 41. Qf4 1-0"""
    ),

    'Botvinnik-Tal 1960 G6': (
        "World Championship — Tal's knight sacrifice in the King's Indian",
        """[Event "WCh 1960"]
[Site "Moscow"]
[Date "1960.03.26"]
[Round "6"]
[White "Botvinnik, Mikhail"]
[Black "Tal, Mikhail"]
[Result "0-1"]

1. c4 Nf6 2. Nf3 g6 3. g3 Bg7 4. Bg2 O-O 5. d4 d6 6. Nc3 Nbd7 7. O-O e5
8. e4 c6 9. h3 Qb6 10. d5 cxd5 11. cxd5 Nc5 12. Ne1 Bd7 13. Nd3 Nxd3
14. Qxd3 Rfc8 15. Rb1 Nh5 16. Be3 Qb4 17. Qe2 Rc4 18. Rfc1 Rac8 19. Kh2 f5
20. exf5 Bxf5 21. Ra1 Nf4 22. gxf4 exf4 23. Bd2 Qxb2 24. Rab1 f3 25. Rxb2 fxe2
26. Rb3 Rd4 27. Be1 Be5+ 28. Kg1 Bf4 29. Nxe2 Rxc1 30. Nxd4 Rxe1+ 31. Bf1 Be4
32. Ne2 Be5 33. f4 Bf6 34. Rxb7 Bxd5 35. Rc7 Bxa2 36. Rxa7 Bc4 37. Ra8+ Kf7
38. Ra7+ Ke6 39. Ra3 d5 40. Kf2 Bh4+ 41. Kg2 Kd6 42. Ng3 Bxg3 43. Bxc4 dxc4
44. Kxg3 Kd5 45. Ra7 c3 46. Rc7 Kd4 47. Rd7+ 0-1"""
    ),

    'Topalov-Anand WCC 2010 G1': (
        "World Championship — sharp Grunfeld, Anand blunders in preparation",
        """[Event "WCh 2010"]
[Site "Sofia"]
[Date "2010.04.24"]
[Round "1"]
[White "Topalov, Veselin"]
[Black "Anand, Viswanathan"]
[Result "1-0"]

1. d4 Nf6 2. c4 g6 3. Nc3 d5 4. cxd5 Nxd5 5. e4 Nxc3 6. bxc3 Bg7 7. Bc4 c5
8. Ne2 Nc6 9. Be3 O-O 10. O-O Na5 11. Bd3 b6 12. Qd2 e5 13. Bh6 cxd4
14. Bxg7 Kxg7 15. cxd4 exd4 16. Rac1 Qd6 17. f4 f6 18. f5 Qe5 19. Nf4 g5
20. Nh5+ Kg8 21. h4 h6 22. hxg5 hxg5 23. Rf3 Kf7 24. Nxf6 Kxf6 25. Rh3 Rg8
26. Rh6+ Kf7 27. Rh7+ Ke8 28. Rcc7 Kd8 29. Bb5 Qxe4 30. Rxc8+ 1-0"""
    ),
}


def replay_game_positions(pgn_str):
    """Replay a PGN game and extract position at each ply.

    Returns list of (pos_dict, fen_str, move_san) tuples.
    Index 0 is the starting position (move_san='start').
    Index i (i>0) is the position after the i-th half-move.
    """
    game = chess.pgn.read_game(io.StringIO(pgn_str))
    if game is None:
        return []

    board = game.board()
    positions = []

    # Starting position
    positions.append((fen_to_pos(board.fen()), board.fen(), 'start'))

    for move in game.mainline_moves():
        san = board.san(move)
        board.push(move)
        positions.append((fen_to_pos(board.fen()), board.fen(), san))

    return positions


def analyze_game_trajectory(game_name, metrics):
    """Analyze one game's trajectory. Print per-ply table and summary.

    metrics: list of dicts per ply with keys:
      ply, move, n_pieces, a1_energy, fiber_energy, breaking_energy,
      e_signed, mat_balance, sf_d1, sf_d12, sf_d20, depth_gap

    Returns summary dict for cross-game aggregation.
    """
    n_plies = len(metrics)
    print(f"\n  --- {game_name} ({n_plies} plies) ---")

    # ── Per-ply table ───────────────────────────────────────────
    has_gap = metrics[0]['depth_gap'] is not None
    if has_gap:
        print(f"  {'Ply':>4s}  {'Move':>8s}  {'Pcs':>3s}  {'A1_E':>7s}  "
              f"{'dA1':>7s}  {'E_sgn':>7s}  {'SF_d12':>7s}  {'|Gap|':>7s}")
    else:
        print(f"  {'Ply':>4s}  {'Move':>8s}  {'Pcs':>3s}  {'A1_E':>7s}  "
              f"{'dA1':>7s}  {'E_sgn':>7s}  {'SF_d12':>7s}")
    print("  " + "-" * 68)

    for i, m in enumerate(metrics):
        sf_str = f"{m['sf_d12']:+7d}" if m['sf_d12'] is not None else "    N/A"
        gap_str = f"{m['depth_gap']:7.0f}" if m.get('depth_gap') is not None else ""
        # ΔA₁: change from previous ply
        if i > 0:
            da1 = m['a1_energy'] - metrics[i - 1]['a1_energy']
            da1_str = f"{da1:+7.2f}"
        else:
            da1_str = "      -"
        e_str = f"{m['e_signed']:+7.2f}"
        if has_gap:
            print(f"  {m['ply']:4d}  {m['move']:>8s}  {m['n_pieces']:3d}  "
                  f"{m['a1_energy']:7.2f}  {da1_str}  {e_str}  {sf_str}  {gap_str}")
        else:
            print(f"  {m['ply']:4d}  {m['move']:>8s}  {m['n_pieces']:3d}  "
                  f"{m['a1_energy']:7.2f}  {da1_str}  {e_str}  {sf_str}")

    # ── Build arrays ───────────────────────────────────────────
    a1_arr = np.array([m['a1_energy'] for m in metrics])
    sf12_arr = np.array([m['sf_d12'] if m['sf_d12'] is not None else np.nan
                         for m in metrics])
    e_signed_arr = np.array([m['e_signed'] for m in metrics])
    mat_arr = np.array([m['mat_balance'] for m in metrics])

    # ── ΔA₁ derivative ─────────────────────────────────────────
    delta_a1 = np.diff(a1_arr, prepend=a1_arr[0])  # delta_a1[0] = 0

    # Ply of maximum A1 energy (peak)
    ply_max_a1 = int(np.argmax(a1_arr))

    # Ply of largest A1 DROP (most negative ΔA₁ = "complexity break")
    ply_max_drop = int(np.argmin(delta_a1[1:])) + 1  # skip index 0
    max_drop_val = delta_a1[ply_max_drop]

    # Ply of largest |ΔA₁| (either direction)
    ply_max_abs_da1 = int(np.argmax(np.abs(delta_a1[1:]))) + 1

    # ── Crisis detection: max |eval change| ─────────────────────
    sf_valid = ~np.isnan(sf12_arr)
    eval_changes = np.zeros(n_plies)
    for i in range(1, n_plies):
        if sf_valid[i] and sf_valid[i - 1]:
            eval_changes[i] = abs(sf12_arr[i] - sf12_arr[i - 1])
    ply_max_eval_change = int(np.argmax(eval_changes))

    # ── Print summary ──────────────────────────────────────────
    print(f"\n  Max A1 energy: ply {ply_max_a1} ({metrics[ply_max_a1]['move']}), "
          f"A1={a1_arr[ply_max_a1]:.2f}")
    print(f"  Max A1 DROP:   ply {ply_max_drop} ({metrics[ply_max_drop]['move']}), "
          f"dA1={max_drop_val:+.2f}")
    print(f"  Max |eval change|: ply {ply_max_eval_change} "
          f"({metrics[ply_max_eval_change]['move']}), "
          f"delta={eval_changes[ply_max_eval_change]:.0f} cp")

    # Alignment comparison: peak vs drop vs crisis
    peak_offset = ply_max_eval_change - ply_max_a1
    drop_offset = ply_max_eval_change - ply_max_drop
    print(f"  Peak alignment: crisis - peak = {peak_offset:+d} plies")
    print(f"  Drop alignment: crisis - drop = {drop_offset:+d} plies "
          f"({'TIGHTER' if abs(drop_offset) < abs(peak_offset) else 'wider'})")

    summary = {
        'game': game_name,
        'n_plies': n_plies,
        'ply_max_a1': ply_max_a1,
        'ply_max_drop': ply_max_drop,
        'max_drop_val': max_drop_val,
        'ply_max_eval_change': ply_max_eval_change,
        'a1_peak_before_crisis': ply_max_a1 <= ply_max_eval_change,
        'a1_drop_before_crisis': ply_max_drop <= ply_max_eval_change,
        'peak_offset': peak_offset,
        'drop_offset': drop_offset,
    }

    # ── Depth-gap correlation (if available) ─────────────────────
    if has_gap:
        gap_arr = np.array([m['depth_gap'] if m['depth_gap'] is not None
                            else np.nan for m in metrics])
        gap_valid = ~np.isnan(gap_arr) & ~np.isnan(a1_arr)
        if gap_valid.sum() >= MIN_PLY_FOR_CORRELATION:
            rho_gap, p_gap = spearmanr(a1_arr[gap_valid], gap_arr[gap_valid])
            print(f"  Spearman(A1, |gap|): rho={rho_gap:+.3f} (p={p_gap:.4f}, "
                  f"N={gap_valid.sum()})")
            summary['rho_a1_gap'] = rho_gap
            summary['p_a1_gap'] = p_gap

            ply_max_gap = int(np.nanargmax(gap_arr))
            print(f"  Max |depth_gap|: ply {ply_max_gap} ({metrics[ply_max_gap]['move']}), "
                  f"|gap|={gap_arr[ply_max_gap]:.0f}")
            summary['ply_max_gap'] = ply_max_gap

    # ── A1 vs |SF eval| correlation ──────────────────────────────
    sf_abs = np.abs(sf12_arr)
    valid = sf_valid & ~np.isnan(a1_arr)
    if valid.sum() >= MIN_PLY_FOR_CORRELATION:
        rho_sf, p_sf = spearmanr(a1_arr[valid], sf_abs[valid])
        print(f"  Spearman(A1, |SF_d12|): rho={rho_sf:+.3f} (p={p_sf:.4f}, "
              f"N={valid.sum()})")
        summary['rho_a1_sf'] = rho_sf
        summary['p_a1_sf'] = p_sf

    # ── |ΔA₁| vs |eval change| correlation ──────────────────────
    abs_da1 = np.abs(delta_a1)
    # Both must be non-zero (skip ply 0 and trivial plies)
    da1_valid = (abs_da1 > 0) & (eval_changes > 0) & sf_valid
    if da1_valid.sum() >= MIN_PLY_FOR_CORRELATION:
        rho_da1, p_da1 = spearmanr(abs_da1[da1_valid], eval_changes[da1_valid])
        print(f"  Spearman(|dA1|, |eval_chg|): rho={rho_da1:+.3f} (p={p_da1:.4f}, "
              f"N={da1_valid.sum()})")
        summary['rho_da1_ec'] = rho_da1
        summary['p_da1_ec'] = p_da1

    # ── E channel partial: E_signed vs SF_d12, controlling material ──
    if valid.sum() >= MIN_PLY_FOR_CORRELATION:
        rho_e_raw, p_e_raw = spearmanr(e_signed_arr[valid], sf12_arr[valid])
        rho_e_part, p_e_part = partial_spearman(
            e_signed_arr[valid], sf12_arr[valid], mat_arr[valid])
        flag_part = significance_flag(p_e_part)
        print(f"  E_signed vs SF_d12: raw rho={rho_e_raw:+.3f}, "
              f"partial(ctrl mat) rho={rho_e_part:+.3f} (p={p_e_part:.4f}) {flag_part}")
        summary['rho_e_partial'] = rho_e_part
        summary['p_e_partial'] = p_e_part

    return summary


def print_trajectory_summary(all_results):
    """Cross-game aggregate statistics."""
    print("\n  " + "=" * 66)
    print("  CROSS-GAME SUMMARY")
    print("  " + "=" * 66)

    # ── Peak vs Drop alignment table ──────────────────────────
    print(f"\n  {'Game':>32s}  {'Plies':>5s}  {'Peak':>5s}  {'Drop':>5s}  "
          f"{'Crisis':>6s}  {'PkOff':>5s}  {'DrOff':>5s}  {'Tighter':>7s}")
    print("  " + "-" * 80)

    for r in all_results:
        pk_off = r['peak_offset']
        dr_off = r['drop_offset']
        tighter = "DROP" if abs(dr_off) < abs(pk_off) else ("PEAK" if abs(pk_off) < abs(dr_off) else "tie")
        print(f"  {r['game']:>32s}  {r['n_plies']:5d}  "
              f"{r['ply_max_a1']:5d}  {r['ply_max_drop']:5d}  "
              f"{r['ply_max_eval_change']:6d}  {pk_off:+5d}  {dr_off:+5d}  "
              f"{tighter:>7s}")

    # ── Aggregate: peak vs drop ───────────────────────────────
    mean_peak_offset = np.mean([r['peak_offset'] for r in all_results])
    mean_drop_offset = np.mean([r['drop_offset'] for r in all_results])
    mean_abs_peak = np.mean([abs(r['peak_offset']) for r in all_results])
    mean_abs_drop = np.mean([abs(r['drop_offset']) for r in all_results])
    n_peak_before = sum(1 for r in all_results if r['a1_peak_before_crisis'])
    n_drop_before = sum(1 for r in all_results if r['a1_drop_before_crisis'])
    n_drop_tighter = sum(1 for r in all_results
                         if abs(r['drop_offset']) < abs(r['peak_offset']))

    print(f"\n  A1 PEAK before crisis: {n_peak_before}/{len(all_results)} games")
    print(f"  A1 DROP before crisis: {n_drop_before}/{len(all_results)} games")
    print(f"  Mean |peak offset|: {mean_abs_peak:.1f} plies")
    print(f"  Mean |drop offset|: {mean_abs_drop:.1f} plies")
    print(f"  Drop tighter than peak: {n_drop_tighter}/{len(all_results)} games")
    if mean_abs_drop < mean_abs_peak:
        print(f"  --> dA1 DROP is the SHARPER crisis indicator "
              f"(mean |offset| {mean_abs_drop:.1f} vs {mean_abs_peak:.1f})")
    else:
        print(f"  --> A1 PEAK is the better indicator "
              f"(mean |offset| {mean_abs_peak:.1f} vs {mean_abs_drop:.1f})")

    # ── Depth-gap correlations ─────────────────────────────────
    gap_results = [r for r in all_results if 'rho_a1_gap' in r]
    if gap_results:
        print(f"\n  Per-game Spearman(A1, |gap|):")
        for r in gap_results:
            flag = significance_flag(r['p_a1_gap'])
            print(f"    {r['game']:>32s}: rho={r['rho_a1_gap']:+.3f} "
                  f"(p={r['p_a1_gap']:.4f}) {flag}")

    # ── E channel partial correlations ─────────────────────────
    e_results = [r for r in all_results if 'rho_e_partial' in r]
    if e_results:
        print(f"\n  Per-game E_signed partial (ctrl material):")
        n_neg = 0
        for r in e_results:
            flag = significance_flag(r['p_e_partial'])
            sign = "-" if r['rho_e_partial'] < 0 else "+"
            if r['rho_e_partial'] < 0:
                n_neg += 1
            print(f"    {r['game']:>32s}: rho={r['rho_e_partial']:+.3f} "
                  f"(p={r['p_e_partial']:.4f}) {flag}")
        mean_e = np.mean([r['rho_e_partial'] for r in e_results])
        print(f"  Mean E partial: {mean_e:+.3f} ({n_neg}/{len(e_results)} negative)")
        if n_neg > len(e_results) / 2:
            print("  --> E channel partial is CONSISTENTLY NEGATIVE across games")

    # ── |ΔA₁| vs |eval change| correlations ───────────────────
    da1_results = [r for r in all_results if 'rho_da1_ec' in r]
    if da1_results:
        rhos = [r['rho_da1_ec'] for r in da1_results]
        mean_da1_rho = np.mean(rhos)
        print(f"\n  Per-game Spearman(|dA1|, |eval_change|):")
        for r in da1_results:
            flag = significance_flag(r['p_da1_ec'])
            print(f"    {r['game']:>32s}: rho={r['rho_da1_ec']:+.3f} "
                  f"(p={r['p_da1_ec']:.4f}) {flag}")
        print(f"  Mean rho: {mean_da1_rho:+.3f}")


def run_experiment_2():
    """Game trajectory analysis for 5 famous games."""
    print("\n" + "=" * 70)
    print("  EXPERIMENT 2: Game Trajectory Analysis")
    print("  Ply-by-ply spectral evolution through 5 master games")
    print("=" * 70)

    # ── Replay all games ────────────────────────────────────────
    all_game_data = []  # (game_name, positions_list)
    for game_name, (description, pgn_str) in TRAJECTORY_PGNS.items():
        positions = replay_game_positions(pgn_str)
        if not positions:
            print(f"  WARNING: Could not parse PGN for {game_name}")
            continue
        print(f"  {game_name}: {len(positions)} positions ({description})")
        all_game_data.append((game_name, positions))

    if not all_game_data:
        print("  ERROR: No games parsed. Skipping Experiment 2.")
        return

    # ── Collect all positions for batched SF evaluation ─────────
    all_fens = []
    game_fen_ranges = []  # (start_idx, end_idx) per game
    for game_name, positions in all_game_data:
        start = len(all_fens)
        for pos, fen, move in positions:
            all_fens.append(fen)
        game_fen_ranges.append((start, len(all_fens)))

    total_positions = len(all_fens)
    print(f"\n  Total positions across all games: {total_positions}")

    # ── Batched SF evaluation ───────────────────────────────────
    print(f"  Evaluating at depth {SF_DEPTH_SHALLOW}...")
    sf_d1_all = stockfish_eval_fens(all_fens, depth=SF_DEPTH_SHALLOW)

    print(f"  Evaluating at depth {SF_DEPTH_TRAJECTORY}...")
    sf_d12_all = stockfish_eval_fens(all_fens, depth=SF_DEPTH_TRAJECTORY)

    sf_d20_all = None
    if COMPUTE_DEEP_GAP:
        print(f"  Evaluating at depth {SF_DEPTH_DEEP} (this may take several minutes)...")
        sf_d20_all = stockfish_eval_fens(all_fens, depth=SF_DEPTH_DEEP)
    else:
        print(f"  Skipping depth {SF_DEPTH_DEEP} (COMPUTE_DEEP_GAP = False)")

    # ── Per-game analysis ───────────────────────────────────────
    all_results = []
    for (game_name, positions), (start, end) in zip(all_game_data, game_fen_ranges):
        metrics = []
        for i, (pos, fen, move) in enumerate(positions):
            idx = start + i

            # Spectral metrics
            sig = board_signal(pos, vals=SPECTRAL_VALS)
            enc_full = encode_512_spectral(pos)
            a1_proj = project_irrep(sig, 'A1')
            e_proj = project_irrep(sig, 'E')
            breaking_parts = [project_irrep(sig, name) for name in BREAKING_IRREPS]

            sf_d1 = sf_d1_all[idx]
            sf_d12 = sf_d12_all[idx]
            sf_d20 = sf_d20_all[idx] if sf_d20_all is not None else None

            depth_gap = None
            if sf_d1 is not None and sf_d20 is not None:
                depth_gap = abs(sf_d20 - sf_d1)

            metrics.append({
                'ply': i,
                'move': move,
                'n_pieces': piece_count(pos),
                'a1_energy': float(np.linalg.norm(a1_proj)),
                'fiber_energy': float(np.linalg.norm(enc_full[FIBER_DIM_START:])),
                'breaking_energy': float(np.linalg.norm(
                    np.concatenate(breaking_parts))),
                'e_signed': float(np.sum(e_proj)),
                'mat_balance': spectral_material_balance(pos),
                'sf_d1': sf_d1,
                'sf_d12': sf_d12,
                'sf_d20': sf_d20,
                'depth_gap': depth_gap,
            })

        result = analyze_game_trajectory(game_name, metrics)
        all_results.append(result)

    # ── Cross-game summary ──────────────────────────────────────
    print_trajectory_summary(all_results)


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 2b: LARGE-SCALE TRAJECTORY ANALYSIS (fishtest PGNs)
#
# Same analysis as Experiment 2 but on N randomly sampled games
# from the HuggingFace fishtest_pgns dataset. Provides statistical
# power that 5 hand-picked games cannot.
#
# Uses pgn_fetcher.py to download Stockfish-vs-Stockfish games.
# ═══════════════════════════════════════════════════════════════

# Number of fishtest games to analyze
FISHTEST_N_GAMES = 20                   # Increase for more statistical power
FISHTEST_SEED = 42                      # Reproducibility
FISHTEST_MIN_MOVES = 30                 # Skip very short games
FISHTEST_MAX_MOVES = 80                 # Skip extremely long games
FISHTEST_TC_MIN = 10.0                  # Skip bullet games (noisy play)
SF_DEPTH_2B = 12                        # SF depth for trajectory eval


def run_experiment_2b():
    """Large-scale trajectory analysis on fishtest PGNs.

    Downloads random games from HuggingFace and runs the same
    ply-by-ply spectral analysis as Experiment 2, but at scale.
    """
    try:
        from pgn_fetcher import PGNFetcher
    except ImportError:
        print("\n  Experiment 2b SKIPPED: pgn_fetcher.py not found")
        return

    print("\n" + "=" * 70)
    print("  EXPERIMENT 2b: Large-Scale Trajectory Analysis (fishtest PGNs)")
    print(f"  {FISHTEST_N_GAMES} random games from HuggingFace, seed={FISHTEST_SEED}")
    print("=" * 70)

    fetcher = PGNFetcher()

    # ── Fetch games ────────────────────────────────────────────
    print(f"\n  Fetching {FISHTEST_N_GAMES} games "
          f"(TC>={FISHTEST_TC_MIN}s, {FISHTEST_MIN_MOVES}-{FISHTEST_MAX_MOVES} moves)...")
    raw_games = fetcher.fetch_random_games(
        n=FISHTEST_N_GAMES,
        seed=FISHTEST_SEED,
        min_moves=FISHTEST_MIN_MOVES,
        max_moves=FISHTEST_MAX_MOVES,
        tc_base_min=FISHTEST_TC_MIN,
    )
    print(f"  Fetched {len(raw_games)} games")

    if len(raw_games) < 3:
        print("  ERROR: Too few games fetched. Skipping Experiment 2b.")
        return

    # ── Replay all games ────────────────────────────────────────
    print("\n  Replaying games and extracting positions...")
    all_game_data = []
    for i, game_dict in enumerate(raw_games):
        pgn_str = game_dict['pgn']
        game_name = (f"Game {i + 1} ({game_dict['headers'].get('Result', '?')}, "
                     f"{game_dict['n_moves']}m)")

        positions = replay_game_positions(pgn_str)
        if not positions:
            print(f"  WARNING: Could not parse game {i + 1}")
            continue
        all_game_data.append((game_name, positions))

    if not all_game_data:
        print("  ERROR: No games parsed. Skipping.")
        return

    # ── Collect all positions for batched SF evaluation ─────────
    all_fens = []
    game_fen_ranges = []
    for game_name, positions in all_game_data:
        start = len(all_fens)
        for pos, fen, move in positions:
            all_fens.append(fen)
        game_fen_ranges.append((start, len(all_fens)))

    total_positions = len(all_fens)
    print(f"  Total positions across {len(all_game_data)} games: {total_positions}")

    # ── Batched SF evaluation (depth 1 + 12 only) ──────────────
    print(f"  Evaluating at depth {SF_DEPTH_SHALLOW}...")
    sf_d1_all = stockfish_eval_fens(all_fens, depth=SF_DEPTH_SHALLOW)

    print(f"  Evaluating at depth {SF_DEPTH_2B}...")
    sf_d12_all = stockfish_eval_fens(all_fens, depth=SF_DEPTH_2B)

    # ── Compute per-ply spectral metrics for each game ──────────
    print("\n  Computing spectral metrics and per-game correlations...")
    pooled_a1 = []
    pooled_sf_abs = []
    pooled_sf_signed = []
    pooled_eval_change = []
    pooled_abs_da1 = []
    pooled_e_signed = []
    pooled_mat = []
    all_summaries = []

    for (game_name, positions), (start, end) in zip(all_game_data, game_fen_ranges):
        a1_vals = []
        sf12_vals = []
        e_signed_vals = []
        mat_vals = []

        for i, (pos, fen, move) in enumerate(positions):
            idx = start + i
            sig = board_signal(pos, vals=SPECTRAL_VALS)
            a1_proj = project_irrep(sig, 'A1')
            e_proj = project_irrep(sig, 'E')
            a1_e = float(np.linalg.norm(a1_proj))
            a1_vals.append(a1_e)
            e_signed_vals.append(float(np.sum(e_proj)))
            mat_vals.append(spectral_material_balance(pos))
            sf12 = sf_d12_all[idx]
            sf12_vals.append(sf12 if sf12 is not None else np.nan)

        a1_arr = np.array(a1_vals)
        sf12_arr = np.array(sf12_vals)
        sf_abs = np.abs(sf12_arr)
        e_arr = np.array(e_signed_vals)
        mat_arr = np.array(mat_vals)

        # ΔA₁ derivative
        delta_a1 = np.diff(a1_arr, prepend=a1_arr[0])
        abs_da1 = np.abs(delta_a1)

        # Eval changes (ply-by-ply)
        eval_changes = np.zeros(len(a1_vals))
        for j in range(1, len(a1_vals)):
            if not np.isnan(sf12_arr[j]) and not np.isnan(sf12_arr[j - 1]):
                eval_changes[j] = abs(sf12_arr[j] - sf12_arr[j - 1])

        # Peak + drop detection
        ply_max_a1 = int(np.argmax(a1_arr))
        ply_max_drop = int(np.argmin(delta_a1[1:])) + 1 if len(delta_a1) > 1 else 0
        ply_max_eval_change = int(np.argmax(eval_changes))
        peak_offset = ply_max_eval_change - ply_max_a1
        drop_offset = ply_max_eval_change - ply_max_drop

        # Per-game correlations
        sf_valid = ~np.isnan(sf12_arr)
        valid = sf_valid & ~np.isnan(a1_arr)
        rho_sf = p_sf = np.nan
        if valid.sum() >= MIN_PLY_FOR_CORRELATION:
            rho_sf, p_sf = spearmanr(a1_arr[valid], sf_abs[valid])

        # E partial
        rho_e_part = p_e_part = np.nan
        if valid.sum() >= MIN_PLY_FOR_CORRELATION:
            rho_e_part, p_e_part = partial_spearman(
                e_arr[valid], sf12_arr[valid], mat_arr[valid])

        # |ΔA₁| vs |eval change|
        rho_da1 = p_da1 = np.nan
        da1_valid = (abs_da1 > 0) & (eval_changes > 0) & sf_valid
        if da1_valid.sum() >= MIN_PLY_FOR_CORRELATION:
            rho_da1, p_da1 = spearmanr(abs_da1[da1_valid], eval_changes[da1_valid])

        summary = {
            'game': game_name,
            'n_plies': len(a1_vals),
            'ply_max_a1': ply_max_a1,
            'ply_max_drop': ply_max_drop,
            'max_drop_val': delta_a1[ply_max_drop],
            'ply_max_eval_change': ply_max_eval_change,
            'a1_peak_before_crisis': ply_max_a1 <= ply_max_eval_change,
            'a1_drop_before_crisis': ply_max_drop <= ply_max_eval_change,
            'peak_offset': peak_offset,
            'drop_offset': drop_offset,
            'rho_a1_sf': rho_sf,
            'p_a1_sf': p_sf,
            'rho_e_partial': rho_e_part,
            'p_e_partial': p_e_part,
            'rho_da1_ec': rho_da1,
            'p_da1_ec': p_da1,
        }
        all_summaries.append(summary)

        # Pool for cross-game statistics
        for j in range(len(a1_vals)):
            if not np.isnan(sf_abs[j]):
                pooled_a1.append(a1_vals[j])
                pooled_sf_abs.append(sf_abs[j])
                pooled_sf_signed.append(sf12_vals[j])
                pooled_eval_change.append(eval_changes[j])
                pooled_abs_da1.append(abs_da1[j])
                pooled_e_signed.append(e_signed_vals[j])
                pooled_mat.append(mat_vals[j])

    # ── Cross-game pooled statistics ────────────────────────────
    print("\n  " + "=" * 66)
    print("  EXPERIMENT 2b: CROSS-GAME AGGREGATE")
    print(f"  {len(all_summaries)} games, {len(pooled_a1)} total plies")
    print("  " + "=" * 66)

    # Per-game summary table (peak vs drop alignment)
    print(f"\n  {'Game':>40s}  {'Plies':>5s}  {'Peak':>5s}  {'Drop':>5s}  "
          f"{'Crisis':>6s}  {'PkOff':>5s}  {'DrOff':>5s}  {'Tighter':>7s}")
    print("  " + "-" * 90)

    for s in all_summaries:
        pk = s['peak_offset']
        dr = s['drop_offset']
        tighter = "DROP" if abs(dr) < abs(pk) else ("PEAK" if abs(pk) < abs(dr) else "tie")
        print(f"  {s['game']:>40s}  {s['n_plies']:5d}  {s['ply_max_a1']:5d}  "
              f"{s['ply_max_drop']:5d}  {s['ply_max_eval_change']:6d}  "
              f"{pk:+5d}  {dr:+5d}  {tighter:>7s}")

    # ── Aggregate: peak vs drop ───────────────────────────────
    n_peak_before = sum(1 for s in all_summaries if s['a1_peak_before_crisis'])
    n_drop_before = sum(1 for s in all_summaries if s['a1_drop_before_crisis'])
    mean_abs_peak = np.mean([abs(s['peak_offset']) for s in all_summaries])
    mean_abs_drop = np.mean([abs(s['drop_offset']) for s in all_summaries])
    n_drop_tighter = sum(1 for s in all_summaries
                         if abs(s['drop_offset']) < abs(s['peak_offset']))

    print(f"\n  A1 PEAK before crisis: {n_peak_before}/{len(all_summaries)} games")
    print(f"  A1 DROP before crisis: {n_drop_before}/{len(all_summaries)} games")
    print(f"  Mean |peak offset|: {mean_abs_peak:.1f} plies")
    print(f"  Mean |drop offset|: {mean_abs_drop:.1f} plies")
    print(f"  Drop tighter than peak: {n_drop_tighter}/{len(all_summaries)} games")
    if mean_abs_drop < mean_abs_peak:
        print(f"  --> dA1 DROP is the SHARPER crisis indicator "
              f"(mean |offset| {mean_abs_drop:.1f} vs {mean_abs_peak:.1f})")
    else:
        print(f"  --> A1 PEAK remains the better indicator "
              f"(mean |offset| {mean_abs_peak:.1f} vs {mean_abs_drop:.1f})")

    # ── Pooled correlations ───────────────────────────────────
    pooled_a1_arr = np.array(pooled_a1)
    pooled_sf_arr = np.array(pooled_sf_abs)
    pooled_ec_arr = np.array(pooled_eval_change)
    pooled_da1_arr = np.array(pooled_abs_da1)
    pooled_e_arr = np.array(pooled_e_signed)
    pooled_mat_arr = np.array(pooled_mat)
    pooled_sfs_arr = np.array(pooled_sf_signed)

    print(f"\n  ── Pooled correlations (N = {len(pooled_a1_arr)} plies) ──")

    if len(pooled_a1_arr) >= 20:
        rho_pooled, p_pooled = spearmanr(pooled_a1_arr, pooled_sf_arr)
        flag = significance_flag(p_pooled)
        print(f"  Spearman(A1, |SF_d12|):        rho={rho_pooled:+.3f} "
              f"(p={p_pooled:.6f}) {flag}")

    # |ΔA₁| vs |eval change|
    nonzero = pooled_ec_arr > 0
    da1_nz = pooled_da1_arr > 0
    both_nz = nonzero & da1_nz
    if both_nz.sum() >= 20:
        rho_da1, p_da1 = spearmanr(pooled_da1_arr[both_nz], pooled_ec_arr[both_nz])
        flag_da1 = significance_flag(p_da1)
        print(f"  Spearman(|dA1|, |eval_chg|):   rho={rho_da1:+.3f} "
              f"(p={p_da1:.6f}, N={both_nz.sum()}) {flag_da1}")

    # A1 vs |eval change|
    if nonzero.sum() >= 20:
        rho_ec, p_ec = spearmanr(pooled_a1_arr[nonzero], pooled_ec_arr[nonzero])
        flag_ec = significance_flag(p_ec)
        print(f"  Spearman(A1, |eval_chg|):      rho={rho_ec:+.3f} "
              f"(p={p_ec:.6f}, N={nonzero.sum()}) {flag_ec}")

    # E partial: E_signed vs SF_d12, controlling material
    if len(pooled_e_arr) >= 20:
        rho_e_raw, p_e_raw = spearmanr(pooled_e_arr, pooled_sfs_arr)
        rho_e_part, p_e_part = partial_spearman(
            pooled_e_arr, pooled_sfs_arr, pooled_mat_arr)
        flag_e = significance_flag(p_e_part)
        print(f"  E_signed vs SF (raw):          rho={rho_e_raw:+.3f}")
        print(f"  E_signed vs SF (partial, mat): rho={rho_e_part:+.3f} "
              f"(p={p_e_part:.6f}) {flag_e}")

    # ── Per-game E partial summary ────────────────────────────
    e_partials = [s['rho_e_partial'] for s in all_summaries
                  if not np.isnan(s.get('rho_e_partial', np.nan))]
    if e_partials:
        n_neg = sum(1 for r in e_partials if r < 0)
        mean_e = np.mean(e_partials)
        print(f"\n  Per-game E partial: mean={mean_e:+.3f}, "
              f"{n_neg}/{len(e_partials)} negative")
        if n_neg > len(e_partials) * 0.6:
            print("  --> E channel partial is CONSISTENTLY NEGATIVE")

    # ── Per-game |ΔA₁| summary ────────────────────────────────
    da1_rhos = [s['rho_da1_ec'] for s in all_summaries
                if not np.isnan(s.get('rho_da1_ec', np.nan))]
    if da1_rhos:
        mean_da1 = np.mean(da1_rhos)
        n_pos = sum(1 for r in da1_rhos if r > 0)
        print(f"  Per-game |dA1| vs |eval_chg|: mean={mean_da1:+.3f}, "
              f"{n_pos}/{len(da1_rhos)} positive")


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT 3: OTHELLO PREPARATION (DESIGN DOCUMENT)
#
# No computation -- print-only design for the Othello control.
# ═══════════════════════════════════════════════════════════════

def print_othello_design():
    """Print Othello experiment design document."""
    print("\n" + "=" * 70)
    print("  EXPERIMENT 3: Othello Preparation (Design Document)")
    print("  Control experiment: same grid, same D4, zero piece-type diversity")
    print("=" * 70)

    print("""
  1. BOARD SIGNAL FORMAT
     - Same 8x8 grid, same sq(r,c) convention, same Laplacian eigenbasis
     - board_signal_othello(pos): s_i in {+1, -1, 0}
       +1 = black disc, -1 = white disc, 0 = empty
     - No piece values needed -- all discs identical (Ising spin field)
     - project_irrep() works unchanged (operates on any 64-dim signal)

  2. ENCODER CHANNELS
     - Channels 1-5 (D4 irreps): Identical to chess. project_irrep works as-is.
     - Channels 6-8 (fiber bundle): SHOULD BE ZERO.
       Single piece type means no cross-species coupling. No fiber structure.
       This is the SPECIFICITY TEST: if chess fiber energy is genuine,
       the same architecture should detect its ABSENCE in Othello.
     - Prediction: fiber_energy ~= 0 for ALL Othello positions.
       If nonzero, the fiber computation has a bug.
     - Architecture reduces from 512-dim to 320-dim (5 irreps x 64).

  3. EVALUATION GROUND TRUTH
     - Primary: Edax engine (strongest open-source Othello AI)
       Supports depth-limited eval and endgame solving.
     - Secondary: 2023 weak solution (Takizawa et al.)
       Perfect-play values for positions reachable from standard opening.
     - Advantage over chess: even moderate-depth Edax plays essentially
       perfectly (game tree much smaller than chess).
     - Depth-gap analog: |Edax_deepsolve - Edax_d1|

  4. KEY EXPERIMENTAL TESTS
     Test 1: Does A1 energy predict depth-gap in Othello?
       (Main hypothesis transfer -- universal grid complexity measure?)
     Test 2: Are fiber channels zero?
       (Specificity confirmation -- fiber detects multi-species, not artifact)
     Test 3: Does spectral similarity correlate with game-theoretic value?
       (Clean benchmark that chess lacked due to game tree size)
     Test 4: Flip propagation analysis
       (Spectral content of disc-flip patterns along rays)

  5. Z2 SYMMETRY IN OTHELLO
     Z2 is EXACT in Othello (unlike chess with directional pawns).
     Swapping all disc colors + swapping side to move = strategically
     equivalent position. The full D4 x Z2 (16 elements) is the
     natural symmetry group for Othello board analysis.

     A1 energy (D4 x Z2 invariant) captures pure positional complexity
     with ZERO color/advantage information. If A1 energy predicts
     depth-gap in BOTH chess and Othello, it measures something
     UNIVERSAL about complexity on grid graphs -- independent of
     game mechanics.

  6. IMPLEMENTATION NOTES
     - encoder_othello.py: Minimal -- import grid infrastructure from
       encoder_512.py, replace board_signal with Ising version
     - No SPECTRAL_VALS needed (all values +/-1)
     - Position legality: Must check Othello rules (valid disc placement)
     - Coordinate mapping: Same as chess (row 0 = top of board)
     - Expected LOC: ~200-300 (much simpler than chess encoder)

  STATUS: Design complete. Implementation after Experiments 1 & 2.
""")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("  A1 DEPTH-GAP FOLLOW-UP EXPERIMENTS")
    print("  Three experiments building on the A1 discovery (rho=+0.452)")
    print("  Full symmetry: D4 x Z2 (16 elements)")
    print("=" * 70)

    # ── Shared setup: build corpus + SF evaluation (once) ───────
    print("\n  Building position corpus...")
    corpus = build_position_corpus()
    print(f"  Corpus: {len(corpus)} positions")

    print("\n  Running Stockfish evaluation (shared by Experiment 1)...")
    evaluated = evaluate_corpus(corpus)
    print(f"  Valid positions after filtering: {len(evaluated)}")

    # ── Experiment 1 ────────────────────────────────────────────
    run_experiment_1(evaluated)

    # ── Experiment 2 ────────────────────────────────────────────
    run_experiment_2()

    # ── Experiment 2b ──────────────────────────────────────────
    run_experiment_2b()

    # ── Experiment 3 ────────────────────────────────────────────
    print_othello_design()

    print("\n" + "=" * 70)
    print("  All experiments complete.")
    print("=" * 70)


if __name__ == '__main__':
    main()
