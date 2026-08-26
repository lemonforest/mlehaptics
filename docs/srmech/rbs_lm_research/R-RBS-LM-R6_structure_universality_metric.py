"""#855 R6 — the cross-coupling / structure-universality METRIC + cross-domain baseline.

The real R6 question (Stream B): do per-LANGUAGE native-instruction kernels share relationship-
STRUCTURE (structure universal) or not? That needs the multilingual corpus fetch + the
substitute-verifier triality (the requester is not multilingual) -> a USER-IN-LOOP continuation.

What R6 does NOW (the tractable, no-fetch part): define + demonstrate the metric the cross-
language test will use, on the available cross-DOMAIN proxy (the F339 srmech vs MFO notebooks,
both English/framework but different knowledge-bodies), with a structure-destroyed CONTROL so
the metric is shown to measure structure (not an artifact).

Metric = normalized co-occurrence-Laplacian EIGENSPECTRUM-SHAPE correlation between two K1
kernels. If two corpora share relationship-structure (even with disjoint surface vocab), their
normalized Class-L eigenspectra have the same SHAPE -> high Pearson r. Surface-vocab overlap is
NOT required -- that is exactly what makes it a structure (not content) metric, and what the
cross-language test needs (different languages = disjoint vocab, same structure if universal).

srmech-native: dense_laplacian -> hermitian_eigendecompose (Class L). No Counter-as-storage
(Counter only accumulates edge weights feeding dense_laplacian, the prescribed path).

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R6_structure_universality_metric.py
"""
import json, re, random
from collections import Counter
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose

HERE = Path(__file__).parent
REPO = HERE.parent.parent.parent
NOTEBOOKS = {
    "srmech": REPO / "docs/srmech/srmech_research_notebook.md",
    "mfo": REPO / "docs/antikythera-maths/mfo_spectral_research_notebook.md",
}
VOCAB, WINDOW, TOPN = 200, 5, 60
STOP = set("the a an and or but if then of in on at to for with by from as is are was were be "
           "this that these those it its they them their we us our you your i me my".split())


def tokenize(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]", text)
            if t.lower() not in STOP and len(t) > 2]


def k1_spectrum(tokens):
    freq = Counter(tokens)
    vocab = [t for t, _ in freq.most_common(VOCAB)]
    idx = {t: i for i, t in enumerate(vocab)}
    N = len(vocab)
    edges = Counter()
    indexed = [idx[t] for t in tokens if t in idx]
    for i in range(len(indexed)):
        for j in range(i + 1, min(i + WINDOW, len(indexed))):
            a, b = indexed[i], indexed[j]
            if a != b:
                edges[(min(a, b), max(a, b))] += 1
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    eigvals, _ = hermitian_eigendecompose(L)
    ev = np.sort(np.asarray(eigvals))[::-1][:TOPN]   # top-N eigenvalues, descending
    return ev / ev[0]                                # normalize by leading eigenvalue (shape, not scale)


def struct_corr(s1, s2):
    n = min(len(s1), len(s2))
    return float(np.corrcoef(s1[:n], s2[:n])[0, 1])


def main():
    print(f"#855 R6 — structure-universality metric (srmech {srmech.__version__})")
    toks = {}
    for k, p in NOTEBOOKS.items():
        toks[k] = tokenize(p.read_text())
        print(f"  {k}: {len(toks[k]):,} content tokens")

    spec = {k: k1_spectrum(v) for k, v in toks.items()}
    # structure-destroyed control: shuffle srmech tokens (kills co-occurrence, keeps vocab/freq)
    rng = random.Random(20260603)
    sh = toks["srmech"][:]; rng.shuffle(sh)
    spec["srmech_shuffled"] = k1_spectrum(sh)

    print("\n  normalized eigenspectrum-shape correlation (Pearson r):")
    r_real = struct_corr(spec["srmech"], spec["mfo"])
    r_ctrl = struct_corr(spec["srmech"], spec["srmech_shuffled"])
    r_mfo_ctrl = struct_corr(spec["mfo"], spec["srmech_shuffled"])
    print(f"    srmech ~ mfo            (real, both framework) : r = {r_real:+.3f}")
    print(f"    srmech ~ srmech-SHUFFLED (structure-destroyed)  : r = {r_ctrl:+.3f}")
    print(f"    mfo ~ srmech-SHUFFLED    (structure-destroyed)  : r = {r_mfo_ctrl:+.3f}")
    print(f"\n  top-8 normalized eigenvalues:")
    for k in ("srmech", "mfo", "srmech_shuffled"):
        print(f"    {k:>16}: {[round(float(x),3) for x in spec[k][:8]]}")

    metric_works = r_real > max(r_ctrl, r_mfo_ctrl) + 0.05
    print(f"\n=== verdict ===")
    print(f"  metric distinguishes shared-structure from destroyed-structure: {metric_works}")
    print(f"  (real srmech~mfo r={r_real:+.3f} vs structure-destroyed r={r_ctrl:+.3f}/{r_mfo_ctrl:+.3f})")
    print(f"  => cross-DOMAIN baseline established. Cross-LANGUAGE test (the real R6) applies this")
    print(f"     same metric across per-language kernels -- GATED on multilingual corpus fetch +")
    print(f"     substitute-verifier triality (requester not multilingual) = user-in-loop continuation.")

    out = {"partition": "R-RBS-LM-R6 (#855 R6)", "srmech_version": srmech.__version__,
           "metric": "normalized K1 Laplacian eigenspectrum-shape Pearson correlation",
           "r_srmech_mfo_real": r_real, "r_srmech_shuffled_ctrl": r_ctrl,
           "r_mfo_shuffled_ctrl": r_mfo_ctrl, "metric_distinguishes_structure": metric_works,
           "topn": TOPN, "vocab": VOCAB, "window": WINDOW,
           "spectra_top8": {k: [float(x) for x in spec[k][:8]] for k in spec},
           "multilingual_status": "corpora SOURCED+ATTESTED (10 locales, #846); ENCODE needs fetch + "
                                  "substitute-verifier triality (user-not-multilingual) = user-in-loop continuation"}
    (HERE / "R-RBS-LM-R6_results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R6_results.json'}")


if __name__ == "__main__":
    main()
