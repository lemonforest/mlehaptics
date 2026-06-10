"""Path A FFT — closed-form Cooley-Tukey cyclic discrete Fourier transform.

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #176:
the cyclic-DFT IS a Class A (content-addressing on canonical sequence
order) ∘ Class I (cyclic-group ℤ/N transform domain) ∘ Class K
(rotation as pin-slot on the unit circle) composition.

Path B dual ships in Phase 4 of the implementation plan via
``srmech.signal_processing.path_b_ops.fft`` (RBS-HDC native FFT at D=8192).

Closed-form reference: numpy's ``NumPy fft`` (Cooley & Tukey 1965 +
FFTPACK / pocketfft backends). Path A wins for small ``N`` and one-shot
calls; Path B wins for substrate-portable transmission and deep cascades.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from srmech.signal_processing import _fft_carrier as _fc

OPERATION_NAME = "fft"
CLASS_COMPOSITION = ("A", "I", "K")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Cooley & Tukey (1965), 'An algorithm for the machine calculation of "
    "complex Fourier series', Math. Comp. 19, 297-301. DOI 10.1090/"
    "S0025-5718-1965-0178586-1 (Crossref-verified)."
)


def op(signal, *, n: Optional[int] = None, axis: int = -1, D: int = 8192):
    """Forward discrete Fourier transform of ``signal``.

    Parameters
    ----------
    signal:
        Real or complex array-like.
    n:
        Optional length of the transformed axis. ``None`` -> use signal length.
    axis:
        Axis over which to compute the FFT. Default last axis.
    D:
        Path B dimensionality (retained for cross-path API consistency; not
        used by the Path A closed-form numpy backend).

    Returns
    -------
    numpy.ndarray
        Complex DFT coefficients.
    """
    arr = np.asarray(signal)
    return _fc.fft(arr, n=n, axis=axis)
