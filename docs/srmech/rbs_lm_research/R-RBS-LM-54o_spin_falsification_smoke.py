"""R-RBS-LM-54o — Spin-0/1/2 form-isomorphism falsification.

Per user 2026-05-26: "does it seem like our structures, the super
rigid Pope poem rules, and the loosie goosy whitman, touch back on
spin 0/1/2 dilaton/photon/graviton things from our MFO notebook
things or I'm conflating things? if not conflation, try falsification"

The framework reading: spin-N counts orthogonal symmetry-breaking
constraints a field carries. Poetry rule-systems map to orthogonal
compositional-constraint count per unit:
  - Whitman (free verse):     0 inter-line constraints → spin-0 form
  - Milton (blank verse):     1 intra-line constraint (meter) → spin-1 form
  - Pope (heroic couplets):   2 INTER-line constraints (meter + bidirectional rhyme) → spin-2 form

Pope's degeneracy in 54n (line-end kernel HURTS by -0.063) is
*spectral collapse under symmetric coupling* — the same shape as
spin-2 polarization-mode degeneracy under transverse-traceless
constraint.

Falsification test:
  Build Laplacian for each corpus.
  Count "degenerate eigenvalue clusters near 0" — i.e., eigvalues
  within ε of each other and within δ of zero, beyond what a
  random graph of same size + edge density would predict.

  Prediction (if form-isomorphism real):
    Whitman:    0 degenerate clusters
    Frankenstein/Plato (prose): 0
    Milton:     1
    Shakespeare (mixed):  1-2
    Pope:       ≥2

  Falsification (if conflation):
    Pattern doesn't appear; cluster counts uncorrelated with rule-
    density. Just over-density artifact, no structural lesson beyond
    "rigid binding hurts eigvec separation."

We measure degenerate clusters via:
  (a) Spectral gap ratio: eigvals[i+1]/eigvals[i] — large gap means
      clean separation; small gap means degeneracy.
  (b) Random-graph baseline: Wigner semi-circle / Erdős–Rényi
      reference for what a random graph of same N + edge-count would
      produce.
  (c) Count eigenvalues within bottom 5% of spectrum that are within
      ε=2% of each other (compared to random baseline).

Per MFO §VII.6.20 epistemic ceiling: we measure form-isomorphism
between rule-density and spectral-clustering. We do NOT claim Pope's
couplets ARE a spin-2 field. Form same as; substrate not.
"""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

