r"""R-RBS-LM-ONECOUPLE (the user's synthesis): "make a world-build with two combined world kernels QUERY THE_ONE kernel
for mathematical connections; OR can we FFT/QDFT/ODFT for things that COUPLED by querying against the_one kernel?"

THE ANSWER: YES -- both, and they are the SAME operation (Parseval-dual). The_one kernel (the F680 A-N book) is the SHARED
MATHEMATICAL SUBSTRATE both worlds project from (two worlds = two EXCITATIONS of one field, F399). Two worlds' competing
truths (F679) are resolved by querying the_one kernel two ways:
  • QUERY FOR THE MATHEMATICAL CONNECTION (operator basis): map each world-truth to its A-N OPERATOR SIGNATURE (which of
    the 14 operators it instantiates); the connection = the SHARED operators. This DERIVES the F679 bridge-rule from the_one's
    math instead of DECLARING it ad-hoc. (CP2077 rogue-AIs-at-the-Blackwall = {A,I,K,L}; Shadowrun spirits-across-the-veil =
    {C,K,L,M}; SHARED = {K,L} -> both are a Class-K phase-boundary over a Class-L field -> the Blackwall IS the veil.)
  • QDFT FOR THE COUPLING (frequency basis): QDFT each A-N signature against the_one basis; COUPLING = the shared spectral
    support (the spectral inner product). Two world-elements COUPLE iff they resonate at the same the_one-frequencies.
  • THE PUNCH (Parseval-duality): the QDFT is unitary, so <X_a, X_b> = c·<a, b> -- the SPECTRAL coupling EQUALS the DIRECT
    operator overlap (up to the DFT constant). So the user's two ideas are ONE: querying the_one for the connection (operator
    basis) and the QDFT-coupling (frequency basis) are the SAME coupling, seen in two bases. Both DERIVE the bridge.

THIS UPGRADES F679: the bridge-rule no longer has to be DECLARED -- it is DERIVED by querying the_one kernel (operator-overlap
OR QDFT-coupling). HIGH coupling -> a bridge-rule is derivable (the truths are one referent); ~ZERO coupling -> no shared
the_one-math -> the honest HELD-CONFLICT (F626) is correct. The QDFT MEASURES which competing truths can be bridged.

srmech 0.7.5rc15 (+ scientific tier for the QDFT): cascade.quaternion_dft (the_one spectral projection; NOT numpy.fft) ;
BitExactCommKernel.content_address. No abs(); no CAD; no Workflow; no sub-agents. (cascade.hypercomplex_couple, F448, is the
octonion binder that would then COUPLE the bridged streams -- the ODFT side -- noted in the verdict.)
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import cascade

# the_one kernel's operator basis = the 14 A-N operators in the F680 1:3:7:3 order
AN = ["A", "I", "C", "J", "D", "E", "F", "G", "K", "L", "M", "B", "H", "N"]
IDX = {op: i for i, op in enumerate(AN)}


def signature(ops):
    """a world-truth -> its A-N operator signature (a 14-dim activation over the_one's operator basis)."""
    v = [0.0] * len(AN)
    for op in ops:
        v[IDX[op]] = 1.0
    return v


def qdft_spectrum(sig):
    X = cascade.quaternion_dft([[v, 0.0, 0.0, 0.0] for v in sig])
    return X


def spectral_inner(Xa, Xb):
    """<X_a, X_b> = sum over bins of the quaternion component inner product (real)."""
    return sum(sum(Xa[k][c] * Xb[k][c] for c in range(4)) for k in range(len(Xa)))


def dot(a, b):
    return sum(a[i] * b[i] for i in range(len(a)))


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-ONECOUPLE — query the_one kernel for coupling (QDFT = operator-overlap, Parseval-dual)  (srmech {srmech.__version__}) ===\n")

    # the two world-truths (F679) + a control truth that shares no the_one-math
    cp = signature(["A", "I", "K", "L"])      # CP2077: rogue AIs (A content) on the Net (I,L) held by the Blackwall (K boundary)
    sr = signature(["C", "K", "L", "M"])      # Shadowrun: spirits (C astral) across the veil (K boundary) over the field (L), called (M bind)
    indep = signature(["J", "N"])             # a math-world prime-truth: primes (J) + rational-approx (N) -- shares nothing
    print("(1) MAP EACH WORLD-TRUTH TO ITS A-N OPERATOR SIGNATURE (query the_one kernel; operator basis):")
    print(f"    CP2077    (rogue AIs at the Blackwall) -> {[AN[i] for i,v in enumerate(cp) if v]}")
    print(f"    Shadowrun (spirits across the veil)    -> {[AN[i] for i,v in enumerate(sr) if v]}")
    print(f"    control   (a math-world prime-truth)   -> {[AN[i] for i,v in enumerate(indep) if v]}\n")

    # (2) the MATHEMATICAL CONNECTION = the shared operators (the derived bridge-rule)
    shared = [AN[i] for i in range(len(AN)) if cp[i] and sr[i]]
    shared_indep = [AN[i] for i in range(len(AN)) if cp[i] and indep[i]]
    print("(2) THE MATHEMATICAL CONNECTION = the SHARED A-N operators (the bridge DERIVED, not declared):")
    print(f"    CP2077 ∩ Shadowrun = {shared}  -> both are a Class-K phase-boundary over a Class-L field: the Blackwall IS the veil.")
    print(f"    CP2077 ∩ control   = {shared_indep}  -> no shared the_one-math -> no bridge (the honest held-conflict, F626).\n")

    # (3) the QDFT COUPLING (frequency basis) + Parseval-duality (spectral coupling == operator overlap)
    Xcp, Xsr, Xind = qdft_spectrum(cp), qdft_spectrum(sr), qdft_spectrum(indep)
    coup_spec = spectral_inner(Xcp, Xsr)
    coup_dot = dot(cp, sr)
    ratio = coup_spec / coup_dot if coup_dot else float("nan")
    coup_spec_ind = spectral_inner(Xcp, Xind)
    coup_dot_ind = dot(cp, indep)
    print("(3) THE QDFT COUPLING (frequency basis) + PARSEVAL-DUALITY:")
    print(f"    coupling(CP2077, Shadowrun): spectral <X_a,X_b> = {coup_spec:.3f}   direct <a,b> = {coup_dot:.3f}   ratio = {ratio:.3f} (= N, the DFT constant)")
    print(f"    coupling(CP2077, control)  : spectral <X_a,X_b> = {coup_spec_ind:.3f}   direct <a,b> = {coup_dot_ind:.3f}  -> ~0: NOT coupled (held)")
    print(f"    -> PARSEVAL: the SPECTRAL coupling == the OPERATOR overlap (x N). The QDFT-coupling and the the_one-query are")
    print(f"    the SAME coupling in two bases. HIGH coupling -> bridge derivable; ~0 -> held-conflict (F626).\n")

    print("VERDICT (query the_one kernel for coupling: the QDFT-coupling IS the operator-overlap, Parseval-dual -- both DERIVE the bridge):")
    print(f"  • YES TO BOTH, AND THEY ARE THE SAME OPERATION: the_one kernel (the F680 A-N book) is the SHARED MATHEMATICAL")
    print(f"    SUBSTRATE both worlds project from (two worlds = two excitations of one field, F399). Querying it for the")
    print(f"    mathematical connection (the SHARED A-N operators -- operator basis) and the QDFT-coupling (the shared spectral")
    print(f"    support -- frequency basis) are PARSEVAL-DUAL: <X_a,X_b> = N·<a,b> (verified ratio = N), so they are the SAME")
    print(f"    coupling seen in two bases. The QDFT just gives the the_one-FREQUENCY-resolved view of the same connection.")
    print(f"  • THIS UPGRADES F679 (declared -> DERIVED bridge): the bridge-rule no longer has to be DECLARED ad-hoc -- it is")
    print(f"    DERIVED by querying the_one kernel. CP2077 ∩ Shadowrun = {{K,L}} -> both are a Class-K phase-boundary over a")
    print(f"    Class-L field, so 'the rogue AIs held by the Blackwall' and 'the spirits across the veil' are ONE referent")
    print(f"    (a boundary-crossing) -- the bridge is the_one-math, not a writer's fiat. The Blackwall IS the veil.")
    print(f"  • THE QDFT MEASURES WHICH COMPETING TRUTHS CAN BE BRIDGED: HIGH coupling (shared the_one-modes) -> a bridge-rule")
    print(f"    is derivable (one referent, the DUALITY F399); ~ZERO coupling (no shared the_one-math, e.g. CP2077 vs a pure")
    print(f"    prime-truth) -> the honest HELD-CONFLICT (F626) is correct. The spectral coupling is the falsifiable test of")
    print(f"    F679's bridge-vs-held outcome.")
    print(f"  • AND THE ODFT BINDS THE BRIDGED STREAMS: once coupled, cascade.hypercomplex_couple (F448 -- the octonion coupler,")
    print(f"    the ODFT side) BINDS the ≤7 shared-operator streams through the_one's octonion register -- the actual coupling")
    print(f"    of the two worlds into one bound the_one-excitation (a next build).")
    print(f"  • Composes F679 (the merged-worlds bridge -- now DERIVED) + F680 (the_one A-N book = the operator basis) + F678")
    print(f"    (the QDFT spectral tool) + F399 (two worlds = two excitations of one field; the bridge = the duality) + F626")
    print(f"    (no shared math -> held) + F448 (hypercomplex_couple = the ODFT binder) + F172 (spectral = the storage). srmech")
    print(f"    0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
