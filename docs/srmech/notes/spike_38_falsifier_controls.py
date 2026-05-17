"""Spike #38 falsifier: is the cosine_sim(mol_L, spec_FFT) = 0.81 finding
*specific to caffeine* or an artifact?

Run controls:
  (C1) caffeine spec FFT vs caffeine-mol Laplacian  (test result)
  (C2) caffeine spec FFT vs ETHANE (C2H6) Laplacian  (very different mol)
  (C3) caffeine spec FFT vs BENZENE (C6H6) Laplacian  (different but cyclic)
  (C4) caffeine spec FFT vs GLUCOSE (C6H12O6) Laplacian  (similar atom count)
  (C5) caffeine spec FFT vs LINEAR-PATH-n14 Laplacian  (same size, trivial topology)
  (C6) caffeine spec FFT vs RANDOM 14-node 15-edge graph (50 seeds, mean)
  (C7) caffeine spec FFT vs CYCLE-n14 Laplacian  (cyclic, same size)
  (C8) RANDOM mass-spec (Poisson 58-peak) vs caffeine-mol Laplacian (signal check)

If C1 stands out clearly from C2-C8, the finding is caffeine-specific.
If C1 is in the middle of the C2-C8 distribution, the finding is artifact.
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


CAFFEINE_PEAKS = [
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


def peaks_to_grid(peaks, m_max=200):
    arr = np.zeros(m_max + 1)
    for mz, rel in peaks:
        if 0 <= mz <= m_max:
            arr[mz] = max(arr[mz], rel / 999.0)
    return arr


def fft_power(signal):
    c = np.fft.rfft(signal) / len(signal)
    return np.abs(c) ** 2


def laplacian_from_edges(n, edges):
    A = np.zeros((n, n))
    for a, b in edges:
        A[a, b] = 1.0
        A[b, a] = 1.0
    return np.diag(A.sum(axis=1)) - A


def cross_corr(eigs_a, eigs_b, n_bins=12):
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


def caffeine_mol_L():
    # 14 heavy atoms: 8 C + 4 N + 2 O
    edges = [
        (8, 0), (0, 9), (9, 1), (1, 2), (2, 3), (3, 8),
        (1, 11), (11, 4), (4, 10), (10, 2),
        (0, 12), (3, 13),
        (8, 5), (9, 6), (10, 7),
    ]
    return laplacian_from_edges(14, edges)


def ethane_mol_L():
    # C2H6: 2 heavy atoms (just C-C). Tiny.
    edges = [(0, 1)]
    return laplacian_from_edges(2, edges)


def benzene_mol_L():
    # C6H6: cyclic 6 carbons
    edges = [(i, (i + 1) % 6) for i in range(6)]
    return laplacian_from_edges(6, edges)


def glucose_mol_L():
    # C6H12O6: 6 C + 6 O = 12 heavy atoms; cyclic-pyranose form
    # Numbering: C1 C2 C3 C4 C5 O5 (ring) + C6 OH-on-C1/C2/C3/C4/C6
    # Ring: C1-C2-C3-C4-C5-O5-C1; C5-C6; OH on C1,C2,C3,C4,C6
    # Atoms: C1=0 C2=1 C3=2 C4=3 C5=4 O5=5 C6=6 OH1=7 OH2=8 OH3=9 OH4=10 OH6=11
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0),  # ring
        (4, 6),  # C5-C6
        (0, 7), (1, 8), (2, 9), (3, 10), (6, 11),  # OH on C1,C2,C3,C4,C6
    ]
    return laplacian_from_edges(12, edges)


def path_n14_L():
    edges = [(i, i + 1) for i in range(13)]
    return laplacian_from_edges(14, edges)


def cycle_n14_L():
    edges = [(i, (i + 1) % 14) for i in range(14)]
    return laplacian_from_edges(14, edges)


def random_n14_15edges_L(seed):
    rng = np.random.default_rng(seed)
    edges = set()
    while len(edges) < 15:
        a, b = rng.integers(0, 14, size=2)
        if a != b:
            e = (min(int(a), int(b)), max(int(a), int(b)))
            edges.add(e)
    return laplacian_from_edges(14, list(edges))


def random_mass_spec(seed, n_peaks=58, m_max=200):
    rng = np.random.default_rng(seed)
    arr = np.zeros(m_max + 1)
    positions = rng.choice(m_max + 1, size=n_peaks, replace=False)
    intensities = rng.random(n_peaks)
    for p, i in zip(positions, intensities):
        arr[p] = i
    return arr


def main():
    print("=" * 80)
    print("Spike #38 falsifier — is cosine_sim(mol_L, spec_FFT) finding specific?")
    print("=" * 80)
    print()

    # Caffeine mass-spec FFT power
    caf_intensity = peaks_to_grid(CAFFEINE_PEAKS)
    caf_fft_pow = fft_power(caf_intensity)
    print(f"  Caffeine mass-spec FFT power: {len(caf_fft_pow)} coefficients")
    print()

    results = []

    # C1: caffeine vs caffeine
    L_caf = caffeine_mol_L()
    e_caf = sla.eigvalsh(L_caf)
    sim_caf = cross_corr(e_caf, caf_fft_pow[1:])
    print(f"  C1 caffeine_FFT vs caffeine_mol_L     = {sim_caf:.4f}  <- this is the test result")
    results.append(("C1_caffeine_self", sim_caf, 1))

    # C2: caffeine FFT vs ethane (n=2)
    L_eth = ethane_mol_L()
    e_eth = sla.eigvalsh(L_eth)
    sim_eth = cross_corr(e_eth, caf_fft_pow[1:])
    print(f"  C2 caffeine_FFT vs ethane_mol_L (n=2) = {sim_eth:.4f}")
    results.append(("C2_ethane", sim_eth, 2))

    # C3: caffeine FFT vs benzene (n=6)
    L_bz = benzene_mol_L()
    e_bz = sla.eigvalsh(L_bz)
    sim_bz = cross_corr(e_bz, caf_fft_pow[1:])
    print(f"  C3 caffeine_FFT vs benzene_mol_L (n=6) = {sim_bz:.4f}")
    results.append(("C3_benzene", sim_bz, 6))

    # C4: caffeine FFT vs glucose (n=12)
    L_glu = glucose_mol_L()
    e_glu = sla.eigvalsh(L_glu)
    sim_glu = cross_corr(e_glu, caf_fft_pow[1:])
    print(f"  C4 caffeine_FFT vs glucose_mol_L (n=12) = {sim_glu:.4f}")
    results.append(("C4_glucose", sim_glu, 12))

    # C5: caffeine FFT vs path-n14
    L_path = path_n14_L()
    e_path = sla.eigvalsh(L_path)
    sim_path = cross_corr(e_path, caf_fft_pow[1:])
    print(f"  C5 caffeine_FFT vs path_n14_L (n=14)  = {sim_path:.4f}")
    results.append(("C5_path_n14", sim_path, 14))

    # C7: caffeine FFT vs cycle-n14
    L_cyc = cycle_n14_L()
    e_cyc = sla.eigvalsh(L_cyc)
    sim_cyc = cross_corr(e_cyc, caf_fft_pow[1:])
    print(f"  C7 caffeine_FFT vs cycle_n14_L (n=14) = {sim_cyc:.4f}")
    results.append(("C7_cycle_n14", sim_cyc, 14))

    # C6: caffeine FFT vs 50 random 14-node 15-edge graphs
    sim_rnd_list = []
    for seed in range(50):
        try:
            L_rnd = random_n14_15edges_L(seed)
            e_rnd = sla.eigvalsh(L_rnd)
            sim_rnd_list.append(cross_corr(e_rnd, caf_fft_pow[1:]))
        except Exception:
            continue
    sim_rnd_mean = float(np.mean(sim_rnd_list))
    sim_rnd_std = float(np.std(sim_rnd_list))
    sim_rnd_max = float(np.max(sim_rnd_list))
    sim_rnd_min = float(np.min(sim_rnd_list))
    print(f"  C6 caffeine_FFT vs random 14-node graphs (50 seeds):")
    print(f"     mean ± std = {sim_rnd_mean:.4f} ± {sim_rnd_std:.4f}")
    print(f"     min, max   = {sim_rnd_min:.4f}, {sim_rnd_max:.4f}")
    results.append(("C6_random_n14_mean", sim_rnd_mean, 14))
    results.append(("C6_random_n14_max", sim_rnd_max, 14))

    # C8: random mass-spec vs caffeine mol-L (signal control)
    sim_random_spec = []
    for seed in range(50):
        spec = random_mass_spec(seed)
        s_fft = fft_power(spec)
        sim_random_spec.append(cross_corr(e_caf, s_fft[1:]))
    sim_random_spec_mean = float(np.mean(sim_random_spec))
    sim_random_spec_std = float(np.std(sim_random_spec))
    print(f"  C8 random_mass_spec vs caffeine_mol_L (50 seeds):")
    print(f"     mean ± std = {sim_random_spec_mean:.4f} ± {sim_random_spec_std:.4f}")
    results.append(("C8_random_spec_vs_caffeine_L_mean", sim_random_spec_mean, None))

    # ---- Verdict ----
    print()
    print("=" * 80)
    print("FALSIFIER VERDICT")
    print("=" * 80)
    print()
    print(f"  Caffeine-self similarity      = {sim_caf:.4f}")
    print(f"  Random-graph similarity mean  = {sim_rnd_mean:.4f}")
    print(f"  Random-graph similarity max   = {sim_rnd_max:.4f}")
    print(f"  Random-spec similarity mean   = {sim_random_spec_mean:.4f}")
    print()

    is_specific = sim_caf > sim_rnd_max
    above_random_by_sigma = (sim_caf - sim_rnd_mean) / sim_rnd_std if sim_rnd_std > 0 else 0
    is_significant = above_random_by_sigma > 2.0

    print(f"  Is caffeine-self ABOVE all random-graph results?  {is_specific}")
    print(f"  Caffeine-self is {above_random_by_sigma:+.2f} sigma above random mean")
    print(f"  >2 sigma significance?  {is_significant}")
    print()

    if is_specific and is_significant:
        verdict = "SPECIFIC"
        text = ("Caffeine-mol-L vs caffeine-FFT similarity stands out from null distribution. "
                "Finding is substrate-specific, not artifact.")
    elif is_significant:
        verdict = "WEAK_SPECIFIC"
        text = ("Caffeine-self is statistically above mean but some random graphs match. "
                "Modest specificity; not robust.")
    else:
        verdict = "ARTIFACT"
        text = ("Caffeine-self similarity is within range of random-graph background. "
                "0.81 cosine similarity is an artifact of histogram-binning, NOT "
                "evidence of substrate-specific Class L structure.")

    print(f"VERDICT: {verdict}")
    print(f"  {text}")

    # Write NDJSON
    out_path = Path(__file__).resolve().parent / "spike_38_falsifier_records_2026-05-17.ndjson"
    records = [
        {"spike": 38, "kind": "falsifier_caffeine_self", "value": float(sim_caf)},
        {"spike": 38, "kind": "falsifier_ethane", "value": float(sim_eth)},
        {"spike": 38, "kind": "falsifier_benzene", "value": float(sim_bz)},
        {"spike": 38, "kind": "falsifier_glucose", "value": float(sim_glu)},
        {"spike": 38, "kind": "falsifier_path_n14", "value": float(sim_path)},
        {"spike": 38, "kind": "falsifier_cycle_n14", "value": float(sim_cyc)},
        {"spike": 38, "kind": "falsifier_random_n14",
         "mean": sim_rnd_mean, "std": sim_rnd_std,
         "min": sim_rnd_min, "max": sim_rnd_max,
         "n_seeds": len(sim_rnd_list)},
        {"spike": 38, "kind": "falsifier_random_spec_vs_caffeine_L",
         "mean": sim_random_spec_mean, "std": sim_random_spec_std,
         "n_seeds": len(sim_random_spec)},
        {"spike": 38, "kind": "falsifier_verdict",
         "caffeine_self_similarity": float(sim_caf),
         "random_graph_mean": sim_rnd_mean,
         "random_graph_max": sim_rnd_max,
         "is_specific_above_random_max": bool(is_specific),
         "above_random_by_sigma": float(above_random_by_sigma),
         "is_significant_above_2sigma": bool(is_significant),
         "verdict": verdict,
         "verdict_text": text},
    ]
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=False) + "\n")
    print()
    print(f"Wrote {len(records)} NDJSON records to {out_path}")


if __name__ == "__main__":
    main()
