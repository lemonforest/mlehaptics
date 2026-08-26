"""F1028 probe 4 — the TWO-AXIS trim rule (sign discovered by probe 3's inversion):
KEEP a window iff it carries >=2 CONTENT ANCHORS (digits + title-tokens); TRIM otherwise.
The high-recurrence formulaic shell ('considered by many', 'often used in') has no anchors;
the knowledge signal ('freezes at 32 f', 'c 5 9 x f 32', 'made in 1724 by daniel gabriel
fahrenheit') is anchor-dense. Declared integers, no thresholds beyond the anchor count."""
import json

idx = json.load(open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json'))
def article(t):
    with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
        f.seek(idx[t]); return json.loads(f.readline())['s'].split()

W = 12
for title in ('fahrenheit', 'april'):
    art = article(title)
    tanch = set(title.split())
    kept = trimmed = 0
    print("\n%s — two-axis trim (keep iff >=2 anchors: digits|title-tokens):" % title)
    for i in range(0, min(len(art), 204), W):
        win = art[i:i + W]
        anchors = sum(1 for w in win if w.isdigit() or w in tanch)
        mark = "keep" if anchors >= 2 else "TRIM"
        kept += mark == "keep"; trimmed += mark == "TRIM"
        print("  [%s] a=%d | %s" % (mark, anchors, ' '.join(win)[:92]))
    print("  -> kept %d / trimmed %d windows (%.0f%% reduction)" % (kept, trimmed, 100.0*trimmed/(kept+trimmed)))
