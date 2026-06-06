#!/usr/bin/env python3
"""R-RBS-LM-END2 — does MORE DATA unlock the longer context? (F434's pre-stated prediction)

F434 found the trigram saturates at 400k tokens (the 2-word context is data-starved). The
pre-stated claim: the saturation is DATA-bound, not a law — with more text the trigram
should start to help. This tests it: a fixed held-out set, training on INCREASING data
(findings + the big research notebooks ≈ 1M+ tokens), tracking the trigram's gain over the
bigram as the corpus grows. If the gain climbs with data, the transparency residue is
(partly) DATA — exactly the LLM's trillions-of-tokens advantage.

Run:  <sci-venv or plain>/bin/python R-RBS-LM-END2_data_scaling_residue.py
Composes F434 (the end-to-end stage) · F433 (the residue = data + representation) · F172.
Witten-Bell backoff. Defensive / no-lineage.
"""
import re
import glob
import os
import math
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
NOTEBOOKS = [
    "docs/antikythera-maths/mfo_spectral_research_notebook.md",
    "docs/srmech/srmech_research_notebook.md",
    "docs/antikythera-maths/ephemerides_spectral_research_notebook.md",
    "docs/chess-maths/chess_spectral_research_notebook.md",
]


def clean_sentences(text):
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'`[^`]*`', ' ', text)
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'\|[^\n]*\|', ' ', text)                  # drop markdown tables
    text = re.sub(r'[*#>|_\[\]()]', ' ', text)
    sents = []
    for sent in re.split(r'(?<=[.!?])\s+', text):
        ws = re.findall(r"[a-z]+(?:'[a-z]+)?", sent.lower())
        if ws:
            sents.append(['<s>'] + ws + ['</s>'])            # each item = one sentence
    return sents


def load_all():
    import random as _r
    sents = []
    for p in sorted(glob.glob(os.path.join(HERE, "R-RBS-LM-FINDING_*.md"))):
        sents += clean_sentences(open(p, encoding='utf-8').read())
    for rel in NOTEBOOKS:
        fp = os.path.join(ROOT, rel)
        if os.path.exists(fp):
            sents += clean_sentences(open(fp, encoding='utf-8').read())
    _r.Random(20260606).shuffle(sents)                       # SHUFFLE sentences → same-distribution split
    return [w for s in sents for w in s]


def build(toks):
    uni = defaultdict(int); bi = defaultdict(lambda: defaultdict(int)); tri = defaultdict(lambda: defaultdict(int))
    for i, w in enumerate(toks):
        uni[w] += 1
        if i >= 1: bi[toks[i-1]][w] += 1
        if i >= 2: tri[(toks[i-2], toks[i-1])][w] += 1
    return uni, bi, tri, len(uni), sum(uni.values())


def p_uni(w, uni, V, N): return (uni.get(w, 0) + 1) / (N + V)
def p_bi(w, w1, uni, bi, V, N):
    d = bi.get(w1)
    if not d: return p_uni(w, uni, V, N)
    s = sum(d.values()); lam = s / (s + len(d))
    return lam * (d.get(w, 0) / s) + (1 - lam) * p_uni(w, uni, V, N)
def p_tri(w, w1, w2, uni, bi, tri, V, N):
    d = tri.get((w2, w1))
    if not d: return p_bi(w, w1, uni, bi, V, N)
    s = sum(d.values()); lam = s / (s + len(d))
    return lam * (d.get(w, 0) / s) + (1 - lam) * p_bi(w, w1, uni, bi, V, N)


def ppl(test, order, uni, bi, tri, V, N):
    lp = 0.0; n = 0
    for i, w in enumerate(test):
        if w == '<s>': continue
        w1 = test[i-1] if i >= 1 else None
        w2 = test[i-2] if i >= 2 else None
        if order == 2 or w2 is None or w1 is None:
            p = p_bi(w, w1, uni, bi, V, N) if w1 else p_uni(w, uni, V, N)
        else:
            p = p_tri(w, w1, w2, uni, bi, tri, V, N)
        lp += math.log(max(p, 1e-12)); n += 1
    return math.exp(-lp / n)


def main():
    toks = load_all()
    # fixed held-out (last 5%), train pool = rest
    hcut = int(len(toks) * 0.95)
    pool, test = toks[:hcut], toks[hcut:]
    print(f"=== data-scaling: does more PAST unlock the 2-word context? (F434 prediction) ===")
    print(f"combined corpus (findings + 4 research notebooks): {len(toks):,} tokens | held-out {len(test):,}\n")
    print(f"{'train tokens':>13} | {'bigram PPL':>11} | {'trigram PPL':>11} | trigram gain over bigram")
    for frac in (0.05, 0.15, 0.4, 0.7, 1.0):
        m = int(len(pool) * frac)
        uni, bi, tri, V, N = build(pool[:m])
        pb = ppl(test, 2, uni, bi, tri, V, N)
        pt = ppl(test, 3, uni, bi, tri, V, N)
        gain = 100 * (pb - pt) / pb
        bar = '█' * max(0, int(gain * 2))
        print(f"{m:>13,} | {pb:>11.1f} | {pt:>11.1f} | {gain:+5.1f}%  {bar}")
    print(f"\n  ⇒ if the trigram gain CLIMBS with data, the saturation was DATA-bound (F434 confirmed):")
    print(f"    the transparency residue is partly the LLM's trillions-of-tokens advantage, not a")
    print(f"    law — longer transparent context unlocks as the past grows. (Representation residue")
    print(f"    — truly long-range/compositional coherence — is what stays beyond any n-gram.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
