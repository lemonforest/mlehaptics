"""
Eigenvalue-spacing statistics — universality across project Laplacians (2026-05-12).

User question reframed: "are eigenvalue spacings of these different Laplacians
drawn from the same universal statistical distribution?"

Connection to Maass forms (per prior conversation):
- Maass-form spectra famously obey GUE (Gaussian Unitary Ensemble) statistics
  — this is the Bohigas-Giannoni-Schmit conjecture for quantum chaotic systems
- Selberg trace formula links Maass eigenvalues to closed geodesic lengths
  on hyperbolic surfaces; the spectrum's STATISTICAL signature is GUE
- Asking "are our Laplacians Maass-like?" is equivalent to asking
  "are they in the GUE universality class?"

The Wigner-Dyson universality classes for random-matrix theory:
- POISSON: integrable / non-interacting systems; P(s) = exp(-s)
- GOE (Gaussian Orthogonal): real-symmetric, time-reversal-symmetric chaotic
  systems; P(s) ≈ (π/2) s exp(-π s² / 4)
- GUE (Gaussian Unitary): complex Hermitian, broken time-reversal chaotic
  systems; P(s) ≈ (32/π²) s² exp(-4 s² / π)

NORMAL graph Laplacians (real-symmetric) → if chaotic, GOE; if integrable,
Poisson. To get GUE, we need broken time-reversal (e.g., magnetic flux,
U(1) gauge connection — like the toroidal magnetic Laplacian from PR #331).

Spike tests 5+ Laplacians for which universality class they inhabit.

Reproduce: `python -X utf8 docs/srmech/notes/eigenvalue_spacing_statistics_script.py`
Deterministic seed 20260512. Reuses cached PDB files from PR #333.
"""

import time
import json
import urllib.request
import numpy as np
import scipy.sparse as sp
import scipy.linalg
import scipy.stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "eigenvalue-spacing-statistics-per-laplacian-2026-05-12.ndjson"


# ─── Theoretical universality distributions ───────────────────────────────

def poisson_pdf(s):
    """Integrable systems."""
    return np.exp(-s)


def goe_pdf(s):
    """Wigner surmise for real-symmetric Gaussian Orthogonal Ensemble."""
    return (np.pi / 2) * s * np.exp(-np.pi * s**2 / 4)


def gue_pdf(s):
    """Wigner surmise for complex Hermitian Gaussian Unitary Ensemble."""
    return (32 / np.pi**2) * s**2 * np.exp(-4 * s**2 / np.pi)


def gse_pdf(s):
    """Symplectic (rarely seen) — included for completeness."""
    return (2**18 / (3**6 * np.pi**3)) * s**4 * np.exp(-64 * s**2 / (9 * np.pi))


# ─── Spectrum unfolding ────────────────────────────────────────────────────

