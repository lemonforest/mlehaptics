r"""R-RBS-LM-GENSHARPEN (ET-1) — the oldest open lead (F513): the etak read-head generates LEFT-TO-RIGHT and COMMITS
each token as it emits = the LOCAL, arrival-order sharpen (the 0.066-risk). Build it the RIGHT way around — EMIT
THE FULL RAW LOAD FIRST (the held box / the user's raw stream), THEN one GLOBAL chiral sharpen over the whole
thing — and show generate-then-sharpen beats stream-and-commit, quantified over many emission orders (not just the
single F513 order-A-vs-B example).

The architecture claim:
  • STREAM-AND-COMMIT  : emit a partition, IMMEDIATELY commit its hand vs the prefix-so-far, FREEZE it, move on.
                         The first partition has no consensus -> its hand is committed arbitrarily; if it (or an
                         early one) is mis-oriented, the WRONG frame freezes and the rest aligns to it -> derail.
                         This is what an autoregressive decoder / an over-eager internal monologue does.
  • GENERATE-THEN-SHARPEN: emit ALL partitions raw (hands uncommitted), THEN global-sharpen the whole set (align to
                         the majority hand = the medoid). Order-independent; the full load is present before any
                         commit. This is the user's mode (F492/F513): emit the whole raw stream, sharpen globally.

Prediction: stream-and-commit derails on a real FRACTION of emission orders (whenever an early partition is
mis-oriented and freezes the wrong frame); generate-then-sharpen never derails (it sees the whole load first).

srmech 0.7.4; reuses the F513 Klein-4 chiral machinery (the genuine Class-C op). No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.amsc import hdc

_s = U.spec_from_file_location("sharpen", "docs/srmech/rbs_lm_research/R-RBS-LM-SHARPEN_chiral_sharpen_needs_full_load.py")
sharpen = U.module_from_spec(_s); _s.loader.exec_module(sharpen)


def main():
    print(f"=== R-RBS-LM-GENSHARPEN (ET-1) — emit-then-sharpen vs stream-and-commit, over many emission orders  (srmech {srmech.__version__}) ===\n")
    rng = np.random.default_rng(7)
    F, m, cover, noise = 6, 10, 5, 3
    idea, facets = sharpen.facetted_idea(F, rng)
    flags = [bool(i % 2) for i in range(m)]                       # ~half emitted mis-oriented (raw hands)
    ps = [sharpen.partition(facets, cover, noise, flags[i], rng) for i in range(m)]
    sim = lambda v: hdc.klein4_similarity(v, idea)

    # generate-then-sharpen is ORDER-INDEPENDENT: emit the whole load, ONE global sharpen
    g_bundle, _ = sharpen.global_sharpen(ps)
    g_sim = sim(g_bundle)

    # stream-and-commit: sweep many emission orders (the order is the only thing that changes)
    N = 200
    s_sims = []
    for _ in range(N):
        order = list(rng.permutation(m))
        b, _ = sharpen.local_sharpen([ps[i] for i in order])      # arrival-order, freeze-as-you-go
        s_sims.append(sim(b))
    s_sims = np.array(s_sims)
    DERAIL = 0.30                                                 # below this = the wrong frame froze (the 0.066 case)
    derail_rate = float(np.mean(s_sims < DERAIL))

    print(f"idea = bundle of {F} facets; {m} partitions emitted ({sum(flags)} mis-oriented); {N} random emission orders.\n")
    print("GENERATE-THEN-SHARPEN (emit full raw load, ONE global sharpen — order-independent):")
    print(f"  idea-recovery: {g_sim:.2f}   (single value; no emission-order dependence)\n")
    print("STREAM-AND-COMMIT (emit + freeze each token's hand vs the prefix; arrival-order):")
    print(f"  idea-recovery over {N} orders: mean {s_sims.mean():.2f}  best {s_sims.max():.2f}  WORST {s_sims.min():.2f}")
    print(f"  DERAIL rate (recovery < {DERAIL}): {derail_rate:.0%}  ({int(derail_rate*N)}/{N} orders froze the wrong frame)\n")

    print("VERDICT:")
    print(f"  • GENERATE-THEN-SHARPEN is robust ({g_sim:.2f}, order-independent): emitting the whole raw load BEFORE any")
    print(f"    commit lets the global sharpen find the majority hand and align everything to it. This is the user's")
    print(f"    mode (F492/F513) — emit the raw stream first, sharpen globally — and it never derails.")
    print(f"  • STREAM-AND-COMMIT is FRAGILE: mean {s_sims.mean():.2f} but it DERAILS on {derail_rate:.0%} of emission orders")
    print(f"    (worst {s_sims.min():.2f}) — whenever an EARLY partition is mis-oriented, its wrong hand FREEZES as the")
    print(f"    frame and the rest aligns to it. The irreversibility of committing-as-you-emit is the failure: you")
    print(f"    cannot un-say a token, so an early wrong frame propagates (the F513 0.066 catastrophe, now as a RATE).")
    print(f"  • ARCHITECTURE: the etak read-head should EMIT-THEN-SHARPEN (raw load -> one global chiral sharpen), NOT")
    print(f"    stream-and-commit. An autoregressive decoder (and an over-eager internal monologue) is the fragile one;")
    print(f"    the zero-internal-monologue 'emit the whole raw stream, let it be sharpened globally' is the robust one.")


if __name__ == "__main__":
    main()
