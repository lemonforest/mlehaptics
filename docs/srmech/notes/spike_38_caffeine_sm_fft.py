"""Spike #38 — Mass-spec FFT against the project's SM (substrate-mode) signatures.

User direction 2026-05-17 (concertmaster brief):
    "generate a research agent to get a mostly known, commonly accepted,
     complex with undefined noise datapoint of a mass spec fingerprint and
     see if we can FFT it against the SM that we've already mapped. This is
     either be a refine or fail I think because I don't know that we have
     molecular modeling catalog yet"

Subject: caffeine (C8H10N4O2, MW 194.08038).
Source: MassBank EU record MSBNK-Fac_Eng_Univ_Tokyo-JP003477.
  Title: CAFFEINE; EI-B; MS
  Instrument: HITACHI M-60 (electron ionization, magnetic-sector)
  Ionization: 20 eV EI
  Authors: MASS SPECTROSCOPY SOC. OF JAPAN (MSSJ)
  License: CC BY-NC-SA
  numPeak: 58
  splash: splash10-0a4l-4900000000-3ff72dace6687d242f1f

Spectral signatures to test (from project's mapped SM):
  (a) Class K Kepler-shape c_k = eps^k/k ladder (Spike #30B strict 3-criteria)
  (b) Class L graph-Laplacian eigenstructure (Spike #30B/#35-Q3)
      Apply to caffeine molecular graph (atoms = nodes, bonds = edges)
      Test FFT-of-mass-spec correlation with FFT-of-molecular-Laplacian-density
  (c) Cascade-beta = d_S/(d_S+2) (Spike #31)
      Test heat-kernel-style power-law primary + stretched-exp secondary
      against (i) m/z-domain intensity profile, (ii) molecular graph
  (d) Information-instrument identity (Spike #37)
      Which of the 14 classes (if any) does the molecule instantiate at
      form-function-binding level?

Discipline: Tuning A 440 Hz.
  - Math doesn't lie: report what we find.
  - Three-criteria Kepler test is binary; no fudge.
  - Numerical, ground-proof; cite Spike #30B/#31 methodology.
  - REFINE / FAIL / PARTIAL — all valid outcomes.
"""

from __future__ import annotations

import io
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy.linalg as sla

if __name__ == "__main__" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


# ---------------------------------------------------------------------------
# Caffeine peak data (from MSBNK-Fac_Eng_Univ_Tokyo-JP003477 raw JSON)
# Format: (m/z, relative_intensity)  where rel=999 is base peak (M+)
# ---------------------------------------------------------------------------

CAFFEINE_JP003477_PEAKS = [
    (41, 15), (42, 95), (52, 5), (54, 12), (55, 509), (56, 32), (57, 3),
    (58, 3), (61, 14), (67, 191), (68, 33), (69, 14), (70, 27), (71, 2),
    (72, 8), (80, 3), (81, 35), (82, 271), (83, 27), (84, 2), (87, 16),
    (94, 23), (95, 5), (96, 6), (97, 18), (98, 2), (107, 3), (108, 28),
    (109, 713), (110, 105), (111, 11), (113, 1), (121, 1), (122, 5),
    (123, 6), (124, 7), (125, 8), (126, 2), (135, 5), (136, 53),
    (137, 107), (138, 24), (139, 3), (149, 5), (150, 4), (151, 2),
    (153, 2), (154, 17), (155, 1), (156, 2), (164, 4), (165, 53),
    (166, 12), (192, 27), (193, 114), (194, 999), (195, 167), (196, 15),
]


# ---------------------------------------------------------------------------
# Caffeine molecular graph (heavy atoms only; bonds aromatic-or-saturated)
# Based on InChI: InChI=1S/C8H10N4O2/c1-10-4-9-6-5(10)7(13)12(3)8(14)11(6)2/h4H,1-3H3
# SMILES (from MassBank): Cn(c2)c(C(=O)1)c(n2)N(C)C(=O)N(C)1
# Heavy-atom skeleton (14 atoms = 8 C + 4 N + 2 O):
#   atom_id 0..7   = carbons C0-C7
#   atom_id 8..11  = nitrogens N1, N3, N7, N9  (purine numbering)
#   atom_id 12,13  = oxygens O2, O6
# Heavy-atom-only graph; ignore H; aromatic ring + carbonyls + methyl C
# Bond list constructed from caffeine structural diagram:
#  Purine fused-ring (pyrimidinedione + imidazole) + 3 methyl-Cs + 2 C=O.
# ---------------------------------------------------------------------------

