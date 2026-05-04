# chess-spectral roadmap

This file replaces the dangling `when-we-need-to-spicy-seahorse.md` and
`ticklish-dreaming-platypus.md` references that previously appeared in
error messages. Those plan documents were never committed; this is the
real status doc. Per-release detail lives in
[python/CHANGELOG.md](python/CHANGELOG.md); this doc is the strategic
view.

## Current release: v1.12.0 (May 2026)

**B-spike-2 from notebook §20.15** — encoder BIP-hybrid (sign ×
magnitude factoring per dim). Sign packs as 1 bit per dim
(algebraically exact); magnitude quantizes to 4 or 8 bits per dim
with per-channel scaling. New `chess_spectral.encoder_bip_hybrid`
module; `encode_2d_bip_hybrid` / `encode_4d_bip_hybrid` public API.
~3.4× compression at 8-bit, 5.8× at 4-bit. Cosine-sim ≥ 99.99% on
the §20.15 acceptance corpus (median 0.999996 / worst 0.999996 on
2D 7-FEN corpus; 0.999979 on 4D canonical Oana-Chiru). 4D 4-bit
research finding documented in §20.18 (lands at 0.994358 — below
99.5% but above 95%). No breaking changes vs 1.11.x.

## v1.11.0 (May 2026) — B-spike-1b: ALU-native phase-operator engine

Promote the §11 phase-operator engine — already integer-arithmetic
over `Z_640` per §20.13 — to a stable public API with no
`python-chess` dependency on the hot path.
`phase_only_pseudo_legal_moves(pos, side_to_move_white,
ep_file=...)` is the integration entry point. Pure ALU-native
pseudo-legal move generation for Pyodide / WASM consumers; ~190 µs
per startpos call (~2.5× slower than Cython python-chess but
structurally faster than the Solution-B-per-piece-loop). 26
immolation tests including parity vs `board.pseudo_legal_moves`
on an 8-FEN corpus. Notebook §20.17 documents the `Z_640` wire
contract as public API.

## v1.10.0 (May 2026) — B-spike-1a: BIP-encoded sheet block

Integer-native form of the 1.9.0 non-Markovian sheet block.
`SheetStateBIP` dataclass packs the 11-dim float64 aux block (88
bytes per position) into 3 bytes (uint16 categorical + uint8
halfmove). 29× compression with bit-exact round trip on the legal
state space (87,264 cases verified exhaustively). Operator fast
paths (`castling_alive`, `kingside_castling_alive`,
`fifty_move_rule_triggered`, `threefold_claimable`) via single
integer ops. Hamming-distance similarity metric for corpus
similarity. Per §19.10's depth-1 floor still holds for single-
position queries; BIP wins are at scale (Pyodide / batch / wire
format).

## v1.9.1 (May 2026) — README polish + v5 sheet design decision

Polish on top of v1.9.0. README PyPI examples updated to use the
future-proof `encode_2d` alias; Roadmap link added to PyPI project
URLs; v5 wire format officially documented as **not** carrying sheet
aux blocks (sheets ride alongside in-memory vectors and live in
PGN / NDJSON / FEN sidecars on disk; see `frame_v5.py` header note +
notebook §19.12 for rationale).

## v1.9.0 (May 2026) — sheets aux block + legal-moves CLI

Representation-completeness ship for the four non-Markovian chess
facts (castling rights, EP target, side-to-move, halfmove clock,
repetition count). 11-dim aux block opt-in via
`encode_2d(pos, sheets=...)` and `encode_4d(pos4, sheets=...)`.
Pyodide-bridge surface for chess4D-OC consumers. New `legal-moves`
CLI for both 2D and 4D. Notebook §19.10 captures the empirical
finding that closes the speed thesis (depth-1 bitboard floor); 1.9.0
ships representation-only, no speed claim. See
[python/CHANGELOG.md](python/CHANGELOG.md) for detail.

## v1.8.x (April-May 2026) — 4D ship-line

v1.8.0 — chess4D-OC visualizer M11.40 unblocker (`GameState4D`
push/pop/board surface; `is_check` / `is_checkmate` / `is_stalemate`;
search() accepts `GameState4D`).
v1.8.1 — canonical Oana-Chiru §3.3 starting position
(`STARTING_FEN4`, `initial_position()`, slice helpers; SHA-256
hash-locked test gate).

## v1.7.x (April 2026) — surface polish

v1.7.0 — D2 native-bitboard fast-path availability flag
(`HAS_NATIVE_BITBOARD`); v5 wire format mode-2 XOR-stream as the
default (~7× compression).
v1.7.1 — FEN4 parser tolerance for an optional slash between pawn
color and axis; PyPI long-description hotfix; immolation README
gate enforcing "What's new in v{X.Y}" section per release.

