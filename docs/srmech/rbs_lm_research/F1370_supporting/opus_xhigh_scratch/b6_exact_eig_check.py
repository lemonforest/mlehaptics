"""B6: does jacobi_eigvals(exact=True) return a spectrum whose sum/product match trace/det? (srmech ops only)"""
import sys, inspect
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math.q import Q
from srmech.math import laplacian as L
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)
doc = inspect.getdoc(L.jacobi_eigvals)
i = doc.find("exact")
print("DOC (exact excerpt):\n", doc[i-200:i+2200])
for lab, M, tr, det in (("[[2,1],[1,0]]", [[Q(2,1),Q(1,1)],[Q(1,1),Q(0,1)]], 2, -1),
                        ("C_5 Laplacian", L.dense_laplacian(5, [(i,(i+1)%5) for i in range(5)], exact=True), 10, 0),
                        ("[[1,1],[1,0]] (golden)", [[Q(1,1),Q(1,1)],[Q(1,1),Q(0,1)]], 1, -1)):
    ev = L.jacobi_eigvals(M, exact=True)
    s = ev[0]
    for x in ev[1:]: s = s + x
    p = ev[0]
    for x in ev[1:]: p = p * x
    print(f"\n{lab}: returned {ev}")
    print(f"   sum of returned = {s}   (trace {tr})   product = {p}   (det {det})")
    try:
        print("   floats of returned:", [float(x) for x in ev])
    except Exception as ex:
        print("   float() of returned raised:", type(ex).__name__, str(ex)[:150])