def unfold_spectrum(eigenvalues: np.ndarray, drop_frac: float = 0.05) -> np.ndarray:
    """
    Unfold spectrum: normalize so the local mean spacing is 1 across the
    range. Standard technique: fit cumulative density N(E), then unfolded
    eigenvalues are N(eigenvalues).

    Drop top/bottom 5% of eigenvalues (edge effects in finite spectrum).
    """
    w = np.sort(eigenvalues.real)
    n = len(w)
    drop = int(drop_frac * n)
    if drop > 0:
        w = w[drop:n - drop]
    # Fit smoothed cumulative density via polynomial of degree 8
    indices = np.arange(len(w))
    # Standard unfolding: use rank as smoothed N(E)
    # Polynomial fit to (eigenvalue, rank) -> smooth N(E)
    deg = min(8, len(w) // 4)
    if deg < 2:
        return w
    coeffs = np.polyfit(w, indices, deg)
    unfolded = np.polyval(coeffs, w)
    return unfolded


def nearest_neighbor_spacings(unfolded: np.ndarray) -> np.ndarray:
    """Differences of consecutive sorted unfolded eigenvalues."""
    sorted_unfolded = np.sort(unfolded)
    spacings = np.diff(sorted_unfolded)
    # Spacings should average to ~1 after unfolding; normalize anyway
    spacings = spacings / spacings.mean() if spacings.mean() > 0 else spacings
    return spacings


def classify_universality(spacings: np.ndarray):
    """KS-test against Poisson, GOE, GUE. Return KS statistic for each."""
    classes = {"poisson": poisson_pdf, "goe": goe_pdf, "gue": gue_pdf}
    results = {}
    for name, pdf in classes.items():
        # CDF for each
        def cdf(s, pdf_fn=pdf):
            from scipy.integrate import quad
            return quad(pdf_fn, 0, s)[0]
        cdf_vals = np.array([cdf(s) for s in np.sort(spacings)])
        emp = np.arange(1, len(spacings) + 1) / len(spacings)
        ks_stat = np.max(np.abs(emp - cdf_vals))
        results[name] = float(ks_stat)
    best = min(results, key=results.get)
    return results, best


# ─── Laplacian builders ────────────────────────────────────────────────────

def chess_board_laplacian():
    """8×8 chess board graph Laplacian (king-move adjacency)."""
    n = 8
    coords = [(i, j) for i in range(n) for j in range(n)]
    N = len(coords)
    A = np.zeros((N, N))
    for a in range(N):
        for b in range(a + 1, N):
            di = abs(coords[a][0] - coords[b][0])
            dj = abs(coords[a][1] - coords[b][1])
            if max(di, dj) == 1:  # king-move adjacency
                A[a, b] = 1
                A[b, a] = 1
    D = np.diag(A.sum(axis=1))
    return D - A


def cycle_laplacian(n):
    """C_n cycle graph — integrable, expected Poisson (sparse spectrum)."""
    A = np.zeros((n, n))
    for i in range(n):
        A[i, (i + 1) % n] = 1
        A[(i + 1) % n, i] = 1
    D = np.diag(A.sum(axis=1))
    return D - A


def magnetic_torus_laplacian(N: int, flux: float):
    """
    Toroidal N×N graph with U(1) magnetic flux φ in Landau gauge.
    Complex Hermitian — should be in GUE universality class.

    From PR #331 (Hopf-fibration spike). At flux=0, this is identity; for
    flux > 0, Wilson-loop holonomy breaks time-reversal symmetry.
    """
    n = N * N
    A = np.zeros((n, n), dtype=np.complex128)
    for i in range(N):
        for j in range(N):
            v = i * N + j
            j_plus = (j + 1) % N
            i_plus = (i + 1) % N
            v_right = i * N + j_plus
            v_down = i_plus * N + j
            # x-direction hop: no phase
            A[v, v_right] = 1.0
            A[v_right, v] = 1.0
            # y-direction hop: Landau gauge phase
            phase = np.exp(2j * np.pi * flux * i / N)
            A[v, v_down] = phase
            A[v_down, v] = np.conj(phase)
    D = np.diag(np.full(n, 4.0))
    return D - A


def fetch_pdb_ca(pdb_id: str) -> np.ndarray:
    cache = OUT_DIR / f"{pdb_id}.pdb"
    if not cache.exists():
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        req = urllib.request.Request(url, headers={"User-Agent": "srmech-spike/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            cache.write_text(resp.read().decode("utf-8"))
    coords = []
    seen = set()
    chain_id = None
    for line in cache.read_text().splitlines():
        if not line.startswith("ATOM"):
            continue
        if line[12:16].strip() != "CA":
            continue
        if line[16:17] not in (" ", "A"):
            continue
        c = line[21:22]
        res_seq = line[22:26].strip()
        if chain_id is None:
            chain_id = c
        elif c != chain_id:
            continue
        key = (c, res_seq)
        if key in seen:
            continue
        seen.add(key)
        coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return np.array(coords)


def protein_L0_laplacian(pdb_id: str, cutoff: float = 8.0):
    coords = fetch_pdb_ca(pdb_id)
    n = coords.shape[0]
    dists = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
    A = ((dists < cutoff) & ~np.eye(n, dtype=bool)).astype(float)
    D = np.diag(A.sum(axis=1))
    return D - A


def protein_L1_laplacian(pdb_id: str, cutoff: float = 8.0):
    """Edge Hodge Laplacian L_1 = B^T B + C C^T from PR #333 Hodge spike."""
    coords = fetch_pdb_ca(pdb_id)
    n = coords.shape[0]
    dists = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
    adj = (dists < cutoff) & ~np.eye(n, dtype=bool)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if adj[i, j]]
    edge_idx = {e: i for i, e in enumerate(edges)}
    triangles = []
    for i in range(n):
        for j in range(i + 1, n):
            if not adj[i, j]:
                continue
            for k in range(j + 1, n):
                if adj[i, k] and adj[j, k]:
                    triangles.append((i, j, k))
    n_e = len(edges)
    B = np.zeros((n, n_e))
    for e, (i, j) in enumerate(edges):
        B[i, e] = -1
        B[j, e] = +1
    C = np.zeros((n_e, len(triangles)))
    for t, (i, j, k) in enumerate(triangles):
        C[edge_idx[(i, j)], t] = +1
        C[edge_idx[(i, k)], t] = -1
        C[edge_idx[(j, k)], t] = +1
    return B.T @ B + C @ C.T


def random_goe_matrix(n: int):
    """Synthetic GOE control: real symmetric, normal entries."""
    A = RNG.standard_normal((n, n))
    A = (A + A.T) / 2
    return A


def random_gue_matrix(n: int):
    """Synthetic GUE control: complex Hermitian, normal entries."""
    A = RNG.standard_normal((n, n)) + 1j * RNG.standard_normal((n, n))
    A = (A + A.conj().T) / 2
    return A


def random_poisson_eigenvalues(n: int):
    """Synthetic Poisson control: independent uniform eigenvalues."""
    return np.sort(RNG.uniform(0, 1, size=n))


# ─── Analysis pipeline ────────────────────────────────────────────────────

def analyze_laplacian(name: str, matrix: np.ndarray, expected: str = None):
    """Compute spectrum + NNS + universality classification."""
    is_complex = np.iscomplexobj(matrix)
    if matrix.ndim == 2 and matrix.shape[0] == matrix.shape[1]:
        w = scipy.linalg.eigvalsh(matrix)
    else:
        w = np.asarray(matrix).ravel()  # already eigenvalues
    n = len(w)
    unfolded = unfold_spectrum(w)
    spacings = nearest_neighbor_spacings(unfolded)
    ks_results, best = classify_universality(spacings)

    print(f"\n  {name} (n={n}, {'complex' if is_complex else 'real'}):")
    print(f"    spectrum range: [{w.min():.4f}, {w.max():.4f}]")
    print(f"    NNS count: {len(spacings)}")
    print(f"    KS distance to Poisson: {ks_results['poisson']:.4f}")
    print(f"    KS distance to GOE:     {ks_results['goe']:.4f}")
    print(f"    KS distance to GUE:     {ks_results['gue']:.4f}")
    expectation_marker = ""
    if expected:
        match = "✓" if best == expected else "✗"
        expectation_marker = f"  (expected: {expected} {match})"
    print(f"    → BEST FIT: {best.upper()}{expectation_marker}")

    return {
        "name": name,
        "n": int(n),
        "is_complex": bool(is_complex),
        "spectrum_min": float(w.min()),
        "spectrum_max": float(w.max()),
        "nns_count": int(len(spacings)),
        "ks_poisson": ks_results["poisson"],
        "ks_goe": ks_results["goe"],
        "ks_gue": ks_results["gue"],
        "best_fit": best,
        "expected": expected,
        "spacings": spacings,
    }


def plot_nns_histogram(results, out_path):
    """Plot empirical NNS histograms vs theoretical Wigner-Dyson curves."""
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    s_range = np.linspace(0.01, 4, 200)
    for i, r in enumerate(results):
        if i >= len(axes):
            break
        ax = axes[i]
        spacings = r["spacings"]
        ax.hist(spacings, bins=30, density=True, alpha=0.6, label=f"n={r['n']}")
        ax.plot(s_range, poisson_pdf(s_range), 'k--', label="Poisson", linewidth=1)
        ax.plot(s_range, goe_pdf(s_range), 'b-', label="GOE", linewidth=1.5)
        ax.plot(s_range, gue_pdf(s_range), 'r-', label="GUE", linewidth=1.5)
        ax.set_xlim(0, 4)
        ax.set_ylim(0, 1.2)
        ax.set_xlabel("s (unfolded spacing)")
        ax.set_ylabel("P(s)")
        ax.set_title(f"{r['name']}\nbest: {r['best_fit'].upper()}", fontsize=10)
        if i == 0:
            ax.legend(loc="upper right", fontsize=8)
    for i in range(len(results), len(axes)):
        axes[i].axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=110)
    plt.close()


def main():
    print("=== Eigenvalue-spacing statistics across project Laplacians ===")
    print(f"Seed: {SEED}")
    print()

    results = []

    # ─── Synthetic controls ─────────────────────────────────────────────────
    print("--- Synthetic controls (expected universality classes) ---")
    results.append(analyze_laplacian("synthetic_GOE_500", random_goe_matrix(500), expected="goe"))
    results.append(analyze_laplacian("synthetic_GUE_500", random_gue_matrix(500), expected="gue"))
    results.append(analyze_laplacian("synthetic_Poisson_500", random_poisson_eigenvalues(500), expected="poisson"))

    # ─── Project Laplacians ─────────────────────────────────────────────────
    print()
    print("--- Project Laplacians ---")

    # Chess 8x8 king-move
    results.append(analyze_laplacian("chess_8x8_kingmove_L0", chess_board_laplacian()))

    # Integrable control: cycle graph C_100
    results.append(analyze_laplacian("cycle_C100_integrable", cycle_laplacian(100)))

    # Magnetic toroidal — PR #331 finding, complex Hermitian (should be GUE)
    results.append(analyze_laplacian("magnetic_torus_8x8_flux1", magnetic_torus_laplacian(8, flux=1.0)))

    # Same but irrational flux (golden ratio) — should break band structure → GUE
    GOLDEN = (np.sqrt(5) - 1) / 2  # 0.618...
    results.append(analyze_laplacian("magnetic_torus_16x16_golden_flux",
                                      magnetic_torus_laplacian(16, flux=GOLDEN), expected="gue"))

    # Protein 1UBQ L_0 (vertex Laplacian)
    results.append(analyze_laplacian("protein_1ubq_L0", protein_L0_laplacian("1UBQ")))

    # Protein 1UBQ L_1 (edge Hodge Laplacian — from PR #333)
    results.append(analyze_laplacian("protein_1ubq_L1_hodge", protein_L1_laplacian("1UBQ")))

    # Bigger protein for better statistics — use a longer one if available
    # Skip if 1UBQ is sufficient

    # ─── Universality verdict ──────────────────────────────────────────────
    print()
    print("=== Universality verdict ===")
    print(f"{'Laplacian':<32s} {'Best fit':<10s} {'KS-Poisson':>10s} {'KS-GOE':>10s} {'KS-GUE':>10s}")
    print("-" * 75)
    for r in results:
        print(f"{r['name']:<32s} {r['best_fit']:<10s} {r['ks_poisson']:>10.4f} {r['ks_goe']:>10.4f} {r['ks_gue']:>10.4f}")

    # Strip spacings before serialization
    records_for_json = []
    for r in results:
        r_copy = {k: v for k, v in r.items() if k != "spacings"}
        records_for_json.append(r_copy)

    with open(RESULTS_FILE, "w") as f:
        for r in records_for_json:
            f.write(json.dumps(r) + "\n")

    plot_nns_histogram(results, OUT_DIR / "eigenvalue-spacing-histograms-2026-05-12.png")

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    eigenvalue-spacing-histograms-2026-05-12.png")

    # ─── Headline interpretation ───────────────────────────────────────────
    print()
    print("=== Interpretation ===")
    project_results = [r for r in results if not r["name"].startswith("synthetic")]
    classes_found = set(r["best_fit"] for r in project_results)
    print(f"Project Laplacian universality classes found: {classes_found}")
    print(f"Synthetic controls hit expected class: "
          f"{sum(1 for r in results[:3] if r['best_fit'] == r['expected'])}/3")
    if "gue" in classes_found:
        gue_ones = [r["name"] for r in project_results if r["best_fit"] == "gue"]
        print(f"GUE (Maass-class) Laplacians: {gue_ones}")


if __name__ == "__main__":
    main()
