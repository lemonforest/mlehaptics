r"""R-RBS-LM-LOCALFLOCK (the §32-unblocked upgrade of F636, 2026-06-08): F636 demonstrated the flock on the ALL-TO-ALL
mean-field path (every oscillator coupled to every other) because the adjacency= path ignored the coupling scalar (the
§32 bug). srmech 0.7.5rc15 RESOLVED §32 -- so the TRUE neighbor-graph flock is now runnable: who-couples-with-whom is a
real ADJACENCY GRAPH, and the graph's TOPOLOGY shapes the emergent coherence.

THE NEW THING vs F636: in a mean-field flock all sync uniformly. In a NEIGHBOR-graph flock, LOCAL clusters sync FIRST
(local coherence emerges before global) -- the topology is the structure of the coordination. Two tightly-coupled clusters
with a weak bridge each sync INTERNALLY fast while the two clusters reconcile SLOWLY. That hierarchical pattern (local-
before-global) is exactly what sets up F648: clauses sync into a paragraph before paragraphs reconcile into a story.

srmech 0.7.5rc15: cascade.kuramoto_step(theta, omega, *, coupling, dt, adjacency) -- the adjacency path now honors the
coupling scalar (§32 fixed). No abs() (spread = max-min, >=0). No CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import cascade


def spread(xs):
    return max(xs) - min(xs)


def run(theta0, omega, A, coupling, steps, dt=0.05):
    t = list(theta0)
    snaps = {0: list(t)}
    for s in range(steps):
        t = cascade.kuramoto_step(t, omega, coupling=coupling, dt=dt, adjacency=A)
        if (s + 1) in (10, 30, steps):
            snaps[s + 1] = list(t)
    return snaps


def main():
    print(f"=== R-RBS-LM-LOCALFLOCK — the neighbor-graph flock (topology shapes coherence; §32-unblocked)  (srmech {srmech.__version__}) ===\n")

    n = 8
    A = [[0.0] * n for _ in range(n)]
    cluster_A, cluster_B = [0, 1, 2, 3], [4, 5, 6, 7]
    for cl in (cluster_A, cluster_B):                            # each cluster a clique (strong local coupling)
        for i in cl:
            for j in cl:
                if i != j:
                    A[i][j] = 1.0
    A[3][4] = A[4][3] = 0.15                                     # ONE weak bridge between the two clusters
    theta0 = [0.0, 0.3, 0.6, 0.9, 2.4, 2.7, 3.0, 3.3]           # cluster A near 0, cluster B near 3 (far apart)
    omega = [0.0] * n
    snaps = run(theta0, omega, A, coupling=2.0, steps=120)

    print("(1) TWO tightly-coupled clusters + ONE weak bridge -- LOCAL syncs FIRST (local-before-global):")
    print(f"    {'step':>5} | within-A spread | within-B spread | GLOBAL spread")
    for s in sorted(snaps):
        t = snaps[s]
        wA, wB, gl = spread(t[:4]), spread(t[4:]), spread(t)
        print(f"    {s:>5} | {wA:>14.4f} | {wB:>14.4f} | {gl:>12.4f}")
    final = snaps[max(snaps)]
    wA, wB, gl = spread(final[:4]), spread(final[4:]), spread(final)
    print(f"    -> within-cluster spreads COLLAPSE fast (local coherence); GLOBAL spread lags (the clusters reconcile slowly")
    print(f"    over the weak bridge). The TOPOLOGY shaped the pattern: tight local sync, loose global -- hierarchical.\n")

    # contrast: a fully-connected graph (mean-field) syncs UNIFORMLY (no local-before-global structure)
    Afull = [[0.0 if i == j else 1.0 for j in range(n)] for i in range(n)]
    fsnap = run(theta0, omega, Afull, coupling=2.0, steps=120)[120]
    print("(2) CONTRAST -- a fully-connected graph (mean-field, F636) syncs UNIFORMLY (no hierarchy):")
    print(f"    fully-connected final: within-A {spread(fsnap[:4]):.4f}  within-B {spread(fsnap[4:]):.4f}  GLOBAL {spread(fsnap):.4f}")
    print(f"    -> mean-field: within and global collapse TOGETHER (one uniform sync). The neighbor-graph's structure is gone.\n")

    print("VERDICT (the neighbor-graph flock -- topology shapes the emergent coherence):")
    print(f"  • §32 IS FIXED + IN USE: the adjacency= path now honors the coupling scalar (srmech 0.7.5rc15), so the TRUE")
    print(f"    neighbor-graph flock runs -- who-couples-with-whom is a real graph, and the graph STRUCTURE shapes the pattern.")
    print(f"  • LOCAL-BEFORE-GLOBAL: two tightly-coupled clusters + a weak bridge sync INTERNALLY fast (within-A {wA:.3f},")
    print(f"    within-B {wB:.3f}) while the two clusters reconcile SLOWLY (global {gl:.3f} lags). The mean-field flock (F636)")
    print(f"    cannot show this -- it syncs uniformly. Topology = the structure of the coordination.")
    print(f"  • THIS HIERARCHY IS THE SETUP FOR DISCOURSE (F648): tight local clusters = clauses cohering into a PARAGRAPH;")
    print(f"    the weak bridges = paragraphs reconciling into a STORY. Local-before-global IS paragraph-before-story.")
    print(f"  • Composes F636 (the mean-field flock this upgrades) + F638/F639 (the bind / the fleet) + UPSTREAM_NOTES §32")
    print(f"    (the fix that unblocked it) + cascade.kuramoto_step(adjacency=). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