DOMAINS = {
    "shakespeare":  {"path": "/tmp/shakespeare.txt",                "predicted_spin": "mixed",    "rules": "meter + sometimes rhyme", "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",              "predicted_spin": "spin-1",   "rules": "meter only",              "label": "Milton"},
    "pope_iliad":   {"path": "/tmp/iliad_pope.txt",                 "predicted_spin": "spin-2",   "rules": "meter + bidirect rhyme",  "label": "Pope Iliad"},
    "longfellow":   {"path": "/tmp/longfellow_dante_inferno.txt",   "predicted_spin": "spin-1.5", "rules": "meter; some terza",       "label": "Longfellow"},
    "whitman":      {"path": "/tmp/whitman.txt",                    "predicted_spin": "spin-0",   "rules": "free verse",              "label": "Whitman"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",               "predicted_spin": "spin-0",   "rules": "prose / no meter",        "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",             "predicted_spin": "spin-0",   "rules": "prose / no meter",        "label": "Plato"},
    "origin":       {"path": "/tmp/origin_species.txt",             "predicted_spin": "spin-0",   "rules": "prose / no meter",        "label": "Origin"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",          "predicted_spin": "spin-0.5", "rules": "verse-like prose; cadence",  "label": "KJV-NT"},
}

KERNEL_N_EIGVECS = 200

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


def build_laplacian_and_spectrum(text, n_eigvecs=KERNEL_N_EIGVECS):
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
    ev_real.sort()  # ascending
    return ev_real, len(edges), N


def build_random_baseline_spectrum(N, n_edges, seed=42):
    """Build a same-N + same-edge-count random graph Laplacian for baseline."""
    rng = np.random.RandomState(seed)
    edges = set()
    weights = []
    while len(edges) < n_edges:
        a, b = rng.randint(0, N, size=2)
        if a == b: continue
        e = (int(min(a,b)), int(max(a,b)))
        if e in edges: continue
        edges.add(e)
        weights.append(float(rng.randint(1, 10)))
    L = dense_laplacian(N, list(edges), weights)
    ev, _ = hermitian_eigendecompose(L)
    ev_real = np.array([float(np.real(e)) for e in ev])
    ev_real.sort()
    return ev_real


def count_degenerate_clusters(ev, eps_rel=0.02, low_frac=0.10):
    """Count clusters of eigenvalues that are:
      - within bottom `low_frac` of the spectrum's range
      - within `eps_rel` (relative to spectrum range) of each other

    Returns (n_clusters, cluster_sizes).
    """
    if len(ev) < 2: return 0, []
    spectrum_range = float(ev[-1] - ev[0])
    if spectrum_range == 0: return 0, []
    low_threshold = ev[0] + low_frac * spectrum_range
    low_eigs = ev[ev <= low_threshold]
    if len(low_eigs) < 2: return 0, []
    eps_abs = eps_rel * spectrum_range
    # Cluster low_eigs by adjacency in sorted order
    clusters = []
    current_cluster = [low_eigs[0]]
    for e in low_eigs[1:]:
        if e - current_cluster[-1] < eps_abs:
            current_cluster.append(e)
        else:
            if len(current_cluster) >= 2:
                clusters.append(current_cluster)
            current_cluster = [e]
    if len(current_cluster) >= 2:
        clusters.append(current_cluster)
    return len(clusters), [len(c) for c in clusters]


def main():
    print(f"=== R-RBS-LM-54o — Spin-N form-isomorphism falsification ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Counting degenerate eigenvalue clusters near 0; predicting spin-0/1/2 mapping")

    print(f"\n--- Building Laplacian + spectrum per corpus ---")
    results = []
    for key, info in DOMAINS.items():
        text = strip_gutenberg(Path(info["path"]).read_text(encoding="utf-8", errors="replace"))
        ev, n_edges, N = build_laplacian_and_spectrum(text)
        if ev is None:
            print(f"  [SKIP] {info['label']}: insufficient data")
            continue

        # Excess clusters over random-graph baseline
        ev_rand = build_random_baseline_spectrum(N, n_edges, seed=42)
        n_clusters, cluster_sizes = count_degenerate_clusters(ev)
        n_clusters_rand, cluster_sizes_rand = count_degenerate_clusters(ev_rand)
        excess = n_clusters - n_clusters_rand

        # Also report eigenvalue spread at the low end (raw measure)
        bottom_5 = ev[:5]
        low_gap_ratio = float(bottom_5[1] / bottom_5[0]) if bottom_5[0] > 1e-12 else float("inf")

        print(f"\n  {info['label']:<14s} [predicted: {info['predicted_spin']:<8s} — {info['rules']}]")
        print(f"    N={N}, edges={n_edges}, spectrum range = {ev[-1]-ev[0]:.3f}")
        print(f"    Degenerate clusters (corpus):     {n_clusters}  sizes={cluster_sizes}")
        print(f"    Degenerate clusters (random):     {n_clusters_rand}  sizes={cluster_sizes_rand}")
        print(f"    Excess over random:                {excess:+d}")
        print(f"    Bottom-5 eigvals: {bottom_5}")
        print(f"    Low-end gap ratio (ev[1]/ev[0]):  {low_gap_ratio:.3f}")

        results.append({
            "key": key, "label": info["label"], "predicted_spin": info["predicted_spin"], "rules": info["rules"],
            "N": N, "edges": n_edges,
            "spectrum_range": float(ev[-1]-ev[0]),
            "n_clusters": n_clusters, "cluster_sizes": cluster_sizes,
            "n_clusters_random": n_clusters_rand, "cluster_sizes_random": cluster_sizes_rand,
            "excess_over_random": excess,
            "low_gap_ratio": low_gap_ratio,
            "bottom_5_eigvals": [float(e) for e in bottom_5],
        })

    # === Verdict ===
    print(f"\n=== Predicted vs measured spin-N form ===")
    print(f"  {'corpus':<14s} {'predicted':<10s} {'excess_clusters':>16s} {'low_gap':>9s}")
    for r in sorted(results, key=lambda x: x["predicted_spin"]):
        print(f"  {r['label']:<14s} {r['predicted_spin']:<10s} {r['excess_over_random']:>+16d} {r['low_gap_ratio']:>9.3f}")

    # Test the form-isomorphism prediction
    # Group by predicted_spin and average excess
    by_spin = {}
    for r in results:
        s = r["predicted_spin"]
        by_spin.setdefault(s, []).append(r["excess_over_random"])

    print(f"\n=== Excess-cluster averages by predicted spin-form ===")
    print(f"  {'predicted_spin':<12s} {'n_corpora':>10s} {'avg_excess':>11s}")
    spin_order = ["spin-0", "spin-0.5", "spin-1", "spin-1.5", "mixed", "spin-2"]
    spin_summary = {}
    for s in spin_order:
        if s in by_spin:
            avg = float(np.mean(by_spin[s]))
            spin_summary[s] = avg
            print(f"  {s:<12s} {len(by_spin[s]):>10d} {avg:>+11.3f}")

    # Falsification logic
    print(f"\n=== Falsification verdict ===")
    spin_0 = spin_summary.get("spin-0", 0)
    spin_1 = spin_summary.get("spin-1", 0)
    spin_2 = spin_summary.get("spin-2", 0)
    monotonic = (spin_0 <= spin_1 <= spin_2) and (spin_2 > spin_0)
    big_gap = abs(spin_2 - spin_0) >= 2  # excess clusters difference

    if monotonic and big_gap:
        verdict = "FORM-ISOMORPHISM SUPPORTED: degenerate-cluster count increases monotonically with predicted spin-N (spin-0={}, spin-1={}, spin-2={})".format(spin_0, spin_1, spin_2)
    elif monotonic:
        verdict = "FORM-ISOMORPHISM WEAK SUPPORT: monotone but small gap; spin-0={}, spin-1={}, spin-2={}".format(spin_0, spin_1, spin_2)
    elif spin_2 > spin_0 and spin_2 > spin_1:
        verdict = "PARTIAL SUPPORT: spin-2 has most clusters but mid-spin (1) not ordered (spin-0={}, spin-1={}, spin-2={})".format(spin_0, spin_1, spin_2)
    else:
        verdict = "FALSIFIED: cluster count does NOT track predicted spin-N (spin-0={}, spin-1={}, spin-2={}); user's mapping was conflation, not form-isomorphism".format(spin_0, spin_1, spin_2)
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54o",
        "results": results,
        "spin_summary": spin_summary,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54o_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
