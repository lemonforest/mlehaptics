r"""R-RBS-LM-CLAUSELEN (item 3, 2026-06-08): F601 measured the story-teller-wave phrase coherence at the ARTICLE scale
(chords ignored sentence boundaries -> coherence decayed slowly, >8 chords = article-TOPIC coherence). Here: bound chords
WITHIN sentences and ask whether there is a CLAUSE/SENTENCE-scale coherence unit distinct from the article topic.

The test (raw chords -- the F601 (B) signal that survived F605, NOT the coarse clusters):
  • WITHIN-sentence consecutive chord similarity (adjacent chords in the SAME sentence).
  • ACROSS-sentence-boundary similarity (last chord of sentence i vs first chord of sentence i+1, same article).
  • RANDOM-pair baseline.
  • within-sentence sim-vs-lag decay -> the clause-scale phrase length.

If WITHIN-sentence > ACROSS-boundary > RANDOM, the sentence is a real PHRASE UNIT (a clause-scale coherence structure
exists, distinct from article topic). If WITHIN approx ACROSS, it is all topic (no special sentence-scale structure) --
honest either way (composes F605's finding that the coarse-cluster 'flow' is mostly topic persistence).

Corpus: Simple English Wikipedia (CC BY-SA), cached OUTSIDE the repo; attested not committed. srmech 0.7.5rc6:
signal_processing.mint_vector (Class-M); hdc.{bundle,similarity} (Class-M chord = bundle). No abs(); capacity-aware
bundling. No CAD; no Workflow; no sub-agents.
"""
import json, re, random
from collections import defaultdict
import srmech
from srmech import signal_processing as sp
from srmech.amsc import hdc

ART = "/home/skirklan/corpora/wikipedia/simplewiki_extracted/articles.jsonl"
N_ARTICLES, W, D, CAP = 1500, 3, 4096, 255
STOP = set("the a an and or but of to in on at for with as by from is are was were be been being this that these those "
           "it its he she they them his her their we you i not no yes do does did have has had will would can could may "
           "might must should de en el la los who which what when where why how then than so if up out also other into".split())
TOK = re.compile(r"[a-z]{3,}")
SENT = re.compile(r"[.!?]+")


def articles(n):
    with open(ART) as f:
        for k, line in enumerate(f):
            if k >= n:
                break
            try:
                yield json.loads(line).get("text", "") or ""
            except Exception:
                continue


