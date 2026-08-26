"""F1182 (#243): the fractal advantage on a REAL fragmentary text — does multi-SCALE recurrence (episode-scale context)
reconstruct a burst LACUNA better than single-SCALE (line-scale context)?

Mechanism (F1181): a contiguous lacuna destroys a line's LOCAL parallels, but the text's EPISODE-scale recurrence
reaches OUTSIDE the burst. So we reconstruct the lacuna by finding its parallel PASSAGE — matching the surviving
context that BRACKETS the lacuna (lines before + lines after) — at a SMALL context window (single-scale) vs a LARGE
one (multi-scale/episode). If the bracketed episode recurs elsewhere, the parallel's middle IS the lost content.

Corpus: the 5 ETCSL Gilgameš tablets concatenated (oral-formulaic — verbatim repeated speeches = episode recurrence),
glyph->concept via siona.anchor. numpy-free; no magnitude-builtin.
"""
import re, sys, random
sys.path.insert(0, "/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/siona")
from siona import anchor
anchor.load_sux()


def load_tablet(tab):
    h = open("/home/skirklan/corpora/etcsl/gilg_c%s.html" % tab, encoding='utf-8', errors='replace').read()
    segs = re.split(r"<a name='c%s\.[0-9A-Za-z.]+'>" % tab, h)
    rows = []
    for seg in segs[1:]:
        gs = [g for _, g in re.findall(r"doTooltip\(event, '(.*?)'\)\"[^>]*>(.*?)</span>", seg)]
        gs = [g for g in gs if g and not g.startswith('(') and g not in ('.', '…')]
        if gs:
            sig = frozenset(w.lower() for c in anchor.transcribe([gs])[0] if c for w in c.replace("to ", "").split())
            if len(sig) >= 2:
                rows.append(sig)
    return rows


lines = []
for tab in ("1811", "1812", "1813", "1814", "1815"):
    lines += load_tablet(tab)
N = len(lines)


def jac(a, b):
    return len(a & b) / max(1, len(a | b))


def ctx_match(A, B):
    """mean line-wise similarity of two equal-length context blocks."""
    return sum(jac(A[i], B[i]) for i in range(len(A))) / max(1, len(A))


def reconstruct(b, L, C):
    """reconstruct lacuna [b,b+L) using bracketing context of C lines each side; return per-line recall."""
    before = lines[b - C:b]
    after = lines[b + L:b + L + C]
    if len(before) < C or len(after) < C:
        return None
    best_p, best_s = -1, -1.0
    for p in range(C, N - L - C):
        if b - L - C <= p <= b + L + C:            # skip the lacuna's own neighbourhood (the burst region)
            continue
        s = ctx_match(lines[p - C:p], before) + ctx_match(lines[p + L:p + L + C], after)
        if s > best_s:
            best_s, best_p = s, p
    if best_p < 0:
        return None
    recon = lines[best_p:best_p + L]
    truth = lines[b:b + L]
    return sum(jac(recon[i], truth[i]) for i in range(L)) / L


random.seed(4)
print("F1182 (#243): real fragmentary text — multi-scale vs single-scale lacuna reconstruction (Gilgameš, %d lines)\n" % N)
print("   lacuna(burst) reconstruction recall, by CONTEXT window C (=recurrence scale used to find the parallel):")
print("   burst L   single-scale (C=1)   stanza (C=4)   episode (C=12)")
for L in (2, 3, 5, 8):
    r1 = r4 = r12 = 0.0
    n = 0
    for _ in range(120):
        b = random.randrange(20, N - 20 - L)
        a = reconstruct(b, L, 1); c = reconstruct(b, L, 4); e = reconstruct(b, L, 12)
        if a is None or c is None or e is None:
            continue
        r1 += a; r4 += c; r12 += e; n += 1
    if n:
        print("     %d        %.3f              %.3f          %.3f" % (L, r1 / n, r4 / n, r12 / n))
print("\n  READ: if episode-scale context (C=12) reconstructs a burst lacuna better than line-scale (C=1), the text's")
print("  MULTI-SCALE recurrence is what survives bursty damage (F1181 on real text). If flat/low, an honest null —")
print("  the text lacks episode-scale verbatim recurrence to reach outside the burst.")
