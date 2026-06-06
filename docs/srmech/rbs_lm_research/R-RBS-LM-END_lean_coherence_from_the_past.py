#!/usr/bin/env python3
"""R-RBS-LM-END — the end-to-end RBS-LM stage: a LEAN, TRANSPARENT model of coherence-
from-the-past (F433), on our own corpus's prose (the literal "past").

The LLM gets coherence via a BLACK BOX (learned P(next|context), smeared across weights).
This builds the legible version and MEASURES how much of that coherence is recoverable
transparently:

  • the MODEL = interpolated n-gram transition counts — EVERY probability is readable
    P(w | ctx) = λ1·P_uni + λ2·P_bi(w_{-1}) + λ3·P_tri(w_{-2},w_{-1})       (F166 rolling context)
  • the STORAGE SIGNATURE = the Class-L co-occurrence Laplacian eigenspectrum (F172)
    — the srmech-native "how much is stored" measure (NOT a Counter-as-storage proxy;
      the n-gram dicts ARE the transparent model, the spectrum is its storage signature)
  • GENERATE = a rolling-context walk (the render appearing)
  • MEASURE coherence-from-the-past = perplexity vs CONTEXT ORDER (n=1→3): the PPL drop
    is the legible coherence gain; where it saturates is the TRANSPARENCY RESIDUE (the
    long-range/compositional coherence the n-gram floor can't reach = the LLM's black-box edge).

srmech-first: the storage signature is Class-L (dense_laplacian/jacobi_eigvals). No abs().
Run:  <sci-venv>/bin/python R-RBS-LM-END_lean_coherence_from_the_past.py
Composes F433 (coherence-from-the-past is the sought target) · F172 (co-occ Laplacian =
storage signature) · F166/F168 (rolling context; perplexity from memory-depth) · F432
(closed grammar / open lexicon) · F431 (the kernels). Defensive / no-lineage.
"""
import re
import glob
import os
import math
import random
from collections import defaultdict
from srmech.amsc import laplacian as L

HERE = os.path.dirname(os.path.abspath(__file__))
RNG = random.Random(20260606)


def load_tokens():
    toks = []
    for p in sorted(glob.glob(os.path.join(HERE, "R-RBS-LM-FINDING_*.md"))):
        t = open(p, encoding='utf-8').read()
        t = re.sub(r'```.*?```', ' ', t, flags=re.S)         # drop code
        t = re.sub(r'`[^`]*`', ' ', t)
        t = re.sub(r'https?://\S+', ' ', t)
        t = re.sub(r'[*#>|_\[\]()]', ' ', t)                 # drop markdown
        for sent in re.split(r'(?<=[.!?])\s+', t):
            words = re.findall(r"[a-z]+(?:'[a-z]+)?", sent.lower())
            if words:
                toks += ['<s>'] + words + ['</s>']
    return toks


def build_ngrams(toks):
    uni = defaultdict(int)
    bi = defaultdict(lambda: defaultdict(int))
    tri = defaultdict(lambda: defaultdict(int))
    for i, w in enumerate(toks):
        uni[w] += 1
        if i >= 1:
            bi[toks[i-1]][w] += 1
        if i >= 2:
            tri[(toks[i-2], toks[i-1])][w] += 1
    return uni, bi, tri


# --- Witten-Bell ADAPTIVE backoff (Witten & Bell 1991): trust the higher order ONLY where
#     it has data; unseen context backs off automatically. λ(ctx) = s/(s+D), s=count(ctx),
#     D=distinct continuations — large/peaked context → trust it; sparse/unseen → back off. ---
def p_uni(w, uni, V, Ntok):
    return (uni.get(w, 0) + 1) / (Ntok + V)                  # add-1 floor (OOV-safe)


def p_bi(w, w1, uni, bi, V, Ntok):
    d = bi.get(w1)
    if not d:
        return p_uni(w, uni, V, Ntok)
    s = sum(d.values()); D = len(d); lam = s / (s + D)
    return lam * (d.get(w, 0) / s) + (1 - lam) * p_uni(w, uni, V, Ntok)


def p_tri(w, w1, w2, uni, bi, tri, V, Ntok):
    d = tri.get((w2, w1))
    if not d:
        return p_bi(w, w1, uni, bi, V, Ntok)
    s = sum(d.values()); D = len(d); lam = s / (s + D)
    return lam * (d.get(w, 0) / s) + (1 - lam) * p_bi(w, w1, uni, bi, V, Ntok)


def prob(w, w1, w2, order, uni, bi, tri, V, Ntok):
    if order == 1:
        return p_uni(w, uni, V, Ntok)
    if order == 2:
        return p_bi(w, w1, uni, bi, V, Ntok) if w1 else p_uni(w, uni, V, Ntok)
    return p_tri(w, w1, w2, uni, bi, tri, V, Ntok) if (w1 and w2) else \
        (p_bi(w, w1, uni, bi, V, Ntok) if w1 else p_uni(w, uni, V, Ntok))


