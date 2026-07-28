"""LANE 1 supplement — can a ZERO-DIVISOR-adapted basis beat the cube
basis for the sedenions?  (S is not a division algebra, so the dim^2 floor
does not bind there — this is the honest search for whether that helps.)
"""
import json, random, itertools
from srmech.amsc.q import Q
from srmech.amsc.qmat import QMat
from srmech.amsc.cascade.cayley_dickson import algebra_table, table_product
import importlib.util as _ilu, os as _os
_core_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                           "lane1_block_diagonalisation_2026-07-28.py")
_spec = _ilu.spec_from_file_location("lane1_core", _core_path)
_core = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_core)
left_reg, rank_of, rowspace = _core.left_reg, _core.rank_of, _core.rowspace
transform_table, nnz = _core.transform_table, _core.nnz
pair_support, matvec = _core.pair_support, _core.matvec

t = algebra_table(16)
# kernel dim of L_x for a zero-divisor x = e_i + e_j
def Lx(x):
    return [[sum(x[i]*t[i][j][k] for i in range(16)) for j in range(16)]
            for k in range(16)]
zd = []
for i in range(1,16):
    for j in range(i+1,16):
        for k in range(1,16):
            for l in range(k+1,16):
                x=[0]*16; x[i]=1; x[j]=1
                y=[0]*16; y[k]=1; y[l]=1
                if all(v==0 for v in table_product(t,x,y)):
                    zd.append(((i,j),(k,l)))
print(json.dumps(dict(kind="S1_zero_divisor_pairs", n=len(zd))))
(i,j),(k,l) = zd[0]
x=[0]*16; x[i]=1; x[j]=1
L = Lx(x)
print(json.dumps(dict(kind="S2_annihilator", x=f"e{i}+e{j}",
      rank_L_x=QMat.from_rows(L).rank(), kernel_dim=16-QMat.from_rows(L).rank(),
      note="at most this many basis vectors can be annihilated by ONE basis vector")))

# best-effort: build bases out of the zero-divisor family, count nnz
best = None
random.seed(1)
vecs = []
for (a,b),(c,d) in zd:
    for pair in ((a,b),(c,d)):
        v=[0]*16; v[pair[0]]=1; v[pair[1]]=1
        if v not in vecs: vecs.append(v)
for trial in range(300):
    random.shuffle(vecs)
    B=[]
    for v in vecs:
        cand = B+[v]
        if rank_of(cand)==len(cand):
            B.append(v)
        if len(B)==16: break
    if len(B)<16:
        # top up with e_0 etc
        for i in range(16):
            e=[0]*16; e[i]=1
            cand=B+[e]
            if rank_of(cand)==len(cand): B.append(e)
            if len(B)==16: break
    if len(B)!=16: continue
    P=[[B[a][i] for a in range(16)] for i in range(16)]
    try:
        Pin=QMat.from_rows(P).inverse().to_lists()
    except Exception:
        continue
    T=transform_table(t,P,Pin)
    c=nnz(T); z=pair_support(T)
    if best is None or c<best[0]:
        best=(c,z,trial)
print(json.dumps(dict(kind="S3_sedenion_best_zero_divisor_basis",
      trials=300, best_nnz=best[0] if best else None,
      vanishing_product_pairs=best[1] if best else None,
      cube_nnz=256, dim_sq=256)))
