"""R-RBS-LM-109 — Music theory cross-substrate irrep test (§2.8.5 handoff)

Mirrors R-RBS-LM-83 methodology against music-theory corpora.

Hypothesis: ANY domain whose substrate-content is irreducible should exhibit
within/cross alignment ratio that SURVIVES adding its candidate composing
substrates. The §2.8.5 prediction: music theory should behave like math (F104,
F109) under this test.

SCOPE NOTE — REDUCED CORPUS SCOPE:
  Handoff requested 3 music corpora (Helmholtz / Rameau / Hawkins) + 3
  composing-substrate corpora (Tyndall / Burke / Kant). These PG IDs were
  fiddly to verify in-session (PG 37113 returned wrong content; PG 16182
  returned Browning letters; etc.). For this preliminary test we use:

  Music: ec_music_theory.txt (PG, 'Essentials of Music Theory: Elementary')
    SPLIT INTO TWO HALVES for within-music alignment baseline.

  Non-music baselines (cached from prior R-RBS-LM work):
    frankenstein (novel), plato_republic (philosophy), kjv_new_testament
    (religious), paradise_lost (poetry), astronomy_yf (science),
    iliad_pope (classical_poetry)

  F104-strongest composing-substrate test: openstax math corpora
    (the F104 unique irrep — strongest possible composing substrate test)

  Aesthetic stand-in: ec_perspective_art.txt (drawing/art/aesthetic content)
    NOT Burke/Kant proper; surrogate per scope constraints.

  Tyndall 'Sound' (physics_acoustic): NOT CACHED. Documented gap.

VERDICT THRESHOLDS (R-RBS-LM-83 mirror):
  ratio > 3.0: MUSIC THEORY IS UNIQUE SUBSTRATE-CONTENT IRREP CONFIRMED
  2.0 ≤ ratio ≤ 3.0: PARTIAL composition-over-some-substrates
  ratio < 2.0: COMPOSITION CONFIRMED

OUTPUT FORMAT: matches R-RBS-LM-83_results.json schema; reduced scope flagged.
"""
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

