"""R-RBS-LM-54n — Rule-aware poetry kernel: line-end + within-line bindings.

Per user (2026-05-26): "poetry is rule dense" — not stopword-light, but
RULE-OVERLAY. Each token participates in multiple simultaneous rule
systems (meter / rhyme / line-position / parallelism). Our current
cascade is rule-blind (distance-5 cooccurrence is prose-shaped).

54m surfaced the finding: Milton (rule-dense English blank verse epic)
beats freq-baseline as ride anchor; Whitman (free verse, rule-RELAXED)
fails badly. The rule-density gradient predicts ride success better
than substrate-class (poetry vs prose).

This partition tests: if we build a rule-aware kernel for poetry that
distinguishes within-line cooccurrence from line-end-position
cooccurrence (captures rhyme + parallelism), does:
  (a) Milton's already-positive signal SHARPEN further?
  (b) Whitman's negative signal IMPROVE (because his catalog/parallelism
      structure becomes visible in the line-end graph)?
  (c) Pope's heroic couplets (rhyme + meter) outperform Milton's
      blank verse (meter only)?

Method:
  1. Read raw poetry preserving line breaks.
  2. Build TWO Laplacian eigvec tables per kernel:
     - E_within: cooccurrence within same line (distance-5)
     - E_lineend: cooccurrence between consecutive line-end tokens
                   (captures rhyme + cross-line parallelism)
  3. For each ride pair, build alignments via BOTH tables.
  4. Run ride via both alignment paths.
  5. Compare to 54m baseline (single distance-5 cooccurrence kernel).

If rule-aware kernel works:
  - line-end-based alignment for rhymed poetry (Pope) should beat
    within-line alignment significantly
  - rule-relaxed anchors (Whitman) should improve when line-end graph
    captures his catalog-parallelism
  - rule-blind ride (54m) underestimated rule-dense substrates
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
    "shakespeare":  {"path": "/tmp/shakespeare.txt",                "class": "poetry", "rule_density": "high-meter+rhyme-mix", "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",              "class": "poetry", "rule_density": "high-blank-verse",     "label": "Milton Paradise Lost"},
    "pope_iliad":   {"path": "/tmp/iliad_pope.txt",                 "class": "poetry", "rule_density": "very-high-couplets",   "label": "Pope Iliad"},
    "longfellow":   {"path": "/tmp/longfellow_dante_inferno.txt",   "class": "poetry", "rule_density": "translation-blank",    "label": "Longfellow Inferno"},
    "whitman":      {"path": "/tmp/whitman.txt",                    "class": "poetry", "rule_density": "free-verse-parallel",  "label": "Whitman Leaves"},
    # Prose comparison (no line structure to exploit)
    "frankenstein": {"path": "/tmp/frankenstein.txt",               "class": "prose",  "rule_density": "n/a-prose",            "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",             "class": "prose",  "rule_density": "n/a-prose",            "label": "Plato Republic"},
}

# Ride pairings to test the rule-aware hypothesis
PAIRS = [
    # Rule-dense anchors (predicted: line-end kernel SHARPENS)
    {"anchor": "milton",       "target": "shakespeare",   "note": "blank-verse → mixed"},
    {"anchor": "pope_iliad",   "target": "milton",        "note": "rhymed-couplets → blank-verse"},
    {"anchor": "milton",       "target": "pope_iliad",    "note": "blank-verse → rhymed-couplets"},
    # Rule-relaxed anchor (predicted: line-end kernel RECOVERS via catalog/parallelism)
    {"anchor": "whitman",      "target": "milton",        "note": "free-verse → blank-verse"},
    {"anchor": "whitman",      "target": "pope_iliad",    "note": "free-verse → rhymed"},
    # Translation anchor (predicted: line-end kernel maybe helps)
    {"anchor": "longfellow",   "target": "pope_iliad",    "note": "translation → rhymed"},
    # Poetry → prose (predicted: line-end kernel ineffective; prose has no line)
    {"anchor": "milton",       "target": "frankenstein",  "note": "poetry → prose control"},
    # Prose → prose (predicted: line-end kernel just runs but is uninformative)
    {"anchor": "frankenstein", "target": "plato",         "note": "prose → prose control"},
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


def filter_token(t):
    return t.lower() not in STOPWORDS_EN and len(t) >= 2


def tokenize_line(line):
    raw = re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", line)
    return [t.lower() for t in raw if filter_token(t)]


def strip_gutenberg(text):
    s = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    e = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if s: text = text[s.end():]
    if e: text = text[:e.start()]
    return text.strip()


def split_lines(text):
    """Split into lines, keep non-empty."""
    return [l.strip() for l in text.split("\n") if l.strip()]


def build_dual_eigvec_tables(text, n_eigvecs=KERNEL_N_EIGVECS, M_per_eigvec=21):
    """Build TWO eigvec tables: within-line + line-end-position.
    Returns (table_within, table_lineend, vocab, idx_map, freq).
    """
    lines = split_lines(text)
    per_line_tokens = [tokenize_line(l) for l in lines]
    per_line_tokens = [toks for toks in per_line_tokens if toks]  # drop empty

    all_t = [t for toks in per_line_tokens for t in toks]
    freq = Counter(all_t)
    N = min(n_eigvecs, len(freq))
    if N < 8: return None, None, None, None, None
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}

    # Within-line graph: tokens cooccurring within distance-5 in same line
    edges_within = Counter()
    for toks in per_line_tokens:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i+1, min(i+5, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges_within[(min(a,b), max(a,b))] += 1

    # Line-end graph: tokens at end-of-line, cooccurring with end-of-next-line tokens
    line_end_tokens = []
    for toks in per_line_tokens:
        # last 2 tokens of each line (covers end-of-line rhyme position window)
        for t in toks[-2:]:
            if t in idx_map:
                line_end_tokens.append(idx_map[t])
                break
    edges_lineend = Counter()
    # Adjacent line-end tokens (captures rhyme, alliteration, parallelism)
    for i in range(len(line_end_tokens) - 1):
        a, b = line_end_tokens[i], line_end_tokens[i+1]
        if a == b: continue
        edges_lineend[(min(a,b), max(a,b))] += 1
    # Also distance-2 (couplet-spanning) and distance-3 (quatrain) connections
    for d in (2, 3, 4):
        for i in range(len(line_end_tokens) - d):
            a, b = line_end_tokens[i], line_end_tokens[i+d]
            if a == b: continue
            edges_lineend[(min(a,b), max(a,b))] += 1

    def build_table(edges_counter):
        if not edges_counter: return None
        L = dense_laplacian(N, list(edges_counter.keys()), [float(w) for w in edges_counter.values()])
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
        return table

    return build_table(edges_within), build_table(edges_lineend), vocab, idx_map, freq


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


def ride(anchor_table, anchor_idx_map, alignment, target_table, anchor_text):
    anchor_tokens = tokenize_line(anchor_text)
    emitted = Counter()
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        per_rank_mags = []
        for i, row in enumerate(anchor_table):
            mag_sq = row["eigvec_full"][vocab_idx] ** 2
            per_rank_mags.append((i, mag_sq))
        per_rank_mags.sort(key=lambda x: -x[1])
        for table_pos, mag in per_rank_mags[:TOP_K_RANKS_PER_TOKEN]:
            if mag <= 1e-9: break
            if table_pos not in alignment: continue
            target_pos, _ = alignment[table_pos]
            for t in target_table[target_pos]["top_tokens"][:TOP_N_EMITTED_PER_RANK]:
                emitted[t] += 1
    return emitted


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def eval_ride(emitted, anchor_freq, target_freq):
    union = list(set(emitted.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emitted.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return 0.0
    return cosine(e_vec, t_vec) - cosine(e_vec, a_vec)


def main():
    print(f"=== R-RBS-LM-54n — Rule-aware poetry kernel ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Two parallel cascades: within-line cooccurrence + line-end position")

    random.seed(42)
    np.random.seed(42)

    needed = set()
    for p in PAIRS:
        needed.add(p["anchor"])
        needed.add(p["target"])

    kernels = {}
    holdouts = {}
    print(f"\n--- Building dual-eigvec tables (within-line + line-end) ---")
    for key in sorted(needed):
        text = strip_gutenberg(Path(DOMAINS[key]["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        tw, te, vocab, idx_map, freq = build_dual_eigvec_tables(train)
        if tw is None:
            print(f"  [SKIP] {DOMAINS[key]['label']:<24s}: insufficient data")
            continue
        kernels[key] = {"within": tw, "lineend": te, "vocab": vocab, "idx_map": idx_map, "freq": freq}
        holdouts[key] = probes
        te_status = "OK" if te is not None else "EMPTY (prose / no line breaks)"
        print(f"  {DOMAINS[key]['label']:<24s} [{DOMAINS[key]['rule_density']:<24s}]: within={len(tw)}; lineend={te_status if te is None else len(te)}; {len(probes)} probes")

    print(f"\n=== Per-pair ride evaluations (within-line vs line-end vs 54m baseline) ===")
    all_results = []
    for pair in PAIRS:
        anchor_key = pair["anchor"]; target_key = pair["target"]
        if anchor_key not in kernels or target_key not in kernels: continue
        ak = kernels[anchor_key]; tk = kernels[target_key]
        print(f"\n--- {DOMAINS[anchor_key]['label']} → {DOMAINS[target_key]['label']} ({pair['note']}) ---")

        # Within-line alignment + ride
        align_within = find_alignment(ak["within"], tk["within"])
        # Line-end alignment + ride (only if both kernels have line-end table)
        align_lineend = find_alignment(ak["lineend"], tk["lineend"]) if (ak["lineend"] is not None and tk["lineend"] is not None) else None

        within_scores = []
        lineend_scores = []
        weighted_baseline_scores = []
        target_vocab = tk["vocab"]
        weights = np.array([tk["freq"].get(t, 1) for t in target_vocab], dtype=float)
        weights /= weights.sum()

        for probe_text in holdouts[anchor_key]:
            # within-line ride
            emit_w = ride(ak["within"], ak["idx_map"], align_within, tk["within"], probe_text)
            within_scores.append(eval_ride(emit_w, ak["freq"], tk["freq"]))
            # line-end ride
            if align_lineend is not None:
                emit_e = ride(ak["lineend"], ak["idx_map"], align_lineend, tk["lineend"], probe_text)
                lineend_scores.append(eval_ride(emit_e, ak["freq"], tk["freq"]))
            # freq-weighted baseline
            atoks = tokenize_line(probe_text)
            n_emit = len(atoks) * TOP_K_RANKS_PER_TOKEN * TOP_N_EMITTED_PER_RANK
            rand_idx = np.random.choice(len(target_vocab), size=min(n_emit, 1000), p=weights, replace=True)
            wp = Counter(target_vocab[i] for i in rand_idx)
            weighted_baseline_scores.append(eval_ride(wp, ak["freq"], tk["freq"]))

        mw = float(np.mean(within_scores))
        me = float(np.mean(lineend_scores)) if lineend_scores else None
        mb = float(np.mean(weighted_baseline_scores))
        w_vs_baseline = mw - mb
        e_vs_baseline = (me - mb) if me is not None else None
        e_vs_w = (me - mw) if me is not None else None
        print(f"  within-line ride:           {mw:+.3f}")
        if me is not None:
            print(f"  line-end ride:              {me:+.3f}")
        print(f"  freq-weighted baseline:     {mb:+.3f}")
        print(f"  within − baseline:          {w_vs_baseline:+.3f}")
        if e_vs_baseline is not None:
            print(f"  line-end − baseline:        {e_vs_baseline:+.3f}   ← key rule-aware signal")
            print(f"  line-end − within:          {e_vs_w:+.3f}   ← rule-aware lift")

        all_results.append({
            "anchor": anchor_key, "target": target_key, "note": pair["note"],
            "within_ride": mw, "lineend_ride": me, "freq_baseline": mb,
            "within_minus_baseline": w_vs_baseline,
            "lineend_minus_baseline": e_vs_baseline,
            "lineend_minus_within": e_vs_w,
        })

    # Aggregate
    print(f"\n=== Aggregate by anchor rule-density ===")
    by_anchor = {}
    for r in all_results:
        key = (r["anchor"], DOMAINS[r["anchor"]]["rule_density"])
        by_anchor.setdefault(key, []).append(r)
    print(f"  {'anchor':<18s} {'rule_density':<22s} {'wn−b':>7s} {'le−b':>7s} {'le−wn':>7s}")
    summaries = []
    for (anchor, rd), rs in by_anchor.items():
        wnb_avg = float(np.mean([r["within_minus_baseline"] for r in rs]))
        leb_avg = float(np.mean([r["lineend_minus_baseline"] for r in rs if r["lineend_minus_baseline"] is not None])) if any(r["lineend_minus_baseline"] is not None for r in rs) else None
        lew_avg = float(np.mean([r["lineend_minus_within"] for r in rs if r["lineend_minus_within"] is not None])) if any(r["lineend_minus_within"] is not None for r in rs) else None
        summaries.append({"anchor": anchor, "rule_density": rd, "wn_baseline": wnb_avg, "le_baseline": leb_avg, "le_within": lew_avg, "n": len(rs)})
        wnb_str = f"{wnb_avg:+.3f}"
        leb_str = f"{leb_avg:+.3f}" if leb_avg is not None else "  n/a"
        lew_str = f"{lew_avg:+.3f}" if lew_avg is not None else "  n/a"
        print(f"  {anchor:<18s} {rd:<22s} {wnb_str:>7s} {leb_str:>7s} {lew_str:>7s}")

    # Verdict
    print(f"\n=== Verdict ===")
    lift_per_anchor = [(s["anchor"], s["rule_density"], s["le_within"]) for s in summaries if s["le_within"] is not None]
    if not lift_per_anchor:
        verdict = "INCONCLUSIVE: no anchor with both within + line-end kernels"
    else:
        positive_lift = [s for s in lift_per_anchor if s[2] > 0.02]
        negative_lift = [s for s in lift_per_anchor if s[2] < -0.02]
        if len(positive_lift) >= 2:
            verdict = f"RULE-AWARE KERNEL HELPS: {len(positive_lift)}/{len(lift_per_anchor)} anchors gain alignment-specific signal (avg lift +{np.mean([s[2] for s in positive_lift]):.3f})"
        elif len(positive_lift) == 1:
            verdict = f"MIXED: only {positive_lift[0][0]} ({positive_lift[0][1]}) gains; others flat or worse"
        elif len(negative_lift) > len(positive_lift):
            verdict = "RULE-AWARE KERNEL HURTS: line-end signal is noisier than within-line for most anchors"
        else:
            verdict = "RULE-AWARE KERNEL NEUTRAL: line-end and within-line equivalent; line-end may need finer rule-decomposition"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54n",
        "per_pair": all_results,
        "by_anchor": summaries,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54n_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
