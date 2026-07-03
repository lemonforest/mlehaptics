"""F1028 probe 2 — TWO-SIDED seed (notebook-frequent AND wiki-rare = the DISTINCTIVE math
vocabulary; the F768 aboutness gate applied to the seed itself) + hop-2 closure + sizes."""
import json, re, gzip, struct, sys

def toks(s):
    return [w for w in re.split(r'[^a-z0-9]+', (s or '').lower()) if len(w) > 2]

seed_tf = {}
for path in (sys.argv[1], sys.argv[2]):
    for w in toks(open(path, encoding='utf-8', errors='replace').read()):
        seed_tf[w] = seed_tf.get(w, 0) + 1

# pass 1: wiki document frequency of every candidate seed word (over lead-60)
cand = {w for w, c in seed_tf.items() if c >= 5}
df = dict.fromkeys(cand, 0)
leads = []
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        rec = json.loads(line)
        lead = rec['s'].split()[:60]
        leads.append((rec.get('t') or rec.get('title') or '', lead, len(line)))
        for w in set(w for w in lead if len(w) > 2) & cand:
            df[w] += 1
N = len(leads)
# DISTINCTIVE: notebook-frequent AND wiki-rare (<1% of leads). Declared, two-sided.
seed = {w for w in cand if df[w] < N * 0.01}
print("candidates %d -> distinctive seed %d (wiki-df < 1%%)" % (len(cand), len(seed)))
print("sample:", sorted(seed, key=lambda w: -seed_tf[w])[:14])

def closure_of(vocab, min_hits):
    return [(t, lead, raw) for t, lead, raw in leads
            if sum(1 for w in set(lead) if w in vocab) >= min_hits]

h1 = closure_of(seed, 3)
print("\nhop-1 closure (>=3 distinctive hits): %d articles (%.2f%%)" % (len(h1), 100.0 * len(h1) / N))
# hop 2: hop-1 titles' words become reachable anchors too
seed2 = set(seed)
for t, lead, _ in h1:
    seed2.update(w for w in toks(t) if len(w) > 3)
h2 = closure_of(seed2, 3)
print("hop-2 closure: %d articles (%.2f%%)" % (len(h2), 100.0 * len(h2) / N))

for name, cl in (("hop-1", h1), ("hop-2", h2)):
    texts = [" ".join(lead) for _, lead, _ in cl]
    raw = "\n".join(texts).encode()
    gz = gzip.compress(raw, 9)
    vocab = {}
    rows = []
    for t in texts:
        rows.append([vocab.setdefault(w, len(vocab)) for w in t.split()])
    wide = len(vocab) > 65535
    fmt = "<I" if wide else "<H"
    stream = b"".join(struct.pack(fmt, i) for r in rows for i in r)
    codegz = gzip.compress(stream + "\n".join(sorted(vocab, key=vocab.get)).encode(), 9)
    fullraw = sum(r for _, _, r in cl)
    print("%s: lead-60 raw %.1f MB | gzip %.1f MB | id-stream gz %.1f MB | FULL bodies %.0f MB (gz ~%.0f)"
          % (name, len(raw) / 1e6, len(gz) / 1e6, len(codegz) / 1e6, fullraw / 1e6, fullraw / 3e6))
json.dump([t for t, _, _ in sorted(h1, key=lambda x: -sum(1 for w in set(x[1]) if w in seed))[:30]],
          open(sys.argv[3], 'w'))
