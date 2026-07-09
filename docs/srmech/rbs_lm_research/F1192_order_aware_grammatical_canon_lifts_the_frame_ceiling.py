"""F1192 (#243): does an ORDER-AWARE grammatical canon lift F1191's bag-of-words frame ceiling?

F1191 honest ceiling: a bag-of-words knowledge kernel recovers WHICH grammatical tokens are present (set-recall 0.337)
but not WHICH-goes-WHERE — because "the vs a vs his vs her" in a slot depends on the local order/agreement a bag discards.
This probe tests the next depth: model the SEQUENTIAL grammatical canon (the Class-I transition structure — which token
canonically follows/precedes which) and measure per-POSITION accuracy, isolating the value of ORDER by holding the task
fixed and varying ONLY whether the neighbours are used.

Task (leave-one-position-out): for every interior position i in held-out sentences, predict the true token tok[i] from
its surviving neighbours tok[i-1], tok[i+1]. Three predictors on the SAME task:
  * BAG (F1191, position-BLIND)  — the marginal mode (the single commonest token); no neighbours used
  * ORDER-left (Class-I bigram)  — argmax of the left-transition canon tok[i-1] → ?
  * ORDER-both (Class-I trigram-ish) — the token that canonically FOLLOWS tok[i-1] AND PRECEDES tok[i+1]
Tier-split (frame = grammatical/high-freq canon vs operand = rare content): if ORDER lifts the FRAME accuracy far above
BAG while the OPERAND stays ~0, then order recovers the grammatical STRUCTURE (the responsion's ordered reinforcement,
F1186), not just the F1191 vocabulary — and the operand is still unrecoverable even with order.

Train/test split so the transition canon never sees the test sentences (no leakage). Corpus: A Tale of Two Cities
(Gutenberg #98). The transition table is the Class-I SEQUENTIAL model (a plain-dict tally — deliberately NOT a Counter,
and NOT a spectral-storage proxy: it is the actual bigram grammar, the order the F1191 bag threw away). numpy-free; no
magnitude-builtin.
"""
import re, random

PATH = "/tmp/gb_98_tale.txt"


def sentences_ordered():
    t = open(PATH, encoding="utf-8", errors="replace").read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", t); e = re.search(r"\*\*\* END OF", t)
    body = t[s.end():e.start()] if (s and e) else t
    out = []
    for raw in re.split(r"[.!?]", body):
        toks = re.findall(r"[a-z]+", raw.lower())              # ordered token list, ALL words kept (function words = the canon)
        if len(toks) >= 8:
            out.append(toks)
    return out


def argmax_dict(d, fallback):
    """the mode of a plain-dict tally (deterministic tie-break; never a magnitude/abs builtin, never Counter)."""
    if not d:
        return fallback
    return max(sorted(d), key=lambda w: d[w])


if __name__ == "__main__":
    sents = sentences_ordered()
    random.seed(17)
    random.shuffle(sents)
    cut = (len(sents) * 9) // 10
    train, test = sents[:cut], sents[cut:]

    # --- the Class-I sequential canon: forward + backward adjacent-transition tallies (plain dicts) ---
    nxt, prv, df = {}, {}, {}
    for s in train:
        for w in set(s):
            df[w] = df.get(w, 0) + 1
        for a, b in zip(s, s[1:]):
            nxt.setdefault(a, {}); nxt[a][b] = nxt[a].get(b, 0) + 1     # a -> b  (left neighbour predicts)
            prv.setdefault(b, {}); prv[b][a] = prv[b].get(a, 0) + 1     # a -> b  (right neighbour predicts, indexed by b)
    N = len(train)
    FRAME_FRAC = 0.01
    thr = FRAME_FRAC * N
    mode = argmax_dict({w: df[w] for w in df}, "the")             # the global marginal mode = the position-BLIND bag guess

    def order_left(prev):
        return argmax_dict(nxt.get(prev, {}), mode)

    def order_both(prev, nx):
        cand = {}
        for b, c in nxt.get(prev, {}).items():
            r = prv.get(nx, {}).get(b, 0)
            if r > 0:
                cand[b] = c * r                                  # canonically follows prev AND precedes nx
        return argmax_dict(cand, order_left(prev))

    # --- evaluate per interior position, tier-split ---
    tiers = ("frame", "operand")
    hit = {p: {tt: 0 for tt in tiers} for p in ("bag", "left", "both")}
    tot = {tt: 0 for tt in tiers}
    for s in test:
        for i in range(1, len(s) - 1):
            true, prev, nx = s[i], s[i - 1], s[i + 1]
            tt = "frame" if df.get(true, 0) >= thr else "operand"
            tot[tt] += 1
            if mode == true:
                hit["bag"][tt] += 1
            if order_left(prev) == true:
                hit["left"][tt] += 1
            if order_both(prev, nx) == true:
                hit["both"][tt] += 1

    print("F1192 (#243): order-aware grammatical canon vs the F1191 bag ceiling — A Tale of Two Cities\n")
    print("   train %d / test %d sentences; per-position leave-one-out; global mode (bag guess) = %r\n" % (
        len(train), len(test), mode))
    print("   per-POSITION top-1 accuracy — does ORDER (using neighbours) beat position-BLIND BAG?")
    print("     predictor                         FRAME (grammatical)   OPERAND (rare content)")
    for p, lab in (("bag", "BAG (marginal, no order)"), ("left", "ORDER-left  (bigram)"), ("both", "ORDER-both  (both neighbours)")):
        print("     %-32s  %.3f                 %.3f" % (
            lab, hit[p]["frame"] / max(1, tot["frame"]), hit[p]["operand"] / max(1, tot["operand"])))
    print("\n   frame positions: %d   operand positions: %d" % (tot["frame"], tot["operand"]))
    print("\n  READ: if ORDER-both >> BAG on the FRAME tier, modelling the sequence recovers the grammatical STRUCTURE")
    print("  (which token goes WHERE), lifting F1191's vocabulary-only ceiling — the responsion is the ORDERED reinforcement")
    print("  (F1186), not a bag. If the OPERAND tier stays ~0 even with order, the unique content is unrecoverable at the")
    print("  order level too (F1175 op/operand boundary holds): order restores the grammatical canon, never the operand.")
