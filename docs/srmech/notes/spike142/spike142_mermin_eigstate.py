"""Identify the +4 eigenstate of the Mermin operator and verify
the GHZ-equivalent state achieves M=4 via the standard Mermin construction.

The Mermin operator with X-Y choice:
   M_op = XXY + XYX + YXX - YYY

Has spectrum ±4, 0, 0, 0, 0, 0, 0. The +4 eigenstate is a GHZ-class state
in the rotated basis. The original Mermin 1990 construction uses
|psi> = (|+++> + |--->)/sqrt(2) or equivalent, NOT |GHZ> = (|000>+|111>)/sqrt(2)
directly.

Actually the standard GHZ violation: |GHZ> achieves M=4 with the operator
M' = XXX - XYY - YXY - YYX. The +/- choice of which Mermin operator depends
on the GHZ-class state (e.g., GHZ+ achieves M=4 with one choice, GHZ-
achieves M=4 with the dual choice).
"""

import sys
import math
from pathlib import Path

WORKTREE_ROOT = Path(r"D:\GitHub\mlehaptics\.claude\worktrees\agent-ad0af059e53cd4257")
SRMECH_PYTHON = WORKTREE_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PYTHON))

import numpy as np
from srmech.qm.spin import pauli_matrices
from srmech.amsc.laplacian import hermitian_eigendecompose


def _kron3(a, b, c):
    return np.kron(np.kron(a, b), c)


X, Y, Z = pauli_matrices()
I_2 = np.eye(2, dtype=complex)

# ----- Mermin 1990 canonical form -----
# Mermin's operator in original paper:
#   M' = sigma_x_1 sigma_y_2 sigma_y_3 + sigma_y_1 sigma_x_2 sigma_y_3 + sigma_y_1 sigma_y_2 sigma_x_3 - sigma_x_1 sigma_x_2 sigma_x_3
# This achieves M=4 on |GHZ+> = (|000> + |111>)/sqrt(2)

M_mermin = _kron3(X, Y, Y) + _kron3(Y, X, Y) + _kron3(Y, Y, X) - _kron3(X, X, X)
eigvals, V = hermitian_eigendecompose(M_mermin)
norm = float(np.max(np.abs(eigvals)))
print(f"M_mermin (Mermin 1990 form XYY+YXY+YYX-XXX):")
print(f"  ||M_mermin|| = {norm:.12f}")
print(f"  Spectrum: {sorted(eigvals.real, reverse=True)}")

# GHZ+ state
psi_ghz_plus = np.zeros(8, dtype=complex)
psi_ghz_plus[0] = 1.0 / math.sqrt(2.0)
psi_ghz_plus[7] = 1.0 / math.sqrt(2.0)
expect_plus = complex(psi_ghz_plus.conj() @ M_mermin @ psi_ghz_plus)
print(f"\n  <GHZ+|M_mermin|GHZ+> = {expect_plus}")

# GHZ- state
psi_ghz_minus = np.zeros(8, dtype=complex)
psi_ghz_minus[0] = 1.0 / math.sqrt(2.0)
psi_ghz_minus[7] = -1.0 / math.sqrt(2.0)
expect_minus = complex(psi_ghz_minus.conj() @ M_mermin @ psi_ghz_minus)
print(f"  <GHZ-|M_mermin|GHZ-> = {expect_minus}")

# Save record
import json
out_path = WORKTREE_ROOT / "docs" / "srmech" / "notes" / "spike142" / "spike142_mermin_eigstate.ndjson"
record = {
    "spike": "#142",
    "kind": "mermin-eigstate-identification",
    "operator_form": "Mermin 1990: XYY + YXY + YYX - XXX",
    "operator_norm": float(norm),
    "spectrum_sorted": [float(e) for e in sorted(eigvals.real, reverse=True)],
    "ghz_plus_expectation": {"real": float(expect_plus.real), "imag": float(expect_plus.imag)},
    "ghz_minus_expectation": {"real": float(expect_minus.real), "imag": float(expect_minus.imag)},
}
with open(out_path, "w") as f:
    f.write(json.dumps(record) + "\n")
print(f"\nNDJSON: {out_path}")
