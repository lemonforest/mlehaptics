r"""R-RBS-LM-CLUSTERDET (item (a), the F599 lever, 2026-06-08): F599 gave English a soft-determinative = the single
highest-IDF context word, bound as sigma_B; it lifted pseudoword WSD +9.8% but BACKED OFF to the prior on 80% of test
cells (a single rare word is sparse -> rarely seen again). The lever (F599 NEXT): replace it with a CLUSTERED context-
class -- an unsupervised Class-M centroid (a coarser, DENSER soft-determinative) -- and re-measure. A denser class should
cut the backoff; whether it RAISES the lift is the honest question (a coarser class is less discriminative per cell).

Same task as F599 (pseudoword disambiguation, Schutze/Yarowsky -- label-free, ground truth = the known original word),
same corpus, same held-out train/test discipline. ONLY the soft-determinative changes:
  • F599 sigma_B = the single highest-IDF context word (sparse, discriminative).
  • F602 sigma_B = the CLUSTER of the context (HDC k-means: ctx = bundle of window content-words; class = nearest of K
    learned centroids). Dense (only K classes), label-free, unsupervised.

COUPLED key = hdc.bind(form_HV, class_anchor_HV[k]) -- the E×B coupling with the clustered class as sigma_B.

srmech 0.7.5rc6: signal_processing.mint_vector (Class-M); hdc.{bind,bundle,similarity} (Class-M; bundle = the context
superposition + the centroid update). No abs(); capacity-aware bundling under the F222 257-ceiling. No CAD/Workflow/sub-agents.
"""
import json, math, re, random
from collections import defaultdict, Counter
import srmech
from srmech import signal_processing as sp
from srmech.amsc import hdc

