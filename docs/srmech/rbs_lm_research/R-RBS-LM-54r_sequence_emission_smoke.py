"""R-RBS-LM-54r — Sequence emission vs bag emission.

Current ride (54g and follow-ups) emits a MULTISET of target tokens.
Bag-evaluation uses target-affinity − anchor-affinity (cosine of
emission distribution vs corpora distributions).

But translation isn't a bag — it's a SEQUENCE. This partition tests
whether ride can preserve the anchor's sequence structure when
projected to target:

Sequence emission mode:
  For each anchor token in order:
    1. Find dominant eigvec rank in anchor
    2. Look up aligned target eigvec
    3. Emit the SINGLE top-magnitude target-vocab token from that eigvec
       (top-1 not top-7; one emission per anchor token)
  Result: ordered sequence of target tokens, length = len(anchor_tokens)

Evaluations:
  (A) Bag-affinity score (same as 54g) on the sequence's multiset
      — should be comparable to bag top-1 mode
  (B) Bigram-coherence: how often adjacent emitted-token pairs appear
      as cooccurring (within distance 5) in the held-out target text,
      compared to a random shuffle of the same emitted tokens
  (C) Trigram-coherence (same with sliding-3 cooccurrence)

If sequence emission preserves target structure, (B) and (C) should
exceed random-shuffle baseline. If not, the ride is fundamentally
position-blind and only bag-mode is meaningful.
"""

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent

DOMAINS = {
    "shakespeare":  {"path": "/tmp/shakespeare.txt",                 "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",               "label": "Milton"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",           "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",             "label": "Quran"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",                "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",              "label": "Plato"},
    "origin":       {"path": "/tmp/origin_species.txt",              "label": "Origin"},
    "whitman":      {"path": "/tmp/whitman.txt",                     "label": "Whitman"},
}

PAIRS = [
    {"anchor": "milton",       "target": "shakespeare",   "note": "rule-dense poetry"},
    {"anchor": "frankenstein", "target": "plato",         "note": "prose→prose"},
    {"anchor": "kjv_nt",       "target": "quran_sale",    "note": "same-fam religious"},
    {"anchor": "whitman",      "target": "milton",        "note": "free-verse anchor"},
    {"anchor": "origin",       "target": "frankenstein",  "note": "prose Victorian"},
]

HOLDOUT_FRACTION = 0.10
N_PROBE_FRAGMENTS = 4
KERNEL_N_EIGVECS = 200
TOP_K_RANKS_PER_TOKEN = 3
BIGRAM_DISTANCE = 5  # cooccurrence window for bigram-coherence

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
    if N < 8: return None, None, None, None, None
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
    if not edges: return None, None, None, None, None
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({"rank": len(ev) - 1 - k, "eigval": float(np.real(ev[k])),
                       "top_tokens": top_tokens, "hypervector": hv, "eigvec_full": eigvec})
    return table, vocab, idx_map, freq, filt


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


def ride_sequence(anchor_table, anchor_idx_map, alignment, target_table, anchor_text):
    """Emit ordered sequence: one target token per anchor token."""
    anchor_tokens = tokenize_filtered(anchor_text)
    sequence = []
    for atok in anchor_tokens:
        if atok not in anchor_idx_map:
            continue
        vocab_idx = anchor_idx_map[atok]
        # Best (highest-magnitude) anchor rank for this token
        best_rank = -1; best_mag = -1
        for i, row in enumerate(anchor_table):
            mag_sq = float(row["eigvec_full"][vocab_idx] ** 2)
            if mag_sq > best_mag:
                best_mag = mag_sq; best_rank = i
        if best_rank < 0 or best_rank not in alignment: continue
        target_pos, _ = alignment[best_rank]
        # Emit top-1 target token from that eigvec
        target_tokens = target_table[target_pos]["top_tokens"]
        if target_tokens:
            sequence.append(target_tokens[0])
    return sequence


def ride_bag_top1(anchor_table, anchor_idx_map, alignment, target_table, anchor_text):
    """Bag mode but top-1 per anchor token, for fair comparison to sequence."""
    return Counter(ride_sequence(anchor_table, anchor_idx_map, alignment, target_table, anchor_text))


def bigram_cooccur_lookup(target_filt, distance=BIGRAM_DISTANCE):
    """Build a dict of how often each token-pair cooccurs within distance in target."""
    pair_count = defaultdict(int)
    for chunk_tokens in target_filt:
        for i in range(len(chunk_tokens)):
            for j in range(i+1, min(i+1+distance, len(chunk_tokens))):
                a, b = chunk_tokens[i], chunk_tokens[j]
                pair_count[(a, b)] += 1
                pair_count[(b, a)] += 1
    return pair_count


