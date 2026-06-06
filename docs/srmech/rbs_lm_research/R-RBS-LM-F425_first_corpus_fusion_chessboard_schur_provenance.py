#!/usr/bin/env python3
"""F425 — the FIRST real corpus fusion: chessboard grid graph through the Schur/DtN op.

The F412→F417→F421 payoff. Our corpus always did the PROJECTION (operand→operator):
  dense_laplacian(board) -> jacobi_eigvals   # drop the board, keep an anonymous spectrum
Now, with the 0.7.1 fusion op (F421), we do the FUSION (operand↔operator, both kept):
  dense_laplacian(board) -> schur_complement(rim)   # KEEP the rim squares, FOLD the interior in

Corpus object: the 8x8 chessboard grid graph (chess-maths notebook, "chess as a spectral
lattice"). Boundary = the 28 rim squares; bulk = the 36 interior squares.

The decisive test (holography, F412): SAME boundary, DIFFERENT bulk -> DIFFERENT S. If the
boundary S-matrix changes when we alter the interior (add a 'wall'), the boundary genuinely
HOLDS the bulk — the operator|operand fusion, not a projection.

Run:  <clean-venv>/bin/python R-RBS-LM-F425_first_corpus_fusion_chessboard_schur_provenance.py
Requires: srmech==0.7.1 (clean venv OUTSIDE the source tree).
Anchor: F421 (the fusion op shipped+verified) · F412 (holographic = fibration) · F417
(Class L = the one-way seam, we only projected) · F419 (the fusion is the breakthrough)
· F416 (cosmogram = fusion in the wild) · chess-maths notebook.
"""
from srmech.amsc import laplacian as L


def grid_edges(n, skip=None):
    skip = skip or set()
    E = []
    for r in range(n):
        for c in range(n):
            u = r * n + c
            for dr, dc in ((0, 1), (1, 0)):
                rr, cc = r + dr, c + dc
                if rr < n and cc < n:
                    v = rr * n + cc
                    if (u, v) not in skip and (v, u) not in skip:
                        E.append((u, v))
    return E


def board_adjacent(a, b, n):
    ra, ca = divmod(a, n); rb, cb = divmod(b, n)
    return abs(ra - rb) + abs(ca - cb) == 1


def main():
    import srmech
    print("srmech native_version:", srmech.native_status().get("native_version"))
    n = 8; N = n * n
    rim = [r*n + c for r in range(n) for c in range(n) if r in (0, n-1) or c in (0, n-1)]
    inter = [i for i in range(N) if i not in rim]
    print(f"\nchessboard {n}x{n}: {N} squares | rim(boundary)={len(rim)} | interior(bulk)={len(inter)}")
    ok = {}

    A = L.dense_laplacian(N, grid_edges(n))
    S_A = L.schur_complement(A, rim, exact=False)

    # (1) AREA LAW: S is |rim| x |rim|, not |board|
    ok['(1) AREA LAW: S is |rim|x|rim|, not board-volume'] = (len(S_A) == len(rim) and len(S_A[0]) == len(rim))

    # (2) FUSION keeps positions AND folds the bulk: effective couplings between non-adjacent rim squares
    pos = {idx: i for i, idx in enumerate(rim)}
    folded = sum(1 for ai, a in enumerate(rim) for b in rim[ai+1:]
                 if not board_adjacent(a, b, n) and abs(S_A[pos[a]][pos[b]]) > 1e-9)
    ok['(2) FUSION: interior folds into rim-rim couplings (non-adjacent)'] = folded > 0

    # (3) HOLOGRAPHY (decisive): same rim, different bulk (interior wall) -> different S
    wall = {(3*n + 3, 3*n + 4)}
    B = L.dense_laplacian(N, grid_edges(n, skip=wall))
    S_B = L.schur_complement(B, rim, exact=False)
    maxdiff = max(abs(S_A[i][j] - S_B[i][j]) for i in range(len(rim)) for j in range(len(rim)))
    changed = sum(1 for i in range(len(rim)) for j in range(len(rim)) if abs(S_A[i][j] - S_B[i][j]) > 1e-9)
    ok['(3) HOLOGRAPHY: boundary S is a function of the bulk (wall changes S)'] = maxdiff > 1e-9

    # (4) contrast with the projection (operand dropped)
    ev = L.jacobi_eigvals(A); ev = ev.tolist() if hasattr(ev, 'tolist') else list(ev)
    ok['(4) projection = anonymous spectrum; fusion = labeled rim + folded bulk'] = (len(ev) == N and len(S_A) == len(rim))

    print(f"\n(1) AREA LAW   — S is {len(S_A)}x{len(S_A[0])} = rim={len(rim)} (NOT board={N})")
    print(f"(2) FUSION     — {folded} effective rim-rim couplings NOT board-adjacent (bulk folded in)")
    print(f"(3) HOLOGRAPHY — interior wall changes boundary S in {changed} entries, max |ΔS|={maxdiff:.5f}")
    print(f"(4) PROJECTION jacobi_eigvals(full)={len(ev)} anon eigenvalues (positions dropped)")
    print(f"    FUSION schur_complement(rim)={len(rim)} labeled rim squares + interior folded in")

    print("\n=== F425: first real corpus fusion (chessboard grid) ===")
    for k, v in ok.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    allok = all(ok.values())
    print("\nVERDICT:", "FIRST CORPUS FUSION RUNS — boundary keeps bulk ✓" if allok else "FAIL ✗")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
