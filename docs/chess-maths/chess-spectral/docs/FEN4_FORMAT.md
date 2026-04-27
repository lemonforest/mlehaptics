# FEN4 — 4D position literal format

**Version:** v1
**Status:** Stable for v1; new features go in v2 (parser dispatches on prefix)
**Used by:** `spectral_4d encode-fen4`, `chess-spectral-4d encode-fen4`

---

## Why a new format

Standard FEN encodes 8×8 = 64 squares using row-by-row run-length notation
(`rnbqkbnr/...`). The 4D encoder operates on Z₈⁴ = 4096 squares — 64 times
larger than 2D. Run-length over a 4D lattice is unreadable, so FEN4 uses
explicit `(x, y, z, w)` coordinates per piece.

FEN4 is **placement-only**: there is no side-to-move, castling, en-passant,
or move clock. The 4D encoder is positional; downstream move replay (in
NDJSON4) carries any move-history state.

---

## Grammar (EBNF)

```
fen4_v1     = "4d-fen" ws "v1:" ws? piece_list ws?
piece_list  = (piece (ws? ";" ws? piece)* (ws? ";")?)?    (* may be empty *)
piece       = piece_spec "@" coord
piece_spec  = non_pawn | pawn
non_pawn    = "N" | "B" | "R" | "Q" | "K"               (* white *)
            | "n" | "b" | "r" | "q" | "k"               (* black *)
pawn        = white_pawn | black_pawn
white_pawn  = "P" axis
black_pawn  = "p" axis
axis        = "w" | "y"                                 (* W- or Y-axis *)
coord       = digit "," digit "," digit "," digit       (* x,y,z,w each in [0,7] *)
digit       = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7"
ws          = (" " | "\t" | "\n" | "\r")+
```

No whitespace is permitted **inside** a `piece_spec` or **inside** a `coord`
(i.e. between coordinate digits). Whitespace is permitted between tokens
and around the `@`, `;`, and version prefix.

---

## Examples

### Empty board
```
4d-fen v1:
```

### Two kings only
```
4d-fen v1: K@0,0,0,0; k@7,7,7,7
```

### Mixed position with pawns
```
4d-fen v1: K@4,0,0,0; k@4,7,7,7;
            Pw@0,1,0,0; Pw@1,1,0,0; Py@0,0,1,1;
            py@7,6,7,7; n@3,3,3,3; B@2,2,2,2
```

### Multi-line (whitespace tolerant)
```
4d-fen v1:
    K @ 0,0,0,0 ;
    k @ 7,7,7,7 ;
    Pw @ 0,1,0,0 ;
```

---

## Piece-spec encoding

| Spec | Color | Type   | Pawn axis |
|------|-------|--------|-----------|
| `N`  | white | knight | —         |
| `B`  | white | bishop | —         |
| `R`  | white | rook   | —         |
| `Q`  | white | queen  | —         |
| `K`  | white | king   | —         |
| `n`  | black | knight | —         |
| `b`  | black | bishop | —         |
| `r`  | black | rook   | —         |
| `q`  | black | queen  | —         |
| `k`  | black | king   | —         |
| `Pw` | white | pawn   | W-axis    |
| `Py` | white | pawn   | Y-axis    |
| `pw` | black | pawn   | W-axis    |
| `py` | black | pawn   | Y-axis    |

**Pawn axis rationale:** Per Oana & Chiru §3 (AppliedMath 6(3):48, 2026),
pawns in 4D advance along one of two privileged axes (W or Y). The Z-axis
is forbidden. FEN4 v1 enforces this by requiring `w` or `y` in every pawn
spec; bare `P` or `p` (without an axis suffix) is rejected.

---

## Square coordinate convention

The 4D board is Z₈⁴. Coordinates `(x, y, z, w)` each lie in `[0, 7]`. The
linear square index used by the encoder is row-major with `x` slowest-varying:

```
sq4(x, y, z, w) = ((x * 8 + y) * 8 + z) * 8 + w
```

So `sq4(0, 0, 0, 0) == 0` and `sq4(7, 7, 7, 7) == 4095`.

This matches the `cs_position_4d_t.sq[]` and `pawn_axis[]` indexing in
[include/cs_types_4d.h](../include/cs_types_4d.h) and the `sq4()` helper in
[python/chess_spectral/tables_4d.py](../python/chess_spectral/tables_4d.py).

---

## Errors

A FEN4 string is **invalid** (parse rejected with non-zero exit) if any of:

- Missing `4d-fen v1:` prefix
- Coordinate digit outside `[0, 7]`
- Coordinate group has fewer or more than four digits
- Two pieces share the same square
- Pawn spec lacks an axis suffix (`P` or `p` without `w`/`y`)
- Unknown axis letter (anything other than `w` or `y` for pawns)
- Unknown piece letter
- Malformed token (missing `@`, missing `;` between specs, etc.)

The C and Python parsers MUST agree on which inputs are valid; this is
covered by [tests/test_fen4_parity.py](../python/tests/test_fen4_parity.py).

---

## Versioning

Future revisions bump the prefix: `4d-fen v2: ...`. Parsers dispatch on
the version tag; v1 readers must reject v2 input rather than silently
mis-parsing. This keeps fixtures reproducible across schema evolution.
