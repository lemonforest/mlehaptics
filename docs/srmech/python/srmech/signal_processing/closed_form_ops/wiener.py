"""Path A Wiener filter — closed-form block / offline frequency-domain Wiener.

Identity per the implementation plan §1: Wiener IS a Class L (Laplacian
eigenbasis on the power-spectrum substrate) ∘ Class N (rational MMSE gain
``S_xx / (S_xx + S_nn)``) composition. The closed-form block / offline
estimator computes the rational gain per frequency bin from the signal
and noise PSDs and applies it via FFT.

Path B dual in Phase 4 (Wiener via bundled eigenvalue handles).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Wiener
(1949) + Kay (1993) §11 + Hayes (1996) §7.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

OPERATION_NAME = "wiener"
CLASS_COMPOSITION = ("L", "N")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Wiener (1949), 'Extrapolation, Interpolation, and Smoothing of "
    "Stationary Time Series', MIT Press. Kay (1993), 'Fundamentals of "
    "Statistical Signal Processing: Estimation Theory', Prentice Hall, "
    "§11. Hayes (1996), 'Statistical Digital Signal Processing and "
    "Modeling', Wiley, §7."
)


def op(
    signal,
    noise_psd,
    *,
    signal_psd: Optional[np.ndarray] = None,
    D: int = 8192,
):
    """Block / offline frequency-domain Wiener filter applied to ``signal``.

    Parameters
    ----------
    signal:
        1-D real noisy observation.
    noise_psd:
        Noise power spectral density (length ``= len(signal)``); estimated
        from a noise-only segment or supplied externally.
    signal_psd:
        Optional signal PSD; if None, estimated as ``max(|X|^2 - noise_psd,
        epsilon)``.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Real Wiener-filtered estimate of the clean signal.
    """
    sig = np.asarray(signal, dtype=np.float64)
    n_psd = np.asarray(noise_psd, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError(f"wiener expects 1-D signal; got {sig.shape}")
    if n_psd.shape != sig.shape:
        raise ValueError(
            f"noise_psd shape {n_psd.shape} != signal shape {sig.shape}"
        )
    X = np.fft.fft(sig)
    obs_psd = X.real ** 2 + X.imag ** 2  # |z|² = real²+imag² (no abs())
    if signal_psd is None:
        s_psd = np.maximum(obs_psd - n_psd, 1e-30)
    else:
        s_psd = np.asarray(signal_psd, dtype=np.float64)
        if s_psd.shape != sig.shape:
            raise ValueError(
                f"signal_psd shape {s_psd.shape} != signal shape {sig.shape}"
            )
    # Class N rational gain: H_W(k) = S_xx(k) / (S_xx(k) + S_nn(k))
    H = s_psd / np.maximum(s_psd + n_psd, 1e-30)
    return np.real(np.fft.ifft(H * X))
