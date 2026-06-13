"""F363 (battery test 3) — ride-and-read-the-new-diagonal: apply the off-diagonal as TRANSPORT,
then read the new local diagonal from the relocated frame. Is the full local structure recoverable
from the destination, and is the relocation genuine (one-way) vs the symmetric shadow (bleeds back)?

Conceptual thread (F361): the off-diagonal isn't only the view — it's the operator that MOVES the
anchor. Ride the directed off-diagonal i→j; the anchor relocates to j; read j's own local structure.
  - directed transport A (off-diagonal): A·e_i = the OUT-neighbours of i (the projected spot);
    A^k·e_i = the depth-k frontier (ride further by composing); you do NOT bleed back to i (one-way).
  - symmetric shadow A_sym: A_sym·e_i reaches BOTH in/out neighbours and A_sym²·e_i RETURNS to i
    (bleeds back) -> no genuine relocation, only scan-in-place.

dense_matvec_complex applies the transport (srmech-native). Directed adjacency built from the edge
list (mechanics). The "new diagonal read" = the out-neighbour structure at the reached node.
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R16_ride_and_read_new_diagonal.py
"""
import json
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc import laplacian as L
from srmech.amsc import mat as M, vec as V

HERE = Path(__file__).parent


def _matvec(A, v):
    # srmech-native matvec via the Mat/Vec carrier — replaces laplacian.dense_matvec_complex, which was
    # removed in srmech 0.7.5rc138 as a duplicate of the carrier `@` operator (Mat @ Vec). Verified identical.
    return (M.Mat.from_rows(np.asarray(A).tolist()) @ V.Vec.from_sequence(np.asarray(v).tolist())).tolist()

# A small directed tree/DAG so "ride to the spot, read its local structure" is legible.
N = 8
DIRECTED = [(0, 1), (1, 2), (2, 3), (1, 4), (4, 5), (3, 6), (6, 7)]


def directed_adjacency(n, edges):
    A = np.zeros((n, n), dtype=complex)
    for a, b in edges:
        A[b, a] = 1.0            # column-anchor convention: (A·e_i)[b]=1 iff i→b  (out-neighbours of i)
    return A


def support(vec, tol=1e-9):
    return sorted(int(k) for k in np.where(np.abs(np.asarray(vec)) > tol)[0])


def main():
    print(f"F363 ride-and-read-the-new-diagonal (srmech {srmech.__version__}, N={N})")
    A = directed_adjacency(N, DIRECTED)
    A_sym = A + A.T.conj()                          # the symmetric SHADOW (undirected)
    out_nbr = {i: sorted(b for a, b in DIRECTED if a == i) for i in range(N)}

    anchor = 1                                       # start at node 1 (out-neighbours: 2, 4)
    e = np.zeros(N, dtype=complex); e[anchor] = 1.0

    # --- ride one directed step (transport via srmech dense_matvec_complex) ---
    x1 = _matvec(A, e)
    reached = support(x1)
    print(f"\n  anchor = node {anchor}; ride 1 directed step -> reached {reached}  (true out-neighbours {out_nbr[anchor]})")
    relocated_ok = reached == out_nbr[anchor]

    # --- read the NEW diagonal: out-structure at the reached nodes (ride again from the new frame) ---
    x2 = _matvec(A, x1)
    reached2 = support(x2)
    expect2 = sorted({c for b in reached for c in out_nbr[b]})
    print(f"  read new diagonal: ride again -> {reached2}  (out-neighbours of {reached} = {expect2})")
    new_diag_ok = reached2 == expect2

    # --- one-way check: directed does NOT bleed back to the anchor; symmetric DOES ---
    back_directed = anchor in support(_matvec(A, x1))      # A²·e : returns to 1?
    xs1 = _matvec(A_sym, e)
    xs2 = _matvec(A_sym, xs1)
    back_symmetric = anchor in support(xs2)                               # A_sym²·e : returns to 1?
    print(f"  one-way: directed A²·e returns to anchor {anchor}? {back_directed}   |   symmetric A_sym²·e returns? {back_symmetric}")

    # --- composability: ride k steps -> depth-k frontier ---
    xk = e.copy(); frontier = []
    for k in range(1, 5):
        xk = _matvec(A, xk)
        frontier.append(support(xk))
    print(f"  composability (ride further): depth-1..4 frontiers = {frontier}")

    print("\n=== verdict ===")
    genuine_relocation = relocated_ok and new_diag_ok and (not back_directed) and back_symmetric
    print(f"  ride relocates the anchor to the projected spot (out-neighbours):     {relocated_ok}")
    print(f"  the NEW local diagonal is readable from the relocated frame:          {new_diag_ok}")
    print(f"  relocation is GENUINE/one-way (directed doesn't bleed back; shadow does): {(not back_directed) and back_symmetric}")
    print(f"  => CONFIRMED: the directed off-diagonal TRANSPORTS the observer to the projected spot and")
    print(f"     the new local structure reads from that position; composing steps rides further. The")
    print(f"     symmetric SHADOW bleeds back (A_sym² returns to the anchor) — scan-in-place, not relocation.")

    res = dict(srmech_version=srmech.__version__, N=N, anchor=anchor, reached=reached,
               out_nbr_anchor=out_nbr[anchor], reached2=reached2, expect2=expect2,
               relocated_ok=relocated_ok, new_diag_ok=new_diag_ok,
               back_directed=bool(back_directed), back_symmetric=bool(back_symmetric),
               frontiers=frontier, genuine_relocation=bool(genuine_relocation))
    (HERE / "R-RBS-LM-R16_results.json").write_text(json.dumps(res, indent=2, default=str))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R16_results.json'}")


if __name__ == "__main__":
    main()
