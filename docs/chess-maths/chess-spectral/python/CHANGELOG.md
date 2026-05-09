# Changelog

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.13.0] — 2026-05-09

B-spike-3 from notebook §20.15 ships (partial): **encoder-eval
speedup work** — bench harness + `spectral_hybrid` evaluator
that computes channel energy directly from a `SpectralBIPHybrid2D`
(skipping the float decode) + LRU-cached wrapper + float32
sibling + diagnostic baselines. **§20.15 acceptance gate met for
the cache-hit path:** ~15× faster than `spectral_float64` at the
warm-LRU steady state. No breaking changes vs 1.12.x.

### Why this is the 1.13.0 ship

§20.15's three-tier B-spike phasing's fourth leg — make the
spectral evaluator's hot path faster for the §16 search engine and
chess4D-OC consumers. The user-mandated discipline: **bench harness
first; speedup claims must come from measured numbers on a fixed
corpus**. No CHANGELOG entry without bench-validated deltas.

### Empirical findings (notebook §20.19)

Bench corpora: 5 opening + 5 midgame + 5 endgame FENs; 500 iters
per (variant × position); median-of-medians per corpus reported.

| Variant | Opening (µs) | Midgame (µs) | Endgame (µs) | vs float64 baseline |
|---|---|---|---|---|
| material (reference) | 4 | 8 | 2 | — |
| **spectral_float64** (1.0–1.12.x default) | **540** | **511** | **233** | 1× |
| qm | 1280 | 1690 | 1276 | 2-3× slower |
| spectral_float32 | 747 | 787 | 350 | **null** (no consistent win) |
| spectral_hybrid_8bit_full (encode+eval) | 1079 | 1111 | 656 | 2× slower |
| **spectral_hybrid_8bit_from_cache** | **36** | **38** | **37** | **~15× / ~14× / ~6× faster** |
| **spectral_hybrid_8bit_lru** (warm cache) | **35** | **36** | **39** | **~15× / ~14× / ~6× faster** |

**Headline:** the cache-hit path (a) and LRU-cached wrapper (b)
deliver ~15× speedup at the warm-LRU steady state. The full
encode+eval hybrid path (a-with-encode) is *slower* than the
float64 baseline because the extra quantization step adds work;
the speedup only materializes when the hybrid form is precomputed
and reused.

**Null result:** path (d) — float32 downstream of the float64
encoder — shows no consistent speedup. Encoder cost dominates
(~700 µs) and the float32 cast adds ~50 µs of conversion work.
Mirrors the ephemerides two-stage architecture (complex128 →
complex64) but only wins when the encoder itself goes float32-
native, which is a separate ship.

**Deferred:** path (c) — Pyodide pure-int loop. Can't be
bench-validated from CPython (numpy is faster than pure-Python on
CPython for these arrays). The win lives on Pyodide / WASM where
numpy-on-WASM has per-call overhead. Picks up when chess4D-OC's
Pyodide profile surfaces an empirical bottleneck.

### Added — `chess_spectral.engine.eval.spectral_hybrid` module

- `evaluate(pos, side, *, magnitude_bits=8)` — full encode + eval
  path; bench-comparable to `spectral.evaluate` (slightly slower
  due to the quantization step).
- `evaluate_from_hybrid(hybrid, side)` — cache-hit fast path;
  takes a precomputed `SpectralBIPHybrid2D` and skips encoding
  entirely. **The big-speedup entry point** — ~15× faster than
  `spectral_float64` at warm-LRU steady state.
- `channel_energies_from_hybrid(hybrid)` — per-channel energy
  computation directly from integer storage. The mathematical
  identity: `‖v_c‖² = Σᵢ (sign × mag)² = Σᵢ mag²` (sign cancels
  in squared sum), so use uint8² sum + per-channel scale²
  multiply.

### Added — `chess_spectral.engine.eval.spectral_hybrid_cache` module

- `HybridCache(max_size=10000)` — LRU cache of
  `SpectralBIPHybrid2D` keyed by position-dict hash. Tracks
  `hits` / `misses` / `hit_rate` for diagnostic output.
  Supports `move_to_end` LRU semantics on access; evicts least-
  recently-used on overflow.
- `make_cached_evaluator(*, magnitude_bits=8, cache_size=10000,
  weights=None)` — factory returning `(evaluator_fn, cache)`. The
  `evaluator_fn` is suitable for `SearchOptions.evaluator`. Models
  the §16 search-engine integration shape; a search at depth 4-6
  with typical 30-70% TT hit rates should see 1.4-3.5× search-time
  speedup.

### Added — `chess_spectral.engine.eval.spectral_float32` module

- `evaluate(pos, side, *, weights=None)` — float32 downstream
  variant. Mirrors the ephemerides two-stage architecture
  (notebook §20.19; ephemerides notebook line 15). Shipped as a
  build-block sibling for the float32-native encoder work
  (deferred), even though the standalone bench shows null.
- `channel_energies_f32(v)` — per-channel L2 energy in float32.

### Added — `tests/bench_spectral_eval.py`

Diagnostic benchmark harness. Variants registered as plug-ins;
adding a new variant is one decorator + one import. Corpora:
opening (5 FENs), midgame (5), endgame (5). Reports mean / median
/ p95 / min / max in µs per (variant × position). Output: human
table to stdout + structured JSON via `--output PATH`. The 1.13.0
baseline + post-implementation results live at
`tests/bench_baselines/before_1.13.0.json` and
`tests/bench_baselines/after_b_spike_3_partial.json`.

### Added — 33 immolation tests in `tests/test_spectral_hybrid_eval.py`

- Channel-energy parity: hybrid agrees with float64 baseline
  within 5% relative on every channel for the 6-FEN representative
  corpus.
- Sign-of-score agreement: hybrid evaluator's sign matches
  float64 baseline (the load-bearing search-correctness property).
- Magnitude envelope: hybrid score within 5% relative of float64.
- 4-bit hybrid sign agreement (looser tolerance — still exact
  on the corpus).
- HybridCache LRU semantics: empty start, miss-then-hit, LRU
  eviction policy, hit/miss counter accuracy.
- `make_cached_evaluator` integration: returns callable + cache;
  distinct positions hash to distinct keys; second pass is all
  hits.
- `spectral_float32` sign agreement within 1e-4 relative of
  float64 baseline.
- Cached-evaluator-vs-baseline corpus integration check (the
  search-correctness property at the cache layer).

### §16.7 amendment — Othello prior contamination

Notebook §16.7 has been amended (2026-05-09) to flag that the
Edax-spectral-Reversi finding (+243 ELO at L6, decays to 0 at L10+)
came from an ML-augmented fork of vanilla Edax. The spectral-
weights contribution can't be cleanly separated from the ML
black-box's contribution; the depth-decay claim is not load-
bearing. **B-spike-3 is no longer gated on whether chess
replicates the Othello result**; tournament validation is open
empirical work for chess to do on its own.

### What this 1.13.0 does NOT do

- Does not modify the existing `spectral.evaluate` path. 1.0–1.12.x
  consumers see no behavior change.
- Does not change `encode_640` / `encode_4d`. C parity tests pass
  unchanged.
- Does not implement a float32-native encoder (deferred — touches
  encoder.py + tables.py + C parity).
- Does not implement Pyodide-friendly pure-Python channel-energy
  loop (deferred until chess4D-OC bench surfaces it).
- Does not run a §16 tournament. The cached evaluator is wired to
  plug into search but tournament validation is Phase 7+.

### Notebook updates

- §16.7 amendment — Othello data ML-contamination disclaimer.
- §20.19 — B-spike-3 implementation update with empirical bench
  numbers + cross-pollination ack to ephemerides Phase 9 cosine
  LUT + Q-format integer-frequency design.
- §20.20 (renumbered from §20.19) — joint progress summary table
  updated to mark B-spike-3 shipped (partial); 4 of 5 phases now
  shipped.
- §20.21 / §20.22 (renumbered from §20.20 / §20.21) — sibling
  project sections.

## [1.12.0] — 2026-05-04

B-spike-2 from notebook §20.15 ships: **encoder BIP-hybrid** —
sign × magnitude factoring across the spectral encoder's per-dim
output. New module `chess_spectral.encoder_bip_hybrid`. Sign packs
as 1 bit per dim (algebraically exact); magnitude quantizes to
4 or 8 bits per dim with per-channel scaling. **§20.15 acceptance
gate met**: cosine-sim ≥ 99.5% median + ≥ 95% worst-case on 2D
and 4D test corpora at 8-bit magnitude. No breaking changes vs
1.11.x; existing `encode_640` / `encode_4d` API unchanged.

### Why this is the 1.12.0 ship

§20.15's three-tier B-spike phasing's third leg. After 1.10.0
shipped sheet-block BIP (B-spike-1a) and 1.11.0 shipped the
ALU-native phase-operator engine (B-spike-1b), the encoder
hybrid is the natural next step — it answers the §20.12 question
of whether the encoder's per-channel magnitude data is
quantizable to integer-native form without losing the cosine-sim
discriminative power downstream consumers depend on.

The empirical answer: **yes at 8-bit per dim, with comfortable
margin** (median 0.999996, worst 0.999996 on the 7-FEN 2D
corpus; 0.999979 on canonical Oana-Chiru 4D startpos).

### Empirical finding worth recording

**4-bit hybrid passes for 2D but lands just below the 99.5%
threshold for 4D** (4D canonical OC: 0.994358). Notebook §20.18
documents this as a research finding: the 45,056-dim 4D encoder
accumulates more cumulative quantization error at 4-bit than the
640-dim 2D encoder does, even though per-dim relative error is
the same. 8-bit is the safe default for 4D; 4-bit is suitable
for 2D where the 5.8× compression matters and ~0.1% cosine-sim
degradation is acceptable.

### Storage budget

| Encoding | 2D bytes | 4D bytes | 2D compression | 4D compression |
|---|---|---|---|---|
| float32 baseline | 2560 | 180,224 | 1× | 1× |
| BIP-hybrid 8-bit | 760 | 50,732 | **3.4×** | **3.6×** |
| BIP-hybrid 4-bit | 440 | 28,204 | **5.8×** | **6.4×** |

Sign bits: 80 / 5,632 bytes (1 bit per dim). Magnitude scales:
40 / 44 bytes (10 / 11 channels × 4-byte float32). Magnitude
payload: 320-640 bytes (2D) / 22-45 KB (4D) depending on bit
budget.

### Added — `chess_spectral.encoder_bip_hybrid` module

- `SpectralBIPHybrid2D` / `SpectralBIPHybrid4D` dataclasses (frozen).
  Three integer/byte-array fields per instance: `sign_packed` (bytes),
  `magnitude_scales` (np.ndarray float32, per-channel), `magnitudes`
  (np.ndarray uint8 — packed nibbles for 4-bit, plain bytes for 8-bit).
- `encode_2d_bip_hybrid(pos, *, magnitude_bits=8, vals=None)` — encodes
  via `encode_640` then factors. Returns `SpectralBIPHybrid2D`.
- `encode_4d_bip_hybrid(pos4, *, magnitude_bits=8, vals=None)` — 4D
  analog. Returns `SpectralBIPHybrid4D`.
- `decode_2d_bip_hybrid(hybrid)` / `decode_4d_bip_hybrid(hybrid)` —
  reconstruct float64 vector. Lossy at the magnitude-quantization
  level; sign-bit storage is exact (decoded sign matches original
  on every dim where decoded magnitude is non-zero).
- `cosine_similarity_hybrid_2d(a, b)` / `cosine_similarity_hybrid_4d`
  — pair-wise cosine similarity between two hybrid vectors via
  decode then dot product. Returns 0.0 if either vector has zero
  norm.
- `round_trip_cosine_sim_2d(pos, *, magnitude_bits=...)` /
  `round_trip_cosine_sim_4d(pos4, ...)` — the §20.15 acceptance
  metric. Compares the float32 baseline vs the hybrid round-trip
  reconstruction.
- `bip_hybrid_storage_bytes_2d(magnitude_bits)` /
  `bip_hybrid_storage_bytes_4d(magnitude_bits)` — documented
  storage budget in bytes per position.
- Layout constants: `DEFAULT_MAGNITUDE_BITS = 8`,
  `VALID_MAGNITUDE_BITS = (4, 8)`, `N_CHANNELS_2D = 10`,
  `CHANNEL_DIM_2D = 64`, `N_CHANNELS_4D = 11`,
  `CHANNEL_DIM_4D = 4096`.

### Added — bridge surface (`chess_spectral_4d.bridge`)

- `bridge.encode_position_2d_bip_hybrid(pos, magnitude_bits=8)` —
  hybrid-encode a 2D position. Returns
  `{"hybrid": {"sign_packed_bytes": list[int],
  "magnitude_scales": list[float], "magnitudes_bytes": list[int],
  "magnitude_bits": int}}`. Plain Python lists across the WASM
  boundary.
- `bridge.encode_position_4d_bip_hybrid(pos4, magnitude_bits=8)` —
  4D analog. Note: 4D magnitudes_bytes is 22,528 entries at 4-bit /
  45,056 at 8-bit. Pyodide consumers should consider TypedArray
  binary transport rather than JSON-list serialization for hot
  paths.

### Added — 62 immolation tests in `tests/test_encoder_bip_hybrid.py`

- Storage budget verification (matches documented values per
  bit budget).
- Sign-bit packing / unpacking round-trip (640-bit and 45056-bit).
- 4-bit nibble packing / unpacking round-trip.
- 2D round-trip shape + dtype + per-channel magnitude bounds.
- **Sign bit storage exact across the corpus** at every magnitude
  budget (the load-bearing BIP-clean property).
- **§20.15 acceptance gate** at 8-bit on the 7-FEN 2D corpus
  (median + worst-case ≥ 99.5% / 95%).
- 4-bit 2D acceptance test (also passes; the empirical finding
  from §20.18).
- 4D round-trip on canonical Oana-Chiru §3.3 startpos.
- 4D 8-bit acceptance gate.
- **4D 4-bit research finding lock** — sim is in [0.99, 0.999]
  band; if it shifts, investigate.
- Pair-wise cosine-sim (`cosine_similarity_hybrid_*`) approximates
  the float baseline within 1% absolute deviation.
- Self-similarity ≈ 1.0 (sanity check).
- Zero-vector round trip exactly preserves zeros.
- Error cases: invalid `magnitude_bits` raises ValueError;
  `storage_bytes_*` rejects non-(4,8).

### Notebook updates

- §20.18 — implementation update for B-spike-2 with the empirical
  acceptance numbers, the 4D 4-bit finding, the per-channel
  optimization opportunities deferred to 1.13.0+, and cross-
  pollination notes for ephemerides-spectral.
- §20.19 — joint progress summary table across §20: B-spike-1a /
  1b / 2 shipped; 3 / 4 parked.

### What this 1.12.0 does NOT do

- Does not implement per-channel optimizations from §20.12. A1 /
  FA / E channels could benefit from non-uniform encoding (skip
  sign for A1, skip magnitude for FA, complex-int for E). 1.13.0+
  if empirically motivated.
- Does not enter the v5 wire format. Wire-format integration (v5
  mode 2 XOR-stream is a natural fit for the sign-portion bit
  pattern) deferred per §19.12 + §20.16; picks up when a consumer
  needs persisted hybrid frames.
- Does not implement B-spike-3 (search-engine evaluator hot path
  with hybrid vectors). Independent ship; depends on §16 search
  integration surface.
- Does not modify `encode_640` / `encode_4d` defaults. Existing
  API surface unchanged. C parity tests pass.
- Does not modify the 1.10.0 sheet block or 1.11.0 phase-operator
  engine.

## [1.11.0] — 2026-05-04

B-spike-1b from notebook §20.15 ships: **ALU-native phase-operator
move generator**. The §11 phase-operator engine — already
integer-arithmetic at the core, already BIP-isomorphic at the
group-theoretic level over `Z_640` — gains a public integration
entry point that doesn't require a `python-chess.Board` argument.
Pure ALU-native pseudo-legal move generation for Pyodide / WASM /
non-Python downstream consumers. No breaking changes vs 1.10.x;
existing API surface unchanged.

### Why this is the 1.11.0 ship

The §20.13 audit established that the engine was already
BIP-isomorphic — phase composition is integer addition modulo
`Z_640`, identical in shape to BIP's `(φ_1 + φ_2) mod 2^K`. What
was missing for downstream consumers was the integration entry
point. Existing `occupation_aware_moves_{a,b,c}` all required a
Board argument because they derived the occupation field, EP
square, and castling-rights state from python-chess. Solutions B
and C of §11.4 are pure phase arithmetic on `dict[phase, charge]`
occupation fields; they just didn't have a public adapter that
fed them encoder-format input directly.

### Added — `occupation_field_from_pos_dict` and `ep_phase_from_ep_file`

Two pure-phase adapters in
`chess_spectral.phase_operators.occupation_field`:

- `occupation_field_from_pos_dict(pos)` — encoder-format
  `{sq: piece_char}` → `{phase: charge}`. Counterpart of the
  existing `occupation_field_from_board(board)`. Accepts both
  int- and str-keyed pos dicts (NDJSON convention).
- `ep_phase_from_ep_file(ep_file, side_to_move_white)` — derive
  the EP target's phase from the file index + side-to-move.
  Mirrors the 1.9.0 `SheetState.ep_file` semantics (white-to-move
  ⇒ EP target on rank 5; black-to-move ⇒ rank 2).

### Added — `phase_only_pseudo_legal_moves` integration entry point

New module `chess_spectral.phase_operators.alu_native` exporting:

- `phase_only_pseudo_legal_moves(pos, side_to_move_white, *,
  ep_file=None) -> list[(from_sq, to_sq, promo)]` — pure
  ALU-native pseudo-legal move generator. Iterates pieces of the
  side to move, dispatches to the per-piece destination
  computations from Solution B, expands pawn promotions into 4
  target moves (Q/R/B/N).
- `PROMOTION_TARGETS` — `('Q', 'R', 'B', 'N')`, the canonical
  promotion-target ordering.

**Pseudo-legal in the python-chess sense:** respects piece
geometry, occupation (own-piece blocking, opposite-charge
capture), pawn double-push from starting rank, en passant,
promotion. Does NOT include castling (deferred — needs attack
map) or check filtering (deferred — needs occupation-by-piece-type
refactor of `phasecast_is_check`).

### Acceptance gate — parity vs `python-chess.pseudo_legal_moves`

`tests/test_phase_operator_alu_native.py` includes a parametrized
parity test against `board.pseudo_legal_moves` on a representative
8-FEN corpus (opening, middlegame, endgame, EP-active,
promotion-imminent). For every position, the move set returned by
`phase_only_pseudo_legal_moves` matches `board.pseudo_legal_moves`
exactly after excluding castles. **All 26 tests pass on first
implementation.**

### Diagnostic benchmark

`tests/bench_phase_operator_movegen.py` measures absolute cost vs
the existing paths:

| Position | python-chess | Solution B (per-piece × 16) | **ALU-native** |
|---|---|---|---|
| Opening (startpos) | ~73 µs | ~1970 µs | **~190 µs** |
| Middlegame (Italian, both castled) | ~82 µs | ~2150 µs | **~250 µs** |
| Endgame (K+R vs K) | ~23 µs | ~80 µs | **~41 µs** |

ALU-native is ~2-3× slower than Cython python-chess (expected),
but **structurally faster than Solution-B-per-piece-loop**
because it builds the occupation field once per position instead
of per-piece. The value is **portability** (no python-chess
dependency on the hot path), not raw speed against Cython.

### Documented `Z_640` wire contract (notebook §20.17)

The constants `MODULUS`, `ROW_GEN`, `COL_GEN`, `DIAG_NE_SW_GEN`,
`DIAG_NW_SE_GEN`, `KNIGHT_SHIFTS`, `KING_SHIFTS` are now part of
the public API surface (re-exported from
`chess_spectral.phase_operators`). They do not move without a
major version bump.

§20.17 also reiterates the §20.13 clarification that the
"8-generator coprimality" is a **spectral** property (irrational
pairwise eigenvalue ratios), not an arithmetic-modular CRT
decomposition. The engine uses a single composite `Z_640`
modulus, not 8 separate `Z_p` rings. `Z_640` does not get the
"free overflow" semantics that BIP encoding gets in `Z_{2^32}`
(notebook §20.11) — every `(a + b) % MODULUS` is an explicit
modulo op, cheap but not zero. Worth noting for cross-pollination
with the antikythera-spectral / ephemerides-spectral BIP work
which uses the power-of-2 path.

### Added — 26 immolation tests in `tests/test_phase_operator_alu_native.py`

- Encoder-sq ↔ chess (rank, file) round trip for all 64 squares.
- `occupation_field_from_pos_dict` parity with
  `occupation_field_from_board` on 8 representative FENs.
- `ep_phase_from_ep_file` parity with `ep_phase_from_board` on
  EP-active positions (post-1.e4, post-1.e4 d5).
- **The acceptance gate**: parametrized parity vs python-chess
  pseudo-legal moves (excluding castles) on the 8-FEN corpus.
- Targeted edge cases: pawn promotion expansion (4 targets),
  EP capture only with `ep_file` supplied, side-to-move
  filtering, str-keyed pos dict acceptance, pseudo-legal count
  at startpos = 20.

### What this 1.11.0 does NOT do

- Does not change the existing `occupation_aware_moves_{a,b,c}`
  functions. They retain their Board-fronted signatures for
  back-compat.
- Does not implement castling in the ALU-native path. Pure-phase
  castling generation is doable but needs an attack map; deferred
  to a 1.12.0+ follow-up when a consumer needs it.
- Does not refactor `phasecast_is_check` to take an occupation
  dict directly. Still takes a Board; the ALU-native path's
  output is pseudo-legal-without-check-filter. Caller is
  responsible for downstream check filtering until the refactor
  lands.
- Does not modify the encoder. The 640 / 45056-dim spectral
  payload is untouched. C parity tests pass unchanged.
- Does not implement BIP for the encoder channels (B-spike-2;
  next ship in the §20.15 phasing).

### Notebook updates

- `chess_spectral_research_notebook.md` §20.17 — implementation
  update for B-spike-1b: scope, acceptance, benchmark numbers,
  Z_640 wire contract, what's deferred for 1.12.0+, cross-
  pollination notes for ephemerides-spectral.

