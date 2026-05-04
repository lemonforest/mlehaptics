# chess_spectral (Python)

Python reference implementations of the **640-dim 2D** and **45 056-dim
4D** spectral chess encoders, plus the **quantum-mechanical front-end**
(2D + 4D kinematics; 4D dynamics shipped in v1.5, 2D dynamics in v1.6.x),
the v1.6 **§16 search + tournament + sweep** engine surface, the
**v5 unified wire format** (three encoding modes — dense / per-channel
replacement / XOR-stream — with empirical 7.23× compression on 4D
fixtures vs dense gzipped), the v1.7 **native bitboard fast-path**
+ **time-budget mid-iteration honoring** (cumulative ~125× speedup on
dense `legal_moves()` calls vs v1.6), and the v1.8 **`GameState4D`
push/pop + board accessors + check predicates** consumer surface
(chess4D-OC visualizer M11.40 unblocker).

Sibling of the C17 port in `../src/`. Use the Python package for REPL /
LLM / notebook analysis, Pyodide-bridge consumers, and the §16
ship-gate matrix runner; use the C binaries for batch encoding
throughput.

The pieces ship under two top-level packages:

- **`chess_spectral`** — 2D encoder + 4D encoder math + 4D phase
  operators + QM extension. Everything that's pure spectral / B_4
  representation theory lives here.
- **`chess_spectral_4d`** — 4D game-state surface (move history,
  side-to-move, draw status, FEN4 round-trip, the Pyodide
  `chess_spectral_4d.bridge` module). Splits cleanly from the
  encoder so the 4D-rules concerns don't bleed into the spectral
  math.

## What's new in v1.12 (May 2026)

The §20.15 third-tier ship: **encoder BIP-hybrid** — sign × magnitude
factoring for the spectral encoder. Sign packs as 1 bit per dim
(algebraically exact); magnitude quantizes to 4 or 8 bits per dim
with per-channel scaling. Cosine-sim ≥ 99.99% at 8-bit on both 2D
and 4D acceptance corpora. No breaking changes vs 1.11.x; `encode_640`
/ `encode_4d` defaults unchanged.

- **Storage**: 760 bytes (2D) / 50 KB (4D) at 8-bit, vs 2,560 / 180
  KB float32 — about **3.4-3.6× compression** with negligible
  cosine-sim loss. At 4-bit: 440 / 28 KB → **5.8-6.4× compression**;
  passes acceptance for 2D, lands just under 99.5% for 4D (research
  finding documented in §20.18).

- **`encode_2d_bip_hybrid` / `encode_4d_bip_hybrid`** — new public
  API. Returns `SpectralBIPHybrid2D` / `SpectralBIPHybrid4D`
  dataclasses with three integer fields: `sign_packed` (bytes),
  `magnitude_scales` (per-channel float32 norms), `magnitudes`
  (uint8 — packed nibbles for 4-bit, plain bytes for 8-bit).

- **`decode_2d_bip_hybrid` / `decode_4d_bip_hybrid`** — reconstruct
  float64 vector. Lossy at the magnitude-quantization level; sign
  storage is exact.

- **`cosine_similarity_hybrid_*`** — pair-wise distance metric for
  hybrid vectors. Approximates the float32 baseline within 1%
  absolute deviation at 8-bit.

- **Bridge surface** — `chess_spectral_4d.bridge.{encode_position_2d_bip_hybrid,
  encode_position_4d_bip_hybrid}` for chess4D-OC / Pyodide consumers.
  Returns plain Python int/list across the WASM boundary.

- **62 immolation tests** lock the §20.15 acceptance gate (8-bit on
  2D + 4D), the sign-bit storage exactness, the per-channel
  magnitude bounds, the 4D 4-bit research finding (sim ∈ [0.99,
  0.999]), the pair-wise cosine-sim approximation, and the 4-bit
  nibble packing round trip.

This is **B-spike-2** in the §20.15 three-tier phasing. B-spike-1a
(sheet-block BIP) shipped in 1.10.0; B-spike-1b (ALU-native phase
engine) shipped in 1.11.0; B-spike-3 (search-engine integration)
remains parked.

## What's new in v1.11 (May 2026)

The §20.15 second-tier ship: **ALU-native phase-operator move
generator**. The §11 phase-operator engine — already integer-
arithmetic at the core, already BIP-isomorphic at the group-
theoretic level over `Z_640` — gains a public integration entry
point that doesn't require a `python-chess.Board` argument. Pure
ALU-native pseudo-legal move generation for Pyodide / WASM /
non-Python downstream consumers. No breaking changes vs 1.10.x.

- **`phase_only_pseudo_legal_moves(pos, side_to_move_white,
  ep_file=...)`** — new integration entry point. Iterates the
  side-to-move's pieces, computes per-piece destination sets via
  Solution B's phase-arithmetic, returns a flat list of
  `(from_sq, to_sq, promotion_char)` tuples in encoder sq
  convention. Pseudo-legal in the python-chess sense (respects
  piece geometry, occupation, double-push, en passant, promotion
  expansion); caller filters check.

- **`occupation_field_from_pos_dict` + `ep_phase_from_ep_file`** —
  pure-phase adapters that skip python-chess entirely. Counterparts
  of the existing `occupation_field_from_board` and
  `ep_phase_from_board`; consumers that have a position dict +
  side-to-move + ep_file (e.g., from a 1.10.0 BIP-encoded sheet
  block) can build the occupation field directly without
  reconstructing a Board.

- **Acceptance gate**: parity vs `board.pseudo_legal_moves` on a
  representative 8-FEN corpus (opening, middlegame, endgame,
  EP-active, promotion-imminent). All move sets match exactly
  modulo castles (deferred to 1.12.0+). 26 tests, pass on first
  implementation.

- **Documented `Z_640` wire contract** (notebook §20.17). The
  constants `MODULUS`, `ROW_GEN`, `COL_GEN`, `DIAG_NE_SW_GEN`,
  `DIAG_NW_SE_GEN`, `KNIGHT_SHIFTS`, `KING_SHIFTS` are part of
  the public API and don't move without a major version bump.

