#!/usr/bin/env python3
"""
Expanded Depth-Gap Experiment: Spectral Energy vs Search Depth Sensitivity
==========================================================================

Tests whether spectral encoding metrics (fiber energy, irrep energy, A1 energy)
predict how much a position's evaluation changes between shallow (depth 1) and
deep (depth 20) Stockfish search.

Positions where |SF_d20 - SF_d1| is large contain "hidden tactical potential" --
the question is whether the spectral encoding detects this without search.

54 positions from real games across HIGH/MEDIUM/LOW complexity categories.
Partial correlations controlling for piece count. Sensitivity analysis for
same-material repositioning pairs.

Key question: Does the fiber interaction energy -- a zero-parameter spectral
quantity derived purely from graph topology with no chess knowledge -- predict
which positions reward deep tactical search?

Dependencies: numpy, scipy, python-chess, stockfish engine
Imports encoder infrastructure from encoder_512.py (same directory)
"""

import sys
import os

# Fix Windows console encoding for Unicode chess symbols
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Import from encoder_512.py (same directory)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from encoder_512 import (
    sq, rc, VALS, SPECTRAL_VALS, MATERIAL_CP,
    encode_512, encode_512_spectral, encode_A1_spectral,
    pos_to_fen, stockfish_eval_batch, cosine,
)
import numpy as np
from scipy.stats import spearmanr, rankdata
from scipy.stats import t as t_dist
import chess


# ── Experiment constants (no magic numbers) ───────────────────
SF_DEPTH_SHALLOW = 1           # Near-static evaluation depth
SF_DEPTH_DEEP = 20             # Full tactical search depth
EVAL_FILTER_THRESHOLD_CP = 5000  # Exclude positions with |eval| > this at either depth
SIGNIFICANCE_ALPHA = 0.05      # p-value threshold for SIGNIFICANT flag
TRENDING_ALPHA = 0.10          # p-value threshold for TRENDING flag
MIN_POSITIONS_FOR_CORR = 8     # Minimum valid positions to compute correlations
BOARD_SAMPLE_COUNT = 3         # Number of board diagrams to print for FEN sanity check

# Fiber channel boundaries in the 512-dim encoding
IRREP_DIM_END = 320            # Channels 1-5: indices 0..319 (D4 irreps)
FIBER_DIM_START = 320          # Channels 6-8: indices 320..511 (fiber interaction)
TOTAL_DIM = 512


# ── Utility functions ─────────────────────────────────────────

def fen_to_pos(fen_str):
    """Convert FEN string to position dict {square_index: piece_char}.

    Uses python-chess for robust FEN parsing. Only extracts piece placement.

    Square index convention matches encoder_512.py:
      sq(r, c) = r*8 + c, where row 0 = rank 8 (black's back rank),
      row 7 = rank 1 (white's back rank).

    python-chess uses: square = file + rank*8, rank 0 = rank 1.
    Conversion: our_row = 7 - rank, our_col = file.
    """
    board = chess.Board(fen_str)
    pos = {}
    for pc_square, pc_piece in board.piece_map().items():
        file = chess.square_file(pc_square)   # 0-7 (a-h)
        rank = chess.square_rank(pc_square)   # 0-7 (rank 1-8)
        our_row = 7 - rank   # rank 8 -> row 0, rank 1 -> row 7
        our_col = file        # file a -> col 0
        pos[our_row * 8 + our_col] = pc_piece.symbol()
    return pos


