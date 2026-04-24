"""Othello spectral encoder package.

Modeled after docs/chess-maths/chess-spectral/ (chess-spectral) but
specialised to D4xZ2 exact symmetry (single-disc Blume-Capel) rather
than chess's approximate-Z2 plus piece-species structure.

Public API
----------
  encode_768(state) -> np.ndarray[768]
      The main encoder entry point.  Input is a length-64 int array
      in {-1, 0, +1} (world-frame Blume-Capel signal).  Output is a
      768-dim float64 vector decomposed as:

         dims  [  0: 320)  5 D4xZ2 '-' irreps on magnetisation s
         dims  [320: 640)  5 D4xZ2 '+' irreps on occupation s^2
         dims  [640: 768)  2 orbit-Laplacian fiber channels
                           (L_ortho @ s, L_diag @ s)

      Layout within each block is [irrep0_row0..63, irrep1_row0..63, ...]
      so channel k occupies dims [k*64, (k+1)*64).

  CHANNEL_NAMES: list[str]
      The 12 channel labels in encoder order.

  channel_energies(enc) -> dict[str, float]
      Convenience: ||channel_k||^2 for each of the 12 channels.

  VERSION: str
      Encoder version string.  Bump on any math change; the cached
      tables are keyed by version so downstream pipelines can detect
      mismatches.

Design choices locked in v0.1.0
-------------------------------
- Internal math: float64 (numpy default).
- Binary on-disk (frame.py): float32 little-endian, for C parity.
- No random init; all tables are deterministic eigendecompositions.
- Encoder is pure function of state (no side-to-move coupling).
  Z2 colour-flip equivariance is handled at the IRREP level, not by
  conditioning on side.
"""

from __future__ import annotations

from pathlib import Path as _Path


def _read_version() -> str:
    """Load the package version from the VERSION file.

    Single source of truth for both the Python package semver and the
    C encoder codegen (codegen/emit_c_tables.py emits the same string
    into the generated C header).  If VERSION file is missing (e.g.
    running from a partial checkout) fall back to a sentinel.
    """
    version_file = _Path(__file__).resolve().parent / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0-unknown"


VERSION: str = _read_version()
__version__: str = VERSION

# Public re-exports (populated on first call - avoids circular
# import during tables/encoder cross-loading).
from .tables import CHANNEL_NAMES, ENCODING_DIM
from .encoder import encode_768, channel_energies

__all__ = [
    "VERSION",
    "__version__",
    "CHANNEL_NAMES",
    "ENCODING_DIM",
    "encode_768",
    "channel_energies",
]
