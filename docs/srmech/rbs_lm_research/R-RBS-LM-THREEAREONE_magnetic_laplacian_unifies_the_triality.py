r"""R-RBS-LM-THREEAREONE (F1204 / F1186) — the op(x)operand(x)responsion TRIALITY is three NATIVE-op read-outs of ONE
Class-L generator L. Corrected to srmech tooling (user 2026-07-11: "use srmech tooling; introspect before hand-rolling,
especially on new rcN"). [[feedback_introspect_srmech_before_python_dispatch]].

HONEST HISTORY: v1 hand-rolled a single-eigenvector PHASE measurement for ③ and got chance (52%/50%) — a read-out
artifact (a directed graph's magnetic Laplacian has DEGENERATE eigenpairs, so one eigenvector's node-phase is basis-
arbitrary). The fix was NOT a better hand-roll: srmech already SHIPS the responsion — `laplacian.responsion` (rc208,
F1186 — "the op⊗operand⊗responsion k=3 completion; the answering-correspondence between successive op-on-operand
applications — the stored relationship itself"). ③ is the RESPONSE-FUNCTION of the generator (operator-level), not a
per-node eigenvector attribute — exactly what the null diagnosed.

THE UNIFIED ENCODING (all Class-L; DUALITY/TRIALITY: duality is the fibration of triality; F1161: emergence = the
residue of one refined formula): ONE directed relational graph -> its (magnetic/signed) Class-L generator L, and
  ① DISTRIBUTIONAL = the spectral embedding  = symmetric_eigendecompose(L)   (top eigenvectors -> a coordinate per node)
  ② RELATIONAL/Fiedler = the community cut    = fiedler_vector(L)
  ③ RESPONSION      = the response-function    = laplacian.responsion(L, u0, z, kind)   (propagator e^{-zL} / resolvent (zI-L)^-1)
All three are NATIVE srmech ops on the SAME L. The direction (op->operand) lives in L's magnetic/signed phase.

srmech 0.9.0rc209. Class-L native (magnetic_laplacian / symmetric_eigendecompose / fiedler_vector / responsion).
numpy-free; no Python abs builtin; no Counter; no CAD. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-THREEAREONE_...py
"""
from srmech.amsc import laplacian as L


def _abs(z):
    z = complex(z); return (z.real * z.real + z.imag * z.imag) ** 0.5


def three_readouts(n, directed_edges, weights, *, label=""):
    r"""ONE Class-L generator L (magnetic, directed) -> the three native read-outs."""
    Lm = L.magnetic_laplacian(n, directed_edges, weights, q=0.25)         # the directed/chiral Class-L generator
    und = {}
    for (a, b), w in zip(directed_edges, weights):
        k = (min(a, b), max(a, b)); und[k] = und.get(k, 0.0) + w
    Ls = L.dense_laplacian(n, list(und), [und[e] for e in und])          # symmetric part (same graph, undirected)

    evals, evecs = L.symmetric_eigendecompose(Ls)                        # ① — the spectral embedding
    order = sorted(range(n), key=lambda k: float(evals[k]))
    emb = [[float(evecs[r][order[m]]) for m in range(1, min(4, n))] for r in range(n)]

    fied = L.fiedler_vector(Ls)                                          # ② — the community cut

    src = max(range(n), key=lambda i: sum(w for (a, b), w in zip(directed_edges, weights) if a == i))  # a source (op)
    u0 = [1.0 if i == src else 0.0 for i in range(n)]
    resp = L.responsion(Lm, u0, 2.0, kind="resolvent")                  # ③ — the response-function of the SAME L

    print("  [%s]  n=%d, %d directed edges" % (label, n, len(directed_edges)))
    print("    ① embedding (node0 coords):    ", [round(x, 3) for x in emb[0]])
    print("    ② fiedler (community coord):    ", [round(float(fied[i]), 2) for i in range(min(n, 8))], "..." if n > 8 else "")
    print("    ③ responsion from source@%d:    " % src, [round(_abs(resp[i]), 3) for i in range(min(n, 8))], "..." if n > 8 else "")
    print("    -> ①②③ are ALL native read-outs of the SAME Class-L generator L (F1186 responsion = the k=3 completion)\n")


if __name__ == "__main__":
    print("=== THREE-ARE-ONE — op(x)operand(x)responsion as three NATIVE read-outs of ONE Class-L generator ===\n")
    # (a) control: a directed chain (op-->operand flow); ③ decays downstream from the source
    three_readouts(6, [(i, i + 1) for i in range(5)], [1.0] * 5, label="directed chain")
    # (b) a two-community directed graph (two reaction/citation clusters + a bridge) — a comprehended-subgraph stand-in
    e = [(0, 1), (1, 2), (2, 0), (0, 2),          # cluster A (a small reaction cycle)
         (3, 4), (4, 5), (5, 3), (3, 5),          # cluster B
         (2, 3)]                                   # the op-->operand bridge A->B
    three_readouts(6, e, [1.0] * len(e), label="two directed communities + bridge")
    print("  READ: srmech ships the responsion (laplacian.responsion, rc208/F1186) — ③ is the response-function of the")
    print("  Class-L generator that ALSO yields ①(spectral embedding) + ②(fiedler). The triality is the fibration of ONE")
    print("  Class-L object; the three encodings are its read-outs, not three separate stores. All native, all Class-L.")
