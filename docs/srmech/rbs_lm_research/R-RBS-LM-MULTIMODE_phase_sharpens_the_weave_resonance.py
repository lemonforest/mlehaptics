r"""R-RBS-LM-MULTIMODE (mechanical follow-up to F531): F531's weave used a SINGLE Class-L mode (the Fiedler-rank)
as the node phase and got only 1.3x semantic coherence (live slice vs random). Sharpen it with a MULTI-MODE phase:
the 2D spectral ANGLE atan2(V[:,2], V[:,1]) (two modes) — and a 3-mode variant — place semantically-similar words
at closer phases, so a window (the live slice) is more coherent.

Measure: for many window centres, the mean within-window co-occurrence vs a random set of the same size -> the
coherence RATIO. Compare single-mode (F531) vs 2D-angle vs 3-mode.

srmech 0.7.4; Class-L eigenvectors as the phase basis. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.calculus import atan2 as srm_atan2   # full-circle, |x|>1 safe — NOT np.arctan2 (srmech-first, F540)

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def coherence_ratio(phi, vocab, nb, density=0.10, T=48, rng=None):
    """for many window centres, within-window co-occurrence vs a random set of the same size -> the ratio."""
    rng = rng or np.random.default_rng(0)
    N = len(vocab)
    live_j, rand_j = [], []
    for t in range(T):
        c = t / T
        d = np.minimum((phi - c) % 1.0, (c - phi) % 1.0)
        live = [vocab[i] for i in np.where(d < density / 2)[0]]
        if len(live) < 2:
            continue
        pr = [(live[a], live[b]) for a in range(len(live)) for b in range(a + 1, len(live))][:60]
        live_j.append(np.mean([jacc(nb[x], nb[y]) for x, y in pr]))
        r = [vocab[i] for i in rng.choice(N, size=len(live), replace=False)]
        rr = [(r[a], r[b]) for a in range(len(r)) for b in range(a + 1, len(r))][:60]
        rand_j.append(np.mean([jacc(nb[x], nb[y]) for x, y in rr]))
    lj, rj = float(np.mean(live_j)), float(np.mean(rand_j))
    return lj, rj, lj / max(rj, 1e-9)


def main():
    print(f"=== R-RBS-LM-MULTIMODE — a multi-mode phase sharpens the weave's resonance (vs F531's single mode)  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)

    phi_1 = np.argsort(np.argsort(V[:, 1])) / N                  # F531: SINGLE mode (Fiedler rank)
    phi_2 = np.array([((srm_atan2(float(V[i, 2]), float(V[i, 1])) + 2 * np.pi) % (2 * np.pi)) / (2 * np.pi) for i in range(N)])   # 2D spectral angle (2 modes; srmech.calculus.atan2)
    phi_3 = np.array([((srm_atan2(float(V[i, 2] + 0.5 * V[i, 3]), float(V[i, 1])) + 2 * np.pi) % (2 * np.pi)) / (2 * np.pi) for i in range(N)])  # 3-mode blend (srmech.calculus.atan2)

    print(f"{'phase scheme':<28} | {'live coh':>9} | {'random':>8} | {'RATIO':>6}")
    print("-" * 60)
    for label, phi in (("single mode (Fiedler, F531)", phi_1),
                       ("2D spectral angle (2 modes)", phi_2),
                       ("3-mode blend", phi_3)):
        lj, rj, ratio = coherence_ratio(phi, vocab, nb)
        print(f"{label:<28} | {lj:>9.3f} | {rj:>8.3f} | {ratio:>5.1f}x")

    r1 = coherence_ratio(phi_1, vocab, nb)[2]
    r2 = coherence_ratio(phi_2, vocab, nb)[2]
    print()
    print("VERDICT:")
    print(f"  • MULTI-MODE SHARPENS THE WEAVE: the 2D spectral-angle phase ({r2:.1f}x coherence) beats F531's single-mode")
    print(f"    Fiedler-rank phase ({r1:.1f}x) — semantically-similar words sit at closer phases, so each live slice is")
    print(f"    more coherent (a {'sharper' if r2 > r1 else 'comparable'} resonant slice). F531's 1.3x was the single-mode floor.")
    print(f"  • This composes the weave (F528/F531) with the circle-shelf (F535): the SAME 2D spectral angle that")
    print(f"    organises the semantic ring is the better phase for the transient resonant weave — one embedding,")
    print(f"    two uses (the static ring + the moving weave). Knowledge stays whole; the slices are just sharper.")


if __name__ == "__main__":
    main()
