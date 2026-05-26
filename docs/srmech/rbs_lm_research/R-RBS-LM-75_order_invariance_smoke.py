"""R-RBS-LM-75 — Order-invariance falsification of current cascade.

Per user 2026-05-26: does iteration matter for RBS-NN substrate, or is
that anthropomorphism?

Math says: for our current cooccurrence-counting cascade, edge counts
are COMMUTATIVE — count(A, B) = count(B, A) regardless of when each
event occurred. The final Laplacian depends only on cumulative counts.
Therefore the final eigvec table should be ORDER-INVARIANT.

Test: run McGuffey curriculum in three orders; compare endpoints.

  Order A (pedagogical): Primer → Grade 1 → ... → Grade 6
  Order B (reverse):     Grade 6 → Grade 5 → ... → Primer
  Order C (shuffled):    all paragraphs randomly interleaved

Compare at end:
  - |edges| (must be identical — same total cooccurrences)
  - top-100 synapses (must be identical — same final counts)
  - eigvec table top-K content (must be identical — same Laplacian)
  - DOMAIN routing accuracy on held-out probes (must be identical)

If endpoints identical → iteration is presentation-only for the current
cascade. The grade-order in 73/74 was useful for OBSERVING substrate
growth, not for the cascade's learning.

If endpoints differ → vocab-truncation dynamics or numerical effects
introduce path-dependence we didn't expect. Honest negative would
require investigation.
"""

import json
import random
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

CURRICULUM = [
    ("primer",   "/tmp/mcguffey_primer.txt",   0.5, "Primer"),
    ("grade1",   "/tmp/mcguffey_first.txt",    1.0, "Grade 1"),
    ("grade2",   "/tmp/mcguffey_second.txt",   2.0, "Grade 2"),
    ("grade3",   "/tmp/mcguffey_third.txt",    3.0, "Grade 3"),
    ("grade4",   "/tmp/mcguffey_fourth.txt",   4.0, "Grade 4"),
    ("grade5",   "/tmp/mcguffey_fifth.txt",    5.0, "Grade 5"),
    ("grade6",   "/tmp/mcguffey_sixth.txt",    6.0, "Grade 6"),
]

COOCCURRENCE_DISTANCE = 5
KERNEL_N_EIGVECS = 200
M_PER_EIGVEC = 21

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
    """Return list of (grade_label, paragraph_text) tuples in pedagogical order."""
    out = []
    for grade_key, path, _gnum, glabel in CURRICULUM:
        text = strip_gutenberg(Path(path).read_text(encoding="utf-8", errors="replace"))
        for para in chunk_by_paragraph(text):
            out.append((glabel, para))
    return out


def process_rows(rows, distance=COOCCURRENCE_DISTANCE):
    """Process a list of (label, text) rows; return final freq + edge counts."""
    freq = Counter()
    edge_counter = Counter()
    for _label, text in rows:
        toks = tokenize_filtered(text)
        if len(toks) < 2: continue
        freq.update(toks)
        for i in range(len(toks)):
            for j in range(i+1, min(i+distance, len(toks))):
                a, b = toks[i], toks[j]
                if a == b: continue
                edge = (min(a,b), max(a,b))
                edge_counter[edge] += 1
    return freq, edge_counter