## [1.10.0] — 2026-05-04

B-spike-1a from notebook §20.16 ships: **BIP-encoded sheet block**
(integer-native form of the 1.9.0 non-Markovian aux block, ~29×
compression with bit-exact round trip on the legal state space).
No breaking changes vs 1.9.x. Same algebraic content, smaller
storage footprint, ALU-native operator fast paths.

### Why this is the 1.10.0 ship

The 1.9.0 sheet block ships an 11-dim float64 aux block (88 bytes
per position) for content that is overwhelmingly *categorical* —
4 castling bits + 1 EP-active + 3 EP-file + 1 side-to-move +
2 repetition + Z₁₀₁ halfmove (cos/sin pair). The new BIP
representation packs the same content into **3 bytes** (uint16
categorical + uint8 halfmove). Notebook §20.10-§20.16 captures
the prior art (Gemini's `bip_instrument.py` antikythera prototype:
305× speedup, 0.011° error = static-Laplacian propagator floor,
NOT bit-serialization loss) and the chess synthesis (sheets are
unique to chess; ephemerides has no non-Markov state to learn
from). The first move of the §20.15 three-tier B-spike phasing.

### Where BIP wins vs the 1.9.0 float path

- **Pyodide / chess4D-OC consumers** — direct uint16 bit-ops are
  native to JavaScript Number / WASM; no Python interpreter
  overhead, no `python-chess.Board` reconstruction. ~50-100×.
- **Batch retrieval over saved corpora** — filtering 10,000
  stored vectors for "any castling alive" is one numpy
  `cats[:] & 0xF` against a packed corpus, vs 10,000
  `python-chess.Board(fen)` reconstructions. ~3 orders of magnitude.
- **Hamming-distance similarity** on the categorical portion is
  sharper than float cosine-sim for binary state.
- **Wire format** — v5 mode-2 XOR-stream compression of sheet
  bits is now natively the right shape. Each ply changes few
  categorical bits; `categorical XOR previous_categorical` is
  mostly zero, compresses well.

### Where BIP does NOT win — depth-1 floor still holds

Per §19.10, single-position queries on python-chess (one
`int & mask` for castling, one attribute load for EP) cannot be
undercut by float-numpy slice + decode. **The same floor applies
to BIP's bit-shift + AND.** Both are at the per-call latency
floor. BIP's wins are at scale, not at single-call latency.

### Added — `chess_spectral.sheets_bip` module

- `SheetStateBIP` dataclass (frozen): two integer fields
  (`categorical: uint16`, `halfmove_clock: uint8`). Bounds-checked
  on construction (rejects out-of-range values, non-zero reserved
  bits).
- `encode_sheet_state_bip(state) -> SheetStateBIP` — convert
  1.9.0 `SheetState` to BIP form. Edge-case handling matches
  1.9.0 (clamp halfmove > 100, saturate repetition > 2,
  ep_file=None encodes as ep_active=0 + ep_file=0).
- `decode_sheet_state_bip(packed) -> SheetState` — lossless
  inverse on the legal state space.
- **Round-trip exact**: 87,264 cases verified by
  `tests/test_sheets_bip.py` (864 categorical × 101 halfmove).

### Added — operator fast paths

Single-integer-op queries against the categorical portion:

- `castling_alive(packed) -> bool` — any castling right alive
- `kingside_castling_alive(packed)` / `queenside_castling_alive`
- `white_castling_alive` / `black_castling_alive`
- `ep_target_active(packed) -> bool` — ep_active bit
- `ep_file_from_bip(packed) -> Optional[int]` — file 0..7 or None
- `side_to_move_white_from_bip(packed) -> bool`
- `repetition_count_from_bip(packed) -> int` — 0/1/2
- `fifty_move_rule_triggered(packed) -> bool` — halfmove ≥ 100
- `threefold_claimable(packed) -> bool` — repetition ≥ 2

Each is a single bit-mask + comparison; no FPU, no Python-loop
overhead.

### Added — distance metrics

- `hamming_distance_categorical(a, b) -> int` — Hamming distance
  over the 11 categorical bits. Useful for corpus-similarity
  retrieval where binary state distinctions matter (positions
  with different castling rights vs same).
- `halfmove_distance(a, b) -> int` — absolute integer difference
  of half-move clocks (one-sided metric on Z₁₀₁).

### Added — bridge surface (`chess_spectral_4d.bridge`)

Three new functions for chess4D-OC / Pyodide consumers; numpy-
free across the WASM boundary:

- `bridge.get_sheet_state_bip(state_or_board)` — returns
  `{"ok": True, "sheet_bip": {"categorical": int,
  "halfmove_clock": int}}`. Dispatches on `GameState4D` vs
  python-chess Board.
- `bridge.encode_sheet_aux_bip(sheet_dict)` — serialize a sheet
  dict to BIP form. Returns `{"categorical": int (uint16),
  "halfmove_clock": int (uint8)}`.
- `bridge.decode_sheet_state_from_bip(categorical, halfmove_clock)`
  — inverse. Validates input ranges before decoding.

### Added — 33 immolation tests in `tests/test_sheets_bip.py`

- Exhaustive 87,264-case round trip (864 categorical × 101
  halfmove) — the load-bearing acceptance gate.
- Operator fast-path parity vs the 1.9.0 SheetState across the
  full state space (8 operators × 864 × 6 halfmove samples).
- Edge cases: ep_file=None, halfmove clamp at 100, repetition
  saturation at 2, reserved-bit zero invariant.
- Distance metrics: Hamming self-distance zero, Hamming castling
  one-bit diff, full-state distance counts correctly accounting
  for binary representation of the repetition field (rep=2 sets
  only bit 10, not 2 bits).
- python-chess Board factory parity (startpos, post-e4 EP).
- 4D `GameState4D` factory parity (canonical Oana-Chiru §3.3
  startpos).
- Bridge round trip (state → encode → decode → equality).
- Bridge error cases (missing fields, invalid ranges,
  unrecognized input types).

### What this 1.10.0 does NOT do

- Does not modify the 1.9.0 float64 sheet block. Both
  representations ship side-by-side.
- Does not enter the v5 wire format. Wire-format integration
  (the natural follow-up given mode-2 XOR-stream's affinity for
  the BIP categorical packing) is still deferred per §19.12;
  picks up when a downstream consumer needs persisted BIP-
  encoded sheet frames.
- Does not change the encoder. The 640 / 45056-dim spectral
  payload is untouched. C parity tests pass unchanged.
- Does not promote the §11 phase-operator engine to public API.
  That's B-spike-1b in the §20.15 phasing; independent of this
  ship and can land separately when prioritized.
- Does not implement BIP for the encoder channels themselves.
  That's B-spike-2 (encoder hybrid), which depends on the
  bit-packing patterns this 1.10.0 establishes.

### Notebook updates

§20.10-§20.16 already shipped in PR #159 (the research artifact
preceding this implementation). 1.10.0 ships against the §20.16
implementation plan as written; no additional notebook updates
needed for this version.

## [1.9.1] — 2026-05-04

Polish on top of v1.9.0. README PyPI examples updated to use the
future-proof `encode_2d` alias, Roadmap link added to PyPI project
URLs, v5 wire format design decision recorded (sheets do **not**
ride in v5; in-memory and on-disk paths diverge intentionally —
see notebook §19.12). No code-behavior changes — encoder defaults
remain bit-for-bit identical to 1.9.0 / C parity.

### Changed

- **README.md** quick-start example uses `encode_2d` (the 1.9.0
  future-proof alias) instead of `encode_640`. Layout block in the
  README directory tree similarly switched. Section heading
  "Quick start (2D, 640-dim)" → "Quick start (2D)" since 640 is
  no longer a stable contract (sheets bumped 640 → 651, future
  channel embiggening may move it again — see notebook §19.11).
  The example now demonstrates querying `ENCODING_DIM` rather
  than hardcoding the value.
- **`pyproject.toml` + `pyproject-pure.toml`** add a
  `Roadmap` entry to `[project.urls]` pointing at
  [`docs/chess-maths/chess-spectral/ROADMAP.md`](../ROADMAP.md).
  PyPI surfaces this as a project-link badge alongside Homepage /
  Repository / Issues / Changelog / Notebook (2D) / Notebook (4D).
- **`ROADMAP.md`** refreshed from a stale "Current release: v1.6.0"
  to a v1.9.1 + 1.9.0 + 1.8.x + 1.7.x retrospective; v1.7-era
  candidates section relabeled to "v1.10+ candidates and parked
  spikes" with concrete pointers to S-spike-2 (sheet wire format),
  B-spike-1 (BSHDC side-car), Tier 2.1/2.2 (η-metric machinery),
  and the API-stability adoption pattern from §19.11.

### Added

- **`frame_v5.py` module-docstring section "Sheets and v5 (1.9.1+
  design decision)"** — documents that v5 frames do not carry the
  sheet aux block; rationale (existing corpus pattern preserves
  source, sheets are in-memory representation feature, no
  downstream consumer needs persisted sheet frames yet); future
  extension path (223 reserved bytes in the v5 header are
  available for `aux_dim` / `aux_offset` fields when a consumer
  needs them); recommended sidecar JSON pattern in the meantime.
- **Notebook §19.12** — "Sheets and the v5 wire format — deferred
  by design" — captures the same decision for the research record,
  with the in-memory-vs-on-disk path table that consumers should
  reference.

## [1.9.0] — 2026-05-04

Lands the §19 spike's Phase-1 sheet block (notebook §19, May 2026)
as a **representation-completeness** feature, plus a new
`legal-moves` CLI command for both 2D and 4D — the gap-filler that
closes the "no command-line legal-move-gen" hole flagged on the
1.9.0 prep thread.

### Why this is the 1.9.0 representation-only ship

The §19 spike originally proposed sheet blocks as a candidate speed
optimization for the non-spatial-geometry move operators (castling,
en passant). Empirical analysis of the 2D pipeline (notebook §19.10)
confirms the depth-1 floor: `python-chess`'s
`board.has_castling_rights()` is one int-AND, the same lookup the
sheet block would need to do via float→int conversion plus numpy
slice. We can't undercut that floor at single-position scale, and
the same logic holds against `Board4D.halfmove_clock >= 100` and the
hash-table threefold-repetition lookup. **1.9.0 ships sheet blocks
as a representation-only feature, not a speed feature.** No speedup
claim in the API surface, no benchmark harness, no fast-path
early-exit logic. The value is making encoder vectors self-
sufficient for downstream consumers of saved/transmitted vectors —
chess4D-OC, Pyodide pipelines, batch retrieval — that don't want
to reconstruct a python-chess `Board` or a `GameState4D` alongside
the vector.

### Added — Sheet aux block (§19 representation-only)

- New module `chess_spectral.sheets` with the 11-dim non-Markovian
  aux block:
  - `SheetState` dataclass (castling rights × 4, EP file, side to
    move, halfmove clock, repetition count).
  - `SheetState.from_chess_board(board)` factory lifts state from a
    `python-chess` Board (castling rights via
    `has_kingside_castling_rights` / `has_queenside_castling_rights`,
    EP file from `ep_square`, halfmove from `halfmove_clock`,
    repetition via `is_repetition`).
  - `SheetState.from_game_state_4d(state)` factory lifts state from
    `chess_spectral_4d.GameState4D`. Castling and EP slots are
    forced to neutral values per the Oana-Chiru ruleset (no
    castling, no en passant — see `spatial_4d/board.py` header);
    halfmove + side-to-move + repetition are populated.
  - `encode_aux_block(state) -> np.ndarray` — serialize to the
    11-dim float64 aux block. Halfmove encoded via Z_101 Fourier
    carrier (cos / sin pair) preserving clock-distance fidelity;
    castling / EP / side-to-move / repetition stored as direct
    binary or small-integer slots.
  - `decode_*` getters for individual slots and `decode_sheet_state`
    for the full round-trip recovery. Half-move recovery rounds to
    the nearest integer in [0, 100]; round-trip exact for all 101
    legal values.
- All eight sheets symbols re-exported at the top level
  (`from chess_spectral import SheetState, encode_aux_block, ...`).
- Layout constants: `SHEET_AUX_DIM = 11`, `SHEET_OFFSET_2D = 640`,
  `SHEET_OFFSET_4D = 45056`. Indexed slot positions
  (`SLOT_CASTLING_WK`, ..., `SLOT_HALFMOVE_SIN`, `SLOT_RESERVED`)
  are part of the wire contract; consumers should use the named
  constants instead of magic numbers.

### Added — Encoder hooks for sheet aux block

- `encode_640(pos, sheets=...)` — opt-in kwarg; when supplied,
  appends the 11-dim aux block, producing a 651-dim float64 vector.
  The first 640 dims are bit-for-bit identical to legacy / C
  encoder output (test_c_py_parity unchanged); aux ride at offset
  `SHEET_OFFSET_2D = 640`.
- `encode_4d(pos4, sheets=...)` — same opt-in kwarg; produces a
  45067-dim float32 vector. Aux block is cast to float32 for dtype
  consistency with the base encoder. First 45056 dims unchanged
  (test_c_py_parity_4d unchanged); aux at offset `SHEET_OFFSET_4D`.
- Default behavior of both functions is bit-for-bit unchanged from
  pre-1.9.0 — the `sheets` kwarg is opt-in and the legacy 640 / 45056
  output is the default.

### Added — `legal-moves` CLI command (closes the gap on the 1.9.0 prep thread)

- `chess-spectral legal-moves --fen "<fen>" [--format uci|san|json]
  [--with-sheets]` — enumerate the side-to-move's legal moves at a
  2D position. Default UCI output (one move per line); JSON format
  includes per-move flags (capture / castling / en-passant /
  promotion) plus optional sheet block. Stdin via `--fen -`. Uses
  `python-chess` for legal-move generation.
- `chess-spectral-4d legal-moves --fen4 "<fen4>" [--format
  compact|json] [--with-sheets] [--side-to-move ...] [--halfmove-
  clock N] [--fullmove-number N]` — analog for 4D-OC. Default
  compact format `x,y,z,w->x,y,z,w` with DP/EP/=Q tags for double-
  push, en-passant, and promotion; JSON output structured. Uses
  `Board4D.legal_moves()` (the native 4D move-gen via the graph-
  Laplacian-derived primitives).
- 12 immolation tests in `tests/test_legal_moves_cli.py` cover the
  startpos move counts, JSON structure, sheet-block presence,
  stdin input, and bad-FEN handling for both dimensions.

### Added — 28 immolation tests for the sheet aux block

`tests/test_sheets_aux_block.py` locks down:
- Aux block shape (11,) + dtype (float64).
- Default-state aux values (cos(0)=1, sin(0)=0, all other slots 0).
- Castling rights round-trip (8 parametrized combinations).
- EP file round-trip (None + files 0..7, 9 parametrized cases).
- Half-move clock round-trip for **every integer [0, 100]** (101
  parametrized cases) — exact recovery via atan2 + rounding.
- Half-move > 100 clamps to 100 (50-move rule has triggered).
- Half-move carrier always on the unit circle (cos² + sin² ≈ 1).
- Side-to-move round-trip (both directions).
- Repetition count round-trip (0/1/2) and clamping for values > 2.
- Aggregate `decode_sheet_state` full round-trip.
- 2D encoder integration: shape, dtype, base-preservation,
  aux-at-offset.
- 4D encoder integration: same four checks, with float32 dtype.
- `from_chess_board` factory lifts python-chess state correctly
  (startpos, post-double-push EP target, halfmove clock advance).
- `from_game_state_4d` factory: castling/EP slots zero per
  ruleset; halfmove + side-to-move + repetition populated.

### Added — Bridge surface for sheet aux block (Pyodide / chess4D-OC)

The `chess_spectral_4d.bridge` module gains three new functions
that round out the sheet-block surface for the `chess4D-OC` worker
and any other Pyodide / WASM consumer. The bridge contract holds
("plain dict, no numpy across WASM"); aux blocks cross the boundary
as plain `list[float]`.

- `bridge.get_sheet_state(state_or_board)` — extract the 11-dim
  non-Markovian sheet state from a `GameState4D` or a
  `python-chess.Board`. Dispatches by type. Returns
  `{"ok": True, "sheet": {...}}` with eight named fields.
- `bridge.encode_sheet_aux(sheet_dict)` — serialize a sheet dict
  to the 11-dim aux block as a plain `list[float]`. Returns
  `{"ok": True, "aux": [11 floats]}`.
- `bridge.decode_sheet_aux_from_vector(vec, offset)` — given an
  encoder vector (as a list of floats; numpy-free path) and the
  aux-block offset (640 for 2D, 45056 for 4D), decode the aux
  block back to a sheet dict. Returns
  `{"ok": True, "sheet": {...}}` or `{"ok": False, "error": "..."}`
  on a too-short vector.
- 13 immolation tests in `tests/test_bridge_sheets.py` cover the
  factory dispatch (4D GameState4D + 2D python-chess Board), the
  numpy-free return path, missing-field and short-vector error
  handling, and the full E2E composition (state → get → encode →
  decode round-trip).

### Added — `encode_2d` alias (future-proof against dim-count changes)

