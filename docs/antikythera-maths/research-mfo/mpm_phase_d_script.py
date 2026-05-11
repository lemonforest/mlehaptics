"""MFO Phase D: Product-manifold mass prediction (SG × CP² × S¹).

Phase C established:
  - SG λ=6 hosts the 18 generation-block COUNT (3 gens × 6 within-gen positions);
  - BIP-cosine alone cannot derive QN-to-block geometrically (tautology under
    720-permutation stress test).
Phase D moves to the product manifold MFO §IV.4 prediction:

  λ_total = λ_SG + c_CP² · λ_CP² + λ_S¹

with PRINCIPLED gauge-quantum-number-to-mode rules (no per-particle freedom).
Three global parameters fit jointly: S (scale), R (S¹ radius), c_CP² (CP² weight).

Rules tested:
  - color → CP² mode: lepton (singlet) → λ_CP² = 0; quark (triplet) → λ_CP² = 12
    (the smallest nontrivial Fubini-Study eigenvalue, p+q=1).
  - generation/within-gen → SG eigenvalue: lift Phase B (d) per-fermion λ_SG
    assignment (1 parameter to fit on its own; for D, those λ_SG values are FIXED
    from B (d) — no re-search).
  - charge → S¹ harmonic: n_S¹ rule, several candidates tested:
      (R1) n_S¹ = round(6·Q)              [n²: lepton 36, up 16, down 4]
      (R2) n_S¹ = round(3·2T₃) = 3·(2T₃)   [n²: T₃=±1/2 → ±3, n²=9 for all charged
                                            (singlets get T₃=0, n=0 — not useful)]
      (R3) n_S¹ = round(Y) with Y the SM hypercharge integer (×6 convention scaled):
           lepton-L Y=-3 → n=-3, n²=9; up-R Y=+4 → n=4, n²=16; down-R Y=-2 → n=2,
           n²=4; etc.
      (R4) n_S¹ = 0 for all → degenerates to SG+CP² fit
      (R5) n_S¹ = round(2·Q) → lepton n=2, up n=1, down n=-1 (smaller integers,
           less spread)

Comparison targets:
  - Phase B (d) SG-only mult-aware gap-anchored: total_err = 0.319
  - Gemini's cp2_assignment (per-particle params): total_err = 1.262
  - Phase D principled: depends on rule.

Outputs (under results-mfo/):
  - mpm_phase_d_spectra.ndjson      eigenvalues for SG (Phase A); CP²; S¹; product
  - mpm_phase_d_fits.ndjson         one record per (rule, optimum)
  - mpm_phase_d_residuals.ndjson    per-fermion residuals for the best rule
  - mpm_phase_d_findings.md         short writeup

Also appends one completion line to research-mfo/mfo_mpm_notes.ndjson.

All output files written with newline='\n' and JSON separators=(',', ':') to
match the project's NDJSON-without-indent house style.

Math doesn't lie. Anomaly authority: if every principled rule fails to beat
SG-alone by >10%, that is a NEGATIVE finding to surface clearly. If a rule
beats it materially, surface that too.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

# Ensure stdout can carry UTF-8 glyphs on Windows consoles (cp1252 default).
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        pass

# === Paths ===
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / 'results-mfo'
NOTES = HERE / 'mfo_mpm_notes.ndjson'
EIGVAL_NDJSON = RESULTS / 'mpm_phase_a_eigenvalues.ndjson'

# === Constants ===
M_E = 0.000511  # electron mass in GeV
SM_MASSES_GEV = {
    'electron': 0.000511,
    'up': 0.0022, 'down': 0.0047,
    'strange': 0.095, 'muon': 0.1057,
    'charm': 1.275, 'tau': 1.777,
    'bottom': 4.18, 'top': 173.0,
}
SM_SORTED = sorted(SM_MASSES_GEV, key=lambda p: SM_MASSES_GEV[p])
TARGET_LOG = {p: math.log10((SM_MASSES_GEV[p] / M_E) ** 2)
              for p in SM_MASSES_GEV}
TARGET_VEC = np.array([TARGET_LOG[p] for p in SM_SORTED])

# Phase B (d) per-fermion SG assignment (gap-anchored, mult-aware, direct-graph).
# Source: mpm_phase_b_mass_fit.ndjson variant=scale_only_gap_anchored_mult_aware_direct.
# Values are 'mapped_eigenvalue' per fermion (the SG λ each fermion is assigned to).
SG_LAMBDA_B_d = {
    'electron': 0.0,
    'up': 0.6372179342523516,
    'down': 0.8776664919782649,
    'strange': 2.250469604435777,
    'muon': 2.999999999999999,
    'charm': 3.6180339887498962,
    'tau': 3.8954298127344167,
    'bottom': 4.302775637731995,
    'top': 5.999999999999999,
}
SG_LAMBDA_VEC = np.array([SG_LAMBDA_B_d[p] for p in SM_SORTED])

# SM quantum numbers per charged-fermion mass eigenstate. We use the simplest
# rule: each fermion's "effective" electric charge Q drives the S¹ harmonic.
# For the lepton sector (charged): Q = -1.
# For up-type quarks (u, c, t): Q = +2/3.
# For down-type quarks (d, s, b): Q = -1/3.
# Hypercharge Y (Y = Q - T₃) for right-handed singlets (mass eigenstates):
# - charged lepton-R: Y = -1 (×6 = -6)
# - up-R: Y = +2/3 (×6 = +4)
# - down-R: Y = -1/3 (×6 = -2)
# We use Y_int = Y × 6 (integer) for clean S¹ harmonic candidates.
SM_QN = {
    'electron': {'Q': -1.0,   'Y6': -6, 'color': 0, 'gen': 1},
    'up':       {'Q': +2/3.,  'Y6': +4, 'color': 3, 'gen': 1},
    'down':     {'Q': -1/3.,  'Y6': -2, 'color': 3, 'gen': 1},
    'strange':  {'Q': -1/3.,  'Y6': -2, 'color': 3, 'gen': 2},
    'muon':     {'Q': -1.0,   'Y6': -6, 'color': 0, 'gen': 2},
    'charm':    {'Q': +2/3.,  'Y6': +4, 'color': 3, 'gen': 2},
    'tau':      {'Q': -1.0,   'Y6': -6, 'color': 0, 'gen': 3},
    'bottom':   {'Q': -1/3.,  'Y6': -2, 'color': 3, 'gen': 3},
    'top':      {'Q': +2/3.,  'Y6': +4, 'color': 3, 'gen': 3},
}


# === Spectra ===
def load_sg_eigenvalues_level5():
    """Read Phase A direct-graph SG eigenvalues at level 5.

    Returns list of (eigenvalue, multiplicity), in ascending eigenvalue order.
    """
    rows = []
    for line in EIGVAL_NDJSON.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec['level'] != 5:
            continue
        ev = float(rec['eigenvalue'])
        if ev < 0:  # numerical noise on zero mode
            ev = 0.0
        rows.append((ev, int(rec['multiplicity_at_eigenvalue'])))
    rows.sort(key=lambda x: x[0])
    return rows


def cp2_eigenvalues(p_max=4):
    """CP² Fubini-Study Laplacian eigenvalues λ_{p,q} = 4(p+q)(p+q+2).

    Distinct values for p + q <= p_max. Multiplicity here is the count of
    (p, q) pairs with p + q = k (k+1 values). For Phase D mass-magnitude work
    we only need the distinct eigenvalues; the assignment rule is 'color → mode'
    not 'distinct λ per fermion'.
    """
    rows = []
    for k in range(p_max + 1):
        lam = 4.0 * k * (k + 2)
        mult = k + 1  # number of (p, q) with p+q=k
        rows.append({'k': k, 'eigenvalue': lam, 'mult_pq': mult,
                     'formula': '4(p+q)(p+q+2)'})
    return rows


def s1_eigenvalues(R, n_max=6):
    """S¹(R) Laplacian eigenvalues λ_n = n²/R²; multiplicity 2 for n>0, 1 for n=0."""
    rows = []
    for n in range(-n_max, n_max + 1):
        rows.append({'n': n, 'eigenvalue': (n * n) / (R * R) if R > 0 else 0.0,
                     'R': R})
    return rows


# === S¹ rules ===
def n_rule(name, qn):
    """Return the S¹ harmonic n given a rule name and a fermion's QN dict."""
    Q = qn['Q']
    Y6 = qn['Y6']
    if name == 'R1_6Q':
        return int(round(6 * Q))
    if name == 'R2_3times_2T3':
        # 2T₃ = ±1 for L doublet, 0 for R singlets. Mass eigenstates are
        # *predominantly* R-handed singlets after EWSB ⇒ T₃ = 0 for all
        # right-handed singlets. This rule collapses S¹ to n=0 for all,
        # degenerating to SG+CP² only. We keep it as a degeneracy check.
        return 0
    if name == 'R3_Y6':
        # n_S¹ = Y×6 = Y6 directly. lepton n=-6 (n²=36); up n=+4 (n²=16); down n=-2 (n²=4)
        return Y6
    if name == 'R4_zero':
        return 0
    if name == 'R5_2Q':
        return int(round(2 * Q))
    if name == 'R6_3Q':
        # lepton n=-3 (n²=9); up n=+2 (n²=4); down n=-1 (n²=1)
        return int(round(3 * Q))
    if name == 'R7_Y3':
        # Y normalized ×3 (so Y_lepton_R = -3, Y_up_R = +2, Y_down_R = -1)
        return Y6 // 2
    raise ValueError(f'Unknown rule: {name}')