- **Diagnostic benchmark**
  (`tests/bench_phase_operator_movegen.py`) — ~190 µs at startpos
  for ALU-native vs ~73 µs for python-chess Cython (~2.5× ratio,
  expected). Structurally faster than Solution-B-per-piece-loop
  because the occupation field is built once per position instead
  of per-piece. Value is **portability**, not raw speed.

- **Deferred** to a 1.12.0+ follow-up: castling generation in the
  ALU-native path (needs attack map), check-filter refactor of
  `phasecast_is_check` (currently takes a Board input). Consumers
  wanting check-filtered legal moves should pair the 1.11.0
  pseudo-legal output with the existing `phasecast_is_check`.

This is **B-spike-1b** in the notebook §20.15 three-tier phasing.
B-spike-1a (sheet-block BIP) shipped in 1.10.0; B-spike-2
(encoder BIP-hybrid) is the next ship and depends on the
bit-packing patterns 1.10.0 established.

## What's new in v1.10 (May 2026)

The §20 BSHDC spike's first ship: **BIP-encoded sheet block**.
Integer-native form of the 1.9.0 non-Markovian aux block that
packs the same content into 3 bytes (vs 88 bytes float64) with a
bit-exact round trip on the legal state space. ALU-native operator
fast paths for Pyodide / chess4D-OC / batch retrieval consumers.
No breaking changes vs 1.9.x; both representations ride side-by-side.

- **`SheetStateBIP` dataclass** — `categorical: uint16` + `halfmove_clock: uint8`.
  ~29× smaller than the 1.9.0 float64 path. Round-trip exact
  for all 87,264 legal sheet states (864 categorical × 101
  half-move) — verified exhaustively in
  `tests/test_sheets_bip.py`. The Z₁₀₁ half-move stays in its
  own `uint8` slot per §19.4's "structural split" finding (no
  embedding into Z₁₂₈ that would introduce a wrap discontinuity).

- **Operator fast paths** — single-integer-op queries against the
  categorical portion: `castling_alive`, `kingside_castling_alive`,
  `ep_target_active`, `fifty_move_rule_triggered`,
  `threefold_claimable`, etc. Each is a bit-mask + comparison,
  no FPU.

- **Distance metrics** — `hamming_distance_categorical(a, b)`
  for corpus-similarity retrieval where binary state distinctions
  matter (sharper than float cosine-sim for the categorical
  portion). `halfmove_distance(a, b)` for the integer Z₁₀₁ slot.

- **Bridge surface** — `chess_spectral_4d.bridge.get_sheet_state_bip` /
  `encode_sheet_aux_bip` / `decode_sheet_state_from_bip`. All
  numpy-free across the WASM boundary; integers cross the
  Pyodide bridge directly.

- **Where BIP wins**: Pyodide / WASM consumers (50-100×), batch
  retrieval over saved corpora (~3 orders of magnitude),
  Hamming-distance corpus filtering, future v5 mode-2 XOR-stream
  wire format compression. **Where it doesn't**: single-position
  depth-1 queries (per §19.10's bitboard floor — bit-shift +
  AND can't undercut python-chess's `int & mask` either).

- **35 new immolation tests** (`tests/test_sheets_bip.py`) lock
  the 87,264-case exhaustive round trip, the 8-operator parity
  vs the 1.9.0 SheetState path, the Hamming-distance behavior
  (including the subtle case that rep=1 vs rep=2 differ in 2
  bits, not 1, due to binary representation), the bridge
  round-trip, and the python-chess + GameState4D factory
  parities.

This is **B-spike-1a** in the notebook §20.15 three-tier phasing.
B-spike-1b (promote §11 phase-operator engine to public API)
remains independent and can ship separately. B-spike-2 (encoder
BIP-hybrid) depends on the bit-packing patterns this 1.10.0
establishes.

## What's new in v1.9 (May 2026)

The §19 spike's Phase-1 sheet block ships as a
**representation-completeness** feature alongside a new
`legal-moves` CLI command for both 2D and 4D. No API breaks vs.
1.8.x; every addition is opt-in surface.

- **Non-Markovian sheet aux block**
  (`from chess_spectral import SheetState, encode_aux_block`) — the
  11-dim aux block carries castling rights, en-passant target,
  side-to-move, half-move clock, and repetition count alongside the
  base encoder vector. Opt in via the new `sheets=` kwarg on
  `encode_640(pos, sheets=...)` and `encode_4d(pos4, sheets=...)`;
  output dimension grows from 640 → 651 (2D) and 45056 → 45067
  (4D), with the base dims byte-identical to legacy / C encoder
  output. Lift state from `python-chess` via
  `SheetState.from_chess_board(board)` or from a 4D `GameState4D`
  via `SheetState.from_game_state_4d(state)`. Half-move clock uses
  a `Z_101` Fourier carrier preserving clock-distance fidelity;
  round-trip exact for every integer `[0, 100]`.

- **Representation only — no speed claim.** Notebook §19.10
  documents the depth-1 bitboard floor: `python-chess`'s
  `has_castling_rights` is one int-AND, and float→int conversion
  from a numpy slice can't undercut it. The same logic holds for
  `Board4D.halfmove_clock >= 100` and the hash-table threefold-
  repetition lookup. The sheet block's value is making encoder
  vectors self-sufficient for downstream consumers of saved /
  transmitted vectors (chess4D-OC, Pyodide pipelines, batch
  retrieval over saved corpora) — not raw runtime speed.

- **`legal-moves` CLI command (2D)** — `chess-spectral legal-moves
  --fen "<fen>" [--format uci|san|json] [--with-sheets]` enumerates
  the side-to-move's legal moves. Default UCI output, one move per
  line; JSON format includes per-move flags (capture / castling /
  en-passant / promotion) plus optional sheet block. Stdin support
  via `--fen -`. Uses `python-chess` for legal-move generation.

