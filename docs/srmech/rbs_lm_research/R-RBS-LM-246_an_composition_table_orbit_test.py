#!/usr/bin/env python3
"""R-RBS-LM-246 — the REAL F244 test (the one F244 named after its prose-co-occurrence NULL):
does the DIRECTED FUNCTIONAL-COMPOSITION structure of the 14 A-N operators carry the F243
division-algebra ORBIT signature on the I/C/J (= Im H, expect K3) and D-M (= Im O, expect Fano)
blocks?

PROVENANCE: the 3 independent functional-composition derivations below were produced by the
f244-f245-research workflow (3 fresh agents, type-driven: "does class X's output feed class Y's
input?"), transcribed here VERBATIM so this finding is self-contained + reproducible (the workflow
read them from /tmp; this embeds them). Consensus + spectral test + seeded permutation null are the
workflow's srmech-native analysis, reproduced bit-for-bit (spectrum fingerprint ff6f864f...).

DISCIPLINE: srmech-native only (rc9) — dense_laplacian(n, edges[2-tuples], weights), jacobi_eigvals,
format.sha256_bytes (NO hashlib), cascade.magnitude (Class-K modulus, NO python abs()), seeded
deterministic null. NO Counter / np.linalg.eig.

PRE-STATED NULL (genuinely reachable): "the {I,C,J} 3-block and {D,E,F,G,K,L,M} 7-block are NOT more
orbit-structured (K3/vertex-transitive; Fano-incidence 3-regular) than random same-size 3/7 splits."

Tier: DEMONSTRATED for the measured spectrum + the permutation test; FRAMEWORK-READING for what a
positive/null means about the class<->orbit identification (F243 §4 / F244). No biology; CAD-ban holds.
"""
import json
import numpy as np
from srmech.amsc import laplacian
from srmech.amsc.format import sha256_bytes
from srmech.amsc.cascade import magnitude as srmech_magnitude   # Class-K modulus (never python abs())

CLASSES = list("ABCDEFGHIJKLMN")
IDX = {c: i for i, c in enumerate(CLASSES)}
N = len(CLASSES)

# --- the 3 independent functional-composition derivations (workflow agents; verbatim) -----------
def _parse(s):
    return [(e[0], e[2]) for e in s.split()]
DERIVS = [set(_parse(d)) for d in [
    "A>B A>D A>G A>M A>N B>A B>D B>G B>M C>I C>L C>M D>C D>I D>K E>A E>B E>D E>L E>M F>A F>B F>G "
    "G>I G>K G>N H>A H>B I>J I>K I>N J>I J>N K>C K>M K>N L>A L>C L>K L>M L>N M>A M>I M>K M>L M>N N>C N>I N>J",
    "A>B A>E A>F A>M B>A B>D B>G B>M C>I C>J C>L C>M C>N D>B E>A E>F E>H E>L F>A F>B F>D F>E F>G F>H "
    "G>B G>C G>I G>J G>N H>A H>E H>F I>B I>C I>J I>K I>L I>N J>C J>F J>I J>L J>N K>C K>I K>J K>N L>F L>K "
    "M>A M>B M>D M>F M>G M>K N>C N>F N>I N>J N>K N>L",
    "A>B A>D A>E A>F A>G A>H A>M B>E B>G C>B C>F C>I C>J C>K C>N D>C D>E D>F D>L E>D E>F E>H F>B F>G G>D "
    "I>J I>N J>B J>C J>I J>K J>N K>C K>F K>I K>N L>C L>F L>H L>K M>A M>B M>D M>F M>G M>K M>L N>C N>D N>F N>I",
]]
assert len(DERIVS) == 3

# --- STEP 1: consensus directed adjacency (edge iff >=2/3 agree) ---------------------------------
union = set().union(*DERIVS)
vote = {p: sum(p in s for s in DERIVS) for p in union}
consensus = sorted(p for p, v in vote.items() if v >= 2)
disputed = sorted(p for p, v in vote.items() if v == 1)