def cp2_mode_for(qn):
    """color → CP² mode rule: lepton (singlet) → λ_CP² = 0; quark (triplet) → 12.

    Eigenvalue 12 is the smallest nontrivial CP² eigenvalue (p+q=1).
    This is a single fixed rule with no per-particle freedom.
    """
    return 0.0 if qn['color'] == 0 else 12.0


# === Fit ===
def predict_log_m2(S, R, c_CP2, fermion, rule):
    """Predicted log10(m²/m_e²) for a fermion under (S, R, c_CP2, rule).

    Formula:
      λ_total = λ_SG(fermion) + c_CP² · λ_CP²(color) + λ_S¹(charge)
      predicted_log_m² = (λ_total - λ_total_electron) / S

    The electron-subtraction ensures predicted_log_m²(electron) = 0 exactly,
    matching the target convention log10(m²_e/m²_e) = 0.
    """
    qn = SM_QN[fermion]
    lam_sg = SG_LAMBDA_B_d[fermion]
    lam_cp2 = cp2_mode_for(qn)
    n = n_rule(rule, qn)
    lam_s1 = (n * n) / (R * R) if R > 0 else 0.0
    lam_total = lam_sg + c_CP2 * lam_cp2 + lam_s1
    return lam_total


def fit_one_rule(rule, S_grid, R_grid, cCP2_grid):
    """Grid search over (S, R, c_CP2) minimising total quadratic log-error.

    Returns dict with best (S, R, c_CP2), error, and per-fermion predictions.
    """
    # Precompute electron's λ_total at each (R, c_CP2)
    best_err = math.inf
    best = None

    qn_table = {p: SM_QN[p] for p in SM_SORTED}
    lam_sg_arr = SG_LAMBDA_VEC
    lam_cp2_arr = np.array([cp2_mode_for(qn_table[p]) for p in SM_SORTED])
    n_arr = np.array([n_rule(rule, qn_table[p]) for p in SM_SORTED], dtype=float)
    n2_arr = n_arr * n_arr

    for R in R_grid:
        s1_arr = n2_arr / (R * R) if R > 0 else np.zeros_like(n2_arr)
        for c_CP2 in cCP2_grid:
            lam_total = lam_sg_arr + c_CP2 * lam_cp2_arr + s1_arr
            # Subtract electron value so electron's predicted log_m² is 0
            lam_total = lam_total - lam_total[0]  # electron is SM_SORTED[0]
            for S in S_grid:
                if S <= 0:
                    continue
                pred = lam_total / S
                err = float(np.sum((pred - TARGET_VEC) ** 2))
                if err < best_err:
                    best_err = err
                    best = {
                        'S': float(S),
                        'R': float(R),
                        'c_CP2': float(c_CP2),
                        'total_err': err,
                        'pred_log_m2': pred.tolist(),
                        'n_S1_per_fermion': n_arr.tolist(),
                        'lam_cp2_per_fermion': lam_cp2_arr.tolist(),
                        'lam_sg_per_fermion': lam_sg_arr.tolist(),
                    }
    best['rule'] = rule
    return best


