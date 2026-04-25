"""Cyclic-group algebra — Z/nZ operators for the mechanism's gears.

A gear with n teeth is a faithful representation of Z/nZ.  A mesh between
gear A (n_A teeth) and gear B (n_B teeth) implements a rational map on the
group algebra C[Z/lcm(n_A, n_B)Z].

This module provides:

- ``CRTTable(moduli)`` — Chinese Remainder-Theorem product decomposition
  of Z/DZ where D = lcm(moduli), giving an explicit embedding map
  Z/n_i Z -> Z/DZ for each modulus n_i.
- ``roll_operator(D, k)`` — the rotation-by-k operator on C[Z/DZ], used
  as the HDC binding (Plate / Kanerva "permutation ring").
- ``gear_mesh_ratio(n_A, n_B)`` — the rational map Z/n_AZ -> Z/n_BZ
  induced by the physical mesh, as a pair of integers (p, q) with
  p/q = n_A/n_B in lowest terms.
- ``cyclic_group_element(n, k)`` — canonical e^{2piik/n} element as a
  complex scalar.

The ``sigma_day`` operator mentioned in B-H2 is constructed in
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
    """CRT decomposition for Z/DZ where D = lcm(moduli).

    When all moduli are pairwise coprime, Z/DZ ≅ ∏ Z/n_i Z and this is
    a bijection.  When they share factors, Z/DZ is strictly larger than
    the product, and the embedding Z/n_i Z -> Z/DZ is x -> x · (D/n_i).

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
        """Embed ``x mod moduli[i]`` into Z/DZ."""
        n = self.moduli[i]
        return (x % n) * (self.D // n) % self.D

    def project(self, x: int, i: int) -> int:
        """Project ``x mod D`` down to Z/moduli[i]Z."""
        return x % self.moduli[i]

    def phase_vector(self, residues: Sequence[int]) -> np.ndarray:
        """For residues r_i in Z/moduli[i]Z, return the vector of
        phase angles theta_i = 2pi r_i / n_i (radians)."""
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

    This is the chess sec9f / HDC binding operator: a shift on C[Z/DZ].
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
    """e^{2piik/n} as a complex scalar in C[Z/nZ]."""
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


def chain_ratio_noisy(
    tooth_counts: Sequence[int],
    epsilons: Sequence[float],
) -> float:
    """Like ``chain_ratio`` but each mesh pair gets a multiplicative
    ``(1 + epsilon)`` perturbation.  Returns a float (not exact rational).

    ``tooth_counts`` is the same alternating mesh/axle list as
    ``chain_ratio``: pairs ``(n_driver, n_driven)``.  ``epsilons`` is
    a sequence of length ``len(tooth_counts) // 2`` -- one epsilon per
    mesh pair.

    Used by ``manufacturing_tolerance`` Track 3 to model bronze-cutting
    fractional-tooth error.  The noiseless integer ``chain_ratio`` is
    preserved untouched (still load-bearing for B-H1 / A-H1).
    """
    if len(tooth_counts) < 2 or len(tooth_counts) % 2 != 0:
        raise ValueError(
            "chain_ratio_noisy needs an even number of gears "
            "(mesh + axle pairs)"
        )
    n_meshes = len(tooth_counts) // 2
    if len(epsilons) != n_meshes:
        raise ValueError(
            f"epsilons must have length {n_meshes} (one per mesh), "
            f"got {len(epsilons)}"
        )
    ratio = 1.0
    for i, eps in enumerate(epsilons):
        n_drv = tooth_counts[2 * i]
        n_drn = tooth_counts[2 * i + 1]
        ratio *= (n_drv / n_drn) * (1.0 + eps)
    return ratio


_EPILOG = """\
Examples:
  # Default: CRT + roll + chain demos:
  python -m research.cyclic_group_algebra

  # Compute a chain ratio:
  python -m research.cyclic_group_algebra --operation chain --gears 224,32,53,96

  # Mesh ratio for one pair:
  python -m research.cyclic_group_algebra --operation mesh --gears 224,64

  # CRT product of arbitrary moduli:
  python -m research.cyclic_group_algebra --operation crt --moduli 19,235

  # Noisy chain ratio (Track 3 utility):
  python -m research.cyclic_group_algebra --operation chain-noisy \\
       --gears 224,32,53,96 --epsilons 0.01,-0.005

References
----------
Plate, T. A. (2003). Holographic Reduced Representations.  CSLI.
"""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m research.cyclic_group_algebra",
        description=("Cyclic-group algebra primitives for the mechanism's "
                     "gears: CRT, roll operator, mesh ratio, chain ratio, "
                     "and a noise-aware chain ratio for Track 3."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--operation", default=None,
        choices=("chain", "chain-noisy", "mesh", "crt", "roll"),
        help="If omitted, runs the demo battery.",
    )
    parser.add_argument(
        "--gears", default=None,
        help="Comma-separated tooth counts for chain/mesh.",
    )
    parser.add_argument(
        "--epsilons", default=None,
        help=("Comma-separated epsilons for chain-noisy.  Length must be "
              "len(gears) // 2."),
    )
    parser.add_argument(
        "--moduli", default=None,
        help="Comma-separated moduli for CRT.",
    )
    parser.add_argument(
        "--D", type=int, default=None,
        help="D for the roll-operator demo.",
    )
    parser.add_argument(
        "--k", type=int, default=1,
        help="k for the roll operator.",
    )
    return parser


def main(argv=None):
    args = _make_parser().parse_args(argv)

    if args.operation == "chain":
        if not args.gears:
            print("ERROR: --gears required for --operation chain.")
            return 2
        gears = [int(x) for x in args.gears.split(",")]
        p, q = chain_ratio(gears)
        print(f"chain_ratio({gears}) = {p}/{q}  ({p / q:.6f})")
        return 0

    if args.operation == "chain-noisy":
        if not args.gears or not args.epsilons:
            print("ERROR: --gears and --epsilons required.")
            return 2
        gears = [int(x) for x in args.gears.split(",")]
        eps = [float(x) for x in args.epsilons.split(",")]
        ratio = chain_ratio_noisy(gears, eps)
        p, q = chain_ratio(gears)
        nominal = p / q
        print(f"chain_ratio_noisy({gears}, {eps}) = {ratio:.6f}")
        print(f"  nominal = {nominal:.6f}, "
              f"relative error = {(ratio / nominal - 1):+.6f}")
        return 0

    if args.operation == "mesh":
        if not args.gears:
            print("ERROR: --gears 'driver,driven' required.")
            return 2
        a, b = (int(x) for x in args.gears.split(","))
        p, q = gear_mesh_ratio(a, b)
        print(f"gear_mesh_ratio({a}, {b}) = {p}/{q}  ({p / q:.6f})")
        return 0

    if args.operation == "crt":
        if not args.moduli:
            print("ERROR: --moduli required for --operation crt.")
            return 2
        moduli = [int(x) for x in args.moduli.split(",")]
        ct = CRTTable(moduli)
        print(f"CRTTable({moduli}) -> D = {ct.D}, "
              f"pairwise_coprime = {ct.pairwise_coprime}")
        return 0

    if args.operation == "roll":
        if args.D is None:
            print("ERROR: --D required for --operation roll.")
            return 2
        print(f"Roll operator on D={args.D}, k={args.k}:")
        print(roll_operator(args.D, args.k).astype(int))
        return 0

    # Default demo battery
    ct = CRTTable([19, 235])
    print("CRT over (19, 235):", ct)
    print("  D =", ct.D, "pairwise coprime:", ct.pairwise_coprime)
    print("  embed(0, 1) =", ct.embed(0, 1),
          "; embed(1, 1) =", ct.embed(1, 1))
    print()
    print("Roll operator on D=5, k=2:")
    print(roll_operator(5, 2).astype(int))
    print()
    print("Gear mesh ratio b1 (224) -> b2 (64):", gear_mesh_ratio(224, 64))
    print("Chain ratio [b1=224, e2=32, e5=53, k1=96]:",
          chain_ratio([224, 32, 53, 96]))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
