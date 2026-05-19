"""Path A IFFT — closed-form Cooley-Tukey cyclic inverse discrete Fourier transform.

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #176:
the inverse cyclic-DFT IS the dual of the forward FFT — a Class A
(content-addressing on canonical sequence order) ∘ Class I (cyclic-group
ℤ/N transform domain) ∘ Class K (negated phase operator) composition.

Per Spike #176 T4 anchor: forward + inverse together produce bit-exact
recovery (``ifft(fft(x)) == x`` at machine ε on real-valued inputs).

Path B dual ships alongside via ``srmech.signal_processing.path_b_ops.ifft``
(RBS-HDC native IFFT at D=8192). Both paths instantiate the same algebra
per ``[[user_stance_identity_not_implementation_discipline]]``.

Phase 4 (v0.4.2rc4) addition. Path A IFFT did not ship in Phase 2 (only
the forward FFT did); Phase 4 lands both as duals so the dual-path
test suite can assert D1 round-trip identity (Spike #176 T4 anchor).

Closed-form reference: numpy's ``numpy.fft.ifft`` (Cooley & Tukey 1965
+ FFTPACK / pocketfft backends).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

OPERATION_NAME = "ifft"
CLASS_COMPOSITION = ("A", "I", "K")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Cooley & Tukey (1965), 'An algorithm for the machine calculation of "
    "complex Fourier series', Math. Comp. 19, 297-301. DOI 10.1090/"
    "S0025-5718-1965-0178586-1 (Crossref-verified). Spike #176 T4 anchor: "
    "round-trip ifft(fft(x)) == x bit-exact at machine epsilon."
)


def op(spectrum, *, n: Optional[int] = None, axis: int = -1, D: int = 8192):
    """Inverse discrete Fourier transform of ``spectrum``.

    Parameters
    ----------
    spectrum:
        Complex array-like of DFT coefficients.
    n:
        Optional length of the transformed axis. ``None`` -> use spectrum length.
    axis:
        Axis over which to compute the IFFT. Default last axis.
    D:
        Path B dimensionality (retained for cross-path API consistency; not
        used by the Path A closed-form numpy backend).

    Returns
    -------
    numpy.ndarray
        Complex inverse-DFT samples.
    """
    arr = np.asarray(spectrum)
    return np.fft.ifft(arr, n=n, axis=axis)
