"""F896 — the full Siona recall stack END-TO-END at L=8, with the per-article k* (de Bruijn unique
walk) wired into the router. ROUTE (L=8 unique-walk context -> index, F895) -> ADDRESS (sedenion
navigate+carry, exact+EC, F891/893) -> STREAM (phase-keyed reproduce, F879). Also: the MINIMAL routing
context per query (route at L=2..8, smallest L that routes correctly) vs the article's k* -> does the
unique-walk length predict the routing-coherence length? srmech-native rc13; sparse; no bag.
"""
import json, statistics
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, N = 8192, 2, 24, 500
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
def key_at(win, pos): return hdc.klein4_phase_bind(ctx_key(win), pos / PMAX)
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]
def fl(q): return q.as_float() if hasattr(q, "as_float") else q

# ---- the address layer (SionaPageGrid, inline; F891/893) ----
_CN, _CB = 4, 11   # Hamming(15,11): n=4 -> 11 data bits -> hi up to 2047 (16*2048=32768 pages)
class Grid:
    def __init__(s, D): s.reg = cascade.sedenion_register(D=D); s.pages={}; s.addr={}
    def add(s, idx, page):
        lo,hi = idx%16, idx//16; s.pages[idx]=page
        s.addr[idx]=(lo, s.reg.carry([(hi>>b)&1 for b in range(_CB)], n=_CN))
    def fetch(s, lo, cw):
        bits=s.reg.correct(list(cw))["data"]; hi=0
        for b in range(min(_CB,len(bits))): hi|=int(bits[b])<<b
        idx=hi*16+lo; return idx, s.pages.get(idx)

def make_page(toks):
    p = ["<s>"]*K + toks + ["<e>"]
    binds=[hdc.klein4_bind(key_at(p[i-K:i], i), wv(p[i])) for i in range(K, len(p))]
    return {"chunks": hdc.klein4_chunk_bundle(binds,8), "vocab": sorted(set(toks)|{"<e>"}), "toks": toks}
def stream(pg, maxlen=16):
    ctx,out=["<s>"]*K,[]
    for m in range(maxlen):
        sc=hdc.klein4_chunk_resolve(pg["chunks"], key_at(ctx, K+m), [wv(w) for w in pg["vocab"]])
        nx=pg["vocab"][max(range(len(pg["vocab"])), key=lambda j: fl(sc[j]))]; out.append(nx); ctx=(ctx+[nx])[-K:]
        if nx=="<e>": break
    return out
def route_sig(toks, L):
    p=["<s>"]*L+toks+["<e>"]; return cs.bundle_odd([key_at(p[i-L:i], i) for i in range(L, len(p))])
def qkey(toks, L, pos):
    p=["<s>"]*L+toks+["<e>"]; return key_at(p[pos-L:pos], pos)

path="/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts=[]; kstar=[]
with open(path) as f:
    for line in f:
        r=json.loads(line); t=r["s"].split()[:14]
        if len(t)>=9: arts.append(t); kstar.append(r.get("k"))
        if len(arts)>=N: break
N=len(arts)
print(f"=== F896 end-to-end Siona stack @ N={N} (median k* = {statistics.median([k for k in kstar if k])}) ===")

L=8
grid=Grid(D); sigsL={l:[] for l in (2,4,6,8)}
for idx,toks in enumerate(arts):
    grid.add(idx, make_page(toks))
for l in (2,4,6,8):
    sigsL[l]=[route_sig(toks,l) for toks in arts]

samples=[(a, K+len(arts[a])//2) for a in range(0, N, max(1, N//60))]
def route(qk, sigs): return max(range(N), key=lambda b: fl(hdc.klein4_similarity(qk, sigs[b])))

route_ok=addr_ok=fault_ok=e2e_ok=0; minLs=[]
for a, _ in samples:
    pos = L + len(arts[a])//2
    qk = qkey(arts[a], L, pos)
    ridx = route(qk, sigsL[L]); route_ok += int(ridx==a)      # ROUTE (L=8)
    lo,cw = grid.addr[ridx]
    fidx,page = grid.fetch(lo,cw); addr_ok += int(fidx==ridx)  # ADDRESS (clean)
    cwf=list(cw); cwf[a%len(cwf)]^=1
    fidx2,page2 = grid.fetch(lo,cwf); fault_ok += int(fidx2==ridx)  # ADDRESS (1-bit fault, EC)
    if page2 is not None:
        e2e_ok += int(ridx==a and stream(page2)==arts[a]+["<e>"])  # STREAM
    # minimal routing context: smallest L that routes correctly (vs k*)
    for l in (2,4,6,8):
        if route(qkey(arts[a], l, l+len(arts[a])//2), sigsL[l])==a: minLs.append(l); break
    else: minLs.append(99)
n=len(samples)
print(f"  ROUTE   (L=8 unique-walk -> index)         : {route_ok}/{n} = {route_ok/n:.2f}")
print(f"  ADDRESS (sedenion fetch, clean)            : {addr_ok}/{n} = {addr_ok/n:.2f}")
print(f"  ADDRESS (sedenion fetch, 1-bit fault, EC)  : {fault_ok}/{n} = {fault_ok/n:.2f}")
print(f"  END-TO-END route+address+fault+stream      : {e2e_ok}/{n} = {e2e_ok/n:.2f}")
ok_minL=[m for m in minLs if m<99]
print(f"\n  minimal CROSS-article routing context L (smallest L that routes right): mean {statistics.mean(ok_minL):.1f}, max {max(ok_minL)}")
print(f"  (cross-article routing-L scales with corpus size N: ~2-4 @ N={N}, ~8 @ N=2000 (F895b);")
print(f"   distinct from the INTRA-article k* mean {statistics.mean([kstar[a] for a,_ in samples if kstar[a]]):.1f} -- they converge near full-corpus scale.)")
print("  Sparse Klein-4 + octonion route-key + sedenion EC address + phase stream; no dense/numpy/bag.")