def refine_around(rule, best_coarse, S_pad=0.2, R_pad=0.2, cCP2_pad=0.2, n_each=41):
    """Refined grid search near the coarse optimum, with logarithmic granularity."""
    S0 = best_coarse['S']
    R0 = best_coarse['R']
    c0 = best_coarse['c_CP2']
    S_grid = np.linspace(max(1e-3, S0 * (1 - S_pad)), S0 * (1 + S_pad), n_each)
    R_grid = np.linspace(max(1e-3, R0 * (1 - R_pad)), R0 * (1 + R_pad), n_each)
    cCP2_grid = np.linspace(max(0.0, c0 * (1 - cCP2_pad)), max(c0 * (1 + cCP2_pad), 1e-3), n_each)
    return fit_one_rule(rule, S_grid, R_grid, cCP2_grid)


# === Main ===
def main():
    print("MFO Phase D -- product-manifold mass prediction (SG x CP2 x S1)")
    print(f"  output dir: {RESULTS}")
    print(f"  Phase B (d) SG per-fermion assignment (fixed): "
          f"{[round(SG_LAMBDA_B_d[p], 4) for p in SM_SORTED]}")
    print(f"  SM targets log10(m^2/m_e^2): "
          f"{[round(t, 4) for t in TARGET_VEC.tolist()]}")

    # === Write spectra ===
    spectra_path = RESULTS / 'mpm_phase_d_spectra.ndjson'
    sg_rows = load_sg_eigenvalues_level5()
    print(f"\n  Loaded {len(sg_rows)} distinct SG level-5 eigenvalues from Phase A")
    cp2_rows = cp2_eigenvalues(p_max=4)
    print(f"  CP2 eigenvalues (p+q <= 4): "
          f"{[r['eigenvalue'] for r in cp2_rows]}")
    # Default R for spectrum dump (will be refit). Use R=1.0 as illustrative.
    s1_rows = s1_eigenvalues(R=1.0, n_max=6)
    with open(spectra_path, 'w', newline='\n') as f:
        for ev, mult in sg_rows:
            f.write(json.dumps({
                'manifold': 'SG_pre_gasket_level5',
                'eigenvalue': ev, 'multiplicity': mult,
                'source': 'mpm_phase_a_eigenvalues.ndjson',
            }, separators=(',', ':')) + '\n')
        for r in cp2_rows:
            f.write(json.dumps({
                'manifold': 'CP2_Fubini_Study',
                'eigenvalue': r['eigenvalue'], 'k_pq_sum': r['k'],
                'multiplicity_pq_count': r['mult_pq'],
                'formula': r['formula'],
            }, separators=(',', ':')) + '\n')
        for r in s1_rows:
            f.write(json.dumps({
                'manifold': 'S1_R1.0_illustrative',
                'eigenvalue': r['eigenvalue'], 'n': r['n'], 'R': r['R'],
            }, separators=(',', ':')) + '\n')
        # Also emit first ~100 product eigenvalues at R=1.0, c_CP2=1.0
        # for documentation only (we'll fit actual R, c_CP2 below)
        prod = []
        for ev_sg, _ in sg_rows[:30]:
            for r_cp2 in cp2_rows[:3]:
                for r_s1 in s1_rows:
                    prod.append({
                        'manifold': 'product_SG_x_CP2_x_S1_illustrative_R1_c1',
                        'lambda_SG': ev_sg, 'lambda_CP2': r_cp2['eigenvalue'],
                        'lambda_S1': r_s1['eigenvalue'],
                        'lambda_total': ev_sg + r_cp2['eigenvalue'] + r_s1['eigenvalue'],
                    })
        prod.sort(key=lambda r: r['lambda_total'])
        for r in prod[:100]:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    print(f"  → wrote {spectra_path}")

    # === Fit per rule ===
    rules = ['R1_6Q', 'R3_Y6', 'R4_zero', 'R5_2Q', 'R6_3Q', 'R7_Y3', 'R2_3times_2T3']

    # Coarse grid
    S_grid_coarse = np.linspace(0.05, 2.0, 60)
    R_grid_coarse = np.linspace(0.5, 5.0, 25)
    cCP2_grid_coarse = np.linspace(0.0, 0.6, 25)

    fits = []
    for rule in rules:
        print(f"\n  === rule: {rule} ===")
        n_vec = [n_rule(rule, SM_QN[p]) for p in SM_SORTED]
        print(f"    n_S1 per fermion (order {SM_SORTED}): {n_vec}")
        coarse = fit_one_rule(rule, S_grid_coarse, R_grid_coarse, cCP2_grid_coarse)
        print(f"    coarse: S={coarse['S']:.4f}, R={coarse['R']:.4f}, "
              f"c_CP2={coarse['c_CP2']:.4f}, err={coarse['total_err']:.4f}")
        # Refinement
        refined = refine_around(rule, coarse, n_each=41)
        # Double refinement for stability
        refined2 = refine_around(rule, refined, S_pad=0.05, R_pad=0.05,
                                  cCP2_pad=0.05, n_each=41)
        print(f"    refined: S={refined2['S']:.4f}, R={refined2['R']:.4f}, "
              f"c_CP2={refined2['c_CP2']:.4f}, err={refined2['total_err']:.4f}")
        fits.append(refined2)

    # === Write fits ndjson ===
    fits_path = RESULTS / 'mpm_phase_d_fits.ndjson'
    with open(fits_path, 'w', newline='\n') as f:
        # Baselines
        f.write(json.dumps({
            'kind': 'baseline',
            'name': 'phase_b_d_sg_only_gap_anchored_mult_aware',
            'total_err': 0.31901432489030274,
            'n_params': 1, 'param_names': ['S'],
            'n_per_particle_params': 0,
            'note': 'Phase B variant (d), framework-honest, mult-aware gap-anchored.',
        }, separators=(',', ':')) + '\n')
        f.write(json.dumps({
            'kind': 'baseline',
            'name': 'gemini_cp2_assignment_per_particle',
            'total_err': 1.262,
            'n_params': 18, 'param_names': ['9 × (s1_n, cp2_k)'],
            'n_per_particle_params': 18,
            'note': 'Reference per-particle free-parameter fit; total_err per Phase C summary.',
        }, separators=(',', ':')) + '\n')
        # Phase D rule fits
        for fit in fits:
            f.write(json.dumps({
                'kind': 'phase_d_rule_fit',
                'rule': fit['rule'],
                'S': fit['S'], 'R': fit['R'], 'c_CP2': fit['c_CP2'],
                'total_err': fit['total_err'],
                'n_global_params': 3,
                'n_per_particle_params': 0,
                'n_S1_per_fermion': fit['n_S1_per_fermion'],
                'lam_cp2_per_fermion': fit['lam_cp2_per_fermion'],
                'lam_sg_per_fermion': fit['lam_sg_per_fermion'],
                'pred_log_m2_per_fermion_order': SM_SORTED,
                'pred_log_m2': fit['pred_log_m2'],
                'target_log_m2': TARGET_VEC.tolist(),
            }, separators=(',', ':')) + '\n')
    print(f"\n  → wrote {fits_path}")

    # === Pick best rule and write residuals ===
    best_fit = min(fits, key=lambda f: f['total_err'])
    print(f"\n  Best rule: {best_fit['rule']} with total_err = {best_fit['total_err']:.4f}")
    baseline_b_d = 0.31901432489030274
    delta = baseline_b_d - best_fit['total_err']
    pct = 100.0 * delta / baseline_b_d
    print(f"  vs Phase B (d) baseline {baseline_b_d:.4f}: "
          f"Δ = {delta:+.4f} ({pct:+.1f}% improvement)")

    residuals_path = RESULTS / 'mpm_phase_d_residuals.ndjson'
    with open(residuals_path, 'w', newline='\n') as f:
        for i, p in enumerate(SM_SORTED):
            qn = SM_QN[p]
            target = TARGET_VEC[i]
            pred = best_fit['pred_log_m2'][i]
            resid = pred - target
            within_10pct = bool(abs(resid) < math.log10(1.10 ** 2))  # ±10% mass
            within_30pct = bool(abs(resid) < math.log10(1.30 ** 2))  # ±30% mass
            f.write(json.dumps({
                'fermion': p,
                'rule': best_fit['rule'],
                'observed_mass_gev': SM_MASSES_GEV[p],
                'target_log_m2_me2': float(target),
                'pred_log_m2_me2': float(pred),
                'residual_log_m2': float(resid),
                'pred_mass_gev': float(M_E * math.sqrt(10 ** pred)),
                'Q': qn['Q'], 'Y6': qn['Y6'], 'color': qn['color'], 'gen': qn['gen'],
                'lam_SG': best_fit['lam_sg_per_fermion'][i],
                'lam_CP2_term': best_fit['c_CP2'] * best_fit['lam_cp2_per_fermion'][i],
                'lam_S1_term': (best_fit['n_S1_per_fermion'][i] ** 2) / (best_fit['R'] ** 2),
                'within_10pct_mass': within_10pct,
                'within_30pct_mass': within_30pct,
                'within_factor2_mass': bool(abs(resid) < math.log10(4.0)),
            }, separators=(',', ':')) + '\n')
    print(f"  → wrote {residuals_path}")

    # === Findings markdown ===
    findings_path = RESULTS / 'mpm_phase_d_findings.md'
    sorted_fits = sorted(fits, key=lambda f: f['total_err'])
    with open(findings_path, 'w', newline='\n', encoding='utf-8') as f:
        f.write("# MFO Phase D: Product-manifold mass prediction (SG × CP² × S¹)\n\n")
        f.write("**Date:** 2026-05-09 · **Phase:** D (downstream of A spectrum, B mass-fit, C QN-binding)\n\n")
        f.write("## The load-bearing question\n\n")
        f.write("Notebook §IV.4 predicts: product geometry F × CP² × S¹ inherits "
                "large-scale gaps from F (between generations), fine structure from "
                "gauge manifolds (within generations), and multiplet degeneracies from "
                "gauge group reps. **Does a principled gauge-quantum-number-to-mode rule "
                "(no per-particle freedom) on top of the Phase B (d) SG assignment, with "
                "CP² × S¹ as fine-structure factors, beat the SG-only baseline?**\n\n")

        f.write("## Setup\n\n")
        f.write("- **λ_total = λ_SG + c_CP² · λ_CP² + λ_S¹**, with electron subtracted.\n")
        f.write("- λ_SG from Phase B (d) mult-aware gap-anchored fit (fixed, not refit).\n")
        f.write("- λ_CP² rule (single, fixed): lepton (color singlet) → 0; "
                "quark (color triplet) → 12 (smallest nontrivial Fubini-Study eigenvalue).\n")
        f.write("- λ_S¹ = n² / R² with several principled n(QN) rules tested:\n")
        f.write("  - R1_6Q: n = round(6·Q)\n")
        f.write("  - R3_Y6: n = Y × 6 (right-handed singlet hypercharge)\n")
        f.write("  - R4_zero: n = 0 (degeneracy check, no S¹)\n")
        f.write("  - R5_2Q: n = round(2·Q)\n")
        f.write("  - R6_3Q: n = round(3·Q)\n")
        f.write("  - R7_Y3: n = Y × 3\n")
        f.write("  - R2_3times_2T3: n = 0 for R-singlets (degeneracy)\n\n")
        f.write("- **3 global parameters** fit jointly: S (scale), R (S¹ radius), c_CP² (CP² weight). No per-particle freedom.\n\n")

        f.write("## Results\n\n")
        f.write("| rule | S | R | c_CP² | total_err | vs Phase B (d) |\n")
        f.write("|:---|---:|---:|---:|---:|:---|\n")
        f.write(f"| **baseline: Phase B (d) SG-only** | 0.5467 | – | – | "
                f"**{baseline_b_d:.4f}** | – |\n")
        f.write(f"| baseline: Gemini cp2_assignment (18 per-particle params) | – | – | – | 1.262 | – |\n")
        for fit in sorted_fits:
            delta = baseline_b_d - fit['total_err']
            pct = 100.0 * delta / baseline_b_d
            if delta > 0:
                tag = f"{pct:+.1f}% better"
            else:
                tag = f"{abs(pct):.1f}% worse"
            f.write(f"| {fit['rule']} | {fit['S']:.4f} | {fit['R']:.4f} | "
                    f"{fit['c_CP2']:.4f} | {fit['total_err']:.4f} | {tag} |\n")
        f.write("\n")

        # Verdict block
        best_rule = sorted_fits[0]['rule']
        best_err = sorted_fits[0]['total_err']
        best_delta = baseline_b_d - best_err
        best_pct = 100.0 * best_delta / baseline_b_d
        material_gain = best_pct >= 10.0
        slight_gain = 0.0 < best_pct < 10.0
        no_gain = best_pct <= 0.0

        f.write("## Verdict\n\n")
        if material_gain:
            verdict_word = "MATERIALLY BEATS"
            outcome = ("Adding principled CP² × S¹ fine structure on top of the Phase B (d) "
                       "SG assignment closes a meaningful fraction of the residual SG-only error. "
                       "The §IV.4 prediction is supported at the qualitative-with-principled-rules level.")
        elif slight_gain:
            verdict_word = "MARGINALLY BEATS"
            outcome = ("CP² × S¹ provide a small improvement over SG-alone but not the order-of-magnitude "
                       "gain that the §IV.4 'fine structure from gauge manifolds' framing implied. "
                       "The framework's prediction is **weakly supported**: the geometry does carry "
                       "some fine-structure content, but the magnitude is modest.")
        elif no_gain:
            verdict_word = "DOES NOT BEAT"
            outcome = ("No principled S¹ harmonic rule, combined with the fixed color → CP² rule, "
                       "improves the SG-only baseline. The §IV.4 'fine structure from gauge manifolds' "
                       "prediction is **not borne out** by L=5 SG + first-CP² mode + simple-rule S¹ "
                       "with 3 global parameters. Either the per-particle rules are wrong, the SG "
                       "λ-assignment (Phase B (d)) is already absorbing the fine structure, or the "
                       "product-spectrum addition λ_F + λ_CP² + λ_S¹ is the wrong combination operation.")
        else:
            verdict_word = "TIES"
            outcome = "Improvement is at the noise floor."

        if best_pct >= 0:
            f.write(f"**Best principled rule ({best_rule}) {verdict_word} the SG-only baseline "
                    f"by {best_pct:.1f}% (best total_err = {best_err:.4f} vs "
                    f"{baseline_b_d:.4f}).**\n\n")
        else:
            f.write(f"**Best principled rule ({best_rule}) {verdict_word} the SG-only baseline "
                    f"(total_err {best_err:.4f} vs {baseline_b_d:.4f}; "
                    f"product-manifold fit is {abs(best_pct):.1f}% WORSE than SG-alone).**\n\n")
        f.write(outcome + "\n\n")

        # Degeneracy check
        zero_like_rules = [f for f in sorted_fits
                            if f['rule'] in ('R4_zero', 'R2_3times_2T3')]
        if zero_like_rules:
            zr = zero_like_rules[0]
            f.write(f"**Degeneracy check:** rule R4_zero (n_S¹ ≡ 0 for all fermions) lands at "
                    f"total_err = {zr['total_err']:.4f} with c_CP² = {zr['c_CP2']:.4f}. "
                    f"If a non-zero S¹ rule produces total_err near this value, the optimizer "
                    f"is collapsing S¹ out (R → ∞ or n → 0 effective). ")
            best_nonzero = [f for f in sorted_fits if f['rule'] not in ('R4_zero', 'R2_3times_2T3')]
            if best_nonzero:
                bn = best_nonzero[0]
                gap_to_zero = zr['total_err'] - bn['total_err']
                f.write(f"Best non-zero S¹ rule: {bn['rule']} at {bn['total_err']:.4f} "
                        f"({gap_to_zero:+.4f} vs R4_zero {zr['total_err']:.4f}). ")
                if abs(gap_to_zero) < 0.02:
                    f.write("**Gap < 0.02 — S¹ is being optimised away.** The data does not "
                            "demand the S¹ factor.\n\n")
                else:
                    f.write("S¹ factor contributes meaningfully (not optimised away).\n\n")

        f.write("## Per-fermion residuals for best rule\n\n")
        f.write(f"Best rule: **{best_rule}**, S = {sorted_fits[0]['S']:.4f}, "
                f"R = {sorted_fits[0]['R']:.4f}, c_CP² = {sorted_fits[0]['c_CP2']:.4f}.\n\n")
        f.write("| fermion | obs mass (GeV) | pred mass (GeV) | residual log m² | within ±30% mass | Q | color |\n")
        f.write("|:---|---:|---:|---:|:---:|---:|---:|\n")
        for i, p in enumerate(SM_SORTED):
            qn = SM_QN[p]
            target = TARGET_VEC[i]
            pred = sorted_fits[0]['pred_log_m2'][i]
            resid = pred - target
            pred_mass = M_E * math.sqrt(10 ** pred)
            ok = '✓' if abs(resid) < math.log10(1.30 ** 2) else '✗'
            f.write(f"| {p} | {SM_MASSES_GEV[p]:.4g} | {pred_mass:.4g} | "
                    f"{resid:+.4f} | {ok} | {qn['Q']:+.3f} | {qn['color']} |\n")
        f.write("\n")

        # Residual pattern check
        leptons = [i for i, p in enumerate(SM_SORTED) if SM_QN[p]['color'] == 0]
        quarks = [i for i, p in enumerate(SM_SORTED) if SM_QN[p]['color'] != 0]
        up_type = [i for i, p in enumerate(SM_SORTED) if SM_QN[p]['Q'] > 0]
        down_type = [i for i, p in enumerate(SM_SORTED) if SM_QN[p]['Q'] < 0 and SM_QN[p]['color'] != 0]
        preds = np.array(sorted_fits[0]['pred_log_m2'])
        targets = TARGET_VEC
        rs = preds - targets
        f.write("## Residual decomposition by quantum number\n\n")
        f.write(f"- Lepton residuals (electron, muon, tau, n={len(leptons)}): "
                f"mean = {float(np.mean(rs[leptons])):+.4f}, "
                f"|RMS| = {float(np.sqrt(np.mean(rs[leptons] ** 2))):.4f}\n")
        f.write(f"- Quark residuals (n={len(quarks)}): "
                f"mean = {float(np.mean(rs[quarks])):+.4f}, "
                f"|RMS| = {float(np.sqrt(np.mean(rs[quarks] ** 2))):.4f}\n")
        f.write(f"- Up-type quark residuals (u, c, t): "
                f"mean = {float(np.mean(rs[up_type])):+.4f}, "
                f"|RMS| = {float(np.sqrt(np.mean(rs[up_type] ** 2))):.4f}\n")
        f.write(f"- Down-type quark residuals (d, s, b): "
                f"mean = {float(np.mean(rs[down_type])):+.4f}, "
                f"|RMS| = {float(np.sqrt(np.mean(rs[down_type] ** 2))):.4f}\n\n")

        f.write("## What this means for notebook §IV.4\n\n")
        if material_gain:
            f.write("**Status update suggestion for §IV.4:** the qualitative match noted in the "
                    "notebook becomes a quantitative-with-principled-rules result: 3 global parameters "
                    "(S, R, c_CP²) + fixed color→CP² rule + a principled charge→S¹ harmonic rule "
                    f"reduce SG-only error by {best_pct:.0f}% on the 9 charged-fermion mass ratios.\n")
        elif slight_gain:
            f.write("**Status update suggestion for §IV.4:** the qualitative-match phrasing should "
                    "stay qualitative. Adding CP² × S¹ with principled rules gives only a "
                    f"{best_pct:.0f}% improvement over SG-alone — the framework's prediction is "
                    "consistent with but not strongly supported by this geometric instantiation.\n")
        else:
            f.write("**Status update suggestion for §IV.4:** the 'fine structure from gauge manifolds' "
                    "claim is **not vindicated** by L=5 SG + first-CP² mode + simple charge→S¹ rules "
                    "with 3 global parameters. The SG λ-assignment already saturates the available "
                    "mass-magnitude information; adding CP² × S¹ with simple principled rules does "
                    "not improve the fit. Either the framework needs (i) more CP² modes per fermion, "
                    "(ii) per-fermion S¹ radii (breaking the 'single S¹' assumption), or "
                    "(iii) a different combination operation (multiplicative rather than additive) — "
                    "all of which dilute the §IV.4 prediction's principled character.\n")
        f.write("\n")

        f.write("## Anomaly authority\n\n")
        f.write("- If R4_zero (n_S¹ ≡ 0) ties the non-zero rules: S¹ is being optimised away. "
                "Reported in the degeneracy-check paragraph above.\n")
        f.write("- If c_CP² → 0 in the optimum: CP² is being optimised away. Check the best-fit "
                "c_CP² value above.\n")
        f.write("- The per-fermion SG λ from Phase B (d) is held fixed in Phase D — this is the "
                "**multiplicity-aware mult-anchored** Phase B fit, framework-honest. We did NOT "
                "re-search SG assignments; if we did, we'd be re-fitting Phase B inside Phase D "
                "and the comparison would be unfair.\n")

    print(f"  → wrote {findings_path}")

    # === Notes line ===
    completion = {
        'date': '2026-05-09',
        'phase': 'D',
        'kind': 'completion',
        'note': (f"Phase D done. Product manifold SG × CP² × S¹ with principled QN rules. "
                 f"Best rule: {best_rule}, total_err = {best_err:.4f} "
                 f"(vs Phase B (d) SG-only {baseline_b_d:.4f}, "
                 f"Δ = {best_delta:+.4f}, {best_pct:+.1f}%). "
                 f"3 global params (S, R, c_CP²), no per-particle freedom. "
                 f"Verdict: {'beats' if best_pct >= 10 else 'marginal/ties' if best_pct > 0 else 'does not beat'} "
                 f"SG-only baseline."),
    }
    with open(NOTES, 'a', newline='\n') as f:
        f.write(json.dumps(completion, separators=(',', ':')) + '\n')
    print(f"\n  Appended completion line to {NOTES}")


if __name__ == '__main__':
    main()
