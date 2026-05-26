"""R-RBS-LM-54s — Print sample emitted sequences from Golden Path tripartition.

All prior 54-arc emission tests scored via cosine over distributions or
bigram cooccurrence. None of them actually *printed* a paragraph for
inspection. This partition closes that gap.

Architecture used: best 54q variant (T4 meta-subtraction + G4
multiplicative gating) plus 54r-style sequence emission.

The tripartition (per Golden Path):
  1. DOMAIN anchor — find target kernel by structural fingerprint (54f)
  2. Find-cascade  — align anchor eigvecs to target eigvecs by content
                     similarity (54c)
  3. Ride-cascade  — for each anchor token, emit top-1 target token from
                     aligned eigvec, preserving sequence order (54r)
  +  Freq-gating (G4 sqrt(ride × freq)) for token-selection variant

Output: for each pair, print the anchor probe text and the emitted
target-vocab sequence. User-inspectable.

Honest scope: this is NOT a benchmark; this is a printout. The reader
judges whether the emitted text "looks like" the target style. If yes,
the Golden Path is producing recognizable output. If no, we know what
the next iteration target is.
"""

import json
import random
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent

DOMAINS = {
    "shakespeare":  {"path": "/tmp/shakespeare.txt",         "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",       "label": "Milton (Paradise Lost)"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",   "label": "KJV New Testament"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",     "label": "Quran (Yusuf Ali)"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",        "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",      "label": "Plato Republic"},
    "origin":       {"path": "/tmp/origin_species.txt",      "label": "Origin of Species"},
}

PAIRS = [
    {"anchor": "milton",       "target": "shakespeare",  "intermediate": "kjv_nt",        "meta": "frankenstein", "note": "best 54q pair"},
    {"anchor": "kjv_nt",       "target": "quran_sale",   "intermediate": "milton",         "meta": "frankenstein", "note": "religious same-family"},
    {"anchor": "frankenstein", "target": "plato",        "intermediate": "origin",         "meta": "shakespeare",  "note": "prose triangulation"},
    {"anchor": "shakespeare",  "target": "milton",       "intermediate": "kjv_nt",        "meta": "frankenstein", "note": "poetry reverse"},
]

HOLDOUT_FRACTION = 0.10
N_PROBES_PER_PAIR = 2
KERNEL_N_EIGVECS = 200
TOP_K_RANKS = 3
TOP_N_EMIT_BAG = 7
# Generate ~80-token sequences per probe for readable output
MAX_SEQUENCE_LENGTH = 80

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
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({"rank": len(ev) - 1 - k, "eigval": float(np.real(ev[k])),
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


def split_holdout(text, n_fragments=4, holdout_frac=HOLDOUT_FRACTION):
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


def ride_sequence_top1(anchor_table, anchor_idx_map, alignment, target_table, anchor_text):
    """For each anchor token, emit single target token (top-1 from aligned eigvec)."""
    anchor_tokens = tokenize_filtered(anchor_text)
    sequence = []
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        best_rank = -1; best_mag = -1.0
        for i, row in enumerate(anchor_table):
            mag_sq = float(row["eigvec_full"][vocab_idx] ** 2)
            if mag_sq > best_mag:
                best_mag = mag_sq; best_rank = i
        if best_rank < 0 or best_rank not in alignment: continue
        target_pos, _ = alignment[best_rank]
        target_tokens = target_table[target_pos]["top_tokens"]
        if target_tokens:
            sequence.append(target_tokens[0])
    return sequence


def ride_sequence_g4_freq_weighted(anchor_table, anchor_idx_map, alignment, target_table,
                                    target_freq, anchor_text):
    """G4-gated variant: for each anchor token, emit target token whose
    score = sqrt(emission_strength * target_freq) is highest."""
    anchor_tokens = tokenize_filtered(anchor_text)
    sequence = []
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        best_rank = -1; best_mag = -1.0
        for i, row in enumerate(anchor_table):
            mag_sq = float(row["eigvec_full"][vocab_idx] ** 2)
            if mag_sq > best_mag:
                best_mag = mag_sq; best_rank = i
        if best_rank < 0 or best_rank not in alignment: continue
        target_pos, _ = alignment[best_rank]
        target_tokens = target_table[target_pos]["top_tokens"]
        if not target_tokens: continue
        # Pick target token with highest G4 score: sqrt(rank_position_strength * target_freq)
        # rank_position_strength: top-1 gets weight 7, top-2 gets 6, ..., top-7 gets 1
        # then multiplied by target_freq[token]
        scored = []
        for pos, t in enumerate(target_tokens[:7]):
            strength = 7 - pos  # 7 for top, decaying
            tf = target_freq.get(t, 1)
            g4_score = float(np.sqrt(strength * tf))
            scored.append((t, g4_score))
        scored.sort(key=lambda x: -x[1])
        sequence.append(scored[0][0])
    return sequence


def ride_sequence_t4_g4(anchor_table, anchor_idx_map, alignment_AT, target_table,
                         alignment_AM, meta_table, target_freq, meta_freq,
                         anchor_text):
    """Best 54q variant: T4 meta-subtraction + G4 gating, sequence mode.

    For each anchor token: get target candidate via AT alignment;
    subtract meta-baseline contribution (T4); apply G4 freq weighting.
    Pick highest-scoring target token.
    """
    anchor_tokens = tokenize_filtered(anchor_text)
    sequence = []
    total_meta = sum(meta_freq.values())
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        best_rank = -1; best_mag = -1.0
        for i, row in enumerate(anchor_table):
            mag_sq = float(row["eigvec_full"][vocab_idx] ** 2)
            if mag_sq > best_mag:
                best_mag = mag_sq; best_rank = i
        if best_rank < 0 or best_rank not in alignment_AT: continue
        target_pos, align_sim = alignment_AT[best_rank]
        target_tokens = target_table[target_pos]["top_tokens"]
        if not target_tokens: continue
        # T4 + G4 scoring: residual after meta-subtraction, then G4-blended
        scored = []
        for pos, t in enumerate(target_tokens[:7]):
            strength = 7 - pos
            tf = target_freq.get(t, 1)
            mf = meta_freq.get(t, 0) / max(total_meta, 1)
            # T4 residual: strength - alpha * expected_meta_share
            residual = max(strength - 0.5 * mf * 7, 0.1)
            # G4 blend
            g4_score = float(np.sqrt(residual * tf))
            scored.append((t, g4_score))
        scored.sort(key=lambda x: -x[1])
        sequence.append(scored[0][0])
    return sequence


def main():
    print(f"=== R-RBS-LM-54s — Print sample emitted sequences ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Architecture: tripartition (DOMAIN-anchor + find-cascade + ride-cascade)")
    print(f"Variants printed: top-1 raw / G4-freq-weighted / T4+G4 (best 54q)\n")

    random.seed(42); np.random.seed(42)

    needed = set()
    for p in PAIRS:
        for role in ["anchor", "target", "intermediate", "meta"]:
            needed.add(p[role])

    kernels = {}; holdouts = {}
    print(f"--- Building kernels ---")
    for key in sorted(needed):
        text = strip_gutenberg(Path(DOMAINS[key]["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        table, vocab, idx_map, freq = build_eigvec_table(train)
        kernels[key] = {"table": table, "vocab": vocab, "idx_map": idx_map, "freq": freq}
        holdouts[key] = probes
        print(f"  {DOMAINS[key]['label']:<26s}: {len(table)} eigvecs; {len(probes)} probes")

    print(f"\n{'='*78}")
    print(f"=== SAMPLE EMITTED SEQUENCES (anchor probe → ride variants → target) ===")
    print(f"{'='*78}\n")

    all_results = []
    for pair in PAIRS:
        ak = kernels[pair["anchor"]]
        tk = kernels[pair["target"]]
        mk = kernels[pair["meta"]]
        align_AT = find_alignment(ak["table"], tk["table"])
        align_AM = find_alignment(ak["table"], mk["table"])

        print(f"\n{'─'*78}")
        print(f"PAIR: {DOMAINS[pair['anchor']]['label']} → {DOMAINS[pair['target']]['label']}")
        print(f"      meta-kernel for T4: {DOMAINS[pair['meta']]['label']}")
        print(f"      note: {pair['note']}")
        print(f"{'─'*78}")

        for p_idx, probe_text in enumerate(holdouts[pair["anchor"]][:N_PROBES_PER_PAIR]):
            anchor_tokens = tokenize_filtered(probe_text)
            anchor_token_count = len(anchor_tokens)
            # Limit anchor probe to MAX_SEQUENCE_LENGTH tokens for readability
            anchor_truncated = " ".join(anchor_tokens[:MAX_SEQUENCE_LENGTH])

            print(f"\n  --- probe {p_idx} ---")
            print(f"\n  ANCHOR TEXT ({anchor_token_count} filtered tokens; first {min(MAX_SEQUENCE_LENGTH, anchor_token_count)} shown):")
            print(f"    {anchor_truncated}")

            # V1: top-1 raw sequence
            seq_top1 = ride_sequence_top1(ak["table"], ak["idx_map"], align_AT, tk["table"], anchor_truncated)
            print(f"\n  RIDE [V1 top-1 raw]:")
            print(f"    {' '.join(seq_top1[:MAX_SEQUENCE_LENGTH])}")

            # V2: G4 freq-weighted sequence
            seq_g4 = ride_sequence_g4_freq_weighted(ak["table"], ak["idx_map"], align_AT,
                                                     tk["table"], tk["freq"], anchor_truncated)
            print(f"\n  RIDE [V2 G4 freq-weighted]:")
            print(f"    {' '.join(seq_g4[:MAX_SEQUENCE_LENGTH])}")

            # V3: T4+G4 best 54q variant
            seq_t4g4 = ride_sequence_t4_g4(ak["table"], ak["idx_map"], align_AT, tk["table"],
                                           align_AM, mk["table"], tk["freq"], mk["freq"],
                                           anchor_truncated)
            print(f"\n  RIDE [V3 T4+G4 (best 54q)]:")
            print(f"    {' '.join(seq_t4g4[:MAX_SEQUENCE_LENGTH])}")

            all_results.append({
                "pair": f"{pair['anchor']}->{pair['target']}",
                "probe_idx": p_idx,
                "anchor_tokens": anchor_tokens[:MAX_SEQUENCE_LENGTH],
                "seq_top1": seq_top1[:MAX_SEQUENCE_LENGTH],
                "seq_g4": seq_g4[:MAX_SEQUENCE_LENGTH],
                "seq_t4g4": seq_t4g4[:MAX_SEQUENCE_LENGTH],
            })

    print(f"\n\n{'='*78}")
    print(f"=== Reader-side observation ===")
    print(f"{'='*78}\n")
    print(f"This is NOT a benchmark. It's a printout for human inspection.")
    print(f"Ask yourself: does the V3 (T4+G4) emission for any pair 'look like' the")
    print(f"target corpus's style? Do you see target-vocab words appearing in")
    print(f"target-typical phrases?")
    print(f"")
    print(f"Honest expectation given 54g/54r/54q metrics:")
    print(f"  - Tokens WILL be from target vocabulary (vocabulary-switch works)")
    print(f"  - Sequence MIGHT have target-typical bigrams (54r showed +9.90 on Milton→Shakespeare)")
    print(f"  - Output WILL NOT read like fluent sentences (we have no syntactic model)")
    print(f"  - Output IS a structural projection, not a learned generation")
    print(f"")
    print(f"What's MISSING for fluent generation (forward roadmap):")
    print(f"  - Position-aware target-eigvec selection (use anchor token POSITION in source)")
    print(f"  - Multi-token lookahead (emit target bigram given anchor bigram context)")
    print(f"  - Syntactic class preservation (noun→noun, verb→verb via additional eigvec layer)")
    print(f"  - Function-word interpolation (we filtered stopwords; emission lacks them)")

    out = {
        "partition": "R-RBS-LM-54s",
        "scope": "Print sample emissions for human inspection",
        "samples": all_results,
    }
    out_path = HERE / "R-RBS-LM-54s_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
