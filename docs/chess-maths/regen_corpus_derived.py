"""regen_corpus_derived — refresh manifest.json / corpus_index.csv /
corpus_summary.md from current .spectralz + .ndjson files, without
re-encoding or re-fetching.

Use when the encoder package tables/character rows change but .spectralz
files on disk were already regenerated with the fix (the encoder step
is skipped — only `extract_features()` is re-run and the manifest's
`games[*]` entries are patched in place). The original `fetch_params`,
`tool_versions`, and non-spectral per-game fields (PGN headers, byte
sizes, Elo, source_date, ...) are preserved.

Usage:
    python regen_corpus_derived.py <run_dir> [<run_dir> ...]

Run `python regen_corpus_derived.py --help` for the full CLI.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time as _time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PKG = _HERE / "chess-spectral" / "python"
sys.path.insert(0, str(_PKG))

from chess_spectral.corpus import (  # noqa: E402
    extract_features,
    write_index_csv,
    write_summary_md,
)

# Spectral fields that extract_features() produces. These are the only
# per-game fields we overwrite; everything else in the manifest is
# preserved verbatim.
_SPECTRAL_FIELDS = {
    "n_plies",
    "mean_A1", "mean_A2", "mean_B1", "mean_B2", "mean_E",
    "mean_F1", "mean_F2", "mean_F3", "mean_FA", "mean_FD",
    "chaos_ratio",
    "nag_count", "blunder_count", "mistake_count",
    "has_eval", "has_clk",
}


def regen_run(run_dir: Path) -> int:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.is_file():
        print(f"skip: no manifest.json under {run_dir}", file=sys.stderr)
        return 1

    # Orphan corpora (metadata only, no raw data to re-encode from) must
    # be skipped entirely — otherwise we'd stamp every game with a
    # "missing file" error and overwrite the original summary.
    if not (run_dir / "spectralz").is_dir() or not (run_dir / "ndjson").is_dir():
        print(f"skip: no spectralz/ or ndjson/ subdir under {run_dir} "
              f"(orphan metadata corpus, nothing to regen)", file=sys.stderr)
        return 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    games = manifest.get("games", [])
    if not games:
        print(f"skip: manifest has no games: {manifest_path}",
              file=sys.stderr)
        return 1

    print(f"regen: {run_dir}  (N={len(games)})", file=sys.stderr)
    t0 = _time.time()

    n_ok = 0
    n_err = 0
    for entry in games:
        spz_rel = entry.get("spectralz")
        nd_rel = entry.get("ndjson")
        if not spz_rel or not nd_rel:
            entry["error"] = "missing spectralz/ndjson path in manifest"
            n_err += 1
            continue
        spz = run_dir / spz_rel
        nd = run_dir / nd_rel
        if not spz.is_file() or not nd.is_file():
            entry["error"] = f"missing file: {spz if not spz.is_file() else nd}"
            n_err += 1
            continue
        try:
            feats = extract_features(spz, nd)
        except Exception as e:  # noqa: BLE001
            entry["error"] = f"extract_features: {e}"
            n_err += 1
            continue
        # Overwrite only the spectral-derived fields.
        for k in _SPECTRAL_FIELDS:
            if k in feats:
                entry[k] = feats[k]
        # Clear any prior error marker if we succeeded this round.
        entry.pop("error", None)
        n_ok += 1

    elapsed = _time.time() - t0

    # Update aggregates block to reflect this regen pass. Preserve the
    # pre-existing n_requested/n_fetched counts from the original fetch
    # (those describe the fetch step, not this one); only refresh
    # n_encoded/n_errors/wall_time_s, which are now this pass's numbers.
    agg = manifest.setdefault("aggregates", {})
    agg["n_encoded"] = n_ok
    agg["n_errors"] = n_err
    agg["wall_time_s"] = round(elapsed, 2)

    # Leave a trail so the manifest records this regen step without
    # stomping the original generation timestamp.
    manifest["regenerated_utc"] = _dt.datetime.now(
        _dt.timezone.utc
    ).isoformat()
    manifest.setdefault("regen_history", []).append({
        "when_utc": manifest["regenerated_utc"],
        "script": "regen_corpus_derived.py",
        "note": ("refresh extract_features() after chess_spectral/tables.py "
                 "CHARS fix; spectralz/ndjson unchanged"),
        "n_ok": n_ok,
        "n_errors": n_err,
    })

    manifest_path.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"  manifest.json  updated  (ok={n_ok} err={n_err})",
          file=sys.stderr)

    run_id = manifest.get("run_id", run_dir.name)
    write_index_csv(games, run_dir / "corpus_index.csv", run_id)
    print(f"  corpus_index.csv  updated", file=sys.stderr)

    n_requested = agg.get("n_requested", len(games))
    n_fetched = agg.get("n_fetched", len(games))
    write_summary_md(
        games, run_dir / "corpus_summary.md",
        run_id, elapsed,
        n_requested=n_requested, n_fetched=n_fetched,
        n_encoded=n_ok, n_errors=n_err,
    )
    print(f"  corpus_summary.md updated", file=sys.stderr)
    return 0 if n_err == 0 else 3


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("run_dirs", type=Path, nargs="+",
                    help="One or more corpus run directories (each with "
                         "manifest.json + spectralz/ + ndjson/).")
    args = ap.parse_args()

    worst = 0
    for d in args.run_dirs:
        rc = regen_run(d)
        worst = max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main())
