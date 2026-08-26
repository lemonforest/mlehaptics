"""F1032 probe — the (D_fine, density) CENSUS + the SELF-TUNED kernel build in one pass.
Per article: profile D_fine (>=384 tokens; shorter = 'short' class, flat tau=12), select tau
by MEASURED band edges (F1031 quantiles p25=0.452 / p75=0.772) + the chronology fingerprint:
  concept   D<0.452            -> tau=6   (facts cluster; deep descent pays)
  mid       0.452<=D<0.772     -> tau=12  (the F1029 slice)
  even+dense D>=0.772, dens>=0.15 -> tau=192 (lists: coarse blocks pass naturally)
  even+thin  D>=0.772, dens<0.15  -> tau=48  (chronology: coarse-only descent drops year-spam)
Outputs: census counts, per-band keep rates, TOTAL kernel size (id-stream+gz), fixtures."""
import json, math, gzip, struct

NUM = {"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
       "twenty","thirty","forty","fifty","hundred","thousand","first","second","third","fourth",
       "fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth"}

def anchors(title, toks):
    t = set(title.lower().split())
    return [w.isdigit() or w in t or w in NUM for w in toks]

def d_fine(a):
    n12 = sum(1 for i in range(len(a) // 12) if any(a[i*12:(i+1)*12]))
    n24 = sum(1 for i in range(len(a) // 24) if any(a[i*24:(i+1)*24]))
    return math.log2(n12 / n24) if n12 and n24 else None

def dyadic(toks, a, tau, W0=192):
    keep = [False] * len(toks)
    def descend(lo, hi):
        n_ = hi - lo
        if n_ <= 0: return
        if sum(a[lo:hi]) * 6 >= n_:
            for j in range(lo, hi): keep[j] = True
            return
        if n_ <= tau: return
        mid = lo + n_ // 2
        descend(lo, mid); descend(mid, hi)
    for i in range(0, len(toks), W0):
        descend(i, min(i + W0, len(toks)))
    return keep

def band_of(D, dens):
    if D is None: return 'short', 12
    if D < 0.452: return 'concept', 6
    if D < 0.772: return 'mid', 12
    return ('even-dense', 192) if dens >= 0.15 else ('even-thin', 48)

census = {}
kin = {}
kout = {}
vocab = {}
rows = []
FIXQ = {}
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        rec = json.loads(line)
        t = (rec.get('t') or '')
        toks = rec['s'].split()
        a = anchors(t, toks)
        D = d_fine(a) if len(toks) >= 384 else None
        dens = sum(a) / max(1, len(a))
        band, tau = band_of(D, dens)
        census[band] = census.get(band, 0) + 1
        k = dyadic(toks, a, tau)
        q = [w for w, kk in zip(toks, k) if kk]
        kin[band] = kin.get(band, 0) + len(toks)
        kout[band] = kout.get(band, 0) + len(q)
        rows.append([vocab.setdefault(w, len(vocab)) for w in q])
        if t in ('fahrenheit', 'april', 'chess', 'black hole', 'mathematics'):
            FIXQ[t] = (band, tau, ' '.join(q))
print("CENSUS + per-band keep:")
for b in ('concept', 'mid', 'even-dense', 'even-thin', 'short'):
    if b in census:
        print("  %-11s n=%7d  keep %5.1f%%" % (b, census[b], 100.0 * kout.get(b,0) / max(1, kin.get(b,1))))
ti, to = sum(kin.values()), sum(kout.values())
print("TOTAL: %d -> %d tokens (%.1f%%)" % (ti, to, 100.0 * to / ti))
fmt = "<I" if len(vocab) > 65535 else "<H"
stream = b"".join(struct.pack(fmt, i) for r in rows for i in r)
code = "\n".join(sorted(vocab, key=vocab.get)).encode()
gz = gzip.compress(stream + code, 9)
print("SELF-TUNED kernel: %.1f MB gz (vs F1029 flat tau=12: 55.9 MB @ 51.6%%)" % (len(gz) / 1e6))
print("\nfixtures (band, tau | survival):")
CHK = {'fahrenheit': ['5 9 x f 32','freezes at 32','boils at 212'], 'april': ['30 days','fourth month'],
       'chess': ['64','two players'], 'black hole': ['gravity','light'], 'mathematics': ['numbers']}
for t, (band, tau, q) in FIXQ.items():
    ok = sum(1 for c in CHK[t] if c in q)
    print("  %-12s %-10s tau=%-3d  %d/%d" % (t, band, tau, ok, len(CHK[t])))
