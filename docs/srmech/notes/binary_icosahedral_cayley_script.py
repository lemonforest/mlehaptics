"""
Binary icosahedral group 2I Cayley graph — exact S^3 discretization (2026-05-12).

PR #345 final future-work item. 2I is the binary icosahedral group, order
120, a finite subgroup of S^3 = SU(2). Its 120 elements are the vertices
of the 600-cell, which form a regular discrete sampling of S^3.

The Cayley graph Cay(2I, S) with symmetric generator set S has known
spectrum from character theory. We compute it numerically and compare
to the first 120 modes of continuum round S^3 (Δ eigenvalues l(l+2)
with degeneracy (l+1)²).

The 120 elements of 2I (as unit quaternions on S^3):
- 8 unit quaternions: (±1, 0, 0, 0), (0, ±1, 0, 0), (0, 0, ±1, 0), (0, 0, 0, ±1)
- 16 elements: (±1/2, ±1/2, ±1/2, ±1/2)
- 96 even permutations of (±1/2, ±φ/2, ±1/(2φ), 0) where φ = (1+√5)/2

Generators (the 24 = |2T| binary tetrahedral elements): the 8 unit-vector
quaternions + 16 sign combinations of (±1/2, ±1/2, ±1/2, ±1/2). Their
Cayley graph is well-defined.

Reproduce: `python -X utf8 docs/srmech/notes/binary_icosahedral_cayley_script.py`
Deterministic; no random sampling needed (group elements are exact).
"""

import json
from itertools import permutations
import numpy as np
import scipy.sparse as sp
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

PHI = (1 + np.sqrt(5)) / 2  # golden ratio
INV_PHI = 1 / PHI  # = phi - 1

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "binary-icosahedral-cayley-per-test-2026-05-12.ndjson"


def generate_2i_elements():
    """Return the 120 quaternion vertices of the 600-cell = elements of 2I."""
    elements = []
    # Type 1: 8 unit-vector quaternions
    for axis in range(4):
        for sign in [+1, -1]:
            q = [0, 0, 0, 0]
            q[axis] = sign
            elements.append(tuple(q))
    # Type 2: 16 elements (±1/2, ±1/2, ±1/2, ±1/2)
    for signs in range(16):
        s = [(+1 if (signs >> i) & 1 == 0 else -1) * 0.5 for i in range(4)]
        elements.append(tuple(s))
    # Type 3: 96 even permutations of (±1/2, ±φ/2, ±1/(2φ), 0)
    base = [0.5, PHI / 2, INV_PHI / 2, 0.0]
    seen_perms = set()
    for perm in permutations([0, 1, 2, 3]):
        # Permutation parity: even iff perm is an even permutation
        parity = 0
        p = list(perm)
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                if p[i] > p[j]:
                    parity += 1
        if parity % 2 != 0:
            continue
        if perm in seen_perms:
            continue
        seen_perms.add(perm)
        # For each sign combination of the 3 non-zero entries
        for signs in range(8):
            sx = +1 if (signs >> 0) & 1 == 0 else -1
            sy = +1 if (signs >> 1) & 1 == 0 else -1
            sz = +1 if (signs >> 2) & 1 == 0 else -1
            permuted = [base[perm.index(i)] for i in range(4)]
            # Apply signs to the non-zero positions
            nz_idx = [i for i in range(4) if permuted[i] != 0]
            permuted[nz_idx[0]] *= sx
            permuted[nz_idx[1]] *= sy
            permuted[nz_idx[2]] *= sz
            elements.append(tuple(round(x, 12) for x in permuted))
    # Deduplicate
    unique = list(set(elements))
    return [np.array(e) for e in unique]


def quaternion_multiply(p, q):
    """Hamilton product."""
    a, b, c, d = p
    e, f, g, h = q
    return np.array([
        a * e - b * f - c * g - d * h,
        a * f + b * e + c * h - d * g,
        a * g - b * h + c * e + d * f,
        a * h + b * g - c * f + d * e,
    ])


def find_element_index(q, elements, tol=1e-9):
    """Find index of quaternion q in the elements list (within tolerance)."""
    for i, e in enumerate(elements):
        if np.allclose(q, e, atol=tol):
            return i
    return -1


