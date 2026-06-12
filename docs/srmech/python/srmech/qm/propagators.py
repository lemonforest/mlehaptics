"""Feynman propagators (scalar / fermion / photon / massive vector).

Per ``[[feedback_science_is_ssot_not_project]]``: each propagator cites
canonical QFT literature.

numpy-FREE (v0.7.5rc123, #564): the 4×4 propagator numerators are held in
the framework-native :class:`~srmech.amsc.mat.Mat` carrier (consumed straight
from the numpy-free :mod:`srmech.qm.relativistic` producers ``minkowski_metric``
/ ``dirac_operator_momentum_space``), the ``k^μ k^ν`` outer product routes
through the Class-L :func:`~srmech.amsc.laplacian.mat_matmul` (column·row), the
scalar Minkowski contraction ``k² = kᵀ η k`` is a numpy-free double-sum fold,
and the ``+iε`` regulator + scalar propagator are plain Python ``complex`` —
**no numpy**. 4-momenta are plain Python sequences of floats.

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

from typing import Optional, Sequence

from srmech.amsc.laplacian import mat_matmul
from srmech.amsc.mat import Mat
from srmech.qm.relativistic import (
    dirac_operator_momentum_space,
    four_momentum_squared,
    minkowski_metric,
)


# ----------------------------------------------------------------------
# numpy-free Mat helpers
# ----------------------------------------------------------------------


def _scale(s, m: "Mat") -> "Mat":
    """``s · M`` (scalar × ``Mat``) as a new complex ``Mat`` (numpy-free)."""
    rows = [[s * m[i, j] for j in range(m.n_cols)] for i in range(m.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


def _mat_sub(a: "Mat", b: "Mat") -> "Mat":
    """``A − B`` element-wise as a new complex ``Mat`` (numpy-free)."""
    rows = [[a[i, j] - b[i, j] for j in range(a.n_cols)] for i in range(a.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


def _outer(u: Sequence[float], v: Sequence[float]) -> "Mat":
    """``u v^T`` (outer product) as a 4×4 complex ``Mat`` via the column·row
    Class-L :func:`mat_matmul` cascade (the numpy-free outer-product replacement;
    ``Mat`` is 2-D only so the vectors arrive as plain float lists)."""
    col = Mat.from_rows([[complex(x)] for x in u], is_complex=True)   # (n, 1)
    row = Mat.from_rows([[complex(x) for x in v]], is_complex=True)   # (1, n)
    return mat_matmul(col, row)


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
    k: Sequence[float], m: float, epsilon: float = 0.0
) -> "Mat":
    """Dirac fermion Feynman propagator ``S_F(k) = i (γ^μ k_μ + m) / (k² - m² + iε)``.

    Returns a 4×4 complex ``Mat``. On-shell pole at ``k² = m²``.

    Canonical SSoT: Peskin-Schroeder §4.7 eq 4.107 + 4.111;
    Bjorken-Drell §5.4; Schwartz §6.3.

    Args:
        k: 4-momentum ``(k_0, k_1, k_2, k_3)`` as a length-4 sequence of floats.
        m: Fermion mass.
        epsilon: iε regulator.

    Returns:
        ``S_F(k)`` as a 4×4 complex ``Mat``.
    """
    k = [float(x) for x in k]
    if len(k) != 4:
        raise ValueError(
            f"feynman_fermion_propagator: k must be 4-vector; got length {len(k)}"
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
    # relativistic.* return numpy-free `Mat` (rc118) — consume directly. The
    # Dirac operator dirac_operator_momentum_space(k, -m) = γ^μ k_μ - (-m) I
    # = γ^μ k_μ + m I is exactly the fermion-propagator numerator.
    numerator = dirac_operator_momentum_space(k, -m)  # γ^μ k_μ + m I (Mat)
    return _scale(1j / denom, numerator)


def feynman_photon_propagator(
    k_squared: float, gauge_xi: float = 0.0, epsilon: float = 0.0,
    k: Optional[Sequence[float]] = None
) -> "Mat":
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
            ``k^μ k^ν``). Optional, a length-4 sequence of floats.

    Returns:
        ``D^{μν}(k)`` as a 4×4 complex ``Mat``.
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
    # g^{μν} (raised-index Minkowski metric). With mostly-minus, η^{μν} = η_{μν}.
    # minkowski_metric() is a numpy-free real Mat (rc118) — consume directly.
    g_upper = minkowski_metric()
    base = _scale(-1j / denom, g_upper)            # -i g^{μν} / (k² + iε)
    if gauge_xi == 0.0 or k is None:
        return base
    k = [float(x) for x in k]
    if len(k) != 4:
        raise ValueError(
            f"feynman_photon_propagator: k must be 4-vector for non-Feynman "
            f"gauge; got length {len(k)}"
        )
    kk = _outer(k, k)                              # k^μ k^ν (Class-L column·row)
    gauge_coeff = -1j * (1.0 - gauge_xi) / (denom * complex(k_squared, epsilon))
    gauge_term = _scale(gauge_coeff, kk)
    return _mat_sub(base, gauge_term)


def feynman_massive_vector_propagator(
    k: Sequence[float], m: float, epsilon: float = 0.0
) -> "Mat":
    """Massive vector (e.g. W, Z) Feynman propagator in unitary gauge.

    Mostly-minus metric::

        D^{μν}(k) = -i (g^{μν} - k^μ k^ν / m²) / (k² - m² + iε)

    Canonical SSoT: Peskin-Schroeder §20.1 eq 20.13;
    Weinberg Vol II §21.1 eq 21.1.21; Schwartz §28.

    Args:
        k: 4-momentum as a length-4 sequence of floats.
        m: Vector boson mass (must be > 0).
        epsilon: iε regulator.

    Returns:
        ``D^{μν}(k)`` as a 4×4 complex ``Mat``.
    """
    k = [float(x) for x in k]
    if len(k) != 4:
        raise ValueError(
            f"feynman_massive_vector_propagator: k must be 4-vector; got length {len(k)}"
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
    # numerator = g^{μν} - k^μ k^ν / m²  (both numpy-free Mat).
    g_upper = minkowski_metric()
    kk = _outer(k, k)                              # k^μ k^ν (Class-L column·row)
    numerator = _mat_sub(g_upper, _scale(1.0 / (m * m), kk))
    return _scale(-1j / denom, numerator)


__all__ = [
    "feynman_fermion_propagator",
    "feynman_massive_vector_propagator",
    "feynman_photon_propagator",
    "feynman_scalar_propagator",
]
