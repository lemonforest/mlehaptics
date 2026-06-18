"""Path A spectral subtraction — closed-form denoising via PSD subtraction with floor.

Identity per the implementation plan §1: spectral subtraction IS a Class L
(FFT-domain elementwise PSD operation) ∘ Class N (rational floor / over-
subtraction factor) composition. The closed-form reference applies
``|Y|^2 = max(|X|^2 - alpha * noise_psd, beta * noise_psd)``.

Path B dual in Phase 6 (Path B floor in bound-vector pipeline).

Carrier-free since v0.7.5rc90 (#564): plain Python ``list`` carriers. The
``np.maximum`` Class-N floor becomes the builtin ``max`` per bin; ``np.angle``
(libm ``atan2``) routes through **``rational.atan2``** (bit-exact to libm for
the phase domain), and the phasor / magnitude — previously the numpy-carrier
``elementwise_transcendental(phase, "exp_i")`` + ``elementwise_sqrt`` helpers —
are inlined per-bin as ``rational.{sqrt,cos,sin}`` so the op runs with numpy
genuinely ABSENT (the helpers stay numpy-carrier internally, so they cannot be
called numpy-free). ``_sc.fft``/``_sc.ifft`` already return ``List[complex]``.
Value-faithful to the pre-change output to machine eps (the rational cascades
match libm ``atan2``/``cos``/``sin`` and ``sqrt`` to ≤1 ULP).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Boll (1979)
+ Berouti, Schwartz & Makhoul (1979).
"""

from __future__ import annotations

from typing import List

from srmech.amsc import rational as _srn
from srmech.amsc.cascade import spectral_cascades as _sc

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
) -> List[float]:
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
    list
        Real denoised signal as a ``list`` of ``float``.
    """
    sig = list(signal)
    if sig and hasattr(sig[0], "__len__") and not isinstance(sig[0], (str, bytes)):
        raise ValueError("spectral_subtraction expects 1-D signal")
    sig = [float(v) for v in sig]
    n_psd = [float(v) for v in noise_psd]
    if len(n_psd) != len(sig):
        raise ValueError(
            f"noise_psd length {len(n_psd)} != signal length {len(sig)}"
        )
    X = list(_sc.fft(sig))
    n = len(X)
    Y = [complex(0)] * n
    for k in range(n):
        re = X[k].real
        im = X[k].imag
        obs_psd = re * re + im * im  # |z|² = real²+imag² (no abs())
        # Class N rational floor: max(|X|^2 - alpha*N, beta*N).
        new_psd = max(obs_psd - alpha * n_psd[k], beta * n_psd[k])
        # New magnitude from new_psd; phase preserved from X (= np.angle(X)).
        mag = _srn.sqrt(new_psd)
        phase = _srn.atan2(im, re)
        Y[k] = complex(mag * _srn.cos(phase), mag * _srn.sin(phase))
    return [v.real for v in _sc.ifft(Y)]
