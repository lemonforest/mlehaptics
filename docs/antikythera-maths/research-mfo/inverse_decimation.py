import numpy as np
import json
from scipy.optimize import minimize_scalar

# Standard Model masses in GeV
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

m_e = sm_masses_gev['electron']
# Sorted masses and names
sorted_sm = sorted(sm_masses_gev.items(), key=lambda x: x[1])
sm_names = [x[0] for x in sorted_sm]
sm_ratios = np.array([(x[1]/m_e)**2 for x in sorted_sm])
sm_log_ratios = np.log10(sm_ratios)

# Generations indices
gen_indices = [
    [0, 1, 2], # G1: e, u, d
    [3, 4, 5], # G2: s, mu, c
    [6, 7, 8]  # G3: tau, b, t
]

def get_sg_spectrum(L=5.0, max_level=5):
    """Generate the L=5 decimation eigenvalues at Level 5."""
    def R_inverse(w):
        disc = L*L - 4*w
        if disc < 0: return []
        sd = np.sqrt(disc)
        return [(L - sd)/2.0, (L + sd)/2.0]

    current_evals = {0.0, L}
    all_evals = set()
    for m in range(max_level + 1):
        for e in current_evals:
            all_evals.add(round(e, 10))
        if m < max_level:
            next_evals = set()
            for w in current_evals:
                for z in R_inverse(w):
                    if 0 <= z <= L + 1:
                        next_evals.add(z)
            next_evals.add(2.0)
            next_evals.add(5.0) # n+2 for L=5 is 5? Wait, born is {2, 5} for SG.
            current_evals = next_evals
    return sorted(list(all_evals))

def compute_error(S, targets, spectrum):
    total_err = 0.0
    mapped_vals = []
    for t in targets:
        scaled = S * t
        # Find closest in spectrum
        closest = min(spectrum, key=lambda x: abs(x - scaled))
        total_err += (scaled - closest)**2
        mapped_vals.append(closest)
    return total_err, mapped_vals

def run_refinement():
    L = 5.0
    spectrum = get_sg_spectrum(L, 5)
    
    # 1. Global Scale Factor Optimization
    res_global = minimize_scalar(lambda s: compute_error(s, sm_log_ratios, spectrum)[0], 
                                 bounds=(0.1, 2.0), method='bounded')
    s_global = res_global.x
    err_global, mapped_global = compute_error(s_global, sm_log_ratios, spectrum)
    
    # 2. Per-Generation Scale Factor Optimization
    s_gens = []
    err_total_gen = 0.0
    mapped_gens = [None] * 9
    
    for indices in gen_indices:
        gen_targets = sm_log_ratios[indices]
        res_gen = minimize_scalar(lambda s: compute_error(s, gen_targets, spectrum)[0],
                                  bounds=(0.1, 2.0), method='bounded')
        s_gen = res_gen.x
        s_gens.append(s_gen)
        err_gen, mapped_gen_vals = compute_error(s_gen, gen_targets, spectrum)
        err_total_gen += err_gen
        for i, idx in enumerate(indices):
            mapped_gens[idx] = mapped_gen_vals[i]

    # Prepare results
    results = {
        "global_optimization": {
            "scale_factor": s_global,
            "total_error": err_global,
            "mappings": [
                {
                    "particle": sm_names[i],
                    "target_log": sm_log_ratios[i],
                    "scaled_val": s_global * sm_log_ratios[i],
                    "mapped_eigenvalue": mapped_global[i]
                } for i in range(9)
            ]
        },
        "per_generation_optimization": {
            "scale_factors": s_gens,
            "total_error": err_total_gen,
            "mappings": [
                {
                    "particle": sm_names[i],
                    "generation": (i // 3) + 1,
                    "scale_factor": s_gens[i // 3],
                    "scaled_val": s_gens[i // 3] * sm_log_ratios[i],
                    "mapped_eigenvalue": mapped_gens[i]
                } for i in range(9)
            ]
        }
    }

    with open("inverse_refined.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Refinement Complete for L=5.")
    print(f"\nGlobal Scale Factor: {s_global:.6f}")
    print(f"Global Total Error: {err_global:.6f}")
    
    print(f"\nPer-Generation Scale Factors: {[f'{s:.6f}' for s in s_gens]}")
    print(f"Per-Generation Total Error: {err_total_gen:.6f}")
    
    print(f"\nTop Mappings (Global):")
    print(f"{'Particle':>10s} {'Target Log':>12s} {'Scaled':>10s} {'Eigenvalue':>12s}")
    for m in results["global_optimization"]["mappings"]:
        print(f"{m['particle']:10s} {m['target_log']:12.4f} {m['scaled_val']:10.4f} {m['mapped_eigenvalue']:12.4f}")

if __name__ == "__main__":
    run_refinement()
