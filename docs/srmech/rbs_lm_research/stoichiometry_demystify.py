"""stoichiometry_demystify.py — the chemistry/stoichiometry LOCK (new research item, 2026-06-02).

Reads organic-chem stoichiometry through the framework key: balancing a reaction =
finding the ZERO-SYNDROME codeword of the atomic-conservation parity check (the
intrinsic EC-code cascade, F259/F260), and the coefficients are the ATTESTED integer
null-space anchor -- NOT magic. The balance is a Class L (null space) ∘ Class N
(best_rational) ∘ Class I (lcm/gcd) cascade.

NOW (this script): balancing / conservation / mole-ratios -- fully within reach.
SOON (gauge maths): the directed reaction MECHANISM (which bonds break/form, in what
  order) = the loop bind (k=7 order/tree/direction), gated on the srmech loop-bind op (#814).

SCOPE: framework-reading ONLY. Benign textbook reactions (combustion, photosynthesis).
NO synthesis routes / reaction prediction / capability -- only the MATH STRUCTURE of
balancing. CAD-ban (algebra, not molecular geometry). Defensive scope. Class-K clean
(reference via squared magnitude; sign via pin-slot/reorient, never abs()).
"""
import numpy as np
from srmech.amsc import laplacian, rational, cyclic

# benign textbook reactions; M[element, species] signed (reactant +, product -)
REACTIONS = {
    "methane combustion   CH4 + O2 -> CO2 + H2O": dict(
        species=["CH4", "O2", "CO2", "H2O"], elements=["C", "H", "O"],
        M=[[1, 0, -1, 0],
           [4, 0, 0, -2],
           [0, 2, -2, -1]],
        known=[1, 2, 1, 2]),
    "ethane combustion    C2H6 + O2 -> CO2 + H2O": dict(
        species=["C2H6", "O2", "CO2", "H2O"], elements=["C", "H", "O"],
        M=[[2, 0, -1, 0],
           [6, 0, 0, -2],
           [0, 2, -2, -1]],
        known=[2, 7, 4, 6]),
    "photosynthesis        CO2 + H2O -> C6H12O6 + O2": dict(
        species=["CO2", "H2O", "C6H12O6", "O2"], elements=["C", "H", "O"],
        M=[[1, 0, -6, 0],
           [0, 2, -12, 0],
           [2, 1, -6, -2]],
        known=[6, 6, 1, 6]),
}


def balance(M):
    """Class L (null space) ∘ Class N (best_rational) ∘ Class I (lcm/gcd) -> smallest positive integers."""
    M = np.array(M, dtype=float)
    evals, evecs = laplacian.symmetric_eigendecompose(M.T @ M)   # Class L: null space = 0-eigenvector
    v = evecs[:, int(np.argmin(evals))]
    ref = int(np.argmax(v * v))                                  # max squared-magnitude (Class-K clean)
    if v[ref] < 0.0:                                             # Class-K sign pin-slot -> Class-C reorient
        v = -v
    S = 10 ** 6
    fr = [rational.best_rational(int(round(x * S)), int(round(v[ref] * S)), 1000) for x in v]  # x/v[ref]=p/q
    lcm = 1
    for _, q in fr:
        lcm = cyclic.lcm(lcm, q)
    coeffs = [(lcm // q) * p for p, q in fr]                     # common-denominator integers
    g = 0
    for c in coeffs:
        g = cyclic.gcd(g, c)                                     # coeffs >=0 after reorient
    return [c // g for c in coeffs], M


def main():
    for name, R in REACTIONS.items():
        coeffs, M = balance(R["M"])
        syndrome = (M @ np.array(coeffs)).astype(int)            # the conservation parity check
        guess = [1] * len(coeffs)
        gs = (M @ np.array(guess)).astype(int)
        print(f"\n{name}")
        print(f"  species  : {R['species']}")
        print(f"  balanced : {coeffs}   (known {R['known']})  match={coeffs == R['known']}")
        print(f"  syndrome M@c  = {list(syndrome)}  -> {'ZERO = balanced codeword' if not syndrome.any() else 'NONZERO'}")
        print(f"  guess {guess} -> syndrome {list(gs)}  -> {'detected imbalance (nonzero)' if gs.any() else 'balanced'}")
    print("\n--- reading ---")
    print("  Balancing = the ZERO-SYNDROME codeword of the atomic-conservation parity check")
    print("  (F259/F260 EC-code), via Class L (null space) ∘ N (best_rational) ∘ I (lcm/gcd).")
    print("  The coefficients are ATTESTED-to-structure (the integer null vector), NOT magic.")
    print("  [Reaction MECHANISM = directed bond make/break order = the loop bind, gauge-gated.]")


if __name__ == "__main__":
    main()
