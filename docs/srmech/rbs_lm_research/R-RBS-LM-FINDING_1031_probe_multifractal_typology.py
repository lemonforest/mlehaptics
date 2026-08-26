"""F1031 probe — PER-ARTICLE D-PROFILES: the multifractal article typology.
For every article >=384 tokens: box-count its anchor field at W=12/24/48/96;
per-octave D_fine=log2(N12/N24), D_mid=log2(N24/N48), D_coarse=log2(N48/N96).
TYPOLOGY VALIDATION (declared structural classes, no content opinion): titles
'list of ...' | pure-year titles ('1945') | month articles | everything else --
if the typology is real, these separate in D-profile. Plus fixture positions."""
import json, math

NUM = {"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
       "twenty","thirty","forty","fifty","hundred","thousand","first","second","third","fourth",
       "fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth"}
MONTHS = {"january","february","march","april","may","june","july","august","september",
          "october","november","december"}
SCALES = (12, 24, 48, 96)

def profile(title, toks):
    t = set(title.lower().split())
    a = [w.isdigit() or w in t or w in NUM for w in toks]
    N = {}
    for s in SCALES:
        nb = len(a) // s
        N[s] = sum(1 for i in range(nb) if any(a[i*s:(i+1)*s]))
    if N[96] == 0 or N[12] == 0:
        return None
    D = [math.log2(N[a_] / max(1, N[b_])) for a_, b_ in zip(SCALES, SCALES[1:])]
    dens = sum(a) / len(a)
    return D, dens

groups = {"list-of": [], "year": [], "month": [], "other": []}
profiles = {}
n = 0
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        rec = json.loads(line)
        toks = rec['s'].split()
        if len(toks) < 384:
            continue
        t = (rec.get('t') or '').lower()
        p = profile(t, toks)
        if p is None:
            continue
        D, dens = p
        if t.startswith('list of'):
            g = 'list-of'
        elif t.isdigit() and len(t) == 4:
            g = 'year'
        elif t in MONTHS:
            g = 'month'
        else:
            g = 'other'
        groups[g].append((D, dens))
        if t in ('fahrenheit', 'april', 'chess', 'black hole', 'water', 'mathematics'):
            profiles[t] = (D, dens)
        n += 1
print("profiled %d articles (>=384 tokens)" % n)
print("\ngroup            n      D_fine  D_mid   D_coarse  anchor-density")
for g, rows in groups.items():
    if not rows:
        continue
    m = len(rows)
    Df = sum(r[0][0] for r in rows) / m
    Dm = sum(r[0][1] for r in rows) / m
    Dc = sum(r[0][2] for r in rows) / m
    dn = sum(r[1] for r in rows) / m
    print("  %-13s %6d  %.3f   %.3f   %.3f     %.3f" % (g, m, Df, Dm, Dc, dn))
# distribution of D_fine over 'other' (the typology axis)
oth = sorted(r[0][0] for r in groups['other'])
q = lambda p: oth[int(p * (len(oth) - 1))]
print("\n'other' D_fine quantiles: p10 %.3f | p25 %.3f | p50 %.3f | p75 %.3f | p90 %.3f"
      % (q(.1), q(.25), q(.5), q(.75), q(.9)))
print("\nfixtures / named articles in the space:")
for t, (D, dens) in sorted(profiles.items()):
    print("  %-12s D=(%.3f, %.3f, %.3f)  density %.3f" % (t, D[0], D[1], D[2], dens))
