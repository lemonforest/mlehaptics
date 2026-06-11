"""Path A Farrow structure — closed-form fractional-delay polynomial filter.

Identity per the implementation plan §1: Farrow IS a Class N (rational
polynomial-in-mu fractional delay; ``mu in [0, 1)`` is the rational
fractional-sample-offset) operation. Each polynomial-order coefficient is a
fixed sub-filter; the runtime mixer scales each by ``mu^k``.

The closed-form reference ships the canonical Farrow structure for cubic
Lagrange-interpolation fractional delay.

Path B dual in Phase 6 (Path B rational polynomial bound-vector eval).

Carrier note (#564): numpy-free. The 4-tap Lagrange sub-filter is a fixed
constant table of Python floats and each ``C[k]·x`` is an explicit length-4
Class-M micro-reduction (Σ aᵢ bᵢ over four terms, left-to-right — bit-faithful
to the prior ``dense_dot_real`` route, which fed numpy carriers into the native
elementwise-bind kernel only to contract four reals). No top-level ``import
numpy``; the op runs on a plain-``list`` carrier with no numpy present.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Farrow
(1988) + Erup, Gardner & Harris (1993).
"""

from __future__ import annotations

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
# h(mu, n) = sum_k C[k][n] * mu^k where the 4-tap sub-filter rows are indexed
# by polynomial order 0..3. Plain-tuple constant table (numpy-free carrier per
# #564); each row is a fixed 4-tuple of exact-rational Lagrange coefficients.
_FARROW_LAGRANGE_CUBIC = (
    (0.0, 1.0, 0.0, 0.0),             # C0: input sample at offset 0
    (-1 / 6, -1 / 2, 1.0, -1 / 3),    # C1
    (0.0, 1 / 2, -1.0, 1 / 2),        # C2
    (1 / 6, -1 / 2, 1 / 2, -1 / 6),   # C3
)


def op(signal, *, mu: float = 0.0, D: int = 8192):
    """Apply a fractional-delay Farrow filter with offset ``mu in [0, 1)``.

    Closed-form reference: cubic Lagrange interpolation via Farrow
    structure. For each output sample, fetches 4 input samples + applies
    the polynomial-in-mu mixer.

    Parameters
    ----------
    signal:
        1-D real input (any sequence of reals).
    mu:
        Fractional delay in [0, 1). 0 -> integer-aligned passthrough.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list[float]
        Fractionally-delayed real output (length ``len(signal)``).
    """
    try:
        sig = [float(x) for x in signal]
    except TypeError as exc:  # nested sequence -> not 1-D
        raise ValueError("farrow expects a 1-D real signal") from exc
    if not 0.0 <= mu < 1.0:
        raise ValueError(f"mu must be in [0, 1); got {mu}")
    n = len(sig)
    # Each output sample takes 4 input samples centred around the integer index.
    # For closed-form simplicity, pad with zeros: one before, two after.
    padded = [0.0] + sig + [0.0, 0.0]
    out = []
    for i in range(n):
        # 4 taps at positions [i-1, i, i+1, i+2] in original sig.
        x = padded[i : i + 4]
        # Mixer: y = sum_k mu^k * (C[k] dot x); each dot is an explicit length-4
        # Class-M reduction (left-to-right, numpy-free).
        y = 0.0
        for k in range(4):
            c = _FARROW_LAGRANGE_CUBIC[k]
            dot = c[0] * x[0] + c[1] * x[1] + c[2] * x[2] + c[3] * x[3]
            y += (mu ** k) * dot
        out.append(y)
    return out
