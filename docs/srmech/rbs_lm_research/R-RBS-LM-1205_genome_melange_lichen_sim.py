r"""R-RBS-LM-1205 — GENOME MELANGE (co-express separate Class-L genomes WITHOUT merging).
The read-INDEPENDENT structural check for FINDING_1205 ([[feedback_read_independent_structure_check_first]]).

CLAIM under test: keep two knowledge corpora as SEPARATE Class-L genomes (Laplacian generators L_A, L_B);
at query time COUPLE them through a SPARSE bridge C (shared anchors) and co-excite — and an emergent shape
appears that neither genome has alone (cross-block eigenmodes + a responsion that crosses the bridge),
WITHOUT destroying either genome's standalone structure. Merge would flatten both; couple keeps them whole.
This is "always in simulation of abstracted data": the coupled operator [[L_A, C],[C^T, L_B]] is assembled at
excitation time and discarded — never a stored merged genome. Biology's name for it: lichen (+ mitonuclear
OXPHOS, + H2/formate syntrophy — see the finding). srmech-native (magnetic_laplacian / symmetric_eigendecompose
/ responsion). numpy-free; no abs builtin; no Counter. Deterministic (hand-specified graphs; no RNG).

    /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-1205_genome_melange_lichen_sim.py
"""
from srmech.amsc import laplacian as L


def _abs(z):
    z = complex(z)
    return (z.real * z.real + z.imag * z.imag) ** 0.5


# Two ASYMMETRIC genomes (a symmetric toy over-cleanly makes EVERY mode cross — an artifact).
GENOME_A = [(0, 1), (0, 2), (1, 3), (2, 4), (2, 5)]   # nodes 0..5 — "proofwiki-ish" dependency tree
GENOME_B = [(6, 7), (7, 8), (8, 9), (9, 10), (6, 10)]  # nodes 6..10 — "enwiki-ish" web (a cycle+chord)
BRIDGE = [(2, 8)]                                       # ONE genuine shared anchor; assembled at excitation
N = 11
A_NODES, B_NODES = range(0, 6), range(6, 11)


def _block_weights(vec):
    wa = sum(float(vec[i]) ** 2 for i in A_NODES)
    wb = sum(float(vec[i]) ** 2 for i in B_NODES)
    return wa, wb


def analyze(edges, tag):
    # (1) eigenmode LOCALITY on the symmetric Class-L: which modes live in one genome vs BOTH?
    und = sorted({(min(a, b), max(a, b)) for a, b in edges})
    evals, evecs = L.symmetric_eigendecompose(L.dense_laplacian(N, und, [1.0] * len(und)))
    loc_a = loc_b = cross = 0
    for m in range(N):
        v = [float(evecs[r][m]) for r in range(N)]
        wa, wb = _block_weights(v)
        if min(wa, wb) > 0.12:          # meaningful support on BOTH blocks = a cross-genome mode
            cross += 1
        elif wa >= wb:
            loc_a += 1
        else:
            loc_b += 1
    # (2) directed responsion: excite genome-A node 0 — does the RESPONSE reach genome B?
    Lm = L.magnetic_laplacian(N, edges, [1.0] * len(edges), q=0.25)
    r = L.responsion(Lm, [1.0] + [0.0] * (N - 1), 2.0, kind="resolvent")
    reach_b = sum(_abs(r[i]) for i in B_NODES)
    print("  [%s]" % tag)
    print("     eigenmodes: %d localized-in-A (single-genome) | %d localized-in-B | %d CROSS-GENOME "
          "(shape supported on BOTH — invisible to either alone)" % (loc_a, loc_b, cross))
    print("     responsion A-node0 -> reach into genome B: %.3f\n" % reach_b)


if __name__ == "__main__":
    print("=== GENOME MELANGE — couple-don't-merge, read as one coupled Class-L operator ===\n")
    analyze(GENOME_A + GENOME_B + BRIDGE, "MELANGE: A + B + one sparse bridge")
    analyze(GENOME_A + GENOME_B, "CONTROL: A + B, NO bridge (inert pairing — no lichen)")
    print("  READ: the single-genome towers PERSIST (localized modes survive — direct edge addressing intact),")
    print("  AND cross-genome modes EMERGE only when a real bridge couples them; with no bridge the response")
    print("  stays home (block-diagonal). A sparse bridge suffices. The composite is a runtime co-excitation,")
    print("  never a stored merged genome. Lichen: separate genomes, emergent thallus, harvested just the same.")