def main():
    print(f"=== R-RBS-LM-CLAUSELEN — clause-scale phrase length (sentence-bounded chords) vs article-topic scale  (srmech {srmech.__version__}) ===\n")
    rng = random.Random(0)
    note_hv = {}
    def hv(w):
        if w not in note_hv:
            note_hv[w] = sp.mint_vector(f"note:{w}", D=D)
        return note_hv[w]
    def chord(ws):
        vs = [hv(w) for w in ws][:CAP]
        if len(vs) % 2 == 0 and vs:
            vs = vs + [vs[0]]
        return hdc.bundle(vs) if vs else None

    # per article: list of sentences; per sentence: list of chords (W content words, non-overlapping, WITHIN the sentence)
    articles_chords = []                       # [[ [chord,...] per sentence ] per article]
    for text in articles(N_ARTICLES):
        sents = []
        for s in SENT.split(text):
            toks = [w for w in TOK.findall(s.lower()) if w not in STOP]
            ch = [chord(toks[i:i + W]) for i in range(0, len(toks) - W + 1, W)]
            ch = [c for c in ch if c is not None]
            if ch:
                sents.append(ch)
        if len(sents) >= 2:
            articles_chords.append(sents)
    n_sent = sum(len(a) for a in articles_chords)
    n_chord = sum(len(s) for a in articles_chords for s in a)
    print(f"corpus: Simple English Wikipedia -- {len(articles_chords)} articles, {n_sent} sentences, {n_chord} chords (W={W}).")

    # within-sentence consecutive
    within = [hdc.similarity(s[i], s[i + 1]) for a in articles_chords for s in a for i in range(len(s) - 1)]
    # across-sentence-boundary (last chord of sent i vs first chord of sent i+1, same article)
    across = [hdc.similarity(a[i][-1], a[i + 1][0]) for a in articles_chords for i in range(len(a) - 1)]
    # random baseline
    allc = [c for a in articles_chords for s in a for c in s]
    rnd = [hdc.similarity(allc[rng.randrange(len(allc))], allc[rng.randrange(len(allc))]) for _ in range(20000)]
    mw, ma, mr = sum(within) / len(within), sum(across) / len(across), sum(rnd) / len(rnd)
    print(f"\n(1) clause-scale coherence (raw chords, W={W}):")
    print(f"    WITHIN-sentence consecutive : {mw:.4f}  (lift over random {mw - mr:+.4f})")
    print(f"    ACROSS sentence boundary    : {ma:.4f}  (lift over random {ma - mr:+.4f})")
    print(f"    RANDOM pair (baseline)      : {mr:.4f}")
    drop = (mw - ma) / (mw - mr) if mw != mr else 0.0
    print(f"    -> within > across: {mw > ma}; boundary drop = {drop:.0%} of the within-lift  (is the sentence a phrase unit?)\n")

    # within-sentence sim vs lag -> clause-scale phrase length
    print("(2) WITHIN-sentence sim vs lag (the clause-scale phrase length):")
    for L in (1, 2, 3, 4):
        sims = [hdc.similarity(s[i], s[i + L]) for a in articles_chords for s in a for i in range(len(s) - L)]
        if not sims:
            print(f"    lag {L}: (no chord-pairs at this lag within a sentence)")
            continue
        m = sum(sims) / len(sims)
        print(f"    lag {L}: sim {m:.4f}  (lift over random {m - mr:+.4f})   [{len(sims)} pairs]")
    print()

    print("VERDICT (is there a clause/sentence-scale phrase unit, distinct from article topic?):")
    if mw > ma > mr and drop > 0.15:
        print(f"  • YES -- THE SENTENCE IS A PHRASE UNIT: within-sentence consecutive chords cohere MORE ({mw:.4f}) than chords")
        print(f"    spanning a sentence boundary ({ma:.4f}), both above random ({mr:.4f}); the {drop:.0%} drop at the boundary marks")
        print(f"    a clause-scale coherence unit DISTINCT from the slow article-topic decay F601 measured. The story-teller")
        print(f"    wave has structure at TWO scales: the clause (sentence, sharp) and the topic (article, slow).")
    elif mw > mr and ma > mr and drop <= 0.15:
        print(f"  • MOSTLY TOPIC: within ({mw:.4f}) and across-boundary ({ma:.4f}) coherence are CLOSE (boundary drop only {drop:.0%}),")
        print(f"    both above random ({mr:.4f}) -- so most of the coherence is article-TOPIC (composes F605: the coarse 'flow'")
        print(f"    is topic persistence), with only a weak distinct clause-scale unit. The sentence boundary is a SOFT seam.")
    else:
        print(f"  • WEAK/NULL clause-scale signal: within {mw:.4f}, across {ma:.4f}, random {mr:.4f} -- no strong sentence-scale unit")
        print(f"    at this grain; the wave's coherence is dominated by topic, not clause structure (honest null).")
    print(f"  • EITHER WAY (honest): this sharpens F601's 'length' -- the article-scale >8-chord coherence was TOPIC; the")
    print(f"    clause-scale measurement isolates whether the SENTENCE is a separate, sharper phrase unit. The boundary drop")
    print(f"    of {drop:.0%} is the number. (W={W} raw chords -- the F601(B)/F605 signal that survives, not the coarse clusters.)")
    print(f"  • Composes F601 (the song decomposition; article-scale length) + F605 (coarse 'flow' = topic persistence) +")
    print(f"    F569 (clause/grammar structure) + F596/F599 (the streams). srmech 0.7.5rc6. Favored not privileged (F398);")
    print(f"    held open (F394); null findings count.")


if __name__ == "__main__":
    main()
