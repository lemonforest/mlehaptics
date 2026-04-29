"""qm_4d Experiment 2: bishop wavefunction time-evolution.

Demonstrates the kinematic API by evolving a localized 'bishop
wavefunction' under U(t) = exp(-i H_bishop_4 t / |H|_max). This is
a clean toy QM evolution on the 4096-square Hilbert space using
the chess_spectral.qm_4d Hermitian observable for the bishop.

Setup
-----

  1. Pick a starting square s0 (e.g. center of the 8^4 board).
  2. Compute the legal bishop destinations from s0 on an empty
     board via tables_4d.bishop4_targets.
  3. Initial state psi_0 has equal positive amplitude on each
     bishop destination, normalised. Note: psi_0 is in the
     POSITION basis (one entry per square), not in the encoder's
     mode basis.
  4. Evolve under U(t) = exp(-i H t / lambda_max) for several t
     in {0, 0.1, 0.5, 1.0, 2.0, 5.0}. The lambda_max
     normalisation makes 't' dimensionless and roughly comparable
     to a 'fraction of one cycle of the highest-frequency mode'.
  5. At each step record the position-space probability density
     |psi(s, t)|^2 for s = 0..4095 and the per-channel
     bishop-coupling expectation <psi|H|psi>.
  6. Save findings + 2D x-y projections of the position density
     as PNG (if matplotlib is available).

Outputs
-------
  stdout: per-time slice summaries (max prob, mean coupling)
  qm_bishop_wavefunction.json: full per-time numerics
  qm_bishop_wavefunction_t<k>.png: x-y projection at each time
    (only if matplotlib loads)

Run from python/ working directory:
  python research/qm_bishop_wavefunction.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import scipy.linalg as sla

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.dirname(THIS_DIR)
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

from chess_spectral import tables_4d as t4                  # noqa: E402
from chess_spectral import qm_4d                             # noqa: E402


def _utf8_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass


def _initial_bishop_state(s0: tuple[int, int, int, int]) -> np.ndarray:
    """Uniform-amplitude wavefunction over the bishop's reachable
    squares from s0 (excluding s0 itself). Returns a normalised
    4096-vector in sq4 ordering, complex128 dtype."""
    n = qm_4d.CHANNEL_DIM
    psi = np.zeros(n, dtype=np.complex128)
    targets = list(t4.bishop4_targets(*s0))
    if not targets:
        raise ValueError(
            f"no bishop targets from {s0} -- pick an interior square"
        )
    for t in targets:
        psi[t4.sq4(*t)] = 1.0
    psi /= np.linalg.norm(psi)
    return psi


def _ascii_xy_projection(psi: np.ndarray, label: str = "") -> str:
    """Sum |psi|^2 over (z, w) and render an 8x8 ASCII heatmap of the
    resulting (x, y) marginal. Returns a string."""
    n = t4.BOARD_SIDE
    rho = np.abs(psi) ** 2
    # Reshape to (x, y, z, w), then sum over axes 2, 3.
    rho4d = rho.reshape((n, n, n, n))
    marg_xy = rho4d.sum(axis=(2, 3))
    norm_max = float(marg_xy.max())
    grid = np.zeros_like(marg_xy, dtype=np.float64)
    if norm_max > 0:
        grid = marg_xy / norm_max
    # 5-step gradient.
    palette = " .:#@"
    lines = []
    if label:
        lines.append(f"  [{label}]  marginal max = {norm_max:.4e}")
    for ix in range(n):
        row = []
        for iy in range(n):
            v = grid[ix, iy]
            idx = min(int(v * (len(palette) - 1) + 0.5), len(palette) - 1)
            row.append(palette[idx])
        lines.append("    " + "".join(row))
    return "\n".join(lines)


def _maybe_save_xy_projection_png(
    psi: np.ndarray,
    out_path: Path,
    title: str,
) -> bool:
    """Save an x-y marginal heatmap as a PNG. Returns True if saved,
    False if matplotlib is unavailable."""
    try:
        import matplotlib  # noqa: F401
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    n = t4.BOARD_SIDE
    rho = (np.abs(psi) ** 2).reshape((n, n, n, n))
    marg_xy = rho.sum(axis=(2, 3))
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(marg_xy, cmap="viridis", origin="upper")
    fig.colorbar(im, ax=ax, label="probability mass")
    ax.set_xlabel("y")
    ax.set_ylabel("x")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return True


def main() -> int:
    _utf8_stdout()

    print("=" * 72)
    print("qm_4d Experiment 2: bishop wavefunction time evolution")
    print("=" * 72)
    print("Setup: H = H_bishop_4, U(t) = exp(-i H t / lambda_max).")
    print("Starting state: uniform amplitude over the bishop's reach.")
    print()

    # 1. Build H_bishop_4 (sparse) and a normalising scale.
    print("Building H_bishop_4 ...")
    H = qm_4d.build_H_piece_4('B')
    print(f"  shape = {H.shape}, nnz = {H.nnz}")

    # Normalising scale: largest |eigenvalue|. We use eigvalsh on the
    # dense form -- 4096x4096 fits comfortably and we need the
    # eigendecomposition for the matrix exponential below anyway.
    print("Diagonalising H_bishop_4 (dense eigh) ...")
    H_dense = H.toarray()
    eigvals, eigvecs = np.linalg.eigh(H_dense)
    lam_max = float(np.max(np.abs(eigvals)))
    print(f"  lambda range  = [{eigvals.min():.4f}, {eigvals.max():.4f}]")
    print(f"  |lambda|_max  = {lam_max:.4f}")
    if lam_max <= 0:
        raise RuntimeError("|lambda|_max non-positive; H is degenerate")

    # 2. Initial state: bishop at center (3, 3, 3, 3) -- a center
    # square reaches 42 destinations.
    s0 = (3, 3, 3, 3)
    psi_0 = _initial_bishop_state(s0)
    n_targets = int(np.count_nonzero(psi_0))
    print(f"  initial state: bishop at {s0}, "
          f"|psi_0> over {n_targets} reachable squares")

    # 3. Time grid.
    times = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]

    # Decompose psi_0 in H's eigenbasis. Then U(t) psi_0 has known
    # closed form in that basis: c_k(t) = c_k(0) exp(-i lam_k t / lam_max).
    coeffs0 = eigvecs.conj().T @ psi_0  # complex128 (4096,)

    findings = {
        "starting_square": list(s0),
        "n_initial_destinations": n_targets,
        "lam_max_for_normalisation": lam_max,
        "h_eigenvalue_range": [float(eigvals.min()),
                                 float(eigvals.max())],
        "times": list(times),
        "snapshots": [],
    }

    print()
    print("Time evolution (U(t) = exp(-i H t / |lambda|_max)):")
    print()
    print(f"{'t':>5}   {'<H>':>10}   {'max |psi|^2':>12}   "
          f"{'support':>9}   {'norm':>8}")
    print("-" * 60)

    for ti, t in enumerate(times):
        phases = np.exp(-1j * eigvals * (t / lam_max))
        coeffs_t = coeffs0 * phases
        psi_t = eigvecs @ coeffs_t
        # Diagnostics in the position basis (sq4).
        rho = (np.abs(psi_t) ** 2).real
        max_rho = float(rho.max())
        # support size: count squares with rho > 1e-6.
        support = int(np.count_nonzero(rho > 1e-6))
        n_t = float(np.linalg.norm(psi_t))
        # bishop coupling expectation -- should be conserved.
        e_h = qm_4d.expectation(H, psi_t)
        print(f"{t:>5.2f}   {e_h:>10.4f}   {max_rho:>12.4e}   "
              f"{support:>9d}   {n_t:>8.5f}")

        # Print x-y marginal ASCII heatmap.
        ascii_grid = _ascii_xy_projection(
            psi_t, label=f"t={t:.2f}"
        )
        print(ascii_grid)
        print()

        # Save PNG snapshot if matplotlib is available.
        out_png = Path(__file__).parent / (
            f"qm_bishop_wavefunction_t{ti}.png"
        )
        saved = _maybe_save_xy_projection_png(
            psi_t, out_png,
            title=f"|psi(x, y, *, *)|^2 at t = {t:.2f}",
        )
        if saved:
            print(f"  (saved {out_png.name})")

        findings["snapshots"].append({
            "t": float(t),
            "expectation_H_bishop": float(e_h),
            "max_position_prob": max_rho,
            "support_size_eps_1e-6": support,
            "norm": n_t,
        })

    # 4. Persist JSON findings.
    out_json = Path(__file__).with_suffix('.json')
    out_json.write_text(json.dumps(findings, indent=2))
    print(f"\nFindings written to {out_json}")

    # 5. Conservation cross-check: <H> should be t-independent for
    # closed-system evolution under U = exp(-iHt/lam_max).
    e_h_values = [s["expectation_H_bishop"] for s in findings["snapshots"]]
    drift = float(max(e_h_values) - min(e_h_values))
    print(f"<H>(t) drift over time grid: {drift:.3e}  "
          f"(should be ~0 for energy-conserving unitary evolution)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
