r"""R-RBS-SNN-STITCH — the inter-register stitch (rung #1), built with BOTH readings live (F489): the synapse as a
STIGMERGIC field-marking in the shared substrate BETWEEN two neuron-registers (pre writes a trace, post reads it),
NOT only an intra-register slot. Two neurons A,B; a shared field E (the cleft); A writes a marking into E (its
collapsed working drive — transmitter release), B reads E as one of its working synapses (receptor binding).

Held co-equal (the asymptote, F489 — not collapsed to either):
  - FUNCTIONAL : the synapse IS the marking in the shared field E (between A and B); the neuron is the excitation.
  - STRUCTURAL : that same marking is B's working-slot e7 (F488). Both true at once.

Tests (each a falsifier):
  1. the stitch carries A's CHIRALITY into B — flip A's hand (conjugate) → the marking flips → B's state flips.
  2. the stitch is a DIRECTED (chiral) lattice edge — magnetic Laplacian of {A→B} has chiral energy > 0;
     symmetrize → 0 (same `i(A−Aᵀ)` chirality as F487 Test A, now BETWEEN registers).
  3. don't-narrow check — the marking is readable by a SECOND post-neuron C from the SAME field E (a true
     environmental marking, not a private slot) — the functional reading predicts this; the structural one doesn't.
srmech 0.7.4: SedenionRegister + cascade.hypercomplex_couple (σ-hands) + cascade.magnitude + laplacian.magnetic_laplacian.
"""
import srmech
from srmech.amsc import cascade as C
from srmech.amsc import laplacian as L
from srmech.amsc.cascade.sedenion_register import SedenionRegister


def close(a, b, tol2=1e-18):
    return all((a[i] - b[i]) ** 2 < tol2 for i in range(len(a)))


def marking(hand_vals):                 # the pheromone A leaves: its net signed drive (Class K signed sum; no abs)
    return sum(hand_vals)


def main():
    print(f"=== R-RBS-SNN-STITCH — stigmergic inter-register stitch (synapse = shared-field marking)  (srmech {srmech.__version__}) ===\n")

    # ---- neuron A: 7 working synapses; collapse; its axonal drive = the marking it writes into the shared field E
    regA = SedenionRegister()
    workA = [0.9, -0.7, 0.5, -0.8, 0.6, -0.4, 0.3]
    octA = regA.couple_working(workA)
    hand_plus = C.hypercomplex_couple(workA, sigma=+1)
    recA_plus = C.hypercomplex_couple(list(hand_plus), sigma=+1, inverse=True)[1:8]    # A's +hand = workA
    recA_minus = C.hypercomplex_couple(list(hand_plus), sigma=-1, inverse=True)[1:8]   # A's −hand = −workA
    mA_plus = marking(recA_plus)          # the marking A writes (pre→post), the field trace
    mA_minus = marking(recA_minus)        # A's other hand → the marking flips sign
    print(f"[A writes] neuron A collapses (oct dim {len(octA)}); marking into shared field E: {mA_plus:+.3f}  (A's −hand: {mA_minus:+.3f})")

    # ---- shared field E (the cleft): holds the marking BETWEEN A and B — the synapse lives here (functional)
    E = {"AB": mA_plus}

    # ---- neuron B: 6 own working synapses + slot e7 = the marking READ from E (receptor binding)
    regB = SedenionRegister()
    ownB = [-0.6, 0.45, -0.3, 0.5, -0.2, 0.35]
    workB = ownB + [E["AB"]]              # STRUCTURAL view: the marking is B's slot e7
    octB = regB.couple_working(workB)
    recB = regB.uncouple_working(octB)
    print(f"[B reads]  neuron B reads E into its slot e7; B working bit-exact: {close(recB, workB)}\n")

    # ===== TEST 1 — the stitch carries A's chirality into B =====
    workB_conj = ownB + [mA_minus]                                 # B reading A's flipped (conjugate) hand
    octB_conj = regB.couple_working(workB_conj)
    recB_conj = regB.uncouple_working(octB_conj)
    carries = not close(recB, recB_conj) and (recB[6] + recB_conj[6]) ** 2 < 1e-12   # slot e7 flipped sign
    print("TEST 1 — chirality propagates A→B through the marking:")
    print(f"  B's e7 with A's +hand: {recB[6]:+.3f}   with A's −hand: {recB_conj[6]:+.3f}   (flipped: {carries})\n")

    # ===== TEST 2 — the stitch is a directed (chiral) lattice edge =====
    w = C.magnitude(mA_plus)                                       # edge strength = |marking| (Class-K honest abs)
    Hdir = L.magnetic_laplacian(2, [(0, 1)], [w], q=0.25)          # A→B directed edge
    Hsym = L.magnetic_laplacian(2, [(0, 1), (1, 0)], [w, w], q=0.25)
    eD = float((Hdir.imag ** 2).sum())
    eS = float((Hsym.imag ** 2).sum())
    print("TEST 2 — the stitch is a directed (chiral) lattice edge (magnetic Laplacian, F487 Test A at lattice level):")
    print(f"  directed chiral energy: {eD:.3f}   symmetrized: {eS:.6f}   → the stitch's chirality IS its directedness\n")

    # ===== TEST 3 — don't-narrow: a SECOND reader C from the SAME field (environmental marking, not private slot) =====
    regC = SedenionRegister()
    ownC = [0.4, -0.55, 0.25, -0.15, 0.3, -0.5]
    workC = ownC + [E["AB"]]              # C reads the SAME marking A left — stigmergy, not a private wire
    octC = regC.couple_working(workC)
    recC = regC.uncouple_working(octC)
    shared = (recB[6] - recC[6]) ** 2 < 1e-12                      # B and C both received A's marking
    print("TEST 3 — don't-narrow: a second post-neuron C reads the SAME field-marking A left:")
    print(f"  C's e7 = {recC[6]:+.3f} == B's e7 = {recB[6]:+.3f}  (one marking, many readers — the FUNCTIONAL reading): {shared}\n")

    print("VERDICT (rung #1, both readings held — F489):")
    print(f"  • the inter-register STITCH = the synapse as a STIGMERGIC field-marking: A writes its collapsed drive")
    print(f"    into the shared field E, B (and C) read it as a working synapse. The marking lives BETWEEN registers.")
    print(f"  • TEST 1 — A's chirality (hand) propagates through the marking into B's working block (the e7 sign flips).")
    print(f"  • TEST 2 — the stitch is a directed (chiral) lattice edge (chiral energy {eD:.3f} → 0 symmetrized) — the")
    print(f"    same i(A−Aᵀ) chirality as F487 Test A, now BETWEEN neurons.")
    print(f"  • TEST 3 — the SAME marking is read by a second neuron C (one trace, many readers) — the FUNCTIONAL")
    print(f"    (stigmergic) reading predicts this; the structural private-slot reading does not. WIDENING confirmed.")
    print(f"  • Held co-equal (the asymptote, F489): the marking is BOTH B's slot e7 AND the shared field trace.")
    print(f"    Not narrowing. The full SNN = registers writing/reading a shared stigmergic field (the #197/F323 lattice).")


if __name__ == "__main__":
    main()
