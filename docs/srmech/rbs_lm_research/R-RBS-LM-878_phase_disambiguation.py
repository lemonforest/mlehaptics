"""F878: answer the wave question to improve Siona -- the K=2 branching collapse (F875)
is PHASE-BLINDNESS. Two continuations of the same context = two waves superposed at one
node; separate them by PHASE = the stream position (the 1D_t fiber). Bind the recall key
with klein4_phase_bind (the shipped phase op, s59) at the token's stream-position -> the
two occurrences get different phase-keys -> the resonator separates them. A/B: phase-off
(F877 baseline) vs phase-on. srmech-native (chunk_bundle/chunk_resolve/phase_bind), no bag.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, C, K, PMAX = 8192, 8, 2, 24
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
def key_at(win, pos, use_phase):
    k = ctx_key(win)
    return hdc.klein4_phase_bind(k, pos / PMAX) if use_phase else k    # the 1D_t PHASE (s59) into the key
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:14]
        if len(toks) >= K + 3: arts.append(toks)
        if len(arts) >= 4: break

def make_page(toks, use_phase):
    p = ["<s>"] * K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_at(p[i - K:i], i, use_phase), wv(p[i])) for i in range(K, len(p))]
    return {"chunks": hdc.klein4_chunk_bundle(binds, C), "vocab": sorted(set(toks) | {"<e>"}), "toks": toks}

def stream(page, use_phase, maxlen=16):
    ctx, out = ["<s>"] * K, []
    for m in range(maxlen):
        pos = K + m                                                    # absolute stream position (phase)
        cand = page["vocab"]
        scores = hdc.klein4_chunk_resolve(page["chunks"], key_at(ctx, pos, use_phase), [wv(w) for w in cand])
        nxt = max(range(len(cand)), key=lambda j: scores[j]); nxt = cand[nxt]
        out.append(nxt); ctx = (ctx + [nxt])[-K:]
        if nxt == "<e>": break
    return out

for use_phase in (False, True):
    label = "PHASE-ON (1D_t fiber)" if use_phase else "phase-off (F877 baseline)"
    print(f"=== {label} ===")
    tot_ok = tot = 0
    for i, toks in enumerate(arts):
        page = make_page(toks, use_phase)
        emitted = stream(page, use_phase); target = toks + ["<e>"]
        m = sum(1 for a, b in zip(emitted, target) if a == b); tot_ok += m; tot += len(target)
        tag = "" if emitted == target else "  <-- branch collapse" if len(emitted) < len(target) else ""
        print(f"  page {i}: {m}/{len(target)}{tag}  {' '.join(emitted)}")
    print(f"  overall: {tot_ok}/{tot} = {tot_ok/tot:.2f}\n")
print("phase = the stream-position bound into the recall key via klein4_phase_bind (s59, the 1D_t")
print("fiber). The branching collapse was phase-blindness: same context, two continuations = two")
print("superposed waves at one node; the phase (position) separates them. Reproduction fix (phase")
print("is position-locked to the trained sequence) -- the wave answer that improves Siona recall.")
