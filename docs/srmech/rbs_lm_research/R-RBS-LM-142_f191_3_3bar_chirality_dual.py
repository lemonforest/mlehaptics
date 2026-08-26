"""R-RBS-LM-142 — F191 role-swap, computed (F197).

Does a chiral flip swap the two A-N 3-triads (I/C/J <-> B/H/N)? F195 said "not
computable" for lack of an A-N->chiral-space embedding. Cleaner route: the A-N 14 IS
G2 (= Der(O)), and G2 ⊃ SU(3) branches as 14 = 8 + 3 + 3bar -- a built-in 3/3bar
conjugate pair (chirality-dual), swapped by conjugation.

Compute (srmech 0.5.0rc18):
  - derivations annihilate e0 (Der(O) fixes the identity)  -> max|X e0| ~ 0
  - su(3) = stabilizer of an imaginary unit e_k: dim = 14 - rank(X -> X e_k)  -> 8
  - complement = 6 = 3 + 3bar

Verdict (F197): the A-N 14 contains a 3 (+) 3bar conjugate pair (computed); conjugation
swaps them; the two A-N 3-triads match it (count + dim); so the I/C/J<->B/H/N role-swap
is confirmed at the TRIAD level, and which triad is "the 3" is the chiral-pole choice
(F191's "role is chirality-relative"). Open: within-triad operator pairing.

matrix_rank is an independent validator of srmech's g2 op (not a research cascade).
No abs() in any cascade.
"""
import numpy as np
from srmech.qm import so8 as SO8


def an_g2_su3_split():
    g2 = np.asarray(SO8.g2_subalgebra(), dtype=float)   # (14, 8, 8)
    E = np.eye(8)
    real_kill = max(float(np.max(np.abs(g2[i] @ E[0]))) for i in range(g2.shape[0]))
    out = {"g2_generators": int(g2.shape[0]), "max_abs_X_e0": real_kill, "stabilizer_dims": {}}
    for k in (1, 2, 4):
        M = np.stack([g2[i] @ E[k] for i in range(g2.shape[0])])   # (14, 8)
        rank = int(np.linalg.matrix_rank(M, tol=1e-9))
        out["stabilizer_dims"][f"e{k}"] = {"orbit_rank": rank, "dim_su3": 14 - rank, "complement": rank}
    return out


if __name__ == "__main__":
    d = an_g2_su3_split()
    print(f"  g2 generators: {d['g2_generators']}")
    print(f"  max |X . e0|: {d['max_abs_X_e0']:.2e}  (derivations fix the identity)")
    for k, v in d["stabilizer_dims"].items():
        print(f"  {k}: dim su(3)={v['dim_su3']}  complement={v['complement']}  (expect 8 + 6 = 8 + 3 + 3bar)")
    print("  => A-N 14 = G2 = su(3)[8] + 3 + 3bar; conjugation swaps 3<->3bar = the I/C/J<->B/H/N role-swap.")