# Corpus list (reduced scope per scope note above)
CORPUS = [
    # Music — split-half (1 source corpus → 2 sub-corpora for within-music)
    ("music_h1",        "/tmp/ec_music_theory.txt",            "music"),
    ("music_h2",        "/tmp/ec_music_theory.txt",            "music"),
    # Non-music baselines
    ("frankenstein",    "/tmp/frankenstein.txt",               "novel"),
    ("plato",           "/tmp/plato_republic.txt",             "philosophy"),
    ("kjv_nt",          "/tmp/kjv_new_testament.txt",          "reading_religious"),
    ("milton",          "/tmp/paradise_lost.txt",              "poetry"),
    ("astronomy_yf",    "/tmp/k12_astronomy_youngfolks.txt",   "science"),
    ("iliad_pope",      "/tmp/iliad_pope.txt",                 "classical_poetry"),
    # Composing-substrate falsifier set (the strongest possible per handoff)
    ("openstax_elem",   "/tmp/openstax_elem_algebra.txt",      "math"),
    ("openstax_inter",  "/tmp/openstax_inter_algebra.txt",     "math"),
    # Aesthetic stand-in (handoff requested Burke/Kant — not cached;
    # ec_perspective_art is a SURROGATE for aesthetic composing substrate)
    ("perspective_art", "/tmp/ec_perspective_art.txt",         "aesthetic_kinesthetic"),
    # Tyndall Sound (physics_acoustic) — GAP; NOT CACHED
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
            for j in range(i + 1, min(i + COOCCURRENCE_DISTANCE, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges[(min(a, b), max(a, b))] += 1
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


def load_music_split_half():
    """Load ec_music_theory and split into 2 halves for music within-alignment."""
    text = Path("/tmp/ec_music_theory.txt").read_text(encoding="utf-8", errors="replace")
    text = strip_gutenberg(text)
    mid = len(text) // 2
    h1 = text[:mid]
    h2 = text[mid:]
    return h1, h2


def main():
    print(f"=== R-RBS-LM-109 — Music theory cross-substrate irrep test (§2.8.5) ===\n")
    print(f"srmech: {srmech.__version__}\n")

    print(f"--- Building kernels ---")
    kernels = {}
    music_h1, music_h2 = load_music_split_half()
    music_texts = {"music_h1": music_h1, "music_h2": music_h2}

    for key, path, subj in CORPUS:
        if key in music_texts:
            text = music_texts[key]
        else:
            try:
                text = strip_gutenberg(
                    Path(path).read_text(encoding="utf-8", errors="replace")
                )
            except FileNotFoundError:
                print(f"  [MISSING] {key}: {path} not found; skipping")
                continue
        table = build_kernel(text)
        if table is None:
            print(f"  [EMPTY KERNEL] {key}: skipping")
            continue
        kernels[key] = {"table": table, "subject": subj}
        marker = " *" if subj == "music" else ""
        print(f"  [{subj:<22s}] {key:<22s}: {len(table)} eigvecs{marker}")

    # Music eigvec content (glass-box check)
    print(f"\n--- Music kernel content (glass-box check) ---")
    for key in ["music_h1", "music_h2"]:
        if key in kernels:
            t = kernels[key]["table"]
            print(f"\n  {key}:")
            for r in range(2):
                print(f"    rank {r}: {' '.join(t[r]['top_tokens'][:12])}")

    # Pairwise alignments
    keys = list(kernels.keys())
    pairwise = {}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            pairwise[tuple(sorted((a, b)))] = find_alignment_score(
                kernels[a]["table"], kernels[b]["table"]
            )

    # Music kernel alignments — where does music align most?
    print(f"\n=== Music kernel alignments — where does music align? ===")
    for music_key in ["music_h1", "music_h2"]:
        if music_key not in kernels:
            continue
        alignments = []
        for k in keys:
            if k == music_key: continue
            alignments.append((k, pairwise[tuple(sorted((music_key, k)))]))
        alignments.sort(key=lambda x: -x[1])
        print(f"\n  {music_key} alignments (top 8):")
        for k, s in alignments[:8]:
            subj = kernels[k]['subject']
            marker = (
                "*" if subj == "music" else
                "M" if subj == "math" else
                "A" if subj == "aesthetic_kinesthetic" else " "
            )
            print(f"    ↔ {k:<22s} ({subj:<22s}) = {s:+.4f} {marker}")

    # Within/cross ratio analysis
    music_keys = [k for k in keys if kernels[k]["subject"] == "music"]
    non_music_keys = [k for k in keys if kernels[k]["subject"] != "music"]
    math_keys = [k for k in keys if kernels[k]["subject"] == "math"]
    aesthetic_keys = [k for k in keys if kernels[k]["subject"] == "aesthetic_kinesthetic"]
    baseline_non_music_keys = [
        k for k in non_music_keys
        if kernels[k]["subject"] not in ("math", "aesthetic_kinesthetic", "physics_acoustic")
    ]

    # Within-music alignment
    within_music = None
    if len(music_keys) >= 2:
        within_music = pairwise[tuple(sorted(music_keys[:2]))]

    # Cross to ALL non-music
    cross_all = []
    for m in music_keys:
        for k in non_music_keys:
            cross_all.append(pairwise[tuple(sorted((m, k)))])

    # Cross to aesthetic
    cross_aesthetic = []
    for m in music_keys:
        for k in aesthetic_keys:
            cross_aesthetic.append(pairwise[tuple(sorted((m, k)))])

    # Cross to math (F104 strongest test)
    cross_math = []
    for m in music_keys:
        for k in math_keys:
            cross_math.append(pairwise[tuple(sorted((m, k)))])

    # Cross to baseline (non-music, non-math, non-aesthetic)
    cross_baseline_only = []
    for m in music_keys:
        for k in baseline_non_music_keys:
            cross_baseline_only.append(pairwise[tuple(sorted((m, k)))])

    print(f"\n=== Within/cross ratio analysis ===")
    print(f"  Within-music (split-half h1↔h2):              {within_music:+.4f}" if within_music is not None else "  Within-music: NOT COMPUTABLE")
    print(f"  Cross to ALL non-music (n={len(cross_all)}):           mean = {float(np.mean(cross_all)):+.4f}")
    print(f"  Cross to aesthetic (n={len(cross_aesthetic)}):         mean = {float(np.mean(cross_aesthetic)):+.4f}" if cross_aesthetic else "  Cross to aesthetic: n=0")
    print(f"  Cross to math (F104 irrep) (n={len(cross_math)}):  mean = {float(np.mean(cross_math)):+.4f}" if cross_math else "  Cross to math: n=0")
    print(f"  Cross to baseline-only (n={len(cross_baseline_only)}):   mean = {float(np.mean(cross_baseline_only)):+.4f}" if cross_baseline_only else "  Cross to baseline-only: n=0")

    if within_music is None or not cross_all:
        print("\n  ABORT: insufficient corpora for ratio calculation")
        return

    ratio_full = within_music / float(np.mean(cross_all))
    ratio_baseline_only = (within_music / float(np.mean(cross_baseline_only))) if cross_baseline_only else None
    ratio_minus_math = (within_music / float(np.mean(cross_math))) if cross_math else None
    ratio_change = (ratio_full - ratio_baseline_only) if ratio_baseline_only is not None else None

    print(f"\n  ratio_with_composing_substrates (within / cross_all): {ratio_full:+.4f}")
    if ratio_baseline_only is not None:
        print(f"  ratio_baseline_only (within / cross_baseline):         {ratio_baseline_only:+.4f}")
        print(f"  ratio_change (full - baseline):                        {ratio_change:+.4f}")
    if ratio_minus_math is not None:
        print(f"  ratio_minus_math (within / cross_math; F104 test):     {ratio_minus_math:+.4f}")

    # Verdict per handoff thresholds
    print(f"\n=== Verdict ===")
    if ratio_full > 3.0:
        verdict = (
            f"MUSIC THEORY IS UNIQUE SUBSTRATE-CONTENT IRREP CONFIRMED. "
            f"Ratio = {ratio_full:.2f} survives 3.0 threshold."
        )
    elif ratio_full >= 2.0:
        verdict = (
            f"PARTIAL — composition-over-some-substrates evident. "
            f"Ratio = {ratio_full:.2f} ∈ [2.0, 3.0]; substrate not fully irrep "
            f"at this corpus scale."
        )
    else:
        verdict = (
            f"COMPOSITION CONFIRMED — music theory is NOT substrate-content "
            f"irrep at generational layer; ratio = {ratio_full:.2f} < 2.0. "
            f"F104→F109 framework substrate-emergent-density-as-irrep reading "
            f"needs scope refinement for music."
        )
    print(f"  {verdict}")

    # Honest scope note
    print(f"\n=== Scope limitations ===")
    print(f"  • 1 music source corpus (ec_music_theory.txt), split-half for within")
    print(f"  • No Helmholtz / Rameau / Hawkins (PG IDs needed verification)")
    print(f"  • No Tyndall 'Sound' (physics_acoustic composing substrate gap)")
    print(f"  • Burke/Kant 'aesthetic' substrate proxied via ec_perspective_art")
    print(f"  • Full-scope rerun deferred until canonical PG IDs verified +"
          f" corpora cached")
    print(f"  • Klein-4 composability variant NOT run (deferred to v2)")

    # Output JSON
    out_path = HERE / "R-RBS-LM-109_results.json"
    output = {
        "partition": "R-RBS-LM-109",
        "scope": "REDUCED — 1 music corpus split-half; no Tyndall/Helmholtz/Rameau/Hawkins/Burke/Kant proper",
        "music_within_alignment": within_music,
        "cross_to_all_non_music": float(np.mean(cross_all)) if cross_all else None,
        "cross_to_aesthetic_only": float(np.mean(cross_aesthetic)) if cross_aesthetic else None,
        "cross_to_math_only": float(np.mean(cross_math)) if cross_math else None,
        "cross_to_baseline_only": float(np.mean(cross_baseline_only)) if cross_baseline_only else None,
        "ratio_with_composing_substrates": ratio_full,
        "ratio_baseline_only": ratio_baseline_only,
        "ratio_minus_math": ratio_minus_math,
        "ratio_change": ratio_change,
        "verdict": verdict,
        "kernels_included": list(kernels.keys()),
        "corpus_gaps": [
            "Helmholtz 'Sensations of Tone' (proper PG ID needs verification)",
            "Rameau 'Treatise on Harmony' (canonical English edition)",
            "Hawkins 'History of Music' (multi-volume)",
            "Tyndall 'Sound' (physics_acoustic substrate)",
            "Burke 'Sublime and Beautiful' (aesthetic substrate)",
            "Kant 'Critique of Judgment' (aesthetic substrate)",
        ],
        "klein4_composability_variant": "NOT RUN — deferred to v2 per scope",
    }
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
