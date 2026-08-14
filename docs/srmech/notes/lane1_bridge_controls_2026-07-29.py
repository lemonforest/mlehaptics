"""LANE 1 part 2 — (i) beta of the REAL Clifford algebras (oracle) vs ours,
(ii) does the CONTINUOUS half already ship, (iii) the g_2 negative control.

Shipped ops as subject wherever one exists; the Cl(p,q) oracle is LABELLED.
"""
import json
import sys

sys.path.insert(0, "/mnt/d/GitHub/mlehaptics/docs/srmech/python")

from srmech.amsc.cascade.cayley_dickson import algebra_table
from srmech.qm.potentials import harmonic_oscillator_ladder
from srmech.qm.single_particle import commutator as qm_commutator
from srmech.qm.spin import pauli_clifford_residuals
from srmech.qm.relativistic import clifford_residuals
from srmech.qm.so8 import an_embedding, g2_subalgebra

OUT = []


def emit(rec):
    OUT.append(rec)
    print(json.dumps(rec, sort_keys=True, default=str))


def cl_eps(d, sq):
    """LABELLED ORACLE: Cl(p,q) cochain on subset-bitmask basis."""
    dim = 1 << d
    eps = [[0] * dim for _ in range(dim)]
    for S in range(dim):
        for T in range(dim):
            sign = 1
            for j in range(d):
                if not ((T >> j) & 1):
                    continue
                cross = 0
                for i in range(j + 1, d):
                    if (S >> i) & 1:
                        cross += 1
                if cross % 2 == 1:
                    sign = -sign
            for i in range(d):
                if ((S >> i) & 1) and ((T >> i) & 1):
                    sign = sign * sq[i]
            eps[S][T] = sign
    return eps


def beta_of(dim, eps):
    return [[eps[a][b] * eps[b][a] for b in range(dim)] for a in range(dim)]


def bichar_failures(dim, beta):
    n = 0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                if beta[a ^ b][c] != beta[a][c] * beta[b][c]:
                    n += 1
    return n


def radical(dim, beta):
    return [a for a in range(dim) if all(beta[a][b] == 1 for b in range(dim))]


# ---- (i) beta of the real Cl(0,d) vs the shipped CD beta ------------------
for d in (1, 2, 3, 4):
    dim = 1 << d
    tbl = algebra_table(dim)                       # SHIPPED
    cd_eps = [[tbl[a][b][a ^ b] for b in range(dim)] for a in range(dim)]
    cd_beta = beta_of(dim, cd_eps)
    ce = cl_eps(d, [-1] * d)                       # ORACLE Cl(0,d)
    cb = beta_of(dim, ce)
    same_beta = all(cd_beta[a][b] == cb[a][b] for a in range(dim) for b in range(dim))
    diff_cells = [(a, b) for a in range(dim) for b in range(dim) if cd_beta[a][b] != cb[a][b]]
    emit({"kind": "B1_beta_ours_vs_Cl_0_d", "d": d, "dim": dim,
          "Cl_0_d_beta_is_bicharacter": bichar_failures(dim, cb) == 0,
          "Cl_0_d_beta_radical": radical(dim, cb),
          "ours_beta_is_bicharacter": bichar_failures(dim, cd_beta) == 0,
          "ours_beta_radical": radical(dim, cd_beta),
          "betas_IDENTICAL": same_beta,
          "n_cells_where_beta_differs": len(diff_cells),
          "first_diff_cells": diff_cells[:8],
          "note": "Cl(0,3) beta has a RADICAL (its centre e_123) -> H(+)H; the "
                  "shipped dim-8 beta has trivial radical but is NOT a "
                  "bicharacter, so 'radical' is not even defined for it"})

# ---- (ii) the CONTINUOUS half: does the CCR already ship? ----------------
for n_dim in (4, 8, 30):
    a, ad = harmonic_oscillator_ladder(n_dim)      # SHIPPED
    comm = qm_commutator(a, ad)                    # SHIPPED
    diag = [comm[i, i] for i in range(n_dim)]
    # exact-in-spirit read: how many diagonal entries equal +1 to the last bit,
    # and what does the truncation boundary hold?  (float tier — the shipped
    # surface is float64; that IS the finding, not a measurement choice.)
    ones = sum(1 for k in range(n_dim - 1) if diag[k] == (1 + 0j))
    offdiag_all_zero = all(comm[i, j] == 0j for i in range(n_dim)
                           for j in range(n_dim) if i != j)
    emit({"kind": "B2_CCR_already_ships", "n_dim": n_dim,
          "route": "srmech.qm.potentials.harmonic_oscillator_ladder + "
                   "srmech.qm.single_particle.commutator",
          "diag_entries_exactly_plus1_excluding_boundary": ones,
          "of": n_dim - 1,
          "truncation_boundary_entry": str(diag[-1]),
          "offdiagonal_all_exactly_zero": offdiag_all_zero,
          "tier": "float64 (the shipped continuous surface is float; the "
                  "discrete side is exact int) "})

emit({"kind": "B3_clifford_CAR_side_already_ships",
      "pauli_clifford_residuals": list(pauli_clifford_residuals()),
      "relativistic_clifford_residuals": list(clifford_residuals()),
      "note": "{sigma_i,sigma_j}=2 delta_ij I and {gamma^mu,gamma^nu}=2 eta^{mu nu} "
              "are SHIPPED residual ops; float tier"})

# ---- (iii) g_2 NEGATIVE CONTROL: exhibit the ACTUAL branching ------------
g2 = g2_subalgebra()
emb = an_embedding(1)
keys = sorted(emb.keys())
summary = {}
for k in keys:
    v = emb[k]
    if isinstance(v, (int, float, str, bool)) or v is None:
        summary[k] = v
    elif isinstance(v, (list, tuple)):
        summary[k] = "list[%d]" % len(v)
    elif isinstance(v, dict):
        summary[k] = {kk: (vv if isinstance(vv, (int, float, str, bool)) or vv is None
                           else "list[%d]" % len(vv) if isinstance(vv, (list, tuple))
                           else type(vv).__name__) for kk, vv in sorted(v.items())}
    else:
        summary[k] = type(v).__name__
emit({"kind": "C1_g2_negative_control",
      "dim_g2_shipped": len(g2),
      "an_embedding_keys": keys,
      "an_embedding_summary": summary,
      "claim_tested": "does g_2 branch as 1+3+7+3 under ANY shipped subalgebra?",
      "note": "expect 8+3+3bar under su(3); NOT 1+3+7+3"})

with open("/mnt/d/GitHub/mlehaptics/docs/srmech/notes/lane1_bridge_controls_2026-07-29.ndjson", "w") as f:
    for r in OUT:
        f.write(json.dumps(r, sort_keys=True, default=str) + "\n")
print("WROTE", len(OUT), file=sys.stderr)
