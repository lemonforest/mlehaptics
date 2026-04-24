"""Per-ply feature extraction from .spectralz files.

Takes a .spectralz binary (produced by ``cli encode-pgn`` or by
direct ``frame.write_file`` calls) and emits a flat CSV with one row
per frame containing:

    - ply            : u32 from the frame tail
    - norm_total     : ||enc||^2 (all 768 dims)
    - E_<channel>    : per-channel squared-norm for each of the 12
                        channels (column order = encoder layout)

Optionally, the caller can also request per-cell dims (768 columns
named d000..d767) with --raw.  For corpus-level analysis the
channel-energy CSV is usually what you want.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

from .encoder import channel_energies
from .frame import read_file
from .tables import CHANNEL_NAMES, ENCODING_DIM


def extract_features(
    spectralz_path: Path, out_csv: Path, include_raw_dims: bool = False,
) -> int:
    hdr, frames = read_file(spectralz_path)
    print(
        f"spectralz: {spectralz_path.name}  version={hdr.format_version} "
        f"encoding_dim={hdr.encoding_dim} n_frames={hdr.n_frames}"
    )
    print(f"metadata: {hdr.metadata}")
    if hdr.encoding_dim != ENCODING_DIM:
        raise RuntimeError(
            f"encoder dim mismatch: file={hdr.encoding_dim}, "
            f"runtime={ENCODING_DIM}"
        )
    fieldnames = ["ply", "norm_total"]
    fieldnames += [f"E_{name}" for name in CHANNEL_NAMES]
    if include_raw_dims:
        fieldnames += [f"d{i:03d}" for i in range(ENCODING_DIM)]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fr in frames:
            # frame data is float32 from disk; cast to float64 for
            # computation stability (matches encoder.encode_768 dtype).
            enc = np.asarray(fr.data, dtype=np.float64)
            row = {
                "ply": fr.ply,
                "norm_total": float(np.dot(enc, enc)),
            }
            energies = channel_energies(enc)
            for name in CHANNEL_NAMES:
                row[f"E_{name}"] = energies[name]
            if include_raw_dims:
                for i in range(ENCODING_DIM):
                    row[f"d{i:03d}"] = float(enc[i])
            writer.writerow(row)
    print(f"wrote {out_csv}  ({len(frames)} rows)")
    return 0


def _build_parser():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Standard extraction: ply + norm + 12 channel energies.
  python -m othello_spectral.features \\
      ../results/barcelona.spectralz \\
      --out ../results/barcelona_features.csv

  # Full raw-dim dump (768 extra columns, much larger file).
  python -m othello_spectral.features \\
      ../results/barcelona.spectralz \\
      --out ../results/barcelona_raw.csv \\
      --raw-dims
""",
    )
    p.add_argument(
        "spectralz", type=Path,
        help="Input .spectralz file path.",
    )
    p.add_argument(
        "--out", type=Path, required=True,
        help="Output CSV path.",
    )
    p.add_argument(
        "--raw-dims", action="store_true",
        help="Also emit d000..d767 per-cell columns (large output).",
    )
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    return extract_features(args.spectralz, args.out, args.raw_dims)


if __name__ == "__main__":
    sys.exit(main())
