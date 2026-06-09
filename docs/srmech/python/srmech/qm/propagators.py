"""Feynman propagators (scalar / fermion / photon / massive vector).

Per ``[[feedback_science_is_ssot_not_project]]``: each propagator cites
canonical QFT literature.

**Metric convention**: mostly-minus ``η^{μν} = diag(+1, -1, -1, -1)``
(Peskin-Schroeder). On-shell pole at ``k² = m²``.

**iε prescription**: Feynman propagators carry a ``+iε`` in the
denominator to select the time-ordered Green's function from the path
integral. Numerically, ``epsilon`` parameter sets the regulator;
default ``epsilon = 0.0`` gives the principal-value form for off-shell
momenta. On-shell momenta require ``epsilon > 0`` to avoid division by
zero.

Per Spike #24 + ``[[user_stance_kepler_shape_universal]]``: a propagator
``1 / (k² - m²)`` is a Class K (equation-of-centre / pin-slot) sub-operation
when viewed as a continuous projection from the integer-cyclic upstream
(``k`` on a momentum-space lattice). The lattice scalar propagator
``G(k) = 1 / (m² + k̂²)`` of `notes/spike_24_*` is the same shape;
this module ships the continuum form.

Canonical SSoT:

- Feynman, R.P. (1949) *Phys. Rev.* 76, 749-759 (positron theory).
- Dyson, F.J. (1949) *Phys. Rev.* 75, 486-502.
- Peskin & Schroeder (1995) *Intro QFT*, Chs 4, 9, 10.
- Schwartz, M.D. (2014) *Quantum Field Theory and the Standard Model*,
  Cambridge. Chs 6-8.
- Weinberg (1995) *Quantum Theory of Fields* Vol. I, Ch. 6.
"""

from __future__ import annotations

import numpy as np
from typing import Optional

from srmech.amsc.laplacian import dense_matvec_real
from srmech.qm.relativistic import (
    dirac_operator_momentum_space,
    four_momentum_squared,
    minkowski_metric,
)


def _denominator(k_squared: float, m: float, epsilon: float) -> complex:
    """``k² - m² + iε`` with safe handling of on-shell points."""
    return complex(k_squared - m * m, epsilon)


def feynman_scalar_propagator(
    k_squared: float, m: float, epsilon: float = 0.0
) -> complex:
    """Scalar Feynman propagator ``G_F(k) = i / (k² - m² + iε)``.

    Mostly-minus metric; on-shell pole at ``k² = m²``.

    Canonical SSoT: Peskin-Schroeder §4.2 eq 4.42; Schwartz §6.2.

    Args:
        k_squared: ``k² = k_μ k^μ`` (Lorentz-invariant).
        m: Scalar field mass.
        epsilon: iε regulator (default 0 — off-shell only).

    Returns:
        Complex propagator value.

    Raises:
        ValueError: on-shell point with ``epsilon == 0``.
    """
    if m < 0:
        raise ValueError(f"feynman_scalar_propagator: m must be ≥ 0; got {m}")
    if epsilon < 0:
        raise ValueError(
            f"feynman_scalar_propagator: epsilon must be ≥ 0; got {epsilon}"
        )
    denom = _denominator(k_squared, m, epsilon)
    if denom == 0:
        raise ValueError(
            f"feynman_scalar_propagator: on-shell pole at k² = m² = {m*m}; "
            "set epsilon > 0 for the iε prescription"
        )
    return 1j / denom


def feynman_fermion_propagator(
    k: np.ndarray, m: float, epsilon: float = 0.0
) -> np.ndarray:
    """Dirac fermion Feynman propagator ``S_F(k) = i (γ^μ k_μ + m) / (k² - m² + iε)``.

    Returns a 4×4 complex matrix. On-shell pole at ``k² = m²``.

    Canonical SSoT: Peskin-Schroeder §4.7 eq 4.107 + 4.111;
    Bjorken-Drell §5.4; Schwartz §6.3.

    Args:
        k: 4-momentum ``(k_0, k_1, k_2, k_3)``.
        m: Fermion mass.
        epsilon: iε regulator.

    Returns:
        ``S_F(k)`` as a 4×4 complex matrix.
    """
    k = np.asarray(k, dtype=float)
    if k.shape != (4,):
        raise ValueError(
            f"feynman_fermion_propagator: k must be 4-vector; got {k.shape}"
        )
    if m < 0:
        raise ValueError(f"feynman_fermion_propagator: m must be ≥ 0; got {m}")
    if epsilon < 0:
        raise ValueError(
            f"feynman_fermion_propagator: epsilon must be ≥ 0; got {epsilon}"
        )
    k_squared = four_momentum_squared(k)
    denom = _denominator(k_squared, m, epsilon)
    if denom == 0:
        raise ValueError(
            f"feynman_fermion_propagator: on-shell pole at k² = m² = {m*m}; "
            "set epsilon > 0 for the iε prescription"
        )
    numerator = dirac_operator_momentum_space(k, -m)  # γ^μ k_μ + m
    return 1j * numerator / denom


