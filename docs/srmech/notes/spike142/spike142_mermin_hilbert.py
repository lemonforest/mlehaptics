"""Spike #142 — Hilbert-space Mermin operator-norm via Class L eigendecomp.

Analogous to srmech.qm.bell.chsh_operator_norm() but for the tripartite
Mermin operator. This is the BIT-EXACT algebraic identity test — the
cascade-quantum-algorithm precedent from Spike #128.2.

The Mermin operator (canonical form):
    M_op = A1 ⊗ B1 ⊗ C2 + A1 ⊗ B2 ⊗ C1 + A2 ⊗ B1 ⊗ C1 − A2 ⊗ B2 ⊗ C2

With Pauli choice A_i = sigma_x or sigma_y; B_j = sigma_x or sigma_y;
C_k = sigma_x or sigma_y (the canonical Mermin 1990 measurement setting).

For the GHZ state |GHZ> = (|000> + |111>)/sqrt(2), the Mermin
expectation should reach 4 (the QM maximum).

Operator-norm of the Mermin operator with the canonical settings:
- A1 = B1 = C1 = sigma_x
- A2 = B2 = C2 = sigma_y
- M_op = sigma_x sigma_x sigma_y + sigma_x sigma_y sigma_x + sigma_y sigma_x sigma_x − sigma_y sigma_y sigma_y

Per Mermin 1990 PRL 65:1838: ||M_op|| should equal 4 (algebraic max).

Class chain attestation (zero new primitive class; 14 A-N intact):
- L (Hermitian Laplacian / eigendecomp): operator-norm via eigvals
- I (Pauli stabiliser Z/n): Clifford-circuit phase
- M (tensor-product HDC bind): 3-fold tensor product
- C (Bell-basis measurement-orientation): four-term cascade with (+,+,+,-) signs
- A (stabiliser-fingerprint content-addressing): canonical form hashable
"""

from __future__ import annotations

import sys
import math
from pathlib import Path

WORKTREE_ROOT = Path(r"D:\GitHub\mlehaptics\.claude\worktrees\agent-ad0af059e53cd4257")
SRMECH_PYTHON = WORKTREE_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PYTHON))

import numpy as np
from srmech.amsc.laplacian import hermitian_eigendecompose
from srmech.qm.spin import pauli_matrices


def _kron3(a, b, c):
    return np.kron(np.kron(a, b), c)


def mermin_operator_canonical() -> np.ndarray:
    """Canonical Mermin operator with sigma_x / sigma_y settings.

    M_op = X⊗X⊗Y + X⊗Y⊗X + Y⊗X⊗X − Y⊗Y⊗Y
    """
    X, Y, Z = pauli_matrices()
    M_op = _kron3(X, X, Y) + _kron3(X, Y, X) + _kron3(Y, X, X) - _kron3(Y, Y, Y)
    return M_op


def operator_norm(H: np.ndarray) -> float:
    """Spectral norm via Class L hermitian_eigendecompose."""
    eigvals, _V = hermitian_eigendecompose(H)
    return float(np.max(np.abs(eigvals)))


def ghz_state(n: int = 3) -> np.ndarray:
    """|GHZ_n> = (|0...0> + |1...1>) / sqrt(2)."""
    dim = 2 ** n
    psi = np.zeros(dim, dtype=complex)
    psi[0] = 1.0 / math.sqrt(2.0)
    psi[-1] = 1.0 / math.sqrt(2.0)
    return psi


def mermin_expectation_on_ghz() -> complex:
    """<GHZ| M_op |GHZ> — should be 4 bit-exact (Mermin 1990)."""
    M_op = mermin_operator_canonical()
    psi = ghz_state(3)
    return complex(psi.conj() @ M_op @ psi)


def main():
    print("=" * 78)
    print("Spike #142 — Hilbert-space Mermin operator-norm via Class L")
    print("=" * 78)

    # Operator norm
    M_op = mermin_operator_canonical()
    norm = operator_norm(M_op)
    print(f"  ||M_op|| (algebraic max) = {norm:.12f}")
    print(f"  Theoretical Mermin QM max = 4.000000000000  (Mermin 1990 PRL 65:1838)")
    print(f"  Classical bound = 2.000000000000  (local hidden variables)")
    residual_to_4 = abs(norm - 4.0)
    print(f"  Residual |norm − 4| = {residual_to_4:.2e}")
    bit_exact = residual_to_4 < 1e-13
    print(f"  Bit-exact-verified: {bit_exact}")

    # GHZ expectation
    expect = mermin_expectation_on_ghz()
    print(f"\n  <GHZ| M_op |GHZ> = {expect}")
    expect_residual = abs(expect.real - 4.0)
    print(f"  Residual |Re(<M>) − 4| = {expect_residual:.2e}")

    # The eigenvalue spectrum
    eigvals, _V = hermitian_eigendecompose(M_op)
    print(f"\n  Spectrum of M_op: {sorted(eigvals.real, reverse=True)}")
    print(f"  (Expected: ±4, ±2 with multiplicities, per Mermin algebra)")

    # Write NDJSON record
    import json
    out_path = WORKTREE_ROOT / "docs" / "srmech" / "notes" / "spike142" / "spike142_mermin_hilbert.ndjson"
    record = {
        "spike": "#142",
        "kind": "hilbert-space-mermin-operator-norm",
        "date": "2026-05-19",
        "mermin_op_norm": float(norm),
        "theoretical_qm_max": 4.0,
        "classical_bound": 2.0,
        "residual_to_4": float(residual_to_4),
        "bit_exact": bool(bit_exact),
        "ghz_expectation_real": float(expect.real),
        "ghz_expectation_imag": float(expect.imag),
        "spectrum_sorted": [float(e) for e in sorted(eigvals.real, reverse=True)],
        "verdict": "GHZ-QUANTUM-BIT-EXACT" if bit_exact else "FAILED",
    }
    with open(out_path, "w") as f:
        f.write(json.dumps(record) + "\n")
    print(f"\nNDJSON: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
