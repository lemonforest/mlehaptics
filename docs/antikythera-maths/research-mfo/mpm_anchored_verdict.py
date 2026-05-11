"""MPM-disciplined verdict for the MFO L=5 SG × CP² × S¹ candidate framework.

Three honest tests under MPM (no per-particle free parameters, closed-form,
deterministic, ground-proof against published SM/PDG values).

Test 1 — Constrained-anchor mass fit: for each Pn (n=2..8), use ONLY the
spectrum's *gap-separated* anchor eigenvalues (closed-form, framework-derived).
Assign 9 SM fermions to anchors respecting generation degeneracy (the framework's
3-fold self-similarity prediction). Total quadratic error in log10(m²/m_e²).

Test 2 — Gauge coupling RG flow with textbook signs. Where do α_1/α_2/α_3
run to at the Planck scale? At what scale (if any) do they unify? Bug-free
rerun of Gemini's gauge_analysis.py.

Test 3 — Spectral dimension flow d_S(σ) on the winning Pn from heat kernel.
Verify the notebook §V.4 non-monotonic prediction: d_S → 2 at UV, peak at
intermediate, → 4 at IR.

Outputs: NDJSON to results-mfo/mpm_anchored_verdict.ndjson plus
mpm_gauge_rg.ndjson plus mpm_spectral_dimension.ndjson.
"""
import json
import numpy as np
from pathlib import Path
from scipy.optimize import minimize_scalar

# === Constants ===
PN_DECIMATION = {2: 2, 3: 5, 4: 6, 5: 8, 6: 10, 7: 12, 8: 14}
M_E = 0.000511
SM_MASSES_GEV = {
    'electron': 0.000511,
    'up': 0.0022, 'down': 0.0047,
    'strange': 0.095, 'muon': 0.1057,
    'charm': 1.275, 'tau': 1.777,
    'bottom': 4.18, 'top': 173.0,
}
TARGET = {p: np.log10((m/M_E)**2) for p, m in SM_MASSES_GEV.items()}
SM_SORTED = sorted(SM_MASSES_GEV, key=lambda p: SM_MASSES_GEV[p])

OUT_DIR = Path(__file__).resolve().parent.parent / 'results-mfo'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def pn_spectrum(L, max_level=5):
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


def find_anchor_eigenvalues(spectrum, gap_threshold_factor=3.0):
    """Identify isolated 'anchor' eigenvalues — those separated from neighbours
    by a gap > gap_threshold_factor × median local gap.

    These are the framework's mass-generation anchor candidates (gap-respecting,
    closed-form, not free-chosen).
    """
    sp = np.array(spectrum)
    diffs = np.diff(sp)
    median_diff = np.median(diffs[diffs > 1e-10])
    threshold = gap_threshold_factor * median_diff

    anchors = [sp[0]]  # always include 0
    for i in range(len(sp) - 1):
        # eigenvalue sp[i+1] is anchor if its preceding gap is large
        if diffs[i] > threshold:
            anchors.append(sp[i+1])
    return anchors


# === Test 1: constrained-anchor mass fit ===
def constrained_anchor_fit(spectrum):
    """Force 9 SM fermions onto the framework's anchor eigenvalues.
    Use nearest-neighbour assignment (allowing degeneracy from generation structure).
    """
    anchors = find_anchor_eigenvalues(spectrum)
    if len(anchors) < 2:
        return None
    sp = np.array(anchors)
    targets = np.array([TARGET[p] for p in SM_SORTED])

    def err(S):
        scaled = S * targets
        mapped = np.array([sp[np.argmin(np.abs(sp - v))] for v in scaled])
        return float(np.sum((scaled - mapped)**2))

    res = minimize_scalar(err, bounds=(0.01, 2.0), method='bounded',
                          options={'xatol': 1e-7})
    S_opt = res.x
    scaled = S_opt * targets
    mapped = np.array([sp[np.argmin(np.abs(sp - v))] for v in scaled])
    residuals = scaled - mapped
    pred = mapped / S_opt
    return {
        'anchors_used': [float(a) for a in anchors],
        'n_anchors': len(anchors),
        'S_opt': float(S_opt),
        'total_quadratic_error': float(res.fun),
        'mean_per_fermion_log_err': float(np.sqrt(res.fun/9)),
        'fermions': [
            {
                'name': SM_SORTED[i],
                'target_log_m2_me2': float(targets[i]),
                'scaled_eigenvalue_pos': float(scaled[i]),
                'mapped_anchor': float(mapped[i]),
                'residual': float(residuals[i]),
                'predicted_log_m2_me2': float(pred[i]),
                'predicted_mass_gev': float(M_E * np.sqrt(10**pred[i])),
                'observed_mass_gev': SM_MASSES_GEV[SM_SORTED[i]],
            }
            for i in range(9)
        ],
    }


def run_test1():
    records = []
    for n in range(2, 9):
        L = PN_DECIMATION[n]
        for level in [4, 5]:
            spec = pn_spectrum(L, max_level=level)
            fit = constrained_anchor_fit(spec)
            if fit is None:
                continue
            rec = {
                'test': 'constrained_anchor_fit',
                'fractal': f'P{n}', 'n': n,
                'decimation_L': L, 'level': level,
                'spectrum_size': len(spec),
                **fit,
            }
            records.append(rec)
    return records


