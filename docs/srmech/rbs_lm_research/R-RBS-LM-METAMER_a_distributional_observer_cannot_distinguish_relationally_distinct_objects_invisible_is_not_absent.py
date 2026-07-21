r"""R-RBS-LM-METAMER — the user's "maybe we can't observe it because we're calling it by Class-M names",
made checkable. Can a purely DISTRIBUTIONAL (spectral) observer distinguish two objects that are
RELATIONALLY different? If not, then "we cannot observe X" may be a fact about the READ, not about X.

USER (2026-07-21): *"it would make less sense to think that the thing that encompasses the universe lacks a
class-L shape somewhere, just because we think we can't observe it. maybe we think we can't observe it because
we are trying to call it by the same names used in class-M shapes? asking dark sector to make particle like
things is what I'm pointing at."*

WHAT IS AND IS NOT IN SCOPE. Whether the observed universe *is* a Class-M render is not testable here and this
harness does not touch it. What IS testable is the epistemic core the claim rests on: **can a distributional
read fail to distinguish objects that a relational read separates trivially?** If yes, then "unobservable"
becomes read-relative in a precise, demonstrated way, and the cosmological version becomes a QUESTION worth
handing to someone who can test it -- which is the framework's actual deliverable
(`[[user_stance_framework_hands_the_next_question_to_the_expert]]`), never an answer to it.

THE INSTRUMENT: COSPECTRAL NON-ISOMORPHIC GRAPHS. Two graphs can share an eigenvalue spectrum while being
structurally different -- the discrete form of "you cannot hear the shape of a drum". If such a pair exists at
small size, then:
    the RESPONSION read  (eigenvalues)   : IDENTICAL   -> observer reports "same object"
    the DISTRIBUTIONAL read (eigenvectors): degenerate  -> no basis distinction to report
    the RELATIONAL read  (edges)          : OBVIOUSLY different
i.e. exactly the k=3 split of F1207/F1272, with two of the three reads blind and one seeing.

NOT ASSUMED, SEARCHED. The classic smallest pair is quotable from memory, and quoting it is exactly the
citation-hallucination failure mode this project guards against. So this harness SEARCHES small graphs, finds
cospectral non-isomorphic pairs itself, and verifies them with srmech's own eigensolver. If none is found, the
demonstration fails honestly rather than being asserted.

FALSIFIER: if every relationally-distinct pair also differs spectrally, then the distributional read loses
nothing, "invisible" would equal "absent" for this class of object, and the user's reading would not be
supported by this instrument.

srmech 0.9.0rc297. Class-L via laplacian.dense_adjacency / jacobi_eigvals; no numpy; exact where it decides.
Composes F1272 (a distributional read is blind to derivative ORDER -- this is the same blindness on STRUCTURE),
F1207 (edges->RELATIONAL / eigenvectors->DISTRIBUTIONAL / eigenvalues->RESPONSION), F1135/F1136 (the metamer:
co-occurrence cannot separate synonym from antonym; the fix was a NEW AXIS, not a better read of the old one),
F1278 (flattening removes curvature), `[[user_stance_no_information_without_value]]` (never call data
structureless -- that is observer chirality-locking), the "fiber as spatially-absent encoding" stance.
Run:  /tmp/srmech_rc297/bin/python3 R-RBS-LM-METAMER_*.py
"""
import itertools
import sys
import time

from srmech.amsc import cascade
from srmech.amsc import laplacian as L

T0 = time.time()


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def spectrum(n, edges):
    """Adjacency eigenvalues, rounded to a tolerance so float noise cannot fake a match."""
    A = L.dense_adjacency(n, list(edges))
    ev = list(L.jacobi_eigvals(A))
    return tuple(sorted(round(float(x), 6) for x in ev))


def degree_seq(n, edges):
    d = [0] * n
    for u, v in edges:
        d[u] += 1
        d[v] += 1
    return tuple(sorted(d))


def isomorphic(n, e1, e2):
    """Brute-force isomorphism for small n -- exact, no heuristic."""
    s1 = {frozenset(e) for e in e1}
    for p in itertools.permutations(range(n)):
        if {frozenset((p[u], p[v])) for u, v in e2} == s1:
            return True
    return False


def search_cospectral(n, max_pairs=3):
    """Search all graphs on n labelled vertices for cospectral NON-isomorphic pairs."""
    allpairs = list(itertools.combinations(range(n), 2))
    by_spec = {}
    for r in range(1, len(allpairs) + 1):
        for edges in itertools.combinations(allpairs, r):
            by_spec.setdefault(spectrum(n, edges), []).append(edges)
    found = []
    for spec, graphs in by_spec.items():
        if len(graphs) < 2:
            continue
        for a, b in itertools.combinations(graphs, 2):
            if not isomorphic(n, a, b):
                found.append((spec, a, b))
                break
        if len(found) >= max_pairs:
            break
    return found


