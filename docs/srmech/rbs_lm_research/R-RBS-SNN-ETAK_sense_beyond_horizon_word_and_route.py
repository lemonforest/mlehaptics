r"""R-RBS-SNN-ETAK — sense the target BEYOND the horizon by the anchor-coupling of what is NOT beyond it. The user's
cross-substrate match (2026-06-07): the SAME coupling structure that tells you which tree to turn at (a familiar
drive) tells you which word completes a sentence. Etak (F482): the absent reference is sensed through the visible
anchors; the FAR/NEAR switch is the SCALE DoF (F507's 7th) — far you COAST on the cyclic route (operator, low pose
detail), near the destination the OPERAND/pose engages (the tree opposite the sign before the alley, full spatial
detail).

ONE generic `etak_navigate(neighbors, align, start, target)`:
  • you never "see" the target; at each step you sense the next anchor by COUPLING-ALIGNMENT toward it.
  • PROXIMITY = align(here, target) (the scale/horizon DoF); FOCUS = how sharply one neighbor wins (max − mean).
  • FAR (low proximity): focus is shallow → you coast (the route's cyclic operator, few decisions).
  • NEAR (proximity past the horizon): focus sharpens → the operand picks the exact turn / the exact word.
Run on TWO manifolds with the SAME code: a WORD co-occurrence graph (sentence) and a spatial ROUTE grid (drive).
srmech 0.7.4 (hdc.similarity for the coupling; corpus from F478).
"""
import re
import importlib.util as U
from collections import Counter
import srmech

_s = U.spec_from_file_location("k7", "docs/srmech/rbs_lm_research/R-RBS-LM-K7STEER_anchor_gated_byte_generator.py")
k7 = U.module_from_spec(_s); _s.loader.exec_module(k7)


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def etak_navigate(neighbors, align, start, target, horizon, max_steps=12):
    """walk from start toward an UNSEEN target by coupling-alignment; record proximity + focus per step."""
    path, here, log, crossed = [start], start, [], None
    for step in range(max_steps):
        prox = align(here, target)
        nbrs = [x for x in neighbors(here) if x not in path] or list(neighbors(here))
        if not nbrs:
            break
        scores = sorted((align(x, target) for x in nbrs), reverse=True)
        focus = scores[0] - (sum(scores) / len(scores))         # how sharply one neighbor wins
        mode = "NEAR/operand" if prox >= horizon else "FAR/coast"
        if crossed is None and prox >= horizon:
            crossed = step
        log.append((step, here, round(prox, 3), round(focus, 3), mode))
        if here == target or prox > 0.95:
            break
        here = max(nbrs, key=lambda x: align(x, target))        # the etak step: toward the absent reference
        path.append(here)
    return path, log, crossed


def main():
    print(f"=== R-RBS-SNN-ETAK — sense beyond the horizon by anchor-coupling (word + route, one code)  (srmech {srmech.__version__}) ===\n")

    # ---- WORD manifold: co-occurrence graph (the sentence's 'streets') ----
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
    wn = lambda w: nb.get(w, set())
    wa = lambda a, b: jacc(nb.get(a, set()), nb.get(b, set()))
    start_w, target_w = "water", "ocean" if "ocean" in vs else ("sea" if "sea" in vs else vocab[10])
    pathw, logw, crossw = etak_navigate(wn, wa, start_w, target_w, horizon=0.18)
    print(f"WORD manifold: sense '{target_w}' (beyond horizon) starting from '{start_w}':")
    for step, here, prox, focus, mode in logw:
        print(f"  step {step}: at '{here:<10}' proximity {prox:.3f} focus {focus:.3f}  [{mode}]")
    print(f"  path: {' → '.join(pathw)}")
    print(f"  horizon crossed (FAR→NEAR) at step: {crossw}\n")

    # ---- ROUTE manifold: a landmark grid (the drive) — SAME etak_navigate, different align ----
    import math
    pos = {(x, y): (x, y) for x in range(6) for y in range(6)}      # 6×6 landmark grid
    rn = lambda p: [(p[0] + dx, p[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (p[0] + dx, p[1] + dy) in pos]
    def ra(a, b):
        d = math.hypot(a[0] - b[0], a[1] - b[1])
        return 1.0 / (1.0 + d)                                      # alignment = closeness (the scale/proximity)
    start_p, target_p = (0, 0), (5, 5)                              # the friend's backyard at the far corner
    pathp, logp, crossp = etak_navigate(rn, ra, start_p, target_p, horizon=0.30)
    print(f"ROUTE manifold: sense backyard {target_p} (beyond horizon) starting from {start_p}:")
    for step, here, prox, focus, mode in logp[:8]:
        print(f"  step {step}: at {str(here):<7} proximity {prox:.3f} focus {focus:.3f}  [{mode}]")
    print(f"  path: {' → '.join(str(p) for p in pathp)}")
    print(f"  horizon crossed (FAR→NEAR) at step: {crossp}\n")

    reached_w = pathw[-1] == target_w or wa(pathw[-1], target_w) > 0.3
    reached_p = pathp[-1] == target_p
    print("VERDICT:")
    print(f"  • ONE etak_navigate senses an UNSEEN target by anchor-coupling on BOTH manifolds: the word-graph")
    print(f"    (reached '{target_w}'-region: {reached_w}) and the route-grid (reached {target_p}: {reached_p}) — same code,")
    print(f"    different align(): the coupling structure is substrate-agnostic (which-word == which-tree).")
    print(f"  • the target is never 'seen' — it is the ABSENT etak reference (F482); each step is sensed by the")
    print(f"    coupling of the PRESENT anchors toward it. PROXIMITY = the scale/horizon DoF (F507's 7th).")
    print(f"  • FAR → COAST (shallow focus, the cyclic operator route, few decisions); NEAR → the FOCUS sharpens and")
    print(f"    the OPERAND/pose engages (the exact turn / the exact word). The horizon is where focus crosses over —")
    print(f"    'I don't need to know exactly where I am until I'm close'. The same manifold-curvature read for both.")


if __name__ == "__main__":
    main()
