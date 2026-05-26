"""R-RBS-LM-54m — Poetry vs prose ride benchmark (substrate-mismatch test).

Per user 2026-05-26: "ride is simply not right for this substrate.
this is an okay answer too. but it might be for poetry."

54g showed ride is HALF-POSITIVE on English prose — it switches
vocabulary (vs identity baseline) but does NOT beat freq-weighted-
target baseline. The substrate-mismatch hypothesis: prose disperses
information across many tokens; alignment-driven emission can't
escape frequency-baseline.

Poetry should be different. In English verse, each token carries
more load (less stopword padding; tighter root-word coupling).
Alignment-driven emission should escape frequency-baseline because
the alignment selects load-bearing tokens, not common-prose
connective tissue.

This partition holds translator-form CONSTANT (all English originals)
and varies *only* compression (prose ↔ poetry):

Poetry corpora (English originals / heroic verse translations):
  - Shakespeare Complete Works (blank verse + sonnets, 1600s)
  - Milton Paradise Lost (blank verse epic, 1600s)
  - Pope Iliad (heroic couplets, 1700s)
  - Pope Odyssey (heroic couplets, 1700s)
  - Longfellow Dante Inferno translation (blank verse, 1800s)
  - Whitman Leaves of Grass (free verse, 1800s)

Prose corpora (English originals, comparison baselines):
  - Frankenstein (Romantic novel)
  - Origin of Species (Victorian scientific prose)
  - Plato Republic (philosophical dialogue prose)

Test pairings (within and across substrate-class):
  - poetry → poetry (within-class compressed)
  - prose → prose (within-class non-compressed; 54g baseline)
  - poetry → prose (cross-class)
  - prose → poetry (cross-class)

Metric: ride-quality minus freq-weighted-target baseline.
This is the "alignment-specific signal" — does the ride know more
than just "switch to target's frequent words"?
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
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent

DOMAINS = {
    # Poetry (English originals + verse translations)
    "shakespeare":  {"path": "/tmp/shakespeare.txt",                "class": "poetry", "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",              "class": "poetry", "label": "Milton Paradise Lost"},
    "pope_iliad":   {"path": "/tmp/iliad_pope.txt",                 "class": "poetry", "label": "Pope Iliad"},
    "pope_odyssey": {"path": "/tmp/odyssey_pope.txt",               "class": "poetry", "label": "Pope Odyssey"},
    "longfellow":   {"path": "/tmp/longfellow_dante_inferno.txt",   "class": "poetry", "label": "Longfellow Inferno"},
    "whitman":      {"path": "/tmp/whitman.txt",                    "class": "poetry", "label": "Whitman Leaves"},
    # Prose (English originals)
    "frankenstein": {"path": "/tmp/frankenstein.txt",               "class": "prose",  "label": "Frankenstein"},
    "origin":       {"path": "/tmp/origin_species.txt",             "class": "prose",  "label": "Origin of Species"},
    "plato":        {"path": "/tmp/plato_republic.txt",             "class": "prose",  "label": "Plato Republic"},
}

# Probe pairings (anchor, target) — sample within / cross class
PAIRS = [
    # Within-poetry
    {"anchor": "milton",       "target": "shakespeare",  "class_pair": "poetry→poetry"},
    {"anchor": "whitman",      "target": "milton",       "class_pair": "poetry→poetry"},
    {"anchor": "longfellow",   "target": "pope_iliad",   "class_pair": "poetry→poetry"},
    # Within-prose
    {"anchor": "frankenstein", "target": "plato",        "class_pair": "prose→prose"},
    {"anchor": "origin",       "target": "frankenstein", "class_pair": "prose→prose"},
    # Cross: poetry → prose
    {"anchor": "milton",       "target": "frankenstein", "class_pair": "poetry→prose"},
    {"anchor": "shakespeare",  "target": "plato",        "class_pair": "poetry→prose"},
    # Cross: prose → poetry
    {"anchor": "frankenstein", "target": "milton",       "class_pair": "prose→poetry"},
    {"anchor": "plato",        "target": "shakespeare",  "class_pair": "prose→poetry"},
]

HOLDOUT_FRACTION = 0.10
N_PROBE_FRAGMENTS = 4
KERNEL_N_EIGVECS = 200
TOP_K_RANKS_PER_TOKEN = 3
TOP_N_EMITTED_PER_RANK = 7

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
    if N < 8: return None, None, None, None
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
    if not edges: return None, None, None, None
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
                       "top_tokens": top_tokens, "hypervector": hv, "eigvec_full": eigvec})
    return table, vocab, idx_map, freq


def find_alignment(table_A, table_B):
    n_A = len(table_A); n_B = len(table_B)
    sim_matrix = np.zeros((n_A, n_B))
    for i in range(n_A):
        for j in range(n_B):
            sim_matrix[i, j] = similarity(table_A[i]["hypervector"], table_B[j]["hypervector"])
    used_B = set()
    alignment = {}
    a_order = sorted(range(n_A), key=lambda i: -sim_matrix[i].max())
    for i in a_order:
        candidates = [(j, sim_matrix[i, j]) for j in range(n_B) if j not in used_B]
        if not candidates: continue
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_B.add(best_j)
        alignment[i] = (best_j, float(best_sim))
    return alignment


def split_holdout(text, n_fragments=N_PROBE_FRAGMENTS, holdout_frac=HOLDOUT_FRACTION):
    n = len(text)
    split = int(n * (1 - holdout_frac))
    train = text[:split]
    holdout = text[split:]
    chunks = []
    chunk_size = max(len(holdout) // n_fragments, 4000)
    for i in range(0, len(holdout), chunk_size):
        ch = holdout[i:i + chunk_size]
        if len(ch) >= 1000: chunks.append(ch)
        if len(chunks) >= n_fragments: break
    return train, chunks


def ride(anchor_table, anchor_idx_map, alignment, target_table, anchor_text,
         top_k_ranks=TOP_K_RANKS_PER_TOKEN, top_n_emit=TOP_N_EMITTED_PER_RANK):
    anchor_tokens = tokenize_filtered(anchor_text)
    emitted = Counter()
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        per_rank_mags = []
        for i, row in enumerate(anchor_table):
            mag_sq = row["eigvec_full"][vocab_idx] ** 2
            per_rank_mags.append((i, mag_sq))
        per_rank_mags.sort(key=lambda x: -x[1])
        for table_pos, mag in per_rank_mags[:top_k_ranks]:
            if mag <= 1e-9: break
            if table_pos not in alignment: continue
            target_pos, _ = alignment[table_pos]
            for t in target_table[target_pos]["top_tokens"][:top_n_emit]:
                emitted[t] += 1
    return emitted


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def evaluate_ride(emitted, anchor_freq, target_freq):
    union = list(set(emitted.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emitted.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return {"anchor_affinity": 0.0, "target_affinity": 0.0, "ride_quality": 0.0}
    return {"anchor_affinity": cosine(e_vec, a_vec),
            "target_affinity": cosine(e_vec, t_vec),
            "ride_quality": cosine(e_vec, t_vec) - cosine(e_vec, a_vec)}


def main():
    print(f"=== R-RBS-LM-54m — Poetry vs prose ride benchmark ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Hypothesis: ride works on poetry (compressed) but not prose (dispersed)")
    print(f"Test: ride-quality vs freq-weighted-target baseline per substrate-class pair")

    random.seed(42)
    np.random.seed(42)

    needed = set()
    for p in PAIRS:
        needed.add(p["anchor"])
        needed.add(p["target"])

    kernels = {}; holdouts = {}; freqs = {}
    print(f"\n--- Building kernels (training 90%) ---")
    for key in sorted(needed):
        text = strip_gutenberg(Path(DOMAINS[key]["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        table, vocab, idx_map, freq = build_eigvec_table(train)
        kernels[key] = {"table": table, "vocab": vocab, "idx_map": idx_map, "freq": freq}
        holdouts[key] = probes
        freqs[key] = freq
        cl = DOMAINS[key]["class"]
        print(f"  [{cl:<7s}] {DOMAINS[key]['label']:<24s}: {len(table)} eigvecs; {len(probes)} probes; train={len(train)//1024}K")

    print(f"\n=== Per-pair ride evaluations ===")
    all_results = []
    for pair in PAIRS:
        anchor_key = pair["anchor"]; target_key = pair["target"]
        print(f"\n--- {DOMAINS[anchor_key]['label']} → {DOMAINS[target_key]['label']} ({pair['class_pair']}) ---")
        alignment = find_alignment(kernels[anchor_key]["table"], kernels[target_key]["table"])

        ride_q = []
        identity_q = []
        weighted_target_q = []
        target_vocab = kernels[target_key]["vocab"]
        weights = np.array([freqs[target_key].get(t, 1) for t in target_vocab], dtype=float)
        weights /= weights.sum()

        for probe_text in holdouts[anchor_key]:
            # ride
            emitted = ride(kernels[anchor_key]["table"], kernels[anchor_key]["idx_map"],
                            alignment, kernels[target_key]["table"], probe_text)
            ride_q.append(evaluate_ride(emitted, freqs[anchor_key], freqs[target_key])["ride_quality"])
            # identity baseline (anchor probe tokens as-is)
            atoks = tokenize_filtered(probe_text)
            ident_emit = Counter(atoks)
            identity_q.append(evaluate_ride(ident_emit, freqs[anchor_key], freqs[target_key])["ride_quality"])
            # freq-weighted target baseline
            n_emit = len(atoks) * TOP_K_RANKS_PER_TOKEN * TOP_N_EMITTED_PER_RANK
            rand_idx = np.random.choice(len(target_vocab), size=min(n_emit, 1000), p=weights, replace=True)
            wp = Counter(target_vocab[i] for i in rand_idx)
            weighted_target_q.append(evaluate_ride(wp, freqs[anchor_key], freqs[target_key])["ride_quality"])

        mean_ride = float(np.mean(ride_q))
        mean_id = float(np.mean(identity_q))
        mean_w = float(np.mean(weighted_target_q))
        ride_vs_iden = mean_ride - mean_id
        ride_vs_weighted = mean_ride - mean_w
        print(f"  ride mean:                {mean_ride:+.3f}")
        print(f"  identity baseline:        {mean_id:+.3f}")
        print(f"  freq-weighted-target:     {mean_w:+.3f}")
        print(f"  ride − identity:          {ride_vs_iden:+.3f}   (vocab-switch evidence)")
        print(f"  ride − freq-weighted:     {ride_vs_weighted:+.3f}   (alignment-specific signal)")

        all_results.append({
            "anchor": anchor_key, "target": target_key,
            "class_pair": pair["class_pair"],
            "mean_ride": mean_ride, "mean_identity": mean_id,
            "mean_freq_weighted_target": mean_w,
            "ride_minus_identity": ride_vs_iden,
            "ride_minus_freq_weighted": ride_vs_weighted,
        })

    # Aggregate by class-pair
    print(f"\n=== Aggregate by substrate-class pair ===")
    by_class_pair = {}
    for r in all_results:
        by_class_pair.setdefault(r["class_pair"], []).append(r)
    print(f"  {'class_pair':<18s} {'n':>3s} {'ride':>7s} {'iden':>7s} {'wgt':>7s} {'r−iden':>8s} {'r−wgt':>8s}")
    summaries = {}
    for cp, rs in by_class_pair.items():
        mr = float(np.mean([r["mean_ride"] for r in rs]))
        mi = float(np.mean([r["mean_identity"] for r in rs]))
        mw = float(np.mean([r["mean_freq_weighted_target"] for r in rs]))
        ri = mr - mi; rw = mr - mw
        summaries[cp] = {"n_pairs": len(rs), "ride": mr, "iden": mi, "wgt": mw, "ride_minus_iden": ri, "ride_minus_wgt": rw}
        print(f"  {cp:<18s} {len(rs):>3d} {mr:>+7.3f} {mi:>+7.3f} {mw:>+7.3f} {ri:>+8.3f} {rw:>+8.3f}")

    # Verdict logic
    print(f"\n=== Verdict ===")
    poetry_within = summaries.get("poetry→poetry", {}).get("ride_minus_wgt", 0)
    prose_within = summaries.get("prose→prose", {}).get("ride_minus_wgt", 0)
    delta = poetry_within - prose_within
    print(f"  poetry→poetry ride−freq-wgt: {poetry_within:+.3f}")
    print(f"  prose→prose ride−freq-wgt:   {prose_within:+.3f}")
    print(f"  Δ (poetry advantage):        {delta:+.3f}")

    if poetry_within > 0.05 and prose_within < 0.0:
        verdict = "STRONG substrate-mismatch CONFIRMED: ride works on poetry (beats freq-wgt), fails on prose (loses to freq-wgt)"
    elif delta > 0.10:
        verdict = "MODERATE substrate-mismatch: poetry ride beats prose ride by Δ={:+.3f}".format(delta)
    elif delta > 0.03:
        verdict = "WEAK substrate-mismatch: poetry slightly better but margin small (Δ={:+.3f})".format(delta)
    elif abs(delta) < 0.03:
        verdict = "NO substrate-mismatch: poetry and prose ride perform similarly (Δ={:+.3f}); ride mechanism is substrate-agnostic and limited regardless".format(delta)
    else:
        verdict = "REVERSE: prose ride beats poetry ride (Δ={:+.3f}); user hypothesis NOT supported".format(delta)
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54m",
        "all_pairs": all_results,
        "by_class_pair": summaries,
        "poetry_within_ride_vs_wgt": poetry_within,
        "prose_within_ride_vs_wgt": prose_within,
        "poetry_vs_prose_delta": delta,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54m_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
