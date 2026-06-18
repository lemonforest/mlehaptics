"""Path B sign-quantise — Class K pin-slot threshold projection.

Identity per ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #174
(structure-preserving denoising primitive): sign-quantise IS a Class K
(threshold / pin-slot / asymptotic-DOF projection) operation. The bit-
discrete sign is the most-compressive non-trivial projection of a real-
valued signal onto the unit ℤ/2 substrate.

Spike #174 SHA-256 BER preservation anchor: at +20 dB SNR, per-channel
sign-quantisation against a calibration threshold preserves SHA-256
bit-discrete content of the underlying clean signal, while Kalman
filtering destroys 19.79% BER at the same SNR. The structure-preserving
property surfaces because sign-quantise IS bit-discrete by construction
(no smoothing across the decision boundary).

Path A dual: :func:`srmech.signal_processing.closed_form_ops.sign_quantise.op`
(numpy sign + dead-band threshold). Both paths IS the same algebra per
``[[user_stance_identity_not_implementation_discipline]]``; bit-exact D1
algebra-identity on the substrate-natural inputs.

The Path B implementation is identical to the Path A reference at the
output level — sign-quantise is already Class K-native; there is no
"binding-layer" overhead for substrate-natural sign decisions. The
distinction is at the dispatch / cascade level: the Path B registration
signals to the cascade dispatcher that sign-quantise composes cleanly
with downstream Class M / Class A operations without re-encoding.

Trauma-informed defensive scope: methodology-research / educational
framing only.

Canonical SSoT
--------------
- Donoho & Johnstone (1994) DOI 10.1093/biomet/81.3.425 — hard / soft
  thresholding.
- Spike #174 — sign-quantise SHA-256 BER preservation at +20 dB SNR;
  ``docs/srmech/notes/spike174_sign_quantise_anchor.py``.
- Plate (1995) IEEE TNN 6, 623.
"""

from __future__ import annotations

from typing import List

OPERATION_NAME = "sign_quantise"
CLASS_COMPOSITION = ("K", "M")
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Donoho & Johnstone (1994), 'Ideal spatial adaptation by wavelet "
    "shrinkage', Biometrika 81(3), 425-455. DOI 10.1093/biomet/81.3.425 "
    "(Crossref). Spike #174 sign-quantise SHA-256 BER preservation at "
    "+20 dB SNR; structure-preserving denoising primitive (anchored)."
)


def op(
    signal,
    *,
    threshold: float = 0.0,
    dead_band: float = 0.0,
    D: int = 8192,
    substrate: str = "cyclic",
):
    """Path B sign-quantise via Class K threshold + Class M dispatch.

    Per Spike #174 anchor: sign-quantise IS Class K pin-slot projection;
    the Path B implementation produces bit-exact identical output to
    Path A on substrate-natural inputs. Class M tag in the composition
    reflects that the output is naturally bindable HDC content.

    Parameters
    ----------
    signal:
        Real array-like.
    threshold:
        Decision threshold; output is ``+1`` above, ``-1`` below.
    dead_band:
        Half-width of the dead-band around ``threshold``; values within
        ``[threshold - dead_band, threshold + dead_band]`` map to ``0``.
    D:
        Path B dimensionality hint (default 8192).
    substrate:
        Substrate label hint. Sign-quantise is substrate-independent at
        the algebra level (Class K projection); accepted for API
        consistency with other Path B ops.

    Returns
    -------
    list of int
        Integer-valued ``{-1, 0, +1}`` list, one per input sample. D1
        algebra-identical to
        :func:`srmech.signal_processing.closed_form_ops.sign_quantise.op`.

    numpy-free (carrier-removal #564, rc94): the Class-K decision is an
    explicit per-element sign-branch (NO ``abs()``; the ``np.where`` carrier is
    gone). The carrier is a plain Python ``list`` throughout.
    """
    arr = [float(v) for v in signal]
    if dead_band <= 0.0:
        # Class K threshold projection: pin-slot at decision boundary.
        return [1 if v >= threshold else -1 for v in arr]
    # Three-level Class K projection with dead-band; the dead-band is the
    # asymptotic-DOF "near-boundary" zone where the pin-slot rejects projection.
    hi = threshold + dead_band
    lo = threshold - dead_band
    out: List[int] = []
    for v in arr:
        if v > hi:
            out.append(1)
        elif v < lo:
            out.append(-1)
        else:
            out.append(0)
    return out


def _register() -> None:
    """Register Path B sign-quantise with the dispatcher's path_registry."""
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    from srmech.signal_processing.closed_form_ops.sign_quantise import (
        op as path_a_sign_quantise,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_sign_quantise,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )
    register(
        OPERATION_NAME,
        path=PATH_B,
        impl=op,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )


_register()