## v1.6.0 (April 2026) — original §16 ship-gate

The §16 ship-gate release. Search core + tournament harness + sweep
runner ship as CLI commands; v5 unified wire format (three encoding
modes — dense, per-channel, XOR-stream) ships at the Python read/write
layer; in-house 4D bitboard move generator + graph-Laplacian legality
oracle ship as runtime infrastructure for the §16.2 search.

**All v1.2.4 CLI commands remain real.** No `[stub]` markers remain in
either `spectral` or `spectral_4d` help output. v1.6 adds `search`,
`tournament`, and `sweep` to both 2D and 4D Python CLIs (per-side
symmetric agent specs let white and black be configured independently
in the same single-process loop).

### 2D commands (`spectral`)
| Command | Status | Notes |
|---------|--------|-------|
| `encode` | ✅ wired | NDJSON / PGN / URL → .spectral[z] |
| `encode-fen` | ✅ wired | Single FEN → 1-frame .spectral |
| `csv` | ✅ wired | .spectral[z] → per-ply 10-channel CSV |
| `compare` | ✅ wired (v1.2.4) | Cosine-similarity report |
| `query` | ✅ wired (v1.2.4) | Channel-energy breakdown at ply N |
| `heatmap` | ✅ wired (v1.2.4) | ANSI 8×8 of one channel at one ply |
| `analyze` | ✅ wired (v1.2.4) | A1 peak/drop/crisis JSON summary |
| `export` | ✅ wired (v1.2.4) | .spectral → JSON for the web viewer |
| `play` | ✅ wired (v1.2.4) | Non-interactive ply-by-ply listing |

### 4D commands (`spectral_4d`)
| Command | Status | Notes |
|---------|--------|-------|
| `encode-fixture` | ✅ wired | Parity-test entry point (raw float32 to stdout) |
| `encode-fen4` | ✅ wired (v1.2.4) | FEN4 v1 literal → 1-frame .spectralz4 |
| `encode` | ✅ wired (v1.2.4) | NDJSON4 ply-log → .spectralz4 bulk |
| `csv` | ✅ wired (v1.2.4) | .spectralz4 → per-ply 11-channel CSV |
| `version` / `help` | ✅ wired | — |

### 4D Python CLI (`chess-spectral-4d`)
| Command | Status | Notes |
|---------|--------|-------|
| `tables-verify` | ✅ wired | Phase-N validation gates |
| `encode-fen4` | ✅ wired (v1.2.4) | byte-identical to C |
| `encode-moves4` | ✅ wired (v1.2.4) | byte-identical to C |
| `corpus-gen` | ✅ wired (v1.2.4) | Wrap N NDJSON4 → corpus folder |
| `search` | ✅ wired (v1.6.0) | Per-side agent spec; --fen4 required |
| `tournament` | ✅ wired (v1.6.0) | 4D round-robin; --start-fen4 required |

### v1.6.0 engine + ship-gate CLI (`spectral_py`)
| Command | Status | Notes |
|---------|--------|-------|
| `search` | ✅ wired (v1.6.0) | Single-position iterative-deepening alpha-beta search |
| `tournament` | ✅ wired (v1.6.0) | Round-robin between any agents (per-side symmetric spec) |
| `sweep` | ✅ wired (v1.6.0) | §16.5 / §2787 ship-gate matrix runner |

---

## Open work (post-v1.2.4)

These items are tracked in [AUDIT_2026-04.md](AUDIT_2026-04.md) but
were intentionally left out of v1.2.4's scope:

- **F-01 to F-21**: Performance and idiomatic improvements (LTO, einsum
  vectorisation, restrict qualifiers, etc.). All are independent and
  parity-preserving; ship one at a time.
- **safety_field `include_pawns=True`**: Currently raises
  NotImplementedError (loud failure). Implementation is gated on
  factoring `PAWN_SYM_FIBER` out of the encoder.
- **B1/B2 stale-test refresh**: Done in v1.2.4. Future channel-value
  changes should regenerate the expected dict in
  `python/tests/test_parity.py` from the C output (it is the authority
  per AUDIT §1).

## Future work (v1.10+ candidates and parked spikes)

Items in this section are research-track or design-track work that
hasn't shipped yet. None of these are commitments — each is
independent and may be deferred or closed based on empirical
findings.

### Sheet-block follow-ons (notebook §19)

- **S-spike-1 — sheet aux block.** ✅ Shipped in v1.9.0. 11-dim
  float64 aux block carrying castling rights, EP target,
  side-to-move, halfmove clock, repetition count.
