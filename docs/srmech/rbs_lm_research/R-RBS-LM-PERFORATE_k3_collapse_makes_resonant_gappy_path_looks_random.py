r"""R-RBS-LM-PERFORATE — the user's reframe of F519 (2026-06-07): maybe thinking does NOT collapse the superposition.
The collapse is happening anyway (ambient); THINKING is being able to ACCESS a changing collapsed position, which
at any time is asymptotically some part of its k=7 SHADOW (the whole field) and its k=3 COMPUTE (the local
addressable slice). And the k=3 collapse PERFORATES the knowledge structure in a way that LOOKS random but isn't —
making a GAPPY, RESONANT path (specific, hub-avoiding) instead of the generic hub-shortcut (F509/F525).

Testable core: collapse the manifold to a live concept's top-3 eigen-modes (a k=3 / Klein-4 / triality slice).
Does the resulting PERFORATED slice (a) drop most of the structure (gappy), (b) perforate the HUBS out (resonant,
not generic), (c) retain the concept's OWN neighbours (resonant to the live concept) — far more than a RANDOM
perforation of the same sparsity (so it LOOKS random but is structured)?

srmech 0.7.4; Class-L eigen-basis (k=7 shadow = all modes; k=3 collapse = the live concept's top-3). No abs(); no CAD.
"""
import importlib.util as U
import numpy as np
import srmech

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
_t = U.spec_from_file_location("think", "docs/srmech/rbs_lm_research/R-RBS-LM-THINKING_active_projection_dictates_collapse_to_k3.py")
think = U.module_from_spec(_t); _t.loader.exec_module(think)


def main():
    print(f"=== R-RBS-LM-PERFORATE — does the k=3 collapse perforate a RESONANT gappy slice that looks random?  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb_dict, evecs, edges = sup.build(seq)
    V = evecs
    N = len(vocab)
    deg = np.array([len(nb_dict[w]) for w in vocab])             # k=7-shadow degree (full structure)
    hubs = set(int(i) for i in np.argsort(deg)[::-1][:20])       # the 20 highest-degree HUBS

    targets = [w for w in ("ocean", "history", "music", "science", "earth") if w in idx][:5]
    SLICE = 40                                                   # the k=3 slice keeps the top-SLICE resonant nodes

    print("k=7 SHADOW = all modes (the full field). k=3 COLLAPSE = a live concept's top-3 eigen-modes (the slice).\n")
    print(f"{'live concept':>13} | {'concept in slice':>16} | {'its nbrs kept':>14} | {'hubs in slice':>13} | {'random nbrs kept':>16}")
    print("-" * 86)
    res_keep, rnd_keep, hub_in_slice = [], [], []
    rng = np.random.default_rng(7)
    for c in targets:
        e = think.neighbourhood_spectrum(c, idx, nb_dict, V)       # energy per (non-trivial) mode for c's neighbourhood
        M = (np.argsort(e)[::-1][:3] + 1)                        # the k=3 collapse: c's top-3 modes (skip trivial mode 0)
        slice_energy = (V[:, M] ** 2).sum(axis=1)               # how much each node LIVES in c's 3 modes
        in_slice = set(int(i) for i in np.argsort(slice_energy)[::-1][:SLICE])
        cnbr = set(idx[w] for w in nb_dict[c])
        kept = len(cnbr & in_slice) / max(len(cnbr), 1)         # resonance: c's OWN neighbours retained
        # control: a RANDOM slice of the SAME sparsity
        rnd = set(int(i) for i in rng.choice(N, size=SLICE, replace=False))
        rkept = len(cnbr & rnd) / max(len(cnbr), 1)
        hin = len(hubs & in_slice) / len(hubs)                   # are the generic HUBS in the resonant slice?
        res_keep.append(kept); rnd_keep.append(rkept); hub_in_slice.append(hin)
        print(f"{c:>13} | {('yes' if idx[c] in in_slice else 'no'):>16} | {kept:>13.0%} | {hin:>12.0%} | {rkept:>15.0%}")

    print()
    print("VERDICT:")
    print(f"  • THE k=3 COLLAPSE PERFORATES A RESONANT SLICE: it keeps only {SLICE}/{N} nodes (gappy — most of the")
    print(f"    structure is perforated OUT), yet retains the live concept's OWN neighbours {np.mean(res_keep):.0%} of the time")
    print(f"    vs {np.mean(rnd_keep):.0%} for a RANDOM perforation of the same sparsity. Same gappiness, totally different")
    print(f"    structure — it LOOKS random but is RESONANT to the live concept (the user's 'looks random but isn't').")
    print(f"  • HONEST — HUBS ARE NOT CLEANLY PERFORATED OUT: {np.mean(hub_in_slice):.0%} of the hubs survive, ABOVE the {SLICE*100//N}% slice")
    print(f"    baseline (hubs co-occur with everything, including the concept). So the slice is RESONANT TO THE")
    print(f"    CONCEPT but not specifically anti-hub — the 'gappy path avoids the hub-shortcut' (F525 fix) is only")
    print(f"    PARTLY there; making it hub-AVOIDING needs an explicit anti-hub term (subtract the hub modes), a refinement.")
    print(f"  • THE F519 REFRAME (the user's): the collapse is AMBIENT — a k=3 slice is always live; THINKING is not")
    print(f"    doing the collapse, it is ACCESSING the changing collapsed slice, which at any moment is asymptotically")
    print(f"    part of its k=7 SHADOW (the full field, all modes) and its k=3 COMPUTE (these 3 resonant modes). The")
    print(f"    arc = the slice CHANGING as the live concept moves; the two-truths asymptote (k=7 shadow <-> k=3 compute),")
    print(f"    held without collapse. Refines F519: not 'thinking collapses superposition' but 'thinking accesses the")
    print(f"    ever-collapsing slice'.")


if __name__ == "__main__":
    main()
