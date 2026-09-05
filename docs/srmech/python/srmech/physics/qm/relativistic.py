"""Relativistic QM: Dirac γ-matrix algebra + Klein-Gordon + Weyl + Majorana.

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites
canonical relativistic QM / QFT literature.

numpy-FREE (v0.7.5rc118, #564): the γ-matrices and derived 4×4 operators are
held in the framework-native :class:`~srmech.math.mat.Mat` carrier (assembled
from the numpy-free Pauli 2×2 ``Mat`` blocks), every matrix product routes
through the Class-L :func:`~srmech.math.laplacian.mat_matmul`, residual norms
through :func:`~srmech.math.laplacian.mat_norm`, and the Klein-Gordon
dispersion through the Class-N :func:`srmech.math.rational.sqrt` — **no numpy**.
4-momenta are plain Python sequences of floats.

Metric convention: **mostly-minus** ``η^{μν} = diag(+1, -1, -1, -1)``
(Peskin-Schroeder convention; the standard QFT-side choice).

γ-matrix representation: **Dirac (standard) basis** per Peskin-Schroeder
eq A.18. Other representations (Weyl/chiral, Majorana) derivable from this
via similarity transformations; the Dirac basis is the most common
textbook starting point.

Per ``[[user_stance_1d_collapse_to_loe_identity_not_action]]`` + the
Spike #24 14-class vocabulary: γ-matrices are a **Class M Clifford
binding** primitive — they bind the Dirac spinor space ``ℂ^4`` into
Lorentz-covariant form. Cl(1,3) Clifford algebra: ``{γ^μ, γ^ν} = 2 η^{μν} I_4``.

Canonical SSoT:

- Dirac, P.A.M. (1928) *Proc. Roy. Soc. A* 117, 610-624; 118, 351-361.
- Klein, O. (1926) *Zeitschrift für Physik* 37, 895-906;
  Gordon, W. (1926) *Zeitschrift für Physik* 40, 117-133.
- Weyl, H. (1929) *Zeitschrift für Physik* 56, 330.
- Majorana, E. (1937) *Nuovo Cimento* 14, 171.
- Peskin, M.E. & Schroeder, D.V. (1995) *An Introduction to Quantum Field
  Theory*, Westview / Addison-Wesley. Chapters 3-4.
- Bjorken, J.D. & Drell, S.D. (1964) *Relativistic Quantum Mechanics*.
- Weinberg, S. (1995) *The Quantum Theory of Fields*, Volume I.
"""

from __future__ import annotations

import ctypes
from typing import Sequence, Tuple
from srmech.math.q import Q, exact_vector as _exact_vector  # rc466 (`#T1188`): the ONE exact reader

from srmech import _native
from srmech.math import rational as _srn
from srmech.math.laplacian import mat_matmul, mat_norm
from srmech.math.mat import Mat
from srmech.physics.qm.spin import pauli_matrices, pauli_identity


# ----------------------------------------------------------------------
# numpy-free Mat helpers
# ----------------------------------------------------------------------


def _eye4() -> "Mat":
    """The 4×4 complex identity ``I_4`` as a ``Mat`` (numpy-free)."""
    return Mat.from_rows(
        [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)],
        is_complex=True,
    )


def _scale(s, m: "Mat") -> "Mat":
    """``s · M`` (scalar × ``Mat``) via the :class:`Mat` carrier ``*`` — routes to
    the native ``srmech_mat_scale`` C twin when present (rc141 carrier surface),
    else the byte-identical pure-Python elementwise (the complete alternative).

    Every ``_scale`` operand in this module is a **complex** ``Mat`` (γ-matrices,
    the 4×4 identity, product chains), so the format-preserving carrier keeps the
    complex layout — byte-identical to the prior force-complex helper (the rc145
    B8a C-dispatch: γ₅ / projectors / charge-conjugation now run the scale in C on
    the native path). No ``abs()`` — sign lives in the value (Class K)."""
    return s * m


def _mat_add(a: "Mat", b: "Mat") -> "Mat":
    """``A + B`` via the carrier ``+`` — native ``srmech_mat_add`` C twin when
    present, else the byte-identical pure-Python elementwise (rc145 B8a)."""
    return a + b


def _mat_sub(a: "Mat", b: "Mat") -> "Mat":
    """``A − B`` via the carrier ``−`` — native ``srmech_mat_sub`` C twin when
    present, else the byte-identical pure-Python elementwise (rc145 B8a)."""
    return a - b


