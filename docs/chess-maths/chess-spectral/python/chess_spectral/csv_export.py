"""
CSV export — mirrors the `spectral csv` command in the C CLI.

Columns:
    ply, move_from, move_to,
    dist_prev, cos_prev, dA1,
    E_A1, E_A2, E_B1, E_B2, E_E, E_F1, E_F2, E_F3, E_FA, E_FD,
    E_total

Number formatting is chat-friendly (terse, LLM-paste-friendly) and
matches the C side's fmt_csv_num/fmt_csv_cos in src/main.c so the two
implementations produce byte-identical output for the same .spectral
file. If you tweak rules here, tweak them there.
"""
from __future__ import annotations

import json
import math
import sys
from typing import Iterable, TextIO

import numpy as np

from .encoder import CHANNELS, BOARD_DIM, ENCODING_DIM
from .frame import Frame, Header, open_read_transparent, read_header, read_frame

_HEADER_ROW = (
    "ply,move_from,move_to,"
    "dist_prev,cos_prev,dA1,"
    "E_A1,E_A2,E_B1,E_B2,E_E,E_F1,E_F2,E_F3,E_FA,E_FD,"
    "E_total"
)

# Extra columns appended when --meta is given. Ordering matches the
# pgn_bridge.py record field names.
_META_COLUMNS = ("eval", "clk", "nag")
_META_HEADER_SUFFIX = "," + ",".join(_META_COLUMNS)


def fmt_num(x: float) -> str:
    """Chat-friendly number formatter. Matches C's fmt_csv_num:

        |x| < 1e-6    → "0"
        |x| >= 100    → integer
        |x| >= 1      → two decimals
        |x| >= 0.01   → three decimals
        else          → compact exponential (%.2e)
    """
    ax = abs(x)
    if ax < 1e-6:
        return "0"
    if ax >= 100.0:
        # C's %.0f rounds half-to-even on most platforms; Python's round()
        # does the same. But printf half-to-even and str(round()) can
        # disagree on exact .5 edges. We use f"{x:.0f}" which calls the
        # same underlying vsnprintf-style formatter.
        return f"{x:.0f}"
    if ax >= 1.0:
        return f"{x:.2f}"
    if ax >= 0.01:
        return f"{x:.3f}"
    return f"{x:.2e}"


def fmt_cos(x: float) -> str:
    """cos_prev: always 4 decimals so 0.9980 vs 0.0170 stay
    distinguishable. Matches C's fmt_csv_cos."""
    return f"{x:.4f}"


# ─── Per-frame row computation ──────────────────────────────────────────

def _channel_energies(enc: np.ndarray) -> list[float]:
    """||channel||² for each of the 10 channels in CHANNELS order.
    Computed in float64 to match C's double arithmetic."""
    e64 = enc.astype(np.float64, copy=False)
    return [float(np.dot(e64[start:start + BOARD_DIM],
                          e64[start:start + BOARD_DIM]))
            for _, start in CHANNELS]


def _row(fr: Frame, prev_enc: np.ndarray | None) -> str:
    """Compute one CSV row for frame fr. prev_enc may be None (ply 0)."""
    E = _channel_energies(fr.encoding)
    total = sum(E)

    if prev_enc is None:
        dist_prev = 0.0
        cos_prev  = 0.0
        dA1       = 0.0
    else:
        cur  = fr.encoding.astype(np.float64, copy=False)
        prev = prev_enc.astype(np.float64, copy=False)
        diff = cur - prev
        dist_prev = float(math.sqrt(float(np.dot(diff, diff))))

        n_cur  = float(math.sqrt(float(np.dot(cur, cur))))
        n_prev = float(math.sqrt(float(np.dot(prev, prev))))
        denom  = n_cur * n_prev
        cos_prev = float(np.dot(cur, prev) / denom) if denom > 0.0 else 0.0

        d_a1 = cur[:BOARD_DIM] - prev[:BOARD_DIM]
        dA1  = float(math.sqrt(float(np.dot(d_a1, d_a1))))

    parts: list[str] = [
        str(fr.ply),
        str(fr.move_from & 0xFF),
        str(fr.move_to & 0xFF),
        fmt_num(dist_prev),
        fmt_cos(cos_prev),
        fmt_num(dA1),
    ]
    parts.extend(fmt_num(e) for e in E)
    parts.append(fmt_num(total))
    return ",".join(parts)


