"""R-RBS-LM-54g — Closed-loop ride: emit real target-vocabulary tokens.

54d measured structural alignment quality but did NOT emit tokens.
This partition closes the loop: given an anchor fragment, project it
through the alignment into target's vocabulary, and measure whether
the emitted token bag is closer to target's distribution than to
anchor's.

Method (per Golden Path):
  1. Build kernels from training portions of each corpus (offline).
  2. Build find-cascade alignment: anchor eigvec i ↔ target eigvec j
     (content-similarity match — 54c methodology).
  3. For each anchor probe fragment:
     a. For each anchor token, find dominant anchor eigvec ranks
        (where the token has the largest squared-magnitude component).
     b. For each dominant rank, lookup aligned target eigvec.
     c. Emit top-N tokens from each aligned target eigvec.
     d. Bag-collect all emitted target tokens.
  4. Score the emitted bag two ways:
     - anchor-affinity: cosine to anchor-corpus token-frequency vector
     - target-affinity: cosine to target-corpus token-frequency vector
     - ride-quality = target-affinity − anchor-affinity
       (positive ⇒ ride moves output toward target language)

Baselines:
  - random-target: emit random tokens from target vocab
  - identity (no ride): emit the anchor probe tokens themselves
  - target-uniform: emit uniformly from target vocab

The honest negative: if ride-quality near 0, the alignment doesn't
carry enough signal to actually translate at the token level.
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

# Three pairings to test ride direction
PAIRS = [
    {"anchor": "kjv_nt",      "target": "quran_sale",   "family_relation": "same-family (abrahamic)"},
    {"anchor": "kjv_nt",      "target": "bhagavad",     "family_relation": "cross-super-family (religious eastern)"},
    {"anchor": "kjv_nt",      "target": "frankenstein", "family_relation": "cross-substrate (religious→novel)"},
    {"anchor": "plato",       "target": "frankenstein", "family_relation": "cross-substrate-secular (philos→novel)"},
]

DOMAINS = {
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt", "family": "religious_abrahamic", "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",   "family": "religious_abrahamic", "label": "Quran-Sale"},
    "bhagavad":     {"path": "/tmp/bhagavad_gita.txt",     "family": "religious_eastern",   "label": "Bhagavad Gita"},
    "origin":       {"path": "/tmp/origin_species.txt",    "family": "secular_science",     "label": "Origin of Species"},
    "plato":        {"path": "/tmp/plato_republic.txt",    "family": "secular_philosophy",  "label": "Plato Republic"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",      "family": "secular_novel",       "label": "Frankenstein"},
}

HOLDOUT_FRACTION = 0.10
N_PROBE_FRAGMENTS = 4
KERNEL_N_EIGVECS = 200
TOP_K_RANKS_PER_TOKEN = 3   # for each anchor token, look at top-3 eigvec ranks where it has highest magnitude
TOP_N_EMITTED_PER_RANK = 7  # for each aligned target eigvec, emit top-7 tokens

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
    """Build eigvec table with rich content for ride lookups.
    Returns: (table list, vocab list, eigvec_matrix (N x N)).
    """
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
        alignment[i] = (best_j, float(best_sim))  # using positional i, not table_A[i]["rank"]
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


def freq_to_normalized(freq, vocab):
    """Convert Counter to L1-normalized distribution over the union vocab."""
    total = sum(freq.get(t, 0) for t in vocab) or 1
    return np.array([freq.get(t, 0) / total for t in vocab], dtype=float)


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def ride(anchor_table, anchor_idx_map, alignment, target_table,
         anchor_text, top_k_ranks=TOP_K_RANKS_PER_TOKEN,
         top_n_emit=TOP_N_EMITTED_PER_RANK):
    """Closed-loop ride: anchor_text → emitted target token bag."""
    anchor_tokens = tokenize_filtered(anchor_text)
    # Need eigvec_full for each anchor rank. Re-extract from table.
    # anchor_table[i]["eigvec_full"] is the eigenvector at table position i.
    emitted = Counter()
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        # Find top-K ranks (table positions) where this token has largest squared magnitude
        per_rank_mags = []
        for i, row in enumerate(anchor_table):
            mag_sq = row["eigvec_full"][vocab_idx] ** 2
            per_rank_mags.append((i, mag_sq))
        per_rank_mags.sort(key=lambda x: -x[1])
        for table_pos, mag in per_rank_mags[:top_k_ranks]:
            if mag <= 1e-9: break
            if table_pos not in alignment: continue
            target_pos, _ = alignment[table_pos]
            target_tokens = target_table[target_pos]["top_tokens"][:top_n_emit]
            for t in target_tokens:
                emitted[t] += 1
    return emitted


def evaluate_ride(emitted, anchor_freq, target_freq):
    """Compute ride-quality = cos(emitted, target) − cos(emitted, anchor)."""
    # Union vocab over all three
    union = list(set(emitted.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emitted.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return {"anchor_affinity": 0.0, "target_affinity": 0.0, "ride_quality": 0.0}
    anchor_aff = cosine(e_vec, a_vec)
    target_aff = cosine(e_vec, t_vec)
    return {"anchor_affinity": anchor_aff,
            "target_affinity": target_aff,
            "ride_quality": target_aff - anchor_aff}


def main():
    print(f"=== R-RBS-LM-54g — Closed-loop ride: emit target tokens ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Holdout: {HOLDOUT_FRACTION:.0%}; probes per corpus: {N_PROBE_FRAGMENTS}")
    print(f"Top-K ranks per anchor token: {TOP_K_RANKS_PER_TOKEN}; emit-N per rank: {TOP_N_EMITTED_PER_RANK}")

    random.seed(42)
    np.random.seed(42)

    # Build all needed kernels + holdouts up front
    needed = set()
    for p in PAIRS:
        needed.add(p["anchor"])
        needed.add(p["target"])
    kernels = {}
    holdouts = {}
    freqs = {}
    print(f"\n--- Building kernels (training 90%) ---")
    for key in sorted(needed):
        text = strip_gutenberg(Path(DOMAINS[key]["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        table, vocab, idx_map, freq = build_eigvec_table(train)
        kernels[key] = {"table": table, "vocab": vocab, "idx_map": idx_map, "freq": freq}
        holdouts[key] = probes
        freqs[key] = freq
        print(f"  {DOMAINS[key]['label']:<22s}: kernel {len(table)} eigvecs; {len(probes)} probes")

    # Run each pairing
    print(f"\n=== Ride evaluations ===")
    all_results = []
    for pair in PAIRS:
        anchor_key = pair["anchor"]; target_key = pair["target"]
        print(f"\n--- {DOMAINS[anchor_key]['label']} → {DOMAINS[target_key]['label']} ({pair['family_relation']}) ---")

        # Build alignment between anchor kernel and target kernel
        alignment = find_alignment(kernels[anchor_key]["table"], kernels[target_key]["table"])

        # Run ride on each anchor probe fragment
        ride_qualities = []
        for p_idx, probe_text in enumerate(holdouts[anchor_key]):
            emitted = ride(kernels[anchor_key]["table"],
                            kernels[anchor_key]["idx_map"],
                            alignment,
                            kernels[target_key]["table"],
                            probe_text)
            score = evaluate_ride(emitted, freqs[anchor_key], freqs[target_key])
            ride_qualities.append(score["ride_quality"])
            print(f"  probe {p_idx}: emitted={sum(emitted.values())} tokens, "
                  f"anchor-aff={score['anchor_affinity']:+.3f}, "
                  f"target-aff={score['target_affinity']:+.3f}, "
                  f"ride-quality={score['ride_quality']:+.3f}")

        # Baseline 1: identity (no ride; just use anchor probe tokens directly)
        baseline_identity = []
        for probe_text in holdouts[anchor_key]:
            atoks = tokenize_filtered(probe_text)
            ident_emit = Counter(atoks)
            score = evaluate_ride(ident_emit, freqs[anchor_key], freqs[target_key])
            baseline_identity.append(score["ride_quality"])

        # Baseline 2: random tokens from target vocab
        target_vocab = kernels[target_key]["vocab"]
        baseline_random_target = []
        for probe_text in holdouts[anchor_key]:
            atoks = tokenize_filtered(probe_text)
            n_emit_typical = len(atoks) * TOP_K_RANKS_PER_TOKEN * TOP_N_EMITTED_PER_RANK
            rand_picks = random.choices(target_vocab, k=min(n_emit_typical, 1000))
            rand_emit = Counter(rand_picks)
            score = evaluate_ride(rand_emit, freqs[anchor_key], freqs[target_key])
            baseline_random_target.append(score["ride_quality"])

        # Baseline 3: target-frequency-weighted random (smarter random)
        weights = np.array([freqs[target_key].get(t, 1) for t in target_vocab], dtype=float)
        weights /= weights.sum()
        baseline_weighted_target = []
        for probe_text in holdouts[anchor_key]:
            atoks = tokenize_filtered(probe_text)
            n_emit_typical = len(atoks) * TOP_K_RANKS_PER_TOKEN * TOP_N_EMITTED_PER_RANK
            rand_idx = np.random.choice(len(target_vocab), size=min(n_emit_typical, 1000), p=weights, replace=True)
            wp = Counter(target_vocab[i] for i in rand_idx)
            score = evaluate_ride(wp, freqs[anchor_key], freqs[target_key])
            baseline_weighted_target.append(score["ride_quality"])

        mean_ride = float(np.mean(ride_qualities))
        mean_id = float(np.mean(baseline_identity))
        mean_rand = float(np.mean(baseline_random_target))
        mean_weighted = float(np.mean(baseline_weighted_target))
        print(f"  ride mean quality:                {mean_ride:+.3f}")
        print(f"  baseline (no ride, identity):     {mean_id:+.3f}")
        print(f"  baseline (random target vocab):   {mean_rand:+.3f}")
        print(f"  baseline (freq-weighted target):  {mean_weighted:+.3f}")
        improv_over_identity = mean_ride - mean_id
        print(f"  ride − identity (genuine xlation): {improv_over_identity:+.3f}")

        all_results.append({
            "anchor": anchor_key,
            "target": target_key,
            "family_relation": pair["family_relation"],
            "ride_qualities": ride_qualities,
            "mean_ride": mean_ride,
            "mean_identity": mean_id,
            "mean_random_target": mean_rand,
            "mean_freq_weighted_target": mean_weighted,
            "improvement_over_identity": improv_over_identity,
        })

    # Aggregate verdict
    print(f"\n=== Cross-pair summary ===")
    print(f"  {'pair':<35s} {'ride':>7s} {'iden':>7s} {'rand':>7s} {'wgt':>7s} {'ride−iden':>10s}")
    for r in all_results:
        tag = f"{DOMAINS[r['anchor']]['label']}→{DOMAINS[r['target']]['label']}"[:35]
        print(f"  {tag:<35s} {r['mean_ride']:>+7.3f} {r['mean_identity']:>+7.3f} "
              f"{r['mean_random_target']:>+7.3f} {r['mean_freq_weighted_target']:>+7.3f} "
              f"{r['improvement_over_identity']:>+10.3f}")

    print(f"\n=== Verdict ===")
    avg_improv = float(np.mean([r["improvement_over_identity"] for r in all_results]))
    if avg_improv > 0.2:
        verdict = f"STRONG ride: avg ride-iden improvement +{avg_improv:.3f}; closed-loop translation works"
    elif avg_improv > 0.05:
        verdict = f"MODERATE ride: avg improvement +{avg_improv:.3f}; ride pushes output toward target but not dramatically"
    elif avg_improv > -0.05:
        verdict = f"NEUTRAL ride: ride-iden ≈ 0 (avg {avg_improv:+.3f}); ride does NOT meaningfully translate at token level"
    else:
        verdict = f"NEGATIVE ride: avg {avg_improv:+.3f}; ride is actively wrong; need different ride mechanism"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54g",
        "pairs": all_results,
        "avg_improvement_over_identity": avg_improv,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54g_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
