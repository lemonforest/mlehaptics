"""R-RBS-LM-78 — K-12 multi-subject corpus extension.

Per user 2026-05-26: "K-12 + higher education corpus will let us understand
different teach level materials as well was part of my thinking. extend
our test to include all k-12 subjects, not just grammar. we learn language
when we learn word problems in math as well."

Coverage extension adds 7 K-12 subject-specific corpora beyond reading +
grammar-instruction:

  SCIENCE / NATURE (3 corpora):
    PG 45112 Astronomy for Young Folks (Isabel Martin Lewis; 402K)
    PG 60318 Star-land (Robert Ball; 601K) — astronomy narrative
    PG 25646 Child's Health Primer (Jane Andrews; 123K) — physiology / health

  HISTORY (1 corpus):
    PG 23495 The Story of the Greeks (H. A. Guerber; 430K) — narrative history

  GEOGRAPHY / ECONOMICS (3 corpora):
    PG 12228 Home Geography for Primary Grades (C. C. Long; 118K)
    PG 24884 Commercial Geography (Jacques W. Redway; 621K)
    PG 38762 How We Are Fed: A Geographical Reader (Chamberlain; 188K)

Combined with existing corpora:
  READING: McGuffey Primer + Grades 1-6 (7 corpora)
  GRAMMAR-INSTRUCTION: Kittredge, Kirkham, Strunk (3 corpora)

Total: 17 corpora across 5 substrate-kinds (reading, grammar-instruction,
science, history, geography).

COVERAGE GAP DOCUMENTED:
  - MATH: no K-12 arithmetic / math textbook found on PG; Ray's, Milne's,
    and similar 19th-century math primers not digitized. Gap persists.

Two questions for the cascade:
  (1) Do K-12 subjects form distinct substrate-classes via the cascade?
      Do science-corpora cluster among themselves more than with history?
  (2) What's the cross-subject alignment landscape?
      Does science share form with geography? Does history share with reading?

Per Finding 70 correction: using set-cosine over top-K token sets;
the random-bipolar-bundle HDC layer is decorative for this routing test.

Per [[feedback_human_coherent_steps_in_reports]]: this builds a substrate-
coverage MAP. The map will be useful for any future inference / generation
work that needs to know which K-12 subjects the cascade has form-knowledge of.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

CORPUS = [
    # Reading material (McGuffey)
    ("primer",          "/tmp/mcguffey_primer.txt",                  0.5,  "Primer",                "reading"),
    ("grade1",          "/tmp/mcguffey_first.txt",                   1.0,  "Grade 1",               "reading"),
    ("grade2",          "/tmp/mcguffey_second.txt",                  2.0,  "Grade 2",               "reading"),
    ("grade3",          "/tmp/mcguffey_third.txt",                   3.0,  "Grade 3",               "reading"),
    ("grade4",          "/tmp/mcguffey_fourth.txt",                  4.0,  "Grade 4",               "reading"),
    ("grade5",          "/tmp/mcguffey_fifth.txt",                   5.0,  "Grade 5",               "reading"),
    ("grade6",          "/tmp/mcguffey_sixth.txt",                   6.0,  "Grade 6",               "reading"),
    # Grammar / composition instruction
    ("kittredge",       "/tmp/kittredge_advanced_grammar.txt",       8.0,  "Kittredge Adv Gr",      "grammar"),
    ("kirkham",         "/tmp/goold_brown_grammar.txt",              9.0,  "Kirkham Gr Lectures",   "grammar"),
    ("strunk",          "/tmp/strunk_elements.txt",                  12.0, "Strunk Elements",       "grammar"),
    # Science
    ("astronomy_yf",    "/tmp/k12_astronomy_youngfolks.txt",         5.0,  "Astronomy YF",          "science"),
    ("starland",        "/tmp/k12_starland.txt",                     6.0,  "Star-land",             "science"),
    ("childs_health",   "/tmp/k12_childs_health_primer.txt",         3.0,  "Child's Health Primer", "science"),
    # History
    ("greeks_history",  "/tmp/k12_story_of_greeks.txt",              7.0,  "Story of the Greeks",   "history"),
    # Geography
    ("home_geography",  "/tmp/k12_home_geography.txt",               3.0,  "Home Geography",        "geography"),
    ("commercial_geog", "/tmp/k12_commercial_geography.txt",         9.0,  "Commercial Geography",  "geography"),
    ("how_we_are_fed",  "/tmp/k12_how_we_are_fed.txt",               5.0,  "How We Are Fed",        "geography"),
]

KERNEL_N_EIGVECS = 200
M_PER_EIGVEC = 21
COOCCURRENCE_DISTANCE = 5

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


def build_kernel(text):
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(KERNEL_N_EIGVECS, len(freq))
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
        top_idx = np.argsort(-mag_sq)[:M_PER_EIGVEC]
        top_tokens = [vocab[i] for i in top_idx]
        table.append({"rank": len(ev)-1-k, "eigval": float(np.real(ev[k])),
                       "top_tokens": top_tokens, "token_set": set(top_tokens)})
    return table, freq, len(edges)


def sim_cosine(a, b):
    sa, sb = a["token_set"], b["token_set"]
    if not sa or not sb: return 0.0
    return float(len(sa & sb) / np.sqrt(len(sa) * len(sb)))


def find_alignment_score(table_a, table_b):
    sims = []; used = set()
    for i in range(len(table_a)):
        cands = [(j, sim_cosine(table_a[i], table_b[j]))
                 for j in range(len(table_b)) if j not in used]
        if not cands: break
        bj, bs = max(cands, key=lambda x: x[1])
        used.add(bj); sims.append(bs)
    return float(np.mean(sims)) if sims else 0.0


def main():
    print(f"=== R-RBS-LM-78 — K-12 multi-subject corpus map ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"17 corpora across 5 substrate-kinds (reading / grammar / science / history / geography)")
    print(f"COVERAGE GAP: math (no K-12 math textbook found on PG)\n")

    print(f"--- Building per-corpus kernels ---")
    kernels = {}
    for key, path, level, label, subject in CORPUS:
        text = strip_gutenberg(Path(path).read_text(encoding="utf-8", errors="replace"))
        table, freq, n_edges = build_kernel(text)
        kernels[key] = {"table": table, "freq": freq, "n_edges": n_edges,
                          "level": level, "label": label, "subject": subject,
                          "n_tokens": sum(freq.values())}
        print(f"  [{subject:<9s} L{level:>4.1f}] {label:<24s} | vocab={len(freq):>6d} | tokens={sum(freq.values()):>7d}")

    # Top eigvec content per corpus
    print(f"\n=== Top eigvec[0] content per corpus (10 tokens each) ===")
    for key, _, _, label, subject in CORPUS:
        t = kernels[key]["table"]
        if not t: continue
        print(f"  [{subject:<9s}] {label:<24s}: {' '.join(t[0]['top_tokens'][:10])}")

    # Pairwise alignment matrix (compressed; show subject groupings)
    print(f"\n=== Pairwise alignment computation ({len(CORPUS)} × {len(CORPUS)}) ===")
    keys = [c[0] for c in CORPUS]
    pairwise = {}
    for i, a in enumerate(keys):
        for b in keys[i+1:]:
            # Use sorted-tuple key for symmetric lookup
            pairwise[tuple(sorted((a, b)))] = find_alignment_score(kernels[a]["table"], kernels[b]["table"])

    # === Subject-level analysis ===
    subjects_list = ["reading", "grammar", "science", "history", "geography"]
    subject_members = {s: [k for k, _, _, _, sj in CORPUS if sj == s] for s in subjects_list}

    print(f"\n=== Substrate-class clustering (subject vs subject) ===")
    print(f"  {'subject':<11s} {'n_members':>9s} {'within_avg':>11s} {'cross_avg':>10s} {'ratio':>7s}")
    subject_stats = {}
    for s in subjects_list:
        members = subject_members[s]
        if len(members) < 2:
            within_avg = None
        else:
            within = [pairwise[tuple(sorted((a,b)))] for i, a in enumerate(members) for b in members[i+1:]]
            within_avg = float(np.mean(within))
        # Cross: all pairs where one is in s, other is not
        cross = []
        for a in members:
            for k in keys:
                if k == a: continue
                if k in members: continue
                cross.append(pairwise[tuple(sorted((a,k)))])
        cross_avg = float(np.mean(cross)) if cross else 0.0
        ratio = within_avg / cross_avg if (within_avg is not None and cross_avg > 0) else None
        wavg_str = f"{within_avg:+.4f}" if within_avg is not None else "  n/a "
        ratio_str = f"{ratio:.2f}" if ratio is not None else " n/a "
        print(f"  {s:<11s} {len(members):>9d} {wavg_str:>11s} {cross_avg:>+10.4f} {ratio_str:>7s}")
        subject_stats[s] = {"n_members": len(members), "within_avg": within_avg,
                              "cross_avg": cross_avg, "ratio": ratio}

    # === Subject-to-subject mean alignment matrix ===
    print(f"\n=== Subject-to-subject mean alignment matrix ===")
    print(f"  {'A \\\\ B':<11s}", end="")
    for s in subjects_list: print(f"{s[:9]:>10s}", end="")
    print()
    subject_pairs = {}
    for sa in subjects_list:
        print(f"  {sa[:11]:<11s}", end="")
        for sb in subjects_list:
            members_a = subject_members[sa]; members_b = subject_members[sb]
            if sa == sb:
                if len(members_a) < 2: print(f"{'-':>10s}", end=""); continue
                pairs = [pairwise[tuple(sorted((a,b)))] for i, a in enumerate(members_a) for b in members_a[i+1:]]
            else:
                pairs = [pairwise[tuple(sorted((a,b)))] for a in members_a for b in members_b]
            m = float(np.mean(pairs)) if pairs else 0.0
            subject_pairs[f"{sa}|{sb}"] = m
            print(f"{m:>+10.4f}", end="")
        print()

    # === Strongest cross-subject alignments ===
    print(f"\n=== Strongest pairwise alignments (top 10 across all corpus pairs) ===")
    sorted_pairs = sorted(pairwise.items(), key=lambda x: -x[1])[:10]
    for (a, b), s in sorted_pairs:
        sub_a = kernels[a]["subject"]; sub_b = kernels[b]["subject"]
        same_subject = "SAME" if sub_a == sub_b else "CROSS"
        print(f"  {kernels[a]['label']:<24s} ({sub_a:<9s}) ↔ "
              f"{kernels[b]['label']:<24s} ({sub_b:<9s}) = {s:+.4f} [{same_subject}]")

    print(f"\n=== Weakest pairwise alignments (bottom 10) ===")
    for (a, b), s in sorted(pairwise.items(), key=lambda x: x[1])[:10]:
        sub_a = kernels[a]["subject"]; sub_b = kernels[b]["subject"]
        same_subject = "SAME" if sub_a == sub_b else "CROSS"
        print(f"  {kernels[a]['label']:<24s} ({sub_a:<9s}) ↔ "
              f"{kernels[b]['label']:<24s} ({sub_b:<9s}) = {s:+.4f} [{same_subject}]")

    # === Verdict ===
    print(f"\n=== Verdict ===")
    # Are subjects substrate-class-distinct on average?
    in_class_avg = float(np.mean([s["within_avg"] for s in subject_stats.values() if s["within_avg"] is not None]))
    cross_class_avg = float(np.mean([s["cross_avg"] for s in subject_stats.values()]))
    print(f"  Average within-subject alignment: {in_class_avg:+.4f}")
    print(f"  Average cross-subject alignment:  {cross_class_avg:+.4f}")
    ratio = in_class_avg / max(cross_class_avg, 1e-9)
    print(f"  Within / cross ratio: {ratio:.2f}")
    if ratio > 1.5:
        verdict = (f"STRONG substrate-CLASS structure: K-12 subjects form distinct "
                   f"substrate-classes (within {ratio:.2f}x tighter than cross). The cascade "
                   f"detects subject boundaries in K-12 language.")
    elif ratio > 1.15:
        verdict = (f"MODERATE substrate-class structure: subjects partially distinct (ratio {ratio:.2f})")
    else:
        verdict = (f"WEAK substrate-class structure: subjects structurally similar (ratio {ratio:.2f}); "
                   f"K-12 language has lots of shared form across subjects")
    print(f"  {verdict}")

    print(f"\n  COVERAGE GAPS (per discipline):")
    print(f"    - MATH: no K-12 arithmetic / math textbook available on PG. Gap persists.")
    print(f"    - Subjects with single corpus (history n=1) have no within-subject baseline.")
    print(f"    - Modern K-12 materials (post-1925) need different sources (OpenStax, etc).")

    out = {
        "partition": "R-RBS-LM-78",
        "n_corpora": len(CORPUS),
        "subjects": list(subjects_list),
        "corpora": {key: {"label": kernels[key]["label"], "level": kernels[key]["level"],
                            "subject": kernels[key]["subject"], "n_tokens": kernels[key]["n_tokens"]}
                     for key, *_ in CORPUS},
        "pairwise_alignments": {f"{a}|{b}": float(s) for (a, b), s in pairwise.items()},
        "subject_stats": subject_stats,
        "subject_pairs": subject_pairs,
        "in_class_avg": in_class_avg,
        "cross_class_avg": cross_class_avg,
        "within_cross_ratio": ratio,
        "verdict": verdict,
        "coverage_gaps": ["math (no K-12 textbook on PG)",
                            "single-corpus subjects (history n=1)",
                            "modern K-12 (post-1925)"],
    }
    out_path = HERE / "R-RBS-LM-78_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