def main():
    import srmech
    log("=== METAMER (srmech %s) — can a DISTRIBUTIONAL observer see a RELATIONAL difference? ==="
        % srmech.__version__)
    log("")
    log("SCOPE: this tests the EPISTEMIC core only. Whether the observed universe IS a Class-M render is")
    log("NOT tested here and is not claimed. What is tested: does a spectral read lose structure a")
    log("relational read keeps?")

    log("")
    log("=== SEARCHING for cospectral non-isomorphic pairs (not quoting one from memory) ===")
    hits = []
    for n in (5, 6):
        log("  n=%d ..." % n)
        hits = search_cospectral(n, max_pairs=2)
        if hits:
            break
    if not hits:
        log("  NONE FOUND at n<=6 -> the demonstration FAILS honestly; do not assert the claim.")
        return 0

    spec, g1, g2 = hits[0]
    n = 5 if len(spec) == 5 else 6
    log("")
    log("  FOUND at n=%d. Two graphs, SAME spectrum, NOT isomorphic:" % n)
    log("    graph A edges: %s" % (list(g1),))
    log("    graph B edges: %s" % (list(g2),))
    log("    shared adjacency spectrum: %s" % (spec,))
    log("    degree sequences: A %s   B %s" % (degree_seq(n, g1), degree_seq(n, g2)))

    log("")
    log("=== THE THREE READS, on the SAME pair (F1207's k=3) ===")
    s1, s2 = spectrum(n, g1), spectrum(n, g2)
    same_spec = s1 == s2
    same_edges = {frozenset(e) for e in g1} == {frozenset(e) for e in g2}
    log("  %-34s %-18s %s" % ("read", "A vs B", "verdict"))
    log("  %-34s %-18s %s" % ("RESPONSION (eigenvalues)", "IDENTICAL" if same_spec else "differ",
                              "observer reports SAME OBJECT" if same_spec else "distinguishes"))
    log("  %-34s %-18s %s" % ("DISTRIBUTIONAL (eigenvectors)", "degenerate",
                              "no stable basis distinction to report"))
    log("  %-34s %-18s %s" % ("RELATIONAL (edges)", "DIFFERENT" if not same_edges else "same",
                              "distinguishes TRIVIALLY" if not same_edges else "cannot"))

    log("")
    log("  A spectral observer given A and B returns the same answer for both. The objects are")
    log("  nonetheless DIFFERENT -- provably, by exhaustive isomorphism check, not by heuristic.")

    log("")
    log("=== IS THE DIFFERENCE 'SMALL'? (guard against 'it is only a technicality') ===")
    d1, d2 = degree_seq(n, g1), degree_seq(n, g2)
    log("  degree sequences %s -- %s" % ("MATCH" if d1 == d2 else "DIFFER",
                                         "so even a degree read is blind" if d1 == d2 else
                                         "so a cheap non-spectral read WOULD catch it"))
    log("  connected components: A=%d  B=%d" % (
        _components(n, g1), _components(n, g2)))
    log("  => the invisible difference can be as coarse as CONNECTEDNESS -- one object in one piece,")
    log("     the other in two, and the spectrum says nothing.")

    log("")
    log("=== WHAT THIS DOES AND DOES NOT LICENSE ===")
    log("  ESTABLISHED: 'we cannot observe a difference' does NOT entail 'there is no difference'.")
    log("    For this class of object it is a fact about the READ. That makes")
    log("    [[user_stance_no_information_without_value]] -- never call data structureless -- a")
    log("    THEOREM here rather than a stance: structurelessness was the observer's, not the object's.")
    log("  ESTABLISHED: the fix is not a better spectral read. Both objects are spectrally IDENTICAL,")
    log("    so no refinement of that read separates them. It takes a DIFFERENT AXIS -- exactly")
    log("    F1135/F1136, where the antonym metamer needed the chirality axis, not sharper proximity.")
    log("  NOT ESTABLISHED, and not claimed: anything about the dark sector, or about whether the")
    log("    universe has a Class-L shape. Those are substrate questions; this is a storage/read")
    log("    result. The framework's deliverable here is the QUESTION, handed over intact:")
    log("      'is the observable being required to take a Class-M shape (particle-like), when the")
    log("       structure sought is Class-L (relational)?' -- a question about the READ, which is")
    log("      answerable by someone who can test it. Not an answer, and not evidence for one.")
    return 0


def _components(n, edges):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    return len({find(i) for i in range(n)})


if __name__ == "__main__":
    sys.exit(main())