- **S-spike-2 — wire format integration for sheets.** Currently
  deferred. Sheets are an in-memory representation feature; on
  disk, non-Markov state lives in PGN / NDJSON / FEN sidecars
  (the existing corpus-gen layout already preserves the source
  game record). Wire-format integration becomes worthwhile when
  a downstream consumer needs to persist encoder vectors WITH
  sheet aux blocks — most likely the v5.1 mode-2 XOR-stream
  extension when chess4D-OC adopts persisted-vector retrieval.
  Header has 223 reserved bytes for the necessary fields; no
  struct change required.
- **S-spike-3 — sheet-aware search-engine evaluator.** Closed as
  not-recommended. Sheet channels are categorical (rights alive
  or dead); search evaluator weights are continuous. A separate
  `eval=spectral+sheets` evaluator family is the right shape if
  sheet-aware scoring is wanted; weighted-channel hooks into the
  existing `eval=spectral` path would lose information.

### BSHDC / bit-serialization (notebook §20)

The §20.15 three-tier B-spike phasing's status as of v1.12.0:

- **B-spike-1a — sheet-block BIP encoding.** ✅ Shipped in v1.10.0.
  Integer-native form (uint16 + uint8 = 3 bytes) for the 1.9.0
  88-byte float64 sheet block. 29× compression with bit-exact
  round trip on the legal state space (87,264 cases). See
  notebook §20.14 / §20.16 for design + implementation plan.
- **B-spike-1b — ALU-native phase-operator engine.** ✅ Shipped
  in v1.11.0. `phase_only_pseudo_legal_moves(pos,
  side_to_move_white, ep_file=...)` integration entry point with
  no python-chess dependency on the hot path. Z_640 wire contract
  documented in notebook §20.13 / §20.17. Parity vs
  `board.pseudo_legal_moves` on an 8-FEN corpus locks the
  acceptance gate.
- **B-spike-2 — encoder BIP-hybrid.** ✅ Shipped in v1.12.0. Sign
  × magnitude factoring per dim. 3.4× / 5.8× compression at
  8-bit / 4-bit. §20.15 acceptance gate met at 8-bit; 4D 4-bit
  research finding documented in §20.18 (lands at 0.994 — below
  99.5% but above 95%).
- **B-spike-3 — search-engine evaluator hot path with hybrid
  vectors.** Parked. Tournament: float32 spectral vs hybrid
  spectral at equal search depth. Acceptance: tournament ELO
  within noise + ≥ 10× wall-clock speedup on the evaluator hot
  path. Picks up when a §16-aware consumer wants the runtime
  speedup empirically validated.
- **B-spike-4 — pure-phase encoder rewrite.** Parked. ~3000-5000
  LOC rewrite eliminating float32 from the encoder path entirely.
  High risk; gated behind clear empirical motivation (which
  B-spike-2's success at preserving cosine-sim already partially
  provides — but a full rewrite still wants stronger justification).

### Per-channel optimization opportunities (notebook §20.12, deferred to 1.13.0+)

The 1.12.0 BIP-hybrid uses uniform sign × magnitude treatment per
dim. Three channels could benefit from non-uniform encoding:

- **A1 (D₄ trivial irrep, pure magnitude).** Sign is always
  zero / non-negative; the sign bit is uninformative. Skipping
  saves ~64 bits (2D) / 4096 bits (4D).
- **FA channels (antisymmetric pawn fiber, pure sign).**
  Magnitude is uniform within sign; the magnitude byte is
  uninformative. Skipping saves ~64 bytes (2D) / per-channel
  bytes for FA_PAWN_W and FA_PAWN_Y in 4D.
- **E channel (D₄ 2-D irrep, genuinely complex).** Could benefit
  from a complex-int packing rather than sign × magnitude.

Estimated savings if all three optimizations applied: ~10-15%
additional compression. 1.13.0+ work if the per-dim uniformity
of 1.12.0's sign × magnitude proves to be the dominant cost.

### API stability (notebook §19.11)

- **Adopt `encode_2d`** in all new consumer code; query
  `chess_spectral.ENCODING_DIM` (or `enc.shape[0]`) and iterate
  channels via `chess_spectral.CHANNELS` rather than hardcoding
  640. The dim count is not a stable contract — sheets bumped
  640 → 651 already, and channel embiggening (Tier 2.1/2.2,
  ψ-driven density / partial-trace channels) or BSHDC enrichment
  may move it again. `encode_640` remains a permanent alias.

### QM extension Tier 2 (deferred — η-metric machinery)

- **Tier 2.1 — `get_qm_density_from_psi` /
  `get_probability_current_from_psi`.** Needs ADR-005's pawn
  pseudo-Hermitian η-metric to be implementation-complete.
  Probe 3's PARTIAL PASS finding (notebook §18.1) has a known
  decomposition path (M_pawn = M_single + M_double; η-metric
  on single-push only) that hasn't landed yet.
