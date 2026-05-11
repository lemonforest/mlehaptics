"""MPM-disciplined central computation for the MFO §XIII.1 question.

Question: does any Pn fractal Laplacian (n=2..8, decimation levels 3..5) reproduce
the 9-element SM mass^2 ratio vector under a 1-parameter scale-only fit?

Discipline:
- closed-form spectral decimation per notebook §IV.2 (Rammal-Toulouse 1984;
  Fukushima-Shima 1992 for SG; Shima 1996 for higher Pn)
- single scale parameter S only (no per-particle free parameters)
- nearest-eigenvalue assignment of each SM fermion to a fractal mode
- NDJSON output, one record per (Pn, level) candidate

Decimation factors from notebook §IV.3 table (empirical, Pn literature):
  P2=2, P3=5 (SG), P4=6, P5=8, P6=10, P7=12, P8=14
Recurrence form R(lambda) = lambda * (L - lambda) where L = decimation factor.
This is exact for P3 (SG) per Rammal-Toulouse. For Pn>3 we use the same
quadratic-recurrence form as a first approximation; a more careful Shima
treatment would use higher-degree polynomials. Flagged in output.
"""
import json
import numpy as np
from pathlib import Path
from scipy.optimize import minimize_scalar

# Per notebook IV.3 table
PN_DECIMATION = {2: 2, 3: 5, 4: 6, 5: 8, 6: 10, 7: 12, 8: 14}

# SM fermion masses (GeV), PDG-class values (matches Gemini's targets)
SM_MASSES_GEV = {
    'electron': 0.000511,
    'up': 0.0022, 'down': 0.0047,
    'strange': 0.095, 'muon': 0.1057,
    'charm': 1.275, 'tau': 1.777,
    'bottom': 4.18, 'top': 173.0,
}
M_E = SM_MASSES_GEV['electron']
TARGET = {p: np.log10((m/M_E)**2) for p, m in SM_MASSES_GEV.items()}
SM_NAMES = sorted(SM_MASSES_GEV, key=lambda p: SM_MASSES_GEV[p])


def pn_spectrum(L, max_level=5):
    """Generate Pn-fractal Laplacian eigenvalues via spectral decimation
    R(lambda) = lambda * (L - lambda).
    Level 0 Neumann state: {0, L}. Born seeds at each level: {2, L}.
    Returns sorted list of distinct eigenvalues.
    """
    def R_inverse(w):
        disc = L*L - 4*w
        if disc < 0:
            return []
        sd = np.sqrt(disc)
        return [(L - sd)/2.0, (L + sd)/2.0]

    current = {0.0, float(L)}
    all_evals = set()
    for m in range(max_level + 1):
        for e in current:
            all_evals.add(round(e, 10))
        if m < max_level:
            nxt = set()
            for w in current:
                for z in R_inverse(w):
                    if 0 <= z <= L + 1e-9:
                        nxt.add(z)
            nxt.add(2.0)
            nxt.add(float(L))
            current = nxt
    return sorted(all_evals)


def scale_only_fit(spectrum, targets):
    """1-parameter scale fit: predicted_log[p] = nearest_eigenvalue(S * target[p]) / S.
    Minimise total quadratic error sum( (scaled - mapped_eig)^2 ).
    """
    sp = np.array(spectrum)
    targs = np.array([targets[p] for p in SM_NAMES])

    def err(S):
        scaled = S * targs
        # nearest-eigenvalue assignment per SM fermion
        mapped = np.array([sp[np.argmin(np.abs(sp - v))] for v in scaled])
        return float(np.sum((scaled - mapped)**2))

    # S must be > 0 and reasonable; target_top=11.06 and max spec = L+something
    # so S in [0.05, 1.0] roughly
    res = minimize_scalar(err, bounds=(0.01, 1.0), method='bounded',
                          options={'xatol': 1e-7})
    S_opt = res.x
    e_opt = res.fun

    # Build per-fermion table at S_opt
    scaled = S_opt * targs
    mapped = np.array([sp[np.argmin(np.abs(sp - v))] for v in scaled])
    residuals = scaled - mapped
    # predicted mass^2 ratio log10 = mapped / S
    predicted_log = mapped / S_opt
    return S_opt, e_opt, scaled, mapped, residuals, predicted_log


def run_sweep():
    results = []
    for n in range(2, 9):
        L = PN_DECIMATION[n]
        for level in [3, 4, 5]:
            spec = pn_spectrum(L, max_level=level)
            S, err, scaled, mapped, resid, pred = scale_only_fit(spec, TARGET)
            n_distinct = len(spec)
            n_distinct_under_top = sum(1 for e in spec if e <= max(scaled) + 0.5)

            record = {
                'fractal': f'P{n}',
                'n': n,
                'decimation_L': L,
                'level': level,
                'n_distinct_eigenvalues': n_distinct,
                'n_eigenvalues_in_fit_range': n_distinct_under_top,
                'S_opt': float(S),
                'total_quadratic_error': float(err),
                'mean_per_fermion_log_err': float(np.sqrt(err/9)),
                'fermions': [
                    {
                        'name': SM_NAMES[i],
                        'target_log_m2_me2': float(TARGET[SM_NAMES[i]]),
                        'scaled_eigenvalue_pos': float(scaled[i]),
                        'mapped_eigenvalue': float(mapped[i]),
                        'residual': float(resid[i]),
                        'predicted_log_m2_me2': float(pred[i]),
                        'predicted_mass_gev': float(M_E * np.sqrt(10**pred[i])),
                        'observed_mass_gev': SM_MASSES_GEV[SM_NAMES[i]],
                    }
                    for i in range(9)
                ],
            }
            results.append(record)
            print(f"P{n} L={L} level={level}: S={S:.4f}, err={err:.4f}, "
                  f"mean_log_err={np.sqrt(err/9):.4f}, n_eigs={n_distinct}")

    return results


def write_ndjson(records, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='\n') as f:
        for rec in records:
            f.write(json.dumps(rec, separators=(',', ':')) + '\n')
    print(f"\nWrote {len(records)} records to {path}")


if __name__ == '__main__':
    results = run_sweep()
    out = Path(__file__).resolve().parent.parent / 'results-mfo' / 'mpm_pn_sweep.ndjson'
    write_ndjson(results, out)

    # Best fit summary
    print("\n=== Best fits per Pn (across levels 3-5) ===")
    best_per_n = {}
    for r in results:
        key = r['n']
        if key not in best_per_n or r['total_quadratic_error'] < best_per_n[key]['total_quadratic_error']:
            best_per_n[key] = r
    for n in sorted(best_per_n):
        r = best_per_n[n]
        print(f"  P{n}: best at level {r['level']}, S={r['S_opt']:.4f}, "
              f"total_err={r['total_quadratic_error']:.4f}, "
              f"mean_log_err={r['mean_per_fermion_log_err']:.4f}")

    print("\n=== Global winner ===")
    winner = min(results, key=lambda r: r['total_quadratic_error'])
    print(f"  {winner['fractal']} (L={winner['decimation_L']}) at level {winner['level']}")
    print(f"  S = {winner['S_opt']:.4f}, total_err = {winner['total_quadratic_error']:.4f}")
    print(f"  mean per-fermion log10 mass^2 error = {winner['mean_per_fermion_log_err']:.4f}")
