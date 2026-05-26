"""R-RBS-LM-77 — Extend grade ladder with high-school + college material.

Per user 2026-05-26: "wish should have also identified missing college level
material" — coverage discipline failure in 73 where we claimed "asymptotic"
without testing upper bound.

Corpus extension stages three additional layers above McGuffey Grade 6:

  Kittredge & Farley "An Advanced English Grammar" (1913)
    PG 45814; 725K; late-elementary to high school grammar INSTRUCTION

  Kirkham "English Grammar in Familiar Lectures" (1829)
    PG 14070; 689K; adult comprehensive grammar INSTRUCTION

  Strunk "Elements of Style" (1918)
    PG 37134; 108K; college freshman composition INSTRUCTION

Important substrate-kind distinction:
  - McGuffey readers = reading MATERIAL (text for children to READ)
  - Kittredge/Kirkham/Strunk = language INSTRUCTION (rules ABOUT language)

These are qualitatively different substrate-content kinds. The cascade may
NOT extend cleanly between them.

Two questions:

  (1) Does the McGuffey monotone-ladder extend through Kittredge → Kirkham
      → Strunk? Test grade-distance alignment with the upper levels added.

  (2) Or does grammar-instruction form a separate substrate-class from
      reading-material? Compare within-class vs cross-class alignment.

If (1) confirms — the asymptotic claim from 73 gains support (ladder
continues upward).

If (2) confirms — we've found a substrate-class boundary at the
material-vs-instruction split. The McGuffey ladder is its own
substrate-class; grammar-instruction is its own. Different finding.

Both possible findings are within MFO §VII.6.20 form-iso ceiling.
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
    # McGuffey readers (Grades 1-6 + Primer) — reading material
    ("primer",     "/tmp/mcguffey_primer.txt",            0.5, "Primer",          "reading"),
    ("grade1",     "/tmp/mcguffey_first.txt",             1.0, "Grade 1",          "reading"),
    ("grade2",     "/tmp/mcguffey_second.txt",            2.0, "Grade 2",          "reading"),
    ("grade3",     "/tmp/mcguffey_third.txt",             3.0, "Grade 3",          "reading"),
    ("grade4",     "/tmp/mcguffey_fourth.txt",            4.0, "Grade 4",          "reading"),
    ("grade5",     "/tmp/mcguffey_fifth.txt",             5.0, "Grade 5",          "reading"),
    ("grade6",     "/tmp/mcguffey_sixth.txt",             6.0, "Grade 6",          "reading"),
    # Upper level — grammar/composition instruction
    ("kittredge",  "/tmp/kittredge_advanced_grammar.txt", 8.0, "Kittredge Adv Gr", "instruction"),
    ("kirkham",    "/tmp/goold_brown_grammar.txt",        9.0, "Kirkham (PG14070)","instruction"),
    ("strunk",     "/tmp/strunk_elements.txt",           12.0, "Strunk Elements",  "instruction"),
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
    print(f"=== R-RBS-LM-77 — Extend grade ladder with HS + college material ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Adding Kittredge / Kirkham / Strunk above McGuffey ladder\n")

    print(f"--- Building per-corpus kernels ---")
    kernels = {}
    for key, path, level, label, substrate_kind in CORPUS:
        text = strip_gutenberg(Path(path).read_text(encoding="utf-8", errors="replace"))
        table, freq, n_edges = build_kernel(text)
        kernels[key] = {"table": table, "freq": freq, "n_edges": n_edges,
                          "level": level, "label": label, "substrate_kind": substrate_kind,
                          "n_tokens": sum(freq.values())}
        print(f"  [{substrate_kind:<11s}] {label:<20s} (level {level:>4.1f}) | "
              f"vocab={len(freq):>6d} | tokens={sum(freq.values()):>7d} | "
              f"edges={n_edges:>6d} | eigvecs={len(table) if table else 0}")

    # Top eigvec content per corpus
    print(f"\n=== Top eigvec[0] content per corpus ===")
    for key, _, _, label, kind in CORPUS:
        t = kernels[key]["table"]
        if not t: continue
        print(f"  [{kind:<11s}] {label:<20s}: {' '.join(t[0]['top_tokens'][:12])}")

    # Pairwise alignment matrix
    print(f"\n=== Pairwise alignment matrix ===")
    corpus_keys = [c[0] for c in CORPUS]
    pairwise = {}
    print(f"  {'A \\\\ B':<13s}", end="")
    for b in corpus_keys: print(f"{b[:9]:>10s}", end="")
    print()
    for a in corpus_keys:
        print(f"  {a[:13]:<13s}", end="")
        for b in corpus_keys:
            if a == b:
                print(f"{'-':>10s}", end=""); continue
            key = (min(a,b), max(a,b))
            if key not in pairwise:
                pairwise[key] = find_alignment_score(kernels[a]["table"], kernels[b]["table"])
            print(f"{pairwise[key]:>+10.4f}", end="")
        print()

    # === Question 1: Does McGuffey ladder extend upward? ===
    print(f"\n=== Q1: Does McGuffey ladder extend through Kittredge → Strunk? ===")
    # Test sequence: Grade 6 ↔ Kittredge (gap +2), Grade 6 ↔ Kirkham (+3), Grade 6 ↔ Strunk (+6)
    sequence = ["grade6", "kittredge", "kirkham", "strunk"]
    print(f"  Sequential alignment (each step higher in proposed ladder):")
    for i in range(len(sequence) - 1):
        a, b = sequence[i], sequence[i+1]
        key = (min(a,b), max(a,b))
        print(f"    {kernels[a]['label']:<18s} ↔ {kernels[b]['label']:<18s} = {pairwise[key]:+.4f}")
    print(f"\n  Compare with McGuffey-internal adjacent-grade alignments (mean):")
    mcguffey_adj = []
    mcguffey_seq = ["primer", "grade1", "grade2", "grade3", "grade4", "grade5", "grade6"]
    for i in range(len(mcguffey_seq) - 1):
        a, b = mcguffey_seq[i], mcguffey_seq[i+1]
        key = (min(a,b), max(a,b))
        mcguffey_adj.append(pairwise[key])
    print(f"    Mean McGuffey adjacent alignment: {np.mean(mcguffey_adj):.4f}")
    print(f"    (If extension works, Grade6↔Kittredge↔Kirkham↔Strunk should be similar)")

    # === Question 2: Substrate-kind split? ===
    print(f"\n=== Q2: Is grammar-instruction a separate substrate-class? ===")
    reading_keys = [k for k, _, _, _, kind in CORPUS if kind == "reading"]
    instruction_keys = [k for k, _, _, _, kind in CORPUS if kind == "instruction"]

    # Within-class alignment
    within_reading = []
    for i, a in enumerate(reading_keys):
        for b in reading_keys[i+1:]:
            within_reading.append(pairwise[(min(a,b), max(a,b))])
    within_instruction = []
    for i, a in enumerate(instruction_keys):
        for b in instruction_keys[i+1:]:
            within_instruction.append(pairwise[(min(a,b), max(a,b))])
    cross_class = []
    for a in reading_keys:
        for b in instruction_keys:
            cross_class.append(pairwise[(min(a,b), max(a,b))])

    avg_wr = float(np.mean(within_reading))
    avg_wi = float(np.mean(within_instruction))
    avg_cross = float(np.mean(cross_class))
    print(f"  Within-reading (McGuffey internal) avg: {avg_wr:+.4f}  (n={len(within_reading)})")
    print(f"  Within-instruction avg:                 {avg_wi:+.4f}  (n={len(within_instruction)})")
    print(f"  Cross-class (reading ↔ instruction):    {avg_cross:+.4f}  (n={len(cross_class)})")
    ratio_within_to_cross = ((avg_wr + avg_wi) / 2) / max(avg_cross, 1e-9)
    print(f"  Within-class avg / cross-class avg ratio: {ratio_within_to_cross:.2f}")

    # === Verdicts ===
    print(f"\n=== Verdicts ===")

    # Q1 verdict
    g6_kit = pairwise[("grade6", "kittredge")]
    kit_kirk = pairwise[("kirkham", "kittredge")]
    kirk_st = pairwise[("kirkham", "strunk")]
    extension_seq = [g6_kit, kit_kirk, kirk_st]
    if all(s > 0.05 for s in extension_seq):
        q1_verdict = (f"Q1: ladder EXTENDS — Grade6→Kittredge ({g6_kit:.3f}), "
                       f"Kittredge↔Kirkham ({kit_kirk:.3f}), Kirkham↔Strunk ({kirk_st:.3f}) "
                       f"all > 0.05; ladder structure continues upward")
    else:
        q1_verdict = (f"Q1: ladder DOES NOT EXTEND cleanly — gaps in alignment "
                       f"({extension_seq}); structural progression breaks at upper level")
    print(f"  {q1_verdict}")

    # Q2 verdict
    if ratio_within_to_cross > 1.5:
        q2_verdict = (f"Q2: substrate-kind SPLIT — within-class alignment "
                       f"{ratio_within_to_cross:.2f}x cross-class. Grammar-instruction IS "
                       f"a separate substrate-class from reading-material.")
    elif ratio_within_to_cross > 1.15:
        q2_verdict = (f"Q2: WEAK substrate-kind split — ratio {ratio_within_to_cross:.2f}; "
                       f"some class signal but not sharp")
    else:
        q2_verdict = (f"Q2: NO substrate-kind split — reading and instruction "
                       f"are structurally similar (ratio {ratio_within_to_cross:.2f}). "
                       f"They form one substrate-class.")
    print(f"  {q2_verdict}")

    out = {
        "partition": "R-RBS-LM-77",
        "corpora": {key: {"label": kernels[key]["label"], "level": kernels[key]["level"],
                            "substrate_kind": kernels[key]["substrate_kind"],
                            "n_tokens": kernels[key]["n_tokens"]} for key, *_ in CORPUS},
        "pairwise_alignments": {f"{a}|{b}": float(s) for (a, b), s in pairwise.items()},
        "mcguffey_adjacent_mean": float(np.mean(mcguffey_adj)),
        "extension_sequence": {"grade6_kittredge": g6_kit, "kittredge_kirkham": kit_kirk,
                                "kirkham_strunk": kirk_st},
        "within_reading_mean": avg_wr,
        "within_instruction_mean": avg_wi,
        "cross_class_mean": avg_cross,
        "within_to_cross_ratio": ratio_within_to_cross,
        "q1_verdict": q1_verdict, "q2_verdict": q2_verdict,
    }
    out_path = HERE / "R-RBS-LM-77_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
