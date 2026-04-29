"""Encoder injectivity probe for chess_spectral.encoder_4d.encode_4d.

Pre-flight check #1 for the planned chess_spectral.qm_4d module: the
state-to-psi map state_to_psi(position) is required to be injective on
the corpus of legal 4D positions, since the QM correspondence ψ ↔
position breaks if two distinct positions hash to identical 45056-dim
float32 vectors.

Strategy: build a >=1000-element corpus of distinct 4D positions from
three sources (in order of preference):
    1. Seeded self-play via tests/test_smoke_e2e._seeded_self_play_4d
    2. Static fixtures in tests/fixtures/positions_4d.jsonl
    3. Synthesized: K@(0,0,0,0) + k@(7,7,7,7) + ONE extra piece varied
       across piece type x square in Z_8^4 (excluding the king corners)

Encode each position via Python encoder (we have C-Python parity at
1e-10), hash exact bit pattern of float32[45056] via SHA-256, and report
collisions FEN4-by-FEN4. Saves the corpus + per-position hash to
encoder_injectivity_4d_results.csv next to this file.

Run from python/ working dir so chess_spectral resolves:
    python research/encoder_injectivity_4d.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import warnings
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# ---- Path bootstrap so this file can be invoked directly -------------
HERE = Path(__file__).resolve().parent
PYTHON_DIR = HERE.parent  # .../chess-spectral/python
TESTS_DIR = PYTHON_DIR / "tests"
FIXTURES_PATH = TESTS_DIR / "fixtures" / "positions_4d.jsonl"
RESULTS_CSV = HERE / "encoder_injectivity_4d_results.csv"

# Prepend the python/ dir so `chess_spectral` and the `tests` package
# are both importable regardless of the user's PYTHONPATH.
for p in (str(PYTHON_DIR), str(TESTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402

from chess_spectral.encoder_4d import encode_4d, ENCODING_DIM_4D  # noqa: E402
from chess_spectral import fen_4d  # noqa: E402


# ---- Corpus sources --------------------------------------------------

def _piece_value_from_str(s: str):
    """Mirror fixtures convention: 1-char non-pawn or 2-char pawn (color+axis)."""
    if len(s) == 2 and s[0] in ("P", "p"):
        return (s[0], s[1])
    return s


def _pos_to_fen4(pos: Dict[int, object]) -> str:
    """Serialize a position dict (sq_idx -> piece value) to FEN4 v1.

    Used as a canonical key for de-duplicating positions across sources.
    Mirrors the format produced by _seeded_self_play_4d._to_fen4 but
    works on int square indices."""
    if not pos:
        return "4d-fen v1:"

    def _coord(sq: int) -> Tuple[int, int, int, int]:
        x = (sq >> 9) & 7
        y = (sq >> 6) & 7
        z = (sq >> 3) & 7
        w = sq & 7
        return (x, y, z, w)

    parts: List[str] = []
    for sq in sorted(pos.keys()):
        v = pos[sq]
        if isinstance(v, tuple):
            piece_str = v[0] + v[1]  # e.g. "Pw"
        else:
            piece_str = v
        x, y, z, w = _coord(sq)
        parts.append(f"{piece_str}@{x},{y},{z},{w}")
    return "4d-fen v1: " + "; ".join(parts)


def gather_seeded_self_play(n_seeds: int, max_plies: int) -> List[Tuple[str, Dict[int, object]]]:
    """Run _seeded_self_play_4d for multiple seeds; return list of
    (fen4, pos_dict). The helper produces a sequence of plies; each ply
    is one position."""
    # Suppress the helper's import warnings about pawn axis defaults.
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from test_smoke_e2e import _seeded_self_play_4d  # type: ignore[attr-defined]

    out: List[Tuple[str, Dict[int, object]]] = []
    for seed in range(1, n_seeds + 1):
        plies = _seeded_self_play_4d(white_seed=seed, black_seed=seed * 31 + 7,
                                     max_plies=max_plies)
        for p in plies:
            fen4 = p["fen4"]
            try:
                pos = fen_4d.parse(fen4)
            except fen_4d.Fen4ParseError as e:
                print(f"  WARN: seed={seed} ply={p['ply']} parse error: {e}",
                      file=sys.stderr)
                continue
            out.append((fen4, pos))
    return out


def gather_fixtures(path: Path) -> List[Tuple[str, Dict[int, object]]]:
    """Load each line of positions_4d.jsonl, convert to (fen4, pos_dict)."""
    out: List[Tuple[str, Dict[int, object]]] = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            pieces_raw = obj.get("pieces", {})
            pos: Dict[int, object] = {}
            for sq_str, piece_str in pieces_raw.items():
                pos[int(sq_str)] = _piece_value_from_str(piece_str)
            fen4 = _pos_to_fen4(pos)
            out.append((fen4, pos))
    return out


def gather_synthetic_one_extra_piece() -> List[Tuple[str, Dict[int, object]]]:
    """K@(0,0,0,0) + k@(7,7,7,7) + ONE extra piece at every other
    Z_8^4 square, varying piece type. ~6 * 4094 = ~24564 positions.

    Piece types span: N, B, R, Q (skip P/p — pawn requires axis suffix
    AND axis constraints; we add a separate small synthetic block for
    pawn-axis sweep below). White-K and black-k corners are excluded
    from the 'extra' loop. Both colors of each non-pawn piece are used
    so we get good entropy on the encoder's signed channels.
    """
    out: List[Tuple[str, Dict[int, object]]] = []
    K_SQ = 0  # (0,0,0,0)
    k_SQ = 4095  # (7,7,7,7)
    base = {K_SQ: "K", k_SQ: "k"}

    EXTRA_PIECE_VALUES = ["N", "n", "B", "b", "R", "r", "Q", "q"]

    for piece in EXTRA_PIECE_VALUES:
        for sq in range(4096):
            if sq in (K_SQ, k_SQ):
                continue
            pos = dict(base)
            pos[sq] = piece
            fen4 = _pos_to_fen4(pos)
            out.append((fen4, pos))

    # Plus a small pawn-axis sweep: pawns at every square (axis = 'w')
    # to prove pawn channels also probed for collisions.
    for piece_color in ("P", "p"):
        for sq in range(4096):
            if sq in (K_SQ, k_SQ):
                continue
            pos = dict(base)
            pos[sq] = (piece_color, "w")
            fen4 = _pos_to_fen4(pos)
            out.append((fen4, pos))

    return out


# ---- Hashing & analysis ---------------------------------------------

def vec_hash_sha256(vec: np.ndarray) -> str:
    """SHA-256 of the EXACT float32 byte pattern. No float-tolerance
    fuzzing; bit-identical encodings produce identical hashes."""
    assert vec.dtype == np.float32, f"expected float32, got {vec.dtype}"
    assert vec.shape == (ENCODING_DIM_4D,), f"shape {vec.shape}"
    return hashlib.sha256(vec.tobytes()).hexdigest()


# ---- Main driver -----------------------------------------------------

def main() -> int:
    print("=" * 72)
    print("encode_4d INJECTIVITY PROBE")
    print("=" * 72)

    # Source 1: self-play
    print("\n[1/3] Gathering seeded self-play positions...")
    sp = gather_seeded_self_play(n_seeds=20, max_plies=30)
    print(f"      collected {len(sp)} positions ({20} seeds x up to 31 plies)")

    # Source 2: static fixtures
    print("\n[2/3] Loading static fixtures from positions_4d.jsonl...")
    fx = gather_fixtures(FIXTURES_PATH)
    print(f"      loaded {len(fx)} fixtures")

    # Source 3: synthetic one-extra-piece sweep
    print("\n[3/3] Synthesizing one-extra-piece corpus...")
    sy = gather_synthetic_one_extra_piece()
    print(f"      synthesized {len(sy)} positions")

    # Combine; dedupe by FEN4 string (each position appears once even if
    # it shows up in multiple sources — the *encoding* of duplicates is
    # trivially identical so it would hide collisions).
    print("\nDeduplicating by FEN4 string...")
    by_fen: Dict[str, Dict[int, object]] = {}
    source_for_fen: Dict[str, str] = {}
    for label, src in (("self_play", sp), ("fixture", fx), ("synthetic", sy)):
        for fen4, pos in src:
            if fen4 not in by_fen:
                by_fen[fen4] = pos
                source_for_fen[fen4] = label

    n_total = len(sp) + len(fx) + len(sy)
    n_unique_positions = len(by_fen)
    print(f"  raw total:             {n_total}")
    print(f"  unique by FEN4 string: {n_unique_positions}")

    # Encode + hash
    print(f"\nEncoding + hashing {n_unique_positions} positions...")
    rows: List[Tuple[str, str, str, float]] = []  # (fen4, src, hash, l2)
    hash_to_fens: Dict[str, List[str]] = {}
    norms: List[float] = []
    for i, (fen4, pos) in enumerate(by_fen.items()):
        if i % 5000 == 0 and i > 0:
            print(f"  ... {i}/{n_unique_positions}")
        vec = encode_4d(pos)
        h = vec_hash_sha256(vec)
        l2 = float(np.linalg.norm(vec))
        rows.append((fen4, source_for_fen[fen4], h, l2))
        hash_to_fens.setdefault(h, []).append(fen4)
        norms.append(l2)

    n_unique_encodings = len(hash_to_fens)
    n_collisions = n_unique_positions - n_unique_encodings

    # Report
    print("\n" + "=" * 72)
    print("RESULTS")
    print("=" * 72)
    print(f"n_positions (after FEN4 dedupe):  {n_unique_positions}")
    print(f"n_unique_positions (by FEN4):     {n_unique_positions}")
    print(f"n_unique_encodings (by SHA-256):  {n_unique_encodings}")
    print(f"collisions (positions - encodings): {n_collisions}")

    norms_arr = np.array(norms, dtype=np.float64)
    print("\nL2 norm distribution of encoding vectors:")
    print(f"  min:    {norms_arr.min():.6f}")
    print(f"  median: {float(np.median(norms_arr)):.6f}")
    print(f"  max:    {norms_arr.max():.6f}")

    # Source breakdown
    print("\nBreakdown by source (after dedupe):")
    src_counts: Dict[str, int] = {}
    for (_fen, src, _h, _l2) in rows:
        src_counts[src] = src_counts.get(src, 0) + 1
    for k, v in sorted(src_counts.items()):
        print(f"  {k:12s}: {v}")

    if n_collisions > 0:
        print(f"\n*** {n_collisions} COLLISIONS DETECTED ***")
        colliding = [(h, fens) for h, fens in hash_to_fens.items() if len(fens) > 1]
        # Sort: largest collision-cluster first
        colliding.sort(key=lambda kv: -len(kv[1]))
        print("First 5 colliding-FEN4 pairs (or larger clusters):")
        shown = 0
        for h, fens in colliding:
            if shown >= 5:
                break
            print(f"\n  Cluster size {len(fens)}, hash {h[:16]}...")
            for fen4 in fens[:4]:
                print(f"    {fen4}")
            if len(fens) > 4:
                print(f"    ... and {len(fens) - 4} more")
            shown += 1
    else:
        print("\nVERDICT: encode_4d is INJECTIVE on the tested corpus.")

    # CSV
    print(f"\nWriting CSV to {RESULTS_CSV}")
    with RESULTS_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fen4", "source", "encoding_sha256", "l2_norm"])
        for r in rows:
            w.writerow(r)
    print(f"  wrote {len(rows)} rows")

    return 0 if n_collisions == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
