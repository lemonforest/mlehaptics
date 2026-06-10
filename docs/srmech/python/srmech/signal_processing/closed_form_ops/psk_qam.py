"""Path A PSK / QAM constellation mapping — closed-form digital modulation primitive.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
this op covers civilian-comms baseband modulation (WiFi-class symbol mapping,
educational physics-textbook content). No targeting; no capability-assessment;
no military framing.

Identity per the implementation plan §1: PSK / QAM constellation IS a Class I
(cyclic group ℤ/M for the symbol alphabet) ∘ Class K (threshold / decision-
region projection on the I-Q plane) composition. Class I provides the integer
symbol indices; Class K provides the constellation point lookup and inverse
detection.

Path B dual in Phase 6 (Path B ℤ/M cyclic + threshold).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Proakis &
Salehi (2008, 5th ed.) *Digital Communications* §4.3 (PSK) + §4.4 (QAM);
educational baseband-modulation textbook reference only.
"""

from __future__ import annotations

import numpy as np

from srmech.amsc import rational as _srn

from srmech.amsc import rational as _srn

from srmech.amsc.laplacian import elementwise_hypot, elementwise_transcendental

OPERATION_NAME = "psk_qam"
CLASS_COMPOSITION = ("I", "K")
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Proakis & Salehi (2008, 5th ed.), 'Digital Communications', McGraw-Hill, "
    "§4.3 (PSK constellation) + §4.4 (QAM constellation). Educational "
    "civilian-comms textbook reference."
)


def _psk_constellation(M: int) -> np.ndarray:
    """M-PSK constellation: ``exp(j * 2*pi * k / M)`` for k in 0..M-1."""
    return elementwise_transcendental(2.0 * np.pi * np.arange(M) / M, "exp_i")


def _qam_constellation(M: int) -> np.ndarray:
    """Square M-QAM constellation; requires sqrt(M) to be integer."""
    sqrt_m = int(round(_srn.sqrt(float(M))))
    if sqrt_m * sqrt_m != M:
        raise ValueError(f"square QAM requires M = K^2; got M={M}")
    # Gray-coded levels: {-(sqrt_m-1), ..., -1, 1, ..., (sqrt_m-1)}
    levels = 2.0 * np.arange(sqrt_m) - (sqrt_m - 1)
    i_pts, q_pts = np.meshgrid(levels, levels)
    return (i_pts + 1j * q_pts).flatten()


def op(
    symbols,
    *,
    modulation: str = "psk",
    M: int = 4,
    demodulate: bool = False,
    D: int = 8192,
):
    """Map symbol indices to constellation points, or demodulate received
    points back to nearest-neighbour symbol indices.

    Parameters
    ----------
    symbols:
        Modulate: array of integer symbol indices in ``[0, M)``.
        Demodulate: array of complex received constellation points.
    modulation:
        ``"psk"`` or ``"qam"``.
    M:
        Constellation order (2, 4, 8 PSK; 4, 16, 64 QAM).
    demodulate:
        If True, return nearest-neighbour symbol indices.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Modulate: complex constellation-point array.
    Demodulate: integer symbol-index array.
    """
    if modulation == "psk":
        const = _psk_constellation(M)
    elif modulation == "qam":
        const = _qam_constellation(M)
    else:
        raise ValueError(f"modulation must be 'psk' or 'qam'; got {modulation}")

    if demodulate:
        received = np.asarray(symbols, dtype=np.complex128)
        flat = received.ravel()
        # Class K: nearest-neighbour decision-region projection.
        _d = flat[:, None] - const[None, :]
        dists = elementwise_hypot(_d.real, _d.imag)  # |z| = hypot(real,imag) (no abs())
        idx = np.argmin(dists, axis=1)
        return idx.reshape(received.shape)

    syms = np.asarray(symbols, dtype=np.int64)
    if np.any(syms < 0) or np.any(syms >= M):
        raise ValueError(f"symbols must be in [0, {M})")
    return const[syms]
