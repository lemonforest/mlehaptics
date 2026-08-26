"""R-RBS-LM-76 v2 — Plasticity-augmented cascade with analytical-formula decay.

The original 76 used naive per-row decay (O(|edges| × T) where T ~6651 rows
and |edges| grew to ~500K — stalled at ~25+ min). This rewrite uses the
analytical formula:

  For each edge touched at rows r_1, r_2, ..., r_k out of T total rows:
    final_weight = Σ α^(T - r_i - 1)

This is O(total_touches) total instead of O(|edges| × T). For our corpus
~20-30K touches total → completes in seconds.

Tests whether plasticity rules (decay + reinforcement) introduce path-
dependence per Finding 75 (current cascade is order-invariant). Per user
2026-05-26: "iterative may be exactly how this storage medium gains
confidence, since it's not a list of words like a book."

Same test design as 76 v1:
  Order A (pedagogical):  Primer → Grade 6 + decay
  Order B (reverse):      Grade 6 → Primer + decay
  Order C (shuffled):     all paragraphs random + decay
  Baseline (no decay):    A with α=1.0 (= 74's behavior)

α = 0.999 per row.

Compare:
  - Final |edges|, top-100 synapses
  - Final eigvec content
  - Path-dependence: do A/B/C differ?
"""

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

CURRICULUM = [
    ("primer",   "/tmp/mcguffey_primer.txt"),
    ("grade1",   "/tmp/mcguffey_first.txt"),
    ("grade2",   "/tmp/mcguffey_second.txt"),
    ("grade3",   "/tmp/mcguffey_third.txt"),
    ("grade4",   "/tmp/mcguffey_fourth.txt"),
    ("grade5",   "/tmp/mcguffey_fifth.txt"),
    ("grade6",   "/tmp/mcguffey_sixth.txt"),
]

COOCCURRENCE_DISTANCE = 5
KERNEL_N_EIGVECS = 200
M_PER_EIGVEC = 21
DECAY_ALPHA = 0.999
PRUNE_THRESHOLD = 0.01

