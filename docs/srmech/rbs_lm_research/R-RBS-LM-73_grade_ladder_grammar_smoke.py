"""R-RBS-LM-73 — English grammar substrate from McGuffey grade ladder.

Per user 2026-05-26: "omg open access grammar books! ... start from grade 1"

The architecture shift:
  OLD path (54s fluency gap): cascade is at word-content level; no grammar
  structure → emissions are bag-of-content-words in anchor order, not fluent
  sentences

  NEW path (R-RBS-LM-73): use OPEN ACCESS GRAMMAR BOOKS as substrate-content
  DIRECTLY. Don't infer grammar via statistical POS tagger (that's noisy
  stochastic-HDC in the user's framework). The grammar books themselves are
  asymptotically-accurate human-authored encodings of English language rules.

Per the user's "start from grade 1" insight: the foundation builds bottom-up.
  Grade 1 teaches what a sentence IS (subject + predicate).
  Grade 2 builds on it with simple compound forms.
  Grade 6 has full literary English.

If the cascade methodology is sound, the grade ladder should show:
  - Top eigvec content shifts predictably from grade to grade
  - Each grade's substrate contains structurally what's below it plus what's new
  - Cross-grade alignment forms a monotone ladder of structural complexity
  - Late grades have richer / more varied eigvec content than early grades

Corpora (all from Project Gutenberg; CC0/public domain; verified attested):
  PG 14642  McGuffey's Eclectic Primer            42K   pre-Grade 1
  PG 14640  McGuffey's First Eclectic Reader      64K   Grade 1
  PG 14668  McGuffey's Second Eclectic Reader    122K   Grade 2
  PG 14766  McGuffey's Third Eclectic Reader     168K   Grade 3
  PG 14880  McGuffey's Fourth Eclectic Reader    389K   Grade 4
  PG 15040  McGuffey's Fifth Eclectic Reader     605K   Grade 5
  PG 16751  McGuffey's Sixth Eclectic Reader     842K   Grade 6
  PG 15456  McGuffey's Eclectic Spelling Book    171K   companion

Method:
  1. For each grade, build cascade kernel (Laplacian eigvecs over distance-5
     cooccurrence) — same methodology as 54a-r but on graded English primers
  2. Examine top-K eigvec content per grade
  3. Compute pairwise alignment (set-cosine per Finding 70 correction) across
     the ladder
  4. Test: is alignment monotone with grade-distance? (Grade 1 ↔ Grade 2 closer
     than Grade 1 ↔ Grade 6?)
  5. Reader-side qualitative check: do early-grade eigvecs cluster around
     basic-sight-words / SVO patterns? Do late-grade eigvecs cluster around
     more literary vocabulary?

Per Finding 70 correction: using set-cosine (not random-bipolar HDC) for
similarity. The Class L eigvec layer is load-bearing; Class M bundle would
be redundant with set-cosine.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

GRADES = {
    "primer":   {"path": "/tmp/mcguffey_primer.txt",   "grade": 0.5, "label": "Primer"},
    "grade1":   {"path": "/tmp/mcguffey_first.txt",    "grade": 1.0, "label": "Grade 1 (First Reader)"},
    "grade2":   {"path": "/tmp/mcguffey_second.txt",   "grade": 2.0, "label": "Grade 2 (Second Reader)"},
    "grade3":   {"path": "/tmp/mcguffey_third.txt",    "grade": 3.0, "label": "Grade 3 (Third Reader)"},
    "grade4":   {"path": "/tmp/mcguffey_fourth.txt",   "grade": 4.0, "label": "Grade 4 (Fourth Reader)"},
    "grade5":   {"path": "/tmp/mcguffey_fifth.txt",    "grade": 5.0, "label": "Grade 5 (Fifth Reader)"},
    "grade6":   {"path": "/tmp/mcguffey_sixth.txt",    "grade": 6.0, "label": "Grade 6 (Sixth Reader)"},
    "spelling": {"path": "/tmp/mcguffey_spelling.txt", "grade": 2.5, "label": "Spelling Book"},
}

KERNEL_N_EIGVECS = 200
M_PER_EIGVEC = 21
COOCCURRENCE_DISTANCE = 5

# Light stopword filter — keep enough that we can see structural words
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


def build_kernel(text, n_eigvecs=KERNEL_N_EIGVECS, m_per_eigvec=M_PER_EIGVEC):
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(n_eigvecs, len(freq))
    if N < 8: return None, freq, 0
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges = Counter()
    for toks in filt:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i+1, min(i+COOCCURRENCE_DISTANCE, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges[(min(a,b), max(a,b))] += 1
    if not edges: return None, freq, 0
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:m_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        table.append({"rank": len(ev) - 1 - k, "eigval": float(np.real(ev[k])),
                       "top_tokens": top_tokens, "token_set": set(top_tokens)})
    return table, freq, len(edges)


def sim_cosine(a, b):
    set_a = a["token_set"]; set_b = b["token_set"]
    if not set_a or not set_b: return 0.0
    return float(len(set_a & set_b) / np.sqrt(len(set_a) * len(set_b)))


def find_alignment_score(table_a, table_b):
    sims = []
    used_b = set()
    for i in range(len(table_a)):
        cands = [(j, sim_cosine(table_a[i], table_b[j]))
                 for j in range(len(table_b)) if j not in used_b]
        if not cands: break
        best_j, best_s = max(cands, key=lambda x: x[1])
        used_b.add(best_j)
        sims.append(best_s)
    return float(np.mean(sims)) if sims else 0.0


def main():
    print(f"=== R-RBS-LM-73 — McGuffey grade ladder grammar substrate ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"User direction: start from grade 1; build the ladder up\n")

    print(f"--- Building per-grade kernels ---")
    kernels = {}
    for key, info in GRADES.items():
        text = strip_gutenberg(Path(info["path"]).read_text(encoding="utf-8", errors="replace"))
        table, freq, n_edges = build_kernel(text)
        kernels[key] = {"table": table, "freq": freq, "n_edges": n_edges, "n_tokens": sum(freq.values())}
        n_eigvecs = len(table) if table else 0
        print(f"  [grade {info['grade']:>3.1f}] {info['label']:<32s} | "
              f"vocab={len(freq):>5d} | tokens={sum(freq.values()):>6d} | "
              f"edges={n_edges:>6d} | eigvecs={n_eigvecs:>3d}")

    # Examine top eigvec content per grade
    print(f"\n=== Top-5 eigvec content by grade (what each grade's structure encodes) ===")
    for key in ["primer", "grade1", "grade2", "grade3", "grade4", "grade5", "grade6"]:
        info = GRADES[key]
        table = kernels[key]["table"]
        if not table: continue
        print(f"\n  {info['label']}:")
        for r in range(min(5, len(table))):
            tokens = table[r]["top_tokens"][:15]
            print(f"    rank {r}: {' '.join(tokens)}")

    # Pairwise alignment matrix
    print(f"\n=== Pairwise alignment matrix (set-cosine; per Finding 70 correction) ===")
    grade_keys = ["primer", "grade1", "grade2", "grade3", "grade4", "grade5", "grade6", "spelling"]
    pairwise = {}
    print(f"  {'A \\\\ B':<10s}", end="")
    for b in grade_keys: print(f"{b[:9]:>10s}", end="")
    print()
    for a in grade_keys:
        print(f"  {a[:10]:<10s}", end="")
        for b in grade_keys:
            if a == b:
                print(f"{'-':>10s}", end=""); continue
            key = (min(a,b), max(a,b))
            if key not in pairwise:
                if kernels[a]["table"] and kernels[b]["table"]:
                    pairwise[key] = find_alignment_score(kernels[a]["table"], kernels[b]["table"])
                else:
                    pairwise[key] = 0.0
            print(f"{pairwise[key]:>+10.4f}", end="")
        print()

    # Grade-distance monotonicity test
    print(f"\n=== Grade-distance monotonicity test ===")
    print(f"Hypothesis: alignment(grade-i, grade-i+1) > alignment(grade-i, grade-i+k) for k>1")
    print(f"  Grade pair                       Distance   Alignment")
    grade_pairs_for_monotone = []
    for i in range(7):  # grades 0-6 (primer + 6 readers)
        for j in range(i+1, 7):
            ki = ["primer", "grade1", "grade2", "grade3", "grade4", "grade5", "grade6"][i]
            kj = ["primer", "grade1", "grade2", "grade3", "grade4", "grade5", "grade6"][j]
            key = (min(ki,kj), max(ki,kj))
            d = j - i
            s = pairwise.get(key, 0.0)
            grade_pairs_for_monotone.append((d, s))
            print(f"  {GRADES[ki]['label'][:18]:<18s} ↔ {GRADES[kj]['label'][:18]:<18s}  d={d}  sim={s:+.4f}")

    # Aggregate by distance
    print(f"\n  Mean alignment by grade-distance:")
    by_dist = {}
    for d, s in grade_pairs_for_monotone:
        by_dist.setdefault(d, []).append(s)
    for d in sorted(by_dist):
        sims = by_dist[d]
        print(f"    distance {d}: mean = {np.mean(sims):+.4f} (n={len(sims)})")

    # Monotone test
    means = [float(np.mean(by_dist[d])) for d in sorted(by_dist)]
    is_monotone = all(means[i] >= means[i+1] - 0.001 for i in range(len(means)-1))
    print(f"\n  Monotone non-increasing across grade-distance? {is_monotone}")

    # Verdict
    print(f"\n=== Verdict ===")
    span = means[0] - means[-1] if means else 0.0
    if is_monotone and span > 0.02:
        verdict = (f"GRADE LADDER STRUCTURE CONFIRMED: alignment decreases monotonically with "
                   f"grade-distance (Δ={span:+.3f} across distance 1→6). The McGuffey readers form "
                   f"an asymptotically-organized substrate-content ladder of English structural complexity.")
    elif span > 0.02:
        verdict = (f"GRADE LADDER STRUCTURE PARTIAL: alignment decreases with grade-distance "
                   f"(Δ={span:+.3f}) but not strictly monotone. Substrate-content forms a structural "
                   f"trend with some interleaving.")
    elif span > -0.02:
        verdict = (f"GRADE LADDER FLAT: alignment uniform across grade-distance (Δ={span:+.3f}). "
                   f"The cascade does not distinguish grade-level structurally.")
    else:
        verdict = (f"GRADE LADDER REVERSED: far grades align MORE than near grades (Δ={span:+.3f}). "
                   f"Unexpected; could indicate the cascade is finding vocabulary overlap rather than "
                   f"structural progression.")
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-73",
        "grades": {k: {"label": v["label"], "grade": v["grade"],
                        "n_tokens": kernels[k]["n_tokens"], "n_edges": kernels[k]["n_edges"]}
                    for k, v in GRADES.items()},
        "top_eigvec_tokens_per_grade": {
            k: kernels[k]["table"][0]["top_tokens"] if kernels[k]["table"] else None
            for k in grade_keys},
        "pairwise_alignments": {f"{a}|{b}": float(s) for (a, b), s in pairwise.items()},
        "mean_alignment_by_distance": {str(d): float(np.mean(s)) for d, s in by_dist.items()},
        "is_monotone": bool(is_monotone),
        "alignment_span": float(span),
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-73_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