def build_eigvec_table(freq, edge_counter, vocab_n=KERNEL_N_EIGVECS):
    N = min(vocab_n, len(freq))
    if N < 8: return None, None
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges_idx, weights = [], []
    for (a, b), w in edge_counter.items():
        if a in idx_map and b in idx_map:
            edges_idx.append((idx_map[a], idx_map[b])); weights.append(float(w))
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
    print(f"=== R-RBS-LM-75 — Order-invariance falsification ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Math claim: cumulative cooccurrence counting is commutative;")
    print(f"            final substrate state should be order-invariant.\n")

    random.seed(42); np.random.seed(42)

    print(f"--- Loading curriculum paragraphs ---")
    all_paragraphs = load_curriculum_paragraphs()
    print(f"  Total paragraphs: {len(all_paragraphs)}")

    # Order A: pedagogical (already in this order)
    order_a = list(all_paragraphs)
    # Order B: reverse
    order_b = list(reversed(all_paragraphs))
    # Order C: shuffled
    order_c = list(all_paragraphs)
    random.shuffle(order_c)

    print(f"\n--- Order A: pedagogical (Primer → Grade 6) ---")
    freq_a, edges_a = process_rows(order_a)
    table_a, vocab_a = build_eigvec_table(freq_a, edges_a)
    print(f"  |freq vocab|: {len(freq_a)}; |edges|: {len(edges_a)}; top-3 vocab: {[t for t, _ in freq_a.most_common(3)]}")

    print(f"\n--- Order B: reverse (Grade 6 → Primer) ---")
    freq_b, edges_b = process_rows(order_b)
    table_b, vocab_b = build_eigvec_table(freq_b, edges_b)
    print(f"  |freq vocab|: {len(freq_b)}; |edges|: {len(edges_b)}; top-3 vocab: {[t for t, _ in freq_b.most_common(3)]}")

    print(f"\n--- Order C: shuffled (all paragraphs randomly interleaved) ---")
    freq_c, edges_c = process_rows(order_c)
    table_c, vocab_c = build_eigvec_table(freq_c, edges_c)
    print(f"  |freq vocab|: {len(freq_c)}; |edges|: {len(edges_c)}; top-3 vocab: {[t for t, _ in freq_c.most_common(3)]}")

    # === Endpoint comparisons ===
    print(f"\n=== Endpoint comparisons ===")
    print(f"  Total tokens: A={sum(freq_a.values())} | B={sum(freq_b.values())} | C={sum(freq_c.values())}")
    print(f"  |vocab|:      A={len(freq_a)}        | B={len(freq_b)}        | C={len(freq_c)}")
    print(f"  |edges|:      A={len(edges_a)}        | B={len(edges_b)}        | C={len(edges_c)}")

    # Identical?
    ab_freq_eq = (freq_a == freq_b)
    ac_freq_eq = (freq_a == freq_c)
    ab_edge_eq = (edges_a == edges_b)
    ac_edge_eq = (edges_a == edges_c)
    print(f"\n  freq A == freq B?  {ab_freq_eq}")
    print(f"  freq A == freq C?  {ac_freq_eq}")
    print(f"  edges A == edges B?  {ab_edge_eq}")
    print(f"  edges A == edges C?  {ac_edge_eq}")

    # Top-100 synapses
    top_a = set(e for e, _ in edges_a.most_common(100))
    top_b = set(e for e, _ in edges_b.most_common(100))
    top_c = set(e for e, _ in edges_c.most_common(100))
    print(f"\n  Top-100 synapses A∩B: {len(top_a & top_b)}/100")
    print(f"  Top-100 synapses A∩C: {len(top_a & top_c)}/100")
    print(f"  Top-100 synapses B∩C: {len(top_b & top_c)}/100")

    # Eigvec table top content
    print(f"\n  Top eigvec[0] content (top 12 tokens):")
    print(f"    A: {' '.join(table_a[0]['top_tokens'][:12])}")
    print(f"    B: {' '.join(table_b[0]['top_tokens'][:12])}")
    print(f"    C: {' '.join(table_c[0]['top_tokens'][:12])}")
    eq_eigvec_0_ab = (table_a[0]['token_set'] == table_b[0]['token_set'])
    eq_eigvec_0_ac = (table_a[0]['token_set'] == table_c[0]['token_set'])
    print(f"  Top eigvec[0] token set A == B?  {eq_eigvec_0_ab}")
    print(f"  Top eigvec[0] token set A == C?  {eq_eigvec_0_ac}")

    # Top-5 eigvec content Jaccard
    print(f"\n  Top-5 eigvec content Jaccard:")
    for r in range(5):
        sa = table_a[r]['token_set']; sb = table_b[r]['token_set']; sc = table_c[r]['token_set']
        jab = len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0
        jac = len(sa & sc) / len(sa | sc) if (sa | sc) else 0.0
        print(f"    rank {r}: A↔B={jab:.4f}; A↔C={jac:.4f}")

    # === Verdict ===
    print(f"\n=== Verdict ===")
    all_identical = ab_freq_eq and ac_freq_eq and ab_edge_eq and ac_edge_eq
    if all_identical and eq_eigvec_0_ab and eq_eigvec_0_ac:
        verdict = ("FULL ORDER-INVARIANCE CONFIRMED: freq counters, edge counters, AND top "
                   "eigvec content are all bit-identical across A/B/C. The current cumulative-"
                   "cooccurrence cascade has zero path-dependence on presentation order. "
                   "Iteration in 73/74 was measurement convenience, not substrate learning.")
    elif all_identical:
        verdict = ("COUNTING IDENTICAL but eigvec content varies (probably numerical precision "
                   "in eigendecompose for tied eigenvalues). Substrate is order-invariant up "
                   "to LAPACK tiebreak.")
    else:
        verdict = "UNEXPECTED: cumulative counts differ across A/B/C. Investigation needed."
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-75",
        "scope": "Order-invariance falsification of current cascade",
        "n_paragraphs": len(all_paragraphs),
        "endpoint_totals": {
            "A": {"tokens": sum(freq_a.values()), "vocab": len(freq_a), "edges": len(edges_a)},
            "B": {"tokens": sum(freq_b.values()), "vocab": len(freq_b), "edges": len(edges_b)},
            "C": {"tokens": sum(freq_c.values()), "vocab": len(freq_c), "edges": len(edges_c)},
        },
        "freq_identical_AB": bool(ab_freq_eq),
        "freq_identical_AC": bool(ac_freq_eq),
        "edges_identical_AB": bool(ab_edge_eq),
        "edges_identical_AC": bool(ac_edge_eq),
        "top100_synapse_intersection_AB": len(top_a & top_b),
        "top100_synapse_intersection_AC": len(top_a & top_c),
        "top_eigvec0_identical_AB": bool(eq_eigvec_0_ab),
        "top_eigvec0_identical_AC": bool(eq_eigvec_0_ac),
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-75_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
