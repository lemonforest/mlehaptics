"""Path A sign-quantise — closed-form Class K threshold-with-acceptance-band.

Identity per ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #174:
sign-quantise IS a Class K (threshold / pin-slot / asymptotic-DOF projection)
operation. The closed-form reference applies ``sign(x - threshold)`` with an
optional dead-band around zero.

Phase 2 ships the Path A surface as a Python-only Class K composition per the
plan's §6 Phase 2 task list (note: Class K's C primitive port is phase-language
deferred to v0.4.3 per the plan's §7.6 and ``[[feedback_no_binding_layer_carveout]]``).

Path B dual in Phase 4 (Path B threshold via Class K bit-rotation per Spike
#174 anchor).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Donoho &
Johnstone (1994) hard / soft thresholding + Spike #174 sign-quantise SHA-256
BER preservation result.
"""

from __future__ import annotations

OPERATION_NAME = "sign_quantise"
CLASS_COMPOSITION = ("K",)
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Donoho & Johnstone (1994), 'Ideal spatial adaptation by wavelet "
    "shrinkage', Biometrika 81(3), 425-455. DOI 10.1093/biomet/81.3.425 "
    "(Crossref). Spike #174 sign-quantise SHA-256 BER preservation at +20 dB "
    "SNR; srmech notebook §3.8.{spike_174_anchor}."
)


def op(signal, *, threshold: float = 0.0, dead_band: float = 0.0, D: int = 8192):
    """Sign-quantise ``signal`` with optional dead-band around threshold.

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
        Path B dimensionality (Path A unused).

    Returns
    -------
    list[int]
        Integer-valued ``{-1, 0, +1}`` list, one entry per input sample
        (the framework-native numpy-free carrier; #564 carrier-flip).
    """
    # Carrier: a plain Python list of floats (numpy-free; iterating an
    # ndarray input yields scalars, so an array_like still works).
    arr = [float(x) for x in signal]
    out = []
    if dead_band <= 0.0:
        # Class K pin-slot: the threshold IS the sign boundary (no abs()).
        for x in arr:
            out.append(1 if x >= threshold else -1)
    else:
        hi = threshold + dead_band
        lo = threshold - dead_band
        for x in arr:
            if x > hi:
                out.append(1)
            elif x < lo:
                out.append(-1)
            else:
                out.append(0)          # the dead-band (acceptance) zone
    return out
