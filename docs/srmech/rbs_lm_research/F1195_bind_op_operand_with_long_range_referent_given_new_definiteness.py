"""F1195 (#243): BIND op and operand with the long-range REFERENT — does the operand's prior mention (given/new) unlock
the grammatical residual that local order (F1193) and local content (F1194) could not?

F1194: local content adds +0.001 to the adjacent-order grammatical prediction — op and operand PARTITION cleanly; the
residual ("the vs a") is discourse/referential-bound, above the local window. F1193: the operand is recoverable only from
long-EXACT recurrence (its prior mention). This probe supplies exactly that — the long-range REFERENT — and tests whether
it binds: for a masked determiner slot before a head noun R, the referent signal is GIVEN/NEW = was R mentioned earlier in
the recent discourse? (given → definite "the"; new → indefinite "a/an" — the classic given/new definiteness). This is the
operand's exact-recurrence (F1193/F1177) offered as the k=3 BINDER of op(x)operand (the k=2 partition, F1194).

Two measurements:
  (1) BROAD — all frame slots: BIGRAM (order) vs BIGRAM+REFERENT (order + given/new). Does the referent add lift where
      local content added +0.001?
  (2) TARGETED — determiner slots (true ∈ {the, a, an}), where definiteness lives: the given/new base rates
      P(the|given) / P(a|new), and the accuracy of the pure given→the/new→a REFERENT rule vs the bigram.

Document/discourse ORDER is preserved (NO shuffle; per-novel first-90%/last-10% split), and given/new is computed at
inference from the OBSERVED prior context (a rolling window of recent content tokens) — no leakage from the masked token.
Corpus: 3 novels (#98/#829/#1342). Class-I + referent-conditioned tallies (plain dicts, NOT Counter). numpy-free; no
magnitude-builtin.
"""
import re

PATHS = ["/tmp/gb_98_tale.txt", "/tmp/gb_829_gulliver.txt", "/tmp/gb_1342_pride.txt"]
WINDOW = 80                     # recent-discourse memory (content tokens) — ~a paragraph; the referent's "given" range
DET = ("the", "a", "an")


def doc_sentences(p):
    t = open(p, encoding="utf-8", errors="replace").read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", t); e = re.search(r"\*\*\* END OF", t)
    body = t[s.end():e.start()] if (s and e) else t
    out = []
    for raw in re.split(r"[.!?]", body):
        toks = re.findall(r"[a-z]+", raw.lower())
        if len(toks) >= 8:
            out.append(toks)
    return out


def nearest_right_content(s, i, is_frame):
    j = i + 1
    while j < len(s):
        if not is_frame(s[j]):
            return s[j]
        j += 1
    return None


