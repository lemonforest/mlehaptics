# `chess_spectral.qm_4d_bridge` — v1.5 Pyodide bridge API

**Version:** v1.5 (chess-spectral ≥ 1.5.0)
**Status:** Stable for v1.5; v1.7+ adds the deferred density-matrix /
per-piece-marginal methods (currently `NotImplementedError`).
**Audience:** chess4D-OC and other Pyodide consumers building against
the §17.1 / §17.5 method set.

This document is the **API contract**. The research narrative behind
each method (why these exist, what design choices led here) lives in
[`chess_spectral_research_notebook.md` §17](../../chess_spectral_research_notebook.md);
the technical decisions are recorded as
[ADRs in `docs/adr/qm_4d/`](adr/qm_4d/README.md). Both are linked
inline below.

---

## Overview

`chess_spectral.qm_4d_bridge` is the consumer-facing Pyodide bridge:
13 methods exposed as plain Python callables that return Pyodide-
JSON-serializable dicts. Each return dict carries an `'ok'` key
(always `True` for valid input; failures raise rather than returning
`{'ok': False}`).

**Shape of the surface** (numbered per the research notebook):

- **§17.1 — 7 QM-extension methods.** Drive the M14.x visualization
  and the v1.6+ engine evaluator. All read-only on the underlying
  classical state except `apply_move_qm` / `apply_move_qm_full`.
- **§17.5 — 6 dev / debug methods.** Version, encoder shape, FEN4
  round-trip, fixture loading, legal-move query.

**The heterogeneous-dispatch contract.** `apply_move_qm` returns a
per-channel dict whose values are a mix of `csr_matrix` and plain
Python dicts ("marker dicts"). This is intentional — different
channels have different mathematical types under a move (strict-
unitary, partial-isometry, measurement-only re-encode, rank-1
update). Consumers either dispatch on `isinstance(value, dict)` and
handle each case, or call `apply_move_qm_full` which does the
dispatch and returns an assembled `ψ_post`.

For most consumers `apply_move_qm_full` is the right entry point;
`apply_move_qm` is exposed for downstream code that needs the raw
per-channel structure (e.g., to render per-channel diagnostics).

**The `ComplexArray` wire format.** Every ψ-returning method
serializes the complex amplitude as **real+imag interleaved Float32**:
a 1-D `Float32` array of length `2 × 45056 = 90112`, where
`psi[2k] = Re(ψ_k)` and `psi[2k+1] = Im(ψ_k)`. The chess4D-OC
M14.x WebGL renderer reads this directly into a `Float32Array` for
shader uniforms / texture upload — no JS-side conversion needed.

