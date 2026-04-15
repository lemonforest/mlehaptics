# Chess-maths corpus sweep results

Automated tool calls write into this directory so the parent `chess-maths/`
stays readable. Each run gets its own subdirectory with a stable layout.

## Layout

    results/
    ├── .gitignore              # excludes bulk artifacts; tracks manifests + CSV + summary
    ├── README.md               # this file
    ├── pilot_<run_id>/         # small-N smoke tests (run_corpus_pilot.py)
    │   ├── manifest.json
    │   ├── pgn/
    │   ├── ndjson/
    │   └── spectralz/
    └── sweep_<run_id>/         # corpus-scale runs (run_corpus_sweep.py)
        ├── manifest.json       # provenance + per-game metadata + features
        ├── corpus_index.csv    # one row per game; sortable in Excel
        ├── corpus_summary.md   # top-N by chaos / NAGs / length, corpus stats
        ├── pgn/
        ├── ndjson/
        └── spectralz/

The manifest, `corpus_index.csv`, and `corpus_summary.md` are committed
to git. The PGN, NDJSON, and `.spectralz` artifacts are regenerable from
the fetcher + seed + bridge + encoder combination recorded in the
manifest — delete them locally whenever space matters.

## Generating a new run

From `docs/chess-maths/`:

```bash
# Smoke test (3-20 games, no feature extraction)
python run_corpus_pilot.py --n 3 --seed 42

# Corpus sweep (50+ games, with per-game features + sortable index)
python run_corpus_sweep.py --n 50 --seed 7
python run_corpus_sweep.py --n 200 --seed 7 --run-id sweep_weekend
```

Default `run_id` patterns:
- `pilot_<source>_<date>_N<n>_seed<seed>`
- `sweep_<source>_<date>_N<n>_seed<seed>`

Pass `--source hf` (only source wired in both drivers today; TWIC /
chessgames.com are available in `pgn_fetcher.py` but not in the
drivers yet).

## Pipeline

1. `pgn_fetcher.py` — pull `N` random games from HuggingFace
   `official-stockfish/fishtest_pgns` (Stockfish-vs-Stockfish engine
   games, 2018–2021, filtered by move count + time control).
2. Driver writes one `.pgn` per game (full PGN text — headers +
   movetext, lossless).
3. `chess-spectral/bridge/pgn_bridge.py` — convert each PGN to v2
   lossless NDJSON (one JSON object per ply with `fen`, `uci`, `san`,
   `move_from`, `move_to`, and when present `nag` / `eval` / `clk` /
   `comment`), plus a per-game `type:"game_header"` record with all
   PGN tag pairs.
4. `chess-spectral/python/spectral_py.py encode` — encode each NDJSON
   to a gzipped `.spectralz` (640-dim vector per ply).
5. (sweep only) `chess_spectral.extract_features` reads back the
   spectralz + NDJSON to compute mean channel energies, chaos ratio
   (L2-fiber / L2-irrep), NAG counts, and ply count — written to
   `corpus_index.csv` and summarised in `corpus_summary.md`.

## corpus_index.csv columns

- Identity: `index`, `run_id`, `result`, `n_moves`, `n_plies`,
  `white`, `black`, `white_elo`, `black_elo`, `event`, `date`,
  `source_tc`
- Features: `chaos_ratio`, `nag_count`, `blunder_count`,
  `mistake_count`, `has_eval`, `has_clk`
- Channel energies (mean across plies): `mean_A1`, `mean_A2`,
  `mean_B1`, `mean_B2`, `mean_E`, `mean_F1`, `mean_F2`, `mean_F3`,
  `mean_FA`, `mean_FD`
- Bytes: `pgn_bytes`, `ndjson_bytes`, `spectralz_bytes`
- `error` — populated if any pipeline stage failed for this game;
  the rest of the row is then blank

Downstream tools (`analyze_safety.py`, `analyze_channel_deltas.py`)
still consume the PGN directly for their own analyses — the
`corpus_index.csv` is the cheap way to pre-sort a corpus before
spending time on heavier per-game work.