# ─── Meta (PGN annotations) side-channel ────────────────────────────────

def _load_meta(meta_path: str) -> dict[int, dict[str, str]]:
    """Read a pgn_bridge NDJSON file and return a {ply: {col: value}}
    map for the subset of columns in _META_COLUMNS. Missing columns for
    a given ply default to empty strings so CSV alignment stays intact.

    For multi-game NDJSON, the last record wins on ply collision — which
    makes this best used with single-game .spectral files (the common
    case). Two-game merges are out of scope here.
    """
    out: dict[int, dict[str, str]] = {}
    with open(meta_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Skip the NDJSON bridge header.
            if "bridge_version" in rec and "ply" not in rec:
                continue
            if "ply" not in rec:
                continue
            ply = int(rec["ply"])
            out[ply] = {
                col: str(rec[col]) if col in rec and rec[col] is not None else ""
                for col in _META_COLUMNS
            }
    return out


def _meta_suffix(ply: int, meta: dict[int, dict[str, str]]) -> str:
    """Return ',eval,clk,nag' for a row, or ',,,,' if no record for ply."""
    row = meta.get(ply)
    if row is None:
        return "," + ",".join("" for _ in _META_COLUMNS)
    return "," + ",".join(row[col] for col in _META_COLUMNS)


# ─── Public entry points ────────────────────────────────────────────────

def write_csv(input_path: str, output: TextIO | str,
              meta_path: str | None = None) -> int:
    """Read .spectral[z] from input_path, write CSV to `output`
    (either a text stream or a path — "-" means stdout). Returns
    n_plies written. Streams through the file; O(1) memory per row.

    If `meta_path` is given (an NDJSON file from pgn_bridge.py), extra
    `eval,clk,nag` columns are appended to each row. Without `meta_path`,
    output is byte-identical to the C CLI's CSV.
    """
    meta = _load_meta(meta_path) if meta_path else None
    fp = open_read_transparent(input_path)
    try:
        hdr = read_header(fp)
        close_out = False
        if isinstance(output, str):
            if output == "-":
                out = sys.stdout
            else:
                # Default text-mode translation — on Windows this gives
                # CRLF line endings, matching C's fprintf output.
                out = open(output, "w", encoding="utf-8")
                close_out = True
        else:
            out = output

        try:
            header_row = _HEADER_ROW + (_META_HEADER_SUFFIX if meta else "")
            out.write(header_row + "\n")
            prev_enc: np.ndarray | None = None
            for _ in range(hdr.n_plies):
                fr = read_frame(fp)
                row = _row(fr, prev_enc)
                if meta is not None:
                    row += _meta_suffix(fr.ply, meta)
                out.write(row + "\n")
                prev_enc = fr.encoding
            return hdr.n_plies
        finally:
            if close_out:
                out.close()
    finally:
        fp.close()


def iter_rows(frames: Iterable[Frame]) -> Iterator[str]:  # type: ignore[name-defined]
    """Yield CSV rows (including header) from an in-memory frame list.
    Useful in notebooks / REPL when you already have frames loaded."""
    yield _HEADER_ROW
    prev_enc: np.ndarray | None = None
    for fr in frames:
        yield _row(fr, prev_enc)
        prev_enc = fr.encoding


# Small import shim so `from .csv_export import iter_rows` works without
# dragging typing.Iterator into the module-level namespace at import time.
from typing import Iterator  # noqa: E402