- `chess_spectral.encode_2d` is a permanent alias of
  `chess_spectral.encode_640`. Both names map to the same function
  in 1.9.0 and forward; `encode_640` is preserved for backward
  compatibility but the dim count (640) is **not a stable contract**
  — sheets bumped output to 651 already, future channel
  embiggening or non-Markov-state extensions may bump it further.
  New consumer code should prefer `encode_2d` (mirroring the 4D
  path's `encode_4d`) and query `chess_spectral.ENCODING_DIM` or
  `enc.shape[0]` rather than hardcoding 640. See notebook §19.11
  for the full future-work plan.

### Notebook updates

`docs/chess-maths/chess_spectral_research_notebook.md` gained:

- **§19.9** — implementation update: S-spike-1 shipped in 1.9.0
  with the 11-dim aux block as designed.
- **§19.10** — "Empirical bound: depth-1 bitboard floor": captures
  Steven's "we won't beat bitboards at depth 1" lemma, closes the
  speed thesis, recharacterizes 1.9.0 as a representation-only
  ship, and names the regimes where sheet blocks remain valuable
  (saved-corpus retrieval, Pyodide contexts without a python-chess
  Board, transmission contracts).
- **§19.11** — "Future work: dim-count is not a stable contract;
  rename `encode_640` → `encode_2d`": documents three forces on the
  encoder shape (sheet enrichment beyond Phase 1, channel
  embiggening, bit-serialized HDC enrichment per the antikythera
  /DE441 reference), recommends the future-proof API patterns
  (`encode_2d`, `ENCODING_DIM` query, `CHANNELS` iteration), and
  notes that no rename of `encode_4d` is needed since `4d` already
  factors out the dim-pinning.

## [1.8.1] — 2026-05-01

Closes the 1.8.0 wishlist's tier-1.4 (`initial_position()` factory)
by lifting the canonical Oana-Chiru §3.3 4D starting layout into
this package as the authoritative source. No API breaks vs. 1.8.0.

### Why this is its own release

The 1.8.0 PR (#152) deferred the canonical-start factory because
no FEN4 string for it lived anywhere in this repo — the value had
been "made up" downstream and the chess4D-OC visualizer was using
its own hand-rolled fixture. Now that the upstream paper's §3.3
spec ("4D Initial Position Specification") has been transcribed
into a programmatic constructor, the package itself can serve as
the canonical source going forward.

### Added — Canonical 4D initial position (wishlist tier 1.4)

- New module `chess_spectral_4d.initial_position` containing:
  - `STARTING_FEN4` — the canonical 4D Oana-Chiru initial position
    as a FEN4 v1 placement literal. **896 pieces** total: 448 white
    + 448 black, **28 kings per side**. Byte-stable across Python
    versions (`fen_4d.serialize` sorts pieces by ascending square
    index).
  - `initial_position() -> GameState4D` — factory that constructs
    a fresh `GameState4D` at the canonical layout. Equivalent to
    `GameState4D.from_fen(STARTING_FEN4)`; exists for ergonomics
    and so the chess4D-OC visualizer can drop its hand-rolled
    fixture-loading shim.
  - `central_slices()`, `white_only_slices()`, `black_only_slices()`,
    `empty_slices()` — helper sets that return the (z, w) slice
    classifications from §3.3:
    - `|C| = 4` (z ∈ {3, 4}, w ∈ {3, 4})
    - `|W_only| = 24`
    - `|B_only| = 24`
    - `|E| = 12`
    - Total: 64 ✓
- All five symbols re-exported at the top level
  (`from chess_spectral_4d import STARTING_FEN4, initial_position`).

### Implementation notes

- Uses 0-indexed FEN4 v1 coordinates throughout (paper §3.3 uses
  1-indexed; subtraction-by-1 documented in the module docstring
  and the slice helpers).
- Pawn axis assignment per Definition 11: even file (x ∈ {0, 2, 4,
  6}) → Y-oriented (`Py` / `py`); odd file (x ∈ {1, 3, 5, 7}) →
  W-oriented (`Pw` / `pw`).
- Standard 2D back-rank on each non-empty slice: R N B Q K B N R
  at y=0 (white) or y=7 (black).

### Added — 24 immolation tests for the canonical layout

`tests/test_initial_position_4d.py` locks down:
- Slice cardinalities (4 / 24 / 24 / 12) and pairwise disjointness.
- Slice union covers all 64 (z, w) pairs.
- Total piece counts (896, 448 / 448).
- 28 kings per side.
- 224 pawns per side (8 per non-empty slice × 28 slices).
- Per-slice structure (central has both colors, empty has none,
  white-only has no lowercase, black-only has no uppercase).
- Back-rank order R-N-B-Q-K-B-N-R parameterized over multiple
  slices.
- Pawn axis assignment by file parity, every non-empty slice.
- FEN4 round-trip (`from_fen(STARTING_FEN4).to_fen() == STARTING_FEN4`).
- `initial_position().to_fen() == STARTING_FEN4`.
- Side-to-move starts as `SIDE_WHITE`.
- **`STARTING_FEN4` SHA-256 hash locked** — any layout drift
  surfaces here with a clear "intentional? update both this hash
  and the §3.3 reference in `initial_position.py`" message.

The 1.7.1 README "What's new in v{X.Y}" gate still passes; this
release re-uses the existing v1.8 section in the README rather
than adding a new "v1.8.1" section (the two ship under the same
v1.8 line).

## [1.8.0] — 2026-05-01

The chess4D-OC visualizer's M11.40 unblocker release. Tier-1 of the
[upstream wishlist](https://github.com/lemonforest/chess-maths-viewer)
ships in 1.8.0; tier-2 (ψ-driven density / current, partial-trace
density matrices) follows in 1.8.1+ once the η-metric machinery
lands. No API breaks vs. 1.7.x — every addition is opt-in surface on
top of the existing `GameState4D` / `Move4D` / engine `search`.

### Added — `GameState4D` consumer surface (chess4D-OC tier 1)

Previously `chess_spectral_4d.GameState4D` was a position+history
*snapshot* — consumers had to round-trip through FEN4 to mutate it.
1.8.0 promotes it to a persistent mutation type that mirrors
`python-chess.Board`'s push/pop ergonomics, which lets the chess4D-
OC worker drop its `python-chess4d-oana-chiru` runtime dep.

**Tier 1.1 — push / pop**

- `GameState4D.push(move) -> Move4D` — apply a move, mutating in
  place. Accepts either a `Move4D` (pulls `from_sq` / `to_sq` /
  `promote_to`) or a `((from_xyzw), (to_xyzw))` /
  `((from_xyzw), (to_xyzw), promote_to)` tuple. Returns the recorded
  `Move4D` so callers can grab capture / promotion metadata.
- `GameState4D.pop() -> Move4D` — undo the last move. Restores
  `position`, half-move clock, side-to-move, and decrements the
  threefold-repetition counter for the position being left.
  Raises `IndexError` if history is empty (parallel to
  `chess.Board.pop()`'s contract).

`MoveHistory4D` gains `initial_fen4` and `initial_side_to_move`
fields, set in `record_initial_position`, so `pop()` can rewind
the very first ply without the consumer threading the initial
state separately.

**Tier 1.2 — board view + accessors**

- `GameState4D.board` — read-only `_BoardView4D` proxy over the
  live position dict. Methods: `occupant(sq)`, `pieces_of(side)`,
  `__contains__`, `__len__`. The view does not copy or freeze the
  underlying state — push / pop mutations are reflected
  immediately.
- `GameState4D.occupant(sq)` and `GameState4D.pieces_of(side)`
  — same accessors, exposed directly on the state for consumers
  who want to skip the `.board` indirection. `sq` accepts both
  the linear `int` index and the `(x,y,z,w)` `Coord4D` tuple.

**Tier 1.3 — `to_fen` / `from_fen` aliases**

`GameState4D.to_fen()` and `GameState4D.from_fen(fen4, ...)`
delegate to the existing `to_fen4` / `from_fen4`. Symmetric with
`python-chess.Board.{to,from}_fen`. The 1.7.1 slash-tolerant FEN4
form (`P/w@`) is accepted on both names.

**Tier 1.6 — encoder-shaped iterator**

- `GameState4D.iter_pieces() -> Iterator[Tuple[int, PieceValue]]`
  yields `(sq_idx, piece_value)` pairs in the format
  `chess_spectral.encoder_4d.encode_4d` consumes directly:
  `dict(state.iter_pieces())` is exactly the encoder's input.
  The chess4D-OC worker's `_state_to_pos4` collapses to a one-liner.

### Added — engine + game-state predicates (chess4D-OC tier 3)

**Tier 3.1 — `search()` accepts `GameState4D` directly**

`chess_spectral_4d.engine.search.search` now accepts either a
`Board4D` (existing surface) or a `GameState4D`. When a state is
passed, the search constructs a transient `Board4D` from
`state.position` + `state.side_to_move` and dispatches normally;
the chess4D-OC worker can drop its `Board4D.from_fen(state.to_fen4())`
hop. Implementation duck-types (looks for `.position` and
`.side_to_move`) so the engine's import graph stays one-way.

**Tier 3.2 — `is_check` / `is_checkmate` / `is_stalemate`**

- `GameState4D.is_check()` — wraps `Board4D.is_check()`.
- `GameState4D.is_checkmate()` — in check AND no legal move.
  Uses `next(iter(legal_moves), None)` so it bails on the first
  legal move; cost is `O(legal-move generation)` worst case
  (~2s at the dense 28-king start after 1.7.0's fast-paths).
- `GameState4D.is_stalemate()` — NOT in check AND no legal move.

These let the chess4D-OC visualizer route through the upstream
package instead of reimplementing the predicates in JS.

### Deferred to 1.8.1+

- **Tier 1.4 — `initial_position()` factory**: needs the canonical
  Oana-Chiru 28-king start FEN4 string. Until it lands as a
  documented constant, consumers should pass their own FEN4 to
  `GameState4D.from_fen(fen4)`. Tracked.
- **Tier 2.1 — `get_qm_density_from_psi` / `get_probability_current
  _from_psi`**: ψ-driven density / current for the M14.4c entanglement-
  viz layer. Needs factoring of the existing `get_qm_density` to
  expose the ψ → density step.
- **Tier 2.2 — `get_density_matrix_of` (M14.3 blocker)**: still
  raises `NotImplementedError` per ADR-005 (η-metric construction).

### Added — 16 immolation tests for the new surface

`tests/test_gamestate4d_consumer_surface.py` covers every Tier 1.1
/ 1.2 / 1.3 / 1.5 / 1.6 / 3.1 / 3.2 contract, asserting both the
shape (return types, signatures) and at least one concrete behaviour
per item. Hard gate — chess4D-OC's M11.40 PR will fail loudly if any
of these regress.

The existing `test_immolation_readme_announces_current_version`
gate (1.7.1) auto-checks the README has a "What's new in v1.8"
section before the 1.8.0 wheel ships.

## [1.7.1] — 2026-05-01

PyPI long-description hotfix on top of 1.7.0. Pure-docs / pure-test
release; no API or behavior changes.

### Why a 1.7.1 hotfix

1.7.0 wheels on PyPI shipped with a stale long-description: the
README forward-referenced v1.7 items as "deferred to v1.7+" and
lacked a "What's new in v1.7" section, both leftover from the v1.6
vantage point. The polish + immolation entries below in the [1.7.0]
section *did* ship in PyPI 1.7.0; the README inconsistency was
caught only during pre-publish review of the README itself, after
1.7.0 had already auto-published. 1.7.1 is the corrective
publication. **Provenance note:** the `chess-spectral-v1.7.0` git
tag points one commit past the actual 1.7.0 PyPI build (the tag was
inadvertently advanced when this README/immolation PR merged); the
PyPI 1.7.0 wheels were built from the `chess-spectral-v1.7.0` tag
*before* this advance, i.e. commit `2e66712`. 1.7.1 ships the
forward-rolled state cleanly so future archeology resolves to the
1.7.1 tag for the README + new immolation gate.

### Documentation — README v1.7 surface refresh (PyPI long-description)

Three deferral targets that previously read "deferred to v1.7+"
were forward-rolled to "v1.8+" now that v1.7 is shipping —
ADR-005 pawn pseudo-Hermitian η-metric, `get_density_matrix_of`,
and `get_qm_density(piece_id=...)`. These are all genuinely still
deferred (v1.7 didn't ship the partial-trace machinery they need;
the v1.7 scope was the chess4D-OC visualizer wishlist, not the QM
bridge backlog). The "v1.7+" framing was stale on the PyPI long-
description from v1.6's vantage point; "v1.8+" is forward-accurate.

Also added a **"What's new in v1.7"** section above "What's new in
v1.6", calling out the four headline 1.7 pieces (time-budget mid-
iteration; native bitboard fast-path with ~16× iteration; legal-move
algorithmic refactor with ~12.7×; cumulative ~125× on the visualizer
pain point; `HAS_NATIVE_BITBOARD` top-level export). The package
summary line now mentions the v1.7 fast-path + budget honoring.

### Fixed — FEN4 parser tolerates optional `/` between pawn color and axis

Both Python (`chess_spectral.fen_4d.parse`) and C
(`cs_fen_4d_parse`) now accept `P/w@x,y,z,w` as equivalent to
`Pw@x,y,z,w`. Pre-1.7.1 a literal slash in this position raised
`Fen4ParseError` / returned `-3` from the C parser. The slash form
is more readable for humans hand-authoring FEN4 strings — a
reasonable accommodation, mirroring the FEN family's tolerance of
common syntactic variations elsewhere.

The serializer (`fen_4d.serialize`) continues to emit the canonical
no-slash form, so round-tripping a `P/w@`-input preserves the
slash-less representation on output. Both forms are byte-identical
under the C `spectral_4d encode-fen4` pipeline (parity verified by
new tests in `tests/test_fen4_parity.py`).

8 new tests across the Python parser and C-Python parity layer:
- 4 slash-form fixtures added to the parameterized
  `VALID_FIXTURES` list (`P/w`, `P/y`, `p/w`, `p/y` plus a
  mixed-slash-and-no-slash fixture).
- `test_python_parser_slash_form_equivalent_to_no_slash` —
  parameterized over (color, axis); asserts both forms parse to
  the same dict.
- `test_c_python_parity_slash_form_pawn` — same parameterization;
  asserts the C `spectral_4d encode-fen4` writes byte-identical
  `.spectral4` for both forms.

### Added — Immolation README gate (catches the v1.7+ deferral / missing-section bug pattern automatically)

- New test in `tests/test_smoke_e2e.py`:
  `test_immolation_readme_announces_current_version` hard-asserts
  that the README has a `## What's new in v{major}.{minor}` section
  matching the current pyproject version. Catches the bug class
  that motivated this 1.7.1 hotfix. Read the version directly via
  regex (no `tomllib` import — Python 3.10 reachability).
- The same test ALSO emits an advisory `[immolation] LLM doc-scrub
  candidates in README.md` block listing any `deferred to v{X.Y}+`
  mentions where (X,Y) is at or below the current version. Output
  is formatted as `file:line: text` triples, deliberately structured
  as friendly LLM input for the next doc-scrub pass. Does NOT fail
  the test (false-positive risk on legitimate "still-deferred-since-
  v1.5" historical notes); zero output is the steady state. Future
  release-cycle PRs that introduce stale forward-references will
  surface them on the merge train rather than at pre-publish review.

## [1.7.0] — 2026-05-01

### Added — release-pipeline polish (immolation embiggening + downstream surface)

These items shipped in PyPI 1.7.0 (post-tag, via the polish-tag
advance documented in the 1.7.1 provenance note above).

- **`HAS_NATIVE_BITBOARD` re-exported at the top-level `chess_spectral`
  package**, so downstream consumers (the chess4D-OC visualizer and
  similar Pyodide / desktop apps) can `from chess_spectral import
  HAS_NATIVE_BITBOARD` to badge "native fast-path active" / fall back
  cleanly when the native lib isn't present (sdist install, Pyodide
  WASM-less, ABI mismatch). Previously only reachable as
  `chess_spectral.spatial_4d.bitboard.HAS_NATIVE_BITBOARD` — the
  longer path is preserved as a backward-compat alias.

- **Four new tests in the immolation suite** (`tests/test_smoke_e2e.py`)
  covering the 1.7.0 D1 + D2 cohort:
  - `test_immolation_search_honors_time_budget_mid_iteration` —
    a tight `time_budget_ms` on a dense 28-king position must return
    within budget + 0.5s grace with a non-None `best_move`. Catches
    a regression to the pre-1.7.0 between-iterations-only check.
  - `test_immolation_search_result_has_timed_out_field` — structural
    sanity check on the `SearchResult.timed_out` field that downstream
    consumers depend on to distinguish natural completion from
    deadline exit.
  - `test_immolation_has_native_bitboard_flag_exposed_at_top_level` —
    `from chess_spectral import HAS_NATIVE_BITBOARD` works, the flag
    is in `__all__`, and reads as a bool. Catches accidental demotion
    of the flag to a sub-package-only export.
  - `test_immolation_native_bitboard_iteration_parity_when_available` —
    when `HAS_NATIVE_BITBOARD` is True, `Bitboard4D.to_squares()`
    output matches a pure-Python reference recompute. Skipped on
    sdist / Pyodide builds where native isn't present. Catches
    marshaling regressions in `cs_bb4_to_squares` or its ctypes
    wrapper.

### Changed — CLI `--help` text refreshed for 1.7.0 mid-iteration honoring

The `time_budget_ms` agent-spec key and the `--time-budget-ms` sweep
flag now mention the 1.7.0 behavior: the deadline is checked at every
search node (not just between iterative-deepening iterations), so
even a tight budget on a dense position returns the deepest-completed-
so-far best move within ~0.5s grace. Affected surfaces:

- `chess_spectral.cli search` description
- `chess_spectral.cli sweep --time-budget-ms` help
- `chess_spectral.engine.tournament.agent_spec` module docstring
- `chess_spectral_4d.cli tournament` description ("Realistic settings"
  paragraph) — also calls out the cumulative ~125× speedup on the
  dense start vs 1.6.x.

### Original 1.7.0 release notes

The chess4D-OC visualizer's reported user-facing-pain-points release.
Two upstream improvements to chess-spectral 1.6.1's 4D engine
performance, both shipped on top of v1.6.1's public surface — no
behavior changes for existing 2D/4D users; new opt-in surface where
applicable.

### Headline improvements

| Improvement | Before (1.6.1) | After (1.7.0) | Speedup |
|---|---|---|---|
| `search(...)` honors `time_budget_ms` mid-iteration | budget checked between iterations only — depth-1 at the dense start could run for ~510s on a 5s budget | budget checked at every node + partial-iteration result returned | budget honored within 0.5s grace |
| `Bitboard4D.to_squares()` / `squares()` (the move-gen iterator hot path) | pure-Python `b & -b` loop | native `cs_bb4_to_squares` C primitive | ~16× |
| `Board4D.legal_moves()` at the dense 28-king start | per-king redundant attacker iteration | one-pass attacker iteration with bitboard intersect on K kings simultaneously | ~12.7× (262× cumulative vs pure-Python rc1) |

The cumulative effect on the wishlist's reported pain point — the
chess4D-OC visualizer's ~250s `legal_moves()` at the standard 28-king
starting position — is **~125× faster** in 1.7.0 (from ~250s down to
~2s on the same hardware), with no API changes.

### Native fast-path infrastructure (D2)

- **`include/cs_bitboard4d.h` + `src/cs_bitboard4d.c`** — pure-C
  primitives for the 4096-bit Bitboard4D over the Z_8^4 lattice.
  Build hookup via CMake + scikit-build-core; the shared library
  ships in the wheel under `chess_spectral/_native/` and is loaded
  via ctypes at import. Pure-Python `Bitboard4D` continues to work
  as fallback (sdist install, Pyodide / micropip) — verified by a
  dedicated `fallback-test` CI job.
- **`cs_bb4_to_squares`** is the load-bearing speedup. Per-bit LSB
  extraction in C (`__builtin_ctzll` / `_BitScanForward64` / SWAR
  fallback) plus `b &= b - 1` clear, all without crossing the ctypes
  boundary per square. `Bitboard4D.to_squares()` and `squares()`
  route through it when `HAS_NATIVE_BITBOARD` is True.
- **C ABI version stamp** (`cs_bb4_abi_version` returns 2) so the
  Python wrapper can refuse mismatched binaries.
- **Wheel guardrails** — every published wheel runs
  `test_native_bitboard4d.py` at install time; a separate sanity
  check grep-asserts `cs_bitboard4d.{so,dll,dylib}` is present in
  each wheel before the artefact is uploaded. `verify-wheels` at
  per-PR CI mirrors the publish matrix.

### Search ergonomics (D1)

- **`SearchOptions.time_budget_ms` honored mid-iteration.** The
  iterative-deepening driver checks the deadline at every
  `_alpha_beta` node entry, not just between iterations. On
  expiry, returns the partial best-move from the deepest
  fully-completed iteration with `SearchResult.timed_out=True`.
- New field: `SearchResult.timed_out: bool` distinguishes natural
  completion (`max_depth` reached) from deadline exit. Existing
  callers see no API change; opt-in to the new field as needed.

### Algorithmic improvements

- **Legal-move filter** rewritten from "K calls × N attackers each"
  to "one pass over N attackers, intersect with all K kings per
  step, short-circuit on first hit". Same per-op cost as the OLD
  `_is_attacked` (both are O(1) bitboard tests on 4096-bit ints),
  but tests all K kings in one bitboard op instead of K bit tests.
  Pareto win on every input we measured.

### Known limitations / deferred to v1.7.x or v1.8

- **Pyodide native WASM build of cs_bitboard4d.so** is deferred. The
  existing `py3-none-any` pure-Python wheel already serves Pyodide
  consumers correctly (just without the native speedup). A WASM
  build would need emscripten + pyodide-build infrastructure and is
  tracked as M2.5 if there's user demand.
- **`_alpha_beta` inner loop in C** is deferred. The wishlist
  ranked it the lowest-priority piece of the native scope; the
  algorithmic refactor in M2.3 plus native iteration covers most of
  the user-visible benefit. M2.6 if it turns out to matter.

### Tests

- 249 spatial_4d / move-gen / native-bitboard tests pass.
- `fallback-test` CI job verifies `HAS_NATIVE_BITBOARD=False` plus
  226 spatial_4d tests when the native lib isn't available.
- The cibuildwheel matrix exercises the native path on every wheel
  build (3 OS × 5 Python = 15 cells) on tag push.

## [1.7.0rc4] — 2026-05-01 (TestPyPI only)

**M2.3 — algorithmic hot-path: batch attacker test for legal-move
filter.** Pareto speedup of `Board4D.legal_moves()` at the dense
28-king start position. Pure-Python algorithmic change; no native
code added.

### Changed

- `Board4D._any_own_king_attacked_after_push` now iterates attackers
  *once* and per-attacker tests `king_bb.intersects(attack_set)`,
  short-circuiting on the first attacker that hits any king.
  Previously: K calls × N attackers each (one `_is_attacked` per
  king, each iterating all attackers separately). Now: O(N) per
  push with the same short-circuit behaviour.

  **Profiling (1.7.0rc3 baseline) showed
  `_any_own_king_attacked_after_push` was ~60% of total
  `legal_moves()` cost on a representative non-in-check 264-piece
  position (28 kings/side + sliders + 56 pawns/side). Microbench:**

  | Position | rc3 (old per-king) | rc4 (new) | speedup |
  |---|---|---|---|
  | Non-in-check, 264 pieces | 26 022 ms | 2 043 ms | **12.7×** |
  | Pathological dense (kings in mutual attack) | 686 ms | 432 ms | 1.6× |

  Both cases improved (Pareto win). The realistic case (the wishlist's
  reported chess4D-OC visualizer pain point) sees the bigger gain
  because the OLD path's K-fold redundancy hurt most when no king
  was attacked yet.

  Implementation note: the shape of the new code closely mirrors the
  pre-existing `_is_attacked`, with `if sq in attack_set` swapped for
  `if king_bb.intersects(attack_set)`. Same per-op cost (both are
  O(1) bitboard tests on 4096-bit ints), but one call replaces K.

  All 249 spatial_4d-related tests + apply_move + castling + native-
  bitboard tests pass unchanged. No API changes.

## [1.7.0rc3] — 2026-05-01 (TestPyPI only)

**M2.2 — native iteration fast-path + M2.1 visibility bug fix.** Wires
the foundation laid in M2.1 to a real speedup on the chess
move-generation hot path, and unblocks the previously-shipped (but
silently inert) M2.1 native primitives.

### Fixed

- **M2.1 visibility regression: cs_bb4_* symbols were hidden, not
  exported.** The M2.1 CMakeLists set `C_VISIBILITY_PRESET=hidden` on
  the `cs_bitboard4d` target intending to keep internal helpers
  private — but the only "internal" symbols in this TU are
  `static inline` helpers (`popcount64`, `ctz64`) that are never
  linker-visible regardless of the property. With hidden visibility,
  the entire `cs_bb4_*` API ended up hidden too: `dlsym()` returned
  NULL at Python ctypes load time, and `HAS_NATIVE_BITBOARD` silently
  stayed `False` even when the wheel shipped a working `.so`/`.dll`.
  The native-only tests in `test_native_bitboard4d.py` noticed via
  their `if not HAS_NATIVE: skip` guards, so M2.1 CI passed without
  exercising the native code path. M2.2 drops the hidden-visibility
  setting; the cs_bb4_* API now exports correctly.
  (`docs/chess-maths/chess-spectral/CMakeLists.txt`)

### Added

- **`int cs_bb4_to_squares(int *out_squares, const uint64_t *bits)`**
  — native iteration. Fills `out_squares[]` with the indices of set
  bits, ascending. Returns the count written. Caller must allocate
  at least `CS_BB4_N_SQUARES` (=4096) ints worst-case. Uses the LSB
  intrinsic (`__builtin_ctzll` / `_BitScanForward64` / De Bruijn
  fallback) plus `b &= b - 1` clear, all in C. One ctypes call per
  bitboard amortizes the marshaling overhead.
- **`Bitboard4D.to_squares()` and `Bitboard4D.squares()`** now route
  through the native helper when `HAS_NATIVE_BITBOARD` is True.
  Marshaling uses `int.to_bytes(512, 'little')` (C-implemented in
  CPython, ~1 µs) plus `ctypes.c_uint64.from_buffer_copy` (~1 µs);
  total per-call overhead ~5 µs, amortized over the entire
  bitboard. **Microbenchmark on 50 dense (popcount-2000) + 500
  sparse (popcount-24) bitboards: 130 ms pure-Python → 8 ms native
  (~16×).**
- **C ABI version bump 1 → 2** to flag the new `cs_bb4_to_squares`
  symbol. The Python wrapper checks the version at load time and
  silently falls back to pure-Python on a mismatch (rebuild your
  binary or accept the slow path).

### Not changed (deliberate)

We intentionally did NOT route `__or__` / `__and__` / `__xor__` /
`popcount` through the native path. CPython's native-C int operators
on 4096-bit ints already use digit-level SWAR in `Objects/longobject.c`
— faster than the ctypes round trip would be. The ~10 µs of marshaling
per call (Python int → uint64[64] → ctypes call → uint64[64] → Python
int) dominates over the ~50 ns CPython int op for these primitives.
Only multi-bit operations like iteration (where one ctypes call
amortizes over many bits) benefit from native dispatch.

## [1.7.0rc2] — 2026-04-30 (TestPyPI only)

**M2.1 — D2 prep: native bitboard primitives + build hookup.** Foundation
milestone for the C-extension hot path. The `cs_bitboard4d` shared library
ships in the wheel (`chess_spectral/_native/`); the Python ctypes wrapper
loads it at import; `chess_spectral.spatial_4d.bitboard.HAS_NATIVE_BITBOARD`
flags availability. Pure-Python `Bitboard4D` continues to work unchanged
(method-level integration lands in M2.2).

### Added

- `include/cs_bitboard4d.h` + `src/cs_bitboard4d.c` — pure-C primitives:
  popcount, bitwise AND/OR/XOR/NOT/sub, set/clear/toggle/test square,
  empty/full predicates, equals, intersects. ABI version stamp
  (`CS_BB4_ABI_VERSION = 1`) with version-mismatch fallback.
- `chess_spectral/_native_bitboard4d.py` — ctypes wrapper.
  `HAS_NATIVE` reports whether the library loaded; on failure the
  module still imports, exposes `LOAD_ERROR` explaining why, and
  callers fall back to pure Python.
- `chess_spectral.spatial_4d.bitboard.HAS_NATIVE_BITBOARD` flag,
  re-exported from the wrapper so callers don't need to import the
  private module.
- `tests/test_native_bitboard4d.py` — 8 tests. 3 always run (module
  imports, flag consistency, error reporting); 5 skip when native
  isn't built (covering popcount, bitwise ops, per-square ops,
  predicates against numpy uint64[64] inputs).

### Build

- `CMakeLists.txt`: new `add_library(cs_bitboard4d SHARED ...)` target.
  POSIX hides internal symbols via `C_VISIBILITY_PRESET hidden`; Windows
  drops the `lib` prefix to produce `cs_bitboard4d.dll` matching the
  ctypes wrapper's lookup order.
- `if(DEFINED SKBUILD)`: install `cs_bitboard4d` into
  `chess_spectral/_native/` alongside `spectral` / `spectral_4d`.

### What's deferred

- M2.2 (next): wire `Bitboard4D.popcount`, `__or__`/`__and__`/etc.
  through the native fast-path when `HAS_NATIVE_BITBOARD`.
- M2.3: `_alpha_beta` inner loop in C.
- M2.4: cibuildwheel + Pyodide build + sdist-only fallback CI job.

## [1.7.0rc1] — 2026-04-30 (TestPyPI only)

First milestone of the **chess-spectral 1.7.0** release pipeline addressing
the chess4D-OC visualizer's user-facing-pain-points report. **D1 only**
(time-budget bug fix); D2 (C-extension hot path) lands in 1.7.0rcN as it
progresses, with rc bumps after each milestone hitting TestPyPI for
verification. Final 1.7.0 promotes to production PyPI once D2 is complete.

Released to TestPyPI ONLY (the 1.7.0rc tag does NOT match the autotag
workflow's strict-semver regex; manual dispatch with
``gh workflow run chess-spectral-publish.yml -f target=testpypi``).

### Fixed (D1)

- `chess_spectral.engine.search.search` and `chess_spectral_4d.engine.search.search`: `time_budget_ms` is now honored mid-iteration, not just between iterations. Previously the deadline was checked only every 1024 nodes inside `_negamax`, AND `list(board.legal_moves())` materialized eagerly — at dense 4D positions a tight budget could blow past by the cost of a full move-list materialization (~250s at the 28-king starting position). Fix:
  - Every-node deadline check at top of `_negamax` (was every-1024).
  - `_materialize_legal_moves` helper iterates the legal-move generator with a deadline check between each yield, returning a partial list on abort.
  - Root iteration loop checks the deadline before each candidate move; partial-iteration `iter_best_move` is preserved on time-out instead of being discarded.
  - First yielded move always survives the deadline check (so positions with legal moves always have a non-None `best_move`, even on a 5ms budget).

### Added

- `SearchResult.timed_out: bool` — True when the search aborted because the `time_budget_ms` deadline elapsed mid-iteration. `depth_reached` remains the deepest FULLY-completed iteration; `best_move` may come from a partial iteration deeper than that. False when the iteration completes naturally at `max_depth`.

### Tests

- New: `test_search_time_budget_honored_with_slow_evaluator` (2D + 4D parallel) — uses a synthetic 50ms-per-leaf evaluator to verify a 2000ms budget aborts within a 500ms grace, with `timed_out=True` and `best_move != None`.
- New: `test_search_time_budget_no_legal_moves_returns_none` (2D) — confirms `best_move=None` is reserved for true game-over, not for tight budgets.
- New: `test_search_natural_completion_sets_timed_out_false` (4D).
- Updated: `test_search_time_budget_aborts_early` (4D) — accepts the new semantic that `depth_reached=0` is valid when even the first iteration's materialization aborts.

### Acknowledgments

Reported via the chess4D-OC visualizer's user-facing-pain-points issue. Pure-Python performance of 4D move-gen at dense positions is the underlying issue; `chess-spectral 1.7.0` will address it via a C-extension hot path. This 1.6.2 release fixes the budget-honoring discipline so partial-iteration progress is preserved while we wait on the native code.

## [1.6.1] — 2026-04-30

The v1.6 follow-up release. Closes the v1.6 deferred-items workstream
(Track 1 = Python QM 2D parity with v1.5 4D, Track 2 = v5 unified wire
format C-side mirror across all three encoding modes plus the CLI
flag, Track 3 = root-cause + fix the long-standing
`test_pgn_to_spectralz_real_game::xfail(linux)` segfault). Two
companion docs PRs (#129 chess2d-OC misnaming, #135 README oracles
polish) are folded in. The release ships entirely on top of v1.6.0's
public surface — no behavior changes for existing 2D/4D users; new
opt-in surface for `--encoding={xor,channel,full}` and the C-side v5
reader/writer functions.

### Fixed — Linux segfault in `spectral encode --pgn -z` (POSIX feature test)

**Root cause:** glibc gates `fdopen` behind `_POSIX_C_SOURCE >= 200809L`
in `<stdio.h>`. `src/main.c` didn't define this macro, so `fdopen`
was an implicit declaration and the compiler defaulted to assuming
it returned `int`. On x86_64 that **truncated the 64-bit `FILE*`
return value to 32 bits**, producing an invalid pointer. The next
`fgets()` call dereferenced the truncated pointer and SIGSEGVed
inside libc.

The bug only manifested on Linux+glibc because:
- macOS exposes POSIX symbols by default (no feature test needed)
- Windows uses `_fdopen` via `_open_osfhandle` (different code path)
- ASAN preset on Linux happens to compile at -O1 which preserved
  the truncated-pointer bug pattern in a way that "happened to
  work" — the bug was real on ASAN too, just dormant.

The fix is one line:
`#define _POSIX_C_SOURCE 200809L` before the system header includes
in `src/main.c`. Reproduced and gdb-verified under Ubuntu 22.04 +
GCC 11.4 + WSL2; before the fix the program crashed in
`fgets(__stream=0x5559c2a0, ...)` (32-bit-truncated pointer) at
`src/main.c:596`; after the fix the encode pipeline returns 0 and
writes 88 frames as expected.

The `xfail(linux)` decorator on `test_pgn_to_spectralz_real_game`
is removed; the test now runs unconditionally. The historical
context (LTO red herring, then GCC -O2 red herring, then the real
diagnosis) is preserved as a comment block above the test.

### Changed — drop IPO/LTO from the `release` CMake preset

The `release` configure preset no longer sets
`CMAKE_INTERPROCEDURAL_OPTIMIZATION=TRUE`. Cleanup carried in the
same PR as the segfault fix above. The release preset now matches
what cibuildwheel does (no LTO), so the shipped `.whl` artefact is
faithfully reproducible from the preset. The audit's F-08 LTO
recommendation can come back later behind a `CheckIPOSupported`
gate.

### Documentation — README: name all three move-rule oracles side by side

- The "What's new in v1.6" section now groups the three in-house
  move-rule oracles into a single bullet that names them as three
  alternative mathematical lenses on the same legality predicate:
  bitboard / attack-tables (`spatial_4d`, engineering lens),
  phase-space operators (`phase_operators` / `phase_operators_4d`,
  algebraic lens), and discrete-Laplacian eigenbasis (spectral
  lens). Renamed the third from "graph-Laplacian eigenbasis" to
  "discrete-Laplacian eigenbasis" — same matrix (the lattice's
  Kron-sum of P_8 path-graph Laplacians is, by definition, the
  standard 5-point-stencil discrete Laplacian on the 8×8 / 8^4
  grid), but more recognizable phrasing for readers from
  physics/numerics. No behavior change; PyPI long-description only.

### Added — v1.6.x Track 2 PR-5: `--encoding={xor,channel,full}` CLI flag (2D + 4D)

The final v1.6.x Track 2 PR per ADR-001's phasing. Both the 2D and 4D
encode CLIs now accept an opt-in `--encoding` flag that routes through
the v5 unified writer:

- `chess_spectral.cli encode` and `encode-fen`: `--encoding={xor,
  channel,full}`
- `chess_spectral_4d.cli encode-fen4` and `encode-moves4`:
  `--encoding={xor,channel,full}` (requires `--output`; the v5 writer
  back-fills `n_plies` in the header so it cannot stream to stdout).

Modes:
- `xor` (mode 2): bit-XOR delta from the previous frame.
  ADR-001 names this as the eventual default for new writes
  (~7.23× compression on real games via long zero runs that gzip
  eats for free, measured on a 50-ply 4D knight-tour fixture).
- `channel` (mode 1): per-channel replacement. Emits only channels
  that changed since the previous frame; the first frame is always
  a FULL block.
- `full` (mode 0): v5 dense — same frame body as v2/v4 but under a
  v5 header. Useful as a research-platform escape hatch for
  byte-for-byte parity testing with prior tools.

**Default behavior unchanged.** Omit `--encoding` and the writer
falls through to the existing v2 / v4 writers byte-for-byte. The
default switch to `xor` (per ADR-001) is tracked as a separate v1.7
follow-up gated on full C-side parity migration so v2/v4 readers
continue to work on existing infrastructure.

12 new tests in `tests/test_cli_encoding_flag.py`: omit-flag default
still writes v2 / v4; each `--encoding=<mode>` writes the right v5
mode byte (offset 32 of the 256-byte v5 header) at the right
n_dimensions; the v5 xor and channel single-frame round-trips parse
correctly via `iter_v5_frames_*`; 4D requires-output guard.

### Added — v1.6.x Track 2 PR-4: v5 C-side XOR-stream (mode 2) full-file I/O

- **`cs_v5_write_xor_stream_{2d,4d}_file(fp, dense_encodings, n_plies)`** —
  fixed-frame-size writer. Frame 0 is written verbatim; frame N>0
  has its encoding bytes XOR'd in-flight against frame N-1's *real*
  encoding (uint32-view bit XOR; move tail unchanged). Wins on chess
  workloads where most ply-to-ply byte changes are localised — XOR
  produces long runs of zero bytes that gzip eats for free.
  Empirical 4D measurement: 7.23× compression on a 50-ply knight-tour
  fixture vs. dense gzip.

- **`cs_v5_read_xor_stream_{2d,4d}_file(fp, hdr_out, dense_buf,
  max_plies, n_plies_out)`** — read counterpart. Reads each fixed-size
  body verbatim, then in-place XORs the encoding portion against the
  previous reconstructed frame's encoding (which is already in the
  caller's dense_buf at offset (i-1)*frame_bytes). Frame 0 is left
  as read. Move tail bytes are copied through unchanged.

  5 new C-side test cases (25 new assertions, total 110): 4-frame 2D
  progressive-delta round-trip, 3-frame 2D zero-delta round-trip,
  **disk-layout invariant**: writing two identical frames produces
  all-zero encoding bytes for frame 1 on disk (this is the property
  that gzip exploits), single 4D round-trip, mode-mismatch reject
  (xor reader on dense file → -8).

  All three encoding modes (dense/per-channel/xor) now ship for both
  dimensions on the C side. The `--encoding={xor,channel,full}` CLI
  flag lands in v1.6.x Track 2 PR-5.

### Added — v1.6.x Track 2 PR-3: v5 C-side per-channel (mode 1) full-file I/O

- **`cs_v5_write_per_channel_{2d,4d}_file(fp, dense_encodings,
  n_plies)`** — write a v5 mode-1 file from a contiguous buffer of
  dense-equivalent frames. The writer emits frame 0 as a FULL block
  (all `CS_V5_N_CHANNELS_{2D=10,4D=11}` channels written) and then for
  each subsequent frame compares each channel byte-exact against the
  previous dense frame and emits only the channels that differ. The
  move-metadata tail is appended verbatim after each body.

- **`cs_v5_read_per_channel_{2d,4d}_file(fp, hdr_out, dense_buf,
  max_plies, n_plies_out)`** — read counterpart. Reconstructs each
  frame's full dense layout from per-channel deltas (seeded by FULL
  block, then iteratively patched). Validates body geometry: returns
  `-9` on a malformed body (bad channel idx, body-size mismatch, or a
  non-leading delta frame missing prev state); `-8` on header
  mode/dimension mismatch; `-7` on truncation.

  New constants in `cs_frame_v5.h`: `CS_V5_PC_FLAG_FULL=0x01`,
  `CS_V5_N_CHANNELS_{2D=10,4D=11}`, `CS_V5_CHANNEL_DIM_{2D=64,4D=4096}`,
  `CS_V5_PC_HEADER_SIZE=6`, `CS_V5_PC_BLOCK_PREFIX=2`,
  `CS_V5_MOVE_TAIL_{2D=8,4D=14}`.

  6 new C-side test cases (33 new assertions, total 85) covering:
  4-frame 2D progressive single-channel deltas (full + 3 deltas),
  3-frame zero-delta (frames 1 & 2 emit 0 channels), 2-frame
  all-channels-changed, single 4D frame round-trip, mode-mismatch
  reject (mode-1 reader on a mode-0 file → -8), and 4-write/2-read
  truncation.

  XOR-stream (mode 2) reader/writer ships in subsequent v1.6.x Track 2
  PR-4; `--encoding={xor,channel,full}` CLI flag lands in the final
  Track 2 PR.

### Fixed — naming: "chess2d-OC" was a misnaming

- "chess4d-OC" is short for "chess4d-oana-chiru" — it's a specific
  4D chess ruleset (Oana & Chiru, *AppliedMath* 6(3):48, 2026) that
  the chess4d-OC consumer is built on. **There is no Oana-Chiru
  ruleset for 2D chess** — standard chess rules are just standard.
- An earlier draft of `qm_2d_bridge.py`, `qm_2d_dynamics.py`, and the
  v1.6.x CHANGELOG entry incorrectly said "chess2d-OC" by analogy
  with chess4d-OC. Fixed: the 2D consumer is just "chess2d" (or
  "the 2D consumer", or "chess4d-OC's 2D sibling"). Added a clarifying
  note in the qm_2d_bridge module docstring so future readers don't
  re-make the mistake.

### Added — v1.6.x Track 1 PR-D: apply_move_qm dispatcher (§17.2 #4)

- **`qm_2d_bridge.apply_move_qm(pre_state, post_state, *, from_sq,
  to_sq, side_to_move_post, return_per_channel)`**. Closes the v1.5
  `applyMoveQm` analogue at 2D. Hybrid dispatch:
  - **A_1 channel**: strict-unitary path via
    `qm_2d_dynamics.u_move_a1_2d` when `from_sq` + `to_sq` are
    given AND the pre/post positions confirm a non-capture move.
    Falls back to the measurement-only re-encode otherwise.
  - **Channels 1..9 (A2/B1/B2/E/F1-3/FA/FD)**: measurement-only
    re-encode via `qm_2d.state_to_psi(post_state)`. Same v1.5 4D
    pattern used for FIB_SYM_* channels — known correct,
    consumer-ready, doesn't require per-channel u_move builders
    that need design specs we don't have for non-A_1 2D channels.

  Returns a Pyodide-friendly dict with the assembled post-ψ as
  Float32 interleaved real+imag (matches the §17.1 ComplexArray
  format), the basis dim (640), and `<psi|psi>` for normalization
  verification. Optional `return_per_channel=True` exposes the
  per-channel dispatch (csr_matrix for A_1 strict-path; marker
  dicts with `reason='measurement-only'` and `psi_post_block` for
  the others).

  6 new tests in `tests/test_qm_2d_bridge.py`: e2-e4 round-trip
  (normalization), strict A_1 path vs re-encode fallback, complete
  per-channel dispatch (10 channels with the right types), null-move
  guard, chess.Board acceptance.

### Added — v1.6.x Track 2 PR-2: v5 C-side dense full-file I/O (2D + 4D)

- **`cs_v5_write_dense_{2d,4d}_file(fp, frame_bytes, n_plies)`** —
  high-level helpers that compose the v5 header + frame bodies into
  a complete dense-mode (mode 0) v5 file. Caller passes a contiguous
  byte buffer of `n_plies × CS_V5_FRAME_BYTES_{2D=2568, 4D=180238}`
  bytes; the function fills in the header from constants and the
  n_plies argument.

- **`cs_v5_read_dense_{2d,4d}_file(fp, hdr_out, frame_buf, max_plies,
  n_plies_out)`** — read counterpart. Validates that the header is
  the expected dimension + dense mode (returns -8 on mismatch).
  Reads min(file's n_plies, max_plies) frames into `frame_buf`;
  reports the actual count via `*n_plies_out`.

  4 new C-side test cases (13 new assertions, total 52) covering:
  3-frame 2D round-trip with deterministic-pattern bytes, 5-frame
  write + 2-frame truncated read, single 4D frame round-trip, and a
  cross-dimension reject (a 2D reader on a 4D file returns -8).

### Added — v1.6.x Track 2 PR-1: v5 wire format C-side header

- **`include/cs_frame_v5.h`** + **`src/cs_frame_v5.c`** — C-side
  mirror of the v5 unified wire format header reader/writer. Packs
  the 256-byte v5 header struct (`cs_v5_header_t`), peeks the version
  field from a stream, and reads/writes via stdio. Mirrors
  `python/chess_spectral/frame_v5.py` byte-for-byte.

  31 C-side assertions in `test/test_frame_v5.c` covering: 2D dense
  + 4D XOR-stream pack/unpack round-trips, reserved-bytes zero-fill,
  4 validation rejection paths (bad n_dimensions / encoding_mode /
  dim-mismatch / bad magic), file round-trip, and a load-bearing
  **byte-parity test** asserting the C-produced 256-byte buffer
  equals Python's `HeaderV5.pack()` output for a fixed fixture.

  Frame-body reader/writer for the three encoding modes (dense /
  per-channel / XOR-stream) ships in subsequent v1.6.x Track 2 PRs;
  the `--encoding=` CLI flag wiring lands in the final Track 2 PR.

### Added — v1.6.x Track 1 PR-C: qm_2d_bridge §17.2 dispatch surface (skeleton)

The 2D analogue of `qm_4d_bridge` (which shipped the §17.1 + §17.5
methods in v1.5). Closes the consumer-facing v1.5 gap by giving
the 2D consumer + the upcoming web visualizer a callable §17.2
surface on top of the v1.6 kinematic layer.

Methods shipped (8 of the 13 in scope; the remaining 5 require
per-channel u_move dynamics that arrive in PR-D / PR-E):

  §17.5 dev/debug surface (5 methods):
    - get_version       — package version + bridge surface tag
    - get_encoder_shape — 640-dim, 10 channels × 64 modes
    - get_fen_state     — Board → FEN, or position-dict → FEN
                          (translates the chess_spectral row-flip
                          square convention to python-chess's)
    - load_fen          — FEN → position dict + side-to-move flag
    - has_legal_moves   — python-chess legal-move count + check flag

  §17.2 kinematic methods (3, all backed by qm_2d):
    - get_qm_state       — ψ as Float32 interleaved real+imag
                           (matches the §17.1 ComplexArray on-the-
                           wire format)
    - get_qm_density     — |ψ|² per cell summed across 10 channels
    - get_qm_expectation — ⟨ψ|H_p|ψ⟩ for the 5 Hermitian piece-reach
                           observables (rook/bishop/queen/king/knight)

Methods deferred to PR-D / PR-E:
    - apply_move_qm / apply_move_qm_full  — needs per-channel u_move
                           builders + capture path
    - measure_at, get_density_matrix_of, get_probability_current —
                           need partial-trace / density-matrix
                           machinery (defer to v1.7+ per the 4D
                           pattern)

Each method returns a Pyodide-JSON-friendly dict with at least an
`ok` key. ψ is serialised as Float32 interleaved real+imag (real,
imag, real, imag, ...) — same on-the-wire format as 4D, so the
chess4D-OC consumer's M14.x WebGL renderer reads either via
``Float32Array``.

Bug fix included: the position-dict round-trip path translates
chess_spectral's square indexing (row 0 = rank 8, sq 0 = a8) to
python-chess's (row 0 = rank 1, sq 0 = a1). An earlier draft of the
bridge naively passed sq indices through, producing legal-move
counts of 4 (knight-only) instead of the canonical 20 from the
starting position.

23 new tests in `tests/test_qm_2d_bridge.py` covering all 8 methods,
the ComplexArray serialiser, and the convention-translation
regression guard.

### Added — v1.6.x Track 1 PR-B: u_move_a1_2d (A_1 channel projector-sandwich)

- **`P_A1_2D()`** — A_1 (D_4 trivial irrep) orbit projector on C^64.
  `(1/8) * sum_{g in D_4} Π(g)` where Π is the 64-dim permutation
  representation. Real-symmetric, idempotent, rank == 10 (exactly the
  number of D_4 orbits on the 8×8 lattice — same count as the
  encoder's per-channel split).

- **`u_move_a1_2d(from_sq, to_sq)`** — A_1 channel move-as-unitary on
  C^64, the 2D analogue of `qm_4d_dynamics.u_move_a1`. Built via the
  projector-sandwich form: `U_a1 = P_A1 @ U_swap @ P_A1`. Sub-unitary
  on the full C^64 (zero outside `range(P_A1)`); strict-unitary on
  `range(P_A1)` exactly when `from_sq` and `to_sq` are in the same
  D_4 orbit. Same algebra + same caveats as the 4D side per ADR-003
  §3.1's amended Phase 3.5 finding.

  Capture path (B5 analog) ships in v1.6.x PR-D.

  11 new tests covering: P_A1 shape / Hermiticity / idempotence /
  rank-10 / caching; u_move_a1 shape / lives-in-A_1-subspace /
  null-move + out-of-range error paths / operator norm ≤ 1 /
  **intra-orbit strict unitarity on range(P_A1)**.

### Added — v1.6.x Track 1 PR-A: qm_2d_dynamics skeleton

- **New `chess_spectral.qm_2d_dynamics` module** — Track B Zeno layer
  for 2D, mirroring `qm_4d_dynamics` at d=2. Ships:
  - `H_FREE_2D()` — the free-particle Hamiltonian `H_0 = -Δ_{P_8²}`
    as a 64×64 sparse Hermitian matrix (Kron-sum of two `L_8`
    path-graph Laplacians; spectrum in `[-7.7, 0]`).
  - `evolve_under_h0(psi, t, *, channel=None)` — Zeno-style
    continuous-time evolution `U(t) = exp(-i H_0 t)`. Accepts a
    single 64-dim channel block or the full 640-dim ψ (broadcasts
    `H_0` across the 10 channels via `I_{10} ⊗ H_0`); optional
    `channel=` evolves a single named block.

  This is the smallest brick of the §17.2 surface — closes the v1.5
  asymmetry where 4D shipped the full Track B + bridge but 2D only
  had Track A kinematics. Per-channel `u_move_*_2d` builders and
  the qm_2d_bridge dispatch ship in subsequent v1.6.x PRs.

  17 new tests in `tests/test_qm_2d_dynamics.py`: H_FREE_2D
  Hermiticity, negative-semidefinite spectrum, [−7.7, 0] bounds;
  `evolve_under_h0` norm + energy preservation, U(-t)∘U(t)=I,
  per-channel broadcast match, `channel=` only touches that block;
  error paths (wrong shape, 2-D input, ambiguous `channel=` on
  64-dim ψ, unknown channel name).

### Changed — v1.6.x: stale `--rounds-per-pair` reference in tournament help

- Fixed: `spectral_py tournament --help` description text said
  `--rounds-per-pair` but the actual flag is `--n-games-per-pair`
  (a leftover from an early draft of the spec). User-visible only;
  no behavior change.

### Documentation — v1.6.x README refresh

- **`python/README.md` (the PyPI long-description) now calls out
  v1.6.** New "What's new in v1.6" section covering: search +
  tournament + sweep CLI commands, the three §16.1 evaluator
  families, the in-house 4D bitboard move generator
  (`spatial_4d`), the graph-Laplacian legality oracle, the v5
  unified wire format with empirical 7.23× compression on 4D, and
  the `verify-wheels` CI gate. Cross-links to
  [`docs/WIRE_FORMAT.md`](../docs/WIRE_FORMAT.md) for the byte-level
  v2/v3/v4/v5 spec.

## [1.6.0] — 2026-04-30

The §16 ship-gate release. v1.5 shipped the QM extension at 4D; v1.6
makes the framework testable end-to-end on real games at both
dimensions: search core, tournament harness, agent-spec CLI, and the
sweep ship-gate runner. Plus the v5 unified wire format
(reader/writer at all three encoding modes), the in-house 4D bitboard
move generator, the graph-Laplacian legality oracle, and a doc set
that finally calls out the `.spectralz[4]` byte layout from the user
side.

The §16.5 / §2787 per-depth Elo sweep is the empirical gate that
v1.6 unblocks; running it (manually, against the user's chosen
fixture set) is now a one-line invocation
(`spectral_py sweep --evaluators material,spectral,qm --depths 1,2,3,4 ...`).

### Tests — immolation suite augmentation

- **7 new tests in `tests/test_smoke_e2e.py`** covering the v1.6
  engine CLI commands: 2D `search` (all 3 evaluators from starting
  position + arbitrary FEN), 2D `tournament` (minimal 2-agent + the
  per-side-asymmetric §16 use case), 2D `sweep` (2×2 matrix), 4D
  `search` (two-kings position), 4D `tournament` (two-kings start).
  Sub-suite runs in < 5 s on a warm interpreter (depth=1, max_plies≤10).
  Closes the immolation gap that would have let regressions in the
  agent-spec parser or the round-robin loop slip past CI.

### Added — v1.6 engine CLI surface

- **`spectral_py sweep` ship-gate runner.** One-shot driver for the
  §16.5 / §2787 ship-gate matrix. Builds the cross product of
  `--evaluators` × `--depths` (default 3 × 4 = 12 cells), runs a
  full round-robin with the same single-process tournament harness
  as `tournament`, and emits Elo ratings + per-pair records as JSON.

  ::

      spectral_py sweep \
          --evaluators material,spectral,qm \
          --depths 1,2,3,4 \
          --n-games-per-pair 10 \
          --time-budget-ms 5000 \
          -o sweep_results.json

  Per-cell games are omitted from the output by default (`--include-
  games` to add them); the aggregate `pair_records` is what the §16
  ship-gate evaluation reads. Each cell carries the same agent
  options; for per-cell asymmetry use `tournament` with explicit
  `--agent` specs.

- **`search` and `tournament` subcommands** wired into both
  `chess_spectral.cli` (2D) and `chess_spectral_4d.cli` (4D), driven
  by a shared **agent-spec parser** in
  `chess_spectral.engine.tournament.agent_spec`. Per-side symmetric
  spec syntax — white and black are independently configured. The
  §16 ship-gate's "white=spectral@4 vs black=qm@3" pattern is a
  first-class CLI use case. Per-spec keys: `label`, `evaluator`
  (material/spectral/qm), `depth`, `time_budget_ms`, `weights` (path),
  `quiescence_max_depth`, `no_tt`, `no_mvv_lva`, `no_quiescence`.

### Documentation

- **New `docs/WIRE_FORMAT.md`** — canonical user-facing spec for the
  `.spectral[z]` / `.spectralz4` binary container. Covers all four
  shipped versions (v2 / v3 / v4 / v5), the encoding modes within v5
  (dense / per-channel / xor-stream), the reader-dispatch convention
  (peek 12 bytes → route by version), backward-compat guarantees,
  and the gzip transport wrapper. Cross-linked from ROADMAP.md and
  python/README.md. This is the user-facing companion to the v5 design
  ADR (`docs/adr/wire_format/ADR-001-v5-unified-encoding-modes.md`).

- **python/README.md** updated to mention `frame_v5.py` alongside
  `frame.py` (v2 legacy reader) and `frame_4d.py` (v3/v4 legacy
  reader). Module layout section now reflects the v5 unified format
  as the default for new writes from v1.6.

### Tracked — to be fixed in v1.6 follow-up

- **LTO/IPO segfault in `spectral encode --pgn -z` on Linux release.**
  When `chess` (python-chess) is installed in CI (necessary for the
  `engine.search` package introduced in PR-5), the
  `test_pgn_to_spectralz_real_game` test runs the full PGN ingestion
  pipeline. On `ubuntu-latest + release` (the only preset with
  `CMAKE_INTERPROCEDURAL_OPTIMIZATION=TRUE`), the C process consistently
  segfaults across 3 retries. The same C binary passes on:
  - `ubuntu-latest + asan` (LTO disabled)
  - `macos-14 + release` (different LTO impl)
  - `windows-latest + msvc-release` (no LTO by default)
  - all 15 cibuildwheel verify-wheels cells (no LTO)

  Marked `xfail(strict=False)` on `sys.platform.startswith("linux")` in
  `tests/test_smoke_e2e.py::test_pgn_to_spectralz_real_game` to keep
  the merge train moving. To investigate: build on Linux with
  `-fno-strict-aliasing`, gdb the segfault location, then either fix
  the underlying UB or drop IPO from the release preset.

  This is NOT a regression — the test was previously skipped because
  `chess` wasn't installed in CI; PR-5 made the install explicit and
  surfaced the dormant bug. The C `spectral encode --pgn -z` path
  has been broken on Linux LTO builds since at least v1.5.0.

### Added — v1.6 wire format unification

- **v5 XOR-stream encoding (Python)** per ADR-001 (v1.6 PR-D). Mode 2
  of three. Each frame's stored encoding bytes are the bit-XOR (uint32-
  wise) of the real encoding with the previous reconstructed frame.
  Frame 0 is XOR'd with zero = verbatim. The reader applies cumulative
  XOR to reconstruct.

  Wins on chess hypervectors specifically: most channels stay stable per
  ply, so XOR yields long zero-byte runs that gzip compresses
  essentially for free. Empirical 4D spike: **7.23× compression** vs
  dense gzipped on a 50-ply knight-tour fixture; 2D spike was 1.08×
  (gzip already eats most of the redundancy on the 640-dim 2D
  encoding).

  Public API additions:
  - ``pack_frame_xor_2d`` / ``pack_frame_xor_4d``
  - ``write_v5_xor_2d`` / ``write_v5_xor_4d``
  - ``iter_v5_frames_xor_stream`` (cumulative-XOR streaming reader)

  Frame body layout: identical to mode 0 (dense) — the bytes are just
  XOR-encoded relative to the previous frame. This is what makes XOR
  the leanest encoding mode (no per-frame size overhead, just bit-XOR
  on a fixed-size payload).

  7 new tests in ``test_frame_v5.py``: first-frame-verbatim invariant;
  full 2D + 4D round-trip; bit-exact lossless reconstruction for
  random floats (the load-bearing property — XOR results can produce
  NaN bit patterns that must round-trip); zero-byte runs for stable
  frames; gzip compression sanity on 4D fixture; iter rejects wrong
  mode. Local sweep: 39/39 v5 tests pass.

### Fixed — bit-exact dense pack/unpack for XOR-mode payloads

- **``pack_frame_2d_dense`` / ``pack_frame_4d_dense`` now use byte-exact
  copy (``ndarray.tobytes()`` / ``np.frombuffer``) instead of
  ``struct.Struct(f"<{N}fI4B").pack(*tolist(), ...)``. The struct path
  silently normalized NaN bit patterns when going through float64 in
  ``.tolist()``, which broke XOR-stream round-trips: legitimately stored
  NaN-shaped XOR results were losing payload bits. With the byte-exact
  path, all 2^32 float32 bit patterns round-trip including NaNs and
  denormals.

- **v5 per-channel replacement encoding (Python)** per ADR-001 (v1.6
  PR-C). Mode 1 of three. Each frame stores only the channels that
  differ from the previous frame; the very first frame emits all
  channels with a FULL flag (so the reader has a baseline). Wins on
  workloads where most channels are stable across plies — the v1.6
  spike measured 4D 2.84× compression vs dense gzipped on a 50-ply
  knight-tour fixture.

  Public API additions:
  - ``pack_frame_per_channel`` / ``unpack_frame_per_channel``
  - ``write_v5_per_channel_2d`` / ``write_v5_per_channel_4d``
  - ``iter_v5_frames_per_channel`` (streaming reconstructor)

  Frame body layout per ply: u32 body_size + u8 flags + u8
  n_channels_present + (channel_idx u8 + reserved u8 + channel buffer
  float32[channel_dim]) × n_channels_present + move-metadata tail
  (8 B 2D / 14 B 4D, same as mode 0). Channels are reshaped from the
  encoder's flat output (10×64=640 for 2D; 11×4096=45056 for 4D).

  10 new tests in ``python/tests/test_frame_v5.py``: full-frame and
  delta-frame round-trips for 2D + 4D; no-change frame emits zero
  channels; end-to-end write-then-read; sanity that mode 1 produces a
  smaller file than mode 0 on stable-channel workloads; negative
  tests on shape mismatch + missing prev for delta unpack.

- **v5 unified wire format reader/writer (Python, dense mode)** per
  ADR-001 (v1.6 PR-B). New ``chess_spectral.frame_v5`` module ships the
  256-byte v5 header that supersedes v2 (.spectralz) and v4
  (.spectralz4). Header carries explicit ``n_dimensions`` (2 or 4)
  and ``encoding_mode`` (0=dense, 1=per-channel, 2=XOR-stream); the
  three-mode dispatch is what makes a single header serve both 2D and
  4D files at every encoding level.

  Public API:
  - ``HeaderV5`` dataclass (``pack`` / ``unpack`` / sanity checks)
  - ``pack_frame_2d_dense`` / ``unpack_frame_2d_dense`` — same body as
    v2 dense, just carried under v5's header
  - ``pack_frame_4d_dense`` / ``unpack_frame_4d_dense`` — same body as v4
  - ``write_v5_dense_2d`` / ``write_v5_dense_4d`` — full file writer
    in mode 0 (the eventual ``--encoding=full`` flag's effect)
  - ``peek_version`` — auto-detects v2/v4/v5 by reading 12 bytes
  - ``open_read_transparent`` — gzip-aware fp opener
  - ``read_v5_header`` / ``iter_v5_frames_dense`` — streaming reader

  PR-B implements **dense (mode 0) only** and the version-dispatch
  surface. Modes 1 (per-channel replacement) + 2 (XOR-stream) ship in
  PR-C / PR-D; the C-side mirror in PR-E; CLI wiring in PR-F.

  Backward compat: legacy v2/v4 readers in ``frame.py`` /
  ``frame_4d.py`` stay forever; existing files keep working
  unmodified. v5 writer produces a different header but the dense
  frame body bytes are identical to v2/v4, so a v5 file decoded as
  raw frames matches its v2/v4 equivalent byte-for-byte (modulo the
  header).

### Added — v1.6 phase 6 prep

- **2D search core** (`chess_spectral.engine.search`) per §16.2
  (v1.6 PR-5). Standard alpha-beta game-tree search wrapping the
  §16.1 evaluator API:
  - **Negamax + alpha-beta pruning** with iterative deepening from
    depth 1 up to `max_depth`.
  - **Transposition table** (Zobrist-hashed via
    `chess.polyglot.zobrist_hash`) with EXACT / LOWER / UPPER bound
    types. Replaces shallow with deep on collision; FIFO-evicts on
    bounded-size overflow.
  - **MVV-LVA move ordering** (captures by victim/attacker value;
    TT-suggested move first; deterministic non-capture tiebreak).
  - **Quiescence search** (capture-only extension at leaves with
    stand-pat baseline; depth-bounded to cut pathological capture
    chains).
  - **Time-budget short-circuit** (millisecond deadline; aborted
    iterations are discarded so the result is always at the deepest
    fully-completed iteration).
  - **Ablation flags** for the §16 tournament: `use_tt`,
    `use_mvv_lva`, `use_quiescence`. Each can be turned off
    independently to isolate per-component effect on Elo.

  Public API:
  - `chess_spectral.engine.search.search(board, evaluator, options)
    -> SearchResult` — single entry point. `board` is a
    `chess.Board`; `evaluator` is any of the §16.1 evaluators
    (material / spectral / qm); `options` is a `SearchOptions`
    dataclass.
  - `SearchResult` — `best_move`, `best_score`, `depth_reached`,
    `nodes_searched`, `elapsed_ms`, `pv` (principal variation),
    `tt_hits`, `tt_size`.
  - `SearchOptions` — `max_depth=4`, `time_budget_ms=None`,
    `use_tt=True`, `use_mvv_lva=True`, `use_quiescence=True`,
    `quiescence_max_depth=8`.
  - Internal modules (importable but not __all__): `core` (negamax /
    iterative deepening), `ttable` (TranspositionTable, BoundType),
    `ordering` (MVV-LVA), `quiescence`, `_board_adapter` (chess.Board
    → encoder position dict in O(piece_count), ~10x faster than
    FEN round-trip).

  Determinism: `search(board, evaluator, options)` is a deterministic
  function of (board state, evaluator, options). No RNG, no clock-
  dependent ordering. Required for the §16 tournament's reproducible
  Elo computation.

  Mate handling: mate-in-1 found at `max_depth=1`; mate-in-2 found
  at `max_depth=3`. Mate-distance correction: faster mates score
  higher (subtract `ply_from_root` from `MATE_SCORE`).

  Test surface: 29 unit tests in `tests/test_engine_search.py`
  covering basic correctness, mate detection, terminal positions,
  determinism, all ablation flags, time budget, all three evaluators
  driving the search uniformly, TT internals, move ordering,
  board_to_position adapter parity, PV starts with best_move.

  Note: 4D search core ships as a follow-up PR.

- **QM-expectation evaluator** at both 2D and 4D (v1.6 PR-4). Third
  and final §16.1 evaluator family. Computes
  `score = Σ_p α_p · ⟨ψ|(I_n ⊗ H_p)|ψ⟩` where ψ is the QM lift of
  the encoder output (qm_2d / qm_4d), `H_p` is the per-channel
  Hermitian piece-reach observable for piece p (rook / bishop /
  queen / king / knight; pawns deferred per qm_4d ADR-005). The
  lifted operator is computed channel-by-channel for memory
  efficiency (no 640×640 / 45 056×45 056 materialization).

  Public API (mirrored 2D + 4D, identical to spectral evaluator
  contract):
  - `chess_spectral.engine.eval.qm.evaluate(position, side_to_move,
    *, weights=None) -> float`
  - `evaluate_breakdown(...)` — per-piece contributions for the
    §17.2 `evaluatePosition.breakdown` HUD field.
  - `observable_expectations(psi) -> dict[piece_name, float]` — raw
    `⟨ψ|(I⊗H_p)|ψ⟩` per piece.
  - `load_weights_json(path)` — same validation discipline as the
    spectral evaluator: typo'd piece names raise `ValueError`.
  - `DEFAULT_WEIGHTS` / `PIECE_NAMES` (2D); `DEFAULT_WEIGHTS_4D` /
    `PIECE_NAMES_4D` (4D). Default weight = 1.0 per piece;
    intentionally unbiased per §16's empirical-tournament-as-truth
    discipline.

  All three §16.1 evaluator families now ship with the same API
  contract (`evaluate(position, side_to_move) -> float`,
  side-to-move-flipped, deterministic). The §16 self-play
  tournament harness (PR-7) can iterate over all three uniformly.

  **§16.7 framing:** the QM-expectation form `⟨ψ|O|ψ⟩` is
  *structurally different* from the spectral evaluator's linear
  channel-energy sum. Whether QM faces the same depth-decay the
  Othello prior documented for spectral weighting is genuinely open
  per §16.7's design notes — that's the load-bearing empirical
  question §16's tournament harness will answer.

  Test surface: 30 unit tests in `tests/test_engine_qm.py` covering
  observable-expectation API (real-valued, shape-checked, zero-psi
  graceful), evaluator core (empty / non-empty / side-to-move
  flip / weights), JSON round-trip + validation, breakdown
  consistency (sum = evaluate, sign-flip), 4D anti-podal-kings
  graceful zero (encoder-kernel handling), API surface, and
  cross-evaluator-family signature consistency.

- **Spectral channel-energy evaluator** at both 2D and 4D (v1.6 PR-3).
  2D 640-dim encoder. Sibling of `chess_spectral.qm_4d` (4D, 45 056-
  dim, shipped in v1.5.0). Closes the asymmetry surfaced during v1.6
  Phase 6 planning: the §16 plan calls for a QM-expectation evaluator
  on **both** 2D and 4D, but v1.5.0 only shipped the 4D side. Without
  `qm_2d`, the §16 ship gate (per-depth Elo sweep across material ×
  spectral × QM at 2D and 4D) cannot be met. v1.6 PR-1.

  Public API (mirrors qm_4d):
  - `state_to_psi(position, side_to_move)` — encode position to
    L2-normalized ψ ∈ ℂ^640 with Z_2 sector flip on side-to-move.
  - `inner_product`, `norm`, `expectation` — linear-algebra primitives.
  - `is_normalized`, `is_hermitian`, `is_unitary` — validation
    predicates.
  - `d4_closure`, `d4_element_name`, `d4_unitary_rep_64`,
    `d4_unitary_rep_full` — order-8 D_4 hyperoctahedral group action.
    8-element cached LUT (vs B_4's 384 in 4D); `d4_unitary_rep_full`
    is `I_10 ⊗ U_64(g)` on ℂ^640.
  - `channel_projector(c)`, `prob_channel`, `measure_channel_distribution`
    — 10-channel PVM (`A1`, `A2`, `B1`, `B2`, `E`, `F1`, `F2`, `F3`,
    `FA`, `FD` × 64 modes each).
  - `H_rook_2`, `H_bishop_2`, `H_queen_2`, `H_king_2`, `H_knight_2` —
    sparse Hermitians on ℂ^64 built from the 8×8 piece reach
    predicates. Lazily cached via `__getattr__`. Rook spectrum is
    integer {-2..14} on the open `P_8 × P_8` lattice; the four others
    are non-integer due to boundary clipping (same physics as the 4D
    side).
  - `H_pawn_2` — raises `NotImplementedError` with a deferral pointer
    to a future pseudo-Hermitian / η-metric extension (mirrors qm_4d
    ADR-005 disposition).
  - `build_H_piece_2(piece)`, `measure_observable_distribution(H, ψ)`
    — explicit constructors and Born-rule eigenbasis helpers.

  Test surface (44 tests in `tests/test_qm_2d.py`): state-to-psi
  shape/normalization/Z_2 parity, D_4 closure + unitary lift +
  caching, channel PVM idempotency + orthogonality + completeness,
  Born probabilities sum to one, all 5 Hermitian piece observables
  Hermitian within float, rook integer spectrum verified, pawn raises
  with informative message, expectation real for Hermitian, and
  spectral-decomposition Born weights sum to ‖ψ‖².

- **Spectral channel-energy evaluator** at both 2D and 4D (v1.6 PR-3).
  Second of the three §16.1 evaluator families. Computes
  `score = Σ_c w_c · ‖proj_c(v)‖²` from the encoder output, where
  `proj_c` slices the per-channel mode block (10 × 64 in 2D; 11 ×
  4096 in 4D).

  Public API (mirrored 2D + 4D):
  - `chess_spectral.engine.eval.spectral.evaluate(position,
    side_to_move, *, weights=None) -> float` — score from
    side-to-move's perspective. `weights` accepts None (default
    equal-weighting per §16.1.2's "intentionally bland defaults"
    rationale), a `{channel_name: float}` dict, or a path to a
    JSON weights file.
  - `evaluate_breakdown(position, side_to_move, *, weights=None) ->
    dict[str, float]` — per-channel score contributions (already
    side-to-move-flipped). Sum equals `evaluate`. Required for the
    §17.2 `evaluatePosition` bridge method's `breakdown` field that
    the chess4D-OC HUD displays.
  - `channel_energies(v) -> dict[str, float]` — per-channel L2
    energies from any encoder output vector. Sum equals `‖v‖²` by
    Plancherel. Useful for direct channel inspection.
  - `load_weights_json(path) -> dict[str, float]` — loads per-channel
    weights from a JSON file. Missing channels default to 1.0;
    **unknown channel names raise `ValueError`** so a typo in a
    weights file doesn't silently produce wrong scores.
  - `DEFAULT_WEIGHTS` / `DEFAULT_WEIGHTS_4D` — equal 1.0 per channel.
    Documented as intentionally non-tuned: §16's tournament harness
    is the empirical mechanism for weight refinement, and Phase 7
    learned-weight work is where any hand-tuning would land.

  Default weights are unbiased per §16.7 — the Othello prior shows
  spectral channel-energy weighting is structurally analogous to
  Architecture A in the Edax-Othello archive (which won +243 Elo at
  L6 and decayed to 0 at L10+). Whether chess shows the same
  depth-decay is the load-bearing empirical question §16 answers.

  Test surface: 27 unit tests in `tests/test_engine_spectral.py`
  covering Plancherel sanity (sum of channel energies == ‖v‖²),
  empty / non-empty positions, side-to-move sign flipping, default
  vs custom weights, partial-weights default-to-1.0, JSON
  round-trip, JSON unknown-channel raises, JSON non-dict raises,
  breakdown sums to evaluate, 4D pawn-axis-distinguishes-channels
  (FA_PAWN_W vs FA_PAWN_Y), and namespace re-export sanity.

- **`chess_spectral.engine` and `chess_spectral_4d.engine`** — Phase 6
  evaluator/search/tournament namespaces (v1.6 PR-2). Bootstraps the
  engine package skeleton with the **material evaluator** (the first
  of the three §16.1 evaluator families):

  Public API (mirrored at both 2D and 4D):
  - `chess_spectral.engine.eval.material.evaluate(position,
    side_to_move, *, values='spectral') -> float` — material score
    from side-to-move's perspective. `values` accepts `'spectral'`
    (default; uses `tables.SPECTRAL_VALS`), `'standard'` (textbook
    `tables.VALS` 1/3/3.5/5/9/100), or a custom `{piece_char: float}`
    dict (pieces absent from the dict score 0; useful for ablations).
  - `chess_spectral.engine.eval.material.evaluate_white(position, *,
    values='spectral') -> float` — convenience: always white's
    perspective, no side-to-move flip. For HUD displays / corpus
    statistics.
  - `chess_spectral_4d.engine.eval.material.evaluate(...)` — 4D
    analogue. Strips pawn axis (`('P', 'w')` → `'P'`) before value
    lookup; legacy single-char `'P'`/`'p'` accepted without warning
    spam (search loops would otherwise drown in deprecation noise).

  No encoder call, no scipy, no math beyond integer addition. Pure
  baseline that the spectral / QM evaluators (PR-3 / PR-4) are
  empirically tested *against* in the §16 self-play tournament. The
  evaluator-API contract (`evaluate(position, side_to_move) -> float`,
  side-to-move-flipped, deterministic) is now established for the
  search core (PR-5) to consume.

  Test surface: 27 unit tests in `tests/test_engine_material.py`
  covering empty / starting / lopsided positions, side-to-move sign
  flipping, all three value-table modes, custom dict ablation, 4D
  pawn-axis stripping, legacy single-char pawn acceptance, unknown
  piece chars score 0, unknown table strings raise `ValueError`,
  cross-dim consistency (a rook is worth the same in 2D and 4D), and
  namespace re-export sanity.

## [1.5.0] — 2026-04-29

The QM-extension release. Adds **chess_spectral.qm_4d** (Track A
kinematic — quantum-mechanical front-end on top of the 4D encoder),
**chess_spectral.qm_4d_dynamics** (Track B Phase 4 — full move-as-
unitary dynamics across all 11 channels for non-capture AND capture
moves), and **chess_spectral.qm_4d_bridge** (the §17.1 7-method
Pyodide bridge surface plus 6 §17.5 dev/debug methods). Also
consolidates the v1.4.0-era API gap fixes (which were prepared but
never tagged on PyPI; rolled into this release).

The chess4D-OC downstream consumer can integrate via
`pip install chess-spectral==1.5.0` and call the new bridge methods
through the Pyodide worker.

### Added

#### v1.4 API gap surface (originally prepared for v1.4.0; rolled in)

- **`apply_move(state, from_sq, to_sq, *, promote_to='Q')`**
  ([`chess_spectral_4d.apply_move`](chess_spectral_4d/apply_move.py)).
  Promotion-piece argument with default `'Q'` for back-compat;
  accepts any of `Q`, `R`, `B`, `N`. Closes the v1.3.x silent auto-
  queen behavior. Tested with all four targets × white/black × W-axis
  /Y-axis pawns.

- **`MoveHistory4D` + `GameState4D` + `Move4D`**
  ([`chess_spectral_4d.move_history`](chess_spectral_4d/move_history.py)).
  Append-only ply-history container with side-to-move and FIDE half-
  move-clock plumbing. SHA-256 position hashing for repetition
  tracking. Side-to-move and clock are tracked on the history
  container, NOT the position dict — keeps the encoder's input
  contract unchanged.

- **Threefold-repetition + 50-move-rule + insufficient-material draw
  detection** via `chess_spectral_4d.bridge.get_draw_status(state, *,
  has_legal_moves=...)`. Returns one of `'none' | 'threefold' |
  'fifty-move' | 'insufficient' | 'stalemate'`. 2D insufficient-
  material classification matches python-chess; 4D analog raises
  `NotImplementedError` (open design question on the bishop "color
  class" rule for Z_8^4).

- **`get_move_history(state)` + `load_state(fen4)`** bridge methods —
  Pyodide-friendly history list and FEN4 → GameState4D re-import.

- **`fen_4d.serialize(pos)`** ([`chess_spectral.fen_4d`](chess_spectral/fen_4d.py)).
  Inverse of `parse`; canonical sorted output. Round-trip property
  `parse(serialize(p)) == p` tested across 130 fixtures.

- **chess4d 0.4 castling + EP regression test** in the immolation
  suite confirming no silent-corruption bugs in the upstream rules
  library.

#### Track A kinematic QM front-end (`chess_spectral.qm_4d`)

The kinematic layer — state space, observables, measurement structure,
and symmetry / group action. *What* the QM picture's states and
operators look like. The dynamics — *how* states evolve, including
both move-as-unitary and continuous time evolution — live in the
sibling `qm_4d_dynamics` module described below.

- **`state_to_psi(state, side_to_move)`** — encoder output cast to
  `complex128` ψ ∈ ℂ^45056, L2-normalized, with Z_2 superselection
  via the side-to-move sign multiplier (resolves the 8-collision
  central-inversion + color-flip kernel from Pre-flight 1).

- **11-channel projection-valued measure** with Born-rule helpers:
  `prob_channel(psi, c)`, `measure_channel_distribution(psi)`.

- **Five Hermitian piece-reach observables** (`H_rook_4`, `H_bishop_4`,
  `H_queen_4`, `H_king_4`, `H_knight_4`) — graph-adjacency matrices
  in disguise; lazy module-level construction. Per-piece spectrum
  bounds: rook `[-4, 28]` (integer; vertex-transitive lattice degree),
  bishop `[-12, 54.4]`, queen `[-16, 81.9]`, king `[-22, 67.7]`,
  knight `[-36.06, 36.06]`. Pawn observables raise
  `NotImplementedError` pointing at Track B's pseudo-Hermitian
  η-metric path.

- **`b4_unitary_rep(g)`** — B_4 hyperoctahedral group representation
  on ℂ^4096; Kronecker-extension to ℂ^45056 via `b4_unitary_rep_full`.
  384-element cached LUT.

#### Track B Phase 4 dynamics (`chess_spectral.qm_4d_dynamics`)

The dynamics layer — *how* states evolve under both continuous time
(`evolve_under_h0`) and discrete move-as-unitary transitions (the 11
per-channel `u_move_*` builders). The pre-conditions — what states
and observables look like — live in the sibling `qm_4d` module
described above.

- **`evolve_under_h0(psi, t, *, channel=None)`** — Zeno-style time
  evolution under H_0 = -Δ_{P_8^4} via `scipy.sparse.linalg.expm_multiply`.
  Norm-preserving, energy-conserving, time-reversal-symmetric.
  `H_FREE_4D` cached singleton sparse Hamiltonian. Spectrum matches
  the `tables_4d.kron_sum4_eigvals` Pre-flight 3 verification at
  1.30e-13 residual.

The 11 per-channel move-as-unitary builders:

- **All 11 per-channel `u_move_*` builders** for non-capture AND
  capture moves:
  - `u_move_a1` (A_1 trivial irrep; strict unitary same-orbit only)
  - `u_move_std4(state, move, axis)` for axis ∈ {X,Y,Z,W} (spatial
    coord channels; strict unitary same-orbit + same-`|coord_resid|`)
  - `u_move_fa_pawn(state, move, axis)` for axis ∈ {W,Y} (pawn
    antisymmetric channels; strict unitary axis-flip pairs only)
  - `u_move_fib_meas(state, move, fib_idx)` for fib_idx ∈ {1,2,3}
    (FIB_SYM channels; measurement-only re-encode per Phase 3.5
    amendment to ADR-003 §3.3)
  - `u_move_fd_diag` (FD_DIAG; rank-1 update + renormalization, cond
    p95 = 8.6 < 100 acceptance gate)

- **Capture handling** for all channels via Option A (re-encode +
  marker dict carrying `psi_post_block` + `captured_piece`). Capture
  reasons: `capture-rank-1-with-renorm` (A_1, STD4_*, FD_DIAG),
  `capture-partial-isometry` (FA_PAWN_*), `capture-measurement-only`
  (FIB_SYM_*).

- **`M_pawn = M_single + M_double` decomposition** per Phase 3.5
  amendment to ADR-005. `_build_m_pawn_single(axis)` is P_w-pseudo-
  Hermitian at residual 0.000e+00 (matches Probe 3); `_build_m_pawn_
  double(axis)` accounts for the η-breaking double-push starting-rank
  term.

- **ADR-001 phase formulas** per channel family: A_1 = 1, STD4_a =
  `e^(i × π/4 × δ_a)`, FA_PAWN_a = `e^(i × π/2 × sgn(δ_a))`.

#### §17.1 Pyodide bridge surface (`chess_spectral.qm_4d_bridge`)

- **7 §17.1 consumer methods**:
  - `get_qm_state(state)` → `{ok, psi, basisDim, normSq}` with
    ComplexArray = real+imag interleaved Float32 wire format
  - `get_qm_density(state, piece_id=None)` → `{ok, density}`
    (per-piece marginal raises NIE → v1.7+)
  - `apply_move_qm(state, move)` → assembled per-channel dict
    (csr_matrix + marker dict heterogeneous values)
  - `apply_move_qm_full(state, move)` → assembled ψ_post via per-
    channel dispatch (the measurement-only-re-encode dispatch logic;
    THE key new infrastructure)
  - `measure_at(state, coords, observable=None, *, rng=None)` →
    Born-rule projective measurement
  - `get_density_matrix_of(state, piece_id)` → raises NIE → v1.7+
    (partial trace over channels)
  - `get_probability_current(state)` → `j_p(c) = Im(ψ* ∇ψ)` field
    via Kron-sum lattice-gradient operator (anti-Hermitian by
    construction; integrated divergence ≈ 0)
  - `get_qm_expectation(state, observable)` → `⟨ψ|H|ψ⟩` for named H

- **6 §17.5 dev/debug methods**: `get_version`, `get_encoder_shape`,
  `get_fen4_state`, `load_fen4`, `load_jsonl_fixture`,
  `has_legal_moves(state, team)`.

- **`complex_to_interleaved_float32`** Pyodide-bridge serialization
  helper (the §17.1 ComplexArray wire format).

#### Documentation, design records, and audits

- **5 Track B Architecture Decision Records** in
  [`docs/adr/qm_4d/`](../docs/adr/qm_4d/): ADR-001 (per-channel B_4
  irrep phase), ADR-002 (Zeno time evolution; Stinespring deferred),
  ADR-003 (tiered per-channel move transformation; FIB measurement-
  only; orbit-restricted strict-unitary), ADR-004 (Z_2 superselection
  via state_to_psi, NOT operator anti-commutation), ADR-005 (pawn
  pseudo-Hermitian η-metric, two-tier delivery).

- **Phase 3.5 prototype probes + ADR amendments**: 4 probe scripts
  validating each ADR's design gate, plus
  [`PHASE_3_5_PROBE_RESULTS.md`](../docs/adr/qm_4d/PHASE_3_5_PROBE_RESULTS.md)
  documenting 3 amendments (FIB → measurement-only, ADR-004 §3.4
  weakened to state-level parity, ADR-005 M_single/M_double
  decomposition).

- **ADR-003 §3.1 amendment** for the orbit-restricted strict-unitary
  tier (Phase 4 B1's empirical finding):
  [`ADR-003-AMENDMENT-orbit-restriction.md`](../docs/adr/qm_4d/ADR-003-AMENDMENT-orbit-restriction.md).

- **Phase 4 B4 Z_2 grading state-level test surface** — 15 tests
  verifying `state_to_psi` IS the canonical sector-flip mechanism;
  complementary positive surface to the pre-existing no-anti-
  commutation tests.

- **Bridge contract documentation** — new
  [`docs/bridge_api.md`](../docs/bridge_api.md) (704 lines): consumer-
  facing API contract for chess4D-OC and other Pyodide consumers.
  Tone matches `FEN4_FORMAT.md` / `NDJSON4_FORMAT.md`.

- **Documentation overstrong-claim audit** —
  [`docs/AUDIT_v1.5_DOCS.md`](../docs/AUDIT_v1.5_DOCS.md) (924 lines,
  35 findings across STRONG / MEDIUM / WEAK severity tiers). Two
  user-flagged claims softened inline (the "first 4D chess engine
  ever shipped" and "must test at L4/L8/L16" phrasings); remaining
  30 findings deferred to user review.

- **`--help` discipline audit + 10 mechanical fixes** —
  [`docs/AUDIT_v1.5_HELP_DISCIPLINE.md`](../docs/AUDIT_v1.5_HELP_DISCIPLINE.md).
  Per the §16.4 immolation discipline rule; all 10 violations were
  the same shape (subparser missing `description=`) and were fixed
  inline.

- **Immolation suite embiggenment**: 41 → 81 tests (+40 new) covering
  v1.4 API gaps + Track A kinematic + Phase 4 channel builders +
  apply_move_qm dispatch + B2 evolution + §17.1 bridge surface +
  Pre-flight smoke. The canonical release gate now exercises every
  v1.5 surface.

### Changed

- **README expanded 200 → 473 lines** with v1.5 surface: 4D quick-
  start example, `qm_4d` / `qm_4d_dynamics` / `qm_4d_bridge` sections,
  v1.4 API gaps section, §17.1 bridge contract section, refreshed
  CLI section (current console-script syntax), `phase_operators_4d`
  section (overdue from v1.3), and a "See also" cross-referencing
  the research notebooks. Bump-resistant version-example snippet
  preserved (uses `__version__ == __version__` equality, NOT a
  literal version string).

- **Targeted overstrong-claim softening** in research notebook §16
  + 4D notebook + ADR-001:
  - "first 4D chess engine ever shipped" → "we make no 'first ever'
    claim"
  - "must test at L4/L8/L16" → "test at multiple representative
    depths; L4/L8/L16 are illustrative starting points"

### Notes

- **Phase 4 closes**; all 11 channels handle non-capture + capture
  moves. `apply_move_qm` returns assembled per-channel dict for ALL
  inputs; never raises NotImplementedError.

- **v1.4.0 was prepared but never tagged on PyPI.** All v1.4-era
  work (the API gap surface above) is consolidated into this v1.5.0
  release. The semver bump is minor (1.3.2 → 1.5.0); skipping 1.4
  reflects that no shipping artifact ever carried that version.

- **Deferred to v1.6+**: Phase 6 chess engine + tournament harness
  (search core + 3 evaluator families + self-play harness + per-depth
  Elo sweep). The chess4D-OC consumer can integrate v1.5 in parallel
  with v1.6 work.

- **Deferred to v1.7+**: per-piece marginals (`get_qm_density(piece_id=…)`),
  reduced density matrices (`get_density_matrix_of`), full Stinespring
  dilation for capture handling, ADR-003 Option (b) orbit-quotient
  refactor, ADR-005 v1.6 promotion to full η-metric pseudo-Hermitian
  pawn observables.

## [1.4.0] — never released; rolled into v1.5.0

> **Note:** v1.4.0 was prepared and committed but never tagged on
> PyPI. All v1.4-era work (the nine API gaps captured in research
> notebook §16.9 + §17.3 — the chess4D-OC consumer's wish-list
> before Phase 6 engine work begins) is consolidated into v1.5.0.
> The detailed entries below are preserved as the historical record;
> the canonical user-facing summary is the [1.5.0] section above.

Closes the nine API gaps captured in research notebook §16.9 + §17.3
(the chess4D-OC consumer's wish-list before Phase 6 engine work
begins). All of v1.3.x's existing API and tests remain green; this
release is purely additive.

### Added

- **FEN4 round-trip — `chess_spectral.fen_4d.serialize(pos) -> str`.**
  Inverse of `parse`. Round-trip property: `parse(serialize(p)) == p`
  for any valid position. Output is canonical (pieces sorted by
  ascending square index, separated by `"; "`); empty positions
  serialize to just `"4d-fen v1:"` (the bare prefix). Closes §16.9
  #4. Tested in `tests/test_fen4_round_trip.py` against:
  the 15 fixture positions (`tests/fixtures/positions_4d.jsonl`),
  100 seeded random self-play positions, the 4096-piece
  every-cell stress case, and the empty-position + canonical-form
  invariants.

- **State-load API — `chess_spectral_4d.bridge.load_state(fen4)`.**
  Wraps `fen_4d.parse` + `GameState4D.from_fen4` and returns either
  `{"ok": True, "state": GameState4D}` on success or `{"ok":
  False, "error": "..."}` on parse failure. Closes §16.9 #5.
  Tested in `tests/test_load_state_4d.py` with encoding-parity vs
  direct `parse()` on 4 fixture FENs and round-trip via
  `state.to_fen4()`.

- **Promotion-piece argument — `apply_move(state, from_sq, to_sq,
  *, promote_to='Q')`** (new module
  `chess_spectral_4d.apply_move`). Default `'Q'` matches the
  v1.3.x silent auto-queen behavior; accepts any of `'Q'`, `'R'`,
  `'B'`, `'N'` (case-insensitive). Color is inferred from the
  moving pawn (white pawn → uppercase, black pawn → lowercase).
  Promotion is triggered iff the moving piece is a pawn and the
  destination is on the appropriate "promotion rank" for the
  pawn's `(color, axis)`; `promote_to` is silently ignored on
  non-promotion moves (matches python-chess semantics). Closes
  §16.9 #1. Tested in `tests/test_apply_move_promotion_4d.py`
  with all four targets × white/black × W-axis/Y-axis pawns,
  plus encoded-vector reflects-promoted-piece checks.

- **Move-history plumbing — `chess_spectral_4d.move_history`.**
  New `Move4D` (frozen dataclass record), `MoveHistory4D`
  (append-only ply list with side-to-move, half-move-clock, and
  position-hash table), and `GameState4D` (position + history
  bundle). Position hashing for repetition tracking uses SHA-256
  of `serialize(pos)` plus the side-to-move byte (deterministic,
  collision-resistant in practice; no Zobrist tables to maintain).
  Side-to-move and half-move clock are tracked **on the history
  container, not on the position dict** — keeps the encoder's
  input contract unchanged. Closes §16.9 #2 prerequisite.

- **Threefold-repetition detection.** Triggered when any
  `(position, side-to-move)` hash count reaches
  `THREEFOLD_THRESHOLD = 3`. Reachable via
  `gs.history.repetition_count(pos)` and through
  `bridge.get_draw_status` (priority: threefold > 50-move >
  insufficient > stalemate). Closes §16.9 #2. Tested in
  `tests/test_game_state_4d.py` with a deterministic 8-ply A→B→A→B
  cycle (3 occurrences of the starting position) — draw fires at
  ply 8.

- **50-move-rule detection.** `MoveHistory4D.half_move_clock`
  resets to 0 on any pawn move OR capture (FIDE Article 9.3) and
  increments otherwise. Threshold `FIFTY_MOVE_THRESHOLD = 100`
  (50 full moves). Reachable via `gs.history.half_move_clock` and
  through `bridge.get_draw_status`. Closes §16.9 #3. Tested with
  a 100-half-move two-king walk through 51 unique squares per
  side (no threefold contamination).

- **Insufficient-material classification (2D) —
  `bridge.is_insufficient_material_2d(pos_2d)`.** Matches
  python-chess: K-vs-K, K+B-vs-K, K+N-vs-K, and K+B-vs-K+B with
  bishops on same-color squares all classify as `True`; K+P,
  K+R, K+Q, two-knights-one-side, and opposite-color KBKB all
  classify as `False`. Closes the 2D half of the new §17.3 row.
  4D analog (`is_insufficient_material_4d`) raises
  `NotImplementedError` — the bishop "color class" rule on Z_8^4
  is an open design question deferred to a future ADR.

- **`getDrawStatus()` bridge method —
  `bridge.get_draw_status(state, *, has_legal_moves=...)`.**
  Returns `{"ok": True, "status": <one of 'none', 'threefold',
  'fifty-move', 'insufficient', 'stalemate'>}`. Detection priority:
  threefold > 50-move > insufficient > stalemate. Stalemate
  detection requires the caller to pass `has_legal_moves=True`
  or `False`; if `None` is passed (default) and no other draw
  fires, the function raises `NotImplementedError` rather than
  silently mis-classifying a stalemate as `'none'`. The 4D
  legal-moves observable is wired in v1.5+ (Track A's QM
  roadmap); 2D callers can compute the boolean via python-chess
  and pass it through. Closes §17.3 row 1.

- **`getMoveHistory()` bridge method —
  `bridge.get_move_history(state)`.** Returns
  `{"ok": True, "moves": [<Move4D.to_dict()>, ...]}`. Each entry
  carries `ply`, `from`, `to`, `piece`, `halfMoveClock`, plus
  optional `promoteTo` and `capturedPiece` keys. Pyodide-bridge
  friendly (no internal types leak out; pure-Python lists +
  dicts + ints). Closes §17.3 row 2.

- **Castling + en-passant regression suite — chess4d 0.4 audit.**
  `tests/test_castling_ep_4d_regression.py` (8 tests; ~7 pass + 1
  path-dependent skip on a typical run) exercises chess4d's
  castling-rights bookkeeping, EP-target tracking, and Move4D flag
  surface. Findings documented in
  `python/research/chess4d_castling_ep_audit.md`: chess4d 0.4
  handles both edge cases correctly through its `legal_moves()`
  generator; no silent-corruption bugs found, no regression patch
  needed. Closes §17.3 castling + EP rows.

### Test count delta

The new test files add **210 passing tests + 1 path-dependent
skip** on top of the v1.3.2 baseline. Breakdown:

| File | Passing | Skipped |
|---|---|---|
| `test_fen4_round_trip.py` | 130 | 0 |
| `test_load_state_4d.py` | 16 | 0 |
| `test_apply_move_promotion_4d.py` | 26 | 0 |
| `test_game_state_4d.py` | 31 | 0 |
| `test_castling_ep_4d_regression.py` | 7 | 1 |
| **Total** | **210** | **1** |

All v1.3.2 tests continue to pass — 102 tests in the fast subset
(`test_version_consistency`, `test_roundtrip_4d`, `test_fen4_parity`,
`test_encoder_4d`); 44 876 in the parametric phase-operator suites;
260 in the pawn-axis / phase-4d-check / phase-4d-unobstructed
suites; 92 in the 2D phase_operators suite. No regressions.

### Bridge contract pinned in `chess_spectral_4d/__init__.py`

The new public surface is exposed at the top level:

    GameState4D, Move4D, MoveHistory4D       # game-state types
    SIDE_WHITE, SIDE_BLACK                   # side-to-move
    coord_to_sq, sq_to_coord                 # 4D ↔ linear index
    position_hash_key                        # repetition hash
    apply_move                               # state-application
    bridge                                   # Pyodide-bridge module

with the FEN4 serializer at `chess_spectral.fen_4d.serialize`.

### Deferred to future minors

- **4D insufficient-material classification.** Open design question
  on the bishop "color class" rule for Z_8^4. v1.4.0 ships the 2D
  version (`is_insufficient_material_2d`) and a placeholder
  `is_insufficient_material_4d` that raises `NotImplementedError`.
  Tracked for a v1.5.x or v1.6.x ADR.
- **4D stalemate detection.** Requires the QM legal-moves
  observable currently being built in Track A. v1.4.0's
  `get_draw_status` accepts `has_legal_moves: bool` to defer the
  decision to the caller; the boolean will become a `state.has_legal_moves`
  property in v1.5+ when the legal-move generator is wired
  through.

## [1.3.2] — 2026-04-28

Two correctness fixes that ride together: the v1.3.1 corpus-encoding
bug (the user-reported `FEN4 parse error -4` truncation) and the
long-running `__version__` string drift. No API change.

### Fixed

- **`spectral_4d encode` (NDJSON4 → .spectralz4) no longer truncates
  FEN4 input at 2048 bytes.** Pre-1.3.2 the bulk encode path used a
  2 KiB stack buffer for each FEN4 string, plus an 8 KiB stack
  buffer for each NDJSON line. Real chess4d positions serialize to
  ~9.4 KiB at startpos and well above for any in-game position, so
  the bulk path was effectively unusable for the chess4d corpus —
  it produced a header-only `.spectralz4` (256 bytes) and a
  misleading `FEN4 parse error -4` (`CODE_BAD_COORD`) on stderr.
  The single-position writer (`encode-fen4`) was unaffected because
  it points directly at `argv` with no buffer copy. Fix:
    - The internal FEN4 buffer in `cmd_encode` grew from 2 KiB stack
      to 64 KiB heap; the line buffer grew from 8 KiB stack to 80
      KiB heap. Both buffers are paired with `free()` calls on every
      exit path.
    - `json_str_field4` now returns `-2` on overflow (instead of
      silently truncating to fit). The caller emits a clear
      `"FEN4 string longer than 64 KiB"` error, so any future
      hypothetical overflow surfaces as actionable diagnostic
      output rather than as a misleading parse failure downstream.
    - The same fix is applied to the 2D `spectral encode` path
      (`json_str_field` returns `-2` on overflow; the 2D `fen[]`
      buffer grew from 128 to 8192 bytes — 2D FENs are short, but
      the silent-truncate failure mode was identical).
  New regression tests: [`test_encode_long_fen4.py`](tests/test_encode_long_fen4.py)
  pins the 193-piece originally-broken case and the 4096-piece
  worst-case fully-loaded board. The immolation suite
  ([`test_smoke_e2e.py`](tests/test_smoke_e2e.py)) now asserts
  byte-equivalence between the two C 4D encode paths
  (`encode-fen4 --fen4 STRING` vs `encode -i NDJSON4`) at both
  short and long-FEN4 sizes — the invariant that makes the
  truncation bug impossible to ship again.

- **`chess_spectral.__version__` no longer drifts from the dist
  version.** Pre-1.3.2 the string was hardcoded at `"1.2.3"` and
  never updated across six successive `pyproject.toml` bumps
  (1.2.4, 1.2.5, 1.2.6, 1.3.0, 1.3.1). Users on v1.3.1 who imported
  `chess_spectral.__version__` saw "1.2.3" while
  `importlib.metadata.version("chess-spectral")` correctly reported
  "1.3.1". Both `chess_spectral.__version__` and
  `chess_spectral_4d.__version__` now derive dynamically from
  `importlib.metadata`; they cannot drift again.

### Changed

- **`chess_spectral_4d.VERSION` is now an alias for
  `__version__`** (the dist version). Pre-1.3.2 it carried a
  separate "encoder format version" string ("1.1.3") that bumped on
  protocol changes — but the two version concepts caused more
  confusion than the artifact-protocol distinction was worth, with
  multiple dist releases shipping while VERSION stayed pinned.
  Collapsed to a single source of truth (the dist version in
  `pyproject.toml`). `chess-spectral-4d version` will now print the
  dist version in its banner instead of "1.1.3".

### Added (continued)

- **`tests/test_version_consistency.py`** pins three regression
  assertions: `chess_spectral.__version__`,
  `chess_spectral_4d.__version__`, and `chess_spectral_4d.VERSION`
  must all equal `importlib.metadata.version("chess-spectral")`.
  Future hardcoding regressions fail at test time.

- **Immolation suite version-drift guard**
  ([`test_smoke_e2e.py::test_no_hardcoded_version_strings_drift_in_shipped_python`](tests/test_smoke_e2e.py)).
  Walks shipped Python sources and fails on any
  `__version__ = "X.Y.Z"` literal other than the documented
  `"0.0.0+unknown"` fallback, AND asserts that `pyproject.toml` and
  `pyproject-pure.toml` agree on the dist version. This is the
  structural backstop for the `__version__` drift bug: even if a
  future contributor reintroduces a hardcoded literal, the release
  gate catches it. Pre-1.3.2 our drift-catching only ran when the
  package was pip-installed; this one runs against the source tree.

- **README's stale `('1.1.3', '1.1.3')` literal example output**
  replaced with a bump-resistant equality check (`__version__ ==
  __version__` between the two packages, plus a comment pointing at
  `importlib.metadata`). The literal was already wrong by 1.1.4; the
  drift was invisible because no test scrutinised README contents.

## [1.3.1] — 2026-04-28

Two distribution improvements riding on one patch release. No API
or behavior change for users on supported platforms; this is purely
about widening the set of *installable* environments.

### Added

- **`py3-none-any` pure-Python wheel.** The chess-spectral release
  now ships a pure-Python wheel alongside the platform-specific
  wheels. This unblocks installation in environments that can't run
  our bundled `_native/spectral{.exe}` binaries:
  - **Pyodide / micropip** in browsers (mobile + desktop). The
    Pyodide runtime is single-process WASM with no `fork`/`exec`,
    so even a WASM build of our binaries couldn't be `subprocess`'d.
    The pure wheel uses the Python encoder paths exclusively —
    bit-for-bit equivalent to the C output (verified by
    `test_c_py_parity*`).
  - **Less-common platforms** where we don't ship a platform wheel
    (fresh Linux ARM, BSDs, etc.). pip falls through to the pure
    wheel after exhausting platform candidates.

  Per-release artifact count goes from 15 platform wheels + sdist
  (16) to 15 platform wheels + 1 pure wheel + sdist (17). Built via
  hatchling (a separate [`pyproject-pure.toml`](pyproject-pure.toml))
  because scikit-build-core's primary contract is platform wheels.
  See the new `build-pure-wheel` job in
  [`chess-spectral-publish.yml`](../../../.github/workflows/chess-spectral-publish.yml)
  for the build invocation. Verified locally: the pure wheel
  installs cleanly in a fresh venv; CLI commands work via Python
  fallback; `_find_c_binary()` correctly returns `None`; 4D phase
  ops + encoder produce expected outputs.

  **Performance note for pure-wheel users.** The Python encoder is
  ~30-60× slower than the C binary on most workloads. For Pyodide
  hover-renderer use cases (one preview encoding per hover, often
  with delta caching per
  [`bench_incremental_encoding.py`](research/bench_incremental_encoding.py)),
  this is well within interactive budget. For batch corpus encoding
  on a fresh ARM box, users will notice the slowdown; we recommend
  building from sdist (which the platform wheel pipeline does)
  instead.

- **Python 3.14 wheels.** The cibuildwheel matrix in
  [`.github/workflows/chess-spectral-publish.yml`](../../../.github/workflows/chess-spectral-publish.yml)
  was missing a cp314 entry — an oversight from the v1.2.4 publish-
  pipeline build-out (set up before 3.14 was released). Adding 314
  to the matrix grows the per-release platform-wheel count from 12
  to 15 (3 OS × 5 Python). The corresponding
  `Programming Language :: Python :: 3.14` classifier is added to
  `pyproject.toml` and `pyproject-pure.toml`.

## [1.3.0] — 2026-04-28

Adds the **chess4d-OC phase-operator move engine** — the 4D analogue
of the 2D `chess_spectral.phase_operators` package — validated
against [`python-chess4d-oana-chiru`](https://pypi.org/project/python-chess4d-oana-chiru/),
the Python reference implementation of Oana & Chiru (2026). Closes
the §11 phase-operator hypothesis arc on 4D: the φ_4d coprime
cyclic phase structure fully captures the Oana-Chiru piece geometry
on `Z_8^4`, both unobstructed and with occupancy.

Full design + experimental record:
[`docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md`](../../PHASE_OPERATOR_SUPPLEMENT_4D.md).

Minor version bump (not patch) because this adds a substantial new
public API surface (`chess_spectral.phase_operators_4d`).

### Added

- **`chess_spectral.phase_operators_4d` package** — 4D phase
  operators with the same shape as the 2D `phase_operators`
  package:
  - `MODULUS_4D = 145451`, `GEN_X = 9719`, `GEN_Y = 647`,
    `GEN_Z = 43`, `GEN_W = 3`, plus precomputed shift tuples
    and `phi4(x,y,z,w)`.
  - Piece operators: `P_rook4`, `P_bishop4`, `P_queen4`,
    `P_king4`, `P_knight4`, and pawn ops parameterized by
    `axis ∈ {'w', 'y'}` per O&C §3.10 Def 11.
  - `phase_to_coords_4d`: `PHI_TO_XYZW`, `XYZW_TO_PHI`,
    `invert(phi)`, `phase_set_to_board(phases)`.
  - `occupation_aware_moves_a_4d(state, origin, piece)` —
    Solution A: phase-op candidates ∩ chess4d oracle dests.
  - `phasecast_is_check_4d(state, color)` — pawn-aware reverse
    cast; non-pawn-only variant
    `phasecast_is_check_4d_no_pawns` retained for ablation.
  - `move_leaves_king_in_check_4d(state, move)` — pawn-aware
    move filter; non-pawn-only variant
    `move_leaves_king_in_check_4d_no_pawns` retained.

- **Pinned design** via mixed-radix tower with **ladder
  coefficient 14** (vs the 2D framework's effective 8). Phase B's
  structural gate caught a real failure at the original
  ladder-coefficient-7 attempt: the Phase A constraints (C1-C4)
  passed at `(M=12181, GEN=(1523,191,23,3))` but operator-shift
  differences span `[-14, 14]^4` and that wider box surfaced an
  integer dependency `g_y = 10·g_w + 7·g_z` (i.e.,
  `191 = 30 + 161`) that caused cross-piece destination aliasing.
  The new fifth constraint **C5: operator-aliasing freedom** is
  codified in
  [`tests/test_phase_4d_design.py::test_c5_no_integer_dependency_in_minus14_to_14_box`](tests/test_phase_4d_design.py)
  so this regression cannot recur silently. See
  [PHASE_OPERATOR_SUPPLEMENT_4D §13.1.4](../../PHASE_OPERATOR_SUPPLEMENT_4D.md)
  for the full story.

- **`research/chess4d_phase_design.py`** — design search +
  brute-force `[-14, 14]^4` dependency verifier. Ported from
  [`docs/othello-maths/research/coprime_generators.py`](../../../othello-maths/research/coprime_generators.py)
  and extended to 4 axes.

- **Test suites** (under `python/tests/`):
  - `test_phase_4d_design.py` — 15 tests: C1 coprime, C2 image
    bijection, C3 non-subgroup, C4 derived-gen distinctness,
    **C5 [-14,14]^4 integer-dep-freedom**, plus O&C-mobility
    cross-checks.
  - `test_phase_4d_unobstructed.py` — 24 tests including the
    Phase B structural gate at 4096 origins × 9 piece configs
    against `tables_4d.X_targets` (36,864 set-equality
    assertions).
  - `test_phase_4d_occupation_aware.py` — Phase C+E gate at
    44,803 (state, origin, piece) cases against the
    `python-chess4d-oana-chiru` oracle. ~3 minutes runtime.
  - `test_phase_4d_check_detection.py` — 232 tests covering both
    `_no_pawns` and pawn-aware variants, plus 7 hand-built
    targeted check constructions (rook on x-axis, knight (2,1)
    leap, bishop xy-diagonal, queen zw-diagonal, blocked rook,
    W-axis pawn check, Y-axis pawn check).

- **Cross-pollination from `docs/othello-maths/`**:
  - The *coprimality is necessary but not sufficient* discipline
    (Patch 2 of
    [`CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`](../../../othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md))
    motivates Phase A's full image-bijection check.
  - The Z_2 channel framing for axis-tagged pieces (§3 Option B
    of [`OTHELLO_PHASE_OP_PREFLIGHT.md`](../../../othello-maths/OTHELLO_PHASE_OP_PREFLIGHT.md))
    aligns with the encoder's existing W/Y antisym pawn channel
    split. Phase E's pawn capture geometry (xw / xy plane) is
    the natural lift.

- **Immolation suite extensions** (`tests/test_smoke_e2e.py`):
  - `test_4d_phase_operators_smoke` — touch each P_X4 operator on
    a sample origin; assert O&C interior mobilities and
    rook ∪ bishop = queen.
  - `test_4d_phase_check_detection_smoke` — initial position has
    no check from either color, both `_no_pawns` and full paths.
  - `test_no_unwired_stubs_in_shipped_python_or_c` — meta-test
    walks the shipped sources and fails if any function still
    contains `cmd_todo("...")` (C) or `_not_implemented(...)`
    (Python) — the regression class that shipped 12 unwired CLI
    commands in v1.2.3.

### Changed

- **`safety_field.compute_safety_field` no longer accepts
  `include_pawns`**. The §9o safety-field hypothesis (ΔS tracks
  engine-Δeval) was tested in v1.0 and produced a null result
  (`ρ ≈ 0`) — see
  [`chess_spectral_research_notebook.md`](../../chess_spectral_research_notebook.md)
  §9o. The `include_pawns` parameter was originally added in
  v1.2.4 as a "future hook" for the symmetric-pawn-Laplacian
  extension (with `True` raising `NotImplementedError` to avoid
  the silent-discard mode it had in v1.2.3). With the parent
  hypothesis confirmed dead, reserving the hook adds maintenance
  cost without benefit; the parameter is removed. The default
  `include_pawns=False` math is preserved verbatim for §9o
  reproducibility. Closes v1.2.4 inventory item #14 with a
  documented "rejected — failed exploration" outcome rather than
  a deferred wiring.

- **`pyproject.toml::[project.optional-dependencies] test`** adds
  `python-chess4d-oana-chiru>=0.3.3` so the Phase C/D gates can
  import the oracle. *Not* in main `dependencies` (would create
  a circular install — `python-chess4d-oana-chiru[spectral]`
  already depends on `chess-spectral`). The phase operator
  package itself is pure-stdlib for unobstructed reach;
  `chess4d` is imported lazily inside Solution A and the
  reverse-cast functions, so the package still works without the
  test extra installed.

### Documentation

- **New: `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md`** —
  occupies the §13 slot in the 4D notebook, mirrors the 2D
  supplement's structure (§13.1 design / §13.2 ops / §13.3
  empty-board gate / §13.4 occupation-aware / §13.5 check
  detection / §13.6 pawn axis / §13.7 transfer summary / §13.8
  cross-pollination credits).
- **`docs/chess-maths/chess_spectral_4d_notebook.md`** appends a
  high-level "Phase operators (v1.2)" pointer to the new
  supplement.
- **`docs/othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`**
  status header updated to **FULLY APPLIED** with citations. A
  PR-closure audit confirmed all six patches were already present
  in [`chess_spectral_research_notebook.md`](../../chess_spectral_research_notebook.md)
  (Patches 1-5 at the documented section locations; Patch 6's D₄
  character-table audit was applied with the corrected B₁ / B₂
  rows in [`chess_d4_direct.py`](../../chess_d4_direct.py) and
  [`chess_spectral/tables.py`](chess_spectral/tables.py)). A
  programmatic class-constancy verifier reproducing the audit was
  run and reported PASS for all five irrep rows. The Othello
  orphan-data loop is closed; no follow-up PR needed.

## [1.2.6] — 2026-04-27

Security patch closing CodeQL alert
[#26](https://github.com/lemonforest/mlehaptics/security/code-scanning/26)
(`cpp/command-line-injection`, severity: critical).

### Fixed

- **PGN bridge is no longer launched through a shell.** The C `encode`
  command's PGN ingestion path historically built a command line with
  `snprintf` (interpolating user-supplied `--url` and `--input`
  arguments) and ran it via `popen()`, which routes through `cmd.exe
  /c` on Windows and `/bin/sh -c` on POSIX. CodeQL correctly flagged
  this as `cpp/command-line-injection`: a `--url` containing shell
  metacharacters (`&`, `;`, backtick, `"`, …) would be interpreted as
  shell syntax. The bridge now spawns directly via `fork()` +
  `execvp()` on POSIX and `_pipe()` + `_dup2()` + `_spawnvp()` on
  Windows, with each token (interpreter, script path, flag, value)
  passed as one opaque element of an argv array. No shell is ever
  involved, so user-supplied input cannot escape into command syntax.
  Verified by a negative test: a URL containing `" & echo PWNED & "`
  is now passed verbatim to `pgn_bridge.py` (which rejects it as a
  malformed URL) instead of executing the embedded `echo`.
  ([`src/main.c`](src/main.c) — new `bridge_proc_t`, `bridge_open()`,
  `bridge_close()`; `CS_POPEN` / `CS_PCLOSE` macros removed.)

### No behavior change for legitimate inputs

All 230 Python tests pass against the rebuilt binary with the new
spawn path. PGN file ingestion, stdin PGN ingestion, URL fetch,
`--pgn-start` / `--pgn-count` slicing, and the bridge's exit-code
propagation all behave identically to 1.2.5; only the underlying
process-launch mechanism changed.

## [1.2.5] — 2026-04-27

Re-attempt of the v1.2.4 release. The 1.2.4 tag's publish workflow
hung indefinitely on GitHub Actions' macos-13 (Intel) runner queue
and never reached the PyPI upload step. No 1.2.4 wheels exist on
PyPI. v1.2.5 is the same package contents as v1.2.4 with a working
publish pipeline.

### Fixed

- **Publish workflow drops macos-13 from the wheel matrix.** Apple's
  Intel Mac line is in deprecation; GitHub Actions macos-13 runner
  capacity is severely constrained — runs queue 1+ hour without ever
  starting. Matrix shrinks 4 OS × 4 Python = 16 cells to 3 OS × 4
  Python = 12 cells (`ubuntu-latest`, `macos-14`, `windows-latest`).
  The chess-spectral source still works on Intel Macs; users on that
  platform get the sdist (compiles in ~20 s with cmake + a C
  compiler) instead of a pre-built wheel.

- **CodeQL Default Setup → Advanced Setup.** Default Setup was
  triggering a parse-error status on
  `docs/chess-maths/chess_d4_direct.py` — a research script that's
  not part of any released package. The file parses cleanly under
  CPython 3.9–3.14 (`py_compile` + `ast.parse` succeed at every
  feature_version); CodeQL's specific Python extractor has a quirk
  with it. Default Setup also ran `c-cpp` analysis with
  `build-mode: none` (buildless extraction → less accurate results)
  because our `CMakeLists.txt` isn't at the repo root. New
  `.github/workflows/codeql.yml` runs CodeQL with `build-mode:
  manual` for c-cpp (full cmake build before extract → tracing
  extraction → full type/include coverage) and honors
  `.github/codeql/codeql-config.yml`, which scopes Python analysis
  to the actual shipped packages (`chess_spectral/**`,
  `chess_spectral_4d/**`) plus the antikythera-maths package.
  Research scripts under `docs/chess-maths/` are out of scope.

### No source changes from 1.2.4

The chess-spectral source tree (encoder math, CLI commands, table
data, immolation suite) is byte-identical to 1.2.4. Only CI/release
infrastructure changed.

## [1.2.4] — 2026-04-25

Wires every advertised CLI command and ships the native binaries inside
the wheel. Patch-level because every wired command was already in the
help text and module docstrings — `1.2.3` users had a reasonable
expectation they worked. This release closes the gap between what was
promised and what shipped.

See [ROADMAP.md](../ROADMAP.md) for the current command surface.

### Added — Phase A (FEN4 + single-position encoding)

- **FEN4 v1 placement-literal format** — see [docs/FEN4_FORMAT.md](../docs/FEN4_FORMAT.md).
  Compact, human-readable 4D position literal: `4d-fen v1: K@0,0,0,0;
  k@7,7,7,7; Pw@1,2,3,4`. Pawn axis (W or Y) is mandatory per
  Oana & Chiru Definition 11.
- **C FEN4 parser** in `include/cs_fen_4d.h` + `src/cs_fen_4d.c`.
- **Python FEN4 parser** in `chess_spectral.fen_4d` (`parse`,
  `Fen4ParseError`, `parse_to_jsonl_obj`).
- **C 4D frame I/O** in `include/cs_frame_4d.h` + `src/cs_frame_4d.c`
  (header + frame + read/write helpers, byte-equivalent to
  `python/chess_spectral/frame_4d.py`).
- **`spectral_4d encode-fen4`** (was `cmd_todo` stub) and
  **`chess-spectral-4d encode-fen4`** (was `_not_implemented` stub).
  Both produce byte-identical 1-frame v4 `.spectralz4` files.
- **57 FEN4 parity tests** in `tests/test_fen4_parity.py` covering
  parser accept/reject + C↔Python byte equivalence (plain + gzipped).

### Added — Phase B (bulk encoding + corpus)

- **NDJSON4 ply-log format** — see [docs/NDJSON4_FORMAT.md](../docs/NDJSON4_FORMAT.md).
  One FEN4 per line + optional move metadata. No move replay (mirrors
  the 2D NDJSON pipeline).
- **`spectral_4d encode`** (was stub) — NDJSON4 → v4 `.spectralz4` bulk
  encoder. Header backfill, optional gzip via `cs_gzip`.
- **`spectral_4d csv`** (was stub) — per-ply 11-channel energies +
  dist/cos/dA1 + 8-coord move metadata.
- **`chess-spectral-4d encode-moves4`** (was stub) — Python sibling of
  the C `encode`. Renamed `--fen` → `--fen4` in `encode-fen4` for clarity.
- **`chess-spectral-4d corpus-gen`** (was stub) — wraps N NDJSON4
  ply-logs into a corpus folder + manifest.json.
- **15 e2e parity tests** in `tests/test_e2e_spectralz4_parity.py`
  covering bulk encode + csv determinism.

### Added — Phase C (2D CLI completion)

- **`spectral compare`** — cosine-similarity report between two
  .spectral files (min/mean/max + ply with min cosine).
- **`spectral query`** — 10-channel energy breakdown at a given ply.
- **`spectral heatmap`** — ANSI 8×8 heatmap of one channel at one ply.
- **`spectral analyze`** — JSON summary of A1 peak / drop / crisis ply.
  Heuristics from `chess_spectral_research_notebook.md` §p.1636-1648
  (ΔA₁ derivative analysis).
- **`spectral export`** — full .spectral → JSON dump for the web viewer.
- **`spectral play`** — ply-by-ply listing (non-interactive; defers
  the interactive viewer to a follow-up).
- **Python wrappers** for all five (compare, query, heatmap, analyze,
  export) registered as `spectral_py` subcommands. Output byte-identical
  to the C side.
- **14 2D CLI parity tests** in `tests/test_2d_cli_parity.py`.

### Fixed

- **`compute_safety_field(include_pawns=True)` no longer silently
  produces the `False` answer**. The `include_pawns` parameter was
  previously discarded with `del include_pawns # TODO: ...` (AUDIT
  inventory item #14). It now raises `NotImplementedError` with a
  pointer to the tracking issue. Default behavior (`include_pawns=False`)
  is unchanged.
- **`test_encoder_starting_position_channel_energies` had stale expected
  values** for B1 / B2 (45.2825 / 45.2825 — likely from a pre-PATCH-6
  audit version). Both C and Python encoders now agree on
  B1=0.0 / B2=19.8450; the test was updated to match (AUDIT #24b).
- **Parity test no longer silently skips when fixtures absent**
  (AUDIT #22). `tests/test_parity.py` now generates a synthetic
  3-ply fixture using the C binary if the Carlsen-Caruana cache isn't
  available, ensuring real assertions run in CI.

### Changed

- **Build system: hatchling → scikit-build-core**. The wheel now
  includes the `spectral` and `spectral_4d` native binaries inside
  `chess_spectral/_native/`. PyPI users get the ~38× C encoder
  speedup automatically.
- **`_find_c_binary` extended** to look in the wheel `_native/` dir
  before falling back to repo build paths. New `_find_c_binary_4d` for
  the 4D binary.
- **CMakePresets.json** added with `release` / `dev-debug` / `asan` /
  `msvc-release` presets (per [AUDIT_2026-04.md F-07](../AUDIT_2026-04.md)).
- **GitHub Actions**: existing `chess-spectral-publish.yml` rewritten
  in place to use cibuildwheel (matrix: linux/macos/windows ×
  py3.10–3.13) — preserves the trusted-publisher binding and the
  autotag dispatch path. New `chess-spectral-ci.yml` adds per-PR
  build + test on representative cells PLUS a `verify-wheels` job
  that runs cibuildwheel (cp312 only, all 3 OSes) on every PR — this
  catches wheel-build regressions before tag-push so the publish
  workflow doesn't discover scikit-build-core / cibuildwheel config
  bugs at release time.
- **`STUBBED_CHANNELS` machinery removed** from
  `tests/test_c_py_parity_4d.py` (~40 lines) — no channels have been
  stubbed since v1.1.1/P6 (AUDIT #17).
- **Stale scaffolding comments removed** from `CMakeLists.txt`,
  `src/cs_encoder_4d.c`, and `python/chess_spectral/tables_4d.py`
  (AUDIT #15, #16, #18).
- **Broken plan-file references** (`when-we-need-to-spicy-seahorse.md`,
  `ticklish-dreaming-platypus.md`) replaced with pointers to the
  new [ROADMAP.md](../ROADMAP.md) (AUDIT #19, #20, #21).
- **`miniz` dependency surface documented** at the top of
  `src/cs_gzip.c` — explicitly lists which miniz APIs we use and
  which we deliberately avoid (AUDIT #25).

### Tests

- Total: **156 passing**, 0 skipped (was 27 + 3 skipped before this
  release). 86 of those are new in v1.2.4 (FEN4 + e2e + 2D CLI parity).
- C↔Python byte-for-byte parity now gated end-to-end for both 2D and
  4D encoders, including 1-frame and N-frame `.spectralz` / `.spectralz4`
  files.

## [1.2.3] — 2026-04-24

Restores the `[corpus]`-optional contract documented in 1.2.x.
`spectral-chess4d-oana-chiru` (and any other 4D-only consumer) can
now `pip install chess-spectral` without the `[corpus]` extra and
still `import chess_spectral` cleanly.

### Fixed

- **Eager-import regression in `chess_spectral.phase_operators`.**
  Six submodules (`castling`, `occupation_field`, `occupation_aware_a/b/c`,
  `phase_check_detection`) had a top-level `import chess` that ran
  during `from chess_spectral import ...`, transitively forcing
  python-chess (~1.5 MB) as a hard dependency even though the
  project declares `chess` as `[corpus]`-optional.  All six now use
  `TYPE_CHECKING`-gated annotations and function-body lazy imports.

  `castling.py` additionally replaced the module-level
  `chess.WHITE` / `chess.BLACK` references (used as keys in the
  `CASTLES` dict literal) with explicit `_WHITE = True` /
  `_BLACK = False` constants — documented as matching the stable
  python-chess API where `chess.Color is bool`.

### Measured impact

- `import chess_spectral` with python-chess **blocked from
  sys.meta_path**: succeeds in ~3.1 s (was `ImportError` before).
- `import chess_spectral` with python-chess available: 3590 ms →
  3174 ms (−416 ms, 11 % faster; python-chess no longer loaded
  eagerly).
- `sys.modules` count after import: 555 → 554.

### API surface

No public API changes.  All names re-exported from
`chess_spectral` and `chess_spectral.phase_operators` continue to
work identically when python-chess is installed.  Calling a chess-
dependent function (e.g. `occupation_aware_moves_a`, `available_
castles`) without python-chess installed raises `ImportError` at
call time with a clear message, instead of at import time.

### Tests

All 161 tests pass (92 phase_operators + 69 core).
`tests/test_parity.py::test_encoder_starting_position_channel_energies`
is a known pre-existing failure unrelated to this change
(expected values in the fixture have not been updated since the
1.2.1 B₁/B₂ character fix); it fails identically on `main` at
1.2.2.

## [1.2.2] — 2026-04-23

Source-tree consistency follow-up to 1.2.1.  The 1.2.1 release corrected
`chess_spectral.tables.CHARS` in the Python package but did not
regenerate the companion C data file `src/cs_tables_data.c`, which
continued to hold the pre-fix B₁/B₂ rows.  The PyPI wheel is pure-Python
and therefore was already correct at 1.2.1 — users who `pip install
chess-spectral==1.2.1` saw the fix via `tables.py`.  **Users who rebuild
the companion `spectral.exe` / `spectral_4d.exe` C binaries from source
(CMake Release) at the 1.2.1 tag would get the old broken B₁/B₂ values**
and the C ↔ Python parity test (`tests/test_c_py_parity.py`) would
diverge.  1.2.2 closes that gap.

### Fixed

- Regenerated `src/cs_tables_data.c` from the corrected Python
  `tables.CHARS` by re-running `codegen/emit_tables.py`.  Delta vs
  1.2.1 is 2 lines (only the CHARS[3] and CHARS[4] rows), matching
  the Python delta committed in 1.2.1:

      B₁: {1,-1, 1,-1, 1,-1, 1,-1}   →  {1,-1, 1,-1, +1,+1,-1,-1}
      B₂: {1,-1, 1,-1,-1, 1,-1, 1}   →  {1,-1, 1,-1,-1,-1,+1,+1}

- Rebuilt `spectral.exe` locally (CMake Release target) against the
  regenerated C source and re-ran the committed parity test:

      OK: 88 frames × 640 dims, max |delta| = 0 (byte-identical),
      move metadata identical

  End-to-end regression: Python fix (from 1.2.1) → codegen →
  regenerated C source (this release) → rebuilt C binary →
  spectralz v4 frames all agree.

### No PyPI wheel changes

- The pure-Python wheel produced by hatchling at 1.2.2 is byte-
  identical to the wheel produced at 1.2.1.  The release exists to
  keep the tagged source tree internally consistent and so that
  `git diff chess-spectral-v1.2.1 chess-spectral-v1.2.2 -- chess-spectral/src/`
  is a legible 2-line C data delta.  Same pattern as the 1.1.3
  "pipeline-exercise" release that drove the autotag → PyPI chain
  end-to-end without changing behaviour.

### Advisory for spectralz users

Any `.spectralz` v4 frames produced by a C binary built from source at
or before 1.2.1 have stale B₁/B₂ dims (640-dim encoding, channels
128-191 and 192-255).  Pure-Python-encoded frames are unaffected.
Affected users should re-encode their corpora with a 1.2.2-built C
binary (or any Python-backed encoder at 1.2.1+).

### Changed

- Version bumped 1.2.1 → 1.2.2 (semver patch; source-tree
  consistency; no public-API change).

## [1.2.1] — 2026-04-23

Bug-fix release.  The `CHARS` character table in `chess_spectral.tables`
had a class-constancy violation on the B₁ and B₂ rows that silently
broke idempotence of `project_irrep` on those two irreps.  Sanity tests
(A₁ D₄-invariance, fiber reconstruction) were unaffected and did not
catch the bug.  The defect was discovered by the Othello Phase 1 pass
(`docs/othello-maths/`) which lifted the table to D₄×Z₂, at which point
the failure surfaced as a loud idempotence violation (error ~0.64 on
B₁⁻ and B₂⁻ projections).

### Fixed

- **D₄ character table class-constancy bug in `tables.py` (CHARS).**
  Prior B₁ row `[1,-1, 1,-1, 1,-1, 1,-1]` and B₂ row
  `[1,-1, 1,-1,-1, 1,-1, 1]` failed class-constancy on the conjugacy
  classes `{g=4, g=5}` (axis reflections — σ_v and σ_h) and
  `{g=6, g=7}` (diagonal reflections — σ_d and σ_d').  Verified by
  direct conjugation on `D4_PERMS`: `g₁ · g₄ · g₁⁻¹ = g₅` and
  `g₁ · g₆ · g₁⁻¹ = g₇`, so each reflection pair is conjugate and
  every valid character row must assign them the same value.
- Corrected rows: `B₁ = [1,-1, 1,-1, +1, +1, -1, -1]` (axis reflections
  +1, diagonal −1), `B₂ = [1,-1, 1,-1, -1, -1, +1, +1]` (axis −1,
  diagonal +1).  Post-fix `project_irrep` sanity: idempotence max
  error 2.2×10⁻¹⁶, completeness max error 4.4×10⁻¹⁶ (both at machine
  precision).

### Numerical impact (for users depending on B₁/B₂ projections)

At chess starting position with traditional piece values
(P=1, N=3, B=3.5, R=5, Q=9, K=100):

| Channel | Pre-fix energy | Post-fix energy |
|---------|---------------:|----------------:|
| A₁      | 0.000          | 0.000           |
| A₂      | 4140.500       | 4140.500        |
| **B₁**  | **2545.375**   | **0.000**       |
| **B₂**  | **2545.375**   | **4140.500**    |
| E       | (unchanged)    | (unchanged)     |

Pre-fix B₁ and B₂ frequently coincided numerically because the non-
class-constant character rows collapsed both projections onto the same
linear combination.  Any downstream statistic that distinguished B₁
from B₂ (or combined them in a "breaking" sum) was affected.

Reprocessed chess §9h' depth-gap experiment (55 Stockfish d=1 vs d=20
positions, re-run against the corrected table on 2026-04-23) shows:

- B₁ partial ρ: +0.461 (pre) → +0.303 (post)
- B₂ partial ρ: +0.461 (pre) → +0.490 (post) — now outperforms A₁
  partial +0.456 as a complexity predictor
- "breaking signed" partial ρ: +0.101 non-significant (pre) → −0.310
  p=0.022 (post) — a previously-null hypothesis ("breaking channels
  signed sum predicts advantage after material control") is now
  confirmed

Full audit note with numerical delta table in
`docs/chess-maths/chess_spectral_research_notebook.md` §9a, and the
updated §9h′ Tables 1 and 2.

### No other changes

- No encoder output changes on A₁, A₂, or E channels (those character
  rows were already class-consistent).
- Phase-operator subpackage (`chess_spectral.phase_operators`) does
  not use `tables.CHARS` — unaffected.
- spectralz v4 frame format unchanged.
- Public API surface unchanged (only the numerical values returned
  by `project_irrep(sig, 'B1')` and `project_irrep(sig, 'B2')` move,
  and they move to the correct values).

### Changed

- Version bumped 1.2.0 → 1.2.1 (semver patch; behavioural correction
  to a public numerical API).

## [1.2.0] — 2026-04-22

Feature release. Adds the §11 phase-space move generator and check
detector as the `chess_spectral.phase_operators` subpackage. Previously
these modules lived at `docs/chess-maths/phase_operators/` with no PyPI
distribution; users had to import via `sys.path` tricks. They are now
first-class `chess_spectral` API, installable via
`pip install chess-spectral`.

### Added

- `chess_spectral.phase_operators` subpackage exposing the validated
  §11 primitives:
  - Phase arithmetic on Z_640 (`phi`, `P_rook`, `P_bishop`, `P_queen`,
    `P_king`, `P_knight`, `P_pawn_white`, `P_pawn_black`, and the
    generator constants `ROW_GEN`, `COL_GEN`, `DIAG_NE_SW_GEN`,
    `DIAG_NW_SE_GEN`, `MODULUS`, `KNIGHT_SHIFTS`, `KING_SHIFTS`).
  - Inverse lookup (`invert`, `PHI_TO_RC`, `RC_TO_PHI`,
    `phase_set_to_board`).
  - Occupation-aware move generation in three equivalent solutions
    (`occupation_aware_moves_a/b/c`) including en passant via
    `ep_phase_from_board` and castling via `available_castles` /
    `castle_king_destinations` / `CASTLES`.
  - Phase-native check detection (`phasecast_is_check`,
    `move_leaves_king_in_check`) — validated 100% against
    python-chess's `is_check` over 3393 pseudo-legal transitions in
    the §11.5 experiment.
- Top-level re-exports for the high-traffic primitives so
  `from chess_spectral import phasecast_is_check,
  occupation_aware_moves_c, phi, ...` works without the subpackage
  path. Full API remains accessible at
  `chess_spectral.phase_operators.*`.
- 92 unit tests migrated from the research tree into the packaged
  suite at `tests/phase_operators/`, runnable via
  `pytest tests/phase_operators/`. Existing `chess_spectral` tests
  (encoder parity, roundtrip, edge support) unchanged.

### Changed

- Version bumped 1.1.3 → 1.2.0 (feature addition; semver minor).
- No changes to encoder, `spectralz` wire format, frame I/O, CLI,
  safety field, corpus processing, or any existing public API. All
  pre-1.2.0 call sites continue to work unchanged.

### Research artifacts (unaffected)

The following §11/§12 research modules remain at their original
`docs/chess-maths/` paths because they are experiment-scoped, not
library surface:

- `docs/chess-maths/phase_operators/{equivalence_check,
  occupation_equivalence_check, benchmark_solutions, phase_similarity,
  similarity_experiment, partition_detector, partition_experiment}.py`
- `docs/chess-maths/king_attack_encoder/` (§12 Phase A2)

Their imports now reference `chess_spectral.phase_operators` rather
than relying on `sys.path` manipulation. A `pip install` of
`chess-spectral` is now a prerequisite for running them.

## [1.1.3] — 2026-04-20

Pipeline-exercise release. Functionally identical to 1.1.2; exists to
drive the full autotag → dispatch → PyPI-publish chain end-to-end after
the `workflow_dispatch` + explicit `gh workflow run` fix in
`.github/workflows/chess-spectral-{autotag,publish}.yml` landed on main.
`chess-spectral-v1.1.2` never produced a PyPI artifact (autotag ran
before the dispatch fix and the GITHUB_TOKEN anti-recursion guard
silently swallowed the publish trigger); the dangling tag has been
deleted.

### Changed

- Version bumped 1.1.2 → 1.1.3. No encoder, wire-format, or public-API
  changes.

## [1.1.2] — 2026-04-20

Packaging release. First version published to PyPI under the distribution
name `chess-spectral`. No runtime behavior changes; encoder outputs and
spectralz v4 frame bytes are identical to 1.1.1.

### Added

- `CHANGELOG.md` (this file).
- `py.typed` markers in both `chess_spectral/` and `chess_spectral_4d/`
  so downstream mypy users see the in-tree type hints.
- `Typing :: Typed` classifier and `Homepage` / `Issues` / `Changelog`
  entries in `[project.urls]`.
- Repo-level CI: `.github/workflows/chess-spectral-autotag.yml` watches
  the package subtree for version bumps and creates annotated
  `chess-spectral-v{X.Y.Z}` tags + GitHub Releases, and
  `.github/workflows/chess-spectral-publish.yml` builds the sdist +
  wheel and publishes to PyPI via trusted publishing (OIDC) on tag
  push.

### Changed

- Build backend switched from `setuptools` to `hatchling` to match the
  sibling `python-chess4d-oana-chiru` project's convention. Package
  contents (wheel layout, console scripts, runtime imports) are
  unchanged.
- Version bumped from 1.1.1 → 1.1.2. The encoder, wire formats, and
  public API are identical to 1.1.1; the bump exists because the
  `chess-spectral-v1.1.1` git tag is already in place (downstream
  pins to it via `git+` direct reference) and the autotag workflow
  won't re-tag the same version.

## [1.1.1] — 2026-04-19

Initial pip-installable release (via `git+https://` direct reference;
not yet on PyPI). Ships the 2D 640-dim and 4D 45 056-dim spectral
encoders together under a single distribution.

### Added

- `pyproject.toml` at `docs/chess-maths/chess-spectral/python/` — name
  `chess-spectral`, two packages (`chess_spectral`, `chess_spectral_4d`),
  two console scripts (`chess-spectral`, `chess-spectral-4d`), `[corpus]`
  extra for `python-chess`.
- `chess_spectral_4d` facade re-exports (`encode_4d`, `frame_4d`,
  `write_spectralz_v4`, …) so downstream code can import from the
  top-level package without reaching into `chess_spectral.encoder_4d`.
- 4D encoder v1.1.1 pawn-axis split: `FA_PAWN_W` (W-axis) and
  `FA_PAWN_Y` (Y-axis) sub-channels per Oana & Chiru Definition 11;
  `encoding_dim` grew from 40 960 to 45 056 (11 channels × 4096
  eigenmodes).
- spectralz v4 frame format (bumped from v3); readers still accept v3
  for backward compatibility.
- Full C ↔ Python parity gate on all 11 4D channels at TOL=1e-10
  (see `tests/test_c_py_parity_4d.py`).

### Changed

- 4D encoder: channel slot 9 (previously `FA_PAWN`) is now split;
  `FD_DIAG` moved from slot 9 to slot 10.
- `chess_spectral.corpus` dependency now under the `[corpus]` extra
  rather than required at base install.