- **`legal-moves` CLI command (4D)** — `chess-spectral-4d
  legal-moves --fen4 "<fen4>" [--format compact|json]
  [--with-sheets] [--side-to-move white|black] [--halfmove-clock N]
  [--fullmove-number N]` enumerates legal moves at a 4D-OC
  position. Default compact format `x,y,z,w->x,y,z,w` with `DP`
  (double push), `EP` (en-passant capture), and `=Q` (promotion)
  tags; JSON format structured. Uses `Board4D.legal_moves()` (the
  native 4D move-gen via graph-Laplacian-derived primitives).

- **Pyodide-bridge surface for sheets** — `chess_spectral_4d.bridge`
  gains `get_sheet_state`, `encode_sheet_aux`, and
  `decode_sheet_aux_from_vector`. The bridge contract holds
  ("plain dict, no numpy across the WASM boundary"); aux blocks
  cross as `list[float]`. `chess4D-OC` and any other browser /
  Pyodide consumer can now reason about castling rights / EP /
  halfmove / repetition without reconstructing a `python-chess.Board`
  or a `GameState4D` worker-side.

- **`encode_2d` future-proof alias** — `from chess_spectral import
  encode_2d` (1.9.0+) is the recommended name going forward,
  mirroring the 4D path's `encode_4d`. `encode_640` remains as a
  permanent alias, but the **dim count is not a stable contract**
  — sheets already bumped 640 → 651, and future channel
  enrichment (per the §20 BSHDC spike's antikythera-spectral
  reference) or further non-Markov state extensions may move it
  again. Query `ENCODING_DIM` (or check `enc.shape`) and iterate
  channels via `CHANNELS` rather than hardcoding 640. See
  notebook §19.11 for the full future-work note.

- **53 new immolation tests** lock the sheet round-trip (every
  legal halfmove value, every castling combination, every EP
  file), the encoder integration (base preservation + aux at
  correct offset), the factory lifts (`from_chess_board`,
  `from_game_state_4d`), the CLI smoke surface for both 2D and 4D
  legal-move enumeration, and the bridge round-trip
  (state → get → encode → decode) for both dimensions.

