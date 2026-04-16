# chess_spectral (Python)

Python reference implementation of the 640-dim spectral chess encoder,
sibling of the C17 port in `../src/`. Use this for REPL / LLM / notebook
analysis; use the C binary for batch throughput.

Output is **byte-identical** to the C CLI — the `spectral csv` command
here produces the same bytes as the C `spectral csv` does on the same
input file. The Python CLI (`spectral_py.py`) mirrors the C CLI
subcommand-for-subcommand.

## Layout

    chess_spectral/
      encoder.py       # encode_640(pos) → np.ndarray(640,)
      frame.py         # v2 .spectral[z] binary I/O + transparent gzip
      csv_export.py    # dist_prev / cos_prev / energies CSV
    spectral_py.py     # CLI: `python spectral_py.py csv file.spectralz`
    tests/
      test_parity.py   # Python output == C output (5 tests)

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