def bigram_coherence_score(sequence, target_bigram_lookup):
    """Average bigram cooccurrence count in target for adjacent emitted pairs."""
    if len(sequence) < 2: return 0.0
    scores = []
    for i in range(len(sequence) - 1):
        pair = (sequence[i], sequence[i+1])
        scores.append(target_bigram_lookup.get(pair, 0))
    return float(np.mean(scores))


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def eval_bag(emit, anchor_freq, target_freq):
    if not emit: return 0.0
    union = list(set(emit.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emit.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return 0.0
    return cosine(e_vec, t_vec) - cosine(e_vec, a_vec)


def main():
    print(f"=== R-RBS-LM-54r — Sequence emission vs bag emission ===\n")
    print(f"srmech: {srmech.__version__}")

    random.seed(42); np.random.seed(42)

    needed = set()
    for p in PAIRS:
        needed.add(p["anchor"]); needed.add(p["target"])

    kernels = {}; holdouts = {}
    print(f"\n--- Building kernels (training 90%) ---")
    for key in sorted(needed):
        text = strip_gutenberg(Path(DOMAINS[key]["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        table, vocab, idx_map, freq, filt = build_eigvec_table(train)
        kernels[key] = {"table": table, "vocab": vocab, "idx_map": idx_map, "freq": freq, "filt": filt}
        holdouts[key] = probes
        print(f"  {DOMAINS[key]['label']:<14s}: {len(table)} eigvecs; {len(probes)} probes")

    print(f"\n--- Building target bigram lookup tables ---")
    target_bigrams = {}
    for p in PAIRS:
        if p["target"] not in target_bigrams:
            target_bigrams[p["target"]] = bigram_cooccur_lookup(kernels[p["target"]]["filt"])
            print(f"  {DOMAINS[p['target']]['label']}: {len(target_bigrams[p['target']])} unique pairs")

    print(f"\n=== Per-pair sequence vs bag evaluation ===")
    all_results = []
    for pair in PAIRS:
        anchor_key = pair["anchor"]; target_key = pair["target"]
        ak = kernels[anchor_key]; tk = kernels[target_key]
        alignment = find_alignment(ak["table"], tk["table"])
        bg_lookup = target_bigrams[target_key]

        print(f"\n--- {DOMAINS[anchor_key]['label']} → {DOMAINS[target_key]['label']} ({pair['note']}) ---")

        # Per probe metrics
        seq_bag_scores = []
        seq_bigram_scores = []
        shuffle_bigram_scores = []
        for probe_text in holdouts[anchor_key]:
            sequence = ride_sequence(ak["table"], ak["idx_map"], alignment, tk["table"], probe_text)
            if not sequence:
                continue
            # (A) Bag-evaluation of the sequence as multiset
            bag = Counter(sequence)
            seq_bag_scores.append(eval_bag(bag, ak["freq"], tk["freq"]))
            # (B) Bigram coherence
            seq_bigram_scores.append(bigram_coherence_score(sequence, bg_lookup))
            # (C) Shuffled baseline: same tokens, random order
            shuffled = list(sequence)
            random.shuffle(shuffled)
            shuffle_bigram_scores.append(bigram_coherence_score(shuffled, bg_lookup))

        seq_bag_mean = float(np.mean(seq_bag_scores)) if seq_bag_scores else 0.0
        seq_bg_mean = float(np.mean(seq_bigram_scores)) if seq_bigram_scores else 0.0
        shuf_bg_mean = float(np.mean(shuffle_bigram_scores)) if shuffle_bigram_scores else 0.0
        sequence_lift = seq_bg_mean - shuf_bg_mean

        print(f"  bag-affinity (multiset eval):  {seq_bag_mean:+.3f}")
        print(f"  bigram coherence (sequence):   {seq_bg_mean:.2f}")
        print(f"  bigram coherence (shuffled):   {shuf_bg_mean:.2f}")
        print(f"  sequence lift over shuffle:    {sequence_lift:+.2f}  {'✓' if sequence_lift > 0.5 else (' ' if sequence_lift > -0.5 else '-')}")

        all_results.append({
            "anchor": anchor_key, "target": target_key, "note": pair["note"],
            "seq_bag_affinity": seq_bag_mean,
            "seq_bigram_coherence": seq_bg_mean,
            "shuffle_bigram_coherence": shuf_bg_mean,
            "sequence_lift": sequence_lift,
        })

    # Aggregate
    print(f"\n=== Aggregate ===")
    avg_lift = float(np.mean([r["sequence_lift"] for r in all_results]))
    avg_seq_bg = float(np.mean([r["seq_bigram_coherence"] for r in all_results]))
    avg_shuf_bg = float(np.mean([r["shuffle_bigram_coherence"] for r in all_results]))
    print(f"  Avg sequence bigram coherence: {avg_seq_bg:.2f}")
    print(f"  Avg shuffled  bigram coherence: {avg_shuf_bg:.2f}")
    print(f"  Avg sequence-over-shuffle lift: {avg_lift:+.2f}")

    print(f"\n=== Verdict ===")
    if avg_lift > 2.0:
        verdict = f"SEQUENCE STRUCTURE PRESERVED: ride emits target-coherent sequence (avg lift {avg_lift:+.2f})"
    elif avg_lift > 0.5:
        verdict = f"SEQUENCE STRUCTURE PARTIAL: ride preserves some sequence structure (avg lift {avg_lift:+.2f})"
    elif avg_lift > -0.5:
        verdict = f"SEQUENCE STRUCTURE NONE: ride is position-blind; bag and sequence give same target-coherence (lift {avg_lift:+.2f})"
    else:
        verdict = f"SEQUENCE STRUCTURE NEGATIVE: ride emits SHUFFLED-style output; sequence is worse than random (lift {avg_lift:+.2f})"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54r",
        "per_pair": all_results,
        "avg_sequence_lift": avg_lift,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54r_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