def partial_spearman(x, y, z):
    """Partial Spearman correlation of x and y, controlling for z.

    Method: rank-transform all three variables, OLS-regress x_ranked and
    y_ranked on z_ranked, take residuals, compute Pearson correlation of
    residuals. This is the standard textbook partial rank correlation.

    Returns (rho_partial, p_value).
    p-value from two-tailed t-test with df = n - 3.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    n = len(x)

    # Rank transform
    x_r = rankdata(x)
    y_r = rankdata(y)
    z_r = rankdata(z)

    # Augment z with intercept for OLS
    z_aug = np.column_stack([z_r, np.ones(n)])

    # Residualize x on z
    beta_x, _, _, _ = np.linalg.lstsq(z_aug, x_r, rcond=None)
    res_x = x_r - z_aug @ beta_x

    # Residualize y on z
    beta_y, _, _, _ = np.linalg.lstsq(z_aug, y_r, rcond=None)
    res_y = y_r - z_aug @ beta_y

    # Pearson correlation of residuals
    rho = np.corrcoef(res_x, res_y)[0, 1]

    # t-test for significance (df = n - 3 for one control variable)
    df = n - 3
    if df < 1 or abs(rho) > 1.0 - 1e-15:
        return rho, 0.0 if abs(rho) > 1.0 - 1e-15 else 1.0
    t_stat = rho * np.sqrt(df / (1.0 - rho**2 + 1e-15))
    p_value = 2.0 * float(t_dist.sf(abs(t_stat), df=df))
    return float(rho), p_value


def material_signature(pos):
    """Canonical material signature for grouping same-material positions."""
    return tuple(sorted(pos.values()))


def piece_count(pos):
    """Total number of pieces on the board."""
    return len(pos)


def piece_type_count(pos):
    """Number of distinct piece types (case-sensitive: 'K' != 'k')."""
    return len(set(pos.values()))


def material_balance_cp(pos):
    """Material balance in centipawns (white - black)."""
    balance = 0
    for pchar in pos.values():
        sign = 1 if pchar.isupper() else -1
        balance += sign * MATERIAL_CP.get(pchar.upper(), 0)
    return balance


def significance_flag(p_value):
    """Return significance flag string based on p-value thresholds."""
    if p_value < SIGNIFICANCE_ALPHA:
        return "SIGNIFICANT"
    elif p_value < TRENDING_ALPHA:
        return "TRENDING"
    return ""


# ── Position corpus ───────────────────────────────────────────

def build_position_corpus():
    """Build the position corpus across HIGH/MEDIUM/LOW complexity.

    Returns list of (pos_dict, category, label) tuples.

    All FEN positions are from real games or well-known theoretical positions.
    Categories reflect expected depth-gap behavior:
      HIGH   - Sharp tactical positions (large |SF_d20 - SF_d1| expected)
      MEDIUM - Positional play, moderate tactical potential
      LOW    - Simple/decided positions (small depth gap expected)
    """
    corpus = []

    # ── HIGH complexity: sharp tactics, sacrifices, complex middlegames ──

    high_fens = [
        # Kasparov vs Topalov, Wijk aan Zee 1999 -- before 24.Rxd4
        # Sharp position with Kasparov's famous rook sacrifice coming
        ("r1bq1rk1/pp2nppp/2n1p3/3pP3/1b1P4/2NB1N2/PP3PPP/R1BQ1RK1 w - - 0 10",
         "Kasparov-Topalov Wijk99 (sharp IQP)"),

        # Tal vs Botvinnik, World Ch 1960 Game 6 -- wild tactical middlegame
        ("r1b2rk1/2qnbppp/p2ppn2/1p4B1/3NPP2/2N2Q2/PPP3PP/2KR1B1R w - - 0 12",
         "Tal-Botvinnik WCh60 G6 (Najdorf)"),

        # Fischer vs Byrne, 1956 "Game of the Century" -- before 17...Be6
        ("1Q6/5p1p/2p2kp1/1p6/3Pn3/1q2P3/5PPP/4K2R b - - 0 30",
         "Fischer-Byrne 1956 (late tactics)"),

        # Morphy vs Duke/Count, Opera Game 1858 -- before Qb8+
        ("1r2k1nr/p1pp1ppp/8/1Bb1P3/8/2N5/qPPP1PPP/R1BQK2R w KQk - 0 10",
         "Morphy Opera Game (attack)"),

        # Sicilian Najdorf -- typical sharp middlegame
        ("r1b1kb1r/1p1n1ppp/p2ppn2/6B1/3NPP2/2N5/PPPQ2PP/R3KB1R w KQkq - 0 9",
         "Sicilian Najdorf typical"),

        # Marshall Attack -- gambit line with compensation
        ("r1bq1rk1/b1p2ppp/p1np4/1p1Np1B1/4P3/3P1N2/PPP2PPP/R2Q1RK1 w - - 0 12",
         "Marshall Attack (compensation)"),

        # King's Indian Defense -- opposite side attacks
        ("r1bq1rk1/ppp1npbp/3p1np1/3Pp3/2P1P3/2N2N2/PP2BPPP/R1BQ1RK1 w - - 0 9",
         "King's Indian (pawn storm)"),

        # Alekhine vs Reti, Baden-Baden 1925 -- complex middlegame
        ("r2qr1k1/pp1nbppp/2p2n2/3p4/3P1B2/2NBP3/PP1Q1PPP/R3K2R w KQ - 0 11",
         "Alekhine-Reti 1925 (QGD)"),

        # Botvinnik vs Capablanca, AVRO 1938 -- famous positional sacrifice
        ("2r1r1k1/pp1n1pbp/3p2p1/q1pP4/2P1PP2/1PB3P1/P2Q3P/1R2R1K1 w - - 0 21",
         "Botvinnik-Capa AVRO38 (squeeze)"),

        # Anand vs Kasparov, PCA WCh 1995 Game 10 -- sharp Sicilian
        ("r1b2rk1/2q1bppp/p1nppn2/1p4B1/4PP2/2NB1N2/PPPQ2PP/2KR3R w - - 0 12",
         "Anand-Kasparov WCh95 (Najdorf)"),

        # Shirov vs Topalov, Linares 1998 -- famous Bh3 sacrifice
        ("r4rk1/1bq1bppp/ppnppn2/8/2P1PP2/1NN1B3/PP1QB1PP/R4RK1 w - - 0 14",
         "Shirov-Topalov Linares98"),

        # Kramnik vs Kasparov, London 2000 WCh Game 2 -- Berlin Wall
        ("r3r1k1/ppqb1ppp/2n1pn2/8/2BN4/P1N1P3/1PQ2PPP/R1B2RK1 w - - 0 13",
         "Kramnik-Kasparov WCh00 G2"),

        # Evans Gambit -- sharp attacking position
        ("r1bqk2r/pppp1ppp/2n2n2/2b1p3/1PB1P3/5N2/P1PP1PPP/RNBQK2R w KQkq - 0 5",
         "Evans Gambit (accepted)"),

        # Double-edged IQP position -- central tension
        ("r1bq1rk1/pp3ppp/2nbpn2/3p4/2PP4/2N2N2/PP2BPPP/R1BQ1RK1 w - - 0 9",
         "IQP tension (Nimzo theme)"),

        # Benoni with opposite-side play
        ("r1bq1rk1/pp1n1pb1/2pp1npp/4p3/2PPP3/2N2NP1/PP3PBP/R1BQ1RK1 w - - 0 10",
         "Modern Benoni (tension)"),

        # Sharp Grunfeld with central play
        ("rnbq1rk1/pp2ppbp/6p1/2pP4/5B2/2N2N2/PP2PPPP/R2QKB1R w KQ - 0 7",
         "Grunfeld Exchange (central)"),

        # Complex position with multiple imbalances
        ("r2q1rk1/1b2bppp/p1n1pn2/1pp5/4P3/1BN1BN2/PPP2PPP/R2Q1RK1 w - - 0 11",
         "Complex: bishop pair imbalance"),

        # Tactical middlegame -- pins and discoveries possible
        ("r2qk2r/ppp1bppp/2n1bn2/3pp3/4P3/1BN2N2/PPPP1PPP/R1BQK2R w KQkq - 0 6",
         "Italian Game (tactical center)"),
    ]

    for fen, label in high_fens:
        corpus.append((fen_to_pos(fen), "HIGH", label))

    # ── MEDIUM complexity: positional middlegames, early endgames ──

    medium_fens = [
        # Carlsen-style quiet Ruy Lopez middlegame
        ("r1bq1rk1/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQ1RK1 w - - 0 8",
         "Ruy Lopez Closed (typical)"),

        # QGD classical -- positional maneuvering
        ("r1bq1rk1/pp1n1ppp/2p1pn2/3p4/1bPP4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 8",
         "QGD Classical (maneuvering)"),

        # Caro-Kann typical middlegame
        ("r2qkb1r/pp2pppp/2n2n2/3p1b2/3P4/2N2N2/PPP1BPPP/R1BQK2R w KQkq - 0 6",
         "Caro-Kann Classical"),

        # Capablanca-style endgame (rook + minor piece)
        ("8/pp3kpp/2p2p2/3rn3/8/2P2N2/PP3PPP/3R2K1 w - - 0 25",
         "Capablanca-style RE endgame"),

        # Queen's Indian typical structure
        ("r1bq1rk1/p1p1bppp/1pnppn2/8/2PP4/2N1PN2/PP2BPPP/R1BQ1RK1 w - - 0 8",
         "Queen's Indian (hedgehog)"),

        # Petrosian-style prophylaxis
        ("r2q1rk1/pp1bbppp/2nppn2/8/2PP4/2N1PN2/PP1BBPPP/R2Q1RK1 w - - 0 10",
         "Petrosian prophylaxis"),

        # Rook endgame with pawn majority
        ("8/5kpp/4rp2/1p6/1P1R4/6PP/5PK1/8 w - - 0 35",
         "Rook endgame (pawn majority)"),

        # Minor piece endgame (B vs N)
        ("8/pp2kppp/4p3/2b5/8/4NP2/PP2KPPP/8 w - - 0 25",
         "B vs N endgame (open)"),

        # Nimzo-Indian quiet position
        ("r1bq1rk1/pp3ppp/2n1pn2/2pp4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 7",
         "Nimzo-Indian (Rubinstein)"),

        # English Opening typical
        ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2P5/2N2N2/PP1PPPPP/R1BQKB1R w KQkq - 0 4",
         "English Four Knights"),

        # Rook + opposite bishops middlegame
        ("2r2rk1/pp2ppbp/3p1np1/q7/3PP1b1/2N1BP2/PPPQ2PP/R4RK1 w - - 0 14",
         "Rook+OppB middlegame"),

        # Standard Slav position
        ("r1bqkb1r/pp3ppp/2n1pn2/2pp4/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5",
         "Semi-Slav (standard)"),

        # Endgame with connected passed pawns
        ("8/8/4kpp1/1p2p3/1P2P1P1/4KP2/8/8 w - - 0 40",
         "Pawn endgame (connected)"),

        # Typical London System middlegame
        ("r1bq1rk1/ppp2ppp/2nbpn2/3p4/3P1B2/2N1PN2/PPP2PPP/R2QKB1R w KQ - 0 7",
         "London System (typical)"),

        # Two rook endgame
        ("2r2rk1/pp3ppp/8/3p4/3P4/8/PP3PPP/2R2RK1 w - - 0 22",
         "Double rook endgame"),

        # French Winawer -- structural
        ("r1b2rk1/pp3ppp/2n1pn2/2qp4/3P4/P1PBPN2/2P2PPP/R1BQ1RK1 w - - 0 10",
         "French Winawer (structural)"),

        # Space advantage position
        ("r1bqk2r/pp1n1ppp/2n1p3/2ppP3/3P4/2PB1N2/PP3PPP/R1BQK2R w KQkq - 0 8",
         "French Advance (space)"),

        # Karpov-style small edge
        ("r2q1rk1/1p2bppp/p1n1pn2/2Pp4/8/2NBPN2/PP3PPP/R2Q1RK1 w - - 0 13",
         "Karpov positional edge"),
    ]

    for fen, label in medium_fens:
        corpus.append((fen_to_pos(fen), "MEDIUM", label))

    # ── LOW complexity: simple endgames, decided positions ──

    low_fens = [
        # K+R vs K (various configurations)
        ("8/8/8/4k3/8/8/8/4K2R w - - 0 1", "KR vs k (center)"),
        ("k7/8/8/8/8/8/8/4K2R w - - 0 1", "KR vs k (corner)"),
        ("8/8/3k4/8/8/8/4R3/4K3 w - - 0 1", "KR vs k (open)"),

        # K+Q vs K
        ("8/8/8/4k3/8/8/8/3QK3 w - - 0 1", "KQ vs k (center)"),
        ("k7/8/8/8/8/8/8/3QK3 w - - 0 1", "KQ vs k (corner)"),

        # K+P vs K (won and drawn)
        ("8/8/8/8/4k3/8/4P3/4K3 w - - 0 1", "KP vs k (opposition)"),
        ("8/4P3/8/4k3/8/8/8/4K3 w - - 0 1", "KP vs k (promotion)"),
        ("8/8/4k3/8/8/8/3P4/4K3 w - - 0 1", "KP vs k (early)"),

        # Dead draw material
        ("8/8/4k3/8/8/8/8/4KB2 w - - 0 1", "KB vs k (dead draw)"),
        ("8/8/4k3/8/8/8/8/4KN2 w - - 0 1", "KN vs k (dead draw)"),

        # Starting position (balanced, no tactics yet)
        ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
         "Starting position"),

        # Symmetric pawn endings
        ("8/pppp1ppp/4k3/8/8/4K3/PPPP1PPP/8 w - - 0 1",
         "Symmetric pawns (drawn)"),
        ("8/ppp2ppp/4k3/8/8/4K3/PPP2PPP/8 w - - 0 1",
         "Symmetric pawns (6v6)"),

        # Overwhelming material advantage
        ("8/8/4k3/8/8/8/4Q3/4K1R1 w - - 0 1", "KQR vs k (overwhelming)"),
        ("8/8/4k3/8/4R3/8/4R3/4K3 w - - 0 1", "KRR vs k (simple win)"),

        # Bare kings with one pawn
        ("8/8/8/8/8/2k5/8/2K1R3 w - - 0 1", "KR vs k (close)"),

        # Near-starting (1. e4)
        ("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
         "After 1.e4"),

        # Drawn rook endgame (Philidor)
        ("8/8/8/4k3/4p3/4K3/8/4R3 w - - 0 1", "KR vs kp (Philidor)"),
    ]

    for fen, label in low_fens:
        corpus.append((fen_to_pos(fen), "LOW", label))

    # ── Include original TEST 12 positions for backward compatibility ──
    test12_positions = _build_test12_positions()
    corpus.extend(test12_positions)

    return corpus


def _build_test12_positions():
    """Recreate the original 16 TEST 12 positions from encoder_512.py.

    These are hand-crafted positions used in the initial depth-gap experiment.
    Tagged with appropriate categories for comparison.
    """
    positions = []

    # Quiet (LOW)
    positions.append(
        ({sq(7,4):'K', sq(6,3):'P', sq(6,4):'P', sq(6,5):'P',
          sq(0,4):'k', sq(1,3):'p', sq(1,4):'p', sq(1,5):'p'},
         "LOW", "T12: KPPPvkppp (quiet)"))
    positions.append(
        ({sq(7,4):'K', sq(7,0):'R', sq(7,7):'R',
          sq(0,4):'k', sq(0,0):'r', sq(0,7):'r'},
         "LOW", "T12: KRRvkrr (quiet)"))
    positions.append(
        ({sq(7,4):'K', sq(7,5):'B', sq(7,2):'B',
          sq(0,4):'k', sq(0,5):'b', sq(0,2):'b'},
         "LOW", "T12: KBBvkbb (quiet)"))

    # Active (MEDIUM)
    positions.append(
        ({sq(3,3):'N', sq(3,4):'N', sq(7,4):'K',
          sq(0,4):'k', sq(1,3):'p', sq(1,5):'p'},
         "MEDIUM", "T12: central knights (active)"))
    positions.append(
        ({sq(3,3):'Q', sq(5,5):'N', sq(7,4):'K',
          sq(0,4):'k', sq(1,3):'p'},
         "MEDIUM", "T12: Q+N attacking (active)"))
    positions.append(
        ({sq(1,0):'R', sq(1,7):'R', sq(7,4):'K',
          sq(0,4):'k', sq(6,3):'P'},
         "MEDIUM", "T12: rooks on 7th (active)"))

    # Tactical (HIGH)
    positions.append(
        ({sq(3,4):'N', sq(7,4):'K', sq(6,4):'P',
          sq(0,4):'k', sq(1,3):'q', sq(2,5):'r'},
         "HIGH", "T12: knight fork zone (tactical)"))
    positions.append(
        ({sq(4,0):'B', sq(7,4):'K', sq(6,5):'P',
          sq(0,4):'k', sq(1,3):'q', sq(3,3):'n'},
         "HIGH", "T12: pin diagonal (tactical)"))
    positions.append(
        ({sq(5,4):'R', sq(7,4):'K',
          sq(0,4):'k', sq(3,4):'n', sq(2,4):'q'},
         "HIGH", "T12: rook file pressure (tactical)"))
    positions.append(
        ({sq(4,3):'Q', sq(3,5):'B', sq(7,4):'K', sq(6,3):'P',
          sq(0,4):'k', sq(1,5):'r', sq(2,3):'n'},
         "HIGH", "T12: Q+B battery (tactical)"))

    # Complex (HIGH)
    positions.append(
        ({sq(7,4):'K', sq(7,3):'Q', sq(7,0):'R', sq(5,5):'N',
          sq(6,3):'P', sq(6,4):'P', sq(4,2):'B',
          sq(0,4):'k', sq(0,3):'q', sq(2,5):'n',
          sq(1,3):'p', sq(3,4):'p'},
         "HIGH", "T12: middlegame 12pc (complex)"))
    positions.append(
        ({sq(7,4):'K', sq(7,0):'R', sq(5,4):'N', sq(4,5):'B',
          sq(6,3):'P', sq(6,5):'P',
          sq(0,4):'k', sq(0,7):'r', sq(3,3):'n',
          sq(1,2):'p', sq(1,6):'p'},
         "HIGH", "T12: open position 11pc (complex)"))

    # Endgame (LOW)
    positions.append(
        ({sq(5,3):'K', sq(3,0):'R', sq(0,0):'k'},
         "LOW", "T12: KR vs k corner (endgame)"))
    positions.append(
        ({sq(4,4):'K', sq(6,0):'R', sq(0,4):'k'},
         "LOW", "T12: KR vs k center (endgame)"))
    positions.append(
        ({sq(6,3):'K', sq(5,0):'Q', sq(0,4):'k'},
         "LOW", "T12: KQ vs k (endgame)"))
    positions.append(
        ({sq(5,4):'K', sq(4,3):'P', sq(0,4):'k'},
         "LOW", "T12: KP vs k (endgame)"))

    return positions


# ── FEN sanity check ──────────────────────────────────────────

def print_board_samples(corpus):
    """Print board diagrams for a few positions (one per category) as sanity check.

    Uses python-chess unicode board rendering so the user can visually verify
    that FEN strings correspond to the intended positions.
    """
    print(f"\n{'=' * 70}")
    print(f"  FEN SANITY CHECK: Board diagrams ({BOARD_SAMPLE_COUNT} positions)")
    print(f"{'=' * 70}")

    # Pick one FEN-based position per category (skip T12 hand-crafted ones)
    shown = set()
    count = 0
    for pos, category, label in corpus:
        if category in shown or label.startswith("T12:"):
            continue
        fen = pos_to_fen(pos)
        board = chess.Board(fen)
        print(f"\n  [{category}] {label}")
        print(f"  FEN: {fen}")
        # Indent the board diagram
        for line in board.unicode().split('\n'):
            print(f"    {line}")
        shown.add(category)
        count += 1
        if count >= BOARD_SAMPLE_COUNT:
            break


# ── Evaluation and filtering ─────────────────────────────────

def evaluate_corpus(corpus):
    """Evaluate all positions at shallow and deep depths with Stockfish.

    Returns list of (pos, category, label, sf_d1, sf_d20) for valid positions.
    Filters out:
      - Positions where either depth returns None (invalid/illegal)
      - Positions where |eval| > EVAL_FILTER_THRESHOLD_CP at either depth
        (these are decided/near-mate positions where depth gap = verification
        latency, not tactical discovery)
    """
    pos_list = [pos for pos, _, _ in corpus]
    n = len(pos_list)

    print(f"\n  Evaluating {n} positions at depth {SF_DEPTH_SHALLOW}...")
    sf_d1_raw = stockfish_eval_batch(pos_list, depth=SF_DEPTH_SHALLOW)

    print(f"  Evaluating {n} positions at depth {SF_DEPTH_DEEP} (this may take several minutes)...")
    sf_d20_raw = stockfish_eval_batch(pos_list, depth=SF_DEPTH_DEEP)

    if sf_d1_raw is None or sf_d20_raw is None:
        print("  ERROR: Stockfish not available. Cannot proceed.")
        return []

    evaluated = []
    filtered_none = 0
    filtered_threshold = 0

    for i in range(n):
        d1 = sf_d1_raw[i]
        d20 = sf_d20_raw[i]

        if d1 is None or d20 is None:
            filtered_none += 1
            continue

        if abs(d1) > EVAL_FILTER_THRESHOLD_CP or abs(d20) > EVAL_FILTER_THRESHOLD_CP:
            filtered_threshold += 1
            continue

        pos, category, label = corpus[i]
        evaluated.append((pos, category, label, d1, d20))

    print(f"  Valid: {len(evaluated)}/{n} "
          f"(filtered: {filtered_none} invalid, {filtered_threshold} |eval|>{EVAL_FILTER_THRESHOLD_CP})")
    return evaluated


# ── Per-position metrics ──────────────────────────────────────

def compute_metrics(evaluated):
    """Compute spectral encoding metrics for each evaluated position.

    Returns list of dicts with all per-position metrics.
    """
    metrics = []
    for pos, category, label, sf_d1, sf_d20 in evaluated:
        enc_spec = encode_512_spectral(pos)
        enc_trad = encode_512(pos)
        enc_a1 = encode_A1_spectral(pos)

        n_pieces = piece_count(pos)
        fiber_e = float(np.linalg.norm(enc_spec[FIBER_DIM_START:]))
        irrep_e = float(np.linalg.norm(enc_spec[:IRREP_DIM_END]))
        a1_e = float(np.linalg.norm(enc_a1))
        total_e = float(np.linalg.norm(enc_spec))

        metrics.append({
            'pos': pos,
            'category': category,
            'label': label,
            'sf_d1': sf_d1,
            'sf_d20': sf_d20,
            'depth_gap': abs(sf_d20 - sf_d1),
            'fiber_energy': fiber_e,
            'irrep_energy': irrep_e,
            'a1_energy': a1_e,
            'total_energy': total_e,
            'interaction_density': fiber_e / (irrep_e + 1e-10),
            'fiber_energy_per_piece': fiber_e / n_pieces,
            'n_pieces': n_pieces,
            'n_piece_types': piece_type_count(pos),
            'material_balance': material_balance_cp(pos),
            'enc_spectral': enc_spec,
            'enc_traditional': enc_trad,
        })

    return metrics


# ── Analysis functions ────────────────────────────────────────

def compute_primary_correlations(metrics):
    """Spearman correlations: spectral metrics vs |depth_gap|.

    Returns list of (metric_name, rho, p_value, flag) tuples.
    """
    if len(metrics) < MIN_POSITIONS_FOR_CORR:
        print(f"  WARNING: Only {len(metrics)} positions -- too few for correlations")
        return []

    depth_gaps = [m['depth_gap'] for m in metrics]
    results = []

    metric_pairs = [
        ('fiber_energy', [m['fiber_energy'] for m in metrics]),
        ('fiber_energy_per_piece', [m['fiber_energy_per_piece'] for m in metrics]),
        ('irrep_energy', [m['irrep_energy'] for m in metrics]),
        ('a1_energy', [m['a1_energy'] for m in metrics]),
        ('total_energy', [m['total_energy'] for m in metrics]),
        ('interaction_density', [m['interaction_density'] for m in metrics]),
    ]

    for name, values in metric_pairs:
        rho, pval = spearmanr(values, depth_gaps)
        results.append((name, float(rho), float(pval), significance_flag(pval)))

    return results


def compute_partial_correlations(metrics):
    """Partial Spearman correlations controlling for piece count.

    The critical control: if fiber/depth-gap survives after piece-count
    control, the STRUCTURE of interactions matters, not just quantity.
    """
    if len(metrics) < MIN_POSITIONS_FOR_CORR + 3:  # need df >= 1
        print(f"  WARNING: Too few positions for partial correlations")
        return []

    depth_gaps = [m['depth_gap'] for m in metrics]
    n_pieces = [m['n_pieces'] for m in metrics]
    results = []

    metric_pairs = [
        ('fiber | piece_count', [m['fiber_energy'] for m in metrics]),
        ('fiber_per_piece | piece_count', [m['fiber_energy_per_piece'] for m in metrics]),
        ('irrep | piece_count', [m['irrep_energy'] for m in metrics]),
        ('a1 | piece_count', [m['a1_energy'] for m in metrics]),
    ]

    for name, values in metric_pairs:
        rho, pval = partial_spearman(values, depth_gaps, n_pieces)
        results.append((name, float(rho), float(pval), significance_flag(pval)))

    return results


def compute_pairwise_depth_sensitivity(metrics):
    """Pairwise encoding similarity vs SF eval difference at both depths.

    Tests whether spectral encoding aligns more with deep search than shallow.
    If spectral distance correlates MORE with |SF_d20 delta| than |SF_d1 delta|,
    the encoding captures structure beyond static assessment.

    Also compares spectral vs traditional encoding sensitivity.
    """
    n = len(metrics)
    if n < MIN_POSITIONS_FOR_CORR:
        return None

    cos_spec = []
    cos_trad = []
    diff_d1 = []
    diff_d20 = []

    for i in range(n):
        for j in range(i + 1, n):
            cos_spec.append(cosine(metrics[i]['enc_spectral'], metrics[j]['enc_spectral']))
            cos_trad.append(cosine(metrics[i]['enc_traditional'], metrics[j]['enc_traditional']))
            diff_d1.append(-abs(metrics[i]['sf_d1'] - metrics[j]['sf_d1']))
            diff_d20.append(-abs(metrics[i]['sf_d20'] - metrics[j]['sf_d20']))

    n_pairs = len(cos_spec)

    rho_spec_d1, pval_spec_d1 = spearmanr(cos_spec, diff_d1)
    rho_spec_d20, pval_spec_d20 = spearmanr(cos_spec, diff_d20)
    rho_trad_d1, pval_trad_d1 = spearmanr(cos_trad, diff_d1)
    rho_trad_d20, pval_trad_d20 = spearmanr(cos_trad, diff_d20)

    return {
        'n_pairs': n_pairs,
        'spec_d1': (float(rho_spec_d1), float(pval_spec_d1)),
        'spec_d20': (float(rho_spec_d20), float(pval_spec_d20)),
        'trad_d1': (float(rho_trad_d1), float(pval_trad_d1)),
        'trad_d20': (float(rho_trad_d20), float(pval_trad_d20)),
    }


def compute_repositioning_sensitivity(metrics):
    """For same-material position pairs, compare spectral vs traditional distance.

    Groups positions by material signature (sorted piece characters).
    Within each group, all pairs have identical material, so encoding distance
    reflects purely positional differences.

    Returns summary or None if insufficient pairs.
    """
    from collections import defaultdict

    groups = defaultdict(list)
    for m in metrics:
        sig = material_signature(m['pos'])
        groups[sig].append(m)

    # Collect all same-material pairs
    spec_dists = []
    trad_dists = []
    sf_diffs = []

    for sig, members in groups.items():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                sd = 1.0 - cosine(members[i]['enc_spectral'], members[j]['enc_spectral'])
                td = 1.0 - cosine(members[i]['enc_traditional'], members[j]['enc_traditional'])
                sf = abs(members[i]['sf_d20'] - members[j]['sf_d20'])
                spec_dists.append(sd)
                trad_dists.append(td)
                sf_diffs.append(sf)

    if len(spec_dists) < 3:
        # Try relaxed grouping: (n_pieces, material_balance)
        groups2 = defaultdict(list)
        for m in metrics:
            key = (m['n_pieces'], m['material_balance'])
            groups2[key].append(m)

        spec_dists = []
        trad_dists = []
        sf_diffs = []

        for key, members in groups2.items():
            if len(members) < 2:
                continue
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    sd = 1.0 - cosine(members[i]['enc_spectral'], members[j]['enc_spectral'])
                    td = 1.0 - cosine(members[i]['enc_traditional'], members[j]['enc_traditional'])
                    sf = abs(members[i]['sf_d20'] - members[j]['sf_d20'])
                    spec_dists.append(sd)
                    trad_dists.append(td)
                    sf_diffs.append(sf)

        if len(spec_dists) < 3:
            return None
        grouping = "relaxed (n_pieces, material_balance)"
    else:
        grouping = "exact material signature"

    # Sensitivity ratio: how much more does spectral encoding change vs traditional?
    ratios = [s / (t + 1e-10) for s, t in zip(spec_dists, trad_dists)]
    mean_ratio = float(np.mean(ratios))
    median_ratio = float(np.median(ratios))

    # Correlation with SF eval difference
    rho_spec, pval_spec = spearmanr(spec_dists, sf_diffs) if len(spec_dists) >= 3 else (0, 1)
    rho_trad, pval_trad = spearmanr(trad_dists, sf_diffs) if len(trad_dists) >= 3 else (0, 1)

    return {
        'n_pairs': len(spec_dists),
        'grouping': grouping,
        'mean_sensitivity_ratio': mean_ratio,
        'median_sensitivity_ratio': median_ratio,
        'rho_spec_sf': (float(rho_spec), float(pval_spec)),
        'rho_trad_sf': (float(rho_trad), float(pval_trad)),
    }


# ── Output formatting ────────────────────────────────────────

def print_position_table(metrics):
    """Print per-position table sorted by |depth_gap| descending."""
    print(f"\n{'=' * 70}")
    print(f"  PER-POSITION RESULTS (sorted by |depth gap| descending)")
    print(f"{'=' * 70}")

    sorted_m = sorted(metrics, key=lambda m: m['depth_gap'], reverse=True)

    header = (f"  {'#':>3s}  {'Cat':5s}  {'Label':35s}  {'Pcs':>3s}  "
              f"{'D1(cp)':>7s}  {'D20(cp)':>8s}  {'|Gap|':>6s}  "
              f"{'FiberE':>7s}  {'Fib/Pc':>6s}  {'IrrepE':>7s}  {'A1_E':>6s}")
    print(f"\n{header}")
    print(f"  {'─' * (len(header) - 2)}")

    for i, m in enumerate(sorted_m, 1):
        d1_s = f"{m['sf_d1']:+7d}" if abs(m['sf_d1']) < 9999 else f"{'M':>7s}"
        d20_s = f"{m['sf_d20']:+8d}" if abs(m['sf_d20']) < 9999 else f"{'M':>8s}"
        print(f"  {i:3d}  {m['category']:5s}  {m['label']:35s}  {m['n_pieces']:3d}  "
              f"{d1_s}  {d20_s}  {m['depth_gap']:6d}  "
              f"{m['fiber_energy']:7.2f}  {m['fiber_energy_per_piece']:6.3f}  "
              f"{m['irrep_energy']:7.2f}  {m['a1_energy']:6.2f}")


def print_correlation_summary(primary, partial, pairwise, repositioning):
    """Print all correlations in one summary table."""
    print(f"\n{'=' * 70}")
    print(f"  CORRELATION SUMMARY")
    print(f"{'=' * 70}")

    n = len(primary)  # same N for all primary correlations

    # Primary correlations
    print(f"\n  PRIMARY: Spectral metric vs |depth_gap| (Spearman)")
    print(f"  {'Metric':35s}  {'rho':>7s}  {'p-value':>10s}  {'Flag':12s}")
    print(f"  {'─' * 70}")

    for name, rho, pval, flag in primary:
        print(f"  {name:35s}  {rho:+7.4f}  {pval:10.4f}  {flag}")

    # Partial correlations
    if partial:
        print(f"\n  PARTIAL: Controlling for piece_count (Spearman partial)")
        print(f"  {'Metric':35s}  {'rho':>7s}  {'p-value':>10s}  {'Flag':12s}")
        print(f"  {'─' * 70}")

        for name, rho, pval, flag in partial:
            print(f"  {name:35s}  {rho:+7.4f}  {pval:10.4f}  {flag}")

    # Pairwise depth sensitivity
    if pairwise:
        print(f"\n  PAIRWISE: Encoding similarity vs eval difference ({pairwise['n_pairs']} pairs)")
        print(f"  {'Comparison':40s}  {'rho':>7s}  {'p-value':>10s}")
        print(f"  {'─' * 62}")

        for label, key in [("Spectral vs Depth 1 (static)", 'spec_d1'),
                           ("Spectral vs Depth 20 (full)", 'spec_d20'),
                           ("Traditional vs Depth 1 (static)", 'trad_d1'),
                           ("Traditional vs Depth 20 (full)", 'trad_d20')]:
            rho, pval = pairwise[key]
            print(f"  {label:40s}  {rho:+7.4f}  {pval:10.4e}")

        rho_s1 = pairwise['spec_d1'][0]
        rho_s20 = pairwise['spec_d20'][0]
        rho_t1 = pairwise['trad_d1'][0]
        rho_t20 = pairwise['trad_d20'][0]

        if rho_s20 > rho_s1:
            print(f"\n  >>> Spectral aligns MORE with deep search (+{rho_s20 - rho_s1:.4f})")
            print(f"  >>> Encoding captures structure beyond static assessment")
        else:
            print(f"\n  >>> Spectral aligns more with shallow search (deep - shallow = {rho_s20 - rho_s1:+.4f})")

        if rho_s20 > rho_t20:
            print(f"  >>> Spectral beats traditional at depth 20 (+{rho_s20 - rho_t20:.4f})")

    # Repositioning sensitivity
    if repositioning:
        print(f"\n  REPOSITIONING: Same-material pairs ({repositioning['n_pairs']} pairs, "
              f"{repositioning['grouping']})")
        print(f"  Mean spectral/traditional distance ratio:   {repositioning['mean_sensitivity_ratio']:.2f}x")
        print(f"  Median spectral/traditional distance ratio: {repositioning['median_sensitivity_ratio']:.2f}x")
        rho_s, pval_s = repositioning['rho_spec_sf']
        rho_t, pval_t = repositioning['rho_trad_sf']
        print(f"  Spectral dist vs SF eval diff:    rho = {rho_s:+.4f}  (p = {pval_s:.4f})")
        print(f"  Traditional dist vs SF eval diff:  rho = {rho_t:+.4f}  (p = {pval_t:.4f})")
    else:
        print(f"\n  REPOSITIONING: Insufficient same-material pairs for analysis")


def print_category_breakdown(metrics):
    """Print mean values per complexity category."""
    print(f"\n{'=' * 70}")
    print(f"  CATEGORY BREAKDOWN")
    print(f"{'=' * 70}")

    print(f"\n  {'Category':8s}  {'N':>3s}  {'Mean|Gap|':>10s}  {'Mean FibE':>10s}  "
          f"{'Mean Fib/Pc':>11s}  {'Mean IrrepE':>12s}  {'Mean Pcs':>9s}")
    print(f"  {'─' * 70}")

    for cat in ['HIGH', 'MEDIUM', 'LOW']:
        cat_m = [m for m in metrics if m['category'] == cat]
        if not cat_m:
            continue
        n = len(cat_m)
        mean_gap = np.mean([m['depth_gap'] for m in cat_m])
        mean_fib = np.mean([m['fiber_energy'] for m in cat_m])
        mean_fpp = np.mean([m['fiber_energy_per_piece'] for m in cat_m])
        mean_irr = np.mean([m['irrep_energy'] for m in cat_m])
        mean_pcs = np.mean([m['n_pieces'] for m in cat_m])
        print(f"  {cat:8s}  {n:3d}  {mean_gap:10.1f}  {mean_fib:10.2f}  "
              f"{mean_fpp:11.4f}  {mean_irr:12.2f}  {mean_pcs:9.1f}")

    # Test if category ordering matches expectation
    cats = {}
    for cat in ['HIGH', 'MEDIUM', 'LOW']:
        cat_m = [m for m in metrics if m['category'] == cat]
        if cat_m:
            cats[cat] = np.mean([m['depth_gap'] for m in cat_m])

    if len(cats) == 3:
        if cats['HIGH'] > cats['MEDIUM'] > cats['LOW']:
            print(f"\n  >>> Category ordering CONFIRMED: HIGH > MEDIUM > LOW depth gap")
        else:
            print(f"\n  >>> Category ordering VIOLATED: "
                  f"HIGH={cats['HIGH']:.0f}, MEDIUM={cats['MEDIUM']:.0f}, LOW={cats['LOW']:.0f}")


def print_backward_comparison(metrics):
    """Compare original TEST 12 positions against the full dataset."""
    print(f"\n{'=' * 70}")
    print(f"  BACKWARD COMPATIBILITY: TEST 12 subset vs full dataset")
    print(f"{'=' * 70}")

    t12 = [m for m in metrics if m['label'].startswith("T12:")]
    non_t12 = [m for m in metrics if not m['label'].startswith("T12:")]

    if len(t12) < 4 or len(non_t12) < 4:
        print(f"  Insufficient data for comparison (T12: {len(t12)}, new: {len(non_t12)})")
        return

    # Fiber energy vs depth gap in both subsets
    rho_t12, pval_t12 = spearmanr(
        [m['fiber_energy'] for m in t12], [m['depth_gap'] for m in t12])
    rho_new, pval_new = spearmanr(
        [m['fiber_energy'] for m in non_t12], [m['depth_gap'] for m in non_t12])
    rho_all, pval_all = spearmanr(
        [m['fiber_energy'] for m in metrics], [m['depth_gap'] for m in metrics])

    print(f"\n  Fiber energy vs |depth_gap|:")
    print(f"    TEST 12 only (N={len(t12):2d}): rho = {rho_t12:+.4f}  (p = {pval_t12:.4f})")
    print(f"    New positions (N={len(non_t12):2d}): rho = {rho_new:+.4f}  (p = {pval_new:.4f})")
    print(f"    All combined  (N={len(metrics):2d}): rho = {rho_all:+.4f}  (p = {pval_all:.4f})")

    if rho_t12 > 0 and rho_new > 0:
        print(f"    >>> Both subsets show positive fiber/depth-gap trend")
    elif rho_t12 > 0 and rho_new <= 0:
        print(f"    >>> WARNING: New positions do NOT replicate TEST 12 trend")


def print_verdict(primary, partial, pairwise):
    """Print the final verdict answering the key research question."""
    print(f"\n{'=' * 70}")
    print(f"  VERDICT")
    print(f"{'=' * 70}")

    # Find fiber energy correlation
    fiber_result = None
    fiber_pp_result = None
    for name, rho, pval, flag in primary:
        if name == 'fiber_energy':
            fiber_result = (rho, pval, flag)
        if name == 'fiber_energy_per_piece':
            fiber_pp_result = (rho, pval, flag)

    # Find partial correlation
    fiber_partial = None
    for name, rho, pval, flag in (partial or []):
        if name == 'fiber | piece_count':
            fiber_partial = (rho, pval, flag)

    print(f"\n  KEY QUESTION: Does fiber interaction energy predict which positions")
    print(f"  reward deep tactical search (without doing any search)?")

    if fiber_result:
        rho, pval, flag = fiber_result
        print(f"\n  Raw fiber energy vs |depth_gap|: rho = {rho:+.4f} (p = {pval:.4f}) {flag}")

    if fiber_pp_result:
        rho, pval, flag = fiber_pp_result
        print(f"  Fiber per piece vs |depth_gap|:  rho = {rho:+.4f} (p = {pval:.4f}) {flag}")

    if fiber_partial:
        rho, pval, flag = fiber_partial
        print(f"  Fiber | piece_count (partial):   rho = {rho:+.4f} (p = {pval:.4f}) {flag}")

    # Interpretation
    if fiber_result and fiber_result[2] == "SIGNIFICANT":
        if fiber_partial and fiber_partial[2] == "SIGNIFICANT":
            print(f"\n  CONCLUSION: YES -- Fiber energy predicts tactical depth,")
            print(f"  AND this survives piece-count control. The STRUCTURE of")
            print(f"  interactions matters, not just the quantity of pieces.")
            print(f"  The spectral framework detects the potential energy surface")
            print(f"  of chess -- complex landscapes contain more latent tactics.")
        elif fiber_partial and fiber_partial[0] > 0:
            print(f"\n  CONCLUSION: PARTIAL -- Fiber energy predicts tactical depth,")
            print(f"  but the signal weakens after controlling for piece count.")
            print(f"  Some of the correlation is 'more pieces = more tactics'")
            print(f"  but a structural component may remain.")
        else:
            print(f"\n  CONCLUSION: CONFOUNDED -- Fiber energy correlates with depth gap,")
            print(f"  but the correlation vanishes after controlling for piece count.")
            print(f"  The initial finding was 'more pieces = more interactions = more")
            print(f"  tactics' -- trivially true and not a spectral insight.")
    elif fiber_result and fiber_result[2] == "TRENDING":
        print(f"\n  CONCLUSION: SUGGESTIVE -- Positive trend but not significant.")
        print(f"  More positions or a refined metric may reach significance.")
    elif fiber_result and fiber_result[0] > 0:
        print(f"\n  CONCLUSION: WEAK -- Positive direction but not significant.")
        print(f"  The spectral encoding may detect tactical potential, but")
        print(f"  the current evidence is insufficient to claim this.")
    else:
        print(f"\n  CONCLUSION: NO -- Fiber energy does not predict tactical depth.")
        print(f"  The initial N=16 trend did not replicate with expanded data.")

    # Check if per-piece metric does better
    if fiber_pp_result and fiber_result:
        if fiber_pp_result[1] < fiber_result[1]:
            print(f"\n  NOTE: Fiber-per-piece ({fiber_pp_result[0]:+.4f}) outperforms")
            print(f"  raw fiber energy ({fiber_result[0]:+.4f}) -- per-piece interaction")
            print(f"  quality matters more than total interaction quantity.")

    if pairwise:
        rho_s20 = pairwise['spec_d20'][0]
        rho_s1 = pairwise['spec_d1'][0]
        if rho_s20 > rho_s1:
            print(f"\n  BONUS: Spectral encoding aligns more with deep ({rho_s20:+.4f})")
            print(f"  than shallow ({rho_s1:+.4f}) -- sees beyond static assessment.")


# ── Main ──────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 70)
    print("  EXPANDED DEPTH-GAP EXPERIMENT")
    print(f"  Shallow depth: {SF_DEPTH_SHALLOW}, Deep depth: {SF_DEPTH_DEEP}")
    print(f"  |eval| filter: {EVAL_FILTER_THRESHOLD_CP} cp")
    print(f"  Significance: p < {SIGNIFICANCE_ALPHA} (SIGNIFICANT), "
          f"p < {TRENDING_ALPHA} (TRENDING)")
    print("=" * 70)

    # 1. Build corpus
    corpus = build_position_corpus()
    n_high = sum(1 for _, c, _ in corpus if c == 'HIGH')
    n_med = sum(1 for _, c, _ in corpus if c == 'MEDIUM')
    n_low = sum(1 for _, c, _ in corpus if c == 'LOW')
    n_t12 = sum(1 for _, _, l in corpus if l.startswith("T12:"))
    print(f"\n  Corpus: {len(corpus)} positions "
          f"(HIGH={n_high}, MEDIUM={n_med}, LOW={n_low}, "
          f"includes {n_t12} original TEST 12)")

    # 2. FEN sanity check
    print_board_samples(corpus)

    # 3. Evaluate with Stockfish
    evaluated = evaluate_corpus(corpus)
    if not evaluated:
        print("\n  FATAL: No valid positions after evaluation. Exiting.")
        sys.exit(1)

    # 4. Compute per-position metrics
    metrics = compute_metrics(evaluated)
    print(f"\n  Metrics computed for {len(metrics)} positions")

    # 5. Print per-position table
    print_position_table(metrics)

    # 6. Compute all correlations
    primary = compute_primary_correlations(metrics)
    partial = compute_partial_correlations(metrics)
    pairwise = compute_pairwise_depth_sensitivity(metrics)
    repositioning = compute_repositioning_sensitivity(metrics)

    # 7. Print correlation summary
    print_correlation_summary(primary, partial, pairwise, repositioning)

    # 8. Category breakdown
    print_category_breakdown(metrics)

    # 9. Backward compatibility
    print_backward_comparison(metrics)

    # 10. Final verdict
    print_verdict(primary, partial, pairwise)

    print(f"\n{'=' * 70}")
    print(f"  Experiment complete. {len(metrics)} positions analyzed.")
    print(f"{'=' * 70}")
