"""F1028 probe 3 — OPINION-TRIM BY SHAPE DISTORTION (the user's training op): score each
12-token window of an article by the CROSS-ARTICLE SUPPORT of its content bigrams (how many
OTHER articles carry the same adjacent pair). Factual/relational spans recur corpus-wide;
opinion/evaluative spans are hapax relationships. Declared rule: a window whose median
bigram-support is 0 (no other article has ANY of its pairs) is the opinion/noise candidate.
Read-independent: pure structure, no content labels, no opinion word-list."""
import json, re
from collections import defaultdict

def toks(s):
    return [w for w in re.split(r'[^a-z0-9]+', (s or '').lower()) if len(w) > 2]

# pass 1: bigram document frequency over a 20k-article sample (content bigrams, lead-120)
bdf = defaultdict(int)
sample = 0
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        rec = json.loads(line)
        ws = toks(' '.join(rec['s'].split()[:120]))
        for bg in set(zip(ws, ws[1:])):
            bdf[bg] += 1
        sample += 1
        if sample >= 20000:
            break
print("bigram table over %d articles: %d distinct pairs" % (sample, len(bdf)))

# pass 2: score the fahrenheit article's windows
idx = json.load(open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json'))
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    f.seek(idx['fahrenheit'])
    art = json.loads(f.readline())['s'].split()
W = 12
print("\nfahrenheit article, window support (median other-article count of the window's pairs):")
for i in range(0, min(len(art), 204), W):
    win = art[i:i + W]
    ws = toks(' '.join(win))
    sups = sorted(bdf.get(bg, 0) - 0 for bg in zip(ws, ws[1:]))
    med = sups[len(sups) // 2] if sups else 0
    mark = "TRIM" if med <= 1 else "keep"
    print("  [%s] med=%3d | %s" % (mark, med, ' '.join(win)[:96]))
