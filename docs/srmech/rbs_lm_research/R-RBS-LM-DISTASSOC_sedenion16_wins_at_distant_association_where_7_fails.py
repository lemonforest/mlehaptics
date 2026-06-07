r"""R-RBS-LM-DISTASSOC (thread-pull from F547, 2026-06-07): F547 found the live-7 + sedenion-16 hybrid gives NO lift on
NEIGHBOUR recall (the far chord is the wrong tool for that), but predicted the two circles are complementary
RELATIONS — the 7 for local neighbours, the 16 for DISTANT ASSOCIATION. This is the test of that prediction, on the
metric where the 16 SHOULD win: retrieving a word's DISTANT associates (2-hop co-occurrence — related via a bridge,
NOT direct neighbours).

If the prediction holds: the local 7-circle (great at 1-hop, F547=82%) is POOR at 2-hop-only associates (they're not
local by construction), while the sedenion-16's far-chord tome (the distant-semantic partner, F540) recovers MORE of
them. Each circle wins on its OWN relation — the complementarity F547 claimed, now on the discriminating metric.

This also connects the stale cross-navigation / "ride" work (R-RBS-LM-54k cross-kernel triangulation; F189 grammar-
walked-via-logic): the distant-association relation IS the cross-navigation bridge.

srmech 0.7.4; Class-L spectral ring via srmech.calculus.atan2 at NT=7 and NT=16. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech
from srmech.calculus import atan2 as srm_atan2

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
TWO_PI = 6.283185307179586


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def main():
    print(f"=== R-RBS-LM-DISTASSOC — does the sedenion-16 WIN at distant association where the local-7 fails? (F547 thread)  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)
    ang = np.array([(srm_atan2(float(V[i, 2]), float(V[i, 1])) + TWO_PI) % TWO_PI for i in range(N)])

    def tomes_for(NT):
        tof = (ang / TWO_PI * NT).astype(int) % NT
        return tof, [[i for i in range(N) if tof[i] == t] for t in range(NT)]
    t7, T7 = tomes_for(7)
    t16, T16 = tomes_for(16)

    def tsim16(a, b):
        pa, pb = T16[a], T16[b]
        if not pa or not pb:
            return 0.0
        return float(np.mean([jacc(nb[vocab[x]], nb[vocab[y]]) for x in pa[:8] for y in pb[:8]]))

    probes = [w for w in ("ocean", "history", "music", "science", "earth", "light", "war", "city", "world", "river", "time", "life") if w in idx]
    loc1_7, loc1_16, dist_7, dist_16 = [], [], [], []
    for w in probes:
        one_hop = nb[w]
        if not one_hop:
            continue
        two_hop = set()                                          # DISTANT associates: 2-hop minus 1-hop minus self
        for u in one_hop:
            two_hop |= nb[u]
        distant = two_hop - one_hop - {w}
        if not distant:
            continue
        a7, a16 = t7[idx[w]], t16[idx[w]]
        local7 = {vocab[x] for t in (a7, (a7 + 1) % 7, (a7 - 1) % 7) for x in T7[t]}
        far = max((t for t in range(16) if min((t - a16) % 16, (a16 - t) % 16) >= 3),
                  key=lambda t: tsim16(a16, t), default=(a16 + 8) % 16)
        far16 = {vocab[x] for x in T16[far]}
        loc1_7.append(len(one_hop & local7) / len(one_hop))      # 1-hop recall (F547: local circle wins)
        loc1_16.append(len(one_hop & far16) / len(one_hop))
        dist_7.append(len(distant & local7) / len(distant))      # DISTANT recall (16 should win)
        dist_16.append(len(distant & far16) / len(distant))

    print(f"{'relation / scheme':<40} {'local-7 circle':>15} {'sedenion-16 far chord':>22}")
    print("-" * 80)
    print(f"{'1-hop NEIGHBOURS (F547 metric)':<40} {np.mean(loc1_7):>14.0%} {np.mean(loc1_16):>22.0%}")
    print(f"{'2-hop DISTANT associates (this metric)':<40} {np.mean(dist_7):>14.0%} {np.mean(dist_16):>22.0%}")
    print()
    win7 = np.mean(loc1_7) > np.mean(loc1_16)
    win16 = np.mean(dist_16) > np.mean(dist_7)
    print("VERDICT:")
    if win7 and win16:
        print(f"  • COMPLEMENTARITY CONFIRMED ON THE DISCRIMINATING METRIC: the local-7 circle wins on 1-HOP neighbours")
        print(f"    ({np.mean(loc1_7):.0%} vs {np.mean(loc1_16):.0%}), and the sedenion-16 far-chord wins on 2-HOP DISTANT associates")
        print(f"    ({np.mean(dist_16):.0%} vs {np.mean(dist_7):.0%}). Each circle is the right tool for its OWN relation — exactly F547's claim,")
        print(f"    now shown where it bites: the 16 IS the distant-association store, not a neighbour-recall booster.")
    else:
        print(f"  • MIXED: 1-hop {'local-7 wins' if win7 else 'tie/16'} ; 2-hop distant {'sedenion-16 wins' if win16 else 'local-7 still ahead'}.")
        print(f"    local-7 1-hop {np.mean(loc1_7):.0%}/{np.mean(loc1_16):.0%}; distant {np.mean(dist_7):.0%}/{np.mean(dist_16):.0%} — honest read of the corpus.")
    print(f"  • CONNECTS the stale cross-navigation / 'ride' work (R-RBS-LM-54k cross-kernel triangulation; F189")
    print(f"    grammar-walked-via-logic): the DISTANT-association relation IS the cross-navigation bridge — the far chord")
    print(f"    is the substrate-level version of riding one kernel into another. Low-stat ({len(probes)} probes); F394; F398.")


if __name__ == "__main__":
    main()
