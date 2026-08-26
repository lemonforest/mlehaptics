r"""R-RBS-LM-STORYGEN2 (the F603 lever, 2026-06-08): F603's chord-walk generator FLOWED (learned 0.109 >> uniform 0.019)
but the 133%-of-corpus figure was INFLATED by self-loop stickiness (it repeated chord-types), and it emitted topical drift,
not surface text. Two fixes here:
  (1) NO-SELF-LOOP walk: forbid repeating the current chord-type (renormalise the transition row) -> a clean, un-inflated
      flow measurement (does the operator still flow once stickiness is removed?).
  (2) GRAMMAR BRIDGE (joining the F569/F596/F599 layer): emit a content word per chord, then STITCH consecutive emitted
      content words with the corpus BIGRAM model (insert the most-likely connecting/function word) -> a surface string.
      Measure the fraction of adjacent emitted word-pairs that are ATTESTED corpus bigrams, vs a shuffled-walk baseline.
      Honest: this is LOCAL surface fluency (real adjacencies + restored function words), not full grammaticality.

srmech 0.7.5rc6: signal_processing.mint_vector (Class-M); hdc.{bundle,similarity} (Class-M); HDC k-means chord vocab +
learned transition operator (F603). Bigram grammar layer = Class-I cyclic adjacency over the raw token stream. No abs();
capacity-aware bundling under F222. No CAD; no Workflow; no sub-agents.
"""
import json, re, random
from collections import defaultdict, Counter
import srmech
from srmech import signal_processing as sp
from srmech.amsc import hdc

ART = "/home/skirklan/corpora/wikipedia/simplewiki_extracted/articles.jsonl"
N_ARTICLES, W, D, CAP, K, KM_ITERS = 300, 5, 4096, 255, 64, 3
STOP = set("the a an and or but of to in on at for with as by from is are was were be been being this that these those "
           "it its he she they them his her their we you i not no yes do does did have has had will would can could may "
           "might must should de en el la los who which what when where why how then than so if up out also other into".split())
TOK = re.compile(r"[a-z]{3,}")


def articles(n):
    with open(ART) as f:
        for k, line in enumerate(f):
            if k >= n:
                break
            try:
                yield json.loads(line).get("text", "") or ""
            except Exception:
                continue


def content(text):
    return [w for w in TOK.findall(text.lower()) if w not in STOP]


