"""F1190 (#243): the reconstruction FILL statistic (vs a frequency prior) + a KNOWLEDGE-KERNEL-seeded variant.

Two questions the F1189 single-line 4/13 anecdote could not answer:

(1) STATISTIC — average the fill recall over many held-out offering lines, against a FREQUENCY-PRIOR baseline (guess the
    commonest offering lemmas, ignoring context). Does the spectral FAMILY (siona.reconstruct) genuinely beat "just guess
    the common offering words"? (The offering frame IS high-frequency vocabulary, so the prior is a HARD baseline here —
    the honest test, F1175's lens-vs-prior on a text where the prior is strong.)

(2) KNOWLEDGE KERNEL (the user's question) — the offering formula is ELLIPTICAL BY CONVENTION: a specific ḥtp-dꞽ-nswt
    line abbreviates the canonical frame because it was IMPLIED (everyone knew pr.t-ḫrw tʾ ḥnq.t kꜣ ꜣpd šs mnḫ.t =
    'invocation-offerings of bread, beer, ox, fowl, alabaster, linen'). So the elided-because-canonical words are exactly
    what a GENRE-TEMPLATE kernel can restore — fired "because of something implied": when the surviving context carries the
    offering TRIGGER (pr.t-ḫrw / ḥtp / nswt), the canonical frame is implied → seed it. The UNIQUE operand (the deceased's
    name/titles) is never implied → it stays with the corpus-parallel (F1188) / the expert (F282).

The knowledge kernel is corpus-ATTESTED, not magic: trigger = the formula's defining marker lemmas; frame = the lemmas
appearing in >= a fraction of trigger-bearing lines (an attested corpus ratio, MPR class-B — a personal name appears once
so it can NEVER enter the frame; the ratio itself separates frame from operand). Uses siona.reconstruct for the family
path; numpy-free; no magnitude-builtin; plain-dict tally (no Counter).
"""
import json, random
from siona import reconstruct as R

SLICE = "/home/skirklan/corpora/egyptian_tla/earlier_slice.jsonl"
STOP = set(("n m r ꞽ ꞽn ꞽs ꞽr ꞽm pw pn tn nn nb pꜣ tꜣ nꜣ ḥr ḥnꜥ ẖr ꞽw wnn jw ky k f s sn ṯn tn ꞽꜣ ꜥ".split()))
TRIGGER = ("pr.t-ḫrw", "ḥtp", "nswt")                 # the ḥtp-dꞽ-nswt formula's defining marker lemmas (attested)
OFFERING = ("pr.t-ḫrw", "ḥtp", "nswt", "kꜣ", "ꜣpd", "tʾ", "ḥnq.t", "šs", "mnḫ.t", "ꞽḫ.t")


def lemma_set(rec):
    out = []
    for tok in rec.get("lemmatization", "").split():
        lem = tok.split("|", 1)[1] if "|" in tok else tok
        if lem.startswith("=") or lem in STOP or len(lem) < 2:
            continue
        out.append(lem)
    return frozenset(out)


def is_offering(lm):
    return sum(1 for w in OFFERING if w in lm) >= 3


def recall(pred, masked):
    return len(set(pred) & masked) / len(masked) if masked else 0.0


def precision(pred, masked):
    return len(set(pred) & masked) / len(pred) if pred else 0.0


