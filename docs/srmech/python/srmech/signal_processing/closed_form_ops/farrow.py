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

rc151 (BATCH B4d) classification: ``composition_of_c``.  For a fixed ``mu`` the
polynomial-in-``mu`` mixer collapses to ONE effective length-4 FIR
``h_eff[j] = Σ_k mu^k · C[k][j]`` (the Class-N poly-in-mu evaluation), and the
Farrow output is then the cross-correlation ``y[i] = Σ_j h_eff[j]·padded[i+j]``
of the (one-before / two-after) zero-padded signal with ``h_eff`` — a
(feed-forward-only) linear convolution.  So it re-expresses that correlation as a
**Toeplitz matvec** ``M·b`` routed through ``_dsp.correlate_matmul`` →
``laplacian.mat_matvec`` ∘ ``mat_matmul`` → the c_dispatched
``srmech_dense_matmul_complex`` when the native lib is present, and falls back to
the complete numpy-free pure ``_dsp.correlate`` cascade otherwise.  NUMERIC
(within-tol, not byte-identical): the matmul float accumulation may FMA-fuse ~1
ULP on some platforms, so the parity contract is differential (reldiff ≤ 1e-9),
NOT byte-equality.  The ``mu=0`` mixer is ``h_eff = C[0] = (0,1,0,0)`` → exact
integer-delay passthrough (the value oracle).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Farrow
(1988) + Erup, Gardner & Harris (1993).
"""

from __future__ import annotations

from srmech.math.q import Q as _Q, exact_scalar as _exact_scalar   # rc466 (`#T1188`)

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
# by polynomial order 0..3. rc466 (`#T1188`): the table is stored EXACTLY, as
# the rationals the Lagrange derivation produces (through rc465 it was stored
# as floats, so -1/6 and -1/3 were rounded before any signal arrived); the
# float table is DERIVED from it once, and each float entry is the correctly
# rounded value of its exact rational — byte-identical to the old literals.
_FARROW_LAGRANGE_CUBIC_Q = (
    (_Q(0), _Q(1), _Q(0), _Q(0)),                    # C0: input sample at offset 0
    (_Q(-1, 6), _Q(-1, 2), _Q(1), _Q(-1, 3)),         # C1
    (_Q(0), _Q(1, 2), _Q(-1), _Q(1, 2)),              # C2
    (_Q(1, 6), _Q(-1, 2), _Q(1, 2), _Q(-1, 6)),       # C3
)
_FARROW_LAGRANGE_CUBIC = tuple(tuple(float(c) for c in row)
                               for row in _FARROW_LAGRANGE_CUBIC_Q)


def op(signal, *, mu=0, D: int = 8192):
    """Apply a fractional-delay Farrow filter with offset ``mu in [0, 1)``.

    Closed-form reference: cubic Lagrange interpolation via Farrow
    structure. For each output sample, fetches 4 input samples + applies
    the polynomial-in-mu mixer.

    Parameters
    ----------
    signal:
        1-D real input (any sequence of reals).
    mu:
        Fractional delay in [0, 1). 0 -> integer-aligned passthrough. Exact
        (``int`` / ``Q`` / a ``(num, den)`` pair) or ``float``; the default is
        the exact ``0``.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list[float]
        Fractionally-delayed real output (length ``len(signal)``) — ``int`` /
        ``Q`` leaves on the exact route.

    Accuracy (rc466, `#T1188`)
    --------------------------
    **The carrier is the operand's.** An exact ``signal`` with an exact ``mu``
    computes the effective 4-tap kernel ``h_eff[j] = Σ_k mu^k · C[k][j]`` over
    the exact Lagrange table and correlates on the type-preserving pure cascade
    (:func:`srmech.signal_processing._dsp_cascades.correlate`) on BOTH
    projections — the EXACT Farrow output at any rational offset, and at
    ``mu = 0`` the exact integer-delay passthrough the op's own contract
    promises (through rc465 ``farrow([2**53+1, 1, 2], mu=0)[0]`` came back
    ``9007199254740992.0``: the op changed the value it passed through). A
    float leaf in the signal, or a float ``mu``, keeps the float route — the
    float table and the c_dispatched Toeplitz matvec — **accurate to
    round-off** (~1 ULP; reldiff <= 1e-9 to the pure cascade).
    """
    from srmech.signal_processing import _dsp_cascades as _dsp

    mu_q = _exact_scalar(mu)
    if mu_q is not None and _dsp.exact_operands(signal):
        if not 0 <= mu_q < 1:
            raise ValueError(f"mu must be in [0, 1); got {mu}")
        sig_q = list(signal)
        if not sig_q:
            return []
        padded_q = [0] + sig_q + [0, 0]
        h_eff_q = [
            sum((mu_q ** k) * _FARROW_LAGRANGE_CUBIC_Q[k][j] for k in range(4))
            for j in range(4)
        ]
        return list(_dsp.correlate(padded_q, h_eff_q, mode="valid"))
    try:
        sig = [float(x) for x in signal]
    except TypeError as exc:  # nested sequence -> not 1-D
        raise ValueError("farrow expects a 1-D real signal") from exc
    mu = float(mu)
    if not 0.0 <= mu < 1.0:
        raise ValueError(f"mu must be in [0, 1); got {mu}")
    n = len(sig)
    if n == 0:
        return []
    # For closed-form simplicity, pad with zeros: one before, two after, so each
    # output takes 4 taps at positions [i-1, i, i+1, i+2] in the original sig.
    padded = [0.0] + sig + [0.0, 0.0]
    # Class-N poly-in-mu mixer: the 4 sub-filters collapse to ONE length-4
    # effective FIR h_eff[j] = Σ_k mu^k · C[k][j] (each mu^k an explicit
    # left-to-right power). y[i] = Σ_j h_eff[j]·padded[i+j] is then the "valid"
    # cross-correlation of padded with h_eff (length n).
    h_eff = [
        sum((mu ** k) * _FARROW_LAGRANGE_CUBIC[k][j] for k in range(4))
        for j in range(4)
    ]
    # composition_of_c (rc151 / B4d): when the native dense-matmul is present the
    # correlation is a Toeplitz matvec through the c_dispatched
    # srmech_dense_matmul_complex; otherwise the complete numpy-free pure cascade.
    # The matmul path is within-tol (reldiff ≤ 1e-9), not byte-identical.
    from srmech import _native
    from srmech.signal_processing import _dsp_cascades as _dsp

    if (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_dense_matmul_complex")
    ):
        return list(_dsp.correlate_matmul(padded, h_eff, mode="valid"))
    return list(_dsp.correlate(padded, h_eff, mode="valid"))
