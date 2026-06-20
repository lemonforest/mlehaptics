"""F893 — wire the sedenion grid as Siona's page-address layer: the full recall stack
ROUTE (resonance -> page index, F882/F880) -> ADDRESS (sedenion navigate+carry, exact + Hamming-EC,
F891) -> STREAM (phase-keyed within-page reproduction, F879). The address layer makes the routed
index STRUCTURED (base-16) and FAULT-TOLERANT (single-bit address error corrected), which the flat
F880 index was not. >16 pages. srmech-native rc11; sparse Klein-4; Q-aware; no bag.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, NPAGE = 8192, 2, 24, 64
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

# ---- the Siona page-address layer: sedenion navigate+carry as the fault-tolerant index (F891) ----
class SionaPageGrid:
    def __init__(self, D=8192):
        self.reg = cascade.sedenion_register(D=D); self.pages = {}; self.addr = {}
    def add(self, idx, page):
        self.pages[idx] = page
        lo, hi = idx % 16, idx // 16
        self.addr[idx] = (lo, self.reg.carry([(hi >> b) & 1 for b in range(4)], n=3))   # Hamming(7,4) EC
    def fetch(self, lo, carry_cw):                                # base-slot + EC'd high bits -> exact page
        bits = self.reg.correct(carry_cw)["data"]                # single-error-correcting decode
        hi = sum(int(bits[b]) << b for b in range(min(4, len(bits))))
        idx = hi * 16 + lo
        return idx, self.pages.get(idx)

def make_page(toks):
    p = ["<s>"] * K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_at(p[i-K:i], i), wv(p[i])) for i in range(K, len(p))]
    return {"chunks": hdc.klein4_chunk_bundle(binds, 8), "vocab": sorted(set(toks) | {"<e>"}), "toks": toks}
def page_sig(toks):
    p = ["<s>"] * K + toks + ["<e>"]
    return cs.bundle_odd([key_at(p[i-K:i], i) for i in range(K, len(p))])
def stream(page, maxlen=16):
    ctx, out = ["<s>"] * K, []
    for m in range(maxlen):
        cand = page["vocab"]
        sc = hdc.klein4_chunk_resolve(page["chunks"], key_at(ctx, K+m), [wv(w) for w in cand])
        nxt = cand[max(range(len(cand)), key=lambda j: sc[j])]; out.append(nxt); ctx = (ctx+[nxt])[-K:]
        if nxt == "<e>": break
    return out

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as fh:
    for line in fh:
        t = json.loads(line)["s"].split()[:14]
        if len(t) >= K + 3: arts.append(t)
        if len(arts) >= NPAGE: break
NPAGE = len(arts)

print(f"=== F893 Siona recall stack: ROUTE -> ADDRESS(sedenion) -> STREAM @ {NPAGE} pages ===")
grid = SionaPageGrid(D=D); sigs = []
for idx, toks in enumerate(arts):
    grid.add(idx, make_page(toks)); sigs.append(page_sig(toks))

# query = a stored mid-context from each article (reproduction routing, F880)
def route(qk): return max(range(NPAGE), key=lambda b: hdc.klein4_similarity(qk, sigs[b]))
samples = []
for idx, toks in enumerate(arts):
    p = ["<s>"]*K + toks + ["<e>"]; mid = K + (len(toks)//2)
    samples.append((idx, key_at(p[mid-K:mid], mid)))

route_ok = addr_ok = addr_fault_ok = e2e_ok = 0
for true_idx, qk in samples:
    ridx = route(qk)                                   # 1) ROUTE: resonance -> page index
    route_ok += int(ridx == true_idx)
    lo, cw = grid.addr[ridx]                           # 2) ADDRESS: sedenion navigate+carry (exact + EC)
    fidx, page = grid.fetch(lo, cw); addr_ok += int(fidx == ridx)
    cwf = list(cw); cwf[true_idx % len(cwf)] ^= 1      # inject a single-bit fault in the address carry
    fidx2, page2 = grid.fetch(lo, cwf); addr_fault_ok += int(fidx2 == ridx)
    if page2 is not None:                              # 3) STREAM: phase-keyed within-page reproduce
        e2e_ok += int(stream(page2) == arts[ridx] + ["<e>"] and ridx == true_idx)
n = len(samples)
print(f"  1) ROUTE  (resonance -> index)            : {route_ok}/{n} = {route_ok/n:.2f}")
print(f"  2) ADDRESS(sedenion fetch, clean)         : {addr_ok}/{n} = {addr_ok/n:.2f}")
print(f"  2') ADDRESS(sedenion fetch, 1-bit fault)  : {addr_fault_ok}/{n} = {addr_fault_ok/n:.2f}  (EC-recovered)")
print(f"  3) END-TO-END route+address+fault+stream  : {e2e_ok}/{n} = {e2e_ok/n:.2f}")
print("\n  ADDRESS layer = exact + single-error-correcting (sedenion navigate+carry, F891), independent of")
print("  the lossy ROUTE (resonance ceiling). >16 pages handled by the base-16 carry. Sparse; no bag.")
