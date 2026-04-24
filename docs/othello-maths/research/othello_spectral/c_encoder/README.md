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

## Build (once stubs are filled in)

```
cd docs/othello-maths/research/othello_spectral

# 1. Generate the tables header (creates include/othello_spectral_tables.h).
python -m othello_spectral.codegen.emit_c_tables

# 2. Compile.
cc -std=c17 -Wall -Wextra -O2 -I c_encoder/include \
   c_encoder/src/othello_spectral.c \
   -o c_encoder/othello_spectral_reference
```

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
