# Chess Spectral Encoders — Map and Reproduction Recipe

> **TL;DR for newcomers:** the production encoder is `chess_spectral.encode_640`
> in [chess-spectral/python/chess_spectral/encoder.py](chess-spectral/python/chess_spectral/encoder.py).
> Everything else in this directory at the top level (`encoder_v3.py`,
> `encoder_512.py`) is historical R&D. Skip to **Reproduction recipe** below
> if you want to regenerate the corpus.

## Try it in your browser

A live visualiser consumes the 640-dim `.spectralz` corpus archives directly,
no install required: <https://lemonforest.github.io/chess-maths-viewer>.
Drop a `sweep_*.7z` from `results/` (or use the bundled sample) to get a
synchronised chessboard + spectral heatmap + per-channel energy charts for
all 10 channels × 64 eigenmodes. Source:
<https://github.com/lemonforest/chess-maths-viewer>.

## Encoder versions

| Stage | File | Output dim | Status | What it is |
|---|---|---:|---|---|
| Global fiber (failed) | (no file) | n/a | **failed** | Position-independent fiber-per-piece-type. Knight on e5 == knight on a1. Documented in notebook §8. |
| Grok local fiber | (no standalone file; subsumed into v3) | 64 | research | Per-square local fiber, fixed the global-fiber problem (PST r=0.971) but is purely additive (no many-body). |
| Gemini quadratic | (no standalone file; subsumed into v3) | 64 | research | Quadratic form weighting captures many-body but has 983× dynamic range. |
| **v3 dual-channel** | [archive/encoder_v3.py](archive/encoder_v3.py) | **70** | **archived** | 64 GFT + 3 geometric fiber + 3 interaction fiber. Demonstration of the geometric/interaction split. Self-contained pedagogical script. |
| **512-dim HDC** | [archive/encoder_512.py](archive/encoder_512.py) | **512** | **archived** | 8 channels × 64. First full HDC encoder: 5 D4 irreps + 3 symmetric fiber. Self-contained pedagogical script. |
| **640-dim production** | [chess-spectral/python/chess_spectral/encoder.py](chess-spectral/python/chess_spectral/encoder.py) (`encode_640`) | **640** | **production** | 10 channels × 64. Adds antisymmetric pawn fiber (FA, dims 512-575) and diagonal deviation (FD, dims 576-639). The first 512 dims are byte-for-byte identical to encoder_512 (same math, same tables). This is what produces every `.spectralz` file in `results/`. |

The 70-dim and 512-dim versions are NOT subsets of the 640-dim production
encoder in code — they re-derive the eigenbasis and tables independently. They
ARE subsets in *math*: encode_640's first 512 dims reproduce the encoder_512
output exactly, and the geometric/interaction split from encoder_v3 lives in
the F1/F2/F3 fiber channels of both.

The encoder lineage in narrative form is documented in
[research notebook §8](chess_spectral_research_notebook.md), and the
production 640-dim channel layout is in
[research notebook §9a](chess_spectral_research_notebook.md).

## 640-dim channel layout (production)

| Dims | Channel | Type | Notebook section |
|---:|---|---|---|
| 0-63 | A₁ | D4 irrep, fully invariant | §9a, §9g |
| 64-127 | A₂ | D4 irrep | §9a |
| 128-191 | B₁ | D4 irrep | §9a |
| 192-255 | B₂ | D4 irrep | §9a |
| 256-319 | E | D4 irrep, 2-dim oriented asymmetry | §9a, §9h′ |
| 320-383 | F1 (sym fiber σ₁) | Symmetric off-diagonal, 72.6% variance | §9a |
| 384-447 | F2 (sym fiber σ₂) | Symmetric off-diagonal, 16.9% variance | §9a |
| 448-511 | F3 (sym fiber σ₃) | Symmetric off-diagonal, 10.5% variance | §9a |
| 512-575 | FA | Antisymmetric pawn fiber (Z₂-breaking) | §9a, §9m, §9p |
| 576-639 | FD | Diagonal deviation (rook's shadow) | §9a, §7b |

Channel constants live in
[chess-spectral/python/chess_spectral/corpus.py:33-35](chess-spectral/python/chess_spectral/corpus.py#L33).
Note: the dashboard's "Fiber Topology" view sums F1+F2+F3, while the corpus
`chaos_ratio` metric sums FA+FD only — see notebook §9q for the naming
discrepancy.

## Reproduction recipe (PGN → dashboard)

End-to-end, three commands:

```bash
# 1. Fetch PGNs + encode .spectralz + extract per-game features.
#    Produces results/sweep_<run-id>/{pgn,ndjson,spectralz,
#                                     corpus_index.csv,manifest.json}.
python docs/chess-maths/run_corpus_sweep.py \
    --source lichess --username DrNykterstein --n 10 \
    --run-id lichess_drnykterstein_$(date +%Y-%m-%d)_N10

# 2. Subsample at uniform ply stride and emit GAMES literal + dashboard JSX.
#    Produces results/sweep_*/<name>.data.js and <name>.dashboard.jsx.
python docs/chess-maths/results/build_dashboard_data.py \
    docs/chess-maths/results/sweep_lichess_drnykterstein_2026-04-15_N10 \
    --ply-step 2 --emit-jsx \
    --name sweep_lichess_drnykterstein_2026-04-15_N10

# 3. (Optional) Audit chaos-ratio length confound across all sweeps.
python docs/chess-maths/analyze_chaos_length.py docs/chess-maths/results/ \
    --out docs/chess-maths/results/chaos_length_$(date +%Y-%m-%d).md
```

For one-off encoding without the sweep harness:

```bash
# Encode a single FEN to a .spectral file.
python docs/chess-maths/chess-spectral/python/spectral_py.py \
    encode-fen --fen "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" \
    -o startpos.spectral

# Encode an NDJSON game (from pgn_bridge.py output).
python docs/chess-maths/chess-spectral/python/spectral_py.py \
    encode -i game.ndjson -o game.spectralz -z

# Read a .spectralz and emit a chat-friendly CSV.
python docs/chess-maths/chess-spectral/python/spectral_py.py \
    csv game.spectralz -o game.csv
```

Run any script with `--help` to see current flags — flag names and defaults
are the source of truth.

## Why three encoders exist in the tree

The research notebook (§8) walks through the encoder evolution as a sequence
of failed-then-fixed experiments, each contributing one piece of the final
production encoder. The standalone scripts (`encoder_v3.py`, `encoder_512.py`)
are *executable* versions of those notebook sections — they run their own
test batteries and print results, which is useful when reading the notebook
alongside the code. They are NOT used by anything in the corpus pipeline.

If you only care about reproducing or extending the published findings, you
only need the `chess_spectral` package. If you want to understand *why* the
production encoder has the structure it does, run the older scripts in order
(v3 → 512) while reading notebook §8 → §9a.