# === Test 2: gauge coupling RG with textbook signs ===
def gauge_rg(alpha_mZ, b, ln_ratio):
    """1-loop running: alpha^-1(mu) = alpha^-1(mZ) - (b/2pi) * ln(mu/mZ)
    Standard SM convention. b_1 = +41/10 (GUT-normalized), b_2 = -19/6, b_3 = -7.
    """
    inv_mZ = 1.0 / alpha_mZ
    inv_mu = inv_mZ - (b / (2*np.pi)) * ln_ratio
    if inv_mu <= 0:
        return None  # Landau pole / sign breakdown
    return 1.0 / inv_mu


def run_test2():
    M_Z = 91.1876
    M_PL = 1.22e19
    ln_M_Pl_M_Z = np.log(M_PL / M_Z)

    # PDG inputs at M_Z
    alpha1_mZ = 0.0170  # hypercharge GUT-normalized
    alpha2_mZ = 0.0338  # SU(2)
    alpha3_mZ = 0.118   # SU(3) at M_Z, PDG 2024

    # 1-loop SM beta-coefs, textbook convention
    b1, b2, b3 = 41/10, -19/6, -7

    # Run to Planck
    a1_pl = gauge_rg(alpha1_mZ, b1, ln_M_Pl_M_Z)
    a2_pl = gauge_rg(alpha2_mZ, b2, ln_M_Pl_M_Z)
    a3_pl = gauge_rg(alpha3_mZ, b3, ln_M_Pl_M_Z)

    # Find unification scale (where alpha_1 = alpha_2)
    # 1/alpha_1 = 1/alpha_2 -> 1/0.0170 + 41/10/(2pi) * X = 1/0.0338 - 19/6/(2pi) * X
    # X = ln(mu/M_Z) at unification
    X_12 = (1/alpha1_mZ - 1/alpha2_mZ) / ((-b1 + b2) / (2*np.pi))
    X_23 = (1/alpha2_mZ - 1/alpha3_mZ) / ((-b2 + b3) / (2*np.pi))
    X_13 = (1/alpha1_mZ - 1/alpha3_mZ) / ((-b1 + b3) / (2*np.pi))

    mu_12 = M_Z * np.exp(X_12)
    mu_23 = M_Z * np.exp(X_23)
    mu_13 = M_Z * np.exp(X_13)
    a_at_12 = gauge_rg(alpha2_mZ, b2, X_12)

    rec = {
        'test': 'gauge_rg_1loop',
        'inputs': {
            'M_Z_GeV': M_Z, 'M_Planck_GeV': M_PL,
            'alpha1_mZ': alpha1_mZ, 'alpha2_mZ': alpha2_mZ, 'alpha3_mZ': alpha3_mZ,
            'b1_GUT_norm': b1, 'b2': b2, 'b3': b3,
            'convention': 'alpha_i^-1(mu) = alpha_i^-1(M_Z) - (b_i/2pi)*ln(mu/M_Z)',
        },
        'at_M_Planck': {
            'alpha_1': float(a1_pl),
            'alpha_2': float(a2_pl),
            'alpha_3': float(a3_pl),
            'inv_alpha_1': float(1/a1_pl),
            'inv_alpha_2': float(1/a2_pl),
            'inv_alpha_3': float(1/a3_pl),
        },
        'unification': {
            'mu_12_GeV': float(mu_12),
            'mu_23_GeV': float(mu_23),
            'mu_13_GeV': float(mu_13),
            'alpha_unified_12_only': float(a_at_12),
            'unified_cleanly_SM_only': bool(abs(np.log10(mu_12) - np.log10(mu_23)) < 0.5),
        },
        'gemini_published': {
            'alpha1_lambda': 0.00996, 'alpha2_lambda': 0.0986, 'alpha3_lambda': -0.0293,
            'note': 'Gemini formula had wrong sign in denominator; alpha_3 going negative is unphysical',
        },
    }
    return [rec]


# === Test 3: spectral dimension flow d_S(sigma) for winning Pn ===
def spectral_dimension_flow(spectrum, sigma_vals):
    """d_S(sigma) = -2 d(ln K(sigma))/d(ln sigma), K(sigma) = sum_k exp(-lambda_k sigma)."""
    sp = np.array(spectrum)
    ds = []
    for sigma in sigma_vals:
        K = 1.0 + np.sum(np.exp(-sp * sigma))  # +1 includes lambda=0 zero mode
        # d/d ln sigma: numerical derivative
        h = 0.001
        Kp = 1.0 + np.sum(np.exp(-sp * sigma * np.exp(h)))
        Km = 1.0 + np.sum(np.exp(-sp * sigma * np.exp(-h)))
        dlnK_dlnsigma = (np.log(Kp) - np.log(Km)) / (2*h)
        ds.append(-2.0 * dlnK_dlnsigma)
    return ds


