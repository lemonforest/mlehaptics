"""Precomputed tables for the Othello spectral encoder.

Lays out the 768-dim encoder block structure and caches the projector
matrices and orbit Laplacians used by encoder.py.

Cache policy (v0.1.0)
---------------------
Tables are constructed at first use and held in module globals.  No
.npz or version-keyed persistence yet — at D = 768 the construction
cost (10 projector matrices + 2 orbit Laplacians) is well under a
second.  A later phase will add .npz caching with VERSION-keyed
filenames, matching chess-spectral's pattern, once the codegen step
for the ANSI C17 encoder is in scope.

C-parity constraints
--------------------
All tables are built from deterministic linear algebra over rational
D4xZ2 character entries in {-1, 0, 1, 2}; there is no random init
or floating-point rounding path that would differ between Python and
C.  Tables are stored as float64 in memory; binary format (see
frame.py) uses float32 with explicit little-endian struct packing.
"""

from __future__ import annotations

import numpy as np

# Avoid importing the sibling package (othello_spectral) inside its
# own __init__ during tables load.  Re-parent sys.path so we can
# always reach the flat research/ modules.
import sys
from pathlib import Path
_RESEARCH_DIR = Path(__file__).resolve().parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from d4_z2 import D4_CHARS, D4_DIMS, D4_PERMS, IRREP_LABELS, Z2_CHARS  # noqa: E402
from ray_laplacians import orbit_laplacians  # noqa: E402


# ---------------------------------------------------------------------------
# Encoder block layout (v0.1.0)
# ---------------------------------------------------------------------------

# Order matters: this is the canonical dim ordering emitted by
# encode_768.  Channels 0-4 (Z2-odd irreps on s) are magnetisation
# modes; 5-9 (Z2-even irreps on s^2) are occupation modes; 10-11 are
# orbit-Laplacian fiber channels.  Each channel contributes 64
# consecutive dims to the output vector.
_MAGN_IRREPS: tuple[str, ...] = ("A1-", "A2-", "B1-", "B2-", "E-")
_OCC_IRREPS:  tuple[str, ...] = ("A1+", "A2+", "B1+", "B2+", "E+")

CHANNEL_NAMES: tuple[str, ...] = (
    # 0..4: D4xZ2 '-' irreps applied to magnetisation s
    "magn_A1minus", "magn_A2minus", "magn_B1minus", "magn_B2minus", "magn_Eminus",
    # 5..9: D4xZ2 '+' irreps applied to occupation s^2
    "occ_A1plus",  "occ_A2plus",  "occ_B1plus",  "occ_B2plus",  "occ_Eplus",
    # 10..11: orbit-Laplacian fiber channels applied to s
    "fiber_ortho_s", "fiber_diag_s",
)
N_CHANNELS: int = len(CHANNEL_NAMES)  # 12
CELLS_PER_CHANNEL: int = 64
ENCODING_DIM: int = N_CHANNELS * CELLS_PER_CHANNEL  # 768


def channel_slice(index: int) -> slice:
    """Return the slice for channel ``index`` within the 768-dim output."""
    if not 0 <= index < N_CHANNELS:
        raise IndexError(
            f"channel index out of range: {index} (0..{N_CHANNELS - 1})"
        )
    lo = index * CELLS_PER_CHANNEL
    return slice(lo, lo + CELLS_PER_CHANNEL)


# ---------------------------------------------------------------------------
# Projector matrices (10 x 64 x 64)
# ---------------------------------------------------------------------------
# For every D4xZ2 irrep mu_eps, the projector is
#
#     P_{mu_eps} = (d_mu / 16) * sum_{(g,z)} chi_{mu,eps}(g,z) * rho(g,z)
#
# where rho(g,z) = (-1)^z * permutation_matrix(D4_PERMS[g]).
# We materialise P_{mu_eps} as a 64 x 64 matrix; projecting a signal
# f is then P_{mu_eps} @ f.  Character projection is the same algebra
# as d4_z2.project_irrep, restated as a matrix multiply so the encoder
# can be expressed as a single (12 x 64) x (64) matrix action.


def _permutation_matrix(perm: np.ndarray) -> np.ndarray:
    """Build the (64, 64) permutation matrix P with
    (P @ f)[i] = f[perm[i]] — matching the convention used by
    ``d4_z2.apply_element``."""
    P = np.zeros((64, 64), dtype=np.float64)
    for i in range(64):
        P[i, perm[i]] = 1.0
    return P


