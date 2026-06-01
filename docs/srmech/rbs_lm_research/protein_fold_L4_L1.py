"""protein_fold_L4_L1.py — bold-fold arc (MS#22 #822), lenses L4 + L1, on the vendored CC0 hoodoos.

L4 (contact map = Class-L graph): the residue contact graph's Laplacian SPECTRUM is the
    fold's srmech-native structural fingerprint (F172). Fiedler lambda_2 = rigidity/hinge.
L1 (fold = codeword): the native fold is the conservation-bounded codeword; perturbing a
    LOAD-BEARING (high-degree) residue should raise a bigger SYNDROME (spectral shift) than
    perturbing a peripheral (low-degree) one -- the load-bearing residue is the parity-check bit.

SCOPE: framework-reading of folding STRUCTURE only. Inputs = attested CC0 PDB Calpha
coordinates (read, not modeled); output = the contact-graph Laplacian SPECTRUM (algebra/
spectral). NO 3D-coordinate prediction, NO MD, NO design, NO clinical. CAD-ban respected
(we read the graph spectrum, not fabricate geometry). No-lineage. Class-K clean (Euclidean
norms for distances; spectral differences via L2; no abs() sign-folding).

srmech v0.7.0rc2 native: dense_laplacian, jacobi_eigvals (Class L).
"""
import os
import numpy as np
from srmech.amsc import laplacian

HOODOOS = {
    "ubiquitin 1UBQ":  "docs/srmech/hoodoos/ubiquitin-1ubq.pdb",
    "villin HP35 2F4K": "docs/srmech/hoodoos/villin-hp35-2f4k.pdb",
    "knotted MJ0366 2EFV": "docs/srmech/hoodoos/mj0366-knotted-2efv.pdb",
}
ROOT = "/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c"
CUTOFF, SEQSEP = 8.0, 0   # standard Cα Gaussian-network: ALL pairs within cutoff (backbone ~3.8Å included -> connected graph)


def parse_ca(path):
    """Calpha coords of the chain with the most CA atoms (single-chain folds)."""
    chains = {}
    seen = {}
    with open(path) as fh:
        for ln in fh:
            if not ln.startswith("ATOM"):
                continue
            if ln[12:16].strip() != "CA":
                continue
            if ln[16] not in (" ", "A"):          # altloc: blank or A only
                continue
            ch, res = ln[21], ln[22:26]
            key = (ch, res)
            if key in seen:
                continue
            seen[key] = True
            xyz = (float(ln[30:38]), float(ln[38:46]), float(ln[46:54]))
            chains.setdefault(ch, []).append(xyz)
    best = max(chains, key=lambda c: len(chains[c]))
    return np.array(chains[best], float)


def contacts(coords, cutoff=CUTOFF, sep=SEQSEP):
    n = len(coords)
    edges = []
    for i in range(n):
        for j in range(i + sep + 1, n):
            if np.linalg.norm(coords[i] - coords[j]) < cutoff:   # Euclidean, not a sign-op
                edges.append((i, j))
    return edges


def spectrum(n, edges):
    L = np.array(laplacian.dense_laplacian(n, edges), float)
    ev = np.sort(np.array(laplacian.jacobi_eigvals(L), float))
    return ev


def main():
    print("=== L4 — contact-graph Laplacian spectra (the fold's srmech-native fingerprint) ===")
    cache = {}
    print(f"  {'fold':>22} | {'res':>4} {'contacts':>8} {'<deg>':>5} | {'lambda2 (Fiedler)':>17} {'lambda_max':>10} {'comps':>5}")
    for name, rel in HOODOOS.items():
        coords = parse_ca(os.path.join(ROOT, rel))
        n = len(coords)
        edges = contacts(coords)
        ev = spectrum(n, edges)
        cache[name] = (coords, edges, ev)
        lam2 = ev[1] if n > 1 else 0.0
        comps = int(np.sum(ev < 1e-9))
        print(f"  {name:>22} | {n:>4} {len(edges):>8} {2*len(edges)/n:>5.2f} | {lam2:>17.4f} {ev[-1]:>10.3f} {comps:>5}")
    print("  reading: lambda2 (algebraic connectivity) = rigidity/hinge; helix-bundle (villin)")
    print("  vs mixed-alpha/beta (ubiquitin) vs knotted (MJ0366) separate by spectral profile.\n")

    print("=== L1 — fold = codeword: load-bearing vs peripheral residue knockout -> syndrome ===")
    name = "ubiquitin 1UBQ"
    coords, edges, ev_native = cache[name]
    n = len(coords)
    deg = np.zeros(n, int)
    for i, j in edges:
        deg[i] += 1; deg[j] += 1
    r_hi = int(np.argmax(deg))                       # load-bearing (most contacts = parity-check bit)
    r_lo = int(np.argmin(np.where(deg > 0, deg, 999)))  # peripheral (fewest, but >0)

    def syndrome(r):
        kept = [(i, j) for (i, j) in edges if i != r and j != r]   # knock out residue r's contacts
        ev_p = spectrum(n, kept)
        return float(np.linalg.norm(ev_p - ev_native))             # L2 spectral shift = the syndrome

    s_hi, s_lo = syndrome(r_hi), syndrome(r_lo)
    print(f"  {name}: native fold = the codeword (connected GNM; lambda2={ev_native[1]:.4f} = algebraic connectivity)")
    print(f"  knock out LOAD-BEARING residue r={r_hi} (degree {deg[r_hi]}): syndrome (spectral L2 shift) = {s_hi:.4f}")
    print(f"  knock out PERIPHERAL   residue r={r_lo} (degree {deg[r_lo]}): syndrome (spectral L2 shift) = {s_lo:.4f}")
    print(f"  prediction (lens L1): load-bearing syndrome > peripheral -> {s_hi:.4f} > {s_lo:.4f} : {s_hi > s_lo}")
    print("  reading: the load-bearing (high-degree) residue IS a parity-check bit -- its loss")
    print("  produces a larger detected error (the fold leaves the codeword more); the peripheral")
    print("  residue is a redundant register slot. The native fold is the zero-syndrome codeword.")


if __name__ == "__main__":
    main()
