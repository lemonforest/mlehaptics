r"""R-RBS-SNN-CHEAPANCHOR — the user's refinement (2026-06-07): "my brain has to look for something to couple and
that was the cheapest anchor also." The etak navigator (F508) stepped toward the TARGET (target-optimal). But the
brain MUST couple to *something* (there is no null / no-coupling option) — so by default it grabs the CHEAPEST
anchor (least energy = most salient / most-connected / most-frequent), NOT the target-optimal one. Target-alignment
only OVERRIDES the cheap default once you are NEAR (the operand engaging, F508's horizon). This is F485 (the cheap
path) / F495 (glucose-economy) at the anchor-SELECTION level.

Demonstrated: on the word co-occurrence manifold, compare two selection rules from the same start —
  • CHEAPEST-anchor (degree-greedy): step to the most-connected neighbour (cheapest to couple) → drifts to the HUB
    (the high-frequency default attractor), regardless of any target.
  • TARGET-aligned (F508 etak): step toward the held target → reaches it.
The brain defaults to CHEAPEST (coast on the salient backbone); the OPERAND (expensive, target-specific) is the
override engaged only NEAR. This explains the missing-parts (F492 — the cheap coast drops the operand) AND the
fewer-turns route preference (fewer EXPENSIVE coupling decisions). srmech 0.7.4; corpus from F478.
"""
import re
import importlib.util as U
from collections import Counter
import srmech

_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def walk(neighbors, pick, start, max_steps=10):
    path, here = [start], start
    for _ in range(max_steps):
        nbrs = [x for x in neighbors(here) if x not in path] or list(neighbors(here))
        if not nbrs:
            break
        nxt = pick(here, nbrs)
        path.append(nxt)
        here = nxt
    return path


def main():
    print(f"=== R-RBS-SNN-CHEAPANCHOR — the brain MUST couple, and grabs the CHEAPEST anchor by default  (srmech {srmech.__version__}) ===\n")
    text = k7.load_text()
    seq = re.findall(r"[a-z]{4,}", text.lower())
    vocab = [w for w, _ in Counter(seq).most_common(400)]
    vs = set(vocab)
    nb = {w: set() for w in vocab}
    for i, w in enumerate(seq):
        if w in vs:
            for j in range(max(0, i - 4), min(len(seq), i + 5)):
                if j != i and seq[j] in vs:
                    nb[w].add(seq[j])
    deg = {w: len(nb[w]) for w in vocab}                 # coupling-cost proxy: high degree = CHEAPEST to couple to
    n = lambda w: nb.get(w, set())

    hub = max(vocab, key=lambda w: deg[w])
    print(f"the manifold HUB (highest degree = the cheapest anchor of all): '{hub}' (degree {deg[hub]})\n")

    start, target = "water", "history"
    # CHEAPEST-anchor: step to the most-connected neighbour (least energy to couple)
    cheap = walk(n, lambda h, nbrs: max(nbrs, key=lambda x: deg[x]), start)
    # TARGET-aligned (F508 etak): step toward the held target
    aimed = walk(n, lambda h, nbrs: max(nbrs, key=lambda x: jacc(nb[x], nb[target])), start)

    print(f"CHEAPEST-anchor walk from '{start}'  (grab the most-connected = least-energy coupling each step):")
    print(f"  {' → '.join(cheap)}")
    print(f"  endpoint '{cheap[-1]}' degree {deg[cheap[-1]]}  — drifts to the high-frequency DEFAULT attractor (≈ the hub)\n")
    print(f"TARGET-aligned walk from '{start}' toward held target '{target}'  (the expensive, operand override):")
    print(f"  {' → '.join(aimed)}")
    print(f"  endpoint '{aimed[-1]}'  align-to-target {jacc(nb[aimed[-1]], nb[target]):.2f}  — reaches the target region\n")

    cheap_to_hub = deg[cheap[-1]] >= 0.6 * deg[hub]
    aimed_to_target = jacc(nb[aimed[-1]], nb[target]) > jacc(nb[cheap[-1]], nb[target])
    print("VERDICT:")
    print(f"  • the brain MUST couple to SOMETHING (no null option) → by default it grabs the CHEAPEST anchor")
    print(f"    (the most salient/connected/frequent — least energy). That walk DRIFTS to the high-frequency hub")
    print(f"    (toward-hub: {cheap_to_hub}), NOT to any specific target — it coasts the cheap backbone.")
    print(f"  • the TARGET-aligned (operand) coupling is the EXPENSIVE override; it reaches the target region")
    print(f"    (closer-than-cheap: {aimed_to_target}) but costs the spend — so the brain only engages it NEAR (F508 horizon).")
    print(f"  • this is F485/F495 at the anchor-SELECTION level: cheapest-coupling is the energy-optimal DEFAULT.")
    print(f"    It explains the missing-parts (F492: the cheap coast drops the operand) and the fewer-turns route")
    print(f"    preference (fewer EXPENSIVE coupling decisions). NOT a flaw — the substrate's intrinsic economy (form=function).")


if __name__ == "__main__":
    main()
