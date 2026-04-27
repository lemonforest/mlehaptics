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

## Format references

- [docs/FEN4_FORMAT.md](docs/FEN4_FORMAT.md) — FEN4 v1 placement literal
- [docs/NDJSON4_FORMAT.md](docs/NDJSON4_FORMAT.md) — NDJSON4 ply-log schema
- [chess_spectral_research_notebook.md](../chess_spectral_research_notebook.md)
  — Mathematical foundations + analyze heuristics