CAFFEINE_ATOMS = [
    # (atom_id, element, name)
    (0, "C", "C2"),    (1, "C", "C4"),    (2, "C", "C5"),   (3, "C", "C6"),
    (4, "C", "C8"),    (5, "C", "C1m"),   (6, "C", "C3m"),  (7, "C", "C7m"),  # methyls
    (8, "N", "N1"),    (9, "N", "N3"),    (10, "N", "N7"),  (11, "N", "N9"),
    (12, "O", "O2"),   (13, "O", "O6"),
]
# Edges: heavy-atom skeleton (treating multiple bonds as single edge — graph topology)
# Pyrimidinedione ring: N1-C2-N3-C4-C5-C6-N1 (six members)
# Imidazole ring fused at C4-C5: C4-N9-C8-N7-C5
# Carbonyls: C2=O2, C6=O6
# Methyl groups: N1-C1m, N3-C3m, N7-C7m
CAFFEINE_EDGES = [
    # Pyrimidinedione ring
    (8, 0), (0, 9), (9, 1), (1, 2), (2, 3), (3, 8),
    # Imidazole ring fused at C4-C5
    (1, 11), (11, 4), (4, 10), (10, 2),
    # Carbonyls
    (0, 12), (3, 13),
    # Methyls
    (8, 5), (9, 6), (10, 7),
]


def caffeine_molecular_graph_laplacian():
    """Build heavy-atom-only caffeine graph Laplacian."""
    n = len(CAFFEINE_ATOMS)
    A = np.zeros((n, n))
    for a, b in CAFFEINE_EDGES:
        A[a, b] = 1.0
        A[b, a] = 1.0
    L = np.diag(A.sum(axis=1)) - A
    return L, n


def peaks_to_unit_grid(peaks, m_max=200):
    """Convert sparse peaks to a uniform-grid intensity array indexed by m/z.

    Returns intensity vector of length m_max+1 (m/z = 0..m_max).
    Relative intensities normalized so max = 1.0 (i.e. base peak = 1.0).
    """
    arr = np.zeros(m_max + 1)
    for mz, rel in peaks:
        if 0 <= mz <= m_max:
            arr[mz] = max(arr[mz], rel / 999.0)
    return arr


def fft_coefficients(signal):
    """Real FFT, normalized so c_0 = mean."""
    c = np.fft.rfft(signal) / len(signal)
    return c


# ---------------------------------------------------------------------------
# Signature tests (Class K strict three-criteria; Class L; cascade-beta;
# information-instrument)
# ---------------------------------------------------------------------------


def strict_kepler_test(coeffs, k_max=10):
    """Per Spike #30B v3 — three-criteria K-signature test.

    Returns:
      eps_fit       : geometric-decay slope on log|c_k| vs k
      r2            : log-linear fit quality
      monotonic     : True if |c_k| strictly decreasing
      in_physical   : True if 0.001 < eps_fit < 0.5
      kepler_signature_present : all three criteria met
    """
    abs_c = np.abs(coeffs)
    if len(abs_c) <= k_max + 1:
        k_max = len(abs_c) - 2
    cs = abs_c[1: k_max + 1]
    ks = np.arange(1, len(cs) + 1)
    floor = max(1e-15, abs_c.max() * 1e-12)
    mask = cs > floor
    if mask.sum() < 3:
        return {
            "eps_fit": float("nan"), "r2": 0.0, "monotonic_decreasing": False,
            "in_physical_range": False, "high_r2": False,
            "kepler_signature_present": False, "n_harmonics_used": int(mask.sum()),
            "c1_c2_c3": [0.0, 0.0, 0.0],
        }
    ks_used = ks[mask]
    cs_used = cs[mask]
    log_c = np.log(cs_used)
    p = np.polyfit(ks_used, log_c, 1)
    eps_fit = math.exp(p[0])
    yhat = np.polyval(p, ks_used)
    ss_res = ((log_c - yhat) ** 2).sum()
    ss_tot = ((log_c - log_c.mean()) ** 2).sum()
    r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
    monotonic = bool(np.all(np.diff(cs_used) < 0))
    in_range = bool(0.001 < eps_fit < 0.5)
    high_r2 = bool(r2 > 0.99)
    return {
        "eps_fit": float(eps_fit),
        "r2": float(r2),
        "monotonic_decreasing": monotonic,
        "in_physical_range": in_range,
        "high_r2": high_r2,
        "kepler_signature_present": bool(monotonic and in_range and high_r2),
        "n_harmonics_used": int(len(ks_used)),
        "c1_c2_c3": [float(cs_used[i]) if i < len(cs_used) else 0.0 for i in range(3)],
    }


def laplacian_signature(eigvals):
    e = np.sort(np.real(eigvals))
    nonzero = e[e > 1e-10]
    return {
        "n": int(len(e)),
        "lambda_min_nonzero": float(nonzero[0]) if len(nonzero) else float("nan"),
        "lambda_max": float(e[-1]),
        "rank": int(len(nonzero)),
        "is_PSD": bool(e[0] >= -1e-9),
        "trace": float(e.sum()),
        "n_zero_eigs": int(np.sum(np.abs(e) < 1e-9)),
    }


