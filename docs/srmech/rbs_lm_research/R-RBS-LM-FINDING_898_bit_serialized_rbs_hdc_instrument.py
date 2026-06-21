"""F898 — BUILD THE THING: the resonant bit-serialized RBS-HDC instrument. Encode articles into their
Klein-4 recall structure (the chunked-M, F879), SERIALIZE the hypervectors to BITS (2-bit/slot packed,
the boolean belly), write a binary .rbs file, read it BACK from disk, deserialize, and RECALL the
article from the bits — the instrument standing on its own. A shared global CODEBOOK (vocab -> Klein-4)
is the only text, built once. Measure the bit-serialized instrument size. srmech-native; no dense float.
"""
import json, os, tempfile, array
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, C = 8192, 2, 24, 8
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

# --- THE BIT SERIALIZER: Klein-4 HV <-> 2-bit-packed bytes (4 sectors -> 2 bits -> 4 slots/byte) ---
def hv_to_bits(hv):
    secs = hv.tolist()                                  # D sector values in {0,1,2,3}
    out = bytearray((len(secs) + 3) // 4)
    for i, s in enumerate(secs):
        out[i >> 2] |= (int(s) & 3) << ((i & 3) * 2)
    return bytes(out)
def bits_to_hv(b, D=D):
    secs = [ (b[i >> 2] >> ((i & 3) * 2)) & 3 for i in range(D) ]
    return hdc.HV.from_sequence(secs, sectors=4)

def make_chunks(toks):                                  # the article's recall structure = chunked-M
    p = ["<s>"]*K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_at(p[i-K:i], i), wv(p[i])) for i in range(K, len(p))]
    return hdc.klein4_chunk_bundle(binds, C)
def stream(chunks, vocab, maxlen=64):
    ctx, out = ["<s>"]*K, []
    for m in range(maxlen):
        sc = hdc.klein4_chunk_resolve(chunks, key_at(ctx, K+m), [wv(w) for w in vocab])
        nx = vocab[max(range(len(vocab)), key=lambda j: fl(sc[j]))]; out.append(nx); ctx = (ctx+[nx])[-K:]
        if nx == "<e>": break
    return out

path = "/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
arts = []
with open(path) as f:
    for line in f:
        t = json.loads(line)["s"].split()
        if 12 <= len(t) <= 40: arts.append(t)
        if len(arts) >= 10: break

print(f"=== F898 the bit-serialized RBS-HDC instrument ({len(arts)} real articles) ===")
# (0) serializer round-trip
t0 = hdc.klein4_random(D, seed=99); rt = bits_to_hv(hv_to_bits(t0)).tolist() == t0.tolist()
print(f"  serializer: HV -> {len(hv_to_bits(t0))} bytes (2-bit packed; native tobytes was {len(t0.tobytes())}); round-trip exact: {rt}")

tmp = tempfile.mkdtemp(prefix="rbs_")
codebook = sorted({w for toks in arts for w in (["<s>","<e>"]+toks)})   # the ONE shared codebook (token strings)
text_total = hdc_total = recall_ok = 0
for idx, toks in enumerate(arts):
    chunks = make_chunks(toks)                          # the RBS-HDC instrument (in HVs)
    inst_path = os.path.join(tmp, f"art{idx}.rbs")
    with open(inst_path, "wb") as fh:                   # SERIALIZE the instrument to a binary file
        for ch in chunks: fh.write(hv_to_bits(ch))
    hdc_total += os.path.getsize(inst_path); text_total += len(" ".join(toks).encode())
    # READ BACK from disk -> deserialize -> recall (the instrument standing on its own)
    raw = open(inst_path, "rb").read(); step = (D + 3)//4
    chunks2 = [bits_to_hv(raw[i*step:(i+1)*step]) for i in range(len(raw)//step)]
    out = stream(chunks2, codebook)
    recall_ok += int(out == toks + ["<e>"])
print(f"\n  per-article RBS-HDC instrument: {hdc_total//len(arts)} bytes (binary HVs) vs text {text_total//len(arts)} bytes")
print(f"  RECALL FROM THE SERIALIZED BITS (read .rbs from disk -> deserialize -> stream): {recall_ok}/{len(arts)} exact")
print(f"  shared codebook: {len(codebook)} tokens (the one text artifact; regenerates the Klein-4 vocab)")
print("\n  THIS is the instrument: bit-serialized Klein-4 HVs that recall the article from disk. No text bloat in the HDC; no dense float; no bag.")
