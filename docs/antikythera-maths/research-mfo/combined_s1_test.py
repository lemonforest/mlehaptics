import numpy as np
import json

# Standard Model target mass-squared ratios relative to electron
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
m_e = 0.000511
sm_ratios = sorted([(v/m_e)**2 for v in sm_masses_gev.values()])
target_log = np.log10(sm_ratios)

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
            next_evals.add(5.0)
            current_evals = next_evals
    return sorted(list(all_evals))

def run_combined_test():
    L = 5.0
    R = 1000.0
    s1_base = 1.0 / (R**2)
    
    fractal = get_sg_spectrum(L, 5)
    
    # Combined spectrum: Fractal + S1 (k^2/R^2)
    # We take enough S1 modes to fill the gap
    combined = set()
    for f in fractal:
        for k in range(500): # k=0 to 499
            val = f + (k**2 * s1_base)
            if val > 1e-12:
                combined.add(round(val, 10))
    
    sorted_combined = sorted(list(combined))
    top_9 = np.array(sorted_combined[:9])
    
    normalized_9 = top_9 / top_9[0]
    log_9 = np.log10(normalized_9)
    
    error = np.sum((log_9 - target_log)**2)
    
    results = {
        "parameters": {"L": L, "n": 3, "R": R, "S1_base": s1_base},
        "error": float(error),
        "eigenvalues": top_9.tolist(),
        "ratios": normalized_9.tolist(),
        "target_ratios": sm_ratios
    }
    
    print(f"Combined Spectral Test (Fractal L=5 x S1 R=1000)")
    print(f"Total Log10 Squared Error: {error:.6f}")
    print(f"\n{'Particle':>10s} {'Target Ratio':>15s} {'Computed Ratio':>15s} {'Error (log)':>10s}")
    
    particles = sorted(sm_masses_gev.keys(), key=lambda x: sm_masses_gev[x])
    for i in range(9):
        p_error = (log_9[i] - target_log[i])**2
        print(f"{particles[i]:10s} {sm_ratios[i]:15.4f} {normalized_9[i]:15.4f} {p_error:10.4f}")

    with open("results-mfo/combined_s1_test.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_combined_test()