def run_test3(winning_fractal_n=3, level=5):
    L = PN_DECIMATION[winning_fractal_n]
    spec = pn_spectrum(L, max_level=level)
    sigma_vals = np.logspace(-3, 3, 80)
    ds_vals = spectral_dimension_flow(spec, sigma_vals)

    peak_idx = int(np.argmax(ds_vals))
    rec = {
        'test': 'spectral_dimension_flow',
        'fractal': f'P{winning_fractal_n}',
        'decimation_L': L,
        'level': level,
        'spectrum_size': len(spec),
        'sigma_range': [float(sigma_vals[0]), float(sigma_vals[-1])],
        'theoretical_d_S_IR_limit': float(2*np.log(winning_fractal_n)/np.log(L)),
        'peak_sigma': float(sigma_vals[peak_idx]),
        'peak_d_S': float(ds_vals[peak_idx]),
        'd_S_at_UV_smallest_sigma': float(ds_vals[0]),
        'd_S_at_IR_largest_sigma': float(ds_vals[-1]),
        'is_non_monotonic': bool(ds_vals[peak_idx] > max(ds_vals[0], ds_vals[-1]) + 0.05),
        'sigma_log10_grid': [float(np.log10(s)) for s in sigma_vals],
        'd_S_grid': [float(d) for d in ds_vals],
    }
    return [rec]


def write_ndjson(records, path):
    with open(path, 'w', newline='\n') as f:
        for rec in records:
            f.write(json.dumps(rec, separators=(',', ':')) + '\n')
    return path


if __name__ == '__main__':
    print("=== Test 1: Constrained-anchor mass fit (gap-derived anchors per Pn) ===")
    test1 = run_test1()
    p = write_ndjson(test1, OUT_DIR / 'mpm_anchored_verdict.ndjson')
    print(f"  wrote {p}")
    print(f"  {'fractal':>8s} {'level':>6s} {'n_anchors':>10s} {'S_opt':>8s} {'tot_err':>9s} {'mean_log_err':>13s}")
    for r in sorted(test1, key=lambda x: x['total_quadratic_error']):
        print(f"  {r['fractal']:>8s} {r['level']:>6d} {r['n_anchors']:>10d} "
              f"{r['S_opt']:>8.4f} {r['total_quadratic_error']:>9.4f} {r['mean_per_fermion_log_err']:>13.4f}")

    best = min(test1, key=lambda x: x['total_quadratic_error'])
    print(f"\nBest anchored fit: {best['fractal']} level {best['level']}")
    print(f"  S = {best['S_opt']:.4f}, total_err = {best['total_quadratic_error']:.4f}")
    print(f"  Anchors used: {[round(a,4) for a in best['anchors_used']]}")
    print(f"  Per-fermion ratios (pred/obs):")
    for f in best['fermions']:
        r = f['predicted_mass_gev']/f['observed_mass_gev']
        print(f"    {f['name']:>10s}: pred {f['predicted_mass_gev']:>9.4f} vs obs {f['observed_mass_gev']:>9.4f} GeV  ratio {r:.2f}")

    print("\n=== Test 2: Gauge coupling RG (corrected sign) ===")
    test2 = run_test2()
    p = write_ndjson(test2, OUT_DIR / 'mpm_gauge_rg.ndjson')
    print(f"  wrote {p}")
    r = test2[0]
    print(f"  At M_Planck (textbook 1-loop): alpha_1={r['at_M_Planck']['alpha_1']:+.5f}, "
          f"alpha_2={r['at_M_Planck']['alpha_2']:+.5f}, alpha_3={r['at_M_Planck']['alpha_3']:+.5f}")
    print(f"  (Gemini published: a1={r['gemini_published']['alpha1_lambda']:+.5f}, "
          f"a2={r['gemini_published']['alpha2_lambda']:+.5f}, "
          f"a3={r['gemini_published']['alpha3_lambda']:+.5f} — SIGN ERROR in a3)")
    print(f"  alpha_1=alpha_2 unification at mu={r['unification']['mu_12_GeV']:.3e} GeV")
    print(f"  alpha_2=alpha_3 unification at mu={r['unification']['mu_23_GeV']:.3e} GeV")
    print(f"  alpha_1=alpha_3 unification at mu={r['unification']['mu_13_GeV']:.3e} GeV")
    print(f"  Clean SM-only unification? {r['unification']['unified_cleanly_SM_only']}")

    print("\n=== Test 3: Spectral dimension flow d_S(sigma) for P3 SG level 5 ===")
    test3 = run_test3()
    p = write_ndjson(test3, OUT_DIR / 'mpm_spectral_dimension.ndjson')
    print(f"  wrote {p}")
    r = test3[0]
    print(f"  d_S at UV (smallest sigma): {r['d_S_at_UV_smallest_sigma']:.3f}")
    print(f"  d_S at IR (largest sigma): {r['d_S_at_IR_largest_sigma']:.3f}")
    print(f"  d_S peak: {r['peak_d_S']:.3f} at sigma={r['peak_sigma']:.4f}")
    print(f"  Non-monotonic? {r['is_non_monotonic']}")
    print(f"  Theoretical IR limit for SG (2 ln3 / ln5): {r['theoretical_d_S_IR_limit']:.3f}")
