"""Spin-½ operators: Pauli matrices + Clifford algebra Cl(0,3).

The Pauli matrices σ_x, σ_y, σ_z generate the Clifford algebra ``Cl(0,3)``
with anti-commutation ``{σ_i, σ_j} = 2 δ_{ij} I`` and commutation
``[σ_i, σ_j] = 2i ε_{ijk} σ_k``. Per
``[[user_stance_1d_collapse_to_loe_identity_not_action]]`` + Spike #24:
Pauli matrices are a **Class M Clifford binding** primitive — they bind
the 2-spinor space into substrate-localised form. Foundational to the
Dirac equation (relativistic QM, rc10) and to qubit / quantum-information
primitives.

Canonical SSoT:

- Pauli, W. (1927) *Zeitschrift für Physik* 43, 601-623.
- Sakurai, J.J. *Modern QM* §3.2.
- Cohen-Tannoudji *QM* §IV.A.
"""

from __future__ import annotations

from typing import Tuple

from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat


def pauli_matrices() -> Tuple["Mat", "Mat", "Mat"]:
    """Return the three Pauli matrices ``(σ_x, σ_y, σ_z)``.

    numpy-FREE (v0.7.5rc115, #564) — each is an **exact** 2×2 complex
    Hermitian :class:`~srmech.amsc.mat.Mat` with entries in ``{0, ±1, ±i}``
    (no float approximation; entries are plain Python ``complex`` scalars).

    Canonical SSoT: Pauli (1927) *Zeitschrift für Physik* 43, 601;
    Sakurai *Modern QM* §3.2 eq 3.2.1.

    Returns:
        ``(sigma_x, sigma_y, sigma_z)``: each a 2×2 complex Hermitian
        traceless ``Mat`` satisfying ``σ_i² = I`` and the Clifford algebra.
    """
    sigma_x = Mat.from_rows([[0, 1], [1, 0]], is_complex=True)
    sigma_y = Mat.from_rows([[0, -1j], [1j, 0]], is_complex=True)
    sigma_z = Mat.from_rows([[1, 0], [0, -1]], is_complex=True)
    return sigma_x, sigma_y, sigma_z


def pauli_identity() -> "Mat":
    """The 2×2 identity (Cl(0,3) scalar) as an exact complex ``Mat``."""
    return Mat.from_rows([[1, 0], [0, 1]], is_complex=True)


def _entries(m: "Mat"):
    """Flat row-major list of a ``Mat``'s plain complex entries (numpy-free)."""
    return [m[i, j] for i in range(m.n_rows) for j in range(m.n_cols)]


def pauli_clifford_residuals() -> Tuple[float, float]:
    """Numerical residuals for the Clifford algebra relations on σ_i.

    Verifies:

    - **Anticommutation**: ``{σ_i, σ_j} = 2 δ_{ij} I`` for all i, j.
    - **Commutation**: ``[σ_i, σ_j] = 2i ε_{ijk} σ_k`` (cyclic).

    Canonical SSoT: Sakurai *Modern QM* §3.2 eq 3.2.2-3.2.3.

    Returns:
        ``(max_anticomm_dev, max_comm_dev)``: maximum Frobenius-norm
        deviation from the expected relations. Both should be at machine
        precision (~1e-15).
    """
    sx, sy, sz = pauli_matrices()
    I = pauli_identity()
    # Anticommutator residuals — Class-L native matmul (mat_matmul) for every
    # Pauli product, combined entrywise as numpy-free flat complex lists, then
    # the rc114 Class-N mat_norm. No numpy, no abs().
    def _norm_sum(*pairs):   # ‖Σ_k sign_k · P_k‖ over aligned 2×2 entries
        ents = [_entries(p) for _, p in pairs]
        signs = [s for s, _ in pairs]
        combined = [sum(sg * e[k] for sg, e in zip(signs, ents))
                    for k in range(len(ents[0]))]
        return mat_norm(combined)
    mm = mat_matmul
    max_anti = max([
        _norm_sum((1, mm(sx, sy)), (1, mm(sy, sx))),
        _norm_sum((1, mm(sx, sz)), (1, mm(sz, sx))),
        _norm_sum((1, mm(sy, sz)), (1, mm(sz, sy))),
        _norm_sum((1, mm(sx, sx)), (-1, I)),
        _norm_sum((1, mm(sy, sy)), (-1, I)),
        _norm_sum((1, mm(sz, sz)), (-1, I)),
    ])
    # Commutator residuals (cyclic): ‖[σ_i,σ_j] − 2i ε_{ijk} σ_k‖.
    max_comm = max([
        _norm_sum((1, mm(sx, sy)), (-1, mm(sy, sx)), (-2j, sz)),
        _norm_sum((1, mm(sy, sz)), (-1, mm(sz, sy)), (-2j, sx)),
        _norm_sum((1, mm(sz, sx)), (-1, mm(sx, sz)), (-2j, sy)),
    ])
    return max_anti, max_comm


def pauli_spin_operator(direction) -> "Mat":
    """Spin-½ projection onto an arbitrary axis: ``S_n = (ℏ/2) σ · n̂``.

    Returns ``σ · n̂ / 2`` (ℏ = 1 convention) as an exact-shape 2×2 complex
    ``Mat`` where ``n̂`` is the unit vector along the chosen direction.
    numpy-FREE (v0.7.5rc115) — ``direction`` is any 3-element sequence
    (list / tuple / ndarray), the magnitude is the rc114 ``mat_norm`` and the
    combination is an entrywise list build (no numpy, no abs()).

    Canonical SSoT: Sakurai *Modern QM* §3.2 eq 3.2.51; Griffiths
    *Intro QM* §4.4.

    Args:
        direction: 3-element sequence (need not be unit; will be normalized).

    Returns:
        2×2 Hermitian ``Mat`` with eigenvalues ±½.

    Raises:
        ValueError: zero-magnitude direction or wrong length.
    """
    try:
        d = [float(x) for x in direction]
    except TypeError:
        raise ValueError("pauli_spin_operator: direction must be a 3-vector")
    if len(d) != 3:
        raise ValueError(
            f"pauli_spin_operator: direction must be a 3-vector; got length {len(d)}"
        )
    norm = mat_norm(d)
    if norm == 0.0:
        raise ValueError("pauli_spin_operator: direction must be non-zero")
    nhat = [x / norm for x in d]
    sx, sy, sz = pauli_matrices()
    out = [
        [0.5 * (nhat[0] * sx[i, j] + nhat[1] * sy[i, j] + nhat[2] * sz[i, j])
         for j in range(2)]
        for i in range(2)
    ]
    return Mat.from_rows(out, is_complex=True)


__all__ = [
    "pauli_clifford_residuals",
    "pauli_identity",
    "pauli_matrices",
    "pauli_spin_operator",
]
