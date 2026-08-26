"""F1028 probe 1 — the FOUNDATIONAL SEED-CLOSURE reduction + leanest-encoding survey.
Seed = the srmech + MFO research-notebook vocabulary (the math that 'completely understands
the universe' per the user's criterion). Closure = smallwiki articles whose LEAD tokens hit
the seed vocabulary (hop 1; integer match counts, no thresholds beyond a declared min-hits).
Then measure candidate encodings on the closure set. All sizes in real bytes."""
import json, re, gzip, io, sys

def toks(s):
    return [w for w in re.split(r'[^a-z0-9]+', (s or '').lower()) if len(w) > 2]

# --- the SEED: srmech + MFO notebook vocabulary (content words, doc-freq filtered) ---
seed_tf = {}
for path in (sys.argv[1], sys.argv[2]):
    for w in toks(open(path, encoding='utf-8', errors='replace').read()):
        seed_tf[w] = seed_tf.get(w, 0) + 1
# a seed word must recur (>=5 in the notebooks) -- one-off prose words are not the math vocabulary
seed = {w for w, c in seed_tf.items() if c >= 5}
print("seed vocabulary: %d words (>=5 occurrences across srmech+MFO notebooks)" % len(seed))

# --- walk ALL smallwiki leads; closure membership = lead-token seed hits ---
idx = json.load(open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json'))
N = len(idx)
closure = {}   # title -> (lead_tokens, hits)
tot_raw = 0
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        rec = json.loads(line)
        lead = rec['s'].split()[:60]
        lt = [w for w in lead if len(w) > 2]
        hits = sum(1 for w in set(lt) if w in seed)
        tot_raw += len(line)
        if hits >= 8:            # declared: >=8 DISTINCT seed words in the lead
            closure[rec.get('t', rec.get('title', str(len(closure))))] = (lead, hits)
print("smallwiki: %d articles, %.0f MB raw" % (N, tot_raw / 1e6))
print("closure (>=8 distinct seed hits in lead-60): %d articles (%.1f%%)" % (
    len(closure), 100.0 * len(closure) / N))

# --- encoding survey on the closure set (lead-60 kernel notes) ---
texts = [" ".join(lead) for lead, _ in closure.values()]
raw = "\n".join(texts).encode()
gz = gzip.compress(raw, 9)
# id-stream: global codebook + u16/u32 ids
vocab = {}
ids = []
for t in texts:
    row = []
    for w in t.split():
        if w not in vocab:
            vocab[w] = len(vocab)
        row.append(vocab[w])
    ids.append(row)
import struct
wide = len(vocab) > 65535
fmt, sz = ("<I", 4) if wide else ("<H", 2)
stream = b"".join(struct.pack(fmt, i) for row in ids for i in row)
codebook = "\n".join(sorted(vocab, key=vocab.get)).encode()
idgz = gzip.compress(stream + codebook, 9)
# klein-4 relationship instrument: fixed 2-bit x D per article (D=8192 -> 2 KB each)
k4 = len(texts) * (8192 // 4)
# the CHIRAL GRAPH (rc105 shape): title-level co-occurrence edges + per-edge charge
# (u32 u, u32 v, i8 charge-index) + the title codebook
E_est = sum(len(set(t.split())) for t in texts)   # ~one edge per distinct lead word (lower-bound shape)
graph = E_est * 9 + codebook.__sizeof__()
print("\nencoding survey on the closure kernel (lead-60 notes):")
print("  raw text            : %6.1f MB" % (len(raw) / 1e6))
print("  gzip -9             : %6.1f MB" % (len(gz) / 1e6))
print("  id-stream+codebook gz: %5.1f MB  (vocab %d, %s ids)" % (len(idgz) / 1e6, len(vocab), "u32" if wide else "u16"))
print("  klein4 M (D=8192)   : %6.1f MB  (2 KB/article, holographic -- not exact text)" % (k4 / 1e6))
print("  chiral graph (edges+charges, est.): %5.1f MB" % (graph / 1e6))
json.dump(sorted(closure, key=lambda t: -closure[t][1])[:30], open(sys.argv[3], 'w'))
print("\ntop-30 closure titles ->", sys.argv[3])
