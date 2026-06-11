"""Standard Model: electroweak unification, Higgs mechanism, Yukawa, CKM.

Per ``[[feedback_science_is_ssot_not_project]]``: canonical SSoT for each
operation is the SM literature. Numerical values (W/Z masses, mixing
angles, fermion masses) are NOT hardcoded — this module ships the
algebraic primitives that map (gauge couplings, Higgs vev, Yukawa
couplings) to observable masses. Experimental values are caller-supplied.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]``: SM
substrate-coupling operations on the SU(3)_c × SU(2)_L × U(1)_Y gauge
representation space. Dissolves into Class M (Lie-algebra binding) +
Class K (continuous projection-shadow) per the unified framework.

**Convention** (Peskin-Schroeder §20):

- Higgs potential: ``V(φ) = -μ² |φ|² + λ |φ|⁴`` (μ² > 0).
- Vacuum expectation value: ``v² = μ² / (2λ)``.
- W mass: ``M_W = g v / 2``.
- Z mass: ``M_Z = v √(g² + g'²) / 2``.
- Weinberg angle: ``tan θ_W = g' / g``; equivalently ``cos θ_W = M_W / M_Z``.
- Photon: massless (kept by U(1)_em residual symmetry).

Canonical SSoT:

- Glashow, S.L. (1961) *Nucl. Phys.* 22, 579-588.
- Weinberg, S. (1967) *Phys. Rev. Lett.* 19, 1264-1266.
- Salam, A. (1968) *Elementary Particle Theory* (Almqvist & Wiksell).
- Higgs, P.W. (1964) *Phys. Rev. Lett.* 13, 508-509;
  Englert, F. & Brout, R. (1964) *Phys. Rev. Lett.* 13, 321-323;
  Guralnik, G.S., Hagen, C.R. & Kibble, T.W.B. (1964) *Phys. Rev. Lett.*
  13, 585-587.
- Cabibbo, N. (1963) *Phys. Rev. Lett.* 10, 531-533.
- Kobayashi, M. & Maskawa, T. (1973) *Prog. Theor. Phys.* 49, 652-657.
- Peskin & Schroeder (1995) *Intro QFT*, Chs 20-21.
- Schwartz (2014) *QFT and the SM*, Chs 28-29.
"""

from __future__ import annotations

from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat

from srmech.amsc import rational as _srn


# ----------------------------------------------------------------------
# Higgs potential + vacuum expectation value
# ----------------------------------------------------------------------


def higgs_potential(phi: complex, mu_squared: float, lam: float) -> float:
    """Higgs potential ``V(φ) = -μ² |φ|² + λ |φ|⁴`` (mexican hat).

    For ``μ² > 0`` and ``λ > 0``, the potential has minima on the circle
    ``|φ| = sqrt(μ²/(2λ))`` and a local maximum at ``φ = 0``.

    Canonical SSoT: Higgs (1964) eq 4; Peskin-Schroeder §20.1 eq 20.6.

    Args:
        phi: Complex scalar field value.
        mu_squared: Mass-squared parameter ``μ²`` (positive).
        lam: Self-coupling ``λ`` (positive).

    Returns:
        ``V(φ)`` (real scalar).
    """
    if mu_squared <= 0:
        raise ValueError(f"higgs_potential: mu_squared must be > 0; got {mu_squared}")
    if lam <= 0:
        raise ValueError(f"higgs_potential: lam must be > 0; got {lam}")
    # |φ|² = real²+imag² (no abs()); value-identical for real (imag==0) and complex φ.
    phi_sq = phi.real ** 2 + phi.imag ** 2
    return -mu_squared * phi_sq + lam * phi_sq * phi_sq


def higgs_vev(mu_squared: float, lam: float) -> float:
    """Higgs vacuum expectation value ``v = sqrt(μ² / (2λ))``.

    Minimum of ``V(φ) = -μ² |φ|² + λ |φ|⁴`` occurs at
    ``d V / d |φ|² = 0`` ⇒ ``|φ|² = μ² / (2λ)``.

    Canonical SSoT: Peskin-Schroeder §20.1 eq 20.7.

    Args:
        mu_squared: Mass-squared parameter (positive).
        lam: Self-coupling (positive).

    Returns:
        Vacuum expectation value ``v > 0``.
    """
    if mu_squared <= 0:
        raise ValueError(f"higgs_vev: mu_squared must be > 0; got {mu_squared}")
    if lam <= 0:
        raise ValueError(f"higgs_vev: lam must be > 0; got {lam}")
    return _srn.sqrt(mu_squared / (2.0 * lam))


