"""R-RBS-LM-54j — Multi-step ride with freq-weighted gating.

Per user 2026-05-26: "ride might be one of more than one step with
freq weighted somehow that help decide."

54g showed ride loses to freq-weighted-target baseline. The freq
baseline isn't the enemy; it's a participant. This partition tests
gating strategies that COMBINE ride emission with freq-weighted
target, instead of treating them as competitors.

Gating strategies tested:
  G0  pure ride (54g baseline)
  G1a ride × target_freq^0.5   (mild freq tilt — let freq guide ride choices)
  G1b ride × target_freq^1.0   (equal weight)
  G1c ride × target_freq^2.0   (heavy freq tilt — close to baseline)
  G2  ride / target_freq       (anti-freq — boost rare alignment-specific)
  G3  ride − freq_baseline_expected (background subtraction)
  G4  sqrt(ride × target_freq) (geometric mean — multiplicative blend)

For each gating, ride INTENSITY is conserved by L1-normalizing the
emission distribution before evaluation. The metric is still
ride-quality minus freq-weighted-target baseline (alignment-specific
signal).

Hypothesis: G2 (anti-freq) and G3 (background subtraction) should
isolate the alignment-specific signal that 54g showed exists but
gets swamped. The natural co-design with freq-weighted is at the
ranking layer, not the emission layer.
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
    "shakespeare":  {"path": "/tmp/shakespeare.txt",                 "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",               "label": "Milton"},
    "whitman":      {"path": "/tmp/whitman.txt",                     "label": "Whitman"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",           "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",             "label": "Quran"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",                "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",              "label": "Plato"},
    "origin":       {"path": "/tmp/origin_species.txt",              "label": "Origin"},
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


def ride_uniform(anchor_table, anchor_idx_map, alignment, target_table, anchor_text):
    """Baseline 54g ride: uniform weight, top-7."""
    anchor_tokens = tokenize_filtered(anchor_text)
    emitted = Counter()
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        per_rank_mags = []
        for i, row in enumerate(anchor_table):
            mag_sq = float(row["eigvec_full"][vocab_idx] ** 2)
            per_rank_mags.append((i, mag_sq))
        per_rank_mags.sort(key=lambda x: -x[1])
        for table_pos, mag in per_rank_mags[:TOP_K_RANKS_PER_TOKEN]:
            if mag <= 1e-9: break
            if table_pos not in alignment: continue
            target_pos, _ = alignment[table_pos]
            for t in target_table[target_pos]["top_tokens"][:TOP_N_EMITTED_PER_RANK]:
                emitted[t] += 1.0
    return emitted


def gate(emitted, target_freq, total_target_tokens, gating):
    """Apply a gating strategy to the ride emission.
    Returns a Counter of gated weights.
    """
    out = Counter()
    if gating == "G0":  # pure ride
        return Counter(emitted)
    elif gating.startswith("G1"):  # ride × target_freq^β
        beta = {"G1a": 0.5, "G1b": 1.0, "G1c": 2.0}[gating]
        for t, w in emitted.items():
            tf = target_freq.get(t, 0)
            if tf > 0:
                out[t] = w * (tf ** beta)
        return out
    elif gating == "G2":  # ride / target_freq (boost rare)
        for t, w in emitted.items():
            tf = target_freq.get(t, 0)
            if tf > 0:
                out[t] = w / tf
        return out
    elif gating == "G3":  # background subtraction
        total_emitted = sum(emitted.values())
        for t, w in emitted.items():
            expected_freq_share = target_freq.get(t, 0) / max(total_target_tokens, 1)
            expected_emit = total_emitted * expected_freq_share
            residual = w - expected_emit
            if residual > 0:
                out[t] = residual
        return out
    elif gating == "G4":  # sqrt(ride × target_freq)
        for t, w in emitted.items():
            tf = target_freq.get(t, 0)
            if tf > 0:
                out[t] = np.sqrt(w * tf)
        return out
    return out


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def eval_emission(emitted, anchor_freq, target_freq):
    if not emitted: return 0.0
    union = list(set(emitted.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emitted.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return 0.0
    return cosine(e_vec, t_vec) - cosine(e_vec, a_vec)


GATING_VARIANTS = ["G0", "G1a", "G1b", "G1c", "G2", "G3", "G4"]
GATING_LABELS = {
    "G0":  "pure ride (54g)",
    "G1a": "ride × freq^0.5",
    "G1b": "ride × freq^1.0",
    "G1c": "ride × freq^2.0",
    "G2":  "ride / freq (anti)",
    "G3":  "background subtract",
    "G4":  "sqrt(ride × freq)",
}


def main():
    print(f"=== R-RBS-LM-54j — Freq-weighted gating sweep ===\n")
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
        table, vocab, idx_map, freq = build_eigvec_table(train)
        kernels[key] = {"table": table, "vocab": vocab, "idx_map": idx_map, "freq": freq}
        holdouts[key] = probes
        print(f"  {DOMAINS[key]['label']:<18s}: {len(table)} eigvecs; {len(probes)} probes")

    print(f"\n=== Per-pair gating sweep ===")
    all_results = []
    for pair in PAIRS:
        anchor_key = pair["anchor"]; target_key = pair["target"]
        ak = kernels[anchor_key]; tk = kernels[target_key]
        alignment = find_alignment(ak["table"], tk["table"])

        # Freq-weighted target baseline
        target_vocab = tk["vocab"]
        weights = np.array([tk["freq"].get(t, 1) for t in target_vocab], dtype=float)
        weights /= weights.sum()
        baseline_scores = []
        for probe_text in holdouts[anchor_key]:
            atoks = tokenize_filtered(probe_text)
            n_emit = len(atoks) * TOP_K_RANKS_PER_TOKEN * TOP_N_EMITTED_PER_RANK
            rand_idx = np.random.choice(len(target_vocab), size=min(n_emit, 1000), p=weights, replace=True)
            wp = Counter(target_vocab[i] for i in rand_idx)
            baseline_scores.append(eval_emission(wp, ak["freq"], tk["freq"]))
        baseline_mean = float(np.mean(baseline_scores))
        total_target = sum(tk["freq"].values())

        print(f"\n--- {DOMAINS[anchor_key]['label']} → {DOMAINS[target_key]['label']} ({pair['note']}) ---")
        print(f"  freq-weighted baseline: {baseline_mean:+.3f}")

        # Pre-compute pure-ride emissions for all probes
        ride_emissions = []
        for probe_text in holdouts[anchor_key]:
            emit = ride_uniform(ak["table"], ak["idx_map"], alignment, tk["table"], probe_text)
            ride_emissions.append(emit)

        pair_results = {"anchor": anchor_key, "target": target_key, "note": pair["note"], "baseline": baseline_mean, "gating": {}}
        for g in GATING_VARIANTS:
            scores = []
            for emit in ride_emissions:
                gated = gate(emit, tk["freq"], total_target, g)
                scores.append(eval_emission(gated, ak["freq"], tk["freq"]))
            gated_mean = float(np.mean(scores))
            delta = gated_mean - baseline_mean
            tag = "✓" if delta > 0.02 else (" " if delta > -0.02 else "-")
            print(f"  {g:<4s} {GATING_LABELS[g]:<22s}: {gated_mean:+.3f}; vs baseline {delta:+.3f} {tag}")
            pair_results["gating"][g] = {"mean": gated_mean, "delta": delta}
        all_results.append(pair_results)

    # Cross-pair variant ranking
    print(f"\n=== Cross-pair gating ranking ===")
    print(f"  {'gating':<26s} {'avg':>9s} {'avg Δ':>9s} {'wins':>7s} {'losses':>7s}")
    gating_summary = {}
    for g in GATING_VARIANTS:
        means = [p["gating"][g]["mean"] for p in all_results]
        deltas = [p["gating"][g]["delta"] for p in all_results]
        wins = sum(1 for d in deltas if d > 0.02)
        losses = sum(1 for d in deltas if d < -0.02)
        gating_summary[g] = {"avg_mean": float(np.mean(means)), "avg_delta": float(np.mean(deltas)), "wins": wins, "losses": losses}
        print(f"  {g} {GATING_LABELS[g]:<22s} {np.mean(means):>+9.3f} {np.mean(deltas):>+9.3f} {wins:>7d} {losses:>7d}")

    best = max(gating_summary.items(), key=lambda x: x[1]["avg_delta"])
    print(f"\n=== Verdict ===")
    print(f"  Best gating: {best[0]} ({GATING_LABELS[best[0]]}); avg Δ = {best[1]['avg_delta']:+.3f}")
    if best[1]["avg_delta"] > 0.05:
        verdict = f"FREQ-GATING WORKS: {best[0]} avg lift +{best[1]['avg_delta']:.3f}; multi-step ride architecture validated"
    elif best[1]["avg_delta"] > 0.0:
        verdict = f"FREQ-GATING MARGINAL: best {best[0]} avg lift {best[1]['avg_delta']:+.3f}; ride sharpens slightly under gating"
    else:
        verdict = f"FREQ-GATING INSUFFICIENT: even best ({best[0]}) below baseline ({best[1]['avg_delta']:+.3f})"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54j",
        "per_pair": all_results,
        "gating_summary": gating_summary,
        "best_gating": best[0],
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54j_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
