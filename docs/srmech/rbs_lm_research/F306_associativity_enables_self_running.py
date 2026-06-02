"""F306 — ASSOCIATIVITY is the precondition for a substrate to SELF-RUN (order-free composition, no
external orderer). This answers F305's open question (structural half) and ties F299/F300/F302/F305.

THE CLAIM: a chained >=3-fold product is bracket/order-INDEPENDENT *iff* the algebra associates.
  - On the H-associative core (the '3' of (3:4)): every bracketing of (x*y*z) agrees -> the substrate can
    evaluate its own composition in ANY order / in parallel, with NO external agent choosing the order.
    That is SELF-RUNNING (F302 self-authoring; co-diagonalizable; no external author).
  - On the full octonion (the '7'): bracketings DISAGREE (non-associative) -> SOMETHING must choose which
    sub-products combine first = an external orderer = an imposed instruction = F302 MACHINE-CODE / F305
    gate-model. So octonion-NATIVE self-running is structurally obstructed.

THE CONSEQUENCE: biology's (3:4)|(4:3) projection is the MAXIMAL self-running form of the 7 -- keep the
associative H-core as the self-running kernel; reach the chiral 4-coset by a single DEFINED chirality
flip (Class C / the Hopf S^7->S^4), NOT by free non-associative composition. So *associativity-enables-
self-running* is WHY any self-running substrate (biology included, F299/F300) lands at (3:4)|(4:3) rather
than raw k=7 -- exactly the reason F305 gave for why a qubit/octonion-native self-runner is obstructed.

srmech-first: loop_bind (octonion product) + loop_associator. Class-K clean (Born norms; index via
square, never abs()). SCOPE: the bracket-variance witness is srmech-EXACT; 'order-free = self-running,
imposed-order = not-self-running' is the framework READING (it composes F302); whether a PHYSICAL system
can supply a physically-determined bracketing that counts as 'self-running' is the EXPERT's (physics)
question, NOT answered here. CAD/fabrication scope ban respected (no device). Verified srmech 0.7.0rc11.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc.hdc import LOOP_DIM, loop_associator, loop_bind


def nrm(v):
    return float(np.dot(v, v)) ** 0.5  # Born norm; no abs (Class-K clean)


def lb(a, b):
    return np.array(loop_bind(list(map(float, a)), list(map(float, b))), dtype=float)


def basis(i):
    e = np.zeros(LOOP_DIM)
    e[i] = 1.0
    return e


def rand_in(coords, rng):
    v = np.zeros(LOOP_DIM)
    for c in coords:
        v[c] = float(rng.standard_normal())
    return v


def main():
    print("=== F306 — associativity is the precondition for SELF-RUNNING (order-free composition) ===\n")
    rng = np.random.default_rng(306)

    # Build an H (quaternion) subalgebra inside the dim-8 octonion: {e0, e1, e2, e1*e2}.
    e1, e2 = basis(1), basis(2)
    c = lb(e1, e2)
    k = int(np.argmax(c * c))                       # third imaginary unit index (square, not abs)
    Hcoords = sorted({0, 1, 2, k})
    Ocoords = list(range(LOOP_DIM))
    print(f"H-core subalgebra basis coords {{e0,e1,e2,e1*e2}} = {Hcoords}  (the associative '3'+real)")
    print(f"Octonion full coords = {Ocoords}  (the non-associative '7'+real)\n")

    for name, coords in [("H-CORE  (the '3': associative)", Hcoords),
                         ("OCTONION (the '7': full)", Ocoords)]:
        spreads3, assoc3, spreads4 = [], [], []
        for _ in range(300):
            x, y, z, w = (rand_in(coords, rng) for _ in range(4))
            # 3-fold: the two canonical bracketings
            lf = lb(lb(x, y), z)                     # ((x*y)*z)  left-fold
            rf = lb(x, lb(y, z))                     # (x*(y*z))  right-fold
            spreads3.append(nrm(lf - rf))
            assoc3.append(nrm(np.array(loop_associator(list(map(float, x)),
                                                       list(map(float, y)),
                                                       list(map(float, z))), dtype=float)))
            # 4-fold: two of the five distinct bracketings (spread grows with chain length)
            b_left = lb(lb(lb(x, y), z), w)          # (((x*y)*z)*w)
            b_bal = lb(lb(x, y), lb(z, w))           # ((x*y)*(z*w))
            spreads4.append(nrm(b_left - b_bal))
        s3 = float(np.mean(spreads3)); a3 = float(np.mean(assoc3)); s4 = float(np.mean(spreads4))
        order_free = s3 < 1e-9
        print(f"--- {name} ---")
        print(f"  3-fold bracket-spread  mean ||(xy)z - x(yz)|| = {s3:.3e}   "
              f"-> {'ORDER-FREE (no external orderer needed) = SELF-RUNNING' if order_free else 'ORDER-DEPENDENT (an external orderer MUST choose) = NOT self-running'}")
        print(f"  loop_associator norm   mean                  = {a3:.3e}   (0 = associates)")
        print(f"  4-fold bracket-spread  mean (left vs balanced)= {s4:.3e}   "
              f"({'still 0 — every chain length stays order-free' if s4 < 1e-9 else 'GROWS — longer self-composition needs more imposed ordering'})\n")

    print("=== reading ===")
    print("  ORDER-FREE (associator 0, H-core) = the substrate composes its own state in any order / in")
    print("  parallel, with NO external agent picking brackets = SELF-RUNNING (F302 self-authoring).")
    print("  ORDER-DEPENDENT (associator != 0, octonion) = an external orderer must choose the bracketing")
    print("  = an imposed instruction = F302 MACHINE-CODE / F305 gate-model. So octonion-NATIVE self-running")
    print("  is structurally OBSTRUCTED by non-associativity.")
    print("  => biology's (3:4)|(4:3) is the MAXIMAL self-running form of the 7: associative H-core self-runs;")
    print("     the chiral 4-coset is a single DEFINED chirality flip (Class C / Hopf S^7->S^4), not free")
    print("     composition. associativity-enables-self-running is WHY any self-runner lands at (3:4)|(4:3)")
    print("     and not raw k=7 (F299/F300) — the same obstruction F305 named for octonion/qubit hardware.")
    print()
    print("  HONEST BOUNDARY: the bracket-variance is srmech-EXACT; 'order-free = self-running' is the")
    print("  framework reading (composing F302); whether a PHYSICAL substrate can supply a physically-")
    print("  determined bracketing that still counts as self-running is the EXPERT's (physics) question.")


if __name__ == "__main__":
    main()