def _block4(tl, tr, bl, br) -> "Mat":
    """Assemble a 4×4 complex ``Mat`` from four 2×2 blocks.

    Each block is a 2×2 ``Mat`` or ``None`` (the 2×2 zero block) — the numpy-free
    ``np.block`` replacement for the Dirac γ-matrix 2×2-block construction.
    """
    blocks = [[tl, tr], [bl, br]]
    rows = []
    for bi in range(2):
        for i in range(2):
            row = []
            for bj in range(2):
                b = blocks[bi][bj]
                for j in range(2):
                    row.append(0j if b is None else b[i, j])
            rows.append(row)
    return Mat.from_rows(rows, is_complex=True)


def _canon_true_zeros(m: "Mat") -> "Mat":
    """Canonicalize every TRUE-ZERO component of a constant ``Mat``:
    ``−0.0 → +0.0`` (rc212, #755). ``x + 0.0`` flips ONLY ``−0.0`` and leaves
    every other value bit-identical, so this touches nothing but the
    construction-artifact signed zeros the ``_scale(-1.0, ·)`` block negation
    leaves in the γ literals — a byte-identity hazard for the standalone-C
    constant emitter, and never a signed zero the math depends on (each slot
    is exactly 0, or the exactly-zero component of a ±1 / ±i entry)."""
    return Mat.from_rows(
        [[complex(m[i, j].real + 0.0, m[i, j].imag + 0.0)
          for j in range(m.n_cols)] for i in range(m.n_rows)],
        is_complex=True,
    )


def _qm_gamma_native(mu: int) -> "Mat | None":
    """One Dirac γ^mu from the standalone-C constant emitter
    ``srmech_qm_dirac_gamma`` (rc212) — ``None`` when the symbol is absent /
    the call fails (the canonicalized pure block assembly is the complete,
    byte-identical alternative, not a rescue)."""
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_qm_dirac_gamma")):
        return None
    out = (ctypes.c_double * 32)()
    rc = _native.LIB.srmech_qm_dirac_gamma(ctypes.c_int32(mu), out)
    if rc != _native.SRMECH_OK:
        return None
    return Mat.from_rows(
        [[complex(out[2 * (4 * i + j)], out[2 * (4 * i + j) + 1])
          for j in range(4)] for i in range(4)],
        is_complex=True,
    )


def _qm_minkowski_native() -> "Mat | None":
    """The Minkowski metric from the standalone-C constant emitter
    ``srmech_qm_minkowski_metric`` (rc212) — ``None`` when the symbol is
    absent / the call fails (the pure literal is the complete, byte-identical
    alternative)."""
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_qm_minkowski_metric")):
        return None
    out = (ctypes.c_double * 16)()
    rc = _native.LIB.srmech_qm_minkowski_metric(out)
    if rc != _native.SRMECH_OK:
        return None
    return Mat.from_rows(
        [[out[4 * i + j] for j in range(4)] for i in range(4)],
        is_complex=False,
    )


# ----------------------------------------------------------------------
# operations
# ----------------------------------------------------------------------


def minkowski_metric() -> "Mat":
    """Mostly-minus Minkowski metric ``η^{μν} = diag(+1, -1, -1, -1)``.

    Returned as a 4×4 **real** ``Mat`` (numpy-free).

    rc212 (#755): dispatches to the standalone-C constant emitter
    ``srmech_qm_minkowski_metric`` when native is present (byte-identical to
    the pure literal), so a bare-C host produces the same constant DATA.

    Canonical SSoT: Peskin-Schroeder §3.1 eq 3.4 (mostly-minus convention).
    """
    native = _qm_minkowski_native()
    if native is not None:
        return native
    return Mat.from_rows(
        [[1.0, 0.0, 0.0, 0.0],
         [0.0, -1.0, 0.0, 0.0],
         [0.0, 0.0, -1.0, 0.0],
         [0.0, 0.0, 0.0, -1.0]],
        is_complex=False,
    )


def gamma_matrices() -> Tuple["Mat", "Mat", "Mat", "Mat"]:
    """Dirac γ-matrices ``(γ^0, γ^1, γ^2, γ^3)`` in the Dirac representation.

    In ``2 × 2`` block form using Pauli σ-matrices and the 2×2 identity::

        γ^0 = [[ I_2,  0  ],
               [  0, -I_2 ]]

        γ^i = [[  0,   σ_i ],
               [ -σ_i, 0  ]]   for i = 1, 2, 3.

    rc212 (#755): dispatches to the standalone-C constant emitter
    ``srmech_qm_dirac_gamma`` when native is present — byte-identical to the
    canonicalized pure block assembly below (``_canon_true_zeros`` flips the
    ``−0.0`` construction artifacts the ``_scale(-1.0, ·)`` negation leaves
    in the zero slots), so a bare-C host produces the same constant DATA.

    Canonical SSoT: Peskin-Schroeder §3.2 eq 3.25 + A.6;
    Bjorken-Drell §3.2 eq 3.8.

    Returns:
        ``(g0, g1, g2, g3)``: four 4×4 complex ``Mat`` satisfying the
        Clifford algebra ``{γ^μ, γ^ν} = 2 η^{μν} I_4``.
    """
    native = tuple(_qm_gamma_native(mu) for mu in range(4))
    if all(g is not None for g in native):
        return native
    # spin.pauli_* return numpy-free `Mat` (rc115); consume them directly as the
    # 2×2 blocks — no numpy, no boundary coercion (this module flipped at rc118).
    I2 = pauli_identity()
    sx, sy, sz = pauli_matrices()
    g0 = _canon_true_zeros(_block4(I2, None, None, _scale(-1.0, I2)))
    g1 = _canon_true_zeros(_block4(None, sx, _scale(-1.0, sx), None))
    g2 = _canon_true_zeros(_block4(None, sy, _scale(-1.0, sy), None))
    g3 = _canon_true_zeros(_block4(None, sz, _scale(-1.0, sz), None))
    return g0, g1, g2, g3