# ----------------------------------------------------------------------
# Electroweak: gauge boson masses + Weinberg angle
# ----------------------------------------------------------------------


def weak_mixing_angle(g: float, g_prime: float) -> float:
    """Weak (Weinberg) mixing angle ``θ_W = atan(g' / g)``.

    Canonical SSoT: Weinberg (1967) eq 8; Peskin-Schroeder §20.2 eq 20.31.

    Args:
        g: SU(2)_L gauge coupling.
        g_prime: U(1)_Y gauge coupling.

    Returns:
        ``θ_W`` in **radians** (the angle itself; NOT ``sin²θ_W`` and NOT
        degrees); ``tan θ_W = g'/g``. For the PDG ``sin²θ_W ≈ 0.231``
        convention, take ``math.sin(weak_mixing_angle(g, g_prime))**2``.
    """
    if g <= 0:
        raise ValueError(f"weak_mixing_angle: g must be > 0; got {g}")
    return _srn.atan2(g_prime, g)


def w_boson_mass(g: float, vev: float) -> float:
    """W boson mass ``M_W = g v / 2``.

    From spontaneous symmetry breaking of SU(2)_L × U(1)_Y → U(1)_em
    via the Higgs vev.

    Canonical SSoT: Peskin-Schroeder §20.2 eq 20.30.

    Args:
        g: SU(2)_L gauge coupling.
        vev: Higgs vacuum expectation value.

    Returns:
        W boson mass.
    """
    if g <= 0:
        raise ValueError(f"w_boson_mass: g must be > 0; got {g}")
    if vev <= 0:
        raise ValueError(f"w_boson_mass: vev must be > 0; got {vev}")
    return g * vev / 2.0


def z_boson_mass(g: float, g_prime: float, vev: float) -> float:
    """Z boson mass ``M_Z = v √(g² + g'²) / 2``.

    Canonical SSoT: Peskin-Schroeder §20.2 eq 20.32.

    Args:
        g: SU(2)_L gauge coupling.
        g_prime: U(1)_Y gauge coupling.
        vev: Higgs vacuum expectation value.

    Returns:
        Z boson mass.
    """
    if g <= 0 or g_prime <= 0 or vev <= 0:
        raise ValueError(
            f"z_boson_mass: g, g_prime, vev must all be > 0; got "
            f"g={g}, g_prime={g_prime}, vev={vev}"
        )
    return vev * _srn.sqrt(g * g + g_prime * g_prime) / 2.0


def weinberg_relation_residual(g: float, g_prime: float, vev: float) -> float:
    """Verify ``M_W = M_Z cos θ_W`` (Weinberg relation).

    Returns the absolute deviation ``|M_W - M_Z cos θ_W|``. Should be
    at machine precision because the relation is algebraically exact
    given the standard tree-level formulas.

    Canonical SSoT: Peskin-Schroeder §20.2 eq 20.33.
    """
    MW = w_boson_mass(g, vev)
    MZ = z_boson_mass(g, g_prime, vev)
    theta_W = weak_mixing_angle(g, g_prime)
    # Class-K magnitude via explicit sign-branch (no abs()); scalar real.
    _d = MW - MZ * _srn.cos(theta_W)
    return _d if _d >= 0.0 else -_d


def electroweak_summary(g: float, g_prime: float, vev: float) -> dict:
    """Bundle electroweak observables in one dict.

    Includes M_W, M_Z, θ_W, cos θ_W, sin θ_W, and the Weinberg-relation
    residual.

    Canonical SSoT: composite of Peskin-Schroeder §20.2 eq 20.30-33.
    """
    theta_W = weak_mixing_angle(g, g_prime)
    return {
        "M_W": w_boson_mass(g, vev),
        "M_Z": z_boson_mass(g, g_prime, vev),
        "theta_W_rad": theta_W,
        "cos_theta_W": _srn.cos(theta_W),
        "sin_theta_W": _srn.sin(theta_W),
        "weinberg_residual": weinberg_relation_residual(g, g_prime, vev),
    }


# ----------------------------------------------------------------------
# Yukawa couplings → fermion masses
# ----------------------------------------------------------------------