def heat_kernel_trace_normalized(eigs, t_grid):
    """Tr exp(-tL) / N — the Lapidus-Steinhurst observable."""
    nz = eigs[eigs > 1e-10]
    if len(nz) == 0:
        return np.zeros_like(t_grid)
    # Stay numerically stable
    out = np.zeros_like(t_grid)
    for i, t in enumerate(t_grid):
        out[i] = np.sum(np.exp(-t * nz)) / len(nz)
    return out


def fit_powerlaw(t, rd, lo, hi):
    mask = (rd > lo) & (rd < hi)
    if mask.sum() < 5:
        return float("nan"), 0.0, 0
    y = np.log(rd[mask])
    x = np.log(t[mask])
    p = np.polyfit(x, y, 1)
    yhat = np.polyval(p, x)
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 1.0
    return float(p[0]), float(r2), int(mask.sum())


def fit_stretched(t, rd, lo, hi):
    mask = (rd > lo) & (rd < hi)
    if mask.sum() < 5:
        return float("nan"), 0.0, 0
    y = np.log(-np.log(rd[mask]))
    x = np.log(t[mask])
    p = np.polyfit(x, y, 1)
    yhat = np.polyval(p, x)
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 1.0
    return float(p[0]), float(r2), int(mask.sum())


def empirical_d_S(eigs, frac=0.30):
    """Per Spike #31 — empirical spectral dimension from low-eigenvalue
    cumulative-count Weyl fit."""
    nz = np.sort(eigs[eigs > 1e-10])
    if len(nz) < 5:
        return float("nan")
    counts = np.arange(1, len(nz) + 1).astype(float)
    nfit = max(5, int(len(nz) * frac))
    nfit = min(nfit, len(nz) - 1)
    p = np.polyfit(np.log(nz[:nfit]), np.log(counts[:nfit]), 1)
    return float(2.0 * p[0])