def gamma_5() -> "Mat":
    """``γ_5 = i γ^0 γ^1 γ^2 γ^3`` — chirality matrix.

    In the Dirac representation::

        γ_5 = [[ 0, I_2 ],
               [ I_2, 0 ]]

    Properties: ``γ_5² = I_4``, ``{γ_5, γ^μ} = 0`` for all μ, ``γ_5† = γ_5``.

    Canonical SSoT: Peskin-Schroeder §3.4 eq 3.72; Bjorken-Drell §6.1.
    """
    g0, g1, g2, g3 = gamma_matrices()
    # γ_5 = i·γ0·γ1·γ2·γ3 — Class-L mat_matmul cascade for the γ-matrix chain.
    chain = mat_matmul(mat_matmul(mat_matmul(g0, g1), g2), g3)
    return _scale(1j, chain)


def clifford_residuals() -> Tuple[float, float, float]:
    """Numerical residuals for the Cl(1,3) Clifford algebra relations.

    Verifies at machine precision:

    1. ``{γ^μ, γ^ν} = 2 η^{μν} I_4`` for all μ, ν.
    2. ``γ_5² = I_4``.
    3. ``{γ_5, γ^μ} = 0`` for all μ.

    Canonical SSoT: Peskin-Schroeder §3.2 eq 3.21 + §3.4 eq 3.72.

    Returns:
        ``(max_clifford_dev, gamma5_squared_dev, gamma5_anticomm_dev)``:
        all should be at ~1e-14 in double precision.
    """
    gammas = gamma_matrices()
    eta = minkowski_metric()
    I4 = _eye4()
    max_clifford = 0.0
    for mu in range(4):
        for nu in range(4):
            anti = _mat_add(
                mat_matmul(gammas[mu], gammas[nu]),
                mat_matmul(gammas[nu], gammas[mu]),
            )
            expected = _scale(2.0 * eta[mu, nu], I4)
            max_clifford = max(max_clifford, mat_norm(_mat_sub(anti, expected)))
    g5 = gamma_5()
    g5_sq_dev = mat_norm(_mat_sub(mat_matmul(g5, g5), I4))
    g5_anti_dev = max(
        mat_norm(_mat_add(mat_matmul(g5, gammas[mu]), mat_matmul(gammas[mu], g5)))
        for mu in range(4)
    )
    return max_clifford, g5_sq_dev, g5_anti_dev


def weyl_left_projector() -> "Mat":
    """Left-chirality projector ``P_L = (I - γ_5) / 2``.

    Projects a Dirac spinor onto its left-handed Weyl component.
    Properties: ``P_L² = P_L``, ``P_L P_R = 0``, ``P_L + P_R = I``.

    Canonical SSoT: Peskin-Schroeder §3.4 eq 3.71.
    """
    return _scale(0.5, _mat_sub(_eye4(), gamma_5()))


def weyl_right_projector() -> "Mat":
    """Right-chirality projector ``P_R = (I + γ_5) / 2``.

    Canonical SSoT: Peskin-Schroeder §3.4 eq 3.71.
    """
    return _scale(0.5, _mat_add(_eye4(), gamma_5()))


def charge_conjugation_matrix() -> "Mat":
    """Charge-conjugation matrix ``C = i γ^2 γ^0`` (Dirac representation).

    Used to define charge conjugation ``ψ_c = C ψ̄^T`` and the Majorana
    self-conjugacy condition ``ψ = ψ_c``.

    Canonical SSoT: Peskin-Schroeder eq A.27; Bjorken-Drell §5.2.
    """
    g0, g1, g2, g3 = gamma_matrices()
    return _scale(1j, mat_matmul(g2, g0))