**1.9.1 update — README polish + v5 wire format design decision.**
Quick-start example switched from `encode_640` to the
future-proof `encode_2d` alias (the 640-dim count is no longer a
stable contract — see §19.11). PyPI project links gain a
`Roadmap` entry pointing at
[`ROADMAP.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/chess-maths/chess-spectral/ROADMAP.md).
v5 wire format officially documented as **not** carrying the sheet
aux block — sheets ride alongside in-memory vectors, and on-disk
the source PGN / NDJSON / FEN sidecar already carries the
non-Markov state. See [`frame_v5.py`](https://github.com/lemonforest/mlehaptics/blob/main/docs/chess-maths/chess-spectral/python/chess_spectral/frame_v5.py)
header note + notebook §19.12 for full rationale and the future-
extension path (223 reserved bytes in the v5 header give plenty
of room when a consumer eventually needs persisted sheet frames).

## What's new in v1.8 (May 2026)

The chess4D-OC visualizer's **M11.40 unblocker** release. Tier-1
of the upstream wishlist ships in 1.8.0 — `GameState4D` graduates
from a position+history snapshot to a persistent mutation type,
mirroring `python-chess.Board`'s push/pop ergonomics so the
chess4D-OC worker can drop the `python-chess4d-oana-chiru`
runtime dep. No API breaks vs. 1.7.x — every addition is opt-in
surface.

- **`GameState4D.push(move)` / `GameState4D.pop()`** — apply /
  undo a ply, mutating in place. `push` accepts a `Move4D` or a
  `((from_xyzw), (to_xyzw)[, promote_to])` tuple. `pop` raises
  `IndexError` on an empty history (parallel to
  `chess.Board.pop()`'s contract). Returns the recorded /
  popped `Move4D` so callers can recover capture / promotion
  metadata.

- **`GameState4D.board` view** — read-only proxy over the live
  position dict. Exposes `occupant(sq)` and `pieces_of(side)`
  accessors plus `__contains__` and `__len__`. `sq` accepts both
  the linear `int` and the `(x,y,z,w)` `Coord4D` tuple. The view
  does not copy — push / pop mutations are reflected
  immediately.

- **`GameState4D.to_fen()` / `GameState4D.from_fen(fen4)`** —
  symmetric aliases for `to_fen4` / `from_fen4` (the 1.7.1
  slash-tolerant FEN4 form is accepted on both names).

- **`GameState4D.iter_pieces()`** — yields `(sq_idx, piece_value)`
  tuples in the format `chess_spectral.encoder_4d.encode_4d`
  consumes directly. `dict(state.iter_pieces())` is a one-liner
  replacement for the chess4D-OC worker's previous
  `_state_to_pos4` helper.

- **`chess_spectral_4d.engine.search.search()` accepts
  `GameState4D`** — same `SearchResult` shape as before; the
  engine constructs a transient `Board4D` internally. Drops the
  `Board4D.from_fen(state.to_fen4())` hop chess4D-OC was
  previously paying per search call.

- **`GameState4D.is_check()` / `is_checkmate()` / `is_stalemate()`**
  — wraps `Board4D.is_check()` plus a short-circuit
  legal-moves probe for mate / stalemate. `is_checkmate` /
  `is_stalemate` bail on the first legal move via
  `next(iter(...), None)`, so the dense-position cost is
  `O(legal-move generation)` worst case — about 2s at the dense
  28-king start with the 1.7.0 native bitboard fast-path active.

- **16 new immolation tests** in
  `tests/test_gamestate4d_consumer_surface.py` lock down the
  contract shape and at least one concrete behaviour per
  wishlist item. Hard gate — chess4D-OC's M11.40 PR will fail
  loudly if any of these regress.

**1.8.1 update — canonical 4D initial position landed.**
`chess_spectral_4d.initial_position()` returns a fresh
`GameState4D` at the Oana-Chiru §3.3 4D starting layout (896
pieces total: 448 white + 448 black, 28 kings per side).
`STARTING_FEN4` exposes the same layout as a FEN4 v1 string for
consumers that want a literal. Slice helpers
(`central_slices()`, `white_only_slices()`, `black_only_slices()`,
`empty_slices()`) expose the §3.3 (z, w) classification with
`|C| = 4`, `|W_only| = 24`, `|B_only| = 24`, `|E| = 12`. 24 new
immolation tests including a SHA-256 hash lock on the canonical
FEN4 string.

Tier-2 (ψ-driven density / current, partial-trace density
matrices) is still deferred — needs the η-metric machinery from
ADR-005.

## What's new in v1.7 (May 2026)

The chess4D-OC visualizer wishlist release. Headline pieces:

- **`SearchOptions.time_budget_ms` honored mid-iteration**
  (`chess_spectral_4d.engine.search`). Previously the deadline was
  checked only between iterative-deepening iterations — a 5-second
  budget on the dense 28-king starting position could overrun by
  ~100× before depth-1 alone completed. v1.7 threads the deadline
  into the alpha-beta inner loop and returns the deepest-completed-
  so-far best move on deadline exit. New `SearchResult.timed_out:
  bool` field distinguishes deadline-exit from natural completion.

- **Native bitboard fast-path** (`chess_spectral.spatial_4d`,
  `cs_bitboard4d` shared library). Pure-C primitives for the
  4096-bit `Bitboard4D` — popcount, bitwise AND/OR/XOR/NOT/sub,
  per-square set/clear/toggle/test, predicates, and the load-bearing
  `cs_bb4_to_squares` iteration helper (per-bit LSB extraction in
  C plus `b &= b - 1` clear, all without crossing the ctypes boundary
  per square). Ships in the wheel under `chess_spectral/_native/`;
  loaded via ctypes at import. Pure-Python `Bitboard4D` continues to
  work as fallback (sdist install, Pyodide / micropip) — verified by
  a dedicated `fallback-test` CI job. `Bitboard4D.to_squares()` /
  `.squares()` route through the native helper when
  `chess_spectral.HAS_NATIVE_BITBOARD` is True; **~16× faster**
  iteration on dense bitboards.

- **`Board4D.legal_moves()` algorithmic refactor.** The legal-move
  filter at the dense 28-king start position previously called
  `_is_attacked` once per own king (K=28 calls, each iterating all
  N opponent attackers from scratch). v1.7 iterates attackers once
  and tests `king_bb.intersects(attack_set)` per attacker, short-
  circuiting on the first hit — same per-op cost (O(1) bitboard
  test) but one call replaces K. **~12.7× faster** on the
  representative non-in-check 264-piece position.

- **Cumulative wishlist outcome.** The chess4D-OC visualizer's
  reported `legal_moves()` ~250s pain point at the standard 28-king
  start is now ~2s on the same hardware (**~125× faster**) with
  no API changes. Time-budget-checked search now respects user
  budgets within ~0.5s grace regardless of position density.

- **Downstream consumer flag.** `HAS_NATIVE_BITBOARD` is exposed
  at the top-level `chess_spectral` package — consumers can do
  `from chess_spectral import HAS_NATIVE_BITBOARD` to badge "native
  fast-path active" or fall back cleanly when the native lib isn't
  present.

For the full release history see [`CHANGELOG.md`](CHANGELOG.md).

## What's new in v1.6 (April 2026)

The §16 ship-gate release. Headline pieces:

- **Search core, tournament harness, and sweep ship-gate runner**
  ship as CLI commands at both 2D and 4D. Per-side symmetric agent
  specs let white and black be configured independently in the same
  single-process tournament loop:

  ```bash
  spectral_py sweep \
      --evaluators material,spectral,qm \
      --depths 1,2,3,4 \
      --n-games-per-pair 10 \
      --time-budget-ms 5000 \
      -o sweep.json
  ```

- **Three §16.1 evaluator families** (`material`, `spectral`, `qm`)
  ship at both 2D and 4D with a uniform
  `evaluate(position, side_to_move) -> float` contract — drop in any
  of them as the search heuristic.

- **Three independent in-house move-rule oracles** — each encodes
  the same legality predicate ("is move *m* legal in position *p*?")
  through a different mathematical lens, validated head-to-head
  against the `python-chess[4d]` reference and against each other.
  Not because one is more correct — they all agree on the same legal
  set — but because each lens is a standalone artifact for studying
  how spatial motion can be encoded:

  1. **Bitboard / attack-tables** (`chess_spectral.spatial_4d`) —
     the engineering lens. Bitboard4D primitive, per-piece attack
     tables (knight, king, rook, bishop, queen via magic-bitboard-
     style ray casting), axis-typed pawn moves (Pw/Py per Oana-Chiru
     §3 Def 11), Board4D game state, and draw rules. Same idea as a
     classic chess engine, lifted to Z_8^4.
  2. **Phase-space operators** (`chess_spectral.phase_operators`,
     `chess_spectral.phase_operators_4d`) — the algebraic lens.
     Per-piece move generation as group actions on a phase-space
     representation; legality is "the candidate move is in the orbit
     of the piece operator, intersected with the occupation oracle."
     2D ships under §11; 4D under §13.
  3. **Discrete-Laplacian eigenbasis oracle** (2D + 4D) — the
     spectral lens. The lattice's discrete Laplacian (Kron-sum of
     P_8 path-graph Laplacians; eigenvectors form a DCT-style basis)
     doubles as a structural lookup table for move legality — the
     **same** eigenbasis the spectral encoder uses to embed positions
     also tells you which moves are reachable. Concrete demonstration
     that "encode the geometry" and "encode the rules" share one
     foundation.

- **v5 unified `.spectral[z]` / `.spectralz4` wire format**
  (`chess_spectral.frame_v5`) — single 256-byte header serves both
  2D and 4D via explicit `n_dimensions` field. Three encoding modes
  selected by `encoding_mode`: dense (= legacy v2/v4 frame body),
  per-channel replacement (variable-size, ~2.84× compression on 4D
  stable workloads), and XOR-stream (fixed-size, **7.23× compression
  on 4D** vs dense gzipped). See
  [`docs/WIRE_FORMAT.md`](../docs/WIRE_FORMAT.md) for the byte-level
  spec covering all four shipped versions (v2/v3/v4/v5) and the
  reader-dispatch convention.

- **CI gate**: the 15-cell `verify-wheels` matrix is now opt-in via
  the `wheel-check` PR label (was running on every PR; saves ~150
  runner-min/PR while keeping the publish-time matrix as the
  load-bearing wheel-correctness gate).

For the full release history see
[`CHANGELOG.md`](CHANGELOG.md).

Both packages share a single dist version derived from
`importlib.metadata`; see [Install](#install) below.

## Install

From PyPI (recommended):

```bash
pip install chess-spectral
```

The base install pulls only `numpy` and `scipy` — sufficient for
encoding, the 4D phase operators, the kinematic QM layer, and the full
§17.1 bridge surface.

Optional extras:

```bash
# PGN ingest via chess_spectral.corpus (adds python-chess)
pip install "chess-spectral[corpus]"

# 4D phase-operator validation gates against the Oana & Chiru oracle
pip install "chess-spectral[test]"   # adds python-chess4d-oana-chiru
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
chess-spectral --help            # 2D CLI
chess-spectral-4d --help         # 4D CLI
```

Both packages also expose `__version__`, derived dynamically from the
installed dist:

```python
>>> import chess_spectral, chess_spectral_4d
>>> chess_spectral.__version__ == chess_spectral_4d.__version__
True   # both derive from importlib.metadata.version("chess-spectral");
       # they cannot drift from each other or from the wheel.
```

### In-place (no install)

The legacy workflow still works: every test and analysis script uses
`sys.path.insert` to bootstrap off the `python/` directory, so
`pytest docs/chess-maths/chess-spectral/python/tests/` runs without any
install.

## Quick start (2D)

```python
>>> from chess_spectral import (
...     encode_2d, channel_energies, read_encodings, fen_to_pos,
...     ENCODING_DIM, CHANNELS,
... )

>>> pos = fen_to_pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
>>> enc = encode_2d(pos)
>>> enc.shape
(640,)
>>> ENCODING_DIM   # don't hardcode 640; the dim count may grow (see §19.11)
640

>>> channel_energies(enc)
{'A1': 0.0, 'A2': 19.845, 'B1': 45.2825, 'B2': 45.2825,
 'E': 322.57, 'F1': 88.77, 'F2': 1851.01, 'F3': 1507.65,
 'FA': 19.92, 'FD': 0.0}

# Read a whole game that was encoded by either C or Python
>>> hdr, arr = read_encodings("game.spectralz")  # transparent gzip
>>> arr.shape
(161, 640)
```

## Quick start (4D, 45 056-dim)

The 4D encoder runs on the `Z_8^4` hypercubic lattice with `B_4`
hyperoctahedral symmetry adaptation (per Oana & Chiru, *AppliedMath*
6(3):48, 2026). Output is a 45 056-dim float32 vector partitioned into
**11 channels of 4096 modes each**: `A1`, `STD4_X/Y/Z/W`,
`FIB_SYM_1/2/3`, `FA_PAWN_W`, `FA_PAWN_Y`, `FD_DIAG`.

```python
>>> from chess_spectral.fen_4d import parse
>>> from chess_spectral.encoder_4d import (
...     encode_4d, channel_energies_4d, CHANNELS_4D,
... )

>>> pos = parse("4d-fen v1: K@4,0,0,0; k@4,7,7,7")
>>> v = encode_4d(pos)
>>> v.shape, v.dtype
((45056,), dtype('float32'))

>>> energies = channel_energies_4d(v)   # per-channel L2 energies
>>> sorted(energies)
['A1', 'FA_PAWN_W', 'FA_PAWN_Y', 'FD_DIAG',
 'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
 'STD4_W', 'STD4_X', 'STD4_Y', 'STD4_Z']
```

The 4D **game-state** surface (move history, draw detection, FEN4
round-trip, promotion-piece argument) lives in `chess_spectral_4d`:

```python
>>> from chess_spectral_4d import GameState4D, apply_move, MoveHistory4D
>>> from chess_spectral_4d import bridge

# Load a placement from a FEN4 string (white-to-move by default)
>>> result = bridge.load_state("4d-fen v1: K@4,0,0,0; k@4,7,7,7")
>>> state = result['state']
>>> isinstance(state, GameState4D)
True

# apply_move(state, from_sq, to_sq, *, promote_to='Q') is the v1.4 API
>>> # state2 = apply_move(state, from_sq=4, to_sq=5, promote_to='Q')

# Draw status: priority threefold > 50-move > insufficient > stalemate
>>> bridge.get_draw_status(state, has_legal_moves=True)
{'ok': True, 'status': 'none'}
```

For raw move-rule logic (legal-move generation, check detection) on
`Z_8^4`, see `chess_spectral.phase_operators_4d` below.

## Quick start (QM extension, v1.5+)

The QM extension ships in **two layers**, mirroring the standard
physics split:

- **Kinematics** — `chess_spectral.qm_4d`. *What* states and operators
  look like: state space, observables, measurement structure, the
  `B_4` group action. Lifts encoder output to `ψ ∈ ℂ^{45056}`, exposes
  the 11-channel decomposition as a built-in projection-valued measure
  (PVM), builds five Hermitian piece-reach observables (rook / bishop /
  queen / king / knight) on the per-channel `ℂ^{4096}` factor, and
  ships the 384-element `B_4` unitary representation as a cached LUT.
- **Dynamics** — `chess_spectral.qm_4d_dynamics`. *How* states change:
  the 11 per-channel `u_move_*` builders for move-as-unitary
  transitions (discrete) plus `evolve_under_h0` for Zeno-style
  continuous time evolution between move boundaries.

Consumers that want a Pyodide-JSON-shaped surface use the
`chess_spectral.qm_4d_bridge` dispatch layer described in the next
section.

```python
>>> from chess_spectral.fen_4d import parse
>>> from chess_spectral.qm_4d import (
...     state_to_psi,
...     prob_channel, measure_channel_distribution,
...     channel_projector,
...     H_rook_4, H_bishop_4, H_queen_4, H_king_4, H_knight_4,
...     measure_observable_distribution,
...     b4_unitary_rep_4096, b4_unitary_rep_full,
...     expectation, is_normalized, is_hermitian, is_unitary,
... )

>>> pos = parse("4d-fen v1: K@4,0,0,0; k@4,7,7,7; R@0,0,0,0")
>>> psi = state_to_psi(pos, side_to_move=True)
>>> psi.shape, psi.dtype
((45056,), dtype('complex128'))
>>> is_normalized(psi)
True

# Born-rule channel measurement: probability mass per channel
>>> prob_channel(psi, c=0)            # A1 channel
3.3e-08
>>> probs = measure_channel_distribution(psi)   # all 11 channels
>>> abs(probs.sum() - 1.0) < 1e-10
True

# ⟨ψ|H_rook|ψ⟩ on the rook channel block
>>> # expectation(H_rook_4, psi[0:4096])    # H_piece_4 is sparse 4096x4096

# Born-rule eigenbasis distribution: |⟨φ_k|ψ⟩|² grouped by eigenvalue
>>> # eigvals, probs = measure_observable_distribution(H_rook_4, psi[0:4096])

# B_4 group action (384 elements). 4096-dim per-channel block, or the
# I_11 ⊗ U_4096(g) Kronecker extension to the full 45 056-dim space.
>>> # U = b4_unitary_rep_full(g)            # cached; sparse 45056x45056
```

The Hermitian piece-reach observables `H_rook_4`, `H_bishop_4`,
`H_queen_4`, `H_king_4`, `H_knight_4` are built on demand and cached.
They are real-symmetric on `ℂ^{4096}` with integer / near-integer
spectra (Hermiticity verified at floating residual ~5e-15; Pre-flight
2 in [`qm_4d.py`](chess_spectral/qm_4d.py)). Pawn observables break
Hermiticity under the standard inner product (directed push) — the
pseudo-Hermitian `η`-metric construction is deferred to v1.8+ per
[ADR-005](../docs/adr/qm_4d/ADR-005-pawn-pseudo-hermitian-eta-metric.md).

`b4_unitary_rep_4096(g)` and `b4_unitary_rep_full(g)` realize the
order-384 hyperoctahedral group as sparse unitaries on `ℂ^{4096}` and
`ℂ^{45056}` respectively (the latter is `I_{11} ⊗ U_{4096}(g)` — same
B_4 action applied independently to each of the 11 channels). Both are
cached per group element. `measure_observable_distribution(H, ψ)`
diagonalizes any Hermitian observable on `ℂ^{4096}` and returns the
Born-rule probability distribution over distinct eigenvalues.

**Move-as-unitary dynamics** (Phase 4, Track B) live in
`chess_spectral.qm_4d_dynamics`. The module ships per-channel builders
for **all 11 channels and both non-capture and capture moves**:

- `u_move_a1` — A_1 channel via projector-sandwich (B1).
- `u_move_std4` — STD4_X/Y/Z/W via similarity-transform; same-orbit
  is strict-unitary, cross-orbit returns a measurement-only marker
  (B3a, ADR-003 amendment).
- `u_move_fa_pawn` — FA_PAWN_W/Y via axis-parity-odd projector
  sandwich (B3b).
- `u_move_fib_meas` — FIB_SYM_1/2/3 via measurement-only re-encode
  (B3c, per the Phase 3.5 amendment to ADR-003 §3.3).
- `u_move_fd_diag` — FD_DIAG via rank-1 update + renormalization (B3d/e).
- `evolve_under_h0` + `H_FREE_4D` — Zeno-style continuous evolution
  between move boundaries, where `H_0 = -Δ` is the lattice Laplacian
  (B2, ADR-002).

## §17.1 Pyodide bridge surface (v1.5)

`chess_spectral.qm_4d_bridge` is the **consumer-facing bridge** —
the 7 §17.1 QM-extension methods plus 6 §17.5 dev/debug methods —
designed for Pyodide consumers (e.g., the chess4D-OC visualizer)
that need Pyodide-JSON-serializable returns and Float32 ψ-amplitudes
ready for `Float32Array` shader uploads.

```python
>>> from chess_spectral.qm_4d_bridge import (
...     # §17.1 (QM-extension surface)
...     get_qm_state, get_qm_density, apply_move_qm, apply_move_qm_full,
...     measure_at, get_density_matrix_of, get_probability_current,
...     get_qm_expectation,
...     # §17.5 (dev / debug surface)
...     get_version, get_encoder_shape, get_fen4_state, load_fen4,
...     load_jsonl_fixture, has_legal_moves,
... )

# Round-trip: load a FEN4, get ψ as Float32 interleaved, apply a move,
# get the updated ψ.
>>> r = load_fen4("4d-fen v1: K@0,0,0,0; k@7,7,7,7; R@1,0,0,0")
>>> state = r['state']

>>> r = get_qm_state(state, side_to_move=True)
>>> r['basisDim'], r['psi'].dtype, r['psi'].shape
(45056, dtype('float32'), (90112,))   # 2 × 45 056 — real+imag interleaved
>>> abs(r['normSq'] - 1.0) < 1e-6
True

# Per-cell density: |ψ|² summed across the 11 channels per cell
>>> r = get_qm_density(state)
>>> r['density'].shape, abs(r['density'].sum() - 1.0) < 1e-6
((4096,), True)

# Apply a move and get the assembled ψ_post (Float32 interleaved).
# move format: (from_sq, to_sq) as ints OR ((x,y,z,w), (x,y,z,w))
>>> # r = apply_move_qm_full(state, move=(1, 2))
>>> # r['ok'], r['psi'].shape
>>> # (True, (90112,))

# §17.5 debug surface
>>> get_version()['version']         # e.g., '1.5.0'
>>> get_encoder_shape()['totalDim']  # 45056
>>> get_encoder_shape()['channels']  # [{'name': 'A1', 'offset': 0, 'dim': 4096}, ...]
```

**Wire format** (`ComplexArray`, `Float32Array`-friendly): every ψ
return is a 1-D `Float32` array of length `2 * 45056 = 90112`, where
`psi[2k]` is `Re(ψ_k)` and `psi[2k+1]` is `Im(ψ_k)`. This matches the
§17.1 contract documented in the
[research notebook §17.1](../../chess_spectral_research_notebook.md).

**`apply_move_qm` vs `apply_move_qm_full`.** The low-level
`apply_move_qm` returns a per-channel dispatch dict (mixed `csr_matrix`
+ marker dict values) for consumers that want to reason about per-
channel structure. The high-level `apply_move_qm_full` does the
block-by-block assembly (`csr_matrix` → `U_chan @ ψ_pre[block]`;
marker dict → `psi_post_block` splice) and returns the assembled
`ψ_post` as Float32 interleaved. Most consumers want the `_full`
variant.

The B5 milestone (April 2026) closed the last unshipped channels, so
the bridge no longer raises for any move type — non-captures and
captures both succeed via the channels' B5 capture-path branches. See
[`qm_4d_bridge.py`](chess_spectral/qm_4d_bridge.py) for per-method
docstrings and [`qm_4d_dynamics.py`](chess_spectral/qm_4d_dynamics.py)
for the per-channel construction details.

**Deferred to v1.8+:**
- `get_density_matrix_of` (reduced density matrix; needs partial-
  trace machinery on channel labels).
- `get_qm_density(piece_id=...)` (per-piece marginal; same blocker).

Both raise `NotImplementedError` with a pointer to the v1.8+ milestone.
(v1.7.0 shipped the D1 / D2 native fast-path workstream — see the
"What's new in v1.7" section below — and rolled the partial-trace
work to a follow-up.)

## CLI

The 2D CLI (`chess-spectral`, entry point `chess_spectral.cli:main`)
mirrors the C `spectral` CLI subcommand-for-subcommand. Output is
**byte-identical** to the C binary on the same input — the
`spectral csv` command produces the same bytes on either side.

```bash
chess-spectral csv         game.spectralz -o game.csv
chess-spectral encode      -i game.ndjson -o game.spectralz -z
chess-spectral encode-fen  --fen "..."   -o single.spectral
chess-spectral compare     a.spectralz b.spectralz
chess-spectral query       game.spectralz --ply 30
chess-spectral heatmap     game.spectralz --ply 30 --channel A1
chess-spectral analyze     game.spectralz
chess-spectral export      game.spectralz -o game.json
chess-spectral version
```

The 4D CLI (`chess-spectral-4d`):

```bash
chess-spectral-4d tables-verify  --phase all
chess-spectral-4d encode-fen4    --fen4 "4d-fen v1: K@0,0,0,0; ..."
chess-spectral-4d encode-moves4  --moves game.ndjson4 -o game.spectralz4 -z
chess-spectral-4d corpus-gen     --games game1.ndjson4 game2.ndjson4 ...
chess-spectral-4d version
```

Both CLIs follow the `--help` discipline: every subcommand and every
argument has non-empty help text. Run `<cmd> --help` (or
`<cmd> <subcommand> --help`) before invoking; the immolation suite
gates this in CI.

## Layout

    chess_spectral/                # 2D + 4D encoder math + QM extension
      __init__.py                  # __version__ via importlib.metadata
      encoder.py                   # encode_2d(pos) → np.ndarray (encode_640 = legacy alias)
      frame.py                     # v2 .spectral[z] binary I/O + transparent gzip
      csv_export.py                # dist_prev / cos_prev / energies CSV
      cli.py                       # `chess-spectral` (2D CLI)
      phase_operators/             # 2D §11 phase-space move generator (1.2.0+)

      encoder_4d.py                # encode_4d(pos4) → float32(45056,)
      frame_4d.py                  # v3/v4 .spectralz4 binary I/O (legacy reader)
      frame_v5.py                  # v5 unified wire format (2D + 4D, 3 encoding modes; default for new writes from v1.6)
      tables_4d.py                 # B_4 group, lattice tables, eigenmodes
      fen_4d.py                    # FEN4 v1 placement-literal parser + serialize
      phase_operators_4d/          # 4D §13 phase-operator move engine (1.3.0+)

      qm_4d.py                     # Track A kinematic QM front-end (1.5.0+)
      qm_4d_dynamics.py            # Track B per-channel U_move builders (1.5.0+)
      qm_4d_bridge.py              # §17.1 + §17.5 Pyodide bridge surface (1.5.0+)

    chess_spectral_4d/             # 4D game-state surface (1.4.0+)
      __init__.py                  # GameState4D, Move4D, MoveHistory4D, apply_move, bridge
      move_history.py              # ply log, side-to-move, 50-move clock, repetition hash
      apply_move.py                # apply_move(state, from_sq, to_sq, *, promote_to='Q')
      bridge.py                    # load_state, get_draw_status, get_move_history,
                                   #   is_insufficient_material_2d
      cli.py                       # `chess-spectral-4d` (4D CLI)

    pyproject.toml                 # PEP 621 packaging metadata
    tests/                         # pytest suite (see test count below)

**Test count (post-v1.5):** 45 895 tests collected. Breakdown:
~44 876 parametric 4D phase-operator tests (the bulk), 81-test
end-to-end immolation suite (`test_smoke_e2e.py`, expanded from 41
for v1.5 surface coverage), 272 v1.5 QM tests across the kinematic
front-end (`test_qm_4d.py`, `test_qm_4d_z2_grading.py`), the Track B
B1..B5 dynamics gates (`test_qm_4d_dynamics_b{1,2,3a,3b,3c,3d,5}.py`),
and the §17.1/§17.5 bridge surface (`test_qm_4d_bridge_v15.py`),
plus 102 fast tests, 260 pawn-axis / phase-4d-check / phase-4d-
unobstructed tests, 92 2D phase_operators tests, and 210 v1.4
game-state tests. Run via
`pytest docs/chess-maths/chess-spectral/python/tests/`.

## Phase operators (2D, §11)

`chess_spectral.phase_operators` ships a phase-space move generator
and check detector (added in 1.2.0). The primitives compute all moves
and check relationships as modular arithmetic on a single integer per
square — `phi(r, c) = r·67 + c·7 mod 640` — rather than geometric
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
dests = occupation_aware_moves_c(board, "N", 0, 1, +1)
# -> frozenset({(2, 0), (2, 2)})   (a3 and c3)

phasecast_is_check(board)  # False on the starting position
```

Validation coverage and rationale: see
[`PHASE_OPERATOR_SUPPLEMENT.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md).

## Phase operators (4D, §13)

`chess_spectral.phase_operators_4d` (1.3.0+) is the 4D analogue —
mixed-radix tower with **modulus 145451** and ladder coefficient 14
(vs the 2D framework's 8). Validated against
[`python-chess4d-oana-chiru`](https://pypi.org/project/python-chess4d-oana-chiru/)
at **44 803** (state, origin, piece) cases for occupation-aware moves
and 232 cases for check detection.

```python
from chess_spectral.phase_operators_4d import (
    phi4,
    P_rook4, P_bishop4, P_queen4, P_king4, P_knight4,
    P_pawn4_white, P_pawn4_black,
    occupation_aware_moves_a_4d,    # phase-op candidates ∩ chess4d oracle
    phasecast_is_check_4d,
    move_leaves_king_in_check_4d,
)
```

Full design + experimental record:
[`PHASE_OPERATOR_SUPPLEMENT_4D.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md).

## When to use what

The 2D and 4D encoders are independent build targets that share table
generation discipline. Pick by what you're encoding; the QM extension
sits on top of the 4D encoder.

| | 2D (`chess_spectral`) | 4D (`chess_spectral` + `chess_spectral_4d`) |
|--|--|--|
| Encoding dim | 640 | 45 056 |
| Lattice | `Z_8 × Z_8` | `Z_8^4` |
| Symmetry group | `D_4` (order 8) | `B_4` hyperoctahedral (order 384) |
| Game rules | python-chess (`fen_to_pos`) | Oana & Chiru (`python-chess4d-oana-chiru`) |
| Channels | 10 (`A1, A2, B1, B2, E, F1, F2, F3, FA, FD`) | 11 (`A1, STD4_X/Y/Z/W, FIB_SYM_1/2/3, FA_PAWN_W/Y, FD_DIAG`) |
| Phase operators | `phase_operators` (1.2.0+) | `phase_operators_4d` (1.3.0+) |
| QM extension | not yet shipped | `qm_4d` + `qm_4d_dynamics` + `qm_4d_bridge` (1.5.0+) |

Python vs C — same encoders on either side, byte-identical output:

| | C (`../src/`) | Python (this package) |
|--|--|--|
| Throughput | µs/encode | ms/encode |
| REPL / notebooks | ✗ | ✓ |
| LLM-pasteable | binary | code |
| `scipy.linalg` exploration | ✗ | ✓ |
| Embeds in mobile / web (Pyodide) | ✓ | ✓ (Pyodide) |
| Exact numerical reference | tables baked at build | rebuilt from primitives |

Develop new channels in Python first (faster iteration, `scipy.linalg`
at hand, no rebuild loop). Once the math is frozen, port to C and
verify parity via the test suite — the critical test is
`test_csv_matches_c_byte_for_byte` (2D) /
`test_e2e_spectralz4_parity.py` (4D), which assert the C-produced
encoded bytes equal the Python-produced bytes.

## See also

- **Cross-disciplinary applications** — research notebook §15
  ([`chess_spectral_research_notebook.md`](../../chess_spectral_research_notebook.md))
  for the framing of chess-spectral as a `H(4, 8)` Hamming-scheme
  toolkit with `B_4`-equivariant frozen featurizer and Born-rule
  loss hooks.
- **§17 bridge contracts** — same notebook, §17.1 / §17.5 for the
  consumer-facing method specs that this package implements.
- **4D notebook** — [`chess_spectral_4d_notebook.md`](../../chess_spectral_4d_notebook.md)
  for the 4D-specific research record (encoder injectivity, B_4
  spectral identity, qm_4d pre-flight findings).
- **Track B ADRs** — [`docs/adr/qm_4d/`](../docs/adr/qm_4d/) for the
  design record of the v1.5 QM extension:
  - ADR-001 phase convention for unitary moves
  - ADR-002 time-evolution semantics (continuous H_0 between move
    boundaries; `evolve_under_h0`)
  - ADR-003 per-channel move transformation (+ Phase 3.5
    orbit-restriction amendment for cross-orbit STD4 / FIB_SYM
    measurement-only re-encode)
  - ADR-004 Z_2 superselection structure (side-to-move sign
    multiplier, resolves the 8-collision encoder hash issue)
  - ADR-005 pawn pseudo-Hermitian η-metric (deferred to v1.8+)
  - `PHASE_3_5_PROBE_RESULTS.md` — empirical probe record that drove
    the ADR-003 amendment.
- **Pawn-axis split (v1.1.1)** — Oana & Chiru Definition 11; the
  encoder splits the pawn antisymmetric channel into W-axis and
  Y-axis sub-channels (`FA_PAWN_W`, `FA_PAWN_Y`) and grew from
  40 960-dim to 45 056-dim. See `encoder_4d.py` header for the
  rationale.
