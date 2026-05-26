"""R-RBS-LM-54p — Cluster rank & participation ratio for spin form-iso.

54o falsified the "spin-N maps to cluster-COUNT" prediction (Pope had 1
cluster, same as Milton). But the bottom-eigenvalue GAP RATIOS show
Pope IS more clustered at the very-low-eigvalue end than Milton, just
below the 2% tolerance threshold 54o used.

This partition uses TWO sharper measurements:

  (A) Tight-tolerance cluster count: try multiple tolerances (0.01%,
      0.1%, 1%, 5% of spectrum range) and look for the threshold at
      which Pope shows more clusters than Milton.

  (B) Inverse Participation Ratio (IPR) of bottom-K eigvecs:
        IPR(v) = sum(v_i^4) / (sum(v_i^2))^2
      Higher IPR = more localized (single mode).
      Lower IPR = more delocalized (multiple modes — spin-N≥1 candidate).

  (C) Effective dimension of bottom-K eigvec subspace via the singular-
      value rank of stacked low eigvecs. A degenerate plane (spin-2)
      should give higher effective dimension than a degenerate line
      (spin-1).

Predictions if form-isomorphism real:
  Whitman:    bottom-K eigvecs are sharply distinct (high IPR, high gaps)
  Frankenstein/Plato: distinct ground states (moderate IPR)
  Milton:     bottom-K eigvecs share some delocalization (lower IPR)
  Pope:       bottom-K eigvecs more delocalized (lowest IPR; effective rank > Milton)

If pattern doesn't appear → spin-form mapping fully falsified.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

DOMAINS = {
    "shakespeare":  {"path": "/tmp/shakespeare.txt",                "predicted": "mixed",    "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",              "predicted": "spin-1",   "label": "Milton"},
    "pope_iliad":   {"path": "/tmp/iliad_pope.txt",                 "predicted": "spin-2",   "label": "Pope Iliad"},
    "longfellow":   {"path": "/tmp/longfellow_dante_inferno.txt",   "predicted": "spin-1.5", "label": "Longfellow"},
    "whitman":      {"path": "/tmp/whitman.txt",                    "predicted": "spin-0",   "label": "Whitman"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",               "predicted": "spin-0",   "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",             "predicted": "spin-0",   "label": "Plato"},
    "origin":       {"path": "/tmp/origin_species.txt",             "predicted": "spin-0",   "label": "Origin"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",          "predicted": "spin-0.5", "label": "KJV-NT"},
}

KERNEL_N_EIGVECS = 200
N_BOTTOM_EIGVECS_FOR_IPR = 10

STOPWORDS_EN = set("""
the a an and or but if then else of in on at to for with by from as is are
was were be been being have has had having do does did doing done will
would shall should may might can could not no this that these those it its
they them their there here he she we us our you your i me my mine yours
which what who whom whose where when why how all any some none many much
more most less few several each every both either neither so such only also
than just too very much such etc ie eg via vs per pre post sub super
o which thee thou thy ye us our hath shall said say
""".split())


def tokenize_filtered(text):
    raw = re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", text)
    return [t.lower() for t in raw if t.lower() not in STOPWORDS_EN and len(t) >= 2]


def strip_gutenberg(text):
    s = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    e = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if s: text = text[s.end():]
    if e: text = text[:e.start()]
    return text.strip()


def chunk_text(text, n_chunks=64):
    raw = re.split(r"\n\s*\n+", text)
    out, cur, sz = [], [], 0
    target = max(len(text) // n_chunks, 1000)
    for c in raw:
        cur.append(c); sz += len(c)
        if sz >= target:
            out.append("\n".join(cur)); cur = []; sz = 0
    if cur: out.append("\n".join(cur))
    return out


def build_laplacian(text, n_eigvecs=KERNEL_N_EIGVECS):
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(n_eigvecs, len(freq))
    if N < 8: return None, None, 0
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges = Counter()
    for toks in filt:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i+1, min(i+5, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges[(min(a,b), max(a,b))] += 1
    if not edges: return None, None, 0
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    ev_real = np.array([float(np.real(e)) for e in ev])
    evc_real = np.real(evc).astype(float)
    # Sort eigvals ascending; rearrange eigvecs accordingly
    order = np.argsort(ev_real)
    ev_sorted = ev_real[order]
    evc_sorted = evc_real[:, order]
    return ev_sorted, evc_sorted, len(edges)


def tight_cluster_counts(ev, tolerances_rel):
    """Count clusters of eigenvalues within tolerance, in the bottom 10% of spectrum."""
    if len(ev) < 2: return {t: 0 for t in tolerances_rel}
    spectrum_range = float(ev[-1] - ev[0])
    if spectrum_range == 0: return {t: 0 for t in tolerances_rel}
    low_threshold = ev[0] + 0.10 * spectrum_range
    low_eigs = ev[ev <= low_threshold]
    counts = {}
    for tol in tolerances_rel:
        eps_abs = tol * spectrum_range
        clusters = []
        if len(low_eigs) < 2:
            counts[tol] = 0; continue
        current = [low_eigs[0]]
        for e in low_eigs[1:]:
            if e - current[-1] < eps_abs:
                current.append(e)
            else:
                if len(current) >= 2: clusters.append(current)
                current = [e]
        if len(current) >= 2: clusters.append(current)
        counts[tol] = len(clusters)
    return counts


def inverse_participation_ratio(v):
    """IPR = sum(v_i^4) / (sum(v_i^2))^2. Higher = more localized."""
    v2 = v * v
    s2 = float(v2.sum())
    if s2 == 0: return 0.0
    s4 = float((v2 * v2).sum())
    return s4 / (s2 ** 2)


def effective_rank(evc_subset, threshold=0.01):
    """Effective rank of a set of vectors: number of singular values >
    threshold × max-singular-value."""
    if evc_subset.shape[1] == 0: return 0
    s = np.linalg.svd(evc_subset, compute_uv=False)
    max_s = s.max() if s.max() > 0 else 1.0
    return int(np.sum(s > threshold * max_s))


def main():
    print(f"=== R-RBS-LM-54p — Cluster rank & participation ratio (spin form-iso part 2) ===\n")
    print(f"srmech: {srmech.__version__}")

    print(f"\n--- Building Laplacian + bottom-eigvec analysis per corpus ---")
    tolerances = [0.0001, 0.001, 0.01, 0.05]
    results = []

    for key, info in DOMAINS.items():
        text = strip_gutenberg(Path(info["path"]).read_text(encoding="utf-8", errors="replace"))
        ev, evc, n_edges = build_laplacian(text)
        if ev is None:
            print(f"  [SKIP] {info['label']}: insufficient data")
            continue

        # (A) Tight-tolerance cluster counts
        tcc = tight_cluster_counts(ev, tolerances)

        # Skip the trivial first eigvec (eigenvalue ≈ 0; from Laplacian connectivity)
        # Take eigvecs 1..N_BOTTOM_EIGVECS_FOR_IPR (the actually-low non-trivial ones)
        bottom_eigvecs = evc[:, 1:1 + N_BOTTOM_EIGVECS_FOR_IPR]

        # (B) IPR of each bottom eigvec; average + min (most delocalized)
        iprs = [inverse_participation_ratio(bottom_eigvecs[:, i]) for i in range(bottom_eigvecs.shape[1])]
        avg_ipr = float(np.mean(iprs))
        min_ipr = float(np.min(iprs))

        # (C) Effective rank of bottom-K eigvec subspace
        eff_rank = effective_rank(bottom_eigvecs)

        # (D) Gap-ratio at bottom (eigvals 1-5 spread, normalized)
        spectrum_range = float(ev[-1] - ev[0])
        bottom_5 = ev[1:6]  # skip the trivial 0 eigval
        bottom_5_spread = float((bottom_5[-1] - bottom_5[0]) / spectrum_range) if spectrum_range > 0 else 0

        print(f"\n  {info['label']:<14s} [predicted: {info['predicted']}]")
        print(f"    tight clusters @ {tolerances}: {[tcc[t] for t in tolerances]}")
        print(f"    bottom-{N_BOTTOM_EIGVECS_FOR_IPR} eigvec IPR: avg={avg_ipr:.4f}, min={min_ipr:.4f}")
        print(f"    bottom-{N_BOTTOM_EIGVECS_FOR_IPR} eigvec effective rank (svd): {eff_rank}")
        print(f"    bottom-5 spread (normalized): {bottom_5_spread:.6f}")

        results.append({
            "key": key, "label": info["label"], "predicted": info["predicted"],
            "spectrum_range": spectrum_range,
            "tight_cluster_counts": tcc,
            "ipr_avg": avg_ipr, "ipr_min": min_ipr,
            "effective_rank": eff_rank,
            "bottom_5_spread_normalized": bottom_5_spread,
        })

    # Aggregate by predicted spin
    print(f"\n=== Aggregate by predicted spin-form ===")
    print(f"  {'spin':<10s} {'n':>3s} {'avg IPR':>10s} {'avg eff-rank':>14s} {'avg bot5-spread':>17s}")
    by_spin = {}
    for r in results:
        s = r["predicted"]
        by_spin.setdefault(s, []).append(r)
    spin_order = ["spin-0", "spin-0.5", "spin-1", "spin-1.5", "mixed", "spin-2"]
    for s in spin_order:
        if s not in by_spin: continue
        rs = by_spin[s]
        avg_ipr = float(np.mean([r["ipr_avg"] for r in rs]))
        avg_eff_rank = float(np.mean([r["effective_rank"] for r in rs]))
        avg_bot5_spread = float(np.mean([r["bottom_5_spread_normalized"] for r in rs]))
        print(f"  {s:<10s} {len(rs):>3d} {avg_ipr:>10.4f} {avg_eff_rank:>14.2f} {avg_bot5_spread:>17.6f}")

    # Verdict: did spin-2 show signal NOT visible in cluster-count?
    print(f"\n=== Falsification verdict (cluster rank + IPR) ===")
    pope_r = next((r for r in results if r["key"] == "pope_iliad"), None)
    milton_r = next((r for r in results if r["key"] == "milton"), None)
    whitman_r = next((r for r in results if r["key"] == "whitman"), None)

    if pope_r and milton_r and whitman_r:
        print(f"  Pope IPR (avg):    {pope_r['ipr_avg']:.4f}")
        print(f"  Milton IPR (avg):  {milton_r['ipr_avg']:.4f}")
        print(f"  Whitman IPR (avg): {whitman_r['ipr_avg']:.4f}")
        print(f"  Pope eff-rank:    {pope_r['effective_rank']}")
        print(f"  Milton eff-rank:  {milton_r['effective_rank']}")
        print(f"  Whitman eff-rank: {whitman_r['effective_rank']}")
        print(f"  Pope bot5 spread:    {pope_r['bottom_5_spread_normalized']:.6f}")
        print(f"  Milton bot5 spread:  {milton_r['bottom_5_spread_normalized']:.6f}")
        print(f"  Whitman bot5 spread: {whitman_r['bottom_5_spread_normalized']:.6f}")

        # Test: bot5-spread should be smaller (more clustered) for Pope than Milton, smaller for Milton than Whitman
        if pope_r["bottom_5_spread_normalized"] < milton_r["bottom_5_spread_normalized"] < whitman_r["bottom_5_spread_normalized"]:
            verdict = "FORM-ISOMORPHISM SUPPORTED in bottom-5 eigenvalue spread: Pope < Milton < Whitman (more rules = tighter clustering at the very bottom)"
        elif pope_r["bottom_5_spread_normalized"] < whitman_r["bottom_5_spread_normalized"]:
            verdict = "FORM-ISOMORPHISM PARTIAL: Pope spread < Whitman spread (binary distinction holds; finer mapping mixed)"
        else:
            verdict = "FORM-ISOMORPHISM FURTHER FALSIFIED at bottom-spread level too: no clear ordering"
    else:
        verdict = "INCONCLUSIVE: missing comparison points"

    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54p",
        "results": results,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54p_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