def build_cayley_graph(elements, generators):
    """Build Cayley graph: edge (i, j) if elements[j] = elements[i] · g for g in generators."""
    n = len(elements)
    rows, cols = [], []
    for i, g_i in enumerate(elements):
        for gen in generators:
            product = quaternion_multiply(g_i, gen)
            j = find_element_index(product, elements)
            if j >= 0 and j != i:
                rows.append(i); cols.append(j)
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    A = ((A + A.T) > 0).astype(float)
    return A.tocsr()


def normalized_laplacian(A):
    deg = np.asarray(A.sum(axis=1)).ravel()
    D_inv_sqrt = sp.diags(1.0 / np.sqrt(deg))
    L = sp.diags(deg) - A
    return (D_inv_sqrt @ L @ D_inv_sqrt).toarray()


def detect_degeneracy_groups(eigvals, tol_factor=0.05):
    nonzero = eigvals[eigvals > 1e-6]
    if len(nonzero) == 0: return []
    groups, current = [], [nonzero[0]]
    for i in range(1, len(nonzero)):
        if (nonzero[i] - nonzero[i - 1]) / (nonzero[i - 1] + 1e-12) < tol_factor:
            current.append(nonzero[i])
        else:
            groups.append((float(np.mean(current)), len(current)))
            current = [nonzero[i]]
    groups.append((float(np.mean(current)), len(current)))
    return groups


