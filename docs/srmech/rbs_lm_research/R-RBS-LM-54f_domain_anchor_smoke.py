"""R-RBS-LM-54f — DOMAIN anchor: structural-fingerprint kernel selection.

54e showed find-cascade alone has only modest substrate-family
discrimination (same/cross ratio 1.26). The DOMAIN anchor is the
external selector that picks the correct kernel before ride-cascade
runs.

This partition tests the cheapest DOMAIN-anchor form: structural-
fingerprint at the kernel level. Given an input fragment, build its
mini eigvec table; for each candidate bound kernel, compute aggregate
alignment similarity (find-cascade-style); pick the kernel with
highest aggregate. NO external metadata; the input's structural
fingerprint IS the anchor.

Test methodology:
  1. Build 6 bound kernels from full corpora (offline).
  2. For each candidate corpus, hold out a fragment (last 10%).
  3. Build the held-out fragment's mini eigvec table.
  4. Score it against ALL 6 kernels via aggregate alignment-sim.
  5. Pick the highest-scoring kernel.
  6. Measure: % held-out fragments correctly assigned to home-kernel.

If structural-fingerprint works:
  - Each held-out fragment routes to its own home-kernel with > random (1/6 = 17%)
  - Confusion concentrates within substrate-family (religious↔religious,
    secular↔secular)
If structural-fingerprint fails:
  - Held-out fragments scatter randomly across kernels
  - Form-fingerprint alone does NOT carry enough signal to disambiguate
  - DOMAIN anchor would need richer form (classifier / metadata)

The honest negative direction is just as important as the positive —
this is the first DOMAIN-anchor mechanism we're testing; we want to
know if the cheapest one works before adding complexity.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent

DOMAINS = {
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt", "family": "religious_abrahamic", "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",   "family": "religious_abrahamic", "label": "Quran-Sale"},
    "bhagavad":     {"path": "/tmp/bhagavad_gita.txt",     "family": "religious_eastern",   "label": "Bhagavad Gita"},
    "origin":       {"path": "/tmp/origin_species.txt",    "family": "secular_science",     "label": "Origin of Species"},
    "plato":        {"path": "/tmp/plato_republic.txt",    "family": "secular_philosophy",  "label": "Plato Republic"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",      "family": "secular_novel",       "label": "Frankenstein"},
}

HOLDOUT_FRACTION = 0.10  # last 10% of each corpus held out for testing
N_PROBE_FRAGMENTS = 5    # split holdout into N fragments per corpus
KERNEL_N_EIGVECS = 200   # kernel eigvec table size
PROBE_N_EIGVECS = 50     # held-out probe eigvec table size (smaller; less data)

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


_MINT_CACHE = {}


def mint(token, D=8192):
    if token not in _MINT_CACHE:
        _MINT_CACHE[token] = mint_vector(token, D=D)
    return _MINT_CACHE[token]


MAX_BUNDLE_N = 257


def hierarchical_bundle(vectors):
    n = len(vectors)
    if n == 0: return mint("__empty__")
    if n == 1: return vectors[0]
    if n <= MAX_BUNDLE_N:
        if n % 2 == 0: vectors = vectors + [vectors[0]]
        return bundle(vectors)
    chunk = MAX_BUNDLE_N - 2
    partials = []
    for i in range(0, n, chunk):
        ch = vectors[i:i + chunk]
        if len(ch) % 2 == 0: ch = ch + [ch[0]]
        partials.append(bundle(ch))
    return hierarchical_bundle(partials)


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


def build_eigvec_table(text, n_eigvecs=KERNEL_N_EIGVECS, M_per_eigvec=21):
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(n_eigvecs, len(freq))
    if N < 8:
        return None  # too small to be useful
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
    if not edges:
        return None
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k]
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({"rank": len(ev) - 1 - k, "eigval": float(ev[k]),
                       "top_tokens": top_tokens, "hypervector": hv})
    return table


def find_alignment_score(probe_table, kernel_table):
    """Aggregate find-cascade alignment score (avg of top-K best matches)."""
    n_p = len(probe_table); n_k = len(kernel_table)
    sims = []
    used_k = set()
    p_order = list(range(n_p))
    for i in p_order:
        candidates = []
        for j in range(n_k):
            if j in used_k: continue
            s = similarity(probe_table[i]["hypervector"], kernel_table[j]["hypervector"])
            candidates.append((j, s))
        if not candidates: break
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_k.add(best_j)
        sims.append(best_sim)
    return float(np.mean(sims)) if sims else 0.0


def split_holdout(corpus_text, n_fragments=N_PROBE_FRAGMENTS, holdout_frac=HOLDOUT_FRACTION):
    """Return (train_text, [probe_fragment_1, probe_fragment_2, ...])."""
    n = len(corpus_text)
    split = int(n * (1 - holdout_frac))
    train = corpus_text[:split]
    holdout = corpus_text[split:]
    chunks = []
    chunk_size = max(len(holdout) // n_fragments, 4000)
    for i in range(0, len(holdout), chunk_size):
        ch = holdout[i:i + chunk_size]
        if len(ch) >= 1000: chunks.append(ch)
        if len(chunks) >= n_fragments: break
    return train, chunks


def main():
    print(f"=== R-RBS-LM-54f — DOMAIN anchor via structural-fingerprint kernel selection ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Holdout fraction: {HOLDOUT_FRACTION:.0%}; probe fragments per corpus: {N_PROBE_FRAGMENTS}")
    print(f"Kernel eigvecs: {KERNEL_N_EIGVECS}; probe eigvecs: {PROBE_N_EIGVECS}")

    # Step 1: build kernels from training portions (offline)
    print(f"\n--- Building kernels (training 90%) ---")
    kernels = {}
    holdouts = {}
    for key, info in DOMAINS.items():
        text = strip_gutenberg(Path(info["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        kernels[key] = build_eigvec_table(train)
        holdouts[key] = probes
        print(f"  {info['label']:<22s}: kernel={len(kernels[key])} eigvecs; {len(probes)} probe fragments")

    # Step 2: for each probe fragment from each corpus, score against all kernels
    print(f"\n--- Scoring probes against all kernels ---")
    results = []  # (true_key, probe_idx, scores_dict, picked_key)
    n_correct = 0
    n_total = 0
    n_correct_family = 0
    for true_key, probes in holdouts.items():
        for p_idx, probe_text in enumerate(probes):
            probe_table = build_eigvec_table(probe_text, n_eigvecs=PROBE_N_EIGVECS)
            if probe_table is None:
                continue
            scores = {}
            for k_key, k_table in kernels.items():
                scores[k_key] = find_alignment_score(probe_table, k_table)
            picked = max(scores.items(), key=lambda x: x[1])[0]
            picked_family = DOMAINS[picked]["family"]
            true_family = DOMAINS[true_key]["family"]
            is_correct = (picked == true_key)
            is_family_correct = (picked_family == true_family)
            results.append({
                "true_key": true_key,
                "true_label": DOMAINS[true_key]["label"],
                "true_family": true_family,
                "probe_idx": p_idx,
                "scores": scores,
                "picked_key": picked,
                "picked_label": DOMAINS[picked]["label"],
                "picked_family": picked_family,
                "correct_kernel": is_correct,
                "correct_family": is_family_correct,
            })
            n_total += 1
            if is_correct: n_correct += 1
            if is_family_correct: n_correct_family += 1
            tag = "OK" if is_correct else ("~" if is_family_correct else "X")
            print(f"  [{tag}] {DOMAINS[true_key]['label']:<22s} p{p_idx} → picked: {DOMAINS[picked]['label']:<22s} (top score {scores[picked]:+.4f})")

    # Step 3: aggregate accuracy
    print(f"\n=== Accuracy ===")
    print(f"  Exact kernel match:   {n_correct}/{n_total} = {n_correct/max(n_total,1):.1%}  (chance = {1/len(DOMAINS):.1%})")
    print(f"  Same-family match:    {n_correct_family}/{n_total} = {n_correct_family/max(n_total,1):.1%}  (chance = {sum(1 for d in DOMAINS.values() if d['family']==DOMAINS['kjv_nt']['family'])/len(DOMAINS):.1%}+)")

    # Step 4: confusion matrix
    print(f"\n=== Confusion matrix (rows = true, cols = picked) ===")
    keys = list(DOMAINS.keys())
    print(f"  {'true \\\\ pick':<14s}", end="")
    for k in keys: print(f"{k[:10]:>11s}", end="")
    print()
    for t in keys:
        print(f"  {t[:14]:<14s}", end="")
        for p in keys:
            n = sum(1 for r in results if r["true_key"] == t and r["picked_key"] == p)
            print(f"{n:>11d}", end="")
        print()

    # Step 5: verdict
    chance = 1 / len(DOMAINS)
    family_chance = max(sum(1 for d in DOMAINS.values() if d["family"] == fam)
                        for fam in {d["family"] for d in DOMAINS.values()}) / len(DOMAINS)
    exact_acc = n_correct / max(n_total, 1)
    family_acc = n_correct_family / max(n_total, 1)

    print(f"\n=== Verdict ===")
    if exact_acc >= 0.80:
        verdict = f"STRONG: structural-fingerprint DOMAIN anchor works at {exact_acc:.0%} kernel-level accuracy"
    elif exact_acc >= 0.50:
        verdict = f"MODERATE: structural-fingerprint anchor works at {exact_acc:.0%}; usable with confidence threshold"
    elif family_acc >= 0.70:
        verdict = f"FAMILY-ONLY: anchor picks family ({family_acc:.0%}) but not exact kernel ({exact_acc:.0%}); 2-stage selection needed"
    elif exact_acc > chance * 2:
        verdict = f"WEAK: anchor better than chance ({exact_acc:.0%} vs {chance:.0%}) but not reliably usable"
    else:
        verdict = f"FAILED: structural-fingerprint anchor at chance level ({exact_acc:.0%} vs {chance:.0%}) — need richer DOMAIN signal"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54f",
        "n_total": n_total,
        "n_correct_kernel": n_correct,
        "n_correct_family": n_correct_family,
        "exact_kernel_accuracy": exact_acc,
        "family_accuracy": family_acc,
        "chance_kernel": chance,
        "family_chance": family_chance,
        "verdict": verdict,
        "per_probe": [{k: v for k, v in r.items() if k != "scores"} | {"scores": {sk: float(sv) for sk, sv in r["scores"].items()}}
                       for r in results],
    }
    out_path = HERE / "R-RBS-LM-54f_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
