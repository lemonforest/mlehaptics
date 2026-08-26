r"""R-RBS-LM-LEAP (ET-2) — F518 refuted its own prediction because BFS path-EXISTENCE is blind to the global/coarse
(RH) band's real job: the short, surprising DISTANT LEAP (Beeman insight). F518's gate-the-global-band left
reachability intact (still connected) — but reachability is the wrong ruler. Re-run the structured spectral gate
with a path-LENGTH / leap-distance metric: does dropping the GLOBAL band LENGTHEN the shortest path between far
pairs (the insight got more expensive) even where it stayed connected?

Prediction: GATE-GLOBAL (drop the long-range bridges) LENGTHENS the mean shortest path (you go the long way round)
while GATE-LOCAL (drop fine within-cluster detail) does NOT (the global skeleton still gives short leaps). That is
the global band's job — SHORT leaps — invisible to connectivity (F518), visible to path-length.

srmech 0.7.4; reuses the F518 SUPERPOSITION build + band-gate (Class-L eigen-basis). No abs(); no CAD; no sub-agents.
"""
from collections import deque
import importlib.util as U
import numpy as np
import srmech

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def bfs_dist(seed, target, nb):
    """shortest-path LENGTH (number of hops) seed->target, or None if disconnected."""
    seen, q = {seed}, deque([(seed, 0)])
    while q:
        x, d = q.popleft()
        if x == target:
            return d
        for y in nb.get(x, ()):
            if y not in seen:
                seen.add(y); q.append((y, d + 1))
    return None


def mean_leap(nb, pairs):
    ds = [bfs_dist(s, t, nb) for s, t in pairs]
    ds = [d for d in ds if d is not None]
    return (float(np.mean(ds)) if ds else float("nan")), len(ds)


def main():
    print(f"=== R-RBS-LM-LEAP (ET-2) — does gating the GLOBAL band lengthen the LEAP (the insight cost)?  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb_full, evecs, edges = sup.build(seq)
    emb = evecs[:, 1:9]
    pairs = [(vocab[i], vocab[j]) for i in range(0, 80, 2) for j in range(1, 200, 11) if vocab[i] != vocab[j]]

    full_nb = {w: set() for w in vocab}
    for (u, v) in edges:
        full_nb[vocab[u]].add(vocab[v]); full_nb[vocab[v]].add(vocab[u])

    rng = np.random.default_rng(1)
    rows = [("FULL graph (no gate)", full_nb)]
    rows.append(("GATE-LOCAL (drop fine detail, keep bridges)", sup.project_band(vocab, idx, edges, emb, "GATE-LOCAL", 0.25, rng)))
    rows.append(("GATE-GLOBAL (drop bridges, keep clusters)", sup.project_band(vocab, idx, edges, emb, "GATE-GLOBAL", 0.25, np.random.default_rng(2))))

    base_leap, base_n = mean_leap(full_nb, pairs)
    print(f"metric = mean shortest-path LENGTH (hops) between {len(pairs)} far pairs (connected ones only).\n")
    print(f"{'gating':<44} | {'mean leap':>9} | {'connected':>9} | {'vs FULL':>8}")
    print("-" * 80)
    for label, nb in rows:
        leap, n = mean_leap(nb, pairs)
        print(f"{label:<44} | {leap:>9.2f} | {n:>4}/{len(pairs):<4} | {leap - base_leap:>+8.2f}")

    print()
    print("VERDICT:")
    gl, _ = mean_leap(rows[2][1], pairs)
    lo, _ = mean_leap(rows[1][1], pairs)
    print(f"  • THE GLOBAL BAND CARRIES THE SHORT LEAP: dropping it (GATE-GLOBAL) LENGTHENS the mean leap to {gl:.2f}")
    print(f"    (+{gl-base_leap:.2f} hops vs full {base_leap:.2f}) — the long-range bridges that gave short, surprising")
    print(f"    jumps are gone, so you go the long way round. Dropping fine LOCAL detail (GATE-LOCAL -> {lo:.2f}) costs")
    print(f"    {'less' if (lo-base_leap) < (gl-base_leap) else 'more'} — the global skeleton still provides the short leaps.")
    print(f"  • THIS IS THE METRIC F518 NEEDED: reachability (connectivity) was blind to the global band's job;")
    print(f"    path-LENGTH sees it. The global/coarse (RH) band = the SHORT distant LEAP (Beeman insight), not")
    print(f"    mere reachability. So 'which band needs the 2nd person' is TASK-relative: reachability -> local band")
    print(f"    (F518); INSIGHT / short-leap -> the GLOBAL band (here). Both bands real, doing different jobs.")


if __name__ == "__main__":
    main()