def feynman_photon_propagator(
    k_squared: float, gauge_xi: float = 0.0, epsilon: float = 0.0,
    k: Optional[np.ndarray] = None
) -> np.ndarray:
    """Photon (massless gauge boson) Feynman propagator.

    In Feynman gauge (``gauge_xi = 1``)::

        D^{μν}(k) = -i g^{μν} / (k² + iε)

    In general covariant gauge (``ξ`` arbitrary)::

        D^{μν}(k) = -i [g^{μν} - (1 - ξ) k^μ k^ν / k²] / (k² + iε)

    Note: ``ξ = 0`` is Landau gauge (transverse); ``ξ = 1`` is Feynman
    gauge (most common). Default ``gauge_xi = 0`` here selects Feynman
    gauge for simplicity (only ``-i g^{μν} / k²`` term).

    Canonical SSoT: Peskin-Schroeder §4.8 eq 4.118-4.121 + §16.6;
    Schwartz §8.4.

    Args:
        k_squared: ``k² = k_μ k^μ``.
        gauge_xi: Covariant gauge parameter. 0 = Feynman gauge (default);
            for non-Feynman gauge pass both ``gauge_xi`` and ``k``.
        epsilon: iε regulator.
        k: Full 4-momentum (needed for non-Feynman gauge to compute
            ``k^μ k^ν``). Optional.

    Returns:
        ``D^{μν}(k)`` as a 4×4 complex matrix.
    """
    if epsilon < 0:
        raise ValueError(
            f"feynman_photon_propagator: epsilon must be ≥ 0; got {epsilon}"
        )
    denom = complex(k_squared, epsilon)
    if denom == 0:
        raise ValueError(
            "feynman_photon_propagator: on-shell pole at k² = 0; "
            "set epsilon > 0 for the iε prescription"
        )
    eta = minkowski_metric()
    # g^{μν} (raised-index Minkowski metric). With mostly-minus, η^{μν} = η_{μν}.
    g_upper = eta
    base = -1j * g_upper / denom
    if gauge_xi == 0.0 or k is None:
        return base
    k = np.asarray(k, dtype=float)
    if k.shape != (4,):
        raise ValueError(
            f"feynman_photon_propagator: k must be 4-vector for non-Feynman "
            f"gauge; got {k.shape}"
        )
    k_lower = dense_matvec_real(eta, k)  # real 4×4 metric times real 4-vector
    kk = np.outer(k, k)  # k^μ k^ν
    gauge_term = -1j * (1.0 - gauge_xi) * kk / (denom * complex(k_squared, epsilon))
    return base - gauge_term


def feynman_massive_vector_propagator(
    k: np.ndarray, m: float, epsilon: float = 0.0
) -> np.ndarray:
    """Massive vector (e.g. W, Z) Feynman propagator in unitary gauge.

    Mostly-minus metric::

        D^{μν}(k) = -i (g^{μν} - k^μ k^ν / m²) / (k² - m² + iε)

    Canonical SSoT: Peskin-Schroeder §20.1 eq 20.13;
    Weinberg Vol II §21.1 eq 21.1.21; Schwartz §28.

    Args:
        k: 4-momentum.
        m: Vector boson mass (must be > 0).
        epsilon: iε regulator.

    Returns:
        ``D^{μν}(k)`` as a 4×4 complex matrix.
    """
    k = np.asarray(k, dtype=float)
    if k.shape != (4,):
        raise ValueError(
            f"feynman_massive_vector_propagator: k must be 4-vector; got {k.shape}"
        )
    if m <= 0:
        raise ValueError(
            f"feynman_massive_vector_propagator: m must be > 0; got {m}"
        )
    if epsilon < 0:
        raise ValueError(
            f"feynman_massive_vector_propagator: epsilon must be ≥ 0; got {epsilon}"
        )
    k_squared = four_momentum_squared(k)
    denom = _denominator(k_squared, m, epsilon)
    if denom == 0:
        raise ValueError(
            f"feynman_massive_vector_propagator: on-shell pole at k² = m² = {m*m}; "
            "set epsilon > 0 for the iε prescription"
        )
    eta = minkowski_metric()
    kk = np.outer(k, k)
    numerator = eta - kk / (m * m)
    return -1j * numerator / denom


__all__ = [
    "feynman_fermion_propagator",
    "feynman_massive_vector_propagator",
    "feynman_photon_propagator",
    "feynman_scalar_propagator",
]