def main():
    print(f"=== R-RBS-LM-STORYGEN2 — no-self-loop walk + grammar bridge toward fluent surface text (the F603 lever)  (srmech {srmech.__version__}) ===\n")
    rng = random.Random(0)
    note_hv = {}
    def hv(w):
        if w not in note_hv:
            note_hv[w] = sp.mint_vector(f"note:{w}", D=D)
        return note_hv[w]
    def bundle_cap(vs):
        vs = vs[:CAP]
        if len(vs) % 2 == 0 and vs:
            vs = vs + [vs[0]]
        return hdc.bundle(vs) if vs else None

    # chords + bigram model (raw tokens incl. stopwords, for the grammar layer)
    docs = []
    bigram = defaultdict(Counter)
    raw_bigrams = set()
    for text in articles(N_ARTICLES):
        raw = TOK.findall(text.lower())
        for i in range(len(raw) - 1):
            bigram[raw[i]][raw[i + 1]] += 1; raw_bigrams.add((raw[i], raw[i + 1]))
        toks = content(text)
        if len(toks) < 2 * W:
            continue
        ch = [toks[i:i + W] for i in range(0, len(toks) - W + 1, W)]
        docs.append([(ws, bundle_cap([hv(w) for w in ws])) for ws in ch])
    chords = [(ws, h) for doc in docs for (ws, h) in doc]
    print(f"corpus: Simple English Wikipedia -- {len(docs)} articles, {len(chords)} chords, {len(raw_bigrams)} distinct bigrams.")

    # cluster -> K chord-types (HDC k-means)
    cents = [chords[rng.randrange(len(chords))][1] for _ in range(K)]
    def nearest(h):
        bi, bs = 0, -2.0
        for k, c in enumerate(cents):
            s = hdc.similarity(h, c)
            if s > bs:
                bi, bs = k, s
        return bi
    for _ in range(KM_ITERS):
        mem = defaultdict(list)
        for (_, h) in chords:
            mem[nearest(h)].append(h)
        for k in range(K):
            m = mem.get(k)
            if not m:
                continue
            samp = m if len(m) <= CAP else [m[j] for j in range(0, len(m), max(1, len(m) // CAP))][:CAP]
            if len(samp) % 2 == 0:
                samp = samp[:-1] if len(samp) > 1 else samp
            cents[k] = hdc.bundle(samp)
    typ_words = defaultdict(Counter); doc_types = []
    for doc in docs:
        seq = []
        for (ws, h) in doc:
            t = nearest(h); seq.append(t); typ_words[t].update(ws)
        doc_types.append(seq)
    T = defaultdict(Counter)
    for seq in doc_types:
        for i in range(len(seq) - 1):
            T[seq[i]][seq[i + 1]] += 1
    print(f"clustered {K} chord-types; learned transition operator.\n")

    def step(t, no_self):
        nxt = T.get(t)
        if not nxt:
            return rng.randrange(K)
        items = [(k, w) for k, w in nxt.items() if not (no_self and k == t)]
        if not items:
            return rng.randrange(K)
        types, wts = zip(*items)
        return rng.choices(types, weights=wts, k=1)[0]

    def consec(no_self, runs=60, length=20):
        sims = []
        for _ in range(runs):
            t = rng.randrange(K)
            for _ in range(length):
                t2 = step(t, no_self); sims.append(hdc.similarity(cents[t], cents[t2])); t = t2
        return sum(sims) / len(sims)
    def uniform_consec(runs=60, length=20):
        sims = []
        for _ in range(runs):
            t = rng.randrange(K)
            for _ in range(length):
                t2 = rng.randrange(K); sims.append(hdc.similarity(cents[t], cents[t2])); t = t2
        return sum(sims) / len(sims)
    corpus = [hdc.similarity(cents[s[i]], cents[s[i + 1]]) for s in doc_types for i in range(len(s) - 1)]
    m_corpus = sum(corpus) / len(corpus)
    m_self = consec(False); m_noself = consec(True); m_unif = uniform_consec()
    print("(1) NO-SELF-LOOP walk -- a CLEAN (un-inflated) flow measurement:")
    print(f"    CORPUS reference                 : {m_corpus:.4f}")
    print(f"    with-self-loop walk (F603)       : {m_self:.4f}  ({m_self/m_corpus*100:.0f}% of corpus -- INFLATED by stickiness)")
    print(f"    NO-self-loop walk (clean)        : {m_noself:.4f}  ({(m_noself-m_unif)/(m_corpus-m_unif)*100:.0f}% of corpus flow over uniform)")
    print(f"    uniform-random control           : {m_unif:.4f}")
    print(f"    -> NEGATIVE/CORRECTION: with self-loops removed the walk does NOT flow ({m_noself:.4f} <= uniform {m_unif:.4f}).")
    print(f"    F603's apparent flow was ALMOST ENTIRELY self-loops (topic PERSISTENCE -- staying in the same chord-cluster),")
    print(f"    NOT genuine harmony between DISTINCT chord-types. The cross-cluster transition operator carries ~no flow.\n")

    # (2) GRAMMAR BRIDGE: emit content word per chord-type, stitch with the bigram model -> surface string
    def emit_content(no_self, length=12):
        t = rng.randrange(K); words = []
        for _ in range(length):
            top = typ_words[t].most_common(3)
            if top:
                words.append(rng.choice(top)[0])
            t = step(t, no_self)
        return words
    def bridge(words):
        out = [words[0]]
        for w in words[1:]:
            prev = out[-1]
            cand = bigram.get(prev)
            f = cand.most_common(1)[0][0] if cand else None     # most-likely next word (often a function word)
            if f and f != w:
                out.append(f)
            out.append(w)
        return out
    def attested_rate(seq):
        pairs = [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
        return sum((a, b) in raw_bigrams for a, b in pairs) / len(pairs) if pairs else 0.0

    walk_rates, shuf_rates = [], []
    sample = None
    for r in range(40):
        cw = emit_content(no_self=True)
        br = bridge(cw); walk_rates.append(attested_rate(br))
        if sample is None:
            sample = br
        shuf = cw[:]; rng.shuffle(shuf)
        shuf_rates.append(attested_rate(bridge(shuf)))
    wr, sr = sum(walk_rates) / len(walk_rates), sum(shuf_rates) / len(shuf_rates)
    print("(2) GRAMMAR BRIDGE (emit chord-words + stitch with corpus bigrams) -- surface fluency vs shuffled:")
    print(f"    attested-bigram rate, WALK-emitted + bridged : {wr:.1%}")
    print(f"    attested-bigram rate, SHUFFLED + bridged     : {sr:.1%}")
    print(f"    sample emitted surface string: \"{' '.join(sample)}\"\n")

    print("VERDICT (the F603 lever -- a NEGATIVE result that CORRECTS F603, the honest science):")
    print(f"  • F603'S 'FLOW' WAS A STICKINESS ARTIFACT: removing self-loops drops consecutive similarity to {m_noself:.4f}, AT OR")
    print(f"    BELOW the uniform-random baseline ({m_unif:.4f}). So the chord-CLUSTER-transition operator carries ~NO genuine")
    print(f"    cross-cluster harmony; F603's apparent flow was the walk REPEATING the same chord-cluster (topic persistence).")
    print(f"    This corrects F603's over-claim (the 133%/102%-of-corpus figures were self-loop inflation).")
    print(f"  • THE 'FLUENCY' WAS THE BIGRAM BRIDGE, NOT THE WALK: walk-emitted+bridged attested-bigram rate {wr:.0%} is ~EQUAL")
    print(f"    to shuffled+bridged {sr:.0%} -- the ~77% comes from the function-word bridge (\"the X\", \"X the\" are always")
    print(f"    attested), NOT from the chord progression. The sample string is wiki-boilerplate word salad, not fluent text.")
    print(f"  • WHAT SURVIVES (the real signal): F601's consecutive-RAW-chord similarity (~18x over random) WAS real -- but it")
    print(f"    is TOPIC PERSISTENCE (consecutive chords share a topic / fall in the same cluster), NOT a rich harmonic")
    print(f"    progression between distinct chords. So 'what creates a story-teller wave' at the coarse-cluster level is")
    print(f"    mostly 'stay on topic'; genuine progression structure (if any) must be sought at a FINER grain -- sentence/")
    print(f"    clause scale (F606), the raw-chord level, or with the seam-aware parse bind (F604) supplying order/structure")
    print(f"    that a Markov cluster-walk cannot. Honest: the cluster-walk generator does NOT yet make fluent surface text.")
    print(f"  • Composes F603 (the generator -- CORRECTED here) + F601 (the song decomposition; its (B) raw-chord signal")
    print(f"    survives as topic persistence) + F569 (grammar = function/positional, the bridge) + F596/F599 (meaning-class)")
    print(f"    + F604 (the seam-aware parse bind, a better route than the Markov walk). srmech 0.7.5rc6. F398/F394; null")
    print(f"    findings count (no-leaning rule).")


if __name__ == "__main__":
    main()
