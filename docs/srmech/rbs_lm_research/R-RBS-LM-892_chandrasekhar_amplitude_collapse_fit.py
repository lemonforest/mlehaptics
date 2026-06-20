"""F892 (thread 2) — fit the amplitude-collapse-vs-load to a degeneracy/Chandrasekhar form. F890 found
the null gets DARKER (amplitude collapses) with load, not gentler-edged. F871 predicts signal ~ 1/sqrt(N)
(the SNR floor). TEST: measure mean recall amplitude vs load N (averaged over references), find the
power law signal ~ N^-p (p~0.5 = capacity/degeneracy), and the COLLAPSE THRESHOLD N* where signal sinks
into the floor noise = the dark-star transition (the Chandrasekhar 'mass'). srmech-native; Q->float at
the analysis boundary; sparse Klein-4; no bag.
"""
import json, math, statistics
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX = 8192, 2, 24
cs = S.ContextSubstrate(D=D, hex_chars=16)
def _dig(s):
    h = fmt.sha256_bytes(s.encode()); return bytes.fromhex(h) if isinstance(h, str) else h
def byte_k4(b): return hdc.klein4_random(D, seed=b)
def word_k4(w):
    return cs.bundle_odd([hdc.klein4_bind(byte_k4(b), cs.pos_key(i)) for i, b in enumerate(w.encode("utf-8"))])
def byte_oct(b):
    d = _dig(f"LoE.byte.{b}"); return tuple((d[i] % 9) - 4 for i in range(8))
def word_oct(w):
    bs = w.encode("utf-8"); p = byte_oct(bs[0])
    for b in bs[1:]: p = tuple(cascade.cd_mult(p, byte_oct(b)))
    return p
def ctx_key(win):
    p = word_oct(win[0])
    for w in win[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    return hdc.klein4_random(D, seed=int.from_bytes(_dig(",".join(str(x) for x in p))[:8], "big"))
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]
unbind = getattr(hdc, "klein4_unbind", hdc.klein4_bind)
def fl(q): return q.as_float() if hasattr(q, "as_float") else q

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
seqs = []
with open(path) as fh:
    for line in fh:
        t = json.loads(line)["s"].split()
        if len(t) >= 12: seqs.append(t[:12])
        if len(seqs) >= 80: break
# a big pool of (key, token, bind) triples
items = []
for toks in seqs:
    p = ["<s>"]*K + toks + ["<e>"]
    for i in range(K, len(p)):
        k = hdc.klein4_phase_bind(ctx_key(p[i-K:i]), i/PMAX)
        items.append((k, p[i], hdc.klein4_bind(k, wv(p[i]))))
R = 10                                                # references averaged per load
loads = [1,2,4,8,16,24,32,48,64,96,128,192,256,384,512]
print(f"=== F892 Chandrasekhar fit: recall amplitude vs load N (pool {len(items)} binds, {R} refs avg) ===")
print("  N (mass) | recall amp | floor | signal=amp-floor")
floor_vals=[]
rows=[]
for N in loads:
    amps=[]; floors=[]
    for r in range(R):
        base = r * 7 % (len(items)-N)
        chunk = items[base:base+N]
        M = hdc.klein4_bundle(*[b for _,_,b in chunk])
        kref,tref,_ = chunk[0]
        amps.append(fl(hdc.klein4_similarity(unbind(M, kref), wv(tref))))
        # floor: probe with a foreign key/token not bound in this chunk
        kf,_,_ = items[(base+N) % len(items)]; _,tf,_ = items[(base+N+1) % len(items)]
        floors.append(fl(hdc.klein4_similarity(unbind(M, kf), wv(tf))))
    a=statistics.mean(amps); f=statistics.mean(floors); floor_vals.append(f)
    rows.append((N,a,f,a-f))
    print(f"  {N:5d}    |  {a:.4f}   | {f:.4f}| {a-f:+.4f}")
floor=statistics.mean(floor_vals); floor_sd=statistics.pstdev([x for _,_,_,_ in [(0,0,0,0)]] or [0]) # placeholder
# power-law fit signal ~ N^-p over the points where signal>0
pts=[(math.log(N), math.log(s)) for N,_,_,s in rows if s>1e-4]
n=len(pts); sx=sum(x for x,_ in pts); sy=sum(y for _,y in pts); sxx=sum(x*x for x,_ in pts); sxy=sum(x*y for x,y in pts)
p=-(n*sxy-sx*sy)/(n*sxx-sx*sx)
# Chandrasekhar threshold N*: where signal first sinks to <= the floor's own scatter
floor_scatter=statistics.pstdev(floor_vals)
Nstar=next((N for N,_,_,s in rows if s<=2*floor_scatter), None)
print(f"\n  power law: signal ~ N^(-{p:.2f})   (0.5 = the 1/sqrt(N) capacity/degeneracy law, F871)")
print(f"  floor {floor:.4f} (scatter {floor_scatter:.4f}); COLLAPSE THRESHOLD N* ~ {Nstar} binds")
print(f"  (N* = the dark-star transition = the substrate's Chandrasekhar 'mass' — signal lost in the floor)")
print("  Q->float at analysis boundary. Sparse Klein-4; no bag.")
