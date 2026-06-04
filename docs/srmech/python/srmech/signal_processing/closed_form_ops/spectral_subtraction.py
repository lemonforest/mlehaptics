"""Path A spectral subtraction — closed-form denoising via PSD subtraction with floor.

Identity per the implementation plan §1: spectral subtraction IS a Class L
(FFT-domain elementwise PSD operation) ∘ Class N (rational floor / over-
subtraction factor) composition. The closed-form reference applies
``|Y|^2 = max(|X|^2 - alpha * noise_psd, beta * noise_psd)``.

Path B dual in Phase 6 (Path B floor in bound-vector pipeline).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Boll (1979)
+ Berouti, Schwartz & Makhoul (1979).
"""

from __future__ import annotations

import numpy as np

OPERATION_NAME = "spectral_subtraction"
CLASS_COMPOSITION = ("L", "N")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Boll (1979), 'Suppression of acoustic noise in speech using spectral "
    "subtraction', IEEE Trans. ASSP 27(2), 113-120. DOI 10.1109/TASSP.1979."
    "1163209 (Crossref). Berouti, Schwartz & Makhoul (1979), 'Enhancement "
    "of speech corrupted by acoustic noise', Proc. ICASSP 4, 208-211."
)


def op(
    signal,
    noise_psd,
    *,
    alpha: float = 1.0,
    beta: float = 0.01,
    D: int = 8192,
):
    """Spectral subtraction denoising.

    Parameters
    ----------
    signal:
        1-D real noisy observation.
    noise_psd:
        Noise PSD estimate (length ``= len(signal)``).
    alpha:
        Over-subtraction factor (Class N rational; default 1.0 = strict
        subtraction).
    beta:
        Spectral-floor factor; output magnitude floor at ``beta * noise_psd``
        (prevents zero-magnitude bins and musical noise).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Real denoised signal.
    """
    sig = np.asarray(signal, dtype=np.float64)
    n_psd = np.asarray(noise_psd, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError(f"spectral_subtraction expects 1-D signal; got {sig.shape}")
    if n_psd.shape != sig.shape:
        raise ValueError(
            f"noise_psd shape {n_psd.shape} != signal shape {sig.shape}"
        )
    X = np.fft.fft(sig)
    obs_psd = X.real ** 2 + X.imag ** 2  # |z|² = real²+imag² (no abs())
    # Class N rational floor: max(|X|^2 - alpha*N, beta*N)
    new_psd = np.maximum(obs_psd - alpha * n_psd, beta * n_psd)
    # Preserve phase from X; new magnitude from new_psd.
    phase = np.angle(X)
    Y = np.sqrt(new_psd) * np.exp(1j * phase)
    return np.real(np.fft.ifft(Y))