STOPWORDS_EN = set("""
the a an and or but of in on at to for with by from as is are was were be been
have has had this that these those it its they them their there here
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


def chunk_by_paragraph(text):
    raw = re.split(r"\n\s*\n+", text)
    for c in raw:
        c = c.strip()
        if len(c) >= 50: yield c


def load_curriculum_paragraphs():
    out = []
    for grade_key, path in CURRICULUM:
        text = strip_gutenberg(Path(path).read_text(encoding="utf-8", errors="replace"))
        for para in chunk_by_paragraph(text):
            out.append((grade_key, para))
    return out


def process_rows_analytical(rows, decay_alpha=DECAY_ALPHA,
                              prune_threshold=PRUNE_THRESHOLD,
                              distance=COOCCURRENCE_DISTANCE):
    """Analytical-formula plasticity: track touch-rows per edge; compute
    final weights via Σ α^(T-r-1)."""
    freq = Counter()
    edge_touches = defaultdict(list)
    T = len(rows)

    for row_idx, (_label, text) in enumerate(rows):
        toks = tokenize_filtered(text)
        if len(toks) < 2: continue
        freq.update(toks)
        for i in range(len(toks)):
            for j in range(i+1, min(i+distance, len(toks))):
                a, b = toks[i], toks[j]
                if a == b: continue
                edge_touches[(min(a,b), max(a,b))].append(row_idx)

    # Precompute α^k for k = 0..T-1
    if decay_alpha < 1.0:
        alpha_powers = [1.0]
        for _ in range(T):
            alpha_powers.append(alpha_powers[-1] * decay_alpha)
        edge_weights = {}
        for e, touches in edge_touches.items():
            w = sum(alpha_powers[T - r - 1] for r in touches)
            if w >= prune_threshold:
                edge_weights[e] = w
    else:
        edge_weights = {e: float(len(touches)) for e, touches in edge_touches.items()}

    return freq, edge_weights, T


def build_eigvec_table(freq, edge_weights, vocab_n=KERNEL_N_EIGVECS):
    N = min(vocab_n, len(freq))
    if N < 8: return None, None
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges_idx, weights = [], []
    for (a, b), w in edge_weights.items():
        if a in idx_map and b in idx_map and w > 0:
            edges_idx.append((idx_map[a], idx_map[b]))
            weights.append(float(w))
    if not edges_idx: return None, vocab
    L = dense_laplacian(N, edges_idx, weights)
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_PER_EIGVEC]
        top_tokens = [vocab[i] for i in top_idx]
        table.append({"rank": len(ev)-1-k, "eigval": float(np.real(ev[k])),
                       "top_tokens": top_tokens, "token_set": set(top_tokens)})
    return table, vocab


def main():
    print(f"=== R-RBS-LM-76 v2 — Analytical-formula plasticity-augmented cascade ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Decay α: {DECAY_ALPHA} per row (half-life ~{int(np.log(2)/np.log(1/DECAY_ALPHA))} rows)")
    print(f"Prune threshold: {PRUNE_THRESHOLD}\n")

    random.seed(42); np.random.seed(42)

    all_paragraphs = load_curriculum_paragraphs()
    print(f"Total paragraphs: {len(all_paragraphs)}")

    order_a = list(all_paragraphs)
    order_b = list(reversed(all_paragraphs))
    order_c = list(all_paragraphs); random.shuffle(order_c)

    print(f"\n--- Order A (pedagogical) + decay ---")
    freq_a, edges_a, t_a = process_rows_analytical(order_a)
    table_a, _ = build_eigvec_table(freq_a, edges_a)
    print(f"  T={t_a} rows; |edges|={len(edges_a)}; total_weight={sum(edges_a.values()):.1f}")
    top_a = sorted(edges_a.items(), key=lambda x: -x[1])[:5]
    print(f"  Top-5 synapses: " + ", ".join(f"{a}-{b}={w:.2f}" for (a,b),w in top_a))

    print(f"\n--- Order B (reverse) + decay ---")
    freq_b, edges_b, t_b = process_rows_analytical(order_b)
    table_b, _ = build_eigvec_table(freq_b, edges_b)
    print(f"  T={t_b} rows; |edges|={len(edges_b)}; total_weight={sum(edges_b.values()):.1f}")
    top_b = sorted(edges_b.items(), key=lambda x: -x[1])[:5]
    print(f"  Top-5 synapses: " + ", ".join(f"{a}-{b}={w:.2f}" for (a,b),w in top_b))

    print(f"\n--- Order C (shuffled) + decay ---")
    freq_c, edges_c, t_c = process_rows_analytical(order_c)
    table_c, _ = build_eigvec_table(freq_c, edges_c)
    print(f"  T={t_c} rows; |edges|={len(edges_c)}; total_weight={sum(edges_c.values()):.1f}")
    top_c = sorted(edges_c.items(), key=lambda x: -x[1])[:5]
    print(f"  Top-5 synapses: " + ", ".join(f"{a}-{b}={w:.2f}" for (a,b),w in top_c))

    print(f"\n--- Baseline (no decay; α=1.0) ---")
    freq_bl, edges_bl, t_bl = process_rows_analytical(order_a, decay_alpha=1.0, prune_threshold=0)
    table_bl, _ = build_eigvec_table(freq_bl, edges_bl)
    print(f"  T={t_bl} rows; |edges|={len(edges_bl)}; total_weight={sum(edges_bl.values()):.0f}")

    # === Path-dependence analysis ===
    print(f"\n=== Path-dependence test ===\n")
    top100_a = set(e for e, _ in sorted(edges_a.items(), key=lambda x: -x[1])[:100])
    top100_b = set(e for e, _ in sorted(edges_b.items(), key=lambda x: -x[1])[:100])
    top100_c = set(e for e, _ in sorted(edges_c.items(), key=lambda x: -x[1])[:100])
    print(f"  Top-100 synapse intersections (with decay):")
    print(f"    A ∩ B = {len(top100_a & top100_b)}/100")
    print(f"    A ∩ C = {len(top100_a & top100_c)}/100")
    print(f"    B ∩ C = {len(top100_b & top100_c)}/100")

    # Eigvec content comparison
    print(f"\n  Top eigvec[0] content (first 10 tokens):")
    print(f"    A: {' '.join(table_a[0]['top_tokens'][:10])}")
    print(f"    B: {' '.join(table_b[0]['top_tokens'][:10])}")
    print(f"    C: {' '.join(table_c[0]['top_tokens'][:10])}")
    print(f"    BL (no decay): {' '.join(table_bl[0]['top_tokens'][:10])}")

    # Substrate quality: top-100 weight share
    print(f"\n=== Substrate quality (top-100 share of total weight) ===\n")
    for name, edges in [("A (ped+decay)", edges_a), ("B (rev+decay)", edges_b),
                         ("C (shuf+decay)", edges_c), ("BL (no decay)", edges_bl)]:
        if not edges: continue
        weights = np.array(list(edges.values()))
        if weights.sum() == 0: continue
        top100_share = float(np.sort(weights)[::-1][:100].sum() / weights.sum())
        print(f"  {name}: top-100 share = {top100_share:.3f}; total weight = {weights.sum():.1f}; |edges| = {len(weights)}")

    # === Verdicts ===
    print(f"\n=== Verdicts ===\n")
    a_top100 = float(np.sort(np.array(list(edges_a.values())))[::-1][:100].sum() / sum(edges_a.values()))
    bl_top100 = float(np.sort(np.array(list(edges_bl.values())))[::-1][:100].sum() / sum(edges_bl.values()))

    # Q1: path-dependence?
    path_dep = (len(top100_a & top100_b) < 90) or (table_a[0]['token_set'] != table_b[0]['token_set'])
    if path_dep:
        v1 = f"Q1: PATH-DEPENDENCE OBSERVED with decay. Orders A/B/C produce different final states (Jaccard <90). Plasticity introduces iteration-sensitivity."
    else:
        v1 = f"Q1: PATH-INVARIANT even with decay. Orders converge (Jaccard >=90). Decay too weak at α={DECAY_ALPHA} to differentiate."
    print(f"  {v1}")

    # Q2: substrate quality?
    if a_top100 > bl_top100 * 1.1:
        v2 = f"Q2: PLASTICITY SHARPENS substrate. Pedagogical+decay top-100 share {a_top100:.3f} vs no-decay {bl_top100:.3f} (concentration improves {a_top100/bl_top100:.2f}x). Decay actively concentrates substrate."
    elif a_top100 > bl_top100 * 0.95:
        v2 = f"Q2: PLASTICITY NEUTRAL. Top-100 concentration similar (decay {a_top100:.3f} vs no-decay {bl_top100:.3f}). Decay doesn't help or hurt at this α."
    else:
        v2 = f"Q2: PLASTICITY DEGRADES substrate. Decay top-100 share {a_top100:.3f} < no-decay {bl_top100:.3f}. Decay erodes more signal than it concentrates."
    print(f"  {v2}")

    out = {
        "partition": "R-RBS-LM-76 v2",
        "decay_alpha": DECAY_ALPHA, "prune_threshold": PRUNE_THRESHOLD,
        "n_paragraphs": len(all_paragraphs),
        "endpoint_summary": {
            "A": {"n_edges": len(edges_a), "total_weight": float(sum(edges_a.values())), "top100_share": float(a_top100)},
            "B": {"n_edges": len(edges_b), "total_weight": float(sum(edges_b.values()))},
            "C": {"n_edges": len(edges_c), "total_weight": float(sum(edges_c.values()))},
            "BL": {"n_edges": len(edges_bl), "total_weight": float(sum(edges_bl.values())), "top100_share": float(bl_top100)},
        },
        "top100_AB_intersect": len(top100_a & top100_b),
        "top100_AC_intersect": len(top100_a & top100_c),
        "top100_BC_intersect": len(top100_b & top100_c),
        "verdict_path": v1,
        "verdict_quality": v2,
    }
    out_path = HERE / "R-RBS-LM-76_v2_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
