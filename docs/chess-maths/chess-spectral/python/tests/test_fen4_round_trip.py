"""FEN4 round-trip tests (chess-spectral 1.4.0, §16.9 #4 / §17.4).

Covers the inverse-of-parse contract: ``parse(serialize(p)) == p``
for any valid 4D position dict. Exercises:

    * the 15 fixture positions in tests/fixtures/positions_4d.jsonl
    * 100 seeded self-play positions (random small placements)
    * the empty position (serializes to just the prefix)
    * the 4D startpos analog (full 896-piece dense board)
    * piece-value provenance for non-pawns and pawn (color, axis)
      tuples
    * the canonical-form property (consecutive serialize → parse →
      serialize cycles converge to a fixed string)
    * malformed-input rejection by ``serialize``

Run via::

    cd python && python -m pytest tests/test_fen4_round_trip.py -v
"""

from __future__ import annotations

import json
import os
import random
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import fen_4d  # noqa: E402


FIXTURES_PATH = os.path.join(HERE, "fixtures", "positions_4d.jsonl")


# ─── Fixture loading ────────────────────────────────────────────────

def _fixture_to_pos_dict(pieces: dict) -> dict:
    """Translate the JSONL fixture format ({sq_str: piece_str}) into
    the position dict consumed by encoder_4d / serialize.

    Pawn values 'Pw' / 'Py' / 'pw' / 'py' decode to (color, axis)
    tuples; non-pawns stay as single-char strings.
    """
    out = {}
    for sq_str, piece_str in pieces.items():
        sq = int(sq_str)
        if piece_str[0] in ("P", "p"):
            color = piece_str[0]
            axis = piece_str[1] if len(piece_str) > 1 else "w"
            out[sq] = (color, axis)
        else:
            out[sq] = piece_str
    return out


def _load_fixtures() -> list:
    """Load all 15 fixture positions as (name, pos_dict) tuples."""
    fixtures = []
    with open(FIXTURES_PATH, "r", encoding="utf-8") as fp:
        for line in fp:
            rec = json.loads(line)
            fixtures.append((rec["name"], _fixture_to_pos_dict(rec["pieces"])))
    return fixtures


FIXTURE_DATA = _load_fixtures()


# ─── Fixture-based round-trip ──────────────────────────────────────

@pytest.mark.parametrize("name,pos", FIXTURE_DATA)
def test_fixture_round_trip(name: str, pos: dict) -> None:
    """parse(serialize(p)) == p for every fixture position."""
    serialized = fen_4d.serialize(pos)
    re_parsed = fen_4d.parse(serialized)
    assert re_parsed == pos, (
        f"round-trip mismatch for fixture {name!r}: "
        f"original={pos}, after round-trip={re_parsed}"
    )


def test_fixture_count() -> None:
    """The fixture file should contain exactly 15 positions (the
    documented count in tests/fixtures/positions_4d.jsonl). If this
    fails, either the fixture changed (bump the constant) or the
    loader is broken."""
    assert len(FIXTURE_DATA) == 15


# ─── Empty position edge case ──────────────────────────────────────

def test_empty_position_serializes_to_bare_prefix() -> None:
    """An empty position must serialize to just ``'4d-fen v1:'`` (the
    prefix, no trailing pieces or whitespace), and parse back to {}."""
    out = fen_4d.serialize({})
    assert out == "4d-fen v1:"
    assert fen_4d.parse(out) == {}


def test_empty_position_round_trip_idempotent() -> None:
    """Applying serialize→parse→serialize twice must produce the same
    canonical form on the second pass — i.e. serialize is a fixed
    point under the parse→serialize composition."""
    pos = {}
    s1 = fen_4d.serialize(pos)
    p1 = fen_4d.parse(s1)
    s2 = fen_4d.serialize(p1)
    assert s1 == s2


# ─── Side-to-move comment (FEN4 v1 design) ─────────────────────────

def test_side_to_move_not_encoded_by_fen4_v1() -> None:
    """FEN4 v1 deliberately does NOT encode side-to-move on the wire
    (it's a placement-only literal). v1.4.0 ships side-to-move as a
    runtime field on GameState4D / MoveHistory4D, NOT a FEN4 feature.

    This test pins the design: serialize is purely placement; two
    positions that differ only in 'whose turn is it' produce
    bit-identical strings.
    """
    pos = {0: "K", 4095: "k"}
    assert fen_4d.serialize(pos) == "4d-fen v1: K@0,0,0,0; k@7,7,7,7"
    # The FEN4 has no whitespace / token / suffix that varies by
    # side-to-move. A consumer that needs side-to-move must track it
    # alongside the literal (e.g. via GameState4D).


# ─── 4D startpos (full 896-piece board) ────────────────────────────

def _build_4d_startpos_dense() -> dict:
    """Construct a dense 4D position with 896 pieces. The 4D rules of
    Oana & Chiru (2026) are still under discussion at the
    startpos-density level; we don't need the *correct* startpos
    here — we just need a maximally-stress-tested position so the
    serializer is exercised at the scale of a real 4D game.

    Layout: each w-layer is filled with one piece type:
        w=0: 64 white kings        w=7: 64 black kings
        w=1: 64 white queens       w=6: 64 black queens
        w=2: 64 white rooks        w=5: 64 black rooks
        w=3: 64 W-axis white pawns w=4: 64 W-axis black pawns

    Each layer holds 8 * 8 * 8 = 512 squares (cube over (x, y, z)),
    so the 8 w-layers together fill all 8 * 512 = 4096 squares — i.e.
    every cell on the lattice is occupied. This is the maximum-density
    stress case for the FEN4 placement literal.
    """
    pos: dict = {}
    layout_by_w = {
        0: "K",
        7: "k",
        1: "Q",
        6: "q",
        2: "R",
        5: "r",
        3: ("P", "w"),
        4: ("p", "w"),
    }
    for w_target, value in layout_by_w.items():
        for x in range(8):
            for y in range(8):
                for z in range(8):
                    sq = ((x * 8 + y) * 8 + z) * 8 + w_target
                    pos[sq] = value
    return pos


