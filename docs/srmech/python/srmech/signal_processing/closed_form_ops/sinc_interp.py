"""Path A sinc interpolation — closed-form Whittaker-Shannon band-limit interpolation.

Identity per the implementation plan §1: sinc interpolation IS a Class L
(band-limit Laplacian eigenbasis: ideal low-pass filter with cutoff at
Nyquist) ∘ Class K (band-limit pin-slot threshold) composition. The classical
Whittaker-Shannon formula reconstructs a band-limited signal at arbitrary
time-offsets via a sum of shifted sinc kernels.

numpy-free (carrier-removal #564, rc93): the sinc kernel uses the substrate-
native ``_sinc`` (sin(πx)/(πx), Class-N rational cascade over the **Class-N π
cascade** ``_PI``, Spike #32; the x=0 removable singularity is a Class-K branch
returning 1.0, no division, no ``abs()``). The complex Whittaker-Shannon matvec
``out[q] = Σ_s sinc((t_q−t_s)/T)·y[s]`` is an inline nested sum over plain
``list``s — NOT via ``dense_matvec_complex`` (which is numpy-carrier INTERNALLY,
the rc70 "runnable ≠ loadable" trap). numpy is no longer imported.

Path B dual in Phase 6 (Path B band-limit bundle).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Whittaker
(1915) + Shannon (1949) + Oppenheim & Schafer (2010, 3rd ed.) §4.1.
"""

from __future__ import annotations

from typing import List

from srmech.amsc import rational as _srn

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

# Class-N π cascade (Archimedes hexagon-doubling, Spike #32) — the substrate-
# native π source for the sinc kernel; NOT math.pi / np.pi.
_PI = float(_srn.pi_cascade_digits(30))


def _sinc(x: float) -> float:
    """Normalised sinc ``sin(πx)/(πx)`` matching ``np.sinc``, numpy-free.

    Routes through ``rational.sin`` over the Class-N ``_PI`` source. The
    removable singularity at ``x == 0`` is a Class-K branch (returns ``1.0``,
    no division), so there is no ``abs()`` and no divide-by-zero.
    """
    if x == 0.0:
        return 1.0
    px = _PI * x
    return _srn.sin(px) / px


def _median(values: List[float]) -> float:
    """Median of a list (matches ``numpy.median``: mean of the two middle
    elements for even length)."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


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
    list of complex (or a single complex for a scalar ``target_indices``)
        Interpolated values at ``target_indices``.
    """
    sig_seq = list(signal)
    if sig_seq and hasattr(sig_seq[0], "__len__") and not isinstance(
        sig_seq[0], (str, bytes)
    ):
        raise ValueError("sinc_interp expects 1-D signal and sample_indices")
    y = [complex(v) for v in sig_seq]
    ts_seq = list(sample_indices)
    if ts_seq and hasattr(ts_seq[0], "__len__") and not isinstance(
        ts_seq[0], (str, bytes)
    ):
        raise ValueError("sinc_interp expects 1-D signal and sample_indices")
    t_s = [float(v) for v in ts_seq]
    if len(y) != len(t_s):
        raise ValueError(
            f"signal length {len(y)} != sample_indices length {len(t_s)}"
        )
    # Estimate sample spacing (median of consecutive differences).
    if len(t_s) >= 2:
        T = _median([t_s[i + 1] - t_s[i] for i in range(len(t_s) - 1)])
    else:
        T = 1.0
    # A scalar target (python/numpy scalar) has no __len__.
    tq_is_scalar = not hasattr(target_indices, "__len__")
    if tq_is_scalar:
        t_q = [float(target_indices)]
    else:
        t_q = [float(v) for v in target_indices]
    # Complex Whittaker-Shannon matvec: out[q] = Σ_s sinc((t_q−t_s)/T)·y[s].
    out = []
    for tq in t_q:
        acc = 0j
        for s in range(len(t_s)):
            acc += _sinc((tq - t_s[s]) / T) * y[s]
        out.append(acc)
    if tq_is_scalar:
        return out[0]
    return out