def fermion_mass_from_yukawa(yukawa: float, vev: float) -> float:
    """Fermion mass from Yukawa coupling: ``m_f = y_f v / √2``.

    Origin: Yukawa term ``L_Y = -y_f (ψ̄_L φ ψ_R + h.c.)`` becomes a Dirac
    mass term ``-(y_f v / √2) ψ̄ψ`` after spontaneous symmetry breaking.

    Canonical SSoT: Peskin-Schroeder §20.2 eq 20.27;
    Schwartz §29.1 eq 29.18.

    Args:
        yukawa: Yukawa coupling ``y_f``.
        vev: Higgs vacuum expectation value.

    Returns:
        Fermion (Dirac) mass.
    """
    if vev <= 0:
        raise ValueError(f"fermion_mass_from_yukawa: vev must be > 0; got {vev}")
    return yukawa * vev / _srn.sqrt(2.0)


# ----------------------------------------------------------------------
# Flavour: CKM matrix (standard parameterization)
# ----------------------------------------------------------------------


def ckm_matrix(
    theta_12: float,
    theta_13: float,
    theta_23: float,
    delta_cp: float = 0.0,
) -> "Mat":
    """CKM quark-mixing matrix (standard parameterization).

    Three Euler-like mixing angles plus one CP-violating phase. The matrix
    is ``V = U_23 U_13 U_12`` per the PDG / Chau-Keung convention::

        V = [[  c12 c13,                s12 c13,               s13 e^{-iδ} ],
             [ -s12 c23 - c12 s23 s13 e^{iδ},  c12 c23 - s12 s23 s13 e^{iδ},  s23 c13 ],
             [  s12 s23 - c12 c23 s13 e^{iδ}, -c12 s23 - s12 c23 s13 e^{iδ},  c23 c13 ]]

    where ``c_ij = cos θ_ij``, ``s_ij = sin θ_ij``. Result is unitary.

    Canonical SSoT: Cabibbo (1963); Kobayashi & Maskawa (1973);
    Chau, L.-L. & Keung, W.-Y. (1984) *Phys. Rev. Lett.* 53, 1802;
    Particle Data Group review *§12.1*.

    Args:
        theta_12: ``θ_12`` (Cabibbo angle, 12-mixing).
        theta_13: ``θ_13`` (1-3 mixing).
        theta_23: ``θ_23`` (2-3 mixing).
        delta_cp: CP-violating phase (radians).

    Returns:
        3×3 complex unitary matrix.
    """
    c12, s12 = _srn.cos(theta_12), _srn.sin(theta_12)
    c13, s13 = _srn.cos(theta_13), _srn.sin(theta_13)
    c23, s23 = _srn.cos(theta_23), _srn.sin(theta_23)
    phase = _srn.cexp(delta_cp)        # e^{iδ} scalar Euler cascade (Class-N)
    inv_phase = _srn.cexp(-delta_cp)   # e^{-iδ}
    # numpy-FREE entrywise build of exact Class-N scalar cascades, wrapped in
    # the numpy-free Mat carrier (v0.7.5rc116, #564).
    return Mat.from_rows([
        [
            c12 * c13,
            s12 * c13,
            s13 * inv_phase,
        ],
        [
            -s12 * c23 - c12 * s23 * s13 * phase,
            c12 * c23 - s12 * s23 * s13 * phase,
            s23 * c13,
        ],
        [
            s12 * s23 - c12 * c23 * s13 * phase,
            -c12 * s23 - s12 * c23 * s13 * phase,
            c23 * c13,
        ],
    ], is_complex=True)


def ckm_unitarity_residual(V: "Mat") -> float:
    """Frobenius norm of ``V V† - I`` — should be at machine precision.

    numpy-FREE (v0.7.5rc116): ``V·Vᴴ`` via the native ``mat_matmul``, the
    entrywise ``− I`` as a plain ``Mat``-entry subtraction, and the Frobenius
    norm via the rc114 Class-N ``mat_norm`` (no numpy).

    Canonical SSoT: PDG review §12.1.
    """
    vvh = mat_matmul(V, V.conj().T)
    n = vvh.n_rows
    diff = [
        vvh[i, j] - (1.0 if i == j else 0.0)
        for i in range(n)
        for j in range(vvh.n_cols)
    ]
    return mat_norm(diff)


__all__ = [
    "ckm_matrix",
    "ckm_unitarity_residual",
    "electroweak_summary",
    "fermion_mass_from_yukawa",
    "higgs_potential",
    "higgs_vev",
    "w_boson_mass",
    "weak_mixing_angle",
    "weinberg_relation_residual",
    "z_boson_mass",
]