ART = "/home/skirklan/corpora/wikipedia/simplewiki_extracted/articles.jsonl"
N_ARTICLES, WINDOW, MAX_OCC, K_PAIRS, D, CAP = 20000, 8, 300, 40, 4096, 255
K_CLASSES, KM_ITERS = 64, 3
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
    print(f"=== R-RBS-LM-CLUSTERDET — clustered context-class soft-determinative (E×B): does a DENSER learned class cut backoff?  (srmech {srmech.__version__}) ===\n")
    rng = random.Random(0)

    tf = Counter()
    for text in articles(N_ARTICLES):
        tf.update(content(text))
    common = [w for w, _ in tf.most_common(4000) if 8 <= len(w) <= 12][:2 * K_PAIRS]
    pairs = [(common[2 * i], common[2 * i + 1]) for i in range(min(K_PAIRS, len(common) // 2))]
    targets = {w: (a, b) for (a, b) in pairs for w in (a, b)}
    form_of = {w: f"{a}|{b}" for (a, b) in pairs for w in (a, b)}
    print(f"corpus: Simple English Wikipedia; {len(pairs)} pseudoword pairs.")

    # collect occurrences with the FULL context window (for clustering), the original word, the form
    note_hv = {}
    def hv(w):
        if w not in note_hv:
            note_hv[w] = sp.mint_vector(f"note:{w}", D=D)
        return note_hv[w]
    def ctx_bundle(ws):
        vs = [hv(w) for w in ws][:CAP]
        if not vs:
            return None
        if len(vs) % 2 == 0:
            vs.append(hv(ws[0]))
        return hdc.bundle(vs)

    occ = []                                                 # (form, original, ctx_hv)
    per = Counter()
    for text in articles(N_ARTICLES):
        toks = content(text)
        for i, w in enumerate(toks):
            if w in targets and per[w] < MAX_OCC:
                lo, hi = max(0, i - WINDOW), min(len(toks), i + WINDOW + 1)
                ctx = [c for c in (toks[lo:i] + toks[i + 1:hi]) if c != w]
                cb = ctx_bundle(ctx)
                if cb is None:
                    continue
                occ.append((form_of[w], w, cb)); per[w] += 1
    print(f"collected {len(occ)} occurrences (window +/-{WINDOW}); HDC k-means: K={K_CLASSES}, {KM_ITERS} iters.\n")

    # unsupervised HDC k-means over context bundles -> K centroids (label-free)
    cents = [occ[rng.randrange(len(occ))][2] for _ in range(K_CLASSES)]
    def nearest(cb):
        bi, bs = 0, -2.0
        for k, c in enumerate(cents):
            s = hdc.similarity(cb, c)
            if s > bs:
                bi, bs = k, s
        return bi
    for _ in range(KM_ITERS):
        members = defaultdict(list)
        for (_, _, cb) in occ:
            members[nearest(cb)].append(cb)
        for k in range(K_CLASSES):
            m = members.get(k, [])
            if not m:
                continue
            sample = m if len(m) <= CAP else [m[j] for j in range(0, len(m), max(1, len(m) // CAP))][:CAP]
            if len(sample) % 2 == 0:
                sample = sample[:-1] if len(sample) > 1 else sample + [sample[0]]
            cents[k] = hdc.bundle(sample)
    # assign final class index to each occurrence
    assigned = [(f, w, nearest(cb)) for (f, w, cb) in occ]

    # class symbol HV (a clean minted anchor per cluster id) = the soft-determinative for the E×B bind
    class_hv = {k: sp.mint_vector(f"ctxclass:{k}", D=D) for k in range(K_CLASSES)}
    orig_hv = {w: sp.mint_vector(f"orig:{w}", D=D) for w in targets}
    TIE = sp.mint_vector("tiebreak:neutral", D=D)
    def freq_bundle(words):
        c = Counter(words); total = sum(c.values())
        scaled = {w: max(1, round(n / total * CAP)) for w, n in c.items()} if total > CAP else dict(c)
        vs = []
        for w, n in scaled.items():
            vs += [orig_hv[w]] * n
        vs = vs[:CAP]
        if len(vs) % 2 == 0:
            vs.append(TIE)
        return hdc.bundle(vs)

    train = [o for i, o in enumerate(assigned) if i % 2 == 0]
    test = [o for i, o in enumerate(assigned) if i % 2 == 1]
    single_pool = defaultdict(list); coupled_pool = defaultdict(list)
    for (f, w, k) in train:
        single_pool[f].append(w); coupled_pool[(f, k)].append(w)
    single_mem = {f: freq_bundle(v) for f, v in single_pool.items()}
    coupled_mem = {key: freq_bundle(v) for key, v in coupled_pool.items()}

    def pick(mem, a, b):
        return a if hdc.similarity(mem, orig_hv[a]) >= hdc.similarity(mem, orig_hv[b]) else b

    s_ok = c_ok = backoff = 0
    for (f, w_true, k) in test:
        a, b = f.split("|")
        s_pred = pick(single_mem[f], a, b) if f in single_mem else a
        if (f, k) in coupled_mem:
            c_pred = pick(coupled_mem[(f, k)], a, b)
        else:
            c_pred = s_pred; backoff += 1
        s_ok += (s_pred == w_true); c_ok += (c_pred == w_true)
    n = len(test)
    s_acc, c_acc = s_ok / n, c_ok / n
    print("(1) PSEUDOWORD WSD ACCURACY with a CLUSTERED context-class soft-determinative (held-out test):")
    print(f"    SINGLE-stream (form only)                          : {s_acc:.1%}  ({s_ok}/{n})")
    print(f"    COUPLED (E×B: bind(form, clustered context-class)) : {c_acc:.1%}  ({c_ok}/{n})")
    print(f"    GAIN                                               : {c_acc - s_acc:+.1%}")
    print(f"    backoff to prior (unseen (form,class)): {backoff}/{n} = {backoff/n:.0%}\n")

    print("(2) COMPARISON to F599 (single highest-IDF word as the soft-determinative):")
    print(f"    F599 (single-IDF-word class) : gain +9.8%, backoff 80%")
    print(f"    F602 (clustered K={K_CLASSES} class) : gain {c_acc - s_acc:+.1%}, backoff {backoff/n:.0%}")
    print(f"    -> a DENSER class ({'cut' if backoff/n < 0.80 else 'did NOT cut'} the backoff); lift {'rose' if (c_acc-s_acc) > 0.098 else 'did NOT rise above F599'}.\n")

    verdict = "YES" if (c_acc - s_acc) > 0.02 else ("NO (within noise)" if abs(c_acc - s_acc) <= 0.02 else "WORSE")
    print("VERDICT (does a clustered/denser learned soft-determinative help, and cut the backoff?):")
    print(f"  • {verdict}: the clustered context-class (an unsupervised Class-M centroid, K={K_CLASSES}) bound as sigma_B lifts")
    print(f"    English pseudoword WSD by {c_acc - s_acc:+.1%} (vs F599's +9.8% with a single-IDF-word class), with backoff")
    print(f"    {backoff/n:.0%} (vs F599's 80%). The denser class {'reduces' if backoff/n < 0.80 else 'does not reduce'} the unseen-cell backoff; the lift")
    print(f"    trade-off (denser = more cells seen, but each class is coarser/less discriminative) is measured, not assumed.")
    print(f"  • READING: the E×B coupling (F593/F596) keeps working in English with a LEARNED class; the class-granularity")
    print(f"    (single-rare-word vs clustered-centroid) is the lever between coverage (low backoff) and sharpness (per-cell")
    print(f"    discriminativeness). English makes you tune that trade-off; Egyptian gave it for free (the determinative is")
    print(f"    both dense AND sharp, hence F596's +25.7%).")
    print(f"  • Composes F599 (the single-word soft-determinative) + F596 (Egyptian given determinative) + F593 (E×B bind) +")
    print(f"    F569 (English hides the class) + F132/F166/F222. srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
