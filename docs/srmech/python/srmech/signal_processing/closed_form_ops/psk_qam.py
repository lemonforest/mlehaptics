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

Carrier-removal #564 (rc106): numpy-FREE — the PSK constellation points
``e^{i·2π·k/M}`` route through the Class-N ``rational.cos`` / ``rational.sin``
cascade over the substrate-native ``_PI`` source (``_exp_i``, native libm-free);
the QAM grid is built from pure-Python Gray-coded levels (``√M`` via the Class-N
``rational.sqrt``); and the demodulator's nearest-neighbour decision is
``argmin |received − const|²`` (squared distance is monotone in ``|·|``, so no
``sqrt`` and no ``abs()``). Inputs are coerced numpy-free and the op returns
plain Python ``list``s. No top-level ``import numpy``.

rc153 (BATCH B7) classification: ``composition_of_c``. The genuine float math
is the constellation build — the PSK phases ``e^{i·2π·k/M}`` ride the
c_dispatched ``rational.cos`` / ``rational.sin`` cascade and the QAM grid rides
the c_dispatched ``rational.sqrt`` (``√M``). Modulate is then an integer index
lookup; demodulate is a nearest-neighbour Class-K decision-region search over
the numpy-free ``|received − const|²`` squared-distance glue. NUMERIC within-tol
(native == pure to reldiff ≤ 1e-9, NOT byte-identical).

Path B dual in Phase 6 (Path B ℤ/M cyclic + threshold).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Proakis &
Salehi (2008, 5th ed.) *Digital Communications* §4.3 (PSK) + §4.4 (QAM);
educational baseband-modulation textbook reference only.
"""

from __future__ import annotations

from typing import List

from srmech.amsc import rational as _srn

OPERATION_NAME = "psk_qam"
CLASS_COMPOSITION = ("I", "K")
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Proakis & Salehi (2008, 5th ed.), 'Digital Communications', McGraw-Hill, "
    "§4.3 (PSK constellation) + §4.4 (QAM constellation). Educational "
    "civilian-comms textbook reference."
)

# Class-N π cascade (Archimedes hexagon-doubling, Spike #32) — the substrate-
# native π source for the PSK constellation phases; NOT math.pi / np.pi.
_PI = float(_srn.pi_cascade_digits(30))


def _exp_i(theta: float) -> complex:
    """``e^{iθ} = cos θ + i·sin θ`` via the Class-N rational trig cascade.

    Bit-faithful to the prior ``elementwise_transcendental(·, 'exp_i')`` path
    (both run the same native libm-free ``rational.cos`` / ``rational.sin``
    range-reduced cascade); numpy-free.
    """
    return complex(_srn.cos(theta), _srn.sin(theta))


def _as_list(v) -> list:
    """Coerce an array-like to a plain Python list (numpy-free)."""
    return v.tolist() if hasattr(v, "tolist") else list(v)


def _psk_constellation(M: int) -> List[complex]:
    """M-PSK constellation: ``exp(j·2π·k/M)`` for k in 0..M-1 (numpy-free)."""
    return [_exp_i(2.0 * _PI * k / M) for k in range(M)]


def _qam_constellation(M: int) -> List[complex]:
    """Square M-QAM constellation; requires sqrt(M) to be integer (numpy-free)."""
    sqrt_m = int(round(float(_srn.sqrt(float(M)))))   # √M → float before round()
    if sqrt_m * sqrt_m != M:
        raise ValueError(f"square QAM requires M = K^2; got M={M}")
    # Gray-coded levels: {-(sqrt_m-1), ..., -1, 1, ..., (sqrt_m-1)}
    levels = [2.0 * j - (sqrt_m - 1) for j in range(sqrt_m)]
    # numpy-free equivalent of ``np.meshgrid(levels, levels)`` flattened C-order:
    # point = I + jQ with I = levels[col] (x / first arg), Q = levels[row]
    # (y / second arg); the row-major flatten iterates rows (Q) outer, cols (I)
    # inner — byte-faithful to the prior ``.flatten()`` ordering.
    return [
        complex(levels[col], levels[row])
        for row in range(sqrt_m)
        for col in range(sqrt_m)
    ]


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
        Modulate: array-like of integer symbol indices in ``[0, M)``.
        Demodulate: array-like of complex received constellation points.
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
    Modulate: ``list`` of complex constellation points (one per input symbol).
    Demodulate: ``list`` of integer symbol indices (one per received point).
    """
    if modulation == "psk":
        const = _psk_constellation(M)
    elif modulation == "qam":
        const = _qam_constellation(M)
    else:
        raise ValueError(f"modulation must be 'psk' or 'qam'; got {modulation}")

    if demodulate:
        received = [complex(z) for z in _as_list(symbols)]
        # Class K: nearest-neighbour decision-region projection. Decide on
        # argmin |received − const|² (squared distance is monotone in
        # |·| = hypot(re, im), so no sqrt and no abs(); strict ``<`` keeps the
        # first-minimum index, matching the prior np.argmin tie-break).
        out: List[int] = []
        for z in received:
            best_k = 0
            best_d2 = None
            for k in range(len(const)):
                d = z - const[k]
                d2 = d.real * d.real + d.imag * d.imag
                if best_d2 is None or d2 < best_d2:
                    best_d2 = d2
                    best_k = k
            out.append(best_k)
        return out

    syms = [int(s) for s in _as_list(symbols)]
    for s in syms:
        if s < 0 or s >= M:
            raise ValueError(f"symbols must be in [0, {M})")
    return [const[s] for s in syms]
