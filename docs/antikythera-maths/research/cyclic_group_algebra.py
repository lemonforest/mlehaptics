"""Cyclic-group algebra — ℤ/nℤ operators for the mechanism's gears.

A gear with n teeth is a faithful representation of ℤ/nℤ.  A mesh between
gear A (n_A teeth) and gear B (n_B teeth) implements a rational map on the
group algebra ℂ[ℤ/lcm(n_A, n_B)ℤ].

This module provides:

- ``CRTTable(moduli)`` — Chinese Remainder-Theorem product decomposition
  of ℤ/Dℤ where D = lcm(moduli), giving an explicit embedding map
  ℤ/n_i ℤ -> ℤ/Dℤ for each modulus n_i.
- ``roll_operator(D, k)`` — the rotation-by-k operator on ℂ[ℤ/Dℤ], used
  as the HDC binding (Plate / Kanerva "permutation ring").
- ``gear_mesh_ratio(n_A, n_B)`` — the rational map ℤ/n_Aℤ -> ℤ/n_Bℤ
  induced by the physical mesh, as a pair of integers (p, q) with
  p/q = n_A/n_B in lowest terms.
- ``cyclic_group_element(n, k)`` — canonical e^{2πik/n} element as a
  complex scalar.

The ``σ_day`` operator mentioned in B-H2 is constructed in
``encode_ant.py`` because its action depends on the encoder's D choice.
"""

from __future__ import annotations

from functools import reduce
from math import gcd, lcm
from typing import Iterable, List, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# CRT product decomposition
# ---------------------------------------------------------------------------

def lcm_many(xs: Iterable[int]) -> int:
    return reduce(lcm, xs, 1)


def gcd_many(xs: Iterable[int]) -> int:
    return reduce(gcd, xs, 0)


def is_coprime(a: int, b: int) -> bool:
    return gcd(a, b) == 1