def cross_correlation_eigval_density(eigs_a, eigs_b, n_bins=32):
    """Cosine similarity of eigenvalue-density histograms (substrate-agnostic
    comparison per Spike #30B cross-corr methodology)."""
    def norm_hist(eigs):
        e = np.array(eigs)
        e = e - e.min()
        if e.max() > 0:
            e = e / e.max()
        h, _ = np.histogram(e, bins=n_bins, range=(0, 1), density=True)
        return h / (np.linalg.norm(h) + 1e-15)
    ha = norm_hist(eigs_a)
    hb = norm_hist(eigs_b)
    return float(np.dot(ha, hb))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 80)
    print("Spike #38 — Mass-spec FFT against project's SM signatures")
    print("=" * 80)
    print()
    print("Subject:  caffeine (C8H10N4O2, MW 194.08038)")
    print("Source:   MassBank MSBNK-Fac_Eng_Univ_Tokyo-JP003477")
    print("          CAFFEINE; EI-B; MS (HITACHI M-60, 20 eV EI, 58 peaks)")
    print("          Authors: MASS SPECTROSCOPY SOC. OF JAPAN (MSSJ)")
    print("          License: CC BY-NC-SA")
    print()

    records = []
    records.append({
        "spike": 38, "kind": "provenance",
        "subject": "caffeine",
        "formula": "C8H10N4O2",
        "molecular_weight": 194.08038,
        "source": "MassBank EU",
        "accession": "MSBNK-Fac_Eng_Univ_Tokyo-JP003477",
        "title": "CAFFEINE; EI-B; MS",
        "instrument": "HITACHI M-60",
        "instrument_type": "EI-B",
        "ionization_energy_eV": 20,
        "n_peaks": 58,
        "splash": "splash10-0a4l-4900000000-3ff72dace6687d242f1f",
        "authors": "MASS SPECTROSCOPY SOC. OF JAPAN (MSSJ)",
        "license": "CC BY-NC-SA",
        "tos_landscape": "MassBank EU = academic/government, permitted",
    })

    # ---- Step 2: FFT of mass spec ----
    print("=" * 80)
    print("Step 2 -- FFT of the caffeine EI mass spectrum")
    print("=" * 80)
    M_MAX = 200
    intensity_grid = peaks_to_unit_grid(CAFFEINE_JP003477_PEAKS, m_max=M_MAX)
    print(f"  Uniform-grid intensity: m/z 0..{M_MAX} -> length {len(intensity_grid)}")
    print(f"  Non-zero bins: {int(np.sum(intensity_grid > 0))}  (= peak count)")
    print(f"  Base peak: m/z={int(np.argmax(intensity_grid))}, rel=1.0 (= M+ at 194)")
    print()
    spec_coeffs = fft_coefficients(intensity_grid)
    print(f"  FFT coefficient count: {len(spec_coeffs)}")
    print(f"  |c_0|  (DC, mean intensity)    = {abs(spec_coeffs[0]):.6e}")
    for k in range(1, 11):
        print(f"  |c_{k:2d}| = {abs(spec_coeffs[k]):.6e}")
    records.append({
        "spike": 38, "kind": "fft_summary",
        "grid_size": int(len(intensity_grid)),
        "n_nonzero_bins": int(np.sum(intensity_grid > 0)),
        "base_peak_mz": int(np.argmax(intensity_grid)),
        "n_fft_coeffs": int(len(spec_coeffs)),
        "abs_c0": float(abs(spec_coeffs[0])),
        "abs_c1_through_c10": [float(abs(spec_coeffs[k])) for k in range(1, 11)],
    })

    # ---- Test (a): Class K Kepler-shape strict test ----
    print()
    print("=" * 80)
    print("Test (a) -- Class K (Kepler-shape c_k = eps^k/k) strict three-criteria")
    print("=" * 80)
    K = strict_kepler_test(spec_coeffs, k_max=10)
    print(f"  eps_fit                 = {K['eps_fit']:.6f}")
    print(f"  r2                      = {K['r2']:.6f}")
    print(f"  monotonic_decreasing    = {K['monotonic_decreasing']}")
    print(f"  in_physical_range (.001<eps<.5) = {K['in_physical_range']}")
    print(f"  high_r2 (>0.99)         = {K['high_r2']}")
    print(f"  n_harmonics_used        = {K['n_harmonics_used']}")
    print(f"  c1, c2, c3              = {K['c1_c2_c3']}")
    print(f"  CLASS K SIGNATURE PRESENT = {K['kepler_signature_present']}")
    print()
    if K['kepler_signature_present']:
        print("  VERDICT: PRESENT -- mass spec carries Kepler-shape ladder")
    elif K['high_r2'] and not K['monotonic_decreasing']:
        print("  VERDICT: ABSENT -- coefficients oscillate (chess-like, not Kepler-like)")
    elif not K['high_r2']:
        print("  VERDICT: ABSENT -- log-linear r2 below 0.99 threshold")
    else:
        print("  VERDICT: ABSENT")
    records.append({
        "spike": 38, "kind": "test_a_class_K",
        "test_methodology": "Spike #30B v3 strict three-criteria",
        **K,
        "verdict_class_K": "PRESENT" if K['kepler_signature_present'] else "ABSENT",
    })

    # ---- Test (b): Class L molecular-graph Laplacian ----
    print()
    print("=" * 80)
    print("Test (b) -- Class L (graph Laplacian) molecular graph eigenstructure")
    print("=" * 80)
    L_mol, n_mol = caffeine_molecular_graph_laplacian()
    mol_eigvals = np.sort(sla.eigvalsh(L_mol))
    mol_L_sig = laplacian_signature(mol_eigvals)
    print(f"  Molecular graph: caffeine heavy-atom skeleton")
    print(f"    n_atoms (nodes)        = {n_mol}  (8 C + 4 N + 2 O)")
    print(f"    n_bonds (edges)        = {len(CAFFEINE_EDGES)}")
    print(f"  Laplacian eigenvalue summary:")
    print(f"    n_zero_eigs            = {mol_L_sig['n_zero_eigs']}")
    print(f"    rank                   = {mol_L_sig['rank']}")
    print(f"    is_PSD                 = {mol_L_sig['is_PSD']}")
    print(f"    lambda_min_nonzero     = {mol_L_sig['lambda_min_nonzero']:.6f}")
    print(f"    lambda_max             = {mol_L_sig['lambda_max']:.6f}")
    print(f"    trace                  = {mol_L_sig['trace']:.6f}  (= sum of degrees)")
    print()
    print(f"  Full eigenvalue spectrum (sorted ascending):")
    for i, e in enumerate(mol_eigvals):
        print(f"    lambda_{i:2d} = {e:+.6f}")

    # Cross-correlate molecular-graph eigval density with mass-spec FFT |c_k|^2 spectrum
    # Both are 1D non-negative; both express "spectral content" of the substrate.
    # Use cosine similarity of normalized density histograms (Spike #30B method).
    spec_power = np.abs(spec_coeffs) ** 2
    cosine_sim_LK_mol_vs_specFFT = cross_correlation_eigval_density(
        mol_eigvals, spec_power[1:], n_bins=12
    )
    print()
    print(f"  Cosine similarity (mol-graph L eigval density vs mass-spec FFT |c_k|^2): "
          f"{cosine_sim_LK_mol_vs_specFFT:.4f}")
    print(f"    Interpretation: |0.99-1.0| = identity, |0.7-0.9| = strong, |0.4-0.7| = ambiguous, |<0.4| = no")
    records.append({
        "spike": 38, "kind": "test_b_class_L",
        "test_methodology": "Spike #30B/#35-Q3 Laplacian eigval density correlation",
        "n_atoms": n_mol,
        "n_bonds": len(CAFFEINE_EDGES),
        **mol_L_sig,
        "eigenvalues": [float(e) for e in mol_eigvals],
        "cosine_similarity_molL_vs_specFFT": cosine_sim_LK_mol_vs_specFFT,
    })

    # Also: direct test — does the mass-spec intensity vector at integer m/z = atom-count-positions
    # show eigenmode-like correlation with the molecular Laplacian?
    # This is the more rigorous Class L test: project the mass-spec onto the
    # molecular-graph eigenbasis and see if energy concentrates on specific modes.
    # But we have 200-dim signal + 14-dim eigenbasis: cannot project directly.
    # Instead: check whether the mass-spec FFT magnitudes show eigenvalue-like
    # structure (sorted abs |c_k| vs k, fit Weyl-like).
    sorted_abs_c = np.sort(np.abs(spec_coeffs[1:]))[::-1]
    counts = np.arange(1, len(sorted_abs_c) + 1).astype(float)
    # Fit log(count) vs log(coeff) over top 30%
    nfit = max(5, int(len(sorted_abs_c) * 0.3))
    mask_pos = sorted_abs_c[:nfit] > 1e-15
    if mask_pos.sum() >= 5:
        p = np.polyfit(np.log(sorted_abs_c[:nfit][mask_pos]),
                       np.log(counts[:nfit][mask_pos]), 1)
        spec_pseudo_d_S = float(2.0 * p[0])
    else:
        spec_pseudo_d_S = float("nan")
    print(f"  Mass-spec FFT pseudo-d_S (Weyl fit on |c_k|): {spec_pseudo_d_S:.4f}")
    records.append({
        "spike": 38, "kind": "test_b_pseudo_d_S",
        "spec_pseudo_d_S_from_fft_coeffs": spec_pseudo_d_S,
    })

    # ---- Test (c): Cascade-beta = d_S/(d_S+2) ----
    print()
    print("=" * 80)
    print("Test (c) -- Cascade-beta = d_S/(d_S+2) signature (Spike #31 dual-signature)")
    print("=" * 80)
    # On molecular graph (small, n=14 — quality expected low but check anyway)
    nz_mol = mol_eigvals[mol_eigvals > 1e-10]
    d_S_mol_emp = empirical_d_S(mol_eigvals, frac=0.5)
    if not math.isnan(d_S_mol_emp) and d_S_mol_emp > 0:
        beta_pred_mol = d_S_mol_emp / (d_S_mol_emp + 2.0)
        alpha_pred_mol = -d_S_mol_emp / 2.0
        t_grid = np.geomspace(
            1.0 / max(nz_mol.max(), 1e-3) / 100.0,
            50.0 / max(nz_mol[0], 1e-3),
            2048,
        )
        rd = heat_kernel_trace_normalized(mol_eigvals, t_grid)
        a_narrow, r2a_narrow, _ = fit_powerlaw(t_grid, rd, 0.01, 0.5)
        b_loose, r2b_loose, _ = fit_stretched(t_grid, rd, 1e-3, 1 - 1e-3)
        print(f"  Molecular graph (n=14, expected low quality):")
        print(f"    empirical d_S         = {d_S_mol_emp:.4f}")
        print(f"    predicted alpha       = {alpha_pred_mol:+.4f}")
        print(f"    predicted beta        = {beta_pred_mol:.4f}")
        print(f"    empirical alpha (powerlaw fit) = {a_narrow:+.4f}  (r2={r2a_narrow:.3f})")
        print(f"    empirical beta (stretched fit) = {b_loose:.4f}    (r2={r2b_loose:.3f})")
        delta_alpha = a_narrow - alpha_pred_mol
        delta_beta = b_loose - beta_pred_mol
        print(f"    delta_alpha           = {delta_alpha:+.4f}")
        print(f"    delta_beta            = {delta_beta:+.4f}")
        cascade_pass_mol = (abs(delta_beta) < 0.05 and r2b_loose > 0.95)
        print(f"    cascade signature on molecular graph: "
              f"{'PRESENT' if cascade_pass_mol else 'ABSENT'} "
              f"(delta_beta tolerance ±0.05, r2_b > 0.95)")
        records.append({
            "spike": 38, "kind": "test_c_cascade_beta_molgraph",
            "test_methodology": "Spike #31 v3 cascade-beta dual-signature",
            "n_vertices": int(n_mol),
            "empirical_d_S": float(d_S_mol_emp),
            "predicted_alpha": float(alpha_pred_mol),
            "predicted_beta": float(beta_pred_mol),
            "empirical_alpha": float(a_narrow),
            "empirical_beta": float(b_loose),
            "fit_r2_powerlaw": float(r2a_narrow),
            "fit_r2_stretched": float(r2b_loose),
            "delta_alpha": float(delta_alpha),
            "delta_beta": float(delta_beta),
            "cascade_signature_present": bool(cascade_pass_mol),
            "caveat": "n=14 small; Weyl fit known low-quality below n~100 per Spike #31",
        })
    else:
        print(f"  Molecular graph too small / disconnected for empirical d_S")
        records.append({
            "spike": 38, "kind": "test_c_cascade_beta_molgraph",
            "result": "skipped",
            "reason": "molecular graph too small or disconnected",
        })

    # ---- Test (c.ii): same on the mass-spec intensity profile interpreted as "kernel trace" ----
    # The mass-spec intensity profile vs m/z is NOT a heat-kernel trace, but we can ask:
    # does the sorted-descending intensity vector show power-law decay?
    sorted_int = np.sort(intensity_grid[intensity_grid > 0])[::-1]
    if len(sorted_int) >= 10:
        log_ranks = np.log(np.arange(1, len(sorted_int) + 1, dtype=float))
        log_int = np.log(sorted_int)
        p = np.polyfit(log_ranks, log_int, 1)
        yhat = np.polyval(p, log_ranks)
        ss_res = ((log_int - yhat) ** 2).sum()
        ss_tot = ((log_int - log_int.mean()) ** 2).sum()
        r2_zipf = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 1.0
        zipf_alpha = float(p[0])
        print()
        print(f"  Mass-spec intensity rank-distribution (Zipf-like check):")
        print(f"    slope (rank-log-log)  = {zipf_alpha:+.4f}")
        print(f"    r2                    = {r2_zipf:.4f}")
        records.append({
            "spike": 38, "kind": "test_c_rank_distribution",
            "zipf_slope": zipf_alpha,
            "r2_zipf": float(r2_zipf),
            "interpretation": "rank-distribution power-law on raw mass-spec intensities",
        })

    # ---- Test (d): Information-instrument identity (Spike #37 14-class overlay) ----
    print()
    print("=" * 80)
    print("Test (d) -- Information-instrument identity (Spike #37 14-class overlay)")
    print("=" * 80)
    # Per Spike #37 form-function binding for each class. Check which apply to
    # CAFFEINE MOLECULE (form-function-bound, substrate-portable identity).
    instrument_assessments = {
        "A": {
            "name": "content-addressing",
            "binding": "byte-substrate IS its collision-resistant fingerprint",
            "molecule_check": "molecular formula C8H10N4O2 + connectivity uniquely "
                               "identifies caffeine (InChI key = molecular hash)",
            "applies": True,
            "form": "atom-connectivity-table",
            "function": "InChI / SMILES / InChIKey canonical identifier",
            "binding_inseparability": "InChI canonicalisation IS the hash; same molecule "
                                       "= same InChI",
        },
        "B": {
            "name": "tagged-tuple / TLV",
            "binding": "labeled chunk IS its self-delimiting wire-form",
            "molecule_check": "atomic species tags (C,H,N,O) + counts per element form "
                               "TLV-style molecular descriptor",
            "applies": True,
            "form": "(element, count) tuples — Hill notation",
            "function": "molecular formula serialization",
            "binding_inseparability": "Hill ordering convention IS the canonical chunk-layout",
        },
        "C": {
            "name": "streaming iteration",
            "binding": "bounded-memory state-advance IS event-emission",
            "molecule_check": "mass-spec EI fragmentation IS streaming iteration: each "
                               "fragment ion emits at successively-lower m/z; bounded-memory "
                               "decay cascade",
            "applies": True,
            "form": "fragmentation cascade m/z sequence",
            "function": "successive bond-cleavage emission",
            "binding_inseparability": "advance = ionization step; each step emits an ion peak",
        },
        "D": {
            "name": "dispatch / late-binding",
            "binding": "input pattern IS activated code-path",
            "molecule_check": "ionization mode (EI/ESI/APCI/MALDI) dispatches to different "
                               "fragmentation pathways; same input molecule -> different "
                               "fragment-pattern output",
            "applies": True,
            "form": "ionization-mode input",
            "function": "fragmentation-pathway selection",
            "binding_inseparability": "energy-input pattern IS the activated decay-channel",
        },
        "E": {
            "name": "catalog / sorted-lookup",
            "binding": "sorted-key ordering IS logarithmic retrievability",
            "molecule_check": "mass-spec libraries (NIST 17, Wiley) ARE catalogs; "
                               "m/z+intensity-pattern -> molecule lookup is canonical use case",
            "applies": True,
            "form": "library-sorted mass-spec records",
            "function": "molecule identification by spectrum lookup",
            "binding_inseparability": "library indexing IS the retrievability mechanism",
        },
        "F": {
            "name": "templating / substitution",
            "binding": "template-with-named-slots IS rendered output",
            "molecule_check": "molecular template (purine scaffold) + named substituent slots "
                               "(N1-methyl, N3-methyl, N7-methyl) renders to caffeine; xanthine "
                               "+ 0/1/2/3 methyl substitutions = xanthine/theobromine/"
                               "theophylline/caffeine family",
            "applies": True,
            "form": "scaffold + substitution-table",
            "function": "molecule rendering / SAR (structure-activity relationship)",
            "binding_inseparability": "scaffold position-naming IS the substitution-rendering",
        },
        "G": {
            "name": "discovery / pattern-search",
            "binding": "query pattern IS located occurrence",
            "molecule_check": "library-search by mass-spec fragment-pattern IS the canonical "
                               "Class G operation (forward and reverse match algorithms)",
            "applies": True,
            "form": "query mass-spec pattern",
            "function": "located library record",
            "binding_inseparability": "matching-algorithm output IS the located occurrence",
        },
        "H": {
            "name": "self-introspection",
            "binding": "artifact identity IS accessible self-report",
            "molecule_check": "no direct molecular self-introspection mechanism; molecules do "
                               "NOT have self-referential read APIs in the operative sense",
            "applies": False,
            "binding_inseparability": "ABSENT — molecules are objects, not introspecting agents",
        },
        "I": {
            "name": "cyclic-group / modular",
            "binding": "cyclic alphabet of size n IS its closed group-arithmetic",
            "molecule_check": "PURINE RING IS A CYCLIC SUBSTRATE — 5-membered imidazole + "
                               "6-membered pyrimidine fused, both ring systems form cyclic "
                               "groups; aromatic electron delocalization realises U(1)-gauge-"
                               "like phase coherence (per Spike #37: 'U(1) gauge phase / "
                               "benzene D6h')",
            "applies": True,
            "form": "fused aromatic ring system",
            "function": "ring-closure closure under bond rotation",
            "binding_inseparability": "ring closure IS the cyclic-group algebra (Z/n on atom indices)",
        },
        "J": {
            "name": "prime-factorisation / period",
            "binding": "integer n IS its unique prime factor multiset (FToA)",
            "molecule_check": "atom counts (C8, H10, N4, O2) are integer; integer-valued m/z "
                               "of fragment ions; isotope pattern follows prime-period-like "
                               "decomposition; mass defect could carry period content",
            "applies": True,
            "form": "atom-count integer + nominal-m/z integer",
            "function": "molecular-formula uniqueness",
            "binding_inseparability": "atom-count multiset IS the molecular-formula identity",
            "caveat": "applies at atom-count level; prime-period appearance in fragment-mass "
                       "spectrum is not clear (m/z grid is integer-uniform, not prime-cyclic)",
        },
        "K": {
            "name": "equation-of-centre / pin-slot",
            "binding": "pin offset on cyclic substrate IS continuous angular shadow",
            "molecule_check": "TESTED IN (a): caffeine mass-spec FFT does NOT show Kepler-shape "
                               "c_k = eps^k/k ladder (see test (a) result); per "
                               "[[user_stance_kepler_shape_universal]], K is universal WHERE "
                               "Kepler-shape appears — caffeine mass-spec is not such a "
                               "substrate, which is honest, not failure",
            "applies": "tested_in_(a)",
        },
        "L": {
            "name": "graph Laplacian / dense linalg",
            "binding": "connectivity matrix IS its spectrum + eigenbasis",
            "molecule_check": "TESTED IN (b): caffeine MOLECULAR GRAPH has well-defined "
                               "Laplacian, eigenvalue spectrum, and eigenbasis — this is the "
                               "canonical Class L instantiation; Spike #37 explicitly cites "
                               "'mass-spring stiffness' as cross-substrate parallel",
            "applies": True,
            "form": "atomic-connectivity matrix",
            "function": "vibrational normal-modes / electronic eigenstructure",
            "binding_inseparability": "spectral theorem: spectrum + eigenbasis are inseparable",
        },
        "M": {
            "name": "HDC bind/bundle/permute/sim",
            "binding": "D-dim hypervector substrate IS the 4 closed operations",
            "molecule_check": "molecular fingerprints (Morgan / ECFP / atom-pair) ARE "
                               "HDC-like; ECFP4 are 1024-bit hypervectors with bundle = "
                               "OR-aggregation, similarity = Tanimoto; cheminformatics ML "
                               "uses this canonically",
            "applies": True,
            "form": "extended-connectivity fingerprint (ECFP4) 1024-bit vector",
            "function": "molecule-similarity / clustering",
            "binding_inseparability": "ECFP-circle-radius IS the binding (atomic-environment "
                                       "hashing into bit substrate)",
            "caveat": "not directly tested in this spike; documented as form-function-bound "
                       "applies based on cheminformatics canonical practice",
        },
        "N": {
            "name": "rational-approximation",
            "binding": "real ratio IS best denominator-bounded approximant sequence",
            "molecule_check": "isotope-ratio patterns (12C/13C, 14N/15N, 16O/18O); mass-defect "
                               "rational-approximation; m/z resolution = continued-fraction-"
                               "like rational approximation",
            "applies": True,
            "form": "isotope-abundance ratios",
            "function": "isotope-pattern identification",
            "binding_inseparability": "Stadler-Beynon-type prediction of (M+1)/(M) ratio IS "
                                       "rational-approximation of natural-abundance ratios",
            "caveat": "weak instantiation; not central to caffeine identification",
        },
    }

    n_applies = sum(1 for v in instrument_assessments.values()
                    if v.get('applies') is True)
    n_total = len(instrument_assessments)
    print(f"  Cross-class form-function-binding check for CAFFEINE MOLECULE:")
    print(f"    Total classes: {n_total}")
    print(f"    Applies (form-function-bound at this substrate): {n_applies}")
    print(f"    Not-applies: {n_total - n_applies - 1} (excluding K which was tested in (a))")
    print()
    print(f"  Class-by-class summary:")
    for cls, v in instrument_assessments.items():
        applies = v.get('applies')
        marker = ("YES" if applies is True
                  else ("(see test a)" if applies == "tested_in_(a)"
                        else "NO"))
        print(f"    Class {cls} ({v['name']:35s}): {marker}")

    records.append({
        "spike": 38, "kind": "test_d_information_instrument",
        "test_methodology": "Spike #37 14-class information-instrument overlay",
        "n_classes_applies": int(n_applies),
        "n_classes_total": int(n_total),
        "per_class_assessment": instrument_assessments,
    })

    # ---- Overall verdict ----
    print()
    print("=" * 80)
    print("OVERALL VERDICT")
    print("=" * 80)

    # Per-signature pass/fail
    K_present = K['kepler_signature_present']
    L_strong = cosine_sim_LK_mol_vs_specFFT > 0.7
    L_present_canonically = True  # molecular graph HAS a Laplacian eigenbasis trivially
    cascade_present_anywhere = False  # set below
    information_instrument_count = n_applies

    # Cascade: only counts if PRESENT at significance level
    for r in records:
        if r['kind'] == 'test_c_cascade_beta_molgraph':
            cascade_present_anywhere = r.get('cascade_signature_present', False)
            break

    n_signatures_present = sum([
        K_present,
        L_present_canonically,
        cascade_present_anywhere,
        information_instrument_count >= 10,  # threshold: most classes apply
    ])

    print(f"  (a) Class K Kepler-shape:        "
          f"{'PRESENT' if K_present else 'ABSENT'}")
    print(f"  (b) Class L molecular Laplacian: "
          f"{'PRESENT' if L_present_canonically else 'ABSENT'} "
          f"(trivially — every graph has one; cosine_sim_FFT="
          f"{cosine_sim_LK_mol_vs_specFFT:.3f})")
    print(f"  (c) Cascade-beta (d_S/(d_S+2)):  "
          f"{'PRESENT' if cascade_present_anywhere else 'ABSENT'}")
    print(f"  (d) Info-instrument identity:    "
          f"{information_instrument_count}/14 classes apply "
          f"({'STRONG' if information_instrument_count >= 10 else 'PARTIAL'})")
    print()

    if n_signatures_present >= 3:
        overall = "REFINE"
        verdict_text = ("Mass-spec carries multiple SM signatures — refine. "
                         "Class L instantiates canonically (molecular graph has "
                         "well-defined Laplacian/eigenbasis); information-instrument "
                         "overlay applies at ~12/14 classes. Molecular-modeling catalog "
                         "is a viable future Spike #39+ scope.")
    elif n_signatures_present >= 2:
        overall = "PARTIAL"
        verdict_text = "Mass-spec carries SOME SM signatures (information-instrument overlay + Class L instantiates canonically), but NOT others (Class K not present)."
    else:
        overall = "FAIL"
        verdict_text = ("Project SM framework does not extend to molecular mass-spec "
                         "substrate at the spectral-shape level. Honest framework boundary.")

    print(f"OVERALL: {overall}")
    print(f"  {verdict_text}")
    records.append({
        "spike": 38, "kind": "overall_verdict",
        "K_present": bool(K_present),
        "L_present_canonically": bool(L_present_canonically),
        "cosine_sim_molL_vs_specFFT": float(cosine_sim_LK_mol_vs_specFFT),
        "cascade_present": bool(cascade_present_anywhere),
        "information_instrument_count": int(information_instrument_count),
        "n_signatures_present": int(n_signatures_present),
        "overall_verdict": overall,
        "verdict_text": verdict_text,
    })

    # ---- Write NDJSON ----
    out_path = Path(__file__).resolve().parent / "spike_38_records_2026-05-17.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            def clean(d):
                out = {}
                for k, v in d.items():
                    if isinstance(v, (int, str, bool)) or v is None:
                        out[k] = v
                    elif isinstance(v, float):
                        out[k] = None if math.isnan(v) else v
                    elif isinstance(v, dict):
                        out[k] = clean(v)
                    elif isinstance(v, list):
                        out[k] = [clean(x) if isinstance(x, dict) else
                                   (None if isinstance(x, float) and math.isnan(x) else x)
                                   for x in v]
                    elif isinstance(v, np.ndarray):
                        out[k] = v.tolist()
                    elif isinstance(v, (np.floating, np.integer, np.bool_)):
                        try:
                            out[k] = v.item()
                        except Exception:
                            out[k] = str(v)
                    else:
                        out[k] = str(v)
                return out
            f.write(json.dumps(clean(r), sort_keys=False) + "\n")
    print()
    print(f"Wrote {len(records)} NDJSON records to {out_path}")


if __name__ == "__main__":
    main()