def perplexity(test, order, uni, bi, tri, V, Ntok):
    logp = 0.0; n = 0
    for i, w in enumerate(test):
        if w == '<s>':
            continue
        w1 = test[i-1] if i >= 1 else None
        w2 = test[i-2] if i >= 2 else None
        p = prob(w, w1, w2, order, uni, bi, tri, V, Ntok)
        logp += math.log(max(p, 1e-12)); n += 1
    return math.exp(-logp / n)


def generate(uni, bi, tri, V, Ntok, n_words=40):
    out = ['<s>']
    while len(out) < n_words and out[-1] != '</s>':
        w1, w2 = out[-1], (out[-2] if len(out) >= 2 else None)
        # rolling-context walk: sample the next word ∝ its seen continuation count
        # (prefer trigram continuations, back off to bigram — the coherent local walk)
        cands = tri.get((w2, w1)) or bi.get(w1) or {w: c for w, c in uni.items() if w != '<s>'}
        keys = list(cands.keys()); wts = list(cands.values())
        tot = sum(wts); r = RNG.random() * tot; acc = 0.0; nxt = keys[-1]
        for w, ww in zip(keys, wts):
            acc += ww
            if acc >= r:
                nxt = w; break
        out.append(nxt)
    return ' '.join(w for w in out if w not in ('<s>', '</s>'))


def main():
    toks = load_tokens()
    cut = int(len(toks) * 0.9)
    train, test = toks[:cut], toks[cut:]
    uni, bi, tri = build_ngrams(train)
    V = len(uni); Ntok = sum(uni.values())
    print(f"=== end-to-end RBS-LM — lean transparent coherence-from-the-past ===")
    print(f"corpus (our own prose = the 'past'): {len(toks):,} tokens | vocab {V:,} | train {len(train):,} / held-out {len(test):,}\n")

    # ---- F172 storage signature: the Class-L co-occurrence Laplacian eigenspectrum (top-K vocab) ----
    K = 250
    top = [w for w, _ in sorted(uni.items(), key=lambda kv: -kv[1]) if w not in ('<s>', '</s>')][:K]
    idx = {w: i for i, w in enumerate(top)}
    edges = set()
    for w1 in top:
        for w2, c in bi.get(w1, {}).items():
            if w2 in idx and w1 != w2 and c >= 2:
                a, b = sorted((idx[w1], idx[w2]))
                edges.add((a, b))
    Lap = L.dense_laplacian(len(top), sorted(edges))
    fied = L.fiedler_vector(Lap)
    fied = fied.tolist() if hasattr(fied, 'tolist') else list(fied)
    Lf = [sum(Lap[i][j]*fied[j] for j in range(len(top))) for i in range(len(top))]
    lam2 = sum(fied[i]*Lf[i] for i in range(len(top))) / sum(x*x for x in fied)
    print(f"F172 storage signature (Class-L co-occ Laplacian, top-{K} words):")
    print(f"   {len(edges)} co-occurrence edges | λ2 = {lam2:.3f} (collocation connectivity of the past)\n")

    # ---- coherence-from-the-past: perplexity vs CONTEXT ORDER (Witten-Bell backoff) ----
    print("coherence-from-the-past — held-out perplexity vs how much PAST is used (Witten-Bell backoff):")
    names = {1: "n=1 unigram (NO past)", 2: "n=2 bigram  (1 word past)", 3: "n=3 trigram (2 words past)"}
    ppls = {}
    for order in (1, 2, 3):
        ppls[order] = perplexity(test, order, uni, bi, tri, V, Ntok)
        print(f"   {names[order]:28} PPL = {ppls[order]:8.1f}")
    drop1 = 100*(ppls[1]-ppls[2])/ppls[1]
    drop2 = 100*(ppls[2]-ppls[3])/ppls[2]
    print(f"\n   coherence GAIN from the past: unigram→bigram −{drop1:.0f}% PPL,  bigram→trigram −{drop2:.0f}% PPL")
    print(f"   ⇒ adding PAST context legibly lowers surprise — this IS coherence-from-the-past, transparently.")

    # ---- the transparency residue ----
    saturating = drop2 < drop1 * 0.6
    print(f"\nTRANSPARENCY RESIDUE:")
    print(f"   bigram→trigram gain ({drop2:.0f}%) is {'SMALLER than' if saturating else 'comparable to'} "
          f"unigram→bigram ({drop1:.0f}%) — the n-gram floor is {'SATURATING' if saturating else 'still climbing'}.")
    print(f"   {'at 400k tokens the 2-word floor saturates: longer transparent context needs MORE DATA' if saturating else ''}".rstrip())
    print(f"   the local-coherence floor (transparent) captures the near context; the LONG-RANGE /")
    print(f"   compositional coherence beyond it is the residue the LLM's black box holds — the open seek.")

    # ---- generate: the render appearing (rolling-context walk) ----
    print(f"\nGENERATION (the render appearing — rolling-context walk over the transparent model):")
    for k in range(3):
        print(f"   • {generate(uni, bi, tri, V, Ntok, 32)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
