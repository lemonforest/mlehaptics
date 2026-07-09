"""F1172 probe: does a LOW Laplacian eigenmode of the line-line coupling graph oscillate at the
SAME period where the temporal recurrence R(k) peaks?  (the F1171 caveat-(c) identity test)

Non-circular by construction:
  - R(k)  = mean Jaccard(line i, line i+k)  -> the TEMPORAL recurrence (line-index domain, F1171).
  - low eigenmodes = smallest-nonzero eigenvectors of the line-line weighted Laplacian (SPECTRAL domain).
Mechanism: a period-P recurrence adds chords line_i ~ line_{i+P}, which LOWERS the eigenvalue of the
period-P oscillation mode.  So identity => the recurrence periods appear among LOW modes, killed by a
line-order shuffle (which destroys the index-period but keeps the same edge multiset).
srmech Class-L for the eigendecomposition; no ndarray, no magnitude-builtin.
"""
import re, sys, random
sys.path.insert(0, "/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c/docs/srmech/siona")
from siona import anchor
from srmech.amsc import laplacian as L
anchor.load_sux()


def load(path, tab):
    """General ETCSL loader: split on ANY line-anchor (c<tab>.<subid>), so c1811.N (flat),
    c1812.1.A.1 (versioned) and c1814.1.1 all parse to one line-unit per anchor (F1172 parser fix)."""
    h = open(path, encoding='utf-8', errors='replace').read()
    segs = re.split(r"<a name='c%s\.[0-9A-Za-z.]+'>" % tab, h)   # bound on every line-anchor
    RAW = []
    for seg in segs[1:]:
        gs = [g for _, g in re.findall(r"doTooltip\(event, '(.*?)'\)\"[^>]*>(.*?)</span>", seg)]
        gs = [g for g in gs if g and not g.startswith('(') and g not in ('.', '…')]
        if gs:
            RAW.append(gs)
    ls = [frozenset(w.lower() for c in anchor.transcribe([ln])[0] if c for w in c.replace("to ", "").split()) for ln in RAW]
    return [s for s in ls if len(s) >= 2]


def sim(a, b):
    return len(a & b) / max(len(a | b), 1)


