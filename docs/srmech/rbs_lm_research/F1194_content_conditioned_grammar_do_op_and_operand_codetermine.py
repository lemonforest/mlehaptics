"""F1194 (#243): content-conditioned grammar — is the grammatical residual unlockable by the OPERAND? Do op and operand
CO-DETERMINE, or partition cleanly?

F1193: predicting a masked grammatical (frame) token from its ADJACENT tokens saturates at the bigram (~0.20) — the
residual ("the vs a vs his all fit the slot") is local ambiguity that more ORDER does not resolve, because (hypothesis)
resolving it needs the CONTENT, not more adjacent function words. This probe conditions the frame prediction on the nearby
CONTENT tokens instead: predict the masked frame token from the nearest content word to the LEFT and the head-noun-like
content word to the RIGHT (skipping the function chaff). The decisive comparison, on the SAME masked-frame task:

  * BIGRAM (adjacent)      — argmax P(frame | tok[i-1])                       (F1193's ~0.20 order predictor)
  * CONTENT-right          — argmax P(frame | nearest right content word)     (the head noun: "___ hand" → his/the)
  * CONTENT-both           — argmax P(frame | left content) · P(frame | right content)
  * COMBINED (order+content) — argmax P(frame | tok[i-1]) · P(frame | left content) · P(frame | right content)

If COMBINED >> BIGRAM, the content CO-DETERMINES the frame — op and operand are not a clean partition, they co-determine
(the grammatical residual is unlockable by the operand). If COMBINED ≈ BIGRAM, the frame slot is grammatically
self-contained and the residual is DISCOURSE/operand-bound beyond the local content (routes to the expert, F282).
Conditionals (not raw counts) so a ubiquitous "the" does not dominate by frequency. Corpus: 3 pooled novels (#98/#829/
#1342). Class-I sequential + content-association tallies (plain dicts, NOT Counter). numpy-free; no magnitude-builtin.
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


def nearest_content(s, i, step, is_frame):
    """the nearest CONTENT token from position i walking by `step` (−1 left / +1 right), skipping frame/function words."""
    j = i + step
    while 0 <= j < len(s):
        if not is_frame(s[j]):
            return s[j]
        j += step
    return None


if __name__ == "__main__":
    sents = sentences()
    random.seed(23)
    random.shuffle(sents)
    cut = (len(sents) * 9) // 10
    train, test = sents[:cut], sents[cut:]

    df = {}
    for s in train:
        for w in set(s):
            df[w] = df.get(w, 0) + 1
    N = len(train)
    thr = 0.01 * N
    frame = frozenset(w for w in df if df[w] >= thr)

    def is_frame(w):
        return w in frame

    adj, cl, cr = {}, {}, {}                                # P(frame|prev) / P(frame|left-content) / P(frame|right-content)
    for s in train:
        for i in range(len(s)):
            if not is_frame(s[i]):
                continue
            if i > 0:
                adj.setdefault(s[i - 1], {}); adj[s[i - 1]][s[i]] = adj[s[i - 1]].get(s[i], 0) + 1
            L = nearest_content(s, i, -1, is_frame)
            R = nearest_content(s, i, +1, is_frame)
            if L is not None:
                cl.setdefault(L, {}); cl[L][s[i]] = cl[L].get(s[i], 0) + 1
            if R is not None:
                cr.setdefault(R, {}); cr[R][s[i]] = cr[R].get(s[i], 0) + 1

    def total(d):
        return sum(d.values())
    adjT = {k: total(v) for k, v in adj.items()}
    clT = {k: total(v) for k, v in cl.items()}
    crT = {k: total(v) for k, v in cr.items()}
    bag_mode = max(sorted(df), key=lambda w: df[w])

    def cond(tbl, tblT, key, t):
        d = tbl.get(key)
        return (d.get(t, 0) / tblT[key]) if d else 0.0

    def pick(cands, scorer, fallback):
        best, bs = fallback, -1.0
        for t in cands:
            sc = scorer(t)
            if sc > bs:
                bs, best = sc, t
        return best

    hit = {m: 0 for m in ("bag", "bigram", "content_right", "content_both", "combined")}
    tot = 0
    cov_r = 0
    for s in test:
        for i in range(len(s)):
            if not is_frame(s[i]) or i == 0 or i == len(s) - 1:
                continue
            true, prev = s[i], s[i - 1]
            L = nearest_content(s, i, -1, is_frame)
            R = nearest_content(s, i, +1, is_frame)
            tot += 1
            if R in cr:
                cov_r += 1
            cands = set(adj.get(prev, {})) | set(cl.get(L, {})) | set(cr.get(R, {}))
            if not cands:
                cands = {bag_mode}
            if bag_mode == true:
                hit["bag"] += 1
            if pick(cands, lambda t: cond(adj, adjT, prev, t), bag_mode) == true:
                hit["bigram"] += 1
            if pick(cands, lambda t: cond(cr, crT, R, t), bag_mode) == true:
                hit["content_right"] += 1
            if pick(cands, lambda t: cond(cl, clT, L, t) * cond(cr, crT, R, t), bag_mode) == true:
                hit["content_both"] += 1
            if pick(cands, lambda t: (cond(adj, adjT, prev, t) + 1e-9) * (cond(cl, clT, L, t) + 1e-3)
                    * (cond(cr, crT, R, t) + 1e-3), bag_mode) == true:
                hit["combined"] += 1

    print("F1194 (#243): content-conditioned grammar — do op & operand CO-DETERMINE?  (3 novels; train %d / test %d)\n"
          % (len(train), len(test)))
    print("   masked FRAME (grammatical) positions: %d   (right-content context seen in train: %.0f%%)\n"
          % (tot, 100 * cov_r / max(1, tot)))
    print("   predictor                              frame-position accuracy")
    for m, lab in (("bag", "BAG (marginal, no context)"), ("bigram", "BIGRAM (adjacent order, F1193)"),
                   ("content_right", "CONTENT-right (head noun)"), ("content_both", "CONTENT-both (L+R content)"),
                   ("combined", "COMBINED (order × content)")):
        print("     %-36s   %.3f" % (lab, hit[m] / max(1, tot)))
    print("\n   the decisive lift: COMBINED − BIGRAM = %+.3f" % ((hit["combined"] - hit["bigram"]) / max(1, tot)))
    print("\n  READ: if COMBINED >> BIGRAM, the nearby CONTENT co-determines the grammatical slot — op and operand are NOT a")
    print("  clean partition, they CO-DETERMINE (the F1193 residual is unlockable by the operand). If COMBINED ≈ BIGRAM, the")
    print("  frame slot is grammatically self-contained and its residual is DISCOURSE/operand-bound beyond local content")
    print("  (needs the wider story → the expert, F282) — op and operand partition, each carrying what the other cannot.")