def dirac_operator_momentum_space(k: Sequence[float], m: float) -> "Mat":
    """Dirac operator in momentum space: ``γ^μ k_μ - m I_4``.

    With mostly-minus metric, ``γ^μ k_μ = γ^0 k_0 - γ^1 k_1 - γ^2 k_2 - γ^3 k_3``.
    A Dirac spinor ψ satisfies the momentum-space Dirac equation
    ``(γ^μ k_μ - m) ψ(k) = 0`` on-shell ``k² = m²``.

    Canonical SSoT: Peskin-Schroeder §3.2 eq 3.45 + 3.46.

    Args:
        k: 4-momentum ``(k_0, k_1, k_2, k_3)`` as a length-4 sequence of floats.
        m: Mass (rest energy in natural units).

    Returns:
        ``(γ^μ k_μ - m I_4)`` as a 4×4 complex ``Mat``.
    """
    k = [float(x) for x in k]
    if len(k) != 4:
        raise ValueError(
            f"dirac_operator_momentum_space: k must be 4-vector; got length {len(k)}"
        )
    g0, g1, g2, g3 = gamma_matrices()
    eta = minkowski_metric()
    # k_μ = η_{μν} k^ν (mostly-minus metric); η diagonal real → k_lower[i] = η_ii k_i.
    k_lower = [sum(eta[i, j] * k[j] for j in range(4)) for i in range(4)]
    slash_k = _mat_add(
        _mat_add(_scale(k_lower[0], g0), _scale(k_lower[1], g1)),
        _mat_add(_scale(k_lower[2], g2), _scale(k_lower[3], g3)),
    )
    return _mat_sub(slash_k, _scale(m, _eye4()))


def klein_gordon_dispersion(k_spatial: Sequence[float], m: float) -> float:
    """Klein-Gordon on-shell energy ``E = +sqrt(|k|² + m²)``.

    Positive-frequency solution of the relativistic dispersion
    ``E² = |k|² + m²`` (mostly-minus metric: ``k² = E² - |k|² = m²``
    on-shell).

    Canonical SSoT: Klein (1926) eq 5; Gordon (1926) eq 1;
    Peskin-Schroeder §2.3 eq 2.39.

    Args:
        k_spatial: 3-momentum vector as a length-3 sequence of floats.
        m: Mass.

    Returns:
        Positive-frequency on-shell energy.
    """
    k_spatial = [float(x) for x in k_spatial]
    if len(k_spatial) != 3:
        raise ValueError(
            f"klein_gordon_dispersion: k_spatial must be 3-vector; "
            f"got length {len(k_spatial)}"
        )
    if m < 0:
        raise ValueError(f"klein_gordon_dispersion: m must be ≥ 0; got {m}")
    k_sq = sum(x * x for x in k_spatial)   # |k|² — Class-N plain dot
    return float(_srn.sqrt(k_sq + m * m))


def four_momentum_squared(k: Sequence) -> "float | Q":
    """Lorentz-invariant squared 4-momentum ``k² = k_μ k^μ = k_0² - |k|²``.

    Mostly-minus convention. On-shell: ``k² = m²``.

    Canonical SSoT: Peskin-Schroeder §3.1 eq 3.4.

    **THE CARRIER IS THE OPERAND'S, NOT THE OP'S** (rc466, `#T1188`). The form
    is a polynomial — rational-closed — so an exact 4-vector (every component
    ``int`` / ``Q`` / ``(num, den)``) returns the EXACT
    :class:`~srmech.math.q.Q` ``k_0² − k_1² − k_2² − k_3²``; a float component
    anywhere keeps the float64 bilinear form over :func:`minkowski_metric`,
    **accurate to round-off**. Through rc465 ``[float(x) for x in k]`` ran at
    the entry, so ``four_momentum_squared([2**53+1, 0, 0, 0])`` returned
    ``8.112963841460668e+31`` for an exact ``(2**53+1)**2``. The propagators
    that consume this value (:mod:`srmech.physics.qm.propagators`) accept the
    ``Q`` — ``complex(k_squared - m*m, epsilon)`` collapses it at THEIR float
    boundary.
    """
    exact = _exact_vector(k, n=4)
    if exact is not None:
        return exact[0] * exact[0] - exact[1] * exact[1] - exact[2] * exact[2] - exact[3] * exact[3]
    k = [float(x) for x in k]
    if len(k) != 4:
        raise ValueError(
            f"four_momentum_squared: k must be 4-vector; got length {len(k)}"
        )
    eta = minkowski_metric()
    # k² = kᵀ η k (η diagonal real) — numpy-free double-sum bilinear.
    return sum(k[i] * eta[i, j] * k[j] for i in range(4) for j in range(4))


__all__ = [
    "charge_conjugation_matrix",
    "clifford_residuals",
    "dirac_operator_momentum_space",
    "four_momentum_squared",
    "gamma_5",
    "gamma_matrices",
    "klein_gordon_dispersion",
    "minkowski_metric",
    "weyl_left_projector",
    "weyl_right_projector",
]