def _build_projector_d4xz2_minus(irrep_label: str) -> np.ndarray:
    """Build the D4xZ2 '-' irrep projector acting on a Z2-odd signal.

    Following d4_z2.project_irrep convention, the Z2 action is the
    sign flip of the signal (apply_element(sig, g, 1) = -P_g sig).
    Under this convention the '+' irrep projectors are identically
    zero on ANY signal; the '-' irrep projectors are the useful
    ones and satisfy

        P_{mu-} = (d_mu / 16) * sum_{g,z} chi_mu(g) * (-1)^z * (-1)^z * P_g
                = (d_mu / 8) * sum_g chi_mu(g) * P_g

    which is algebraically the D4-only projector scaled by 2x
    (absorbs the Z2 sum).  We retain the full derivation in case a
    future revision adopts a different Z2 convention (e.g. Z2 acting
    on colour labels rather than signal signs).
    """
    if not irrep_label.endswith("-"):
        raise ValueError(
            f"_build_projector_d4xz2_minus called on {irrep_label!r}; "
            f"only '-' irreps are non-trivial under the current "
            f"d4_z2 sign-flip convention."
        )
    mu = irrep_label[:-1]
    d_mu = D4_DIMS[mu]
    chi_d4 = D4_CHARS[mu]
    P = np.zeros((64, 64), dtype=np.float64)
    for g in range(8):
        P = P + chi_d4[g] * _permutation_matrix(D4_PERMS[g])
    return (d_mu / 8.0) * P


def _build_projector_d4(d4_irrep: str) -> np.ndarray:
    """Build the pure D4 irrep projector, suitable for Z2-even signals
    such as occupation s^2.  Character formula:

        P_mu = (d_mu / |D4|) * sum_g chi_mu(g) * P_g
             = (d_mu / 8) * sum_g chi_mu(g) * P_g
    """
    if d4_irrep not in D4_CHARS:
        raise ValueError(
            f"unknown D4 irrep {d4_irrep!r}; expected one of {list(D4_CHARS)}"
        )
    d_mu = D4_DIMS[d4_irrep]
    chi_d4 = D4_CHARS[d4_irrep]
    P = np.zeros((64, 64), dtype=np.float64)
    for g in range(8):
        P = P + chi_d4[g] * _permutation_matrix(D4_PERMS[g])
    return (d_mu / 8.0) * P


# Module-level caches.  Built on first access.
_PROJECTORS: dict[str, np.ndarray] | None = None
_L_ORTHO: np.ndarray | None = None
_L_DIAG: np.ndarray | None = None


def projector(irrep_label: str) -> np.ndarray:
    """Return the (64, 64) projector for a D4xZ2 irrep.

    '-' irreps are applied to Z2-odd signals (magnetisation s).
    '+' irreps are applied to Z2-even signals (occupation s^2)
    via the pure-D4 projector of the same D4 irrep.  Caller is
    responsible for choosing the appropriate signal type.
    """
    global _PROJECTORS
    if _PROJECTORS is None:
        _PROJECTORS = {}
        for lbl in IRREP_LABELS:
            if lbl.endswith("-"):
                _PROJECTORS[lbl] = _build_projector_d4xz2_minus(lbl)
            else:
                _PROJECTORS[lbl] = _build_projector_d4(lbl[:-1])
    if irrep_label not in _PROJECTORS:
        raise ValueError(f"unknown irrep {irrep_label!r}")
    return _PROJECTORS[irrep_label]


def orbit_laplacian_pair() -> tuple[np.ndarray, np.ndarray]:
    """Return (L_ortho, L_diag), each a (64, 64) symmetric PSD
    matrix, cached at module level."""
    global _L_ORTHO, _L_DIAG
    if _L_ORTHO is None or _L_DIAG is None:
        L_o, L_d, _ = orbit_laplacians(directed=False)
        _L_ORTHO = L_o.astype(np.float64)
        _L_DIAG  = L_d.astype(np.float64)
    return _L_ORTHO, _L_DIAG


def magn_irreps() -> tuple[str, ...]:
    """Z2-odd irrep labels in canonical encoder order."""
    return _MAGN_IRREPS


def occ_irreps() -> tuple[str, ...]:
    """Z2-even irrep labels in canonical encoder order."""
    return _OCC_IRREPS
