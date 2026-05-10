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
sorted_sm = sorted(sm_masses_gev.items(), key=lambda x: x[1])
sm_names = [x[0] for x in sorted_sm]
target_log = np.array([np.log10((x[1]/m_e)**2) for x in sorted_sm])

# Per-generation log-scale factors (S) from the refined inverse test
s_gens = [0.702896, 0.761239, 0.468710]

# Fractal eigenvalues (L=5, Level 5)
base_fractal_evals = [
    0.0000,   # electron (G1)
    0.4384,   # up (G1)
    0.4384,   # down (G1)
    1.3557,   # strange (G2)
    1.3767,   # muon (G2)
    2.0000,   # charm (G2)
    2.0000,   # tau (G3)
    2.0000,   # bottom (G3)
    3.6180    # top (G3)
]

def run_per_gen_radius_sweep():
    # R sweep range: 10 to 10,000 in log steps
    r_range = 10.0 ** np.arange(1.0, 4.5, 0.5)
    
    best_total_error = float('inf')
    best_config = {}

    print(f"Starting Per-Generation Radius Sweep...")
    
    for R12 in r_range:
        for R3 in r_range:
            current_total_error = 0.0
            assignments = []
            
            for i in range(9):
                target = target_log[i]
                base_lam = base_fractal_evals[i]
                gen_idx = i // 3
                S = s_gens[gen_idx]
                R = R3 if gen_idx == 2 else R12
                s1_unit = 1.0 / (R**2)
                
                best_n = 0
                min_particle_err = float('inf')
                best_log_pred = 0.0
                
                for n in range(11): # 0 to 10
                    log_pred = (base_lam + (n**2 * s1_unit)) / S
                    err = (log_pred - target)**2
                    if err < min_particle_err:
                        min_particle_err = err
                        best_n = n
                        best_log_pred = log_pred
                
                current_total_error += min_particle_err
                assignments.append({
                    "particle": sm_names[i],
                    "n": best_n,
                    "error": min_particle_err,
                    "log_pred": best_log_pred
                })
            
            if current_total_error < best_total_error:
                best_total_error = current_total_error
                best_config = {
                    "R12": float(R12),
                    "R3": float(R3),
                    "total_error": float(current_total_error),
                    "assignments": assignments
                }

    with open("results-mfo/s1_radius_per_gen.json", "w") as f:
        json.dump(best_config, f, indent=2)

    print(f"\nBest Total Error: {best_config['total_error']:.6f}")
    print(f"Optimal Radii: R12={best_config['R12']:.1f}, R3={best_config['R3']:.1f}")
    print(f"\n{'Particle':>10s} {'Target Log':>12s} {'Best n':>6s} {'Final Log':>12s} {'Error':>10s}")
    for i, a in enumerate(best_config['assignments']):
        print(f"{a['particle']:10s} {target_log[i]:12.4f} {a['n']:6d} {a['log_pred']:12.4f} {a['error']:10.4f}")

if __name__ == "__main__":
    run_per_gen_radius_sweep()
