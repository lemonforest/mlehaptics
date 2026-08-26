"""F1035 — EMIT the foundational kernel artifact v1 (the distributable):
hop-3 walk closure from the srmech+MFO seed -> self-tuned quantized spans (F1032 bands) ->
id-stream + codebook + title index + CHIRAL EDGE LIST (u,v,charge-sense) + the ATTESTED OP-LOG
(source sha, seed hash, every rule parameter). Round-trip verified."""
import json, re, gzip, struct, math, os, sys, datetime
from collections import defaultdict
from srmech.amsc.format import sha256_bytes

NEG = {"not", "no", "never", "without"}
NUM = {"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
       "twenty","thirty","forty","fifty","hundred","thousand","first","second","third","fourth",
       "fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth"}
W0, RHO_NUM, RHO_DEN = 192, 1, 6

def anchors(title, toks):
    t = set(title.split())
    return [w.isdigit() or w in t or w in NUM for w in toks]

def d_fine(a):
    n12 = sum(1 for i in range(len(a)//12) if any(a[i*12:(i+1)*12]))
    n24 = sum(1 for i in range(len(a)//24) if any(a[i*24:(i+1)*24]))
    return math.log2(n12/n24) if n12 and n24 else None

def tau_of(D, dens):
    if D is None: return 12
    if D < 0.452: return 6
    if D < 0.772: return 12
    return 192 if dens >= 0.15 else 48

def dyadic(toks, a, tau):
    keep = [False]*len(toks)
    def descend(lo, hi):
        n_ = hi-lo
        if n_ <= 0: return
        if sum(a[lo:hi]) * RHO_DEN >= n_ * RHO_NUM:
            for j in range(lo, hi): keep[j] = True
            return
        if n_ <= tau: return
        mid = lo + n_//2
        descend(lo, mid); descend(mid, hi)
    for i in range(0, len(toks), W0):
        descend(i, min(i+W0, len(toks)))
    return keep

INSTR = '/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson'
idx = json.load(open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json'))
titles1 = {t for t in idx if ' ' not in t and len(t) > 3}

# pass 1: quantized spans + mention edges for ALL articles (the walk needs the full graph)
out_edges = defaultdict(set)
qspans = {}
with open(INSTR) as f:
    for line in f:
        rec = json.loads(line)
        t = (rec.get('t') or '').lower()
        toks = rec['s'].split()
        a = anchors(t, toks)
        q = [w for w, k in zip(toks, dyadic(toks, a, tau_of(d_fine(a) if len(toks) >= 384 else None,
                                                            sum(a)/max(1,len(a))))) if k]
        qspans[t] = q
        tset = set(t.split())
        for w in set(q):
            if w in titles1 and w not in tset:
                out_edges[t].add(w)

# seed + hop-3 walk
def ntoks(p):
    return [w for w in re.split(r'[^a-z0-9]+', open(p, encoding='utf-8', errors='replace').read().lower())
            if len(w) > 3]
tf = defaultdict(int)
for p in (sys.argv[1], sys.argv[2]):
    for w in ntoks(p): tf[w] += 1
seed = sorted(w for w, c in tf.items() if c >= 5 and w in titles1)
frontier = set(seed) & set(out_edges)
closure = set(frontier)
for hop in range(3):
    nxt = set()
    for u in frontier: nxt |= out_edges.get(u, set())
    nxt -= closure; closure |= nxt; frontier = nxt
closure = sorted(closure)

# emit: id-stream + codebook + titles + edges(with negation sense) restricted to the closure
vocab, rows = {}, []
tid = {t: i for i, t in enumerate(closure)}
edges = []
for t in closure:
    q = qspans.get(t, [])
    rows.append([vocab.setdefault(w, len(vocab)) for w in q])
    tset = set(t.split())
    for i, w in enumerate(q):
        if w in tid and w not in tset:
            neg = any(x in NEG and not (x == "no" and i2+1 < len(q) and q[i2+1].isdigit())
                      for i2, x in enumerate(q[max(0,i-8):i], start=max(0,i-8)))
            edges.append((tid[t], tid[w], -1 if neg else 1))
out_dir = '/home/skirklan/corpora/kernel_artifacts/foundational_kernel_v1'
os.makedirs(out_dir, exist_ok=True)
fmt = "<I" if len(vocab) > 65535 else "<H"
stream = b"".join(struct.pack(fmt, i) for r in rows for i in r)
lens = b"".join(struct.pack("<I", len(r)) for r in rows)
code = "\n".join(sorted(vocab, key=vocab.get)).encode()
tit = "\n".join(closure).encode()
edg = b"".join(struct.pack("<IIb", u, v, c) for u, v, c in edges)
blob = gzip.compress(struct.pack("<III", len(rows), len(vocab), len(edges))
                     + lens + stream + code + b"\x00" + tit + b"\x00" + edg, 9)
open(os.path.join(out_dir, 'kernel.bin.gz'), 'wb').write(blob)
with open(INSTR, 'rb') as f:
    h = sha256_bytes(f.read(1 << 24))  # first 16 MB as the source fingerprint (full hash = slow; declared)
oplog = {
    "artifact": "siona-foundational-kernel/1",
    "built_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": {"path": INSTR, "sha256_first16MB": h, "license": "CC-BY-SA-4.0 (simplewiki-derived)"},
    "seed": {"n": len(seed), "sha256": sha256_bytes("\n".join(seed).encode()),
             "rule": "notebook token freq >= 5 AND single-word smallwiki title, len > 3"},
    "walk": {"hops": 3, "edges": "quantized-span single-word-title mentions, directed"},
    "quantization": {"W0": W0, "rho": "1/6", "tau_bands": "D<0.452:6 | <0.772:12 | >=0.772 dens>=0.15:192 | else:48",
                     "anchors": "digit | title-token | numword", "sha256_rule": sha256_bytes(
                         b"dyadic W0=192 rho=1/6 tau-banded F1032; anchors digit|title|numword")},
    "negation_guard": "'no' followed by digit = number abbreviation (F1034)",
    "counts": {"articles": len(closure), "vocab": len(vocab), "edges": len(edges),
               "neg_edges": sum(1 for _, _, c in edges if c < 0),
               "tokens": sum(len(r) for r in rows)},
}
json.dump(oplog, open(os.path.join(out_dir, 'oplog.json'), 'w'), indent=1)
print("ARTIFACT: %s" % out_dir)
print("  kernel.bin.gz: %.2f MB | articles %d | vocab %d | tokens %.2fM | edges %d (%d negated)"
      % (len(blob)/1e6, len(closure), len(vocab), oplog['counts']['tokens']/1e6,
         len(edges), oplog['counts']['neg_edges']))
# ROUND-TRIP: decode article 'gravity' (if in closure) back from the blob
import io
raw = gzip.decompress(blob)
na, nv, ne = struct.unpack("<III", raw[:12])
off = 12
rl = [struct.unpack("<I", raw[off+4*i:off+4*i+4])[0] for i in range(na)]
off += 4*na
isz = 4 if nv > 65535 else 2
tot = sum(rl)
ids = struct.unpack("<%d%s" % (tot, "I" if isz == 4 else "H"), raw[off:off+isz*tot])
off += isz*tot
rest = raw[off:].split(b"\x00")
words = rest[0].decode().split("\n")
titles_out = rest[1].decode().split("\n")
if 'gravity' in titles_out:
    gi = titles_out.index('gravity')
    start = sum(rl[:gi])
    dec = " ".join(words[i] for i in ids[start:start+rl[gi]])
    ok = dec == " ".join(qspans['gravity'])
    print("  ROUND-TRIP 'gravity': %s (%d tokens)" % ("EXACT" if ok else "MISMATCH", rl[gi]))
