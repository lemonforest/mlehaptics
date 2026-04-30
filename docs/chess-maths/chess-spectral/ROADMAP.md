# chess-spectral roadmap

This file replaces the dangling `when-we-need-to-spicy-seahorse.md` and
`ticklish-dreaming-platypus.md` references that previously appeared in
error messages. Those plan documents were never committed; this is the
real status doc.

## Current release: v1.2.4 (April 2026)

**All advertised CLI commands are real.** No `[stub]` markers remain in
either `spectral` or `spectral_4d` help output.

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

## v1.7 candidates (post-v1.6 ship gate)

These are research-track items deliberately deferred until after the
§16.5 / §2787 per-depth Elo sweep ships in v1.6. Each is independent
and falsifiable.

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

- [docs/FEN4_FORMAT.md](docs/FEN4_FORMAT.md) — FEN4 v1 placement literal
- [docs/NDJSON4_FORMAT.md](docs/NDJSON4_FORMAT.md) — NDJSON4 ply-log schema
- [chess_spectral_research_notebook.md](../chess_spectral_research_notebook.md)
  — Mathematical foundations + analyze heuristics
