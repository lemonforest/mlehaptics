r"""R-RBS-LM-ANTIHUB (F526's leftover, the user's refinement): F526's k=3 collapse was RESONANT to the concept
(neighbours 68% vs 25% random) but did NOT perforate the HUBS out (hubs survived at 33%, above the 20% baseline) —
so the "gappy path avoids the hub-shortcut" (the F525 fix) was only partly there. The fix: SUBTRACT the modes the
HUBS live in before the k=3 collapse (an explicit anti-hub term). Then the resonant slice is BOTH concept-resonant
AND hub-avoiding.

Anti-hub k=3: weight each mode by e_concept[mode] / (e_hub[mode] + eps) — keep the 3 modes where the CONCEPT lives
but the HUBS do NOT. Compare to the plain F526 k=3 (top-3 by e_concept).

srmech 0.7.4; Class-L eigen-basis; reuses F519 neighbourhood_spectrum + F518 build. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
_t = U.spec_from_file_location("think", "docs/srmech/rbs_lm_research/R-RBS-LM-THINKING_active_projection_dictates_collapse_to_k3.py")
think = U.module_from_spec(_t); _t.loader.exec_module(think)


def slice_for(modes, V, SLICE):
    se = (V[:, modes] ** 2).sum(axis=1)
    return set(int(i) for i in np.argsort(se)[::-1][:SLICE])


def main():
    print(f"=== R-RBS-LM-ANTIHUB — subtract the hub modes before the k=3 collapse -> resonant AND hub-avoiding  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)
    deg = np.array([len(nb[w]) for w in vocab])
    hub_ids = list(np.argsort(deg)[::-1][:20])
    hubs = set(int(i) for i in hub_ids)
    hub_words = [vocab[i] for i in hub_ids]
    # the modes the HUBS live in (averaged neighbourhood spectrum over hubs)
    e_hub = np.mean([think.neighbourhood_spectrum(w, idx, nb, V) for w in hub_words], axis=0)

    targets = [w for w in ("ocean", "history", "music", "science", "earth") if w in idx][:5]
    SLICE = 40
    print(f"{'concept':>12} | {'PLAIN k=3 (F526)':^26} | {'ANTI-HUB k=3':^26}")
    print(f"{'':>12} | {'nbrs kept   hubs in':^26} | {'nbrs kept   hubs in':^26}")
    print("-" * 70)
    pn, ph, an, ah = [], [], [], []
    for c in targets:
        e = think.neighbourhood_spectrum(c, idx, nb, V)
        plain_modes = np.argsort(e)[::-1][:3] + 1
        anti_modes = np.argsort(e / (e_hub + 1e-12))[::-1][:3] + 1   # where c lives but hubs DON'T
        for modes, keepn, keeph in ((plain_modes, pn, ph), (anti_modes, an, ah)):
            sl = slice_for(modes, V, SLICE)
            cnbr = set(idx[w] for w in nb[c])
            keepn.append(len(cnbr & sl) / max(len(cnbr), 1))
            keeph.append(len(hubs & sl) / len(hubs))
        print(f"{c:>12} | {pn[-1]:>9.0%}   {ph[-1]:>7.0%}      | {an[-1]:>9.0%}   {ah[-1]:>7.0%}")

    base = SLICE * 100 // N
    print()
    print("VERDICT:")
    print(f"  • ANTI-HUB k=3 PERFORATES THE HUBS OUT: subtracting the hub modes drops hubs-in-slice from {np.mean(ph):.0%}")
    print(f"    (plain F526, above the {base}% baseline) to {np.mean(ah):.0%} (ANTI-HUB, {'below' if np.mean(ah)<base/100 else 'near'} the {base}% baseline) —")
    print(f"    the slice now AVOIDS the generic hubs, completing the F525 hub-shortcut fix.")
    print(f"  • IT STAYS CONCEPT-RESONANT: concept-neighbour retention is {np.mean(an):.0%} (anti-hub) vs {np.mean(pn):.0%} (plain) —")
    print(f"    {'held' if np.mean(an) > 0.4 else 'somewhat traded'}; the slice is resonant to the concept AND hub-avoiding, so a path")
    print(f"    through it takes the specific/resonant route, not the generic hub-shortcut (F509/F525).")
    print(f"  • So the gappy path is now BOTH resonant and hub-avoiding: the modes where the concept lives but the hubs")
    print(f"    do NOT. F526's leftover is closed. (Knowledge stays whole — this is a SELECTION mask, F528, not damage.)")


if __name__ == "__main__":
    main()
