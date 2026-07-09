"""F1173 probe: does the (x)EC arc generalize to a NON-COGNATE second language?
Egyptian (Afro-Asiatic; TLA 'earlier' slice) vs Sumerian (isolate) — genuinely non-cognate, different script.

Re-runs BOTH prior results on Egyptian, same method, no ndarray, no magnitude-builtin:
  F1171: is the EC recurrence INTRINSIC (R(k) beats a line-shuffle) + multi-scale (a comb, not one subharmonic)?
  F1172: does a LOW Laplacian eigenmode of the line-line coupling graph oscillate at the recurrence periods?
Egyptian line-signature = the set of CONTENT-POS lemmas (NOUN/VERB/ADJ/PROPN) — the native glyph->concept is the
lemmatization, already done, so no translation layer. Slice has NO doc boundaries -> test contiguous windows and
FIRST check local (period-1) coherence, so we know whether the slice is even document-ordered before trusting R(k).
"""
import json, random
from srmech.amsc import laplacian as L

CONTENT = {"NOUN", "VERB", "ADJ", "PROPN"}
PATH = "/home/skirklan/corpora/egyptian_tla/earlier_slice.jsonl"


def load_all():
    rows = []
    for line in open(PATH, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        lem = (r.get("lemmatization") or "").split()
        pos = (r.get("UPOS") or "").split()
        lemmas = []
        if len(pos) == len(lem):
            for p, t in zip(pos, lem):
                if p in CONTENT:
                    lemmas.append(t.split("|")[-1].lower())     # native lemma of a content token
        else:
            lemmas = [t.split("|")[-1].lower() for t in lem]    # fallback: all lemmas
        rows.append(frozenset(w for w in lemmas if len(w) > 1))
    return rows


def sim(a, b):
    return len(a & b) / max(len(a | b), 1)


def recurrence(lsig):
    """F1171: R(k) z-spectrum vs 40-shuffle -> intrinsic? multi-scale comb? plus the local (P=1) coherence."""
    N = len(lsig)
    def ac(s):
        return [sum(sim(s[i], s[i + k]) for i in range(len(s) - k)) / (len(s) - k) for k in range(1, N // 2)]
    R = ac(lsig)
    random.seed(1)
    base = [ac(random.sample(lsig, N)) for _ in range(40)]
    mu = [sum(b[k] for b in base) / 40 for k in range(len(R))]
    sd = [(sum((b[k] - mu[k]) ** 2 for b in base) / 40) ** 0.5 or 1e-9 for k in range(len(R))]
    z = [(R[k] - mu[k]) / sd[k] for k in range(len(R))]
    inh = sum(mu); per = sum(max(0.0, R[k] - mu[k]) for k in range(len(R)))
    peaks = set(k + 1 for k in range(1, len(z)) if z[k] > 2.0)          # non-local recurrence periods
    return {"local_z": z[0], "periodic_pct": 100 * per / inh, "peaks": peaks}


def low_mode_periods(lsig, order=None, n_low=10):
    """F1172: dominant oscillation period of each low eigenmode of the line-line weighted Laplacian."""
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


ALL = load_all()
print("Egyptian (NON-COGNATE) — F1173: does the (x)EC arc generalize?  (%d total lines in slice)\n" % len(ALL))
windows = [(0, 250), (2000, 2250), (4000, 4250)]     # 3 independent contiguous windows = tablet-equivalents
zs = []
for (lo, hi) in windows:
    lsig = [s for s in ALL[lo:hi] if len(s) >= 2]
    N = len(lsig)
    if N < 24:
        print("window [%d:%d]: too sparse (N=%d)\n" % (lo, hi, N)); continue
    rec = recurrence(lsig)
    ordered = rec["local_z"] > 3.0                    # is the slice document-ordered here?
    low = low_mode_periods(lsig)
    low_strong = [p for (p, r) in low if r > 0.15]
    hit = overlap(low_strong, rec["peaks"])
    random.seed(7); ctrl = []
    for _ in range(20):
        o = list(range(N)); random.shuffle(o)
        cl = low_mode_periods(lsig, order=o)
        ctrl.append(overlap([p for (p, r) in cl if r > 0.15], rec["peaks"]))
    cmu = sum(ctrl) / len(ctrl)
    csd = (sum((c - cmu) ** 2 for c in ctrl) / len(ctrl)) ** 0.5 or 1e-9
    zc = (hit - cmu) / csd
    print("window [%d:%d]  (N=%d, %s):" % (lo, hi, N, "document-ordered" if ordered else "NOT clearly ordered — read with care"))
    print("  F1171 intrinsic: local(P=1) z=%.1f ; periodic energy +%.1f%% above aperiodic floor ; recurrence peaks %s" % (
        rec["local_z"], rec["periodic_pct"], sorted(rec["peaks"])))
    print("  F1172 identity : %d/%d strong low-modes hit a recurrence peak ; shuffle %.1f±%.1f -> z=%.1f" % (
        hit, len(low_strong), cmu, csd, zc))
    print()
    if ordered:
        zs.append(zc)
if zs:
    Z = sum(zs) / (len(zs) ** 0.5)
    print("Egyptian STOUFFER identity z over %d ordered windows = %.2f  (per-window %s)" % (
        len(zs), Z, ", ".join("%.1f" % z for z in zs)))
    print("  -> %s" % ("GENERALIZES cross-family (identity holds in Egyptian too)" if Z > 2.0
                        else "sub-decisive in Egyptian — honest weak/null (does NOT clearly generalize on this slice)"))
else:
    print("No clearly document-ordered window found -> cannot fairly test the identity on this slice (honest null-of-method).")
