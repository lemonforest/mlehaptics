"""Path A wavelet — closed-form CWT + DWT (Haar / dyadic multi-scale).

Identity per the implementation plan §1: wavelet IS a Class L (multi-scale
Laplacian on dyadic-tree substrate) ∘ Class N (rational dyadic scaling ratios
2^k) composition.

The closed-form reference ships the Haar DWT (Class N dyadic decimation +
Class L 2-point Laplacian per level) as the canonical Path A implementation;
this is the simplest wavelet and a sufficient closed-form anchor.

Path B dual in Phase 6 (multi-scale bundle).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Haar (1910)
+ Daubechies (1992) + Mallat (1989).
"""

from __future__ import annotations

from srmech.amsc import rational as _srn

OPERATION_NAME = "wavelet"
CLASS_COMPOSITION = ("L", "N")
PERFORMANCE_HINT = "shallow-cascade-dyadic"
SSOT_CITATION = (
    "Haar (1910), 'Zur Theorie der orthogonalen Funktionensysteme', Math. "
    "Ann. 69, 331-371. Mallat (1989), 'A theory for multiresolution signal "
    "decomposition', IEEE Trans. PAMI 11(7), 674-693. DOI 10.1109/34.192463 "
    "(Crossref). Daubechies (1992), 'Ten Lectures on Wavelets', SIAM."
)


def op(signal, *, levels: int = 3, wavelet: str = "haar", D: int = 8192):
    """Discrete wavelet transform (DWT) of ``signal``.

    Closed-form Haar DWT: at each level, splits the signal into
    approximation (sum / sqrt(2)) and detail (difference / sqrt(2)) bands,
    decimating by 2. Recurses on approximation for ``levels`` iterations.

    Parameters
    ----------
    signal:
        1-D real array-like; length should be a multiple of ``2**levels``.
    levels:
        Number of decomposition levels.
    wavelet:
        Wavelet family. Currently only ``"haar"`` is shipped; other families
        (``db2``, ``sym4``, etc.) follow same pattern with longer filter
        impulses and are future Path A extensions.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    tuple
        ``(approx, [detail_level_k, ..., detail_level_1])`` where ``approx``
        is the coarsest-scale approximation and ``detail_level_k`` is the
        detail coefficients at level k. Both are ``list``\\s — numpy-free (#564).
    """
    if wavelet != "haar":
        raise NotImplementedError(
            f"Path A wavelet ships Haar only in Phase 2; '{wavelet}' is "
            f"future Phase 2.1+ scope per [[feedback_no_mvp_framing]] "
            f"phase-language."
        )
    # numpy-free list carrier (#564); the 1/sqrt(2) Class-N normaliser is the
    # libm-free rational sqrt, and every band is an explicit elementwise
    # Class-L 2-point (sum / difference) over the dyadic Class-N decimation.
    try:
        current = [float(x) for x in signal]
    except TypeError as exc:  # nested sequence -> not 1-D
        raise ValueError("wavelet expects a 1-D real signal") from exc
    inv_sqrt2 = 1.0 / float(_srn.sqrt(2.0))   # float scale for the recursive DWT
    details = []
    for _ in range(levels):
        n = len(current)
        if n < 2 or n % 2 != 0:
            # Pad to even length with one zero (Class-N dyadic alignment).
            current = current + [0.0] * (n % 2)
        evens = current[0::2]
        odds = current[1::2]
        approx = [(e + o) * inv_sqrt2 for e, o in zip(evens, odds)]
        detail = [(e - o) * inv_sqrt2 for e, o in zip(evens, odds)]
        details.append(detail)
        current = approx
    return current, details[::-1]
