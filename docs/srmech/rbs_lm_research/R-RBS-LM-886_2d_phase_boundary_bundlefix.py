"""F886 (corrects F885) — BUG FIX: klein4_chunk_bundle(binds, 1) returns len(binds) size-1 chunks, so
[0] was a SINGLE BIND, not an over-stuffed bundle. F885's 'uniform collapse' was measured on one bind
(artifact). The true single over-stuffed M = klein4_bundle(*binds). Redo BOTH: (A) F885 position-
amplitude over vs under capacity, and (B) F886 the MFO 2D phase-boundary sweep, with the correct bundle.
srmech-native; Q->float at display; sparse Klein-4; no bag.
"""
import json, statistics
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, LEN, GRID = 8192, 2, 24, 12, 13
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
def bundle(vs): return hdc.klein4_bundle(*vs)               # TRUE single bundle (was the bug)
def f(q): return q.as_float() if hasattr(q, "as_float") else q

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
seqs = []
with open(path) as fh:
    for line in fh:
        toks = json.loads(line)["s"].split()
        if len(toks) >= LEN: seqs.append(toks[:LEN])
        if len(seqs) >= 60: break

def build(n):
    binds, probes = [], []
    for toks in seqs[:n]:
        p = ["<s>"] * K + toks + ["<e>"]
        for i in range(K, len(p)):
            binds.append(hdc.klein4_bind(hdc.klein4_phase_bind(ctx_key(p[i-K:i]), i/PMAX), wv(p[i])))
            probes.append((i-K, p[i-K:i], i, p[i]))
    return bundle(binds), probes, len(binds)

print("=== (A) F885 REDO with TRUE bundle: true-token resonance per position ===")
for n, lbl in ((60, "OVER (60 seq)"), (1, "UNDER (1 seq)")):
    M, probes, nb = build(n)
    npos = LEN+1; acc=[0.0]*npos; cnt=[0]*npos
    for m, ctx, ap, tok in probes:
        s = f(hdc.klein4_similarity(unbind(M, hdc.klein4_phase_bind(ctx_key(ctx), ap/PMAX)), wv(tok)))
        acc[m]+=s; cnt[m]+=1
    prof=[acc[i]/cnt[i] if cnt[i] else 0 for i in range(npos)]
    print(f"  {lbl:14s} {nb:4d} binds | mean {sum(prof)/len(prof):.4f} | pos0 {prof[0]:.3f} | interior[1:] {min(prof[1:]):.3f}-{max(prof[1:]):.3f}")

print("\n=== (B) F886 2D phase-boundary sweep (MFO: dark star = 2D phase boundary), recoverable ref ===")
binds=[]
for toks in seqs[:1]:
    p = ["<s>"]*K+toks+["<e>"]
    for i in range(K,len(p)): binds.append(hdc.klein4_bind(hdc.klein4_phase_bind(ctx_key(p[i-K:i]), i/PMAX), wv(p[i])))
ref_ctx, ref_tok = ["the","first"], "letter"
ref_key0 = ctx_key(ref_ctx); binds.append(hdc.klein4_bind(ref_key0, wv(ref_tok)))
M = bundle(binds)
def res_at(a, b):
    k = hdc.klein4_phase_bind(ref_key0, a, elem=2); k = hdc.klein4_phase_bind(k, b, elem=1)
    return f(hdc.klein4_similarity(unbind(M, k), wv(ref_tok)))
grid=[[res_at(i/(GRID-1), j/(GRID-1)) for j in range(GRID)] for i in range(GRID)]
flat=[v for r in grid for v in r]; lo,hi=min(flat),max(flat); rng=hi-lo or 1
chars=" .:-=+*#%@"
print(f"  {len(binds)} binds (recoverable); range [{lo:.4f},{hi:.4f}] floor~0.25; rows=phi_g5 cols=phi_w7")
for i in range(GRID):
    print("  "+"".join(chars[min(8,int((v-lo)/rng*9))] for v in grid[i]))
grads=[cascade.magnitude(grid[i][j+1]-grid[i][j]) for i in range(GRID) for j in range(GRID-1)]  # Class-K real pin-slot magnitude of the delta
mid=(hi+lo)/2
print(f"\n  peak(0,0) {grid[0][0]:.4f} | mean {sum(flat)/len(flat):.4f} | floor {lo:.4f} | hi {hi:.4f}")
print(f"  frac above midpoint {sum(1 for v in flat if v>mid)/len(flat):.2f} | max grad {max(grads):.4f} vs mean {statistics.mean(grads):.4f}")
print("  SHARP boundary (cliff: small high-region + max>>mean grad) vs SMOOTH gradient vs FLAT(no signal).")
print("  Q->float at display. Sparse Klein-4; no bag.")