class CRTTable:
    """CRT decomposition for ℤ/Dℤ where D = lcm(moduli).

    When all moduli are pairwise coprime, ℤ/Dℤ ≅ ∏ ℤ/n_i ℤ and this is
    a bijection.  When they share factors, ℤ/Dℤ is strictly larger than
    the product, and the embedding ℤ/n_i ℤ -> ℤ/Dℤ is x -> x · (D/n_i).

    Attributes
    ----------
    moduli : list[int]
        The moduli as given.
    D : int
        lcm of moduli.
    pairwise_coprime : bool
        True iff the moduli are pairwise coprime (so CRT is a bijection).
    """

    def __init__(self, moduli: Sequence[int]):
        if len(moduli) == 0:
            raise ValueError("CRTTable needs at least one modulus")
        for m in moduli:
            if m < 1:
                raise ValueError(f"modulus must be positive: {m}")
        self.moduli: List[int] = list(moduli)
        self.D: int = lcm_many(self.moduli)
        self.pairwise_coprime: bool = all(
            is_coprime(self.moduli[i], self.moduli[j])
            for i in range(len(self.moduli))
            for j in range(i + 1, len(self.moduli))
        )

    def embed(self, i: int, x: int) -> int:
        """Embed ``x mod moduli[i]`` into ℤ/Dℤ."""
        n = self.moduli[i]
        return (x % n) * (self.D // n) % self.D

    def project(self, x: int, i: int) -> int:
        """Project ``x mod D`` down to ℤ/moduli[i]ℤ."""
        return x % self.moduli[i]

    def phase_vector(self, residues: Sequence[int]) -> np.ndarray:
        """For residues r_i in ℤ/moduli[i]ℤ, return the vector of
        phase angles θ_i = 2π r_i / n_i (radians)."""
        if len(residues) != len(self.moduli):
            raise ValueError(
                f"expected {len(self.moduli)} residues, got {len(residues)}"
            )
        return np.array(
            [2.0 * np.pi * (r % n) / n for r, n in zip(residues, self.moduli)],
            dtype=np.float64,
        )

    def __repr__(self) -> str:
        return (f"CRTTable(moduli={self.moduli}, D={self.D}, "
                f"pairwise_coprime={self.pairwise_coprime})")


# ---------------------------------------------------------------------------
# Roll operator (HDC binding)
# ---------------------------------------------------------------------------

def roll_operator(D: int, k: int) -> np.ndarray:
    """Return the D×D permutation matrix that rolls by k positions.

    This is the chess §9f / HDC binding operator: a shift on ℂ[ℤ/Dℤ].
    For performance in downstream callers, prefer ``np.roll`` on the
    vector directly; this matrix form is provided for explicit
    algebraic manipulation.
    """
    k = k % D
    P = np.zeros((D, D), dtype=np.float64)
    for i in range(D):
        P[(i + k) % D, i] = 1.0
    return P


def roll_vector(v: np.ndarray, k: int) -> np.ndarray:
    """Roll a D-length vector by k positions (the fast path)."""
    return np.roll(v, k)


# ---------------------------------------------------------------------------
# Gear-mesh ratio
# ---------------------------------------------------------------------------

def gear_mesh_ratio(n_driver: int, n_driven: int) -> Tuple[int, int]:
    """For a mesh between two gears, the output angle per unit input
    angle is n_driver / n_driven.  Return that in lowest terms.

    Example
    -------
    >>> gear_mesh_ratio(224, 64)
    (7, 2)
    """
    g = gcd(n_driver, n_driven)
    return (n_driver // g, n_driven // g)


def cyclic_group_element(n: int, k: int) -> complex:
    """e^{2πik/n} as a complex scalar in ℂ[ℤ/nℤ]."""
    return np.exp(2.0j * np.pi * (k % n) / n)


# ---------------------------------------------------------------------------
# Compose a mesh chain: (n1 -> n2 -> n3 -> ...) into a rational ratio.
# ---------------------------------------------------------------------------

def chain_ratio(tooth_counts: Sequence[int]) -> Tuple[int, int]:
    """For a chain of meshing gears with tooth counts [n1, n2, n3, ...]
    connected as n1 drives n2, n2 shares axle with n3 drives n4, etc.,
    return the overall input:output ratio in lowest terms.

    This simple helper assumes pairs alternate ``mesh, axle, mesh,
    axle, ...`` — i.e. ``chain_ratio([n1, n2, n3, n4])`` interprets
    n1-meshes-n2, n2-on-axle-with-n3, n3-meshes-n4.  The ratio is
    (n1 * n3) / (n2 * n4).
    """
    if len(tooth_counts) < 2:
        raise ValueError("need at least two tooth counts")
    if len(tooth_counts) % 2 != 0:
        raise ValueError(
            "chain_ratio needs an even number of gears "
            "(mesh + axle pairs); got " + str(tooth_counts)
        )
    drivers = 1
    drivens = 1
    for i in range(0, len(tooth_counts), 2):
        drivers *= tooth_counts[i]
        drivens *= tooth_counts[i + 1]
    g = gcd(drivers, drivens)
    return (drivers // g, drivens // g)


if __name__ == "__main__":
    # CRT on Metonic-cycle moduli
    ct = CRTTable([19, 235])
    print("CRT over (19, 235):", ct)
    print("  D =", ct.D, "pairwise coprime:", ct.pairwise_coprime)
    print("  embed(0, 1) =", ct.embed(0, 1), "; embed(1, 1) =", ct.embed(1, 1))
    print()
    print("Roll operator on D=5, k=2:")
    print(roll_operator(5, 2).astype(int))
    print()
    print("Gear mesh ratio b1 (224) → b2 (64):", gear_mesh_ratio(224, 64))
    print("Chain ratio [b1=224, e2=32, e5=53, k1=96]:",
          chain_ratio([224, 32, 53, 96]))
