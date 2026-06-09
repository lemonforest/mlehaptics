"""Path A Farrow structure — closed-form fractional-delay polynomial filter.

Identity per the implementation plan §1: Farrow IS a Class N (rational
polynomial-in-mu fractional delay; ``mu in [0, 1)`` is the rational
fractional-sample-offset) operation. Each polynomial-order coefficient is a
fixed sub-filter; the runtime mixer scales each by ``mu^k``.

The closed-form reference ships the canonical Farrow structure for cubic
Lagrange-interpolation fractional delay.

Path B dual in Phase 6 (Path B rational polynomial bound-vector eval).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Farrow
(1988) + Erup, Gardner & Harris (1993).
"""

from __future__ import annotations

import numpy as np

from srmech.amsc.laplacian import dense_dot_real

OPERATION_NAME = "farrow"
CLASS_COMPOSITION = ("N",)
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Farrow (1988), 'A continuously variable digital delay element', IEEE "
    "ISCAS 1988, 2641-2645. DOI 10.1109/ISCAS.1988.15483 (Crossref). Erup, "
    "Gardner & Harris (1993), 'Interpolation in digital modems--Part II: "
    "Implementation and performance', IEEE Trans. Commun. 41(6), 998-1008. "
    "DOI 10.1109/26.231921."
)


# Cubic Lagrange interpolation Farrow sub-filters (Erup et al. 1993).
# h(mu, n) = sum_k C[k, n] * mu^k where the 4-tap sub-filter rows are
# indexed by polynomial order 0..3.
_FARROW_LAGRANGE_CUBIC = np.array(
    [
        [0.0, 1.0, 0.0, 0.0],          # C0: input sample at offset 0
        [-1 / 6, -1 / 2, 1.0, -1 / 3], # C1
        [0.0, 1 / 2, -1.0, 1 / 2],     # C2
        [1 / 6, -1 / 2, 1 / 2, -1 / 6],# C3
    ],
    dtype=np.float64,
)


def op(signal, *, mu: float = 0.0, D: int = 8192):
    """Apply a fractional-delay Farrow filter with offset ``mu in [0, 1)``.

    Closed-form reference: cubic Lagrange interpolation via Farrow
    structure. For each output sample, fetches 4 input samples + applies
    the polynomial-in-mu mixer.

    Parameters
    ----------
    signal:
        1-D real input.
    mu:
        Fractional delay in [0, 1). 0 -> integer-aligned passthrough.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Fractionally-delayed real output.
    """
    sig = np.asarray(signal, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError(f"farrow expects 1-D signal; got {sig.shape}")
    if not 0.0 <= mu < 1.0:
        raise ValueError(f"mu must be in [0, 1); got {mu}")
    n = sig.shape[0]
    out = np.zeros(n, dtype=np.float64)
    # Each output sample takes 4 input samples centred around the integer index.
    # For closed-form simplicity, pad with zeros.
    padded = np.concatenate([np.zeros(1), sig, np.zeros(2)])
    for i in range(n):
        # 4 taps at positions [i-1, i, i+1, i+2] in original sig
        x = padded[i : i + 4]
        # Mixer: y = sum_k mu^k * (C[k] dot x)
        y = 0.0
        for k in range(4):
            y += (mu ** k) * dense_dot_real(_FARROW_LAGRANGE_CUBIC[k], x)
        out[i] = y
    return out
