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

## Research / illustrative threads

Capturing ideas that aren't on the v1.6 critical path but are
worth landing eventually for cross-disciplinary illustration value
or as independent validators of existing surfaces.

### Graph-Laplacian eigenbasis move-legality oracle

A third independent move-legality oracle alongside `python-chess`
(2D) / `python-chess4d-oana-chiru` (4D) and our own
`chess_spectral.phase_operators` (modular-arithmetic predicates).
The piece-movement adjacency matrices `A_p` already live in
`tables.py` (2D) and `tables_4d.py` (4D); their graph Laplacians
`L_p = D_p - A_p` admit eigendecomposition, and the spectrum acts
as a structural lookup oracle:

- `A_p[i, j] = Σ_k λ_k · v_k[i] · v_k[j]` -- if this sum is 1 the
  move (i, j) is geometrically reachable; if 0 it is not. The
  eigenvalue-grouping structure exposes symmetry classes of moves
  the modular-arithmetic operators don't surface explicitly.
- For 4D, the 4096×4096 Laplacian factors as a Kronecker sum of
  four 8×8 path-graph Laplacians, so the eigenbasis is the same
  DCT-II tower the encoder already uses (no new caching).
- Validates **on an empty-board reach predicate**, not full
  occupation-aware legality. Pair with existing occupation /
  capture / castling / en-passant logic for a complete oracle.
- **Demonstrates yet another way the spectral toolkit applies** --
  the same eigenbasis used for encoding can be used for
  legality-checking, giving the project a parallel structure
  between "spectral encoding" and "spectral legality."

May also serve as the in-house 4D move-generation backend (vs the
`python-chess4d-oana-chiru` runtime-dep alternative; that path is
explicitly closed because of a circular dependency that's why it's
in the `[test]` extras only). Ships as part of the v1.6 engine arc
as a research / production module; cross-validation gate in
`tests/test_spectral_legality.py`.

### Possible future absorption of python-chess4d-oana-chiru

Open question (not committed): whether to absorb the entire 4D rule
library (Oana & Chiru 2026) into chess-spectral as the canonical 4D
chess implementation, vs keep it as an upstream dependency. The
graph-Laplacian oracle is the first in-house piece of 4D rule logic;
if absorption happens later, the oracle is part of the absorbed set.
Trade-offs: scope creep vs single-source-of-truth + no circular-dep
management. Decision deferred -- this note captures the framing for
when the decision is made.

## Format references

- [docs/FEN4_FORMAT.md](docs/FEN4_FORMAT.md) — FEN4 v1 placement literal
- [docs/NDJSON4_FORMAT.md](docs/NDJSON4_FORMAT.md) — NDJSON4 ply-log schema
- [chess_spectral_research_notebook.md](../chess_spectral_research_notebook.md)
  — Mathematical foundations + analyze heuristics
