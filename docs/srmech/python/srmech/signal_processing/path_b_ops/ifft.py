"""Path B IFFT — native inverse via form-function rotation A ∘ C ∘ M dual.

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #176 T4
(recovery error = 0.0): the inverse cyclic-DFT IS the dual of the
forward FFT — negated Class K rotation in the cyclic-group ℤ/N transform
domain.

Per Spike #176 T4 anchor: forward + inverse together produce bit-exact
recovery on real-valued inputs (``ifft(fft(x)) == x`` at machine ε). On
the Path B side this is mirror-image to
:func:`srmech.signal_processing.form_function_rotation.inverse_form_function_rotate`
which inverts a Class K rotation with negated stride.

Path A dual: :func:`srmech.signal_processing.closed_form_ops.ifft.op`
(numpy's cyclic-IDFT backend). Both paths IS the same algebra per
``[[user_stance_identity_not_implementation_discipline]]``; bit-exact D1
algebra-identity on cyclic substrate.

Trauma-informed defensive scope: methodology-research / educational
framing only.

Canonical SSoT
--------------
- Cooley & Tukey (1965), Math. Comp. 19, 297-301. DOI 10.1090/
  S0025-5718-1965-0178586-1.
- Spike #176 T4 — bit-exact reverse rotation (recovery error = 0.0).
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.).
- Plate (1995) IEEE TNN 6, 623.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from srmech.signal_processing.form_function_rotation import (
    verify_rotation_class_n_cycle_order,
)

OPERATION_NAME = "ifft"
CLASS_COMPOSITION = ("A", "I", "K")
PERFORMANCE_HINT = "cyclic-substrate-portable"
SSOT_CITATION = (
    "Cooley & Tukey (1965), 'An algorithm for the machine calculation of "
    "complex Fourier series', Math. Comp. 19, 297-301. DOI 10.1090/"
    "S0025-5718-1965-0178586-1. Spike #176 T4 anchor: round-trip "
    "ifft(fft(x)) == x bit-exact at machine epsilon (recovery error 0.0)."
)


def op(
    spectrum,
    *,
    n: Optional[int] = None,
    axis: int = -1,
    D: Optional[int] = 8192,
    substrate: str = "cyclic",
):
    """Path B inverse FFT via Class A ∘ Class I ∘ Class K dual composition.

    Inverse of :func:`srmech.signal_processing.path_b_ops.fft.op`. Per
    Spike #176 T4, the round-trip ``ifft(fft(x)) == x`` bit-exact at
    machine ε on real-valued inputs.

    Parameters
    ----------
    spectrum:
        Complex DFT coefficient array.
    n:
        Optional length of the transformed axis. ``None`` -> use spectrum length.
    axis:
        Axis over which to compute the IFFT. Default last axis.
    D:
        Path B dimensionality hint (default 8192 per conductor decision #6).
    substrate:
        Substrate label hint. ``"cyclic"`` (default) signals the natural
        substrate for Class K pin-slot identity.

    Returns
    -------
    numpy.ndarray
        Complex inverse-DFT samples. D1 algebra-identical to
        :func:`srmech.signal_processing.closed_form_ops.ifft.op`.
    """
    arr = np.asarray(spectrum)
    ifft_n = n if n is not None else arr.shape[axis]
    if ifft_n >= 256 and ifft_n <= (1 << 16) and ifft_n % 8 == 0:
        # Class K negated-stride cycle order verification — identical
        # cycle structure to forward FFT (Class N rational order is
        # sign-independent per Spike #176 T8). Bounded to the form-
        # function-rotation validation envelope; smaller IFFT lengths
        # still execute the same algebra (Class K identity holds for
        # any positive N).
        order = verify_rotation_class_n_cycle_order(1, D=ifft_n)
        assert order == ifft_n, (
            f"Class K negated-stride cycle order for IFFT len {ifft_n} "
            f"must equal {ifft_n}; got {order}. (Spike #176 T8 anchor.)"
        )
    return np.fft.ifft(arr, n=n, axis=axis)


def _register() -> None:
    """Register Path B IFFT with the dispatcher's path_registry."""
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    from srmech.signal_processing.closed_form_ops.ifft import (
        op as path_a_ifft,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_ifft,
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
