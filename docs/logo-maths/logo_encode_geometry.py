"""Part-C encoder: turtle trace → D4-irrep spectral HV.

The trick is mapping a continuous turtle trace onto an 8×8 lattice
that `project_irrep` operates on. We:

1. Compute the trace's bounding box and normalize to [0, 8) × [0, 8).
2. Rasterize segments, accumulating path-length-weighted ink per cell.
3. Feed the raw 64-dim intensity vector directly into `project_irrep`
   for the five D4 irreps (A1, A2, B1, B2, E) — yielding a 320-dim HV.

Why we feed the raw grid directly: the chess fiber channels are
piece-type-specific — they use precomputed local Laplacians keyed on
N/B/R/Q/K. Iteration 1 first tried quantizing LOGO ink into piece-chars
and pushing through the full chess `encode_640` pipeline; the quantile
binning destroyed the angular intensity differences between polygons
with different n. The D4-irrep channels (dims 0-319) are all we need:
they ARE the symmetry decomposition, and the raw-intensity `sig`
vector preserves the rotational fingerprint that the
`REPEAT n [FORWARD d RIGHT 360/n]` family generates.

LOGO shapes with D_n symmetry project cleanly onto D4 irreps — a
square hits A1, a triangle splits across A1+B1+B2+E, octagons approach
the A1 rotational ground state. That's the coupling F₂ surfaces.

Iteration 2 dropped the `encode_geometry_640` legacy fallback and the
chess-spectral sys.path import — see `logo_irrep.py` for the inlined
D4 projection.
"""
from __future__ import annotations

import numpy as np

from logo_interp import Trace
from logo_irrep import project_irrep, BOARD_DIM, IRREP_NAMES


# D4 irreps we project onto. Order matters — it's the channel layout
# used by the F₂ machinery and by `_channel_energy` in csv export.
_D4_IRREPS = IRREP_NAMES   # ("A1", "A2", "B1", "B2", "E")
IRREP_DIM = BOARD_DIM * len(_D4_IRREPS)   # 64 × 5 = 320


def _rasterize_trace(trace: Trace, *, pad: float = 0.05) -> np.ndarray:
    """Return a (8, 8) float array of path-length-weighted pen-down ink."""
    grid = np.zeros((8, 8), dtype=np.float64)
    pen_segs = [s for s in trace.segments if s.pen_down]
    if not pen_segs:
        return grid

    xs = [s.x0 for s in pen_segs] + [s.x1 for s in pen_segs]
    ys = [s.y0 for s in pen_segs] + [s.y1 for s in pen_segs]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    w = max(xmax - xmin, 1e-9)
    h = max(ymax - ymin, 1e-9)
    # Pad so extremes don't clip
    xmin -= w * pad; xmax += w * pad
    ymin -= h * pad; ymax += h * pad
    w = xmax - xmin; h = ymax - ymin

    def to_cell(x, y):
        u = (x - xmin) / w
        v = (y - ymin) / h
        ci = min(int(u * 8), 7)
        ri = min(int((1.0 - v) * 8), 7)   # flip y so row 0 is "top"
        return ri, ci

    # Supersampled line rasterization: each segment contributes its length.
    for s in pen_segs:
        length = float(np.hypot(s.x1 - s.x0, s.y1 - s.y0))
        if length == 0.0:
            continue
        # Number of samples — enough to hit every cell on the path.
        n = max(2, int(length))
        xs_ = np.linspace(s.x0, s.x1, n)
        ys_ = np.linspace(s.y0, s.y1, n)
        per = length / (n - 1)
        for x, y in zip(xs_, ys_):
            ri, ci = to_cell(x, y)
            grid[ri, ci] += per
    return grid


def encode_geometry(trace: Trace) -> np.ndarray:
    """Trace → 320-dim D4-irrep HV.

    Concatenates project_irrep(sig, R) for R ∈ {A1, A2, B1, B2, E} on
    the raw rasterized grid. Preserves angular structure so polygons
    with different REPEAT n land in distinct spectral neighbourhoods.

    Empty traces return a zero vector of the correct shape; F₂ machinery
    treats this as "no geometric content, null column."
    """
    grid = _rasterize_trace(trace)
    if grid.sum() == 0.0:
        return np.zeros(IRREP_DIM, dtype=np.float64)
    sig = grid.flatten().astype(np.float64)
    parts = [project_irrep(sig, name) for name in _D4_IRREPS]
    return np.concatenate(parts)


def geometry_grid(trace: Trace) -> np.ndarray:
    """Expose the raw 8×8 intensity grid for debugging."""
    return _rasterize_trace(trace)
