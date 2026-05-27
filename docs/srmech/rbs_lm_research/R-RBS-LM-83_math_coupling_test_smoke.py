"""R-RBS-LM-83 — Math as 1st-order coupling test (Finding 97 ADDENDUM).

Empirical falsification of Finding 97 ADDENDUM:
  Math is the unique substrate-content irrep — even when we add the
  substrates math actually couples with (kinesthetic learning,
  counting-perception, procedural-algorithm), math's within/cross
  ratio should DROP MODESTLY but stay at TOP of ranking.

  If ratio stays > 3.0 after kinesthetic additions → math IS unique
  substrate-content irrep CONFIRMED.
  If ratio drops < 2.0 → math is composition over substrates AFTER ALL.

Three Montessori corpora added (kinesthetic / procedural / hands-on):
  PG 39863  The Montessori Method (Maria Montessori; 737K)
  PG 42869  The Montessori Elementary Material (751K)
  PG 29635  Dr. Montessori's Own Handbook (173K)

These corpora describe kinesthetic learning materials (manipulables for
counting, procedural step-by-step learning, hands-on object handling).
If math is a composition over these substrates, math kernels should
align tightly with Montessori kernels.

Reuses R-RBS-LM-79 corpus + adds the 3 Montessori corpora.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

# Subset of relevant corpora from 79 + new Montessori additions
CORPUS = [
    # Math (the alleged unique irrep)
    ("openstax_elem_alg",   "/tmp/openstax_elem_algebra.txt",        "math"),
    ("openstax_inter_alg",  "/tmp/openstax_inter_algebra.txt",       "math"),
    # Other K-12 subjects (for ratio comparison)
    ("kjv_nt",              "/tmp/kjv_new_testament.txt",            "reading_religious"),
    ("plato",               "/tmp/plato_republic.txt",               "philosophy"),
    ("frankenstein",        "/tmp/frankenstein.txt",                 "novel"),
    ("milton",              "/tmp/paradise_lost.txt",                "poetry"),
    # Science
    ("astronomy_yf",        "/tmp/k12_astronomy_youngfolks.txt",     "science"),
    ("starland",            "/tmp/k12_starland.txt",                 "science"),
    ("childs_health",       "/tmp/k12_childs_health_primer.txt",     "science"),
    # Geography
    ("home_geography",      "/tmp/k12_home_geography.txt",           "geography"),
    ("commercial_geog",     "/tmp/k12_commercial_geography.txt",     "geography"),
    # NEW: Montessori (candidate substrates math couples with)
    ("montessori_method",   "/tmp/montessori_method.txt",            "kinesthetic"),
    ("montessori_elem",     "/tmp/montessori_elementary.txt",        "kinesthetic"),
    ("montessori_handbook", "/tmp/montessori_handbook.txt",          "kinesthetic"),
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
    if N < 8: return None
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
    if not edges: return None
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_PER_EIGVEC]
        top_tokens = [vocab[i] for i in top_idx]
        table.append({"top_tokens": top_tokens, "token_set": set(top_tokens)})
    return table


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
    print(f"=== R-RBS-LM-83 — Math as 1st-order coupling test ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Adding Montessori (kinesthetic) corpora; will math's ratio drop?\n")

    print(f"--- Building kernels ---")
    kernels = {}
    for key, path, subj in CORPUS:
        text = strip_gutenberg(Path(path).read_text(encoding="utf-8", errors="replace"))
        table = build_kernel(text)
        kernels[key] = {"table": table, "subject": subj}
        marker = " *" if subj == "kinesthetic" else ""
        print(f"  [{subj:<18s}] {key:<22s}: {len(table)} eigvecs{marker}")

    print(f"\n--- Montessori eigvec content (glass-box check) ---")
    for key in ["montessori_method", "montessori_elem", "montessori_handbook"]:
        t = kernels[key]["table"]
        print(f"\n  {key}:")
        for r in range(2):
            print(f"    rank {r}: {' '.join(t[r]['top_tokens'][:12])}")

    # Pairwise
    keys = [c[0] for c in CORPUS]
    pairwise = {}
    for i, a in enumerate(keys):
        for b in keys[i+1:]:
            pairwise[tuple(sorted((a, b)))] = find_alignment_score(kernels[a]["table"], kernels[b]["table"])

    # === Math kernel alignments — where does math align most? ===
    print(f"\n=== Math kernel alignments — does Montessori help? ===")
    for math_key in ["openstax_elem_alg", "openstax_inter_alg"]:
        alignments = []
        for k in keys:
            if k == math_key: continue
            alignments.append((k, pairwise[tuple(sorted((math_key, k)))]))
        alignments.sort(key=lambda x: -x[1])
        print(f"\n  {math_key} alignments (top 8):")
        for k, s in alignments[:8]:
            marker = "*" if kernels[k]['subject'] == "kinesthetic" else " "
            print(f"    ↔ {k:<22s} ({kernels[k]['subject']:<18s}) = {s:+.4f}{marker}")

    # === Math within/cross ratio with kinesthetic in cross set ===
    math_keys = [k for k, _, s in CORPUS if s == "math"]
    other_keys = [k for k, _, s in CORPUS if s != "math"]
    kinesthetic_keys = [k for k, _, s in CORPUS if s == "kinesthetic"]
    non_math_non_kine = [k for k in other_keys if k not in kinesthetic_keys]

    # Within math
    within_math = pairwise[tuple(sorted(math_keys))]

    # Cross to all non-math
    cross_all = []
    for m in math_keys:
        for k in other_keys:
            cross_all.append(pairwise[tuple(sorted((m, k)))])

    # Cross to kinesthetic specifically
    cross_kine = []
    for m in math_keys:
        for k in kinesthetic_keys:
            cross_kine.append(pairwise[tuple(sorted((m, k)))])

    # Cross to non-kinesthetic (baseline; same as 80's math cross)
    cross_non_kine = []
    for m in math_keys:
        for k in non_math_non_kine:
            cross_non_kine.append(pairwise[tuple(sorted((m, k)))])

    print(f"\n=== Math within/cross ratio analysis ===")
    print(f"  Within-math alignment:           {within_math:+.4f}")
    print(f"  Cross to ALL non-math (n={len(cross_all)}):     mean = {float(np.mean(cross_all)):+.4f}")
    print(f"  Cross to KINESTHETIC (n={len(cross_kine)}):   mean = {float(np.mean(cross_kine)):+.4f}")
    print(f"  Cross to NON-KINESTHETIC (n={len(cross_non_kine)}): mean = {float(np.mean(cross_non_kine)):+.4f}")

    ratio_with_kine = within_math / float(np.mean(cross_all))
    ratio_no_kine = within_math / float(np.mean(cross_non_kine))

    print(f"\n  Within/cross ratio WITH kinesthetic in cross set:    {ratio_with_kine:.2f}")
    print(f"  Within/cross ratio WITHOUT kinesthetic (80 baseline): {ratio_no_kine:.2f}")
    print(f"  Ratio change from adding Montessori: {ratio_with_kine - ratio_no_kine:+.2f}")

    # === Verdict per Finding 97 ADDENDUM ===
    print(f"\n=== Finding 97 ADDENDUM falsification verdict ===")
    if ratio_with_kine > 3.0:
        verdict = (f"MATH IS UNIQUE SUBSTRATE-CONTENT IRREP CONFIRMED. "
                   f"Even with Montessori (kinesthetic/procedural) corpora added, "
                   f"math's within/cross ratio = {ratio_with_kine:.2f} stays > 3.0. "
                   f"Math substrate-content is irreducible per delivery; the 'irrep' "
                   f"appearance is NOT an artifact of incomplete substrate catalog.")
    elif ratio_with_kine > 2.0:
        verdict = (f"MATH IS PARTIALLY-DECOMPOSABLE. "
                   f"Math's ratio dropped from {ratio_no_kine:.2f} → {ratio_with_kine:.2f} "
                   f"when kinesthetic substrates added. Significant but not complete decomposition. "
                   f"Math remains the highest-ratio substrate but is coupled to kinesthetic "
                   f"more than the baseline analysis showed.")
    else:
        verdict = (f"MATH AS UNIQUE IRREP FALSIFIED. "
                   f"Ratio dropped from {ratio_no_kine:.2f} → {ratio_with_kine:.2f} (below 2.0). "
                   f"Math IS a composition over kinesthetic / procedural / counting-perception "
                   f"substrates after all. The 'irrep' appearance in 80 was an artifact of "
                   f"incomplete substrate-catalog coverage.")
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-83",
        "math_within_alignment": within_math,
        "cross_to_all_non_math": float(np.mean(cross_all)),
        "cross_to_kinesthetic_only": float(np.mean(cross_kine)),
        "cross_to_non_kinesthetic": float(np.mean(cross_non_kine)),
        "ratio_with_kinesthetic": ratio_with_kine,
        "ratio_without_kinesthetic": ratio_no_kine,
        "ratio_change": ratio_with_kine - ratio_no_kine,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-83_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
