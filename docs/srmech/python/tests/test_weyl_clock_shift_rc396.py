"""rc396 (`#T1031`, position-operator half) — the Weyl clock/shift loop closes
the ring position/momentum triad.

srmech already ships the momentum GENERATOR ``lattice_momentum`` (``p̂ = -i∂_x``).
This closes the loop: the fenced POSITION ``x̂`` on a ring is NOT a naive linear
``diag(k·dx)`` (multi-valued on a ring — it jumps at the seam) but the Weyl
**clock** ``U = diag(ω^k)``, ``ω = e^{2πi/n}`` (single-valued, the phase wraps).
Its partner is the **shift** ``V`` (cyclic one-site translation = the group-level
momentum). They obey the **Weyl relation** ``U V = ω V U`` — the compact,
finite-dimensional form of the canonical ``[x̂, p̂] = iℏ``.

Canonical SSoT: Schwinger, J. (1960) "Unitary Operator Bases", *Proc. Natl.
Acad. Sci. USA* **46**, 570–579 (the clock-and-shift finite QM); Weyl, H. (1931)
*The Theory of Groups and Quantum Mechanics* (the commutation relation).

numpy-FREE (this whole module): the working matrices are the framework-native
:class:`~srmech.math.mat.Mat` and every linear-algebra step routes through the
Class-L ``mat_*`` family / the ``@`` idiom — no numpy anywhere.
"""
from __future__ import annotations

import pytest

from srmech.math.laplacian import mat_matmul, mat_norm
from srmech.math.mat import Mat
from srmech.physics.qm.single_particle import clock_operator, shift_operator
from srmech.physics.qm.spin import pauli_matrices

# n = 2 and n = 4 land every clock/shift entry on {0, ±1, ±i} (whole
# quarter-turns), so the whole loop is BIT-EXACT there; n ∈ {3, 5} are pure
# sub-quarter angles and n = 8 mixes exact and sub-quarter entries — those are
# machine-ε.
NS = (2, 3, 4, 5, 8)
EXACT_NS = (2, 4)
_TOL = 1e-12


def _identity(n: int) -> "Mat":
    """The n×n complex identity as a :class:`Mat` (numpy-free)."""
    return Mat.from_rows(
        [[1 + 0j if i == j else 0j for j in range(n)] for i in range(n)],
        is_complex=True,
    )


def _matpow(m: "Mat", p: int) -> "Mat":
    """``m**p`` via iterated Class-L matmul (Mat has no ``__pow__``)."""
    out = _identity(m.n_rows)
    for _ in range(p):
        out = mat_matmul(out, m)
    return out


# ----------------------------------------------------------------------
# the loop's canonical commutation: U V = ω V U
# ----------------------------------------------------------------------


def test_weyl_relation_holds_to_machine_eps():
    """``clock·shift == ω·(shift·clock)`` — the finite-dim ``[x̂, p̂] = iℏ``.

    ``ω`` is read straight off the clock (its second diagonal entry is ``ω^1``),
    so this also pins the exact ω-power CONVENTION: with ``U = diag(ω^k)`` and
    ``V`` the shift-UP, the relation is ``U V = ω V U`` (ω on the ``VU`` side).
    """
    for n in NS:
        U = clock_operator(n)
        V = shift_operator(n)
        omega = U[1, 1]                       # ω^1 = the primitive n-th root
        dev = mat_norm((U @ V) - omega * (V @ U))
        assert dev < _TOL, f"n={n}: Weyl deviation {dev}"
        if n in EXACT_NS:
            assert dev == 0.0, (
                f"n={n}: all ±1/±i entries → the Weyl relation must be "
                f"BIT-EXACT, got {dev}")


def test_the_conjugate_convention_is_wrong_non_vacuity():
    """⚠️ NON-VACUITY. Prove the relation is NOT trivially satisfied by any ω.

    For ``n ≥ 3`` the primitive root ``ω`` is genuinely complex, so the mirror
    convention ``U V = ω̄ V U`` must FAIL — otherwise the machine-ε assert above
    would pass for the wrong reason. (At ``n = 2, 4`` ``ω`` is real so ``ω̄ = ω``
    and the mirror is indistinguishable — excluded here on purpose.)
    """
    for n in (3, 5, 8):
        U = clock_operator(n)
        V = shift_operator(n)
        omega_bar = U[1, 1].conjugate()
        dev = mat_norm((U @ V) - omega_bar * (V @ U))
        assert dev > 1e-6, (
            f"n={n}: the ω̄ convention should be far from satisfied; got {dev}")


# ----------------------------------------------------------------------
# the payoff cross-check: n = 2 reduces to the shipped Pauli surface
# ----------------------------------------------------------------------


def test_n2_reduces_to_pauli_bit_exact():
    """At ``n = 2``: ``U = σ_z``, ``V = σ_x``, and the chiral third
    ``i·(V·U) = σ_y`` — the whole Weyl pair IS Pauli, and ``Y = iXZ`` (with
    ``X = shift``, ``Z = clock``) falls out of the multiply already shipped. No
    separate ``Y`` op is added; it is DERIVED here."""
    sx, sy, sz = pauli_matrices()
    U = clock_operator(2)
    V = shift_operator(2)
    assert U == sz, "clock_operator(2) must be exactly σ_z"
    assert V == sx, "shift_operator(2) must be exactly σ_x"
    # i·X·Z with X = shift (σ_x), Z = clock (σ_z): i·(V·U) = σ_y, bit-exact.
    y = 1j * (V @ U)
    assert y == sy, "i·(shift·clock) must be exactly σ_y (Y = iXZ)"


# ----------------------------------------------------------------------
# unitarity + the cyclic order-n identity
# ----------------------------------------------------------------------


def test_clock_and_shift_are_unitary():
    for n in NS:
        U = clock_operator(n)
        V = shift_operator(n)
        I = _identity(n)
        assert mat_norm((U @ U.conj().T) - I) < _TOL, f"n={n}: U not unitary"
        assert mat_norm((V @ V.conj().T) - I) < _TOL, f"n={n}: V not unitary"
        # V is a real permutation matrix, so V·Vᴴ = I is BIT-EXACT for every n.
        assert (V @ V.conj().T) == I, f"n={n}: V·Vᴴ must be exactly I"
        if n in EXACT_NS:
            assert (U @ U.conj().T) == I, f"n={n}: U·Uᴴ must be exactly I"


def test_order_n_identity():
    """``U**n == I`` and ``V**n == I`` — the cyclic group ``Z_n`` closes."""
    for n in NS:
        U = clock_operator(n)
        V = shift_operator(n)
        I = _identity(n)
        assert mat_norm(_matpow(U, n) - I) < 1e-9, f"n={n}: U**n ≠ I"
        # The shift is an integer permutation, so V**n = I is BIT-EXACT.
        assert _matpow(V, n) == I, f"n={n}: V**n must be exactly I"
        if n in EXACT_NS:
            assert _matpow(U, n) == I, f"n={n}: U**n must be exactly I"


# ----------------------------------------------------------------------
# domain guard
# ----------------------------------------------------------------------


def test_n_below_two_raises():
    for bad in (1, 0, -1):
        with pytest.raises(ValueError):
            clock_operator(bad)
        with pytest.raises(ValueError):
            shift_operator(bad)
