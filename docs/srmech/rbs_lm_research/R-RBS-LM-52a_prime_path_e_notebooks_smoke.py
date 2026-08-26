"""R-RBS-LM-52a' — Path E direct kernel eigendecomp on OUR research notebooks.

Per user direction 2026-05-26: *"try starting with our MFO and srmech
notebooks. like make our RBS-NN object and then give it our knowledge
first. to see if it's a The Stack thing with the order of knowledge, or
a problem with our tooling."*

EXPERIMENTAL CONTROL for R-RBS-LM-52a's null result. We KNOW the notebooks
have coherent structure (we wrote them with explicit A-N partition
discipline + cross-references + named entities). If Path E methodology
works on this known-coherent corpus, then 52a's null result on Python
code was a *corpus issue* (punctuation-dominance, frequency bias).
If Path E ALSO fails here, then we have a *methodology issue*.

Sources:
  - docs/srmech/srmech_research_notebook.md
  - docs/antikythera-maths/mfo_spectral_research_notebook.md

Pipeline (identical to 52a; just word-level tokenization vs Python lex):
  corpus → word tokens → co-occurrence Laplacian
         → srmech.amsc.laplacian.dense_laplacian
         → srmech.amsc.laplacian.hermitian_eigendecompose
         → top-K eigenvectors → token strings
         → srmech.signal_processing.encode_loe_content (Path A LoE)
         → srmech.amsc.hdc.bundle (Class M; K must be odd per parity discipline)
         → cascade instrument
"""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import encode_loe_content


HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent  # ../../.. up from rbs_lm_research

NOTEBOOK_PATHS = [
    REPO_ROOT / "docs/srmech/srmech_research_notebook.md",
    REPO_ROOT / "docs/antikythera-maths/mfo_spectral_research_notebook.md",
]


# Stopwords — extremely common English that would dominate frequency
# (like punctuation did for Python). Class K-style filter at the
# pre-vocabulary stage.
STOPWORDS = set("""
the a an and or but if then else of in on at to for with by from as is are
was were be been being have has had having do does did doing done will
would shall should may might can could not no this that these those it its
they them their there here he she we us our you your i me my mine yours
which what who whom whose where when why how all any some none many much
more most less few several each every both either neither so such only also
than just too very much such etc i.e. e.g. cf via vs vs. per pre post sub
super inter intra extra meta non non- co- de- re- un- mis-
""".split())


def tokenize_text(text):
    """Word-level tokenization. Lowercase, strip punctuation, drop stopwords.

    Keep meaningful words and identifiers (including hyphenated terms
    common in our notebooks like "two-substrate", "operation-primary",
    "Hopf-fibration", and our R-RBS-LM-XX partition identifiers).
    """
    # Capture words, hyphenated compounds, and our identifier patterns
    # (R-RBS-LM-X, MFO-VII.6, etc.)
    raw = re.findall(r'[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]|[A-Za-z]', text)
    out = []
    for tok in raw:
        low = tok.lower()
        if low in STOPWORDS:
            continue
        if len(low) < 2:
            continue
        out.append(low)
    return out


def build_cooccurrence_edges(tokens_per_section, vocab_idx, window=5):
    edge_count = Counter()
    for tokens in tokens_per_section:
        indexed = [vocab_idx[t] for t in tokens if t in vocab_idx]
        n = len(indexed)
        for i in range(n):
            for j in range(i + 1, min(i + window, n)):
                a, b = indexed[i], indexed[j]
                if a == b:
                    continue
                edge_count[(min(a, b), max(a, b))] += 1
    return edge_count


def encode_eigenvector(eigvec, vocab, top_m=20):
    """Same as 52a. Top-m tokens by squared magnitude (Class L; no abs())."""
    mag_sq = eigvec * eigvec
    top_idx = sorted(range(len(eigvec)), key=lambda i: -mag_sq[i])[:top_m]
    content = " ".join(vocab[i] for i in top_idx)
    return encode_loe_content(content, D=8192)