- **Tier 2.2 — partial-trace density matrix per piece type.**
  Same gating.

### v1.7-era candidates (mostly shipped, one parked)

These are research-track items deliberately deferred until after the
§16.5 / §2787 per-depth Elo sweep shipped in v1.6. Most landed in
v1.7-1.9; the E-irrep directional decomposition is still open.

### E-irrep directional decomposition

**Hypothesis.** The encoder currently exposes the D₄ E irrep as one
64-dim vector per square — a magnitude-only summary that collapses
the 2D internal structure. The empirical §9h′ analysis found that
E correlates with positional weakness (signed-sum partial ρ = −0.293,
p < 0.05 vs Stockfish eval after material control), but "weakness"
on a chessboard has a direction. The 4D E plane (orthogonal-orbit E
2-dim ⊕ diagonal-orbit E 2-dim) factors into four directional
sub-channels:

  * `e₁ = (N − S) / √2`     — vertical asymmetry (one wing heavier)
  * `e₂ = (E − W) / √2`     — horizontal asymmetry (kingside vs queenside)
  * `e₃ = (NE − SW) / √2`   — main-diagonal asymmetry (a1-h8 cluster)
  * `e₄ = (SE − NW) / √2`   — anti-diagonal asymmetry (a8-h1 cluster)

The bulk E channel is the L2 norm of these four sub-coefficients per
square (lossy w.r.t. directional information).

**Falsifiable prediction.** Re-run the §9h′ partial-correlation
analysis on the four sub-coefficients separately. If they all carry
the same correlation, bulk E was the right resolution and the
directional info is decorative. If at least one beats −0.293 and
at least one is near zero, the directional decomposition carries
real signal that the bulk magnitude obscures.

**Phasing.**

1. **v1.7-A (research script, no encoder change).** Add
   `research/e_irrep_directional_analysis.py` that re-projects the
   pre-channel ray data (the encoder's 8-ray intermediate, before
   channel projection) onto e₁..e₄, computes per-square
   sub-coefficients on the §9h′ corpus, and reports four partial
   correlations vs Stockfish eval. **No encoder version bump; no
   wire format impact.** This is a pure analysis pass.

2. **Decision point.** Inspect the four ρ values. If signal: proceed
   to v1.7-B. If no signal: file the result as a "bulk E was right"
   finding and close.

3. **v1.7-B (encoder version bump).** Replace the bulk E channel
   with four directional sub-channels, taking the encoder from 10
   channels (640 dims) to 13 channels (832 dims), 2D only initially.
   Bumps `encoding_dim` in v5 wire format header (no struct change —
   the dim is already a header field). The §16.1 evaluator family
   needs re-validation against the new channel layout.

4. **v1.7-C (4D analogue).** Same decomposition for the 4D encoder's
   D₄ × Z₂-axis structure if the 2D experiment shows signal. Defer
   until 2D is proven.

**Why v1.7, not v1.6.** Encoder dimension is a breaking change to
everything downstream of the 640-dim contract — including the §16.1
evaluator trifecta (material/spectral/qm) just merged in PR-1..PR-4
and the per-depth Elo sweep that's the v1.6 ship gate. We finish v1.6
first, then start v1.7 with a clean ship-gate baseline to A/B against.

### LTO/IPO segfault in `spectral encode --pgn -z` on Linux release

Tracked in [python/CHANGELOG.md](python/CHANGELOG.md). Currently
xfailed on `sys.platform.startswith("linux")` with strict=False so
CI stays green; macOS / Windows / cibuildwheel matrix all enforce.
Investigation hooks: `_run_c` retry helper now surfaces stdout/stderr
in the CalledProcessError on permanent failure, so the next CI run
on a green-elsewhere PR will give us a debug breadcrumb.

To investigate: build on Linux with `-fno-strict-aliasing`, gdb the
segfault location, then either fix the underlying UB or drop IPO from
the release preset.

---

## Format references

- [docs/WIRE_FORMAT.md](docs/WIRE_FORMAT.md) — `.spectral[z]` / `.spectralz4` binary container (v2 / v3 / v4 / v5; reader dispatch)
- [docs/FEN4_FORMAT.md](docs/FEN4_FORMAT.md) — FEN4 v1 placement literal
- [docs/NDJSON4_FORMAT.md](docs/NDJSON4_FORMAT.md) — NDJSON4 ply-log schema
- [docs/adr/wire_format/ADR-001-v5-unified-encoding-modes.md](docs/adr/wire_format/ADR-001-v5-unified-encoding-modes.md)
  — design rationale + phasing for the v5 unified format
- [chess_spectral_research_notebook.md](../chess_spectral_research_notebook.md)
  — Mathematical foundations + analyze heuristics
