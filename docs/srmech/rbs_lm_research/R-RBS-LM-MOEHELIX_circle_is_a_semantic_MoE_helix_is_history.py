r"""R-RBS-LM-MOEHELIX (the user's architecture clarification 2026-06-07): the CIRCLE bookshelf (F535) is a type of
MIXTURE-OF-EXPERTS (semantic, routed by meaning, fixed-capacity), and the HELIX (F533/F534) is HISTORY (temporal,
unbounded, start-anchored, rewindable). Two DIFFERENT memory systems, addressed differently:
  • CIRCLE = MoE: each tome is an EXPERT; the Class-L spectral angle organises experts so NEIGHBOURS are related;
    a query ROUTES by its angle to its expert + neighbours (top-k), consults ONLY those (sparse), no global gating;
    the ring buffer replaces the least-used expert. Addressed by MEANING.
  • HELIX = HISTORY: the chronological tape of tomes; each history anchored at its START (Class A) + endianness
    (Class C); unbounded, rewindable (F527 log). Addressed by TIME.
  • CONSOLIDATION: a new experience APPENDS to the helix (by time) AND ROUTES into the circle (by meaning) — the
    episodic->semantic handoff (a hippocampus->cortex-style split; a framework reading, not a biology claim).

This builds the circle-as-MoE routing: does cheap angle-routing pick the RELEVANT experts (~the oracle top-k)?
srmech 0.7.4; Class-L spectral angle (the router) + co-occurrence relevance. No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech

_c = U.spec_from_file_location("circ", "docs/srmech/rbs_lm_research/R-RBS-LM-CIRCLESHELF_semantic_ring_neighbors_alike_not_global_hdc.py")
# reuse its manifold/embedding pieces via the SUPERPOSITION build it imports
_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def main():
    print(f"=== R-RBS-LM-MOEHELIX — the circle is a semantic MoE (route by meaning); the helix is history (by time)  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab)
    ang = (np.arctan2(V[:, 2], V[:, 1]) + 2 * np.pi) % (2 * np.pi)
    NT = 16
    tome_of = (ang / (2 * np.pi) * NT).astype(int) % NT
    experts = [[i for i in range(N) if tome_of[i] == t] for t in range(NT)]

    def relevance(e, qw):                                        # how relevant is expert e to query word qw
        ws = experts[e]
        return float(np.mean([jacc(nb[qw], nb[vocab[x]]) for x in ws])) if ws else 0.0

    print("(1) CIRCLE = MoE: cheap angle-routing vs the oracle (does routing pick the relevant experts?):")
    match, k = [], 3
    for qw in [w for w in ("ocean", "history", "music", "science", "earth", "light") if w in idx][:6]:
        e0 = tome_of[idx[qw]]
        routed = {e0, (e0 + 1) % NT, (e0 - 1) % NT}              # ROUTER: expert + neighbours (top-k by angle, O(1))
        oracle = set(np.argsort([relevance(e, qw) for e in range(NT)])[::-1][:k])  # the actually-most-relevant k
        ov = len(routed & oracle) / k
        match.append(ov)
        r_rel = np.mean([relevance(e, qw) for e in routed])
        rest = np.mean([relevance(e, qw) for e in range(NT) if e not in routed])
        print(f"    query '{qw:>8}' -> route to experts {sorted(routed)} | routed relevance {r_rel:.3f} vs rest {rest:.3f} | matches oracle {ov:.0%}")
    print(f"    -> angle-routing matches the oracle top-{k} {np.mean(match):.0%} of the time, consulting {k}/{NT} experts (sparse).\n")

    print("(2) SPARSE, NO GLOBAL GATING: the router uses the query's ANGLE (an O(1) lookup), not a scan of all")
    print(f"    {NT} experts — exactly the MoE efficiency, and exactly why we do NOT need a global HDC of the circle (F535).\n")

    print("(3) HELIX = HISTORY (the OTHER system): the same content is also on the chronological helix — addressed by")
    print(f"    TIME (start-anchor + endianness, F533/F534), unbounded + rewindable (F527). The circle is addressed by")
    print(f"    MEANING. A new experience APPENDS to the helix (when) AND ROUTES into the circle (what) — consolidation.\n")

    print("VERDICT:")
    print(f"  • THE CIRCLE IS A SEMANTIC MoE: tomes = experts on a smooth (spectral) expert manifold; a query routes by")
    print(f"    its angle to its expert + neighbours (matches the oracle top-{k} {np.mean(match):.0%}), consulting only {k}/{NT} —")
    print(f"    sparse, content-routed, no global gating; the ring buffer evicts the least-used expert (F535).")
    print(f"  • THE HELIX IS HISTORY: chronological, start-anchored (Class A) + endianness (Class C), unbounded,")
    print(f"    rewindable (F527/F533/F534). Two systems: the circle is addressed by MEANING, the helix by TIME.")
    print(f"  • CONSOLIDATION ties them: a new experience APPENDS to the helix (the record) AND ROUTES into the circle")
    print(f"    (the relevant expert) — episodic->semantic. A framework reading of the two memories, not a biology claim.")


if __name__ == "__main__":
    main()