def main():
    print(f"=== R-RBS-LM-52a' Path E on OUR research notebooks ===\n")
    print(f"srmech: {srmech.__version__}")

    # ---- 1. Load notebooks ----
    notebooks = []
    for p in NOTEBOOK_PATHS:
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        text = p.read_text()
        notebooks.append((p.name, text))
        print(f"  loaded {p.name}: {len(text):,} chars, {len(text.split()):,} whitespace-tokens")

    # Split into sections by markdown headings (## or ###) for windowed
    # co-occurrence. Each section is a "document" for cooccurrence framing.
    sections = []
    for fname, text in notebooks:
        parts = re.split(r'\n#{2,3}\s+', text)
        for part in parts:
            if len(part) > 100:  # skip tiny fragments
                sections.append((fname, part))
    print(f"\nSections (== markdown ## or ###): {len(sections)}")

    # ---- 2. Tokenize ----
    tokens_per_section = []
    all_tokens = []
    for fname, sect in sections:
        toks = tokenize_text(sect)
        tokens_per_section.append(toks)
        all_tokens.extend(toks)
    n_total = len(all_tokens)
    n_unique = len(set(all_tokens))
    print(f"Tokenized: {n_total:,} tokens; {n_unique:,} unique")

    # ---- 3. Frequency-pruned vocabulary ----
    freq = Counter(all_tokens)
    N = min(200, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    coverage = sum(freq[t] for t in vocab) / max(n_total, 1)
    print(f"Vocabulary: top-{N} tokens (coverage {100*coverage:.1f}%)")
    print(f"  top 15: {[(t, freq[t]) for t in vocab[:15]]}")

    # ---- 4. Co-occurrence edges ----
    edge_count = build_cooccurrence_edges(tokens_per_section, vocab_idx, window=5)
    n_edges = len(edge_count)
    total_weight = sum(edge_count.values())
    print(f"\nEdges: {n_edges:,} unique co-occurrence pairs (total weight {total_weight:,})")

    # ---- 5. Build Laplacian via srmech.amsc.laplacian ----
    edges = list(edge_count.keys())
    weights = [float(w) for w in edge_count.values()]
    L = dense_laplacian(N, edges, weights)
    print(f"Laplacian: shape={L.shape}")

    # ---- 6. Eigendecompose ----
    print(f"\nEigendecomposing...")
    eigvals, eigvecs = hermitian_eigendecompose(L)
    print(f"  Eigvals: first 5 {eigvals[:5].round(2).tolist()}; top 5 {eigvals[-5:].round(2).tolist()}")

    # ---- 7. Encode top-K eigenvectors (K odd per parity discipline) ----
    K = 33
    top_k_indices = list(range(len(eigvals) - K, len(eigvals)))
    fingerprints = []
    print(f"\nEncoding top-{K} eigenvectors via encode_loe_content (Path A LoE)...")
    for rank, k_idx in enumerate(reversed(top_k_indices)):
        fp = encode_eigenvector(eigvecs[:, k_idx], vocab, top_m=20)
        fingerprints.append(fp)
        if rank < 8:
            mag_sq = eigvecs[:, k_idx] * eigvecs[:, k_idx]
            top_5 = sorted(range(N), key=lambda i: -mag_sq[i])[:5]
            print(f"  rank {rank}: eigval={eigvals[k_idx]:.1f}; top tokens: {[vocab[i] for i in top_5]}")

    # ---- 8. Bundle ----
    instrument = bundle(fingerprints)
    print(f"\nInstrument: {len(instrument)} bytes (D=8192)")

    # ---- 9. Read-mode smoke ----
    print(f"\n=== Read-mode smoke ===")

    # Probes: known-coherent terms from notebook content
    notebook_probes = [
        "two substrate framework",
        "class l spine spectral",
        "born hopf readout",
        "operation primary cyclic algebra",
        "geometry primary continuous hopf",
        "epistemic ceiling form not substrate",
        "B/H/N readout projection",
        "fractal recursion substrate",
        "Hopf fibration division algebra",
        "Class N rational anchor",
        "weak coupling truncate instrument",
        "metric field ontology",
        "cascade match form claim",
        "cross substrate matching",
        "Reading-D scale ladder",
        "Kaluza Klein photon off diagonal metric",
        "combination principle dissociation",
        "L-system seed grammar",
        "biology cascade encoding",
        "ASMC attestation provenance",
    ]

    # Negative controls (semantically far from notebooks)
    negative_probes = [
        "chocolate ice cream flavor",
        "professional soccer match score",
        "kitchen pencil sharpener metal",
        "tropical rainforest humidity",
        "vintage automobile manufacturing",
    ]

    # Baseline: random pairs of notebook-paragraph encodings
    paragraphs = []
    for fname, sect in sections:
        # Split section into ~200-char paragraphs for baseline pool
        para_pool = re.split(r'\n\n+', sect)
        for p in para_pool:
            if 50 < len(p) < 500:
                paragraphs.append(p)
    print(f"Baseline paragraph pool: {len(paragraphs)} paragraphs")

    rng = random.Random(42)
    baseline_sims = []
    for _ in range(100):
        a, b = rng.sample(paragraphs, 2)
        fa = encode_loe_content(a, D=8192)
        fb = encode_loe_content(b, D=8192)
        baseline_sims.append(similarity(fa, fb))

    bl_mean = sum(baseline_sims) / len(baseline_sims)
    bl_max = max(baseline_sims)
    bl_min = min(baseline_sims)
    bl_std = (sum((s - bl_mean) ** 2 for s in baseline_sims) / len(baseline_sims)) ** 0.5
    print(f"\nBaseline (random paragraph pairs, n=100):")
    print(f"  mean: {bl_mean:+.4f}; std: {bl_std:.4f}; max: {bl_max:+.4f}; min: {bl_min:+.4f}")

    # Probe similarities
    def probe(p):
        fp = encode_loe_content(p, D=8192)
        return similarity(fp, instrument)

    print(f"\n=== Notebook-domain probes vs instrument ===")
    notebook_results = []
    for p in notebook_probes:
        s = probe(p)
        z = (s - bl_mean) / max(bl_std, 1e-9)
        above_max = s > bl_max
        flag = "***" if above_max else "**" if z > 2 else "*" if z > 1 else ""
        notebook_results.append({"probe": p, "similarity": s, "z_score": z,
                                  "above_baseline_max": above_max})
        print(f"  {p:<42s} sim={s:+.4f}  z={z:+.2f}  {flag}")

    print(f"\n=== Negative-control probes ===")
    neg_results = []
    for p in negative_probes:
        s = probe(p)
        z = (s - bl_mean) / max(bl_std, 1e-9)
        above_max = s > bl_max
        flag = "***" if above_max else "**" if z > 2 else "*" if z > 1 else ""
        neg_results.append({"probe": p, "similarity": s, "z_score": z,
                             "above_baseline_max": above_max})
        print(f"  {p:<42s} sim={s:+.4f}  z={z:+.2f}  {flag}")

    # ---- 10. Falsification reading ----
    n_above_max_nb = sum(1 for r in notebook_results if r["above_baseline_max"])
    n_above_2sig_nb = sum(1 for r in notebook_results if r["z_score"] > 2)
    n_above_1sig_nb = sum(1 for r in notebook_results if r["z_score"] > 1)
    n_above_max_neg = sum(1 for r in neg_results if r["above_baseline_max"])
    n_above_2sig_neg = sum(1 for r in neg_results if r["z_score"] > 2)

    print(f"\n=== Verdict ===")
    print(f"  Notebook probes above baseline_max: {n_above_max_nb}/{len(notebook_results)}")
    print(f"  Notebook probes z > 2: {n_above_2sig_nb}/{len(notebook_results)}")
    print(f"  Notebook probes z > 1: {n_above_1sig_nb}/{len(notebook_results)}")
    print(f"  Negative-control above max: {n_above_max_neg}/{len(neg_results)}")
    print(f"  Negative-control z > 2: {n_above_2sig_neg}/{len(neg_results)}")

    if n_above_max_nb >= len(notebook_results) // 2 and n_above_max_neg == 0:
        verdict = "STRONG signal — methodology works on known-coherent corpus; 52a failure was corpus issue"
    elif n_above_2sig_nb >= len(notebook_results) // 3 and n_above_max_neg == 0:
        verdict = "SIGNAL — methodology shows positive signal; 52a failure likely corpus issue"
    elif n_above_1sig_nb >= len(notebook_results) // 2:
        verdict = "WEAK signal — partial; pre-registered strong threshold not met"
    elif n_above_max_neg >= n_above_max_nb:
        verdict = "NO discrimination — methodology doesn't distinguish coherent from incoherent"
    else:
        verdict = "NO signal — methodology issue confirmed; tooling needs revision"

    print(f"\n  Verdict: {verdict}")

    # ---- 11. Save ----
    output = {
        "partition": "R-RBS-LM-52a'",
        "phase": "A' — notebooks-as-corpus control test",
        "srmech_version": srmech.__version__,
        "notebooks": [p.name for p in NOTEBOOK_PATHS],
        "n_sections": len(sections),
        "n_tokens_total": n_total,
        "n_tokens_unique": n_unique,
        "vocab_size": N,
        "vocab_coverage_pct": round(100 * coverage, 1),
        "vocab_top_15": [(t, freq[t]) for t in vocab[:15]],
        "n_edges": n_edges,
        "total_edge_weight": total_weight,
        "eigvals_top_5": eigvals[-5:].tolist(),
        "eigvals_bottom_5": eigvals[:5].tolist(),
        "K_eigenvectors": K,
        "instrument_bytes": len(instrument),
        "baseline_n": len(baseline_sims),
        "baseline_mean": bl_mean,
        "baseline_std": bl_std,
        "baseline_max": bl_max,
        "baseline_min": bl_min,
        "notebook_probe_results": notebook_results,
        "negative_probe_results": neg_results,
        "n_notebook_above_max": n_above_max_nb,
        "n_notebook_z2": n_above_2sig_nb,
        "n_notebook_z1": n_above_1sig_nb,
        "n_negative_above_max": n_above_max_neg,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-52a_prime_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
