"""F1174: the COHERENT non-cognate NARRATIVE test — Chinese (Sino-Tibetan; maximally non-cognate to the Sumerian
isolate + Egyptian Afro-Asiatic).  Chinese is LOGOGRAPHIC, so each character IS a glyph->concept (no lemmatizer) —
the cleanest possible fit to the anchor model.  Two coherent single-narrative epics, both heavily oral-formulaic:
西遊記 Journey to the West + 三國志演義 Three Kingdoms.

Re-runs the coherence-gated F1171 (intrinsic recurrence) + F1172 (low-eigenmode<->recurrence-period identity) probe.
Per-line signature = set of CONTENT characters (a declared grammatical-particle stoplist removed — operators declared
by rule, F817/operators-declared).  srmech Class-L; numpy-free; no magnitude-builtin.

Source (attested, public domain): Project Gutenberg ebook 23962 (西遊記) https://www.gutenberg.org/ebooks/23962
and ebook 23950 (三國志演義) https://www.gutenberg.org/ebooks/23950 . Fetch to /tmp/gb_<id>.txt before running.
"""
import re, random
from srmech.amsc import laplacian as L

# declared grammatical-particle / high-frequency-function stoplist (operators-by-rule, NOT tuned to a result)
STOP = set("的了之也者而以於乎哉矣焉不無有是為得所與及其或又且則乃亦皆但在我你他她它們个個這那此彼著着過一"
           "很卻便就都要來去說道曰見「」『』，、。！？：；（）　 ")


def load(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", t)
    e = re.search(r"\*\*\* END OF", t)
    body = t[s.end():e.start()] if (s and e) else t
    lines = []
    for sent in re.split(r"[。！？\n]", body):
        chars = frozenset(c for c in sent if ('一' <= c <= '鿿') and c not in STOP)
        lines.append(chars)
    return lines


def sim(a, b):
    return len(a & b) / max(len(a | b), 1)


def recurrence(lsig):
    N = len(lsig)
    def ac(s):
        return [sum(sim(s[i], s[i + k]) for i in range(len(s) - k)) / (len(s) - k) for k in range(1, N // 2)]
    R = ac(lsig)
    random.seed(1)
    base = [ac(random.sample(lsig, N)) for _ in range(30)]
    mu = [sum(b[k] for b in base) / 30 for k in range(len(R))]
    sd = [(sum((b[k] - mu[k]) ** 2 for b in base) / 30) ** 0.5 or 1e-9 for k in range(len(R))]
    z = [(R[k] - mu[k]) / sd[k] for k in range(len(R))]
    inh = sum(mu); per = sum(max(0.0, R[k] - mu[k]) for k in range(len(R)))
    peaks = set(k + 1 for k in range(1, len(z)) if z[k] > 2.0)
    return {"local_z": z[0], "periodic_pct": 100 * per / inh, "peaks": peaks}


def low_mode_periods(lsig, order=None, n_low=10):
    N = len(lsig)
    idx = order if order is not None else list(range(N))
    seq = [lsig[i] for i in idx]
    edges, weights = [], []
    for a in range(N):
        for b in range(a + 1, N):
            s = sim(seq[a], seq[b])
            if s > 0.0:
                edges.append((a, b)); weights.append(s)
    if not edges:
        return []
    lap = L.signed_laplacian(N, edges, weights)
    evals, evecs = L.symmetric_eigendecompose(lap)
    evals = [float(x) for x in evals]
    ordr = sorted(range(N), key=lambda i: evals[i])
    nz = [i for i in ordr if evals[i] > 1e-6][:n_low]
    out = []
    for c in nz:
        v = [float(evecs[r][c]) for r in range(N)]
        mu = sum(v) / N
        vc = [x - mu for x in v]
        denom = sum(x * x for x in vc) or 1e-9
        best_lag, best_r = 0, -1.0
        for lag in range(2, N // 2):
            num = sum(vc[i] * vc[i + lag] for i in range(N - lag))
            r = num / denom
            if r > best_r:
                best_r, best_lag = r, lag
        out.append((best_lag, best_r))
    return out


def overlap(periods, peakset, tol=1):
    return sum(1 for p in periods if any(-tol <= p - q <= tol for q in peakset))


def probe_window(lsig):
    N = len(lsig)
    rec = recurrence(lsig)
    low = low_mode_periods(lsig)
    low_strong = [p for (p, r) in low if r > 0.15]
    hit = overlap(low_strong, rec["peaks"])
    random.seed(7); ctrl = []
    for _ in range(12):
        o = list(range(N)); random.shuffle(o)
        ctrl.append(overlap([p for (p, r) in low_mode_periods(lsig, order=o) if r > 0.15], rec["peaks"]))
    cmu = sum(ctrl) / len(ctrl)
    csd = (sum((c - cmu) ** 2 for c in ctrl) / len(ctrl)) ** 0.5 or 1e-9
    return rec, (hit - cmu) / csd, hit, len(low_strong), cmu, csd


TEXTS = [("西遊記 Journey to the West", "/tmp/gb_23962.txt"),
         ("三國志演義 Three Kingdoms", "/tmp/gb_23950.txt")]
print("F1174: coherent non-cognate NARRATIVE test — Chinese (Sino-Tibetan, logographic)\n")
all_z = []
for name, path in TEXTS:
    alllines = [s for s in load(path) if len(s) >= 2]      # keep content-bearing sentence-lines, IN ORDER
    T = len(alllines)
    print("=== %s  (%d content sentence-lines) ===" % (name, T))
    zs = []
    # 3 windows from DIFFERENT parts of the narrative (independent episodes)
    for frac in (0.2, 0.5, 0.8):
        st = int(T * frac)
        lsig = alllines[st:st + 250]
        N = len(lsig)
        if N < 24:
            continue
        rec, zc, hit, nstrong, cmu, csd = probe_window(lsig)
        ordered = rec["local_z"] > 3.0
        print("  window @%.0f%% (N=%d, %s): local(P=1) z=%.1f ; periodic +%.1f%% ; peaks %s" % (
            100 * frac, N, "ordered" if ordered else "NOT ordered", rec["local_z"], rec["periodic_pct"], sorted(rec["peaks"])[:8]))
        print("      identity: %d/%d strong low-modes on a recurrence peak ; shuffle %.1f±%.1f -> z=%.1f" % (
            hit, nstrong, cmu, csd, zc))
        if ordered:
            zs.append(zc)
    if zs:
        Z = sum(zs) / (len(zs) ** 0.5)
        all_z.extend(zs)
        print("  -> %s Stouffer identity z = %.2f over %d ordered windows (per-window %s)\n" % (
            name.split()[0], Z, len(zs), ", ".join("%.1f" % z for z in zs)))
if all_z:
    Zall = sum(all_z) / (len(all_z) ** 0.5)
    print("OVERALL Chinese Stouffer identity z = %.2f over %d ordered windows across both epics" % (Zall, len(all_z)))
    print("  -> %s" % ("GENERALIZES cross-family: the low-eigenmode<->recurrence-period identity holds in a coherent non-cognate narrative"
                        if Zall > 2.0 else "sub-decisive even on coherent Chinese — honest weak result"))
