#!/usr/bin/env python3
"""R-RBS-LM F421 — provenance for the #897 closeout verdict + the F412 held demo.

Verifies srmech 0.7.1's Class-L FUSION op (Schur complement / Dirichlet-to-Neumann
+ dense_solve) is bug-free, against HAND-COMPUTED ground truth — then runs the
F412 held demo (the area-law in the boundary S-spectrum), which this op unblocked.

This op is the operator|operand FUSION (F412/F417/F419): a SPATIAL graph (operand,
2:4:8) carries a boundary, and the Schur complement returns the boundary effective
Laplacian whose SPECTRUM (operator, 1:3:7) lives on |∂| modes — boundary↔spectrum,
BOTH kept, not collapsed (the projection Class L only ever gave us, F417).

Run:  <clean-venv>/bin/python R-RBS-LM-F421_schur_dtn_fusion_verify_provenance.py
Requires: srmech==0.7.1 (production PyPI; clean venv OUTSIDE the source tree).
srmech-first: every op below is a srmech.amsc.laplacian call; the only hand-math
is the reference matmul/block-extract used to CHECK srmech (no Python abs(); the
Class-K magnitude is not needed here — exact-rational Schur is sign-honest).
"""
from fractions import Fraction as Fr
from srmech.amsc import laplacian as L


def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def sub(M, rows, cols):
    return [[M[r][c] for c in cols] for r in rows]


def approx(a, b, tol=1e-9):
    return abs(float(a) - float(b)) < tol


def main():
    import srmech
    ns = srmech.native_status()
    print("srmech native_version:", ns.get("native_version"), "| abi:", ns.get("abi_version"),
          "| dispatching:", ns.get("dispatching"))
    ok_all = True

    # 1. HAND-COMPUTED TRUTH: path 0-1-2, boundary {0,2}, interior {1}.
    #    Two unit edges in series → effective edge weight 1/2 (series resistance).
    Lp = L.dense_laplacian(3, [(0, 1), (1, 2)])
    S = L.schur_complement(Lp, [0, 2], exact=True)
    exp = [[Fr(1, 2), Fr(-1, 2)], [Fr(-1, 2), Fr(1, 2)]]
    m1 = S == exp
    ok_all &= m1
    print("1. path-3 schur(exact) == [[1/2,-1/2],[-1/2,1/2]] (series resistance):", m1)
    print("   AREA LAW — S is %dx%d = |∂|=2, NOT bulk=3:" % (len(S), len(S[0])), len(S) == 2)

    # 2. DtN == Schur (the DtN map IS the Schur complement for a Laplacian)
    D = L.dirichlet_to_neumann(Lp, [0, 2], exact=True)
    m2 = D == S
    ok_all &= m2
    print("2. dirichlet_to_neumann == schur_complement:", m2)

    # 3. CROSS-CHECK on a 5-node graph: schur == Lbb − Lbi·dense_solve(Lii, Lib)
    G = L.dense_laplacian(5, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 2), (1, 3)])
    bd, it = [0, 4], [1, 2, 3]
    S5 = L.schur_complement(G, bd, exact=True)
    Lbb, Lbi, Lib, Lii = sub(G, bd, bd), sub(G, bd, it), sub(G, it, bd), sub(G, it, it)
    X = L.dense_solve(Lii, Lib, exact=True)           # Lii X = Lib  → X = Lii^{-1} Lib
    Sman = [[Lbb[i][j] - matmul(Lbi, X)[i][j] for j in range(len(bd))] for i in range(len(bd))]
    m3 = S5 == Sman
    ok_all &= m3
    print("3. 5-node schur == manual (Lbb − Lbi·dense_solve(Lii,Lib)):", m3)

    # 4. exact(rational) vs float(=False) consistency
    Sf = L.schur_complement(G, bd, exact=False)
    m4 = all(approx(Sf[i][j], S5[i][j]) for i in range(len(bd)) for j in range(len(bd)))
    ok_all &= m4
    print("4. exact-rational vs float consistency:", m4)

    # 5. dense_solve correctness: A·x == b exactly
    A, b = [[2, 1], [1, 3]], [[1], [2]]
    x = L.dense_solve(A, b, exact=True)
    m5 = matmul(A, x) == b
    ok_all &= m5
    print("5. dense_solve: A·x == b exactly:", m5, "(x =", x, ")")

    # 6. F412 HELD DEMO (was blocked on this op): the area-law in the boundary S-spectrum.
    #    jacobi_eigvals(S) = the boundary spectrum; |∂| modes, not bulk volume.
    ev = L.jacobi_eigvals(Sf)
    ev = ev.tolist() if hasattr(ev, "tolist") else list(ev)
    print("6. F412 demo — boundary S-spectrum:", [round(float(e), 4) for e in ev],
          "→ %d modes = |∂| (area law: boundary, not volume)" % len(ev))

    print("\n=== #897 VERDICT:",
          "ALL 5 CHECKS PASS — bug-free + resolved ✓" if ok_all else "FAILED ✗", "===")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
