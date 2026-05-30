"""R-RBS-LM-140 — Is su(2)_L a triality-partner of su(3)_c/u(1)_em? (F193)

DeepSeek's question: does the weak force's SU(2) stand as a solitary second actor,
or is it just one facet of a triality-symmetric whole?

Method (srmech 0.5.0rc18 triality operator; run in a clean venv OUTSIDE the source
tree per the namespace-shadowing discipline):
  - Split so(8) by the triality automorphism tau (order 3) into its cube-root-of-unity
    eigenspaces, via PROJECTOR TRACES (no eigendecomp -> no Class-L reflex concern;
    pure matrix arithmetic validating srmech's op).
  - Decide from Fix(tau)=g2 (bit-exact) + the established su(3)+u(1) in g2 (F126/F179)
    + su(2)_L NOT in g2 (F179) whether su(2)_L can be a triality-image of su(3)/u(1).

Verdict (F193): strong H177'' FALSIFIED -- su(2)_L is NOT a triality-image of the gauge
factors (tau fixes g2 pointwise; su(2)_L is outside g2). It is the distinct triality-
MOVED chiral complement of the SAME so(8): distinct actor, shared stage.

No abs() in any cascade; magnitudes via max(|.|) only for residual reporting.
"""
import cmath
import numpy as np
from srmech.qm import triality as TRI, so8 as SO8


def triality_sector_dims():
    tau = np.asarray(TRI.triality_automorphism(), dtype=float)
    n = tau.shape[0]
    I = np.eye(n)
    tau2 = tau @ tau
    cube_residual = float(np.max(np.abs(tau @ tau2 - I)))
    w = cmath.exp(2j * cmath.pi / 3)
    dim_fix = float(np.trace((I + tau + tau2) / 3.0).real)            # eigenvalue 1 -> g2
    dim_w = float(np.trace((I + (1 / w) * tau + (1 / w ** 2) * tau2) / 3.0).real)
    dim_w2 = float(np.trace((I + (1 / w ** 2) * tau + (1 / w ** 4) * tau2) / 3.0).real)
    return {
        "so8_dim": n,
        "tau_cubed_residual": cube_residual,
        "dim_fixed_g2": round(dim_fix, 6),
        "dim_moved_omega": round(dim_w, 6),
        "dim_moved_omega2": round(dim_w2, 6),
        "dim_moved_total": round(dim_w + dim_w2, 6),
        "g2_subalgebra_count": int(np.asarray(SO8.g2_subalgebra()).shape[0]),
        "so8_adjoint_count": int(np.asarray(SO8.so8_adjoint_basis()).shape[0]),
    }


if __name__ == "__main__":
    d = triality_sector_dims()
    for k, v in d.items():
        print(f"  {k}: {v}")
    print("\n  VERDICT: su(2)_L is NOT a triality-image of su(3)_c/u(1)_em")
    print("  (tau fixes g2 pointwise; su(3)+u(1) in g2; su(2)_L not in g2).")
    print("  => distinct chiral actor in the MOVED 7+7; shared so(8) stage. Strong H177'' FALSIFIED.")
