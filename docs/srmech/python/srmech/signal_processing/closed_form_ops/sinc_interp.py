"""Path A sinc interpolation — closed-form Whittaker-Shannon band-limit interpolation.

Identity per the implementation plan §1: sinc interpolation IS a Class L
(band-limit Laplacian eigenbasis: ideal low-pass filter with cutoff at
Nyquist) ∘ Class K (band-limit pin-slot threshold) composition. The classical
Whittaker-Shannon formula reconstructs a band-limited signal at arbitrary
time-offsets via a sum of shifted sinc kernels.

Path B dual in Phase 6 (Path B band-limit bundle).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Whittaker
(1915) + Shannon (1949) + Oppenheim & Schafer (2010, 3rd ed.) §4.1.
"""

from __future__ import annotations

import numpy as np

OPERATION_NAME = "sinc_interp"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Whittaker (1915), 'On the functions which are represented by the "
    "expansions of the interpolation-theory', Proc. Royal Soc. Edinburgh "
    "35, 181-194. Shannon (1949), 'Communication in the presence of "
    "noise', Proc. IRE 37(1), 10-21. DOI 10.1109/JRPROC.1949.232969 "
    "(Crossref). Oppenheim & Schafer (2010, 3rd ed.), 'Discrete-Time "
    "Signal Processing', Prentice Hall, §4.1."
)


def op(signal, sample_indices, target_indices, *, D: int = 8192):
    """Whittaker-Shannon sinc interpolation.

    Reconstructs ``f(target_indices)`` from ``f(sample_indices) = signal``
    via the band-limited sinc sum.

    Parameters
    ----------
    signal:
        Real or complex values at ``sample_indices``.
    sample_indices:
        Real-valued sample times of the known values.
    target_indices:
        Real-valued sample times to evaluate at.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Interpolated values at ``target_indices``.
    """
    y = np.asarray(signal, dtype=np.complex128)
    t_s = np.asarray(sample_indices, dtype=np.float64)
    t_q = np.asarray(target_indices, dtype=np.float64)
    if y.ndim != 1 or t_s.ndim != 1:
        raise ValueError(
            f"sinc_interp expects 1-D signal and sample_indices; got "
            f"{y.shape} and {t_s.shape}"
        )
    if y.shape[0] != t_s.shape[0]:
        raise ValueError(
            f"signal length {y.shape[0]} != sample_indices length {t_s.shape[0]}"
        )
    # Estimate sample spacing.
    if t_s.shape[0] >= 2:
        T = np.median(np.diff(t_s))
    else:
        T = 1.0
    # Sinc matrix: K[q, s] = sinc((t_q - t_s) / T)
    if t_q.ndim == 0:
        t_q_arr = np.array([t_q], dtype=np.float64)
    else:
        t_q_arr = t_q
    K = np.sinc((t_q_arr[:, None] - t_s[None, :]) / T)
    out = K @ y
    if t_q.ndim == 0:
        return out[0]
    return out