def test_4d_startpos_round_trip() -> None:
    """Round-trip a 4096-piece (every-cell) dense position through
    serialize→parse. This is the FEN4 'maximum density' stress case."""
    pos = _build_4d_startpos_dense()
    assert len(pos) == 4096
    s = fen_4d.serialize(pos)
    re_parsed = fen_4d.parse(s)
    assert re_parsed == pos


def test_4d_startpos_canonical_idempotent() -> None:
    """serialize(parse(serialize(p))) == serialize(p) for the dense
    startpos — confirming canonical form for large positions."""
    pos = _build_4d_startpos_dense()
    s1 = fen_4d.serialize(pos)
    s2 = fen_4d.serialize(fen_4d.parse(s1))
    assert s1 == s2


def test_4d_full_board_round_trip_alphabet() -> None:
    """Round-trip a 4096-piece position that cycles through every
    piece value (all non-pawns plus pawn axis variants), so every
    branch of the serialize value-encoding logic is exercised."""
    pos = {}
    for sq in range(4096):
        cycle = sq % 12
        if cycle == 0:
            pos[sq] = "K"
        elif cycle == 1:
            pos[sq] = "k"
        elif cycle == 2:
            pos[sq] = "Q"
        elif cycle == 3:
            pos[sq] = "q"
        elif cycle == 4:
            pos[sq] = "R"
        elif cycle == 5:
            pos[sq] = "r"
        elif cycle == 6:
            pos[sq] = "B"
        elif cycle == 7:
            pos[sq] = "b"
        elif cycle == 8:
            pos[sq] = "N"
        elif cycle == 9:
            pos[sq] = "n"
        elif cycle == 10:
            pos[sq] = ("P", "w")
        else:
            pos[sq] = ("p", "y")
    s = fen_4d.serialize(pos)
    re_parsed = fen_4d.parse(s)
    assert re_parsed == pos
    assert len(re_parsed) == 4096


# ─── Random self-play round-trip (100 positions) ───────────────────

def _seeded_random_position(rng: random.Random, n_pieces: int) -> dict:
    """Generate a random valid position with up to ``n_pieces`` pieces.
    Squares are sampled without replacement; piece values are drawn
    from the full 4D piece alphabet including pawn (color, axis)
    tuples on both pawn axes.
    """
    pieces_white = ["N", "B", "R", "Q", "K"]
    pieces_black = ["n", "b", "r", "q", "k"]
    pawn_colors = ["P", "p"]
    pawn_axes = ["w", "y"]

    n_pieces = min(n_pieces, 4096)
    squares = rng.sample(range(4096), n_pieces)
    pos: dict = {}
    for sq in squares:
        roll = rng.random()
        if roll < 0.4:
            pos[sq] = (rng.choice(pawn_colors), rng.choice(pawn_axes))
        elif roll < 0.7:
            pos[sq] = rng.choice(pieces_white)
        else:
            pos[sq] = rng.choice(pieces_black)
    return pos


@pytest.mark.parametrize("seed", list(range(100)))
def test_random_position_round_trip(seed: int) -> None:
    """100 seeded positions → serialize → parse → equal."""
    rng = random.Random(seed)
    n = rng.randint(0, 50)  # 0..50 pieces — covers empty, sparse, dense-ish
    pos = _seeded_random_position(rng, n)
    s = fen_4d.serialize(pos)
    re_parsed = fen_4d.parse(s)
    assert re_parsed == pos, f"seed={seed}, n={n}: pos={pos}, got={re_parsed}"


# ─── Canonical-form invariants ────────────────────────────────────

def test_serialize_is_canonical() -> None:
    """Two positions equal as dicts (regardless of insertion order)
    serialize to bit-identical strings, because serialize sorts by
    ascending square index."""
    a = {3: "K", 1: "Q", 5: "R"}
    b = {5: "R", 1: "Q", 3: "K"}
    assert fen_4d.serialize(a) == fen_4d.serialize(b)


# ─── Malformed-input rejection by serialize ───────────────────────

def test_serialize_rejects_out_of_range_square() -> None:
    with pytest.raises(ValueError, match="out of range"):
        fen_4d.serialize({4096: "K"})


def test_serialize_rejects_negative_square() -> None:
    with pytest.raises(ValueError, match="out of range"):
        fen_4d.serialize({-1: "K"})


def test_serialize_rejects_unknown_piece_letter() -> None:
    with pytest.raises(ValueError, match="non-pawn value"):
        fen_4d.serialize({0: "X"})


def test_serialize_rejects_pawn_with_bad_axis() -> None:
    with pytest.raises(ValueError, match="axis"):
        fen_4d.serialize({0: ("P", "z")})  # z-axis pawn forbidden


def test_serialize_rejects_pawn_with_bad_color() -> None:
    with pytest.raises(ValueError, match="color"):
        fen_4d.serialize({0: ("X", "w")})


def test_serialize_rejects_malformed_pawn_tuple() -> None:
    with pytest.raises(ValueError, match="2-tuple"):
        fen_4d.serialize({0: ("P",)})


def test_serialize_rejects_unsupported_value_type() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        fen_4d.serialize({0: 42})  # type: ignore[dict-item]


# ─── Direct invocation ─────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"],
                   check=False)
