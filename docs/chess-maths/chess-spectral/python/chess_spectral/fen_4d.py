"""FEN4 v1 placement-literal parser. See docs/FEN4_FORMAT.md for the
grammar.

The parser produces a position dict in the format consumed by
:func:`chess_spectral.encoder_4d.encode_4d` —
``{int_square: piece_value}`` where ``piece_value`` is either a single
character (non-pawns) or a ``(color, axis)`` tuple (pawns).

Parity contract: the C parser in ``src/cs_fen_4d.c`` must accept the
same set of inputs (and reject the same set), and produce a position
that round-trips to the same encoding bytes. Verified by
``python/tests/test_fen4_parity.py``.

Errors raise :class:`Fen4ParseError`. Error codes mirror the C parser
(see :class:`Fen4ParseError.code` and the ``CODE_*`` constants).
"""
from __future__ import annotations

from typing import Dict, Tuple, Union

PieceValue = Union[str, Tuple[str, str]]
"""Either a 1-char piece name (non-pawn) or a (color, axis) pair (pawn)."""

PREFIX = "4d-fen v1:"
"""Mandatory version-tagged prefix."""

# Error codes — magnitudes match cs_fen_4d.h so cross-language tests can
# assert on the same numeric value.
CODE_NULL = -1
CODE_BAD_PREFIX = -2
CODE_BAD_PIECE = -3
CODE_BAD_COORD = -4
CODE_DUPLICATE = -5
CODE_TRAILING = -6


class Fen4ParseError(ValueError):
    """Raised when a FEN4 string fails to parse.

    Attributes
    ----------
    code : int
        Negative integer matching the C parser's return value (see
        ``CODE_*`` module constants).
    offset : int
        Byte offset into the input where the error was detected.
    """
    def __init__(self, code: int, offset: int, msg: str):
        super().__init__(f"FEN4 parse error at offset {offset}: {msg}")
        self.code = code
        self.offset = offset


# ─── Internal helpers ───────────────────────────────────────────────────


_NON_PAWN_WHITE = frozenset("NBRQK")
_NON_PAWN_BLACK = frozenset("nbrqk")
_NON_PAWN = _NON_PAWN_WHITE | _NON_PAWN_BLACK
_AXIS_LETTERS = frozenset("wy")


def _is_ws(c: str) -> bool:
    return c in (" ", "\t", "\n", "\r")


def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and _is_ws(s[i]):
        i += 1
    return i


def _parse_coord(s: str, i: int) -> Tuple[Tuple[int, int, int, int], int]:
    """Parse "x,y,z,w" starting at i. Returns (coord, new_index)."""
    out = [0, 0, 0, 0]
    for k in range(4):
        if i >= len(s) or not ('0' <= s[i] <= '7'):
            raise Fen4ParseError(CODE_BAD_COORD, i,
                                 f"expected digit 0-7, got {s[i:i+1]!r}")
        out[k] = int(s[i])
        i += 1
        if k < 3:
            if i >= len(s) or s[i] != ',':
                raise Fen4ParseError(CODE_BAD_COORD, i,
                                     f"expected ',' between coord digits, "
                                     f"got {s[i:i+1]!r}")
            i += 1
    return (out[0], out[1], out[2], out[3]), i


def _parse_piece_spec(s: str, i: int) -> Tuple[PieceValue, int]:
    """Parse a piece spec starting at i. Returns (value, new_index).

    1.7.1+: accepts an *optional* ``'/'`` separator between the pawn
    color char and its axis letter. Both ``Pw@...`` (canonical) and
    ``P/w@...`` (slash-separated) parse to the same value. The slash
    form is more readable for humans hand-authoring FEN4 strings —
    a reasonable accommodation, mirroring chess.com / lichess's
    tolerance of common syntactic variations in FEN. The serializer
    in :func:`serialize` continues to emit the canonical no-slash
    form, so round-tripping a ``P/w@``-input preserves the slash-
    less representation on output.
    """
    if i >= len(s):
        raise Fen4ParseError(CODE_BAD_PIECE, i,
                             "expected piece spec, got end-of-input")
    c = s[i]
    # Pawns: must carry an axis suffix, optionally preceded by '/'.
    if c == 'P' or c == 'p':
        # Skip an optional '/' separator. This is the 1.7.1
        # tolerance — pre-1.7.1 a literal 'P/w@...' raised
        # CODE_BAD_PIECE on the slash since we read s[i+1] directly.
        axis_idx = i + 1
        if axis_idx < len(s) and s[axis_idx] == '/':
            axis_idx += 1
        if axis_idx >= len(s) or s[axis_idx] not in _AXIS_LETTERS:
            raise Fen4ParseError(CODE_BAD_PIECE, i,
                                 f"pawn {c!r} must be followed by axis "
                                 f"letter ('w' or 'y'), optionally with "
                                 f"a leading '/' separator; got "
                                 f"{s[i+1:axis_idx+1]!r}")
        return (c, s[axis_idx]), axis_idx + 1
    # Non-pawn pieces: single char.
    if c in _NON_PAWN:
        return c, i + 1
    raise Fen4ParseError(CODE_BAD_PIECE, i,
                         f"unknown piece spec {c!r}")


# ─── Public API ─────────────────────────────────────────────────────────


