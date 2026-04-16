"""build_dashboard_data — generate the GAMES literal for spectral_corpus_dashboard.jsx
from a corpus sweep directory at uniform ply stride.

Reads manifest.json + each game_NNN.spectralz, computes per-frame channel
energies via the same _frame_channel_energies() the sweep already uses,
subsamples at the same stride for every game, and writes
spectral_corpus_dashboard.data.js as `export const GAMES = [...]`.

Usage:
    python build_dashboard_data.py <run_dir> [--ply-step 2] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Make the in-repo chess_spectral package importable regardless of cwd.
_PKG_PARENT = Path(__file__).resolve().parents[1] / "chess-spectral" / "python"
sys.path.insert(0, str(_PKG_PARENT))

from chess_spectral.frame import read_encodings  # noqa: E402
from chess_spectral.corpus import _frame_channel_energies  # noqa: E402


def _game_record(idx: int, n_plies: int, cr: float, energies: dict, step: int) -> dict:
    sel = list(range(0, n_plies, step))
    return {
        "id":    idx,
        "n":     n_plies,
        "cr":    round(float(cr), 2),
        "plies": sel,
        "a1":    [round(float(energies["A1"][i]), 2) for i in sel],
        "e":     [round(float(energies["E"][i]),  2) for i in sel],
        "ft":    [round(float(sum(energies[c][i] for c in
                  ("F1", "F2", "F3"))), 2) for i in sel],
        "fa":    [round(float(energies["FA"][i]), 2) for i in sel],
    }


def build(run_dir: Path, ply_step: int) -> list[dict]:
    manifest = json.loads((run_dir / "manifest.json").read_text())
    games_meta = manifest["games"]
    out = []
    for meta in games_meta:
        idx = meta["index"]
        spz_path = run_dir / "spectralz" / f"game_{idx:03d}.spectralz"
        if not spz_path.exists():
            print(f"  skip G{idx}: missing {spz_path.name}", file=sys.stderr)
            continue
        _hdr, arr = read_encodings(str(spz_path))
        n_plies = int(arr.shape[0])
        if n_plies == 0:
            print(f"  skip G{idx}: zero frames", file=sys.stderr)
            continue
        energies = _frame_channel_energies(arr)
        out.append(_game_record(idx, n_plies, meta.get("chaos_ratio", 0.0),
                                energies, ply_step))
        print(f"  G{idx}: {n_plies} plies → {len(out[-1]['plies'])} samples "
              f"(step={ply_step})", file=sys.stderr)
    return out


_DEFAULT_TEMPLATE = Path(__file__).parent / "spectral_corpus_dashboard.jsx"
_IMPORT_RE = re.compile(
    r'import\s*\{\s*GAMES\s*\}\s*from\s*"[^"]+";'
)


def _emit_jsx(template_path: Path, out_path: Path, data_filename: str) -> None:
    """Copy the canonical dashboard JSX, rewriting the GAMES import to point
    at this sweep's data file (sibling in the same directory)."""
    src = template_path.read_text(encoding="utf-8")
    new_import = f'import {{ GAMES }} from "./{data_filename}";'
    if not _IMPORT_RE.search(src):
        raise RuntimeError(
            f"template {template_path} has no `import {{ GAMES }} from \"...\"` line "
            f"to rewrite — was the canonical JSX restructured?"
        )
    out_path.write_text(_IMPORT_RE.sub(new_import, src), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", type=Path,
                    help="Sweep results directory (contains manifest.json + spectralz/).")
    ap.add_argument("--ply-step", type=int, default=2,
                    help="Uniform sampling stride applied to every game (default: 2).")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output data-file path. Default: "
                         "`results/spectral_corpus_dashboard.data.js` (canonical), "
                         "or `<out-dir>/<name>.data.js` when --out-dir is set.")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="Directory for both data and JSX (per-sweep mode). "
                         "When omitted but --emit-jsx is set, defaults to the sweep dir.")
    ap.add_argument("--name", type=str, default=None,
                    help="Base name for per-sweep outputs (default: sweep dir basename). "
                         "Produces <name>.data.js and (with --emit-jsx) <name>.dashboard.jsx.")
    ap.add_argument("--emit-jsx", action="store_true",
                    help="Also emit a JSX dashboard alongside the data file, "
                         "templated from the canonical results/spectral_corpus_dashboard.jsx.")
    ap.add_argument("--template", type=Path, default=_DEFAULT_TEMPLATE,
                    help=f"JSX template path (default: {_DEFAULT_TEMPLATE.name}).")
    args = ap.parse_args()

    if args.ply_step < 1:
        ap.error("--ply-step must be ≥ 1")
    if not (args.run_dir / "manifest.json").exists():
        ap.error(f"no manifest.json under {args.run_dir}")

    # Resolve output paths.
    name = args.name or args.run_dir.name
    if args.out_dir is None and args.emit_jsx:
        args.out_dir = args.run_dir
    if args.out is None:
        args.out = (args.out_dir / f"{name}.data.js" if args.out_dir
                    else Path(__file__).parent / "spectral_corpus_dashboard.data.js")

    if args.emit_jsx and not args.template.exists():
        ap.error(f"template not found: {args.template}")

    games = build(args.run_dir, args.ply_step)
    if not games:
        print("no games produced; aborting write", file=sys.stderr)
        return 1

    payload = json.dumps(games, separators=(",", ":"))
    header = (
        f"// Auto-generated by build_dashboard_data.py from {args.run_dir.name}\n"
        f"// ply_step={args.ply_step}, n_games={len(games)}. Do not hand-edit.\n"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(header + f"export const GAMES = {payload};\n",
                        encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes, "
          f"{len(games)} games)", file=sys.stderr)

    if args.emit_jsx:
        jsx_path = args.out_dir / f"{name}.dashboard.jsx"
        _emit_jsx(args.template, jsx_path, args.out.name)
        print(f"wrote {jsx_path} ({jsx_path.stat().st_size} bytes, "
              f"templated from {args.template.name})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