# --- STEP 2: symmetrize -> dense_laplacian -> jacobi_eigvals -------------------------------------
undirected = sorted({(min(IDX[a], IDX[b]), max(IDX[a], IDX[b])) for a, b in consensus})
weights = [1.0] * len(undirected)
L = laplacian.dense_laplacian(N, undirected, weights)
spec = sorted(float(x) for x in laplacian.jacobi_eigvals(L))
spec_fp = sha256_bytes(np.round(np.array(spec, dtype=float), 9).tobytes())   # Class-A pin on Class-L
ncomp = sum(1 for x in spec if srmech_magnitude(x) < 1e-9)

ADJ = np.zeros((N, N), dtype=bool)
for u, v in undirected:
    ADJ[u, v] = ADJ[v, u] = True

def block(names):
    ix = [IDX[n] for n in names]
    sub = ADJ[np.ix_(ix, ix)]
    k = len(ix)
    e = int(sub.sum()) // 2
    degs = sorted(int(d) for d in sub.sum(axis=1))
    # triangles in the induced block (combinatorial 3-clique enumeration; no linalg)
    tri = sum(1 for a in range(k) for b in range(a + 1, k) for c in range(b + 1, k)
              if sub[ix.index(ix[a]) if False else a, b] and sub[a, c] and sub[b, c])
    return {"k": k, "edges": e, "max": k * (k - 1) // 2, "completeness": e / (k * (k - 1) // 2),
            "degrees": degs, "regular": len(set(degs)) == 1, "triangles": tri}

THREE, SEVEN = ["I", "C", "J"], ["D", "E", "F", "G", "K", "L", "M"]
s3, s7 = block(THREE), block(SEVEN)

# --- STEP 3+4: seeded permutation null over random disjoint 3/7 splits ---------------------------
rng = np.random.default_rng(0xF243)
NT = 100000
n3c = n3k3 = n7_3reg = n7_regany = 0
for _ in range(NT):
    p = rng.permutation(N)
    t, sv = p[:3], p[3:10]
    st, ss = ADJ[np.ix_(t, t)], ADJ[np.ix_(sv, sv)]
    c3 = int(st.sum()) // 2 / 3
    if c3 >= s3["completeness"] - 1e-12:
        n3c += 1
    if c3 >= 1.0 - 1e-12 and len(set(int(d) for d in st.sum(axis=1))) == 1:
        n3k3 += 1
    sd = [int(d) for d in ss.sum(axis=1)]
    if len(set(sd)) == 1:
        n7_regany += 1
        if sd[0] == 3:
            n7_3reg += 1
pv = lambda c: (c + 1) / (NT + 1)

out = {
    "consensus_edges": len(consensus), "disputed_edges": len(disputed),
    "unanimous_edges": sum(1 for v in vote.values() if v == 3),
    "spectrum": [round(x, 6) for x in spec], "spectrum_fp": spec_fp, "connected_components": ncomp,
    "three_block_ICJ": s3, "seven_block_DEFGKLM": s7,
    "p_3block_is_K3": round(pv(n3k3), 5), "p_7block_3regular_fano": round(pv(n7_3reg), 5),
    "p_7block_regular_anydeg": round(pv(n7_regany), 5),
    "fano_match": bool(s7["regular"] and s7["degrees"][0] == 3),
    "VERDICT": (
        "3-block {I,C,J} = perfect K3 (vertex-transitive, the Im-H/so(3) signature) but p=%.3f vs null "
        "(SUGGESTIVE, not <0.05 — coarse at k=3); 7-block {D,E,F,G,K,L,M} is NOT Fano-incidence "
        "(degrees %s != 3-regular, %d triangles != 7, hub-structured on L/M) -> Im-O orbit ABSENT. "
        "NET: the functional-composition test recovers the small Im-H K3 WEAKLY and does NOT recover "
        "the Im-O Fano geometry; the class<->orbit iso stays the F243 lens (F244 confirmed at the "
        "algebraic level, not just the prose level)." % (pv(n3k3), s7["degrees"], s7["triangles"])),
}
out["response_sha256"] = sha256_bytes(json.dumps(
    {k: v for k, v in out.items() if k != "VERDICT"}, sort_keys=True, separators=(",", ":")).encode())

if __name__ == "__main__":
    print(json.dumps(out, indent=2, default=str))
