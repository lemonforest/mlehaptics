# Cheap MEASUREMENTS of three senses of "anisotropic" on srmech ops (main checkout, pure cell).
import sys, json, io
sys.path.insert(0, r"D:/GitHub/mlehaptics/docs/srmech/python")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from fractions import Fraction as Fr
import srmech

try:
    from srmech import _native as N
except Exception:
    N = None
print("srmech", srmech.__version__, "file", srmech.__file__, "HAS_NATIVE", getattr(N, "HAS_NATIVE", None))
from srmech.math.laplacian import dense_laplacian, cyclic_laplacian_spectrum
from srmech.cascade.cayley_dickson import cd_norm_sq
out = {}
# S1 (Rayleigh / operator sense): is L a scalar multiple of I?  directions with different Rayleigh quotients.
n = 5
edges = [(i, (i+1) % n) for i in range(n)]
L = dense_laplacian(n, edges, exact=True)
def quad(x): return sum(x[i]*L[i][j]*x[j] for i in range(n) for j in range(n))
def dot(x): return sum(v*v for v in x)
dirs = {"ones": [Fr(1)]*5, "e0": [Fr(1),0,0,0,0], "alt": [Fr(1),Fr(-1),Fr(1),Fr(-1),0], "e0-e1": [Fr(1),Fr(-1),0,0,0]}
rq = {k: str(quad(v)/dot(v)) for k, v in dirs.items()}
out["S1_rayleigh_quotients_C5"] = rq
out["S1_distinct_values"] = len(set(rq.values()))
spec = cyclic_laplacian_spectrum(5)
out["S1_cyclic_spectrum_keys"] = sorted(spec.keys())[:12]
out["S1_all_rational"] = spec.get("all_rational")
# S2 (algebraic / Witt sense): does the Laplacian quadratic form have a nonzero isotropic vector?
out["S2_q(ones)"] = str(quad(dirs["ones"]))
# S3 (norm sense, F247 hinge): definite octonion norm vs split twist
oct_null = [1,0,0,0,1,0,0,0]
out["S3_definite_O_norm(e0+e4)"] = str(cd_norm_sq(oct_null))
for g in [(1,1,1),(-1,-1,1),(-1,-1,-1)]:
    try:
        vals = {}
        for idx in range(1,8):
            x = [0]*8; x[0]=1; x[idx]=1
            vals[idx] = str(cd_norm_sq(x, gammas=g))
        out[f"S3_norm(e0+e_i) gammas={g}"] = vals
    except Exception as e:
        out[f"S3 gammas={g}"] = repr(e)[:200]
print(json.dumps(out, indent=1, ensure_ascii=False))
