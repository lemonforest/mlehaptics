r"""R-RBS-SNN-LATTICE — continuing the riding assumption past the horizon: a HIGH-fan-in neuron (fan-in > 7) is
addressed as one `SedenionRegister` = the working octonion (≤7 chiral synapses, bit-exact, two hands) STITCHED to
the Hamming carry (the overflow synapses, error-corrected). This is F485's "biology collapses to a handed storage
and CARRIES the rest" made concrete on the shipped §31 register — the cheap path past 𝕆.

The register's two blocks ARE the two regimes the horizon (F487 Test C) predicts:
  - WORKING e0..e7 = neuron-anchor + 7 dominant synapses → couple_working (≤𝕆 reversible, bit-exact) + the two
    chiral hands (σ=±1, F486/F487). Full chirality AND full magnitude precision.
  - CARRY  e8..e15 = the next 4 (overflow) synapses, stored as a Hamming(7,4) codeword of their DIRECTION bits →
    error-corrected. Chirality (direction) PRESERVED + survives a synaptic storage bit-error; magnitude DROPPED.
So an 11-coupling neuron fits one register (7 chiral + 4 carried). The chirality is the invariant carried across
BOTH blocks; bit-exact magnitude is what degrades past the horizon — exactly F485's storage-handed cheap path.
srmech 0.7.4: SedenionRegister.{couple_working,uncouple_working,carry,correct,write,read} + hypercomplex_couple.
"""
import srmech
from srmech.amsc.cascade.sedenion_register import SedenionRegister
from srmech.amsc import cascade as C


def close(a, b, tol2=1e-18):
    return all((a[i] - b[i]) ** 2 < tol2 for i in range(len(a)))


def main():
    print(f"=== R-RBS-SNN-LATTICE — a high-fan-in neuron as one register: 7 chiral + 4 carried  (srmech {srmech.__version__}) ===\n")
    reg = SedenionRegister()

    # an 11-fan-in neuron: 11 directed synapse net-flows (the sign carries direction = chirality; |value| = strength)
    syn = [+0.9, -0.7, +0.5, -0.8, +0.6, -0.4, +0.3, +0.22, -0.18, +0.12, -0.05]
    order = sorted(range(11), key=lambda i: syn[i] ** 2, reverse=True)   # rank by strength² (Class K; no abs())
    work_idx, carry_idx = order[:7], order[7:11]
    work = [syn[i] for i in work_idx]
    print(f"[NEURON] fan-in 11; 7 strongest → working (chiral); 4 weakest → carry (EC):")
    print(f"  working synapses (net-flow): {[round(v,2) for v in work]}")
    print(f"  carry   synapses (net-flow): {[round(syn[i],2) for i in carry_idx]}\n")

    # ===== WORKING BLOCK: neuron + 7 dominant synapses, chirally addressed bit-exact =====
    for s, i in enumerate(work_idx, start=1):
        reg.write(s, f"syn{i}", sign=(1 if syn[i] > 0 else -1))          # symbolic slot + direction
    oct_ = reg.couple_working(work)                                       # the register's native ≤7 store
    rec = reg.uncouple_working(oct_)
    store_ok = close(rec, work)
    hp = C.hypercomplex_couple(work, sigma=+1)                            # the two chiral hands (F486/F487)
    hand_plus = C.hypercomplex_couple(list(hp), sigma=+1, inverse=True)[1:8]
    hand_minus = C.hypercomplex_couple(list(hp), sigma=-1, inverse=True)[1:8]
    hands_ok = close(hand_plus, work) and close(hand_minus, [-v for v in work])
    print("[WORKING e0..e7] neuron-anchor + 7 chiral synapses:")
    print(f"  couple/uncouple round-trip (register store, bit-exact): {store_ok}")
    print(f"  two hands (σ=±1): hand+ = pre→post (recovers), hand− = post→pre (conjugate): {hands_ok}\n")

    # ===== CARRY BLOCK: the 4 overflow synapses' DIRECTION (chirality), Hamming(7,4) error-corrected =====
    dir_bits = [1 if syn[i] > 0 else 0 for i in carry_idx]                # carry the direction = chirality bit
    cw = reg.carry(dir_bits, n=3)                                         # Hamming(7,4) codeword
    corrupted = list(cw); corrupted[3] ^= 1                               # a single synaptic storage bit-error
    res = reg.correct(corrupted)
    ec_ok = res["data"] == dir_bits
    print("[CARRY e8..e15] 4 overflow synapses (direction-only, EC):")
    print(f"  direction bits in: {dir_bits} → Hamming(7,4) codeword {cw}")
    print(f"  after a single synaptic bit-error (pos {res['error_position']}) → correct() recovers: {res['data']}  (EC ok: {ec_ok})")
    print(f"  → chirality (direction) PRESERVED + error-corrected; magnitude DROPPED (the cheap path)\n")

    ok = store_ok and hands_ok and ec_ok
    print("VERDICT (continuing the assumption past the horizon):")
    print(f"  • one SedenionRegister IS the SNN neuron-object: an 11-coupling neuron = 7 chiral (bit-exact, two")
    print(f"    hands) + 4 carried (Hamming-EC direction) — the §31 register's two blocks ARE F487's two regimes.")
    print(f"  • the CHIRALITY is the invariant carried across BOTH blocks (full in working, direction-bit in carry);")
    print(f"    bit-exact MAGNITUDE is what degrades past 𝕆 — exactly F485's storage-handed cheap path. all-ok: {ok}")
    print(f"  • the full SNN = a LATTICE of these registers (each a ≤7-chiral neuron-object + carry), stitched")
    print(f"    neuron-to-neuron — the build-up target (#197/F323). Next rungs: the inter-register stitch (one")
    print(f"    neuron's carry feeding the next's working); navigate-routed read across the lattice; a real")
    print(f"    connectome's fan-in distribution vs the 7/4 split. Ride continues — no better path revealed yet.")


if __name__ == "__main__":
    main()