if __name__ == "__main__":
    docs = [doc_sentences(p) for p in PATHS]
    # df + frame tier from the TRAIN portion (first 90% of each doc, discourse order preserved)
    train_docs = [d[: (len(d) * 9) // 10] for d in docs]
    test_docs = [d[(len(d) * 9) // 10:] for d in docs]
    df = {}
    for d in train_docs:
        for s in d:
            for w in set(s):
                df[w] = df.get(w, 0) + 1
    N = sum(len(d) for d in train_docs)
    thr = 0.01 * N
    frame = frozenset(w for w in df if df[w] >= thr)

    def is_frame(w):
        return w in frame

    def walk(d, on_frame):
        """walk one document in order, maintaining the rolling recent-content window; call on_frame(s,i,given) at every
        interior frame position, then advance the window past each token (so `given` sees only PRIOR context)."""
        recent, rc = [], {}
        for s in d:
            for i in range(len(s)):
                if is_frame(s[i]) and 0 < i < len(s):
                    R = nearest_right_content(s, i, is_frame)
                    given = 1 if (R is not None and rc.get(R, 0) > 0) else 0
                    on_frame(s, i, given, R)
                if not is_frame(s[i]):                    # advance the discourse window (content tokens only)
                    recent.append(s[i]); rc[s[i]] = rc.get(s[i], 0) + 1
                    if len(recent) > WINDOW:
                        old = recent.pop(0); rc[old] -= 1

    bigram, ref = {}, {}                                   # P(frame|prev) ; P(frame|prev,given)
    det_by_given = {0: {}, 1: {}}                          # determiner counts split by given/new

    def train_on(s, i, given, R):
        p = s[i - 1]
        bigram.setdefault(p, {}); bigram[p][s[i]] = bigram[p].get(s[i], 0) + 1
        ref.setdefault((p, given), {}); ref[(p, given)][s[i]] = ref[(p, given)].get(s[i], 0) + 1
        if s[i] in DET:
            det_by_given[given][s[i]] = det_by_given[given].get(s[i], 0) + 1
    for d in train_docs:
        walk(d, train_on)

    def amax(d, fb):
        return max(sorted(d), key=lambda w: d[w]) if d else fb
    bag = max(sorted(df), key=lambda w: df[w])
    best_bi = {p: amax(v, bag) for p, v in bigram.items()}
    best_ref = {k: amax(v, bag) for k, v in ref.items()}

    hit_bi = hit_ref = tot = 0                             # broad: all frame slots
    d_bi = d_rule = d_ref = d_tot = 0                      # targeted: determiner slots

    def test_on(s, i, given, R):
        global hit_bi, hit_ref, tot, d_bi, d_rule, d_ref, d_tot
        true, p = s[i], s[i - 1]
        tot += 1
        if best_bi.get(p, bag) == true:
            hit_bi += 1
        if best_ref.get((p, given), best_bi.get(p, bag)) == true:
            hit_ref += 1
        if true in DET:
            d_tot += 1
            if best_bi.get(p, bag) == true:
                d_bi += 1
            if best_ref.get((p, given), best_bi.get(p, bag)) == true:
                d_ref += 1
            if ("the" if given else "a") == true:          # the pure given→the / new→a referent rule
                d_rule += 1
    for d in test_docs:
        walk(d, test_on)

    def p_the(g):
        d = det_by_given[g]; s = sum(d.values())
        return (d.get("the", 0) / s) if s else 0.0

    def p_a(g):
        d = det_by_given[g]; s = sum(d.values())
        return ((d.get("a", 0) + d.get("an", 0)) / s) if s else 0.0

    print("F1195 (#243): bind op & operand with the long-range REFERENT (given/new)  (3 novels, discourse order)\n")
    print("   (1) BROAD — all frame slots (%d test positions):" % tot)
    print("       BIGRAM (order only)            %.3f" % (hit_bi / max(1, tot)))
    print("       BIGRAM + REFERENT (given/new)  %.3f   (lift %+.3f)" % (
        hit_ref / max(1, tot), (hit_ref - hit_bi) / max(1, tot)))
    print("\n   (2) TARGETED — determiner slots the/a/an (%d test positions), where definiteness lives:" % d_tot)
    print("       given/new base rates (train):  P(the | GIVEN)=%.2f  P(the | NEW)=%.2f   P(a/an | NEW)=%.2f  P(a/an | GIVEN)=%.2f"
          % (p_the(1), p_the(0), p_a(0), p_a(1)))
    print("       BIGRAM (order only)                       %.3f" % (d_bi / max(1, d_tot)))
    print("       REFERENT rule (given→the / new→a)         %.3f" % (d_rule / max(1, d_tot)))
    print("       BIGRAM + REFERENT (order + given/new)     %.3f   (lift over bigram %+.3f)" % (
        d_ref / max(1, d_tot), (d_ref - d_bi) / max(1, d_tot)))
    print("\n  READ: if the referent LIFTS determiner accuracy over the bigram (where local content added +0.001, F1194),")
    print("  the long-range referent (the operand's prior mention = exact recurrence, F1193/F1177) BINDS op(x)operand — the")
    print("  k=3 that resolves the residual the k=2 local partition could not. If P(the|given) >> P(the|new), the given/new")
    print("  signal is real. Residual-of-residual (definite-by-familiarity, not prior-mention) stays → the expert (F282).")
