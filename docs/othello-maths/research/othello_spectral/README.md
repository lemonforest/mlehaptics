# othello_spectral

D₄ × Z₂ spectral encoder for Othello positions.  Partner package to
[chess-spectral](../../../chess-maths/chess-spectral/).  Emits a
768-dim float64 vector per position; the on-disk binary format uses
little-endian float32 and is designed to be bit-identical to a
future ANSI C17 reference encoder.

## Install

```bash
cd docs/othello-maths/research/othello_spectral
pip install -e .
```

## Quick start

```python
import numpy as np
from othello_spectral import encode_768, channel_energies, CHANNEL_NAMES

# World-frame Blume-Capel signal: +1 = black, -1 = white, 0 = empty.
state = np.zeros(64, dtype=int)
state[3 * 8 + 3] = -1  # d4 white
state[3 * 8 + 4] = +1  # e4 black
state[4 * 8 + 3] = +1  # d5 black
state[4 * 8 + 4] = -1  # e5 white

enc = encode_768(state)           # shape (768,) float64
en  = channel_energies(enc)        # {channel_name: ||block||^2}
```

## CLI

```bash
python -m othello_spectral.cli version
python -m othello_spectral.cli channels
python -m othello_spectral.cli encode-obf '---------...-X---...XO- X;'
python -m othello_spectral.cli encode-pgn path/to/games.pgn \
    --out out.spectralz
```

## Encoder layout (v0.3.0, D=768, sheaf-fiber default)

| dims        | channel                | source signal                              |
|-------------|------------------------|--------------------------------------------|
| [  0: 64)   | magn_A1minus           | magnetisation s                             |
| [ 64:128)   | magn_A2minus           | magnetisation s                             |
| [128:192)   | magn_B1minus           | magnetisation s                             |
| [192:256)   | magn_B2minus           | magnetisation s                             |
| [256:320)   | magn_Eminus            | magnetisation s                             |
| [320:384)   | occ_A1plus             | occupation s²                               |
| [384:448)   | occ_A2plus             | occupation s²                               |
| [448:512)   | occ_B1plus             | occupation s²                               |
| [512:576)   | occ_B2plus             | occupation s²                               |
| [576:640)   | occ_Eplus              | occupation s²                               |
| [640:704)   | **sheaf_pending_black**| per-cell R3 pending-bracket count, black    |
| [704:768)   | **sheaf_pending_white**| per-cell R3 pending-bracket count, white    |

v0.3.0 replaces the v0.2.0 rank-2 orbit-Laplacian fiber
(`fiber_ortho_s`, `fiber_diag_s`) with sheaf-derived per-cell
pending-bracket counts.  The new channels encode active flank
structure and give ~40 % stronger correlation with Takizawa's
proved `archive_mean_lb` than the previous occupation channels
(partial ρ −0.447 vs −0.319 for A1 on 2587 positions).

The v0.2.0 geometric fiber is still available via
`encode_768(state, fiber_mode="rank2")` — and is the mode the
current C reference encoder supports.  The C port of the sheaf
bracket walker is a future item.

## Binary format (.spectralz)

256-byte header + N × 772-byte frames (768 float32 + 1 uint32 ply).
All fields little-endian, explicit `struct.pack` layout.  See
[`frame.py`](./frame.py) for the full specification.

## Versioning and C parity

- Package version is stored in `VERSION`; Python reads it via
  `othello_spectral.__version__`, codegen emits it into the C header.
- All tables are rational character matrices + integer-entry
  Laplacians — no random init, no floating-point roundoff path that
  would differ between Python and C.
- 10/10 smoke tests pass (`python -m othello_spectral.tests.test_encoder_sanity`;
  `python -m othello_spectral.tests.test_encoder_invariance`).

## Layout

```
othello_spectral/
├── VERSION                # semver, single source of truth
├── __init__.py            # public API, reads VERSION
├── tables.py              # precomputed projectors + orbit Laplacians
├── encoder.py             # encode_768
├── frame.py               # .spectralz binary format
├── cli.py                 # command-line entry
├── pyproject.toml         # packaging metadata
├── README.md              # this file
├── tests/
│   ├── test_encoder_sanity.py
│   └── test_encoder_invariance.py
├── codegen/               # Python -> C table emitter (stubbed)
│   └── emit_c_tables.py
└── c_encoder/             # ANSI C17 reference implementation (stubbed)
    ├── README.md
    ├── include/
    │   └── othello_spectral.h
    └── src/
        └── othello_spectral.c
```

## License

GPL-3.0-or-later (matches parent project).
