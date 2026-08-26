"""F1193 (#243): widen the order window (bigram → trigram → 4-gram) — does grammatical-placement accuracy keep climbing,
or saturate? And if it saturates, is it because ORDER stops mattering or because we run out of DATA?

F1192: one left neighbour (bigram) lifted grammatical-position accuracy 2.1× over the position-blind bag; both neighbours
2.8×. This widens the LEFT context (the classic n-gram ladder: context length L = 0 bag / 1 bigram / 2 trigram / 3 4-gram)
and decomposes the saturation honestly into THREE numbers per order:
  * REALISTIC accuracy (stupid-backoff: use the longest seen context, else back off) — what you actually get
  * COVERAGE — the fraction of positions whose full L-context was SEEN in train (the data-sparsity gate)
  * WHEN-SEEN accuracy — accuracy ONLY on positions where the full L-context was seen — does more order keep helping
    WHEN the data is present? (isolates "order stops mattering" from "we ran out of data")
If WHEN-SEEN keeps climbing while REALISTIC saturates, the ceiling is DATA (a bigger corpus extends it), not order — the
ordered reinforcement (F1186/F1179) keeps paying, we just stop having the n-gram evidence. Tier-split (frame vs operand):
the operand stays unrecoverable at every order (F1175).

Corpus: 3 Gutenberg novels (Tale of Two Cities #98 + Gulliver #829 + Pride and Prejudice #1342) — grammatical canon is
author-invariant, so pooling gives the higher n-grams fair data. The n-gram tables are the Class-I SEQUENTIAL model
(plain-dict tallies, NOT Counter, NOT a spectral proxy — the actual n-gram grammar). numpy-free; no magnitude-builtin.
"""
import re, random

PATHS = ["/tmp/gb_98_tale.txt", "/tmp/gb_829_gulliver.txt", "/tmp/gb_1342_pride.txt"]


def sentences():
    out = []
    for p in PATHS:
        t = open(p, encoding="utf-8", errors="replace").read()
        s = re.search(r"\*\*\* START OF.*?\*\*\*", t); e = re.search(r"\*\*\* END OF", t)
        body = t[s.end():e.start()] if (s and e) else t
        for raw in re.split(r"[.!?]", body):
            toks = re.findall(r"[a-z]+", raw.lower())
            if len(toks) >= 8:
                out.append(toks)
    return out


def argmax_dict(d):
    return max(sorted(d), key=lambda w: d[w]) if d else None


if __name__ == "__main__":
    sents = sentences()
    random.seed(19)
    random.shuffle(sents)
    cut = (len(sents) * 9) // 10
    train, test = sents[:cut], sents[cut:]

    MAXL = 3                                            # context lengths 0(bag)..3(4-gram)
    models = {L: {} for L in range(MAXL + 1)}          # models[L][ctx-tuple] -> {next: count}; models[0][()] = marginal
    df = {}
    for s in train:
        for w in set(s):
            df[w] = df.get(w, 0) + 1
        for i in range(len(s)):
            for L in range(MAXL + 1):
                if i - L < 0:
                    continue
                ctx = tuple(s[i - L:i])
                models[L].setdefault(ctx, {})
                models[L][ctx][s[i]] = models[L][ctx].get(s[i], 0) + 1
    N = len(train)
    thr = 0.01 * N

    # precompute each context's argmax ONCE (not re-sorted per prediction — the L=0 marginal is the whole vocab)
    best = {L: {ctx: argmax_dict(d) for ctx, d in models[L].items()} for L in range(MAXL + 1)}

    def predict_backoff(s, i, L):
        for k in range(L, -1, -1):                      # longest seen context, else back off
            ctx = tuple(s[i - k:i]) if k else ()
            if i - k >= 0 and ctx in best[k]:
                return best[k][ctx]
        return best[0][()]

    tiers = ("frame", "operand")
    # per L: realistic hits, when-seen hits, when-seen count, total
    real = {L: {tt: 0 for tt in tiers} for L in range(MAXL + 1)}
    seen_hit = {L: {tt: 0 for tt in tiers} for L in range(MAXL + 1)}
    seen_tot = {L: {tt: 0 for tt in tiers} for L in range(MAXL + 1)}
    tot = {tt: 0 for tt in tiers}
    for s in test:
        for i in range(1, len(s) - 1):
            true = s[i]
            tt = "frame" if df.get(true, 0) >= thr else "operand"
            tot[tt] += 1
            for L in range(MAXL + 1):
                if predict_backoff(s, i, L) == true:
                    real[L][tt] += 1
                ctx = tuple(s[i - L:i]) if L else ()    # was the FULL L-context seen in train?
                if i - L >= 0 and ctx in best[L]:
                    seen_tot[L][tt] += 1
                    if best[L][ctx] == true:
                        seen_hit[L][tt] += 1

    labels = {0: "bag (L=0)", 1: "bigram (L=1)", 2: "trigram (L=2)", 3: "4-gram (L=3)"}
    print("F1193 (#243): widen the order window — bigram → trigram → 4-gram  (3 novels; train %d / test %d sentences)\n"
          % (len(train), len(test)))
    print("   FRAME (grammatical) tier — %d positions:" % tot["frame"])
    print("     order          realistic(backoff)   coverage(ctx seen)   accuracy WHEN-SEEN")
    for L in range(MAXL + 1):
        cov = seen_tot[L]["frame"] / max(1, tot["frame"])
        ws = seen_hit[L]["frame"] / max(1, seen_tot[L]["frame"])
        print("     %-13s  %.3f                %.3f                %.3f" % (
            labels[L], real[L]["frame"] / max(1, tot["frame"]), cov, ws))
    print("\n   OPERAND (rare content) tier — %d positions:" % tot["operand"])
    print("     order          realistic(backoff)   accuracy WHEN-SEEN")
    for L in range(MAXL + 1):
        ws = seen_hit[L]["operand"] / max(1, seen_tot[L]["operand"])
        print("     %-13s  %.3f                %.3f" % (labels[L], real[L]["operand"] / max(1, tot["operand"]), ws))
    print("\n  READ: REALISTIC = what you get (climbs then saturates as high n-grams go unseen). COVERAGE = how often the")
    print("  full L-context was in train (falls fast — the sparsity gate). WHEN-SEEN = accuracy where the context IS")
    print("  present: if WHEN-SEEN keeps climbing while REALISTIC saturates, the ceiling is DATA (bigger corpus extends it),")
    print("  NOT order — the ordered reinforcement (F1186/F1179) keeps paying, we just run out of n-gram evidence. Operand")
    print("  stays low at every order (F1175): more grammatical order never recovers the unique content.")