The helper [`complex_to_interleaved_float32`](#helpers) exposes this
serialization for consumers that need to apply it themselves.

---

## §17.1 QM-extension surface (7 methods)

### `get_qm_state`

```python
def get_qm_state(state, *, side_to_move=True) -> dict
```

Drives M14.1 raw-amplitude render, M14.2 phase-as-color, M14.3
trajectory replay.

**Parameters.**

- `state` — position dict `{sq_int: piece_value}` or any object with
  a `.position` attribute (e.g.,
  [`chess_spectral_4d.GameState4D`](../python/chess_spectral_4d/__init__.py)).
- `side_to_move: bool` — `True` = white-to-move (default), `False` =
  black-to-move. Controls the Z_2 superselection sign on ψ per
  [ADR-004](adr/qm_4d/ADR-004-z2-superselection-structure.md).

**Returns.** Dict with:

- `ok: bool` — always `True` for valid input.
- `psi: ndarray[float32, (90112,)]` — `ComplexArray` (real+imag
  interleaved Float32). For cell `c` of channel `i` the amplitude is
  `psi[2*(i*4096+c)] + 1j*psi[2*(i*4096+c)+1]`.
- `basisDim: int` — always `45056`.
- `normSq: float` — `⟨ψ|ψ⟩`. Equals `1.0` within float rounding for
  any non-empty position; `0.0` for the empty-position sentinel.

**Edge cases.**

- **Empty position** (`state == {}` or `pos == {}`): returns ψ = 0,
  `normSq = 0.0`. The M14.x renderer should skip rendering in this
  case (no amplitude to display).
- **Single-piece position:** ψ is normalized; `normSq ≈ 1.0`.
- **Position-of-collision** (the 8 anti-podal-king + diagonal-piece
  cases from Pre-flight 1): the side-to-move sign distinguishes
  pre-collision pairs. ψ is well-defined in both sectors.

**Example.**

```python
>>> from chess_spectral.qm_4d_bridge import get_qm_state
>>> from chess_spectral.fen_4d import parse
>>> pos = parse("4d-fen v1: K@4,0,0,0; k@4,7,7,7; R@0,0,0,0")
>>> r = get_qm_state(pos, side_to_move=True)
>>> r['basisDim'], r['psi'].shape, r['psi'].dtype
(45056, (90112,), dtype('float32'))
>>> abs(r['normSq'] - 1.0) < 1e-6
True
```

---

### `get_qm_density`

```python
def get_qm_density(state, piece_id=None, *, side_to_move=True) -> dict
```

`|ψ|²` per cell on the 4096-cell lattice. Drives M14.1 full-position
amplitude render.

**Parameters.**

- `state` — position dict or object with `.position`.
- `piece_id: int, optional` — if given, requests a per-piece
  marginal. **Currently raises `NotImplementedError`; deferred to
  v1.7+.**
- `side_to_move` — forwarded to `state_to_psi`.

**Returns.** Dict with:

- `ok: bool`.
- `density: ndarray[float32, (4096,)]` — `Σ_chan |ψ_chan(cell)|²` for
  each cell. For a normalized ψ, `density.sum() ≈ 1.0`.

**Raises.**

- `NotImplementedError` if `piece_id is not None` — the per-piece
  marginal needs a partial-trace operator over channel labels and a
  channel-to-piece attribution map (the encoder's bilinear FIB / FD
  / FA channels make the attribution 1-to-N rather than 1-to-1).
  Deferred to v1.7+ alongside `get_density_matrix_of`.

**Edge cases.**

- Empty position → `density = zeros(4096)`.

---

### `apply_move_qm` (low-level, per-channel dict)

```python
def apply_move_qm(state, move, *, optional_return_unitary=False) -> dict
```

The §17.1 `applyMoveQm` raw API. Returns the per-channel dispatch
dict; for an assembled ψ_post use `apply_move_qm_full` below.

**Parameters.**

- `state` — pre-move state.
- `move` — endpoints. Accepts:
  - tuple of two ints: `(from_sq, to_sq)`,
  - tuple of two 4-tuples: `((x0, y0, z0, w0), (x1, y1, z1, w1))`,
  - any object with `.from_sq` / `.to_sq` attributes (e.g.,
    `chess_spectral_4d.Move4D`).
- `optional_return_unitary: bool` — currently ignored. Reserved for a
  v1.5+ enhancement that will assemble and return the block-diagonal
  45 056 × 45 056 sparse `U_move`.

**Returns.** Dict keyed by channel name. The 11 keys are
`'A1'`, `'STD4_X'`, `'STD4_Y'`, `'STD4_Z'`, `'STD4_W'`,
`'FA_PAWN_W'`, `'FA_PAWN_Y'`, `'FIB_SYM_1'`, `'FIB_SYM_2'`,
`'FIB_SYM_3'`, `'FD_DIAG'`. Each value is one of:

| Value type     | When | Meaning |
|---|---|---|
| `csr_matrix` (4096×4096, complex128) | non-capture, channel admits a strict-unitary or sub-unitary form | apply as `U_chan @ ψ_pre[chan_block]` |
| dict with `psi_post_block` | measurement-only / rank-1 / cross-orbit / **all capture cases** | splice `value['psi_post_block']` directly into `ψ_post[chan_block]` |
| dict without `psi_post_block` | cross-orbit STD4 fallback path | re-encode the post-move position via [`state_to_psi`](../python/chess_spectral/qm_4d.py) and slice the channel block |

The **shipping channel-by-channel matrix** (post-B5):

| Channel | Non-capture | Capture |
|---|---|---|
| `A1` | `csr_matrix` (same-orbit) / marker (cross-orbit) | marker `'capture-rank-1-with-renorm'` |
| `STD4_X/Y/Z/W` | `csr_matrix` (same-orbit) / marker (cross-orbit) | marker `'capture-rank-1-with-renorm'` |
| `FA_PAWN_W/Y` | `csr_matrix` (axis-flip non-capture) | marker `'capture-partial-isometry'` |
| `FIB_SYM_1/2/3` | marker `'measurement-only'` | marker `'capture-measurement-only'` |
| `FD_DIAG` | marker `'rank-1-update-with-renorm'` | marker `'capture-rank-1-with-renorm'` |

**Dispatch contract.** Consumers iterate the dict and handle each
value:

```python
for chan_name, value in channels.items():
    block_offset = ... # see CHANNELS_4D table below
    if isinstance(value, dict):
        # Marker dict
        if 'psi_post_block' in value:
            psi_post[block_slice] = value['psi_post_block']
        else:
            # Cross-orbit STD4: re-encode at the consumer layer
            psi_post[block_slice] = re_encode(post_position)[block_slice]
    else:
        # csr_matrix
        psi_post[block_slice] = value @ psi_pre[block_slice]
```

After block-wise dispatch, renormalize ψ_post (capture moves can
break norm via the FA_PAWN partial-isometry path; the rank-1 +
renorm pattern from
[ADR-003 §3.1](adr/qm_4d/ADR-003-per-channel-move-transformation.md)
channels 8-9).

**Edge cases.**

- **Capture moves** route every channel through marker dicts; the
  consumer splices all 11 blocks directly into ψ_post (no per-channel
  matrix multiplications needed).
- **Cross-orbit** `STD4_*` and `A1` moves return markers without
  `psi_post_block`; the consumer (or `apply_move_qm_full`) does a
  measurement-only re-encode of the post-move position.
- **Castling, en-passant, promotion** are handled by the upstream
  classical move-application (the `state_to_psi` re-encode
  inside the marker construction). The QM bridge sees them as
  ordinary moves; the FEN4-based re-encode reflects the post-move
  classical position correctly.
- **No-op move** (`from_sq == to_sq`): produces identity-like
  per-channel entries; ψ_post ≈ ψ_pre.

**Pyodide notes.** The `csr_matrix` entries in the returned dict are
SciPy sparse — Pyodide handles them via the standard SciPy bridge.
Marker dicts are pure-Python (ints, floats, ndarrays, strings) so
they cross the bridge cleanly.

---

### `apply_move_qm_full` (high-level, assembled ψ_post)

```python
def apply_move_qm_full(
    state, move, *,
    side_to_move=True,
    side_to_move_post=None,
    return_per_channel=False,
) -> dict
```

The recommended `applyMoveQm` entry point for most consumers. Wraps
`apply_move_qm`, performs the per-channel block dispatch described
above, and returns the assembled `ψ_post` as Float32 interleaved.

**Parameters.**

- `state`, `move` — same as `apply_move_qm`.
- `side_to_move: bool` — side-to-move BEFORE the move (used to
  construct ψ_pre). Default `True`.
- `side_to_move_post: bool, optional` — side-to-move AFTER the move.
  Default flips `side_to_move` (standard alternation). Used both for
  the cross-orbit STD4 fallback re-encode and for the marker
  constructions inside per-channel builders.
- `return_per_channel: bool` — if `True`, also include the raw
  per-channel dispatch dict under `perChannel` key. Useful for
  debugging / per-channel diagnostics; default `False`.

**Returns.** Dict with:

- `ok: bool`.
- `psi: ndarray[float32, (90112,)]` — assembled ψ_post serialized
  as `ComplexArray`.
- `basisDim: int` — `45056`.
- `normSq: float` — `⟨ψ_post|ψ_post⟩`. After renormalization this is
  `1.0` within float rounding (or `0.0` for the pathological zero-
  vector case, e.g., a position with no pieces).
- `perChannel: dict, optional` — present only if
  `return_per_channel=True`. The raw dispatch dict from
  `apply_move_qm`.

**Per-channel renormalization.** Capture moves drop amplitude (the
captured piece's contribution is removed from FA_PAWN's 8-mode block,
or from the source square's contribution in the rank-1-update
channels). The bridge renormalizes ψ_post to `‖ψ_post‖ = 1` after
block-wise assembly, matching ADR-002's Zeno-style projection +
renormalization. For non-capture moves the renormalization is a
near-no-op (norm preservation is exact within float rounding for the
strict-unitary channels).

**Example.**

```python
>>> from chess_spectral.qm_4d_bridge import apply_move_qm_full
>>> from chess_spectral.fen_4d import parse
>>> pos = parse("4d-fen v1: K@4,0,0,0; k@4,7,7,7; R@0,0,0,0")
>>> r = apply_move_qm_full(pos, move=((0,0,0,0), (1,0,0,0)),
...                        side_to_move=True)
>>> r['ok'], r['psi'].shape, r['basisDim']
(True, (90112,), 45056)
>>> abs(r['normSq'] - 1.0) < 1e-6
True
```

---

### `measure_at`

```python
def measure_at(state, coords, observable=None, *,
               side_to_move=True, rng=None) -> dict
```

Born-rule projective measurement at lattice coords. Drives M14.5.

**Parameters.**

- `state` — position dict or `.position`-bearing object.
- `coords` — lattice coords. Accepts a 4-tuple `(x, y, z, w)` (each
  in `[0, 7]`) or a linear-square index in `[0, 4096)`.
- `observable: str, optional` — default `None` measures the
  position observable at `coords`. Named observables: `'rook'`,
  `'bishop'`, `'queen'`, `'king'`, `'knight'` measure the
  eigenvalue distribution of the corresponding piece-reach Hermitian
  on the cell-channel block at `coords`. Pawn observables are
  reserved (raise `NotImplementedError`; deferred to Track B per
  [ADR-005](adr/qm_4d/ADR-005-pawn-pseudo-hermitian-eta-metric.md)).
- `side_to_move` — forwarded to `state_to_psi`.
- `rng: numpy.random.Generator, optional` — source of randomness for
  the Born-rule sample. Default `numpy.random.default_rng()` (fresh
  seed). Pass a seeded generator for reproducible measurements.

**Returns.** Dict with:

- `ok: bool`.
- `probability: float` — `|⟨c|ψ⟩|²` of the measured outcome.
- `sampledOutcome: int | float` — cell index for the position
  observable, eigenvalue (float) for a named observable.
- `postCollapsePsi: ndarray[float32, (90112,)]` — collapsed and
  renormalized ψ as `ComplexArray`.

**Edge cases.**

- **Zero-amplitude cell:** if `|⟨c|ψ⟩|² = 0` at the measured cell,
  the post-collapse ψ would be zero; the bridge returns
  `postCollapsePsi = zeros(90112)` rather than dividing by zero.
- **`observable='pawn'` / `'pawn_w'` / `'pawn_y'`:** raises
  `NotImplementedError` with a Track B / ADR-005 pointer. The
  pseudo-Hermitian / η-metric pawn-observable machinery is deferred.

---

### `get_density_matrix_of` *(deferred to v1.7+)*

```python
def get_density_matrix_of(state, piece_id) -> dict
```

Reduced density matrix for a piece via partial trace over the rest
of the system. Drives M14.4 entanglement viz.

**Status: raises `NotImplementedError`.** The reduced density matrix
`ρ = Tr_chans(|ψ⟩⟨ψ|)` requires a channel-to-piece attribution map
and a partial-trace operator over channel labels — both mechanical
once the attribution is decided, but the bilinear FIB / FD_DIAG /
FA_PAWN channels make the attribution 1-to-N rather than 1-to-1
in the current encoder. Deferred to v1.7+ (along with the per-piece
variant of `get_qm_density`).

The function signature is reserved in the v1.5 API so v1.7+ can
promote without breaking consumers.

---

### `get_probability_current`

```python
def get_probability_current(state, *, side_to_move=True) -> dict
```

`j_p(c) = Im(ψ* ∇ψ)` — probability current field on the lattice.
Drives M14.6 QM-filament viz.

**Parameters.**

- `state`, `side_to_move` — as elsewhere.

**Returns.** Dict with:

- `ok: bool`.
- `j: ndarray[float32, (4096, 4)]` — per-cell × per-axis current
  vector. `j[c, a]` is the component at cell `c` along axis
  `a ∈ {0, 1, 2, 3}` (= x, y, z, w).

**Implementation notes.** The gradient is a finite-difference
operator on `P_8 □ P_8 □ P_8 □ P_8` (Kronecker sum of per-axis 1-D
central-difference operators with reflecting boundary). The
operators are anti-Hermitian, so `j` is real-valued. The current is
summed across all 11 channels.

For a static ψ (no time evolution under `H_0` between calls),
`∇·j ≈ 0` at floating-point residual — the discrete continuity
equation `∂_t ρ + ∇·j = 0` reduces to divergence-freeness. This is
verified by tests.

---

### `get_qm_expectation`

```python
def get_qm_expectation(state, observable, *,
                       side_to_move=True, weights=None) -> dict
```

`⟨ψ|H|ψ⟩` for a named Hermitian observable. Composes with the
v1.6+ engine `evaluatePosition` to form the QM evaluator family.

**Parameters.**

- `state`, `side_to_move` — as elsewhere.
- `observable: str` — one of `{'rook', 'bishop', 'queen', 'king',
  'knight'}` (case-insensitive). Pawn observables raise
  `NotImplementedError` per ADR-005 (deferred to Track B's full
  η-metric machinery; v1.5 ships only `H_pawn_*_herm` symmetric-
  projection variants, not exposed as named bridge observables).
- `weights: Mapping[str, float], optional` — per-channel weight
  overrides. Currently ignored; v1.5 treats H as the lifted
  `I_11 ⊗ H` operator (uniform channel weighting). Reserved for
  v1.7+ where the engine evaluator may expose per-channel weights.

**Returns.** Dict with:

- `ok: bool`.
- `value: float` — `⟨ψ|H_full|ψ⟩` where `H_full = I_11 ⊗ H`.
  Equals the sum of per-channel-block expectation values.

**Raises.**

- `NotImplementedError` for `observable in {'pawn', 'pawn_w',
  'pawn_y'}`.
- `ValueError` for unknown observable names.

**Implementation note.** The bridge avoids materializing the lifted
45056 × 45056 operator; it sums per-block via
`Σ_chan ⟨ψ_chan | H | ψ_chan⟩` directly.

---

## §17.5 dev / debug surface (6 methods)

These are short, mechanical, and not on the M14.x critical path.

### `get_version`

```python
def get_version() -> dict
```

Returns `{'ok': True, 'version': str}`. Wrapper over
`chess_spectral.__version__`, which derives dynamically from
`importlib.metadata.version("chess-spectral")` (per the v1.3.2
contract; cannot drift from the installed wheel).

Useful at consumer startup to verify worker version.

---

### `get_encoder_shape`

```python
def get_encoder_shape() -> dict
```

Returns the channel layout for visualizer self-validation.

**Returns.**

```python
{
    'ok': True,
    'channels': [
        {'name': 'A1',         'offset':     0, 'dim': 4096},
        {'name': 'STD4_X',     'offset':  4096, 'dim': 4096},
        {'name': 'STD4_Y',     'offset':  8192, 'dim': 4096},
        {'name': 'STD4_Z',     'offset': 12288, 'dim': 4096},
        {'name': 'STD4_W',     'offset': 16384, 'dim': 4096},
        {'name': 'FIB_SYM_1',  'offset': 20480, 'dim': 4096},
        {'name': 'FIB_SYM_2',  'offset': 24576, 'dim': 4096},
        {'name': 'FIB_SYM_3',  'offset': 28672, 'dim': 4096},
        {'name': 'FA_PAWN_W',  'offset': 32768, 'dim': 4096},
        {'name': 'FA_PAWN_Y',  'offset': 36864, 'dim': 4096},
        {'name': 'FD_DIAG',    'offset': 40960, 'dim': 4096},
    ],
    'totalDim': 45056,
}
```

Source of truth: [`chess_spectral.encoder_4d.CHANNELS_4D`](../python/chess_spectral/encoder_4d.py).

The visualizer uses this to validate at startup that the worker
matches the expected channel set — e.g., catches a stale worker
still on a v1.0-era 10-channel layout shipping against a v1.5+
HUD expecting 11.

---

### `get_fen4_state`

```python
def get_fen4_state(state) -> dict
```

Returns `{'ok': True, 'fen4': str}`. Thin wrapper over
[`chess_spectral.fen_4d.serialize`](FEN4_FORMAT.md) applied to the
current state's position dict.

For the FEN4 grammar, see [FEN4_FORMAT.md](FEN4_FORMAT.md).

---

### `load_fen4`

```python
def load_fen4(fen4_string) -> dict
```

Re-imports a FEN4 string into a fresh state dict.

**Returns.** `{'ok': True, 'state': dict[int, PieceValue]}` — the
parsed position dict, ready to feed any §17.1 method. Caller can
wrap this in a [`chess_spectral_4d.GameState4D`](../python/chess_spectral_4d/__init__.py)
if move history / clock tracking is needed; for kinematic-only QM
analysis the dict alone is sufficient.

**Raises.** Any exception from [`fen_4d.parse`](FEN4_FORMAT.md#errors)
on malformed input (typically `ValueError`).

---

### `load_jsonl_fixture`

```python
def load_jsonl_fixture(pieces_obj) -> dict
```

Alternative to `load_fen4` for consumers that already have the
structured pieces dict. Three accepted shapes:

- **Direct sq-keyed dict:** `{sq_int: piece_value, ...}` — returned
  as-is (idempotent path).
- **JSONL fixture wrapper:** `{'name': str, 'pieces': {sq_str:
  piece_str, ...}}` — the format used in
  [`tests/fixtures/positions_4d.jsonl`](../python/tests/fixtures/positions_4d.jsonl).
  Pawns encoded as `'Pw'` / `'Py'` / `'pw'` / `'py'` (color + axis
  as a 2-char string) are expanded to the `(color, axis)` tuple.
- **Coord-list form:** `{'pieces': [{'coord': [x,y,z,w], 'piece':
  'K', ...}, ...]}` — converted to sq-keyed via
  [`tables_4d.sq4`](../python/chess_spectral/tables_4d.py).

**Returns.** `{'ok': True, 'state': dict[int, PieceValue]}`.

**Raises.** `TypeError` / `ValueError` on malformed input.

---

### `has_legal_moves`

```python
def has_legal_moves(state, team) -> dict
```

Boolean: does `team` have any legal move? Required for stalemate
detection in
[`chess_spectral_4d.bridge.get_draw_status`](../python/chess_spectral_4d/bridge.py)
(no legal moves + not in check ⇒ stalemate).

**Parameters.**

- `state` — accepts two shapes:
  - `chess4d.GameState` (with `.board` attribute) → full-legality
    path via
    [`occupation_aware_moves_a_4d`](../python/chess_spectral/phase_operators_4d/__init__.py).
    Requires `chess4d` installed (ships as a project dependency).
  - position dict or object with `.position` → best-effort empty-
    board adjacency lower-bound. Over-counts (no obstruction / king-
    in-check / occupancy filter), but `hasMoves==False ⇒ definitely
    no legal moves`, which is the useful direction for stalemate
    detection.
- `team: str` — `'white'` or `'black'` (case-insensitive).

**Returns.** Dict with:

- `ok: bool`.
- `hasMoves: bool`.
- `count: int` — actual move count when computable (Path A); upper-
  bound count on Path B.

**Raises.** `ValueError` on invalid `team`. `ImportError` if Path A
is requested but `chess4d` is not installed.

---

## Helpers

### `complex_to_interleaved_float32`

```python
def complex_to_interleaved_float32(psi: np.ndarray) -> np.ndarray
```

Serialize a complex ψ to a Float32 array of interleaved real+imag
pairs.

**Returns.** `ndarray[float32, (2 * psi.size,)]` with
`out[0::2] = psi.real`, `out[1::2] = psi.imag`. Cast to `complex128`
internally; original shape is flattened.

This is the inverse of the consumer's `Float32Array` →
`{ real, imag }` deserialization. Most consumers do not need to call
this directly — every `psi`-returning bridge method already returns
the interleaved Float32. Exposed for advanced consumers building
their own ψ-modification pipelines.

---

## Error contract

| Condition | Behavior |
|---|---|
| Valid input, normal path | Returns dict with `ok: True` |
| Malformed input (bad coords, unknown observable, etc.) | Raises `TypeError` or `ValueError` |
| Per-piece marginal (`get_qm_density(piece_id=...)`) | Raises `NotImplementedError` (v1.7+) |
| `get_density_matrix_of` (any call) | Raises `NotImplementedError` (v1.7+) |
| Pawn observable (`'pawn'` / `'pawn_w'` / `'pawn_y'`) in `measure_at` or `get_qm_expectation` | Raises `NotImplementedError` (Track B / ADR-005 pointer) |
| Empty position passed to `get_qm_state` | Returns ψ = 0, `normSq: 0.0` (no exception) |
| Capture move passed to `apply_move_qm_full` | Returns assembled & renormalized ψ_post |
| Cross-orbit STD4 / A_1 move | Returns assembled ψ_post via measurement-only re-encode (transparently to caller) |
| `chess4d`-shape state passed to `has_legal_moves` without `chess4d` installed | Raises `ImportError` |

Bridge methods do not return `{'ok': False}` — failures raise. This
matches the chess4D-OC consumer's expectation of explicit error
handling rather than silent `ok: False` propagation.

---

## Versioning

**Package version requirement:** `chess-spectral >= 1.5.0`. Both
`chess_spectral` and `chess_spectral_4d` packages share a single dist
version derived from `importlib.metadata`; verify at consumer
startup via `get_version()`.

**v1.5 ships:** All 13 methods documented above. The 7 §17.1 methods
all return well-defined results for any valid input (no
`NotImplementedError` raises for inputs that v1.5 declared
in-scope). The two deferred §17.1 methods (`get_density_matrix_of`,
`get_qm_density(piece_id=...)`) raise `NotImplementedError` with
pointers to v1.7+.

**v1.6 (planned):** Adds the §17.2 engine bridge surface
(`getBestMove`, `evaluatePosition`, `runTournament`) — see
[research notebook §17.2](../../chess_spectral_research_notebook.md#172-chess-spectral-16--engine-submodule-bridge-surface).
The §17.5 `listAvailableEvalTypes` method ships in v1.6 (returns the
set of evaluators the engine supports at the running version).

**v1.7+ (deferred):** Per-piece marginal in `get_qm_density`;
reduced density matrix in `get_density_matrix_of`; pawn-observable
support in `measure_at` / `get_qm_expectation` via the full η-metric
machinery (per [ADR-005](adr/qm_4d/ADR-005-pawn-pseudo-hermitian-eta-metric.md)).
Bridge method names are reserved in v1.5 so v1.7+ promotion does
not break consumers.

**Stability promise.** Within v1.5.x patch releases, the method
signatures and return-dict shapes documented here will not change.
Behavior fixes (e.g., Phase 4 amendment-driven changes to the
per-channel marker dispatch) may land but always preserve the
`{'ok': True, 'psi': ..., 'basisDim': 45056, ...}` external shape.

---

## See also

- **Research narrative:** [`chess_spectral_research_notebook.md` §17](../../chess_spectral_research_notebook.md)
  — design rationale, version ladder, scope decisions.
- **Architecture decisions:** [`docs/adr/qm_4d/`](adr/qm_4d/README.md)
  — phase convention (ADR-001), time evolution (ADR-002), per-channel
  move construction (ADR-003 + amendment), Z_2 superselection
  (ADR-004), pawn pseudo-Hermitian (ADR-005). Each ADR documents the
  options considered and the rejection reasons.
- **Phase 3.5 empirical validation:** [`PHASE_3_5_PROBE_RESULTS.md`](adr/qm_4d/PHASE_3_5_PROBE_RESULTS.md)
  — probe pass/fail vs each ADR's acceptance criterion + amendments.
  This is the authoritative status doc when an ADR's original text
  conflicts with current behavior.
- **Format references:**
  - [FEN4_FORMAT.md](FEN4_FORMAT.md) — FEN4 v1 placement-literal
    grammar (consumed by `load_fen4` / `get_fen4_state`).
  - [NDJSON4_FORMAT.md](NDJSON4_FORMAT.md) — NDJSON4 ply-log format.
- **Encoder source:** [`chess_spectral/encoder_4d.py`](../python/chess_spectral/encoder_4d.py)
  for `CHANNELS_4D`, `encode_4d`, `channel_energies_4d`.
- **QM kinematic layer:** [`chess_spectral/qm_4d.py`](../python/chess_spectral/qm_4d.py)
  for `state_to_psi`, the H_piece observables, and the channel
  projectors.
- **Move dynamics:** [`chess_spectral/qm_4d_dynamics.py`](../python/chess_spectral/qm_4d_dynamics.py)
  for the per-channel `u_move_*` builders that `apply_move_qm`
  dispatches to.
