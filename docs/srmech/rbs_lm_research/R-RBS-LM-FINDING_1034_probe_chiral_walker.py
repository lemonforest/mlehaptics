"""F1034 probe — THE WALKER: hop-bounded navigation over the quantized mention-edge graph
from the srmech+MFO math seed (the F1028 foundational-reduction criterion, graph-walk form —
bag-closure saturated at hop 2; does the WALK stay bounded?). Plus the corpus FLUX RANKING:
the most-negated concepts (aggregate negation fraction per mentioned title)."""
import json, re, sys
from collections import defaultdict

NEG = {"not", "no", "never", "without"}
NUM = {"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
       "twenty","thirty","forty","fifty","hundred","thousand","first","second","third","fourth",
       "fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth"}

def quantize(title, toks, W=12, S=6):
    t = set(title.split())
    a = [w.isdigit() or w in t or w in NUM for w in toks]
    keep = [False]*len(toks)
    for i in range(0, max(1, len(toks)-W+1), S):
        if sum(a[i:i+W]) >= 2:
            for j in range(i, min(i+W, len(toks))): keep[j] = True
    return [w for w,k in zip(toks,keep) if k]

idx = json.load(open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json'))
titles1 = {t for t in idx if ' ' not in t and len(t) > 3}
out_edges = defaultdict(set)      # title -> mentioned titles (directed, from quantized spans)
neg_cnt = defaultdict(int)        # mentioned title -> negated mentions
pos_cnt = defaultdict(int)
sizes = {}
n = 0
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        rec = json.loads(line)
        t = (rec.get('t') or '').lower()
        toks = rec['s'].split()
        q = quantize(t, toks)
        sizes[t] = len(q)
        tset = set(t.split())
        def is_neg(win, k):
            # 'no' adjacent to a digit is the NUMBER abbreviation (Op. 59 No. 2), not negation --
            # the no/number HOMOGRAPH caught by the v1 ranking (mazurka 78% 'negated')
            for j, x in enumerate(win):
                if x in NEG:
                    if x == "no" and (
                        (j + 1 < len(win) and win[j + 1].isdigit())
                        or (j + 1 == len(win) and k < len(q) and q[k].isdigit())):
                        continue
                    return True
            return False
        for i, w in enumerate(q):
            if w in titles1 and w not in tset:
                out_edges[t].add(w)
                if is_neg(q[max(0, i-8):i], i):
                    neg_cnt[w] += 1
                else:
                    pos_cnt[w] += 1
        n += 1
print("graph built: %d articles, %d nodes with out-edges, %d total edges"
      % (n, len(out_edges), sum(len(v) for v in out_edges.values())))

# --- the SEED: notebook-distinctive words that ARE single-word titles ---
def toks_of(p):
    return [w for w in re.split(r'[^a-z0-9]+', open(p, encoding='utf-8', errors='replace').read().lower())
            if len(w) > 3]
tf = defaultdict(int)
for p in (sys.argv[1], sys.argv[2]):
    for w in toks_of(p):
        tf[w] += 1
seed = {w for w, c in tf.items() if c >= 5 and w in titles1}
print("seed: %d notebook-frequent single-word titles (sample: %s)"
      % (len(seed), sorted(seed, key=lambda w: -tf[w])[:10]))

# --- THE WALK: hop-bounded BFS over out-edges ---
frontier = set(seed) & set(out_edges)
visited = set(frontier)
for hop in (1, 2, 3):
    nxt = set()
    for u in frontier:
        nxt |= out_edges.get(u, set())
    nxt -= visited
    visited |= nxt
    frontier = nxt
    ktok = sum(sizes.get(t, 0) for t in visited)
    print("hop %d: +%6d new | closure %6d articles (%.1f%% of corpus) | quantized ~%.1f M tokens"
          % (hop, len(nxt), len(visited), 100.0 * len(visited) / n, ktok / 1e6))

# --- THE FLUX RANKING: most-negated concepts (>=30 mentions) ---
print("\nmost-NEGATED concepts (negation fraction, >=30 mentions):")
ranked = sorted(((neg_cnt[w], pos_cnt[w], w) for w in neg_cnt
                 if neg_cnt[w] + pos_cnt[w] >= 30),
                key=lambda x: -x[0] / (x[0] + x[1]))
for ng, ps, w in ranked[:12]:
    print("  %-16s %4d neg / %5d total (%.0f%%)" % (w, ng, ng + ps, 100.0 * ng / (ng + ps)))
