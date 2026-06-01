"""loop_bind_sol_resonance.py — the ephemerides Sol bridge: loop bind BEYOND playback.

Applies the k=7 loop bind (F272-F274) to an ATTESTED orbital-resonance lock: the
Galilean Laplace resonance Io:Europa:Ganymede,  n_Io - 3*n_Eu + 2*n_Ga = 0
(coefficients [1,-3,2]; libration argument lambda_Io - 3*lambda_Eu + 2*lambda_Ga
librates about 180 deg). A mean-motion resonance is a directed, signed, ORDERED
lock that binds three moons into one dynamical BOUND STATE.

PLAYBACK (the Antikythera / cyclic-group way, commutative): encodes the periods
  (what repeats) but washes out order / sign / direction.
LOOP BIND (k=7): encodes the directed, signed resonance ARGUMENT -- the bound
  state's internal structure -- recoverably (and invertibly nested under the host).

SCOPE: framework-reading ONLY. CAD-ban -> NO N-body / orbital integration; we encode
  the resonance STRUCTURE, not the dynamics. Literature owns celestial mechanics; the
  resonance integers [1,-3,2] are attested-to-structure (F260), periods attested-B
  (JPL/NASA). The 'glueball / bound state' is the k=7 LENS (F269), NOT a physics claim
  that orbits are gauge fields. Class-K clean (signs via conj/chirality, not abs;
  cosine via inner products). Defensive scope.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop_bind_moufang import loop_bind, conj, normsq, DIM        # noqa: E402
from srmech.amsc import hdc                                       # noqa: E402

SEED = 4
BODIES = ["Io", "Europa", "Ganymede"]
RES_COEFFS = [1, -3, 2]                 # attested-to-structure (Laplace lock, F260)
PERIODS_DAYS = [1.769, 3.551, 7.155]    # attested-B (JPL); ~1:2:4


def unit(v):
    return v / (normsq(v) ** 0.5)


def cos(u, v):
    return float(np.dot(u, v)) / ((normsq(u) * normsq(v)) ** 0.5)


def main():
    rng = np.random.default_rng(SEED)
    anchors = {b: unit(rng.standard_normal(DIM)) for b in BODIES}

    def signed(b, coeff):
        """Sign of the resonance coefficient = Class-C chirality (conj for the minus)."""
        a = anchors[b]
        return a if coeff > 0 else conj(a)

    def loop_chain(order_coeffs):
        items = [signed(b, c) for b, c in order_coeffs]
        acc = items[0]
        for it in items[1:]:
            acc = loop_bind(acc, it)           # left-fold loop bind: order + sign survive
        return acc

    forward = list(zip(BODIES, RES_COEFFS))                  # [Io+, Eu-, Ga+]  (the real lock)
    reverse = list(zip(BODIES[::-1], RES_COEFFS[::-1]))      # [Ga+, Eu-, Io+]
    wrongsign = list(zip(BODIES, [1, 3, 2]))                 # all + : drops the -3 sign

    E_fwd, E_rev, E_ws = loop_chain(forward), loop_chain(reverse), loop_chain(wrongsign)
    print("=== LOOP BIND (k=7): the directed, signed resonance argument ===")
    print(f"  cos(forward, reverse)    = {cos(E_fwd, E_rev):+.3f}  (<1 -> resonance DIRECTION recoverable)")
    print(f"  cos(forward, wrong-sign) = {cos(E_fwd, E_ws):+.3f}  (<1 -> resonance SIGN pattern recoverable)")

    # PLAYBACK baseline: commutative klein4 bundle of the body anchors (the period set)
    kb = [hdc.klein4_random(2048, seed=200 + i) for i in range(3)]
    P_fwd = hdc.klein4_bundle(kb[0], kb[1], kb[2])
    P_rev = hdc.klein4_bundle(kb[2], kb[1], kb[0])
    print("\n=== PLAYBACK (commutative bundle): the period set only ===")
    print(f"  sim(forward, reverse)    = {hdc.klein4_similarity(P_fwd, P_rev):.3f}  (=1 -> direction LOST)")

    # NESTING / bound state: the host (Jupiter) binds the resonant trio into one object
    jup = unit(rng.standard_normal(DIM))
    bound = loop_bind(jup, E_fwd)
    recovered = loop_bind(conj(jup), bound)        # unbind host -> recover the trio's bound arg
    print("\n=== NESTING / bound state (host binds the resonant trio) ===")
    print(f"  unbind host -> recover trio: cos = {cos(recovered, E_fwd):.6f}  (=1 -> invertibly nested)")

    print("\n--- verdict ---")
    print("  PLAYBACK keeps the periods (what repeats) but not the lock's order/sign/direction.")
    print("  The LOOP BIND keeps the full directed, signed resonance argument AND nests it")
    print("  invertibly under its host -> the resonance LOCK encoded as a recoverable BOUND")
    print("  STATE (the k=7/glueball lens), not three independently-replayed cycles.")


if __name__ == "__main__":
    main()