def parse(fen4: str) -> Dict[int, PieceValue]:
    """Parse a FEN4 v1 placement literal into a position dict.

    The returned dict maps each occupied square's integer index
    (``((x*8+y)*8+z)*8+w``) to a piece value: single-char string for
    non-pawns, ``(color, axis)`` tuple for pawns.

    Empty boards return an empty dict.

    Raises
    ------
    Fen4ParseError
        If the input is missing the prefix, contains a malformed piece
        spec or coordinate, declares two pieces on the same square, or
        has trailing garbage after the piece list.
    """
    if fen4 is None:
        raise Fen4ParseError(CODE_NULL, 0, "input is None")

    s = fen4
    i = _skip_ws(s, 0)

    if not s.startswith(PREFIX, i):
        raise Fen4ParseError(CODE_BAD_PREFIX, i,
                             f"missing {PREFIX!r} prefix")
    i += len(PREFIX)
    i = _skip_ws(s, i)

    pos: Dict[int, PieceValue] = {}
    if i >= len(s):
        return pos  # empty board

    while True:
        value, i = _parse_piece_spec(s, i)
        i = _skip_ws(s, i)

        if i >= len(s) or s[i] != '@':
            raise Fen4ParseError(CODE_BAD_PIECE, i,
                                 f"expected '@' after piece spec, got "
                                 f"{s[i:i+1]!r}")
        i += 1
        i = _skip_ws(s, i)

        coord, i = _parse_coord(s, i)
        x, y, z, w = coord
        sq = ((x * 8 + y) * 8 + z) * 8 + w
        if sq in pos:
            raise Fen4ParseError(CODE_DUPLICATE, i,
                                 f"duplicate square ({x},{y},{z},{w})")
        pos[sq] = value

        i = _skip_ws(s, i)
        if i >= len(s):
            return pos
        if s[i] != ';':
            raise Fen4ParseError(CODE_TRAILING, i,
                                 f"expected ';' or end-of-input, got "
                                 f"{s[i:i+1]!r}")
        i += 1
        i = _skip_ws(s, i)
        if i >= len(s):
            return pos  # trailing ';' is permitted


def serialize(pos: Dict[int, PieceValue]) -> str:
    """Serialize a position dict back to a FEN4 v1 placement literal.

    Inverse of :func:`parse`. The round-trip property holds for any
    valid position::

        parse(serialize(p)) == p

    The produced output is canonical: pieces are emitted in ascending
    square-index order, separated by ``"; "`` (a semicolon followed by
    a single space). Empty positions serialize to just the prefix
    string ``"4d-fen v1:"``.

    Parameters
    ----------
    pos
        Position dict as produced by :func:`parse` — keys are linear
        square indices (``((x*8+y)*8+z)*8+w``), values are either a
        single-character piece string (non-pawns) or a ``(color, axis)``
        tuple (pawns; ``color`` ∈ ``{'P', 'p'}``, ``axis`` ∈ ``{'w',
        'y'}``).

    Returns
    -------
    str
        A valid FEN4 v1 placement literal accepted by :func:`parse`.

    Raises
    ------
    ValueError
        If a square index is out of range ``[0, 4096)``, a piece value
        is malformed, or a pawn carries an invalid axis.
    """
    if not pos:
        return PREFIX
    parts: list[str] = []
    for sq in sorted(pos.keys()):
        if not isinstance(sq, int) or sq < 0 or sq >= 4096:
            raise ValueError(
                f"square index {sq!r} out of range [0, 4096)"
            )
        value = pos[sq]
        # decode square back to (x, y, z, w)
        w = sq % 8
        z = (sq // 8) % 8
        y = (sq // 64) % 8
        x = (sq // 512) % 8

        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError(
                    f"pawn value at square {sq} must be a 2-tuple, "
                    f"got {value!r}"
                )
            color, axis = value
            if color not in ("P", "p"):
                raise ValueError(
                    f"pawn color at square {sq} must be 'P' or 'p', "
                    f"got {color!r}"
                )
            if axis not in _AXIS_LETTERS:
                raise ValueError(
                    f"pawn axis at square {sq} must be 'w' or 'y', "
                    f"got {axis!r}"
                )
            piece_str = f"{color}{axis}"
        elif isinstance(value, str):
            if value not in _NON_PAWN:
                raise ValueError(
                    f"non-pawn value at square {sq} must be one of "
                    f"{sorted(_NON_PAWN)}, got {value!r}"
                )
            piece_str = value
        else:
            raise ValueError(
                f"unsupported piece value type at square {sq}: "
                f"{type(value).__name__}"
            )
        parts.append(f"{piece_str}@{x},{y},{z},{w}")
    return f"{PREFIX} " + "; ".join(parts)


def parse_to_jsonl_obj(fen4: str) -> Dict[str, str]:
    """Parse a FEN4 string and return the JSONL fixture-style ``"pieces"``
    object — keys are stringified square indices, values are 1-char
    pieces (non-pawns) or 2-char ``color+axis`` strings (pawns).

    This is the format consumed by ``spectral_4d encode-fixture`` /
    ``parse_pieces_object`` in ``src/main_4d.c``. Useful for round-trip
    fixtures and for callers that prefer to invoke the existing
    fixture-encode path.
    """
    out: Dict[str, str] = {}
    for sq, value in parse(fen4).items():
        if isinstance(value, tuple):
            color, axis = value
            out[str(sq)] = color + axis
        else:
            out[str(sq)] = value
    return out
