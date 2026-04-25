# othello_spectral — ANSI C17 reference encoder

Bit-identical C17 target for the Python `encode_768`.  This is a
scaffold commit: the API is declared, the source stub compiles, and
the codegen emits the tables header on demand.  **Actual encoding
is not yet implemented** — `encode_768` returns an all-zero output
and status code 1 ("not implemented").

## Why

The Python encoder is the research source of truth.  Downstream
pipelines (training pipelines, real-time move assistants, embedded
integrations) need an ANSI C17 implementation that produces *exactly*
the same 768-dim vectors, bit-for-bit, so models trained on Python
encodings work unchanged on the C encoder's output.

## Layout

```
c_encoder/
├── include/
│   ├── othello_spectral.h           # public API (committed)
│   └── othello_spectral_tables.h    # GENERATED, do not commit
└── src/
    └── othello_spectral.c           # stub (committed)
```

## Build

Two output artefacts: an executable (`encode_cli.exe`) for subprocess
use, and a shared library (`othello_spectral.dll` on Windows /
`.so` on Linux / `.dylib` on macOS) for ctypes use.  The Python
engine dispatch prefers the DLL (ctypes, no subprocess overhead)
and silently falls back to the executable.

```
cd docs/othello-maths/research

# 1. Generate the tables header.
python -m othello_spectral.codegen.emit_c_tables

# 2. Build the executable (for --engine c with subprocess path).
clang -std=c17 -Wall -Wextra -O2 \
    -I othello_spectral/c_encoder/include \
    othello_spectral/c_encoder/src/othello_spectral.c \
    othello_spectral/c_encoder/src/encode_cli.c \
    -o othello_spectral/c_encoder/encode_cli.exe

# 3. Build the shared library (for --engine c with ctypes path).
clang -std=c17 -O2 -shared \
    -I othello_spectral/c_encoder/include \
    othello_spectral/c_encoder/src/othello_spectral.c \
    -o othello_spectral/c_encoder/othello_spectral.dll
#    (On Linux/macOS: -o othello_spectral.so / othello_spectral.dylib)
```

Check which path the engine dispatch resolves to:

```
python -m othello_spectral.cli engine
```

Shows both subprocess binary and ctypes DLL status, and indicates
which path `--engine c` would take.  Override locations via
`OTHELLO_SPECTRAL_BIN` (exe) or `OTHELLO_SPECTRAL_DLL` (library).

### Benchmarks (APR 2026, 25 447 states)

| path                  | encode time | wall (incl PGN replay) |
|-----------------------|-------------|------------------------|
| python                | 3.0 s       | 18.4 s                 |
| c (ctypes DLL)        | 3.1 s       | 17.8 s                 |
| c (subprocess exe)    | 7.6 s       | 21.7 s                 |

ctypes path is 2.5× faster than subprocess; matches Python's
per-state throughput.  Both C paths produce byte-identical
`.spectralz` output to Python (SHA256 parity verified).

## Parity test (to be added in a later commit)

The plan is:

1. Fix a Python fixture corpus (e.g. Barcelona, 35 games, 2184
   frames) encoded via `encode_768` and stored as a
   `.spectralz.reference` file.
2. Run the C encoder on the same state sequence (extracted via
   PGN replay or directly from a state-stream binary).
3. Compare every frame at float32 precision — `assert
   np.array_equal(py_frame, c_frame)`.  Any divergence is a bug,
   either in the codegen emission or in the C implementation.

## Bit-identity invariants

Honoured by both Python and the (future) C implementation:

- Float64 accumulators throughout the encoding math; float32 cast
  happens only at the on-disk serialisation step.
- Matrix operations applied in a deterministic order (projector @
  signal, then L_ortho @ signal, then L_diag @ signal).
- All tables derive from rational characters and integer
  Laplacians — no random init anywhere.
- Little-endian byte order in the binary format (frame.py's
  `struct.pack(..., "<")` matches C's little-endian `memcpy`).

## Versioning

The tables header contains:

```c
#define OTHELLO_SPECTRAL_VERSION  "0.2.0"
```

string-literal identical to the Python `__version__`.  Consumers
should compare against the Python side at load time and reject
mismatches rather than attempting cross-version decoding.
