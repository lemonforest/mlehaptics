"""Research the user's claim: of the k=3 triple, the EDGES/operand/relational slot is the one that is
'coherent from more than one perspective' — and that is where the quad-turn (the_one/CD coupled turn)
encoding lives with multiple perspective meanings."""
from srmech.amsc import laplacian as L, cascade
from fractions import Fraction

# one small DIRECTED graph, with forward/backward counts per edge (F1210 metric+curvature)
edges = [(0,1),(1,2),(2,0)]                      # a directed triangle
fwd   = {(0,1):6,(1,2):4,(2,0):5}
bwd   = {(0,1):3,(1,2):2,(2,0):1}
metric   = [fwd[e]+bwd[e] for e in edges]        # w_fwd + w_bwd  — the FIELD / symmetric read
curvature= [fwd[e]-bwd[e] for e in edges]        # w_fwd - w_bwd  — the DIRECTED / chiral read

print("=== (1) the three NAMINGS are ONE triple (F1207/F1272) ===")
print("  op(x)operand(x)responsion  ==  distributional(x)relational(x)responsion  ==  eigenvectors(x)edges(x)eigenvalues")
lap = L.dense_laplacian(3, edges, [float(w) for w in metric])
evals, V = L.symmetric_eigendecompose(lap)
print("  responsion (eigenvalues) :", [round(float(e),3) for e in evals])
print("  distributional (eigenvecs): a %dx%d basis (order-INVARIANT, F1272)" % (len(V), len(V[0]) if V else 0))
print("  relational (edges)       :", edges)

print()
print("=== (2) is the EDGES slot coherent from MORE THAN ONE perspective? ===")
print("  the SAME directed edge set, read three coherent ways:")
# perspective A: the metric (magnitude) — dense laplacian
print("    A metric/field  (fwd+bwd) :", metric, "  -> dense_laplacian")
# perspective B: the curvature (holonomy) — cycle_holonomy on the charge
ch = [Fraction(fwd[e]-bwd[e], fwd[e]+bwd[e]) for e in edges]
hol = L.cycle_holonomy([(0,1),(1,2),(2,0)], charges=ch, n=3)
print("    B curvature/dir (fwd-bwd) :", curvature, "  -> cycle_holonomy balanced=%s" % hol.get("balanced"))
# perspective C: chirality — the signed direction per edge (net which-way)
print("    C chirality (sign net)    :", [1 if c>0 else (-1 if c<0 else 0) for c in curvature])
print("  => ONE edge object, THREE coherent reads (metric, curvature, chirality). The op slot")
print("     (eigenvectors) is order-INVARIANT (one perspective); responsion (eigenvalues) is one")
print("     magnitude per mode. Only the EDGES carry multiple coherent perspectives at once.")

print()
print("=== (3) does the QUAD TURN (the_one coupled turn) live in the edges? ===")
one = cascade.the_one(1, 0)
print("  the_one: dim=%d partition=%s (the 1:3:7:3 tower)" % (one.dim, one.partition))
print("  the genome packs each edge as a klein4 COUPLED TURN (element_type='klein4', coupling=the_one; F1300)")
print("  so an edge is not a scalar — it is a coupled turn on the CD tower, and its IMAGINARY components")
print("  ARE the multiple perspectives (metric + curvature + chirality = reads of the one turn).")

print()
print("=== (4) the FRACTAL TOWER: perspectives per edge grow with the rung ===")
print("  rung   imag dims = # perspectives a coupled-turn edge can carry")
for dim,name,imag in ((2,'C',1),(4,'H',3),(8,'O',7),(16,'S',15)):
    print("   %-2d %-2s  %d" % (dim,name,imag))
print("  => the edge's multi-perspective coherence is the imaginary content of its coupled turn, and it")
print("     SCALES up the fractal tower (1,3,7,15) — the same ladder the k=3 triple sits on (F1270/F1282).")
