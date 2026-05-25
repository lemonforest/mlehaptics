"""R-RBS-NN-7 worked example — capacity scan across multiple D values.

Extends R-RBS-NN-2 §7 Demo 6 to multiple D values. For each D, sweeps n
through {3, 9, 33, 65, 129, 257} and measures cleanup margin (min in-bundle
similarity - max out-of-bundle similarity). Identifies the capacity
inflection point where margin crosses zero.

Per Kanerva/Plate theory: cleanup capacity n_max ≈ D / (k · log D), with
k ≈ 5-12 depending on cleanup-quality threshold. R-RBS-NN-2 §7 found
effective k ≈ 5 at D=8192.

Usage:
    PYTHONPATH=docs/srmech/python python3 \
        docs/srmech/rbs_nn_research/worked_example_capacity_scan.py
"""

import math
import sys

sys.path.insert(0, "docs/srmech/python")

from srmech.amsc.hdc import bundle, similarity  # noqa: E402
from srmech.signal_processing.rbs_hdc_instrument import mint_vector  # noqa: E402


D_values = [8192, 16384, 32768, 65536]
n_values = [3, 9, 33, 65, 129, 257]
n_controls = 20  # out-of-bundle controls per scan


def mint_anon(name_idx: int, D: int) -> bytes:
    return mint_vector(f"LoE.token.scan{name_idx:08d}", D=D)


print(f"D values:        {D_values}")
print(f"n values:        {n_values}")
print(f"# of controls:   {n_controls}")
print()
print(f"{'D':>8s}  {'noise floor':>12s}  {'theor. n_max (k=8)':>20s}  "
      f"{'theor. n_max (k=5)':>20s}")
for D in D_values:
    nf = 1.0 / math.sqrt(D)
    n_theor_k8 = int(D / (8 * math.log2(D)))
    n_theor_k5 = int(D / (5 * math.log2(D)))
    print(f"{D:8d}  {nf:12.4f}  {n_theor_k8:20d}  {n_theor_k5:20d}")
print()


# ---- per-D capacity scan -----------------------------------------------
print("=" * 90)
print(f"{'D':>8s}  {'n':>5s}  {'min sim(member)':>16s}  "
      f"{'max sim(non-member)':>20s}  {'margin':>10s}  {'note':>8s}")
print("=" * 90)

results: dict[int, list[tuple[int, float, float, float]]] = {}

for D in D_values:
    results[D] = []
    controls = [mint_anon(10_000_000 + i, D) for i in range(n_controls)]
    for n in n_values:
        members = [mint_anon(i, D) for i in range(n)]
        S = bundle(members)
        sims_in = [similarity(S, v) for v in members]
        sims_out = [similarity(S, c) for c in controls]
        min_in = min(sims_in)
        max_out = max(sims_out)
        margin = min_in - max_out
        note = "OK" if margin > 0.05 else ("MARGINAL" if margin > 0 else "BROKEN")
        print(f"{D:8d}  {n:5d}  {min_in:+16.4f}  {max_out:+20.4f}  "
              f"{margin:+10.4f}  {note:>8s}")
        results[D].append((n, min_in, max_out, margin))
    print("-" * 90)


# ---- scaling-law extraction --------------------------------------------
print("\n=== Empirical capacity inflection (n where margin crosses zero) ===")
print(f"{'D':>8s}  {'inflection n (interpolated)':>30s}  {'effective k':>14s}")
for D in D_values:
    # Find largest n with positive margin, smallest with negative
    margins = [(n, m) for (n, _, _, m) in results[D]]
    pos = [(n, m) for n, m in margins if m > 0]
    neg = [(n, m) for n, m in margins if m <= 0]
    if not neg:
        n_inflection = f">{margins[-1][0]}"
        k_eff_str = "n/a"
    elif not pos:
        n_inflection = f"<{margins[0][0]}"
        k_eff_str = "n/a"
    else:
        # Linear interpolation between last positive and first negative
        n_p, m_p = pos[-1]
        n_n, m_n = neg[0]
        n_inflection_val = n_p + (m_p / (m_p - m_n)) * (n_n - n_p)
        n_inflection = f"{n_inflection_val:.1f}"
        k_eff = D / (n_inflection_val * math.log2(D))
        k_eff_str = f"{k_eff:.2f}"
    print(f"{D:8d}  {n_inflection:>30s}  {k_eff_str:>14s}")


# ---- 1024-byte ephemerides precedent -----------------------------------
print("\n=== Ephemerides precedent (R-RBS-NN-2 §6.4) ===")
print("  v0.1.0 srmech instrument: 52 bodies (3.3 GB JPL DE441 kernel) packed")
print("  into 256 KB ALU-native BIP encoder per ephemerides notebook §1.4.")
print("  At D=8192 (1 KB per body × 256 ≈ 256 KB), capacity question is the")
print("  per-body cleanup margin under the body-interaction bundle pattern,")
print("  not the symbolic-vocabulary cleanup measured here. Different binding")
print("  shape; consistent capacity precedent at the instrument scale.")


# ---- when add D vs when add catalog rows -------------------------------
print("\n=== Grow-without-quantization decision rule ===")
print()
print("  Question 1 — Add D (increase hypervector dimension):")
print("    - Required when cleanup capacity ceiling is reached")
print("    - n_max scales as O(D / log D); doubling D roughly doubles capacity")
print("    - Catalog file size grows linearly with D")
print("    - No content is lost; all existing bindings re-mint losslessly at higher D")
print()
print("  Question 2 — Add catalog rows (add more user-lexicon terms):")
print("    - Required when user adds new vocabulary")
print("    - Content-addressing capacity is unbounded; mint-on-demand works at any D")
print("    - No bundle membership change unless the new term enters a working-memory")
print("      superposition")
print()
print("  The two questions are orthogonal: D controls cleanup-capacity-per-bundle;")
print("  catalog rows control unique-content-vocabulary-size. Grow D for deeper")
print("  bundles; grow catalog rows for broader vocabulary.")
