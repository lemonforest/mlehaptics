"""R-RBS-LM-80 — Extra-curricular substrate extension.

Per user 2026-05-26: "we can also see what adding coding camps and other extra
curricular activities contribute. maybe not helpful here but for creating
curriculum in the future" + "start number 2 so we can fetch the material".

User confirmed byte-level tokenization handles abstract music/art symbols
(from R-RBS-LM-25 ASL+Braille byte-spread work).

Seven new extra-curricular corpora added to the substrate map:

  MUSIC:    PG 65500 Essentials of Music Theory (Gardner)
  ART/PERSPECTIVE: PG 20165 Theory and Practice of Perspective (Storey)
  DRAWING:  PG 44815 Writing and Drawing Made Easy (Chinnery)
  SCOUTING: PG 29558 Boy Scouts Handbook (Boy Scouts of America)
  GAMES:    PG 39445 Hoyle's Games Modernized (Hoffmann + Hoyle)
  SPORTS:   PG 10028 Spalding's Official Baseball Guide 1913
  COOKING:  PG 65061 The Boston Cooking-School Cook Book (Fannie Farmer)

Coding is already covered by 52d codeparrot streaming kernel (separate
streaming methodology).

Combined with 79 corpus (20 K-12+ corpora), we now have 27 corpora across
10+ substrate-kinds — substantially complete substrate-coverage map for
demonstrating Finding 85 (curriculum-evaluation) and Finding 86 (substrate-
bounded safety per kernel binding).

Test questions:
  Q1: Do music, art, cooking, etc. each form distinct substrate-classes?
      (Like math at 5.02x in 79?)
  Q2: Which extra-curricular substrates OVERLAP with K-12 formal subjects?
      (Sports overlaps with rules-instruction? Art with science?)
  Q3: Glass-box readout per corpus — what substrate-content does each
      extra-curricular activity encode?

Per Finding 84: every eigvec content readout IS the glass-box attribution.
Per Finding 85: this extends the substrate-coverage library for future
curriculum-evaluation work.
Per Finding 86: each new bindable kernel enables more granular substrate-
bounded tutors (e.g., music-only tutor, art-history tutor).
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
    # Reading (McGuffey grade ladder)
    ("primer",          "/tmp/mcguffey_primer.txt",                  0.5,  "Primer",                "reading"),
    ("grade1",          "/tmp/mcguffey_first.txt",                   1.0,  "Grade 1",               "reading"),
    ("grade2",          "/tmp/mcguffey_second.txt",                  2.0,  "Grade 2",               "reading"),
    ("grade3",          "/tmp/mcguffey_third.txt",                   3.0,  "Grade 3",               "reading"),
    ("grade4",          "/tmp/mcguffey_fourth.txt",                  4.0,  "Grade 4",               "reading"),
    ("grade5",          "/tmp/mcguffey_fifth.txt",                   5.0,  "Grade 5",               "reading"),
    ("grade6",          "/tmp/mcguffey_sixth.txt",                   6.0,  "Grade 6",               "reading"),
    # Historical grammar
    ("kittredge",       "/tmp/kittredge_advanced_grammar.txt",       8.0,  "Kittredge Adv Gr",      "grammar_hist"),
    ("kirkham",         "/tmp/goold_brown_grammar.txt",              9.0,  "Kirkham Gr Lectures",   "grammar_hist"),
    ("strunk",          "/tmp/strunk_elements.txt",                  12.0, "Strunk Elements",       "grammar_hist"),
    # Modern composition
    ("openstax_writing","/tmp/openstax_writing_guide.txt",           13.0, "OS Writing Guide",      "composition_mod"),
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
    # Math
    ("openstax_elem_alg",   "/tmp/openstax_elem_algebra.txt",        7.0,  "OS Elem Algebra 2e",    "math"),
    ("openstax_inter_alg",  "/tmp/openstax_inter_algebra.txt",       10.0, "OS Inter Algebra 2e",   "math"),
    # ---- Extra-curricular (NEW) ----
    ("ec_music",        "/tmp/ec_music_theory.txt",                  6.0,  "Essentials Music Th",   "music"),
    ("ec_perspective",  "/tmp/ec_perspective_art.txt",               10.0, "Theory of Perspective", "art"),
    ("ec_drawing",      "/tmp/ec_drawing_easy.txt",                  4.0,  "Drawing Made Easy",     "art"),
    ("ec_scouting",     "/tmp/ec_scouting_boys.txt",                 5.0,  "Boy Scouts Handbook",   "scouting"),
    ("ec_games",        "/tmp/ec_hoyle_games.txt",                   8.0,  "Hoyle's Games",         "games"),
    ("ec_baseball",     "/tmp/ec_spalding_baseball.txt",             8.0,  "Spalding Baseball",     "sports"),
    ("ec_cooking",      "/tmp/ec_farmer_cookbook.txt",               8.0,  "Boston Cook Book",      "cooking"),
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
    print(f"=== R-RBS-LM-80 — Extra-curricular substrate extension ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"27 corpora across 10+ substrate-kinds")
    print(f"NEW extra-curricular: music, art, scouting, games, sports, cooking\n")

    print(f"--- Building per-corpus kernels ---")
    kernels = {}
    for key, path, level, label, subject in CORPUS:
        text = strip_gutenberg(Path(path).read_text(encoding="utf-8", errors="replace"))
        table, freq, n_edges = build_kernel(text)
        kernels[key] = {"table": table, "freq": freq, "n_edges": n_edges,
                          "level": level, "label": label, "subject": subject,
                          "n_tokens": sum(freq.values())}
        marker = " *" if subject in ("music","art","scouting","games","sports","cooking") else ""
        print(f"  [{subject:<15s} L{level:>4.1f}] {label:<24s} | vocab={len(freq):>6d} | tokens={sum(freq.values()):>7d}{marker}")

    # Glass-box readout for extra-curricular substrates specifically
    print(f"\n=== GLASS-BOX eigvec content for EXTRA-CURRICULAR substrates ===")
    extracurricular_subjects = ("music","art","scouting","games","sports","cooking")
    for key, _, _, label, subject in CORPUS:
        if subject not in extracurricular_subjects: continue
        t = kernels[key]["table"]
        if not t: continue
        print(f"\n  [{subject:<9s}] {label}:")
        for r in range(min(2, len(t))):
            print(f"    rank {r}: {' '.join(t[r]['top_tokens'][:15])}")

    # Pairwise alignment
    print(f"\n=== Pairwise alignment ({len(CORPUS)} × {len(CORPUS)}) ===")
    keys = [c[0] for c in CORPUS]
    pairwise = {}
    for i, a in enumerate(keys):
        for b in keys[i+1:]:
            pairwise[tuple(sorted((a, b)))] = find_alignment_score(kernels[a]["table"], kernels[b]["table"])

    # Substrate-class clustering
    subjects_list = ["reading", "grammar_hist", "composition_mod", "math",
                       "science", "history", "geography",
                       "music", "art", "scouting", "games", "sports", "cooking"]
    subject_members = {s: [k for k, _, _, _, sj in CORPUS if sj == s] for s in subjects_list}

    print(f"\n=== Substrate-class clustering ===")
    print(f"  {'subject':<17s} {'n':>3s} {'within':>9s} {'cross':>9s} {'ratio':>7s}")
    subject_stats = {}
    for s in subjects_list:
        members = subject_members[s]
        if len(members) < 2:
            within_avg = None
        else:
            within = [pairwise[tuple(sorted((a,b)))] for i, a in enumerate(members) for b in members[i+1:]]
            within_avg = float(np.mean(within))
        cross = []
        for a in members:
            for k in keys:
                if k == a or k in members: continue
                cross.append(pairwise[tuple(sorted((a,k)))])
        cross_avg = float(np.mean(cross)) if cross else 0.0
        ratio = within_avg / cross_avg if (within_avg is not None and cross_avg > 0) else None
        wavg_str = f"{within_avg:+.4f}" if within_avg is not None else "  n/a "
        ratio_str = f"{ratio:.2f}" if ratio is not None else " n/a "
        marker = " *" if s in extracurricular_subjects else ""
        print(f"  {s:<17s} {len(members):>3d} {wavg_str:>9s} {cross_avg:>+9.4f} {ratio_str:>7s}{marker}")
        subject_stats[s] = {"n_members": len(members), "within_avg": within_avg,
                              "cross_avg": cross_avg, "ratio": ratio}

    # Find where each extra-curricular substrate aligns most strongly
    print(f"\n=== Where each extra-curricular substrate aligns most ===")
    for key, _, _, label, subject in CORPUS:
        if subject not in extracurricular_subjects: continue
        alignments = []
        for k in keys:
            if k == key: continue
            alignments.append((k, pairwise[tuple(sorted((key, k)))]))
        alignments.sort(key=lambda x: -x[1])
        print(f"\n  {label} ({subject}):")
        for k, s in alignments[:5]:
            print(f"    ↔ {kernels[k]['label']:<26s} ({kernels[k]['subject']:<15s}) = {s:+.4f}")

    # Coverage map summary
    print(f"\n=== Coverage map summary (substrate-class distinctness ratios) ===")
    print(f"  Substrate-class           | n |  within  | cross   | ratio | rank")
    print(f"  --------------------------|---|----------|---------|-------|-----")
    ranked = sorted([(s, st) for s, st in subject_stats.items() if st["ratio"] is not None],
                     key=lambda x: -x[1]["ratio"])
    for i, (s, st) in enumerate(ranked):
        marker = "*" if s in extracurricular_subjects else " "
        print(f"  {s:<25s} | {st['n_members']:>1d} | {st['within_avg']:>+7.4f} | "
              f"{st['cross_avg']:>+7.4f} | {st['ratio']:>5.2f} | {i+1:>3d} {marker}")

    out = {
        "partition": "R-RBS-LM-80",
        "n_corpora": len(CORPUS),
        "subjects": subjects_list,
        "corpora": {key: {"label": kernels[key]["label"], "level": kernels[key]["level"],
                            "subject": kernels[key]["subject"], "n_tokens": kernels[key]["n_tokens"]}
                     for key, *_ in CORPUS},
        "pairwise_alignments": {f"{a}|{b}": float(s) for (a, b), s in pairwise.items()},
        "subject_stats": subject_stats,
    }
    out_path = HERE / "R-RBS-LM-80_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
