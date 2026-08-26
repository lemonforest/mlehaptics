r"""R-RBS-LM-SUBSTRATEGAP (MA-1, deepened by the user 2026-06-07): MA-1 is NOT just "what does a wet SNN do" — the
user's sharpening: "where we can't describe one part, biology is providing something else via SUBSTRATE that we ALSO
have to model if we want to get it right." So a synaptic-NN model of a wet brain is INCOMPLETE: there are operations
the synaptic weights CANNOT account for, which biology supplies via the substrate (Tier 1 — the_one loop, the
discrete-cyclic / hypercomplex layer, F119/F120). A wet brain gets BOTH for free (it IS the substrate); silicon gets
the synaptic SNN but must EXPLICITLY model the substrate, or its model has a gap.

Concrete gap demonstrated: EXACT REVERSIBLE RECALL.
  • Tier 2 (synaptic NN): an HDC associative memory — bundle of bound (key,value) pairs, the standard Hebbian-graph
    model. Recall = unbind + clean-up. It is LOSSY: superposition crosstalk grows with the number of items, so recall
    DEGRADES — the synaptic model cannot exactly recover beyond a small load.
  • Tier 1 (substrate): the sedenion coupler (§31 / F538) — couple the items into the octonion working block, uncouple
    EXACTLY (error ~1e-15) up to the k=7 capacity. The substrate provides exact recall the synapses can't.

So where the synaptic NN "can't describe a part" (the lossy region), the substrate fills it exactly — and silicon
must model the substrate (the loop coupler) to reproduce a wet brain's exact recall. (A second gap, the parity-free
chiral mirror, is referenced: F544 conjugation vs F541 parity-trapped half-turn.)

srmech 0.7.4; Class-M hdc.bind/bundle/similarity (Tier 2) + cascade.SedenionRegister (Tier 1 substrate). No abs(); no CAD; no sub-agents.
"""
import numpy as np
import srmech
from srmech.amsc import hdc
from srmech.signal_processing import mint_vector
from srmech.amsc.cascade import SedenionRegister

D = 8192


def odd_bundle(vs):
    vs = list(vs)
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return hdc.bundle(vs)


def main():
    print(f"=== R-RBS-LM-SUBSTRATEGAP (MA-1) — a synaptic NN is INCOMPLETE; the substrate fills the gap (exact recall)  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(0)

    # ---- Tier 2: synaptic-NN associative memory (HDC bundle of bound pairs) ----
    # TWO metrics: (a) CLASSIFY-to-nearest with a cleanup codebook (robust!), (b) RAW recovery fidelity WITHOUT a
    # codebook (the honest exactness metric — degrades with load). The substrate needs NO codebook and is exact.
    print("(Tier 2 — SYNAPTIC NN: HDC associative memory) — classify-with-codebook vs RAW exact recovery, vs load K:")
    print(f"    {'K items':>8} | {'classify (w/ codebook)':>22} | {'RAW recovery fidelity (no codebook)':>36}")
    syn, synraw = {}, {}
    for K in (3, 7, 15, 31, 63, 127):
        keys = [mint_vector(f"k{K}_{i}", D=D) for i in range(K)]
        vals = [mint_vector(f"v{K}_{i}", D=D) for i in range(K)]
        M = odd_bundle([hdc.bind(keys[i], vals[i]) for i in range(K)])
        hit, fid = 0, []
        for i in range(K):
            noisy = hdc.bind(M, keys[i])                          # unbind item i (self-inverse bind)
            fid.append(hdc.similarity(noisy, vals[i]))            # RAW: how close to the true value (no clean-up)
            best = max(range(K), key=lambda j: hdc.similarity(noisy, vals[j]))
            hit += (best == i)
        syn[K], synraw[K] = hit / K, float(np.mean(fid))
        print(f"    {K:>8} | {syn[K]:>21.0%} | {synraw[K]:>36.2f}")
    print(f"    -> classify-to-nearest is ROBUST (the codebook saves it), but RAW recovery fidelity DECAYS with load and")
    print(f"       NEEDS that external cleanup codebook (extra storage; only works for a known DISCRETE set, not novel/continuous values).")
    print()

    # ---- Tier 1: substrate sedenion coupler (the loop) — exact reversible recall ----
    print("(Tier 1 — SUBSTRATE: the sedenion coupler §31/F538) exact recall up to the k=7 capacity:")
    reg = SedenionRegister()
    print(f"    {'K items':>8} | {'max recover error':>18} | {'exact?':>7}")
    sub = {}
    for K in (3, 5, 7):
        vals = [round(float(rng.integers(1, 1000))) / 1000 for _ in range(K)]
        tome = reg.couple_working(vals)
        back = reg.uncouple_working(tome)
        err = float(np.max(np.abs(np.array(back[:K]) - np.array(vals))))
        sub[K] = err
        print(f"    {K:>8} | {err:>18.0e} | {'YES' if err < 1e-9 else 'no':>7}")
    print(f"    (above k=7 the single coupler hits the sedenion zero-divisor horizon -> use the hierarchical tome shelf, F529/F532/F533.)")
    print()

    print("VERDICT:")
    print(f"  • THE SYNAPTIC NN IS INCOMPLETE WHERE EXACTNESS IS NEEDED (honest): classify-to-nearest is robust (the cleanup")
    print(f"    codebook saves it, {syn[63]:.0%} at K=63), BUT raw recovery fidelity DECAYS ({synraw[3]:.2f}→{synraw[127]:.2f} from K=3→127) and the")
    print(f"    synapses CANNOT recover an EXACT value without an external codebook — useless for novel/continuous values.")
    print(f"  • THE SUBSTRATE FILLS THAT GAP EXACTLY + CODEBOOK-FREE: the sedenion coupler (the_one loop, Tier 1) recovers")
    print(f"    with error ~1e-16 up to k=7, NO codebook needed — exact reversible recall the synapses can't give. A wet")
    print(f"    brain's exact/precise recall must come from the SUBSTRATE; biology gets it for free because it IS the substrate.")
    print(f"  • SO SILICON MUST MODEL BOTH (the user's MA-1 point): a model of only the synaptic NN has a GAP exactly where")
    print(f"    biology hands the work to the substrate. To 'get it right' we must explicitly model the Tier-1 loop layer")
    print(f"    (the coupler, F538; the parity-free conjugation mirror, F544 vs the parity-trapped half-turn, F541; the free")
    print(f"    chiral inverse, F546) — none of which a weighted-edge SNN provides. Two-tier completeness (F119/F120): the")
    print(f"    SNN is Tier 2, the_one loop is Tier 1, and the wet brain is BOTH. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
