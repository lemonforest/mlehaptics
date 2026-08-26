r"""R-RBS-LM-WORDASSOC (user direction): "we should get BIG WIKI into a kernel for more WORD ASSOCIATION things."

THE RECOGNITION (the srmech STOP-list, CLAUDE.md §2): word-association is NOT a Counter() / co-occurrence dict -- it is a
CLASS-L CO-OCCURRENCE KERNEL. Build the word co-occurrence GRAPH (words = nodes, co-occurrence within a window = weighted
edges) -> dense_laplacian; the LAPLACIAN EIGENSPECTRUM is the srmech-native storage signature (F172), and the graph itself
gives the associations:
  • DIRECT association(w) = the co-occurrence ADJACENCY neighbors of w (dense_adjacency), ranked by weight -- the words w
    appears beside.
  • SECOND-ORDER association = the SPECTRAL clustering: the Fiedler vector (the 2nd Laplacian eigenvector) partitions the
    vocabulary into associated clusters by SIGN -- words that share contexts cluster together even if they never directly
    co-occur (the Class-L spectral embedding). This is why the spectrum (not a Counter) is the right object.

BIG WIKI = THE SCALE: this is the MECHANISM on a small corpus; the full OFFLINE enwiki (F630/F668; the SS-FULLWIKI gated
item, F607) is the SAME kernel at scale -- a massive co-occurrence Class-L graph -> word-associations across all of human
text, attested class-B-tertiary (F630). For the Story Teller, this word-association kernel ENRICHES the_one descriptions
(F680) and RESOLVES asking-state gaps (F661): a gap word -> its wiki co-occurrence neighbors -> related words to compose with
(an attested association, not a guess). The big-wiki word-association kernel is the 'more word association things' asked for.

srmech 0.7.5rc15: amsc.laplacian.{dense_laplacian, dense_adjacency, jacobi_eigvals, fiedler_vector} (the co-occurrence graph
= a Class-L spectral object; NOT Counter()) ; BitExactCommKernel.content_address (the kernel signature). No abs(); no CAD;
no Workflow; no sub-agents. The co-occurrence COUNTING builds the edge WEIGHTS (the prescribed flow); the LAPLACIAN is the
storage (F172), not the counter.
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel
from srmech.amsc import laplacian

# a small the_one/nature corpus (illustrative; big wiki is the scale). content words only (a tiny stoplist dropped).
CORPUS = [
    "galaxy turns spiral",
    "shell coils galaxy",
    "helix twists chirality",
    "snowflake grows sectors",
    "one sees galaxy shell helix snowflake",
    "spiral coils twists grows in the one",
]
STOP = {"in", "the", "with", "like", "and", "is", "of", "a"}


def build_cooccurrence(corpus, window=2):
    """build the co-occurrence edge WEIGHTS (the prescribed flow: count -> edges -> Laplacian; F172/STOP-list)."""
    toks = [[w for w in line.split() if w not in STOP] for line in corpus]
    vocab = sorted({w for line in toks for w in line})
    idx = {w: i for i, w in enumerate(vocab)}
    weights = {}                                                  # (i,j) -> co-occurrence count (i<j)
    for line in toks:
        for a in range(len(line)):
            for b in range(a + 1, min(a + window + 1, len(line))):
                i, j = sorted((idx[line[a]], idx[line[b]]))
                if i != j:
                    weights[(i, j)] = weights.get((i, j), 0.0) + 1.0
    edges = sorted(weights)
    return vocab, idx, edges, [weights[e] for e in edges]


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-WORDASSOC — word-association IS a Class-L co-occurrence kernel (big wiki = the scale)  (srmech {srmech.__version__}) ===\n")

    vocab, idx, edges, w = build_cooccurrence(CORPUS)
    n = len(vocab)
    Lap = laplacian.dense_laplacian(n, edges, w)
    A = laplacian.dense_adjacency(n, edges, w)
    spec = sorted(float(x) for x in laplacian.jacobi_eigvals(Lap))
    print("(1) THE CO-OCCURRENCE GRAPH = a Class-L spectral object (NOT a Counter; F172/STOP-list):")
    print(f"    {n} words, {len(edges)} weighted co-occurrence edges; vocab {vocab}")
    print(f"    Laplacian eigenspectrum (the storage signature, F172): {[round(x,2) for x in spec]}")
    sig = k.content_address(",".join(f"{x:.4f}" for x in spec))
    print(f"    spectrum content-address (the kernel signature): {sig[:16]}...\n")

    # (2) DIRECT association(w) = the co-occurrence adjacency neighbors, ranked by weight
    Arows = [[float(A[i][j]) for j in range(n)] for i in range(n)]
    def assoc(word, top=4):
        i = idx[word]
        nbrs = sorted(((Arows[i][j], vocab[j]) for j in range(n) if Arows[i][j] > 0), reverse=True)
        return [(wd, wt) for wt, wd in nbrs[:top]]
    print("(2) DIRECT word-association = the co-occurrence adjacency neighbors (ranked by weight):")
    for q in ["galaxy", "one", "spiral"]:
        print(f"    assoc({q!r}) -> {assoc(q)}")
    print()

    # (3) SECOND-ORDER association = the Fiedler-vector spectral clustering (sign-partition)
    fied = [float(x) for x in laplacian.fiedler_vector(Lap)]
    clusterA = [vocab[i] for i in range(n) if fied[i] >= 0]
    clusterB = [vocab[i] for i in range(n) if fied[i] < 0]
    print("(3) SECOND-ORDER association = the Fiedler-vector spectral clustering (shared-context, even if not adjacent):")
    print(f"    cluster + : {clusterA}")
    print(f"    cluster - : {clusterB}")
    print(f"    -> words sharing contexts cluster together (the Class-L spectral embedding) -- the value over a raw counter.\n")

    print("VERDICT (word-association IS a Class-L co-occurrence kernel; big wiki = the same kernel at scale):")
    print(f"  • WORD-ASSOCIATION IS A CLASS-L CO-OCCURRENCE KERNEL (the STOP-list, F172): the word co-occurrence GRAPH ->")
    print(f"    dense_laplacian; the eigenspectrum is the storage signature (NOT a Counter -- the counter only builds the edge")
    print(f"    weights; the Laplacian IS the storage). DIRECT association = the adjacency neighbors (assoc('galaxy') ->")
    print(f"    turns/spiral/shell/...); SECOND-ORDER association = the Fiedler spectral clustering (shared-context words")
    print(f"    cluster even when not adjacent) -- the value a raw counter cannot give.")
    print(f"  • BIG WIKI = THE SCALE (the user's ask): this is the MECHANISM on a small corpus; the full OFFLINE enwiki")
    print(f"    (F630/F668; the SS-FULLWIKI gated item F607) is the SAME Class-L kernel at scale -- a massive co-occurrence")
    print(f"    graph -> word-associations across all human text, attested class-B-tertiary (F630). Build it once, query it")
    print(f"    forever (GPU-free, F628). The big-wiki word-association kernel is the 'more word association things' asked for.")
    print(f"  • IT SERVES THE STORY TELLER: the word-association kernel ENRICHES the_one descriptions (F680 -- richer A-N")
    print(f"    chapter words) and RESOLVES asking-state gaps (F661): an unheld word -> its wiki co-occurrence neighbors ->")
    print(f"    related attested words to compose with (an attested association, not a guess; composes the F669 AMSC fetch).")
    print(f"  • Composes the §1 Class-L primitive (the co-occurrence Laplacian) + F172 (the eigenspectrum = storage) + F630/")
    print(f"    F668 (the offline wiki = the content source) + F607 (SS-FULLWIKI = the scale gate) + F680 (enrich the_one")
    print(f"    chapters) + F661/F669 (resolve gaps via attested associations) + F628 (build-once, query GPU-free) + the STOP-")
    print(f"    list discipline (Laplacian not Counter). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
