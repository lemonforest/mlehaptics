import numpy as np
import json
from pathlib import Path
import heapq

# Standard Model target masses in GeV
sm_masses_gev = {
    'electron': 0.000511,
    'up': 0.0022,
    'down': 0.0047,
    'strange': 0.095,
    'muon': 0.1057,
    'charm': 1.275,
    'tau': 1.777,
    'bottom': 4.18,
    'top': 173.0,
}

# Target: ratios of mass squared relative to electron, sorted
m_e = sm_masses_gev['electron']
sm_mass_sq_ratios = sorted([(v/m_e)**2 for v in sm_masses_gev.values()])
target_log = np.log10(sm_mass_sq_ratios)

def generalized_decimation(n, L, max_level=5):
    """
    Generalized spectral decimation for a fractal with n copies
    and decimation factor L.
    """
    def R_inverse(w):
        disc = L*L - 4*w
        if disc < 0:
            return []
        sd = np.sqrt(disc)
        return [(L - sd)/2.0, (L + sd)/2.0]

    memo = {}
    def get_evals_at_level(m):
        if m == 0:
            return {0.0, float(L)}
        if m in memo:
            return memo[m]
        prev = get_evals_at_level(m - 1)
        new_evals = set()
        for w in prev:
            for z in R_inverse(w):
                if 0 <= z <= L + 1:
                    new_evals.add(round(z, 12))
        new_evals.add(2.0)
        new_evals.add(float(n + 2))
        memo[m] = new_evals
        return new_evals

    continuous_evals = set()
    for m in range(max_level + 1):
        for e in get_evals_at_level(m):
            if e > 1e-10:
                continuous_evals.add(round((L**m) * e, 6))
    return sorted(list(continuous_evals))

# Precompute fractal eigenvalues for each (n, L)
print("Precomputing fractal spectra...")
fractal_cache = {}
for n in range(3, 9):
    for L in range(4, 21):
        # We only need the smallest few to find the overall smallest 9 total
        evals = generalized_decimation(n, L, max_level=5)
        fractal_cache[(n, L)] = evals[:15]  # Keep top 15

# CP2 and S1 constants
cp2_base = [0, 12, 32, 60, 96, 140]
s1_n = [0, 1, 2, 3, 4]

# R sweep values: log steps from 0.1 to 10
r_values = np.logspace(-1, 1, 9)

candidates = []

print("Starting anisotropic product sweep...")
# To reduce redundant permutations (L1, L2, L3), we enforce L1 <= L2 <= L3
n_total = 6 * (17 * 18 * 19 // 6) * 9  # Approx count
count = 0

for n in range(3, 9):
    for L1 in range(4, 21):
        E1 = fractal_cache[(n, L1)]
        for L2 in range(L1, 21):
            E2 = fractal_cache[(n, L2)]
            for L3 in range(L2, 21):
                E3 = fractal_cache[(n, L3)]
                
                # Combine fractal axes
                fractal_sums = set()
                for e1 in E1:
                    for e2 in E2:
                        for e3 in E3:
                            fractal_sums.add(e1 + e2 + e3)
                # Add 0 to fractal sums to allow zero contributions from fractal axes
                # (Technically each axis has a 0 mode, but generalized_decimation returns non-zero)
                # In a product manifold, the 0 mode is always present.
                # Let's add it explicitly for the combined set.
                fractal_sums.add(0.0)
                sorted_fractal = sorted(list(fractal_sums))[:30]

                for R in r_values:
                    s1_evals = [(n_s**2) / (R**2) for n_s in s1_n]
                    
                    # Total combinations
                    combined = set()
                    for f in sorted_fractal:
                        for cp in cp2_base:
                            for s1 in s1_evals:
                                val = f + cp + s1
                                if val > 1e-10:
                                    combined.add(round(val, 6))
                    
                    if len(combined) < 9:
                        continue
                    
                    sorted_combined = sorted(list(combined))
                    top_9 = np.array(sorted_combined[:9])
                    normalized_9 = top_9 / top_9[0]
                    log_9 = np.log10(normalized_9)
                    
                    error = np.sum((log_9 - target_log)**2)
                    
                    candidates.append({
                        "n": n,
                        "L1": L1, "L2": L2, "L3": L3,
                        "R": float(R),
                        "error": float(error),
                        "ratios": normalized_9.tolist()
                    })
                    
                    count += 1
                    if count % 5000 == 0:
                        print(f"Processed {count} configurations...")

# Sort and save
candidates.sort(key=lambda x: x["error"])
top_100 = candidates[:100]

results_path = Path("results-mfo/anisotropic_product_sweep.json")
with open(results_path, "w") as f:
    json.dump(top_100, f, indent=2)

print("\nSweep complete.")
print(f"Top 10 candidates (sorted by log10 squared error):")
print(f"{'n':>2s} {'L1':>3s} {'L2':>3s} {'L3':>3s} {'R':>6s} {'Error':>10s}")
for c in candidates[:10]:
    print(f"{c['n']:2d} {c['L1']:3d} {c['L2']:3d} {c['L3']:3d} {c['R']:6.3f} {c['error']:10.4f}")

print(f"\nResults saved to {results_path}")