def recurrence_peaks(lsig):
    """R(k) z-spectrum vs shuffle -> the significant temporal recurrence periods (F1171)."""
    N = len(lsig)
    def ac(s):
        return [sum(sim(s[i], s[i + k]) for i in range(len(s) - k)) / (len(s) - k) for k in range(1, N // 2)]
    R = ac(lsig)
    random.seed(1)
    base = [ac(random.sample(lsig, N)) for _ in range(40)]
    mu = [sum(b[k] for b in base) / 40 for k in range(len(R))]
    sd = [(sum((b[k] - mu[k]) ** 2 for b in base) / 40) ** 0.5 or 1e-9 for k in range(len(R))]
    z = [(R[k] - mu[k]) / sd[k] for k in range(len(R))]
    return set(k + 1 for k in range(1, len(z)) if z[k] > 2.0)   # periods (>1) that beat shuffle


def line_graph_low_mode_periods(lsig, order=None, n_low=10):
    """Build the line-line weighted (Jaccard) coupling graph over the given line ORDER, Class-L
    eigendecompose, and return the dominant oscillation period of each of the n_low lowest-nonzero
    eigenmodes (with the autocorrelation strength of that period)."""
    N = len(lsig)
    idx = order if order is not None else list(range(N))
    seq = [lsig[i] for i in idx]
    edges, weights = [], []
    for a in range(N):
        for b in range(a + 1, N):
            s = sim(seq[a], seq[b])
            if s > 0.0:                                   # co-incidence edge, weight = Jaccard (zero free params)
                edges.append((a, b)); weights.append(s)
    lap = L.signed_laplacian(N, edges, weights)           # all-positive weights = ordinary weighted Laplacian
    evals, evecs = L.symmetric_eigendecompose(lap)
    evals = [float(x) for x in evals]
    ordr = sorted(range(N), key=lambda i: evals[i])
    nz = [i for i in ordr if evals[i] > 1e-6][:n_low]     # the LOWEST nonzero modes
    out = []
    for c in nz:
        v = [float(evecs[r][c]) for r in range(N)]
        mu = sum(v) / N
        vc = [x - mu for x in v]
        denom = sum(x * x for x in vc) or 1e-9
        best_lag, best_r = 0, -1.0
        for lag in range(2, N // 2):                       # dominant oscillation period of this eigenmode
            num = sum(vc[i] * vc[i + lag] for i in range(N - lag))
            r = num / denom
            if r > best_r:
                best_r, best_lag = r, lag
        out.append((best_lag, best_r, evals[c]))
    return out


def overlap(periods, peakset, tol=1):
    return sum(1 for p in periods if any(-tol <= p - q <= tol for q in peakset))   # two-sided window (no magnitude-builtin)


CLEAN = {"1811", "1814", "1815"}     # single-version narrative sequence; 1812/1813 carry parallel MS versions
zs_clean = []
for tab in ("1811", "1812", "1813", "1814", "1815"):
    lsig = load("/home/skirklan/corpora/etcsl/gilg_c%s.html" % tab, tab)
    if len(lsig) > 250:                                    # Class-L native bound n<=256; cap (note the truncation)
        lsig = lsig[:250]
    N = len(lsig)
    if N < 24:
        print("=== c%s: too short (N=%d) ===\n" % (tab, N)); continue
    peaks = recurrence_peaks(lsig)
    low = line_graph_low_mode_periods(lsig)
    strongest = max(low, key=lambda t: t[1])               # the single strongest-oscillating low mode
    low_strong = [p for (p, r, ev) in low if r > 0.15]
    hit = overlap(low_strong, peaks)
    random.seed(7)
    ctrl = []
    for _ in range(20):
        o = list(range(N)); random.shuffle(o)
        cl = line_graph_low_mode_periods(lsig, order=o)
        ctrl.append(overlap([p for (p, r, ev) in cl if r > 0.15], peaks))
    cmu = sum(ctrl) / len(ctrl)
    csd = (sum((c - cmu) ** 2 for c in ctrl) / len(ctrl)) ** 0.5 or 1e-9
    zc = (hit - cmu) / csd
    st_hit = any(-1 <= strongest[0] - q <= 1 for q in peaks)   # two-sided window (no magnitude-builtin)
    tag = "CLEAN" if tab in CLEAN else "versioned(MS A/B — recurrence confounded)"
    print("=== tablet c%s  (N=%d, %s) ===" % (tab, N, tag))
    print("  recurrence peaks R(k): %s" % sorted(peaks))
    print("  strongest low-mode: period %d (strength %.2f, eigval %.3f) %s" % (
        strongest[0], strongest[1], strongest[2], "= a recurrence peak  ✓" if st_hit else "(not a peak)"))
    print("  IDENTITY: %d/%d strong low-modes hit a recurrence peak;  shuffle %.1f±%.1f  ->  z=%.1f" % (
        hit, len(low_strong), cmu, csd, zc))
    print()
    if tab in CLEAN:
        zs_clean.append(zc)
# Stouffer combination across the independent CLEAN tablets (shared epic/language/encoder -> suggestive-plus, not iron-clad)
if zs_clean:
    Zc = sum(zs_clean) / (len(zs_clean) ** 0.5)
    print("STOUFFER-combined identity z over %d CLEAN tablets = %.2f  (per-tablet z=%s)" % (
        len(zs_clean), Zc, ", ".join("%.1f" % z for z in zs_clean)))
    print("  -> %s" % ("SIGNIFICANT combined (identity holds directionally; low modes carry the recurrence periods)"
                        if Zc > 2.0 else "still sub-decisive combined — honest weak/directional identity"))
