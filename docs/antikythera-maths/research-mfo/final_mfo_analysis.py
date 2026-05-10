import numpy as np
import json

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
sorted_sm = sorted(sm_masses_gev.items(), key=lambda x: x[1])
sm_names = [x[0] for x in sorted_sm]
target_log = np.array([np.log10((x[1]/m_e)**2) for x in sorted_sm])

# Global parameters from best model
L = 5.0
n_fractal = 3
S = 0.297479
R = 1000.0
s1_unit = 1.0 / (R**2)

# Fractal "Anchors" (Level 5, L=5) from inverse refinement
anchors = [
    0.0000,   # electron
    0.4384,   # up
    0.4384,   # down
    1.3557,   # strange
    1.3767,   # muon
    2.0000,   # charm
    2.0000,   # tau
    2.0000,   # bottom
    3.6180    # top
]

# Multiplet grouping
multiplets = {
    'electron': 'charged_lepton',
    'muon': 'charged_lepton',
    'tau': 'charged_lepton',
    'up': 'up_quark',
    'charm': 'up_quark',
    'top': 'up_quark',
    'down': 'down_quark',
    'strange': 'down_quark',
    'bottom': 'down_quark'
}

def run_final_analysis():
    mappings = []
    
    print(f"Final MFO Analysis: L={L}, S={S:.4f}, R={R}")
    print(f"{'Particle':>10s} {'Anchor λ':>10s} {'Best n':>4s} {'Pred Log':>10s} {'Obs Log':>10s} {'Residual':>10s} {'Shift':>10s}")
    
    for i, name in enumerate(sm_names):
        target = target_log[i]
        base_lam = anchors[i]
        
        # Optimize n for this R
        best_n = 0
        min_err = float('inf')
        best_log_pred = 0.0
        
        for n in range(11):
            log_pred = (base_lam + (n**2 * s1_unit)) / S
            err = (log_pred - target)**2
            if err < min_err:
                min_err = err
                best_n = n
                best_log_pred = log_pred
        
        residual = target - best_log_pred
        shift = 10**residual
        
        mappings.append({
            "particle": name,
            "generation": (i // 3) + 1,
            "multiplet": multiplets[name],
            "anchor_eigenvalue": base_lam,
            "s1_n": best_n,
            "predicted_log": best_log_pred,
            "observed_log": target,
            "residual": residual,
            "shift_factor": shift
        })
        
        print(f"{name:10s} {base_lam:10.4f} {best_n:4d} {best_log_pred:10.4f} {target:10.4f} {residual:10.4f} {shift:10.4f}")

    # Aggregate by grouping
    patterns = {
        "by_generation": {},
        "by_multiplet": {}
    }
    
    for m in mappings:
        g = str(m["generation"])
        mul = m["multiplet"]
        
        if g not in patterns["by_generation"]: patterns["by_generation"][g] = []
        patterns["by_generation"][g].append(m["shift_factor"])
        
        if mul not in patterns["by_multiplet"]: patterns["by_multiplet"][mul] = []
        patterns["by_multiplet"][mul].append(m["shift_factor"])

    print("\n--- Systematic Patterns (Mean Shift Factors) ---")
    print("\nBy Generation:")
    for g, shifts in sorted(patterns["by_generation"].items()):
        print(f"  Gen {g}: {np.mean(shifts):.4f} (std: {np.std(shifts):.4f})")
        
    print("\nBy Multiplet:")
    for mul, shifts in sorted(patterns["by_multiplet"].items()):
        print(f"  {mul:15s}: {np.mean(shifts):.4f}")

    final_results = {
        "parameters": {"L": L, "n": n_fractal, "S": S, "R": R},
        "mappings": mappings,
        "patterns": {
            "generation_means": {g: np.mean(v) for g, v in patterns["by_generation"].items()},
            "multiplet_means": {m: np.mean(v) for m, v in patterns["by_multiplet"].items()}
        }
    }

    with open("results-mfo/fractal_sm_mapping.json", "w") as f:
        json.dump(final_results, f, indent=2)

if __name__ == "__main__":
    run_final_analysis()
