# chess_spectral (Python)

Python reference implementation of the 640-dim (2D) and 45 056-dim (4D)
spectral chess encoders, sibling of the C17 port in `../src/`. Use this
for REPL / LLM / notebook analysis; use the C binary for batch throughput.

## Install

From PyPI (recommended):

```bash
pip install chess-spectral
```

The base install pulls only `numpy` and `scipy`. If you need PGN ingest
via `chess_spectral.corpus`, request the `[corpus]` extra to add
`python-chess`:

```bash
pip install "chess-spectral[corpus]"
```

Package page: <https://pypi.org/project/chess-spectral/>

### From source

Editable install from a local checkout:

```bash
pip install -e docs/chess-maths/chess-spectral/python/
```

From a git URL (pin a commit in production):

```bash
pip install "git+https://github.com/lemonforest/mlehaptics.git@COMMIT#subdirectory=docs/chess-maths/chess-spectral/python"
```

After install, two console scripts are on your `$PATH`:

```bash
chess-spectral --help            # 2D CLI (formerly `python spectral_py.py`)
chess-spectral-4d --help         # 4D CLI
```

Both packages also expose `__version__`:

```python
>>> import chess_spectral, chess_spectral_4d
>>> chess_spectral.__version__, chess_spectral_4d.__version__
('1.1.3', '1.1.3')
```

### In-place (no install)

The legacy workflow still works: every test and analysis script uses
`sys.path.insert` to bootstrap off the `python/` directory, so
`pytest docs/chess-maths/chess-spectral/python/tests/` runs without any
install.

Output is **byte-identical** to the C CLI — the `spectral csv` command
here produces the same bytes as the C `spectral csv` does on the same
input file. The Python CLI (`chess-spectral`, entry point
`chess_spectral.cli:main`) mirrors the C CLI subcommand-for-subcommand.

## Layout

    chess_spectral/
      encoder.py             # encode_640(pos) → np.ndarray(640,)
      frame.py               # v2 .spectral[z] binary I/O + transparent gzip
      csv_export.py          # dist_prev / cos_prev / energies CSV
      cli.py                 # `chess-spectral csv file.spectralz` (2D CLI)
      phase_operators/       # §11 phase-space move generator + is_check (1.2.0+)
    chess_spectral_4d/
      cli.py                 # `chess-spectral-4d tables-verify --phase all`
    pyproject.toml           # PEP 621 packaging metadata
    tests/
      test_parity.py         # Python output == C output (5 tests)
      phase_operators/       # §11 validation suite (92 tests; 1.2.0+)

## Quick start

```python
>>> from chess_spectral import (
...     encode_640, channel_energies, read_encodings, fen_to_pos,
... )

>>> pos = fen_to_pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
>>> enc = encode_640(pos)
>>> enc.shape
(640,)

>>> channel_energies(enc)
{'A1': 0.0, 'A2': 19.845, 'B1': 45.2825, 'B2': 45.2825,
 'E': 322.57, 'F1': 88.77, 'F2': 1851.01, 'F3': 1507.65,
 'FA': 19.92, 'FD': 0.0}

# Read a whole game that was encoded by either C or Python
>>> hdr, arr = read_encodings("game.spectralz")  # transparent gzip
>>> arr.shape
(161, 640)
```

## CLI

    python spectral_py.py csv        game.spectralz -o game.csv
    python spectral_py.py encode     -i game.ndjson -o game.spectralz -z
    python spectral_py.py encode-fen --fen "..."   -o single.spectral
    python spectral_py.py version

## Phase operators (§11)

`chess_spectral` ships a phase-space move generator and check
detector as the `chess_spectral.phase_operators` subpackage (added
in 1.2.0). The primitives compute all moves and check relationships
as modular arithmetic on a single integer per square —
`phi(r, c) = r·67 + c·7 mod 640` — rather than geometric
coordinates. They are a drop-in equivalent to python-chess's
`pseudo_legal_moves` + `is_check`, validated at 100% on the reference
corpus, and compose naturally with the spectral encoder's coprime
phase structure.

```python
import chess
from chess_spectral.phase_operators import (
    occupation_aware_moves_c,   # pseudo-legal dests from a square
    available_castles,          # legal castles for side-to-move
    phasecast_is_check,         # is the mover's king attacked?
    move_leaves_king_in_check,  # would this move expose our king?
)

board = chess.Board()

# Pseudo-legal destinations for the knight on b1 (the 1,2 indexed
# from bottom-left: row 0, col 1). mover_charge is +1 for white.
dests = occupation_aware_moves_c(board, "N", 0, 1, +1)
# -> frozenset({(2, 0), (2, 2)})   (a3 and c3)

# Check detection
phasecast_is_check(board)  # False on the starting position
```

Validation coverage (see
[PHASE_OPERATOR_SUPPLEMENT.md](https://github.com/lemonforest/mlehaptics/blob/main/docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md)
for the full research record):

- Empty-board pseudo-legal destinations for every piece type at
  every square — 416 / 416 pairs (§11.3).
- Occupation-aware pseudo-legal moves including en passant and
  castling — 1153 / 1153 at n=100 positions (§11.4).
- `is_check` on arbitrary pseudo-legal transitions — 3393 / 3393
  (§11.5 path 1).

### When to use phase operators vs python-chess

Both give you the same answers. The phase-space formulation is
faster than python-chess's `pseudo_legal_moves` in pure Python
(~7 µs/piece for the fastest solution vs ~15–20 µs for python-chess's
equivalent), and slower than python-chess's bitboard `is_check`
(`phasecast_is_check` runs ~138 µs vs ~22 µs for python-chess). The
subpackage exists because the phase-space formulation is the
substrate the §11/§12 spectral research is built on — not because
it universally out-performs python-chess. If you're writing a search
engine hot loop, python-chess's bitboards are the right choice. If
you're doing phase-space research (similarity, partition detection,
encoder composition) or need the operators as primitives in C via a
future codegen port, the subpackage is the right choice.

## Parity with C

The encoder uses the same tables (`PAWN_ANTI_FIBER`, `DIAG_DEV`) as the
codegen that feeds the C side. Tables are rebuilt at import time from
`encoder_512` primitives plus the directed pawn adjacency from
`chess_pawn_laplacian` — so both implementations can be verified from
first principles.

Run the parity suite:

    python tests/test_parity.py

The critical test is `test_csv_matches_c_byte_for_byte` — reads the C-
produced `.spectral` file, runs the Python CSV exporter, asserts the
output equals the C CSV bit-for-bit.

## Why two implementations

| | C | Python |
|--|--|--|
| Throughput | µs/encode | ms/encode |
| REPL / notebooks | ✗ | ✓ |
| LLM-pasteable | binary | code |
| Scipy / numpy exploration | ✗ | ✓ |
| Embeds in mobile / web | ✓ | ✗ |
| Exact numerical reference | tables baked at build | rebuilt from primitives |

Develop new channels in Python first (faster iteration, `scipy.linalg`
at hand, no rebuild loop). Once the math is frozen, port to C and
verify parity via the test suite.
