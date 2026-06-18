"""Path B Wiener filter — Class L Laplacian-eigenbasis ∘ Class N rational gain.

Identity per the implementation plan §1 + Spike #178 §1: Wiener filtering
IS a Class L (Laplacian eigenbasis on the power-spectrum substrate) ∘
Class N (rational MMSE gain ``S_xx / (S_xx + S_nn)``) composition. The
Path B-native form operates on the cyclic-graph Laplacian (which for the
cyclic substrate has FFT basis as eigenbasis per Chung 1997 §1.4) with
Class N rational gain applied per eigenmode.

Path A dual: :func:`srmech.signal_processing.closed_form_ops.wiener.op`
(closed-form ``g(λ) = λ_s / (λ_s + λ_n)`` per Kay 1993 §11). Both paths
IS the same algebra per
``[[user_stance_identity_not_implementation_discipline]]``; D1 algebra-
identity holds bit-exact for the FFT eigenbasis (where cyclic-graph
Laplacian eigenbasis IS the FFT basis).

The Class L identification uses the **cyclic-graph Laplacian**: for a
cyclic substrate of length N, the graph Laplacian ``L = 2I - S - S^{-1}``
(where S is the cyclic shift) has eigenvectors equal to the columns of
the inverse-DFT matrix; eigenvalues are ``λ_k = 2 - 2cos(2πk/N) = 4
sin^2(πk/N)``. Operating in the eigenbasis is operating in the FFT
spectral domain.

The Class N rational gain ``H(λ_k) = S_xx(k) / (S_xx(k) + S_nn(k))`` is
applied per eigenmode; per Spike #24 bonus 9 (cascade lives on circles)
and Class N rational algebra, the gain composition preserves the cyclic-
group structure of the substrate.

Trauma-informed defensive scope: methodology-research / educational
framing only.

Canonical SSoT
--------------
- Wiener (1949), *Extrapolation, Interpolation, and Smoothing of
  Stationary Time Series*, MIT Press.
- Kay (1993), *Fundamentals of Statistical Signal Processing:
  Estimation Theory*, Prentice Hall, §11. SSoT for the closed-form
  rational gain.
- Hayes (1996), *Statistical Digital Signal Processing and Modeling*,
  Wiley, §7.
- Chung (1997), *Spectral Graph Theory*, AMS — cyclic-graph Laplacian
  eigenbasis IS the FFT basis (§1.4).
- Plate (1995) IEEE TNN 6, 623.
"""

from __future__ import annotations

from srmech.amsc.cascade import spectral_cascades as _sc

OPERATION_NAME = "wiener"
CLASS_COMPOSITION = ("L", "N", "M")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Wiener (1949), 'Extrapolation, Interpolation, and Smoothing of "
    "Stationary Time Series', MIT Press. Kay (1993), §11 'Fundamentals "
    "of Statistical Signal Processing: Estimation Theory', Prentice "
    "Hall (SSoT for closed-form rational gain). Hayes (1996), §7. "
    "Chung (1997), *Spectral Graph Theory*, AMS (cyclic-graph Laplacian "
    "eigenbasis IS the FFT basis)."
)


def op(
    signal,
    noise_psd,
    *,
    signal_psd=None,
    D: int = 8192,
    substrate: str = "cyclic",
):
    """Path B Wiener filter via Class L eigenbasis + Class N rational gain.

    The Path B-native composition operates in the cyclic-graph Laplacian
    eigenbasis (which IS the FFT basis per Chung 1997 §1.4) and applies
    the Class N rational MMSE gain ``H(λ_k) = S_xx(k) / (S_xx(k) + S_nn(k))``
    per eigenmode. The result is mapped back via inverse FFT.

    D1 algebra-identical to the Path A reference per
    ``[[user_stance_identity_not_implementation_discipline]]``; both
    compute the same closed-form Wiener output (the Path B identity
    surfaces the Class L / Class N decomposition that the Path A
    formula instantiates implicitly).

    Parameters
    ----------
    signal:
        1-D real noisy observation.
    noise_psd:
        Noise power spectral density (length ``= len(signal)``).
    signal_psd:
        Optional signal PSD; if None, estimated as ``max(|X|^2 -
        noise_psd, epsilon)``.
    D:
        Path B dimensionality hint (default 8192).
    substrate:
        Substrate label hint. ``"cyclic"`` is the natural Class L
        substrate where the graph Laplacian eigenbasis IS the FFT
        basis.

    Returns
    -------
    list
        Real Wiener-filtered estimate of the clean signal (``list`` of
        ``float``, length ``len(signal)``). Numpy-free (#564), D1 algebra-
        identical to
        :func:`srmech.signal_processing.closed_form_ops.wiener.op`.
    """
    rows = list(signal)
    if rows and hasattr(rows[0], "__len__"):
        raise ValueError(f"wiener expects 1-D signal; got {len(rows)} rows")
    sig = [float(v) for v in rows]
    n_psd = [float(v) for v in noise_psd]
    n = len(sig)
    if len(n_psd) != n:
        raise ValueError(f"noise_psd length {len(n_psd)} != signal length {n}")
    # Class L: transform to cyclic-graph Laplacian eigenbasis (== FFT basis).
    # _sc.fft already returns List[complex] numpy-free.
    X = list(_sc.fft(sig))
    obs_psd = [x.real * x.real + x.imag * x.imag for x in X]  # |z|²=real²+imag² (no abs())
    if signal_psd is None:
        # Class-L floor (np.maximum with the eps scalar) per bin.
        s_psd = [max(obs_psd[k] - n_psd[k], 1e-30) for k in range(n)]
    else:
        s_psd = [float(v) for v in signal_psd]
        if len(s_psd) != n:
            raise ValueError(f"signal_psd length {len(s_psd)} != signal length {n}")
    # Class N rational gain per eigenmode:
    # H(lambda_k) = S_xx(k) / (S_xx(k) + S_nn(k)).
    # This IS the Class N rational MMSE algebra per Kay 1993 §11.
    H = [s_psd[k] / max(s_psd[k] + n_psd[k], 1e-30) for k in range(n)]
    # Class M bind on the spectrum (elementwise multiplication is the
    # cyclic-substrate Class M bind dual via convolution theorem).
    # Inverse Class L: map back from eigenbasis to sample domain.
    filtered = _sc.ifft([H[k] * X[k] for k in range(n)])
    return [v.real for v in filtered]


def _register() -> None:
    """Register Path B Wiener filter with the dispatcher's path_registry."""
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    from srmech.signal_processing.closed_form_ops.wiener import (
        op as path_a_wiener,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_wiener,
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
