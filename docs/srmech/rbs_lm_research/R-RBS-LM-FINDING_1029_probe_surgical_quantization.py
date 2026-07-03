"""F1029 probe — SURGICAL QUANTIZATION of ALL smallwiki (no article culling): every article's
FULL body reduces to its anchored knowledge spans. v2 trim: sliding windows (W=12, stride 6;
a token survives if ANY window holding it keeps), anchors = digits | title-tokens | numwords
(the board's closed class). Measure: kept-token fraction, quantized id-stream+gz size,
fixture survival (the F1027 formula + anchors, April's facts). Streaming; full 384 MB."""
import json, gzip, struct, sys

NUM = {"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
       "twenty","thirty","forty","fifty","hundred","thousand","first","second","third","fourth",
       "fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth"}
W, S = 12, 6

def quantize(title, toks):
    tanch = set(title.split())
    anch = [w.isdigit() or w in tanch or w in NUM for w in toks]
    keep = [False] * len(toks)
    for i in range(0, max(1, len(toks) - W + 1), S):
        if sum(anch[i:i + W]) >= 2:
            for j in range(i, min(i + W, len(toks))):
                keep[j] = True
    return [w for w, k in zip(toks, keep) if k]

vocab = {}
rows = []
titles = []
tot_in = tot_out = 0
fix = {}
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for n, line in enumerate(f):
        rec = json.loads(line)
        t = rec.get('t') or rec.get('title') or ''
        toks = rec['s'].split()
        q = quantize(t.lower(), toks)
        tot_in += len(toks); tot_out += len(q)
        titles.append(t)
        rows.append([vocab.setdefault(w, len(vocab)) for w in q])
        if t in ('fahrenheit', 'april', 'chess'):
            fix[t] = ' '.join(q)
        if n % 60000 == 0:
            print("  ...%dk articles" % (n // 1000), flush=True)
print("ALL %d articles quantized: %d -> %d tokens (%.1f%% kept)" % (
    len(rows), tot_in, tot_out, 100.0 * tot_out / max(1, tot_in)))
fmt = "<I" if len(vocab) > 65535 else "<H"
stream = b"".join(struct.pack(fmt, i) for r in rows for i in r)
code = "\n".join(sorted(vocab, key=vocab.get)).encode()
tidx = "\n".join(titles).encode()
gz = gzip.compress(stream + code + tidx, 9)
print("quantized ALL-articles kernel: id-stream %.1f MB + codebook %.1f MB -> GZ %.1f MB (vocab %d)"
      % (len(stream) / 1e6, len(code) / 1e6, len(gz) / 1e6, len(vocab)))
print("enwiki scaling estimate (~x24 text): ~%.0f MB gz (order-of-magnitude)" % (len(gz) * 24 / 1e6))
print("\nfixture survival:")
for t, q in fix.items():
    checks = {'fahrenheit': ['5 9 x f 32', 'freezes at 32', '212'],
              'april': ['30 days', 'fourth month'],
              'chess': ['64', 'two players']}[t]
    for c in checks:
        print("  %-11s %-16r %s" % (t, c, 'SURVIVES' if c in q else 'lost'))
    print("  %-11s quantized head: %s" % (t, q[:110]))