if __name__ == "__main__":
    recs = [json.loads(l) for l in open(SLICE, encoding="utf-8")]
    sigs = [lemma_set(r) for r in recs]
    off = [i for i, lm in enumerate(sigs) if is_offering(lm) and len(lm) >= 8]     # >=8 so a half-mask leaves >=4 each side
    pool_sigs = [sigs[i] for i in off]

    # -- frequency prior: corpus-wide offering-lemma frequency (context-FREE guess) --
    df = {}
    for lm in pool_sigs:
        for w in lm:
            df[w] = df.get(w, 0) + 1
    freq_rank = sorted(df, key=lambda w: (-df[w], w))

    # -- the KNOWLEDGE KERNEL: the canonical offering FRAME = lemmas in >= FRAME_FRAC of the offering lines (attested
    #    corpus ratio; a once-only personal name can never clear it, so the ratio itself separates frame from operand) --
    FRAME_FRAC = 0.06
    n_off = len(pool_sigs)
    frame = frozenset(w for w in df if df[w] >= FRAME_FRAC * n_off)
    print("F1190 (#243): fill statistic vs prior + knowledge-kernel seed  (offering lines: %d)\n" % n_off)
    print("   knowledge kernel — canonical offering FRAME (>=%.0f%% of offering lines, corpus-attested), %d lemmas:"
          % (100 * FRAME_FRAC, len(frame)))
    print("      %s\n" % " ".join(sorted(frame, key=lambda w: -df[w])[:24]))

    random.seed(11)
    trials = random.sample(range(n_off), min(80, n_off))
    modes = ["prior", "family", "knowledge", "family+knowledge"]
    # EQUAL-BUDGET recall: every mode ranks its guesses and is capped to exactly |masked| — the fair comparison (no mode
    # can win on recall just by guessing MORE). Also keep the UNCAPPED family recall/precision to show the tradeoff.
    Rbud = {m: 0.0 for m in modes}
    Rraw = {m: 0.0 for m in modes}; Praw = {m: 0.0 for m in modes}
    lift_frame = lift_operand = 0                       # where does knowledge's EXTRA-over-family recall land?
    got = 0
    for t in trials:
        lm = list(pool_sigs[t]); random.shuffle(lm)
        survive = frozenset(lm[: len(lm) // 2]); masked = set(lm[len(lm) // 2:])
        if len(masked) < 3:
            continue
        got += 1
        b = len(masked)                                            # the equal guess budget
        others = [pool_sigs[i] for i in range(n_off) if i != t]    # the offering family (post-grouping fill scenario)

        # ranked prediction lists (best-first) per mode
        rk_prior = [w for w in freq_rank if w not in survive]                       # by corpus frequency
        rk_family = R.reconstruct(survive, others, k=12, frac=0.30)["recovered"]    # by family support (already ranked)
        fired = frozenset(frame) if (set(survive) & set(TRIGGER)) else frozenset()  # fire the frame iff trigger implied
        rk_know = sorted((w for w in fired if w not in survive), key=lambda w: -df[w])
        seen = set(rk_family)
        rk_fk = list(rk_family) + [w for w in rk_know if w not in seen]             # family first, then the elided frame

        ranked = {"prior": rk_prior, "family": rk_family, "knowledge": rk_know, "family+knowledge": rk_fk}
        for m in modes:
            Rbud[m] += recall(ranked[m][:b], masked)               # equal-budget: top-|masked| only
            Rraw[m] += recall(ranked[m], masked); Praw[m] += precision(ranked[m], masked)

        extra = (set(rk_fk) & masked) - (set(rk_family) & masked)  # words knowledge recovered that family missed
        lift_frame += sum(1 for w in extra if w in frame)
        lift_operand += sum(1 for w in extra if w not in frame)

    print("   EQUAL-BUDGET recall (every mode capped to exactly |masked| ranked guesses — the fair headline):")
    for m in modes:
        print("     %-18s   %.3f" % (m, Rbud[m] / got))
    print("\n   uncapped (natural guess-count) recall / precision — shows the recall↔precision tradeoff:")
    for m in ("family", "family+knowledge"):
        print("     %-18s   recall %.3f   precision %.3f" % (m, Rraw[m] / got, Praw[m] / got))
    print("\n   knowledge's EXTRA correct-recoveries over family-alone: %d frame-lemmas, %d operand-lemmas" % (
        lift_frame, lift_operand))
    print("   (prediction: the lift is ~ALL frame — the knowledge kernel restores the elided-because-canonical frame,")
    print("    and NOTHING of the unique operand, because the operand is never implied.)")
    print("\n  READ: (1) equal-budget family vs prior = does the local spectral family beat guessing common offering words")
    print("  at the SAME guess budget; (2) family+knowledge vs family = what the genre-template kernel adds, and the")
    print("  frame/operand split of its lift = WHETHER it adds exactly the implied-canonical frame (the op-side ellipsis gap).")
