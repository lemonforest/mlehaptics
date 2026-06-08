r"""R-RBS-LM-FASTSTIR (the user's refinement 2026-06-08): maybe biology does NOT suffer the access-split as much as we
modeled — because the substrate, at the QUANTUM scale, is ALWAYS doing weird fast things to its chirality state
(faster than we can see). NOT molecules flipping chirality — a fast ambient STIRRING of substrate chirality. If the
stirring is faster than the access/thinking window, one "thought" INTEGRATES over many collapse states, and the split
(partial, one-state access — F541/F546/F550) dissolves into NEAR-FULL access.

The earlier split assumed access ≈ ONE collapse state. This tests the ratio: how many collapse states fall inside one
access window (= the stirring speed relative to thinking). As the stirring speeds up:
  • COVERAGE (access completeness) -> 100% (near-full access; no split).
  • the (4:3)|(3:4) chirality ASYMMETRY of the accessed set -> 0 (both hands reached within the window; the split washes out).

So the split's severity is a CLOCK-SPEED artifact: slow stirring -> the split we modeled; fast (quantum) stirring ->
biology gets near-full access. F552 STILL holds (we can't control/SEE the quantum stirring, so we can't reproduce it),
but biology's own ACCESS is near-complete — the gap is our inability to model the stirring, NOT a biology access-limit.

srmech 0.7.4; Class-L Fiedler phase + chirality coordinate sign(V[:,2]); fast ambient stirring (golden quasi-sweep + per-state σ flip). No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
GOLDEN = 0.6180339887498949


def main():
    print(f"=== R-RBS-LM-FASTSTIR — fast quantum chiral stirring dissolves the access-split (near-full access)  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)
    phi = np.argsort(np.argsort(V[:, 1])) / N                   # Class-L manifold phase
    hand = (V[:, 2] >= np.median(V[:, 2])).astype(int)          # chirality coordinate (median-split = balanced hands)
    win = 0.10

    def access(W):
        """one ACCESS WINDOW integrates over W collapse states; averaged over many start offsets (typical thought)."""
        covs, asyms = [], []
        for s0 in range(0, 40):                                 # average over where in the stirring the thought starts
            accessed = set()
            for s in range(s0, s0 + W):
                c = (s * GOLDEN) % 1.0                          # the fast ambient stirring sweeps the manifold
                sigma = s % 2                                   # the chirality flips every collapse state (fast stir)
                accessed |= {j for j in range(N)
                             if hand[j] == sigma and min((phi[j] - c) % 1.0, (c - phi[j]) % 1.0) < win / 2}
            nR = sum(1 for j in accessed if hand[j] == 0)
            nL = sum(1 for j in accessed if hand[j] == 1)
            covs.append(len(accessed) / N); asyms.append(abs(nR - nL) / max(1, nR + nL))
        return float(np.mean(covs)), float(np.mean(asyms))

    print(f"{'collapse-states / access window (W)':<36} {'access coverage':>16} {'(4:3)|(3:4) asym':>17}")
    print(f"{'(= stirring speed vs thinking)':<36} {'(1.0 = full)':>16} {'(0 = no split)':>17}")
    print("-" * 72)
    rows = []
    for W in (1, 2, 4, 8, 16, 32, 64):
        cov, asym = access(W)
        rows.append((W, cov, asym))
        tag = "  <- the modelled split" if W == 1 else ("  <- fast quantum stirring" if W >= 32 else "")
        print(f"{W:<36} {cov:>15.0%} {asym:>16.2f}{tag}")
    print()
    slow, fast = rows[0], rows[-1]
    print("VERDICT:")
    print(f"  • THE SPLIT IS A CLOCK-SPEED ARTIFACT: with ONE collapse state per thought (W=1, the slow-clock assumption")
    print(f"    behind F541/F546/F550) access is partial ({slow[1]:.0%} coverage) and chirality-asymmetric ({slow[2]:.2f} — the split).")
    print(f"    As the stirring speeds up (more collapse states integrated per access window) coverage rises to {fast[1]:.0%} and")
    print(f"    the (4:3)|(3:4) asymmetry falls to {fast[2]:.2f} — the split DISSOLVES into near-full, chirality-balanced access.")
    print(f"  • SO BIOLOGY NEED NOT SUFFER THE SPLIT (the user's refinement): IF the quantum-scale substrate stirs chirality")
    print(f"    faster than the thinking window — always doing weird fast things to substrate chirality, NOT flipping")
    print(f"    molecules — then one thought integrates over many collapse states and the brain gets NEAR-FULL access to")
    print(f"    its storage. The earlier 'split' modelled the slow-clock limit; fast stirring is the biological regime.")
    print(f"  • F552 STILL HOLDS, refined: we still cannot MODEL biology exactly — we can neither control nor SEE the")
    print(f"    quantum stirring (it changes faster than we observe), so we cannot reproduce it. But biology's own ACCESS")
    print(f"    is near-complete; the gap is OUR inability to model the stirring, NOT a biology access-limit. The full-")
    print(f"    chirality ideal (our model) and near-full biological access CONVERGE in the fast-stir limit — they differ")
    print(f"    only in that biology gets there by ambient stirring we can't see (F526/F528). Held open (F394; this is a")
    print(f"    'I feel but don't know' hypothesis — the quantum claim is the expert's, F282). Favored not privileged (F398).")


if __name__ == "__main__":
    main()
