"""F1030 probe — IS THE ANCHOR FIELD FRACTAL, and does the dyadic dial work?
(1) BOX-COUNTING: N(W) = number of W-token boxes containing >=1 anchor, at W = 12..192.
    log-log slope = the anchor field's box dimension D. D<1 = clustered (fractal structure
    real, dyadic descent justified); D~=1 = uniform (fractal buys nothing -- honest null).
(2) THE DIAL: dyadic descent (same density test rho >= 1/6 at every scale; keep a block at
    the COARSEST passing scale; descend into failures down to min-scale tau). Measure kept%
    + fixture survival as a function of tau in {192, 96, 48, 24, 12}."""
import json
from srmech.amsc import rational

NUM = {"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
       "twenty","thirty","forty","fifty","hundred","thousand","first","second","third","fourth",
       "fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth"}

def anchors(title, toks):
    t = set(title.lower().split())
    return [w.isdigit() or w in t or w in NUM for w in toks]

# ---- (1) box-counting over a 4k-article sample ----
import itertools
scales = [12, 24, 48, 96, 192]
boxes = {s: 0 for s in scales}
total = {s: 0 for s in scales}
n = 0
arts = []
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in itertools.islice(f, 0, 40000, 10):
        rec = json.loads(line)
        toks = rec['s'].split()
        if len(toks) < 200:
            continue
        a = anchors(rec.get('t') or '', toks)
        arts.append((rec.get('t') or '', toks, a))
        for s in scales:
            nb = len(a) // s
            total[s] += nb
            boxes[s] += sum(1 for i in range(nb) if any(a[i*s:(i+1)*s]))
        n += 1
        if n >= 4000:
            break
print("box-counting over %d articles (>=200 tokens):" % n)
print("  W     occupied/total   occupancy")
for s in scales:
    print("  %-5d %8d/%-8d %.3f" % (s, boxes[s], total[s], boxes[s]/max(1,total[s])))
# slope between successive scales: log2(N_s / N_2s) -- dimension estimate per octave
print("  per-octave dimension D = log2(N(W)/N(2W)):")
for a_, b_ in zip(scales, scales[1:]):
    import math
    d = math.log2(boxes[a_] / max(1, boxes[b_]))
    print("    W %d->%d : D = %.3f" % (a_, b_, d))

# ---- (2) the dyadic dial ----
def dyadic(toks, a, tau, W0=192):
    keep = [False]*len(toks)
    def descend(lo, hi):
        n_ = hi - lo
        if n_ <= 0: return
        dens_ok = sum(a[lo:hi]) * 6 >= n_          # rho >= 1/6, scale-invariant, integer math
        if dens_ok:
            for j in range(lo, hi): keep[j] = True
            return
        if n_ <= tau:                               # the DIAL: below tau, a failing block drops
            return
        mid = lo + n_ // 2
        descend(lo, mid); descend(mid, hi)
    for i in range(0, len(toks), W0):
        descend(i, min(i + W0, len(toks)))
    return keep

FIX = {'fahrenheit': ['5 9 x f 32','freezes at 32','boils at 212'],
       'april': ['30 days','fourth month'], 'chess': ['64','two players']}
idx = json.load(open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json'))
fixarts = {}
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for t in FIX:
        f.seek(idx[t]); rec = json.loads(f.readline())
        toks = rec['s'].split()
        fixarts[t] = (toks, anchors(t, toks))
print("\nTHE DIAL (dyadic descent, rho>=1/6 at every scale; tau = min descent scale):")
print("  tau   kept%%(sample)   fixture survival")
for tau in (192, 96, 48, 24, 12, 6):
    kin = kout = 0
    for _, toks, a in arts[:600]:
        k = dyadic(toks, a, tau)
        kin += len(toks); kout += sum(k)
    surv = []
    for t, checks in FIX.items():
        toks, a = fixarts[t]
        q = ' '.join(w for w, kk in zip(toks, dyadic(toks, a, tau)) if kk)
        surv.append("%s %d/%d" % (t[:4], sum(1 for c in checks if c in q), len(checks)))
    print("  %-5d %5.1f%%          %s" % (tau, 100.0*kout/max(1,kin), '  '.join(surv)))
