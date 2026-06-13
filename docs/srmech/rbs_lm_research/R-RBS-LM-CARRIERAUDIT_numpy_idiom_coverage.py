r"""R-RBS-LM-CARRIERAUDIT (F728) — measure how numpy-SHAPED the srmech `Mat`/`Vec` carriers are.

WHY (the design goal, user direction 2026-06-13): the carriers must preserve the *spirit* of a numpy array
WITHOUT being numpy — because a current-gen LLM reflexively reaches for numpy to do math instead of srmech. If the
carrier answers the numpy idioms an LLM writes (`.shape`, `m[i,j]`, `m @ n`, `a + b`, `m[:2]`, `m[-1]`), the reflex
routes THROUGH srmech silently. Every idiom that RAISES instead pushes the LLM to `np.asarray(m.tolist())` -> numpy,
defeating the purpose. So this audit = the §2 srmech-first reflex-override, applied at the DATA-TYPE level: it
scores the carrier's numpy-reflex-absorption and names the gaps. Re-run on each rc.

Run (numpy-free venv):  <venv>/python R-RBS-LM-CARRIERAUDIT_numpy_idiom_coverage.py
rc132 RESULT: ✅ shape / m[i,j] / m[i] row / m[i][j] / len / iterate / .T / @ / .tolist ;
              ❌ elementwise (+,-,*,scalar) / slicing m[:2],m[:,j] / negative index  (the bail-to-numpy gap).
No abs(); no CAD; research-subtree provenance.
"""
import srmech
from srmech.amsc import laplacian as Lp, mat as M


def _probe(label, fn):
    try:
        fn(); return (label, True, "")
    except Exception as e:
        return (label, False, f"{type(e).__name__}: {str(e)[:48]}")


def main():
    print(f"=== R-RBS-LM-CARRIERAUDIT — numpy-idiom coverage of Mat/Vec  (srmech {srmech.__version__}) ===\n")
    m = Lp.dense_laplacian(3, [(0, 1), (1, 2), (2, 0)])
    m2 = M.Mat.from_rows([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    v = Lp.jacobi_eigvals(m)
    idioms = [
        ("shape",            lambda: m.shape),
        ("m[i,j]",           lambda: m[0, 0]),
        ("m[i] row",         lambda: m[0][0]),
        ("len / iterate",    lambda: (len(m), sum(1 for _ in m))),
        (".T",               lambda: m.T.shape),
        ("@ matmul",         lambda: (m @ m2).shape),
        ("v @ v dot",        lambda: v @ v),
        (".tolist",          lambda: m.tolist()),
        ("a + b",            lambda: m + m),
        ("a - b",            lambda: m - m),
        ("a * scalar",       lambda: m * 2),
        ("scalar * a",       lambda: 2 * m),
        ("slice m[:2]",      lambda: m[:2]),
        ("col m[:,0]",       lambda: m[:, 0]),
        ("neg m[-1,-1]",     lambda: m[-1, -1]),
        ("v slice v[:2]",    lambda: v[:2]),
        ("v + v",            lambda: v + v),
    ]
    results = [_probe(lbl, fn) for lbl, fn in idioms]
    have = [r for r in results if r[1]]
    miss = [r for r in results if not r[1]]
    for lbl, ok, err in results:
        print(f"  {'OK ' if ok else 'GAP'}  {lbl:14}{'' if ok else '  <- '+err}")
    print(f"\nABSORBED {len(have)}/{len(results)} numpy idioms.  REFLEX-BAIL GAP ({len(miss)}): "
          + ", ".join(lbl for lbl, _, _ in miss))
    print("  Each GAP raises -> an LLM falls back to np.asarray(x.tolist()) -> numpy (defeats the carrier's purpose).")
    print("  Goal-completing adds: __add__/__sub__/__mul__/__rmul__/__neg__/__truediv__, slice-aware __getitem__")
    print("  (incl. column m[:,j]), negative indices. Then Mat/Vec is a near-total numpy-reflex sink. (F728)")


if __name__ == "__main__":
    main()
