"""F1187 (#243): the deeper-recurrence corpus — where does F1182's reconstruction sweet-spot scale land on a text with
DEEPER multi-scale recurrence than Gilgameš?

F1182 (Gilgameš): stanza (C=4) beat line (C=1) but episode (C=12) overshot — the sweet-spot was capped at Gilgameš's
recurrence ceiling (the formula/stanza scale). Prediction: a litany corpus (recurrence at the line AND the multi-line
block scale) should push the sweet-spot to a LARGER context scale.

Corpus: Budge's Egyptian Literature (Gutenberg 28282) — the Book of the Dead litanies (Hail x148, Homage x106, I-have-not
x89), the densest-formulaic block located as in F1175. Same F1182 method: excise a burst LACUNA, reconstruct by matching
the bracketing context at increasing scale C, measure recall. numpy-free; no magnitude-builtin.
"""
import re, random

STOP = set(("the of a an and to in on at for with by from as is are was were be been being it he she they thou thee "
            "thy thine ye you your his her its their this that these those o oh unto upon into out over who whom which "
            "what when where how then than not no i am art hath have has had do doth did shall will would may might me "
            "my we us our them him all one there here now come came forth made make let god").split())


def lines_of(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", t); e = re.search(r"\*\*\* END OF", t)
    body = t[s.end():e.start()] if (s and e) else t
    out = []
    for ln in re.split(r"[.\n;:!?]", body):
        ws = frozenset(w for w in re.findall(r"[a-z]+", ln.lower()) if w not in STOP and len(w) > 2)
        out.append(ws)
    return out


def densest_block(rows, markers_raw, W=260):
    flag = [1 if any(m in ln for m in markers_raw) else 0 for ln in raw_lines]
    best = (-1, 0)
    for st in range(0, len(rows) - W, 20):
        c = sum(flag[st:st + W])
        if c > best[0]:
            best = (c, st)
    return best[1]


raw = open("/tmp/egylit.txt", encoding='utf-8', errors='replace').read()
s = re.search(r"\*\*\* START OF.*?\*\*\*", raw); e = re.search(r"\*\*\* END OF", raw)
body = raw[s.end():e.start()]
raw_lines = [ln.lower() for ln in re.split(r"[.\n;:!?]", body)]
rows = lines_of("/tmp/egylit.txt")
st = densest_block(rows, ("hail", "homage", "i have not", "grant thou"))
block = [r for r in rows[st:st + 260] if len(r) >= 2]
N = len(block)


def jac(a, b):
    return len(a & b) / max(1, len(a | b))


def ctx(A, B):
    return sum(jac(A[i], B[i]) for i in range(len(A))) / max(1, len(A))


def reconstruct(b, L, C):
    before = block[b - C:b]; after = block[b + L:b + L + C]
    if len(before) < C or len(after) < C:
        return None
    best_p, best_s = -1, -1.0
    for p in range(C, N - L - C):
        if b - L - C <= p <= b + L + C:
            continue
        sc = ctx(block[p - C:p], before) + ctx(block[p + L:p + L + C], after)
        if sc > best_s:
            best_s, best_p = sc, p
    if best_p < 0:
        return None
    recon = block[best_p:best_p + L]; truth = block[b:b + L]
    return sum(jac(recon[i], truth[i]) for i in range(L)) / L


random.seed(4)
print("F1187 (#243): deeper-recurrence corpus — Book of the Dead litanies (densest block, %d lines)\n" % N)
print("   lacuna reconstruction recall by CONTEXT scale C (the recurrence scale used to find the parallel):")
print("   burst L   line(C=1)   stanza(C=4)   passage(C=8)   episode(C=16)")
for L in (2, 3, 5, 8):
    acc = {1: 0.0, 4: 0.0, 8: 0.0, 16: 0.0}; n = 0
    for _ in range(120):
        b = random.randrange(20, N - 20 - L)
        r = {C: reconstruct(b, L, C) for C in (1, 4, 8, 16)}
        if any(v is None for v in r.values()):
            continue
        for C in acc:
            acc[C] += r[C]
        n += 1
    if n:
        best = max(acc, key=lambda C: acc[C])
        print("     %d       %.3f        %.3f          %.3f          %.3f   (best: C=%d)" % (
            L, acc[1] / n, acc[4] / n, acc[8] / n, acc[16] / n, best))
print("\n  READ: if the sweet-spot (best C) has moved UP from Gilgameš's stanza (C=4, F1182) toward passage/episode (C=8/16),")
print("  the deeper-recurrence litany pushes the reconstruction scale higher — confirming F1182's reading that the fractal")
print("  advantage's sweet-spot tracks the text's ACTUAL recurrence ceiling (litanies recur at larger scales than Gilgameš).")