def main():
    print("=== Binary icosahedral group 2I Cayley graph — exact S^3 discretization ===")
    print(f"φ = (1+√5)/2 = {PHI:.6f}; 1/φ = {INV_PHI:.6f}")
    print()

    # Generate 2I elements
    elements = generate_2i_elements()
    print(f"[1] Generated {len(elements)} elements (expected 120 for 2I)")
    if len(elements) != 120:
        print(f"  WARNING: expected 120, got {len(elements)}")

    # Verify all on S^3 (unit quaternions)
    norms = [np.linalg.norm(e) for e in elements]
    print(f"    Quaternion norms: min={min(norms):.6f}, max={max(norms):.6f} (should be 1.0)")
    print()

    # Generator set: 7 unit-vector quaternions + type-3 golden-ratio element
    # 7 unit-vectors alone generate Q_8 (order 8) which splits 2I into 15 cosets.
    # Adding one type-3 element bridges cosets to fully generate 2I.
    gens_8 = []
    for axis in range(4):
        for sign in [+1, -1]:
            q = [0, 0, 0, 0]
            q[axis] = sign
            gens_8.append(np.array(q))
    gens_8 = [g for g in gens_8 if not np.allclose(g, [1, 0, 0, 0])]
    # Add type-3 generator: (1/2, φ/2, 1/(2φ), 0) — known 2I element of order 10
    type3_gen = np.array([0.5, PHI / 2, INV_PHI / 2, 0.0])
    gens_8.append(type3_gen)
    # Add its inverse so generator set is symmetric (Hermitian Laplacian)
    type3_inv = np.array([0.5, -PHI / 2, -INV_PHI / 2, 0.0])  # conjugate
    gens_8.append(type3_inv)
    # And one more "long" element for safety: (1/2, 1/(2φ), 0, φ/2)
    type3_gen2 = np.array([0.5, INV_PHI / 2, 0.0, PHI / 2])
    gens_8.append(type3_gen2)
    type3_inv2 = np.array([0.5, -INV_PHI / 2, 0.0, -PHI / 2])
    gens_8.append(type3_inv2)
    print(f"[2] Generator set (size {len(gens_8)}): 7 unit-vector + 4 golden-ratio type-3 generators")
    print()

    print("[3] Building Cayley graph...")
    A = build_cayley_graph(elements, gens_8)
    n_edges = int(A.nnz / 2)
    avg_deg = float(A.sum() / len(elements))
    print(f"    {n_edges} undirected edges; average degree {avg_deg:.1f}")
    print()

    print("[4] Computing normalized Laplacian spectrum...")
    L = normalized_laplacian(A)
    eigvals = np.sort(scipy.linalg.eigvalsh(L))
    print(f"    Spectrum range: [{eigvals[0]:.4f}, {eigvals[-1]:.4f}]")
    print()

    # Degeneracy groups
    print("=== Top 25 eigenvalues + degeneracy detection ===")
    for i in range(min(25, len(eigvals))):
        print(f"    [{i:3d}] {eigvals[i]:.5f}")
    print()
    groups = detect_degeneracy_groups(eigvals, tol_factor=0.05)
    print(f"Degeneracy groups (tol 5%):")
    for g_idx, (val, count) in enumerate(groups[:6]):
        l = g_idx + 1
        deg_predicted_s3 = (l + 1) ** 2
        match = "MATCH S^3" if count == deg_predicted_s3 else f"(continuum S^3 l={l}: {deg_predicted_s3})"
        print(f"  l={l}: {count} modes near eigenvalue {val:.4f}  {match}")
    print()

    # Mode-ratio analysis
    print("=== MFO §VII.4.1.1 mode-ratio check ===")
    if len(groups) >= 3:
        ratio_l2 = groups[1][0] / groups[0][0]
        ratio_l3 = groups[2][0] / groups[0][0]
        print(f"  l=2/l=1 ratio: {ratio_l2:.4f}  (continuum S^3: 8/3 = {8/3:.4f}, gap {100*abs(ratio_l2 - 8/3) / (8/3):.1f}%)")
        print(f"  l=3/l=1 ratio: {ratio_l3:.4f}  (continuum S^3: 5.0, gap {100*abs(ratio_l3 - 5) / 5:.1f}%)")
    print()

    # Verdict
    print("=== Verdict ===")
    expected_degs = [4, 9, 16, 25, 36]
    match_count = sum(1 for i, (_, c) in enumerate(groups[:5]) if c == expected_degs[i])
    print(f"  Continuum S^3 degeneracy matched: {match_count}/5")
    if match_count >= 3:
        print(f"  ✓ Cayley(2I, {len(gens_8)} gens) is a clean discrete realization of S^3 spectrum")
    elif match_count >= 1:
        print(f"  Partial match — generator choice may affect degeneracy structure")
    else:
        print(f"  Generator set didn't recover continuum degeneracy at this configuration")

    # Save
    records = [
        {"test": "config", "group": "2I", "order": len(elements),
         "n_generators": len(gens_8), "n_edges": n_edges,
         "avg_degree": float(avg_deg)},
        {"test": "spectrum",
         "all_eigenvalues": [float(e) for e in eigvals]},
        {"test": "degeneracy_groups",
         "groups": [(float(v), int(c)) for v, c in groups]},
        {"test": "mfo_continuum_check",
         "l2_l1_ratio": float(groups[1][0] / groups[0][0]) if len(groups) >= 2 else None,
         "l3_l1_ratio": float(groups[2][0] / groups[0][0]) if len(groups) >= 3 else None,
         "continuum_l2_l1": 8 / 3, "continuum_l3_l1": 5.0,
         "match_count_vs_continuum": int(match_count),
         "expected_degeneracies": expected_degs},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].plot(eigvals, "g-o", markersize=4)
    axes[0].set_xlabel("Eigenvalue index"); axes[0].set_ylabel("Eigenvalue")
    axes[0].set_title(f"Cayley(2I, 7 gens) spectrum — 120 eigenvalues")
    axes[0].grid(alpha=0.3)

    # Histogram showing degeneracy
    axes[1].hist(eigvals, bins=40, alpha=0.7, edgecolor='black')
    # Mark continuum S^3 mode positions (normalized)
    if len(groups) >= 1:
        l1_eigval = groups[0][0]
        for l in range(1, 5):
            cont_pos = l1_eigval * l * (l + 2) / 3  # normalize l=1 to match measured
            axes[1].axvline(cont_pos, color="red", linestyle="--", alpha=0.5,
                             label=f"l={l} continuum" if l == 1 else None)
    axes[1].set_xlabel("Eigenvalue"); axes[1].set_ylabel("Count")
    axes[1].set_title("Eigenvalue histogram — clustering shows degeneracies")
    axes[1].grid(alpha=0.3); axes[1].legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "binary-icosahedral-cayley-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()
