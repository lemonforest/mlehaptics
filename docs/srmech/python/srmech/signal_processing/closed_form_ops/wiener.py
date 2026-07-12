"""Path A Wiener filter — closed-form block / offline frequency-domain Wiener.

Identity per the implementation plan §1: Wiener IS a Class L (Laplacian
eigenbasis on the power-spectrum substrate) ∘ Class N (rational MMSE gain
``S_xx / (S_xx + S_nn)``) composition. The closed-form block / offline
estimator computes the rational gain per frequency bin from the signal
and noise PSDs and applies it via FFT.

Path B dual in Phase 4 (Wiener via bundled eigenvalue handles).

Carrier-free since v0.7.5rc87 (#564): plain Python ``list`` carriers; ``_sc.fft``
/ ``_sc.ifft`` already return ``List[complex]``; the per-bin power, the
``np.maximum(..., eps)`` floors and the Class-N rational gain are explicit
elementwise list comprehensions, ``|X|² = X.real² + X.imag²`` (no ``abs()``).

rc150 (B4c) classification: ``composition_of_c``.  The two heavy numeric kernels
are the forward + inverse transform, and both funnel through ``_sc.fft`` /
``_sc.ifft`` — which dispatch their FLOAT path to the c_dispatched numeric FFT
foundation ``srmech_fft_c128`` (rc139) and fall back to the complete pure ``cexp``
cascade when the native lib is absent (the SAME composition_of_c pattern as the
rc139 fft/ifft wrappers + the B4a stft/cross_spectral windowed-transform ops).
The per-bin power ``|X|²=re²+im²``, the Class-L eps-floor ``max(·, eps)`` and the
Class-N rational MMSE gain ``S_xx/(S_xx+S_nn)`` are numpy-free elementwise glue
(no ``abs()``).  NUMERIC (within-tol, not byte-identical): native == pure to
reldiff ≤ 1e-9 (the FFT butterflies may FMA-fuse ~1 ULP on some platforms).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Wiener
(1949) + Kay (1993) §11 + Hayes (1996) §7.
"""

from __future__ import annotations

from srmech.amsc.cascade import spectral_cascades as _sc

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
    signal_psd=None,
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
    list
        Real Wiener-filtered estimate of the clean signal (``list`` of
        ``float``, length ``len(signal)``).
    """
    rows = list(signal)
    if rows and hasattr(rows[0], "__len__"):
        raise ValueError(f"wiener expects 1-D signal; got {len(rows)} rows")
    sig = [float(v) for v in rows]
    n_psd = [float(v) for v in noise_psd]
    n = len(sig)
    if len(n_psd) != n:
        raise ValueError(f"noise_psd length {len(n_psd)} != signal length {n}")
    X = list(_sc.fft(sig))
    # |z|² = real²+imag² (no abs())
    obs_psd = [x.real * x.real + x.imag * x.imag for x in X]
    if signal_psd is None:
        # Class-L floor (np.maximum with the eps scalar) per bin.
        s_psd = [max(obs_psd[k] - n_psd[k], 1e-30) for k in range(n)]
    else:
        s_psd = [float(v) for v in signal_psd]
        if len(s_psd) != n:
            raise ValueError(f"signal_psd length {len(s_psd)} != signal length {n}")
    # Class N rational gain: H_W(k) = S_xx(k) / (S_xx(k) + S_nn(k))
    H = [s_psd[k] / max(s_psd[k] + n_psd[k], 1e-30) for k in range(n)]
    filtered = _sc.ifft([H[k] * X[k] for k in range(n)])
    return [v.real for v in filtered]
